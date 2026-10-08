#include "syntax/parse.h"
#include "diag/diag.h"
#include "kernel/arena.h"
#include "lex/lex.h"
#include "syntax/ast.h"
#include <string.h>
#include <stdbool.h>

typedef struct Parser {
    AxArena *arena;
    const AxToken *tokens;
    size_t count;
    size_t pos;
    AxDiagSink *sink;
    StrInterner *interner;
    bool mode_on;
    bool no_struct;
    bool type_tentative;
    bool allow_bodiless_fn;
    int tentative;
    bool tentative_failed;
    size_t split_len;
    size_t split_idx[64];
    AxToken split_tok[64];
} Parser;

static inline const AxToken *peek(Parser *p) {
    if (p->pos < p->count) return &p->tokens[p->pos];
    return &p->tokens[p->count - 1];
}

static inline const AxToken *peek_nth(Parser *p, size_t n) {
    if (p->pos + n < p->count) return &p->tokens[p->pos + n];
    return &p->tokens[p->count - 1];
}

static inline const AxToken *advance(Parser *p) {
    if (p->pos < p->count) return &p->tokens[p->pos++];
    return &p->tokens[p->count - 1];
}

static inline bool check(Parser *p, AxTokenKind kind) {
    return peek(p)->kind == kind;
}

static inline bool consume(Parser *p, AxTokenKind kind) {
    if (check(p, kind)) {
        advance(p);
        return true;
    }
    return false;
}

static void report(Parser *p, Span span, AxDiagCode code, const char *msg) {
    if (p->tentative > 0) {
        p->tentative_failed = true;
        return;
    }
    AxDiagnostic diag = {0};
    diag.code = code;
    diag.severity = AX_DIAG_ERROR;
    diag.primary = span;
    diag.message = msg;
    ax_diag_sink_report(p->sink, &diag);
}

static void expect(Parser *p, AxTokenKind kind, AxDiagCode code, const char *msg) {
    if (check(p, kind)) {
        advance(p);
    } else {
        report(p, peek(p)->span, code, msg);
    }
}

static void *alloc_node(Parser *p, size_t size) {
    void *ptr = ax_arena_alloc(p->arena, size, 8);
    memset(ptr, 0, size);
    return ptr;
}
#define NEW_NODE(p, type) ((type *)alloc_node(p, sizeof(type)))

// Forward decls
static AxAstExpr *parse_expr(Parser *p);
static AxAstExpr *parse_expr_prec(Parser *p, int min_prec);
static AxAstExpr *parse_header_expr(Parser *p);
static AxAstType *parse_type(Parser *p);
static AxAstPat *parse_pattern(Parser *p);
static AxAstPat *parse_pat_no_or(Parser *p);
static AxAstBlock *parse_block(Parser *p);
static AxAstItem *parse_item(Parser *p);
static AxAstStmt *parse_stmt(Parser *p);
static AxAstGenericArgs *parse_generic_args(Parser *p);
static AxAstAttr *parse_attributes(Parser *p);
static AxAstVis parse_visibility(Parser *p);
static AxAstGenericParams *parse_generic_params(Parser *p);
static AxAstWhereClause *parse_where_clause(Parser *p);
static AxAstType *parse_bounds(Parser *p);

static int get_infix_prec(AxTokenKind k) {
    switch (k) {
        case AX_TOK_DOT: case AX_TOK_LPAREN: case AX_TOK_LBRACKET: case AX_TOK_QUESTION: case AX_TOK_ARROW: return 1;
        case AX_TOK_KW_AS: return 3;
        case AX_TOK_STAR: case AX_TOK_SLASH: case AX_TOK_PERCENT: return 4;
        case AX_TOK_PLUS: case AX_TOK_MINUS: return 5;
        case AX_TOK_SHL: case AX_TOK_SHR: return 6;
        case AX_TOK_AMP: return 7;
        case AX_TOK_CARET: return 8;
        case AX_TOK_PIPE: return 9;
        case AX_TOK_EQ_EQ: case AX_TOK_BANG_EQ: case AX_TOK_LT: case AX_TOK_LT_EQ: case AX_TOK_GT: case AX_TOK_GT_EQ: return 10;
        case AX_TOK_AMP_AMP: return 11;
        case AX_TOK_PIPE_PIPE: return 12;
        case AX_TOK_DOT_DOT: case AX_TOK_DOT_DOT_EQ: return 13;
        default: return 0;
    }
}

static void sync_to_term(Parser *p) {
    while (!check(p, AX_TOK_EOF) && !check(p, AX_TOK_SEMI) && !check(p, AX_TOK_RBRACE)) {
        if (p->mode_on && (peek(p)->flags & AX_TOK_FLAG_NL_BEFORE)) {
            break;
        }
        advance(p);
    }
}

static AxAstDottedName parse_dotted_name(Parser *p) {
    AxAstDottedName path = {0};
    path.span = peek(p)->span;
    StrId buf[32];
    size_t count = 0;
    while (!check(p, AX_TOK_EOF) && count < 32) {
        if (check(p, AX_TOK_IDENT)) {
            buf[count++] = peek(p)->val.ident_val;
            advance(p);
        } else {
            report(p, peek(p)->span, AX_PARSE_EXPECTED_TOKEN, "Expected identifier");
            break;
        }
        if (consume(p, AX_TOK_DOT)) {
            continue;
        }
        break;
    }
    path.count = count;
    path.segments = alloc_node(p, sizeof(StrId) * count);
    for (size_t i = 0; i < count; i++) path.segments[i] = buf[i];
    return path;
}

static AxAstUseTree *parse_use_tree(Parser *p) {
    AxAstUseTree *tree = NEW_NODE(p, AxAstUseTree);
    tree->span = peek(p)->span;
    tree->path = parse_dotted_name(p);
    if (consume(p, AX_TOK_KW_AS)) {
        if (check(p, AX_TOK_IDENT)) {
            tree->alias = peek(p)->val.ident_val;
            advance(p);
        } else {
            report(p, peek(p)->span, AX_PARSE_EXPECTED_TOKEN, "Expected alias identifier");
        }
    } else if (consume(p, AX_TOK_DOT)) {
        expect(p, AX_TOK_LBRACE, AX_PARSE_EXPECTED_TOKEN, "Expected '{'");
        AxAstUseTree **curr = &tree->subtrees;
        while (!check(p, AX_TOK_RBRACE) && !check(p, AX_TOK_EOF)) {
            *curr = parse_use_tree(p);
            curr = &(*curr)->next;
            if (!consume(p, AX_TOK_COMMA)) break;
        }
        expect(p, AX_TOK_RBRACE, AX_PARSE_UNCLOSED_DELIMITER, "Expected '}'");
    }
    return tree;
}

static AxAstBinOp token_to_binop(AxTokenKind k) {
    switch (k) {
        case AX_TOK_PLUS: return AX_BINOP_ADD;
        case AX_TOK_MINUS: return AX_BINOP_SUB;
        case AX_TOK_STAR: return AX_BINOP_MUL;
        case AX_TOK_SLASH: return AX_BINOP_DIV;
        case AX_TOK_PERCENT: return AX_BINOP_REM;
        case AX_TOK_AMP: return AX_BINOP_BITAND;
        case AX_TOK_PIPE: return AX_BINOP_BITOR;
        case AX_TOK_CARET: return AX_BINOP_BITXOR;
        case AX_TOK_SHL: return AX_BINOP_SHL;
        case AX_TOK_SHR: return AX_BINOP_SHR;
        case AX_TOK_EQ_EQ: return AX_BINOP_EQ;
        case AX_TOK_BANG_EQ: return AX_BINOP_NE;
        case AX_TOK_LT: return AX_BINOP_LT;
        case AX_TOK_LT_EQ: return AX_BINOP_LE;
        case AX_TOK_GT: return AX_BINOP_GT;
        case AX_TOK_GT_EQ: return AX_BINOP_GE;
        case AX_TOK_AMP_AMP: return AX_BINOP_LOGAND;
        case AX_TOK_PIPE_PIPE: return AX_BINOP_LOGOR;
        default: return AX_BINOP_ADD;
    }
}

static void split_gt(Parser *p, AxTokenKind rest) {
    if (p->tentative > 0) {
        if (p->split_len >= sizeof(p->split_idx) / sizeof(p->split_idx[0])) {
            p->tentative_failed = true;
            return;
        }
        p->split_idx[p->split_len] = p->pos;
        p->split_tok[p->split_len] = *peek(p);
        p->split_len++;
    }
    AxToken *mut_tok = (AxToken *)peek(p);
    mut_tok->kind = rest;
    mut_tok->span.start += 1;
    mut_tok->flags &= ~AX_TOK_FLAG_NL_BEFORE;
}

static void split_rollback(Parser *p, size_t mark) {
    while (p->split_len > mark) {
        p->split_len--;
        AxToken *mut_tok = (AxToken *)&p->tokens[p->split_idx[p->split_len]];
        *mut_tok = p->split_tok[p->split_len];
    }
}

static AxAstGenericArgs *parse_generic_args(Parser *p) {
    if (!check(p, AX_TOK_LT)) return NULL;
    AxAstGenericArgs *args = NEW_NODE(p, AxAstGenericArgs);
    args->span = peek(p)->span;
    advance(p);
    
    bool old = p->mode_on;
    p->mode_on = false;
    
    AxAstGenericArg **curr = &args->args;
    while (!check(p, AX_TOK_GT) && !check(p, AX_TOK_SHR) && !check(p, AX_TOK_GT_EQ) && !check(p, AX_TOK_SHR_EQ) && !check(p, AX_TOK_EOF)) {
        AxAstGenericArg *arg = NEW_NODE(p, AxAstGenericArg);
        arg->span = peek(p)->span;
        if (check(p, AX_TOK_IDENT) && peek_nth(p, 1)->kind == AX_TOK_EQ) {
            arg->name = peek(p)->val.ident_val;
            advance(p); // IDENT
            advance(p); // =
        }
        arg->type = parse_type(p);
        *curr = arg;
        curr = &arg->next;
        if (!consume(p, AX_TOK_COMMA)) break;
    }
    
    if (check(p, AX_TOK_SHR)) {
        split_gt(p, AX_TOK_GT);
    } else if (check(p, AX_TOK_GT_EQ)) {
        split_gt(p, AX_TOK_EQ);
    } else if (check(p, AX_TOK_SHR_EQ)) {
        split_gt(p, AX_TOK_GT_EQ);
    } else if (check(p, AX_TOK_GT)) {
        advance(p);
    } else {
        report(p, peek(p)->span, AX_PARSE_EXPECTED_TOKEN, "Expected '>'");
    }
    
    p->mode_on = old;
    return args;
}

