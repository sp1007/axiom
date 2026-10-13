#ifndef AX_HIR_HIR_H
#define AX_HIR_HIR_H

#include "syntax/ast.h"
#include "kernel/id.h"
#include "resolve/resolve.h"

/* HIR (High-Level Intermediate Representation)
 * 
 * Defines the semantic data model after name resolution.
 * All paths are resolved to their corresponding AxSymbolId.
 * Postfix operations and compound assignments are desugared.
 */

typedef struct AxHirAttr AxHirAttr;
typedef struct AxHirAttrArg AxHirAttrArg;
typedef struct AxHirVis AxHirVis;
typedef struct AxHirGenericParams AxHirGenericParams;
typedef struct AxHirGenericParam AxHirGenericParam;
typedef struct AxHirGenericArgs AxHirGenericArgs;
typedef struct AxHirGenericArg AxHirGenericArg;
typedef struct AxHirWhereClause AxHirWhereClause;
typedef struct AxHirWherePred AxHirWherePred;
typedef struct AxHirBlock AxHirBlock;
typedef struct AxHirItem AxHirItem;
typedef struct AxHirStmt AxHirStmt;
typedef struct AxHirExpr AxHirExpr;
typedef struct AxHirPat AxHirPat;
typedef struct AxHirType AxHirType;
typedef struct AxHirMatchArm AxHirMatchArm;
typedef struct AxHirFieldInit AxHirFieldInit;
typedef struct AxHirFieldDecl AxHirFieldDecl;
typedef struct AxHirVariantDecl AxHirVariantDecl;
typedef struct AxHirParam AxHirParam;
typedef struct AxHirUseTree AxHirUseTree;

typedef struct AxHirPath {
    Span span;
    AxSymbolId symbol;
    StrId name;
    AxHirGenericArgs *generic_args;
} AxHirPath;

typedef enum AxHirVisKind {
    AX_HIR_VIS_PRIVATE,
    AX_HIR_VIS_PUB,
    AX_HIR_VIS_PUB_PACKAGE,
    AX_HIR_VIS_PUB_MODULE,
} AxHirVisKind;

struct AxHirVis {
    Span span;
    AxHirVisKind kind;
};

struct AxHirAttrArg {
    Span span;
    StrId name;
    AxHirExpr *expr;
    AxHirAttrArg *next;
};

struct AxHirAttr {
    Span span;
    StrId name;
    AxHirAttrArg *args;
    AxHirAttr *next;
};

/* Types */

typedef enum AxHirTypeKind {
    AX_HIR_TYPE_ERROR,
    AX_HIR_TYPE_PATH,
    AX_HIR_TYPE_TUPLE,
    AX_HIR_TYPE_ARRAY,
    AX_HIR_TYPE_SLICE,
    AX_HIR_TYPE_VIEW,
    AX_HIR_TYPE_PTR,
    AX_HIR_TYPE_FN,
    AX_HIR_TYPE_DYN,
} AxHirTypeKind;

struct AxHirType {
    AxHirTypeKind kind;
    Span span;
    AxHirType *next;
    union {
        struct {
            AxHirPath path;
        } path;
        struct {
            AxHirType *elem_types;
        } tuple;
        struct {
            AxHirExpr *count;
            AxHirType *elem;
        } array;
        struct {
            AxHirType *elem;
        } slice;
        struct {
            bool is_mut;
            AxHirType *elem;
        } view;
        struct {
            bool is_mut;
            AxHirType *elem;
        } ptr;
        struct {
            bool is_unsafe;
            StrId abi;
            AxHirType *param_types;
            AxHirType *ret_type;
        } fn;
        struct {
            AxHirType *bounds;
        } dyn;
    };
};

/* Patterns */

typedef enum AxHirPatKind {
    AX_HIR_PAT_ERROR,
    AX_HIR_PAT_WILDCARD,
    AX_HIR_PAT_RANGE,
    AX_HIR_PAT_LITERAL,
    AX_HIR_PAT_BINDING,
    AX_HIR_PAT_PATH,
    AX_HIR_PAT_TUPLE,
    AX_HIR_PAT_OR,
    AX_HIR_PAT_STRUCT,
} AxHirPatKind;

typedef struct AxHirPatField {
    Span span;
    StrId name;
    AxHirPat *pat;
    struct AxHirPatField *next;
} AxHirPatField;

struct AxHirPat {
    AxHirPatKind kind;
    Span span;
    AxHirPat *next;
    union {
        struct {
            bool is_inclusive;
            AxHirPat *start;
            AxHirPat *end;
        } range;
        struct {
            AxToken tok;
            bool is_negated;
        } literal;
        struct {
            bool is_mut;
            AxSymbolId symbol;
        } binding;
        struct {
            AxHirPath path;
            AxHirPat *payload;
        } path;
        struct {
            AxHirPat *elems;
        } tuple;
        struct {
            AxHirPat *pats;
        } or_pat;
        struct {
            AxHirPath path;
            AxHirPatField *fields;
            bool has_rest;
        } struct_pat;
    };
};

