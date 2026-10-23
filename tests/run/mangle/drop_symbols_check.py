#!/usr/bin/env python3
"""T141 (ADR-0034 section 6, REQ-OBJ-004): destructor symbols use the reserved `<Type>$drop` form.

Builds each `tests/run/mangle` program to a COFF object with the compiler under test and reads the
object's symbol table. Fails when
  * two DEFINED external symbols share a name (the pre-ADR-0034 `<Type>_drop` spelling makes a user
    `fn Foo_drop()` and the destructor of `impl Drop for Foo` collide, and two modules with
    `impl Drop for Helper` collide on `Helper_drop`), or
  * an expected destructor / user symbol is missing (pins the exact reserved spelling).

usage: drop_symbols_check.py <compiler> <tmp_dir> <root>
"""

import os
import struct
import subprocess
import sys

# program -> defined symbols that must exist in its object
EXPECTED = {
    "tests/run/mangle/drop_vs_free_fn.ax": ["Foo$drop", "Foo_drop", "Alpha$drop", "Beta$drop"],
    "tests/run/mangle/drop_cross_module_same_name.ax": ["Helper$drop", "Helper$drop$2"],
    "tests/run/mangle/qa_t141_same_name_drop_second_module.ax": ["Res$drop"],
    "tests/run/mangle/widget_drop_user_fn.ax": ["Widget$drop", "Widget_drop"],
}

IMAGE_SYM_CLASS_EXTERNAL = 2


def coff_symbols(path):
    data = open(path, "rb").read()
    _machine, _nsec, _ts, symptr, nsym, _opt, _ch = struct.unpack_from("<HHIIIHH", data, 0)
    strtab = symptr + nsym * 18
    out = []
    i = 0
    while i < nsym:
        off = symptr + i * 18
        raw = data[off:off + 8]
        _value, secnum, _typ, sclass, naux = struct.unpack_from("<IhHBB", data, off + 8)
        if raw[:4] == b"\0\0\0\0":
            soff = struct.unpack_from("<I", raw, 4)[0]
            end = data.index(b"\0", strtab + soff)
            name = data[strtab + soff:end].decode("latin1")
        else:
            name = raw.rstrip(b"\0").decode("latin1")
        out.append((name, secnum, sclass))
        i += 1 + naux
    return out


def main():
    if len(sys.argv) != 4:
        print(__doc__)
        return 2
    compiler, tmp, root = sys.argv[1], sys.argv[2], sys.argv[3]
    os.makedirs(tmp, exist_ok=True)
    failures = 0
    for rel, expected in EXPECTED.items():
        src = os.path.join(root, rel)
        obj = os.path.join(tmp, os.path.basename(rel)[:-3] + ".obj")
        r = subprocess.run([compiler, "build", "--std-root", os.path.join(root, "std"), "--emit=obj", "-o", obj, src],
                           stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
        if r.returncode != 0:
            print("FAIL %s: build exit %d: %s" % (rel, r.returncode, r.stdout.decode("utf-8", "replace")[:400]))
            failures += 1
            continue
        defined = [n for (n, sec, cls) in coff_symbols(obj) if sec > 0 and cls == IMAGE_SYM_CLASS_EXTERNAL]
        seen = set()
        dups = sorted({n for n in defined if n in seen or seen.add(n)})
        if dups:
            print("FAIL %s: duplicate defined symbols: %s" % (rel, ", ".join(dups)))
            failures += 1
        missing = [n for n in expected if n not in defined]
        if missing:
            print("FAIL %s: missing defined symbols: %s (defined: %s)" % (rel, ", ".join(missing), ", ".join(sorted(set(defined)))))
            failures += 1
        if not dups and not missing:
            print("ok %s" % rel)
    if failures:
        print("DROP-SYMBOLS FAIL %d" % failures)
        return 1
    print("DROP-SYMBOLS OK")
    return 0


if __name__ == "__main__":
    sys.exit(main())
