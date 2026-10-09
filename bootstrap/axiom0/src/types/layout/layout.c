#include "types/layout/layout.h"
#include <stdlib.h>

typedef struct {
    uint32_t index;
    uint32_t size;
    uint32_t align;
} FieldLayout;

static int compare_fields(const void *a, const void *b) {
    const FieldLayout *fa = (const FieldLayout *)a;
    const FieldLayout *fb = (const FieldLayout *)b;
    if (fa->align != fb->align) {
        return fa->align < fb->align ? 1 : -1; // Descending align
    }
    if (fa->size != fb->size) {
        return fa->size < fb->size ? 1 : -1;   // Descending size
    }
    return fa->index > fb->index ? 1 : (fa->index < fb->index ? -1 : 0); // Ascending index
}

uint32_t ax_type_align(TypeId id, const TypeInterner *in) {
    if (id.v == 0) return 1;
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
        case AX_TY_STRUCT: {
            uint32_t align = 1;
            for (size_t i = 0; i < ty->strct.field_count; i++) {
                uint32_t fa = ax_type_align(ty->strct.fields[i], in);
                if (fa > align) align = fa;
            }
            return align;
        }
        default: return 1;
    }
}

uint32_t ax_type_size(TypeId id, const TypeInterner *in) {
    if (id.v == 0) return 0;
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
            size_t count = ty->tuple.field_count;
            if (count == 0) return 0;
            FieldLayout fl_stack[128];
            FieldLayout *fl = count <= 128 ? fl_stack : malloc(count * sizeof(FieldLayout));
            uint32_t max_align = 1;
            for (size_t i = 0; i < count; i++) {
                fl[i].index = (uint32_t)i;
                fl[i].align = ax_type_align(ty->tuple.fields[i], in);
                fl[i].size = ax_type_size(ty->tuple.fields[i], in);
                if (fl[i].align > max_align) max_align = fl[i].align;
            }
            qsort(fl, count, sizeof(FieldLayout), compare_fields);
            
            uint32_t offset = 0;
            for (size_t i = 0; i < count; i++) {
                offset = (offset + fl[i].align - 1) & ~(fl[i].align - 1);
                offset += fl[i].size;
            }
            if (count > 128) free(fl);
            return (offset + max_align - 1) & ~(max_align - 1);
        }
        case AX_TY_STRUCT: {
            size_t count = ty->strct.field_count;
            if (count == 0) return 0;
            FieldLayout fl_stack[128];
            FieldLayout *fl = count <= 128 ? fl_stack : malloc(count * sizeof(FieldLayout));
            uint32_t max_align = 1;
            for (size_t i = 0; i < count; i++) {
                fl[i].index = (uint32_t)i;
                fl[i].align = ax_type_align(ty->strct.fields[i], in);
                fl[i].size = ax_type_size(ty->strct.fields[i], in);
                if (fl[i].align > max_align) max_align = fl[i].align;
            }
            if (!ty->strct.is_repr_c) {
                qsort(fl, count, sizeof(FieldLayout), compare_fields);
            }
            
            uint32_t offset = 0;
            for (size_t i = 0; i < count; i++) {
                offset = (offset + fl[i].align - 1) & ~(fl[i].align - 1);
                offset += fl[i].size;
            }
            if (count > 128) free(fl);
            return (offset + max_align - 1) & ~(max_align - 1);
        }
        default: return 0;
    }
}

AxLayout ax_type_layout(TypeId type, const TypeInterner* interner) {
    AxLayout l;
    l.size = ax_type_size(type, interner);
    l.align = ax_type_align(type, interner);
    return l;
}

uint32_t ax_type_field_offset(TypeId id, size_t field_idx, const TypeInterner *in) {
    const AxType *ty = ax_type_get(in, id);
    if (!ty) return 0;
    
    if (ty->kind == AX_TY_TUPLE) {
        size_t count = ty->tuple.field_count;
        if (field_idx >= count) return 0;
        FieldLayout fl_stack[128];
        FieldLayout *fl = count <= 128 ? fl_stack : malloc(count * sizeof(FieldLayout));
        for (size_t i = 0; i < count; i++) {
            fl[i].index = (uint32_t)i;
            fl[i].align = ax_type_align(ty->tuple.fields[i], in);
            fl[i].size = ax_type_size(ty->tuple.fields[i], in);
        }
        qsort(fl, count, sizeof(FieldLayout), compare_fields);
        
        uint32_t offset = 0;
        uint32_t target_offset = 0;
        for (size_t i = 0; i < count; i++) {
            offset = (offset + fl[i].align - 1) & ~(fl[i].align - 1);
            if (fl[i].index == field_idx) {
                target_offset = offset;
                break;
            }
            offset += fl[i].size;
        }
        if (count > 128) free(fl);
        return target_offset;
    } else if (ty->kind == AX_TY_STRUCT) {
        size_t count = ty->strct.field_count;
        if (field_idx >= count) return 0;
        FieldLayout fl_stack[128];
        FieldLayout *fl = count <= 128 ? fl_stack : malloc(count * sizeof(FieldLayout));
        for (size_t i = 0; i < count; i++) {
            fl[i].index = (uint32_t)i;
            fl[i].align = ax_type_align(ty->strct.fields[i], in);
            fl[i].size = ax_type_size(ty->strct.fields[i], in);
        }
        if (!ty->strct.is_repr_c) {
            qsort(fl, count, sizeof(FieldLayout), compare_fields);
        }
        
        uint32_t offset = 0;
        uint32_t target_offset = 0;
        for (size_t i = 0; i < count; i++) {
            offset = (offset + fl[i].align - 1) & ~(fl[i].align - 1);
            if (fl[i].index == field_idx) {
                target_offset = offset;
                break;
            }
            offset += fl[i].size;
        }
        if (count > 128) free(fl);
        return target_offset;
    }
    return 0;
}
