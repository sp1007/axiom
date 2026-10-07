#include "mir/mir.h"
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <ctype.h>

typedef struct {
    const char *text;
    size_t pos;
    size_t len;
    AxArena *arena;
    TypeInterner *interner;
    TypeId type_map[1024];
} MirParser;

static void skip_ws(MirParser *p) {
    
    while (p->pos < p->len) {
        unsigned char c = (unsigned char)p->text[p->pos];
        if (c == ' ' || c == '\n' || c == '\r' || c == '\t' || c == '\v' || c == '\f') {
            p->pos++;
        } else {
            break;
        }
    }
}

static bool match_str(MirParser *p, const char *s) {
    skip_ws(p);
    size_t slen = strlen(s);
    bool match = (p->pos + slen <= p->len && strncmp(p->text + p->pos, s, slen) == 0);
    if (match) {
        p->pos += slen;
        return true;
    }
    return false;
}

#define expect_str(p, s) expect_str_impl(p, s)
static void expect_str_impl(MirParser *p, const char *s) {
    if (!match_str(p, s)) {
        AX_ICE("MIR parse error: expected '%s' at '%s'", s, p->text + p->pos);
    }
}

static bool match_ident(MirParser *p, const char *s) {
    skip_ws(p);
    size_t slen = strlen(s);
    if (p->pos + slen <= p->len && strncmp(p->text + p->pos, s, slen) == 0) {
        if (isalnum((unsigned char)s[slen - 1]) || s[slen - 1] == '_') {
            if (p->pos + slen < p->len && (isalnum((unsigned char)p->text[p->pos + slen]) || p->text[p->pos + slen] == '_')) {
                return false;
            }
        }
        p->pos += slen;
        return true;
    }
    return false;
}

static uint64_t parse_int(MirParser *p) {
    skip_ws(p);
    uint64_t val = 0;
    bool has_digit = false;
    while (p->pos < p->len && isdigit((unsigned char)p->text[p->pos])) {
        val = val * 10 + (p->text[p->pos] - '0');
        p->pos++;
        has_digit = true;
    }
    if (!has_digit) {
        AX_ICE("MIR parse error: expected integer");
    }
    return val;
}

static AxMirLocalId parse_local(MirParser *p) {
    expect_str(p, "_");
    uint32_t v = (uint32_t)parse_int(p);
    return (AxMirLocalId){v};
}

static AxMirBbId parse_bb(MirParser *p) {
    expect_str(p, "bb");
    uint32_t v = (uint32_t)parse_int(p);
    return (AxMirBbId){v};
}

static TypeId parse_type(MirParser *p) {
    expect_str(p, "type#");
    uint32_t v = (uint32_t)parse_int(p);
    if (v < 1024 && p->type_map[v].v != 0) {
        return p->type_map[v];
    }
    return (TypeId){v};
}

static AxMirPlace parse_place(MirParser *p) {
    AxMirPlace place = {0};
    AxMirProjKind left_stack[16];
    size_t left_count = 0;
    
    while (true) {
        if (match_str(p, "(*")) {
            left_stack[left_count++] = AX_MIR_PROJ_DEREF;
        } else if (match_str(p, "(")) {
            left_stack[left_count++] = AX_MIR_PROJ_FIELD; // placeholder
        } else {
            break;
        }
    }
    
    place.local = parse_local(p);
    
    AxMirProjection projs[16];
    size_t proj_count = 0;
    
    for (size_t i = 0; i < left_count; i++) {
        if (left_stack[i] == AX_MIR_PROJ_DEREF) {
            expect_str(p, ")");
            projs[proj_count++].kind = AX_MIR_PROJ_DEREF;
        } else {
            if (match_str(p, ").")) {
                projs[proj_count].kind = AX_MIR_PROJ_FIELD;
                projs[proj_count].field_idx = (uint32_t)parse_int(p);
                proj_count++;
            } else if (match_str(p, ")[")) {
                projs[proj_count].kind = AX_MIR_PROJ_INDEX;
                projs[proj_count].index_local = parse_local(p);
                expect_str(p, "]");
                proj_count++;
            } else if (match_str(p, " as variant#")) {
                projs[proj_count].kind = AX_MIR_PROJ_DOWNCAST;
                projs[proj_count].variant_idx = (uint32_t)parse_int(p);
                expect_str(p, ")");
                proj_count++;
            } else {
                AX_ICE("Invalid right projection");
            }
        }
    }
    
    place.proj_count = proj_count;
    if (proj_count > 0) {
        place.projs = AX_ARENA_NEW_ARRAY(p->arena, AxMirProjection, proj_count);
        memcpy(place.projs, projs, sizeof(AxMirProjection) * proj_count);
    }
    return place;
}

