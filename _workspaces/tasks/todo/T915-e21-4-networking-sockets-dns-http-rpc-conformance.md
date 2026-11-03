---
id: T915
title: E21.4 Networking sockets, DNS, async IO, TLS boundary & HTTP/RPC conformance suite
phase: P21-standard-library-completion
owner: axiom-qa
reviewer: axiom-architect
model: sonnet
gate_model: sonnet
depends: [T221, T311, T313, T914]
priority: 225
status: todo
attempts: 0
paths: [tests/conformance/p21/e21_4_networking]
spec: [spec/SPEC-123-networking-sockets-dns-http.md, tasks/0461, tasks/0335, tasks/0838, tasks/0859]
covers: [REQ-STD-171, REQ-STD-177, REQ-RT-154, REQ-RT-155, REQ-RT-156, REQ-RT-157, REQ-RT-173, REQ-RT-175, REQ-RT-576, REQ-RT-577, REQ-RT-578, REQ-RT-579, REQ-RT-580, REQ-RT-581, REQ-RT-582, REQ-RT-583, REQ-RT-584, REQ-RT-585]
---
# T915 — E21.4 Networking sockets, DNS, async IO, TLS boundary & HTTP/RPC conformance suite

## Goal
Certify E21.4 exit criteria with an end-to-end networking conformance suite covering IPv4/IPv6 addressing, blocking/async TCP and UDP sockets, DNS resolution, TLS framing, HTTP client/server, and RPC service gateways.

## Scope
- Create conformance tests in `tests/conformance/p21/e21_4_networking` verifying move-only socket ownership (`REQ-RT-154`), raw byte payload discipline (`REQ-RT-155`), portable reactor integration (`REQ-RT-156`), and stream framing (`REQ-RT-157`).
- Verify DNS wire packet decoding/encoding, loopback HTTP/1.1 request/response pipelines, TLS session boundary enforcement (`REQ-STD-171`), and typed RPC call multiplexing/timeout propagation (`REQ-STD-177`, `REQ-RT-173`, `REQ-RT-175`).
- Verify differential agreement between `--interp` and native execution (`0 WEAK-NATIVE`).

## Acceptance
- [ ] All conformance tests in `tests/conformance/p21/e21_4_networking` pass in `--interp` and native modes with `0 WEAK-NATIVE`.
- [ ] Full test suite passes in the snapshot (`axiomc2.exe`); `reqcov.py --strict` and `harness_check.py` exit 0.
- [ ] Report `_workspaces/reports/T915-report.md` with exact `## Files changed`.

## Out of scope
- Unrelated epics; editing `docs/` or `bootstrap/axiom0/` (frozen at `axiom0-frozen`).

## Notes
- Phase P21 (`P21-standard-library-completion`), depends on P11 gate `T311` and P13 gate `T313` (`ROADMAP.md` §2–§3).
- `bootstrap/axiom0` is frozen at tag `axiom0-frozen` (ROADMAP R3); all compiler and library changes live in `compiler/` and `std/`.
- Build and test inside the task snapshot (`python tools/build_axiomc.py --out build-snap-T915/build` and `python tools/axtest.py --compiler build-snap-T915/build/axiomc2.exe --exclude-requires axiom0-internal`).
- All Axiom source code and examples use canonical syntax (`axiom-syntax`): `=` for binding/assignment (no `:=`, no `var`), `.` for module/type paths (no `::`).

## Log
- 2026-11-03 10:35:00 created by T221 (P21 phase planning)
