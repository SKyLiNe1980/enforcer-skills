#!/usr/bin/env python3
"""Decode hc22000 hashcat hash files to human-readable network names.

Format: WPA*02*MIC*MAC_AP*MAC_STA*ESSID_HEX*ANONCE*EAPOL*NC

Usage:
    python3 decode_hashes.py /tmp/handshakes.hc22000
    python3 decode_hashes.py /tmp/handshakes.hc22000 --brief
"""

import sys

def mac(bytes_hex):
    return ':'.join([bytes_hex[j:j+2] for j in range(0, 12, 2)]).upper()

def decode(hashes_file, brief=False):
    with open(hashes_file) as f:
        hashes = [l.strip() for l in f if l.strip()]

    print(f"Total hashes: {len(hashes)}\n")

    for i, h in enumerate(hashes, 1):
        parts = h.split('*')
        if len(parts) < 9:
            print(f"{i}. <malformed: {len(parts)} fields>")
            continue

        mac_ap = mac(parts[3])
        mac_sta = mac(parts[4])
        essid_hex = parts[5]

        try:
            essid = bytes.fromhex(essid_hex).decode('ascii')
        except Exception:
            essid = f"<non-ascii hex>"

        if brief:
            print(f"{i}. {essid:30s} AP:{mac_ap}")
        else:
            print(f"{i}. {essid}")
            print(f"   AP: {mac_ap}   Client: {mac_sta}")
            print(f"   MIC: {parts[2]}")

if __name__ == '__main__':
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(1)

    brief = '--brief' in sys.argv
    decode(sys.argv[1], brief)
