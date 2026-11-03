# SPEC-35 — Unified Async I/O, Proactor/Reactor Contract, Completion-Safe Buffer Ownership, Timer Wheel, `AsyncFile` & `std.net` Sockets (`std.async`, `std.io`, `std.fs`, `std.net`)

## Tóm tắt

Đặc tả chính tắc (`SPEC-35`) cho mô hình vào/ra bất đồng bộ thống nhất của Axiom (`E11.6`): hợp đồng `Reactor` kết hợp hoàn thành (`Proactor` trên Windows IOCP / Linux `io_uring`) và sẵn sàng (`Reactor` trên Linux `epoll` / macOS `kqueue`) đằng sau một giao diện độc lập nền tảng; mô hình sở hữu bộ đệm an toàn đến khi hoàn thành vật lý (`IoBuf`, giữ sống bộ đệm trong `Reactor` ngay cả khi `Future` bị hủy hoặc `Drop` sớm); bánh xe định thời phân cấp không tạo luồng OS (`sleep`, `sleep_until`, `Interval`, tích hợp `Deadline`/`Timeout`); các giao diện `AsyncRead`/`AsyncWrite`, tệp bất đồng bộ `AsyncFile` (tách biệt `close().await` có thể lỗi với `Drop` tất định), và ngăn xếp mạng `std.net` (`AsyncTcpListener`, `AsyncTcpStream` hỗ trợ `split()` thành `TcpReadHalf` + `TcpWriteHalf`, `AsyncUdpSocket`) cùng bộ hàm nội tại `host.aio_*`. Tài liệu này hợp nhất `docs/base/specs/0221` và các đặc tả `tasks/0335`, `0438`, `0440`, `0441`, `0461`, `0464`, nối tiếp `SPEC-30`..`SPEC-34` và `SPEC-04 §11` (`AXS-EXT-110`, `AXS-EXT-130`).
Các quyết định cốt lõi:
- **Mô hình I/O bất đồng bộ dựa trên `Future` không tạo luồng ngầm và hoàn thành tối đa một lần (`REQ-ASY-035`, `REQ-ASY-151`, `REQ-ASY-155`, `REQ-ASY-158`)**: Mọi thao tác I/O bất đồng bộ biểu diễn điểm tạm dừng qua `Future<T>` mà không ngầm tạo luồng OS; mỗi thao tác vật lý hoàn thành tối đa một lần; việc `Drop` một `Future` I/O không đồng nghĩa với việc hệ điều hành đã hủy tức thì hay hoàn tác dữ liệu trên đường truyền, mà phải đi qua giao thức hủy hợp tác (`CancelIoEx` / `aio_cancel`) có kiểm soát vòng đời tài nguyên.
- **Sở hữu bộ đệm an toàn khi hoàn thành (`Completion-Safe Buffer Ownership`, `REQ-ASY-152`, `REQ-ASY-157`, `REQ-CONC-153`)**: Khác với I/O đồng bộ chỉ mượn `view`/`mut_view` trên ngăn xếp, một thao tác I/O đang bay (`in-flight`) được hạt nhân OS ghi/đọc trực tiếp bằng DMA/overlapped. Do đó `IoBuf` hoặc bộ đệm trung gian được ghim thuộc quyền sở hữu của khe `Reactor` cho đến khi gói hoàn thành từ hạt nhân trả về; nếu `Future` bị `Drop` sớm (ví dụ do `Timeout`), `Drop` phát lệnh `host.aio_cancel` và chuyển khe sang trạng thái `CancellingZombie`, tuyệt đối không giải phóng hay tái sử dụng bộ nhớ khi hạt nhân còn có thể truy cập.
- **Bánh xe định thời (`TimerWheel`) gắn trực tiếp vào `Reactor` và ngữ nghĩa định kỳ tường minh (`REQ-ASY-153`, `REQ-ASY-154`, `REQ-ASY-159`)**: Hàng ngàn bộ hẹn giờ (`sleep`, `sleep_until`, `Interval`, `Timeout`) dùng chung cấu trúc bánh xe/đống thời gian đơn điệu (`host.monotonic_ns()`) điều khiển thời gian chờ của `host.aio_wait` mà không tạo luồng OS cho mỗi timer; `Interval` quy định tường minh chế độ nhịp (`FixedRate` / `FixedDelay`) và chính sách bù nhịp trễ (`MissedTickBehavior`: `Burst`, `Skip`, `Delay`).
- **Tách năng lực đọc/ghi song song trên socket (`split()`, `REQ-CONC-152`) và dọn dẹp tệp tường minh**: `AsyncTcpStream` không cho phép đột biến đồng thời không đồng bộ hóa, nhưng cung cấp `stream.split() -> (TcpReadHalf, TcpWriteHalf)` để hai tác vụ đọc và ghi song song toàn phần (full-duplex) an toàn kiểu; `AsyncFile` tách biệt `close().await -> Result<(), IoError>` với `Drop` không ném lỗi.

Status: draft (T425, 2026-11-03)
Owner: axiom-architect
Consolidates: `docs/base/specs/0221 - IO-ASYNC-001 — Unified IO Model.md`, `docs/base/tasks/0335 - BOOTSTRAP-076 — Axiom IO, File, Socket, Process, OS Handle & Resource Model.md`, `docs/base/tasks/0438 - BOOTSTRAP-179 — IO, File, Socket, Device, Zero-Copy & Unified Data Path.md`, `docs/base/tasks/0440 - BOOTSTRAP-181 — Time, Clock, Timer, Scheduling Time & Temporal Semantics.md`, `docs/base/tasks/0441 - BOOTSTRAP-182 — Networking, Socket Model, Async IO & Zero-Copy Network Stack.md`, `docs/base/tasks/0461 - BOOTSTRAP-202 — Networking, Distributed Systems, RPC & High-Performance IO.md`, `docs/base/tasks/0464 - BOOTSTRAP-205 — Time, Scheduling, Real-Time, Timers & Temporal Semantics.md`
Covers: `REQ-ASY-035`, `REQ-ASY-151`
Consumers: `T426` (`std/sys/windows/iocp.ax`, `std/async/reactor.ax`, `std/async/timer.ax`, `std/core/host.ax`, `compiler/interp/oracle.ax`), `T427` (`std/io/async_io.ax`, `std/fs/async_file.ax`, `std/net/mod.ax`), `T428` (`tests/conformance/p11/e11_6_async_io`)

---

## 1. Unified Async I/O Architecture & Proactor/Reactor Contract

**AXS-AIO-001** (Unified resource & buffer model with distinct synchronous and asynchronous execution surfaces; `REQ-ASY-151`, `0221 §1–11, §35, §42 AIO-20..28, AIO-36, AIO-40`, `tasks/0335 §1–15, §26–28, §100 AIO-20..40, AIO-91..95`, `tasks/0438 §179.100, §2097 AIO-20..29`).
1. **Separation of Resource and Buffer ownership domains (`0221 §42 AIO-20`, `tasks/0335 AIO-20..21`, `tasks/0438 AIO-20`)**:
   - An I/O resource (`File`, `AsyncFile`, `AsyncTcpListener`, `AsyncTcpStream`, `AsyncUdpSocket`) owns an OS kernel handle (`i64`, distinct from memory pointers per `AIO-36`), whereas a buffer (`[N]u8`, `ByteBuf`, `IoBuf`) owns physical memory storage.
   - Resource types are single-owner move types (`!Copy`) with deterministic `Drop` obligations (`tasks/0335 AIO-22, AIO-27, AIO-30..31`). Duplicating an underlying OS handle requires an explicit operation (`try_clone` / `duplicate`), never an implicit copy (`tasks/0335 AIO-28, AIO-42, AIO-57`).
2. **Synchronous vs asynchronous API separation (`0221 §1, §10–11, §35 AIO-26..28`, `tasks/0335 AIO-91..93`, `tasks/0438 AIO-26`)**:
   - Synchronous I/O operations (`std.io.File`, `std.fs`) block the calling execution thread directly in the OS kernel without requiring an async scheduler (`0221 §35 AIO-28`).
   - Asynchronous I/O operations (`std.fs.AsyncFile`, `std.net.*`, `std.async.timer.*`) return passive `Future<Output = Result<..., IoError>>` state machines driven by an executor and reactor without implicitly spawning OS threads (`REQ-ASY-151`, `0221 §42 AIO-27`, `tasks/0335 §27 AIO-65, AIO-93`, `tasks/0438 AIO-23`).
   - Both synchronous and asynchronous I/O share the same error taxonomy (`std.io.IoError`), byte-oriented payload representation, and ownership/capability invariants (`0221 §1, §42 AIO-26, AIO-40`).

**AXS-AIO-002** (`Future`-based I/O suspension & at-most-once completion invariant; `REQ-ASY-151`, `REQ-ASY-155`, `0221 §13, §36 AIO-24`, `tasks/0438 §2097 AIO-23, AIOASYNC-24..25`, `tasks/0441 §182.125, §182.201 ANET-40, ANET-42..43, ANET-48`).
1. **No thread-per-I/O and no hidden worker pool (`REQ-ASY-151`, `REQ-ASY-155`, `tasks/0438 AIO-23`, `tasks/0441 ANET-40`)**:
   - Initiating or awaiting an async I/O `Future` (`read`, `write`, `accept`, `connect`, `recv_from`, `send_to`, `sleep`) registers an operation slot in the active `Reactor` and suspends the calling task (`Poll.Pending`) without creating a dedicated OS thread.
2. **At-most-once completion (`REQ-ASY-151`, `tasks/0438 AIOASYNC-24`)**:
   - Every submitted I/O operation identified by `IoOpId` transitions to a terminal completion state (`Completed(result)` or `Cancelled`) **at most once**.
   - Once the awaiting `Future` observes `Poll.Ready(out)`, the operation slot is retired and any subsequent `poll()` on the completed I/O `Future` is rejected by the standard state-machine contract (`AX_ASYNC_POLL_AFTER_COMPLETE`, `SPEC-33 AXS-ASY-044`).
3. **Spurious wake resilience and unordered completions (`tasks/0441 ANET-42..43, ANET-48`)**:
   - A `Waker.wake()` notification indicates that an operation *may* have progressed; the `Future.poll` implementation always inspects the reactor slot state before returning `Poll.Ready` (`ANET-43`).
   - When multiple independent I/O operations are submitted concurrently, the OS kernel may complete them in any order (`ANET-48`, `tasks/0438 AIOOPT-22`); sequential ordering requires explicit `.await` sequencing by the caller.

