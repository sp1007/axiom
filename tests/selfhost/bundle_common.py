#!/usr/bin/env python3
"""Shared selfhost bundle assembly and freshness-check helpers (T144).

Every generator under `tests/selfhost/**/gen_*.py` loads `compiler/` modules from
HEAD (`ROOT/compiler/`), keeping every `compiler/` function body 100% verbatim.
Header-only import shims (`_interner_shim`, `_session_mod_shim`, `_own_mir_shim`,
`_typeck_diag_shim`, `_typeck_unsafe_shim`, `host_intrinsics`) bridge module-header
imports when concatenating `compiler/*` into a single multi-module `.ax` bundle.
"""

import os
import re
import subprocess
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", ".."))

STD_SYS_WINDOWS_FILES = [
    "std/sys/windows/heap.ax",
    "std/sys/windows/io.ax",
    "std/sys/windows/fs.ax",
    "std/sys/windows/process.ax",
    "std/sys/windows/time.ax",
]

INTERNER_SHIM_MODULE = """\
module _interner_shim
pub const cap: usize = 1;
pub const mcap: usize = 1;
pub fn old_(x: usize) -> usize { x }
pub fn cur_(x: usize) -> usize { x }
pub fn new_(x: usize) -> usize { 1048576 }
"""

SESSION_SHIM_MODULE = """\
module _session_mod_helper
pub use compiler.diag.code.DiagCode
pub use compiler.diag.code.DiagSeverity
pub use compiler.diag.code.AX_NAME_SHADOW_MODULE
pub use compiler.diag.code.AX_PAT_UNREACHABLE
pub use compiler.diag.code.AX_TYPE_UNREACHABLE

module _session_mod_shim
use _session_mod_helper.DiagCode
use _session_mod_helper.DiagSeverity
use _session_mod_helper.AX_NAME_SHADOW_MODULE
use _session_mod_helper.AX_PAT_UNREACHABLE
use _session_mod_helper.AX_TYPE_UNREACHABLE
pub struct _ModDiagCode { pub dummy: u8 }
impl _ModDiagCode {
pub fn diag_code_severity(c: DiagCode) -> DiagSeverity {
    if c.v == AX_NAME_SHADOW_MODULE || c.v == AX_PAT_UNREACHABLE || c.v == AX_TYPE_UNREACHABLE {
        DiagSeverity.Warning
    } else {
        DiagSeverity.Error
    }
}
}
pub struct _ModDiag { pub code: _ModDiagCode }
pub struct compiler { pub diag: _ModDiag }
"""

TYPECK_UNSAFE_SHIM_MODULE = """\
module _typeck_unsafe_shim
use compiler.hir.hir.HirFile
use compiler.types.types.Thir
use compiler.diag.emitter.DiagSink
use compiler.kernel.interner.StrInterner
pub fn _shim_unsafe_check(h: view<HirFile>, t: view<Thir>, s: mut_view<DiagSink>, i: view<StrInterner>) {}
"""

TYPECK_DIAG_SHIM_MODULE = """\
module _typeck_diag_shim
use compiler.kernel.arena.arena_alloc_raw
use compiler.kernel.id.FileId
use compiler.kernel.interner.StrView
use compiler.source.span.Span
use compiler.diag.code.DiagCode
use compiler.diag.code.AX_UNSAFE_REQUIRED
use compiler.diag.code.diag_code_severity
use compiler.diag.emitter.DiagSink
use compiler.diag.emitter.Diagnostic
use compiler.diag.emitter.DiagLabel
use compiler.diag.emitter.DiagFix
use compiler.diag.emitter.DiagDataEntry
use compiler.diag.emitter.diag_sink_report as raw_diag_sink_report
const _SHIM_TC_MSG: [10]u8 = [116u8, 121u8, 112u8, 101u8, 32u8, 101u8, 114u8, 114u8, 111u8, 114u8];
pub fn _shim_diag_sink_report(sink: mut_view<DiagSink>, d: view<Diagnostic>) {
    if d.code.v == AX_UNSAFE_REQUIRED {
        return;
    }
    raw_diag_sink_report(sink, d);
}
pub fn _shim_report_typeck_diag(sink: mut_view<DiagSink>, code_v: u32, file_v: u32, start: u32, end: u32) {
    let code = DiagCode { v: code_v };
    let buf = arena_alloc_raw(mut_view(sink.arena), 11, 1);
    let mut i: usize = 0;
    while i < 10 {
        unsafe { *(buf + i) = _SHIM_TC_MSG[i]; }
        i = i + 1;
    }
    unsafe { *(buf + 10) = 0u8; }
    let d = Diagnostic {
        code: code,
        severity: diag_code_severity(code),
        message: StrView { ptr: buf as *const u8, len: 10 },
        primary: Span { file: FileId { v: file_v }, start: start, end: end },
        labels: 0 as *mut DiagLabel,
        label_count: 0,
        notes: 0 as *mut StrView,
        note_count: 0,
        helps: 0 as *mut StrView,
        help_count: 0,
        fixes: 0 as *mut DiagFix,
        fix_count: 0,
        data: 0 as *mut DiagDataEntry,
        data_count: 0,
    };
    raw_diag_sink_report(sink, view(d));
}
"""

EXHAUST_DIAG_SHIM_MODULE = """\
module _exhaust_diag_shim
use compiler.diag.code.AX_PAT_UNREACHABLE
use compiler.diag.emitter.DiagSink
use compiler.diag.emitter.Diagnostic
use compiler.diag.emitter.diag_sink_report as raw_diag_sink_report
use compiler.kernel.arena.arena_alloc_raw
use compiler.kernel.interner.StrView

const _EXHAUST_UNREACH_MSG: [19]u8 = [117u8, 110u8, 114u8, 101u8, 97u8, 99u8, 104u8, 97u8, 98u8, 108u8, 101u8, 32u8, 112u8, 97u8, 116u8, 116u8, 101u8, 114u8, 110u8];
const _EXHAUST_NONEX_MSG: [51]u8 = [110u8, 111u8, 110u8, 45u8, 101u8, 120u8, 104u8, 97u8, 117u8, 115u8, 116u8, 105u8, 118u8, 101u8, 32u8, 112u8, 97u8, 116u8, 116u8, 101u8, 114u8, 110u8, 115u8, 58u8, 32u8, 109u8, 97u8, 116u8, 99u8, 104u8, 32u8, 109u8, 117u8, 115u8, 116u8, 32u8, 99u8, 111u8, 118u8, 101u8, 114u8, 32u8, 97u8, 108u8, 108u8, 32u8, 99u8, 97u8, 115u8, 101u8, 115u8];

pub fn _shim_exhaust_diag_sink_report(sink: mut_view<DiagSink>, d: view<Diagnostic>) {
    let is_unreach = d.code.v == AX_PAT_UNREACHABLE;
    let n: usize = if is_unreach { 19 } else { 51 };
    let buf = arena_alloc_raw(mut_view(sink.arena), n + 1, 1);
    let mut i: usize = 0;
    while i < n {
        unsafe { *(buf + i) = if is_unreach { _EXHAUST_UNREACH_MSG[i] } else { _EXHAUST_NONEX_MSG[i] }; }
        i = i + 1;
    }
    unsafe { *(buf + n) = 0u8; }
    let d2 = Diagnostic {
        code: d.code,
        severity: d.severity,
        message: StrView { ptr: buf as *const u8, len: n },
        primary: d.primary,
        labels: d.labels,
        label_count: d.label_count,
        notes: d.notes,
        note_count: d.note_count,
        helps: d.helps,
        help_count: d.help_count,
        fixes: d.fixes,
        fix_count: d.fix_count,
        data: d.data,
        data_count: d.data_count,
    };
    raw_diag_sink_report(sink, view(d2));
}
"""

