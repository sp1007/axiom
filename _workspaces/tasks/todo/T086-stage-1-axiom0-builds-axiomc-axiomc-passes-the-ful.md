---
id: T086
title: Stage-1: axiom0 builds axiomc; axiomc passes the full suite
phase: P10-selfhost
owner: axiom-qa
reviewer: axiom-architect
model: opus
gate_model: opus
depends: [T085, T134, T139, T140, T141, T142, T143, T144, T145, T146]
priority: 120
status: todo
attempts: 0
paths: [tools/bootstrap.py, tests/selfhost/stage1, tests/perf]
spec: [0167, 0150, tasks/0371]
covers: [REQ-OWN-001, REQ-OWN-002, REQ-OWN-003, REQ-OWN-004, REQ-OWN-005, REQ-OWN-006]
---
# T086 — Stage-1: axiom0 builds axiomc; axiomc passes the full suite

## Goal
The Axiom compiler, written in Axiom, works.

## Scope
- tools/bootstrap.py builds axiomc with axiom0, using `--stack-reserve 67108864` (64 MB, ADR-0003); the runner runs the suite with `--compiler axiomc --exclude-requires axiom0-internal` (C unit tests, encoder tables and C test drivers cannot run against axiomc).

## Acceptance
- [ ] Every test without `requires: axiom0-internal` passes with axiomc1; the report lists the excluded count per kind.
- [ ] **Independent subset (ADR-0034 §3)** — with `--compiler <axiomc1>`, natively built, every test of the following passes in every mode it declares, none of them `requires: axiom0-internal`, none restricted to `modes: interp` except "oracle-only check" tests: `tests/conformance/**`; `tests/run/numeric/**` including the Python-generated integer table and `int_semantics_current.test` (T140); `tests/run/drop/**` and `tests/run/mangle/**` (T141); the hash vectors — `tests/std/core/qa_hash_vectors.ax` and the real-module `compiler/kernel/hash.ax` test against `hash_vectors.txt` (T134); `tests/link/objdump_validate.test` on executables and objects written by axiomc1 (T142); the Axiom twin of the GNU-as vectors `tests/encode/axiom/gnu_as_vectors.ax` and `encode_tables_current.test` (T143); `tests/ui/parse/terminator_*` (T146); every `bundles_current.test` (T144). The report lists the subset's test count and PASS count separately from the rest of the suite; the gate is BLOCKED if any subset test fails or is skipped.
- [ ] The runner's `WEAK-NATIVE` count (T139) is 0 under `tests/run/numeric`, `tests/run/drop`, `tests/run/ptr`, `tests/run/native_*` and `tests/std` with axiomc1 (T145).
- [ ] `--emit=obj` of axiomc1 and of axiom0 are byte-identical for every tests/run program (the cheapest whole-compiler differential check; category B evidence, ADR-0034 §1 — necessary, not sufficient); any difference is explained and fixed.
- [ ] Budget (ADR-0005 §7): wall time and peak memory of axiom0 → axiomc1 and of the axiomc1 self-compile, with `--time-passes`, recorded in `tests/perf/selfhost.csv` and within the SPEC-20 budget. Over budget → report BLOCKED: the architect applies the regalloc contingency before T087.
- [ ] QA does not patch the compiler: each failure becomes a fix task for the owning port task (filed by the architect); the gate closes only when they are done.
- [ ] Gate rule (ADR-0005 §3): PASS or BLOCKED. Every non-passing test is an `xfail: <task-id>` for a spec gap that has an ADR; implementation bugs are fixed (their fix task done) before the gate closes; XPASS counts as a failure.
- [ ] `python tools/gatecheck.py`, `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] The per-task build command of axiomc (through `tools/bootstrap.py`, output into `build-snap-<ID>/build`) is stated in the report; T087 turns it into `tools/build_axiomc.py`.
- [ ] Full test suite passes (not only new tests); build warning-free; archcheck clean (once available).
- [ ] Report `_workspaces/reports/T086-report.md` with exact `## Files changed`.

## Out of scope
- Features scheduled for later tasks (see spec/SPEC-00-bootstrap.md milestone ladder); do not jump ahead.

## Notes
- Spec refs are docs/base/specs numbers unless prefixed `tasks/` or `spec/`; read `spec/` canonical docs first (axiom-spec-index).
- All Axiom code uses canonical syntax (axiom-syntax): `=` only, `.` paths only.
- Oracle independence (ADR-0034, audit `_workspaces/audit/2026-10-19/oracle-independence.md`): most
  selfhost evidence compares the port with axiom0 (category B) and inherits axiom0's design defects;
  the independent subset above is what proves axiomc1 correct. Prerequisites added 2026-10-20: T140
  (AX0-FIX-02 integer semantics), T141 (AX0-FIX-03 Drop), T142 (objdump), T143 (GNU-as twin), T144
  (bundle freshness), T145 (native-evidence sweep), T146 (AX0-FIX-04 terminator).
- axiom0 is built fresh in the snapshot (`build-snap-T086/build`); `build/axiom0.exe` in the main tree
  is stale and must not be used to build axiomc1.

## Log
- 2026-10-06 02:24:24 covers += REQ-OWN-001, REQ-OWN-002, REQ-OWN-003, REQ-OWN-004, REQ-OWN-005, REQ-OWN-006 (metadata only)
