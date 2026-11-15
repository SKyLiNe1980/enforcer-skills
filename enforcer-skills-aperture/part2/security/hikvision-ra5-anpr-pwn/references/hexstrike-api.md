# HexStrike AI v6.0.0 — Local API Endpoints
# Runs on http://127.0.0.1:8888

## Core Endpoints
| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Server health, tool availability, telemetry |
| POST | `/api/command` | Execute command: `{"command":"nmap -sV 10.0.0.1"}` |
| GET | `/api/telemetry` | CPU, memory, uptime, network I/O |
| GET | `/api/cache/stats` | Cache hit rate, misses, evictions |

## Intelligence Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | `/api/intelligence/analyze-target` | `{"target":"IP"}` → risk level, attack surface score |
| POST | `/api/intelligence/select-tools` | `{"target":"IP","task":"recon"}` → recommended tool list |
| POST | `/api/intelligence/optimize-parameters` | Parameter optimization for selected tools |

## Response Format (command)
```json
{
  "success": true,
  "stdout": "...",
  "stderr": "",
  "return_code": 0,
  "execution_time": 0.015,
  "timed_out": false,
  "timestamp": "2026-06-06T20:55:40.761212"
}
```

## Notes
- 127 tools cataloged, 77 currently installed (PATH-dependent)
- Success rate ~44% — install missing tools to improve
- Cache layer: 31% hit rate, max 1000 entries
- Localhost only (127.0.0.1:8888)
- Designed for Claude Desktop MCP bridge, but REST API works standalone
