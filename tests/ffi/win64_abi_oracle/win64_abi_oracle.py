#!/usr/bin/env python3
"""T503: driver of the external Windows x64 ABI oracle (ADR-0034 §8 OI-12).

  win64_abi_oracle.py calls   <compiler> <root> <tmp> [--emit-dir D]
  win64_abi_oracle.py layout  <compiler> <root> <tmp> [--emit-dir D]
  win64_abi_oracle.py control <compiler> <root> <tmp>

`calls`: builds the C side with `gcc -shared` (a missing gcc is a hard failure: gcc is the oracle,
ADR-0034 §7), builds the generated Axiom program (`@link` to that DLL) natively at -O0 and -O1 and runs
it next to the DLL. 1..8 mixed-width scalar arguments, 1..24 byte `@repr(C)` structs by value (in
parameters, returns, callbacks, and after other arguments) are checked in both directions
(Axiom -> C DLL and C DLL -> Axiom `extern "C" fn` callback).
`layout`: gcc prints sizeof/_Alignof/offsetof of every struct; the table is cross-checked against a Python
C-layout algorithm and against the Axiom `@repr(C)` layouts compiled by the compiler under test.
`control`: the same pipeline with deliberately corrupted expectations must be reported as FAIL by the Axiom
executable (proves that the native leg checks something).
"""

import os
import shutil
import subprocess
import sys
import tempfile

HERE = os.path.dirname(os.path.abspath(__file__))
sys.dont_write_bytecode = True
sys.path.insert(0, HERE)
import abi_table as T  # noqa: E402

DLL = "win64_abi_oracle"


def write(path, text):
    with open(path, "w", encoding="utf-8", newline="\n") as f:
        f.write(text)


def find_gcc():
    gcc = shutil.which("gcc") or shutil.which("gcc", path="C:\\msys64\\ucrt64\\bin")
    if not gcc:
        print("gcc not found (it is the oracle of this test; ADR-0034 §7: no skip)")
        sys.exit(1)
    return gcc


def run(cmd, **kw):
    return subprocess.run(cmd, capture_output=True, **kw)


def text(b):
    return b.decode("utf-8", "replace").replace("\r\n", "\n")


def build_ax(compiler, root, opt, src, out):
    r = run([compiler, "build", opt, "--std-root", os.path.join(root, "std"), "-o", out, src])
    if r.returncode != 0:
        return False, "axiom build %s failed (rc=%d): %s%s" % (opt, r.returncode, text(r.stdout)[:1500],
                                                               text(r.stderr)[:3000])
    return True, ""


def emit(args, name, content):
    if args.emit_dir:
        os.makedirs(args.emit_dir, exist_ok=True)
        write(os.path.join(args.emit_dir, name), content)


def stage(work, sub, gcc, c_src, gopt, mutate=()):
    d = os.path.join(work, sub)
    os.makedirs(d)
    csrc = os.path.join(d, DLL + ".c")
    write(csrc, T.c_dll_source(mutate))
    r = run([gcc, gopt, "-shared", "-Wall", "-Werror", csrc, "-o", os.path.join(d, DLL + ".dll")])
    if r.returncode != 0:
        return None, "gcc failed: " + text(r.stderr)[:3000]
    return d, ""


def mode_calls(compiler, root, tmp, args, control=False):
    gcc = find_gcc()
    work = tempfile.mkdtemp(prefix="w64abi_", dir=tmp)
    mutate = ("sc_5_3", "cb_4_2", "si_A12") if control else ()
    csrc = T.c_dll_source(mutate)
    emit(args, DLL + ".c", csrc)
    axsrc, checks = T.ax_program(DLL, mutate)
    emit(args, "abi_calls.ax", axsrc)
    for sub, gopt, opt in (("o0", "-O0", "-O0"), ("o1", "-O2", "-O1")):
        d, err = stage(work, sub, gcc, csrc, gopt, mutate)
        if d is None:
            print(err)
            return 1
        src = os.path.join(d, "abi_calls.ax")
        write(src, axsrc)
        exe = os.path.join(d, "abi_calls.exe")
        ok, err = build_ax(compiler, root, opt, src, exe)
        if not ok:
            print(err)
            return 1
        r = run([exe], cwd=d, timeout=120)
        out = text(r.stdout)
        if control:
            need = ["FAIL sc_5_3", "FAIL cs_4_2", "FAIL si_A12"]
            missing = [n for n in need if n not in out]
            if r.returncode == 0 or missing:
                print("control %s: corrupted expectations were not all detected (rc=%d, missing %s)\n%s"
                      % (opt, r.returncode, missing, out[:2000]))
                return 1
            continue
        want = "WIN64-ABI-CALLS ok %d checks\n" % checks
        if r.returncode != 0 or out != want:
            print("%s: rc=%d\n%s" % (opt, r.returncode, out[:4000]))
            return 1
    print("WIN64-ABI-CONTROL-OK" if control else "WIN64-ABI-CALLS-ORACLE PASS (%d checks x 2 opt levels)" % checks)
    return 0


