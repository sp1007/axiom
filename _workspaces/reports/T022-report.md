# T022 — VS0 gate: subset conformance on the oracle — report

## Summary

Delivered the VS0 conformance suite (`tests/conformance/vs0/`, 82 `.ax` programs + README),
`tools/gatecheck.py` (SPEC-00 AXS-BOOT-051 steps 1–5 plus rules (a)–(d)) with 33 self-tests,
CI wiring in `tools/ci.sh`, and a parser↔HIR↔THIR↔MIR seam review.

**The gate is BLOCKED.** `gatecheck --gate T022` reports MS-P1 PASS, MS-P2 PASS,
MS-P3 BLOCKED (68 vs0 FAILs, all caused by implementation bugs in parser, typeck/driver,
MIR builder and interpreter — none in my paths), plus a global board violation of rule (d)
(`spec/selfhost-subset.tsv:45`, F-CONST.SCALAR delivered by T061, which is not an ancestor
of consumer T069). No `xfail` was used: no failure is a spec gap with an ADR.

## Files changed

- tests/conformance/vs0/arith_i16_mul_edge.ax
- tests/conformance/vs0/arith_i64_no_overflow.ax
- tests/conformance/vs0/arith_i64_overflow.ax
- tests/conformance/vs0/arith_mul_overflow.ax
- tests/conformance/vs0/arith_neg_min_overflow.ax
- tests/conformance/vs0/arith_precedence.ax
- tests/conformance/vs0/arith_sub_overflow.ax
- tests/conformance/vs0/arith_u32_underflow.ax
- tests/conformance/vs0/arith_u8_overflow.ax
- tests/conformance/vs0/bits_and_or_xor_not.ax
- tests/conformance/vs0/bits_precedence_mask.ax
- tests/conformance/vs0/bool_bitwise_no_short_circuit.ax
- tests/conformance/vs0/call_arg_count.ax
- tests/conformance/vs0/call_arg_type_mismatch.ax
- tests/conformance/vs0/call_five_args.ax
- tests/conformance/vs0/call_mutual_recursion.ax
- tests/conformance/vs0/call_panic_in_callee.ax
- tests/conformance/vs0/call_recursion_sum.ax
- tests/conformance/vs0/call_unit_function.ax
- tests/conformance/vs0/cf_if_else_chain.ax
- tests/conformance/vs0/cf_loop_return.ax
- tests/conformance/vs0/cf_nested_if_in_while.ax
- tests/conformance/vs0/cf_while_condition_false.ax
- tests/conformance/vs0/cmp_bool_order.ax
- tests/conformance/vs0/cmp_non_associative.ax
- tests/conformance/vs0/cmp_unsigned_order.ax
- tests/conformance/vs0/div_rem_negative_divisor.ax
- tests/conformance/vs0/div_unsigned.ax
- tests/conformance/vs0/float_unsupported.ax
- tests/conformance/vs0/fp01_return_42.ax
- tests/conformance/vs0/fp02_return_bool.ax
- tests/conformance/vs0/fp03_return_40_plus_2.ax
- tests/conformance/vs0/fp10_overflow_panics.ax
- tests/conformance/vs0/let_inferred_from_annotation.ax
- tests/conformance/vs0/let_shadowing.ax
- tests/conformance/vs0/lit_bool_not_integer.ax
- tests/conformance/vs0/lit_default_from_use.ax
- tests/conformance/vs0/lit_minus_129_i8.ax
- tests/conformance/vs0/lit_min_i32_folded.ax
- tests/conformance/vs0/lit_min_i8_suffix.ax
- tests/conformance/vs0/lit_mixed_signedness.ax
- tests/conformance/vs0/lit_neg_unsigned.ax
- tests/conformance/vs0/lit_neg_zero_unsigned.ax
- tests/conformance/vs0/lit_u64_max.ax
- tests/conformance/vs0/lit_u64_max_plus_one.ax
- tests/conformance/vs0/main_block_tail.ax
- tests/conformance/vs0/main_returns_i64.ax
- tests/conformance/vs0/main_u32.ax
- tests/conformance/vs0/main_unit.ax
- tests/conformance/vs0/main_with_params.ax
- tests/conformance/vs0/order_binary_left_first.ax
- tests/conformance/vs0/order_binary_right_before_op.ax
- tests/conformance/vs0/order_call_args_left_to_right.ax
- tests/conformance/vs0/README.md
- tests/conformance/vs0/rem_by_zero.ax
- tests/conformance/vs0/rem_min_minus_one.ax
- tests/conformance/vs0/return_missing_value.ax
- tests/conformance/vs0/seam_add_left_assoc_no_overflow.ax
- tests/conformance/vs0/seam_bitnot_value.ax
- tests/conformance/vs0/seam_div_left_assoc.ax
- tests/conformance/vs0/seam_duplicate_diag_once.ax
- tests/conformance/vs0/seam_if_cond_binary.ax
- tests/conformance/vs0/seam_if_header_ident_not_struct.ax
- tests/conformance/vs0/seam_sub_left_assoc.ax
- tests/conformance/vs0/seam_unary_minus_binds_tight.ax
- tests/conformance/vs0/seam_unary_not_bool.ax
- tests/conformance/vs0/seam_while_cond_binary.ax
- tests/conformance/vs0/sem_t04_div_truncates.ax
- tests/conformance/vs0/sem_t05_rem_sign_of_dividend.ax
- tests/conformance/vs0/sem_t06_div_by_zero.ax
- tests/conformance/vs0/sem_t07_min_div_minus_one.ax
- tests/conformance/vs0/sem_t08_shift_out_of_range.ax
- tests/conformance/vs0/sem_t09_arith_shift_right.ax
- tests/conformance/vs0/sem_t14_short_circuit_and.ax
- tests/conformance/vs0/sem_t15_literal_out_of_range.ax
- tests/conformance/vs0/sem_t16_no_implicit_widening.ax
- tests/conformance/vs0/shift_amount_other_type.ax
- tests/conformance/vs0/shift_negative_amount.ax
- tests/conformance/vs0/shift_u8_by_8.ax
- tests/conformance/vs0/shift_unsigned_logical.ax
- tests/conformance/vs0/short_circuit_and_skips_panic.ax
- tests/conformance/vs0/short_circuit_or_evaluates_right.ax
- tests/conformance/vs0/short_circuit_or_skips_panic.ax
- tools/tests/gatecheck/run_selftests.py
- tools/tests/gatecheck/test_gatecheck.py
- tools/gatecheck.py
- tools/ci.sh
- tests/hir/control.ax
- tests/hir/control.hir
- tools/ci.ps1

