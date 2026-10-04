#ifndef AX_TESTS_UNIT_UNIT_H
#define AX_TESTS_UNIT_UNIT_H

/* Tiny assertion header for C unit tests (axiom-c-stage0 / axiom-testing).
 *
 * Unit tests: put `AX_TEST(name) { ... }` in any .c file below tests/unit (the marker must start
 * the line). CMake discovers the markers at configure time and generates the main() of
 * `axiom0-unit`; nothing is registered by hand. Test names are global: use a module prefix
 * (`lex_empty_input`). A failed check records the failure and the test keeps running.
 *
 * Own-main tests: any file named cdriver_<name>.c below tests is built into its own executable
 * (also if it lives in tests/unit). It may define
 * AX_UNIT_STANDALONE before including this header to get the same checks, then returns
 * `ax_unit_exit_code()` from its main().
 */

#include <stdio.h>
#include <string.h>

#define AX_TEST(name) void axut_##name(void)

#define AX_CHECK(cond)                                                                            \
    do {                                                                                          \
        if (!(cond)) {                                                                            \
            ax_unit_failf(__FILE__, __LINE__, "check failed: %s", #cond);                         \
        }                                                                                         \
    } while (0)

#define AX_CHECK_EQ_INT(actual, expected)                                                         \
    do {                                                                                          \
        long long ax_a_ = (long long)(actual);                                                    \
        long long ax_e_ = (long long)(expected);                                                  \
        if (ax_a_ != ax_e_) {                                                                     \
            ax_unit_failf(__FILE__, __LINE__, "%s == %s: got %lld, expected %lld", #actual,       \
                          #expected, ax_a_, ax_e_);                                               \
        }                                                                                         \
    } while (0)

#define AX_CHECK_EQ_STR(actual, expected)                                                         \
    do {                                                                                          \
        const char *ax_a_ = (actual);                                                             \
        const char *ax_e_ = (expected);                                                           \
        if (ax_a_ == NULL || ax_e_ == NULL || strcmp(ax_a_, ax_e_) != 0) {                        \
            ax_unit_failf(__FILE__, __LINE__, "%s == %s: got \"%s\", expected \"%s\"", #actual,   \
                          #expected, ax_a_ ? ax_a_ : "(null)", ax_e_ ? ax_e_ : "(null)");        \
        }                                                                                         \
    } while (0)

#ifdef AX_UNIT_STANDALONE
#include <stdarg.h>

static int ax_unit_failures_;

static inline void ax_unit_failf(const char *file, int line, const char *fmt, ...) {
    va_list ap;
    ++ax_unit_failures_;
    fprintf(stdout, "  %s:%d: ", file, line);
    va_start(ap, fmt);
    vfprintf(stdout, fmt, ap);
    va_end(ap);
    fputc('\n', stdout);
}

static inline int ax_unit_exit_code(void) {
    return ax_unit_failures_ == 0 ? 0 : 1;
}
#else
void ax_unit_failf(const char *file, int line, const char *fmt, ...); /* in the generated main */
#endif

#endif /* AX_TESTS_UNIT_UNIT_H */
