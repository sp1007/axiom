---
id: T016
title: Driver CLI: check/build/run/inspect, pass timing, JSON diagnostics
phase: P2-frontend
owner: axiom-frontend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T015]
priority: 26
status: done
attempts: 1
paths: [bootstrap/axiom0/src/driver, tests/driver]
locks: [bootstrap/axiom0/src/diag/codes/DRIVER.def, bootstrap/axiom0/src/diag/codes/IO.def]
spec: [0257, tasks/0411, 0146]
started: 2026-10-06 03:31:40
finished: 2026-10-06 03:55:34
---
# T016 — Driver CLI: check/build/run/inspect, pass timing, JSON diagnostics

## Goal
Stable CLI contract for humans, tests and AI agents.

## Scope
- Commands: `check`, `build -o`, `run [--interp]`, `inspect --emit=...`, `version`, `--features` (capability probe for the runner).
- Options: `--target`, `-O0/-O1`, `--json`, `--time-passes`, `--color=never`; exit codes: 0 ok, 1 diagnostics, 2 usage, 3 ICE.
- Pipeline orchestration module that later stages plug into (stubs return 'not yet supported' diagnostics).
- `src/driver/pipeline.c`: the ordered stage list (source → lex → parse → resolve → HIR → …) that commands and emitters call. A later stage task adds one registration line here (the file is its `locks:` entry) and keeps its glue code in its own module; emitters written before this task (tokens, ast, resolved, hir) are switched to the pipeline here. `--features` is derived from the registered stages.
- Options are declared in a table next to the command or stage that owns them, so later tasks add theirs (`--stack-reserve` T027/T028, `--std-root` T060, `--verify-each` T043) without editing a shared parser.
- `run [--interp] file.ax -- <args…>` passes program arguments through (runner directive `args:`; ADR-0002).

## Acceptance
- [ ] tests/driver cases for each command/option and exit code.
- [ ] A test stage and a test option registered from a scratch file work without editing the option parser (shown in the report).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T016-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-06 03:31:40 started (attempt 1) T016-impl
- 2026-10-06 03:55:34 accepted by QA -> done
