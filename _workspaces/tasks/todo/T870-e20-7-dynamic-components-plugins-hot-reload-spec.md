---
id: T870
title: E20.7 Canonical Axiom dynamic components, plugin discovery, cross-boundary ownership/capability handles & hot-reload state migration specification (SPEC-115)
phase: P20-build-system-package-ecosystem
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T220, T681, T685, T318, T866]
priority: 220
status: todo
attempts: 0
paths: [spec/SPEC-115-dynamic-components-plugins-hot-reload.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-114-abi-stability-versioning-binary-compat.md, spec/SPEC-89-artifact-library-matrix.md, 0104, tasks/0583, tasks/0584, tasks/0739, tasks/0856]
covers: [REQ-ECO-8734]
---
# T870 — E20.7 Canonical Axiom dynamic components, plugin discovery, cross-boundary ownership/capability handles & hot-reload state migration specification (SPEC-115)

## Goal
Consolidate the canonical specification for Axiom-to-Axiom dynamic components, plugin discovery/negotiation, cross-boundary ownership/capability/allocator isolation, epoch lease safety, and state-migrating hot-reload into `spec/SPEC-115-dynamic-components-plugins-hot-reload.md` (`AXS-COMP-*` rule IDs).

## Scope
- Write `spec/SPEC-115-dynamic-components-plugins-hot-reload.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-COMP-NNN` rules.
- Specify the Axiom Dynamic Component model beyond raw C ABI (`0104 §20-22, 54`, `tasks/0584 §325.1-19`, `tasks/0856 §1-25`, `REQ-ECO-8734`): `@component_interface` and `@plugin_export` declarations, embedded `.axcomp` component manifest sections (component ID, SemVer version, `AbiFingerprint`, required/provided capabilities, exported vtable descriptors), and load-time version + capability negotiation (`tasks/0584 §325.6-9`).
- Specify ownership, capability, and memory isolation across dynamic component boundaries (`tasks/0584 §325.10-21`, `tasks/0856 §16-24`): forbidding raw cross-module pointer escapes, pairing owned cross-boundary allocations with their originating component allocator (`ComponentBox<T>`), generational `ComponentHandle<T>` tables, and epoch-leased `view`/`mut_view` references that prevent unloading a component while any active borrow or stack frame remains live.
- Specify the deterministic hot-reload state-hand-off protocol (`tasks/0584 §325.22-24`, `tasks/0856 §26-40`, `0104 §54`): `Quiesce` (drain active epoch leases) → `ExportState` (typed schema-versioned state snapshot) → `UnloadOldEpoch` → `LoadNewEpoch` → `MigrateState` (schema verification and state hand-off) → `Resume`, with transactional rollback to the old epoch if migration fails.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-115-dynamic-components-plugins-hot-reload.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-COMP-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T870-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of the `@component_interface` compiler checks and `std.component` runtime (`T871`–`T872`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P20 (`P20-build-system-package-ecosystem`), depends on P16 gate `T316` and P18 gate `T318` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:12:00 created by T220 (P20 phase planning)
