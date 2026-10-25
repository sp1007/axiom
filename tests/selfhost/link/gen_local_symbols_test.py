#!/usr/bin/env python3
"""Generator of tests/selfhost/link/qa_pe_local_symbols.ax (T147, ADR-0035 section 2).

The bundle is built from the REAL `compiler/obj` and `compiler/link` sources (the same module
assembly as the other selfhost generators) and exercises the Axiom PE linker on the hand-written
COFF objects of tests/link/local_symbols (bytes written by gen_local_symbols_obj.py from the PE/COFF
specification, not by either compiler):

  * local_symbols.obj: two STATIC symbols with the same name at different .rdata offsets referenced
    from two functions, plus an EXTERNAL data definition. The linked image is written to disk, run,
    and must exit with the code that proves every reference resolved to its own symbol.
  * local_symbols.obj + dup_ext.obj: a duplicate EXTERNAL definition still fails with
    AX_LINK_DUPLICATE_SYMBOL.

Usage: python tests/selfhost/link/gen_local_symbols_test.py [--check]
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tests", "selfhost"))
sys.path.insert(0, os.path.join(ROOT, "tests", "selfhost", "driver"))
sys.path.insert(0, os.path.join(ROOT, "tests", "link", "local_symbols"))

import bundle_common as bc  # noqa: E402
import gen_driver_tests as drv  # noqa: E402
import gen_local_symbols_obj as lso  # noqa: E402

MODULES = [
    ("compiler.kernel.id", "compiler"),
    ("compiler.kernel.hash", "compiler"),
    ("compiler.kernel.arena", "compiler"),
    ("compiler.kernel.interner", "compiler"),
    ("compiler.source.span", "compiler"),
    ("compiler.source.manager", "compiler"),
    ("compiler.diag.code", "compiler"),
    ("compiler.diag.emitter", "compiler"),
    ("compiler.obj.coff", "compiler"),
    ("compiler.obj.writer", "compiler"),
    ("compiler.obj", "compiler"),
    ("compiler.link.pe", "compiler"),
    ("compiler.link.import", "compiler"),
    ("compiler.link.linker", "compiler"),
    ("compiler.link", "compiler"),
]

MAIN_TEMPLATE = """\
module selfhost_local_symbols_test

use host_intrinsics.heap_alloc
use host_intrinsics.open
use host_intrinsics.write
use host_intrinsics.close
use host_intrinsics.remove
use host_intrinsics.monotonic_ns
use compiler.diag.code.AX_LINK_DUPLICATE_SYMBOL
use compiler.diag.emitter.DiagSink
use compiler.diag.emitter.diag_sink_new
use compiler.diag.emitter.diag_sink_free
use compiler.diag.emitter.diag_sink_has_errors
use compiler.obj.CoffBuf
use compiler.obj.coff_buf_with_capacity
use compiler.obj.coff_buf_free
use compiler.link.linker_diag_code_at
use compiler.link.pe_link_single_coff_to_buf
use compiler.link.pe_link_coff_buffers_to_buf

@link("kernel32")
extern "system" {
    fn CreateProcessW(lpApplicationName: *const u16, lpCommandLine: *mut u16, lpProcessAttributes: *mut u8, lpThreadAttributes: *mut u8, bInheritHandles: i32, dwCreationFlags: u32, lpEnvironment: *mut u8, lpCurrentDirectory: *const u16, lpStartupInfo: *mut u8, lpProcessInformation: *mut u8) -> i32;
    fn WaitForSingleObject(hHandle: *mut u8, dwMilliseconds: u32) -> u32;
    fn GetExitCodeProcess(hProcess: *mut u8, lpExitCode: *mut u32) -> i32;
    fn CloseHandle(hObject: *mut u8) -> i32;
}

@intrinsic unsafe fn address_of_mut<T>(val: T) -> *mut T { 0 as *mut T }

unsafe fn ptr_from_mut<T>(v: mut_view<T>) -> *mut T {
    address_of_mut(*v)
}

