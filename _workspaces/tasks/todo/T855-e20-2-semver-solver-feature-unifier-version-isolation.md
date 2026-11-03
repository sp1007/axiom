---
id: T855
title: E20.2 Deterministic SemVer 2.0 constraint solver, monotonic feature unifier & side-by-side package version isolation
phase: P20-build-system-package-ecosystem
owner: axiom-semantics
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T220, T316, T318, T851, T854]
priority: 205
status: todo
attempts: 0
paths: [compiler/pkg/semver, compiler/pkg/resolver, tests/run/pkg_resolver]
spec: [spec/SPEC-111-package-manager-resolution-lockfiles.md, 0098, tasks/0412, tasks/0446, tasks/0661, tasks/1065]
covers: [REQ-ECO-8736, REQ-PKG-022, REQ-PKG-024, REQ-PKG-025]
---
# T855 — E20.2 Deterministic SemVer 2.0 constraint solver, monotonic feature unifier & side-by-side package version isolation

## Goal
Implement the SemVer 2.0 version parser/comparator, PubGrub-style deterministic dependency constraint solver, monotonic feature unifier, and side-by-side package version isolation per `spec/SPEC-111-package-manager-resolution-lockfiles.md`.

## Scope
- Implement `compiler/pkg/semver` parsing and ordering SemVer 2.0 versions (`major.minor.patch`, pre-release identifiers, build metadata) and evaluating version constraints (`=`, `^`, `~`, `<`, `<=`, `>`, `>=`, compound ranges; `tasks/1065 §7-17`).
- Implement `compiler/pkg/resolver` performing deterministic, declaration-order-independent constraint resolution with human-readable conflict derivation trees, separating host (`build`/`comptime`) vs target (`normal`/`dev`) feature unification, and rejecting any graph state that silently drops a required feature or mutates language semantics (`REQ-PKG-022`, `REQ-PKG-024`, `REQ-PKG-025`, `REQ-ECO-8736`).
- Implement side-by-side incompatible major-version isolation in package symbol mangling and `CompilerDB` package IDs so two incompatible major versions coexist safely with distinct nominal types unless explicitly bridged (`0098 §10-12`, `tasks/0661 §10`).
- Add run and diagnostic tests in `tests/run/pkg_resolver`.

## Acceptance
- [ ] Run tests in `tests/run/pkg_resolver` verify SemVer 2.0 ordering, deterministic resolution independent of manifest key/filesystem order, conflict derivation diagnostics, monotonic feature unification (`REQ-PKG-025`), and side-by-side major-version isolation in `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T855-report.md` with exact `## Files changed`.

## Out of scope
- `axiom.lock` disk persistence, content-addressed cache directory, and `axiomc pkg` CLI commands (`T856`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P20 (`P20-build-system-package-ecosystem`), depends on P16 gate `T316` and P18 gate `T318` (`ROADMAP.md` §2–§3).
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T855/build` and `python tools/axtest.py --compiler build-snap-T855/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:12:00 created by T220 (P20 phase planning)
