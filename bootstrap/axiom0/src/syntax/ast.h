#ifndef AX_SYNTAX_AST_H
#define AX_SYNTAX_AST_H

#include "kernel/base.h"
#include "kernel/arena.h"
#include "lex/lex.h"

/* AST nodes are allocated in an AxArena. They use invasive `next` pointers for lists.
 * This file reserves the full v0.1 data model (ADR-0005 §4). */

typedef struct AxAstAttr AxAstAttr;
typedef struct AxAstAttrArg AxAstAttrArg;
typedef struct AxAstVis AxAstVis;
typedef struct AxAstGenericParams AxAstGenericParams;
typedef struct AxAstGenericParam AxAstGenericParam;
typedef struct AxAstGenericArgs AxAstGenericArgs;
typedef struct AxAstGenericArg AxAstGenericArg;
typedef struct AxAstWhereClause AxAstWhereClause;
typedef struct AxAstWherePred AxAstWherePred;
typedef struct AxAstBlock AxAstBlock;
typedef struct AxAstItem AxAstItem;
typedef struct AxAstStmt AxAstStmt;
typedef struct AxAstExpr AxAstExpr;
typedef struct AxAstPat AxAstPat;
typedef struct AxAstType AxAstType;
typedef struct AxAstMatchArm AxAstMatchArm;
typedef struct AxAstFieldInit AxAstFieldInit;
typedef struct AxAstFieldDecl AxAstFieldDecl;
typedef struct AxAstVariantDecl AxAstVariantDecl;
typedef struct AxAstParam AxAstParam;
typedef struct AxAstUseTree AxAstUseTree;

typedef struct AxAstDottedName {
    Span span;
    StrId *segments;
    size_t count;
} AxAstDottedName;

typedef enum AxAstVisKind {
    AX_VIS_PRIVATE,
    AX_VIS_PUB,
    AX_VIS_PUB_PACKAGE,
    AX_VIS_PUB_MODULE,
} AxAstVisKind;

struct AxAstVis {
    Span span;
    AxAstVisKind kind;
};

struct AxAstAttrArg {
    Span span;
    StrId name; /* 0 if positional */
    AxAstExpr *expr;
    AxAstAttrArg *next;
};

struct AxAstAttr {
    Span span;
    StrId name;
    AxAstAttrArg *args;
    AxAstAttr *next;
};

/* Types */

typedef enum AxAstTypeKind {
    AX_TYPE_ERROR,
    AX_TYPE_PATH,
    AX_TYPE_TUPLE,
    AX_TYPE_ARRAY,
    AX_TYPE_SLICE,
    AX_TYPE_VIEW,
    AX_TYPE_PTR,
    AX_TYPE_FN,
    AX_TYPE_DYN,
} AxAstTypeKind;

typedef struct AxAstTypePathSegment {
    Span span;
    StrId name;
    AxAstGenericArgs *generic_args;
    struct AxAstTypePathSegment *next;
} AxAstTypePathSegment;

struct AxAstType {
    AxAstTypeKind kind;
    Span span;
    AxAstType *next;
    union {
        struct {
            AxAstTypePathSegment *segments;
        } path;
        struct {
            AxAstType *elem_types;
        } tuple;
        struct {
            AxAstExpr *count;
            AxAstType *elem;
        } array;
        struct {
            AxAstType *elem;
        } slice;
        struct {
            bool is_mut;
            AxAstType *elem;
        } view;
        struct {
            bool is_mut;
            AxAstType *elem;
        } ptr;
        struct {
            bool is_unsafe;
            StrId abi; /* 0 if no extern */
            AxAstType *param_types; /* unnamed params */
            AxAstType *ret_type; /* NULL if () */
        } fn;
        struct {
            AxAstType *bounds; /* linked list of TypePath */
        } dyn;
    };
};

/* Patterns */

typedef enum AxAstPatKind {
    AX_PAT_ERROR,
    AX_PAT_WILDCARD,
    AX_PAT_RANGE,
    AX_PAT_LITERAL,
    AX_PAT_BINDING,
    AX_PAT_PATH,
    AX_PAT_TUPLE,
    AX_PAT_OR,
    AX_PAT_STRUCT,
} AxAstPatKind;

