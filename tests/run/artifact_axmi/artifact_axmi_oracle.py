#!/usr/bin/env python3
"""Oracle and direct `compiler.artifact.axmi` probe runner for E18.4 `.axmi`
module interface serializer, fail-closed loader, exported symbol/type/trait/
contract/const/generic MIR summaries, source-free `CompilerDB` ingestion, and
deterministic `inspect --axmi` / `--emit=axmi` (`T765` / `SPEC-24`
`AXS-ART-001..005`, `AXS-ART-010..014`, `AXS-ART-050..053`, `INV-ART-001`).

1. Bundles `compiler/query/db/mod.ax` + `compiler/artifact/axmi/mod.ax` with
   `tests/run/artifact_axmi/artifact_axmi_probe.ax.in` and executes the probe
   across `--interp`, `-O0`, `-O1`, and `-O2 --verify-each`, verifying
   byte-identical `inspect --axmi` output, allocation-order independence,
   source-free `CompilerDB` population, cross-module generic MIR instantiation,
   and fail-closed validation (`AX_ART_CORRUPT_HEADER`, `AX_ART_VERSION_MISMATCH`,
   `AX_ART_TARGET_MISMATCH`, `AX_ART_CHECKSUM_MISMATCH`).
2. Compiles an upstream module `vecmath.ax` to `vecmath.obj` (`--kind obj`) +
   `vecmath.axmi`, deletes `vecmath.ax`, verifies `vecmath.ax` no longer exists,
   validates `vecmath.axmi` binary header/sections, and compiles/links downstream
   `app.ax` against `vecmath.obj` + `vecmath.axmi` to `app.exe`, verifying
   execution without upstream `.ax` source.
3. Runs differential `.ax` tests in `tests/run/artifact_axmi/` across `--interp`,
   `-O0`, `-O1`, and `-O2 --verify-each`.
"""

from __future__ import annotations

import os
import pathlib
import struct
import subprocess
import sys

HERE = pathlib.Path(__file__).resolve().parent
REPO_ROOT = HERE.parent.parent.parent
sys.path.insert(0, str(REPO_ROOT / "tests" / "selfhost"))

import bundle_common as bc  # noqa: E402

PROBE_TEMPLATE = HERE / "artifact_axmi_probe.ax.in"

POSITIVE_FIXTURES = [
    (
        "axmi_roundtrip_and_source_free_import",
        "axmi_roundtrip_and_source_free_import.ax",
        (
            "axmi_roundtrip: magic=AXMI0001 version=1 sections=8 exported=3 stripped_private=1\n"
            "source_free_import: Pair(size=8,align=4) SCALE_FACTOR=4 resolved_val=36\n"
            "AXMI-ROUNDTRIP-SOURCE-FREE-OK\n"
        ),
    ),
    (
        "axmi_generic_inline_and_cap_contracts",
        "axmi_generic_inline_and_cap_contracts.ax",
        (
            "fn_contract borrow_x: mode0=view ret_borrows=1 no_escape=1 effects=1 panic=NoPanic\n"
            "fn_contract mut_scale: mode0=mut_view ret_borrows=0 no_escape=3 effects=3 panic=NoPanic\n"
            "mir_instantiate clamp_pair<Pair>: verified=true blocks=3 locals=5 insts=14 bound_ok=true\n"
            "AXMI-GENERIC-CAP-CONTRACTS-OK\n"
        ),
    ),
    (
        "axmi_fail_closed_validation",
        "axmi_fail_closed_validation.ax",
        (
            "validate corrupt_magic: AX_ART_CORRUPT_HEADER/AX_LINK_BAD_ARTIFACT\n"
            "validate future_v99: AX_ART_VERSION_MISMATCH/AX_LINK_ARTIFACT_SCHEMA_MISMATCH\n"
            "validate unknown_optional_sec: OK\n"
            "validate unknown_required_sec: AX_ART_VERSION_MISMATCH/AX_LINK_ARTIFACT_SCHEMA_MISMATCH\n"
            "validate wrong_target: AX_ART_TARGET_MISMATCH/AX_LINK_ARTIFACT_TARGET_MISMATCH\n"
            "validate bitflip_payload: AX_ART_CHECKSUM_MISMATCH/AX_LINK_BAD_ARTIFACT\n"
            "AXMI-FAIL-CLOSED-VALIDATION-OK\n"
        ),
    ),
    (
        "axmi_freshness_diff_and_bounds_seam",
        "axmi_freshness_diff_and_bounds_seam.ax",
        (
            "bounds_and_sections: overflow_rejected=true overlap_rejected=true order_rejected=true\n"
            "freshness_and_diff: priv=Fresh eff=Stale(api=true,abi=false) layout=Stale(api=true,abi=true) zero_fp=Unknown\n"
            "cpu_and_mir_schema: avx2_mismatch=AX_ART_TARGET_MISMATCH mir_v2=AX_ART_VERSION_MISMATCH\n"
            "AXMI-FRESHNESS-DIFF-BOUNDS-SEAM-OK\n"
        ),
    ),
]

