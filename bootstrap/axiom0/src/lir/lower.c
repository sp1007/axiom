#include "lir/lir.h"
#include <stdlib.h>

typedef struct LirBuilder {
    AxArena *arena;
    TypeInterner *interner;
    const AxMirBody *mir;
    
    AxLirStackSlot *slots;
    size_t slot_count;
    size_t slot_cap;
    
    AxLirVReg *vregs;
    size_t vreg_count;
    size_t vreg_cap;
    
    AxLirBb *bbs;
    size_t bb_count;
    
    AxLirInst *cur_insts;
    size_t cur_inst_count;
    size_t cur_inst_cap;
} LirBuilder;

static AxLirVRegId make_vreg(LirBuilder *b, TypeId ty) {
    if (b->vreg_count == b->vreg_cap) {
        b->vreg_cap = b->vreg_cap == 0 ? 16 : b->vreg_cap * 2;
        b->vregs = realloc(b->vregs, b->vreg_cap * sizeof(AxLirVReg));
    }
    AxLirVRegId id = { (uint32_t)b->vreg_count };
    b->vregs[id.v].ty = ty;
    b->vreg_count++;
    return id;
}

static void emit_inst(LirBuilder *b, AxLirInst inst) {
    if (b->cur_inst_count == b->cur_inst_cap) {
        b->cur_inst_cap = b->cur_inst_cap == 0 ? 16 : b->cur_inst_cap * 2;
        b->cur_insts = realloc(b->cur_insts, b->cur_inst_cap * sizeof(AxLirInst));
    }
    b->cur_insts[b->cur_inst_count++] = inst;
}

static AxLirVRegId emit_stack_addr(LirBuilder *b, AxLirStackSlotId slot) {
    AxLirVRegId dest = make_vreg(b, b->interner->t_usize); // Assuming pointers are usize
    AxLirInst inst = { .kind = AX_LIR_INST_STACK_ADDR, .dest = dest, .stack_addr = { .slot = slot } };
    emit_inst(b, inst);
    return dest;
}

static AxLirVRegId emit_const(LirBuilder *b, uint64_t val, TypeId ty) {
    AxLirVRegId dest = make_vreg(b, ty);
    AxLirInst inst = { .kind = AX_LIR_INST_CONST, .dest = dest, .constant = { .val = val, .ty = ty } };
    emit_inst(b, inst);
    return dest;
}

static AxLirVRegId emit_load(LirBuilder *b, AxLirVRegId ptr, TypeId ty) {
    AxLirVRegId dest = make_vreg(b, ty);
    AxLirInst inst = { .kind = AX_LIR_INST_LOAD, .dest = dest, .load = { .ptr = ptr, .ty = ty } };
    emit_inst(b, inst);
    return dest;
}

static void emit_store(LirBuilder *b, AxLirVRegId ptr, AxLirVRegId val) {
    AxLirInst inst = { .kind = AX_LIR_INST_STORE, .dest = {0}, .store = { .ptr = ptr, .val = val } };
    emit_inst(b, inst);
}

static AxLirVRegId emit_offset(LirBuilder *b, AxLirVRegId ptr, AxLirVRegId off) {
    AxLirVRegId dest = make_vreg(b, b->interner->t_usize);
    AxLirInst inst = { .kind = AX_LIR_INST_ADD, .dest = dest, .binary = { .lhs = ptr, .rhs = off } };
    emit_inst(b, inst);
    return dest;
}

