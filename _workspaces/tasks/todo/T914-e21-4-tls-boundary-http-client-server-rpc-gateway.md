---
id: T914
title: E21.4 TLS transport boundary, HTTP client/server framing & typed RPC service gateway
phase: P21-standard-library-completion
owner: axiom-stdlib
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: [T221, T311, T313, T912, T913, T938, T948, T949]
priority: 224
status: todo
attempts: 0
paths: [std/net/tls, std/net/http, std/net/rpc, tests/run/std_net_http_rpc]
spec: [spec/SPEC-123-networking-sockets-dns-http.md, tasks/0461, tasks/0838, tasks/0859]
covers: [REQ-STD-171, REQ-STD-177, REQ-RT-173, REQ-RT-175, REQ-RT-561, REQ-RT-562, REQ-RT-563, REQ-RT-564, REQ-RT-565, REQ-RT-566, REQ-RT-567, REQ-RT-568, REQ-RT-569, REQ-RT-570, REQ-RT-571, REQ-RT-572, REQ-RT-573, REQ-RT-574, REQ-RT-575]
---
# T914 — E21.4 TLS transport boundary, HTTP client/server framing & typed RPC service gateway

## Goal
Implement the `std.net.tls` transport boundary, `std.net.http` client/server protocol engine, and `std.net.rpc` typed framing/gateway runtime per `spec/SPEC-123-networking-sockets-dns-http.md`.

## Scope
- Implement `std/net/tls` (`TlsConfig`, `RootCertStore`, `ServerName`, `ClientSession`, `ServerSession`, `TlsStream<S>` with explicit ALPN, strict RFC 5280 DER X.509 certificate verification hooks, OS system root trust store loading, and hardened pure-Axiom TLS 1.3 protocol engine powered by `T938` AES-GCM/ECDSA/RSA-PSS; `tasks/0838 §9-12`, `REQ-STD-171`).
- Implement `std/net/http` (`Method`, `StatusCode`, `HeaderMap`, `Uri`, HTTP/1.1 and HTTP/2 framing with Rapid Reset CVE-2023-44487 / CONTINUATION flood limits, request/response parser and serializer, `Content-Length` and chunked transfer coding, connection keep-alive pool, and loopback `HttpClient`/`HttpServer`; `tasks/0859 §3-9`, `REQ-STD-177`).
- Implement WebSocket RFC 6455 framing and handshake key derivation using `std.encoding.base64` (`T948`) and `std.crypto.legacy.Sha1` (`T949`).
- Implement `std/net/rpc` (`RpcFrame`, length-delimited multiplexed request/response correlation, per-call deadline propagation, backpressure limits, and `ServiceGateway` router without remote pointers or hidden GC; `tasks/0461 §19-30`, `tasks/0859 §10-15`, `REQ-RT-173`, `REQ-RT-175`).
- Add run tests in `tests/run/std_net_http_rpc`.

## Acceptance
- [ ] Run tests in `tests/run/std_net_http_rpc` verify TLS record framing and certificate verification policy, HTTP/1.1 chunked and keep-alive client/server round-trips, and multiplexed RPC deadline/cancellation handling in `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`).
- [ ] Report `_workspaces/reports/T914-report.md` with exact `## Files changed`.

## Out of scope
- Distributed consensus and cluster runtimes (`P24 E24.7`).
- Editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T914/build` and `python tools/axtest.py --compiler build-snap-T914/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:35:00 created by T221 (P21 phase planning)
