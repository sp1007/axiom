STATUS: COMPLETE round=0
# T403 Report - E11.1 Synchronization & Happens-Before Contracts in MIR Optimizer & Verifier

## Summary

Implemented synchronization barrier annotations and happens-before preservation contracts across the MIR representation, MIR optimizer passes (`const_fold`, `dce`, `cfg_simp`, `optir`), and MIR verifier (`E11.1`, `spec/SPEC-30-concurrency.md` §3.4 & §8, `0126`, `ACONC-27`, `ACONC-76`, `ACONCUR-190..191`, `ACONCUR-195..196`):

1. **MIR Synchronization & Memory-Barrier Classification (`compiler/mir/mir.ax`)**:
   - Added ordering and statement/terminator barrier predicates:
     - `mir_order_has_acquire(ord)` (`Acquire`, `AcqRel`, `SeqCst`) and `mir_order_has_release(ord)` (`Release`, `AcqRel`, `SeqCst`).
     - `mir_stmt_is_sync_barrier(st)`, `mir_stmt_is_acquire_barrier(st)`, and `mir_stmt_is_release_barrier(st)` classifying `MIR_STMT_ATOMIC` (`atomic_load`, `atomic_store`, `atomic_rmw`, `atomic_cmpxchg`, `atomic_cmpxchg_weak`, `atomic_fence`, `compiler_fence`, `spin_loop_hint`) as synchronization boundaries.
     - `mir_term_is_sync_barrier(term)` classifying `MIR_TERM_CALL` and `MIR_TERM_DROP` as potential inter-thread synchronization boundaries (`lock`/`unlock`/`spawn`/`join`/channel/condvar/barrier operations).
     - `mir_bb_has_sync_barrier(bb)` and `mir_body_has_sync_barrier(body)` for basic-block and function-body barrier queries.

2. **MIR Optimizer Happens-Before Preservation (`compiler/opt/{const_fold,dce,cfg_simp,mod}.ax`, `compiler/opt/optir/mod.ax`)**:
   - **Constant Folding (`compiler/opt/const_fold.ax`)**: Added `opt_stmt_is_sync_barrier` and `opt_term_is_sync_barrier`, guarding `opt_const_fold` so synchronization barrier statements are never folded or rewritten, while purely local constant expressions (`MIR_RVALUE_BINARY_OP`, `MIR_RVALUE_OVERFLOWS_BINARY_OP`, `MIR_RVALUE_UNARY_OP`) continue to fold cleanly.
   - **Dead Code Elimination (`compiler/opt/dce.ax`)**: Added `opt_place_has_deref`, `opt_operand_reads_deref`, `opt_rvalue_reads_deref`, and `opt_body_has_atomic_sync`. In functions containing atomic synchronization barriers (`MIR_STMT_ATOMIC`), dereference memory reads (`*p`) are preserved along with dereference stores and `MIR_STMT_ATOMIC` statements so ordinary loads/stores separated by synchronization barriers are never eliminated across happens-before boundaries.
   - **CFG Simplification (`compiler/opt/cfg_simp.ax`)**: Added `opt_cfg_bb_has_sync_barrier` and guarded linear basic-block merging so synchronization terminators (`MIR_TERM_CALL`, `MIR_TERM_DROP`) are never bypassed or collapsed across blocks.
   - **OptIR Lowering (`compiler/opt/optir/mod.ax`)**: Extended `optir_init_locals` and `optir_lower_mir_blocks` to scan `MIR_STMT_ATOMIC` operands/places and lower `MIR_STMT_ATOMIC` to `OPT_INST_ATOMIC` with `OPT_FLAG_SIDE_EFFECT | OPT_FLAG_MAY_LOAD | OPT_FLAG_MAY_STORE | OPT_FLAG_BARRIER`.

3. **Zero-Cost `Send`/`Share` Erasure & Deterministic Concurrency Verification (`compiler/verify/verifier.ax`)**:
   - Implemented `verify_mir_conc_erasure` (invoked from `verify_mir`), verifying that:
     - No MIR local in `body.locals` carries a runtime marker-trait (`HIR_ITEM_TRAIT`) representation (`ACONCUR-190..191`, `SPEC-30` `AXS-CONC-019`).
     - Functions with `Send`/`Share` generic bounds have `body.arg_count == verify_fn_param_count(func)`, ensuring zero hidden runtime witness parameters or descriptor arguments.
   - Tightened `MIR_STMT_ATOMIC` verification in `verify_mir_check_stmt` to reject out-of-range atomic opcodes (`aop > MIR_ATOMIC_SPIN_HINT`) and ensure 100% deterministic verification (`ACONCUR-196`).

