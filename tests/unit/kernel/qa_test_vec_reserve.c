#include <stdint.h>

#include "kernel/vec.h"
#include "unit.h"

AX_DEFINE_VEC(KtU16Vec, uint16_t);

AX_TEST(kernel_vec_reserve_empty_large) {
    KtU16Vec v = KtU16Vec_new();
    
    /* Reserve a very large number on an empty vector */
    KtU16Vec_reserve(&v, 5000);
    AX_CHECK(v.cap >= 5000);
    AX_CHECK_EQ_INT(v.len, 0);

    /* Ensure we can push elements into it without reallocation */
    uint16_t *initial_data = v.data;
    for (uint32_t i = 0; i < 5000; ++i) {
        KtU16Vec_push(&v, (uint16_t)i);
    }
    
    AX_CHECK(v.data == initial_data); /* Should not have reallocated */
    AX_CHECK_EQ_INT(v.len, 5000);
    AX_CHECK_EQ_INT(KtU16Vec_get(&v, 4999), 4999);

    /* Pop down to zero and ensure reserve logic works on populated vec */
    KtU16Vec_clear(&v);
    KtU16Vec_reserve(&v, 10);
    /* Capacity shouldn't shrink */
    AX_CHECK(v.cap >= 5000);
    
    KtU16Vec_free(&v);
}
