---
id: T461c
title: Runner — `skip-unless: pymodule <name>` so generator checks that need a non-stdlib Python module (mpmath) skip instead of failing
phase: P12-numeric-floating-point-simd
owner: axiom-qa
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: []
priority: 90
status: todo
attempts: 0
timeout_min: 120
paths: [tests/tools/skip_unless_pymodule, tests/std/math/check_vectors.test, tests/std/math/check_tables.test]
locks: [tools/axtest.py, .claude/skills/axiom-testing/SKILL.md]
spec: [spec/SPEC-104-docgen-test-framework-ux.md]
covers: [REQ-TST-112]
---
# T461c — Python-module prerequisites in the test runner

## Why
`_workspaces/reports/T461-qa.md` N1: `tests/std/math/check_vectors.test` and `check_tables.test` run
`make_vectors.py --check` / `gen_tables.py --check`, which `import mpmath` (third party; present on this machine only
through sympy). On a machine without it both FAIL with `ImportError`; `skip-unless:` knows only `tool <name>` and
`feature <name>` (`tools/axtest.py`). Test tooling is stdlib-only by principle; a generator that needs a reference
library is fine, but its absence must be a visible SKIP, not a FAIL.

## Scope
1. `tools/axtest.py`: accept `skip-unless: pymodule <name>` (checked once per run with `importlib.util.find_spec` in
   the runner's own interpreter, the same one used for `cmd:` python steps — verify that and say so); the SKIP reason
   names the module. Update the directive table/error text (`needs tool|feature|pymodule`).
2. Add `// skip-unless: pymodule mpmath` (in the files' own directive syntax) to the two math checks.
3. Runner self-tests in `tests/tools/skip_unless_pymodule/`: a present module (`json`) runs, an absent one
   (`axiom_no_such_module_xyz`) skips with the reason, a malformed directive is an error.
4. Document the directive in `.claude/skills/axiom-testing/SKILL.md` (directive list, one line).

## Acceptance
- [ ] New self-tests pass; the two math checks still PASS here and SKIP with a reason when mpmath is hidden
      (show it with an environment where `find_spec("mpmath")` is None, e.g. `-I` plus a clean `PYTHONPATH`).
- [ ] `tests/tools/**`, `tests/std/math/**` pass; the cache key logic is unchanged for tests without the directive.
- [ ] Normal gate. Report `_workspaces/reports/T461c-report.md` with an exact `## Files changed`.

## Log
- 2026-11-26 created by architect (`_workspaces/reports/unblock-T428a.md`, triage of T461-qa.md N1)
