# T423a report

## Summary
Fixed `drop_in_place<T>(p)` so that for every concrete type `T` with `needs_drop<T>() == true`, it runs the full recursive drop glue matching scope-end `DROP` (`SPEC-12 AXS-DROP-005`, `SPEC-54 AXS-PAN-010`):
- **Root cause**:
  1. `compiler/mir/builder.ax` (`mb_scan_or_rewrite_calls`) only rewrote `TY_BUILTIN_DROP_IN_PLACE` into a destructor call when `T` was a generic `TY_STRUCT` with its own `impl<...> Drop` (`mb_instantiate_drop_for_ty`), while `compiler/interp/interp.ax` (`find_drop_fn_for_type`) and `compiler/lir/builder.ax` (`find_drop_fn_sym_name`) only looked up a direct `Drop` impl on `T`. As a result, `drop_in_place<T>(p)` was a silent no-op for closures capturing droppable values, tuples, fixed arrays `[N]T`, and glue-only structs/enums without their own `Drop` impl, and skipped field destructors when a struct had both its own `Drop` impl and droppable fields.
  2. `compiler/traits/mono.ax`: `type_contains_param` did not inspect `TY_CLOSURE` capture/parameter/return types (so closures capturing generic parameters inside generic functions appeared concrete before substitution), and `subst_ty_enum_or_closure` mixed `closure_id` with checked `u32 * 31u32` multiplication (`cid_mix * 31u32`), panicking on arithmetic overflow when substituting multi-capture closures in generic functions.
  3. `compiler/interp/interp.ax`: `resolve_or_build_mir_body` checked `(*inst).mir_body != 0` instead of `> 1`, which would treat `mb_prepare_mono`'s `1` worklist sentinel as a `MirBody` pointer on on-demand resolution.
- **Fix**:
  1. `compiler/mir/builder.ax` (`mb_try_build_drop_in_place`, invoked on `TY_BUILTIN_DROP_IN_PLACE` in `mb_build_control_or_call_expr`): when the resolved pointee type `T` is concrete (`!type_contains_param`) and `mir_type_needs_drop_in(T, ...)` holds, lower `drop_in_place<T>(p)` into `_ptr = p; drop(*_ptr) -> next_bb` (`MIR_TERM_DROP` on the dereferenced `*mut T` temporary). `mb_scan_or_rewrite_calls` already enqueues all transitive monomorphized `Drop` impls for every `MIR_TERM_DROP` via `mb_enqueue_drop_insts_for_ty`, and `mir_drop_elaborate` (`drop_expand_block`) expands `drop(*_ptr)` identically for both `--interp` and native codegen: own `Drop` impl first when present, then fields in declaration order, closure `CAP_MOVE` captures in capture order, tuple elements, array elements `0..N`, active enum variant payload fields, and nested combinations, unconditionally (no drop flag on raw pointer `_ptr: *mut T`). Concrete types with `!needs_drop<T>()` and unspecialized generic bodies keep `TY_BUILTIN_DROP_IN_PLACE` as a no-op (preserving oracle raw-pointer validation and escape-promotion fast paths).
  2. `compiler/traits/mono.ax`: extended `type_contains_param` to walk `TY_CLOSURE` capture types, parameter types, and return type; replaced checked `cid_mix * 31u32` in `subst_ty_enum_or_closure` with wrapping 32-bit `mono_cid_mix`.
  3. `compiler/interp/interp.ax`: guarded `(*inst).mir_body` reuse in `resolve_or_build_mir_body` with `(mb_ptr as usize) > 1`.

## Files changed
- compiler/mir/builder.ax
- compiler/traits/mono.ax
- compiler/interp/interp.ax
- tests/run/drop_in_place_glue/closure_captures.ax
- tests/run/drop_in_place_glue/closure_capturing_box.ax
- tests/run/drop_in_place_glue/tuple_and_array.ax
- tests/run/drop_in_place_glue/struct_and_enum_glue.ax
- tests/run/drop_in_place_glue/no_drop_noop.ax
- tests/run/drop_in_place_glue/heap_cell_closure_and_tuple.ax

## Tests
All builds and test runs executed inside isolated snapshot `build-snap-T423a/` (`HEAD 4f2daaf08dc1`):
- Stage-2/Stage-3 self-host bootstrap (`python tools/build_axiomc.py --out build --root . --stage 2`):
  - `STAGE1 OK` (`29,724,672` bytes, `sha256=8f5f7cdb4578ee87`)
  - `STAGE2 (O1) OK` (`8,956,928` bytes, `sha256=556bd69e9f4b36f3`)
  - `STAGE3 (O1) OK` (`8,956,928` bytes, `sha256=556bd69e9f4b36f3`)
  - `FIXED-POINT (O1) OK`: `sha256(axiomc2_O1) == sha256(axiomc3_O1) == 556bd69e9f4b36f38d566bc37234d3be7f317c5730f154e9e8bdf421086da3ae`
  - `STAGE0-GUARD OK`: `axiomc1` and `B` produced byte-identical `.exe` on 6 smoke programs (`-O1`, incl. `Xin chào thế giới`)
- New task tests (`python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal --no-cache -j 2 run/drop_in_place_glue`):
  - `TOTAL 18 PASS 18 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0` (6 tests across `interp`, `native`, `native-O1`: 1- and 3-capture closures vs scope-drop order, closure in generic fn, closure capturing `HeapBox<T>`, tuple `(Guard, i64, Guard)`, `[2]Guard` and `[2](Guard, Guard)`, struct without `Drop`, enum variants, struct and generic struct with own `Drop` + `Guard` field, no-drop no-op types + copy-only closure, heap-allocated cells with re-init, and generic `fn kill<T>(p: *mut T)` across all cases).
- Mutation liveness check (in snapshot): mutated `D:62\n` -> `D:63\n` in `closure_captures.ax` -> `TOTAL 3 PASS 0 FAIL 3` (`interp`, `native`, `native-O1` all failed at byte 63); restored -> `TOTAL 3 PASS 3 FAIL 0`.
- Targeted suites (`python tools/axtest.py --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 std/fiber std/thread run/drop std/collections selfhost/mir selfhost/interp selfhost/lir`):
  - `TOTAL 325 PASS 319 FAIL 0 SKIP 0 XFAIL 6`, `WEAK-NATIVE 0` (`qa_fiber_drop` and all fiber/thread/drop/collections/selfhost mir+interp+lir groups PASS).
- Per-task gate (`python tools/taskgate.py --task T423a --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2`):
  - `TASKGATE T423a exit=0`: `TOTAL 531 PASS 529 FAIL 0 SKIP 2 XFAIL 0` (273 unique ids: 6 own, 245 affected, 32 smoke), `WEAK-NATIVE: 0` in own/changed tests, `BASELINE OK`, `Failing ids: none`, `archcheck: clean (232 files scanned, 0 violations)`, cache verification sample `20/58` `mismatch none`.

## Spec deviations
none

## Follow-ups
- `std/fiber/mod.ax`: once `T423a` is accepted and `std/fiber/mod.ax` is free, the temporary move-out workaround (`let _dead: F = *(c_ptr as *mut F);` in `fiber_trampoline` phase 2 and `Drop for Fiber`, ADR-0046 F1 workaround) can be simplified back to `drop_in_place<F>(c_ptr as *mut F);`.

STATUS: COMPLETE round=0