#ifndef AX_MIR_DROP_H
#define AX_MIR_DROP_H

#include "mir/mir.h"
#include "hir/hir.h"
#include "diag/diag.h"

void ax_mir_drop_elaborate(AxMirBody *body, const AxThir *thir, AxDiagSink *sink, const StrInterner *interner);

#endif // AX_MIR_DROP_H
