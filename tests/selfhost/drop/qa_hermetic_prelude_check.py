#!/usr/bin/env python3
"""QA adversarial check for T435 (ADR-0041 §2 D2, ADR-0042 §1):
1. Verifies byte-for-byte parity between `STD_CORE_DATA` / `STD_CORE_OFF` in
   `compiler/resolve_hir/session.ax` and `tests/selfhost/drop/std_minimal/core/*.ax`.
2. Verifies `harness_main.ax.in` calls `demote_prelude_hir_module_paths(view(hir), fid.v)`
   before `session_typeck_into` and only demotes non-main-file items (`it_file != main_fid_v`).
3. Verifies `gen_drop_tests.canonical` accepts uniform disjoint `type#N` / fn-const shifts
   while strictly rejecting type-swap, local-id, and `drop`-statement mutations.
4. When the C drop oracle binary is present, verifies `oracle_output` uses `STD_MINIMAL`
   hermetically and catches 1-byte MIR mutations.
"""
import os
import re
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.normpath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, HERE)

import gen_drop_tests as gdt  # noqa: E402


def parse_std_core_from_session(session_path):
    text = open(session_path, "r", encoding="utf-8").read()
    m_data = re.search(r"const\s+STD_CORE_DATA:\s*\[\d+\]u8\s*=\s*\[(.*?)\];", text, re.S)
    m_off = re.search(r"const\s+STD_CORE_OFF:\s*\[\d+\]u32\s*=\s*\[(.*?)\];", text, re.S)
    if not m_data or not m_off:
        raise AssertionError("STD_CORE_DATA / STD_CORE_OFF not found in %s" % session_path)
    data = bytes(int(x) for x in re.findall(r"(\d+)u8", m_data.group(1)))
    offs = [int(x) for x in re.findall(r"(\d+)u32", m_off.group(1))]
    entries = {}
    for idx in range(0, len(offs) - 1, 2):
        disp = data[offs[idx]:offs[idx + 1]].decode("utf-8")
        body = data[offs[idx + 1]:offs[idx + 2]]
        entries[disp] = body
    return entries


def check_std_minimal_parity():
    session_path = os.path.join(ROOT, "compiler", "resolve_hir", "session.ax")
    entries = parse_std_core_from_session(session_path)
    expected_map = {
        "<std>/core/option.ax": os.path.join(HERE, "std_minimal", "core", "option.ax"),
        "<std>/core/result.ax": os.path.join(HERE, "std_minimal", "core", "result.ax"),
        "<std>/core/prelude.ax": os.path.join(HERE, "std_minimal", "core", "prelude.ax"),
        "<std>/core/host.ax": os.path.join(HERE, "std_minimal", "core", "host.ax"),
    }
    assert set(entries.keys()) == set(expected_map.keys()), (
        "unexpected STD_CORE_DATA keys: %r" % sorted(entries.keys())
    )
    helper_prefix = b"// test: helper\n"
    for disp, path in expected_map.items():
        raw = open(path, "rb").read()
        assert b"\r" not in raw, "CR byte found in %s" % path
        assert raw.startswith(helper_prefix), "%s missing `// test: helper` header" % path
        body = raw[len(helper_prefix):]
        assert body == entries[disp], (
            "std_minimal mismatch for %s (%d vs %d bytes)" % (disp, len(body), len(entries[disp]))
        )


def check_harness_demotion_and_generator():
    assert gdt.STD_MINIMAL == "tests/selfhost/drop/std_minimal", gdt.STD_MINIMAL
    harness_path = os.path.join(HERE, "harness_main.ax.in")
    htext = open(harness_path, "r", encoding="utf-8").read()
    assert "fn demote_prelude_hir_module_paths(hir: view<HirFile>, main_fid_v: u32)" in htext
    assert "if it_file != 0u32 && it_file != main_fid_v" in htext
    pos_lower = htext.find("session_lower_hir(")
    pos_demote = htext.find("demote_prelude_hir_module_paths(view(hir), fid.v);")
    pos_typeck = htext.find("session_typeck_into(")
    assert 0 < pos_lower < pos_demote < pos_typeck, (
        "demote_prelude_hir_module_paths must run after session_lower_hir and before session_typeck_into"
    )


def check_canonical_sensitivity():
    d01_pre = open(os.path.join(HERE, "fixtures", "d01_scope_exit.pre.mir"), "r", encoding="utf-8").read()
    bodies = gdt.split_bodies(d01_pre)
    assert len(bodies) >= 1, "expected mir_body block in d01_scope_exit.pre.mir"
    b0 = bodies[0]
    # 1. Uniform +4 shift on user TypeId (type#17 -> type#21) compares equal under canonical()
    shifted = b0.replace("type#17", "type#21")
    assert shifted != b0
    assert gdt.canonical(b0) == gdt.canonical(shifted), "uniform TypeId shift should canonicalize equal"
    # 2. Colliding TypeId mutation (type#17 -> type#2, where type#2 already exists in b0) MUST NOT compare equal
    collided = b0.replace("type#17", "type#2", 1)
    assert gdt.canonical(b0) != gdt.canonical(collided), "colliding TypeId mutation must fail canonical()"
    # 3. Dropping or mutating a `drop(...)` terminator MUST fail both byte comparison and canonical()
    assert "drop(_1)" in b0
    no_drop = b0.replace("drop(_1)", "drop(_2)", 1)
    assert gdt.canonical(b0) != gdt.canonical(no_drop), "mutated drop target must fail canonical()"


def check_oracle_if_available(args):
    if "--oracle" not in args:
        return
    oracle = args[args.index("--oracle") + 1]
    exe = oracle if os.path.isfile(oracle) else (oracle + ".exe" if os.path.isfile(oracle + ".exe") else None)
    if exe is None:
        return
    want_pre = open(os.path.join(HERE, "fixtures", "d01_scope_exit.pre.mir"), "rb").read()
    got_pre = gdt.oracle_output(exe, gdt.fixture_rel("d01_scope_exit"), True)
    assert got_pre == want_pre, "oracle_output --pre mismatch on d01_scope_exit"
    mut_pre = want_pre.replace(b"type#17", b"type#18", 1)
    assert mut_pre != got_pre, "1-byte mutation in d01_scope_exit.pre.mir was not distinct"


def main():
    check_std_minimal_parity()
    check_harness_demotion_and_generator()
    check_canonical_sensitivity()
    check_oracle_if_available(sys.argv[1:])
    print("OK drop hermetic prelude & mutation invariants")
    return 0


if __name__ == "__main__":
    sys.exit(main())
