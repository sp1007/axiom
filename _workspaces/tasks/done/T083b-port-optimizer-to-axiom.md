---
id: T083b
title: Port MIR optimizer (-O1 const folding, DCE, CFG simplify) to Axiom
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T082e]
priority: 117
status: done
attempts: 1
paths: [compiler/opt, tests/selfhost/opt]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-OPT-388, REQ-OPT-389]
started: 2026-10-18 04:48:31
finished: 2026-10-18 10:52:47
---
# T083b — Port MIR optimizer (-O1 const folding, DCE, CFG simplify) to Axiom

## Goal
Port the MIR -O1 baseline optimizer (`compiler/opt/`) from C to Axiom.

## Scope
- Port constant folding on scalar types and checked arithmetic operations.
- Port dead code elimination (DCE) for unreachable blocks and unused statements.
- Port CFG simplification: merging linear blocks and eliminating redundant conditional jumps.
- Unit tests under `tests/selfhost/opt/`.

## Acceptance
- [ ] Optimizer implemented in `compiler/opt/` — complete and readable: no line-packing or dropped features to meet a size target; ~1.5k lines per file is a split guide, not a limit (a larger module is split into several files under the task's paths, AXS-SELF-004).
- [ ] Unit tests pass in both interpreter and native modes.
- [ ] Optimized MIR matches `axiom0 inspect --emit=mir-opt` on optimization test fixtures.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T083b-report.md` with exact `## Files changed`.

## Out of scope
- Advanced optimization ladder 2 (copy prop, inlining, SROA: deferred to post-self-host T064).

## Notes
- `model: opus`: Optimization passes require careful correctness and transformation legality (model policy).
- Sub-task of T083 split per ADR-0005 §8 and SPEC-20 §4.7.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-18 04:48:31 started (attempt 1) T083b-impl
- 2026-10-18 10:52:47 accepted by QA -> done
