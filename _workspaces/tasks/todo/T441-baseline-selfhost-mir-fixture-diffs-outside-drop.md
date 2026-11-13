---
id: T441
title: Baseline fix — selfhost MIR comparisons outside drop (interp_opt diff_mir_b exit 312, own_mir_verify diff_drop_b exit 301)
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T452, T435]
priority: 18
status: todo
attempts: 0
timeout_min: 900
paths: [tests/selfhost/interp_opt, tests/selfhost/own_mir_verify]
locks: [tests/selfhost, _workspaces/baseline-failures.txt]
spec: [spec/decisions/ADR-0042-architect-inbox-1-baseline-admissions-and-followups.md, spec/decisions/ADR-0041-complete-suite-baseline-and-test-cache.md, spec/SPEC-12-drop.md, spec/SPEC-20-selfhost.md]
covers: [REQ-TST-089, REQ-TST-034]
---
# T441 — Baseline fix: selfhost MIR comparisons outside `selfhost/drop`

## Goal
`selfhost/interp_opt/qa_interp_opt_diff_mir_b.ax` and `selfhost/own_mir_verify/qa_own_mir_diff_drop_b.ax` pass in
interp, native and native-O1 and stay green when the implicitly loaded prelude grows (ADR-0042 §1).

## Scope
- Observed (T452 report, T452-qa, identical at HEAD): `qa_interp_opt_diff_mir_b` exits 312 in native and native-O1
  (case 12: optimized MIR differs from its fixture); `qa_own_mir_diff_drop_b` exits 301 (case 1 build).
- First diagnose: print the first differing line of each case. If it is type-id/def-id numbering coupled to prelude
  contents (the T435 cause), apply the comparison T435 introduced (pinned prelude/std root or canonical ids, see
  T435's report and generator) to these generators; regenerate fixtures and bundles only with their generators
  (`gen_*_tests.py`), never by hand.
- If it is a real builder/optimizer/drop-elaboration difference, it is a compiler bug: stop, report a minimal repro
  for a split (architect); the ids stay on the baseline under the new task.
- Remove the two `T441` lines from `_workspaces/baseline-failures.txt` when they pass.

## Acceptance
- [ ] Both ids pass in all their modes under `axiomc2.exe` built in `build-snap-T441`; `selfhost/interp_opt/bundles_current.test`
  and `selfhost/own_mir_verify/bundles_current.test` pass.
- [ ] Mutation proof: one fixture byte changed makes each bundle fail in native (exit != 0) — shows the comparison is live.
- [ ] The other bundles of both groups still pass (they share the generators).
- [ ] Gate per axiom-qa.md "Per-task gate scope"; failing ids ⊆ baseline after the removals; WEAK-NATIVE 0 for both groups.
- [ ] Report `_workspaces/reports/T441-report.md` with exact `## Files changed`.

## Out of scope
- Editing `compiler/` (a compiler difference becomes a new task), `bootstrap/axiom0`, `docs/`.

## Notes
- Depends on T435 so the drop-group decision exists first and is reused rather than reinvented.

## Log
- 2026-11-13 created by axiom-architect (ADR-0042 §1, architect inbox 1)
