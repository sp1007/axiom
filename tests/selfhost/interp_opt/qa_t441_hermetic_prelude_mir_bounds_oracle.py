#!/usr/bin/env python3
"""QA adversarial boundary oracle for T441 (ADR-0041 §2 D2, ADR-0042 §1):
(a) Verifies `gen_interp_opt_tests.py --check` and `gen_own_mir_verify_tests.py --check`
    pass and both templates call `demote_prelude_hir_module_paths(view(hir), fid.v)`
    immediately before `session_typeck_into` and pin `--std-root tests/selfhost/drop/std_minimal`.
(b) Verifies all 16 bundles across `tests/selfhost/interp_opt/*.ax` (7) and
    `tests/selfhost/own_mir_verify/*.ax` (9) declare `// test: run` with non-weak native
    evidence (`// stdout:` or non-zero `// exit:`), have `0` CR bytes, and embed unshifted
    `type#17` MIR fixtures for `d01_scope_exit.ax` (case 12 of `qa_interp_opt_diff_mir_b.ax`)
    and `d03_struct_fields.ax` (case 1 of `qa_own_mir_diff_drop_b.ax`).
(c) Runs `{compiler} inspect --emit=mir -O1` with `--std-root tests/selfhost/drop/std_minimal`
    vs an augmented temporary prelude copy (adding 2 synthetic `struct`/`enum` items to a temp
    copy of `std_minimal/core/prelude.ax`), proving that un-isolated prelude growth shifts user
    `TypeId`s (`type#21` -> `type#23`) while `demote_prelude_hir_module_paths` + pinned
    `std_minimal` keep the generated bundle fixtures hermetically locked at `type#17`.
"""
import glob
import os
import shutil
import subprocess
import sys
import tempfile


def read_no_cr(path):
    raw = open(path, "rb").read()
    assert b"\r" not in raw, "CR byte found in %s" % path
    return raw


