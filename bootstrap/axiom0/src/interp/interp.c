#include "interp/interp.h"
#include "mir/build/build.h"
#include "types/layout/layout.h"
#include <stdlib.h>
#include <string.h>
#include "kernel/hashmap.h"
#include "kernel/base.h"

typedef AxMirBody *AxMirBodyPtr;
AX_DEFINE_HASHMAP(AxMirMap, AxHirItemPtr, AxMirBodyPtr, ax_key_hash_ptr, ax_key_eq_ptr);

// Interpreter state
typedef struct {
    AxHirItem *main_fn;
    AxThir *thir;
    const AxHir *hir;
    StrInterner *interner;
    const AxResolveMap *rmap;
    const AxAst *ast;
    AxDiagSink *sink;
    int step_limit;
    int call_depth_limit;
    void *mir_map;
    
    int steps;
    int call_depth;
    
    AxArena arena;
    bool failed;
    int exit_code;
    const char **out_panic_msg;
    FILE *out;
    uint64_t dummy_buf;
} InterpCtx;

typedef struct {
    uint64_t vals[8];
} AxInterpValue;

typedef struct {
    AxMirBody *body;
    AxInterpValue *locals;
} CallFrame;

static void panic_interp(InterpCtx *ctx, const char *msg);

static AxHirItem *find_func_by_symbol(InterpCtx *ctx, uint64_t sym_v) {
    if (sym_v == 0) return NULL;
    for (const AxHirItem *it = ctx->hir->items; it; it = it->next) {
        if (it->kind == AX_HIR_ITEM_FN && it->fn.symbol.v == (uint32_t)sym_v) {
            return (AxHirItem*)it;
        }
        if (it->kind == AX_HIR_ITEM_IMPL) {
            for (const AxHirItem *m = it->impl.members; m; m = m->next) {
                if (m->kind == AX_HIR_ITEM_FN && m->fn.symbol.v == (uint32_t)sym_v) {
                    return (AxHirItem*)m;
                }
            }
        }
        if (it->kind == AX_HIR_ITEM_TRAIT) {
            for (const AxHirItem *m = it->trait.members; m; m = m->next) {
                if (m->kind == AX_HIR_ITEM_FN && m->fn.symbol.v == (uint32_t)sym_v) {
                    return (AxHirItem*)m;
                }
            }
        }
    }

    StrId target_name = {0};
    for (const AxAstItem *it = ctx->ast->items; it; it = it->next) {
        AxSymbolId *it_sym = AxNodeMap_get(&ctx->rmap->node_map, it);
        if (it_sym && it_sym->v == (uint32_t)sym_v) {
            if (it->kind == AX_ITEM_FN) {
                target_name = it->fn.name;
            }
            break;
        }
        if (it->kind == AX_ITEM_IMPL) {
            for (const AxAstItem *m = it->impl.members; m; m = m->next) {
                AxSymbolId *m_sym = AxNodeMap_get(&ctx->rmap->node_map, m);
                if (m_sym && m_sym->v == (uint32_t)sym_v) {
                    if (m->kind == AX_ITEM_FN) {
                        target_name = m->fn.name;
                    }
                    break;
                }
            }
            if (target_name.v != 0) break;
        }
        if (it->kind == AX_ITEM_TRAIT) {
            for (const AxAstItem *m = it->trait.members; m; m = m->next) {
                AxSymbolId *m_sym = AxNodeMap_get(&ctx->rmap->node_map, m);
                if (m_sym && m_sym->v == (uint32_t)sym_v) {
                    if (m->kind == AX_ITEM_FN) {
                        target_name = m->fn.name;
                    }
                    break;
                }
            }
            if (target_name.v != 0) break;
        }
    }
    
    if (target_name.v == 0) {
        return NULL;
    }
    
    for (const AxHirItem *it = ctx->hir->items; it; it = it->next) {
        if (it->kind == AX_HIR_ITEM_FN && it->fn.name.v == target_name.v) {
            return (AxHirItem*)it;
        }
        if (it->kind == AX_HIR_ITEM_IMPL) {
            for (const AxHirItem *m = it->impl.members; m; m = m->next) {
                if (m->kind == AX_HIR_ITEM_FN && m->fn.name.v == target_name.v) {
                    return (AxHirItem*)m;
                }
            }
        }
        if (it->kind == AX_HIR_ITEM_TRAIT) {
            for (const AxHirItem *m = it->trait.members; m; m = m->next) {
                if (m->kind == AX_HIR_ITEM_FN && m->fn.name.v == target_name.v) {
                    return (AxHirItem*)m;
                }
            }
        }
    }
    return NULL;
}


