#!/usr/bin/env python3
"""Bundle generator and freshness check for tests/std/async/structured (T422).

Each run test is one `.ax` file that concatenates, verbatim, the live std sources it needs
(std/sync/atomic.ax ... std/async/*.ax) with the test program from `src/<name>.axsrc`. This
guarantees the tests exercise exactly the code in std/async (same scheme as tests/std/async/executor
and tests/std/sync). `--check` fails when a committed bundle is out of date.

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

CANCEL_SOURCES = ASYNC_CORE + [
    "std/async/cancel.ax",
]

TIMEOUT_SOURCES = ASYNC_CORE + [
    "std/async/timeout.ax",
]

GOVERNOR_SOURCES = ASYNC_CORE + [
    "std/async/governor.ax",
]

GROUP_SOURCES = ASYNC_CORE + [
    "std/async/cancel.ax",
    "std/async/governor.ax",
    "std/async/timeout.ax",
    "std/async/group.ax",
]

ALL_SOURCES = ASYNC_CORE + [
    "std/async/cancel.ax",
    "std/async/timeout.ax",
    "std/async/governor.ax",
    "std/async/group.ax",
]

LOCAL_EXAMPLE_SOURCES = ASYNC_CORE + [
    "std/sync/rc.ax",
    "std/async/sync.ax",
]

# name -> (expected stdout, std sources, timeout seconds[, extra header directive])
TESTS = {
    "cancel_token_tree": ("OK cancel_token_tree 2341 4\\n", CANCEL_SOURCES, 60),
    "deadline_timeout": ("OK deadline_timeout 5 5\\n", TIMEOUT_SOURCES, 60),
    "resource_governor_limits": ("OK resource_governor_limits 6\\n", GOVERNOR_SOURCES, 60),
    "group_join_all": ("OK group_join_all 8 36 0\\n", GROUP_SOURCES, 60),
    "group_sibling_cancel": ("OK group_sibling_cancel panicked 7 0\\n", GROUP_SOURCES, 60),
    "group_drop_cancels": ("OK group_drop_cancels 6 0\\n", GROUP_SOURCES, 60),
    "group_governor_quota": ("OK group_governor_quota 2 0\\n", GROUP_SOURCES, 60),
    "handle_drop_vs_detach": ("OK handle_drop_vs_detach 2 3 7\\n", GROUP_SOURCES, 60),
    "task_panic_contained": ("OK task_panic_contained 1 1 7\\n", GROUP_SOURCES, 60),
    "group_deadline": ("OK group_deadline 3 0\\n", GROUP_SOURCES, 60),
    "group_generic_output": ("OK group_generic_output 100 11\\n", GROUP_SOURCES, 60),
    "qa_nested_groups_races": ("OK qa_nested_groups_races 0\\n", GROUP_SOURCES, 60),
    "spec34_task_group_example": ("OK spec34_task_group_example 30\\n", GROUP_SOURCES, 60),
    "spec34_local_executor_example": ("OK spec34_local_executor_example 40\\n", LOCAL_EXAMPLE_SOURCES, 60),
    "group_two_output_types": ("OK group_two_output_types 30 100 33 0\\n", GROUP_SOURCES, 60),
    "qa_t422c_drop_edges": ("OK qa_t422c_drop_edges 1 3 40 50 1 0\\n", GROUP_SOURCES, 90),
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


def build_bundle(name, expected_stdout, sources, timeout, extra=None):
    header = (
        "// test: run\n"
        "// modes: interp native\n"
        "// timeout: %d\n"
        "// stdout: %s\n" % (timeout, expected_stdout)
    )
    if extra:
        header += "// %s\n" % extra
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
        expected_stdout, sources, timeout = TESTS[name][:3]
        extra = TESTS[name][3] if len(TESTS[name]) > 3 else None
        src_path = os.path.join(SRC, name + ".axsrc")
        if not os.path.exists(src_path):
            if args.check:
                mismatches.append(name + ": missing src/" + name + ".axsrc")
            continue
        expected = build_bundle(name, expected_stdout, sources, timeout, extra)
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
            print("ERROR: structured-concurrency test bundles are out of date:", file=sys.stderr)
            for m in mismatches:
                print("  - " + m, file=sys.stderr)
            print("Run `python tests/std/async/structured/gen_tests.py` to regenerate.", file=sys.stderr)
            return 1
        sys.stdout.buffer.write(b"OK structured bundles match live std/async\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
