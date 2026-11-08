---
id: T856
title: E20.2 Canonical axiom.lock serializer/verifier, content-addressed package store, offline vendoring & axiomc pkg CLI
phase: P20-build-system-package-ecosystem
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T220, T681, T685, T318, T854, T855]
priority: 206
status: doing
attempts: 1
paths: [std/pkg/lockfile, std/pkg/store, compiler/driver/pkg_cmd, tests/run/pkg_lockfile]
spec: [spec/SPEC-111-package-manager-resolution-lockfiles.md, 0098, tasks/0412, tasks/0446, tasks/0661, tasks/1065]
covers: [REQ-ECO-8736, REQ-PKG-022, REQ-PKG-024, REQ-PKG-025]
started: 2026-11-08 23:43:33
agent: T856-impl
---
# T856 — E20.2 Canonical axiom.lock serializer/verifier, content-addressed package store, offline vendoring & axiomc pkg CLI

## Goal
Implement the canonical `axiom.lock` v1 parser/serializer, SHA-256 content-addressed local package store, offline `vendor/` directory support, and `axiomc pkg` management CLI per `spec/SPEC-111-package-manager-resolution-lockfiles.md`.

## Scope
- Implement `std/pkg/lockfile` reading and writing canonical `axiom.lock` v1 files with deterministic lexicographic entry ordering, exact resolved versions, source coordinates, SHA-256 content hashes, unified features, and `--locked` drift detection (`0098 §5-6`, `tasks/0446 §187.5-6`, `tasks/1065 §24-35`).
- Implement `std/pkg/store` managing the content-addressed package cache (keyed by SHA-256 digest, never trusting filenames alone per `tasks/0412 §9-10`) and air-gapped `--offline` / `vendor/` directory materialization (`tasks/0446 §187.160`).
- Implement `compiler/driver/pkg_cmd` supporting `axiomc pkg init`, `add`, `remove`, `update`, `lock`, `tree`, `verify-lock`, and `vendor` (`REQ-PKG-022`, `REQ-PKG-024`, `REQ-PKG-025`, `REQ-ECO-8736`).
- Add run tests in `tests/run/pkg_lockfile`.

## Acceptance
- [ ] Run tests in `tests/run/pkg_lockfile` verify `axiom.lock` round-trip canonical serialization, `--locked` drift rejection, SHA-256 hash mismatch rejection, offline `vendor/` builds, and `axiomc pkg tree|lock|vendor` CLI execution in `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T856-report.md` with exact `## Files changed`.

## Out of scope
- Remote package registry archive publishing and repository mirroring (`T858`–`T861`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P20 (`P20-build-system-package-ecosystem`), depends on P16 gate `T316` and P18 gate `T318` (`ROADMAP.md` §2–§3).
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T856/build` and `python tools/axtest.py --compiler build-snap-T856/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:12:00 created by T220 (P20 phase planning)
- 2026-11-08 23:43:33 started (attempt 1) T856-impl
