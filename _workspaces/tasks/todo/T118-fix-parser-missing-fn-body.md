---
id: T118
title: Fix parser crash on missing function body
phase: P2-frontend
owner: axiom-frontend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T013, T015b]
priority: 11
status: todo
attempts: 0
paths: [bootstrap/axiom0/src/syntax/parse.c, tests/parse]
locks: [bootstrap/axiom0/src/diag/codes/PARSE.def]
spec: [spec/SPEC-02-grammar.md]
covers: [REQ-GRM-001]
unblocks: 1
---
# T118 — Fix parser crash on missing function body

## Goal
Fix a parser bug where a missing function body sets `item->fn.body = NULL` without emitting a syntax error, causing a downstream crash in MIR building (discovered by `fuzz.py --smoke`).

## Scope
- Modify `parse_item` in `bootstrap/axiom0/src/syntax/parse.c` to conditionally require a function body.
- Permit bodiless functions in `extern` and `trait` blocks (if applicable) while emitting `AX_PARSE_EXPECTED_TOKEN` for standard functions.
- Add a parse golden test for missing function body to `tests/parse/`.

## Acceptance
- [ ] Parse golden test for missing function body passes.
- [ ] `fuzz.py --smoke` passes without timeout/crash on `fn n()`.
- [ ] Report `_workspaces/reports/T118-report.md` with exact `## Files changed`.

## Out of scope
- Other parser bug fixes.