static AxMirOperand parse_operand(MirParser *p) {
    AxMirOperand op = {0};
    if (match_ident(p, "copy")) {
        op.kind = AX_MIR_OP_COPY;
        op.place = parse_place(p);
    } else if (match_ident(p, "move")) {
        op.kind = AX_MIR_OP_MOVE;
        op.place = parse_place(p);
    } else if (match_ident(p, "const")) {
        op.kind = AX_MIR_OP_CONST;
        if (match_ident(p, "true")) {
            op.constant.val = 1;
        } else if (match_ident(p, "false")) {
            op.constant.val = 0;
        } else {
            op.constant.val = parse_int(p);
        }
        op.constant.ty.v = 0;
    } else {
        op.kind = AX_MIR_OP_COPY;
        op.place = parse_place(p);
    }
    return op;
}

static AxMirBinOp parse_binop_symbol(MirParser *p) {
    if (match_str(p, "+")) return AX_MIR_BINOP_ADD;
    if (match_str(p, "-")) return AX_MIR_BINOP_SUB;
    if (match_str(p, "*")) return AX_MIR_BINOP_MUL;
    if (match_str(p, "/")) return AX_MIR_BINOP_DIV;
    if (match_str(p, "%")) return AX_MIR_BINOP_REM;
    if (match_str(p, "==")) return AX_MIR_BINOP_EQ;
    if (match_str(p, "!=")) return AX_MIR_BINOP_NE;
    if (match_str(p, "<=")) return AX_MIR_BINOP_LE;
    if (match_str(p, ">=")) return AX_MIR_BINOP_GE;
    if (match_str(p, "<<")) return AX_MIR_BINOP_SHL;
    if (match_str(p, ">>")) return AX_MIR_BINOP_SHR;
    if (match_str(p, "<")) return AX_MIR_BINOP_LT;
    if (match_str(p, ">")) return AX_MIR_BINOP_GT;
    if (match_str(p, "^")) return AX_MIR_BINOP_BIT_XOR;
    if (match_str(p, "&")) return AX_MIR_BINOP_BIT_AND;
    if (match_str(p, "|")) return AX_MIR_BINOP_BIT_OR;
    return (AxMirBinOp)-1;
}

