#!/usr/bin/env python3
"""Benchmark bundle generator and freshness check for tests/perf/p11_executor (T424).

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

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "..", "std", "async", "structured"))
from bundle_closure import bundle_sources  # noqa: E402  (shared helper, T449a)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
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

FIBER_TIMED_SOURCES = [
    "std/sys/windows/io.ax",
    "std/sys/windows/heap.ax",
    "std/sys/windows/time.ax",
    "std/sys/windows/thread.ax",
    "std/sys/windows/fiber.ax",
    "std/fiber/mod.ax",
]

# Fibers resumed from inside executor tasks and from several OS threads.
FIBER_ASYNC_SOURCES = ASYNC_CORE + [
    "std/sys/windows/fiber.ax",
    "std/fiber/mod.ax",
]

# name -> (std sources, timeout seconds)
TESTS = {
    "spawn_poll_throughput": (ASYNC_CORE, 120),
    "steal_fanout_fanin": (GROUP_SOURCES, 180),
    "channel_ping_pong": (CHANNEL_SOURCES, 180),
    "fiber_switch_overhead": (FIBER_TIMED_SOURCES, 180),
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


EPUT_RE = re.compile(r'eput\("((?:[^"\\]|\\n)*)"\)')


def expand_eput(text, name):
    """`eput("abc\\n")` -> `eput_byte(97u8); ...` and `@NAME@` -> the benchmark name."""
    text = text.replace("@NAME@", name)

    def one(m):
        lit = m.group(1).replace("\\n", chr(10))
        return " ".join("eput_byte(%du8);" % ord(ch) for ch in lit)

    return EPUT_RE.sub(one, text)


def build_bundle(name, sources, timeout):
    header = (
        "// test: run\n"
        "// modes: interp native\n"
        "// timeout: %d\n"
        "// stdout-contains: OK %s \n"
        "// stderr-contains: BENCH %s ops=\n" % (timeout, name, name)
    )
    parts = [header.rstrip("\n")]
    program = expand_eput(number_checks(read_text(os.path.join(SRC, name + ".axsrc"))), name).strip()
    common = expand_eput(number_checks(read_text(os.path.join(SRC, "_common.axsrc"))), name).strip()
    for rel in bundle_sources(ROOT, sources, program + "\n" + common):
        parts.append(read_text(os.path.join(ROOT, rel.replace("/", os.sep))).strip())
    parts.append(program)
    parts.append(common)
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
        sources, timeout = TESTS[name]
        src_path = os.path.join(SRC, name + ".axsrc")
        if not os.path.exists(src_path):
            if args.check:
                mismatches.append(name + ": missing src/" + name + ".axsrc")
            continue
        expected = build_bundle(name, sources, timeout)
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
            print("ERROR: p11 executor perf bundles are out of date:", file=sys.stderr)
            for m in mismatches:
                print("  - " + m, file=sys.stderr)
            print("Run `python tests/perf/p11_executor/gen_tests.py` to regenerate.", file=sys.stderr)
            return 1
        sys.stdout.buffer.write(b"OK p11 executor perf bundles match live std/async and std/fiber\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
