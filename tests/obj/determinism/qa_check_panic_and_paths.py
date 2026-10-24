#!/usr/bin/env python3
"""QA T147 boundary test (ADR-0035 section 1): panic-data symbols and path independence.

usage: qa_check_panic_and_paths.py <axiom0> <tmp_dir> <repo_root>

For every program under tests/run/str, tests/run/parity/strings and the assert/panic canaries of
tests/run/intrinsics, `axiom0 build --emit=obj`:
  * every `.Lpanic*` symbol is named `.Lpanic.<n>`, defined (SectionNumber > 0) and STATIC, and the
    numbers are exactly 0..N-1 (per-object counter starting at 0; no `.Lpanic_<n>` legacy name);
  * every `.Lstr.<f>.<k>` symbol starts on an 8-byte boundary of its section (NUL + pad to 8);
  * every relocation whose target is a `.Lstr`/`.Lpanic` symbol targets a defined STATIC record
    (bound by index, no undefined twin);
  * the object and the `build` image are byte-identical when the source is copied to another
    directory and the output goes to another directory (no path in the outputs).
"""

import glob
import os
import re
import shutil
import struct
import subprocess
import sys

PANIC_RE = re.compile(rb"^\.Lpanic\.(\d+)$")


def run(cmd):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=300)


def parse(data):
    machine, nsec, _ts, symptr, nsyms, _opt, _chars = struct.unpack_from("<HHIIIHH", data, 0)
    assert machine == 0x8664, "not an AMD64 COFF object"
    strtab = symptr + 18 * nsyms
    syms = {}
    i = 0
    while i < nsyms:
        rec = data[symptr + 18 * i: symptr + 18 * (i + 1)]
        name8, value, section, _type, storage, naux = struct.unpack("<8sIhHBB", rec)
        if name8[:4] == b"\0\0\0\0":
            off = struct.unpack("<I", name8[4:])[0]
            name = data[strtab + off:data.index(b"\0", strtab + off)]
        else:
            name = name8.rstrip(b"\0")
        syms[i] = (name, value, section, storage)
        i += 1 + naux
    relocs = []
    for s in range(nsec):
        sh = data[20 + 40 * s: 20 + 40 * (s + 1)]
        _n, _vs, _va, _sz, _raw, rptr, _lp, nrel, _nl, _ch = struct.unpack("<8sIIIIIIHHI", sh)
        for r in range(nrel):
            _va2, idx, _t = struct.unpack_from("<IIH", data, rptr + 10 * r)
            relocs.append(idx)
    return syms, relocs


def build(compiler, args, src, out):
    if os.path.exists(out):
        os.remove(out)
    r = run([compiler, "build"] + args + ["-o", out, src])
    if r.returncode != 0:
        raise SystemExit("FAIL: build %s %s: rc=%d %s" % (args, src, r.returncode, r.stderr.decode("utf-8", "replace")))
    with open(out, "rb") as f:
        return f.read()


def main():
    compiler, tmp, root = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(tmp, exist_ok=True)
    programs = sorted(glob.glob(os.path.join(root, "tests", "run", "str", "*.ax"))
                      + glob.glob(os.path.join(root, "tests", "run", "parity", "strings", "*.ax"))
                      + glob.glob(os.path.join(root, "tests", "run", "intrinsics", "assert_*.ax"))
                      + glob.glob(os.path.join(root, "tests", "run", "intrinsics", "panic_*.ax")))
    if not programs:
        raise SystemExit("FAIL: no programs found")
    alt_src_dir = os.path.join(tmp, "other_src_dir")
    alt_out_dir = os.path.join(tmp, "other_out_dir_with_a_longer_name")
    os.makedirs(alt_src_dir, exist_ok=True)
    os.makedirs(alt_out_dir, exist_ok=True)
    total_panic = 0
    for src in programs:
        rel = os.path.relpath(src, root)
        obj = build(compiler, ["--emit=obj"], src, os.path.join(tmp, "a.obj"))
        syms, relocs = parse(obj)
        panic_ns = []
        for (name, value, section, storage) in syms.values():
            if name.startswith(b".Lpanic"):
                m = PANIC_RE.match(name)
                if not m:
                    raise SystemExit("FAIL: %s: panic symbol %r is not .Lpanic.<n>" % (rel, name))
                if section <= 0 or storage != 3:
                    raise SystemExit("FAIL: %s: %r is not a defined STATIC symbol" % (rel, name))
                panic_ns.append(int(m.group(1)))
            elif name.startswith(b".Lstr"):
                if value % 8 != 0:
                    raise SystemExit("FAIL: %s: %r at offset %d is not 8-byte aligned" % (rel, name, value))
        if sorted(panic_ns) != list(range(len(panic_ns))):
            raise SystemExit("FAIL: %s: panic numbers %r are not 0..N-1" % (rel, sorted(panic_ns)))
        total_panic += len(panic_ns)
        for idx in relocs:
            if idx not in syms:
                raise SystemExit("FAIL: %s: relocation against symbol index %d (not a primary record)" % (rel, idx))
            name, _v, section, storage = syms[idx]
            if (name.startswith(b".Lstr") or name.startswith(b".Lpanic")) and (section <= 0 or storage != 3):
                raise SystemExit("FAIL: %s: relocation targets non-local %r" % (rel, name))
        # path independence: copy the source elsewhere, write the outputs elsewhere
        alt_src = os.path.join(alt_src_dir, os.path.basename(src))
        shutil.copyfile(src, alt_src)
        obj2 = build(compiler, ["--emit=obj"], alt_src, os.path.join(alt_out_dir, "b.obj"))
        if obj2 != obj:
            raise SystemExit("FAIL: %s: object depends on the source/output path" % rel)
        exe1 = build(compiler, [], src, os.path.join(tmp, "a.exe"))
        exe2 = build(compiler, [], alt_src, os.path.join(alt_out_dir, "b.exe"))
        if exe1 != exe2:
            raise SystemExit("FAIL: %s: image depends on the source/output path" % rel)
    if total_panic == 0:
        raise SystemExit("FAIL: no .Lpanic symbol seen (corpus lost its assert/panic programs)")
    print("QA-PANIC-PATHS ok programs=%d panic_syms=%d" % (len(programs), total_panic))
    return 0


if __name__ == "__main__":
    sys.exit(main())
