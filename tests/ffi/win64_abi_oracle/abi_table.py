#!/usr/bin/env python3
"""T503: single source of truth of the external Windows x64 ABI oracle (ADR-0034 §8 OI-12).

One table of scalar signatures, by-value structs and layout structs is rendered into
  * a C file built with `gcc -shared` (the oracle: gcc implements the Microsoft x64 ABI), and
  * an Axiom program that links the DLL with `@link` and checks every value in both directions.
Expected results come from the Python reference below (FNV-style mix over raw bit patterns and a
Python C-layout algorithm) and from the gcc-built DLL itself; the Axiom compiler under test is a
third, independent opinion. Python 3 standard library only.
"""

import struct

M64 = (1 << 64) - 1
H0 = 0xCBF29CE484222325


def mix(h, v):
    h = ((h ^ (v & M64)) * 0x100000001B3) & M64
    return ((h << 13) | (h >> 51)) & M64


class Lcg(object):
    """Own generator: the sequence must not depend on the Python version."""

    def __init__(self, seed):
        self.s = seed & M64

    def next(self):
        self.s = (self.s * 6364136223846793005 + 1442695040888963407) & M64
        return self.s >> 33


# ---------------------------------------------------------------------------- scalar types
# name -> (C type, Axiom type, bit width, kind, values as raw unsigned bit patterns)
TYPES = {
    "i8": ("int8_t", "i8", 8, "sint", [0x80, 0xFF, 0x7F, 0xB3, 0x01]),
    "u8": ("uint8_t", "u8", 8, "uint", [0xFF, 0x80, 0x01, 0xA5, 0x00]),
    "i16": ("int16_t", "i16", 16, "sint", [0x8000, 0xFFFF, 0x7FFF, 0xC0DE, 0x0102]),
    "u16": ("uint16_t", "u16", 16, "uint", [0xFFFF, 0x8000, 0x0001, 0xBEEF, 0x1234]),
    "i32": ("int32_t", "i32", 32, "sint", [0x80000000, 0xFFFFFFFF, 0x7FFFFFFF, 0x12345678, 0xDEADBEEF]),
    "u32": ("uint32_t", "u32", 32, "uint", [0xFFFFFFFF, 0x80000000, 0x00000001, 0xCAFEBABE, 0x0F0F0F0F]),
    "i64": ("int64_t", "i64", 64, "sint",
            [0x8000000000000000, 0xFFFFFFFFFFFFFFFF, 0x7FFFFFFFFFFFFFFF, 0x1122334455667788]),
    "u64": ("uint64_t", "u64", 64, "uint",
            [0xFFFFFFFFFFFFFFFF, 0x8000000000000000, 0x0123456789ABCDEF, 0x0000000000000001, 0xFEDCBA9876543210]),
    "f32": ("float", "f32", 32, "f32", [0x80000000, 0x3FC00000, 0x7F7FFFFF, 0x00000001, 0xC2F6E666]),
    "f64": ("double", "f64", 64, "f64",
            [0x8000000000000000, 0x7E37E43C8800759C, 0x0000000000000001, 0xBF6475A1CAC08312,
             0x400921FB54442D18]),
    "p": ("const uint8_t *", "*const u8", 64, "ptr",
          [0x00007FF612345678, 0x0000000000000008, 0x00007FFFFFFFFFF0, 0x0000123456789ABC]),
}

SCALAR_ARG_TYPES = ["i8", "u16", "i32", "u64", "f32", "f64", "p"]
FIELD_TYPES = ["i8", "u8", "i16", "u16", "i32", "u32", "u64", "f32", "f64"]


def tvals(t):
    return TYPES[t][4]


def val(t, i):
    v = tvals(t)
    return v[i % len(v)]


def hbits(t, bits):
    """Value of a raw bit pattern as seen by the hash (zero-extended to 64 bits)."""
    return bits & M64


def c_lit(t, bits):
    kind = TYPES[t][3]
    w = TYPES[t][2]
    if kind == "sint":
        sv = bits - (1 << w) if bits >> (w - 1) else bits
        if sv == -(1 << (w - 1)):
            return "(%s)(-%d - 1)" % (TYPES[t][0], (1 << (w - 1)) - 1)
        return "(%s)(%d)" % (TYPES[t][0], sv)
    if kind == "uint":
        return "(%s)0x%XULL" % (TYPES[t][0], bits)
    if kind == "f32":
        return "F32(0x%08XU)" % bits
    if kind == "f64":
        return "F64(0x%016XULL)" % bits
    return "(const uint8_t *)0x%XULL" % bits


