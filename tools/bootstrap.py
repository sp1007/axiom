#!/usr/bin/env python3
"""Bootstrap driver for the self-hosted Axiom compiler (T086 / T087; SPEC-00 §6, SPEC-20 §4/§6).

Python 3 standard library only. Assembles the multi-module `axiomc` bundle using the canonical
module order from `tests/selfhost/obj_link_driver/gen_obj_link_driver_tests.py` (`axiomc_bundle_text()`)
and drives:
  - Stage 1: `axiom0` -> `axiomc1.exe`
  - Stage 2: `axiomc1` -> `axiomc2.exe`
  - Stage 3: `axiomc2` -> `axiomc3.exe` (with SHA-256 fixed-point verification)

All builds pass `--stack-reserve 67108864` (64 MB per ADR-0003) and `--std-root <std>`, and run
with `SOURCE_DATE_EPOCH=0` and host C/binutils toolchains (`gcc`, `clang`, `ld`, `as`, `link`)
filtered from `PATH` (INV-BOOT-003).
"""

import argparse
import ctypes
from ctypes import wintypes
import hashlib
import os
import subprocess
import sys
import tempfile
import time

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DEFAULT_STACK_RESERVE = 67108864  # 64 MB per ADR-0003

# Budget limits per SPEC-20 §6.2 / ADR-0005 §7:
STAGE1_MAX_WALL_S = 120.0       # < 2 minutes
STAGE1_MAX_PEAK_MB = 2048.0     # < 2.0 GB
STAGE2_MAX_WALL_S = 600.0       # < 10 minutes
STAGE2_MAX_PEAK_MB = 4096.0     # < 4.0 GB


class PROCESS_MEMORY_COUNTERS(ctypes.Structure):
    _fields_ = [
        ("cb", wintypes.DWORD),
        ("PageFaultCount", wintypes.DWORD),
        ("PeakWorkingSetSize", ctypes.c_size_t),
        ("WorkingSetSize", ctypes.c_size_t),
        ("QuotaPeakPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPagedPoolUsage", ctypes.c_size_t),
        ("QuotaPeakNonPagedPoolUsage", ctypes.c_size_t),
        ("QuotaNonPagedPoolUsage", ctypes.c_size_t),
        ("PagefileUsage", ctypes.c_size_t),
        ("PeakPagefileUsage", ctypes.c_size_t),
    ]


def query_peak_memory_bytes(handle_int):
    """Return (peak_working_set_bytes, peak_commit_bytes) for a Win32 process handle."""
    if os.name != "nt" or not handle_int:
        return (0, 0)
    pmc = PROCESS_MEMORY_COUNTERS()
    pmc.cb = ctypes.sizeof(PROCESS_MEMORY_COUNTERS)
    ok = 0
    try:
        fn = getattr(ctypes.windll.kernel32, "K32GetProcessMemoryInfo", None)
        if fn is None:
            fn = ctypes.windll.psapi.GetProcessMemoryInfo
        fn.argtypes = [wintypes.HANDLE, ctypes.POINTER(PROCESS_MEMORY_COUNTERS), wintypes.DWORD]
        fn.restype = wintypes.BOOL
        ok = fn(wintypes.HANDLE(handle_int), ctypes.byref(pmc), pmc.cb)
    except Exception:
        ok = 0
    if not ok:
        return (0, 0)
    return (int(pmc.PeakWorkingSetSize), int(pmc.PeakPagefileUsage))


def load_bundle_text(root):
    obj_link_dir = os.path.join(root, "tests", "selfhost", "obj_link_driver")
    selfhost_dir = os.path.join(root, "tests", "selfhost")
    for p in (obj_link_dir, selfhost_dir):
        if p not in sys.path:
            sys.path.insert(0, p)
    import gen_obj_link_driver_tests as gen
    return gen.axiomc_bundle_text()


def clean_bootstrap_env():
    """Return a clean environment with SOURCE_DATE_EPOCH=0 and no gcc/ld/as on PATH."""
    env = dict(os.environ)
    env["SOURCE_DATE_EPOCH"] = "0"
    for k in ("AXIOM_STD",):
        env.pop(k, None)
    raw_path = env.get("PATH", "")
    kept = []
    forbidden_tools = ("gcc.exe", "ld.exe", "as.exe", "clang.exe", "link.exe")
    for entry in raw_path.split(os.pathsep):
        e = entry.strip().strip('"')
        if not e:
            continue
        has_toolchain = False
        for tool in forbidden_tools:
            if os.path.isfile(os.path.join(e, tool)):
                has_toolchain = True
                break
        if not has_toolchain:
            kept.append(entry)
    env["PATH"] = os.pathsep.join(kept)
    return env


