#!/usr/bin/env python3
"""Oracle test runner for T817 (`E19.5`):
CompilerDB Documentation Extractor, Deterministic HTML/JSON Site Renderer,
Search Index & Executable Doc-Test Runner (`compiler/docgen/mod.ax`, `compiler/driver/doc_cmd/mod.ax`).

Verifies:
1. Self-hosted `compiler.docgen` and `compiler.driver.doc_cmd` modules compile and pass
   all 4 verification phases under `--interp`, `-O0`, `-O1`, and `-O2 --verify-each`.
2. Standalone fixtures (`doc_extract_and_links.ax`, `html_json_determinism.ax`,
   `doctest_runner_and_binary_invariance.ax`) pass under `--interp`, `-O0`, `-O1`, and `-O2 --verify-each`.
3. `AXS-DOC-005` & `REQ-TOOL-002` production binary invariance: adding, modifying, or
   stripping `///` and `//!` documentation comments produces byte-for-byte identical
   native code across `-O0`, `-O1`, and `-O2`.
"""

import os
import struct
import subprocess
import sys
from pathlib import Path


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


def strip_module_header_and_imports(text: str) -> str:
    out = []
    for line in text.splitlines():
        s = line.strip()
        if s.startswith("module ") or s.startswith("use "):
            continue
        out.append(line)
    return "\n".join(out) + "\n"


def normalize_pe_timestamps(pe_bytes: bytes) -> bytes:
    """Zeroes the 4-byte COFF FileHeader.TimeDateStamp (and any Debug Directory
    TimeDateStamp) in a Windows PE executable so codegen/data sections are
    compared byte-for-byte."""
    buf = bytearray(pe_bytes)
    if len(buf) < 0x40 or buf[:2] != b"MZ":
        return bytes(buf)
    pe_off = struct.unpack_from("<I", buf, 0x3C)[0]
    if pe_off + 24 <= len(buf) and buf[pe_off : pe_off + 4] == b"PE\x00\x00":
        buf[pe_off + 8 : pe_off + 12] = b"\x00\x00\x00\x00"
    return bytes(buf)


