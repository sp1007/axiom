# T061d report: Native catch-up: constant tables in .rdata

## Summary
Task T061d implements native code generation support for constant aggregate tables (e.g. byte lookup tables, string tables, struct array tables). Constant tables are materialized once into `.rdata`, deduplicated deterministically by contents and ordered alphabetically by symbol name. String fields within constant aggregates emit string literals into `.rdata` and generate 64-bit absolute relocations (`AX_RELOC_X86_64_64` / `IMAGE_REL_AMD64_ADDR64`).

Key changes:
1. **LIR Lowering (`bootstrap/axiom0/src/lir/lower.c`, `lir.h`)**:
   - `AxLirStackSlot` tracks `bool is_const`.
   - `lower_place_addr` detects `AX_MIR_LOCAL_CONST` and emits `AX_LIR_INST_FN_ADDR` for RIP-relative addressing (`.Lconst_<sym>_<name>`).
   - Assignment statements into constant locals in MIR are skipped (since the value lives in `.rdata`).
   - Constant slots in `AxLirBody` have `is_const = true`.
2. **Frame Lowering (`bootstrap/axiom0/src/target/x64/frame/frame.c`)**:
   - Stack frame allocation skips stack slot space for `is_const` locals, ensuring constant tables consume zero stack bytes.
   - Non-const zero-sized locals retain standard slot allocation (`if (size < 8) size = 8`) to preserve saved frame pointer integrity.
3. **Driver & Object Model (`bootstrap/axiom0/src/driver/build_native/build.c`, `emit_obj.c`, `emit_mc.c`)**:
   - Implemented `emit_const_tables` to scan monomorphized instances / HIR items for `AX_MIR_LOCAL_CONST` tables.
   - Emits byte contents into `.rdata`, recurses into aggregate types to resolve `Str` slices and emit string literals, creating `AX_RELOC_X86_64_64` relocations pointing to the string data.
   - Deduplicates identical table contents, assigning identical offsets in `.rdata` to shared tables while preserving separate symbol entries.
   - Sorts table symbols deterministically in alphabetical order before writing to the object model.
   - Handles `AX_X64_MI_LEA` with `AX_X64_OP_SYM` in machine code and object emission.

## Files changed
- bootstrap/axiom0/src/driver/build_native/build.c
- bootstrap/axiom0/src/driver/emit_mc.c
- bootstrap/axiom0/src/driver/emit_obj.c
- bootstrap/axiom0/src/lir/lir.h
- bootstrap/axiom0/src/lir/lower.c
- bootstrap/axiom0/src/target/x64/frame/frame.c
- tests/run/comptime/qa_table_struct_str.ax
- tests/run/comptime/qa_table_u8_loop.ax
- tests/run/comptime/table_str.ax
- tests/run/comptime/table_struct.ax
- tests/run/comptime/table_u8_256.ax
- tests/run/native_const/identical_tables.ax
- tests/run/native_const/table_4kb.ax

## Verification
- **Comptime Directives**: All 5 `// native-after: T061d` directives removed from `tests/run/comptime/*.ax`. `git grep "native-after: T061d" tests` returns 0 matches.
- **Stack Frame Size**: Verified with `tests/run/native_const/table_4kb.ax` (`[4096]u8`). Stack frame size allocated by function prologue is 248 bytes (`add $0xf8, %rsp`), strictly smaller than 256 bytes.
- **Deduplication & Determinism**: Verified with `tests/run/native_const/identical_tables.ax`. Symbols `.Lconst_25_TABLE_A` and `.Lconst_26_TABLE_B` share offset 0 in `.rdata`. Table symbols are deterministically sorted.
- **Cross-link Oracle**: Tested `table_str.ax` object file emitted with `--emit=obj`. Linked with GCC (MinGW-w64 x86_64) into an executable and executed successfully with exit code 0.
- **Architecture Check**: `python tools/archcheck.py` reported 151 files scanned, 0 violations.
- **Full Test Suite**: Tested in isolated snapshot `build-snap-T061d`:
  - `python tools/axtest.py --root build-snap-T061d --compiler build-snap-T061d/build/axiom0.exe --build-dir build-snap-T061d/build`: `TOTAL 1343 PASS 1321 FAIL 0 SKIP 22 XFAIL 0`.
  - CTest: 17/17 tests passed (100%).

## Spec deviations
none

## Follow-ups
none

STATUS: COMPLETE round=0
