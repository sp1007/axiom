#!/usr/bin/env python3
"""Bundle generator and freshness check for tests/std/thread/native_panic_hook (T538).

Each run test is one `.ax` file that concatenates, verbatim, the live std sources std.thread needs
(std/sys/windows/thread.ax and its prerequisites) with the test program from `src/<name>.axsrc`, so the
tests exercise exactly the panic hook code in std/sys/windows/thread.ax. `--check` fails when a committed
bundle is out of date.
"""

import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
SRC = os.path.join(HERE, "src")

THREAD_SOURCES = [
    "std/sync/atomic.ax",
    "std/sys/windows/heap.ax",
    "std/sys/windows/time.ax",
    "std/sys/windows/thread.ax",
    "std/time/time.ax",
    "std/text/utf8.ax",
    "std/text/string.ax",
    "std/thread/mod.ax",
]

# name -> (expected stdout, expected exit code, modes)
TESTS = {
    # A user ExitProcess(101) on a spawned thread ends the process with 101 (no ExitProcess hook).
    "nph_exit101_thread": ("contained -1\\n", 101, "native"),
    # A panic on a spawned thread is still contained (join Err); a later main-thread panic exits 101.
    "nph_panic_contained": ("OK nph_panic_contained -1 9 -1\\n", 101, "interp native"),
}

COVERS = "REQ-TST-072, REQ-CONC-219"

CHECK_DEF = """
// Failure reporting: `check(cond)` in src/<name>.axsrc is rewritten to `check_at(<source line>, cond)`.
// Not `assert()`: the stdout comparison is the evidence in native mode (standing rule T134).
fn check_at(line: i32, cond: bool) {
    if !cond {
        print("FAIL line ");
        print_int(line as i64);
        print("\\n");
        loop {}
    }
}
"""


def read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")


def number_checks(text):
    out = []
    for idx, line in enumerate(text.split(chr(10))):
        out.append(re.sub(r"check\(", "check_at(%d, " % (idx + 1), line))
    return chr(10).join(out)


def build_bundle(name, expected_stdout, exit_code, modes):
    header = (
        "// test: run\n"
        "// modes: %s\n"
        "// timeout: 60\n"
        "// covers: %s\n"
        "// stdout: %s\n"
        "// exit: %d\n" % (modes, COVERS, expected_stdout, exit_code)
    )
    parts = [header.rstrip("\n")]
    for rel in THREAD_SOURCES:
        parts.append(read_text(os.path.join(ROOT, rel.replace("/", os.sep))).strip())
    parts.append(number_checks(read_text(os.path.join(SRC, name + ".axsrc"))).strip())
    parts.append(CHECK_DEF.strip())
    return "\n\n".join(parts) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify the test bundles are up to date")
    args = parser.parse_args()

    mismatches = []
    for name, (expected_stdout, exit_code, modes) in TESTS.items():
        expected = build_bundle(name, expected_stdout, exit_code, modes)
        target = os.path.join(HERE, name + ".ax")
        if args.check:
            if not os.path.exists(target):
                mismatches.append(name + ".ax: does not exist")
            elif read_text(target) != expected:
                mismatches.append(name + ".ax: out of date")
        else:
            with open(target, "w", encoding="utf-8", newline="\n") as f:
                f.write(expected)
            print("Generated " + name + ".ax")

    if args.check:
        if mismatches:
            print("ERROR: native_panic_hook bundles are out of date:", file=sys.stderr)
            for m in mismatches:
                print("  - " + m, file=sys.stderr)
            print("Run `python tests/std/thread/native_panic_hook/gen_tests.py` to regenerate.", file=sys.stderr)
            return 1
        sys.stdout.buffer.write(b"OK native_panic_hook bundles match live std\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
