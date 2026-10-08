#include "types/layout/layout.h"
#include "isel.h"
#include <stdlib.h>

static void emit(AxX64MIBody *mi, AxX64MIBb *mbb, AxX64MIOpcode opc, AxX64Op op1, AxX64Op op2) {
    AxX64MI *inst = ax_x64_mi_new(&mi->arena, opc);
    if (op1.kind != AX_X64_OP_NONE) ax_x64_mi_add_op(inst, op1);
    if (op2.kind != AX_X64_OP_NONE) ax_x64_mi_add_op(inst, op2);
    if (mbb->last_inst) {
        mbb->last_inst->next = inst;
        mbb->last_inst = inst;
    } else {
        mbb->first_inst = mbb->last_inst = inst;
    }
}


static void emit_trunc(AxX64MIBody *mi, AxX64MIBb *mbb, TypeId ty, TypeInterner *interner, uint8_t scratch_reg) {
    uint32_t size = ax_type_size(ty, interner);
    const AxType *t = ax_type_get(interner, ty);
    bool is_signed = true;
    if (t) {
        if (t->kind == 10 /* AX_TY_U8 */ || t->kind == 11 /* AX_TY_U16 */ || t->kind == 12 /* AX_TY_U32 */ || t->kind == 13 /* AX_TY_U64 */ || t->kind == 14 /* AX_TY_USIZE */ || t->kind == 3 /* AX_TY_BOOL */) {
            is_signed = false;
        }
    }

    if (size == 1) {
        if (is_signed) {
            emit(mi, mbb, AX_X64_MI_SHL, ax_x64_op_reg(scratch_reg), ax_x64_op_imm(56));
            emit(mi, mbb, AX_X64_MI_SAR, ax_x64_op_reg(scratch_reg), ax_x64_op_imm(56));
        } else {
            emit(mi, mbb, AX_X64_MI_AND, ax_x64_op_reg(scratch_reg), ax_x64_op_imm(0xFF));
        }
    } else if (size == 2) {
        if (is_signed) {
            emit(mi, mbb, AX_X64_MI_SHL, ax_x64_op_reg(scratch_reg), ax_x64_op_imm(48));
            emit(mi, mbb, AX_X64_MI_SAR, ax_x64_op_reg(scratch_reg), ax_x64_op_imm(48));
        } else {
            emit(mi, mbb, AX_X64_MI_AND, ax_x64_op_reg(scratch_reg), ax_x64_op_imm(0xFFFF));
        }
    } else if (size == 4) {
        if (is_signed) {
            emit(mi, mbb, AX_X64_MI_SHL, ax_x64_op_reg(scratch_reg), ax_x64_op_imm(32));
            emit(mi, mbb, AX_X64_MI_SAR, ax_x64_op_reg(scratch_reg), ax_x64_op_imm(32));
        } else {
            emit(mi, mbb, AX_X64_MI_SHL, ax_x64_op_reg(scratch_reg), ax_x64_op_imm(32));
            emit(mi, mbb, AX_X64_MI_SHR, ax_x64_op_reg(scratch_reg), ax_x64_op_imm(32));
        }
    }
}

