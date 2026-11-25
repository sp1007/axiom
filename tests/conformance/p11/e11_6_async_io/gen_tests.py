#!/usr/bin/env python3
"""Bundle generator and freshness check for the TaskGroup test of tests/conformance/p11/e11_6_async_io (T428).

`taskgroup_async_io.ax` concatenates, verbatim, the live std sources of the structured-concurrency stack
(std/sync/atomic.ax ... std/async/group.ax) with the test program from `src/taskgroup_async_io.axsrc`. The
bundle is required because `TaskGroup.spawn` cannot be instantiated from a program that imports the live
`std.asyn.group` module (AX_CONC_CAPTURE_NOT_SEND inside std/async/group.ax; see the T428 report, follow-up F3);
every TaskGroup test of the repository (tests/std/async/structured, tests/conformance/p11/e11_5_executors) is
bundled the same way. The I/O half of the test (std.net, std.io.async_io, std.asyn.reactor) is imported live.
`--check` fails when the committed bundle is out of date. All other tests of this directory are plain `.ax` files.
"""

import argparse
import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
SRC = os.path.join(HERE, "src")

# Dependency-ordered closure of the modules the test imports (std.net, std.io.async_io, std.asyn.*), computed from
# the `use std.*` lines; std/core/* stays live (the compiler provides it). Bundling a module that live std code also
# imports without bundling that code too makes two incompatible copies of its types, so the whole closure is inlined.
GROUP_SOURCES = [
    "std/sync/atomic.ax",
    "std/time/time.ax",
    "std/sync/arc.ax",
    "std/bytes/byte_buf.ax",
    "std/io/io.ax",
    "std/async/waker.ax",
    "std/async/task.ax",
    "std/async/timeout.ax",
    "std/async/timer.ax",
    "std/async/reactor.ax",
    "std/async/executor.ax",
    "std/async/cancel.ax",
    "std/async/governor.ax",
    "std/async/group.ax",
    "std/io/async_io.ax",
    "std/net/mod.ax",
]

# name -> (covers, expected stdout, std sources, timeout seconds)
TESTS = {
    "taskgroup_async_io": (
        "REQ-ASY-155 REQ-ASY-152 REQ-CONC-153",
        "OK taskgroup_async_io completed=2 clients=27 server=27 cancelled=1 untouched=1\\n",
        GROUP_SOURCES,
        120,
    ),
}


def read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")


def build_bundle(name, covers, expected_stdout, sources, timeout):
    header = (
        "// test: run\n"
        "// modes: interp native\n"
        "// timeout: %d\n"
        "// covers: %s\n"
        "// stdout: %s\n" % (timeout, covers, expected_stdout)
    )
    parts = [header.rstrip("\n")]
    for rel in sources:
        parts.append(read_text(os.path.join(ROOT, rel.replace("/", os.sep))).strip())
    parts.append(read_text(os.path.join(SRC, name + ".axsrc")).strip())
    return "\n\n".join(parts) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify the test bundles are up to date")
    parser.add_argument("names", nargs="*", help="only these tests (default: all)")
    args = parser.parse_args()

    names = args.names if args.names else list(TESTS.keys())
    mismatches = []
    for name in names:
        covers, expected_stdout, sources, timeout = TESTS[name]
        expected = build_bundle(name, covers, expected_stdout, sources, timeout)
        target = os.path.join(HERE, name + ".ax")
        if args.check:
            if not os.path.exists(target):
                mismatches.append(name + ".ax: does not exist")
                continue
            actual = read_text(target)
            if actual != expected:
                mismatches.append(
                    "%s.ax: out of date (length actual=%d vs expected=%d)" % (name, len(actual), len(expected))
                )
        else:
            with open(target, "w", encoding="utf-8", newline="\n") as f:
                f.write(expected)
            print("Generated " + name + ".ax")

    if args.check:
        if mismatches:
            print("ERROR: e11_6 conformance bundles are out of date:", file=sys.stderr)
            for m in mismatches:
                print("  - " + m, file=sys.stderr)
            print("Run `python tests/conformance/p11/e11_6_async_io/gen_tests.py` to regenerate.", file=sys.stderr)
            return 1
        sys.stdout.buffer.write(b"OK e11_6 async I/O bundles match live std/async\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