typedef enum {
    GA_FOLLOW_NONE,        /* cast type (AXS-GRM-054): no follower condition */
    GA_FOLLOW_CALL_DOT,    /* `(` or `.` */
    GA_FOLLOW_CALL_DOT_BRACE /* `(`, `.` or `{` (struct literals allowed, AXS-GRM-059) */
} GenericFollow;

/* AXS-GRM-056: tentative parse of GenericArgs. Commits (returns the args) iff the parse succeeds
   without any diagnostic and the follower rule holds; otherwise restores the position and the
   token stream and returns NULL. Reports no diagnostics. */
static AxAstGenericArgs *try_generic_args(Parser *p, GenericFollow follow) {
    if (!check(p, AX_TOK_LT)) return NULL;
    if (p->mode_on && (peek(p)->flags & AX_TOK_FLAG_NL_BEFORE)) return NULL;
    size_t pos = p->pos;
    size_t split_mark = p->split_len;
    bool outer_failed = p->tentative_failed;
    p->tentative++;
    p->tentative_failed = false;
    
    /* temporarily disable no_struct & type_tentative so parse_generic_args behaves deterministically */
    bool old_no_struct = p->no_struct;
    bool old_type_tentative = p->type_tentative;
    p->no_struct = false;
    p->type_tentative = false;
    
    AxAstGenericArgs *args = parse_generic_args(p);
    
    p->no_struct = old_no_struct;
    p->type_tentative = old_type_tentative;
    
    bool ok = !p->tentative_failed;
    p->tentative--;
    p->tentative_failed = outer_failed;
    if (ok && follow != GA_FOLLOW_NONE) {
        const AxToken *t = peek(p);
        bool nl = p->mode_on && (t->flags & AX_TOK_FLAG_NL_BEFORE) != 0;
        ok = (t->kind == AX_TOK_LPAREN && !nl) || t->kind == AX_TOK_DOT ||
             (follow == GA_FOLLOW_CALL_DOT_BRACE && t->kind == AX_TOK_LBRACE && !nl);
    }
    if (!ok) {
        split_rollback(p, split_mark);
        p->pos = pos;
        return NULL;
    }
    if (p->tentative == 0) p->split_len = 0; /* committed outside any tentative parse */
    return args;
}

static AxAstType *parse_bounds(Parser *p) {
    AxAstType *head = parse_type(p);
    AxAstType **curr = &head->next;
    while (consume(p, AX_TOK_PLUS)) {
        *curr = parse_type(p);
        curr = &(*curr)->next;
    }
    return head;
}

static AxAstType *parse_type(Parser *p) {
    AxAstType *type = NEW_NODE(p, AxAstType);
    type->span = peek(p)->span;
    type->next = NULL;

    if (check(p, AX_TOK_IDENT) || check(p, AX_TOK_KW_SELF_TYPE)) {
        type->kind = AX_TYPE_PATH;
        AxAstTypePathSegment *head = NULL, *tail = NULL;
        while (check(p, AX_TOK_IDENT) || check(p, AX_TOK_KW_SELF_TYPE)) {
            AxAstTypePathSegment *seg = NEW_NODE(p, AxAstTypePathSegment);
            seg->span = peek(p)->span;
            seg->name = check(p, AX_TOK_KW_SELF_TYPE) ? ax_intern_cstr(p->interner, "Self") : peek(p)->val.ident_val;
            advance(p);
            
            if (check(p, AX_TOK_LT)) {
                seg->generic_args = p->type_tentative ? try_generic_args(p, GA_FOLLOW_NONE)
                                                      : parse_generic_args(p);
            }
            
            if (tail) tail->next = seg;
            else head = seg;
            tail = seg;
            
            if (consume(p, AX_TOK_DOT)) continue;
            break;
        }
        type->path.segments = head;
    } else if (consume(p, AX_TOK_LPAREN)) {
        if (consume(p, AX_TOK_RPAREN)) {
            type->kind = AX_TYPE_TUPLE;
            type->tuple.elem_types = NULL;
        } else {
            type->kind = AX_TYPE_TUPLE;
            AxAstType **curr = &type->tuple.elem_types;
            while (!check(p, AX_TOK_RPAREN) && !check(p, AX_TOK_EOF)) {
                *curr = parse_type(p);
                curr = &(*curr)->next;
                if (!consume(p, AX_TOK_COMMA)) break;
            }
            expect(p, AX_TOK_RPAREN, AX_PARSE_UNCLOSED_DELIMITER, "Expected ')'");
            if (type->tuple.elem_types != NULL && type->tuple.elem_types->next == NULL && peek_nth(p, -2)->kind != AX_TOK_COMMA) {
                return type->tuple.elem_types;
            }
        }
    } else if (consume(p, AX_TOK_LBRACKET)) {
        AxAstExpr *expr_or_type = parse_expr(p);
        expect(p, AX_TOK_RBRACKET, AX_PARSE_UNCLOSED_DELIMITER, "Expected ']'");
        
        bool next_is_type = check(p, AX_TOK_IDENT) || check(p, AX_TOK_LPAREN) || check(p, AX_TOK_LBRACKET) || 
                            check(p, AX_TOK_STAR) || check(p, AX_TOK_KW_FN) || check(p, AX_TOK_KW_UNSAFE) || 
                            check(p, AX_TOK_KW_EXTERN) || check(p, AX_TOK_KW_VIEW) || check(p, AX_TOK_KW_MUT_VIEW) || check(p, AX_TOK_KW_DYN) || check(p, AX_TOK_KW_SELF_TYPE);
                            
        if (next_is_type) {
            type->kind = AX_TYPE_ARRAY;
            type->array.count = expr_or_type;
            type->array.elem = parse_type(p);
        } else {
            type->kind = AX_TYPE_SLICE;
            AxAstType *elem_type = NEW_NODE(p, AxAstType);
            if (expr_or_type->kind == AX_EXPR_PATH) {
                elem_type->kind = AX_TYPE_PATH;
                elem_type->path.segments = expr_or_type->path.segments;
            } else {
                elem_type->kind = AX_TYPE_ERROR;
            }
            type->slice.elem = elem_type;
        }
    } else if (check(p, AX_TOK_KW_VIEW) || check(p, AX_TOK_KW_MUT_VIEW)) {
        type->kind = AX_TYPE_VIEW;
        type->view.is_mut = check(p, AX_TOK_KW_MUT_VIEW);
        advance(p);
        expect(p, AX_TOK_LT, AX_PARSE_EXPECTED_TOKEN, "Expected '<'");
        type->view.elem = parse_type(p);
        expect(p, AX_TOK_GT, AX_PARSE_EXPECTED_TOKEN, "Expected '>'");
    } else if (consume(p, AX_TOK_STAR)) {
        type->kind = AX_TYPE_PTR;
        if (consume(p, AX_TOK_KW_MUT)) type->ptr.is_mut = true;
        else if (consume(p, AX_TOK_KW_CONST)) type->ptr.is_mut = false;
        else report(p, peek(p)->span, AX_PARSE_EXPECTED_TOKEN, "Expected mut or const");
        type->ptr.elem = parse_type(p);
    } else if (check(p, AX_TOK_KW_FN) || check(p, AX_TOK_KW_UNSAFE) || check(p, AX_TOK_KW_EXTERN)) {
        type->kind = AX_TYPE_FN;
        type->fn.is_unsafe = consume(p, AX_TOK_KW_UNSAFE);
        if (consume(p, AX_TOK_KW_EXTERN)) {
            if (check(p, AX_TOK_STR)) {
                type->fn.abi = ax_intern(p->interner, (StrView){ (const char*)peek(p)->val.str_val.bytes, peek(p)->val.str_val.len });
                advance(p);
            }
        }
        expect(p, AX_TOK_KW_FN, AX_PARSE_EXPECTED_TOKEN, "Expected 'fn'");
        expect(p, AX_TOK_LPAREN, AX_PARSE_EXPECTED_TOKEN, "Expected '('");
        AxAstType **curr = &type->fn.param_types;
        while (!check(p, AX_TOK_RPAREN) && !check(p, AX_TOK_EOF)) {
            *curr = parse_type(p);
            curr = &(*curr)->next;
            if (!consume(p, AX_TOK_COMMA)) break;
        }
        expect(p, AX_TOK_RPAREN, AX_PARSE_UNCLOSED_DELIMITER, "Expected ')'");
        if (consume(p, AX_TOK_ARROW)) {
            type->fn.ret_type = parse_type(p);
        }
    } else if (consume(p, AX_TOK_KW_DYN)) {
        type->kind = AX_TYPE_DYN;
        type->dyn.bounds = parse_bounds(p);
    } else {
        report(p, type->span, AX_PARSE_EXPECTED_TYPE, "Expected type");
        type->kind = AX_TYPE_ERROR;
        advance(p);
    }
    return type;
}

