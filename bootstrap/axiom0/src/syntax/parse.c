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
} Parser;

static inline const AxToken *peek(Parser *p) {
    if (p->pos < p->count) return &p->tokens[p->pos];
    return &p->tokens[p->count - 1]; // Assume EOF is at the end
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
    return ax_arena_alloc(p->arena, size, 8);
}
#define NEW_NODE(p, type) ((type *)alloc_node(p, sizeof(type)))

// Forward decls
static AxAstExpr *parse_expr(Parser *p);
static AxAstExpr *parse_expr_prec(Parser *p, int min_prec);
static AxAstType *parse_type(Parser *p);
static AxAstPat *parse_pattern(Parser *p);
static AxAstBlock *parse_block(Parser *p);
static AxAstItem *parse_item(Parser *p);
static AxAstStmt *parse_stmt(Parser *p);

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
    // For now, assume a single identifier for simplicity, wait no, let's do real parse
    // Actually wait, ast.h says AxAstDottedName has StrId *segments; size_t count;
    // Let's allocate a static buffer for up to 32 segments
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
    tree->alias.v = 0;
    tree->subtrees = NULL;
    tree->next = NULL;
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

static AxAstExpr *parse_primary(Parser *p) {
    const AxToken *tok = peek(p);
    AxAstExpr *expr = NEW_NODE(p, AxAstExpr);
    expr->span = tok->span;
    expr->next = NULL;


    if (tok->kind == AX_TOK_MINUS || tok->kind == AX_TOK_BANG || tok->kind == AX_TOK_TILDE) {
        expr->kind = AX_EXPR_UNARY;
        expr->unary.op = (tok->kind == AX_TOK_MINUS) ? AX_UNOP_NEG : (tok->kind == AX_TOK_BANG ? AX_UNOP_NOT : AX_UNOP_BITNOT);
        advance(p);
        expr->unary.expr = parse_expr_prec(p, 13); // Unary precedence
        return expr;
    } else if (tok->kind == AX_TOK_INT || tok->kind == AX_TOK_FLOAT || tok->kind == AX_TOK_STR ||
        tok->kind == AX_TOK_BYTE_STR || tok->kind == AX_TOK_CHAR || tok->kind == AX_TOK_KW_TRUE ||
        tok->kind == AX_TOK_KW_FALSE) {
        expr->kind = AX_EXPR_LITERAL;
        expr->literal = *tok;
        advance(p);
        return expr;
    } else if (tok->kind == AX_TOK_IDENT) {
        expr->kind = AX_EXPR_PATH;
        AxAstTypePathSegment *seg = NEW_NODE(p, AxAstTypePathSegment);
        seg->span = tok->span;
        seg->name = tok->val.ident_val;
        seg->generic_args = NULL;
        seg->next = NULL;
        expr->path.segments = seg;
        advance(p);
        return expr;
    } else if (consume(p, AX_TOK_LPAREN)) {
        expr->kind = AX_EXPR_PAREN;
        bool old = p->mode_on;
        p->mode_on = false;
        expr->paren.expr = parse_expr(p);
        p->mode_on = old;
        expect(p, AX_TOK_RPAREN, AX_PARSE_UNCLOSED_DELIMITER, "Expected ')'");
        return expr;
    }

    report(p, tok->span, AX_PARSE_EXPECTED_EXPR, "Expected expression");
    expr->kind = AX_EXPR_ERROR;
    advance(p);
    return expr;
}

static AxAstExpr *parse_expr_prec(Parser *p, int min_prec) {
    AxAstExpr *left = parse_primary(p);

    while (true) {
        const AxToken *tok = peek(p);
        int prec = get_infix_prec(tok->kind);
        if (prec == 0 || prec > min_prec) break;

        if (p->mode_on && (tok->flags & AX_TOK_FLAG_NL_BEFORE)) {
            if (tok->kind != AX_TOK_DOT) {
                break;
            }
        }

        advance(p); // Consume operator
        if (tok->kind == AX_TOK_KW_AS) {
            AxAstExpr *cast = NEW_NODE(p, AxAstExpr);
            cast->span = left->span;
            cast->kind = AX_EXPR_CAST;
            cast->cast.expr = left;
            cast->cast.type = parse_type(p);
            left = cast;
            continue;
        }

        AxAstExpr *bin = NEW_NODE(p, AxAstExpr);
        bin->span = left->span;
        bin->kind = AX_EXPR_BINARY;
        bin->binary.left = left;
        bin->binary.op = token_to_binop(tok->kind);
        
        int next_prec = prec;
        if (prec == 10 || prec == 13) {
            next_prec = prec - 1; // non-associative fallback
        }

        bin->binary.right = parse_expr_prec(p, next_prec);
        left = bin;
    }

    return left;
}