4. **Tests & Self-Host Bundles (`tests/mir/concurrency/`, `tests/selfhost/`)**:
   - Added `-O0` (`inspect --emit=mir -O0`) and `-O1` (`inspect --emit=mir-opt -O1`) inspection tests (`sync_barrier_o0_baseline.{ax,test}`, `sync_barrier_opt_preserved.{ax,test}`), zero-cost `Send`/`Share` erasure inspection test (`send_share_zero_cost_erasure.{ax,test}`), and end-to-end execution test (`happens_before_sync_run.ax`).
   - Regenerated all affected self-host bundles under `tests/selfhost/`.

## Files changed
- `compiler/mir/mir.ax`
- `compiler/opt/cfg_simp.ax`
- `compiler/opt/const_fold.ax`
- `compiler/opt/dce.ax`
- `compiler/opt/mod.ax`
- `compiler/opt/optir/mod.ax`
- `compiler/verify/verifier.ax`
- `tests/mir/concurrency/happens_before_sync_run.ax`
- `tests/mir/concurrency/send_share_zero_cost_erasure.ax`
- `tests/mir/concurrency/send_share_zero_cost_erasure.test`
- `tests/mir/concurrency/sync_barrier_o0_baseline.ax`
- `tests/mir/concurrency/sync_barrier_o0_baseline.test`
- `tests/mir/concurrency/sync_barrier_opt_preserved.ax`
- `tests/mir/concurrency/sync_barrier_opt_preserved.test`
- `tests/selfhost/abi/qa_abi_lir_lower.ax`
- `tests/selfhost/backend/qa_backend_diff_lir_a.ax`
- `tests/selfhost/backend/qa_backend_diff_lir_b.ax`
- `tests/selfhost/backend/qa_backend_diff_mi_mc_a.ax`
- `tests/selfhost/backend/qa_backend_diff_mi_mc_b.ax`
- `tests/selfhost/backend/qa_backend_edge.ax`
- `tests/selfhost/backend/qa_backend_unit.ax`
- `tests/selfhost/bundle_common.py`
- `tests/selfhost/cap/qa_own_cap.ax`
- `tests/selfhost/driver/qa_driver_commands_a.ax`
- `tests/selfhost/driver/qa_driver_commands_b.ax`
- `tests/selfhost/driver/qa_driver_inspect_diff_a.ax`
- `tests/selfhost/driver/qa_driver_inspect_diff_b.ax`
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
- `tests/selfhost/lir/qa_lir_from_mir.ax`
- `tests/selfhost/lir/qa_lir_seam_edge.ax`
- `tests/selfhost/mir/qa_mir_builder_and_drop_a.ax`
- `tests/selfhost/mir/qa_mir_builder_and_drop_b.ax`
- `tests/selfhost/mir/qa_mir_builder_and_drop_c.ax`
- `tests/selfhost/mir/qa_mir_text_roundtrip.ax`
- `tests/selfhost/obj_link_driver/qa_obj_link_driver_diff.ax`
- `tests/selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax`
- `tests/selfhost/opt/qa_opt_pipeline.ax`
- `tests/selfhost/opt/qa_opt_unit.ax`
- `tests/selfhost/own/qa_own_init.ax`
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_build_a.ax`
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_build_b.ax`
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_cap_ptr.ax`
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_init.ax`
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_own_a.ax`
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_own_b.ax`
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_verify_mir.ax`
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_a.ax`
- `tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_b.ax`
- `tests/selfhost/verify/qa_verify_mir.ax`
- `tests/selfhost/verify/qa_verify_pipeline.ax`

## Verification

- `build-snap-T403/build/axiomc2.exe`: Stage-1 and Stage-2 (`-O1`) self-host build succeeded (`BUILD-AXIOMC OK`, `size=6888960`, `sha256=a6d77b66e11a4097b0a416266957b83a383235694a0ef376cd2bd1a5327bd49b`).
- `mir/concurrency` and `mir/atomics`: 10/10 PASS (`WEAK-NATIVE 0`).
- `selfhost/opt`, `selfhost/interp_opt`, `opt/`, `diff/opt/`, `run/intrinsics/assert_false.ax`, `run/intrinsics/panic_abort.ax`, `ui/intrinsics/unknown_intrinsic.ax`: PASS (`WEAK-NATIVE 0`).
- All 35 `tests/selfhost/*/gen_*.py --check` checks inside `build-snap-T403`: 0 differences.
- `python tools/archcheck.py`: 0 violations.
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T403`: verified clean.

STATUS: COMPLETE round=0
