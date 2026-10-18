# T085a Report — Port COFF Object Writer & Object Model to Axiom

## Summary

Ported the target-neutral object model (`bootstrap/axiom0/src/objmodel/objmodel.h` and `bootstrap/axiom0/src/objmodel/objmodel.c`) and the deterministic Windows x64 COFF relocatable `.obj` binary writer (`bootstrap/axiom0/src/obj/coff/writer.h` and `bootstrap/axiom0/src/obj/coff/writer.c`) from C to canonical Axiom under `compiler/obj/`, with self-contained unit and differential test suites under `tests/selfhost/obj/`.

### Implemented Modules (`compiler/obj/`)

1. **`compiler/obj/coff.ax`** (`module compiler.obj.coff`):
   - **Growable Byte Buffer (`CoffBuf`)**: `coff_buf_new`, `coff_buf_with_capacity`, `coff_buf_free`, `coff_buf_clear`, `coff_buf_reserve`, `coff_buf_put_u8`, `coff_buf_put_u16`, `coff_buf_put_i16`, `coff_buf_put_u32`, `coff_buf_put_u64`, `coff_buf_put_bytes`, plus `Drop` implementation.
   - **Typed 1-Based Indices (`SectionId`, `SymbolId`)**: 0-sentinel (`none()`, `is_none()`, `eq()`) plus `ax_section_id_*` and `ax_symbol_id_*` C-API-compatible helpers.
   - **Object Model Constants & COFF Constants**:
     - `SEC_CODE` / `AX_SEC_CODE`, `SEC_DATA` / `AX_SEC_DATA`, `SEC_RODATA` / `AX_SEC_RODATA`, `SEC_BSS` / `AX_SEC_BSS`
     - `SEC_FLAG_NONE` / `AX_SEC_FLAG_NONE`, `SEC_FLAG_EXEC` / `AX_SEC_FLAG_EXEC`, `SEC_FLAG_WRITE` / `AX_SEC_FLAG_WRITE`, `SEC_FLAG_READ` / `AX_SEC_FLAG_READ`
     - `RELOC_NONE` / `AX_RELOC_NONE`, `RELOC_X86_64_PC32` / `AX_RELOC_X86_64_PC32`, `RELOC_X86_64_32` / `AX_RELOC_X86_64_32`, `RELOC_X86_64_64` / `AX_RELOC_X86_64_64`, `RELOC_X86_64_GOT32` / `AX_RELOC_X86_64_GOT32`, `RELOC_X86_64_PLT32` / `AX_RELOC_X86_64_PLT32`
     - `SYM_LOCAL` / `AX_SYM_LOCAL`, `SYM_GLOBAL` / `AX_SYM_GLOBAL`, `SYM_EXTERNAL` / `AX_SYM_EXTERNAL`
     - `COFF_FILE_HEADER_SIZE` (20), `COFF_SECTION_HEADER_SIZE` (40), `COFF_RELOC_SIZE` (10), `COFF_SYMBOL_SIZE` (18), `IMAGE_FILE_MACHINE_AMD64` (`0x8664`), `IMAGE_SCN_*`, `IMAGE_SYM_CLASS_*`, `IMAGE_REL_AMD64_*`.
   - **COFF Binary Header & Record Decoders & Mapping Helpers**:
     - `CoffFileHeader`, `CoffSectionHeader`, `CoffRelocation`, `CoffSymbolRecord`
     - `coff_align_flag`, `coff_section_characteristics`, `coff_reloc_type`, `coff_storage_class`
     - `coff_read_u16_le`, `coff_read_u32_le`, `coff_read_i32_le`, `coff_read_u64_le`, `coff_write_u16_le`, `coff_write_u32_le`, `coff_write_u64_le`
     - `coff_decode_file_header`, `coff_decode_section_header`, `coff_decode_relocation`, `coff_decode_symbol_record`.
   - **Target-Neutral Object Model (`Reloc`, `Section`, `ObjSymbol`, `ObjModel`)**:
     - Exact field parity with `bootstrap/axiom0/src/objmodel/objmodel.h` (`Reloc { offset, kind, symbol_id, addend }`, `Section { id, name, name_len, kind, flags, align, bytes, bytes_len, bytes_cap, relocs, relocs_len, relocs_cap }`, `ObjSymbol { id, name, name_len, section_id, value, size, linkage }`, `ObjModel { sections, sections_len, sections_cap, symbols, symbols_len, symbols_cap, str_arena }`).
     - String ownership via `str_arena` (`*mut Arena`) so section and symbol names passed from stack buffers or `Str` slices are arena-duplicated with a trailing NUL byte and remain valid for the lifetime of `ObjModel`.
     - Full section/symbol/relocation API (`objmodel_new`, `objmodel_init`, `objmodel_free`, `objmodel_add_section`, `objmodel_add_section_bytes`, `objmodel_add_section_str`, `objmodel_get_section`, `objmodel_get_section_mut`, `objmodel_find_section`, `objmodel_find_section_bytes`, `objmodel_find_section_str`, `objmodel_add_symbol`, `objmodel_add_symbol_bytes`, `objmodel_add_symbol_str`, `objmodel_get_symbol`, `objmodel_get_symbol_mut`, `objmodel_find_symbol`, `objmodel_find_symbol_bytes`, `objmodel_find_symbol_str`, `section_add_byte`, `section_add_bytes`, `section_append_bytes`, `section_append_zeroes`, `section_append_slice`, `section_add_reloc`, `objmodel_section_add_byte`, `objmodel_section_add_bytes`, `objmodel_section_append_slice`, `objmodel_section_add_reloc`, plus `ax_*` aliases).

