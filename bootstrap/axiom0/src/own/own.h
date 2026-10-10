#ifndef AX_OWN_OWN_H
#define AX_OWN_OWN_H

#include "types/types.h"
#include "mir/mir.h"
#include "diag/diag.h"

typedef enum AxOwnState {
    AX_OWN_UNINIT,
    AX_OWN_OWNED,
    AX_OWN_MOVED,
    AX_OWN_PARTIAL
} AxOwnState;

bool ax_type_is_copy(TypeId id, const AxThir *thir, const StrInterner *str_in);
void ax_own_check(const AxHirItem *it, AxMirBody *body, const AxThir *thir, AxDiagSink *sink, const StrInterner *str_in);

#endif // AX_OWN_OWN_H
