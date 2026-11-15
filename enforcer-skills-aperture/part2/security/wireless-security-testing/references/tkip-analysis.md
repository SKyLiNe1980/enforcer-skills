# RedWine & Ziggo8528082 — WPA1/TKIP Case Studies

## RedWine — Pure WPA1, 0 clients

| Field | Value |
|-------|-------|
| BSSID | 22:3B:F3:31:D9:46 |
| ESSID | RedWine |
| Channel | 3 (2422 MHz) |
| Signal | -56 to -64 dBm |
| Chipset | Atheros (OUI 00:03:7f) |
| Rates | 802.11b/g only (1-18 Mbps) |
| Clients | 0 (consistently across multiple scans) |

### Beacon decode

The AP advertises the **old WPA Information Element** (tag 221, OUI 00:50:f2 Microsoft, type 1),
NOT the RSN IE (tag 48). This makes it **pure WPA1**, not WPA2.

```
Tag: Vendor Specific: Microsoft Corp.: WPA Information Element
    Multicast Cipher Suite: 00:50:f2 (Microsoft Corp.) TKIP
    Unicast Cipher Suite List:
        00:50:f2 (Microsoft Corp.) AES (CCM)   <-- type 4
        00:50:f2 (Microsoft Corp.) TKIP         <-- type 2
    AKM: PSK
```

### Attack attempts and results

| Attempt | Result |
|---------|--------|
| Fake auth + association | **SUCCESS** — AID:1, sole client |
| 4-way handshake trigger | Failed — AP cached session, no re-handshake |
| Traffic sniff (200 packets) | Only beacons + probe responses — 0 data frames |
| ARP replay (1300+ packets) | 0 ARP requests — dead silent |
| tkiptun-ng | Blocked — no encrypted data frames to replay |

### Key takeaway

Fake auth succeeding is unusual and worth noting, but without at least one
encrypted data frame, tkiptun-ng and chopchop have nothing to work with.
The AP is powered on but completely idle — no upstream router behind it
generating broadcast traffic.

---

## Ziggo8528082 — WPA2 RSN with TKIP, 0 clients

| Field | Value |
|-------|-------|
| BSSID | EC:08:6B:53:66:29 |
| ESSID | Ziggo8528082 |
| Channel | 1 (2412 MHz) |
| Signal | -63 to -65 dBm |
| ISP | Ziggo (Dutch cable ISP) |
| Clients | 0 (30s scan) |

### Beacon decode

Unlike RedWine, this AP advertises BOTH RSN (WPA2) and WPA1 IEs:

```
RSN Information (WPA2):
    Group Cipher Suite: 00:0f:ac TKIP
    Pairwise Cipher Suite List: 00:0f:ac AES (CCM), 00:0f:ac TKIP
    AKM: PSK

WPA Information Element (WPA1):
    Multicast Cipher Suite: 00:50:f2 TKIP
    Unicast Cipher Suite List: 00:50:f2 AES (CCM), 00:50:f2 TKIP
```

Dual-stack TKIP — both the WPA2 and WPA1 IEs advertise TKIP as a valid
group and pairwise cipher. This is a modern ISP router (likely Ubee/Compal)
that supports TKIP for backward compatibility.

### Attack attempts

Not attempted. Same 0-client problem as RedWine. Worth revisiting if a
client ever appears.

---

## TKIP hunting methodology (evolved)

### Method A: tshark sweep (best for finding all TKIP APs)
```bash
tshark -i wlan2 -f "type mgt subtype beacon" -w beacons.pcap -c 200
tshark -r beacons.pcap -Y "wlan.rsn.gcs.type == 2" -T fields -e wlan.sa -e wlan.ssid | sort -u
```
Only Ziggo8528082 matched across the entire survey. RedWine did NOT match
because it only advertises TKIP via the old WPA IE, not RSN.

