---
id: T077
title: Port kernel, source DB, diagnostics to Axiom (integration + differential)
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T077a, T077b, T077c]
priority: 111
status: done
attempts: 1
paths: [compiler/kernel_source_diag, tests/selfhost/kernel_source_diag]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-DRV-020, REQ-DRV-021]
started: 2026-10-14 06:54:10
finished: 2026-10-14 07:22:46
---
# T077 — Port kernel, source DB, diagnostics to Axiom (integration + differential)

## Goal
Integrate kernel, source DB, and diagnostics in Axiom and run differential testing against `axiom0`.

## Scope
- Integrate `compiler/kernel`, `compiler/source`, and `compiler/diag`.
- Differential test harness comparing outputs with `axiom0` across the entire tests corpus.
- Verification of `--json` error emission and source span rendering.

## Acceptance
- [ ] Differential equality over the corpus (documented counts); integration tests pass in interp and native.
- [ ] Sub-tasks T077a, T077b, T077c integrated into a cohesive subsystem.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T077-report.md` with exact `## Files changed`.

## Out of scope
- Lexer and parser (handled in T078 and T079).

## Notes
- Group integration task for T077a, T077b, T077c per ADR-0005 §8 and SPEC-20 §4.1.
- Exact differential artefact: `--json` error diagnostics and data structure dumps.
- Harness entry: `tests/selfhost/kernel_source_diag`.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-14 06:54:10 started (attempt 1) 
- 2026-10-14 07:22:46 accepted by QA -> done