def parse_time_passes(stdout_text):
    """Extract ordered (pass_name, seconds) pairs from `--time-passes` output."""
    passes = []
    for line in stdout_text.splitlines():
        s = line.strip()
        if s.startswith("time: "):
            parts = s[6:].strip().split()
            if len(parts) >= 2 and parts[1].endswith("s"):
                try:
                    secs = float(parts[1][:-1])
                    passes.append((parts[0], secs))
                except ValueError:
                    pass
    return passes


def sha256_file(path):
    h = hashlib.sha256()
    with open(path, "rb") as f:
        while True:
            chunk = f.read(65536)
            if not chunk:
                break
            h.update(chunk)
    return h.hexdigest()


def run_stage_build(
    stage_label,
    compiler_path,
    bundle_path,
    output_path,
    std_root,
    stack_reserve,
    opt_level,
    time_passes,
    cwd,
    env,
):
    cmd = [
        compiler_path,
        "build",
        bundle_path,
        "-o",
        output_path,
        "--stack-reserve",
        str(stack_reserve),
        "--std-root",
        std_root,
    ]
    if opt_level == "O1":
        cmd.append("-O1")
    elif opt_level == "O0":
        cmd.append("-O0")
    if time_passes:
        cmd.append("--time-passes")

    if os.path.isfile(output_path):
        try:
            os.remove(output_path)
        except OSError:
            pass

    t0 = time.perf_counter()
    proc = subprocess.Popen(
        cmd,
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    out_bytes, err_bytes = proc.communicate()
    wall_s = time.perf_counter() - t0
    peak_ws, peak_commit = query_peak_memory_bytes(int(proc._handle) if hasattr(proc, "_handle") else 0)
    rc = proc.returncode

    out_text = out_bytes.decode("utf-8", "replace").replace("\r\n", "\n")
    err_text = err_bytes.decode("utf-8", "replace").replace("\r\n", "\n")
    passes = parse_time_passes(out_text) if time_passes else []
    peak_rss_mb = max(peak_ws, peak_commit) / (1024.0 * 1024.0)
    peak_ws_mb = peak_ws / (1024.0 * 1024.0)
    peak_commit_mb = peak_commit / (1024.0 * 1024.0)

    return {
        "stage": stage_label,
        "cmd": cmd,
        "rc": rc,
        "stdout": out_text,
        "stderr": err_text,
        "wall_s": wall_s,
        "peak_ws_bytes": peak_ws,
        "peak_commit_bytes": peak_commit,
        "peak_ws_mb": peak_ws_mb,
        "peak_commit_mb": peak_commit_mb,
        "peak_mb": peak_rss_mb,
        "passes": passes,
        "output": output_path,
        "size_bytes": os.path.getsize(output_path) if os.path.isfile(output_path) else 0,
        "sha256": sha256_file(output_path) if os.path.isfile(output_path) else "",
    }


def write_perf_csv(csv_path, stage_results):
    os.makedirs(os.path.dirname(os.path.abspath(csv_path)), exist_ok=True)
    lines = ["stage,opt,pass,seconds,milliseconds,peak_ws_mb,peak_commit_mb,binary_bytes,sha256"]
    for res in stage_results:
        st = res["stage"]
        opt = res.get("opt", "default")
        ws_mb = "%.2f" % res["peak_ws_mb"]
        cm_mb = "%.2f" % res["peak_commit_mb"]
        sz = str(res["size_bytes"])
        digest = res["sha256"]
        for pname, secs in res["passes"]:
            ms = int(round(secs * 1000.0))
            lines.append(
                "%s,%s,%s,%.6f,%d,%s,%s,%s,%s"
                % (st, opt, pname, secs, ms, ws_mb, cm_mb, sz, digest)
            )
        total_ms = int(round(res["wall_s"] * 1000.0))
        lines.append(
            "%s,%s,wall_total,%.6f,%d,%s,%s,%s,%s"
            % (st, opt, res["wall_s"], total_ms, ws_mb, cm_mb, sz, digest)
        )
    with open(csv_path, "w", encoding="utf-8", newline="\n") as f:
        f.write("\n".join(lines) + "\n")


def find_default_stage0(root):
    candidates = [
        os.path.join(root, "build", "axiom0.exe"),
        os.path.join(root, "build", "axiom0"),
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return candidates[0]


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace", newline="\n")
        except Exception:
            pass

    ap = argparse.ArgumentParser(description="Bootstrap the self-hosted Axiom compiler (axiomc).")
    ap.add_argument("--root", default=ROOT, help="Repository root directory")
    ap.add_argument("--stage0", default=None, help="Path to Stage-0 compiler (axiom0.exe)")
    ap.add_argument("--build-dir", default=None, help="Output build directory (default: dirname of --stage0)")
    ap.add_argument("--out", default=None, help="Explicit output path for Stage-1 binary (axiomc1.exe)")
    ap.add_argument("--bundle-out", default=None, help="Path to write assembled axiomc_bundle.ax")
    ap.add_argument("--std-root", default=None, help="Path to std library root (default: <root>/std)")
    ap.add_argument("--stack-reserve", type=int, default=DEFAULT_STACK_RESERVE, help="PE stack reserve in bytes")
    ap.add_argument("--stage", type=int, choices=(1, 2, 3), default=1, help="Highest bootstrap stage to build (1, 2, or 3)")
    ap.add_argument("--opt", choices=("default", "O0", "O1"), default="default", help="Optimization flag for Stage-1 build")
    ap.add_argument("--stage2-opt", choices=("default", "O0", "O1"), default="O1", help="Optimization flag for Stage-2/3 self-compile")
    ap.add_argument("--time-passes", action="store_true", help="Pass --time-passes and report per-pass timings")
    ap.add_argument("--perf-csv", default=None, help="Write self-host timing and memory CSV to this path")
    ap.add_argument("--check-budget", action="store_true", help="Enforce SPEC-20 §6.2 wall-time and RAM budgets")
    args = ap.parse_args(argv)

    root = os.path.abspath(args.root)
    stage0 = os.path.abspath(args.stage0) if args.stage0 else find_default_stage0(root)
    if not os.path.isfile(stage0):
        print("bootstrap: error: stage0 compiler not found at %s" % stage0, file=sys.stderr)
        return 2

    build_dir = os.path.abspath(args.build_dir) if args.build_dir else os.path.dirname(stage0)
    os.makedirs(build_dir, exist_ok=True)

    std_root = os.path.abspath(args.std_root) if args.std_root else os.path.join(root, "std")
    if not os.path.isdir(std_root):
        print("bootstrap: error: std root not found at %s" % std_root, file=sys.stderr)
        return 2

    axiomc1 = os.path.abspath(args.out) if args.out else os.path.join(build_dir, "axiomc1.exe")
    axiomc2 = os.path.join(os.path.dirname(axiomc1), "axiomc2.exe")
    axiomc3 = os.path.join(os.path.dirname(axiomc1), "axiomc3.exe")

    bundle_text = load_bundle_text(root)
    tmp_ctx = None
    if args.bundle_out:
        bundle_path = os.path.abspath(args.bundle_out)
        os.makedirs(os.path.dirname(bundle_path), exist_ok=True)
    else:
        tmp_ctx = tempfile.TemporaryDirectory(prefix="axiom_bootstrap_")
        bundle_path = os.path.join(tmp_ctx.name, "axiomc_bundle.ax")

    try:
        with open(bundle_path, "wb") as f:
            f.write(bundle_text.encode("utf-8"))

        env = clean_bootstrap_env()
        stage_results = []

        # Stage 1: axiom0 -> axiomc1
        r1 = run_stage_build(
            "stage1_axiom0_to_axiomc1",
            stage0,
            bundle_path,
            axiomc1,
            std_root,
            args.stack_reserve,
            args.opt,
            args.time_passes or bool(args.perf_csv),
            root,
            env,
        )
        r1["opt"] = args.opt
        stage_results.append(r1)
        if r1["rc"] != 0 or not os.path.isfile(axiomc1):
            print(
                "bootstrap: FAIL stage1 (axiom0 -> axiomc1) rc=%d\n%s"
                % (r1["rc"], r1["stderr"][:2000]),
                file=sys.stderr,
            )
            return 1
        print(
            "STAGE1 OK: %s (%d bytes, sha256=%s, wall=%.2fs, peak_ws=%.1fMB, peak_commit=%.1fMB)"
            % (axiomc1, r1["size_bytes"], r1["sha256"][:16], r1["wall_s"], r1["peak_ws_mb"], r1["peak_commit_mb"])
        )

        # Stage 2: axiomc1 -> axiomc2
        if args.stage >= 2:
            r2 = run_stage_build(
                "stage2_axiomc1_to_axiomc2",
                axiomc1,
                bundle_path,
                axiomc2,
                std_root,
                args.stack_reserve,
                args.stage2_opt,
                args.time_passes or bool(args.perf_csv),
                root,
                env,
            )
            r2["opt"] = args.stage2_opt
            stage_results.append(r2)
            if r2["rc"] != 0 or not os.path.isfile(axiomc2):
                print(
                    "bootstrap: FAIL stage2 (axiomc1 -> axiomc2) rc=%d\n%s"
                    % (r2["rc"], r2["stderr"][:2000]),
                    file=sys.stderr,
                )
                return 1
            print(
                "STAGE2 OK: %s (%d bytes, sha256=%s, wall=%.2fs, peak_ws=%.1fMB, peak_commit=%.1fMB)"
                % (axiomc2, r2["size_bytes"], r2["sha256"][:16], r2["wall_s"], r2["peak_ws_mb"], r2["peak_commit_mb"])
            )

        # Stage 3: axiomc2 -> axiomc3
        if args.stage >= 3:
            r3 = run_stage_build(
                "stage3_axiomc2_to_axiomc3",
                axiomc2,
                bundle_path,
                axiomc3,
                std_root,
                args.stack_reserve,
                args.stage2_opt,
                args.time_passes or bool(args.perf_csv),
                root,
                env,
            )
            r3["opt"] = args.stage2_opt
            stage_results.append(r3)
            if r3["rc"] != 0 or not os.path.isfile(axiomc3):
                print(
                    "bootstrap: FAIL stage3 (axiomc2 -> axiomc3) rc=%d\n%s"
                    % (r3["rc"], r3["stderr"][:2000]),
                    file=sys.stderr,
                )
                return 1
            print(
                "STAGE3 OK: %s (%d bytes, sha256=%s, wall=%.2fs, peak_ws=%.1fMB, peak_commit=%.1fMB)"
                % (axiomc3, r3["size_bytes"], r3["sha256"][:16], r3["wall_s"], r3["peak_ws_mb"], r3["peak_commit_mb"])
            )
            if r2["sha256"] != r3["sha256"]:
                print(
                    "bootstrap: FAIL fixed-point mismatch: sha256(axiomc2)=%s != sha256(axiomc3)=%s"
                    % (r2["sha256"], r3["sha256"]),
                    file=sys.stderr,
                )
                return 1
            print("FIXED-POINT OK: sha256(axiomc2) == sha256(axiomc3) == %s" % r3["sha256"])

        if args.perf_csv:
            write_perf_csv(args.perf_csv, stage_results)
            print("PERF-CSV WRITTEN: %s" % args.perf_csv)

        if args.check_budget:
            if r1["wall_s"] >= STAGE1_MAX_WALL_S:
                print(
                    "bootstrap: FAIL stage1 wall time %.2fs exceeds budget %.2fs"
                    % (r1["wall_s"], STAGE1_MAX_WALL_S),
                    file=sys.stderr,
                )
                return 1
            if r1["peak_ws_mb"] >= STAGE1_MAX_PEAK_MB:
                print(
                    "bootstrap: FAIL stage1 peak memory %.1fMB exceeds budget %.1fMB"
                    % (r1["peak_ws_mb"], STAGE1_MAX_PEAK_MB),
                    file=sys.stderr,
                )
                return 1
            if args.stage >= 2:
                if r2["wall_s"] >= STAGE2_MAX_WALL_S:
                    print(
                        "bootstrap: FAIL stage2 wall time %.2fs exceeds budget %.2fs"
                        % (r2["wall_s"], STAGE2_MAX_WALL_S),
                        file=sys.stderr,
                    )
                    return 1
                if r2["peak_ws_mb"] >= STAGE2_MAX_PEAK_MB:
                    print(
                        "bootstrap: FAIL stage2 peak memory %.1fMB exceeds budget %.1fMB"
                        % (r2["peak_ws_mb"], STAGE2_MAX_PEAK_MB),
                        file=sys.stderr,
                    )
                    return 1

        return 0
    finally:
        if tmp_ctx is not None:
            tmp_ctx.cleanup()


if __name__ == "__main__":
    sys.exit(main())
