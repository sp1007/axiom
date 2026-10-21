#include "lir/lir.h"
#include "mir/build/intrinsics.h"
#include <stdlib.h>
#include <stdio.h>
#include <string.h>
#include "types/layout/layout.h"
#include "kernel/interner.h"
#include "kernel/str.h"

typedef struct LirBuilder {
    AxArena *arena;
    TypeInterner *interner;
    const AxMirBody *mir;
    const struct AxHir *hir;
    struct StrInterner *str_in;
    
    AxLirStackSlot *slots;
    size_t slot_count;
    size_t slot_cap;
    
    AxLirVReg *vregs;
    size_t vreg_count;
    size_t vreg_cap;
    
    AxLirBb *bbs;
    size_t bb_count;
    size_t bb_cap;
    
    AxLirInst *cur_insts;
    size_t cur_inst_count;
    size_t cur_inst_cap;
} LirBuilder;

/* Host intrinsics are the AX_INTR_HOST rows of the intrinsic table (T134). */
static bool is_host_intrinsic_name(StrView name) {
    return ax_intrinsic_is_host(name);
}

static const char *get_fn_sym_name(const struct AxHir *hir, struct StrInterner *str_in, uint32_t sym_v) {
    if (sym_v != 0 && hir && str_in) {
        for (const struct AxHirItem *it = hir->items; it; it = it->next) {
            if (it->kind == AX_HIR_ITEM_FN && it->fn.symbol.v == sym_v) {
                if (it->fn.name.v != 0) {
                    StrView sv = ax_interner_get(str_in, it->fn.name);
                    for (const struct AxHirAttr *attr = it->attrs; attr; attr = attr->next) {
                        StrView an = ax_interner_get(str_in, attr->name);
                        if (ax_sv_eq_cstr(an, "intrinsic") && is_host_intrinsic_name(sv)) {
                            char *iname = malloc(sv.len + 16);
                            snprintf(iname, sv.len + 16, "__ax_host_%.*s", (int)sv.len, sv.ptr);
                            return iname;
                        }
                    }
                    if (it->fn.abi.v != 0) {
                        for (const struct AxHirAttr *attr = it->attrs; attr; attr = attr->next) {
                            StrView an = ax_interner_get(str_in, attr->name);
                            if (ax_sv_eq_cstr(an, "link") && attr->args && attr->args->expr && attr->args->expr->kind == AX_HIR_EXPR_LITERAL) {
                                StrView link_val = {
                                    .ptr = (const char*)attr->args->expr->literal.val.str_val.bytes,
                                    .len = attr->args->expr->literal.val.str_val.len
                                };
                                if (link_val.len > 0) {
                                    char *ename = malloc(link_val.len + 1 + sv.len + 1);
                                    snprintf(ename, link_val.len + 1 + sv.len + 1, "%.*s$%.*s", (int)link_val.len, link_val.ptr, (int)sv.len, sv.ptr);
                                    return ename;
                                }
                            }
                        }
                        char *ename = malloc(13 + sv.len + 1);
                        snprintf(ename, 13 + sv.len + 1, "KERNEL32.dll$%.*s", (int)sv.len, sv.ptr);
                        return ename;
                    }
                    char *name = malloc(sv.len + 1);
                    memcpy(name, sv.ptr, sv.len);
                    name[sv.len] = '\0';
                    return name;
                }
                break;
            }
            if (it->kind == AX_HIR_ITEM_IMPL) {
                for (const struct AxHirItem *m = it->impl.members; m; m = m->next) {
                    if (m->kind == AX_HIR_ITEM_FN && m->fn.symbol.v == sym_v) {
                        if (m->fn.name.v != 0) {
                            StrView sv = ax_interner_get(str_in, m->fn.name);
                            for (const struct AxHirAttr *attr = m->attrs; attr; attr = attr->next) {
                                StrView an = ax_interner_get(str_in, attr->name);
                                if (ax_sv_eq_cstr(an, "intrinsic") && is_host_intrinsic_name(sv)) {
                                    char *iname = malloc(sv.len + 16);
                                    snprintf(iname, sv.len + 16, "__ax_host_%.*s", (int)sv.len, sv.ptr);
                                    return iname;
                                }
                            }
                            char *name = malloc(sv.len + 1);
                            memcpy(name, sv.ptr, sv.len);
                            name[sv.len] = '\0';
                            return name;
                        }
                        break;
                    }
                }
            }
            if (it->kind == AX_HIR_ITEM_TRAIT) {
                for (const struct AxHirItem *m = it->trait.members; m; m = m->next) {
                    if (m->kind == AX_HIR_ITEM_FN && m->fn.symbol.v == sym_v) {
                        if (m->fn.name.v != 0) {
                            StrView sv = ax_interner_get(str_in, m->fn.name);
                            for (const struct AxHirAttr *attr = m->attrs; attr; attr = attr->next) {
                                StrView an = ax_interner_get(str_in, attr->name);
                                if (ax_sv_eq_cstr(an, "intrinsic") && is_host_intrinsic_name(sv)) {
                                    char *iname = malloc(sv.len + 16);
                                    snprintf(iname, sv.len + 16, "__ax_host_%.*s", (int)sv.len, sv.ptr);
                                    return iname;
                                }
                            }
                            char *name = malloc(sv.len + 1);
                            memcpy(name, sv.ptr, sv.len);
                            name[sv.len] = '\0';
                            return name;
                        }
                        break;
                    }
                }
            }
        }
    }
    char *name = malloc(64);
    snprintf(name, 64, "__ax_fn_%u", sym_v);
    return name;
}

static const char *get_const_table_sym_name(const struct AxHir *hir, struct StrInterner *str_in, uint32_t sym_v) {
    if (sym_v != 0 && hir && str_in) {
        for (const struct AxHirItem *it = hir->items; it; it = it->next) {
            if (it->kind == AX_HIR_ITEM_CONST && it->const_decl.symbol.v == sym_v) {
                if (it->const_decl.name.v != 0) {
                    StrView sv = ax_interner_get(str_in, it->const_decl.name);
                    char *name = malloc(sv.len + 32);
                    snprintf(name, sv.len + 32, ".Lconst_%u_%.*s", sym_v, (int)sv.len, sv.ptr);
                    return name;
                }
                break;
            }
            if (it->kind == AX_HIR_ITEM_IMPL) {
                for (const struct AxHirItem *m = it->impl.members; m; m = m->next) {
                    if (m->kind == AX_HIR_ITEM_CONST && m->const_decl.symbol.v == sym_v) {
                        if (m->const_decl.name.v != 0) {
                            StrView sv = ax_interner_get(str_in, m->const_decl.name);
                            char *name = malloc(sv.len + 32);
                            snprintf(name, sv.len + 32, ".Lconst_%u_%.*s", sym_v, (int)sv.len, sv.ptr);
                            return name;
                        }
                        break;
                    }
                }
            }
            if (it->kind == AX_HIR_ITEM_TRAIT) {
                for (const struct AxHirItem *m = it->trait.members; m; m = m->next) {
                    if (m->kind == AX_HIR_ITEM_CONST && m->const_decl.symbol.v == sym_v) {
                        if (m->const_decl.name.v != 0) {
                            StrView sv = ax_interner_get(str_in, m->const_decl.name);
                            char *name = malloc(sv.len + 32);
                            snprintf(name, sv.len + 32, ".Lconst_%u_%.*s", sym_v, (int)sv.len, sv.ptr);
                            return name;
                        }
                        break;
                    }
                }
            }
        }
    }
    char *name = malloc(32);
    snprintf(name, 32, ".Lconst_%u", sym_v);
    return name;
}

static size_t add_lir_bb(LirBuilder *b) {
    if (b->bb_count == b->bb_cap) {
        b->bb_cap = b->bb_cap == 0 ? 16 : b->bb_cap * 2;
        b->bbs = realloc(b->bbs, b->bb_cap * sizeof(AxLirBb));
    }
    size_t new_idx = b->bb_count++;
    memset(&b->bbs[new_idx], 0, sizeof(AxLirBb));
    return new_idx;
}

static void finish_bb(LirBuilder *b, size_t bb_idx, AxLirTerminator term) {
    b->bbs[bb_idx].inst_count = b->cur_inst_count;
    if (b->cur_inst_count > 0) {
        b->bbs[bb_idx].insts = ax_arena_alloc(b->arena, b->cur_inst_count * sizeof(AxLirInst), _Alignof(AxLirInst));
        memcpy(b->bbs[bb_idx].insts, b->cur_insts, b->cur_inst_count * sizeof(AxLirInst));
    } else {
        b->bbs[bb_idx].insts = NULL;
    }
    b->bbs[bb_idx].terminator = term;
    b->cur_inst_count = 0;
}

