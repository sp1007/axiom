---
id: T085a
title: Port COFF object writer & object model to Axiom
phase: P10-selfhost
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T077]
priority: 119
status: done
attempts: 1
paths: [compiler/obj, tests/selfhost/obj]
spec: [0167, tasks/0261, spec/SPEC-20-selfhost.md, 0152]
covers: [REQ-CORE-3181]
started: 2026-10-18 12:55:19
finished: 2026-10-18 14:52:55
---
# T085a — Port COFF object writer & object model to Axiom

## Goal
Port COFF object file model and binary writer (`compiler/obj/`) from C to Axiom.

## Scope
- Port COFF header formatting, section headers (.text, .rdata, .data), symbol table entries, string table, and relocation entries.
- Port deterministic member and section layout.
- Unit tests under `tests/selfhost/obj/`.

## Acceptance
- [ ] COFF object writer implemented in `compiler/obj/` — complete and readable: no line-packing or dropped features to meet a size target; ~1.5k lines per file is a split guide, not a limit (a larger module is split into several files under the task's paths, AXS-SELF-004).
- [ ] Unit tests pass in both interpreter and native modes.
- [ ] Emitted `.obj` file matches `axiom0 build --emit=obj` byte-for-byte on test programs.
- [ ] Full test suite passes; build warning-free; archcheck clean.
- [ ] Report `_workspaces/reports/T085a-report.md` with exact `## Files changed`.

## Out of scope
- PE executable linking (handled in T085b).

## Notes
- Sub-task of T085 split per ADR-0005 §8 and SPEC-20 §4.9.
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-18 12:55:19 started (attempt 1) T085a-impl
- 2026-10-18 14:52:55 accepted by QA -> done
