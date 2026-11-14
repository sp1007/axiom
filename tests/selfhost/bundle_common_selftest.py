#!/usr/bin/env python3
"""Self-test of tests/selfhost/bundle_common.assemble_compiler_modules duplicate-module rejection (T443).

Plain Python 3 standard library; run directly (`python tests/selfhost/bundle_common_selftest.py`) or through
`tests/selfhost/bundle_common_selftest.test`. Prints one `ok <name>` line per check and `bundle_common selftest: N checks passed`.

Background (ADR-0042 section 5): T430 listed a module twice in a generator; the result was 126 AX_NAME_DUPLICATE
errors deep inside a 30k-line bundle. A repeated module name must fail at generation time with one clear error.
Byte-identity of clean lists against the committed bundles is covered by the 36 `gen_*.py --check` runs
(`selfhost/*/bundles_current.test`); the checks here pin the shape of the output and the error contract.
"""

import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)
sys.dont_write_bytecode = True

import bundle_common as bc  # noqa: E402

CLEAN = ["compiler.kernel.id", "compiler.kernel.hash", "compiler.kernel.arena"]
CALLER = "gen_selftest_fixture.py"

_passed = 0


def ok(name):
    global _passed
    _passed += 1
    print("ok %s" % name)


def expect_dup_error(mods, expected_names, name):
    try:
        bc.assemble_compiler_modules(mods, root=bc.ROOT, caller=CALLER)
    except ValueError as e:
        msg = str(e)
        assert msg.startswith("duplicate module(s) "), "%s: unexpected message %r" % (name, msg)
        for n in expected_names:
            assert n in msg, "%s: message %r does not name %r" % (name, msg, n)
        assert CALLER in msg, "%s: message %r does not name the caller" % (name, msg)
        ok(name)
        return
    raise AssertionError("%s: duplicate module list %r was accepted" % (name, mods))


def module_lines(text):
    return re.findall(r"^module (\S+)$", text, re.M)


def main():
    # 1. exact duplicate is rejected, names the module and the caller
    expect_dup_error(CLEAN + ["compiler.kernel.hash"], ["compiler.kernel.hash"], "exact duplicate rejected")

    # 2. duplicate as adjacent entries and several duplicates are all reported
    expect_dup_error(
        ["compiler.kernel.id", "compiler.kernel.id", "compiler.kernel.hash", "compiler.kernel.hash"],
        ["compiler.kernel.id", "compiler.kernel.hash"],
        "several duplicates all reported",
    )

    # 3. duplicate after normalisation: `.mod` suffix form
    expect_dup_error(["compiler.kernel", "compiler.kernel.mod"], ["compiler.kernel"], "dot-mod alias duplicate rejected")

    # 4. duplicate after normalisation: reserved-keyword aliases (move/unsafe -> move_ck/unsafe_ck)
    expect_dup_error(["compiler.own.move", "compiler.own.move_ck"], ["compiler.own.move_ck"], "move alias duplicate rejected")
    expect_dup_error(["compiler.own.unsafe_ck", "compiler.own.unsafe"], ["compiler.own.unsafe_ck"], "unsafe alias duplicate rejected")

    # 5. tuple-form entries are checked too
    expect_dup_error([("compiler.kernel.id", 1), "compiler.kernel.id"], ["compiler.kernel.id"], "tuple entry duplicate rejected")

    # 6. caller defaults to the running script when not given
    try:
        bc.assemble_compiler_modules(["compiler.kernel.id", "compiler.kernel.id"], root=bc.ROOT)
    except ValueError as e:
        assert os.path.basename(sys.argv[0]) in str(e), "default caller missing in %r" % str(e)
        ok("default caller is the running script")
    else:
        raise AssertionError("duplicate accepted without caller")

    # 7. no silent de-duplication: the helper reports, it does not rewrite the list
    lst = ["compiler.kernel.id", "compiler.kernel.id"]
    assert bc.find_duplicate_modules(lst) == ["compiler.kernel.id"]
    assert lst == ["compiler.kernel.id", "compiler.kernel.id"]
    ok("helper reports without mutating")

    # 8. a clean list is accepted and emits each module exactly once, in order
    text = bc.assemble_compiler_modules(CLEAN, root=bc.ROOT, caller=CALLER)
    assert module_lines(text) == CLEAN, "unexpected module order: %r" % module_lines(text)
    ok("clean list emits each module once in order")

    # 9. a clean list is deterministic and independent of the entry shape (plain vs tuple)
    again = bc.assemble_compiler_modules([(m, 0) for m in CLEAN], root=bc.ROOT, caller=CALLER)
    assert again == text, "clean output differs between runs / entry shapes"
    ok("clean output deterministic")

    # 10. a clean list that contains a module and its different sibling (not an alias) is not a false positive
    assert bc.find_duplicate_modules(["compiler.kernel", "compiler.kernel.id", "compiler.own.move", "compiler.own.unsafe"]) == []
    ok("no false positive for distinct modules")

    print("bundle_common selftest: %d checks passed" % _passed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
