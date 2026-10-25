#!/usr/bin/env python3
"""Selfhost unit & differential test generator for compiler/driver (T085c).

Assembles selfhost test bundles in tests/selfhost/driver/ that verify the
complete Axiom compiler driver and pipeline CLI (compiler.driver.opts,
compiler.driver.pipeline, compiler.driver) against axiom0:

  - qa_driver_cli_and_project.ax (modes: interp native):
      CLI option parsing (help/--help/-h, version, --features, inspect, check,
      build, run), usage/version/features/emitter formatting parity against
      axiom0, all option error paths (missing command, unknown command, unknown
      option, missing option value, boolean option with '=', unknown emitter,
      missing -o, unsupported target, missing input file), axiom.toml manifest
      parsing (valid [package] bin/lib, comments/CRLF, negative malformed cases,
      and disk manifest_parse_file), find_std_root_with discovery hierarchy
      (--std-root -> AXIOM_STD -> exe_path -> cwd), derive_module_path, and
      project_discover (single-file and multi-file nested packages).
  - qa_driver_inspect_diff_a.ax (modes: interp native):
      End-to-end differential tests of driver_run_args on `inspect --emit=<kind>`
      comparing stdout/stderr/exit-code against axiom0 across tokens, ast,
      resolved, hir, thir, mir, and mir-opt (-O1) on .ax and .mir inputs.
  - qa_driver_inspect_diff_b.ax (modes: native):
      End-to-end differential tests of driver_run_args on `inspect --emit=<kind>`
      across backend emitters (lir, mi, mc, obj at -O0 and -O1) on .ax and .mir
      inputs plus multi-file package inspection.
  - qa_driver_commands_a.ax (modes: interp native):
      End-to-end tests of driver_run_args on version, --features, help, check
      (ok, human diagnostics, --json diagnostics, --time-passes, .mir input,
      multi-file package), and run (-O0, -O1, --interp, .mir input).
  - qa_driver_commands_b.ax (modes: native):
      End-to-end tests of driver_run_args and driver_execute_build_into across
      multi-file module packages (hello, mutual, nested, prelude_implicit,
      reexport), runtime panic handling (exit 101 + "panic: " stderr), and
      native `build` (--emit=obj COFF object with ax_main symbol, default PE32+
      .exe linking, --stack-reserve override, -O1 build, multi-file package
      build, and real disk output with cleanup).

Usage:
  python tests/selfhost/driver/gen_driver_tests.py [--axiom0 <path/to/axiom0.exe>]
"""

import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))
sys.path.insert(0, os.path.abspath(os.path.join(HERE, "..")))
import bundle_common as bc

LIGHT_MODULES = [
    ("compiler.kernel.id", "compiler"),
    ("compiler.kernel.hash", "compiler"),
    ("compiler.kernel.arena", "compiler"),
    ("compiler.kernel.interner", "compiler"),
    ("compiler.source.span", "compiler"),
    ("compiler.source.manager", "compiler"),
    ("compiler.diag.code", "compiler"),
    ("compiler.diag.emitter", "compiler"),
    ("compiler.diag.format", "compiler"),
    ("compiler.diag.json", "compiler"),
    ("compiler.kernel_source_diag.session", "compiler"),
    ("compiler.driver.opts", "compiler"),
]

FULL_MODULES = [
    ("compiler.kernel.id", "compiler"),
    ("compiler.kernel.hash", "compiler"),
    ("compiler.kernel.arena", "compiler"),
    ("compiler.kernel.interner", "compiler"),
    ("compiler.source.span", "compiler"),
    ("compiler.source.manager", "compiler"),
    ("compiler.diag.code", "compiler"),
    ("compiler.diag.emitter", "compiler"),
    ("compiler.diag.format", "compiler"),
    ("compiler.diag.json", "compiler"),
    ("compiler.kernel_source_diag.session", "compiler"),
    ("compiler.lex.token", "compiler"),
    ("compiler.lex.scanner", "compiler"),
    ("compiler.lexer.session", "compiler"),
    ("compiler.syntax.ast", "compiler"),
    ("compiler.syntax.parse", "compiler"),
    ("compiler.parser.session", "compiler"),
    ("compiler.resolve.symtab", "compiler"),
    ("compiler.resolve.rib", "compiler"),
    ("compiler.resolve.resolver", "compiler"),
    ("compiler.hir.hir", "compiler"),
    ("compiler.hir.lower", "compiler"),
    ("compiler.resolve_hir.session", "compiler"),
    ("compiler.types.types", "compiler"),
    ("compiler.types.layout", "compiler"),
    ("compiler.types.exhaust", "compiler"),
    ("compiler.traits.solver", "compiler"),
    ("compiler.traits.mono", "compiler"),
    ("compiler.types.typeck", "compiler"),
    ("compiler.types", "compiler"),
    ("compiler.traits", "compiler"),
    ("compiler.typeck.session", "compiler"),
    ("compiler.typeck", "compiler"),
    ("compiler.typeck_traits.session", "compiler"),
    ("compiler.typeck_traits", "compiler"),
    ("compiler.mir.mir", "compiler"),
    ("compiler.mir.drop", "compiler"),
    ("compiler.mir.builder", "compiler"),
    ("compiler.mir", "compiler"),
    ("compiler.own.move", "compiler"),
    ("compiler.own.cap", "compiler"),
    ("compiler.own.init", "compiler"),
    ("compiler.own.unsafe", "compiler"),
    ("compiler.own", "compiler"),
    ("compiler.verify.verifier", "compiler"),
    ("compiler.verify", "compiler"),
    ("compiler.own_mir_verify.session", "compiler"),
    ("compiler.own_mir_verify", "compiler"),
    ("compiler.opt.const_fold", "compiler"),
    ("compiler.opt.dce", "compiler"),
    ("compiler.opt.cfg_simp", "compiler"),
    ("compiler.opt", "compiler"),
    ("compiler.interp.value", "compiler"),
    ("compiler.interp.oracle", "compiler"),
    ("compiler.interp.frame", "compiler"),
    ("compiler.interp.interp", "compiler"),
    ("compiler.interp", "compiler"),
    ("compiler.interp_opt.session", "compiler"),
    ("compiler.interp_opt", "compiler"),
    ("compiler.lir.lir", "compiler"),
    ("compiler.lir.builder", "compiler"),
    ("compiler.lir", "compiler"),
    ("compiler.abi.win64", "compiler"),
    ("compiler.abi", "compiler"),
    ("compiler.obj.coff", "compiler"),
    ("compiler.obj.writer", "compiler"),
    ("compiler.obj", "compiler"),
    ("compiler.target.x64.encode", "compiler"),
    ("compiler.target.x64.isel", "compiler"),
    ("compiler.target.x64.frame", "compiler"),
    ("compiler.target.x64", "compiler"),
    ("compiler.backend.session", "compiler"),
    ("compiler.backend", "compiler"),
    ("compiler.link.pe", "compiler"),
    ("compiler.link.import", "compiler"),
    ("compiler.link.linker", "compiler"),
    ("compiler.link", "compiler"),
    ("compiler.driver.opts", "compiler"),
    ("compiler.driver.pipeline", "compiler"),
    ("compiler.driver", "compiler"),
]


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def write_bytes(path, data):
    with open(path, "wb") as f:
        f.write(data)


def byte_table(name, data):
    if not data:
        return "const %s: [1]u8 = [0u8];" % name
    lines = ["const %s: [%d]u8 = [" % (name, len(data))]
    for i in range(0, len(data), 24):
        chunk = data[i:i + 24]
        lines.append("    " + ", ".join("%du8" % b for b in chunk) + ",")
    lines.append("];")
    return "\n".join(lines)


def build_prelude_text():
    return bc.build_prelude_text(include_sym_pad=True, sym_pad_count=800, include_std_sys=True, root=ROOT)


def assemble_modules(mod_list):
    return bc.assemble_compiler_modules(mod_list, root=ROOT)


def find_exe(default_rels):
    for rel in default_rels:
        p = os.path.join(ROOT, *rel.split("/"))
        if os.path.isfile(p):
            return p
    return None


def run_axiom0(axiom0, args, expect_rc=None):
    cmd = [os.path.abspath(axiom0)] + list(args)
    res = subprocess.run(cmd, cwd=ROOT, stdout=subprocess.PIPE, stderr=subprocess.PIPE)
    if expect_rc is not None and res.returncode != expect_rc:
        raise SystemExit(
            "axiom0 %r returned %d (expected %d): stderr=%r"
            % (args, res.returncode, expect_rc, res.stderr)
        )
    return res.returncode, res.stdout.replace(b"\r\n", b"\n"), res.stderr.replace(b"\r\n", b"\n")


def pack_blobs(blobs):
    all_bytes = bytearray()
    offs = []
    lens = []
    for b in blobs:
        offs.append(len(all_bytes))
        lens.append(len(b))
        all_bytes.extend(b)
    return bytes(all_bytes), offs, lens


