---
id: T082a
title: Port MIR data model and MIR builder to Axiom
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T081]
priority: 116
status: todo
attempts: 0
paths: [compiler/mir/mir.ax, compiler/mir/builder.ax, tests/selfhost/mir]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-MIR-338, REQ-MIR-339, REQ-MIR-340]
---
# T082a — Port MIR data model and MIR builder to Axiom

## Goal
Port Mid-level Intermediate Representation (MIR) data structures and HIR->MIR lowering (`compiler/mir/`) from C to Axiom.

## Scope
- Port MIR control-flow graph (CFG), basic blocks, statements (assign, storage live/dead), terminators (goto, switch_int, return, call, panic), rvalues, and operands.
- Port lowering from typed HIR to raw unoptimized MIR.
- Unit tests under `tests/selfhost/mir/`.

## Acceptance
- [ ] MIR builder implemented in `compiler/mir/` — complete and readable: no line-packing or dropped features to meet a size target; ~1.5k lines per file is a split guide, not a limit (a larger module is split into several files under the task's paths, AXS-SELF-004).
- [ ] Unit tests pass in both interpreter and native modes.
- [ ] Unoptimized MIR CFG matches `axiom0 inspect --emit=mir-raw` on representative test programs.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T082a-report.md` with exact `## Files changed`.

## Out of scope
- Ownership analyses, drop elaboration, and MIR verification (handled in T082b–T082e).

## Notes
- `model: opus`: MIR construction requires semantic precision (model policy).
- Sub-task of T082 split per ADR-0005 §8 and SPEC-20 §4.6.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