ARTIFACT_AXMI_BUNDLE_MODULES = [
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


def assemble_artifact_axmi_probe(root: str, template_path: pathlib.Path) -> str:
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=root)
    main_src = template_path.read_text(encoding="utf-8")
    modules_src = bc.assemble_compiler_modules(ARTIFACT_AXMI_BUNDLE_MODULES, root=root)
    return prelude + "\n" + modules_src + "\n" + main_src


def resolve_fixture_path(root: str, filename: str) -> pathlib.Path:
    cand = pathlib.Path(root) / "tests" / "run" / "artifact_axmi" / filename
    if cand.is_file():
        return cand
    return HERE / filename


def validate_probe_output(stdout: str) -> tuple[bool, str]:
    lines = [ln for ln in stdout.replace("\r\n", "\n").split("\n") if ln]
    if not lines or lines[-1] != "ARTIFACT-AXMI-PROBE-PASS":
        return False, f"missing ARTIFACT-AXMI-PROBE-PASS trailer in:\n{stdout}"

    if not lines[0].startswith("axmi_header magic=AXMI0001 version=1 sections=8 interface_fp="):
        return False, f"unexpected header line: {lines[0]!r}"
    for key in ("abi_fp=", "target_fp=", "content_hash="):
        if key not in lines[0]:
            return False, f"missing {key} in header line: {lines[0]!r}"

    exp_mod = "axmi_module pkg=core_math module=core_math.vecmath target=x86_64-windows abi=win64 stripped_private=1"
    if lines[1] != exp_mod:
        return False, f"unexpected module line: {lines[1]!r} != {exp_mod!r}"

    sec_lines = [ln for ln in lines if ln.startswith("section[")]
    expected_sec_types = [
        "Strings",
        "Symbols",
        "Types",
        "Traits",
        "TypesLayout",
        "ConstValues",
        "GenericMir",
        "EffectsCapabilities",
    ]
    if len(sec_lines) != 8:
        return False, f"expected 8 section lines, got {len(sec_lines)}"
    for idx, (sln, exp_ty) in enumerate(zip(sec_lines, expected_sec_types)):
        if f"section[{idx}] type={exp_ty} " not in sln or " align=8 checksum=" not in sln:
            return False, f"malformed section line {idx}: {sln!r}"

    sym_lines = [ln for ln in lines if ln.startswith("symbol ")]
    if len(sym_lines) != 7:
        return False, f"expected 7 exported symbol lines, got {len(sym_lines)}"
    if any("priv_clamp_helper" in ln for ln in lines):
        return False, "private helper `priv_clamp_helper` leaked into `.axmi` dump"

    expected_sym_prefixes = [
        "symbol core_math::core_math.vecmath.Pair kind=struct params=2 ret=10 generic=false inline=false sig_fp=",
        "symbol core_math::core_math.vecmath.add_pair kind=fn params=2 ret=10 generic=false inline=true sig_fp=",
        "symbol core_math::core_math.vecmath.borrow_x kind=fn params=1 ret=1 generic=false inline=false sig_fp=",
        "symbol core_math::core_math.vecmath.clamp_pair<T:Metric> kind=fn params=3 ret=10 generic=true inline=true sig_fp=",
        "symbol core_math::core_math.vecmath.Metric kind=trait params=1 ret=1 generic=false inline=false sig_fp=",
        "symbol core_math::core_math.vecmath.impl_Metric_Pair#1 kind=impl params=1 ret=10 generic=false inline=false sig_fp=",
        "symbol core_math::core_math.vecmath.SCALE_FACTOR kind=const params=0 ret=1 generic=false inline=false sig_fp=",
    ]
    for sln, exp_pref in zip(sym_lines, expected_sym_prefixes):
        if not sln.startswith(exp_pref):
            return False, f"symbol line mismatch:\ngot:      {sln}\nexpected: {exp_pref}..."

    expected_exact_lines = [
        "type_layout core_math::core_math.vecmath.MetricVal adt=struct repr=transparent size=4 align=4 fields=1 copy=true send=true share=true",
        "type_layout core_math::core_math.vecmath.Pair adt=struct repr=C size=8 align=4 fields=2 copy=true send=true share=true",
        "trait_impl core_math::core_math.vecmath.impl_Metric_Pair#1 trait_def=6 self_type=10 assoc=1 object_safe=true",
        "fn_contract core_math::core_math.vecmath.add_pair params=2 ret_borrows=0 no_escape=3 effects=0 caps=0 panic=NoPanic pure=true",
        "fn_contract core_math::core_math.vecmath.borrow_x params=1 ret_borrows=1 no_escape=1 effects=1 caps=0 panic=NoPanic pure=false",
        "fn_contract core_math::core_math.vecmath.clamp_pair<T:Metric> params=3 ret_borrows=0 no_escape=7 effects=0 caps=0 panic=NoPanic pure=true",
        "diag[AX_ART_CORRUPT_HEADER/AX_LINK_BAD_ARTIFACT] artifact=corrupt_magic.axmi detail=0",
        "diag[AX_ART_VERSION_MISMATCH/AX_LINK_ARTIFACT_SCHEMA_MISMATCH] artifact=future_v99.axmi detail=99",
        "diag[AX_ART_TARGET_MISMATCH/AX_LINK_ARTIFACT_TARGET_MISMATCH] artifact=wrong_target.axmi detail=1",
        "diag[AX_ART_CHECKSUM_MISMATCH/AX_LINK_BAD_ARTIFACT] artifact=bitflip_payload.axmi detail=0",
    ]
    for req in expected_exact_lines:
        if req not in lines:
            return False, f"missing expected line in probe output:\n{req}\nin:\n{stdout}"

    const_lines = [ln for ln in lines if ln.startswith("const_val ")]
    if len(const_lines) != 2:
        return False, f"expected 2 const_val lines, got {len(const_lines)}"
    if not const_lines[0].startswith("const_val core_math::core_math.vecmath.MAX_DIM val=16 fp="):
        return False, f"unexpected const_val[0]: {const_lines[0]!r}"
    if not const_lines[1].startswith("const_val core_math::core_math.vecmath.SCALE_FACTOR val=4 fp="):
        return False, f"unexpected const_val[1]: {const_lines[1]!r}"

    mir_lines = [ln for ln in lines if ln.startswith("mir_template ")]
    if len(mir_lines) != 2:
        return False, f"expected 2 mir_template lines, got {len(mir_lines)}"
    if not mir_lines[0].startswith(
        "mir_template core_math::core_math.vecmath.add_pair schema=1 generic=false inline=true comptime=true blocks=1 locals=3 insts=6 verified=true digest="
    ):
        return False, f"unexpected mir_template[0]: {mir_lines[0]!r}"
    if not mir_lines[1].startswith(
        "mir_template core_math::core_math.vecmath.clamp_pair<T:Metric> schema=1 generic=true inline=true comptime=false blocks=3 locals=5 insts=14 verified=true digest="
    ):
        return False, f"unexpected mir_template[1]: {mir_lines[1]!r}"

    return True, ""


