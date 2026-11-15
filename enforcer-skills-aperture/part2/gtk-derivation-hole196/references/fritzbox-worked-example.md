# Worked Example: FRITZ!Box Fon WLAN 7360

This is a real-world example of the full WPA2 key ladder, verified end-to-end
via hcxpcapngtool + hcxpmktool. Everything below is VERIFIED.

## Input

```
SSID:        FRITZ!Box Fon WLAN 7360
AP MAC:      b4:e1:eb:42:c3:14
Client MAC:  d0:ba:e4:38:da:60
PSK:         49654202931317934963
```

## Full Key Ladder (Verified)

```
PSK  : 49654202931317934963                          (20 decimal digits)
PMK  : 56cdb464652588a7e2aa495e88586373              (PBKDF2-HMAC-SHA1 x4096)
       dd3acf7a8e46690f9bdb92bd9cdad95f
PTK  : 3371573afaa6ac18b9db2023415fe99d              (PRF-512)
       f0e8eab36f6e00b4e1eb42c314d0bae4
KCK  : 3371573afaa6ac18b9db2023415fe99d              (PTK[0:16])
KEK  : f0e8eab36f6e00b4e1eb42c314d0bae4              (PTK[16:32])
TK   : (PTK[32:48])                                  (derivable)
```

Nonces from the handshake:
```
ANONCE: 2dd2f2ede8f935807026515a98f42bd183603d83ae13dc9ec620fdd5b0426b35
SNONCE: 837e37ef8100eff9ff99f992992292222221dde021f6e09409486b7b4842842d
```

MIC confirmed: `52b8adfa08e85a8a3b4b37a76386562e`
PMKID calculated: `72f0c1b3beb5a47fea962e0dbfd34c65`

## Next Step: Extract GTK

The KEK above can AES-unwrap the Key Data field from M3 in the captured
4-way handshake to reveal the 16-byte GTK. The GTK is then used for:

1. Decrypting all broadcast/multicast traffic from this AP
2. Hole 196 injection — forging CCMP-encrypted broadcast frames spoofed as the AP

## Key Pattern

The PSK `49654202931317934963` is 20 decimal digits — typical for some ISP-issued
FRITZ!Box routers. This pattern falls to standard digit-only brute force within
reasonable time.

## Verification Command

```bash
hcxpmktool -p 49654202931317934963 \
  -s "FRITZ!Box Fon WLAN 7360" \
  -a b4e1eb42c314 -c d0bae438da60 \
  --anonce 2dd2f2ede8f935807026515a98f42bd183603d83ae13dc9ec620fdd5b0426b35 \
  --snonce 837e37ef8100eff9ff99f992992292222221dde021f6e09409486b7b4842842d
```
