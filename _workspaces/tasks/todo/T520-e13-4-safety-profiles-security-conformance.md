---
id: T520
title: E13.4 — Safety profiles, capability security & constant-time conformance suite
phase: P13-low-level-systems-unsafe-frees
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T517, T518, T519]
priority: 169
status: todo
attempts: 0
paths: [tests/conformance/p13/e13_4_security_profiles]
spec: [spec/SPEC-53-safety-profiles-capability-security.md, tasks/0342, tasks/0449, tasks/0467, tasks/0703]
covers: [REQ-CAP-137, REQ-CAP-123, REQ-CAP-131, REQ-CAP-010]
---
# T520 — E13.4 — Safety profiles, capability security & constant-time conformance suite

## Goal
Certify E13.4 exit criteria with a conformance suite covering `@forbid_unsafe`, `--safety-profile sandbox`, capability authority tokens, `Secret<T>` zeroization, and `@constant_time` verification.

## Scope
- Create positive and negative conformance tests in `tests/conformance/p13/e13_4_security_profiles` testing `@forbid_unsafe`, sandboxed capability-only execution, pin/buffer lifetime preservation (`REQ-CAP-137`), `Secret<T>` zeroization, and `@constant_time` timing-leak rejection.
- Run all executable security conformance tests in both `--interp` and native modes.

## Acceptance
- [ ] All positive and negative conformance tests in `tests/conformance/p13/e13_4_security_profiles` pass in `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] Report `_workspaces/reports/T520-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P13 (`P13-low-level-systems-unsafe-frees`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T520/build` and `python tools/axtest.py --compiler build-snap-T520/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-03 02:03:00 created by T213 (P13 phase planning)
