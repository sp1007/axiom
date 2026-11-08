---
id: T853
title: E20.1 Build graph, workspace orchestration, feature/profile determinism & driver CLI conformance suite
phase: P20-build-system-package-ecosystem
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T220, T681, T685, T318, T852]
priority: 203
status: done
attempts: 1
paths: [tests/conformance/p20/e20_1_build_graph_driver]
spec: [spec/SPEC-110-build-graph-driver.md, 0168, tasks/0356, tasks/0372, tasks/0411, tasks/0661]
covers: [REQ-PKG-022, REQ-PKG-024, REQ-PKG-025]
started: 2026-11-08 20:44:51
finished: 2026-11-08 21:26:42
---
# T853 — E20.1 Build graph, workspace orchestration, feature/profile determinism & driver CLI conformance suite

## Goal
Certify E20.1 exit criteria with an end-to-end conformance suite covering multi-package workspace manifests, deterministic build graphs, host/target cross-compilation separation, incremental artifact caching, and driver CLI commands.

## Scope
- Create conformance tests in `tests/conformance/p20/e20_1_build_graph_driver` verifying:
  - multi-package workspace DAG construction, worker-count invariance (1 vs 4 workers produce identical build graphs and artifacts), and filesystem enumeration order independence (`0168 §16-17`, `tasks/0411 §47`);
  - package-level cycle rejection vs legal intra-package module recursion (`tasks/0356 §13`, `tasks/0372 §7`);
  - feature flag and `@cfg` determinism without silent feature disabling or core semantic mutation (`REQ-PKG-025`);
  - host vs target compilation split and content-addressed cache invalidation/poisoning guards (`REQ-PKG-022`, `REQ-PKG-024`);
  - differential equivalence between `--interp` and native execution (`0 WEAK-NATIVE`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p20/e20_1_build_graph_driver` pass in `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T853-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P20 (`P20-build-system-package-ecosystem`), depends on P16 gate `T316` and P18 gate `T318` (`ROADMAP.md` §2–§3).
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T853/build` and `python tools/axtest.py --compiler build-snap-T853/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:12:00 created by T220 (P20 phase planning)
- 2026-11-08 20:44:51 started (attempt 1) T853-impl
- 2026-11-08 21:26:42 accepted by QA -> done
