---
id: T1003
title: E23.1 Full language conformance suite, compiler qualification & .axcert conformance
phase: P23-v1-0-conformance-freeze-releas
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T223, T311, T312, T313, T314, T315, T316, T317, T318, T319, T320, T321, T322, T1002]
priority: 233
status: todo
attempts: 0
paths: [tests/conformance/p23/e23_1_conformance_qualification]
spec: [spec/SPEC-140-conformance-suite-compiler-qualification.md, 0017, 0145, 0150, tasks/0602, tasks/0603]
covers: [REQ-CORE-3133, REQ-CORE-3134, REQ-CORE-3136, REQ-TST-112]
---
# T1003 — E23.1 Full language conformance suite, compiler qualification & .axcert conformance

## Goal
Certify E23.1 exit criteria with a comprehensive conformance suite covering all `AXS-CNF-*` rules of `spec/SPEC-140-conformance-suite-compiler-qualification.md`, six-state outcome classification, multi-layer semantic trace verification, differential qualification (`Q0`–`Q4`), and `.axcert` certificate generation/verification.

## Scope
- Create `tests/conformance/p23/e23_1_conformance_qualification` covering all 24 language, compiler, and target conformance categories (`Syntax`, `NameResolution`, `Types`, `Generics`, `Traits`, `Inference`, `Values`, `Copy`, `Move`, `Drop`, `Ownership`, `Capability`, `Views`, `PatternMatching`, `ControlFlow`, `Errors`, `Comptime`, `Concurrency`, `Async`, `GPU`, `FFI`, `ABI`, `Modules`, `Visibility`; `0017`, `0150 §5, §46`, `tasks/0602 §10`).
- Verify six-state outcome classification (`PASS`, `FAIL`, `UNSUPPORTED`, `IMPLEMENTATION_DEFINED`, `TARGET_DEFINED`, `CONDITIONAL`; `REQ-CORE-3133`) and multi-layer semantic trace checking (`REQ-CORE-3134`).
- Verify observable semantic equivalence across `-O0`..`-Oz`, `NoLTO`/`ThinLTO`/`FullLTO`, `CleanBuild`/`IncrementalBuild`, `ColdCache`/`WarmCache`, three-stage self-hosting bootstrap convergence (`Q4 Self-Hosting Qualified`; `REQ-CORE-3136`), and `.axcert` certificate round-trip verification (`ACONF-01..25`, `REQ-TST-112`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p23/e23_1_conformance_qualification` pass with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T1003-report.md` with exact `## Files changed`.

## Out of scope
- Compiler or stdlib changes; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P23 (`P23-v1-0-conformance-freeze-releas`), depends on `T223`, P11–P22 phase gates (`T311`–`T322`), and `T1002`.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T1003/build` and `python tools/axtest.py --compiler build-snap-T1003/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 11:15:00 created by T223 (P23 phase planning)
