# Downloading models to the Windows box — verified 2026-08-11

## bitsadmin FAILS over SSH; use curl.exe instead

`bitsadmin /create /download <job> <url> <dest>` failed with
"Invalid number of arguments" every time it was driven through the SSH tunnel —
both inline via `ssh cmd /c "..."` AND via a .bat file copied to the box.
The SSH/cmd quoting mangles bitsadmin's argument parsing.

**The method that WORKED (Windows 10+ ships curl.exe 8.x):**

```
curl.exe -sL -C - --retry 5 --retry-delay 10 --retry-all-errors \
  --max-time 5400 -o "C:\ComfyUI\models\<folder>\<file>" "<HF resolve URL>"
```

- `-L` follows HF redirects; `-C -` resumes a partial download; `--retry` for
  flaky transfers.
- Run it via `ssh ... cmd /c "curl.exe ..."` — quoting is fine because the
  command has no nested quotes that bitsadmin chokes on.
- Drive it from a python script in a background process for the big files;
  keep a log file and a `--status-only` size check.

## SIZE-check downloads, never existence-check

A killed curl leaves a **0-byte stub** on the destination. A presence check
(`if exist "<dest>" echo PRESENT`) wrongly counts the stub as downloaded —
the script then "skips" the file and it stays empty forever.

Use a size check with a threshold instead:

```
for %F in ("C:\ComfyUI\models\<folder>\<file>") do @echo %~zF
```

Anything under ~10MB is a stub, not a real download. (The 14B diffusion model
is ~14.3GB, the text encoder ~6.7GB, VAE ~253MB.)

## Verify byte-exact against the HF listing

Get the expected size from the HF API and compare:

```
curl -sL "https://huggingface.co/api/models/<owner>/<repo>/tree/main/<path>"
```

The listed `size` field must match the file's bytes exactly (e.g. Wan 2.2 Remix
NSFW v2.0 high_lighting = 14,291,272,136). If the local file matches the listed
size byte-for-byte, the download is complete and correct.

## One quirk: remote curl survives the SSH client dying

If you kill the local python driver, the SSH client dies but the remote
curl.exe keeps running on Windows. The file keeps growing. Don't panic and
don't restart the download — just wait and re-check the size; a subsequent
`-C -` resume also works.
