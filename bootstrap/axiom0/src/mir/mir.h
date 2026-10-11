#ifndef AX_MIR_MIR_H
#define AX_MIR_MIR_H

#include "kernel/kernel.h"
#include "kernel/arena.h"
#include "kernel/id.h"
#include "types/types.h"
#include "hir/hir.h"
#include <stdio.h>

AX_DEFINE_ID(AxMirLocalId);
AX_DEFINE_ID(AxMirBbId);

typedef Span AxLocation;

typedef enum AxMirRegion {
    AX_MIR_REGION_UNKNOWN,
    AX_MIR_REGION_SAME,
    AX_MIR_REGION_DISJOINT,
    AX_MIR_REGION_CONTAINS,
    AX_MIR_REGION_OVERLAPS,
} AxMirRegion;

typedef enum AxMirView {
    AX_MIR_VIEW_UNKNOWN,
    AX_MIR_VIEW_READ,
    AX_MIR_VIEW_MUT,
} AxMirView;

typedef enum AxMirLocalKind {
    AX_MIR_LOCAL_RETURN,
    AX_MIR_LOCAL_USER,
    AX_MIR_LOCAL_TEMP,
    AX_MIR_LOCAL_ARG,
} AxMirLocalKind;

typedef struct AxMirLocalDecl {
    AxMirLocalKind kind;
    TypeId ty;
    bool mut;
    AxLocation location;
} AxMirLocalDecl;

typedef enum AxMirProjKind {
    AX_MIR_PROJ_DEREF,
    AX_MIR_PROJ_FIELD,
    AX_MIR_PROJ_INDEX,
    AX_MIR_PROJ_DOWNCAST,
    AX_MIR_PROJ_SUB_SLICE,
} AxMirProjKind;

typedef struct AxMirProjection {
    AxMirProjKind kind;
    union {
        uint32_t field_idx;
        AxMirLocalId index_local;
        uint32_t variant_idx;
        struct {
            AxMirLocalId from_local;
            AxMirLocalId to_local;
            bool has_from;
            bool has_to;
        } sub_slice;
    };
} AxMirProjection;

typedef struct AxMirPlace {
    AxMirLocalId local;
    AxMirProjection *projs;
    size_t proj_count;
    AxMirRegion region;
    AxMirView view;
    uint32_t drop_flag;
} AxMirPlace;

typedef enum AxMirBinOp {
    AX_MIR_BINOP_ADD, AX_MIR_BINOP_SUB, AX_MIR_BINOP_MUL, AX_MIR_BINOP_DIV, AX_MIR_BINOP_REM,
    AX_MIR_BINOP_BIT_XOR, AX_MIR_BINOP_BIT_AND, AX_MIR_BINOP_BIT_OR,
    AX_MIR_BINOP_SHL, AX_MIR_BINOP_SHR,
    AX_MIR_BINOP_EQ, AX_MIR_BINOP_LT, AX_MIR_BINOP_LE,
    AX_MIR_BINOP_NE, AX_MIR_BINOP_GE, AX_MIR_BINOP_GT,
    AX_MIR_BINOP_OFFSET
} AxMirBinOp;

typedef enum AxMirUnOp {
    AX_MIR_UNOP_NOT,
    AX_MIR_UNOP_NEG,
    AX_MIR_UNOP_BITNOT
} AxMirUnOp;

typedef enum AxMirOperandKind {
    AX_MIR_OP_COPY,
    AX_MIR_OP_MOVE,
    AX_MIR_OP_CONST,
} AxMirOperandKind;

typedef enum AxMirConstKind {
    AX_MIR_CONST_INT,
    AX_MIR_CONST_STR,
} AxMirConstKind;

typedef struct AxMirConst {
    TypeId ty;
    AxMirConstKind kind;
    union {
        uint64_t val; 
        struct {
            const uint8_t *bytes;
            size_t len;
        } str;
    };
} AxMirConst;

typedef struct AxMirOperand {
    AxMirOperandKind kind;
    AxMirRegion region;
    AxMirView view;
    uint32_t drop_flag;
    AxLocation location;
    union {
        AxMirPlace place;
        AxMirConst constant;
    };
} AxMirOperand;

typedef enum AxMirCastKind {
    AX_MIR_CAST_INT_TO_INT,
    AX_MIR_CAST_PTR_TO_PTR,
    AX_MIR_CAST_INT_TO_PTR,
    AX_MIR_CAST_PTR_TO_INT,
} AxMirCastKind;

