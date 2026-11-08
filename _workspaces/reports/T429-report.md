# T429 Report — E11.2: Sub-64-bit atomic MI size preservation & struct-embedded Atomic<T> prelude resolution

## Summary

Resolved both compiler issues blocking epic `E11.2` (conformance task `T409`) per `spec/SPEC-31-atomics.md` (`REQ-CONC-134`, `REQ-ATM-022`, `AXS-ATM-005`, `AXS-ATM-010`, `AXS-ATM-012`, `AXS-ATM-018`):
1. **Sub-64-bit atomic MI operand width preservation (`compiler/driver/pipeline.ax`)**: Removed unconditional overwriting of `inst.size = 8u8` in `driver_emit_build_mi_body_obj` (lines 1858–1864) and `driver_emit_objmodel_filtered_ex` (line 4004), preserving the exact operand widths (`1u8`, `2u8`, `4u8`) set by instruction selection for `X64_MI_XCHG`, `X64_MI_LOCK_XADD`, `X64_MI_ATOMIC_RMW_LOOP`, and `X64_MI_LOCK_CMPXCHG`. This ensures native x86-64 code emits width-exact `BYTE PTR`, `WORD PTR`, and `DWORD PTR` instructions without `REX.W`, preventing adjacent memory clobbering and fixing negative signed sub-64-bit CAS.
2. **Prelude-first registration & alias caching guards (`compiler/types/typeck.ax`)**: Reorganized `typeck_pass1a` into a clean two-pass sequence: Pass 1a (prelude) registers prelude/std structs (`Atomic<T>`) and enums with their full field definitions, and resolves prelude type aliases (`AtomicBool`, `AtomicU32`, etc.); Pass 1a (user) registers all user structs, enums, and generic parameters in their exact declaration order. Additionally guarded `lookup_path_type_by_name` and `lookup_path_type` against caching `t_error` for prelude aliases, completely resolving bogus `AX_TYPE_UNKNOWN_FIELD` errors and restoring method and `view<Atomic<T>>` dispatch without disrupting self-host struct layout or recursion.
3. **Tests & verification**:
   - Added `tests/run/atomics/sub_64_bit_widths.ax` and `tests/run/atomics/struct_embedded_atomics.ax`, verifying width-exact memory safety, negative signed CAS loops, struct-embedded atomics, and `view<Atomic<T>>` helper calls across `--interp` and native modes.
   - Regenerated all 56 affected selfhost bundles across `tests/selfhost/` to maintain 100% freshness (`bundles_current.test` passes 34/34).
   - Rebuilt `build-snap-T429/build/axiomc2.exe` from Stage 0 and Stage 1.
   - Confirmed both read-only `T409` QA repros (`qa_signed_cas_const_ptr_and_sb_relaxed.ax` and `qa_struct_embedded_atomics_and_view_methods.ax`) pass 100% cleanly.

## Key Changes & Architecture

1. **`compiler/driver/pipeline.ax`**:
   - Lines 1858–1864 (`driver_emit_build_mi_body_obj`): Replaced `if opc != X64_MI_MOV && opc != X64_MI_CMP { (*inst).size = 8u8; } else if (*inst).size == 0u8 { (*inst).size = 8u8; }` with `if (*inst).size == 0u8 { (*inst).size = 8u8; }`.
   - Line 4004 (`driver_emit_objmodel_filtered_ex`): Replaced unconditional `(*inst).size = 8u8;` with `if (*inst).size == 0u8 { (*inst).size = 8u8; }`.
   - Instruction selection (`compiler/backend/x86_64/isel.ax`) sets `inst.size` according to `LirInst.size`. Preserving `inst.size` allows `x64_encode_mi_inst_obj` to emit size-exact 1-byte (`AL`, `lock cmpxchg BYTE PTR`, `xchg BYTE PTR`), 2-byte (`AX`, `lock cmpxchg WORD PTR`), and 4-byte (`EAX`, `lock cmpxchg DWORD PTR`) instructions.

