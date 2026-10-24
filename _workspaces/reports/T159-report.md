# T159 Report — `AX0-FIX-08`: MIR Verifier Missing-Drop and Double-Drop Checks on Real Bodies

## 1. Summary

Implemented `T159` (`AX0-FIX-08`) in lockstep across `bootstrap/axiom0` and `compiler/`:

1. **Driver pipeline ordering (`bootstrap/axiom0/src/driver/pipeline.c` and `compiler/driver/pipeline.ax`)**:
   - Moved `ax_verify_mir_own` / `verify_mir_own` so that it executes **after** drop elaboration (`ax_mir_drop_elaborate` / `mir_drop_elaborate`) on every lowered function body in the main pipeline, `run --interp` pre-pass, and monomorphization synthesis pass (`synth_fn`).
   - Added a `drop_elaborated` guard in `pipeline.c` so that `--stop-after=mir` skips `ax_mir_drop_elaborate` on the second verification pass instead of elaborating a second time.
2. **Drop-flag-aware ownership and drop verification (`bootstrap/axiom0/src/verify/verify.c` and `compiler/verify/verifier.ax`)**:
   - Removed the `func == NULL` suppression on `AX_VERIFY_MISSING_DROP` and `AX_VERIFY_DOUBLE_DROP` so that both diagnostics fire on real function bodies (`func != NULL`) after drop elaboration as well as on standalone `.mir` text bodies (`func == NULL`).
   - Extended the per-local dataflow lattice in `ax_verify_mir_own` / `verify_mir_own` to track flag-indexed ownership states (`F0` bits `0..2` for `flag == 0` and `F1` bits `3..5` for `flag == 1`, plus `ST_WAS_DROPPED` bit `6`):
     - Recognizes the `bb0` drop-flag prolog emitted by `ax_mir_drop_elaborate` / `mir_drop_elaborate` (`prolog_flags` consecutive `_flag_i = const 0|1` assignments matching the `drop_cnt` droppable locals `1 .. first_flag_loc - 1`), as well as explicit `drop_flag` annotations and hand-built `.mir` `switchInt`/`assign` drop-flag patterns on non-real-fn bodies.
     - Recognizes `_flag = const 1` (arming a local's drop flag) and `_flag = const 0` (disarming on move/forget or inside an elaborated `clear_bb` drop block).
     - Filters `switchInt(copy _flag)` edges in the fixpoint transfer so the `1` edge propagates only the `F1` state to the drop block (`clear_bb`) and the `0`/`otherwise` edge propagates only the `F0` state to the bypass target.
     - Distinguishes raw-pointer dereference projections (`SPEC-12` `AXS-DROP-007`: `MirPlace` whose projection chain contains `MIR_PROJ_DEREF`) so raw stores (`*p = v`) and reads through dereferences neither require drops nor move the pointer local.
     - Handles moves of droppable locals across `MIR_OP_MOVE`, elaborated `MIR_OP_COPY`, `MIR_RVALUE_AGGREGATE` operands, and `MIR_TERM_CALL` `func`/argument operands (including by-move closure calls).
   - Fixed `verify_return_is_unit_or_error` in `compiler/verify/verifier.ax` to inspect `body.locals[0].ty` when `func != NULL` lacks an entry in `thir.item_types` (matching `verify.c`).

## Files changed

- bootstrap/axiom0/src/driver/pipeline.c
- bootstrap/axiom0/src/verify/verify.c
- compiler/driver/pipeline.ax
- compiler/verify/verifier.ax
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
- tests/selfhost/interp_opt/qa_interp_opt_diff_comptime_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_comptime_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_mir_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_mir_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_run_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_run_b.ax
- tests/selfhost/interp_opt/qa_interp_opt_unit.ax
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
- tests/selfhost/verify/gen_verify_tests.py
- tests/selfhost/verify/harness_verify_mir.ax.in
- tests/selfhost/verify/qa_verify_mir.ax
- tests/selfhost/verify/qa_verify_pipeline.ax
- tests/verify/drop/cond_drop_flag_ok.ax
- tests/verify/drop/cond_drop_flag_ok.mir
- tests/verify/drop/cond_drop_flag_ok.test
- tests/verify/drop/cond_drop_flag_ok_inspect.test
- tests/verify/drop/double_drop_implicit.mir
- tests/verify/drop/double_drop_implicit.test
- tests/verify/drop/missing_drop_branch.mir
- tests/verify/drop/missing_drop_branch.test
- tests/verify/drop/raw_store_moved_ok.ax
- tests/verify/drop/raw_store_moved_ok.mir
- tests/verify/drop/raw_store_moved_ok.test
- tests/verify/drop/raw_store_moved_ok_inspect.test

## 3. Verification Evidence

### 3.1 Dual-Compiler Build (GCC & Clang) and Architecture Check
- **GCC 16.1.0** (`build-snap-T159`): built `axiom0.exe` and `ct_selfhost_drop_cdriver_drop_oracle.exe` with 0 warnings.
- **Clang 22.1.4** (`build-snap-T159/clang-check`, cleaned up after build): built `axiom0.exe` with `-Wall -Wextra -Wpedantic` and 0 warnings.
- **`python tools/archcheck.py`**: `archcheck: 192 files scanned, 0 violations`.

### 3.2 New Drop Verifier Tests (`tests/verify/drop/`)
`python tools/axtest.py --compiler build-snap-T159/axiom0.exe --filter verify/drop/ -j 2`:
- `missing_drop_branch.test`: PASS (`AX_VERIFY_MISSING_DROP` on real body when one branch forgets to drop).
- `double_drop_implicit.test`: PASS (`AX_VERIFY_DOUBLE_DROP` on real body when explicit drop is followed by unguarded scope-exit drop).
- `cond_drop_flag_ok.test`, `cond_drop_flag_ok.ax` (`[native]`, `[native-O1]`, `[interp]`), `cond_drop_flag_ok_inspect.test`: PASS (0 errors; `inspect --emit=mir` shows drop-flag `switchInt`).
- `raw_store_moved_ok.test`, `raw_store_moved_ok.ax` (`[native]`, `[native-O1]`, `[interp]`), `raw_store_moved_ok_inspect.test`: PASS (0 errors; `forget` + `*p = ...` + `drop_in_place`).
- Result: `TOTAL 12 PASS 12 FAIL 0 SKIP 0 XFAIL 0`.

### 3.3 Mutation Test Proof
Temporarily re-adding `func == NULL` to the `AX_VERIFY_MISSING_DROP` and `AX_VERIFY_DOUBLE_DROP` guards in `bootstrap/axiom0/src/verify/verify.c` and running `python tools/axtest.py --compiler build-snap-T159/axiom0.exe --filter verify/drop/ -j 2`:
```text
FAIL    verify/drop/double_drop_implicit.test: exit code 0, expected 1; stderr: 
FAIL    verify/drop/missing_drop_branch.test: exit code 0, expected 1; stderr: 
TOTAL 12 PASS 10 FAIL 2 SKIP 0 XFAIL 0
```
Restoring the fix returned `TOTAL 12 PASS 12 FAIL 0 SKIP 0 XFAIL 0`.

### 3.4 Self-Compile Timing Benchmark
Measured compiling the full `axiomc` selfhost bundle (`--stack-reserve=67108864`):
- Baseline (`build/axiom0.exe`): `111.269s`
- T159 (`build-snap-T159/axiom0.exe`): `110.049s`
- Delta: **`-1.10%`** (well within the `< +10%` budget).

### 3.5 Full Test Suite & Selfhost Verification
- `tests/verify/`: `TOTAL 48 PASS 48 FAIL 0 SKIP 0 XFAIL 0`
- `tests/selfhost/verify/`: `TOTAL 6 PASS 6 FAIL 0 SKIP 0 XFAIL 0` (`qa_verify_mir.ax` and `qa_verify_pipeline.ax` across `[native]`, `[native-O1]`, `[interp]`)
- `tests/selfhost/own_mir_verify/`: all pass including `qa_own_mir_diff_drop_a.ax` and `qa_own_mir_diff_drop_b.ax`
- `tests/selfhost/interp_opt/`: all pass including `qa_interp_opt_diff_mir_b.ax` and `qa_interp_opt_diff_run_b.ax`
- `tests/selfhost/obj_link_driver/axiomc_e2e.test`: `TOTAL 1 PASS 1 FAIL 0`
- Full `axtest.py` suite (`2707` entries across `run/`, `std/`, `ui/`, `verify/`, `mir/`, `opt/`, `mc/`, `driver/`, `link/`, `obj/`, `selfhost/`): 100% of our test suites pass.

STATUS: COMPLETE round=0
