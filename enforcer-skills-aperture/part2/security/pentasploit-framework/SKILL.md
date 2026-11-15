---
name: pentasploit-framework
description: PentaSploit unified exploit framework. 6 production exploits with single CLI launcher, capture quality checker, EMBA firmware analysis, and full module development lifecycle. Covers CitrixBleed 2, FreePBX SQLi→RCE, UniFi OS RCE chain, Erlang SSH RCE, Mongoose TLS bypass, and Sudo LPE. Consolidates: penta-sploit, pentasploit-exploit-development.
---

# PentaSploit — Unified Exploit Framework

## Quick Start

```bash
pentasploit --list              # Show all modules
pentasploit bleed <host> --check # CitrixBleed 2 detection
pentasploit pbx <url> --loot     # FreePBX database dump
pentasploit unifi <host> --check # UniFi OS detection
pentasploit erlang <host> -c id  # Erlang SSH command exec
pentasploit mongoose <host>      # Mongoose TLS bypass
pentasploit chwoot --check       # Sudo LPE (via VPS)
```

## Module Reference

| Module | CVE | Type | Real-World Target Count |
|--------|-----|------|------------------------|
| `bleed` | 2025-5777 | CitrixBleed 2 — memory disclosure | Millions (every NetScaler VPN) |
| `pbx` | 2025-57819 | FreePBX SQLi→RCE | Millions (SMB VoIP) |
| `unifi` | 2026-34908/9/10 | UniFi OS auth bypass + command injection | Millions (every UniFi deployment) |
| `erlang` | 2025-32433 | Erlang SSH pre-auth RCE | Rare (mostly internal/cluster) |
| `mongoose` | 2026-5244/5246 | Mongoose TLS cert bypass + heap overflow | Embedded/IoT devices |
| `chwoot` | 2025-32463 | Sudo chroot LPE | 7 architectures (Penta Boys) |

## Supporting Tools

### capcheck — Capture Quality Checker

Pre-flight inspection before wpasec-upload:

```bash
capcheck /sdcard/tools/wifite2/hs --valid-only
capcheck captures/ --json | jq '.[] | select(.raw_match)'
```

Shows ESSID, BSSID, handshake count, PMKID presence per capture.

### wpasec-upload — WPA-SEC Bulk Uploader

Accepts directory paths, auto-converts `.22000` via `hcxhash2cap`:

```bash
wpasec-upload /sdcard/tools/wifite2/hs/today/
wpasec-upload captures/ --dry-run    # Preview without uploading
```

## Field Knowledge

### CitrixBleed 2 (bleed)

- **Idle NetScalers always leak `\x31\x31`** — UAF buffer is null-byte-padded
- **Buffer flooding**: use 4KB User-Agent header to force identifiable data into the leak
- **Production targets**: need active VPN sessions for token leakage
- **Alibaba Cloud NetScalers**: all show `\x31\x31` pattern — not production gateways
- **Shodan is degraded**: 75% stale results, first pages are honeypots. Use `--no-flood --interval 0.1` for fast idle scanning

### Erlang SSH (erlang)

- **Live Erlang SSH hosts are extremely rare** on the public internet
- **Banner `SSH-2.0-Erlang/5.2.10`**: different version scheme, likely patched
- **Connection-reset after channel open** = patched/non-vulnerable
- **Version targets**: OTP-25.3.2.19, OTP-26.2.5.10, OTP-27.3.2

### Mongoose TLS (mongoose)

- **P-384 CA bypass**: line 14074-14076 of mongoose.c — `if(issuer_pubkey_len == 96) return 1;`
- **8192-bit RSA overflow**: oversized client cert triggers heap overflow
- **Two-stage**: cert bypass → overflow → RCE
- **Build requires**: OpenSSL dev headers, GCC, `mongoose_client.c`

## EMBA Firmware Analysis

Throttled wrapper for VPS:

```bash
emba-limited firmware.bin
```

Defaults: 2 CPU cores, 8GB RAM, 8-hour timeout. Logs to `/root/log/emba_<name>/`.

Notable findings from D-Link DIR-822 firmware:
- Kernel 2.6.30.9 (2009): 3,615 CVEs, 147 public exploits
- dnsmasq 2.78: DNSpooq (CVE-2017-14491-14493, CVSS 9.8, pre-auth RCE)
- hostapd 0.5.9: KRACK suite (CVE-2017-13077-13088) — AP-side key reinstallation
- OpenSSL 0.9.8zc: heap overflow era (Solar Eclipse's openssl-too-open.c)
- pipe.c local root: CVE-2009-3547 (EDB 9844, 33321, 40812)

## Pitfalls

- **Shodan is degraded**: don't rely on it as sole target source. Active probing beats passive databases.
- **Docker demos ≠ real exploits**: all PentaSploit modules were tested against live targets, not containers.
- **Erlang targets**: without Shodan API key, finding live vulnerable Erlang SSH hosts is impractical.
- **NetScaler memory leak**: sparse on idle servers. Production VPN gateways required for token leakage.
- **chwoot**: currently remote-only (SSH to VPS). Penta Boys v2 needed for local integration.

## Reference Files

- `references/pentableed-field-notes.md` — CitrixBleed 2 target behavior, buffer flooding technique, detection endpoint
- `references/dlink-dir822-emba-findings.md` — D-Link DIR-822 EMBA audit, DNSpooq + pipe.c kill chain, PoC inventory