def gen_cli_and_project_bundle(prelude, light_mods, axiom0):
    out_path = os.path.join(HERE, "qa_driver_cli_and_project.ax")
    if axiom0 is None:
        blobs = bc.extract_blobs_from_bundle(out_path, "BLOBS", "BLOB_OFFS", "BLOB_LENS")
        blob_bytes, offs, lens = pack_blobs(blobs)
    else:
        _, exp_help, _ = run_axiom0(axiom0, ["help"], expect_rc=0)
        _, exp_version, _ = run_axiom0(axiom0, ["version"], expect_rc=0)
        _, exp_features, _ = run_axiom0(axiom0, ["--features"], expect_rc=0)
        _, _, exp_inspect_help = run_axiom0(axiom0, ["inspect", "--help"], expect_rc=2)
        _, _, exp_unknown_cmd = run_axiom0(axiom0, ["bogus"], expect_rc=2)
        _, _, exp_unknown_opt = run_axiom0(axiom0, ["check", "--unknown-flag", "tests/driver/test.ax"], expect_rc=2)
        _, _, exp_missing_val = run_axiom0(axiom0, ["check", "--target"], expect_rc=2)
        _, _, exp_unknown_emit = run_axiom0(axiom0, ["inspect", "--emit=bogus", "tests/driver/test.ax"], expect_rc=2)
        _, _, exp_check_no_file = run_axiom0(axiom0, ["check"], expect_rc=2)
        _, _, exp_build_no_file = run_axiom0(axiom0, ["build"], expect_rc=2)
        _, _, exp_build_no_o = run_axiom0(axiom0, ["build", "tests/driver/test.ax"], expect_rc=2)
        _, _, exp_run_no_file = run_axiom0(axiom0, ["run"], expect_rc=2)
        _, _, exp_inspect_no_file = run_axiom0(axiom0, ["inspect", "--emit=tokens"], expect_rc=2)

        blobs = [
            exp_help,              # 0: help usage
            exp_version,           # 1: version
            exp_features,          # 2: --features
            exp_inspect_help,      # 3: inspect --help stderr
            exp_unknown_cmd,       # 4: unknown command 'bogus' stderr
            exp_unknown_opt,       # 5: unknown option '--unknown-flag' stderr
            exp_missing_val,       # 6: option '--target' requires an argument stderr
            exp_unknown_emit,      # 7: unknown emitter 'bogus' stderr
            exp_check_no_file,     # 8: check needs an input file
            exp_build_no_file,     # 9: build needs an input file
            exp_build_no_o,        # 10: build needs an output file (-o)
            exp_run_no_file,       # 11: run needs an input file
            exp_inspect_no_file,   # 12: usage: axiom0 inspect --emit=tokens <file>
            # Strings for CLI, manifest, std_root, derive_module_path, project_discover:
            b"axiom0",                       # 13
            b"help",                         # 14
            b"--help",                       # 15
            b"-h",                           # 16
            b"version",                      # 17
            b"--features",                   # 18
            b"inspect",                      # 19
            b"check",                        # 20
            b"build",                        # 21
            b"run",                          # 22
            b"bogus",                        # 23
            b"--unknown-flag",               # 24
            b"tests/driver/test.ax",         # 25
            b"--target",                     # 26
            b"--emit=bogus",                 # 27
            b"--emit=tokens",                # 28
            b"--color=never",                # 29
            b"--time-passes",                # 30
            b"--json",                       # 31
            b"-O1",                          # 32
            b"--verify-each",                # 33
            b"--target=x86_64-pc-windows-msvc",  # 34
            b"--std-root=std",               # 35
            b"--interp",                     # 36
            b"--step-limit=12345",           # 37
            b"--max-call-depth=678",         # 38
            b"--",                           # 39
            b"arg1",                         # 40
            b"arg2",                         # 41
            b"x86_64-pc-windows-msvc",       # 42
            b"std",                          # 43
            b"--target=aarch64-unknown-linux-gnu",  # 44
            b"--json=true",                  # 45
            b"axiom0: option '--json' does not take an argument\n",  # 46
            b"-o",                           # 47
            b"out.exe",                      # 48
            b"--stack-reserve",              # 49
            b"2097152",                      # 50
            # Manifest test inputs:
            b"# Package manifest\r\n[package]\r\nname = \"my_pkg\" # inline comment\r\nkind = \"lib\"\r\n",  # 51
            b"my_pkg",                       # 52
            b"lib",                          # 53
            b"name = \"no_section\"\n",      # 54: missing [package]
            b"[dependencies]\nfoo = \"1\"\n", # 55: unknown section
            b"[package]\nkind = \"bin\"\n",  # 56: missing name
            b"[package]\nname = \"\"\n",     # 57: empty name
            b"[package]\nname = unquoted\n", # 58: unquoted value
            b"[package]\nname = \"ok\"\nbroken_no_eq\n",  # 59: missing '='
            b"tests/modules/hello/axiom.toml",  # 60
            b"hello",                        # 61
            b"bin",                          # 62
            # std_root & derive_module_path & project_discover inputs:
            b".",                            # 63
            b"./std",                        # 64
            b"nonexistent_std_dir_xyz",      # 65
            b"build/axiom0.exe",             # 66
            b"main",                         # 67
            b"src/main.ax",                  # 68
            b"src/math.ax",                  # 69
            b"math",                         # 70
            b"src/utils/calc.ax",            # 71
            b"utils.calc",                   # 72
            b"src/a/b/c.ax",                 # 73
            b"a.b.c",                        # 74
            b"tests/modules/hello/src/main.ax",   # 75
            b"tests/modules/nested/src/main.ax",  # 76
            b"a",                            # 77
            b"ast",                          # 78
            b"hir",                          # 79
            b"lir",                          # 80
            b"mc",                           # 81
            b"mi",                           # 82
            b"mir",                          # 83
            b"mir-opt",                      # 84
            b"obj",                          # 85
            b"resolved",                     # 86
            b"thir",                         # 87
            b"tokens",                       # 88
        ]
        blob_bytes, offs, lens = pack_blobs(blobs)

    main_src = """\
module selfhost_driver_cli_and_project_test

use host_intrinsics.heap_alloc
use host_intrinsics.heap_free
use compiler.kernel.arena.Arena
use compiler.kernel.arena.arena_new
use compiler.kernel.arena.arena_destroy
use compiler.kernel.interner.StrView
use compiler.diag.emitter.DiagSink
use compiler.diag.emitter.diag_sink_init
use compiler.diag.emitter.diag_sink_free
use compiler.diag.emitter.diag_sink_error_count
use compiler.diag.format.DiagBuffer
use compiler.diag.format.diag_buf_new
use compiler.diag.format.diag_buf_free
use compiler.driver.opts.AX_EXIT_OK
use compiler.driver.opts.AX_EXIT_USAGE
use compiler.driver.opts.CMD_NONE
use compiler.driver.opts.CMD_HELP
use compiler.driver.opts.CMD_VERSION
use compiler.driver.opts.CMD_FEATURES
use compiler.driver.opts.CMD_INSPECT
use compiler.driver.opts.CMD_CHECK
use compiler.driver.opts.CMD_BUILD
use compiler.driver.opts.CMD_RUN
use compiler.driver.opts.EMIT_NONE
use compiler.driver.opts.EMIT_AST
use compiler.driver.opts.EMIT_HIR
use compiler.driver.opts.EMIT_LIR
use compiler.driver.opts.EMIT_MC
use compiler.driver.opts.EMIT_MI
use compiler.driver.opts.EMIT_MIR
use compiler.driver.opts.EMIT_MIR_OPT
use compiler.driver.opts.EMIT_OBJ
use compiler.driver.opts.EMIT_RESOLVED
use compiler.driver.opts.EMIT_THIR
use compiler.driver.opts.EMIT_TOKENS
use compiler.driver.opts.DriverOptions
use compiler.driver.opts.opts_mul_usize
use compiler.driver.opts.sv_slot_get
use compiler.driver.opts.sv_slot_set
use compiler.driver.opts.driver_options_alloc
use compiler.driver.opts.driver_options_dealloc
use compiler.driver.opts.driver_format_usage
use compiler.driver.opts.driver_format_version
use compiler.driver.opts.driver_format_features
use compiler.driver.opts.driver_format_emitters
use compiler.driver.opts.driver_find_command
use compiler.driver.opts.driver_find_emitter
use compiler.driver.opts.driver_parse_cli
use compiler.driver.opts.PackageManifest
use compiler.driver.opts.manifest_alloc
use compiler.driver.opts.manifest_dealloc
use compiler.driver.opts.manifest_parse_text
use compiler.driver.opts.manifest_read_file
use compiler.driver.opts.find_std_root_with
use compiler.driver.opts.derive_module_path
use compiler.driver.opts.Project
use compiler.driver.opts.ProjectFile
use compiler.driver.opts.project_alloc
use compiler.driver.opts.project_dealloc
use compiler.driver.opts.project_discover
use compiler.driver.opts.project_file_const_at
use compiler.driver.opts.pf_get_module_path

@intrinsic fn size_of<T>() -> usize { 0 }
@intrinsic fn align_of<T>() -> usize { 0 }

unsafe fn diag_sink_alloc() -> *mut DiagSink {
    let bytes = size_of<DiagSink>();
    let raw = heap_alloc(bytes, align_of<DiagSink>());
    let mut i: usize = 0;
    while i < bytes {
        *(raw + i) = 0u8;
        i = i + 1;
    }
    let p = raw as *mut DiagSink;
    diag_sink_init(mut_view(*p));
    p
}

unsafe fn diag_sink_dealloc(p: *mut DiagSink) {
    if (p as usize) == 0 { return; }
    diag_sink_free(mut_view(*p));
    heap_free(p as *mut u8, size_of<DiagSink>(), align_of<DiagSink>());
}

%(blob_table)s
const BLOB_OFFS: [%(num_blobs)d]usize = [%(offs)s];
const BLOB_LENS: [%(num_blobs)d]usize = [%(lens)s];

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

fn buf_matches_blob(buf: view<DiagBuffer>, blob_idx: usize) -> bool {
    let off = BLOB_OFFS[blob_idx];
    let blen = BLOB_LENS[blob_idx];
    if buf.len != blen {
        return false;
    }
    let mut i: usize = 0;
    while i < blen {
        let b = unsafe { *(buf.ptr + i) };
        if b != BLOBS[off + i] {
            return false;
        }
        i = i + 1;
    }
    true
}

fn sv_matches_blob(sv: view<StrView>, blob_idx: usize) -> bool {
    let off = BLOB_OFFS[blob_idx];
    let blen = BLOB_LENS[blob_idx];
    if sv.len != blen {
        return false;
    }
    let mut i: usize = 0;
    while i < blen {
        let b = unsafe { *(sv.ptr + i) };
        if b != BLOBS[off + i] {
            return false;
        }
        i = i + 1;
    }
    true
}

fn check_parse_cli_case(
    argv: *const StrView,
    argc: usize,
    exp_rc: i32,
    exp_out_blob: isize,
    exp_err_blob: isize
) -> bool {
    let dopts = unsafe { driver_options_alloc() };
    let mut out_buf = diag_buf_new();
    let mut err_buf = diag_buf_new();
    let rc = unsafe { driver_parse_cli(argv, argc, mut_view(*dopts), mut_view(out_buf), mut_view(err_buf)) };
    let mut ok = rc == exp_rc;
    if ok && exp_out_blob >= 0isize {
        if !buf_matches_blob(view(out_buf), exp_out_blob as usize) {
            ok = false;
        }
    }
    if ok && exp_err_blob >= 0isize {
        if !buf_matches_blob(view(err_buf), exp_err_blob as usize) {
            ok = false;
        }
    }
    diag_buf_free(mut_view(out_buf));
    diag_buf_free(mut_view(err_buf));
    unsafe { driver_options_dealloc(dopts); }
    ok
}

fn find_cmd_blob(blob_idx: usize) -> u32 {
    let b = blob_sv(blob_idx);
    driver_find_command(view(b))
}

fn find_emit_blob(blob_idx: usize) -> u32 {
    let b = blob_sv(blob_idx);
    driver_find_emitter(view(b))
}

fn test_cli_formatting_and_lookup() -> i32 {
    let mut b = diag_buf_new();
    driver_format_usage(mut_view(b));
    if !buf_matches_blob(view(b), 0) {
        diag_buf_free(mut_view(b));
        return 10;
    }
    diag_buf_free(mut_view(b));

    let mut b2 = diag_buf_new();
    driver_format_version(mut_view(b2));
    if !buf_matches_blob(view(b2), 1) {
        diag_buf_free(mut_view(b2));
        return 11;
    }
    diag_buf_free(mut_view(b2));

    let mut b3 = diag_buf_new();
    driver_format_features(mut_view(b3));
    if !buf_matches_blob(view(b3), 2) {
        diag_buf_free(mut_view(b3));
        return 12;
    }
    diag_buf_free(mut_view(b3));

    if find_cmd_blob(14) != CMD_HELP { return 13; }
    if find_cmd_blob(15) != CMD_HELP { return 14; }
    if find_cmd_blob(16) != CMD_HELP { return 15; }
    if find_cmd_blob(17) != CMD_VERSION { return 16; }
    if find_cmd_blob(18) != CMD_FEATURES { return 17; }
    if find_cmd_blob(19) != CMD_INSPECT { return 18; }
    if find_cmd_blob(20) != CMD_CHECK { return 19; }
    if find_cmd_blob(21) != CMD_BUILD { return 20; }
    if find_cmd_blob(22) != CMD_RUN { return 21; }
    if find_cmd_blob(23) != CMD_NONE { return 22; }

    if find_emit_blob(78) != EMIT_AST { return 23; }
    if find_emit_blob(79) != EMIT_HIR { return 24; }
    if find_emit_blob(80) != EMIT_LIR { return 25; }
    if find_emit_blob(81) != EMIT_MC { return 26; }
    if find_emit_blob(82) != EMIT_MI { return 27; }
    if find_emit_blob(83) != EMIT_MIR { return 28; }
    if find_emit_blob(84) != EMIT_MIR_OPT { return 29; }
    if find_emit_blob(85) != EMIT_OBJ { return 30; }
    if find_emit_blob(86) != EMIT_RESOLVED { return 31; }
    if find_emit_blob(87) != EMIT_THIR { return 32; }
    if find_emit_blob(88) != EMIT_TOKENS { return 33; }
    if find_emit_blob(23) != EMIT_NONE { return 34; }
    0
}

fn test_cli_parsing() -> i32 {
    let a = alloc_argv(16);
    let ap = a as *const StrView;
    set_arg_blob(a, 0, 13);

    // 1. No args -> rc 2, err == usage
    if !check_parse_cli_case(ap, 1, AX_EXIT_USAGE, -1isize, 0isize) { return 40; }

    // 2. help, --help, -h -> rc 0, out == usage
    set_arg_blob(a, 1, 14);
    if !check_parse_cli_case(ap, 2, AX_EXIT_OK, 0isize, -1isize) { return 41; }
    set_arg_blob(a, 1, 15);
    if !check_parse_cli_case(ap, 2, AX_EXIT_OK, 0isize, -1isize) { return 42; }
    set_arg_blob(a, 1, 16);
    if !check_parse_cli_case(ap, 2, AX_EXIT_OK, 0isize, -1isize) { return 43; }

    // 3. version, --features -> rc 0
    set_arg_blob(a, 1, 17);
    if !check_parse_cli_case(ap, 2, AX_EXIT_OK, 1isize, -1isize) { return 44; }
    set_arg_blob(a, 1, 18);
    if !check_parse_cli_case(ap, 2, AX_EXIT_OK, 2isize, -1isize) { return 45; }

    // 4. inspect --help -> rc 2, err == inspect usage + emitters
    set_arg_blob(a, 1, 19);
    set_arg_blob(a, 2, 15);
    if !check_parse_cli_case(ap, 3, AX_EXIT_USAGE, -1isize, 3isize) { return 46; }

    // 5. unknown command 'bogus' -> rc 2
    set_arg_blob(a, 1, 23);
    if !check_parse_cli_case(ap, 2, AX_EXIT_USAGE, -1isize, 4isize) { return 47; }

    // 6. unknown option '--unknown-flag' -> rc 2
    set_arg_blob(a, 1, 20);
    set_arg_blob(a, 2, 24);
    set_arg_blob(a, 3, 25);
    if !check_parse_cli_case(ap, 4, AX_EXIT_USAGE, -1isize, 5isize) { return 48; }

    // 7. missing value for '--target' -> rc 2
    set_arg_blob(a, 1, 20);
    set_arg_blob(a, 2, 26);
    if !check_parse_cli_case(ap, 3, AX_EXIT_USAGE, -1isize, 6isize) { return 49; }

    // 8. unknown emitter '--emit=bogus' -> rc 2
    set_arg_blob(a, 1, 19);
    set_arg_blob(a, 2, 27);
    set_arg_blob(a, 3, 25);
    if !check_parse_cli_case(ap, 4, AX_EXIT_USAGE, -1isize, 7isize) { return 50; }

    // 9. missing input files and missing -o
    set_arg_blob(a, 1, 20);
    if !check_parse_cli_case(ap, 2, AX_EXIT_USAGE, -1isize, 8isize) { return 51; }
    set_arg_blob(a, 1, 21);
    if !check_parse_cli_case(ap, 2, AX_EXIT_USAGE, -1isize, 9isize) { return 52; }
    set_arg_blob(a, 1, 21);
    set_arg_blob(a, 2, 25);
    if !check_parse_cli_case(ap, 3, AX_EXIT_USAGE, -1isize, 10isize) { return 53; }
    set_arg_blob(a, 1, 22);
    if !check_parse_cli_case(ap, 2, AX_EXIT_USAGE, -1isize, 11isize) { return 54; }
    set_arg_blob(a, 1, 19);
    set_arg_blob(a, 2, 28);
    if !check_parse_cli_case(ap, 3, AX_EXIT_USAGE, -1isize, 12isize) { return 55; }

    // 10. boolean option with '=' (--json=true) -> rc 2
    set_arg_blob(a, 1, 20);
    set_arg_blob(a, 2, 45);
    set_arg_blob(a, 3, 25);
    if !check_parse_cli_case(ap, 4, AX_EXIT_USAGE, -1isize, 46isize) { return 56; }

    // 11. unsupported target -> rc 2
    set_arg_blob(a, 1, 20);
    set_arg_blob(a, 2, 44);
    set_arg_blob(a, 3, 25);
    if !check_parse_cli_case(ap, 4, AX_EXIT_USAGE, -1isize, -1isize) { return 57; }

    // 12. Full flag set + `--` pass-through args
    set_arg_blob(a, 1, 22);  // run
    set_arg_blob(a, 2, 29);  // --color=never
    set_arg_blob(a, 3, 30);  // --time-passes
    set_arg_blob(a, 4, 31);  // --json
    set_arg_blob(a, 5, 32);  // -O1
    set_arg_blob(a, 6, 33);  // --verify-each
    set_arg_blob(a, 7, 34);  // --target=x86_64-pc-windows-msvc
    set_arg_blob(a, 8, 35);  // --std-root=std
    set_arg_blob(a, 9, 36);  // --interp
    set_arg_blob(a, 10, 37); // --step-limit=12345
    set_arg_blob(a, 11, 38); // --max-call-depth=678
    set_arg_blob(a, 12, 25); // tests/driver/test.ax
    set_arg_blob(a, 13, 39); // --
    set_arg_blob(a, 14, 40); // arg1
    set_arg_blob(a, 15, 41); // arg2

    let dopts = unsafe { driver_options_alloc() };
    let mut out_b = diag_buf_new();
    let mut err_b = diag_buf_new();
    let rc = unsafe { driver_parse_cli(ap, 16, mut_view(*dopts), mut_view(out_b), mut_view(err_b)) };
    let mut flags_ok = unsafe {
        rc == AX_EXIT_OK &&
        (*dopts).cmd == CMD_RUN &&
        (*dopts).color_never &&
        (*dopts).time_passes &&
        (*dopts).json &&
        (*dopts).opt_O1 &&
        !(*dopts).opt_O0 &&
        (*dopts).verify_each &&
        (*dopts).run_interp &&
        (*dopts).step_limit == 12345 &&
        (*dopts).max_call_depth == 678 &&
        sv_matches_blob(view((*dopts).target), 42) &&
        sv_matches_blob(view((*dopts).std_root), 43) &&
        sv_matches_blob(view((*dopts).input_file), 25) &&
        (*dopts).run_argc == 2
    };
    if flags_ok {
        let r0 = unsafe { sv_slot_get((*dopts).run_args as *const StrView, 0) };
        let r1 = unsafe { sv_slot_get((*dopts).run_args as *const StrView, 1) };
        if !sv_matches_blob(view(r0), 40) || !sv_matches_blob(view(r1), 41) {
            flags_ok = false;
        }
    }
    diag_buf_free(mut_view(out_b));
    diag_buf_free(mut_view(err_b));
    unsafe { driver_options_dealloc(dopts); }
    if !flags_ok { return 58; }

    // 13. Space-separated build options: build -o out.exe --stack-reserve 2097152 tests/driver/test.ax
    set_arg_blob(a, 1, 21);
    set_arg_blob(a, 2, 47);
    set_arg_blob(a, 3, 48);
    set_arg_blob(a, 4, 49);
    set_arg_blob(a, 5, 50);
    set_arg_blob(a, 6, 25);
    let bopts = unsafe { driver_options_alloc() };
    let mut out_b2 = diag_buf_new();
    let mut err_b2 = diag_buf_new();
    let brc = unsafe { driver_parse_cli(ap, 7, mut_view(*bopts), mut_view(out_b2), mut_view(err_b2)) };
    let b_ok = unsafe {
        brc == AX_EXIT_OK &&
        (*bopts).cmd == CMD_BUILD &&
        sv_matches_blob(view((*bopts).output), 48) &&
        sv_matches_blob(view((*bopts).stack_reserve), 50) &&
        sv_matches_blob(view((*bopts).input_file), 25)
    };
    diag_buf_free(mut_view(out_b2));
    diag_buf_free(mut_view(err_b2));
    unsafe { driver_options_dealloc(bopts); }
    if !b_ok { return 59; }
    0
}

fn test_manifest_and_std_root() -> i32 {
    let m = unsafe { manifest_alloc() };
    let b51 = blob_sv(51);
    let ok1 = unsafe { manifest_parse_text(view(b51), mut_view(*m)) };
    let valid1 = unsafe { ok1 && sv_matches_blob(view((*m).name), 52) && sv_matches_blob(view((*m).kind), 53) };
    unsafe { manifest_dealloc(m); }
    if !valid1 { return 60; }

    // Negative manifest cases (54..59)
    let mut neg_idx: usize = 54;
    while neg_idx <= 59 {
        let nm = unsafe { manifest_alloc() };
        let bneg = blob_sv(neg_idx);
        let nok = unsafe { manifest_parse_text(view(bneg), mut_view(*nm)) };
        unsafe { manifest_dealloc(nm); }
        if nok { return (70 + (neg_idx - 54)) as i32; }
        neg_idx = neg_idx + 1;
    }

    // Disk manifest_read_file on tests/modules/hello/axiom.toml
    let dm = unsafe { manifest_alloc() };
    let b60 = blob_sv(60);
    let dok = unsafe { manifest_read_file(view(b60), mut_view(*dm)) };
    let dvalid = unsafe { dok && sv_matches_blob(view((*dm).name), 61) };
    unsafe { manifest_dealloc(dm); }
    if !dvalid { return 78; }

    // find_std_root_with hierarchy
    let mut arena = arena_new();
    let empty = StrView { ptr: 0 as *const u8, len: 0 };
    let b43 = blob_sv(43);
    let b65 = blob_sv(65);
    let b66 = blob_sv(66);
    let r1 = find_std_root_with(view(b43), view(empty), view(empty), mut_view(arena));
    if !sv_matches_blob(view(r1), 43) {
        arena_destroy(mut_view(arena));
        return 79;
    }

    let r2 = find_std_root_with(view(b65), view(b43), view(b66), mut_view(arena));
    if r2.len != 0 {
        arena_destroy(mut_view(arena));
        return 80;
    }

    let r3 = find_std_root_with(view(empty), view(b43), view(empty), mut_view(arena));
    if !sv_matches_blob(view(r3), 43) {
        arena_destroy(mut_view(arena));
        return 81;
    }

    let r4 = find_std_root_with(view(empty), view(empty), view(b66), mut_view(arena));
    if r4.len == 0 {
        arena_destroy(mut_view(arena));
        return 82;
    }

    // derive_module_path
    let b68 = blob_sv(68);
    let mp0 = derive_module_path(view(b68), mut_view(arena));
    if !sv_matches_blob(view(mp0), 67) {
        arena_destroy(mut_view(arena));
        return 84;
    }
    let b69 = blob_sv(69);
    let mp1 = derive_module_path(view(b69), mut_view(arena));
    if !sv_matches_blob(view(mp1), 70) {
        arena_destroy(mut_view(arena));
        return 85;
    }
    let b71 = blob_sv(71);
    let mp2 = derive_module_path(view(b71), mut_view(arena));
    if !sv_matches_blob(view(mp2), 72) {
        arena_destroy(mut_view(arena));
        return 86;
    }
    let b73 = blob_sv(73);
    let mp3 = derive_module_path(view(b73), mut_view(arena));
    if !sv_matches_blob(view(mp3), 74) {
        arena_destroy(mut_view(arena));
        return 87;
    }

    arena_destroy(mut_view(arena));
    0
}

fn test_project_discovery() -> i32 {
    let empty = StrView { ptr: 0 as *const u8, len: 0 };

    // 1. Single-file discovery on tests/driver/test.ax (1 user file + 3 std core files = 4)
    let sink1 = unsafe { diag_sink_alloc() };
    let p1 = unsafe { project_alloc() };
    let b25 = blob_sv(25);
    let ok1 = unsafe { project_discover(view(b25), view(empty), mut_view(*p1), mut_view(*sink1)) };
    let v1 = unsafe { ok1 && !(*p1).is_package && (*p1).file_count == 4 && diag_sink_error_count(view(*sink1)) == 0 };
    unsafe {
        project_dealloc(p1);
        diag_sink_dealloc(sink1);
    }
    if !v1 { return 90; }

    // 2. Multi-file package discovery on tests/modules/hello/src/main.ax (2 user + 3 std = 5)
    let sink2 = unsafe { diag_sink_alloc() };
    let p2 = unsafe { project_alloc() };
    let b75 = blob_sv(75);
    let ok2 = unsafe { project_discover(view(b75), view(empty), mut_view(*p2), mut_view(*sink2)) };
    let mut v2 = unsafe {
        ok2 &&
        (*p2).is_package &&
        (*p2).has_manifest &&
        sv_matches_blob(view((*p2).manifest.name), 61) &&
        (*p2).file_count == 5 &&
        diag_sink_error_count(view(*sink2)) == 0
    };
    if v2 {
        let pf0 = unsafe { project_file_const_at((*p2).files as *const ProjectFile, 0) };
        let pf1 = unsafe { project_file_const_at((*p2).files as *const ProjectFile, 1) };
        let mp0 = pf_get_module_path(pf0);
        let mp1 = pf_get_module_path(pf1);
        if !sv_matches_blob(view(mp0), 67) || !sv_matches_blob(view(mp1), 70) {
            v2 = false;
        }
    }
    unsafe {
        project_dealloc(p2);
        diag_sink_dealloc(sink2);
    }
    if !v2 { return 91; }

    // 3. Nested multi-file package discovery on tests/modules/nested/src/main.ax (2 user + 3 std = 5)
    let sink3 = unsafe { diag_sink_alloc() };
    let p3 = unsafe { project_alloc() };
    let b76 = blob_sv(76);
    let ok3 = unsafe { project_discover(view(b76), view(empty), mut_view(*p3), mut_view(*sink3)) };
    let mut v3 = unsafe { ok3 && (*p3).is_package && (*p3).file_count == 5 && diag_sink_error_count(view(*sink3)) == 0 };
    if v3 {
        let nf0 = unsafe { project_file_const_at((*p3).files as *const ProjectFile, 0) };
        let nf1 = unsafe { project_file_const_at((*p3).files as *const ProjectFile, 1) };
        let nmp0 = pf_get_module_path(nf0);
        let nmp1 = pf_get_module_path(nf1);
        // Sorted paths: src/main.ax ("main"), src/utils/calc.ax ("utils.calc")
        if !sv_matches_blob(view(nmp0), 67) || !sv_matches_blob(view(nmp1), 72) {
            v3 = false;
        }
    }
    unsafe {
        project_dealloc(p3);
        diag_sink_dealloc(sink3);
    }
    if !v3 { return 92; }
    0
}

pub fn main() -> i32 {
    let r1 = test_cli_formatting_and_lookup();
    if r1 != 0 { return r1; }
    let r2 = test_cli_parsing();
    if r2 != 0 { return r2; }
    let r3 = test_manifest_and_std_root();
    if r3 != 0 { return r3; }
    let r4 = test_project_discovery();
    if r4 != 0 { return r4; }
    0
}
""" % {
        "blob_table": byte_table("BLOBS", blob_bytes),
        "num_blobs": len(offs),
        "offs": ", ".join(str(x) for x in offs),
        "lens": ", ".join(str(x) for x in lens),
    }

    header = "// test: run\n// timeout: 1200\n// modes: interp native\n\n"
    full_text = header + prelude + "\n" + light_mods + "\n" + main_src
    return out_path, full_text.encode("utf-8")


