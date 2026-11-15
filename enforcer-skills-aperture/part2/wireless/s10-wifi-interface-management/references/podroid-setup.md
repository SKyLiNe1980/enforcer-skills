# Podroid — No-Root WiFi Pentesting on Android

Podroid is an Android app that runs a VM with full USB pass-through, allowing WiFi tools
without root or custom kernels.

## Setup
1. Install Podroid from Play Store
2. Download Alpine Linux image (minimal, ~50MB)
3. Configure USB pass-through for Alfa AWUS036NH
4. Boot VM, install required tools:

```bash
apk add aircrack-ng wireless-tools git build-base linux-headers
pip install wifite2
git clone https://github.com/ZerBea/hcxdumptool
cd hcxdumptool && make
# ... etc
```

## Interface handling
- `iwconfig` shows the Alfa adapter but can't manipulate it (no wireless extensions in VM)
- Use `iw dev` or `airmon-ng` instead
- `airmon-ng start wlan0` → monitor mode confirmed via `airodump-ng`
- `aireplay-ng -9` — injection test passed

## Verified working
- Monitor mode: ✅
- Packet injection: ✅
- wifite2 PMKID passive: ✅
- airodump-ng: ✅

## Use case
Run on S25 Ultra (daily driver) while S10+ runs Hermes/Enforcer. Two phones,
one for pentesting, one for AI coordination. No root, no kernel modifications.