**AXS-AIO-003** (Unified Proactor/Reactor backend abstraction; `REQ-ASY-158`, `0221 §9, §12–16, §42 AIO-29`, `tasks/0335 §28 AIO-64`, `tasks/0438 §2097 AIO-29`, `tasks/0441 §182.200–201 ANET-41, ANET-50..53`, `tasks/0461 §202.43–44, §202.72–74 ANET-43..44, ANET-57`).
1. **Target-independent semantic surface (`REQ-ASY-158`, `0221 §12–15 AIO-29`, `tasks/0461 ANET-43..44`)**:
   - Platform event notification mechanisms—completion-based **Proactors** (Windows `IOCP`, Linux `io_uring`) and readiness-based **Reactors** (Linux `epoll`, macOS/BSD `kqueue`)—are hidden behind a single unified `std.async.Reactor` contract (`std/async/reactor.ax`) and the `host.aio_*` host boundary (`SPEC-04 AXS-EXT-110`).
   - Replacing or selecting a platform backend never alters observable Axiom source semantics, ownership rules, or error classifications (`tasks/0441 ANET-51..52`).

```text
+-------------------------------------------------------------------------+
| High-Level Async I/O Surface (`std.io`, `std.fs`, `std.net`, `std.async`)|
|   AsyncFile, AsyncTcpListener, AsyncTcpStream, AsyncUdpSocket, Timer    |
+------------------------------------+------------------------------------+
                                     | submits IoOp + IoBuf, awaits IoOpId
                                     v
+-------------------------------------------------------------------------+
| Unified Reactor & Timer Wheel (`std/async/reactor.ax`, `timer.ax`)      |
|   IoOpSlot Table + Pinned IoBuf Retention + Hierarchical TimerWheel     |
+------------------------------------+------------------------------------+
                                     | `host.aio_*` (SPEC-04 AXS-EXT-110)
            +------------------------+------------------------+
            |                        |                        |
            v                        v                        v
+-----------------------+ +----------------------+ +----------------------+
| Windows x64 Native    | | Linux Native (E16.9) | | Deterministic Oracle |
| `std/sys/windows/`    | | `io_uring` / `epoll` | | `compiler/interp/`   |
| `iocp.ax` (`OVERLAPPED`| | completion/readiness | | `oracle.ax` virtual  |
| + `CancelIoEx`)       | | translation          | | queue & loopback net |
+-----------------------+ +----------------------+ +----------------------+
```

2. **Bridging Completion (Proactor) and Readiness (Reactor) (`0221 §12–15`)**:
   - On a **Proactor** backend (Windows IOCP, Linux `io_uring`), `host.aio_submit_*` passes the reactor-pinned buffer address and an operation context (`OVERLAPPED` / `sqe`) directly to the kernel; the kernel performs the transfer and posts a completion packet harvested by `host.aio_wait`.
   - On a **Readiness** backend (Linux `epoll`, macOS `kqueue`), the backend registers interest (`EPOLLIN` / `EPOLLOUT`) on the non-blocking descriptor (`O_NONBLOCK`), and when readiness is reported during `host.aio_wait`, performs the non-blocking `pread`/`pwrite`/`recv`/`send` into the reactor-pinned buffer before emitting the completion event (`0221 §14, §34 AIO-32`).

**AXS-AIO-004** (`Reactor` operation table, `IoOpId`, and executor parking integration in `std/async/reactor.ax`; `T426`, `0221 §13–14`, `tasks/0461 §202.72–75`, `SPEC-34 AXS-EXEC-010, AXS-EXEC-014`).
Module `std.async` (`std/async/reactor.ax`, re-exported from `std/async/mod.ax`) defines the unified `Reactor`:

```axiom
@derive(Copy, Clone, Eq, PartialEq, Hash)
pub struct IoOpId {
    pub raw: u64,
}

@derive(Copy, Clone, Eq, PartialEq)
pub enum IoOpState {
    Submitted,
    Completed,
    CancellingZombie,
    Free,
}

pub struct IoOpSlot {
    pub op_id: u64,
    pub state: IoOpState,
    pub handle: i64,
    pub result: i64,
    pub aux: u64,
    pub waker: Option<Waker>,
    pub owned_buf_ptr: *mut u8,
    pub owned_buf_cap: usize,
    pub user_dst_ptr: *mut u8,
    pub user_dst_len: usize,
}

pub struct Reactor {
    os_handle: i64,
    slots: Vec<IoOpSlot>,
    timers: TimerWheel,
    in_flight_count: usize,
}

impl Reactor {
    pub fn new() -> Result<Reactor, IoError>
    pub fn os_handle(self: view<Reactor>) -> i64
    pub fn has_pending_work(self: view<Reactor>) -> bool
    pub fn poll_nonblocking(self: mut_view<Reactor>) -> Result<usize, IoError>
    pub fn turn(self: mut_view<Reactor>, max_wait_ns: Option<u64>) -> Result<usize, IoError>
    pub fn wake(self: view<Reactor>)
    pub fn shutdown(self: mut_view<Reactor>)
}
```

1. **Generation-stamped `IoOpId` (`0221 §13`)**:
   - Each submitted operation receives a unique `IoOpId { raw: u64 }` matching the `op_id` returned by `host.aio_submit_*` (encoding slot index and monotonic generation so a late OS completion never aliases a recycled slot).
2. **Executor event-loop integration (`SPEC-34 AXS-EXEC-010, AXS-EXEC-014`, `tasks/0461 §202.73–74`)**:
   - Every `LocalExecutor` owns a local `Reactor`, and every multi-threaded `Executor` shares a coordinator `Reactor` (or per-worker reactor handle woken via `host.aio_wake`).
   - During the executor poll loop:
     - Between task batches, the executor calls `reactor.poll_nonblocking()` (`host.aio_wait(..., timeout_ns = 0)`) and advances expired timers in `reactor.timers`, waking all tasks whose I/O or timer operations completed.
     - When no runnable tasks remain in any local or global queue (`in_flight_count > 0` or `!timers.is_empty()`), the parking worker calls `reactor.turn(timers.next_expiration_delay_ns())`, which blocks inside `host.aio_wait` until either an I/O completion arrives, the next timer expires, or another thread calls `reactor.wake()` (`host.aio_wake`).

**AXS-AIO-005** (Distinction between `Future` drop, explicit cancellation, and physical OS completion; `REQ-ASY-035`, `REQ-ASY-152`, `REQ-ASY-155`, `REQ-ASY-158`, `0127 §23`, `0221 §17–18, §42 AIO-25`, `tasks/0335 §24–25, §100 AIO-76..80`, `tasks/0438 §2097 AIO-24, AIOASYNC-21..23`, `tasks/0441 §182.126–129, §182.201 ANET-44..46`, `tasks/0461 §202.37–38 ANET-37..38`).
1. **Dropping a `Future` does not instantaneously halt external OS or wire operations (`REQ-ASY-035`, `REQ-ASY-152`, `REQ-ASY-155`, `REQ-ASY-158`)**:
   - Dropping an in-flight I/O `Future` (e.g. when a `Timeout<F>` expires or a `TaskGroup` cancels sibling tasks) means the **caller no longer awaits the result** (`0221 §17`, `tasks/0441 §182.127`).
   - It does **not** guarantee that the OS kernel has immediately stopped DMA into the buffer, nor does it roll back bytes already transmitted over a network socket or written to disk (`REQ-ASY-035`, `REQ-ASY-155`, `ANET-44`).
