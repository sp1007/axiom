#ifndef AX_TRAITS_SOLVER_H
#define AX_TRAITS_SOLVER_H

#include "types/types.h"
#include "hir/hir.h"

typedef enum AxTraitResult {
    AX_TRAIT_PROVEN,
    AX_TRAIT_DISPROVEN,
    AX_TRAIT_AMBIGUOUS,
    AX_TRAIT_OVERFLOW
} AxTraitResult;

void ax_traits_check_overlap(const AxHir *hir, AxDiagSink *sink, StrInterner *str_in);

#endif
