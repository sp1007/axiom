# T425 Report — E11.6 Canonical Unified Async I/O & Reactor Specification (`SPEC-35`)

## Tóm tắt
Báo cáo hoàn thành task `T425` (`E11.6`): biên soạn đặc tả chuẩn `spec/SPEC-35-async-io.md` quy định mô hình
vào/ra bất đồng bộ thống nhất của Axiom (`AXS-AIO-001`..`AXS-AIO-052`), bao gồm hợp đồng Proactor/Reactor
độc lập nền tảng nối Windows IOCP (`CreateIoCompletionPort`, `OVERLAPPED`, `GetQueuedCompletionStatusEx`,
`CancelIoEx`), Linux `io_uring`/`epoll` và bộ mô phỏng tất định (`compiler/interp/oracle.ax`); mô hình sở hữu
bộ đệm an toàn đến khi hoàn thành vật lý (`IoBuf`, giữ sống bộ đệm trong `Reactor` ở trạng thái
`CancellingZombie` khi `Future` bị hủy hoặc `Drop` sớm); bánh xe định thời phân cấp `TimerWheel` không tạo
luồng OS (`sleep`, `sleep_until`, `Interval` với `FixedRate`/`FixedDelay` và `MissedTickBehavior`, tích hợp
`Deadline`/`Timeout`); các giao diện `AsyncRead`/`AsyncWrite`, tệp bất đồng bộ `AsyncFile` (tách biệt
`close().await` có thể lỗi với `Drop` tất định), và ngăn xếp mạng `std.net` (`AsyncTcpListener`,
`AsyncTcpStream` hỗ trợ `split()` thành `TcpReadHalf` + `TcpWriteHalf`, `AsyncUdpSocket`) cùng 20 hàm nội tại
`host.aio_*`. Đồng thời cập nhật `spec/INDEX.md` và `spec/SPEC-04-core-extensibility.md` (`AXS-EXT-110`,
`AXS-EXT-130`).

## Summary of Deliverables

1. **`spec/SPEC-35-async-io.md` (`AXS-AIO-001`..`AXS-AIO-052`)**:
   - **§1 Unified Async I/O Architecture & Proactor/Reactor Contract (`AXS-AIO-001`..`AXS-AIO-007`)**: Establishes separation of resource and buffer ownership domains, `Future`-based suspension without implicit OS threads and at-most-once completion (`REQ-ASY-151`, `REQ-ASY-155`), unified Proactor/Reactor abstraction bridging Windows IOCP and Linux `io_uring`/`epoll` (`REQ-ASY-158`), `Reactor` operation table (`IoOpId`, `IoOpSlot`, `IoOpState`), physical operation cancellation vs `Future` drop (`REQ-ASY-035`, `REQ-ASY-152`, `REQ-ASY-158`), Windows x64 IOCP backend contract (`std/sys/windows/iocp.ax`), and deterministic oracle virtual-time & loopback completion queues (`compiler/interp/oracle.ax`).
   - **§2 Completion-Safe Buffer Ownership, `IoBuf` & Registered/DMA Memory Contracts (`AXS-AIO-010`..`AXS-AIO-014`)**: Defines the In-Flight Buffer Retention Invariant and Buffer-Lifecycle State Diagram (`CallerOwned -> InFlightOwned -> CompletedReturned` and `InFlightOwned -> CancellingZombie -> ReclaimedAfterCompletion`, `REQ-ASY-152`, `REQ-ASY-157`), `IoBuf` and `IoResultBuf`, reactor-pinned staging buffers for slice-based operations, scatter/gather capability disjointness, and DMA/RDMA registered memory lifetime contracts (`REQ-CONC-153`).
   - **§3 Hierarchical Timer Wheel, `sleep`, `Interval` & `Deadline` Integration (`AXS-AIO-020`..`AXS-AIO-023`)**: Specifies the zero-OS-thread `TimerWheel` in `std/async/timer.ax` driving `host.aio_wait` timeouts (`REQ-ASY-154`), `sleep`/`sleep_until`, `Interval` (`IntervalMode.FixedRate`/`FixedDelay` and `MissedTickBehavior.Burst`/`Skip`/`Delay`, `REQ-ASY-159`), and `Deadline`/`Timeout<F>` integration (`REQ-ASY-153`).
   - **§4 Unified `AsyncRead` / `AsyncWrite` Traits & `AsyncFile` (`AXS-AIO-030`..`AXS-AIO-033`)**: Extends `IoError` for async cancellation/timeouts/networking, specifies `AsyncRead`/`AsyncWrite` (`read_buf`, `read`, `read_exact`, `write_buf`, `write`, `write_all`), `AsyncFile` concurrent positional `read_at`/`write_at` over `view<AsyncFile>`, and explicit fallible `close(self).await` vs non-fallible `Drop`.
   - **§5 Asynchronous Networking (`std.net`, `AXS-AIO-040`..`AXS-AIO-044`)**: Specifies `Ipv4Addr`, `SocketAddr`, `AsyncTcpListener`, `AsyncTcpStream`, full-duplex capability splitting `stream.split() -> (TcpReadHalf, TcpWriteHalf)` and `tcp_rejoin` (`REQ-CONC-152`), and `AsyncUdpSocket`.
   - **§6–§9 Host Intrinsics (`host.aio_*`), Examples, Traceability & Sources (`AXS-AIO-050`..`AXS-AIO-052`)**: Defines the 20 `host.aio_*` intrinsics, `Happens-Before` memory ordering rules, positive/negative canonical Axiom examples (`=` and `.`), requirement traceability matrix (`REQ-ASY-035`, `REQ-ASY-151`, and downstream `E11.6` requirements), and sources.

2. **`spec/SPEC-04-core-extensibility.md` & `spec/INDEX.md` Updates**:
   - **`spec/SPEC-04-core-extensibility.md`**: Appended the 20 `host.aio_*` intrinsics to `AXS-EXT-110` (`§11`) and updated the `E11.6 Async IO` row in `AXS-EXT-130` (`§13`).
   - **`spec/INDEX.md`**: Added `spec/SPEC-35-async-io.md` to `§2`, `AXS-AIO-NNN` to `§4`, and updated the Concurrency & Async row in `§5`.

## Verification
- `python .claude/skills/axiom-tasks/scripts/reqcov.py --strict`: PASS (100.0% requirement coverage)
- `python .claude/skills/axiom-tasks/scripts/harness_check.py`: PASS
- `python tools/gatecheck.py --no-run`: PASS
- `python .claude/skills/axiom-tasks/scripts/taskctl.py changes T425`: PASS (`0 REFUSED`)

STATUS: COMPLETE round=0

## Files changed
- `spec/SPEC-35-async-io.md`
- `spec/INDEX.md`
- `spec/SPEC-04-core-extensibility.md`
