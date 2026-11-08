---
id: T816
title: E19.5 Canonical documentation generator (axiomc doc) & integrated test/pass-bisection framework specification (SPEC-104)
phase: P19-developer-tooling
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T219, T752, T755, T756, T759, T812]
priority: 206
status: doing
attempts: 1
paths: [spec/SPEC-104-docgen-test-framework-ux.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-21-query-engine-semantic-db.md, spec/SPEC-103-diagnostics-ux-ai-interface.md, 0120, 0121, 0147, 0161, 0163, tasks/0361, tasks/0374, tasks/0418, tasks/0423, tasks/0662, tasks/0693, tasks/0695, tasks/0696]
covers: [REQ-TOOL-002, REQ-TOOL-003, REQ-TOOL-005, REQ-TOOL-006, REQ-TOOL-007, REQ-TOOL-008, REQ-TOOL-009, REQ-TOOL-010, REQ-TOOL-011, REQ-TOOL-179, REQ-TOOL-187, REQ-TST-112]
started: 2026-11-08 16:18:26
agent: T816-impl
---
# T816 — E19.5 Canonical documentation generator (axiomc doc) & integrated test/pass-bisection framework specification (SPEC-104)

## Goal
Consolidate the canonical specification for Axiom's documentation generator (`axiomc doc`) and integrated test, differential MIR-oracle, optimization pass replay/bisection, and debug/trace verification UX (`axiomc test`) into `spec/SPEC-104-docgen-test-framework-ux.md` (`AXS-DOC-*` and `AXS-TST-*` rule IDs).

## Scope
- Write `spec/SPEC-104-docgen-test-framework-ux.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-DOC-NNN` / `AXS-TST-NNN` rules.
- Specify `axiomc doc`: extracting `///` and `//!` documentation comments and resolved semantic signatures from `CompilerDB` (`tasks/0374`, `tasks/0693`), rendering canonical signatures (ownership, `view`/`mut_view` capabilities, trait bounds, safety contracts, `std` effect badges, intra-doc `[item.path]` links) to deterministic static HTML and JSON index, and executing fenced Axiom doc-tests (`tasks/0418`).
- Specify `axiomc test` UX 2.0 (`tasks/0361`, `tasks/0418`, `tasks/0423`, `tasks/0662`, `REQ-TST-112`): first-class `test "name" { ... }` discovery, isolated test-binary generation so build/test/oracle/trace features never change core language semantics or add runtime overhead to production binaries (`REQ-TOOL-002`, `REQ-TOOL-003`, `REQ-TOOL-008`, `REQ-TOOL-187`), MIR interpreter differential oracle validation (`REQ-TOOL-009`), optimization pass replay (`--opt-replay`) and automatic pass bisection (`--opt-bisect`) to isolate miscompilations (`REQ-TOOL-179`), and native debug-metadata verification hooks (target-independent semantic debug model `REQ-TOOL-007`, `-O0` `.debug_line` emission `REQ-TOOL-010` vs tiered rich DWARF sections `REQ-TOOL-011`, logical inlined frames `REQ-TOOL-006`, and honest `OptimizedOut` representation without artificial physical state `REQ-TOOL-005`).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-104-docgen-test-framework-ux.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-DOC-NNN` and `AXS-TST-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T816-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of `axiomc doc` and `axiomc test` (`T817`–`T818`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P19 (`P19-developer-tooling`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 09:50:00 created by T219 (P19 phase planning)
- 2026-11-08 16:18:26 started (attempt 1) T816-impl
