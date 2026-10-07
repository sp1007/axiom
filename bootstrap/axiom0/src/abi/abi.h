#ifndef AX_ABI_ABI_H
#define AX_ABI_ABI_H

#include "types/types.h"
#include "lir/lir.h"
#include <stdbool.h>
#include <stdint.h>

typedef enum AxAbiLocKind {
    AX_ABI_LOC_REG,
    AX_ABI_LOC_STACK,
    AX_ABI_LOC_INDIRECT // pointer in reg
} AxAbiLocKind;

typedef struct AxAbiLoc {
    AxAbiLocKind kind;
    union {
        uint32_t reg;       // Register ID (machine specific)
        uint32_t offset;    // Offset from stack base
    };
} AxAbiLoc;

typedef struct AxAbiArg {
    TypeId ty;
    AxAbiLoc loc;
} AxAbiArg;

typedef struct AxAbiSig {
    AxAbiArg *args;
    size_t arg_count;
    AxAbiArg ret;
    uint32_t shadow_space;
    uint32_t stack_args_size;
} AxAbiSig;

typedef struct AxAbi {
    AxAbiSig (*classify)(const AxType *fn_ty, TypeInterner *interner, AxArena *arena);
} AxAbi;

// LIR to LIR ABI lowering pass
void ax_lir_lower_abi(AxLirBody *body, TypeInterner *interner, const AxAbi *abi, const AxType *fn_ty);

extern const AxAbi ax_abi_win64;

#endif