static bool lir_type_needs_drop(const LirBuilder *b, TypeId ty_id) {
    if (TypeId_is_none(ty_id) || ty_id.v == 0) return false;
    const AxType *t = ax_type_get(b->interner, ty_id);
    if (!t) return false;

    if (t->kind == AX_TY_STRUCT) {
        if (t->strct.def && t->strct.def->struct_decl.struct_fields == NULL) return true;
        if (b->hir && t->strct.def && t->strct.def->struct_decl.name.v != 0 && b->str_in) {
            StrView target_sname = ax_interner_get(b->str_in, t->strct.def->struct_decl.name);
            for (const struct AxHirItem *it = b->hir->items; it; it = it->next) {
                if (it->kind == AX_HIR_ITEM_IMPL && it->impl.trait_path && it->impl.self_type && it->impl.self_type->kind == AX_HIR_TYPE_PATH) {
                    StrView trait_sname = {0};
                    if (it->impl.trait_path->path.path.name.v != 0) {
                        trait_sname = ax_interner_get(b->str_in, it->impl.trait_path->path.path.name);
                    }
                    if (trait_sname.len == 4 && memcmp(trait_sname.ptr, "Drop", 4) == 0) {
                        StrView impl_sname = {0};
                        if (it->impl.self_type->path.path.name.v != 0) {
                            impl_sname = ax_interner_get(b->str_in, it->impl.self_type->path.path.name);
                        }
                        if (ax_sv_eq(target_sname, impl_sname)) {
                            for (const struct AxHirItem *m = it->impl.members; m; m = m->next) {
                                if (m->kind == AX_HIR_ITEM_FN) {
                                    return true;
                                }
                            }
                        }
                    }
                }
            }
        }
        for (size_t i = 0; i < t->strct.field_count; i++) {
            if (lir_type_needs_drop(b, t->strct.fields[i])) return true;
        }
        return false;
    }
    if (t->kind == AX_TY_TUPLE) {
        for (size_t i = 0; i < t->tuple.field_count; i++) {
            if (lir_type_needs_drop(b, t->tuple.fields[i])) return true;
        }
        return false;
    }
    if (t->kind == AX_TY_ARRAY) {
        return lir_type_needs_drop(b, t->array.elem);
    }
    return false;
}

static const char *find_drop_fn_sym_name(const struct AxHir *hir, struct StrInterner *str_in, TypeId ty_id, const TypeInterner *interner) {
    if (TypeId_is_none(ty_id) || ty_id.v == 0) return NULL;
    const AxType *ty = ax_type_get(interner, ty_id);
    if (!ty || ty->kind != AX_TY_STRUCT) return NULL;
    StrView target_sname = ax_interner_get(str_in, ty->strct.def->struct_decl.name);
    for (const struct AxHirItem *it = hir ? hir->items : NULL; it; it = it->next) {
        if (it->kind == AX_HIR_ITEM_IMPL && it->impl.trait_path && it->impl.self_type && it->impl.self_type->kind == AX_HIR_TYPE_PATH) {
            StrView trait_sname = {0};
            if (it->impl.trait_path->path.path.name.v != 0) {
                trait_sname = ax_interner_get(str_in, it->impl.trait_path->path.path.name);
            }
            if (trait_sname.len == 4 && memcmp(trait_sname.ptr, "Drop", 4) == 0) {
                StrView impl_sname = {0};
                if (it->impl.self_type->path.path.name.v != 0) {
                    impl_sname = ax_interner_get(str_in, it->impl.self_type->path.path.name);
                }
                if (ax_sv_eq(target_sname, impl_sname)) {
                    for (const struct AxHirItem *m = it->impl.members; m; m = m->next) {
                        if (m->kind == AX_HIR_ITEM_FN) {
                            if (m->fn.name.v != 0) {
                                StrView sv = ax_interner_get(str_in, m->fn.name);
                                char *name = malloc(sv.len + 1);
                                memcpy(name, sv.ptr, sv.len);
                                name[sv.len] = '\0';
                                return name;
                            }
                            return get_fn_sym_name(hir, str_in, m->fn.symbol.v);
                        }
                    }
                }
            }
        }
    }
    return NULL;
}


static AxLirVRegId make_vreg(LirBuilder *b, TypeId ty) {
    if (b->vreg_count == b->vreg_cap) {
        b->vreg_cap = b->vreg_cap == 0 ? 16 : b->vreg_cap * 2;
        b->vregs = realloc(b->vregs, b->vreg_cap * sizeof(AxLirVReg));
    }
    AxLirVRegId id = { (uint32_t)b->vreg_count };
    b->vregs[id.v].ty = ty;
    b->vreg_count++;
    return id;
}

static void emit_inst(LirBuilder *b, AxLirInst inst) {
    if (b->cur_inst_count == b->cur_inst_cap) {
        b->cur_inst_cap = b->cur_inst_cap == 0 ? 16 : b->cur_inst_cap * 2;
        b->cur_insts = realloc(b->cur_insts, b->cur_inst_cap * sizeof(AxLirInst));
    }
    b->cur_insts[b->cur_inst_count++] = inst;
}

static AxLirVRegId emit_stack_addr(LirBuilder *b, AxLirStackSlotId slot) {
    AxLirVRegId dest = make_vreg(b, b->interner->t_usize); // Assuming pointers are usize
    AxLirInst inst = { .kind = AX_LIR_INST_STACK_ADDR, .dest = dest, .stack_addr = { .slot = slot } };
    emit_inst(b, inst);
    return dest;
}

static AxLirVRegId emit_const(LirBuilder *b, uint64_t val, TypeId ty) {
    AxLirVRegId dest = make_vreg(b, ty);
    AxLirInst inst = { .kind = AX_LIR_INST_CONST, .dest = dest, .constant = { .val = val, .ty = ty } };
    emit_inst(b, inst);
    return dest;
}

static AxLirVRegId emit_load(LirBuilder *b, AxLirVRegId ptr, TypeId ty) {
    AxLirVRegId dest = make_vreg(b, ty);
    AxLirInst inst = { .kind = AX_LIR_INST_LOAD, .dest = dest, .load = { .ptr = ptr, .ty = ty } };
    emit_inst(b, inst);
    return dest;
}

static void emit_store(LirBuilder *b, AxLirVRegId ptr, AxLirVRegId val) {
    AxLirInst inst = { .kind = AX_LIR_INST_STORE, .dest = {0}, .store = { .ptr = ptr, .val = val } };
    emit_inst(b, inst);
}

static AxLirVRegId emit_offset(LirBuilder *b, AxLirVRegId ptr, AxLirVRegId off) {
    AxLirVRegId dest = make_vreg(b, b->interner->t_usize);
    AxLirInst inst = { .kind = AX_LIR_INST_ADD, .dest = dest, .binary = { .lhs = ptr, .rhs = off } };
    emit_inst(b, inst);
    return dest;
}

static TypeId get_place_type(const LirBuilder *b, const AxMirPlace *place) {
    TypeId ty = b->mir->locals[place->local.v].ty;
    uint32_t current_variant = (uint32_t)-1;
    for (size_t i = 0; i < place->proj_count; i++) {
        switch (place->projs[i].kind) {
            case AX_MIR_PROJ_DEREF: {
                const AxType *t = ax_type_get(b->interner, ty);
                if (t && t->kind == AX_TY_PTR) ty = t->ptr.pointee;
                else if (t && (t->kind == AX_TY_VIEW || t->kind == AX_TY_MUT_VIEW)) ty = t->view.pointee;
                else if (t && t->kind == AX_TY_STR) ty = b->interner->t_u8;
                break;
            }
            case AX_MIR_PROJ_FIELD: {
                const AxType *t = ax_type_get(b->interner, ty);
                uint32_t idx = place->projs[i].field_idx;
                if (t && t->kind == AX_TY_ENUM && current_variant != (uint32_t)-1) {
                    if (idx < t->enm.variant_field_counts[current_variant]) ty = t->enm.variant_fields[current_variant][idx];
                    current_variant = (uint32_t)-1;
                } else if (t && (t->kind == AX_TY_STRUCT || t->kind == AX_TY_TUPLE)) {
                    if (t->kind == AX_TY_STRUCT && idx < t->strct.field_count) ty = t->strct.fields[idx];
                    else if (t->kind == AX_TY_TUPLE && idx < t->tuple.field_count) ty = t->tuple.fields[idx];
                }
                break;
            }
            case AX_MIR_PROJ_INDEX: {
                const AxType *t = ax_type_get(b->interner, ty);
                if (t && t->kind == AX_TY_ARRAY) ty = t->array.elem;
                else if (t && t->kind == AX_TY_SLICE) ty = t->slice.elem;
                else if (t && t->kind == AX_TY_STR) ty = b->interner->t_u8;
                break;
            }
            case AX_MIR_PROJ_SUB_SLICE: {
                const AxType *t = ax_type_get(b->interner, ty);
                TypeId elem_ty = {0};
                if (t && t->kind == AX_TY_ARRAY) elem_ty = t->array.elem;
                else if (t && t->kind == AX_TY_SLICE) elem_ty = t->slice.elem;
                else if (t && t->kind == AX_TY_STR) elem_ty = b->interner->t_u8;
                AxType sl; memset(&sl, 0, sizeof(sl));
                sl.kind = AX_TY_SLICE;
                sl.slice.elem = elem_ty;
                ty = ax_intern_type(b->interner, &sl);
                break;
            }
            case AX_MIR_PROJ_DOWNCAST: {
                current_variant = place->projs[i].variant_idx;
                break;
            }
        }
    }
    return ty;
}

