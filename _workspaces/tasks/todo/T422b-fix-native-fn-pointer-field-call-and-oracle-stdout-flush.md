---
id: T422b
title: Fix — native call through a fn-pointer field expression links `__ax_fn_0` (FU-2); oracle drops buffered stdout on step-limit (FU-K)
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T452]
priority: 24
status: todo
attempts: 0
timeout_min: 600
paths: [tests/run/fn_ptr_field_call, tests/run/interp_step_limit_flush]
locks: [compiler/mir/builder.ax, compiler/lir/builder.ax, compiler/interp, tests/selfhost]
spec: [spec/decisions/ADR-0042-architect-inbox-1-baseline-admissions-and-followups.md, spec/SPEC-03-core-semantics.md]
covers: [REQ-TST-072, REQ-TST-046]
---
# T422b — Fix: calls through fn-pointer field expressions; oracle stdout on step-limit

## Goal
`((*vt).wake)(data)` compiles and runs natively like it does in the oracle, and an oracle run that ends with the
step-limit error still writes the stdout produced before the limit (T421 FU-2, T422 FU-K; ADR-0042 §2).

## Scope
- FU-2 repro (T421 report): calling a function-pointer field expression `((*vt).wake)(data)` links as undefined symbol
  `__ax_fn_0` in native mode; binding it to a local first works. Lower an indirect call whose callee is any operand
  (place projection) as an indirect call, never through a synthesised symbol.
- FU-K (T422 report): flush the oracle's buffered stdout before reporting the step-limit (and any other fatal oracle
  error), so a hang diagnosis sees the output.
- Tests: `tests/run/fn_ptr_field_call/*.ax` (field of struct, through pointer, nested; interp/native/native-O1, exact
  `// stdout:`); `tests/run/interp_step_limit_flush/*` (interp only: expected stdout prefix + step-limit error).
- Regenerate selfhost bundles of edited modules with their generators.

## Acceptance
- [ ] FU-2 repro prints the same output in all modes; FU-K test shows the prefix before the error.
- [ ] Gate per axiom-qa.md "Per-task gate scope"; failing ids ⊆ baseline; WEAK-NATIVE 0 for new run tests.
- [ ] Report `_workspaces/reports/T422b-report.md` with exact `## Files changed`.

## Out of scope
- `std/async` workarounds, `bootstrap/axiom0`, `docs/`.

## Log
- 2026-11-13 created by axiom-architect (ADR-0042 §2; T421 FU-2, T422 FU-K)
