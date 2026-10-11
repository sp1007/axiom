#define AX_UNIT_STANDALONE
#include "unit.h"
#include "mir/mir.h"
#include "mir/drop/drop.h"
#include <string.h>
#include "types/types.h"

static void test_mir_drop_stmt_and_place(void) {
    AxMirProjection proj = { .kind = AX_MIR_PROJ_FIELD, .field_idx = 3 };
    AxMirStmt stmt;
    memset(&stmt, 0, sizeof(stmt));
    stmt.kind = AX_MIR_STMT_DROP;
    stmt.drop.local.v = 5;
    stmt.drop.proj_count = 1;
    stmt.drop.projs = &proj;

    AX_CHECK_EQ_INT(stmt.kind, AX_MIR_STMT_DROP);
    AX_CHECK_EQ_INT(stmt.drop.local.v, 5);
    AX_CHECK_EQ_INT(stmt.drop.proj_count, 1);
    AX_CHECK_EQ_INT(stmt.drop.projs[0].field_idx, 3);
}

static void test_mir_bb_stmt_cap(void) {
    AxMirBb bb;
    memset(&bb, 0, sizeof(bb));
    bb.stmt_cap = 64;
    bb.stmt_count = 1;
    AX_CHECK_EQ_INT(bb.stmt_cap, 64);
    AX_CHECK_EQ_INT(bb.stmt_count, 1);
}

static void test_mir_drop_terminator_and_flag(void) {
    AxMirTerminator term;
    memset(&term, 0, sizeof(term));
    term.kind = AX_MIR_TERM_DROP;
    term.drop_flag = 0xbeef;
    term.drop.place.local.v = 2;
    term.drop.place.proj_count = 0;
    term.drop.target.v = 10;
    term.drop.unwind.v = 11;

    AX_CHECK_EQ_INT(term.kind, AX_MIR_TERM_DROP);
    AX_CHECK_EQ_INT(term.drop_flag, 0xbeef);
    AX_CHECK_EQ_INT(term.drop.place.local.v, 2);
    AX_CHECK_EQ_INT(term.drop.target.v, 10);
    AX_CHECK_EQ_INT(term.drop.unwind.v, 11);
}

static void test_mir_drop_elaborate_stub(void) {
    AxMirBody body;
    memset(&body, 0, sizeof(body));
    ax_mir_drop_elaborate(&body, NULL, NULL, NULL, NULL, NULL);
    // Verified that stub does not crash or dereference NULL prematurely
    AX_CHECK(true);
}

static void test_mir_drop_parse_and_print(void) {
    AxArena arena = {0};
    ax_arena_init(&arena, 4096);
    TypeInterner interner = {0};
    ax_type_interner_init(&interner);
    
    const char *text = 
        "mir_body {\n"
        "    let mut _0: type#0;\n"
        "    let mut _1: type#1;\n"
        "  bb0: {\n"
        "    Drop(_1);\n"
        "    drop(_1) -> [return: bb0, unwind: bb0];\n"
        "  }\n"
        "}\n";
    
    AxMirBody *body = ax_mir_parse(text, &interner, &arena);
    AX_CHECK(body != NULL);
    AX_CHECK_EQ_INT(body->bb_count, 1);
    AX_CHECK_EQ_INT(body->bbs[0].stmt_count, 1);
    AX_CHECK_EQ_INT(body->bbs[0].stmts[0].kind, AX_MIR_STMT_DROP);
    AX_CHECK_EQ_INT(body->bbs[0].terminator.kind, AX_MIR_TERM_DROP);
    
    FILE *f = tmpfile();
    AX_CHECK(f != NULL);
    ax_mir_print(f, body);
    rewind(f);
    char buf[1024] = {0};
    fread(buf, 1, sizeof(buf) - 1, f);
    fclose(f);
    
    AX_CHECK(strstr(buf, "Drop(_1);") != NULL);
    AX_CHECK(strstr(buf, "drop(_1) -> [return: bb0, unwind: bb0];") != NULL);
    
    ax_type_interner_free(&interner);
    ax_arena_destroy(&arena);
}

int main(void) {
    test_mir_drop_stmt_and_place();
    test_mir_bb_stmt_cap();
    test_mir_drop_terminator_and_flag();
    test_mir_drop_elaborate_stub();
    test_mir_drop_parse_and_print();
    return ax_unit_exit_code();
}
