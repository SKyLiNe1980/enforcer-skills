---
name: s10-wifi-interface-management
description: Managing Alfa AWUS051NH/AWUS036NH interfaces on S10+ with Gemster Kernel. Covers interface availability, rename quirks, and Android WiFi HAL conflicts.
---

# S10+ WiFi Interface Management

## Interface Layout
The S10+ has multiple WiFi interfaces exposed by the Gemster Kernel:
- `wlan0`, `wlan1` — Internal phone WiFi (Android managed, leave alone)
- `ext2`, `ext3` — External Alfa adapters (AWUS036NH, AWUS051NH)

## Rename Quirks
Renaming interfaces (`ip link set ext2 name wlan2`) causes issues:
- **Many tools can't see renamed interfaces** — they disappear from `iwconfig`/`airmon-ng` listing
- **Zero traffic after rename** — interface silently drops all frames
- **Fix**: `ifdown <iface> && ifup <iface>` to reset, or replug USB adapter
- **Wait 3-5 seconds** after replug before using the interface

## Adapter Comparison

| Feature | AWUS036H | AWUS036NH | AWUS051NH |
|---------|----------|-----------|-----------|
| Range/Sensitivity | Best (causes channel bleed) | Good | Mid |
| Injection | Good | Good | Mid |
| TxPower in Monitor | Refuses | Works | Mixed |
| PMKID Capture | Misses M2/M3 frames | Clean | Clean |
| Reliability | Most reliable | Reliable | Least |
| Quirks | Channel bleed on passive | None | Occasional weirdness |
| Best Use | Active deauth/handshake | Passive PMKID | Backup/roaming |

**Preferred:** 036H for active attacks, 036NH for passive PMKID collection.
- **Experiment strategy**: Keep one adapter renamed (wlan2, hidden from Android) and one normal (ext3, for tools that expect it). Best of both worlds.

## Android WiFi HAL Conflicts
- Android's WiFi HAL reclaims interfaces when wpa_supplicant touches them
- **Do NOT connect to APs from S10+** — Android fights for routing control
- S10+ roles: **monitor mode only** (capture, deauth, PMKID)
- **Use Vye for managed connections** (authenticate to APs, get IPs)

## Recovery
If interfaces vanish after walking near your own WiFi or after failed connections:
1. `ip link show | grep ext` — check what's alive
2. Replug USB adapter if interface missing
3. `airmon-ng check kill` if wpa_supplicant conflict
4. Wait 5 seconds, then `airmon-ng start <iface>` to put back in monitor

## Adapter Profiles
| Adapter | Sensitivity | TX Power | Injection | PMKID Quality | Quirks |
|---------|------------|----------|-----------|---------------|--------|
| AWUS036H | Best range | Won't change in monitor | Good | Sometimes misses M2/M3 | Favorite overall |
| AWUS036NH | Good | Changes freely | Good | Clean | Most reliable |
| AWUS051NH | Mid | Mid | Mid | Mid | Nothing standout |

- **AWUS036H**: High sensitivity = great range but catches adjacent-channel bleed (e.g., Ziggo AP EAPOL frames bleeding into passive PMKID captures on channel 6). Filter by BSSID with `hcxdumptool --filterlist_ap=<file>` to exclude strong adjacent APs. Use `airodump-ng --bssid <target> -c <channel>` to lock onto a single channel.
- **Passive PMKID capture pitfall**: hcxdumptool in passive mode on the 036H may capture duplicate EAPOL handshakes from strong adjacent APs. The resulting `.22000` file will contain the same hash repeated many times. Fix: `sort -u captures.22000 > deduped.22000` before uploading to wpa-sec. Also apply to `.cap`/`.pcapng` with `hcxhashtool`.
- **PMKID dedup rule**: Always `sort -u` on `.22000` files before upload. Duplicate hashes waste cracking resources.
- **HCXDumpTool**: Use `--ignore_stale` to skip already-seen PMKIDs during long-running passive captures.

## WPA Attack Methodology — Pitfalls
- **ARP replay (`aireplay-ng -3`) is WEP-era**. It generates IVs for WEP cracking. Does NOT work on WPA/WPA2/WPA3. Do not suggest this for WPA targets.
- **For WPA**: deauth (`-0`) forces reconnection and captures the 4-way handshake. That's it. No injection needed beyond deauth.

## Podroid Alternative (S25 Ultra)
See [references/podroid-mobile-capture.md](references/podroid-mobile-capture.md) — S25 with Alpine VM + Alfa adapter for root-free mobile WiFi capture. Use as dedicated SIGINT node alongside S10+.