static uint8_t* get_place_ptr(InterpCtx *ctx, CallFrame *frame, const AxMirPlace *place, TypeId *out_ty, uint64_t *out_fat_len) {
    if (place->local.v >= frame->body->local_count) {
        return NULL; // should ICE
    }
    
    uint8_t *ptr = (uint8_t*)&frame->locals[place->local.v];
    *out_ty = frame->body->locals[place->local.v].ty;
    uint32_t current_variant = (uint32_t)-1;
    uint64_t fat_len = 0;
    TypeId current_ty = *out_ty;
    if (out_fat_len) *out_fat_len = 0;
    for (size_t i = 0; i < place->proj_count; i++) {
        const AxMirProjection *proj = &place->projs[i];
        if (proj->kind == AX_MIR_PROJ_DEREF) {
            const AxType *ty = ax_type_get(&ctx->thir->interner, current_ty);
            if (ty->kind == AX_TY_VIEW || ty->kind == AX_TY_MUT_VIEW) {
                if (ax_type_get(&ctx->thir->interner, ty->view.pointee)->kind == AX_TY_SLICE) {
                    fat_len = *(uint64_t*)(ptr + 8);
                }
                current_ty = ty->view.pointee;
            } else if (ty->kind == AX_TY_STR) {
                fat_len = *(uint64_t*)(ptr + 8);
                current_ty = ctx->thir->interner.t_u8;
            } else {
                current_ty = ty->ptr.pointee;
            }
            ptr = (uint8_t*)(*(uintptr_t*)ptr);
        } else if (proj->kind == AX_MIR_PROJ_DOWNCAST) {
            current_variant = proj->variant_idx;
        } else if (proj->kind == AX_MIR_PROJ_FIELD) {
            uint32_t offset;
            const AxType *ty = ax_type_get(&ctx->thir->interner, current_ty);
            if (ty->kind == AX_TY_ENUM && current_variant != (uint32_t)-1) {
                offset = ax_type_enum_field_offset(current_ty, current_variant, proj->field_idx, &ctx->thir->interner);
                current_ty = ty->enm.variant_fields[current_variant][proj->field_idx];
                current_variant = (uint32_t)-1;
            } else {
                offset = ax_type_field_offset(current_ty, proj->field_idx, &ctx->thir->interner);
                if (ty->kind == AX_TY_STRUCT) {
                    current_ty = ty->strct.fields[proj->field_idx];
                } else if (ty->kind == AX_TY_TUPLE) {
                    current_ty = ty->tuple.fields[proj->field_idx];
                } else if (ty->kind == AX_TY_CLOSURE) {
                    current_ty = (proj->field_idx == 0) ? ctx->thir->interner.t_u64 : ty->closure.captures[proj->field_idx - 1].type;
                }
            }
            ptr += offset;
                } else if (proj->kind == AX_MIR_PROJ_SUB_SLICE) {
            const AxType *ty = ax_type_get(&ctx->thir->interner, current_ty);
            uint64_t len = 0;
            TypeId elem_ty;
            if (ty->kind == AX_TY_ARRAY) {
                len = ty->array.len;
                elem_ty = ty->array.elem;
            } else if (ty->kind == AX_TY_SLICE) {
                len = fat_len;
                elem_ty = ty->slice.elem;
            } else if (ty->kind == AX_TY_STR) {
                len = fat_len;
                elem_ty = ctx->thir->interner.t_u8;
            } else {
                panic_interp(ctx, "sub-slicing into non-array/slice");
                return (uint8_t*)&ctx->dummy_buf;
            }
            
            uint64_t start_idx = 0;
            if (proj->sub_slice.has_from) {
                uint8_t *idx_ptr = (uint8_t*)&frame->locals[proj->sub_slice.from_local.v];
                TypeId idx_ty = frame->body->locals[proj->sub_slice.from_local.v].ty;
                uint32_t idx_size = ax_type_size(idx_ty, &ctx->thir->interner);
                if (idx_size == 4) start_idx = *(uint32_t*)idx_ptr;
                else if (idx_size == 8) start_idx = *(uint64_t*)idx_ptr;
            }
            uint64_t end_idx = len;
            if (proj->sub_slice.has_to) {
                uint8_t *idx_ptr = (uint8_t*)&frame->locals[proj->sub_slice.to_local.v];
                TypeId idx_ty = frame->body->locals[proj->sub_slice.to_local.v].ty;
                uint32_t idx_size = ax_type_size(idx_ty, &ctx->thir->interner);
                if (idx_size == 4) end_idx = *(uint32_t*)idx_ptr;
                else if (idx_size == 8) end_idx = *(uint64_t*)idx_ptr;
            }
            if (start_idx > end_idx || end_idx > len) {
                panic_interp(ctx, "sub-slice out of bounds");
                return (uint8_t*)&ctx->dummy_buf;
            }
            fat_len = end_idx - start_idx;
            uint32_t elem_size = ax_type_size(elem_ty, &ctx->thir->interner);
            ptr += start_idx * elem_size;
            
            AxType sl; memset(&sl, 0, sizeof(sl));
            sl.kind = AX_TY_SLICE;
            sl.slice.elem = elem_ty;
            current_ty = ax_intern_type(&ctx->thir->interner, &sl);
        } else if (proj->kind == AX_MIR_PROJ_INDEX) {
            const AxType *ty = ax_type_get(&ctx->thir->interner, current_ty);
            uint64_t len = 0;
            TypeId elem_ty;
            if (ty->kind == AX_TY_ARRAY) {
                len = ty->array.len;
                elem_ty = ty->array.elem;
            } else if (ty->kind == AX_TY_SLICE) {
                len = fat_len;
                elem_ty = ty->slice.elem;
            } else if (ty->kind == AX_TY_STR) {
                len = fat_len;
                elem_ty = ctx->thir->interner.t_u8;
            } else {
                panic_interp(ctx, "indexing into non-array/slice");
                return (uint8_t*)&ctx->dummy_buf;
            }
            
            uint8_t *idx_ptr = (uint8_t*)&frame->locals[proj->index_local.v];
            TypeId idx_ty = frame->body->locals[proj->index_local.v].ty;
            uint32_t idx_size = ax_type_size(idx_ty, &ctx->thir->interner);
            uint64_t index = 0;
            if (idx_size == 4) index = *(uint32_t*)idx_ptr;
            else if (idx_size == 8) index = *(uint64_t*)idx_ptr;
            
            if (index >= len) {
                panic_interp(ctx, "index out of bounds");
                return (uint8_t*)&ctx->dummy_buf;
            }
            
            uint32_t elem_size = ax_type_size(elem_ty, &ctx->thir->interner);
            ptr += index * elem_size;
            current_ty = elem_ty;
        }
    }
    *out_ty = current_ty;
    if (out_fat_len) *out_fat_len = fat_len;
    return ptr;
}

static uint64_t eval_operand(InterpCtx *ctx, CallFrame *frame, const AxMirOperand *op) {
    if (op->kind == AX_MIR_OP_CONST) {
        return op->constant.val;
    } else {
        TypeId ty;
        uint8_t *ptr = get_place_ptr(ctx, frame, &op->place, &ty, NULL);
        uint32_t size = ax_type_size(ty, &ctx->thir->interner);
        uint64_t val = 0;
        if (size == 1) val = *(uint8_t*)ptr;
        else if (size == 2) val = *(uint16_t*)ptr;
        else if (size == 4) val = *(uint32_t*)ptr;
        else if (size >= 8) val = *(uint64_t*)ptr;
        else val = *(uint64_t*)ptr;
        return val;
    }
}



static void panic_interp(InterpCtx *ctx, const char *msg) {
    if (ctx->out_panic_msg) {
        *ctx->out_panic_msg = msg;
    }
    ctx->failed = true;
    ctx->exit_code = 101;
}

static void check_step_limit(InterpCtx *ctx) {
    if (ctx->step_limit > 0 && ctx->steps >= ctx->step_limit) {
        AxDiagnostic d = {0};
        d.code = AX_DRIVER_INTERP_STEP_LIMIT;
        d.severity = AX_DIAG_ERROR;
        d.message = "step limit exceeded";
        ax_diag_sink_report(ctx->sink, &d);
        ctx->failed = true;
        ctx->exit_code = 124;
    }
}