typedef struct AxAstPatField {
    Span span;
    StrId name;
    AxAstPat *pat; /* if NULL, shorthand `name` */
    struct AxAstPatField *next;
} AxAstPatField;

struct AxAstPat {
    AxAstPatKind kind;
    Span span;
    AxAstPat *next;
    union {
        struct {
            bool is_inclusive;
            AxAstPat *start; /* literal pat */
            AxAstPat *end;   /* literal pat */
        } range;
        struct {
            AxToken tok; /* INT, CHAR, true, false */
            bool is_negated;
        } literal;
        struct {
            bool is_mut;
            StrId name;
        } binding;
        struct {
            AxAstTypePathSegment *segments; /* re-use path segment for pattern paths */
            AxAstPat *payload; /* NULL, or a tuple/struct pat */
        } path;
        struct {
            AxAstPat *elems;
        } tuple;
        struct {
            AxAstPat *pats;
        } or_pat;
        struct {
            AxAstTypePathSegment *segments;
            AxAstPatField *fields;
            bool has_rest; /* .. */
        } struct_pat;
    };
};

/* Expressions */

typedef enum AxAstExprKind {
    AX_EXPR_ERROR,
    AX_EXPR_LITERAL,
    AX_EXPR_PATH,
    AX_EXPR_TUPLE,
    AX_EXPR_PAREN,
    AX_EXPR_ARRAY,
    AX_EXPR_STRUCT,
    AX_EXPR_BLOCK,
    AX_EXPR_IF,
    AX_EXPR_MATCH,
    AX_EXPR_LOOP,
    AX_EXPR_WHILE,
    AX_EXPR_FOR,
    AX_EXPR_UNSAFE,
    AX_EXPR_VIEW,
    AX_EXPR_COMPTIME,
    AX_EXPR_JUMP,
    AX_EXPR_CLOSURE,
    AX_EXPR_RANGE,
    AX_EXPR_BINARY,
    AX_EXPR_UNARY,
    AX_EXPR_CAST,
    AX_EXPR_POSTFIX,
} AxAstExprKind;

typedef enum AxAstBinOp {
    AX_BINOP_ADD, AX_BINOP_SUB, AX_BINOP_MUL, AX_BINOP_DIV, AX_BINOP_REM,
    AX_BINOP_BITAND, AX_BINOP_BITOR, AX_BINOP_BITXOR,
    AX_BINOP_SHL, AX_BINOP_SHR,
    AX_BINOP_EQ, AX_BINOP_NE, AX_BINOP_LT, AX_BINOP_LE, AX_BINOP_GT, AX_BINOP_GE,
    AX_BINOP_LOGAND, AX_BINOP_LOGOR,
} AxAstBinOp;

typedef enum AxAstUnOp {
    AX_UNOP_NEG, AX_UNOP_NOT, AX_UNOP_BITNOT, AX_UNOP_DEREF,
} AxAstUnOp;

typedef enum AxAstPostfixKind {
    AX_POSTFIX_FIELD,
    AX_POSTFIX_TUPLE_INDEX,
    AX_POSTFIX_CALL,
    AX_POSTFIX_INDEX,
    AX_POSTFIX_TRY,
    AX_POSTFIX_AWAIT,
    AX_POSTFIX_ARROW,
} AxAstPostfixKind;

typedef struct AxAstPostfixSeg {
    AxAstPostfixKind kind;
    Span span;
    struct AxAstPostfixSeg *next;
    union {
        struct {
            StrId name;
            AxAstGenericArgs *generic_args;
        } field;
        uint32_t tuple_index;
        struct {
            AxAstExpr *args;
        } call;
        struct {
            AxAstExpr *arg; /* can be range */
        } index;
        StrId arrow_name;
    };
} AxAstPostfixSeg;

typedef enum AxAstJumpKind {
    AX_JUMP_RETURN,
    AX_JUMP_BREAK,
    AX_JUMP_CONTINUE,
} AxAstJumpKind;

