#!/usr/bin/env python3
"""T459: C <-> Axiom oracle for the Windows x64 floating-point ABI (SPEC-41 AXS-FLT-041).

Builds xmm_interop.ax as a DLL at -O0 and -O1, builds xmm_interop_host.c with gcc and runs it. gcc's
calling convention is the oracle for argument/return placement in both directions, and the host checks
that all 128 bits of XMM6..XMM15 survive every call into Axiom code (a control thunk that clobbers XMM6
first proves that the check detects a violation).

Usage (exec manifest): xmm_interop_oracle.py <compiler> <root> <tmp>
"""

import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    compiler, root, tmp = (os.path.abspath(a) for a in sys.argv[1:4])
    gcc = shutil.which("gcc") or shutil.which("gcc", path="C:\\msys64\\ucrt64\\bin")
    if not gcc:
        print("gcc not found (it is the oracle of this test)")
        return 1
    os.makedirs(tmp, exist_ok=True)
    work = tempfile.mkdtemp(prefix="xmmabi_", dir=tmp)
    env = dict(os.environ)
    env["PATH"] = os.path.dirname(gcc) + os.pathsep + env.get("PATH", "")
    host = os.path.join(work, "host.exe")
    r = subprocess.run([gcc, "-O1", "-ffp-contract=off", os.path.join(HERE, "xmm_interop_host.c"), "-o", host],
                       capture_output=True, env=env)
    if r.returncode != 0:
        print("gcc failed: " + r.stderr.decode("utf-8", "replace")[:2000])
        return 1
    for opt in ("-O0", "-O1"):
        dll = os.path.join(work, "axflt%s.dll" % opt)
        r = subprocess.run([compiler, "build", opt, "--std-root", os.path.join(root, "std"), "--kind", "dll",
                            "-o", dll, os.path.join(HERE, "xmm_interop.ax")], capture_output=True)
        if r.returncode != 0:
            print("build %s failed: %s" % (opt, r.stderr.decode("utf-8", "replace")[:2000]))
            return 1
        r = subprocess.run([host, dll], capture_output=True, timeout=60, env=env)
        out = r.stdout.decode("utf-8", "replace").replace("\r\n", "\n")
        if r.returncode != 0 or not out.endswith("CONTROL ok\nXMM-INTEROP ok\n"):
            print("%s: rc=%d\n%s" % (opt, r.returncode, out))
            return 1
    print("XMM-INTEROP-ORACLE PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())