static AxAstExpr *parse_expr(Parser *p) {
    return parse_expr_prec(p, 14);
}

static AxAstType *parse_type(Parser *p) {
    AxAstType *type = NEW_NODE(p, AxAstType);
    type->span = peek(p)->span;
    type->next = NULL;

    if (consume(p, AX_TOK_IDENT)) {
        type->kind = AX_TYPE_PATH;
        type->path.segments = NEW_NODE(p, AxAstTypePathSegment);
        type->path.segments->name = peek_nth(p, -1)->val.ident_val;
        type->path.segments->next = NULL;
    } else {
        report(p, type->span, AX_PARSE_EXPECTED_TYPE, "Expected type");
        type->kind = AX_TYPE_ERROR;
        advance(p);
    }
    return type;
}

static AxAstPat *parse_pattern(Parser *p) {
    AxAstPat *pat = NEW_NODE(p, AxAstPat);
    pat->span = peek(p)->span;
    pat->next = NULL;

    if (consume(p, AX_TOK_KW_MUT)) {
        expect(p, AX_TOK_IDENT, AX_PARSE_EXPECTED_TOKEN, "Expected identifier after mut");
        pat->kind = AX_PAT_BINDING;
        pat->binding.is_mut = true;
        pat->binding.name = peek_nth(p, -1)->val.ident_val;
    } else if (consume(p, AX_TOK_IDENT)) {
        pat->kind = AX_PAT_BINDING;
        pat->binding.is_mut = false;
        pat->binding.name = peek_nth(p, -1)->val.ident_val;
    } else {
        report(p, pat->span, AX_PARSE_EXPECTED_PATTERN, "Expected pattern");
        pat->kind = AX_PAT_ERROR;
        advance(p);
    }
    return pat;
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
        param->next = NULL;
        if (consume(p, AX_TOK_KW_MUT)) {
            param->is_mut = true;
        } else {
            param->is_mut = false;
        }
        param->name = peek(p)->val.ident_val;
        expect(p, AX_TOK_IDENT, AX_PARSE_EXPECTED_TOKEN, "Expected param name");
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
        } else {
            stmt->let.expr = NULL;
        }
        stmt->let.else_block = NULL;
    } else {
        AxAstExpr *expr = parse_expr(p);
        const AxToken *tok = peek(p);
        if (tok->kind >= AX_TOK_EQ && tok->kind <= AX_TOK_SHR_EQ) {
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

static AxAstItem *parse_item(Parser *p) {
    AxAstItem *item = NEW_NODE(p, AxAstItem);
    item->span = peek(p)->span;
    item->attrs = NULL;
    item->vis.kind = AX_VIS_PRIVATE;
    item->next = NULL;

    if (check(p, AX_TOK_IDENT) && ax_sv_eq(ax_interner_get(p->interner, peek(p)->val.ident_val), ax_sv_cstr("import"))) {
        report(p, peek(p)->span, AX_PARSE_IMPORT, "import is not a keyword");
        advance(p);
        item->kind = AX_ITEM_USE;
        item->use.tree = parse_use_tree(p);
        sync_to_term(p);
    } else if (consume(p, AX_TOK_KW_MODULE)) {
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
    } else if (consume(p, AX_TOK_KW_STATIC)) {
        item->kind = AX_ITEM_STATIC;
        item->static_decl.is_unsafe = false;
        item->static_decl.is_mut = false;
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
    } else if (consume(p, AX_TOK_KW_FN)) {
        item->kind = AX_ITEM_FN;
        item->fn.name = peek(p)->val.ident_val;
        expect(p, AX_TOK_IDENT, AX_PARSE_EXPECTED_TOKEN, "Expected function name");
        expect(p, AX_TOK_LPAREN, AX_PARSE_EXPECTED_TOKEN, "Expected '('");
        item->fn.params = parse_params(p);
        expect(p, AX_TOK_RPAREN, AX_PARSE_EXPECTED_TOKEN, "Expected ')'");
        
        if (consume(p, AX_TOK_ARROW)) {
            item->fn.ret_type = parse_type(p);
        } else {
            item->fn.ret_type = NULL;
        }

        if (check(p, AX_TOK_LBRACE)) {
            AxAstBlock *block = parse_block(p);
            item->fn.body = block;
        } else {
            item->fn.body = NULL;
            sync_to_term(p);
        }
    } else if (consume(p, AX_TOK_KW_STRUCT)) {
        item->kind = AX_ITEM_STRUCT;
        item->struct_decl.name = peek(p)->val.ident_val;
        expect(p, AX_TOK_IDENT, AX_PARSE_EXPECTED_TOKEN, "Expected struct name");
        if (check(p, AX_TOK_LBRACE)) {
            advance(p); // '{'
            item->struct_decl.is_tuple = false;
            expect(p, AX_TOK_RBRACE, AX_PARSE_EXPECTED_TOKEN, "Expected '}'");
        } else {
            sync_to_term(p);
        }
    } else if (consume(p, AX_TOK_KW_ENUM)) {
        item->kind = AX_ITEM_ENUM;
        item->enum_decl.name = peek(p)->val.ident_val;
        expect(p, AX_TOK_IDENT, AX_PARSE_EXPECTED_TOKEN, "Expected enum name");
        if (check(p, AX_TOK_LBRACE)) {
            advance(p);
            expect(p, AX_TOK_RBRACE, AX_PARSE_EXPECTED_TOKEN, "Expected '}'");
        } else {
            sync_to_term(p);
        }
    } else if (consume(p, AX_TOK_KW_TRAIT)) {
        item->kind = AX_ITEM_TRAIT;
        item->trait.name = peek(p)->val.ident_val;
        expect(p, AX_TOK_IDENT, AX_PARSE_EXPECTED_TOKEN, "Expected trait name");
        if (check(p, AX_TOK_LBRACE)) {
            advance(p);
            expect(p, AX_TOK_RBRACE, AX_PARSE_EXPECTED_TOKEN, "Expected '}'");
        } else {
            sync_to_term(p);
        }
    } else if (consume(p, AX_TOK_KW_IMPL)) {
        item->kind = AX_ITEM_IMPL;
        item->impl.self_type = parse_type(p);
        if (check(p, AX_TOK_LBRACE)) {
            advance(p);
            expect(p, AX_TOK_RBRACE, AX_PARSE_EXPECTED_TOKEN, "Expected '}'");
        } else {
            sync_to_term(p);
        }
    } else if (consume(p, AX_TOK_KW_TYPE)) {
        item->kind = AX_ITEM_TYPE_ALIAS;
        item->type_alias.name = peek(p)->val.ident_val;
        expect(p, AX_TOK_IDENT, AX_PARSE_EXPECTED_TOKEN, "Expected type name");
        expect(p, AX_TOK_EQ, AX_PARSE_EXPECTED_TOKEN, "Expected '='");
        item->type_alias.type = parse_type(p);
        sync_to_term(p);
    } else {
        report(p, item->span, AX_PARSE_EXPECTED_ITEM, "Expected item");
        item->kind = AX_ITEM_ERROR;
        advance(p);
        sync_to_term(p);
    }
    return item;
}

AxParseResult ax_parse(AxArena *arena, const AxToken *tokens, size_t token_count, AxDiagSink *sink, StrInterner *interner) {
    Parser p = {arena, tokens, token_count, 0, sink, interner, true};
    AxParseResult res = {0};
    
    AxAstItem **curr_item = &res.ast.items;
    while (!check(&p, AX_TOK_EOF)) {
        *curr_item = parse_item(&p);
        curr_item = &(*curr_item)->next;
    }
    
    return res;
}
