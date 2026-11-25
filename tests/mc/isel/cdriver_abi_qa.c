#include <stdio.h>
/* T503 (ADR-0034 §8): explicit checks that stay live in release (-DNDEBUG) builds, where a
   compiled-out check would leave this driver verifying nothing. */
#define CHECK(cond)                                                                  \
    do {                                                                             \
        if (!(cond)) {                                                               \
            fprintf(stderr, "%s:%d: CHECK failed: %s\n", __FILE__, __LINE__, #cond); \
            return 1;                                                                \
        }                                                                            \
    } while (0)
#include "abi/abi.h"

int main(void) {
    TypeInterner interner;
    ax_type_interner_init(&interner);
    AxArena arena;
    ax_arena_init(&arena, 0);

    // QA test: Test aggregate of size 8 (passed by value) vs size 9 (passed by ref)
    TypeId arr8_ty = ax_intern_type(&interner, &(AxType){ .kind = AX_TY_ARRAY, .array = { .elem = interner.t_i8, .len = 8 } });
    TypeId arr9_ty = ax_intern_type(&interner, &(AxType){ .kind = AX_TY_ARRAY, .array = { .elem = interner.t_i8, .len = 9 } });

    // Function taking size 8 then size 9
    TypeId params[2] = { arr8_ty, arr9_ty };
    AxType fn = { .kind = AX_TY_FN, .fn = { .ret_type = interner.t_unit, .param_count = 2, .param_types = params } };
    
    AxAbiSig sig = ax_abi_win64.classify(&fn, &interner, &arena);
    CHECK(sig.arg_count == 2);
    // Size 8 is passed by value in RCX
    CHECK(sig.args[0].loc.kind == AX_ABI_LOC_REG && sig.args[0].loc.reg == 1); // RCX
    // Size 9 is passed by reference, pointer in RDX
    CHECK(sig.args[1].loc.kind == AX_ABI_LOC_INDIRECT && sig.args[1].loc.reg == 2); // RDX

    printf("cdriver_abi_qa pass\n");
    ax_arena_destroy(&arena);
    ax_type_interner_free(&interner);
    return 0;
}
