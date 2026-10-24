/*
 * T147 / ADR-0035 section 2: links the given COFF objects with the axiom0 PE linker.
 *   usage: ct_link_local_symbols_cdriver_link_objs <out.exe> <a.obj> [b.obj ...]
 * Prints `LINKED` on success, or `LINK-FAILED <diagnostic-code-name>` on failure.
 */
#include "link/pe/linker.h"
#include "diag/diag.h"
#include "kernel/base.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>

AxDiagSink diag;
static const char *g_last_code = "none";

void ax_diag_sink_init(AX_MAYBE_UNUSED AxDiagSink *sink) { (void)sink; }
void ax_diag_sink_free(AX_MAYBE_UNUSED AxDiagSink *sink) { (void)sink; }
void ax_diag_sink_report(AX_MAYBE_UNUSED AxDiagSink *sink, const AxDiagnostic *d) {
    (void)sink;
    g_last_code = ax_diag_code_name(d->code);
}

int main(int argc, char **argv) {
    if (argc < 3) {
        fprintf(stderr, "usage: %s <out.exe> <obj>...\n", argv[0]);
        return 2;
    }
    ax_diag_sink_init(&diag);
    const char *const *inputs = (const char *const *)(argv + 2);
    bool ok = ax_pe_link(inputs, (size_t)(argc - 2), argv[1], 0x100000, &diag);
    if (ok) {
        printf("LINKED\n");
    } else {
        printf("LINK-FAILED %s\n", g_last_code);
    }
    ax_diag_sink_free(&diag);
    return ok ? 0 : 1;
}
