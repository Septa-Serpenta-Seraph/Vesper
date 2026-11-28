# CachyOS Dual-Boot Research (Aug 2026)

Research findings from the Aug 2, 2026 session where Tyler planned a CachyOS
test-drive on his laptop (AMD board, ASUS ROG BIOS). He chickened out of the
BIOS step mid-way ("set to Other OS" done, then stopped) — the install itself
is still pending.

## Sources
- CachyOS wiki: https://wiki.cachyos.org/installation/installation_on_root/
- Reddit r/cachyos "How Do I ACTUALLY Dual-boot Windows And Cachy?"
- CachyOS forums (NVIDIA driver threads)
- CachyOS wiki dual-GPU / chwd pages

## Key facts confirmed

### Requirements (official wiki)
- Secure Boot must be disabled
- ≥30 GB empty partition (shrink from Windows Disk Management: `diskmgmt.msc`, right-click C:, Shrink Volume, ≥30720 MB)
- Bootable USB

### Boot managers
CachyOS offers three; each has a different EFI partition size need:
- **Limine** (default): FAT32 ≥4096 MiB, mount `/boot`
- **systemd-boot / rEFInd**: FAT32 ≥2048 MiB, mount `/boot`
- **GRUB**: FAT32 ≥512 MiB, mount `/boot/efi`

Windows detection per boot manager:
- Limine: `sudo limine-scan`, then copy Windows EFI binaries:
  `sudo cp -r /mnt/WinBoot/EFI/Microsoft/ /boot/EFI`
- GRUB: `sudo pacman -S os-prober`, set `GRUB_DISABLE_OS_PROBER=false` in `/etc/default/grub`, `sudo grub-mkconfig -o /boot/grub/grub.cfg`

### NVIDIA
- CachyOS builds NVIDIA into the kernel monolithic-style (not DKMS) — usually works out of the box
- Verify: `nvidia-smi`
- If not: `sudo pacman -S nvidia-dkms` or `sudo chwd -a`
- chwd tool: `sudo chwd --list-installed`, `sudo chwd -a` for auto GPU config
- Older forum posts about garuda-nvidia-config conflicts are Garuda-specific, not CachyOS

### Tyler's hardware context (for the install session)
- Laptop (AMD board — fTPM, AMD PBS visible in BIOS)
- ASUS ROG UEFI, Advanced Mode; Secure Boot toggle = Boot tab → OS Type → "Other OS" (already done Aug 2)
- Still needed: Fast Startup off, BitLocker pause, shrink C:, boot USB
- Desktop (main rig) deferred — Secure Boot concern there is anti-cheat games; laptop is the safe test bed
