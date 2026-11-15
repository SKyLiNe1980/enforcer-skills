# Alfa WiFi Adapter Comparison (S10+ Gemster Kernel)

| Adapter | Chipset | Range | Sensitivity | Injection | Quirks |
|---------|---------|-------|-------------|-----------|--------|
| **AWUS036H** | RTL8187L | Best | Highest | Best | Refuses txpower change in monitor mode. PMKIDs sometimes miss M2/M3. Captures occasionally noisy. Best range of the three. **Favorite for passive collection.** |
| **AWUS036NH** | RT2870/RT3070 | Good | Good | Good | Most reliable. Accepts txpower changes. Handles monitor mode cleanly. **Best for active attacks.** |
| **AWUS051NH** | RT2770/RT2750 | Mid | Mid | Mid | Nothing standout, nothing terrible. **Backup/extra interface.** |

## WPA Handshake Capture

**Correct**: `aireplay-ng -0 5 -a <AP> -c <CLIENT> <iface>` — deauth forces reconnection + 4-way capture.

**Wrong** (DO NOT suggest): `aireplay-ng -3` — ARP replay is WEP-era IV generation. Zero value for WPA.

Some clients ignore deauth — try different clients on the same AP. The SeikoEpson printer at A4:D7:3C:68:0B:41 reliably reconnects.

## Passive PMKID Notes

- `.22000` files from passive hcxdumptool may contain duplicate EAPOL hashes from strong adjacent APs bleeding across channels.
- **Fix**: `sort -u captures.22000 > deduped.22000` before uploading to wpa-sec.
- The 036H's high sensitivity makes this more common — it sees APs from adjacent channels.
