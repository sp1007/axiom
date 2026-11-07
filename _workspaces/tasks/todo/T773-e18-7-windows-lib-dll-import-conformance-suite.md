---
id: T773
title: E18.7 — Windows x64 static .lib, PE DLL, import library & GNU ld cross-link conformance suite
phase: P18-compiler-architecture-2-0
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T751]
priority: 702
status: todo
attempts: 0
paths: [tests/conformance/p18/e18_7_windows_artifacts]
spec: [spec/SPEC-26-windows-artifact-kinds.md, spec/decisions/ADR-0034-oracle-independence-audit.md, 0164, 0185, 0186, 0187, 0217, tasks/0369, tasks/0563]
covers: [REQ-LNK-113, REQ-LNK-114, REQ-LNK-115, REQ-LNK-116, REQ-LNK-117, REQ-LNK-118, REQ-LNK-119, REQ-LNK-120, REQ-LNK-121]
started: 2026-11-07 06:05:53
---
# T773 — E18.7 — Windows x64 static .lib, PE DLL, import library & GNU ld cross-link conformance suite

## Goal
Certify E18.7 (`REQ-OWNER-006` and `ADR-0034` §4 OI-07b) with an end-to-end conformance suite covering `--kind exe|obj|lib|dll`, COFF `.lib` archives, PE32+ `.dll` + import `.lib` generation/consumption, DLL rebasing, and GNU `ld` cross-linking.

## Scope
- Create conformance tests in `tests/conformance/p18/e18_7_windows_artifacts` verifying:
  - producing and consuming Axiom static `.lib` and third-party C `.lib`/`.a` archives with dead-member stripping;
  - producing and consuming PE32+ `.dll` + short-import `.lib`, including `@export` functions/globals, `DllMain` module initialization failure returning `FALSE`, and forced non-preferred base relocation (`.reloc`);
  - `ADR-0034` §4 OI-07b GNU `ld` cross-link equivalence across `--emit=obj` outputs;
  - byte-identical `.lib`/`.dll`/`.exe` reproducibility across repeated builds (`0 WEAK-NATIVE`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p18/e18_7_windows_artifacts` pass in `--interp` (where applicable) and native modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T773-report.md` with exact `## Files changed`.

## Out of scope
- Non-Windows targets (`E16.10`); editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P18 (`P18-compiler-architecture-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T773/build` and `python tools/axtest.py --compiler build-snap-T773/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 03:00:20 created by T218 (P18 phase planning)
- 2026-11-07 06:05:53 started (attempt 1) T773-impl
- 2026-11-07 10:39:08 requeue: restart (not charged: attempt refunded)