struct AxAstFieldInit {
    Span span;
    StrId name;
    AxAstExpr *expr; /* NULL if shorthand */
    AxAstFieldInit *next;
};

struct AxAstMatchArm {
    Span span;
    AxAstPat *pat;
    AxAstExpr *guard;
    AxAstExpr *body;
    AxAstMatchArm *next;
};

struct AxAstBlock {
    Span span;
    AxAstStmt *stmts;
};

struct AxAstExpr {
    AxAstExprKind kind;
    Span span;
    AxAstExpr *next;
    union {
        AxToken literal;
        struct {
            AxAstTypePathSegment *segments;
        } path;
        struct {
            AxAstExpr *expr;
        } paren;
        struct {
            AxAstExpr *elems;
        } tuple;
        struct {
            AxAstExpr *elems;
            AxAstExpr *count; /* if repeat [v; n] */
        } array;
        struct {
            AxAstTypePathSegment *segments;
            AxAstFieldInit *fields;
        } struct_lit;
        struct {
            AxAstBlock block;
        } block;
        struct {
            AxAstPat *let_pat; /* if let ... */
            AxAstExpr *cond;
            AxAstBlock block;
            AxAstExpr *else_branch; /* IfExpr or Block */
        } if_expr;
        struct {
            AxAstExpr *expr;
            AxAstMatchArm *arms;
        } match;
        struct {
            StrId label; /* 0 if none */
            AxAstBlock block;
        } loop;
        struct {
            StrId label;
            AxAstPat *let_pat; /* if while let */
            AxAstExpr *cond;
            AxAstBlock block;
        } while_expr;
        struct {
            StrId label;
            AxAstPat *pat;
            AxAstExpr *iter;
            AxAstBlock block;
        } for_expr;
        struct {
            AxAstBlock block;
        } unsafe_block;
        struct {
            bool is_mut;
            AxAstExpr *expr;
        } view;
        struct {
            AxAstBlock block;
        } comptime;
        struct {
            AxAstJumpKind jump_kind;
            StrId label;
            AxAstExpr *expr;
        } jump;
        struct {
            AxAstParam *params; /* actually Pat instead of Name in AST? Spec says ParamName: [mut] (IDENT | self) | _ */
            AxAstType *ret_type;
            AxAstExpr *body; /* Can be block */
        } closure;
        struct {
            bool is_inclusive;
            AxAstExpr *start;
            AxAstExpr *end;
        } range;
        struct {
            AxAstBinOp op;
            AxAstExpr *left;
            AxAstExpr *right;
        } binary;
        struct {
            AxAstUnOp op;
            AxAstExpr *expr;
        } unary;
        struct {
            AxAstExpr *expr;
            AxAstType *type;
        } cast;
        struct {
            AxAstExpr *head;
            AxAstPostfixSeg *segments;
        } postfix;
    };
};

/* Statements */

typedef enum AxAstStmtKind {
    AX_STMT_ERROR,
    AX_STMT_LET,
    AX_STMT_ASSIGN,
    AX_STMT_EXPR,
} AxAstStmtKind;

typedef enum AxAstAssignOp {
    AX_ASSIGN_EQ, AX_ASSIGN_ADD, AX_ASSIGN_SUB, AX_ASSIGN_MUL, AX_ASSIGN_DIV, AX_ASSIGN_REM,
    AX_ASSIGN_BITAND, AX_ASSIGN_BITOR, AX_ASSIGN_BITXOR, AX_ASSIGN_SHL, AX_ASSIGN_SHR,
} AxAstAssignOp;

struct AxAstStmt {
    AxAstStmtKind kind;
    Span span;
    AxAstStmt *next;
    union {
        struct {
            AxAstPat *pat;
            AxAstType *type;
            AxAstExpr *expr;
            AxAstBlock *else_block;
        } let;
        struct {
            AxAstAssignOp op;
            AxAstExpr *left;
            AxAstExpr *right;
        } assign;
        struct {
            AxAstExpr *expr;
            bool has_semi;
        } expr_stmt;
    };
};

/* Items */