static AxLirVRegId lower_place_addr(LirBuilder *b, const AxMirPlace *place, TypeId *out_ty) {
    AxLirStackSlotId slot = { place->local.v };
    AxLirVRegId addr = emit_stack_addr(b, slot);
    TypeId ty = b->mir->locals[place->local.v].ty;
    
    // Projections
    for (size_t i = 0; i < place->proj_count; i++) {
        switch (place->projs[i].kind) {
            case AX_MIR_PROJ_DEREF: {
                addr = emit_load(b, addr, b->interner->t_usize);
                const AxType *t = ax_type_get(b->interner, ty);
                if (t && t->kind == AX_TY_PTR) ty = t->ptr.pointee;
                break;
            }
            case AX_MIR_PROJ_FIELD: {
                const AxType *t = ax_type_get(b->interner, ty);
                uint32_t idx = place->projs[i].field_idx;
                uint32_t offset = 0;
                uint32_t max_align = 1;
                TypeId next_ty = {0};
                size_t f_count = 0;
                TypeId *fields = NULL;
                if (t && t->kind == AX_TY_STRUCT) {
                    f_count = t->strct.field_count;
                    fields = t->strct.fields;
                } else if (t && t->kind == AX_TY_TUPLE) {
                    f_count = t->tuple.field_count;
                    fields = t->tuple.fields;
                }
                
                for (size_t k = 0; k <= idx && k < f_count; k++) {
                    TypeId field_ty = fields[k];
                    uint32_t fa = ax_type_align(field_ty, b->interner);
                    uint32_t fs = ax_type_size(field_ty, b->interner);
                    if (fa > max_align) max_align = fa;
                    offset = (offset + fa - 1) & ~(fa - 1);
                    if (k == idx) {
                        next_ty = field_ty;
                        break;
                    }
                    offset += fs;
                }
                ty = next_ty;
                AxLirVRegId dummy_off = emit_const(b, offset, b->interner->t_usize);
                addr = emit_offset(b, addr, dummy_off);
                break;
            }
            case AX_MIR_PROJ_INDEX: {
                const AxType *t = ax_type_get(b->interner, ty);
                TypeId elem_ty = {0};
                if (t && t->kind == AX_TY_ARRAY) elem_ty = t->array.elem;
                AxLirStackSlotId idx_slot = { place->projs[i].index_local.v };
                AxLirVRegId idx_addr = emit_stack_addr(b, idx_slot);
                AxLirVRegId idx_val = emit_load(b, idx_addr, b->interner->t_usize);
                uint32_t fs = ax_type_size(elem_ty, b->interner);
                AxLirVRegId dummy_size = emit_const(b, fs, b->interner->t_usize);
                AxLirVRegId off = make_vreg(b, b->interner->t_usize);
                emit_inst(b, (AxLirInst){ .kind = AX_LIR_INST_MUL, .dest = off, .binary = { .lhs = idx_val, .rhs = dummy_size } });
                addr = emit_offset(b, addr, off);
                ty = elem_ty;
                break;
            }
            case AX_MIR_PROJ_DOWNCAST: {
                break;
            }
        }
    }
    
    if (out_ty) *out_ty = ty;
    return addr;
}

static AxLirVRegId lower_operand(LirBuilder *b, const AxMirOperand *op) {
    switch (op->kind) {
        case AX_MIR_OP_COPY:
        case AX_MIR_OP_MOVE: {
            TypeId place_ty;
            AxLirVRegId addr = lower_place_addr(b, &op->place, &place_ty);
            return emit_load(b, addr, place_ty);
        }
        case AX_MIR_OP_CONST:
            return emit_const(b, op->constant.val, op->constant.ty);
    }
    return (AxLirVRegId){0};
}

