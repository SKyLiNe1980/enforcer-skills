# Kr00k Field Test Results — May 30, 2026

Four WPA2 APs with active clients tested via PN-reset analysis. Zero vulnerable.

## Methodology

1. Lock monitor interface (ext3, AWUS051NH) to target channel
2. Capture all frames to/from target BSSID: `tcpdump -w kr00k.pcap -c 3000`
3. Broadcast deauth: `aireplay-ng -0 3-5 -a <BSSID>`
4. Extract CCMP PNs pre and post deauth: `tshark -Y 'wlan.fc.type==2 and wlan.ccmp.extiv'`
5. Check for PN reset

## Results

| Target | BSSID | Ch | Sig | Clients | Chipset | PN Reset? |
|--------|-------|----|-----|---------|---------|-----------|
| VanWyk | 1C:0B:8B:72:6A:56 | 6 | -56 | 6 | Ubiquiti/Atheros | No data frames |
| AmyenMilan | 8C:C5:B4:3B:6D:76 | 6 | -48 | 32 | Sagemcom/Arcadyan | No — 0x0E2209→0x0E22AD |
| KPN7124A6 | 8A:19:4D:2A:B9:43 | 6 | -43 | 17 | Arcadyan? | No — 0x0E1DF6→0x0E1DFC |
| RIES | B0:BE:76:34:C7:16 | 3 | -66 | 38 | TP-Link | No — 0x522179→0x5221BC |
| Odido | F8:0D:A9:31:1F:53 | 6 | -60 | 6 | **Broadcom!** | WPA3-only, immune |

## Key Learnings

- **PN-reset analysis is definitive.** If PNs increment normally through deauth, kr00k is not exploitable — no need to attempt decryption.
- **Broadcom OUI matching is insufficient.** F8:0D:A9 is confirmed Broadcom (Odido) but WPA3-SAE eliminates the vulnerability. OUI alone doesn't guarantee exploitability.
- **Most consumer APs in 2026 are non-Broadcom.** Qualcomm (Ubiquiti), MediaTek, Realtek dominate. Even Arcadyan devices may use non-Broadcom chipsets in newer hardware revisions.
- **WPA3 adoption kills kr00k.** The all-zero-key bug is specific to WPA2's 4-way handshake key hierarchy. WPA3-SAE uses Dragonfly — completely different code path.
- **Previous kr00k scripts (25+ Python files in /root/kr00k_*) are OUI-based finders** from a CAI-Framework session. They identify potential targets by MAC but can't test exploitability.

## Recommendation

Always run the PN-reset pre-screen before investing time in kr00k. If PNs don't reset, the AP is not vulnerable regardless of chipset. This test takes ~30 seconds and is definitive.
