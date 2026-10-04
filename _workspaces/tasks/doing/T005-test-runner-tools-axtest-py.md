---
id: T005
title: Test runner tools/axtest.py
phase: P0-foundation
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T004]
priority: 11
status: doing
attempts: 1
paths: [tools/axtest.py, tools/tests/axtest, tests/README.md]
spec: [0166, 0145, 0017]
started: 2026-10-04 07:58:18
agent: T005-impl
---
# T005 — Test runner tools/axtest.py

## Goal
Implement the test runner specified in the axiom-testing skill so every later task can express acceptance as tests.

## Scope
- Discovery of `tests/**.ax`, `*.test` manifests and project directories. Directives in the leading `//` comment lines: `test`, `exit`, `stdout`, `stderr`, `modes`, `target`, `flags`, `args`, `env`, `stdin`, `timeout`, `xfail: <task-id> <reason>`, `skip-unless: tool <name>`, `native-after: <task-id>`, `requires: axiom0-internal`; inline `//~ ERROR|WARN CODE` and `//~^`.
- Kinds: `run` (interp and native; a mode the compiler does not advertise through `axiom0 --features` is SKIP "mode unavailable" — a missing or failing `--features` means no modes, never an error); `ui`; `golden` (any sibling `x.<ext>` of `x.ax` is compared with `inspect --emit=<ext>`: tokens, ast, resolved, hir, thir, mir, lir, mi, mc, … — a new emitter needs no runner edit); `diff`; `exec` (a `*.test` manifest: `cmd:` with `{compiler}` / `{build}` placeholders, expected `exit` / `stdout`, `skip-unless`, `requires` — used for C unit tests, encoder tables, object/link checks and the cross-link oracle).
- Project tests: a directory that contains `axiom.toml` is one test; its directives are read from `src/main.ax`; files inside it are not discovered separately (used from T060 on).
- `native-after: <task-id>` (ADR-0005 §1): the native mode of that test is SKIP with the reason "native after <task-id>"; `--list-directive native-after:T033` prints the files still carrying it.
- Result states (0264 §18): PASS, FAIL, SKIP (always with a reason), XFAIL, XPASS (an expected failure that passes — counted as a failure), CRASH (compiler exit code 3, or an access-violation/abort status that the test does not expect), TIMEOUT. Default timeout 10 s per step (`timeout:` overrides, `--timeout-scale N`).
- `--filter`, `--verbose`, `--json`, `--bless`, `--compiler`, `--std-root` (passed through; default `std`), `-j N`, `--exclude-requires axiom0-internal` (used when the compiler under test is axiomc, T086). Summary line `TOTAL n PASS p FAIL f SKIP s XFAIL x`, where FAIL includes XPASS, CRASH and TIMEOUT; non-zero exit when FAIL > 0.
- Subprocess I/O in binary: expected `stdout:` directives are decoded as UTF-8 escapes and compared byte-for-byte with the raw output (a stray `\r` or wrong UTF-8 byte is a FAIL, with a hex diff in the message).
- Self-tests in tools/tests/axtest using a stub compiler script to prove each directive, kind and state works.
- This is the only task that edits tools/axtest.py (ADR-0005 §2): every kind and directive later tasks need is delivered here.

## Acceptance
- [ ] Runner self-tests pass (`python tools/tests/axtest/run_selftests.py`).
- [ ] Pure Python 3 standard library.
- [ ] Self-tests include: exact match of `Xin chào thế giới\n` (22 + 1 bytes), and failures for a CRLF variant and a variant with one wrong UTF-8 byte.
- [ ] Self-tests for every directive and state: `args` / `env` / `stdin` reach the stub; `native-after` skips native only; a failing `xfail` test is XFAIL and a passing one is XPASS (exit code 1); `skip-unless: tool definitely-missing-tool` is SKIP; an `exec` manifest; a project directory; stub exit code 3 is CRASH; a sleeping stub is TIMEOUT; a stub without `--features` gives SKIP for run modes; `--exclude-requires`.
- [ ] Documented in tests/README.md (directive table, kinds, states, how later tasks add tests without editing the runner).
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T005-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.

## Log
- 2026-10-04 07:58:18 started (attempt 1) T005-impl
