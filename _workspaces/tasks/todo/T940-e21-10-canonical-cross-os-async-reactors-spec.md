---
id: T940
title: E21.10 — Canonical specification for cross-OS native async reactors (SPEC-129)
phase: P21-standard-library-completion
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T221, T311, T316]
priority: 252
status: todo
attempts: 0
paths: [spec/SPEC-129-cross-os-async-reactors.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [spec/SPEC-129-cross-os-async-reactors.md, spec/decisions/ADR-0039-p12-p22-systems-web-zeroday-opengl-expansion.md]
covers: [REQ-RT-156, REQ-ASY-158]
---
# T940 — E21.10 — Canonical specification for cross-OS native async reactors (SPEC-129)

## Goal
Consolidate the canonical specification for native, cross-platform asynchronous I/O reactors (Linux `io_uring` + `epoll`, macOS/iOS `kqueue`, Windows `IOCP`) into `spec/SPEC-129-cross-os-async-reactors.md` (`AXS-REAC-*` rule IDs).

## Scope
- Write `spec/SPEC-129-cross-os-async-reactors.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-REAC-NNN` rules.
- Specify the unified asynchronous reactor trait contract `AsyncReactor` providing non-blocking socket poll, timer registration, and completion dispatch.
- Specify Linux dual-engine reactor architecture:
  * Primary `io_uring` engine utilizing submission (SQ) and completion (CQ) rings with kernel submission offload (`IORING_SETUP_SQPOLL`).
  * Runtime probe for `io_uring_setup`; automatic graceful fallback to edge-triggered `epoll` (`EPOLLET`) in sandboxed container, Docker, or seccomp-restricted environments.
  * Invariant for premature future cancellation: when an async I/O future is dropped mid-flight, transition buffer ownership to an internal `IoOpState.CancellingZombie` state. The physical memory buffer remains pinned until kernel CQE completion is dequeued, completely preventing kernel DMA write-after-free corruption.
- Specify Darwin `kqueue` / `kevent64` reactor architecture for macOS and iOS:
  * Edge-triggered `EV_CLEAR` filter registration for read/write events.
  * `EVFILT_TIMER` fine-grained nanosecond timers without timer threads.
- Specify Windows IOCP integration interoperability with the unified reactor model.
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-129-cross-os-async-reactors.md` exists with Vietnamese `## Tóm tắt`, numbered `AXS-REAC-NNN` rules, positive/negative examples, and DMA cancellation safety proofs.
- [ ] `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T940-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of the OS reactors (`T941`–`T943`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T940/build` and `python tools/axtest.py --compiler build-snap-T940/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-09 23:30:00 created by axiom-architect (ADR-0039 P21 async reactors expansion)
