#!/usr/bin/env python3
"""Selfhost integration test generator for the COFF writer + PE linker + driver group (T085).

It reuses the module assembly of tests/selfhost/driver/gen_driver_tests.py (the compiler.* Axiom
modules are concatenated into one translation unit together with the host-intrinsic prelude, because
the stage-0 test runner compiles one file at a time) and adds the T085 modules
compiler.obj_link_driver and compiler.obj_link_driver.main.

Outputs
  axiomc_bundle_text()        the whole `axiomc` program as one source text; used by
                              axiomc_e2e_oracle.py (exec test axiomc_e2e.test), never committed.
  qa_obj_link_driver_diff.ax  in-process differential bundle (modes: native): the Axiom driver builds
                              a fixed corpus into COFF objects and PE32+ images in memory (-O0, -O1,
                              --stack-reserve) and every byte is compared with axiom0 output captured
                              when the bundle is generated; the object -> linker hand-off
                              (compiler.obj -> compiler.link) is checked against the axiom0 image; a
                              real on-disk build and two diagnostic paths are compared too.
  qa_obj_link_driver_smoke.ax small twin of the above (modes: interp native).

Usage:
  python tests/selfhost/obj_link_driver/gen_obj_link_driver_tests.py [--axiom0 <path/to/axiom0.exe>]
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.join(ROOT, "tests", "selfhost", "driver"))

import gen_driver_tests as drv  # noqa: E402

T085_MODULES = [
    ("compiler.obj_link_driver", "compiler"),
    ("compiler.obj_link_driver.main", "compiler"),
]

# Programs of the in-process differential bundle (relative to the repository root). Every program
# must build deterministically with axiom0 and be byte-identical between axiom0 and the Axiom
# pipeline. Programs with string literals are allowed since T147 (ADR-0035 section 1: object-local
# `.Lstr.<f>.<k>` symbols, resolved by symbol index).
DIFF_CORPUS_FULL = [
    "tests/mc/frame/main_42.ax",
    "tests/mc/isel/vs1_arith.ax",
    "tests/mc/isel/vs1_locals.ax",
    "tests/mc/isel/vs1_return.ax",
    "tests/modules/hello/src/main.ax",
    "tests/modules/nested/src/main.ax",
    "tests/run/parity/strings/fn_literals_plain.ax",
]
DIFF_CORPUS_SMOKE = [
    "tests/mc/frame/main_42.ax",
]


def axiomc_bundle_text():
    """The complete `axiomc` program (prelude + every compiler module + entry point)."""
    mods = drv.assemble_modules(drv.FULL_MODULES + T085_MODULES)
    return drv.build_prelude_text() + "\n" + mods


def reference_build(axiom0, flags, source, out_name):
    """Runs `axiom0 build <flags> -o out <source>` twice; returns the bytes (asserts determinism)."""
    out_path = os.path.join(HERE, out_name)
    results = []
    try:
        for _ in range(2):
            if os.path.exists(out_path):
                os.remove(out_path)
            drv.run_axiom0(axiom0, ["build"] + flags + ["-o", out_path, source], expect_rc=0)
            results.append(drv.read_bytes(out_path))
    finally:
        if os.path.exists(out_path):
            os.remove(out_path)
    if results[0] != results[1]:
        raise SystemExit("axiom0 build of %s %r is not deterministic" % (source, flags))
    return results[0]


MAIN_TEMPLATE = """\
module selfhost_obj_link_driver_test