static AxLirVRegId lower_place_addr(LirBuilder *b, const AxMirPlace *place, TypeId *out_ty) {
    AxLirVRegId addr;
    if (b->mir->locals[place->local.v].kind == AX_MIR_LOCAL_CONST) {
        uint32_t sym_v = b->mir->locals[place->local.v].const_sym.v;
        const char *sym_name = get_const_table_sym_name(b->hir, b->str_in, sym_v);
        addr = make_vreg(b, b->interner->t_usize);
        emit_inst(b, (AxLirInst){ .kind = AX_LIR_INST_FN_ADDR, .dest = addr, .fn_addr = { .sym_name = sym_name } });
    } else {
        AxLirStackSlotId slot = { place->local.v };
        addr = emit_stack_addr(b, slot);
    }
    TypeId ty = b->mir->locals[place->local.v].ty;
    uint32_t current_variant = (uint32_t)-1;
    
    // Projections
    for (size_t i = 0; i < place->proj_count; i++) {
        switch (place->projs[i].kind) {
            case AX_MIR_PROJ_DEREF: {
                addr = emit_load(b, addr, b->interner->t_usize);
                const AxType *t = ax_type_get(b->interner, ty);
                if (t && t->kind == AX_TY_PTR) {
                    ty = t->ptr.pointee;
                } else if (t && (t->kind == AX_TY_VIEW || t->kind == AX_TY_MUT_VIEW)) {
                    ty = t->view.pointee;
                } else if (t && t->kind == AX_TY_STR) {
                    ty = b->interner->t_u8;
                }
                break;
            }
            case AX_MIR_PROJ_FIELD: {
                const AxType *t = ax_type_get(b->interner, ty);
                uint32_t idx = place->projs[i].field_idx;
                uint32_t offset = 0;
                TypeId next_ty = {0};
                if (t && t->kind == AX_TY_ENUM && current_variant != (uint32_t)-1) {
                    offset = ax_type_enum_field_offset(ty, current_variant, idx, b->interner);
                    if (idx < t->enm.variant_field_counts[current_variant]) next_ty = t->enm.variant_fields[current_variant][idx];
                    current_variant = (uint32_t)-1;
                } else if (t && (t->kind == AX_TY_STRUCT || t->kind == AX_TY_TUPLE)) {
                    offset = ax_type_field_offset(ty, idx, b->interner);
                    if (t->kind == AX_TY_STRUCT && idx < t->strct.field_count) next_ty = t->strct.fields[idx];
                    else if (t->kind == AX_TY_TUPLE && idx < t->tuple.field_count) next_ty = t->tuple.fields[idx];
                }
                
                ty = next_ty;
                if (offset != 0) {
                    AxLirVRegId dummy_off = emit_const(b, offset, b->interner->t_usize);
                    addr = emit_offset(b, addr, dummy_off);
                }
                break;
            }
            case AX_MIR_PROJ_SUB_SLICE: {
                const AxType *t = ax_type_get(b->interner, ty);
                TypeId elem_ty = {0};
                if (t && t->kind == AX_TY_ARRAY) elem_ty = t->array.elem;
                else if (t && t->kind == AX_TY_SLICE) elem_ty = t->slice.elem;
                else if (t && t->kind == AX_TY_STR) elem_ty = b->interner->t_u8;
                if (place->projs[i].sub_slice.has_from) {
                    AxLirStackSlotId idx_slot = { place->projs[i].sub_slice.from_local.v };
                    AxLirVRegId idx_addr = emit_stack_addr(b, idx_slot);
                    AxLirVRegId idx_val = emit_load(b, idx_addr, b->interner->t_usize);
                    uint32_t fs = ax_type_size(elem_ty, b->interner);
                    if (fs == 1) {
                        addr = emit_offset(b, addr, idx_val);
                    } else {
                        AxLirVRegId dummy_size = emit_const(b, fs, b->interner->t_usize);
                        AxLirVRegId offset = make_vreg(b, b->interner->t_usize);
                        emit_inst(b, (AxLirInst){ .kind = AX_LIR_INST_MUL, .dest = offset, .binary = { .lhs = idx_val, .rhs = dummy_size } });
                        addr = emit_offset(b, addr, offset);
                    }
                }
                if (t && t->kind == AX_TY_ARRAY) {
                    AxType sl; memset(&sl, 0, sizeof(sl));
                    sl.kind = AX_TY_SLICE;
                    sl.slice.elem = elem_ty;
                    ty = ax_intern_type(b->interner, &sl);
                }
                break;
            }
            case AX_MIR_PROJ_INDEX: {
                const AxType *t = ax_type_get(b->interner, ty);
                TypeId elem_ty = {0};
                if (t && t->kind == AX_TY_ARRAY) elem_ty = t->array.elem;
                else if (t && t->kind == AX_TY_SLICE) elem_ty = t->slice.elem;
                else if (t && t->kind == AX_TY_STR) elem_ty = b->interner->t_u8;
                AxLirStackSlotId idx_slot = { place->projs[i].index_local.v };
                AxLirVRegId idx_addr = emit_stack_addr(b, idx_slot);
                AxLirVRegId idx_val = emit_load(b, idx_addr, b->interner->t_usize);
                uint32_t fs = ax_type_size(elem_ty, b->interner);
                if (fs == 1) {
                    addr = emit_offset(b, addr, idx_val);
                } else {
                    AxLirVRegId dummy_size = emit_const(b, fs, b->interner->t_usize);
                    AxLirVRegId off = make_vreg(b, b->interner->t_usize);
                    emit_inst(b, (AxLirInst){ .kind = AX_LIR_INST_MUL, .dest = off, .binary = { .lhs = idx_val, .rhs = dummy_size } });
                    addr = emit_offset(b, addr, off);
                }
                ty = elem_ty;
                break;
            }
            case AX_MIR_PROJ_DOWNCAST: {
                current_variant = place->projs[i].variant_idx;
                break;
            }
        }
    }
    
    if (out_ty) *out_ty = ty;
    return addr;
}

static AxLirVRegId emit_const_str(LirBuilder *b, const uint8_t *bytes, size_t len, TypeId ty) {
    AxLirVRegId dest = make_vreg(b, ty);
    AxLirInst inst = { .kind = AX_LIR_INST_CONST_STR, .dest = dest, .const_str = { .bytes = bytes, .len = len } };
    emit_inst(b, inst);
    return dest;
}

static AxLirVRegId lower_operand(LirBuilder *b, const AxMirOperand *op) {
    switch (op->kind) {
        case AX_MIR_OP_COPY:
        case AX_MIR_OP_MOVE: {
            TypeId place_ty;
            AxLirVRegId addr = lower_place_addr(b, &op->place, &place_ty);
            return emit_load(b, addr, place_ty);
        }
        case AX_MIR_OP_CONST: {
            if (op->constant.kind == AX_MIR_CONST_STR) {
                return emit_const_str(b, op->constant.str.bytes, op->constant.str.len, op->constant.ty);
            }
            const AxType *ct = op->constant.ty.v ? ax_type_get(b->interner, op->constant.ty) : NULL;
            if (ct && (ct->kind == AX_TY_FN || ct->kind == AX_TY_CLOSURE)) {
                uint32_t sym_v = (uint32_t)op->constant.val;
                const char *fn_name = get_fn_sym_name(b->hir, b->str_in, sym_v);
                AxLirVRegId dest = make_vreg(b, op->constant.ty);
                AxLirInst inst = { .kind = AX_LIR_INST_FN_ADDR, .dest = dest, .fn_addr = { .sym_name = fn_name } };
                emit_inst(b, inst);
                return dest;
            }
            return emit_const(b, op->constant.val, op->constant.ty);
        }
    }
    return (AxLirVRegId){0};
}

static AxLirInstKind lower_binop(AxMirBinOp op, bool is_signed) {
    switch (op) {
        case AX_MIR_BINOP_ADD: return AX_LIR_INST_ADD;
        case AX_MIR_BINOP_SUB: return AX_LIR_INST_SUB;
        case AX_MIR_BINOP_MUL: return AX_LIR_INST_MUL;
        case AX_MIR_BINOP_DIV: return is_signed ? AX_LIR_INST_DIV : AX_LIR_INST_UDIV;
        case AX_MIR_BINOP_REM: return is_signed ? AX_LIR_INST_REM : AX_LIR_INST_UREM;
        case AX_MIR_BINOP_BIT_XOR: return AX_LIR_INST_BIT_XOR;
        case AX_MIR_BINOP_BIT_AND: return AX_LIR_INST_BIT_AND;
        case AX_MIR_BINOP_BIT_OR: return AX_LIR_INST_BIT_OR;
        case AX_MIR_BINOP_SHL: return AX_LIR_INST_SHL;
        case AX_MIR_BINOP_SHR: return is_signed ? AX_LIR_INST_SAR : AX_LIR_INST_SHR;
        case AX_MIR_BINOP_EQ: return AX_LIR_INST_ICMP_EQ;
        case AX_MIR_BINOP_NE: return AX_LIR_INST_ICMP_NE;
        case AX_MIR_BINOP_LT: return is_signed ? AX_LIR_INST_ICMP_SLT : AX_LIR_INST_ICMP_ULT;
        case AX_MIR_BINOP_LE: return is_signed ? AX_LIR_INST_ICMP_SLE : AX_LIR_INST_ICMP_ULE;
        case AX_MIR_BINOP_GT: return is_signed ? AX_LIR_INST_ICMP_SGT : AX_LIR_INST_ICMP_UGT;
        case AX_MIR_BINOP_GE: return is_signed ? AX_LIR_INST_ICMP_SGE : AX_LIR_INST_ICMP_UGE;
        case AX_MIR_BINOP_OFFSET: return AX_LIR_INST_ADD;
        /* T134: LIR add/sub/mul wrap and the isel truncates to the destination type, which is exactly the
         * wrapping_<op> semantics; the checked variants are guarded by separate overflow asserts. */
        case AX_MIR_BINOP_WRAPPING_ADD: return AX_LIR_INST_ADD;
        case AX_MIR_BINOP_WRAPPING_SUB: return AX_LIR_INST_SUB;
        case AX_MIR_BINOP_WRAPPING_MUL: return AX_LIR_INST_MUL;
    }
    return AX_LIR_INST_ADD;
}

