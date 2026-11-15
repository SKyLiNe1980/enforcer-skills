#!/usr/bin/env python3
"""
Drop-in replacement for wlancap2wpasec — upload captures to wpa-sec.stanev.org
using the current two-step session-based flow. stdlib-only, no dependencies.

Usage:
    python3 wpasec_upload.py -k <32-char-hex-key> capture.pcapng
    python3 wpasec_upload.py -k <key> *.pcapng
    python3 wpasec_upload.py -k <key> -R capture.pcapng  # remove after success
    python3 wpasec_upload.py --dry-run *.cap
    python3 wpasec_upload.py -s -k <key>   # save key to ~/.wpasec

The old wlancap2wpasec (hcxtools) is broken: it sends the key as a Cookie header
in a single POST to / with field name 'file'. The site now requires:
  1. POST key as form-urlencoded to /?submit (sets session cookie)
  2. POST file as multipart to /?submit with field name 'webfile' + session cookie
"""

import argparse
import os
import re
import sys
import time
from pathlib import Path
from urllib.request import (
    Request,
    build_opener,
    HTTPCookieProcessor,
    HTTPRedirectHandler,
)
from urllib.parse import urlencode
from http.cookiejar import CookieJar

WPASEC_URL = "https://wpa-sec.stanev.org"
WPASEC_SUBMIT = f"{WPASEC_URL}/?submit"
KEY_FILE = Path.home() / ".wpasec"


def read_key(filepath=KEY_FILE):
    try:
        line = filepath.read_text().strip().splitlines()[0].strip()
        if re.fullmatch(r"[0-9a-fA-F]{32}", line):
            return line.lower()
    except (FileNotFoundError, IndexError):
        pass
    return None


def resolve_key(args):
    key = args.key or os.environ.get("WPASEC_KEY") or read_key()
    if not key:
        print("No wpa-sec key. Use -k, WPASEC_KEY, or save to ~/.wpasec")
        sys.exit(1)
    if not re.fullmatch(r"[0-9a-fA-F]{32}", key):
        print(f"Invalid key format (need 32 hex chars): {key}")
        sys.exit(1)
    return key.lower()


# ── urllib 302 handling ─────────────────────────────────────────────────
# CRITICAL: Python's HTTPRedirectHandler normally FOLLOWS 302 redirects.
# To stop following, you override redirect_request() to return None.
# BUT returning None from redirect_request() causes http_error_302() to
# return None, which the default error handler treats as an unhandled
# redirect and raises HTTPError. The fix: ALSO override http_error_302()
# to return the response object (fp) directly, treating 302 as success.

class StopRedirect(HTTPRedirectHandler):
    def redirect_request(self, req, fp, code, msg, headers, newurl):
        return None
    def http_error_302(self, req, fp, code, msg, headers):
        return fp  # accept 302 as a valid response


def make_opener():
    cj = CookieJar()
    return build_opener(HTTPCookieProcessor(cj), StopRedirect()), cj


def establish_session(key, timeout=30):
    opener, cj = make_opener()
    data = urlencode({"key": key}).encode("ascii")
    req = Request(WPASEC_SUBMIT, data=data, method="POST")
    req.add_header("Content-Type", "application/x-www-form-urlencoded")
    try:
        resp = opener.open(req, timeout=timeout)
        # 302 = server accepts key and sets session cookie, 200 also seen
        if resp.status not in (200, 302):
            print(f"  Key POST returned HTTP {resp.status}")
            return None
    except Exception as e:
        print(f"  Key POST failed: {e}")
        return None
    return opener


def upload_file(opener, filepath):
    path = Path(filepath)
    if not path.is_file():
        print(f"  SKIP: not a file: {filepath}")
        return None
    if path.stat().st_size == 0:
        print(f"  SKIP: empty file: {filepath}")
        return None

    boundary = f"----wpasec{int(time.time())}"
    file_bytes = path.read_bytes()
    body = (
        f"--{boundary}\r\n"
        f'Content-Disposition: form-data; name="webfile"; filename="{path.name}"\r\n'
        f"Content-Type: application/octet-stream\r\n\r\n"
    ).encode("latin-1") + file_bytes + f"\r\n--{boundary}--\r\n".encode("latin-1")

    req = Request(WPASEC_SUBMIT, data=body, method="POST")
    req.add_header("Content-Type", f"multipart/form-data; boundary={boundary}")
    try:
        resp = opener.open(req, timeout=120)
        return resp.read().decode("utf-8", errors="replace")
    except Exception as e:
        print(f"  FAILED: {e}")
        return None


def parse_response(body):
    if not body:
        return "(empty)"
    text = re.sub(r"<[^>]+>", " ", body)
    text = re.sub(r"\s+", " ", text).strip()
    m = re.search(r"ESSID[^:]*:\s*(\S.*)", text)
    if m:
        return f"ESSID: {m.group(1).strip()}"
    for phrase in [
        "already submitted",
        "successfully uploaded",
        "not a valid capture",
        "submitted successfully",
    ]:
        idx = text.lower().find(phrase)
        if idx >= 0:
            start = max(0, idx - 10)
            end = min(len(text), idx + len(phrase) + 70)
            return text[start:end].strip()
    return text[:180]


def main():
    ap = argparse.ArgumentParser(description="Upload WPA captures to wpa-sec.stanev.org")
    ap.add_argument("files", nargs="*", help="Capture file(s)")
    ap.add_argument("-k", "--key", help="32-char wpa-sec hex key")
    ap.add_argument("-R", "--remove", action="store_true",
                    help="Remove file after success")
    ap.add_argument("-n", "--dry-run", action="store_true",
                    help="Preview only (no key needed)")
    ap.add_argument("-s", "--save-key", action="store_true",
                    help="Save -k value to ~/.wpasec")
    ap.add_argument("--stdin", action="store_true",
                    help="Read file list from stdin (one per line)")
    args = ap.parse_args()

    files = list(args.files)
    if args.stdin:
        files.extend(line.strip() for line in sys.stdin if line.strip())

    if args.save_key:
        key = args.key or os.environ.get("WPASEC_KEY")
        if not key or not re.fullmatch(r"[0-9a-fA-F]{32}", key):
            print("--save-key needs a valid key via -k or WPASEC_KEY")
            sys.exit(1)
        KEY_FILE.parent.mkdir(parents=True, exist_ok=True)
        KEY_FILE.write_text(key.lower() + "\n")
        print(f"Key saved -> {KEY_FILE}")
        if not files:
            return

    if args.dry_run:
        print(f"DRY RUN - {len(files)} file(s):")
        for f in files:
            print(f"  {f}")
        return

    key = resolve_key(args)

    print(f"-> {WPASEC_URL}")
    opener = establish_session(key)
    if opener is None:
        print("Session failed - check your key and network.")
        sys.exit(1)
    print("  Session OK\n")

    ok, fail = 0, 0
    for fp in files:
        fname = Path(fp).name
        print(f"  {fname} ...", end=" ", flush=True)
        body = upload_file(opener, fp)
        if body is None:
            fail += 1
            continue

        print(parse_response(body))

        lower = body.lower()
        if "not a valid capture" in lower:
            fail += 1
        else:
            ok += 1
            if args.remove:
                try:
                    Path(fp).unlink()
                    print(f"    (removed)")
                except OSError:
                    pass

    print(f"\n{ok} ok  |  {fail} failed  |  {len(files)} total")


if __name__ == "__main__":
    main()
