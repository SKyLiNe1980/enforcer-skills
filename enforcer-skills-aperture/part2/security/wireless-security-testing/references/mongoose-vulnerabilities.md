# Mongoose Embedded Library Vulnerabilities (CVE-2026-5244/5245/5246)

Evilsocket research, disclosed 2026-04-02. Three independent preauth vulnerabilities in Mongoose
v7.0–v7.20, a single-file C embedded network library deployed on hundreds of millions of IoT
devices (Siemens, Schneider Electric, Broadcom, Bosch, Google, Samsung, Qualcomm, LG, ZTE).

Vulnerable commit: `eefec28b50bd9b2f08efd2477d033907f27cd837` (Mongoose v7.20).
Fixed in v7.21 (2026-04-01).

## CVE-2026-5246 — mTLS Authentication Bypass (CVSS 5.6 Medium)

**File:** `src/tls_builtin.c:1526-1528`

When the CA certificate uses a P-384 (secp384r1) ECDSA key, signature verification returns
success without performing any check:

```c
} else if (issuer->pubkey.len == 96) {
    MG_VERBOSE(("ignore secp386 for now"));
    return 1;  // SUCCESS — no verification at all
}
```

Any client cert is accepted. If a Mongoose mTLS server uses a P-384 CA, authentication
is completely bypassed. Does NOT apply to RSA CAs — only ECDSA P-384.

**Target applicability:** LG webOS TV port 3001 (mTLS with RSA 2048 cert → RSA path, this
bypass doesn't apply directly). Unknown whether ZTE-Home uses ECDSA CA.

## CVE-2026-5244 — TLS Heap Buffer Overflow → Preauth RCE (CVSS 7.3 High)

**File:** `src/tls_builtin.c:1645`

During certificate parsing in the TLS handshake, the client certificate's RSA public key
is copied into a fixed 528-byte buffer with NO bounds check:

```c
memmove(tls->pubkey, ci->pubkey.buf, ci->pubkey.len);
//       [528 bytes]     [attacker-controlled from X.509 DER]
```

`ci->pubkey.len` is set at line 1459 from the DER-encoded certificate:
```c
cert->pubkey = mg_str_n((char *) pki_key.value + 1, pki_key.len - 1);
```

An 8192-bit RSA key produces ~1030 bytes → 502-byte heap overflow past `tls_data` struct.

**Exploitation path:**
- `tls_data` is heap-allocated via `mg_calloc(1, sizeof(struct tls_data))` (line 2340)
- The overflow smashes whatever heap object follows `tls_data`
- On MIPS Linux with `READ_IMPLIES_EXEC` (executable heap), shellcode in the cert payload
  is directly executable
- Target function pointer: `mg_connection->fn` (the event handler, called after cert parsing)
- Attack triggers during TLS handshake, before any HTTP request — fully preauth

**Target applicability:**
- LG webOS TV port 3001 (SSL/mTLS): HIGH — Mongoose httpd with TLS, but needs `MG_TLS_BUILTIN`
- ZTE-Home: UNKNOWN — need to check if HTTPS management port exists with Mongoose TLS

**Impact:** On hardened targets (ASLR, NX), exploitation requires info leak. On embedded
MIPS/ARM with no hardening (the norm), single-shot preauth RCE as root.

## CVE-2026-5245 — mDNS Stack Buffer Overflow → Preauth RCE (CVSS 5.6 Medium)

**File:** `src/dns.c:371, 388`

The mDNS PTR query handler packs four DNS records (PTR + SRV + TXT + A) into a fixed
282-byte stack buffer:

```c
uint8_t buf[sizeof(struct mg_dns_header) + 256 + sizeof(mdns_answer) + 4];
// = 12 + 256 + 10 + 4 = 282 bytes
```

The TXT record is copied without bounds checking:
```c
memcpy(p, r->txt.buf, r->txt.len);  // NO BOUNDS CHECK (line 371)
```

With standard IoT TXT metadata (~450 bytes of firmware version, model, serial, capabilities):
```
total = 82 + 10 + 2×63 + 450 = 668 bytes → 386-byte stack overflow
```

**Attack:** Single 34-byte UDP packet to 224.0.0.251:5353 (mDNS multicast). On MIPS with
`-z execstack` (common on embedded Linux), saved return address is overwritten with
shellcode address → RCE.

**Target applicability:**
- ZTE-Home device: HIGH — Mongoose confirmed on port 9080, mDNS almost certainly compiled in
- LG webOS TV: HIGH — Mongoose httpd on port 3000, webOS heavily uses mDNS for device discovery

**Kick:** This is a single UDP multicast packet → root RCE. No TLS, no auth, no connection.
Just fire and wait for the callback.

## Real-World Target Mapping (Vinay's Network)

### ZTE-Home (KPN)
```
9080/tcp  Mongoose httpd  (application/json API)
9011/tcp  Dropbear sshd 2019.78
49152/tcp UPnP 1.6.22
```
Attack vector: mDNS stack overflow (CVE-2026-5245) via single UDP packet.

### LG webOS TV (55UP77006LB)
```
3000/tcp  LG smart TV http service (likely Mongoose)
3001/tcp  SSL/HTTP (mTLS, LGE SSG CA, RSA 2048)
1974/tcp  UPnP DIAL
7000/tcp  AirTunes rtspd
9080/tcp  NRDP/2020.1.7.0
```
Attack vector: TLS heap overflow (CVE-2026-5244) on port 3001.

**Standby behavior:** LG webOS retracts ALL services when entering deep standby (~15 min).
Wake-on-LAN required to bring them back. Quick Start+ setting keeps SoC alive 24/7.

## Recon Methodology for Mongoose Targets

1. **nmap service scan:** `nmap -sV -p 3000,3001,8000,8080,8443,9080,9443 <target>`
   — Mongoose httpd banners are distinctive: `Mongoose httpd` or `LG smart TV http service`
2. **mDNS probe:** `avahi-browse -a -r -t` or send PTR query to 224.0.0.251:5353
   — Mongoose mDNS responses include rich TXT records (model, firmware, features)
3. **TLS fingerprint:** `sslscan <target>:3001` or `nmap --script ssl-enum-ciphers`
   — Check for Mongoose `MG_TLS_BUILTIN` cipher suite characteristics
4. **Version confirmation:** HTTP OPTIONS on Mongoose endpoints, check response headers
   for Mongoose version strings in `Server` header

## Source Code Availability

Vulnerable Mongoose v7.20 cloned to `/root/mongoose-vuln/` at commit `eefec28b50bd9`.
Key files:
- `src/tls_builtin.c` — TLS implementation (lines 1645, 1526 for vulns)
- `src/dns.c` — mDNS handler (lines 371, 388 for stack overflow)
- `mongoose.h` — struct definitions (mg_connection, mg_dns_header, tls_data at line 92)

No public PoC released by evilsocket. Writeup provides enough detail to reconstruct.

## Pitfalls

- LG TV enters deep standby after ~15 min — all services vanish. Use WoL to revive.
- mDNS stack overflow requires TXT records large enough to overflow — not all devices
  register rich TXT metadata.
- TLS heap overflow needs `MG_TLS_BUILTIN` — if Mongoose was compiled with OpenSSL/mbedTLS,
  this code path doesn't execute.
- MIPS exploitation depends on `READ_IMPLIES_EXEC` or `-z execstack` — ARM targets may
  need different shellcode and exploitation technique.
