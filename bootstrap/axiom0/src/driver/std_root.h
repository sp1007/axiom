#ifndef AX_DRIVER_STD_ROOT_H
#define AX_DRIVER_STD_ROOT_H

#include <stdbool.h>

/* Discovers the std library root directory according to ADR-0006 §8:
 * 1. explicit_flag (--std-root <dir>)
 * 2. environment variable AXIOM_STD
 * 3. <exe dir>/../std
 * 4. <exe dir>/std
 * Returns the path (with forward slashes), or NULL if not found. */
const char *ax_find_std_root(const char *explicit_flag);

#endif /* AX_DRIVER_STD_ROOT_H */
