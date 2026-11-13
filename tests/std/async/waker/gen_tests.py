#!/usr/bin/env python3
"""Bundle generator and freshness check for tests/std/async/waker (T421a).

Regression tests for the waker protocol and task-slot correctness of std/async: join-waker race,
task_wake livelock / cancel-flag clobber, RawWaker vtable dispatch, and dropping the outputs of
detached or never-joined tasks.

Each run test is one `.ax` file that concatenates, verbatim, the live std sources it needs with the
test program from `src/<name>.axsrc` (same scheme as tests/std/async/structured). `--check` fails when
a committed bundle is out of date.
"""

import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
SRC = os.path.join(HERE, "src")

COMMON_PREREQS = [
    "std/sync/atomic.ax",
    "std/sys/windows/heap.ax",
    "std/sys/windows/time.ax",
    "std/sys/windows/thread.ax",
    "std/time/time.ax",
    "std/text/utf8.ax",
    "std/text/string.ax",
    "std/thread/local.ax",
    "std/thread/mod.ax",
]

ASYNC_CORE = COMMON_PREREQS + [
    "std/async/waker.ax",
    "std/async/task.ax",
    "std/async/executor.ax",
]

GROUP_SOURCES = ASYNC_CORE + [
    "std/async/cancel.ax",
    "std/async/governor.ax",
    "std/async/timeout.ax",
    "std/async/group.ax",
]

# name -> (expected stdout, std sources, timeout seconds)
TESTS = {
    "join_waker_race": ("OK join_waker_race 1000 lost 0\\n", ASYNC_CORE, 180),
    "cancel_self_waking": ("OK cancel_self_waking 500 1000 clobbered 0\\n", ASYNC_CORE, 180),
    "user_waker_vtable": ("OK user_waker_vtable 41 4 1 2 4\\n", ASYNC_CORE, 60),
    "detached_output_drop": ("OK detached_output_drop 300 0\\n", GROUP_SOURCES, 120),
}


def read_text(path):
    with open(path, "r", encoding="utf-8") as f:
        return f.read().replace("\r\n", "\n")


CHECK_DEF = """
// Failure reporting: `check(cond)` in src/<name>.axsrc is rewritten to `check_at(<source line>, cond)`,
// so a failing assertion prints its line before the (timeout-bounded) spin. Not `assert()`: the
// stdout comparison is the evidence in native mode (standing rule T134).
fn check_at(line: i32, cond: bool) {
    if !cond {
        print("FAIL line ");
        print_int(line as i64);
        print("\\n");
        loop {}
    }
}
"""


def number_checks(text):
    out = []
    for idx, line in enumerate(text.split(chr(10))):
        out.append(re.sub(r"check\(", "check_at(%d, " % (idx + 1), line))
    return chr(10).join(out)


def build_bundle(name, expected_stdout, sources, timeout):
    header = (
        "// test: run\n"
        "// modes: interp native\n"
        "// timeout: %d\n"
        "// stdout: %s\n" % (timeout, expected_stdout)
    )
    parts = [header.rstrip("\n")]
    for rel in sources:
        parts.append(read_text(os.path.join(ROOT, rel.replace("/", os.sep))).strip())
    parts.append(number_checks(read_text(os.path.join(SRC, name + ".axsrc"))).strip())
    parts.append(CHECK_DEF.strip())
    return "\n\n".join(parts) + "\n"


def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--check", action="store_true", help="verify the test bundles are up to date")
    parser.add_argument("names", nargs="*", help="only these tests (default: all)")
    args = parser.parse_args()

    names = args.names if args.names else list(TESTS.keys())
    mismatches = []
    for name in names:
        expected_stdout, sources, timeout = TESTS[name]
        src_path = os.path.join(SRC, name + ".axsrc")
        if not os.path.exists(src_path):
            if args.check:
                mismatches.append(name + ": missing src/" + name + ".axsrc")
            continue
        expected = build_bundle(name, expected_stdout, sources, timeout)
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
            print("ERROR: waker regression test bundles are out of date:", file=sys.stderr)
            for m in mismatches:
                print("  - " + m, file=sys.stderr)
            print("Run `python tests/std/async/waker/gen_tests.py` to regenerate.", file=sys.stderr)
            return 1
        sys.stdout.buffer.write(b"OK waker bundles match live std/async\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