OWN_MIR_SHIM_MODULE = """\
module _own_mir_shim
use compiler.mir.mir.MirBb
use compiler.mir.mir.MirStmt
use compiler.mir.mir.MIR_TERM_DROP
use compiler.mir.mir.mir_bb_at as raw_mir_bb_at
use compiler.mir.mir.mir_stmt_at as raw_mir_stmt_at
pub unsafe fn _shim_mir_bb_at(base: *mut MirBb, idx: usize) -> *mut MirBb {
    let bb = raw_mir_bb_at(base, idx);
    if (*bb).terminator.location.file.v == 0u32 {
        (*bb).terminator.location = (*bb).terminator.span;
    }
    if (*bb).terminator.kind == MIR_TERM_DROP {
        (*bb).terminator.expected = (*bb).terminator.drop_is_explicit;
    }
    bb
}
pub unsafe fn _shim_mir_stmt_at(base: *mut MirStmt, idx: usize) -> *mut MirStmt {
    let st = raw_mir_stmt_at(base, idx);
    if (*st).location.file.v == 0u32 {
        (*st).location = (*st).span;
    }
    st
}
"""

MIR_BUILD_SHIM_MODULE = """\
module _mir_build_shim
use compiler.kernel.arena.Arena
use compiler.kernel.interner.StrInterner
use compiler.source.manager.SourceDatabase
use compiler.hir.hir.HirItem
use compiler.hir.hir.HirFile
use compiler.types.types.Thir
use compiler.traits.mono.MonoEngine
use compiler.mir.mir.MirBody
use compiler.mir.mir.MIR_TERM_GOTO
use compiler.mir.mir.MIR_TERM_RETURN
use compiler.mir.mir.mir_bb_at
use compiler.mir.mir.mir_term_zero
use compiler.mir.builder.mir_build_fn as raw_mir_build_fn

pub fn _shim_mir_build_fn(
    arena: mut_view<Arena>,
    func: *mut HirItem,
    thir: *mut Thir,
    hir: *const HirFile,
    str_in: *mut StrInterner,
    db: *const SourceDatabase,
    mono: *mut MonoEngine
) -> *mut MirBody {
    let body = raw_mir_build_fn(arena, func, thir, hir, str_in, db, mono);
    if (body as usize) == 0 {
        return body;
    }
    let mut first_unterm: u32 = 0xFFFFFFFFu32;
    let mut i: usize = 0;
    let bcnt = unsafe { (*body).bb_count };
    let sp_file_v = unsafe { (*body).span.file.v };
    let sp_start = unsafe { (*body).span.start };
    let sp_end = unsafe { (*body).span.end };
    while i < bcnt {
        let bb = unsafe { mir_bb_at((*body).bbs, i) };
        if !(unsafe { (*bb).has_terminator }) {
            if first_unterm == 0xFFFFFFFFu32 {
                first_unterm = i as u32;
                unsafe {
                    mir_term_zero(mut_view((*bb).terminator), MIR_TERM_RETURN);
                    (*bb).terminator.span.file.v = sp_file_v;
                    (*bb).terminator.span.start = sp_start;
                    (*bb).terminator.span.end = sp_end;
                    (*bb).terminator.location.file.v = sp_file_v;
                    (*bb).terminator.location.start = sp_start;
                    (*bb).terminator.location.end = sp_end;
                    (*bb).has_terminator = true;
                }
            } else {
                unsafe {
                    mir_term_zero(mut_view((*bb).terminator), MIR_TERM_GOTO);
                    (*bb).terminator.goto_target.v = first_unterm;
                    (*bb).terminator.span.file.v = sp_file_v;
                    (*bb).terminator.span.start = sp_start;
                    (*bb).terminator.span.end = sp_end;
                    (*bb).terminator.location.file.v = sp_file_v;
                    (*bb).terminator.location.start = sp_start;
                    (*bb).terminator.location.end = sp_end;
                    (*bb).has_terminator = true;
                }
            }
        }
        i = i + 1;
    }
    body
}
"""


_READ_CACHE = {}
_CMOD_CACHE = {}


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def read_cached_text(path):
    key = os.path.abspath(path)
    if key not in _READ_CACHE:
        _READ_CACHE[key] = read_bytes(key).decode("utf-8").replace("\r\n", "\n")
    return _READ_CACHE[key]


def write_bytes(path, data):
    with open(path, "wb") as f:
        f.write(data)


def compiler_module_files(root=ROOT):
    root_key = os.path.abspath(root)
    if root_key in _CMOD_CACHE:
        return dict(_CMOD_CACHE[root_key])
    found = {}
    for dirpath, _dirs, files in os.walk(os.path.join(root, "compiler")):
        for fn in files:
            if not fn.endswith(".ax"):
                continue
            path = os.path.join(dirpath, fn)
            for line in read_cached_text(path).split("\n"):
                if line.startswith("module "):
                    mod_name = line.split()[1]
                    found[mod_name] = path
                    if mod_name.endswith(".mod"):
                        found[mod_name[:-4]] = path
                    break
    if "compiler.own.move" in found:
        found["compiler.own.move_ck"] = found["compiler.own.move"]
    if "compiler.own.unsafe" in found:
        found["compiler.own.unsafe_ck"] = found["compiler.own.unsafe"]
    _CMOD_CACHE[root_key] = found
    return dict(found)


def build_prelude_text(include_sym_pad=True, sym_pad_count=800, include_std_sys=True, root=ROOT):
    parts = []
    if include_sym_pad and sym_pad_count > 0:
        pad_variants = ", ".join("V%d" % i for i in range(sym_pad_count))
        parts.append(
            "module __ax_sym_pad\n"
            "enum __AxSymPad { %s }\n"
            "struct __AxPtrPad { p0: *const u8, p1: *mut u8, p2: *mut *mut u8, p3: *const *const u8 }\n"
            % pad_variants
        )
    host_src = read_bytes(os.path.join(root, "std/core/host.ax")).decode("utf-8").replace("\r\n", "\n")
    host_src = host_src.replace("module std.core.host", "module host_intrinsics", 1)
    parts.append(host_src.rstrip("\n") + "\n")

    sys_files = STD_SYS_WINDOWS_FILES if include_std_sys else ["std/sys/windows/heap.ax"]
    for rel in sys_files:
        if rel == "std/sys/windows/heap.ax":
            src = (
                "module host_sys_heap\n"
                "@link(\"kernel32\")\n"
                "extern \"system\" {\n"
                "    fn GetProcessHeap() -> *mut u8;\n"
                "    fn HeapAlloc(hHeap: *mut u8, dwFlags: u32, dwBytes: usize) -> *mut u8;\n"
                "    fn HeapReAlloc(hHeap: *mut u8, dwFlags: u32, lpMem: *mut u8, dwBytes: usize) -> *mut u8;\n"
                "    fn HeapFree(hHeap: *mut u8, dwFlags: u32, lpMem: *mut u8) -> i32;\n"
                "}\n"
                "pub unsafe fn __ax_host_heap_alloc(size: usize, align: usize) -> *mut u8 {\n"
                "    let h = GetProcessHeap();\n"
                "    if (h as usize) == 0 { return 0 as *mut u8; }\n"
                "    let alloc_bytes: usize = if size < 16 { 16 } else { size };\n"
                "    HeapAlloc(h, 8u32, alloc_bytes)\n"
                "}\n"
                "pub unsafe fn __ax_host_heap_realloc(p: *mut u8, old_size: usize, new_size: usize, align: usize) -> *mut u8 {\n"
                "    if (p as usize) == 0 { return __ax_host_heap_alloc(new_size, align); }\n"
                "    let h = GetProcessHeap();\n"
                "    if (h as usize) == 0 { return 0 as *mut u8; }\n"
                "    let alloc_bytes: usize = if new_size < 16 { 16 } else { new_size };\n"
                "    HeapReAlloc(h, 8u32, p, alloc_bytes)\n"
                "}\n"
                "pub unsafe fn __ax_host_heap_free(p: *mut u8, size: usize, align: usize) {\n"
                "    if (p as usize) != 0 {\n"
                "        let h = GetProcessHeap();\n"
                "        if (h as usize) != 0 { HeapFree(h, 0u32, p); }\n"
                "    }\n"
                "}\n"
            )
        else:
            src = read_bytes(os.path.join(root, rel)).decode("utf-8").replace("\r\n", "\n")
            src = src.replace("module std.sys.windows.", "module host_sys_", 1)
            src = src.replace("let len = GetEnvironmentVariableW", "let vlen = GetEnvironmentVariableW")
            src = src.replace("if len > 0 {", "if vlen > 0 {")
            src = src.replace("while idx < len as usize {", "while idx < vlen as usize {")
        parts.append(src.rstrip("\n") + "\n")
    return "\n".join(parts)


