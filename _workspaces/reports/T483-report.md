# T483 report: AX_CONST_SHIFT_RANGE and the i64 MIN literal

## Summary
- `AX_CONST_SHIFT_RANGE` is registered as compiler code **168** (next free id after `AX_TYPE_INVALID_TLS_DECL` = 167;
  the SPEC-40 catalogue number 3104 is not used by the compiler, per ADR-0042 §4). Registered in `compiler/diag/code.ax`
  (constant, name table, default message), in the name printer `compiler/diag/format.ax` (codes >= 133 are printed from
  small per-code tables there; without this the diagnostic printed as `<unknown>`), and as an `explain` registry entry
  (idx 37, area CONST, `EXPLAIN_REGISTRY_COUNT` 37 -> 38).
- Constant evaluation reports it for a shift count `< 0` or `>= T.BITS`, all widths including 128 bits:
  - typeck's integer constant evaluator (`eval_const_expr_u128`: `const` items, impl consts, array lengths);
  - the MIR interpreter const path: `interp_panic` in `compiler/interp/value.ax` maps the shift-range panic to the new
    code when `is_comptime` (`interp_opt/session.ax` forwards `comptime_err_code` unchanged, so it needed no edit).
  Overflow (`AX_CONST_OVERFLOW`) and division by zero (`AX_CONST_DIV_ZERO`) are unchanged; runtime shifts still panic
  `shift amount out of range`.
- `-9223372036854775808i64` / `isize` (and the unsuffixed form typed by context, and the hex form) is now valid at run
  time: `compiler/types/typeck.ax` records the unary node of every negated literal in `LitCheck.unary`; after the
  literal's type is final and the range check passed, `check_literal_ranges` folds `-<lit>` into one literal node
  holding the 128-bit two's complement of the magnitude (`tc_fold_neg_literal`). A folded literal carries
  `TC_TOK_FLAG_NEG_FOLDED` so a second typeck pass over the same HIR recovers the magnitude and range-checks it as
  negated again (idempotent; test `min_literal_in_trait_default.ax`). `9223372036854775808i64` without `-` and
  `-9223372036854775809i64` still report `AX_TYPE_LITERAL_OUT_OF_RANGE`.

## Decisions (for the architect)
1. **Fold scope.** The task text asks to fold for `i8..i128/isize`. Observed at HEAD: only `i64`/`isize` MIN is wrong
   (`i8/i16/i32` MIN and `i128` MIN already work; `i128` has a dedicated MIR-builder path). A first version folded every
   signed `-lit`; that changed MIR/LIR for ordinary negative literals (`-5isize`, `let a: i32 = -2147483648`) and
   broke the selfhost bundles that compare axiomc output with axiom0 goldens (`selfhost/lir/qa_lir_from_ax`,
   `selfhost/mir/*`, `selfhost/opt/*`, `selfhost/backend/*`, `selfhost/own_mir_verify/*`). The final fold applies only to the
   one unrepresentable magnitude, `2^63` of `i64`/`isize`; every other negated literal keeps its exact MIR. Rationale: the
   checked `0 - x` that MIR builds for `-lit` is correct for every value whose magnitude is representable.
   The MIR builder (`compiler/mir/builder.ax`, locked by T444b) was not touched; folding in typeck makes the builder see
   a plain literal constant.
2. **Files outside `paths`/`locks` that had to change** (direct consequences of the new code):
   - `compiler/diag/format.ax` (name printer, see above);
   - `tests/ui/int128/const_overflow_neg.ax`: four shift lines now expect `AX_CONST_SHIFT_RANGE`;
   - `tests/run/diag_ux2/*` and `tests/conformance/p19/e19_4_diagnostics_ai/*`: the explain registry has 38 entries;
   - `tests/selfhost/interp_opt/gen_interp_opt_tests.py`: the case `virtual/qa_shift_ovf_err.ax` expects diag code 168
     instead of 96 (the generator embeds the expected code; the axiom0 golden of that case still says overflow, axiom0 is
     frozen and has no such code).
3. **Native i128 MIN literal.** `tests/run/int_min_literals/min_literal_i128.ax` first carried `// native-after: T453`;
   T453 has since landed and QA removed the directive (the test passes in all three modes).
