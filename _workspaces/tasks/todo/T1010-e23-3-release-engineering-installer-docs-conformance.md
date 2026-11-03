---
id: T1010
title: E23.3 Release archives, installer verification, documentation site & v1.0 release readiness conformance suite
phase: P23-v1-0-conformance-freeze-releas
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T223, T311, T312, T313, T314, T315, T316, T317, T318, T319, T320, T321, T322, T1008, T1009]
priority: 241
status: todo
attempts: 0
paths: [tests/conformance/p23/e23_3_release_engineering]
spec: [spec/SPEC-142-release-engineering-distribution-versioning.md, 0150, tasks/0602, tasks/0603, tasks/0604, tasks/0605, tasks/0772, tasks/1034]
covers: [REQ-TOOL-001, REQ-CORE-3135, REQ-CORE-3136, REQ-CORE-3137, REQ-CORE-3138, REQ-PKG-022, REQ-TST-112, REQ-ECO-8736]
---
# T1010 — E23.3 Release archives, installer verification, documentation site & v1.0 release readiness conformance suite

## Goal
Certify E23.3 exit criteria with an end-to-end conformance suite covering reproducible v1.0 release archives, `ReleaseManifest` & `QualificationEvidenceGraph` verification, Ed25519 signature & revocation checks, toolchain installer lifecycle, AST/HIR migration & version separation (`AREL-01..30`, `AEVOL-01..30`), and canonical v1.0 documentation site generation.

## Scope
- Create `tests/conformance/p23/e23_3_release_engineering` covering all `AXS-REL-*` rules of `spec/SPEC-142-release-engineering-distribution-versioning.md`.
- Verify reproducible `axiomc release build|qualify|verify|sign|revoke|rollback` across release channels (`nightly`, `beta`, `rc`, `stable`, `lts`), confirming that skipped or failed mandatory gates reject `rc`/`stable` qualification (`AREL-02..03`, `REQ-CORE-3135`, `REQ-CORE-3136`, `REQ-PKG-022`, `REQ-TOOL-001`).
- Verify distinct version tracking (`Language Version`, `Compiler Version`, `Language Edition`, `Standard Library Version`, `ABI Version`, `Package Version`, `Target Version`), AST/HIR semantic migration (`axiomc migrate`), clean-room toolchain installer lifecycle (`install`, `switch`, `rollback`, `uninstall`), and `axiomc doc --site` documentation completeness (`REQ-CORE-3137`, `REQ-CORE-3138`, `REQ-TST-112`, `REQ-ECO-8736`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p23/e23_3_release_engineering` pass with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T1010-report.md` with exact `## Files changed`.

## Out of scope
- Compiler or stdlib changes; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P23 (`P23-v1-0-conformance-freeze-releas`), depends on `T223`, P11–P22 phase gates (`T311`–`T322`), `T1008`, and `T1009`.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T1010/build` and `python tools/axtest.py --compiler build-snap-T1010/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 11:15:00 created by T223 (P23 phase planning)
