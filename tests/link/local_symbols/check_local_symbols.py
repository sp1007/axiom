#!/usr/bin/env python3
"""T147 / ADR-0035 section 2: same-object references are bound by symbol index (axiom0 linker).

usage: check_local_symbols.py <build_dir> <tmp_dir>
Builds the hand-written objects, links them with the C driver (which calls `ax_pe_link`), runs the
image and compares its exit code with the value that proves every reference resolved to its own
symbol; then links the object together with a second one that defines EXTERNAL `ext_k` again and
requires the duplicate-symbol diagnostic.
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
import gen_local_symbols_obj as gen  # noqa: E402


def run(cmd):
    return subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, timeout=120)


def main():
    build_dir, tmp = sys.argv[1], sys.argv[2]
    os.makedirs(tmp, exist_ok=True)
    driver = os.path.join(build_dir, "tests", "ct_link_local_symbols_cdriver_link_objs")
    if sys.platform == "win32":
        driver += ".exe"
    sys.argv = [sys.argv[0], tmp]
    gen.main()
    obj = os.path.join(tmp, "local_symbols.obj")
    dup = os.path.join(tmp, "dup_ext.obj")
    exe = os.path.join(tmp, "local_symbols.exe")

    r = run([driver, exe, obj])
    if r.returncode != 0 or r.stdout.strip() != "LINKED":
        print("FAIL: link of local_symbols.obj: rc=%d out=%r err=%r" % (r.returncode, r.stdout, r.stderr))
        return 1
    p = run([exe])
    if p.returncode != gen.EXPECTED_EXIT_CODE:
        print("FAIL: image exit code %d, expected %d (a same-object reference bound to the wrong symbol)"
              % (p.returncode, gen.EXPECTED_EXIT_CODE))
        return 1

    r = run([driver, os.path.join(tmp, "dup.exe"), obj, dup])
    if r.returncode == 0 or r.stdout.strip() != "LINK-FAILED AX_LINK_DUPLICATE_SYMBOL":
        print("FAIL: duplicate EXTERNAL definition: rc=%d out=%r" % (r.returncode, r.stdout))
        return 1
    print("LOCAL-SYMBOLS axiom0 ok exit=%d" % p.returncode)
    return 0


if __name__ == "__main__":
    sys.exit(main())