4. **Explain registry.** One entry per code area was the existing shape; the new entry is a second CONST-area entry, so
   `explain_entry_count()` is 38 and `explain_render_list` shows it.
5. `spec/diagnostics.md` / SPEC-03 AXS-SEM-037 are for the architect (code 168, name `AX_CONST_SHIFT_RANGE`).

## Tests
- New: `tests/ui/const_shift_range/{shift_count_out_of_range,shift_in_range_and_overflow_codes,min_literal_range}.ax`,
  `tests/run/int_min_literals/{min_literals_all,min_literals_const_and_arith,min_literal_neg_still_panics,min_literal_in_trait_default,min_literal_i128}.ax`
  (run tests pass in interp, native and native-O1; `-m` on a runtime MIN value still panics `arithmetic overflow`).
- Gate (`tools/taskgate.py --task T483 -j 2`, inside `build-snap-T483`, final run): `TOTAL 408 PASS 404 FAIL 0 SKIP 4`,
  baseline OK, failing ids none, archcheck clean (229 files, 0 violations), WEAK-NATIVE 0 in own/changed tests
  (13 elsewhere in the run). The 4 SKIPs are the `native-after: T453` modes of `min_literal_i128.ax` and pre-existing skips.

## Files changed
- compiler/diag/code.ax
- compiler/diag/explain/mod.ax
- compiler/diag/format.ax
- compiler/interp/value.ax
- compiler/types/typeck.ax
- tests/ui/int128/const_overflow_neg.ax
- tests/conformance/p19/e19_4_diagnostics_ai/e19_4_diagnostics_ai_oracle.py
- tests/conformance/p19/e19_4_diagnostics_ai/e19_4_diagnostics_ai_probe.ax.in
- tests/conformance/p19/e19_4_diagnostics_ai/README.md
- tests/run/diag_ux2/diag_ux2_oracle.py
- tests/run/diag_ux2/diag_ux2_probe.ax.in
- tests/selfhost/interp_opt/gen_interp_opt_tests.py
- tests/run/int_min_literals/min_literals_all.ax
- tests/run/int_min_literals/min_literal_i128.ax
- tests/run/int_min_literals/min_literals_const_and_arith.ax
- tests/run/int_min_literals/min_literal_neg_still_panics.ax
- tests/run/int_min_literals/min_literal_in_trait_default.ax
- tests/ui/const_shift_range/min_literal_range.ax
- tests/ui/const_shift_range/shift_count_out_of_range.ax
- tests/ui/const_shift_range/shift_in_range_and_overflow_codes.ax
- tests/run/int_min_literals/qa_min_literal_contexts.ax
- tests/run/int_min_literals/qa_runtime_shift_still_panics.ax
- tests/run/int_min_literals/qa_runtime_shift_i128_neg_panics.ax
- tests/ui/const_shift_range/qa_const_block_and_aggregate_shift.ax
- tests/ui/const_shift_range/qa_const_shift_more_widths.ax
- _workspaces/reports/T483-report.md

## Round 1
QA finding F1: a constant block/array/tuple initialiser with an out-of-range shift still reported `AX_CONST_OVERFLOW`,
because the MIR shift guard is an `assert(.., "shift amount out of range")` and a failing assert reaches
`interp_panic_sv`, not `interp_panic(.., SHIFT_RANGE)`. Fix in `compiler/interp/value.ax`: the comptime branch of
`interp_panic_sv` now classifies a message containing "shift amount out of range" (new `interp_msg_has_shift_range`,
compared against `INTERP_MSG_BYTES[594..619]`) as `AX_CONST_SHIFT_RANGE`, next to the existing division-by-zero
classification. QA's `qa_const_block_and_aggregate_shift.ax` is the regression test.
Not done (QA note N1, non-blocking): a dedicated message for code 168 in `report_typeck_diag`; messages there are an
indexed byte table (`tc_alloc_diag_msg`), so it is left to a follow-up; the diagnostic prints the generic `type error`.
No other file changed in round 1 besides the QA tests listed above.

STATUS: COMPLETE round=1
