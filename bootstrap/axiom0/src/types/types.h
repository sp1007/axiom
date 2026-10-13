#ifndef AX_TYPES_TYPES_H
#define AX_TYPES_TYPES_H

#include "kernel/kernel.h"
#include "hir/hir.h"
#include "diag/diag.h"

AX_DEFINE_ID(TypeId);

#include "types/const/eval.h"

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
    AX_TY_STR,
    AX_TY_SLICE,
    AX_TY_INT_VAR
} AxTypeKind;

#define AX_TY_PTR (AX_TY_INT_VAR + 1)
#define AX_TY_ARRAY (AX_TY_INT_VAR + 2)
#define AX_TY_TUPLE (AX_TY_INT_VAR + 3)
#define AX_TY_STRUCT (AX_TY_INT_VAR + 4)
#define AX_TY_BUILTIN_LEN (AX_TY_INT_VAR + 5)
#define AX_TY_ENUM (AX_TY_INT_VAR + 6)
#define AX_TY_BUILTIN_PRINT (AX_TY_INT_VAR + 7)
#define AX_TY_BUILTIN_PRINT_INT (AX_TY_INT_VAR + 8)
#define AX_TY_BUILTIN_DROP (AX_TY_INT_VAR + 9)
#define AX_TY_VIEW (AX_TY_INT_VAR + 10)
#define AX_TY_MUT_VIEW (AX_TY_INT_VAR + 11)
#define AX_TY_PARAM (AX_TY_INT_VAR + 12)
#define AX_TY_VAR (AX_TY_INT_VAR + 13)
#define AX_TY_CLOSURE (AX_TY_INT_VAR + 14)
#define AX_TY_BUILTIN_ADDRESS_OF (AX_TY_INT_VAR + 15)
#define AX_TY_BUILTIN_ADDRESS_OF_MUT (AX_TY_INT_VAR + 16)
#define AX_TY_BUILTIN_IS_NULL (AX_TY_INT_VAR + 17)
#define AX_TY_BUILTIN_PTR_ADD (AX_TY_INT_VAR + 18)
#define AX_TY_BUILTIN_PTR_SUB (AX_TY_INT_VAR + 19)
#define AX_TY_BUILTIN_SIZE_OF (AX_TY_INT_VAR + 20)
#define AX_TY_BUILTIN_ALIGN_OF (AX_TY_INT_VAR + 21)
#define AX_TY_BUILTIN_NEEDS_DROP (AX_TY_INT_VAR + 22)
#define AX_TY_BUILTIN_DROP_IN_PLACE (AX_TY_INT_VAR + 23)
#define AX_TY_BUILTIN_FORGET (AX_TY_INT_VAR + 24)
#define AX_TY_BUILTIN_PTR_COPY (AX_TY_INT_VAR + 25)
#define AX_TY_BUILTIN_PTR_COPY_NONOVERLAPPING (AX_TY_INT_VAR + 26)
#define AX_TY_BUILTIN_PTR_WRITE_BYTES (AX_TY_INT_VAR + 27)
#define AX_TY_BUILTIN_NULL (AX_TY_INT_VAR + 28)
#define AX_TY_BUILTIN_NULL_MUT (AX_TY_INT_VAR + 29)

typedef enum AxCaptureMode {
    AX_CAP_COPY,
    AX_CAP_VIEW,
    AX_CAP_MUT_VIEW,
    AX_CAP_MOVE
} AxCaptureMode;