## Tests

All runs inside the snapshot `build-snap-T022` (HEAD f966fc8 + this change set; gcc + Ninja,
no warnings, no C changes).

| Command | Result |
|---|---|
| `python tools/axtest.py --compiler build/axiom0.exe conformance/vs0/` | TOTAL 148, PASS 14, FAIL 68, SKIP 66 (SKIP = `native-after:` T028/T033/T037 open tasks) |
| `python tools/axtest.py --compiler build/axiom0.exe` (full) | TOTAL 310, PASS 171, all FAILs inside vs0; everything outside vs0 passes (stable over 4 runs) |
| `python tools/tests/gatecheck/run_selftests.py` | 33 tests OK |
| `python tools/gatecheck.py --gate T022 --compiler build/axiom0.exe` | exit 1: MS-P1 PASS, MS-P2 PASS, MS-P3 BLOCKED, rule (d) violation |
| `python tools/archcheck.py` | 0 violations |
| `python tools/reqcov.py --strict` | COVERAGE OK |
| `python tools/harness_check.py` | HARNESS OK |

Passing vs0 tests: arith_precedence, call_arg_count, call_five_args, call_unit_function,
cf_loop_return, cf_while_condition_false, fp01, fp02, fp03, let_shadowing,
lit_u64_max_plus_one, main_block_tail, main_u32, main_unit.

Note: one isolated earlier FAIL of `unit/diag/diag_unit.test` right after relinking was not
reproducible (likely antivirus scanning the fresh binary) — environment, not code.

## gatecheck design

- Step 1 structure checks; steps 2–3 select due milestones and run axtest `--json` on their
  `must_pass` dirs; C-unit-only dirs (`tests/unit/driver`, `tests/unit/source`) are covered by
  the `tests/unit` manifests that run `axiom0-unit`.
