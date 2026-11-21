#!/usr/bin/env python3
"""Standard per-task build driver for the self-hosted Axiom compiler `axiomc` (T087; SPEC-20 §7, ADR-0005 §15).

Usage:
    python tools/build_axiomc.py --out build-snap-<ID>/build

Python 3 standard library only.
1. Ensures `axiom0.exe` exists in `<out>` (building `bootstrap/axiom0` via CMake/Ninja if absent).
2. Invokes `tools/bootstrap.py` with host C/linker toolchains stripped from `PATH` and
   `SOURCE_DATE_EPOCH=0` to build Stage-1 (`axiomc1.exe`) and Stage-2 (`axiomc2.exe`, plus
   `axiomc.exe`) inside `<out>`.
3. Reuses a Stage-0/1/2 binary only when its input manifest `<bin>.inputs.json` matches exactly (T444c, REQ-BLD-028):
   sha256 of every `compiler/**/*.ax` and `std/**/*.ax|toml` source (axiom0: of every file under
   `bootstrap/axiom0`), the bundle text, the producing compiler binary and the stage flags. File mtimes are never
   consulted (a snapshot keeps main-tree mtimes, so an edited file can be older than the binary). Each binary
   prints `REUSED <bin> (inputs <hash16>)` or `REBUILT <bin> (reason)`; pass `--force` to rebuild everything.
4. Seeded fast bootstrap (T487) falls back to the full chain (T423f): when the seed was chosen by `auto` (the default,
   or a literal `--seed auto`) and stage "seeded A" (A = seed(new sources)) fails to compile -- a new host intrinsic or
   new syntax the cached seed does not know -- the same invocation prints
   `bootstrap: seeded A failed, falling back to full chain` and reruns the full `axiom0 -> c1 -> c2 (-> c3)` chain,
   whose result becomes the new cached seed. An explicit `--seed <path>` still fails hard (the caller asked for that
   seed); a failure of any later seeded stage (B, C, B == C, stage-0 smoke parity) is never retried.
"""

import argparse
import os
import shutil
import subprocess
import sys

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))
import bootstrap  # noqa: E402


SEEDED_A_FAIL_MARKER = "bootstrap: FAIL seeded A"
FALLBACK_NOTICE = "bootstrap: seeded A failed, falling back to full chain"


class _StderrTee(object):
    """Forward everything written to stderr unchanged and keep a copy (to recognise the seeded-A failure line)."""

    def __init__(self, inner):
        self.inner = inner
        self.parts = []

    def write(self, text):
        self.parts.append(text)
        return self.inner.write(text)

    def flush(self):
        return self.inner.flush()

    def __getattr__(self, name):
        return getattr(self.inner, name)

    def text(self):
        return "".join(self.parts)


def run_bootstrap(boot_argv, allow_full_chain_fallback):
    """Run `bootstrap.main(boot_argv)`; with `allow_full_chain_fallback`, rerun it as a full chain when it failed
    because the seed could not compile the new sources (stage "seeded A")."""
    if not allow_full_chain_fallback:
        return bootstrap.main(boot_argv)
    real_stderr = sys.stderr
    tee = _StderrTee(real_stderr)
    sys.stderr = tee
    try:
        rc = bootstrap.main(boot_argv)
    finally:
        sys.stderr = real_stderr
    if rc == 0 or SEEDED_A_FAIL_MARKER not in tee.text():
        return rc
    print(FALLBACK_NOTICE, flush=True)
    chain_argv = []
    skip = False
    for tok in boot_argv:
        if skip:
            skip = False
        elif tok == "--seed":
            skip = True
        else:
            chain_argv.append(tok)
    chain_argv.append("--full-chain")
    return bootstrap.main(chain_argv)


def find_cmake_and_ninja_env():
    env = dict(os.environ)
    if shutil.which("cmake", path=env.get("PATH")) is None:
        msys_bin = r"C:\msys64\ucrt64\bin"
        if os.path.isdir(msys_bin):
            env["PATH"] = msys_bin + os.pathsep + env.get("PATH", "")
    return env


def stage0_inputs(src_dir, cc, build_type):
    """Expected-inputs record of `axiom0.exe`: content of every file under `src_dir` (C sources, headers, CMake
    files; build output directories and binaries skipped, see bootstrap.hash_tree) plus cc and build type."""
    files = bootstrap.hash_tree(src_dir, "bootstrap/axiom0")
    return bootstrap.make_inputs("axiom0", files, flags={"cc": cc, "build_type": build_type})