use host_intrinsics.heap_alloc
use host_intrinsics.file_size
use host_intrinsics.monotonic_ns
use host_intrinsics.open
use host_intrinsics.read
use host_intrinsics.close
use host_intrinsics.remove
use compiler.kernel.interner.StrView
use compiler.diag.format.DiagBuffer
use compiler.diag.format.diag_buf_new
use compiler.diag.format.diag_buf_free
use compiler.diag.format.diag_buf_push_bytes
use compiler.diag.format.diag_buf_push_u32
use compiler.diag.emitter.DiagSink
use compiler.diag.emitter.diag_sink_new
use compiler.diag.emitter.diag_sink_free
use compiler.driver.opts.opts_mul_usize
use compiler.driver.opts.sv_slot_set
use compiler.obj_link_driver.CoffBuf
use compiler.obj_link_driver.coff_buf_with_capacity
use compiler.obj_link_driver.coff_buf_free
use compiler.obj_link_driver.pe_link_single_coff_to_buf
use compiler.obj_link_driver.AX_EXIT_OK
use compiler.obj_link_driver.DriverOptions
use compiler.obj_link_driver.driver_options_alloc
use compiler.obj_link_driver.driver_options_dealloc
use compiler.obj_link_driver.driver_parse_cli
use compiler.obj_link_driver.driver_execute_build_into
use compiler.obj_link_driver.driver_run_args

@intrinsic unsafe fn address_of_mut<T>(val: T) -> *mut T { 0 as *mut T }

unsafe fn ptr_from_mut<T>(v: mut_view<T>) -> *mut T {
    address_of_mut(*v)
}

%(blob_table)s
const BLOB_OFFS: [%(num_blobs)d]usize = [%(offs)s];
const BLOB_LENS: [%(num_blobs)d]usize = [%(lens)s];

// Fixed blobs: 0 "axiom0", 1 "build", 2 "--emit=obj", 3 "-o", 4 "out_mem.obj", 5 "out_mem.exe",
// 6 "-O1", 7 "--stack-reserve=2097152", 8 temp-name prefix, 9 temp-name suffix,
// 10 "tests/nonexistent_t085.ax", 11 expected stderr of the nonexistent-input build,
// 12 expected stderr of `build` without input.  Case k starts at 13 + 6 * k:
// +0 source path, +1 obj -O0, +2 exe -O0, +3 obj -O1, +4 exe -O1, +5 exe -O0 --stack-reserve=2097152.
// LITE (interp twin): one -O0 compile (object bytes), Axiom linker on that object (image bytes), hand-off of
// axiom0's object, diagnostics only. The one-step image build, -O1 and --stack-reserve legs run natively.
const LITE: bool = %(lite)s;
const CASE_COUNT: usize = %(case_count)d;
const CASE_BASE: usize = 13;
const CASE_STRIDE: usize = 6;

fn blob_sv(idx: usize) -> StrView {
    let off = BLOB_OFFS[idx];
    let blen = BLOB_LENS[idx];
    let buf = unsafe { heap_alloc(blen + 1, 1) };
    let mut i: usize = 0;
    while i < blen {
        unsafe { *(buf + i) = BLOBS[off + i]; }
        i = i + 1;
    }
    unsafe { *(buf + blen) = 0u8; }
    StrView {
        ptr: buf as *const u8,
        len: blen,
    }
}

fn alloc_argv(cap: usize) -> *mut StrView {
    let bytes = opts_mul_usize(cap, 16);
    unsafe { heap_alloc(bytes, 8) as *mut StrView }
}

fn set_arg_blob(argv: *mut StrView, idx: usize, blob_idx: usize) {
    let s = blob_sv(blob_idx);
    sv_slot_set(argv, idx, view(s));
}

fn bytes_match_blob(data: *const u8, data_len: usize, blob_idx: usize) -> bool {
    let off = BLOB_OFFS[blob_idx];
    let blen = BLOB_LENS[blob_idx];
    if data_len != blen {
        return false;
    }
    let mut i: usize = 0;
    while i < blen {
        let b = unsafe { *(data + i) };
        if b != BLOBS[off + i] {
            return false;
        }
        i = i + 1;
    }
    true
}

fn coff_buf_matches_blob(cb: view<CoffBuf>, blob_idx: usize) -> bool {
    bytes_match_blob(cb.ptr as *const u8, cb.len, blob_idx)
}

fn case_blob(k: usize, which: usize) -> usize {
    CASE_BASE + CASE_STRIDE * k + which
}

