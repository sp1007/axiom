---
id: T443
title: selfhost bundle_common.assemble_compiler_modules rejects duplicate module names with a clear error
phase: P11-concurrency-async
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T452]
priority: 20
status: todo
attempts: 0
paths: [tests/selfhost/bundle_common.py, tests/selfhost/bundle_common_selftest.py]
locks: [tests/selfhost]
spec: [spec/decisions/ADR-0042-architect-inbox-1-baseline-admissions-and-followups.md, spec/SPEC-20-selfhost.md]
covers: [REQ-TST-098]
---
# T443 — bundle_common rejects duplicate module names

## Goal
A module list with a repeated module name (the T430 root cause: 126 `AX_NAME_DUPLICATE` errors deep inside a 30k-line
bundle) fails at generation time with one clear message naming the module and the caller (ADR-0042 §5).

## Scope
- `tests/selfhost/bundle_common.py::assemble_compiler_modules`: detect a module name listed twice (after
  normalisation) and raise an error `duplicate module(s) [...] in <caller list>`; no silent de-duplication.
- `tests/selfhost/bundle_common_selftest.py` (plain Python, runnable directly and by `axtest` if the group already
  runs `.py` self-tests; otherwise add a small `.test` manifest next to it): a duplicate is rejected; a clean list
  produces byte-identical output to today.
- Run every `tests/selfhost/*/gen_*.py --check`: all up to date (no generator output changes).

## Acceptance
- [ ] Self-test passes; mutation: removing the check makes it fail.
- [ ] All 36 generators `--check` up to date; all `selfhost/*/bundles_current.test` pass.
- [ ] Report `_workspaces/reports/T443-report.md` with exact `## Files changed`.

## Out of scope
- The generators' module lists (unless one has a duplicate: then report it), `compiler/`, `docs/`.

## Log
- 2026-11-13 created by axiom-architect (ADR-0042 §5, T430 follow-up)