def ensure_stage0(out_dir, root, explicit_stage0=None, cc="clang", build_type="Release"):
    if explicit_stage0:
        p = os.path.abspath(explicit_stage0)
        if not os.path.isfile(p):
            raise RuntimeError("explicit --stage0 binary not found: %s" % p)
        return p

    cand = os.path.join(out_dir, "axiom0.exe" if os.name == "nt" else "axiom0")

    # Check if out_dir is inside a snapshot that has its own bootstrap/axiom0
    snap_root = os.path.dirname(out_dir)
    src_dir = os.path.join(snap_root, "bootstrap", "axiom0")
    if not os.path.isfile(os.path.join(src_dir, "CMakeLists.txt")):
        src_dir = os.path.join(root, "bootstrap", "axiom0")

    expected = stage0_inputs(src_dir, cc, build_type)
    why = bootstrap.reuse_blocker(cand, expected)
    if why is None:
        print("REUSED %s (inputs %s)" % (cand, expected["inputs_hash"][:16]))
        return cand
    # An existing build tree may consider its outputs up to date by mtime although a source changed with an older
    # mtime (snapshot copies keep main-tree mtimes): rebuild from clean so the content change is honoured.
    clean_first = os.path.isfile(cand) or os.path.isfile(os.path.join(out_dir, "build.ninja"))
    bootstrap.drop_manifest(cand)

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

    bld_cmd = ["cmake", "--build", out_dir, "--config", build_type, "--parallel", "2"]
    if clean_first:
        bld_cmd.append("--clean-first")
    r = subprocess.run(bld_cmd, cwd=root, env=env)
    if r.returncode != 0:
        raise RuntimeError("cmake build failed with exit code %d" % r.returncode)

    if not os.path.isfile(cand):
        raise RuntimeError("stage0 binary was not produced at %s" % cand)
    bootstrap.write_manifest(cand, expected)
    print("REBUILT %s (%s)" % (cand, why))
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
    ap.add_argument(
        "--seed",
        default=None,
        help="Seed Stage-2 compiler path for seeded fast bootstrap (A=seed(src), B=A(src), C=B(src), B==C), "
        "or 'auto' (default when not --force/--full-chain/--trust-root) to resolve from --cache-dir (T487); "
        "with 'auto' a seed that cannot compile the new sources falls back to the full chain (T423f), "
        "an explicit path fails hard",
    )
    ap.add_argument(
        "--cache-dir",
        default=None,
        help="Content-addressed Stage-2 compiler cache directory (default: <main_checkout>/_workspaces/artifacts/compiler-cache)",
    )
    ap.add_argument(
        "--full-chain",
        action="store_true",
        help="Force the full axiom0 -> c1 -> c2 (-> c3) chain, disabling seeded mode",
    )
    ap.add_argument(
        "--trust-root",
        action="store_true",
        help="Run the full axiom0 -> c1 -> c2 -> c3 trust-root chain and verify c2 == B byte-identical against the seed",
    )
    ap.add_argument(
        "--no-stage0-smoke",
        action="store_true",
        help="Skip the stage-0 smoke-set .exe byte-parity guard between axiomc1 and seeded B",
    )
    ap.add_argument("--force", action="store_true", help="Rebuild every stage even when the input manifests match")
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
    eff_cache_dir = os.path.abspath(args.cache_dir) if args.cache_dir else bootstrap.default_compiler_cache_dir(effective_root)

    eff_seed = args.seed
    if eff_seed is None and args.stage >= 2 and not args.force and not args.full_chain and not args.trust_root:
        eff_seed = "auto"

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
        "--cache-dir",
        eff_cache_dir,
    ]
    if eff_seed:
        boot_argv.extend(["--seed", eff_seed])
    if args.full_chain:
        boot_argv.append("--full-chain")
    if args.trust_root:
        boot_argv.append("--trust-root")
    if args.no_stage0_smoke:
        boot_argv.append("--no-stage0-smoke")
    if not args.force:
        boot_argv.append("--reuse-existing")
    if args.time_passes:
        boot_argv.append("--time-passes")

    # T423f: only an `auto` seed (the cached one, not a path the caller chose) may fall back to the full chain.
    fallback_ok = eff_seed == "auto" and not args.full_chain and not args.trust_root
    rc = run_bootstrap(boot_argv, fallback_ok)
    if rc != 0:
        return rc

    if args.stage >= 2 and not os.path.isfile(axiomc2):
        axiomc2_o0 = os.path.join(out_dir, "axiomc2_O0.exe")
        if os.path.isfile(axiomc2_o0):
            bootstrap.safe_copy_binary(axiomc2_o0, axiomc2)
            mp_o0 = bootstrap.manifest_path(axiomc2_o0)
            if os.path.isfile(mp_o0):
                shutil.copy2(mp_o0, bootstrap.manifest_path(axiomc2))

    target_bin = axiomc2 if args.stage >= 2 else axiomc1
    if not os.path.isfile(target_bin):
        print("build_axiomc: error: expected binary not found at %s" % target_bin, file=sys.stderr)
        return 1

    if os.path.abspath(target_bin) != os.path.abspath(axiomc):
        bootstrap.safe_copy_binary(target_bin, axiomc)
        target_mp = bootstrap.manifest_path(target_bin)
        if os.path.isfile(target_mp):
            shutil.copy2(target_mp, bootstrap.manifest_path(axiomc))
        else:
            bootstrap.drop_manifest(axiomc)

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
