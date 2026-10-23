#!/usr/bin/env python3
"""Generate self-contained selfhost MIR optimizer test files under `tests/selfhost/opt/`.

Each generated `.ax` file bundles the required `compiler/*` modules, the Win32
`__ax_host_heap_alloc` / `__ax_host_heap_free` prelude, and the test `main` module,
following the selfhost test layout used in `tests/selfhost/verify/`.
"""

import os
import sys

HERE = os.path.dirname(os.path.abspath(__file__))
ROOT = os.path.abspath(os.path.join(HERE, "..", "..", ".."))

REFERENCE_BUNDLE = "tests/selfhost/mir/qa_mir_builder_and_drop_a.ax"

CORE_MODULES = [
    ("compiler.kernel.id", "reference"),
    ("compiler.kernel.hash", "reference"),
    ("compiler.kernel.arena", "reference"),
    ("compiler.kernel.interner", "reference"),
    ("compiler.source.span", "reference"),
    ("compiler.source.manager", "reference"),
    ("compiler.diag.code", "reference"),
    ("compiler.diag.emitter", "reference"),
    ("compiler.diag.format", "reference"),
    ("compiler.lex.token", "reference"),
    ("compiler.syntax.ast", "reference"),
    ("compiler.hir.hir", "reference"),
    ("compiler.types.types", "reference"),
    ("compiler.mir.mir", "compiler"),
    ("compiler.mir.drop", "compiler"),
    ("compiler.verify.verifier", "compiler"),
    ("compiler.verify", "compiler"),
    ("compiler.opt.const_fold", "compiler"),
    ("compiler.opt.dce", "compiler"),
    ("compiler.opt.cfg_simp", "compiler"),
    ("compiler.opt", "compiler"),
]

PIPELINE_MODULES = [
    ("compiler.kernel.id", "reference"),
    ("compiler.kernel.hash", "reference"),
    ("compiler.kernel.arena", "reference"),
    ("compiler.kernel.interner", "reference"),
    ("compiler.source.span", "reference"),
    ("compiler.source.manager", "reference"),
    ("compiler.diag.code", "reference"),
    ("compiler.diag.emitter", "reference"),
    ("compiler.diag.format", "reference"),
    ("compiler.diag.json", "reference"),
    ("compiler.kernel_source_diag.session", "reference"),
    ("compiler.lex.token", "reference"),
    ("compiler.lex.scanner", "reference"),
    ("compiler.lexer.session", "reference"),
    ("compiler.syntax.ast", "reference"),
    ("compiler.syntax.parse", "reference"),
    ("compiler.parser.session", "reference"),
    ("compiler.resolve.symtab", "reference"),
    ("compiler.resolve.rib", "reference"),
    ("compiler.resolve.resolver", "reference"),
    ("compiler.hir.hir", "reference"),
    ("compiler.hir.lower", "reference"),
    ("compiler.resolve_hir.session", "reference"),
    ("compiler.types.types", "reference"),
    ("compiler.types.layout", "reference"),
    ("compiler.types.exhaust", "reference"),
    ("compiler.traits.solver", "reference"),
    ("compiler.traits.mono", "reference"),
    ("compiler.types.typeck", "reference"),
    ("compiler.types", "reference"),
    ("compiler.traits", "reference"),
    ("compiler.typeck.session", "reference"),
    ("compiler.typeck", "reference"),
    ("compiler.typeck_traits.session", "reference"),
    ("compiler.typeck_traits", "reference"),
    ("compiler.mir.mir", "compiler"),
    ("compiler.mir.drop", "compiler"),
    ("compiler.mir.builder", "compiler"),
    ("compiler.mir", "compiler"),
    ("compiler.verify.verifier", "compiler"),
    ("compiler.verify", "compiler"),
    ("compiler.opt.const_fold", "compiler"),
    ("compiler.opt.dce", "compiler"),
    ("compiler.opt.cfg_simp", "compiler"),
    ("compiler.opt", "compiler"),
]

PRELUDE = """\
@link("kernel32")
extern "system" {
    fn GetProcessHeap() -> *mut u8;
    fn HeapAlloc(hHeap: *mut u8, dwFlags: u32, dwBytes: usize) -> *mut u8;
    fn HeapFree(hHeap: *mut u8, dwFlags: u32, lpMem: *mut u8) -> i32;
}

const HEAP_ZERO_MEMORY: u32 = 8u32;
const MIN_HEAP_ALLOC: usize = 16;

pub unsafe fn __ax_host_heap_alloc(size: usize, align: usize) -> *mut u8 {
    let h = GetProcessHeap();
    if (h as usize) == 0 {
        return 0 as *mut u8;
    }
    let alloc_bytes: usize = if size < MIN_HEAP_ALLOC { MIN_HEAP_ALLOC } else { size };
    HeapAlloc(h, HEAP_ZERO_MEMORY, alloc_bytes)
}

pub unsafe fn __ax_host_heap_free(p: *mut u8, size: usize, align: usize) {
    if (p as usize) != 0 {
        let h = GetProcessHeap();
        if (h as usize) != 0 {
            HeapFree(h, 0u32, p);
        }
    }
}
"""