// Runs the driver `build` command through driver_execute_build_into with the artifact captured in
// memory (no file is written). Returns true when the build succeeded and wrote nothing to stderr.
fn build_into_buf(argv: *const StrView, argc: usize, bin: *mut CoffBuf) -> bool {
    let dopts = unsafe { driver_options_alloc() };
    let mut out_b = diag_buf_new();
    let mut err_b = diag_buf_new();
    let prc = unsafe { driver_parse_cli(argv, argc, mut_view(*dopts), mut_view(out_b), mut_view(err_b)) };
    if prc != AX_EXIT_OK {
        diag_buf_free(mut_view(out_b));
        diag_buf_free(mut_view(err_b));
        unsafe { driver_options_dealloc(dopts); }
        return false;
    }
    let brc = unsafe {
        driver_execute_build_into(view(*dopts), mut_view(out_b), mut_view(err_b), bin, false)
    };
    let ok = brc == AX_EXIT_OK && err_b.len == 0;
    diag_buf_free(mut_view(out_b));
    diag_buf_free(mut_view(err_b));
    unsafe { driver_options_dealloc(dopts); }
    ok
}

// `axiomc build [--emit=obj] [-O1] [--stack-reserve=2097152] -o out <source>` against a reference blob.
fn build_matches(k: usize, emit_obj: bool, o1: bool, stack_reserve: bool, expect_blob: usize) -> bool {
    let argv = alloc_argv(8);
    let ap = argv as *const StrView;
    let mut n: usize = 0;
    set_arg_blob(argv, n, 0);
    n = n + 1;
    set_arg_blob(argv, n, 1);
    n = n + 1;
    if emit_obj {
        set_arg_blob(argv, n, 2);
        n = n + 1;
    }
    if o1 {
        set_arg_blob(argv, n, 6);
        n = n + 1;
    }
    if stack_reserve {
        set_arg_blob(argv, n, 7);
        n = n + 1;
    }
    set_arg_blob(argv, n, 3);
    n = n + 1;
    if emit_obj {
        set_arg_blob(argv, n, 4);
    } else {
        set_arg_blob(argv, n, 5);
    }
    n = n + 1;
    set_arg_blob(argv, n, case_blob(k, 0));
    n = n + 1;
    let mut bin_buf = coff_buf_with_capacity(1024);
    let bin_ptr = unsafe { ptr_from_mut(mut_view(bin_buf)) };
    let built = build_into_buf(ap, n, bin_ptr);
    let ok = built && coff_buf_matches_blob(view(bin_buf), expect_blob);
    coff_buf_free(mut_view(bin_buf));
    ok
}

// Object -> linker hand-off: the COFF object bytes of axiom0 (a blob), fed to the Axiom PE linker,
// must give exactly the PE32+ image of axiom0 (a blob).
fn handoff_matches(stack_reserve: bool, exe_blob: usize, obj_blob: usize) -> bool {
    let obj = blob_sv(obj_blob);
    let mut exe = coff_buf_with_capacity(4096);
    let mut sink = diag_sink_new();
    let sink_ptr = unsafe { ptr_from_mut(mut_view(sink)) };
    let reserve: u32 = if stack_reserve { 2097152u32 } else { 1048576u32 };
    let linked = pe_link_single_coff_to_buf(obj.ptr, obj.len, reserve, mut_view(exe), sink_ptr);
    let ok = linked && coff_buf_matches_blob(view(exe), exe_blob);
    coff_buf_free(mut_view(exe));
    diag_sink_free(mut_view(sink));
    ok
}

