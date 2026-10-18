---
id: T084c
title: Port x64 instruction selection and frame lowering to Axiom
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T084b, T084d]
priority: 118
status: doing
attempts: 1
paths: [compiler/target/x64, tests/selfhost/isel]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-TGT-327, REQ-X64-001]
started: 2026-10-18 15:53:32
agent: T084c-impl
---
# T084c — Port x64 instruction selection and frame lowering to Axiom

## Goal
Port x86-64 instruction selection and stack frame layout (`compiler/target/x64/isel.ax`, `frame.ax`) from C to Axiom.

## Scope
- Port instruction selection: mapping LIR virtual instructions to concrete x86-64 machine instructions.
- Port stack frame layout, local variable offset calculation, and function prologue/epilogue synthesis.
- Unit tests under `tests/selfhost/isel/`.

## Acceptance
- [ ] Instruction selector and frame layout implemented — complete and readable: no line-packing or dropped features to meet a size target; ~1.5k lines per file is a split guide, not a limit (a larger module is split into several files under the task's paths, AXS-SELF-004).
- [ ] Unit tests pass in both interpreter and native modes.
- [ ] Selected instruction sequence and stack frame layout match `axiom0`.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T084c-report.md` with exact `## Files changed`.

## Out of scope
- Machine code binary encoding (handled in T084d).

## Notes
- Sub-task of T084 split per ADR-0005 §8 and SPEC-20 §4.8.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-18 15:53:32 started (attempt 1) T084c-impl
