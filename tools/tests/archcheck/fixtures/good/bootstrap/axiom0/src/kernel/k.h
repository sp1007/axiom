#ifndef AX_KERNEL_K_H
#define AX_KERNEL_K_H

#include <stdint.h>
#include "k2.h"
#include "../kernel/k2.h"
#include "generated/not_a_layer.h"

/* #include "syntax/ast.h" is only a comment, and so is printf("x") here */
// exit(1); abort();

typedef struct { uint32_t v; } FileId;
typedef int (*KCallback)(int);
struct Forward;
enum { K_A, K_B };
extern int k_declared_elsewhere;
int k_prototype(int a, const char *b);
int k_array_size(char buf[sizeof(int)]);
_Static_assert(sizeof(int) >= 2, "int");

static const int k_table[] = { 1, 2, 3 };
static const char *const k_names[] = { "printf(", "exit(", "// not a comment" };
static const char k_text[] = "abort() #include \"syntax/ast.h\"";
static int (*const k_fn)(int) = 0;
const struct Forward *const k_fwd = 0;

static inline int k_twice(int x) {
    static const int k_factor = 2;
    int snprintf_like = 0;
    return x * k_factor + snprintf_like;
}

struct Holder {
    int (*fn)(int);
    int values[4];
};

static int k_snprintf(char *b, int n) { return snprintf(b, (size_t)n, "x"); }
static int k_ax_printf(void) { return ax_printf("x") + obj->exit(0) + obj.abort(); }

#endif
