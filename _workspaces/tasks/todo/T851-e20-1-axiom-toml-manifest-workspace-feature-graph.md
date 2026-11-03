---
id: T851
title: E20.1 Declarative axiom.toml package/workspace manifest parser, feature/@cfg evaluator & acyclic package graph
phase: P20-build-system-package-ecosystem
owner: axiom-frontend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T220, T316, T318, T850]
priority: 201
status: todo
attempts: 0
paths: [compiler/build/manifest, compiler/build/workspace, tests/run/build_manifest]
spec: [spec/SPEC-110-build-graph-driver.md, 0168, tasks/0356, tasks/0372, tasks/0661]
covers: [REQ-PKG-022, REQ-PKG-024, REQ-PKG-025]
---
# T851 — E20.1 Declarative axiom.toml package/workspace manifest parser, feature/@cfg evaluator & acyclic package graph

## Goal
Implement the declarative `axiom.toml` package and workspace manifest parser, deterministic `@cfg` and feature flag evaluator, and acyclic package-level dependency graph builder per `spec/SPEC-110-build-graph-driver.md`.

## Scope
- Implement `compiler/build/manifest` parsing `[package]`, `[workspace]`, `[[bin]]`, `[lib]`, `[dependencies]`, `[dev-dependencies]`, `[build-dependencies]`, `[features]`, `[profile.dev]`, `[profile.release]`, and target-conditional `[target.'cfg(...)'.dependencies]` tables without arbitrary imperative script execution (`0168 §3, 9`, `tasks/0372 §3-12`).
- Implement `compiler/build/workspace` discovering multi-package workspace members, constructing the canonical package-level DAG, rejecting package-level dependency cycles with causal cycle diagnostics while permitting intra-package module cycles governed by module semantics (`tasks/0356 §13`, `tasks/0372 §7`, `tasks/0411 §13`).
- Implement deterministic feature and `@cfg` predicate evaluation enforcing `REQ-PKG-025` (unknown or disabled required features fail explicitly; metadata and build features never implicitly alter language syntax or core type semantics).
- Add run and negative diagnostic tests in `tests/run/build_manifest`.

## Acceptance
- [ ] Run tests in `tests/run/build_manifest` verify multi-package `axiom.toml` parsing, workspace member discovery, package cycle rejection, target `@cfg` filtering, and `REQ-PKG-025` feature/semantic invariants in both `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T851-report.md` with exact `## Files changed`.

## Out of scope
- `CompilerDB` build action scheduling, artifact caching, and workspace CLI subcommands (`T852`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P20 (`P20-build-system-package-ecosystem`), depends on P16 gate `T316` and P18 gate `T318` (`ROADMAP.md` §2–§3).
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T851/build` and `python tools/axtest.py --compiler build-snap-T851/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:12:00 created by T220 (P20 phase planning)