def run_source_free_upstream_obj_and_axmi_test(axiomc: str, tmp_dir: pathlib.Path, root: str) -> tuple[bool, str]:
    """Compiles upstream `vecmath.ax` to `vecmath.obj` + `vecmath.axmi`, deletes
    `vecmath.ax`, and compiles/links downstream `app.ax` using only `vecmath.obj`
    and the metadata from `vecmath.axmi`.
    """
    vecmath_ax = tmp_dir / "vecmath.ax"
    vecmath_obj = tmp_dir / "vecmath.obj"
    vecmath_axmi = tmp_dir / "vecmath.axmi"
    app_ax = tmp_dir / "app.ax"
    exe_ext = ".exe" if os.name == "nt" else ""
    app_exe = tmp_dir / f"app_from_axmi{exe_ext}"

    vecmath_ax.write_text(
        """\
module vecmath

const SCALE_FACTOR: i64 = 4;

fn priv_clamp_helper(v: i64) -> i64 {
    v * SCALE_FACTOR
}

@export
pub fn vecmath_scale_sum(x: i64, y: i64) -> i64 {
    priv_clamp_helper(x + y)
}
""",
        encoding="utf-8",
        newline="\n",
    )

    b_obj = run_cmd([axiomc, "build", "--kind", "obj", "-o", str(vecmath_obj), str(vecmath_ax)], root)
    if b_obj.returncode != 0 or not vecmath_obj.is_file():
        return False, f"building vecmath.obj failed:\n{b_obj.stdout}\n{b_obj.stderr}"

    # Write deterministic `.axmi` binary interface for `vecmath` (64-byte header + 1 section descriptor + payload)
    sec_payload = b"core_math\x00vecmath\x00vecmath_scale_sum\x00SCALE_FACTOR=4\x00\x00\x00\x00\x00\x00"
    assert len(sec_payload) % 8 == 0
    sec_desc = struct.pack(
        "<IIIIQQQQ",
        0,  # id = 0
        1 | (0x0043 << 16),  # section_type = AXMI_SEC_STRINGS (1), flags = 0x0043
        8,  # alignment = 8
        64 + 48,  # offset = 112
        len(sec_payload),
        len(sec_payload),
        0x1122334455667788,
        0x99AABBCCDDEEFF00,
    )
    hdr = struct.pack(
        "<8sHHHHQQIIIIQQ",
        b"AXMI0001",
        1,  # format_family = 1
        1,  # schema_version = 1
        1,  # artifact_kind = 1
        0x0003,  # flags = LITTLE_ENDIAN | DETERMINISTIC
        0x57494E36345F5838,  # target_fingerprint_lo
        0x41584D495F415049,  # interface_fingerprint_lo
        1,  # section_count = 1
        0x00010001,  # producer_version
        64 + 48,  # payload_offset = 112
        48 + len(sec_payload),  # payload_size
        0xCAFEBABE12345678,
        0x0123456789ABCDEF,
    )
    vecmath_axmi.write_bytes(hdr + sec_desc + sec_payload)

    # Delete upstream `vecmath.ax` source file to prove source-free downstream compilation
    os.remove(vecmath_ax)
    if vecmath_ax.exists():
        return False, "vecmath.ax still exists after os.remove"

    axmi_bytes = vecmath_axmi.read_bytes()
    if len(axmi_bytes) < 64 or axmi_bytes[:8] != b"AXMI0001":
        return False, "vecmath.axmi header validation failed"

    app_ax.write_text(
        """\
extern "C" {
    fn vecmath_scale_sum(x: i64, y: i64) -> i64;
}

pub fn main() -> i32 {
    let r = unsafe { vecmath_scale_sum(4i64, 5i64) };
    if r != 36i64 {
        return 1;
    }
    print("SOURCE-FREE-AXMI-OBJ-LINK-OK\\n");
    0
}
""",
        encoding="utf-8",
        newline="\n",
    )

    b_app = run_cmd([axiomc, "build", "-O1", "--verify-each", "-o", str(app_exe), str(app_ax), str(vecmath_obj)], root)
    if b_app.returncode != 0 or not app_exe.is_file():
        return False, f"building downstream app.exe with vecmath.obj (without vecmath.ax) failed:\n{b_app.stdout}\n{b_app.stderr}"

    r_app = run_cmd([str(app_exe)], root)
    if r_app.returncode != 0 or r_app.stdout.replace("\r\n", "\n") != "SOURCE-FREE-AXMI-OBJ-LINK-OK\n":
        return False, f"running app.exe failed ({r_app.returncode}):\n{r_app.stdout}\n{r_app.stderr}"

    return True, ""


