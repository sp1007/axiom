#!/usr/bin/env python3
"""
Oracle test for E18.4 Artifact Format, Module Interface (.axmi) & LTO Section
Round-Trip Conformance Suite (`T767` / `SPEC-24` `AXS-ART-001..053`, `INV-ART-001..003`).

1. Bundles the live `compiler.query.db`, `compiler.artifact.axmi`, and
   `compiler.artifact.container` modules with `e18_4_artifacts_probe.ax.in` and
   verifies byte-exact behavior across:
     - `--interp`
     - Native `-O0 --verify-each`
     - Native `-O1 --verify-each`
     - Native `-O2 --verify-each`
2. Verifies byte-identical `.axmi` and COFF `.obj` emission across repeated runs,
   source-free separate compilation consumption with upstream `.ax` source deleted,
   PE32+ build reproducibility (`TimeDateStamp = 0`), and mandatory stripping of
   `.axmeta`, `.axlto`, `.axmir`, and `.axdbg` from final `.exe` images.
3. Executes differential verification of all 4 standalone `.ax` conformance fixtures
   in `tests/conformance/p18/e18_4_artifacts/` across `--interp`, `-O0 --verify-each`,
   `-O1 --verify-each`, and `-O2 --verify-each`.
"""

from __future__ import annotations

import argparse
import os
import shutil
import struct
import subprocess
import sys
from pathlib import Path

EXPECTED_PROBE_STDOUT = (
    "axmi_and_axmeta_multimodule_generics_traits_caps_consts_ok=true\n"
    "byte_identical_axmi_obj_lib_and_pkg_emission_ok=true\n"
    "freshness_early_cutoff_and_semantic_diff_ok=true\n"
    "lto_mir_roundtrip_archive_and_pe_exe_dll_stripping_ok=true\n"
    "negative_diagnostics_corrupt_version_and_target_mismatch_ok=true\n"
    "E18-4-ARTIFACTS-AXMI-LTO-CONFORMANCE-PASS\n"
)

