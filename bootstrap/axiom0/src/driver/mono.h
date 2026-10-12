#ifndef AX_TRAITS_MONO_H
#define AX_TRAITS_MONO_H

#include "hir/hir.h"
#include "mir/mir.h"
#include "types/types.h"
#include "kernel/str.h"

typedef struct AxMonoInstance {
    AxHirItem *item;
    AxMirBody *body;
    StrId mangled_name;
    struct AxMonoInstance *next;
} AxMonoInstance;

struct AxDriverState;

void ax_stage_mono(struct AxDriverState *st);

#endif // AX_TRAITS_MONO_H
