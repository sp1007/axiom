---
id: T941
title: E21.10 — Linux io_uring + epoll dual-engine reactor & IoOpState.CancellingZombie DMA safety
phase: P21-standard-library-completion
owner: axiom-backend
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T940, T652]
priority: 253
status: todo
attempts: 0
paths: [std/async/reactor/linux, tests/run/linux_reactors]
spec: [spec/SPEC-129-cross-os-async-reactors.md, spec/decisions/ADR-0039-p12-p22-systems-web-zeroday-opengl-expansion.md]
covers: [REQ-RT-156, REQ-ASY-158]
---
# T941 — E21.10 — Linux io_uring + epoll dual-engine reactor & IoOpState.CancellingZombie DMA safety

## Goal
Implement the Linux dual-engine asynchronous reactor combining high-throughput `io_uring` with runtime seccomp/container detection and seamless fallback to `epoll`, enforcing zero DMA write-after-free hazards on early future cancellation.

## Scope
- Implement `std/async/reactor/linux`:
  * Initialize `io_uring` with submission ring (SQ) and completion ring (CQ).
  * If `io_uring_setup` returns `EPERM` or `ENOSYS` (common in restricted Docker containers or hardened seccomp filters), transparently initialize the fallback `epoll` reactor (`epoll_create1(EPOLL_CLOEXEC)`, `epoll_ctl`, `epoll_pwait`).
  * Support async socket operations (`accept`, `connect`, `recv`, `send`) and file operations (`read`, `write`, `fsync`).
- Enforce strict kernel DMA write-after-free safety on future cancellation:
  * When an ongoing `recv` or `read` future is cancelled / dropped before completion, do NOT free or reuse the underlying buffer.
  * Move the operation into an internal `IoOpState.CancellingZombie` table retaining the buffer place until the kernel completes the CQE with `ECANCELED` or data bytes, preventing silent kernel memory scribbling.

## Acceptance
- [ ] Run tests in `tests/run/linux_reactors` verify async socket TCP echo and file reads under both `io_uring` and `epoll` fallback modes.
- [ ] Stress test dropping 10,000 async read futures mid-flight while receiving continuous network streams passes with 0 memory corruption, verified under ASan and Valgrind in WSL2 / Linux.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T941-report.md` with exact `## Files changed`.

## Out of scope
- Windows IOCP implementation (covered in `E11.6` / `E21.4`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T941/build` and `python tools/axtest.py --compiler build-snap-T941/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-09 23:30:00 created by axiom-architect (ADR-0039 P21 async reactors expansion)
