# Mic-chain research pass — 2026-10-10

Condensed from a live research session. Kept as a knowledge bank so the next pass
starts from facts instead of re-searching.

---

## Antlion ModMic — the attach-anywhere family

The only real "clip a mic onto any headphone" product line, and **Sundara + ModMic is a
known-good pairing** (there's a Reddit thread literally titled *"Hifiman Sundara + ModMic
Wireless = best headset ever?"*). Antlion markets to open-back owners specifically.

| Model | ~Price | Notes |
|---|---|---|
| ModMic Uni 2+ | $65 | 3.5mm analog. ⚠️ Needs an input that supplies **plug-in power** |
| ModMic USB 2 | $100 | Own ADC — no sound-card noise, works anywhere |
| ModMic Wireless | $150 | 2.4 GHz dongle, zero cables |

**Honest quality framing:** it's very good for voice — above any gaming headset, holds up
in podcasting — but it is a **noise-cancelling electret**, not a studio condenser. "Better
than a headset" and "studio quality" are different claims.

⚠️ **The Uni 2+ trap:** it needs plug-in power from a 3.5mm mic jack. Audio interfaces'
XLR combo inputs do **not** provide that. So the cheap model would have to go into the
motherboard's mic jack — exactly the noisy path you'd be trying to escape. For an
interface user, **USB 2** is the right pick.

⚠️ **Open-back leakage is real and worse on planars.** Open-back headphones dump sound
outward, the ModMic mounts on the cup, so it hears your audio. Known issue; there's a
whole r/headphones thread on it. Mitigate with moderate volume, cardioid angle toward the
mouth, and let the gate do the rest — or keep a cheap closed-back pair for competitive
play.

**The genuine studio ceiling**, if asked: a lav clipped to the headphone cable — **Rode
Lavalier II** (~$100) or **Deity W.Lav Pro** — into an interface with a bias-powering
3.5mm→XLR adapter. Or a DPA 4088 headset mic (broadcast standard, ~$700).

---

## VST host comparison — for live mic processing, lightest first

| Option | Weight | VST2? | Needs a cable? | Notes |
|---|---|---|---|---|
| **Equalizer APO + ReaGate** | ~2 MB, negligible CPU | ✅ | ❌ | Installs on the mic endpoint. Best fit |
| **Cantabile Lite** | Light-moderate | ✅ (x86+x64 via jBridge) | ✅ | Free, built for real-time FX, saves config. Requires Win10 AE+ / Win11, 64-bit only |
| **Light Host** | Very light | ✅ | ✅ | Minimal host; Antlion pairs it with ReaPlugs |
| **VSTHost** | Very light | ✅ | ✅ | Hermann Seib. Works, awkward |
| **LiveProfessor 2** | Moderate | ✅ | ✅ | Free, built for live/broadcast routing |
| **Global VST Host** (MS Store) | Light | ❌ **VST3 only** | ✅ | Cannot load ReaGate. Avoid |
| **Voicemeeter** | Heavy | — | — | Rejected on footprint |
| **OBS filters** | Very heavy | — | — | 400 MB app for one gate |

Key disqualifier: **ReaPlugs are VST2-only.** Any host that's VST3-only is out.

---

## VSTHost v1.58 manual — verbatim excerpts worth keeping

> *"The **Input port** combo box shows all available input devices. This box will never
> contain ASIO drivers; since ASIO drivers combine the operation of input and output
> drivers, they are only listed in the **Output Port** combo box. Whenever an ASIO driver
> is selected in the Output Port box, the Input Port box is grayed out to reflect the fact
> that ASIO doesn't need a separate Input port."*

> *"The devices listed in the combo boxes all have a prefix, either **MME:** for Windows
> Multimedia Extensions drivers, or **DSound:** for DirectSound drivers …, or **ASIO:** for
> ASIO drivers."*

> *"In general, you should always take the drivers that are closest to the hardware … If an
> ASIO driver is available for your sound card, take it."*

> *"Avoid this ASIO driver whenever possible … 'ASIO Multimedia Driver' … adds a layer
> above the Windows MME driver. It gives a horrible performance."*
> *(i.e. don't use Cubase/Nuendo's emulation driver.)*

> *"it's better to select '* No Wave *' for Input and Output Port, close the dialog, reopen
> it, and then select ASIO4All as output driver. This should work with all audio drivers,
> even if they're poorly written."*

Structure facts:
- Menu bar: `File · Edit · Effect · Engine · Devices · View · Window · Help`
- `Devices → Wave...` opens *"Select Wave Devices"* (Input port / Output Port / Sample Rate
  / Buffer Size).
- `Devices → Asio Control Panel...` and `Devices → Asio Channel Selection...` are **greyed
  out until an ASIO driver is selected** — a free readiness indicator.
- `Engine → Configure → Input Assign` shows **"Engine Input Wave Device"** as the right-hand
  source column. If it reads *Silence 1 / Silence 2*, no real device is selected.
- Plug-in slots **0 and 1 are always the built-in Input and Output** blocks (since V1.46,
  shown as `{In}` and `{Out}`).
- `Engine → Run` starts the audio engine.
- Built-in plugins include **Audio PassThru**, Submixer, Reverb, Tone Generator, Delay.
- Performance files (`.vsthost`) hold the whole setup; `Performance → Update Input/Output`
  folds the current device assignment into the loaded performance.
- Default MME buffer is **4410 samples at 44.1 kHz ≈ 100 ms** — unusably laggy for voice
  chat. ASIO buffer typically 128–512 samples.

Documentation: `https://www.hermannseib.com/documents/VSTHost.pdf`

---

## Focusrite Loopback mechanics

Source: Focusrite support articles 360006883140 (Control) and 13229216604562 (Control 2).

- Loopback **"loops back" computer audio outputs to virtual input channels** within the
  interface. **Mute the loopback channels in your recording software** or you create a
  feedback loop.
- **Focusrite Control:** `Output Routing` → select **Loopback Output** → **Custom Mix** →
  tick the hardware inputs / DAW playback channels that should feed it.
- **Focusrite Control 2, Solo & 2i2 4th Gen:** stereo loopback on **channels 3–4**. Set the
  recording input to channels 3–4. Optionally *Preferences → "Send Direct Monitor mix to
  Loopback"* to capture what you hear.
- **Other devices (Control 2):** by default the loopback channel is **Playback 1-2**. Make a
  custom mix, right-click the Mix's *Routed to →* pencil, tick **Loopback**.
- **THE HIDDEN STEP — Windows:** *"If not using a DAW, the Loopback channel will not
  appear, and you might only be able to select Input 1+2 of the device."* Fix: **Focusrite
  Notifier icon in the taskbar → Expose/Hide Windows Channels** → tick the channels. Article
  360010711620.
- macOS is worse: *"Applications such as Microsoft Teams and Discord do not allow for
  specific input selection, and will only use input 1 of your interface."* (Windows is more
  flexible — worth saying when the topic comes up.)

