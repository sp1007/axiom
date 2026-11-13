#!/usr/bin/env python3
"""E15.2 Conformance Suite Oracle (T608; SPEC-71):
End-to-end differential conformance suite covering capability-driven alias analysis,
MemorySSA store-to-load/RLE/DSE/memcpy optimization, intraprocedural & interprocedural
escape analysis (NoEscape / ArgumentEscape / ReturnEscape / GlobalEscape, recursive SCC
summaries), explicit closure semantic signatures & capability enforcement (REQ-OPT-385,
REQ-OPT-386), allocation promotion & observation barriers (REQ-OPT-307, REQ-OPT-308,
REQ-OPT-309), and caller-allocated return-slot optimization (NRVO / sret, REQ-OPT-310)
across --interp, -O0, -O1, and -O2 --verify-each.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
PROBE_TEMPLATE = HERE / "e15_2_conformance_probe.ax.in"

EXPECTED_PROBE_STDOUT = (
    "PROBE_E15_2_ALIAS_AND_MEMOPT=OK\n"
    "PROBE_E15_2_CLOSURE_SIGNATURE_AND_CAP=OK\n"
    "PROBE_E15_2_ESCAPE_LATTICE_SCC_AND_BARRIERS=OK\n"
    "PROBE_E15_2_PROMOTIONS_NRVO_AND_ROLLBACK=OK\n"
    "PROBE_E15_2_ALL=OK\n"
)

CONFORMANCE_DIFF_FIXTURES: list[tuple[str, str, str]] = [
    (
        "alias_cap_forwarding_rle_dse",
        "alias_cap_forwarding_rle_dse.ax",
        "Xin chào E15.2 alias_cap_forwarding_rle_dse\n"
        "mut_forward_rle=245\n"
        "field_const_dyn=605\n"
        "seq_reborrow=173\n"
        "loop_backedge=385\n"
        "raw_ptr_alias=910\n"
        "checksum=2318\n",
    ),
    (
        "escape_box_buffer_slot_promotion",
        "escape_box_buffer_slot_promotion.ax",
        "Xin chào E15.2 escape_box_buffer_slot_promotion\n"
        "box_sroa=318\n"
        "box_stack_scc=792\n"
        "inline_buf_vec=546\n"
        "disjoint_slots=684\n"
        "checksum=2340\n",
    ),
    (
        "closure_signature_capture_promotion",
        "closure_signature_capture_promotion.ax",
        "Xin chào E15.2 closure_signature_capture_promotion\n"
        "noncap_and_copy=380\n"
        "view_capture=294\n"
        "mut_view_capture=515\n"
        "move_capture=427\n"
        "checksum=1616\n",
    ),
    (
        "nrvo_return_slot_and_drop_parity",
        "nrvo_return_slot_and_drop_parity.ax",
        "Xin chào E15.2 nrvo_return_slot_and_drop_parity\n"
        "nrvo_struct=460\n"
        "nrvo_branch_array=524\n"
        "nrvo_conflict_guard=395\n"
        "drop_lifo_trace=1234\n"
        "checksum=2613\n",
    ),
    (
        "stable_address_and_escape_barriers",
        "stable_address_and_escape_barriers.ax",
        "Xin chào E15.2 stable_address_and_escape_barriers\n"
        "identity_distinct=210\n"
        "stable_addr_obs=345\n"
        "sink_and_loop_heap=628\n"
        "oversized_and_memops=492\n"
        "checksum=1675\n",
    ),
]

CAP_PROBE_BLOBS: list[bytes] = [
    # Blob 38: Closure/view capturing `&mut _1` while shared view `_2 = &_1` is still used -> AX_CAP_CONFLICT_MUT
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let mut _1: type#8;\n"
        b"    let _2: type#17;\n"
        b"    let _3: type#18;\n"
        b"    bb0: {\n"
        b"        _1 = const 10: type#8;\n"
        b"        _2 = &_1;\n"
        b"        _3 = &mut _1;\n"
        b"        (*_3) = const 20: type#8;\n"
        b"        _0 = copy (*_2);\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 39: Closure/view capturing `&_1` while mutable view `_2 = &mut _1` is still used -> AX_CAP_CONFLICT_READ
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let mut _1: type#8;\n"
        b"    let _2: type#18;\n"
        b"    let _3: type#17;\n"
        b"    bb0: {\n"
        b"        _1 = const 10: type#8;\n"
        b"        _2 = &mut _1;\n"
        b"        _3 = &_1;\n"
        b"        (*_2) = copy (*_3);\n"
        b"        _0 = copy (*_2);\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # Blob 40: Disjoint mutable capture borrows -> 0 capability errors
    (
        b"mir_body {\n"
        b"    let mut _0: type#8; // return\n"
        b"    let mut _1: type#8;\n"
        b"    let mut _2: type#8;\n"
        b"    let _3: type#18;\n"
        b"    let _4: type#18;\n"
        b"    bb0: {\n"
        b"        _1 = const 10: type#8;\n"
        b"        _2 = const 20: type#8;\n"
        b"        _3 = &mut _1;\n"
        b"        (*_3) = const 15: type#8;\n"
        b"        _4 = &mut _2;\n"
        b"        (*_4) = const 25: type#8;\n"
        b"        _0 = copy (*_3);\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
]


def get_axiomc(compiler: str, build_dir: str, tmp_dir: str, root: str) -> str:
    base = os.path.basename(compiler).lower()
    if base.startswith("axiomc"):
        return compiler
    for cand in ("axiomc2.exe", "axiomc1.exe", "axiomc.exe", "axiomc2", "axiomc1", "axiomc"):
        p = os.path.join(build_dir, cand)
        if os.path.isfile(p):
            return p
    sys.path.insert(0, os.path.join(root, "tests", "selfhost", "obj_link_driver"))
    import gen_obj_link_driver_tests as gen  # noqa: E402

    bundle_ax = os.path.join(tmp_dir, "axiomc_bundle.ax")
    with open(bundle_ax, "wb") as f:
        f.write(gen.axiomc_bundle_text().encode("utf-8"))
    out_exe = os.path.join(tmp_dir, "axiomc.exe" if os.name == "nt" else "axiomc")
    cmd = [compiler, "build", "--stack-reserve=67108864", "-o", out_exe, bundle_ax]
    r = subprocess.run(cmd, cwd=root, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=600)
    if r.returncode != 0:
        sys.stderr.write("failed to build axiomc:\n" + r.stderr.decode("utf-8", "replace"))
        raise SystemExit(1)
    return out_exe


def run_cmd(args: list[str], cwd: str | None = None, timeout: int = 300) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        args,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def load_all_e15_2_blobs(root: str) -> list[bytes]:
    opt_escape_dir = os.path.join(root, "tests", "run", "opt_escape")
    opt_alias_dir = os.path.join(root, "tests", "run", "opt_alias")
    if opt_escape_dir not in sys.path:
        sys.path.insert(0, opt_escape_dir)
    if opt_alias_dir not in sys.path:
        sys.path.insert(0, opt_alias_dir)

    import opt_alias_oracle as oao  # noqa: E402
    import opt_escape_oracle as oeo  # noqa: E402

    # Blobs 0..32: ESCAPE_PROBE_BLOBS (33 blobs)
    # Blobs 33..37: ALIAS_PROBE_BLOBS[0..5] (5 blobs)
    # Blobs 38..40: CAP_PROBE_BLOBS (3 blobs)
    return list(oeo.ESCAPE_PROBE_BLOBS) + list(oao.ALIAS_PROBE_BLOBS[:5]) + list(CAP_PROBE_BLOBS)


def assemble_e15_2_probe(root: str, probe_template_path: pathlib.Path) -> str:
    selfhost_dir = os.path.join(root, "tests", "selfhost")
    selfhost_opt_dir = os.path.join(selfhost_dir, "opt")
    if selfhost_dir not in sys.path:
        sys.path.insert(0, selfhost_dir)
    if selfhost_opt_dir not in sys.path:
        sys.path.insert(0, selfhost_opt_dir)

    import bundle_common as bc  # noqa: E402
    import gen_opt_tests as got  # noqa: E402

    blobs = load_all_e15_2_blobs(root)
    template_text = probe_template_path.read_text(encoding="utf-8")
    main_src = template_text.replace("@PROBE_MIR_FN@", got.str_fn("probe_mir_raw", blobs))
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=False, root=root)
    e15_2_modules = list(got.CORE_MODULES) + [
        ("compiler.opt.alias", "compiler"),
        ("compiler.opt.memopt", "compiler"),
        ("compiler.opt.escape", "compiler"),
    ]
    modules_src = bc.assemble_compiler_modules(e15_2_modules, root=root)
    return prelude + "\n" + modules_src + "\n" + main_src


def resolve_fixture_path(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "conformance" / "p15" / "e15_2_alias_escape" / filename
    if cand.is_file():
        return cand
    return HERE / filename


def verify_pe_binary(exe_path: pathlib.Path) -> bool:
    if not exe_path.is_file() or exe_path.stat().st_size <= 512:
        return False
    if os.name == "nt" and exe_path.read_bytes()[:2] != b"MZ":
        return False
    return True


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: e15_2_conformance_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir_str = os.path.abspath(sys.argv[3])
    root = os.path.abspath(sys.argv[4])
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir, tmp_dir_str, root))
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    # 1. Assemble and execute the 6-module E15.2 probe under -O0, -O1, and -O2 --verify-each
    probe_template = resolve_fixture_path(root, "e15_2_conformance_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "e15_2_conformance_probe_bundle.ax"
    probe_bundle.write_text(assemble_e15_2_probe(root, probe_template), encoding="utf-8", newline="\n")

    for flag in ("-O0", "-O1", "-O2"):
        probe_exe = tmp_dir / f"e15_2_probe_{flag[1:]}{exe_ext}"
        bproc = run_cmd(
            [axiomc, "build", "--stack-reserve=67108864", flag, "--verify-each", "-o", str(probe_exe), str(probe_bundle)],
            root,
            timeout=300,
        )
        if bproc.returncode != 0:
            sys.stderr.write(f"build e15_2_probe {flag} --verify-each failed:\n{bproc.stdout}\n{bproc.stderr}\n")
            return 1
        if not verify_pe_binary(probe_exe):
            sys.stderr.write(f"invalid PE binary produced for e15_2_probe {flag}\n")
            return 1
        rproc = run_cmd([str(probe_exe)], root, timeout=120)
        if rproc.returncode != 0:
            sys.stderr.write(
                f"e15_2_probe {flag} failed with exit code {rproc.returncode}:\n{rproc.stderr}\nstdout:\n{rproc.stdout}\n"
            )
            return 1
        norm_probe = rproc.stdout.replace("\r\n", "\n")
        if norm_probe != EXPECTED_PROBE_STDOUT:
            sys.stderr.write(
                f"stdout mismatch for e15_2_probe under {flag}:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_probe}\n"
            )
            return 1

    # 2. Differential execution of all 5 E15.2 conformance fixtures across --interp, -O0, -O1, -O2 (--verify-each)
    for stem, filename, exp_out in CONFORMANCE_DIFF_FIXTURES:
        src_path = resolve_fixture_path(root, filename)
        iproc = run_cmd([axiomc, "run", "--interp", str(src_path)], root, timeout=120)
        if iproc.returncode != 0:
            sys.stderr.write(f"interp {stem} failed with {iproc.returncode}:\n{iproc.stderr}\n")
            return 1
        norm_interp = iproc.stdout.replace("\r\n", "\n")
        if norm_interp != exp_out:
            sys.stderr.write(f"stdout mismatch for {stem} under --interp:\nexpected:\n{exp_out}\ngot:\n{norm_interp}\n")
            return 1

        for flag in ("-O0", "-O1", "-O2"):
            exe_path = tmp_dir / f"{stem}_{flag[1:]}{exe_ext}"
            bproc = run_cmd([axiomc, "build", flag, "--verify-each", "-o", str(exe_path), str(src_path)], root)
            if bproc.returncode != 0:
                sys.stderr.write(f"build {stem} {flag} --verify-each failed:\n{bproc.stderr}\n")
                return 1
            if not verify_pe_binary(exe_path):
                sys.stderr.write(f"invalid PE binary produced for {stem} {flag}\n")
                return 1
            rproc = run_cmd([str(exe_path)], root)
            if rproc.returncode != 0:
                sys.stderr.write(f"run {stem} {flag} failed with {rproc.returncode}:\n{rproc.stderr}\n")
                return 1
            norm_out = rproc.stdout.replace("\r\n", "\n")
            if norm_out != exp_out:
                sys.stderr.write(f"stdout mismatch for {stem} under {flag}:\nexpected:\n{exp_out}\ngot:\n{norm_out}\n")
                return 1

    # 3. Deterministic --emit=optir and --emit=memssa inspection across -O0, -O1, -O2 --verify-each
    inspect_src = resolve_fixture_path(root, "closure_signature_capture_promotion.ax")
    for flag in ("-O0", "-O1", "-O2"):
        o1 = run_cmd([axiomc, "inspect", "--emit=optir", flag, "--verify-each", str(inspect_src)], root)
        o2 = run_cmd([axiomc, "inspect", "--emit=optir", flag, "--verify-each", str(inspect_src)], root)
        if o1.returncode != 0 or o2.returncode != 0 or o1.stdout != o2.stdout or not o1.stdout.strip():
            sys.stderr.write(f"deterministic --emit=optir {flag} failed:\n{o1.stderr}\n")
            return 1
        m1 = run_cmd([axiomc, "inspect", "--emit=memssa", flag, "--verify-each", str(inspect_src)], root)
        m2 = run_cmd([axiomc, "inspect", "--emit=memssa", flag, "--verify-each", str(inspect_src)], root)
        if m1.returncode != 0 or m2.returncode != 0 or m1.stdout != m2.stdout or not m1.stdout.strip():
            sys.stderr.write(f"deterministic --emit=memssa {flag} failed:\n{m1.stderr}\n")
            return 1

    sys.stdout.buffer.write(b"E15.2-ALIAS-ESCAPE-PROMOTE-CONFORMANCE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
