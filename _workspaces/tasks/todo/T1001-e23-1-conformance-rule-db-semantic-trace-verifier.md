---
id: T1001
title: E23.1 Conformance rule database, semantic trace comparator & multi-stage verification engine
phase: P23-v1-0-conformance-freeze-releas
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T223, T311, T312, T313, T314, T315, T316, T317, T318, T319, T320, T321, T322, T1000]
priority: 231
status: todo
attempts: 0
paths: [compiler/conformance/rules, compiler/conformance/semantic_trace, compiler/conformance/oracle, tests/selfhost/conformance_engine]
locks: [compiler/interp/interp.ax, compiler/mir/verifier.ax]
spec: [spec/SPEC-140-conformance-suite-compiler-qualification.md, 0017, 0145, 0150, tasks/0602]
covers: [REQ-CORE-3133, REQ-CORE-3134]
---
# T1001 — E23.1 Conformance rule database, semantic trace comparator & multi-stage verification engine

## Goal
Implement `ConformanceDB`, `SpecRuleDB`, `ConformanceTestDB`, `SemanticTraceDB`, and the multi-layer semantic conformance comparator in `compiler/conformance/` per `spec/SPEC-140-conformance-suite-compiler-qualification.md`.

## Scope
- Implement `SpecRuleDB` and `ConformanceTestDB` in `compiler/conformance/rules`: indexing machine-readable `AXS-*` specification rules, test metadata (`id`, `category`, `expected`, `targets`, `diagnostics`, `semantic_properties`), and the six-state outcome classifier (`PASS`, `FAIL`, `UNSUPPORTED`, `IMPLEMENTATION_DEFINED`, `TARGET_DEFINED`, `CONDITIONAL`; `REQ-CORE-3133`, `tasks/0602 §1, §9, §57`).
- Implement `SemanticTraceDB` and the multi-layer semantic property verifier in `compiler/conformance/semantic_trace`: inspecting and comparing variable usability (`Owned`, `Moved`, `PartiallyMoved`, `Dropped`, `Uninit`), assignment types, `Copy`/`Move` transitions, capability lifetimes (`View`, `MutView`), `Verified MIR` structural invariants (`NoUseAfterMove`, `NoInvalidCapability`, `NoDataRace`, `NoInvalidDrop`), and runtime `SemanticTrace` events (`Value`, `Move`, `Copy`, `Drop`, `Panic`, `Return`, `Capability`, `Task`, `Synchronization`; `REQ-CORE-3134`, `0017 §1-6`, `tasks/0602 §2, §6-8, §17-22`).
- Implement the differential Oracle & diagnostic conformance comparator in `compiler/conformance/oracle`: comparing reference interpreter execution against native execution (`UNDEFINED_UNSAFE` classification for unsafe contract violations; `0145`, `0150 §12`), comparing `DiagnosticCode`, `Severity`, `PrimarySpan`, `RelevantSpan`, and `SemanticCause` without prose fragility (`ACONF-04`, `tasks/0602 §12-13`), and raising `SpecificationAmbiguity` when reference and compiler disagree on an underspecified rule (`ACONF-23..24`, `tasks/0602 §64`).
- Add selfhost unit and run tests in `tests/selfhost/conformance_engine`.

## Acceptance
- [ ] Selfhost tests in `tests/selfhost/conformance_engine` verify six-state test classification (`PASS`, `FAIL`, `UNSUPPORTED`, `IMPLEMENTATION_DEFINED`, `TARGET_DEFINED`, `CONDITIONAL`), multi-layer semantic trace comparison (`Move`/`Copy`/`Drop`/usability/MIR properties), semantic diagnostic comparison, and `SpecificationAmbiguity` detection.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T1001-report.md` with exact `## Files changed`.

## Out of scope
- Qualification matrix runner, `.axcert` certificate generation, and `axiomc conformance|qualify|cert` CLI (`T1002`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P23 (`P23-v1-0-conformance-freeze-releas`), depends on `T223`, P11–P22 phase gates (`T311`–`T322`), and `T1000`.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T1001/build` and `python tools/axtest.py --compiler build-snap-T1001/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 11:15:00 created by T223 (P23 phase planning)
