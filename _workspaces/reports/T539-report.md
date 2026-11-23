# T539 report

## Summary

Resolved `fullrun-4` regression R4 (`ui/method/inherent_methods_err.ax`: `Point.sum(10)` emitting `AX_SEC_CAPABILITY_FORGERY` instead of `AX_TYPE_MISMATCH`), introduced in `T517` (`4579f0ec`).

1. **`compiler/types/typeck.ax` (`tc_try_report_capability_forgery`)**:
   - Preserved `src_kind_code = 1u8` (`raw_ptr`) for `sk == TY_PTR` (`*const T`, `*mut T`) on both explicit casts (`is_explicit_cast == true`) and implicit coercions (`is_explicit_cast == false`).
   - Preserved `src_kind_code = 2u8` (`integer_addr`) on both explicit casts and implicit coercions for pointer-sized integer address types (`sk == TY_USIZE || sk == TY_ISIZE`) and raw address wrapper structs (`PhysAddr`, `VirtAddr`, `WasmAddr` via `sec_is_raw_addr_struct_name`).
   - Restricted non-address integer primitives (`i8..i128`, `u8..u128` other than `usize`/`isize`) and untyped integer literals (`TY_INT_VAR` via `is_intlike`) to set `src_kind_code = 2u8` only when `is_explicit_cast == true` (e.g., `10 as view<Point>`, `10i32 as mut_view<Point>`, `0u64 as FsCap`). On implicit coercions (`is_explicit_cast == false`), `tc_try_report_capability_forgery` returns `false` so `coerce` and `check_block` report standard `AX_TYPE_MISMATCH`.
2. **`tests/ui/security_profiles/capability_forgery_non_addr_int_coercion_neg.ax`**:
   - Added boundary UI regression coverage verifying:
     - Implicit coercions of `10`, `10i32`, `0u64`, and `1u8` to `view<Point>`, `mut_view<Point>`, and `FsCap` across UFCS/method calls (`Point.sum`, `Point.bump`, `p.use_cap`), function calls, `let` bindings, inner block tails, function-body block tails, and `return` emit `AX_TYPE_MISMATCH` (48 diagnostics).
     - Explicit casts (`10 as view<Point>`, `10i32 as mut_view<Point>`, `0u64 as FsCap`, `1u8 as view<Point>`) and both explicit casts and implicit coercions of `usize`, `isize`, `*const Point`, `*mut Point`, `PhysAddr`, `VirtAddr`, and `WasmAddr` to `view<Point>`, `mut_view<Point>`, `FsCap`, and `NetCap` emit `AX_SEC_CAPABILITY_FORGERY` (33 diagnostics).
3. **`tests/ui/method/inherent_methods_err.ax`**:
   - Left untouched and verified passing as written.

## Files changed

- `compiler/types/typeck.ax`
- `tests/ui/security_profiles/capability_forgery_non_addr_int_coercion_neg.ax`

## Verification

All builds and tests executed inside isolated snapshot `build-snap-T539/` (`HEAD c9e00e2262ad`):

- Stage-2/3 fixed-point build (`python tools/build_axiomc.py --out build --root . --stage 2`):
  - `FIXED-POINT (O1) OK`: `sha256(axiomc2_O1) == sha256(axiomc3_O1) == e3e39aba18d21b40a5daffd9c5f7f79c090271f7504155c1240b2f958b549558` (8,687,104 bytes)
  - `STAGE0-GUARD OK`: `axiomc1` and seeded `B` produced byte-identical `.exe` on all 6 smoke programs
- Targeted UI & security profile suite (`python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal --no-cache -j 2 -v ui/method/inherent_methods_err.ax --filter ui/security_profiles`):
  - `TOTAL 18 PASS 18 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`
- Task gate (`python tools/taskgate.py --task T539 --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`):
  - `TOTAL 183 PASS 182 FAIL 0 SKIP 1 XFAIL 0` (`exit=0`)
  - `BASELINE OK`, `Failing ids: none`
  - `WEAK-NATIVE: 3 in the run; 0 in the task's own/changed tests`
  - `archcheck: clean (exit 0) archcheck: 232 files scanned, 0 violations`

## Spec deviations

none

STATUS: COMPLETE round=0
