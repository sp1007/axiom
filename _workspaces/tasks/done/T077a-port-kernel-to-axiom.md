---
id: T077a
title: Port kernel to Axiom (arena, interner, hashtable, dynarray, idtable)
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T076]
priority: 111
status: done
attempts: 1
paths: [compiler/kernel, tests/selfhost/kernel]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-DRV-020]
started: 2026-10-14 03:45:04
finished: 2026-10-14 04:14:45
---
# T077a — Port kernel to Axiom (arena, interner, hashtable, dynarray, idtable)

## Goal
Port the core kernel utilities and data structures (`compiler/kernel/`) from C to Axiom.

## Scope
- Port arena allocator, string interner, 64-bit compiler hash, growable arrays, and typed ID tables to Axiom.
- Ensure identical string interning semantics and deterministic hashing matching `bootstrap/axiom0/src/kernel/`.
- Unit tests under `tests/selfhost/kernel/`.

## Acceptance
- [ ] Core data structures implemented in `compiler/kernel/` with ≤ 1,500 lines of Axiom.
- [ ] Unit tests pass in both interpreter and native modes.
- [ ] Differential test verifies interning and hashing agree with `axiom0`.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T077a-report.md` with exact `## Files changed`.

## Out of scope
- Source file database and diagnostics (handled in T077b and T077c).

## Notes
- Sub-task of T077 split per ADR-0005 §8 and SPEC-20 §4.1.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-14 03:45:04 started (attempt 1) 
- 2026-10-14 04:14:45 accepted by QA -> done
