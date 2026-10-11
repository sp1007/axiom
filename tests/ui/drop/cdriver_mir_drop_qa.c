#define AX_UNIT_STANDALONE
#include "unit.h"
#include "mir/mir.h"
#include "mir/drop/drop.h"
#include <string.h>
#include "types/types.h"

static void test_qa_drop_multi_basic_blocks(void) {
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
        "    goto -> bb1;\n"
        "  }\n"
        "  bb1: {\n"
        "    drop(_1) -> [return: bb2, unwind: bb3];\n"
        "  }\n"
        "  bb2: {\n"
        "    return;\n"
        "  }\n"
        "  bb3: {\n"
        "    unreachable;\n"
        "  }\n"
        "}\n";

    AxMirBody *body = ax_mir_parse(text, &interner, &arena);
    AX_CHECK(body != NULL);
    AX_CHECK_EQ_INT(body->bb_count, 4);

    // bb0 checks
    AX_CHECK_EQ_INT(body->bbs[0].stmt_count, 1);
    AX_CHECK_EQ_INT(body->bbs[0].stmts[0].kind, AX_MIR_STMT_DROP);
    AX_CHECK_EQ_INT(body->bbs[0].stmts[0].drop.local.v, 1);
    AX_CHECK_EQ_INT(body->bbs[0].terminator.kind, AX_MIR_TERM_GOTO);
    AX_CHECK_EQ_INT(body->bbs[0].terminator.goto_target.v, 1);

    // bb1 checks
    AX_CHECK_EQ_INT(body->bbs[1].stmt_count, 0);
    AX_CHECK_EQ_INT(body->bbs[1].terminator.kind, AX_MIR_TERM_DROP);
    AX_CHECK_EQ_INT(body->bbs[1].terminator.drop.place.local.v, 1);
    AX_CHECK_EQ_INT(body->bbs[1].terminator.drop.target.v, 2);
    AX_CHECK_EQ_INT(body->bbs[1].terminator.drop.unwind.v, 3);

    // bb2 and bb3 checks
    AX_CHECK_EQ_INT(body->bbs[2].terminator.kind, AX_MIR_TERM_RETURN);
    AX_CHECK_EQ_INT(body->bbs[3].terminator.kind, AX_MIR_TERM_UNREACHABLE);

    // Test print round-trip
    FILE *f = tmpfile();
    AX_CHECK(f != NULL);
    ax_mir_print(f, body);
    rewind(f);
    char buf[2048] = {0};
    fread(buf, 1, sizeof(buf) - 1, f);
    fclose(f);

    AX_CHECK(strstr(buf, "Drop(_1);") != NULL);
    AX_CHECK(strstr(buf, "drop(_1) -> [return: bb2, unwind: bb3];") != NULL);

    ax_type_interner_free(&interner);
    ax_arena_destroy(&arena);
}

static void test_qa_drop_with_projections(void) {
    AxArena arena = {0};
    ax_arena_init(&arena, 4096);
    TypeInterner interner = {0};
    ax_type_interner_init(&interner);

    const char *text =
        "mir_body {\n"
        "    let mut _0: type#0;\n"
        "    let mut _1: type#1;\n"
        "  bb0: {\n"
        "    Drop((_1).2);\n"
        "    Drop((*_1));\n"
        "    drop((_1).0) -> [return: bb0, unwind: bb0];\n"
        "  }\n"
        "}\n";

    AxMirBody *body = ax_mir_parse(text, &interner, &arena);
    AX_CHECK(body != NULL);
    AX_CHECK_EQ_INT(body->bb_count, 1);
    AX_CHECK_EQ_INT(body->bbs[0].stmt_count, 2);

    // Stmt 0: Drop((_1).2)
    AX_CHECK_EQ_INT(body->bbs[0].stmts[0].kind, AX_MIR_STMT_DROP);
    AX_CHECK_EQ_INT(body->bbs[0].stmts[0].drop.local.v, 1);
    AX_CHECK_EQ_INT(body->bbs[0].stmts[0].drop.proj_count, 1);
    AX_CHECK_EQ_INT(body->bbs[0].stmts[0].drop.projs[0].kind, AX_MIR_PROJ_FIELD);
    AX_CHECK_EQ_INT(body->bbs[0].stmts[0].drop.projs[0].field_idx, 2);

    // Stmt 1: Drop((*_1))
    AX_CHECK_EQ_INT(body->bbs[0].stmts[1].kind, AX_MIR_STMT_DROP);
    AX_CHECK_EQ_INT(body->bbs[0].stmts[1].drop.local.v, 1);
    AX_CHECK_EQ_INT(body->bbs[0].stmts[1].drop.proj_count, 1);
    AX_CHECK_EQ_INT(body->bbs[0].stmts[1].drop.projs[0].kind, AX_MIR_PROJ_DEREF);

    // Terminator: drop((_1).0)
    AX_CHECK_EQ_INT(body->bbs[0].terminator.kind, AX_MIR_TERM_DROP);
    AX_CHECK_EQ_INT(body->bbs[0].terminator.drop.place.local.v, 1);
    AX_CHECK_EQ_INT(body->bbs[0].terminator.drop.place.proj_count, 1);
    AX_CHECK_EQ_INT(body->bbs[0].terminator.drop.place.projs[0].kind, AX_MIR_PROJ_FIELD);
    AX_CHECK_EQ_INT(body->bbs[0].terminator.drop.place.projs[0].field_idx, 0);

    // Verify print output contains the projected drop place syntax
    FILE *f = tmpfile();
    AX_CHECK(f != NULL);
    ax_mir_print(f, body);
    rewind(f);
    char buf[2048] = {0};
    fread(buf, 1, sizeof(buf) - 1, f);
    fclose(f);

    AX_CHECK(strstr(buf, "Drop((_1).2);") != NULL);
    AX_CHECK(strstr(buf, "Drop((*_1));") != NULL);
    AX_CHECK(strstr(buf, "drop((_1).0) -> [return: bb0, unwind: bb0];") != NULL);

    ax_type_interner_free(&interner);
    ax_arena_destroy(&arena);
}

int main(void) {
    test_qa_drop_multi_basic_blocks();
    test_qa_drop_with_projections();
    return ax_unit_exit_code();
}
