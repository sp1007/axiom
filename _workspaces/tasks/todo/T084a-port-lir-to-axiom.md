---
id: T084a
title: Port LIR data model and builder to Axiom
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T082d]
priority: 118
status: todo
attempts: 0
paths: [compiler/lir, tests/selfhost/lir]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-LIR-030, REQ-LAY-298]
---
# T084a — Port LIR data model and builder to Axiom

## Goal
Port Low-level Intermediate Representation (LIR) data structures and lowering from MIR (`compiler/lir/`) from C to Axiom.

## Scope
- Port LIR virtual registers, instruction opcodes, machine basic blocks, and operands.
- Port lowering from MIR to LIR virtual register instructions.
- Unit tests under `tests/selfhost/lir/`.

## Acceptance
- [ ] LIR builder implemented in `compiler/lir/` — complete and readable: no line-packing or dropped features to meet a size target; ~1.5k lines per file is a split guide, not a limit (a larger module is split into several files under the task's paths, AXS-SELF-004).
- [ ] Unit tests pass in both interpreter and native modes.
- [ ] LIR instruction stream matches `axiom0 inspect --emit=lir` on representative test programs.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T084a-report.md` with exact `## Files changed`.

## Out of scope
- ABI lowering and machine code encoding (handled in T084b–T084d).

## Notes
- Sub-task of T084 split per ADR-0005 §8 and SPEC-20 §4.8.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