static AxAstPat *parse_pat_no_or(Parser *p) {
    AxAstPat *pat = NEW_NODE(p, AxAstPat);
    pat->span = peek(p)->span;
    pat->next = NULL;

    if (consume(p, AX_TOK_UNDERSCORE)) {
        pat->kind = AX_PAT_WILDCARD;
    } else if (check(p, AX_TOK_INT) || check(p, AX_TOK_CHAR) || check(p, AX_TOK_KW_TRUE) || check(p, AX_TOK_KW_FALSE) || (check(p, AX_TOK_MINUS) && peek_nth(p, 1)->kind == AX_TOK_INT)) {
        bool neg = consume(p, AX_TOK_MINUS);
        AxToken tok = *peek(p);
        advance(p);
        
        if (check(p, AX_TOK_DOT_DOT) || check(p, AX_TOK_DOT_DOT_EQ)) {
            pat->kind = AX_PAT_RANGE;
            pat->range.is_inclusive = consume(p, AX_TOK_DOT_DOT_EQ);
            if (pat->range.is_inclusive == false) consume(p, AX_TOK_DOT_DOT); // already checked
            
            AxAstPat *start = NEW_NODE(p, AxAstPat);
            start->span = tok.span;
            start->kind = AX_PAT_LITERAL;
            start->literal.tok = tok;
            start->literal.is_negated = neg;
            
            bool end_neg = consume(p, AX_TOK_MINUS);
            AxToken end_tok = *peek(p);
            expect(p, end_tok.kind == AX_TOK_INT || end_tok.kind == AX_TOK_CHAR ? end_tok.kind : AX_TOK_INT, AX_PARSE_EXPECTED_TOKEN, "Expected range bound");
            
            AxAstPat *end = NEW_NODE(p, AxAstPat);
            end->span = end_tok.span;
            end->kind = AX_PAT_LITERAL;
            end->literal.tok = end_tok;
            end->literal.is_negated = end_neg;
            
            pat->range.start = start;
            pat->range.end = end;
        } else {
            pat->kind = AX_PAT_LITERAL;
            pat->literal.tok = tok;
            pat->literal.is_negated = neg;
        }
    } else if (check(p, AX_TOK_IDENT) || check(p, AX_TOK_KW_SELF_TYPE) || check(p, AX_TOK_KW_MUT)) {
        if (check(p, AX_TOK_IDENT) && !check(p, AX_TOK_KW_SELF_TYPE) && peek_nth(p, 1)->kind != AX_TOK_DOT && peek_nth(p, 1)->kind != AX_TOK_LPAREN && peek_nth(p, 1)->kind != AX_TOK_LBRACE && !check(p, AX_TOK_KW_MUT)) {
            // Identifier pattern
            pat->kind = AX_PAT_BINDING;
            pat->binding.is_mut = false;
            pat->binding.name = peek(p)->val.ident_val;
            advance(p);
        } else if (consume(p, AX_TOK_KW_MUT)) {
            pat->kind = AX_PAT_BINDING;
            pat->binding.is_mut = true;
            pat->binding.name = peek(p)->val.ident_val;
            expect(p, AX_TOK_IDENT, AX_PARSE_EXPECTED_TOKEN, "Expected identifier after mut");
        } else {
            // PathPat
            AxAstTypePathSegment *head = NULL, *tail = NULL;
            while (check(p, AX_TOK_IDENT) || check(p, AX_TOK_KW_SELF_TYPE)) {
                AxAstTypePathSegment *seg = NEW_NODE(p, AxAstTypePathSegment);
                seg->span = peek(p)->span;
                seg->name = check(p, AX_TOK_KW_SELF_TYPE) ? ax_intern_cstr(p->interner, "Self") : peek(p)->val.ident_val;
                advance(p);
                if (tail) tail->next = seg;
                else head = seg;
                tail = seg;
                if (consume(p, AX_TOK_DOT)) continue;
                break;
            }
            if (consume(p, AX_TOK_LPAREN)) {
                pat->kind = AX_PAT_PATH;
                pat->path.segments = head;
                
                AxAstPat *tuple = NEW_NODE(p, AxAstPat);
                tuple->span = pat->span;
                tuple->kind = AX_PAT_TUPLE;
                
                AxAstPat **curr = &tuple->tuple.elems;
                while (!check(p, AX_TOK_RPAREN) && !check(p, AX_TOK_EOF)) {
                    *curr = parse_pattern(p);
                    curr = &(*curr)->next;
                    if (!consume(p, AX_TOK_COMMA)) break;
                }
                expect(p, AX_TOK_RPAREN, AX_PARSE_UNCLOSED_DELIMITER, "Expected ')'");
                pat->path.payload = tuple;
            } else if (consume(p, AX_TOK_LBRACE)) {
                pat->kind = AX_PAT_STRUCT;
                pat->struct_pat.segments = head;
                pat->struct_pat.has_rest = false;
                
                AxAstPatField **curr = &pat->struct_pat.fields;
                while (!check(p, AX_TOK_RBRACE) && !check(p, AX_TOK_EOF)) {
                    if (consume(p, AX_TOK_DOT_DOT)) {
                        pat->struct_pat.has_rest = true;
                        break;
                    }
                    AxAstPatField *field = NEW_NODE(p, AxAstPatField);
                    field->span = peek(p)->span;
                    
                    if (consume(p, AX_TOK_KW_MUT)) {
                        field->name = peek(p)->val.ident_val;
                        expect(p, AX_TOK_IDENT, AX_PARSE_EXPECTED_TOKEN, "Expected identifier after mut");
                        AxAstPat *p_pat = NEW_NODE(p, AxAstPat);
                        p_pat->span = field->span;
                        p_pat->kind = AX_PAT_BINDING;
                        p_pat->binding.is_mut = true;
                        p_pat->binding.name = field->name;
                        field->pat = p_pat;
                    } else {
                        field->name = peek(p)->val.ident_val;
                        expect(p, AX_TOK_IDENT, AX_PARSE_EXPECTED_TOKEN, "Expected field name");
                        if (consume(p, AX_TOK_COLON)) {
                            field->pat = parse_pattern(p);
                        } else {
                            field->pat = NULL; // shorthand
                        }
                    }
                    *curr = field;
                    curr = &field->next;
                    if (!consume(p, AX_TOK_COMMA)) break;
                }
                expect(p, AX_TOK_RBRACE, AX_PARSE_UNCLOSED_DELIMITER, "Expected '}'");
            } else {
                pat->kind = AX_PAT_PATH;
                pat->path.segments = head;
                pat->path.payload = NULL;
            }
        }
    } else if (consume(p, AX_TOK_LPAREN)) {
        if (consume(p, AX_TOK_RPAREN)) {
            pat->kind = AX_PAT_TUPLE;
            pat->tuple.elems = NULL;
        } else {
            pat->kind = AX_PAT_TUPLE;
            AxAstPat **curr = &pat->tuple.elems;
            while (!check(p, AX_TOK_RPAREN) && !check(p, AX_TOK_EOF)) {
                *curr = parse_pattern(p);
                curr = &(*curr)->next;
                if (!consume(p, AX_TOK_COMMA)) break;
            }
            expect(p, AX_TOK_RPAREN, AX_PARSE_UNCLOSED_DELIMITER, "Expected ')'");
            if (pat->tuple.elems != NULL && pat->tuple.elems->next == NULL && peek_nth(p, -2)->kind != AX_TOK_COMMA) {
                return pat->tuple.elems; // (pat)
            }
        }
    } else {
        report(p, pat->span, AX_PARSE_EXPECTED_PATTERN, "Expected pattern");
        pat->kind = AX_PAT_ERROR;
        advance(p);
    }
    return pat;
}

static AxAstPat *parse_pattern(Parser *p) {
    AxAstPat *pat = parse_pat_no_or(p);
    if (check(p, AX_TOK_PIPE)) {
        AxAstPat *or_pat = NEW_NODE(p, AxAstPat);
        or_pat->span = pat->span;
        or_pat->kind = AX_PAT_OR;
        or_pat->or_pat.pats = pat;
        AxAstPat **curr = &pat->next;
        while (consume(p, AX_TOK_PIPE)) {
            *curr = parse_pat_no_or(p);
            curr = &(*curr)->next;
        }
        return or_pat;
    }
    return pat;
}

