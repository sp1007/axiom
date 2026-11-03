---
id: T854
title: E20.2 Canonical AXPACKAGE package manager, deterministic SemVer resolver, feature unification & axiom.lock specification (SPEC-111)
phase: P20-build-system-package-ecosystem
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T220, T316, T318]
priority: 204
status: todo
attempts: 0
paths: [spec/SPEC-111-package-manager-resolution-lockfiles.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-110-build-graph-driver.md, 0098, tasks/0412, tasks/0446, tasks/0661, tasks/1065]
covers: [REQ-ECO-8736, REQ-PKG-022, REQ-PKG-024, REQ-PKG-025]
---
# T854 — E20.2 Canonical AXPACKAGE package manager, deterministic SemVer resolver, feature unification & axiom.lock specification (SPEC-111)

## Goal
Consolidate the canonical specification for Axiom's `AXPACKAGE` package identity, SemVer 2.0 version constraint solver, monotonic feature unification, side-by-side major-version dependency isolation, and `axiom.lock` reproducibility contract into `spec/SPEC-111-package-manager-resolution-lockfiles.md` (`AXS-PKG-*` rule IDs).

## Scope
- Write `spec/SPEC-111-package-manager-resolution-lockfiles.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-PKG-NNN` rules.
- Specify `PackageIdentity = (Registry, Namespace, Name, Version, SourceId, ContentHash, SemanticInterfaceFingerprint)` (`0098 §4-8`, `tasks/0412 §4-7`, `tasks/0446 §187.2-6`, `tasks/1065 §4-17`) and SemVer 2.0 version constraints (`=`, `^`, `~`, inequality ranges, pre-release and build-metadata ordering) for registry, VCS (commit-pinned), path, and workspace dependencies (`REQ-PKG-022`, `REQ-ECO-8736`).
- Specify deterministic compile-time/build-time dependency resolution (`AXPACKAGE`) without runtime resolution (`REQ-PKG-024`), conflict explanation trees, side-by-side major version isolation with distinct nominal type identities unless bridged by an explicit public dependency re-export (`0098 §10-12`, `tasks/0661 §10`), and monotonic additive feature unification across `normal`, `dev`, and `build` graphs that never silently disables required features or alters source semantics (`REQ-PKG-025`).
- Specify the canonical `axiom.lock` v1 format (lexicographically sorted packages, exact resolved versions, source coordinates, SHA-256 content hashes, enabled feature sets, target conditions, and `SdkFingerprint` bindings), `--locked` / `--offline` / `--vendor` modes, and the `axiomc pkg` CLI subcommands (`tasks/0446 §187.5-6`, `tasks/1065 §24-60`).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-111-package-manager-resolution-lockfiles.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-PKG-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T854-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of the SemVer solver, lockfile store, and `axiomc pkg` CLI (`T855`–`T856`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P20 (`P20-build-system-package-ecosystem`), depends on P16 gate `T316` and P18 gate `T318` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:12:00 created by T220 (P20 phase planning)