/* Expressions */

typedef enum AxHirExprKind {
    AX_HIR_EXPR_ERROR,
    AX_HIR_EXPR_LITERAL,
    AX_HIR_EXPR_PATH,
    AX_HIR_EXPR_TUPLE,
    AX_HIR_EXPR_ARRAY,
    AX_HIR_EXPR_STRUCT,
    AX_HIR_EXPR_BLOCK,
    AX_HIR_EXPR_IF,
    AX_HIR_EXPR_MATCH,
    AX_HIR_EXPR_LOOP,
    AX_HIR_EXPR_WHILE,
    AX_HIR_EXPR_FOR,
    AX_HIR_EXPR_UNSAFE,
    AX_HIR_EXPR_VIEW,
    AX_HIR_EXPR_COMPTIME,
    AX_HIR_EXPR_JUMP,
    AX_HIR_EXPR_CLOSURE,
    AX_HIR_EXPR_RANGE,
    AX_HIR_EXPR_BINARY,
    AX_HIR_EXPR_UNARY,
    AX_HIR_EXPR_CAST,
    
    // Postfix desugared
    AX_HIR_EXPR_FIELD,
    AX_HIR_EXPR_TUPLE_INDEX,
    AX_HIR_EXPR_CALL,
    AX_HIR_EXPR_METHOD_CALL,
    AX_HIR_EXPR_INDEX,
    AX_HIR_EXPR_TRY,
    AX_HIR_EXPR_AWAIT,
} AxHirExprKind;

struct AxHirFieldInit {
    Span span;
    StrId name;
    AxHirExpr *expr;
    AxHirFieldInit *next;
};

struct AxHirMatchArm {
    Span span;
    AxHirPat *pat;
    AxHirExpr *guard;
    AxHirExpr *body;
    AxHirMatchArm *next;
};

struct AxHirBlock {
    Span span;
    AxHirStmt *stmts;
};

struct AxHirExpr {
    AxHirExprKind kind;
    Span span;
    AxHirExpr *next;
    union {
        AxToken literal;
        struct {
            AxHirPath path;
        } path;
        struct {
            AxHirExpr *elems;
        } tuple;
        struct {
            AxHirExpr *elems;
            AxHirExpr *count;
        } array;
        struct {
            AxHirPath path;
            AxHirFieldInit *fields;
        } struct_lit;
        struct {
            AxHirBlock block;
        } block;
        struct {
            AxHirPat *let_pat;
            AxHirExpr *cond;
            AxHirBlock block;
            AxHirExpr *else_branch; /* Always an AX_HIR_EXPR_BLOCK if desugared else-if, or NULL */
        } if_expr;
        struct {
            AxHirExpr *expr;
            AxHirMatchArm *arms;
        } match;
        struct {
            StrId label;
            AxHirBlock block;
        } loop;
        struct {
            StrId label;
            AxHirPat *let_pat;
            AxHirExpr *cond;
            AxHirBlock block;
        } while_expr;
        struct {
            StrId label;
            AxHirPat *pat;
            AxHirExpr *iter;
            AxHirBlock block;
        } for_expr;
        struct {
            AxHirBlock block;
        } unsafe_block;
        struct {
            bool is_mut;
            AxHirExpr *expr;
        } view;
        struct {
            AxHirBlock block;
        } comptime;
        struct {
            AxAstJumpKind jump_kind;
            StrId label;
            AxHirExpr *expr;
        } jump;
        struct {
            AxHirParam *params;
            AxHirType *ret_type;
            AxHirExpr *body;
        } closure;
        struct {
            bool is_inclusive;
            AxHirExpr *start;
            AxHirExpr *end;
        } range;
        struct {
            AxAstBinOp op;
            AxHirExpr *left;
            AxHirExpr *right;
        } binary;
        struct {
            AxAstUnOp op;
            AxHirExpr *expr;
        } unary;
        struct {
            AxHirExpr *expr;
            AxHirType *type;
        } cast;
        
        struct {
            AxHirExpr *base;
            StrId name;
            AxHirGenericArgs *generic_args;
        } field;
        struct {
            AxHirExpr *base;
            uint32_t tuple_index;
        } tuple_index;
        struct {
            AxHirExpr *callee;
            AxHirExpr *args;
        } call;
        struct {
            AxHirExpr *receiver;
            StrId method_name;
            AxHirGenericArgs *generic_args;
            AxHirExpr *args;
        } method_call;
        struct {
            AxHirExpr *base;
            AxHirExpr *arg;
        } index;
        struct {
            AxHirExpr *expr;
            bool is_opt;
            uint32_t payload_idx;
            uint32_t err_idx;
        } try_expr;
        struct {
            AxHirExpr *expr;
        } await_expr;
    };
};

/* Statements */

typedef enum AxHirStmtKind {
    AX_HIR_STMT_ERROR,
    AX_HIR_STMT_LET,
    AX_HIR_STMT_ASSIGN, // compound assignment is desugared to simple assign + binary op
    AX_HIR_STMT_EXPR,
} AxHirStmtKind;