AxX64MIBody *ax_x64_isel(const AxLirBody *lir, TypeInterner *interner) {
    (void)interner; // for size lookups later
    AxArena arena;
    ax_arena_init(&arena, 0);
    AxX64MIBody *mi = AX_ARENA_NEW(&arena, AxX64MIBody);
    mi->arena = arena;
    
    mi->shadow_space = lir->frame_req.max_outgoing_args_bytes;
    mi->stack_args_size = 0; // passed down if we need it
    
    mi->bb_count = lir->bb_count;
    if (mi->bb_count > 0) {
        mi->bbs = AX_ARENA_NEW_ARRAY(&mi->arena, AxX64MIBb, mi->bb_count);
    }
    
    // Simple vreg mapping to stack slots (naive ISEL)
    uint32_t slot_offset = lir->slot_count; 
    
    for (size_t b = 0; b < lir->bb_count; b++) {
        const AxLirBb *lbb = &lir->bbs[b];
        AxX64MIBb *mbb = &mi->bbs[b];
        mbb->id = b; // assume bb index is ID
        mbb->first_inst = NULL;
        mbb->last_inst = NULL;
        
        for (size_t i = 0; i < lbb->inst_count; i++) {
            const AxLirInst *inst = &lbb->insts[i];
            
            /* BOOTSTRAP-SHORTCUT(E15.8): Hardcoded RAX (0) and RCX (1) as scratch registers for naive isel.
               Retired by linear-scan register allocator. */
            switch (inst->kind) {
                case AX_LIR_INST_CONST:
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(0 /*RAX*/), ax_x64_op_imm(inst->constant.val));
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_frame(slot_offset + inst->dest.v, 0), ax_x64_op_reg(0));
                    break;
                case AX_LIR_INST_ADD:
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(0), ax_x64_op_frame(slot_offset + inst->binary.lhs.v, 0));
                    emit(mi, mbb, AX_X64_MI_ADD, ax_x64_op_reg(0), ax_x64_op_frame(slot_offset + inst->binary.rhs.v, 0));
                    emit_trunc(mi, mbb, lir->vregs[inst->dest.v].ty, interner, 0);
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_frame(slot_offset + inst->dest.v, 0), ax_x64_op_reg(0));
                    break;
                case AX_LIR_INST_SUB:
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(0), ax_x64_op_frame(slot_offset + inst->binary.lhs.v, 0));
                    emit(mi, mbb, AX_X64_MI_SUB, ax_x64_op_reg(0), ax_x64_op_frame(slot_offset + inst->binary.rhs.v, 0));
                    emit_trunc(mi, mbb, lir->vregs[inst->dest.v].ty, interner, 0);
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_frame(slot_offset + inst->dest.v, 0), ax_x64_op_reg(0));
                    break;

                case AX_LIR_INST_BIT_AND:
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(0), ax_x64_op_frame(slot_offset + inst->binary.lhs.v, 0));
                    emit(mi, mbb, AX_X64_MI_AND, ax_x64_op_reg(0), ax_x64_op_frame(slot_offset + inst->binary.rhs.v, 0));
                    emit_trunc(mi, mbb, lir->vregs[inst->dest.v].ty, interner, 0);
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_frame(slot_offset + inst->dest.v, 0), ax_x64_op_reg(0));
                    break;
                case AX_LIR_INST_BIT_OR:
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(0), ax_x64_op_frame(slot_offset + inst->binary.lhs.v, 0));
                    emit(mi, mbb, AX_X64_MI_OR, ax_x64_op_reg(0), ax_x64_op_frame(slot_offset + inst->binary.rhs.v, 0));
                    emit_trunc(mi, mbb, lir->vregs[inst->dest.v].ty, interner, 0);
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_frame(slot_offset + inst->dest.v, 0), ax_x64_op_reg(0));
                    break;
                case AX_LIR_INST_BIT_XOR:
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(0), ax_x64_op_frame(slot_offset + inst->binary.lhs.v, 0));
                    emit(mi, mbb, AX_X64_MI_XOR, ax_x64_op_reg(0), ax_x64_op_frame(slot_offset + inst->binary.rhs.v, 0));
                    emit_trunc(mi, mbb, lir->vregs[inst->dest.v].ty, interner, 0);
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_frame(slot_offset + inst->dest.v, 0), ax_x64_op_reg(0));
                    break;


                case AX_LIR_INST_SHL:
                case AX_LIR_INST_SHR:
                case AX_LIR_INST_SAR:
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(0 /*RAX*/), ax_x64_op_frame(slot_offset + inst->binary.lhs.v, 0));
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(1 /*RCX*/), ax_x64_op_frame(slot_offset + inst->binary.rhs.v, 0));
                    emit(mi, mbb, inst->kind == AX_LIR_INST_SHL ? AX_X64_MI_SHL : (inst->kind == AX_LIR_INST_SAR ? AX_X64_MI_SAR : AX_X64_MI_SHR), ax_x64_op_reg(0), ax_x64_op_reg(1));
                    emit_trunc(mi, mbb, lir->vregs[inst->dest.v].ty, interner, 0);
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_frame(slot_offset + inst->dest.v, 0), ax_x64_op_reg(0));
                    break;
                case AX_LIR_INST_MUL:
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(0), ax_x64_op_frame(slot_offset + inst->binary.lhs.v, 0));
                    emit(mi, mbb, AX_X64_MI_IMUL, ax_x64_op_reg(0), ax_x64_op_frame(slot_offset + inst->binary.rhs.v, 0));
                    emit_trunc(mi, mbb, lir->vregs[inst->dest.v].ty, interner, 0);
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_frame(slot_offset + inst->dest.v, 0), ax_x64_op_reg(0));
                    break;
                                  case AX_LIR_INST_ICMP_EQ:
                  case AX_LIR_INST_ICMP_NE:
                  case AX_LIR_INST_ICMP_SLT:
                  case AX_LIR_INST_ICMP_SLE:
                  case AX_LIR_INST_ICMP_SGT:
                  case AX_LIR_INST_ICMP_SGE:
                  case AX_LIR_INST_ICMP_ULT:
                  case AX_LIR_INST_ICMP_ULE:
                  case AX_LIR_INST_ICMP_UGT:
                  case AX_LIR_INST_ICMP_UGE: {
                      emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(0), ax_x64_op_frame(slot_offset + inst->binary.lhs.v, 0));
                      emit(mi, mbb, AX_X64_MI_CMP, ax_x64_op_reg(0), ax_x64_op_frame(slot_offset + inst->binary.rhs.v, 0));
                      uint8_t cond = AX_CC_E;
                      if (inst->kind == AX_LIR_INST_ICMP_NE) cond = AX_CC_NE;
                      else if (inst->kind == AX_LIR_INST_ICMP_SLT) cond = AX_CC_L;
                      else if (inst->kind == AX_LIR_INST_ICMP_SLE) cond = AX_CC_LE;
                      else if (inst->kind == AX_LIR_INST_ICMP_SGT) cond = AX_CC_G;
                      else if (inst->kind == AX_LIR_INST_ICMP_SGE) cond = AX_CC_GE;
                      else if (inst->kind == AX_LIR_INST_ICMP_ULT) cond = AX_CC_B;
                      else if (inst->kind == AX_LIR_INST_ICMP_ULE) cond = AX_CC_BE;
                      else if (inst->kind == AX_LIR_INST_ICMP_UGT) cond = AX_CC_A;
                      else if (inst->kind == AX_LIR_INST_ICMP_UGE) cond = AX_CC_AE;
                      emit(mi, mbb, AX_X64_MI_SETCC, ax_x64_op_imm(cond), ax_x64_op_reg(0));
                      emit(mi, mbb, AX_X64_MI_AND, ax_x64_op_reg(0), ax_x64_op_imm(0xFF));
                      emit_trunc(mi, mbb, lir->vregs[inst->dest.v].ty, interner, 0);
                      emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_frame(slot_offset + inst->dest.v, 0), ax_x64_op_reg(0));
                      break;
                  }
                  case AX_LIR_INST_DIV:
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(0), ax_x64_op_frame(slot_offset + inst->binary.lhs.v, 0));
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(2 /*RDX*/), ax_x64_op_reg(0 /*RAX*/));
                    emit(mi, mbb, AX_X64_MI_SAR, ax_x64_op_reg(2 /*RDX*/), ax_x64_op_imm(63));
                    emit(mi, mbb, AX_X64_MI_IDIV, ax_x64_op_frame(slot_offset + inst->binary.rhs.v, 0), (AxX64Op){0});
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_frame(slot_offset + inst->dest.v, 0), ax_x64_op_reg(0));
                    break;
                case AX_LIR_INST_REM:
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(0), ax_x64_op_frame(slot_offset + inst->binary.lhs.v, 0));
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(2 /*RDX*/), ax_x64_op_reg(0 /*RAX*/));
                    emit(mi, mbb, AX_X64_MI_SAR, ax_x64_op_reg(2 /*RDX*/), ax_x64_op_imm(63));
                    emit(mi, mbb, AX_X64_MI_IDIV, ax_x64_op_frame(slot_offset + inst->binary.rhs.v, 0), (AxX64Op){0});
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_frame(slot_offset + inst->dest.v, 0), ax_x64_op_reg(2 /*RDX*/));
                    break;
                case AX_LIR_INST_NEG:
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(0), ax_x64_op_frame(slot_offset + inst->unary.operand.v, 0));
                    // we can't use AX_X64_MI_NEG yet because it's not in mi.h, wait!
                    // I will just use SUB from 0:
                    // mov rax, 0; sub rax, [operand]
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(1), ax_x64_op_imm(0));
                    emit(mi, mbb, AX_X64_MI_SUB, ax_x64_op_reg(1), ax_x64_op_reg(0));
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_frame(slot_offset + inst->dest.v, 0), ax_x64_op_reg(1));
                    break;
                case AX_LIR_INST_BITNOT:
                    // NOT x == -1 - x, so we use SUB which is fully supported
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(10), ax_x64_op_imm(-1));
                    emit(mi, mbb, AX_X64_MI_SUB, ax_x64_op_reg(10), ax_x64_op_frame(slot_offset + inst->unary.operand.v, 0));
                    emit_trunc(mi, mbb, lir->vregs[inst->dest.v].ty, interner, 10);
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_frame(slot_offset + inst->dest.v, 0), ax_x64_op_reg(10));
                    break;
                  case AX_LIR_INST_ABI_ARG:
                      if (inst->dest.v != 0xFFFFFFFF) {
                          if (inst->abi_arg.loc_kind == 0) { // REG
                              emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_frame(slot_offset + inst->dest.v, 0), ax_x64_op_reg(inst->abi_arg.loc_reg_or_offset));
                          } else if (inst->abi_arg.loc_kind == 1) { // STACK
                              AxX64Op mem = { .kind = AX_X64_OP_MEM, .mem = { .base = 5 /*RBP*/, .index = AX_REG_NONE, .scale = 1, .disp = 16 + inst->abi_arg.loc_reg_or_offset, .is_rip = false } };
                              emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(0), mem);
                              emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_frame(slot_offset + inst->dest.v, 0), ax_x64_op_reg(0));
                          }
                      } else {
                          if (inst->abi_arg.loc_kind == 0) { // REG
                              emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(inst->abi_arg.loc_reg_or_offset), ax_x64_op_frame(slot_offset + inst->abi_arg.val.v, 0));
                          } else if (inst->abi_arg.loc_kind == 1) { // STACK
                              AxX64Op mem = { .kind = AX_X64_OP_MEM, .mem = { .base = 4 /*RSP*/, .index = AX_REG_NONE, .scale = 1, .disp = inst->abi_arg.loc_reg_or_offset, .is_rip = false } };
                              emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(0), ax_x64_op_frame(slot_offset + inst->abi_arg.val.v, 0));
                              emit(mi, mbb, AX_X64_MI_MOV, mem, ax_x64_op_reg(0));
                          }
                      }
                      break;
                                  case AX_LIR_INST_CALL:
                      emit(mi, mbb, AX_X64_MI_CALL, (AxX64Op){0}, (AxX64Op){0});
                      mbb->last_inst->msg = inst->call.sym_name;
                      break;
                  case AX_LIR_INST_ABI_RESULT:
                    if (inst->abi_result.loc_kind == 0) { // REG
                        emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_frame(slot_offset + inst->dest.v, 0), ax_x64_op_reg(inst->abi_result.loc_reg_or_offset));
                    }
                    break;
                case AX_LIR_INST_STACK_ADDR:
                    emit(mi, mbb, AX_X64_MI_LEA, ax_x64_op_reg(0 /*RAX*/), ax_x64_op_frame(inst->stack_addr.slot.v, 0));
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_frame(slot_offset + inst->dest.v, 0), ax_x64_op_reg(0));
                    break;
                case AX_LIR_INST_LOAD:
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(0 /*RAX*/), ax_x64_op_frame(slot_offset + inst->load.ptr.v, 0));
                    {
                        AxX64Op mem = { .kind = AX_X64_OP_MEM, .mem = { .base = 0 /*RAX*/, .index = AX_REG_NONE, .scale = 1, .disp = 0, .is_rip = false } };
                        emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(1 /*RCX*/), mem);
                        emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_frame(slot_offset + inst->dest.v, 0), ax_x64_op_reg(1));
                    }
                    break;
                case AX_LIR_INST_STORE:
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(0 /*RAX*/), ax_x64_op_frame(slot_offset + inst->store.ptr.v, 0));
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(1 /*RCX*/), ax_x64_op_frame(slot_offset + inst->store.val.v, 0));
                    {
                        AxX64Op mem = { .kind = AX_X64_OP_MEM, .mem = { .base = 0 /*RAX*/, .index = AX_REG_NONE, .scale = 1, .disp = 0, .is_rip = false } };
                        emit(mi, mbb, AX_X64_MI_MOV, mem, ax_x64_op_reg(1));
                    }
                    break;
                default:
                    break;
            }
        }
        
        switch (lbb->terminator.kind) {
                          case AX_LIR_TERM_SWITCH: {
                  emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(10), ax_x64_op_frame(slot_offset + lbb->terminator.switch_int.cond.v, 0));
                  for (size_t k = 0; k < lbb->terminator.switch_int.count; k++) {
                      emit(mi, mbb, AX_X64_MI_CMP, ax_x64_op_reg(10), ax_x64_op_imm(lbb->terminator.switch_int.targets[k].value));
                      emit(mi, mbb, AX_X64_MI_JCC, ax_x64_op_imm(AX_CC_E), ax_x64_op_imm(lbb->terminator.switch_int.targets[k].target.v));
                  }
                  emit(mi, mbb, AX_X64_MI_JMP, ax_x64_op_imm(lbb->terminator.switch_int.otherwise.v), (AxX64Op){0});
                  break;
              }
              case AX_LIR_TERM_ASSERT: {
                  emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(0 /*RAX*/), ax_x64_op_frame(slot_offset + lbb->terminator.assert_term.cond.v, 0));
                  emit(mi, mbb, AX_X64_MI_CMP, ax_x64_op_reg(0 /*RAX*/), ax_x64_op_imm(1));
                  emit(mi, mbb, AX_X64_MI_ASSERT, ax_x64_op_imm(lbb->terminator.assert_term.target.v), (AxX64Op){0});
                  mbb->last_inst->msg = lbb->terminator.assert_term.msg;
                  break;
              }
              case AX_LIR_TERM_JMP:
                  emit(mi, mbb, AX_X64_MI_JMP, ax_x64_op_imm(lbb->terminator.jmp_target.v), (AxX64Op){0});
                  break;
              case AX_LIR_TERM_RETURN: {
                  const AxType *ret_ty = ax_type_get(interner, lir->slots[0].ty);
                if (ret_ty && ret_ty->kind == AX_TY_UNIT) {
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(0 /*RAX*/), ax_x64_op_imm(0));
                } else {
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(0 /*RAX*/), ax_x64_op_frame(0, 0));
                }
                emit(mi, mbb, AX_X64_MI_RET, (AxX64Op){0}, (AxX64Op){0});
                break;
            }
            default:
                break;
        }
    }
    
    return mi;
}
