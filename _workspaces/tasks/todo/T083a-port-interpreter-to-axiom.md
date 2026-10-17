---
id: T083a
title: Port MIR interpreter and host oracle to Axiom
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T082d]
priority: 117
status: todo
attempts: 0
paths: [compiler/interp, tests/selfhost/interp]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-OPT-387]
---
# T083a — Port MIR interpreter and host oracle to Axiom

## Goal
Port the MIR step execution interpreter and host interface oracle (`compiler/interp/`) from C to Axiom.

## Scope
- Port runtime value representation, stack frames, heap allocation emulation, and step evaluation loop.
- Port host interface oracle calls (heap, file I/O, process, clock) matching ADR-0002.
- Unit tests under `tests/selfhost/interp/`.

## Acceptance
- [ ] MIR interpreter implemented in `compiler/interp/` — complete and readable: no line-packing or dropped features to meet a size target; ~1.5k lines per file is a split guide, not a limit (a larger module is split into several files under the task's paths, AXS-SELF-004).
- [ ] Unit tests pass in both interpreter and native modes.
- [ ] Program execution exit codes and standard output match `axiom0` in interp mode.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T083a-report.md` with exact `## Files changed`.

## Out of scope
- MIR optimizer (handled in T083b).

## Notes
- `model: opus`: Porting the interpreter and comptime oracle requires semantic precision (model policy).
- Sub-task of T083 split per ADR-0005 §8 and SPEC-20 §4.7.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
