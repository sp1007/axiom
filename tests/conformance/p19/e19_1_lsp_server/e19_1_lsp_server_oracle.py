#!/usr/bin/env python3
"""End-to-end E19.1 Conformance Oracle (`T803` / `SPEC-100` `AXS-LSP-001..063`,
`INV-LSP-001..003`, `REQ-TOOL-183..185`, `REQ-TOOL-188..189`, `REQ-TOOL-191`,
`REQ-TOOL-297..300`): Language Server (`axiomc lsp`), `CompilerDB` Semantic IDE
Engine, `AXEDITOR` / `AXCODEEDITOR`, and Thin VS Code Extension (`tools/vscode-axiom`).

Steps:
1. Validates the thin VS Code client in `tools/vscode-axiom/` (`package.json`,
   `language-configuration.json`, `syntaxes/axiom.tmLanguage.json`, `extension.js`,
   `README.md`) per `SPEC-100 §6.3 AXS-LSP-052`.
2. Bundles the live `std/editor/mod.ax`, `compiler/query/db/mod.ax`,
   `compiler/lsp/protocol/mod.ax`, `compiler/lsp/vfs/mod.ax`,
   `compiler/lsp/handlers/mod.ax`, and `compiler/driver/lsp_cmd/mod.ax` modules
   with `e19_1_lsp_server_probe.ax.in`, executes the bundle in `--interp`, and
   compiles + executes it AT MOST ONCE at `-O0` (per <120s resource rule),
   verifying byte-for-byte identical output and zero backend codegen during IDE
   queries.
3. Runs differential verification (`--interp` vs native `-O1 --verify-each`) across
   all 4 standalone `.ax` conformance tests in `tests/conformance/p19/e19_1_lsp_server/`.
"""

from __future__ import annotations

import json
import os
import pathlib
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "tests" / "selfhost"))

import bundle_common as bc  # noqa: E402

PROBE_TEMPLATE = HERE / "e19_1_lsp_server_probe.ax.in"

EXPECTED_PROBE_STDOUT = (
    "probe[session_lifecycle] pre_init=-32002 init_ok=true open_ok=true change_ok=true diag_cnt=1 hover_ok=true def_doc=0 tdef_doc=0 impl_cnt=1 refs_cnt=2 dsym_cnt=2 wsym_cnt=1 comp_cnt=4 prep_ok=true rename_edits=2 sem_toks=6 inlays=5 post_shut=-32600 exit_code=0 cancel_err=-32800 supersede_err=-32800 zero_codegen=true\n"
    "probe[axeditor_unicode_piece_tree] promoted=true tree_valid=true edits=600 vn_bytes=22 vn_utf16=17 vn_after_col=28 emoji_utf16=4 clamp_ok=true grapheme_fwd=4 grapheme_bwd=4 tx_commit=true tx_rollback=true undo_redo_ok=true\n"
    "probe[generational_ids_and_recovery] id_stable=true backdated=true stale_status=2 expected_gen=1 actual_gen=2 reused_gen=2 root_diags=5 cascades_suppressed=2 indep_fn_err=true can_codegen=false\n"
    "probe[constraints_rename_and_axcodeeditor] ro_cnt=4 ro_excl_vis=1 ro_excl_cap=1 rw_cnt=5 ambig_cnt=2 moved_cnt=0 moved_excl=6 builtin_rename=false kw_rename=false conflict_code=6001 tok_mods_ok=true inlay_mutated=false span_valid=true span_stale=false\n"
    "E19-1-LSP-SERVER-CONFORMANCE-PROBE-PASS\n"
)

CONFORMANCE_FIXTURES = [
    (
        "end_to_end_lsp_session_and_zero_codegen",
        "end_to_end_lsp_session_and_zero_codegen.ax",
        "end_to_end_lsp_session_and_zero_codegen.stdout",
    ),
    (
        "axeditor_piece_tree_and_vietnamese_utf16_spans",
        "axeditor_piece_tree_and_vietnamese_utf16_spans.ax",
        "axeditor_piece_tree_and_vietnamese_utf16_spans.stdout",
    ),
    (
        "partial_recovery_and_generational_id_stability",
        "partial_recovery_and_generational_id_stability.ax",
        "partial_recovery_and_generational_id_stability.stdout",
    ),
    (
        "completion_constraints_rename_and_axcodeeditor",
        "completion_constraints_rename_and_axcodeeditor.ax",
        "completion_constraints_rename_and_axcodeeditor.stdout",
    ),
]

E19_1_BUNDLE_MODULES = [
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


def assemble_e19_1_probe(root: str, template_path: pathlib.Path) -> str:
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=root)
    editor_path = pathlib.Path(root) / "std" / "editor" / "mod.ax"
    if not editor_path.is_file():
        editor_path = REPO_ROOT / "std" / "editor" / "mod.ax"
    editor_src = editor_path.read_text(encoding="utf-8").replace(
        "use std.core.host.", "use host_intrinsics."
    )
    modules_src = bc.assemble_compiler_modules(E19_1_BUNDLE_MODULES, root=root)
    main_src = template_path.read_text(encoding="utf-8")
    return prelude + "\n" + editor_src + "\n" + modules_src + "\n" + main_src