static AxMirRvalue parse_rvalue(MirParser *p) {
    AxMirRvalue rv = {0};
    if (match_ident(p, "len(")) {
        rv.kind = AX_MIR_RVALUE_LEN;
        rv.len = parse_place(p);
        expect_str(p, ")");
    } else if (match_ident(p, "overflows(")) {
        rv.kind = AX_MIR_RVALUE_OVERFLOWS_BINARY_OP;
        AxMirOperand lhs = parse_operand(p);
        AxMirBinOp op = parse_binop_symbol(p);
        AxMirOperand rhs = parse_operand(p);
        expect_str(p, ")");
        rv.binary_op.op = op;
        rv.binary_op.lhs = lhs;
        rv.binary_op.rhs = rhs;
    } else if (match_str(p, "&mut ")) {
        rv.kind = AX_MIR_RVALUE_REF;
        rv.ref.bk = AX_MIR_BORROW_MUT;
        rv.ref.place = parse_place(p);
    } else if (match_str(p, "&")) {
        rv.kind = AX_MIR_RVALUE_REF;
        rv.ref.bk = AX_MIR_BORROW_SHARED;
        rv.ref.place = parse_place(p);
    } else if (match_ident(p, "aggregate(variant#")) {
        rv.kind = AX_MIR_RVALUE_AGGREGATE;
        rv.aggregate.variant_idx = (uint32_t)parse_int(p);
        expect_str(p, ",");
        expect_str(p, "[");
        AxMirOperand ops[16];
        size_t count = 0;
        while (!match_str(p, "]")) {
            if (count > 0) expect_str(p, ",");
            ops[count++] = parse_operand(p);
        }
        expect_str(p, ")");
        rv.aggregate.operand_count = count;
        rv.aggregate.operands = AX_ARENA_NEW_ARRAY(p->arena, AxMirOperand, count);
        memcpy(rv.aggregate.operands, ops, sizeof(AxMirOperand) * count);
    } else if (match_ident(p, "offset(")) {
        rv.kind = AX_MIR_RVALUE_BINARY_OP;
        rv.binary_op.op = AX_MIR_BINOP_OFFSET;
        rv.binary_op.lhs = parse_operand(p);
        expect_str(p, ",");
        rv.binary_op.rhs = parse_operand(p);
        expect_str(p, ")");
    } else if (match_str(p, "!")) {
        rv.kind = AX_MIR_RVALUE_UNARY_OP;
        rv.unary_op.op = AX_MIR_UNOP_NOT;
        rv.unary_op.operand = parse_operand(p);
    } else if (match_str(p, "~")) {
        rv.kind = AX_MIR_RVALUE_UNARY_OP;
        rv.unary_op.op = AX_MIR_UNOP_BITNOT;
        rv.unary_op.operand = parse_operand(p);
    } else if (match_str(p, "-")) {
        rv.kind = AX_MIR_RVALUE_UNARY_OP;
        rv.unary_op.op = AX_MIR_UNOP_NEG;
        rv.unary_op.operand = parse_operand(p);
    } else if (match_ident(p, "[")) {
        rv.kind = AX_MIR_RVALUE_REPEAT;
        rv.repeat.op = parse_operand(p);
        expect_str(p, ";");
        rv.repeat.count = parse_operand(p);
        expect_str(p, "]");
    } else if (match_ident(p, "discriminant(")) {
        rv.kind = AX_MIR_RVALUE_DISCRIMINANT;
        rv.discriminant = parse_place(p);
        expect_str(p, ")");
    } else {
        AxMirOperand op1 = parse_operand(p);
        if (match_ident(p, "as")) {
            rv.kind = AX_MIR_RVALUE_CAST;
            rv.cast.op = op1;
            rv.cast.ty = parse_type(p);
        } else {
            AxMirBinOp binop = parse_binop_symbol(p);
            if ((int)binop != -1) {
                rv.kind = AX_MIR_RVALUE_BINARY_OP;
                rv.binary_op.op = binop;
                rv.binary_op.lhs = op1;
                rv.binary_op.rhs = parse_operand(p);
            } else {
                rv.kind = AX_MIR_RVALUE_USE;
                rv.use = op1;
            }
        }
    }
    return rv;
}

static AxMirStmt parse_stmt(MirParser *p) {
    AxMirStmt stmt = {0};
    skip_ws(p);
    if (match_ident(p, "StorageLive(")) {
        stmt.kind = AX_MIR_STMT_STORAGE_LIVE;
        stmt.storage_live = parse_local(p);
        expect_str(p, ")");
    } else if (match_ident(p, "StorageDead(")) {
        stmt.kind = AX_MIR_STMT_STORAGE_DEAD;
        stmt.storage_dead = parse_local(p);
        expect_str(p, ")");
    } else {
        stmt.kind = AX_MIR_STMT_ASSIGN;
        stmt.assign.place = parse_place(p);
        expect_str(p, "=");
        stmt.assign.rvalue = parse_rvalue(p);
    }
    expect_str(p, ";");
    return stmt;
}