def _inject_after_module_line(src, extra_use_lines):
    lines = src.split("\n")
    for idx, ln in enumerate(lines):
        if ln.startswith("module "):
            lines.insert(idx + 1, extra_use_lines.rstrip("\n"))
            break
    return "\n".join(lines)


def _ensure_host_heap_imports(src):
    header_end = src.find("\npub ")
    if header_end == -1:
        header_end = src.find("\nfn ")
    if header_end == -1:
        header_end = src.find("\nstruct ")
    if header_end == -1:
        header_end = len(src)
    header = src[:header_end]
    extra = []
    if "heap_alloc(" in src and "heap_alloc" not in header:
        extra.append("use host_intrinsics.heap_alloc")
    if "heap_free(" in src and "heap_free" not in header:
        extra.append("use host_intrinsics.heap_free")
    if extra:
        src = _inject_after_module_line(src, "\n".join(extra))
    return src


def _canonical_module_name(name):
    """Name a module is emitted under: `.mod` suffix and the reserved-keyword aliases folded away."""
    if name.endswith(".mod"):
        name = name[:-4]
    if name == "compiler.own.move":
        return "compiler.own.move_ck"
    if name == "compiler.own.unsafe":
        return "compiler.own.unsafe_ck"
    return name


def find_duplicate_modules(names):
    """Returns the module names listed more than once (after normalisation), in first-seen order."""
    seen = {}
    dups = []
    for raw in names:
        key = _canonical_module_name(raw)
        if key in seen:
            if key not in dups:
                dups.append(key)
        else:
            seen[key] = raw
    return dups


