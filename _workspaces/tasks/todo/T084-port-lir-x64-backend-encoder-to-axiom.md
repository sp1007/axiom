---
id: T084
title: Port LIR + x64 backend + encoder to Axiom (integration + differential)
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T083, T084a, T084b, T084c, T084d]
priority: 118
status: todo
attempts: 0
paths: [compiler/backend, tests/selfhost/backend]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-ABI-106, REQ-ABI-107, REQ-ABI-108, REQ-LAY-298, REQ-LIR-030, REQ-TGT-327, REQ-X64-001]
---
# T084 — Port LIR + x64 backend + encoder to Axiom (integration + differential)

## Goal
Integrate LIR, ABI lowering, x64 backend, and encoder in Axiom and run differential testing against `axiom0`.

## Scope
- Integrate `compiler/lir`, `compiler/abi`, and `compiler/target/x64`.
- Differential test harness comparing LIR dumps (`inspect --emit=lir`) and emitted machine code bytes with `axiom0`.
- Verification of calling conventions, stack frame layout, and instruction encoding across the entire tests corpus.

## Acceptance
- [ ] Differential equality over the corpus (documented counts); module tests pass in interp and native.
- [ ] Sub-tasks T084a through T084d integrated and passing differential checks.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T084-report.md` with exact `## Files changed`.

## Out of scope
- COFF and PE emission (handled in T085).

## Notes
- Group integration task for T084a–T084d per ADR-0005 §8 and SPEC-20 §4.8.
- Exact differential artefact: `inspect --emit=lir` and encoded machine code bytes.
- Harness entry: `tests/selfhost/backend`.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
