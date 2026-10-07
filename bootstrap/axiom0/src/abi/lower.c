#include "abi.h"

void ax_lir_lower_abi(AxLirBody *body, TypeInterner *interner, const AxAbi *abi, const AxType *fn_ty) {
    AxArena arena;
    ax_arena_init(&arena, 0);
    
    AxAbiSig sig = abi->classify(fn_ty, interner, &arena);
    
    // Set frame requirements
    body->frame_req.max_outgoing_args_bytes = sig.shadow_space; // for now, assuming calls take this
    body->frame_req.requires_16_byte_alignment = true;
    
    // Update instructions
    for (size_t b = 0; b < body->bb_count; b++) {
        AxLirBb *bb = &body->bbs[b];
        for (size_t i = 0; i < bb->inst_count; i++) {
            AxLirInst *inst = &bb->insts[i];
            if (inst->kind == AX_LIR_INST_ABI_ARG) {
                uint32_t idx = inst->abi_arg.index;
                if (idx < sig.arg_count) {
                    inst->abi_arg.loc_kind = sig.args[idx].loc.kind;
                    if (sig.args[idx].loc.kind == AX_ABI_LOC_STACK) {
                        inst->abi_arg.loc_reg_or_offset = sig.args[idx].loc.offset;
                    } else {
                        inst->abi_arg.loc_reg_or_offset = sig.args[idx].loc.reg;
                    }
                }
            } else if (inst->kind == AX_LIR_INST_ABI_RESULT) {
                inst->abi_result.loc_kind = sig.ret.loc.kind;
                if (sig.ret.loc.kind == AX_ABI_LOC_STACK) {
                    inst->abi_result.loc_reg_or_offset = sig.ret.loc.offset;
                } else {
                    inst->abi_result.loc_reg_or_offset = sig.ret.loc.reg;
                }
            }
        }
    }
    
    ax_arena_destroy(&arena);
}
