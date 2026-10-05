---
id: T324
title: Phase P24 gate — Ecosystem runtimes (post-v1)
phase: P24-ecosystem-runtimes-post-v1
owner: axiom-qa
reviewer: axiom-architect
model: opus
gate_model: opus
depends: [T224]
priority: 324
status: deferred
attempts: 0
paths: [tests/conformance/p24, _workspaces/reports/phase-P24-review.md]
spec: [spec/ROADMAP.md]
covers: [REQ-ECO-8733, REQ-ECO-8735, REQ-ECO-8737, REQ-ECO-8738, REQ-ECO-8739, REQ-ECO-8740, REQ-ECO-8741, REQ-ECO-8742, REQ-ECO-8743, REQ-ECO-8744, REQ-ECO-8745, REQ-ECO-8746, REQ-ECO-8747, REQ-ECO-8748, REQ-ECO-8749]
---
# T324 — Phase P24 gate: Ecosystem runtimes (post-v1)

## Goal
Certify that phase P24 meets the exit criteria of every epic E24.1–E24.8 in `spec/ROADMAP.md` §3 and that all requirements mapped to the phase are implemented.

## Scope
- Run the full suite on all supported targets; run each epic's exit-criterion checks.
- `reqcov.py --phase P24-ecosystem-runtimes-post-v1`: every requirement implemented or explicitly re-mapped (with note).
- Collect epic conformance results into `tests/conformance/p24`.

## Acceptance
- [ ] Every epic exit criterion demonstrated with commands and results in the QA report.
- [ ] Full suite green (gate rule: PASS or BLOCKED); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T324-report.md` with exact `## Files changed`.

## Out of scope
- New features; fixes go to new tasks created by the architect.

## Notes
- DEFERRED together with T224: post-v1 ecosystem. It becomes active only when the project owner schedules P24; the autopilot must not unblock it.
- Depends on the planning task T224, which adds every phase task as a dependency of this gate.

## Log
- 2026-10-06 02:23:58 covers += REQ-ECO-8733, REQ-ECO-8735, REQ-ECO-8737, REQ-ECO-8738, REQ-ECO-8739, REQ-ECO-8740, REQ-ECO-8741, REQ-ECO-8742, REQ-ECO-8743, REQ-ECO-8744, REQ-ECO-8745, REQ-ECO-8746, REQ-ECO-8747, REQ-ECO-8748, REQ-ECO-8749 (metadata only)
