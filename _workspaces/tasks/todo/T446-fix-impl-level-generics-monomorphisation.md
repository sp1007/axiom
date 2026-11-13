---
id: T446
title: Fix — impl-level generics are monomorphised (layout, size_of, needs_drop, trait dispatch on the parameter, native instantiation) (FU-F, FU-G)
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: opus
depends: [T452]
priority: 21
status: todo
attempts: 0
timeout_min: 900
paths: [compiler/traits/mono.ax, tests/run/generic_impl_mono]
locks: [compiler/traits/solver.ax, compiler/types/typeck.ax, compiler/types/layout.ax, compiler/mir/builder.ax, compiler/lir/builder.ax, tests/selfhost]
spec: [spec/decisions/ADR-0042-architect-inbox-1-baseline-admissions-and-followups.md, spec/SPEC-03-core-semantics.md, spec/SPEC-04-core-extensibility.md]
covers: [REQ-TST-072, REQ-TST-051]
---
# T446 — Fix: monomorphisation of impl-level generic parameters

## Goal
Methods of `impl<F> T<F>` / `impl<F: Tr> Tr2 for T<F>` are instantiated per concrete `F` exactly like free generic
functions: layout, `size_of<F>()`, `needs_drop<F>()` and trait calls on `F` use the concrete type, in the oracle and
natively (T422 FU-F, FU-G; ADR-0042 §2).

## Scope
- FU-F repro (T422 report): `struct Wrap<F> { a: u64, flag: u32, fut: F }` constructed with a 16-byte `F`; a method
  `fn m(self: mut_view<Wrap<F>>)` printing `self.a`, `self.flag` prints the wrong words (`a=5 flag=9` for `a=9,
  flag=7`); offsets use an 8-byte placeholder, fields are reordered, `size_of<F>()` is the placeholder and
  `needs_drop<F>()` is `false`.
- FU-G repro: in `impl<F: Future<Output = i64>> Future for W<F>`, `self.fut.poll(..)` binds to the first `Future` impl
  in scope instead of `F`'s; a generic free function called from such a method is not instantiated natively
  (`AX_LINK_UNDEFINED_SYMBOL: show`).
- Substitute the impl's generic arguments into every method body before layout, drop elaboration and trait
  resolution; instantiate callees reached from instantiated methods (worklist), natively too.
- Tests `tests/run/generic_impl_mono/*.ax`: field offsets with 1/8/16/24-byte `F`, `size_of`, `needs_drop` with a
  `Drop` type, trait dispatch with two impls in scope, nested generic call; interp/native/native-O1, exact `// stdout:`.
- Regenerate selfhost bundles of edited modules with their generators.

## Acceptance
- [ ] Both repros print the correct values in all three modes; `@repr(C)` is no longer needed for correctness.
- [ ] `tests/run/generic*`, `tests/run/trait*`, `tests/std` pass.
- [ ] Gate per axiom-qa.md "Per-task gate scope"; failing ids ⊆ baseline; WEAK-NATIVE 0 for new tests.
- [ ] Report `_workspaces/reports/T446-report.md` with exact `## Files changed`.

## Out of scope
- Explicit type arguments / inference (T448), associated types and overlap (T447), `std/` API changes (T422c),
  `bootstrap/axiom0`, `docs/`.

## Log
- 2026-11-13 created by axiom-architect (ADR-0042 §2; T422 FU-F, FU-G)
