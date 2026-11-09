---
id: T947
title: E21.11 — Hardened HTTPS/H2 server, DoS guards, streaming Multipart & SSE/WebSocket
phase: P21-standard-library-completion
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T946, T914, T574]
priority: 259
status: todo
attempts: 0
paths: [std/web/server, tests/conformance/p21/e21_11_web_framework]
spec: [spec/SPEC-152-web-framework-openapi-extractors.md, spec/decisions/ADR-0039-p12-p22-systems-web-zeroday-opengl-expansion.md]
covers: [REQ-STD-171, REQ-STD-177]
---
# T947 — E21.11 — Hardened HTTPS/H2 server, DoS guards, streaming Multipart & SSE/WebSocket

## Goal
Implement the production-hardened `std.web.Server` runtime supporting HTTPS and HTTP/2, DoS mitigations, path-traversal proof `StaticDir`, streaming multipart forms, real-time SSE/WebSocket, and certify E21.11 exit criteria with an end-to-end conformance suite.

## Scope
- Implement `std/web/server`:
  * TLS 1.3 and ALPN negotiation for HTTP/1.1 and HTTP/2 protocols using `std.net.tls` (`T914`).
  * Enforce DoS mitigations: configurable read timeouts rejecting Slowloris attacks, strict `max_body_bytes` limit (default 2 MiB, per-route configurable) aborting payloads with HTTP 413, and HTTP/2 Rapid Reset stream limits.
- Implement path-traversal resistant static file hosting in `std.web.StaticDir`:
  * Strictly canonicalize path prefixes, rejecting directory traversal (`..`), embedded null bytes (`\0`), Windows 8.3 short name aliases (`FILE~1.TXT`), NTFS alternate data streams (`::$DATA`), and reserved DOS device names (`CON`, `PRN`, `AUX`, `NUL`).
- Implement streaming request/response handlers:
  * `Multipart`: stream large file uploads directly to temporary files without buffering whole bodies in memory.
  * `SseStream`: stream Server-Sent Events using async generator streams (`T574`).
  * `WebSocketUpgrade`: upgrade HTTP connections to full-duplex WebSocket channels (RFC 6455) using constant-time `Base64` (`T948`) and quarantined `Sha1` (`T949`).
- Create comprehensive conformance suite in `tests/conformance/p21/e21_11_web_framework` running loopback fuzzing against live HTTP server instances.

## Acceptance
- [ ] All conformance tests in `tests/conformance/p21/e21_11_web_framework` pass in both `--interp` and native modes (`0 WEAK-NATIVE`).
- [ ] Slowloris and payload-bomb stress tests verify that server connections are terminated cleanly without unbounded memory growth.
- [ ] Static file traversal tests verify that attempts to access parent directories, NTFS `::$DATA` streams, or forbidden aliases return HTTP 404/403.
- [ ] WebSocket and SSE streaming tests verify bidirectional communication and clean cancellation.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T947-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T947/build` and `python tools/axtest.py --compiler build-snap-T947/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`).

## Log
- 2026-11-09 23:35:00 created by axiom-architect (ADR-0039 P21 std.web expansion)
