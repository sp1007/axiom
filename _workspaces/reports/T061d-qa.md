# QA Report: T061d — Native catch-up: constant tables in .rdata

## Round 0

### Summary
Independent verification of task T061d (Native catch-up: constant tables in .rdata). Built and tested exclusively inside snapshot `build-snap-T061d/`. All acceptance criteria independently verified: 0 compiler warnings under both GCC (16.1.0) and Clang (22.1.4); archcheck clean (0 violations); full test suite passes (1324 PASS, 0 FAIL, 22 SKIP, 0 XFAIL). Directives `// native-after: T061d` completely retired (0 hits). Stack frame size for 4 KB table function confirmed at 248 bytes (< 256 bytes). Constant table deduplication in `.rdata` and deterministic ordering verified. GCC cross-link oracle on emitted objects verified. Boundary cross-check test added for multiple heterogeneous tables and empty string slice relocations.

### Checks Performed & Evidence

1. **Change set & path validation**:
   - Command: `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T061d`
   - Verified all touched files (`bootstrap/axiom0/src/lir/lower.c`, `lir.h`, `bootstrap/axiom0/src/target/x64/frame/frame.c`, `bootstrap/axiom0/src/driver/build_native/build.c`, `emit_obj.c`, `emit_mc.c`, `tests/run/comptime/*.ax`, `tests/run/native_const/*.ax`) strictly respect task paths and locks. 0 REFUSED lines.

2. **Snapshot Build & Compiler Warning-Free Status**:
   - GCC build:
     - Command: `ninja -C build-snap-T061d/build -t clean && cmake --build build-snap-T061d/build`
     - Result: Clean compilation of all 126 build targets with 0 warnings, 0 errors.
   - Clang build:
     - Command: `cmake -S build-snap-T061d/bootstrap/axiom0 -B build-snap-T061d/build-clang -G Ninja -DCMAKE_C_COMPILER=clang && cmake --build build-snap-T061d/build-clang`
     - Result: Clean compilation with 0 warnings, 0 errors.
   - CTest suite:
     - Command: `ctest --test-dir build-snap-T061d/build --output-on-failure`
     - Result: 17/17 tests passed (100%).

3. **Architecture Layer Checker**:
   - Command: `python tools/archcheck.py --root build-snap-T061d`
   - Result: `archcheck: 145 files scanned, 0 violations` (INV-LAYER-001..008 respected).

4. **Retirement of `native-after: T061d`**:
   - Command: `git grep -rn "native-after: T061d" tests`
   - Result: 0 hits (exit code 1). All 5 comptime table tests in `tests/run/comptime/` (`table_u8_256.ax`, `table_str.ax`, `table_struct.ax`, `qa_table_u8_loop.ax`, `qa_table_struct_str.ax`) now pass natively.

5. **Stack Frame Size (< 256 bytes for 4 KB Table)**:
   - Command: `build-snap-T061d/build/axiom0.exe build --emit=obj -o build-snap-T061d/build/table_4kb.obj tests/run/native_const/table_4kb.ax`
   - Disassembly inspection (`objdump -d build-snap-T061d/build/table_4kb.obj`):
     - `index_table()` prologue: `sub $0xf8, %rsp` (0xf8 = 248 bytes < 256 bytes).
     - Epilogue: `add $0xf8, %rsp`.
     - Table access: `lea 0x0(%rip), %rax` with `IMAGE_REL_AMD64_REL32` relocation referencing `.Lconst_25_TABLE_4KB`.
     - Confirmed: 0 bytes of table data copied to the stack.

6. **Table Deduplication & Determinism in `.rdata`**:
   - Command: `build-snap-T061d/build/axiom0.exe build --emit=obj -o build-snap-T061d/build/identical_tables.obj tests/run/native_const/identical_tables.ax`
   - Symbol & section inspection (`objdump -t` & `objdump -s -j .rdata`):
     - `.Lconst_25_TABLE_A`: section 1 (.rdata), offset 0x00000000.
     - `.Lconst_26_TABLE_B`: section 1 (.rdata), offset 0x00000000.
     - Payload at offset 0x0 is exactly 16 bytes (`0a000000 14000000 1e000000 28000000`), followed immediately by `.Lpanic_0` at offset 0x10. Tables are deduplicated to a single instance in `.rdata`.
     - Symbols are sorted alphabetically deterministically.
   - Deterministic rebuild: independent compilations produce byte-identical object files (verified via exact byte comparison).

7. **GCC Cross-Link Oracle**:
   - Emitted object files (`table_str.obj`, `table_struct.obj`, `table_4kb.obj`) contain `IMAGE_REL_AMD64_ADDR64` relocations in `.rdata` for `Str` pointers and `IMAGE_REL_AMD64_REL32` for RIP-relative accesses.
   - Linked using GCC (MinGW-w64 x86_64) into native executables.
   - All executables ran and exited with status 0.

8. **Full Suite Execution**:
   - Command: `python tools/axtest.py --root build-snap-T061d --compiler build-snap-T061d/build/axiom0.exe --build-dir build-snap-T061d/build`
   - Result: `TOTAL 1346 PASS 1324 FAIL 0 SKIP 22 XFAIL 0`
   - 0 failures, 0 crashes, 0 timeouts.

### Boundary Cross-Check Tests Added
- `tests/run/native_const/qa_table_str_empty_and_multitables.ax`:
  Exercises multiple heterogeneous constant tables in one compilation unit, specifically verifying empty strings (`""`, length 0) within a `[4]Str` table alongside non-empty strings, and a separate table of structs (`[3]Item`) containing `(u32, Str)`. Validated with both interpreter/native execution and GCC cross-link oracle.

### Findings
None.

## Files changed
- tests/run/native_const/qa_table_str_empty_and_multitables.ax

## Verdict
VERDICT: PASS round=0
