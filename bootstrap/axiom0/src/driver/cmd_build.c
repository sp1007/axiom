#include "driver/driver.h"
#include <stdlib.h>

static int run_build(const AxIo *io, int argc, char **argv) {
    char **pos_argv = NULL;
    int pos_argc = 0;
    if (ax_options_parse(io, argc, argv, ax_all_options, &pos_argc, &pos_argv, NULL) != AX_EXIT_OK) {
        return AX_EXIT_USAGE;
    }

    if (pos_argc < 2) {
        fputs("axiom0: build needs an input file\n", io->err);
        free(pos_argv);
        return AX_EXIT_USAGE;
    }

    if (ax_opt_build_o == NULL) {
        fputs("axiom0: build needs an output file (-o)\n", io->err);
        free(pos_argv);
        return AX_EXIT_USAGE;
    }

    AxDriverState st;
    ax_pipeline_init(&st, io);
    st.main_file = pos_argv[1];
    
    // We don't have codegen yet, so this will fail with AX_DRIVER_STAGE_NOT_AVAILABLE
    int rc = ax_pipeline_run(&st, AX_STAGE_LIMIT /* dummy for codegen */);
    
    ax_pipeline_free(&st);
    free(pos_argv);
    return rc;
}

const AxCommand axcmd_build = {"build", "compile the program", run_build};
