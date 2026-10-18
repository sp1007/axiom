# T083b Report: Port Optimizer (`-O1`) to Axiom (`compiler/opt/`)

## Summary
Ported the MIR `-O1` optimizer (`bootstrap/axiom0/src/opt/opt.h` and `bootstrap/axiom0/src/opt/opt.c`) to Axiom under `compiler/opt/` (`const_fold.ax`, `dce.ax`, `cfg_simp.ax`, and `mod.ax`), and created selfhost unit and differential pipeline test suites under `tests/selfhost/opt/`.

## Round 1 QA Fixes (`_workspaces/reports/T083b-qa.md`)
- **Finding 1 (`## Files changed` manifest)**: Added the canonical `## Files changed` section listing all 9 created/modified files so `taskctl.py changes T083b` and `taskctl.py snapshot T083b` resolve cleanly with zero `REFUSED` lines.
- **Finding 2 (`opt_const_fold` lookahead removal)**: Removed the blind `j + 1` next-statement lookahead inside the `MIR_RVALUE_BINARY_OP` branch of `opt_const_fold` (`compiler/opt/const_fold.ax`), ensuring every `MIR_RVALUE_OVERFLOWS_BINARY_OP` is folded solely on its own operands (`do_const_fold_binop(stmt.rvalue.lhs, stmt.rvalue.rhs)`), matching `bootstrap/axiom0/src/opt/opt.c:183-201`. Added Case 5 regression test in `tests/selfhost/opt/harness_opt_unit.ax.in`.
- **Finding 3 (`opt_rvalue_is_pure` and unreachable blocks in `opt_dce`)**:
  - Updated `opt_rvalue_is_pure` (`compiler/opt/dce.ax`) to return `true` only for `MIR_RVALUE_USE`, `MIR_RVALUE_REF`, `MIR_RVALUE_LEN`, `MIR_RVALUE_CAST`, `MIR_RVALUE_DISCRIMINANT`, and `MIR_RVALUE_AGGREGATE`, matching `bootstrap/axiom0/src/opt/opt.c:340-348`.
  - Updated `opt_dce` (`compiler/opt/dce.ax`) to skip basic blocks whose terminator is `MIR_TERM_UNREACHABLE` in both the use-counting loop and the statement-removal loop, matching `bootstrap/axiom0/src/opt/opt.c:363,421`. Added Case 6 regression test in `tests/selfhost/opt/harness_opt_unit.ax.in`.
- **Finding 4 (Exact `opt.c` behavioral parity in `const_fold.ax` and `cfg_simp.ax`)**:
  - Added `lhs.constant.ty.v != rhs.constant.ty.v` and `bits > 64u32` checks in `do_const_fold_binop` (`compiler/opt/const_fold.ax`), matching `opt.c:21-23`.
  - Restricted `MIR_UNOP_NOT` in `do_const_fold_unop` (`compiler/opt/const_fold.ax`) to `bool` operands (`opt_type_is_bool`), while `MIR_UNOP_BITNOT` handles integer bitwise NOT, matching `opt.c:140-146`.
  - Set the type of folded `MIR_RVALUE_OVERFLOWS_BINARY_OP` constants to `body.locals[stmt.place.local.v].ty` (with `bool_ty` fallback), and wrapped `opt_const_fold` (`compiler/opt/const_fold.ax`) and `opt_cfg_simplify` (`compiler/opt/cfg_simp.ax`) in fixed-point `while pass_changed` loops, matching `opt.c:175,192,220`.
- **Finding 5 (Differential coverage of all `tests/opt/` fixtures)**:
  - Extended `tests/selfhost/opt/gen_opt_tests.py`, `tests/selfhost/opt/harness_opt_unit.ax.in`, and `tests/selfhost/opt/harness_opt_pipeline.ax.in` to test all three `tests/opt/` fixtures (`tests/opt/const_fold_run.ax`, `tests/opt/qa_dce_run.ax`, and `tests/opt/qa_edge_cases_run.ax`) both at the standalone MIR level (`qa_opt_unit.ax` Cases 4, 7, 8) and through the full selfhost frontend + `mir_build_fn` + `opt_run` pipeline (`qa_opt_pipeline.ax` Fixtures 0, 1, 2), verifying byte-for-byte MIR parity with `axiom0 -O1` prior to `mir_drop_elaborate` (matching `bootstrap/axiom0/src/driver/pipeline.c:446-508`).

## Files changed

- compiler/opt/cfg_simp.ax
- compiler/opt/const_fold.ax
- compiler/opt/dce.ax
- compiler/opt/mod.ax
- tests/selfhost/opt/gen_opt_tests.py
- tests/selfhost/opt/harness_opt_pipeline.ax.in
- tests/selfhost/opt/harness_opt_unit.ax.in
- tests/selfhost/opt/qa_opt_pipeline.ax
- tests/selfhost/opt/qa_opt_unit.ax

## Verification
All builds and tests were executed in the isolated snapshot `build-snap-T083b`:
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T083b`: 9 files listed, 0 `REFUSED` lines.
- `cmake --build build`: 0 warnings, 0 errors.
- `ctest --test-dir build --output-on-failure`: 18/18 passed (100%).
- `python tools/archcheck.py`: 188 files scanned, 0 violations.
- `python tools/axtest.py --build-dir build --filter selfhost/opt`: 6/6 passed (`qa_opt_unit.ax` and `qa_opt_pipeline.ax` in `[interp]`, `[native]`, and `[native-O1]`).
- `python tools/axtest.py --build-dir build --filter opt`: 30/30 passed.

STATUS: COMPLETE round=1
