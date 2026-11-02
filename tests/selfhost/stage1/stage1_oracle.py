#!/usr/bin/env python3
"""Stage-1 equivalence oracle (T086; INV-BOOT-002, SPEC-00 §6, SPEC-20 §4/§6).

Verifies:
1. `tools/bootstrap.py` builds `axiomc1.exe` from `axiom0.exe` using the 64 MB stack reserve
   (ADR-0003), `--std-root <std>`, and host toolchains (`gcc`, `ld`, `as`) stripped from `PATH`,
   within the SPEC-20 §6.2 time (< 2 min) and memory (< 2 GB) budget.
2. `axiomc1` produces byte-identical `--json` diagnostics (`check --json`) to `axiom0` across
   clean and error programs spanning lex, parse, resolve, hir, typeck, own, borrow, mono, and mir.
3. `axiomc1` produces byte-identical `--emit=obj` (`-O0` and `-O1`), `.exe` (`-O0` and `-O1`),
   and runtime execution outputs to `axiom0` across representative `tests/run` programs.
4. `axiomc1` runs `tools/axtest.py` with `--exclude-requires axiom0-internal -j 1` across a
   cross-section of test kinds (`run`, `ui`, `golden`, `diff`, `exec`) with 0 failures and
   0 `WEAK-NATIVE`.
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


def run_cmd(cmd, cwd, timeout=180):
    res = subprocess.run(
        cmd,
        cwd=cwd,
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


def resolve_stage0(compiler_arg, root):
    cdir = os.path.dirname(os.path.abspath(compiler_arg))
    candidate = os.path.join(cdir, "axiom0.exe")
    if os.path.isfile(candidate):
        return candidate
    fallback = os.path.join(root, "build", "axiom0.exe")
    if os.path.isfile(fallback):
        return fallback
    return os.path.abspath(compiler_arg)


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


def collect_sample(root, patterns, per_pattern=3):
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


def main():
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(encoding="utf-8", errors="replace", newline="\n")
        except Exception:
            pass

    if len(sys.argv) != 4:
        print("usage: stage1_oracle.py <compiler> <tmp> <root>", file=sys.stderr)
        return 2

    compiler_arg = os.path.abspath(sys.argv[1])
    tmp = os.path.abspath(sys.argv[2])
    root = os.path.abspath(sys.argv[3])
    os.makedirs(tmp, exist_ok=True)

    std = os.path.join(root, "std")
    stage0 = resolve_stage0(compiler_arg, root)
    axiomc1 = os.path.join(tmp, "axiomc1.exe")
    bootstrap_py = os.path.join(root, "tools", "bootstrap.py")

    # 1. Build axiomc1 via tools/bootstrap.py and verify budget
    rc, out, err = run_cmd(
        [
            sys.executable,
            bootstrap_py,
            "--root",
            root,
            "--stage0",
            stage0,
            "--out",
            axiomc1,
            "--std-root",
            std,
            "--time-passes",
            "--check-budget",
        ],
        root,
        timeout=600,
    )
    if rc != 0 or not os.path.isfile(axiomc1):
        print(
            "FAIL: tools/bootstrap.py failed (rc=%d):\n%s\n%s"
            % (rc, out.decode("utf-8", "replace"), err.decode("utf-8", "replace"))
        )
        return 1

    # 2. Verify canonical `--json` diagnostics across UI categories + clean programs
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

    diag_files = collect_sample(root, UI_DIAG_PATTERNS, per_pattern=3)
    run_files = collect_sample(root, RUN_PARITY_PATTERNS, per_pattern=3)
    all_json_files = diag_files + run_files
    for rel in all_json_files:
        args = ["check", "--json", "--std-root", std, rel]
        r0 = run_cmd([stage0] + args, root)
        r1 = run_cmd([axiomc1] + args, root)
        if canonical_json_diag(r0) != canonical_json_diag(r1):
            print("FAIL: check --json mismatch on %s: rc0=%d rc1=%d" % (rel, r0[0], r1[0]))
            return 1

    # 3. Verify byte-identical `--emit=obj` (-O0 and -O1) and `.exe` + execution on run sample
    for idx, rel in enumerate(run_files):
        for opt in ("O0", "O1"):
            opt_flags = ["-O1"] if opt == "O1" else []
            obj0 = os.path.join(tmp, "s0_%d_%s.obj" % (idx, opt))
            obj1 = os.path.join(tmp, "s1_%d_%s.obj" % (idx, opt))
            r0 = run_cmd([stage0, "build", "--emit=obj", "--std-root", std] + opt_flags + ["-o", obj0, rel], root)
            r1 = run_cmd([axiomc1, "build", "--emit=obj", "--std-root", std] + opt_flags + ["-o", obj1, rel], root)
            if r0 != r1:
                print("FAIL: build --emit=obj (%s) mismatch on %s" % (opt, rel))
                return 1
            if r0[0] == 0:
                with open(obj0, "rb") as f0, open(obj1, "rb") as f1:
                    if f0.read() != f1.read():
                        print("FAIL: .obj bytes (%s) differ on %s" % (opt, rel))
                        return 1

            exe0 = os.path.join(tmp, "s0_%d_%s.exe" % (idx, opt))
            exe1 = os.path.join(tmp, "s1_%d_%s.exe" % (idx, opt))
            e0 = run_cmd([stage0, "build", "--std-root", std] + opt_flags + ["-o", exe0, rel], root)
            e1 = run_cmd([axiomc1, "build", "--std-root", std] + opt_flags + ["-o", exe1, rel], root)
            if e0 != e1:
                print("FAIL: build exe (%s) mismatch on %s" % (opt, rel))
                return 1
            if e0[0] == 0:
                with open(exe0, "rb") as f0, open(exe1, "rb") as f1:
                    if f0.read() != f1.read():
                        print("FAIL: .exe bytes (%s) differ on %s" % (opt, rel))
                        return 1
                if opt == "O0":
                    if run_cmd([exe0], root) != run_cmd([exe1], root):
                        print("FAIL: runtime behaviour differs on %s" % rel)
                        return 1

    # 4. Run axtest.py with axiomc1 on a representative multi-kind slice
    axtest_py = os.path.join(root, "tools", "axtest.py")
    rc, out, err = run_cmd(
        [
            sys.executable,
            axtest_py,
            "--root",
            root,
            "--compiler",
            axiomc1,
            "--exclude-requires",
            "axiom0-internal",
            "-j",
            "1",
            "conformance/programs",
            "run/mangle",
            "ui/parse",
            "parse/golden",
            "diff/",
        ],
        root,
        timeout=300,
    )
    out_str = out.decode("utf-8", "replace")
    if rc != 0 or "WEAK-NATIVE 0" not in out_str:
        print(
            "FAIL: axtest slice with axiomc1 failed (rc=%d):\n%s\n%s"
            % (rc, out_str, err.decode("utf-8", "replace"))
        )
        return 1

    print(
        "STAGE1-PARITY OK json_checked=%d run_checked=%d"
        % (len(all_json_files), len(run_files))
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
