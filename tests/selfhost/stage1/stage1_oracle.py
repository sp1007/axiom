#!/usr/bin/env python3
"""Stage-1 equivalence oracle (T086 / T436; INV-BOOT-002, SPEC-00 §6, SPEC-20 §4/§6/§7).

Verifies:
1. `tools/bootstrap.py` builds (or validates a current pre-built) `axiomc1.exe` from `axiom0.exe`
   using the 64 MB stack reserve (ADR-0003), `--std-root <std>`, and host toolchains (`gcc`, `ld`,
   `as`) stripped from `PATH`.
2. `axiomc1` (and `{compiler}`) produce canonical-identical `--json` diagnostics (`check --json`)
   to `axiom0` across clean and error programs spanning lex, parse, resolve, hir, typeck, own,
   borrow, mono, mir, and driver.
3. `axiomc1` and `axiom0` both compile representative `tests/run` programs (`-O0` and `-O1`) with
   identical exit codes and runtime execution outputs, and `axiomc1` produces byte-identical
   `--emit=obj` (`-O0` and `-O1`) and `.exe` (`-O0` and `-O1`) artifacts to `{compiler}` (`axiomc2`).
4. `tools/axtest.py` passes with `--exclude-requires axiom0-internal --no-cache -j 2` and
   `0 WEAK-NATIVE` across `axiomc1` and `{compiler}` (`axiomc2`) multi-kind test slices.

Any failure prints the failing step identifier and a detailed diff/diagnostic to both `stderr` and
`stdout` before exiting non-zero.
"""

import difflib
import glob
import json
import os
import shutil
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


def fail_step(step, message, detail=""):
    body = "FAIL [%s]: %s" % (step, message)
    if detail:
        body = body + "\n" + detail.rstrip("\n")
    print(body, file=sys.stderr, flush=True)
    print(body, file=sys.stdout, flush=True)
    return 1


def format_text_diff(label_a, text_a, label_b, text_b):
    lines = list(
        difflib.unified_diff(
            text_a.splitlines(keepends=True),
            text_b.splitlines(keepends=True),
            fromfile=label_a,
            tofile=label_b,
            n=3,
        )
    )
    return "".join(lines[:80])


def format_bytes_diff(label_a, bytes_a, label_b, bytes_b):
    min_len = min(len(bytes_a), len(bytes_b))
    first_diff = None
    for i in range(min_len):
        if bytes_a[i] != bytes_b[i]:
            first_diff = i
            break
    if first_diff is None and len(bytes_a) != len(bytes_b):
        first_diff = min_len
    msg = "%s len=%d vs %s len=%d" % (label_a, len(bytes_a), label_b, len(bytes_b))
    if first_diff is not None:
        a_slice = bytes_a[first_diff : first_diff + 16].hex()
        b_slice = bytes_b[first_diff : first_diff + 16].hex()
        msg += " (first diff at byte 0x%x: %s=%s vs %s=%s)" % (
            first_diff,
            label_a,
            a_slice,
            label_b,
            b_slice,
        )
    return msg


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


def resolve_prebuilt_stage1(compiler_arg, root):
    cdir = os.path.dirname(os.path.abspath(compiler_arg))
    for cand in (
        os.path.join(cdir, "axiomc1.exe"),
        os.path.join(root, "build", "axiomc1.exe"),
    ):
        if os.path.isfile(cand):
            return cand
    return None


def resolve_stage2(compiler_arg, root, stage0, axiomc1):
    arg_abs = os.path.abspath(compiler_arg)
    if os.path.isfile(arg_abs) and os.path.basename(arg_abs).lower() != "axiom0.exe":
        return arg_abs
    cdir = os.path.dirname(arg_abs)
    for cand in (
        os.path.join(cdir, "axiomc2.exe"),
        os.path.join(root, "build", "axiomc2.exe"),
    ):
        if os.path.isfile(cand):
            return cand
    return axiomc1


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


def canonical_json_diag(r):
    rc_val, out_bytes, err_bytes = r
    raw = (err_bytes if err_bytes.strip() else out_bytes).decode("utf-8", "replace").strip()
    if not raw:
        return (rc_val, out_bytes, 1, 0, 0, [])
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
    return (
        rc_val,
        out_bytes,
        doc.get("schema", 1),
        doc.get("errors", 0),
        doc.get("warnings", 0),
        diags,
    )


