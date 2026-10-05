#include "kernel/base.h"
#include "unit.h"

AX_TEST(kernel_base_xmalloc_zero) {
    void *p1 = ax_xmalloc(0);
    AX_CHECK(p1 != NULL);
    
    void *p2 = ax_xcalloc(0, 10);
    AX_CHECK(p2 != NULL);

    void *p3 = ax_xcalloc(10, 0);
    AX_CHECK(p3 != NULL);

    void *p4 = ax_xrealloc(NULL, 0);
    AX_CHECK(p4 != NULL);

    ax_xfree(p1);
    ax_xfree(p2);
    ax_xfree(p3);
    ax_xfree(p4);
}
