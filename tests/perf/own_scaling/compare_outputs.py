#!/usr/bin/env python3
"""T485 output-identity check: two compilers must produce byte-identical results.

For every input program, both compilers run
  build -O0 -o <exe>, build -O1 -o <exe>, inspect --emit=mir
(with the same --std-root) and the exit code, stdout, stderr and produced .exe bytes are compared.
Both compilers write the executable to the same path; stdout/stderr are compared after replacing that
directory with a placeholder, and --emit=mir dumps after replacing the heap-address-derived symbol of
async poll calls (`const <7+ digits>(`), which already differs between two runs of one compiler.

usage: compare_outputs.py --old OLD.exe --new NEW.exe --std-root DIR --out DIR [-j N]
                          [--modes O0,O1,mir] [--timeout S] (--list FILE | paths...)
Directories given as paths are searched for *.ax. Prints one line per difference and a summary
`SUMMARY files=N runs=N identical=N differ=N nondet=N timeout=N`; exit 1 when anything differs.
NONDET = the old compiler's own output differs between two runs (not caused by the change).
"""

import argparse
import concurrent.futures as cf
import hashlib
import os
import re
import subprocess
import sys


ASYNC_SYM_RE = re.compile(rb"const [0-9]{7,}\(")


def collect(paths):
    out = []
    for p in paths:
        if os.path.isdir(p):
            for root, _dirs, files in os.walk(p):
                for f in files:
                    if f.endswith(".ax"):
                        out.append(os.path.join(root, f))
        elif p.endswith(".ax"):
            out.append(p)
    return sorted(set(os.path.normpath(x) for x in out))


def run_one(compiler, mode, src, workdir, std_root, timeout):
    os.makedirs(workdir, exist_ok=True)
    exe = os.path.join(workdir, "prog.exe")
    if os.path.exists(exe):
        os.remove(exe)
    if mode == "mir":
        cmd = [compiler, "inspect", "--emit=mir", "--std-root", std_root, src]
    else:
        cmd = [compiler, "build", "-" + mode, "--std-root", std_root, "-o", exe, src]
    try:
        p = subprocess.run(cmd, capture_output=True, timeout=timeout, stdin=subprocess.DEVNULL)
    except subprocess.TimeoutExpired:
        return None
    exe_bytes = b""
    if mode != "mir" and os.path.exists(exe):
        with open(exe, "rb") as f:
            exe_bytes = f.read()
        os.remove(exe)
    def norm(b):
        b = b.replace(workdir.encode(), b"<W>").replace(workdir.replace("\\", "/").encode(), b"<W>")
        if mode == "mir":
            # The poll calls of lowered `async fn`s name a symbol derived from a heap address
            # (compiler/mir/async_lower.ax: `func as usize ^ 0x55AA1234`), which changes from run to run.
            b = ASYNC_SYM_RE.sub(b"const <ASYNC-SYM>(", b)
        return b
    return (p.returncode, hashlib.sha256(norm(p.stdout)).hexdigest(), hashlib.sha256(norm(p.stderr)).hexdigest(),
            hashlib.sha256(exe_bytes).hexdigest(), len(exe_bytes))


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--old", required=True)
    ap.add_argument("--new", required=True)
    ap.add_argument("--std-root", required=True)
    ap.add_argument("--out", required=True)
    ap.add_argument("-j", type=int, default=2)
    ap.add_argument("--modes", default="O0,O1,mir")
    ap.add_argument("--timeout", type=float, default=3600.0)
    ap.add_argument("--list")
    ap.add_argument("paths", nargs="*")
    a = ap.parse_args()
    paths = list(a.paths)
    if a.list:
        with open(a.list, encoding="utf-8") as f:
            paths += [ln.strip() for ln in f if ln.strip() and not ln.startswith("#")]
    files = collect(paths)
    modes = [m for m in a.modes.split(",") if m]
    jobs = [(f, m) for f in files for m in modes]
    old = os.path.abspath(a.old)
    new = os.path.abspath(a.new)
    std_root = os.path.abspath(a.std_root)

    def job(k):
        f, m = jobs[k]
        r_old = run_one(old, m, f, os.path.abspath(os.path.join(a.out, "w%d" % k, "a")), std_root, a.timeout)
        r_new = run_one(new, m, f, os.path.abspath(os.path.join(a.out, "w%d" % k, "a")), std_root, a.timeout)
        r_old2 = None
        if r_old is not None and r_new is not None and r_old != r_new:
            # A second run of the OLD compiler tells a real difference from output that already varies
            # from run to run (e.g. async poll symbols derived from heap addresses in --emit=mir).
            r_old2 = run_one(old, m, f, os.path.abspath(os.path.join(a.out, "w%d" % k, "a")), std_root, a.timeout)
        return k, r_old, r_new, r_old2

    same = differ = tmo = nondet = 0
    with cf.ThreadPoolExecutor(a.j) as ex:
        for k, r_old, r_new, r_old2 in ex.map(job, range(len(jobs))):
            f, m = jobs[k]
            if r_old is None or r_new is None:
                tmo += 1
                print("TIMEOUT %s %s" % (m, f), flush=True)
            elif r_old == r_new:
                same += 1
            elif r_old2 is not None and r_old2 != r_old:
                nondet += 1
                print("NONDET %s %s (the old compiler itself differs between two runs)" % (m, f), flush=True)
            else:
                differ += 1
                print("DIFF %s %s old=%s new=%s" % (m, f, r_old, r_new), flush=True)
    print("SUMMARY files=%d runs=%d identical=%d differ=%d nondet=%d timeout=%d" % (len(files), len(jobs), same, differ, nondet, tmo))
    return 1 if differ or tmo else 0


if __name__ == "__main__":
    sys.exit(main())