def gen_inspect_diff_bundle(filename, modes, prelude, full_mods, axiom0, cases, fast_std=False):
    out_path = os.path.join(HERE, filename)
    case_meta = []
    if axiom0 is None:
        blobs = bc.extract_blobs_from_bundle(out_path, "BLOBS", "BLOB_OFFS", "BLOB_LENS")
        blob_bytes, offs, lens = pack_blobs(blobs)
        for idx, (_emit_flag, opt_o1, _input_path) in enumerate(cases):
            base = 4 + 4 * idx
            case_meta.append((base, 1 if opt_o1 else 0, base + 1, 0, base + 2, base + 3))
    else:
        blobs = [b"axiom0", b"inspect", b"-O1", b"--std-root=tests/driver"]
        for emit_flag, opt_o1, input_path in cases:
            emit_idx = len(blobs)
            blobs.append(emit_flag.encode("utf-8"))
            in_idx = len(blobs)
            blobs.append(input_path.encode("utf-8"))

            extra = ["--std-root=tests/driver"] if fast_std else []
            if emit_flag == "--emit=mir-opt" or (emit_flag == "--emit=mir" and opt_o1):
                args = ["inspect"] + extra + ["--emit=mir", "-O1", input_path]
            else:
                args = ["inspect"] + extra + [emit_flag] + (["-O1"] if opt_o1 else []) + [input_path]
            rc, out_b, err_b = run_axiom0(axiom0, args, expect_rc=0)
            out_idx = len(blobs)
            blobs.append(out_b)
            err_idx = len(blobs)
            blobs.append(err_b)
            case_meta.append((emit_idx, 1 if opt_o1 else 0, in_idx, rc, out_idx, err_idx))

        blob_bytes, offs, lens = pack_blobs(blobs)

    main_src = """\
module selfhost_driver_inspect_diff_test

use host_intrinsics.heap_alloc
use compiler.kernel.interner.StrView
use compiler.diag.format.DiagBuffer
use compiler.diag.format.diag_buf_new
use compiler.diag.format.diag_buf_free
use compiler.driver.opts.opts_mul_usize
use compiler.driver.opts.sv_slot_set
use compiler.driver.pipeline.driver_run_args

%(blob_table)s
const BLOB_OFFS: [%(num_blobs)d]usize = [%(offs)s];
const BLOB_LENS: [%(num_blobs)d]usize = [%(lens)s];

const CASE_EMIT: [%(num_cases)d]usize = [%(case_emit)s];
const CASE_O1: [%(num_cases)d]u32 = [%(case_o1)s];
const CASE_IN: [%(num_cases)d]usize = [%(case_in)s];
const CASE_RC: [%(num_cases)d]i32 = [%(case_rc)s];
const CASE_OUT: [%(num_cases)d]usize = [%(case_out)s];
const CASE_ERR: [%(num_cases)d]usize = [%(case_err)s];
const USE_FAST_STD: u32 = %(use_fast_std)du32;

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

fn buf_matches_blob(buf: view<DiagBuffer>, blob_idx: usize) -> bool {
    let off = BLOB_OFFS[blob_idx];
    let blen = BLOB_LENS[blob_idx];
    if buf.len != blen {
        return false;
    }
    let mut i: usize = 0;
    while i < blen {
        let b = unsafe { *(buf.ptr + i) };
        if b != BLOBS[off + i] {
            return false;
        }
        i = i + 1;
    }
    true
}

pub fn main() -> i32 {
    let argv = alloc_argv(6);
    let ap = argv as *const StrView;
    let mut c: usize = 0;
    while c < %(num_cases)d {
        set_arg_blob(argv, 0, 0);
        set_arg_blob(argv, 1, 1);
        let mut argc: usize = 4;
        if USE_FAST_STD != 0u32 {
            set_arg_blob(argv, 2, 3);
            set_arg_blob(argv, 3, CASE_EMIT[c]);
            if CASE_O1[c] != 0u32 {
                set_arg_blob(argv, 4, 2);
                set_arg_blob(argv, 5, CASE_IN[c]);
                argc = 6;
            } else {
                set_arg_blob(argv, 4, CASE_IN[c]);
                argc = 5;
            }
        } else {
            set_arg_blob(argv, 2, CASE_EMIT[c]);
            if CASE_O1[c] != 0u32 {
                set_arg_blob(argv, 3, 2);
                set_arg_blob(argv, 4, CASE_IN[c]);
                argc = 5;
            } else {
                set_arg_blob(argv, 3, CASE_IN[c]);
                argc = 4;
            }
        }

        let mut out_buf = diag_buf_new();
        let mut err_buf = diag_buf_new();
        let rc = driver_run_args(ap, argc, mut_view(out_buf), mut_view(err_buf));
        let ok_rc = rc == CASE_RC[c];
        let ok_out = buf_matches_blob(view(out_buf), CASE_OUT[c]);
        let ok_err = buf_matches_blob(view(err_buf), CASE_ERR[c]);
        diag_buf_free(mut_view(out_buf));
        diag_buf_free(mut_view(err_buf));
        if !ok_rc {
            return (10 + c) as i32;
        }
        if !ok_out {
            return (40 + c) as i32;
        }
        if !ok_err {
            return (70 + c) as i32;
        }
        c = c + 1;
    }
    0
}
""" % {
        "blob_table": byte_table("BLOBS", blob_bytes),
        "num_blobs": len(offs),
        "offs": ", ".join(str(x) for x in offs),
        "lens": ", ".join(str(x) for x in lens),
        "num_cases": len(case_meta),
        "case_emit": ", ".join(str(x[0]) for x in case_meta),
        "case_o1": ", ".join("%du32" % x[1] for x in case_meta),
        "case_in": ", ".join(str(x[2]) for x in case_meta),
        "case_rc": ", ".join(str(x[3]) for x in case_meta),
        "case_out": ", ".join(str(x[4]) for x in case_meta),
        "case_err": ", ".join(str(x[5]) for x in case_meta),
        "use_fast_std": 1 if fast_std else 0,
    }

    header = "// test: run\n// timeout: 1200\n// modes: %s\n\n" % modes
    full_text = header + prelude + "\n" + full_mods + "\n" + main_src
    return out_path, full_text.encode("utf-8")