### Method B: grep for TKIP in WPA IE (catches WPA1-only APs)
```bash
tshark -r beacons.pcap -V | grep -B5 "Multicast Cipher Suite.*TKIP"
```
This catches both RedWine-style WPA1 (Microsoft OUI) and Ziggo-style
WPA2+RSN TKIP (IEEE OUI).

### Method C: airodump CSV grep (quick but incomplete)
```bash
grep -i "tkip" /tmp/survey-01.csv
```
May miss some APs. airodump can show "WPA2 CCMP PSK" even when TKIP
is advertised in the beacon — always verify with tshark.

---


## EPCOT — Active low-traffic WPA2 target (-18 dBm, sleepy client)

| Field | Value |
|-------|-------|
| BSSID | B4:FB:E4:47:98:BF |
| ESSID | EPCOT |
| Channel | 1 (2412 MHz) |
| Signal | -18 to -19 dBm (extremely close) |
| Encryption | WPA2 CCMP PSK |
| Clients | Invisible in airodump-ng station list, but data frames prove 1+ exist |
| Data rate | ~2 encrypted frames/min (sleepy keepalives) |

### Discovery

This AP appeared in the initial airodump survey at -22 dBm with 34 data frames
and multiple nodes (ch1 + ch11). A 30s targeted scan showed 41 data frames but
no stations listed in the real-time display. A 60s tcpdump capture confirmed:
2 encrypted Data frames (IV shown, KeyID 1) at -18 to -19 dBm signal.

The client(s) are extremely idle — sending keepalive packets at ~2/min — but
they ARE there. This makes EPCOT fundamentally different from RedWine/Ziggo8528082:
encrypted data EXISTS and can be captured.

### Attack surface

This is a prime candidate for protocol-level attacks that don't require the
WPA key:

- **Deauth + handshake capture**: force the sleepy client to disconnect and
  re-handshake. At -18 dBm, the 4-way handshake will be captured cleanly.
- **FragAttack probing**: test the AP's fragment reassembly and A-MSDU
  aggregation handling (requires patched drivers — check chipset compatibility
  at /sdcard/tools/fragattacks/)
- **KRACK retransmission tests**: capture the 4-way handshake and check for
  key reinstallation during retransmitted message 3 (requires WPA passphrase;
  scripts at /root/krackattacks-scripts/)
- **kr00k**: the Broadcom/WPA2 vulnerability in frame encryption after
  disassociation

### Initial findings

- Handshake previously captured via broad hcxdumptool sweep (hash #5 of 6,
  client 5C:2F:AF:06:BE:14, AP B4:FB:E4:47:98:BF)
- Encrypted data frames confirmed via tcpdump at -18 dBm
- Client invisible in airodump-ng real-time display despite active data

### Deauth attempts (2026-05-25 session)

PMF verified OFF via beacon RSN capabilities — deauth SHOULD work:

| Attempt | Method | Packets/ACKs | EAPOL Result |
|---------|--------|-------------|--------------|
| Targeted (-c 00:09:B0:F3:2C:3D) | 10 deauths, ~2000+ sent | Thousands of ACKs received | 1 EAPOL frame (M1 only) — 0 handshake |
| Broadcast (no -c) | 5 broadcast deauths | N/A | 3 EAPOL frames (M1/M3 only) — 0 handshake |

Despite thousands of acknowledged deauth frames, the sleepy IoT client never
completed a full 4-way handshake within the capture window. The client IS
responding (M1/M3 from AP observed), but M2/M4 never arrive — likely because
the IoT device reconnects on its own schedule (minutes, not seconds) and
our ~30s capture windows were too short.

Next steps: 15-minute airodump stakeout on ch1 to catch a full handshake.

### Key takeaway

An AP can have active encrypted traffic with NO stations showing in
airodump-ng. Don't trust the station list alone — look at the #Data column.
If data frames > 0, clients exist even if invisible. However, IoT clients
may resist deauth floods and require extended dwell times (10-15 min) to
capture a complete handshake. Broadcast deauth is worth trying when targeted
deauth fails, but the root issue is timing, not targeting.
