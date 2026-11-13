---
id: T482
title: Investigate & fix — O1 miscompile of the original u128_neg_raw carry form in the stage-2 compiler (FU-T452-NEG)
phase: P12-numeric-floating-point-simd
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: opus
depends: [T452]
priority: 26
status: todo
attempts: 0
timeout_min: 900
paths: [tests/run/o1_neg_carry_repro]
locks: [compiler/opt, compiler/mir/builder.ax, compiler/lir/builder.ax, compiler/target/x64, tests/selfhost]
spec: [spec/decisions/ADR-0042-architect-inbox-1-baseline-admissions-and-followups.md, spec/SPEC-40-integers.md, spec/SPEC-20-selfhost.md]
covers: [REQ-TST-043, REQ-TST-090]
---
# T482 — Investigate: O1 miscompile behind the neg_carry workaround

## Goal
Find and fix the optimizer or codegen defect that made the stage-2 `-O1` compiler lose a carry in the original
`u128_neg_raw` form, so semantically equal source forms compile to equal behaviour at O1 (T452 report FU-T452-NEG,
T452-qa neg_carry decision; ADR-0042 §4).

## Scope
- Recipe (T452-qa): re-apply the original three lines to `u128_neg_raw` in a scratch copy of `compiler/interp/interp.ax`
  (and `opt_u128_neg_raw` in `compiler/opt/const_fold.ax`):
  `let nlo = w_add_u64(lo ^ 0xFFFFFFFFFFFFFFFFu64, 1u64);`
  `let carry: u64 = if lo == 0u64 { 1u64 } else { 0u64 };`
  `let nhi = w_add_u64(hi ^ 0xFFFFFFFFFFFFFFFFu64, carry);`
  build an O1 stage-2 compiler (`tools/build_axiomc.py`, scratch snapshot), run
  `axiomc2 run --interp tests/run/int128_interp/neg_carry.ax` -> exit 1 (hi = `0xFFFFFFFFFFFFFFFE` for `-(1i128 << 64)`);
  the O1 folder gave `-TWO64` = 340282366920938463426481119284349108224. A standalone 20-line copy did not reproduce.
- Bisect: build stage 2 at O0 (allow the long timeout) to separate O1 passes from codegen; then disable -O1 passes one
  at a time (or `--time-passes`/pass flags if available) and diff the MIR/LIR of `u128_neg_raw` in the bundle
  (`inspect --emit=mir-opt|lir`) between the good and bad builds. Candidates: an `if` expression feeding an add after
  `^` with an all-ones u64 constant; constant propagation across the call to `w_add_u64` (inlining); the T452 folder
  changes applied while compiling the compiler.
- Reduce to a standalone program that fails at O1 (`tests/run/o1_neg_carry_repro/*.ax`, interp vs native-O1, exact
  `// stdout:`), fix the pass/codegen, keep the T452 workaround in place (no edit of `compiler/interp` needed).
- If no defect is found after the bisection, the report states the evidence (per-pass diffs) and the architect decides.

## Acceptance
- [ ] Root cause named with the responsible pass/function and a minimal repro test that fails before and passes after.
- [ ] A stage-2 O1 compiler built from the original form passes `neg_carry.ax` and `const_fold_neg_carry.test`
  (scratch build; evidence in the report).
- [ ] Gate per axiom-qa.md "Per-task gate scope"; failing ids ⊆ baseline; WEAK-NATIVE 0 for the repro test.
- [ ] Report `_workspaces/reports/T482-report.md` with exact `## Files changed`.

## Out of scope
- Restoring the original form in `compiler/interp` (cosmetic), `bootstrap/axiom0`, `docs/`.

## Log
- 2026-11-13 created by axiom-architect (ADR-0042 §4; T452 FU-T452-NEG)
