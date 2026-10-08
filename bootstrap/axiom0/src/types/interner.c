#include "types/types.h"
#include <stdlib.h>

void ax_type_interner_init(TypeInterner *in) {
    ax_arena_init(&in->arena, 0);
    AxTypeMap_init(&in->map);
    in->types = NULL;
    in->len = 0;
    in->cap = 0;
    in->next_int_var = 1;
    
    // Register built-ins
    AxType t;
    t.kind = AX_TY_ERROR; in->t_error = ax_intern_type(in, &t);
    t.kind = AX_TY_UNIT; in->t_unit = ax_intern_type(in, &t);
    t.kind = AX_TY_NEVER; in->t_never = ax_intern_type(in, &t);
    t.kind = AX_TY_BOOL; in->t_bool = ax_intern_type(in, &t);
    t.kind = AX_TY_CHAR; in->t_char = ax_intern_type(in, &t);
    t.kind = AX_TY_I8; in->t_i8 = ax_intern_type(in, &t);
    t.kind = AX_TY_I16; in->t_i16 = ax_intern_type(in, &t);
    t.kind = AX_TY_I32; in->t_i32 = ax_intern_type(in, &t);
    t.kind = AX_TY_I64; in->t_i64 = ax_intern_type(in, &t);
    t.kind = AX_TY_ISIZE; in->t_isize = ax_intern_type(in, &t);
    t.kind = AX_TY_U8; in->t_u8 = ax_intern_type(in, &t);
    t.kind = AX_TY_U16; in->t_u16 = ax_intern_type(in, &t);
    t.kind = AX_TY_U32; in->t_u32 = ax_intern_type(in, &t);
    t.kind = AX_TY_U64; in->t_u64 = ax_intern_type(in, &t);
    t.kind = AX_TY_USIZE; in->t_usize = ax_intern_type(in, &t);
}

void ax_type_interner_free(TypeInterner *in) {
    ax_xfree(in->types);
    AxTypeMap_free(&in->map);
    ax_arena_destroy(&in->arena);
}

TypeId ax_intern_type(TypeInterner *in, const AxType *type) {
    TypeId *existing = AxTypeMap_get(&in->map, *type);
    if (existing) {
        return *existing;
    }
    
    AxType *new_type = ax_arena_alloc(&in->arena, sizeof(AxType), _Alignof(AxType));
    *new_type = *type;
    
    // Deep copy fn types
    if (type->kind == AX_TY_FN && type->fn.param_count > 0) {
        new_type->fn.param_types = ax_arena_alloc(&in->arena, sizeof(TypeId) * type->fn.param_count, _Alignof(TypeId));
        for (size_t i = 0; i < type->fn.param_count; i++) {
            new_type->fn.param_types[i] = type->fn.param_types[i];
        }
    }
    if (type->kind == AX_TY_TUPLE && type->tuple.field_count > 0) {
        new_type->tuple.fields = ax_arena_alloc(&in->arena, sizeof(TypeId) * type->tuple.field_count, _Alignof(TypeId));
        for (size_t i = 0; i < type->tuple.field_count; i++) new_type->tuple.fields[i] = type->tuple.fields[i];
    }
    if (type->kind == AX_TY_STRUCT && type->strct.field_count > 0) {
        new_type->strct.fields = ax_arena_alloc(&in->arena, sizeof(TypeId) * type->strct.field_count, _Alignof(TypeId));
        for (size_t i = 0; i < type->strct.field_count; i++) new_type->strct.fields[i] = type->strct.fields[i];
    }
    
    if (in->len == in->cap) {
        in->types = (AxType **)ax_grow_array(in->types, &in->cap, sizeof(AxType *), in->len + 1);
    }
    
    in->types[in->len] = new_type;
    TypeId id = TypeId_from_index(in->len);
    in->len++;
    
    AxTypeMap_insert(&in->map, *new_type, id);
    return id;
}

const AxType *ax_type_get(const TypeInterner *in, TypeId id) {
    if (TypeId_is_none(id) || TypeId_index(id) >= in->len) {
        AX_ICE("TypeInterner: invalid id %u", (unsigned)id.v);
    }
    return in->types[TypeId_index(id)];
}

bool ax_type_is_int(TypeId id, const TypeInterner *in) {
    const AxType *t = ax_type_get(in, id);
    return t->kind >= AX_TY_I8 && t->kind <= AX_TY_USIZE;
}

bool ax_type_is_signed(TypeId id, const TypeInterner *in) {
    const AxType *t = ax_type_get(in, id);
    return t->kind >= AX_TY_I8 && t->kind <= AX_TY_ISIZE;
}

bool ax_type_is_unsigned(TypeId id, const TypeInterner *in) {
    const AxType *t = ax_type_get(in, id);
    return t->kind >= AX_TY_U8 && t->kind <= AX_TY_USIZE;
}

void ax_thir_init(AxThir *thir) {
    ax_type_interner_init(&thir->interner);
    AxExprTypeMap_init(&thir->expr_types);
    AxPatTypeMap_init(&thir->pat_types);
    AxItemTypeMap_init(&thir->item_types);
    AxParamTypeMap_init(&thir->param_types);
    AxSymbolTypeMap_init(&thir->symbol_types);
}

void ax_thir_free(AxThir *thir) {
    AxSymbolTypeMap_free(&thir->symbol_types);
    AxParamTypeMap_free(&thir->param_types);
    AxItemTypeMap_free(&thir->item_types);
    AxPatTypeMap_free(&thir->pat_types);
    AxExprTypeMap_free(&thir->expr_types);
    ax_type_interner_free(&thir->interner);
}
