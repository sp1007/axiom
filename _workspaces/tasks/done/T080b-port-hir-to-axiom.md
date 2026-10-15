---
id: T080b
title: Port HIR data model and lowering to Axiom
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T080a]
priority: 114
status: done
attempts: 1
paths: [compiler/hir, tests/selfhost/hir]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-MOD-142, REQ-RES-243]
started: 2026-10-15 10:23:09
finished: 2026-10-15 11:31:49
---
# T080b — Port HIR data model and lowering to Axiom

## Goal
Port High-level Intermediate Representation (HIR) and AST->HIR lowering (`compiler/hir/`) from C to Axiom.

## Scope
- Port HIR node structures, definition IDs, and lowering from AST to HIR.
- Port pattern desugaring, `for`-loop desugaring, and path resolution lowering.
- Unit tests under `tests/selfhost/hir/`.

## Acceptance
- [ ] HIR lowering implemented in `compiler/hir/` — complete and readable: no line-packing or dropped features to meet a size target; ~1.5k lines per file is a split guide, not a limit (a larger module is split into several files under the task's paths, AXS-SELF-004).
- [ ] Unit tests pass in both interpreter and native modes.
- [ ] Emitted HIR matches `axiom0 inspect --emit=hir` on representative test programs.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T080b-report.md` with exact `## Files changed`.

## Out of scope
- Full corpus differential validation (handled in integration task T080).

## Notes
- Sub-task of T080 split per ADR-0005 §8 and SPEC-20 §4.4.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-15 10:23:09 started (attempt 1) axiom-frontend
- 2026-10-15 11:31:49 finished without commit (manual) -> done; run `taskctl commit` next
