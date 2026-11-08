---
id: T807
title: E19.2 Canonical formatter idempotence, comment preservation & full-corpus conformance suite
phase: P19-developer-tooling
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T219, T752, T755, T756, T759, T806]
priority: 197
status: doing
attempts: 1
paths: [tests/conformance/p19/e19_2_formatter]
spec: [spec/SPEC-101-canonical-formatter.md, tasks/0476, tasks/0693, tasks/0695, tasks/0696]
covers: [REQ-TOOL-183, REQ-TOOL-298]
started: 2026-11-08 17:55:58
agent: T807-impl
---
# T807 — E19.2 Canonical formatter idempotence, comment preservation & full-corpus conformance suite

## Goal
Certify E19.2 and P19 formatter exit criteria (`formatter idempotence over the whole corpus`) with a comprehensive conformance suite covering `compiler/`, `std/`, and `tests/`.

## Scope
- Create conformance tests in `tests/conformance/p19/e19_2_formatter` verifying:
  - `fmt(fmt(src)) == fmt(src)` idempotence and AST/semantic invariance across the entire valid Axiom corpus (`compiler/`, `std/`, and `tests/`);
  - preservation of all line, block, and doc comments (`//`, `/* */`, `///`, `//!`) and UTF-8 literals (including `"Xin chào thế giới"`);
  - `axiomc fmt --check` exit code and diff accuracy, plus LSP formatting agreement with CLI formatting;
  - differential equivalence between `--interp` and native execution (`0 WEAK-NATIVE`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p19/e19_2_formatter` pass in `--interp` and native modes with `0 WEAK-NATIVE`, proving formatter idempotence over the whole corpus.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T807-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P19 (`P19-developer-tooling`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T807/build` and `python tools/axtest.py --compiler build-snap-T807/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 09:50:00 created by T219 (P19 phase planning)
- 2026-11-08 17:55:58 started (attempt 1) T807-impl
