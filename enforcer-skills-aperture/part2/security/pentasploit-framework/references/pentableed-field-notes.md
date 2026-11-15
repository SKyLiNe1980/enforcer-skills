# PentaBleed field notes

## Leak behavior
- Idle/cloud NetScalers: always leak `\x31\x31` (uninitialized UAF buffer, null bytes stop `%.*s`)
- Production VPN gateways: leak real HTTP request data, tokens, cookies when sessions are active
- 12 requests in 120s = too slow; `--interval 0.1` = ~600 req/min
- 4KB User-Agent flood fills UAF buffer with identifiable data; bleed back via detection endpoint

## Detection endpoint
```
POST /p/u/doAuthentication.do HTTP/1.0
Host: target
Content-Type: application/x-www-form-urlencoded
Content-Length: 5

login
```

Vulnerable response: `<InitialValue>` non-empty (anything >5 chars after strip).
Patched: `<InitialValue>` empty or HTTP 400 (nginx rejects path divergence).

## Buffer flooding technique (watchTowr)
1. First request: massive User-Agent (~4KB of marker data)
2. Second request: normal detection probe
3. Look for marker data in `<InitialValue>` response
4. Repeat, alternating flood/bleed

## Target hunting
- Shodan: `NetScaler` on AS45102 (Alibaba Cloud) = 326 results. Most idle, all leak \x31\x31.
- Production targets: Fortune 500 VPN gateways, not cloud VPS ranges.
- CISA KEV-listed, actively exploited July 2025.
