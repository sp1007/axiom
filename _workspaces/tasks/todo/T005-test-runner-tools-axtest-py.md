---
id: T005
title: Test runner tools/axtest.py
phase: P0-foundation
owner: axiom-qa
reviewer: axiom-architect
depends: [T004]
priority: 11
status: todo
attempts: 0
paths: [tools/axtest.py, tools/tests, tests/README.md]
spec: [0166, 0145, 0017]
---
# T005 — Test runner tools/axtest.py

## Goal
Implement the test runner specified in the axiom-testing skill so every later task can express acceptance as tests.

## Scope
- Discovery of tests/**.ax; directives: test/exit/stdout/modes/target/flags; inline `//~ ERROR|WARN CODE` and `//~^`.
- Kinds: run (interp/native, native skipped until compiler supports it via capability probe `axiom0 --features`), ui, golden (tokens/ast/hir/thir/mir/lir by sibling file extension), diff.
- --filter, --verbose, --json, --bless, --compiler, -j N parallel, timeout per test, summary line `TOTAL n PASS p FAIL f SKIP s`, non-zero exit on failure.
- Self-tests in tools/tests using a stub compiler script to prove each directive works.

## Acceptance
- [ ] Runner self-tests pass (`python tools/tests/run_selftests.py`).
- [ ] Pure Python 3 standard library.
- [ ] Documented in tests/README.md.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T005-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
