#include "lir/lir.h"

void ax_lir_print(FILE *out, const AxLirBody *body) {
    fprintf(out, "lir_body {\n");
    for (size_t i = 0; i < body->slot_count; i++) {
        fprintf(out, "    slot%zu: type#%u;\n", i, body->slots[i].ty.v);
    }
    
    for (size_t i = 0; i < body->bb_count; i++) {
        fprintf(out, "    bb%zu: {\n", i);
        AxLirBb *bb = &body->bbs[i];
        for (size_t j = 0; j < bb->inst_count; j++) {
            AxLirInst *inst = &bb->insts[j];
            fprintf(out, "        ");
            
            if (inst->kind != AX_LIR_INST_STORE && inst->kind != AX_LIR_INST_CALL && inst->kind != AX_LIR_INST_ABI_ARG) {
                fprintf(out, "v%u = ", inst->dest.v);
            }
            
            switch (inst->kind) {
                case AX_LIR_INST_ADD: fprintf(out, "add v%u, v%u;\n", inst->binary.lhs.v, inst->binary.rhs.v); break;
                case AX_LIR_INST_SUB: fprintf(out, "sub v%u, v%u;\n", inst->binary.lhs.v, inst->binary.rhs.v); break;
                case AX_LIR_INST_MUL: fprintf(out, "mul v%u, v%u;\n", inst->binary.lhs.v, inst->binary.rhs.v); break;
                case AX_LIR_INST_DIV: fprintf(out, "div v%u, v%u;\n", inst->binary.lhs.v, inst->binary.rhs.v); break;
                case AX_LIR_INST_REM: fprintf(out, "rem v%u, v%u;\n", inst->binary.lhs.v, inst->binary.rhs.v); break;
                case AX_LIR_INST_UDIV: fprintf(out, "udiv v%u, v%u;\n", inst->binary.lhs.v, inst->binary.rhs.v); break;
                case AX_LIR_INST_UREM: fprintf(out, "urem v%u, v%u;\n", inst->binary.lhs.v, inst->binary.rhs.v); break;
                case AX_LIR_INST_BIT_XOR: fprintf(out, "xor v%u, v%u;\n", inst->binary.lhs.v, inst->binary.rhs.v); break;
                case AX_LIR_INST_BIT_AND: fprintf(out, "and v%u, v%u;\n", inst->binary.lhs.v, inst->binary.rhs.v); break;
                case AX_LIR_INST_BIT_OR:  fprintf(out, "or v%u, v%u;\n", inst->binary.lhs.v, inst->binary.rhs.v); break;
                case AX_LIR_INST_SHL:     fprintf(out, "shl v%u, v%u;\n", inst->binary.lhs.v, inst->binary.rhs.v); break;
                case AX_LIR_INST_SHR:
            case AX_LIR_INST_SAR:     fprintf(out, "shr v%u, v%u;\n", inst->binary.lhs.v, inst->binary.rhs.v); break;
                case AX_LIR_INST_ICMP_EQ: fprintf(out, "icmp.eq v%u, v%u;\n", inst->binary.lhs.v, inst->binary.rhs.v); break;
                case AX_LIR_INST_ICMP_NE: fprintf(out, "icmp.ne v%u, v%u;\n", inst->binary.lhs.v, inst->binary.rhs.v); break;
                case AX_LIR_INST_ICMP_SLT: fprintf(out, "icmp.slt v%u, v%u;\n", inst->binary.lhs.v, inst->binary.rhs.v); break;
                case AX_LIR_INST_ICMP_SLE: fprintf(out, "icmp.sle v%u, v%u;\n", inst->binary.lhs.v, inst->binary.rhs.v); break;
                case AX_LIR_INST_ICMP_SGT: fprintf(out, "icmp.sgt v%u, v%u;\n", inst->binary.lhs.v, inst->binary.rhs.v); break;
                case AX_LIR_INST_ICMP_SGE: fprintf(out, "icmp.sge v%u, v%u;\n", inst->binary.lhs.v, inst->binary.rhs.v); break;
                case AX_LIR_INST_ICMP_ULT: fprintf(out, "icmp.ult v%u, v%u;\n", inst->binary.lhs.v, inst->binary.rhs.v); break;
                case AX_LIR_INST_ICMP_ULE: fprintf(out, "icmp.ule v%u, v%u;\n", inst->binary.lhs.v, inst->binary.rhs.v); break;
                case AX_LIR_INST_ICMP_UGT: fprintf(out, "icmp.ugt v%u, v%u;\n", inst->binary.lhs.v, inst->binary.rhs.v); break;
                case AX_LIR_INST_ICMP_UGE: fprintf(out, "icmp.uge v%u, v%u;\n", inst->binary.lhs.v, inst->binary.rhs.v); break;
                
                case AX_LIR_INST_NEG: fprintf(out, "neg v%u;\n", inst->unary.operand.v); break;
                case AX_LIR_INST_NOT: fprintf(out, "not v%u;\n", inst->unary.operand.v); break;
                case AX_LIR_INST_BITNOT: fprintf(out, "bitnot v%u;\n", inst->unary.operand.v); break;
                
                case AX_LIR_INST_LOAD: fprintf(out, "load v%u;\n", inst->load.ptr.v); break;
                case AX_LIR_INST_STORE: fprintf(out, "store v%u, v%u;\n", inst->store.ptr.v, inst->store.val.v); break;
                case AX_LIR_INST_STACK_ADDR: fprintf(out, "stack_addr slot%u;\n", inst->stack_addr.slot.v); break;
                case AX_LIR_INST_OFFSET: fprintf(out, "offset v%u, v%u;\n", inst->binary.lhs.v, inst->binary.rhs.v); break;
                case AX_LIR_INST_CONST: fprintf(out, "const %llu;\n", (unsigned long long)inst->constant.val); break;
                case AX_LIR_INST_CONST_STR: fprintf(out, "const_str \"...\" (len %zu);\n", inst->const_str.len); break;
                case AX_LIR_INST_FN_ADDR: fprintf(out, "fn_addr %s;\n", inst->fn_addr.sym_name); break;
                case AX_LIR_INST_SADD_OVERFLOW: fprintf(out, "sadd_overflow v%u, v%u;\n", inst->overflow_op.lhs.v, inst->overflow_op.rhs.v); break;
                case AX_LIR_INST_UADD_OVERFLOW: fprintf(out, "uadd_overflow v%u, v%u;\n", inst->overflow_op.lhs.v, inst->overflow_op.rhs.v); break;
                case AX_LIR_INST_SSUB_OVERFLOW: fprintf(out, "ssub_overflow v%u, v%u;\n", inst->overflow_op.lhs.v, inst->overflow_op.rhs.v); break;
                case AX_LIR_INST_USUB_OVERFLOW: fprintf(out, "usub_overflow v%u, v%u;\n", inst->overflow_op.lhs.v, inst->overflow_op.rhs.v); break;
                case AX_LIR_INST_SMUL_OVERFLOW: fprintf(out, "smul_overflow v%u, v%u;\n", inst->overflow_op.lhs.v, inst->overflow_op.rhs.v); break;
                case AX_LIR_INST_UMUL_OVERFLOW: fprintf(out, "umul_overflow v%u, v%u;\n", inst->overflow_op.lhs.v, inst->overflow_op.rhs.v); break;
                case AX_LIR_INST_SDIV_OVERFLOW: fprintf(out, "sdiv_overflow v%u, v%u;\n", inst->overflow_op.lhs.v, inst->overflow_op.rhs.v); break;
                case AX_LIR_INST_UDIV_OVERFLOW: fprintf(out, "udiv_overflow v%u, v%u;\n", inst->overflow_op.lhs.v, inst->overflow_op.rhs.v); break;
                case AX_LIR_INST_SREM_OVERFLOW: fprintf(out, "srem_overflow v%u, v%u;\n", inst->overflow_op.lhs.v, inst->overflow_op.rhs.v); break;
                case AX_LIR_INST_UREM_OVERFLOW: fprintf(out, "urem_overflow v%u, v%u;\n", inst->overflow_op.lhs.v, inst->overflow_op.rhs.v); break;
                case AX_LIR_INST_CALL:
                    if (inst->call.sym_name) {
                        fprintf(out, "call %s;\n", inst->call.sym_name);
                    } else {
                        fprintf(out, "call_indirect v%u;\n", inst->call.callee_vreg.v);
                    }
                    break;
                case AX_LIR_INST_ABI_ARG: fprintf(out, "abi_arg %u, v%u;\n", inst->abi_arg.index, inst->abi_arg.val.v); break;
                case AX_LIR_INST_ABI_RESULT: fprintf(out, "abi_result %u;\n", inst->abi_result.index); break;
            }
        }
        
        fprintf(out, "        ");
        AxLirTerminator *term = &bb->terminator;
        switch (term->kind) {
            case AX_LIR_TERM_JMP:
                fprintf(out, "jmp bb%u;\n", term->jmp_target.v);
                break;
            case AX_LIR_TERM_JCC:
                fprintf(out, "jcc v%u, bb%u, bb%u;\n", term->jcc.cond.v, term->jcc.then_target.v, term->jcc.else_target.v);
                break;
            case AX_LIR_TERM_SWITCH:
                fprintf(out, "switch v%u [\n", term->switch_int.cond.v);
                for (size_t k = 0; k < term->switch_int.count; k++) {
                    fprintf(out, "            %llu: bb%u,\n", (unsigned long long)term->switch_int.targets[k].value, term->switch_int.targets[k].target.v);
                }
                fprintf(out, "            otherwise: bb%u\n        ];\n", term->switch_int.otherwise.v);
                break;
            case AX_LIR_TERM_RETURN:
                fprintf(out, "return;\n");
                break;
            case AX_LIR_TERM_UNREACHABLE:
                fprintf(out, "unreachable;\n");
                break;
            case AX_LIR_TERM_ASSERT:
                fprintf(out, "assert v%u, bb%u, \"%s\";\n", term->assert_term.cond.v, term->assert_term.target.v, term->assert_term.msg);
                break;
        }
        fprintf(out, "    }\n");
    }
    fprintf(out, "}\n");
}
