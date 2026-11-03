---
id: T1002
title: E23.1 Compiler qualification runner, optimization/cache/bootstrap differential & .axcert CLI
phase: P23-v1-0-conformance-freeze-releas
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T223, T311, T312, T313, T314, T315, T316, T317, T318, T319, T320, T321, T322, T1001]
priority: 232
status: todo
attempts: 0
paths: [compiler/conformance/qualification, compiler/conformance/certificate, compiler/driver/conformance_cmd, tests/selfhost/qualification_cert]
locks: [compiler/driver/cli.ax]
spec: [spec/SPEC-140-conformance-suite-compiler-qualification.md, 0150, tasks/0602, tasks/0603]
covers: [REQ-CORE-3133, REQ-CORE-3136, REQ-TST-112]
---
# T1002 — E23.1 Compiler qualification runner, optimization/cache/bootstrap differential & .axcert CLI

## Goal
Implement `QualificationDB`, `CertificateDB`, `BootstrapDB`, the multi-profile differential qualification runner (`Q0`–`Q4`), `.axcert` certificate generation/verification, and the `axiomc conformance`, `axiomc qualify`, and `axiomc cert` CLI commands per `spec/SPEC-140-conformance-suite-compiler-qualification.md`.

## Scope
- Implement the Compiler Qualification Matrix runner (`Q0 Experimental` .. `Q4 Self-Hosting Qualified`) in `compiler/conformance/qualification`: validating observable semantic equivalence across optimization levels (`-O0`, `-O1`, `-O2`, `-O3`, `-Os`, `-Oz`), LTO modes (`NoLTO`, `ThinLTO`, `FullLTO`), build modes (`CleanBuild`, `IncrementalBuild`), cache states (`ColdCache`, `WarmCache`), target ABI/object/linker conformance, and three-stage self-hosting bootstrap convergence (`stage1` → `stage2` → `stage3` + Reference Interpreter differential; `ACONF-06..22`, `REQ-CORE-3136`, `0150 §11, §20-24`, `tasks/0602 §33-50`).
- Implement `.axcert` qualification certificate generation, inspection, and fingerprint verification in `compiler/conformance/certificate`: recording compiler version, language edition, spec revision, target matrix, `ConformanceSuiteFingerprint`, test outcomes, fuzz corpus fingerprint, and toolchain fingerprint (`ACONF-19..21`, `tasks/0602 §51-54`).
- Implement `axiomc conformance` (`run|list|explain|coverage|diff|target|diagnostics|semantic`), `axiomc qualify` (`target|release|bootstrap`), and `axiomc cert` (`generate|inspect|verify`) in `compiler/driver/conformance_cmd`, including AI-readable failure/rule provenance reports (`REQ-TST-112`, `tasks/0602 §58-60`).
- Add selfhost tests in `tests/selfhost/qualification_cert`.

## Acceptance
- [ ] Selfhost tests in `tests/selfhost/qualification_cert` verify cross-optimization (`-O0`..`-Oz`), LTO, incremental/cache, and 3-stage bootstrap qualification (`Q0`–`Q4`), `.axcert` generation/verification, and `axiomc conformance explain` rule traceability.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T1002-report.md` with exact `## Files changed`.

## Out of scope
- Full E23.1 QA conformance suite certification (`T1003`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P23 (`P23-v1-0-conformance-freeze-releas`), depends on `T223`, P11–P22 phase gates (`T311`–`T322`), and `T1001`.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T1002/build` and `python tools/axtest.py --compiler build-snap-T1002/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 11:15:00 created by T223 (P23 phase planning)
