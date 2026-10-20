#include "mir/build/intrinsics.h"
#include <string.h>

/* Width suffixes in AxIntrinsicWidth order (index 0 is AX_INTR_W_NONE). */
static const char *const k_width_suffix[] = {
    "", "i8", "i16", "i32", "i64", "isize", "u8", "u16", "u32", "u64", "usize"
};
#define AX_INTR_WIDTH_COUNT 11

/* clang-format off */
static const AxIntrinsicDesc k_table[] = {
    /* name                      class             op                          builtin_ty                              per_width gen sig */
    /* typeck retypes the callee to the AX_TY_BUILTIN_* kind carried in this table (via pipeline annotation) */
    { "size_of",                 AX_INTR_BUILTIN,  AX_INTR_OP_NONE,            AX_TY_BUILTIN_SIZE_OF,                  false, 1, ">usize" },
    { "align_of",                AX_INTR_BUILTIN,  AX_INTR_OP_NONE,            AX_TY_BUILTIN_ALIGN_OF,                 false, 1, ">usize" },
    { "needs_drop",              AX_INTR_BUILTIN,  AX_INTR_OP_NONE,            AX_TY_BUILTIN_NEEDS_DROP,               false, 1, ">bool" },
    { "drop_in_place",           AX_INTR_BUILTIN,  AX_INTR_OP_NONE,            AX_TY_BUILTIN_DROP_IN_PLACE,            false, 1, "*>unit" },
    { "forget",                  AX_INTR_BUILTIN,  AX_INTR_OP_NONE,            AX_TY_BUILTIN_FORGET,                   false, 1, "*>unit" },
    { "ptr_copy",                AX_INTR_BUILTIN,  AX_INTR_OP_NONE,            AX_TY_BUILTIN_PTR_COPY,                 false, 1, "*,*,usize>unit" },
    { "ptr_copy_nonoverlapping", AX_INTR_BUILTIN,  AX_INTR_OP_NONE,            AX_TY_BUILTIN_PTR_COPY_NONOVERLAPPING,  false, 1, "*,*,usize>unit" },
    { "ptr_write_bytes",         AX_INTR_BUILTIN,  AX_INTR_OP_NONE,            AX_TY_BUILTIN_PTR_WRITE_BYTES,          false, 1, "*,u8,usize>unit" },
    { "null",                    AX_INTR_BUILTIN,  AX_INTR_OP_NONE,            AX_TY_BUILTIN_NULL,                     false, 1, ">*" },
    { "null_mut",                AX_INTR_BUILTIN,  AX_INTR_OP_NONE,            AX_TY_BUILTIN_NULL_MUT,                 false, 1, ">*" },
    { "is_null",                 AX_INTR_BUILTIN,  AX_INTR_OP_NONE,            AX_TY_BUILTIN_IS_NULL,                  false, 1, "*>bool" },
    { "ptr_add",                 AX_INTR_BUILTIN,  AX_INTR_OP_NONE,            AX_TY_BUILTIN_PTR_ADD,                  false, 1, "*,usize>*" },
    { "ptr_sub",                 AX_INTR_BUILTIN,  AX_INTR_OP_NONE,            AX_TY_BUILTIN_PTR_SUB,                  false, 1, "*,usize>*" },
    { "address_of",              AX_INTR_BUILTIN,  AX_INTR_OP_NONE,            AX_TY_BUILTIN_ADDRESS_OF,               false, 1, "*>*" },
    { "address_of_mut",          AX_INTR_BUILTIN,  AX_INTR_OP_NONE,            AX_TY_BUILTIN_ADDRESS_OF_MUT,           false, 1, "*>*" },
    /* host intrinsics: calls of __ax_host_<name> (ADR-0002) */
    { "heap_alloc",              AX_INTR_HOST,     AX_INTR_OP_NONE,            0,                                      false, 0, "usize,usize>mp8" },
    { "heap_realloc",            AX_INTR_HOST,     AX_INTR_OP_NONE,            0,                                      false, 0, "mp8,usize,usize,usize>mp8" },
    { "heap_free",               AX_INTR_HOST,     AX_INTR_OP_NONE,            0,                                      false, 0, "mp8,usize,usize>unit" },
    { "stdio",                   AX_INTR_HOST,     AX_INTR_OP_NONE,            0,                                      false, 0, "u32>i64" },
    { "open",                    AX_INTR_HOST,     AX_INTR_OP_NONE,            0,                                      false, 0, "cp8,usize,u32>i64" },
    { "read",                    AX_INTR_HOST,     AX_INTR_OP_NONE,            0,                                      false, 0, "i64,mp8,usize>i64" },
    { "write",                   AX_INTR_HOST,     AX_INTR_OP_NONE,            0,                                      false, 0, "i64,cp8,usize>i64" },
    { "close",                   AX_INTR_HOST,     AX_INTR_OP_NONE,            0,                                      false, 0, "i64>i64" },
    { "file_size",               AX_INTR_HOST,     AX_INTR_OP_NONE,            0,                                      false, 0, "i64>i64" },
    { "args_count",              AX_INTR_HOST,     AX_INTR_OP_NONE,            0,                                      false, 0, ">usize" },
    { "arg",                     AX_INTR_HOST,     AX_INTR_OP_NONE,            0,                                      false, 0, "usize,mp8,usize>i64" },
    { "env_get",                 AX_INTR_HOST,     AX_INTR_OP_NONE,            0,                                      false, 0, "cp8,usize,mp8,usize>i64" },
    { "exe_path",                AX_INTR_HOST,     AX_INTR_OP_NONE,            0,                                      false, 0, "mp8,usize>i64" },
    { "exit",                    AX_INTR_HOST,     AX_INTR_OP_NONE,            0,                                      false, 0, "i32>unit|i32>never" },
    { "remove",                  AX_INTR_HOST,     AX_INTR_OP_NONE,            0,                                      false, 0, "cp8,usize>i64" },
    { "mkdir",                   AX_INTR_HOST,     AX_INTR_OP_NONE,            0,                                      false, 0, "cp8,usize>i64" },
    { "metadata",                AX_INTR_HOST,     AX_INTR_OP_NONE,            0,                                      false, 0, "cp8,usize,mp64>i64" },
    { "dir_open",                AX_INTR_HOST,     AX_INTR_OP_NONE,            0,                                      false, 0, "cp8,usize>i64" },
    { "dir_next",                AX_INTR_HOST,     AX_INTR_OP_NONE,            0,                                      false, 0, "i64,mp8,usize>i64" },
    { "dir_close",               AX_INTR_HOST,     AX_INTR_OP_NONE,            0,                                      false, 0, "i64>i64" },
    { "monotonic_ns",            AX_INTR_HOST,     AX_INTR_OP_NONE,            0,                                      false, 0, ">u64" },
    /* MIR terminators on the abort path (exit code 101, SPEC-03) */
    { "assert",                  AX_INTR_MIR_TERM, AX_INTR_OP_ASSERT,          0,                                      false, 0, "bool>unit" },
    { "panic",                   AX_INTR_MIR_TERM, AX_INTR_OP_PANIC,           0,                                      false, 0, ">unit|*>unit|>never|*>never" },
    { "unreachable",             AX_INTR_MIR_TERM, AX_INTR_OP_UNREACHABLE,     0,                                      false, 0, ">unit|>never" },
    /* wrapping and bit intrinsics, one per integer width */
    { "wrapping_add",            AX_INTR_MIR_OP,   AX_INTR_OP_WRAPPING_ADD,    0,                                      true,  0, "W,W>W" },
    { "wrapping_sub",            AX_INTR_MIR_OP,   AX_INTR_OP_WRAPPING_SUB,    0,                                      true,  0, "W,W>W" },
    { "wrapping_mul",            AX_INTR_MIR_OP,   AX_INTR_OP_WRAPPING_MUL,    0,                                      true,  0, "W,W>W" },
    { "wrapping_neg",            AX_INTR_MIR_OP,   AX_INTR_OP_WRAPPING_NEG,    0,                                      true,  0, "W>W" },
    { "rotate_left",             AX_INTR_MIR_OP,   AX_INTR_OP_ROTATE_LEFT,     0,                                      true,  0, "W,u32>W" },
    { "rotate_right",            AX_INTR_MIR_OP,   AX_INTR_OP_ROTATE_RIGHT,    0,                                      true,  0, "W,u32>W" },
    { "leading_zeros",           AX_INTR_MIR_OP,   AX_INTR_OP_LEADING_ZEROS,   0,                                      true,  0, "W>u32" },
    { "trailing_zeros",          AX_INTR_MIR_OP,   AX_INTR_OP_TRAILING_ZEROS,  0,                                      true,  0, "W>u32" },
    { "count_ones",              AX_INTR_MIR_OP,   AX_INTR_OP_COUNT_ONES,      0,                                      true,  0, "W>u32" },
};
/* clang-format on */