static AxMirTerminator parse_terminator(MirParser *p, AxMirPlace *call_dest) {
    AxMirTerminator term = {0};
    if (match_ident(p, "goto")) {
        expect_str(p, "->");
        term.kind = AX_MIR_TERM_GOTO;
        term.goto_target = parse_bb(p);
    } else if (match_ident(p, "return")) {
        term.kind = AX_MIR_TERM_RETURN;
    } else if (match_ident(p, "unreachable")) {
        term.kind = AX_MIR_TERM_UNREACHABLE;
    } else if (match_ident(p, "drop(")) {
        term.kind = AX_MIR_TERM_DROP;
        term.drop.place = parse_place(p);
        expect_str(p, ")");
        expect_str(p, "->");
        expect_str(p, "[");
        expect_str(p, "return:");
        term.drop.target = parse_bb(p);
        expect_str(p, ",");
        expect_str(p, "unwind:");
        term.drop.unwind = parse_bb(p);
        expect_str(p, "]");
    } else if (match_ident(p, "switchInt(")) {
        term.kind = AX_MIR_TERM_SWITCH_INT;
        term.switch_int.discr = parse_operand(p);
        expect_str(p, ")");
        expect_str(p, "->");
        expect_str(p, "[");
        AxMirSwitchTarget targets[16];
        size_t count = 0;
        while (!match_ident(p, "otherwise:")) {
            targets[count].value = parse_int(p);
            expect_str(p, ":");
            targets[count].target = parse_bb(p);
            if (match_str(p, ",")) {}
            count++;
        }
        term.switch_int.targets.otherwise = parse_bb(p);
        expect_str(p, "]");
        term.switch_int.targets.count = count;
        if (count > 0) {
            term.switch_int.targets.values = AX_ARENA_NEW_ARRAY(p->arena, AxMirSwitchTarget, count);
            memcpy(term.switch_int.targets.values, targets, sizeof(AxMirSwitchTarget) * count);
        }
    } else if (match_ident(p, "assert(")) {
        term.kind = AX_MIR_TERM_ASSERT;
        term.assert.cond = parse_operand(p);
        expect_str(p, "==");
        if (match_ident(p, "true")) {
            term.assert.expected = true;
        } else if (match_ident(p, "false")) {
            term.assert.expected = false;
        } else {
            AX_ICE("Expected true or false in assert");
        }
        if (match_str(p, ",")) {
            skip_ws(p);
            expect_str(p, "\"");
            size_t start = p->pos;
            while (p->pos < p->len && p->text[p->pos] != '"') p->pos++;
            size_t len = p->pos - start;
            char *msg = AX_ARENA_NEW_ARRAY(p->arena, char, len + 1);
            memcpy(msg, p->text + start, len);
            msg[len] = '\0';
            term.assert.msg = msg;
            expect_str(p, "\"");
        } else {
            term.assert.msg = NULL;
        }
        expect_str(p, ")");
        expect_str(p, "->");
        expect_str(p, "[");
        expect_str(p, "return:");
        term.assert.target = parse_bb(p);
        expect_str(p, ",");
        expect_str(p, "unwind:");
        term.assert.unwind = parse_bb(p);
        expect_str(p, "]");
    } else if (call_dest != NULL) {
        // It's a call terminator (parsed place = call_dest)
        term.kind = AX_MIR_TERM_CALL;
        term.call.destination = *call_dest;
        term.call.func = parse_operand(p);
        expect_str(p, "(");
        AxMirOperand args[16];
        size_t count = 0;
        while (!match_str(p, ")")) {
            if (count > 0) expect_str(p, ",");
            args[count++] = parse_operand(p);
        }
        expect_str(p, "->");
        expect_str(p, "[");
        expect_str(p, "return:");
        term.call.target = parse_bb(p);
        expect_str(p, ",");
        expect_str(p, "unwind:");
        term.call.unwind = parse_bb(p);
        expect_str(p, "]");
        term.call.arg_count = count;
        if (count > 0) {
            term.call.args = AX_ARENA_NEW_ARRAY(p->arena, AxMirOperand, count);
            memcpy(term.call.args, args, sizeof(AxMirOperand) * count);
        }
    } else {
        AX_ICE("MIR parse error: unknown terminator");
    }
    expect_str(p, ";");
    return term;
}

