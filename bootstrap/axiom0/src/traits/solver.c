#include "traits/solver.h"
#include "diag/diag.h"

void ax_traits_check_overlap(const AxHir *hir, AxDiagSink *sink, StrInterner *str_in) {
    (void)str_in;
    for (const AxHirItem *i1 = hir->items; i1; i1 = i1->next) {
        if (i1->kind != AX_HIR_ITEM_IMPL) continue;
        for (const AxHirItem *i2 = i1->next; i2; i2 = i2->next) {
            if (i2->kind != AX_HIR_ITEM_IMPL) continue;
            if (i1->impl.trait_path && i2->impl.trait_path && i1->impl.self_type && i2->impl.self_type) {
                if (i1->impl.trait_path->kind == AX_HIR_TYPE_PATH && i2->impl.trait_path->kind == AX_HIR_TYPE_PATH) {
                    if (i1->impl.trait_path->path.path.symbol.v == i2->impl.trait_path->path.path.symbol.v) {
                        if (i1->impl.self_type->kind == AX_HIR_TYPE_PATH && i2->impl.self_type->kind == AX_HIR_TYPE_PATH) {
                            if (i1->impl.self_type->path.path.symbol.v == i2->impl.self_type->path.path.symbol.v) {
                                AxDiagnostic d = {0};
                                d.code = AX_TRAIT_OVERLAP;
                                d.severity = AX_DIAG_ERROR;
                                d.message = "overlapping implementations for trait";
                                d.primary = i2->span;
                                ax_diag_sink_report(sink, &d);
                            }
                        }
                    }
                }
            }
        }
    }
}