@@BLOB_TABLE@@
const BLOB_OFFS: [2]usize = [@@OFFS@@];
const BLOB_LENS: [2]usize = [@@LENS@@];
const EXPECTED_EXIT: u32 = @@EXPECTED@@u32;

// Blob 0: local_symbols.obj, blob 1: dup_ext.obj.
fn blob_copy(idx: usize) -> *mut u8 {
    let off = BLOB_OFFS[idx];
    let blen = BLOB_LENS[idx];
    let buf = unsafe { heap_alloc(blen + 1, 1) };
    let mut i: usize = 0;
    while i < blen {
        unsafe { *(buf + i) = BLOBS[off + i]; }
        i = i + 1;
    }
    buf
}

// Runs `path` (ASCII, NUL-free) and returns its exit code, or 0xFFFFFFFF when it cannot be started.
fn run_image(path: *const u8, plen: usize) -> u32 {
    let wide = unsafe { heap_alloc((plen + 1) * 2, 2) } as *mut u16;
    let mut i: usize = 0;
    while i < plen {
        unsafe { *(wide + i) = (*(path + i)) as u16; }
        i = i + 1;
    }
    unsafe { *(wide + plen) = 0u16; }
    let mut si: [128]u8 = [0u8; 128];
    let mut pi: [32]u8 = [0u8; 32];
    let psi = unsafe { address_of_mut(si[0]) };
    let ppi = unsafe { address_of_mut(pi[0]) };
    unsafe { *(psi as *mut u32) = 104u32; }
    let ok = unsafe { CreateProcessW(wide as *const u16, wide, 0 as *mut u8, 0 as *mut u8, 0, 0u32, 0 as *mut u8, 0 as *const u16, psi, ppi) };
    if ok == 0 {
        return 0xFFFFFFFFu32;
    }
    let h_proc = unsafe { *(ppi as *mut *mut u8) };
    let h_thread = unsafe { *((ppi as usize + 8) as *mut *mut u8) };
    let _ = unsafe { WaitForSingleObject(h_proc, 10000u32) };
    let mut code: [1]u32 = [0xFFFFFFFFu32];
    let _ = unsafe { GetExitCodeProcess(h_proc, address_of_mut(code[0])) };
    let _ = unsafe { CloseHandle(h_proc) };
    let _ = unsafe { CloseHandle(h_thread) };
    code[0]
}

fn test_exit_code() -> i32 {
    let obj = blob_copy(0);
    let mut exe = coff_buf_with_capacity(4096);
    let mut sink = diag_sink_new();
    let sink_ptr = unsafe { ptr_from_mut(mut_view(sink)) };
    let linked = pe_link_single_coff_to_buf(obj as *const u8, BLOB_LENS[0], 1048576u32, mut_view(exe), sink_ptr);
    if !linked || diag_sink_has_errors(view(sink)) {
        coff_buf_free(mut_view(exe));
        diag_sink_free(mut_view(sink));
        return 10;
    }
    // build/tmp_local_symbols_<stamp>.exe
    let pfx: [22]u8 = [98u8, 117u8, 105u8, 108u8, 100u8, 47u8, 116u8, 109u8, 112u8, 95u8, 108u8, 115u8, 121u8, 109u8, 95u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8, 0u8];
    let mut path: [64]u8 = [0u8; 64];
    let mut n: usize = 0;
    while n < 15 {
        path[n] = pfx[n];
        n = n + 1;
    }
    let mut stamp = (monotonic_ns() & 0xFFFFFFu64) as u32;
    let mut digits: [10]u8 = [0u8; 10];
    let mut nd: usize = 0;
    if stamp == 0u32 {
        digits[0] = 48u8;
        nd = 1;
    }
    while stamp > 0u32 {
        digits[nd] = 48u8 + ((stamp % 10u32) as u8);
        stamp = stamp / 10u32;
        nd = nd + 1;
    }
    while nd > 0 {
        nd = nd - 1;
        path[n] = digits[nd];
        n = n + 1;
    }
    path[n] = 46u8;
    path[n + 1] = 101u8;
    path[n + 2] = 120u8;
    path[n + 3] = 101u8;
    n = n + 4;
    let ppath = unsafe { address_of_mut(path[0]) };
    let h = unsafe { open(ppath as *const u8, n, 1u32) };
    if h < 0i64 {
        coff_buf_free(mut_view(exe));
        diag_sink_free(mut_view(sink));
        return 11;
    }
    let wrote = unsafe { write(h, exe.ptr as *const u8, exe.len) };
    let _ = close(h);
    let mut rc = 0;
    if wrote != (exe.len as i64) {
        rc = 12;
    } else {
        let code = run_image(ppath as *const u8, n);
        if code != EXPECTED_EXIT {
            rc = 13;
        }
    }
    let _ = unsafe { remove(ppath as *const u8, n) };
    coff_buf_free(mut_view(exe));
    diag_sink_free(mut_view(sink));
    rc
}

