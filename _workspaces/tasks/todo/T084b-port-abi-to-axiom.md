---
id: T084b
title: Port Windows x64 ABI lowering to Axiom
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T084a]
priority: 118
status: todo
attempts: 0
paths: [compiler/abi, tests/selfhost/abi]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-ABI-106, REQ-ABI-107, REQ-ABI-108]
---
# T084b — Port Windows x64 ABI lowering to Axiom

## Goal
Port Windows x64 calling conventions and ABI register allocation rules (`compiler/abi/`) from C to Axiom.

## Scope
- Port parameter passing conventions (RCX, RDX, R8, R9, stack arguments), return value rules, and caller/callee-saved registers.
- Port shadow space allocation (32 bytes mandatory home space) and 16-byte stack alignment invariants.
- Unit tests under `tests/selfhost/abi/`.

## Acceptance
- [ ] Windows x64 ABI lowering implemented in `compiler/abi/` — complete and readable: no line-packing or dropped features to meet a size target; ~1.5k lines per file is a split guide, not a limit (a larger module is split into several files under the task's paths, AXS-SELF-004).
- [ ] Unit tests pass in both interpreter and native modes.
- [ ] ABI register assignment and call argument passing match `axiom0`.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T084b-report.md` with exact `## Files changed`.

## Out of scope
- Machine code encoding (handled in T084d).

## Notes
- Sub-task of T084 split per ADR-0005 §8 and SPEC-20 §4.8.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
