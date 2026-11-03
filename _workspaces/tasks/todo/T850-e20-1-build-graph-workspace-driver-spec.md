---
id: T850
title: E20.1 Canonical build graph, declarative axiom.toml workspace & driver orchestration specification (SPEC-110)
phase: P20-build-system-package-ecosystem
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T220, T316, T318]
priority: 200
status: todo
attempts: 0
paths: [spec/SPEC-110-build-graph-driver.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-21-query-engine-semantic-db.md, spec/SPEC-22-incremental-compilation.md, spec/SPEC-88-cross-compilation-platform-layer.md, 0168, tasks/0356, tasks/0372, tasks/0411, tasks/0661]
covers: [REQ-PKG-022, REQ-PKG-024, REQ-PKG-025]
---
# T850 — E20.1 Canonical build graph, declarative axiom.toml workspace & driver orchestration specification (SPEC-110)

## Goal
Consolidate the canonical specification for Axiom's declarative `axiom.toml` package and workspace manifests, acyclic package/build/link graph architecture, host-vs-target cross-build split, content-addressed cache keys, and `CompilerDB`-backed workspace driver CLI into `spec/SPEC-110-build-graph-driver.md` (`AXS-BLD-*` rule IDs).

## Scope
- Write `spec/SPEC-110-build-graph-driver.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-BLD-NNN` rules.
- Specify the five distinct structural layers (`0168 §2-8`, `tasks/0356 §1-13`, `tasks/0372 §1-8`, `tasks/0661 §1-18`): `Module` (namespace and semantic compilation unit), `Package` (distribution, version, and dependency unit), `Workspace` (multi-package coordination root), `DependencyGraph` (acyclic package-level dependency DAG across `normal`, `dev`, `build`, and `comptime` scopes), and `BuildGraph` (typed compilation-unit and artifact action DAG integrated with `CompilerDB` queries; `REQ-PKG-022`, `REQ-PKG-024`).
- Specify declarative `axiom.toml` workspace and package manifests (`0168 §3, 9-13`, `tasks/0356 §14-16`, `tasks/0372 §10-13`), deterministic `@cfg` and feature flag evaluation, and `dev`/`release` optimization profiles, enforcing `REQ-PKG-025` (package metadata and build features never implicitly alter core language semantics or silently disable required features).
- Specify the strict host-vs-target environment split for cross-compilation and comptime/build tools (`0168 §14-15`, `tasks/0356 §17-20`, `tasks/0411 §24`), multi-tier content-addressed build cache keys (`SemanticFingerprint`, `AbiFingerprint`, `CodegenFingerprint`, `BuildFingerprint`) with cache-poisoning defense (`0168 §16-17`, `tasks/0411 §20-22`), and the `axiomc build|check|run|test|bench|clean|graph` workspace CLI contract (`tasks/0411 §2-16`).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-110-build-graph-driver.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-BLD-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T850-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of the manifest parser, build graph planner, and workspace CLI (`T851`–`T852`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P20 (`P20-build-system-package-ecosystem`), depends on P16 gate `T316` and P18 gate `T318` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:12:00 created by T220 (P20 phase planning)
