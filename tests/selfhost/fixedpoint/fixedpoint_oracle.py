#!/usr/bin/env python3
"""Stage-2 / Stage-3 fixed-point and functional equivalence oracle (T087; INV-DET-004, INV-BOOT-003, SPEC-00 §6, SPEC-20 §6).

Verifies:
1. `tools/bootstrap.py --check-both-opt` completes with `gcc`, `ld`, `as`, `clang`, and `link`
   removed from `PATH` (`INV-BOOT-003`, ABOOT-74/75) and `SOURCE_DATE_EPOCH=0`.
2. Fixed point in two distinct directories (`dir_stage2_<opt> != dir_stage3_<opt>`) at BOTH `-O0`
   and `-O1` (`INV-DET-004`):
   - `axiomc2_O0.exe` and `axiomc3_O0.exe` are 100% byte-identical (`sha256` and raw bytes).
   - `axiomc2_O1.exe` and `axiomc3_O1.exe` are 100% byte-identical (`sha256` and raw bytes).
3. `tools/build_axiomc.py --out <build_dir>` succeeds and produces `axiomc2.exe` / `axiomc.exe`.
4. Functional equivalence (`tasks/0262 §42`): `axiomc1` and `axiomc2` (and `axiomc3`) produce
   identical `--json` diagnostics (`check --json`), byte-identical `.obj` and `.exe` binaries
   at `-O0` and `-O1` across distinct working directories, and identical runtime results.
"""

import glob
import json
import os
import subprocess
import sys


UI_DIAG_PATTERNS = [
    "tests/ui/lex/*.ax",
    "tests/ui/parse/*.ax",
    "tests/ui/resolve/*.ax",
    "tests/ui/hir/*.ax",
    "tests/ui/typeck/*.ax",
    "tests/ui/own/*.ax",
    "tests/ui/borrow/*.ax",
    "tests/ui/mono/*.ax",
    "tests/ui/mir/*.ax",
    "tests/ui/driver/*.ax",
]

RUN_PARITY_PATTERNS = [
    "tests/run/numeric/*.ax",
    "tests/run/drop/*.ax",
    "tests/run/mangle/*.ax",
    "tests/run/ptr/*.ax",
    "tests/conformance/*.ax",
]


def run_cmd(cmd, cwd, env=None, timeout=600):
    res = subprocess.run(
        cmd,
        cwd=cwd,
        env=env,
        stdin=subprocess.DEVNULL,
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE,
        timeout=timeout,
    )
    return (
        res.returncode,
        res.stdout.replace(b"\r\n", b"\n"),
        res.stderr.replace(b"\r\n", b"\n"),
    )


def resolve_build_dir_and_stage0(compiler_arg, root, tmp):
    cdir = os.path.dirname(os.path.abspath(compiler_arg))
    cand0 = os.path.join(cdir, "axiom0.exe")
    if os.path.isfile(cand0):
        return cdir, cand0
    # Check build-snap-T087/build or build/
    for sub in ("build-snap-T087/build", "build"):
        bdir = os.path.join(root, *sub.split("/"))
        s0 = os.path.join(bdir, "axiom0.exe")
        if os.path.isfile(s0):
            return bdir, s0
    return tmp, os.path.abspath(compiler_arg)


def is_helper_file(path):
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            for _ in range(10):
                line = f.readline()
                if not line:
                    break
                if line.strip().startswith("// test:") and "helper" in line:
                    return True
    except OSError:
        return True
    return False


def collect_sample(root, patterns, per_pattern=2):
    out = []
    seen = set()
    for pat in patterns:
        matches = [m for m in sorted(glob.glob(os.path.join(root, pat))) if not is_helper_file(m)]
        for m in matches[:per_pattern]:
            rel = os.path.relpath(m, root).replace("\\", "/")
            if rel not in seen:
                seen.add(rel)
                out.append(rel)
    return out


