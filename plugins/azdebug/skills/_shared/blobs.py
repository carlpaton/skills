#!/usr/bin/env python3
"""Read-only Azure Blob helper. Only lists, downloads and reads blobs.

Run with -I:
  python3 -I blobs.py list     --account A --container C [--prefix P] [--auth-mode login|key]
  python3 -I blobs.py pull     --account A --container C [--prefix P] --dest DIR [--auth-mode ...]
  python3 -I blobs.py show     --account A --container C --blob NAME [--max-bytes N] [--shape] [--auth-mode ...]

Default auth is `login` (your Entra ID, needs a Storage Blob Data Reader role). `key` makes az
fetch the account key with your management permissions: use it only after the user agreed.
Keys are never printed. `pull` never overwrites existing files.
"""
import argparse
import json
import os
import subprocess
import sys
import tempfile


def az(args, auth):
    cmd = ["az", "storage", "blob", *args, "--auth-mode", auth, "-o", "json"]
    r = subprocess.run(cmd, capture_output=True, text=True)
    if r.returncode != 0:
        err = r.stderr.strip()
        if "required permissions" in err or "AuthorizationPermissionMismatch" in err:
            err = ("No blob data role on this account for the signed-in user. Ask the user to grant "
                   "Storage Blob Data Reader, or to approve --auth-mode key.")
        sys.exit(err or "az failed")
    return r.stdout


def blobs(a):
    q = "[].{name:name,size:properties.contentLength,modified:properties.lastModified}"
    out = az(["list", "--account-name", a.account, "-c", a.container, "--prefix", a.prefix,
              "--query", q], a.auth_mode)
    return json.loads(out or "[]")


def shape(v, depth=0):
    """Structure only: keys and types, with string lengths, never the values."""
    if isinstance(v, dict):
        return {k: shape(x, depth + 1) for k, x in v.items()} if depth < 4 else "{...}"
    if isinstance(v, list):
        return [f"{len(v)} items", shape(v[0], depth + 1)] if v and depth < 4 else f"[{len(v)} items]"
    if isinstance(v, str):
        return f"str({len(v)})"
    return type(v).__name__ if v is None else f"{type(v).__name__}={v}"


def main():
    p = argparse.ArgumentParser()
    p.add_argument("cmd", choices=["list", "pull", "show"])
    p.add_argument("--account", required=True)
    p.add_argument("--container", required=True)
    p.add_argument("--prefix", default="")
    p.add_argument("--blob")
    p.add_argument("--dest")
    p.add_argument("--max-bytes", type=int, default=20000)
    p.add_argument("--shape", action="store_true", help="show: print keys and types only, no values")
    p.add_argument("--auth-mode", choices=["login", "key"], default="login")
    a = p.parse_args()

    if a.cmd == "list":
        rows = blobs(a)
        print("modified(UTC)\tbytes\tname")
        for b in sorted(rows, key=lambda b: b["modified"] or ""):
            print(f"{b['modified']}\t{b['size']}\t{b['name']}")
        print(f"# {len(rows)} blobs, {sum(b['size'] or 0 for b in rows)} bytes")
    elif a.cmd == "pull":
        if not a.dest:
            sys.exit("--dest is required")
        os.makedirs(a.dest, exist_ok=True)
        rows = blobs(a)
        done = skipped = 0
        for b in rows:
            target = os.path.join(a.dest, b["name"])
            if os.path.exists(target):
                skipped += 1
                continue
            os.makedirs(os.path.dirname(target), exist_ok=True)
            az(["download", "--account-name", a.account, "-c", a.container, "-n", b["name"],
                "-f", target, "--no-progress"], a.auth_mode)
            done += 1
        print(f"downloaded {done}, skipped {skipped} existing, into {a.dest}")
    else:
        if not a.blob:
            sys.exit("--blob is required")
        with tempfile.TemporaryDirectory() as tmp:
            f = os.path.join(tmp, "blob")
            az(["download", "--account-name", a.account, "-c", a.container, "-n", a.blob,
                "-f", f, "--no-progress"], a.auth_mode)
            with open(f, encoding="utf-8", errors="replace") as fh:
                text = fh.read()
        if a.shape:
            try:
                print(json.dumps(shape(json.loads(text)), indent=2))
                return
            except ValueError:
                sys.exit("not JSON, cannot show shape")
        print(text[: a.max_bytes])
        if len(text) > a.max_bytes:
            print(f"\n# truncated at {a.max_bytes} of {len(text)} bytes", file=sys.stderr)


if __name__ == "__main__":
    main()
