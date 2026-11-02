# T163 Report: Stage 1 Final Suite Fixes (InterpValue, Typeck Box, and Native Timeout)

## Summary

Resolved the 3 root causes behind the 8 failing test files (11 entries out of 2,887 active entries) uncovered by the `T086` Stage-1 full test suite verification:

1. **Port MIR interpreter `InterpValue` 256-byte capacity and non-colliding synthetic address space (`compiler/interp/value.ax`, `compiler/interp/interp.ax`, `compiler/interp/frame.ax`)**:
   - Expanded `InterpValue.vals` from `[8]u64` (64 bytes) to `[32]u64` (256 bytes), matching the bootstrap C interpreter's `uint64_t vals[32]` in `bootstrap/axiom0/src/interp/host.h:57`.
   - Updated `interp_val_zero`, `interp_val_u64`, `interp_zero_val`, `interp_copy_val`, and all `InterpValue` literal initializers in `compiler/interp/interp.ax` to `[0u64; 32]`. This eliminates silent 64-byte truncation when passing > 64-byte structs by value in `eval_call` (`MirOperand` at 88 bytes, `Diagnostic` at 104 bytes, and `ConstEvalResult` at 80 bytes).
   - Moved `INTERP_SYNTH_BASE_RUNTIME` from `0x10000000u64` (256 MB) to `0x4000000000000000u64` and `INTERP_SYNTH_BASE_COMPTIME` from `0x20000000u64` to `0x5000000000000000u64` (above the 48-bit/57-bit x86_64 user-space virtual address range), and compacted dead stack local entries whose address was never taken (`alloc_id == 0u32`) in `frame_cleanup` (`compiler/interp/frame.ax`). Because `axiomc1.exe` is linked by `compiler/link/pe.ax` without `IMAGE_DLLCHARACTERISTICS_HIGH_ENTROPY_VA`, Windows `GetProcessHeap()` allocates heap segments in the low 32-bit range (`0x00500000 .. 0x7FFF0000`), which previously collided with `[INTERP_SYNTH_BASE_RUNTIME, ctx.next_synth_addr)` during large selfhost `[interp]` tests and caused `interp_resolve_synth_ptr` to rewrite real host heap pointers to unrelated interpreter allocations.

2. **Typeck finalization of `TY_PTR` / `TY_STRUCT` / `TY_ENUM` and MIR verifier ADT compatibility (`compiler/types/typeck.ax`, `compiler/verify/verifier.ax`)**:
   - Extended the in-place interner resolution loop in `finalize_types` (`compiler/types/typeck.ax`) to resolve `TY_PTR` (`pointee`), `TY_STRUCT` (`args` and `fields`), and `TY_ENUM` (`args` and `variant_fields`) via `resolve_deep_ty`, in addition to `TY_TUPLE`, `TY_ARRAY`, and `TY_SLICE`.
   - Previously, unannotated generic struct paths in function signatures (such as `fn drop(self: mut_view<Box>)` and `pub fn box_new<T>(val: T) -> Box` in `tests/std/alloc/qa_box.ax`) created `TY_STRUCT` entries (`Box<?var#0>`) and field `TY_PTR` entries (`*mut ?var#0`) in the interner during Pass 1b whose `TY_VAR` arguments were unified with `T` (`TY_PARAM(0)`) during Pass 2, but were never resolved in-place in the interner by `finalize_types` before `cx.type_vars` was freed. During monomorphization (`compiler/traits/mono.ax`), `subst_ty` only substitutes `TY_PARAM`s, leaving stale `TY_VAR` references in cloned `Drop::drop` bodies and causing `verify_mir_body` to fail.
   - Because `finalize_types` updates existing `AxType` entries in-place without allocating new `TypeId`s in the interner, all `tests/thir` dump tests remain byte-for-byte unchanged.
   - Also extended `verify_types_compatible` (`compiler/verify/verifier.ax`) to check structural compatibility of `TY_STRUCT` and `TY_ENUM` with identical `def` and compatible `args`.

3. **Test timeout directive for `tests/run/native_ptr/write_bytes_1mb.ax`**:
   - Added `// timeout: 120` to `tests/run/native_ptr/write_bytes_1mb.ax` so compiling a 1 MB local array `[0; 1048576]` under an unoptimized `-O0` `axiomc1.exe` binary does not hit the default 10s timeout.

4. **Selfhost bundles**:
   - Regenerated all affected selfhost bundles (`34/34` `bundles_current.test` PASS).

## Files changed

