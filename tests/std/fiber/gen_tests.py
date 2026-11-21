#!/usr/bin/env python3
"""Bundle generator and freshness check for tests/std/fiber (T423).

Each run test is one `.ax` file that concatenates, verbatim, the live std sources it needs
(std/sys/windows/heap.ax, thread.ax, fiber.ax, std/fiber/mod.ax ...) with the test program from
`src/<name>.axsrc`. This guarantees the tests exercise exactly the code in std/fiber and
std/sys/windows/fiber.ax (same scheme as tests/std/async/* and tests/std/sync). `--check` fails when
a committed bundle is out of date.
"""

import argparse
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
SRC = os.path.join(HERE, "src")

# std.fiber needs host.thread_current_id (thread.ax) and the heap hooks; the platform layer is part
# of the bundle exactly like in the other std bundles.
FIBER_SOURCES = [
    "std/sys/windows/heap.ax",
    "std/sys/windows/thread.ax",
    "std/sys/windows/fiber.ax",
    "std/fiber/mod.ax",
]

# The affinity test also spawns real OS threads (std.thread and its prerequisites).
FIBER_THREAD_SOURCES = [
    "std/sync/atomic.ax",
    "std/sys/windows/heap.ax",
    "std/sys/windows/time.ax",
    "std/sys/windows/thread.ax",
    "std/sys/windows/fiber.ax",
    "std/time/time.ax",
    "std/text/utf8.ax",
    "std/text/string.ax",
    "std/thread/local.ax",
    "std/thread/mod.ax",
    "std/fiber/mod.ax",
]

# name -> (expected stdout, std sources, timeout seconds)
TESTS = {
    "fiber_ping_pong": ("OK fiber_ping_pong 6 3 100 132456 1\\n", FIBER_SOURCES, 60),
    "fiber_deep_stack": ("OK fiber_deep_stack 7 210 210 9 15\\n", FIBER_SOURCES, 60),
    "fiber_stack_sizes": ("OK fiber_stack_sizes 11325 5050 5050\\n", FIBER_SOURCES, 60),
    "fiber_scheduler_rr": ("OK fiber_scheduler_rr 10 20 30 11 21 12 0\\n", FIBER_SOURCES, 60),
    "fiber_drop_cleanup": ("OK fiber_drop_cleanup 2 1 0 7\\n", FIBER_SOURCES, 60),
    "fiber_nested": ("OK fiber_nested 101 102 123\\n", FIBER_SOURCES, 60),
    "fiber_host_contract": ("OK fiber_host_contract 11 21 60 -4 -4 0 -4\\n", FIBER_SOURCES, 60),
    "fiber_affinity": ("OK fiber_affinity 1 -4 -4\\n", FIBER_THREAD_SOURCES, 60),
    "fiber_panic_contained": ("OK fiber_panic_contained 1 42\\n", FIBER_SOURCES, 60),
    # QA-added adversarial tests (T423 gate).
    "qa_fiber_values": ("OK qa_fiber_values 207 83 0 7 -5 456\\n", FIBER_SOURCES, 60),
    "qa_fiber_many": ("OK qa_fiber_many 134550 180\\n", FIBER_SOURCES, 120),
    "qa_fiber_drop": ("OK qa_fiber_drop 1234576\\n", FIBER_SOURCES, 60),
    "qa_fiber_nested3": ("OK qa_fiber_nested3 10 2001 30 2023 6 5 60\\n", FIBER_SOURCES, 60),
    "qa_fiber_foreign_collision": ("OK qa_fiber_foreign_collision 6005 6006 77\\n", FIBER_THREAD_SOURCES, 60),
    "qa_fiber_resume_finished": ("before\\n", FIBER_SOURCES, 60),
    "qa_fiber_yield_outside": ("before\\n", FIBER_SOURCES, 60),
    "qa_fiber_handle_reuse": ("OK qa_fiber_handle_reuse 300 300 150 150\\n", FIBER_SOURCES, 120),
}

# Tests whose expected outcome is a panic (exit 101, stdout up to the panic point).
EXPECT_EXIT = {
    "qa_fiber_resume_finished": 101,
    "qa_fiber_yield_outside": 101,
}

# Tests whose native mode is skipped until a catch-up task lands (`// native-after:`): a panic inside a
# native fiber ends the process (exit 101); containment as FiberState.Panicked exists only in the oracle.
NATIVE_AFTER = {
    "fiber_panic_contained": "T423b",
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
    modes = "interp native"
    header = (
        "// test: run\n"
        "// modes: %s\n"
        "// timeout: %d\n"
        "// covers: REQ-CONC-151, REQ-CONC-189\n"
        "// stdout: %s\n" % (modes, timeout, expected_stdout)
    )
    if name in EXPECT_EXIT:
        header += "// exit: %d\n" % EXPECT_EXIT[name]
    if name in NATIVE_AFTER:
        header += "// native-after: %s\n" % NATIVE_AFTER[name]
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
            print("ERROR: fiber test bundles are out of date:", file=sys.stderr)
            for m in mismatches:
                print("  - " + m, file=sys.stderr)
            print("Run `python tests/std/fiber/gen_tests.py` to regenerate.", file=sys.stderr)
            return 1
        sys.stdout.buffer.write(b"OK fiber bundles match live std/fiber\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
