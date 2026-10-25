#!/usr/bin/env python3
"""Differential test generator for compiler/own_mir_verify (T082).

Assembles selfhost test bundles in tests/selfhost/own_mir_verify/ that test the
integrated compiler.own_mir_verify session pipeline against axiom0 and cdriver_drop_oracle:

  - qa_own_mir_diff_build_a.ax, qa_own_mir_diff_build_b.ax
  - qa_own_mir_diff_drop_a.ax, qa_own_mir_diff_drop_b.ax
  - qa_own_mir_diff_diag_own_a.ax, qa_own_mir_diff_diag_own_b.ax
  - qa_own_mir_diff_diag_init.ax
  - qa_own_mir_diff_diag_cap_ptr.ax
  - qa_own_mir_diff_diag_verify_mir.ax

Usage:
  python tests/selfhost/own_mir_verify/gen_own_mir_verify_tests.py \
      [--axiom0 <path/to/axiom0.exe>] [--oracle <path/to/ct_selfhost_drop_cdriver_drop_oracle.exe>] [--check]
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tests", "selfhost"))

import bundle_common as bc  # noqa: E402

MODULES = [
    ("compiler.kernel.id", "compiler"),
    ("compiler.kernel.hash", "compiler"),
    ("compiler.kernel.arena", "compiler"),
    ("compiler.kernel.interner", "compiler"),
    ("compiler.source.span", "compiler"),
    ("compiler.source.manager", "compiler"),
    ("compiler.diag.code", "compiler"),
    ("compiler.diag.emitter", "compiler"),
    ("compiler.diag.format", "compiler"),
    ("compiler.diag.json", "compiler"),
    ("compiler.kernel_source_diag.session", "compiler"),
    ("compiler.lex.token", "compiler"),
    ("compiler.lex.scanner", "compiler"),
    ("compiler.lexer.session", "compiler"),
    ("compiler.syntax.ast", "compiler"),
    ("compiler.syntax.parse", "compiler"),
    ("compiler.parser.session", "compiler"),
    ("compiler.resolve.symtab", "compiler"),
    ("compiler.resolve.rib", "compiler"),
    ("compiler.resolve.resolver", "compiler"),
    ("compiler.hir.hir", "compiler"),
    ("compiler.hir.lower", "compiler"),
    ("compiler.resolve_hir.session", "compiler"),
    ("compiler.types.types", "compiler"),
    ("compiler.types.layout", "compiler"),
    ("compiler.types.exhaust", "compiler"),
    ("compiler.traits.solver", "compiler"),
    ("compiler.traits.mono", "compiler"),
    ("compiler.types.typeck", "compiler"),
    ("compiler.types", "compiler"),
    ("compiler.traits", "compiler"),
    ("compiler.typeck.session", "compiler"),
    ("compiler.typeck", "compiler"),
    ("compiler.typeck_traits.session", "compiler"),
    ("compiler.typeck_traits", "compiler"),
    ("compiler.mir.mir", "compiler"),
    ("compiler.mir.drop", "compiler"),
    ("compiler.mir.builder", "compiler"),
    ("compiler.mir", "compiler"),
    ("compiler.own.move", "compiler"),
    ("compiler.own.cap", "compiler"),
    ("compiler.own.init", "compiler"),
    ("compiler.own.unsafe", "compiler"),
    ("compiler.own", "compiler"),
    ("compiler.verify.verifier", "compiler"),
    ("compiler.verify", "compiler"),
    ("compiler.own_mir_verify.session", "compiler"),
    ("compiler.own_mir_verify", "compiler"),
]

PRELUDE = bc.build_prelude_text(include_sym_pad=True, sym_pad_count=800, include_std_sys=False, root=ROOT)

MIR_BUILD_GROUPS = [
    ("build_a", "BUILD_A", [
        "calls",
        "first_mir",
    ], False),
    ("build_b", "BUILD_B", [
        "bitnot",
        "div_assert",
        "mul_assert",
        "qa_eval_order",
        "shift_assert",
        "short_circuit",
        "unary_neg_assert",
    ], True),
]

DROP_GROUPS = [
    ("drop_a", "DROP_A", [
        "d01_scope_exit",
    ], False),
    ("drop_b", "DROP_B", [
        "d02_conditional_move",
        "d03_struct_fields",
        "d04_enum_variants",
        "d05_mixed_nesting",
        "d06_control_flow",
        "d07_call_results",
        "d09_closures",
        "d10_destructor",
        "d11_qa_edges",
    ], True),
]

DIAG_GROUPS = [
    ("own_a", "OWN_A", [
        ("tests/ui/own/use_after_move.ax", ["AX_MOVE_USE_AFTER_MOVE"], 1),
        ("tests/ui/own/uninit.ax", ["AX_INIT_USE_UNINIT"], 0),
    ], [], False),
    ("own_b", "OWN_B", [
        ("tests/ui/own/branch_reinit_move.ax", ["AX_MOVE_USE_AFTER_MOVE"], 1),
        ("tests/ui/own/conditional_move.ax", ["AX_MOVE_USE_AFTER_MOVE"], 1),
        ("tests/ui/own/loop_move.ax", ["AX_MOVE_USE_AFTER_MOVE"], 1),
        ("tests/ui/own/nested_partial_move.ax", ["AX_MOVE_USE_AFTER_MOVE"], 1),
        ("tests/ui/own/param_move.ax", ["AX_MOVE_USE_AFTER_MOVE"], 1),
        ("tests/ui/own/partial_move.ax", ["AX_MOVE_USE_AFTER_MOVE"], 1),
        ("tests/ui/own/partial_move_struct.ax", ["AX_MOVE_USE_AFTER_MOVE"], 1),
        ("tests/ui/own/qa_drop_uam_double.ax", ["AX_MOVE_USE_AFTER_MOVE"], 1),
        ("tests/ui/own/qa_explicit_drop_uam.ax", ["AX_MOVE_USE_AFTER_MOVE"], 1),
        ("tests/ui/own/uninit.ax", ["AX_INIT_USE_UNINIT"], 0),
        ("tests/ui/own/use_after_move.ax", ["AX_MOVE_USE_AFTER_MOVE"], 1),
    ], [], True),
    ("init", "INIT", [
        ("tests/ui/init/cond_init.ax", ["AX_INIT_USE_UNINIT"], 0),
        ("tests/ui/init/cond_reinit.ax", ["AX_MOVE_USE_AFTER_MOVE"], 1),
        ("tests/ui/init/loop_uninit.ax", ["AX_INIT_USE_UNINIT"], 0),
        ("tests/ui/init/partial_init.ax", ["AX_INIT_USE_UNINIT"], 0),
        ("tests/ui/init/qa_partial_struct_use.ax", ["AX_INIT_USE_UNINIT"], 0),
        ("tests/ui/init/reinit_after_move.ax", ["AX_MOVE_USE_AFTER_MOVE"], 1),
        ("tests/ui/init/uninit_basic.ax", ["AX_INIT_USE_UNINIT"], 0),
    ], [], True),
    ("cap_ptr", "CAP_PTR", [
        ("tests/ui/cap/test_view.ax", [
            "AX_TYPE_STORED_VIEW_SELF_REF",
            "AX_TYPE_STORED_VIEW_ESCAPE",
            "AX_TYPE_STORED_VIEW_ESCAPE",
        ], 0),
        ("tests/ui/cap/test_view_cap.ax", [
            "AX_CAP_OUTLIVES_OWNER",
            "AX_CAP_CONFLICT_READ",
            "AX_CAP_CONFLICT_MUT",
            "AX_CAP_OUTLIVES_OWNER",
        ], 0),
        ("tests/ui/cap/test_view_qa.ax", [
            "AX_CAP_CONFLICT_MUT",
            "AX_CAP_OUTLIVES_OWNER",
        ], 0),
        # T157 (SPEC-11 AXS-CAP-004/009): owner-outlives with droppable and i32 owners.
        ("tests/ui/cap/view_outlives_drop_owner.ax", [
            "AX_CAP_OUTLIVES_OWNER",
            "AX_CAP_OUTLIVES_OWNER",
            "AX_CAP_OUTLIVES_OWNER",
        ], 0),
        ("tests/ui/ptr/addrof_outside_unsafe.ax", ["AX_UNSAFE_REQUIRED"], 0),
        ("tests/ui/ptr/arith_outside_unsafe.ax", ["AX_UNSAFE_REQUIRED"], 0),
        ("tests/ui/ptr/call_outside_unsafe.ax", ["AX_UNSAFE_REQUIRED"], 0),
        ("tests/ui/ptr/deref_outside_unsafe.ax", ["AX_UNSAFE_REQUIRED"], 0),
    ], [], True),
    ("verify_mir", "VERIFY_MIR", [], [
        ("tests/verify/bad_target.mir", ["AX_VERIFY_BAD_TARGET"]),
        ("tests/verify/call_signature.mir", ["AX_VERIFY_CALL_SIGNATURE"]),
        ("tests/verify/return_type.mir", []),
        ("tests/verify/type_mismatch.mir", ["AX_VERIFY_TYPE_MISMATCH"]),
        ("tests/verify/type_mismatch_binop.mir", ["AX_VERIFY_TYPE_MISMATCH"]),
        ("tests/verify/type_mismatch_cast.mir", ["AX_VERIFY_TYPE_MISMATCH"]),
        ("tests/verify/uninit_cond.mir", ["AX_VERIFY_UNINIT_USE"]),
        ("tests/verify/uninit_use.mir", ["AX_VERIFY_UNINIT_USE"]),
        ("tests/verify/unknown_local.mir", ["AX_VERIFY_UNKNOWN_LOCAL"]),
        ("tests/verify/unknown_local_storage.mir", ["AX_VERIFY_UNKNOWN_LOCAL"]),
        ("tests/verify/unterminated_block.mir", ["AX_VERIFY_UNTERMINATED_BLOCK"]),
        ("tests/verify/own/call_unwind_owned.mir", ["AX_VERIFY_MISSING_DROP", "AX_VERIFY_MISSING_DROP"]),
        ("tests/verify/own/conditional_move.mir", ["AX_VERIFY_USE_AFTER_MOVE", "AX_VERIFY_MISSING_DROP"]),
        ("tests/verify/own/double_drop.mir", ["AX_VERIFY_DOUBLE_DROP"]),
        ("tests/verify/own/missing_drop.mir", ["AX_VERIFY_MISSING_DROP"]),
        ("tests/verify/own/missing_drop_no_unreachable.mir", ["AX_VERIFY_MISSING_DROP"]),
        ("tests/verify/own/overwrite_owned.mir", ["AX_VERIFY_MISSING_DROP"]),
        ("tests/verify/own/qa_conditional_double_drop.mir", ["AX_VERIFY_DOUBLE_DROP"]),
        ("tests/verify/own/qa_loop_move.mir", ["AX_VERIFY_USE_AFTER_MOVE", "AX_VERIFY_MISSING_DROP"]),
        ("tests/verify/own/return_moved.mir", ["AX_VERIFY_USE_AFTER_MOVE"]),
        ("tests/verify/own/use_after_move.mir", [
            "AX_VERIFY_USE_AFTER_MOVE",
            "AX_VERIFY_MISSING_DROP",
            "AX_VERIFY_MISSING_DROP",
        ]),
    ], False),
]


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def byte_table(name, data):
    if not data:
        return "const %s: [1]u8 = [0u8];" % name
    lines = ["const %s: [%d]u8 = [" % (name, len(data))]
    for i in range(0, len(data), 16):
        chunk = data[i:i + 16]
        lines.append("    " + ", ".join("%du8" % b for b in chunk) + ",")
    lines.append("];")
    return "\n".join(lines)


def u32_table(name, values):
    if not values:
        return "const %s: [1]u32 = [0u32];" % name
    lines = ["const %s: [%d]u32 = [" % (name, len(values))]
    for i in range(0, len(values), 10):
        chunk = values[i:i + 10]
        lines.append("    " + ", ".join("%du32" % v for v in chunk) + ",")
    lines.append("];")
    return "\n".join(lines)


def code_table(name, codes):
    if not codes:
        return "const %s: [1]u32 = [0u32];" % name
    lines = ["const %s: [%d]u32 = [" % (name, len(codes))]
    for c in codes:
        lines.append("    %s," % c)
    lines.append("];")
    return "\n".join(lines)


def assemble_modules():
    return bc.assemble_compiler_modules(MODULES, root=ROOT)


def find_exe(default_rels):
    for rel in default_rels:
        p = os.path.join(ROOT, *rel.split("/"))
        if os.path.isfile(p):
            return p
    return None


def run_oracle_drop(oracle, rel_ax):
    cmd = [os.path.abspath(oracle), "--std-root", "std", rel_ax]
    res = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode != 0:
        raise SystemExit("oracle failed on %s: %s" % (rel_ax, res.stderr.decode("utf-8", "replace")))
    out = res.stdout.replace(b"\r\n", b"\n")
    header = ("== %s\n" % rel_ax).encode("utf-8")
    if out.startswith(header):
        out = out[len(header):]
    return out


def run_axiom0_check_stderr(axiom0, rel_ax):
    cmd = [os.path.abspath(axiom0), "check", rel_ax]
    res = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if res.returncode == 0:
        raise SystemExit("expected axiom0 check to fail on %s" % rel_ax)
    return res.stderr.replace(b"\r\n", b"\n")


def build_mir_diff_bundle(modules_text, group, upper, items, native_only):
    blobs = []
    synth_flags = []
    prelude_flags = []
    for path_rel, src_bytes, pre_bytes, drop_bytes, synth_bytes, has_synth, needs_prelude in items:
        blobs.append(path_rel.encode("utf-8"))
        blobs.append(src_bytes)
        blobs.append(pre_bytes)
        blobs.append(drop_bytes)
        blobs.append(synth_bytes)
        synth_flags.append(1 if has_synth else 0)
        prelude_flags.append(1 if needs_prelude else 0)
    data = b"".join(blobs)
    offsets = [0]
    for b in blobs:
        offsets.append(offsets[-1] + len(b))

    template = read_bytes(os.path.join(HERE, "harness_mir_diff.ax.in")).decode("utf-8")
    main_src = (
        template
        .replace("@CASE_COUNT@", str(len(items)))
        .replace("@GROUP@", upper)
        .replace("@DATA_TABLE@", byte_table("CASE_DATA", data))
        .replace("@OFFSET_TABLE@", u32_table("CASE_OFF", offsets))
        .replace("@SYNTH_TABLE@", u32_table("CASE_SYNTH", synth_flags))
        .replace("@PRELUDE_TABLE@", u32_table("CASE_PRELUDE", prelude_flags))
    )
    twin_name = "qa_own_mir_diff_build_a.ax" if group.startswith("build") else "qa_own_mir_diff_drop_a.ax"
    modes_line = (
        "// modes: native\n"
        "// Reason: heavy selfhost MIR+drop batch; small interp twin is %s.\n" % twin_name
    ) if native_only else ""
    header = (
        "// test: run\n"
        "// timeout: 1200\n"
        "%s"
        "// stdout: OK own_mir_verify %s (%d cases)\\n\n"
        "// Generated by tests/selfhost/own_mir_verify/gen_own_mir_verify_tests.py; do not edit.\n\n"
    ) % (modes_line, upper, len(items))
    full_text = header + PRELUDE + "\n" + modules_text + "\n" + main_src
    out_path = os.path.join(HERE, "qa_own_mir_diff_%s.ax" % group)
    return out_path, full_text


def build_diag_diff_bundle(modules_text, axiom0, group, upper, ax_cases, mir_cases, native_only):
    out_path = os.path.join(HERE, "qa_own_mir_diff_diag_%s.ax" % group)
    old_ax_blobs = None
    if not axiom0 and ax_cases and os.path.isfile(out_path):
        old_ax_blobs = bc.extract_blobs_from_bundle(out_path, "AX_DATA", "AX_OFF")

    ax_blobs = []
    ax_counts = []
    ax_code_offs = [0]
    ax_codes = []
    ax_moved_lbl = []

    for idx, (rel_path, codes, has_moved_lbl) in enumerate(ax_cases):
        src_bytes = read_bytes(os.path.join(ROOT, *rel_path.split("/"))).replace(b"\r\n", b"\n")
        if axiom0:
            exp_human = run_axiom0_check_stderr(axiom0, rel_path)
        else:
            exp_human = old_ax_blobs[3 * idx + 2]
        ax_blobs.append(rel_path.encode("utf-8"))
        ax_blobs.append(src_bytes)
        ax_blobs.append(exp_human)
        ax_counts.append(len(codes))
        ax_codes.extend(codes)
        ax_code_offs.append(len(ax_codes))
        ax_moved_lbl.append(has_moved_lbl)

    ax_data = b"".join(ax_blobs)
    ax_offs = [0]
    for b in ax_blobs:
        ax_offs.append(ax_offs[-1] + len(b))

    mir_blobs = []
    mir_counts = []
    mir_code_offs = [0]
    mir_codes = []

    for rel_path, codes in mir_cases:
        src_bytes = read_bytes(os.path.join(ROOT, *rel_path.split("/"))).replace(b"\r\n", b"\n")
        mir_blobs.append(rel_path.encode("utf-8"))
        mir_blobs.append(src_bytes)
        mir_counts.append(len(codes))
        mir_codes.extend(codes)
        mir_code_offs.append(len(mir_codes))

    mir_data = b"".join(mir_blobs)
    mir_offs = [0]
    for b in mir_blobs:
        mir_offs.append(mir_offs[-1] + len(b))

    template = read_bytes(os.path.join(HERE, "harness_diag_diff.ax.in")).decode("utf-8")
    main_src = (
        template
        .replace("@AX_CASE_COUNT@", str(len(ax_cases)))
        .replace("@MIR_CASE_COUNT@", str(len(mir_cases)))
        .replace("@GROUP@", upper)
        .replace("@AX_DATA_TABLE@", byte_table("AX_DATA", ax_data))
        .replace("@AX_OFFSET_TABLE@", u32_table("AX_OFF", ax_offs))
        .replace("@AX_EXP_COUNTS@", u32_table("AX_EXP_COUNTS", ax_counts))
        .replace("@AX_EXP_OFF@", u32_table("AX_EXP_OFF", ax_code_offs))
        .replace("@AX_EXP_CODES@", code_table("AX_EXP_CODES", ax_codes))
        .replace("@AX_EXP_MOVED_LBL@", u32_table("AX_EXP_MOVED_LBL", ax_moved_lbl))
        .replace("@MIR_DATA_TABLE@", byte_table("MIR_DATA", mir_data))
        .replace("@MIR_OFFSET_TABLE@", u32_table("MIR_OFF", mir_offs))
        .replace("@MIR_EXP_COUNTS@", u32_table("MIR_EXP_COUNTS", mir_counts))
        .replace("@MIR_EXP_OFF@", u32_table("MIR_EXP_OFF", mir_code_offs))
        .replace("@MIR_EXP_CODES@", code_table("MIR_EXP_CODES", mir_codes))
    )
    modes_line = (
        "// modes: native\n"
        "// Reason: heavy selfhost UI corpus batch; small interp twin is qa_own_mir_diff_diag_own_a.ax.\n"
    ) if native_only else ""
    header = (
        "// test: run\n"
        "// timeout: 1200\n"
        "%s"
        "// stdout: OK own_mir_verify diag %s (%d ax + %d mir)\\n\n"
        "// Generated by tests/selfhost/own_mir_verify/gen_own_mir_verify_tests.py; do not edit.\n\n"
    ) % (modes_line, upper, len(ax_cases), len(mir_cases))
    full_text = header + PRELUDE + "\n" + modules_text + "\n" + main_src
    return out_path, full_text


def main():
    args = sys.argv[1:]
    check_mode = "--check" in args or "check" in args
    axiom0 = None
    oracle = None
    if "--axiom0" in args:
        axiom0 = args[args.index("--axiom0") + 1]
    if "--oracle" in args:
        oracle = args[args.index("--oracle") + 1]

    modules_text = assemble_modules()
    outs = []

    for group, upper, names, native_only in MIR_BUILD_GROUPS:
        out_path = os.path.join(HERE, "qa_own_mir_diff_%s.ax" % group)
        old_blobs = None
        if not oracle and os.path.isfile(out_path):
            old_blobs = bc.extract_blobs_from_bundle(out_path, "CASE_DATA", "CASE_OFF")
        items = []
        for idx, name in enumerate(names):
            rel_ax = "tests/mir/build/%s.ax" % name
            rel_mir = "tests/mir/build/%s.mir" % name
            src_bytes = read_bytes(os.path.join(ROOT, *rel_ax.split("/"))).replace(b"\r\n", b"\n")
            pre_bytes = read_bytes(os.path.join(ROOT, *rel_mir.split("/"))).replace(b"\r\n", b"\n")
            if oracle:
                drop_bytes = run_oracle_drop(oracle, rel_ax)
            else:
                drop_bytes = old_blobs[5 * idx + 3]
            items.append((rel_ax, src_bytes, pre_bytes, drop_bytes, b"", False, False))
        outs.append(build_mir_diff_bundle(modules_text, group, upper, items, native_only))

    prelude_drop_cases = {"d03_struct_fields", "d09_closures", "d10_destructor", "d11_qa_edges"}
    for group, upper, names, native_only in DROP_GROUPS:
        items = []
        for name in names:
            rel_ax = "tests/selfhost/drop/fixtures/%s.ax" % name
            base_dir = os.path.join(ROOT, "tests", "selfhost", "drop", "fixtures")
            src_bytes = read_bytes(os.path.join(base_dir, name + ".ax")).replace(b"\r\n", b"\n")
            pre_bytes = read_bytes(os.path.join(base_dir, name + ".pre.mir")).replace(b"\r\n", b"\n")
            drop_bytes = read_bytes(os.path.join(base_dir, name + ".drop.mir")).replace(b"\r\n", b"\n")
            synth_path = os.path.join(base_dir, name + ".synth.mir")
            has_synth = os.path.isfile(os.path.join(base_dir, name + ".impl.ax")) and os.path.isfile(synth_path)
            synth_bytes = read_bytes(synth_path).replace(b"\r\n", b"\n") if has_synth else b""
            needs_prelude = name in prelude_drop_cases
            items.append((rel_ax, src_bytes, pre_bytes, drop_bytes, synth_bytes, has_synth, needs_prelude))
        outs.append(build_mir_diff_bundle(modules_text, group, upper, items, native_only))

    for group, upper, ax_cases, mir_cases, native_only in DIAG_GROUPS:
        outs.append(build_diag_diff_bundle(modules_text, axiom0, group, upper, ax_cases, mir_cases, native_only))

    return bc.write_or_check_bundles(outs, check_mode, root=ROOT)


if __name__ == "__main__":
    sys.exit(main())
