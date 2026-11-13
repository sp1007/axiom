---
id: T447
title: Fix — impl generics visible in associated types (FU-B); overlap check honours concrete type arguments (FU-C)
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T452]
priority: 23
status: todo
attempts: 0
timeout_min: 900
paths: [tests/typeck/impl_generics_assoc, tests/ui/trait_overlap_concrete]
locks: [compiler/resolve, compiler/traits/solver.ax, compiler/types/typeck.ax, tests/selfhost]
spec: [spec/decisions/ADR-0042-architect-inbox-1-baseline-admissions-and-followups.md, spec/SPEC-03-core-semantics.md]
covers: [REQ-TST-072, REQ-TST-051]
---
# T447 — Fix: associated types with impl generics; overlap check with concrete arguments

## Goal
`impl<F: Future<Output = T>, T> Future for W<F, T> { type Output = Result<T, E>; ... }` resolves `T`, and
`impl<F> Future for W<F, i64>` / `impl<F> Future for W<F, ()>` are accepted as non-overlapping (T422 FU-B, FU-C;
ADR-0042 §2).

## Scope
- FU-B repro (T422 report): `type Output = Result<T, E>` inside an impl with generics `<F, T>` gives
  `AX_NAME_UNRESOLVED` on `T`; same for `impl<T> Future for GroupNext<T> { type Output = Option<TaskResult<T>>; }`.
  The impl's generic scope must enclose its associated-type definitions.
- FU-C repro: the coherence check reports `AX_TRAIT_OVERLAP` for impls that differ only in a concrete type argument;
  unify the impl headers (fresh variables for the impl generics, concrete types must match) before reporting.
- Tests: `tests/typeck/impl_generics_assoc/*` (positive, the associated type is used through `F.Output`);
  `tests/ui/trait_overlap_concrete/*` (the two impls accepted; a real overlap `impl<F, T>` + `impl<F>` with `T` free
  still gives `AX_TRAIT_OVERLAP`).
- Regenerate selfhost bundles of edited modules with their generators.

## Acceptance
- [ ] Both repros compile; the real-overlap negative test still reports `AX_TRAIT_OVERLAP` with the right span.
- [ ] `tests/typeck`, `tests/ui/trait*`, `tests/resolve` pass (baseline ids excepted).
- [ ] Gate per axiom-qa.md "Per-task gate scope"; failing ids ⊆ baseline.
- [ ] Report `_workspaces/reports/T447-report.md` with exact `## Files changed`.

## Out of scope
- Monomorphisation (T446), inference (T448), `std/`, `bootstrap/axiom0`, `docs/`.

## Log
- 2026-11-13 created by axiom-architect (ADR-0042 §2; T422 FU-B, FU-C)
