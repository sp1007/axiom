#include <stdio.h>
#include <assert.h>
#include "abi/abi.h"

int main() {
    TypeInterner interner;
    ax_type_interner_init(&interner);
    AxArena arena;
    ax_arena_init(&arena, 0);

    // Build types for testing
    // Type 1: 0 to 6 integer arguments
    TypeId params1[6] = { interner.t_i32, interner.t_i32, interner.t_i32, interner.t_i32, interner.t_i32, interner.t_i32 };
    AxType fn1 = { .kind = AX_TY_FN, .fn = { .ret_type = interner.t_unit, .param_count = 6, .param_types = params1 } };
    AxAbiSig sig1 = ax_abi_win64.classify(&fn1, &interner, &arena);
    assert(sig1.arg_count == 6);
    assert(sig1.args[0].loc.kind == AX_ABI_LOC_REG && sig1.args[0].loc.reg == 1); // RCX
    assert(sig1.args[1].loc.kind == AX_ABI_LOC_REG && sig1.args[1].loc.reg == 2); // RDX
    assert(sig1.args[2].loc.kind == AX_ABI_LOC_REG && sig1.args[2].loc.reg == 8); // R8
    assert(sig1.args[3].loc.kind == AX_ABI_LOC_REG && sig1.args[3].loc.reg == 9); // R9
    assert(sig1.args[4].loc.kind == AX_ABI_LOC_STACK && sig1.args[4].loc.offset == 32);
    assert(sig1.args[5].loc.kind == AX_ABI_LOC_STACK && sig1.args[5].loc.offset == 40);

    // Type 2: 8-byte aggregate (passed by value) and 16-byte aggregate (passed by ref)
    TypeId arr8_ty = ax_intern_type(&interner, &(AxType){ .kind = AX_TY_ARRAY, .array = { .elem = interner.t_i32, .len = 2 } });
    TypeId arr16_ty = ax_intern_type(&interner, &(AxType){ .kind = AX_TY_ARRAY, .array = { .elem = interner.t_i32, .len = 4 } });
    TypeId params2[2] = { arr8_ty, arr16_ty };
    AxType fn2 = { .kind = AX_TY_FN, .fn = { .ret_type = interner.t_unit, .param_count = 2, .param_types = params2 } };
    AxAbiSig sig2 = ax_abi_win64.classify(&fn2, &interner, &arena);
    assert(sig2.arg_count == 2);
    assert(sig2.args[0].loc.kind == AX_ABI_LOC_REG && sig2.args[0].loc.reg == 1); // RCX
    assert(sig2.args[1].loc.kind == AX_ABI_LOC_INDIRECT && sig2.args[1].loc.reg == 2); // RDX (pointer)

    // Type 3: aggregate return through hidden pointer
    TypeId params3[1] = { interner.t_i32 };
    AxType fn3 = { .kind = AX_TY_FN, .fn = { .ret_type = arr16_ty, .param_count = 1, .param_types = params3 } };
    AxAbiSig sig3 = ax_abi_win64.classify(&fn3, &interner, &arena);
    assert(sig3.ret.loc.kind == AX_ABI_LOC_INDIRECT && sig3.ret.loc.reg == 1); // Hidden pointer in RCX
    assert(sig3.arg_count == 1);
    assert(sig3.args[0].loc.kind == AX_ABI_LOC_REG && sig3.args[0].loc.reg == 2); // First actual arg shifted to RDX

    printf("cdriver_abi pass\n");
    ax_arena_destroy(&arena);
    ax_type_interner_free(&interner);
    return 0;
}
