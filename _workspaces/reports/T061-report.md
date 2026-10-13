# T061 report

## Summary
Task T061 implements const items and constant expressions (array sizes, repeat arrays, constant tables) evaluated by the MIR interpreter oracle with step/call-depth limits and diagnostics.
- Const-evaluator interface (ADR-0004 §8, SPEC-04 §12 AXS-EXT-120): `types` declares `AxConstEvaluator` and `AxConstValue` in `types/const/eval.h`. The driver instantiates the interpreter evaluator and passes it to `ax_typeck_with_evaluator`. `types` never includes `interp` (verified by `archcheck.py` INV-LAYER-004: 0 violations).
- Constant tables (ADR-0004 §2, SPEC-04 §12 AXS-EXT-121): aggregate constants (`[256]u8`, keyword `Str` table, struct table) are materialised once in permanent memory via `AX_MIR_LOCAL_CONST` and indexed in place, never copied per use.
- `static` and `static mut` items are rejected in Pass 1b with `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` (ADR-0001, E13.3).
- Comptime diagnostics implemented: `AX_CONST_OVERFLOW`, `AX_CONST_DIV_ZERO`, `AX_CONST_CYCLE` (cycle detection via evaluation stack), `AX_CONST_EVAL_LIMIT` (step and call-depth limits).
- Repeat arrays `[expr; N]` and array types `[N]T` evaluate constant expressions for array length.

## Files changed
- bootstrap/axiom0/src/diag/codes/CONST.def
- bootstrap/axiom0/src/driver/pipeline.c
- bootstrap/axiom0/src/interp/interp.c
- bootstrap/axiom0/src/interp/interp.h
- bootstrap/axiom0/src/mir/build/build.h
- bootstrap/axiom0/src/mir/build/builder.c
- bootstrap/axiom0/src/mir/mir.h
- bootstrap/axiom0/src/types/const/eval.h
- bootstrap/axiom0/src/types/typeck.c
- bootstrap/axiom0/src/types/types.h
- tests/run/comptime/array_len.ax
- tests/run/comptime/scalar_const.ax
- tests/run/comptime/table_str.ax
- tests/run/comptime/table_struct.ax
- tests/run/comptime/table_u8_256.ax
- tests/ui/comptime/cycle_err.ax
- tests/ui/comptime/div_zero_err.ax
- tests/ui/comptime/eval_limit_err.ax
- tests/ui/comptime/invalid_type_err.ax
- tests/ui/comptime/overflow_err.ax
- tests/ui/comptime/static_err.ax

## Tests
- `axtest.py --filter comptime -v`: 15 passed, 6 skipped (native after T061d), 0 failed.
  - `run/comptime/scalar_const.ax` [interp, native, native-O1]: passed
  - `run/comptime/array_len.ax` [interp, native, native-O1]: passed
  - `run/comptime/table_str.ax` [interp]: passed (native skipped after T061d)
  - `run/comptime/table_struct.ax` [interp]: passed (native skipped after T061d)
  - `run/comptime/table_u8_256.ax` [interp]: passed (native skipped after T061d)
  - `ui/comptime/static_err.ax`: passed
  - `ui/comptime/cycle_err.ax`: passed
  - `ui/comptime/eval_limit_err.ax`: passed
  - `ui/comptime/overflow_err.ax`: passed
  - `ui/comptime/div_zero_err.ax`: passed
  - `ui/comptime/invalid_type_err.ax`: passed
- Full test suite: TOTAL 1284 PASS 1278 FAIL 0 SKIP 6 XFAIL 0
- Architecture check (`tools/archcheck.py`): 142 files scanned, 0 violations

## Spec deviations
none

## Follow-ups
None for T061. Constant tables in native codegen will be hooked up in milestone T061d.

STATUS: COMPLETE round=0
