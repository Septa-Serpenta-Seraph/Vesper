# DualSense / DSX Adaptive-Trigger Mods (PC)

Domain notes for bridge-dependent controller mods — the class where a game-side
plugin only works when a separate host app is running. Rockstar games (RDR2, GTA V)
are the main cases here, but the structure generalises.

## The mental model that answers most questions

These mods have **two halves**, and the downloadable `.asi` is only one of them:

- The `.asi` (e.g. `NodixDualSense.asi`) is injected into the game via ScriptHook.
  It reads game state (weapon, health, horse, wanted level) and streams
  trigger-effect instructions out over **localhost UDP**.
- **DSX / DualSenseX is the bridge** that receives those instructions and
  actually drives the controller's adaptive triggers and lightbar over USB or
  Bluetooth. Without a DSX process running, the `.asi` has nothing to talk to.

So: **the `.asi` alone never produces adaptive triggers.** Owning a DualSense
and dropping the file in the game folder is not enough. Any "can I use this
without DSX?" answer is *no* — but see the free-version route below.

## Free vs paid bridge

- **DSX on Steam** (~$8) is the current, maintained build.
- **Paliverse/DualSenseX on GitHub** is the free open-source line, last release
  v1.4.9 (2021) and explicitly no longer supported/updated. It uses the same
  localhost UDP server/client method, so it is a legitimate free first try for
  mods that list "Steam or GitHub" as sources.
- Caveat to state honestly: some mods (e.g. DualSense4Rockstar) were built and
  tested against the Steam build and say the GitHub build is not supported.
  Check the specific mod's requirements page before promising the free route.

## Install order and version traps

1. Install the **ViGEmBus driver** (controller emulation layer).
2. Install the bridge: DSX Steam, or free GitHub DSX v1.4.9.
3. Install the game hook at the version the mod requires — this matters:
   RDR2 mods may ask for **ScriptHookRDR2 V2** specifically (a separate mod from
   the older V1). Match the stated major version.
4. Drop the `.asi` into the folder containing the game `.exe`.
5. In DSX enable the **UDP server**; confirm the port matches what the mod
   expects (port 6969 for the NodixTech RDR2 mod). A port mismatch is the classic
   silent failure — the game runs, the controller simply does nothing.
6. Launch DSX with the controller connected, then the game. F5 opens some mod
   menus.

## Side effects worth warning about

- DSX typically emulates an **Xbox 360 pad**, so in-game prompts show A/B/X/Y.
  A separate PlayStation Icons Replacement mod restores PS prompts.
- DSX can override other emulator tools (DS4Windows, Steam Input), so haptics
  or vibration from those may stop working while DSX is active.

## Answer shape

Give the short verdict first ("the .asi needs DSX"), then the free option and its
caveat, then the concrete install order with version/port specifics. Specs up
front, no hedging.