static void eval_call(InterpCtx *ctx, AxHirItem *func, AxInterpValue *args_raw, size_t arg_count, AxInterpValue *out_ret) {
    ctx->call_depth++;
    if (ctx->call_depth_limit > 0 && ctx->call_depth > ctx->call_depth_limit) {
        AxDiagnostic d = {0};
        d.code = AX_DRIVER_INTERP_STACK_LIMIT;
        d.severity = AX_DIAG_ERROR;
        d.message = "call depth limit exceeded";
        ax_diag_sink_report(ctx->sink, &d);
        ctx->failed = true;
        ctx->exit_code = 124;
        ctx->call_depth--;
        return;
    }
    
    bool is_intrinsic = false;
    uint64_t args[16] = {0};
    for (size_t i = 0; i < arg_count && i < 16; i++) {
        if (args_raw) args[i] = args_raw[i].vals[0];
    }
    for (AxHirAttr *attr = func->attrs; attr; attr = attr->next) {
        StrView an = ax_interner_get(ctx->interner, attr->name);
        if (ax_sv_eq_cstr(an, "intrinsic")) {
            is_intrinsic = true;
            break;
        }
    }

    if (is_intrinsic) {
        StrView name = ax_interner_get(ctx->interner, func->fn.name);
        if (ax_sv_eq_cstr(name, "assert")) {
            if (arg_count > 0 && args[0] == 0) {
                panic_interp(ctx, "assertion failed");
            }
            if (out_ret) out_ret->vals[0] = 0;
            return;
        } else if (ax_sv_eq_cstr(name, "unreachable")) {
            panic_interp(ctx, "entered unreachable code");
            return;
        } else if (ax_sv_eq_cstr(name, "panic")) {
            panic_interp(ctx, "panic");
            return;
        } else {
            TypeId *fn_ty_ptr = AxItemTypeMap_get(&ctx->thir->item_types, func);
            int bits = 64;
            if (fn_ty_ptr) {
                const AxType *fn_ty = ax_type_get(&ctx->thir->interner, *fn_ty_ptr);
                if (fn_ty->kind == AX_TY_FN && fn_ty->fn.ret_type.v != 0) {
                    // For intrinsics that return `u32` (like leading_zeros), the operand width is the parameter type.
                    const AxType *op_ty = ax_type_get(&ctx->thir->interner, fn_ty->fn.param_types[0]);
                    switch(op_ty->kind) {
                        case AX_TY_I8: case AX_TY_U8: bits = 8; break;
                        case AX_TY_I16: case AX_TY_U16: bits = 16; break;
                        case AX_TY_I32: case AX_TY_U32: bits = 32; break;
                        default: bits = 64; break;
                    }
                }
            }
            uint64_t mask = bits == 64 ? ~(uint64_t)0 : (((uint64_t)1 << bits) - 1);
            
            #define IS_OP(name, op) (name.len >= strlen(op) && memcmp(name.ptr, op, strlen(op)) == 0 && (name.len == strlen(op) || name.ptr[strlen(op)] == '_'))

            if (IS_OP(name, "wrapping_add")) {
                if (out_ret && arg_count == 2) {
                    out_ret->vals[0] = (args[0] + args[1]) & mask;
                    // printf("wrapping_add %llu + %llu = %llu\n", args[0], args[1], *out_ret);
                }
                return;
            } else if (IS_OP(name, "wrapping_sub")) {
                if (out_ret && arg_count == 2) out_ret->vals[0] = (args[0] - args[1]) & mask;
                return;
            } else if (IS_OP(name, "wrapping_mul")) {
                if (out_ret && arg_count == 2) out_ret->vals[0] = (args[0] * args[1]) & mask;
                return;
            } else if (IS_OP(name, "wrapping_neg")) {
                if (out_ret && arg_count == 1) out_ret->vals[0] = (0 - args[0]) & mask;
                return;
            } else if (IS_OP(name, "rotate_left")) {
                if (out_ret && arg_count == 2) {
                    uint32_t n = (uint32_t)args[1] % bits;
                    out_ret->vals[0] = ((args[0] << n) | (args[0] >> ((bits - n) % bits))) & mask;
                }
                return;
            } else if (IS_OP(name, "rotate_right")) {
                if (out_ret && arg_count == 2) {
                    uint32_t n = (uint32_t)args[1] % bits;
                    out_ret->vals[0] = ((args[0] >> n) | (args[0] << ((bits - n) % bits))) & mask;
                }
                return;
            } else if (IS_OP(name, "leading_zeros")) {
                if (out_ret && arg_count == 1) {
                    uint64_t val = args[0] & mask;
                    if (val == 0) out_ret->vals[0] = bits;
                    else {
                        uint32_t lz = 0;
                        for (int i = bits - 1; i >= 0; i--) {
                            if ((val >> i) & 1) break;
                            lz++;
                        }
                        out_ret->vals[0] = lz;
                    }
                }
                return;
            } else if (IS_OP(name, "trailing_zeros")) {
                if (out_ret && arg_count == 1) {
                    uint64_t val = args[0] & mask;
                    if (val == 0) out_ret->vals[0] = bits;
                    else {
                        uint32_t tz = 0;
                        for (int i = 0; i < bits; i++) {
                            if ((val >> i) & 1) break;
                            tz++;
                        }
                        out_ret->vals[0] = tz;
                    }
                }
                return;
            } else if (IS_OP(name, "count_ones")) {
                if (out_ret && arg_count == 1) {
                    uint64_t val = args[0] & mask;
                    uint32_t ones = 0;
                    for (int i = 0; i < bits; i++) {
                        if ((val >> i) & 1) ones++;
                    }
                    out_ret->vals[0] = ones;
                }
                return;
            }
            #undef IS_OP
        }
    }

    if (func->kind == AX_HIR_ITEM_FN && !func->fn.body && ctx->interner) {
        StrView fname = ax_interner_get(ctx->interner, func->fn.name);
        for (const AxHirItem *it = ctx->hir->items; it; it = it->next) {
            if (it->kind == AX_HIR_ITEM_IMPL) {
                for (const AxHirItem *m = it->impl.members; m; m = m->next) {
                    if (m->kind == AX_HIR_ITEM_FN && m->fn.body) {
                        StrView mname = ax_interner_get(ctx->interner, m->fn.name);
                        if (ax_sv_eq(fname, mname)) {
                            func = (AxHirItem*)m;
                            break;
                        }
                    }
                }
                if (func->fn.body) break;
            }
        }
    }

    AxMirBodyPtr *cached_body_ptr = AxMirMap_get((AxMirMap*)ctx->mir_map, func);
    if (!cached_body_ptr) {
        AX_ICE("interpreter: function has no verified MIR body");
    }
    AxMirBody *body = *cached_body_ptr;
    
    CallFrame frame;
    frame.body = body;
    frame.locals = calloc(body->local_count, sizeof(AxInterpValue));
    
    // args start at local 1
    for (size_t i = 0; i < arg_count; i++) {
        if (i + 1 < body->local_count) {
            frame.locals[i + 1] = args_raw[i];
        }
    }
    
    AxMirBbId current_bb = {0};
    
    while (!ctx->failed) {
        ctx->steps++;
        check_step_limit(ctx);
        if (ctx->failed) break;
        
        if (current_bb.v >= body->bb_count) {
            break;
        }
        
        AxMirBb *bb = &body->bbs[current_bb.v];
        
        for (size_t i = 0; i < bb->stmt_count; i++) {
            ctx->steps++;
            check_step_limit(ctx);
            if (ctx->failed) break;
            AxMirStmt *stmt = &bb->stmts[i];
            
            if (stmt->kind == AX_MIR_STMT_ASSIGN) {
                uint64_t val = 0;
                switch (stmt->assign.rvalue.kind) {
                    case AX_MIR_RVALUE_USE: {
                        TypeId dest_ty;
                        uint8_t *dest = get_place_ptr(ctx, &frame, &stmt->assign.place, &dest_ty, NULL);
                        if (stmt->assign.rvalue.use.kind == AX_MIR_OP_CONST) {
                            uint32_t size = ax_type_size(dest_ty, &ctx->thir->interner);
                            if (stmt->assign.rvalue.use.constant.ty.v != 0 && TypeId_eq(stmt->assign.rvalue.use.constant.ty, ctx->thir->interner.t_str)) {
                                *(const uint8_t**)dest = stmt->assign.rvalue.use.constant.str.bytes;
                                *(uint64_t*)(dest + 8) = stmt->assign.rvalue.use.constant.str.len;
                            } else {
                                uint64_t val = stmt->assign.rvalue.use.constant.val;
                                if (size == 1) *(uint8_t*)dest = (uint8_t)val;
                                else if (size == 2) *(uint16_t*)dest = (uint16_t)val;
                                else if (size == 4) *(uint32_t*)dest = (uint32_t)val;
                                else if (size == 8) *(uint64_t*)dest = val;
                            }
                        } else {
                            TypeId src_ty;
                            uint8_t *src = get_place_ptr(ctx, &frame, &stmt->assign.rvalue.use.place, &src_ty, NULL);
                            uint32_t size = ax_type_size(dest_ty, &ctx->thir->interner);
                            memcpy(dest, src, size);
                        }
                        goto skip_write;
                    }
                    case AX_MIR_RVALUE_DISCRIMINANT: {
                        TypeId src_ty;
                        uint8_t *src = get_place_ptr(ctx, &frame, &stmt->assign.rvalue.discriminant, &src_ty, NULL);
                        const AxType *ty = ax_type_get(&ctx->thir->interner, src_ty);
                        if (ty->kind == AX_TY_ENUM) {
                            val = *(uint32_t*)src;
                        } else {
                            AX_ICE("interpreter: discriminant on non-enum");
                        }
                        break;
                    }
                                        case AX_MIR_RVALUE_AGGREGATE: {
                        TypeId dest_ty;
                        uint8_t *dest = get_place_ptr(ctx, &frame, &stmt->assign.place, &dest_ty, NULL);
                        const AxType *ty = ax_type_get(&ctx->thir->interner, dest_ty);
                        
                        if (ty->kind == AX_TY_ENUM) {
                            *(uint32_t*)dest = stmt->assign.rvalue.aggregate.variant_idx;
                        }
                        
                        for (size_t i = 0; i < stmt->assign.rvalue.aggregate.operand_count; i++) {
                            uint32_t offset = 0;
                            TypeId field_ty = TypeId_none();
                            if (ty->kind == AX_TY_ARRAY) {
                                field_ty = ty->array.elem;
                                offset = i * ax_type_size(field_ty, &ctx->thir->interner);
                            } else if (ty->kind == AX_TY_ENUM) {
                                offset = ax_type_enum_field_offset(dest_ty, stmt->assign.rvalue.aggregate.variant_idx, i, &ctx->thir->interner);
                                field_ty = ty->enm.variant_fields[stmt->assign.rvalue.aggregate.variant_idx][i];
                            } else {
                                offset = ax_type_field_offset(dest_ty, i, &ctx->thir->interner);
                                if (ty->kind == AX_TY_STRUCT) {
                                    field_ty = ty->strct.fields[i];
                                } else if (ty->kind == AX_TY_TUPLE) {
                                    field_ty = ty->tuple.fields[i];
                                } else if (ty->kind == AX_TY_CLOSURE) {
                                    field_ty = (i == 0) ? ctx->thir->interner.t_u64 : ty->closure.captures[i - 1].type;
                                }
                            }
                            uint32_t f_size = ax_type_size(field_ty, &ctx->thir->interner);
                            
                            AxMirOperand *f_op = &stmt->assign.rvalue.aggregate.operands[i];
                            if (f_op->kind == AX_MIR_OP_CONST) {
                                uint64_t val = f_op->constant.val;
                                if (f_size == 1) *(uint8_t*)(dest + offset) = (uint8_t)val;
                                else if (f_size == 2) *(uint16_t*)(dest + offset) = (uint16_t)val;
                                else if (f_size == 4) *(uint32_t*)(dest + offset) = (uint32_t)val;
                                else if (f_size == 8) *(uint64_t*)(dest + offset) = val;
                            } else {
                                TypeId s_ty;
                                uint8_t *src = get_place_ptr(ctx, &frame, &f_op->place, &s_ty, NULL);
                                memcpy(dest + offset, src, f_size);
                            }
                        }
                        goto skip_write;
                    }
                    case AX_MIR_RVALUE_REPEAT: {
                        TypeId dest_ty;
                        uint8_t *dest = get_place_ptr(ctx, &frame, &stmt->assign.place, &dest_ty, NULL);
                        const AxType *ty = ax_type_get(&ctx->thir->interner, dest_ty);
                        
                        TypeId elem_ty = ty->array.elem;
                        uint32_t f_size = ax_type_size(elem_ty, &ctx->thir->interner);
                        
                        uint64_t count_val = 0;
                        if (stmt->assign.rvalue.repeat.count.kind == AX_MIR_OP_CONST) {
                            count_val = stmt->assign.rvalue.repeat.count.constant.val;
                        } else {
                            TypeId dummy;
                            uint8_t *c_ptr = get_place_ptr(ctx, &frame, &stmt->assign.rvalue.repeat.count.place, &dummy, NULL);
                            count_val = *(uint64_t*)c_ptr; // assuming usize or u32/u64
                        }
                        
                        AxMirOperand *val_op = &stmt->assign.rvalue.repeat.op;
                        for (uint64_t i = 0; i < count_val; i++) {
                            uint32_t offset = i * f_size;
                            if (val_op->kind == AX_MIR_OP_CONST) {
                                uint64_t val = val_op->constant.val;
                                if (f_size == 1) *(uint8_t*)(dest + offset) = (uint8_t)val;
                                else if (f_size == 2) *(uint16_t*)(dest + offset) = (uint16_t)val;
                                else if (f_size == 4) *(uint32_t*)(dest + offset) = (uint32_t)val;
                                else if (f_size == 8) *(uint64_t*)(dest + offset) = val;
                            } else {
                                TypeId s_ty;
                                uint8_t *src = get_place_ptr(ctx, &frame, &val_op->place, &s_ty, NULL);
                                memcpy(dest + offset, src, f_size);
                            }
                        }
                        goto skip_write;
                    }
                    case AX_MIR_RVALUE_REF: {
                        TypeId dest_ty;
                        uint8_t *dest = get_place_ptr(ctx, &frame, &stmt->assign.place, &dest_ty, NULL);
                        TypeId src_ty;
                        uint64_t src_fat_len = 0;
                        uint8_t *src = get_place_ptr(ctx, &frame, &stmt->assign.rvalue.ref.place, &src_ty, &src_fat_len);
                        const AxType *t = ax_type_get(&ctx->thir->interner, dest_ty);
                        if ((t->kind == AX_TY_VIEW || t->kind == AX_TY_MUT_VIEW) && ax_type_get(&ctx->thir->interner, t->view.pointee)->kind == AX_TY_SLICE) {
                            *(uint8_t**)dest = src;
                            const AxType *s_t = ax_type_get(&ctx->thir->interner, src_ty);
                            uint64_t len = 0;
                            if (s_t->kind == AX_TY_SLICE) {
                                len = src_fat_len;
                            } else if (s_t->kind == AX_TY_ARRAY) {
                                len = s_t->array.len;
                            } else if (s_t->kind == AX_TY_STR || ((s_t->kind == AX_TY_VIEW || s_t->kind == AX_TY_MUT_VIEW) && ax_type_get(&ctx->thir->interner, s_t->view.pointee)->kind == AX_TY_SLICE)) {
                                len = *(uint64_t*)(src + 8);
                                *(uint8_t**)dest = *(uint8_t**)src;
                            }
                            *(uint64_t*)(dest + 8) = len;
                        } else {
                            *(uint8_t**)dest = src;
                        }
                        goto skip_write;
                    }
                    case AX_MIR_RVALUE_LEN: {
                        TypeId dest_ty;
                        uint8_t *dest = get_place_ptr(ctx, &frame, &stmt->assign.place, &dest_ty, NULL);
                        
                        TypeId arg_ty;
                        get_place_ptr(ctx, &frame, &stmt->assign.rvalue.len, &arg_ty, NULL);
                        const AxType *t = ax_type_get(&ctx->thir->interner, arg_ty);
                        
                        uint64_t len = 0;
                        if (t->kind == AX_TY_ARRAY) {
                            len = t->array.len;
                        } else if (t->kind == AX_TY_STR || ((t->kind == AX_TY_VIEW || t->kind == AX_TY_MUT_VIEW) && ax_type_get(&ctx->thir->interner, t->view.pointee)->kind == AX_TY_SLICE)) {
                            uint8_t *ptr = get_place_ptr(ctx, &frame, &stmt->assign.rvalue.len, &arg_ty, NULL);
                            len = *(uint64_t*)(ptr + 8);
                        } else {
                            len = 0; // ICE
                        }
                        
                        uint32_t d_size = ax_type_size(dest_ty, &ctx->thir->interner);
                        if (d_size == 4) *(uint32_t*)dest = (uint32_t)len;
                        else if (d_size == 8) *(uint64_t*)dest = len;
                        goto skip_write;
                    }
                    case AX_MIR_RVALUE_BINARY_OP:
                    case AX_MIR_RVALUE_OVERFLOWS_BINARY_OP: {
                        uint64_t lhs = eval_operand(ctx, &frame, &stmt->assign.rvalue.binary_op.lhs);
                        uint64_t rhs = eval_operand(ctx, &frame, &stmt->assign.rvalue.binary_op.rhs);
                        AxMirBinOp op = stmt->assign.rvalue.binary_op.op;
                        
                        TypeId ty = {0};
                        if (stmt->assign.rvalue.binary_op.lhs.kind == AX_MIR_OP_CONST) {
                            ty = stmt->assign.rvalue.binary_op.lhs.constant.ty;
                        } else {
                            AxMirLocalId loc = stmt->assign.rvalue.binary_op.lhs.place.local;
                            ty = frame.body->locals[loc.v].ty;
                        }
                        if (ty.v == 0) {
                            if (stmt->assign.rvalue.binary_op.rhs.kind == AX_MIR_OP_CONST) {
                                ty = stmt->assign.rvalue.binary_op.rhs.constant.ty;
                            } else {
                                AxMirLocalId loc = stmt->assign.rvalue.binary_op.rhs.place.local;
                                ty = frame.body->locals[loc.v].ty;
                            }
                        }
                        const AxType *t = NULL;
                        if (ty.v != 0) {
                            t = ax_type_get(&ctx->thir->interner, ty);
                        }
                        
                        bool is_signed = true;
                        int bits = 32;
                        if (t) {
                            switch (t->kind) {
                                case AX_TY_I8: is_signed = true; bits = 8; break;
                                case AX_TY_I16: is_signed = true; bits = 16; break;
                                case AX_TY_I32: is_signed = true; bits = 32; break;
                                case AX_TY_I64: is_signed = true; bits = 64; break;
                                case AX_TY_ISIZE: is_signed = true; bits = 64; break;
                                case AX_TY_U8: is_signed = false; bits = 8; break;
                                case AX_TY_U16: is_signed = false; bits = 16; break;
                                case AX_TY_U32: is_signed = false; bits = 32; break;
                                case AX_TY_U64: is_signed = false; bits = 64; break;
                                case AX_TY_USIZE: is_signed = false; bits = 64; break;
                                case AX_TY_BOOL: is_signed = false; bits = 1; break;
                                default: break;
                            }
                        }
                        
                        uint64_t res = 0;
                        bool overflow = false;
                        if (is_signed) {
                            int64_t a = 0;
                            int64_t b = 0;
                            
                            if (stmt->assign.rvalue.binary_op.lhs.kind == AX_MIR_OP_CONST) {
                                a = (int64_t)stmt->assign.rvalue.binary_op.lhs.constant.val;
                            } else {
                                if (bits == 8) a = (int8_t)lhs;
                                else if (bits == 16) a = (int16_t)lhs;
                                else if (bits == 32) a = (int32_t)lhs;
                                else a = (int64_t)lhs;
                            }
                            
                            if (stmt->assign.rvalue.binary_op.rhs.kind == AX_MIR_OP_CONST) {
                                b = (int64_t)stmt->assign.rvalue.binary_op.rhs.constant.val;
                            } else {
                                if (bits == 8) b = (int8_t)rhs;
                                else if (bits == 16) b = (int16_t)rhs;
                                else if (bits == 32) b = (int32_t)rhs;
                                else b = (int64_t)rhs;
                            }
                    
                            int64_t r = 0;
                            switch (op) {
                                case AX_MIR_BINOP_ADD: overflow = __builtin_add_overflow(a, b, &r); break;
                                case AX_MIR_BINOP_SUB: overflow = __builtin_sub_overflow(a, b, &r); break;
                                case AX_MIR_BINOP_MUL: overflow = __builtin_mul_overflow(a, b, &r); break;
                                case AX_MIR_BINOP_DIV:
                                    if (b == 0) { panic_interp(ctx, "division by zero"); }
                                    else if (b == -1 && bits == 64 && a == (-9223372036854775807LL - 1)) { overflow = true; r = a; }
                                    else if (b == -1 && bits < 64 && a == -((int64_t)1 << (bits - 1))) { overflow = true; r = a; }
                                    else {
                                        uint64_t ua = a < 0 ? (uint64_t)(-(a + 1)) + 1 : (uint64_t)a;
                                        uint64_t ub = b < 0 ? (uint64_t)(-(b + 1)) + 1 : (uint64_t)b;
                                        r = (int64_t)(ua / ub);
                                        if ((a < 0) != (b < 0) && r != 0) r = -r;
                                    }
                                    break;
                                case AX_MIR_BINOP_REM:
                                    if (b == 0) { panic_interp(ctx, "division by zero"); }
                                    else if (b == -1 && bits == 64 && a == (-9223372036854775807LL - 1)) { overflow = true; r = 0; }
                                    else if (b == -1 && bits < 64 && a == -((int64_t)1 << (bits - 1))) { overflow = true; r = 0; }
                                    else {
                                        uint64_t ua = a < 0 ? (uint64_t)(-(a + 1)) + 1 : (uint64_t)a;
                                        uint64_t ub = b < 0 ? (uint64_t)(-(b + 1)) + 1 : (uint64_t)b;
                                        r = (int64_t)(ua % ub);
                                        if (a < 0 && r != 0) r = -r;
                                    }
                                    break;
                                case AX_MIR_BINOP_EQ: r = (a == b); break;
                                case AX_MIR_BINOP_NE: r = (a != b); break;
                                case AX_MIR_BINOP_LT: r = (a < b); break;
                                case AX_MIR_BINOP_LE: r = (a <= b); break;
                                case AX_MIR_BINOP_GT: r = (a > b); break;
                                case AX_MIR_BINOP_GE: r = (a >= b); break;
                                case AX_MIR_BINOP_SHL:
                                    if (b < 0 || b >= bits) { overflow = true; break; }
                                    r = (int64_t)((uint64_t)a << b);
                                    break;
                                case AX_MIR_BINOP_SHR:
                                    if (b < 0 || b >= bits) { overflow = true; break; }
                                    if (a < 0) {
                                        uint64_t ua = (uint64_t)a;
                                        ua >>= b;
                                        uint64_t sign_ext = ~(((uint64_t)1 << (64 - b)) - 1);
                                        r = (int64_t)(ua | sign_ext);
                                    } else {
                                        r = a >> b;
                                    }
                                    break;
                                case AX_MIR_BINOP_BIT_AND: r = a & b; break;
                                case AX_MIR_BINOP_BIT_OR: r = a | b; break;
                                case AX_MIR_BINOP_BIT_XOR: r = a ^ b; break;
                                default: AX_ICE("interpreter: unknown binary operator"); break;
                            }
                    
                            if (op == AX_MIR_BINOP_ADD || op == AX_MIR_BINOP_SUB || op == AX_MIR_BINOP_MUL) {
                                if (bits < 64) {
                                    int64_t min_val = -((int64_t)1 << (bits - 1));
                                    int64_t max_val = ((int64_t)1 << (bits - 1)) - 1;
                                    if (r < min_val || r > max_val) overflow = true;
                                }
                            }
                            
                            if (bits < 64) {
                                uint64_t mask = ((uint64_t)1 << bits) - 1;
                                res = (uint64_t)r & mask;
                            } else {
                                res = (uint64_t)r;
                            }
                        } else {
                            uint64_t a = 0;
                            uint64_t b = 0;
                            if (bits == 8) { a = (uint8_t)lhs; b = (uint8_t)rhs; }
                            else if (bits == 16) { a = (uint16_t)lhs; b = (uint16_t)rhs; }
                            else if (bits == 32) { a = (uint32_t)lhs; b = (uint32_t)rhs; }
                            else { a = (uint64_t)lhs; b = (uint64_t)rhs; }
                    
                            uint64_t r = 0;
                            switch (op) {
                                case AX_MIR_BINOP_ADD: overflow = __builtin_add_overflow(a, b, &r); break;
                                case AX_MIR_BINOP_SUB: overflow = __builtin_sub_overflow(a, b, &r); break;
                                case AX_MIR_BINOP_MUL: overflow = __builtin_mul_overflow(a, b, &r); break;
                                case AX_MIR_BINOP_DIV:
                                    if (b == 0) { panic_interp(ctx, "division by zero"); }
                                    else { r = a / b; }
                                    break;
                                case AX_MIR_BINOP_REM:
                                    if (b == 0) { panic_interp(ctx, "division by zero"); }
                                    else { r = a % b; }
                                    break;
                                case AX_MIR_BINOP_EQ: r = (a == b); break;
                                case AX_MIR_BINOP_NE: r = (a != b); break;
                                case AX_MIR_BINOP_LT: r = (a < b); break;
                                case AX_MIR_BINOP_LE: r = (a <= b); break;
                                case AX_MIR_BINOP_GT: r = (a > b); break;
                                case AX_MIR_BINOP_GE: r = (a >= b); break;
                                case AX_MIR_BINOP_SHL:
                                    if (b >= (uint64_t)bits) { overflow = true; break; }
                                    r = a << b;
                                    break;
                                case AX_MIR_BINOP_SHR:
                                    if (b >= (uint64_t)bits) { overflow = true; break; }
                                    r = a >> b;
                                    break;
                                case AX_MIR_BINOP_BIT_AND: r = a & b; break;
                                case AX_MIR_BINOP_BIT_OR: r = a | b; break;
                                case AX_MIR_BINOP_BIT_XOR: r = a ^ b; break;
                                default: AX_ICE("interpreter: unknown binary operator"); break;
                            }
                    
                            if (op == AX_MIR_BINOP_ADD || op == AX_MIR_BINOP_SUB || op == AX_MIR_BINOP_MUL) {
                                if (bits < 64) {
                                    uint64_t max_val = ((uint64_t)1 << bits) - 1;
                                    if (r > max_val) overflow = true;
                                }
                            }
                            
                            if (bits < 64) {
                                uint64_t mask = ((uint64_t)1 << bits) - 1;
                                res = r & mask;
                            } else {
                                res = r;
                            }
                        }
                        
                        if (ctx->failed) break;

                        if (stmt->assign.rvalue.kind == AX_MIR_RVALUE_BINARY_OP) {
                            if (overflow) {
                                if (op == AX_MIR_BINOP_SHL || op == AX_MIR_BINOP_SHR) {
                                    panic_interp(ctx, "shift amount out of range");
                                } else if (op == AX_MIR_BINOP_ADD || op == AX_MIR_BINOP_SUB || op == AX_MIR_BINOP_MUL || op == AX_MIR_BINOP_DIV || op == AX_MIR_BINOP_REM) {
                                    panic_interp(ctx, "arithmetic overflow");
                                }
                            }
                            val = res;
                        } else {
                            val = overflow ? 1 : 0;
                        }
                        break;
                    }
                    case AX_MIR_RVALUE_UNARY_OP: {
                        uint64_t op_val = eval_operand(ctx, &frame, &stmt->assign.rvalue.unary_op.operand);
                        
                        TypeId ty = {0};
                        if (stmt->assign.rvalue.unary_op.operand.kind == AX_MIR_OP_CONST) {
                            ty = stmt->assign.rvalue.unary_op.operand.constant.ty;
                        } else {
                            AxMirLocalId loc = stmt->assign.rvalue.unary_op.operand.place.local;
                            ty = frame.body->locals[loc.v].ty;
                        }
                        const AxType *t = NULL;
                        if (ty.v != 0) {
                            t = ax_type_get(&ctx->thir->interner, ty);
                        }
                        bool is_signed = true;
                        int bits = 32;
                        if (t) {
                            switch (t->kind) {
                                case AX_TY_I8: is_signed = true; bits = 8; break;
                                case AX_TY_I16: is_signed = true; bits = 16; break;
                                case AX_TY_I32: is_signed = true; bits = 32; break;
                                case AX_TY_I64: is_signed = true; bits = 64; break;
                                case AX_TY_ISIZE: is_signed = true; bits = 64; break;
                                case AX_TY_U8: is_signed = false; bits = 8; break;
                                case AX_TY_U16: is_signed = false; bits = 16; break;
                                case AX_TY_U32: is_signed = false; bits = 32; break;
                                case AX_TY_U64: is_signed = false; bits = 64; break;
                                case AX_TY_USIZE: is_signed = false; bits = 64; break;
                                case AX_TY_BOOL: is_signed = false; bits = 1; break;
                                default: break;
                            }
                        }
                        
                        if (stmt->assign.rvalue.unary_op.op == AX_MIR_UNOP_NOT) {
                            val = (op_val == 0);
                        } else if (stmt->assign.rvalue.unary_op.op == AX_MIR_UNOP_BITNOT) {
                            val = ~op_val;
                            if (bits < 64) val &= ((uint64_t)1 << bits) - 1;
                        } else if (stmt->assign.rvalue.unary_op.op == AX_MIR_UNOP_NEG) {
                            if (is_signed) {
                                int64_t s_val = 0;
                                if (stmt->assign.rvalue.unary_op.operand.kind == AX_MIR_OP_CONST) {
                                    s_val = (int64_t)op_val;
                                } else {
                                    if (bits == 8) s_val = (int8_t)op_val;
                                    else if (bits == 16) s_val = (int16_t)op_val;
                                    else if (bits == 32) s_val = (int32_t)op_val;
                                    else s_val = (int64_t)op_val;
                                }
                                
                                int64_t min_val = bits == 64 ? (-9223372036854775807LL - 1) : -((int64_t)1 << (bits - 1));
                                if (s_val == min_val) {
                                    panic_interp(ctx, "arithmetic overflow");
                                } else {
                                    int64_t r = -s_val;
                                    val = (uint64_t)r;
                                    if (bits < 64) val &= ((uint64_t)1 << bits) - 1;
                                }
                            } else {
                                uint64_t mask = bits == 64 ? ~(uint64_t)0 : (((uint64_t)1 << bits) - 1);
                                if ((op_val & mask) != 0) {
                                    panic_interp(ctx, "arithmetic overflow");
                                } else {
                                    val = 0;
                                }
                            }
                        } else {
                            AX_ICE("interpreter: unknown unary operator");
                        }
                        break;
                    }
                    case AX_MIR_RVALUE_CAST: {
                        uint64_t op_val = eval_operand(ctx, &frame, &stmt->assign.rvalue.cast.op);
                        
                        TypeId src_ty = {0};
                        if (stmt->assign.rvalue.cast.op.kind == AX_MIR_OP_CONST) {
                            src_ty = stmt->assign.rvalue.cast.op.constant.ty;
                        } else {
                            AxMirLocalId loc = stmt->assign.rvalue.cast.op.place.local;
                            src_ty = frame.body->locals[loc.v].ty;
                        }
                        TypeId dest_ty = stmt->assign.rvalue.cast.ty;
                        
                        const AxType *s_t = NULL;
                        if (src_ty.v != 0) s_t = ax_type_get(&ctx->thir->interner, src_ty);
                        const AxType *d_t = NULL;
                        if (dest_ty.v != 0) d_t = ax_type_get(&ctx->thir->interner, dest_ty);
                        
                        bool src_signed = false;
                        int src_bits = 64;
                        if (s_t) {
                            switch (s_t->kind) {
                                case AX_TY_I8: src_signed = true; src_bits = 8; break;
                                case AX_TY_I16: src_signed = true; src_bits = 16; break;
                                case AX_TY_I32: src_signed = true; src_bits = 32; break;
                                case AX_TY_I64: case AX_TY_ISIZE: src_signed = true; src_bits = 64; break;
                                case AX_TY_U8: src_signed = false; src_bits = 8; break;
                                case AX_TY_U16: src_signed = false; src_bits = 16; break;
                                case AX_TY_U32: case AX_TY_CHAR: src_signed = false; src_bits = 32; break;
                                case AX_TY_U64: case AX_TY_USIZE: src_signed = false; src_bits = 64; break;
                                case AX_TY_BOOL: src_signed = false; src_bits = 1; break;
                                default: break;
                            }
                        }
                        
                        int dest_bits = 64;
                        if (d_t) {
                            switch (d_t->kind) {
                                case AX_TY_I8: case AX_TY_U8: dest_bits = 8; break;
                                case AX_TY_I16: case AX_TY_U16: dest_bits = 16; break;
                                case AX_TY_I32: case AX_TY_U32: case AX_TY_CHAR: dest_bits = 32; break;
                                default: dest_bits = 64; break;
                            }
                        }
                        
                        uint64_t res = op_val;
                        // 1. Sign extend if needed
                        if (src_signed && src_bits < 64) {
                            uint64_t sign_bit = (uint64_t)1 << (src_bits - 1);
                            if (res & sign_bit) {
                                uint64_t mask = ~(((uint64_t)1 << src_bits) - 1);
                                res |= mask;
                            }
                        }
                        
                        // 2. Truncate to dest
                        if (dest_bits < 64) {
                            res &= (((uint64_t)1 << dest_bits) - 1);
                        }
                        val = res;
                        break;
                    }
                    default:
                        val = 0;
                        break;
                }
                if (ctx->failed) break;
                TypeId dest_ty;
                uint8_t *dest = get_place_ptr(ctx, &frame, &stmt->assign.place, &dest_ty, NULL);
                uint32_t dest_size = ax_type_size(dest_ty, &ctx->thir->interner);
                if (dest_size == 1) *(uint8_t*)dest = (uint8_t)val;
                else if (dest_size == 2) *(uint16_t*)dest = (uint16_t)val;
                else if (dest_size == 4) *(uint32_t*)dest = (uint32_t)val;
                else if (dest_size == 8) *(uint64_t*)dest = val;
skip_write:;
            }
        }
        
        if (ctx->failed) break;
        
        AxMirTerminator *term = &bb->terminator;
        if (term->kind == AX_MIR_TERM_GOTO) {
            current_bb = term->goto_target;
        } else if (term->kind == AX_MIR_TERM_ASSERT) {
            uint64_t cond = eval_operand(ctx, &frame, &term->assert.cond);
            bool expected = term->assert.expected;
            if ((cond != 0) != expected) {
                if (term->assert.msg) {
                    panic_interp(ctx, term->assert.msg);
                } else {
                    panic_interp(ctx, "assertion failed");
                }
                break;
            }
            current_bb = term->assert.target;
        } else if (term->kind == AX_MIR_TERM_RETURN) {
            break;
                } else if (term->kind == AX_MIR_TERM_DROP) { AX_ICE("AX_MIR_TERM_DROP should have been elaborated away"); }
 else if (term->kind == AX_MIR_TERM_SWITCH_INT) {
            uint64_t discr = eval_operand(ctx, &frame, &term->switch_int.discr);
            AxMirBbId next = term->switch_int.targets.otherwise;
            for (size_t i = 0; i < term->switch_int.targets.count; i++) {
                if (discr == term->switch_int.targets.values[i].value) {
                    next = term->switch_int.targets.values[i].target;
                    break;
                }
            }
            current_bb = next;
        } else if (term->kind == AX_MIR_TERM_CALL) {
            if (term->call.func.kind == AX_MIR_OP_CONST) {
                const AxType *ft = ax_type_get(&ctx->thir->interner, term->call.func.constant.ty);
                if (ft->kind == AX_TY_BUILTIN_PRINT) {
                    const uint8_t *bytes = NULL;
                    size_t len = 0;
                    if (term->call.args[0].kind == AX_MIR_OP_CONST) {
                        bytes = term->call.args[0].constant.str.bytes;
                        len = term->call.args[0].constant.str.len;
                    } else {
                        TypeId ty;
                        uint8_t *ptr = get_place_ptr(ctx, &frame, &term->call.args[0].place, &ty, NULL);
                        bytes = *(const uint8_t**)ptr;
                        len = *(uint64_t*)(ptr + 8);
                    }
                    fwrite(bytes, 1, len, ctx->out);
                    current_bb = term->call.target;
                    continue;
                }
                if (ft->kind == AX_TY_BUILTIN_PRINT_INT) {
                    uint64_t val = eval_operand(ctx, &frame, &term->call.args[0]);
                    TypeId arg_ty_id;
                    if (term->call.args[0].kind == AX_MIR_OP_CONST) {
                        arg_ty_id = term->call.args[0].constant.ty;
                    } else {
                        get_place_ptr(ctx, &frame, &term->call.args[0].place, &arg_ty_id, NULL);
                    }
                    if (ax_type_is_signed(arg_ty_id, &ctx->thir->interner)) {
                        uint32_t size = ax_type_size(arg_ty_id, &ctx->thir->interner);
                        int64_t sval = val;
                        if (size == 1) sval = (int8_t)val;
                        else if (size == 2) sval = (int16_t)val;
                        else if (size == 4) sval = (int32_t)val;
                        fprintf(ctx->out, "%lld", (long long)sval);
                    } else {
                        fprintf(ctx->out, "%llu", (unsigned long long)val);
                    }
                    current_bb = term->call.target;
                    continue;
                }
            }
            uint64_t func_val = eval_operand(ctx, &frame, &term->call.func);
            AxHirItem *callee = find_func_by_symbol(ctx, func_val);
            if (!callee) {
                panic_interp(ctx, "unresolved function call");
                break;
            }
            
            size_t callee_param_count = 0;
            for (const AxHirParam *p = callee->fn.params; p; p = p->next) callee_param_count++;
            
            size_t total_args = callee_param_count > term->call.arg_count ? callee_param_count : term->call.arg_count;
            size_t cap_count = callee_param_count > term->call.arg_count ? (callee_param_count - term->call.arg_count) : 0;
            
            AxInterpValue *call_args = calloc(total_args ? total_args : 1, sizeof(AxInterpValue));
            
            if (cap_count > 0 && term->call.func.kind != AX_MIR_OP_CONST) {
                TypeId func_ty;
                uint8_t *closure_ptr = get_place_ptr(ctx, &frame, &term->call.func.place, &func_ty, NULL);
                uint32_t offset = 8;
                const AxHirParam *cp = callee->fn.params;
                for (size_t c = 0; c < cap_count && cp; c++, cp = cp->next) {
                    const TypeId *pty = AxParamTypeMap_get(&ctx->thir->param_types, cp);
                    TypeId cap_field_ty = pty ? *pty : ctx->thir->interner.t_u64;
                    uint32_t a = ax_type_align(cap_field_ty, &ctx->thir->interner);
                    uint32_t s = ax_type_size(cap_field_ty, &ctx->thir->interner);
                    if (a > 0) offset = (offset + a - 1) & ~(a - 1);
                    memcpy(&call_args[c], closure_ptr + offset, s ? s : 8);
                    offset += (s ? s : 8);
                }
            }
            
            for (size_t i = 0; i < term->call.arg_count; i++) {
                if (term->call.args[i].kind == AX_MIR_OP_CONST) {
                    call_args[cap_count + i].vals[0] = term->call.args[i].constant.val;
                } else {
                    TypeId src_ty;
                    uint8_t* src = get_place_ptr(ctx, &frame, &term->call.args[i].place, &src_ty, NULL);
                    memcpy(&call_args[cap_count + i], src, ax_type_size(src_ty, &ctx->thir->interner));
                }
            }
            
            AxInterpValue ret_val = {0};
            eval_call(ctx, callee, call_args, total_args, &ret_val);
            free(call_args);
            
            if (ctx->failed) break;
            
            TypeId dest_ty; uint8_t* dest = get_place_ptr(ctx, &frame, &term->call.destination, &dest_ty, NULL); memcpy(dest, &ret_val, ax_type_size(dest_ty, &ctx->thir->interner));
            current_bb = term->call.target;
        } else {
            panic_interp(ctx, "unsupported terminator");
            break;
        }
    }
    
    if (out_ret) *out_ret = frame.locals[0];
    free(frame.locals);
    ctx->call_depth--;
}

int ax_interp_run(AxHirItem *main_fn, AxThir *thir, const AxHir *hir, StrInterner *interner, const AxResolveMap *rmap, const AxAst *ast, AxDiagSink *sink, int step_limit, int call_depth_limit, void *mir_map, const char **out_panic_msg, FILE *out) {
    InterpCtx ctx = {0};
    ctx.main_fn = main_fn;
    ctx.thir = thir;
    ctx.hir = hir;
    ctx.interner = interner;
    ctx.rmap = rmap;
    ctx.ast = ast;
    ctx.sink = sink;
    ctx.step_limit = step_limit;
    ctx.call_depth_limit = call_depth_limit;
    ctx.mir_map = mir_map;
    ctx.out_panic_msg = out_panic_msg;
    ctx.out = out;
    ax_arena_init(&ctx.arena, 0);
    
    AxInterpValue ret = {0};
    eval_call(&ctx, main_fn, NULL, 0, &ret);
    
    ax_arena_destroy(&ctx.arena);
    
    if (ctx.failed) {
        return ctx.exit_code;
    }
    return (int)ret.vals[0];
}
