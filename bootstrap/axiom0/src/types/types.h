#ifndef AX_TYPES_TYPES_H
#define AX_TYPES_TYPES_H

#include "kernel/kernel.h"
#include "hir/hir.h"
#include "diag/diag.h"

AX_DEFINE_ID(TypeId);

typedef enum AxTypeKind {
    AX_TY_ERROR,
    AX_TY_UNIT,
    AX_TY_NEVER,
    AX_TY_BOOL,
    AX_TY_CHAR,
    AX_TY_I8,
    AX_TY_I16,
    AX_TY_I32,
    AX_TY_I64,
    AX_TY_ISIZE,
    AX_TY_U8,
    AX_TY_U16,
    AX_TY_U32,
    AX_TY_U64,
    AX_TY_USIZE,
    AX_TY_FN,
    AX_TY_INT_VAR
} AxTypeKind;

#define AX_TY_PTR (AX_TY_INT_VAR + 1)
#define AX_TY_ARRAY (AX_TY_INT_VAR + 2)
#define AX_TY_TUPLE (AX_TY_INT_VAR + 3)

typedef struct AxType {
    AxTypeKind kind;
    union {
        struct {
            bool is_unsafe;
            StrId abi;
            TypeId *param_types;
            size_t param_count;
            TypeId ret_type;
        } fn;
        struct {
            uint32_t var_id;
        } int_var;
        struct {
            TypeId pointee;
            bool is_mut;
        } ptr;
        struct {
            TypeId elem;
            uint64_t len;
        } array;
        struct {
            TypeId *fields;
            size_t field_count;
        } tuple;
    };
} AxType;

typedef struct TypeInterner TypeInterner;

AX_MAYBE_UNUSED static inline uint64_t ax_key_hash_type(const AxType *k) {
    uint64_t h = ax_hash_u32(k->kind);
    if (k->kind == AX_TY_FN) {
        h = ax_hash_combine(h, ax_hash_u32(k->fn.is_unsafe));
        h = ax_hash_combine(h, ax_hash_u32(k->fn.abi.v));
        h = ax_hash_combine(h, ax_hash_u32(k->fn.ret_type.v));
        h = ax_hash_combine(h, ax_hash_u64((uint64_t)k->fn.param_count));
        for (size_t i = 0; i < k->fn.param_count; i++) {
            h = ax_hash_combine(h, ax_hash_u32(k->fn.param_types[i].v));
        }
    } else if (k->kind == AX_TY_INT_VAR) {
        h = ax_hash_combine(h, ax_hash_u32(k->int_var.var_id));
    } else if (k->kind == AX_TY_PTR) {
        h = ax_hash_combine(h, ax_hash_u32(k->ptr.pointee.v));
        h = ax_hash_combine(h, ax_hash_u32(k->ptr.is_mut));
    } else if (k->kind == AX_TY_ARRAY) {
        h = ax_hash_combine(h, ax_hash_u32(k->array.elem.v));
        h = ax_hash_combine(h, ax_hash_u64(k->array.len));
    } else if (k->kind == AX_TY_TUPLE) {
        h = ax_hash_combine(h, ax_hash_u64((uint64_t)k->tuple.field_count));
        for (size_t i = 0; i < k->tuple.field_count; i++) {
            h = ax_hash_combine(h, ax_hash_u32(k->tuple.fields[i].v));
        }
    }
    return h;
}

AX_MAYBE_UNUSED static inline bool ax_key_eq_type(const AxType *a, const AxType *b) {
    if (a->kind != b->kind) return false;
    if (a->kind == AX_TY_FN) {
        if (a->fn.is_unsafe != b->fn.is_unsafe) return false;
        if (a->fn.abi.v != b->fn.abi.v) return false;
        if (a->fn.ret_type.v != b->fn.ret_type.v) return false;
        if (a->fn.param_count != b->fn.param_count) return false;
        for (size_t i = 0; i < a->fn.param_count; i++) {
            if (a->fn.param_types[i].v != b->fn.param_types[i].v) return false;
        }
        return true;
    } else if (a->kind == AX_TY_INT_VAR) {
        return a->int_var.var_id == b->int_var.var_id;
    } else if (a->kind == AX_TY_PTR) {
        return a->ptr.pointee.v == b->ptr.pointee.v && a->ptr.is_mut == b->ptr.is_mut;
    } else if (a->kind == AX_TY_ARRAY) {
        return a->array.elem.v == b->array.elem.v && a->array.len == b->array.len;
    } else if (a->kind == AX_TY_TUPLE) {
        if (a->tuple.field_count != b->tuple.field_count) return false;
        for (size_t i = 0; i < a->tuple.field_count; i++) {
            if (a->tuple.fields[i].v != b->tuple.fields[i].v) return false;
        }
        return true;
    }
    return true;
}

AX_DEFINE_HASHMAP(AxTypeMap, AxType, TypeId, ax_key_hash_type, ax_key_eq_type);

struct TypeInterner {
    AxArena arena;
    AxTypeMap map;
    AxType **types;
    size_t len;
    size_t cap;
    uint32_t next_int_var;
    
    TypeId t_error;
    TypeId t_unit;
    TypeId t_never;
    TypeId t_bool;
    TypeId t_char;
    TypeId t_i8, t_i16, t_i32, t_i64, t_isize;
    TypeId t_u8, t_u16, t_u32, t_u64, t_usize;
};

