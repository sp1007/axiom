---
id: T722
title: E17.6 Address, memory, UB, bounds & thread sanitizer conformance suite
phase: P17-debugging-runtime-introspectio
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T217, T316, T721]
priority: 193
status: todo
attempts: 0
paths: [tests/conformance/p17/e17_6_sanitizers]
spec: [spec/SPEC-97-sanitizers-runtime-verification.md, 0147, tasks/0599, tasks/0694, tasks/0733]
covers: [REQ-DBG-116, REQ-DBG-120]
---
# T722 — E17.6 Address, memory, UB, bounds & thread sanitizer conformance suite

## Goal
Certify the E17.6 and P17 sanitizer suite exit criterion: zero false positives on valid programs and exact source-mapped detection across Address, Bounds, Provenance, Memory, UB, and Thread sanitizers.

## Scope
- Create `tests/conformance/p17/e17_6_sanitizers` covering:
-   - Positive conformance: safe and sound `unsafe` corpus programs run under `--sanitize=all` with zero false positives and identical outputs to uninstrumented builds.
-   - `ASan`/`Bounds`/`Provenance` negative tests: heap buffer overflow, stack buffer overflow, use-after-free, double-free, out-of-bounds raw pointer arithmetic, and stale provenance tag dereference.
-   - `MSan` negative tests: reading uninitialized `MaybeUninit<T>` bytes and partially initialized struct fields.
-   - `UBSan` negative tests: misaligned raw pointer load/store, null raw pointer dereference, invalid shift width, unchecked `unsafe` integer overflow, and invalid enum discriminant transmutation.
-   - `TSan` negative tests: unsynchronized `unsafe` shared-memory data race and ABBA mutex lock-order inversion.

## Acceptance
- [ ] All conformance tests in `tests/conformance/p17/e17_6_sanitizers` pass.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T722-report.md` with exact `## Files changed`.

## Out of scope
- Trace and replay conformance (`T726`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P17 (`P17-debugging-runtime-introspectio`), depends on P16 gate `T316` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all implementation lives in `compiler/` and `std/`.
- All Axiom code and examples use canonical syntax (`axiom-syntax`): `=` only, `.` paths only.

## Log
- 2026-11-03 09:25:00 created by T217 (P17 phase planning)
