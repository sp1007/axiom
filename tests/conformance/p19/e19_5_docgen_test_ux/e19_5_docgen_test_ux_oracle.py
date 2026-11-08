#!/usr/bin/env python3
"""End-to-end E19.5 Conformance Oracle (`T819` / `SPEC-104` `AXS-DOC-001..053`,
`AXS-TST-001..053`; `INV-DOC-001..002`, `INV-TST-001..002`; `REQ-TOOL-002`,
`REQ-TOOL-003`, `REQ-TOOL-005..011`, `REQ-TOOL-179`, `REQ-TOOL-187`,
`REQ-TOOL-298`, `REQ-TST-112`):
CompilerDB Documentation Extractor, Deterministic HTML/JSON Site Renderer,
Search Index, Executable Doc-Tests, Non-Semantic Doc-Comment Binary Invariance,
First-Class `test "name" { ... }` Runner, `axiomc test --diff` MIR Interpreter
Differential Oracle, `compiler.opt.bisect` Pass Replay & Binary Bisection,
Target-Independent DWARF v5 / CodeView Debug Info, and Zero-Overhead `std.trace`.

Steps:
1. Bundles the live `std/meta_effects/mod.ax`, `compiler/docgen/mod.ax`,
   `compiler/driver/doc_cmd/mod.ax`, `compiler/opt/bisect/mod.ax`,
   `compiler/test_runner/mod.ax`, and `compiler/driver/test_cmd/mod.ax` modules
   with `e19_5_docgen_test_ux_probe.ax.in`, executes the bundle in `--interp`,
   and compiles + executes it AT MOST ONCE at `-O0` (per <120s resource rule),
   verifying byte-for-byte identical output.
2. Verifies `AXS-DOC-005` / `INV-DOC-002` production binary invariance: adding,
   modifying, or stripping `///` and `//!` documentation comments produces
   byte-for-byte identical native PE executables (after normalizing COFF
   `TimeDateStamp`).
3. Runs differential verification (`--interp` vs native `-O1 --verify-each`) across
   all 4 standalone `.ax` conformance fixtures in `tests/conformance/p19/e19_5_docgen_test_ux/`
   and inspects the linked production `.exe` images to certify zero leaked
   `.axmeta`, `.axmi`, `.axlto`, `.axmir`, `.axdb`, `.axoracle`, or `__ax_interp_eval`
   sections or magic bytes.
"""

from __future__ import annotations

import os
import pathlib
import struct
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "tests" / "selfhost"))

import bundle_common as bc  # noqa: E402

PROBE_TEMPLATE = HERE / "e19_5_docgen_test_ux_probe.ax.in"

EXPECTED_PROBE_STDOUT = (
    "probe[docgen_html_json_links] zero_codegen=true extract_ok=true links_ok=true neg_link_rej=true html_det_ok=true json_det_ok=true\n"
    "probe[doctest_and_invariance] non_sem_inv=true feat_inv=true harness_ok=true span_remap_ok=true doctests_passed=4 doctests_ignored=1 neg_cf_failed=1 doc_cli_ok=true\n"
    "probe[test_diff_and_bisect] isolation_ok=true parallel_det_ok=true diff_ok=true handoff_bisect=true culprit_step=6 evals=4 replay_ok=true ice_verify_ok=true\n"
    "probe[debug_trace_and_cli] target_indep=true o0_line_ok=true tiered_dwarf_ok=true inline_frames=3 opt_out_honest=true trace_zero_cost=true test_cli_ok=true\n"
    "E19-5-DOCGEN-TEST-UX-CONFORMANCE-PROBE-PASS\n"
)

CONFORMANCE_FIXTURES = [
    (
        "docgen_html_json_and_intra_links",
        "docgen_html_json_and_intra_links.ax",
        "docgen_html_json_and_intra_links.stdout",
    ),
    (
        "doctest_execution_and_binary_invariance",
        "doctest_execution_and_binary_invariance.ax",
        "doctest_execution_and_binary_invariance.stdout",
    ),
    (
        "test_runner_mir_differential_and_bisect",
        "test_runner_mir_differential_and_bisect.ax",
        "test_runner_mir_differential_and_bisect.stdout",
    ),
    (
        "debug_trace_zero_overhead_and_diagnostics",
        "debug_trace_zero_overhead_and_diagnostics.ax",
        "debug_trace_zero_overhead_and_diagnostics.stdout",
    ),
]

