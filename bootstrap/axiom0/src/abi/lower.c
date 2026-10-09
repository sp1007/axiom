#include "abi.h"

void ax_lir_lower_abi(AxLirBody *body, TypeInterner *interner, const AxAbi *abi, const AxType *fn_ty) {
    AxArena arena;
    ax_arena_init(&arena, 0);
    
    AxAbiSig sig = abi->classify(fn_ty, interner, &arena);
    
    body->frame_req.max_outgoing_args_bytes = sig.shadow_space; 
    body->frame_req.requires_16_byte_alignment = true;
    
    for (size_t b = 0; b < body->bb_count; b++) {
        AxLirBb *bb = &body->bbs[b];
        for (size_t i = 0; i < bb->inst_count; i++) {
            AxLirInst *inst = &bb->insts[i];
            if (inst->kind == AX_LIR_INST_ABI_ARG) {
                uint32_t idx = inst->abi_arg.index;
                if (inst->dest.v != 0xFFFFFFFF) { 
                    if (idx < sig.arg_count) {
                        inst->abi_arg.loc_kind = sig.args[idx].loc.kind;
                        if (sig.args[idx].loc.kind == AX_ABI_LOC_STACK) {
                            inst->abi_arg.loc_reg_or_offset = sig.args[idx].loc.offset;
                        } else {
                            inst->abi_arg.loc_reg_or_offset = sig.args[idx].loc.reg;
                        }
                    }
                } else { 
                    AxLirInst *call_inst = NULL;
                    for (size_t j = i + 1; j < bb->inst_count; j++) {
                        if (bb->insts[j].kind == AX_LIR_INST_CALL) { call_inst = &bb->insts[j]; break; }
                    }
                    if (call_inst) {
                        AxArena temp_arena; ax_arena_init(&temp_arena, 0);
                        const AxType *callee = ax_type_get(interner, call_inst->call.callee_ty);
                        if (callee) {
                            AxAbiSig call_sig = abi->classify(callee, interner, &temp_arena);
                            if (idx < call_sig.arg_count) {
                                inst->abi_arg.loc_kind = call_sig.args[idx].loc.kind;
                                if (call_sig.args[idx].loc.kind == AX_ABI_LOC_STACK) {
                                    inst->abi_arg.loc_reg_or_offset = call_sig.args[idx].loc.offset;
                                } else {
                                    inst->abi_arg.loc_reg_or_offset = call_sig.args[idx].loc.reg;
                                }
                            }
                            if (call_sig.shadow_space > body->frame_req.max_outgoing_args_bytes) {
                                body->frame_req.max_outgoing_args_bytes = call_sig.shadow_space;
                            }
                        }
                        ax_arena_destroy(&temp_arena);
                    }
                } 
            } else if (inst->kind == AX_LIR_INST_ABI_RESULT) {
                AxLirInst *call_inst = NULL;
                for (size_t j = i; j > 0; j--) {
                    if (bb->insts[j - 1].kind == AX_LIR_INST_CALL) { call_inst = &bb->insts[j - 1]; break; }
                }
                if (call_inst) {
                    AxArena temp_arena; ax_arena_init(&temp_arena, 0);
                    const AxType *callee = ax_type_get(interner, call_inst->call.callee_ty);
                    if (callee) {
                        AxAbiSig call_sig = abi->classify(callee, interner, &temp_arena);
                        inst->abi_result.loc_kind = call_sig.ret.loc.kind;
                        if (call_sig.ret.loc.kind == AX_ABI_LOC_STACK) {
                            inst->abi_result.loc_reg_or_offset = call_sig.ret.loc.offset;
                        } else {
                            inst->abi_result.loc_reg_or_offset = call_sig.ret.loc.reg;
                        }
                    }
                    ax_arena_destroy(&temp_arena);
                } else {
                    inst->abi_result.loc_kind = sig.ret.loc.kind;
                    if (sig.ret.loc.kind == AX_ABI_LOC_STACK) {
                        inst->abi_result.loc_reg_or_offset = sig.ret.loc.offset;
                    } else {
                        inst->abi_result.loc_reg_or_offset = sig.ret.loc.reg;
                    }
                }
            }
        }
    }
    
    ax_arena_destroy(&arena);
}
