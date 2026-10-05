#ifndef AX_LINK_PE_LINKER_H
#define AX_LINK_PE_LINKER_H

#include "diag/diag.h"
#include <stdbool.h>
#include <stdint.h>
#include <stddef.h>

/**
 * Link one or more COFF object files into a PE32+ executable.
 * 
 * @param input_paths Array of input object file paths.
 * @param input_count Number of input paths.
 * @param output_path Output executable path.
 * @param stack_reserve Size of stack reserve (if 0, defaults to 0x100000).
 * @param diag Diagnostic sink.
 * @return true on success, false on failure.
 */
bool ax_pe_link(const char *const *input_paths, size_t input_count, const char *output_path, uint32_t stack_reserve, AxDiagSink *diag);

#endif /* AX_LINK_PE_LINKER_H */