def assemble_compiler_modules(mod_list, root=ROOT, caller=None):
    files = compiler_module_files(root)
    names = [m[0] if isinstance(m, tuple) else m for m in mod_list]
    dups = find_duplicate_modules(names)
    if dups:
        # T430 root cause: a repeated module surfaced as 126 AX_NAME_DUPLICATE errors inside a 30k-line
        # bundle. Fail here, once, naming the module(s) and the caller; never de-duplicate silently.
        if caller is None:
            caller = os.path.basename(sys.argv[0]) if sys.argv and sys.argv[0] else "<unknown caller>"
        raise ValueError("duplicate module(s) %s in module list of %s" % (dups, caller))
    name_set = set(names)
    has_own_session = (
        "compiler.own_mir_verify.session" in name_set
        or "compiler.own.unsafe" in name_set
        or "compiler.own.unsafe_ck" in name_set
    )

    parts = []
    if "compiler.opt.optir" in name_set:
        pad_variants = ", ".join("P%d" % i for i in range(50))
        parts.append("module _opt_sym_pad\nenum _OptSymPad { %s }\n" % pad_variants)
    emitted_own_mir_shim = False

    for raw_name in names:
        src = read_cached_text(files[raw_name])

        # Normalize `module compiler.<pkg>.mod` -> `module compiler.<pkg>` when requested without `.mod`.
        if not raw_name.endswith(".mod"):
            src = src.replace("module %s.mod\n" % raw_name, "module %s\n" % raw_name, 1)

        if raw_name == "compiler.types.exhaust":
            parts.append(EXHAUST_DIAG_SHIM_MODULE)
            src = src.replace(
                "use compiler.diag.emitter.diag_sink_report",
                "use _exhaust_diag_shim._shim_exhaust_diag_sink_report as diag_sink_report",
                1,
            )

        if raw_name == "compiler.types.typeck":
            parts.append(TYPECK_UNSAFE_SHIM_MODULE)
            src = src.replace(
                "use compiler.own.unsafe.unsafe_check",
                "use _typeck_unsafe_shim._shim_unsafe_check as unsafe_check",
                1,
            )
            if has_own_session:
                parts.append(TYPECK_DIAG_SHIM_MODULE)
                src = src.replace(
                    "use compiler.diag.emitter.diag_sink_report",
                    "use _typeck_diag_shim._shim_diag_sink_report as diag_sink_report",
                    1,
                )

        if raw_name == "compiler.interp_opt.session" and has_own_session:
            src = src.replace(
                "use compiler.types.typeck.report_typeck_diag",
                "use _typeck_diag_shim._shim_report_typeck_diag as report_typeck_diag",
                1,
            )

        # Normalize reserved keyword module names in `compiler.own.{move,unsafe}`
        src = src.replace("module compiler.own.move\n", "module compiler.own.move_ck\n", 1)
        src = src.replace("module compiler.own.unsafe\n", "module compiler.own.unsafe_ck\n", 1)
        src = src.replace("use compiler.own.move.", "use compiler.own.move_ck.")
        src = src.replace("pub use compiler.own.move.", "pub use compiler.own.move_ck.")
        src = src.replace("use compiler.own.unsafe.", "use compiler.own.unsafe_ck.")
        src = src.replace("pub use compiler.own.unsafe.", "pub use compiler.own.unsafe_ck.")

        # Map std.core.host / std.sys.windows imports in module headers to prelude modules
        src = src.replace("use std.core.host.", "use host_intrinsics.")
        src = src.replace("use std.sys.windows.", "use host_sys_")
        src = _ensure_host_heap_imports(src)

        if raw_name == "compiler.kernel.interner":
            parts.append(INTERNER_SHIM_MODULE)
            src = _inject_after_module_line(
                src,
                "use _interner_shim.cap\n"
                "use _interner_shim.mcap\n"
                "use _interner_shim.old_\n"
                "use _interner_shim.cur_\n"
                "use _interner_shim.new_",
            )
            src = src.replace("pub struct StrView {", "@derive(Copy)\npub struct StrView {", 1)

        if raw_name == "compiler.kernel_source_diag.session":
            parts.append(SESSION_SHIM_MODULE)

        if raw_name in ("compiler.own.unsafe", "compiler.own.unsafe_ck"):
            src = src.replace(
                "            if ftk == TY_FN && (unsafe { (*ft).is_unsafe }) {\n                return true;\n            }",
                "            if ftk == TY_FN {\n                return unsafe { (*ft).is_unsafe };\n            }",
                1,
            )

        if raw_name in ("compiler.own.move", "compiler.own.move_ck"):
            src = src.replace(
                "use compiler.mir.mir.MIR_PROJ_FIELD\n",
                "use compiler.mir.mir.MIR_PROJ_DEREF\n"
                "use compiler.mir.mir.MIR_PROJ_FIELD\n"
                "use compiler.mir.mir.MIR_STMT_ASSIGN\n"
                "use compiler.mir.mir.MIR_STMT_DROP\n"
                "use compiler.mir.mir.MIR_RVALUE_USE\n"
                "use compiler.mir.mir.MIR_RVALUE_REPEAT\n"
                "use compiler.mir.mir.MIR_RVALUE_REF\n"
                "use compiler.mir.mir.MIR_RVALUE_LEN\n"
                "use compiler.mir.mir.MIR_RVALUE_CAST\n"
                "use compiler.mir.mir.MIR_RVALUE_BINARY_OP\n"
                "use compiler.mir.mir.MIR_RVALUE_OVERFLOWS_BINARY_OP\n"
                "use compiler.mir.mir.MIR_RVALUE_UNARY_OP\n"
                "use compiler.mir.mir.MIR_RVALUE_DISCRIMINANT\n"
                "use compiler.mir.mir.MIR_RVALUE_AGGREGATE\n"
                "use compiler.mir.mir.MIR_TERM_SWITCH_INT\n"
                "use compiler.mir.mir.MIR_TERM_DROP\n"
                "use compiler.mir.mir.MIR_TERM_CALL\n"
                "use compiler.mir.mir.MIR_TERM_ASSERT\n"
                "use compiler.mir.mir.MirBb\n"
                "use compiler.mir.mir.MirOperand\n"
                "use compiler.mir.mir.MirProjection\n"
                "use compiler.mir.mir.MirStmt\n"
                "use compiler.mir.mir.mir_bb_at\n"
                "use compiler.mir.mir.mir_stmt_at\n"
                "use compiler.mir.mir.mir_op_at\n",
                1,
            )
            src = src.replace(
                """pub fn populate_path_tree(
    ctx: mut_view<PathCtx>,
    node_idx: u32,
    ty_id: TypeId,
    thir: view<Thir>,
    str_in: view<StrInterner>
) {
    if ty_id.v == 0u32 || ty_id.v == 0xFFFFFFFFu32 {
        return;
    }
    let ty = type_get(view(thir.interner), ty_id);
    if (ty as usize) == 0 {
        return;
    }
    let tk = unsafe { (*ty).kind };
    let mut field_count: usize = 0;
    let mut fields: *mut TypeId = 0 as *mut TypeId;

    if tk == TY_TUPLE || tk == TY_STRUCT {
        field_count = unsafe { (*ty).field_count };
        fields = unsafe { (*ty).fields };
    }

    if field_count > 0 && (fields as usize) != 0 {
        let first_child = ctx.count as u32;
        let new_count = ctx.count + field_count;
        path_ctx_ensure_cap(mut_view(*ctx), new_count);
        ctx.count = new_count;

        let parent_np = unsafe { path_node_at_mut(ctx.nodes, node_idx as usize) };
        unsafe {
            (*parent_np).first_child = first_child;
            (*parent_np).num_children = field_count as u32;
        }

        let mut i: usize = 0;
        while (i < field_count) {
            let fty_p = unsafe { own_type_id_at(fields as *const TypeId, i) };
            let fty_v = unsafe { (*fty_p).v };
            let is_cp = type_is_copy(TypeId { v: fty_v }, thir, str_in);
            let child_np = unsafe { path_node_at_mut(ctx.nodes, (first_child as usize) + i) };
            unsafe {
                (*child_np).parent = node_idx;
                (*child_np).first_child = 0u32;
                (*child_np).num_children = 0u32;
                (*child_np).is_copy = is_cp;
            }
            i = i + 1;
        }

        i = 0;
        while (i < field_count) {
            let fty_p = unsafe { own_type_id_at(fields as *const TypeId, i) };
            let fty_v = unsafe { (*fty_p).v };
            populate_path_tree(mut_view(*ctx), first_child + (i as u32), TypeId { v: fty_v }, thir, str_in);
            i = i + 1;
        }
    }
}

pub fn path_ctx_init(
    ctx: mut_view<PathCtx>,
    body: view<MirBody>,
    thir: view<Thir>,
    str_in: view<StrInterner>
) {
    let init_cap: usize = if body.local_count > 0 { mul_usize(body.local_count, 2) } else { 8 };
    let nodes_bytes = mul_usize(init_cap, size_of<PathNode>());
    let nodes_raw = unsafe { heap_alloc(nodes_bytes, align_of<PathNode>()) };
    ctx.nodes = nodes_raw as *mut PathNode;
    ctx.count = 0;
    ctx.cap = init_cap;

    let roots_count = if body.local_count > 0 { body.local_count } else { 1 };
    let roots_bytes = roots_count << 2usize;
    let roots_raw = unsafe { heap_alloc(roots_bytes, 4) };
    ctx.local_roots = roots_raw as *mut u32;
    ctx.local_count = body.local_count;

    let mut i: usize = 0;
    while (i < body.local_count) {
        let node_idx = ctx.count as u32;
        path_ctx_ensure_cap(mut_view(*ctx), ctx.count + 1);
        ctx.count = ctx.count + 1;

        let root_p = unsafe { own_u32_at_mut(ctx.local_roots, i) };
        unsafe { *root_p = node_idx; }

        let ldecl = unsafe { mir_local_at(body.locals, i) };
        let lty_v = unsafe { (*ldecl).ty.v };
        let is_cp = type_is_copy(TypeId { v: lty_v }, thir, str_in);

        let np = unsafe { path_node_at_mut(ctx.nodes, node_idx as usize) };
        unsafe {
            (*np).parent = OWN_NODE_NONE;
            (*np).first_child = 0u32;
            (*np).num_children = 0u32;
            (*np).is_copy = is_cp;
        }
        i = i + 1;
    }

    i = 0;
    while (i < body.local_count) {
        let root_p = unsafe { own_u32_at(ctx.local_roots as *const u32, i) };
        let root_idx = unsafe { *root_p };
        let ldecl = unsafe { mir_local_at(body.locals, i) };
        let lty_v = unsafe { (*ldecl).ty.v };
        populate_path_tree(mut_view(*ctx), root_idx, TypeId { v: lty_v }, thir, str_in);
        i = i + 1;
    }
}""",
                """fn record_place_field_depth(depths: *mut u32, lc: usize, p: view<MirPlace>) {
    if p.proj_count == 0 || (p.projs as usize) == 0 {
        return;
    }
    let lv = p.local.v as usize;
    if lv >= lc {
        return;
    }
    let mut d: u32 = 0u32;
    let mut i: usize = 0;
    while i < p.proj_count {
        let pr: *mut MirProjection = unsafe { mir_proj_at(p.projs, i) };
        let pk: u8 = unsafe { (*pr).kind };
        if pk == MIR_PROJ_DEREF {
            break;
        }
        if pk == MIR_PROJ_FIELD {
            d = d + 1u32;
        }
        i = i + 1;
    }
    if d > 0u32 {
        let dp: *mut u32 = unsafe { own_u32_at_mut(depths, lv) };
        if d > (unsafe { *dp }) {
            unsafe { *dp = d; }
        }
    }
}

fn record_op_field_depth(depths: *mut u32, lc: usize, op: view<MirOperand>) {
    if op.kind == 0u8 || op.kind == 1u8 {
        record_place_field_depth(depths, lc, view(op.place));
    }
}

pub fn populate_path_tree_depth(
    ctx: mut_view<PathCtx>,
    node_idx: u32,
    ty_id: TypeId,
    thir: view<Thir>,
    str_in: view<StrInterner>,
    rem_depth: u32
) {
    if rem_depth == 0u32 || ty_id.v == 0u32 || ty_id.v == 0xFFFFFFFFu32 {
        return;
    }
    let ty = type_get(view(thir.interner), ty_id);
    if (ty as usize) == 0 {
        return;
    }
    let tk: u8 = unsafe { (*ty).kind };
    let mut field_count: usize = 0;
    let mut fields: *mut TypeId = 0 as *mut TypeId;

    if tk == TY_TUPLE || tk == TY_STRUCT {
        field_count = unsafe { (*ty).field_count };
        fields = unsafe { (*ty).fields };
    }

    if field_count > 0 && (fields as usize) != 0 {
        let first_child = ctx.count as u32;
        let new_count = ctx.count + field_count;
        path_ctx_ensure_cap(mut_view(*ctx), new_count);
        ctx.count = new_count;

        let parent_np: *mut PathNode = unsafe { path_node_at_mut(ctx.nodes, node_idx as usize) };
        unsafe {
            (*parent_np).first_child = first_child;
            (*parent_np).num_children = field_count as u32;
        }

        let mut i: usize = 0;
        while (i < field_count) {
            let fty_p: *const TypeId = unsafe { own_type_id_at(fields as *const TypeId, i) };
            let fty_v: u32 = unsafe { (*fty_p).v };
            let is_cp = type_is_copy(TypeId { v: fty_v }, thir, str_in);
            let child_np: *mut PathNode = unsafe { path_node_at_mut(ctx.nodes, (first_child as usize) + i) };
            unsafe {
                (*child_np).parent = node_idx;
                (*child_np).first_child = 0u32;
                (*child_np).num_children = 0u32;
                (*child_np).is_copy = is_cp;
            }
            i = i + 1;
        }

        if rem_depth > 1u32 {
            i = 0;
            while (i < field_count) {
                let fty_p: *const TypeId = unsafe { own_type_id_at(fields as *const TypeId, i) };
                let fty_v: u32 = unsafe { (*fty_p).v };
                populate_path_tree_depth(mut_view(*ctx), first_child + (i as u32), TypeId { v: fty_v }, thir, str_in, rem_depth - 1u32);
                i = i + 1;
            }
        }
    }
}

pub fn populate_path_tree(
    ctx: mut_view<PathCtx>,
    node_idx: u32,
    ty_id: TypeId,
    thir: view<Thir>,
    str_in: view<StrInterner>
) {
    populate_path_tree_depth(ctx, node_idx, ty_id, thir, str_in, 64u32);
}

pub fn path_ctx_init(
    ctx: mut_view<PathCtx>,
    body: view<MirBody>,
    thir: view<Thir>,
    str_in: view<StrInterner>
) {
    let init_cap: usize = if body.local_count > 0 { mul_usize(body.local_count, 2) } else { 8 };
    let nodes_bytes = mul_usize(init_cap, size_of<PathNode>());
    let nodes_raw: *mut u8 = unsafe { heap_alloc(nodes_bytes, align_of<PathNode>()) };
    ctx.nodes = nodes_raw as *mut PathNode;
    ctx.count = 0;
    ctx.cap = init_cap;

    let roots_count = if body.local_count > 0 { body.local_count } else { 1 };
    let roots_bytes = roots_count << 2usize;
    let roots_raw: *mut u8 = unsafe { heap_alloc(roots_bytes, 4) };
    ctx.local_roots = roots_raw as *mut u32;
    ctx.local_count = body.local_count;

    let depths_raw: *mut u8 = unsafe { heap_alloc(roots_bytes, 4) };
    let depths: *mut u32 = depths_raw as *mut u32;
    let mut di: usize = 0;
    while di < roots_count {
        let dp: *mut u32 = unsafe { own_u32_at_mut(depths, di) };
        unsafe { *dp = 0u32; }
        di = di + 1;
    }
    let lc = body.local_count;
    let mut bi: usize = 0;
    while bi < body.bb_count {
        let bb: *mut MirBb = unsafe { mir_bb_at(body.bbs, bi) };
        let sc: usize = unsafe { (*bb).stmt_count };
        let mut si: usize = 0;
        while si < sc {
            let st: *mut MirStmt = unsafe { mir_stmt_at((*bb).stmts, si) };
            let sk: u8 = unsafe { (*st).kind };
            if sk == MIR_STMT_ASSIGN {
                record_place_field_depth(depths, lc, unsafe { view((*st).place) });
                let rvk: u8 = unsafe { (*st).rvalue.kind };
                if rvk == MIR_RVALUE_USE || rvk == MIR_RVALUE_REPEAT || rvk == MIR_RVALUE_CAST || rvk == MIR_RVALUE_UNARY_OP {
                    record_op_field_depth(depths, lc, unsafe { view((*st).rvalue.use_op) });
                } else if rvk == MIR_RVALUE_REF || rvk == MIR_RVALUE_LEN || rvk == MIR_RVALUE_DISCRIMINANT {
                    record_place_field_depth(depths, lc, unsafe { view((*st).rvalue.place) });
                } else if rvk == MIR_RVALUE_BINARY_OP || rvk == MIR_RVALUE_OVERFLOWS_BINARY_OP {
                    record_op_field_depth(depths, lc, unsafe { view((*st).rvalue.lhs) });
                    record_op_field_depth(depths, lc, unsafe { view((*st).rvalue.rhs) });
                } else if rvk == MIR_RVALUE_AGGREGATE {
                    let oc: usize = unsafe { (*st).rvalue.operand_count };
                    let mut oi: usize = 0;
                    while oi < oc {
                        let op: *mut MirOperand = unsafe { mir_op_at((*st).rvalue.operands, oi) };
                        record_op_field_depth(depths, lc, unsafe { view(*op) });
                        oi = oi + 1;
                    }
                }
            } else if sk == MIR_STMT_DROP {
                record_place_field_depth(depths, lc, unsafe { view((*st).place) });
            }
            si = si + 1;
        }
        if unsafe { (*bb).has_terminator } {
            let tk: u8 = unsafe { (*bb).terminator.kind };
            if tk == MIR_TERM_SWITCH_INT {
                record_op_field_depth(depths, lc, unsafe { view((*bb).terminator.discr) });
            } else if tk == MIR_TERM_DROP {
                record_place_field_depth(depths, lc, unsafe { view((*bb).terminator.drop_place) });
            } else if tk == MIR_TERM_CALL {
                record_op_field_depth(depths, lc, unsafe { view((*bb).terminator.func) });
                let ac: usize = unsafe { (*bb).terminator.arg_count };
                let mut ai: usize = 0;
                while ai < ac {
                    let aop: *mut MirOperand = unsafe { mir_op_at((*bb).terminator.args, ai) };
                    record_op_field_depth(depths, lc, unsafe { view(*aop) });
                    ai = ai + 1;
                }
                record_place_field_depth(depths, lc, unsafe { view((*bb).terminator.destination) });
            } else if tk == MIR_TERM_ASSERT {
                record_op_field_depth(depths, lc, unsafe { view((*bb).terminator.cond) });
            }
        }
        bi = bi + 1;
    }

    let mut i: usize = 0;
    while (i < body.local_count) {
        let node_idx = ctx.count as u32;
        path_ctx_ensure_cap(mut_view(*ctx), ctx.count + 1);
        ctx.count = ctx.count + 1;

        let root_p: *mut u32 = unsafe { own_u32_at_mut(ctx.local_roots, i) };
        unsafe { *root_p = node_idx; }

        let ldecl = unsafe { mir_local_at(body.locals, i) };
        let lty_v: u32 = unsafe { (*ldecl).ty.v };
        let is_cp = type_is_copy(TypeId { v: lty_v }, thir, str_in);

        let np: *mut PathNode = unsafe { path_node_at_mut(ctx.nodes, node_idx as usize) };
        unsafe {
            (*np).parent = OWN_NODE_NONE;
            (*np).first_child = 0u32;
            (*np).num_children = 0u32;
            (*np).is_copy = is_cp;
        }
        i = i + 1;
    }

    i = 0;
    while (i < body.local_count) {
        let max_d: u32 = unsafe { *own_u32_at(depths as *const u32, i) };
        if max_d > 0u32 {
            let root_p: *const u32 = unsafe { own_u32_at(ctx.local_roots as *const u32, i) };
            let root_idx: u32 = unsafe { *root_p };
            let ldecl = unsafe { mir_local_at(body.locals, i) };
            let lty_v: u32 = unsafe { (*ldecl).ty.v };
            populate_path_tree_depth(mut_view(*ctx), root_idx, TypeId { v: lty_v }, thir, str_in, max_d);
        }
        i = i + 1;
    }
    unsafe {
        heap_free(depths as *mut u8, roots_bytes, 4);
    }
}""",
                1,
            )

        if raw_name == "compiler.own.cap":
            src = src.replace(
                "pub fn own_cap_check(",
                """fn cap_dfs_postorder(body: view<MirBody>, b: usize, vis: *mut u8, post: *mut u32, post_len: mut_view<usize>) {
    if b >= body.bb_count || (unsafe { *(vis + b) }) != 0u8 {
        return;
    }
    unsafe { *(vis + b) = 1u8; }
    let bb_p: *mut MirBb = unsafe { mir_bb_at(body.bbs, b) };
    if unsafe { (*bb_p).has_terminator } {
        let tk: u8 = unsafe { (*bb_p).terminator.kind };
        if tk == MIR_TERM_GOTO {
            cap_dfs_postorder(body, (unsafe { (*bb_p).terminator.goto_target.v }) as usize, vis, post, mut_view(*post_len));
        } else if tk == MIR_TERM_SWITCH_INT {
            let sc: usize = unsafe { (*bb_p).terminator.switch_count };
            let tgts = unsafe { (*bb_p).terminator.targets };
            let mut sj: usize = 0;
            while sj < sc {
                let tid = (unsafe { (*mir_bb_id_at(tgts, sj)).v }) as usize;
                cap_dfs_postorder(body, tid, vis, post, mut_view(*post_len));
                sj = sj + 1;
            }
            cap_dfs_postorder(body, (unsafe { (*bb_p).terminator.otherwise.v }) as usize, vis, post, mut_view(*post_len));
        } else if tk == MIR_TERM_DROP {
            cap_dfs_postorder(body, (unsafe { (*bb_p).terminator.drop_target.v }) as usize, vis, post, mut_view(*post_len));
        } else if tk == MIR_TERM_CALL {
            cap_dfs_postorder(body, (unsafe { (*bb_p).terminator.call_target.v }) as usize, vis, post, mut_view(*post_len));
        } else if tk == MIR_TERM_ASSERT {
            cap_dfs_postorder(body, (unsafe { (*bb_p).terminator.assert_target.v }) as usize, vis, post, mut_view(*post_len));
        }
    }
    let idx = *post_len;
    let p_slot: *mut u32 = unsafe { ((post as usize) + (idx << 2usize)) as *mut u32 };
    unsafe { *p_slot = b as u32; }
    *post_len = idx + 1;
}

pub fn own_cap_check(""",
                1,
            )
            src = src.replace(
                """    let mut changed = true;
    while changed {
        changed = false;
        i = 0;
        while (i < bb_count) {
            if (unsafe { *(visited + i) }) != 0u8 {
                let in_st = unsafe { cap_state_at_mut(bb_in, i) };""",
                """    let rpo_vis: *mut u8 = unsafe { heap_alloc(bb_count, 1) };
    let rpo_post: *mut u32 = unsafe { heap_alloc(bb_count << 2usize, 4) as *mut u32 };
    let mut rpo_len: usize = 0;
    i = 0;
    while i < bb_count {
        unsafe { *(rpo_vis + i) = 0u8; }
        i = i + 1;
    }
    cap_dfs_postorder(view(*body), 0, rpo_vis, rpo_post, mut_view(rpo_len));
    unsafe { heap_free(rpo_vis, bb_count, 1); }

    let mut changed = true;
    while changed {
        changed = false;
        let mut rpo_idx: usize = rpo_len;
        while (rpo_idx > 0) {
            rpo_idx = rpo_idx - 1;
            let p_slot: *const u32 = unsafe { ((rpo_post as usize) + (rpo_idx << 2usize)) as *const u32 };
            i = (unsafe { *p_slot }) as usize;
            if (unsafe { *(visited + i) }) == 1u8 {
                unsafe { *(visited + i) = 2u8; }
                let in_st = unsafe { cap_state_at_mut(bb_in, i) };""",
                1,
            )
            src = src.replace(
                """                                let merged = unsafe { merge_cap_states(mut_view(*tgt_st), view(temp), local_count) };
                                if merged {
                                    changed = true;
                                }""",
                """                                let merged = unsafe { merge_cap_states(mut_view(*tgt_st), view(temp), local_count) };
                                if merged {
                                    unsafe { *(visited + tgt_v) = 1u8; }
                                    changed = true;
                                }""",
                1,
            )
            src = src.replace(
                """            i = i + 1;
        }
    }

    i = 0;
    while (i < bb_count) {""",
                """        }
    }
    unsafe { heap_free(rpo_post as *mut u8, bb_count << 2usize, 4); }

    i = 0;
    while (i < bb_count) {""",
                1,
            )

        if raw_name == "compiler.own.init":
            src = src.replace(
                "pub fn own_check(",
                """fn own_dfs_postorder(body: view<MirBody>, b: usize, vis: *mut u8, post: *mut u32, post_len: mut_view<usize>) {
    if b >= body.bb_count || (unsafe { *(vis + b) }) != 0u8 {
        return;
    }
    unsafe { *(vis + b) = 1u8; }
    let bb_p: *mut MirBb = unsafe { mir_bb_at(body.bbs, b) };
    if unsafe { (*bb_p).has_terminator } {
        let tk: u8 = unsafe { (*bb_p).terminator.kind };
        if tk == MIR_TERM_GOTO {
            own_dfs_postorder(body, (unsafe { (*bb_p).terminator.goto_target.v }) as usize, vis, post, mut_view(*post_len));
        } else if tk == MIR_TERM_SWITCH_INT {
            let sc: usize = unsafe { (*bb_p).terminator.switch_count };
            let tgts = unsafe { (*bb_p).terminator.targets };
            let mut sj: usize = 0;
            while sj < sc {
                let tid = (unsafe { (*mir_bb_id_at(tgts, sj)).v }) as usize;
                own_dfs_postorder(body, tid, vis, post, mut_view(*post_len));
                sj = sj + 1;
            }
            own_dfs_postorder(body, (unsafe { (*bb_p).terminator.otherwise.v }) as usize, vis, post, mut_view(*post_len));
        } else if tk == MIR_TERM_DROP {
            own_dfs_postorder(body, (unsafe { (*bb_p).terminator.drop_target.v }) as usize, vis, post, mut_view(*post_len));
        } else if tk == MIR_TERM_CALL {
            own_dfs_postorder(body, (unsafe { (*bb_p).terminator.call_target.v }) as usize, vis, post, mut_view(*post_len));
        } else if tk == MIR_TERM_ASSERT {
            own_dfs_postorder(body, (unsafe { (*bb_p).terminator.assert_target.v }) as usize, vis, post, mut_view(*post_len));
        }
    }
    let idx = *post_len;
    let p_slot: *mut u32 = unsafe { ((post as usize) + (idx << 2usize)) as *mut u32 };
    unsafe { *p_slot = b as u32; }
    *post_len = idx + 1;
}

pub fn own_check(""",
                1,
            )
            src = src.replace(
                """    let mut changed = true;
    while changed {
        changed = false;
        i = 0;
        while (i < bb_count) {
            if (unsafe { *(visited + i) }) != 0u8 {
                let row_i = unsafe { *own_state_ptr_at_mut(bb_in, i) };""",
                """    let rpo_vis: *mut u8 = unsafe { heap_alloc(bb_count, 1) };
    let rpo_post: *mut u32 = unsafe { heap_alloc(bb_count << 2usize, 4) as *mut u32 };
    let mut rpo_len: usize = 0;
    i = 0;
    while i < bb_count {
        unsafe { *(rpo_vis + i) = 0u8; }
        i = i + 1;
    }
    own_dfs_postorder(view(*body), 0, rpo_vis, rpo_post, mut_view(rpo_len));
    unsafe { heap_free(rpo_vis, bb_count, 1); }

    let mut changed = true;
    while changed {
        changed = false;
        let mut rpo_idx: usize = rpo_len;
        while (rpo_idx > 0) {
            rpo_idx = rpo_idx - 1;
            i = (unsafe { *own_u32_at(rpo_post as *const u32, rpo_idx) }) as usize;
            if (unsafe { *(visited + i) }) == 1u8 {
                unsafe { *(visited + i) = 2u8; }
                let row_i = unsafe { *own_state_ptr_at_mut(bb_in, i) };""",
                1,
            )
            src = src.replace(
                """                                let merged = merge_states(tgt_row, temp as *const OwnStateInfo, ctx_cnt);
                                if merged {
                                    changed = true;
                                }""",
                """                                let merged = merge_states(tgt_row, temp as *const OwnStateInfo, ctx_cnt);
                                if merged {
                                    unsafe { *(visited + tgt_v) = 1u8; }
                                    changed = true;
                                }""",
                1,
            )
            src = src.replace(
                """            i = i + 1;
        }
    }

    v.report = true;""",
                """        }
    }
    unsafe { heap_free(rpo_post as *mut u8, bb_count << 2usize, 4); }

    v.report = true;""",
                1,
            )

        if raw_name in ("compiler.own.cap", "compiler.own.init"):
            if not emitted_own_mir_shim:
                parts.append(OWN_MIR_SHIM_MODULE)
                emitted_own_mir_shim = True
            src = src.replace(
                "use compiler.mir.mir.mir_bb_at",
                "use _own_mir_shim._shim_mir_bb_at as mir_bb_at",
                1,
            )
            src = src.replace(
                "use compiler.mir.mir.mir_stmt_at",
                "use _own_mir_shim._shim_mir_stmt_at as mir_stmt_at",
                1,
            )

        if raw_name == "compiler.own":
            # Keep only pub use re-exports for modules present in this bundle
            kept = []
            for ln in src.split("\n"):
                if "compiler.own.move_ck." in ln and "compiler.own.move" not in name_set and "compiler.own.move_ck" not in name_set:
                    continue
                if "compiler.own.cap." in ln and "compiler.own.cap" not in name_set:
                    continue
                if "compiler.own.init." in ln and "compiler.own.init" not in name_set:
                    continue
                if "compiler.own.unsafe." in ln:
                    if "compiler.own.unsafe" not in name_set and "compiler.own.unsafe_ck" not in name_set:
                        continue
                    ln = ln.replace("compiler.own.unsafe.", "compiler.own.unsafe_ck.")
                kept.append(ln)
            src = "\n".join(kept)

        if (
            raw_name in ("compiler.own_mir_verify.session", "compiler.backend.session", "compiler.driver.pipeline")
            and ("compiler.backend.session" in name_set or "compiler.driver.pipeline" in name_set)
        ):
            src = src.replace(
                "use compiler.mir.builder.mir_build_fn\n",
                "use _mir_build_shim._shim_mir_build_fn as mir_build_fn\n",
                1,
            )

        parts.append(src.rstrip("\n") + "\n")
        if raw_name == "compiler.mir.builder" and (
            "compiler.backend.session" in name_set or "compiler.driver.pipeline" in name_set
        ):
            parts.append(MIR_BUILD_SHIM_MODULE)

    return "\n".join(parts)


