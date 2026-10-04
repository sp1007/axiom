#include <string.h>

#include "driver/driver.h"

/* Lookup over the generated tables (the tables themselves live in the generated registry.c). */

const AxCommand *ax_find_command(const char *name) {
    for (const AxCommand *const *c = ax_commands; *c != NULL; ++c) {
        if (strcmp((*c)->name, name) == 0) {
            return *c;
        }
    }
    return NULL;
}

const AxEmitter *ax_find_emitter(const char *name) {
    for (const AxEmitter *const *e = ax_emitters; *e != NULL; ++e) {
        if (strcmp((*e)->name, name) == 0) {
            return *e;
        }
    }
    return NULL;
}
