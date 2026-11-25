# T428 Report — E11.6 Async file, socket & timer conformance suite

## Summary
Added `tests/conformance/p11/e11_6_async_io/` with eight run tests (all `modes: interp native`, the runner adds `native-O1`;
every test compares an exact `stdout:` line) plus a README, a bundle generator and a freshness check:

| Test | Covers |
|---|---|
| `file_pipeline_tasks.ax` | 3-stage `AsyncFile` pipeline, 4 concurrent positional writers, 4 read-XOR-write tasks, `read_exact`, EOF read, `close().await` |
| `tcp_multi_client_echo.ax` | 4 concurrent connections on one `AsyncTcpListener`, accept task spawning per-connection echo tasks, half-close/EOF |
| `tcp_framing_split.ax` | length-prefixed framing (empty frame, byte-trickled frame) over `split()` halves, 3 tasks, `UnexpectedEof` end of stream |
| `udp_burst_exchange.ax` | 8-datagram burst, boundaries/lengths/content, per-datagram acks to the sender address |
| `cancel_token_reads.ax` | `CancellationToken` cancelling in-flight TCP/UDP reads (select-style `CancelRace`), already-cancelled token, zombie drain, late data intact |
| `timeout_reads_buffer_safety.ax` | `with_io_timeout_ms` cancelling IoBuf/slice/UDP reads, sentinel heap + stack buffers untouched, zombie accounting, dropped file-read future |
| `taskgroup_async_io.ax` (bundle) | `TaskGroup` + async I/O on `Executor`, `cancel_all` cancelling a blocked UDP `recv_from` |
| `timers_with_io.ax` | timer wheel + IOCP ordering, `Interval`, no leaked timer after an early I/O completion |

## Verification (in build-snap-T428, axiomc2.exe, HEAD 2b7e509 + the task's files)
- `python tools/axtest.py --compiler build/axiomc2.exe --exclude-requires axiom0-internal -j 2 conformance/p11/e11_6_async_io`:
  `TOTAL 25 PASS 25 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0` (8 tests x interp/native/native-O1 + the bundle freshness test).
- Native-evidence mutation proof: in the snapshot only, `udp_burst_exchange.ax` expectation `8 36 8 1` changed to `8 37 8 1`
  -> `FAIL ... [interp]`, `[native]`, `[native-O1]` (stdout differs at byte 25); restored and diffed identical to the main tree.
- `python tools/taskgate.py --task T428 ...` (inside the snapshot): exit 0, archcheck clean (238 files, 0 violations), failing ids none,
  `TOTAL 80 PASS 80`, `WEAK-NATIVE 0` in the task's own tests (3 elsewhere in the smoke draw, not the task's).
- `reqcov.py --strict`: `gaps: 0 COVERAGE OK`; `harness_check.py`: `HARNESS OK`.
- Time-based tests (`timers_with_io`, token/timeout cancel tests) use gaps of >= 90 ms between ordered events and only lower-bound elapsed times.
- Tests that read files outside their directory: `check_conformance_bundles.test` declares `nocache:`; the run tests only read std through the compiler (dependency-tracked).

## Findings (implementation gaps found while writing the suite; the tests are written around them, none is patched here)
These are real defects/gaps in std or the compiler (out of scope for this task: "Modifying compiler or std source files").
The architect should file fix tasks; once fixed the suite can be extended with the direct forms. Minimal repros are
reproducible with the snapshot compiler (`axiomc2.exe run --interp --std-root std <file>` and `build` for native).

- **F1 (high) — address of an `async fn` local is not stable across `.await`** (contradicts AXS-AIO-012 item 2, which allows `read(dst_ptr)` into "a local buffer owned by the async fn"; SPEC-33 §54 says frames are relocatable).
  Repro: `async fn rx(b: *const AsyncUdpSocket) -> i64 { let mut buf: [16]u8 = [0u8; 16]; let n = match unsafe { view(*b).recv_from(address_of_mut(buf[0]), 16usize).await } { Result.Ok(p) => p.0, Result.Err(_) => return -1i64 }; (n as i64) * 1000i64 + (buf[0] as i64) }`
  spawned with `LocalExecutor.spawn_local` and fed one datagram "TIM": oracle -> `AX_UNSAFE_INTERP_UB use of dangling pointer` at `std/net/mod.ax:799` (ptr_copy into the stale destination); native -> prints `3000` instead of `3084` (copy lands in a stale copy of the local).
  Same root cause for `mut_view(local_stream).read_exact(..)/write_all(..).await` inside an async fn: `ReadExactFuture` keeps a pointer to the local stream -> oracle UB at `std/io/async_io.ax:723`.
  Workaround in the suite: tasks use `IoBuf` I/O or pointers into a stable frame owned by `main`.
- **F2 (high) — oracle TCP listener has no backlog** (`compiler/interp/oracle.ax` `aio_submit_connect` ~3169: single `pending_accept_op` slot per listener, the server-side stream of a connect that arrives with no pending accept is dropped; `aio_submit_accept` ~3151 just overwrites the slot). A later `accept()` never completes -> hang in the interp only (native IOCP queues in the kernel backlog) -> interp/native divergence.
  Repro: two concurrent `AsyncTcpStream.connect` tasks against a listener whose accept loop re-posts `accept()` after serving the first connection (`tcp_multi_client_echo` without the `gate`): interp hangs, native passes.
  Workaround: `gate` handshake / sequential connects so that an accept is always pending at connect time.