2. **`compiler/obj/writer.ax`** (`module compiler.obj.writer`):
   - `coff_write_to_buf(model: view<ObjModel>, out: mut_view<CoffBuf>) -> bool`
   - `coff_encode_bytes(model: view<ObjModel>) -> CoffBuf`
   - `coff_write_path_bytes(model: view<ObjModel>, path_ptr: *const u8, path_len: usize) -> bool`
   - `coff_write(model: view<ObjModel>, output_path: *const u8) -> bool` / `ax_coff_write`
   - `coff_write_str(model: view<ObjModel>, output_path: Str) -> bool`
   - Produces deterministic Windows x64 COFF relocatable `.obj` binaries matching `bootstrap/axiom0/src/obj/coff/writer.c` byte-for-byte:
     1. 20-byte `IMAGE_FILE_HEADER` (`Machine = 0x8664`, `TimeDateStamp = 0`, deterministic `PointerToSymbolTable`, `NumberOfSymbols`).
     2. 40-byte `IMAGE_SECTION_HEADER` records (inline 8-byte section name, `SizeOfRawData` computed from symbols' `value + size` for `AX_SEC_BSS` or `bytes_len` for initialized sections, `PointerToRawData = 0` when `bytes_len == 0`, `PointerToRelocations`, `NumberOfRelocations`, section characteristics & alignment flags).
     3. Section raw data with non-destructive inline relocation addend patching (`PC32`/`PLT32` writes `(int32_t)addend + 4` LE, `32`/`GOT32` writes `(int32_t)addend` LE, `64` writes `(uint64_t)addend` LE) followed immediately by 10-byte COFF relocation records (`VirtualAddress`, 0-based `SymbolTableIndex = symbol_id.v - 1`, `Type`).
     4. 18-byte `IMAGE_SYMBOL` records (inline 8-byte name for `<= 8` bytes, or `Zeroes = 0` + string table `Offset` starting at `4` for `> 8` bytes; `SectionNumber = 0` for `IMAGE_SYM_UNDEFINED` or 1-based section index; `StorageClass = IMAGE_SYM_CLASS_EXTERNAL` (2) or `IMAGE_SYM_CLASS_STATIC` (3)).
     5. COFF string table (`uint32_t` total byte size prefix `>= 4` followed by NUL-terminated long symbol names `> 8` bytes).

3. **`compiler/obj/mod.ax`** (`module compiler.obj`):
   - Public facade re-exporting all types, constants, and functions from `compiler.obj.coff` and `compiler.obj.writer`.

## Verification

- **`python tools/archcheck.py`**: `188 files scanned, 0 violations`.
- **`python tools/axtest.py selfhost/obj`**:
  - `PASS selfhost/obj/qa_obj_model.ax [interp]`
  - `PASS selfhost/obj/qa_obj_model.ax [native]`
  - `PASS selfhost/obj/qa_obj_model.ax [native-O1]`
  - `PASS selfhost/obj/qa_coff_writer_diff.ax [interp]`
  - `PASS selfhost/obj/qa_coff_writer_diff.ax [native]`
  - `PASS selfhost/obj/qa_coff_writer_diff.ax [native-O1]`
- **Differential Verification Coverage (`qa_coff_writer_diff.ax`)**:
  1. Byte-for-byte equality against `tests/obj/cdriver_coff.c` `test_basic_obj()` (`basic.obj`, 146 bytes: `.text` + `.bss` with symbol-derived BSS `SizeOfRawData = 8` and `PointerToRawData = 0`).
  2. Byte-for-byte equality against `tests/obj/cdriver_coff.c` `test_relocs_obj()` (`relocs.obj`, 316 bytes: `.text`, `.data`, `.rdata`, UTF-8 string bytes, `ADDR64` and `REL32` relocations, inline addend `-4 -> 0`, and long symbol names `my_data_word`, `ptr_to_msg`, `check_data` in the COFF string table).
  3. Byte-for-byte equality against `tests/obj/cdriver_coff.c` `addr32nb.obj` (96 bytes: `.pdata` with `AX_RELOC_X86_64_32 -> IMAGE_REL_AMD64_ADDR32NB`).
  4. Inline relocation addend patching verification across all 5 relocation kinds (`PC32`, `PLT32`, `32`, `GOT32`, `64`).
  5. Byte-for-byte equality against `axiom0 build --emit=obj` on `tests/selfhost/obj/inputs/ret42.ax` (311 bytes) and `tests/selfhost/obj/inputs/calls.ax` (980 bytes), plus on-disk file I/O roundtrip via `coff_write_str`.

## Follow-ups (Stage-0 `axiom0` Notes)

1. **`axiom0` interpreter return-value buffer size (`bootstrap/axiom0/src/interp/host.h` & `interp.c`)**: `AxInterpValue` is `uint64_t vals[8]` (64 bytes), and `eval_call` passes `sizeof(AxInterpValue)` to `exec_mir_body` before copying `ax_type_size(dest_ty)` bytes into `dest`. Returning any struct `> 64` bytes by value reads past `ret_val` in `[interp]`. Keeping `ObjModel` at 56 bytes (`<= 64` bytes) avoids this limit cleanly.
2. **`axiom0` interpreter `AX_MIR_OP_CONST` `Str` call arguments (`bootstrap/axiom0/src/interp/interp.c:1519`)**: When a string literal is passed directly as a call argument (`AX_MIR_OP_CONST`), `interp.c` copies only `constant.val` (`0`) into `call_args` instead of `constant.str.bytes` and `constant.str.len`. Evaluating string literal arguments through a block expression `{ "literal" }` or local variable uses `AX_MIR_RVALUE_USE`, which copies both `str.bytes` and `str.len`.

## Files changed
- compiler/obj/coff.ax
- compiler/obj/writer.ax
- compiler/obj/mod.ax
- tests/selfhost/obj/qa_obj_model.ax
- tests/selfhost/obj/qa_coff_writer_diff.ax

STATUS: COMPLETE round=0
