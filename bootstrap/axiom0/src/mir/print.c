#include "mir/mir.h"
#include <stdio.h>

static void print_indent(FILE *out, int level) {
    for (int i = 0; i < level * 4; i++) {
        fputc(' ', out);
    }
}

static void print_local(FILE *out, AxMirLocalId id) {
    fprintf(out, "_%u", id.v);
}

static void print_bb(FILE *out, AxMirBbId id) {
    fprintf(out, "bb%u", id.v);
}

static void print_place(FILE *out, const AxMirPlace *place) {
    for (size_t i = 0; i < place->proj_count; i++) {
        switch (place->projs[i].kind) {
            case AX_MIR_PROJ_DEREF: fprintf(out, "(*"); break;
            case AX_MIR_PROJ_FIELD: fprintf(out, "("); break;
            case AX_MIR_PROJ_INDEX: fprintf(out, "("); break;
            case AX_MIR_PROJ_DOWNCAST: fprintf(out, "("); break;
        }
    }
    
    print_local(out, place->local);
    
    for (size_t i = 0; i < place->proj_count; i++) {
        switch (place->projs[i].kind) {
            case AX_MIR_PROJ_DEREF: fprintf(out, ")"); break;
            case AX_MIR_PROJ_FIELD: fprintf(out, ").%u", place->projs[i].field_idx); break;
            case AX_MIR_PROJ_INDEX: fprintf(out, ")["); print_local(out, place->projs[i].index_local); fprintf(out, "]"); break;
            case AX_MIR_PROJ_DOWNCAST: fprintf(out, " as variant#%u)", place->projs[i].variant_idx); break;
        }
    }
}

static void print_operand(FILE *out, const AxMirOperand *op) {
    switch (op->kind) {
        case AX_MIR_OP_COPY:
            fprintf(out, "copy ");
            print_place(out, &op->place);
            break;
        case AX_MIR_OP_MOVE:
            fprintf(out, "move ");
            print_place(out, &op->place);
            break;
        case AX_MIR_OP_CONST:
            fprintf(out, "const %llu", (unsigned long long)op->constant.val);
            break;
    }
}

static void print_rvalue(FILE *out, const AxMirRvalue *rv) {
    switch (rv->kind) {
        case AX_MIR_RVALUE_USE:
            print_operand(out, &rv->use);
            break;
        case AX_MIR_RVALUE_REPEAT:
            fprintf(out, "[");
            print_operand(out, &rv->repeat.op);
            fprintf(out, "; ");
            print_operand(out, &rv->repeat.count);
            fprintf(out, "]");
            break;
        case AX_MIR_RVALUE_REF:
            fprintf(out, "&%s", rv->ref.bk == AX_MIR_BORROW_MUT ? "mut " : "");
            print_place(out, &rv->ref.place);
            break;
        case AX_MIR_RVALUE_LEN:
            fprintf(out, "len(");
            print_place(out, &rv->len);
            fprintf(out, ")");
            break;
        case AX_MIR_RVALUE_CAST:
            print_operand(out, &rv->cast.op);
            fprintf(out, " as type#%u", rv->cast.ty.v);
            break;
        case AX_MIR_RVALUE_OVERFLOWS_BINARY_OP:
        case AX_MIR_RVALUE_BINARY_OP: {
            const char *op_str = "?";
            switch (rv->binary_op.op) {
                case AX_MIR_BINOP_ADD: op_str = "+"; break;
                case AX_MIR_BINOP_SUB: op_str = "-"; break;
                case AX_MIR_BINOP_MUL: op_str = "*"; break;
                case AX_MIR_BINOP_DIV: op_str = "/"; break;
                case AX_MIR_BINOP_REM: op_str = "%"; break;
                case AX_MIR_BINOP_BIT_XOR: op_str = "^"; break;
                case AX_MIR_BINOP_BIT_AND: op_str = "&"; break;
                case AX_MIR_BINOP_BIT_OR: op_str = "|"; break;
                case AX_MIR_BINOP_SHL: op_str = "<<"; break;
                case AX_MIR_BINOP_SHR: op_str = ">>"; break;
                case AX_MIR_BINOP_EQ: op_str = "=="; break;
                case AX_MIR_BINOP_LT: op_str = "<"; break;
                case AX_MIR_BINOP_LE: op_str = "<="; break;
                case AX_MIR_BINOP_NE: op_str = "!="; break;
                case AX_MIR_BINOP_GE: op_str = ">="; break;
                case AX_MIR_BINOP_GT: op_str = ">"; break;
                case AX_MIR_BINOP_OFFSET: op_str = "offset"; break;
            }
            if (rv->binary_op.op == AX_MIR_BINOP_OFFSET) {
                fprintf(out, "offset(");
                print_operand(out, &rv->binary_op.lhs);
                fprintf(out, ", ");
                print_operand(out, &rv->binary_op.rhs);
                fprintf(out, ")");
            } else {
                if (rv->kind == AX_MIR_RVALUE_OVERFLOWS_BINARY_OP) fprintf(out, "overflows(");
                print_operand(out, &rv->binary_op.lhs);
                fprintf(out, " %s ", op_str);
                print_operand(out, &rv->binary_op.rhs);
                if (rv->kind == AX_MIR_RVALUE_OVERFLOWS_BINARY_OP) fprintf(out, ")");
            }
            break;
        }
        case AX_MIR_RVALUE_UNARY_OP:
            if (rv->unary_op.op == AX_MIR_UNOP_NOT) fprintf(out, "!");
            else if (rv->unary_op.op == AX_MIR_UNOP_BITNOT) fprintf(out, "~");
            else fprintf(out, "-");
            print_operand(out, &rv->unary_op.operand);
            break;
        case AX_MIR_RVALUE_DISCRIMINANT:
            fprintf(out, "discriminant(");
            print_place(out, &rv->discriminant);
            fprintf(out, ")");
            break;
        case AX_MIR_RVALUE_AGGREGATE:
            fprintf(out, "aggregate(variant#%u, [", rv->aggregate.variant_idx);
            for (size_t i = 0; i < rv->aggregate.operand_count; i++) {
                if (i > 0) fprintf(out, ", ");
                print_operand(out, &rv->aggregate.operands[i]);
            }
            fprintf(out, "])");
            break;
    }
}

