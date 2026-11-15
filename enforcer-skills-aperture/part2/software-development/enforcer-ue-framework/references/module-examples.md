# Self-Declaring Module Examples

Real working modules from 2026-06-28 session. Each is a complete, tested drop-in module.

## PentaBleed (96 lines) — `modules/remote/citrix_bleed.py`

Most complete example. Has harvest/loot/sessions payloads, HTTPS target, stealth mode flag.

Key patterns:
- Multiple payload types (flag_only vs flag+takes)
- Boolean flags (NO_FLOOD) handled via `"flags": {"NO_FLOOD": "--no-flood"}` in MODULE
- Host prefix: `https://` prepended via `MODULE["https"] = True`

## PentaRedis (62 lines) — `modules/remote/redis_rce.py`

Most complex arg handling. Has 5 payloads, reverse_shell combines LHOST:LPORT.

Key patterns:
- Payload takes value: `"command": {"flag": "-c", "takes": "COMMAND"}` — run() auto-appends `options["COMMAND"]` after `-c`
- LHOST/LPORT skipped unless `payload == "reverse_shell"`
- `--reverse HOST:PORT` constructed via special post-processing in run()
- `no_json: True` because pentaredis.py doesn't support `--json`

## PentaPBX (45 lines) — `modules/remote/freepbx_sqli.py`

Simplest example. SQLi injection with 5 payloads.

Key patterns:
- COMMAND skipped in arg_map when payload already handles it (`"command": {"flag": "--cron-cmd", "takes": "COMMAND"}`)
- Host URL: prepend `http://` if no scheme present
- `no_json: True`, `https: False`

## Discovery System

`module_discovery.py` scans `modules/{remote,recon,local}/` for `.py` files, loads via `importlib`, extracts `MODULE` dict. Errors logged but don't break console.

Merge strategy: discovered modules OVERRIDE hardcoded MODULES dict entries.