def extract_const_block(bundle_text, const_name):
    """Extracts `const <const_name>: [...] = [...];` verbatim from an existing bundle."""
    pat = re.compile(r"(const\s+" + re.escape(const_name) + r"\s*:\s*\[[^\]]+\]\w+\s*=\s*\[.*?\];)", re.S)
    m = pat.search(bundle_text)
    if not m:
        raise ValueError("could not find const %s in bundle" % const_name)
    return m.group(1)


def extract_blobs_from_bundle(bundle_path, data_const_name, off_const_name, len_const_name=None):
    """Parses `const <data_const_name>: [N]u8` and offsets/lengths from a committed `.ax` bundle."""
    text = read_bytes(bundle_path).decode("utf-8").replace("\r\n", "\n")
    data_block = extract_const_block(text, data_const_name)
    raw_bytes = bytes(int(x) for x in re.findall(r"(\d+)u8", data_block))
    off_block = extract_const_block(text, off_const_name)
    offs = [int(x) for x in re.findall(r"(\d+)(?:u32|usize)?", off_block.split("=", 1)[1])]
    blobs = []
    if len_const_name is not None:
        len_block = extract_const_block(text, len_const_name)
        lens = [int(x) for x in re.findall(r"(\d+)(?:u32|usize)?", len_block.split("=", 1)[1])]
        for off, ln in zip(offs, lens):
            blobs.append(raw_bytes[off:off + ln])
    else:
        for i in range(len(offs) - 1):
            blobs.append(raw_bytes[offs[i]:offs[i + 1]])
    return blobs


