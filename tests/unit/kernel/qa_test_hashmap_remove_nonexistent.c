#include <stdint.h>
#include "kernel/hashmap.h"
#include "unit.h"

AX_DEFINE_HASHMAP(KtRemoveMap, uint32_t, int, ax_key_hash_u32, ax_key_eq_u32);

AX_TEST(kernel_hashmap_remove_nonexistent) {
    KtRemoveMap m;
    KtRemoveMap_init(&m);
    
    int val = -1;
    bool result = KtRemoveMap_remove(&m, 42, &val);
    AX_CHECK(!result);
    
    KtRemoveMap_insert(&m, 1, 100);
    result = KtRemoveMap_remove(&m, 42, &val);
    AX_CHECK(!result);
    
    result = KtRemoveMap_remove(&m, 1, &val);
    AX_CHECK(result);
    AX_CHECK_EQ_INT(val, 100);
    
    KtRemoveMap_free(&m);
}