def gen_commands_a_bundle(prelude, full_mods, axiom0):
    out_path = os.path.join(HERE, "qa_driver_commands_a.ax")
    if axiom0 is None:
        blobs = bc.extract_blobs_from_bundle(out_path, "BLOBS", "BLOB_OFFS", "BLOB_LENS")
        blob_bytes, offs, lens = pack_blobs(blobs)
    else:
        _, exp_version, _ = run_axiom0(axiom0, ["version"], expect_rc=0)
        _, exp_features, _ = run_axiom0(axiom0, ["--features"], expect_rc=0)
        _, exp_help, _ = run_axiom0(axiom0, ["help"], expect_rc=0)
        _, _, exp_check_err = run_axiom0(axiom0, ["check", "--std-root=tests/driver", "tests/driver/error.ax"], expect_rc=1)
        _, _, exp_json_err = run_axiom0(axiom0, ["check", "--std-root=tests/driver", "--json", "tests/driver/error.ax"], expect_rc=1)

        blobs = [
            b"axiom0",                           # 0
            b"version",                          # 1
            b"--features",                       # 2
            b"help",                             # 3
            b"check",                            # 4
            b"run",                              # 5
            b"--json",                           # 6
            b"--time-passes",                    # 7
            b"--interp",                         # 8
            b"-O1",                              # 9
            b"tests/driver/test.ax",             # 10
            b"tests/driver/error.ax",            # 11
            b"tests/lir/const.mir",              # 12
            b"--std-root=tests/driver",          # 13
            b"tests/opt/const_fold_run.ax",      # 14
            exp_version,                         # 15
            exp_features,                        # 16
            exp_help,                            # 17
            exp_check_err,                       # 18
            exp_json_err,                        # 19
            b"time: source    ",                 # 20
            b"time: lex       ",                 # 21
            b"time: parse     ",                 # 22
            b"time: resolve   ",                 # 23
            b"time: hir       ",                 # 24
            b"time: typeck    ",                 # 25
            b"time: own       ",                 # 26
        ]
        blob_bytes, offs, lens = pack_blobs(blobs)

    main_src = """\
module selfhost_driver_commands_a_test

use host_intrinsics.heap_alloc
use compiler.kernel.interner.StrView
use compiler.diag.format.DiagBuffer
use compiler.diag.format.diag_buf_new
use compiler.diag.format.diag_buf_free
use compiler.driver.opts.AX_EXIT_OK
use compiler.driver.opts.AX_EXIT_DIAG
use compiler.driver.opts.opts_mul_usize
use compiler.driver.opts.sv_slot_set
use compiler.driver.pipeline.driver_run_args

%(blob_table)s
const BLOB_OFFS: [%(num_blobs)d]usize = [%(offs)s];
const BLOB_LENS: [%(num_blobs)d]usize = [%(lens)s];

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

fn buf_matches_blob(buf: view<DiagBuffer>, blob_idx: usize) -> bool {
    let off = BLOB_OFFS[blob_idx];
    let blen = BLOB_LENS[blob_idx];
    if buf.len != blen {
        return false;
    }
    let mut i: usize = 0;
    while i < blen {
        let b = unsafe { *(buf.ptr + i) };
        if b != BLOBS[off + i] {
            return false;
        }
        i = i + 1;
    }
    true
}

fn buf_contains_blob(buf: view<DiagBuffer>, blob_idx: usize) -> bool {
    let off = BLOB_OFFS[blob_idx];
    let n_len = BLOB_LENS[blob_idx];
    let b_len = buf.len;
    if n_len == 0 { return true; }
    if b_len < n_len { return false; }
    let mut i: usize = 0;
    while i + n_len <= b_len {
        let mut match_ok = true;
        let mut j: usize = 0;
        while j < n_len {
            let b = unsafe { *(buf.ptr + i + j) };
            if b != BLOBS[off + j] {
                match_ok = false;
                break;
            }
            j = j + 1;
        }
        if match_ok {
            return true;
        }
        i = i + 1;
    }
    false
}

pub fn main() -> i32 {
    let argv = alloc_argv(6);
    let ap = argv as *const StrView;
    set_arg_blob(argv, 0, 0);

    // 1. version
    set_arg_blob(argv, 1, 1);
    let mut out1 = diag_buf_new();
    let mut err1 = diag_buf_new();
    let rc1 = driver_run_args(ap, 2, mut_view(out1), mut_view(err1));
    let ok1 = rc1 == AX_EXIT_OK && buf_matches_blob(view(out1), 15) && err1.len == 0;
    diag_buf_free(mut_view(out1));
    diag_buf_free(mut_view(err1));
    if !ok1 { return 10; }

    // 2. --features
    set_arg_blob(argv, 1, 2);
    let mut out2 = diag_buf_new();
    let mut err2 = diag_buf_new();
    let rc2 = driver_run_args(ap, 2, mut_view(out2), mut_view(err2));
    let ok2 = rc2 == AX_EXIT_OK && buf_matches_blob(view(out2), 16) && err2.len == 0;
    diag_buf_free(mut_view(out2));
    diag_buf_free(mut_view(err2));
    if !ok2 { return 11; }

    // 3. help
    set_arg_blob(argv, 1, 3);
    let mut out3 = diag_buf_new();
    let mut err3 = diag_buf_new();
    let rc3 = driver_run_args(ap, 2, mut_view(out3), mut_view(err3));
    let ok3 = rc3 == AX_EXIT_OK && buf_matches_blob(view(out3), 17) && err3.len == 0;
    diag_buf_free(mut_view(out3));
    diag_buf_free(mut_view(err3));
    if !ok3 { return 12; }

    // 4. check --std-root=tests/driver --time-passes tests/driver/test.ax -> ok + timing lines
    set_arg_blob(argv, 1, 4);
    set_arg_blob(argv, 2, 13);
    set_arg_blob(argv, 3, 7);
    set_arg_blob(argv, 4, 10);
    let mut out4 = diag_buf_new();
    let mut err4 = diag_buf_new();
    let rc4 = driver_run_args(ap, 5, mut_view(out4), mut_view(err4));
    let ok4 = rc4 == AX_EXIT_OK &&
        err4.len == 0 &&
        buf_contains_blob(view(out4), 20) &&
        buf_contains_blob(view(out4), 21) &&
        buf_contains_blob(view(out4), 22) &&
        buf_contains_blob(view(out4), 23) &&
        buf_contains_blob(view(out4), 24) &&
        buf_contains_blob(view(out4), 25) &&
        buf_contains_blob(view(out4), 26);
    diag_buf_free(mut_view(out4));
    diag_buf_free(mut_view(err4));
    if !ok4 { return 13; }

    // 5. check --std-root=tests/driver tests/driver/error.ax -> human error matches axiom0 byte-for-byte
    set_arg_blob(argv, 1, 4);
    set_arg_blob(argv, 2, 13);
    set_arg_blob(argv, 3, 11);
    let mut out5 = diag_buf_new();
    let mut err5 = diag_buf_new();
    let rc5 = driver_run_args(ap, 4, mut_view(out5), mut_view(err5));
    let ok5 = rc5 == AX_EXIT_DIAG && out5.len == 0 && buf_matches_blob(view(err5), 18);
    diag_buf_free(mut_view(out5));
    diag_buf_free(mut_view(err5));
    if !ok5 { return 14; }

    // 6. check --std-root=tests/driver --json tests/driver/error.ax -> JSON error matches axiom0 byte-for-byte
    set_arg_blob(argv, 1, 4);
    set_arg_blob(argv, 2, 13);
    set_arg_blob(argv, 3, 6);
    set_arg_blob(argv, 4, 11);
    let mut out6 = diag_buf_new();
    let mut err6 = diag_buf_new();
    let rc6 = driver_run_args(ap, 5, mut_view(out6), mut_view(err6));
    let ok6 = rc6 == AX_EXIT_DIAG && out6.len == 0 && buf_matches_blob(view(err6), 19);
    diag_buf_free(mut_view(out6));
    diag_buf_free(mut_view(err6));
    if !ok6 { return 15; }

    // 7. run tests/lir/const.mir (standalone .mir verification + execution returns 42)
    set_arg_blob(argv, 1, 5);
    set_arg_blob(argv, 2, 12);
    let mut out7 = diag_buf_new();
    let mut err7 = diag_buf_new();
    let rc7 = driver_run_args(ap, 3, mut_view(out7), mut_view(err7));
    let ok7 = rc7 == 42 && err7.len == 0;
    diag_buf_free(mut_view(out7));
    diag_buf_free(mut_view(err7));
    if !ok7 { return 16; }

    0
}
""" % {
        "blob_table": byte_table("BLOBS", blob_bytes),
        "num_blobs": len(offs),
        "offs": ", ".join(str(x) for x in offs),
        "lens": ", ".join(str(x) for x in lens),
    }

    header = "// test: run\n// timeout: 1200\n// modes: interp native\n\n"
    full_text = header + prelude + "\n" + full_mods + "\n" + main_src
    return out_path, full_text.encode("utf-8")


