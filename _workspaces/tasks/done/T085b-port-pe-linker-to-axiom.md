---
id: T085b
title: Port PE32+ linker to Axiom
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T085a]
priority: 119
status: done
attempts: 1
paths: [compiler/link, tests/selfhost/link]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-CORE-3181]
started: 2026-10-18 14:53:19
finished: 2026-10-18 18:16:37
---
# T085b — Port PE32+ linker to Axiom

## Goal
Port in-memory PE32+ linker and executable builder (`compiler/link/`) from C to Axiom.

## Scope
- Port MS-DOS stub, PE signature, COFF file header, PE32+ optional header, and section headers.
- Port import address table (IAT) and import lookup table synthesis for kernel32.dll (ExitProcess, GetStdHandle, WriteFile, etc.).
- Port relative virtual address (RVA) calculations and relocation resolution.
- Unit tests under `tests/selfhost/link/`.

## Acceptance
- [ ] PE32+ linker implemented in `compiler/link/` — complete and readable: no line-packing or dropped features to meet a size target; ~1.5k lines per file is a split guide, not a limit (a larger module is split into several files under the task's paths, AXS-SELF-004).
- [ ] Unit tests pass in both interpreter and native modes.
- [ ] Linked PE32+ executable image runs correctly and outputs match `axiom0` builds.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T085b-report.md` with exact `## Files changed`.

## Out of scope
- Driver CLI flags (handled in T085c).

## Notes
- Sub-task of T085 split per ADR-0005 §8 and SPEC-20 §4.9.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-18 14:53:19 started (attempt 1) T085b-impl
- 2026-10-18 18:16:37 accepted by QA -> done
