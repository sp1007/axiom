---
id: T1009
title: E23.3 Cross-platform toolchain installer, AST/HIR migration engine & v1.0 documentation site generator
phase: P23-v1-0-conformance-freeze-releas
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T223, T311, T312, T313, T314, T315, T316, T317, T318, T319, T320, T321, T322, T1004, T1007]
priority: 240
status: todo
attempts: 0
paths: [std/release/installer, compiler/evolution/migration, compiler/doc/site_gen, tools/release, tests/run/release_installer_docs]
locks: [compiler/driver/doc_cmd.ax, compiler/driver/cli.ax]
spec: [spec/SPEC-142-release-engineering-distribution-versioning.md, 0150, tasks/0603, tasks/0604, tasks/0605, tasks/1034]
covers: [REQ-CORE-3137, REQ-TST-112, REQ-ECO-8736]
---
# T1009 — E23.3 Cross-platform toolchain installer, AST/HIR migration engine & v1.0 documentation site generator

## Goal
Implement the cross-platform toolchain installer & version manager, AST/HIR edition migration & compatibility engine (`axiomc migrate` / `axiomc compat`), and canonical v1.0 static documentation site generator (`axiomc doc --site`) per `spec/SPEC-142-release-engineering-distribution-versioning.md`.

## Scope
- Implement the cross-platform toolchain installer and version manager in `std/release/installer` and `tools/release`: offline and repository-backed installation of release bundles, Ed25519 signature and `.axcert` verification before activation, side-by-side channel/version management (`stable`, `lts`, `1.0.0`), per-target `.axsdk` component installation, atomic rollback, and clean uninstallation (`REQ-ECO-8736`, `tasks/0603 §54`, `tasks/0605`, `tasks/1034`).
- Implement the controlled-evolution compatibility & AST/HIR migration engine in `compiler/evolution/migration`: `CompatibilityGraphDB`, `axiomc compat` (`source|semantic|abi|binary|package`), and `axiomc migrate` (`check|plan|verify`) operating on typed AST/HIR (never blind text replacement), classifying confidence (`Exact`, `ProvenEquivalent`, `LikelyEquivalent`, `ManualReview`, `Impossible`) and re-verifying migrated code through full type, ownership, and capability checking (`REQ-CORE-3137`, `AEVOL-10..27`, `tasks/0604 §18-25, §54-66, §73-74`).
- Implement the static v1.0 documentation and specification site generator in `compiler/doc/site_gen` (`axiomc doc --site`): rendering a self-contained, searchable HTML documentation site combining the canonical `spec/SPEC-*.md` language specification, `std/` API reference, `spec/diagnostics.md` error catalog, `spec/invariants.md`, and `spec/RELEASE-v1.md` (`REQ-TST-112`).
- Add end-to-end run tests in `tests/run/release_installer_docs`.

## Acceptance
- [ ] Run tests in `tests/run/release_installer_docs` verify offline toolchain install/switch/rollback/uninstall with signature verification, AST/HIR `axiomc migrate` with full re-verification, and `axiomc doc --site` generating the complete v1.0 documentation site with zero broken links.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T1009-report.md` with exact `## Files changed`.

## Out of scope
- Full E23.3 QA release-engineering conformance suite (`T1010`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P23 (`P23-v1-0-conformance-freeze-releas`), depends on `T223`, P11–P22 phase gates (`T311`–`T322`), `T1004`, and `T1007`.
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T1009/build` and `python tools/axtest.py --compiler build-snap-T1009/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 11:15:00 created by T223 (P23 phase planning)