def resolve_suite_file(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "conformance" / "p19" / "e19_1_lsp_server" / filename
    if cand.is_file():
        return cand
    return HERE / filename


def verify_vscode_extension(root: str) -> None:
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
    if pkg.get("name") != "vscode-axiom":
        raise RuntimeError("package.json must have name 'vscode-axiom'")

    act_events = set(pkg.get("activationEvents", []))
    if "onLanguage:axiom" not in act_events:
        raise RuntimeError("package.json must include 'onLanguage:axiom' activationEvent")

    langs = pkg.get("contributes", {}).get("languages", [])
    if not any(l.get("id") == "axiom" and ".ax" in l.get("extensions", []) for l in langs):
        raise RuntimeError("package.json must register language id 'axiom' with '.ax' extension")

    mods = {m.get("id") for m in pkg.get("contributes", {}).get("semanticTokenModifiers", [])}
    required_mods = {"ownedValue", "readView", "mutView", "movedValue"}
    if not required_mods.issubset(mods):
        raise RuntimeError(
            f"package.json missing AXCODEEDITOR semanticTokenModifiers: {required_mods - mods}"
        )

    props = set(pkg.get("contributes", {}).get("configuration", {}).get("properties", {}).keys())
    required_props = {
        "axiom.lsp.serverPath",
        "axiom.lsp.positionEncoding",
        "axiom.lsp.inlayHints.inferredTypes",
        "axiom.lsp.inlayHints.parameterNames",
        "axiom.lsp.inlayHints.ownershipFlow",
        "axiom.lsp.inlayHints.asyncSuspension",
    }
    if not required_props.issubset(props):
        raise RuntimeError(f"package.json missing configuration properties: {required_props - props}")

    lang_cfg = json.loads(lang_cfg_path.read_text(encoding="utf-8"))
    if lang_cfg.get("comments", {}).get("lineComment") != "//":
        raise RuntimeError("language-configuration.json must configure '//' lineComment")

    tm = json.loads(tm_path.read_text(encoding="utf-8"))
    if tm.get("scopeName") != "source.axiom":
        raise RuntimeError("axiom.tmLanguage.json must declare scopeName 'source.axiom'")

    js_src = js_path.read_text(encoding="utf-8")
    for token in (
        '"lsp"',
        '"--stdio"',
        "--position-encoding=",
        "--inlay-types=",
        "--inlay-params=",
        "--inlay-ownership=",
        "--inlay-async=",
        "LanguageClient",
        "buildServerArgs",
    ):
        if token not in js_src:
            raise RuntimeError(f"extension.js missing required thin-client token: {token}")


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: e19_1_lsp_server_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir_str = os.path.abspath(sys.argv[3])
    root = os.path.abspath(sys.argv[4])
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir))
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    # 1. Validate thin VS Code extension (`tools/vscode-axiom/`) (`AXS-LSP-052`)
    verify_vscode_extension(root)

    # 2. Bundle and execute live E19.1 compiler + editor probe (`--interp` and single `-O0` build)
    probe_template = resolve_suite_file(root, "e19_1_lsp_server_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "e19_1_lsp_server_probe_bundle.ax"
    probe_bundle.write_text(
        assemble_e19_1_probe(root, probe_template), encoding="utf-8", newline="\n"
    )

    iproc = run_cmd([axiomc, "run", "--interp", str(probe_bundle)], root, timeout=180)
    if iproc.returncode != 0:
        sys.stderr.write(
            f"e19_1_lsp_server_probe --interp failed ({iproc.returncode}):\n{iproc.stdout}\n{iproc.stderr}\n"
        )
        return 1
    norm_interp = iproc.stdout.replace("\r\n", "\n")
    if norm_interp != EXPECTED_PROBE_STDOUT:
        sys.stderr.write(
            f"stdout mismatch for e19_1_lsp_server_probe under --interp:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_interp}\n"
        )
        return 1

    # Compile the compiler bundle AT MOST ONCE at `-O0` so the test completes in <120s
    probe_exe = tmp_dir / f"e19_1_lsp_server_probe_O0{exe_ext}"
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
            f"build e19_1_lsp_server_probe -O0 failed:\n{bproc.stdout}\n{bproc.stderr}\n"
        )
        return 1

    rproc = run_cmd([str(probe_exe)], root, timeout=120)
    if rproc.returncode != 0:
        sys.stderr.write(
            f"e19_1_lsp_server_probe -O0 failed ({rproc.returncode}):\n{rproc.stderr}\nstdout:\n{rproc.stdout}\n"
        )
        return 1
    norm_native = rproc.stdout.replace("\r\n", "\n")
    if norm_native != EXPECTED_PROBE_STDOUT:
        sys.stderr.write(
            f"stdout mismatch for e19_1_lsp_server_probe under -O0:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_native}\n"
        )
        return 1

    # 3. Differential verification of standalone `.ax` conformance fixtures (`--interp` vs `-O1 --verify-each`)
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

    sys.stdout.buffer.write(b"E19-1-LSP-SERVER-CONFORMANCE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
