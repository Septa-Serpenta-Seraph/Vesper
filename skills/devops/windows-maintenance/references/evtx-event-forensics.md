# EVTX Event-Log Forensics — GPU & Power Failure Diagnosis

Verified 8/16/26 on Tyler's RTX 5070 Ti (recurring Code 43, fixed twice by PSU drain).
Workflow: export `Events.evtx` from Event Viewer (Windows Logs → System → Save All Events),
parse on Linux with `scripts/evtx-dump.py`, correlate timestamps with failure windows
(remember: evtx timestamps are UTC; MT = UTC-6).

## Key event IDs and what they mean

| Event | Meaning |
|---|---|
| `nvlddmkm` (any ID) | NVIDIA driver logged a crash/TDR. **Absence = no driver crash happened.** |
| `WHEA` | Hardware fault (PCIe error, etc.) logged. **Absence = silicon/link looks healthy.** |
| Kernel-Power 41 (L1 critical), `BugcheckCode=0` | Unexpected reboot / hard power cut with NO blue screen. `BugcheckCode≠0` = real BSOD. |
| Event 6008 (EventLog 32768) | "Previous shutdown at <time> was not clean" — dirty shutdown marker. |
| Display 4125 (L4 info) | Display-link blip — screen went black briefly. Clusters after sleep/resume = card struggling to wake. |
| Kernel-Power TargetState=4 / EffectiveState=4 | System entered S3 sleep. |
| Kernel-Boot `LastShutdownGood=False` | The boot after a dirty shutdown. |
| Kernel-Power 42/107/109 | Power-state transition events (secondary detail). |

## The diagnostic chain (what the log told us)

Recurring Code 43 + drain-always-fixes-it case:
1. **No `nvlddmkm`, no WHEA anywhere** → the card never crashed under load and the PCIe
   link never faulted → NOT a driver crash, NOT dead silicon, NOT a bad connector
   (a bad connector fails under load, and would not cleanly re-fix twice).
2. **Display 4125s clustered right after sleep/resume cycles** (e.g. sleep 15:03 → resume
   15:07 → 4125 at 16:14 & 16:17) → the card was already failing to wake from power
   states a full day before the first Code 43.
3. **Kernel-Power 41 (BugcheckCode=0) + Event 6008 at the failure times** → the "fixes"
   themselves were hard power removals (the drains). Confirms drain = the only reset.
4. **Verdict: power-state init issue** — card parks in a deep PCIe/ASPM state at
   sleep/shutdown, fails to wake at next boot → Windows sees a card that won't answer → Code 43.

## Fixes for the power-state-init verdict (in order)

1. `powercfg /setacvalueindex scheme_current sub_pciexpress aspm 0` + `powercfg /setactive scheme_current`
2. Power plan: Sleep = Never on AC
3. Rule out Fast Startup: `powercfg /a` (Hibernation absent → already cold boots);
   registry `HKLM\SYSTEM\CurrentControlSet\Control\Session Manager\Power` → `HiberbootEnabled`
4. DDU clean driver reinstall (driver saving a bad card state at shutdown = same loop)
5. BIOS ErP / Deep S5 — every shutdown becomes a full drain automatically

## Notes

- Event records in an evtx export are NOT guaranteed chronological — sort by the
  SystemTime attribute before reading a story into them.
- The `Display` provider events are information-level (L4); don't filter them out
  when hunting black-screen issues — they're the clue, not the noise.
- A single session can have multiple boot/shutdown pairs; anchor on
  `LastBootId`/`BootId` values to group cycles.
