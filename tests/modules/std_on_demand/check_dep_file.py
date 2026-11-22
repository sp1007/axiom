#!/usr/bin/env python3
"""T423h (ADR-0048 §4, ADR-0041 §4): `--dep-file` of a program that loads std modules on demand.

Usage (from the repository root, as dep_file.test does):
    python tests/modules/std_on_demand/check_dep_file.py <tmp dir> <compiler>

Runs `<compiler> check --std-root std --dep-file <tmp>/deps.txt tests/modules/std_on_demand/fixtures/dep_main.ax`
(`use std.process.exit`) and checks, independently of the compiler:
  * the loaded std files (lines `std/<rel> <sha256>`) are exactly the golden list `dep_file.golden`, and each hash
    is the sha256 of the bytes on disk (hashlib);
  * the std directories the index walked are listed as `<dir>/ dir` lines: the std root itself and every
    directory below it that holds an `.ax` file (computed here with os.walk);
  * a std file that was only read for its module header (e.g. `std/core/mem.ax`) is not listed.
Prints the loaded std files (the golden view) and `dep-file std_on_demand: OK`, or FAIL lines.
"""

import hashlib
import os
import re
import subprocess
import sys

ROOT = os.path.abspath(os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", ".."))
HERE = "tests/modules/std_on_demand"
LINE_RE = re.compile(r"^(.*\S) ([0-9a-f]{64}|-|dir)$")


def main():
    tmp, compiler = sys.argv[1], sys.argv[2:]
    if compiler and os.path.exists(compiler[0]):
        compiler = [os.path.abspath(compiler[0])] + compiler[1:]
    os.makedirs(tmp, exist_ok=True)
    dep = os.path.join(tmp, "deps.txt")
    if os.path.exists(dep):
        os.remove(dep)
    r = subprocess.run(compiler + ["check", "--std-root", "std", "--dep-file", dep, HERE + "/fixtures/dep_main.ax"],
                       cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE, stdin=subprocess.DEVNULL,
                       timeout=600)
    fails = []
    if r.returncode != 0:
        fails.append("check exited %d: %r" % (r.returncode, r.stderr[-400:]))
    if not os.path.isfile(dep):
        print("FAIL: no dependency file written")
        return 1
    data = open(dep, "rb").read().decode("utf-8")
    entries = {}
    for line in data.split("\n"):
        if not line:
            continue
        m = LINE_RE.match(line)
        if not m:
            fails.append("malformed line %r" % line)
            continue
        entries[m.group(1)] = m.group(2)

    loaded = sorted(p for p, t in entries.items() if p.startswith("std/") and len(t) == 64)
    golden = [l.strip() for l in open(os.path.join(ROOT, HERE, "dep_file.golden"), encoding="utf-8")
              if l.strip() and not l.startswith("#")]
    for p in loaded:
        print(p)
    if loaded != golden:
        fails.append("loaded std files %r != golden %r" % (loaded, golden))
    for p in loaded:
        with open(os.path.join(ROOT, p), "rb") as f:
            if hashlib.sha256(f.read()).hexdigest() != entries[p]:
                fails.append("hash mismatch for %s" % p)

    want_dirs = {"std/"}
    for dirpath, _dirs, files in os.walk(os.path.join(ROOT, "std")):
        if any(f.endswith(".ax") for f in files):
            rel = os.path.relpath(dirpath, ROOT).replace(os.sep, "/")
            want_dirs.add(rel.rstrip("/") + "/")
    got_dirs = {p if p.endswith("/") else p + "/" for p, t in entries.items() if t == "dir" and p.startswith("std")}
    missing = sorted(want_dirs - got_dirs)
    if missing:
        fails.append("std directories not listed as `dir`: %r" % missing)
    if "std/core/mem.ax" in entries:
        fails.append("std/core/mem.ax (read only for its header) is listed")

    for f in fails:
        print("FAIL: " + f)
    if not fails:
        print("dep-file std_on_demand: OK")
    return 1 if fails else 0


if __name__ == "__main__":
    sys.exit(main())
