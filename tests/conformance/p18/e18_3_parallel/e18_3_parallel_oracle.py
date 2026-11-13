#!/usr/bin/env python3
"""
Oracle test for E18.3 Parallel Compilation Determinism Conformance Suite
(`T763` / `SPEC-23` `AXS-PAR-001..053`, `INV-PAR-001..003`).

Bundles the live `compiler.query.db`, `compiler.incremental.fingerprint`,
`compiler.incremental.cache`, `compiler.parallel.scheduler`, and
`compiler.parallel.codegen` modules with `e18_3_parallel_probe.ax.in` and
verifies byte-exact behavior across:
  1. `--interp`
  2. Native `-O0 --verify-each`
  3. Native `-O1 --verify-each`
  4. Native `-O2 --verify-each`
Plus verification of on-disk `.axiom-cache/dep-graph.axcache` (`AXCACHE1`) and
`.axiom-cache/objects/*.obj` COFF artifacts (`Machine = 0x8664`, `TimeDateStamp = 0`),
PE32+ build reproducibility, and differential execution of all standalone `.ax`
conformance fixtures in `tests/conformance/p18/e18_3_parallel/`.
"""

from __future__ import annotations

import argparse
import os
import struct
import subprocess
import sys
import time
from pathlib import Path

EXPECTED_PROBE_STDOUT = (
    "jobs_1_2_4_8_hir_mir_and_interner_invariance_ok=true\n"
    "cross_worker_cycle_rotation_and_single_flight_ok=true\n"
    "jobs_1_2_4_8_byte_identical_obj_exe_and_lir_dumps_ok=true\n"
    "warm_noop_parallel_cache_reuse_ok=true\n"
    "hybrid_parallel_incremental_rebuild_determinism_ok=true\n"
    "multi_cgu_partition_and_archive_order_ok=true\n"
    "fault_retry_quarantine_and_dup_verify_ok=true\n"
    "randomized_delay_multifile_diag_ordering_ok=true\n"
    "E18-3-PARALLEL-COMPILATION-CONFORMANCE-PASS\n"
)

E18_3_BUNDLE_MODULES: list[tuple[str, str]] = [
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
    ("compiler.incremental.fingerprint", "compiler"),
    ("compiler.incremental.cache", "compiler"),
    ("compiler.parallel.scheduler", "compiler"),
    ("compiler.parallel.codegen", "compiler"),
]


def get_axiomc(compiler: Path, build_dir: Path) -> Path:
    exe = ".exe" if os.name == "nt" else ""
    for base in (build_dir, build_dir / "build"):
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
    modules_src = bc.assemble_compiler_modules(E18_3_BUNDLE_MODULES, root=str(root))
    main_src = probe_path.read_text(encoding="utf-8")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    out_path.write_text(prelude + "\n" + modules_src + "\n" + main_src, encoding="utf-8", newline="\n")


def verify_on_disk_cache_files(cache_dir: Path, mode_label: str) -> bool:
    index_path = cache_dir / "dep-graph.axcache"
    if not index_path.is_file():
        print(f"FAIL [{mode_label}]: missing on-disk index {index_path}", file=sys.stderr)
        return False
    raw = index_path.read_bytes()
    if len(raw) < 120 or raw[:8] != b"AXCACHE1":
        print(f"FAIL [{mode_label}]: invalid AXCACHE1 header in {index_path}", file=sys.stderr)
        return False
    schema_ver = int.from_bytes(raw[8:12], "little")
    if schema_ver != 1:
        print(f"FAIL [{mode_label}]: unexpected schema_version={schema_ver}", file=sys.stderr)
        return False
    tmp_index = cache_dir / "dep-graph.axcache.tmp"
    if tmp_index.exists():
        print(f"FAIL [{mode_label}]: leftover temporary file {tmp_index}", file=sys.stderr)
        return False
    obj_dir = cache_dir / "objects"
    obj_files = sorted(obj_dir.glob("*.obj")) if obj_dir.is_dir() else []
    if len(obj_files) < 4:
        print(f"FAIL [{mode_label}]: expected >= 4 cached .obj files in {obj_dir}, found {len(obj_files)}", file=sys.stderr)
        return False
    for of in obj_files:
        ob = of.read_bytes()
        if len(ob) < 64 or ob[:2] != b"\x64\x86" or ob[4:8] != b"\x00\x00\x00\x00":
            print(f"FAIL [{mode_label}]: non-deterministic or invalid COFF header in {of}", file=sys.stderr)
            return False
    return True


