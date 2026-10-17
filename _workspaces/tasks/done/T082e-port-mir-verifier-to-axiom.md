---
id: T082e
title: Port MIR verifier to Axiom
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T082d]
priority: 116
status: done
attempts: 1
paths: [compiler/verify, tests/selfhost/verify]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-ERR-087]
started: 2026-10-17 23:03:18
finished: 2026-10-18 04:36:02
---
# T082e — Port MIR verifier to Axiom

## Goal
Port the MIR invariant verifier (`compiler/verify/`) from C to Axiom.

## Scope
- Port verification of CFG well-formedness, typed local consistency, and terminator reachability.
- Port verification of capability invariants and drop flag consistency.
- Unit tests under `tests/selfhost/verify/`.

## Acceptance
- [ ] MIR verifier implemented in `compiler/verify/` — complete and readable: no line-packing or dropped features to meet a size target; ~1.5k lines per file is a split guide, not a limit (a larger module is split into several files under the task's paths, AXS-SELF-004).
- [ ] Unit tests pass in both interpreter and native modes.
- [ ] Verifier correctly accepts valid MIR and rejects malformed IR fixtures identically to `axiom0`.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T082e-report.md` with exact `## Files changed`.

## Out of scope
- MIR interpretation and optimization (handled in T083).

## Notes
- `model: opus`: MIR verification requires semantic precision (model policy).
- Sub-task of T082 split per ADR-0005 §8 and SPEC-20 §4.6.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-17 21:39:33 started (attempt 1) T082e-impl
- 2026-10-17 23:03:16 requeue: restart (not charged: attempt refunded)
- 2026-10-17 23:03:18 started (attempt 1) T082e-impl
- 2026-10-18 04:36:02 accepted by QA -> done