def canonical_json_diag(r):
    rc_val, out_bytes, err_bytes = r
    raw = (err_bytes if err_bytes.strip() else out_bytes).decode("utf-8", "replace").strip()
    if not raw:
        return (rc_val, out_bytes, b"")
    doc = json.loads(raw)
    diags = []
    for d in doc.get("diagnostics", []):
        dc = dict(d)
        dc.pop("id", None)
        diags.append(dc)
    diags.sort(
        key=lambda d: (
            (d.get("primary") or {}).get("start", 0),
            (d.get("primary") or {}).get("end", 0),
            d.get("code", ""),
            d.get("message", ""),
        )
    )
    return (rc_val, out_bytes, doc.get("schema"), doc.get("errors"), doc.get("warnings"), diags)


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace", newline="\n")
        except Exception:
            pass

    if len(sys.argv) != 4:
        print("usage: fixedpoint_oracle.py <compiler> <tmp> <root>", file=sys.stderr)
        return 2

    compiler_arg = os.path.abspath(sys.argv[1])
    tmp = os.path.abspath(sys.argv[2])
    root = os.path.abspath(sys.argv[3])
    os.makedirs(tmp, exist_ok=True)

    tools_dir = os.path.join(root, "tools")
    if tools_dir not in sys.path:
        sys.path.insert(0, tools_dir)
    import bootstrap as b

    std = os.path.join(root, "std")
    build_dir, stage0 = resolve_build_dir_and_stage0(compiler_arg, root, tmp)
    bootstrap_py = os.path.join(root, "tools", "bootstrap.py")
    build_axiomc_py = os.path.join(root, "tools", "build_axiomc.py")

    # 1. Verify clean bootstrap environment strips gcc/ld/as/clang/link
    clean_env = b.clean_bootstrap_env()
    ok_env, bad_tool = b.verify_no_external_tools_on_path(clean_env)
    if not ok_env:
        print("FAIL: clean_bootstrap_env left external tool on PATH: %s" % bad_tool)
        return 1
    if clean_env.get("SOURCE_DATE_EPOCH") != "0":
        print("FAIL: SOURCE_DATE_EPOCH is not '0'")
        return 1

    # 2. Run bootstrap.py --check-both-opt --reuse-existing to verify Stage-2 == Stage-3 at -O0 and -O1
    rc, out, err = run_cmd(
        [
            sys.executable,
            bootstrap_py,
            "--root",
            root,
            "--stage0",
            stage0,
            "--build-dir",
            build_dir,
            "--std-root",
            std,
            "--check-both-opt",
            "--reuse-existing",
        ],
        root,
        timeout=1500,
    )
    out_text = out.decode("utf-8", "replace")
    err_text = err.decode("utf-8", "replace")
    if rc != 0:
        print("FAIL: bootstrap.py --check-both-opt failed (rc=%d):\n%s\n%s" % (rc, out_text, err_text))
        return 1
    if "FIXED-POINT (O1) OK:" not in out_text or "FIXED-POINT (O0) OK:" not in out_text:
        print("FAIL: bootstrap.py output missing FIXED-POINT (O1/O0) OK markers:\n%s" % out_text)
        return 1

    # Verify the two-directory fixed-point artifacts on disk for both O0 and O1
    axiomc1 = os.path.join(build_dir, "axiomc1.exe")
    for opt in ("O0", "O1"):
        dir_s2 = os.path.abspath(os.path.join(build_dir, "dir_stage2_%s" % opt))
        dir_s3 = os.path.abspath(os.path.join(build_dir, "dir_stage3_%s" % opt))
        if dir_s2 == dir_s3:
            print("FAIL: stage2 and stage3 directories are not distinct for %s" % opt)
            return 1
        s2_bin = os.path.join(dir_s2, "axiomc2.exe")
        s3_bin = os.path.join(dir_s3, "axiomc3.exe")
        if not os.path.isfile(s2_bin) or not os.path.isfile(s3_bin):
            print("FAIL: missing stage2/stage3 binaries for %s: %s, %s" % (opt, s2_bin, s3_bin))
            return 1
        if os.path.getsize(s2_bin) < 10_000_000:
            print("FAIL: unexpectedly small binary for %s: %d bytes" % (opt, os.path.getsize(s2_bin)))
            return 1
        h2 = b.sha256_file(s2_bin)
        h3 = b.sha256_file(s3_bin)
        if h2 != h3 or not b.files_byte_identical(s2_bin, s3_bin):
            print("FAIL: byte mismatch for %s: sha256(s2)=%s != sha256(s3)=%s" % (opt, h2, h3))
            return 1

    axiomc2 = os.path.join(build_dir, "axiomc2.exe")
    axiomc3 = os.path.join(build_dir, "axiomc3.exe")

    # 3. Verify `tools/build_axiomc.py --out <build_dir>`
    rc_ba, out_ba, err_ba = run_cmd(
        [sys.executable, build_axiomc_py, "--out", build_dir, "--root", root],
        root,
        timeout=600,
    )
    out_ba_text = out_ba.decode("utf-8", "replace")
    if rc_ba != 0 or "BUILD-AXIOMC OK:" not in out_ba_text:
        print(
            "FAIL: build_axiomc.py failed (rc=%d):\n%s\n%s"
            % (rc_ba, out_ba_text, err_ba.decode("utf-8", "replace"))
        )
        return 1

    # 4. Functional equivalence: axiomc1 vs axiomc2 vs axiomc3 `--json` diagnostics
    diag_files = collect_sample(root, UI_DIAG_PATTERNS, per_pattern=2)
    run_files = collect_sample(root, RUN_PARITY_PATTERNS, per_pattern=2)
    all_json_files = diag_files + run_files
    for rel in all_json_files:
        args = ["check", "--json", "--std-root", std, rel]
        r1 = run_cmd([axiomc1] + args, root, env=clean_env)
        r2 = run_cmd([axiomc2] + args, root, env=clean_env)
        r3 = run_cmd([axiomc3] + args, root, env=clean_env)
        if r1 != r2 or r2 != r3 or canonical_json_diag(r1) != canonical_json_diag(r2):
            print("FAIL: check --json mismatch between axiomc1/axiomc2/axiomc3 on %s" % rel)
            return 1

    # 5. Functional equivalence & two-directory reproducibility on corpus run files at -O0 and -O1
    dir_a = os.path.join(tmp, "work_dir_a")
    dir_b = os.path.join(tmp, "work_dir_b")
    os.makedirs(dir_a, exist_ok=True)
    os.makedirs(dir_b, exist_ok=True)

    for idx, rel in enumerate(run_files):
        src_abs = os.path.join(root, *rel.split("/"))
        for opt in ("O0", "O1"):
            opt_flags = ["-O1"] if opt == "O1" else ["-O0"]
            obj1 = os.path.join(dir_a, "p_%d_%s.obj" % (idx, opt))
            obj2 = os.path.join(dir_b, "p_%d_%s.obj" % (idx, opt))
            r1 = run_cmd(
                [axiomc1, "build", "--emit=obj", "--std-root", std] + opt_flags + ["-o", obj1, src_abs],
                dir_a,
                env=clean_env,
            )
            r2 = run_cmd(
                [axiomc2, "build", "--emit=obj", "--std-root", std] + opt_flags + ["-o", obj2, src_abs],
                dir_b,
                env=clean_env,
            )
            if r1 != r2 or r1[0] != 0 or not b.files_byte_identical(obj1, obj2):
                print("FAIL: --emit=obj (%s) mismatch between axiomc1 (dir_a) and axiomc2 (dir_b) on %s" % (opt, rel))
                return 1

            exe1 = os.path.join(dir_a, "p_%d_%s.exe" % (idx, opt))
            exe2 = os.path.join(dir_b, "p_%d_%s.exe" % (idx, opt))
            e1 = run_cmd(
                [axiomc1, "build", "--std-root", std] + opt_flags + ["-o", exe1, src_abs],
                dir_a,
                env=clean_env,
            )
            e2 = run_cmd(
                [axiomc2, "build", "--std-root", std] + opt_flags + ["-o", exe2, src_abs],
                dir_b,
                env=clean_env,
            )
            if e1 != e2 or e1[0] != 0 or not b.files_byte_identical(exe1, exe2):
                print("FAIL: .exe (%s) mismatch between axiomc1 (dir_a) and axiomc2 (dir_b) on %s" % (opt, rel))
                return 1

            if opt == "O1":
                run1 = run_cmd([exe1], dir_a, env=clean_env)
                run2 = run_cmd([exe2], dir_b, env=clean_env)
                if run1 != run2:
                    print("FAIL: runtime execution mismatch on %s" % rel)
                    return 1

    print(
        "FIXEDPOINT-PARITY OK sha256_O1=%s sha256_O0=%s json_checked=%d run_checked=%d"
        % (
            b.sha256_file(os.path.join(build_dir, "dir_stage3_O1", "axiomc3.exe")),
            b.sha256_file(os.path.join(build_dir, "dir_stage3_O0", "axiomc3.exe")),
            len(all_json_files),
            len(run_files),
        )
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