E19_5_BUNDLE_MODULES = [
    ("compiler.kernel.arena", "compiler"),
    ("compiler.kernel.hash", "compiler"),
    ("compiler.kernel.id", "compiler"),
    ("compiler.kernel.interner", "compiler"),
    ("compiler.source.span", "compiler"),
    ("compiler.source.manager", "compiler"),
    ("compiler.diag.code", "compiler"),
    ("compiler.diag.emitter", "compiler"),
    ("compiler.diag.format", "compiler"),
    ("compiler.diag.json", "compiler"),
    ("compiler.query.db", "compiler"),
    ("compiler.diag.ux2", "compiler"),
    ("compiler.docgen", "compiler"),
    ("compiler.driver.doc_cmd", "compiler"),
    ("compiler.opt.bisect", "compiler"),
    ("compiler.test_runner", "compiler"),
    ("compiler.driver.test_cmd", "compiler"),
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


def assemble_e19_5_probe(root: str, template_path: pathlib.Path) -> str:
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=root)
    meta_effects_path = pathlib.Path(root) / "std" / "meta_effects" / "mod.ax"
    if not meta_effects_path.is_file():
        meta_effects_path = REPO_ROOT / "std" / "meta_effects" / "mod.ax"
    meta_effects_src = meta_effects_path.read_text(encoding="utf-8").replace(
        "use std.core.host.", "use host_intrinsics."
    )
    modules_src = bc.assemble_compiler_modules(E19_5_BUNDLE_MODULES, root=root)
    main_src = template_path.read_text(encoding="utf-8")
    return prelude + "\n" + meta_effects_src + "\n" + modules_src + "\n" + main_src


