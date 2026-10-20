#!/usr/bin/env python3
"""QA boundary cross-check for the integrated `axiomc` (T085 gate).

Usage: python qa_axiomc_cli_edges_oracle.py <axiom0.exe> <tmp-dir> <repo-root>

The end-to-end oracle (axiomc_e2e_oracle.py) compares `build` outputs over programs that compile.
This script covers the seams it does not exercise: command-line edge cases (usage errors, bad option
values, unwritable output, empty / directory / malformed inputs, `check`, `inspect`, `run`), checked
against axiom0 on identical command lines (exit code, stdout, stderr, and the bytes of any artefact).

Every case is either
  same     axiomc and axiom0 must agree exactly, or
  diverge  a documented difference (see NOTE) that must still exist: when it disappears the test fails
           (XPASS) so that the entry is moved to `same`.

The last stdout line is `AXIOMC-EDGES same=<n> diverge=<m>`; exit status 0 only when every case holds.
"""

import os
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, HERE)

import gen_obj_link_driver_tests as gen  # noqa: E402

AXIOMC_STACK_RESERVE = "67108864"
MAIN42 = "tests/mc/frame/main_42.ax"
ARITH = "tests/mc/isel/vs1_arith.ax"
LOCALS = "tests/mc/isel/vs1_locals.ax"

# (name, expectation, argv template). `{out}` expands to <tmp>/<ref|got>, `{in}` to <tmp>/in.
CASES = [
    ("usage-no-command", "same", []),
    ("usage-unknown-command", "same", ["bogus"]),
    ("build-no-input", "same", ["build"]),
    ("build-dangling-o", "same", ["build", "-o"]),
    ("build-unknown-flag", "same", ["build", "--bogus", MAIN42]),
    ("build-bad-stack-reserve", "same", ["build", "--stack-reserve=abc", MAIN42]),
    ("build-bad-emit", "same", ["build", "--emit=bogus", MAIN42]),
    ("build-O2-rejected", "same", ["build", "-O2", "-o", "{out}/o2.exe", ARITH]),
    ("build-stack-reserve-0", "same", ["build", "--stack-reserve=0", "-o", "{out}/s0.exe", MAIN42]),
    ("build-O1-stack-1MB", "same", ["build", "-O1", "--stack-reserve=1048576", "-o", "{out}/k.exe", ARITH]),
    ("build-O1-obj", "same", ["build", "-O1", "--emit=obj", "-o", "{out}/k.obj", LOCALS]),
    ("build-empty-input", "same", ["build", "-o", "{out}/e.exe", "{in}/empty.ax"]),
    ("build-directory-input", "same", ["build", "-o", "{out}/d.exe", "tests/mc"]),
    ("build-missing-input", "same", ["build", "-o", "{out}/m.exe", "tests/does_not_exist_t085.ax"]),
    ("check-ok", "same", ["check", MAIN42]),
    ("check-syntax-error", "same", ["check", "{in}/syn.ax"]),
    ("check-type-error", "same", ["check", "{in}/ty.ax"]),
    ("inspect-tokens-syntax-error", "same", ["inspect", "--emit=tokens", "{in}/syn.ax"]),
    ("inspect-bad-emit", "same", ["inspect", "--emit=nonsense", MAIN42]),
    ("run-interp-exit-code", "same", ["run", "--interp", MAIN42]),
    # NOTE: axiom0 only front-end-checks `run` without --interp (pipeline.c: stage INTERP is skipped, rc 0);
    # axiomc always interprets and returns the program's exit code (42 here).
    ("run-default-mode", "diverge", ["run", MAIN42]),
    # NOTE: axiom0 returns 0 without writing anything when the output directory does not exist
    # (it ignores the write failure); axiomc reports it (exit 1).
    ("build-unwritable-output-dir", "diverge", ["build", "-o", "{out}/nodir/x.exe", MAIN42]),
    # NOTE: after AX_LEX_INVALID_UTF8 errors axiom0 still parses the damaged token stream and prints the
    # cascade of parse errors; axiomc stops after the lexer diagnostics.
    ("check-invalid-utf8", "diverge", ["check", "{in}/garbage.ax"]),
]


