---
id: T858
title: E20.3 Canonical package registry protocol, .axpkg content-addressed archive, offline mirror & distribution runtime specification (SPEC-112)
phase: P20-build-system-package-ecosystem
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T220, T316, T318]
priority: 208
status: todo
attempts: 0
paths: [spec/SPEC-112-package-registry-distribution.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-111-package-manager-resolution-lockfiles.md, spec/SPEC-24-artifact-format-module-interfaces.md, tasks/0412, tasks/0665, tasks/0739, tasks/0858, tasks/1065]
covers: [REQ-ECO-8736, REQ-PKG-024]
---
# T858 — E20.3 Canonical package registry protocol, .axpkg content-addressed archive, offline mirror & distribution runtime specification (SPEC-112)

## Goal
Consolidate the canonical specification for Axiom's Native Application Package Registry, sparse/static repository index protocol, deterministic `.axpkg` distribution archive format, precompiled `.axmeta` binary/interface package consumption, offline mirrors, and update/rollback channels into `spec/SPEC-112-package-registry-distribution.md` (`AXS-REG-*` rule IDs).

## Scope
- Write `spec/SPEC-112-package-registry-distribution.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-REG-NNN` rules.
- Specify the architectural boundary between core compilation and the package registry (`tasks/0412 §8-10`, `tasks/0665 §1-8`, `tasks/0858 §1-18`, `REQ-ECO-8736`, `REQ-PKG-024`): the compiler never performs implicit network calls during compilation; package fetching is an explicit, content-verified pre-build step.
- Specify the deterministic `.axpkg` archive format (sorted POSIX relative paths, zeroed modification timestamps, normalized permissions, embedded canonical `axiom.toml`, `.axmeta` interface summary, and SHA-256 Merkle tree digest), immutable published package versions (`tasks/0858 §16-17`), and source vs precompiled `.axmeta` binary/interface package consumption (`tasks/0665 §8`, `tasks/0739 §493.1-12`).
- Specify the sparse registry index protocol, multi-repository configuration with explicit priority vs trust routing (`tasks/0858 §11-14`), offline-first local repository mirrors (`tasks/0858 §9-10`, `tasks/1065 §50-65`), and update channel / transactional rollback metadata (`tasks/0858 §25-40`).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-112-package-registry-distribution.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-REG-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T858-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of the `.axpkg` archiver, registry client, and distribution CLI (`T859`–`T860`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P20 (`P20-build-system-package-ecosystem`), depends on P16 gate `T316` and P18 gate `T318` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:12:00 created by T220 (P20 phase planning)
