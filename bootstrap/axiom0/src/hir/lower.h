#ifndef AX_HIR_LOWER_H
#define AX_HIR_LOWER_H

#include "hir/hir.h"
#include "resolve/resolve.h"
#include "kernel/arena.h"
#include "diag/diag.h"

AxHir ax_lower_ast(AxArena *arena, const AxAst *ast, const AxResolveMap *rmap, AxDiagSink *sink);

#endif /* AX_HIR_LOWER_H */
