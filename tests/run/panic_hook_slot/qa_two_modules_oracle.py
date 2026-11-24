#!/usr/bin/env python3
"""T538 QA: the panic hook slot is per module, and the Win64 call contract of the stub.

1. An Axiom EXE and an Axiom DLL, each with its own std fiber/thread runtime: panics on fibers and spawned
   threads are contained in both modules; neither image imports `__ax_panic_hook_set`; a panic raised by
   DLL code on a thread the EXE owns is not contained (the DLL's slot does not know it): exit 101.
2. `axiom_panic` of `--rt-obj` called from C, with a C hook set from another thread: aligned RSP, writable
   32-byte shadow space, clobbered volatile registers, exit 101 after the hook returns; slot 8-aligned.
"""

import os
import shutil
import subprocess
import sys
from pathlib import Path

DLL_AX = """module qad

use std.thread.spawn
use std.fiber.Fiber
use std.fiber.FiberState

@intrinsic fn panic(msg: str) {}

@export
pub extern "C" fn d_fiber() -> i32 {
    let mut f: Fiber<(), i64> = Fiber.new(|| -> i64 { panic("dll fiber"); 1i64 });
    match f.resume() {
        FiberState.Yielded(_u) => 1,
        FiberState.Completed(_r) => 2,
        FiberState.Panicked => 33,
    }
}

@export
pub extern "C" fn d_thread() -> i32 {
    let t = spawn(|| -> i64 { panic("dll thread"); 1i64 });
    match t.join() {
        Result.Ok(_x) => 1,
        Result.Err(_e) => 44,
    }
}

@export
pub extern "C" fn d_panic() -> i32 {
    panic("dll plain");
    1
}
"""

EXE_AX = """module main

use std.thread.spawn
use std.fiber.Fiber
use std.fiber.FiberState

@intrinsic fn panic(msg: str) {}

@link("qad")
extern "C" {
    fn d_fiber() -> i32;
    fn d_thread() -> i32;
    fn d_panic() -> i32;
}

pub fn main() -> i32 {
    let mut f: Fiber<(), i64> = Fiber.new(|| -> i64 { panic("exe fiber"); 1i64 });
    match f.resume() {
        FiberState.Yielded(_u) => { print("yielded\\n"); },
        FiberState.Completed(_r) => { print("completed\\n"); },
        FiberState.Panicked => { print("exe fiber contained\\n"); },
    }
    print_int(unsafe { d_thread() } as i64);
    print("\\n");
    let t = spawn(|| -> i64 { let r = unsafe { d_fiber() }; r as i64 });
    match t.join() {
        Result.Ok(x) => { print_int(x); print("\\n"); },
        Result.Err(_e) => { print("err\\n"); },
    }
    let u = spawn(|| -> i64 { panic("exe thread"); 1i64 });
    match u.join() {
        Result.Ok(_x) => { print("ok\\n"); },
        Result.Err(_e) => { print("exe thread contained\\n"); },
    }
    let v = spawn(|| -> i64 { let r = unsafe { d_panic() }; r as i64 });
    match v.join() {
        Result.Ok(_x) => { print("ok\\n"); },
        Result.Err(_e) => { print("cross-module contained\\n"); },
    }
    print("not reached\\n");
    0
}
"""

RT_C = r"""#include <windows.h>
extern void axiom_panic(const char *, size_t);
extern size_t __ax_panic_hook_set(size_t);
extern size_t __ax_panic_hook;
void __main(void) {}
static void W(const char *s) { DWORD w; WriteFile(GetStdHandle(STD_OUTPUT_HANDLE), s, lstrlenA(s), &w, 0); }
unsigned hook_body(const char *m, size_t n, size_t rsp) {
    DWORD w;
    W((rsp & 15) == 8 ? "aligned " : "MISALIGNED ");
    WriteFile(GetStdHandle(STD_OUTPUT_HANDLE), m, (DWORD)n, &w, 0);
    return 7;
}
__attribute__((naked)) static void hook(void) {
    __asm__ volatile(
        "movq $0x1111111111111111,%rax\n movq %rax,8(%rsp)\n movq %rax,16(%rsp)\n movq %rax,24(%rsp)\n movq %rax,32(%rsp)\n"
        "movq %rsp,%r8\n subq $40,%rsp\n call hook_body\n addq $40,%rsp\n"
        "movq $-1,%rax\n movq %rax,%rcx\n movq %rax,%rdx\n movq %rax,%r8\n movq %rax,%r9\n movq %rax,%r10\n movq %rax,%r11\n ret\n");
}
static DWORD WINAPI setter(void *p) { (void)p; return __ax_panic_hook_set((size_t)hook) == 0 ? 5 : 6; }
int main(void) {
    DWORD rc = 0;
    if (__ax_panic_hook != 0) W("slot not zero\n");
    if (((size_t)&__ax_panic_hook) & 7) W("slot misaligned\n");
    HANDLE h = CreateThread(0, 0, setter, 0, 0, 0);
    WaitForSingleObject(h, INFINITE);
    GetExitCodeThread(h, &rc);
    W(rc == 5 ? "prev zero\n" : "prev bad\n");
    W(__ax_panic_hook == (size_t)hook ? "slot set\n" : "slot bad\n");
    W(__ax_panic_hook_set((size_t)hook) == (size_t)hook ? "prev hook\n" : "prev bad\n");
    axiom_panic("boom\n", 5);
    W("not reached\n");
    return 0;
}
"""