def ax_lit(t, bits):
    kind = TYPES[t][3]
    w = TYPES[t][2]
    name = TYPES[t][1]
    if kind == "sint":
        sv = bits - (1 << w) if bits >> (w - 1) else bits
        if sv == -(1 << (w - 1)):
            return "(-%d%s - 1%s)" % ((1 << (w - 1)) - 1, name, name)
        if sv < 0:
            return "(-%d%s)" % (-sv, name)
        return "%d%s" % (sv, name)
    if kind == "uint":
        return "0x%X%s" % (bits, name)
    if kind == "f32":
        return "from_bits_f32(0x%08Xu32)" % bits
    if kind == "f64":
        return "from_bits_f64(0x%016Xu64)" % bits
    return "(0x%Xusize as *const u8)" % bits


def ax_ne(t, expr, bits):
    """Axiom boolean expression: `expr` differs (bitwise for floats) from the pattern."""
    kind = TYPES[t][3]
    if kind == "f32":
        return "to_bits_f32(%s) != 0x%08Xu32" % (expr, bits)
    if kind == "f64":
        return "to_bits_f64(%s) != 0x%016Xu64" % (expr, bits)
    if kind == "ptr":
        return "(%s as usize) != 0x%Xusize" % (expr, bits)
    return "%s != %s" % (expr, ax_lit(t, bits))


def c_bits(t, expr):
    kind = TYPES[t][3]
    if kind == "f32":
        return "bf32(%s)" % expr
    if kind == "f64":
        return "bf64(%s)" % expr
    if kind == "ptr":
        return "(uint64_t)(uintptr_t)(%s)" % expr
    return "(uint64_t)(uint%d_t)(%s)" % (TYPES[t][2], expr)


# ---------------------------------------------------------------------------- scalar signatures
def scalar_sigs():
    sigs = []
    rng = Lcg(503)
    ints = ["i8", "u16", "i32", "u64"]
    for n in range(1, 9):
        v0 = [ints[i % 4] for i in range(n)]
        v1 = [["f32", "f64"][i % 2] for i in range(n)]
        v2 = [["i32", "f64", "u64", "f32", "i8", "f64", "u16", "f32"][i] for i in range(n)]
        v3 = [["f64", "i8", "f32", "u64", "f64", "u16", "f32", "p"][i] for i in range(n)]
        variants = [v0, v1, v2, v3]
        for _ in range(4):
            variants.append([SCALAR_ARG_TYPES[rng.next() % 7] for _ in range(n)])
        for k, types in enumerate(variants):
            sid = n * 10 + k
            args = [(t, val(t, sid * 7 + i * 3)) for i, t in enumerate(types)]
            sigs.append({"name": "%d_%d" % (n, k), "sid": sid, "args": args})
    return sigs


def sig_hash(sig):
    h = H0
    for t, b in sig["args"]:
        h = mix(h, hbits(t, b))
    return h


# ---------------------------------------------------------------------------- by-value structs
# size is computed (and cross-checked against gcc by the layout test).
STRUCTS = [
    ("A1", ["u8"]), ("A2", ["u8", "u8"]), ("A3", ["u8", "u8", "u8"]), ("A4", ["u16", "i8", "u8"]),
    ("A5", ["u8", "u8", "u8", "u8", "u8"]), ("A6", ["u16", "u16", "u16"]),
    ("A7", ["u8", "u8", "u8", "u8", "u8", "u8", "u8"]),
    ("A8", ["u32", "u32"]), ("F8", ["f32", "f32"]), ("D8", ["f64"]), ("P8", ["u8", "u32"]),
    ("A12", ["u32", "u32", "u32"]), ("F12", ["f32", "f32", "f32"]), ("P12", ["u8", "u32", "u8"]),
    ("A16", ["u64", "u64"]), ("D16", ["f64", "f64"]), ("M16", ["f64", "u64"]),
    ("A24", ["u64", "u64", "u64"]), ("M24", ["u8", "f64", "u16"]), ("Q24", ["i32", "f32", "u64", "f64"]),
]


def tsize(t):
    return TYPES[t][2] // 8


