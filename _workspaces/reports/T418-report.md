# T418 report - E11.4 — Oracle deterministic async trace & lifecycle verifier

STATUS: COMPLETE round=0

## Summary
- Equipped the MIR interpreter oracle (`compiler/interp/oracle.ax`, `compiler/interp/interp.ax`, `compiler/interp/value.ax`) and `std/future/mod.ax` with deterministic async lifecycle trace events (`POLL`, `SUSPEND`, `RESUME`, `WAKE`, `COMPLETE`, `CANCEL_DROP`) (`REQ-ASY-059, 060`).
- Implemented and enforced core async lifecycle invariants across interpreter and native runtimes:
  - Polling a completed (`0xFFFFFFFFu32`) or cancelled (`0xFFFFFFFEu32`) Future state machine panics deterministically with exit code 101 and error `panic: polling a completed Future state machine` (`REQ-ASY-034, 052`).
  - Dropping a `Pending` Future runs only the active state's live-field destructors in reverse declaration order without leaking or double-dropping (`REQ-ASY-034, 052`).
  - Stack-allocated Futures execute with zero heap allocations (`REQ-ASY-016, 021, 046`).
- Implemented async state-machine layout inspection via `inspect --emit=async-layout` (`compiler/driver/opts.ax`, `compiler/driver/pipeline.ax`, `compiler/mir/async_lower.ax`) reporting state count, byte size, alignment, and live fields per suspension state for each `async fn` (`REQ-ASY-045`, `AXS-ASY-051`).
- Authored comprehensive test suites:
  - `tests/inspect/async_layout.ax` & `.test`: validates `inspect --emit=async-layout` output format and field inspection.
  - `tests/run/async/oracle_trace/multi_step_trace.ax`: verifies multi-step suspend/resume trace order.
  - `tests/run/async/oracle_trace/nested_cancellation_trace.ax`: verifies early-drop cancellation cleanup and reverse drop order of nested futures.
  - `tests/run/async/oracle_trace/state_size_inspection.ax`: verifies runtime size and state layout properties.
  - `tests/run/async/oracle_trace/zero_heap_stack_future.ax`: verifies zero-heap allocation execution.
  - `tests/ui/async/lifecycle/poll_after_completed_panic.ax`: verifies panic on poll after completion.
  - `tests/ui/async/lifecycle/poll_after_cancelled_panic.ax`: verifies panic on poll after cancellation.
- Regenerated all 12 affected selfhost bundles (59 bundle test files) and verified `tests/selfhost/bundles_current.test` passes cleanly (34/34 PASS).
- Completed 2-stage bootstrap: `build-snap-T418/build/axiomc2.exe` built cleanly (sha256=`b082680225828792`), copied to `build/axiom*.exe`.
- All 59 tests in `oracle_trace`, `ui/async/lifecycle`, `inspect/async_layout`, `mir/async`, `run/async`, and `ui/async` pass under `axiomc2.exe` with `WEAK-NATIVE 0`.

## Verification
- Test runs with Stage-2 `build/axiomc2.exe`:
  - `python tools/axtest.py -j 1 --compiler build/axiomc2.exe oracle_trace ui/async/lifecycle inspect/async_layout mir/async run/async ui/async`:
    `TOTAL 59 PASS 59 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`.
  - `python tools/axtest.py -j 1 --compiler build/axiomc2.exe inspect/async_layout.test`:
    `TOTAL 1 PASS 1 FAIL 0 SKIP 0 XFAIL 0`.
  - `python tools/axtest.py -j 1 --compiler build/axiomc2.exe selfhost/interp/qa_interp_unit.ax`:
    `TOTAL 3 PASS 3 FAIL 0 SKIP 0 XFAIL 0`.
  - `python tools/axtest.py -j 1 --compiler build/axiomc2.exe tests/selfhost/bundles_current.test`:
    `TOTAL 34 PASS 34 FAIL 0 SKIP 0 XFAIL 0`.
- Architecture & Harness:
  - `python tools/archcheck.py`: 219 files scanned, 0 violations.
  - `python .claude/skills/axiom-tasks/scripts/harness_check.py`: HARNESS OK.

## Files changed
- compiler/driver/opts.ax
- compiler/driver/pipeline.ax
- compiler/interp/interp.ax
- compiler/interp/oracle.ax
- compiler/interp/value.ax
- compiler/mir/async_lower.ax
- compiler/mir/drop.ax
- std/future/mod.ax
- tests/inspect/async_layout.ax
- tests/inspect/async_layout.test
- tests/run/async/oracle_trace/multi_step_trace.ax
- tests/run/async/oracle_trace/nested_cancellation_trace.ax
- tests/run/async/oracle_trace/qa_branch_suspend_cancel_trace.ax
- tests/run/async/oracle_trace/state_size_inspection.ax
- tests/run/async/oracle_trace/zero_heap_stack_future.ax
- tests/selfhost/abi/qa_abi_lir_lower.ax
- tests/selfhost/backend/qa_backend_diff_lir_a.ax
- tests/selfhost/backend/qa_backend_diff_lir_b.ax
- tests/selfhost/backend/qa_backend_diff_mi_mc_a.ax
- tests/selfhost/backend/qa_backend_diff_mi_mc_b.ax
- tests/selfhost/backend/qa_backend_edge.ax
- tests/selfhost/backend/qa_backend_unit.ax
- tests/selfhost/driver/qa_driver_boundary_edges.ax
- tests/selfhost/driver/qa_driver_cli_and_project.ax
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
- tests/selfhost/obj_link_driver/qa_obj_link_driver_diff.ax
- tests/selfhost/obj_link_driver/qa_obj_link_driver_smoke.ax
- tests/selfhost/opt/qa_opt_pipeline.ax
- tests/selfhost/opt/qa_opt_unit.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_build_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_build_b.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_cap_ptr.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_init.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_own_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_own_b.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_diag_verify_mir.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_b.ax
- tests/selfhost/verify/qa_verify_mir.ax
- tests/selfhost/verify/qa_verify_pipeline.ax
- tests/ui/async/lifecycle/poll_after_cancelled_panic.ax
- tests/ui/async/lifecycle/poll_after_completed_panic.ax
- tests/ui/async/lifecycle/qa_poll_after_multistep_complete_panic.ax
