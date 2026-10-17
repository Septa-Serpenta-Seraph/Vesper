> **Absorbed skill.** This was the standalone `windows-audio-routing` skill; it now lives as a reference under the **windows-maintenance** umbrella.

# Windows Audio Routing — Getting a Processed Mic Into Discord

The recurring class: *"I want my microphone to sound like X in Discord / OBS / a call."*
Usually a noise gate, EQ, or compressor. The hard part is never the plugin — it's **how
the audio gets from the plugin to the app.** Most guides bury that; this skill puts it
first.

## Tyler's context (so you don't re-derive it)

- **Interface:** Focusrite **Scarlett _Solo_** (confirmed 2026-10-11). ⚠️ **A 3rd-Gen Solo
  has NO Loopback at all** — so for Tyler, the entire "ASIO → Loopback" branch is a dead
  end, not merely the less convenient option. Say so *early*; he spent an evening building
  a VSTHost chain that could never have reached Discord on that box. On a Solo, EQ APO
  isn't just the lightest path — it's the only one that sidesteps the problem instead of
  solving it.
- **Headphones:** HiFiMan Sundara — *open-back*, so
  ModMic-style clip-on mics will pick up his headphone audio. Warn before he buys one.
- **The actual problem:** **Adora is behind him**, so background *speech* leaks into the
  mic. He wants a gate that keys on level.
- **Anti-bloat rule (his, standing):** one job ≠ heavy software. VoiceMeeter is rejected
  as resource-heavy. Reaper is rejected as a DAW. He wants small.
- He already has **VSTHost** and **ReaPlugs** installed.

## ⚠️ The core insight: ASIO cannot be seen by Discord

Discord is a **non-ASIO (WDM)** app. ASIO channels are invisible to it by design. Any
ASIO-based chain therefore needs a *bridge* back into WDM. **Every confusing failure in
this class traces back to this.**

Exactly two bridges exist:

1. **Interface Loopback** — the Scarlett's own virtual channels. Best: no extra software.
   Availability varies by model *and generation*.
2. **A virtual audio cable** (VB-Cable) — works anywhere, but it's a WDM device, so any
   host feeding it must run in **WDM/MME mode, not ASIO**.

**Corollary that trips everyone:** a host using ASIO for input *cannot* also output to
VB-Cable. One driver per engine.

## The decision tree — lightest first

### 1. Equalizer APO on the microphone endpoint  ← start here

**No host app. No virtual cable. No ASIO/WDM bridging. No interface-model dependency.**

Equalizer APO installs an APO **on a device endpoint**, and it supports **capture
(recording) devices** — i.e. microphones. Attach the VST there and every app using that
mic gets the processed signal automatically. ~2 MB, negligible CPU. Antlion Audio (who
ship a competing tutorial) state outright that EQ APO has a much lower footprint than OBS
or Cantabile.

| Step | Do |
|---|---|
| 1 | Install Equalizer APO (x64). `https://sourceforge.net/projects/equalizerapo/` · direct: `https://sourceforge.net/projects/equalizerapo/files/latest/download` |
| 2 | In the **Device Selector**, tick the interface **under the _Capture_ tab** — *not* Playback. The same name appears in both. |
| 3 | Run the built-in **test** the Device Selector offers. It verifies the APO took, and auto-adjusts install mode if not. |
| 4 | **Reboot is usually unnecessary** since v1.3.1 — the installer restarts the audio service itself. |
| 5 | In **Configuration Editor**: clear the default config. `+` → **Control → Device** → Change → select the mic. |
| 6 | Under that Device node: `+` → **Plugins → VST Plugin** → **Load** → pick the `.dll`. |
| 7 | **Open Panel** to edit the plugin GUI. **Ctrl+S** — applies live, no restart. |

⚠️ **Tick ONLY the mic, never the Playback device.** If a gate config ever reaches your
outputs, your music starts cutting out.

