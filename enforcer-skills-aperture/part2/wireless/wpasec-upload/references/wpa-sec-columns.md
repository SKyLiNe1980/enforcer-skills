# wpa-sec "My Nets" Column Reference

When viewing `https://wpa-sec.stanev.org/?nets` (must enter your key first):

| Column | Meaning |
|--------|---------|
| CC | Country code flag (geolocation of BSSID) |
| BSSID | AP MAC address (click for packet-level detail) |
| SSID | Network name |
| Type | WPA version (WPA2, WPA3, mixed mode) |
| Feat | EAPOL features captured — e.g., `M2M3/M2/A RCnC` = M2+M3 captured, best pair is M2, ANONCE available, Replay Counter checked. `M1M2/M2/U` = M1+M2, unchecked replay. |
| WPA key | Cracked password appears here (textbox, empty until found) |
| Key info | Password metadata when cracked: length, character classes, or "known algorithm" tag (e.g., KPN/Fritz!Box/Ziggo default key formula). Empty until cracked. |
| Get works | Counter: how many times distributed cracking workers (help_crack.py) fetched this network's hash as a work unit. `0` = no one picked it up yet. |
| Timestamp | Submission time |

## Statistics (from /?stats)

- Overall success rate: ~39.6%
- "Cracked by known algorithm": ~125k — these are ISP default keys recognized by pattern
- PMKID success rate: ~36.45% (slightly lower than EAPOL handshakes)
- Contributors: typically 30-40 active at any time

## Why .22000 isn't accepted

The site requires raw pcaps (not hashcat .22000 format) so the server can run hcxpcapngtool itself to:
- Verify replay counter consistency
- Check timestamp sanity
- Validate proper EAPOL sequence
- Prevent corrupted/mangled hashes from wasting distributed cracker GPU cycles