---

## Equalizer APO — installation & syntax facts

- Project: `https://sourceforge.net/projects/equalizerapo/` · direct download:
  `https://sourceforge.net/projects/equalizerapo/files/latest/download`
- Latest observed: **1.4.2** (2025-03-21), file `EqualizerAPO-x64-1.4.2.exe`, ~12 MB.
- **v1.3.1+ can restart the Windows audio service instead of requiring a reboot.**
- **v1.4 replaced the old Configurator with a Qt-based "Device Selector"**, which includes a
  test dialog that verifies the APO install and auto-adjusts the install mode.
- **v1.3+ installs as SFX/EFX by default on Win 8.1+**, which removes the need for the
  "troubleshooting options" odyssey most older guides walk through.
- **Capture-device support is real** — the Device Selector lists input devices under
  *Capture*; you can install the APO on a microphone.
- **VST command syntax:**
  ```
  Device: <exact device name>
  VSTPlugin: "<absolute path to .dll>"
  ```
  ⚠️ **Quotes are mandatory.** SourceForge forum, verbatim: *"VST plugin commands must use
  quotes. Incorrect: `VSTPlugin: plugin.dll`. Correct: `VSTPlugin: "plugin.dll"`."*
- The `Device:` line can be name-only (`Device: Microphone`) or include a GUID in braces
  (`Device: Realtek(R) Audio Microphone {c4f6ae1e-...}`). **Best practice: generate it with
  the GUI's Change button rather than typing it.**
- **GOTCHA: EQ APO pulls the plugin out of the processing path while the plugin's editor
  window is open.** So VST meters freeze in an "Open Panel" window. Not a failure.
- **The proof test:** add `Preamp: -40 dB` under the Device node, save, test the mic in
  Discord. Voice goes near-inaudible → the APO is live on that endpoint. No change → it's
  attached elsewhere.
- Community caveat: some plugins with GUIs can crash APO — **save the config first**.

Config reference: `https://sourceforge.net/p/equalizerapo/wiki/Configuration%20reference/`

---

## ReaPlugs

- `https://www.reaper.fm/reaplugs/` — free (donationware), **VST2**, ships both 32- and
  64-bit. Installs a set of standalone VSTs including `reagate-standalone.dll`,
  `reacomp-standalone.dll`, `reaeq-standalone.dll`, `reafir_standalone.dll`,
  `reaxcomp-standalone.dll`, `readelay-standalone.dll`, `reaverb-standalone.dll`.
- **Note the filename inconsistency:** most are `rea<name>-standalone.dll`, but ReaFir is
  `reafir_standalone.dll` (underscore). Don't typo it in an EQ APO config line.
- Antlion's own mic-processing tutorials use **ReaPlugs + Equalizer APO** together, which is
  decent evidence the combination works.

---

## Discord-side settings that matter

`Voice & Video` → **disable Noise Suppression (Krisp), Echo Cancellation, and Automatic
Gain Control** when running an upstream gate. Two gates in series clip word onsets; AGC
raises the floor and undoes the gate entirely.

---

## The limitation worth stating up front

A gate removes noise **between** utterances. It cannot remove a second person **speaking at
the same time** — the gate is already open. That case needs a physical fix (closer, more
directional mic, aimed away) or a different microphone entirely. AI denoisers trained on
speech (RTX Voice, Krisp) preserve voices by design and won't help.

Also worth flagging for the same reason: an **open-back** headphone plus an
interface-mounted mic means the mic hears the headphones. Closed-backs, or a directional mic
away from the cups, is the mitigation.
