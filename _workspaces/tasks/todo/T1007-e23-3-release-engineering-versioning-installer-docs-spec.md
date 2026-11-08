---
id: T1007
title: E23.3 Canonical v1.0 release engineering, versioning policy, installer & docs site specification (SPEC-142)
phase: P23-v1-0-conformance-freeze-releas
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T223, T311, T312, T313, T314, T315, T316, T317, T318, T319, T320, T321, T322]
priority: 238
status: todo
attempts: 0
paths: [spec/SPEC-142-release-engineering-distribution-versioning.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [0150, tasks/0602, tasks/0603, tasks/0604, tasks/0605, tasks/0772, tasks/1034]
covers: [REQ-TOOL-001, REQ-CORE-3135, REQ-CORE-3136, REQ-CORE-3137, REQ-CORE-3138, REQ-PKG-022, REQ-TST-112, REQ-ECO-8736]
---
# T1007 — E23.3 Canonical v1.0 release engineering, versioning policy, installer & docs site specification (SPEC-142)

## Goal
Consolidate the canonical specification for Axiom v1.0 release engineering, release channels & qualification gates, multi-target binary archives, toolchain installer/version manager, documentation site generation, and semantic versioning/migration policy into `spec/SPEC-142-release-engineering-distribution-versioning.md` (`AXS-REL-*` rule IDs).

## Scope
- Write `spec/SPEC-142-release-engineering-distribution-versioning.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-REL-NNN` rules (`0150 §28-40, §46-47`, `tasks/0603 §1-72`, `tasks/0604 §1-76`, `tasks/0605`, `tasks/0772`, `tasks/1034`).
- Specify the release channels (`nightly`, `dev`, `beta`, `rc`, `stable`, `lts`; `REQ-CORE-3135`), mandatory Release Candidate / Stable qualification gates (`Language Conformance`, `Compiler Validation`, `Target Qualification`, `ABI/FFI`, `Security`, `Fuzz Regression`, `Performance`, `Binary Size`, `Reproducibility`, `Bootstrap`; `REQ-CORE-3136`, `AREL-01..30`), content-addressed `QualificationEvidenceGraph`, expirable `Waiver` records, and `AxiomReleaseCertificate` / `ReleaseManifest` schemas (`tasks/0603 §2-31, §45-70`).
- Specify the multi-dimension versioning policy (`Language Version`, `Compiler Version`, `Language Edition`, `Standard Library Version`, `ABI Version`, `Package Version`, `Target Version`; `REQ-CORE-3137`, `REQ-CORE-3138`, `REQ-PKG-022`), AST/HIR semantic migration (`axiomc migrate`), and compatibility verification (`axiomc compat source|semantic|abi|binary|package`; `AEVOL-01..30`, `tasks/0604 §18-25, §74-75`).
- Specify the self-contained multi-target v1.0 release bundles (C-free compiler binary, `std/`, `.axsdk` target sysroots, root `LICENSE` Apache-2.0 with Section 3 Patent Grant and `NOTICE` founding-author attribution for `Sơn Phạm <sp@outlook.com.vn>`, `.axcert`, provenance, Ed25519 signatures; `REQ-TOOL-001`, `REQ-ECO-8736`), cross-platform toolchain installer (`axiom-init` / `axiomc self`), and static documentation & specification site generator (`axiomc doc --site`; `REQ-TST-112`).
- Update `spec/INDEX.md`, `spec/diagnostics.md` (registering `AX_REL_*` and `AX_MIGRATE_*` diagnostic codes), and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-142-release-engineering-distribution-versioning.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-REL-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T1007-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of the release pipeline builder, signer, installer, and documentation site generator (`T1008`–`T1009`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P23 (`P23-v1-0-conformance-freeze-releas`), depends on `T223` and all P11–P22 phase gates (`T311`–`T322`).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T1007/build` and `python tools/axtest.py --compiler build-snap-T1007/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 11:15:00 created by T223 (P23 phase planning)
