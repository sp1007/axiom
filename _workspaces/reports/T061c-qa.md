# QA Report: T061c — Host-interface intrinsics: oracle implementation + native call lowering

## Round 0

### Summary
Independent verification of task T061c (Host-interface intrinsics: oracle implementation + native call lowering). Built and tested exclusively inside snapshot `build-snap-T061c/`. All acceptance criteria independently verified; 0 compiler warnings under both GCC and Clang; archcheck clean (0 violations); full test suite passes (1293 PASS, 0 FAIL). Boundary cross-check tests added for `metadata` (file, directory, and non-existent) and negative handle error codes (`-4` InvalidInput).

### Checks Performed & Evidence

1. **Change set & path validation**:
   - Command: `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T061c`
   - Verified that all modified compiler files (`pipeline.c`, `host.c`, `host.h`, `interp.c`, `interp.h`, `lower.c`), intrinsic definitions (`std/core/host.ax`), and test files (`tests/run/host/`) fall strictly within task paths and locks.

2. **Snapshot Build & Warning-Free Verification**:
   - GCC build:
     - Command: `cmake -S build-snap-T061c/bootstrap/axiom0 -B build-snap-T061c/build -G Ninja -DCMAKE_C_COMPILER=gcc && cmake --build build-snap-T061c/build`
     - Result: Succeeded with 0 warnings.
   - Clang build:
     - Command: `cmake -S build-snap-T061c/bootstrap/axiom0 -B build-snap-T061c/build-clang -G Ninja -DCMAKE_C_COMPILER=clang && cmake --build build-snap-T061c/build-clang`
     - Result: Succeeded with 0 warnings.
   - Unit tests:
     - Command: `build-snap-T061c/build/axiom0-unit.exe`
     - Result: `UNIT 71 tests, 0 failed`

3. **Architecture Layer Checker**:
   - Command: `python tools/archcheck.py --root build-snap-T061c`
   - Result: `archcheck: 145 files scanned, 0 violations` (strictly respects INV-LAYER-001..008).

4. **Acceptance Criteria Verification**:
   - **Heap operations (`alloc.ax`, `use_after_free.ax`)**:
     - `alloc.ax`: verified `heap_alloc(16, 8)`, byte writes, `heap_realloc(p, 16, 32, 8)`, verification of retained data, expansion writes, and `heap_free` pass cleanly.
     - `use_after_free.ax`: verified accessing a freed pointer immediately triggers oracle UB detection (`use-after-free`), exiting with code 125.
   - **IO & Process operations (`write_stdout_stderr.ax`, `args.ax`, `env.ax`, `exit7.ax`)**:
     - `write_stdout_stderr.ax`: byte-exact UTF-8 writes to stdout (`Xin chào thế giới\n`) and stderr (`lỗi\n`) pass.
     - `args.ax`: verified CLI arguments forwarding past `--` with UTF-8 (`"xin chào"`), reporting `args_count()` == 2 and exact string in `arg(1)`.
     - `env.ax`: verified `env_get` with `AXIOM_TEST_HOST=xin_chao` returning exact length and content.
     - `exit7.ax`: verified `exit(7)` terminates the interpreter with exit code 7.
   - **FS & Clock operations (`file_io.ax`, `dir.ax`, `clock.ax`)**:
     - `file_io.ax`: file create/write/size/close/reopen-read/compare/remove cycle passes.
     - `dir.ax`: directory creation, file creation inside directory, `dir_open`, entry iteration via `dir_next`, `dir_close`, and directory cleanup pass.
     - `clock.ax`: `monotonic_ns` verified non-decreasing over loop execution.
   - **Native Lowering & Link Error Handling**:
     - All tests carry the prescribed directives: `// native-after: T070` for heap, `// native-after: T074` for io/process, and `// native-after: T074b` for fs/clock.
     - `native_undefined_symbol.test`: verified that attempting a native compile without implementations produces `AX_LINK_UNDEFINED_SYMBOL: __ax_host_heap_alloc` with exit code 1 (no crash).
     - Confirmed native compilation cleanly reports missing symbols across all three groups: `__ax_host_heap_alloc`, `__ax_host_stdio`, `__ax_host_monotonic_ns`.

5. **Full Suite Execution**:
   - Command: `python tools/axtest.py --compiler build/axiom0.exe` (run inside snapshot `build-snap-T061c/`)
   - Result: `TOTAL 1325 PASS 1293 FAIL 0 SKIP 32 XFAIL 0`
   - Zero crashes, zero regressions.

### Boundary Cross-Check Tests Added
- `tests/run/host/fs/metadata.ax`: Exercises the `metadata` intrinsic (`// native-after: T074b`), checking file attribute kind (1 for regular file, 2 for directory), exact file size in bytes, and `-1` (NotFound) on nonexistent paths.
- `tests/run/host/io/invalid_handle.ax`: Negative test verifying that invalid handles passed to `read`, `write`, `close`, `file_size`, `arg`, `dir_next`, and `dir_close` return `-4` (`InvalidInput`) rather than crashing or causing undefined behavior.

### Findings
None.

## Files changed
- tests/run/host/fs/metadata.ax
- tests/run/host/io/invalid_handle.ax

VERDICT: PASS round=0
