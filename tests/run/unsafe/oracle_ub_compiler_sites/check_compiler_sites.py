#!/usr/bin/env python3
"""T543 guard: compiler/**/*.ax must never dereference the direct result of arena_alloc_raw( / heap_alloc(.

`*(arena_alloc_raw(..) as *mut T)` is a typed load of freshly allocated, never-written bytes. The oracle reports it as
UB-04 (SPEC-50 AXS-UNS-014, `AX_UNSAFE_INTERP_UB: read of uninitialized memory`); natively it only "works" because the
Windows heap hands out zeroed pages. Build the value with a struct literal or a constructor (`mir_stmt_new`) instead.

usage: check_compiler_sites.py <repo-root>            scan <repo-root>/compiler, exit 1 and print file:line on a hit
       check_compiler_sites.py --plant                prove the detector: plant the pattern in a temp tree, expect a hit
"""
import os
import re
import sys
import tempfile

PATTERN = re.compile(r"\*\(\s*(arena_alloc_raw|heap_alloc)\(")


def strip_line_comments(text):
    # keep line numbers: blank out everything from `//` to end of line (the pattern never needs a string literal)
    return "\n".join(line.split("//", 1)[0] for line in text.split("\n"))


def scan(root):
    hits = []
    base = os.path.join(root, "compiler")
    for dirpath, _dirs, files in os.walk(base):
        for name in sorted(files):
            if not name.endswith(".ax"):
                continue
            path = os.path.join(dirpath, name)
            with open(path, "rb") as fh:
                text = strip_line_comments(fh.read().decode("utf-8", "replace"))
            for m in PATTERN.finditer(text):
                line = text.count("\n", 0, m.start()) + 1
                rel = os.path.relpath(path, root).replace(os.sep, "/")
                hits.append((rel, line, text.split("\n")[line - 1].strip()))
    return hits


def main(argv):
    if len(argv) == 2 and argv[1] == "--plant":
        with tempfile.TemporaryDirectory() as tmp:
            os.makedirs(os.path.join(tmp, "compiler", "opt"))
            planted = os.path.join(tmp, "compiler", "opt", "planted.ax")
            with open(planted, "wb") as fh:
                fh.write(b"fn f(arena: mut_view<Arena>) {\n"
                         b"    let mut st = unsafe { *(arena_alloc_raw(mut_view(*arena), 8, 8) as *mut u64) };\n"
                         b"    let mut h = unsafe { *(\n        heap_alloc(8, 8) as *mut u64) };\n"
                         b"}\n")
            hits = scan(tmp)
            if [h[1] for h in hits] == [2, 3]:
                print("PLANT-DETECTED compiler/opt/planted.ax:2 and :3")
                return 0
            print("PLANT-MISSED hits=%r" % (hits,))
            return 1
    if len(argv) != 2:
        print(__doc__)
        return 2
    hits = scan(argv[1])
    for rel, line, src in hits:
        print("%s:%d: typed load of fresh allocation (UB-04): %s" % (rel, line, src))
    if hits:
        print("COMPILER-SITES FAIL %d" % len(hits))
        return 1
    print("COMPILER-SITES PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
