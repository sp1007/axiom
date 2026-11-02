#!/usr/bin/env python3
"""Bootstrap driver for the self-hosted Axiom compiler (T086 / T087; SPEC-00 §6, SPEC-20 §4/§6).

Python 3 standard library only. Assembles the multi-module `axiomc` bundle using the canonical
module order from `tests/selfhost/obj_link_driver/gen_obj_link_driver_tests.py` (`axiomc_bundle_text()`)
and drives:
  - Stage 1: `axiom0` -> `axiomc1.exe`
  - Stage 2: `axiomc1` -> `axiomc2.exe` (in directory A: `<build_dir>/dir_stage2_<opt>`)
  - Stage 3: `axiomc2` -> `axiomc3.exe` (in directory B: `<build_dir>/dir_stage3_<opt>`,
             verifying byte-identical SHA-256 fixed point in two distinct directories)

Supports checking the fixed point at `-O1`, `-O0`, or both (`--check-both-opt` / `--stage2-opt both`).
All builds pass `--stack-reserve 67108864` (64 MB per ADR-0003) and `--std-root <std>`, and run
with `SOURCE_DATE_EPOCH=0` and host C/binutils toolchains (`gcc`, `clang`, `ld`, `as`, `link`, `cl`, `lld`)
removed from `PATH` (INV-BOOT-003, ABOOT-74/75).
"""

import argparse
import ctypes
from ctypes import wintypes
import hashlib
import os
import shutil
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
STAGE3_MAX_WALL_S = 600.0       # < 10 minutes
STAGE3_MAX_PEAK_MB = 4096.0     # < 4.0 GB


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
    """Return a clean environment with SOURCE_DATE_EPOCH=0 and no gcc/ld/as/clang/link on PATH."""
    env = dict(os.environ)
    env["SOURCE_DATE_EPOCH"] = "0"
    for k in ("AXIOM_STD",):
        env.pop(k, None)
    raw_path = env.get("PATH", "")
    kept = []
    forbidden_tools = (
        "gcc.exe",
        "ld.exe",
        "as.exe",
        "clang.exe",
        "link.exe",
        "cl.exe",
        "lld.exe",
        "lld-link.exe",
        "gcc",
        "ld",
        "as",
        "clang",
    )
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


def verify_no_external_tools_on_path(env):
    """Verify that gcc, ld, as, clang, link are absent from env['PATH'] (INV-BOOT-003)."""
    raw_path = env.get("PATH", "")
    forbidden = ("gcc.exe", "ld.exe", "as.exe", "clang.exe", "link.exe")
    for entry in raw_path.split(os.pathsep):
        e = entry.strip().strip('"')
        if not e:
            continue
        for tool in forbidden:
            full = os.path.join(e, tool)
            if os.path.isfile(full):
                return False, full
    return True, None


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


def files_byte_identical(path_a, path_b):
    if not os.path.isfile(path_a) or not os.path.isfile(path_b):
        return False
    if os.path.getsize(path_a) != os.path.getsize(path_b):
        return False
    with open(path_a, "rb") as fa, open(path_b, "rb") as fb:
        while True:
            ca = fa.read(65536)
            cb = fb.read(65536)
            if ca != cb:
                return False
            if not ca:
                return True


def latest_source_mtime(root):
    latest = 0.0
    for sub in ("compiler", "std"):
        base = os.path.join(root, sub)
        if not os.path.isdir(base):
            continue
        for dirpath, _dirnames, filenames in os.walk(base):
            for fn in filenames:
                if fn.endswith(".ax"):
                    try:
                        m = os.path.getmtime(os.path.join(dirpath, fn))
                        if m > latest:
                            latest = m
                    except OSError:
                        pass
    return latest


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
        "opt": opt_level,
        "cmd": cmd,
        "cwd": cwd,
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