static AxAstExpr *parse_primary(Parser *p) {
    const AxToken *tok = peek(p);
    AxAstExpr *expr = NEW_NODE(p, AxAstExpr);
    expr->span = tok->span;
    expr->next = NULL;

    if (tok->kind == AX_TOK_MINUS || tok->kind == AX_TOK_BANG || tok->kind == AX_TOK_TILDE || tok->kind == AX_TOK_STAR) {
        expr->kind = AX_EXPR_UNARY;
        expr->unary.op = (tok->kind == AX_TOK_MINUS) ? AX_UNOP_NEG : (tok->kind == AX_TOK_BANG ? AX_UNOP_NOT : (tok->kind == AX_TOK_TILDE ? AX_UNOP_BITNOT : AX_UNOP_DEREF));
        advance(p);
        expr->unary.expr = parse_expr_prec(p, 2);
        return expr;
    } else if (tok->kind == AX_TOK_INT || tok->kind == AX_TOK_FLOAT || tok->kind == AX_TOK_STR ||
        tok->kind == AX_TOK_BYTE_STR || tok->kind == AX_TOK_CHAR || tok->kind == AX_TOK_KW_TRUE ||
        tok->kind == AX_TOK_KW_FALSE) {
        expr->kind = AX_EXPR_LITERAL;
        expr->literal = *tok;
        advance(p);
        return expr;
    } else if (tok->kind == AX_TOK_DOT_DOT || tok->kind == AX_TOK_DOT_DOT_EQ) {
        expr->kind = AX_EXPR_RANGE;
        expr->range.start = NULL;
        expr->range.is_inclusive = (tok->kind == AX_TOK_DOT_DOT_EQ);
        advance(p);
        const AxToken *next = peek(p);
        if (next->kind == AX_TOK_RBRACKET || next->kind == AX_TOK_RBRACE || next->kind == AX_TOK_RPAREN || next->kind == AX_TOK_COMMA || next->kind == AX_TOK_SEMI || next->kind == AX_TOK_EOF) {
            expr->range.end = NULL;
        } else {
            expr->range.end = parse_expr_prec(p, 12);
        }
        return expr;
    } else if (tok->kind == AX_TOK_IDENT || tok->kind == AX_TOK_KW_SELF_TYPE) {
        // PathExpr or StructLit
        size_t initial_pos = p->pos;
        bool is_struct = false;
        if (!p->no_struct) {
            /* AXS-GRM-058 lookahead: a chain of names (with optional generic args) followed by
               `{`. Done as a silent tentative scan; position and tokens are restored after. */
            size_t split_mark = p->split_len;
            bool outer_failed = p->tentative_failed;
            p->tentative++;
            while (check(p, AX_TOK_IDENT) || check(p, AX_TOK_KW_SELF_TYPE)) {
                advance(p);
                try_generic_args(p, GA_FOLLOW_CALL_DOT_BRACE);
                if (consume(p, AX_TOK_DOT)) continue;
                break;
            }
            is_struct = check(p, AX_TOK_LBRACE) && !(p->mode_on && (peek(p)->flags & AX_TOK_FLAG_NL_BEFORE));
            p->tentative--;
            p->tentative_failed = outer_failed;
            split_rollback(p, split_mark);
            p->pos = initial_pos;
        }

        if (is_struct) {
            AxAstTypePathSegment *head = NULL, *tail = NULL;
            while (check(p, AX_TOK_IDENT) || check(p, AX_TOK_KW_SELF_TYPE)) {
                AxAstTypePathSegment *seg = NEW_NODE(p, AxAstTypePathSegment);
                seg->span = peek(p)->span;
                seg->name = check(p, AX_TOK_KW_SELF_TYPE) ? ax_intern_cstr(p->interner, "Self") : peek(p)->val.ident_val;
                advance(p);
                seg->generic_args = try_generic_args(p, GA_FOLLOW_CALL_DOT_BRACE);
                if (tail) tail->next = seg;
                else head = seg;
                tail = seg;
                if (consume(p, AX_TOK_DOT)) continue;
                break;
            }
            expr->kind = AX_EXPR_STRUCT;
            expr->struct_lit.segments = head;
            advance(p); // {
            AxAstFieldInit **curr = &expr->struct_lit.fields;
            while (!check(p, AX_TOK_RBRACE) && !check(p, AX_TOK_EOF)) {
                AxAstFieldInit *fi = NEW_NODE(p, AxAstFieldInit);
                fi->span = peek(p)->span;
                fi->name = peek(p)->val.ident_val;
                expect(p, AX_TOK_IDENT, AX_PARSE_EXPECTED_TOKEN, "Expected field name");
                if (consume(p, AX_TOK_COLON)) {
                    fi->expr = parse_expr(p);
                } else {
                    fi->expr = NULL;
                }
                *curr = fi;
                curr = &fi->next;
                if (!consume(p, AX_TOK_COMMA)) break;
            }
            expect(p, AX_TOK_RBRACE, AX_PARSE_UNCLOSED_DELIMITER, "Expected '}'");
            return expr;
        } else {
            // Not a struct lit: parse only ONE segment, so that dotted chains like a.b.c are
            // parsed by parse_expr_prec as ExprPostfix.
            AxAstTypePathSegment *seg = NEW_NODE(p, AxAstTypePathSegment);
            seg->span = peek(p)->span;
            seg->name = check(p, AX_TOK_KW_SELF_TYPE) ? ax_intern_cstr(p->interner, "Self") : peek(p)->val.ident_val;
            advance(p);
            /* `{` cannot follow here: with struct literals allowed it was taken above, and in a
               header it is not a follower (AXS-GRM-059). */
            seg->generic_args = try_generic_args(p, GA_FOLLOW_CALL_DOT);
            seg->next = NULL;
            expr->kind = AX_EXPR_PATH;
            expr->path.segments = seg;
            return expr;
        }
    } else if (consume(p, AX_TOK_LPAREN)) {
        bool old = p->mode_on;
        bool old_no_struct = p->no_struct;
        p->mode_on = false;
        p->no_struct = false;
        if (consume(p, AX_TOK_RPAREN)) {
            expr->kind = AX_EXPR_TUPLE;
            expr->tuple.elems = NULL;
        } else {
            AxAstExpr *inner = parse_expr(p);
            if (consume(p, AX_TOK_COMMA)) {
                expr->kind = AX_EXPR_TUPLE;
                AxAstExpr **curr = &inner->next;
                while (!check(p, AX_TOK_RPAREN) && !check(p, AX_TOK_EOF)) {
                    *curr = parse_expr(p);
                    curr = &(*curr)->next;
                    if (!consume(p, AX_TOK_COMMA)) break;
                }
                expr->tuple.elems = inner;
            } else {
                expr->kind = AX_EXPR_PAREN;
                expr->paren.expr = inner;
            }
            expect(p, AX_TOK_RPAREN, AX_PARSE_UNCLOSED_DELIMITER, "Expected ')'");
        }
        p->mode_on = old;
        p->no_struct = old_no_struct;
        return expr;
    } else if (consume(p, AX_TOK_LBRACKET)) {
        bool old = p->mode_on;
        bool old_no_struct = p->no_struct;
        p->mode_on = false;
        p->no_struct = false;
        expr->kind = AX_EXPR_ARRAY;
        if (consume(p, AX_TOK_RBRACKET)) {
            expr->array.elems = NULL;
            expr->array.count = NULL;
        } else {
            AxAstExpr *first = parse_expr(p);
            if (consume(p, AX_TOK_SEMI)) {
                expr->array.elems = first;
                expr->array.count = parse_expr(p);
            } else {
                expr->array.elems = first;
                expr->array.count = NULL;
                AxAstExpr **curr = &first->next;
                if (consume(p, AX_TOK_COMMA)) {
                    while (!check(p, AX_TOK_RBRACKET) && !check(p, AX_TOK_EOF)) {
                        *curr = parse_expr(p);
                        curr = &(*curr)->next;
                        if (!consume(p, AX_TOK_COMMA)) break;
                    }
                }
            }
            expect(p, AX_TOK_RBRACKET, AX_PARSE_UNCLOSED_DELIMITER, "Expected ']'");
        }
        p->mode_on = old;
        p->no_struct = old_no_struct;
        return expr;
    } else if (check(p, AX_TOK_LBRACE)) {
        expr->kind = AX_EXPR_BLOCK;
        expr->block.block = *parse_block(p);
        return expr;
    } else if (consume(p, AX_TOK_KW_IF)) {
        expr->kind = AX_EXPR_IF;
        if (consume(p, AX_TOK_KW_LET)) {
            expr->if_expr.let_pat = parse_pattern(p);
            expect(p, AX_TOK_EQ, AX_PARSE_EXPECTED_TOKEN, "Expected '='");
        }
        expr->if_expr.cond = parse_header_expr(p); // parse cond
        expr->if_expr.block = *parse_block(p);
        if (consume(p, AX_TOK_KW_ELSE)) {
            if (check(p, AX_TOK_KW_IF)) {
                expr->if_expr.else_branch = parse_expr(p); // parse if
            } else {
                AxAstExpr *else_block = NEW_NODE(p, AxAstExpr);
                else_block->span = peek(p)->span;
                else_block->kind = AX_EXPR_BLOCK;
                else_block->block.block = *parse_block(p);
                expr->if_expr.else_branch = else_block;
            }
        }
        return expr;
    } else if (consume(p, AX_TOK_KW_MATCH)) {
        expr->kind = AX_EXPR_MATCH;
        expr->match.expr = parse_header_expr(p);
        expect(p, AX_TOK_LBRACE, AX_PARSE_EXPECTED_TOKEN, "Expected '{'");
        AxAstMatchArm **curr = &expr->match.arms;
        while (!check(p, AX_TOK_RBRACE) && !check(p, AX_TOK_EOF)) {
            AxAstMatchArm *arm = NEW_NODE(p, AxAstMatchArm);
            arm->span = peek(p)->span;
            arm->pat = parse_pattern(p);
            if (consume(p, AX_TOK_KW_IF)) {
                arm->guard = parse_expr(p);
            }
            expect(p, AX_TOK_FAT_ARROW, AX_PARSE_EXPECTED_TOKEN, "Expected '=>'");
            arm->body = parse_expr(p);
            *curr = arm;
            curr = &arm->next;
            consume(p, AX_TOK_COMMA); // optional comma
        }
        expect(p, AX_TOK_RBRACE, AX_PARSE_UNCLOSED_DELIMITER, "Expected '}'");
        return expr;
    } else if (check(p, AX_TOK_KW_LOOP) || (check(p, AX_TOK_LABEL) && peek_nth(p, 1)->kind == AX_TOK_COLON && peek_nth(p, 2)->kind == AX_TOK_KW_LOOP)) {
        expr->kind = AX_EXPR_LOOP;
        if (check(p, AX_TOK_LABEL)) {
            expr->loop.label = peek(p)->val.ident_val;
            advance(p);
            advance(p); // :
        }
        advance(p); // loop
        expr->loop.block = *parse_block(p);
        return expr;
    } else if (check(p, AX_TOK_KW_WHILE) || (check(p, AX_TOK_LABEL) && peek_nth(p, 1)->kind == AX_TOK_COLON && peek_nth(p, 2)->kind == AX_TOK_KW_WHILE)) {
        expr->kind = AX_EXPR_WHILE;
        if (check(p, AX_TOK_LABEL)) {
            expr->while_expr.label = peek(p)->val.ident_val;
            advance(p);
            advance(p); // :
        }
        advance(p); // while
        if (consume(p, AX_TOK_KW_LET)) {
            expr->while_expr.let_pat = parse_pattern(p);
            expect(p, AX_TOK_EQ, AX_PARSE_EXPECTED_TOKEN, "Expected '='");
        }
        expr->while_expr.cond = parse_header_expr(p);
        expr->while_expr.block = *parse_block(p);
        return expr;
    } else if (check(p, AX_TOK_KW_FOR) || (check(p, AX_TOK_LABEL) && peek_nth(p, 1)->kind == AX_TOK_COLON && peek_nth(p, 2)->kind == AX_TOK_KW_FOR)) {
        expr->kind = AX_EXPR_FOR;
        if (check(p, AX_TOK_LABEL)) {
            expr->for_expr.label = peek(p)->val.ident_val;
            advance(p);
            advance(p); // :
        }
        advance(p); // for
        expr->for_expr.pat = parse_pattern(p);
        expect(p, AX_TOK_KW_IN, AX_PARSE_EXPECTED_TOKEN, "Expected 'in'");
        expr->for_expr.iter = parse_header_expr(p);
        expr->for_expr.block = *parse_block(p);
        return expr;
    } else if (consume(p, AX_TOK_KW_UNSAFE)) {
        expr->kind = AX_EXPR_UNSAFE;
        expr->unsafe_block.block = *parse_block(p);
        return expr;
    } else if (check(p, AX_TOK_KW_VIEW) || check(p, AX_TOK_KW_MUT_VIEW)) {
        expr->kind = AX_EXPR_VIEW;
        expr->view.is_mut = check(p, AX_TOK_KW_MUT_VIEW);
        advance(p);
        expect(p, AX_TOK_LPAREN, AX_PARSE_EXPECTED_TOKEN, "Expected '('");
        expr->view.expr = parse_expr(p);
        expect(p, AX_TOK_RPAREN, AX_PARSE_UNCLOSED_DELIMITER, "Expected ')'");
        return expr;
    } else if (consume(p, AX_TOK_KW_COMPTIME)) {
        expr->kind = AX_EXPR_COMPTIME;
        expr->comptime.block = *parse_block(p);
        return expr;
    } else if (consume(p, AX_TOK_KW_RETURN) || consume(p, AX_TOK_KW_BREAK) || consume(p, AX_TOK_KW_CONTINUE)) {
        expr->kind = AX_EXPR_JUMP;
        AxTokenKind k = peek_nth(p, -1)->kind;
        expr->jump.jump_kind = (k == AX_TOK_KW_RETURN) ? AX_JUMP_RETURN : (k == AX_TOK_KW_BREAK ? AX_JUMP_BREAK : AX_JUMP_CONTINUE);
        if (k != AX_TOK_KW_RETURN && check(p, AX_TOK_LABEL) && !(peek(p)->flags & AX_TOK_FLAG_NL_BEFORE)) {
            expr->jump.label = peek(p)->val.ident_val;
            advance(p);
        }
        if (k != AX_TOK_KW_CONTINUE) {
            // parse operand if it exists and no NL_BEFORE (in mode ON)
            if (p->mode_on && (peek(p)->flags & AX_TOK_FLAG_NL_BEFORE)) {
                expr->jump.expr = NULL;
            } else {
                // check if it can start expr
                AxTokenKind nk = peek(p)->kind;
                if (nk != AX_TOK_SEMI && nk != AX_TOK_RBRACE && nk != AX_TOK_EOF) {
                    expr->jump.expr = parse_expr(p);
                } else {
                    expr->jump.expr = NULL;
                }
            }
        }
        return expr;
    } else if (consume(p, AX_TOK_PIPE_PIPE) || consume(p, AX_TOK_PIPE)) {
        expr->kind = AX_EXPR_CLOSURE;
        AxTokenKind k = peek_nth(p, -1)->kind;
        if (k == AX_TOK_PIPE) {
            AxAstParam **curr = &expr->closure.params;
            while (!check(p, AX_TOK_PIPE) && !check(p, AX_TOK_EOF)) {
                AxAstParam *param = NEW_NODE(p, AxAstParam);
                param->span = peek(p)->span;
                if (consume(p, AX_TOK_KW_MUT)) param->is_mut = true;
                if (consume(p, AX_TOK_UNDERSCORE)) {
                    param->name.v = 0;
                } else {
                    param->name = peek(p)->val.ident_val;
                    expect(p, AX_TOK_IDENT, AX_PARSE_EXPECTED_TOKEN, "Expected param name");
                }
                if (consume(p, AX_TOK_COLON)) {
                    param->type = parse_type(p);
                }
                *curr = param;
                curr = &param->next;
                if (!consume(p, AX_TOK_COMMA)) break;
            }
            expect(p, AX_TOK_PIPE, AX_PARSE_EXPECTED_TOKEN, "Expected '|'");
        } else {
            expr->closure.params = NULL;
        }
        
        if (consume(p, AX_TOK_ARROW)) {
            expr->closure.ret_type = parse_type(p);
            expr->closure.body = NEW_NODE(p, AxAstExpr);
            expr->closure.body->span = peek(p)->span;
            expr->closure.body->kind = AX_EXPR_BLOCK;
            expr->closure.body->block.block = *parse_block(p);
        } else {
            expr->closure.body = parse_expr_prec(p, 14);
        }
        return expr;
    }

    report(p, tok->span, AX_PARSE_EXPECTED_EXPR, "Expected expression");
    expr->kind = AX_EXPR_ERROR;
    advance(p);
    return expr;
}

