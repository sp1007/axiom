#ifndef AX_DRIVER_BUILD_NATIVE_DATA_SYMS_H
#define AX_DRIVER_BUILD_NATIVE_DATA_SYMS_H

/*
 * Compiler-generated object-local data symbols (ADR-0035 section 1).
 *
 * One code path shared by `axiom0 build`, `build --emit=obj` and `inspect --emit=obj`, so the
 * three can never disagree on naming, linkage, padding or relocation targets.
 */

#include "objmodel/objmodel.h"
#include "target/x64/mir/mi.h"
#include <stdint.h>

/*
 * Emits the string literals of one function body into `.rdata`: bytes, a NUL terminator and zero
 * padding to 8 bytes, one STATIC (AX_SYM_LOCAL) symbol `.Lstr.<fn_ordinal>.<sym_id>` per literal,
 * defined exactly once. Every `lea reg, <string>` of `mi_body` is rewritten to reference that
 * symbol's own id, so the COFF relocation targets the symbol index (no undefined twin).
 * `fn_ordinal` is the 0-based position of the body in the object's emission order.
 */
void ax_emit_fn_string_data(ax_objmodel_t *obj, ax_section_id_t rdata_sec_id,
                            AxX64MIBody *mi_body, uint32_t fn_ordinal);

/* Formats the panic-message symbol name `.Lpanic.<n>` into `buf` (n = per-object counter). */
void ax_panic_sym_name(char *buf, size_t cap, uint32_t n);

#endif /* AX_DRIVER_BUILD_NATIVE_DATA_SYMS_H */
