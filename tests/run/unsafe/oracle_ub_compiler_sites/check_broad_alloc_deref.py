#!/usr/bin/env python3
"""T543 QA boundary test: a wider net than check_compiler_sites.py.

Reports a dereference of the direct result of any arena/heap allocation call in compiler/**/*.ax, including the forms the
primary guard's regex misses: whitespace between `*` and `(`, a module-qualified call, and the `arena_alloc` /
`heap_alloc_*` families. All of them read never-written bytes (UB-04, SPEC-50 AXS-UNS-014).
usage: check_broad_alloc_deref.py <repo-root> | --self-check
"""
import os
import re
import sys

PATTERN = re.compile(r"\*\s*\(\s*(?:\w+\.)*(?:arena_alloc\w*|heap_alloc\w*|mem_alloc\w*)\s*\(")


def strip_comments(text):
    return "\n".join(line.split("//", 1)[0] for line in text.split("\n"))


def scan_text(text):
    text = strip_comments(text)
    return [text.count("\n", 0, m.start()) + 1 for m in PATTERN.finditer(text)]


def main(argv):
    if argv[1:] == ["--self-check"]:
        cases = {
            "let a = unsafe { *(arena_alloc_raw(x, 8, 8) as *mut u64) };": [1],
            "let a = unsafe { * (arena_alloc_raw(x, 8, 8) as *mut u64) };": [1],
            "let a = unsafe { *(\n  mem.arena_alloc(x, 8) as *mut u64) };": [1],
            "let a = unsafe { *(heap_alloc_zeroed(8, 8) as *mut u64) };": [1],
            "// *(arena_alloc_raw(x) as *mut u64)\nlet p = arena_alloc_raw(x, 8, 8) as *mut u64;": [],
        }
        for src, want in cases.items():
            got = scan_text(src)
            if got != want:
                print("SELF-CHECK FAIL %r want %r got %r" % (src, want, got))
                return 1
        print("BROAD-SELF-CHECK PASS")
        return 0
    root = argv[1]
    hits = 0
    for dp, _d, files in os.walk(os.path.join(root, "compiler")):
        for name in sorted(files):
            if name.endswith(".ax"):
                path = os.path.join(dp, name)
                with open(path, "rb") as fh:
                    for line in scan_text(fh.read().decode("utf-8", "replace")):
                        print("%s:%d: typed load of fresh allocation" % (os.path.relpath(path, root).replace(os.sep, "/"), line))
                        hits += 1
    print("BROAD-SCAN %s %d" % ("FAIL" if hits else "PASS", hits))
    return 1 if hits else 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
