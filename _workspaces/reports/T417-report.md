# T417 Report — Live-across-await analysis, view & guard rejection across await, and Future Send derivation

## Summary

Implemented task **T417** (Milestone **E11.4**, Phase P11), establishing the live-across-await dataflow analysis in xiomc to compute live state at .await suspension points, reject iew<T>, mut_view<T>, and synchronous lock guards crossing .await, and derive Future: Send strictly from live-across-await state per spec/SPEC-33-async.md (REQ-ASY-024..033, REQ-ASY-042..043, REQ-ASY-053, REQ-ASY-077, REQ-ASY-160, REQ-CONC-010, REQ-CONC-017, REQ-CONC-048, AXS-ASY-031, AXS-EXT-044):

1. **Await Lowering to MIR Suspend Terminator (compiler/mir/mir.ax, compiler/mir/builder.ax)**:
   - Added MIR_TERM_SUSPEND: u8 = 7u8 representing .await coroutine suspension points (AXS-EXT-044).
   - Reused existing MirTerminator fields (drop_flag for suspension point ID, drop_place for future operand, destination for output place, call_target for resume BB, and call_unwind for cleanup/drop BB) to preserve strict binary and struct layout compatibility across all compiler optimization passes.
   - Lowered HIR_EXPR_AWAIT to MIR_TERM_SUSPEND with automatic pre-suspension drop elaboration for dead locals (REQ-ASY-024, 033).
   - Unwrapped 
et_ty of _0 local for async functions from TY_COROUTINE to inner output type.

2. **MIR Verification & Live-Across-Await Analysis (compiler/verify/verifier.ax, compiler/own/cap.ax)**:
   - Integrated MIR_TERM_SUSPEND handling across terminator verification, CFG edge propagation, predecessor indexing, postorder traversal, and ownership analysis.
   - Unwrapped TY_COROUTINE when checking _0 return compatibility against async function return signatures.
   - Implemented erify_own_async_checks and erify_type_contains_view to reject iew<T>, mut_view<T>, and types containing views live across .await with AX_ASYNC_VIEW_ACROSS_AWAIT (158u32, REQ-ASY-028..031). Also rejected sync fn parameters containing views when the function contains .await.
   - Implemented erify_type_is_guard to reject synchronous lock guards (MutexGuard, RwLockReadGuard, RwLockWriteGuard, SpinLockGuard, etc.) and @no_suspend_hold types live across .await with AX_ASYNC_GUARD_ACROSS_AWAIT (159u32, REQ-CONC-010, 017, 048, REQ-ASY-053).
   - Populated coroutine rgs and rg_count with parameters and $igcup_k 	ext{LiveAcross}(SP_k)$ for auto-trait solving (REQ-ASY-025).

3. **Auto-Trait Solving & Send/Share Derivation (compiler/traits/solver.ax, compiler/types/typeck.ax, compiler/driver/pipeline.ax)**:
   - Marked synchronous lock guards and @no_suspend_hold types during typecheck (	c_mark_guard_structs).
   - In 	ype_satisfies_auto_trait: enforced that TY_COROUTINE is unconditionally !Share (uto_kind == 2), while Send (uto_kind == 1) requires that inner return type and all live-across-await types in rgs implement Send (REQ-ASY-042, 043, 077).
   - In emit_conc_bound_diag: emitted AX_ASYNC_FUTURE_NOT_SEND (160u32) naming the non-Send local and suspension point when a non-Send type is live across .await.
   - In compiler/driver/pipeline.ax: added pipe_check_spawn_send to validate Future: Send bounds on async boundaries. Ensured unconditional JSON diagnostic rendering on --json even for clean builds (exit 0).

4. **UI Test Suites**:
   - 	ests/ui/async/borrow_across_await/:
     * orrow_across_await_neg.ax: rejects view held across .await (AX_ASYNC_VIEW_ACROSS_AWAIT).
     * mut_view_across_await_neg.ax: rejects mut_view held across .await.
     * stored_view_across_await_neg.ax: rejects struct containing view held across .await.
     * param_view_across_await_neg.ax: rejects view parameter in async function with .await.
     * orrow_confined_pos.ax: verifies view confined strictly before .await or re-borrowed after .await is accepted.
   - 	ests/ui/async/lock_guard_await/:
     * lock_guard_mutex_neg.ax: rejects MutexGuard held across .await (AX_ASYNC_GUARD_ACROSS_AWAIT).
     * lock_guard_rwlock_neg.ax: rejects RwLockReadGuard and RwLockWriteGuard held across .await.
     * lock_guard_no_suspend_hold_neg.ax: rejects custom @no_suspend_hold structs held across .await.
     * lock_guard_dropped_pos.ax: verifies guard dropped before .await is accepted.
   - 	ests/ui/async/send_bounds/:
     * send_bounds_pos.ax: verifies Future with Send locals live across .await satisfies Send.
     * send_bounds_neg.ax: rejects Future with non-Send raw pointer live across .await passed to spawn<Fut: Future + Send> (AX_ASYNC_FUTURE_NOT_SEND).

