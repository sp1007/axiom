#include <stdio.h>
#include <assert.h>
#include "abi/abi.h"

int main(void) {
    TypeInterner interner;
    ax_type_interner_init(&interner);
    AxArena arena;
    ax_arena_init(&arena, 0);

    // QA2 test: Test hidden return pointer shifting arguments and putting some on stack
    TypeId arr16_ty = ax_intern_type(&interner, &(AxType){ .kind = AX_TY_ARRAY, .array = { .elem = interner.t_i8, .len = 16 } });
    TypeId arr8_ty = ax_intern_type(&interner, &(AxType){ .kind = AX_TY_ARRAY, .array = { .elem = interner.t_i8, .len = 8 } });

    // Function returning size 16, taking 5 size 8 args
    TypeId params[5] = { arr8_ty, arr8_ty, arr8_ty, arr8_ty, arr8_ty };
    AxType fn = { .kind = AX_TY_FN, .fn = { .ret_type = arr16_ty, .param_count = 5, .param_types = params } };
    
    AxAbiSig sig = ax_abi_win64.classify(&fn, &interner, &arena);
    assert(sig.arg_count == 5);
    
    // Hidden return pointer in RCX
    assert(sig.ret.loc.kind == AX_ABI_LOC_INDIRECT && sig.ret.loc.reg == 1); // RCX

    // Arg 1 is passed in RDX
    assert(sig.args[0].loc.kind == AX_ABI_LOC_REG && sig.args[0].loc.reg == 2); // RDX
    // Arg 2 is passed in R8
    assert(sig.args[1].loc.kind == AX_ABI_LOC_REG && sig.args[1].loc.reg == 8); // R8
    // Arg 3 is passed in R9
    assert(sig.args[2].loc.kind == AX_ABI_LOC_REG && sig.args[2].loc.reg == 9); // R9
    // Arg 4 is passed on stack at offset 32
    assert(sig.args[3].loc.kind == AX_ABI_LOC_STACK && sig.args[3].loc.offset == 32);
    // Arg 5 is passed on stack at offset 40
    assert(sig.args[4].loc.kind == AX_ABI_LOC_STACK && sig.args[4].loc.offset == 40);

    printf("cdriver_abi_qa2 pass\n");
    ax_arena_destroy(&arena);
    ax_type_interner_free(&interner);
    return 0;
}
