# PentaSploit Exploit Development Pattern

Framework architecture for building CVE exploit modules consistently.

## File Structure

```
vault/exploits/cve-YYYY-NNNNN-name/
├── penta<name>.py          # Main exploit (weaponized, CLI)
├── README.md                 # Vulnerability summary, usage
└── (references/)
```

## CLI Pattern (Every Exploit)

```python
# All exploits share this CLI structure:
parser.add_argument("target")          # Required target
parser.add_argument("--check")          # Safe detection (no exploitation)
parser.add_argument("-c", "--command")  # Command execution
parser.add_argument("--shell")          # Reverse shell
parser.add_argument("--lhost/--lport")  # Listener config
parser.add_argument("--recon")          # Post-exploit recon
parser.add_argument("--json")           # Structured output
parser.add_argument("-f/--targets-file") # Batch mode
parser.add_argument("--threads")        # Parallelism
```

## Anti-Patterns Learned from PentaSploit v2

- Docker-only testing = zero real targets exploited
- Confidence meters that say "1.00" on failures
- CLI flags that don't exist (`--fingerprint`, `--list-payloads`)
- JSON output identical to text output
- "polymorphic shellcode" claims without working real-world exploits

## Current Arsenal

| Tool | CVE | Type | Status |
|------|-----|------|--------|
| chwoot | 2025-32463 | Sudo LPE | 7 arches, QEMU tested |
| PentaShell | 2025-32433 | Erlang SSH RCE | Built, targets rare |
| PentaUnify | 2026-34908/9/10 | UniFi OS RCE | Built, millions of targets |
| PentaPBX | 2025-57819 | FreePBX SQLi→RCE | Built, millions of targets |
| PentaBleed | 2025-5777 | CitrixBleed 2 MemLeak | Built, real targets confirmed |

## CitrixBleed 2 Field Notes

- `\x31\x31` = default uninitialized nsppe buffer. NOT a rate-limit.
- Idle cloud VPS NetScalers leak 8 bytes. Production VPN gateways leak sessions.
- Flood technique (4KB User-Agent) forces data into UAF buffer for bleeding.
- CISA KEV-listed, heavily exploited on Fortune 500 VPNs, not Alibaba Cloud VPS.
