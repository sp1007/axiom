#ifndef AX_INTERP_HOST_H
#define AX_INTERP_HOST_H

#include "interp/interp.h"
#include "kernel/str.h"
#include <stdint.h>
#include <stdbool.h>

typedef struct {
    uint32_t alloc_id;
    uint64_t base_addr;
    uint64_t size;
    uint32_t align;
    uint8_t *host_ptr;
    bool is_live;
    int call_depth;
} InterpAlloc;

typedef struct InterpHostState InterpHostState;
typedef struct InterpCtx InterpCtx;

struct InterpCtx {
    AxHirItem *main_fn;
    AxThir *thir;
    const AxHir *hir;
    StrInterner *interner;
    const AxResolveMap *rmap;
    const AxAst *ast;
    AxDiagSink *sink;
    int step_limit;
    int call_depth_limit;
    void *mir_map;
    
    int steps;
    int call_depth;
    
    AxArena arena;
    bool failed;
    int exit_code;
    const char **out_panic_msg;
    FILE *out;
    uint64_t dummy_buf;

    InterpAlloc *allocs;
    size_t alloc_count;
    size_t alloc_cap;
    uint64_t next_synth_addr;

    bool is_comptime;
    AxConstEvalResult comptime_result;
    Span current_span;

    InterpHostState *host;
};

typedef struct {
    uint64_t vals[32];
} AxInterpValue;

uint8_t *ax_interp_validate_raw_ptr(InterpCtx *ctx, uint64_t addr, uint64_t size, uint32_t align);
InterpAlloc *ax_interp_register_alloc(InterpCtx *ctx, uint8_t *host_ptr, uint64_t size, uint32_t align, int call_depth);
void ax_interp_report_ub(InterpCtx *ctx, const char *msg);
void ax_interp_panic(InterpCtx *ctx, const char *msg);

bool ax_interp_eval_host_intrinsic(InterpCtx *ctx, StrView name, const uint64_t *args, size_t arg_count, AxInterpValue *out_ret);
void ax_interp_host_init(InterpCtx *ctx, int argc, const char **argv);
void ax_interp_host_cleanup(InterpCtx *ctx);

#endif /* AX_INTERP_HOST_H */
