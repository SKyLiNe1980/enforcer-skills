# .22000 Hash File Upload to wpa-sec

## The Problem

hcxpcapngtool v7.1 dropped reverse conversion (.22000 hash → pcap capture).
This broke the wpasec-upload .22000 handling which relied on `hcxpcapngtool -o`.

wpa-sec.stanev.org does NOT accept .22000 hash files directly — they must
be converted to a capture format (.cap/.pcapng) first.

## The Fix: hcxhash2cap

`hcxhash2cap` can convert .22000 hash files BACK to .cap format:

```bash
hcxhash2cap --pmkid-eapol <input.22000> -c <output.cap>
```

This is the replacement for `hcxpcapngtool -o` in the reverse direction.

## Pitfall: _0 suffix

When the target output file already exists (e.g. a zero-byte tempfile stub
created by `tempfile.NamedTemporaryFile`), hcxhash2cap may write to
`<filename>_0.cap` instead of `<filename>.cap`. Fix: pre-delete the temp
stub before calling hcxhash2cap, or glob for `*.cap` variants after.

```python
tmp = tempfile.NamedTemporaryFile(suffix=".cap", delete=False)
tmp.close()
os.unlink(tmp.name)  # delete stub before hcxhash2cap writes

subprocess.run(["hcxhash2cap", "--pmkid-eapol", str(filepath), "-c", tmp.name])

# hcxhash2cap may write to requested path or _0 / _1 variants
candidates = sorted(glob.glob(tmp.name.replace(".cap", "*.cap")))
actual = tmp.name if tmp.name in candidates else candidates[0]
```

## Tool Version Note

hcxpcapngtool 7.1+ only does capture → hash (forward). The `-o` flag
outputs .22000 hash files. It does NOT accept .22000 as input.
`hcxhash2cap` is the dedicated reverse converter (hash → capture).

Both tools are from the hcxtools 7.1.0 package.
