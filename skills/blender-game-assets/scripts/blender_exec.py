#!/usr/bin/env python3
"""Run Python inside the live Blender through the Blender Lab MCP add-on socket.

Usage:
    blender_exec.py [--host H] [--port N] [--timeout S] [--raw] file1.py [file2.py ...]

The files are concatenated in order (put bpy_lib.py first) and executed in
Blender's main thread. The code must assign a dict to `result`. Prints the JSON
response ({"status", "result", "stdout"}); with --raw prints only `result`.
Exit code 1 when Blender reports an error.
"""
import argparse
import json
import socket
import sys


def run(code, host="127.0.0.1", port=9876, timeout=1800):
    payload = json.dumps({"type": "execute", "code": code, "strict_json": False}).encode() + b"\0"
    with socket.create_connection((host, port), timeout=timeout) as s:
        s.sendall(payload)
        buf = bytearray()
        while b"\0" not in buf:
            chunk = s.recv(65536)
            if not chunk:
                break
            buf.extend(chunk)
    return json.loads(bytes(buf).split(b"\0", 1)[0])


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("files", nargs="+")
    ap.add_argument("--host", default="127.0.0.1")
    ap.add_argument("--port", type=int, default=9876)
    ap.add_argument("--timeout", type=float, default=1800)
    ap.add_argument("--raw", action="store_true", help="print only the result dict")
    a = ap.parse_args()
    code = "\n\n".join(open(f, encoding="utf-8").read() for f in a.files)
    resp = run(code, a.host, a.port, a.timeout)
    out = resp.get("result") if a.raw and resp.get("status") == "ok" else resp
    print(json.dumps(out, indent=1, ensure_ascii=False))
    sys.exit(0 if resp.get("status") == "ok" else 1)


if __name__ == "__main__":
    main()
