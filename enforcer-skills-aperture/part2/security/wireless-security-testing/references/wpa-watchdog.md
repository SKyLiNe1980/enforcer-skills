# wpa-watchdog — Auto-Upload PMKID Captures

Standalone folder monitor for PMKID captures. Drop `.cap`/`.pcap`/`.pcapng`/`.22000`
files in `~/wpa-drop/` and they auto-upload to wpa-sec. Processed files move to
`done/` subfolder. Dedup, logging, the works.

## Location
`/root/bin/wpa-watchdog` — runs locally on S10+/Kali.

## Usage

```bash
# One-shot: process all captures in watch dir (dry-run)
python3 /root/bin/wpa-watchdog --oneshot

# One-shot with actual upload
python3 /root/bin/wpa-watchdog --oneshot --upload

# Daemon mode: watch every 5 minutes
python3 /root/bin/wpa-watchdog --daemon --upload --interval 300

# Custom directory
python3 /root/bin/wpa-watchdog --dir /sdcard/tools/wifite2/hs --oneshot
```

## Cron Setup
```
*/5 * * * * python3 /root/bin/wpa-watchdog --oneshot --upload >> /root/wpa-watchdog.log 2>&1
```

## Integration with MCP
The Enforcer MCP server exposes `wpasec_preview` and `wpasec_upload` tools.
wpa-watchdog wraps the CLI upload script and works independently of MCP.

## Workflow
1. wifite2/hcxdumptool drops captures in `~/wpa-drop/`
2. wpa-watchdog (cron or daemon) picks them up
3. Uploads to wpa-sec via `wpasec-upload`
4. Moves to `done/` on success
5. Dedup via MD5(first 1KB + file size) — same capture ignored
