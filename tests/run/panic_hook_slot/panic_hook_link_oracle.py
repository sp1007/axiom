#!/usr/bin/env python3
"""T538 panic hook slot: linker and runtime-object checks.

1. `build --rt-obj` defines `axiom_panic`, `__ax_panic_hook` (in `.data`) and
   `__ax_panic_hook_set`; `objdump -d` decodes it without `(bad)`.
2. A program without fibers/threads links without a `.data` section (the hook slot stays on the
   read-only zero qword in the `axiom_panic` stub) and its panic exits 101 with the message.
3. A program using std.thread gets a writable `.data` slot; a spawned-thread panic is contained (join
   Err) and a user ExitProcess(101) on a spawned thread ends the process with 101.
4. The thread scenario (tests/std/thread/native_panic_hook/nph_exit101_thread.ax) built with `--emit=obj`
   and cross-linked by `gcc -nostdlib` against `axiom_rt.obj` (SPEC-26 INV-WLIB-003) behaves the same.
5. A DLL that spawns a panicking thread contains the panic (join Err) when loaded by a C host.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

THREAD_PROG = """module main

use std.thread.spawn

@intrinsic fn panic(msg: str) {}

@link("kernel32")
extern "system" {
    fn ExitProcess(uExitCode: u32);
}

pub fn main() -> i32 {
    let a = spawn(|| -> i64 {
        panic("oracle worker boom");
        1i64
    });
    let av = match a.join() {
        Result.Ok(x) => x,
        Result.Err(_e) => -1i64,
    };
    print("joined ");
    print_int(av);
    print("\\n");
    let ex = spawn(|| -> i64 {
        unsafe { ExitProcess(101u32); }
        7i64
    });
    let ev = match ex.join() {
        Result.Ok(x) => x,
        Result.Err(_e) => -1i64,
    };
    print("not reached ");
    print_int(ev);
    print("\\n");
    0
}
"""

DLL_PROG = """module d

use std.thread.spawn

@intrinsic fn panic(msg: str) {}

@export
pub extern "C" fn dll_probe() -> i32 {
    let t = spawn(|| -> i64 { panic("oracle dll boom"); 1i64 });
    match t.join() {
        Result.Ok(_x) => 1,
        Result.Err(_e) => 77,
    }
}
"""

DLL_HOST_C = r"""#include <windows.h>
#include <stdio.h>
int main(int argc, char **argv) {
    HMODULE m = LoadLibraryA(argv[1]);
    if (!m) { printf("load %lu\n", GetLastError()); return 2; }
    int (*f)(void) = (int (*)(void))GetProcAddress(m, "dll_probe");
    if (!f) return 3;
    printf("probe=%d", f());
    return 0;
}
"""

PLAIN_PROG = """module main

@intrinsic fn panic(msg: str) {}

