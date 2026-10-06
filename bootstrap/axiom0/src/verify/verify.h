#ifndef AX_VERIFY_VERIFY_H
#define AX_VERIFY_VERIFY_H

#include "mir/mir.h"
#include "diag/diag.h"

void ax_verify_mir(const AxMirBody *body, const AxThir *thir, AxDiagSink *sink, const AxHirItem *func);

#endif // AX_VERIFY_VERIFY_H
