/* Own-main test driver for AX_ICE / AX_ASSERT and the ICE paths of the kernel containers. Each mode
 * triggers one internal compiler error; the *.test manifests next to this file expect the banner
 * on stderr and exit code 3.
 *
 * abort() would end the process with a platform-specific status (3 on Windows, SIGABRT on POSIX)
 * and may open an error-reporting dialog on Windows, so a SIGABRT handler turns it into a portable
 * _Exit(3). The banner has been flushed to stderr before abort() is called. */
#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

#include "kernel/kernel.h"

AX_DEFINE_ID(CdFileId);
AX_DEFINE_ID_TABLE(CdFileTable, CdFileId, int);
AX_DEFINE_VEC(CdIntVec, int);

static void on_abort(int sig) {
    (void)sig;
    _Exit(3);
}

int main(int argc, char **argv) {
    signal(SIGABRT, on_abort);
    const char *mode = argc > 1 ? argv[1] : "";
    if (strcmp(mode, "ice") == 0) {
        AX_ICE("deliberate test ICE %d", 42);
    } else if (strcmp(mode, "assert") == 0) {
        int two = argc; /* 2 at run time, so the assertion is not folded away */
        AX_ASSERT(two == 1);
    } else if (strcmp(mode, "table-none") == 0) {
        CdFileTable t;
        CdFileTable_init(&t);
        CdFileTable_push(&t, 1);
        (void)CdFileTable_get(&t, CdFileId_none());
    } else if (strcmp(mode, "table-range") == 0) {
        CdFileTable t;
        CdFileTable_init(&t);
        CdFileTable_push(&t, 1);
        (void)CdFileTable_get(&t, CdFileId_from_index(5));
    } else if (strcmp(mode, "vec-range") == 0) {
        CdIntVec v = CdIntVec_new();
        CdIntVec_push(&v, 1);
        (void)CdIntVec_get(&v, 1);
    } else if (strcmp(mode, "interner-none") == 0) {
        StrInterner in;
        ax_interner_init(&in);
        (void)ax_interner_get(&in, StrId_none());
    } else if (strcmp(mode, "arena-align") == 0) {
        AxArena a;
        ax_arena_init(&a, 0);
        (void)ax_arena_alloc(&a, 8, 3);
    }
    fprintf(stderr, "cdriver_ice: unknown or non-failing mode '%s'\n", mode);
    return 0;
}
