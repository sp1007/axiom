---
id: T1008
title: E23.3 Multi-target v1.0 release binary builder, SBOM/provenance bundler & Ed25519 release signer
phase: P23-v1-0-conformance-freeze-releas
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T223, T311, T312, T313, T314, T315, T316, T317, T318, T319, T320, T321, T322, T1002, T1005, T1007]
priority: 239
status: todo
attempts: 0
paths: [compiler/release/builder, compiler/release/manifest, compiler/driver/release_cmd, tests/selfhost/release_builder]
locks: [compiler/driver/cli.ax]
spec: [spec/SPEC-142-release-engineering-distribution-versioning.md, 0150, tasks/0603, tasks/0604, tasks/0772]
covers: [REQ-TOOL-001, REQ-CORE-3135, REQ-CORE-3136, REQ-CORE-3138, REQ-PKG-022]
---
# T1008 — E23.3 Multi-target v1.0 release binary builder, SBOM/provenance bundler & Ed25519 release signer

## Goal
Implement `ReleaseDB`, `ReleaseManifestDB`, `EvidenceDB`, the multi-target v1.0 release archive builder, Ed25519 release signer/verifier, and `axiomc release` CLI commands per `spec/SPEC-142-release-engineering-distribution-versioning.md`.

## Scope
- Implement `ReleaseManifest`, `QualificationEvidenceGraph`, `AxiomReleaseCertificate`, and channel policy enforcement (`nightly`, `dev`, `beta`, `rc`, `stable`, `lts`; `REQ-CORE-3135`, `REQ-CORE-3136`) in `compiler/release/manifest`: enforcing `AREL-01..30` (every mandatory gate must pass for `rc`/`stable`, skipped mandatory gates invalidate qualification, independent performance/size metrics without synthetic aggregate scores, expirable `Waiver` records, and distinct `Language`/`Compiler`/`Edition`/`Std`/`ABI`/`Package`/`Target` version stamps; `REQ-CORE-3138`, `tasks/0603 §2-31, §42-48, §67-70`).
- Implement the reproducible multi-target v1.0 release bundle builder in `compiler/release/builder`: packaging C-free native compiler binaries (`axiomc`), `std/`, `.axsdk` sysroots, `.axif`/`.axmeta` interfaces, debug symbols, `.axcert` conformance certificates, `UnsafeSurfaceReport`, content-addressed build/test/fuzz/benchmark provenance, and Ed25519 signatures across the tier-1/tier-2 target matrix (`REQ-TOOL-001`, `REQ-PKG-022`, `tasks/0603 §2, §32-41`, `tasks/0772`).
- Implement `axiomc release` (`build|candidate|qualify|verify|inspect|diff|sign|publish|revoke|rollback`) and `axiomc evidence` (`inspect|verify|diff`) in `compiler/driver/release_cmd`, supporting `--json` machine-readable qualification reports (`tasks/0603 §47-55, §69`).
- Add selfhost tests in `tests/selfhost/release_builder`.

## Acceptance
- [ ] Selfhost tests in `tests/selfhost/release_builder` verify `ReleaseManifest` and `QualificationEvidenceGraph` construction, channel policy gates (`nightly` vs `rc`/`stable`), binary dependency and `UnsafeSurfaceReport` auditing, Ed25519 release signing/verification, and revocation/rollback handling.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T1008-report.md` with exact `## Files changed`.

## Out of scope
- Toolchain installer, AST/HIR migration engine, and static documentation site generator (`T1009`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P23 (`P23-v1-0-conformance-freeze-releas`), depends on `T223`, P11–P22 phase gates (`T311`–`T322`), `T1002`, `T1005`, and `T1007`.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T1008/build` and `python tools/axtest.py --compiler build-snap-T1008/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 11:15:00 created by T223 (P23 phase planning)
