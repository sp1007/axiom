# T085b Report — Port PE32+ Linker to Axiom (`compiler/link/`)

## Summary

Ported the `axiom0` PE32+ linker (`bootstrap/axiom0/src/link/pe/linker.{h,c}`, 742 lines of C) to Axiom under `compiler/link/` for the self-hosting `axiom1` compiler, and added unit, differential, and Windows execution tests under `tests/selfhost/link/`.

### Implemented Modules (`compiler/link/`)
1. **`compiler/link/pe.ax`** (1,066 lines):
   - PE32+ constants (`PE_DOS_HEADER_SIZE`, `PE_OPTIONAL_HEADER64_TOTAL_SIZE`, `PE_IMPORT_DESCRIPTOR_SIZE`, `PE_MAGIC_PE32_PLUS`, `PE_DEFAULT_IMAGE_BASE = 0x140000000`, `PE_DEFAULT_SECTION_ALIGN = 0x1000`, `PE_DEFAULT_FILE_ALIGN = 0x200`, `PE_DEFAULT_STACK_RESERVE = 0x100000`, image/subsystem/DLL characteristics, data directory indices `PE_DIR_EXPORT..PE_DIR_COM_DESCRIPTOR`, and AMD64 relocation constants `IMAGE_REL_AMD64_REL32_1..5`).
   - Alignment, layout, ASCII, and C-string helpers (`pe_align_up_u32`, `pe_align_up_usize`, `pe_compute_headers_size`, `pe_section_align_from_chars`, `pe_ascii_tolower`, `pe_bytes_ieq`, `pe_cstr_ieq`, `pe_cstr_starts_with`, `pe_cstr_find_char`, `pe_parse_u32_decimal`, `pe_read_i64_le`, `pe_write_i32_le`, `pe_buf_put_zeroes`, `pe_str_to_cstr_buf`).
   - PE32+ header and descriptor structures (`PeDataDirectory`, `PeImportDescriptor`, `PeOptionalHeader64`) along with binary encoders and decoders (`pe_emit_dos_header`, `pe_emit_pe_signature`, `pe_emit_file_header`, `pe_emit_optional_header64`, `pe_emit_data_directories`, `pe_emit_section_header`, `pe_decode_dos_header`, `pe_check_signature`, `pe_decode_optional_header64`, `pe_decode_data_directory`, `pe_decode_import_descriptor`, `pe_write_import_descriptor`).
   - Core linker context structures (`MergedSection`, `GlobalSymbol`, `PeReloc`, `LinkerContext`) and operations (`linker_context_init`, `linker_context_free`, `linker_find_section`, `linker_get_or_create_section`, `linker_append_section_data`, `linker_find_global`, `linker_add_global`, `linker_add_reloc`).

2. **`compiler/link/import.ax`** (775 lines):
   - Machine-code byte templates and emitters for all 5 CRT/entry/abort/alloc stubs synthesized into `.text`:
     - `__axiom_abort` (13 bytes, calls `ExitProcess(134)`)
     - `__axiom_start` (36 bytes, aligns RSP, calls `main`, passes return code in `ecx` to `ExitProcess`)
     - `exit` (9 bytes, calls `ExitProcess`)
     - `malloc` (29 bytes, calls `GetProcessHeap` + `HeapAlloc(hHeap, 8, size)`)
     - `free` (38 bytes, null-checks pointer, calls `GetProcessHeap` + `HeapFree(hHeap, 0, ptr)`)
   - Dynamic DLL import table data structures (`ImportFunc`, `DllImportGroup`, `ImportTable`) and synthesis routines:
     - `linker_parse_dll_func` for `dll!func` symbols, `linker_resolve_win32_dll` mapping standard Win32 symbols (`ExitProcess`, `GetStdHandle`, `WriteFile`, `ReadFile`, `CreateFileW`, `CloseHandle`, `DeleteFileW`, `GetFileAttributesW`, `CreateDirectoryW`, `RemoveDirectoryW`, `MoveFileExW`, `GetEnvironmentVariableW`, `SetEnvironmentVariableW`, `GetCommandLineW`, `GetCurrentDirectoryW`, `GetFileSizeEx`, `SetFilePointerEx`, `GetSystemTimeAsFileTime`, `QueryPerformanceCounter`, `QueryPerformanceFrequency`, `Sleep`, `GetProcessHeap`, `HeapAlloc`, `HeapFree`, `HeapReAlloc`, `VirtualAlloc`, `VirtualFree`, `GetLastError`) to `kernel32.dll` and `CommandLineToArgvW` to `shell32.dll`.
     - `linker_scan_and_collect_imports` and `linker_build_idata_section` building the two-pass `.idata` layout (Import Directory Table + null descriptor, ILT, Hint/Name Table with even-byte padding, IAT, DLL name strings, and 6-byte `FF 25 <disp32>` JMP thunks in `.text` plus `__imp_<func>` IAT symbols).

