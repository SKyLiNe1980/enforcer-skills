# TKIP Verification via Beacon Analysis

airo dump-ng CSV output truncates the cipher field. "WPA2 CCMP PSK" does NOT mean TKIP is absent. Only beacon-level IEs reveal the truth.

## Beacon IE Structure

### RSN Information Element (Tag 48)
WPA2 uses this IE. Check the Group Cipher Suite and Pairwise Cipher Suite List:

```
Tag: RSN Information (48)
  Group Cipher Suite: 00:0f:ac TKIP (type 2)    <-- GROUP traffic uses TKIP
  Pairwise Cipher Suite List: AES (CCM) + TKIP   <-- Clients CAN use TKIP
```

OUI breakdown:
- `00:0f:ac` = IEEE 802.11
- Type 2 = TKIP
- Type 4 = AES (CCMP)

### WPA Information Element (Tag 221, OUI 00:50:f2)
WPA1 uses this vendor-specific IE. Same cipher suite structure:

```
Tag: Vendor Specific (221), OUI: 00:50:f2 (Microsoft)
  Type: WPA Information Element (0x01)
  Multicast Cipher Suite: TKIP (type 2)
  Unicast Cipher Suite List: AES (CCM) + TKIP
```

OUI breakdown:
- `00:50:f2` = Microsoft Corp.
- Type 2 = TKIP
- Type 4 = AES (CCMP)

## TKIP Attack Relevance

| Finding | Attack Surface |
|---------|---------------|
| Group cipher = TKIP | All broadcast/multicast is TKIP-encrypted, regardless of client cipher |
| Pairwise includes TKIP | Clients CAN negotiate TKIP — tkiptun-ng, Beck-Tews, chopchop viable |
| Only WPA IE, no RSN | Pure WPA1 — older hardware, higher chance of weak defaults |
| Both RSN + WPA IE with TKIP | Dual-stack — broad attack surface |

## Prerequisites for TKIP Attacks

All TKIP attacks (tkiptun-ng, chopchop, Beck-Tews) need at least ONE valid encrypted data frame. Without it:
- Nothing to replay
- Nothing to chop
- MIC countermeasure attack can't trigger

If an AP advertises TKIP but has zero clients and zero data traffic, it's a dead end unless you can artificially generate encrypted traffic (extremely difficult without the key).

## Real-World Example: RedWine (WPA1 with TKIP)

```
Beacon from 22:3B:F3:31:D9:46 (RedWine):
  WPA Version: 1
  Multicast Cipher: TKIP
  Unicast Ciphers: AES-CCMP + TKIP
  AKM: PSK
  No RSN IE (pure WPA1)
  Chipset: Atheros (OUI 00:03:7f)
  Rates: 802.11b/g only (no n/ac/ax)
```

Result: 0 clients, 0 data frames. Fake auth succeeded (AID:1) but no traffic generated. TKIP attack surface confirmed but no encrypted data to work with.

## Real-World Example: Ziggo8528082 (WPA2 with dual TKIP)

```
RSN IE: Group cipher TKIP, Pairwise AES-CCMP + TKIP
WPA IE: Multicast TKIP, Unicast AES-CCMP + TKIP
```

Dual-stack TKIP across both WPA1 and WPA2. Same dead-end: 0 clients, 0 data.
