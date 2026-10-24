#!/usr/bin/env python3
"""T147 / ADR-0035 section 1: object-local, deterministic string data symbols.

usage: check_string_symbols.py <axiom0> <tmp_dir> <repo_root>

For every program under tests/run/str and tests/run/parity/strings:
  * `axiom0 build --emit=obj` and `axiom0 build` run twice produce byte-identical files, and
    `axiom0 inspect --emit=obj` run twice does too (no heap address, counter or path in a name);
  * the object defines every `.Lstr.<f>.<k>` symbol exactly once as STATIC, has no undefined
    `.Lstr.*` symbol (no twin), and every literal starts on an 8-byte boundary (the previous literal was NUL-terminated and padded to 8).
"""

import glob
import os
import re
import struct
import subprocess
import sys

STR_RE = re.compile(rb"^\.Lstr\.\d+\.\d+$")


def run(cmd):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300)


def coff_symbols(data):
    machine, nsec, _ts, symptr, nsyms, _opt, _chars = struct.unpack_from("<HHIIIHH", data, 0)
    assert machine == 0x8664, "not an AMD64 COFF object"
    strtab = symptr + 18 * nsyms
    out = []
    i = 0
    while i < nsyms:
        rec = data[symptr + 18 * i: symptr + 18 * (i + 1)]
        name8, value, section, _type, storage, naux = struct.unpack("<8sIhHBB", rec)
        if name8[:4] == b"\0\0\0\0":
            off = struct.unpack("<I", name8[4:])[0]
            end = data.index(b"\0", strtab + off)
            name = data[strtab + off:end]
        else:
            name = name8.rstrip(b"\0")
        out.append((name, value, section, storage))
        i += 1 + naux
    return out


def build_twice(compiler, args, src, tmp, tag):
    blobs = []
    for n in range(2):
        out = os.path.join(tmp, "%s_%d.bin" % (tag, n))
        if os.path.exists(out):
            os.remove(out)
        r = run([compiler, "build"] + args + ["-o", out, src])
        if r.returncode != 0:
            raise SystemExit("FAIL: %s %s %s: rc=%d %s" % (compiler, args, src, r.returncode, r.stderr.decode("utf-8", "replace")))
        with open(out, "rb") as f:
            blobs.append(f.read())
    return blobs


def inspect_twice(compiler, src):
    outs = []
    for _ in range(2):
        r = run([compiler, "inspect", "--emit=obj", src])
        if r.returncode != 0:
            raise SystemExit("FAIL: inspect --emit=obj %s: rc=%d" % (src, r.returncode))
        outs.append(r.stdout)
    return outs


def main():
    compiler, tmp, root = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(tmp, exist_ok=True)
    programs = sorted(glob.glob(os.path.join(root, "tests", "run", "str", "*.ax"))
                      + glob.glob(os.path.join(root, "tests", "run", "parity", "strings", "*.ax")))
    if not programs:
        raise SystemExit("FAIL: no programs found")
    checked = 0
    for src in programs:
        rel = os.path.relpath(src, root)
        a, b = build_twice(compiler, ["--emit=obj"], src, tmp, "obj")
        if a != b:
            raise SystemExit("FAIL: %s: two `build --emit=obj` runs differ" % rel)
        a, b = build_twice(compiler, [], src, tmp, "exe")
        if a != b:
            raise SystemExit("FAIL: %s: two `build` runs differ" % rel)
        a, b = inspect_twice(compiler, src)
        if a != b:
            raise SystemExit("FAIL: %s: two `inspect --emit=obj` runs differ" % rel)
        # symbol hygiene on the built object and on the inspect output
        with open(os.path.join(tmp, "obj_0.bin"), "rb") as f:
            built = f.read()
        for label, data in (("build", built), ("inspect", a)):
            seen = set()
            for (name, value, section, storage) in coff_symbols(data):
                if not name.startswith(b".Lstr"):
                    continue
                if not STR_RE.match(name):
                    raise SystemExit("FAIL: %s (%s): string symbol %r is not .Lstr.<f>.<k>" % (rel, label, name))
                if section <= 0:
                    raise SystemExit("FAIL: %s (%s): undefined twin of %r" % (rel, label, name))
                if storage != 3:
                    raise SystemExit("FAIL: %s (%s): %r is not STATIC" % (rel, label, name))
                if value % 8 != 0:
                    raise SystemExit("FAIL: %s (%s): %r at offset %d is not 8-byte aligned (literal not padded to 8)"
                                     % (rel, label, name, value))
                if name in seen:
                    raise SystemExit("FAIL: %s (%s): %r defined twice" % (rel, label, name))
                seen.add(name)
        checked += 1
    print("STRING-SYMBOLS ok programs=%d" % checked)
    return 0


if __name__ == "__main__":
    sys.exit(main())