def format_canonical_diag(canon):
    rc_val, out_bytes, schema, errors, warnings, diags = canon
    return json.dumps(
        {
            "rc": rc_val,
            "stdout": out_bytes.decode("utf-8", "replace"),
            "schema": schema,
            "errors": errors,
            "warnings": warnings,
            "diagnostics": diags,
        },
        indent=2,
        sort_keys=True,
    )


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

    # 1. Build or validate axiomc1 via tools/bootstrap.py
    prebuilt_c1 = resolve_prebuilt_stage1(compiler_arg, root)
    bootstrap_cmd = [
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
    ]
    if prebuilt_c1 is not None and os.path.getmtime(prebuilt_c1) >= os.path.getmtime(stage0):
        shutil.copy2(prebuilt_c1, axiomc1)
        bootstrap_cmd.append("--reuse-existing")
    else:
        bootstrap_cmd.append("--time-passes")

    rc, out, err = run_cmd(bootstrap_cmd, root, timeout=600)
    if rc != 0 or not os.path.isfile(axiomc1):
        return fail_step(
            "step1:bootstrap",
            "tools/bootstrap.py failed (rc=%d)" % rc,
            "stdout:\n%s\nstderr:\n%s"
            % (out.decode("utf-8", "replace"), err.decode("utf-8", "replace")),
        )

    stage2 = resolve_stage2(compiler_arg, root, stage0, axiomc1)

    # 2. Verify canonical `--json` diagnostics across UI categories + clean programs
    diag_files = collect_sample(root, UI_DIAG_PATTERNS, per_pattern=3)
    run_files = collect_sample(root, RUN_PARITY_PATTERNS, per_pattern=3)
    all_json_files = diag_files + run_files
    for rel in all_json_files:
        args = ["check", "--json", "--std-root", std, rel]
        r0 = run_cmd([stage0] + args, root)
        r1 = run_cmd([axiomc1] + args, root)
        try:
            c0 = canonical_json_diag(r0)
            c1 = canonical_json_diag(r1)
        except Exception as exc:
            return fail_step(
                "step2:check-json",
                "invalid JSON diagnostic output on %s: %s" % (rel, exc),
                "stage0 stderr:\n%s\naxiomc1 stderr:\n%s"
                % (r0[2].decode("utf-8", "replace"), r1[2].decode("utf-8", "replace")),
            )
        if c0 != c1:
            diff_txt = format_text_diff(
                "stage0:" + rel,
                format_canonical_diag(c0) + "\n",
                "axiomc1:" + rel,
                format_canonical_diag(c1) + "\n",
            )
            return fail_step(
                "step2:check-json",
                "check --json mismatch on %s (rc0=%d rc1=%d)" % (rel, r0[0], r1[0]),
                diff_txt,
            )

    # 3. Verify `--emit=obj` and `.exe` build + execution parity on run sample (-O0 and -O1)
    for idx, rel in enumerate(run_files):
        for opt in ("O0", "O1"):
            opt_flags = ["-O1"] if opt == "O1" else []
            obj0 = os.path.join(tmp, "s0_%d_%s.obj" % (idx, opt))
            obj1 = os.path.join(tmp, "s1_%d_%s.obj" % (idx, opt))
            obj2 = os.path.join(tmp, "s2_%d_%s.obj" % (idx, opt))
            r0 = run_cmd([stage0, "build", "--emit=obj", "--std-root", std] + opt_flags + ["-o", obj0, rel], root)
            r1 = run_cmd([axiomc1, "build", "--emit=obj", "--std-root", std] + opt_flags + ["-o", obj1, rel], root)
            r2 = run_cmd([stage2, "build", "--emit=obj", "--std-root", std] + opt_flags + ["-o", obj2, rel], root)
            if r0 != r1 or r1 != r2:
                return fail_step(
                    "step3:build-obj",
                    "build --emit=obj (%s) status/output mismatch on %s (rc0=%d rc1=%d rc2=%d)"
                    % (opt, rel, r0[0], r1[0], r2[0]),
                    "stage0 err: %s\naxiomc1 err: %s\nstage2 err: %s"
                    % (
                        r0[2].decode("utf-8", "replace"),
                        r1[2].decode("utf-8", "replace"),
                        r2[2].decode("utf-8", "replace"),
                    ),
                )
            if r1[0] == 0:
                with open(obj1, "rb") as f1, open(obj2, "rb") as f2:
                    b1, b2 = f1.read(), f2.read()
                    if b1 != b2:
                        return fail_step(
                            "step3:obj-bytes",
                            ".obj bytes (%s) differ between axiomc1 and stage2 on %s" % (opt, rel),
                            format_bytes_diff("axiomc1.obj", b1, "stage2.obj", b2),
                        )

            exe0 = os.path.join(tmp, "s0_%d_%s.exe" % (idx, opt))
            exe1 = os.path.join(tmp, "s1_%d_%s.exe" % (idx, opt))
            exe2 = os.path.join(tmp, "s2_%d_%s.exe" % (idx, opt))
            e0 = run_cmd([stage0, "build", "--std-root", std] + opt_flags + ["-o", exe0, rel], root)
            e1 = run_cmd([axiomc1, "build", "--std-root", std] + opt_flags + ["-o", exe1, rel], root)
            e2 = run_cmd([stage2, "build", "--std-root", std] + opt_flags + ["-o", exe2, rel], root)
            if e0 != e1 or e1 != e2:
                return fail_step(
                    "step3:build-exe",
                    "build exe (%s) status/output mismatch on %s (rc0=%d rc1=%d rc2=%d)"
                    % (opt, rel, e0[0], e1[0], e2[0]),
                    "stage0 err: %s\naxiomc1 err: %s\nstage2 err: %s"
                    % (
                        e0[2].decode("utf-8", "replace"),
                        e1[2].decode("utf-8", "replace"),
                        e2[2].decode("utf-8", "replace"),
                    ),
                )
            if e1[0] == 0:
                with open(exe1, "rb") as f1, open(exe2, "rb") as f2:
                    b1, b2 = f1.read(), f2.read()
                    if b1 != b2:
                        return fail_step(
                            "step3:exe-bytes",
                            ".exe bytes (%s) differ between axiomc1 and stage2 on %s" % (opt, rel),
                            format_bytes_diff("axiomc1.exe", b1, "stage2.exe", b2),
                        )
                run0 = run_cmd([exe0], root)
                run1 = run_cmd([exe1], root)
                if run0 != run1:
                    return fail_step(
                        "step3:runtime-parity",
                        "runtime behaviour (%s) differs between stage0 and axiomc1 on %s (rc0=%d rc1=%d)"
                        % (opt, rel, run0[0], run1[0]),
                        format_text_diff(
                            "stage0.stdout",
                            run0[1].decode("utf-8", "replace"),
                            "axiomc1.stdout",
                            run1[1].decode("utf-8", "replace"),
                        ),
                    )

    # 4. Run axtest.py on representative slices with axiomc1 and stage2
    axtest_py = os.path.join(root, "tools", "axtest.py")
    slices = [
        (
            "axiomc1",
            axiomc1,
            ["run/drop/001.ax", "run/drop/002.ax", "run/drop/003.ax", "ui/parse", "parse/golden"],
        ),
        (
            "stage2",
            stage2,
            ["conformance/programs", "run/mangle", "ui/parse", "parse/golden", "diff/"],
        ),
    ]
    for label, comp_bin, slice_filters in slices:
        rc, out, err = run_cmd(
            [
                sys.executable,
                axtest_py,
                "--root",
                root,
                "--compiler",
                comp_bin,
                "--exclude-requires",
                "axiom0-internal",
                "--no-cache",
                "-j",
                "2",
            ]
            + slice_filters,
            root,
            timeout=300,
        )
        out_str = out.decode("utf-8", "replace")
        err_str = err.decode("utf-8", "replace")
        if rc != 0 or "WEAK-NATIVE 0" not in out_str:
            return fail_step(
                "step4:axtest-%s" % label,
                "axtest slice with %s failed (rc=%d)" % (label, rc),
                "stdout:\n%s\nstderr:\n%s" % (out_str, err_str),
            )

    print(
        "STAGE1-PARITY OK json_checked=%d run_checked=%d"
        % (len(all_json_files), len(run_files))
    )
    return 0


if __name__ == "__main__":
    sys.exit(main())
