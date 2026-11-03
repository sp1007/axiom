---
id: T425
title: E11.6 — Canonical unified async I/O & reactor specification (SPEC-35)
phase: P11-concurrency-async
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T420]
priority: 148
status: done
attempts: 1
paths: [spec/SPEC-35-async-io.md]
locks: [spec/INDEX.md, spec/SPEC-04-core-extensibility.md]
spec: [0221, tasks/0335, tasks/0438, tasks/0440, tasks/0441, tasks/0461, tasks/0464]
covers: [REQ-ASY-035, REQ-ASY-151]
started: 2026-11-03 08:26:19
finished: 2026-11-03 08:40:22
---
# T425 — E11.6 — Canonical unified async I/O & reactor specification (SPEC-35)

## Goal
Write canonical `spec/SPEC-35-async-io.md` (`AXS-AIO-*` rule IDs) defining the unified async I/O model, completion-safe buffer ownership, Windows IOCP / Linux epoll & io_uring reactor contract, timer wheel, `AsyncFile`, and `AsyncTcp`/`AsyncUdp` sockets.

## Scope
- Write `spec/SPEC-35-async-io.md` with a Vietnamese `## Tóm tắt` section and numbered `AXS-AIO-NNN` rules.
- Define the unified Proactor/Reactor abstraction (`0221`, `tasks/0438`, `tasks/0461`) bridging Windows IOCP (`CreateIoCompletionPort`, `OVERLAPPED`, `CancelIoEx`) and Linux `io_uring`/`epoll` behind a target-independent completion/readiness reactor contract.
- Specify completion-safe buffer ownership (`REQ-ASY-152, 157`): an in-flight I/O operation retains ownership (or pinned reactor storage) of the I/O buffer until OS completion occurs, so dropping an I/O `Future` early initiates `CancelIoEx` / cancellation without freeing or reusing the buffer while the kernel still writes to it.
- Specify `AsyncRead`, `AsyncWrite`, `AsyncFile`, `AsyncTcpListener`, `AsyncTcpStream` (including `split()` into concurrent `ReadHalf` + `WriteHalf` capabilities, `REQ-CONC-152`), `AsyncUdpSocket`, reactor timer wheel (`sleep`, `Interval`, `Deadline` integration without OS thread per timer, `REQ-ASY-154`), and host intrinsics (`host.aio_*`) in `spec/SPEC-04-core-extensibility.md §11`.
- Update `spec/INDEX.md`.

## Acceptance
- [ ] `spec/SPEC-35-async-io.md` exists with a Vietnamese `## Tóm tắt`, `AXS-AIO-NNN` rule IDs, buffer-lifecycle state diagram, and host intrinsic signatures.
- [ ] `spec/SPEC-04-core-extensibility.md` and `spec/INDEX.md` are updated.
- [ ] `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T425-report.md` with exact `## Files changed`.

## Out of scope
- Implementing reactor, file, or socket code (handled by `T426`–`T427`).

## Notes
- Phase P11 (`P11-concurrency-async`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T425/build` and `python tools/axtest.py --compiler build-snap-T425/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:10:00 created by T211 (P11 phase planning)
- 2026-11-03 08:26:19 started (attempt 1) T425-impl
- 2026-11-03 08:40:22 accepted by QA -> done