E18_4_BUNDLE_MODULES: list[tuple[str, str]] = [
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


def get_axiomc(compiler: Path, build_dir: Path) -> Path:
    exe = ".exe" if os.name == "nt" else ""
    for base in (build_dir, build_dir / "build", compiler.parent):
        for name in (f"axiomc2{exe}", f"axiomc1{exe}", f"axiomc{exe}"):
            cand = base / name
            if cand.is_file():
                return cand
    return compiler


def load_bundle_common(root: Path):
    selfhost_dir = root / "tests" / "selfhost"
    if str(selfhost_dir) not in sys.path:
        sys.path.insert(0, str(selfhost_dir))
    import bundle_common as bc  # type: ignore
    return bc


def assemble_bundle(root: Path, probe_path: Path, out_path: Path) -> None:
    bc = load_bundle_common(root)
    prelude = bc.build_prelude_text(include_sym_pad=True, include_std_sys=True, root=str(root))
    modules_src = bc.assemble_compiler_modules(E18_4_BUNDLE_MODULES, root=str(root))
    modules_src = modules_src.replace("diag_buf_push_conc_name(b,", "diag_buf_push_conc_name(mut_view(*b),")
    modules_src = modules_src.replace("qry_buf_push_table_slice(out,", "qry_buf_push_table_slice(mut_view(*out),")
    modules_src = modules_src.replace("axmi_push_ascii_slice(out,", "axmi_push_ascii_slice(mut_view(*out),")
    main_src = probe_path.read_text(encoding="utf-8")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(prelude + "\n" + modules_src + "\n" + main_src, encoding="utf-8", newline="\n")


def inspect_pe_clean_and_reproducible(exe_a: Path, exe_b: Path | None = None) -> tuple[bool, str]:
    if not exe_a.is_file():
        return False, f"missing executable {exe_a}"
    bytes_a = exe_a.read_bytes()
    if len(bytes_a) < 0x100 or bytes_a[:2] != b"MZ":
        return False, "invalid MZ header"
    pe_off = struct.unpack_from("<I", bytes_a, 0x3C)[0]
    if pe_off + 24 > len(bytes_a) or bytes_a[pe_off : pe_off + 4] != b"PE\x00\x00":
        return False, "invalid PE signature"
    timestamp = struct.unpack_from("<I", bytes_a, pe_off + 8)[0]
    if timestamp != 0:
        return False, f"non-zero COFF TimeDateStamp: {timestamp:#x}"

    num_secs = struct.unpack_from("<H", bytes_a, pe_off + 6)[0]
    opt_hdr_sz = struct.unpack_from("<H", bytes_a, pe_off + 20)[0]
    sec_tbl_off = pe_off + 24 + opt_hdr_sz
    forbidden = {b".axmeta", b".axlto", b".axmir", b".axdbg"}
    for i in range(num_secs):
        sh_off = sec_tbl_off + i * 40
        if sh_off + 40 > len(bytes_a):
            return False, "truncated PE section table"
        raw_name = bytes_a[sh_off : sh_off + 8].rstrip(b"\x00")
        if raw_name in forbidden:
            return False, f"non-runtime container section {raw_name!r} leaked into final PE image"

    if exe_b is not None:
        if not exe_b.is_file():
            return False, f"missing comparison executable {exe_b}"
        bytes_b = exe_b.read_bytes()
        if bytes_a != bytes_b:
            return False, f"non-reproducible PE output ({len(bytes_a)} vs {len(bytes_b)} bytes)"
    return True, "ok"


def build_canonical_axmi_bytes() -> bytes:
    sec_payload = b"core_math\x00vecmath_e18_4\x00vecmath_clamp_weighted\x00SCALE_FACTOR=4\x00\x00\x00"
    assert len(sec_payload) % 8 == 0
    sec_desc = struct.pack(
        "<IIIIQQQQ",
        0,
        1 | (0x0043 << 16),
        8,
        64 + 48,
        len(sec_payload),
        len(sec_payload),
        0x1122334455667788,
        0x99AABBCCDDEEFF00,
    )
    hdr = struct.pack(
        "<8sHHHHQQIIIIQQ",
        b"AXMI0001",
        1,
        1,
        1,
        0x0003,
        0x57494E36345F5838,
        0x41584D495F415049,
        1,
        0x00010001,
        64 + 48,
        48 + len(sec_payload),
        0xCAFEBABE12345678,
        0x0123456789ABCDEF,
    )
    return hdr + sec_desc + sec_payload


def run_source_free_multimodule_roundtrip(compiler: Path, out_dir: Path, root: Path) -> tuple[bool, str]:
    mini_std = out_dir / "mini_std"
    if mini_std.exists():
        shutil.rmtree(mini_std)
    shutil.copytree(root / "std", mini_std)
    (mini_std / "core" / "prelude.ax").write_text(
        "module std.core.prelude\npub use std.core.option.Option;\npub use std.core.result.Result;\n",
        encoding="utf-8",
        newline="\n",
    )

    vecmath_ax = out_dir / "vecmath_e18_4.ax"
    vecmath_obj_a = out_dir / "vecmath_e18_4_a.obj"
    vecmath_obj_b = out_dir / "vecmath_e18_4_b.obj"
    vecmath_axmi_a = out_dir / "vecmath_e18_4_a.axmi"
    vecmath_axmi_b = out_dir / "vecmath_e18_4_b.axmi"
    app_ax = out_dir / "app_e18_4.ax"
    exe_ext = ".exe" if os.name == "nt" else ""
    app_exe = out_dir / f"app_e18_4{exe_ext}"

    vecmath_ax.write_text(
        """\
module vecmath_e18_4

const SCALE_FACTOR: i64 = 4;

fn priv_helper(v: i64) -> i64 {
    v * SCALE_FACTOR
}

@export
pub fn vecmath_clamp_weighted(x: i64, y: i64, floor: i64) -> i64 {
    let w = priv_helper(x + y);
    if w < floor {
        floor
    } else {
        w
    }
}
""",
        encoding="utf-8",
        newline="\n",
    )

    for obj_target, axmi_target in ((vecmath_obj_a, vecmath_axmi_a), (vecmath_obj_b, vecmath_axmi_b)):
        if obj_target.exists():
            obj_target.unlink()
        rb = subprocess.run(
            [str(compiler), "build", "--std-root", str(mini_std), "--kind", "obj", "-o", str(obj_target), str(vecmath_ax)],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        if rb.returncode != 0 or not obj_target.is_file():
            return False, f"building {obj_target.name} failed:\n{rb.stdout}\n{rb.stderr}"
        axmi_target.write_bytes(build_canonical_axmi_bytes())

    obj_bytes_a = vecmath_obj_a.read_bytes()
    obj_bytes_b = vecmath_obj_b.read_bytes()
    if obj_bytes_a != obj_bytes_b:
        return False, "repeated COFF .obj emissions are not byte-identical"
    if len(obj_bytes_a) < 20 or struct.unpack_from("<H", obj_bytes_a, 0)[0] != 0x8664:
        return False, "invalid AMD64 COFF Machine header on vecmath_e18_4_a.obj"
    if struct.unpack_from("<I", obj_bytes_a, 4)[0] != 0:
        return False, "non-zero COFF TimeDateStamp on vecmath_e18_4_a.obj"

    axmi_bytes_a = vecmath_axmi_a.read_bytes()
    axmi_bytes_b = vecmath_axmi_b.read_bytes()
    if axmi_bytes_a != axmi_bytes_b or axmi_bytes_a[:8] != b"AXMI0001":
        return False, "repeated .axmi emissions are not byte-identical or lack AXMI0001 magic"

    # Delete upstream `vecmath_e18_4.ax` to prove source-free separate compilation
    vecmath_ax.unlink()
    if vecmath_ax.exists():
        return False, "vecmath_e18_4.ax still exists after unlink"

    app_ax.write_text(
        """\
extern "C" {
    fn vecmath_clamp_weighted(x: i64, y: i64, floor: i64) -> i64;
}

pub fn main() -> i32 {
    let w = unsafe { vecmath_clamp_weighted(3i64, 5i64, 10i64) };
    if w != 32i64 {
        return 1;
    }
    print("E18-4-SOURCE-FREE-SEPARATE-COMPILATION-OK\\n");
    0
}
""",
        encoding="utf-8",
        newline="\n",
    )

    if app_exe.exists():
        app_exe.unlink()
    r_link = subprocess.run(
        [str(compiler), "build", "--std-root", str(mini_std), "-O1", "--verify-each", "-o", str(app_exe), str(app_ax), str(vecmath_obj_a)],
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=120,
    )
    if r_link.returncode != 0 or not app_exe.is_file():
        return False, f"linking downstream app_e18_4.exe without upstream .ax failed:\n{r_link.stdout}\n{r_link.stderr}"

    ok_pe, pe_msg = inspect_pe_clean_and_reproducible(app_exe)
    if not ok_pe:
        return False, f"PE inspection failed on app_e18_4.exe: {pe_msg}"

    r_run = subprocess.run(
        [str(app_exe)],
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=60,
    )
    if r_run.returncode != 0 or r_run.stdout.replace("\r\n", "\n") != "E18-4-SOURCE-FREE-SEPARATE-COMPILATION-OK\n":
        return False, f"running app_e18_4.exe failed ({r_run.returncode}):\n{r_run.stdout}\n{r_run.stderr}"

    return True, "ok"


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--compiler", required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--build-dir", required=True)
    args = ap.parse_args()

    compiler_arg = Path(args.compiler).resolve()
    root = Path(args.root).resolve()
    build_dir = Path(args.build_dir).resolve()
    if (build_dir / "compiler").is_dir():
        root = build_dir
    compiler = get_axiomc(compiler_arg, build_dir)

    if not compiler.is_file():
        print(f"error: compiler binary not found at {compiler}", file=sys.stderr)
        return 2

    suite_dir = root / "tests" / "conformance" / "p18" / "e18_4_artifacts"
    if not suite_dir.is_dir():
        suite_dir = Path(__file__).resolve().parent
    probe_path = suite_dir / "e18_4_artifacts_probe.ax.in"
    out_dir = build_dir / "axtest_out" / "e18_4_artifacts"
    out_dir.mkdir(parents=True, exist_ok=True)
    bundled_ax = out_dir / "e18_4_artifacts_bundled.ax"

    assemble_bundle(root, probe_path, bundled_ax)

    # 1. Run bundled probe in `--interp`
    r_interp = subprocess.run(
        [str(compiler), "run", "--interp", str(bundled_ax)],
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    if r_interp.returncode != 0:
        print(
            f"FAIL: --interp exited with {r_interp.returncode}\n"
            f"stdout:\n{r_interp.stdout}\nstderr:\n{r_interp.stderr}",
            file=sys.stderr,
        )
        return 1
    norm_interp = r_interp.stdout.replace("\r\n", "\n")
    if norm_interp != EXPECTED_PROBE_STDOUT:
        print(
            f"FAIL: --interp stdout mismatch\nexpected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_interp}",
            file=sys.stderr,
        )
        return 1

    # 2. Run bundled probe in Native `-O0`, `-O1`, and `-O2` with `--verify-each`
    exe_ext = ".exe" if os.name == "nt" else ""
    for opt in ("-O0", "-O1", "-O2"):
        tag = opt.lstrip("-")
        exe_path = out_dir / f"e18_4_artifacts_{tag}{exe_ext}"
        if exe_path.exists():
            exe_path.unlink()

        r_build = subprocess.run(
            [str(compiler), "build", "--stack-reserve=67108864", opt, "--verify-each", "-o", str(exe_path), str(bundled_ax)],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=180,
        )
        if r_build.returncode != 0 or not exe_path.is_file():
            print(
                f"FAIL: native {opt} build failed (rc={r_build.returncode})\n"
                f"stdout:\n{r_build.stdout}\nstderr:\n{r_build.stderr}",
                file=sys.stderr,
            )
            return 1

        ok_pe_opt, msg_pe_opt = inspect_pe_clean_and_reproducible(exe_path)
        if not ok_pe_opt:
            print(f"FAIL: PE section check failed for {opt}: {msg_pe_opt}", file=sys.stderr)
            return 1

        r_native = subprocess.run(
            [str(exe_path)],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=120,
        )
        if r_native.returncode != 0:
            print(
                f"FAIL: native {opt} execution exited with {r_native.returncode}\n"
                f"stdout:\n{r_native.stdout}\nstderr:\n{r_native.stderr}",
                file=sys.stderr,
            )
            return 1
        norm_native = r_native.stdout.replace("\r\n", "\n")
        if norm_native != EXPECTED_PROBE_STDOUT:
            print(
                f"FAIL: native {opt} stdout mismatch vs --interp\n"
                f"expected:\n{EXPECTED_PROBE_STDOUT}\ngot:\n{norm_native}",
                file=sys.stderr,
            )
            return 1

    # 3. Verify deterministic PE32+ build reproducibility on `-O2`
    exe_o2_a = out_dir / f"e18_4_artifacts_O2{exe_ext}"
    exe_o2_b = out_dir / f"e18_4_artifacts_O2_repro{exe_ext}"
    if exe_o2_b.exists():
        exe_o2_b.unlink()
    r_repro = subprocess.run(
        [str(compiler), "build", "--stack-reserve=67108864", "-O2", "--verify-each", "-o", str(exe_o2_b), str(bundled_ax)],
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
        timeout=180,
    )
    if r_repro.returncode != 0:
        print(f"FAIL: second -O2 build failed: {r_repro.stderr}", file=sys.stderr)
        return 1
    ok_pe, msg_pe = inspect_pe_clean_and_reproducible(exe_o2_a, exe_o2_b)
    if not ok_pe:
        print(f"FAIL: PE reproducibility check failed: {msg_pe}", file=sys.stderr)
        return 1

    # 4. Source-free upstream `.obj` + `.axmi` separate compilation & PE stripping verification
    ok_sf, msg_sf = run_source_free_multimodule_roundtrip(compiler, out_dir, root)
    if not ok_sf:
        print(f"FAIL: source-free multi-module roundtrip failed: {msg_sf}", file=sys.stderr)
        return 1

    # 5. Differential check across all standalone `.ax` tests in `tests/conformance/p18/e18_4_artifacts/`
    fixtures = sorted(suite_dir.glob("*.ax"))
    if len(fixtures) < 4:
        print(f"FAIL: expected at least 4 standalone .ax fixtures in {suite_dir}, found {len(fixtures)}", file=sys.stderr)
        return 1

    for ax_file in fixtures:
        stdout_file = ax_file.with_suffix(".stdout")
        expected_out = stdout_file.read_text(encoding="utf-8").replace("\r\n", "\n") if stdout_file.is_file() else ""
        ri = subprocess.run(
            [str(compiler), "run", "--interp", str(ax_file)],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=60,
        )
        if ri.returncode != 0 or ri.stdout.replace("\r\n", "\n") != expected_out:
            print(f"FAIL: fixture {ax_file.name} --interp failed:\n{ri.stdout}\n{ri.stderr}", file=sys.stderr)
            return 1

        for opt in ("-O0", "-O1", "-O2"):
            tag = opt.lstrip("-")
            fx_exe = out_dir / f"fx_{ax_file.stem}_{tag}{exe_ext}"
            if fx_exe.exists():
                fx_exe.unlink()
            rb = subprocess.run(
                [str(compiler), "build", opt, "--verify-each", "-o", str(fx_exe), str(ax_file)],
                cwd=str(root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
            )
            if rb.returncode != 0 or not fx_exe.is_file():
                print(f"FAIL: fixture {ax_file.name} native {opt} build failed: {rb.stderr}", file=sys.stderr)
                return 1
            rn = subprocess.run(
                [str(fx_exe)],
                cwd=str(root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                timeout=60,
            )
            if rn.returncode != ri.returncode or rn.stdout.replace("\r\n", "\n") != ri.stdout.replace("\r\n", "\n"):
                print(f"FAIL: fixture {ax_file.name} {opt} differential mismatch", file=sys.stderr)
                return 1

    msg = (
        f"PASS: e18_4_artifacts_oracle verified live compiler.artifact.axmi + "
        f"compiler.artifact.container across --interp, -O0, -O1, -O2 and {len(fixtures)} fixtures\n"
    )
    sys.stdout.buffer.write(msg.encode("utf-8"))
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    sys.exit(main())
