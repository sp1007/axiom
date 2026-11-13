---
id: T431
title: Baseline fix — artifact container, separate compilation, build graph, PE DLL link, build --emit=obj, encoder tables
phase: P11-concurrency-async
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T452]
priority: 16
status: todo
attempts: 0
timeout_min: 900
paths: [tests/run/artifact_container, tests/conformance/p18/e18_4_artifacts, tests/conformance/p18/e18_6_separate_compilation, tests/conformance/p20/e20_1_build_graph_driver, tests/driver/build_emit_obj.test, tests/link/dll, tests/encode, compiler/artifact, compiler/link, compiler/obj, compiler/build]
locks: [tests/selfhost, compiler/driver, tools/gen_encode_tests.py, _workspaces/baseline-failures.txt]
spec: [spec/decisions/ADR-0041-complete-suite-baseline-and-test-cache.md, spec/SPEC-24-artifact-format-module-interfaces.md, spec/SPEC-26-windows-artifact-kinds.md, spec/SPEC-27-separate-compilation-linker-v2.md, spec/SPEC-110-build-graph-driver.md]
covers: [REQ-LNK-614, REQ-LNK-073, REQ-LNK-057, REQ-PKG-022]
---
# T431 — Baseline fix: artifact / link / encoder / build-path failures

## Goal
The 8 ids listed for T431 in `_workspaces/baseline-failures.txt` pass again under `axiomc2` (or, for a host-tool
dependency, SKIP through `requires:` and are reclassified `environment`).

## Scope
- Diagnose each id at HEAD with `-v`: `run/artifact_container/artifact_container_engine.test`,
  `conformance/p18/e18_4_artifacts/e18_4_artifacts_oracle.test`,
  `conformance/p18/e18_6_separate_compilation/e18_6_separate_compilation_oracle.test`,
  `conformance/p20/e20_1_build_graph_driver/e20_1_build_graph_driver_oracle.test`, `driver/build_emit_obj.test`,
  `link/dll/gnu_ld_run.test`, `link/dll/pe_dll.test`, `encode/encode_tables_current.test`.
- `encode_tables_current.test` is a freshness check: regenerate the tables with `tools/gen_encode_tests.py` and
  confirm the regenerated encodings are correct (no hand edits).
- Probe/oracle drift in test harnesses (like T430) is fixed in the harness; a real regression in `compiler/artifact`,
  `compiler/link`, `compiler/obj`, `compiler/build` or `compiler/driver` is fixed there, with a regression test; any
  other `compiler/` area is reported for a split.
- A test that needs GNU `ld`/`gcc` must SKIP via `requires:` when the tool is absent; if that is the only cause, set the
  line's class to `environment` in the report and keep it out of the baseline only if it now SKIPs.
- Regenerate selfhost bundles that embed edited modules; remove the fixed T431 lines from the baseline.

## Acceptance
- [ ] Each of the 8 ids passes (or SKIPs for a documented missing host tool) under `axiomc2.exe` built in
  `build-snap-T431`.
- [ ] Complete suite: failing ids are a subset of the baseline after this task's removals; WEAK-NATIVE 0;
  `archcheck.py` clean; every `tests/selfhost/**/bundles_current.test` passes.
- [ ] The fixed lines are removed from `_workspaces/baseline-failures.txt` in this task's change set.
- [ ] Report `_workspaces/reports/T431-report.md` with each id's root cause and exact `## Files changed`.

## Out of scope
- `bootstrap/axiom0` (frozen). `docs/`. Compiler areas other than those named above.

## Notes
- Build/test in `build-snap-T431` with `tools/build_axiomc.py` and `tools/axtest.py --exclude-requires axiom0-internal -j 2`.

## Log
- 2026-11-13 07:40:00 created by axiom-architect (ADR-0041, complete-suite baseline)
