---
id: T804
title: E19.2 Canonical language form, lossless CST trivia model & deterministic formatter specification (SPEC-101)
phase: P19-developer-tooling
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T219, T318]
priority: 194
status: todo
attempts: 0
paths: [spec/SPEC-101-canonical-formatter.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-01-lexical.md, spec/SPEC-02-grammar.md, tasks/0476, tasks/0374, tasks/0448, tasks/0693, tasks/0695, tasks/0696]
covers: [REQ-TOOL-183, REQ-TOOL-298]
---
# T804 — E19.2 Canonical language form, lossless CST trivia model & deterministic formatter specification (SPEC-101)

## Goal
Consolidate the canonical specification for Axiom's lossless Concrete Syntax Tree (CST) trivia model and zero-configuration canonical formatter (`axiomc fmt`) into `spec/SPEC-101-canonical-formatter.md` (`AXS-FMT-*` rule IDs).

## Scope
- Write `spec/SPEC-101-canonical-formatter.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-FMT-NNN` rules.
- Specify the lossless CST / token-trivia attachment model built on the shared compiler lexer/parser (`REQ-TOOL-183`, `REQ-TOOL-298`), preserving line comments (`//`), block comments (`/* */`), doc comments (`///`, `//!`), intentional blank lines, and UTF-8 spans (`tasks/0476 §217.97-99`).
- Specify the canonical formatting rules for all Axiom v1.0 constructs (`tasks/0476 §217.1-134`): `=` binding/assignment, `.` paths, `use` grouping/sorting, 4-space indentation, brace placement, trailing commas in multi-line lists, Wadler-Lindig width-bounded line breaking, and canonical newline statement termination.
- Specify the formatter safety invariants: AST equivalence (`parse(fmt(src)) == parse(src)` modulo trivia), strict idempotence (`fmt(fmt(src)) == fmt(src)`), and refusal to overwrite files containing syntax errors.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-101-canonical-formatter.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-FMT-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T804-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of the CST formatter and `axiomc fmt` CLI (`T805`–`T806`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P19 (`P19-developer-tooling`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 09:50:00 created by T219 (P19 phase planning)