fn test_duplicate_external() -> i32 {
    let a = blob_copy(0);
    let b = blob_copy(1);
    let mut ptrs: [2]*const u8 = [a as *const u8, b as *const u8];
    let mut lens: [2]usize = [BLOB_LENS[0], BLOB_LENS[1]];
    let pptrs = unsafe { address_of_mut(ptrs[0]) };
    let plens = unsafe { address_of_mut(lens[0]) };
    let mut exe = coff_buf_with_capacity(4096);
    let mut sink = diag_sink_new();
    let sink_ptr = unsafe { ptr_from_mut(mut_view(sink)) };
    let linked = pe_link_coff_buffers_to_buf(pptrs as *const *const u8, plens as *const usize, 2, 1048576u32, mut_view(exe), sink_ptr);
    let mut rc = 0;
    if linked {
        rc = 20;
    } else if !diag_sink_has_errors(view(sink)) {
        rc = 21;
    } else if linker_diag_code_at(view(sink), 0) != AX_LINK_DUPLICATE_SYMBOL {
        rc = 22;
    }
    coff_buf_free(mut_view(exe));
    diag_sink_free(mut_view(sink));
    rc
}

pub fn main() -> i32 {
    let r1 = test_exit_code();
    if r1 != 0 { return r1; }
    let r2 = test_duplicate_external();
    if r2 != 0 { return r2; }
    print("OK PE linker local symbols\\n");
    0
}
"""


def build_local_symbols_bundle():
    prelude = bc.build_prelude_text(include_sym_pad=True, sym_pad_count=800, include_std_sys=True, root=ROOT)
    mods = bc.assemble_compiler_modules(MODULES, root=ROOT)
    blobs = [lso.build_local_symbols_obj(), lso.build_dup_ext_obj()]
    blob_bytes, offs, lens = drv.pack_blobs(blobs)
    main_src = (
        MAIN_TEMPLATE
        .replace("@@BLOB_TABLE@@", drv.byte_table("BLOBS", blob_bytes))
        .replace("@@OFFS@@", ", ".join(str(x) for x in offs))
        .replace("@@LENS@@", ", ".join(str(x) for x in lens))
        .replace("@@EXPECTED@@", str(lso.EXPECTED_EXIT_CODE))
    )
    header = (
        "// test: run\n"
        "// timeout: 600\n"
        "// modes: native\n"
        "// This bundle is native only, because it runs the linked image through direct kernel32 FFI (CreateProcessW), which the MIR interpreter cannot call (ADR-0002)\n"
        "// stdout: OK PE linker local symbols\\n\n\n"
    )
    return header + prelude + "\n" + mods + "\n" + main_src


def main(argv=None):
    if argv is None:
        argv = sys.argv[1:]
    check_mode = "--check" in argv or "check" in argv
    out = os.path.join(HERE, "qa_pe_local_symbols.ax")
    text = build_local_symbols_bundle()
    return bc.write_or_check_bundles([(out, text)], check_mode, root=ROOT)


if __name__ == "__main__":
    sys.exit(main())
