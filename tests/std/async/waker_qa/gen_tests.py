#!/usr/bin/env python3
"""Bundle generator and freshness check for tests/std/async/waker_qa (T421a QA adversarial tests).

QA-written adversarial interleavings for the T421a waker protocol: wake during poll, cancel during
poll (incl. a cancel flag without a wake), handle dropped while a joined task completes, detached
and group-owned children dropped with panics, and a task waker dropped late on a foreign thread.

Each run test is one `.ax` file that concatenates, verbatim, the live std sources it needs with the
test program from `src/<name>.axsrc` (same scheme as tests/std/async/structured). `--check` fails when
a committed bundle is out of date.

The listed std sources are seeds: the generator adds the dependency closure of their imports and of the
test program's imports (`structured/bundle_closure.py`), so a std module that gains an import cannot make
a bundle stale or incomplete (T449a).
"""

import argparse
import os
import re
import sys

sys.path.insert(0, os.path.join(os.path.dirname(os.path.abspath(__file__)), "..", "structured"))
from bundle_closure import bundle_sources  # noqa: E402  (shared helper, T449a)

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", "..", ".."))
SRC = os.path.join(HERE, "src")

# The tests need no std module beyond the import closure that `bundle_sources` derives from the sources
# listed below and from the test program. In particular std.text.string / std.thread are not bundled any
# more: they are not imported by std.asyn.*, and bundling them next to std.io (which defines its own
# `String`/`string_new`) makes the compiler report AX_TYPE_MISMATCH on `Result.Ok(string_new())`.
COMMON_PREREQS = []

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
    "qa_wake_during_poll": ("OK qa_wake_during_poll 200 overlaps 0 lost 0\\n", ASYNC_CORE, 180),
    "qa_cancel_during_poll": ("OK qa_cancel_during_poll 200 cancelled 100 completed 50 futures 200 outputs 0\\n", ASYNC_CORE, 180),
    "qa_join_drop_vs_complete": ("OK qa_join_drop_vs_complete 300 leaked 0\\n", ASYNC_CORE, 180),
    "qa_group_drop_detached": ("OK qa_group_drop_detached 40 futures 0 outputs 0\\n", GROUP_SOURCES, 180),
    "qa_late_waker_drop": ("OK qa_late_waker_drop 100 early 0 drops 100\\n", ASYNC_CORE, 180),
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
            print("wrote " + os.path.relpath(target, ROOT).replace(os.sep, "/"))

    if args.check:
        if mismatches:
            print("ERROR: waker_qa test bundles are out of date:", file=sys.stderr)
            for m in mismatches:
                print("  - " + m, file=sys.stderr)
            print("Run `python tests/std/async/waker_qa/gen_tests.py` to regenerate.", file=sys.stderr)
            return 1
        sys.stdout.buffer.write(b"OK waker_qa bundles match live std/async\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
