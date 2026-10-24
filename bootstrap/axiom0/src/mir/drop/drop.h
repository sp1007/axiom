#ifndef AX_MIR_DROP_H
#define AX_MIR_DROP_H

#include "mir/mir.h"
#include "hir/hir.h"
#include "diag/diag.h"

void ax_mir_drop_elaborate(AxMirBody *body, const AxThir *thir, const AxHir *hir, const struct SourceDatabase *db, AxDiagSink *sink, const StrInterner *interner);
const AxHirItem *ax_find_drop_impl_fn(TypeId ty, const AxThir *thir, const StrInterner *interner, const AxHir *hir, const struct SourceDatabase *db);
/* True iff `impl` is `impl Drop for T` with the trait path resolving to the prelude lang item Drop
 * (SPEC-12 AXS-DROP-008): not a path to a user trait named Drop, not a shadowing `trait Drop`. */
bool ax_hir_impl_is_lang_drop(const AxHirItem *impl, const AxHir *hir, const StrInterner *interner, const struct SourceDatabase *db);
bool ax_type_needs_drop(TypeId ty, const AxThir *thir, const StrInterner *interner, const AxHir *hir, const struct SourceDatabase *db);

#endif // AX_MIR_DROP_H
