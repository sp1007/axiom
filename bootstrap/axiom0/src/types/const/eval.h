#ifndef AX_TYPES_CONST_EVAL_H
#define AX_TYPES_CONST_EVAL_H

#include "kernel/kernel.h"
#include "diag/diag.h"
#include "hir/hir.h"

#ifndef AX_TYPES_TYPES_H
/* When included standalone, declare TypeId */
AX_DEFINE_ID(TypeId);
#endif

typedef enum AxConstKind {
    AX_CONST_INT,       /* integer, bool (0 or 1), char */
    AX_CONST_STR,       /* string slice { bytes, len } */
    AX_CONST_AGGREGATE, /* struct, array, tuple: raw materialised bytes */
    AX_CONST_UNIT,
    AX_CONST_ERROR
} AxConstKind;

typedef struct AxConstValue {
    AxConstKind kind;
    TypeId ty;
    union {
        uint64_t int_val;
        struct {
            const uint8_t *bytes;
            size_t len;
        } str_val;
        struct {
            uint8_t *data;
            size_t size;
            size_t align;
            uint32_t alloc_id;
        } aggregate;
    };
} AxConstValue;

typedef struct AxConstLimits {
    int max_steps;
    int max_call_depth;
} AxConstLimits;

typedef struct AxConstEvalResult {
    bool ok;
    AxConstValue val;
    AxDiagCode err_code;
    Span err_span;
    const char *err_msg;
} AxConstEvalResult;

struct AxThir;

typedef AxConstEvalResult (*AxConstEvalFn)(
    void *ctx,
    struct AxThir *thir,
    const AxHirExpr *expr,
    TypeId expected_ty,
    AxConstLimits limits
);

typedef struct AxConstEvaluator {
    void *ctx;
    AxConstEvalFn eval_expr;
} AxConstEvaluator;

#endif /* AX_TYPES_CONST_EVAL_H */
