#include "driver/driver.h"
#include "mir/mir.h"
#include "mir/build/build.h"
#include "lir/lir.h"
#include <stdlib.h>
#include <string.h>

static int emit_lir_run(const AxIo *io, int argc, char **argv) {
    char **pos_argv = NULL;
    int pos_argc = 0;
    if (ax_options_parse(io, argc, argv, ax_all_options, &pos_argc, &pos_argv, NULL) != AX_EXIT_OK) {
        return AX_EXIT_USAGE;
    }

    if (pos_argc != 2) {
        fputs("axiom0: usage: axiom0 inspect --emit=lir <file>\n", io->err);
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
            ax_lir_print(io->out, lir_body);
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
                AxLirBody *lir_body = ax_lir_lower(mir_body, &st.hir, &st.thir.interner, &st.interner, NULL);
                if (lir_body) {
                    ax_lir_print(io->out, lir_body);
                }
            }
        }
    }
    
    ax_pipeline_free(&st);
    free(pos_argv);
    return AX_EXIT_OK;
}

const AxEmitter axemit_lir = {
    "lir",
    "Emit LIR (parse from .mir or lower from .ax)",
    emit_lir_run
};


