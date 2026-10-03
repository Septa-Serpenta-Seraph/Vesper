# VM Disk Expansion — Hyper-V

## When to Expand

- Disk usage >85% on `df -h /`
- `No space left on device` errors during pip install
- Planning to install large packages (sentence-transformers ~2-4GB, PyTorch ~2GB)

## Hyper-V VHD Expansion Steps

1. **Shut down the VM fully** (not save-state — full shutdown)
2. In Hyper-V Manager on the host:
   - Right-click VM → Settings → Hard Drive → Edit
   - Choose **Expand** → set new size (e.g., 600 GB)
   - Finish/Apply
3. **Boot the VM** and run inside it:
```bash
# Expand partition to fill disk
sudo parted /dev/sda resizepart 3 100%

# Resize LVM physical volume
sudo pvresize /dev/sda3

# Extend logical volume to use all free space
sudo lvextend -l +100%FREE /dev/ubuntu-vg/ubuntu-lv

# Resize filesystem
sudo resize2fs /dev/ubuntu-vg/ubuntu-lv
```
4. Verify: `df -h /` — should show new size, ~4% used

## Post-Expansion Checklist

- [ ] Qdrant binary still exists in `~/.hermes/qdrant/qdrant` (not `/tmp`)
- [ ] Qdrant is running: `curl -s http://localhost:6333/health`
- [ ] Hermes config still points to correct Qdrant URL
- [ ] Cron job for Qdrant auto-restart is still active: `hermes cron list`

## Disk Space Budget (600GB VM)

| Component | Size |
|---|---|
| Hermes agent + venv | ~2.6 GB |
| sentence-transformers + model | ~2-4 GB |
| Qdrant binary | 82 MB |
| Qdrant storage (per 10K chunks) | ~15 MB |
| Hermes state.db (sessions) | ~70 MB |
| Lorebooks + skills | ~50 MB |
| **Usable free space** | **~590 GB** |
