---
name: nethunter-python-tools
description: Python tool setup & troubleshooting on Kali Nethunter / Android — venv on FUSE (/sdcard), editable install fixes, missing deps, bulk module auditing, and general Python deployment on the Nethunter platform. Consolidates: nethunter-python.
---
  - "Python venv fails on /sdcard with symlink error"
  - "pip install -e succeeds but import fails with ModuleNotFoundError"
  - "Python tool on Nethunter won't start, import errors, missing modules"
  - "Need to audit a large Python codebase with many modules for import failures"
  - "Setting up a security tool from /sdcard/tools on Android"
---

# Nethunter Python Tool Setup & Troubleshooting

Covers the recurring pain points of getting Python security tools running on Kali Nethunter / Android, where `/sdcard` is a FUSE (FAT/exFAT) filesystem that does NOT support symlinks.

---

## 1. venv creation fails on /sdcard

### Symptom
```
Error: [Errno 38] Function not implemented: 'lib' -> '/sdcard/tools/.../lib64'
```

### Root Cause
`/sdcard` is mounted as FUSE (typically wrapping FAT32/exFAT). Python's `venv` module creates a `lib64 -> lib` symlink, which FUSE filesystems reject.

### Fix
Create the venv on a native Linux filesystem (ext4, tmpfs):

| Path | Filesystem | Symlinks? | Notes |
|------|-----------|-----------|-------|
| `/root/` | ext4 | Yes | Persistent, good for user tools |
| `/data/local/tmp/` | ext4 | Yes | Persistent, Android-native |
| `/tmp/` | tmpfs | Yes | Volatile, cleared on reboot |
| `/sdcard/` | FUSE | **No** | FAT/exFAT wrapper — never create venvs here |

**Recommended pattern:**

```bash
# Create venv on ext4
python3 -m venv /root/.toolname/venv

# Install deps
/root/.toolname/venv/bin/pip install -r /sdcard/tools/toolname/requirements.txt

# Verify
/root/.toolname/venv/bin/python -c "import toolname; print('OK')"
```

### Launcher script pattern
Create a wrapper at the tool's directory that sources the remote venv:

```bash
#!/bin/bash
# /sdcard/tools/<tool>/venv-activate.sh
VENV_PATH="/root/.airstrike/venv"
source "$VENV_PATH/bin/activate"
if [ $# -gt 0 ]; then
    exec "$@"
else
    echo "venv activated. Run: python -m <tool>"
fi
```

If `python3-venv` is also missing (ensurepip not available):
```bash
apt-get install -y python3.13-venv   # match your Python version
```

---

## 2. `pip install -e` succeeds but `import <package>` fails

### Symptom
```
ModuleNotFoundError: No module named '<root_package>'
```
Even though `pip install -e /sdcard/tools/<project>` reported success.

### Root Cause
The auto-generated editable-install finder (`__editable___<pkg>_<version>_finder.py` in site-packages) has a `MAPPING` dict that maps subpackages to their filesystem paths, but often **omits the root package itself**.

### Fix
1. Find the finder file:
```bash
ls <venv>/lib/python*/site-packages/__editable___*.py
```
2. Patch the MAPPING dict to add the root package entry:
```python
MAPPING: dict[str, str] = {
    '<root_pkg>': '/sdcard/tools/<project>',   # ← ADD THIS LINE
    'subpkg_a': '/sdcard/tools/<project>/subpkg_a',
    ...
}
```
3. Verify:
```bash
<venv>/bin/python -c "import <root_pkg>; print('OK')"
```

---

## 3. Missing system packages (pip rejects --user on Kali)

On Kali, `pip install <pkg>` may fail with "externally-managed-environment" (PEP 668). Use:
```bash
pip install --break-system-packages <pkg>
```

Common missing deps for security tools:
- `pycryptodome` → provides `Crypto` (AES, etc.)
- `python3.13-venv` → provides `ensurepip`
- `pysnmp`, `scapy`, `paramiko`

---

## 4. Bulk module audit pattern

When auditing a large framework (1000+ modules) for import failures:

### Step 1 — Bulk import test
Use the framework's own module indexer if it exists, otherwise walk the filesystem:
```python
from framework.utils import index_modules, import_exploit
modules = index_modules()
for m in modules:
    try:
        import_exploit(f'framework.modules.{m}')
    except Exception as e:
        print(f'FAIL: {m} -> {type(e).__name__}: {e}')
```

### Step 2 — Categorize by error type
Group failures by exception class. Common categories:
- `NameError: 'OptX' not defined` → missing alias in shared exports
- `OptionValidationError` → validation range too restrictive
- `TypeError: 'OptBool' not callable` → module attribute shadows decorator
- `struct.error: pack expected X got Y` → byte format mismatch
- `ModuleNotFoundError` → missing dependency or broken import path
- `ImportError: No module named 'X'` → class name doesn't match convention

### Step 3 — Fix root cause in shared framework code
Prefer fixing the **framework** over individual modules:
- Add missing aliases to `__init__.py` exports (e.g., `OptInt = OptInteger`)
- Widen validation ranges in shared option classes (e.g., allow port 0 for non-TCP protocols)
- Create missing `__init__.py` files for orphaned package directories
- Install missing system dependencies

Only fix individual modules when the bug is truly unique to one file (naming collision, wrong struct format).

### Step 4 — Verify
Re-run the bulk import test. Target: zero failures.

---

## 5. Other Nethunter quirks

- **`&` backgrounding in terminal fails**: The Hermes terminal tool rejects shell `&` backgrounding. Use `terminal(background=true)` for long-running processes, or `execute_code` to orchestrate.
- **Heredocs with Python inside `execute_code`**: The `terminal()` call inside `execute_code` may produce empty output with shell heredocs (`<< 'PYEOF'`). Use `write_file` to create a script, then `terminal("python3 /tmp/script.py")` instead. This pattern appears whenever you need to run multi-line Python from within an `execute_code` block.
- **Always check `df -T` before creating venvs on external storage.**

---

## References

- `references/embedxpl-audit.md` — Full audit log from the EmbedXPL-Forge session: error catalog, files touched, before/after counts.
- `references/airstrike-case.md` — Reproduced case study: AirStrike venv failure on /sdcard, resolution steps, verification.
