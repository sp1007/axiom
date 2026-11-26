---
id: T423j
title: Baseline fix — link/dll/gnu_ld_run.test fails on the T428a async tests (`__ax_host_aio_close` / `__ax_host_aio_cancel` undefined for GNU ld)
phase: P12-numeric-floating-point-simd
owner: axiom-frontend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: []
priority: 5
status: todo
attempts: 0
timeout_min: 300
paths: [tests/link/dll/gnu_ld_run_oracle.py]
locks: [compiler/driver/pipeline.ax, _workspaces/baseline-failures.txt]
spec: [spec/SPEC-26-windows-artifact-kinds.md, spec/decisions/ADR-0048-std-module-loading-host-providers.md, spec/decisions/ADR-0034-oracle-independence.md, spec/decisions/ADR-0002-oracle-host-interface.md]
covers: [REQ-TST-072]
---
# T423j — The GNU ld cross-link oracle links the async I/O host providers

## Why
Found by the T428m Tier-1 sweep (`_workspaces/reports/T428m-report.md`) and reproduced by the architect with the HEAD
compiler `_workspaces/artifacts/compiler-cache/axiomc2_O1_642250f08b7af786.exe` (`_workspaces/reports/unblock-T428m.md`):
`tests/link/dll/gnu_ld_run_oracle.py` reports `5/1143 GNU ld cross-linked tests failed`, all under
`tests/run/async/addr_stable_locals/` (added by T428a, 61acdeb9): `tcp_local_stream.ax`, `udp_recv_from_local.ax`,
`qa_cancel_spawned_intrusive.ax`, `qa_cancel_spawned_task.ax`, `qa_r1_panic_pending_inplace.ax`. GNU ld stops with
`undefined reference to '__ax_host_aio_close'` / `'__ax_host_aio_cancel'`. Both symbols are defined in
`std/sys/windows/iocp.ax`, so the oracle's host-provider archive (`axiom_host_rt.lib`, built in step 1b from
`std/sys/windows/*.ax`) does not export them as GNU ld sees them, or the `--emit=obj` of the test references them
under a name the archive does not carry. The in-house PE linker links the same programs (the tests pass natively).
T423i fixed the same class of failure for the earlier host intrinsics. Admitted to the baseline on 2026-11-26 with
this task as its fix task.

## Scope
1. Diagnose which side is wrong: dump the external symbols of the `iocp.ax` provider object and of one failing
   `prog.obj` (the oracle already has `inspect_coff_external_symbols`) and compare the names/storage classes.
2. Fix it at the source. If the oracle builds or packs the providers incompletely, fix
   `tests/link/dll/gnu_ld_run_oracle.py`. If the compiler emits a wrong symbol (name, storage class, missing
   `pub`/export of a host provider in `--emit=obj` mode), fix it in `compiler/driver/pipeline.ax` (shared lock) and
   say so in the report; any other compiler file needed is reported as `STATUS: BLOCKED` with the exact list.
   Never skip the five tests and never add a per-test exclusion list.
3. Remove the `link/dll/gnu_ld_run.test` line from `_workspaces/baseline-failures.txt` in the same change.

## Acceptance
- [ ] `link/dll/gnu_ld_run.test` passes (`GNU-LD-RUN-ORACLE ok`, 0 failed cases) with the stage-2 compiler.
- [ ] Baseline line removed.
- [ ] If `compiler/driver/pipeline.ax` changed: stage-2 build and the stage-2 == stage-3 fixed point at `-O0`/`-O1`.
- [ ] Normal gate (task test + affected set + smoke); failing ids ⊆ `_workspaces/baseline-failures.txt`.
- [ ] Report `_workspaces/reports/T423j-report.md`: root cause, the fix, an exact `## Files changed`.

## Log
- 2026-11-26 created by architect (`_workspaces/reports/unblock-T428m.md`)
