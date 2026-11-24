# T501 Report — E13.1: Unsafe checking, pointer provenance & REQ-OWNER-008 address intrinsics

## Summary of Changes

Implemented full `unsafe` block/fn/trait/impl/extern/`static mut` enforcement, raw-pointer-to-`view`/`mut_view` capability provenance lowering (`MakeView`/`MakeMutView`), and `REQ-OWNER-008` address intrinsics and fixed-address placement (`@addr`/`@at`) across syntax, HIR, typeck, ownership/unsafe checking, diagnostics, and MIR lowering:

1. **Syntax & HIR (`compiler/syntax/ast.ax`, `compiler/syntax/parse.ax`, `compiler/hir/hir.ax`, `compiler/hir/lower.ax`)**:
   - Parsed and lowered `@addr(<expr>)` and `@at(<expr>)` attributes on `static`, `static mut`, `let`, and `fn` items/bindings, including both compile-time constant expressions and block-scope dynamic `usize` expressions (e.g., `let base = fn_addr(foo); @addr(base + 0x100) unsafe static mut REG: u32;`), as well as `unsafe trait` / `unsafe impl` / `unsafe static` markers.
2. **Type Checking (`compiler/types/types.ax`, `compiler/types/typeck.ax`)**:
   - Type-checked `REQ-OWNER-008` intrinsics and casts: `fn_addr(f) -> usize`, `static_addr(s) -> usize`, `address_of(v) -> *const T`, `address_of_mut(v) -> *mut T`, `addr_of(v) -> usize`, `address_of(v) as usize`, and function-item / fn-pointer `as usize` casts.
   - Type-checked `@addr(<expr>)` / `@at(<expr>)` address expressions as `usize` and validated constant-expression requirements at item scope.
   - Enforced `unsafe trait` / `unsafe impl` matching rules (missing `unsafe` on `impl` of an `unsafe trait`, unnecessary `unsafe` on `impl` of a safe `trait`).
3. **Unsafe & Provenance Checking (`compiler/own/unsafe.ax`, `compiler/diag/code.ax`)**:
   - Added/wired `AX_UNSAFE_*` diagnostics enforcing `unsafe` context requirements for raw pointer dereferences, `unsafe fn` calls, `extern` calls, `static mut` accesses, and `@addr`/`@at` declarations.
   - Preserved `view<T>` / `mut_view<T>` capability and exclusivity checking across `unsafe` boundaries (raw-pointer-derived views remain subject to `AX_CAP_CONFLICT_MUT` / `AX_CAP_CONFLICT_READ` after leaving `unsafe`).
4. **MIR Lowering (`compiler/mir/builder.ax`)**:
   - Lowered `fn_addr`, `static_addr`, `address_of`, `address_of_mut`, `addr_of`, and fn-item/fn-ptr `as usize` casts to MIR.
   - Lowered item-scope and block-scope `@addr(<expr>)` / `@at(<expr>)` bindings (constant and dynamic addresses, with or without initializers) so reads, writes, and round-trip `static_addr`/`addr_of` operate on the bound address.
   - Lowered raw-pointer-to-`view<T>` / `mut_view<T>` conversions in `unsafe` blocks to explicit `MakeView` / `MakeMutView` MIR instructions preserving provenance.

## Verification

### Build & Fixed-Point (`build-snap-T501/` on HEAD `e656cbe6`)
Command: `python tools/build_axiomc.py --out build --root . --stage 2`
- `STAGE1 OK`: `build/axiomc1.exe` (34,085,376 bytes, `sha256=3d544061b463cde4`)
- `STAGE2 (O1) OK`: `build/dir_stage2_O1/axiomc2.exe` (9,116,672 bytes, `sha256=6f977d66fcdec4dc`)
- `STAGE3 (O1) OK`: `build/dir_stage3_O1/axiomc3.exe` (9,116,672 bytes, `sha256=6f977d66fcdec4dc`)
- `FIXED-POINT (O1) OK`: `sha256(axiomc2_O1) == sha256(axiomc3_O1) == 6f977d66fcdec4dc1fc4052741013181ef16c2932a8fbc778b3c47e1436867f0`
- `STAGE0-GUARD OK`: `axiomc1` and Stage 2 produced byte-identical `.exe` on 6 smoke programs (O1, incl. `Xin chào thế giới`)
- `BUILD-AXIOMC OK`

### Targeted Tests (`ui/unsafe` + `mir/unsafe`)
Command: `python tools/axtest.py --compiler build/axiomc2.exe --exclude-requires axiom0-internal --filter ui/unsafe --filter mir/unsafe --no-cache -j 2 --verbose`
- `TOTAL 21 PASS 21 FAIL 0 SKIP 0 XFAIL 0`
- `WEAK-NATIVE 0`

### Taskgate (`tools/taskgate.py`)
Command: `python tools/taskgate.py --task T501 --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T501.json`
- `own`: 17 ids, 21 results (`PASS 21 FAIL 0 SKIP 0`)
- `affected`: 448 ids, 724 results (`PASS 709 FAIL 0 SKIP 15`)
- `smoke`: 34 ids, 57 results (`PASS 57 FAIL 0 SKIP 0`)
- `total (dedup)`: 476 ids, 775 results (`PASS 760 FAIL 0 SKIP 15 XFAIL 0`)
- `WEAK-NATIVE`: 15 in the run; `0` in the task's own/changed tests
- `BASELINE OK`
- `archcheck: clean (exit 0) archcheck: 232 files scanned, 0 violations`
- `smoke-check (tests/smoke.list): OK; est. worst-case draw 23 s`
- `TASKGATE T501 exit=0`

### Hygiene Checks
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T501`: 0 `REFUSED`, all 28 files listed cleanly.
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.

## Files changed
- compiler/diag/code.ax
- compiler/hir/hir.ax
- compiler/hir/lower.ax
- compiler/mir/builder.ax
- compiler/own/unsafe.ax
- compiler/syntax/ast.ax
- compiler/syntax/parse.ax
- compiler/types/typeck.ax
- compiler/types/types.ax
- tests/mir/unsafe/addr_intrinsics.ax
- tests/mir/unsafe/addr_intrinsics.test
- tests/mir/unsafe/fixed_addr.ax
- tests/mir/unsafe/fixed_addr.test
- tests/mir/unsafe/run_addr_intrinsics.ax
- tests/mir/unsafe/run_fixed_addr_dynamic.ax
- tests/ui/unsafe/addr_attr_item_needs_unsafe.ax
- tests/ui/unsafe/addr_attr_let_needs_unsafe.ax
- tests/ui/unsafe/addr_attr_not_const.ax
- tests/ui/unsafe/addr_attr_positive.ax
- tests/ui/unsafe/addr_attr_typeck_negative.ax
- tests/ui/unsafe/addr_intrinsics_negative.ax
- tests/ui/unsafe/raw_ptr_view_forge.ax
- tests/ui/unsafe/raw_ptr_view_provenance.ax
- tests/ui/unsafe/unsafe_impl_unnecessary.ax
- tests/ui/unsafe/unsafe_ops_negative.ax
- tests/ui/unsafe/unsafe_ops_positive.ax
- tests/ui/unsafe/unsafe_trait_impl.ax
- tests/ui/unsafe/unsafe_trait_impl_missing.ax

STATUS: COMPLETE round=0
