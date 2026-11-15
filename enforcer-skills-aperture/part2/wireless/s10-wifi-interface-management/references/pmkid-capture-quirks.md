# PMKID Capture Quirks — S10+ with Gemster Kernel

## Passive PMKID Capture
Running `hcxdumptool` or `wifite2 --pmkid` in passive mode captures PMKIDs from all nearby APs.
The AWUS036H's high sensitivity means strong APs on adjacent channels bleed into captures.

### Channel Bleed Example
Ziggo7176712 (strong signal on nearby channel) produced 18 identical duplicate EAPOL handshakes 
(WPA*02*) in a single passive session, overwhelming the legitimate PMKIDs.

### Fixes
1. **Post-processing deduplication**: `sort -u capture.22000 > clean.22000`
   - Identical .22000 hash lines are exact string matches — sort -u removes them
2. **BSSID filtering during capture**: `hcxdumptool --filterlist_ap=filter.txt` for known noise APs
3. **Targeted capture**: Don't use passive for specific targets — use `airodump-ng --bssid XX:XX:XX:XX`

## WPA Handshake Capture — Correct Technique
- **Deauth client** (`aireplay-ng -0 3 -a <BSSID> -c <CLIENT>`) → client reconnects → 4-way captured
- **DO NOT use ARP replay** for WPA — ARP replay (`aireplay-ng -3`) is WEP-era IV generation
- ARP replay does nothing useful for WPA/WPA2/WPA3
- Some embedded device MACs ignore deauth (printers, IoT) — target other clients