def struct_layout(fields):
    off = 0
    al = 1
    offs = []
    for f in fields:
        s = tsize(f)
        off = (off + s - 1) // s * s
        offs.append(off)
        off += s
        al = max(al, s)
    return (off + al - 1) // al * al, al, offs


def struct_inst(si, fields, inst):
    return [val(f, si * 5 + i * 3 + inst) for i, f in enumerate(fields)]


def struct_hash(si, fields, inst):
    h = H0
    for f, b in zip(fields, struct_inst(si, fields, inst)):
        h = mix(h, hbits(f, b))
    return h


# mixed-position shapes: (a: i8, s: S, d: f64, e: u16, s2: S, g: f32)
MIX_A, MIX_D, MIX_E, MIX_G = ("i8", 1), ("f64", 2), ("u16", 3), ("f32", 4)


def mix_hash(si, fields):
    h = H0
    h = mix(h, val("i8", si))
    for f, b in zip(fields, struct_inst(si, fields, 0)):
        h = mix(h, b)
    h = mix(h, val("f64", si + 1))
    h = mix(h, val("u16", si + 2))
    for f, b in zip(fields, struct_inst(si, fields, 1)):
        h = mix(h, b)
    h = mix(h, val("f32", si + 3))
    return h


def last_hash(sel, xbits, ybits):
    h = H0
    h = mix(h, sel)
    h = mix(h, xbits)
    h = mix(h, ybits)
    return h


# ---------------------------------------------------------------------------- layout structs
# type expressions: ("t", name) | ("arr", expr, n) | ("s", structname)
LAYOUT_BASE = {
    "bool": ("bool", "bool", 1, 1),
    "usize": ("uintptr_t", "usize", 8, 8),
    "ptr": ("const uint8_t *", "*const u8", 8, 8),
}


def _t(name):
    return ("t", name)


LAYOUT_STRUCTS = [
    ("L_pad1", [("a", _t("u8")), ("b", _t("u64")), ("c", _t("u8"))]),
    ("L_ladder", [("a", _t("u8")), ("b", _t("u16")), ("c", _t("u32")), ("d", _t("u64"))]),
    ("L_down", [("a", _t("i8")), ("b", _t("i8")), ("c", _t("i16")), ("d", _t("i32")), ("e", _t("u64"))]),
    ("L_fmix", [("a", _t("f32")), ("b", _t("u8")), ("c", _t("f64"))]),
    ("L_tail", [("a", _t("u64")), ("b", _t("u8"))]),
    ("L_ptr", [("a", _t("u8")), ("p", _t("ptr")), ("b", _t("u8")), ("n", _t("usize"))]),
    ("L_bool", [("a", _t("u8")), ("b", _t("bool")), ("c", _t("u32")), ("d", _t("bool"))]),
    ("L_arr", [("a", _t("u8")), ("b", ("arr", _t("u16"), 3)), ("c", _t("u8")), ("d", ("arr", _t("u8"), 5)),
               ("e", _t("u32"))]),
    ("L_arr2", [("a", ("arr", _t("u8"), 3)), ("b", ("arr", _t("f64"), 2)), ("c", _t("i16"))]),
    ("L_inner", [("a", _t("u8")), ("b", _t("u32"))]),
    ("L_nest", [("a", _t("u8")), ("i", ("s", "L_inner")), ("b", _t("u16")), ("j", ("s", "L_inner")),
                ("c", _t("u8"))]),
    ("L_nest8", [("a", _t("u8")), ("i", ("s", "L_ladder")), ("b", _t("u8"))]),
]
# every by-value ABI struct is a layout row too
for _si, (_n, _f) in enumerate(STRUCTS):
    LAYOUT_STRUCTS.append(("S_" + _n, [("f%d" % i, _t(t)) for i, t in enumerate(_f)]))


def _lay_type(expr, structs):
    """(size, align) of a type expression using the Python C-layout algorithm."""
    if expr[0] == "t":
        n = expr[1]
        if n in LAYOUT_BASE:
            return LAYOUT_BASE[n][2], LAYOUT_BASE[n][3]
        s = tsize(n)
        return s, s
    if expr[0] == "arr":
        s, a = _lay_type(expr[1], structs)
        return s * expr[2], a
    sz, al, _ = py_layout(expr[1], structs)
    return sz, al