// Object -> linker hand-off inside the Axiom pipeline: the object the driver emits, linked by the
// Axiom linker, must equal the image the driver builds in one step.
fn pipeline_handoff_matches(k: usize) -> bool {
    let argv = alloc_argv(8);
    let ap = argv as *const StrView;
    set_arg_blob(argv, 0, 0);
    set_arg_blob(argv, 1, 1);
    set_arg_blob(argv, 2, 2);
    set_arg_blob(argv, 3, 3);
    set_arg_blob(argv, 4, 4);
    set_arg_blob(argv, 5, case_blob(k, 0));
    let mut obj = coff_buf_with_capacity(1024);
    let obj_ptr = unsafe { ptr_from_mut(mut_view(obj)) };
    let built = build_into_buf(ap, 6, obj_ptr);
    if !built {
        coff_buf_free(mut_view(obj));
        return false;
    }
    let mut exe = coff_buf_with_capacity(4096);
    let mut sink = diag_sink_new();
    let sink_ptr = unsafe { ptr_from_mut(mut_view(sink)) };
    let linked = pe_link_single_coff_to_buf(obj.ptr as *const u8, obj.len, 1048576u32, mut_view(exe), sink_ptr);
    let ok = linked && coff_buf_matches_blob(view(exe), case_blob(k, 2));
    coff_buf_free(mut_view(obj));
    coff_buf_free(mut_view(exe));
    diag_sink_free(mut_view(sink));
    ok
}

// LITE (interp twin) check with one compile instead of two: the object the driver emits (`--emit=obj`)
// must equal axiom0's object, and that very object, linked by the Axiom linker, must equal axiom0's image.
// Returns 0 on success, 1 when the build fails, 2 when the object bytes differ, 3 when the image differs.
fn pipeline_obj_and_image_status(k: usize) -> i32 {
    let argv = alloc_argv(8);
    let ap = argv as *const StrView;
    set_arg_blob(argv, 0, 0);
    set_arg_blob(argv, 1, 1);
    set_arg_blob(argv, 2, 2);
    set_arg_blob(argv, 3, 3);
    set_arg_blob(argv, 4, 4);
    set_arg_blob(argv, 5, case_blob(k, 0));
    let mut obj = coff_buf_with_capacity(1024);
    let obj_ptr = unsafe { ptr_from_mut(mut_view(obj)) };
    let built = build_into_buf(ap, 6, obj_ptr);
    if !built {
        coff_buf_free(mut_view(obj));
        return 1;
    }
    if !coff_buf_matches_blob(view(obj), case_blob(k, 1)) {
        coff_buf_free(mut_view(obj));
        return 2;
    }
    let mut exe = coff_buf_with_capacity(4096);
    let mut sink = diag_sink_new();
    let sink_ptr = unsafe { ptr_from_mut(mut_view(sink)) };
    let linked = pe_link_single_coff_to_buf(obj.ptr as *const u8, obj.len, 1048576u32, mut_view(exe), sink_ptr);
    let ok = linked && coff_buf_matches_blob(view(exe), case_blob(k, 2));
    coff_buf_free(mut_view(obj));
    coff_buf_free(mut_view(exe));
    diag_sink_free(mut_view(sink));
    if !ok { return 3; }
    0
}

fn read_file_matches_blob(path: view<StrView>, blob_idx: usize) -> bool {
    let fd = unsafe { open(path.ptr, path.len, 0u32) };
    if fd < 0i64 {
        return false;
    }
    let fsz = file_size(fd);
    if fsz < 0i64 {
        let _ = close(fd);
        return false;
    }
    let n = fsz as usize;
    let buf = unsafe { heap_alloc(n + 1, 1) };
    let got = unsafe { read(fd, buf, n) };
    let _ = close(fd);
    got == (n as i64) && bytes_match_blob(buf as *const u8, n, blob_idx)
}