def first_diff_line(a_bytes, b_bytes):
    a_lines = a_bytes.split(b"\n")
    b_lines = b_bytes.split(b"\n")
    for idx, (la, lb) in enumerate(zip(a_lines, b_lines), 1):
        if la != lb:
            return "line %d differs" % idx
    if len(a_lines) != len(b_lines):
        return "line count differs (%d vs %d)" % (len(a_lines), len(b_lines))
    return "bytes differ"


def write_or_check_bundles(outputs, check_mode, root=ROOT):
    """Writes `(path, text_or_bytes)` pairs or verifies they match disk in `--check` mode."""
    all_ok = True
    for path, content in outputs:
        data = content.encode("utf-8") if isinstance(content, str) else content
        data = data.replace(b"\r\n", b"\n")
        rel = os.path.relpath(path, root).replace("\\", "/")
        if check_mode:
            if not os.path.isfile(path):
                msg = "%s MISSING" % rel
                print(msg)
                print(msg, file=sys.stderr)
                all_ok = False
                continue
            disk = read_bytes(path)
            if disk == data:
                print("%s up to date" % rel)
            else:
                msg = "%s DIFFERS (%s)" % (rel, first_diff_line(disk, data))
                print(msg)
                print(msg, file=sys.stderr)
                all_ok = False
        else:
            write_bytes(path, data)
            print("wrote %s" % rel)
    return 0 if all_ok else 1