def parse_table(out):
    table = {}
    for line in out.splitlines():
        p = line.split()
        if not p:
            continue
        table[p[0]] = (int(p[1]), int(p[2]), [int(x) for x in p[3:]])
    return table


def mode_layout(compiler, root, tmp, args, control=False):
    gcc = find_gcc()
    work = tempfile.mkdtemp(prefix="w64lay_", dir=tmp)
    csrc = os.path.join(work, "layout.c")
    write(csrc, T.c_layout_source())
    emit(args, "layout.c", T.c_layout_source())
    r = run([gcc, "-O0", "-Wall", "-Werror", csrc, "-o", os.path.join(work, "layout.exe")])
    if r.returncode != 0:
        print("gcc failed: " + text(r.stderr)[:3000])
        return 1
    r = run([os.path.join(work, "layout.exe")], timeout=60)
    table = parse_table(text(r.stdout))
    for name, _ in T.LAYOUT_STRUCTS:
        if name not in table:
            print("gcc table lacks " + name)
            return 1
        if table[name] != T.py_layout(name):
            print("gcc vs python layout reference differ for %s: gcc=%r python=%r" %
                  (name, table[name], T.py_layout(name)))
            return 1
    mutate = ("L_arr",) if control else ()
    axsrc, checks = T.ax_layout_program(table, mutate)
    emit(args, "layout.ax", axsrc)
    for opt in ("-O0", "-O1"):
        src = os.path.join(work, "layout%s.ax" % opt)
        write(src, axsrc)
        exe = os.path.join(work, "layout%s.exe" % opt)
        ok, err = build_ax(compiler, root, opt, src, exe)
        if not ok:
            print(err)
            return 1
        r = run([exe], timeout=60)
        out = text(r.stdout)
        if control:
            if r.returncode == 0 or "FAIL sizeof L_arr" not in out:
                print("control %s: corrupted size was not detected (rc=%d)\n%s" % (opt, r.returncode, out))
                return 1
            continue
        if r.returncode != 0 or out != "WIN64-LAYOUT ok %d checks\n" % checks:
            print("%s: rc=%d\n%s" % (opt, r.returncode, out[:4000]))
            return 1
    print("WIN64-LAYOUT-CONTROL-OK" if control else
          "WIN64-LAYOUT-ORACLE PASS (%d checks x 2 opt levels, %d structs)" % (checks, len(T.LAYOUT_STRUCTS)))
    return 0


def main():
    a = sys.argv[1:]
    emit_dir = None
    if "--emit-dir" in a:
        i = a.index("--emit-dir")
        emit_dir = a[i + 1]
        del a[i:i + 2]

    class Args(object):
        pass

    args = Args()
    args.emit_dir = emit_dir
    mode = a[0]
    compiler, root, tmp = (os.path.abspath(x) for x in a[1:4])
    os.makedirs(tmp, exist_ok=True)
    if mode == "calls":
        return mode_calls(compiler, root, tmp, args)
    if mode == "layout":
        return mode_layout(compiler, root, tmp, args)
    if mode == "control":
        rc = mode_calls(compiler, root, tmp, args, control=True)
        if rc != 0:
            return rc
        return mode_layout(compiler, root, tmp, args, control=True)
    print("unknown mode " + mode)
    return 2


if __name__ == "__main__":
    sys.exit(main())
