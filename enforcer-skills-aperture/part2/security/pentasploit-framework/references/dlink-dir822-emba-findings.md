# D-Link DIR-822 EMBA Findings — Firmware Vulnerability Audit

## Device

- **Model**: D-Link DIR-822
- **Firmware**: 3.12
- **Kernel**: Linux 2.6.30.9 (Oct 2009 — 17 years old)
- **Tool**: EMBA 2.0.1

## Component Inventory

| Component | Version | CVEs | Exploits | Era |
|-----------|---------|------|----------|-----|
| linux_kernel | 2.6.30.9 | 3,615 | 147 | 2009 |
| openssl | 0.9.8zc | massive | many | 2010 |
| hostapd | 0.5.9 | 14 (KRACK) | some | 2007 |
| dnsmasq | 2.78 | 7 (DNSpooq) | several | 2017 |
| busybox | 1.14.1 | several | some | 2009 |
| ppp | 2.4.2b3 | 5 | 1 | 2006 |
| iptables | 1.4.7 | 1 | 0 | 2010 |
| e2fsprogs | 1.41.12 | several | some | 2009 |
| wireless_tools | 29 | some | some | 2007 |

## Attack Chain

### Remote (LAN-side, Pre-Auth)

1. **DNSpooq** (CVE-2017-14491, CVSS 9.8):
   - Send malicious DHCPv6 packet → heap overflow in dnsmasq
   - dnsmasq runs as root on this device
   - One packet = RCE as root
   - PoC: EDB 42941 (2-byte heap overflow)

2. **DNSpooq** (CVE-2017-14493, CVSS 9.8):
   - Stack overflow in DHCPv6 handling
   - PoC: EDB 42943

### Local Privilege Escalation

3. **pipe.c local root** (CVE-2009-3547, CVSS 7.0):
   - Classic pipe.c NULL deref → root
   - Works on 2.6.0 through 2.6.32
   - PoCs: EDB 9844 (Python), 33321 (C), 40812 (C), 33322 (C)

### WiFi Attacks (AP-Side)

4. **KRACK** (CVE-2017-13077, 13082):
   - hostapd 0.5.9 is the Access Point
   - Key reinstallation works AGAINST the AP
   - Can decrypt client traffic or inject frames

## PoC Files

Vaulted at: `/root/.hermes/vault/exploits/dlink-dir822-emba/pocs/`

| File | CVE | Description |
|------|-----|-------------|
| 42941.py | 2017-14491 | DNSpooq 2-byte heap overflow |
| 42942.py | 2017-14492 | DNSpooq heap overflow |
| 42943.py | 2017-14493 | DNSpooq stack overflow |
| 9844.py | 2009-3547 | pipe.c local root (Python) |
| 33321.c | 2009-3547 | pipe.c local root (C) |

## EMBA Resource Control

```bash
emba-limited firmware.bin   # 2 cores, 8GB RAM, 8-hour timeout
```

Wrapper at `/usr/local/bin/emba-limited` on VPS.
Logs to `/root/log/emba_<name>/`.
Full HTML report: `/root/log/html-report/emba.html` (26KB).