def verify_pe_reproducible(exe_a: Path, exe_b: Path) -> tuple[bool, str]:
    if not exe_a.is_file() or not exe_b.is_file():
        return False, "missing built executable"
    bytes_a = exe_a.read_bytes()
    bytes_b = exe_b.read_bytes()
    if len(bytes_a) < 0x100 or bytes_a[:2] != b"MZ":
        return False, "invalid MZ header"
    pe_off = struct.unpack_from("<I", bytes_a, 0x3C)[0]
    if pe_off + 24 > len(bytes_a) or bytes_a[pe_off : pe_off + 4] != b"PE\x00\x00":
        return False, "invalid PE signature"
    timestamp = struct.unpack_from("<I", bytes_a, pe_off + 8)[0]
    if timestamp != 0:
        return False, f"non-zero COFF TimeDateStamp: {timestamp:#x}"
    if bytes_a != bytes_b:
        return False, f"non-reproducible PE output ({len(bytes_a)} vs {len(bytes_b)} bytes)"
    return True, "ok"


# --- Load-aware step deadline (T440, ADR-0042 section 1) ------------------------------------------
# All subprocess steps of this oracle share ONE wall-clock budget instead of fixed per-step timeouts:
# the old fixed 180 s limit of the bundled `--interp` step was hit on the shared 4-core machine under
# `-j 2` load and surfaced as a TimeoutExpired traceback (T422-qa section 7). ORACLE_BUDGET_S is 3x the
# slowest measured wall time of the whole oracle at scale 1 (table in _workspaces/reports/T440-report.md).
# It is multiplied by AXTEST_TIMEOUT_SCALE (default 1): set that variable to the runner's
# `--timeout-scale` value when re-running a timed-out id (tools/axtest.py does not export it yet).
# A hang anywhere stops the run at the deadline with one `TIMEOUT:` line on stderr and exit 1;
# the manifest `timeout:` stays above the budget so the oracle reports first.
ORACLE_BUDGET_S = 1002.0


def _timeout_scale() -> float:
    try:
        scale = float(os.environ.get("AXTEST_TIMEOUT_SCALE") or "1")
    except ValueError:
        return 1.0
    return scale if scale > 0 else 1.0


_DEADLINE = time.monotonic() + ORACLE_BUDGET_S * _timeout_scale()


class OracleTimeout(Exception):
    pass


def bounded_run(cmd, **kwargs):
    """subprocess.run with the time left of the oracle budget as its timeout."""
    left = _DEADLINE - time.monotonic()
    step = " ".join([os.path.basename(str(cmd[0]))] + [str(c) for c in cmd[1:3]])
    if left <= 0:
        raise OracleTimeout(f"budget exhausted before `{step}`")
    try:
        return subprocess.run(cmd, timeout=left, **kwargs)
    except subprocess.TimeoutExpired:
        raise OracleTimeout(
            f"`{step}` killed after {left:.0f}s (budget {ORACLE_BUDGET_S:g}s x scale {_timeout_scale():g})"
        ) from None


def guarded_main(main_fn) -> int:
    try:
        return main_fn()
    except OracleTimeout as e:
        sys.stderr.write(f"TIMEOUT: {e}\n")
        return 1