⚠️ **The single biggest silent failure: the editor's TOP `Device:` dropdown.**
The Configuration Editor has a `Device:` selector at the top-left (beside `Channel
configuration`). It chooses **which endpoint's configuration you are writing**. It defaults
to `Default (Speakers - …)`. If you build a Correct-Looking Config — Capture-scoped `Device:`
node, plugin loaded, both rows powered green — while that dropdown still points at
**Speakers**, the lines never reach the microphone and *nothing happens anywhere*. The row-1
node saying `Type: Capture … State: APO installed` is **not** proof the config is landing
there.

**Set that dropdown to the microphone entry before doing anything else.** Confirmed as the
actual blocker on 2026-10-11 after every other step was correct.

⚠️ **Match architectures:** 64-bit EQ APO needs a 64-bit plugin. A 32-bit ReaPlugs (in
`Program Files (x86)`) will *load* and then do nothing.

### 2. Cantabile Lite + VB-Cable

Free, purpose-built for real-time FX, saves its configuration so it returns on launch,
hosts x86 and x64 via jBridge. Heavier than EQ APO, a fraction of Voicemeeter.
`https://www.cantabilesoftware.com/free-vst-host`

### 3. Light Host / VSTHost + VB-Cable

Minimal hosts. VSTHost is already installed. Works — see its quirks below.

### Avoid

- **Global VST Host** (MS Store) — **VST3 only**, and ReaPlugs are **VST2**. It physically
  cannot load ReaGate.
- **Voicemeeter** — rejected on footprint.
- **OBS filters** — a 400 MB app to run one gate.

## VSTHost specifics (Hermann Seib)

Real menu names from the v1.58 manual, not guesses:

- **Top menu bar:** `File · Edit · Effect · Engine · Devices · View · Window · Help`
- **Device selection is `Devices → Wave...`** (dialog titled *"Select Wave Devices"*):
  *Input port / Output Port / Sample Rate / Buffer Size*.
- **ASIO drivers appear ONLY in the Output Port dropdown.** Verbatim: *"This box will
  never contain ASIO drivers; since ASIO drivers combine the operation of input and
  output drivers, they are only listed in the Output Port combo box. Whenever an ASIO
  driver is selected in the Output Port box, the Input Port box is grayed out."*
  **A greyed-out Input Port is correct, not broken.**
- **"Silence 1 / Silence 2" in `Engine → Configure → Input Assign` means no audio device
  is selected yet.** VSTHost ships on a dummy device so it can load plugins with nothing
  connected. Input Assign only lists channels of the *current* device.
- **`Asio Control Panel...` / `Asio Channel Selection...` greyed out** in the Devices menu
  = no ASIO driver selected. They light up the moment you pick one — use that as your
  success indicator.
- **MME default buffer is 4410 samples ≈ 100 ms.** Route through MME to VB-Cable and leave
  that, and your voice reaches Discord a tenth of a second late. Drop to 512–1024.
- Manual's own trick when a driver won't take: set Input and Output to `* No Wave *`, OK,
  reopen the dialog, *then* select ASIO.
- The command line accepts a performance file — `Performance → Save As` plus a shortcut is
  how you avoid redoing device selection every launch. `Performance → Update
  Input/Output` writes the current device assignment into the performance.

## Focusrite Loopback — the hidden step

Loopback **does not appear in Windows by default**, even when it exists. Focusrite's own
article: *"If not using a DAW, the Loopback channel will not appear, and you might only be
able to select Input 1+2 of the device."*

**To expose it:** click the **Focusrite Notifier icon in the taskbar** → **"Expose/Hide
Windows Channels"** → tick the loopback channels. *Now* Discord can see them.

- **Focusrite Control:** `Output Routing` → **Loopback Output** → **Custom Mix** → add the
  channels the host is feeding.
- **Scarlett Solo / 2i2 4th Gen:** simpler — ASIO output channels **3–4** *are* the
  loopback; a stereo loopback channel, no Custom Mix needed.
- ⚠️ **Mute the loopback channel anywhere you monitor**, or you build a feedback loop.
- ⚠️ Send the host's output to a pair that **isn't feeding your speakers.**

## Equalizer APO configuration syntax