2. **`compiler/types/typeck.ax`**:
   - In `lookup_path_type_by_name` (lines 3549, 3613) and `lookup_path_type` (line 3837), added guards `if !is_error(mut_view(*cx), (TypeId { v: computed.v })) && computed.v != 0u32` before caching `item_type` on alias AST items, ensuring transient unresolutions do not poison type interning.
   - Implemented `tc_item_is_prelude_or_std`, `tc_register_single_struct`, `tc_register_single_enum`, and `tc_resolve_type_alias`.
   - In `typeck_pass1a`:
     - **Pass 1a (prelude)**: Scans for prelude/std items, registering prelude/std structs (specifically `@lang("atomic") pub struct Atomic<T> { pub v: T }`), enums, and resolving prelude type aliases (`AtomicBool`, `AtomicU32`, etc.) before any user structs are inspected.
     - **Pass 1a (user)**: In declaration order, registers all user structs, enums, and generic parameters. When user struct fields reference `Atomic<T>` or prelude aliases, `lookup_path_type_by_name` successfully locates the valid, already-registered `TypeId`, enabling accurate field typing and allowing method call resolution on struct fields.

3. **`tests/run/atomics/`**:
   - `sub_64_bit_widths.ax`: Exercises `AtomicBool`, `AtomicU8`, `AtomicU16`, `AtomicU32`, `AtomicI8`, `AtomicI16`, `AtomicI32`, verifying contiguous array and struct memory preservation (no neighbor byte clobbering), negative signed CAS (`compare_exchange` and `compare_exchange_weak` retry loop), and all RMW arithmetic/bitwise operations.
   - `struct_embedded_atomics.ax`: Exercises structs embedding `Atomic<T>`, prelude atomic aliases, nested structs with atomics, direct method calls on struct fields, and passing `view<Atomic<T>>` to free functions.

## Files changed

- compiler/driver/pipeline.ax
- compiler/types/typeck.ax
- tests/run/atomics/struct_embedded_atomics.ax
- tests/run/atomics/sub_64_bit_widths.ax
- tests/selfhost/backend/qa_backend_diff_lir_a.ax
- tests/selfhost/backend/qa_backend_diff_lir_b.ax
- tests/selfhost/backend/qa_backend_diff_mi_mc_a.ax
- tests/selfhost/backend/qa_backend_diff_mi_mc_b.ax
- tests/selfhost/backend/qa_backend_edge.ax
- tests/selfhost/backend/qa_backend_unit.ax
- tests/selfhost/driver/qa_driver_commands_a.ax
- tests/selfhost/driver/qa_driver_commands_b.ax
- tests/selfhost/driver/qa_driver_inspect_diff_a.ax
- tests/selfhost/driver/qa_driver_inspect_diff_b.ax
- tests/selfhost/drop/qa_drop_d01.ax
- tests/selfhost/drop/qa_drop_d02.ax
- tests/selfhost/drop/qa_drop_d03.ax
- tests/selfhost/drop/qa_drop_d04.ax
- tests/selfhost/drop/qa_drop_d05.ax
- tests/selfhost/drop/qa_drop_d06.ax
- tests/selfhost/drop/qa_drop_d07.ax
- tests/selfhost/drop/qa_drop_d09.ax
- tests/selfhost/drop/qa_drop_d10.ax
- tests/selfhost/drop/qa_drop_d11.ax
- tests/selfhost/drop/qa_drop_d12.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_comptime_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_comptime_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_mir_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_mir_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_run_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_run_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_unit.ax
- tests/selfhost/lir/qa_lir_from_ax_a.ax
- tests/selfhost/lir/qa_lir_from_ax_b.ax
- tests/selfhost/lir/qa_lir_from_ax_c.ax
- tests/selfhost/lir/qa_lir_from_ax_d.ax
- tests/selfhost/lir/qa_lir_from_ax_e.ax
- tests/selfhost/mir/qa_mir_builder_and_drop_a.ax
- tests/selfhost/mir/qa_mir_builder_and_drop_b.ax
- tests/selfhost/mir/qa_mir_builder_and_drop_c.ax
- tests/selfhost/obj_link_driver/qa_obj_link_driver_diff.ax
- tests/selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax
- tests/selfhost/opt/qa_opt_pipeline.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_build_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_build_b.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_cap_ptr.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_init.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_own_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_own_b.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_verify_mir.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_b.ax
- tests/selfhost/traits/qa_traits_solver_mono.ax
- tests/selfhost/typeck/qa_typeck_a.ax
- tests/selfhost/typeck/qa_typeck_b.ax
- tests/selfhost/typeck/qa_typeck_c.ax
- tests/selfhost/typeck_traits/qa_typeck_traits_a.ax
- tests/selfhost/typeck_traits/qa_typeck_traits_b.ax
- tests/selfhost/typeck_traits/qa_typeck_traits_c.ax
- tests/selfhost/verify/qa_verify_pipeline.ax

STATUS: COMPLETE round=0
