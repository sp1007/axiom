#!/usr/bin/env python3
"""E19.3 / T810 Semantic AST Diff/Merge/Patch & Lineage History Engine (`AXDIFF`,
`AXMERGE`, `AXPATCH`, `AXHISTORY`, `AXVCS`) and CLI Driver (`compiler.driver.refactor_cmd`)
verification oracle.

1. Bundles `std/editor/mod.ax` + `std/vcs/mod.ax` + `compiler.query.db` + `compiler.lsp.*`
   + `compiler.refactor.transforms` + `compiler.refactor.vcs.{diff,merge,patch,mod}`
   + `compiler.driver.refactor_cmd` + `semantic_vcs_probe.ax.in` and executes across
   `--interp`, `-O0`, `-O1`, and `-O2 --verify-each`.
2. Runs standalone `.ax` fixtures in `tests/run/semantic_vcs/` across `--interp`, `-O0`,
   `-O1`, and `-O2 --verify-each`, verifying exact `.stdout` parity.
"""

from __future__ import annotations

import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "tests" / "selfhost"))

import bundle_common as bc  # noqa: E402

PROBE_TEMPLATE = HERE / "semantic_vcs_probe.ax.in"

EXPECTED_PROBE_STDOUT = (
    "P1_AXDIFF_FMT_SEM=0 P1_MOVED=1 P1_RENAMED=1 P1_BREAKING=3 P1_INCOMP=8\n"
    "P2_AXMERGE_IMPORTS=14 P2_IDEM=true P2_REN_BODY=true P2_SEM_CONFLICT_DIAG=3101\n"
    "P3_AXPATCH_RELOC=1 P3_ROLLBACK=true P3_COMPOSE_REN=1 P3_REBASE_KEY=21\n"
    "P4_AXHIST_HOPS=4 P4_BLAME_SKIP_FMT=2 P4_TREE_DET=true P4_CAS_CONFLICT=3\n"
    "P5_CLI_DIFF_OK=0 P5_CLI_BRK=1 P5_CLI_MERGE_OK=0 P5_CLI_BAD=2 CODEGEN=0\n"
)

POSITIVE_FIXTURES = [
    (
        "axdiff_tree_vs_text_and_semantic_diff",
        "axdiff_tree_vs_text_and_semantic_diff.ax",
        "axdiff_tree_vs_text_and_semantic_diff.stdout",
    ),
    (
        "axmerge_ast_auto_merge_and_semantic_conflicts",
        "axmerge_ast_auto_merge_and_semantic_conflicts.ax",
        "axmerge_ast_auto_merge_and_semantic_conflicts.stdout",
    ),
    (
        "axpatch_atomic_transactions_and_rebase",
        "axpatch_atomic_transactions_and_rebase.ax",
        "axpatch_atomic_transactions_and_rebase.stdout",
    ),
    (
        "axhistory_lineage_and_axvcs_determinism",
        "axhistory_lineage_and_axvcs_determinism.ax",
        "axhistory_lineage_and_axvcs_determinism.stdout",
    ),
]

SEMANTIC_VCS_BUNDLE_MODULES = [
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
    ("compiler.refactor.vcs.diff", "compiler"),
    ("compiler.refactor.vcs.merge", "compiler"),
    ("compiler.refactor.vcs.patch", "compiler"),
    ("compiler.refactor.vcs", "compiler"),
    ("compiler.driver.refactor_cmd", "compiler"),
]


def get_axiomc(compiler: str, build_dir: str, tmp_dir: str, root: str) -> str:
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


def assemble_semantic_vcs_probe(root: str, template_path: pathlib.Path) -> str:
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
    modules_src = bc.assemble_compiler_modules(SEMANTIC_VCS_BUNDLE_MODULES, root=root)
    main_src = template_path.read_text(encoding="utf-8")
    return prelude + "\n" + editor_src + "\n" + vcs_src + "\n" + modules_src + "\n" + main_src


