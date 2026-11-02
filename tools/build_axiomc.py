#!/usr/bin/env python3
"""Standard per-task build driver for the self-hosted Axiom compiler `axiomc` (T087; SPEC-20 §7, ADR-0005 §15).

Usage:
    python tools/build_axiomc.py --out build-snap-<ID>/build

Python 3 standard library only.
1. Ensures `axiom0.exe` exists in `<out>` (building `bootstrap/axiom0` via CMake/Ninja if absent).
2. Invokes `tools/bootstrap.py` with host C/linker toolchains stripped from `PATH` and
   `SOURCE_DATE_EPOCH=0` to build Stage-1 (`axiomc1.exe`) and Stage-2 (`axiomc2.exe`, plus
   `axiomc.exe`) inside `<out>`.
3. Reuses up-to-date Stage-1/Stage-2 binaries when no `compiler/**/*.ax` or `std/**/*.ax` source
   is newer than `<out>/axiomc2.exe` (pass `--force` to force a full rebuild).
"""

import argparse
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bootstrap  # noqa: E402


def find_cmake_and_ninja_env():
    env = dict(os.environ)
    if shutil.which("cmake", path=env.get("PATH")) is None:
        msys_bin = r"C:\msys64\ucrt64\bin"
        if os.path.isdir(msys_bin):
            env["PATH"] = msys_bin + os.pathsep + env.get("PATH", "")
    return env


def ensure_stage0(out_dir, root, explicit_stage0=None, cc="clang", build_type="Release"):
    if explicit_stage0:
        p = os.path.abspath(explicit_stage0)
        if not os.path.isfile(p):
            raise RuntimeError("explicit --stage0 binary not found: %s" % p)
        return p

    cand = os.path.join(out_dir, "axiom0.exe" if os.name == "nt" else "axiom0")
    if os.path.isfile(cand):
        return cand

    # Check if out_dir is inside a snapshot that has its own bootstrap/axiom0
    snap_root = os.path.dirname(out_dir)
    src_dir = os.path.join(snap_root, "bootstrap", "axiom0")
    if not os.path.isfile(os.path.join(src_dir, "CMakeLists.txt")):
        src_dir = os.path.join(root, "bootstrap", "axiom0")

    env = find_cmake_and_ninja_env()
    os.makedirs(out_dir, exist_ok=True)
    cfg_cmd = [
        "cmake",
        "-S",
        src_dir,
        "-B",
        out_dir,
        "-G",
        "Ninja",
        "-DCMAKE_C_COMPILER=%s" % cc,
        "-DCMAKE_BUILD_TYPE=%s" % build_type,
    ]
    r = subprocess.run(cfg_cmd, cwd=root, env=env)
    if r.returncode != 0:
        raise RuntimeError("cmake configure failed with exit code %d" % r.returncode)

    bld_cmd = ["cmake", "--build", out_dir, "--config", build_type]
    r = subprocess.run(bld_cmd, cwd=root, env=env)
    if r.returncode != 0:
        raise RuntimeError("cmake build failed with exit code %d" % r.returncode)

    if not os.path.isfile(cand):
        raise RuntimeError("stage0 binary was not produced at %s" % cand)
    return cand


def main(argv=None):
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace", newline="\n")
        except Exception:
            pass

    ap = argparse.ArgumentParser(description="Build the Stage-2 self-hosted Axiom compiler (axiomc) into --out <dir>.")
    ap.add_argument("--out", required=True, help="Target build directory (e.g. build-snap-<ID>/build)")
    ap.add_argument("--root", default=ROOT, help="Repository root directory")
    ap.add_argument("--stage0", default=None, help="Optional explicit path to Stage-0 compiler (axiom0.exe)")
    ap.add_argument("--std-root", default=None, help="Optional explicit path to std/ directory")
    ap.add_argument("--stage", type=int, choices=(1, 2, 3), default=2, help="Bootstrap stage to build (default: 2)")
    ap.add_argument("--opt", choices=("O0", "O1", "both"), default="O1", help="Stage-2/3 optimization level (default: O1)")
    ap.add_argument("--force", action="store_true", help="Force full rebuild even if binaries are newer than sources")
    ap.add_argument("--time-passes", action="store_true", help="Report per-pass timings")
    args = ap.parse_args(argv)

    root = os.path.abspath(args.root)
    out_dir = os.path.abspath(args.out)
    os.makedirs(out_dir, exist_ok=True)

    # If out_dir is inside a task snapshot (`build-snap-<ID>/build`) that has its own compiler/ and std/ tree,
    # prefer the snapshot root when `--root` was not explicitly overridden.
    snap_parent = os.path.dirname(out_dir)
    if (
        os.path.abspath(args.root) == os.path.abspath(ROOT)
        and os.path.isdir(os.path.join(snap_parent, "compiler"))
        and os.path.isdir(os.path.join(snap_parent, "std"))
    ):
        effective_root = snap_parent
    else:
        effective_root = root

    try:
        stage0 = ensure_stage0(out_dir, effective_root, explicit_stage0=args.stage0)
    except RuntimeError as exc:
        print("build_axiomc: error: %s" % exc, file=sys.stderr)
        return 1

    std_root = os.path.abspath(args.std_root) if args.std_root else os.path.join(effective_root, "std")
    axiomc1 = os.path.join(out_dir, "axiomc1.exe")
    axiomc2 = os.path.join(out_dir, "axiomc2.exe")
    axiomc = os.path.join(out_dir, "axiomc.exe")

    boot_argv = [
        "--root",
        effective_root,
        "--stage0",
        stage0,
        "--build-dir",
        out_dir,
        "--out",
        axiomc1,
        "--std-root",
        std_root,
        "--stage",
        str(args.stage),
        "--stage2-opt",
        args.opt,
    ]
    if not args.force:
        boot_argv.append("--reuse-existing")
    if args.time_passes:
        boot_argv.append("--time-passes")

    rc = bootstrap.main(boot_argv)
    if rc != 0:
        return rc

    target_bin = axiomc2 if args.stage >= 2 else axiomc1
    if not os.path.isfile(target_bin):
        print("build_axiomc: error: expected binary not found at %s" % target_bin, file=sys.stderr)
        return 1

    if os.path.abspath(target_bin) != os.path.abspath(axiomc):
        shutil.copy2(target_bin, axiomc)

    # Smoke-check the built compiler
    smoke = subprocess.run(
        [target_bin, "version"],
        cwd=effective_root,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
    )
    if smoke.returncode != 0:
        print("build_axiomc: error: '%s version' failed with rc=%d" % (target_bin, smoke.returncode), file=sys.stderr)
        return 1

    sz = os.path.getsize(target_bin)
    digest = bootstrap.sha256_file(target_bin)
    print(
        "BUILD-AXIOMC OK: %s (also %s) size=%d sha256=%s"
        % (target_bin, axiomc, sz, digest)
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
