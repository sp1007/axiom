#!/usr/bin/env python3
"""Oracle and direct `compiler.artifact.container` probe runner for E18.4 COFF
`.obj` / `.lib` / `.axpkg` non-alloc discardable (`.axmeta`, `.axlto`, `.axmir`)
container sections, schema-versioned fail-closed reader/writer, LTO Verified MIR
summary consumption, and final PE32+ `.exe` / `.dll` section stripping (`T766` /
`SPEC-24` `AXS-ART-002..005`, `AXS-ART-020..024`, `AXS-ART-050..053`, `INV-ART-002`).
"""

from __future__ import annotations

import os
import pathlib
import shutil
import struct
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "tests" / "selfhost"))

import bundle_common as bc  # noqa: E402

PROBE_TEMPLATE = HERE / "artifact_container_probe.ax.in"

POSITIVE_FIXTURES = [
    (
        "container_coff_embed_and_roundtrip",
        "container_coff_embed_and_roundtrip.ax",
        (
            "coff_embed: machine=0x8664 sections=5 axmeta=AXMETA01(fam=4) axlto=AXLTO001(fam=3) axmir=AXMIR001(fam=2) chars=0x42000200\n"
            "determinism_and_roundtrip: bytes_equal=true fp_bound=true lto_fns=3 mir_bodies=2 db_query_ok=true axpkg=AXPKG001(fam=6)\n"
            "CONTAINER-COFF-EMBED-ROUNDTRIP-OK\n"
        ),
    ),
    (
        "container_fail_closed_validation",
        "container_fail_closed_validation.ax",
        (
            "validate magic_and_chars: axmeta_magic=AX_ART_CORRUPT_HEADER axlto_magic=AX_ART_CORRUPT_HEADER exec_chars=AX_ART_CORRUPT_HEADER\n"
            "validate schema_and_sec: axmeta_v99=AX_ART_VERSION_MISMATCH axlto_v77=AX_ART_VERSION_MISMATCH mir_v55=AX_ART_VERSION_MISMATCH req_sec=AX_ART_VERSION_MISMATCH opt_sec=OK\n"
            "validate target_and_integrity: triple=AX_ART_TARGET_MISMATCH cpu=AX_ART_TARGET_MISMATCH cksum=AX_ART_CHECKSUM_MISMATCH fp_drift=AX_ART_CHECKSUM_MISMATCH unverified_mir=AX_ART_CORRUPT_HEADER\n"
            "CONTAINER-FAIL-CLOSED-VALIDATION-OK\n"
        ),
    ),
    (
        "container_lto_mir_and_exe_strip",
        "container_lto_mir_and_exe_strip.ax",
        (
            "pe_link exe_and_dll: status=OK runtime_sections=2 stripped_axmeta=2 stripped_axlto=2 stripped_axmir=1 stripped_clean=true\n"
            "lto_verified_mir: fns=5 mir_bodies=3 call_edges=3 dead_internal=1 inline_candidates=4\n"
            "link_guard: injected_axmeta_rejected=true leaked_magic_rejected=true stale_dep_fp=AX_ART_CHECKSUM_MISMATCH\n"
            "CONTAINER-LTO-MIR-EXE-STRIP-OK\n"
        ),
    ),
    (
        "container_archive_foreign_and_bounds_seam",
        "container_archive_foreign_and_bounds_seam.ax",
        (
            "coff_archive: magic=!<arch> members=2 axiom_objs=1 foreign_objs=1 extracted_axmeta=1 extracted_axlto=1\n"
            "bounds_seam: trunc_coff=AX_ART_CORRUPT_HEADER oob_raw_ptr=AX_ART_CORRUPT_HEADER bad_ar_hdr=AX_ART_CORRUPT_HEADER lto_without_meta=AX_ART_CORRUPT_HEADER\n"
            "CONTAINER-ARCHIVE-FOREIGN-BOUNDS-SEAM-OK\n"
        ),
    ),
]

ARTIFACT_CONTAINER_BUNDLE_MODULES = [
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
    ("compiler.artifact.axmi", "compiler"),
    ("compiler.artifact.container", "compiler"),
]


