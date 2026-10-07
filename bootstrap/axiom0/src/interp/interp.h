#ifndef AX_INTERP_INTERP_H
#define AX_INTERP_INTERP_H

#include "types/types.h"
#include "diag/diag.h"
#include "resolve/resolve.h"
#include "syntax/ast.h"

int ax_interp_run(AxHirItem *main_fn, AxThir *thir, const AxHir *hir, StrInterner *interner, const AxResolveMap *rmap, const AxAst *ast, AxDiagSink *sink, int step_limit, int call_depth_limit, void *mir_map, const char **out_panic_msg);

#endif
