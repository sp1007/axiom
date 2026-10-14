---
id: T085c
title: Port compiler driver & pipeline CLI to Axiom
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T085b]
priority: 119
status: todo
attempts: 0
paths: [compiler/driver, tests/selfhost/driver]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-DRV-022]
---
# T085c — Port compiler driver & pipeline CLI to Axiom

## Goal
Port the command-line driver and pipeline orchestrator (`compiler/driver/`) from C to Axiom.

## Scope
- Port CLI option parsing (`build`, `check`, `inspect`, `run`), output path handling, and target flag options.
- Port pipeline orchestration linking all compiler passes from source to binary output.
- Port inspection emitters (`inspect --emit=tokens|ast|hir|thir|mir|mir-opt|lir|obj`).
- Unit tests under `tests/selfhost/driver/`.

## Acceptance
- [ ] Compiler driver implemented in `compiler/driver/` — complete and readable: no line-packing or dropped features to meet a size target; ~1.5k lines per file is a split guide, not a limit (a larger module is split into several files under the task's paths, AXS-SELF-004).
- [ ] Unit tests pass in both interpreter and native modes.
- [ ] Driver CLI commands and flags produce identical outputs to `axiom0`.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T085c-report.md` with exact `## Files changed`.

## Out of scope
- Full self-hosting bootstrap pipeline (handled in T086 and T087).

## Notes
- Sub-task of T085 split per ADR-0005 §8 and SPEC-20 §4.9.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
