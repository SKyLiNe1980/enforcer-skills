# hcxhash2cap — .22000 to .cap conversion

`hcxhash2cap` (hcxtools 7.1.0) converts hashcat-format hash files back to capture files.

## Usage
```bash
# Convert a .22000 PMKID/EAPOL hash file to a .cap file
hcxhash2cap --pmkid-eapol input.22000 -c output.cap

# Also supports deprecated formats:
hcxhash2cap --pmkid=input.16800 -c output.cap     # old PMKID (16800)
hcxhash2cap --hccapx=input.2500 -c output.cap     # old hccapx (2500)
hcxhash2cap --hccap=input.hccap -c output.cap     # ancient hccap
hcxhash2cap --john=input.john -c output.cap       # John the Ripper format
```

## Quirks

### _0 suffix
If the output file already exists, hcxhash2cap appends `_0` to avoid collision:
```
hcxhash2cap --pmkid-eapol test.22000 -c /tmp/out.cap
# Creates: /tmp/out_0.cap (if /tmp/out.cap already exists)
```

Workaround: delete the output file before running hcxhash2cap, or glob for `*.cap` variants after conversion.

### Multi-hash files
When a .22000 contains multiple hashes (different APs), hcxhash2cap may split them into separate files with `_0`, `_1` suffixes. All variants should be uploaded.

### Input format
The .22000 file must contain valid `WPA*01*` or `WPA*02*` prefixed hash lines. hcxhash2cap will silently skip invalid lines.

## Why not hcxpcapngtool?
hcxpcapngtool 7.1.0+ only accepts pcap/pcapng/cap as INPUT and outputs .22000 hash files. It does NOT do reverse conversion (hash → capture). This is a deliberate design change — use hcxhash2cap for the reverse direction.

## Related tools
- `hcxpcapngtool` — pcap/pcapng/cap → .22000 hash (forward)
- `hcxhashtool` — hash file filtering, deduplication, ESSID extraction
- `hcxpsktool` — PSK recovery from known passwords