- Step 4: for due milestones' native features, no test may still carry `native-after:` naming
  that milestone's native task.
- Step 5: check commands — `gatecheck` evaluated in-process; `differential`/`determinism`
  report "no command yet" (not a pass).
- Rules (a) invariants (heading accepts `-` or em dash), (c) directives, (d) subset TSV
  ancestry (delivering task must be an ancestor of the consumer in the depends graph).
- Accepted SKIP reasons only: `native-after` an open task, mode not required by any due
  milestone, tool not found, requires-excluded. "compiler lacks feature" is rejected — it would
  let a gate pass vacuously.

## Seam review (parser ↔ HIR ↔ THIR ↔ MIR ↔ interp)

Every failure below was isolated to a single stage with a minimal repro; the vs0 `seam_*`
tests pin each one.

### BLOCKED list

**P — parser `bootstrap/axiom0/src/syntax/parse.c` (T011/T012)**
1. Lines ~686/742 (also ~702 match, ~755 for): headers use `parse_expr_prec(p, 0)`; ops with
   prec > 0 break the loop so only a primary is parsed — `if a == 3 {` fails
   (AX_PARSE_EXPECTED_TOKEN / LEADING_OPERATOR). Existing tests used `if (cond)` and masked it.
   Fails: seam_if_cond_binary, seam_while_cond_binary and ~25 more using comparisons in headers.
2. Lines ~848/1013: binary operators are right-associative (right operand parsed at `prec`
   with break on `prec > min_prec`): `10 - 3 - 2 == 9`. Fails: seam_sub_left_assoc,
   seam_div_left_assoc, seam_add_left_assoc_no_overflow.
3. Line ~527: prefix operand parsed at prec 13 so `-1 + 8` is `-(1+8)`.
   Fails: seam_unary_minus_binds_tight, sem_t09_arith_shift_right.
4. Lines ~559–569/608–617: tentative generic-args parse emits AX_PARSE_EXPECTED_TYPE before
   backtracking (`n < 0 {`, `a < 2 < 3`). Fails: cf_if_else_chain, cmp_non_associative.
5. Line ~577: `ident {` in a header parsed as struct literal. Fails:
   seam_if_header_ident_not_struct, sem_t14_short_circuit_and, seam_unary_not_bool,
   call_mutual_recursion.

**T — typeck `bootstrap/axiom0/src/types/typeck.c` (T017) / driver `driver/pipeline.c`**
1. One error emits AX_TYPE_MISMATCH twice. Fails: sem_t16_no_implicit_widening,
   seam_duplicate_diag_once, call_arg_type_mismatch, lit_bool_not_integer, lit_mixed_signedness.
2. No AXS-SEM-021 literal range / negated-unsigned check. Fails: sem_t15_literal_out_of_range,
   lit_minus_129_i8, lit_neg_unsigned.
3. Floats not rejected (AXS-SEM-010). Fails: float_unsupported.
4. `main` signature checked only in `stage_run` (pipeline.c:191–206), not in `check`; TYPE.def
   marks only MAIN_MISSING as build/run-only. Fails: main_with_params, main_returns_i64.
5. pipeline.c:196 hard-codes `strstr(main_file, "tests/driver/test.ax")` →
   AX_DRIVER_STAGE_NOT_AVAILABLE: test-specific behaviour in production code (remove).

**M — MIR builder `bootstrap/axiom0/src/mir/build/builder.c` (T019)**
1. Line ~238: unary `~` lowered as NEG. Fails: seam_bitnot_value.
2. No overflow / div-by-zero / shift-range `Assert` in MIR: FP-03 requires checked Add with an
   assert edge to the panic path, which AXS-BOOT-007 / T023 rely on; checks exist only in the
   interpreter. The golden `tests/mir/build/first_mir.mir` encodes this deviation and must be
   regenerated with the fix.
3. `build_expr_into` has no final else: unhandled HIR kinds silently produce no MIR (should ICE
   or diagnose).

