#include <signal.h>
#include <stdio.h>
#include <stdlib.h>
#include "mir/build/build.h"
#include "hir/hir.h"
static void on_abort(int sig) { (void)sig; _Exit(3); }
int main(void) {
    if (!getenv("AXIOM_TEST_ICE")) return 0;
    signal(SIGABRT, on_abort);
    AxArena arena = {0};
    ax_arena_init(&arena, 4096);
    AxThir thir = {0};
    ax_type_interner_init(&thir.interner);
    AxHirExpr bad_expr = {0};
    bad_expr.kind = (AxHirExprKind)999;
    AxHirStmt stmt = {0};
    stmt.kind = AX_HIR_STMT_EXPR;
    stmt.expr_stmt.expr = &bad_expr;
    AxHirBlock block = {0};
    block.stmts = &stmt;
    AxHirItem item = {0};
    item.kind = AX_HIR_ITEM_FN;
    item.fn.body = &block;
    ax_mir_build(&item, &thir, &arena);
    return 0;
}