static AxLirInstKind lower_binop(AxMirBinOp op, bool is_signed) {
    switch (op) {
        case AX_MIR_BINOP_ADD: return AX_LIR_INST_ADD;
        case AX_MIR_BINOP_SUB: return AX_LIR_INST_SUB;
        case AX_MIR_BINOP_MUL: return AX_LIR_INST_MUL;
        case AX_MIR_BINOP_DIV: return AX_LIR_INST_DIV;
        case AX_MIR_BINOP_REM: return AX_LIR_INST_REM;
        case AX_MIR_BINOP_BIT_XOR: return AX_LIR_INST_BIT_XOR;
        case AX_MIR_BINOP_BIT_AND: return AX_LIR_INST_BIT_AND;
        case AX_MIR_BINOP_BIT_OR: return AX_LIR_INST_BIT_OR;
        case AX_MIR_BINOP_SHL: return AX_LIR_INST_SHL;
        case AX_MIR_BINOP_SHR: return is_signed ? AX_LIR_INST_SAR : AX_LIR_INST_SHR;
        case AX_MIR_BINOP_EQ: return AX_LIR_INST_ICMP_EQ;
        case AX_MIR_BINOP_NE: return AX_LIR_INST_ICMP_NE;
        case AX_MIR_BINOP_LT: return is_signed ? AX_LIR_INST_ICMP_SLT : AX_LIR_INST_ICMP_ULT;
        case AX_MIR_BINOP_LE: return is_signed ? AX_LIR_INST_ICMP_SLE : AX_LIR_INST_ICMP_ULE;
        case AX_MIR_BINOP_GT: return is_signed ? AX_LIR_INST_ICMP_SGT : AX_LIR_INST_ICMP_UGT;
        case AX_MIR_BINOP_GE: return is_signed ? AX_LIR_INST_ICMP_SGE : AX_LIR_INST_ICMP_UGE;
        case AX_MIR_BINOP_OFFSET: return AX_LIR_INST_ADD;
    }
    return AX_LIR_INST_ADD;
}

static AxLirVRegId lower_rvalue(LirBuilder *b, const AxMirRvalue *rv, TypeId dest_ty) {
    switch (rv->kind) {
        case AX_MIR_RVALUE_USE:
            return lower_operand(b, &rv->use);
        case AX_MIR_RVALUE_REF:
            return lower_place_addr(b, &rv->ref.place, NULL);
        case AX_MIR_RVALUE_BINARY_OP: {
            AxLirVRegId lhs = lower_operand(b, &rv->binary_op.lhs);
            AxLirVRegId rhs = lower_operand(b, &rv->binary_op.rhs);
            const AxType *t = ax_type_get(b->interner, dest_ty);
              bool is_signed = true;
              if (t && (t->kind == 10 || t->kind == 11 || t->kind == 12 || t->kind == 13 || t->kind == 14 || t->kind == 3)) {
                  is_signed = false;
              }
              AxLirInstKind kind = lower_binop(rv->binary_op.op, is_signed);
            AxLirVRegId dest = make_vreg(b, dest_ty);
            emit_inst(b, (AxLirInst){ .kind = kind, .dest = dest, .binary = { .lhs = lhs, .rhs = rhs } });
            return dest;
        }
        case AX_MIR_RVALUE_UNARY_OP: {
            AxLirVRegId op = lower_operand(b, &rv->unary_op.operand);
            AxLirInstKind kind = AX_LIR_INST_NEG;
            if (rv->unary_op.op == AX_MIR_UNOP_NOT) kind = AX_LIR_INST_NOT;
            else if (rv->unary_op.op == AX_MIR_UNOP_BITNOT) kind = AX_LIR_INST_BITNOT;
            AxLirVRegId dest = make_vreg(b, dest_ty);
            emit_inst(b, (AxLirInst){ .kind = kind, .dest = dest, .unary = { .operand = op } });
            return dest;
        }
        case AX_MIR_RVALUE_AGGREGATE:
            return emit_const(b, 0, dest_ty); // Not used directly, handled in assign
        default:
            return emit_const(b, 0, b->interner->t_isize);
    }
}

#include "kernel/interner.h"
#include "kernel/str.h"

