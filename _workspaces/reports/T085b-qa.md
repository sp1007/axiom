# T085b QA Gate Report — Port PE32+ Linker to Axiom (`compiler/link/`)

## Round 0

### 1. Task Changeset & Ownership Check
Command:
```
python .claude/skills/axiom-tasks/scripts/taskctl.py changes T085b
```
Output:
```
stage _workspaces/reports/T085b-report.md
stage compiler/link/import.ax
stage compiler/link/linker.ax
stage compiler/link/mod.ax
stage compiler/link/pe.ax
stage tests/selfhost/link/qa_pe_headers_and_imports.ax
stage tests/selfhost/link/qa_pe_linker_diff.ax
```
- 0 `REFUSED` lines. All modified files are under the task's `paths: [compiler/link, tests/selfhost/link]`.
- `_workspaces/reports/T085b-report.md` ends with `STATUS: COMPLETE round=0` and lists the exact `## Files changed`.

### 2. Snapshot Build & Architecture Layer Check
Commands (executed in `build-snap-T085b`):
```
cmake -S bootstrap/axiom0 -B build -G Ninja -DCMAKE_C_COMPILER=gcc
cmake --build build
python tools/archcheck.py
```
Result:
- `axiom0.exe` and all C driver targets built with 0 warnings (`AX_WERROR=ON`).
- `archcheck: 188 files scanned, 0 violations`.

### 3. Acceptance & Spec Conformance Verification
- **PE32+ Linker Implementation (`compiler/link/`)**:
  - `compiler/link/pe.ax` (1,067 lines): PE32+ constants, alignment/layout/ASCII helpers, `PeDataDirectory`, `PeImportDescriptor`, `PeOptionalHeader64` encoders/decoders, and `LinkerContext` (`MergedSection`, `GlobalSymbol`, `PeReloc`) arena/heap management.
  - `compiler/link/import.ax` (776 lines): Runtime startup & host stubs (`AXIOM_START_CODE`, `AXIOM_PANIC_CODE`, `AXIOM_PRINT_CODE`, `AXIOM_PRINT_INT_CODE`), `ImportTable` / `ImportDll` / `ImportFunc` management, case-insensitive DLL normalization (`kernel32` -> `KERNEL32.dll`), relocation-driven DLL import discovery (`DLL$func` and `__IAT_func`), 6-byte `FF 25 <disp32>` jump thunk synthesis in `.text`, and `.idata` construction + RVA patching.
  - `compiler/link/linker.ax` (1,006 lines): Linker diagnostics (`AX_LINK_BAD_OBJECT`, `AX_LINK_DUPLICATE_SYMBOL`, `AX_LINK_UNDEFINED_SYMBOL`), COFF `.obj` parsing and section/symbol/relocation merging (`linker_load_coff_object`), RVA & file offset layout (`linker_assign_rvas`), AMD64 relocation resolution (`REL32`, `REL32_1..5`, `ADDR64`, `ADDR32NB`, `ADDR32`, `ABSOLUTE`), and PE32+ executable serialization (`linker_emit_pe_image`, `pe_link_coff_buffers_to_buf`, `pe_link_single_coff_to_buf`, `pe_link_objmodel_to_buf`, `pe_link_one_file_str`, `ax_pe_link`).
  - `compiler/link/mod.ax` (159 lines): Clean module facade re-exporting public symbols of `compiler.link`.
  - Canonical Axiom syntax verified across all files (`=` only, `.` paths only, no `BOOTSTRAP-SHORTCUT`, all files well within the ~1.5k split guide of AXS-SELF-004).
- **Differential & Execution Verification (`tests/selfhost/link/qa_pe_linker_diff.ax`)**:
  - Byte-for-byte identical PE32+ executable output verified against `axiom0`'s C linker for `main42.exe`, `main42_bigstack.exe`, `ret42.exe`, and `calls.exe`.
  - Multi-object linking across `.text`, `.data`, `.rdata`, and `.bss` with cross-module `EXTERNAL` and colliding `STATIC` symbols verified, written to disk, and executed on Windows returning exit code `42`.

### 4. Boundary Cross-Check & QA Edge-Case Tests Added
- Audited the seam between `compiler.obj` (`CoffFileHeader`, `CoffSectionHeader`, `CoffSymbolRecord`, `CoffRelocation`, `CoffBuf`) and `compiler.link` (`linker_load_coff_object`, `import_discover_from_relocs`).
- Added `test_qa_coff_edge_cases_and_seams` to `tests/selfhost/link/qa_pe_headers_and_imports.ax` testing:
  1. Long COFF section names resolved from the COFF string table via `/<decimal_offset>` (`/4` -> `".text_long"` truncated to 8-byte `".text_lo"`).
  2. COFF symbol records with `NumberOfAuxSymbols = 1` followed by an external symbol referenced by a relocation (`SymbolTableIndex = 2`), verifying auxiliary symbol skipping and symbol index alignment.
  3. Exact 8-character `ShortName` symbol (`"eightchr"`) with no NUL byte in the 8-byte COFF field, verifying NUL-terminated extraction in `GlobalSymbol`.
  4. Direct `__IAT_<func>` relocation discovery (`__IAT_GetLastError`) without a `DLL$` prefix into `KERNEL32.dll`.
  5. Additional negative boundary checks in `linker_load_coff_object`: wrong `Machine` field (`0x014C` i386) and truncated section header table (`NumberOfSections = 4` in a 20-byte buffer), both reporting `AX_LINK_BAD_OBJECT`.

### 5. Test Suite Execution (in `build-snap-T085b`)
Command:
```
python tools/axtest.py --compiler build/axiom0.exe selfhost/link selfhost/obj link obj e2e
```
Output:
```
TOTAL 21 PASS 21 FAIL 0 SKIP 0 XFAIL 0
```
All 21 test executions (including `selfhost/link/qa_pe_headers_and_imports.ax` and `selfhost/link/qa_pe_linker_diff.ax` in `[interp]`, `[native]`, and `[native-O1]`) passed.

### Findings
None.

## Files changed
- `tests/selfhost/link/qa_pe_headers_and_imports.ax`

## Verdict
VERDICT: PASS round=0
