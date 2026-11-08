---
id: T808
title: E19.3 Canonical semantic refactoring engine & AST-aware AXDIFF/AXMERGE/AXPATCH/AXHISTORY/AXVCS specification (SPEC-102)
phase: P19-developer-tooling
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T219, T752, T755, T756, T759, T800, T804]
priority: 198
status: todo
attempts: 0
paths: [spec/SPEC-102-refactoring-engine-semantic-vcs.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-100-lsp-server-ide-engine.md, spec/SPEC-101-canonical-formatter.md, 0101, tasks/0448, tasks/1059, tasks/1060, tasks/1061, tasks/1062, tasks/1063, tasks/1064]
covers: [REQ-TOOL-183, REQ-TOOL-186, REQ-TOOL-301, REQ-TOOL-302, REQ-TOOL-303, REQ-TOOL-304, REQ-TOOL-305]
---
# T808 — E19.3 Canonical semantic refactoring engine & AST-aware AXDIFF/AXMERGE/AXPATCH/AXHISTORY/AXVCS specification (SPEC-102)

## Goal
Consolidate the canonical specification for Axiom's `CompilerDB`-verified refactoring engine and semantic-aware diff/merge/patch/history/VCS subsystems (`AXDIFF`, `AXMERGE`, `AXPATCH`, `AXHISTORY`, `AXVCS`) into `spec/SPEC-102-refactoring-engine-semantic-vcs.md` (`AXS-REF-*` rule IDs).

## Scope
- Write `spec/SPEC-102-refactoring-engine-semantic-vcs.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-REF-NNN` rules.
- Specify semantics-preserving refactoring operations driven by `CompilerDB` (`0101 §12-17`, `REQ-TOOL-183`, `REQ-TOOL-186`): extract function (synthesizing owned, `view`, and `mut_view` parameters and return types from ownership/capability flow), extract/inline local binding, generate missing exhaustive `match` arms, canonicalize `use` imports, and capability-qualification upgrades.
- Specify the semantic-aware `AXDIFF` tree comparator (`0101 §45`, `tasks/1059`, `REQ-TOOL-301`), AST-aware 3-way `AXMERGE` conflict resolver (`tasks/1060`, `REQ-TOOL-302`), transactional AST/text `AXPATCH` engine (`tasks/1061`, `tasks/1064`, `REQ-TOOL-303`), symbol/refactoring lineage `AXHISTORY` graph (`tasks/1062`, `REQ-TOOL-304`), and deterministic semantic-aware `AXVCS` repository model (`tasks/1063`, `REQ-TOOL-305`).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-102-refactoring-engine-semantic-vcs.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-REF-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T808-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of the refactoring transforms and `AXDIFF`/`AXMERGE`/`AXPATCH`/`AXHISTORY`/`AXVCS` (`T809`–`T810`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P19 (`P19-developer-tooling`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 09:50:00 created by T219 (P19 phase planning)