typedef enum AxMirRvalueKind {
    AX_MIR_RVALUE_USE,
    AX_MIR_RVALUE_REPEAT,
    AX_MIR_RVALUE_REF,        
    AX_MIR_RVALUE_LEN,
    AX_MIR_RVALUE_CAST,
    AX_MIR_RVALUE_OVERFLOWS_BINARY_OP,
    AX_MIR_RVALUE_BINARY_OP,
    AX_MIR_RVALUE_UNARY_OP,
    AX_MIR_RVALUE_DISCRIMINANT,
    AX_MIR_RVALUE_AGGREGATE,
} AxMirRvalueKind;

typedef enum AxMirBorrowKind {
    AX_MIR_BORROW_SHARED,
    AX_MIR_BORROW_MUT,
} AxMirBorrowKind;

typedef struct AxMirRvalue {
    AxMirRvalueKind kind;
    union {
        AxMirOperand use; 
        struct {
            AxMirOperand op;
            AxMirOperand count;
        } repeat;
        struct {
            AxMirBorrowKind bk;
            AxMirPlace place;
        } ref;
        AxMirPlace len;
        struct {
            AxMirCastKind kind;
            AxMirOperand op;
            TypeId ty;
        } cast;
        struct {
            AxMirBinOp op;
            AxMirOperand lhs;
            AxMirOperand rhs;
        } binary_op;
        struct {
            AxMirUnOp op;
            AxMirOperand operand;
        } unary_op;
        AxMirPlace discriminant;
        struct {
            uint32_t variant_idx;
            AxMirOperand *operands;
            size_t operand_count;
        } aggregate;
    };
} AxMirRvalue;

typedef enum AxMirStmtKind {
    AX_MIR_STMT_ASSIGN,
    AX_MIR_STMT_STORAGE_LIVE,
    AX_MIR_STMT_STORAGE_DEAD,
    AX_MIR_STMT_DROP,
} AxMirStmtKind;

typedef struct AxMirStmt {
    AxMirStmtKind kind;
    AxLocation location;
    union {
        struct {
            AxMirPlace place;
            AxMirRvalue rvalue;
        } assign;
        AxMirLocalId storage_live;
        AxMirLocalId storage_dead;
        AxMirPlace drop;
    };
} AxMirStmt;

typedef enum AxMirTerminatorKind {
    AX_MIR_TERM_GOTO,
    AX_MIR_TERM_SWITCH_INT,
    AX_MIR_TERM_RETURN,
    AX_MIR_TERM_UNREACHABLE,
    AX_MIR_TERM_DROP,
    AX_MIR_TERM_CALL,
    AX_MIR_TERM_ASSERT,
} AxMirTerminatorKind;

typedef struct AxMirSwitchTarget {
    uint64_t value;
    AxMirBbId target;
} AxMirSwitchTarget;

typedef struct AxMirSwitchTargets {
    AxMirSwitchTarget *values;
    size_t count;
    AxMirBbId otherwise;
} AxMirSwitchTargets;

typedef struct AxMirTerminator {
    AxMirTerminatorKind kind;
    AxMirRegion region;
    AxMirView view;
    uint32_t drop_flag;
    AxLocation location;
    union {
        AxMirBbId goto_target;
        struct {
            AxMirOperand discr;
            AxMirSwitchTargets targets;
        } switch_int;
        struct {
            AxMirPlace place;
            AxMirBbId target;
            AxMirBbId unwind;
        } drop;
        struct {
            AxMirOperand func;
            AxMirOperand *args;
            size_t arg_count;
            AxMirPlace destination;
            AxMirBbId target;
            AxMirBbId unwind;
        } call;
        struct {
            AxMirOperand cond;
            bool expected;
            const char *msg;
            AxMirBbId target;
            AxMirBbId unwind;
        } assert;
    };
} AxMirTerminator;

typedef struct AxMirBb {
    AxMirStmt *stmts;
    size_t stmt_count;
    size_t stmt_cap;
    AxMirTerminator terminator;
} AxMirBb;

typedef struct AxMirBody {
    AxArena arena;
    AxMirLocalDecl *locals;
    size_t local_count;
    AxMirBb *bbs;
    size_t bb_count;
} AxMirBody;

AxMirBody *ax_mir_parse(const char *text, TypeInterner *interner, AxArena *arena);
void ax_mir_print(FILE *out, const AxMirBody *body);

#endif // AX_MIR_MIR_H
