#include "types/layout/layout.h"
#include "abi.h"

static const uint32_t ARG_REGS[] = { 1, 2, 8, 9 }; // RCX, RDX, R8, R9

static AxAbiSig win64_classify(const AxType *fn_ty, TypeInterner *interner, AxArena *arena) {
    AxAbiSig sig = {0};
    if (fn_ty->kind != AX_TY_FN) return sig;
    
    sig.shadow_space = 32;
    uint32_t stack_offset = 32;
    uint32_t arg_idx = 0; // index in ARG_REGS
    
    // Check return type
    uint32_t ret_size = ax_type_size(fn_ty->fn.ret_type, interner);
    bool ret_in_mem = (ret_size > 8 || (ret_size != 1 && ret_size != 2 && ret_size != 4 && ret_size != 8 && ret_size != 0));
    
    if (ret_in_mem) {
        sig.ret.loc.kind = AX_ABI_LOC_INDIRECT;
        sig.ret.loc.reg = ARG_REGS[arg_idx++]; // RCX gets the hidden pointer
        sig.ret.ty = fn_ty->fn.ret_type;
    } else {
        sig.ret.loc.kind = AX_ABI_LOC_REG;
        sig.ret.loc.reg = 0; // RAX
        sig.ret.ty = fn_ty->fn.ret_type;
    }
    
    sig.arg_count = fn_ty->fn.param_count;
    if (sig.arg_count > 0) {
        sig.args = AX_ARENA_NEW_ARRAY(arena, AxAbiArg, sig.arg_count);
    }
    
    for (size_t i = 0; i < sig.arg_count; i++) {
        TypeId pty = fn_ty->fn.param_types[i];
        uint32_t psize = ax_type_size(pty, interner);
        bool in_mem = (psize > 8 || (psize != 1 && psize != 2 && psize != 4 && psize != 8 && psize != 0));
        
        sig.args[i].ty = pty;
        if (in_mem) {
            // Passed by reference (pointer in reg or stack)
            if (arg_idx < 4) {
                sig.args[i].loc.kind = AX_ABI_LOC_INDIRECT;
                sig.args[i].loc.reg = ARG_REGS[arg_idx++];
            } else {
                sig.args[i].loc.kind = AX_ABI_LOC_INDIRECT;
                sig.args[i].loc.offset = stack_offset;
                stack_offset += 8;
                arg_idx++;
            }
        } else {
            // Passed by value
            if (arg_idx < 4) {
                sig.args[i].loc.kind = AX_ABI_LOC_REG;
                sig.args[i].loc.reg = ARG_REGS[arg_idx++];
            } else {
                sig.args[i].loc.kind = AX_ABI_LOC_STACK;
                sig.args[i].loc.offset = stack_offset;
                stack_offset += 8;
                arg_idx++;
            }
        }
    }
    
    sig.stack_args_size = stack_offset > 32 ? stack_offset - 32 : 0;
    return sig;
}

const AxAbi ax_abi_win64 = {
    .classify = win64_classify
};
