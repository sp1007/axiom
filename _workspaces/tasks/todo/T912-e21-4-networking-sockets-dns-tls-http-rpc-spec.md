---
id: T912
title: E21.4 Canonical networking, sockets, DNS, TLS boundary & HTTP/RPC transport specification (SPEC-123)
phase: P21-standard-library-completion
owner: axiom-architect
reviewer: axiom-qa
model: opus
gate_model: sonnet
depends: [T221, T311, T313]
priority: 222
status: todo
attempts: 0
paths: [spec/SPEC-123-networking-sockets-dns-http.md]
locks: [spec/INDEX.md, spec/diagnostics.md, spec/invariants.md]
spec: [tasks/0461, tasks/0335, tasks/0838, tasks/0859]
covers: [REQ-STD-171, REQ-STD-177, REQ-RT-154, REQ-RT-155, REQ-RT-156, REQ-RT-157, REQ-RT-173, REQ-RT-175, REQ-RT-523, REQ-RT-524, REQ-RT-525, REQ-RT-526, REQ-RT-527, REQ-RT-528, REQ-RT-529, REQ-RT-530, REQ-RT-531, REQ-RT-532, REQ-RT-533, REQ-RT-534, REQ-RT-535, REQ-RT-536, REQ-RT-537, REQ-RT-538, REQ-RT-539, REQ-RT-540]
---
# T912 — E21.4 Canonical networking, sockets, DNS, TLS boundary & HTTP/RPC transport specification (SPEC-123)

## Goal
Consolidate the canonical specification for Axiom's networking stack—IPv4/IPv6 addressing, blocking/async TCP and UDP sockets, DNS resolution, TLS transport boundary, HTTP/1.1 framing, and typed RPC/service gateway abstractions—into `spec/SPEC-123-networking-sockets-dns-http.md` (`AXS-NET-*` rule IDs).

## Scope
- Write `spec/SPEC-123-networking-sockets-dns-http.md` starting with a Vietnamese `## Tóm tắt` section and numbered `AXS-NET-NNN` rules.
- Specify move-only socket resource ownership (`TcpListener`, `TcpStream`, `UdpSocket`, `SocketAddr`, `IpAddr`, `Ipv4Addr`, `Ipv6Addr`; `tasks/0335 §10-18`, `tasks/0461 §3-18`, `tasks/0838 §1-12`, `REQ-STD-171`, `REQ-RT-154`..`REQ-RT-157`), enforcing raw byte buffer payloads (`view<u8>` / `mut_view<u8>`), explicit deadlines/timeouts, and portable mapping onto IOCP (Windows) and epoll/`io_uring` (Linux).
- Specify synchronous and asynchronous DNS name resolution (`Resolver`, `LookupHost`, `/etc/hosts` and system resolver integration, deterministic mock DNS in the oracle; `tasks/0838 §5-8`).
- Specify the explicit TLS transport boundary (`TlsConfig`, `CertStore`, `ServerName`, `TlsStream<S>` wrapping any `Read + Write` / `AsyncRead + AsyncWrite` stream), HTTP client/server message framing (`Request`, `Response`, `Headers`, chunked transfer, keep-alive pools), and typed RPC/service gateway contracts without implicit remote pointers or distributed GC (`tasks/0461 §19-30`, `tasks/0859 §1-15`, `REQ-STD-177`, `REQ-RT-173`, `REQ-RT-175`).
- Update `spec/INDEX.md`, `spec/diagnostics.md`, and `spec/invariants.md`.

## Acceptance
- [ ] `spec/SPEC-123-networking-sockets-dns-http.md` exists with a Vietnamese `## Tóm tắt`, numbered `AXS-NET-NNN` rules, positive/negative canonical Axiom examples (`=` and `.` syntax), and source citations.
- [ ] `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict` and `python .claude/skills/axiom-tasks/scripts/harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T912-report.md` with exact `## Files changed`.

## Out of scope
- Implementation of sockets, DNS, TLS, HTTP, and RPC modules (`T913`–`T914`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T912/build` and `python tools/axtest.py --compiler build-snap-T912/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:35:00 created by T221 (P21 phase planning)
