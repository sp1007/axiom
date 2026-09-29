---
id: T050
title: Verifier v2: ownership/capability/drop re-verification
phase: P6-ownership
owner: axiom-semantics
reviewer: axiom-qa
depends: [T049]
priority: 70
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/verify, tests/verify/own]
spec: [0027, 0029, 0034, 0035, 0019, 0020]
---
# T050 — Verifier v2: ownership/capability/drop re-verification

## Goal
Independent verification that elaborated MIR respects the ownership model (defence in depth).

## Scope
- Verifier checks move/drop/view invariants on MIR independent from the analysis that produced it; driver refuses unverified MIR.

## Acceptance
- [ ] Hand-written invalid MIR (double drop, use after move, missing drop) rejected.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T050-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