def resolve_suite_file(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "conformance" / "p19" / "e19_5_docgen_test_ux" / filename
    if cand.is_file():
        return cand
    return HERE / filename


def normalize_pe_timestamps(pe_bytes: bytes) -> bytes:
    """Zeroes the 4-byte COFF FileHeader.TimeDateStamp in a Windows PE executable
    so codegen/data sections can be compared byte-for-byte."""
    buf = bytearray(pe_bytes)
    if len(buf) < 0x40 or buf[:2] != b"MZ":
        return bytes(buf)
    pe_off = struct.unpack_from("<I", buf, 0x3C)[0]
    if pe_off + 24 <= len(buf) and buf[pe_off : pe_off + 4] == b"PE\x00\x00":
        buf[pe_off + 8 : pe_off + 12] = b"\x00\x00\x00\x00"
    return bytes(buf)


def verify_production_exe_clean(exe_path: pathlib.Path) -> bool:
    raw = exe_path.read_bytes()
    for forbidden in (
        b"AXMETA01",
        b"AXMI0001",
        b"AXLTO001",
        b"AXMIR001",
        b"AXDB0001",
        b".axmeta",
        b".axdb",
        b".axmir",
        b".axoracle",
        b"__ax_interp_eval",
    ):
        if forbidden in raw:
            sys.stderr.write(f"Production binary {exe_path} leaked token {forbidden!r}\n")
            return False
    return True


def verify_doc_comment_binary_invariance(axiomc: str, root: str, tmp_dir: pathlib.Path) -> bool:
    src_with_docs = """//! Module-level inner documentation for E19.5 binary invariance (`AXS-DOC-005`, `INV-DOC-002`).
//!
//! Certifies that `///` and `//!` comments never alter emitted native machine code.

/// Compute deterministic rolling window checksum.
///
/// # Examples
/// ```axiom
/// assert_eq(compute_window_checksum(12, 18), 52)
/// ```
pub fn compute_window_checksum(a: i64, b: i64) -> i64 {
    let x = a * 2 + b
    x + 10
}

/// Entrypoint for binary invariance verification.
pub fn main() -> i32 {
    let v = compute_window_checksum(12, 18)
    if v != 52 { return 1 }
    print("52\\n")
    0
}
"""
    src_without_docs = """pub fn compute_window_checksum(a: i64, b: i64) -> i64 {
    let x = a * 2 + b
    x + 10
}

pub fn main() -> i32 {
    let v = compute_window_checksum(12, 18)
    if v != 52 { return 1 }
    print("52\\n")
    0
}
"""
    exe_ext = ".exe" if os.name == "nt" else ""
    src_path = tmp_dir / "e19_5_doc_invariance.ax"
    exe_path = tmp_dir / f"e19_5_doc_invariance{exe_ext}"

    src_path.write_text(src_with_docs, encoding="utf-8", newline="\n")
    r1 = run_cmd([axiomc, "build", "-O1", "-o", str(exe_path), str(src_path)], root, timeout=120)
    if r1.returncode != 0:
        sys.stderr.write(f"compile with docs (-O1) failed:\n{r1.stderr}\n")
        return False
    bytes_with_docs = normalize_pe_timestamps(exe_path.read_bytes())

    src_path.write_text(src_without_docs, encoding="utf-8", newline="\n")
    r2 = run_cmd([axiomc, "build", "-O1", "-o", str(exe_path), str(src_path)], root, timeout=120)
    if r2.returncode != 0:
        sys.stderr.write(f"compile without docs (-O1) failed:\n{r2.stderr}\n")
        return False
    bytes_without_docs = normalize_pe_timestamps(exe_path.read_bytes())

    if bytes_with_docs != bytes_without_docs:
        sys.stderr.write("AXS-DOC-005 / INV-DOC-002 violation: doc comments altered native binary\n")
        return False
    return verify_production_exe_clean(exe_path)


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: e19_5_docgen_test_ux_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir_str = os.path.abspath(sys.argv[3])
    root = os.path.abspath(sys.argv[4])
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir))
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    # 1. Bundle and execute live E19.5 docgen + test_runner + bisect probe (`--interp` and single `-O0` build)
    probe_template = resolve_suite_file(root, "e19_5_docgen_test_ux_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "e19_5_docgen_test_ux_probe_bundle.ax"
    probe_bundle.write_text(
        assemble_e19_5_probe(root, probe_template), encoding="utf-8", newline="\n"
    )

    iproc = run_cmd([axiomc, "run", "--interp", str(probe_bundle)], root, timeout=180)
    if iproc.returncode != 0:
        sys.stderr.write(
            f"e19_5_docgen_test_ux_probe --interp failed ({iproc.returncode}):\n{iproc.stdout}\n{iproc.stderr}\n"
        )
        return 1
    norm_interp = iproc.stdout.replace("\r\n", "\n")
    if norm_interp != EXPECTED_PROBE_STDOUT:
        sys.stderr.write(
            f"stdout mismatch for e19_5_docgen_test_ux_probe under --interp:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_interp}\n"
        )
        return 1

    # Compile the compiler bundle AT MOST ONCE at `-O0` so the test completes in <120s
    probe_exe = tmp_dir / f"e19_5_docgen_test_ux_probe_O0{exe_ext}"
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
            f"build e19_5_docgen_test_ux_probe -O0 failed:\n{bproc.stdout}\n{bproc.stderr}\n"
        )
        return 1

    rproc = run_cmd([str(probe_exe)], root, timeout=120)
    if rproc.returncode != 0:
        sys.stderr.write(
            f"e19_5_docgen_test_ux_probe -O0 failed ({rproc.returncode}):\n{rproc.stderr}\nstdout:\n{rproc.stdout}\n"
        )
        return 1
    norm_native = rproc.stdout.replace("\r\n", "\n")
    if norm_native != EXPECTED_PROBE_STDOUT:
        sys.stderr.write(
            f"stdout mismatch for e19_5_docgen_test_ux_probe under -O0:\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_native}\n"
        )
        return 1

    # 2. Verify production binary invariance under `///` and `//!` doc comments (`INV-DOC-002`)
    if not verify_doc_comment_binary_invariance(axiomc, root, tmp_dir):
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
        if not verify_production_exe_clean(fx_exe):
            return 1

    sys.stdout.buffer.write(b"E19-5-DOCGEN-TEST-UX-CONFORMANCE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