static AxAstExpr *parse_expr_prec(Parser *p, int min_prec) {
    AxAstExpr *left = parse_primary(p);
    bool left_is_cmp = false; /* `left` is a level-10 comparison built by this loop */

    while (true) {
        const AxToken *tok = peek(p);
        int prec = get_infix_prec(tok->kind);
        if (prec == 0 || prec > min_prec) break;
        bool was_cmp = left_is_cmp;
        left_is_cmp = false;

        if (p->mode_on && (tok->flags & AX_TOK_FLAG_NL_BEFORE)) {
            if (tok->kind != AX_TOK_DOT) {
                break;
            }
        }

        if (tok->kind == AX_TOK_DOT) {
            advance(p);
            if (check(p, AX_TOK_IDENT)) {
                AxAstExpr *postfix = NEW_NODE(p, AxAstExpr);
                postfix->span = left->span;
                postfix->kind = AX_EXPR_POSTFIX;
                postfix->postfix.head = left;
                AxAstPostfixSeg *seg = NEW_NODE(p, AxAstPostfixSeg); seg->span = postfix->span; if (ax_sv_eq(ax_interner_get(p->interner, peek(p)->val.ident_val), ax_sv_cstr("await"))) {
                    seg->kind = AX_POSTFIX_AWAIT;
                    advance(p);
                } else {
                    seg->kind = AX_POSTFIX_FIELD;
                    seg->field.name = peek(p)->val.ident_val;
                    advance(p);
                    if (check(p, AX_TOK_LT)) {
                        size_t old_pos = p->pos;
                        AxAstGenericArgs *args = parse_generic_args(p);
                        if (check(p, AX_TOK_LPAREN)) {
                            seg->field.generic_args = args;
                        } else {
                            p->pos = old_pos; // backtrack
                        }
                    }
                }
                seg->next = NULL;
                postfix->postfix.segments = seg;
                left = postfix;
                continue;
            } else if (check(p, AX_TOK_INT)) {
                AxAstExpr *postfix = NEW_NODE(p, AxAstExpr);
                postfix->span = left->span;
                postfix->kind = AX_EXPR_POSTFIX;
                postfix->postfix.head = left;
                AxAstPostfixSeg *seg = NEW_NODE(p, AxAstPostfixSeg); seg->span = postfix->span; seg->kind = AX_POSTFIX_TUPLE_INDEX;
                // Parse int value... Wait, val is union.
                seg->tuple_index = (uint32_t)peek(p)->val.int_val.value; // assuming int_val exists
                advance(p);
                postfix->postfix.segments = seg;
                left = postfix;
                continue;
            } else {
                report(p, peek(p)->span, AX_PARSE_EXPECTED_TOKEN, "Expected field or method name");
                break;
            }
        }
        
        if (tok->kind == AX_TOK_LPAREN) {
            advance(p);
            AxAstExpr *postfix = NEW_NODE(p, AxAstExpr);
            postfix->span = left->span;
            postfix->kind = AX_EXPR_POSTFIX;
            postfix->postfix.head = left;
            AxAstPostfixSeg *seg = NEW_NODE(p, AxAstPostfixSeg); seg->span = postfix->span; seg->kind = AX_POSTFIX_CALL;
            
            bool old = p->mode_on;
            p->mode_on = false;
            AxAstExpr **curr = &seg->call.args;
            while (!check(p, AX_TOK_RPAREN) && !check(p, AX_TOK_EOF)) {
                *curr = parse_expr(p);
                curr = &(*curr)->next;
                if (!consume(p, AX_TOK_COMMA)) break;
            }
            p->mode_on = old;
            expect(p, AX_TOK_RPAREN, AX_PARSE_UNCLOSED_DELIMITER, "Expected ')'");
            
            postfix->postfix.segments = seg;
            left = postfix;
            continue;
        }

        if (tok->kind == AX_TOK_LBRACKET) {
            advance(p);
            AxAstExpr *postfix = NEW_NODE(p, AxAstExpr);
            postfix->span = left->span;
            postfix->kind = AX_EXPR_POSTFIX;
            postfix->postfix.head = left;
            AxAstPostfixSeg *seg = NEW_NODE(p, AxAstPostfixSeg); seg->span = postfix->span; seg->kind = AX_POSTFIX_INDEX;
            
            bool old = p->mode_on;
            p->mode_on = false;
            
            seg->index.arg = parse_expr(p);
            p->mode_on = old;
            expect(p, AX_TOK_RBRACKET, AX_PARSE_UNCLOSED_DELIMITER, "Expected ']'");
            
            postfix->postfix.segments = seg;
            left = postfix;
            continue;
        }
        
        if (tok->kind == AX_TOK_QUESTION) {
            advance(p);
            AxAstExpr *postfix = NEW_NODE(p, AxAstExpr);
            postfix->span = left->span;
            postfix->kind = AX_EXPR_POSTFIX;
            postfix->postfix.head = left;
            AxAstPostfixSeg *seg = NEW_NODE(p, AxAstPostfixSeg); seg->span = postfix->span; seg->kind = AX_POSTFIX_TRY;
            postfix->postfix.segments = seg;
            left = postfix;
            continue;
        }

        if (tok->kind == AX_TOK_ARROW) {
            advance(p);
            AxAstExpr *postfix = NEW_NODE(p, AxAstExpr);
            postfix->span = left->span;
            postfix->kind = AX_EXPR_POSTFIX;
            postfix->postfix.head = left;
            AxAstPostfixSeg *seg = NEW_NODE(p, AxAstPostfixSeg); seg->span = postfix->span; seg->kind = AX_POSTFIX_ARROW;
            seg->arrow_name = peek(p)->val.ident_val;
            expect(p, AX_TOK_IDENT, AX_PARSE_EXPECTED_TOKEN, "Expected identifier after ->");
            postfix->postfix.segments = seg;
            left = postfix;
            continue;
        }

        if (tok->kind == AX_TOK_KW_AS) {
            advance(p);
            AxAstExpr *cast = NEW_NODE(p, AxAstExpr);
            cast->span = left->span;
            cast->kind = AX_EXPR_CAST;
            cast->cast.expr = left;
            
            bool old_tt = p->type_tentative;
            p->type_tentative = true;
            cast->cast.type = parse_type(p);
            p->type_tentative = old_tt;
            
            left = cast;
            continue;
        }

        advance(p); // Consume operator

        AxAstExpr *bin = NEW_NODE(p, AxAstExpr);
        bin->span = left->span;
        
        if (tok->kind == AX_TOK_DOT_DOT || tok->kind == AX_TOK_DOT_DOT_EQ) {
            bin->kind = AX_EXPR_RANGE;
            bin->range.start = left;
            bin->range.is_inclusive = (tok->kind == AX_TOK_DOT_DOT_EQ);
            const AxToken *next = peek(p);
            if (next->kind == AX_TOK_RBRACKET || next->kind == AX_TOK_RBRACE || next->kind == AX_TOK_RPAREN || next->kind == AX_TOK_COMMA || next->kind == AX_TOK_SEMI || next->kind == AX_TOK_EOF) {
                bin->range.end = NULL;
            } else {
                bin->range.end = parse_expr_prec(p, 12);
            }
        } else {
            bin->kind = AX_EXPR_BINARY;
            bin->binary.left = left;
            bin->binary.op = token_to_binop(tok->kind);
            if (prec == 10) {
                /* AXS-GRM-051: comparisons are non-associative. `left` is already a comparison
                   only when it was built by this loop at level 10 (a parenthesised comparison
                   is an ExprParen). Recover by parsing on, left-associatively. */
                if (was_cmp) {
                    report(p, tok->span, AX_PARSE_CHAINED_COMPARISON,
                           "comparison operators cannot be chained; use parentheses or `&&`");
                }
            }
            /* AXS-GRM-050: every binary level is left-associative (or non-associative): the
               right operand only takes operators that bind strictly tighter. */
            bin->binary.right = parse_expr_prec(p, prec - 1);
        }
        
        left_is_cmp = (bin->kind == AX_EXPR_BINARY && prec == 10);
        left = bin;
    }

    return left;
}

