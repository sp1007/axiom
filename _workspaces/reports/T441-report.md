# T441 Report: Baseline fix — selfhost MIR comparisons outside `selfhost/drop`

## Summary

Fixed `tests/selfhost/interp_opt/qa_interp_opt_diff_mir_b.ax` (`exit 312`) and `tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_b.ax` (`exit 301`) so that all 18 tests (42 legs) in `selfhost/interp_opt/` and `selfhost/own_mir_verify/` pass across `interp`, `native`, and `native-O1` (`WEAK-NATIVE 0`) and remain hermetically isolated from future growth of the live `std/core/prelude.ax` (`ADR-0041 §2 D2`, `ADR-0042 §1`).

## Root Cause Diagnosis

1. **`selfhost/interp_opt/qa_interp_opt_diff_mir_b.ax` (`exit 312`, case 12 `tests/selfhost/drop/fixtures/d01_scope_exit.ax`)**:
   - Cases `0..11` (`tests/opt/*` and `tests/mir/build/*`) have `CASE_PRELUDE[case_idx] == 0u32` and pass byte-for-byte.
   - Case `12` (`tests/selfhost/drop/fixtures/d01_scope_exit.ax`) is the first fixture with `CASE_PRELUDE[case_idx] == 1u32` (`session_append_std_prelude`).
   - First differing line in `d01_scope_exit.ax`:
     - Actual (`pre_out`): `    let mut _1: type#21;`
     - Expected (`exp_mir_opt`): `    let mut _1: type#17;`
   - Every diff in `d01_scope_exit.ax` .. `d11_qa_edges.ax` was the identical `+4` user struct/enum `TypeId` shift (`type#17` -> `type#21`, `type#18` -> `type#22`, etc.) caused by `typeck_pass1a` hoisting `Option<T>` (`2` types) and `Result<T, E>` (`2` types) from `STD_CORE_DATA` ahead of user types (`T429` / `T435`).
2. **`selfhost/own_mir_verify/qa_own_mir_diff_drop_b.ax` (`exit 301`, case 1 `tests/selfhost/drop/fixtures/d03_struct_fields.ax`)**:
   - Case `0` (`d02_conditional_move.ax`) has `CASE_PRELUDE[0] == 0u32` and passes byte-for-byte.
   - Case `1` (`d03_struct_fields.ax`) is the first fixture in `DROP_B` with `CASE_PRELUDE[1] == 1u32`.
   - First differing line in `d03_struct_fields.ax`:
     - Actual (`pre_out`): `    let mut _1: type#21;`
     - Expected (`exp_pre`): `    let mut _1: type#17;`
   - Zero MIR builder, optimizer, or drop elaboration differences exist; the mismatch is strictly the same `+4` `TypeId` shift on user structs/enums when `session_append_std_prelude` items carry `module_path = ["std", ...]`.

## Hermetic Fix (Reusing `T435` Pattern)

1. **Pre-typeck prelude `module_path` demotion (`demote_prelude_hir_module_paths`)**:
   - Added `demote_prelude_hir_module_paths(view(hir), fid.v)` immediately before `session_typeck_into` in both `tests/selfhost/interp_opt/harness_mir_opt_diff.ax.in` and `tests/selfhost/own_mir_verify/harness_mir_diff.ax.in`.
   - Clearing `module_path.count` on appended non-main-file `HirItem`s after `session_lower_hir` prevents `typeck_pass1a` from hoisting `Option<T>` and `Result<T, E>` ahead of user types while preserving all resolved `10000+` std `SymbolId`s and keeping `bytes_equal` 100% byte-for-byte strict.
2. **Pinned minimal std root for `--axiom0` and `--oracle` in both generators**:
   - Updated `tests/selfhost/interp_opt/gen_interp_opt_tests.py` (`run_axiom0_mir_opt`, `run_axiom0_run`) and `tests/selfhost/own_mir_verify/gen_own_mir_verify_tests.py` (`run_oracle_drop`, `run_axiom0_check_stderr`) to pass `--std-root tests/selfhost/drop/std_minimal` so future live `std/core/prelude.ax` additions cannot perturb golden generation.
3. **Baseline cleanup**:
   - Removed `selfhost/interp_opt/qa_interp_opt_diff_mir_b.ax` and `selfhost/own_mir_verify/qa_own_mir_diff_drop_b.ax` (`T441`) from `_workspaces/baseline-failures.txt`.

## Verification

1. **Generator & `--axiom0` freshness checks**:
   - `python tests/selfhost/interp_opt/gen_interp_opt_tests.py --check` -> all 7 bundles up to date (exit `0`).
   - `python tests/selfhost/own_mir_verify/gen_own_mir_verify_tests.py --check` -> all 9 bundles up to date (exit `0`).
   - `python tests/selfhost/interp_opt/gen_interp_opt_tests.py --axiom0 build-snap-T441/build/axiom0.exe --check` -> exit `0`.
   - `python tests/selfhost/own_mir_verify/gen_own_mir_verify_tests.py --axiom0 build-snap-T441/build/axiom0.exe --check` -> exit `0`.
2. **1-byte fixture mutation proof**:
   - Mutated 1 byte in case 0's expected MIR blob (`type#8` -> `type#9` in `qa_interp_opt_diff_mir_b.ax`, `type#2` -> `type#3` in `qa_own_mir_diff_drop_b.ax`) inside `build-snap-T441` and ran `axtest.py --no-cache`:
     - `FAIL selfhost/interp_opt/qa_interp_opt_diff_mir_b.ax [native]: exit code 300, expected 0`
     - `FAIL selfhost/interp_opt/qa_interp_opt_diff_mir_b.ax [native-O1]: exit code 300, expected 0`
     - `FAIL selfhost/own_mir_verify/qa_own_mir_diff_drop_b.ax [native]: exit code 300, expected 0`
     - `FAIL selfhost/own_mir_verify/qa_own_mir_diff_drop_b.ax [native-O1]: exit code 300, expected 0`
   - Restored `build-snap-T441` via `taskctl.py snapshot T441` immediately afterwards.
3. **Full `selfhost/interp_opt` and `selfhost/own_mir_verify` suite in `build-snap-T441`**:
   - `python tools/axtest.py --root build-snap-T441 --compiler build-snap-T441/build/axiomc2.exe --build-dir build-snap-T441/build --exclude-requires axiom0-internal -v -j 2 selfhost/interp_opt selfhost/own_mir_verify` -> `TOTAL 42 PASS 42 FAIL 0 SKIP 0 XFAIL 0` (`WEAK-NATIVE 0`).

## Files changed

- _workspaces/baseline-failures.txt
- tests/selfhost/interp_opt/gen_interp_opt_tests.py
- tests/selfhost/interp_opt/harness_mir_opt_diff.ax.in
- tests/selfhost/interp_opt/qa_interp_opt_diff_mir_a.ax
- tests/selfhost/interp_opt/qa_interp_opt_diff_mir_b.ax
- tests/selfhost/own_mir_verify/gen_own_mir_verify_tests.py
- tests/selfhost/own_mir_verify/harness_mir_diff.ax.in
- tests/selfhost/own_mir_verify/qa_own_mir_diff_build_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_build_b.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_a.ax
- tests/selfhost/own_mir_verify/qa_own_mir_diff_drop_b.ax

## Status

STATUS: COMPLETE round=0