static AxLirVRegId lower_rvalue(LirBuilder *b, const AxMirRvalue *rv, TypeId dest_ty) {
    switch (rv->kind) {
        case AX_MIR_RVALUE_USE:
            return lower_operand(b, &rv->use);
        case AX_MIR_RVALUE_REF:
            return lower_place_addr(b, &rv->ref.place, NULL);
        case AX_MIR_RVALUE_OVERFLOWS_BINARY_OP: {
            AxLirVRegId lhs = lower_operand(b, &rv->binary_op.lhs);
            AxLirVRegId rhs = lower_operand(b, &rv->binary_op.rhs);
            AxLirInstKind kind = 0;
            TypeId op_ty = b->interner->t_i32; // fallback
            if (rv->binary_op.lhs.kind == AX_MIR_OP_COPY || rv->binary_op.lhs.kind == AX_MIR_OP_MOVE) {
                op_ty = (rv->binary_op.lhs.place.proj_count > 0) ? get_place_type(b, &rv->binary_op.lhs.place) : b->mir->locals[rv->binary_op.lhs.place.local.v].ty;
            } else if (rv->binary_op.lhs.kind == AX_MIR_OP_CONST) {
                op_ty = rv->binary_op.lhs.constant.ty;
            }
            const AxType *t = ax_type_get(b->interner, op_ty);
            bool is_signed = true;
            if (t && ((t->kind >= AX_TY_U8 && t->kind <= AX_TY_USIZE) || t->kind == AX_TY_BOOL || t->kind == AX_TY_PTR || t->kind == AX_TY_VIEW || t->kind == AX_TY_MUT_VIEW)) {
                is_signed = false;
            }
            switch (rv->binary_op.op) {
                case AX_MIR_BINOP_ADD: kind = is_signed ? AX_LIR_INST_SADD_OVERFLOW : AX_LIR_INST_UADD_OVERFLOW; break;
                case AX_MIR_BINOP_SUB: kind = is_signed ? AX_LIR_INST_SSUB_OVERFLOW : AX_LIR_INST_USUB_OVERFLOW; break;
                case AX_MIR_BINOP_MUL: kind = is_signed ? AX_LIR_INST_SMUL_OVERFLOW : AX_LIR_INST_UMUL_OVERFLOW; break;
                case AX_MIR_BINOP_DIV: kind = is_signed ? AX_LIR_INST_SDIV_OVERFLOW : AX_LIR_INST_UDIV_OVERFLOW; break;
                case AX_MIR_BINOP_REM: kind = is_signed ? AX_LIR_INST_SREM_OVERFLOW : AX_LIR_INST_UREM_OVERFLOW; break;
                default: kind = AX_LIR_INST_SADD_OVERFLOW; break; // fallback
            }
            AxLirVRegId dest = make_vreg(b, dest_ty);
            uint32_t bit_width = ax_type_size(op_ty, b->interner) * 8;
            emit_inst(b, (AxLirInst){ .kind = kind, .dest = dest, .overflow_op = { .lhs = lhs, .rhs = rhs, .bit_width = bit_width } });
            return dest;
        }
        case AX_MIR_RVALUE_BINARY_OP: {
            AxLirVRegId lhs = lower_operand(b, &rv->binary_op.lhs);
            AxLirVRegId rhs = lower_operand(b, &rv->binary_op.rhs);
            TypeId op_ty = b->interner->t_i32;
            if (rv->binary_op.lhs.kind == AX_MIR_OP_COPY || rv->binary_op.lhs.kind == AX_MIR_OP_MOVE) {
                op_ty = (rv->binary_op.lhs.place.proj_count > 0) ? get_place_type(b, &rv->binary_op.lhs.place) : b->mir->locals[rv->binary_op.lhs.place.local.v].ty;
            } else if (rv->binary_op.lhs.kind == AX_MIR_OP_CONST) {
                op_ty = rv->binary_op.lhs.constant.ty;
            }
            const AxType *t = ax_type_get(b->interner, op_ty);
            bool is_signed = true;
            if (t && ((t->kind >= AX_TY_U8 && t->kind <= AX_TY_USIZE) || t->kind == AX_TY_BOOL || t->kind == AX_TY_PTR || t->kind == AX_TY_VIEW || t->kind == AX_TY_MUT_VIEW)) {
                is_signed = false;
            }
            AxLirInstKind kind = lower_binop(rv->binary_op.op, is_signed);
            AxLirVRegId dest = make_vreg(b, dest_ty);
            emit_inst(b, (AxLirInst){ .kind = kind, .dest = dest, .binary = { .lhs = lhs, .rhs = rhs } });
            return dest;
        }
        case AX_MIR_RVALUE_UNARY_OP: {
            AxLirVRegId op = lower_operand(b, &rv->unary_op.operand);
            AxLirInstKind kind = AX_LIR_INST_NEG;
            if (rv->unary_op.op == AX_MIR_UNOP_NOT) kind = AX_LIR_INST_NOT;
            else if (rv->unary_op.op == AX_MIR_UNOP_BITNOT) kind = AX_LIR_INST_BITNOT;
            AxLirVRegId dest = make_vreg(b, dest_ty);
            emit_inst(b, (AxLirInst){ .kind = kind, .dest = dest, .unary = { .operand = op } });
            return dest;
        }
        case AX_MIR_RVALUE_CAST:
            return lower_operand(b, &rv->cast.op);
        case AX_MIR_RVALUE_DISCRIMINANT: {
            TypeId src_ty = {0};
            AxLirVRegId addr = lower_place_addr(b, &rv->discriminant, &src_ty);
            return emit_load(b, addr, b->interner->t_u32);
        }
        case AX_MIR_RVALUE_LEN: {
            TypeId place_ty = b->mir->locals[rv->len.local.v].ty;
            for (size_t i = 0; i < rv->len.proj_count; i++) {
                const AxType *t = ax_type_get(b->interner, place_ty);
                if (rv->len.projs[i].kind == AX_MIR_PROJ_DEREF) {
                    if (t->kind == AX_TY_PTR) place_ty = t->ptr.pointee;
                    else if (t->kind == AX_TY_VIEW || t->kind == AX_TY_MUT_VIEW) place_ty = t->view.pointee;
                    else if (t->kind == AX_TY_STR) place_ty = b->interner->t_u8;
                } else if (rv->len.projs[i].kind == AX_MIR_PROJ_FIELD) {
                    if (t->kind == AX_TY_TUPLE) place_ty = t->tuple.fields[rv->len.projs[i].field_idx];
                    else if (t->kind == AX_TY_STRUCT) place_ty = t->strct.fields[rv->len.projs[i].field_idx];
                } else if (rv->len.projs[i].kind == AX_MIR_PROJ_INDEX) {
                    if (t->kind == AX_TY_ARRAY) place_ty = t->array.elem;
                    else if (t->kind == AX_TY_SLICE) place_ty = t->slice.elem;
                    else if (t->kind == AX_TY_STR) place_ty = b->interner->t_u8;
                }
            }
            const AxType *t = ax_type_get(b->interner, place_ty);
            if (t && t->kind == AX_TY_ARRAY) {
                return emit_const(b, t->array.len, b->interner->t_usize);
            } else if (t && (t->kind == AX_TY_VIEW || t->kind == AX_TY_MUT_VIEW || t->kind == AX_TY_STR)) {
                TypeId src_ty = {0};
                AxLirVRegId addr = lower_place_addr(b, &rv->len, &src_ty);
                AxLirVRegId offset = emit_const(b, 8, b->interner->t_usize);
                AxLirVRegId len_addr = emit_offset(b, addr, offset);
                return emit_load(b, len_addr, b->interner->t_usize);
            } else if (t && t->kind == AX_TY_SLICE) {
                // Should not happen, len() takes view/array directly.
                return emit_const(b, 0, b->interner->t_usize);
            }
            return emit_const(b, 0, b->interner->t_usize);
        }
        case AX_MIR_RVALUE_AGGREGATE:
            return emit_const(b, 0, dest_ty); // Not used directly, handled in assign
        default:
            return emit_const(b, 0, b->interner->t_isize);
    }
}

