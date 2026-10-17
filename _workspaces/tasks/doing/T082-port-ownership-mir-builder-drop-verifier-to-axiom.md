---
id: T082
title: Port ownership, MIR builder, drop, verifier to Axiom (integration + differential MIR)
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T082a, T082b, T082c, T082d, T082e]
priority: 116
status: doing
attempts: 1
paths: [compiler/own_mir_verify, tests/selfhost/own_mir_verify]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-DRP-183, REQ-ERR-087, REQ-MIR-338, REQ-MIR-339, REQ-MIR-340, REQ-OWN-338]
started: 2026-10-18 04:36:29
agent: T082-impl
---
# T082 — Port ownership, MIR builder, drop, verifier to Axiom (integration + differential MIR)

## Goal
Integrate ownership, MIR builder, drop elaboration, and verifier in Axiom and run differential MIR testing against `axiom0`.

## Scope
- Integrate `compiler/mir`, `compiler/own`, and `compiler/verify`.
- Differential test harness comparing elaborated MIR with `axiom0 inspect --emit=mir` over the whole tests corpus.
- Verification of ownership move rules, initialization tracking, and drop insertion.

## Acceptance
- [ ] Differential equality over the corpus (documented counts); module tests pass in interp and native.
- [ ] Sub-tasks T082a through T082e integrated and passing differential checks.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T082-report.md` with exact `## Files changed`.

## Out of scope
- Interpreter and optimization passes (handled in T083).

## Notes
- `model: opus`: Porting ownership, MIR, drop, and verifier requires semantic precision (model policy).
- Group integration task for T082a–T082e per ADR-0005 §8 and SPEC-20 §4.6.
- Exact differential artefact: `inspect --emit=mir`.
- Harness entry: `tests/selfhost/own_mir_verify`.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-18 04:36:29 started (attempt 1) T082-impl