3. **`compiler/link/linker.ax`** (1,005 lines):
   - Linker diagnostic reporting (`AX_LINK_UNDEFINED_SYMBOL`, `AX_LINK_DUPLICATE_SYMBOL`, `AX_LINK_BAD_OBJECT`, `AX_LINK_IO_ERROR`).
   - `linker_load_coff_object` and `linker_load_coff_file`: COFF `.obj` validation, section merging with alignment padding, long section name resolution (`/offset` in COFF string table), symbol table parsing (short 8-byte names, string table offsets, auxiliary symbol skipping, `IMAGE_SYM_CLASS_EXTERNAL` duplicate detection, `IMAGE_SYM_CLASS_STATIC` local symbol registration), and relocation extraction (`ADDR64` 64-bit addend vs 32-bit signed addends).
   - `linker_assign_rvas`, `linker_apply_relocations` (`IMAGE_REL_AMD64_REL32`, `REL32_1..5`, `ADDR64`, `ADDR32NB`, `ADDR32`, `ABSOLUTE`), `linker_emit_pe_image`, and high-level entry points (`pe_link_coff_buffers_to_buf`, `pe_link_single_coff_to_buf`, `pe_link_objmodel_to_buf`, `pe_link`, `ax_pe_link`, `pe_link_files_str`, `pe_link_one_file_str`).

4. **`compiler/link/mod.ax`** (158 lines):
   - Re-exports the public PE32+ constants, types, header/import helpers, and linker entry points for `compiler.link`.

### Tests (`tests/selfhost/link/`)
- `tests/selfhost/link/qa_pe_headers_and_imports.ax`: Unit tests for PE32+ alignment/layout/string helpers, DOS/COFF/OptionalHeader64/DataDirectory/SectionHeader/ImportDescriptor binary encode/decode roundtrips, runtime stub and `.idata` import table synthesis, all AMD64 relocation types (`REL32`, `REL32_1..5`, `ADDR64`, `ADDR32NB`, `ADDR32`, `ABSOLUTE`), and diagnostic error reporting (`AX_LINK_BAD_OBJECT`, `AX_LINK_DUPLICATE_SYMBOL`, `AX_LINK_UNDEFINED_SYMBOL`).
- `tests/selfhost/link/qa_pe_linker_diff.ax`: Byte-for-byte differential tests comparing Axiom-linked PE32+ executables against `axiom0`'s C linker (`main42.exe`, `main42_bigstack.exe`, `ret42.exe`, `calls.exe`), multi-object linking across `.text`/`.data`/`.rdata`/`.bss` with cross-module `EXTERNAL` and colliding `STATIC` symbols, on-disk `.obj -> .exe` linking via `pe_link_one_file_str`, and actual Windows execution of the linked `.exe` binaries verifying exit code `42`.

## Files changed

- `compiler/link/import.ax`
- `compiler/link/linker.ax`
- `compiler/link/mod.ax`
- `compiler/link/pe.ax`
- `tests/selfhost/link/qa_pe_headers_and_imports.ax`
- `tests/selfhost/link/qa_pe_linker_diff.ax`

## Verification

- Snapshot build (`build-snap-T085b/build`): clean, 0 warnings (`AX_WERROR=ON`).
- `python tools/archcheck.py`: clean.
- `python tools/axtest.py --compiler build/axiom0.exe selfhost/link link obj e2e`: all tests pass across `[interp]`, `[native]`, and `[native-O1]`.

STATUS: COMPLETE round=0