2. **Mandatory `Drop` protocol for in-flight I/O futures (`REQ-ASY-152`, `REQ-ASY-158`)**:
   - When an I/O `Future` is dropped while its `IoOpSlot` is still in `IoOpState.Submitted`:
     1. The `Future`'s `Drop` implementation invokes `reactor.cancel_op(self.op_id)`, which calls `host.aio_cancel(reactor.os_handle, self.op_id.raw)` (`CancelIoEx` on Windows).
     2. The slot transitions from `IoOpState.Submitted` to `IoOpState.CancellingZombie`, clearing `slot.waker = Option.None` and `slot.user_dst_ptr = 0 as *mut u8` (so the caller's stack frame is never written to after `Future` drop), while **retaining** `slot.owned_buf_ptr` inside the reactor.
     3. Only when `host.aio_wait` subsequently reaps the OS completion packet for `op_id` (whether the kernel completed the transfer or aborted it with `ERROR_OPERATION_ABORTED` / `IoError.Cancelled`) does the reactor free `slot.owned_buf_ptr` and transition the slot to `IoOpState.Free` (`tasks/0335 AIO-80`, `tasks/0438 AIOASYNC-21`).
   - During `reactor.shutdown()` (or `Executor.shutdown()`), the reactor cancels any remaining `CancellingZombie` operations and drains `host.aio_wait` until `in_flight_count == 0`, guaranteeing zero leaked buffers and zero dangling background I/O (`tasks/0441 ANET-45`, `tasks/0464 §205.95`).
3. **Linearization of cancellation races (`REQ-ASY-158`, `tasks/0441 §182.126`, `tasks/0461 ANET-38`)**:
   - If an explicit cancellation request (`cancel()`) races with physical OS completion:
     - If the OS completion packet arrives with transferred bytes `>= 0` before the kernel honours `CancelIoEx`, the operation's completion status is `Completed(n)`.
     - If the kernel aborts the operation via `CancelIoEx`, the completion packet carries `IoError.Cancelled` (`-6`).

**AXS-AIO-006** (Windows x64 IOCP backend contract in `std/sys/windows/iocp.ax`; `T426`, `T427`, `0221 §12–14`, `tasks/0441 §182.200`).
On `x86_64-windows` (`std/sys/windows/iocp.ax`), the `host.aio_*` intrinsics map to Win32 and Winsock2 completion APIs linked via `@link("kernel32.dll")` and `@link("ws2_32.dll")`:
1. **Completion Port**: `CreateIoCompletionPort`, `GetQueuedCompletionStatusEx` (batch-reaping `OVERLAPPED_ENTRY` records in a single syscall), `PostQueuedCompletionStatus` (for `host.aio_wake`), and `CancelIoEx` (for per-operation `OVERLAPPED` cancellation without cancelling unrelated operations on the same file/socket handle).
2. **Per-operation `AioOverlapped` envelope**: Each in-flight operation allocates or pools a fixed-address `AioOverlapped` struct whose first field is the Win32 `OVERLAPPED { Internal, InternalHigh, Offset, OffsetHigh, hEvent }` header followed by `op_id: u64`, `op_kind: u32`, `handle: i64`, `staging_buf: *mut u8`, `staging_cap: usize`, and `peer_addr_storage: [64]u8`. Because `AioOverlapped` is heap-allocated per slot, moving the Axiom `Future` value across stack frames or tasks never invalidates the `LPOVERLAPPED` pointer held by the Windows kernel (`tasks/0335 AIO-55`).
3. **Synchronous completion handling (`ERROR_IO_PENDING`)**: On Windows, if `ReadFile`, `WriteFile`, `WSARecv`, `WSASend`, `AcceptEx`, or `ConnectEx` returns synchronously (`TRUE`) or fails with `GetLastError() == ERROR_IO_PENDING` (`WSA_IO_PENDING = 997`), the completion packet is still queued to the IOCP port (unless `FILE_SKIP_COMPLETION_PORT_ON_SUCCESS` is explicitly enabled), so `host.aio_wait` observes a uniform completion stream. Immediate errors other than `ERROR_IO_PENDING` (e.g. `ERROR_HANDLE_EOF = 38`, mapped to `0` bytes read) are either queued as synthetic immediate completions in the reactor table or returned immediately.

**AXS-AIO-007** (Deterministic oracle async I/O & virtual-time backend in `compiler/interp/oracle.ax`; `T426`, `SPEC-33 AXS-ASY-051`, `SPEC-34 AXS-EXEC-016`, `tasks/0438 §179.97`, `tasks/0440 §181.103–106, §181.152 ATIMETEST-20..22`).
In `--interp` mode (`compiler/interp/oracle.ax`), `host.aio_*` executes deterministically without wall-clock sleep or OS socket nondeterminism:
1. **Virtual monotonic clock advancement**: When `host.aio_wait(reactor, out, max_events, timeout_ns)` is called and no I/O completions are immediately ready in the reactor's pending queue, if `timeout_ns > 0`, the oracle advances its virtual monotonic clock (`monotonic_ns`) by `timeout_ns` (or to the next scheduled completion timestamp) and returns `0` immediately without sleeping the host OS thread (`ATIMETEST-21..22`).
2. **Deterministic file & loopback socket queues**:
   - `aio_file_open`, `aio_submit_read_at`, `aio_submit_write_at`, and `aio_submit_flush` operate over the oracle's file handle table, enqueueing deterministic completion records `(op_id, result, 0)` in submission order (or transitioning to `result = -6` (`IoError.Cancelled`) if `aio_cancel(reactor, op_id)` is called before `aio_wait` reaps the entry).
   - `aio_tcp_bind`, `aio_submit_accept`, `aio_submit_connect`, `aio_submit_recv`, `aio_submit_send`, `aio_udp_bind`, `aio_submit_recv_from`, and `aio_submit_send_to` route loopback traffic (`127.0.0.1`, `0x7F000001`) through deterministic in-memory endpoint queues inside the oracle session: a `connect` pairs with a pending or subsequent `accept` on the matching port, `send` buffers bytes into the peer stream's receive FIFO and marks any blocked `recv` operation ready for the next `aio_wait`, and `send_to` enqueues discrete `(payload, sender_addr)` datagrams for `recv_from`.

---

## 2. Completion-Safe Buffer Ownership, `IoBuf`, & Registered/DMA Memory Contracts

**AXS-AIO-010** (Completion-safe buffer ownership & the In-Flight Buffer Retention Invariant; `REQ-ASY-152`, `REQ-ASY-157`, `0221 §2–6, §17–18, §28–30, §42 AIO-20..25`, `tasks/0335 §22–25, §100 AIO-76..80`, `tasks/0438 §2097 AIO-22, AIOASYNC-20..22`, `tasks/0441 §182.201 ANET-32..35, ANET-46`, `tasks/0461 §202.23–26, §202.100 ANET-23..26`).
1. **Why async I/O requires completion-pinned buffer ownership (`0221 §3–6, §18`)**:
   - In Axiom's capability model, ordinary borrowed views (`view<T>`, `mut_view<T>`) cannot be held across `.await` suspension points (`SPEC-33 AXS-ASY-034`, `AX_ASYNC_VIEW_ACROSS_AWAIT`), and stack frames of `Future` state machines may be dropped at any `.await` point if the enclosing task or `Timeout` is cancelled (`0221 §4, §18`).
   - If an OS kernel Proactor (`IOCP` / `io_uring`) is performing asynchronous DMA or overlapped writes into a buffer when the awaiting `Future` is dropped, reclaiming or reusing that buffer before the OS confirms completion would cause a kernel write-after-free (`REQ-ASY-152`, `0221 §18 AIO-25`, `tasks/0438 AIOASYNC-21`).
2. **Buffer-Lifecycle State Diagram (`REQ-ASY-152`, `REQ-ASY-157`)**:
   Every buffer participating in an asynchronous I/O operation follows the strict state machine below without requiring programmer-written lifetime annotations (`ANET-24`):

```text
+-------------------------------------------------------------------------+
| State 1: CallerOwned (`IoBuf` owned by task, or caller slice before op) |
+------------------------------------+------------------------------------+
                                     |
       submit async I/O (`read_buf` moves `IoBuf` into Reactor slot;
       borrowed `read` allocates/pins staging `IoBuf` in Reactor slot)
                                     |
                                     v
+-------------------------------------------------------------------------+
| State 2: InFlightOwned (Pinned in `Reactor.slots[id]`; kernel DMA live) |
|   - Caller has NO read/write access to the in-flight `IoBuf`.           |
|   - Buffer address is fixed in heap (`*mut u8`) outside `Future` frame. |
+-----------------+-------------------------------------+-----------------+
                  |                                     |
   Path A: `Future` awaited to completion    Path B: `Future` dropped early
   (`host.aio_wait` reaps completion)        (`Timeout` / `TaskGroup` cancel)
                  |                                     |
                  v                                     v
+-----------------------------------+ +-----------------------------------+
| State 3A: CompletedReturned       | | State 3B: CancellingZombie        |
|   - Kernel access has ceased.     | |   - `Future.drop` calls           |
|   - `read_buf` returns `(IoBuf,n)`| |     `host.aio_cancel(op_id)`.     |
|     back to caller (`CallerOwned`)| |   - `Future` stack frame is freed,|
|   - Borrowed `read` copies `n`    | |     `IoBuf` STAYS pinned in       |
|     bytes to caller slice on poll | |     `Reactor` while kernel drains.|
|     resume & frees staging `IoBuf`| +-----------------+-----------------+
+-----------------------------------+                   |
                                         `host.aio_wait` finally reaps
                                         OS abort/completion packet
                                                        |
                                                        v
                                      +-----------------------------------+
                                      | State 4: ReclaimedAfterCompletion |
                                      |   - Kernel access proven finished.|
                                      |   - `Reactor` frees pinned `IoBuf`|
                                      |     and marks `IoOpSlot` `Free`.  |
                                      +-----------------------------------+
```

**AXS-AIO-011** (`IoBuf` and `IoResultBuf` in `std/io/async_io.ax`; `T427`, `REQ-ASY-152`, `REQ-ASY-157`, `0221 §5–6, §29–30`, `tasks/0461 ANET-23..25`).
Module `std.io.async_io` (`std/io/async_io.ax`) defines the completion-safe owned buffer `IoBuf` and operation result wrapper `IoResultBuf`:

```axiom
pub struct IoBuf {
    pub ptr: *mut u8,
    pub len: usize,
    pub cap: usize,
}

pub struct IoResultBuf {
    pub buf: IoBuf,
    pub res: Result<usize, IoError>,
}

impl IoBuf {
    pub fn with_capacity(cap: usize) -> IoBuf
    pub fn from_slice(src: view<[u8]>) -> IoBuf
    pub fn from_byte_buf(buf: ByteBuf) -> IoBuf
    pub fn into_byte_buf(self) -> ByteBuf
    pub fn len(self: view<IoBuf>) -> usize
    pub fn capacity(self: view<IoBuf>) -> usize
    pub fn is_empty(self: view<IoBuf>) -> bool
    pub fn as_slice(self: view<IoBuf>) -> view<[u8]>
    pub fn as_mut_slice(self: mut_view<IoBuf>) -> mut_view<[u8]>
    pub fn clear(self: mut_view<IoBuf>)
    pub fn set_len(self: mut_view<IoBuf>, new_len: usize)
}
```

1. **Ownership & `Send` semantics**:
   - `IoBuf` is a single-owner heap buffer (`!Copy`, implements `Drop`, `Send`, and `Share`) whose backing memory `ptr` is allocated via `host.heap_alloc(cap, 8)` at a stable address independent of any stack frame.
   - Moving an `IoBuf` by value into `read_buf(buf)` or `write_buf(buf)` transfers ownership of `(ptr, len, cap)` into the `Reactor`'s `IoOpSlot` (`0221 §5, §28–29`, `ANET-25`), preventing the caller from reading, mutating, or dropping the buffer while the OS operation is in flight (`ANET-33..34`).
   - When the operation completes normally (`State 3A`), `IoResultBuf { buf, res }` returns ownership of the same `IoBuf` (with `buf.len` updated to the bytes read on `read_buf`) together with `res: Result<usize, IoError>` with zero intermediate memory copies (`0221 §7, §29`).
   - If the `Future` is dropped before completion (`State 3B`), ownership of the `IoBuf` remains in the `Reactor` slot until OS completion (`State 4`), sacrificing the abandoned buffer to uphold memory safety (`REQ-ASY-152`, `REQ-ASY-157`).

**AXS-AIO-012** (Scoped slice operations (`read`, `write`) via reactor-pinned staging buffers; `T427`, `REQ-ASY-152`, `REQ-ASY-157`, `0221 §6, §30`, `tasks/0461 ANET-26`).
To support ergonomic slice-based I/O without forcing every caller to manually thread `IoBuf` ownership (`0221 §6, §30`) while respecting `AX_ASYNC_VIEW_ACROSS_AWAIT` (`SPEC-33 AXS-ASY-034`):
1. **Owned-buffer primitive path (`read_buf`, `write_buf`)**: Zero-copy path where the caller moves `IoBuf` into the future and receives `IoResultBuf` back on completion.
2. **Pointer/slice convenience path (`read`, `read_exact`, `write`, `write_all`)**:
   - When a caller invokes an async operation using a reactor-managed staging buffer (or passes `(dst_ptr: *mut u8, len: usize)` inside an `async fn` where `dst` is a local buffer owned by the `async fn` state machine), the `Reactor` allocates and pins an internal staging buffer `owned_buf_ptr` for the OS kernel transfer.
   - Only inside the synchronous body of `Future.poll(cx)`—after `host.aio_wait` confirms the kernel transfer has completed (`IoOpState.Completed`) and while the `Future` is actively being polled—does the `Future` copy the completed bytes into the caller's destination storage and free the staging buffer.
   - If the `Future` is dropped early while `Poll.Pending`, `user_dst_ptr` is never touched again and the kernel writes harmlessly into the reactor-owned staging buffer until `CancelIoEx` completes (`REQ-ASY-152`, `REQ-ASY-157`).

**AXS-AIO-013** (Scatter/gather vectored I/O & capability disjointness; `0221 §22–23, §42 AIO-33`, `tasks/0438 AZCOPY-24..25`, `tasks/0441 ANET-35, ANET-37`, `tasks/0461 ANET-29`).
1. **Vectored write (`write_vectored`)**: Multiple shared `IoBuf` / `view<[u8]>` buffers may alias safely because `WRITE` to an I/O stream requires only `READ` capability on the source memory (`0221 §22–23 AIO-22, AIO-33`).
2. **Vectored read (`read_vectored`)**: Because reading from an I/O resource writes into destination buffers (`AIO-21`), each destination buffer in a scatter-read (`Vec<IoBuf>`) MUST be a distinct owned `IoBuf` (or proven disjoint `mut_view<[u8]>` capability per `SPEC-11` / `SPEC-30 AXS-CONC-031`, `ACAP-68`, `ANET-29, ANET-35`).

**AXS-AIO-014** (Zero-copy, DMA, and RDMA registered memory lifetime contracts; `REQ-CONC-153`, `0221 §7–8, §26–27, §42 AIO-30, AIO-35`, `tasks/0335 §20, §100 AIO-54..55`, `tasks/0438 §2097 AZCOPY-20..26, ADMA-20..25`, `tasks/0461 §202.79–80 ANET-54`, `tasks/0465 §206.25 ANET2-46..47`).
1. **Zero-copy as a semantics-preserving optimization (`0221 §8, §42 AIO-30`, `tasks/0438 AZCOPY-20..21`, `tasks/0461 ANET-27..28`)**:
   - Zero-copy transfer (`IoBuf` direct kernel DMA, `TransmitFile` / `sendfile` / `splice`) is permitted whenever layout and ownership contracts allow, but never alters observable ownership or mutates a buffer still observable as immutable by the caller (`AZCOPY-21`, `ANET-28`).
2. **DMA and RDMA registered memory regions (`REQ-CONC-153`, `tasks/0438 ADMA-20..25`, `tasks/0461 §202.79–80 ANET-54`, `tasks/0465 §206.25 ANET2-46..47`)**:
   - When a buffer is registered for hardware DMA or RDMA (`RegisteredRegion` / `IoBuf` pinned in a registration table), the memory registration resource MUST remain valid across all dependent in-flight operations (`REQ-CONC-153`, `ANET2-46`): attempting to unmap or free a registered region while `in_flight_ops > 0` defers physical reclamation until the reactor/RDMA completion queue (`CQ`) delivers terminal completion notifications for every dependent operation (`REQ-CONC-153`, `ADMA-22, ADMA-25`, `ANET2-47`).
   - Buffer reuse by the application is governed strictly by the completion notification (`IoResultBuf` delivery), never by wall-clock delay or unverified cancellation requests (`REQ-CONC-153`).

---

## 3. Hierarchical Timer Wheel, `sleep`, `Interval`, & `Deadline` Integration

**AXS-AIO-020** (Zero-OS-thread reactor timer wheel in `std/async/timer.ax`; `T426`, `REQ-ASY-154`, `tasks/0440 §181.147, §181.152 ATIMER-20..27`, `tasks/0464 §205.81 ATIME-28`).
1. **No OS thread per timer (`REQ-ASY-154`, `tasks/0440 ATIMER-27`)**:
   - Async timers (`sleep`, `sleep_until`, `Interval`, and reactor-driven `Timeout`) NEVER spawn a dedicated OS thread per timer (`REQ-ASY-154`).
   - Instead, `Reactor` embeds a deterministic `TimerWheel` (`std/async/timer.ax`) indexed by monotonic deadline (`u64` nanoseconds from `host.monotonic_ns()`, `ATIME-21..22`).
2. **`TimerWheel` structure and complexity (`T426`, `tasks/0464 §205.81`)**:
   - `TimerWheel` maintains registered timer entries `{ timer_id: u64, deadline_ns: u64, waker: Option<Waker>, cancelled: bool }` organized in hierarchical time-wheel slots (or a min-heap ordered by `(deadline_ns, timer_id)`) supporting thousands of concurrent timers with $O(1)$ next-expiration lookup (`next_deadline_ns() -> Option<u64>`).
   - When the executor parks in `reactor.turn()`, it computes `timeout_ns = max(0, next_deadline_ns - host.monotonic_ns())` and passes `timeout_ns` directly to `host.aio_wait`.
   - When `host.aio_wait` returns (or during `reactor.poll_nonblocking()`), `TimerWheel.advance_to(host.monotonic_ns())` pops all non-cancelled entries with `deadline_ns <= now_ns` in deterministic `(deadline_ns, timer_id)` order and invokes `waker.wake()`.

**AXS-AIO-021** (`sleep(duration)` and `sleep_until(deadline)` in `std/async/timer.ax`; `T426`, `REQ-ASY-153`, `REQ-ASY-154`, `tasks/0440 ATIMER-20..24`, `tasks/0464 ATIME-26..28, ATIME-32..33`).
Module `std.async` (`std/async/timer.ax`, re-exported from `std/async/mod.ax`) defines one-shot async timers:

```axiom
pub struct SleepFuture {
    timer_id: u64,
    deadline: Deadline,
    registered: bool,
}

pub fn sleep(duration: Duration) -> SleepFuture
pub fn sleep_ns(duration_ns: u64) -> SleepFuture
pub fn sleep_ms(duration_ms: u64) -> SleepFuture
pub fn sleep_until(deadline: Deadline) -> SleepFuture
```

1. **Minimum wait semantics (`tasks/0440 ATIMER-20..21`, `tasks/0464 ATIME-28`)**:
   - `sleep(d)` computes `deadline = Deadline.after_ns(d.as_nanos())` on construction (or first poll) and resolves to `Poll.Ready(())` on the first poll where `host.monotonic_ns() >= deadline.deadline_ns`.
   - If `deadline.is_expired()` is already `true` on initial poll, `SleepFuture.poll` returns `Poll.Ready(())` immediately without registering in `TimerWheel`.
   - Otherwise, `SleepFuture.poll(cx)` registers `(timer_id, deadline.deadline_ns, cx.waker().clone())` in the active `Reactor`'s `TimerWheel` and returns `Poll.Pending`.
2. **Timer cancellation on `Drop` (`tasks/0440 ATIMER-24`, `tasks/0464 ATIME-32..33`)**:
   - Dropping `SleepFuture` before it resolves to `Poll.Ready(())` removes or marks `cancelled = true` on `timer_id` in `TimerWheel` and drops its stored `Waker`, guaranteeing zero dangling wakeups (`ATIME-32..33`).

**AXS-AIO-022** (Periodic `Interval`, schedule mode, and `MissedTickBehavior` in `std/async/timer.ax`; `T426`, `REQ-ASY-159`, `tasks/0440 ATIMER-25..26`, `tasks/0464 §205.6–8, §205.100 ATIME-29..31`).
To satisfy `REQ-ASY-159` (`ATIME-29..31`), periodic timers explicitly distinguish fixed-rate vs fixed-delay scheduling and declare an explicit missed-tick policy:

```axiom
@derive(Copy, Clone, Eq, PartialEq)
pub enum IntervalMode {
    FixedRate,
    FixedDelay,
}

@derive(Copy, Clone, Eq, PartialEq)
pub enum MissedTickBehavior {
    Burst,
    Skip,
    Delay,
}

pub struct Interval {
    period_ns: u64,
    next_tick_ns: u64,
    mode: IntervalMode,
    missed_policy: MissedTickBehavior,
}

impl Interval {
    pub fn every_ns(period_ns: u64) -> Interval
    pub fn every_ms(period_ms: u64) -> Interval
    pub fn with_mode(self, mode: IntervalMode) -> Interval
    pub fn with_missed_tick_behavior(self, policy: MissedTickBehavior) -> Interval
    pub fn mode(self: view<Interval>) -> IntervalMode
    pub fn missed_tick_behavior(self: view<Interval>) -> MissedTickBehavior
    pub fn reset(self: mut_view<Interval>)
    pub fn tick(self: mut_view<Interval>) -> SleepFuture
}
```

1. **Schedule mode (`IntervalMode`, `REQ-ASY-159`, `ATIME-29..30`)**:
   - `IntervalMode.FixedRate` (default): Targets an drift-free cadence $t_0, t_0 + P, t_0 + 2P, \dots$ anchored at the initial schedule origin.
   - `IntervalMode.FixedDelay`: Schedules each subsequent tick at `now_ns + period_ns` measured from when `tick()` is called after the previous tick completes.
2. **Explicit missed-tick policies (`MissedTickBehavior`, `REQ-ASY-159`, `ATIME-31`)**:
   When `now_ns >= next_tick_ns + period_ns` (one or more ticks were missed because the task was busy):
   - `MissedTickBehavior.Burst` (default): `tick()` fires immediately for each missed tick (`next_tick_ns = next_tick_ns + period_ns`) until caught up with `now_ns`.
   - `MissedTickBehavior.Skip`: Skips all missed intermediate ticks and advances `next_tick_ns` to the next future multiple $t_0 + k \cdot P > \text{now\_ns}$ aligned to the original phase.
   - `MissedTickBehavior.Delay`: Shifts the phase origin to `now_ns`, setting `next_tick_ns = now_ns + period_ns`.

**AXS-AIO-023** (`Deadline` and `Timeout<F>` integration with the reactor timer wheel; `T426`, `T428`, `REQ-ASY-153`, `REQ-ASY-159`, `SPEC-34 AXS-EXEC-024`, `tasks/0440 ATIME-32..33, ATIMEOUT-20..24`, `tasks/0464 §205.76–77 ATIME-26..27`).
1. **Wakeup registration on `Timeout<F>` (`SPEC-34 AXS-EXEC-024`, `T426`)**:
   - When `Timeout<F>.poll(cx)` polls the inner future `self.fut` and `self.fut` returns `Poll.Pending`:
     - If `self.deadline.is_expired()` is `true`, `Timeout<F>` immediately returns `Poll.Ready(Result.Err(TimeoutError {}))`.
     - Otherwise, `Timeout<F>` registers `cx.waker().clone()` at `self.deadline.deadline_ns` in the active `Reactor`'s `TimerWheel`. Thus, if `self.fut` (such as a blocked `stream.read(...)` or `channel.recv()`) never wakes before `self.deadline`, the `TimerWheel` wakes the task at `self.deadline.deadline_ns`, causing `Timeout<F>.poll` to run again, observe `is_expired() == true`, return `Result.Err(TimeoutError {})`, and drop `self.fut` (which in turn triggers `AXS-AIO-005` `CancelIoEx` on the in-flight I/O operation).
2. **Distinction between `TimeoutError` and `CancellationToken` (`REQ-ASY-153`, `REQ-ASY-159`, `ATIMEOUT-20..21`)**:
   - Expiring a `Deadline` / `Timeout<F>` produces a value-level `Result.Err(TimeoutError {})` (or `IoError.TimedOut`) in the awaiting task without implicitly cancelling unrelated sibling tasks in the enclosing `TaskGroup`.
   - Nested operations propagate budgets via `effective_deadline = parent_deadline.min(child_deadline)` (`REQ-ASY-153`, `ATIME-33`).

---

## 4. Unified `AsyncRead` / `AsyncWrite` Traits & `AsyncFile` (`std.io`, `std.fs`)

**AXS-AIO-030** (Extended `IoError` taxonomy for async, timer, and network operations in `std/io/io.ax` and `std/io/async_io.ax`; `T426`, `T427`, `0221 §33–34, §42 AIO-32, AIO-37`, `tasks/0335 §100 AIO-97..98`, `tasks/0441 §182.139–142`).
To represent asynchronous cancellation, timeouts, and network transport failures while preserving underlying host error codes (`AIO-37`, `AIO-97..98`), `std.io.IoError` (`std/io/io.ax`, locked by `T427`) is extended as an append-only enum:

```axiom
@derive(Copy, Clone, Eq, PartialEq)
pub enum IoError {
    NotFound,
    PermissionDenied,
    AlreadyExists,
    InvalidHandle,
    InvalidData,
    TimedOut,
    Cancelled,
    ConnectionRefused,
    ConnectionReset,
    BrokenPipe,
    AddrInUse,
    UnexpectedEof,
    Other(i64),
}
```

1. **Standardized negative host error mapping (`io_error_from_code(code: i64) -> IoError`)**:
   - `-1` → `IoError.NotFound`
   - `-2` → `IoError.PermissionDenied`
   - `-3` → `IoError.AlreadyExists`
   - `-4` → `IoError.InvalidHandle`
   - `-5` → `IoError.TimedOut`
   - `-6` → `IoError.Cancelled` (`ERROR_OPERATION_ABORTED = 995` on Windows IOCP)
   - `-7` → `IoError.ConnectionRefused` (`WSAECONNREFUSED = 10061`)
   - `-8` → `IoError.ConnectionReset` (`WSAECONNRESET = 10054`)
   - `-9` → `IoError.Other(-9)`
   - `-10` → `IoError.BrokenPipe` (`ERROR_BROKEN_PIPE = 109` / `WSAECONNABORTED = 10053`)
   - `-11` → `IoError.AddrInUse` (`WSAEADDRINUSE = 10048`)
   - Any other `< 0` code `c` → `IoError.Other(c)`.
2. **`WouldBlock` encapsulation (`0221 §34 AIO-32`)**:
   - Low-level non-blocking readiness checks (`WSAEWOULDBLOCK` / `EAGAIN` / `ERROR_IO_PENDING`) are handled inside the `Reactor` and `Future.poll` state machine by registering the caller's `Waker` and returning `Poll.Pending`; high-level `AsyncRead`/`AsyncWrite` callers never have to spin on `WouldBlock`.

**AXS-AIO-031** (`AsyncRead` and `AsyncWrite` traits and helper futures in `std/io/async_io.ax`; `T427`, `0221 §10, §29–32`, `tasks/0438 AIO-25`).
Module `std.io.async_io` (`std/io/async_io.ax`) defines the unified byte-stream traits and helper operations:

```axiom
pub struct AsyncReadBufFuture {
    reactor_handle: i64,
    op_id: IoOpId,
}

pub struct AsyncWriteBufFuture {
    reactor_handle: i64,
    op_id: IoOpId,
}

pub struct AsyncReadSliceFuture {
    reactor_handle: i64,
    op_id: IoOpId,
    dst_ptr: *mut u8,
    dst_cap: usize,
}

pub struct AsyncWriteSliceFuture {
    reactor_handle: i64,
    op_id: IoOpId,
}

pub trait AsyncRead {
    fn read_buf(self: mut_view<Self>, buf: IoBuf) -> AsyncReadBufFuture
    fn read(self: mut_view<Self>, dst: *mut u8, cap: usize) -> AsyncReadSliceFuture
}

pub trait AsyncWrite {
    fn write_buf(self: mut_view<Self>, buf: IoBuf) -> AsyncWriteBufFuture
    fn write(self: mut_view<Self>, src: *const u8, count: usize) -> AsyncWriteSliceFuture
}

pub async fn read_exact<R: AsyncRead>(reader: mut_view<R>, dst: *mut u8, len: usize) -> Result<(), IoError>
pub async fn write_all<W: AsyncWrite>(writer: mut_view<W>, src: *const u8, len: usize) -> Result<(), IoError>
```

1. **Partial read/write representation (`tasks/0335 §35 AIO-60`, `tasks/0438 AIO-25`)**:
   - `read` / `read_buf` resolves to `0` bytes only when the stream reaches end-of-file (`EOF`) or when `cap == 0`; otherwise it returns `1..=cap` bytes transferred in a single OS completion.
   - `read_exact` loops over `read` until exactly `len` bytes are filled, or returns `Result.Err(IoError.UnexpectedEof)` if `read` returns `0` before `len` bytes arrive.
   - `write_all` loops over `write` until all `len` bytes are written, or returns `Result.Err(IoError.BrokenPipe)` if `write` returns `0`.

**AXS-AIO-032** (`AsyncFile` resource ownership and positional/cursor overlapped I/O in `std/fs/async_file.ax`; `T427`, `0221 §19–20, §39 AIO-38..39`, `tasks/0335 §5–25, §100 AIO-41..48`).
Module `std.fs.async_file` (`std/fs/async_file.ax`) provides asynchronous file operations bound to a `Reactor`:

```axiom
pub struct AsyncFile {
    reactor_handle: i64,
    handle: i64,
    cursor: u64,
    is_open: bool,
}

impl AsyncFile {
    pub fn open(reactor: view<Reactor>, path: Str) -> Result<AsyncFile, IoError>
    pub fn create(reactor: view<Reactor>, path: Str) -> Result<AsyncFile, IoError>
    pub fn open_rw(reactor: view<Reactor>, path: Str) -> Result<AsyncFile, IoError>
    pub fn read_at(self: view<AsyncFile>, offset: u64, dst: *mut u8, cap: usize) -> AsyncReadSliceFuture
    pub fn write_at(self: view<AsyncFile>, offset: u64, src: *const u8, count: usize) -> AsyncWriteSliceFuture
    pub fn read_buf_at(self: view<AsyncFile>, offset: u64, buf: IoBuf) -> AsyncReadBufFuture
    pub fn write_buf_at(self: view<AsyncFile>, offset: u64, buf: IoBuf) -> AsyncWriteBufFuture
    pub async fn read_all_at(self: view<AsyncFile>, offset: u64, len: usize) -> Result<IoBuf, IoError>
    pub async fn write_all_at(self: view<AsyncFile>, offset: u64, data: view<[u8]>) -> Result<(), IoError>
    pub fn flush(self: view<AsyncFile>) -> AsyncFlushFuture
    pub fn file_size(self: view<AsyncFile>) -> Result<u64, IoError>
    pub async fn close(self) -> Result<(), IoError>
}
```

1. **Concurrent positional I/O via `view<AsyncFile>` (`tasks/0335 §16–17 AIO-43`, `tasks/0438 §179.96 AIOOPT-22`)**:
   - Because Windows IOCP `OVERLAPPED` (`Offset`, `OffsetHigh`) and Linux `io_uring` `IORING_OP_READ`/`WRITE` carry an explicit 64-bit file offset per operation rather than mutating a kernel-global file cursor, `read_at`, `write_at`, `read_buf_at`, and `write_buf_at` take `self: view<AsyncFile>`.
   - Multiple tasks (or concurrent futures in a `TaskGroup`) holding `view<AsyncFile>` MAY issue overlapped positional reads and writes to disjoint file offsets simultaneously without locking (`AIO-43`, `AIOOPT-22`).
   - Sequential `AsyncRead` / `AsyncWrite` implementations on `AsyncFile` take `self: mut_view<AsyncFile>` and advance `self.cursor` by the completed byte count.
2. **`Send` and `Share` properties (`tasks/0335 AIO-75`)**:
   - `AsyncFile` implements `Send` and `Share` (its OS handle is associated with the completion port and positional operations are kernel-atomic with respect to handle state).

**AXS-AIO-033** (Explicit fallible `AsyncFile.close(self).await` vs non-fallible deterministic `Drop`; `T427`, `tasks/0335 §9–15, §100 AIO-31..37, AIO-44..45`).
1. **Fallible cleanup via `close(self).await -> Result<(), IoError>` (`tasks/0335 AIO-33..36`)**:
   - Calling `file.close().await` consumes `AsyncFile` by value (`Move`), flushes pending state if requested, invokes `host.aio_close(self.reactor_handle, self.handle)`, marks `self.is_open = false`, and returns `Result<(), IoError>` so the application can observe and handle close/flush errors (`AIO-33, AIO-35`).
   - Because `close(self)` consumes ownership of `AsyncFile`, the compiler statically prevents any subsequent use or double-close (`AIO-36`).
2. **Non-fallible deterministic `Drop` (`tasks/0335 AIO-31..32, AIO-34, AIO-37`)**:
   - If an `AsyncFile` goes out of scope without `close().await` having been called (`self.is_open == true`), `Drop.drop(self: mut_view<AsyncFile>)` invokes `host.aio_close(self.reactor_handle, self.handle)` to cancel any remaining in-flight operations and release the OS handle without panicking or propagating recoverable errors (`AIO-32, AIO-37`).

---

## 5. Asynchronous Networking (`std.net`): `AsyncTcpListener`, `AsyncTcpStream` (`split()`), & `AsyncUdpSocket`

**AXS-AIO-040** (Network endpoint types `Ipv4Addr` and `SocketAddr` in `std/net/mod.ax`; `T427`, `tasks/0335 §29–36 AIO-56..63`, `tasks/0441 §182.201 ANET-20..25, ANET-30..31, ANET-70..72`, `tasks/0461 ANET-20..22, ANET-32..36`).
Module `std.net` (`std/net/mod.ax`) defines portable endpoint types and byte-stream/datagram socket resources:

```axiom
@derive(Copy, Clone, Eq, PartialEq, Hash)
pub struct Ipv4Addr {
    pub octets: [4]u8,
}

@derive(Copy, Clone, Eq, PartialEq, Hash)
pub struct SocketAddr {
    pub ip: Ipv4Addr,
    pub port: u16,
}

impl Ipv4Addr {
    pub fn new(a: u8, b: u8, c: u8, d: u8) -> Ipv4Addr
    pub fn localhost() -> Ipv4Addr
    pub fn unspecified() -> Ipv4Addr
    pub fn to_u32_be(self) -> u32
    pub fn from_u32_be(bits: u32) -> Ipv4Addr
}

impl SocketAddr {
    pub fn new(ip: Ipv4Addr, port: u16) -> SocketAddr
    pub fn localhost(port: u16) -> SocketAddr
}
```

1. **Byte-oriented payloads and explicit wire framing (`tasks/0441 ANET-30..31, ANET-70..72`, `tasks/0461 ANET-32..36`)**:
   - Network sockets transmit raw bytes (`u8`, `IoBuf`), never implicit UTF-8 strings (`ANET-30..31`).
   - TCP (`AsyncTcpStream`) is a byte stream without built-in message boundaries (`ANET-70`, `tasks/0461 ANET-35`); application framing (length-prefixed, delimiter-based) is an explicit protocol concern (`ANET-72`, `tasks/0461 ANET-34`).
   - UDP (`AsyncUdpSocket`) preserves discrete datagram boundaries (`ANET-71`, `tasks/0461 ANET-36`).

**AXS-AIO-041** (`AsyncTcpListener` in `std/net/mod.ax`; `T427`, `tasks/0335 §32 AIO-59`, `tasks/0441 §182.131–133 ANET-61`).
`AsyncTcpListener` represents an owned listening TCP socket bound to a local `SocketAddr`:

```axiom
pub struct AsyncTcpListener {
    reactor_handle: i64,
    handle: i64,
    local: SocketAddr,
    is_open: bool,
}

pub struct AcceptFuture {
    reactor_handle: i64,
    op_id: IoOpId,
}

impl AsyncTcpListener {
    pub fn bind(reactor: view<Reactor>, addr: SocketAddr) -> Result<AsyncTcpListener, IoError>
    pub fn local_addr(self: view<AsyncTcpListener>) -> SocketAddr
    pub fn accept(self: view<AsyncTcpListener>) -> AcceptFuture
    pub fn close(self) -> Result<(), IoError>
}
```

1. **Ephemeral port resolution**: Binding to `SocketAddr.localhost(0u16)` requests an OS-assigned ephemeral port; `AsyncTcpListener.bind` queries `host.aio_socket_local_port(handle)` and stores the resolved `SocketAddr` in `self.local` so `listener.local_addr()` always returns the actual bound port.
2. **Ownership transfer on `accept().await` (`tasks/0441 §182.132–133 ANET-61`)**:
   - `AcceptFuture` implements `Future<Output = Result<(AsyncTcpStream, SocketAddr), IoError>>`.
   - Each accepted `AsyncTcpStream` is an independent owned resource (`Send`) already associated with the `Reactor`, allowing it to be moved directly into `executor.spawn(...)` or `group.spawn(...)` without `Arc` overhead (`tasks/0441 §182.133`).

**AXS-AIO-042** (`AsyncTcpStream` in `std/net/mod.ax` & prohibition of unsynchronized concurrent mutation; `T427`, `REQ-CONC-152`, `tasks/0335 §31, §35 AIO-58, AIO-60`, `tasks/0441 §182.108–109, §182.201 ANET-60..62, ANET-70`).
`AsyncTcpStream` represents a connected TCP byte stream:

```axiom
@derive(Copy, Clone, Eq, PartialEq)
pub enum ShutdownMode {
    Read,
    Write,
    Both,
}

pub struct AsyncTcpStream {
    reactor_handle: i64,
    handle: i64,
    peer: SocketAddr,
    is_open: bool,
}

impl AsyncTcpStream {
    pub fn connect(reactor: view<Reactor>, addr: SocketAddr) -> ConnectFuture
    pub fn peer_addr(self: view<AsyncTcpStream>) -> SocketAddr
    pub fn read(self: mut_view<AsyncTcpStream>, dst: *mut u8, cap: usize) -> AsyncReadSliceFuture
    pub fn write(self: mut_view<AsyncTcpStream>, src: *const u8, count: usize) -> AsyncWriteSliceFuture
    pub fn read_buf(self: mut_view<AsyncTcpStream>, buf: IoBuf) -> AsyncReadBufFuture
    pub fn write_buf(self: mut_view<AsyncTcpStream>, buf: IoBuf) -> AsyncWriteBufFuture
    pub async fn read_exact(self: mut_view<AsyncTcpStream>, dst: *mut u8, len: usize) -> Result<(), IoError>
    pub async fn write_all(self: mut_view<AsyncTcpStream>, src: *const u8, len: usize) -> Result<(), IoError>
    pub fn shutdown(self: view<AsyncTcpStream>, how: ShutdownMode) -> Result<(), IoError>
    pub fn split(self) -> (TcpReadHalf, TcpWriteHalf)
    pub fn close(self) -> Result<(), IoError>
}
```

1. **No unsynchronized concurrent mutation on unsplit `AsyncTcpStream` (`REQ-CONC-152`, `tasks/0441 ANET-62`)**:
   - `AsyncTcpStream` implements `Send` (ownership can move between tasks), but its `read`, `write`, `read_buf`, and `write_buf` methods require exclusive `self: mut_view<AsyncTcpStream>` capability.
   - Consequently, two tasks cannot concurrently call `read` and `write` on the same unsplit `AsyncTcpStream` without either synchronizing via `AsyncMutex<AsyncTcpStream>` or splitting the stream into directional capabilities via `stream.split()` (`REQ-CONC-152`).
2. **Protocol shutdown vs resource close (`tasks/0335 §31 AIO-58`)**:
   - `stream.shutdown(ShutdownMode.Write)` sends a TCP FIN (half-close) on the wire while keeping the socket handle valid for reading until the resource is closed or dropped (`AIO-58`).

**AXS-AIO-043** (Full-duplex capability splitting `AsyncTcpStream.split(self) -> (TcpReadHalf, TcpWriteHalf)` and `rejoin`; `T427`, `REQ-CONC-152`, `tasks/0441 §182.108–110, §182.134–135, §182.201 ANET-62`).
To enable concurrent full-duplex reading and writing on a single TCP connection across two tasks without mutex contention (`REQ-CONC-152`, `tasks/0441 §182.109, §182.135`):

```axiom
pub struct TcpReadHalf {
    inner: Arc<TcpStreamShared>,
}

pub struct TcpWriteHalf {
    inner: Arc<TcpStreamShared>,
}

impl TcpReadHalf {
    pub fn read(self: mut_view<TcpReadHalf>, dst: *mut u8, cap: usize) -> AsyncReadSliceFuture
    pub fn read_buf(self: mut_view<TcpReadHalf>, buf: IoBuf) -> AsyncReadBufFuture
    pub async fn read_exact(self: mut_view<TcpReadHalf>, dst: *mut u8, len: usize) -> Result<(), IoError>
}

impl TcpWriteHalf {
    pub fn write(self: mut_view<TcpWriteHalf>, src: *const u8, count: usize) -> AsyncWriteSliceFuture
    pub fn write_buf(self: mut_view<TcpWriteHalf>, buf: IoBuf) -> AsyncWriteBufFuture
    pub async fn write_all(self: mut_view<TcpWriteHalf>, src: *const u8, len: usize) -> Result<(), IoError>
    pub fn shutdown_write(self: mut_view<TcpWriteHalf>) -> Result<(), IoError>
}

pub fn tcp_rejoin(read_half: TcpReadHalf, write_half: TcpWriteHalf) -> Result<AsyncTcpStream, IoError>
```

1. **Directional capability isolation (`REQ-CONC-152`, `ANET-62`)**:
   - `stream.split()` consumes `AsyncTcpStream` by value (`Move`) and returns `(TcpReadHalf, TcpWriteHalf)`.
   - `TcpReadHalf` is `!Copy`, `Send` (and implements `AsyncRead`), exposing **only** receive operations (`read`, `read_buf`, `read_exact`) requiring `mut_view<TcpReadHalf>`. Thus at most one read operation can be issued through `TcpReadHalf` at a time.
   - `TcpWriteHalf` is `!Copy`, `Send` (and implements `AsyncWrite`), exposing **only** transmit and write-half shutdown operations (`write`, `write_buf`, `write_all`, `shutdown_write`) requiring `mut_view<TcpWriteHalf>`. Thus at most one write operation can be issued through `TcpWriteHalf` at a time.
   - Because OS TCP sockets have independent kernel receive and send queues, a reader task owning `TcpReadHalf` and a writer task owning `TcpWriteHalf` execute in parallel with zero data races (`REQ-CONC-152`).
2. **Shared handle lifetime & `tcp_rejoin` (`tasks/0441 §182.110`)**:
   - The underlying OS socket handle inside `TcpStreamShared` remains open until **both** `TcpReadHalf` and `TcpWriteHalf` are dropped (when `Arc<TcpStreamShared>` strong count reaches `0`, its `Drop` calls `host.aio_close`), or until both halves are reunited via `tcp_rejoin(read_half, write_half)` (which verifies both halves belong to the same stream handle and returns the reconstructed `AsyncTcpStream`).

**AXS-AIO-044** (`AsyncUdpSocket` in `std/net/mod.ax`; `T427`, `tasks/0441 §182.201 ANET-71`, `tasks/0461 ANET-36`).
`AsyncUdpSocket` provides connectionless asynchronous datagram I/O:

```axiom
pub struct AsyncUdpSocket {
    reactor_handle: i64,
    handle: i64,
    local: SocketAddr,
    is_open: bool,
}

pub struct UdpRecvFromFuture {
    reactor_handle: i64,
    op_id: IoOpId,
    dst_ptr: *mut u8,
    dst_cap: usize,
}

pub struct UdpSendToFuture {
    reactor_handle: i64,
    op_id: IoOpId,
}

impl AsyncUdpSocket {
    pub fn bind(reactor: view<Reactor>, addr: SocketAddr) -> Result<AsyncUdpSocket, IoError>
    pub fn local_addr(self: view<AsyncUdpSocket>) -> SocketAddr
    pub fn send_to(self: view<AsyncUdpSocket>, src: *const u8, len: usize, target: SocketAddr) -> UdpSendToFuture
    pub fn recv_from(self: view<AsyncUdpSocket>, dst: *mut u8, cap: usize) -> UdpRecvFromFuture
    pub fn close(self) -> Result<(), IoError>
}
```

1. **Datagram boundary preservation (`ANET-71`, `tasks/0461 ANET-36`)**:
   - `UdpSendToFuture` implements `Future<Output = Result<usize, IoError>>` and transmits a single UDP datagram to `target`.
   - `UdpRecvFromFuture` implements `Future<Output = Result<(usize, SocketAddr), IoError>>` and receives a single UDP datagram along with the sender's `SocketAddr` decoded from the completion packet's `aux` word (`(ip_u32 << 16) | port_u16`).

---

## 6. Host Interface Intrinsics (`host.aio_*`), Memory Ordering & Conformance Contract

**AXS-AIO-050** (Host-interface intrinsics `host.aio_*` in `std/core/host.ax` and `SPEC-04 §11`; `T426`, `T427`, `SPEC-04 AXS-EXT-110, AXS-EXT-130`).
Task `T426` appends the following 20 `host.aio_*` intrinsics to `std/core/host.ax`, wires their `IntrinsicId` entries in `compiler/types/typeck.ax`, `compiler/lir/builder.ax`, and `compiler/interp/oracle.ax`, and implements their native Windows x64 IOCP + Winsock2 backend in `std/sys/windows/iocp.ax` (`T426` / `T427`):

| Intrinsic | Signature in `std/core/host.ax` | Semantics & Return Convention |
|---|---|---|
| `aio_create` | `pub fn aio_create() -> i64` | Creates an OS completion port / reactor (`>= 1` handle; `< 0` negated `IoError`). |
| `aio_destroy` | `pub fn aio_destroy(reactor: i64) -> i64` | Closes the reactor handle (`0` success, `< 0` error). |
| `aio_wake` | `pub fn aio_wake(reactor: i64) -> i64` | Posts an explicit wakeup packet (`PostQueuedCompletionStatus`) to unblock `aio_wait` (`0` success, `< 0` error). |
| `aio_wait` | `pub unsafe fn aio_wait(reactor: i64, events_out: *mut u64, max_events: usize, timeout_ns: i64) -> i64` | Waits up to `timeout_ns` (`< 0` infinite, `0` poll, `> 0` ns) and writes up to `max_events` triples `(op_id, result_i64_bits, aux)` into `events_out`. Returns event count `>= 0`, or `< 0` error. |
| `aio_cancel` | `pub fn aio_cancel(reactor: i64, op_id: u64) -> i64` | Initiates `CancelIoEx` on in-flight `op_id`. Buffer stays pinned until `aio_wait` reaps `op_id`. Returns `0` success, `< 0` error. |
| `aio_file_open` | `pub unsafe fn aio_file_open(reactor: i64, path: *const u8, path_len: usize, mode: u32) -> i64` | Opens file with `FILE_FLAG_OVERLAPPED` (`0` read, `1` create+write, `2` append, `3` rw+create) and binds to `reactor` (`>= 1` handle, `< 0` error). |
| `aio_submit_read_at` | `pub unsafe fn aio_submit_read_at(reactor: i64, handle: i64, offset: u64, buf: *mut u8, len: usize) -> i64` | Submits overlapped `ReadFile` at `offset` into reactor-pinned `buf`. Returns `op_id >= 1` (`< 0` error). |
| `aio_submit_write_at` | `pub unsafe fn aio_submit_write_at(reactor: i64, handle: i64, offset: u64, buf: *const u8, len: usize) -> i64` | Submits overlapped `WriteFile` at `offset` from reactor-pinned `buf`. Returns `op_id >= 1` (`< 0` error). |
| `aio_submit_flush` | `pub fn aio_submit_flush(reactor: i64, handle: i64) -> i64` | Submits asynchronous file flush (`FlushFileBuffers`). Returns `op_id >= 1` (`< 0` error). |
| `aio_tcp_bind` | `pub fn aio_tcp_bind(reactor: i64, addr_ipv4: u32, port: u16) -> i64` | Creates overlapped TCP listener bound to `(addr_ipv4, port)` (`listen`) and associates with `reactor` (`>= 1` handle, `< 0` error). |
| `aio_socket_local_port` | `pub fn aio_socket_local_port(handle: i64) -> i64` | Returns bound local port `1..65535` via `getsockname` (`< 0` error). |
| `aio_submit_accept` | `pub fn aio_submit_accept(reactor: i64, listener: i64) -> i64` | Submits overlapped `AcceptEx`. Completion `result` = stream handle `>= 1`, `aux = (peer_ip << 16) \| peer_port`. Returns `op_id >= 1`. |
| `aio_submit_connect` | `pub fn aio_submit_connect(reactor: i64, addr_ipv4: u32, port: u16) -> i64` | Creates overlapped TCP socket and submits `ConnectEx` to `(addr_ipv4, port)`. Completion `result` = connected stream handle `>= 1`. Returns `op_id >= 1`. |
| `aio_submit_recv` | `pub unsafe fn aio_submit_recv(reactor: i64, stream: i64, buf: *mut u8, len: usize) -> i64` | Submits overlapped `WSARecv` into reactor-pinned `buf`. Completion `result` = bytes read (`0` EOF). Returns `op_id >= 1`. |
| `aio_submit_send` | `pub unsafe fn aio_submit_send(reactor: i64, stream: i64, buf: *const u8, len: usize) -> i64` | Submits overlapped `WSASend` from reactor-pinned `buf`. Completion `result` = bytes sent. Returns `op_id >= 1`. |
| `aio_tcp_shutdown` | `pub fn aio_tcp_shutdown(stream: i64, how: u32) -> i64` | Shuts down TCP stream (`0` read, `1` write, `2` both; `0` success, `< 0` error). |
| `aio_udp_bind` | `pub fn aio_udp_bind(reactor: i64, addr_ipv4: u32, port: u16) -> i64` | Creates overlapped UDP socket bound to `(addr_ipv4, port)` and associates with `reactor` (`>= 1` handle, `< 0` error). |
| `aio_submit_recv_from` | `pub unsafe fn aio_submit_recv_from(reactor: i64, sock: i64, buf: *mut u8, len: usize) -> i64` | Submits overlapped `WSARecvFrom`. Completion `result` = bytes read, `aux = (peer_ip << 16) \| peer_port`. Returns `op_id >= 1`. |
| `aio_submit_send_to` | `pub unsafe fn aio_submit_send_to(reactor: i64, sock: i64, buf: *const u8, len: usize, addr_ipv4: u32, port: u16) -> i64` | Submits overlapped `WSASendTo` to `(addr_ipv4, port)`. Completion `result` = bytes sent. Returns `op_id >= 1`. |
| `aio_close` | `pub fn aio_close(reactor: i64, handle: i64) -> i64` | Cancels remaining in-flight ops on `handle` and closes the OS file/socket handle (`0` success, `< 0` error). |

**AXS-AIO-051** (Memory ordering & `Happens-Before` rules across async I/O and timers; `tasks/0438 AIOASYNC-25`, `tasks/0440 §181.110–111, §181.152 ATIME-25, ATIMER-23, ATIMEOUT-24`, `tasks/0441 ANET-63`, `SPEC-30 AXS-CONC-042`).
1. **Completion publication of I/O buffer contents (`SPEC-30 AXS-CONC-042`)**:
   - Submitting an `IoBuf` to `host.aio_submit_*` happens-before the kernel reads/writes the buffer; the kernel completion reaped by `host.aio_wait` (`Release`) synchronizes-with the `Waker.wake()` (`AcqRel` on `TaskHeader.state`, `SPEC-34 AXS-EXEC-004`) and happens-before the resumed task reads the completed `IoBuf`.
2. **Passage of time is never a memory synchronization primitive (`tasks/0438 AIOASYNC-25`, `tasks/0440 ATIME-25, ATIMER-23, ATIMEOUT-24`, `tasks/0441 ANET-63`)**:
   - Calling `host.monotonic_ns()`, `sleep(d).await`, `Interval.tick().await`, or observing a `TimeoutError` does **not** establish a `Happens-Before` edge between unrelated tasks or threads (`ATIME-25`, `ATIMER-23`). All inter-task shared-memory visibility must use explicit synchronization (`Atomic<T>`, `AsyncMutex<T>`, channels, or `TaskHandle.join`).

**AXS-AIO-052** (`E11.6` Conformance Verification Contract for `T426`, `T427`, and `T428`).
1. **`T426` (`tests/std/async/reactor/*.ax`)**: Verifies `Reactor` IOCP completion wakeup, `TimerWheel` ordering across 100+ concurrent `sleep` timers with zero extra OS threads (`REQ-ASY-154`), `Interval` `FixedRate`/`FixedDelay` and `MissedTickBehavior` (`Burst`, `Skip`, `Delay`, `REQ-ASY-159`), `Timeout<F>` expiration (`REQ-ASY-153`), and `CancellingZombie` buffer retention when an in-flight operation's `Future` is dropped before completion (`REQ-ASY-158`).
2. **`T427` (`tests/std/async/io/*.ax`)**: Verifies `IoBuf` hand-off (`REQ-ASY-152, 157`), concurrent positional `AsyncFile` `read_at`/`write_at` and explicit `close().await`, loopback `AsyncTcpListener`/`AsyncTcpStream` request/response, full-duplex concurrent read/write via `stream.split()` (`REQ-CONC-152`), `AsyncUdpSocket` `send_to`/`recv_from`, and cancellation/timeout of blocked socket reads.
3. **`T428` (`tests/conformance/p11/e11_6_async_io/*.ax`)**: End-to-end conformance suite running in `[interp]`, `[native]`, and `[native-O1]` verifying multi-task `AsyncFile` pipelines, multi-client loopback TCP framing with `split()` halves, UDP burst exchange, `Timeout` + `CancellationToken` cancellation of in-flight I/O (`REQ-ASY-155`), and registered/in-flight buffer reuse governance (`REQ-CONC-153`).

---

## 7. Canonical Axiom Examples

### 7.1 Positive Example 1: `AsyncFile` Overlapped Positional Write & Read with `IoBuf` Ownership Hand-Off (`AXS-AIO-011`, `AXS-AIO-032`, `AXS-AIO-033`)
```axiom
module example.async_file_iobuf

use std.async.LocalExecutor
use std.io.async_io.IoBuf
use std.fs.async_file.AsyncFile

pub fn main() -> i32 {
    let mut exec = LocalExecutor.new()
    let code = exec.block_on(async {
        let reactor = exec.reactor()
        let f_w = match AsyncFile.create(reactor, "build/aio_demo.bin") {
            Result.Ok(f) => f,
            Result.Err(_) => return 1i32,
        }

        let payload = IoBuf.from_slice(view("AXIOM-AIO"))
        let w_out = f_w.write_buf_at(0u64, payload).await
        match w_out.res {
            Result.Ok(n) => {
                if n != 9usize { return 2i32 }
            }
            Result.Err(_) => return 3i32,
        }
        match f_w.close().await {
            Result.Ok(_) => {}
            Result.Err(_) => return 4i32,
        }

        let f_r = match AsyncFile.open(reactor, "build/aio_demo.bin") {
            Result.Ok(f) => f,
            Result.Err(_) => return 5i32,
        }
        let r_buf = IoBuf.with_capacity(16usize)
        let r_out = f_r.read_buf_at(0u64, r_buf).await
        let _ = f_r.close().await
        match r_out.res {
            Result.Ok(n) => {
                if n == 9usize && r_out.buf.len() == 9usize {
                    return 0i32
                }
                return 6i32
            }
            Result.Err(_) => return 7i32,
        }
    })
    return code
}
```

### 7.2 Positive Example 2: Loopback `AsyncTcpListener` + `AsyncTcpStream.split()` Full-Duplex Concurrency (`AXS-AIO-041`..`AXS-AIO-043`, `REQ-CONC-152`)
```axiom
module example.async_tcp_split_echo

use std.async.(LocalExecutor, with_timeout_ms)
use std.io.async_io.IoBuf
use std.net.(SocketAddr, AsyncTcpListener, AsyncTcpStream)

pub fn main() -> i32 {
    let mut exec = LocalExecutor.new()
    let status = exec.block_on(async {
        let reactor = exec.reactor()
        let listener = match AsyncTcpListener.bind(reactor, SocketAddr.localhost(0u16)) {
            Result.Ok(l) => l,
            Result.Err(_) => return 1i32,
        }
        let bind_addr = listener.local_addr()

        let server_task = exec.spawn_local(async {
            let (stream, _peer) = match listener.accept().await {
                Result.Ok(pair) => pair,
                Result.Err(_) => return 10i32,
            }
            let (mut r_half, mut w_half) = stream.split()
            let r_out = r_half.read_buf(IoBuf.with_capacity(64usize)).await
            match r_out.res {
                Result.Ok(n) => {
                    let w_out = w_half.write_buf(r_out.buf).await
                    match w_out.res {
                        Result.Ok(wn) => if wn == n { return 0i32 } else { return 11i32 },
                        Result.Err(_) => return 12i32,
                    }
                }
                Result.Err(_) => return 13i32,
            }
        })

        let client = match AsyncTcpStream.connect(reactor, bind_addr).await {
            Result.Ok(s) => s,
            Result.Err(_) => return 2i32,
        }
        let (mut cr, mut cw) = client.split()

        let send_task = exec.spawn_local(async {
            let out = cw.write_buf(IoBuf.from_slice(view("PING"))).await
            match out.res {
                Result.Ok(4usize) => return 0i32,
                _ => return 20i32,
            }
        })
        let recv_task = exec.spawn_local(async {
            let out = with_timeout_ms(1000u64, cr.read_buf(IoBuf.with_capacity(16usize))).await
            match out {
                Result.Ok(io_res) => match io_res.res {
                    Result.Ok(4usize) => return 0i32,
                    _ => return 21i32,
                },
                Result.Err(_) => return 22i32,
            }
        })

        let a = send_task.join().await
        let b = recv_task.join().await
        let c = server_task.join().await
        let _ = listener.close()
        return a + b + c
    })
    return status
}
```

### 7.3 Negative Example: Unsynchronized Concurrent Mutation of an Unsplit `AsyncTcpStream` (`REQ-CONC-152`, `AX_CONC_SHARED_MUT`)
```axiom
module example.reject_unsplit_socket_race

use std.async.LocalExecutor
use std.net.AsyncTcpStream
use std.io.async_io.IoBuf

pub fn reject_concurrent_unsplit_rw(exec: mut_view<LocalExecutor>, mut stream: AsyncTcpStream) {
    // Attempting to borrow `mut_view(stream)` simultaneously for both read and write
    // without calling `stream.split()` violates capability disjointness (`REQ-CONC-152`):
    let f_read = stream.read_buf(IoBuf.with_capacity(64usize))
    let f_write = stream.write_buf(IoBuf.from_slice(view("HELLO"))) // ERROR [AX_CONC_SHARED_MUT]: conflicting `mut_view<AsyncTcpStream>` capabilities
    let _ = f_read
    let _ = f_write
    let _ = exec
}
```

---

## 8. Requirement & Conformance Traceability Matrix

### 8.1 Primary Requirements Covered by `T425` (`covers:`)

| Requirement ID | Summary (`spec/requirements/CATALOG.md`) | Governing Rules in `SPEC-35` |
|---|---|---|
| `REQ-ASY-035` | Dropping a `Future` does not imply automatic cancellation of external OS or network operations, requiring explicit cooperative cancellation mechanisms. | `AXS-AIO-005`, `AXS-AIO-010`, `AXS-AIO-023` |
| `REQ-ASY-151` | Asynchronous I/O is represented as `Future`-based suspension without requiring thread creation, and operation completion occurs at most once. | `AXS-AIO-001`, `AXS-AIO-002`, `AXS-AIO-003` |

### 8.2 Downstream `E11.6` Implementation Requirements Specified by `SPEC-35`

| Consumer Task | Requirement IDs | Governing Rules in `SPEC-35` |
|---|---|---|
| `T426` (Windows IOCP reactor, timer wheel & oracle async I/O backend) | `REQ-ASY-153`, `REQ-ASY-154`, `REQ-ASY-158`, `REQ-ASY-159` | `AXS-AIO-003`..`AXS-AIO-007`, `AXS-AIO-020`..`AXS-AIO-023`, `AXS-AIO-050`..`AXS-AIO-052` |
| `T427` (Unified `AsyncRead`/`AsyncWrite`, `AsyncFile` & loopback `AsyncTcp`/`AsyncUdp` sockets) | `REQ-ASY-152`, `REQ-CONC-152`, `REQ-ASY-157` | `AXS-AIO-010`..`AXS-AIO-013`, `AXS-AIO-030`..`AXS-AIO-033`, `AXS-AIO-040`..`AXS-AIO-044` |
| `T428` (Async file, socket & timer conformance suite) | `REQ-ASY-155`, `REQ-CONC-153` | `AXS-AIO-002`, `AXS-AIO-005`, `AXS-AIO-010`, `AXS-AIO-014`, `AXS-AIO-052` |

---

## 9. Sources

- `spec/SPEC-04-core-extensibility.md` — `AXS-EXT-100` (intrinsic registry), `AXS-EXT-110` (host-interface intrinsics `host.aio_*`), `AXS-EXT-130` (`E11.6` extension points).
- `spec/SPEC-30-concurrency.md` — `AXS-CONC-001`..`AXS-CONC-050` (`Send`/`Share`, capability disjointness, `Happens-Before` memory model).
- `spec/SPEC-32-threads-sync.md` — `AXS-SYNC-001`..`AXS-SYNC-051` (`Arc<T>`, `std.sync` primitives).
- `spec/SPEC-33-async.md` — `AXS-ASY-001`..`AXS-ASY-052` (`Future<T>`, `Poll<T>`, `Waker`, `Context`, `AX_ASYNC_VIEW_ACROSS_AWAIT`, per-state cancellation `Drop` glue).
- `spec/SPEC-34-executors-fibers.md` — `AXS-EXEC-001`..`AXS-EXEC-056` (`LocalExecutor`, work-stealing `Executor`, `TaskGroup`, `CancellationToken`, `Deadline`, `Timeout<F>`, `ResourceGovernor`).
- `docs/base/specs/0221 - IO-ASYNC-001 — Unified IO Model.md` — §§1–45 (`AIO-20..40`: unified resource/buffer model, owned `IoBuf` vs scoped operations, Proactor/Reactor abstraction, cancellation memory safety, scatter/gather, DMA/mmap lifetimes).
- `docs/base/tasks/0335 - BOOTSTRAP-076 — Axiom IO, File, Socket, Process, OS Handle & Resource Model.md` — §§1–100 (`AIO-20..100`: resource ownership, non-fallible `Drop` vs explicit fallible `close()`, positional file I/O, socket shutdown vs close, in-flight buffer retention).
- `docs/base/tasks/0438 - BOOTSTRAP-179 — IO, File, Socket, Device, Zero-Copy & Unified Data Path.md` — §§179.1–179.100 (`AIO-20..29`, `AZCOPY-20..26`, `AIOASYNC-20..25`, `ADMA-20..25`, `AIOOPT-20..25`).
- `docs/base/tasks/0440 - BOOTSTRAP-181 — Time, Clock, Timer, Scheduling Time & Temporal Semantics.md` — §§181.1–181.152 (`ATIME-20..35`, `ATIMER-20..27`, `ATIMEOUT-20..24`, `ATIMETEST-20..24`).
- `docs/base/tasks/0441 - BOOTSTRAP-182 — Networking, Socket Model, Async IO & Zero-Copy Network Stack.md` — §§182.1–182.201 (`ANET-20..86`: socket ownership, `split()` read/write halves, TCP byte stream vs UDP datagram, cancellation race semantics).
- `docs/base/tasks/0461 - BOOTSTRAP-202 — Networking, Distributed Systems, RPC & High-Performance IO.md` — §§202.1–202.100 (`ANET-20..72`: completion-safe buffers without lifetime syntax, portable `io_uring`/`IOCP`/`epoll`/`kqueue` reactor contract, RDMA/DMA lifetime).
- `docs/base/tasks/0464 - BOOTSTRAP-205 — Time, Scheduling, Real-Time, Timers & Temporal Semantics.md` — §§205.1–205.100 (`ATIME-20..70`: `Deadline` vs cancellation, `Interval` fixed-rate vs fixed-delay, missed-tick policies, timer wheel coalescing).
- `docs/base/tasks/0465 - BOOTSTRAP-206 — Networking, Protocol Stack, Sockets, HTTP, QUIC & Zero-Copy IO.md` — §206.25 (`ANET2-46..47`: RDMA memory registration and completion-governed buffer reuse).