def read_bytes(path):
    with open(path, "rb") as f:
        return f.read()


def write_bytes(path, data):
    with open(path, "wb") as f:
        f.write(data)


def compiler_module_files():
    found = {}
    for dirpath, _dirs, files in os.walk(os.path.join(ROOT, "compiler")):
        for fn in files:
            if not fn.endswith(".ax"):
                continue
            path = os.path.join(dirpath, fn)
            with open(path, encoding="utf-8") as f:
                for line in f:
                    if line.startswith("module "):
                        found[line.split()[1]] = path
                        break
    return found


def reference_sections():
    text = read_bytes(os.path.join(ROOT, REFERENCE_BUNDLE)).decode("utf-8")
    sections = {}
    current = None
    buf = []
    for line in text.split("\n"):
        if line.startswith("module "):
            if current:
                sections[current] = "\n".join(buf)
            current = line.split()[1]
            buf = [line]
        elif current:
            buf.append(line)
    if current:
        sections[current] = "\n".join(buf)
    return sections


def assemble_modules(mod_list):
    files = compiler_module_files()
    ref = reference_sections()
    parts = []
    for name, origin in mod_list:
        src = read_bytes(files[name]).decode("utf-8") if origin == "compiler" else ref[name]
        parts.append(src.rstrip("\n") + "\n")
    return "\n".join(parts)


def byte_table(name, data):
    lines = ["const %s: [%d]u8 = [" % (name, len(data))]
    for i in range(0, len(data), 16):
        chunk = data[i:i + 16]
        lines.append("    " + ", ".join("%du8" % b for b in chunk) + ",")
    lines.append("];")
    return "\n".join(lines)


def u32_table(name, values):
    lines = ["const %s: [%d]u32 = [" % (name, max(1, len(values)))]
    if not values:
        lines.append("    0u32,")
    else:
        for i in range(0, len(values), 10):
            chunk = values[i:i + 10]
            lines.append("    " + ", ".join("%du32" % v for v in chunk) + ",")
    lines.append("];")
    return "\n".join(lines)


def pack_blobs(blobs):
    offsets = [0]
    for b in blobs:
        offsets.append(offsets[-1] + len(b))
    return b"".join(blobs), offsets