static void print_terminator(FILE *out, const AxMirTerminator *term, int level) {
    print_indent(out, level);
    switch (term->kind) {
        case AX_MIR_TERM_GOTO:
            fprintf(out, "goto -> ");
            print_bb(out, term->goto_target);
            fprintf(out, ";\n");
            break;
        case AX_MIR_TERM_SWITCH_INT:
            fprintf(out, "switchInt(");
            print_operand(out, &term->switch_int.discr);
            fprintf(out, ") -> [");
            for (size_t i = 0; i < term->switch_int.targets.count; i++) {
                if (i > 0) fprintf(out, ", ");
                fprintf(out, "%llu: ", (unsigned long long)term->switch_int.targets.values[i].value);
                print_bb(out, term->switch_int.targets.values[i].target);
            }
            if (term->switch_int.targets.count > 0) {
                fprintf(out, ", ");
            }
            fprintf(out, "otherwise: ");
            print_bb(out, term->switch_int.targets.otherwise);
            fprintf(out, "];\n");
            break;
        case AX_MIR_TERM_RETURN:
            fprintf(out, "return;\n");
            break;
        case AX_MIR_TERM_UNREACHABLE:
            fprintf(out, "unreachable;\n");
            break;
        case AX_MIR_TERM_DROP:
            fprintf(out, "drop(");
            print_place(out, &term->drop.place);
            fprintf(out, ") -> [return: ");
            print_bb(out, term->drop.target);
            fprintf(out, ", unwind: ");
            print_bb(out, term->drop.unwind);
            fprintf(out, "];\n");
            break;
        case AX_MIR_TERM_CALL:
            print_place(out, &term->call.destination);
            fprintf(out, " = ");
            print_operand(out, &term->call.func);
            fprintf(out, "(");
            for (size_t i = 0; i < term->call.arg_count; i++) {
                if (i > 0) fprintf(out, ", ");
                print_operand(out, &term->call.args[i]);
            }
            fprintf(out, ") -> [return: ");
            print_bb(out, term->call.target);
            fprintf(out, ", unwind: ");
            print_bb(out, term->call.unwind);
            fprintf(out, "];\n");
            break;
        case AX_MIR_TERM_ASSERT:
            fprintf(out, "assert(");
            print_operand(out, &term->assert.cond);
            if (term->assert.msg) {
                fprintf(out, " == %s, \"%s\") -> [return: ", term->assert.expected ? "true" : "false", term->assert.msg);
            } else {
                fprintf(out, " == %s) -> [return: ", term->assert.expected ? "true" : "false");
            }
            print_bb(out, term->assert.target);
            fprintf(out, ", unwind: ");
            print_bb(out, term->assert.unwind);
            fprintf(out, "];\n");
            break;
    }
}

void ax_mir_print(FILE *out, const AxMirBody *body) {
    fprintf(out, "mir_body {\n");
    for (size_t i = 0; i < body->local_count; i++) {
        print_indent(out, 1);
        fprintf(out, "let %s_%zu: type#%u;\n", body->locals[i].mut ? "mut " : "", i, body->locals[i].ty.v);
    }
    
    for (size_t i = 0; i < body->bb_count; i++) {
        print_indent(out, 1);
        fprintf(out, "bb%zu: {\n", i);
        
        AxMirBb *bb = &body->bbs[i];
        for (size_t j = 0; j < bb->stmt_count; j++) {
            print_indent(out, 2);
            AxMirStmt *stmt = &bb->stmts[j];
            switch (stmt->kind) {
                case AX_MIR_STMT_ASSIGN:
                    print_place(out, &stmt->assign.place);
                    fprintf(out, " = ");
                    print_rvalue(out, &stmt->assign.rvalue);
                    fprintf(out, ";\n");
                    break;
                case AX_MIR_STMT_STORAGE_LIVE:
                    fprintf(out, "StorageLive(");
                    print_local(out, stmt->storage_live);
                    fprintf(out, ");\n");
                    break;
                case AX_MIR_STMT_STORAGE_DEAD:
                    fprintf(out, "StorageDead(");
                    print_local(out, stmt->storage_dead);
                    fprintf(out, ");\n");
                    break;
            }
        }
        print_terminator(out, &bb->terminator, 2);
        
        print_indent(out, 1);
        fprintf(out, "}\n");
    }
    
    fprintf(out, "}\n");
}
