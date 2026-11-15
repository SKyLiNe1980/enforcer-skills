# capcheck — Pre-flight Capture Quality Inspector

Companion tool to `wpasec-upload`. Runs `aircrack-ng` on captures BEFORE uploading to filter garbage.

## Tool

`/root/bin/capcheck`

## Usage

```bash
# Show all captures with handshake validity
capcheck /sdcard/tools/wifite2/hs --valid-only

# JSON output for pipeline use
capcheck /sdcard/tools/wifite2/hs/today --json

# Filter to only good captures, then upload
capcheck /sdcard/tools/wifite2/hs --valid-only --json | \
  jq -r '.[] | select(.raw_match) | .file' | \
  wpasec-upload --stdin
```

## What it catches

- **Empty captures**: no handshake or PMKID data → skip upload
- **Ziggo noise**: duplicates from strong nearby APs bleeding into passive PMKID captures (common with high-sensitivity 036H)
- **Bad 22000**: hash files with zero valid PMKID/EAPOL lines
- **Duplicate 22000**: identical hash lines repeated dozens of times in passive PMKID collections

## .22000 file support

Parses `WPA*01*` (PMKID) and `WPA*02*` (EAPOL) hash lines. Shows ESSID, BSSID, and type for each hash.

## Pitfall: high-sensitivity adapters

The AWUS036H (-95 dBm sensitivity) pulls adjacent-channel traffic into passive PMKID captures. Ziggo and FritzBox APs with strong signals bleed into every capture file, creating duplicate hashes. The `sort -u` dedup on the .22000 file fixes it post-capture. capcheck flags this by showing duplicate ESSID entries.
