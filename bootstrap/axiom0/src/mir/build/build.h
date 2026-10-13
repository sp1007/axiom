#ifndef AX_MIR_BUILD_BUILD_H
#define AX_MIR_BUILD_BUILD_H

#include "mir/mir.h"
#include "hir/hir.h"
#include "types/types.h"

AxMirBody *ax_mir_build(const AxHirItem *func, const AxThir *thir, AxArena *arena);
AxMirBody *ax_mir_build_expr(const AxHirExpr *expr, TypeId ty, const AxThir *thir, AxArena *arena);

#endif