#define AX_INTR_TABLE_LEN (sizeof(k_table) / sizeof(k_table[0]))

bool ax_intrinsic_lookup(StrView name, AxIntrinsicRef *out) {
    /* Exact names first. */
    for (size_t i = 0; i < AX_INTR_TABLE_LEN; i++) {
        const AxIntrinsicDesc *d = &k_table[i];
        if (!d->per_width && ax_sv_eq_cstr(name, d->name)) {
            if (out) { out->desc = d; out->width = AX_INTR_W_NONE; }
            return true;
        }
    }
    /* `<family>_<width>`: split at the last underscore. */
    size_t cut = name.len;
    while (cut > 0 && name.ptr[cut - 1] != '_') cut--;
    if (cut == 0) return false;
    StrView prefix = ax_sv_slice(name, 0, cut - 1);
    StrView suffix = ax_sv_slice(name, cut, name.len - cut);
    AxIntrinsicWidth w = AX_INTR_W_NONE;
    for (int k = 1; k < AX_INTR_WIDTH_COUNT; k++) {
        if (ax_sv_eq_cstr(suffix, k_width_suffix[k])) { w = (AxIntrinsicWidth)k; break; }
    }
    if (w == AX_INTR_W_NONE) return false;
    for (size_t i = 0; i < AX_INTR_TABLE_LEN; i++) {
        const AxIntrinsicDesc *d = &k_table[i];
        if (d->per_width && ax_sv_eq_cstr(prefix, d->name)) {
            if (out) { out->desc = d; out->width = w; }
            return true;
        }
    }
    return false;
}

