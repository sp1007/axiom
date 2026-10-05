#include <stdint.h>

#include "kernel/vec.h"
#include "unit.h"

AX_DEFINE_VEC(KtU32Vec, uint32_t);

typedef struct KtPair {
    int a;
    double b;
} KtPair;
AX_DEFINE_VEC(KtPairVec, KtPair);

AX_TEST(kernel_vec_push_get_growth) {
    KtU32Vec v = KtU32Vec_new();
    AX_CHECK_EQ_INT(KtU32Vec_len(&v), 0);
    for (uint32_t i = 0; i < 10000; ++i) {
        AX_CHECK_EQ_INT(KtU32Vec_push(&v, i * 3u), i);
    }
    AX_CHECK_EQ_INT(v.len, 10000);
    AX_CHECK(v.cap >= 10000);
    int ok = 1;
    for (uint32_t i = 0; i < 10000; ++i) {
        ok &= KtU32Vec_get(&v, i) == i * 3u;
    }
    AX_CHECK(ok);
    KtU32Vec_free(&v);
    AX_CHECK(v.data == NULL && v.len == 0 && v.cap == 0);
}

AX_TEST(kernel_vec_capacity_policy) {
    KtU32Vec v;
    KtU32Vec_init(&v);
    KtU32Vec_push(&v, 1);
    AX_CHECK_EQ_INT(v.cap, 8); /* minimum capacity */
    for (uint32_t i = 0; i < 8; ++i) {
        KtU32Vec_push(&v, i);
    }
    AX_CHECK_EQ_INT(v.cap, 16); /* doubles */
    KtU32Vec_reserve(&v, 100);
    AX_CHECK(v.cap >= 109);
    size_t cap = v.cap;
    KtU32Vec_reserve(&v, 1); /* no-op when it fits */
    AX_CHECK_EQ_INT(v.cap, cap);
    KtU32Vec_free(&v);
}

AX_TEST(kernel_vec_pop_set_truncate_remove) {
    KtU32Vec v = KtU32Vec_new();
    for (uint32_t i = 0; i < 6; ++i) {
        KtU32Vec_push(&v, i);
    }
    AX_CHECK_EQ_INT(KtU32Vec_pop(&v), 5);
    AX_CHECK_EQ_INT(*KtU32Vec_last(&v), 4);
    KtU32Vec_set(&v, 0, 100);
    *KtU32Vec_at(&v, 1) = 101;
    KtU32Vec_remove_ordered(&v, 2); /* 100 101 3 4 */
    AX_CHECK_EQ_INT(v.len, 4);
    AX_CHECK_EQ_INT(KtU32Vec_get(&v, 0), 100);
    AX_CHECK_EQ_INT(KtU32Vec_get(&v, 1), 101);
    AX_CHECK_EQ_INT(KtU32Vec_get(&v, 2), 3);
    AX_CHECK_EQ_INT(KtU32Vec_get(&v, 3), 4);
    KtU32Vec_remove_ordered(&v, 3);
    AX_CHECK_EQ_INT(v.len, 3);
    KtU32Vec_truncate(&v, 1);
    AX_CHECK_EQ_INT(v.len, 1);
    KtU32Vec_clear(&v);
    AX_CHECK_EQ_INT(v.len, 0);
    KtU32Vec_push(&v, 9); /* usable after clear */
    AX_CHECK_EQ_INT(KtU32Vec_get(&v, 0), 9);
    KtU32Vec_free(&v);
}

AX_TEST(kernel_vec_struct_elements) {
    KtPairVec v = KtPairVec_new();
    for (int i = 0; i < 100; ++i) {
        KtPair p = {i, i * 0.5};
        KtPairVec_push(&v, p);
    }
    AX_CHECK_EQ_INT(KtPairVec_get(&v, 77).a, 77);
    AX_CHECK(KtPairVec_get(&v, 77).b == 38.5);
    KtPairVec_free(&v);
}
