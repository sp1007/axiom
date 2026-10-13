# T057 - Closures, capture inference, function values

## Files changed
- bootstrap/axiom0/src/driver/mono.c
- bootstrap/axiom0/src/interp/interp.c
- bootstrap/axiom0/src/mir/build/builder.c
- bootstrap/axiom0/src/mir/drop/drop.c
- bootstrap/axiom0/src/own/own.c
- bootstrap/axiom0/src/resolve/resolve.c
- bootstrap/axiom0/src/syntax/parse.c
- bootstrap/axiom0/src/types/interner.c
- bootstrap/axiom0/src/types/layout/layout.c
- bootstrap/axiom0/src/types/typeck.c
- bootstrap/axiom0/src/types/types.h
- bootstrap/axiom0/src/verify/verify.c
- tests/run/closure/capture_modes.ax
- tests/run/closure/closure_types.ax
- tests/run/closure/fn_pointers.ax
- tests/run/closure/fn_traits.ax
- tests/run/closure/generic_fns.ax
- tests/run/closure/qa_mixed_captures.ax
- tests/run/closure/qa_move_capture.ax
- tests/run/closure/syntax.ax
- tests/ui/closure/capture_conflict_mut.ax
- tests/ui/closure/capture_use_after_move.ax
- tests/ui/closure/capturing_to_fn_ptr.ax
- tests/ui/closure/fn_trait_reject_mut.ax
- tests/ui/closure/qa_closure_move_twice.ax
- tests/ui/closure/reserved_move.ax
- tests/ui/closure/type_mismatch.ax
- tests/ui/closure/uncallable_generic.ax

## Scope and Test Mapping

| Scope Area | Positive Test | Negative Test | Status |
| :--- | :--- | :--- | :--- |
| 1. Closure syntax → HIR (`|x| expr`, `|x, y| { ... }`, explicit return types) | `tests/run/closure/syntax.ax` | `tests/ui/closure/reserved_move.ax` | PASS |
| 2. Capture inference (`copy`, `view`, `mut_view`, `move` by usage) | `tests/run/closure/capture_modes.ax`, `tests/run/closure/qa_mixed_captures.ax`, `tests/run/closure/qa_move_capture.ax` | `tests/ui/closure/capture_conflict_mut.ax`, `tests/ui/closure/capture_use_after_move.ax`, `tests/ui/closure/qa_closure_move_twice.ax` | PASS |
| 3. Unnameable closure types (distinct anonymous types per closure, non-interchangeable) | `tests/run/closure/closure_types.ax` | `tests/ui/closure/type_mismatch.ax` | PASS |
| 4. Fn-like traits (`Fn`, `FnMut`, `FnOnce`, `Callable` satisfaction and invocation) | `tests/run/closure/fn_traits.ax` | `tests/ui/closure/fn_trait_reject_mut.ax` | PASS |
| 5. Function pointers and non-capturing closure coercion to `fn` pointers | `tests/run/closure/fn_pointers.ax` | `tests/ui/closure/capturing_to_fn_ptr.ax` | PASS |
| 6. Passing closures to generic functions with trait bounds | `tests/run/closure/generic_fns.ax` | `tests/ui/closure/uncallable_generic.ax` | PASS |

## Test Suite Results
- Closure test suite:
  - Executed via `python tools/axtest.py --compiler build-snap-T057/build/axiom0.exe --filter closure -v`
  - Total: 33 tests (17 executed interp/ui, 16 skipped native per `native-after: T059`), 17 PASS, 0 FAIL, 16 SKIP, 0 XFAIL.
- Full compiler test suite:
  - Executed via `python tools/axtest.py --compiler build-snap-T057/build/axiom0.exe`
  - Total: 1223 tests, 1181 PASS, 0 FAIL, 42 SKIP, 0 XFAIL.
- Unit tests:
  - Executed via `build-snap-T057/build/axiom0-unit.exe`
  - Total: 71 tests, 0 failed.
- Build status:
  - Clean build completed with 0 warnings, 0 errors.

## Round 1 Fixes

### Architectural Violations Addressed
1. **INV-LAYER-001 violation in `bootstrap/axiom0/src/types/typeck.c:3`**:
   - `types` layer included `own/own.h` to call `ax_type_is_copy()`.
   - Fixed by moving `ax_type_is_copy` declaration to `bootstrap/axiom0/src/types/types.h` and implementation to `bootstrap/axiom0/src/types/interner.c`.
   - Removed duplicate implementation from `bootstrap/axiom0/src/own/own.c`.
   - Removed `#include "own/own.h"` from `bootstrap/axiom0/src/types/typeck.c`.
2. **INV-LAYER-006 violation in `bootstrap/axiom0/src/types/typeck.c:3352`**:
   - Mutable function-local static `static uint32_t s_closure_id = 1;` was used to generate unique closure IDs.
   - Fixed by storing `next_closure_id` in `TypeckCtx` (initialized to 1 in `ax_typeck`), and incrementing `cx->next_closure_id++`.

### Invariants Verification
- Executed `python tools/archcheck.py` on both main tree and snapshot:
  - 139 files scanned, 0 violations.

## Round 2 Fixes

### Compiler Warnings Addressed
1. **`-Wsometimes-uninitialized` warning in `bootstrap/axiom0/src/interp/interp.c:538`**:
   - Variable `field_ty` was declared uninitialized and conditionally assigned in an `if-else` chain, triggering Clang `-Wsometimes-uninitialized` under `-Werror`.
   - Fixed by initializing `TypeId field_ty = TypeId_none();` at declaration.
   - Verified warning-free syntax check under Clang with `-Wall -Wextra -Wpedantic -Werror` on all 11 modified C source files.
   - Clean rebuild under GCC/Ninja with 0 warnings, 0 errors.

### Verification
- Unit tests: 71 tests, 0 failed (`build-snap-T057/build/axiom0-unit.exe`).
- Closure test suite: 33 tests, 17 PASS, 0 FAIL, 16 SKIP, 0 XFAIL (`axtest.py --filter closure`).
- Full compiler test suite: 1223 tests, 1181 PASS, 0 FAIL, 42 SKIP, 0 XFAIL (`axtest.py`).
- Architecture invariants: 139 files scanned, 0 violations (`archcheck.py`).

STATUS: COMPLETE round=2
