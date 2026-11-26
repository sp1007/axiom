#!/usr/bin/env python3
"""Bundle generator and freshness check for tests/conformance/p11/e11_5_executors (T424).

Each run test is one `.ax` file that concatenates, verbatim, the live std sources it needs
(std/sync/atomic.ax ... std/async/*.ax, std/fiber/mod.ax) with the test program from
`src/<name>.axsrc`. This guarantees the suite exercises exactly the code in std/async and std/fiber
(same scheme as tests/std/async/* and tests/std/fiber). `--check` fails when a committed bundle is out
of date.

The listed std sources are seeds: the generator adds the dependency closure of their imports and of the
test program's imports (`tests/std/async/structured/bundle_closure.py`, T449a; adopted here by T428a), so a std
module that gains an import cannot make a bundle stale or incomplete.
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "..", "std", "async", "structured"))
from bundle_closure import bundle_sources  # noqa: E402  (shared helper, T449a)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
SRC = os.path.join(HERE, "src")

# The async tests need no std module beyond the import closure that `bundle_sources` derives from the sources
# listed below and from the test program; std.text.string / std.thread bundled next to std.io (which defines its
# own `String`/`string_new`) give AX_TYPE_MISMATCH on `Result.Ok(string_new())` (same fix as T449a).
COMMON_PREREQS = []

ASYNC_CORE = COMMON_PREREQS + [
    "std/async/waker.ax",
    "std/async/task.ax",
    "std/async/executor.ax",
]

GROUP_SOURCES = ASYNC_CORE + [
    "std/async/cancel.ax",
    "std/async/timeout.ax",
    "std/async/governor.ax",
    "std/async/group.ax",
]

SYNC_SOURCES = ASYNC_CORE + [
    "std/async/sync.ax",
]

CHANNEL_SOURCES = ASYNC_CORE + [
    "std/async/channel.ax",
]

FIBER_SOURCES = [
    "std/sys/windows/heap.ax",
    "std/sys/windows/thread.ax",
    "std/sys/windows/fiber.ax",
    "std/fiber/mod.ax",
]

# Fibers resumed from inside executor tasks and from several OS threads.
FIBER_ASYNC_SOURCES = ASYNC_CORE + [
    "std/sys/windows/fiber.ax",
    "std/fiber/mod.ax",
]

# name -> (covers, expected stdout, std sources, timeout seconds)
TESTS = {
    "cancel_tree_groups": (
        "REQ-ASY-165 REQ-CONC-040 REQ-CONC-155 REQ-ASY-019",
        "OK cancel_tree_groups 6 30 1 0\\n",
        GROUP_SOURCES,
        120,
    ),
    "sibling_failure_isolation": (
        "REQ-ASY-165 REQ-ASY-019 REQ-CONC-155",
        "OK sibling_failure_isolation 1 3 100 9 0\\n",
        GROUP_SOURCES,
        120,
    ),
    "cancel_race_linearizes": (
        "REQ-ASY-165 REQ-CONC-155 REQ-CONC-149",
        "OK cancel_race_linearizes 32 0 0\\n",
        GROUP_SOURCES,
        120,
    ),
    "local_cancel_drop_order": (
        "REQ-ASY-165 REQ-CONC-155 REQ-ASY-060",
        "OK local_cancel_drop_order 1234125 12435 1122 0\\n",
        GROUP_SOURCES,
        60,
    ),
    "asyncmutex_cancel_wakes_next": (
        "REQ-ASY-165 REQ-CONC-049 REQ-ASY-129 REQ-ASY-130",
        "OK asyncmutex_cancel_wakes_next 23 34 134 123 21122111211211\\n",
        SYNC_SOURCES,
        60,
    ),
    "spawn_affinity_vs_migration": (
        "REQ-ASY-165 REQ-CONC-151 REQ-CONC-034 REQ-ASY-041 REQ-CONC-148",
        "OK spawn_affinity_vs_migration 1 1 1 1\\n",
        ASYNC_CORE,
        120,
    ),
    "channel_cancel_safety": (
        "REQ-ASY-165 REQ-CONC-049 REQ-ASY-054",
        "OK channel_cancel_safety 9 6 0 1\\n",
        CHANNEL_SOURCES,
        60,
    ),
    "fiber_switch_conformance": (
        "REQ-ASY-165 REQ-CONC-151 REQ-CONC-189",
        "OK fiber_switch_conformance 1 101204306102205103 40 1020301121311222\\n",
        FIBER_SOURCES,
        60,
    ),
    "fiber_in_async_and_threads": (
        "REQ-ASY-165 REQ-CONC-151 REQ-CONC-189 REQ-CONC-190",
        "OK fiber_in_async_and_threads 604 7 324 56\\n",
        FIBER_ASYNC_SOURCES,
        120,
    ),
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


def build_bundle(name, covers, expected_stdout, sources, timeout):
    header = (
        "// test: run\n"
        "// modes: interp native\n"
        "// timeout: %d\n"
        "// covers: %s\n"
        "// stdout: %s\n" % (timeout, covers, expected_stdout)
    )
    parts = [header.rstrip("\n")]
    program = number_checks(read_text(os.path.join(SRC, name + ".axsrc"))).strip()
    for rel in bundle_sources(ROOT, sources, program):
        parts.append(read_text(os.path.join(ROOT, rel.replace("/", os.sep))).strip())
    parts.append(program)
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
        covers, expected_stdout, sources, timeout = TESTS[name]
        src_path = os.path.join(SRC, name + ".axsrc")
        if not os.path.exists(src_path):
            if args.check:
                mismatches.append(name + ": missing src/" + name + ".axsrc")
            continue
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
            print("ERROR: e11_5 executor conformance bundles are out of date:", file=sys.stderr)
            for m in mismatches:
                print("  - " + m, file=sys.stderr)
            print("Run `python tests/conformance/p11/e11_5_executors/gen_tests.py` to regenerate.", file=sys.stderr)
            return 1
        sys.stdout.buffer.write(b"OK e11_5 executor bundles match live std/async and std/fiber\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
