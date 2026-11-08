---
id: T852
title: E20.1 CompilerDB build graph planner, host/target cross-build split, content-addressed cache & workspace CLI
phase: P20-build-system-package-ecosystem
owner: axiom-backend
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T220, T681, T685, T318, T850, T851]
priority: 202
status: done
attempts: 1
paths: [compiler/build/graph, compiler/build/cache, compiler/driver/workspace_cmd, tests/run/build_graph]
spec: [spec/SPEC-110-build-graph-driver.md, spec/SPEC-21-query-engine-semantic-db.md, spec/SPEC-22-incremental-compilation.md, 0168, tasks/0356, tasks/0372, tasks/0411, tasks/0661]
covers: [REQ-PKG-022, REQ-PKG-024, REQ-PKG-025]
started: 2026-11-08 19:10:03
finished: 2026-11-08 20:44:16
---
# T852 — E20.1 CompilerDB build graph planner, host/target cross-build split, content-addressed cache & workspace CLI

## Goal
Implement the `CompilerDB`-backed deterministic Build Graph planner, host-vs-target cross-compilation environment split, content-addressed artifact cache with poisoning defense, and `axiomc build|check|run|clean|graph` workspace orchestration CLI per `spec/SPEC-110-build-graph-driver.md`.

## Scope
- Implement `compiler/build/graph` lowering the resolved workspace package graph into a deterministic compilation-unit and artifact action DAG (`.axmeta`, `.obj`/`.o`, `.lib`/`.a`, `.dll`/`.so`/`.dylib`, `.exe`/ELF/Mach-O/`.wasm`), separating host compilation units (`build` and `comptime` dependencies) from target compilation units (`normal` and `dev` dependencies; `0168 §14-15`, `tasks/0356 §17-20`, `tasks/0411 §11-16, 24`).
- Implement `compiler/build/cache` computing composite cache keys from `SemanticFingerprint`, `AbiFingerprint`, `CodegenFingerprint`, and `BuildFingerprint` (`tasks/0411 §18-22`, `tasks/0661 §18-19`), verifying artifact integrity on cache hits, and atomically committing cache entries so cancelled builds never publish partial artifacts.
- Implement `compiler/driver/workspace_cmd` providing workspace-aware `axiomc build`, `axiomc check`, `axiomc run`, `axiomc clean`, and `axiomc graph --format=json|dot` commands (`REQ-PKG-022`, `REQ-PKG-024`, `REQ-PKG-025`).
- Add run tests in `tests/run/build_graph`.

## Acceptance
- [ ] Run tests in `tests/run/build_graph` verify deterministic build plan construction, host-vs-target environment separation, `.axmeta` interface-vs-implementation incremental rebuild reuse, cache-poisoning rejection, and `axiomc graph` output across `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T852-report.md` with exact `## Files changed`.

## Out of scope
- External package version constraint solving and `axiom.lock` generation (`T854`–`T857`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P20 (`P20-build-system-package-ecosystem`), depends on P16 gate `T316` and P18 gate `T318` (`ROADMAP.md` §2–§3).
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T852/build` and `python tools/axtest.py --compiler build-snap-T852/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:12:00 created by T220 (P20 phase planning)
- 2026-11-08 19:10:03 started (attempt 1) T852-impl
- 2026-11-08 20:44:16 accepted by QA -> done
