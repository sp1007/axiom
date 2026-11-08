---
id: T815
title: E19.4 Diagnostics UX 2.0, explain codes, machine-applicable fixes & AI-agent fact interface conformance suite
phase: P19-developer-tooling
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T219, T752, T755, T756, T759, T814]
priority: 205
status: doing
attempts: 1
paths: [tests/conformance/p19/e19_4_diagnostics_ai]
spec: [spec/SPEC-103-diagnostics-ux-ai-interface.md, 0101, 0129, 0146, tasks/0360, tasks/0374, tasks/0421, tasks/0425, tasks/0444, tasks/0448, tasks/0456]
covers: [REQ-TOOL-004, REQ-TOOL-180, REQ-TOOL-181, REQ-TOOL-182, REQ-TOOL-185, REQ-TOOL-186, REQ-TOOL-187, REQ-TOOL-190, REQ-TOOL-298]
started: 2026-11-08 17:48:14
agent: T815-impl
---
# T815 — E19.4 Diagnostics UX 2.0, explain codes, machine-applicable fixes & AI-agent fact interface conformance suite

## Goal
Certify E19.4 exit criteria with an end-to-end conformance suite covering Diagnostics UX 2.0 causal provenance, cascading suppression, `axiomc explain`, `axiomc fix`, `axiomc inspect layout`, `.axmeta` container/`std` effect queries, and AI-agent verification.

## Scope
- Create conformance tests in `tests/conformance/p19/e19_4_diagnostics_ai` verifying:
  - causal provenance spans and zero cascading artificial errors on ownership/capability/type failures (`REQ-TOOL-298`);
  - `axiomc explain <CODE>` completeness and `axiomc fix` convergence to a clean compile (`REQ-TOOL-185`, `REQ-TOOL-186`);
  - `axiomc inspect layout` (`REQ-TOOL-004`), structured semantic fact graph export (`REQ-TOOL-180`), `.axmeta` container properties (`REQ-TOOL-181`), `std` effect metadata (`REQ-TOOL-190`), and strict separation of `.axmeta`/`.axdb`/debug artifacts from production binaries (`REQ-TOOL-182`, `REQ-TOOL-187`);
  - differential equivalence between `--interp` and native execution (`0 WEAK-NATIVE`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p19/e19_4_diagnostics_ai` pass in `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T815-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P19 (`P19-developer-tooling`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T815/build` and `python tools/axtest.py --compiler build-snap-T815/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 09:50:00 created by T219 (P19 phase planning)
- 2026-11-08 17:48:14 started (attempt 1) T815-impl
