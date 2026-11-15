# Tool Fixes & Kernel Build Notes

## wpasec-upload: .22000 Conversion (hcxpcapngtool → hcxhash2cap)

hcxpcapngtool 7.1.0+ dropped the ability to convert `.22000` hash files
back to `.pcap`/`.pcapng`. It only does pcap → hash now, not reverse.

**The replacement**: `hcxhash2cap --pmkid-eapol` which converts `.22000` →
`.cap` files that wpa-sec.stanev.org accepts.

### Command
```bash
hcxhash2cap --pmkid-eapol input.22000 -c output.cap
```

### Script fix applied
Patched `/root/bin/wpasec-upload` to use `hcxhash2cap` instead of `hcxpcapngtool`.
The `-c` flag produces `.cap` files. hcxhash2cap may append `_0` / `_1` suffixes
for multi-hash files — the script now globs for `*.cap` variants after conversion.

### Verification
```bash
wpasec-upload --dry-run pmkid_file.22000  # " [.22000 → cap]"
```

## Out-of-Tree Kernel Module Build on Kali

### Scenario
A kernel module (e.g. `dvb-usb-af9015.ko`) listed by `dpkg -L` as installed
but actually missing from disk. `apt reinstall` fails because the package is
no longer in the Kali mirror (old kernel version). Need to build from source.

### Prerequisites
```bash
apt install linux-headers-$(uname -r)
```

### Step 1: Get source headers from kernel.org
The full kernel source is too large for a shallow clone on slow connections.
Download individual files from cgit:

```bash
KVER=v6.8.11
BASE="https://git.kernel.org/pub/scm/linux/kernel/git/stable/linux.git/plain"
curl -sLO "$BASE/drivers/media/usb/dvb-usb-v2/af9015.c?h=$KVER"
curl -sLO "$BASE/drivers/media/usb/dvb-usb-v2/af9015.h?h=$KVER"
```

**Pitfall**: kernel.org cgit raw URLs may return HTML error pages (8740 bytes)
instead of C source. The 8740-byte files all start with `<!DOCTYPE html>`.
Workaround: use `git clone --depth 1 --branch v6.8.11` on a machine with
faster internet (VPS), then SCP the needed files.

### Step 2: Collect ALL transitive header dependencies
af9015.h includes → dvb_usb.h → (more media headers) → tuner headers.
Full dependency chain for af9015:

```
drivers/media/usb/dvb-usb-v2/af9015.{c,h}
drivers/media/usb/dvb-usb-v2/dvb_usb.{h,common.h}
drivers/media/dvb-frontends/{af9013.h,af9013_priv.h,dvb-pll.h}
drivers/media/tuners/{mt2060.h,qt1010.h,tda18271.h,mxl5005s.h,tda18218.h,...}
include/media/*.h
```

Download the whole set from a VPS with a full kernel git clone:
```bash
cd /tmp/linux-6.8.11  # full git clone on VPS
tar czf dvb_full.tar.gz \
  drivers/media/dvb-core/*.[ch] \
  drivers/media/dvb-frontends/*.h \
  drivers/media/tuners/*.h \
  drivers/media/usb/dvb-usb-v2/*.[ch] \
  include/media/*.h \
  include/uapi/linux/dvb/*.h
scp dvb_full.tar.gz target:~/
```

### Step 3: Makefile for out-of-tree build
```makefile
KDIR := /lib/modules/$(shell uname -r)/build
obj-m := af9015.o
af9015-objs := drivers/media/usb/dvb-usb-v2/af9015.o

ccflags-y := -I$(src)/include -I$(src)/include/uapi \
             -I$(src)/drivers/media/dvb-core \
             -I$(src)/drivers/media/dvb-frontends \
             -I$(src)/drivers/media/tuners \
             -I$(src)/drivers/media/usb/dvb-usb-v2

default:
	$(MAKE) -C $(KDIR) M=$(PWD) modules
```

### Step 4: Build and load
```bash
sudo make -C /lib/modules/$(uname -r)/build M=$PWD modules
sudo modprobe dvb-core dvb-usb dvb-usb-v2
# Ensure firmware is in /lib/firmware/
sudo insmod af9015.ko
dmesg | tail -20   # check for "TerraTec Cinergy T Stick RC"
ls /dev/dvb/adapter0  # verify
```

### Common failures
- **"Unknown symbol in module" (err -2)**: Module.symvers CRC mismatch between
  built module and running kernel. Must copy `/lib/modules/$(uname -r)/build/Module.symvers`
  into the build directory before building, OR build BOTH the dependency module
  (dvb-usb-v2.ko) and the target module (af9015.ko) in the same tree.
- **HTML instead of C source**: kernel.org cgit anti-scraping. Use VPS git clone.
- **broken apt due to SSE3 dependency on Pentium M**: `dpkg --purge --force-all`
  the qt6 package that requires sse3-support, then `apt --fix-broken install`.

## DVB-T Stick as SDR (AF9015/AF9013/TDA18218)
- The TerraTec Cinergy T RC MKII (0ccd:0097) uses AF9015 bridge + AF9013 frontend + TDA18218 tuner
- SDRangel can read raw IQ from the standard DVB frontend API — no custom kernel module needed
- `dvb2iq` or `cat /dev/dvb/adapter0/dvr0` for headless IQ capture
- SNOWLeo-SDR patch set adds SDR support at FPGA level, not kernel module
- The stick covers 42-870 MHz via the TDA18218 tuner