AxMirBody *ax_mir_parse(const char *text, TypeInterner *interner, AxArena *arena) {
    MirParser p = { .text = text, .pos = 0, .len = strlen(text), .arena = arena, .interner = interner };
    memset(p.type_map, 0, sizeof(p.type_map));
    AxMirBody *body = AX_ARENA_NEW(arena, AxMirBody);
    
    expect_str(&p, "mir_body");
    expect_str(&p, "{");
    
    while (match_ident(&p, "type")) {
        uint32_t id = (uint32_t)parse_int(&p);
        expect_str(&p, "=");
        expect_str(&p, "fn(");
        TypeId params[16];
        size_t param_count = 0;
        while (!match_str(&p, ")")) {
            if (param_count > 0) expect_str(&p, ",");
            params[param_count++] = parse_type(&p);
        }
        expect_str(&p, "->");
        TypeId ret_ty = parse_type(&p);
        expect_str(&p, ";");
        
        AxType t = {0};
        t.kind = AX_TY_FN;
        t.fn.param_count = param_count;
        if (param_count > 0) {
            t.fn.param_types = AX_ARENA_NEW_ARRAY(arena, TypeId, param_count);
            memcpy(t.fn.param_types, params, sizeof(TypeId) * param_count);
        }
        t.fn.ret_type = ret_ty;
        
        if (id < 1024) {
            p.type_map[id] = ax_intern_type(interner, &t);
        }
    }

    AxMirLocalDecl locals[256];
    size_t local_count = 0;
    while (match_ident(&p, "let")) {
        bool mut = match_ident(&p, "mut");
        AxMirLocalId id = parse_local(&p);
        expect_str(&p, ":");
        TypeId ty = parse_type(&p);
        expect_str(&p, ";");
        locals[local_count].kind = (id.v == 0) ? AX_MIR_LOCAL_RETURN : AX_MIR_LOCAL_USER;
        locals[local_count].mut = mut;
        locals[local_count].ty = ty;
        local_count++;
    }
    body->local_count = local_count;
    body->locals = AX_ARENA_NEW_ARRAY(arena, AxMirLocalDecl, local_count);
    memcpy(body->locals, locals, sizeof(AxMirLocalDecl) * local_count);
    
    AxMirBb bbs[256];
    size_t bb_count = 0;
    while (match_str(&p, "bb")) {
        uint32_t bbid = (uint32_t)parse_int(&p);
        (void)bbid;
        expect_str(&p, ":");
        expect_str(&p, "{");
        
        bbs[bb_count].terminator.kind = 255;
        AxMirStmt stmts[128];
        size_t stmt_count = 0;
        
        while (p.pos < p.len) {
            size_t saved_check = p.pos;
            if (match_str(&p, "}")) {
                p.pos = saved_check;
                break;
            }
            
            size_t saved = p.pos;
            bool is_term = match_ident(&p, "goto") || match_ident(&p, "return") || 
                           match_ident(&p, "unreachable") || match_ident(&p, "drop") || 
                           match_ident(&p, "switchInt") || match_ident(&p, "assert");
            p.pos = saved;
            
            if (is_term) {
                bbs[bb_count].terminator = parse_terminator(&p, NULL);
                break;
            } else {
                // Not a standalone terminator. Could be a statement OR a call terminator.
                // Call terminator looks like: `_1 = ... (...) -> [return: bb1, unwind: bb2];`
                // Statement looks like: `_1 = ...;` or `StorageLive(_1);`
                if (match_ident(&p, "StorageLive(") || match_ident(&p, "StorageDead(")) {
                    p.pos = saved;
                    AxMirStmt tmp = parse_stmt(&p); stmts[stmt_count++] = tmp;
                } else {
                    AxMirPlace place = parse_place(&p);
                    expect_str(&p, "=");
                    
                    // Now we check if what follows is a call or rvalue.
                    // A call function operand could be a const or copy/move, but `print.c` prints:
                    // `print_place(io, &term->call.destination); fprintf(io->out, " = "); print_operand(io, &term->call.func); fprintf(io->out, "(");`
                    // Wait! Since operand parsing might consume `(` ? No, operand doesn't consume `(`.
                    size_t op_saved = p.pos;
                    bool is_call = false;
                    for (size_t i = p.pos; i < p.len && p.text[i] != ';' && p.text[i] != '}'; i++) {
                        if (p.text[i] == '-' && i + 1 < p.len && p.text[i+1] == '>') {
                            is_call = true;
                            break;
                        }
                    }
                    if (is_call) {
                        p.pos = op_saved;
                        bbs[bb_count].terminator = parse_terminator(&p, &place);
                        break;
                    } else {
                        p.pos = saved;
                        AxMirStmt tmp = parse_stmt(&p); stmts[stmt_count++] = tmp;
                    }
                }
            }
        }
        
        
        expect_str(&p, "}");
        bbs[bb_count].stmt_count = stmt_count;
        if (stmt_count > 0) {
            bbs[bb_count].stmts = AX_ARENA_NEW_ARRAY(arena, AxMirStmt, stmt_count);
            memcpy(bbs[bb_count].stmts, stmts, sizeof(AxMirStmt) * stmt_count);
        }
        bb_count++;
    }
    
    body->bb_count = bb_count;
    body->bbs = AX_ARENA_NEW_ARRAY(arena, AxMirBb, bb_count);
    memcpy(body->bbs, bbs, sizeof(AxMirBb) * bb_count);
    
    expect_str(&p, "}");
    return body;
}
