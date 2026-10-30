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

/* T161: the MIR of a trait default method's instance for one implementing type (the member typeck adds to every
 * impl that does not override the method): `Self` replaced by that type and trait-member calls on it bound to its
 * impl. Any other item's body is returned unchanged. */
AxMirBody *ax_mono_instantiate_default(struct AxDriverState *st, const AxHirItem *inst, AxMirBody *body);

#endif // AX_TRAITS_MONO_H
