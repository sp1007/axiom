---
id: T492
title: Fix — a trait bound naming a `use … as Alias` import fails (AX_TYPE_UNKNOWN_FIELD); retire the 10007/10008/10009 sentinel symbol ids
phase: P12-numeric-floating-point-simd
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T164]
priority: 13
status: doing
attempts: 1
paths: [compiler/traits/solver.ax, compiler/hir/lower.ax, compiler/hir/hir.ax, tests/run/trait_use_alias]
locks: [compiler/resolve]
spec: [spec/SPEC-20-selfhost.md, spec/decisions/ADR-0043-cyclic-type-graphs-and-symbol-id-space.md]
covers: [REQ-RES-060]
started: 2026-11-19 07:30:52
agent: T492-impl
---
# T492 — Trait bound through a `use … as` alias; sentinel ids

## Why
The T164 round-1 gate (`_workspaces/reports/T164-qa.md`, "Alias imports") found a pre-existing bug, identical at HEAD
before and after T164:
```
use std.core.cmp.Ord as StdOrd
fn s<T: StdOrd>(a: view<T>, b: view<T>) -> i32 { ... a.cmp(b) ... }
```
is rejected with `AX_TYPE_UNKNOWN_FIELD` (same for a user trait `use tr.Ord as MyOrd`). The trait-item lookup falls
back to the use-site name (the alias) instead of the trait's own name/defining module. T164 gave `HirPath` the
defining domain/module (`def_dom`, `def_mod`) from the resolver's naming table; the lookup should use the item's own
name from the same table, never the alias spelling.

Also from T164 (report Follow-up 2, QA agreed it may wait): the fixed sentinel symbol ids 10007/10008/10009 (e.g. the
unresolved-`Future` placeholder marked std in `lower.ax`) are leftovers of the old range scheme. Replace them by
explicit flags/real ids so no code compares a `SymbolId` with a constant (ADR-0043 §2, INV-BOOT-005).

## Scope
- Root-cause the alias lookup and fix it in the solver/lowering (both compilers if axiom0 has the same path — if the
  fix needs axiom0, report BLOCKED so the architect creates an AX0-FIX task; axiom0 is frozen).
- Remove the 10007/10008/10009 sentinels in axiomc; `grep -E "1000[789]"` over `compiler/` must find no symbol-id
  comparison afterwards (list what remains and why in the report).
- Regression tests `tests/run/trait_use_alias/`: alias of a std trait, alias of a user trait, alias equal to another
  trait's name, alias used in a generic bound, in `impl Alias for T`, and in a supertrait list; observable stdout +
  exit in interp, native, native-O1.

## Acceptance
- [ ] New tests pass in every mode; mutation proof (one expected value changed → FAIL in all three modes).
- [ ] T164's `tests/run/symbol_id_space/` still passes; fixed point holds; normal gate, failing ids ⊆ baseline.
- [ ] Report `_workspaces/reports/T492-report.md` with exact `## Files changed`.

## Log
- 2026-11-19 created by orchestrator (T164 gate round 1 follow-up: alias imports; T164 report Follow-up 2: sentinels)
- 2026-11-19 07:30:52 started (attempt 1) T492-impl