def py_layout(name, structs=None):
    structs = dict(LAYOUT_STRUCTS) if structs is None else structs
    off = 0
    al = 1
    offs = []
    for _fname, fty in structs[name]:
        s, a = _lay_type(fty, structs)
        off = (off + a - 1) // a * a
        offs.append(off)
        off += s
        al = max(al, a)
    return (off + al - 1) // al * al, al, offs


def c_type(expr):
    if expr[0] == "t":
        n = expr[1]
        return LAYOUT_BASE[n][0] if n in LAYOUT_BASE else TYPES[n][0]
    if expr[0] == "s":
        return expr[1]
    return None


def ax_type(expr):
    if expr[0] == "t":
        n = expr[1]
        return LAYOUT_BASE[n][1] if n in LAYOUT_BASE else TYPES[n][1]
    if expr[0] == "s":
        return expr[1]
    return "[%d]%s" % (expr[2], ax_type(expr[1]))


def c_layout_source():
    """Prints `name size align off0 off1 ...` per layout struct, as seen by gcc."""
    o = ["#include <stdint.h>", "#include <stddef.h>", "#include <stdio.h>", "#include <stdbool.h>", ""]
    for name, fields in LAYOUT_STRUCTS:
        o.append("typedef struct {")
        for fname, fty in fields:
            if fty[0] == "arr":
                o.append("    %s %s[%d];" % (c_type(fty[1]), fname, fty[2]))
            else:
                o.append("    %s %s;" % (c_type(fty), fname))
        o.append("} %s;" % name)
    o.append("")
    o.append("int main(void) {")
    for name, fields in LAYOUT_STRUCTS:
        offs = " ".join("%zu" for _ in fields)
        args = ", ".join("offsetof(%s, %s)" % (name, f) for f, _ in fields)
        o.append('    printf("%s %%zu %%zu %s\\n", sizeof(%s), _Alignof(%s), %s);' % (name, offs, name, name, args))
    o.append("    return 0;")
    o.append("}")
    return "\n".join(o) + "\n"


def ax_default(expr):
    if expr[0] == "t":
        n = expr[1]
        if n == "bool":
            return "false"
        if n == "usize":
            return "0usize"
        if n == "ptr":
            return "(0usize as *const u8)"
        k = TYPES[n][3]
        if k == "f32":
            return "0.0f32"
        if k == "f64":
            return "0.0"
        return "0%s" % TYPES[n][1]
    if expr[0] == "arr":
        return "[" + ", ".join(ax_default(expr[1]) for _ in range(expr[2])) + "]"
    return "%s_zero()" % expr[1]


def ax_layout_program(table, mutate=()):
    """`table`: name -> (size, align, [offsets]) as printed by gcc."""
    o = ["// generated by tests/ffi/win64_abi_oracle/abi_table.py (T503): do not edit",
         "@intrinsic fn size_of<T>() -> usize { 0 }",
         "@intrinsic fn align_of<T>() -> usize { 0 }",
         "@intrinsic unsafe fn address_of<T>(val: T) -> *const T { 0 as *const T }", ""]
    for name, fields in LAYOUT_STRUCTS:
        o.append("@repr(C)")
        o.append("struct %s {" % name)
        for fname, fty in fields:
            o.append("    %s: %s," % (fname, ax_type(fty)))
        o.append("}")
        o.append("fn %s_zero() -> %s {" % (name, name))
        o.append("    return %s {" % name)
        for fname, fty in fields:
            o.append("        %s: %s," % (fname, ax_default(fty)))
        o.append("    };")
        o.append("}")
        o.append("")
    checks = 0
    for name, fields in LAYOUT_STRUCTS:
        size, al, offs = table[name]
        if name in mutate:
            size += 1
        o.append("fn check_%s() -> i32 {" % name)
        o.append("    let mut bad: i32 = 0;")
        o.append("    let s = %s_zero();" % name)
        o.append("    let base = unsafe { address_of(s) } as usize;")
        o.append("    if size_of<%s>() != %dusize { print(\"FAIL sizeof %s\\n\"); bad = bad + 1; }" % (name, size, name))
        o.append("    if align_of<%s>() != %dusize { print(\"FAIL alignof %s\\n\"); bad = bad + 1; }" % (name, al, name))
        checks += 2
        for (fname, _fty), off in zip(fields, offs):
            o.append("    if (unsafe { address_of(s.%s) } as usize) - base != %dusize { "
                     "print(\"FAIL offsetof %s.%s\\n\"); bad = bad + 1; }" % (fname, off, name, fname))
            checks += 1
        o.append("    return bad;")
        o.append("}")
        o.append("")
    o.append("fn main() -> i32 {")
    o.append("    let mut bad: i32 = 0;")
    for name, _ in LAYOUT_STRUCTS:
        o.append("    bad = bad + check_%s();" % name)
    o.append("    if bad != 0 { return bad; }")
    o.append("    print(\"WIN64-LAYOUT ok %d checks\\n\");" % checks)
    o.append("    return 0;")
    o.append("}")
    return "\n".join(o) + "\n", checks