```
Device: Analogue 1 + 2 (Focusrite USB Audio)
VSTPlugin: "C:\Program Files\VstPlugins\ReaPlugs\reagate-standalone.dll"
```

⚠️ **The quotes around the path are MANDATORY.** An unquoted path fails *silently* — no
error, nothing happens. The single most common EQ APO VST gotcha.

Prefer generating the `Device:` line with the GUI's **Change** button; the exact name
string matters and a near-miss is silent.

## First-line diagnostics (run these before theorising)

**1. "Should I see live input somewhere?"**
- **EQ APO Configuration Editor — NO.** It's a config editor, not a meter.
- **A VST panel under EQ APO — NO, and it never will be.** This is *architectural*, not a
  panel-open quirk (see **Live metering** below): the editor hosts a **mockup instance** of
  the plugin whose only job is capturing your knob movements into `config.txt`, while a
  **second instance** inside the Windows audio service does the actual processing. The editor
  is not in the audio path, so it cannot show anything live — panel open or closed.
  **Don't go hunting for a setting that fixes this.**
- **Windows Settings → Sound → Input** — yes, live bar.
- **Discord's own mic test** — the best end-to-end check.

**2. The decisive chain test.** Under the `Device:` line add:
```
Preamp: -40 dB
```
Save, then run Discord's mic test. Voice goes near-inaudible → **the APO is genuinely live
on that device**. Nothing changes → the APO is attached to a different endpoint than you
think. Thirty seconds, settles the question. Delete the line after.

**3. Tune where you can SEE a meter.** Use VSTHost (its engine stays running, so ReaGate's
meter works live) to dial in the threshold against the real room, write the numbers down,
then type those values into ReaGate under EQ APO. VSTHost for *seeing*, EQ APO for
*running*.

## ReaGate starting settings (level-keyed gate for background speech)

| Control | Start at | Why |
|---|---|---|
| Threshold | −38 dB | Opens on speech, shuts between phrases |
| **RMS size** | **2 ms** | Makes level-keyed gating work instead of chattering |
| Hysteresis | −4 dB | Stops on/off chatter at the edge |
| Attack | 2 ms | First syllable gets through |
| Hold | 80 ms | Survives short gaps between words |
| Release | 100 ms | Closes smoothly |
| Detector highpass | ~130 Hz | Room rumble / desk thumps stop holding it open |

Set threshold just **under his quietest speaking level**, not his loudest. That's the whole
tune.

## Discord-side settings (or the gate fights itself)

**Voice & Video → turn OFF Noise Suppression (Krisp), Echo Cancellation, and Automatic
Gain Control.** Two gates in series chop the front off words; AGC raises the floor and
undoes the gate.

## Hiss ≠ background speech — two DIFFERENT tools

**A gate removes *intermittent* noise. It cannot remove *steady* noise.** Saying this plainly
saves an evening of tuning the wrong thing:

- **Adora talking** → intermittent → **gate** (ReaGate).
- **Hiss / static / room tone** → steady → **denoiser**. A gate cannot touch hiss *while
  you're talking*; it only slams the door between words.

If he says *"it's super hissy now"*, he is describing a **denoiser** problem. Recommended:
**RNNoise** — `https://github.com/werman/noise-suppression-for-voice` (grab
`rnnoise_vst.dll`). Free, tiny, VST2, hosts fine in EQ APO.

**Chain order matters — denoise FIRST, then gate:**
```
Device: Analogue 1 + 2 (Focusrite USB Audio)
VSTPlugin: "…\rnnoise_vst.dll"
VSTPlugin: "…\reagate-standalone.dll"
```
Clean signal into the gate lets the threshold sit lower, so quiet words survive. Reversed,
the gate is making decisions on noisy input.

### His hiss is usually not the software

**1. Focusrite Control is a known offender** — Tyler's own long-standing observation, and
he's right. It's a *configuration* app, not a runtime mixer: it grabs the driver,
reinitialises the interface (audible static burst), and sets the device sample rate.
**Set what you need, then CLOSE IT.** Nothing in an EQ APO chain needs it running.

