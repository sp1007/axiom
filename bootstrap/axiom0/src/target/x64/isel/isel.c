#include "types/layout/layout.h"
#include "isel.h"
#include "kernel/base.h"
#include <stdlib.h>

static void emit_sz(AxX64MIBody *mi, AxX64MIBb *mbb, AxX64MIOpcode opc, uint8_t sz, AxX64Op op1, AxX64Op op2) {
    AxX64MI *inst = ax_x64_mi_new(&mi->arena, opc);
    inst->sz = sz;
    if (op1.kind != AX_X64_OP_NONE) ax_x64_mi_add_op(inst, op1);
    if (op2.kind != AX_X64_OP_NONE) ax_x64_mi_add_op(inst, op2);
    if (mbb->last_inst) {
        mbb->last_inst->next = inst;
        mbb->last_inst = inst;
    } else {
        mbb->first_inst = mbb->last_inst = inst;
    }
}

static void emit(AxX64MIBody *mi, AxX64MIBb *mbb, AxX64MIOpcode opc, AxX64Op op1, AxX64Op op2) {
    emit_sz(mi, mbb, opc, 8, op1, op2);
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
    
    bool callee_ret_in_mem = false;
    if (lir->slot_count > 0) {
        uint32_t ret_size = ax_type_size(lir->slots[0].ty, interner);
        callee_ret_in_mem = (ret_size > 8 || (ret_size != 1 && ret_size != 2 && ret_size != 4 && ret_size != 8 && ret_size != 0));
    }
    
    for (size_t b = 0; b < lir->bb_count; b++) {
        const AxLirBb *lbb = &lir->bbs[b];
        AxX64MIBb *mbb = &mi->bbs[b];
        mbb->id = b; // assume bb index is ID
        mbb->first_inst = NULL;
        mbb->last_inst = NULL;
        
        if (b == 0 && callee_ret_in_mem) {
            emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_frame(0, 0), ax_x64_op_reg(1 /*RCX*/));
        }
        
        for (size_t i = 0; i < lbb->inst_count; i++) {
            const AxLirInst *inst = &lbb->insts[i];
            
            /* BOOTSTRAP-SHORTCUT(E15.8): Hardcoded RAX (0) and RCX (1) as scratch registers for naive isel.
               Retired by linear-scan register allocator. */
            switch (inst->kind) {
                case AX_LIR_INST_CONST:
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(0 /*RAX*/), ax_x64_op_imm(inst->constant.val));
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_frame(slot_offset + inst->dest.v, 0), ax_x64_op_reg(0));
                    break;
                case AX_LIR_INST_CONST_STR: {
                    uint32_t sym_id = (uint32_t)(100000 + mi->string_count);
                    if (mi->string_count >= mi->string_cap) {
                        mi->string_cap = mi->string_cap == 0 ? 16 : mi->string_cap * 2;
                        AxX64MIStr *new_strings = malloc(mi->string_cap * sizeof(AxX64MIStr));
                        if (mi->strings) {
                            memcpy(new_strings, mi->strings, mi->string_count * sizeof(AxX64MIStr));
                            free(mi->strings);
                        }
                        mi->strings = new_strings;
                    }
                    mi->strings[mi->string_count].bytes = inst->const_str.bytes;
                    mi->strings[mi->string_count].len = inst->const_str.len;
                    mi->strings[mi->string_count].sym_id = sym_id;
                    mi->string_count++;

                    emit(mi, mbb, AX_X64_MI_LEA, ax_x64_op_reg(0 /*RAX*/), ax_x64_op_sym(sym_id));
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_frame(slot_offset + inst->dest.v, 0), ax_x64_op_reg(0));
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(0 /*RAX*/), ax_x64_op_imm(inst->const_str.len));
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_frame(slot_offset + inst->dest.v, 8), ax_x64_op_reg(0));
                    break;
                }
                case AX_LIR_INST_FN_ADDR: {
                    emit(mi, mbb, AX_X64_MI_LEA, ax_x64_op_reg(0 /*RAX*/), (AxX64Op){ .kind = AX_X64_OP_SYM, .sym = 0 });
                    mbb->last_inst->msg = inst->fn_addr.sym_name;
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_frame(slot_offset + inst->dest.v, 0), ax_x64_op_reg(0));
                    break;
                }
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
                  case AX_LIR_INST_UADD_OVERFLOW:
                case AX_LIR_INST_USUB_OVERFLOW:
                case AX_LIR_INST_UMUL_OVERFLOW: {
                    int is_64 = (inst->overflow_op.bit_width == 64);
                    
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(0 /*RAX*/), ax_x64_op_frame(slot_offset + inst->overflow_op.lhs.v, 0));
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(2 /*RCX*/), ax_x64_op_frame(slot_offset + inst->overflow_op.rhs.v, 0));
                    
                    if (!is_64) {
                        uint64_t mask = 0;
                        uint64_t uint_max = 0;
                        if (inst->overflow_op.bit_width == 8) { mask = 0xFF; uint_max = 0xFF; }
                        else if (inst->overflow_op.bit_width == 16) { mask = 0xFFFF; uint_max = 0xFFFF; }
                        else if (inst->overflow_op.bit_width == 32) { mask = 0xFFFFFFFF; uint_max = 0xFFFFFFFF; }
                        
                        emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(3 /*RDX*/), ax_x64_op_imm(mask));
                        emit(mi, mbb, AX_X64_MI_AND, ax_x64_op_reg(0), ax_x64_op_reg(3));
                        emit(mi, mbb, AX_X64_MI_AND, ax_x64_op_reg(2), ax_x64_op_reg(3));
                        
                        if (inst->kind == AX_LIR_INST_UADD_OVERFLOW) {
                            emit(mi, mbb, AX_X64_MI_ADD, ax_x64_op_reg(0), ax_x64_op_reg(2));
                        } else if (inst->kind == AX_LIR_INST_USUB_OVERFLOW) {
                            emit(mi, mbb, AX_X64_MI_SUB, ax_x64_op_reg(0), ax_x64_op_reg(2));
                        } else {
                            emit(mi, mbb, AX_X64_MI_IMUL, ax_x64_op_reg(0), ax_x64_op_reg(2));
                        }
                        
                        emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(3 /*RDX*/), ax_x64_op_imm(uint_max));
                        
                        if (inst->kind == AX_LIR_INST_USUB_OVERFLOW) {
                            // Underflow for unsigned sub: result is > uint_max? No, result of 64-bit sub of two positive small numbers might be negative (represented as large 64-bit value).
                            // So if A < B, A - B is negative, which means > uint_max.
                            emit(mi, mbb, AX_X64_MI_CMP, ax_x64_op_reg(0), ax_x64_op_reg(3));
                            emit(mi, mbb, AX_X64_MI_SETCC, ax_x64_op_imm(0x7 /*A*/), ax_x64_op_reg(0));
                        } else {
                            emit(mi, mbb, AX_X64_MI_CMP, ax_x64_op_reg(0), ax_x64_op_reg(3));
                            emit(mi, mbb, AX_X64_MI_SETCC, ax_x64_op_imm(0x7 /*A*/), ax_x64_op_reg(0));
                        }
                    } else {
                        if (inst->kind == AX_LIR_INST_UADD_OVERFLOW) {
                            emit(mi, mbb, AX_X64_MI_ADD, ax_x64_op_reg(0), ax_x64_op_reg(2));
                            emit(mi, mbb, AX_X64_MI_SETCC, ax_x64_op_imm(0x2 /*B*/), ax_x64_op_reg(0));
                        } else if (inst->kind == AX_LIR_INST_USUB_OVERFLOW) {
                            emit(mi, mbb, AX_X64_MI_SUB, ax_x64_op_reg(0), ax_x64_op_reg(2));
                            emit(mi, mbb, AX_X64_MI_SETCC, ax_x64_op_imm(0x2 /*B*/), ax_x64_op_reg(0));
                        } else {
                            emit(mi, mbb, AX_X64_MI_MUL, ax_x64_op_reg(2), (AxX64Op){0});
                            emit(mi, mbb, AX_X64_MI_SETCC, ax_x64_op_imm(0x2 /*B*/), ax_x64_op_reg(0)); // wait, MUL sets CF and OF. B is carry flag! So SETC works!
                        }
                    }
                    emit(mi, mbb, AX_X64_MI_AND, ax_x64_op_reg(0), ax_x64_op_imm(1));
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_frame(slot_offset + inst->dest.v, 0), ax_x64_op_reg(0));
                    break;
                }
                case AX_LIR_INST_SADD_OVERFLOW:
                  case AX_LIR_INST_SSUB_OVERFLOW:
                  case AX_LIR_INST_SMUL_OVERFLOW: {
                      int is_64 = (inst->overflow_op.bit_width == 64);
                      
                      emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(0 /*RAX*/), ax_x64_op_frame(slot_offset + inst->overflow_op.lhs.v, 0));
                      if (inst->kind == AX_LIR_INST_SADD_OVERFLOW) {
                          emit(mi, mbb, AX_X64_MI_ADD, ax_x64_op_reg(0), ax_x64_op_frame(slot_offset + inst->overflow_op.rhs.v, 0));
                      } else if (inst->kind == AX_LIR_INST_SSUB_OVERFLOW) {
                          emit(mi, mbb, AX_X64_MI_SUB, ax_x64_op_reg(0), ax_x64_op_frame(slot_offset + inst->overflow_op.rhs.v, 0));
                      } else {
                          emit(mi, mbb, AX_X64_MI_IMUL, ax_x64_op_reg(0), ax_x64_op_frame(slot_offset + inst->overflow_op.rhs.v, 0));
                      }
                      
                      if (is_64) {
                          emit(mi, mbb, AX_X64_MI_SETCC, ax_x64_op_imm(0x0 /*O*/), ax_x64_op_reg(0 /*RAX*/));
                          emit(mi, mbb, AX_X64_MI_AND, ax_x64_op_reg(0 /*RAX*/), ax_x64_op_imm(1));
                      } else {
                          int64_t int_min, int_max;
                          if (inst->overflow_op.bit_width == 8) { int_min = -128LL; int_max = 127LL; }
                          else if (inst->overflow_op.bit_width == 16) { int_min = -32768LL; int_max = 32767LL; }
                          else { int_min = -2147483648LL; int_max = 2147483647LL; }
                          
                          emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(2 /*RDX*/), ax_x64_op_imm(int_min));
                          emit(mi, mbb, AX_X64_MI_CMP, ax_x64_op_reg(0 /*RAX*/), ax_x64_op_reg(2 /*RDX*/));
                          emit(mi, mbb, AX_X64_MI_SETCC, ax_x64_op_imm(0xC /*L*/), ax_x64_op_reg(1 /*RCX*/));
                          emit(mi, mbb, AX_X64_MI_AND, ax_x64_op_reg(1 /*RCX*/), ax_x64_op_imm(1));
                          
                          emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(2 /*RDX*/), ax_x64_op_imm(int_max));
                          emit(mi, mbb, AX_X64_MI_CMP, ax_x64_op_reg(0 /*RAX*/), ax_x64_op_reg(2 /*RDX*/));
                          emit(mi, mbb, AX_X64_MI_SETCC, ax_x64_op_imm(0xF /*G*/), ax_x64_op_reg(0 /*RAX*/));
                          emit(mi, mbb, AX_X64_MI_AND, ax_x64_op_reg(0 /*RAX*/), ax_x64_op_imm(1));
                          
                          emit(mi, mbb, AX_X64_MI_OR, ax_x64_op_reg(0 /*RAX*/), ax_x64_op_reg(1 /*RCX*/));
                      }
                      
                      emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_frame(slot_offset + inst->dest.v, 0), ax_x64_op_reg(0 /*RAX*/));
                      break;
                  }

                  case AX_LIR_INST_UDIV_OVERFLOW:
                  case AX_LIR_INST_UREM_OVERFLOW: {
                      // Unsigned division never overflows! (Except div by zero, which is checked separately)
                      emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(0 /*RAX*/), ax_x64_op_imm(0));
                      emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_frame(slot_offset + inst->dest.v, 0), ax_x64_op_reg(0 /*RAX*/));
                      break;
                  }
                  
                  case AX_LIR_INST_SDIV_OVERFLOW:
                  case AX_LIR_INST_SREM_OVERFLOW: {
                      int64_t int_min;
                      if (inst->overflow_op.bit_width == 8) int_min = -128LL;
                      else if (inst->overflow_op.bit_width == 16) int_min = -32768LL;
                      else if (inst->overflow_op.bit_width == 32) int_min = -2147483648LL;
                      else int_min = 0x8000000000000000ULL;
                      
                      emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(0 /*RAX*/), ax_x64_op_frame(slot_offset + inst->overflow_op.lhs.v, 0));
                      emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(2 /*RDX*/), ax_x64_op_frame(slot_offset + inst->overflow_op.rhs.v, 0));
                      
                      emit(mi, mbb, AX_X64_MI_CMP, ax_x64_op_reg(2 /*RDX*/), ax_x64_op_imm(-1));
                      emit(mi, mbb, AX_X64_MI_SETCC, ax_x64_op_imm(0x4 /*E*/), ax_x64_op_reg(1 /*RCX*/));
                      emit(mi, mbb, AX_X64_MI_AND, ax_x64_op_reg(1 /*RCX*/), ax_x64_op_imm(1));
                      
                      emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(2 /*RDX*/), ax_x64_op_imm(int_min));
                      
                      emit(mi, mbb, AX_X64_MI_CMP, ax_x64_op_reg(0 /*RAX*/), ax_x64_op_reg(2 /*RDX*/));
                      emit(mi, mbb, AX_X64_MI_SETCC, ax_x64_op_imm(0x4 /*E*/), ax_x64_op_reg(0 /*RAX*/));
                      emit(mi, mbb, AX_X64_MI_AND, ax_x64_op_reg(0 /*RAX*/), ax_x64_op_imm(1));
                      
                      emit(mi, mbb, AX_X64_MI_AND, ax_x64_op_reg(0 /*RAX*/), ax_x64_op_reg(1 /*RCX*/));
                      
                      emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_frame(slot_offset + inst->dest.v, 0), ax_x64_op_reg(0 /*RAX*/));
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
                case AX_LIR_INST_NOT:
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(0), ax_x64_op_frame(slot_offset + inst->unary.operand.v, 0));
                    emit(mi, mbb, AX_X64_MI_XOR, ax_x64_op_reg(0), ax_x64_op_imm(1));
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_frame(slot_offset + inst->dest.v, 0), ax_x64_op_reg(0));
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
                          } else if (inst->abi_arg.loc_kind == 2) { // INDIRECT
                              uint32_t size = ax_type_size(lir->vregs[inst->dest.v].ty, interner);
                              if (inst->abi_arg.loc_reg_or_offset < 16) {
                                  emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(0), ax_x64_op_reg(inst->abi_arg.loc_reg_or_offset));
                              } else {
                                  AxX64Op mem = { .kind = AX_X64_OP_MEM, .mem = { .base = 5 /*RBP*/, .index = AX_REG_NONE, .scale = 1, .disp = 16 + inst->abi_arg.loc_reg_or_offset, .is_rip = false } };
                                  emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(0), mem);
                              }
                              for (uint32_t i = 0; i < size; i += 8) {
                                  uint32_t chunk = size - i >= 8 ? 8 : (size - i >= 4 ? 4 : (size - i >= 2 ? 2 : 1));
                                  AxX64Op src_mem = { .kind = AX_X64_OP_MEM, .mem = { .base = 0 /*RAX*/, .index = AX_REG_NONE, .scale = 1, .disp = i, .is_rip = false } };
                                  emit_sz(mi, mbb, AX_X64_MI_MOV, chunk, ax_x64_op_reg(1 /*RCX*/), src_mem);
                                  emit_sz(mi, mbb, AX_X64_MI_MOV, chunk, ax_x64_op_frame(slot_offset + inst->dest.v, i), ax_x64_op_reg(1 /*RCX*/));
                              }
                          }

                      } else {
                          if (inst->abi_arg.loc_kind == 0) { // REG
                              emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(inst->abi_arg.loc_reg_or_offset), ax_x64_op_frame(slot_offset + inst->abi_arg.val.v, 0));
                          } else if (inst->abi_arg.loc_kind == 1) { // STACK
                              AxX64Op mem = { .kind = AX_X64_OP_MEM, .mem = { .base = 4 /*RSP*/, .index = AX_REG_NONE, .scale = 1, .disp = inst->abi_arg.loc_reg_or_offset, .is_rip = false } };
                              emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(0), ax_x64_op_frame(slot_offset + inst->abi_arg.val.v, 0));
                              emit(mi, mbb, AX_X64_MI_MOV, mem, ax_x64_op_reg(0));
                          } else if (inst->abi_arg.loc_kind == 2) { // INDIRECT
                              // Caller passes address of the local struct.
                              emit(mi, mbb, AX_X64_MI_LEA, ax_x64_op_reg(0), ax_x64_op_frame(slot_offset + inst->abi_arg.val.v, 0));
                              if (inst->abi_arg.loc_reg_or_offset < 16) { // It's a register (e.g. RCX = 1)
                                  emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(inst->abi_arg.loc_reg_or_offset), ax_x64_op_reg(0));
                              } else {
                                  AxX64Op mem = { .kind = AX_X64_OP_MEM, .mem = { .base = 4 /*RSP*/, .index = AX_REG_NONE, .scale = 1, .disp = inst->abi_arg.loc_reg_or_offset, .is_rip = false } };
                                  emit(mi, mbb, AX_X64_MI_MOV, mem, ax_x64_op_reg(0));
                              }
                          }
                      }
                      break;
                                  case AX_LIR_INST_CALL: {
                      const AxType *callee_ty = ax_type_get(interner, inst->call.callee_ty);
                      TypeId ret_ty = {0};
                      if (callee_ty) {
                          if (callee_ty->kind == AX_TY_FN) {
                              ret_ty = callee_ty->fn.ret_type;
                          } else if (callee_ty->kind == AX_TY_CLOSURE) {
                              ret_ty = callee_ty->closure.ret_type;
                          }
                      }
                      if (ret_ty.v != 0) {
                          uint32_t ret_size = ax_type_size(ret_ty, interner);
                          bool ret_in_mem = (ret_size > 8 || (ret_size != 1 && ret_size != 2 && ret_size != 4 && ret_size != 8 && ret_size != 0));
                          if (ret_in_mem) {
                              emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(1 /*RCX*/), ax_x64_op_frame(slot_offset + inst->call.dst_addr.v, 0));
                          }
                      }
                      if (inst->call.sym_name) {
                          emit(mi, mbb, AX_X64_MI_CALL, (AxX64Op){0}, (AxX64Op){0});
                          mbb->last_inst->msg = inst->call.sym_name;
                      } else {
                          emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(10 /*R10*/), ax_x64_op_frame(slot_offset + inst->call.callee_vreg.v, 0));
                          emit(mi, mbb, AX_X64_MI_CALL, ax_x64_op_reg(10 /*R10*/), (AxX64Op){0});
                          mbb->last_inst->op_count = 1;
                      }
                      break;
                  }
                                    case AX_LIR_INST_ABI_RESULT:
                    if (inst->abi_result.loc_kind == 0) { // REG
                        emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_frame(slot_offset + inst->dest.v, 0), ax_x64_op_reg(inst->abi_result.loc_reg_or_offset));
                    } else if (inst->abi_result.loc_kind == 2) { // INDIRECT
                        uint32_t load_sz = ax_type_size(lir->vregs[inst->dest.v].ty, interner);
                        if (load_sz <= 8) {
                            if (load_sz != 1 && load_sz != 2 && load_sz != 4 && load_sz != 8) load_sz = 8;
                            AxX64Op mem = { .kind = AX_X64_OP_MEM, .mem = { .base = 0 /*RAX*/, .index = AX_REG_NONE, .scale = 1, .disp = 0, .is_rip = false } };
                            emit_sz(mi, mbb, AX_X64_MI_MOV, load_sz, ax_x64_op_reg(1 /*RCX*/), mem);
                            emit_sz(mi, mbb, AX_X64_MI_MOV, load_sz, ax_x64_op_frame(slot_offset + inst->dest.v, 0), ax_x64_op_reg(1 /*RCX*/));
                        } else {
                            for (uint32_t i = 0; i < load_sz; i += 8) {
                                uint32_t chunk = load_sz - i >= 8 ? 8 : (load_sz - i >= 4 ? 4 : (load_sz - i >= 2 ? 2 : 1));
                                AxX64Op mem = { .kind = AX_X64_OP_MEM, .mem = { .base = 0 /*RAX*/, .index = AX_REG_NONE, .scale = 1, .disp = i, .is_rip = false } };
                                emit_sz(mi, mbb, AX_X64_MI_MOV, chunk, ax_x64_op_reg(1 /*RCX*/), mem);
                                emit_sz(mi, mbb, AX_X64_MI_MOV, chunk, ax_x64_op_frame(slot_offset + inst->dest.v, i), ax_x64_op_reg(1 /*RCX*/));
                            }
                        }
                    }
                    break;
                case AX_LIR_INST_STACK_ADDR: {
                    bool ret_in_mem = false;
                    if (inst->stack_addr.slot.v == 0 && lir->slot_count > 0) {
                        uint32_t ret_size = ax_type_size(lir->slots[0].ty, interner);
                        ret_in_mem = (ret_size > 8 || (ret_size != 1 && ret_size != 2 && ret_size != 4 && ret_size != 8 && ret_size != 0));
                    }
                    if (ret_in_mem) {
                        emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(0 /*RAX*/), ax_x64_op_frame(0, 0));
                        emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_frame(slot_offset + inst->dest.v, 0), ax_x64_op_reg(0));
                    } else {
                        emit(mi, mbb, AX_X64_MI_LEA, ax_x64_op_reg(0 /*RAX*/), ax_x64_op_frame(inst->stack_addr.slot.v, 0));
                        emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_frame(slot_offset + inst->dest.v, 0), ax_x64_op_reg(0));
                    }
                    break;
                }
                case AX_LIR_INST_LOAD:
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(0 /*RAX*/), ax_x64_op_frame(slot_offset + inst->load.ptr.v, 0));
                    {
                        AxX64Op mem = { .kind = AX_X64_OP_MEM, .mem = { .base = 0 /*RAX*/, .index = AX_REG_NONE, .scale = 1, .disp = 0, .is_rip = false } };
                        uint32_t load_sz = ax_type_size(inst->load.ty, interner);
                        if (load_sz <= 8) {
                            if (load_sz != 1 && load_sz != 2 && load_sz != 4 && load_sz != 8) load_sz = 8;
                            emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(1 /*RCX*/), ax_x64_op_imm(0));
                            emit_sz(mi, mbb, AX_X64_MI_MOV, load_sz, ax_x64_op_reg(1 /*RCX*/), mem);
                        } else {
                            for (uint32_t i = 0; i < load_sz; i += 8) {
                                uint32_t chunk = load_sz - i >= 8 ? 8 : (load_sz - i >= 4 ? 4 : (load_sz - i >= 2 ? 2 : 1));
                                mem.mem.disp = i;
                                emit_sz(mi, mbb, AX_X64_MI_MOV, chunk, ax_x64_op_reg(1 /*RCX*/), mem);
                                emit_sz(mi, mbb, AX_X64_MI_MOV, chunk, ax_x64_op_frame(slot_offset + inst->dest.v, i), ax_x64_op_reg(1 /*RCX*/));
                            }
                            goto load_skip_mov; // Skip the single 8-byte move at the end
                        }
                        
                        uint32_t size = ax_type_size(inst->load.ty, interner);
                        bool is_signed = false;
                        const AxType *t = ax_type_get(interner, inst->load.ty);
                        if (t && (t->kind == AX_TY_I8 || t->kind == AX_TY_I16 || t->kind == AX_TY_I32 || t->kind == AX_TY_I64 || t->kind == AX_TY_ISIZE)) {
                            is_signed = true;
                        }
                        if (size == 1) {
                            emit(mi, mbb, AX_X64_MI_SHL, ax_x64_op_reg(1), ax_x64_op_imm(56));
                            emit(mi, mbb, is_signed ? AX_X64_MI_SAR : AX_X64_MI_SHR, ax_x64_op_reg(1), ax_x64_op_imm(56));
                        } else if (size == 2) {
                            emit(mi, mbb, AX_X64_MI_SHL, ax_x64_op_reg(1), ax_x64_op_imm(48));
                            emit(mi, mbb, is_signed ? AX_X64_MI_SAR : AX_X64_MI_SHR, ax_x64_op_reg(1), ax_x64_op_imm(48));
                        } else if (size == 4) {
                            emit(mi, mbb, AX_X64_MI_SHL, ax_x64_op_reg(1), ax_x64_op_imm(32));
                            emit(mi, mbb, is_signed ? AX_X64_MI_SAR : AX_X64_MI_SHR, ax_x64_op_reg(1), ax_x64_op_imm(32));
                        }
                        
                        emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_frame(slot_offset + inst->dest.v, 0), ax_x64_op_reg(1));
                    load_skip_mov:;
                    }
                    break;
                case AX_LIR_INST_STORE:
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(0 /*RAX*/), ax_x64_op_frame(slot_offset + inst->store.ptr.v, 0));
                    emit(mi, mbb, AX_X64_MI_MOV, ax_x64_op_reg(1 /*RCX*/), ax_x64_op_frame(slot_offset + inst->store.val.v, 0));
                    {
                        AxX64Op mem = { .kind = AX_X64_OP_MEM, .mem = { .base = 0 /*RAX*/, .index = AX_REG_NONE, .scale = 1, .disp = 0, .is_rip = false } };
                        if (inst->store.val.v >= lir->vreg_count) { AX_ICE("VReg out of bounds"); }
                        uint32_t size = ax_type_size(lir->vregs[inst->store.val.v].ty, interner);
                        if (size <= 8) {
                            if (size != 1 && size != 2 && size != 4 && size != 8) size = 8;
                            emit_sz(mi, mbb, AX_X64_MI_MOV, size, mem, ax_x64_op_reg(1));
                        } else {
                            for (uint32_t i = 0; i < size; i += 8) {
                                uint32_t chunk = size - i >= 8 ? 8 : (size - i >= 4 ? 4 : (size - i >= 2 ? 2 : 1));
                                emit_sz(mi, mbb, AX_X64_MI_MOV, chunk, ax_x64_op_reg(1 /*RCX*/), ax_x64_op_frame(slot_offset + inst->store.val.v, i));
                                mem.mem.disp = i;
                                emit_sz(mi, mbb, AX_X64_MI_MOV, chunk, mem, ax_x64_op_reg(1 /*RCX*/));
                            }
                        }
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
