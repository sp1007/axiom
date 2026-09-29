---
id: T074
title: std.io / fs / env / process for hosted Windows
phase: P9-stdlib
owner: axiom-stdlib
reviewer: axiom-qa
depends: [T071, T065]
priority: 105
status: todo
attempts: 0
paths: [std/io, std/fs, std/env, std/process, tests/std/io]
spec: [0330, tasks/0335, 0220, 0221]
---
# T074 — std.io / fs / env / process for hosted Windows

## Goal
Enough OS access to write a compiler in Axiom.

## Scope
- stdout/stderr writers, read/write whole files, command-line args, environment, exit, errors as Result types.

## Acceptance
- [ ] run tests using temp files.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T074-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