UNIT_MIR_SNIPPETS = [
    # 0: Case 0 input (const_fold + dce + cfg_simplify)
    (
        b"mir_body {\n"
        b"    let mut _0: type#8;\n"
        b"    let _1: type#8;\n"
        b"    let _2: type#4;\n"
        b"    let _3: type#4;\n"
        b"    let _4: type#8;\n"
        b"    bb0: {\n"
        b"        StorageLive(_4);\n"
        b"        _4 = const 99: type#8;\n"
        b"        StorageDead(_4);\n"
        b"        _2 = overflows(const 40: type#8 + const 2: type#8);\n"
        b"        _3 = !const 0: type#4;\n"
        b"        _1 = const 40: type#8 + const 2: type#8;\n"
        b"        switchInt(const 1: type#8) -> [0: bb2, otherwise: bb1];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _0 = copy _1;\n"
        b"        return;\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        _0 = const 0: type#8;\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # 1: Case 0 expected output
    (
        b"mir_body {\n"
        b"    let mut _0: type#8;\n"
        b"    let _1: type#8;\n"
        b"    let _2: type#4;\n"
        b"    let _3: type#4;\n"
        b"    let _4: type#8;\n"
        b"    bb0: {\n"
        b"        _1 = const 42;\n"
        b"        goto -> bb1;\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _0 = copy _1;\n"
        b"        return;\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # 2: Case 1 input (overflow & div-by-zero non-folding)
    (
        b"mir_body {\n"
        b"    let mut _0: type#6;\n"
        b"    let _1: type#4;\n"
        b"    let _2: type#6;\n"
        b"    bb0: {\n"
        b"        _1 = overflows(const 127: type#6 + const 1: type#6);\n"
        b"        _2 = const 10: type#6 / const 0: type#6;\n"
        b"        _0 = const 127: type#6 + const 1: type#6;\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # 3: Case 1 expected output
    (
        b"mir_body {\n"
        b"    let mut _0: type#6;\n"
        b"    let _1: type#4;\n"
        b"    let _2: type#6;\n"
        b"    bb0: {\n"
        b"        _1 = overflows(const 127 + const 1);\n"
        b"        _2 = const 10 / const 0;\n"
        b"        _0 = const 127 + const 1;\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # 4: Case 2 input (transitive multi-iteration DCE)
    (
        b"mir_body {\n"
        b"    let mut _0: type#8;\n"
        b"    let _1: type#8;\n"
        b"    let _2: type#8;\n"
        b"    let _3: type#9;\n"
        b"    bb0: {\n"
        b"        StorageLive(_1);\n"
        b"        _1 = const 5: type#8;\n"
        b"        _2 = copy _1;\n"
        b"        _3 = move _2 as type#9;\n"
        b"        StorageDead(_1);\n"
        b"        _0 = const 0: type#8;\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # 5: Case 2 expected output
    (
        b"mir_body {\n"
        b"    let mut _0: type#8;\n"
        b"    let _1: type#8;\n"
        b"    let _2: type#8;\n"
        b"    let _3: type#9;\n"
        b"    bb0: {\n"
        b"        _0 = const 0;\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # 6: Case 3 input (redundant switch elimination + linear block merging)
    (
        b"mir_body {\n"
        b"    let mut _0: type#8;\n"
        b"    let _1: type#8;\n"
        b"    let _2: type#8;\n"
        b"    bb0: {\n"
        b"        _1 = const 7: type#8;\n"
        b"        switchInt(copy _1) -> [0: bb2, 1: bb2, otherwise: bb2];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _0 = const 99: type#8;\n"
        b"        return;\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        _2 = const 42: type#8;\n"
        b"        goto -> bb3;\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        _0 = copy _2;\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # 7: Case 4 input (`tests/opt/qa_dce_run.ax` lowered MIR)
    (
        b"mir_body {\n"
        b"    let mut _0: type#8;\n"
        b"    let _1: type#8;\n"
        b"    let mut _2: type#8;\n"
        b"    let _3: type#2;\n"
        b"    let _4: type#2;\n"
        b"    let _5: type#4;\n"
        b"    let _6: type#3;\n"
        b"    let _7: type#3;\n"
        b"    bb0: {\n"
        b"        _1 = const 1: type#8;\n"
        b"        _2 = copy _1;\n"
        b"        switchInt(const 0: type#4) -> [0: bb2, otherwise: bb1];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _2 = const 2: type#8;\n"
        b"        goto -> bb3;\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        goto -> bb3;\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        _5 = copy _2 == const 1: type#8;\n"
        b"        switchInt(move _5) -> [0: bb5, otherwise: bb4];\n"
        b"    }\n"
        b"    bb4: {\n"
        b"        _0 = const 0: type#8;\n"
        b"        return;\n"
        b"    }\n"
        b"    bb5: {\n"
        b"        goto -> bb6;\n"
        b"    }\n"
        b"    bb6: {\n"
        b"        _0 = const 1: type#8;\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # 8: Case 4 expected output (`tests/opt/qa_dce_run.ax` post-`-O1` MIR)
    (
        b"mir_body {\n"
        b"    let mut _0: type#8;\n"
        b"    let _1: type#8;\n"
        b"    let mut _2: type#8;\n"
        b"    let _3: type#2;\n"
        b"    let _4: type#2;\n"
        b"    let _5: type#4;\n"
        b"    let _6: type#3;\n"
        b"    let _7: type#3;\n"
        b"    bb0: {\n"
        b"        _1 = const 1;\n"
        b"        _2 = copy _1;\n"
        b"        goto -> bb2;\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        goto -> bb3;\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        _5 = copy _2 == const 1;\n"
        b"        switchInt(move _5) -> [0: bb5, otherwise: bb4];\n"
        b"    }\n"
        b"    bb4: {\n"
        b"        _0 = const 0;\n"
        b"        return;\n"
        b"    }\n"
        b"    bb5: {\n"
        b"        goto -> bb6;\n"
        b"    }\n"
        b"    bb6: {\n"
        b"        _0 = const 1;\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # 9: Case 5 input (Regression test for Finding 2: foldable binop followed by overflowing/runtime overflows)
    (
        b"mir_body {\n"
        b"    let mut _0: type#6;\n"
        b"    let _1: type#6;\n"
        b"    let _2: type#4;\n"
        b"    let _3: type#4;\n"
        b"    bb0: {\n"
        b"        _1 = const 1: type#6 + const 2: type#6;\n"
        b"        _2 = overflows(const 127: type#6 + const 1: type#6);\n"
        b"        _3 = overflows(copy _1 + copy _1);\n"
        b"        assert(copy _2 == false, \"arithmetic overflow\") -> [return: bb1, unwind: bb2];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        assert(copy _3 == false, \"arithmetic overflow\") -> [return: bb3, unwind: bb2];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        _0 = copy _1;\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # 10: Case 5 expected output
    (
        b"mir_body {\n"
        b"    let mut _0: type#6;\n"
        b"    let _1: type#6;\n"
        b"    let _2: type#4;\n"
        b"    let _3: type#4;\n"
        b"    bb0: {\n"
        b"        _1 = const 3;\n"
        b"        _2 = overflows(const 127 + const 1);\n"
        b"        _3 = overflows(copy _1 + copy _1);\n"
        b"        assert(copy _2 == false, \"arithmetic overflow\") -> [return: bb1, unwind: bb2];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        assert(copy _3 == false, \"arithmetic overflow\") -> [return: bb3, unwind: bb2];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        _0 = copy _1;\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # 11: Case 6 input (Regression test for Finding 3: non-pure unary op + unreachable block skipped in DCE)
    (
        b"mir_body {\n"
        b"    let mut _0: type#8;\n"
        b"    let _1: type#6;\n"
        b"    let _2: type#8;\n"
        b"    bb0: {\n"
        b"        _1 = -const 128: type#6;\n"
        b"        _2 = const 99: type#8;\n"
        b"        _0 = const 7: type#8;\n"
        b"        return;\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _0 = copy _2;\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # 12: Case 6 expected output
    (
        b"mir_body {\n"
        b"    let mut _0: type#8;\n"
        b"    let _1: type#6;\n"
        b"    let _2: type#8;\n"
        b"    bb0: {\n"
        b"        _1 = -const 128;\n"
        b"        _0 = const 7;\n"
        b"        return;\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"}\n"
    ),
    # 13: Case 7 input (`tests/opt/const_fold_run.ax` lowered MIR)
    (
        b"mir_body {\n"
        b"    let mut _0: type#8;\n"
        b"    let _1: type#8;\n"
        b"    let _2: type#8;\n"
        b"    let _3: type#8;\n"
        b"    let _4: type#8;\n"
        b"    let _5: type#2;\n"
        b"    let _6: type#4;\n"
        b"    let _7: type#8;\n"
        b"    let _8: type#4;\n"
        b"    let _9: type#4;\n"
        b"    let _10: type#3;\n"
        b"    let _11: type#3;\n"
        b"    bb0: {\n"
        b"        _1 = const 40: type#8;\n"
        b"        _2 = copy _1;\n"
        b"        _3 = const 2: type#8;\n"
        b"        _4 = copy _3;\n"
        b"        _8 = overflows(copy _2 + copy _4);\n"
        b"        _9 = !copy _8;\n"
        b"        assert(copy _9 == true, \"arithmetic overflow\") -> [return: bb1, unwind: bb2];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _7 = copy _2 + copy _4;\n"
        b"        _6 = move _7 == const 42: type#8;\n"
        b"        switchInt(move _6) -> [0: bb4, otherwise: bb3];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        _0 = const 0: type#8;\n"
        b"        return;\n"
        b"    }\n"
        b"    bb4: {\n"
        b"        goto -> bb5;\n"
        b"    }\n"
        b"    bb5: {\n"
        b"        _0 = const 1: type#8;\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # 14: Case 7 expected output (`tests/opt/const_fold_run.ax` post-`-O1` MIR)
    (
        b"mir_body {\n"
        b"    let mut _0: type#8;\n"
        b"    let _1: type#8;\n"
        b"    let _2: type#8;\n"
        b"    let _3: type#8;\n"
        b"    let _4: type#8;\n"
        b"    let _5: type#2;\n"
        b"    let _6: type#4;\n"
        b"    let _7: type#8;\n"
        b"    let _8: type#4;\n"
        b"    let _9: type#4;\n"
        b"    let _10: type#3;\n"
        b"    let _11: type#3;\n"
        b"    bb0: {\n"
        b"        _1 = const 40;\n"
        b"        _2 = copy _1;\n"
        b"        _3 = const 2;\n"
        b"        _4 = copy _3;\n"
        b"        _8 = overflows(copy _2 + copy _4);\n"
        b"        _9 = !copy _8;\n"
        b"        assert(copy _9 == true, \"arithmetic overflow\") -> [return: bb1, unwind: bb2];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _7 = copy _2 + copy _4;\n"
        b"        _6 = move _7 == const 42;\n"
        b"        switchInt(move _6) -> [0: bb4, otherwise: bb3];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        _0 = const 0;\n"
        b"        return;\n"
        b"    }\n"
        b"    bb4: {\n"
        b"        goto -> bb5;\n"
        b"    }\n"
        b"    bb5: {\n"
        b"        _0 = const 1;\n"
        b"        return;\n"
        b"    }\n"
        b"}\n"
    ),
    # 15: Case 8 input (`tests/opt/qa_edge_cases_run.ax` lowered MIR)
    (
        b"mir_body {\n"
        b"    let mut _0: type#8;\n"
        b"    let _1: type#8;\n"
        b"    let _2: type#8;\n"
        b"    let _3: type#8;\n"
        b"    let _4: type#4;\n"
        b"    let _5: type#4;\n"
        b"    let _6: type#8;\n"
        b"    let _7: type#8;\n"
        b"    let _8: type#4;\n"
        b"    let _9: type#4;\n"
        b"    let _10: type#8;\n"
        b"    let _11: type#8;\n"
        b"    let _12: type#4;\n"
        b"    let _13: type#4;\n"
        b"    let _14: type#8;\n"
        b"    let _15: type#8;\n"
        b"    let _16: type#4;\n"
        b"    let _17: type#4;\n"
        b"    let _18: type#8;\n"
        b"    let _19: type#8;\n"
        b"    let _20: type#8;\n"
        b"    let _21: type#8;\n"
        b"    let _22: type#8;\n"
        b"    let _23: type#8;\n"
        b"    let _24: type#4;\n"
        b"    let _25: type#4;\n"
        b"    let _26: type#4;\n"
        b"    let _27: type#8;\n"
        b"    let _28: type#8;\n"
        b"    let _29: type#4;\n"
        b"    let _30: type#4;\n"
        b"    let _31: type#4;\n"
        b"    let _32: type#8;\n"
        b"    let _33: type#4;\n"
        b"    let _34: type#4;\n"
        b"    let _35: type#2;\n"
        b"    let _36: type#4;\n"
        b"    let _37: type#8;\n"
        b"    let _38: type#8;\n"
        b"    let _39: type#8;\n"
        b"    let _40: type#4;\n"
        b"    let _41: type#4;\n"
        b"    let _42: type#4;\n"
        b"    let _43: type#4;\n"
        b"    let _44: type#4;\n"
        b"    let _45: type#4;\n"
        b"    let _46: type#3;\n"
        b"    let _47: type#3;\n"
        b"    bb0: {\n"
        b"        _1 = const 1: type#8;\n"
        b"        _2 = copy _1;\n"
        b"        _4 = const 30: type#8 >= const 0: type#8;\n"
        b"        assert(copy _4 == true, \"shift amount out of range\") -> [return: bb1, unwind: bb2];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _5 = const 30: type#8 < const 32: type#8;\n"
        b"        assert(copy _5 == true, \"shift amount out of range\") -> [return: bb3, unwind: bb4];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        _3 = copy _2 << const 30: type#8;\n"
        b"        _6 = copy _3;\n"
        b"        _8 = const 30: type#8 >= const 0: type#8;\n"
        b"        assert(copy _8 == true, \"shift amount out of range\") -> [return: bb5, unwind: bb6];\n"
        b"    }\n"
        b"    bb4: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"    bb5: {\n"
        b"        _9 = const 30: type#8 < const 32: type#8;\n"
        b"        assert(copy _9 == true, \"shift amount out of range\") -> [return: bb7, unwind: bb8];\n"
        b"    }\n"
        b"    bb6: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"    bb7: {\n"
        b"        _7 = copy _6 >> const 30: type#8;\n"
        b"        _10 = copy _7;\n"
        b"        _12 = overflows(const 0: type#8 - const 1: type#8);\n"
        b"        _13 = !copy _12;\n"
        b"        assert(copy _13 == true, \"arithmetic overflow\") -> [return: bb9, unwind: bb10];\n"
        b"    }\n"
        b"    bb8: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"    bb9: {\n"
        b"        _11 = -const 1: type#8;\n"
        b"        _14 = copy _11;\n"
        b"        _16 = overflows(copy _14 * copy _14);\n"
        b"        _17 = !copy _16;\n"
        b"        assert(copy _17 == true, \"arithmetic overflow\") -> [return: bb11, unwind: bb12];\n"
        b"    }\n"
        b"    bb10: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"    bb11: {\n"
        b"        _15 = copy _14 * copy _14;\n"
        b"        _18 = copy _15;\n"
        b"        _19 = const 100: type#8;\n"
        b"        _20 = copy _19;\n"
        b"        _21 = const 3: type#8;\n"
        b"        _22 = copy _21;\n"
        b"        _24 = copy _22 != const 0: type#8;\n"
        b"        assert(copy _24 == true, \"division by zero\") -> [return: bb13, unwind: bb14];\n"
        b"    }\n"
        b"    bb12: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"    bb13: {\n"
        b"        _26 = overflows(copy _20 % copy _22);\n"
        b"        _25 = !copy _26;\n"
        b"        assert(copy _25 == true, \"arithmetic overflow\") -> [return: bb15, unwind: bb16];\n"
        b"    }\n"
        b"    bb14: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"    bb15: {\n"
        b"        _23 = copy _20 % copy _22;\n"
        b"        _27 = copy _23;\n"
        b"        _29 = copy _22 != const 0: type#8;\n"
        b"        assert(copy _29 == true, \"division by zero\") -> [return: bb17, unwind: bb18];\n"
        b"    }\n"
        b"    bb16: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"    bb17: {\n"
        b"        _31 = overflows(copy _20 / copy _22);\n"
        b"        _30 = !copy _31;\n"
        b"        assert(copy _30 == true, \"arithmetic overflow\") -> [return: bb19, unwind: bb20];\n"
        b"    }\n"
        b"    bb18: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"    bb19: {\n"
        b"        _28 = copy _20 / copy _22;\n"
        b"        _32 = copy _28;\n"
        b"        _33 = !const 0: type#4;\n"
        b"        _34 = copy _33;\n"
        b"        _40 = overflows(copy _10 + copy _18);\n"
        b"        _41 = !copy _40;\n"
        b"        assert(copy _41 == true, \"arithmetic overflow\") -> [return: bb21, unwind: bb22];\n"
        b"    }\n"
        b"    bb20: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"    bb21: {\n"
        b"        _39 = copy _10 + copy _18;\n"
        b"        _42 = overflows(move _39 + copy _27);\n"
        b"        _43 = !copy _42;\n"
        b"        assert(copy _43 == true, \"arithmetic overflow\") -> [return: bb23, unwind: bb24];\n"
        b"    }\n"
        b"    bb22: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"    bb23: {\n"
        b"        _38 = move _39 + copy _27;\n"
        b"        _44 = overflows(move _38 + copy _32);\n"
        b"        _45 = !copy _44;\n"
        b"        assert(copy _45 == true, \"arithmetic overflow\") -> [return: bb25, unwind: bb26];\n"
        b"    }\n"
        b"    bb24: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"    bb25: {\n"
        b"        _37 = move _38 + copy _32;\n"
        b"        _36 = move _37 == const 36: type#8;\n"
        b"        switchInt(move _36) -> [0: bb28, otherwise: bb27];\n"
        b"    }\n"
        b"    bb26: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"    bb27: {\n"
        b"        switchInt(copy _34) -> [0: bb31, otherwise: bb30];\n"
        b"    }\n"
        b"    bb28: {\n"
        b"        goto -> bb29;\n"
        b"    }\n"
        b"    bb29: {\n"
        b"        _0 = const 1: type#8;\n"
        b"        return;\n"
        b"    }\n"
        b"    bb30: {\n"
        b"        _0 = const 0: type#8;\n"
        b"        return;\n"
        b"    }\n"
        b"    bb31: {\n"
        b"        goto -> bb32;\n"
        b"    }\n"
        b"    bb32: {\n"
        b"        goto -> bb29;\n"
        b"    }\n"
        b"}\n"
    ),
    # 16: Case 8 expected output (`tests/opt/qa_edge_cases_run.ax` post-`-O1` MIR)
    (
        b"mir_body {\n"
        b"    let mut _0: type#8;\n"
        b"    let _1: type#8;\n"
        b"    let _2: type#8;\n"
        b"    let _3: type#8;\n"
        b"    let _4: type#4;\n"
        b"    let _5: type#4;\n"
        b"    let _6: type#8;\n"
        b"    let _7: type#8;\n"
        b"    let _8: type#4;\n"
        b"    let _9: type#4;\n"
        b"    let _10: type#8;\n"
        b"    let _11: type#8;\n"
        b"    let _12: type#4;\n"
        b"    let _13: type#4;\n"
        b"    let _14: type#8;\n"
        b"    let _15: type#8;\n"
        b"    let _16: type#4;\n"
        b"    let _17: type#4;\n"
        b"    let _18: type#8;\n"
        b"    let _19: type#8;\n"
        b"    let _20: type#8;\n"
        b"    let _21: type#8;\n"
        b"    let _22: type#8;\n"
        b"    let _23: type#8;\n"
        b"    let _24: type#4;\n"
        b"    let _25: type#4;\n"
        b"    let _26: type#4;\n"
        b"    let _27: type#8;\n"
        b"    let _28: type#8;\n"
        b"    let _29: type#4;\n"
        b"    let _30: type#4;\n"
        b"    let _31: type#4;\n"
        b"    let _32: type#8;\n"
        b"    let _33: type#4;\n"
        b"    let _34: type#4;\n"
        b"    let _35: type#2;\n"
        b"    let _36: type#4;\n"
        b"    let _37: type#8;\n"
        b"    let _38: type#8;\n"
        b"    let _39: type#8;\n"
        b"    let _40: type#4;\n"
        b"    let _41: type#4;\n"
        b"    let _42: type#4;\n"
        b"    let _43: type#4;\n"
        b"    let _44: type#4;\n"
        b"    let _45: type#4;\n"
        b"    let _46: type#3;\n"
        b"    let _47: type#3;\n"
        b"    bb0: {\n"
        b"        _1 = const 1;\n"
        b"        _2 = copy _1;\n"
        b"        _4 = const 1;\n"
        b"        assert(copy _4 == true, \"shift amount out of range\") -> [return: bb1, unwind: bb2];\n"
        b"    }\n"
        b"    bb1: {\n"
        b"        _5 = const 1;\n"
        b"        assert(copy _5 == true, \"shift amount out of range\") -> [return: bb3, unwind: bb4];\n"
        b"    }\n"
        b"    bb2: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"    bb3: {\n"
        b"        _3 = copy _2 << const 30;\n"
        b"        _6 = copy _3;\n"
        b"        _8 = const 1;\n"
        b"        assert(copy _8 == true, \"shift amount out of range\") -> [return: bb5, unwind: bb6];\n"
        b"    }\n"
        b"    bb4: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"    bb5: {\n"
        b"        _9 = const 1;\n"
        b"        assert(copy _9 == true, \"shift amount out of range\") -> [return: bb7, unwind: bb8];\n"
        b"    }\n"
        b"    bb6: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"    bb7: {\n"
        b"        _7 = copy _6 >> const 30;\n"
        b"        _10 = copy _7;\n"
        b"        _12 = const 0;\n"
        b"        _13 = !copy _12;\n"
        b"        assert(copy _13 == true, \"arithmetic overflow\") -> [return: bb9, unwind: bb10];\n"
        b"    }\n"
        b"    bb8: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"    bb9: {\n"
        b"        _11 = const 4294967295;\n"
        b"        _14 = copy _11;\n"
        b"        _16 = overflows(copy _14 * copy _14);\n"
        b"        _17 = !copy _16;\n"
        b"        assert(copy _17 == true, \"arithmetic overflow\") -> [return: bb11, unwind: bb12];\n"
        b"    }\n"
        b"    bb10: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"    bb11: {\n"
        b"        _15 = copy _14 * copy _14;\n"
        b"        _18 = copy _15;\n"
        b"        _19 = const 100;\n"
        b"        _20 = copy _19;\n"
        b"        _21 = const 3;\n"
        b"        _22 = copy _21;\n"
        b"        _24 = copy _22 != const 0;\n"
        b"        assert(copy _24 == true, \"division by zero\") -> [return: bb13, unwind: bb14];\n"
        b"    }\n"
        b"    bb12: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"    bb13: {\n"
        b"        _26 = overflows(copy _20 % copy _22);\n"
        b"        _25 = !copy _26;\n"
        b"        assert(copy _25 == true, \"arithmetic overflow\") -> [return: bb15, unwind: bb16];\n"
        b"    }\n"
        b"    bb14: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"    bb15: {\n"
        b"        _23 = copy _20 % copy _22;\n"
        b"        _27 = copy _23;\n"
        b"        _29 = copy _22 != const 0;\n"
        b"        assert(copy _29 == true, \"division by zero\") -> [return: bb17, unwind: bb18];\n"
        b"    }\n"
        b"    bb16: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"    bb17: {\n"
        b"        _31 = overflows(copy _20 / copy _22);\n"
        b"        _30 = !copy _31;\n"
        b"        assert(copy _30 == true, \"arithmetic overflow\") -> [return: bb19, unwind: bb20];\n"
        b"    }\n"
        b"    bb18: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"    bb19: {\n"
        b"        _28 = copy _20 / copy _22;\n"
        b"        _32 = copy _28;\n"
        b"        _33 = const 1;\n"
        b"        _34 = copy _33;\n"
        b"        _40 = overflows(copy _10 + copy _18);\n"
        b"        _41 = !copy _40;\n"
        b"        assert(copy _41 == true, \"arithmetic overflow\") -> [return: bb21, unwind: bb22];\n"
        b"    }\n"
        b"    bb20: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"    bb21: {\n"
        b"        _39 = copy _10 + copy _18;\n"
        b"        _42 = overflows(move _39 + copy _27);\n"
        b"        _43 = !copy _42;\n"
        b"        assert(copy _43 == true, \"arithmetic overflow\") -> [return: bb23, unwind: bb24];\n"
        b"    }\n"
        b"    bb22: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"    bb23: {\n"
        b"        _38 = move _39 + copy _27;\n"
        b"        _44 = overflows(move _38 + copy _32);\n"
        b"        _45 = !copy _44;\n"
        b"        assert(copy _45 == true, \"arithmetic overflow\") -> [return: bb25, unwind: bb26];\n"
        b"    }\n"
        b"    bb24: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"    bb25: {\n"
        b"        _37 = move _38 + copy _32;\n"
        b"        _36 = move _37 == const 36;\n"
        b"        switchInt(move _36) -> [0: bb28, otherwise: bb27];\n"
        b"    }\n"
        b"    bb26: {\n"
        b"        unreachable;\n"
        b"    }\n"
        b"    bb27: {\n"
        b"        switchInt(copy _34) -> [0: bb31, otherwise: bb30];\n"
        b"    }\n"
        b"    bb28: {\n"
        b"        goto -> bb29;\n"
        b"    }\n"
        b"    bb29: {\n"
        b"        _0 = const 1;\n"
        b"        return;\n"
        b"    }\n"
        b"    bb30: {\n"
        b"        _0 = const 0;\n"
        b"        return;\n"
        b"    }\n"
        b"    bb31: {\n"
        b"        goto -> bb32;\n"
        b"    }\n"
        b"    bb32: {\n"
        b"        goto -> bb29;\n"
        b"    }\n"
        b"}\n"
    ),
]

def load_opt_fixture_as_fn(rel_path, fn_name):
    src = read_bytes(os.path.join(ROOT, rel_path)).replace(b"\r\n", b"\n")
    target = b"fn main() -> i32"
    replacement = b"fn " + fn_name.encode("ascii") + b"() -> i32"
    replaced = src.replace(target, replacement, 1)
    if replaced == src:
        raise ValueError("expected %r in %s" % (target, rel_path))
    return replaced


PIPE_COMBINED_SRC = (
    load_opt_fixture_as_fn("tests/opt/const_fold_run.ax", "case_const_fold")
    + b"\n"
    + load_opt_fixture_as_fn("tests/opt/qa_dce_run.ax", "case_qa_dce")
    + b"\n"
    + load_opt_fixture_as_fn("tests/opt/qa_edge_cases_run.ax", "case_qa_edge_cases")
)

PIPE_BLOBS = [
    b"tests/selfhost/opt/pipeline_input.ax",
    PIPE_COMBINED_SRC,
    UNIT_MIR_SNIPPETS[14],
    UNIT_MIR_SNIPPETS[8],
    UNIT_MIR_SNIPPETS[16],
]


def str_literal(data):
    out = ['"']
    for b in data:
        if b == 10:
            out.append("\\n")
        elif b == 13:
            out.append("\\r")
        elif b == 9:
            out.append("\\t")
        elif b == 34:
            out.append('\\"')
        elif b == 92:
            out.append("\\\\")
        elif 32 <= b <= 126:
            out.append(chr(b))
        else:
            raise ValueError("non-ascii byte %d" % b)
    out.append('"')
    return "".join(out)


def str_fn(fn_name, blobs):
    lines = ["fn %s(idx: usize) -> str {" % fn_name]
    for i, b in enumerate(blobs):
        lines.append("    if idx == %d { return %s; }" % (i, str_literal(b)))
    lines.append('    ""')
    lines.append("}")
    return "\n".join(lines)


def build_qa_opt_unit():
    template = read_bytes(os.path.join(HERE, "harness_opt_unit.ax.in")).decode("utf-8")
    main_src = template.replace("@UNIT_MIR_FN@", str_fn("unit_mir_raw", UNIT_MIR_SNIPPETS))
    header = (
        "// test: run\n"
        "// timeout: 600\n"
        "// stdout: OK opt unit (const_fold + dce + cfg_simp + mir diff)\\n\n"
        "// Generated by tests/selfhost/opt/gen_opt_tests.py; do not edit.\n\n"
    )
    full_text = header + PRELUDE + "\n" + assemble_modules(CORE_MODULES) + "\n" + main_src
    out_path = os.path.join(HERE, "qa_opt_unit.ax")
    write_bytes(out_path, full_text.encode("utf-8"))
    print("wrote", os.path.relpath(out_path, ROOT).replace(os.sep, "/"))


def build_qa_opt_pipeline():
    template = read_bytes(os.path.join(HERE, "harness_opt_pipeline.ax.in")).decode("utf-8")
    main_src = template.replace("@PIPE_FN@", str_fn("pipe_raw", PIPE_BLOBS))
    header = (
        "// test: run\n"
        "// timeout: 1200\n"
        "// stdout: OK opt pipeline\\n\n"
        "// Generated by tests/selfhost/opt/gen_opt_tests.py; do not edit.\n\n"
    )
    full_text = header + PRELUDE + "\n" + assemble_modules(PIPELINE_MODULES) + "\n" + main_src
    out_path = os.path.join(HERE, "qa_opt_pipeline.ax")
    write_bytes(out_path, full_text.encode("utf-8"))
    print("wrote", os.path.relpath(out_path, ROOT).replace(os.sep, "/"))


def main():
    build_qa_opt_unit()
    build_qa_opt_pipeline()
    return 0


if __name__ == "__main__":
    sys.exit(main())