def check_generators_and_templates(root):
    interp_dir = os.path.join(root, "tests", "selfhost", "interp_opt")
    own_dir = os.path.join(root, "tests", "selfhost", "own_mir_verify")

    gen_interp = os.path.join(interp_dir, "gen_interp_opt_tests.py")
    gen_own = os.path.join(own_dir, "gen_own_mir_verify_tests.py")
    tpl_interp = os.path.join(interp_dir, "harness_mir_opt_diff.ax.in")
    tpl_own = os.path.join(own_dir, "harness_mir_diff.ax.in")

    for p in (gen_interp, gen_own, tpl_interp, tpl_own):
        read_no_cr(p)

    for gen_script in (gen_interp, gen_own):
        res = subprocess.run(
            [sys.executable, gen_script, "--check"],
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert res.returncode == 0, "%s --check failed: %s" % (
            gen_script,
            res.stderr.decode("utf-8", "replace"),
        )
        assert b"up to date" in res.stdout, "%s --check missing 'up to date'" % gen_script

    g_interp_txt = open(gen_interp, "r", encoding="utf-8").read()
    g_own_txt = open(gen_own, "r", encoding="utf-8").read()
    assert 'STD_MINIMAL = "tests/selfhost/drop/std_minimal"' in g_interp_txt
    assert 'STD_MINIMAL = "tests/selfhost/drop/std_minimal"' in g_own_txt
    assert g_interp_txt.count('"--std-root", STD_MINIMAL') >= 2
    assert g_own_txt.count('"--std-root", STD_MINIMAL') >= 2

    for tpl_path in (tpl_interp, tpl_own):
        txt = open(tpl_path, "r", encoding="utf-8").read()
        assert "fn demote_prelude_hir_module_paths(hir: view<HirFile>, main_fid_v: u32)" in txt
        assert "if main_fid_v == 0u32 {" in txt
        assert "if it_file != 0u32 && it_file != main_fid_v {" in txt
        assert "(*it).module_path.count = 0;" in txt
        pos_lower = txt.find("session_lower_hir(")
        pos_demote = txt.find("demote_prelude_hir_module_paths(view(hir), fid.v);")
        pos_typeck = txt.find("session_typeck_into(")
        assert 0 < pos_lower < pos_demote < pos_typeck, (
            "invalid demote_prelude_hir_module_paths ordering in %s" % tpl_path
        )


def check_bundles_and_embedded_blobs(root):
    sys.path.insert(0, os.path.join(root, "tests", "selfhost"))
    import bundle_common as bc  # noqa: E402

    interp_bundles = sorted(glob.glob(os.path.join(root, "tests", "selfhost", "interp_opt", "*.ax")))
    own_bundles = sorted(glob.glob(os.path.join(root, "tests", "selfhost", "own_mir_verify", "*.ax")))
    assert len(interp_bundles) == 2, "expected 2 merged interp_opt bundles, got %d" % len(interp_bundles)
    assert len(own_bundles) == 2, "expected 2 merged own_mir_verify bundles, got %d" % len(own_bundles)

    for bpath in interp_bundles + own_bundles:
        raw = read_no_cr(bpath)
        head = raw[:2048].decode("utf-8")
        assert "// test: run\n" in head, "missing // test: run in %s" % bpath
        has_stdout = "// stdout: OK " in head
        has_nonzero_exit = ("// exit:" in head) and ("// exit: 0\n" not in head)
        assert has_stdout or has_nonzero_exit, "weak native evidence in %s" % bpath

    mir_b = os.path.join(root, "tests", "selfhost", "interp_opt", "qa_interp_opt_native.ax")
    mir_b_blobs = bc.extract_blobs_from_member(mir_b, "qa_interp_opt_diff_mir_b", "CASE_DATA", "CASE_OFF")
    # Case 12 is tests/selfhost/drop/fixtures/d01_scope_exit.ax (3 blobs per case: path, src, exp_mir_opt)
    assert mir_b_blobs[12 * 3] == b"tests/selfhost/drop/fixtures/d01_scope_exit.ax"
    d01_exp_opt = mir_b_blobs[12 * 3 + 2]
    assert b"    let _1: type#17;\n    let _2: type#17;\n" in d01_exp_opt
    assert b"    let _1: type#21;\n" not in d01_exp_opt

    drop_b = os.path.join(root, "tests", "selfhost", "own_mir_verify", "qa_own_mir_diff_native.ax")
    drop_b_blobs = bc.extract_blobs_from_member(drop_b, "qa_own_mir_diff_drop_b", "CASE_DATA", "CASE_OFF")
    # Case 1 is tests/selfhost/drop/fixtures/d03_struct_fields.ax (5 blobs per case: path, src, pre, drop, synth)
    assert drop_b_blobs[1 * 5] == b"tests/selfhost/drop/fixtures/d03_struct_fields.ax"
    d03_exp_pre = drop_b_blobs[1 * 5 + 2]
    assert b"    let _1: type#18;\n    let _2: type#17;\n" in d03_exp_pre
    assert b"    let _1: type#22;\n    let _2: type#21;\n" not in d03_exp_pre


def check_compiler_prelude_growth_isolation(compiler, root, tmp_arg):
    std_min = os.path.join(root, "tests", "selfhost", "drop", "std_minimal")
    d01_rel = "tests/selfhost/drop/fixtures/d01_scope_exit.ax"

    res_base = subprocess.run(
        [compiler, "inspect", "--std-root", std_min, "--emit=mir", "-O1", d01_rel],
        cwd=root,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    assert res_base.returncode == 0, "inspect --emit=mir -O1 failed: %s" % (
        res_base.stderr.decode("utf-8", "replace")
    )
    out_base = res_base.stdout.replace(b"\r\n", b"\n")
    # Without `demote_prelude_hir_module_paths`, `typeck_pass1a` hoists Option (2) + Result (2) -> type#21
    assert b"    let _1: type#21;\n" in out_base, "expected type#21 in un-demoted std_minimal MIR"

    parent_tmp = tmp_arg if (tmp_arg and os.path.isdir(tmp_arg)) else None
    tmp_root = tempfile.mkdtemp(prefix="qa_t441_std_", dir=parent_tmp)
    try:
        aug_std = os.path.join(tmp_root, "std_augmented")
        shutil.copytree(std_min, aug_std)
        prelude_path = os.path.join(aug_std, "core", "prelude.ax")
        with open(prelude_path, "ab") as f:
            f.write(
                b"\npub struct __QaT441ExtraStruct { pub a: i32 }\n"
                b"pub enum __QaT441ExtraEnum { A, B(i32) }\n"
            )
        res_aug = subprocess.run(
            [compiler, "inspect", "--std-root", aug_std, "--emit=mir", "-O1", d01_rel],
            cwd=root,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
        )
        assert res_aug.returncode == 0, "augmented inspect failed: %s" % (
            res_aug.stderr.decode("utf-8", "replace")
        )
        out_aug = res_aug.stdout.replace(b"\r\n", b"\n")
        # Adding 2 synthetic types to <std>/core/prelude.ax shifts user TypeId by +2 more (type#21 -> type#23)
        assert b"    let _1: type#23;\n" in out_aug, (
            "expected type#23 when 2 synthetic prelude types are hoisted"
        )
        assert out_aug != out_base
    finally:
        shutil.rmtree(tmp_root, ignore_errors=True)


def main(argv):
    if len(argv) < 3:
        raise SystemExit("usage: qa_t441_hermetic_prelude_mir_bounds_oracle.py <compiler> <root> [tmp]")
    compiler = os.path.abspath(argv[1])
    root = os.path.abspath(argv[2])
    tmp_arg = os.path.abspath(argv[3]) if len(argv) >= 4 else None

    read_no_cr(os.path.abspath(__file__))
    read_no_cr(
        os.path.join(
            root, "tests", "selfhost", "interp_opt", "qa_t441_hermetic_prelude_mir_bounds.test"
        )
    )

    check_generators_and_templates(root)
    check_bundles_and_embedded_blobs(root)
    check_compiler_prelude_growth_isolation(compiler, root, tmp_arg)
    print("OK T441 hermetic prelude MIR bounds")
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv))
