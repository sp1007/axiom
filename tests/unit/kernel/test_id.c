#include "kernel/id.h"
#include "kernel/interner.h"
#include "unit.h"

/* INV-KERN-001: typed IDs. Distinctness of ID kinds is checked at compile time below (this file
 * would not compile if two kinds were the same type); the negative compile check — passing one kind
 * where another is expected is rejected — is tests/unit/kernel/id_mix_rejected.test. */

AX_DEFINE_ID(KtFileId);
AX_DEFINE_ID(KtModuleId);

typedef struct KtFile {
    int size;
    const char *name;
} KtFile;

AX_DEFINE_ID_TABLE(KtFileTable, KtFileId, KtFile);

#define KT_IS_FILE_ID(x) _Generic((x), KtFileId: 1, default: 0)
_Static_assert(KT_IS_FILE_ID((KtFileId){1}), "KtFileId is KtFileId");
_Static_assert(!KT_IS_FILE_ID((KtModuleId){1}), "KtModuleId must be a distinct type");
_Static_assert(!KT_IS_FILE_ID((StrId){1}), "StrId must be a distinct type");
_Static_assert(!KT_IS_FILE_ID((uint32_t)1), "an ID is not a plain integer");
_Static_assert(sizeof(KtFileId) == sizeof(uint32_t), "IDs are 32-bit handles");

AX_TEST(kernel_id_none_and_index) {
    KtFileId none = KtFileId_none();
    AX_CHECK(KtFileId_is_none(none));
    AX_CHECK(!KtFileId_is_some(none));
    AX_CHECK_EQ_INT(none.v, 0);
    KtFileId first = KtFileId_from_index(0);
    AX_CHECK_EQ_INT(first.v, 1);
    AX_CHECK(KtFileId_is_some(first));
    AX_CHECK_EQ_INT(KtFileId_index(first), 0);
    AX_CHECK_EQ_INT(KtFileId_index(KtFileId_from_index(41)), 41);
    AX_CHECK(KtFileId_eq(KtFileId_from_index(3), KtFileId_from_index(3)));
    AX_CHECK(!KtFileId_eq(KtFileId_from_index(3), none));
}

AX_TEST(kernel_id_table_push_get) {
    KtFileTable t;
    KtFileTable_init(&t);
    AX_CHECK(KtFileId_is_none(KtFileTable_first(&t)));
    AX_CHECK(!KtFileTable_contains(&t, KtFileId_none()));
    KtFile a = {10, "a.ax"};
    KtFile b = {20, "b.ax"};
    KtFileId ia = KtFileTable_push(&t, a);
    KtFileId ib = KtFileTable_push(&t, b);
    AX_CHECK_EQ_INT(ia.v, 1); /* first entry gets v = 1, never 0 */
    AX_CHECK_EQ_INT(ib.v, 2);
    AX_CHECK_EQ_INT(KtFileTable_len(&t), 2);
    AX_CHECK_EQ_INT(KtFileTable_get(&t, ia)->size, 10);
    AX_CHECK_EQ_STR(KtFileTable_get(&t, ib)->name, "b.ax");
    KtFileTable_get(&t, ia)->size = 11;
    AX_CHECK_EQ_INT(KtFileTable_get(&t, ia)->size, 11);
    AX_CHECK(KtFileTable_contains(&t, ib));
    AX_CHECK(!KtFileTable_contains(&t, KtFileId_from_index(2)));
    AX_CHECK(!KtFileTable_contains(&t, KtFileId_none()));
    KtFileTable_free(&t);
    AX_CHECK_EQ_INT(KtFileTable_len(&t), 0);
}

AX_TEST(kernel_id_table_growth_and_iteration) {
    KtFileTable t;
    KtFileTable_init(&t);
    for (int i = 0; i < 5000; ++i) {
        KtFile f = {i, "x"};
        KtFileId id = KtFileTable_push(&t, f);
        AX_CHECK_EQ_INT(id.v, i + 1);
    }
    int n = 0, ok = 1;
    for (KtFileId id = KtFileTable_first(&t); KtFileId_is_some(id); id = KtFileTable_after(&t, id)) {
        ok &= KtFileTable_get(&t, id)->size == n;
        ++n;
    }
    AX_CHECK(ok);
    AX_CHECK_EQ_INT(n, 5000);
    KtFileTable_free(&t);
}