**2. Sample-rate mismatch.** Nail **48 kHz everywhere** — Playback *and* Recording device in
`mmsys.cpl` (Properties → Advanced), plus Discord. 44.1 on one side and 48 on the other is
the classic "why is my interface staticky".

**3. Windows Microphone Boost.** Installing EQ APO can wake the endpoint properties and
enable **+20/+30 dB boost** — a hiss machine. `Win+R` → `mmsys.cpl` → **Recording** → device
→ Properties → **Levels** → **Microphone Boost = 0**. The interface's own gain knob does
that job properly.

**4. Gain staging.** Set interface gain so normal speech peaks around **−12 to −6 dBFS**.
Cranking gain to compensate for a quiet mic amplifies the noise floor with it — the biggest
physical lever on hiss, and it's a knob, not software.

⚠️ **Check mic boost BEFORE uninstalling EQ APO to test.** Uninstalling reverts the audio
endpoint, so the hiss may disappear and look like "EQ APO was the problem" when the install
merely disturbed a Windows boost value. Cheaper 2-second test: **toggle the row-1 power
button** to bypass all processing and listen.

### Threshold: symptom → cause

| Symptom | Cause | Fix |
|---|---|---|
| Gate never closes on anything | Threshold far too low — **observed at −72.7 dB** | Raise toward −38 dB |
| Word onsets clipped, quiet speech lost | Threshold too high — **observed at −12 dB** | Lower toward −30/−38 dB |
| Chatters on/off at the edge | Hysteresis at 0 | Set +4 dB |
| Closes mid-word | Hold / Release too short | Hold 80 ms |

*(Observed defaults on first install: Threshold −72.7, Hold 0, Hysteresis +0.0, Highpass 0,
RMS 0 — i.e. effectively no gate. All five need changing.)*

## The honest limitation — say this out loud

**A gate kills background noise *between* words. It does not help when the other person is
talking at the same time.** If Adora speaks while Tyler speaks, the gate is already open.
The fix there is physical — mic closer, more directional, aimed away from her — not
software. AI denoisers (RTX Voice, Krisp) won't help either; they're trained to preserve
voices.

Set this expectation *before* he spends an evening tuning for a problem the tool can't
solve.

## Live metering — why it's impossible, and the four workarounds

**Why (authoritative, from the Peace developer on the EQ APO forums):** every EQ APO
interface just writes textual commands to `config.txt`. For each VST plugin the engine
starts a **second instance** to process live audio inside the Windows audio service, and
that instance has no UI channel back to the editor. Verbatim: *"no visual feedback is
possible."* Unchanged for years. **This is the price of EQ APO: VST processing with no
host, no ASIO, no virtual cable — and no meters.** Say it plainly rather than letting him
hunt for a toggle.

Ranked workarounds:

1. **Windows input level bar / Discord's mic test.** The gate is the **first** plugin in the
   chain, so the endpoint meter is a close proxy for what the gate sees. Talk normally, note
   where *quiet* speech sits, set the threshold a few dB under it. Free, zero install —
   start here.
2. **Tune in a host, run in EQ APO.** Load the chain in a host once, dial it with live
   meters, write the numbers down, type them into EQ APO, close the host. Best of both.
3. **Peace** (EQ APO front-end) — real live **peak** meters, read from Windows'
   `IAudioMeterInformation::GetChannelsPeakValues`. ⚠️ **Peace rewrites `config.txt`**, so it
   restructures a hand-built config. Use it, meter, then decide.
4. **EqualizerAPO-XT fork** — native **VST3** support and isolated plugin windows. May
   behave better; whether it fixes metering is **unverified** — don't promise it.

## Downward expander — ReaPlugs has no dedicated one, but it has a trick

**Concept first, because it reframes the whole chain: a gate IS a downward expander with an
infinite ratio.** Everything below threshold goes to silence. A *finite* ratio means the
signal below threshold is **reduced, not muted** — dramatically gentler on voice; room tone
breathes instead of chopping.

- **ReaXcomp (already installed) is the answer.** Per the REAPER effects guide, **a band
  ratio set below 1 makes that band act as an expander rather than a compressor.** It's
  multiband too, so you can expand only the rumble band, or only where the background voice
  lives, and leave the rest alone. Nothing to install. *Try this first.*