AxLirBody *ax_lir_lower(const AxMirBody *mir, const struct AxHir *hir, TypeInterner *interner, struct StrInterner *str_in, const AxType *fn_ty) {
    
    AxLirBody *lir = malloc(sizeof(AxLirBody));
    ax_arena_init(&lir->arena, 4096);
    
    LirBuilder b = { .arena = &lir->arena, .interner = interner, .mir = mir };
    
    // Create stack slots
    b.slot_count = mir->local_count;
    b.slots = ax_arena_alloc(&lir->arena, b.slot_count * sizeof(AxLirStackSlot), _Alignof(AxLirStackSlot));
    for (size_t i = 0; i < mir->local_count; i++) {
        b.slots[i].ty = mir->locals[i].ty;
    }
    
    b.interner = interner;
    b.bb_count = mir->bb_count;
    b.bbs = ax_arena_alloc(&lir->arena, b.bb_count * sizeof(AxLirBb), _Alignof(AxLirBb));
    
    for (size_t i = 0; i < mir->bb_count; i++) {
        const AxMirBb *mbb = &mir->bbs[i];
        b.cur_inst_count = 0;
        
        if (i == 0 && fn_ty && fn_ty->kind == AX_TY_FN) {
            for (size_t p = 0; p < fn_ty->fn.param_count; p++) {
                AxLirVRegId dest = make_vreg(&b, fn_ty->fn.param_types[p]);
                emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_ABI_ARG, .dest = dest, .abi_arg = { .index = (uint32_t)p } });
                AxLirVRegId addr = emit_stack_addr(&b, (AxLirStackSlotId){ (uint32_t)(p + 1) });
                emit_store(&b, addr, dest);
            }
        }
        
        for (size_t j = 0; j < mbb->stmt_count; j++) {
            const AxMirStmt *stmt = &mbb->stmts[j];
            if (stmt->kind == AX_MIR_STMT_ASSIGN) {
                TypeId dest_ty = mir->locals[stmt->assign.place.local.v].ty;
                if (stmt->assign.rvalue.kind == AX_MIR_RVALUE_AGGREGATE) {
                    AxLirVRegId addr = lower_place_addr(&b, &stmt->assign.place, NULL);
                    uint32_t offset = 0;
                    uint32_t max_align = 1;
                    const AxType *ty = ax_type_get(b.interner, dest_ty);
                    for (size_t k = 0; k < stmt->assign.rvalue.aggregate.operand_count; k++) {
                        TypeId field_ty = {0};
                        if (ty->kind == AX_TY_STRUCT) field_ty = ty->strct.fields[k];
                        else if (ty->kind == AX_TY_TUPLE) field_ty = ty->tuple.fields[k];
                        
                        uint32_t fa = ax_type_align(field_ty, b.interner);
                        uint32_t fs = ax_type_size(field_ty, b.interner);
                        if (fa > max_align) max_align = fa;
                        offset = (offset + fa - 1) & ~(fa - 1);
                        
                        AxLirVRegId off_reg = emit_const(&b, offset, b.interner->t_usize);
                        AxLirVRegId field_addr = emit_offset(&b, addr, off_reg);
                        
                        AxLirVRegId field_val = lower_operand(&b, &stmt->assign.rvalue.aggregate.operands[k]);
                        emit_store(&b, field_addr, field_val);
                        
                        offset += fs;
                    }
                    continue;
                }
                
                AxLirVRegId val = lower_rvalue(&b, &stmt->assign.rvalue, dest_ty);
                AxLirVRegId addr = lower_place_addr(&b, &stmt->assign.place, NULL);
                emit_store(&b, addr, val);
            }
        }
        
        AxLirTerminator term = {0};
        switch (mbb->terminator.kind) {
            case AX_MIR_TERM_GOTO:
                term.kind = AX_LIR_TERM_JMP;
                term.jmp_target = (AxLirBbId){ mbb->terminator.goto_target.v };
                break;
            case AX_MIR_TERM_SWITCH_INT: {
                AxLirVRegId cond = lower_operand(&b, &mbb->terminator.switch_int.discr);
                term.kind = AX_LIR_TERM_SWITCH;
                term.switch_int.cond = cond;
                term.switch_int.count = mbb->terminator.switch_int.targets.count;
                if (term.switch_int.count > 0) {
                    term.switch_int.targets = ax_arena_alloc(&lir->arena, term.switch_int.count * sizeof(AxLirSwitchTarget), _Alignof(AxLirSwitchTarget));
                    for (size_t k = 0; k < term.switch_int.count; k++) {
                        term.switch_int.targets[k].value = mbb->terminator.switch_int.targets.values[k].value;
                        term.switch_int.targets[k].target = (AxLirBbId){ mbb->terminator.switch_int.targets.values[k].target.v };
                    }
                }
                term.switch_int.otherwise = (AxLirBbId){ mbb->terminator.switch_int.targets.otherwise.v };
                break;
            }
            case AX_MIR_TERM_RETURN:
                term.kind = AX_LIR_TERM_RETURN;
                break;
            case AX_MIR_TERM_CALL: {
                AxLirVRegId *args = ax_arena_alloc(b.arena, mbb->terminator.call.arg_count * sizeof(AxLirVRegId), _Alignof(AxLirVRegId));
                for (size_t k = 0; k < mbb->terminator.call.arg_count; k++) {
                    args[k] = lower_operand(&b, &mbb->terminator.call.args[k]);
                }
                for (size_t k = 0; k < mbb->terminator.call.arg_count; k++) {
                    emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_ABI_ARG, .dest = { 0xFFFFFFFF }, .abi_arg = { .index = (uint32_t)k, .val = args[k] } });
                }
                
                const char *sym_name = NULL;
                if (mbb->terminator.call.func.kind == AX_MIR_OP_CONST) {
                    uint32_t sym_v = (uint32_t)mbb->terminator.call.func.constant.val;
                    if (sym_v != 0 && hir && str_in) {
                        for (const struct AxHirItem *it = hir->items; it; it = it->next) {
                            if (it->kind == AX_HIR_ITEM_FN && it->fn.symbol.v == sym_v) {
                                StrView sv = ax_interner_get(str_in, it->fn.name);
                                char *name = malloc(sv.len + 1);
                                memcpy(name, sv.ptr, sv.len);
                                name[sv.len] = '\0';
                                sym_name = name;
                                break;
                            }
                        }
                    }
                }
                TypeId callee_ty = {0};
                if (mbb->terminator.call.func.kind == AX_MIR_OP_CONST) {
                    callee_ty = mbb->terminator.call.func.constant.ty;
                } else {
                    AxMirLocalId loc = mbb->terminator.call.func.place.local;
                    callee_ty = mir->locals[loc.v].ty;
                }
                emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_CALL, .dest = {0}, .call = { .sym_name = sym_name, .callee_ty = callee_ty } });
                
                AxLirVRegId res = make_vreg(&b, interner->t_isize);

                emit_inst(&b, (AxLirInst){ .kind = AX_LIR_INST_ABI_RESULT, .dest = res, .abi_result = { .index = 0 } });
                
                AxLirVRegId dst_addr = lower_place_addr(&b, &mbb->terminator.call.destination, NULL);
                emit_store(&b, dst_addr, res);
                
                term.kind = AX_LIR_TERM_JMP;
                term.jmp_target = (AxLirBbId){ mbb->terminator.call.target.v };
                break;
            }
            case AX_MIR_TERM_ASSERT: {
                term.kind = AX_LIR_TERM_JMP;
                term.jmp_target = (AxLirBbId){ mbb->terminator.assert.target.v };
                break;
            }
            default:
                term.kind = AX_LIR_TERM_UNREACHABLE;
                break;
        }
        
        b.bbs[i].inst_count = b.cur_inst_count;
        if (b.cur_inst_count > 0) {
            b.bbs[i].insts = ax_arena_alloc(&lir->arena, b.cur_inst_count * sizeof(AxLirInst), _Alignof(AxLirInst));
            for (size_t j = 0; j < b.cur_inst_count; j++) b.bbs[i].insts[j] = b.cur_insts[j];
        } else {
            b.bbs[i].insts = NULL;
        }
        b.bbs[i].terminator = term;
    }
    
    lir->slots = b.slots;
    lir->slot_count = b.slot_count;
    
    if (b.vreg_count > 0) {
        lir->vregs = ax_arena_alloc(&lir->arena, b.vreg_count * sizeof(AxLirVReg), _Alignof(AxLirVReg));
        for (size_t i = 0; i < b.vreg_count; i++) lir->vregs[i] = b.vregs[i];
    } else {
        lir->vregs = NULL;
    }
    lir->vreg_count = b.vreg_count;
    
    lir->bbs = b.bbs;
    lir->bb_count = b.bb_count;
    
    free(b.vregs);
    free(b.cur_insts);
    
    return lir;
}