def make_cached_result(stage_label, opt_level, binary_path, cwd):
    return {
        "stage": stage_label,
        "opt": opt_level,
        "cmd": ["(cached)", binary_path],
        "cwd": cwd,
        "rc": 0,
        "stdout": "",
        "stderr": "",
        "wall_s": 0.0,
        "peak_ws_bytes": 0,
        "peak_commit_bytes": 0,
        "peak_ws_mb": 0.0,
        "peak_commit_mb": 0.0,
        "peak_mb": 0.0,
        "passes": [],
        "output": binary_path,
        "size_bytes": os.path.getsize(binary_path),
        "sha256": sha256_file(binary_path),
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


def run_stage2_and_stage3_for_opt(
    opt_level,
    axiomc1,
    bundle_bytes,
    std_root,
    stack_reserve,
    base_dir,
    max_stage,
    time_passes,
    env,
    reuse_existing=False,
    src_mtime=0.0,
):
    """Run Stage-2 in dir_stage2_<opt> and (if max_stage >= 3) Stage-3 in dir_stage3_<opt>.

    Stage-2 and Stage-3 always execute in two distinct directories (`dir_stage2 != dir_stage3`)
    with identical flags (INV-DET-004, SPEC-00 MS-P10b, SPEC-20 §6.3).
    """
    dir_s2 = os.path.abspath(os.path.join(base_dir, "dir_stage2_%s" % opt_level))
    dir_s3 = os.path.abspath(os.path.join(base_dir, "dir_stage3_%s" % opt_level))
    if dir_s2 == dir_s3:
        raise RuntimeError("stage2 and stage3 directories must be distinct")
    os.makedirs(dir_s2, exist_ok=True)
    os.makedirs(dir_s3, exist_ok=True)

    bundle_s2 = os.path.join(dir_s2, "axiomc_bundle.ax")
    bundle_s3 = os.path.join(dir_s3, "axiomc_bundle.ax")
    with open(bundle_s2, "wb") as f:
        f.write(bundle_bytes)
    with open(bundle_s3, "wb") as f:
        f.write(bundle_bytes)

    s2_out_in_dir = os.path.join(dir_s2, "axiomc2.exe")
    s3_out_in_dir = os.path.join(dir_s3, "axiomc3.exe")
    top_s2_opt = os.path.join(base_dir, "axiomc2_%s.exe" % opt_level)
    top_s3_opt = os.path.join(base_dir, "axiomc3_%s.exe" % opt_level)
    top_s2_default = os.path.join(base_dir, "axiomc2.exe")
    top_s3_default = os.path.join(base_dir, "axiomc3.exe")

    results = []

    # Check if we can reuse an up-to-date Stage-2 binary
    reused_s2 = None
    if reuse_existing:
        for cand in (s2_out_in_dir, top_s2_opt, top_s2_default if opt_level == "O1" else ""):
            if cand and os.path.isfile(cand):
                try:
                    if os.path.getmtime(cand) >= src_mtime and os.path.getsize(cand) > 0:
                        reused_s2 = cand
                        break
                except OSError:
                    pass

    if reused_s2 is not None:
        if os.path.abspath(reused_s2) != os.path.abspath(s2_out_in_dir):
            shutil.copy2(reused_s2, s2_out_in_dir)
        r2 = make_cached_result("stage2_axiomc1_to_axiomc2_%s" % opt_level, opt_level, s2_out_in_dir, dir_s2)
    else:
        r2 = run_stage_build(
            "stage2_axiomc1_to_axiomc2_%s" % opt_level,
            axiomc1,
            bundle_s2,
            s2_out_in_dir,
            std_root,
            stack_reserve,
            opt_level,
            time_passes,
            dir_s2,
            env,
        )
    results.append(r2)
    if r2["rc"] != 0 or not os.path.isfile(s2_out_in_dir):
        print(
            "bootstrap: FAIL stage2 (%s, axiomc1 -> axiomc2) rc=%d\n%s"
            % (opt_level, r2["rc"], r2["stderr"][:2000]),
            file=sys.stderr,
        )
        return False, results

    shutil.copy2(s2_out_in_dir, top_s2_opt)
    if opt_level == "O1":
        shutil.copy2(s2_out_in_dir, top_s2_default)
        shutil.copy2(s2_out_in_dir, os.path.join(base_dir, "axiomc.exe"))

    print(
        "STAGE2 (%s) OK: %s [dir=%s] (%d bytes, sha256=%s, wall=%.2fs, peak_ws=%.1fMB, peak_commit=%.1fMB)"
        % (
            opt_level,
            s2_out_in_dir,
            dir_s2,
            r2["size_bytes"],
            r2["sha256"][:16],
            r2["wall_s"],
            r2["peak_ws_mb"],
            r2["peak_commit_mb"],
        )
    )

    if max_stage >= 3:
        reused_s3 = None
        if reuse_existing:
            for cand in (s3_out_in_dir, top_s3_opt, top_s3_default if opt_level == "O1" else ""):
                if cand and os.path.isfile(cand):
                    try:
                        if os.path.getmtime(cand) >= src_mtime and os.path.getsize(cand) > 0:
                            reused_s3 = cand
                            break
                    except OSError:
                        pass

        if reused_s3 is not None:
            if os.path.abspath(reused_s3) != os.path.abspath(s3_out_in_dir):
                shutil.copy2(reused_s3, s3_out_in_dir)
            r3 = make_cached_result("stage3_axiomc2_to_axiomc3_%s" % opt_level, opt_level, s3_out_in_dir, dir_s3)
        else:
            r3 = run_stage_build(
                "stage3_axiomc2_to_axiomc3_%s" % opt_level,
                s2_out_in_dir,
                bundle_s3,
                s3_out_in_dir,
                std_root,
                stack_reserve,
                opt_level,
                time_passes,
                dir_s3,
                env,
            )
        results.append(r3)
        if r3["rc"] != 0 or not os.path.isfile(s3_out_in_dir):
            print(
                "bootstrap: FAIL stage3 (%s, axiomc2 -> axiomc3) rc=%d\n%s"
                % (opt_level, r3["rc"], r3["stderr"][:2000]),
                file=sys.stderr,
            )
            return False, results

        shutil.copy2(s3_out_in_dir, top_s3_opt)
        if opt_level == "O1":
            shutil.copy2(s3_out_in_dir, top_s3_default)

        print(
            "STAGE3 (%s) OK: %s [dir=%s] (%d bytes, sha256=%s, wall=%.2fs, peak_ws=%.1fMB, peak_commit=%.1fMB)"
            % (
                opt_level,
                s3_out_in_dir,
                dir_s3,
                r3["size_bytes"],
                r3["sha256"][:16],
                r3["wall_s"],
                r3["peak_ws_mb"],
                r3["peak_commit_mb"],
            )
        )
        if r2["sha256"] != r3["sha256"] or not files_byte_identical(s2_out_in_dir, s3_out_in_dir):
            print(
                "bootstrap: FAIL fixed-point mismatch (%s): sha256(axiomc2)=%s != sha256(axiomc3)=%s"
                % (opt_level, r2["sha256"], r3["sha256"]),
                file=sys.stderr,
            )
            return False, results
        print(
            "FIXED-POINT (%s) OK: sha256(axiomc2_%s) == sha256(axiomc3_%s) == %s (%d bytes, built in %s and %s)"
            % (opt_level, opt_level, opt_level, r3["sha256"], r3["size_bytes"], dir_s2, dir_s3)
        )

    return True, results


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
    ap.add_argument("--stage", type=int, choices=(1, 2, 3), default=None, help="Highest bootstrap stage to build (1, 2, or 3)")
    ap.add_argument("--opt", choices=("default", "O0", "O1"), default="default", help="Optimization flag for Stage-1 build")
    ap.add_argument(
        "--stage2-opt",
        choices=("default", "O0", "O1", "both"),
        default="O1",
        help="Optimization flag for Stage-2/3 self-compile (O0, O1, or both)",
    )
    ap.add_argument(
        "--check-both-opt",
        "--verify-fixed-point",
        dest="check_both_opt",
        action="store_true",
        help="Verify Stage-2 == Stage-3 fixed point in distinct directories at both -O0 and -O1",
    )
    ap.add_argument(
        "--reuse-existing",
        action="store_true",
        help="Reuse existing stage binaries when they are newer than compiler/ and std/ sources",
    )
    ap.add_argument("--time-passes", action="store_true", help="Pass --time-passes and report per-pass timings")
    ap.add_argument("--perf-csv", default=None, help="Write self-host timing and memory CSV to this path")
    ap.add_argument("--check-budget", action="store_true", help="Enforce SPEC-20 §6.2 wall-time and RAM budgets")
    args = ap.parse_args(argv)

    if args.check_both_opt:
        max_stage = 3
        opt_levels = ["O1", "O0"]
    else:
        if args.stage is not None:
            max_stage = args.stage
        elif args.out is not None:
            max_stage = 1
        else:
            max_stage = 3
        if args.stage2_opt == "both":
            opt_levels = ["O1", "O0"]
        elif args.stage2_opt == "default":
            opt_levels = ["O0"]
        else:
            opt_levels = [args.stage2_opt]

    root = os.path.abspath(args.root)
    stage0 = os.path.abspath(args.stage0) if args.stage0 else find_default_stage0(root)
    if not os.path.isfile(stage0):
        print("bootstrap: error: stage0 compiler not found at %s" % stage0, file=sys.stderr)
        return 2

    build_dir = os.path.abspath(args.build_dir) if args.build_dir else (
        os.path.dirname(os.path.abspath(args.out)) if args.out else os.path.dirname(stage0)
    )
    os.makedirs(build_dir, exist_ok=True)

    std_root = os.path.abspath(args.std_root) if args.std_root else os.path.join(root, "std")
    if not os.path.isdir(std_root):
        print("bootstrap: error: std root not found at %s" % std_root, file=sys.stderr)
        return 2

    env = clean_bootstrap_env()
    ok_env, bad_tool = verify_no_external_tools_on_path(env)
    if not ok_env:
        print("bootstrap: error: external tool still on PATH: %s" % bad_tool, file=sys.stderr)
        return 1

    axiomc1 = os.path.abspath(args.out) if args.out else os.path.join(build_dir, "axiomc1.exe")
    base_dir = os.path.dirname(axiomc1)
    src_mtime = latest_source_mtime(root)

    bundle_text = load_bundle_text(root)
    bundle_bytes = bundle_text.encode("utf-8")
    tmp_ctx = None
    if args.bundle_out:
        bundle_path = os.path.abspath(args.bundle_out)
        os.makedirs(os.path.dirname(bundle_path), exist_ok=True)
    else:
        tmp_ctx = tempfile.TemporaryDirectory(prefix="axiom_bootstrap_")
        bundle_path = os.path.join(tmp_ctx.name, "axiomc_bundle.ax")

    try:
        with open(bundle_path, "wb") as f:
            f.write(bundle_bytes)

        stage_results = []

        # Stage 1: axiom0 -> axiomc1
        can_reuse_s1 = (
            args.reuse_existing
            and os.path.isfile(axiomc1)
            and os.path.getsize(axiomc1) > 0
            and os.path.getmtime(axiomc1) >= src_mtime
        )
        if can_reuse_s1:
            r1 = make_cached_result("stage1_axiom0_to_axiomc1", args.opt, axiomc1, root)
        else:
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

        # Stage 2 & Stage 3 across requested optimization levels
        if max_stage >= 2:
            for opt_lvl in opt_levels:
                ok_opt, opt_results = run_stage2_and_stage3_for_opt(
                    opt_lvl,
                    axiomc1,
                    bundle_bytes,
                    std_root,
                    args.stack_reserve,
                    base_dir,
                    max_stage,
                    args.time_passes or bool(args.perf_csv),
                    env,
                    reuse_existing=args.reuse_existing,
                    src_mtime=src_mtime,
                )
                stage_results.extend(opt_results)
                if not ok_opt:
                    return 1

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
            for res in stage_results[1:]:
                if res["wall_s"] >= STAGE2_MAX_WALL_S:
                    print(
                        "bootstrap: FAIL %s wall time %.2fs exceeds budget %.2fs"
                        % (res["stage"], res["wall_s"], STAGE2_MAX_WALL_S),
                        file=sys.stderr,
                    )
                    return 1
                if res["peak_ws_mb"] >= STAGE2_MAX_PEAK_MB:
                    print(
                        "bootstrap: FAIL %s peak memory %.1fMB exceeds budget %.1fMB"
                        % (res["stage"], res["peak_ws_mb"], STAGE2_MAX_PEAK_MB),
                        file=sys.stderr,
                    )
                    return 1

        return 0
    finally:
        if tmp_ctx is not None:
            tmp_ctx.cleanup()


if __name__ == "__main__":
    sys.exit(main())
