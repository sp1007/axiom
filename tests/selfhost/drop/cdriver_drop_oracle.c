/* T082d drop-elaboration oracle (C side of the selfhost/drop differential).
 *
 *   ct_selfhost_drop_cdriver_drop_oracle [--std-root <dir>] [--pre] <file.ax>...
 *
 * For every input file it runs the axiom0 pipeline up to TYPECK, builds MIR for each top-level
 * fn of the main file exactly like `axiom0 inspect --emit=mir`, then (unless --pre) runs
 * ax_mir_drop_elaborate with the same arguments as the driver's own stage and prints the body with
 * ax_mir_print. Each file's output is preceded by a `== <path>` line. The goldens under
 * fixtures/ are this program's output, and tests/selfhost/drop/qa_drop_*.ax checks that the Axiom
 * port (compiler/mir/drop.ax) prints the same bytes. Run without arguments (as ctest does) it
 * exits 0.
 */
#include <stdio.h>
#include <string.h>

#include "driver/driver.h"
#include "mir/mir.h"
#include "mir/build/build.h"
#include "mir/drop/drop.h"

static int emit_file(const AxIo *io, const char *path, bool pre_only) {
    AxDriverState st;
    ax_pipeline_init(&st, io);
    st.main_file = path;
    ax_pipeline_run(&st, AX_STAGE_TYPECK);
    if (st.failed) {
        ax_pipeline_free(&st);
        return 1;
    }

    AxArena mir_arena = {0};
    ax_arena_init(&mir_arena, 0);
    fprintf(io->out, "== %s\n", path);
    for (const AxHirItem *item = st.hir.items; item != NULL; item = item->next) {
        if (st.file.v != 0 && item->span.file.v != 0 && item->span.file.v != st.file.v) {
            continue;
        }
        if (item->kind != AX_HIR_ITEM_FN) {
            continue;
        }
        AxMirBody *body = ax_mir_build(item, &st.thir, &mir_arena);
        if (body == NULL) {
            continue;
        }
        if (!pre_only) {
            ax_mir_drop_elaborate(body, &st.thir, &st.hir, &st.db, &st.sink, &st.interner);
        }
        ax_mir_print(io->out, body);
    }
    ax_arena_destroy(&mir_arena);
    ax_pipeline_free(&st);
    return 0;
}

int main(int argc, char **argv) {
    ax_io_set_binary();
    AxIo io = {stdout, stderr};
    bool pre_only = false;
    int rc = 0;
    for (int i = 1; i < argc; i++) {
        if (strcmp(argv[i], "--std-root") == 0 && i + 1 < argc) {
            ax_opt_std_root = argv[i + 1];
            i++;
            continue;
        }
        if (strcmp(argv[i], "--pre") == 0) {
            pre_only = true;
            continue;
        }
        if (emit_file(&io, argv[i], pre_only) != 0) {
            fprintf(stderr, "drop oracle: %s does not type-check\n", argv[i]);
            rc = 1;
        }
    }
    return rc;
}
