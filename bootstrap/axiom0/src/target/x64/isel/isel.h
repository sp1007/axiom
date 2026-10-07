#ifndef AX_TARGET_X64_ISEL_ISEL_H
#define AX_TARGET_X64_ISEL_ISEL_H

#include "lir/lir.h"
#include "target/x64/mir/mi.h"

AxX64MIBody *ax_x64_isel(const AxLirBody *lir, TypeInterner *interner);

#endif