- `compiler/interp/frame.ax`
- `compiler/interp/interp.ax`
- `compiler/interp/value.ax`
- `compiler/types/typeck.ax`
- `compiler/verify/verifier.ax`
- `tests/run/native_ptr/write_bytes_1mb.ax`
- `tests/selfhost/backend/qa_backend_diff_lir_a.ax`
- `tests/selfhost/backend/qa_backend_diff_lir_b.ax`
- `tests/selfhost/backend/qa_backend_diff_mi_mc_a.ax`
- `tests/selfhost/backend/qa_backend_diff_mi_mc_b.ax`
- `tests/selfhost/backend/qa_backend_edge.ax`
- `tests/selfhost/backend/qa_backend_unit.ax`
- `tests/selfhost/drop/qa_drop_d01.ax`
- `tests/selfhost/drop/qa_drop_d02.ax`
- `tests/selfhost/drop/qa_drop_d03.ax`
- `tests/selfhost/drop/qa_drop_d04.ax`
- `tests/selfhost/drop/qa_drop_d05.ax`
- `tests/selfhost/drop/qa_drop_d06.ax`
- `tests/selfhost/drop/qa_drop_d07.ax`
- `tests/selfhost/drop/qa_drop_d09.ax`
- `tests/selfhost/drop/qa_drop_d10.ax`
- `tests/selfhost/drop/qa_drop_d11.ax`
- `tests/selfhost/drop/qa_drop_d12.ax`
- `tests/selfhost/interp/qa_interp_exec_a.ax`
- `tests/selfhost/interp/qa_interp_exec_b.ax`
- `tests/selfhost/interp/qa_interp_unit.ax`
- `tests/selfhost/interp_opt/qa_interp_opt_diff_comptime_a.ax`
- `tests/selfhost/interp_opt/qa_interp_opt_diff_comptime_b.ax`
- `tests/selfhost/interp_opt/qa_interp_opt_diff_mir_a.ax`
- `tests/selfhost/interp_opt/qa_interp_opt_diff_mir_b.ax`
- `tests/selfhost/interp_opt/qa_interp_opt_diff_run_a.ax`
- `tests/selfhost/interp_opt/qa_interp_opt_diff_run_b.ax`
- `tests/selfhost/interp_opt/qa_interp_opt_unit.ax`
- `tests/selfhost/lir/qa_lir_from_ax_a.ax`
- `tests/selfhost/lir/qa_lir_from_ax_b.ax`
- `tests/selfhost/lir/qa_lir_from_ax_c.ax`
- `tests/selfhost/lir/qa_lir_from_ax_d.ax`
- `tests/selfhost/lir/qa_lir_from_ax_e.ax`
- `tests/selfhost/mir/qa_mir_builder_and_drop_a.ax`
- `tests/selfhost/mir/qa_mir_builder_and_drop_b.ax`
- `tests/selfhost/mir/qa_mir_builder_and_drop_c.ax`
- `tests/selfhost/obj_link_driver/qa_obj_link_driver_diff.ax`
- `tests/selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax`
- `tests/selfhost/opt/qa_opt_pipeline.ax`
- `tests/selfhost/opt/qa_opt_unit.ax`
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_build_a.ax`
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_build_b.ax`
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_cap_ptr.ax`
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_init.ax`
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_own_a.ax`
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_own_b.ax`
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_verify_mir.ax`
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_a.ax`
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_b.ax`
- `tests/selfhost/traits/qa_traits_solver_mono.ax`
- `tests/selfhost/typeck/qa_typeck_a.ax`
- `tests/selfhost/typeck/qa_typeck_b.ax`
- `tests/selfhost/typeck/qa_typeck_c.ax`
- `tests/selfhost/typeck_traits/qa_typeck_traits_a.ax`
- `tests/selfhost/typeck_traits/qa_typeck_traits_b.ax`
- `tests/selfhost/typeck_traits/qa_typeck_traits_c.ax`
- `tests/selfhost/verify/qa_verify_mir.ax`
- `tests/selfhost/verify/qa_verify_pipeline.ax`

## Verification

- **Stage-1 compiler (`build-snap-T163/build/axiomc1.exe`) rebuilt from updated `axiomc` bundle**:
  - `0 errors` (`axiom0.exe build --std-root=std --stack-reserve=67108864 -o build-snap-T163/build/axiomc1.exe`).
- **All 8 target test files from `T086` + selfhost `[interp]` stress tests under `build-snap-T163/build/axiomc1.exe` (`-j 1`)**:
  - `std/alloc/qa_box.ax` (`[interp]`, `[native]`, `[native-O1]`) -> PASS
  - `run/native_ptr/write_bytes_1mb.ax` (`[native]`, `[native-O1]`) -> PASS
  - `selfhost/drop/qa_drop_d05.ax` (`[interp]`, `[native]`, `[native-O1]`) -> PASS
  - `selfhost/drop/qa_drop_d06.ax` (`[interp]`, `[native]`, `[native-O1]`) -> PASS
  - `selfhost/hir/qa_hir_desugar_and_drop.ax` (`[interp]`, `[native]`, `[native-O1]`) -> PASS
  - `selfhost/interp_opt/qa_interp_opt_diff_mir_a.ax` (`[interp]`, `[native]`, `[native-O1]`) -> PASS
  - `selfhost/lexer/qa_lexer_corpus_neg_b.ax` (`[interp]`, `[native]`, `[native-O1]`) -> PASS
  - `selfhost/own_mir_verify/qa_own_mir_diff_diag_verify_mir.ax` (`[interp]`, `[native]`, `[native-O1]`) -> PASS
  - `selfhost/own_mir_verify/qa_own_mir_diff_build_a.ax` (`[interp]`, `[native]`, `[native-O1]`) -> PASS
  - `selfhost/typeck/qa_typeck_c.ax` (`[interp]`, `[native]`, `[native-O1]`) -> PASS
  - `selfhost/typeck_traits/qa_typeck_traits_b.ax` (`[interp]`, `[native]`, `[native-O1]`) -> PASS
  - Total: `32/32 PASS, 0 FAIL`.
- **Selfhost bundle freshness (`bundles_current.test`)**:
  - `34/34 PASS, 0 FAIL`.
- **Regression suites under `build-snap-T163/build/axiom0.exe` (`--exclude-requires axiom0-internal -j 1`)**:
  - `typeck`, `verify`, `ui`, `selfhost/typeck`: `393/393 PASS, 0 FAIL`.
  - `thir`: `28/28 PASS, 0 FAIL` (zero `TypeId` shift in THIR dump tests).
- **Mandatory Gates**:
  - `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T163` -> `63` allowed files, `0 REFUSED`.
  - `python tools/gatecheck.py --no-run` -> `MS-P1..MS-P9 PASS`.
  - `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` -> `COVERAGE OK`.
  - `python .claude/skills/axiom-tasks/scripts/harness_check.py` -> `HARNESS OK`.
  - `python tools/archcheck.py` -> `0 violations`.

STATUS: COMPLETE
