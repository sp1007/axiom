---
id: T084d
title: Port x64 machine code encoder to Axiom
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T085a]
priority: 118
status: doing
attempts: 1
paths: [compiler/target/x64/encode.ax, tests/selfhost/encode]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-X64-001]
started: 2026-10-18 14:53:18
agent: T084d-impl
---
# T084d — Port x64 machine code encoder to Axiom

## Goal
Port x86-64 machine code binary encoder (`compiler/target/x64/encode.ax`) from C to Axiom.

## Scope
- Port binary encoding of x86-64 instructions: REX prefixes, opcode maps, ModR/M byte, SIB byte, displacements, and immediates.
- Port relocation record generation for function calls, rodata labels, and branch targets.
- Unit tests under `tests/selfhost/encode/`.

## Acceptance
- [ ] x64 encoder implemented in `compiler/target/x64/encode.ax` — complete and readable: no line-packing or dropped features to meet a size target; ~1.5k lines per file is a split guide, not a limit (a larger module is split into several files under the task's paths, AXS-SELF-004).
- [ ] Unit tests pass in both interpreter and native modes.
- [ ] Emitted machine code bytes match `axiom0` byte-for-byte across instruction fixtures.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T084d-report.md` with exact `## Files changed`.

## Out of scope
- COFF object file formatting (handled in T085a).

## Notes
- Sub-task of T084 split per ADR-0005 §8 and SPEC-20 §4.8.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-18 14:53:18 started (attempt 1) T084d-impl
