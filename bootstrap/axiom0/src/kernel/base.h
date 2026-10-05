#ifndef AX_KERNEL_BASE_H
#define AX_KERNEL_BASE_H

/* Kernel base: fixed-width types, internal-compiler-error reporting (AX_ICE / AX_ASSERT) and
 * checked heap allocation. Lowest layer of axiom0: includes only the C standard library.
 *
 * AX_ICE / AX_ASSERT are for broken compiler invariants only, never for user errors (those are
 * diagnostics, axiom-c-stage0). They print one banner line that starts with
 * "error: internal compiler error:" (recognised by tools/axtest.py, SPEC-03 AXS-SEM-082) plus the
 * source location, then call abort(). This is the only place where the kernel writes to stderr.
 * Assertions stay enabled in every build type. */

#include <stdarg.h>
#include <stdbool.h>
#include <stddef.h>
#include <stdint.h>

/* The few non-standard attributes axiom0 uses are wrapped here (axiom-c-stage0: no extensions in
 * portable code). Both expand to nothing on a compiler without them. */
#if defined(__GNUC__) || defined(__clang__)
#define AX_PRINTF_LIKE(fmt_index, first_arg) __attribute__((format(printf, fmt_index, first_arg)))
#define AX_MAYBE_UNUSED __attribute__((unused))
#else
#define AX_PRINTF_LIKE(fmt_index, first_arg)
#define AX_MAYBE_UNUSED
#endif

#define AX_ARRAY_LEN(a) (sizeof(a) / sizeof((a)[0]))

/* Report an internal compiler error at file:line and abort. Never returns. */
_Noreturn void ax_ice_fail(const char *file, int line, const char *fmt, ...) AX_PRINTF_LIKE(3, 4);
_Noreturn void ax_ice_failv(const char *file, int line, const char *fmt, va_list ap);

/* AX_ICE("format", args...) — unconditional internal compiler error. */
#define AX_ICE(...) ax_ice_fail(__FILE__, __LINE__, __VA_ARGS__)

/* AX_ASSERT(cond) — internal invariant; enabled in all builds. */
#define AX_ASSERT(cond)                                                                           \
    do {                                                                                          \
        if (!(cond)) {                                                                            \
            ax_ice_fail(__FILE__, __LINE__, "assertion failed: %s", #cond);                       \
        }                                                                                         \
    } while (0)

/* Checked heap allocation: out of memory and size overflow are internal compiler errors, so callers
 * never test for NULL. ax_xmalloc/ax_xrealloc of 0 bytes return a valid pointer. */
void *ax_xmalloc(size_t size);
void *ax_xcalloc(size_t count, size_t size);
void *ax_xrealloc(void *ptr, size_t size);
void ax_xfree(void *ptr);

/* a * b, or AX_ICE on overflow. */
size_t ax_mul_size(size_t a, size_t b);
/* a + b, or AX_ICE on overflow. */
size_t ax_add_size(size_t a, size_t b);

/* Grow an array so that it holds at least `needed` elements of `elem_size` bytes. Capacity policy
 * (deterministic): new_cap = max(needed, 2 * cap, 8). Returns the (possibly moved) array; *cap is
 * updated. Contents up to the old capacity are preserved; new bytes are zeroed. */
void *ax_grow_array(void *data, size_t *cap, size_t elem_size, size_t needed);

#endif /* AX_KERNEL_BASE_H */