def gen_commands_b_bundle(prelude, full_mods, axiom0):
    out_path = os.path.join(HERE, "qa_driver_commands_b.ax")
    if axiom0 is None:
        blobs = bc.extract_blobs_from_bundle(out_path, "BLOBS", "BLOB_OFFS", "BLOB_LENS")
        blob_bytes, offs, lens = pack_blobs(blobs)
    else:
        # Precompute reference COFF .obj and PE32+ .exe outputs from axiom0 build
        tmp_obj = os.path.join(HERE, "_gen_tmp_ret42.obj")
        tmp_exe = os.path.join(HERE, "_gen_tmp_ret42.exe")
        tmp_exe_sr = os.path.join(HERE, "_gen_tmp_ret42_sr.exe")
        tmp_exe_pkg = os.path.join(HERE, "_gen_tmp_hello.exe")
        try:
            run_axiom0(axiom0, ["build", "--emit=obj", "-o", tmp_obj, "tests/mc/frame/main_42.ax"], expect_rc=0)
            exp_obj = read_bytes(tmp_obj)
            run_axiom0(axiom0, ["build", "-o", tmp_exe, "tests/mc/frame/main_42.ax"], expect_rc=0)
            exp_exe = read_bytes(tmp_exe)
            run_axiom0(axiom0, ["build", "--stack-reserve=2097152", "-o", tmp_exe_sr, "tests/mc/frame/main_42.ax"], expect_rc=0)
            exp_exe_sr = read_bytes(tmp_exe_sr)
            run_axiom0(axiom0, ["build", "-o", tmp_exe_pkg, "tests/modules/hello/src/main.ax"], expect_rc=0)
            exp_exe_pkg = read_bytes(tmp_exe_pkg)
        finally:
            for p in (tmp_obj, tmp_exe, tmp_exe_sr, tmp_exe_pkg):
                if os.path.exists(p):
                    os.remove(p)

        blobs = [
            b"axiom0",                                     # 0
            b"check",                                      # 1
            b"run",                                        # 2
            b"build",                                      # 3
            b"--emit=obj",                                 # 4
            b"-o",                                         # 5
            b"out_mem.obj",                                # 6
            b"out_mem.exe",                                # 7
            b"--stack-reserve=2097152",                    # 8
            b"tests/mc/frame/main_42.ax",                  # 9
            b"tests/modules/hello/src/main.ax",            # 10
            b"tests/modules/mutual/src/main.ax",           # 11
            b"tests/modules/nested/src/main.ax",           # 12
            b"tests/modules/prelude_implicit/src/main.ax", # 13
            b"tests/modules/reexport/src/main.ax",         # 14
            b"tests/lir/add.mir",                          # 15: uninitialized local -> check/run rc 1
            exp_obj,                                       # 16
            exp_exe,                                       # 17
            exp_exe_sr,                                    # 18
            exp_exe_pkg,                                   # 19
            b"build/tmp_driver_test_",                     # 20
            b".exe",                                       # 21
            b"--interp",                                   # 22
            b"-O1",                                        # 23
            b"tests/opt/const_fold_run.ax",                # 24
            b"tests/driver/test.ax",                       # 25
            b"tests/lir/const.mir",                        # 26
        ]
        blob_bytes, offs, lens = pack_blobs(blobs)

    main_src = """\
module selfhost_driver_commands_b_test

use host_intrinsics.heap_alloc
use host_intrinsics.file_size
use host_intrinsics.monotonic_ns
use host_intrinsics.open
use host_intrinsics.close
use host_intrinsics.remove
use compiler.kernel.interner.StrView
use compiler.diag.format.DiagBuffer
use compiler.diag.format.diag_buf_new
use compiler.diag.format.diag_buf_free
use compiler.diag.format.diag_buf_push_bytes
use compiler.diag.format.diag_buf_push_u32
use compiler.obj.coff.CoffBuf
use compiler.obj.coff.coff_buf_with_capacity
use compiler.obj.coff.coff_buf_free
use compiler.driver.opts.AX_EXIT_OK
use compiler.driver.opts.AX_EXIT_DIAG
use compiler.driver.opts.DriverOptions
use compiler.driver.opts.opts_mul_usize
use compiler.driver.opts.sv_slot_set
use compiler.driver.opts.driver_options_alloc
use compiler.driver.opts.driver_options_dealloc
use compiler.driver.opts.driver_parse_cli
use compiler.driver.pipeline.driver_run_args
use compiler.driver.pipeline.driver_execute_build_into

@intrinsic unsafe fn address_of_mut<T>(val: T) -> *mut T { 0 as *mut T }

unsafe fn ptr_from_mut<T>(v: mut_view<T>) -> *mut T {
    address_of_mut(*v)
}

%(blob_table)s
const BLOB_OFFS: [%(num_blobs)d]usize = [%(offs)s];
const BLOB_LENS: [%(num_blobs)d]usize = [%(lens)s];

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

fn coff_buf_matches_blob(cb: view<CoffBuf>, blob_idx: usize) -> bool {
    let off = BLOB_OFFS[blob_idx];
    let blen = BLOB_LENS[blob_idx];
    if cb.len != blen {
        return false;
    }
    let mut i: usize = 0;
    while i < blen {
        let b = unsafe { *(cb.ptr + i) };
        if b != BLOBS[off + i] {
            return false;
        }
        i = i + 1;
    }
    true
}

fn test_packages_and_mir_errors() -> i32 {
    let argv = alloc_argv(6);
    let ap = argv as *const StrView;
    let exp_rcs: [5]i32 = [42, 30, 84, 1, 7];

    // Check and run all 5 multi-file module packages (blobs 10..14)
    let mut pkg_idx: usize = 10;
    while pkg_idx <= 14 {
        set_arg_blob(argv, 0, 0);
        set_arg_blob(argv, 1, 1);
        set_arg_blob(argv, 2, pkg_idx);
        let mut out_c = diag_buf_new();
        let mut err_c = diag_buf_new();
        let rcc = driver_run_args(ap, 3, mut_view(out_c), mut_view(err_c));
        let okc = rcc == AX_EXIT_OK && err_c.len == 0;
        diag_buf_free(mut_view(out_c));
        diag_buf_free(mut_view(err_c));
        if !okc {
            return (10 + (pkg_idx - 10)) as i32;
        }

        set_arg_blob(argv, 0, 0);
        set_arg_blob(argv, 1, 2);
        set_arg_blob(argv, 2, pkg_idx);
        let mut out_b = diag_buf_new();
        let mut err_b = diag_buf_new();
        let rc = driver_run_args(ap, 3, mut_view(out_b), mut_view(err_b));
        let exp_rc = exp_rcs[pkg_idx - 10];
        let ok = rc == exp_rc && err_b.len == 0;
        diag_buf_free(mut_view(out_b));
        diag_buf_free(mut_view(err_b));
        if !ok {
            return (30 + (pkg_idx - 10)) as i32;
        }
        pkg_idx = pkg_idx + 1;
    }

    // Full-std check tests/driver/test.ax
    set_arg_blob(argv, 0, 0);
    set_arg_blob(argv, 1, 1);
    set_arg_blob(argv, 2, 25);
    let mut out_t = diag_buf_new();
    let mut err_t = diag_buf_new();
    let rct = driver_run_args(ap, 3, mut_view(out_t), mut_view(err_t));
    let okt = rct == AX_EXIT_OK && out_t.len == 0 && err_t.len == 0;
    diag_buf_free(mut_view(out_t));
    diag_buf_free(mut_view(err_t));
    if !okt { return 15; }

    // Standalone .mir check tests/lir/const.mir
    set_arg_blob(argv, 0, 0);
    set_arg_blob(argv, 1, 1);
    set_arg_blob(argv, 2, 26);
    let mut out_cm = diag_buf_new();
    let mut err_cm = diag_buf_new();
    let rccm = driver_run_args(ap, 3, mut_view(out_cm), mut_view(err_cm));
    let okcm = rccm == AX_EXIT_OK && err_cm.len == 0;
    diag_buf_free(mut_view(out_cm));
    diag_buf_free(mut_view(err_cm));
    if !okcm { return 16; }

    // Full-std run --interp -O1 tests/opt/const_fold_run.ax
    set_arg_blob(argv, 0, 0);
    set_arg_blob(argv, 1, 2);
    set_arg_blob(argv, 2, 22);
    set_arg_blob(argv, 3, 23);
    set_arg_blob(argv, 4, 24);
    let mut out_cf = diag_buf_new();
    let mut err_cf = diag_buf_new();
    let rccf = driver_run_args(ap, 5, mut_view(out_cf), mut_view(err_cf));
    let okcf = rccf == AX_EXIT_OK && err_cf.len == 0;
    diag_buf_free(mut_view(out_cf));
    diag_buf_free(mut_view(err_cf));
    if !okcf { return 17; }

    // Negative check on uninitialized .mir (tests/lir/add.mir) -> AX_EXIT_DIAG
    set_arg_blob(argv, 0, 0);
    set_arg_blob(argv, 1, 1);
    set_arg_blob(argv, 2, 15);
    let mut out_m = diag_buf_new();
    let mut err_m = diag_buf_new();
    let rcm = driver_run_args(ap, 3, mut_view(out_m), mut_view(err_m));
    let okm = rcm == AX_EXIT_DIAG && err_m.len > 0;
    diag_buf_free(mut_view(out_m));
    diag_buf_free(mut_view(err_m));
    if !okm { return 18; }
    0
}

fn run_build_into_check(argv: *const StrView, argc: usize, exp_blob_idx: usize) -> bool {
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
    let mut bin_buf = coff_buf_with_capacity(1024);
    let bin_ptr = unsafe { ptr_from_mut(mut_view(bin_buf)) };
    let brc = unsafe {
        driver_execute_build_into(
            view(*dopts),
            mut_view(out_b),
            mut_view(err_b),
            bin_ptr,
            false
        )
    };
    let ok = brc == AX_EXIT_OK && err_b.len == 0 && coff_buf_matches_blob(view(bin_buf), exp_blob_idx);
    coff_buf_free(mut_view(bin_buf));
    diag_buf_free(mut_view(out_b));
    diag_buf_free(mut_view(err_b));
    unsafe { driver_options_dealloc(dopts); }
    ok
}

fn test_build_pipeline() -> i32 {
    let argv = alloc_argv(6);
    let ap = argv as *const StrView;

    // 1. build --emit=obj -o out_mem.obj tests/mc/frame/main_42.ax
    set_arg_blob(argv, 0, 0);
    set_arg_blob(argv, 1, 3);
    set_arg_blob(argv, 2, 4);
    set_arg_blob(argv, 3, 5);
    set_arg_blob(argv, 4, 6);
    set_arg_blob(argv, 5, 9);
    if !run_build_into_check(ap, 6, 16) { return 20; }

    // 2. build -o out_mem.exe tests/mc/frame/main_42.ax
    set_arg_blob(argv, 0, 0);
    set_arg_blob(argv, 1, 3);
    set_arg_blob(argv, 2, 5);
    set_arg_blob(argv, 3, 7);
    set_arg_blob(argv, 4, 9);
    if !run_build_into_check(ap, 5, 17) { return 21; }

    // 3. build --stack-reserve=2097152 -o out_mem.exe tests/mc/frame/main_42.ax
    set_arg_blob(argv, 0, 0);
    set_arg_blob(argv, 1, 3);
    set_arg_blob(argv, 2, 8);
    set_arg_blob(argv, 3, 5);
    set_arg_blob(argv, 4, 7);
    set_arg_blob(argv, 5, 9);
    if !run_build_into_check(ap, 6, 18) { return 22; }

    // 4. build -o out_mem.exe tests/modules/hello/src/main.ax (multi-file package native build)
    set_arg_blob(argv, 0, 0);
    set_arg_blob(argv, 1, 3);
    set_arg_blob(argv, 2, 5);
    set_arg_blob(argv, 3, 7);
    set_arg_blob(argv, 4, 10);
    if !run_build_into_check(ap, 5, 19) { return 23; }

    // 5. Real disk output via driver_run_args with unique monotonic_ns filename + cleanup
    let mut path_buf = diag_buf_new();
    let pfx = blob_sv(20);
    let sfx = blob_sv(21);
    diag_buf_push_bytes(mut_view(path_buf), pfx.ptr, pfx.len);
    let stamp = (monotonic_ns() & 0xFFFFFFFFu64) as u32;
    diag_buf_push_u32(mut_view(path_buf), stamp);
    diag_buf_push_bytes(mut_view(path_buf), sfx.ptr, sfx.len);
    let tmp_sv = StrView { ptr: path_buf.ptr as *const u8, len: path_buf.len };

    set_arg_blob(argv, 0, 0);
    set_arg_blob(argv, 1, 3);
    set_arg_blob(argv, 2, 5);
    sv_slot_set(argv, 3, view(tmp_sv));
    set_arg_blob(argv, 4, 9);
    let mut out_d = diag_buf_new();
    let mut err_d = diag_buf_new();
    let drc = driver_run_args(ap, 5, mut_view(out_d), mut_view(err_d));
    let mut disk_ok = drc == AX_EXIT_OK && err_d.len == 0;
    if disk_ok {
        let fd = unsafe { open(tmp_sv.ptr, tmp_sv.len, 0u32) };
        if fd < 0i64 {
            disk_ok = false;
        } else {
            let fsz = file_size(fd);
            let _ = close(fd);
            if (fsz as usize) != BLOB_LENS[17] {
                disk_ok = false;
            }
        }
        let _ = unsafe { remove(tmp_sv.ptr, tmp_sv.len) };
    }
    diag_buf_free(mut_view(out_d));
    diag_buf_free(mut_view(err_d));
    diag_buf_free(mut_view(path_buf));
    if !disk_ok { return 24; }

    0
}

pub fn main() -> i32 {
    let r1 = test_packages_and_mir_errors();
    if r1 != 0 { return r1; }
    let r2 = test_build_pipeline();
    if r2 != 0 { return r2; }
    0
}
""" % {
        "blob_table": byte_table("BLOBS", blob_bytes),
        "num_blobs": len(offs),
        "offs": ", ".join(str(x) for x in offs),
        "lens": ", ".join(str(x) for x in lens),
    }

    header = "// test: run\n// timeout: 1200\n// modes: native\n\n"
    full_text = header + prelude + "\n" + full_mods + "\n" + main_src
    return out_path, full_text.encode("utf-8")


