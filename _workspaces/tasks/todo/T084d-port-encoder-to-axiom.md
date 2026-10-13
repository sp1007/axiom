---
id: T084d
title: Port x64 machine code encoder to Axiom
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T084c]
priority: 118
status: todo
attempts: 0
paths: [compiler/target/x64/encode.ax, tests/selfhost/encode]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-X64-001]
---
# T084d — Port x64 machine code encoder to Axiom

## Goal
Port x86-64 machine code binary encoder (`compiler/target/x64/encode.ax`) from C to Axiom.

## Scope
- Port binary encoding of x86-64 instructions: REX prefixes, opcode maps, ModR/M byte, SIB byte, displacements, and immediates.
- Port relocation record generation for function calls, rodata labels, and branch targets.
- Unit tests under `tests/selfhost/encode/`.

## Acceptance
- [ ] x64 encoder implemented in `compiler/target/x64/encode.ax` with ≤ 1,500 lines of Axiom.
- [ ] Unit tests pass in both interpreter and native modes.
- [ ] Emitted machine code bytes match `axiom0` byte-for-byte across instruction fixtures.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T084d-report.md` with exact `## Files changed`.

## Out of scope
- COFF object file formatting (handled in T085a).

## Notes
- Sub-task of T084 split per ADR-0005 §8 and SPEC-20 §4.8.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
