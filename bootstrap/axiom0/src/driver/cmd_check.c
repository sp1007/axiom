#include "driver/driver.h"
#include <stdlib.h>

static int run_check(const AxIo *io, int argc, char **argv) {
    char **pos_argv = NULL;
    int pos_argc = 0;
    if (ax_options_parse(io, argc, argv, ax_all_options, &pos_argc, &pos_argv, NULL) != AX_EXIT_OK) {
        return AX_EXIT_USAGE;
    }

    if (pos_argc < 2) {
        fputs("axiom0: check needs an input file\n", io->err);
        free(pos_argv);
        return AX_EXIT_USAGE;
    }

    AxDriverState st;
    ax_pipeline_init(&st, io);
    st.main_file = pos_argv[1];
    
    int rc = ax_pipeline_run(&st, AX_STAGE_HIR);
    
    ax_pipeline_free(&st);
    free(pos_argv);
    return rc;
}

const AxCommand axcmd_check = {"check", "check the program for errors", run_check};
