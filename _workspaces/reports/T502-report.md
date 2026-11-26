# T502 Report — E13.1 Oracle strict-provenance & UB detector

## Summary

The MIR oracle (`--interp`) now tracks byte initialisation of heap blocks, maps `@addr`/`@at` regions on demand, gives functions deterministic
code addresses, and diagnoses forged pointers and writes to read-only memory. Every `AX_UNSAFE_INTERP_UB` carries a structured
`data.ub_kind` entry. The latent out-of-bounds read that the detector found in `compiler/target/x64/frame.ax` is fixed per ADR-0052.

## Design (decisions made)

1. **Uninitialised reads (UB-04).** `heap_alloc`/`heap_realloc` blocks get a shadow byte array (`InterpAlloc.init`, 1 = initialised).
   - Typed loads whose source place goes through a raw pointer run with `ub_load_ctx` set. The validated block is remembered in `ub_last_alloc`
     and `interp_check_init_read` checks the exact final range.
   - Every other validated raw access (stores, `ptr_copy`, `ptr_write_bytes`, host buffers) marks its range initialised. This over-approximates
     initialisation, so it can miss a bug but never invents one.
   - A block reached through a `view`/`mut_view` stops being tracked. `heap_realloc` keeps the copied prefix's state; the grown tail is uninitialised.
2. **Fixed-address map (REQ-OWNER-008).** `InterpCtx.fixed` holds `@addr` regions outside the synthetic range, backed by zeroed host memory.
   - An integer-to-pointer cast to an address in no live allocation or region is accepted only if it binds a placement; anything else reports
     "invalid provenance: pointer forged from an integer address".
   - Item-scope placements are matched by the constant of the hidden `__ax_addr_n` item of a `static`. Block-scope placements are matched by the span
     of the cast statement against the HIR `let`/`static` statements that carry `addr_sym` (collected lazily, once).
   - A null or misaligned dynamic address and a partial overlap of regions report UB-12. Overlays of one address share storage.
3. **Function addresses.** A function value cast to an integer is the `@addr(A)` constant if the function is placed, else
   `0x1000_0000 + 0x100 * symbol_id`. `interp_fn_from_code_addr` is the inverse. Code addresses cannot be dereferenced.
4. **UB-07.** Constant aggregates and string-literal blocks are `INTERP_PERM_READONLY`; a store into one reports "write to read-only memory".
5. **`data.ub_kind`.** `interp_report_ub` attaches a `DiagDataEntry` `ub_kind` (string) to the diagnostic: `dangling_or_freed`, `null_deref`,
   `invalid_provenance`, `out_of_bounds`, `misaligned_access`, `uninitialized_read`, `write_to_readonly`, `overlapping_copy`, `invalid_fixed_addr`
   and `data_race` (all four race/atomic messages). Free of a non-heap block maps to `dangling_or_freed`. Nine `pin_ub_kind_*.test` files pin the
   JSON (`"data":{"ub_kind":"..."}`) for each kind except `data_race`, which is pinned by the existing atomics tests' exit code only.
