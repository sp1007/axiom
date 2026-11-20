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
import tempfile

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

    # T488 merge-group unit checks
    merge_passed = 0

    def mok(name):
        nonlocal merge_passed
        merge_passed += 1
        print("ok merge: %s" % name)

    m1 = "// test: run\n// timeout: 90\n// stdout: OK M1\\n\n\nmodule main\npub fn main() -> i32 { print(\"OK M1\\n\"); 0 }\n"
    m2 = "// test: run\n// timeout: 120\n// stdout: OK M2\\n\n\nmodule main\nfn main() -> i32 { print(\"OK M2\\n\"); 0 }\n"
    merged = bc.assemble_merged_group("module prelude\n", "module compiler.dummy\n", [("qa_m1.ax", m1), ("qa_m2.ax", m2)])
    assert "// timeout: 120\n" in merged
    assert "// stdout: OK M1\\n\n// stdout: OK qa_m1\\n\n// stdout: OK M2\\n\n// stdout: OK qa_m2\\n\n" in merged
    assert "module __case_qa_m1\n" in merged and "module __case_qa_m2\n" in merged
    assert "pub fn __t488_run() -> i32" in merged
    assert 'print("FAIL qa_m1\\n");' in merged and 'print("FAIL qa_m2\\n");' in merged
    assert "__failed = 1;" in merged
    assert "module main\n" in merged
    mok("basic 2-member merge emits isolated modules, OK/FAIL driver, max timeout, concatenated stdout")

    # Mixed modes rejected
    m_nat = "// test: run\n// modes: native\n// stdout: OK N\\n\n\nmodule main\npub fn main() -> i32 { 0 }\n"
    try:
        bc.assemble_merged_group("module p\n", "module c\n", [("qa_m1.ax", m1), ("qa_mn.ax", m_nat)])
        raise AssertionError("mixed modes should be rejected")
    except ValueError as e:
        assert "mixed modes" in str(e)
        mok("mixed modes rejected")

    # Duplicate member rejected
    try:
        bc.assemble_merged_group("module p\n", "module c\n", [("qa_m1.ax", m1), ("qa_m1.ax", m1)])
        raise AssertionError("duplicate member should be rejected")
    except ValueError as e:
        assert "duplicate member" in str(e)
        mok("duplicate member rejected")

    # Single-member merge group rejected
    try:
        bc.assemble_merged_group("module p\n", "module c\n", [("qa_m1.ax", m1)])
        raise AssertionError("1-member merge group should be rejected")
    except ValueError as e:
        assert "at least 2 members" in str(e)
        mok("1-member merge group rejected")

    # Member module slice + const extraction works independently per member
    m_blob1 = (
        "// test: run\n// stdout: OK B1\\n\n\nmodule main\n"
        "const DATA: [3]u8 = [65u8, 66u8, 67u8];\n"
        "const OFF: [2]u32 = [0u32, 3u32];\n"
        "pub fn main() -> i32 { 0 }\n"
    )
    m_blob2 = (
        "// test: run\n// stdout: OK B2\\n\n\nmodule main\n"
        "const DATA: [2]u8 = [88u8, 89u8];\n"
        "const OFF: [2]u32 = [0u32, 2u32];\n"
        "pub fn main() -> i32 { 0 }\n"
    )
    merged_blobs = bc.assemble_merged_group("module p\n", "module c\n", [("qa_b1.ax", m_blob1), ("qa_b2.ax", m_blob2)])
    s1 = bc.extract_module_slice(merged_blobs, "__case_qa_b1")
    s2 = bc.extract_module_slice(merged_blobs, "__case_qa_b2")
    assert "65u8, 66u8, 67u8" in s1 and "88u8" not in s1
    assert "88u8, 89u8" in s2 and "65u8" not in s2
    mok("extract_module_slice isolates identical const names per member")

    # QA adversarial checks (T488 gate):
    # 6. Identical helper/const/struct names isolated across non-`main` module header and omitted module header
    m_iso1 = (
        "// test: run\n// stdout: OK ISO1\\n\n\n"
        "module selfhost_custom_a\n"
        "const LIMIT: usize = 7;\n"
        "struct Item { x: i32 }\n"
        "fn helper(v: i32) -> i32 { v + 1 }\n"
        "pub fn main() -> i32 { let it = Item { x: helper(1) }; if it.x == 2 && LIMIT == 7 { print(\"OK ISO1\\n\"); 0 } else { 1 } }\n"
    )
    m_iso2 = (
        "// test: run\n// stdout: OK ISO2\\n\n\n"
        "const LIMIT: usize = 9;\n"
        "struct Item { x: i32 }\n"
        "fn helper(v: i32) -> i32 { v + 2 }\n"
        "fn main() -> i32 { let it = Item { x: helper(1) }; if it.x == 3 && LIMIT == 9 { print(\"OK ISO2\\n\"); 0 } else { 1 } }\n"
    )
    merged_iso = bc.assemble_merged_group("module p\n", "module c\n", [("qa_iso_a.ax", m_iso1), ("qa_iso_b.ax", m_iso2)])
    iso_s1 = bc.extract_module_slice(merged_iso, "__case_qa_iso_a")
    iso_s2 = bc.extract_module_slice(merged_iso, "__case_qa_iso_b")
    assert "module selfhost_custom_a" not in merged_iso
    assert "module __case_qa_iso_a\n" in iso_s1 and "fn helper(v: i32) -> i32 { v + 1 }" in iso_s1
    assert "module __case_qa_iso_b\n" in iso_s2 and "fn helper(v: i32) -> i32 { v + 2 }" in iso_s2
    assert "pub fn __t488_run() -> i32" in iso_s1 and "pub fn __t488_run() -> i32" in iso_s2
    assert "fn main(" not in iso_s1 and "fn main(" not in iso_s2
    mok("symbol isolation preserves identical helper/const/struct names across custom/missing module headers")

    # 7. Duplicate stem rejected across `.ax` and bare stem spellings
    try:
        bc.assemble_merged_group("module p\n", "module c\n", [("qa_dup.ax", m1), ("qa_dup", m2)])
        raise AssertionError("duplicate stem across .ax and bare form should be rejected")
    except ValueError as e:
        assert "duplicate member qa_dup" in str(e)
        mok("duplicate stem rejected across .ax and bare spellings")

    # 8. Member missing `fn main(` rejected clearly
    m_no_main = "// test: run\n// stdout: OK NM\\n\n\nmodule main\npub fn not_main() -> i32 { 0 }\n"
    try:
        bc.assemble_merged_group("module p\n", "module c\n", [("qa_m1.ax", m1), ("qa_no_main.ax", m_no_main)])
        raise AssertionError("member missing fn main( should be rejected")
    except ValueError as e:
        assert "could not find `fn main(`" in str(e) and "qa_no_main.ax" in str(e)
        mok("member missing fn main rejected")

    # 9. Failure continuation across 3 members + flag preservation/deduplication
    m_f1 = "// test: run\n// flags: -O1\n// stdout: OK F1\\n\n\nmodule main\npub fn main() -> i32 { 0 }\n"
    m_f2 = "// test: run\n// flags: -O1\n// flags: --stack-reserve=2097152\n// stdout: OK F2\\n\n\nmodule main\npub fn main() -> i32 { 0 }\n"
    m_f3 = "// test: run\n// stdout: OK F3\\n\n\nmodule main\npub fn main() -> i32 { 0 }\n"
    merged_3 = bc.assemble_merged_group(
        "module p\n",
        "module c\n",
        [("qa_f1.ax", m_f1), ("qa_f2.ax", m_f2), ("qa_f3.ax", m_f3)],
    )
    assert merged_3.count("// flags: -O1\n") == 1
    assert merged_3.count("// flags: --stack-reserve=2097152\n") == 1
    drv = bc.extract_module_slice(merged_3, "main")
    assert "return" not in drv, "driver must not early-return on member failure"
    assert drv.index("__run_0()") < drv.index("__run_1()") < drv.index("__run_2()")
    assert drv.count("__failed = 1;") == 3
    assert "\n    __failed\n}" in drv
    mok("3-member driver continues after failure with deduplicated flags")

    # 10. extract_blobs_from_member / extract_ints_from_member isolate per-member goldens + fallback + missing error
    m_g1 = (
        "// test: run\n// stdout: OK G1\\n\n\nmodule main\n"
        "const DATA: [3]u8 = [65u8, 66u8, 67u8];\n"
        "const OFF: [2]u32 = [0u32, 3u32];\n"
        "const RCS: [2]i32 = [0i32, -2i32];\n"
        "pub fn main() -> i32 { 0 }\n"
    )
    m_g2 = (
        "// test: run\n// stdout: OK G2\\n\n\nmodule main\n"
        "const DATA: [2]u8 = [88u8, 89u8];\n"
        "const OFF: [2]u32 = [0u32, 2u32];\n"
        "const RCS: [2]i32 = [1i32, 101i32];\n"
        "pub fn main() -> i32 { 0 }\n"
    )
    merged_g = bc.assemble_merged_group("module p\n", "module c\n", [("qa_g1.ax", m_g1), ("qa_g2.ax", m_g2)])
    with tempfile.TemporaryDirectory() as td:
        mp = os.path.join(td, "qa_g_merged.ax")
        fb = os.path.join(td, "qa_g1.ax")
        missing = os.path.join(td, "does_not_exist.ax")
        bc.write_bytes(mp, merged_g.encode("utf-8"))
        bc.write_bytes(fb, m_g1.encode("utf-8"))
        assert bc.extract_blobs_from_member(mp, "qa_g1.ax", "DATA", "OFF") == [b"ABC"]
        assert bc.extract_blobs_from_member(mp, "qa_g2.ax", "DATA", "OFF") == [b"XY"]
        assert bc.extract_ints_from_member(mp, "qa_g1.ax", "RCS") == [0, -2]
        assert bc.extract_ints_from_member(mp, "qa_g2.ax", "RCS") == [1, 101]
        assert bc.extract_blobs_from_member(missing, "qa_g1.ax", "DATA", "OFF", fallback_path=fb) == [b"ABC"]
        try:
            bc.extract_const_block_from_member(missing, "qa_g1.ax", "DATA", fallback_path=missing)
            raise AssertionError("missing merged and fallback should raise FileNotFoundError")
        except FileNotFoundError:
            pass
    mok("extract_blobs/ints_from_member isolates goldens, supports fallback, and errors when absent")

    print("bundle_common merge selftest: %d checks passed" % merge_passed)
    return 0


if __name__ == "__main__":
    sys.exit(main())