typedef enum AxAstItemKind {
    AX_ITEM_ERROR,
    AX_ITEM_MODULE,
    AX_ITEM_USE,
    AX_ITEM_FN,
    AX_ITEM_STRUCT,
    AX_ITEM_ENUM,
    AX_ITEM_TRAIT,
    AX_ITEM_IMPL,
    AX_ITEM_TYPE_ALIAS,
    AX_ITEM_CONST,
    AX_ITEM_STATIC,
    AX_ITEM_EXTERN_BLOCK,
} AxAstItemKind;

struct AxAstGenericParam {
    Span span;
    StrId name;
    AxAstType *bounds; /* linked list of TypePaths */
    AxAstGenericParam *next;
};

struct AxAstGenericParams {
    Span span;
    AxAstGenericParam *params;
};

struct AxAstGenericArg {
    Span span;
    StrId name; /* 0 if type arg */
    AxAstType *type;
    AxAstGenericArg *next;
};

struct AxAstGenericArgs {
    Span span;
    AxAstGenericArg *args;
};

struct AxAstWherePred {
    Span span;
    AxAstType *type;
    AxAstType *bounds; /* linked list of TypePaths */
    AxAstWherePred *next;
};

struct AxAstWhereClause {
    Span span;
    AxAstWherePred *preds;
};

struct AxAstParam {
    Span span;
    bool is_mut;
    StrId name; /* 0 if `_`, special StrId for `self` */
    AxAstType *type;
    AxAstParam *next;
};

struct AxAstFieldDecl {
    AxAstAttr *attrs;
    AxAstVis vis;
    Span span;
    StrId name;
    AxAstType *type;
    AxAstFieldDecl *next;
};

struct AxAstVariantDecl {
    AxAstAttr *attrs;
    Span span;
    StrId name;
    bool is_struct;
    union {
        AxAstType *tuple_types;
        AxAstFieldDecl *struct_fields;
    };
    AxAstVariantDecl *next;
};

struct AxAstUseTree {
    Span span;
    AxAstDottedName path;
    StrId alias;
    AxAstUseTree *subtrees; /* for { A, B } */
    AxAstUseTree *next;
};

struct AxAstItem {
    AxAstItemKind kind;
    Span span;
    AxAstAttr *attrs;
    AxAstVis vis;
    AxAstItem *next;
    union {
        struct {
            AxAstDottedName path;
        } module;
        struct {
            AxAstUseTree *tree;
        } use;
        struct {
            bool is_async;
            bool is_comptime;
            bool is_unsafe;
            StrId abi;
            StrId name;
            AxAstGenericParams *generic_params;
            AxAstParam *params;
            AxAstType *ret_type;
            AxAstWhereClause *where_clause;
            AxAstBlock *body;
        } fn;
        struct {
            StrId name;
            AxAstGenericParams *generic_params;
            AxAstWhereClause *where_clause;
            bool is_tuple;
            union {
                AxAstFieldDecl *struct_fields;
                AxAstType *tuple_types;
            };
        } struct_decl;
        struct {
            StrId name;
            AxAstGenericParams *generic_params;
            AxAstWhereClause *where_clause;
            AxAstVariantDecl *variants;
        } enum_decl;
        struct {
            StrId name;
            AxAstGenericParams *generic_params;
            AxAstType *supertraits;
            AxAstWhereClause *where_clause;
            AxAstItem *members;
        } trait;
        struct {
            AxAstGenericParams *generic_params;
            AxAstType *trait_path;
            AxAstType *self_type;
            AxAstWhereClause *where_clause;
            AxAstItem *members;
        } impl;
        struct {
            StrId name;
            AxAstGenericParams *generic_params;
            AxAstType *type;
        } type_alias;
        struct {
            StrId name;
            AxAstType *type;
            AxAstExpr *expr;
        } const_decl;
        struct {
            bool is_unsafe;
            bool is_mut;
            StrId name;
            AxAstType *type;
            AxAstExpr *expr; /* NULL if overlay */
        } static_decl;
        struct {
            StrId abi;
            AxAstItem *members;
        } extern_block;
    };
};

typedef struct AxAst {
    AxAstItem *items;
} AxAst;

#endif /* AX_SYNTAX_AST_H */
