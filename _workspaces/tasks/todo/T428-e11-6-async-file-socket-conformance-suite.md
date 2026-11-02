---
id: T428
title: E11.6 — Async file, socket & timer conformance suite
phase: P11-concurrency-async
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T425, T426, T427]
priority: 151
status: todo
attempts: 0
paths: [tests/conformance/p11/e11_6_async_io]
spec: [spec/SPEC-35-async-io.md, 0221, tasks/0335, tasks/0438, tasks/0440, tasks/0441, tasks/0461, tasks/0464]
covers: [REQ-ASY-155, REQ-CONC-153]
---
# T428 — E11.6 — Async file, socket & timer conformance suite

## Goal
Verify the `E11.6` exit criterion ('async file/socket tests') across all `AXS-AIO-*` rules under both the deterministic oracle and native Windows x64 IOCP execution.

## Scope
- Create `tests/conformance/p11/e11_6_async_io/` testing multi-task `AsyncFile` pipelines, multi-client loopback `AsyncTcpListener`/`AsyncTcpStream` echo and framing with `split()` halves, `AsyncUdpSocket` burst exchange, `Timeout` + `CancellationToken` cancellation of in-flight file/socket reads (verifying buffer memory safety after Future drop), and `TaskGroup` + async I/O integration.

## Acceptance
- [ ] All tests in `tests/conformance/p11/e11_6_async_io/` pass in `[interp]`, `[native]`, and `[native-O1]` under `axiomc2.exe` (`WEAK-NATIVE 0`, `0 FAIL`).
- [ ] Full test suite passes in `build-snap-T428` under `axiomc2.exe`; `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T428-report.md` with exact `## Files changed`.

## Out of scope
- Modifying compiler or std source files.

## Notes
- Phase P11 (`P11-concurrency-async`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T428/build` and `python tools/axtest.py --compiler build-snap-T428/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:10:00 created by T211 (P11 phase planning)
