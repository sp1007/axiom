#include "interp/interp.h"
#include "link/link.h"
#include "types/types.h"
#include "syntax/ast.h"
#include "objmodel/om.h"

static int g_verbose = 0;

int main(void) {
    g_verbose = 1;
    printf("hello\n");
    exit(0);
}