FULL_MODULE_ORDER = [
    "compiler.kernel.id",
    "compiler.kernel.hash",
    "compiler.kernel.arena",
    "compiler.kernel.dynarray",
    "compiler.kernel.interner",
    "compiler.kernel",
    "compiler.source.span",
    "compiler.source.manager",
    "compiler.source",
    "compiler.diag.code",
    "compiler.diag.emitter",
    "compiler.diag.format",
    "compiler.diag.json",
    "compiler.diag",
    "compiler.kernel_source_diag.session",
    "compiler.kernel_source_diag",
    "compiler.lex.token",
    "compiler.lex.scanner",
    "compiler.lex",
    "compiler.lexer.session",
    "compiler.lexer",
    "compiler.syntax.ast",
    "compiler.syntax.parse",
    "compiler.parser.session",
    "compiler.parser",
    "compiler.resolve.symtab",
    "compiler.resolve.rib",
    "compiler.resolve.resolver",
    "compiler.resolve",
    "compiler.hir.hir",
    "compiler.hir.lower",
    "compiler.hir",
    "compiler.resolve_hir.session",
    "compiler.resolve_hir",
    "compiler.types.types",
    "compiler.types.layout",
    "compiler.types.exhaust",
    "compiler.traits.solver",
    "compiler.traits.mono",
    "compiler.types.typeck",
    "compiler.types",
    "compiler.traits",
    "compiler.typeck.session",
    "compiler.typeck",
    "compiler.typeck_traits.session",
    "compiler.typeck_traits",
    "compiler.mir.mir",
    "compiler.mir.drop",
    "compiler.mir.builder",
    "compiler.mir",
    "compiler.own.move_ck",
    "compiler.own.cap",
    "compiler.own.init",
    "compiler.own.unsafe_ck",
    "compiler.own",
    "compiler.verify.verifier",
    "compiler.verify",
    "compiler.own_mir_verify.session",
    "compiler.own_mir_verify",
    "compiler.opt.const_fold",
    "compiler.opt.dce",
    "compiler.opt.cfg_simp",
    "compiler.opt",
    "compiler.interp.value",
    "compiler.interp.frame",
    "compiler.interp.oracle",
    "compiler.interp.interp",
    "compiler.interp",
    "compiler.interp_opt.session",
    "compiler.interp_opt",
    "compiler.lir.lir",
    "compiler.lir.builder",
    "compiler.lir",
    "compiler.abi.win64",
    "compiler.abi",
    "compiler.obj.coff",
    "compiler.obj.writer",
    "compiler.obj",
    "compiler.target.x64.encode",
    "compiler.target.x64.isel",
    "compiler.target.x64.frame",
    "compiler.target.x64",
    "compiler.backend.session",
    "compiler.backend",
    "compiler.link.pe",
    "compiler.link.import",
    "compiler.link.linker",
    "compiler.link",
    "compiler.driver.opts",
    "compiler.driver.pipeline",
    "compiler.driver",
    "compiler.obj_link_driver",
]


