---
id: T427
title: E11.6 — Unified AsyncRead/AsyncWrite, AsyncFile & loopback AsyncTcp/Udp sockets
phase: P11-concurrency-async
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T426]
priority: 150
status: todo
attempts: 0
paths: [std/io/async_io.ax, std/fs/async_file.ax, std/net, tests/std/async/io, tests/selfhost]
locks: [std/io/io.ax, std/fs/fs.ax, std/sys/windows/iocp.ax]
spec: [spec/SPEC-35-async-io.md, 0221, tasks/0335, tasks/0438, tasks/0441, tasks/0461]
covers: [REQ-ASY-152, REQ-CONC-152, REQ-ASY-157]
---
# T427 — E11.6 — Unified AsyncRead/AsyncWrite, AsyncFile & loopback AsyncTcp/Udp sockets

## Goal
Implement `AsyncRead`/`AsyncWrite`, `AsyncFile`, and `std.net` (`AsyncTcpListener`, `AsyncTcpStream` with `split()`, `AsyncUdpSocket`) on top of the unified reactor.

## Scope
- Implement `std/io/async_io.ax` (`IoBuf`, `AsyncRead`, `AsyncWrite`, `read_exact`, `write_all`, completion-safe buffer hand-off).
- Implement `std/fs/async_file.ax` (`AsyncFile::open`, `create`, `read_at`, `write_at`, `flush`, explicit fallible `close().await` distinct from `Drop`).
- Implement `std/net/mod.ax` (`SocketAddr`, `Ipv4Addr`, `AsyncTcpListener`, `AsyncTcpStream`, `AsyncUdpSocket`) backed by Winsock2 (`WSASocketW`, `AcceptEx`/`ConnectEx`/`WSARecv`/`WSASend` on IOCP) natively and deterministic loopback channels in the oracle.
- Provide `stream.split() -> (TcpReadHalf, TcpWriteHalf)` so a single socket can be read and written concurrently by two tasks without permitting unsynchronized concurrent mutation of the unsplit socket (`REQ-CONC-152`).

## Acceptance
- [ ] `tests/std/async/io/*.ax` (`modes: interp native`) tests concurrent `AsyncFile` overlapped reads and writes, loopback `AsyncTcpListener`/`AsyncTcpStream` request/response, concurrent full-duplex I/O via `stream.split()`, `AsyncUdpSocket` datagram send/recv, and explicit cancellation/timeout of blocked socket reads.
- [ ] Full test suite passes in `build-snap-T427` under `axiomc2.exe` (`WEAK-NATIVE 0`); `archcheck.py` clean.
- [ ] Report `_workspaces/reports/T427-report.md` with exact `## Files changed`.

## Out of scope
- DNS resolver, TLS/HTTPS, and HTTP protocols (Phase 21 `E21.4`).

## Notes
- Phase P11 (`P11-concurrency-async`). `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` (within the `SPEC-00 §9` self-host subset so `axiom0` builds Stage 1) and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T427/build` and `python tools/axtest.py --compiler build-snap-T427/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 00:10:00 created by T211 (P11 phase planning)
