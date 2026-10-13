#ifndef AX_OWN_UNSAFE_H
#define AX_OWN_UNSAFE_H

#include "hir/hir.h"
#include "types/types.h"
#include "diag/diag.h"
#include "kernel/interner.h"

void ax_unsafe_check(const AxHir *hir, const AxThir *thir, AxDiagSink *sink, const StrInterner *interner);

#endif // AX_OWN_UNSAFE_H
