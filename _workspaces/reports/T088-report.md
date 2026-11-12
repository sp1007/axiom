# T088 report - E11.4 MIR state-machine lowering, cancellation drop glue & block_on

## Summary
- `compiler/mir/async_lower.ax` lowers every `async fn` (`Suspend` MIR) into a structural state
  machine: field 0 `state_tag: u32`, saved parameters, the locals that are maybe-initialized at and
  used after each suspension point (forward maybe-init dataflow + backward use liveness), and one
  in-flight sub-future per suspension point. The original body becomes the constructor
  (`tag = 0` + parameters moved in); a synthesized `poll` dispatches with `SwitchInt` on the tag
  (`0` unpolled, `1..N` resume points, `u32::MAX` completed, `u32::MAX-1` panicked/cancelled,
  otherwise `unreachable`) and is registered as `impl Future` for the coroutine type.
- Per-state cancellation drop glue (`compiler/mir/drop.ax` `drop_expand_coroutine`): dropping a
  suspended future in state `k` drops the in-flight sub-future first, then the live locals of
  state `k` in reverse declaration order; dropping a completed future is a no-op.
- `std/future/block_on.ax`: executor-free `block_on` with a stack-local no-op waker.
- Lowering runs before any other body is built (`session_lower_all_async`) in check / inspect /
  interp / native pipelines; sub-future `poll` calls and method calls on coroutine receivers are
  bound to the implementing impl. Lowered bodies are flagged (`MirBody.async_lowered`), verified on
  the source coroutine body (await checks, initialization, ownership) and elaborated/prepared once.

## Tests
- `tests/mir/async/*` (3) and `tests/run/async/*` (6, modes interp + native -O0/-O1): 21/21 PASS
  with Stage-1 `axiomc1` in `build-snap-T088`.
- Selfhost bundles regenerated via their `gen_*.py` (all `--check` up to date).
- Stage-2 bootstrap: built `build-snap-T088/build/axiomc2.exe` (7,787,008 bytes, sha256=`a03ac84a820d08c0`).
- Verification with Stage-2 `axiomc2.exe`:
  `python build-snap-T088/tools/axtest.py --compiler build-snap-T088/build/axiomc2.exe --root build-snap-T088 -j 1 mir/async run/async ui/async`
  Result: `TOTAL 34 PASS 34 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.
- Binaries synced: `build-snap-T088/build/axiom*.exe` copied to `build/`.

## Notes
- `std/future/mod.ax` now re-exports the prelude `Poll`/`Waker`/`Context`/`Future` (the
  duplicate definitions conflicted with the lang items) plus `block_on`.
- Added `compiler/interp/frame.ax`, `compiler/interp_opt/session.ax`, `compiler/own/init.ax` to
  the spec `locks:` (they were edited but missing, so the snapshot never received them).

## Files changed
- compiler/driver/pipeline.ax
- compiler/interp/frame.ax
- compiler/interp/interp.ax
- compiler/interp_opt/session.ax
- compiler/lir/builder.ax
- compiler/mir/async_lower.ax
- compiler/mir/builder.ax
- compiler/mir/drop.ax
- compiler/mir/mir.ax
- compiler/mir/mod.ax
- compiler/own/init.ax
- compiler/own_mir_verify/session.ax
- compiler/traits/solver.ax
- compiler/types/layout.ax
- compiler/verify/verifier.ax
- std/future/block_on.ax
- std/future/mod.ax
- tests/mir/async/async_cancellation_drop.ax
- tests/mir/async/async_cancellation_drop.test
- tests/mir/async/async_lower_basic.ax
- tests/mir/async/async_lower_basic.test
- tests/mir/async/async_lower_multistep.ax
- tests/mir/async/async_lower_multistep.test
- tests/run/async/await_chain.ax
- tests/run/async/block_on_basic.ax
- tests/run/async/cancellation_drop.ax
- tests/run/async/custom_future_pending.ax
- tests/run/async/loop_branch_await.ax
- tests/run/async/qa_multi_pending_branch_loop_state.ax
- tests/run/async/qa_nested_cancel_reverse_drop_order.ax
- tests/run/async/try_early_exit.ax
- tests/selfhost/abi/qa_abi_boundary_seam.ax
- tests/selfhost/abi/qa_abi_lir_lower.ax
- tests/selfhost/abi/qa_abi_win64_classify.ax
- tests/selfhost/backend/gen_backend_tests.py
- tests/selfhost/backend/qa_backend_diff_lir_a.ax
- tests/selfhost/backend/qa_backend_diff_lir_b.ax
- tests/selfhost/backend/qa_backend_diff_mi_mc_a.ax
- tests/selfhost/backend/qa_backend_diff_mi_mc_b.ax
- tests/selfhost/backend/qa_backend_edge.ax
- tests/selfhost/backend/qa_backend_unit.ax
- tests/selfhost/cap/qa_own_cap.ax
- tests/selfhost/driver/gen_driver_tests.py
- tests/selfhost/driver/qa_driver_commands_a.ax
- tests/selfhost/driver/qa_driver_commands_b.ax
- tests/selfhost/driver/qa_driver_inspect_diff_a.ax
- tests/selfhost/driver/qa_driver_inspect_diff_b.ax
- tests/selfhost/drop/gen_drop_tests.py
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
- tests/selfhost/interp/gen_interp_tests.py
- tests/selfhost/interp/qa_interp_exec_a.ax
- tests/selfhost/interp/qa_interp_exec_b.ax
- tests/selfhost/interp/qa_interp_unit.ax
- tests/selfhost/interp_opt/gen_interp_opt_tests.py
- tests/selfhost/interp_opt/qa_interp_opt_diff_comptime_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_comptime_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_mir_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_mir_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_run_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_run_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_unit.ax
- tests/selfhost/isel/qa_frame_layout_and_verify.ax
- tests/selfhost/isel/qa_isel_diff_golden.ax
- tests/selfhost/isel/qa_isel_frame_seam_and_edge_cases.ax
- tests/selfhost/isel/qa_isel_instructions_and_abi.ax
- tests/selfhost/lir/gen_lir_tests.py
- tests/selfhost/lir/qa_lir_from_ax_a.ax
- tests/selfhost/lir/qa_lir_from_ax_b.ax
- tests/selfhost/lir/qa_lir_from_ax_c.ax
- tests/selfhost/lir/qa_lir_from_ax_d.ax
- tests/selfhost/lir/qa_lir_from_ax_e.ax
- tests/selfhost/lir/qa_lir_from_mir.ax
- tests/selfhost/lir/qa_lir_seam_edge.ax
- tests/selfhost/mir/gen_mir_tests.py
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
- tests/selfhost/own_mir_verify/gen_own_mir_verify_tests.py
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
- tests/selfhost/types/qa_types_layout.ax
- tests/selfhost/verify/gen_verify_tests.py
- tests/selfhost/verify/qa_verify_mir.ax
- tests/selfhost/verify/qa_verify_pipeline.ax
- _workspaces/tasks/doing/T088-async-fn-await-state-machine-lowering-single-threa.md
- _workspaces/reports/T088-report.md
- _workspaces/reports/T088-qa.md
