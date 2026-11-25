---
id: T428c
title: Fix — oracle TCP listener has no backlog (single pending-accept slot): concurrent connects hang in interp, pass natively
phase: P11-concurrency-async
owner: axiom-semantics
reviewer: axiom-qa
model: sonnet
gate_model: sonnet
depends: []
priority: 30
status: todo
attempts: 0
paths: [tests/std/net/oracle_listener_backlog, tests/conformance/p11/e11_6_async_io/tcp_concurrent_connects.ax]
locks: [compiler/interp/oracle.ax, tests/conformance/p11/e11_6_async_io/tcp_multi_client_echo.ax]
spec: [spec/SPEC-35-async-io.md, spec/SPEC-33-async.md]
covers: [REQ-ASY-155, REQ-ASY-151]
---
# T428c — Oracle TCP listener backlog and accept queue

## Why
T428 report F2: `compiler/interp/oracle.ax` keeps one `pending_accept_op` slot per listener. `aio_submit_connect`
(~line 3215) completes only if an accept is pending at that moment, otherwise the server side of the connection is
dropped; `aio_submit_accept` (~line 3162) overwrites the slot. Natively, `listen(sock, 128)` (`std/sys/windows/iocp.ax`)
lets the kernel queue established connections, and several `AcceptEx` can be outstanding. Two concurrent
`AsyncTcpStream.connect` tasks against an accept loop that re-posts `accept()` after the first connection therefore hang
in `--interp` and pass natively: an interp/native divergence of the semantic oracle.

## Rule (architect, triage 2026-11-25)
The oracle models the native contract, not a stricter one: per listener a FIFO of established-but-unaccepted connections
bounded by the backlog the std passes to `listen` (128; beyond it a connect fails with the same `IoError` kind the native
path reports for a refused connection), and a FIFO of outstanding accept ops. A connect pairs with the oldest outstanding
accept, else is queued; an accept takes the oldest queued connection, else is queued. Cancelling an accept op removes only
that op; closing the listener fails every queued accept op and drops the queued connections (their client sides see
EOF/reset as natively).

## Scope
1. Implement the rule in `compiler/interp/oracle.ax` (`aio_submit_accept`, `aio_submit_connect`, accept cancellation at
   ~2908, listener close at ~3402). Deterministic: queue order is submission order.
2. Regression tests `tests/std/net/oracle_listener_backlog/` (`modes: interp native`, exact `// stdout:`): 4 connects
   completing before any accept is posted, then 4 accepts (FIFO pairing checked by a byte each client sends); 2 accepts
   posted before 3 connects; accept cancelled with queued connections still acceptable later; listener closed with queued
   connections and pending accepts (client sees EOF, accept reports an error, no hang). Each ordering-dependent case must
   hang/fail in `--interp` on HEAD (use a `// timeout:` so HEAD fails, not hangs the run).
3. Direct form in the E11.6 suite: new `tests/conformance/p11/e11_6_async_io/tcp_concurrent_connects.ax` (truly
   concurrent connects, no gate), and remove the `gate` handshake workaround ("follow-up F2") from
   `tcp_multi_client_echo.ax`, keeping its `stdout:`. Do not edit the suite `README.md` (T311 updates it).

## Acceptance
- [ ] New tests pass in interp, native and native-O1 with `WEAK-NATIVE 0`; the interp leg fails (timeout) on HEAD.
- [ ] `tests/std/async/**`, `tests/std/net/**`, `tests/conformance/p11/**`, `tests/run/async/**` pass.
- [ ] Normal gate including the selfhost groups of `compiler/interp`. Report `_workspaces/reports/T428c-report.md` with an
      exact `## Files changed`.

## Log
- 2026-11-25 created by architect (triage after T428 accept, `_workspaces/reports/triage-2026-11-25-T428.md`)