def main() -> int:
    ap = argparse.ArgumentParser()
    ap.add_argument("--compiler", required=True)
    ap.add_argument("--root", required=True)
    ap.add_argument("--build-dir", required=True)
    args = ap.parse_args()

    compiler_arg = Path(args.compiler).resolve()
    root = Path(args.root).resolve()
    build_dir = Path(args.build_dir).resolve()
    compiler = get_axiomc(compiler_arg, build_dir)

    if not compiler.is_file():
        print(f"error: compiler binary not found at {compiler}", file=sys.stderr)
        return 2

    suite_dir = root / "tests" / "conformance" / "p18" / "e18_3_parallel"
    probe_path = suite_dir / "e18_3_parallel_probe.ax.in"
    out_dir = build_dir / "axtest_out" / "e18_3_parallel"
    out_dir.mkdir(parents=True, exist_ok=True)
    bundled_ax = out_dir / "e18_3_parallel_bundled.ax"

    assemble_bundle(root, probe_path, bundled_ax)

    # 1. Run bundled probe in `--interp`
    r_interp = bounded_run(
        [str(compiler), "run", "--interp", str(bundled_ax)],
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
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
        exe_path = out_dir / f"e18_3_parallel_{tag}{exe_ext}"
        if exe_path.exists():
            exe_path.unlink()

        r_build = bounded_run(
            [str(compiler), "build", "--stack-reserve=67108864", opt, "--verify-each", "-o", str(exe_path), str(bundled_ax)],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if r_build.returncode != 0 or not exe_path.is_file():
            print(
                f"FAIL: native {opt} build failed (rc={r_build.returncode})\n"
                f"stdout:\n{r_build.stdout}\nstderr:\n{r_build.stderr}",
                file=sys.stderr,
            )
            return 1

        disk_cache_dir = out_dir / f"axiom_par_cache_{tag}"
        cache_arg = "--cache-dir=" + str(disk_cache_dir).replace("\\", "/")
        r_native = bounded_run(
            [str(exe_path), cache_arg],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
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
        if not verify_on_disk_cache_files(disk_cache_dir, opt):
            return 1

    # 3. Verify deterministic PE32+ build reproducibility on `-O2`
    exe_o2_a = out_dir / f"e18_3_parallel_O2{exe_ext}"
    exe_o2_b = out_dir / f"e18_3_parallel_O2_repro{exe_ext}"
    if exe_o2_b.exists():
        exe_o2_b.unlink()
    r_repro = bounded_run(
        [str(compiler), "build", "--stack-reserve=67108864", "-O2", "--verify-each", "-o", str(exe_o2_b), str(bundled_ax)],
        cwd=str(root),
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace",
    )
    if r_repro.returncode != 0:
        print(f"FAIL: second -O2 build failed: {r_repro.stderr}", file=sys.stderr)
        return 1
    ok_pe, msg_pe = verify_pe_reproducible(exe_o2_a, exe_o2_b)
    if not ok_pe:
        print(f"FAIL: PE reproducibility check failed: {msg_pe}", file=sys.stderr)
        return 1

    # 4. Differential check across all standalone `.ax` tests in `tests/conformance/p18/e18_3_parallel/`
    fixtures = sorted(suite_dir.glob("*.ax"))
    if len(fixtures) < 3:
        print(f"FAIL: expected at least 3 standalone .ax fixtures in {suite_dir}", file=sys.stderr)
        return 1

    for ax_file in fixtures:
        stdout_file = ax_file.with_suffix(".stdout")
        expected_out = stdout_file.read_text(encoding="utf-8").replace("\r\n", "\n") if stdout_file.is_file() else ""
        ri = bounded_run(
            [str(compiler), "run", "--interp", str(ax_file)],
            cwd=str(root),
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
        )
        if ri.returncode != 0 or ri.stdout.replace("\r\n", "\n") != expected_out:
            print(f"FAIL: fixture {ax_file.name} --interp failed: {ri.stderr}", file=sys.stderr)
            return 1

        for opt in ("-O0", "-O1", "-O2"):
            tag = opt.lstrip("-")
            fx_exe = out_dir / f"fx_{ax_file.stem}_{tag}{exe_ext}"
            if fx_exe.exists():
                fx_exe.unlink()
            rb = bounded_run(
                [str(compiler), "build", opt, "--verify-each", "-o", str(fx_exe), str(ax_file)],
                cwd=str(root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if rb.returncode != 0 or not fx_exe.is_file():
                print(f"FAIL: fixture {ax_file.name} native {opt} build failed: {rb.stderr}", file=sys.stderr)
                return 1
            rn = bounded_run(
                [str(fx_exe)],
                cwd=str(root),
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
            )
            if rn.returncode != ri.returncode or rn.stdout.replace("\r\n", "\n") != ri.stdout.replace("\r\n", "\n"):
                print(f"FAIL: fixture {ax_file.name} {opt} differential mismatch", file=sys.stderr)
                return 1

    msg = (
        f"PASS: e18_3_parallel_oracle verified live compiler.parallel.scheduler + "
        f"compiler.parallel.codegen across --interp, -O0, -O1, -O2 and {len(fixtures)} fixtures\n"
    )
    sys.stdout.buffer.write(msg.encode("utf-8"))
    sys.stdout.buffer.flush()
    return 0


if __name__ == "__main__":
    sys.exit(guarded_main(main))
