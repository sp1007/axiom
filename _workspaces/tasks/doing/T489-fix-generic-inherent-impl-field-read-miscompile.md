---
id: T489
title: Fix silent miscompile — a method of a generic inherent impl reading a field of a struct that has a T-typed field returns 0
phase: P12-numeric-floating-point-simd
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: opus
depends: [T164]
priority: 11
status: doing
attempts: 1
paths: [compiler/mir/builder.ax, compiler/traits, tests/run/generic_inherent_field]
locks: []
spec: [spec/SPEC-20-selfhost.md]
covers: [REQ-OPT-292]
started: 2026-11-20 02:28:33
agent: T489-impl
---
# T489 — Generic inherent impl: field read returns 0

## Why
Found by the T485 gate (`_workspaces/reports/T485-qa.md`, follow-up F-2), pre-existing at HEAD (axiomc2 9c4385ba and
ae078863). Silent wrong code in interp **and** native — the worst kind of compiler bug.

```
struct Wrap<T> { k: i32, v: T }
impl<T> Wrap<T> { fn get(self: view<Wrap<T>>) -> i32 { self.k } }
fn main() -> i32 { let a = Wrap<i32> { k: 3, v: 1 }; a.get() }
```
Expected exit 3; actual 0 (interp 0, native 0; by-value `self`: interp 0 / native 1). Without the `v: T` field it
returns 3. Gate hypothesis: `mb_count_generic_params_in_hir` (compiler/mir/builder.ax) only considers TRAIT impls,
so a member of a generic INHERENT impl is not monomorphized. Confirm by reading, do not assume.

## Scope
- Root-cause and fix; the member must be monomorphized (or rejected with a diagnostic if truly unsupported — it is
  supported by the spec, so fix it).
- Regression tests in `tests/run/generic_inherent_field/`: view self, by-value self, mut_view self, field before and
  after the T field, two instantiations (i32, a struct), method calling another generic inherent method, each with an
  observable result (stdout + exit) in interp, native and native-O1.
- Grep for the same pattern (generic trait-only checks that skip inherent impls) and list any further sites.

## Acceptance
- [ ] All new tests pass in every mode; mutation proof (change one expected value → FAIL in all three modes).
- [ ] Normal gate; self-host fixed point holds.
- [ ] Report `_workspaces/reports/T489-report.md` with exact `## Files changed`.

## Log
- 2026-11-18 created by orchestrator (T485 gate follow-up F-2)
- 2026-11-19 18:41:41 started (attempt 1) T489-impl
- 2026-11-19 18:43:04 requeue: yield to T492 which already has dirty edits in compiler/traits/solver.ax (not charged: attempt refunded)
- 2026-11-20 02:28:33 started (attempt 1) T489-impl