fn test_cases() -> i32 {
    let mut k: usize = 0;
    while k < CASE_COUNT {
        let code = (100 + 10 * k) as i32;
        if LITE {
            // interp twin: one compile (object), then the Axiom linker on that object; the direct
            // one-step image build runs in the native legs (the interpreter runs the whole compiler).
            let st = pipeline_obj_and_image_status(k);
            if st == 1 || st == 2 { return code + 1; }
            if st == 3 { return code + 2; }
            if !handoff_matches(false, case_blob(k, 2), case_blob(k, 1)) { return code + 6; }
        }
        if !LITE {
            if !build_matches(k, true, false, false, case_blob(k, 1)) { return code + 1; }
            if !build_matches(k, false, false, false, case_blob(k, 2)) { return code + 2; }
            if !handoff_matches(false, case_blob(k, 2), case_blob(k, 1)) { return code + 6; }
            if !build_matches(k, true, true, false, case_blob(k, 3)) { return code + 3; }
            if !build_matches(k, false, true, false, case_blob(k, 4)) { return code + 4; }
            if !build_matches(k, false, false, true, case_blob(k, 5)) { return code + 5; }
            if !handoff_matches(true, case_blob(k, 5), case_blob(k, 1)) { return code + 7; }
            if !pipeline_handoff_matches(k) { return code + 8; }
        }
        k = k + 1;
    }
    0
}

fn test_disk_output() -> i32 {
    let argv = alloc_argv(8);
    let ap = argv as *const StrView;
    let mut path_buf = diag_buf_new();
    let pfx = blob_sv(8);
    let sfx = blob_sv(9);
    diag_buf_push_bytes(mut_view(path_buf), pfx.ptr, pfx.len);
    let stamp = (monotonic_ns() & 0xFFFFFFFFu64) as u32;
    diag_buf_push_u32(mut_view(path_buf), stamp);
    diag_buf_push_bytes(mut_view(path_buf), sfx.ptr, sfx.len);
    let tmp_sv = StrView { ptr: path_buf.ptr as *const u8, len: path_buf.len };

    set_arg_blob(argv, 0, 0);
    set_arg_blob(argv, 1, 1);
    set_arg_blob(argv, 2, 3);
    sv_slot_set(argv, 3, view(tmp_sv));
    set_arg_blob(argv, 4, case_blob(0, 0));
    let mut out_d = diag_buf_new();
    let mut err_d = diag_buf_new();
    let drc = driver_run_args(ap, 5, mut_view(out_d), mut_view(err_d));
    let mut ok = drc == AX_EXIT_OK && err_d.len == 0 && out_d.len == 0;
    if ok {
        ok = read_file_matches_blob(view(tmp_sv), case_blob(0, 2));
    }
    let _ = unsafe { remove(tmp_sv.ptr, tmp_sv.len) };
    diag_buf_free(mut_view(out_d));
    diag_buf_free(mut_view(err_d));
    diag_buf_free(mut_view(path_buf));
    if !ok { return 60; }
    0
}

fn test_diagnostics() -> i32 {
    let argv = alloc_argv(8);
    let ap = argv as *const StrView;

    // build -o out_mem.exe tests/nonexistent_t085.ax  -> axiom0's exit code and stderr bytes
    set_arg_blob(argv, 0, 0);
    set_arg_blob(argv, 1, 1);
    set_arg_blob(argv, 2, 3);
    set_arg_blob(argv, 3, 5);
    set_arg_blob(argv, 4, 10);
    let mut out_a = diag_buf_new();
    let mut err_a = diag_buf_new();
    let rca = driver_run_args(ap, 5, mut_view(out_a), mut_view(err_a));
    let oka = rca == %(nonexistent_rc)d && out_a.len == 0 && bytes_match_blob(err_a.ptr as *const u8, err_a.len, 11);
    diag_buf_free(mut_view(out_a));
    diag_buf_free(mut_view(err_a));
    if !oka { return 70; }

    // build  (no input) -> axiom0's exit code and stderr bytes
    set_arg_blob(argv, 0, 0);
    set_arg_blob(argv, 1, 1);
    let mut out_b = diag_buf_new();
    let mut err_b = diag_buf_new();
    let rcb = driver_run_args(ap, 2, mut_view(out_b), mut_view(err_b));
    let okb = rcb == %(noinput_rc)d && out_b.len == 0 && bytes_match_blob(err_b.ptr as *const u8, err_b.len, 12);
    diag_buf_free(mut_view(out_b));
    diag_buf_free(mut_view(err_b));
    if !okb { return 71; }
    0
}

