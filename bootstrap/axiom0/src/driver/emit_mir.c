#include "driver/driver.h"
#include "mir/mir.h"
#include "mir/build/build.h"
#include <stdlib.h>
#include <string.h>

static int emit_mir_run(const AxIo *io, int argc, char **argv) {
    char **pos_argv = NULL;
    int pos_argc = 0;
    if (ax_options_parse(io, argc, argv, ax_all_options, &pos_argc, &pos_argv, NULL) != AX_EXIT_OK) {
        return AX_EXIT_USAGE;
    }

    if (pos_argc != 2) {
        fputs("axiom0: usage: axiom0 inspect --emit=mir <file>\n", io->err);
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
        
        // We only need to read the file
        ax_pipeline_run(&st, AX_STAGE_SOURCE);
        if (st.failed) {
            ax_pipeline_free(&st);
            free(pos_argv);
            return AX_EXIT_DIAG;
        }
        
        // The file text is in st.text
        // Ensure null-terminated string for parser
        char *text = malloc(st.text.len + 1);
        memcpy(text, st.text.ptr, st.text.len);
        text[st.text.len] = '\0';
        
        AxMirBody *body = ax_mir_parse(text, &st.thir.interner, &st.hir_arena);
        ax_mir_print(io->out, body);
        
        free(text);
        ax_pipeline_free(&st);
        free(pos_argv);
        return AX_EXIT_OK;
    }

    // For .ax files, we run the pipeline up to TYPECK, then build MIR for each function
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
            AxMirBody *body = ax_mir_build(item, &st.thir, &st.hir_arena);
            if (body) {
                ax_mir_print(io->out, body);
            }
        }
    }
    
    ax_pipeline_free(&st);
    free(pos_argv);
    return AX_EXIT_OK;
}

const AxEmitter axemit_mir = {
    "mir",
    "Emit MIR (parse from .mir or lower from .ax)",
    emit_mir_run
};
