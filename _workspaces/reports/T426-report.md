# T426 Report — Windows IOCP Reactor, Timer Wheel & Oracle Async I/O Backend

## Summary
Implemented T426 (`SPEC-35`, `REQ-ASY-153`, `REQ-ASY-154`, `REQ-ASY-158`, `REQ-ASY-159`) in canonical Axiom syntax:
- **Host Intrinsics (`std/core/host.ax`, `compiler/types/typeck.ax`, `compiler/lir/builder.ax`)**: Added all 20 `@lang("host_intrinsic")` `host.aio_*` declarations (`aio_create`, `aio_destroy`, `aio_wake`, `aio_wait`, `aio_cancel`, `aio_file_open`, `aio_submit_read_at`, `aio_submit_write_at`, `aio_submit_flush`, `aio_tcp_bind`, `aio_socket_local_port`, `aio_submit_accept`, `aio_submit_connect`, `aio_submit_recv`, `aio_submit_send`, `aio_tcp_shutdown`, `aio_udp_bind`, `aio_submit_recv_from`, `aio_submit_send_to`, `aio_close`), wired exact signature validation and `RT_CAP_ASYNC_REACTOR` capability tracking in `compiler/types/typeck.ax`, and lowered them to `__ax_host_aio_*` in `compiler/lir/builder.ax`.
- **Windows x64 IOCP Backend (`std/sys/windows/iocp.ax`)**: Implemented native Win32 IOCP (`CreateIoCompletionPort`, `GetQueuedCompletionStatusEx`, `PostQueuedCompletionStatus`, `CancelIoEx`, `CreateFileW` with `FILE_FLAG_OVERLAPPED`, `ReadFile`, `WriteFile`, `FlushFileBuffers`) and Winsock2 overlapped socket operations (`WSASocketW`, `WSAIoctl` for `AcceptEx`/`ConnectEx`, `WSARecv`, `WSASend`, `WSARecvFrom`, `WSASendTo`, `bind`, `listen`, `getsockname`, `getpeername`, `shutdown`, `closesocket`) with heap-allocated `AioOverlapped` envelopes.
- **Deterministic Oracle Async I/O & Virtual-Time Backend (`compiler/interp/oracle.ax`, `compiler/interp/interp.ax`)**: Implemented deterministic completion queueing, virtual monotonic clock advancement on `aio_wait(timeout_ns > 0)`, `aio_cancel` (`-6` / `IoError.Cancelled`), overlapped file I/O, and in-memory loopback TCP/UDP socket queues inside `OracleAioState` (freed on `interp_host_cleanup`).
- **Zero-OS-Thread Timer Wheel & Periodic `Interval` (`std/async/timer.ax`)**: Implemented `TimerWheel` (min-heap ordered by `(deadline_ns, timer_id)` with $O(1)$ `next_deadline_ns()` and thread-safe raw-waker storage), `SleepFuture` with `Drop` cancellation (`sleep`, `sleep_ns`, `sleep_ms`, `sleep_until`), and `Interval` supporting `IntervalMode` (`FixedRate`, `FixedDelay`) and `MissedTickBehavior` (`Burst`, `Skip`, `Delay`).
- **Unified `Reactor` & Executor Integration (`std/async/reactor.ax`, `std/async/executor.ax`, `std/async/mod.ax`)**: Implemented `Reactor` managing `IoOpSlot` lifecycle (`Submitted`, `Completed`, `CancellingZombie`, `Free`), retaining owned buffers until OS completion arrives even when an awaiting `Future` is dropped early (`REQ-ASY-152, 157, 158`), and integrated `Reactor` + `TimerWheel` into `LocalExecutor` (with `block_on`, `reactor`, `reactor_handle`, `shutdown`) and `Executor`.
- **Tests (`tests/std/async/reactor/*.ax`)**: Added 4 `modes: interp native` tests covering IOCP completion wakeup, 120 concurrent timers on a single thread in deterministic order with zero extra OS threads, `Interval` missed-tick policies (`Burst`, `Skip`, `Delay`, `FixedDelay`), and `CancellingZombie` buffer retention/reclamation on early `Future` drop.

## Build & Fixed-Point Verification (`build-snap-T426/`)
- Snapshot: `build-snap-T426/` refreshed on HEAD `3f60f9ba` (`36 generator(s), 60 file(s)` bundles regenerated).
- Stage 1 (`build/axiomc1.exe`): `STAGE1 OK` (`34430464` bytes, `sha256=07a6953524481c75`).
- Stage 2 (`build/axiomc2.exe`): `STAGE2 (O1) OK` (`9212416` bytes, `sha256=4bdb5da0aaa4b6a19c80c1b3279b69b1153847fc37d05bb4a05e7935f8199be4`).

## Test & Taskgate Verification (`build-snap-T426/`)
- **Targeted suite** (`python tools/axtest.py --compiler build/axiomc2.exe --exclude-requires axiom0-internal --filter std/async/reactor --no-cache -j 2 --verbose`):
  - `TOTAL 12 PASS 12 FAIL 0 SKIP 0 XFAIL 0`, `WEAK-NATIVE 0`
  - `interval_missed_ticks.ax`, `iocp_completion_wakeup.ax`, `timer_wheel_100_timers.ax`, `zombie_buffer_retention.ax` all PASS in `[interp]`, `[native]`, and `[native-O1]`.
- **Taskgate** (`python tools/taskgate.py --task T426 --compiler build/axiomc2.exe --build-dir build --exclude-requires axiom0-internal -j 2 --json-out _workspaces/artifacts/taskgate-T426.json`):
  - `own`: `4 ids, 12 results, 12 PASS, 0 FAIL` (`WEAK-NATIVE 0`)
  - `smoke`: `34 ids, 55 results, 55 PASS, 0 FAIL`
  - `affected`: `606 ids, 1292 results, 1279 PASS, 1 FAIL, 12 SKIP` (`selfhost 79/79 PASS` including all `bundles_current.test`, `std 134/134 PASS`, `conformance 62/62 PASS`, `run 124/124 PASS`)
  - `archcheck`: `clean (exit 0) — 235 files scanned, 0 violations`
  - `smoke-check`: `OK`
  - **Note on the single affected failure**: `ui/security_profiles/safety_profile_safe_neg.ax` failed with `AX_TYPE_UNSUPPORTED_IN_BOOTSTRAP` at line 18 (`@addr(0x4000usize)`). Verified that the pre-T426 cached HEAD (`3f60f9ba`, T501) compiler (`_workspaces/artifacts/compiler-cache/axiomc2_O1_1ee43638e6dc8ed0.exe`) fails on the exact same line 18 error before any T426 change — this is a pre-existing HEAD (`3f60f9ba`) regression unrelated to T426.

## Hygiene Checks (Main Repo)
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T426`: 14 staged source/test files + report, `0 REFUSED`.
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: `HARNESS OK`.

## Files changed
- `std/core/host.ax`
- `std/sys/windows/iocp.ax`
- `std/async/timer.ax`
- `std/async/reactor.ax`
- `std/async/executor.ax`
- `std/async/mod.ax`
- `compiler/types/typeck.ax`
- `compiler/lir/builder.ax`
- `compiler/interp/oracle.ax`
- `compiler/interp/interp.ax`
- `tests/std/async/reactor/iocp_completion_wakeup.ax`
- `tests/std/async/reactor/timer_wheel_100_timers.ax`
- `tests/std/async/reactor/interval_missed_ticks.ax`
- `tests/std/async/reactor/zombie_buffer_retention.ax`

## Status
STATUS: COMPLETE round=0