struct AxHirStmt {
    AxHirStmtKind kind;
    Span span;
    AxHirStmt *next;
    union {
        struct {
            AxHirPat *pat;
            AxHirType *type;
            AxHirExpr *expr;
            AxHirBlock *else_block;
        } let;
        struct {
            AxHirExpr *left;
            AxHirExpr *right;
        } assign;
        struct {
            AxHirExpr *expr;
            bool has_semi;
        } expr_stmt;
    };
};

/* Items */

typedef enum AxHirItemKind {
    AX_HIR_ITEM_ERROR,
    AX_HIR_ITEM_MODULE,
    AX_HIR_ITEM_USE,
    AX_HIR_ITEM_FN,
    AX_HIR_ITEM_STRUCT,
    AX_HIR_ITEM_ENUM,
    AX_HIR_ITEM_TRAIT,
    AX_HIR_ITEM_IMPL,
    AX_HIR_ITEM_TYPE_ALIAS,
    AX_HIR_ITEM_CONST,
    AX_HIR_ITEM_STATIC,
    AX_HIR_ITEM_EXTERN_BLOCK,
} AxHirItemKind;

struct AxHirGenericParam {
    Span span;
    StrId name;
    AxSymbolId symbol;
    AxHirType *bounds;
    AxHirGenericParam *next;
};

struct AxHirGenericParams {
    Span span;
    AxHirGenericParam *params;
};

struct AxHirGenericArg {
    Span span;
    StrId name;
    AxHirType *type;
    AxHirGenericArg *next;
};

struct AxHirGenericArgs {
    Span span;
    AxHirGenericArg *args;
};

struct AxHirWherePred {
    Span span;
    AxHirType *type;
    AxHirType *bounds;
    AxHirWherePred *next;
};

struct AxHirWhereClause {
    Span span;
    AxHirWherePred *preds;
};

struct AxHirParam {
    Span span;
    bool is_mut;
    StrId name;
    AxSymbolId symbol;
    AxHirType *type;
    AxHirParam *next;
};

struct AxHirFieldDecl {
    AxHirAttr *attrs;
    AxHirVis vis;
    Span span;
    StrId name;
    AxHirType *type;
    AxHirFieldDecl *next;
};

struct AxHirVariantDecl {
    AxHirAttr *attrs;
    Span span;
    StrId name;
    AxSymbolId symbol;
    bool is_struct;
    union {
        AxHirType *tuple_types;
        AxHirFieldDecl *struct_fields;
    };
    AxHirVariantDecl *next;
};

struct AxHirUseTree {
    Span span;
    AxAstDottedName path; // Use trees are not fully lowered to symbols like other paths
    StrId alias;
    AxHirUseTree *subtrees;
    AxHirUseTree *next;
};

struct AxHirItem {
    AxHirItemKind kind;
    Span span;
    AxHirAttr *attrs;
    AxHirVis vis;
    AxHirItem *next;
    AxAstDottedName module_path;
    union {
        struct {
            AxAstDottedName path;
        } module;
        struct {
            AxHirUseTree *tree;
        } use;
        struct {
            bool is_async;
            bool is_comptime;
            bool is_unsafe;
            StrId abi;
            StrId name;
            AxSymbolId symbol;
            AxHirGenericParams *generic_params;
            AxHirParam *params;
            AxHirType *ret_type;
            AxHirWhereClause *where_clause;
            AxHirBlock *body;
        } fn;
        struct {
            StrId name;
            AxSymbolId symbol;
            AxHirGenericParams *generic_params;
            AxHirWhereClause *where_clause;
            bool is_tuple;
            union {
                AxHirFieldDecl *struct_fields;
                AxHirType *tuple_types;
            };
        } struct_decl;
        struct {
            StrId name;
            AxSymbolId symbol;
            AxHirGenericParams *generic_params;
            AxHirWhereClause *where_clause;
            AxHirVariantDecl *variants;
        } enum_decl;
        struct {
            StrId name;
            AxSymbolId symbol;
            AxHirGenericParams *generic_params;
            AxHirType *supertraits;
            AxHirWhereClause *where_clause;
            AxHirItem *members;
        } trait;
        struct {
            AxHirGenericParams *generic_params;
            AxHirType *trait_path;
            AxHirType *self_type;
            AxHirWhereClause *where_clause;
            AxHirItem *members;
        } impl;
        struct {
            StrId name;
            AxSymbolId symbol;
            AxHirGenericParams *generic_params;
            AxHirType *type;
        } type_alias;
        struct {
            StrId name;
            AxSymbolId symbol;
            AxHirType *type;
            AxHirExpr *expr;
        } const_decl;
        struct {
            bool is_unsafe;
            bool is_mut;
            StrId name;
            AxHirType *type;
            AxHirExpr *expr;
        } static_decl;
        struct {
            StrId abi;
            AxHirItem *members;
        } extern_block;
    };
};

typedef struct AxHir {
    AxHirItem *items;
} AxHir;

#endif /* AX_HIR_HIR_H */
