#!/usr/bin/env python3
"""E19.1 / T802 Semantic IDE Queries (`hover`, `definition`, `typeDefinition`, `implementation`,
`references`, `documentSymbol`, `workspace/symbol`, constraint-filtered `completion`,
conflict-checked `prepareRename` & `rename`), `AXCODEEDITOR` presentation layer
(`semanticTokens`, `inlayHint`, highlight layer precedence), `axiomc lsp` CLI driver,
and `tools/vscode-axiom/` thin client verification oracle.

1. Bundles `std/editor/mod.ax` + `compiler.query.db` + `compiler.lsp.protocol` + `compiler.lsp.vfs`
   + `compiler.lsp.handlers` + `compiler.driver.lsp_cmd` + `lsp_queries_probe.ax.in` and runs
   across `--interp`, `-O0`, `-O1`, and `-O2 --verify-each`.
2. Runs standalone `.ax` tests in `tests/run/lsp_queries/` across `--interp`, `-O0`, `-O1`,
   and `-O2 --verify-each`, verifying exact `.stdout` parity.
3. Validates `tools/vscode-axiom/` (`package.json`, `language-configuration.json`,
   `syntaxes/axiom.tmLanguage.json`, `extension.js`, `README.md`) per `SPEC-100 §6.3 AXS-LSP-052`.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "tests" / "selfhost"))

import bundle_common as bc  # noqa: E402

PROBE_TEMPLATE = HERE / "lsp_queries_probe.ax.in"

EXPECTED_PROBE_STDOUT = "\n".join(
    [
        "100401",
        "100402",
        "100403",
        "100404",
        "100405",
        "100406",
        "100407",
        "0",
    ]
) + "\n"

POSITIVE_FIXTURES = [
    (
        "hover_and_navigation",
        "hover_and_navigation.ax",
        "200401\n200402\n0\n",
    ),
    (
        "completion_constraints_and_ambiguity",
        "completion_constraints_and_ambiguity.ax",
        "200403\n200404\n200405\n0\n",
    ),
    (
        "hygienic_rename_and_axcodeeditor_inlays",
        "hygienic_rename_and_axcodeeditor_inlays.ax",
        "200406\n200407\n0\n",
    ),
]

LSP_QUERIES_BUNDLE_MODULES = [
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
    ("compiler.driver.lsp_cmd", "compiler"),
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


def assemble_lsp_queries_probe(root: str, template_path: pathlib.Path) -> str:
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=root)
    editor_path = pathlib.Path(root) / "std" / "editor" / "mod.ax"
    if not editor_path.is_file():
        editor_path = REPO_ROOT / "std" / "editor" / "mod.ax"
    editor_src = editor_path.read_text(encoding="utf-8").replace(
        "use std.core.host.", "use host_intrinsics."
    )
    modules_src = bc.assemble_compiler_modules(LSP_QUERIES_BUNDLE_MODULES, root=root)
    main_src = template_path.read_text(encoding="utf-8")
    return prelude + "\n" + editor_src + "\n" + modules_src + "\n" + main_src


def resolve_fixture_path(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "run" / "lsp_queries" / filename
    if cand.is_file():
        return cand
    return HERE / filename


def verify_vscode_client(root: str) -> None:
    ext_dir = pathlib.Path(root) / "tools" / "vscode-axiom"
    if not ext_dir.is_dir():
        ext_dir = REPO_ROOT / "tools" / "vscode-axiom"
    pkg_path = ext_dir / "package.json"
    lang_cfg_path = ext_dir / "language-configuration.json"
    tm_path = ext_dir / "syntaxes" / "axiom.tmLanguage.json"
    js_path = ext_dir / "extension.js"
    readme_path = ext_dir / "README.md"

    for p in (pkg_path, lang_cfg_path, tm_path, js_path, readme_path):
        if not p.is_file():
            raise RuntimeError(f"Missing VS Code thin client file: {p}")

    pkg = json.loads(pkg_path.read_text(encoding="utf-8"))
    langs = pkg.get("contributes", {}).get("languages", [])
    if not any(l.get("id") == "axiom" and ".ax" in l.get("extensions", []) for l in langs):
        raise RuntimeError("package.json must register language id 'axiom' with '.ax' extension")

    mods = {m.get("id") for m in pkg.get("contributes", {}).get("semanticTokenModifiers", [])}
    required_mods = {"ownedValue", "readView", "mutView", "movedValue"}
    if not required_mods.issubset(mods):
        raise RuntimeError(f"package.json missing required AXCODEEDITOR semanticTokenModifiers: {required_mods - mods}")

    _ = json.loads(lang_cfg_path.read_text(encoding="utf-8"))
    tm = json.loads(tm_path.read_text(encoding="utf-8"))
    if tm.get("scopeName") != "source.axiom":
        raise RuntimeError("axiom.tmLanguage.json must declare scopeName 'source.axiom'")

    js_src = js_path.read_text(encoding="utf-8")
    if '"lsp"' not in js_src or '"--stdio"' not in js_src:
        raise RuntimeError("extension.js must spawn 'axiomc lsp --stdio'")
    if "LanguageClient" not in js_src:
        raise RuntimeError("extension.js must use LanguageClient")


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: lsp_queries_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir_str = os.path.abspath(sys.argv[3])
    root = os.path.abspath(sys.argv[4])
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir, tmp_dir_str, root))
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    # 1. Verify thin VS Code client extension (`tools/vscode-axiom/`) (`AXS-LSP-052`)
    verify_vscode_client(root)

    # 2. Assemble and execute direct std.editor + compiler.lsp.handlers + compiler.driver.lsp_cmd probe
    probe_template = resolve_fixture_path(root, "lsp_queries_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "lsp_queries_probe_bundle.ax"
    probe_bundle.write_text(assemble_lsp_queries_probe(root, probe_template), encoding="utf-8", newline="\n")

    iproc = run_cmd([axiomc, "run", "--interp", str(probe_bundle)], root, timeout=180)
    if iproc.returncode != 0:
        sys.stderr.write(f"lsp_queries_probe --interp failed ({iproc.returncode}):\n{iproc.stdout}\n{iproc.stderr}\n")
        return 1
    norm_interp_probe = iproc.stdout.replace("\r\n", "\n")
    if norm_interp_probe != EXPECTED_PROBE_STDOUT:
        sys.stderr.write(
            f"stdout mismatch for lsp_queries_probe under --interp:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_interp_probe}\n"
        )
        return 1

    for flag in ("-O0", "-O1", "-O2"):
        probe_exe = tmp_dir / f"lsp_queries_probe_{flag[1:]}{exe_ext}"
        bproc = run_cmd(
            [axiomc, "build", "--stack-reserve=67108864", flag, "--verify-each", "-o", str(probe_exe), str(probe_bundle)],
            root,
            timeout=180,
        )
        if bproc.returncode != 0:
            sys.stderr.write(f"build lsp_queries_probe {flag} --verify-each failed:\n{bproc.stdout}\n{bproc.stderr}\n")
            return 1
        rproc = run_cmd([str(probe_exe)], root, timeout=120)
        if rproc.returncode != 0:
            sys.stderr.write(
                f"lsp_queries_probe {flag} failed with exit code {rproc.returncode}:\n{rproc.stderr}\nstdout:\n{rproc.stdout}\n"
            )
            return 1
        norm_probe = rproc.stdout.replace("\r\n", "\n")
        if norm_probe != EXPECTED_PROBE_STDOUT:
            sys.stderr.write(
                f"stdout mismatch for lsp_queries_probe under {flag}:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_probe}\n"
            )
            return 1

    # 3. Differential execution of positive fixtures across --interp, -O0, -O1, -O2 (--verify-each)
    for stem, filename, exp_out in POSITIVE_FIXTURES:
        src_path = resolve_fixture_path(root, filename)
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

    sys.stdout.buffer.write(b"LSP-QUERIES-ENGINE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
