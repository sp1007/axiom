#include "driver/driver.h"

#ifndef AX_VERSION_STRING
#define AX_VERSION_STRING "0.0.0"
#endif

static int run_version(const AxIo *io, int argc, char **argv) {
    if (argc != 1) {
        fprintf(io->err, "axiom0: 'version' takes no arguments (got '%s')\n", argv[1]);
        return AX_EXIT_USAGE;
    }
    fprintf(io->out, "axiom0 %s (stage0)\n", AX_VERSION_STRING);
    return AX_EXIT_OK;
}

const AxCommand axcmd_version = {"version", "print the compiler version", run_version};