void ax_type_interner_init(TypeInterner *in);
void ax_type_interner_free(TypeInterner *in);
TypeId ax_intern_type(TypeInterner *in, const AxType *type);
const AxType *ax_type_get(const TypeInterner *in, TypeId id);
bool ax_type_is_int(TypeId id, const TypeInterner *in);
bool ax_type_is_signed(TypeId id, const TypeInterner *in);
bool ax_type_is_unsigned(TypeId id, const TypeInterner *in);

static inline uint32_t ax_type_align(TypeId id, const TypeInterner *in) {
    if (id.v == in->t_unit.v || id.v == in->t_never.v) return 1;
    if (id.v == in->t_bool.v || id.v == in->t_i8.v || id.v == in->t_u8.v) return 1;
    if (id.v == in->t_i16.v || id.v == in->t_u16.v) return 2;
    if (id.v == in->t_i32.v || id.v == in->t_u32.v || id.v == in->t_char.v) return 4;
    if (id.v == in->t_i64.v || id.v == in->t_u64.v || id.v == in->t_isize.v || id.v == in->t_usize.v) return 8;

    const AxType *ty = ax_type_get(in, id);
    if (!ty) return 1;
    switch ((int)ty->kind) {
        case AX_TY_PTR:
        case AX_TY_FN:
            return 8;
        case AX_TY_ARRAY:
            return ax_type_align(ty->array.elem, in);
        case AX_TY_TUPLE: {
            uint32_t align = 1;
            for (size_t i = 0; i < ty->tuple.field_count; i++) {
                uint32_t fa = ax_type_align(ty->tuple.fields[i], in);
                if (fa > align) align = fa;
            }
            return align;
        }
        default: return 1;
    }
}

static inline uint32_t ax_type_size(TypeId id, const TypeInterner *in) {
    if (id.v == in->t_unit.v || id.v == in->t_never.v) return 0;
    if (id.v == in->t_bool.v || id.v == in->t_i8.v || id.v == in->t_u8.v) return 1;
    if (id.v == in->t_i16.v || id.v == in->t_u16.v) return 2;
    if (id.v == in->t_i32.v || id.v == in->t_u32.v || id.v == in->t_char.v) return 4;
    if (id.v == in->t_i64.v || id.v == in->t_u64.v || id.v == in->t_isize.v || id.v == in->t_usize.v) return 8;

    const AxType *ty = ax_type_get(in, id);
    if (!ty) return 0;
    switch ((int)ty->kind) {
        case AX_TY_PTR:
        case AX_TY_FN:
            return 8;
        case AX_TY_ARRAY:
            return ax_type_size(ty->array.elem, in) * ty->array.len;
        case AX_TY_TUPLE: {
            uint32_t offset = 0;
            uint32_t max_align = 1;
            for (size_t i = 0; i < ty->tuple.field_count; i++) {
                uint32_t fa = ax_type_align(ty->tuple.fields[i], in);
                uint32_t fs = ax_type_size(ty->tuple.fields[i], in);
                if (fa > max_align) max_align = fa;
                offset = (offset + fa - 1) & ~(fa - 1);
                offset += fs;
            }
            return (offset + max_align - 1) & ~(max_align - 1);
        }
        default: return 0;
    }
}

// THIR mappings
#define ax_key_hash_ptr(k) ax_hash_u64((uint64_t)(uintptr_t)*(k))
#define ax_key_eq_ptr(a, b) (*(a) == *(b))

typedef struct AxHirExpr AxHirExpr; typedef const AxHirExpr *AxHirExprPtr;
AX_DEFINE_HASHMAP(AxExprTypeMap, AxHirExprPtr, TypeId, ax_key_hash_ptr, ax_key_eq_ptr);
typedef struct AxHirPat AxHirPat; typedef const AxHirPat *AxHirPatPtr;
AX_DEFINE_HASHMAP(AxPatTypeMap, AxHirPatPtr, TypeId, ax_key_hash_ptr, ax_key_eq_ptr);
typedef struct AxHirItem AxHirItem; typedef const AxHirItem *AxHirItemPtr;
AX_DEFINE_HASHMAP(AxItemTypeMap, AxHirItemPtr, TypeId, ax_key_hash_ptr, ax_key_eq_ptr);
typedef struct AxHirParam AxHirParam; typedef const AxHirParam *AxHirParamPtr;
AX_DEFINE_HASHMAP(AxParamTypeMap, AxHirParamPtr, TypeId, ax_key_hash_ptr, ax_key_eq_ptr);
static inline uint64_t ax_key_hash_symbol(const AxSymbolId *k) { return ax_key_hash_u32(&k->v); }
static inline bool ax_key_eq_symbol(const AxSymbolId *a, const AxSymbolId *b) { return a->v == b->v; }
AX_DEFINE_HASHMAP(AxSymbolTypeMap, AxSymbolId, TypeId, ax_key_hash_symbol, ax_key_eq_symbol);

typedef struct AxThir {
    TypeInterner interner;
    AxExprTypeMap expr_types;
    AxPatTypeMap pat_types;
    AxItemTypeMap item_types;
    AxParamTypeMap param_types;
    AxSymbolTypeMap symbol_types;
} AxThir;

void ax_thir_init(AxThir *thir);
void ax_thir_free(AxThir *thir);

AxThir ax_typeck(const AxHir *hir, AxDiagSink *sink, StrInterner *str_in, const SourceDatabase *db);

#endif
