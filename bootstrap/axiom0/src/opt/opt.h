#ifndef AX_OPT_OPT_H
#define AX_OPT_OPT_H

#include "mir/mir.h"
#include "types/types.h"
#include "diag/diag.h"

void ax_opt_run(AxMirBody *body, AxThir *thir, AxDiagSink *sink, const AxHirItem *item, bool verify_each);

#endif // AX_OPT_OPT_H
