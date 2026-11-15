# Podroid Mobile WiFi Capture (S25 Ultra)

## Setup
- **Podroid**: Android VM with full USB pass-through
- **OS**: Alpine Linux (minimal, installed in Podroid)
- **Tools**: aircrack-ng suite, wifite2, hcxdumptool, hcxtools, tshark
- **Adapter**: Alfa (plugged via OTG cable)
- **Connection**: Tailscale mesh for Hermes integration

## Verification
- Monitor mode: confirmed (`airmon-ng start wlan0`)
- Injection: confirmed (`aireplay-ng -9`)
- PMKID passive: confirmed (`wifite --pmkid-passive`)
- No root required on S25

## Use Case
- Dedicated SIGINT node alongside S10+
- Fire-and-forget: `wifite --pmkid-passive` → walk away → collect later
- Transfer captures via Tailscale to VPS for wpasec-upload
- S25's unlimited 5G for remote access/upload