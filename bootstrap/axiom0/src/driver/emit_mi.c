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
            AxLirBody *lir_body = ax_lir_lower(mir_body, &st.thir.interner);
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
        if (item->kind == AX_HIR_ITEM_FN) {
            AxMirBody *mir_body = ax_mir_build(item, &st.thir, &st.hir_arena);
            if (mir_body) {
                AxLirBody *lir_body = ax_lir_lower(mir_body, &st.thir.interner);
                if (lir_body) {
                    const TypeId *pty = AxItemTypeMap_get(&st.thir.item_types, item);
                    const AxType *fn_ty = ax_type_get(&st.thir.interner, *pty);
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
