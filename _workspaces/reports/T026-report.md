# T026: COFF object writer

## Description
Implemented deterministic COFF object writer in C11 (`ax_coff_write`).
The writer handles sections, symbols, REL32, ADDR64, ADDR32NB relocations, string table for long names, and deterministic file outputs.
Added `cdriver_coff.c` to test COFF object generation using `gcc` for cross-linking.

## Round 1
- Fixed `ADDR32NB` relocation mapping (mapped `AX_RELOC_X86_64_32` to `IMAGE_REL_AMD64_ADDR32NB` as per task scope).
- Fixed BSS section sizing by computing the maximum virtual size from its symbols and writing it to `SizeOfRawData`.

## Files changed
- bootstrap/axiom0/src/obj/coff/writer.c
- bootstrap/axiom0/src/obj/coff/writer.h
- tests/obj/cdriver_coff.c
- tests/obj/fixtures/c_helper.c

STATUS: COMPLETE round=1
