---
name: wpasec-upload
description: Upload WPA captures (.cap/.pcap/.pcapng/.22000) to wpa-sec.stanev.org for distributed cracking. Handles the two-step session flow (key POST → upload) that the broken wlancap2wpasec tool cannot.
---

# wpasec-upload

Upload WPA handshake/PMKID captures to [wpa-sec.stanev.org](https://wpa-sec.stanev.org) for distributed cracking.

## Why this exists

The official `wlancap2wpasec` tool (from hcxtools) is **broken** as of 2026 — it sends the key as a `Cookie: key=...` header in a single request. The wpa-sec site now uses a **two-step session flow**:

1. POST the key as form-urlencoded (`key=<32-char-hex>`) → server sets session cookie
2. POST the capture as multipart with field name `webfile` + session cookie

Also the official tool dumps raw HTML to stdout. This script parses the response into readable output.

## Setup

```bash
# One-time: save your wpa-sec key
wpasec-upload -s -k YOUR_32_HEX_KEY

# Key is stored at ~/.wpasec
```

Get your key: visit https://wpa-sec.stanev.org/?key, enter email, solve captcha.

## Usage

```bash
# Single file
wpasec-upload handshake_EPCOT.cap

# Entire directory — scans for .cap/.pcap/.pcapng/.22000 inside
wpasec-upload /sdcard/tools/wifite2/hs/today/
wpasec-upload /sdcard/tools/wifite2/hs/today/pmkids22000/

# Pipe from find
find . -name "*.pcapng" | wpasec-upload --stdin

# Remove files after successful upload
wpasec-upload -R *.cap

# Dry run — preview what would upload (no key needed)
wpasec-upload --dry-run *.pcapng *.22000
wpasec-upload --dry-run /sdcard/tools/wifite2/hs/

# Disable .22000 auto-conversion
wpasec-upload --no-convert *.22000

# Use explicit key (bypasses ~/.wpasec)
wpasec-upload -k a1b2c3d4... file.cap
```

## File types supported

| Extension | Action |
|-----------|--------|
| `.cap` `.pcap` `.pcapng` `.pcapng.gz` | Direct upload |
| `.22000` | Auto-converted to `.cap` via `hcxhash2cap --pmkid-eapol` |

## Requirements

- Python 3 (stdlib only — no pip deps)
- wpa-sec key (32-char hex)
- `hcxhash2cap` (from hcxtools) for .22000 conversion

## Changelog

- **2026-06-13**: Added directory scanning. Passing a directory path (or piping a directory via `--stdin`) now scans for `.cap`/`.pcap`/`.pcapng`/`.22000` files inside. No more shell-glob failures when captcha files sit in nested subdirectories.
- **2026-06-07**: Fixed .22000 conversion. hcxpcapngtool 7.1.0+ only does pcap→hash (one-way); it does NOT accept .22000 as input anymore. Switched to `hcxhash2cap --pmkid-eapol` for reverse conversion (.22000 → .cap). wpa-sec does NOT accept .22000 directly — conversion is mandatory. Also handles `_0` suffix that hcxhash2cap appends when output file already exists (tempfile stub collision).

## Script location

`/root/bin/wpasec-upload`

## Pitfalls

- The server returns `text/html` for everything — even API responses. The script strips HTML to extract human-readable status.
- The wpa-sec site returns HTTP 302 on key POST success — our custom handler accepts 302 as valid (Python's urllib raises HTTPError otherwise).
- Field name must be `webfile` (not `file` as the old tool used).
- Uploads submitted without a valid key session are processed anonymously and won't appear under "My Nets".
- `hcxpcapngtool` may delete the temp output file on conversion failure (e.g., bad .22000 hash). The script catches `FileNotFoundError` on cleanup — this is expected, not a bug.
- **hcxpcapngtool 7.1.0+ dropped .22000 reverse conversion** — only does pcap→hash (one-way). The script uses `hcxhash2cap --pmkid-eapol` instead. `.22000` files MUST be converted; wpa-sec does NOT accept them directly.
- **hcxhash2cap _0 suffix**: when the output `.cap` file already exists (e.g., from a tempfile stub), hcxhash2cap appends `_0` to the filename. The script now deletes the tempfile stub before conversion and globs for `*.cap` variants afterward.
- The `files` argument uses `nargs="*"` (not `"+"`) so key-only operations like `-s -k KEY` work without requiring file arguments. `--save-key` with no files exits early after saving.
- The wpa-sec site detects duplicates server-side and returns "already submitted" — safe to re-upload the same batch without creating duplicate entries on My Nets.

## References

- `references/wpa-sec-columns.md` — explanation of My Nets page columns (Key info, Get works, Feat, etc.) and site statistics
- `references/dvb-t-af9015-kali.md` — resurrecting AF9015-based DVB-T sticks on Kali (TerraTec Cinergy T RC MKII)
- `references/capcheck.md` — pre-flight capture quality inspector; run before uploading to filter garbage/noise captures