def get_axiomc(compiler: str, build_dir: str, tmp_dir: str, root: str) -> str:
    exe = ".exe" if os.name == "nt" else ""
    for d in (build_dir, os.path.dirname(compiler)):
        for name in (f"axiomc2{exe}", f"axiomc1{exe}", f"axiomc{exe}"):
            cand = os.path.join(d, name)
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


def assemble_artifact_container_probe(root: str, template_path: pathlib.Path) -> str:
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=root)
    main_src = template_path.read_text(encoding="utf-8")
    modules_src = bc.assemble_compiler_modules(ARTIFACT_CONTAINER_BUNDLE_MODULES, root=root)
    modules_src = modules_src.replace("diag_buf_push_conc_name(b,", "diag_buf_push_conc_name(mut_view(*b),")
    modules_src = modules_src.replace("qry_buf_push_table_slice(out,", "qry_buf_push_table_slice(mut_view(*out),")
    modules_src = modules_src.replace("axmi_push_ascii_slice(out,", "axmi_push_ascii_slice(mut_view(*out),")
    return prelude + "\n" + modules_src + "\n" + main_src


def resolve_fixture_path(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "run" / "artifact_container" / filename
    if cand.is_file():
        return cand
    return HERE / filename


def validate_probe_output(stdout: str) -> tuple[bool, str]:
    lines = [ln for ln in stdout.replace("\r\n", "\n").split("\n") if ln]
    if not lines or lines[-1] != "ARTIFACT-CONTAINER-PROBE-PASS":
        return False, f"missing ARTIFACT-CONTAINER-PROBE-PASS trailer in:\n{stdout}"

    required_exact_lines = [
        "=== CASE 1: COFF EMBED, DETERMINISM, ROUNDTRIP & AXPKG ===",
        "=== CASE 2: FAIL-CLOSED CONTAINER VALIDATION & DIAGNOSTICS ===",
        "=== CASE 3: LTO VERIFIED MIR, DEP CHECK & PE EXE/DLL STRIP ===",
        "=== CASE 4: COFF ARCHIVE, FOREIGN C & BOUNDS SEAM ===",
        "determinism_obj_bytes_equal=true len=3548",
        "container_obj sections=5 runtime=2 container=3 foreign=false has_axmeta=true has_axlto=true has_axmir=true chars_meta=1107296768 chars_lto=1107296768",
        "lto_edge caller=12 callee=core_math::core_math.vec.dot_vec2 sites=2 hotness=90 direct=true can_inline=true",
        "axmeta_extracted_db_query_ok=true",
        "diag[AX_ART_CORRUPT_HEADER/AX_LINK_BAD_ARTIFACT] artifact=corrupt_axmeta_magic detail=0",
        "diag[AX_ART_CORRUPT_HEADER/AX_LINK_BAD_ARTIFACT] artifact=corrupt_axlto_magic detail=0",
        "diag[AX_ART_VERSION_MISMATCH/AX_LINK_ARTIFACT_SCHEMA_MISMATCH] artifact=version_mismatch_axmeta detail=99",
        "diag[AX_ART_VERSION_MISMATCH/AX_LINK_ARTIFACT_SCHEMA_MISMATCH] artifact=version_mismatch_axlto detail=77",
        "diag[AX_ART_TARGET_MISMATCH/AX_LINK_ARTIFACT_TARGET_MISMATCH] artifact=target_mismatch_triple detail=1",
        "diag[AX_ART_TARGET_MISMATCH/AX_LINK_ARTIFACT_TARGET_MISMATCH] artifact=target_mismatch_cpu_feat detail=1",
        "diag[AX_ART_CHECKSUM_MISMATCH/AX_LINK_BAD_ARTIFACT] artifact=checksum_mismatch_axmeta detail=0",
        "diag[AX_ART_CHECKSUM_MISMATCH/AX_LINK_BAD_ARTIFACT] artifact=checksum_mismatch_axlto detail=0",
        "diag[AX_ART_VERSION_MISMATCH/AX_LINK_ARTIFACT_SCHEMA_MISMATCH] artifact=unknown_mandatory_sec_axlto detail=1",
        "unknown_optional_sec_axlto_ok=true",
        "diag[AX_ART_CORRUPT_HEADER/AX_LINK_BAD_ARTIFACT] artifact=bad_coff_container_chars detail=1",
        "diag[AX_ART_CHECKSUM_MISMATCH/AX_LINK_BAD_ARTIFACT] artifact=cross_section_fp_drift detail=10",
        "diag[AX_ART_CORRUPT_HEADER/AX_LINK_BAD_ARTIFACT] artifact=unverified_mir_body_axlto detail=8",
        "diag[AX_ART_VERSION_MISMATCH/AX_LINK_ARTIFACT_SCHEMA_MISMATCH] artifact=mir_schema_mismatch_axlto detail=55",
        "pe_injected_axmeta_detected=true",
        "pe_leaked_magic_detected=true",
        "diag[AX_ART_TARGET_MISMATCH/AX_LINK_ARTIFACT_TARGET_MISMATCH] artifact=cross_mod_dep_abi_drift detail=11",
        "container_obj sections=2 runtime=2 container=0 foreign=true has_axmeta=false has_axlto=false has_axmir=false chars_meta=0 chars_lto=0",
        "diag[AX_ART_CORRUPT_HEADER/AX_LINK_BAD_ARTIFACT] artifact=trunc_coff_header detail=0",
        "diag[AX_ART_CORRUPT_HEADER/AX_LINK_BAD_ARTIFACT] artifact=oob_coff_section_raw_ptr detail=1",
        "diag[AX_ART_CORRUPT_HEADER/AX_LINK_BAD_ARTIFACT] artifact=corrupt_archive_header detail=0",
        "diag[AX_ART_CORRUPT_HEADER/AX_LINK_BAD_ARTIFACT] artifact=lto_without_axmeta_obj detail=10",
    ]
    for req in required_exact_lines:
        if req not in lines:
            return False, f"missing expected line in probe output:\n{req}\nin:\n{stdout}"

    required_prefixes = [
        "axmeta_header magic=AXMETA01 version=1 sections=8 interface_fp=",
        "axlto_header magic=AXLTO001 version=1 sections=3 fns=3 edges=1 mir_bodies=2 interface_fp=",
        "lto_fn core_math::core_math.vec.dot_vec2 linkage=pub root=exported insts=6 weight=12 inline=true effects=0 escape=3 alias=3 spec_key=0000000000001001 digest=",
        "lto_fn core_math::core_math.vec.helper_priv linkage=internal root=none insts=4 weight=5 inline=false effects=0 escape=1 alias=1 spec_key=0000000000001003 digest=",
        "lto_fn core_math::core_math.vec.scale_vec2<T> linkage=pub root=exported insts=9 weight=18 inline=true effects=1 escape=1 alias=1 spec_key=0000000000001002 digest=",
        "lto_mir core_math::core_math.vec.dot_vec2 schema=1 blocks=2 locals=4 insts=6 opcodes=4 verified=true digest=",
        "lto_mir core_math::core_math.vec.scale_vec2<T> schema=1 blocks=3 locals=5 insts=9 opcodes=5 verified=true digest=",
        "axpkg_header magic=AXPKG001 version=1 sections=4 obj_size=3548 interface_fp=",
        "pe_link kind=exe objs=2 axiom_objs=2 foreign_objs=0 stripped_secs=5 stripped_bytes=4780 runtime=2 text_bytes=224 rdata_bytes=80 fns=5 inlined=6 dead_stripped=2 mir_bodies=3 pe_clean=true interface_fp=",
        "pe_link kind=dll objs=2 axiom_objs=2 foreign_objs=0 stripped_secs=5 stripped_bytes=4780 runtime=2 text_bytes=224 rdata_bytes=80 fns=5 inlined=6 dead_stripped=2 mir_bodies=3 pe_clean=true interface_fp=",
        "archive members=2 axiom_objs=1 foreign_objs=1 has_axmeta=1 has_axlto=1 runtime=4 interface_fp=",
        "pe_link kind=exe objs=2 axiom_objs=1 foreign_objs=1 stripped_secs=2 stripped_bytes=2252 runtime=2 text_bytes=128 rdata_bytes=40 fns=3 inlined=2 dead_stripped=1 mir_bodies=2 pe_clean=true interface_fp=",
    ]
    for pref in required_prefixes:
        if not any(ln.startswith(pref) for ln in lines):
            return False, f"missing expected prefix in probe output:\n{pref}\nin:\n{stdout}"

    return True, ""


def inspect_pe_for_leaked_container_sections(pe_bytes: bytes) -> tuple[bool, str]:
    """Parses the PE32+ section table of `pe_bytes` and verifies that no
    `.axmeta`, `.axlto`, `.axmir`, or `.axdbg` sections remain in the final executable.
    """
    if len(pe_bytes) < 0x100 or pe_bytes[:2] != b"MZ":
        return False, "invalid MZ header on PE executable"
    pe_off = struct.unpack_from("<I", pe_bytes, 0x3C)[0]
    if pe_off + 24 > len(pe_bytes) or pe_bytes[pe_off : pe_off + 4] != b"PE\x00\x00":
        return False, "invalid PE signature on executable"
    num_secs = struct.unpack_from("<H", pe_bytes, pe_off + 6)[0]
    opt_hdr_sz = struct.unpack_from("<H", pe_bytes, pe_off + 20)[0]
    sec_tbl_off = pe_off + 24 + opt_hdr_sz
    forbidden = {b".axmeta", b".axlto", b".axmir", b".axdbg"}
    for i in range(num_secs):
        sh_off = sec_tbl_off + i * 40
        if sh_off + 40 > len(pe_bytes):
            return False, "truncated PE section table"
        raw_name = pe_bytes[sh_off : sh_off + 8].rstrip(b"\x00")
        if raw_name in forbidden:
            return False, f"non-runtime container section {raw_name!r} leaked into final PE image"
    return True, ""


def run_coff_container_strip_and_link_test(axiomc: str, tmp_dir: pathlib.Path, root: str) -> tuple[bool, str]:
    """Compiles upstream `vecmath_lto.ax` to `vecmath_lto.obj`, verifies its COFF
    header, deletes `vecmath_lto.ax`, links downstream `app_container.ax` with
    `vecmath_lto.obj` to `app_container.exe`, runs `app_container.exe`, and verifies
    that final PE32+ linking leaves zero `.axmeta`/`.axlto`/`.axmir` sections in
    `app_container.exe`.
    """
    vecmath_ax = tmp_dir / "vecmath_lto.ax"
    vecmath_obj = tmp_dir / "vecmath_lto.obj"
    app_ax = tmp_dir / "app_container.ax"
    exe_ext = ".exe" if os.name == "nt" else ""
    app_exe = tmp_dir / f"app_container{exe_ext}"

    mini_std = tmp_dir / "mini_std"
    if mini_std.exists():
        shutil.rmtree(mini_std)
    shutil.copytree(pathlib.Path(root) / "std", mini_std)
    (mini_std / "core" / "prelude.ax").write_text(
        "module std.core.prelude\npub use std.core.option.Option;\npub use std.core.result.Result;\n",
        encoding="utf-8",
        newline="\n",
    )

    vecmath_ax.write_text(
        """\
module vecmath_lto

fn internal_dead_helper(x: i64) -> i64 {
    x * 99
}

@export
pub fn vecmath_dot2(ax: i64, ay: i64, bx: i64, by: i64) -> i64 {
    (ax * bx) + (ay * by)
}
""",
        encoding="utf-8",
        newline="\n",
    )

    b_obj = run_cmd([axiomc, "build", "--std-root", str(mini_std), "--kind", "obj", "-o", str(vecmath_obj), str(vecmath_ax)], root)
    if b_obj.returncode != 0 or not vecmath_obj.is_file():
        return False, f"building vecmath_lto.obj failed:\n{b_obj.stdout}\n{b_obj.stderr}"

    obj_bytes = vecmath_obj.read_bytes()
    if len(obj_bytes) < 20 or struct.unpack_from("<H", obj_bytes, 0)[0] != 0x8664:
        return False, "vecmath_lto.obj is not an AMD64 COFF object"

    os.remove(vecmath_ax)
    if vecmath_ax.exists():
        return False, "vecmath_lto.ax still exists after deletion"

    app_ax.write_text(
        """\
extern "C" {
    fn vecmath_dot2(ax: i64, ay: i64, bx: i64, by: i64) -> i64;
}

pub fn main() -> i32 {
    let d = unsafe { vecmath_dot2(3i64, 4i64, 5i64, 6i64) };
    if d != 39i64 {
        return 1;
    }
    print("COFF-CONTAINER-LINK-AND-STRIP-OK\\n");
    0
}
""",
        encoding="utf-8",
        newline="\n",
    )

    b_app = run_cmd([axiomc, "build", "--std-root", str(mini_std), "-O1", "--verify-each", "-o", str(app_exe), str(app_ax), str(vecmath_obj)], root)
    if b_app.returncode != 0 or not app_exe.is_file():
        return False, f"linking app_container.exe failed:\n{b_app.stdout}\n{b_app.stderr}"

    ok_pe, pe_err = inspect_pe_for_leaked_container_sections(app_exe.read_bytes())
    if not ok_pe:
        return False, pe_err

    r_app = run_cmd([str(app_exe)], root)
    if r_app.returncode != 0 or r_app.stdout.replace("\r\n", "\n") != "COFF-CONTAINER-LINK-AND-STRIP-OK\n":
        return False, f"running app_container.exe failed ({r_app.returncode}):\n{r_app.stdout}\n{r_app.stderr}"

    return True, ""


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: artifact_container_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir_str = os.path.abspath(sys.argv[3])
    root = os.path.abspath(sys.argv[4])
    if os.path.isdir(os.path.join(build_dir, "compiler")):
        root = build_dir
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir, tmp_dir_str, root))
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    # 1. Assemble and execute direct compiler.artifact.container probe under --interp, -O0, -O1, -O2 --verify-each
    probe_template = resolve_fixture_path(root, "artifact_container_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "artifact_container_probe_bundle.ax"
    probe_bundle.write_text(assemble_artifact_container_probe(root, probe_template), encoding="utf-8", newline="\n")

    iproc = run_cmd([axiomc, "run", "--interp", str(probe_bundle)], root, timeout=180)
    if iproc.returncode != 0:
        sys.stderr.write(f"artifact_container_probe --interp failed ({iproc.returncode}):\n{iproc.stdout}\n{iproc.stderr}\n")
        return 1
    norm_interp_probe = iproc.stdout.replace("\r\n", "\n")
    ok_probe, reason = validate_probe_output(norm_interp_probe)
    if not ok_probe:
        sys.stderr.write(f"artifact_container_probe validation failed under --interp:\n{reason}\n")
        return 1

    for flag in ("-O0", "-O1", "-O2"):
        probe_exe = tmp_dir / f"artifact_container_probe_{flag[1:]}{exe_ext}"
        bproc = run_cmd(
            [axiomc, "build", "--stack-reserve=67108864", flag, "--verify-each", "-o", str(probe_exe), str(probe_bundle)],
            root,
            timeout=180,
        )
        if bproc.returncode != 0:
            sys.stderr.write(f"build artifact_container_probe {flag} --verify-each failed:\n{bproc.stdout}\n{bproc.stderr}\n")
            return 1
        rproc = run_cmd([str(probe_exe)], root, timeout=120)
        if rproc.returncode != 0:
            sys.stderr.write(
                f"artifact_container_probe {flag} failed with exit code {rproc.returncode}:\n{rproc.stderr}\nstdout:\n{rproc.stdout}\n"
            )
            return 1
        norm_probe = rproc.stdout.replace("\r\n", "\n")
        if norm_probe != norm_interp_probe:
            sys.stderr.write(
                f"stdout mismatch for artifact_container_probe under {flag} vs --interp:\nexpected:\n{norm_interp_probe}\ngot:\n{norm_probe}\n"
            )
            return 1

    # 2. COFF `.obj` link and PE32+ non-runtime container section stripping verification
    ok_strip, strip_err = run_coff_container_strip_and_link_test(axiomc, tmp_dir, root)
    if not ok_strip:
        sys.stderr.write(f"coff container strip and link test failed:\n{strip_err}\n")
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

    sys.stdout.buffer.write(b"ARTIFACT-CONTAINER-ENGINE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
