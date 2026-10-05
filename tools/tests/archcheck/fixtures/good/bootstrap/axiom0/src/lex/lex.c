#include "kernel/k.h"
#include "diag/diag.h"

/* uses a registered code by name, never registers one */
int lex_fail(void) {
    return diag_emit(sink, AX_LEX_INVALID_UTF8, span);
}
