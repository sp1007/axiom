#!/usr/bin/env python3
"""QA guard for T430: no optimizer oracle may append a module that CORE_MODULES / PIPELINE_MODULES already
provide (a duplicate module in a probe bundle fails with AX_NAME_DUPLICATE, 126x). Static, no compiler needed."""
import collections
import glob
import os
import re
import sys

root = os.path.abspath(sys.argv[1])
scan_root = os.path.abspath(sys.argv[2]) if len(sys.argv) > 2 else root  # 2nd arg: scan another tree (mutation proof)
sys.path.insert(0, os.path.join(root, "tests", "selfhost"))
sys.path.insert(0, os.path.join(root, "tests", "selfhost", "opt"))
import gen_opt_tests as got  # noqa: E402

RX = re.compile(r"list\(got\.(CORE_MODULES|PIPELINE_MODULES)\) \+ \[(.*?)\n\s*\]", re.S)


def dups(base, extra_src):
    names = [n for n, _ in base] + re.findall(r'\("([\w.]+)",', extra_src)
    return sorted(k for k, c in collections.Counter(names).items() if c > 1)


# self-test: the checker must detect the T430 bug
assert dups(got.CORE_MODULES, '("compiler.own.cap", "compiler"),') == ["compiler.own.cap"], "checker is blind"
assert dups(got.CORE_MODULES, "") == [] and dups(got.PIPELINE_MODULES, "") == [], "base lists contain duplicates"

bad, seen = [], 0
files = sorted(f for f in glob.glob(os.path.join(scan_root, "tests", "**", "*.py"), recursive=True)
               if os.sep + "selfhost" + os.sep not in f)
for f in files:
    s = open(f, encoding="utf-8").read()
    for m in RX.finditer(s):
        seen += 1
        d = dups(getattr(got, m.group(1)), m.group(2))
        if d:
            bad.append((os.path.relpath(f, scan_root), d))
if bad:
    for f, d in bad:
        sys.stderr.write("duplicate module(s) %s in %s\n" % (d, f))
    sys.exit(1)
assert seen >= 17 or scan_root != root, "found only %d module lists" % seen
sys.stdout.buffer.write(("T430-MODLIST-NODUP-OK lists=%d\n" % seen).encode())
