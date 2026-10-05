# T027 — PE32+ linker + kernel32 imports + CRT-free startup

## Report
Implemented the PE32+ linker in C for the `bootstrap/axiom0` compiler. It correctly merges COFF sections, registers and applies relocations, lays out a PE32+ executable, and creates the import directory for `kernel32.dll` to import `ExitProcess`.

Also implemented the `axiom_start` entry point code sequence to set up the stack, call `main`, and then call `ExitProcess` with the result. Tested the linker using a custom C driver that constructs a minimal `.obj` file using `objmodel` and verifies the linker's output produces the correct executable exit code (42), and handles the `--stack-reserve` custom allocation properly.

### Round 1 Fixes
- Replaced direct `malloc`/`free` calls in `linker.c` with `ax_xmalloc`/`ax_xfree` from `kernel/base.h` to fix the layer violation and add out-of-memory robustness.
- Added `AX_MAYBE_UNUSED` to `ax_diag_sink_*` functions in `tests/link/cdriver_pe.c` to fix unused parameter warnings.
- Preserved negative testing for undefined symbols in the C driver and the exec manifest `tests/link/link.test`.

### Round 2 Fixes
- Refactored linker state into `LinkerContext` context struct in `linker.c` instead of using file-scope mutable variables (`sections`, `globals`, `relocs`) to fix layer violation `[INV-LAYER-006]`.
- Implemented duplicate symbol detection (`AX_LINK_DUPLICATE_SYMBOL`) when merging object files.
- Added `#pragma pack(push, 1)` and `#pragma pack(pop)` in `pe_defs.h` for COFF structs (like `IMAGE_SYMBOL`) to fix parsing misalignment that caused identical duplicate symbols to go undetected due to 20-byte padded reads instead of 18-byte packed reads.

## Files changed
- bootstrap/axiom0/src/link/pe/linker.c
- bootstrap/axiom0/src/link/pe/linker.h
- bootstrap/axiom0/src/link/pe/pe_defs.h
- tests/link/cdriver_pe.c
- tests/link/fixtures/main42.obj
- tests/link/link.test
STATUS: COMPLETE round=2
