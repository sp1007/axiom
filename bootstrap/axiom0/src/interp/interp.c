#include "interp/interp.h"
#include "mir/build/build.h"
#include <stdlib.h>
#include <string.h>

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
    
    int steps;
    int call_depth;
    
    AxArena arena;
    bool failed;
    int exit_code;
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
    AxDiagnostic d = {0};
    d.code = AX_DRIVER_INTERP_PANIC;
    d.severity = AX_DIAG_ERROR;
    d.message = msg;
    ax_diag_sink_report(ctx->sink, &d);
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
    
    AxArena local_arena;
    ax_arena_init(&local_arena, 0);
    AxMirBody *body = ax_mir_build(func, ctx->thir, &local_arena);
    
    if (!body) {
        ax_arena_destroy(&local_arena);
        ctx->failed = true;
        ctx->exit_code = 1;
        ctx->call_depth--;
        return;
    }
    
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
                    case AX_MIR_RVALUE_BINARY_OP: {
                        uint64_t lhs = eval_operand(&frame, &stmt->assign.rvalue.binary_op.lhs);
                        uint64_t rhs = eval_operand(&frame, &stmt->assign.rvalue.binary_op.rhs);
                        AxMirBinOp op = stmt->assign.rvalue.binary_op.op;
                        
                        int32_t a = (int32_t)lhs;
                        int32_t b = (int32_t)rhs;
                        int32_t res = 0;
                        switch (op) {
                            case AX_MIR_BINOP_ADD:
                                if (__builtin_add_overflow(a, b, &res)) { panic_interp(ctx, "arithmetic overflow"); }
                                break;
                            case AX_MIR_BINOP_SUB:
                                if (__builtin_sub_overflow(a, b, &res)) { panic_interp(ctx, "arithmetic overflow"); }
                                break;
                            case AX_MIR_BINOP_MUL:
                                if (__builtin_mul_overflow(a, b, &res)) { panic_interp(ctx, "arithmetic overflow"); }
                                break;
                            case AX_MIR_BINOP_DIV: 
                                if (b == 0) { panic_interp(ctx, "division by zero"); }
                                else if (a == (int32_t)0x80000000 && b == -1) { panic_interp(ctx, "arithmetic overflow"); }
                                else { res = a / b; }
                                break;
                            case AX_MIR_BINOP_REM:
                                if (b == 0) { panic_interp(ctx, "division by zero"); }
                                else if (a == (int32_t)0x80000000 && b == -1) { panic_interp(ctx, "arithmetic overflow"); }
                                else { res = a % b; }
                                break;
                            case AX_MIR_BINOP_EQ: res = (a == b); break;
                            case AX_MIR_BINOP_NE: res = (a != b); break;
                            case AX_MIR_BINOP_LT: res = (a < b); break;
                            case AX_MIR_BINOP_LE: res = (a <= b); break;
                            case AX_MIR_BINOP_GT: res = (a > b); break;
                            case AX_MIR_BINOP_GE: res = (a >= b); break;
                            default: break;
                        }
                        val = (uint64_t)res;
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
    ax_arena_destroy(&local_arena);
    ctx->call_depth--;
}

int ax_interp_run(AxHirItem *main_fn, AxThir *thir, const AxHir *hir, StrInterner *interner, const AxResolveMap *rmap, const AxAst *ast, AxDiagSink *sink, int step_limit, int call_depth_limit) {
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
    ax_arena_init(&ctx.arena, 0);
    
    uint64_t ret = 0;
    eval_call(&ctx, main_fn, NULL, 0, &ret);
    
    ax_arena_destroy(&ctx.arena);
    
    if (ctx.failed) {
        return ctx.exit_code;
    }
    return (int)ret;
}
