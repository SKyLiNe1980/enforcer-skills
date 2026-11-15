# Case: AirStrike on Kali Nethunter (arm64)

## Environment

- Kernel: `4.14.356-openela-rc1Gemster-Kernel1.0-NetHunter`
- Arch: aarch64 (arm64)
- Python: 3.13.12
- Tool: AirStrike v1.0.0 at `/sdcard/tools/airstrike/`

## Reproduction

```bash
cd /sdcard/tools/airstrike
python3 -m venv .venv
# Error: [Errno 38] Function not implemented: 'lib' -> '/sdcard/tools/airstrike/.venv/lib64'
```

## Root Cause

```
$ df -T /sdcard/tools/
Filesystem     Type 1K-blocks     Used Available Use% Mounted on
/dev/fuse      fuse 491214848 41376540 449707236   9% /sdcard
```

FUSE mount over FAT/exFAT → no symlink support.

## Resolution

1. Installed `python3.13-venv` (was missing)
2. Created venv at `/root/.airstrike/venv` (ext4)
3. Installed all 60+ dependencies from `requirements.txt`
4. Created wrapper: `/sdcard/tools/airstrike/venv-activate.sh`

## Verification

```bash
/root/.airstrike/venv/bin/python -c "from airstrike import __version__; print(__version__)"
# Output: 1.0.0
```
