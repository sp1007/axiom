---
id: T440
title: Baseline fix — p18/p19/p20 oracle probes and lsp_vfs engine (maybe-timeout) with a loaded-machine timeout policy
phase: P11-concurrency-async
owner: axiom-qa
reviewer: axiom-architect
model: opus
gate_model: sonnet
depends: []
priority: 19
status: doing
attempts: 1
timeout_min: 600
paths: [tests/conformance/p18/e18_1_query_engine, tests/conformance/p18/e18_2_incremental, tests/conformance/p18/e18_3_parallel, tests/conformance/p19/e19_1_lsp_server, tests/conformance/p19/e19_2_formatter, tests/conformance/p19/e19_4_diagnostics_ai, tests/conformance/p20/e20_2_package_manager_lockfile, tests/run/lsp_vfs]
locks: [_workspaces/baseline-failures.txt]
spec: [spec/decisions/ADR-0042-architect-inbox-1-baseline-admissions-and-followups.md, spec/decisions/ADR-0041-complete-suite-baseline-and-test-cache.md, spec/SPEC-21-query-engine-semantic-db.md, spec/SPEC-100-lsp-server-ide-engine.md]
covers: [REQ-TST-073, REQ-TST-074, REQ-TST-076]
started: 2026-11-13 19:11:20
agent: T440-impl
---
# T440 — Baseline fix: oracle probes that fail under load (maybe-timeout)

## Goal
The 8 `undiagnosed:maybe-timeout` ids of `_workspaces/baseline-failures.txt` are each either passing reliably on the
shared machine or turned into a precisely diagnosed fix task; no oracle hides a hang behind a larger timeout
(ADR-0042 §1).

## Scope
- Ids: `conformance/p18/e18_1_query_engine/e18_1_query_engine_oracle.test`, `.../e18_2_incremental_oracle.test`,
  `.../e18_3_parallel_oracle.test`, `conformance/p19/.../e19_1_lsp_server_oracle.test`, `e19_2_formatter_oracle.test`,
  `e19_4_diagnostics_ai_oracle.test`, `conformance/p20/.../e20_2_package_manager_lockfile_oracle.test`,
  `run/lsp_vfs/lsp_vfs_engine.test`. Observed (T422-qa §7): Python traceback in each; e18_1 reports
  `e18_1_query_engine_probe --interp failed (143)` (killed on timeout); identical at HEAD; the machine was loaded.
- Policy (ADR-0042 §1, axiom-qa.md): run each id (a) alone on an idle machine, (b) alone with `--timeout-scale 6`,
  (c) under the usual `-j 2` load. Record wall time of the probe build and of the probe run per mode.
  - Load-only (passes in (a)/(b), fails in (c) by timeout): make the oracle's internal subprocess timeouts honour the
    runner's scale (read `AXTEST_TIMEOUT_SCALE` or an equivalent argument the runner already passes; if the runner
    passes nothing, use one env variable and document it in the oracle header) and size them from the measured time
    x 3; the id must then pass under (c).
  - Real failure (fails in (a)): read the traceback, fix the oracle/probe template if the defect is in the test
    (as T430 did for the optimizer probes); a defect in `compiler/` or `std/` is reported with a minimal repro for a
    split (architect), and the id stays on the baseline under the new task.
- Remove the lines of every id that now passes under (c); reclassify the rest with the new task id.

## Acceptance
- [ ] Per-id table in the report: result and wall time for (a), (b), (c), root cause, action.
- [ ] Every id whose line is removed passes three times in a row under `-j 2` in `build-snap-T440`.
- [ ] No oracle timeout exceeds 3x its measured time at scale 1; no infinite wait introduced.
- [ ] Gate per axiom-qa.md "Per-task gate scope"; failing ids ⊆ baseline after the edits.
- [ ] Report `_workspaces/reports/T440-report.md` with exact `## Files changed`.

## Out of scope
- `tools/axtest.py` (a runner change becomes a follow-up), `compiler/`, `std/`, `docs/`.

## Notes
- Related flake (T422-qa): `selfhost/ast/qa_ast_*` hit the 10 s build-step timeout under load and pass with
  `--timeout-scale 6`; mention in the report whether the same scale mechanism would cover them (no edit here).

## Log
- 2026-11-13 created by axiom-architect (ADR-0042 §1, architect inbox 1)
- 2026-11-13 19:11:20 started (attempt 1) T440-impl