- **F3 (high) — `TaskGroup.spawn` cannot be instantiated against live `std.asyn.group`**: any future (async fn or hand-written `unsafe impl Send`) gives `AX_CONC_CAPTURE_NOT_SEND` at `std/async/group.ax:285` (`exec.spawn(fut)`). Repro: `async fn five(a: i64) -> i64 { a }` + `let mut group: TaskGroup<i64> = TaskGroup.new(); let _ = group.spawn(view(exec), five(5i64));` in a program that `use std.asyn.group.TaskGroup` with `--std-root std`. `Executor.spawn(five())` directly is fine. All existing TaskGroup tests are bundles, which hides it; `taskgroup_async_io` is a bundle for the same reason (gen_tests.py inlines the std closure).
- **F4 (medium) — reactor counters are unsynchronized across worker threads**: with `Executor.new(2)` and socket I/O the oracle's race detector reports `AX_UNSAFE_INTERP_UB unsynchronized data race` on `Reactor.in_flight_count` (`std/async/reactor.ax` `register_op`/`turn` write under the lock; `has_pending_work`/`in_flight_count()` read without it, from the executor idle loop). The TaskGroup test therefore uses one worker and `main` never touches the reactor while the group runs.
- **F5 (high) — an operand that is `.await`ed inside an `async fn` is not dropped when the await completes**. Repro (`dropawait`): `struct D { counter: *mut i64 }` with `impl Future` (Ready(7)) and `impl Drop` (increments `*counter`); `block_on(D{..})` increments once, `async fn t(c) -> i64 { let v = D{counter: c}.await; v }` via `spawn_local` leaves the counter unchanged. Consequence: an I/O future that completes through an adapter (`CancelRace`) inside a task never runs its `Drop`, so the in-flight op is not cancelled (no zombie, `in_flight_count` stays 1). Workaround: the race futures are driven by `block_on` in `main` (cancel tasks run as ordinary tasks).
- **F6 (medium) — `Executor` worker loop turns the reactor only when no task is runnable** (`std/async/executor.ax` ~620), so tasks that wait with `yield_now` loops starve I/O completions (`LocalExecutor` polls every 32 ticks and does not have this problem).
- **F7 (low) — native checker `AX_ASYNC_FUTURE_NOT_SEND`** rejects futures holding a `SocketAddr` or a `SleepFuture` across `.await` ("explicit negative impl for `SocketAddr` is not `Send`", "field `wheel` is not `Send`"); the oracle path does not report it (interp/native divergence of the Send check). Workaround: tasks receive the port and build the `SocketAddr` at the call; no sleeps inside `Executor` tasks.
- **F8 (medium) — `std.asyn.timeout.Timeout` around a pending I/O future blocks forever natively under `LocalExecutor.block_on`**: its self-wake (`wake_by_ref`) is a no-op for block_on's null waker and no timer is registered, so `turn(None)` waits forever (the oracle returns immediately). The suite uses the I/O timeout adapter `with_io_timeout_ms` (timer-wheel based, AXS-AIO-023), which works in both modes.
- Pre-existing (unchanged, not caused by this task): the `check_*_bundles` freshness tests under `tests/std/async/*` and `tests/conformance/p11/e11_5_executors` lag the live std (stale bundles); `_workspaces/baseline-failures.txt` covers them.

## Design decisions
- Plain live-std run tests wherever possible (no bundles to go stale); only the TaskGroup test is bundled, with an explicit freshness check.
- All tests are written to the owned-buffer / stable-pointer subset (F1) and report observable results through `stdout:`; failing internal checks return a non-zero exit code or print `ERR ...`.
- No `xfail`: none of F1-F8 has an open architect-filed fix task yet, so none is encoded as xfail; the workaround forms keep the suite green and strict (the native leg checks exact output).

## Follow-ups (for axiom-architect)
File fix tasks for F1 (priority), F2, F3, F5, then F4, F6, F7, F8; each task adds the direct (currently avoided) form of the test as a regression (slice I/O in async tasks, concurrent connects, live `TaskGroup.spawn`, two-worker TaskGroup + I/O, `Timeout` around I/O under `block_on`).

## Files changed
- tests/conformance/p11/e11_6_async_io/README.md
- tests/conformance/p11/e11_6_async_io/check_conformance_bundles.test
- tests/conformance/p11/e11_6_async_io/gen_tests.py
- tests/conformance/p11/e11_6_async_io/src/taskgroup_async_io.axsrc
- tests/conformance/p11/e11_6_async_io/taskgroup_async_io.ax
- tests/conformance/p11/e11_6_async_io/file_pipeline_tasks.ax
- tests/conformance/p11/e11_6_async_io/tcp_multi_client_echo.ax
- tests/conformance/p11/e11_6_async_io/tcp_framing_split.ax
- tests/conformance/p11/e11_6_async_io/udp_burst_exchange.ax
- tests/conformance/p11/e11_6_async_io/cancel_token_reads.ax
- tests/conformance/p11/e11_6_async_io/timeout_reads_buffer_safety.ax
- tests/conformance/p11/e11_6_async_io/timers_with_io.ax

STATUS: COMPLETE round=0