pub fn main() -> i32 {
    let r1 = test_cases();
    if r1 != 0 { return r1; }
    if !LITE {
        let r2 = test_disk_output();
        if r2 != 0 { return r2; }
    }
    let r3 = test_diagnostics();
    if r3 != 0 { return r3; }
    0
}
"""


def gen_diff_bundle(filename, modes, corpus, prelude, full_mods, axiom0, lite=False):
    out_path = os.path.join(HERE, filename)
    if axiom0 is None:
        blobs = drv.bc.extract_blobs_from_bundle(out_path, "BLOBS", "BLOB_OFFS", "BLOB_LENS")
        blob_bytes, offs, lens = drv.pack_blobs(blobs)
        rc_a, rc_b = 1, 2
    else:
        nonexistent = "tests/nonexistent_t085.ax"
        rc_a, _o_a, err_a = drv.run_axiom0(axiom0, ["build", "-o", "out_mem.exe", nonexistent])
        rc_b, _o_b, err_b = drv.run_axiom0(axiom0, ["build"])
        blobs = [
            b"axiom0",
            b"build",
            b"--emit=obj",
            b"-o",
            b"out_mem.obj",
            b"out_mem.exe",
            b"-O1",
            b"--stack-reserve=2097152",
            b"build/tmp_obj_link_driver_",
            b".exe",
            nonexistent.encode("utf-8"),
            err_a,
            err_b,
        ]
        for rel in corpus:
            blobs.append(rel.encode("utf-8"))
            blobs.append(reference_build(axiom0, ["--emit=obj"], rel, "_gen_ref.obj"))
            blobs.append(reference_build(axiom0, [], rel, "_gen_ref.exe"))
            blobs.append(reference_build(axiom0, ["--emit=obj", "-O1"], rel, "_gen_ref_o1.obj"))
            blobs.append(reference_build(axiom0, ["-O1"], rel, "_gen_ref_o1.exe"))
            blobs.append(reference_build(axiom0, ["--stack-reserve=2097152"], rel, "_gen_ref_sr.exe"))
        blob_bytes, offs, lens = drv.pack_blobs(blobs)
    main_src = MAIN_TEMPLATE % {
        "blob_table": drv.byte_table("BLOBS", blob_bytes),
        "num_blobs": len(offs),
        "offs": ", ".join(str(x) for x in offs),
        "lens": ", ".join(str(x) for x in lens),
        "case_count": len(corpus),
        "lite": "true" if lite else "false",
        "nonexistent_rc": rc_a,
        "noinput_rc": rc_b,
    }
    header = "// test: run\n// timeout: 1800\n// modes: %s\n\n" % modes
    text = header + prelude + "\n" + full_mods + "\n" + main_src
    return out_path, text.encode("utf-8")


def main():
    check_mode = ("--check" in sys.argv[1:]) or ("check" in sys.argv[1:])
    refresh_goldens = "--refresh-goldens" in sys.argv[1:]
    axiom0 = drv.find_exe(["build/axiom0.exe", "build/axiom0"]) if refresh_goldens else None
    for i, a in enumerate(sys.argv[1:]):
        if a == "--axiom0" and i + 2 <= len(sys.argv[1:]):
            axiom0 = sys.argv[i + 2]
    prelude = drv.build_prelude_text()
    # the test bundles define their own `main`, so the axiomc entry module is left out
    full_mods = drv.assemble_modules(drv.FULL_MODULES + T085_MODULES[:1])
    outputs = [
        gen_diff_bundle("qa_obj_link_driver_diff.ax", "native", DIFF_CORPUS_FULL, prelude, full_mods, axiom0),
        gen_diff_bundle("qa_obj_link_driver_smoke.ax", "interp native", DIFF_CORPUS_SMOKE, prelude, full_mods, axiom0, lite=True),
    ]
    drv.bc.write_or_check_bundles(outputs, check_mode, root=ROOT)


if __name__ == "__main__":
    main()
