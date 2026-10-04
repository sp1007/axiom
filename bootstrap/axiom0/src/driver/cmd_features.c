#include "driver/driver.h"

/* `axiom0 --features`: capability probe for the test runner (T005 treats a missing or failing probe
 * as "no modes"). One capability per line; the list is empty until a stage task advertises one
 * (T016 derives it from the registered stages, T028 adds `native`). */

static int run_features(const AxIo *io, int argc, char **argv) {
    if (argc != 1) {
        fprintf(io->err, "axiom0: '--features' takes no arguments (got '%s')\n", argv[1]);
        return AX_EXIT_USAGE;
    }
    return AX_EXIT_OK;
}

const AxCommand axcmd_features = {"--features", "list the capabilities of this build, one per line",
                                  run_features};
