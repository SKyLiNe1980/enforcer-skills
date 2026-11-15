# Known Targets — May 2026 Survey

## Environment
- S10+ (wlan2) + Vye mini with 25dBi dish (wlan0)
- Netherlands residential area, KPN/Ziggo ISP dominant
- ~95 APs visible total across both rigs

## Confirmed TKIP Targets

| Network | BSSID | Chipset | WPA | Auth | Assoc | Clients | Data | Notes |
|---------|-------|---------|-----|------|-------|---------|------|-------|
| RedWine | 22:3B:F3:31:D9:46 | Atheros | WPA1-only | ✓ | ✓ AID:1 | 0 | 0 | Pure WPA1, no RSN IE. Beacon analyzed — multicast TKIP, unicast AES+TKIP. 802.11b/g only. |
| Ziggo8528082 | EC:08:6B:53:66:29 | Compal/Ziggo | WPA2+RSN TKIP | ✓ | ✓ AID:1 | 0 | 0 | Dual-stack: RSN group cipher TKIP + WPA IE multicast TKIP. |
| BWA-0A6C60 | 98:F5:37:57:0C:3D | ZTE | WPA1-only | ✓ | ✓ AID:1 | 0 | 10/15s | Dish-only target. **Michael test PASSED** via tkiptun-ng. Live encrypted frames exist but all mDNS/SSDP, no ARP. |
| vek.35 | 40:3F:8C:EC:FF:23 | Unknown | WPA2+RSN TKIP | — | — | 0 | 2/18s | RSN group cipher TKIP + pairwise AES+TKIP. Another ghost — no clients, minimal data. |

## kr00k Targets Tested

All Arcadyan SuperWiFi2.0 Broadcom (KPN ISP routers). Pattern: WPA2 CCMP PSK, WPS rate-limited, allow fake auth+association, but have **zero AP→client data frames**.

| Network | BSSID | Channel | Max Data | Result |
|---------|-------|---------|----------|--------|
| KPN7124A6 | 8A:19:4D:2A:B9:43 | 6 | 26 | Channel control loss — couldn't lock ch6 |
| KPN7124A6 | 8A:45:E8:29:84:0B | 11 | 8 | 1 data frame captured, all client→AP direction |
| H220N123355 | 8A:D7:AA:A2:8A:21 | 1 | 21 | 2544 packets, 61 data frames — all client→AP. AP sent 512 deauth responses (defence). Zero post-deauth AP→client data. |
| AmyenMilan | 8A:B7:BD:2D:F7:B4 | 6 | 11 | Zero data frames from AP |
| KPNCBBF76 | 8A:D7:AA:A0:CB:7D | 1 | 4 | Rate-limited WPS, minimal data |

## Key Lesson
Arcadyan SuperWiFi2.0 routers act as **dumb bridges** — they forward client traffic but never originate AP→client data. Their TX buffers are effectively empty, making kr00k impractical in this environment.

## CSA Attack — Proven Target

| Network | BSSID | Chipset | PMF | Result |
|---------|-------|---------|-----|--------|
| EPCOT | B4:FB:E4:47:98:BF | Ubiquiti | Off | **CSA success.** Client `5C:2F:AF:06:BE:14` followed forged CSA beacons from ch1 to ch6. 7800+ CSA beacons fired from wlan2, airbase-ng rogue AP on wlan3. Client probed rogue AP (2200+ beacons), sent encrypted QoS Data frames. Blocked by missing WPA password for full 4-way handshake. |
