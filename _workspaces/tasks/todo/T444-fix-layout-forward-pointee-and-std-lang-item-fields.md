---
id: T444
title: Fix — struct layout through a forward-referenced pointee (FU-1) and lang-item struct fields inside std.* modules (FU-3)
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T452]
priority: 21
status: todo
attempts: 0
timeout_min: 900
paths: [compiler/types/layout.ax, tests/run/layout_fwd_pointee]
locks: [compiler/types/types.ax, compiler/types/typeck.ax, compiler/resolve, compiler/lir/builder.ax, tests/selfhost]
spec: [spec/decisions/ADR-0042-architect-inbox-1-baseline-admissions-and-followups.md, spec/SPEC-03-core-semantics.md, spec/SPEC-33-async.md]
covers: [REQ-TST-072, REQ-TST-084]
---
# T444 — Fix: layout through forward-referenced pointees and lang-item fields in std modules

## Goal
Field offsets are correct regardless of declaration order and of the module a struct lives in, in the oracle and
natively (T421 FU-1, FU-3; ADR-0042 §2).

## Scope
- FU-1 repro (T421 report): `struct W { id: usize, inner: *mut Inner }` declared before
  `struct Inner { count: usize, ptr: *mut u8 }`; fields set through `heap_alloc`ed memory; reading
  `(*(*w).inner).ptr` gives 0 (interp) / the first word for every field (native). Swapping the declarations fixes it.
  Root cause expected in layout computation of a pointee type not yet laid out when the pointer field is processed.
- FU-3 repro: a node struct with a field of type `Waker`/`RawWaker` declared in a module whose path starts with `std`
  (`(*n).waker = w; (*n).waker.raw.data` reads 0 / shifted words); the identical struct in module `zz.yy` works.
  Find the special handling of `@lang("waker")` (or of `std.*` paths) that bypasses normal layout and remove it.
- Regression tests `tests/run/layout_fwd_pointee/*.ax` (multi-file module where needed for the `std`-path case, via the
  test's own std root or an `std.`-prefixed test module) in interp, native, native-O1 with exact `// stdout:`.
- Regenerate with their generators the selfhost bundles that embed edited modules; all `bundles_current.test` pass.
- Do not touch `std/async` (the T421 workarounds `*mut u8` and `waker_data`/`waker_vt` stay; T421a/T422c may remove them).

## Acceptance
- [ ] Both repros (and declaration-order / module-path permutations) print the expected values in all three modes.
- [ ] `tests/std/async` still passes (no behaviour change for the workarounds).
- [ ] Gate per axiom-qa.md "Per-task gate scope"; failing ids ⊆ baseline; WEAK-NATIVE 0 for the new tests.
- [ ] Report `_workspaces/reports/T444-report.md` with exact `## Files changed`.

## Out of scope
- `bootstrap/axiom0` (frozen), `std/`, `docs/`.

## Notes
- If the fix lies outside the listed locks, stop and report (architect widens the locks).
- Canonical syntax (`=`, `.`), see axiom-syntax.

## Log
- 2026-11-13 created by axiom-architect (ADR-0042 §2; T421 FU-1, FU-3)