bool ax_intrinsic_is_host(StrView name) {
    AxIntrinsicRef r;
    return ax_intrinsic_lookup(name, &r) && r.desc->cls == AX_INTR_HOST;
}

uint32_t ax_intrinsic_encode(const AxIntrinsicRef *ref) {
    uint32_t idx = (uint32_t)(ref->desc - k_table);
    return ((idx + 1u) << 8) | (uint32_t)ref->width;
}

bool ax_intrinsic_decode(uint32_t code, AxIntrinsicRef *out) {
    uint32_t idx = code >> 8;
    if (idx == 0 || idx > AX_INTR_TABLE_LEN) return false;
    uint32_t w = code & 0xFFu;
    if (w >= AX_INTR_WIDTH_COUNT) return false;
    out->desc = &k_table[idx - 1];
    out->width = (AxIntrinsicWidth)w;
    return true;
}

TypeId ax_intrinsic_width_type(AxIntrinsicWidth w, const TypeInterner *in) {
    switch (w) {
        case AX_INTR_W_I8: return in->t_i8;
        case AX_INTR_W_I16: return in->t_i16;
        case AX_INTR_W_I32: return in->t_i32;
        case AX_INTR_W_I64: return in->t_i64;
        case AX_INTR_W_ISIZE: return in->t_isize;
        case AX_INTR_W_U8: return in->t_u8;
        case AX_INTR_W_U16: return in->t_u16;
        case AX_INTR_W_U32: return in->t_u32;
        case AX_INTR_W_U64: return in->t_u64;
        case AX_INTR_W_USIZE: return in->t_usize;
        default: return in->t_error;
    }
}

TypeId ax_intrinsic_width_unsigned_type(AxIntrinsicWidth w, const TypeInterner *in) {
    switch (w) {
        case AX_INTR_W_I8: case AX_INTR_W_U8: return in->t_u8;
        case AX_INTR_W_I16: case AX_INTR_W_U16: return in->t_u16;
        case AX_INTR_W_I32: case AX_INTR_W_U32: return in->t_u32;
        case AX_INTR_W_I64: case AX_INTR_W_U64: return in->t_u64;
        case AX_INTR_W_ISIZE: case AX_INTR_W_USIZE: return in->t_usize;
        default: return in->t_error;
    }
}