static AxAstExpr *parse_expr(Parser *p) {
    return parse_expr_prec(p, 14);
}

/* Cond of if/while, scrutinee of match, iterable of for: a full expression in which a `{` after
   a path starts the construct's block (AXS-GRM-059). */
static AxAstExpr *parse_header_expr(Parser *p) {
    bool old_no_struct = p->no_struct;
    p->no_struct = true;
    AxAstExpr *e = parse_expr(p);
    p->no_struct = old_no_struct;
    return e;
}

static AxAstBlock *parse_block(Parser *p) {
    AxAstBlock *block = NEW_NODE(p, AxAstBlock);
    block->span = peek(p)->span;
    block->stmts = NULL;

    expect(p, AX_TOK_LBRACE, AX_PARSE_EXPECTED_TOKEN, "Expected '{'");
    
    AxAstStmt **curr = &block->stmts;
    while (!check(p, AX_TOK_RBRACE) && !check(p, AX_TOK_EOF)) {
        *curr = parse_stmt(p);
        curr = &(*curr)->next;
    }

    expect(p, AX_TOK_RBRACE, AX_PARSE_UNCLOSED_DELIMITER, "Expected '}'");
    return block;
}

static AxAstParam *parse_params(Parser *p) {
    AxAstParam *head = NULL;
    AxAstParam **curr = &head;
    while (!check(p, AX_TOK_RPAREN) && !check(p, AX_TOK_EOF)) {
        AxAstParam *param = NEW_NODE(p, AxAstParam);
        param->span = peek(p)->span;
        if (consume(p, AX_TOK_KW_MUT)) {
            param->is_mut = true;
        } else {
            param->is_mut = false;
        }
        
        if (check(p, AX_TOK_KW_SELF_VALUE)) {
            param->name = ax_intern_cstr(p->interner, "self");
            advance(p);
        } else if (consume(p, AX_TOK_UNDERSCORE)) {
            param->name.v = 0;
        } else {
            param->name = peek(p)->val.ident_val;
            expect(p, AX_TOK_IDENT, AX_PARSE_EXPECTED_TOKEN, "Expected param name");
        }
        expect(p, AX_TOK_COLON, AX_PARSE_EXPECTED_TOKEN, "Expected ':'");
        param->type = parse_type(p);
        *curr = param;
        curr = &param->next;
        if (!consume(p, AX_TOK_COMMA)) break;
    }
    return head;
}

static AxAstStmt *parse_stmt(Parser *p) {
    AxAstStmt *stmt = NEW_NODE(p, AxAstStmt);
    stmt->span = peek(p)->span;
    stmt->next = NULL;

    if (consume(p, AX_TOK_SEMI)) {
        stmt->kind = AX_STMT_EXPR; // empty stmt, represented as dummy expression maybe?
        stmt->expr_stmt.expr = NEW_NODE(p, AxAstExpr);
        stmt->expr_stmt.expr->kind = AX_EXPR_ERROR; // or something safe
        stmt->expr_stmt.has_semi = true;
        return stmt;
    }

    if (check(p, AX_TOK_IDENT) && ax_sv_eq(ax_interner_get(p->interner, peek(p)->val.ident_val), ax_sv_cstr("import"))) {
        report(p, peek(p)->span, AX_PARSE_IMPORT, "import is not a keyword");
        advance(p);
        stmt->kind = AX_STMT_ERROR;
        sync_to_term(p);
    } else if (check(p, AX_TOK_IDENT) && ax_sv_eq(ax_interner_get(p->interner, peek(p)->val.ident_val), ax_sv_cstr("var"))) {
        report(p, peek(p)->span, AX_PARSE_VAR, "replace var by let mut");
        advance(p);
        stmt->kind = AX_STMT_LET;
        stmt->let.pat = parse_pattern(p);
        if (consume(p, AX_TOK_COLON)) stmt->let.type = parse_type(p);
        else stmt->let.type = NULL;
        if (consume(p, AX_TOK_EQ)) stmt->let.expr = parse_expr(p);
        else stmt->let.expr = NULL;
        stmt->let.else_block = NULL;
    } else if (consume(p, AX_TOK_KW_LET)) {
        stmt->kind = AX_STMT_LET;
        stmt->let.pat = parse_pattern(p);
        if (consume(p, AX_TOK_COLON)) {
            stmt->let.type = parse_type(p);
        } else {
            stmt->let.type = NULL;
        }
        if (consume(p, AX_TOK_EQ)) {
            stmt->let.expr = parse_expr(p);
            if (consume(p, AX_TOK_KW_ELSE)) {
                AxAstBlock *else_blk = parse_block(p);
                stmt->let.else_block = else_blk;
            } else {
                stmt->let.else_block = NULL;
            }
        } else {
            stmt->let.expr = NULL;
            stmt->let.else_block = NULL;
        }
    } else if (check(p, AX_TOK_KW_FN) || check(p, AX_TOK_KW_STRUCT) || check(p, AX_TOK_KW_ENUM) || check(p, AX_TOK_KW_TRAIT) || check(p, AX_TOK_KW_IMPL) || check(p, AX_TOK_KW_TYPE) || check(p, AX_TOK_KW_CONST) || check(p, AX_TOK_KW_STATIC) || check(p, AX_TOK_KW_USE) || check(p, AX_TOK_KW_MODULE) || check(p, AX_TOK_KW_EXTERN) || check(p, AX_TOK_KW_PUB) || (check(p, AX_TOK_KW_UNSAFE) && (peek_nth(p, 1)->kind == AX_TOK_KW_FN || peek_nth(p, 1)->kind == AX_TOK_KW_EXTERN || peek_nth(p, 1)->kind == AX_TOK_KW_TRAIT)) || check(p, AX_TOK_KW_ASYNC)) {
        // Items in block
        report(p, peek(p)->span, AX_PARSE_ITEM_IN_BLOCK, "Items in block are not allowed");
        parse_item(p); // parse and discard
        stmt->kind = AX_STMT_ERROR;
        return stmt;
    } else {
        // leading operator rule
        AxTokenKind k = peek(p)->kind;
        if (k == AX_TOK_PLUS || k == AX_TOK_SLASH || k == AX_TOK_PERCENT || k == AX_TOK_CARET || k == AX_TOK_AMP || k == AX_TOK_AMP_AMP || k == AX_TOK_SHL || k == AX_TOK_SHR || k == AX_TOK_EQ_EQ || k == AX_TOK_BANG_EQ || k == AX_TOK_LT || k == AX_TOK_LT_EQ || k == AX_TOK_GT || k == AX_TOK_GT_EQ || (k >= AX_TOK_EQ && k <= AX_TOK_SHR_EQ) || k == AX_TOK_DOT_DOT || k == AX_TOK_DOT_DOT_EQ || k == AX_TOK_QUESTION || k == AX_TOK_ARROW || k == AX_TOK_FAT_ARROW || k == AX_TOK_KW_AS) {
            report(p, peek(p)->span, AX_PARSE_LEADING_OPERATOR, "Leading operator not allowed");
            advance(p);
        }

        AxAstExpr *expr = parse_expr(p);
        const AxToken *tok = peek(p);
        if ((tok->kind >= AX_TOK_EQ && tok->kind <= AX_TOK_SHR_EQ) && !(p->mode_on && (tok->flags & AX_TOK_FLAG_NL_BEFORE))) {
            stmt->kind = AX_STMT_ASSIGN;
            switch(tok->kind) {
                case AX_TOK_EQ: stmt->assign.op = AX_ASSIGN_EQ; break;
                case AX_TOK_PLUS_EQ: stmt->assign.op = AX_ASSIGN_ADD; break;
                case AX_TOK_MINUS_EQ: stmt->assign.op = AX_ASSIGN_SUB; break;
                case AX_TOK_STAR_EQ: stmt->assign.op = AX_ASSIGN_MUL; break;
                case AX_TOK_SLASH_EQ: stmt->assign.op = AX_ASSIGN_DIV; break;
                case AX_TOK_PERCENT_EQ: stmt->assign.op = AX_ASSIGN_REM; break;
                case AX_TOK_AMP_EQ: stmt->assign.op = AX_ASSIGN_BITAND; break;
                case AX_TOK_PIPE_EQ: stmt->assign.op = AX_ASSIGN_BITOR; break;
                case AX_TOK_CARET_EQ: stmt->assign.op = AX_ASSIGN_BITXOR; break;
                case AX_TOK_SHL_EQ: stmt->assign.op = AX_ASSIGN_SHL; break;
                case AX_TOK_SHR_EQ: stmt->assign.op = AX_ASSIGN_SHR; break;
                default: stmt->assign.op = AX_ASSIGN_EQ; break;
            }
            advance(p);
            stmt->assign.left = expr;
            stmt->assign.right = parse_expr(p);
            consume(p, AX_TOK_SEMI);
        } else {
            stmt->kind = AX_STMT_EXPR;
            stmt->expr_stmt.expr = expr;
            stmt->expr_stmt.has_semi = consume(p, AX_TOK_SEMI);
        }
    }
    
    sync_to_term(p);
    consume(p, AX_TOK_SEMI);
    return stmt;
}

static AxAstGenericParams *parse_generic_params(Parser *p) {
    if (!check(p, AX_TOK_LT)) return NULL;
    AxAstGenericParams *params = NEW_NODE(p, AxAstGenericParams);
    params->span = peek(p)->span;
    advance(p);
    
    bool old = p->mode_on;
    p->mode_on = false;
    
    AxAstGenericParam **curr = &params->params;
    while (!check(p, AX_TOK_GT) && !check(p, AX_TOK_EOF)) {
        AxAstGenericParam *param = NEW_NODE(p, AxAstGenericParam);
        param->span = peek(p)->span;
        param->name = peek(p)->val.ident_val;
        expect(p, AX_TOK_IDENT, AX_PARSE_EXPECTED_TOKEN, "Expected generic param name");
        if (consume(p, AX_TOK_COLON)) {
            param->bounds = parse_bounds(p);
        } else {
            param->bounds = NULL;
        }
        *curr = param;
        curr = &param->next;
        if (!consume(p, AX_TOK_COMMA)) break;
    }
    expect(p, AX_TOK_GT, AX_PARSE_EXPECTED_TOKEN, "Expected '>'");
    
    p->mode_on = old;
    return params;
}