- **ReaComp cannot expand** — its ratio will not go below 1.
- **ReaGate has no ratio control at all** — which is exactly why the community wrote
  **ReaXpander**, and it's a **JS** plugin. JS plugins do **not** load in EQ APO. Road closed.
- If ReaXcomp won't do it: **TheExpressor** (TheZhe, free) — purpose-built downward/upward
  expander, but it's **VST3**, so it needs the EqualizerAPO-XT fork (stock 1.4.2 is VST2
  only). **Floorfish** — the classic free expander, but 32-bit and abandoned; won't load in
  a 64-bit host.

**Chain order: denoise → expand → gate.** And an expander may let you **drop the gate
entirely** — usually the better outcome.

## Desk-borne transients: mouse clicks

**Diagnose first:**
- Clicks audible **only between phrases** → the gate is reacting to them.
- Clicks audible **during speech** → raw acoustic pickup; physical fixes only.

**The cause that catches everyone: structure-borne.** A mic on a desk or desk stand receives
the click *through the wood*, not the air. No plugin fixes that. Physical fixes, biggest
first: **(1)** get the mic off the desk onto a clamped boom — the single largest win;
**(2)** point the cardioid's **null** at the mouse (mouth at the front, mouse at the back);
**(3)** closer mouth + lower gain (halving distance ≈ 6 dB less needed); **(4)** thick cloth
pad under the mouse. Cheap interim when it's bolted down: a folded towel or foam pad under
the clamp/base damps a real chunk of the transmission.

**And a gate makes clicks WORSE, not better.** A click is a loud transient — it punches
*above* threshold, so the gate flies open for it and slams shut a moment later. You hear the
click **plus** a gate artifact, which is why they suddenly sound so pronounced.

**Software that genuinely helps — tune the DETECTOR, not the threshold:**

| Control | Set to | Why |
|---|---|---|
| **RMS size** | **25–40 ms** | The real de-click lever. A ~4 ms click can't build enough *average* energy to open the gate; sustained speech can. |
| Attack | 15–25 ms | A 4 ms click can't fully open a gate that takes 20 ms to open |
| Pre-open | **0 ms** | It's anticipation — the opposite of what you want here |
| Hysteresis | +4 dB | Stops post-click chatter |
| Detector lowpass | **~4 kHz** | Voice sits mostly below it; the click's HF snap contributes less to detection |

⚠️ **Trade-off:** slow attack + long RMS also softens **word onsets** — leading consonants
on quiet speech start disappearing. Walk attack back to 8–10 ms if that happens. **RMS size
does the real work; attack is the trim.**

**Honest limit to state:** software can *manage* structure-borne clicks, never remove them.
And free **real-time de-clicker** plugins essentially **don't exist** — the real answer is a
paid restoration suite (iZotope RX), which isn't a live-chain tool. That's why the
recommendation is to fix it at the detector, not to go shopping.

## Pitfalls

- **Don't grind on a fiddly tool when the user asks you to research alternatives.** Half
  this session went into patching VSTHost's ASIO config before Tyler said *"can you do
  some research on this?"* — and the research surfaced a lighter path that skipped the
  problem entirely. If a tool has been fought for three exchanges, research the class
  before debugging further.
- **ASIO ≠ WDM.** Re-check this assumption at every step; it explains most symptoms.
- **Greyed-out menu items in VSTHost are diagnostics, not failures.**
- **Verify architecture (32 vs 64 bit) before believing a plugin is broken.**
- **Verify quotes in EQ APO paths before believing a plugin is broken.**
- **One driver per host engine.** A host on ASIO cannot output to VB-Cable.

## References

- `references/mic-chain-research.md` — the full research pass: Antlion/ModMic model line
  and prices, open-back leakage, VST host comparison, Focusrite Loopback mechanics, and
  source URLs.

## Related

- `windows-maintenance` — the Win10 box itself (debloat, drivers, services).
- `hermes-gateway-troubleshooting` — when the broken thing is Hermes, not audio.