AxLirBody *ax_lir_lower(const AxMirBody *mir, const struct AxHir *hir, TypeInterner *interner, struct StrInterner *str_in, const AxType *fn_ty) {
    
    AxLirBody *lir = malloc(sizeof(AxLirBody));
    ax_arena_init(&lir->arena, 4096);
    
    LirBuilder b = { .arena = &lir->arena, .interner = interner, .mir = mir, .hir = hir, .str_in = str_in };
    
    // Create stack slots
    b.slot_count = mir->local_count;
    b.slots = ax_arena_alloc(&lir->arena, b.slot_count * sizeof(AxLirStackSlot), _Alignof(AxLirStackSlot));
    for (size_t i = 0; i < mir->local_count; i++) {
        b.slots[i].ty = mir->locals[i].ty;
        b.slots[i].is_const = (mir->locals[i].kind == AX_MIR_LOCAL_CONST);
    }
    
    b.interner = interner;
    b.bb_cap = mir->bb_count + 64;
    b.bbs = calloc(b.bb_cap, sizeof(AxLirBb));
    b.bb_count = mir->bb_count;
    
    for (size_t i = 0; i < mir->bb_count; i++) {
        const AxMirBb *mbb = &mir->bbs[i];
        b.cur_inst_count = 0;
        
        if (i == 0 && fn_ty) {
            const AxType *fty = fn_ty;
            if (fty->kind == AX_TY_CLOSURE && fty->closure.fn_type.v != 0) {
                fty = ax_type_get(b.interner, fty->closure.fn_type);
            }
            if (fty->kind == AX_TY_FN) {
                for (size_t p = 0; p < fty->fn.param_count; p++) {
                    AxLirVRegId dest = make_vreg(&b, fty->fn.param_types[p]);
                    emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_ABI_ARG, .dest = dest, .abi_arg = { .index = (uint32_t)p } });
                    AxLirStackSlotId addr_slot = { (uint32_t)(p + 1) };
                    AxLirVRegId addr = emit_stack_addr(&b, addr_slot);
                    emit_store(&b, addr, dest);
                }
            }
        }
        
        for (size_t j = 0; j < mbb->stmt_count; j++) {
            const AxMirStmt *stmt = &mbb->stmts[j];
            if (stmt->kind == AX_MIR_STMT_ASSIGN) {
                if (mir->locals[stmt->assign.place.local.v].kind == AX_MIR_LOCAL_CONST) {
                    continue;
                }
                TypeId dest_ty = mir->locals[stmt->assign.place.local.v].ty;
                if (stmt->assign.rvalue.kind == AX_MIR_RVALUE_AGGREGATE) {
                    AxLirVRegId addr = lower_place_addr(&b, &stmt->assign.place, &dest_ty);
                    const AxType *ty = ax_type_get(b.interner, dest_ty);
                    if (ty && ty->kind == AX_TY_ENUM) {
                        AxLirVRegId discr_val = emit_const(&b, stmt->assign.rvalue.aggregate.variant_idx, b.interner->t_u32);
                        emit_store(&b, addr, discr_val);
                    }
                    for (size_t k = 0; k < stmt->assign.rvalue.aggregate.operand_count; k++) {
                        uint32_t offset = 0;
                        TypeId field_ty = {0};
                        if (ty && ty->kind == AX_TY_ENUM) {
                            offset = ax_type_enum_field_offset(dest_ty, stmt->assign.rvalue.aggregate.variant_idx, k, b.interner);
                            if (k < ty->enm.variant_field_counts[stmt->assign.rvalue.aggregate.variant_idx]) {
                                field_ty = ty->enm.variant_fields[stmt->assign.rvalue.aggregate.variant_idx][k];
                            }
                        } else if (ty && (ty->kind == AX_TY_STRUCT || ty->kind == AX_TY_TUPLE || ty->kind == AX_TY_CLOSURE)) {
                            offset = ax_type_field_offset(dest_ty, k, b.interner);
                            if (ty->kind == AX_TY_STRUCT && k < ty->strct.field_count) {
                                field_ty = ty->strct.fields[k];
                            } else if (ty->kind == AX_TY_TUPLE && k < ty->tuple.field_count) {
                                field_ty = ty->tuple.fields[k];
                            } else if (ty->kind == AX_TY_CLOSURE) {
                                field_ty = (k == 0) ? b.interner->t_usize : (k - 1 < ty->closure.capture_count ? ty->closure.captures[k - 1].type : (TypeId){0});
                            }
                        } else if (ty && ty->kind == AX_TY_ARRAY) {
                            field_ty = ty->array.elem;
                            uint32_t fa = ax_type_align(field_ty, b.interner);
                            uint32_t fs = ax_type_size(field_ty, b.interner);
                            uint32_t stride = (fs + fa - 1) & ~(fa - 1);
                            offset = (uint32_t)(k * stride);
                        }
                        AxLirVRegId off_reg = emit_const(&b, offset, b.interner->t_usize);
                        AxLirVRegId field_addr = emit_offset(&b, addr, off_reg);
                        
                        AxLirVRegId field_val;
                        if (ty && ty->kind == AX_TY_CLOSURE && k == 0 && stmt->assign.rvalue.aggregate.operands[0].kind == AX_MIR_OP_CONST) {
                            uint32_t sym_v = (uint32_t)stmt->assign.rvalue.aggregate.operands[0].constant.val;
                            const char *fn_name = get_fn_sym_name(b.hir, b.str_in, sym_v);
                            field_val = make_vreg(&b, b.interner->t_usize);
                            emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_FN_ADDR, .dest = field_val, .fn_addr = { .sym_name = fn_name } });
                        } else {
                            field_val = lower_operand(&b, &stmt->assign.rvalue.aggregate.operands[k]);
                        }
                        if (field_ty.v != 0) {
                            b.vregs[field_val.v].ty = field_ty;
                        }
                        emit_store(&b, field_addr, field_val);
                    }
                    continue;
                } else if (stmt->assign.rvalue.kind == AX_MIR_RVALUE_REPEAT) {
                    AxLirVRegId addr = lower_place_addr(&b, &stmt->assign.place, &dest_ty);
                    const AxType *ty = ax_type_get(b.interner, dest_ty);
                    if (ty && ty->kind == AX_TY_ARRAY) {
                        TypeId elem_ty = ty->array.elem;
                        uint32_t fa = ax_type_align(elem_ty, b.interner);
                        uint32_t fs = ax_type_size(elem_ty, b.interner);
                        uint32_t stride = (fs + fa - 1) & ~(fa - 1);
                        
                        uint64_t count = ty->array.len;
                        
                        AxLirVRegId elem_val = lower_operand(&b, &stmt->assign.rvalue.repeat.op);
                        if (elem_ty.v != 0) {
                            b.vregs[elem_val.v].ty = elem_ty;
                        }
                        
                        AxLirVRegId off_reg = make_vreg(&b, b.interner->t_usize);
                        AxLirVRegId elem_addr = make_vreg(&b, b.interner->t_usize);
                        for (uint64_t k = 0; k < count; k++) {
                            uint32_t offset = (uint32_t)(k * stride);
                            emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_CONST, .dest = off_reg, .constant = { .val = offset, .ty = b.interner->t_usize } });
                            emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_ADD, .dest = elem_addr, .binary = { .lhs = addr, .rhs = off_reg } });
                            emit_store(&b, elem_addr, elem_val);
                        }
                    }
                    continue;
                } else if (stmt->assign.rvalue.kind == AX_MIR_RVALUE_REF) {
                    const AxType *ty = ax_type_get(b.interner, dest_ty);
                    if (ty && (ty->kind == AX_TY_VIEW || ty->kind == AX_TY_MUT_VIEW)) {
                        const AxType *pointee = ax_type_get(b.interner, ty->view.pointee);
                        if (pointee && (pointee->kind == AX_TY_SLICE || pointee->kind == AX_TY_STR)) {
                            AxLirVRegId addr = lower_place_addr(&b, &stmt->assign.place, NULL);
                            TypeId src_ty = {0};
                            AxLirVRegId ptr_val = lower_place_addr(&b, &stmt->assign.rvalue.ref.place, &src_ty);
                            emit_store(&b, addr, ptr_val);
                            
                            AxLirVRegId len_reg = {0};
                            const AxType *src_t = ax_type_get(b.interner, src_ty);
                            if (stmt->assign.rvalue.ref.place.proj_count > 0 && stmt->assign.rvalue.ref.place.projs[stmt->assign.rvalue.ref.place.proj_count - 1].kind == AX_MIR_PROJ_SUB_SLICE) {
                                AxMirProjection *sub_slice = &stmt->assign.rvalue.ref.place.projs[stmt->assign.rvalue.ref.place.proj_count - 1];
                                AxLirVRegId from_val = emit_const(&b, 0, b.interner->t_usize);
                                if (sub_slice->sub_slice.has_from) {
                                    AxLirStackSlotId idx_slot = { sub_slice->sub_slice.from_local.v };
                                    AxLirVRegId idx_addr = emit_stack_addr(&b, idx_slot);
                                    from_val = emit_load(&b, idx_addr, b.interner->t_usize);
                                }
                                AxLirVRegId to_val = emit_const(&b, 0, b.interner->t_usize);
                                if (sub_slice->sub_slice.has_to) {
                                    AxLirStackSlotId idx_slot = { sub_slice->sub_slice.to_local.v };
                                    AxLirVRegId idx_addr = emit_stack_addr(&b, idx_slot);
                                    to_val = emit_load(&b, idx_addr, b.interner->t_usize);
                                } else {
                                    AxMirPlace base_place = stmt->assign.rvalue.ref.place;
                                    base_place.proj_count--;
                                    if (base_place.proj_count > 0 && base_place.projs[base_place.proj_count - 1].kind == AX_MIR_PROJ_DEREF) {
                                        base_place.proj_count--;
                                    }
                                    TypeId base_ty = {0};
                                    AxLirVRegId base_addr = lower_place_addr(&b, &base_place, &base_ty);
                                    const AxType *base_t = ax_type_get(b.interner, base_ty);
                                    if (base_t && base_t->kind == AX_TY_ARRAY) {
                                        to_val = emit_const(&b, (uint64_t)base_t->array.len, b.interner->t_usize);
                                    } else {
                                        AxLirVRegId off8 = emit_const(&b, 8, b.interner->t_usize);
                                        AxLirVRegId len_addr = emit_offset(&b, base_addr, off8);
                                        to_val = emit_load(&b, len_addr, b.interner->t_usize);
                                    }
                                }
                                len_reg = make_vreg(&b, b.interner->t_usize);
                                emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_SUB, .dest = len_reg, .binary = { .lhs = to_val, .rhs = from_val } });
                            } else if (src_t && src_t->kind == AX_TY_ARRAY) {
                                len_reg = emit_const(&b, src_t->array.len, b.interner->t_usize);
                            } else if (src_t && (src_t->kind == AX_TY_VIEW || src_t->kind == AX_TY_MUT_VIEW || src_t->kind == AX_TY_STR || src_t->kind == AX_TY_SLICE)) {
                                AxLirVRegId src_addr = lower_place_addr(&b, &stmt->assign.rvalue.ref.place, NULL);
                                AxLirVRegId off8 = emit_const(&b, 8, b.interner->t_usize);
                                AxLirVRegId len_addr = emit_offset(&b, src_addr, off8);
                                len_reg = emit_load(&b, len_addr, b.interner->t_usize);
                            } else {
                                len_reg = emit_const(&b, 0, b.interner->t_usize);
                            }
                            
                            AxLirVRegId off8 = emit_const(&b, 8, b.interner->t_usize);
                            AxLirVRegId len_dest = emit_offset(&b, addr, off8);
                            emit_store(&b, len_dest, len_reg);
                            continue;
                        }
                    }
                }
                
                TypeId target_ty = (stmt->assign.place.proj_count > 0) ? get_place_type(&b, &stmt->assign.place) : dest_ty;
                AxLirVRegId val = lower_rvalue(&b, &stmt->assign.rvalue, target_ty);
                if (target_ty.v != 0) {
                    b.vregs[val.v].ty = target_ty;
                }
                AxLirVRegId addr = lower_place_addr(&b, &stmt->assign.place, NULL);
                emit_store(&b, addr, val);
            }
        }
        
        AxLirTerminator term = {0};
        switch (mbb->terminator.kind) {
            case AX_MIR_TERM_GOTO:
                term.kind = AX_LIR_TERM_JMP;
                term.jmp_target = (AxLirBbId){ mbb->terminator.goto_target.v };
                break;
            case AX_MIR_TERM_SWITCH_INT: {
                AxLirVRegId cond = lower_operand(&b, &mbb->terminator.switch_int.discr);
                term.kind = AX_LIR_TERM_SWITCH;
                term.switch_int.cond = cond;
                term.switch_int.count = mbb->terminator.switch_int.targets.count;
                if (term.switch_int.count > 0) {
                    term.switch_int.targets = ax_arena_alloc(&lir->arena, term.switch_int.count * sizeof(AxLirSwitchTarget), _Alignof(AxLirSwitchTarget));
                    for (size_t k = 0; k < term.switch_int.count; k++) {
                        term.switch_int.targets[k].value = mbb->terminator.switch_int.targets.values[k].value;
                        term.switch_int.targets[k].target = (AxLirBbId){ mbb->terminator.switch_int.targets.values[k].target.v };
                    }
                }
                term.switch_int.otherwise = (AxLirBbId){ mbb->terminator.switch_int.targets.otherwise.v };
                break;
            }
            case AX_MIR_TERM_RETURN:
                term.kind = AX_LIR_TERM_RETURN;
                break;
            case AX_MIR_TERM_CALL: {
                TypeId callee_ty = {0};
                if (mbb->terminator.call.func.kind == AX_MIR_OP_CONST) {
                    callee_ty = mbb->terminator.call.func.constant.ty;
                } else {
                    AxMirLocalId loc = mbb->terminator.call.func.place.local;
                    callee_ty = mir->locals[loc.v].ty;
                }
                const AxType *cty = callee_ty.v ? ax_type_get(b.interner, callee_ty) : NULL;

                if (cty && (cty->kind == AX_TY_BUILTIN_PTR_ADD || cty->kind == AX_TY_BUILTIN_PTR_SUB)) {
                    AxLirVRegId p = lower_operand(&b, &mbb->terminator.call.args[0]);
                    AxLirVRegId count = lower_operand(&b, &mbb->terminator.call.args[1]);
                    TypeId elem_ty = { (uint32_t)mbb->terminator.call.func.constant.val };
                    uint32_t elem_sz = ax_type_size(elem_ty, b.interner);
                    if (elem_sz == 0) elem_sz = 1;
                    AxLirVRegId offset;
                    if (elem_sz == 1) {
                        offset = count;
                    } else {
                        AxLirVRegId sz_reg = emit_const(&b, elem_sz, b.interner->t_usize);
                        offset = make_vreg(&b, b.interner->t_usize);
                        emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_MUL, .dest = offset, .binary = { .lhs = count, .rhs = sz_reg } });
                    }
                    AxLirVRegId res = make_vreg(&b, b.interner->t_usize);
                    emit_inst(&b, (AxLirInst){
                        .kind = (cty->kind == AX_TY_BUILTIN_PTR_ADD) ? AX_LIR_INST_ADD : AX_LIR_INST_SUB,
                        .dest = res,
                        .binary = { .lhs = p, .rhs = offset }
                    });
                    AxLirVRegId dst_addr = lower_place_addr(&b, &mbb->terminator.call.destination, NULL);
                    emit_store(&b, dst_addr, res);
                    finish_bb(&b, i, (AxLirTerminator){ .kind = AX_LIR_TERM_JMP, .jmp_target = (AxLirBbId){ mbb->terminator.call.target.v } });
                    continue;
                }
                if (cty && cty->kind == AX_TY_BUILTIN_NEEDS_DROP) {
                    TypeId elem_ty = { (uint32_t)mbb->terminator.call.func.constant.val };
                    bool nd = lir_type_needs_drop(&b, elem_ty);
                    AxLirVRegId val = emit_const(&b, nd ? 1 : 0, b.interner->t_bool);
                    AxLirVRegId dst_addr = lower_place_addr(&b, &mbb->terminator.call.destination, NULL);
                    emit_store(&b, dst_addr, val);
                    finish_bb(&b, i, (AxLirTerminator){ .kind = AX_LIR_TERM_JMP, .jmp_target = (AxLirBbId){ mbb->terminator.call.target.v } });
                    continue;
                }
                if (cty && cty->kind == AX_TY_BUILTIN_DROP_IN_PLACE) {
                    TypeId elem_ty = { (uint32_t)mbb->terminator.call.func.constant.val };
                    const char *drop_sym = find_drop_fn_sym_name(b.hir, b.str_in, elem_ty, b.interner);
                    if (drop_sym) {
                        AxLirVRegId p = lower_operand(&b, &mbb->terminator.call.args[0]);
                        emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_ABI_ARG, .dest = { 0xFFFFFFFF }, .abi_arg = { .index = 0, .val = p } });
                        TypeId param_ty = b.interner->t_usize;
                        AxType fn_type = {
                            .kind = AX_TY_FN,
                            .fn = {
                                .param_types = &param_ty,
                                .param_count = 1,
                                .ret_type = b.interner->t_unit
                            }
                        };
                        TypeId callee_drop_ty = ax_intern_type(b.interner, &fn_type);
                        emit_inst(&b, (AxLirInst){
                            .kind = AX_LIR_INST_CALL,
                            .dest = {0},
                            .call = {
                                .sym_name = drop_sym,
                                .callee_ty = callee_drop_ty,
                                .dst_addr = (AxLirVRegId){ 0xFFFFFFFF },
                                .callee_vreg = (AxLirVRegId){ 0xFFFFFFFF }
                            }
                        });
                    }
                    finish_bb(&b, i, (AxLirTerminator){ .kind = AX_LIR_TERM_JMP, .jmp_target = (AxLirBbId){ mbb->terminator.call.target.v } });
                    continue;
                }
                if (cty && cty->kind == AX_TY_BUILTIN_PTR_WRITE_BYTES) {
                    AxLirVRegId dst = lower_operand(&b, &mbb->terminator.call.args[0]);
                    AxLirVRegId val = lower_operand(&b, &mbb->terminator.call.args[1]);
                    b.vregs[val.v].ty = b.interner->t_u8;
                    AxLirVRegId count = lower_operand(&b, &mbb->terminator.call.args[2]);
                    TypeId elem_ty = { (uint32_t)mbb->terminator.call.func.constant.val };
                    uint32_t elem_sz = ax_type_size(elem_ty, b.interner);
                    if (elem_sz == 0) elem_sz = 1;
                    AxLirVRegId total_bytes;
                    if (elem_sz == 1) {
                        total_bytes = count;
                    } else {
                        AxLirVRegId sz_reg = emit_const(&b, elem_sz, b.interner->t_usize);
                        total_bytes = make_vreg(&b, b.interner->t_usize);
                        emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_MUL, .dest = total_bytes, .binary = { .lhs = count, .rhs = sz_reg } });
                    }
                    AxLirVRegId idx = make_vreg(&b, b.interner->t_usize);
                    AxLirVRegId zero = emit_const(&b, 0, b.interner->t_usize);
                    emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_ADD, .dest = idx, .binary = { .lhs = zero, .rhs = zero } });

                    size_t head_bb = add_lir_bb(&b);
                    size_t body_bb = add_lir_bb(&b);
                    size_t target_bb = mbb->terminator.call.target.v;
                    finish_bb(&b, i, (AxLirTerminator){ .kind = AX_LIR_TERM_JMP, .jmp_target = (AxLirBbId){ (uint32_t)head_bb } });

                    // head_bb
                    AxLirVRegId cmp = make_vreg(&b, b.interner->t_bool);
                    emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_ICMP_ULT, .dest = cmp, .binary = { .lhs = idx, .rhs = total_bytes } });
                    AxLirSwitchTarget *sw = ax_arena_alloc(b.arena, sizeof(AxLirSwitchTarget), _Alignof(AxLirSwitchTarget));
                    sw[0].value = 1;
                    sw[0].target = (AxLirBbId){ (uint32_t)body_bb };
                    AxLirTerminator head_term = {
                        .kind = AX_LIR_TERM_SWITCH,
                        .switch_int = {
                            .cond = cmp,
                            .targets = sw,
                            .count = 1,
                            .otherwise = (AxLirBbId){ (uint32_t)target_bb }
                        }
                    };
                    finish_bb(&b, head_bb, head_term);

                    // body_bb
                    AxLirVRegId curr_addr = make_vreg(&b, b.interner->t_usize);
                    emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_ADD, .dest = curr_addr, .binary = { .lhs = dst, .rhs = idx } });
                    emit_store(&b, curr_addr, val);
                    AxLirVRegId one = emit_const(&b, 1, b.interner->t_usize);
                    emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_ADD, .dest = idx, .binary = { .lhs = idx, .rhs = one } });
                    finish_bb(&b, body_bb, (AxLirTerminator){ .kind = AX_LIR_TERM_JMP, .jmp_target = (AxLirBbId){ (uint32_t)head_bb } });
                    continue;
                }
                if (cty && cty->kind == AX_TY_BUILTIN_PTR_COPY_NONOVERLAPPING) {
                    AxLirVRegId src = lower_operand(&b, &mbb->terminator.call.args[0]);
                    AxLirVRegId dst = lower_operand(&b, &mbb->terminator.call.args[1]);
                    AxLirVRegId count = lower_operand(&b, &mbb->terminator.call.args[2]);
                    TypeId elem_ty = { (uint32_t)mbb->terminator.call.func.constant.val };
                    uint32_t elem_sz = ax_type_size(elem_ty, b.interner);
                    if (elem_sz == 0) elem_sz = 1;
                    AxLirVRegId total_bytes;
                    if (elem_sz == 1) {
                        total_bytes = count;
                    } else {
                        AxLirVRegId sz_reg = emit_const(&b, elem_sz, b.interner->t_usize);
                        total_bytes = make_vreg(&b, b.interner->t_usize);
                        emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_MUL, .dest = total_bytes, .binary = { .lhs = count, .rhs = sz_reg } });
                    }
                    AxLirVRegId idx = make_vreg(&b, b.interner->t_usize);
                    AxLirVRegId zero = emit_const(&b, 0, b.interner->t_usize);
                    emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_ADD, .dest = idx, .binary = { .lhs = zero, .rhs = zero } });

                    size_t head_bb = add_lir_bb(&b);
                    size_t body_bb = add_lir_bb(&b);
                    size_t target_bb = mbb->terminator.call.target.v;
                    finish_bb(&b, i, (AxLirTerminator){ .kind = AX_LIR_TERM_JMP, .jmp_target = (AxLirBbId){ (uint32_t)head_bb } });

                    // head_bb
                    AxLirVRegId cmp = make_vreg(&b, b.interner->t_bool);
                    emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_ICMP_ULT, .dest = cmp, .binary = { .lhs = idx, .rhs = total_bytes } });
                    AxLirSwitchTarget *sw = ax_arena_alloc(b.arena, sizeof(AxLirSwitchTarget), _Alignof(AxLirSwitchTarget));
                    sw[0].value = 1;
                    sw[0].target = (AxLirBbId){ (uint32_t)body_bb };
                    AxLirTerminator head_term = {
                        .kind = AX_LIR_TERM_SWITCH,
                        .switch_int = {
                            .cond = cmp,
                            .targets = sw,
                            .count = 1,
                            .otherwise = (AxLirBbId){ (uint32_t)target_bb }
                        }
                    };
                    finish_bb(&b, head_bb, head_term);

                    // body_bb
                    AxLirVRegId src_curr = make_vreg(&b, b.interner->t_usize);
                    emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_ADD, .dest = src_curr, .binary = { .lhs = src, .rhs = idx } });
                    AxLirVRegId byte_val = emit_load(&b, src_curr, b.interner->t_u8);
                    AxLirVRegId dst_curr = make_vreg(&b, b.interner->t_usize);
                    emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_ADD, .dest = dst_curr, .binary = { .lhs = dst, .rhs = idx } });
                    emit_store(&b, dst_curr, byte_val);
                    AxLirVRegId one = emit_const(&b, 1, b.interner->t_usize);
                    emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_ADD, .dest = idx, .binary = { .lhs = idx, .rhs = one } });
                    finish_bb(&b, body_bb, (AxLirTerminator){ .kind = AX_LIR_TERM_JMP, .jmp_target = (AxLirBbId){ (uint32_t)head_bb } });
                    continue;
                }
                if (cty && cty->kind == AX_TY_BUILTIN_PTR_COPY) {
                    AxLirVRegId src = lower_operand(&b, &mbb->terminator.call.args[0]);
                    AxLirVRegId dst = lower_operand(&b, &mbb->terminator.call.args[1]);
                    AxLirVRegId count = lower_operand(&b, &mbb->terminator.call.args[2]);
                    TypeId elem_ty = { (uint32_t)mbb->terminator.call.func.constant.val };
                    uint32_t elem_sz = ax_type_size(elem_ty, b.interner);
                    if (elem_sz == 0) elem_sz = 1;
                    AxLirVRegId total_bytes;
                    if (elem_sz == 1) {
                        total_bytes = count;
                    } else {
                        AxLirVRegId sz_reg = emit_const(&b, elem_sz, b.interner->t_usize);
                        total_bytes = make_vreg(&b, b.interner->t_usize);
                        emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_MUL, .dest = total_bytes, .binary = { .lhs = count, .rhs = sz_reg } });
                    }
                    AxLirVRegId is_bwd = make_vreg(&b, b.interner->t_bool);
                    emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_ICMP_ULT, .dest = is_bwd, .binary = { .lhs = src, .rhs = dst } });

                    size_t bwd_setup_bb = add_lir_bb(&b);
                    size_t bwd_head_bb = add_lir_bb(&b);
                    size_t bwd_body_bb = add_lir_bb(&b);
                    size_t fwd_setup_bb = add_lir_bb(&b);
                    size_t fwd_head_bb = add_lir_bb(&b);
                    size_t fwd_body_bb = add_lir_bb(&b);
                    size_t target_bb = mbb->terminator.call.target.v;

                    AxLirSwitchTarget *sw_dir = ax_arena_alloc(b.arena, sizeof(AxLirSwitchTarget), _Alignof(AxLirSwitchTarget));
                    sw_dir[0].value = 1;
                    sw_dir[0].target = (AxLirBbId){ (uint32_t)bwd_setup_bb };
                    finish_bb(&b, i, (AxLirTerminator){
                        .kind = AX_LIR_TERM_SWITCH,
                        .switch_int = {
                            .cond = is_bwd,
                            .targets = sw_dir,
                            .count = 1,
                            .otherwise = (AxLirBbId){ (uint32_t)fwd_setup_bb }
                        }
                    });

                    // bwd_setup_bb: bwd_idx = total_bytes
                    AxLirVRegId bwd_idx = make_vreg(&b, b.interner->t_usize);
                    AxLirVRegId zero_b = emit_const(&b, 0, b.interner->t_usize);
                    emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_ADD, .dest = bwd_idx, .binary = { .lhs = total_bytes, .rhs = zero_b } });
                    finish_bb(&b, bwd_setup_bb, (AxLirTerminator){ .kind = AX_LIR_TERM_JMP, .jmp_target = (AxLirBbId){ (uint32_t)bwd_head_bb } });

                    // bwd_head_bb: bwd_idx > 0
                    AxLirVRegId cmp_zero = emit_const(&b, 0, b.interner->t_usize);
                    AxLirVRegId bwd_cmp = make_vreg(&b, b.interner->t_bool);
                    emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_ICMP_UGT, .dest = bwd_cmp, .binary = { .lhs = bwd_idx, .rhs = cmp_zero } });
                    AxLirSwitchTarget *sw_bwd = ax_arena_alloc(b.arena, sizeof(AxLirSwitchTarget), _Alignof(AxLirSwitchTarget));
                    sw_bwd[0].value = 1;
                    sw_bwd[0].target = (AxLirBbId){ (uint32_t)bwd_body_bb };
                    finish_bb(&b, bwd_head_bb, (AxLirTerminator){
                        .kind = AX_LIR_TERM_SWITCH,
                        .switch_int = {
                            .cond = bwd_cmp,
                            .targets = sw_bwd,
                            .count = 1,
                            .otherwise = (AxLirBbId){ (uint32_t)target_bb }
                        }
                    });

                    // bwd_body_bb: bwd_idx = bwd_idx - 1; copy at bwd_idx
                    AxLirVRegId one_b = emit_const(&b, 1, b.interner->t_usize);
                    emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_SUB, .dest = bwd_idx, .binary = { .lhs = bwd_idx, .rhs = one_b } });
                    AxLirVRegId s_addr_b = make_vreg(&b, b.interner->t_usize);
                    emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_ADD, .dest = s_addr_b, .binary = { .lhs = src, .rhs = bwd_idx } });
                    AxLirVRegId b_val_b = emit_load(&b, s_addr_b, b.interner->t_u8);
                    AxLirVRegId d_addr_b = make_vreg(&b, b.interner->t_usize);
                    emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_ADD, .dest = d_addr_b, .binary = { .lhs = dst, .rhs = bwd_idx } });
                    emit_store(&b, d_addr_b, b_val_b);
                    finish_bb(&b, bwd_body_bb, (AxLirTerminator){ .kind = AX_LIR_TERM_JMP, .jmp_target = (AxLirBbId){ (uint32_t)bwd_head_bb } });

                    // fwd_setup_bb: fwd_idx = 0
                    AxLirVRegId fwd_idx = make_vreg(&b, b.interner->t_usize);
                    AxLirVRegId zero_f = emit_const(&b, 0, b.interner->t_usize);
                    emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_ADD, .dest = fwd_idx, .binary = { .lhs = zero_f, .rhs = zero_f } });
                    finish_bb(&b, fwd_setup_bb, (AxLirTerminator){ .kind = AX_LIR_TERM_JMP, .jmp_target = (AxLirBbId){ (uint32_t)fwd_head_bb } });

                    // fwd_head_bb: fwd_idx < total_bytes
                    AxLirVRegId fwd_cmp = make_vreg(&b, b.interner->t_bool);
                    emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_ICMP_ULT, .dest = fwd_cmp, .binary = { .lhs = fwd_idx, .rhs = total_bytes } });
                    AxLirSwitchTarget *sw_fwd = ax_arena_alloc(b.arena, sizeof(AxLirSwitchTarget), _Alignof(AxLirSwitchTarget));
                    sw_fwd[0].value = 1;
                    sw_fwd[0].target = (AxLirBbId){ (uint32_t)fwd_body_bb };
                    finish_bb(&b, fwd_head_bb, (AxLirTerminator){
                        .kind = AX_LIR_TERM_SWITCH,
                        .switch_int = {
                            .cond = fwd_cmp,
                            .targets = sw_fwd,
                            .count = 1,
                            .otherwise = (AxLirBbId){ (uint32_t)target_bb }
                        }
                    });

                    // fwd_body_bb: copy at fwd_idx; fwd_idx = fwd_idx + 1
                    AxLirVRegId s_addr_f = make_vreg(&b, b.interner->t_usize);
                    emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_ADD, .dest = s_addr_f, .binary = { .lhs = src, .rhs = fwd_idx } });
                    AxLirVRegId b_val_f = emit_load(&b, s_addr_f, b.interner->t_u8);
                    AxLirVRegId d_addr_f = make_vreg(&b, b.interner->t_usize);
                    emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_ADD, .dest = d_addr_f, .binary = { .lhs = dst, .rhs = fwd_idx } });
                    emit_store(&b, d_addr_f, b_val_f);
                    AxLirVRegId one_f = emit_const(&b, 1, b.interner->t_usize);
                    emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_ADD, .dest = fwd_idx, .binary = { .lhs = fwd_idx, .rhs = one_f } });
                    finish_bb(&b, fwd_body_bb, (AxLirTerminator){ .kind = AX_LIR_TERM_JMP, .jmp_target = (AxLirBbId){ (uint32_t)fwd_head_bb } });
                    continue;
                }
                if (cty && cty->kind == AX_TY_BUILTIN_SIZE_OF) {
                    TypeId elem_ty = { (uint32_t)mbb->terminator.call.func.constant.val };
                    uint32_t sz = ax_type_size(elem_ty, b.interner);
                    AxLirVRegId val = emit_const(&b, sz, b.interner->t_usize);
                    AxLirVRegId dst_addr = lower_place_addr(&b, &mbb->terminator.call.destination, NULL);
                    emit_store(&b, dst_addr, val);
                    finish_bb(&b, i, (AxLirTerminator){ .kind = AX_LIR_TERM_JMP, .jmp_target = (AxLirBbId){ mbb->terminator.call.target.v } });
                    continue;
                }
                if (cty && cty->kind == AX_TY_BUILTIN_ALIGN_OF) {
                    TypeId elem_ty = { (uint32_t)mbb->terminator.call.func.constant.val };
                    uint32_t al = ax_type_align(elem_ty, b.interner);
                    AxLirVRegId val = emit_const(&b, al, b.interner->t_usize);
                    AxLirVRegId dst_addr = lower_place_addr(&b, &mbb->terminator.call.destination, NULL);
                    emit_store(&b, dst_addr, val);
                    finish_bb(&b, i, (AxLirTerminator){ .kind = AX_LIR_TERM_JMP, .jmp_target = (AxLirBbId){ mbb->terminator.call.target.v } });
                    continue;
                }
                if (cty && (cty->kind == AX_TY_BUILTIN_NULL || cty->kind == AX_TY_BUILTIN_NULL_MUT)) {
                    AxLirVRegId val = emit_const(&b, 0, b.interner->t_usize);
                    AxLirVRegId dst_addr = lower_place_addr(&b, &mbb->terminator.call.destination, NULL);
                    emit_store(&b, dst_addr, val);
                    finish_bb(&b, i, (AxLirTerminator){ .kind = AX_LIR_TERM_JMP, .jmp_target = (AxLirBbId){ mbb->terminator.call.target.v } });
                    continue;
                }
                if (cty && cty->kind == AX_TY_BUILTIN_IS_NULL) {
                    AxLirVRegId p = lower_operand(&b, &mbb->terminator.call.args[0]);
                    AxLirVRegId zero = emit_const(&b, 0, b.interner->t_usize);
                    AxLirVRegId cmp = make_vreg(&b, b.interner->t_bool);
                    emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_ICMP_EQ, .dest = cmp, .binary = { .lhs = p, .rhs = zero } });
                    AxLirVRegId dst_addr = lower_place_addr(&b, &mbb->terminator.call.destination, NULL);
                    emit_store(&b, dst_addr, cmp);
                    finish_bb(&b, i, (AxLirTerminator){ .kind = AX_LIR_TERM_JMP, .jmp_target = (AxLirBbId){ mbb->terminator.call.target.v } });
                    continue;
                }
                if (cty && cty->kind == AX_TY_BUILTIN_FORGET) {
                    finish_bb(&b, i, (AxLirTerminator){ .kind = AX_LIR_TERM_JMP, .jmp_target = (AxLirBbId){ mbb->terminator.call.target.v } });
                    continue;
                }
                
                size_t cap_count = 0;
                if (cty && cty->kind == AX_TY_CLOSURE) {
                    cap_count = cty->closure.capture_count;
                }
                
                AxLirVRegId cap_vals[64];
                if (cap_count > 0 && mbb->terminator.call.func.kind != AX_MIR_OP_CONST) {
                    AxLirVRegId closure_base = lower_place_addr(&b, &mbb->terminator.call.func.place, NULL);
                    for (size_t c = 0; c < cap_count && c < 64; c++) {
                        uint32_t offset = ax_type_field_offset(callee_ty, c + 1, b.interner);
                        AxLirVRegId cap_off = emit_const(&b, offset, b.interner->t_usize);
                        AxLirVRegId cap_addr = emit_offset(&b, closure_base, cap_off);
                        cap_vals[c] = emit_load(&b, cap_addr, cty->closure.captures[c].type);
                    }
                }
                
                if (cty && cty->kind == AX_TY_CLOSURE && cty->closure.fn_type.v != 0) {
                    callee_ty = cty->closure.fn_type;
                }
                
                AxLirVRegId *arg_vals = mbb->terminator.call.arg_count ? malloc(mbb->terminator.call.arg_count * sizeof(AxLirVRegId)) : NULL;
                for (size_t k = 0; k < mbb->terminator.call.arg_count; k++) {
                    arg_vals[k] = lower_operand(&b, &mbb->terminator.call.args[k]);
                }
                
                const char *sym_name = NULL;
                AxLirVRegId callee_vreg = { 0xFFFFFFFF };
                
                if (mbb->terminator.call.func.kind == AX_MIR_OP_CONST) {
                    uint32_t sym_v = (uint32_t)mbb->terminator.call.func.constant.val;
                    if (cty && cty->kind == AX_TY_BUILTIN_PRINT) {
                        sym_name = "__ax_host_print";
                    } else if (cty && cty->kind == AX_TY_BUILTIN_PRINT_INT) {
                        sym_name = "__ax_host_print_int";
                    } else {
                        sym_name = get_fn_sym_name(b.hir, b.str_in, sym_v);
                    }
                } else if (cty && cty->kind == AX_TY_CLOSURE) {
                    AxLirVRegId closure_base = lower_place_addr(&b, &mbb->terminator.call.func.place, NULL);
                    callee_vreg = emit_load(&b, closure_base, b.interner->t_usize);
                } else {
                    callee_vreg = lower_operand(&b, &mbb->terminator.call.func);
                }
                
                TypeId dst_ty = {0};
                AxLirVRegId dst_addr = lower_place_addr(&b, &mbb->terminator.call.destination, &dst_ty);
                if (dst_ty.v == 0) {
                    dst_ty = mir->locals[mbb->terminator.call.destination.local.v].ty;
                }

                for (size_t c = 0; c < cap_count && c < 64; c++) {
                    emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_ABI_ARG, .dest = { 0xFFFFFFFF }, .abi_arg = { .index = (uint32_t)c, .val = cap_vals[c] } });
                }
                for (size_t k = 0; k < mbb->terminator.call.arg_count; k++) {
                    emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_ABI_ARG, .dest = { 0xFFFFFFFF }, .abi_arg = { .index = (uint32_t)(cap_count + k), .val = arg_vals[k] } });
                }
                free(arg_vals);
                
                emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_CALL, .dest = {0}, .call = { .sym_name = sym_name, .callee_ty = callee_ty, .dst_addr = dst_addr, .callee_vreg = callee_vreg } });
                
                AxLirVRegId res = make_vreg(&b, dst_ty);
                emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_ABI_RESULT, .dest = res, .abi_result = { .index = 0 } });
                emit_store(&b, dst_addr, res);
                
                term.kind = AX_LIR_TERM_JMP;
                term.jmp_target = (AxLirBbId){ mbb->terminator.call.target.v };
                break;
            }
            case AX_MIR_TERM_ASSERT: {
                AxLirVRegId cond_vreg = lower_operand(&b, &mbb->terminator.assert.cond);
                if (!mbb->terminator.assert.expected) {
                    AxLirVRegId one = emit_const(&b, 1, b.interner->t_bool);
                    AxLirVRegId xor_res = make_vreg(&b, b.interner->t_bool);
                    emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_BIT_XOR, .dest = xor_res, .binary = { .lhs = cond_vreg, .rhs = one } });
                    cond_vreg = xor_res;
                }
                term.kind = AX_LIR_TERM_ASSERT;
                term.assert_term.cond = cond_vreg;
                term.assert_term.target = (AxLirBbId){ mbb->terminator.assert.target.v };
                term.assert_term.msg = mbb->terminator.assert.msg;
                break;
            }
            default:
                term.kind = AX_LIR_TERM_UNREACHABLE;
                break;
        }
        
        finish_bb(&b, i, term);
    }
    
    lir->slots = b.slots;
    lir->slot_count = b.slot_count;
    
    if (b.vreg_count > 0) {
        lir->vregs = ax_arena_alloc(&lir->arena, b.vreg_count * sizeof(AxLirVReg), _Alignof(AxLirVReg));
        for (size_t i = 0; i < b.vreg_count; i++) lir->vregs[i] = b.vregs[i];
    } else {
        lir->vregs = NULL;
    }
    lir->vreg_count = b.vreg_count;
    
    if (b.bb_count > 0) {
        lir->bbs = ax_arena_alloc(&lir->arena, b.bb_count * sizeof(AxLirBb), _Alignof(AxLirBb));
        memcpy(lir->bbs, b.bbs, b.bb_count * sizeof(AxLirBb));
    } else {
        lir->bbs = NULL;
    }
    lir->bb_count = b.bb_count;
    
    free(b.bbs);
    free(b.vregs);
    free(b.cur_insts);
    
    return lir;
}