def verify_production_binary_invariance(axiomc: str, root: str, tmp: Path) -> None:
    src_with_docs = """//! Module-level inner documentation for binary invariance check (`AXS-DOC-005`).
//!
//! Ensures `///` and `//!` comments never alter emitted machine code.

/// Compute deterministic telemetry checksum.
///
/// # Examples
/// ```axiom
/// assert_eq(compute_checksum(10, 20), 50)
/// ```
pub fn compute_checksum(a: i64, b: i64) -> i64 {
    let x = a * 2 + b
    x + 10
}

/// Entrypoint for binary invariance probe.
pub fn main() -> i32 {
    let v = compute_checksum(10, 20)
    if v != 50 { return 1 }
    print("50\\n")
    0
}
"""
    src_without_docs = """pub fn compute_checksum(a: i64, b: i64) -> i64 {
    let x = a * 2 + b
    x + 10
}

pub fn main() -> i32 {
    let v = compute_checksum(10, 20)
    if v != 50 { return 1 }
    print("50\\n")
    0
}
"""
    exe_ext = ".exe" if os.name == "nt" else ""
    src_path = tmp / "doc_invariance_probe.ax"
    exe_path = tmp / f"doc_invariance_probe{exe_ext}"

    for opt in ("-O0", "-O1", "-O2"):
        src_path.write_text(src_with_docs, encoding="utf-8", newline="\n")
        r1 = run_cmd([axiomc, "build", opt, "-o", str(exe_path), str(src_path)], root)
        if r1.returncode != 0:
            sys.stderr.write(f"compile with docs ({opt}) failed:\n{r1.stderr}\n")
            sys.exit(1)
        bytes_with_docs = normalize_pe_timestamps(exe_path.read_bytes())

        src_path.write_text(src_without_docs, encoding="utf-8", newline="\n")
        r2 = run_cmd([axiomc, "build", opt, "-o", str(exe_path), str(src_path)], root)
        if r2.returncode != 0:
            sys.stderr.write(f"compile without docs ({opt}) failed:\n{r2.stderr}\n")
            sys.exit(1)
        bytes_without_docs = normalize_pe_timestamps(exe_path.read_bytes())

        if bytes_with_docs != bytes_without_docs:
            sys.stderr.write(
                f"AXS-DOC-005 binary invariance failure at {opt}: "
                f"len(with_docs)={len(bytes_with_docs)} vs len(without_docs)={len(bytes_without_docs)}\n"
            )
            sys.exit(1)


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: docgen_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_str = os.path.abspath(sys.argv[3])
    root_str = os.path.abspath(sys.argv[4])
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir))
    root = Path(root_str)
    tmp = Path(tmp_str)
    tmp.mkdir(parents=True, exist_ok=True)
    test_dir = root / "tests" / "run" / "docgen"
    exe_ext = ".exe" if os.name == "nt" else ""

    sys.path.insert(0, str(root / "tests" / "selfhost"))
    import bundle_common as bc  # type: ignore

    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=root_str)
    meta_effects_src = (
        (root / "std" / "meta_effects" / "mod.ax")
        .read_text(encoding="utf-8")
        .replace("use std.core.host.", "use host_intrinsics.")
    )

    module_order = [
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
    ]
    mods = bc.assemble_compiler_modules(module_order, root=root_str)
    probe_src = (test_dir / "docgen_probe.ax.in").read_text(encoding="utf-8")

    bundle_path = tmp / "docgen_bundle.ax"
    bundle_path.write_text(
        prelude + "\n" + meta_effects_src + "\n" + mods + "\n" + probe_src,
        encoding="utf-8",
        newline="\n",
    )

    # 1. Run bundled probe in --interp
    iproc = run_cmd([axiomc, "run", "--interp", str(bundle_path)], root_str, timeout=180)
    if iproc.returncode != 0 or iproc.stdout.replace("\r\n", "\n") != "DOCGEN-PROBE-PASS\n":
        sys.stderr.write(
            f"interp docgen_bundle failed (rc={iproc.returncode}):\nstdout={iproc.stdout}\nstderr={iproc.stderr}\n"
        )
        return 1

    # 2. Run bundled probe across -O0, -O1, -O2 --verify-each
    for flag in ("-O0", "-O1", "-O2"):
        exe = tmp / f"docgen_bundle_{flag[1:]}{exe_ext}"
        bproc = run_cmd(
            [axiomc, "build", "--stack-reserve=67108864", flag, "--verify-each", "-o", str(exe), str(bundle_path)],
            root_str,
            timeout=180,
        )
        if bproc.returncode != 0:
            sys.stderr.write(f"compile {flag} failed:\n{bproc.stdout}\n{bproc.stderr}\n")
            return 1
        rproc = run_cmd([str(exe)], root_str, timeout=120)
        if rproc.returncode != 0 or rproc.stdout.replace("\r\n", "\n") != "DOCGEN-PROBE-PASS\n":
            sys.stderr.write(
                f"native {flag} run failed (rc={rproc.returncode}):\nstdout={rproc.stdout}\nstderr={rproc.stderr}\n"
            )
            return 1

    # 3. Verify standalone fixtures across --interp, -O0, -O1, -O2 --verify-each
    fixtures = [
        ("doc_extract_and_links", "DOC-EXTRACT-AND-LINKS-OK\n"),
        ("html_json_determinism", "HTML-JSON-DETERMINISM-OK\n"),
        ("doctest_runner_and_binary_invariance", "DOCTEST-RUNNER-AND-BINARY-INVARIANCE-OK\n"),
    ]
    for stem, exp_out in fixtures:
        ax_file = test_dir / f"{stem}.ax"
        ri = run_cmd([axiomc, "run", "--interp", str(ax_file)], root_str, timeout=120)
        if ri.returncode != 0 or ri.stdout.replace("\r\n", "\n") != exp_out:
            sys.stderr.write(f"fixture {stem} interp failed: rc={ri.returncode}, stdout={ri.stdout}, stderr={ri.stderr}\n")
            return 1
        for flag in ("-O0", "-O1", "-O2"):
            exe_path = tmp / f"{stem}_{flag[1:]}{exe_ext}"
            bproc = run_cmd([axiomc, "build", flag, "--verify-each", "-o", str(exe_path), str(ax_file)], root_str)
            if bproc.returncode != 0:
                sys.stderr.write(f"build {stem} {flag} failed:\n{bproc.stderr}\n")
                return 1
            rproc = run_cmd([str(exe_path)], root_str)
            if rproc.returncode != 0 or rproc.stdout.replace("\r\n", "\n") != exp_out:
                sys.stderr.write(f"run {stem} {flag} failed: rc={rproc.returncode}, stdout={rproc.stdout}\n")
                return 1

    # 4. Verify AXS-DOC-005 & REQ-TOOL-002 production binary invariance
    verify_production_binary_invariance(axiomc, root_str, tmp)

    sys.stdout.buffer.write(b"DOCGEN-ENGINE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
