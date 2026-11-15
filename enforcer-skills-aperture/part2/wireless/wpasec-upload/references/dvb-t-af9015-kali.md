# DVB-T Stick Resurrection on Kali — AF9015 (TerraTec Cinergy T RC MKII)

## Device
- **USB ID**: 0ccd:0097 — TerraTec Cinergy T RC MKII
- **Chipset**: AF9015 (USB bridge) + AF9013 (frontend) + TDA18218 (tuner)
- **Kernel tested**: Kali 6.8.11-686-pae (32-bit)
- **Shows as**: HID keyboard (the IR remote), DVB tuner on interface 0 (Vendor Specific Class)

## Problem
Kali's kernel doesn't ship the `dvb-usb-af9015.ko` module. `modprobe dvb-usb-af9015` fails with:
```
FATAL: Module dvb-usb-af9015 not found in directory /lib/modules/...
```

## Solution

### 1. Find the .ko
The module might exist as a stray file from a previous install or cross-compile:
```
find / -name "*af9015*.ko*" 2>/dev/null
```
If not found, obtain one compiled for your kernel version.

### 2. Get firmware
```
# From OpenELEC/LibreELEC repos or kernel-firmware packages
cp dvb-usb-af9015.fw /lib/firmware/
```

### 3. Load with insmod (NOT modprobe)
`modprobe` enforces vermagic/symbol checks and will reject mismatched modules.
`insmod` loads the `.ko` directly regardless:
```
sudo insmod /path/to/dvb-usb-af9015.ko
```
Dependencies (`dvb-core`, `dvb-usb`) must be loaded first — use `modprobe` for those:
```
sudo modprobe dvb-core dvb-usb
```

### 4. Verify
```
ls /dev/dvb/adapter0/   # demux0, dvr0, frontend0, net0
dmesg | grep "successfully initialized"
```
Successful init output:
```
dvb_usb_v2: 'TerraTec Cinergy T Stick RC' successfully initialized and connected
af9013: Afatech AF9013 successfully attached
tda18218: NXP TDA18218HN successfully identified
```

## SDR Use
The AF9015 standard driver exposes `/dev/dvb/adapter0/frontend0` which SDRangel and other DVB wrapper tools can read for raw IQ. No custom SDR kernel module needed.

**SNOWLeo-SDR note**: The `af9015.c` in the SNOWLeo-SDR repo is identical to upstream — no SDR patches in the kernel module. The SDR capability is all userspace (V4L2/DVB wrapper layer).

**SDRangel compile issues on 32-bit**: Qt6 requires SSE3 instructions. The Pentium M Dothan core (Vye) only supports up to SSE2. SDRangel will fail to compile with SSE3-related errors in libhamlib/Qt6 dependencies. Workaround: run SDRangel remotely and stream IQ from the Vye via netcat.

## Pitfalls
- `modprobe` will NOT load a stray `.ko` — use `insmod` directly
- **Symbol CRC mismatch**: The running kernel's `dvb-usb-v2.ko` exports symbols with different CRCs than what the package's `af9015.ko` was built against. Solution: load BOTH `dvb_usb_v2.ko` AND `dvb-usb-af9015.ko` from the SAME kernel package deb. Unload the running dvb-usb-v2 first, then insmod the package's dvb_usb_v2.ko followed by af9015.ko.
- **`insmod` can't load `.ko.xz`**: Decompress first: `xz -dk < file.ko.xz > file.ko`
- Firmware must match the driver version (5.24.0.0 for this build)
- The IR receiver registers as `/dev/lirc0` and `/dev/input/event*`
- Without kernel headers, you can't compile from source — find prebuilt `.ko` or install headers first
- `dpkg -L linux-image-...` may list the `.ko.xz` even when the file is missing from disk — verify with `dpkg --verify linux-image-...`
- **Old kernel debs**: When Kali repos drop a kernel version, check `old.kali.org/kali/pool/main/l/linux/` for the .deb files
- **Vye /tmp is 1GB tmpfs**: Kernel source tarballs (~600MB+) fill it instantly. Use `/home/hermes/` (persistent) for kernel builds
- hcxhash2cap appends `_0` suffix when output `.cap` file already exists (tempfile stub collision) — pre-delete the stub before conversion
- Kernel headers for 686-pae on older Kali require manual `.deb` download when upstream repos drop the version
- **`apt` may be blocked by SSE3 dependency**: Installing Qt6/SDRangel on a Pentium M triggers SSE3-support package dependency that can't be satisfied. Purge affected packages: `dpkg --purge --force-all libqt6webenginecore6 qt6-webengine-dev ...` then `apt --fix-broken install`