5. **Self-Host Regeneration & Stage-2 Native Verification**:
   - Regenerated affected selfhost test bundles (qa_mir_builder_and_drop_*, qa_verify_mir, qa_own_cap, qa_traits_solver_mono, etc.).
   - Verified that undles_current.test passes 34/34.
   - Built optimized Stage-2 native binary (xiomc2.exe, 7.6MB).
   - All 57 tests passed under xiomc2.exe:
     * 11/11 async UI tests (	ests/ui/async/*).
     * 34/34 current bundles (undles_current.test).
     * 12/12 individual selfhost smoke suites (cap, own, 	raits, erify).

## Verification

- python build-snap-T417/tools/axtest.py -j 1 --root build-snap-T417 --build-dir build-snap-T417/build --compiler build-snap-T417/build/axiomc2.exe --exclude-requires axiom0-internal ui/async bundles_current.test selfhost/cap/qa_own_cap.ax selfhost/own/qa_own_init.ax selfhost/traits/qa_traits_solver_mono.ax selfhost/verify/qa_verify_mir.ax -> TOTAL 57 PASS 57 FAIL 0 SKIP 0 XFAIL 0 (WEAK-NATIVE 0).
- python tools/archcheck.py -> 218 files scanned, 0 violations.
- python .claude/skills/axiom-tasks/scripts/reqcov.py --strict -> requirements: 32309, gaps: 0 / COVERAGE OK.
- python .claude/skills/axiom-tasks/scripts/harness_check.py -> HARNESS OK.
- python .claude/skills/axiom-tasks/scripts/taskctl.py changes T417 -> 0 REFUSED lines, 0 UNLISTED lines.

## Files changed

- compiler/driver/pipeline.ax
- compiler/mir/builder.ax
- compiler/mir/mir.ax
- compiler/own/cap.ax
- compiler/traits/solver.ax
- compiler/types/typeck.ax
- compiler/verify/verifier.ax
- tests/selfhost/abi/qa_abi_lir_lower.ax
- tests/selfhost/backend/gen_backend_tests.py
- tests/selfhost/backend/qa_backend_diff_lir_a.ax
- tests/selfhost/backend/qa_backend_diff_lir_b.ax
- tests/selfhost/backend/qa_backend_diff_mi_mc_a.ax
- tests/selfhost/backend/qa_backend_diff_mi_mc_b.ax
- tests/selfhost/backend/qa_backend_edge.ax
- tests/selfhost/backend/qa_backend_unit.ax
- tests/selfhost/cap/qa_own_cap.ax
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
- tests/selfhost/interp/qa_interp_exec_a.ax
- tests/selfhost/interp/qa_interp_exec_b.ax
- tests/selfhost/interp/qa_interp_unit.ax
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
- tests/selfhost/lir/qa_lir_from_mir.ax
- tests/selfhost/lir/qa_lir_seam_edge.ax
- tests/selfhost/mir/qa_mir_builder_and_drop_a.ax
- tests/selfhost/mir/qa_mir_builder_and_drop_b.ax
- tests/selfhost/mir/qa_mir_builder_and_drop_c.ax
- tests/selfhost/mir/qa_mir_text_roundtrip.ax
- tests/selfhost/obj_link_driver/qa_obj_link_driver_diff.ax
- tests/selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax
- tests/selfhost/opt/gen_opt_tests.py
- tests/selfhost/opt/qa_opt_pipeline.ax
- tests/selfhost/opt/qa_opt_unit.ax
- tests/selfhost/own/qa_own_init.ax
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
- tests/selfhost/verify/gen_verify_tests.py
- tests/selfhost/verify/qa_verify_mir.ax
- tests/selfhost/verify/qa_verify_pipeline.ax
- tests/ui/async/borrow_across_await/borrow_across_await_neg.ax
- tests/ui/async/borrow_across_await/borrow_confined_pos.ax
- tests/ui/async/borrow_across_await/mut_view_across_await_neg.ax
- tests/ui/async/borrow_across_await/param_view_across_await_neg.ax
- tests/ui/async/borrow_across_await/stored_view_across_await_neg.ax
- tests/ui/async/lock_guard_await/lock_guard_dropped_pos.ax
- tests/ui/async/lock_guard_await/lock_guard_mutex_neg.ax
- tests/ui/async/lock_guard_await/lock_guard_no_suspend_hold_neg.ax
- tests/ui/async/lock_guard_await/lock_guard_rwlock_neg.ax
- tests/ui/async/send_bounds/send_bounds_neg.ax
- tests/ui/async/send_bounds/send_bounds_pos.ax

## Status

STATUS: COMPLETE round=0