6. **ADR-0052 fix (`frame.ax`).** Added `X64_FRAME_META_WORDS = 5` and one helper `frame_alloc_slot_offsets(arena, slot_count)` that allocates
   `slot_count + 5` words and zero-fills the trailer. `x64_frame_lower_baseline_in_arena`, `x64_frame_lower_raw` and `x64_frame_lower_opt_in_arena`
   all use it; no other `slot_offsets` allocation remains. The helper never returns null. Baseline and raw call it only when there are slots (null
   otherwise, as before); the opt builder calls it unconditionally, as it allocated before, so native output is unchanged. `X64_FRAME_META_WORDS`
   is not re-exported from `compiler/target/x64/mod.ax` (not in this task's locks).
7. **Out of scope / moved.** UB-06 is T542. Item-scope `@addr(A) static S: T = init` is rejected by the T501 typeck (T526/T528/T540).

## Round 1 (QA F1: padding false positive)

- `interp_check_init_read_ty` now checks a typed load by type: scalars check their whole range; structs, tuples and arrays recurse into their
  real fields (`interp_walk_init`, using `type_field_offset`), so padding bytes never trap. Enums, closures and coroutines are not inspected
  (a false negative, never a false positive). Used by `exec_assign_use` and `eval_operand_u64/u128/u64_raw`.
- `interp_aggregate_copied`: after `*dst = *src` of a struct or tuple into a tracked heap block, the copy's field bytes are marked
  initialised and its padding is reset to uninitialised, so the per-byte state is that of the fields.
- New tests: `ok_padding_nested_struct.ax` (nested `@repr(C)` structs, padding at two levels, load + copy), `ok_padding_array_of_structs.ax`
  (`[3]E` of padded structs, load + copy + element reads) and `ub_uninit_nested_field.ax` (a real nested field never written is still UB-04).
  QA's `qa_ok_padding_load/store/ptr_copy` and all other `qa_*` tests pass in every mode.

## Spec deviations

None found: the only other site flagged by the detector in the run set was the `frame.ax` one fixed here. The periodic full run may still find more.

## Verification

Runs in `build-snap-T502` on HEAD 93488dd9 (snapshot refreshed with the frame.ax lock file):
- Stage 1 → 2 → 3: `FIXED-POINT (O1) OK` (sha256 02f4bcbd...), `BUILD-AXIOMC OK`.
- `axtest --filter run/unsafe`: `TOTAL 51 PASS 43 FAIL 0 SKIP 8` (28 run tests plus 9 `ub_kind` pins; the 8 skips are the native modes of the four
  `native-after: T504` tests). The `ok_*` and `roundtrip_local_addr` tests also pass natively.
- `taskgate T502`: `TOTAL 330 PASS 310 FAIL 0 SKIP 20`, `BASELINE OK`, archcheck clean, smoke-check OK, exit 0. This includes
  `selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax` (interp, native, native-O1) and the regenerated selfhost bundles.

## Round 1 verification

Snapshot refreshed on HEAD 93488dd9, stage 2 rebuilt (`FIXED-POINT (O1) OK`, `BUILD-AXIOMC OK`).
- `axtest --filter run/unsafe`: `TOTAL 80 PASS 72 FAIL 0 SKIP 8` (every `qa_*` test and the three new round-1 tests pass in interp, native and
  native-O1; the 8 skips are the `native-after: T504` tests).
- `taskgate T502`: `TOTAL 362 PASS 342 FAIL 0 SKIP 20`, `BASELINE OK`, archcheck clean, smoke-check OK, exit 0.

## Files changed
- compiler/interp/interp.ax
- compiler/interp/mod.ax
- compiler/interp/oracle.ax
- compiler/interp/value.ax
- compiler/target/x64/frame.ax
- tests/run/unsafe/oracle_ub/ok_init_tracking.ax
- tests/run/unsafe/oracle_ub/ok_padding_array_of_structs.ax
- tests/run/unsafe/oracle_ub/ok_padding_nested_struct.ax
- tests/run/unsafe/oracle_ub/ok_provenance_roundtrip.ax
- tests/run/unsafe/oracle_ub/pin_ub_kind_dangling_or_freed.test
- tests/run/unsafe/oracle_ub/pin_ub_kind_invalid_fixed_addr.test
- tests/run/unsafe/oracle_ub/pin_ub_kind_invalid_provenance.test
- tests/run/unsafe/oracle_ub/pin_ub_kind_misaligned_access.test
- tests/run/unsafe/oracle_ub/pin_ub_kind_null_deref.test
- tests/run/unsafe/oracle_ub/pin_ub_kind_out_of_bounds.test
- tests/run/unsafe/oracle_ub/pin_ub_kind_overlapping_copy.test
- tests/run/unsafe/oracle_ub/pin_ub_kind_uninitialized_read.test
- tests/run/unsafe/oracle_ub/pin_ub_kind_write_to_readonly.test
- tests/run/unsafe/oracle_ub/qa_ok_fieldwise_array_struct.ax
- tests/run/unsafe/oracle_ub/qa_ok_padding_load.ax
- tests/run/unsafe/oracle_ub/qa_ok_padding_ptr_copy.ax
- tests/run/unsafe/oracle_ub/qa_ok_padding_store.ax
- tests/run/unsafe/oracle_ub/qa_ok_realloc_shrink_int_roundtrip.ax
- tests/run/unsafe/oracle_ub/qa_ok_static_mut_raw_write.ax
- tests/run/unsafe/oracle_ub/qa_pin_ub_kind_data_race.test
- tests/run/unsafe/oracle_ub/qa_pin_ub_kind_json_uninit_high_half.test
- tests/run/unsafe/oracle_ub/qa_ub_data_race.ax
- tests/run/unsafe/oracle_ub/qa_ub_uninit_struct_high_half.ax
- tests/run/unsafe/oracle_ub/roundtrip_dynamic_base_offset.ax
- tests/run/unsafe/oracle_ub/roundtrip_fn_addr.ax
- tests/run/unsafe/oracle_ub/roundtrip_local_addr.ax
- tests/run/unsafe/oracle_ub/roundtrip_overlay_shared.ax
- tests/run/unsafe/oracle_ub/roundtrip_static_const_addr.ax
- tests/run/unsafe/oracle_ub/ub_double_free.ax
- tests/run/unsafe/oracle_ub/ub_fixed_addr_misaligned.ax
- tests/run/unsafe/oracle_ub/ub_fixed_addr_null.ax
- tests/run/unsafe/oracle_ub/ub_fixed_addr_overlap.ax
- tests/run/unsafe/oracle_ub/ub_forged_fn_code.ax
- tests/run/unsafe/oracle_ub/ub_forged_literal.ax
- tests/run/unsafe/oracle_ub/ub_forged_neighbor.ax
- tests/run/unsafe/oracle_ub/ub_null_deref.ax
- tests/run/unsafe/oracle_ub/ub_oob_load_one_past_end.ax
- tests/run/unsafe/oracle_ub/ub_oob_ptr_arith.ax
- tests/run/unsafe/oracle_ub/ub_oob_store_heap.ax
- tests/run/unsafe/oracle_ub/ub_overlapping_copy.ax
- tests/run/unsafe/oracle_ub/ub_uaf_heap.ax
- tests/run/unsafe/oracle_ub/ub_uaf_realloc_stale.ax
- tests/run/unsafe/oracle_ub/ub_uaf_stack_escape.ax
- tests/run/unsafe/oracle_ub/ub_unaligned_load.ax
- tests/run/unsafe/oracle_ub/ub_unaligned_store.ax
- tests/run/unsafe/oracle_ub/ub_uninit_after_realloc.ax
- tests/run/unsafe/oracle_ub/ub_uninit_nested_field.ax
- tests/run/unsafe/oracle_ub/ub_uninit_read_heap.ax
- tests/run/unsafe/oracle_ub/ub_uninit_read_partial.ax
- tests/run/unsafe/oracle_ub/ub_write_readonly_const.ax

STATUS: COMPLETE round=1