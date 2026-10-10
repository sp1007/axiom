#ifndef AX_OWN_OWN_H
#define AX_OWN_OWN_H

#include "types/types.h"

typedef enum AxOwnState {
    AX_OWN_UNINIT,
    AX_OWN_OWNED,
    AX_OWN_MOVED,
    AX_OWN_PARTIAL
} AxOwnState;

bool ax_type_is_copy(TypeId id, const AxThir *thir, const StrInterner *str_in);

#endif // AX_OWN_OWN_H
