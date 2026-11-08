#!/usr/bin/env python3
"""End-to-end oracle for T775 (E18.6): Linker v2 reachability graph, COMDAT
deduplication, unreferenced section GC (`--gc-sections`), forward `.pdata`/`.xdata`
unwind association, and deterministic `inspect --emit=link-map` / `--emit=gc-sections`.
"""

from __future__ import annotations

import hashlib
import os
import pathlib
import struct
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
PROBE_TEMPLATE = HERE / "link_section_gc_probe.ax.in"

MODULES = [
    ("compiler.kernel.arena", "compiler"),
    ("compiler.kernel.id", "compiler"),
    ("compiler.kernel.hash", "compiler"),
    ("compiler.kernel.interner", "compiler"),
    ("compiler.source.span", "compiler"),
    ("compiler.source.manager", "compiler"),
    ("compiler.diag.code", "compiler"),
    ("compiler.diag.emitter", "compiler"),
    ("compiler.diag.format", "compiler"),
    ("compiler.link.gc", "compiler"),
]

POSITIVE_FIXTURES: list[tuple[str, str, int]] = [
    ("comdat_generic_dedup_and_vtable_fold", "comdat_generic_dedup_and_vtable_fold.ax", 0),
    ("section_gc_roots_and_unwind_sweep", "section_gc_roots_and_unwind_sweep.ax", 0),
    ("link_map_and_gc_sections_inspect", "link_map_and_gc_sections_inspect.ax", 0),
    ("comdat_root_propagation_and_lsda_chain", "comdat_root_propagation_and_lsda_chain.ax", 0),
]

EXPECTED_LINES = [
    "PROBE_ARCHIVE_GC_ROOTS_AND_UNWIND=OK",
    "PROBE_COMDAT_GENERIC_VTABLE_AND_WEAK=OK",
    "PROBE_NEGATIVE_DIAGS_AND_MODES=OK",
    "PROBE_LINK_SECTION_GC_ALL=PASS",
]


def get_axiomc(compiler: str, build_dir: str, tmp_dir: str, root: str) -> str:
    base = os.path.basename(compiler).lower()
    if base.startswith("axiomc"):
        return compiler
    for cand in ("axiomc2.exe", "axiomc1.exe", "axiomc.exe", "axiomc2", "axiomc1", "axiomc"):
        p = os.path.join(build_dir, cand)
        if os.path.isfile(p):
            return p
    return compiler


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


def verify_pe32_plus_wx_and_sections(exe_path: pathlib.Path) -> bytes:
    data = exe_path.read_bytes()
    if len(data) < 512 or data[:2] != b"MZ":
        raise RuntimeError(f"invalid DOS header in {exe_path}")
    pe_off = struct.unpack_from("<I", data, 0x3C)[0]
    if pe_off + 24 > len(data) or data[pe_off : pe_off + 4] != b"PE\x00\x00":
        raise RuntimeError(f"invalid PE signature in {exe_path}")
    machine, num_sections = struct.unpack_from("<HH", data, pe_off + 4)
    opt_hdr_sz = struct.unpack_from("<H", data, pe_off + 20)[0]
    if machine != 0x8664 or num_sections == 0:
        raise RuntimeError(f"unexpected PE machine={hex(machine)} sections={num_sections}")

    sec_table_off = pe_off + 24 + opt_hdr_sz
    IMAGE_SCN_MEM_EXECUTE = 0x20000000
    IMAGE_SCN_MEM_WRITE = 0x80000000
    for i in range(num_sections):
        sh_off = sec_table_off + i * 40
        chars = struct.unpack_from("<I", data, sh_off + 36)[0]
        if (chars & IMAGE_SCN_MEM_EXECUTE) != 0 and (chars & IMAGE_SCN_MEM_WRITE) != 0:
            raise RuntimeError(f"W^X violation in PE section {i}: chars=0x{chars:08x}")
    return data


