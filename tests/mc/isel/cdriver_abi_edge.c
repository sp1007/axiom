#include <stdio.h>
#include <assert.h>
#include "abi/abi.h"

int main() {
    TypeInterner interner;
    ax_type_interner_init(&interner);
    AxArena arena;
    ax_arena_init(&arena, 0);

    // Test a struct of size 3 (passed by reference in MS ABI)
    TypeId arr3_ty = ax_intern_type(&interner, &(AxType){ .kind = AX_TY_ARRAY, .array = { .elem = interner.t_i8, .len = 3 } });
    TypeId params[1] = { arr3_ty };
    AxType fn = { .kind = AX_TY_FN, .fn = { .ret_type = interner.t_unit, .param_count = 1, .param_types = params } };
    
    AxAbiSig sig = ax_abi_win64.classify(&fn, &interner, &arena);
    assert(sig.arg_count == 1);
    // Size 3 should be passed by indirect reference, pointer in RCX
    assert(sig.args[0].loc.kind == AX_ABI_LOC_INDIRECT && sig.args[0].loc.reg == 1); 

    // Test an aggregate of size exactly 4 (passed by value)
    TypeId arr4_ty = ax_intern_type(&interner, &(AxType){ .kind = AX_TY_ARRAY, .array = { .elem = interner.t_i8, .len = 4 } });
    TypeId params_4[1] = { arr4_ty };
    AxType fn_4 = { .kind = AX_TY_FN, .fn = { .ret_type = interner.t_unit, .param_count = 1, .param_types = params_4 } };
    
    AxAbiSig sig_4 = ax_abi_win64.classify(&fn_4, &interner, &arena);
    assert(sig_4.arg_count == 1);
    // Size 4 should be passed by value, in RCX
    assert(sig_4.args[0].loc.kind == AX_ABI_LOC_REG && sig_4.args[0].loc.reg == 1); 

    // Test an aggregate return of size 5 (returned via hidden pointer)
    TypeId params_empty[1] = { interner.t_unit };
    AxType fn_ret5 = { .kind = AX_TY_FN, .fn = { .ret_type = arr3_ty, .param_count = 0, .param_types = params_empty } };
    
    AxAbiSig sig_ret5 = ax_abi_win64.classify(&fn_ret5, &interner, &arena);
    assert(sig_ret5.ret.loc.kind == AX_ABI_LOC_INDIRECT && sig_ret5.ret.loc.reg == 1); // Hidden pointer in RCX

    printf("cdriver_abi_edge pass\n");
    ax_arena_destroy(&arena);
    ax_type_interner_free(&interner);
    return 0;
}
