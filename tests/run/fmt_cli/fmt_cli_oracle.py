#!/usr/bin/env python3
"""Oracle and direct `compiler.fmt.verify` + `compiler.driver.fmt_cmd` +
`compiler.lsp.handlers` formatting probe runner for T806 (E19.2 `axiomc fmt`
CLI (`--check`, `--stdin`), AST equivalence verifier & LSP
`textDocument/formatting` integration; `SPEC-101`, `SPEC-100`, `REQ-TOOL-183`,
`REQ-TOOL-298`).

1. Bundles `std/editor/mod.ax`, `compiler/lex/*`, `compiler/syntax/*`,
   `compiler/fmt/cst/mod.ax`, `compiler/fmt/printer/mod.ax`,
   `compiler/fmt/verify/mod.ax`, `compiler/query/db/mod.ax`,
   `compiler/lsp/protocol/mod.ax`, `compiler/lsp/vfs/mod.ax`,
   `compiler/lsp/handlers/mod.ax`, and `compiler/driver/fmt_cmd/mod.ax` with
   `tests/run/fmt_cli/fmt_cli_probe.ax.in` and executes the direct probe in
   `--interp` and native `-O0`, `-O1`, and `-O2 --verify-each` modes.
2. Runs differential `.ax` fixtures in `tests/run/fmt_cli/` across `--interp`,
   `-O0`, `-O1`, and `-O2 --verify-each`.
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

PROBE_TEMPLATE = HERE / "fmt_cli_probe.ax.in"

EXPECTED_PROBE_STDOUT = (
    "probe[ast_verify] ok_exit=0 comments_conserved=true ast_equiv=true idempotent=true\n"
    "probe[ast_verify_tamper] dropped_comment_exit=3 mutated_ast_exit=3 semi_mismatch_exit=3 bad_reparse_exit=3 syntax_err_exit=1\n"
    "probe[cli_flags_and_manifest] unknown_opt_exit=2 stdin_with_path_exit=2 bad_manifest_exit=2 exclude_ok=true\n"
    "probe[cli_modes] check_unfmt_exit=1 diff_has_headers=true quiet_only_path=true fmt_inplace_exit=0 check_after_fmt_exit=0 mtime_preserved=true syntax_refusal_exit=1 stdin_ok=true\n"
    "probe[lsp_formatting] fmt_accepted=true options_ignored=true minimal_edit_ok=true canonical_noop_edits=0 range_fmt_ok=true broken_doc_edits=0\n"
    "FMT-CLI-PROBE-PASS\n"
)

POSITIVE_FIXTURES = [
    (
        "cli_check_stdin_and_manifest",
        "cli_check_stdin_and_manifest.ax",
        "CLI-CHECK-STDIN-AND-MANIFEST-OK\n",
    ),
    (
        "ast_equiv_and_comment_verifier",
        "ast_equiv_and_comment_verifier.ax",
        "AST-EQUIV-AND-COMMENT-VERIFIER-OK\n",
    ),
    (
        "lsp_formatting_and_range_edits",
        "lsp_formatting_and_range_edits.ax",
        "LSP-FORMATTING-AND-RANGE-EDITS-OK\n",
    ),
]

FMT_CLI_BUNDLE_MODULES = [
    ("compiler.kernel.arena", "compiler"),
    ("compiler.kernel.hash", "compiler"),
    ("compiler.kernel.id", "compiler"),
    ("compiler.kernel.interner", "compiler"),
    ("compiler.source.span", "compiler"),
    ("compiler.source.manager", "compiler"),
    ("compiler.diag.code", "compiler"),
    ("compiler.diag.emitter", "compiler"),
    ("compiler.diag.format", "compiler"),
    ("compiler.lex.token", "compiler"),
    ("compiler.lex.scanner", "compiler"),
    ("compiler.syntax.ast", "compiler"),
    ("compiler.syntax.parse", "compiler"),
    ("compiler.fmt.cst", "compiler"),
    ("compiler.fmt.printer", "compiler"),
    ("compiler.fmt.verify", "compiler"),
    ("compiler.query.db", "compiler"),
    ("compiler.lsp.protocol", "compiler"),
    ("compiler.lsp.vfs", "compiler"),
    ("compiler.lsp.handlers", "compiler"),
    ("compiler.driver.fmt_cmd", "compiler"),
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


def assemble_fmt_cli_probe(root: str, template_path: pathlib.Path) -> str:
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=root)
    editor_path = pathlib.Path(root) / "std" / "editor" / "mod.ax"
    if not editor_path.is_file():
        editor_path = REPO_ROOT / "std" / "editor" / "mod.ax"
    editor_src = editor_path.read_text(encoding="utf-8").replace(
        "use std.core.host.", "use host_intrinsics."
    )
    modules_src = bc.assemble_compiler_modules(FMT_CLI_BUNDLE_MODULES, root=root)
    main_src = template_path.read_text(encoding="utf-8")
    return prelude + "\n" + editor_src + "\n" + modules_src + "\n" + main_src


def resolve_fixture_path(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "run" / "fmt_cli" / filename
    if cand.is_file():
        return cand
    return HERE / filename


def run_probe_bundle(axiomc: str, tmp_dir: str, root: str) -> None:
    template_path = resolve_fixture_path(root, "fmt_cli_probe.ax.in")
    bundle_src = assemble_fmt_cli_probe(root, template_path)
    bundle_path = pathlib.Path(tmp_dir) / "fmt_cli_probe_bundle.ax"
    bundle_path.write_text(bundle_src, encoding="utf-8")

    r_interp = run_cmd([axiomc, "run", "--interp", str(bundle_path)], cwd=root)
    if r_interp.returncode != 0:
        raise RuntimeError(
            f"[probe --interp] exited {r_interp.returncode}:\nSTDOUT:\n{r_interp.stdout}\nSTDERR:\n{r_interp.stderr}"
        )
    if r_interp.stdout.replace("\r\n", "\n") != EXPECTED_PROBE_STDOUT:
        raise RuntimeError(
            f"[probe --interp] stdout mismatch:\nEXPECTED:\n{EXPECTED_PROBE_STDOUT}\nACTUAL:\n{r_interp.stdout}"
        )

    exe_suffix = ".exe" if os.name == "nt" else ""
    for tag, flags in (
        ("O0", ["-O0", "--verify-each"]),
        ("O1", ["-O1", "--verify-each"]),
        ("O2", ["-O2", "--verify-each"]),
    ):
        bin_path = pathlib.Path(tmp_dir) / f"fmt_cli_probe_{tag}{exe_suffix}"
        cmd = [axiomc, "build", "--stack-reserve=67108864", str(bundle_path), *flags, "-o", str(bin_path)]
        r_build = run_cmd(cmd, cwd=root)
        if r_build.returncode != 0:
            raise RuntimeError(
                f"[probe build -{tag}] exited {r_build.returncode}:\nSTDOUT:\n{r_build.stdout}\nSTDERR:\n{r_build.stderr}"
            )
        r_run = run_cmd([str(bin_path)], cwd=root)
        if r_run.returncode != 0:
            raise RuntimeError(
                f"[probe run -{tag}] exited {r_run.returncode}:\nSTDOUT:\n{r_run.stdout}\nSTDERR:\n{r_run.stderr}"
            )
        if r_run.stdout.replace("\r\n", "\n") != EXPECTED_PROBE_STDOUT:
            raise RuntimeError(
                f"[probe run -{tag}] stdout mismatch:\nEXPECTED:\n{EXPECTED_PROBE_STDOUT}\nACTUAL:\n{r_run.stdout}"
            )


def run_positive_fixture(axiomc: str, tmp_dir: str, root: str, name: str, filename: str, expected_stdout: str) -> None:
    ax_path = resolve_fixture_path(root, filename)
    r_interp = run_cmd([axiomc, "run", "--interp", str(ax_path)], cwd=root)
    if r_interp.returncode != 0:
        raise RuntimeError(
            f"[{name} --interp] exited {r_interp.returncode}:\nSTDOUT:\n{r_interp.stdout}\nSTDERR:\n{r_interp.stderr}"
        )
    if r_interp.stdout.replace("\r\n", "\n") != expected_stdout:
        raise RuntimeError(
            f"[{name} --interp] stdout mismatch:\nEXPECTED:\n{expected_stdout}\nACTUAL:\n{r_interp.stdout}"
        )

    exe_suffix = ".exe" if os.name == "nt" else ""
    for tag, flags in (
        ("O0", ["-O0", "--verify-each"]),
        ("O1", ["-O1", "--verify-each"]),
        ("O2", ["-O2", "--verify-each"]),
    ):
        bin_path = pathlib.Path(tmp_dir) / f"{name}_{tag}{exe_suffix}"
        r_build = run_cmd([axiomc, "build", str(ax_path), *flags, "-o", str(bin_path)], cwd=root)
        if r_build.returncode != 0:
            raise RuntimeError(
                f"[{name} build -{tag}] exited {r_build.returncode}:\nSTDOUT:\n{r_build.stdout}\nSTDERR:\n{r_build.stderr}"
            )
        r_run = run_cmd([str(bin_path)], cwd=root)
        if r_run.returncode != 0:
            raise RuntimeError(
                f"[{name} run -{tag}] exited {r_run.returncode}:\nSTDOUT:\n{r_run.stdout}\nSTDERR:\n{r_run.stderr}"
            )
        if r_run.stdout.replace("\r\n", "\n") != expected_stdout:
            raise RuntimeError(
                f"[{name} run -{tag}] stdout mismatch:\nEXPECTED:\n{expected_stdout}\nACTUAL:\n{r_run.stdout}"
            )


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: fmt_cli_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2
    compiler_arg = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir = os.path.abspath(sys.argv[3])
    root = os.path.abspath(sys.argv[4])

    os.makedirs(tmp_dir, exist_ok=True)
    axiomc = os.path.abspath(get_axiomc(compiler_arg, build_dir, tmp_dir, root))

    run_probe_bundle(axiomc, tmp_dir, root)
    for name, filename, expected_stdout in POSITIVE_FIXTURES:
        run_positive_fixture(axiomc, tmp_dir, root, name, filename, expected_stdout)

    sys.stdout.buffer.write(b"FMT-CLI-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
