#include <stdlib.h>
#include <string.h>

#include "driver/driver.h"

/* `axiom0 inspect --emit=<name> [arguments]`: dispatches to the emitter registered by
 * src/driver/emit_<name>.c. The emitter receives argv = {"inspect", <all other arguments>}. */

#define EMIT_PREFIX "--emit="

static void list_emitters(FILE *to) {
    if (ax_emitters[0] == NULL) {
        fputs("axiom0: no emitters are available in this build\n", to);
        return;
    }
    fputs("available emitters:\n", to);
    for (const AxEmitter *const *e = ax_emitters; *e != NULL; ++e) {
        fprintf(to, "  %-12s %s\n", (*e)->name, (*e)->summary);
    }
}

static int run_inspect(const AxIo *io, int argc, char **argv) {
    const char *emit = NULL;
    char **rest = malloc(((size_t)argc + 1) * sizeof *rest);
    if (rest == NULL) {
        fputs("axiom0: out of memory\n", io->err);
        return AX_EXIT_ICE;
    }
    int n = 0;
    rest[n++] = argv[0];
    for (int i = 1; i < argc; ++i) {
        if (strncmp(argv[i], EMIT_PREFIX, sizeof EMIT_PREFIX - 1) == 0) {
            emit = argv[i] + sizeof EMIT_PREFIX - 1;
        } else {
            rest[n++] = argv[i];
        }
    }
    rest[n] = NULL;

    int rc;
    if (emit == NULL || *emit == '\0') {
        fputs("axiom0: usage: axiom0 inspect --emit=<name> [arguments]\n", io->err);
        list_emitters(io->err);
        rc = AX_EXIT_USAGE;
    } else {
        const AxEmitter *e = ax_find_emitter(emit);
        if (e == NULL) {
            fprintf(io->err, "axiom0: unknown emitter '%s'\n", emit);
            list_emitters(io->err);
            rc = AX_EXIT_USAGE;
        } else {
            rc = e->run(io, n, rest);
        }
    }
    free(rest);
    return rc;
}

const AxCommand axcmd_inspect = {"inspect", "dump an intermediate representation (--emit=<name>)",
                                 run_inspect};
