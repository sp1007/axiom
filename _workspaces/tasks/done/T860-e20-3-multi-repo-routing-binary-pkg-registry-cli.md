---
id: T860
title: E20.3 Multi-repository priority/trust routing, precompiled .axmeta/binary package consumption & axiomc pkg publish/fetch/mirror CLI
phase: P20-build-system-package-ecosystem
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T220, T681, T685, T318, T858, T859]
priority: 210
status: done
attempts: 1
paths: [compiler/pkg/distribution, compiler/driver/registry_cmd, tests/run/pkg_distribution]
spec: [spec/SPEC-112-package-registry-distribution.md, spec/SPEC-24-artifact-format-module-interfaces.md, tasks/0665, tasks/0739, tasks/0858, tasks/1065]
covers: [REQ-ECO-8736, REQ-PKG-024]
started: 2026-11-09 02:29:55
finished: 2026-11-09 03:28:49
---
# T860 — E20.3 Multi-repository priority/trust routing, precompiled .axmeta/binary package consumption & axiomc pkg publish/fetch/mirror CLI

## Goal
Implement multi-repository priority/trust routing, precompiled `.axmeta` interface + binary archive consumption, and `axiomc pkg publish|fetch|verify|search|mirror` CLI commands per `spec/SPEC-112-package-registry-distribution.md`.

## Scope
- Implement `compiler/pkg/distribution` supporting both source packages and precompiled `.axmeta` + static/dynamic binary packages (`tasks/0665 §8`, `tasks/0739 §493.1-24`), verifying target coordinate, `AbiFingerprint`, `SemanticFingerprint`, and compiler compatibility before linking without re-parsing source.
- Implement multi-repository priority and namespace pinning (`tasks/0858 §11-14`) so lower-priority or untrusted mirrors cannot shadow pinned namespaces (dependency-confusion defense).
- Implement `compiler/driver/registry_cmd` providing `axiomc pkg publish`, `fetch`, `verify`, `search`, and `mirror` CLI commands (`REQ-ECO-8736`, `REQ-PKG-024`).
- Add run tests in `tests/run/pkg_distribution`.

## Acceptance
- [ ] Run tests in `tests/run/pkg_distribution` verify `axiomc pkg publish|fetch|mirror|verify`, precompiled `.axmeta` + binary package consumption, target/ABI mismatch rejection, and namespace-pinning dependency-confusion defense in `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T860-report.md` with exact `## Files changed`.

## Out of scope
- Ed25519 cryptographic signing and hermetic build sandboxing (`T862`–`T865`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P20 (`P20-build-system-package-ecosystem`), depends on P16 gate `T316` and P18 gate `T318` (`ROADMAP.md` §2–§3).
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T860/build` and `python tools/axtest.py --compiler build-snap-T860/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:12:00 created by T220 (P20 phase planning)
- 2026-11-09 02:29:55 started (attempt 1) T860-impl
- 2026-11-09 03:28:49 accepted by QA -> done
