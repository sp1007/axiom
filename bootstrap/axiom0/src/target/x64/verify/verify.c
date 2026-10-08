#include "verify.h"
#include "kernel/base.h"

void ax_x64_verify(const AxX64MIBody *body, const AxX64FrameLayout *layout) {
    if (body->shadow_space > 0) {
        if (body->shadow_space < 32) {
            AX_ICE("Machine IR verifier: shadow space is present but < 32 bytes");
        }
        if ((layout->frame_size + 56) % 16 != 0) {
            AX_ICE("Machine IR verifier: 16-byte alignment violated at call site");
        }
    }
    
    if (layout->frame_size < body->shadow_space) {
        AX_ICE("Machine IR verifier: frame size consistency violated");
    }
    
    for (size_t b = 0; b < body->bb_count; b++) {
        AxX64MIBb *mbb = &body->bbs[b];
        for (AxX64MI *inst = mbb->first_inst; inst != NULL; inst = inst->next) {
            if (inst->op_count == 2) {
                AxX64OpKind k0 = inst->ops[0].kind;
                AxX64OpKind k1 = inst->ops[1].kind;
                
                if (k0 == AX_X64_OP_MEM && k1 == AX_X64_OP_MEM) {
                    AX_ICE("Machine IR verifier: illegal instruction form (mem, mem)");
                }
                
                if (inst->opcode == AX_X64_MI_MOV || inst->opcode == AX_X64_MI_ADD || inst->opcode == AX_X64_MI_SUB ||
                    inst->opcode == AX_X64_MI_AND || inst->opcode == AX_X64_MI_OR || inst->opcode == AX_X64_MI_XOR) {
                    if (k0 == AX_X64_OP_REG && k1 == AX_X64_OP_REG) continue;
                    if (k0 == AX_X64_OP_REG && k1 == AX_X64_OP_MEM) continue;
                    if (k0 == AX_X64_OP_MEM && k1 == AX_X64_OP_REG) continue;
                    if (k0 == AX_X64_OP_REG && k1 == AX_X64_OP_IMM) continue;
                    if (k0 == AX_X64_OP_MEM && k1 == AX_X64_OP_IMM) continue;
                    
                    AX_ICE("Machine IR verifier: illegal operand form for opcode");
                }
                
                if (inst->opcode == AX_X64_MI_IMUL) {
                    if (k0 == AX_X64_OP_REG && k1 == AX_X64_OP_REG) continue;
                    if (k0 == AX_X64_OP_REG && k1 == AX_X64_OP_MEM) continue;
                    
                    AX_ICE("Machine IR verifier: illegal operand form for imul");
                }
                
                if (inst->opcode == AX_X64_MI_LEA) {
                    if (k0 == AX_X64_OP_REG && (k1 == AX_X64_OP_MEM || k1 == AX_X64_OP_SYM)) continue;
                    
                    AX_ICE("Machine IR verifier: illegal operand form for lea");
                }
                
                if (inst->opcode == AX_X64_MI_SHL || inst->opcode == AX_X64_MI_SAR || inst->opcode == AX_X64_MI_SHR) {
                    if (k0 == AX_X64_OP_REG && k1 == AX_X64_OP_IMM) continue;
                    if (k0 == AX_X64_OP_REG && k1 == AX_X64_OP_REG) {
                        if (inst->ops[1].reg != AX_REG_RCX) {
                            AX_ICE("Machine IR verifier: wrong register class");
                        }
                        continue;
                    }
                    if (k0 == AX_X64_OP_MEM && k1 == AX_X64_OP_IMM) continue;
                    if (k0 == AX_X64_OP_MEM && k1 == AX_X64_OP_REG) {
                        if (inst->ops[1].reg != AX_REG_RCX) {
                            AX_ICE("Machine IR verifier: wrong register class");
                        }
                        continue;
                    }
                    AX_ICE("Machine IR verifier: illegal operand form for shift");
                }
            } else if (inst->op_count == 1) {
                if (inst->opcode == AX_X64_MI_IDIV && inst->ops[0].kind == AX_X64_OP_IMM) {
                    AX_ICE("Machine IR verifier: illegal operand form for idiv");
                }
            }
        }
    }
}
