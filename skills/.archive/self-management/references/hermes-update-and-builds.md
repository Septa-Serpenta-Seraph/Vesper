# Hermes update failures — toolchain & build triage

Verified 2026-10-08 on the Vesper host (Ubuntu 24.04, GCC 13, no LLVM
toolchain). Companion to the "Updating the host install" section in SKILL.md.

## Symptom

`hermes update` aborts during dependency preparation:

```
✗ Installing Python dependencies failed; last 80 lines of output:
  ...
  clang++ -pthread -fno-strict-overflow ... -c build/temp.../_libolm.cpp -o ...
  error: [Errno 2] No such file or directory: 'clang++'
hint: `python-olm` (v3.2.16) was included because `hermes-agent[matrix]`
      (v0.0.0) depends on `mautrix[encryption]` (v0.21.1) which depends on
      `python-olm`
Update preparation failed: venv: uv sync exited 1
```

## Read the failure, don't react to the loudest line

**Setuptools deprecation warnings in the same block are NOISE.** The
`project.license` TOML-table and "License classifiers are deprecated"
messages dominate the output visually and are *warnings*, not the failure. The
actual error is the single bare line:

```
error: [Errno 2] No such file or directory: 'clang++'
```

Scan for `error:` / `RuntimeError` lines; ignore anything carrying
`Warning:`/`DeprecationWarning:`. This is general: build logs bury the cause
under a wall of version-deprecation chatter.

## Root cause: the bundled Python's compiler expectation

Hermes ships its own CPython. That interpreter was **compiled with clang**, so
its `sysconfig` reports clang as the compiler for C extensions:

```bash
P=$(ls -d ~/.hermes/tools/python-3.14.7*/bin/python3)
$P -c "import sysconfig;print('CC =',sysconfig.get_config_var('CC'));
       print('CXX =',sysconfig.get_config_var('CXX'))"
# CC  = clang -pthread
# CXX = clang++ -pthread
```

When a package has no wheel for that Python version, `uv` builds it from sdist,
and the cffi/setuptools build asks for the compiler `sysconfig` names. If clang
is not installed → `[Errno 2] 'clang++'`. **The package is fine; the toolchain
is mismatched.**

Confirm the toolchain state:

```bash
for c in clang clang++ gcc g++ cc c++; do printf "%-8s " $c; command -v $c || echo MISSING; done
```

Trap: `/usr/lib/llvm-18` can exist holding only **runtime** libs
(`libclang-cpp18`, `libclang1-18`) with no `bin/` and no compiler binary. A
directory named `llvm-*` does not mean clang is installed — check the binary.

`python-olm` is only in the graph because of the **matrix** extra
(`hermes-agent[matrix]` → `mautrix[encryption]` → `python-olm`), which is
Linux-gated in `pyproject.toml` (`[tool.hermes.extras-platforms]`).

## Three fixes, cheapest first

### A. Install the compiler the interpreter expects (proper, needs sudo)

```bash
sudo apt install -y clang     # clang 18 is in the repos
hermes update
```

Makes the box match the interpreter. Preferred long-term answer.

### B. Override the compiler for the run (no sudo, one shot, VERIFIED)

```bash
CXX=g++ CC=gcc hermes update
```

Why this reaches the build: Hermes' package manager builds the subprocess
environment from `os.environ`, filtering out only `PYTHON*`, `VIRTUAL_ENV`, and
non-forwarded `UV_*` (`pm/environment.py` → `_base_environment`). **`CC` and
`CXX` pass straight through** to `uv sync`.

Proven: built `python-olm==3.2.16` from the cached sdist with exactly those vars
→ compiled in ~8s, produced `_libolm.abi3.so`, `import olm` OK.

### C. Durable shims (no sudo, survives future updates, VERIFIED)

`~/.local/bin` is **first on PATH** on this host, so scripts placed there are
resolved by every process — including the already-running gateway — with no env
change and no restart.

```sh
# ~/.local/bin/clang     → exec gcc "$@"
# ~/.local/bin/clang++   → exec g++ "$@"
chmod +x ~/.local/bin/clang ~/.local/bin/clang++
```

Both with a header comment explaining WHY (bundled CPython built with clang,
no LLVM installed) and the revert instruction (`sudo apt install -y clang`, then
delete the two files). Keep them honest — the shim reports GCC's version when
asked, so nothing silently believes it is clang.

**Verification that actually proves it** — a cached wheel will lie to you, so
force a fresh build with no env override:

```bash
P=$(ls -d ~/.hermes/tools/python-3.14.7*/bin/python3)
rm -rf /tmp/olmt && mkdir -p /tmp/olmt
env -u CC -u CXX uv pip install --no-cache --python "$P" \
    --target /tmp/olmt python-olm==3.2.16
find /tmp/olmt -name "_libolm*"          # expect _libolm.abi3.so
PYTHONPATH=/tmp/olmt $P -c "import olm; print('ok')"
```

Without `--no-cache` uv serves the previously-built wheel and the test passes
for the wrong reason. **Any "did the fix work?" build test must defeat the
cache.**

### Cheaper option if the extra isn't wanted

If the Matrix gateway is never used, dropping the `matrix` extra removes
`python-olm` from the graph entirely and the build disappears. It is Linux-gated
and part of the default set, so this is a config decision, not a quick edit.

## Free side effect: `hermes` self-repairs its dependency environment

Running *any* `hermes` command while the venv is out of sync triggers an
automatic repair pass, visible at the top of the output:

```
hermes: repairing the recorded dependency environment...
  → Installing Python dependencies…
  ✓ Installing Python dependencies
hermes: dependency environment repaired
```

After the fix was in place, invoking `hermes update --help` repaired the env on
its own and `import olm` / `import mautrix` both succeeded. **So check whether
the problem is still there before assuming a full update run is needed.**

## Generalizable lessons

1. **Build logs bury the cause.** Grep for `error:`; ignore `Warning:` lines.
2. **A mismatched toolchain, not a broken package.** When a bundled interpreter
   names a compiler, the host must have that compiler or an explicit override.
3. **Defeat the build cache when verifying.** `--no-cache`, and unset the env
   vars you're testing around.
4. **Prefer the fix that survives the next run.** A one-shot env var unblocks
   today; a PATH shim or a real install unblocks every future update.
5. **Sandbox before shipping.** Test against a fake input (temp dir, fake
   config) so a wrong fix can't damage the live install.