pub fn main() -> i32 {
    print("plain\\n");
    panic("oracle plain boom");
    0
}
"""


def fail(msg):
    sys.stderr.write("FAIL: %s\n" % msg)
    return 1


def run(cmd, timeout=60):
    return subprocess.run(cmd, capture_output=True, timeout=timeout)


def section_names(objdump, path):
    out = run([objdump, "-h", str(path)]).stdout.decode("utf-8", "replace")
    names = []
    for line in out.splitlines():
        parts = line.split()
        if len(parts) >= 2 and parts[0].isdigit():
            names.append(parts[1])
    return names


def check_run(exe, want_out, want_rc, label):
    r = run([str(exe)], timeout=30)
    out = r.stdout.decode("utf-8", "replace").replace("\r\n", "\n")
    err = r.stderr.decode("utf-8", "replace")
    if r.returncode != want_rc or out != want_out:
        return "%s: rc=%d stdout=%r (want rc=%d stdout=%r) stderr=%r" % (label, r.returncode, out, want_rc, want_out, err)
    if "panic:" not in err:
        return "%s: panic message missing from stderr: %r" % (label, err)
    return None


def main():
    if len(sys.argv) < 4:
        sys.stderr.write("usage: panic_hook_link_oracle.py <compiler> <tmp_dir> <repo_root>\n")
        return 2
    compiler = os.path.abspath(sys.argv[1])
    tmp = Path(os.path.abspath(sys.argv[2]))
    repo_root = Path(os.path.abspath(sys.argv[3]))
    std_root = repo_root / "std"
    tmp.mkdir(parents=True, exist_ok=True)
    gcc = shutil.which("gcc")
    objdump = shutil.which("objdump")
    if not gcc or not objdump:
        return fail("missing gcc or objdump")

    # 1. Runtime object.
    rt_obj = tmp / "axiom_rt.obj"
    r = run([compiler, "build", "--rt-obj", str(rt_obj)])
    if r.returncode != 0 or not rt_obj.is_file():
        return fail("--rt-obj failed: %r" % r.stderr)
    syms = run([objdump, "-t", str(rt_obj)]).stdout.decode("utf-8", "replace")
    for name in ("axiom_panic", "__ax_panic_hook", "__ax_panic_hook_set"):
        if not any(line.split()[-1:] == [name] and "(sec  0)" not in line for line in syms.splitlines()):
            return fail("axiom_rt.obj does not define %r:\n%s" % (name, syms))
    hook_lines = [l for l in syms.splitlines() if l.split()[-1:] == ["__ax_panic_hook"]]
    if not hook_lines or "(sec  2)" not in hook_lines[0]:
        return fail("__ax_panic_hook is not in .data (section 2): %r" % hook_lines)
    dis = run([objdump, "-d", "-r", str(rt_obj)]).stdout.decode("utf-8", "replace")
    if "(bad)" in dis:
        return fail("objdump -d found (bad) in axiom_rt.obj:\n" + dis)
    if dis.count("__ax_panic_hook") < 2:
        return fail("axiom_rt.obj has no relocations against __ax_panic_hook:\n" + dis)

    # 2. No fibers/threads: no .data section, panic exits 101.
    plain_ax = tmp / "plain.ax"
    plain_ax.write_text(PLAIN_PROG, encoding="utf-8", newline="\n")
    plain_exe = tmp / "plain.exe"
    r = run([compiler, "build", "--std-root", str(std_root), "-o", str(plain_exe), str(plain_ax)])
    if r.returncode != 0:
        return fail("plain build failed: %r" % r.stderr)
    secs = section_names(objdump, plain_exe)
    if ".data" in secs:
        return fail("plain.exe unexpectedly has a .data section: %r" % secs)
    e = check_run(plain_exe, "plain\n", 101, "plain.exe")
    if e:
        return fail(e)

    # 3. Thread program linked by axiomc.
    thr_ax = tmp / "thr.ax"
    thr_ax.write_text(THREAD_PROG, encoding="utf-8", newline="\n")
    thr_exe = tmp / "thr.exe"
    r = run([compiler, "build", "--std-root", str(std_root), "-o", str(thr_exe), str(thr_ax)])
    if r.returncode != 0:
        return fail("thr build failed: %r" % r.stderr)
    if ".data" not in section_names(objdump, thr_exe):
        return fail("thr.exe has no .data section for the hook slot")
    e = check_run(thr_exe, "joined -1\n", 101, "thr.exe")
    if e:
        return fail(e)

    # 4. The same scenario as --emit=obj, cross-linked with gcc/ld against axiom_rt.obj. `--emit=obj`
    #    does not carry the std host-intrinsic bodies (heap, thread spawn), so the program is the
    #    native_panic_hook bundle, which embeds the live std/sys/windows/thread.ax as a user module.
    bundle = repo_root / "tests" / "std" / "thread" / "native_panic_hook" / "nph_exit101_thread.ax"
    thr_obj = tmp / "nph_exit101_thread.obj"
    r = run([compiler, "build", "--std-root", str(std_root), "--emit=obj", "-o", str(thr_obj), str(bundle)], timeout=120)
    if r.returncode != 0:
        return fail("bundle --emit=obj failed: %r" % r.stderr)
    gexe = tmp / "thr_gcc.exe"
    r = run([gcc, "-nostdlib", "-Wl,-e,axiom_start", str(thr_obj), str(rt_obj), "-lkernel32", "-lsynchronization",
             "-o", str(gexe)], timeout=120)
    if r.returncode != 0:
        return fail("gcc cross-link failed: %s" % r.stderr.decode("utf-8", "replace"))
    e = check_run(gexe, "contained -1\n", 101, "thr_gcc.exe")
    if e:
        return fail(e)

    # 5. DLL loaded by a C host.
    dll_ax = tmp / "d.ax"
    dll_ax.write_text(DLL_PROG, encoding="utf-8", newline="\n")
    dll = tmp / "d.dll"
    r = run([compiler, "build", "--std-root", str(std_root), "--kind", "dll", "-o", str(dll), str(dll_ax)])
    if r.returncode != 0:
        return fail("dll build failed: %r" % r.stderr)
    host_c = tmp / "host.c"
    host_c.write_text(DLL_HOST_C, encoding="utf-8", newline="\n")
    host = tmp / "host.exe"
    r = run([gcc, str(host_c), "-o", str(host)])
    if r.returncode != 0:
        return fail("gcc host build failed: %r" % r.stderr)
    r = run([str(host), str(dll)], timeout=30)
    if r.returncode != 0 or r.stdout != b"probe=77" or b"panic:" not in r.stderr:
        return fail("dll host: rc=%d stdout=%r stderr=%r" % (r.returncode, r.stdout, r.stderr))

    sys.stdout.buffer.write(b"PANIC-HOOK-LINK-OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
