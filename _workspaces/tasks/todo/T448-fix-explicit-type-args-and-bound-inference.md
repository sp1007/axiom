---
id: T448
title: Fix — explicit type arguments honoured (FU-H); inference from bounds and inside poll methods (FU-D, FU-5)
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T446]
priority: 23
status: todo
attempts: 0
timeout_min: 900
paths: [tests/run/generic_explicit_args, tests/typeck/infer_from_bounds]
locks: [compiler/types/typeck.ax, compiler/traits, compiler/mir/builder.ax, tests/selfhost]
spec: [spec/decisions/ADR-0042-architect-inbox-1-baseline-admissions-and-followups.md, spec/SPEC-03-core-semantics.md, spec/SPEC-02-grammar.md]
covers: [REQ-TST-072, REQ-TST-051]
---
# T448 — Fix: explicit type arguments and inference from bounds

## Goal
`f<A>()` and `g.m<A>()` use `A` (including when `A` appears only in the return type or a bound), and type parameters
determined by trait bounds or by the receiver are inferred (T422 FU-D, FU-H; T421 FU-5; ADR-0042 §2).

## Scope
- FU-H repro (T422 report): `free_one<A>()` evaluates `size_of<T>()` as 8 for a 24-byte `A` (interp); `g.one<A>()` is
  an undefined symbol natively; `join_all<T>() -> Result<GroupResults<T>, E>` needs an annotated result today.
- FU-D repro: inside a generic function with `F: Future<Output = i64>`, calling `h<F, T>(fut: mut_view<F>, ..) ->
  Poll<Result<T, E>>` does not infer `T = i64` from the bound (`AX_TYPE_MISMATCH`/`AX_TYPE_UNKNOWN`).
- FU-5 repro (T421 report): `let h = self.exec.spawn(Child {..}, poll_child)` inside a `Future::poll` reports
  `AX_TYPE_UNKNOWN`; the same call in `main` infers.
- Tests: `tests/run/generic_explicit_args/*.ax` (interp/native/native-O1, exact `// stdout:`), `tests/typeck/infer_from_bounds/*`.
- Regenerate selfhost bundles of edited modules with their generators.

## Acceptance
- [ ] The three repros compile without annotations and print the expected values in all modes.
- [ ] An ambiguous call (no argument, no bound, no annotation) still reports the spec'd inference error.
- [ ] Gate per axiom-qa.md "Per-task gate scope"; failing ids ⊆ baseline; WEAK-NATIVE 0 for new tests.
- [ ] Report `_workspaces/reports/T448-report.md` with exact `## Files changed`.

## Out of scope
- Generic functions as values (T422a), `std/` API changes (T422c), `bootstrap/axiom0`, `docs/`.

## Log
- 2026-11-13 created by axiom-architect (ADR-0042 §2; T422 FU-D, FU-H; T421 FU-5)
