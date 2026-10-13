# QA Report: T061a — Minimal raw pointers, unsafe blocks and memory intrinsics

## Round 0

### Summary
Independent verification of task T061a (Minimal raw pointers, unsafe blocks and memory intrinsics). Built and tested exclusively inside snapshot `build-snap-T061a/`. All acceptance criteria independently verified; 0 build warnings; archcheck clean; full test suite passes. Boundary tests added for memory intrinsics and null pointer dereference oracle detection.

### Checks Performed & Evidence

1. **Change set & path validation**:
   - Command: `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T061a`
   - Result: 0 REFUSED lines initially against engineer changes. All modified files (`types/`, `own/unsafe/`, `mir/`, `interp/`, `tests/`) strictly within task `paths` and `locks`.

2. **Snapshot Build**:
   - Command: `cmake -S build-snap-T061a/bootstrap/axiom0 -B build-snap-T061a/build -G Ninja -DCMAKE_C_COMPILER=gcc && cmake --build build-snap-T061a/build`
   - Result: Build succeeded with 0 warnings.

3. **Architecture Boundary Check**:
   - Command: `python tools/archcheck.py` (run inside snapshot)
   - Result: `archcheck: 141 files scanned, 0 violations`

4. **Acceptance Criteria Verification**:
   - **Pointer operations & run tests**:
     - `run/ptr/linked_list.ax`: Manual linked list over array buffer passes.
     - `run/ptr/sum_walk.ax`: Pointer walk summing array elements passes.
     - `run/ptr/field_write.ax`: Struct field write through raw pointer passes.
     - `run/ptr/layout_intrinsics.ax`: `size_of`, `align_of`, and `needs_drop` match scalar, struct, and array layout.
     - `run/ptr/drop_in_place.ax`: `drop_in_place<T>` invokes destructor on target place.
     - `run/ptr/arena_align.ax`: Pointer-to-usize alignment math and round-trip access passes.
   - **Unsafe block & fn enforcement (UI tests)**:
     - `ui/ptr/addrof_outside_unsafe.ax`: reports `AX_UNSAFE_REQUIRED` on `address_of` outside unsafe.
     - `ui/ptr/arith_outside_unsafe.ax`: reports `AX_UNSAFE_REQUIRED` on pointer arithmetic outside unsafe.
     - `ui/ptr/call_outside_unsafe.ax`: reports `AX_UNSAFE_REQUIRED` on call to `unsafe fn` outside unsafe.
     - `ui/ptr/deref_outside_unsafe.ax`: reports `AX_UNSAFE_REQUIRED` on pointer dereference outside unsafe.
   - **Interpreter Oracle (UB detection)**:
     - `run/ptr/oracle_oob.ax`: out-of-bounds pointer read caught (exit 125, `AX_UNSAFE_INTERP_UB`).
     - `run/ptr/oracle_dangling.ax`: use-after-free / dangling access caught (exit 125, `AX_UNSAFE_INTERP_UB`).
     - `run/ptr/oracle_misaligned.ax`: unaligned pointer read caught (exit 125, `AX_UNSAFE_INTERP_UB`).
     - `run/ptr/oracle_null.ax` (QA added): null pointer dereference caught (exit 125, `AX_UNSAFE_INTERP_UB`).
   - **Memory manipulation intrinsics**:
     - `run/ptr/mem_intrinsics.ax` (QA added): `ptr_copy_nonoverlapping`, `ptr_write_bytes`, and overlapping `ptr_copy` pass.

5. **Full Suite Execution**:
   - Command: `python tools/axtest.py --compiler build/axiom0.exe` (run inside snapshot)
   - Result: `TOTAL 1252 PASS 1196 FAIL 0 SKIP 56 XFAIL 0`
   - Zero crashes, zero unexpected failures, zero regressions.

### Boundary Cross-Check Tests Added
- `tests/run/ptr/mem_intrinsics.ax`: Verifies `ptr_copy_nonoverlapping`, `ptr_write_bytes`, and `ptr_copy` with overlapping source and destination buffers.
- `tests/run/ptr/oracle_null.ax`: Verifies interpreter UB oracle detection when dereferencing a null pointer (`null<T>()`).

### Findings
None.

## Files changed
- tests/run/ptr/mem_intrinsics.ax
- tests/run/ptr/oracle_null.ax

VERDICT: PASS round=0