def assemble_link_section_gc_probe(root: str, probe_template_path: pathlib.Path) -> str:
    selfhost_dir = os.path.join(root, "tests", "selfhost")
    if selfhost_dir not in sys.path:
        sys.path.insert(0, selfhost_dir)

    import bundle_common as bc  # noqa: E402

    main_src = probe_template_path.read_text(encoding="utf-8")
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=False, root=root)
    modules_src = bc.assemble_compiler_modules(MODULES, root=root)
    return prelude + "\n" + modules_src + "\n" + main_src


def resolve_fixture_path(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "run" / "link_section_gc" / filename
    if cand.is_file():
        return cand
    return HERE / filename


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: link_section_gc_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir_str = os.path.abspath(sys.argv[3])
    root = os.path.abspath(sys.argv[4])
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir, tmp_dir_str, root))
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    # 1. Assemble and execute live `compiler.link.gc` probe via `--interp`
    probe_template = resolve_fixture_path(root, "link_section_gc_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "link_section_gc_probe_bundle.ax"
    probe_bundle.write_text(assemble_link_section_gc_probe(root, probe_template), encoding="utf-8", newline="\n")

    rproc = run_cmd([axiomc, "run", "--interp", str(probe_bundle)], root, timeout=600)
    if rproc.returncode != 0:
        sys.stderr.write(
            f"link_section_gc_probe --interp failed with exit code {rproc.returncode}:\n"
            f"{rproc.stderr}\nstdout:\n{rproc.stdout}\n"
        )
        return 1
    norm_probe = rproc.stdout.replace("\r\n", "\n")
    for expected in EXPECTED_LINES:
        if expected not in norm_probe:
            sys.stderr.write(f"Missing expected line in link_section_gc_probe output:\n  {expected}\nFull output:\n{norm_probe}\n")
            return 1

    # 2. Differential execution + PE32+ W^X inspection & determinism across --interp, -O0, -O1, -O2 (--verify-each)
    for stem, filename, exp_exit in POSITIVE_FIXTURES:
        src_path = resolve_fixture_path(root, filename)
        iproc = run_cmd([axiomc, "run", "--interp", str(src_path)], root, timeout=120)
        if iproc.returncode != exp_exit:
            sys.stderr.write(f"interp {stem} failed with {iproc.returncode}:\n{iproc.stderr}\n")
            return 1
        norm_interp = iproc.stdout.replace("\r\n", "\n")

        for flag in ("-O0", "-O1", "-O2"):
            exe_path = tmp_dir / f"{stem}_{flag[1:]}{exe_ext}"
            bproc = run_cmd([axiomc, "build", flag, "--verify-each", "-o", str(exe_path), str(src_path)], root)
            if bproc.returncode != 0:
                sys.stderr.write(f"build {stem} {flag} --verify-each failed:\n{bproc.stderr}\n")
                return 1
            bytes_1 = verify_pe32_plus_wx_and_sections(exe_path)

            if flag == "-O2":
                exe_path_2 = tmp_dir / f"{stem}_{flag[1:]}_det{exe_ext}"
                bproc2 = run_cmd([axiomc, "build", flag, "--verify-each", "-o", str(exe_path_2), str(src_path)], root)
                if bproc2.returncode != 0:
                    sys.stderr.write(f"second build {stem} {flag} --verify-each failed:\n{bproc2.stderr}\n")
                    return 1
                bytes_2 = verify_pe32_plus_wx_and_sections(exe_path_2)
                if hashlib.sha256(bytes_1).digest() != hashlib.sha256(bytes_2).digest():
                    sys.stderr.write(f"non-deterministic PE32+ binary output for {stem} under {flag}\n")
                    return 1

            nproc = run_cmd([str(exe_path)], root)
            if nproc.returncode != exp_exit:
                sys.stderr.write(f"run {stem} {flag} failed with {nproc.returncode}:\n{nproc.stderr}\n")
                return 1
            norm_out = nproc.stdout.replace("\r\n", "\n")
            if norm_out != norm_interp:
                sys.stderr.write(f"stdout mismatch for {stem} under {flag}:\nexpected:\n{norm_interp}\ngot:\n{norm_out}\n")
                return 1

    sys.stdout.buffer.write(b"LINK-SECTION-GC-ENGINE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