def gen_boundary_edges_bundle(prelude, light_mods, axiom0):
    out_path = os.path.join(HERE, "qa_driver_boundary_edges.ax")
    if axiom0 is None:
        blobs = bc.extract_blobs_from_bundle(out_path, "BLOBS", "BLOB_OFFS", "BLOB_LENS")
        blob_bytes, offs, lens = pack_blobs(blobs)
    else:
        _, _, exp_ver_extra = run_axiom0(axiom0, ["version", "extra_arg"], expect_rc=2)
        _, _, exp_feat_extra = run_axiom0(axiom0, ["--features", "--all"], expect_rc=2)
        _, _, exp_emit_empty = run_axiom0(axiom0, ["inspect", "--emit=", "tests/driver/test.ax"], expect_rc=2)
        _, _, exp_inspect_two = run_axiom0(
            axiom0,
            ["inspect", "--emit=ast", "tests/driver/test.ax", "tests/driver/error.ax"],
            expect_rc=2,
        )

        blobs = [
            exp_ver_extra,                                                 # 0
            exp_feat_extra,                                                # 1
            exp_emit_empty,                                                # 2
            exp_inspect_two,                                               # 3
            b"axiom0: unknown target 'x86_64-unknown-linux-gnu' [AX_DRIVER_UNKNOWN_TARGET]\n",  # 4
            b"axiom0",                                                     # 5
            b"version",                                                    # 6
            b"extra_arg",                                                  # 7
            b"--features",                                                 # 8
            b"--all",                                                      # 9
            b"inspect",                                                    # 10
            b"--emit=",                                                    # 11
            b"--emit=ast",                                                 # 12
            b"tests/driver/test.ax",                                       # 13
            b"tests/driver/error.ax",                                      # 14
            b"check",                                                      # 15
            b"--target=x86_64-unknown-linux-gnu",                          # 16
            b"run",                                                        # 17
            b"--",                                                         # 18
            b"-O1",                                                        # 19
            b"--json",                                                     # 20
            b"--unknown-opt",                                              # 21
            b"src\\nested\\dir\\item.ax",                                  # 22
            b"nested.dir.item",                                            # 23
            b"standalone.ax",                                              # 24
            b"standalone",                                                 # 25
            b"nonexistent_input_file_xyz.ax",                              # 26
            b"nonexistent_std_dir_xyz",                                    # 27
            b"tests/modules/hello",                                        # 28
            b"hello",                                                      # 29
        ]
        blob_bytes, offs, lens = pack_blobs(blobs)

    main_src = """\
module selfhost_driver_boundary_edges_test

use host_intrinsics.heap_alloc
use host_intrinsics.heap_free
use compiler.kernel.arena.Arena
use compiler.kernel.arena.arena_new
use compiler.kernel.arena.arena_destroy
use compiler.kernel.interner.StrView
use compiler.diag.code.AX_IO_FILE_NOT_FOUND
use compiler.diag.code.AX_DRIVER_NO_STD
use compiler.diag.emitter.DiagSink
use compiler.diag.emitter.diag_sink_init
use compiler.diag.emitter.diag_sink_free
use compiler.diag.emitter.diag_sink_error_count
use compiler.diag.format.DiagBuffer
use compiler.diag.format.diag_buf_new
use compiler.diag.format.diag_buf_free
use compiler.driver.opts.AX_EXIT_OK
use compiler.driver.opts.AX_EXIT_USAGE
use compiler.driver.opts.CMD_RUN
use compiler.driver.opts.DriverOptions
use compiler.driver.opts.opts_mul_usize
use compiler.driver.opts.sv_slot_get
use compiler.driver.opts.sv_slot_set
use compiler.driver.opts.driver_options_alloc
use compiler.driver.opts.driver_options_dealloc
use compiler.driver.opts.driver_parse_cli
use compiler.driver.opts.derive_module_path
use compiler.driver.opts.Project
use compiler.driver.opts.project_alloc
use compiler.driver.opts.project_dealloc
use compiler.driver.opts.project_discover

@intrinsic fn size_of<T>() -> usize { 0 }
@intrinsic fn align_of<T>() -> usize { 0 }

unsafe fn diag_sink_alloc() -> *mut DiagSink {
    let bytes = size_of<DiagSink>();
    let raw = heap_alloc(bytes, align_of<DiagSink>());
    let mut i: usize = 0;
    while i < bytes {
        *(raw + i) = 0u8;
        i = i + 1;
    }
    let p = raw as *mut DiagSink;
    diag_sink_init(mut_view(*p));
    p
}

unsafe fn diag_sink_dealloc(p: *mut DiagSink) {
    if (p as usize) == 0 { return; }
    diag_sink_free(mut_view(*p));
    heap_free(p as *mut u8, size_of<DiagSink>(), align_of<DiagSink>());
}

%(blob_table)s
const BLOB_OFFS: [%(num_blobs)d]usize = [%(offs)s];
const BLOB_LENS: [%(num_blobs)d]usize = [%(lens)s];

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

fn buf_matches_blob(buf: view<DiagBuffer>, blob_idx: usize) -> bool {
    let off = BLOB_OFFS[blob_idx];
    let blen = BLOB_LENS[blob_idx];
    if buf.len != blen {
        return false;
    }
    let mut i: usize = 0;
    while i < blen {
        let b = unsafe { *(buf.ptr + i) };
        if b != BLOBS[off + i] {
            return false;
        }
        i = i + 1;
    }
    true
}

fn sv_matches_blob(sv: view<StrView>, blob_idx: usize) -> bool {
    let off = BLOB_OFFS[blob_idx];
    let blen = BLOB_LENS[blob_idx];
    if sv.len != blen {
        return false;
    }
    let mut i: usize = 0;
    while i < blen {
        let b = unsafe { *(sv.ptr + i) };
        if b != BLOBS[off + i] {
            return false;
        }
        i = i + 1;
    }
    true
}

fn check_err_case(argv: *const StrView, argc: usize, exp_rc: i32, exp_err_blob: usize) -> bool {
    let dopts = unsafe { driver_options_alloc() };
    let mut out_buf = diag_buf_new();
    let mut err_buf = diag_buf_new();
    let rc = unsafe { driver_parse_cli(argv, argc, mut_view(*dopts), mut_view(out_buf), mut_view(err_buf)) };
    let ok = rc == exp_rc && out_buf.len == 0 && buf_matches_blob(view(err_buf), exp_err_blob);
    diag_buf_free(mut_view(out_buf));
    diag_buf_free(mut_view(err_buf));
    unsafe { driver_options_dealloc(dopts); }
    ok
}

fn test_cli_edge_cases() -> i32 {
    let a = alloc_argv(10);
    let ap = a as *const StrView;
    set_arg_blob(a, 0, 5); // "axiom0"

    // 1. `axiom0 version extra_arg` -> AX_EXIT_USAGE + exact stderr
    set_arg_blob(a, 1, 6);
    set_arg_blob(a, 2, 7);
    if !check_err_case(ap, 3, AX_EXIT_USAGE, 0) { return 10; }

    // 2. `axiom0 --features --all` -> AX_EXIT_USAGE + exact stderr
    set_arg_blob(a, 1, 8);
    set_arg_blob(a, 2, 9);
    if !check_err_case(ap, 3, AX_EXIT_USAGE, 1) { return 11; }

    // 3. `axiom0 inspect --emit= tests/driver/test.ax` -> AX_EXIT_USAGE + emitters list
    set_arg_blob(a, 1, 10);
    set_arg_blob(a, 2, 11);
    set_arg_blob(a, 3, 13);
    if !check_err_case(ap, 4, AX_EXIT_USAGE, 2) { return 12; }

    // 4. `axiom0 inspect --emit=ast tests/driver/test.ax tests/driver/error.ax` -> AX_EXIT_USAGE
    set_arg_blob(a, 1, 10);
    set_arg_blob(a, 2, 12);
    set_arg_blob(a, 3, 13);
    set_arg_blob(a, 4, 14);
    if !check_err_case(ap, 5, AX_EXIT_USAGE, 3) { return 13; }

    // 5. `axiom0 check --target=x86_64-unknown-linux-gnu tests/driver/test.ax` -> exact target error
    set_arg_blob(a, 1, 15);
    set_arg_blob(a, 2, 16);
    set_arg_blob(a, 3, 13);
    if !check_err_case(ap, 4, AX_EXIT_USAGE, 4) { return 14; }

    // 6. `axiom0 run tests/driver/test.ax -- -O1 --json --unknown-opt`
    // Flags after `--` must not be parsed as compiler options; they must land in `run_args`.
    set_arg_blob(a, 1, 17);
    set_arg_blob(a, 2, 13);
    set_arg_blob(a, 3, 18);
    set_arg_blob(a, 4, 19);
    set_arg_blob(a, 5, 20);
    set_arg_blob(a, 6, 21);
    let dopts = unsafe { driver_options_alloc() };
    let mut out_b = diag_buf_new();
    let mut err_b = diag_buf_new();
    let rc = unsafe { driver_parse_cli(ap, 7, mut_view(*dopts), mut_view(out_b), mut_view(err_b)) };
    let mut dash_ok = unsafe {
        rc == AX_EXIT_OK &&
        (*dopts).cmd == CMD_RUN &&
        !(*dopts).opt_O1 &&
        !(*dopts).json &&
        (*dopts).dash_dash &&
        (*dopts).run_argc == 3 &&
        err_b.len == 0
    };
    if dash_ok {
        let r0 = unsafe { sv_slot_get((*dopts).run_args as *const StrView, 0) };
        let r1 = unsafe { sv_slot_get((*dopts).run_args as *const StrView, 1) };
        let r2 = unsafe { sv_slot_get((*dopts).run_args as *const StrView, 2) };
        if !sv_matches_blob(view(r0), 19) || !sv_matches_blob(view(r1), 20) || !sv_matches_blob(view(r2), 21) {
            dash_ok = false;
        }
    }
    diag_buf_free(mut_view(out_b));
    diag_buf_free(mut_view(err_b));
    unsafe { driver_options_dealloc(dopts); }
    if !dash_ok { return 15; }
    0
}

fn test_path_and_discovery_seams() -> i32 {
    let mut arena = arena_new();

    // 1. Backslash path in derive_module_path: `src\\nested\\dir\\item.ax` -> `nested.dir.item`
    let b22 = blob_sv(22);
    let mp_win = derive_module_path(view(b22), mut_view(arena));
    if !sv_matches_blob(view(mp_win), 23) {
        arena_destroy(mut_view(arena));
        return 20;
    }

    // 2. Standalone filename without `src/`: `standalone.ax` -> `standalone`
    let b24 = blob_sv(24);
    let mp_root = derive_module_path(view(b24), mut_view(arena));
    if !sv_matches_blob(view(mp_root), 25) {
        arena_destroy(mut_view(arena));
        return 21;
    }
    arena_destroy(mut_view(arena));

    let empty = StrView { ptr: 0 as *const u8, len: 0 };

    // 3. project_discover with nonexistent input file -> AX_IO_FILE_NOT_FOUND
    let sink1 = unsafe { diag_sink_alloc() };
    let p1 = unsafe { project_alloc() };
    let b26 = blob_sv(26);
    let ok1 = unsafe { project_discover(view(b26), view(empty), mut_view(*p1), mut_view(*sink1)) };
    let mut err1_ok = unsafe { !ok1 && diag_sink_error_count(view(*sink1)) == 1 };
    if err1_ok {
        let d0_code = unsafe { (*(*sink1).diags).code.v };
        if d0_code != AX_IO_FILE_NOT_FOUND {
            err1_ok = false;
        }
    }
    unsafe {
        project_dealloc(p1);
        diag_sink_dealloc(sink1);
    }
    if !err1_ok { return 22; }

    // 4. project_discover with nonexistent explicit `--std-root` -> AX_DRIVER_NO_STD
    let sink2 = unsafe { diag_sink_alloc() };
    let p2 = unsafe { project_alloc() };
    let b13 = blob_sv(13);
    let b27 = blob_sv(27);
    let ok2 = unsafe { project_discover(view(b13), view(b27), mut_view(*p2), mut_view(*sink2)) };
    let mut err2_ok = unsafe { !ok2 && diag_sink_error_count(view(*sink2)) == 1 };
    if err2_ok {
        let d0_code = unsafe { (*(*sink2).diags).code.v };
        if d0_code != AX_DRIVER_NO_STD {
            err2_ok = false;
        }
    }
    unsafe {
        project_dealloc(p2);
        diag_sink_dealloc(sink2);
    }
    if !err2_ok { return 23; }

    // 5. project_discover when given package root directory directly (`tests/modules/hello`)
    let sink3 = unsafe { diag_sink_alloc() };
    let p3 = unsafe { project_alloc() };
    let b28 = blob_sv(28);
    let ok3 = unsafe { project_discover(view(b28), view(empty), mut_view(*p3), mut_view(*sink3)) };
    let dir_ok = unsafe {
        ok3 &&
        (*p3).is_package &&
        (*p3).has_manifest &&
        sv_matches_blob(view((*p3).manifest.name), 29) &&
        (*p3).file_count == 5 &&
        diag_sink_error_count(view(*sink3)) == 0
    };
    unsafe {
        project_dealloc(p3);
        diag_sink_dealloc(sink3);
    }
    if !dir_ok { return 24; }

    0
}

pub fn main() -> i32 {
    let r1 = test_cli_edge_cases();
    if r1 != 0 { return r1; }
    let r2 = test_path_and_discovery_seams();
    if r2 != 0 { return r2; }
    0
}
""" % {
        "blob_table": byte_table("BLOBS", blob_bytes),
        "num_blobs": len(offs),
        "offs": ", ".join(str(x) for x in offs),
        "lens": ", ".join(str(x) for x in lens),
    }

    header = "// test: run\n// timeout: 1200\n// modes: interp native\n\n"
    full_text = header + prelude + "\n" + light_mods + "\n" + main_src
    return out_path, full_text.encode("utf-8")


