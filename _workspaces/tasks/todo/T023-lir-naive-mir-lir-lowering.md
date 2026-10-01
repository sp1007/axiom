---
id: T023
title: LIR + naive MIR→LIR lowering
phase: P4-native
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T021, T003a, T022]
priority: 40
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/lir, tests/lir, bootstrap/axiom0/src/driver/emit_lir.c]
spec: [0162, 0179, 0215, 0232, 0049, spec/SPEC-04-core-extensibility.md]
---
# T023 — LIR + naive MIR→LIR lowering

## Goal
Machine-independent low-level IR: explicit memory, stack slots, calls; MIR ownership erased.

## Scope
- LIR data model + printer (`--emit=lir`); naive lowering: every MIR local → stack slot; operations → LIR ops; calls with abstract ABI placeholders.
- Call sites and function entries use abstract ABI placeholders; the `abi` pass of T025 rewrites them (ADR-0003: ABI lowering is a LIR→LIR pass before instruction selection).

## Acceptance
- [ ] Golden LIR tests: one per tests/run/basic program and one per LIR op kind (`tests/lir/COVERAGE.md` maps op kind → test file).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T023-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