# ---------------------------------------------------------------------------- DLL (C side)
C_PRELUDE = """\
/* generated by tests/ffi/win64_abi_oracle/abi_table.py (T503): do not edit */
#include <stdint.h>
#include <string.h>

#define EXPORT __declspec(dllexport)

static inline float F32(uint32_t b) { float f; memcpy(&f, &b, 4); return f; }
static inline double F64(uint64_t b) { double d; memcpy(&d, &b, 8); return d; }
static inline uint64_t bf32(float f) { uint32_t b; memcpy(&b, &f, 4); return b; }
static inline uint64_t bf64(double d) { uint64_t b; memcpy(&b, &d, 8); return b; }
static inline uint64_t mix(uint64_t h, uint64_t v) {
    h = (h ^ v) * 0x100000001B3ULL;
    return (h << 13) | (h >> 51);
}
#define H0 0xCBF29CE484222325ULL
static uint64_t g_last;
"""


def c_dll_source(mutate=()):
    o = [C_PRELUDE]
    mut = lambda name: " ^ 1ULL" if name in mutate else ""  # noqa: E731
    # --- scalar signatures: Axiom -> C (hash of the raw bits) and C -> Axiom callback
    for s in scalar_sigs():
        ps = ", ".join("%s a%d" % (TYPES[t][0], i) for i, (t, _) in enumerate(s["args"]))
        o.append("EXPORT uint64_t sc_%s(%s) {" % (s["name"], ps))
        o.append("    uint64_t h = H0;")
        for i, (t, _) in enumerate(s["args"]):
            o.append("    h = mix(h, %s);" % c_bits(t, "a%d" % i))
        o.append("    return h%s;" % mut("sc_" + s["name"]))
        o.append("}")
        ts = ", ".join(TYPES[t][0] for t, _ in s["args"])
        cs = ", ".join(c_lit(t, b) for t, b in s["args"])
        o.append("EXPORT uint64_t cs_%s(uint64_t (*cb)(%s)) { return cb(%s); }" % (s["name"], ts, cs))
        o.append("")
    # --- scalar returns and echoes
    for t in SCALAR_ARG_TYPES:
        ct = TYPES[t][0]
        o.append("EXPORT %s rt_%s(uint32_t sel) {" % (ct, t))
        o.append("    switch (sel) {")
        for i, b in enumerate(tvals(t)):
            o.append("    case %d: return %s;" % (i, c_lit(t, b)))
        o.append("    }")
        o.append("    return %s;" % c_lit(t, tvals(t)[0]))
        o.append("}")
        o.append("EXPORT %s ec_%s(%s x) { return x; }" % (ct, t, ct))
        o.append("EXPORT uint64_t cr_%s(%s (*cb)(uint32_t)) {" % (t, ct))
        o.append("    uint64_t h = H0;")
        for i in range(len(tvals(t))):
            o.append("    h = mix(h, %s);" % c_bits(t, "cb(%d)" % i))
        o.append("    return h;")
        o.append("}")
        o.append("")
    # --- by-value structs
    for si, (n, fields) in enumerate(STRUCTS):
        o.append("typedef struct { " + " ".join("%s f%d;" % (TYPES[t][0], i) for i, t in enumerate(fields)) +
                 " } S_%s;" % n)
    o.append("")
    for si, (n, fields) in enumerate(STRUCTS):
        S = "S_" + n
        inst = [", ".join(c_lit(t, b) for t, b in zip(fields, struct_inst(si, fields, k))) for k in (0, 1)]
        hs = lambda var: "".join("    h = mix(h, %s);\n" % c_bits(t, "%s.f%d" % (var, i))  # noqa: E731
                                  for i, t in enumerate(fields))
        o.append("static inline %s i0_%s(void) { %s r = { %s }; return r; }" % (S, n, S, inst[0]))
        o.append("static inline %s i1_%s(void) { %s r = { %s }; return r; }" % (S, n, S, inst[1]))
        o.append("EXPORT uint64_t si_%s(%s s) {\n    uint64_t h = H0;\n%s    return h%s;\n}" %
                 (n, S, hs("s"), mut("si_" + n)))
        o.append("EXPORT %s so_%s(uint32_t sel, double x, uint8_t y) {\n"
                 "    g_last = mix(mix(mix(H0, sel), bf64(x)), y);\n"
                 "    return (sel & 1) ? i1_%s() : i0_%s();\n}" % (S, n, n, n))
        o.append("EXPORT uint64_t sc_in_%s(uint64_t (*cb)(%s)) { return cb(i0_%s()); }" % (n, S, n))
        o.append("EXPORT uint64_t sc_out_%s(%s (*cb)(uint32_t)) {\n    %s r = cb(1);\n    uint64_t h = H0;\n%s"
                 "    return h;\n}" % (n, S, S, hs("r")))
        o.append("EXPORT uint64_t sm_%s(int8_t a, %s s, double d, uint16_t e, %s s2, float g) {\n"
                 "    uint64_t h = H0;\n    h = mix(h, %s);\n%s    h = mix(h, bf64(d));\n"
                 "    h = mix(h, e);\n%s    h = mix(h, bf32(g));\n    return h;\n}" %
                 (n, S, S, c_bits("i8", "a"), hs("s"), hs("s2")))
        o.append("EXPORT uint64_t sm_cb_%s(uint64_t (*cb)(int8_t, %s, double, uint16_t, %s, float)) {\n"
                 "    return cb(%s, i0_%s(), %s, %s, i1_%s(), %s);\n}" %
                 (n, S, S, c_lit("i8", val("i8", si)), n, c_lit("f64", val("f64", si + 1)),
                  c_lit("u16", val("u16", si + 2)), n, c_lit("f32", val("f32", si + 3))))
        o.append("")
    o.append("EXPORT uint64_t sg_last(void) { return g_last; }")
    o.append("")
    return "\n".join(o) + "\n"


