# QA Report: T061b — Native catch-up: raw pointers and memory intrinsics

## Round 0

### Summary
Independent verification of task T061b (Native catch-up: raw pointers and memory intrinsics). Built and tested exclusively inside snapshot `build-snap-T061b/`. All acceptance criteria independently verified; 0 build warnings; archcheck clean; full test suite passes. Boundary cross-check test added verifying zero-count operations, identical pointer copies, multi-byte element scaling in `ptr_write_bytes`, and composite `needs_drop` evaluations.

### Checks Performed & Evidence

1. **Change set & path validation**:
   - Command: `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T061b`
   - Result: 0 REFUSED lines. All modified files (`lower.c`, `tests/run/ptr/`, `tests/run/native_ptr/`) are strictly within the task's assigned paths.
   - Command: `git grep -rn "native-after: T061b" tests`
   - Result: 0 matches found (all `native-after: T061b` directives successfully removed from `tests/run/ptr/`).

2. **Snapshot Build**:
   - Command: `cmake -S bootstrap/axiom0 -B build -G Ninja -DCMAKE_C_COMPILER=gcc && cmake --build build --clean-first` (inside `build-snap-T061b/`)
   - Result: Build succeeded with 0 warnings.
   - Command: `build/axiom0-unit.exe` (inside `build-snap-T061b/`)
   - Result: `UNIT 71 tests, 0 failed`

3. **Architecture Boundary Check**:
   - Command: `python tools/archcheck.py` (run against `build-snap-T061b/`)
   - Result: `archcheck: 141 files scanned, 0 violations`

4. **Acceptance Criteria Verification**:
   - **tests/run/ptr/** (catch-up run tests):
     - `python tools/axtest.py --compiler build/axiom0.exe --filter run/ptr`
     - Result: `TOTAL 25 PASS 25 FAIL 0 SKIP 0 XFAIL 0`
     - All 7 pointer tests (`arena_align.ax`, `drop_in_place.ax`, `field_write.ax`, `layout_intrinsics.ax`, `linked_list.ax`, `mem_intrinsics.ax`, `sum_walk.ax`) pass across all required run modes (interp, native, native-O1).
   - **tests/run/native_ptr/** (native memory intrinsics & edge tests):
     - `python tools/axtest.py --compiler build/axiom0.exe --filter run/native_ptr -v`
     - Result: `TOTAL 8 PASS 8 FAIL 0 SKIP 0 XFAIL 0`
     - `overlap_copy.ax`: overlapping `ptr_copy` in both directions (right shift `src < dst`, left shift `src > dst`) passes natively.
     - `write_bytes_1mb.ax`: 1 MB buffer initialization via `ptr_write_bytes` passes natively.
     - `qa_mem_edge.ax`: edge cases for zero-length copies/writes, identity copies (`src == dst`), scaled multi-byte writes, and composite `needs_drop` pass in interp and native modes.

5. **Full Suite Execution**:
   - Command: `python tools/axtest.py --compiler build/axiom0.exe` (inside snapshot `build-snap-T061b/`)
   - Result: `TOTAL 1263 PASS 1263 FAIL 0 SKIP 0 XFAIL 0`
   - Zero crashes, zero unexpected failures, zero regressions.

### Boundary Cross-Check Tests Added
- `tests/run/native_ptr/qa_mem_edge.ax`: Verifies:
  - Zero-count memory intrinsics (`ptr_copy` with count=0, `ptr_copy_nonoverlapping` with count=0, `ptr_write_bytes` with count=0).
  - Identical pointer copy (`src == dst`) for `ptr_copy`.
  - Multi-byte element scaling in `ptr_write_bytes` (`[4]i32` with count=2 writing 8 bytes `0x12121212`).
  - Correct `needs_drop` behavior on struct types with nested Drop vs non-Drop fields.

### Findings
None.

## Files changed
- tests/run/native_ptr/qa_mem_edge.ax

VERDICT: PASS round=0