uint32_t ax_intrinsic_width_bits(AxIntrinsicWidth w) {
    switch (w) {
        case AX_INTR_W_I8: case AX_INTR_W_U8: return 8;
        case AX_INTR_W_I16: case AX_INTR_W_U16: return 16;
        case AX_INTR_W_I32: case AX_INTR_W_U32: return 32;
        default: return 64;
    }
}

bool ax_intrinsic_width_signed(AxIntrinsicWidth w) {
    return w >= AX_INTR_W_I8 && w <= AX_INTR_W_ISIZE;
}

static bool tok_is(const char *tok, size_t len, const char *lit) {
    return strlen(lit) == len && memcmp(tok, lit, len) == 0;
}

static bool type_matches(const char *tok, size_t len, TypeId ty, TypeId width_ty, const TypeInterner *in) {
    if (tok_is(tok, len, "*")) return true;
    if (tok_is(tok, len, "W")) return ty.v == width_ty.v;
    if (tok_is(tok, len, "i32")) return ty.v == in->t_i32.v;
    if (tok_is(tok, len, "u32")) return ty.v == in->t_u32.v;
    if (tok_is(tok, len, "i64")) return ty.v == in->t_i64.v;
    if (tok_is(tok, len, "u64")) return ty.v == in->t_u64.v;
    if (tok_is(tok, len, "u8")) return ty.v == in->t_u8.v;
    if (tok_is(tok, len, "usize")) return ty.v == in->t_usize.v;
    if (tok_is(tok, len, "bool")) return ty.v == in->t_bool.v;
    if (tok_is(tok, len, "unit")) return ty.v == 0 || ty.v == in->t_unit.v;
    if (tok_is(tok, len, "never")) return ty.v == in->t_never.v;
    bool want_mut = false;
    TypeId pointee = in->t_u8;
    if (tok_is(tok, len, "cp8")) { want_mut = false; pointee = in->t_u8; }
    else if (tok_is(tok, len, "mp8")) { want_mut = true; pointee = in->t_u8; }
    else if (tok_is(tok, len, "mp64")) { want_mut = true; pointee = in->t_u64; }
    else return false;
    if (ty.v == 0) return false;
    const AxType *t = ax_type_get(in, ty);
    return t && t->kind == AX_TY_PTR && t->ptr.pointee.v == pointee.v && t->ptr.is_mut == want_mut;
}

/* Matches one alternative `p1,p2>ret` of [alt, alt_end). */
static bool alt_matches(const char *alt, const char *alt_end, const AxType *fn_ty, TypeId width_ty,
                        const TypeInterner *in) {
    const char *gt = alt;
    while (gt < alt_end && *gt != '>') gt++;
    if (gt == alt_end) return false;
    size_t nparams = 0;
    const char *p = alt;
    while (p < gt) {
        const char *q = p;
        while (q < gt && *q != ',') q++;
        if (nparams >= fn_ty->fn.param_count) return false;
        if (!type_matches(p, (size_t)(q - p), fn_ty->fn.param_types[nparams], width_ty, in)) return false;
        nparams++;
        p = (q < gt) ? q + 1 : q;
    }
    if (nparams != fn_ty->fn.param_count) return false;
    return type_matches(gt + 1, (size_t)(alt_end - gt - 1), fn_ty->fn.ret_type, width_ty, in);
}

bool ax_intrinsic_signature_ok(const AxIntrinsicRef *ref, const AxType *fn_ty, size_t generic_count,
                               const TypeInterner *in) {
    if (!fn_ty || fn_ty->kind != AX_TY_FN) return false;
    if (generic_count != ref->desc->generics) return false;
    TypeId width_ty = ref->desc->per_width ? ax_intrinsic_width_type(ref->width, in) : in->t_error;
    const char *s = ref->desc->sig;
    while (*s) {
        const char *e = s;
        while (*e && *e != '|') e++;
        if (alt_matches(s, e, fn_ty, width_ty, in)) return true;
        s = (*e == '|') ? e + 1 : e;
    }
    return false;
}
