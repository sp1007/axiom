import os
import sys

mono_c = """#include "traits/mono/mono.h"
#include "driver/driver.h"
#include "resolve/resolve.h"
#include "types/typeck.h"
#include <string.h>

static void collect_instance(AxDriverState *st, const AxHirItem *item, const AxGenericArgs *args) {
    // Basic deduplication
    for (AxMonoInstance *inst = st->mono_instances; inst; inst = inst->next) {
        if (inst->item == item) {
            // Simplified equality for args
            if (args == NULL && inst->args.count == 0) return;
            if (args != NULL && args->count == inst->args.count) {
                bool eq = true;
                for (size_t i = 0; i < args->count; i++) {
                    if (args->args[i].v != inst->args.args[i].v) { eq = false; break; }
                }
                if (eq) return;
            }
        }
    }
    
    AxMonoInstance *inst = ax_arena_alloc(&st->hir_arena, sizeof(AxMonoInstance), _Alignof(AxMonoInstance));
    inst->item = item;
    if (args) inst->args = *args;
    else inst->args.count = 0;
    
    inst->mangled_name = item->fn.name; // TODO proper mangling
    inst->body = ax_pipeline_get_mir(item); // TODO actually substitute body
    
    inst->next = st->mono_instances;
    st->mono_instances = inst;
}

void ax_stage_mono(AxDriverState *st) {
    st->mono_instances = NULL;
    for (AxHirItem *it = st->hir.items; it; it = it->next) {
        if (it->kind == AX_HIR_ITEM_FN && (it->fn.generic_params == NULL || it->fn.generic_params->param_count == 0)) {
            collect_instance(st, it, NULL);
        }
    }
}
"""
with open("bootstrap/axiom0/src/traits/mono/mono.c", "w") as f:
    f.write(mono_c)
print("Wrote mono.c")
