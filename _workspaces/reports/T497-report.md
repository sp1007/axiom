# T497 report

## Summary
`AX_TYPE_INDEX_NOT_INT` is registered and reported for a non-integer array/slice/str index.

- Numeric id assigned: **169** (next free compiler id after `AX_CONST_SHIFT_RANGE` = 168). SPEC-40 display number: **2014**
  (the display table in SPEC-40 AXS-INT-060 maps the number; `compiler/diag/code.ax` keeps compiler ids, as for T483/168 -> 3104).
  `spec/diagnostics.md` must get the row `AX_TYPE_INDEX_NOT_INT | 169 | 2014` (architect, per task scope).
- `compiler/diag/code.ax`: constant, name table entry, default message `index must be an integer`.
- `compiler/diag/format.ax`: name branch for code 169 (same mechanism T483 used for 168; the byte table covers only ids < 133).
- `compiler/diag/explain/mod.ax`: explain entry 38 (`EXPLAIN_REGISTRY_COUNT` 38 -> 39); the explain-count oracles were updated
  (`tests/run/diag_ux2`, `tests/conformance/p19/e19_4_diagnostics_ai`: `entries=38` -> `39`, README `38` -> `39`).
- `compiler/types/typeck.ax`: new `check_index_operand` is the single operand check for array/slice/str subscripts and for both
  bounds of a range index. Integer and `IntVar` (-> usize) operands are unchanged. Otherwise it emits `AX_TYPE_INDEX_NOT_INT` with the
  primary span on the index expression and the message `index must be an integer, found <word>` and returns an error type, so no
  secondary `AX_TYPE_MISMATCH` appears. Previously a single index reported `AX_TYPE_MISMATCH` and range bounds reported
  `AX_TYPE_MISMATCH` too.
- Tests: `tests/ui/index_not_int/{bool,bool_literal,char,float_literal,struct_tuple,slice_base,range_bound,integer_indices_ok}.ax`; the
  helper `tests/run/numeric/mixed_int_matrix/repro_index_not_int_code.ax` was converted into `bool.ax` and deleted.

## Design decisions / open questions decided
1. **`<type>` in the message is a kind word, not a full type name.** The type interner has no type printer in this stage, so the
   message names the kind (`bool`, `char`, `Str`, `tuple`, `struct`, `enum`, `fn`, `view`, `pointer`, `array`, `slice`, `unit`, `float`,
   `value`). Tests match codes, not text. A real type printer is a follow-up (see below).
2. **f32/f64.** Float types and literals do not exist in this stage (E12.2: `f32`/`f64` type names and float literals report
   `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP`). A float variable therefore cannot be written as an index operand at all. A float *literal*
   index (`a[1.0f32]`, `a[2.5f64]`, `a[1.5]`) is reported directly as `AX_TYPE_INDEX_NOT_INT` (`float_literal.ax`) before `check_expr`
   would report the unsupported-literal code. The `f32`/`f64`-typed-variable case is untestable until E12.2 (follow-up).
3. **Name printing.** Code 169 is named in `format.ax` (the single rendering path for human, JSON and ux2 output), not through the
   `patch_unknown_intrinsic_diag_buf` text patch in `typeck.ax`.
4. `view<[N]T>` bases are not indexable in this stage (they report `AX_TYPE_CANNOT_INDEX` as before); only `view<[T]>`/`mut_view<[T]>`
   (slices), arrays and `Str` reach the operand check. Behaviour for those bases is otherwise unchanged.

## Files changed
- compiler/diag/code.ax
- compiler/diag/format.ax
- compiler/diag/explain/mod.ax
- compiler/types/typeck.ax
- tests/run/diag_ux2/diag_ux2_oracle.py
- tests/run/diag_ux2/diag_ux2_probe.ax.in
- tests/conformance/p19/e19_4_diagnostics_ai/README.md
- tests/conformance/p19/e19_4_diagnostics_ai/e19_4_diagnostics_ai_oracle.py
- tests/conformance/p19/e19_4_diagnostics_ai/e19_4_diagnostics_ai_probe.ax.in
- tests/run/numeric/mixed_int_matrix/repro_index_not_int_code.ax
- tests/typeck/int128/int_promotion_neg.ax
- tests/ui/index_not_int/bool.ax
- tests/ui/index_not_int/bool_literal.ax
- tests/ui/index_not_int/char.ax
- tests/ui/index_not_int/float_literal.ax
- tests/ui/index_not_int/struct_tuple.ax
- tests/ui/index_not_int/slice_base.ax
- tests/ui/index_not_int/range_bound.ax
- tests/ui/index_not_int/integer_indices_ok.ax

## Tests
Built in `build-snap-T497` (clang Release stage-0; `tools/build_axiomc.py`): stage-2/stage-3 fixed point OK
(sha256 41683ce0...), stage-0 guard OK.
- `python tools/axtest.py --compiler build/axiomc.exe --filter ui/index_not_int` -> 8/8 PASS.
- `python tools/taskgate.py --task T497 --compiler build/axiomc.exe -j 2 --build-dir build` -> `TOTAL 507 PASS 504 FAIL 0 XFAIL 3`,
  BASELINE OK, archcheck clean, `TASKGATE T497 exit=0` (includes tests/ui, tests/run/diag_ux2, p19 e19_4, typeck/int128, smoke).
- First gate run found one stale expectation, `tests/typeck/int128/int_promotion_neg.ax` line 27 (`arr[true]` expected
  `AX_TYPE_MISMATCH`, the old behaviour this task changes); its annotation is now `AX_TYPE_INDEX_NOT_INT` (paths widened by the orchestrator).

## Spec deviations
none (the one changed pre-existing expectation is the intended behaviour change; message wording `found <word>` is coarser than `found <type>`; see decision 1).

## Follow-ups
- Architect: add `AX_TYPE_INDEX_NOT_INT | 169 | 2014` to `spec/diagnostics.md`.
- A type pretty-printer for typeck diagnostics (so `found <type>` can name the exact type, e.g. `Idx`/`(usize, usize)`), and an
  `f32`/`f64` variable test for this code once E12.2 lands floats (the E12.2 task should reuse `check_index_operand`).
- The selfhost generators contain no explicit expectations of this code (bundles are regenerated by the snapshot from `compiler/`), so no
  generator-input path is needed.

STATUS: COMPLETE round=0