static AxAstWhereClause *parse_where_clause(Parser *p) {
    if (!consume(p, AX_TOK_KW_WHERE)) return NULL;
    AxAstWhereClause *wc = NEW_NODE(p, AxAstWhereClause);
    wc->span = peek_nth(p, -1)->span;
    
    AxAstWherePred **curr = &wc->preds;
    while (!check(p, AX_TOK_LBRACE) && !check(p, AX_TOK_SEMI) && !check(p, AX_TOK_EOF)) {
        AxAstWherePred *pred = NEW_NODE(p, AxAstWherePred);
        pred->span = peek(p)->span;
        pred->type = parse_type(p);
        expect(p, AX_TOK_COLON, AX_PARSE_EXPECTED_TOKEN, "Expected ':'");
        pred->bounds = parse_bounds(p);
        *curr = pred;
        curr = &pred->next;
        if (!consume(p, AX_TOK_COMMA)) break;
    }
    return wc;
}

static AxAstAttr *parse_attributes(Parser *p) {
    AxAstAttr *head = NULL;
    AxAstAttr **curr = &head;
    while (consume(p, AX_TOK_AT)) {
        AxAstAttr *attr = NEW_NODE(p, AxAstAttr);
        attr->span = peek_nth(p, -1)->span;
        attr->name = peek(p)->val.ident_val;
        expect(p, AX_TOK_IDENT, AX_PARSE_EXPECTED_TOKEN, "Expected attribute name");
        
        if (check(p, AX_TOK_LPAREN) && !(peek(p)->flags & AX_TOK_FLAG_NL_BEFORE)) {
            advance(p);
            bool old = p->mode_on;
            p->mode_on = false;
            AxAstAttrArg **arg_curr = &attr->args;
            while (!check(p, AX_TOK_RPAREN) && !check(p, AX_TOK_EOF)) {
                AxAstAttrArg *arg = NEW_NODE(p, AxAstAttrArg);
                arg->span = peek(p)->span;
                if (check(p, AX_TOK_IDENT) && peek_nth(p, 1)->kind == AX_TOK_EQ) {
                    arg->name = peek(p)->val.ident_val;
                    advance(p); // IDENT
                    advance(p); // =
                }
                arg->expr = parse_expr(p);
                *arg_curr = arg;
                arg_curr = &arg->next;
                if (!consume(p, AX_TOK_COMMA)) break;
            }
            p->mode_on = old;
            expect(p, AX_TOK_RPAREN, AX_PARSE_UNCLOSED_DELIMITER, "Expected ')'");
        }
        *curr = attr;
        curr = &attr->next;
    }
    return head;
}

static AxAstVis parse_visibility(Parser *p) {
    AxAstVis vis = {0};
    vis.span = peek(p)->span;
    if (consume(p, AX_TOK_KW_PUB)) {
        vis.kind = AX_VIS_PUB;
        if (check(p, AX_TOK_LPAREN) && !(peek(p)->flags & AX_TOK_FLAG_NL_BEFORE)) {
            size_t old = p->pos;
            advance(p);
            if (check(p, AX_TOK_IDENT)) {
                StrId id = peek(p)->val.ident_val;
                if (ax_sv_eq(ax_interner_get(p->interner, id), ax_sv_cstr("package"))) {
                    advance(p);
                    if (consume(p, AX_TOK_RPAREN)) {
                        vis.kind = AX_VIS_PUB_PACKAGE;
                        return vis;
                    }
                } else if (ax_sv_eq(ax_interner_get(p->interner, id), ax_sv_cstr("module"))) {
                    advance(p);
                    if (consume(p, AX_TOK_RPAREN)) {
                        vis.kind = AX_VIS_PUB_MODULE;
                        return vis;
                    }
                }
            }
            p->pos = old; // backtrack if it wasn't pub(package) or pub(module)
        }
    } else {
        vis.kind = AX_VIS_PRIVATE;
    }
    return vis;
}

