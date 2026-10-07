#include "driver/driver.h"
#include <stdlib.h>

const char *ax_run_panic_msg = NULL;
static int run_run(const AxIo *io, int argc, char **argv) {
    char **pos_argv = NULL;
    int pos_argc = 0;
    bool dash_dash = false;
    
    if (ax_options_parse(io, argc, argv, ax_all_options, &pos_argc, &pos_argv, &dash_dash) != AX_EXIT_OK) {
        return AX_EXIT_USAGE;
    }

    if (pos_argc < 2) {
        fputs("axiom0: run needs an input file\n", io->err);
        free(pos_argv);
        return AX_EXIT_USAGE;
    }

    AxDriverState st;
    ax_pipeline_init(&st, io);
    st.main_file = pos_argv[1];
    
    extern const char *ax_run_panic_msg;
    ax_run_panic_msg = NULL;
    
    // We don't have execution yet, so this will fail with AX_DRIVER_STAGE_NOT_AVAILABLE
    int rc = ax_pipeline_run(&st, AX_STAGE_LIMIT /* dummy for run/interp */);
    
    if (rc == 101 && ax_run_panic_msg) {
        fprintf(io->err, "panic: %s\n", ax_run_panic_msg);
        fflush(io->err);
        ax_pipeline_free(&st);
        free(pos_argv);
        exit(101);
    }
    
    ax_pipeline_free(&st);
    free(pos_argv);
    return rc;
}

const AxCommand axcmd_run = {"run", "compile and run the program", run_run};
