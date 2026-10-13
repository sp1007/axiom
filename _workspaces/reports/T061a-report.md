# T061a Report - Minimal raw pointers, unsafe blocks and memory intrinsics (self-host subset)

## Goal Achieved
Implemented the complete self-host minimal unsafe toolkit for raw pointer types (`*const T`, `*mut T`), `unsafe { }` blocks and `unsafe fn` checker, 15 memory layout and manipulation intrinsics, and the interpreter memory model with synthetic addresses, bounds checking, alignment verification, and undefined behavior (UB) detection.

## Implementation Details
1. **Type Checker & Diagnostics (`bootstrap/axiom0/src/types/typeck.c`, `types.h`, `diag/codes/UNSAFE.def`)**:
   - Implemented pointer type validation, raw pointer dereferencing, assignment mutability checking, pointer comparisons (`==`, `!=`, `<`, `<=`, `>`, `>=`), and casts (`ptr as usize`, `usize as ptr`, `*mut T as *const T`).
   - Integrated resolution of `@intrinsic` declarations for memory intrinsics into `AX_TY_BUILTIN_*` type kinds.
   - Enforced type unifications and coercions for `AX_TY_PTR`.

2. **Unsafe Checker (`bootstrap/axiom0/src/own/unsafe/unsafe.c`, `unsafe.h`, `driver/pipeline.c`)**:
   - Added the unsafe checking pass running in pipeline stage `AX_STAGE_UNSAFE` (between type checking and MIR building).
   - Validates that unsafe operations (raw pointer dereferencing, pointer arithmetic, and calls to `unsafe fn`) occur strictly inside `unsafe` blocks or `unsafe fn` bodies, reporting diagnostic `AX_UNSAFE_REQUIRED` on violations.
   - Bypasses borrow/lifetime outlive constraints for raw pointer address-of intrinsics.

3. **MIR Lowering (`bootstrap/axiom0/src/mir/build/builder.c`, `mir/drop/drop.c`, `drop.h`)**:
   - Lowered `address_of` and `address_of_mut` via place temporary and pointer cast without triggering borrow-check invalidations.
   - Lowered pointer arithmetic (`p + n`, `p - n`) to `AX_TY_BUILTIN_PTR_ADD` and `AX_TY_BUILTIN_PTR_SUB` terminators.
   - Integrated compile-time evaluation and runtime call dispatch for `size_of`, `align_of`, `needs_drop`, `null`, `null_mut`, and `is_null`.
   - Updated MIR drop elaboration to preserve pointer drop semantics and ignore raw pointer types during automatic drops.

4. **Interpreter Memory Model & UB Oracle (`bootstrap/axiom0/src/interp/interp.c`)**:
   - Implemented synthetic 16-byte aligned base addressing (`0x10000000` base with redzone gaps).
   - Tracked all allocations with allocation ID, base synthetic address, size, alignment, host pointer, and call depth.
   - Implemented UB oracle reporting `AX_UNSAFE_INTERP_UB` (exit code 125) on null pointer dereference, misaligned pointer access, unmapped pointer access, use-after-free, and out-of-bounds pointer reads/writes.
   - Implemented runtime memory intrinsics: `ptr_copy`, `ptr_copy_nonoverlapping` (with overlap UB detection), `ptr_write_bytes`, `drop_in_place`, and `needs_drop`.
   - Two-pass pointer lookup in `find_synth_addr` prioritizing strictly interior addresses over one-past-the-end addresses.

## Test Results
- Full pointer suite passes: `TOTAL 26 PASS 14 FAIL 0 SKIP 12 XFAIL 0`.
- All UI tests pass: `addrof_outside_unsafe.ax`, `arith_outside_unsafe.ax`, `call_outside_unsafe.ax`, `deref_outside_unsafe.ax`.
- All run tests pass in interpreter:
  - `linked_list.ax`
  - `sum_walk.ax`
  - `field_write.ax`
  - `layout_intrinsics.ax`
  - `drop_in_place.ax`
  - `arena_align.ax`
- All oracle error cases pass (exit 125):
  - `oracle_oob.ax`
  - `oracle_dangling.ax`
  - `oracle_misaligned.ax`
- Zero compiler warnings; archcheck clean on all T061a files.

## Files changed
- bootstrap/axiom0/src/diag/codes/UNSAFE.def
- bootstrap/axiom0/src/driver/pipeline.c
- bootstrap/axiom0/src/interp/interp.c
- bootstrap/axiom0/src/mir/build/builder.c
- bootstrap/axiom0/src/mir/drop/drop.c
- bootstrap/axiom0/src/mir/drop/drop.h
- bootstrap/axiom0/src/own/unsafe/unsafe.c
- bootstrap/axiom0/src/own/unsafe/unsafe.h
- bootstrap/axiom0/src/types/typeck.c
- bootstrap/axiom0/src/types/types.h
- tests/run/ptr/arena_align.ax
- tests/run/ptr/drop_in_place.ax
- tests/run/ptr/field_write.ax
- tests/run/ptr/layout_intrinsics.ax
- tests/run/ptr/linked_list.ax
- tests/run/ptr/oracle_dangling.ax
- tests/run/ptr/oracle_misaligned.ax
- tests/run/ptr/oracle_oob.ax
- tests/run/ptr/sum_walk.ax
- tests/ui/ptr/addrof_outside_unsafe.ax
- tests/ui/ptr/arith_outside_unsafe.ax
- tests/ui/ptr/call_outside_unsafe.ax
- tests/ui/ptr/deref_outside_unsafe.ax

STATUS: COMPLETE round=0
