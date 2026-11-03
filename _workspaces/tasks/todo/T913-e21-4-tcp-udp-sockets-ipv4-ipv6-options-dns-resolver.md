---
id: T913
title: E21.4 Blocking & async TCP/UDP sockets, IPv4/IPv6 addressing, socket options & DNS resolver
phase: P21-standard-library-completion
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T221, T311, T313, T912]
priority: 223
status: todo
attempts: 0
paths: [std/net/addr, std/net/socket, std/net/dns, tests/run/std_net_socket_dns]
spec: [spec/SPEC-123-networking-sockets-dns-http.md, tasks/0461, tasks/0335, tasks/0838]
covers: [REQ-STD-171, REQ-RT-154, REQ-RT-155, REQ-RT-156, REQ-RT-157, REQ-RT-173, REQ-RT-541, REQ-RT-542, REQ-RT-543, REQ-RT-544, REQ-RT-545, REQ-RT-546, REQ-RT-547, REQ-RT-548, REQ-RT-549, REQ-RT-550, REQ-RT-551, REQ-RT-552, REQ-RT-553, REQ-RT-554, REQ-RT-555, REQ-RT-556, REQ-RT-557, REQ-RT-558, REQ-RT-559, REQ-RT-560]
---
# T913 — E21.4 Blocking & async TCP/UDP sockets, IPv4/IPv6 addressing, socket options & DNS resolver

## Goal
Implement IPv4/IPv6 address parsing/formatting, blocking and reactor-integrated TCP/UDP sockets with full socket options, and the DNS resolver in `std.net` per `spec/SPEC-123-networking-sockets-dns-http.md`.

## Scope
- Implement `std/net/addr` (`Ipv4Addr`, `Ipv6Addr`, `IpAddr`, `SocketAddrV4`, `SocketAddrV6`, `SocketAddr`, CIDR subnet matching, and canonical RFC 5952 IPv6 formatting/parsing).
- Implement `std/net/socket` (`TcpListener`, `TcpStream`, `UdpSocket`, `Shutdown`, `SocketOpts` for `nodelay`, `reuse_addr`, `recv_buffer_size`, `send_buffer_size`, `read_timeout`, `write_timeout`, `ttl`, and multicast join/leave, bridging seamlessly with `E11.6` async reactor sockets; `REQ-STD-171`, `REQ-RT-154`..`REQ-RT-157`).
- Implement `std/net/dns` (`lookup_host`, `lookup_addr`, DNS wire packet parser/encoder for A/AAAA/CNAME/TXT records, OS `GetAddrInfoW`/`getaddrinfo` bridge, and deterministic oracle resolver; `tasks/0838 §5-8`).
- Add run tests in `tests/run/std_net_socket_dns`.

## Acceptance
- [ ] Run tests in `tests/run/std_net_socket_dns` verify IPv4/IPv6 CIDR & RFC 5952 parsing, loopback TCP/UDP blocking and async exchanges, socket timeout/shutdown semantics, `Drop` handle closure, and DNS wire/host resolution in `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T913-report.md` with exact `## Files changed`.

## Out of scope
- TLS stream framing, HTTP client/server, and RPC gateway (`T914`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T913/build` and `python tools/axtest.py --compiler build-snap-T913/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:35:00 created by T221 (P21 phase planning)
