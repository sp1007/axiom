#include "driver/driver.h"
#include "hir/hir.h"
#include "mir/mir.h"
#include "mir/build/build.h"
#include "lir/lir.h"
#include "abi/abi.h"
#include "target/x64/isel/isel.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

static void resolve_mir_call_types(AxDriverState *st, AxMirBody *body) {
    if (!body) return;
    for (size_t i = 0; i < body->bb_count; i++) {
        AxMirTerminator *term = &body->bbs[i].terminator;
        if (term->kind != AX_MIR_TERM_CALL || term->call.func.kind != AX_MIR_OP_CONST) continue;
        TypeId orig_ty = term->call.func.constant.ty;
        if (orig_ty.v != 0) {
            const AxType *ot = ax_type_get(&st->thir.interner, orig_ty);
            if (ot && ot->kind != AX_TY_FN) continue;
        }
        uint32_t sym_v = (uint32_t)term->call.func.constant.val;
        const AxHirItem *callee = NULL;
        for (const AxHirItem *it = st->hir.items; it; it = it->next) {
            if (it->kind == AX_HIR_ITEM_FN && it->fn.symbol.v == sym_v) {
                callee = it;
                break;
            }
            if (it->kind == AX_HIR_ITEM_IMPL) {
                for (const AxHirItem *m = it->impl.members; m; m = m->next) {
                    if (m->kind == AX_HIR_ITEM_FN && m->fn.symbol.v == sym_v) {
                        callee = m;
                        break;
                    }
                }
                if (callee) break;
            }
        }
        if (callee) {
            bool is_generic = (callee->fn.generic_params && callee->fn.generic_params->params != NULL);
            if (!is_generic) {
                const TypeId *pty = AxItemTypeMap_get(&st->thir.item_types, callee);
                if (pty && pty->v != 0) {
                    term->call.func.constant.ty = *pty;
                }
            }
        }
    }
}

static const AxType *resolve_item_fn_ty(AxDriverState *st, const AxHirItem *item, const AxMirBody *mir_body) {
    const TypeId *pty = AxItemTypeMap_get(&st->thir.item_types, item);
    TypeId ty_id = pty ? *pty : (TypeId){0};
    if (ty_id.v != 0) {
        const AxType *item_ty = ax_type_get(&st->thir.interner, ty_id);
        if (item_ty && item_ty->kind == AX_TY_CLOSURE && item_ty->closure.fn_type.v != 0) {
            ty_id = item_ty->closure.fn_type;
        }
    }
    if (ty_id.v == 0 && mir_body && mir_body->local_count > 0) {
        size_t arg_count = 0;
        for (size_t i = 1; i < mir_body->local_count; i++) {
            if (mir_body->locals[i].kind == AX_MIR_LOCAL_ARG) arg_count++;
            else break;
        }
        TypeId *param_types = malloc((arg_count ? arg_count : 1) * sizeof(TypeId));
        for (size_t i = 0; i < arg_count; i++) {
            param_types[i] = mir_body->locals[i + 1].ty;
        }
        AxType dummy;
        memset(&dummy, 0, sizeof(dummy));
        dummy.kind = AX_TY_FN;
        dummy.fn.ret_type = mir_body->locals[0].ty;
        dummy.fn.param_count = arg_count;
        dummy.fn.param_types = param_types;
        ty_id = ax_intern_type(&st->thir.interner, &dummy);
    }
    return (ty_id.v != 0) ? ax_type_get(&st->thir.interner, ty_id) : NULL;
}

static int run_emit_mi(const AxIo *io, int argc, char **argv) {
    char **pos_argv = NULL;
    int pos_argc = 0;
    if (ax_options_parse(io, argc, argv, ax_all_options, &pos_argc, &pos_argv, NULL) != AX_EXIT_OK) {
        return AX_EXIT_USAGE;
    }

    if (pos_argc != 2) {
        fputs("axiom0: usage: axiom0 inspect --emit=mi <file>\n", io->err);
        free(pos_argv);
        return AX_EXIT_USAGE;
    }

    const char *path = pos_argv[1];
    
    // Check if it's a .mir file for hand-written tests
    size_t len = strlen(path);
    if (len >= 4 && strcmp(path + len - 4, ".mir") == 0) {
        AxDriverState st;
        ax_pipeline_init(&st, io);
        st.main_file = path;
        
        ax_pipeline_run(&st, AX_STAGE_SOURCE);
        if (st.failed) {
            ax_pipeline_free(&st);
            free(pos_argv);
            return AX_EXIT_DIAG;
        }
        
        char *text = malloc(st.text.len + 1);
        memcpy(text, st.text.ptr, st.text.len);
        text[st.text.len] = '\0';
        
        AxMirBody *mir_body = ax_mir_parse(text, &st.thir.interner, &st.hir_arena);
        if (mir_body) {
            AxLirBody *lir_body = ax_lir_lower(mir_body, &st.hir, &st.thir.interner, &st.interner, NULL);
            AxType fn_ty = { .kind = AX_TY_FN };
            fn_ty.fn.param_count = 0; // assumption for mir tests
            fn_ty.fn.ret_type = mir_body->locals[0].ty;
            fn_ty.fn.param_types = NULL;
            ax_lir_lower_abi(lir_body, &st.thir.interner, &ax_abi_win64, &fn_ty);
            
            AxX64MIBody *mi_body = ax_x64_isel(lir_body, &st.thir.interner);
            ax_x64_mi_print(io->out, mi_body);
        }
        
        free(text);
        ax_pipeline_free(&st);
        free(pos_argv);
        return AX_EXIT_OK;
    }

    AxDriverState st;
    ax_pipeline_init(&st, io);
    st.main_file = path;
    
    ax_pipeline_run(&st, AX_STAGE_TYPECK);
    if (st.failed) {
        ax_pipeline_free(&st);
        free(pos_argv);
        return AX_EXIT_DIAG;
    }
    
    for (const AxHirItem *item = st.hir.items; item != NULL; item = item->next) {
        if (st.file.v != 0 && item->span.file.v != 0 && item->span.file.v != st.file.v) {
            continue;
        }
        if (item->kind == AX_HIR_ITEM_FN) {
            AxMirBody *mir_body = ax_pipeline_get_mir(item);
            if (mir_body) {
                resolve_mir_call_types(&st, mir_body);
                const AxType *fn_ty = resolve_item_fn_ty(&st, item, mir_body);
                AxLirBody *lir_body = ax_lir_lower(mir_body, &st.hir, &st.thir.interner, &st.interner, fn_ty);
                if (lir_body) {
                    ax_lir_lower_abi(lir_body, &st.thir.interner, &ax_abi_win64, fn_ty);
                    AxX64MIBody *mi_body = ax_x64_isel(lir_body, &st.thir.interner);
                    ax_x64_mi_print(io->out, mi_body);
                }
            }
        }
    }
    
    ax_pipeline_free(&st);
    free(pos_argv);
    return AX_EXIT_OK;
}

const AxEmitter axemit_mi = {
    "mi",
    "dump the x64 machine IR",
    run_emit_mi
};


