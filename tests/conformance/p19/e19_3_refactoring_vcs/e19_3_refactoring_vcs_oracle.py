#!/usr/bin/env python3
"""End-to-end E19.3 Conformance Oracle (`T811` / `SPEC-102` `AXS-REF-001..063`,
`INV-REF-001..003`, `REQ-TOOL-183`, `REQ-TOOL-186`, `REQ-TOOL-301..305`):
Semantic Refactoring Engine, LSP `codeAction` / `codeAction/resolve`, and
`AXDIFF` / `AXMERGE` / `AXPATCH` / `AXHISTORY` / `AXVCS` Semantic Version Control.

Steps:
1. Bundles the live `std/editor/mod.ax`, `std/vcs/mod.ax`, `compiler/query/db/mod.ax`,
   `compiler/lsp/protocol/mod.ax`, `compiler/lsp/vfs/mod.ax`, `compiler/lsp/handlers/mod.ax`,
   `compiler/refactor/transforms/mod.ax`, `compiler/refactor/code_actions/mod.ax`,
   `compiler/refactor/vcs/diff.ax`, `compiler/refactor/vcs/merge.ax`,
   `compiler/refactor/vcs/patch.ax`, `compiler/refactor/vcs/mod.ax`, and
   `compiler/driver/refactor_cmd/mod.ax` modules with `e19_3_refactoring_vcs_probe.ax.in`,
   executes the bundle in `--interp`, and compiles + executes it AT MOST ONCE at `-O0`
   (per <120s resource rule), verifying byte-for-byte identical output and zero
   backend codegen during refactoring/VCS queries.
2. Runs differential verification (`--interp` vs native `-O1 --verify-each`) across
   all 4 standalone `.ax` conformance tests in `tests/conformance/p19/e19_3_refactoring_vcs/`.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "tests" / "selfhost"))

import bundle_common as bc  # noqa: E402

PROBE_TEMPLATE = HERE / "e19_3_refactoring_vcs_probe.ax.in"

EXPECTED_PROBE_STDOUT = (
    "probe[refactor_transforms] ext_params=3 ext_ret=1 rej_move=3101 rej_view=3008 ev_occ=2 inl_parens=1 pm_added=2 org_kept=3 org_pruned=1 org_merged=1 cs_sites=1 mv_edits=3 cv_diag=3001\n"
    "probe[code_actions_and_gate] ca_total=6 ca_qf=3 ca_ref=2 ca_src=1 ca_filtered=1 resolved=true db_verified=true unsafe_diag=3201 unsafe_rollback=true stale_err=-32801\n"
    "probe[axdiff_and_axmerge] fmt_sem=0 moved=1 renamed=1 breaking=3 incomp=8 merge_imports=14 idem=true ren_body=true marker_ok=true sem_conf_diag=3101\n"
    "probe[axpatch_axhistory_axvcs] reloc=1 inv_ok=true patch_rollback=true compose_ren=1 rebase_key=21 hist_hops=4 blame_skip_fmt=2 non_res_stop=true tree_det=true cas_conflict=3 cli_ok=0 cli_brk=1 cli_bad=2 zero_codegen=true\n"
    "E19-3-REFACTORING-VCS-CONFORMANCE-PROBE-PASS\n"
)

CONFORMANCE_FIXTURES = [
    (
        "refactoring_semantics_preservation_before_after",
        "refactoring_semantics_preservation_before_after.ax",
        "refactoring_semantics_preservation_before_after.stdout",
    ),
    (
        "compiler_db_verification_gate_and_code_actions",
        "compiler_db_verification_gate_and_code_actions.ax",
        "compiler_db_verification_gate_and_code_actions.stdout",
    ),
    (
        "axdiff_and_axmerge_three_way_semantic_vcs",
        "axdiff_and_axmerge_three_way_semantic_vcs.ax",
        "axdiff_and_axmerge_three_way_semantic_vcs.stdout",
    ),
    (
        "axpatch_axhistory_and_axvcs_determinism",
        "axpatch_axhistory_and_axvcs_determinism.ax",
        "axpatch_axhistory_and_axvcs_determinism.stdout",
    ),
]

E19_3_BUNDLE_MODULES = [
    ("compiler.kernel.arena", "compiler"),
    ("compiler.kernel.hash", "compiler"),
    ("compiler.kernel.id", "compiler"),
    ("compiler.kernel.interner", "compiler"),
    ("compiler.source.span", "compiler"),
    ("compiler.source.manager", "compiler"),
    ("compiler.diag.code", "compiler"),
    ("compiler.diag.emitter", "compiler"),
    ("compiler.diag.format", "compiler"),
    ("compiler.query.db", "compiler"),
    ("compiler.lsp.protocol", "compiler"),
    ("compiler.lsp.vfs", "compiler"),
    ("compiler.lsp.handlers", "compiler"),
    ("compiler.refactor.transforms", "compiler"),
    ("compiler.refactor.code_actions", "compiler"),
    ("compiler.refactor.vcs.diff", "compiler"),
    ("compiler.refactor.vcs.merge", "compiler"),
    ("compiler.refactor.vcs.patch", "compiler"),
    ("compiler.refactor.vcs", "compiler"),
    ("compiler.driver.refactor_cmd", "compiler"),
]


def get_axiomc(compiler: str, build_dir: str) -> str:
    exe = ".exe" if os.name == "nt" else ""
    for name in (f"axiomc2{exe}", f"axiomc1{exe}", f"axiomc{exe}"):
        cand = os.path.join(build_dir, name)
        if os.path.isfile(cand):
            return cand
    return compiler


def run_cmd(cmd: list[str], cwd: str, timeout: int = 180) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        cmd,
        cwd=cwd,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=timeout,
    )


def assemble_e19_3_probe(root: str, template_path: pathlib.Path) -> str:
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=root)
    editor_path = pathlib.Path(root) / "std" / "editor" / "mod.ax"
    if not editor_path.is_file():
        editor_path = REPO_ROOT / "std" / "editor" / "mod.ax"
    editor_src = editor_path.read_text(encoding="utf-8").replace(
        "use std.core.host.", "use host_intrinsics."
    )
    vcs_path = pathlib.Path(root) / "std" / "vcs" / "mod.ax"
    if not vcs_path.is_file():
        vcs_path = REPO_ROOT / "std" / "vcs" / "mod.ax"
    vcs_src = vcs_path.read_text(encoding="utf-8").replace(
        "use std.core.host.", "use host_intrinsics."
    )
    modules_src = bc.assemble_compiler_modules(E19_3_BUNDLE_MODULES, root=root)
    main_src = template_path.read_text(encoding="utf-8")
    return prelude + "\n" + editor_src + "\n" + vcs_src + "\n" + modules_src + "\n" + main_src


def resolve_suite_file(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "conformance" / "p19" / "e19_3_refactoring_vcs" / filename
    if cand.is_file():
        return cand
    return HERE / filename


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: e19_3_refactoring_vcs_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir_str = os.path.abspath(sys.argv[3])
    root = os.path.abspath(sys.argv[4])
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir))
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    # 1. Bundle and execute live E19.3 refactoring + semantic VCS probe (`--interp` and single `-O0` build)
    probe_template = resolve_suite_file(root, "e19_3_refactoring_vcs_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "e19_3_refactoring_vcs_probe_bundle.ax"
    probe_bundle.write_text(
        assemble_e19_3_probe(root, probe_template), encoding="utf-8", newline="\n"
    )

    iproc = run_cmd([axiomc, "run", "--interp", str(probe_bundle)], root, timeout=180)
    if iproc.returncode != 0:
        sys.stderr.write(
            f"e19_3_refactoring_vcs_probe --interp failed ({iproc.returncode}):\n{iproc.stdout}\n{iproc.stderr}\n"
        )
        return 1
    norm_interp = iproc.stdout.replace("\r\n", "\n")
    if norm_interp != EXPECTED_PROBE_STDOUT:
        sys.stderr.write(
            f"stdout mismatch for e19_3_refactoring_vcs_probe under --interp:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_interp}\n"
        )
        return 1

    # Compile the compiler bundle AT MOST ONCE at `-O0` so the test completes in <120s
    probe_exe = tmp_dir / f"e19_3_refactoring_vcs_probe_O0{exe_ext}"
    bproc = run_cmd(
        [
            axiomc,
            "build",
            "--stack-reserve=67108864",
            "-O0",
            "-o",
            str(probe_exe),
            str(probe_bundle),
        ],
        root,
        timeout=120,
    )
    if bproc.returncode != 0:
        sys.stderr.write(
            f"build e19_3_refactoring_vcs_probe -O0 failed:\n{bproc.stdout}\n{bproc.stderr}\n"
        )
        return 1

    rproc = run_cmd([str(probe_exe)], root, timeout=120)
    if rproc.returncode != 0:
        sys.stderr.write(
            f"e19_3_refactoring_vcs_probe -O0 failed ({rproc.returncode}):\n{rproc.stderr}\nstdout:\n{rproc.stdout}\n"
        )
        return 1
    norm_native = rproc.stdout.replace("\r\n", "\n")
    if norm_native != EXPECTED_PROBE_STDOUT:
        sys.stderr.write(
            f"stdout mismatch for e19_3_refactoring_vcs_probe under -O0:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_native}\n"
        )
        return 1

    # 2. Differential verification of standalone `.ax` conformance fixtures (`--interp` vs `-O1 --verify-each`)
    for stem, ax_name, stdout_name in CONFORMANCE_FIXTURES:
        src_path = resolve_suite_file(root, ax_name)
        out_path = resolve_suite_file(root, stdout_name)
        exp_out = out_path.read_text(encoding="utf-8").replace("\r\n", "\n")

        f_interp = run_cmd([axiomc, "run", "--interp", str(src_path)], root, timeout=120)
        if f_interp.returncode != 0:
            sys.stderr.write(f"interp {stem} failed ({f_interp.returncode}):\n{f_interp.stderr}\n")
            return 1
        if f_interp.stdout.replace("\r\n", "\n") != exp_out:
            sys.stderr.write(f"stdout mismatch for {stem} under --interp\n")
            return 1

        fx_exe = tmp_dir / f"{stem}_O1{exe_ext}"
        fb = run_cmd(
            [axiomc, "build", "-O1", "--verify-each", "-o", str(fx_exe), str(src_path)],
            root,
            timeout=120,
        )
        if fb.returncode != 0:
            sys.stderr.write(f"build {stem} -O1 --verify-each failed:\n{fb.stderr}\n")
            return 1
        fr = run_cmd([str(fx_exe)], root, timeout=120)
        if fr.returncode != 0:
            sys.stderr.write(f"run {stem} -O1 failed ({fr.returncode}):\n{fr.stderr}\n")
            return 1
        if fr.stdout.replace("\r\n", "\n") != exp_out:
            sys.stderr.write(f"stdout mismatch for {stem} under -O1\n")
            return 1

    sys.stdout.buffer.write(b"E19-3-REFACTORING-VCS-CONFORMANCE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
