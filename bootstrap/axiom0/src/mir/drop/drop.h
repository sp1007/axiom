#ifndef AX_MIR_DROP_H
#define AX_MIR_DROP_H

#include "mir/mir.h"
#include "hir/hir.h"
#include "diag/diag.h"

void ax_mir_drop_elaborate(AxMirBody *body, const AxThir *thir, const AxHir *hir, const struct SourceDatabase *db, AxDiagSink *sink, const StrInterner *interner);
const AxHirItem *ax_find_drop_impl_fn(TypeId ty, const AxThir *thir, const StrInterner *interner, const AxHir *hir, const struct SourceDatabase *db);
bool ax_type_needs_drop(TypeId ty, const AxThir *thir, const StrInterner *interner, const AxHir *hir, const struct SourceDatabase *db);

#endif // AX_MIR_DROP_H