**I — interpreter `bootstrap/axiom0/src/interp/interp.c` (T021)**
1. Lines ~164–195: all arithmetic done as int32; other widths wrong. Fails: arith_i64_overflow,
   arith_i64_no_overflow, arith_u8_overflow, arith_u32_underflow, arith_i16_mul_edge,
   div_unsigned, cmp_unsigned_order, lit_u64_max, …
2. Default branch returns 0: `& | ^ << >>` unimplemented, no shift range check. Fails:
   sem_t08_shift_out_of_range, shift_*, bits_*, bool_bitwise_no_short_circuit.
3. UNARY_OP rvalue unimplemented (yields 0). Fails: arith_neg_min_overflow, lit_min_i32_folded;
   arith_sub_overflow CRASHes (exit 0xFFFFFFFF).
4. Lines ~75–83: panic emits an AX_DRIVER_INTERP_PANIC diagnostic instead of
   `panic: <msg>\n` on stderr (AXS-SEM-071). Fails every panic test's stderr check
   (fp10, sem_t06, sem_t07, rem_*, call_panic_in_callee, short_circuit_*_skips_panic, …).
5. Rebuilds MIR per call from THIR instead of running the verified bodies; uses host C
   arithmetic (X-HOST-SEM risk). Design concern, not a single failing test.

**B — board** `spec/selfhost-subset.tsv:45`: F-CONST.SCALAR delivered by T061, but consumer
T069 depends `[T056, T060, T059, T061b]` do not reach T061 → gatecheck rule (d) fails globally.
Architect: add T061 to T069's depends or change the consumer.

### Seam observations (no failing test of their own)
- HIR→THIR: typeck has no exhaustive default for expression kinds either; combined with M3 an
  unsupported construct can pass `check` and vanish in MIR. Both stages should ICE on
  unknown kinds.
- Diagnostics duplication (T1) points at errors being reported both at the expression and at
  the enclosing coercion site; dedupe at the coercion seam.

## Decisions (with rationale)

- `lit_u64_max_plus_one` expects AX_LEX_INT_OVERFLOW (SPEC-01 AXS-LEX-054) — the lexer owns
  literals exceeding u64; typeck range checks apply only below that.
- MAIN_SIGNATURE is expected from `check` (TYPE.def scopes only MAIN_MISSING to build/run).
- `//~?` (any-line) annotations used where the spec does not fix a span (main signature,
  AX_TYPE_RETURN).
- Every run test has an exact `// stderr:` line (empty for non-panic) and expected exit codes
  avoid 1–3, because those collide with `run --interp` compiler statuses and produced false
  passes.
- Each run test carries `// native-after: T028|T033|T037` so native modes SKIP for open tasks
  and become mandatory automatically when those tasks close (gatecheck step 4).
- No 0114 program falls inside MS-P3; SEM-T03, T10–T13, T17, T18 need casts/intrinsics
  (MS-P5) and are deferred (README).
- FP-03 MIR golden already lives in `tests/mir/build/first_mir.ax`; vs0 only executes FP-03.

## Spec deviations

- Adaptation: SEM-T04/T05/T09 print `+12` / `+11` / `+14` as exit codes instead of the spec's
  `+2` / `+1` / `+4`, to keep exits out of the 1–3 range used by the driver. Semantics tested
  are identical.
- No deviations in implementation (no compiler code changed).

## Follow-ups

1. Fix task: parser P1–P5 (parse.c) — expression precedence/associativity, headers, generic
   backtrack, struct-literal restriction in headers.
2. Fix task: typeck/driver T1–T5 (dedupe, SEM-021 range, SEM-010 floats, main signature in
   `check`, remove hard-coded test path).
3. Fix task: MIR builder M1–M3 (+ regenerate `tests/mir/build/first_mir.mir`).
4. Fix task: interpreter I1–I5 (width-correct arithmetic, bitwise/shift, unary, panic stderr
   format, run verified MIR).
5. Board: add T061 to T069 depends (or change consumer) — rule (d).
6. `tools/ci.ps1` still calls gatecheck without `--compiler` and does not run the gatecheck
   self-tests; align with `tools/ci.sh` (outside my paths).
7. Re-run `gatecheck --gate T022` after 1–5; expected PASS with no suite changes.

STATUS: COMPLETE round=0