def fail(msg):
    sys.stderr.write("FAIL: %s\n" % msg)
    return 1


def run(cmd, cwd=None, timeout=120):
    return subprocess.run(cmd, cwd=cwd, capture_output=True, timeout=timeout)


def expect(r, rc, out, label):
    got = r.stdout.replace(b"\r\n", b"\n")
    if r.returncode != rc or got != out:
        return "%s: rc=%d stdout=%r stderr=%r (want rc=%d stdout=%r)" % (label, r.returncode, got, r.stderr, rc, out)
    return None


def main():
    if len(sys.argv) < 4:
        sys.stderr.write("usage: qa_two_modules_oracle.py <compiler> <tmp_dir> <repo_root>\n")
        return 2
    compiler = os.path.abspath(sys.argv[1])
    tmp = Path(os.path.abspath(sys.argv[2]))
    std_root = str(Path(os.path.abspath(sys.argv[3])) / "std")
    tmp.mkdir(parents=True, exist_ok=True)
    gcc = shutil.which("gcc")
    objdump = shutil.which("objdump")
    if not gcc or not objdump:
        return fail("missing gcc or objdump")

    (tmp / "qad.ax").write_text(DLL_AX, encoding="utf-8", newline="\n")
    (tmp / "qae.ax").write_text(EXE_AX, encoding="utf-8", newline="\n")
    for opt in ("-O0", "-O1"):
        r = run([compiler, "build", "--std-root", std_root, opt, "--kind", "dll", "-o", "qad.dll", "qad.ax"], cwd=str(tmp))
        if r.returncode != 0:
            return fail("dll build %s: %r" % (opt, r.stderr))
        r = run([compiler, "build", "--std-root", std_root, opt, "-L", ".", "-o", "qae.exe", "qae.ax"], cwd=str(tmp))
        if r.returncode != 0:
            return fail("exe build %s: %r" % (opt, r.stderr))
        for image in ("qad.dll", "qae.exe"):
            dump = run([objdump, "-p", image], cwd=str(tmp)).stdout
            if b"DLL Name" not in dump or b"panic_hook" in dump:
                return fail("%s %s: the setter leaked into the import/export tables" % (image, opt))
        r = run([str(tmp / "qae.exe")], cwd=str(tmp))
        e = expect(r, 101, b"exe fiber contained\n44\n33\nexe thread contained\n", "two modules " + opt)
        if e:
            return fail(e)
        if r.stderr.count(b"panic: explicit panic") != 5:
            return fail("two modules %s: expected 5 panic messages: %r" % (opt, r.stderr))

    (tmp / "rt.c").write_text(RT_C, encoding="utf-8", newline="\n")
    steps = (
        [compiler, "build", "--rt-obj", "axiom_rt.obj"],
        [gcc, "-O2", "-c", "rt.c", "-o", "rtc.o"],
        [gcc, "-nostdlib", "-Wl,-e,axiom_start", "rtc.o", "axiom_rt.obj", "-lkernel32", "-o", "rt.exe"],
    )
    for cmd in steps:
        r = run(cmd, cwd=str(tmp))
        if r.returncode != 0:
            return fail("%r: %r" % (cmd, r.stderr))
    e = expect(run([str(tmp / "rt.exe")]), 101, b"prev zero\nslot set\nprev hook\naligned boom\n", "rt-obj C host")
    if e:
        return fail(e)

    sys.stdout.buffer.write(b"PANIC-HOOK-MODULES-OK\n")
    return 0


if __name__ == "__main__":
    sys.exit(main())
