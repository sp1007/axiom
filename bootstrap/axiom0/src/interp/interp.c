#include "interp/interp.h"
#include "mir/build/build.h"
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
} InterpCtx;

typedef struct {
    uint64_t v; // Simple representation for integer/bool
} AxInterpValue;

typedef struct {
    AxMirBody *body;
    AxInterpValue *locals;
} CallFrame;

static AxHirItem *find_func_by_symbol(InterpCtx *ctx, uint64_t sym_v) {
    if (sym_v == 0) return NULL;
    
    StrId target_name = {0};
    for (const AxAstItem *it = ctx->ast->items; it; it = it->next) {
        AxSymbolId *it_sym = AxNodeMap_get(&ctx->rmap->node_map, it);
        if (it_sym && it_sym->v == (uint32_t)sym_v) {
            if (it->kind == AX_ITEM_FN) {
                target_name = it->fn.name;
            }
            break;
        }
    }
    
    if (target_name.v == 0) {
        return NULL;
    }
    
    for (const AxHirItem *it = ctx->hir->items; it; it = it->next) {
        if (it->kind == AX_HIR_ITEM_FN && it->fn.name.v == target_name.v) {
            return (AxHirItem*)it;
        }
    }
    return NULL;
}

static uint64_t eval_operand(CallFrame *frame, const AxMirOperand *op) {
    if (op->kind == AX_MIR_OP_CONST) {
        if (op->constant.ty.v != 0 && frame->body) {
            // How do we know it's bool? We don't easily have interner here, but we can print all constants!
        }
        return op->constant.val;
    } else {
        AxMirLocalId loc = op->place.local;
        return frame->locals[loc.v].v;
    }
}

static void write_place(CallFrame *frame, const AxMirPlace *place, uint64_t val) {
    AxMirLocalId loc = place->local;
    frame->locals[loc.v].v = val;
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

static void eval_call(InterpCtx *ctx, AxHirItem *func, uint64_t *args, size_t arg_count, uint64_t *out_ret) {
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
            if (out_ret) *out_ret = 0;
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
                    *out_ret = (args[0] + args[1]) & mask;
                    // printf("wrapping_add %llu + %llu = %llu\n", args[0], args[1], *out_ret);
                }
                return;
            } else if (IS_OP(name, "wrapping_sub")) {
                if (out_ret && arg_count == 2) *out_ret = (args[0] - args[1]) & mask;
                return;
            } else if (IS_OP(name, "wrapping_mul")) {
                if (out_ret && arg_count == 2) *out_ret = (args[0] * args[1]) & mask;
                return;
            } else if (IS_OP(name, "wrapping_neg")) {
                if (out_ret && arg_count == 1) *out_ret = (0 - args[0]) & mask;
                return;
            } else if (IS_OP(name, "rotate_left")) {
                if (out_ret && arg_count == 2) {
                    uint32_t n = (uint32_t)args[1] % bits;
                    *out_ret = ((args[0] << n) | (args[0] >> ((bits - n) % bits))) & mask;
                }
                return;
            } else if (IS_OP(name, "rotate_right")) {
                if (out_ret && arg_count == 2) {
                    uint32_t n = (uint32_t)args[1] % bits;
                    *out_ret = ((args[0] >> n) | (args[0] << ((bits - n) % bits))) & mask;
                }
                return;
            } else if (IS_OP(name, "leading_zeros")) {
                if (out_ret && arg_count == 1) {
                    uint64_t val = args[0] & mask;
                    if (val == 0) *out_ret = bits;
                    else {
                        uint32_t lz = 0;
                        for (int i = bits - 1; i >= 0; i--) {
                            if ((val >> i) & 1) break;
                            lz++;
                        }
                        *out_ret = lz;
                    }
                }
                return;
            } else if (IS_OP(name, "trailing_zeros")) {
                if (out_ret && arg_count == 1) {
                    uint64_t val = args[0] & mask;
                    if (val == 0) *out_ret = bits;
                    else {
                        uint32_t tz = 0;
                        for (int i = 0; i < bits; i++) {
                            if ((val >> i) & 1) break;
                            tz++;
                        }
                        *out_ret = tz;
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
                    *out_ret = ones;
                }
                return;
            }
            #undef IS_OP
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
            frame.locals[i + 1].v = args[i];
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
                    case AX_MIR_RVALUE_USE:
                        val = eval_operand(&frame, &stmt->assign.rvalue.use);
                        break;
                    case AX_MIR_RVALUE_BINARY_OP:
                    case AX_MIR_RVALUE_OVERFLOWS_BINARY_OP: {
                        uint64_t lhs = eval_operand(&frame, &stmt->assign.rvalue.binary_op.lhs);
                        uint64_t rhs = eval_operand(&frame, &stmt->assign.rvalue.binary_op.rhs);
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
                        uint64_t op_val = eval_operand(&frame, &stmt->assign.rvalue.unary_op.operand);
                        
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
                        uint64_t op_val = eval_operand(&frame, &stmt->assign.rvalue.cast.op);
                        
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
                write_place(&frame, &stmt->assign.place, val);
            }
        }
        
        if (ctx->failed) break;
        
        AxMirTerminator *term = &bb->terminator;
        if (term->kind == AX_MIR_TERM_GOTO) {
            current_bb = term->goto_target;
        } else if (term->kind == AX_MIR_TERM_ASSERT) {
            uint64_t cond = eval_operand(&frame, &term->assert.cond);
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
        } else if (term->kind == AX_MIR_TERM_SWITCH_INT) {
            uint64_t discr = eval_operand(&frame, &term->switch_int.discr);
            AxMirBbId next = term->switch_int.targets.otherwise;
            for (size_t i = 0; i < term->switch_int.targets.count; i++) {
                if (discr == term->switch_int.targets.values[i].value) {
                    next = term->switch_int.targets.values[i].target;
                    break;
                }
            }
            current_bb = next;
        } else if (term->kind == AX_MIR_TERM_CALL) {
            uint64_t func_val = eval_operand(&frame, &term->call.func);
            AxHirItem *callee = find_func_by_symbol(ctx, func_val);
            if (!callee) {
                panic_interp(ctx, "unresolved function call");
                break;
            }
            
            uint64_t *call_args = calloc(term->call.arg_count, sizeof(uint64_t));
            for (size_t i = 0; i < term->call.arg_count; i++) {
                call_args[i] = eval_operand(&frame, &term->call.args[i]);
            }
            
            uint64_t ret_val = 0;
            eval_call(ctx, callee, call_args, term->call.arg_count, &ret_val);
            free(call_args);
            
            if (ctx->failed) break;
            
            write_place(&frame, &term->call.destination, ret_val);
            current_bb = term->call.target;
        } else {
            panic_interp(ctx, "unsupported terminator");
            break;
        }
    }
    
    *out_ret = frame.locals[0].v;
    free(frame.locals);
    ctx->call_depth--;
}

int ax_interp_run(AxHirItem *main_fn, AxThir *thir, const AxHir *hir, StrInterner *interner, const AxResolveMap *rmap, const AxAst *ast, AxDiagSink *sink, int step_limit, int call_depth_limit, void *mir_map, const char **out_panic_msg) {
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
    ax_arena_init(&ctx.arena, 0);
    
    uint64_t ret = 0;
    eval_call(&ctx, main_fn, NULL, 0, &ret);
    
    ax_arena_destroy(&ctx.arena);
    
    if (ctx.failed) {
        return ctx.exit_code;
    }
    return (int)ret;
}