def main():
    check_mode = ("--check" in sys.argv[1:]) or ("check" in sys.argv[1:])
    refresh_goldens = "--refresh-goldens" in sys.argv[1:]
    axiom0 = find_exe(["build/axiom0.exe", "build/axiom0"]) if refresh_goldens else None
    for i, a in enumerate(sys.argv[1:]):
        if a == "--axiom0" and i + 2 <= len(sys.argv[1:]):
            axiom0 = sys.argv[i + 2]

    prelude = build_prelude_text()
    light_mods = assemble_modules(LIGHT_MODULES)
    full_mods = assemble_modules(FULL_MODULES)

    outputs = []
    outputs.append(gen_cli_and_project_bundle(prelude, light_mods, axiom0))
    outputs.append(gen_boundary_edges_bundle(prelude, light_mods, axiom0))

    inspect_cases_a = [
        ("--emit=tokens", False, "tests/driver/test.ax"),
        ("--emit=ast", False, "tests/driver/test.ax"),
        ("--emit=resolved", False, "tests/driver/test.ax"),
        ("--emit=hir", False, "tests/driver/test.ax"),
        ("--emit=thir", False, "tests/driver/test.ax"),
        ("--emit=mir", False, "tests/driver/test.ax"),
        ("--emit=mir-opt", True, "tests/driver/test.ax"),
        ("--emit=mir", False, "tests/lir/const.mir"),
    ]
    outputs.append(gen_inspect_diff_bundle(
        "qa_driver_inspect_diff_a.ax",
        "interp native",
        prelude,
        full_mods,
        axiom0,
        inspect_cases_a,
        fast_std=True,
    ))

    inspect_cases_b = [
        ("--emit=tokens", False, "tests/mc/frame/main_42.ax"),
        ("--emit=ast", False, "tests/mc/frame/main_42.ax"),
        ("--emit=resolved", False, "tests/mc/frame/main_42.ax"),
        ("--emit=hir", False, "tests/mc/frame/main_42.ax"),
        ("--emit=thir", False, "tests/mc/frame/main_42.ax"),
        ("--emit=mir", False, "tests/mc/frame/main_42.ax"),
        ("--emit=lir", False, "tests/mc/frame/main_42.ax"),
        ("--emit=mi", False, "tests/mc/frame/main_42.ax"),
        ("--emit=mc", False, "tests/mc/frame/main_42.ax"),
        ("--emit=obj", False, "tests/mc/frame/main_42.ax"),
        ("--emit=lir", False, "tests/lir/const.mir"),
        ("--emit=mi", False, "tests/lir/const.mir"),
        ("--emit=mc", False, "tests/lir/const.mir"),
        ("--emit=hir", False, "tests/modules/hello/src/main.ax"),
    ]
    outputs.append(gen_inspect_diff_bundle(
        "qa_driver_inspect_diff_b.ax",
        "native",
        prelude,
        full_mods,
        axiom0,
        inspect_cases_b,
        fast_std=False,
    ))

    outputs.append(gen_commands_a_bundle(prelude, full_mods, axiom0))
    outputs.append(gen_commands_b_bundle(prelude, full_mods, axiom0))
    bc.write_or_check_bundles(outputs, check_mode, root=ROOT)


if __name__ == "__main__":
    main()