def run(cmd, cwd, timeout=120):
    try:
        res = subprocess.run(
            cmd, cwd=cwd, stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=timeout
        )
        return res.returncode, res.stdout, res.stderr
    except subprocess.TimeoutExpired:
        return 124, b"", b"<timeout>"


def norm(data, tmp):
    data = data.replace(b"\r\n", b"\n")
    for form in (tmp, tmp.replace("\\", "/")):
        data = data.replace(form.encode("utf-8"), b"<tmp>")
    for tag in (b"<tmp>/ref", b"<tmp>\\ref", b"<tmp>/got", b"<tmp>\\got"):
        data = data.replace(tag, b"<out>")
    return data


def artefacts(outdir):
    found = {}
    for dirpath, _dirs, files in os.walk(outdir):
        for name in files:
            p = os.path.join(dirpath, name)
            with open(p, "rb") as f:
                found[os.path.relpath(p, outdir).replace("\\", "/")] = f.read()
    return found


def run_case(compiler, argv, tmp, tag, root, std):
    outdir = os.path.join(tmp, tag)
    os.makedirs(outdir, exist_ok=True)
    indir = os.path.join(tmp, "in")
    args = [a.replace("{out}", outdir).replace("{in}", indir) for a in argv]
    if args and args[0] in ("build", "check", "inspect", "run"):
        args = args[:1] + ["--std-root", std] + args[1:]
    code, out, err = run([compiler] + args, root)
    return (code, norm(out, tmp), norm(err, tmp)), artefacts(outdir)


def main():
    if len(sys.argv) < 4:
        print(__doc__)
        return 2
    axiom0 = os.path.abspath(sys.argv[1])
    tmp = os.path.abspath(sys.argv[2])
    root = os.path.abspath(sys.argv[3])
    std = os.path.join(root, "std")
    os.makedirs(os.path.join(tmp, "in"), exist_ok=True)
    inputs = {
        "empty.ax": b"",
        "garbage.ax": b"fn main( -> {{{ \xff\xfe\n",
        "syn.ax": b"fn main( -> {{{\n",
        "ty.ax": b'fn main() -> i32 { let x: i32 = "s"; undefined_fn(); 1 }\n',
    }
    for name, data in inputs.items():
        with open(os.path.join(tmp, "in", name), "wb") as f:
            f.write(data)

    bundle = os.path.join(tmp, "axiomc_bundle.ax")
    with open(bundle, "wb") as f:
        f.write(gen.axiomc_bundle_text().encode("utf-8"))
    axiomc = os.path.join(tmp, "axiomc.exe")
    code, _out, err = run([axiom0, "build", "--stack-reserve=" + AXIOMC_STACK_RESERVE, "-o", axiomc, bundle], root, 1500)
    if code != 0 or not os.path.isfile(axiomc):
        print("FAIL: axiom0 could not build axiomc (rc=%d): %s" % (code, err[:2000].decode("utf-8", "replace")))
        return 1

    failures = []
    same = diverge = 0
    for name, expect, argv in CASES:
        ref = run_case(axiom0, argv, tmp, "ref", root, std)
        got = run_case(axiomc, argv, tmp, "got", root, std)
        for tag in ("ref", "got"):  # fresh output dirs for the next case
            for k in list(artefacts(os.path.join(tmp, tag))):
                os.remove(os.path.join(tmp, tag, k))
        equal = ref == got
        if expect == "same":
            if equal:
                same += 1
            else:
                failures.append("DIFF %s: axiom0=%r axiomc=%r" % (name, ref[0][0], got[0][0]))
                failures.append("     stderr axiom0=%r" % ref[0][2][:300])
                failures.append("     stderr axiomc=%r" % got[0][2][:300])
        else:
            if equal:
                failures.append("XPASS %s now agrees with axiom0: move it to `same`" % name)
            else:
                diverge += 1
    for line in failures:
        print(line)
    if failures:
        print("FAIL %d problems" % len(failures))
    else:
        print("OK")
    print("AXIOMC-EDGES same=%d diverge=%d" % (same, diverge))
    return 1 if failures else 0


if __name__ == "__main__":
    sys.exit(main())
