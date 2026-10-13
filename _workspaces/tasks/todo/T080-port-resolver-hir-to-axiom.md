---
id: T080
title: Port resolver + HIR to Axiom (integration + differential HIR)
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T080a, T080b]
priority: 114
status: todo
attempts: 0
paths: [compiler/resolve_hir, tests/selfhost/resolve_hir]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-MOD-142, REQ-PKG-023, REQ-RES-243]
---
# T080 — Port resolver + HIR to Axiom (integration + differential HIR)

## Goal
Integrate resolver and HIR in Axiom and run differential HIR testing against `axiom0`.

## Scope
- Integrate `compiler/resolve` and `compiler/hir`.
- Differential test harness comparing HIR dumps with `axiom0 inspect --emit=hir` over the whole tests corpus.
- Verification of multi-file module compilation and visibility rules.

## Acceptance
- [ ] Differential equality over the corpus (documented counts); module tests pass in interp and native.
- [ ] Sub-tasks T080a and T080b integrated and passing differential checks.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T080-report.md` with exact `## Files changed`.

## Out of scope
- Type checking (handled in T081).

## Notes
- Group integration task for T080a and T080b per ADR-0005 §8 and SPEC-20 §4.4.
- Exact differential artefact: `inspect --emit=hir`.
- Harness entry: `tests/selfhost/resolve_hir`.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
