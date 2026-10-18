# T085a QA Gate Report — Port COFF Object Writer & Object Model to Axiom

## Round 0

### 1. Task & Change-Set Verification
- **Command**: `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T085a`
- **Result**: Exit code 0, zero `REFUSED` lines. All modified/added files are within `paths: [compiler/obj, tests/selfhost/obj]` and listed in `_workspaces/reports/T085a-report.md` and `_workspaces/reports/T085a-qa.md`.
- **Report status line**: `STATUS: COMPLETE round=0` present on the last line of `_workspaces/reports/T085a-report.md`.

### 2. Build & Architecture Verification (`build-snap-T085a/`)
- **Build command**: `cmake -S bootstrap/axiom0 -B build -G Ninja -DCMAKE_C_COMPILER=gcc && cmake --build build` (inside `build-snap-T085a/`)
- **Build result**: 127 targets built, 0 warnings, 0 errors.
- **Layer / architecture check**: `python tools/archcheck.py` (inside `build-snap-T085a/`) -> `archcheck: 188 files scanned, 0 violations`.
- **Canonical syntax & split guide check (AXS-SELF-004)**:
  - `compiler/obj/coff.ax`: 1354 lines (`<= 1.5k` guide), canonical `=` bindings and `.` module paths.
  - `compiler/obj/writer.ax`: 372 lines, canonical `=` bindings and `.` module paths.
  - `compiler/obj/mod.ax`: 186 lines, public module facade re-exporting all types, constants, and functions.

### 3. Acceptance Criteria Verification
- **AC1 (Complete & readable COFF object writer & object model in `compiler/obj/`)**: Verified `compiler/obj/coff.ax`, `compiler/obj/writer.ax`, and `compiler/obj/mod.ax` against `bootstrap/axiom0/src/objmodel/objmodel.{h,c}` and `bootstrap/axiom0/src/obj/coff/writer.{h,c}`. All data structures (`SectionId`, `SymbolId`, `Reloc`, `Section`, `ObjSymbol`, `ObjModel`, `CoffBuf`, `CoffFileHeader`, `CoffSectionHeader`, `CoffRelocation`, `CoffSymbolRecord`), constants (`AX_SEC_*`, `AX_SEC_FLAG_*`, `AX_RELOC_*`, `AX_SYM_*`, `IMAGE_*`), and deterministic COFF layout rules (header, section headers, BSS symbol-derived `SizeOfRawData`, non-destructive inline relocation addend patching, 0-based `SymbolTableIndex`, short `<= 8` inline names vs `> 8` string-table offsets) are faithfully implemented.
- **AC2 (Unit tests pass in both interpreter and native modes)**:
  - `tests/selfhost/obj/qa_obj_model.ax`: PASS in `[interp]`, `[native]`, `[native-O1]`.
  - `tests/selfhost/obj/qa_coff_writer_diff.ax`: PASS in `[interp]`, `[native]`, `[native-O1]`.
  - `tests/selfhost/obj/qa_coff_edge_cases.ax` (added by QA): PASS in `[interp]`, `[native]`, `[native-O1]`.
- **AC3 (Emitted `.obj` file matches `axiom0 build --emit=obj` byte-for-byte on test programs)**:
  - Verified in `tests/selfhost/obj/qa_coff_writer_diff.ax` against C `ax_coff_write` reference fixtures (`basic.obj`, `relocs.obj`, `addr32nb.obj`) and `axiom0 build --emit=obj` outputs (`ret42.ax` and `calls.ax`), plus on-disk file roundtrip via `coff_write_str`.
- **AC4 (Test suites & archcheck clean)**:
  - `python tools/axtest.py --compiler build/axiom0.exe selfhost/obj obj e2e` (inside `build-snap-T085a/`): `TOTAL 11 PASS 11 FAIL 0 SKIP 0 XFAIL 0` (including all 3 modes `[interp]`, `[native]`, `[native-O1]` for the 3 `selfhost/obj` tests, `obj/cdriver_coff.c`, and `e2e/`).

### 4. Boundary Cross-Check & QA Tests Added
- Added `tests/selfhost/obj/qa_coff_edge_cases.ax` covering:
  1. Empty `ObjModel` encoding (`0` sections, `0` symbols -> 24-byte COFF image with `PointerToSymbolTable = 20`, `strtab_size = 4`) and idempotent double-free on `CoffBuf` and `ObjModel`.
  2. Section name length boundaries (`7`, `8`, `9` bytes -> inline 8-byte truncation/zero-padding) and symbol name length boundaries (`7`, `8`, `9`, `15` bytes -> inline `ShortName` vs string-table `Zeroes = 0, Offset = 4, 14` and `strtab_size = 30`).
  3. `.bss` section with multiple out-of-order symbols (`value + size` = `48`, `8`, `24`) alongside a `.data` symbol, followed by `.data` and `.text` raw data — verifying `.bss` `SizeOfRawData = 48`, `PointerToRawData = 0`, and subsequent section raw data offsets (`140`, `144`) are unaffected by uninitialized `.bss` size.
  4. Non-destructive repeated emission (`coff_encode_bytes` called twice on a section with `PC32` and `ADDR64` relocations): verifies underlying `Section.bytes` in `ObjModel` is not mutated by inline addend patching and both emissions are byte-for-byte identical.
  5. Negative/guard cases: out-of-bounds `section_byte_at`, `section_reloc_at`, `objmodel_get_symbol`, and null/empty path rejection in `coff_write`, `coff_write_path_bytes`, and `coff_write_str`.

### 5. Findings
None.

## Files changed
- tests/selfhost/obj/qa_coff_edge_cases.ax

VERDICT: PASS round=0
