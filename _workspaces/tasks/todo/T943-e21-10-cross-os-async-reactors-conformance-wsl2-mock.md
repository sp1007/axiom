---
id: T943
title: E21.10 — Cross-OS async reactor conformance suite, WSL2 & mock test harness
phase: P21-standard-library-completion
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T941, T942]
priority: 255
status: todo
attempts: 0
paths: [tests/conformance/p21/e21_10_reactors, tests/mock/reactor]
spec: [spec/SPEC-129-cross-os-async-reactors.md, spec/decisions/ADR-0039-p12-p22-systems-web-zeroday-opengl-expansion.md]
covers: [REQ-RT-156, REQ-ASY-158]
---
# T943 — E21.10 — Cross-OS async reactor conformance suite, WSL2 & mock test harness

## Goal
Certify E21.10 exit criteria with a cross-platform asynchronous I/O conformance suite covering Windows IOCP, Linux `io_uring` + `epoll`, macOS `kqueue`, and a Windows host-side simulated reactor mock harness.

## Scope
- Create mock reactor test harness in `tests/mock/reactor` providing an in-memory event loop simulating arbitrary non-blocking I/O event arrival, partial reads, and kernel event queues.
- Create conformance test suite in `tests/conformance/p21/e21_10_reactors`:
  * Verify identical observable behavior of `AsyncRead`, `AsyncWrite`, and `TcpStream` across all reactor engines.
  * Stress-test high concurrency: 1,000 active concurrent connections transferring 10 MiB of random data with zero dropped bytes or deadlocks.
  * Execute cancellation torture tests: randomly drop in-flight I/O futures and verify that DMA buffers are not reused prematurely and file descriptors are properly closed.
  * Validate execution under Windows native (IOCP), WSL2 Linux (`io_uring` and `epoll`), and macOS (via Darwin Mach-O structural validation and runner).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p21/e21_10_reactors` pass on Windows and WSL2/Linux.
- [ ] Concurrency stress test achieves > 10,000 operations/sec with 0 memory corruption.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T943-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T943/build` and `python tools/axtest.py --compiler build-snap-T943/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-09 23:30:00 created by axiom-architect (ADR-0039 P21 async reactors expansion)
