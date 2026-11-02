---
id: T605
title: E15.2 — Canonical alias analysis, escape analysis & allocation promotion specification (SPEC-71)
phase: P15-optimizer-2-0
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T215, T600]
priority: 98
status: done
attempts: 1
paths: [spec/SPEC-71-alias-escape-promotion.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-10-ownership.md, spec/SPEC-11-capability.md, spec/SPEC-70-optir-ssa-memoryssa.md, 0131, 0162, 0165, 0226, tasks/0366, tasks/0395, tasks/0397, tasks/0480, tasks/0486, tasks/0548]
covers: [REQ-OPT-008, REQ-OPT-012, REQ-OPT-024, REQ-OPT-025, REQ-OPT-027, REQ-OPT-028, REQ-OPT-029, REQ-OPT-299, REQ-OPT-300, REQ-OPT-301, REQ-OPT-302, REQ-OPT-303]
started: 2026-11-03 03:48:31
finished: 2026-11-03 04:01:51
---
# T605 — E15.2 — Canonical alias analysis, escape analysis & allocation promotion specification (SPEC-71)

## Goal
Consolidate the canonical specification for Axiom's capability- and provenance-driven alias analysis (`AliasInfo`), escape analysis (`EscapeInfo`), and storage/allocation promotion into `spec/SPEC-71-alias-escape-promotion.md` (`AXS-ALIAS-*` and `AXS-ESC-*` rule IDs).

## Scope
- Write `spec/SPEC-71-alias-escape-promotion.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-ALIAS-NNN` / `AXS-ESC-NNN` rules.
- Specify the `AliasInfo` lattice (`NoAlias`, `MustAlias`, `PartialAlias`, `MayAlias`) derived from Verified MIR ownership and capability facts (`view<T>` `READ`-only stability, `mut_view<T>` disjointness, distinct allocation roots, non-overlapping field/constant-index projections, and raw-pointer provenance conservative barriers — `tasks/0395`, `REQ-OPT-028`, `REQ-OPT-299..303`).
- Specify `EscapeInfo` classification (`NoEscape`, `ArgumentEscape`, `ReturnEscape`, `GlobalEscape` — `tasks/0397`, `REQ-OPT-357`) and the distinction between lifetime/capability validity and physical storage escape.
- Specify legality rules for heap-to-stack and stack-to-register allocation promotion (closures, futures, `Box`, bounded collections, temporary buffers — `REQ-OPT-008`, `REQ-OPT-012`, `REQ-OPT-024`, `REQ-OPT-025`) and the address-observability (`address_of` / `@at` / `volatile`) barrier (`REQ-OPT-027`, `REQ-OPT-029`).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-71-alias-escape-promotion.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-ALIAS-NNN` / `AXS-ESC-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T605-report.md` with exact `## Files changed`.

## Out of scope
- Compiler implementation of alias/escape passes (`T606`–`T607`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P15 (`P15-optimizer-2-0`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 02:39:00 created by T215 (P15 phase planning)
- 2026-11-03 03:48:31 started (attempt 1) 
- 2026-11-03 04:01:51 accepted by QA -> done
