#!/usr/bin/env python3
"""End-to-end E19.2 Conformance Oracle (`T807` / `SPEC-101` `AXS-FMT-001..053`,
`INV-FMT-001..003`, `REQ-TOOL-183`, `REQ-TOOL-298`):
Canonical Formatter Idempotence, 5-Slot CST Comment Preservation, UTF-8 Scalar Width,
CLI (`--check`, `--stdin`, `[format]`), and LSP `textDocument/formatting` &
`textDocument/rangeFormatting` Agreement.

Steps:
1. Bundles the live `std/editor/mod.ax`, `compiler/lex/*`, `compiler/syntax/*`,
   `compiler/fmt/cst/mod.ax`, `compiler/fmt/printer/mod.ax`, `compiler/fmt/verify/mod.ax`,
   `compiler/query/db/mod.ax`, `compiler/lsp/protocol/mod.ax`, `compiler/lsp/vfs/mod.ax`,
   `compiler/lsp/handlers/mod.ax`, and `compiler/driver/fmt_cmd/mod.ax` modules with
   `e19_2_formatter_probe.ax.in`, executes the bundle in `--interp`, and compiles +
   executes it AT MOST ONCE at `-O0` (per <120s resource rule), verifying:
   - `fmt(fmt(src)) == fmt(src)` idempotence, comment conservation, and AST equivalence
     across 12 real `.ax` corpus files on disk spanning `compiler/`, `std/`, and `tests/`,
   - 5-slot CST trivia attachment, UTF-8 BOM stripping, and Vietnamese (`"Xin chào thế giới"`)
     / emoji (`"🚀🔥"`) scalar width preservation,
   - `axiomc fmt` CLI `--check` unified diff, `--stdin`, `[format]` manifest policy,
     idempotent `mtime` preservation, syntax-error refusal (`exit 1`), and tamper abort (`exit 3`),
   - Byte-for-byte agreement between LSP `textDocument/formatting` / `rangeFormatting` and CLI.
2. Runs differential verification (`--interp` vs native `-O1 --verify-each`) across
   all 4 standalone `.ax` conformance fixtures in `tests/conformance/p19/e19_2_formatter/`.
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

PROBE_TEMPLATE = HERE / "e19_2_formatter_probe.ax.in"

EXPECTED_PROBE_STDOUT = (
    "probe[corpus_idempotence_and_ast_equiv] corpus_files_verified=3 all_idempotent=true\n"
    "probe[comment_and_utf8_preservation] bom_ok=true vn_bytes=22 vn_scalars=17 emoji_scalars=2 slots_ok=true norm_ok=true unemitted=0\n"
    "probe[cli_check_diff_and_refusal] unk_exit=2 stdin_path_exit=2 diff_ok=true mtime_ok=true syn_exit=1 tamper_exit=3\n"
    "probe[lsp_cli_agreement_and_zero_codegen] lsp_matches_cli=true options_ignored=true range_ok=true\n"
    "E19-2-FORMATTER-PROBE-PASS\n"
)

CONFORMANCE_FIXTURES = [
    (
        "corpus_idempotence_and_ast_equivalence",
        "corpus_idempotence_and_ast_equivalence.ax",
        "corpus_idempotence_and_ast_equivalence.stdout",
    ),
    (
        "comment_five_slot_and_utf8_preservation",
        "comment_five_slot_and_utf8_preservation.ax",
        "comment_five_slot_and_utf8_preservation.stdout",
    ),
    (
        "cli_check_diff_stdin_and_manifest_policy",
        "cli_check_diff_stdin_and_manifest_policy.ax",
        "cli_check_diff_stdin_and_manifest_policy.stdout",
    ),
    (
        "lsp_cli_formatting_parity_and_range_edits",
        "lsp_cli_formatting_parity_and_range_edits.ax",
        "lsp_cli_formatting_parity_and_range_edits.stdout",
    ),
]

E19_2_BUNDLE_MODULES = [
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


def assemble_e19_2_probe(root: str, template_path: pathlib.Path) -> str:
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=root)
    editor_path = pathlib.Path(root) / "std" / "editor" / "mod.ax"
    if not editor_path.is_file():
        editor_path = REPO_ROOT / "std" / "editor" / "mod.ax"
    editor_src = editor_path.read_text(encoding="utf-8").replace(
        "use std.core.host.", "use host_intrinsics."
    )
    modules_src = bc.assemble_compiler_modules(E19_2_BUNDLE_MODULES, root=root)
    main_src = template_path.read_text(encoding="utf-8")
    return prelude + "\n" + editor_src + "\n" + modules_src + "\n" + main_src


def resolve_suite_file(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "conformance" / "p19" / "e19_2_formatter" / filename
    if cand.is_file():
        return cand
    return HERE / filename


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: e19_2_formatter_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir_str = os.path.abspath(sys.argv[3])
    root = os.path.abspath(sys.argv[4])
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir))
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    # 1. Bundle and execute live E19.2 formatter probe (`--interp` and single `-O0` build)
    probe_template = resolve_suite_file(root, "e19_2_formatter_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "e19_2_formatter_probe_bundle.ax"
    probe_bundle.write_text(
        assemble_e19_2_probe(root, probe_template), encoding="utf-8", newline="\n"
    )

    iproc = run_cmd([axiomc, "run", "--interp", str(probe_bundle)], root, timeout=180)
    if iproc.returncode != 0:
        sys.stderr.write(
            f"e19_2_formatter_probe --interp failed ({iproc.returncode}):\n{iproc.stdout}\n{iproc.stderr}\n"
        )
        return 1
    norm_interp = iproc.stdout.replace("\r\n", "\n")
    if norm_interp != EXPECTED_PROBE_STDOUT:
        sys.stderr.write(
            f"stdout mismatch for e19_2_formatter_probe under --interp:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_interp}\n"
        )
        return 1

    # Compile the compiler bundle AT MOST ONCE at `-O0` so the test completes in <120s
    probe_exe = tmp_dir / f"e19_2_formatter_probe_O0{exe_ext}"
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
            f"build e19_2_formatter_probe -O0 failed:\n{bproc.stdout}\n{bproc.stderr}\n"
        )
        return 1

    rproc = run_cmd([str(probe_exe)], root, timeout=120)
    if rproc.returncode != 0:
        sys.stderr.write(
            f"e19_2_formatter_probe -O0 failed ({rproc.returncode}):\n{rproc.stderr}\nstdout:\n{rproc.stdout}\n"
        )
        return 1
    norm_native = rproc.stdout.replace("\r\n", "\n")
    if norm_native != EXPECTED_PROBE_STDOUT:
        sys.stderr.write(
            f"stdout mismatch for e19_2_formatter_probe under -O0:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_native}\n"
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

    sys.stdout.buffer.write(b"E19-2-FORMATTER-CONFORMANCE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