def resolve_fixture_path(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "run" / "semantic_vcs" / filename
    if cand.is_file():
        return cand
    return HERE / filename


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: semantic_vcs_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir_str = os.path.abspath(sys.argv[3])
    root = os.path.abspath(sys.argv[4])
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir, tmp_dir_str, root))
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    # 1. Assemble and execute bundled semantic_vcs probe across --interp, -O0, -O1, -O2 (--verify-each)
    probe_template = resolve_fixture_path(root, "semantic_vcs_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "semantic_vcs_probe_bundle.ax"
    probe_bundle.write_text(assemble_semantic_vcs_probe(root, probe_template), encoding="utf-8", newline="\n")

    iproc = run_cmd([axiomc, "run", "--interp", str(probe_bundle)], root, timeout=180)
    if iproc.returncode != 0:
        sys.stderr.write(f"semantic_vcs_probe --interp failed ({iproc.returncode}):\n{iproc.stdout}\n{iproc.stderr}\n")
        return 1
    norm_interp_probe = iproc.stdout.replace("\r\n", "\n")
    if norm_interp_probe != EXPECTED_PROBE_STDOUT:
        sys.stderr.write(
            f"stdout mismatch for semantic_vcs_probe under --interp:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_interp_probe}\n"
        )
        return 1

    for flag in ("-O0", "-O1", "-O2"):
        probe_exe = tmp_dir / f"semantic_vcs_probe_{flag[1:]}{exe_ext}"
        bproc = run_cmd(
            [axiomc, "build", "--stack-reserve=67108864", flag, "--verify-each", "-o", str(probe_exe), str(probe_bundle)],
            root,
            timeout=180,
        )
        if bproc.returncode != 0:
            sys.stderr.write(f"build semantic_vcs_probe {flag} --verify-each failed:\n{bproc.stdout}\n{bproc.stderr}\n")
            return 1
        rproc = run_cmd([str(probe_exe)], root, timeout=120)
        if rproc.returncode != 0:
            sys.stderr.write(
                f"semantic_vcs_probe {flag} failed with exit code {rproc.returncode}:\n{rproc.stderr}\nstdout:\n{rproc.stdout}\n"
            )
            return 1
        norm_probe = rproc.stdout.replace("\r\n", "\n")
        if norm_probe != EXPECTED_PROBE_STDOUT:
            sys.stderr.write(
                f"stdout mismatch for semantic_vcs_probe under {flag}:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_probe}\n"
            )
            return 1

    # 2. Differential execution of positive fixtures across --interp, -O0, -O1, -O2 (--verify-each)
    for stem, filename, stdout_filename in POSITIVE_FIXTURES:
        src_path = resolve_fixture_path(root, filename)
        exp_path = resolve_fixture_path(root, stdout_filename)
        exp_out = exp_path.read_text(encoding="utf-8").replace("\r\n", "\n")

        f_interp = run_cmd([axiomc, "run", "--interp", str(src_path)], root, timeout=120)
        if f_interp.returncode != 0:
            sys.stderr.write(f"interp {stem} failed with {f_interp.returncode}:\n{f_interp.stderr}\n")
            return 1
        if f_interp.stdout.replace("\r\n", "\n") != exp_out:
            sys.stderr.write(f"stdout mismatch for {stem} under --interp\n")
            return 1

        for flag in ("-O0", "-O1", "-O2"):
            exe_path = tmp_dir / f"{stem}_{flag[1:]}{exe_ext}"
            bproc = run_cmd([axiomc, "build", flag, "--verify-each", "-o", str(exe_path), str(src_path)], root)
            if bproc.returncode != 0:
                sys.stderr.write(f"build {stem} {flag} --verify-each failed:\n{bproc.stderr}\n")
                return 1
            rproc = run_cmd([str(exe_path)], root)
            if rproc.returncode != 0:
                sys.stderr.write(f"run {stem} {flag} failed with {rproc.returncode}:\n{rproc.stderr}\n")
                return 1
            if rproc.stdout.replace("\r\n", "\n") != exp_out:
                sys.stderr.write(f"stdout mismatch for {stem} under {flag}\n")
                return 1

    sys.stdout.buffer.write(b"SEMANTIC-VCS-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
