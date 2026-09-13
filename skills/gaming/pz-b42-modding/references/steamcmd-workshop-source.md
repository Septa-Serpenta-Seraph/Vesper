# SteamCMD Workshop Source Acquisition (PZ and any game)

How to pull a mod's FULL source from the Steam Workshop without owning it or
using a browser — the technique that fetched Bandits 42.20 (working B42 NPC
reference) on 2026-08-10.

## Why
Workshop mods often have no public GitHub mirror (Bandits has none). SteamCMD's
`workshop_download_item` works ANONYMOUSLY for public workshop items — no login
credentials needed. This is the reliable way to get reference source for
reverse-engineering B42 NPC patterns.

## Where to run it
- **Windows box (has Steam):** portable SteamCMD zip, no admin needed.
- **Linux box (this one):** the steamcmd tar.gz ships a 32-bit binary
  (`linux32/steamcmd`) that needs 32-bit loader + libs. If the box has no
  passwordless sudo to install `lib32gcc-s1 lib32stdc++6`, DON'T fight it —
  install SteamCMD on the Windows host instead (below). It's two commands.

## Steps (Windows host, verified 8/10/26)
```powershell
# 1. Install SteamCMD (portable, no admin)
New-Item -ItemType Directory -Force -Path 'C:\steamcmd' | Out-Null
Invoke-WebRequest -Uri 'https://steamcdn-a.akamaihd.net/client/installer/steamcmd.zip' -OutFile 'C:\steamcmd\steamcmd.zip' -UseBasicParsing
Expand-Archive -Path 'C:\steamcmd\steamcmd.zip' -DestinationPath 'C:\steamcmd' -Force

# 2. Download a workshop item anonymously
#    <APPID> = Steam app id of the game (Project Zomboid = 108600)
#    <ITEMID> = the workshop item id (Bandits = 3268487204)
cd C:\steamcmd
cmd /c "steamcmd.exe +login anonymous +force_install_dir C:\steamcmd\bandits +workshop_download_item 108600 3268487204 +quit"

# 3. Find the files
#    C:\steamcmd\bandits\steamapps\workshop\content\108600\3268487204\mods\Bandits\...
```

## Pull the source back to Linux for grep-able research
```bash
scp -i ~/.ssh/windows_desktop -o StrictHostKeyChecking=no -r \
  "tyler@<DESKTOP_TAILSCALE_IP>:C:/steamcmd/bandits/steamapps/workshop/content/108600/3268487204/mods/Bandits/42.20" \
  /home/lumi/research/pz/bandits-42.20/
```

## Notes / pitfalls
- First run downloads + updates SteamCMD itself ("Extracting package... Installing
  update...") — that's normal, wait for "Update complete, launching...".
- Bandits ships MULTI-VERSION folders: `42.12/ 42.13/ 42.15/ ... 42.20/ common/`.
  Grab the folder matching the installed game version (42.20 for current stable).
- Workshop item IDs come from the workshop URL: `steamcommunity.com/sharedfiles/filedetails/?id=3268487204`.
- Files over 50MB on GitHub get a warning but push fine (<100MB hard limit) —
  that's for the backup script, not SteamCMD.
- `+force_install_dir` before `+workshop_download_item` controls where content lands.
- If the game is private/delisted, anonymous download may fail; public mods are fine.