# ---------------------------------------------------------------------------- Axiom side
AX_PRELUDE = """\
// generated by tests/ffi/win64_abi_oracle/abi_table.py (T503): do not edit
@intrinsic fn to_bits_f32(x: f32) -> u32 { 0u32 }
@intrinsic fn from_bits_f32(v: u32) -> f32 { 0.0 }
@intrinsic fn to_bits_f64(x: f64) -> u64 { 0u64 }
@intrinsic fn from_bits_f64(v: u64) -> f64 { 0.0 }

"""


def ax_program(dll, mutate=()):
    ext = []        # extern declarations
    defs = []       # structs and callbacks
    tests = []      # test functions
    checks = [0]

    def failure(label):
        return 'print("FAIL %s\\n"); bad = bad + 1;' % label

    def check_eq(fn_lines, label, expr, bits, ty="u64"):
        checks[0] += 1
        fn_lines.append("    if %s { %s }" % (ax_ne(ty, expr, bits), failure(label)))

    # ---- scalars
    sc = ["fn t_scalar_calls() -> i32 {", "    let mut bad: i32 = 0;"]
    cb_tests = ["fn t_scalar_callbacks() -> i32 {", "    let mut bad: i32 = 0;"]
    rng = Lcg(0xC0FFEE)
    for s in scalar_sigs():
        n = s["name"]
        params = ", ".join("a%d: %s" % (i, TYPES[t][1]) for i, (t, _) in enumerate(s["args"]))
        ext.append("    fn sc_%s(%s) -> u64;" % (n, params))
        cbty = "extern \"C\" fn(%s) -> u64" % ", ".join(TYPES[t][1] for t, _ in s["args"])
        ext.append("    fn cs_%s(cb: %s) -> u64;" % (n, cbty))
        lits = ", ".join(ax_lit(t, b) for t, b in s["args"])
        exp = sig_hash(s)
        if "sc_" + n in mutate:
            pass  # the C side is mutated for this one
        check_eq(sc, "sc_" + n, "unsafe { sc_%s(%s) }" % (n, lits), exp)
        magic = (rng.next() << 31) ^ rng.next()
        magic |= 1 << 63
        body = ["extern \"C\" fn cb_%s(%s) -> u64 {" % (n, params), "    let mut m: u64 = 0u64;"]
        for i, (t, b) in enumerate(s["args"]):
            body.append("    if %s { m = m | %du64; }" % (ax_ne(t, "a%d" % i, b), 1 << i))
        body.append("    return 0x%Xu64 ^ m;" % magic)
        body.append("}")
        defs.extend(body)
        defs.append("")
        exp_cb = magic ^ (1 if ("cb_" + n) in mutate else 0)
        # for the callback direction the mutation flips the expected magic
        check_eq(cb_tests, "cs_" + n, "unsafe { cs_%s(cb_%s) }" % (n, n), exp_cb)
    sc.append("    return bad;")
    sc.append("}")
    cb_tests.append("    return bad;")
    cb_tests.append("}")
    tests += [sc, cb_tests]

    # ---- scalar returns / echoes / callbacks returning scalars
    rt = ["fn t_scalar_returns() -> i32 {", "    let mut bad: i32 = 0;"]
    for t in SCALAR_ARG_TYPES:
        ax = TYPES[t][1]
        ext.append("    fn rt_%s(sel: u32) -> %s;" % (t, ax))
        ext.append("    fn ec_%s(x: %s) -> %s;" % (t, ax, ax))
        ext.append("    fn cr_%s(cb: extern \"C\" fn(u32) -> %s) -> u64;" % (t, ax))
        for i, b in enumerate(tvals(t)):
            check_eq(rt, "rt_%s(%d)" % (t, i), "unsafe { rt_%s(%du32) }" % (t, i), b, t)
            check_eq(rt, "ec_%s(%d)" % (t, i), "unsafe { ec_%s(%s) }" % (t, ax_lit(t, b)), b, t)
        defs.append("extern \"C\" fn cbr_%s(sel: u32) -> %s {" % (t, ax))
        for i, b in enumerate(tvals(t)):
            defs.append("    if sel == %du32 { return %s; }" % (i, ax_lit(t, b)))
        defs.append("    return %s;" % ax_lit(t, tvals(t)[0]))
        defs.append("}")
        defs.append("")
        h = H0
        for b in tvals(t):
            h = mix(h, hbits(t, b))
        check_eq(rt, "cr_" + t, "unsafe { cr_%s(cbr_%s) }" % (t, t), h)
    rt.append("    return bad;")
    rt.append("}")
    tests.append(rt)

    # ---- by-value structs
    defs.insert(0, "")
    structs_ax = []
    st = ["fn t_struct_%s() -> i32 {"]
    for si, (n, fields) in enumerate(STRUCTS):
        S = "S_" + n
        structs_ax.append("@repr(C)")
        structs_ax.append("struct %s { %s }" % (S, ", ".join("f%d: %s" % (i, TYPES[t][1])
                                                              for i, t in enumerate(fields))))
        structs_ax.append("")

        def lit(k):
            return "%s { %s }" % (S, ", ".join("f%d: %s" % (i, ax_lit(t, b))
                                              for i, (t, b) in enumerate(zip(fields, struct_inst(si, fields, k)))))

        def mism(var, k, mv="m"):
            return "; ".join("if %s { %s = %s | %du64; }" % (ax_ne(t, "%s.f%d" % (var, i), b), mv, mv, 1 << i)
                            for i, (t, b) in enumerate(zip(fields, struct_inst(si, fields, k))))

        ext.append("    fn si_%s(s: %s) -> u64;" % (n, S))
        ext.append("    fn so_%s(sel: u32, x: f64, y: u8) -> %s;" % (n, S))
        ext.append("    fn sc_in_%s(cb: extern \"C\" fn(%s) -> u64) -> u64;" % (n, S))
        ext.append("    fn sc_out_%s(cb: extern \"C\" fn(u32) -> %s) -> u64;" % (n, S))
        ext.append("    fn sm_%s(a: i8, s: %s, d: f64, e: u16, s2: %s, g: f32) -> u64;" % (n, S, S))
        ext.append("    fn sm_cb_%s(cb: extern \"C\" fn(i8, %s, f64, u16, %s, f32) -> u64) -> u64;" % (n, S, S))
        magic1 = (Lcg(si + 1).next() << 20) | (1 << 63) | 0x5A5A
        magic2 = (Lcg(si + 77).next() << 20) | (1 << 63) | 0xA5A5
        defs.append("extern \"C\" fn cbi_%s(s: %s) -> u64 {" % (n, S))
        defs.append("    let mut m: u64 = 0u64;")
        defs.append("    " + mism("s", 0))
        defs.append("    return 0x%Xu64 ^ m;" % magic1)
        defs.append("}")
        defs.append("extern \"C\" fn cbo_%s(sel: u32) -> %s {" % (n, S))
        defs.append("    if (sel & 1u32) == 1u32 { return %s; }" % lit(1))
        defs.append("    return %s;" % lit(0))
        defs.append("}")
        defs.append("extern \"C\" fn cbm_%s(a: i8, s: %s, d: f64, e: u16, s2: %s, g: f32) -> u64 {" % (n, S, S))
        defs.append("    let mut m: u64 = 0u64;")
        defs.append("    if %s { m = m | 1u64; }" % ax_ne("i8", "a", val("i8", si)))
        defs.append("    " + mism("s", 0))
        defs.append("    if %s { m = m | 1u64; }" % ax_ne("f64", "d", val("f64", si + 1)))
        defs.append("    if %s { m = m | 1u64; }" % ax_ne("u16", "e", val("u16", si + 2)))
        defs.append("    " + mism("s2", 1))
        defs.append("    if %s { m = m | 1u64; }" % ax_ne("f32", "g", val("f32", si + 3)))
        defs.append("    return 0x%Xu64 ^ m;" % magic2)
        defs.append("}")
        defs.append("")

        fn = ["fn t_struct_%s() -> i32 {" % n, "    let mut bad: i32 = 0;", "    let v0 = %s;" % lit(0), "    let v1 = %s;" % lit(1), "    let w0 = %s;" % lit(0)]
        check_eq(fn, "si_" + n, "unsafe { si_%s(%s) }" % (n, "v0"), struct_hash(si, fields, 0))
        for sel in (0, 1):
            xb, yb = val("f64", si + sel), val("u8", si + sel)
            fn.append("    let r%d = unsafe { so_%s(%du32, %s, %s) };" % (sel, n, sel, ax_lit("f64", xb),
                                                                         ax_lit("u8", yb)))
            fn.append("    let mut m%d: u64 = 0u64;" % sel)
            fn.append("    " + mism("r%d" % sel, sel, "m%d" % sel))
            checks[0] += 1
            fn.append("    if m%d != 0u64 { %s }" % (sel, failure("so_%s(%d) fields" % (n, sel))))
            check_eq(fn, "sg_last after so_%s(%d)" % (n, sel), "unsafe { sg_last() }",
                     last_hash(sel, xb, yb))
        check_eq(fn, "sc_in_" + n, "unsafe { sc_in_%s(cbi_%s) }" % (n, n), magic1)
        check_eq(fn, "sc_out_" + n, "unsafe { sc_out_%s(cbo_%s) }" % (n, n), struct_hash(si, fields, 1))
        mexp = mix_hash(si, fields)
        check_eq(fn, "sm_" + n, "unsafe { sm_%s(%s, %s, %s, %s, %s, %s) }" %
                 (n, ax_lit("i8", val("i8", si)), "w0", ax_lit("f64", val("f64", si + 1)),
                  ax_lit("u16", val("u16", si + 2)), "v1", ax_lit("f32", val("f32", si + 3))), mexp)
        check_eq(fn, "sm_cb_" + n, "unsafe { sm_cb_%s(cbm_%s) }" % (n, n), magic2)
        fn.append("    return bad;")
        fn.append("}")
        tests.append(fn)

    out = [AX_PRELUDE]
    out.extend(structs_ax)
    out.append("@link(\"%s\")" % dll)
    out.append("extern \"C\" {")
    out.append("    fn sg_last() -> u64;")
    out.extend(ext)
    out.append("}")
    out.append("")
    out.extend(defs)
    names = []
    for t in tests:
        out.extend(t)
        out.append("")
        names.append(t[0].split()[1].split("(")[0])
    out.append("fn main() -> i32 {")
    out.append("    let mut bad: i32 = 0;")
    for nm in names:
        out.append("    bad = bad + %s();" % nm)
    out.append("    if bad != 0 { return bad; }")
    out.append("    print(\"WIN64-ABI-CALLS ok %d checks\\n\");" % checks[0])
    out.append("    return 0;")
    out.append("}")
    return "\n".join(out) + "\n", checks[0]
