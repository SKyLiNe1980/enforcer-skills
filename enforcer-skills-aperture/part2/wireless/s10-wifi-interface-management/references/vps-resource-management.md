# VPS Resource Management

## EMBA Throttled Analysis
Run EMBA without melting the VPS using cgroups:

```bash
emba-limited firmware.bin
```

Wrapper script at `/usr/local/bin/emba-limited` enforces:
- 2 CPU cores max
- 8GB RAM max
- 8-hour timeout (auto-kill)
- All output saved to `/root/log/emba_<name>/`

Edit the script to adjust limits. Located at VPS.

## Capture Quality Checking
Before uploading to wpa-sec, verify captures have valid handshakes:

```bash
# Show captures with valid handshakes/PMKIDs
capcheck /sdcard/tools/wifite2/hs --valid-only

# Pipe to upload
find today/ -name "*.cap" | while read f; do capcheck "$f" --valid-only -q && echo "$f"; done | xargs wpasec-upload
```

Tool at `/root/bin/capcheck` — reports ESSID, BSSID, handshake count, PMKID presence per capture.

## EMBA Firmware Analysis (CPU-heavy)

EMBA firmware analysis can max out all CPU cores and RAM. Throttle with cgroups:

```bash
# Limit to 2 cores, 8GB RAM, 8-hour timeout
sudo cgcreate -g cpu,memory:/emba
sudo cgset -r cpu.max="200000 100000" /emba
sudo cgset -r memory.max=8G /emba
timeout 8h sudo cgexec -g cpu,memory:/emba ./emba -f firmware.bin -l /root/log/name
```

Wrapper script deployed at `/usr/local/bin/emba-limited` on VPS.

## After Penta Boys Sessions

Penta Boys leave containers and zombie processes running. Cleanup:
```bash
docker ps -q | xargs -r docker stop
docker ps -aq | xargs -r docker rm
```

Check for defunct PIDs: `ps aux | grep defunct`

## VPS Specs
- 4 cores, 16GB RAM, 200GB disk
- SSH: root@pwn.my.r00tb0x.online (key: ~/.ssh/hermes_vps)
- hashcat 7.1, hcxdumptool, rizin, rz-ghidra, Docker
