# E11.6 — Async File, Socket & Timer Conformance Suite (`tests/conformance/p11/e11_6_async_io`)

Governing specification: `spec/SPEC-35-async-io.md` (Phase 11, Epic E11.6, Task `T428`, `REQ-ASY-155`, `REQ-CONC-153`).
Implementation under test: `std/io/async_io.ax`, `std/fs/async_file.ax`, `std/net/mod.ax`, `std/async/{reactor,timer,cancel,group,executor}.ax`
(T426 IOCP reactor + timer wheel, T427 AsyncRead/AsyncWrite, AsyncFile, loopback AsyncTcp/Udp).

Seven tests are plain run tests that import the live std modules (`use std.asyn...`, `use std.net...`), so they exercise
exactly the code in `std/`. `taskgroup_async_io.ax` is a generated bundle (`gen_tests.py`, sources in `src/`, freshness
checked by `check_conformance_bundles.test`) because `TaskGroup.spawn` cannot be instantiated against the live
`std.asyn.group` module (see the T428 report, F3); like every TaskGroup test of the repository it inlines the whole
std closure it needs. Every test is `modes: interp native` (the runner adds `native-O1`), runs on the loopback interface
only, and compares an exact `stdout:` line, so the native IOCP leg is proven against the deterministic oracle by
observable output. A failed internal check returns a non-zero exit code (or prints `ERR ...`) instead of the expected
line. Files written by a test go to `build/` and are removed again.

| Test | Rules | What it proves |
|---|---|---|
| `file_pipeline_tasks.ax` | AXS-AIO-010..012, 031, 033 | Three-stage `AsyncFile` pipeline run as concurrent local tasks: four overlapped positional writers, four read-XOR-write transform tasks (chunk i -> chunk 3-i of a second file), sequential `read_exact` verification, EOF read returns 0 bytes, fallible `close().await`. |
| `tcp_multi_client_echo.ax` | AXS-AIO-030..032, 040/041 | One `AsyncTcpListener`, four simultaneous connections of different message lengths; an accept task spawns one echo task per connection; exact echo, half-close then EOF as a 0-byte read. |
| `tcp_framing_split.ax` | AXS-AIO-031, 043 | Length-prefixed frames (including an empty frame and a byte-at-a-time trickled frame) over `split()` halves with three tasks (writer, echo server owning both halves, reader); `UnexpectedEof` on the header read is the clean end of stream. |
| `udp_burst_exchange.ax` | AXS-AIO-050..052 | Burst of eight datagrams of distinct length from one `AsyncUdpSocket` to another, boundaries/lengths/content preserved, per-datagram acknowledgements to the sender address (order-insensitive checks). |
| `cancel_token_reads.ax` | AXS-AIO-005, REQ-ASY-157/158 | `CancellationToken` cancels in-flight TCP and UDP reads through a select-style `CancelRace`; a read on the already cancelled token is refused at once; reactor drains to 0 in-flight; data sent after the cancellation reaches fresh reads intact. |
| `timeout_reads_buffer_safety.ax` | AXS-AIO-005, 023 | `with_io_timeout_ms` cancels an IoBuf read, a slice read and a UDP `recv_from`; sentinel heap buffers and stack buffers stay untouched while the zombie ops unwind and data arrives; zombie accounting (`zombie_count == 0`, three reclaimed); a file read future dropped right after submission is memory safe and a re-read is exact. |
| `taskgroup_async_io.ax` | AXS-AIO-040..043 + SPEC-34 | `TaskGroup<i64>` on the `Executor`: echo server task + client task complete with exact values, a straggler blocked in a UDP `recv_from` is cancelled by `cancel_all` (one `Cancelled` child, destination buffer never written). |
| `timers_with_io.ax` | AXS-AIO-020..023 | Timer wheel and IOCP completions on one executor wake in deadline/completion order and never before their deadline; `Interval.every_ms` ticks; `with_io_timeout_ms` completing early leaves no timer behind. |

Requirement traceability: `REQ-ASY-155` and `REQ-CONC-153` are covered by every test (see `// covers:` in each file).

Timing margins: tests that compare wake order use gaps of at least 90 ms between the events and only lower-bound
elapsed times, so they stay deterministic on the shared development machine.

## Implementation limits the tests are written around (details and repros: `_workspaces/reports/T428-report.md`)

The suite avoids, and the report documents, these gaps found while writing it; each needs a fix task before the
corresponding construct can be covered directly:

- F1 raw pointers to locals of an `async fn` are not stable across `.await` (slice I/O and `read_exact`/`write_all`
  on an async-local stream break); tasks use `IoBuf` I/O or pointers into a stable frame owned by `main`.
- F2 the oracle listener has a single pending-accept slot and no backlog; connections arriving before an accept is
  posted are lost, so accepts are posted before the matching connect.
- F3 live `TaskGroup.spawn` fails `AX_CONC_CAPTURE_NOT_SEND` for every future (bundled std is fine).
- F4 reactor counters race between worker threads (oracle race detector), so the TaskGroup test uses one worker.
- F5 an operand that is `.await`ed inside an `async fn` is not dropped when the await completes.
- F6 the multi-worker `Executor` only turns the reactor when idle (yield loops starve I/O); F7 `SocketAddr` and
  `SleepFuture` are not `Send` for the native checker; F8 `std.asyn.timeout.Timeout` around pending I/O blocks forever
  natively under `LocalExecutor.block_on`.
