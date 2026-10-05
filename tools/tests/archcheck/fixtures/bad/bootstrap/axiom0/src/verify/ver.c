#include <stdio.h>
#include <stdlib.h>

static int counter = 0;
int shared_total;
static const char *names[] = { "a", "b" };
static void (*hook)(int) = 0;
static const int fine_table[] = { 1, 2, 3 };
static const char *const fine_names[] = { "a", "b" };

int next_id(void) {
    static int id = 0;
    static const int step = 1;
    id += step;
    return id;
}

void report(int code) {
    printf("code %d\n", code);
    fprintf(stderr, "bad %d\n", code);
    if (code < 0) {
        exit(1);
    }
    abort();
}

void allowed(void) {
    /* archcheck:allow(INV-LAYER-006): fixture, ICE-style abort */
    abort();
}

void no_reason(void) {
    abort(); /* archcheck:allow(INV-LAYER-006) */
}

void wrong_inv(void) {
    int x = 0; /* archcheck:allow(INV-LAYER-001): not honoured */
    (void)x;
}

void stream_last(FILE *out) {
    fputs("x", stdout);
    fwrite("x", 1, 1,
           stderr);
    fputs("x", out);
}