typedef struct AxClosureCapture {
    AxSymbolId sym;
    AxCaptureMode mode;
    TypeId type;
} AxClosureCapture;

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
            StrId name;
            uint32_t index;
        } param;
        struct {
            uint32_t var_id;
        } int_var;
        struct {
            TypeId pointee;
            bool is_mut;
        } ptr;
        struct {
            TypeId pointee;
        } view;
        struct {
            TypeId elem;
        } slice;
        struct {
            TypeId elem;
            uint64_t len;
        } array;
        struct {
            TypeId *fields;
            size_t field_count;
        } tuple;
        struct {
            const struct AxHirItem *def;
            TypeId *args;
            size_t arg_count;
            TypeId *fields;
            size_t field_count;
            bool is_repr_c;
        } strct;
        struct {
            const struct AxHirItem *def;
            TypeId *args;
            size_t arg_count;
            TypeId **variant_fields;
            size_t *variant_field_counts;
            size_t variant_count;
            bool is_repr_c;
        } enm;
        struct {
            uint32_t closure_id;
            uint32_t fn_sym;
            TypeId fn_type;
            TypeId ret_type;
            size_t param_count;
            TypeId *params;
            size_t capture_count;
            AxClosureCapture *captures;
        } closure;
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
    } else if (k->kind == AX_TY_INT_VAR || k->kind == AX_TY_VAR) {
        h = ax_hash_combine(h, ax_hash_u32(k->int_var.var_id));
    } else if (k->kind == AX_TY_PARAM) {
        h = ax_hash_combine(h, ax_hash_u32(k->param.index));
    } else if (k->kind == AX_TY_PTR) {
        h = ax_hash_combine(h, ax_hash_u32(k->ptr.pointee.v));
        h = ax_hash_combine(h, ax_hash_u32(k->ptr.is_mut));
    } else if (k->kind == AX_TY_VIEW || k->kind == AX_TY_MUT_VIEW) {
        h = ax_hash_combine(h, ax_hash_u32(k->view.pointee.v));
    } else if (k->kind == AX_TY_SLICE) {
        h = ax_hash_combine(h, ax_hash_u32(k->slice.elem.v));
    } else if (k->kind == AX_TY_ARRAY) {
        h = ax_hash_combine(h, ax_hash_u32(k->array.elem.v));
        h = ax_hash_combine(h, ax_hash_u64(k->array.len));
    } else if (k->kind == AX_TY_TUPLE) {
        h = ax_hash_combine(h, ax_hash_u64((uint64_t)k->tuple.field_count));
        for (size_t i = 0; i < k->tuple.field_count; i++) {
            h = ax_hash_combine(h, ax_hash_u32(k->tuple.fields[i].v));
        }
    } else if (k->kind == AX_TY_STRUCT) {
        h = ax_hash_combine(h, ax_hash_u64((uint64_t)(uintptr_t)k->strct.def));
        for (size_t i = 0; i < k->strct.arg_count; i++) {
            h = ax_hash_combine(h, ax_hash_u32(k->strct.args[i].v));
        }
    } else if (k->kind == AX_TY_ENUM) {
        h = ax_hash_combine(h, ax_hash_u64((uint64_t)(uintptr_t)k->enm.def));
        for (size_t i = 0; i < k->enm.arg_count; i++) {
            h = ax_hash_combine(h, ax_hash_u32(k->enm.args[i].v));
        }
    } else if (k->kind == AX_TY_CLOSURE) {
        h = ax_hash_combine(h, ax_hash_u32(k->closure.closure_id));
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
    } else if (a->kind == AX_TY_INT_VAR || a->kind == AX_TY_VAR) {
        return a->int_var.var_id == b->int_var.var_id;
    } else if (a->kind == AX_TY_PARAM) {
        return a->param.index == b->param.index;
    } else if (a->kind == AX_TY_PTR) {
        return a->ptr.pointee.v == b->ptr.pointee.v && a->ptr.is_mut == b->ptr.is_mut;
    } else if (a->kind == AX_TY_VIEW || a->kind == AX_TY_MUT_VIEW) {
        return a->view.pointee.v == b->view.pointee.v;
    } else if (a->kind == AX_TY_SLICE) {
        return a->slice.elem.v == b->slice.elem.v;
    } else if (a->kind == AX_TY_ARRAY) {
        return a->array.elem.v == b->array.elem.v && a->array.len == b->array.len;
    } else if (a->kind == AX_TY_TUPLE) {
        if (a->tuple.field_count != b->tuple.field_count) return false;
        for (size_t i = 0; i < a->tuple.field_count; i++) {
            if (a->tuple.fields[i].v != b->tuple.fields[i].v) return false;
        }
        return true;
    } else if (a->kind == AX_TY_STRUCT) {
        if (a->strct.def != b->strct.def) return false;
        if (a->strct.arg_count != b->strct.arg_count) return false;
        for (size_t i = 0; i < a->strct.arg_count; i++) {
            if (a->strct.args[i].v != b->strct.args[i].v) return false;
        }
        return true;
    } else if (a->kind == AX_TY_ENUM) {
        if (a->enm.def != b->enm.def) return false;
        if (a->enm.arg_count != b->enm.arg_count) return false;
        for (size_t i = 0; i < a->enm.arg_count; i++) {
            if (a->enm.args[i].v != b->enm.args[i].v) return false;
        }
        return true;
    } else if (a->kind == AX_TY_CLOSURE) {
        return a->closure.closure_id == b->closure.closure_id;
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
    TypeId t_str;
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

uint32_t ax_type_align(TypeId id, const TypeInterner *in);
uint32_t ax_type_size(TypeId id, const TypeInterner *in);
// THIR mappings
#define ax_key_hash_ptr(k) ax_hash_u64((uint64_t)(uintptr_t)*(k))
#define ax_key_eq_ptr(a, b) (*(a) == *(b))

typedef struct AxHirExpr AxHirExpr; typedef const AxHirExpr *AxHirExprPtr;
AX_DEFINE_HASHMAP(AxExprTypeMap, AxHirExprPtr, TypeId, ax_key_hash_ptr, ax_key_eq_ptr);
typedef struct AxHirPat AxHirPat; typedef const AxHirPat *AxHirPatPtr;
AX_DEFINE_HASHMAP(AxPatTypeMap, AxHirPatPtr, TypeId, ax_key_hash_ptr, ax_key_eq_ptr);
AX_DEFINE_HASHMAP(AxExprVariantMap, AxHirExprPtr, uint32_t, ax_key_hash_ptr, ax_key_eq_ptr);
AX_DEFINE_HASHMAP(AxPatVariantMap, AxHirPatPtr, uint32_t, ax_key_hash_ptr, ax_key_eq_ptr);
typedef struct AxHirItem AxHirItem; typedef const AxHirItem *AxHirItemPtr;
AX_DEFINE_HASHMAP(AxExprMethodMap, AxHirExprPtr, AxHirItemPtr, ax_key_hash_ptr, ax_key_eq_ptr);
AX_DEFINE_HASHMAP(AxItemTypeMap, AxHirItemPtr, TypeId, ax_key_hash_ptr, ax_key_eq_ptr);
typedef struct AxHirParam AxHirParam; typedef const AxHirParam *AxHirParamPtr;
AX_DEFINE_HASHMAP(AxParamTypeMap, AxHirParamPtr, TypeId, ax_key_hash_ptr, ax_key_eq_ptr);
static inline uint64_t ax_key_hash_symbol(const AxSymbolId *k) { return ax_key_hash_u32(&k->v); }
static inline bool ax_key_eq_symbol(const AxSymbolId *a, const AxSymbolId *b) { return a->v == b->v; }
AX_DEFINE_HASHMAP(AxSymbolTypeMap, AxSymbolId, TypeId, ax_key_hash_symbol, ax_key_eq_symbol);
AX_DEFINE_HASHMAP(AxSymbolConstMap, AxSymbolId, AxConstValue, ax_key_hash_symbol, ax_key_eq_symbol);

typedef struct AxGenericArgs {
    TypeId *args;
    size_t count;
} AxGenericArgs;

AX_DEFINE_HASHMAP(AxExprSubstMap, AxHirExprPtr, AxGenericArgs, ax_key_hash_ptr, ax_key_eq_ptr);
AX_DEFINE_HASHMAP(AxPatSubstMap, AxHirPatPtr, AxGenericArgs, ax_key_hash_ptr, ax_key_eq_ptr);

typedef struct AxThir {
    TypeInterner interner;
    AxExprTypeMap expr_types;
    AxPatTypeMap pat_types;
    AxExprVariantMap expr_variants;
    AxPatVariantMap pat_variants;
    AxExprMethodMap expr_methods;
    AxItemTypeMap item_types;
    AxParamTypeMap param_types;
    AxSymbolTypeMap symbol_types;
    AxSymbolConstMap symbol_consts;
    AxExprSubstMap expr_substs;
    AxPatSubstMap pat_substs;
} AxThir;

void ax_thir_init(AxThir *thir);
void ax_thir_free(AxThir *thir);

// Exposed for monomorphization
struct TypeckCtx;
TypeId ax_subst_ty(struct TypeckCtx *cx, TypeId ty, const AxGenericArgs *args);

AxThir ax_typeck(const AxHir *hir, AxDiagSink *sink, StrInterner *str_in, const SourceDatabase *db);
AxThir ax_typeck_with_evaluator(const AxHir *hir, AxDiagSink *sink, StrInterner *str_in, const SourceDatabase *db, const AxConstEvaluator *evaluator);
bool ax_type_is_copy(TypeId id, const AxThir *thir, const StrInterner *str_in);

#endif
