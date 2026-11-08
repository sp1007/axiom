---
id: T813
title: E19.4 Diagnostics UX 2.0: causal provenance spans, cascading suppression, fix-it applicator & axiomc explain
phase: P19-developer-tooling
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T219, T752, T755, T756, T759, T812]
priority: 203
status: todo
attempts: 0
paths: [compiler/diag/ux2, compiler/diag/explain, compiler/driver/explain_cmd, tests/run/diag_ux2]
spec: [spec/SPEC-103-diagnostics-ux-ai-interface.md, spec/diagnostics.md, 0101, 0146, tasks/0360, tasks/0374, tasks/0421, tasks/0693]
covers: [REQ-TOOL-185, REQ-TOOL-186, REQ-TOOL-298]
---
# T813 — E19.4 Diagnostics UX 2.0: causal provenance spans, cascading suppression, fix-it applicator & axiomc explain

## Goal
Implement Diagnostics UX 2.0 causal provenance rendering, root-cause cascading suppression, the transactional `axiomc fix` machine-applicable fix-it applicator, and `axiomc explain <CODE>` per `spec/SPEC-103-diagnostics-ux-ai-interface.md`.

## Scope
- Implement `compiler/diag/ux2`: multi-span Unicode-aware terminal and JSON rendering with causal provenance chains (`created here` → `moved/borrowed here` → `used here`), deterministic diagnostic fingerprints (`0146 §40`), and `CompilerDB` poison-taint suppression so a single root error does not emit cascading artificial diagnostics (`REQ-TOOL-298`).
- Implement confidence-tagged fix-it emission (`MachineApplicable`, `HasPlaceholders`, `MaybeIncorrect`) and the transactional `axiomc fix` applicator that applies `MachineApplicable` edits and re-verifies the modified source through `CompilerDB` (`0146 §11-12, §41-44`, `REQ-TOOL-185`, `REQ-TOOL-186`).
- Implement the `axiomc explain <CODE>` registry and CLI command in `compiler/diag/explain` and `compiler/driver/explain_cmd` covering all 18 diagnostic areas with spec rule citations and minimal canonical Axiom examples (`0101 §24`, `0146 §15-18`, `tasks/0360`).

## Acceptance
- [ ] Run tests in `tests/run/diag_ux2` verify causal multi-span ownership/capability diagnostics, cascading error suppression, `axiomc fix` transactional fix application and re-verification, and `axiomc explain` output for every diagnostic area.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T813-report.md` with exact `## Files changed`.

## Out of scope
- AI semantic fact graph exporter and layout/container/std effect metadata inspector (`T814`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P19 (`P19-developer-tooling`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T813/build` and `python tools/axtest.py --compiler build-snap-T813/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 09:50:00 created by T219 (P19 phase planning)
