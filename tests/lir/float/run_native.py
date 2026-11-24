#!/usr/bin/env python3
"""T459: build `<case>.ax` natively at -O0 and -O1, run it and compare stdout byte-for-byte with
`<case>.txt` (Python IEEE-754 oracle, see gen_float_cases.py). Also checks that the committed
cases are current (`gen_float_cases.py --check`).

Usage (exec manifest): run_native.py <compiler> <root> <tmp> <case>
Prints `NATIVE-FLOAT PASS <case> <lines>` on success.

The MIR interpreter gains f32/f64 in T458; until then these programs are native-only and the oracle is
the Python reference, not the interpreter.
"""

import os
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    if len(sys.argv) < 5:
        print("usage: run_native.py <compiler> <root> <tmp> <case>", file=sys.stderr)
        return 2
    compiler, root, tmp, case = (os.path.abspath(sys.argv[1]), os.path.abspath(sys.argv[2]),
                                 os.path.abspath(sys.argv[3]), sys.argv[4])
    r = subprocess.run([sys.executable, os.path.join(HERE, "gen_float_cases.py"), "--check"], capture_output=True)
    if r.returncode != 0:
        print(r.stdout.decode("utf-8", "replace"))
        return 1
    os.makedirs(tmp, exist_ok=True)
    work = tempfile.mkdtemp(prefix="flt_" + case + "_", dir=tmp)
    src = os.path.join(HERE, case + ".ax")
    with open(os.path.join(HERE, case + ".txt"), "rb") as f:
        want = f.read()
    std_root = os.path.join(root, "std")
    for opt in ("-O0", "-O1"):
        exe = os.path.join(work, case + opt + ".exe")
        r = subprocess.run([compiler, "build", opt, "--std-root", std_root, src, "-o", exe], capture_output=True)
        if r.returncode != 0:
            print("build %s failed rc=%d: %s" % (opt, r.returncode, r.stderr.decode("utf-8", "replace")[:3000]))
            return 1
        r = subprocess.run([exe], capture_output=True, timeout=60)
        got = r.stdout.replace(b"\r\n", b"\n")
        if r.returncode != 0 or got != want:
            gl = got.decode("utf-8", "replace").split("\n")
            wl = want.decode("utf-8", "replace").split("\n")
            bad = [i for i in range(max(len(gl), len(wl))) if (gl[i] if i < len(gl) else None) != (wl[i] if i < len(wl) else None)]
            print("native %s %s: rc=%d, %d differing line(s)" % (case, opt, r.returncode, len(bad)))
            for i in bad[:20]:
                print("  line %d: got %r want %r" % (i + 1, gl[i] if i < len(gl) else None, wl[i] if i < len(wl) else None))
            return 1
    print("NATIVE-FLOAT PASS %s %d" % (case, want.count(b"\n")))
    return 0


if __name__ == "__main__":
    sys.exit(main())