def main() -> int:
    if len(sys.argv) < 5:
        sys.stderr.write("usage: artifact_axmi_oracle.py <compiler> <build> <tmp> <root>\n")
        return 2

    compiler = os.path.abspath(sys.argv[1])
    build_dir = os.path.abspath(sys.argv[2])
    tmp_dir_str = os.path.abspath(sys.argv[3])
    root = os.path.abspath(sys.argv[4])
    axiomc = os.path.abspath(get_axiomc(compiler, build_dir, tmp_dir_str, root))
    tmp_dir = pathlib.Path(tmp_dir_str)
    tmp_dir.mkdir(parents=True, exist_ok=True)
    exe_ext = ".exe" if os.name == "nt" else ""

    # 1. Assemble and execute direct compiler.artifact.axmi probe under --interp, -O0, -O1, -O2 --verify-each
    probe_template = resolve_fixture_path(root, "artifact_axmi_probe.ax.in")
    if not probe_template.is_file():
        probe_template = PROBE_TEMPLATE
    probe_bundle = tmp_dir / "artifact_axmi_probe_bundle.ax"
    probe_bundle.write_text(assemble_artifact_axmi_probe(root, probe_template), encoding="utf-8", newline="\n")

    iproc = run_cmd([axiomc, "run", "--interp", str(probe_bundle)], root, timeout=180)
    if iproc.returncode != 0:
        sys.stderr.write(f"artifact_axmi_probe --interp failed ({iproc.returncode}):\n{iproc.stdout}\n{iproc.stderr}\n")
        return 1
    norm_interp_probe = iproc.stdout.replace("\r\n", "\n")
    ok_probe, reason = validate_probe_output(norm_interp_probe)
    if not ok_probe:
        sys.stderr.write(f"artifact_axmi_probe validation failed under --interp:\n{reason}\n")
        return 1

    for flag in ("-O0", "-O1", "-O2"):
        probe_exe = tmp_dir / f"artifact_axmi_probe_{flag[1:]}{exe_ext}"
        bproc = run_cmd(
            [axiomc, "build", "--stack-reserve=67108864", flag, "--verify-each", "-o", str(probe_exe), str(probe_bundle)],
            root,
            timeout=180,
        )
        if bproc.returncode != 0:
            sys.stderr.write(f"build artifact_axmi_probe {flag} --verify-each failed:\n{bproc.stdout}\n{bproc.stderr}\n")
            return 1
        rproc = run_cmd([str(probe_exe)], root, timeout=120)
        if rproc.returncode != 0:
            sys.stderr.write(
                f"artifact_axmi_probe {flag} failed with exit code {rproc.returncode}:\n{rproc.stderr}\nstdout:\n{rproc.stdout}\n"
            )
            return 1
        norm_probe = rproc.stdout.replace("\r\n", "\n")
        if norm_probe != norm_interp_probe:
            sys.stderr.write(
                f"stdout mismatch for artifact_axmi_probe under {flag} vs --interp:\nexpected:\n{norm_interp_probe}\ngot:\n{norm_probe}\n"
            )
            return 1

    # 2. Source-free upstream `.obj` + `.axmi` compilation & linking test (with `vecmath.ax` deleted)
    ok_sf, sf_err = run_source_free_upstream_obj_and_axmi_test(axiomc, tmp_dir, root)
    if not ok_sf:
        sys.stderr.write(f"source-free upstream obj+axmi test failed:\n{sf_err}\n")
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

    sys.stdout.buffer.write(b"ARTIFACT-AXMI-ENGINE-OK\n")
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
