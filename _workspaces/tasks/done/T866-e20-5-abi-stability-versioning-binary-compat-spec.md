---
id: T866
title: E20.5 Canonical Axiom ABI stability tiers, versioned symbol contracts, AbiFingerprint/ApiFingerprint & binary compatibility specification (SPEC-114)
phase: P20-build-system-package-ecosystem
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T220, T681, T685, T318]
priority: 216
status: done
attempts: 1
paths: [spec/SPEC-114-abi-stability-versioning-binary-compat.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-24-artifact-format-module-interfaces.md, spec/SPEC-50-unsafe-ub-ffi.md, 0104, tasks/0452, tasks/0583, tasks/0739, tasks/0661, tasks/1065]
covers: [REQ-ECO-8734, REQ-PKG-022, REQ-PKG-024]
started: 2026-11-08 20:00:56
finished: 2026-11-08 20:32:40
---
# T866 — E20.5 Canonical Axiom ABI stability tiers, versioned symbol contracts, AbiFingerprint/ApiFingerprint & binary compatibility specification (SPEC-114)

## Goal
Consolidate the canonical specification for Axiom's three ABI tiers (`Internal`, `Package/Interface`, `Stable Binary`), the four compatibility dimensions (`Source`, `Semantic`, `ABI`, `Binary`), `@abi(stable, version = "...")` type and function contracts, symbol versioning, and automated SemVer/ABI compatibility checking into `spec/SPEC-114-abi-stability-versioning-binary-compat.md` (`AXS-ABI-*` rule IDs).

## Scope
- Write `spec/SPEC-114-abi-stability-versioning-binary-compat.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-ABI-NNN` rules.
- Specify the three ABI tiers (`0104 §1-7`, `tasks/0452 §193.2-8`, `tasks/0583 §324.2-10`): `Internal Axiom ABI` (default, freely optimizable across compiler versions), `Package Interface ABI` (`.axmeta` semantic/generic interface consumed with compiler/target fingerprint verification; `tasks/0739`), and `Stable Binary ABI` (explicit opt-in via `@abi(stable, version = "1.0")` or `@repr(C)` / `@repr(transparent)`).
- Specify the Stable Axiom ABI type system (`0104 §8-20`, `tasks/0452 §193.8-18`, `tasks/0583 §324.9-22`): fixed-width scalars, `@abi(stable)` structs with extensible `size`/`version` headers, `@abi(stable)` tagged enums, opaque handle types (`@opaque`), stable borrowed views (`StableView<T>`, `StableStr`), explicit allocator-paired owned buffers, erased generic exports, and compile-time rejection of unstable types (raw closures, non-stable generics, unrepr'd ADTs) across `@abi(stable)` boundaries (`REQ-ECO-8734`, `REQ-PKG-024`).
- Specify distinct `ApiFingerprint`, `SemanticFingerprint`, and `AbiFingerprint` hashes (`tasks/0452 §193.20-21`, `tasks/0583 §324.2`, `tasks/0739 §493.21-23`), symbol versioning (`@symbol_version`), and the `axiomc abi-check` SemVer/binary compatibility classifier (`compatible`, `minor-additive`, `major-breaking`; `REQ-PKG-022`).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-114-abi-stability-versioning-binary-compat.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-ABI-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T866-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of the `@abi(stable)` checker, fingerprint calculator, and `axiomc abi-check` CLI (`T867`–`T868`).
- Dynamic plugin loading and hot-reload runtime (`T870`–`T873`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P20 (`P20-build-system-package-ecosystem`), depends on P16 gate `T316` and P18 gate `T318` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:12:00 created by T220 (P20 phase planning)
- 2026-11-08 20:00:56 started (attempt 1) T866-impl
- 2026-11-08 20:32:40 accepted by QA -> done