static AxAstItem *parse_item(Parser *p) {
    if (consume(p, AX_TOK_SEMI)) {
        AxAstItem *empty = NEW_NODE(p, AxAstItem);
        empty->kind = AX_ITEM_ERROR;
        return empty; // simple hack
    }

    AxAstItem *item = NEW_NODE(p, AxAstItem);
    item->span = peek(p)->span;
    item->attrs = parse_attributes(p);
    item->vis = parse_visibility(p);
    item->next = NULL;

    if (check(p, AX_TOK_IDENT) && ax_sv_eq(ax_interner_get(p->interner, peek(p)->val.ident_val), ax_sv_cstr("import"))) {
        report(p, peek(p)->span, AX_PARSE_IMPORT, "import is not a keyword");
        advance(p);
        item->kind = AX_ITEM_USE;
        item->use.tree = parse_use_tree(p);
        sync_to_term(p);
    } else if (check(p, AX_TOK_IDENT) && ax_sv_eq(ax_interner_get(p->interner, peek(p)->val.ident_val), ax_sv_cstr("mod"))) {
        report(p, peek(p)->span, AX_PARSE_MOD, "write module at the top");
        advance(p);
        item->kind = AX_ITEM_MODULE;
        sync_to_term(p);
    } else if (consume(p, AX_TOK_KW_MODULE)) {
        if (item->vis.kind != AX_VIS_PRIVATE) {
            report(p, item->span, AX_PARSE_VIS_NOT_ALLOWED, "vis not allowed");
        }
        item->kind = AX_ITEM_MODULE;
        item->module.path = parse_dotted_name(p);
        sync_to_term(p);
    } else if (consume(p, AX_TOK_KW_USE)) {
        item->kind = AX_ITEM_USE;
        item->use.tree = parse_use_tree(p);
        sync_to_term(p);
    } else if (consume(p, AX_TOK_KW_CONST)) {
        item->kind = AX_ITEM_CONST;
        item->const_decl.name = peek(p)->val.ident_val;
        expect(p, AX_TOK_IDENT, AX_PARSE_EXPECTED_TOKEN, "Expected const name");
        expect(p, AX_TOK_COLON, AX_PARSE_EXPECTED_TOKEN, "Expected ':'");
        item->const_decl.type = parse_type(p);
        expect(p, AX_TOK_EQ, AX_PARSE_EXPECTED_TOKEN, "Expected '='");
        item->const_decl.expr = parse_expr(p);
        sync_to_term(p);
    } else if (check(p, AX_TOK_KW_STATIC) || (check(p, AX_TOK_KW_UNSAFE) && peek_nth(p, 1)->kind == AX_TOK_KW_STATIC)) {
        bool is_unsafe = consume(p, AX_TOK_KW_UNSAFE);
        consume(p, AX_TOK_KW_STATIC);
        item->kind = AX_ITEM_STATIC;
        item->static_decl.is_unsafe = is_unsafe;
        item->static_decl.is_mut = consume(p, AX_TOK_KW_MUT);
        item->static_decl.name = peek(p)->val.ident_val;
        expect(p, AX_TOK_IDENT, AX_PARSE_EXPECTED_TOKEN, "Expected static name");
        expect(p, AX_TOK_COLON, AX_PARSE_EXPECTED_TOKEN, "Expected ':'");
        item->static_decl.type = parse_type(p);
        if (consume(p, AX_TOK_EQ)) {
            item->static_decl.expr = parse_expr(p);
        } else {
            item->static_decl.expr = NULL;
        }
        sync_to_term(p);
    } else if (check(p, AX_TOK_KW_FN) || 
              (check(p, AX_TOK_KW_UNSAFE) && peek_nth(p, 1)->kind == AX_TOK_KW_FN) || 
              (check(p, AX_TOK_KW_EXTERN) && (peek_nth(p, 1)->kind == AX_TOK_KW_FN || (peek_nth(p, 1)->kind == AX_TOK_STR && peek_nth(p, 2)->kind == AX_TOK_KW_FN))) ||
              (check(p, AX_TOK_KW_ASYNC) || check(p, AX_TOK_KW_COMPTIME))) {
        
        item->kind = AX_ITEM_FN;
        item->fn.is_async = consume(p, AX_TOK_KW_ASYNC);
        item->fn.is_comptime = consume(p, AX_TOK_KW_COMPTIME);
        item->fn.is_unsafe = consume(p, AX_TOK_KW_UNSAFE);
        
        if (consume(p, AX_TOK_KW_EXTERN)) {
            if (check(p, AX_TOK_STR)) {
                item->fn.abi = ax_intern(p->interner, (StrView){ (const char*)peek(p)->val.str_val.bytes, peek(p)->val.str_val.len });
                advance(p);
            }
        }
        
        expect(p, AX_TOK_KW_FN, AX_PARSE_EXPECTED_TOKEN, "Expected 'fn'");
        item->fn.name = peek(p)->val.ident_val;
        expect(p, AX_TOK_IDENT, AX_PARSE_EXPECTED_TOKEN, "Expected function name");
        
        item->fn.generic_params = parse_generic_params(p);
        
        expect(p, AX_TOK_LPAREN, AX_PARSE_EXPECTED_TOKEN, "Expected '('");
        item->fn.params = parse_params(p);
        expect(p, AX_TOK_RPAREN, AX_PARSE_UNCLOSED_DELIMITER, "Expected ')'");
        
        if (consume(p, AX_TOK_ARROW)) {
            item->fn.ret_type = parse_type(p);
        } else {
            item->fn.ret_type = NULL;
        }
        
        item->fn.where_clause = parse_where_clause(p);

        if (check(p, AX_TOK_LBRACE)) {
            AxAstBlock *block = parse_block(p);
            item->fn.body = block;
        } else {
            item->fn.body = NULL;
            if (!p->allow_bodiless_fn) {
                report(p, peek(p)->span, AX_PARSE_EXPECTED_TOKEN, "Expected '{'");
            }
            sync_to_term(p);
        }
    } else if (consume(p, AX_TOK_KW_STRUCT)) {
        item->kind = AX_ITEM_STRUCT;
        item->struct_decl.name = peek(p)->val.ident_val;
        expect(p, AX_TOK_IDENT, AX_PARSE_EXPECTED_TOKEN, "Expected struct name");
        item->struct_decl.generic_params = parse_generic_params(p);
        
        if (check(p, AX_TOK_LPAREN)) {
            item->struct_decl.is_tuple = true;
            advance(p);
            AxAstType **curr = &item->struct_decl.tuple_types;
            while (!check(p, AX_TOK_RPAREN) && !check(p, AX_TOK_EOF)) {
                *curr = parse_type(p); // Actually TupleField has visibility and attributes, but we might just parse Type and attach attrs if ast.h had it. ast.h has `AxAstType *tuple_types;` wait, `AxAstType` doesn't have visibility!
                // Ah! `AxAstFieldDecl` vs `AxAstType`. In ast.h struct_decl has `AxAstFieldDecl *struct_fields;` OR `AxAstType *tuple_types;`
                *curr = parse_type(p);
                curr = &(*curr)->next;
                if (!consume(p, AX_TOK_COMMA)) break;
            }
            expect(p, AX_TOK_RPAREN, AX_PARSE_UNCLOSED_DELIMITER, "Expected ')'");
            item->struct_decl.where_clause = parse_where_clause(p);
            sync_to_term(p);
        } else {
            item->struct_decl.where_clause = parse_where_clause(p);
            if (consume(p, AX_TOK_LBRACE)) {
                item->struct_decl.is_tuple = false;
                AxAstFieldDecl **curr = &item->struct_decl.struct_fields;
                while (!check(p, AX_TOK_RBRACE) && !check(p, AX_TOK_EOF)) {
                    AxAstFieldDecl *fd = NEW_NODE(p, AxAstFieldDecl);
                    fd->span = peek(p)->span;
                    fd->attrs = parse_attributes(p);
                    fd->vis = parse_visibility(p);
                    fd->name = peek(p)->val.ident_val;
                    expect(p, AX_TOK_IDENT, AX_PARSE_EXPECTED_TOKEN, "Expected field name");
                    expect(p, AX_TOK_COLON, AX_PARSE_EXPECTED_TOKEN, "Expected ':'");
                    fd->type = parse_type(p);
                    *curr = fd;
                    curr = &fd->next;
                    if (!consume(p, AX_TOK_COMMA)) break;
                }
                expect(p, AX_TOK_RBRACE, AX_PARSE_UNCLOSED_DELIMITER, "Expected '}'");
            } else {
                item->struct_decl.struct_fields = NULL;
                sync_to_term(p);
            }
        }
    } else if (consume(p, AX_TOK_KW_ENUM)) {
        item->kind = AX_ITEM_ENUM;
        item->enum_decl.name = peek(p)->val.ident_val;
        expect(p, AX_TOK_IDENT, AX_PARSE_EXPECTED_TOKEN, "Expected enum name");
        item->enum_decl.generic_params = parse_generic_params(p);
        item->enum_decl.where_clause = parse_where_clause(p);
        
        if (consume(p, AX_TOK_LBRACE)) {
            AxAstVariantDecl **v_ptr = &item->enum_decl.variants;
            while (!check(p, AX_TOK_EOF) && !check(p, AX_TOK_RBRACE)) {
                AxAstVariantDecl *v = NEW_NODE(p, AxAstVariantDecl);
                v->span = peek(p)->span;
                v->attrs = parse_attributes(p);
                v->name = peek(p)->val.ident_val;
                expect(p, AX_TOK_IDENT, AX_PARSE_EXPECTED_TOKEN, "Expected variant name");
                
                if (consume(p, AX_TOK_LPAREN)) {
                    v->is_struct = false;
                    AxAstType **curr = &v->tuple_types;
                    while (!check(p, AX_TOK_RPAREN) && !check(p, AX_TOK_EOF)) {
                        *curr = parse_type(p);
                        curr = &(*curr)->next;
                        if (!consume(p, AX_TOK_COMMA)) break;
                    }
                    expect(p, AX_TOK_RPAREN, AX_PARSE_UNCLOSED_DELIMITER, "Expected ')'");
                } else if (consume(p, AX_TOK_LBRACE)) {
                    v->is_struct = true;
                    AxAstFieldDecl **curr = &v->struct_fields;
                    while (!check(p, AX_TOK_RBRACE) && !check(p, AX_TOK_EOF)) {
                        AxAstFieldDecl *fd = NEW_NODE(p, AxAstFieldDecl);
                        fd->span = peek(p)->span;
                        fd->attrs = parse_attributes(p);
                        fd->name = peek(p)->val.ident_val;
                        expect(p, AX_TOK_IDENT, AX_PARSE_EXPECTED_TOKEN, "Expected field name");
                        expect(p, AX_TOK_COLON, AX_PARSE_EXPECTED_TOKEN, "Expected ':'");
                        fd->type = parse_type(p);
                        *curr = fd;
                        curr = &fd->next;
                        if (!consume(p, AX_TOK_COMMA)) break;
                    }
                    expect(p, AX_TOK_RBRACE, AX_PARSE_UNCLOSED_DELIMITER, "Expected '}'");
                }
                
                *v_ptr = v;
                v_ptr = &v->next;
                if (!consume(p, AX_TOK_COMMA)) break;
            }
            expect(p, AX_TOK_RBRACE, AX_PARSE_UNCLOSED_DELIMITER, "Expected '}'");
        } else {
            sync_to_term(p);
        }
    } else if (consume(p, AX_TOK_KW_TRAIT)) {
        item->kind = AX_ITEM_TRAIT;
        item->trait.name = peek(p)->val.ident_val;
        expect(p, AX_TOK_IDENT, AX_PARSE_EXPECTED_TOKEN, "Expected trait name");
        item->trait.generic_params = parse_generic_params(p);
        if (consume(p, AX_TOK_COLON)) {
            item->trait.supertraits = parse_bounds(p);
        }
        item->trait.where_clause = parse_where_clause(p);
        if (consume(p, AX_TOK_LBRACE)) {
            bool old_bodiless = p->allow_bodiless_fn;
            p->allow_bodiless_fn = true;
            AxAstItem **curr = &item->trait.members;
            while (!check(p, AX_TOK_RBRACE) && !check(p, AX_TOK_EOF)) {
                *curr = parse_item(p); // recursive call! It works since traits have fns and types inside
                curr = &(*curr)->next;
            }
            p->allow_bodiless_fn = old_bodiless;
            expect(p, AX_TOK_RBRACE, AX_PARSE_UNCLOSED_DELIMITER, "Expected '}'");
        } else {
            sync_to_term(p);
        }
    } else if (consume(p, AX_TOK_KW_IMPL)) {
        item->kind = AX_ITEM_IMPL;
        if (item->vis.kind != AX_VIS_PRIVATE) {
            report(p, item->span, AX_PARSE_VIS_NOT_ALLOWED, "vis not allowed on impl");
        }
        item->impl.generic_params = parse_generic_params(p);
        
        AxAstType *t1 = parse_type(p);
        if (consume(p, AX_TOK_KW_FOR)) {
            item->impl.trait_path = t1;
            item->impl.self_type = parse_type(p);
        } else {
            item->impl.self_type = t1;
        }
        item->impl.where_clause = parse_where_clause(p);
        
        if (consume(p, AX_TOK_LBRACE)) {
            AxAstItem **curr = &item->impl.members;
            while (!check(p, AX_TOK_RBRACE) && !check(p, AX_TOK_EOF)) {
                *curr = parse_item(p);
                curr = &(*curr)->next;
            }
            expect(p, AX_TOK_RBRACE, AX_PARSE_UNCLOSED_DELIMITER, "Expected '}'");
        } else {
            sync_to_term(p);
        }
    } else if (consume(p, AX_TOK_KW_TYPE)) {
        item->kind = AX_ITEM_TYPE_ALIAS;
        item->type_alias.name = peek(p)->val.ident_val;
        expect(p, AX_TOK_IDENT, AX_PARSE_EXPECTED_TOKEN, "Expected type name");
        item->type_alias.generic_params = parse_generic_params(p);
        
        if (check(p, AX_TOK_COLON)) {
            // assoc type in trait bounds
            advance(p);
            // wait ast.h doesn't have a place for bounds on type alias... Oh wait, AssocType?
            // "type Item : Bounds" vs "type Item = T". If we just consume it it's fine for v0.1 parser.
            parse_bounds(p); 
        }
        
        if (consume(p, AX_TOK_EQ)) {
            item->type_alias.type = parse_type(p);
        }
        sync_to_term(p);
    } else if (consume(p, AX_TOK_KW_EXTERN)) {
        if (item->vis.kind != AX_VIS_PRIVATE) {
            report(p, item->span, AX_PARSE_VIS_NOT_ALLOWED, "vis not allowed on extern block");
        }
        item->kind = AX_ITEM_EXTERN_BLOCK;
        item->extern_block.abi = ax_intern(p->interner, (StrView){ (const char*)peek(p)->val.str_val.bytes, peek(p)->val.str_val.len });
        expect(p, AX_TOK_STR, AX_PARSE_EXPECTED_TOKEN, "Expected string literal for ABI");
        expect(p, AX_TOK_LBRACE, AX_PARSE_EXPECTED_TOKEN, "Expected '{'");
        
        bool old_bodiless = p->allow_bodiless_fn;
        p->allow_bodiless_fn = true;
        AxAstItem **curr = &item->extern_block.members;
        while (!check(p, AX_TOK_RBRACE) && !check(p, AX_TOK_EOF)) {
            *curr = parse_item(p);
            curr = &(*curr)->next;
        }
        p->allow_bodiless_fn = old_bodiless;
        expect(p, AX_TOK_RBRACE, AX_PARSE_UNCLOSED_DELIMITER, "Expected '}'");
    } else {
        report(p, item->span, AX_PARSE_EXPECTED_ITEM, "Expected item");
        item->kind = AX_ITEM_ERROR;
        advance(p);
        sync_to_term(p);
    }
    return item;
}

AxParseResult ax_parse(AxArena *arena, const AxToken *tokens, size_t token_count, AxDiagSink *sink, StrInterner *interner) {
    Parser p = {0};
    p.arena = arena;
    p.tokens = tokens;
    p.count = token_count;
    p.pos = 0;
    p.sink = sink;
    p.interner = interner;
    p.mode_on = true;
    AxParseResult res = {0};
    
    AxAstItem **curr_item = &res.ast.items;
    while (!check(&p, AX_TOK_EOF)) {
        AxAstItem *item = parse_item(&p);
        if (item->kind != AX_ITEM_ERROR) {
            *curr_item = item;
            curr_item = &(*curr_item)->next;
        }
    }
    
    return res;
}