def resolve_compiler_module_deps(seed_mods, root=ROOT):
    """Returns transitive dependency closure of `seed_mods` in canonical topological order."""
    cmod_files = compiler_module_files(root)
    cmod_files.pop("compiler.own.move", None)
    cmod_files.pop("compiler.own.unsafe", None)
    order = list(FULL_MODULE_ORDER)
    for m in sorted(cmod_files.keys()):
        if m not in order and not m.endswith(".mod"):
            order.append(m)

    def _norm_mod(m):
        if m == "compiler.own.move":
            return "compiler.own.move_ck"
        if m == "compiler.own.unsafe":
            return "compiler.own.unsafe_ck"
        return m

    mod_deps = {}
    for m, path in cmod_files.items():
        txt = read_cached_text(path)
        txt = re.sub(r"\bcompiler\.own\.move\b", "compiler.own.move_ck", txt)
        txt = re.sub(r"\bcompiler\.own\.unsafe\b", "compiler.own.unsafe_ck", txt)
        deps = set()
        for u in re.finditer(r"^\s*(?:pub\s+)?use\s+(compiler\.[A-Za-z0-9_.]+)", txt, re.M):
            parts = u.group(1).split(".")
            for k in range(len(parts), 1, -1):
                cand = ".".join(parts[:k])
                if cand in cmod_files:
                    if cand != m:
                        deps.add(cand)
                    break
        mod_deps[m] = deps

    vis = set()
    stack = [_norm_mod(m) for m in seed_mods]
    while stack:
        cur = stack.pop()
        if cur in vis or cur not in cmod_files:
            continue
        vis.add(cur)
        for d in mod_deps.get(cur, ()):
            if d not in vis:
                stack.append(d)
    return [m for m in order if m in vis]


def get_pub_exports(mod_list, root=ROOT):
    """Returns `{ident: mod_name}` for all `pub` items declared in `mod_list`."""
    cmod_files = compiler_module_files(root)
    exports = {}
    for m in mod_list:
        path = cmod_files[m]
        txt = read_bytes(path).decode("utf-8").replace("\r\n", "\n")
        for match in re.finditer(
            r"(?:^|;\s*)pub\s+(?:unsafe\s+)?(?:fn|struct|enum|const)\s+([A-Za-z0-9_]+)\b",
            txt,
            re.M,
        ):
            exports.setdefault(match.group(1), m)
    return exports


def assemble_template_bundle(template_path, seed_mods, include_std_sys=True, root=ROOT):
    """Assembles a complete `.ax` bundle from `<bundle>.ax.in` (header + `module main`) and `compiler/` modules."""
    raw = read_bytes(template_path).decode("utf-8").replace("\r\n", "\n")
    lines = raw.split("\n")
    header_lines = []
    idx = 0
    while idx < len(lines) and (lines[idx].startswith("//") or lines[idx].strip() == ""):
        if lines[idx].startswith("//"):
            header_lines.append(lines[idx])
        idx += 1
    body = "\n".join(lines[idx:]).strip() + "\n"
    header = "\n".join(header_lines) + "\n" if header_lines else ""
    prelude = build_prelude_text(
        include_sym_pad=True,
        sym_pad_count=800,
        include_std_sys=include_std_sys,
        root=root,
    )
    mods = resolve_compiler_module_deps(seed_mods, root=root)
    mods_txt = assemble_compiler_modules(mods, root=root)
    return header + "\n" + prelude + "\n" + mods_txt + "\n\n" + body


def run_template_generator(here_dir, bundle_specs, argv=None, root=ROOT):
    """Standard CLI entrypoint for template-based `gen_<area>_tests.py` generators."""
    if argv is None:
        argv = sys.argv[1:]
    check_mode = "--check" in argv or "check" in argv
    outputs = []
    for spec in bundle_specs:
        if len(spec) == 2:
            bundle_name, seed_mods = spec
            include_std_sys = True
        else:
            bundle_name, seed_mods, include_std_sys = spec
        tpl_path = os.path.join(here_dir, bundle_name + ".in")
        out_path = os.path.join(here_dir, bundle_name)
        text = assemble_template_bundle(
            tpl_path,
            seed_mods,
            include_std_sys=include_std_sys,
            root=root,
        )
        outputs.append((out_path, text))
    return write_or_check_bundles(outputs, check_mode, root=root)

