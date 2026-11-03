# SPEC-34 — Async Executors (`LocalExecutor`, Work-Stealing `Executor`), Structured Concurrency (`TaskGroup`), Async Synchronization, `ResourceGovernor` & Stackful `Fiber` (`std.async`, `std.fiber`)

## Tóm tắt

Đặc tả chính tắc (`SPEC-34`) cho tầng thực thi bất đồng bộ và lập lịch của Axiom (`E11.5`): phân tách tuyệt đối giữa `Future<T>`, `Task` và `Executor`; khối điều khiển tác vụ nội xâm (`TaskControlBlock`) cùng máy trạng thái đánh thức nguyên tử (`IDLE`, `POLLING`, `NOTIFIED`, `COMPLETED`, `CANCELLED`, `PANICKED`); bộ thực thi đơn luồng `LocalExecutor` (`spawn_local` giữ tác vụ `!Send` cố định trên luồng tạo) và bộ thực thi đa luồng đánh cắp công việc `Executor` (`spawn` yêu cầu `F: Future + Send` và `F.Output: Send`); đồng thời có cấu trúc `TaskGroup`, hủy bỏ hợp tác `CancellationToken`, hạn chót `Deadline`/`Timeout`, bộ quản trị tài nguyên `ResourceGovernor`, các nguyên thủy đồng bộ hóa bất đồng bộ (`AsyncMutex<T>`, `AsyncRwLock<T>`, `AsyncSemaphore`, kênh async) và mô hình coroutine có ngăn xếp tường minh `Fiber<Y, R>` (`std.fiber` + `host.fiber_*`). Tài liệu này hợp nhất các quy tắc từ `docs/base/specs/0202`, `0204`, `0205` và các đặc tả tác vụ `0277`, `0278`, `0620`, `0621`, `0834`, `0835`, `0836`, nối tiếp `SPEC-30` (`E11.1`), `SPEC-31` (`E11.2`), `SPEC-32` (`E11.3`), `SPEC-33` (`E11.4`) và hợp đồng mở rộng lõi `SPEC-04` (`AXS-EXT-100`, `AXS-EXT-110`, `AXS-EXT-130`).
Các quyết định cốt lõi:
- **`Future`, `Task` và `Executor` hoàn toàn tách biệt; bộ lập lịch nằm ngoài lõi ngôn ngữ (`REQ-CONC-023`, `REQ-CONC-200`, `REQ-ASY-036`, `REQ-ASY-067`..`068`, `REQ-ASY-089`, `REQ-ASY-094`, `REQ-ASY-149`, `REQ-ASY-156`, `REQ-ASY-161`..`164`)**: `async fn` chỉ sinh máy trạng thái `Future<T>` thụ động (`SPEC-33`), toán tử `?` trong `async fn` chỉ là nhánh điều khiển sớm không chạm tới executor (`REQ-ASY-094`), và chỉ khi gọi `spawn` / `spawn_local` thì `Future` mới được gắn vào một `Task` thuộc quyền quản lý của `Executor` thư viện (`std.async`). Các chương trình không dùng `std.async` không liên kết bất kỳ mã lập lịch nào.
- **Khối điều khiển `TaskControlBlock` nội xâm và máy trạng thái `Waker` nguyên tử không mất đánh thức (`0202 §6–7`, `0205 §9–17`, `tasks/0620 §9–11`)**: `TaskControlBlock` nhúng liên kết hàng đợi nội xâm (`queue_next`) để chuyển trạng thái `WAITING -> READY` mà không cấp phát bộ nhớ trên đường nóng; giao thức chuyển trạng thái nguyên tử `IDLE <-> POLLING <-> NOTIFIED` đảm bảo `Waker.wake()` có tính lũy đẳng (idempotent) và không bao giờ làm mất tín hiệu đánh thức xảy ra đồng thời khi đang `poll()`.
- **Đồng thời có cấu trúc (`TaskGroup`), hủy bỏ hợp tác (`CancellationToken`), `ResourceGovernor` và đồng bộ hóa bất đồng bộ an toàn khi hủy (`tasks/0620`, `tasks/0621`, `tasks/0834`)**: Mọi tác vụ con trong `TaskGroup` không được sống vượt quá phạm vi nhóm trừ khi gọi `.detach()` tường minh; lỗi hoặc `panic` ở một tác vụ con tự động phát tín hiệu hủy hợp tác tới các tác vụ anh em và thu hồi sạch tài nguyên trước khi thoát phạm vi (`REQ-CONC-040`, `REQ-CONC-149`..`150`, `REQ-ASY-019`, `REQ-ASY-051`); `AsyncMutex<T>`, `AsyncRwLock<T>`, `AsyncSemaphore` và kênh bất đồng bộ (`std.async.channel`) cho phép giữ guard qua `.await` và đảm bảo khi một tác vụ đang chờ bị hủy bỏ giữa chừng, quyền đánh thức sẽ được chuyển tiếp chính xác cho tác vụ kế tiếp mà không gây khóa chết (`deadlock`).
- **Thực thi có ngăn xếp `Fiber<Y, R>` (`std.fiber`, `0204`, `tasks/0277`)**: Cung cấp ngữ cảnh thực thi có ngăn xếp độc lập ở không gian người dùng với dung lượng cam kết/dự trữ tường minh (`FiberBuilder`), chuyển ngữ cảnh hợp tác chi phí thấp qua `resume`/`yield_val` (`host.fiber_create`, `host.fiber_resume`, `host.fiber_yield`, `host.fiber_destroy`), và mặc định ghim cố định vào luồng OS khởi tạo (`!Send`, `!Share`) để bảo toàn tính toàn vẹn của `@thread_local` và các con trỏ/view trên ngăn xếp (`REQ-CONC-151`, `REQ-CONC-189`).

Status: draft (T420, 2026-11-03)
Owner: axiom-architect
Consolidates: `docs/base/specs/0202 - ASYNC-TASK-001 — Axiom TaskFutureScheduler Model.md`, `docs/base/specs/0204 - FIBER-001 — Axiom Stackful Execution.md`, `docs/base/specs/0205 - SCHEDULER-001.md`, `docs/base/tasks/0277 - BOOTSTRAP-019 — FIBER + SCHEDULER EXECUTION MODEL.md`, `docs/base/tasks/0278 - BOOTSTRAP-020 — CHANNEL + LOCK-FREE RUNTIME PRIMITIVES.md`, `docs/base/tasks/0620 - BOOTSTRAP-361 — Axiom Async Executor, Task Model & Structured Concurrency Engine.md`, `docs/base/tasks/0621 - BOOTSTRAP-362 — Axiom Synchronization Primitives & AsyncSync Coordination Engine.md`, `docs/base/tasks/0834 - BOOTSTRAP-606.md`, `docs/base/tasks/0835 - BOOTSTRAP-607.md`, `docs/base/tasks/0836 - BOOTSTRAP-607 — Native Application Scheduling, Threading, Async Runtime & Executor 5.0.md`
Covers: `REQ-CONC-023`, `REQ-ASY-036`, `REQ-ASY-040`, `REQ-ASY-051`, `REQ-ASY-060`, `REQ-ASY-067`, `REQ-ASY-068`, `REQ-ASY-089`, `REQ-ASY-094`, `REQ-ASY-149`, `REQ-CONC-149`, `REQ-ASY-156`, `REQ-CONC-200`, `REQ-ASY-161`, `REQ-ASY-162`, `REQ-ASY-163`, `REQ-ASY-164`
Consumers: `T421` (`LocalExecutor`, work-stealing `Executor`, `TaskHandle`, atomic `Waker`, `AsyncMutex`, `AsyncSemaphore`, async channels), `T422` (`TaskGroup`, `CancellationToken`, `Deadline`/`Timeout`, `ResourceGovernor`), `T423` (`std.fiber.Fiber`, `FiberScheduler`, `host.fiber_*` in Windows x64 and oracle), `T424` (`E11.5` executor benchmarks & structured-cancellation conformance suite), `E11.6` (`T425`–`T428`)

---

## 1. Architectural Foundations: `Future` vs `Task` vs `Executor` & Intrusive Task Control Block

**AXS-EXEC-001** (Executors and Tasks as link-on-demand library subsystems outside the language Core; `REQ-ASY-036`, `REQ-ASY-067`, `REQ-ASY-068`, `REQ-ASY-089`, `REQ-ASY-094`, `REQ-ASY-149`, `REQ-ASY-156`, `REQ-CONC-200`, `REQ-ASY-161`, `REQ-ASY-162`, `REQ-ASY-163`, `0127 §25, §64 AASYNC-23..24`, `0131 §58, §63`, `0202 §1, §24–26 AASYNC-56..57, AASYNC-68..70`, `0205 §1, §40 ASCHED-20..21, ASCHED-35..37, ASCHED-41..44, ASCHED-50`, `tasks/0619 §360`, `tasks/0620 §1, §7–8, §39, §45 ATASK-01..04, ATASK-28..30`).
1. **Control-flow transformation vs runtime scheduling (`REQ-ASY-161`, `REQ-ASY-162`, `REQ-ASY-163`)**: As established in `SPEC-33 AXS-ASY-001`, the compiler transforms `async fn`, `async { }`, and `.await` into finite-state machines via control-flow and storage lowering (`compiler/mir/async_lower.ax`), not via a runtime object model. Neither `Executor` nor `Task` is a mandatory part of the language Core (`REQ-ASY-068`, `REQ-CONC-200`, `REQ-ASY-163`).
2. **No implicit thread or executor creation (`REQ-ASY-036`, `REQ-ASY-067`, `REQ-ASY-089`, `REQ-ASY-149`, `REQ-ASY-156`)**:
   - Invoking an `async fn` constructs a passive `Future` state machine value without spawning an OS thread, allocating a `Task`, or starting an executor (`REQ-ASY-089`, `REQ-ASY-149`).
   - A `Future<T>` does not inherently require a multi-task executor (`REQ-ASY-067`) and may be driven directly on the stack via `std.future.block_on` or a custom freestanding poll loop (`REQ-ASY-036`).
   - Evaluating the `?` operator inside an `async fn` performs pure `Result`/`Option` control-flow branching inside `Future.poll` (`SPEC-33 AXS-ASY-023`) without interacting with the task scheduler or executor (`REQ-ASY-094`).
   - Using `async`/`await` syntax or `Send`/`Share` bounds does not implicitly link `std.async` or `std.thread` when no tasks or threads are spawned (`REQ-ASY-156`, `ATASK-30`).

**AXS-EXEC-002** (Strict separation of `Future<T>`, `Task`, `TaskHandle<T>`, and `Executor`; `REQ-CONC-023`, `REQ-ASY-164`, `0126 §3`, `0202 §1, §8, §12, AASYNC-56..58`, `0205 §1–2, §21 ASCHED-31..32`, `tasks/0620 §1–2, §6, §45 ATASK-01..06`).
Axiom maintains a strict four-part architectural boundary in `std.async` (`REQ-ASY-164`):

```text
async fn work(x: i64) -> i64
       |
       | call work(x)
       v
  Future<Output = i64>         (passive stackless state machine; SPEC-33)
       |
       | executor.spawn(fut) / local_exec.spawn_local(fut) / group.spawn(fut)
       v
     Task                      (executor-owned scheduled execution record)
       |
       +---> Executor          (owns runnable/waiting lifecycle & polling)
       |
       +---> TaskHandle<i64>   (caller-held capability to await result, cancel, or detach)
```

1. **`Future<T>` (`std.future.Future`)**: Pure state machine describing an asynchronous computation's current suspension state and live variables (`SPEC-33`). It carries zero scheduling metadata.
2. **`Task` (`std.async.TaskControlBlock<F>`)**: An owned execution instance produced when a `Future` is submitted to an executor via `spawn` or `spawn_local` (`REQ-CONC-023`, `REQ-ASY-164`, `ATASK-02`, `ATASK-05`). An async `Task` execution context is managed by an executor and need not correspond 1-to-1 to an OS thread (`REQ-CONC-023`, `AASYNC-56`): a single OS thread may multiplex thousands of tasks, or a work-stealing pool of $M$ OS worker threads may multiplex $N \gg M$ tasks.
3. **`TaskHandle<T>` / `LocalTaskHandle<T>`**: A single-owner capability (`!Copy`) returned to the spawner to `.await` or `.join()` the task's output, request cooperative cancellation (`.cancel()`), query completion (`.is_finished()`), or explicitly release handle ownership (`.detach()`) (`0202 §1, §12`, `ASCHED-32`). `TaskHandle<T>` owns the right to observe the task's result, whereas physical task storage stays alive until both the executor finishes polling the task and the handle holder consumes or detaches the result (`0205 §21`).
4. **`Executor`**: Library scheduler (`LocalExecutor`, multi-threaded `Executor`, or `DeterministicExecutor`) that maintains runnable queues, supplies `Waker` capabilities, polls runnable tasks, and parks idle workers (`ATASK-03`).

**AXS-EXEC-003** (`TaskControlBlock` layout, hot/cold separation, intrusive queue linkage & storage independence; `T421`, `0202 §6, §13–16, §21–22 AASYNC-53, AASYNC-70`, `0205 §9–12, §21 ASCHED-27..28, ASCHED-45`, `tasks/0620 §6, §24–27 ATASK-19..23`, `tasks/0835 §607.4, §607.6`).
1. **Single coalesced allocation per spawned task (`tasks/0620 §6`)**: When a `Future` `F` is spawned, the runtime embeds `F` and its output storage slot `F.Output` directly inside a typed `TaskControlBlock<F>` (`std/async/task.ax`) so that spawning a task requires at most **one** allocation (or zero heap allocations when placed in a `TaskPool` or caller-provided `TaskStorage<N>`, `AASYNC-53`, `ATASK-20..21`).
2. **Conceptual layout of `TaskHeader` and `TaskControlBlock<F>` (`0202 §6, §13`, `0205 §9–12`)**:
   ```text
   +--------------------------------------------------------------------+
   | TaskHeader (Hot Cache Line — touched by scheduler & Waker)         |
   +--------------------------------------------------------------------+
   | state: Atomic<u32>          // bit-packed wake/lifecycle state     |
   | ref_count: Atomic<u32>      // executor ref + handle ref + wakers  |
   | task_id: u64                // (slot_index: u32, generation: u32)  |
   | owner_thread_id: u64        // non-zero for pinned !Send tasks     |
   | queue_next: *mut TaskHeader // intrusive single-linked queue link  |
   | poll_fn: fn(*mut TaskHeader, mut_view<Context>) -> u32             |
   | drop_fn: fn(*mut TaskHeader)                                       |
   +--------------------------------------------------------------------+
   | Cold / Payload Region (inside TaskControlBlock<F>)                 |
   +--------------------------------------------------------------------+
   | join_waker: Option<Waker>   // waker of task awaiting TaskHandle   |
   | cancel_token: Option<CancellationToken>                            |
   | payload: union {                                                   |
   |   future: F,                // live while IDLE / POLLING / NOTIFIED|
   |   output: TaskResult<F.Output> // written before COMPLETED publish |
   | }                                                                  |
   +--------------------------------------------------------------------+
   ```
3. **Intrusive scheduler linkage (`0205 §11–12 ASCHED-27..28`)**:
   - Every `TaskHeader` embeds its own `queue_next: *mut TaskHeader` pointer. Because a task can reside in at most one ready or wait queue at any instant (`ASCHED-27`), transitioning a task from `WAITING` (`IDLE`) to `READY` (`NOTIFIED`) enqueues the existing `TaskHeader` pointer directly without allocating a separate queue node (`ASCHED-28`).
4. **Generation-stamped `TaskId` (`0202 §14`, `tasks/0834 §606.3`, `tasks/0835 §607.6`)**:
   - Each task is identified by `TaskId { pub id: u64 }` encoding `(index: u32, generation: u32)` when backed by a slot pool or monotonic counter, preventing stale logical handles from aliasing a recycled task slot (`AMEM-39`).
5. **Storage independence and caller-provided `TaskStorage<N>` (`0202 §14–16 AASYNC-53, AASYNC-70`, `tasks/0620 §25–27 ATASK-20..23`)**:
   - Task scheduling semantics are independent of physical allocation strategy (`ASCHED-45`). Besides default heap allocation, `std.async` supports static/stack `TaskStorage<N>` buffers and pooled slabs (`TaskPool`), and the optimizer may fuse or elide task allocation altogether when `await spawn(f())` does not escape (`ATASK-22..23`).

**AXS-EXEC-004** (Atomic task wake state machine & zero-lost-wakeup protocol; `T421`, `REQ-ASY-037`, `REQ-ASY-102`, `0127 §27–28`, `0135 §9`, `0202 §5, §7 AASYNC-59..60`, `0205 §10, §16–17 ASCHED-29..30`, `tasks/0620 §5, §9–11 ATASK-13..15`, `tasks/0621 §56 SYNC-10..12`).
To guarantee idempotent `Waker.wake()` notifications (`REQ-ASY-037`, `ASCHED-29`, `ATASK-14`) and strictly prevent lost wakeups when an event producer calls `wake()` concurrently while a worker thread is executing `Future.poll` (`0205 §17`, `ASCHED-30`, `ATASK-15`), `TaskHeader.state` (`Atomic<u32>`) implements the following atomic state machine in `std/async/task.ax` and `std/async/waker.ax`:

```text
                     spawn()
                        |
                        v
                  +-----------+
                  | NOTIFIED  |<----------------------+
                  | (Queued)  |                       |
                  +-----+-----+                       |
                        |                             |
       worker pops task | CAS(NOTIFIED -> POLLING)    | re-enqueue task
                        v                             |
                  +-----------+   wake() during poll  |
    +------------>|  POLLING  |-----------+           |
    |             +-----+-----+           |           |
    |                   |                 v           |
    |   poll() returns  |           +-----------+     |
    |   Poll.Pending &  |           | NOTIFIED  |-----+
    |   CAS(POLLING ->  |           | (Sticky)  | (poll returns Pending:
    |       IDLE) ok    |           +-----------+  CAS(POLLING->IDLE) fails,
    |                   v                          worker transitions
    |             +-----------+                    NOTIFIED -> re-queued)
    |             |   IDLE    |
    |             | (Waiting) |
    |             +-----+-----+
    |                   |
    |  external wake()  | CAS(IDLE -> NOTIFIED) + enqueue(task)
    +-------------------+

    Terminal transitions from POLLING (or IDLE on cancel-drop):
      poll() -> Poll.Ready(v)  ===> store Output, swap/CAS -> COMPLETED, wake join_waker
      poll() -> panic          ===> store Panic,  swap/CAS -> PANICKED,  wake join_waker
      cancel + drop while IDLE ===> drop Future,  swap/CAS -> CANCELLED, wake join_waker
```

1. **Primary lifecycle states (`u32` low bits `0x07`) and flags**:
   - `TASK_IDLE = 0u32`: The task is suspended (`WAITING`); its `Future` returned `Poll.Pending` and it is not currently on any ready queue.
   - `TASK_POLLING = 1u32`: A worker thread currently holds exclusive mutable access to the task's `Future` and is executing `Future.poll`.
   - `TASK_NOTIFIED = 2u32`: The task is either sitting in a ready queue awaiting a worker (`Queued`) or received a `wake()` while in `TASK_POLLING` (`Sticky Notified`).
   - `TASK_COMPLETED = 3u32`: Terminal state; `Future.poll` returned `Poll.Ready(val)`, `Future` was dropped, and `val` is initialized in `payload.output`.
   - `TASK_CANCELLED = 4u32`: Terminal state; the task was cooperatively cancelled and its `Future` state machine was dropped without producing a value.
   - `TASK_PANICKED = 5u32`: Terminal state; the task panicked during `Future.poll` and its `TaskPanic` payload is recorded.
   - Bit flag `FLAG_CANCEL_REQUESTED = 0x100u32`: Set atomically (`fetch_or` with `Release`) when `task.cancel()` or a parent `TaskGroup` requests cancellation.
   - Bit flag `FLAG_DETACHED = 0x200u32`: Set atomically when `TaskHandle.detach()` is called (`AXS-EXEC-021`).
2. **Exact atomic transitions (`tasks/0620 §9–11`)**:
   - **Pop & Poll (`NOTIFIED -> POLLING`)**: When a worker pops a `TaskHeader` from a ready queue, it transitions the low state from `TASK_NOTIFIED` to `TASK_POLLING` (`Acquire` ordering) and invokes `Future.poll`.
   - **Wake (`IDLE -> NOTIFIED` or `POLLING -> NOTIFIED`)**:
     - If `state == TASK_IDLE`: `compare_exchange(TASK_IDLE, TASK_NOTIFIED, AcqRel, Acquire)` succeeds for exactly one waker, which then pushes `TaskHeader` onto the executor's ready queue.
     - If `state == TASK_POLLING`: `compare_exchange(TASK_POLLING, TASK_NOTIFIED, AcqRel, Acquire)` marks the task as sticky-`NOTIFIED` **without** pushing it to the ready queue yet (because the worker currently polling it still owns the execution slot).
     - If `state == TASK_NOTIFIED`, `TASK_COMPLETED`, `TASK_CANCELLED`, or `TASK_PANICKED`: `wake()` is a no-op (`idempotent`, `ASCHED-29`, `ATASK-14`).
   - **Post-Poll Commit (`POLLING -> IDLE` vs sticky `NOTIFIED`)**:
     - When `Future.poll` returns `Poll.Pending`, the worker attempts `compare_exchange(TASK_POLLING, TASK_IDLE, Release, Acquire)`.
     - If the CAS succeeds, the task is now safely parked in `TASK_IDLE` (`WAITING`); any subsequent `wake()` will see `TASK_IDLE`, transition it to `TASK_NOTIFIED`, and enqueue it.
     - If the CAS fails because a concurrent `wake()` already changed the state from `TASK_POLLING` to `TASK_NOTIFIED` during `poll()`, the worker observes `TASK_NOTIFIED` and immediately re-enqueues (or re-polls after a fairness tick) the task. **Zero wakeups can ever be lost (`ASCHED-30`, `ATASK-15`).**
3. **No global waker runtime required (`REQ-ASY-037`, `REQ-ASY-102`)**: `Waker` instances created by `std.async` manipulate only the target `TaskHeader` and its owning executor queue; they never spawn OS threads (`REQ-ASY-037`) and do not require a global process-wide waker registry (`REQ-ASY-102`).

**AXS-EXEC-005** (`TaskHandle<T>`, `LocalTaskHandle<T>`, `TaskResult<T>`, and `TaskError` in `std/async/task.ax`; `T421`, `T422`, `REQ-ASY-019`, `REQ-ASY-051`, `0202 §12–13`, `0205 §21–23`, `tasks/0620 §2, §20, §24–25`).
The module `std.async` (`std/async/task.ax`, re-exported from `std/async/mod.ax`) defines the user-facing task result and handle types:

```axiom
module std.async

@derive(Copy, Clone, Eq, PartialEq, Ord, Hash)
pub struct TaskId {
    pub id: u64,
}

pub struct TaskPanic {
    pub message: String,
    pub task_id: TaskId,
}

pub enum TaskError {
    Cancelled,
    Panicked(TaskPanic),
}

pub enum TaskResult<T> {
    Completed(T),
    Cancelled,
    Panicked(TaskPanic),
}

pub struct TaskHandle<T> {
    raw_task: *mut u8,
    task_id: TaskId,
}

pub struct LocalTaskHandle<T> {
    raw_task: *mut u8,
    task_id: TaskId,
}
```

1. **Trait implementations**:
   - `TaskHandle<T>` is `!Copy`, implements `Send` iff `T: Send`, and is `!Share` (`0205 §23`).
   - `LocalTaskHandle<T>` is `!Copy`, `!Send`, and `!Share` (pinned to the `LocalExecutor` thread).
   - Both `TaskHandle<T>` and `LocalTaskHandle<T>` implement `Future<Output = Result<T, TaskError>>` (`let res = handle.await`), allowing a parent async task to await a child task without blocking the underlying OS worker thread.
2. **Methods on `TaskHandle<T>` and `LocalTaskHandle<T>`**:
   - `pub fn id(self: view<Self>) -> TaskId` — returns the unique `TaskId`.
   - `pub fn is_finished(self: view<Self>) -> bool` — returns `true` (`Acquire` load) iff the task is in `TASK_COMPLETED`, `TASK_CANCELLED`, or `TASK_PANICKED`.
   - `pub fn cancel(self: view<Self>)` — sets `FLAG_CANCEL_REQUESTED` on the task, triggers its associated `CancellationToken`, and wakes the task if it is in `TASK_IDLE` so it can exit or drop cleanly at its next suspension boundary (`AXS-EXEC-022`).
   - `pub async fn join(self) -> TaskResult<T>` — consumes `self`, awaits task termination, and returns `TaskResult.Completed(val)`, `TaskResult.Cancelled`, or `TaskResult.Panicked(info)` (`REQ-ASY-019`).
   - `pub fn detach(self)` — consumes `self` and sets `FLAG_DETACHED` so the executor reclaims the `TaskControlBlock` and drops any unused output automatically upon task termination (`AXS-EXEC-021`).

**AXS-EXEC-006** (Task completion `Happens-Before` synchronization and zero-copy result transfer; `T421`, `SPEC-30 AXS-CONC-041..042`, `tasks/0620 §24, §37 ATASK-19..20`, `tasks/0621 §34–35, §56 SYNC-17`).
1. **Spawn `Happens-Before`**: All memory writes performed by the caller sequenced-before `spawn(fut)` or `spawn_local(fut)` happen-before ($\prec_{\text{hb}}$) the first `Future.poll` of the spawned task (`Release` store when publishing the task to the ready queue paired with `Acquire` load when the worker dequeues and transitions `NOTIFIED -> POLLING`).
2. **Poll-to-Poll `Happens-Before` across migration**: When a `Send` task suspends on Worker $A$ (`POLLING -> IDLE` with `Release` after writing live state into `TaskControlBlock`) and subsequently resumes on Worker $B$ (`NOTIFIED -> POLLING` with `Acquire`), every write performed by the task before suspension on Worker $A$ happens-before ($\prec_{\text{hb}}$) its resumption on Worker $B$.
3. **Completion `Happens-Before` and move transfer (`ATASK-19`, `SYNC-17`)**: Writing the task output `val: T` into `payload.output` and transitioning `TaskHeader.state` to `TASK_COMPLETED` (`Release`) synchronizes-with ($\prec_{\text{sw}}$) the `Acquire` load in `TaskHandle.poll` / `TaskHandle.join`. Ownership of `val: T` transfers by `Move` from `payload.output` to the awaiting caller without copying or extra heap allocation (`ATASK-19`, `ATASK-20`).

**AXS-EXEC-007** (Panic handling in async tasks; `T422`, `REQ-ASY-019`, `REQ-ASY-051`, `0126 §71`, `0127 §49`, `tasks/0620 §20`, `tasks/0836 §13`).
Panics inside an async task are governed by the active compilation panic profile (`SPEC-04 AXS-EXT-062`) and executor policy (`REQ-ASY-051`):
1. **Under `PanicStrategy.Abort` (when task-level panic capture is not active)**: An uncaught panic inside `Future.poll` immediately terminates the process with exit code `101` (`SPEC-03 AXS-SEM-071`, `REQ-ASY-051`).
2. **Task-boundary panic containment (`REQ-ASY-019`, `0126 §71`)**: When a task is executed inside an executor or `TaskGroup` boundary (`std.async`), an unhandled task panic transitions the `Future` state to `STATE_PANICKED` (`0xFFFF_FFFE`), drops initialized task-local resources, transitions the task header to `TASK_PANICKED`, and exposes the failure explicitly as `TaskResult.Panicked(TaskPanic)` (or `Result.Err(TaskError.Panicked(TaskPanic))` when awaited) rather than corrupting the executor worker thread (`REQ-ASY-019`).

---

## 2. Single-Threaded `LocalExecutor` vs Multi-Threaded Work-Stealing `Executor` (`std.async.executor`)

**AXS-EXEC-010** (`LocalExecutor` and `spawn_local`: same-thread `!Send` execution & aliasing preservation; `T421`, `REQ-CONC-034`, `REQ-CONC-035`, `REQ-CONC-130`, `REQ-CONC-151`, `REQ-CONC-190`, `REQ-ASY-041`, `REQ-ASY-076`, `REQ-ASY-086`, `REQ-ASY-108`, `0126 §14–15`, `0127 §33, §64 AASYNC-32`, `0131 §52`, `0135 §26`, `0160 §26`, `0202 §9, AASYNC-62`, `0205 §6, §40 ASCHED-26, ASCHED-41`, `tasks/0620 §15–16 ATASK-12`).
Module `std.async` (`std/async/executor.ax`) provides `LocalExecutor`, a single-threaded cooperative task executor pinned to the OS thread that created it:

```axiom
pub struct LocalExecutor {
    owner_thread: u64,
    ready_head: *mut u8,
    ready_tail: *mut u8,
    active_tasks: usize,
    governor: Option<Arc<ResourceGovernor>>,
}

impl LocalExecutor {
    pub fn new() -> LocalExecutor
    pub fn with_governor(gov: Arc<ResourceGovernor>) -> LocalExecutor
    pub fn spawn_local<F: Future>(self: mut_view<LocalExecutor>, fut: F) -> LocalTaskHandle<F.Output>
    pub fn run_until<F: Future>(self: mut_view<LocalExecutor>, main_fut: F) -> F.Output
    pub fn run(self: mut_view<LocalExecutor>)
    pub fn try_tick(self: mut_view<LocalExecutor>) -> bool
    pub fn active_task_count(self: view<LocalExecutor>) -> usize
}
```

1. **No `Send` requirement on `spawn_local` (`REQ-CONC-034`, `REQ-CONC-130`, `REQ-CONC-190`, `REQ-ASY-041`, `REQ-ASY-076`, `REQ-ASY-086`, `REQ-ASY-108`)**:
   - `LocalExecutor.spawn_local<F: Future>(fut: F)` does **not** require `F: Send` or `F.Output: Send`. Tasks holding thread-affine types such as `Rc<T>` (`SPEC-32 AXS-SYNC-030`) may be freely spawned onto a `LocalExecutor` (`REQ-ASY-108`).
2. **Strict thread-affinity pinning (`REQ-CONC-151`, `ASCHED-26`)**:
   - `LocalExecutor` is `!Send` and `!Share`. Every task spawned via `spawn_local` records `owner_thread_id = host.thread_current_id()` in its `TaskHeader` and is polled exclusively on that OS thread (`REQ-CONC-151`). Work-stealing thieves can never access a `LocalExecutor`'s queue.
3. **Full ownership, capability, and aliasing enforcement across interleaved local tasks (`REQ-CONC-034`, `REQ-CONC-035`, `REQ-ASY-086`)**:
   - Although `spawn_local` tasks never cross OS threads, multiple tasks on the same `LocalExecutor` interleave at `.await` suspension boundaries (`0126 §15`).
   - Therefore, `spawn_local` MUST NOT bypass ownership, lifetime, or capability aliasing rules (`REQ-CONC-034`, `REQ-CONC-035`, `REQ-ASY-086`):
     - Non-`'static` stack-borrowed `view<T>` / `mut_view<T>` cannot escape into an unscoped `spawn_local` task (`SPEC-30 AXS-CONC-023`).
     - `view<T>` / `mut_view<T>` and synchronous `MutexGuard<T>` / `RwLock*Guard<T>` cannot be held across `.await` inside a `spawn_local` task (`SPEC-33 AXS-ASY-034..035`), preventing one local task from observing or mutating another local task's borrowed state across a suspension point (`REQ-CONC-035`).

**AXS-EXEC-011** (Multi-threaded work-stealing `Executor` and `spawn`: `Send` requirement & worker pool contract; `T421`, `REQ-ASY-040`, `REQ-CONC-148`, `REQ-CONC-189`, `0127 §32`, `0202 §8, §10, AASYNC-61`, `0205 §3–7, §40 ASCHED-24..25, ASCHED-42..43`, `tasks/0620 §15–17 ATASK-11`, `tasks/0835 §607.8–14`, `tasks/0836 §14–20`).
Module `std.async` (`std/async/executor.ax`) provides `Executor`, the multi-threaded work-stealing task scheduler:

```axiom
pub struct ExecutorConfig {
    pub worker_count: usize,
    pub local_queue_capacity: usize,
    pub global_queue_capacity: usize,
    pub governor: Option<Arc<ResourceGovernor>>,
}

pub struct Executor {
    inner: Arc<ExecutorInner>,
}

impl Executor {
    pub fn new(worker_count: usize) -> Executor
    pub fn with_config(cfg: ExecutorConfig) -> Result<Executor, ResourceError>
    pub fn spawn<F>(self: view<Executor>, fut: F) -> TaskHandle<F.Output>
        where F: Future + Send + 'static, F.Output: Send + 'static
    pub fn spawn_blocking<F, T>(self: view<Executor>, f: F) -> TaskHandle<T>
        where F: FnOnce() -> T + Send + 'static, T: Send + 'static
    pub fn block_on<F: Future>(self: view<Executor>, fut: F) -> F.Output
    pub fn shutdown(self: view<Executor>)
    pub fn worker_count(self: view<Executor>) -> usize
}
```

1. **Mandatory `Send` contract for migratable tasks (`REQ-ASY-040`, `REQ-CONC-148`, `REQ-CONC-189`, `AASYNC-61`, `ASCHED-25`, `ATASK-11`)**:
   - Because a task submitted to `Executor.spawn(fut)` may be polled on Worker $A$ before an `.await` and stolen or woken onto Worker $B$ after `.await`, `Executor.spawn` statically requires `F: Future + Send + 'static` and `F.Output: Send + 'static` (`REQ-ASY-040`, `REQ-CONC-189`).
   - By `SPEC-33 AXS-ASY-036`, `F: Send` holds if and only if all parameters and all variables live across any `.await` suspension point satisfy `Send` (`REQ-ASY-040`). Attempting to pass a `!Send` future to `Executor.spawn` is rejected at compile time with `AX_ASYNC_FUTURE_NOT_SEND` / `AX_CONC_NOT_SEND`.
2. **`Share` is not required for task migration (`0205 §7`)**:
   - Because `Future.poll` takes `mut_view<Self>` and the atomic `TaskHeader.state` machine (`AXS-EXEC-004`) guarantees that at most one worker thread enters `TASK_POLLING` at any instant, migrating a task between workers is a sequential ownership transfer (`Send`), not concurrent shared access (`Share`). Thus `F` is never required to implement `Share`.

**AXS-EXEC-012** (Per-worker local deque, bounded global injection queue & work-stealing algorithm; `T421`, `REQ-CONC-148`, `0205 §3–5, §19, §33–36 ASCHED-22..24`, `tasks/0277 §17–21`, `tasks/0835 §607.11–19`, `tasks/0836 §17–24`).
1. **Queue architecture (`0205 §3–5`, `tasks/0836 §17–19`)**:
   ```text
                     External / Cross-Thread Submit
                                  |
                                  v
                    +---------------------------+
                    | Bounded Global Injection  |
                    |          Queue            |
                    +-------------+-------------+
                                  |
             +--------------------+--------------------+
             v                    v                    v
      +--------------+     +--------------+     +--------------+
      |   Worker 0   |     |   Worker 1   |     |   Worker K   |
      | Local Deque  |<--->| Local Deque  |<--->| Local Deque  |
      | (LIFO/FIFO)  |steal| (LIFO/FIFO)  |steal| (LIFO/FIFO)  |
      +--------------+     +--------------+     +--------------+
   ```
   - **Per-worker local deque (`LocalQueue`)**: Each worker owns a fixed-capacity ring buffer / Chase-Lev work-stealing deque (default `256` tasks). When a task running on Worker $i$ spawns a child task or wakes another task on the same executor, it pushes to Worker $i$'s local deque without acquiring a global lock (`ASCHED-22`). The owner pops locally from the bottom (`LIFO`/`FIFO` fast path for cache locality), while idle thief workers steal from the top (`FIFO`, taking the oldest queued tasks).
   - **Bounded global injection queue**: Submissions from outside the worker threads (or overflows when a worker's local deque is full) push into a bounded MPMC global injection queue governed by `ExecutorConfig.global_queue_capacity` (`tasks/0835 §607.15–16`).
2. **Worker scheduling loop & fairness tick (`0205 §19`, `tasks/0836 §20, §25`)**:
   - On each scheduling iteration, Worker $i$:
     1. Every `61` local polls (fairness tick), checks the global injection queue first so external submissions cannot starve behind local ping-pong tasks (`tasks/0836 §25`).
     2. Otherwise pops a runnable task from its own `LocalQueue`.
     3. If its `LocalQueue` is empty, pops a batch from the global injection queue.
     4. If the global queue is also empty, attempts to steal up to half of the runnable tasks from another worker's `LocalQueue` (iterating victims starting from a pseudo-random or round-robin offset).
     5. If no work is found across all workers, transitions to parked state via `host.futex_wait` on its worker park word (`tasks/0836 §23–24`).
3. **Scheduling order is not memory ordering (`REQ-CONC-148`, `tasks/0620 §45 ATASK-28`)**:
   - Work-stealing deque push/pop/steal operations use `Release`/`Acquire` atomic orderings so task state transfers safely across workers, but application logic MUST NOT rely on scheduler poll order for inter-task memory visibility without explicit synchronization (`Atomic`, `AsyncMutex`, channels, or task `.await` completion, `REQ-CONC-148`).

**AXS-EXEC-013** (Blocking isolation & `spawn_blocking`; `T421`, `tasks/0620 §13–14 ATASK-17..18`, `tasks/0835 §607.37–39`, `tasks/0836 §G7`).
1. **Non-blocking `poll()` contract (`ATASK-17`)**: Tasks running on `LocalExecutor` or the CPU work-stealing `Executor` MUST NOT invoke synchronous OS-blocking operations inside `Future.poll` (`SPEC-33 AXS-ASY-027`).
2. **`Executor.spawn_blocking` (`ATASK-18`, `tasks/0835 §607.38`)**: Synchronous blocking operations (such as legacy blocking file I/O or heavy synchronous FFI calls) are offloaded via `executor.spawn_blocking(f)`, which executes `f()` on a dedicated blocking worker thread and resolves the returned `TaskHandle<T>` via `Waker.wake()` upon completion without starving async polling workers.

**AXS-EXEC-014** (Cooperative task yield `std.async.yield_now`; `T421`, `tasks/0836 §25–26`).
Module `std.async` provides `pub async fn yield_now()`:
1. On its first `poll(cx)`, `YieldNowFuture` invokes `cx.waker().wake_by_ref()`, transitions its internal flag to `yielded = true`, and returns `Poll.Pending`, returning control to the executor so other ready tasks in the queue can run.
2. On its second `poll(cx)`, `YieldNowFuture` returns `Poll.Ready(())`.

**AXS-EXEC-015** (Executor lifecycle & deterministic shutdown; `T421`, `0205 §24 ASCHED-46`, `tasks/0620 §38`).
1. Every `Executor` progresses deterministically through four lifecycle phases (`0205 §24`):
   `RUNNING -> SHUTDOWN_REQUESTED -> DRAINING -> STOPPED`.
2. Calling `executor.shutdown()` (or dropping the last owning `Executor` handle) sets the shutdown flag, wakes all parked worker threads via `host.futex_wake`, drains or cancels remaining tasks according to shutdown policy, and joins all worker OS threads via `host.thread_join` before freeing `ExecutorInner` (`ASCHED-46`). No worker thread may outlive the destroyed `Executor`.

**AXS-EXEC-016** (Deterministic single-threaded test executor & oracle verification; `T421`, `T424`, `REQ-ASY-060`, `0127 §58`, `0205 §37–38`, `tasks/0620 §40`).
1. To verify async poll order, wake order, cancellation, and `Drop` behavior reproducibly and independently of wall-clock timing or OS thread scheduling (`REQ-ASY-060`), `std.async` and the MIR interpreter oracle (`--interp`) provide deterministic single-threaded execution:
   - `LocalExecutor` polls ready tasks in strict, deterministic FIFO queue order.
   - In `--interp` mode, multi-worker `Executor` runs on the oracle's deterministic cooperative thread scheduler (`SPEC-32 AXS-SYNC-004`) combined with the deterministic `POLL`/`SUSPEND`/`WAKE`/`RESUME`/`COMPLETE`/`CANCEL_DROP` lifecycle trace (`SPEC-33 AXS-ASY-050`).

---

## 3. Structured Concurrency (`TaskGroup`), Cooperative Cancellation (`CancellationToken`), Deadlines & `ResourceGovernor`

**AXS-EXEC-020** (`TaskGroup<T>` structured concurrency scope in `std/async/group.ax`; `T422`, `REQ-CONC-040`, `REQ-CONC-150`, `REQ-CONC-155`, `REQ-CONC-199`, `REQ-ASY-019`, `0126 §19`, `0202 §11 AASYNC-63`, `0205 §25`, `tasks/0620 §3, §19–20, §45 ATASK-09`, `tasks/0836 §10–13`).
Module `std.async` (`std/async/group.ax`, re-exported from `std/async/mod.ax`) provides `TaskGroup<T>`, enforcing lexically scoped structured concurrency for asynchronous tasks:

```axiom
pub struct TaskGroup<T> {
    cancel_source: CancellationSource,
    handles: Vec<TaskHandle<T>>,
    first_error: Option<TaskError>,
    governor: Option<Arc<ResourceGovernor>>,
}

impl<T: Send + 'static> TaskGroup<T> {
    pub fn new() -> TaskGroup<T>
    pub fn with_cancellation(parent_token: view<CancellationToken>) -> TaskGroup<T>
    pub fn with_governor(gov: Arc<ResourceGovernor>) -> TaskGroup<T>
    pub fn cancellation_token(self: view<TaskGroup<T>>) -> CancellationToken
    pub fn spawn<F>(self: mut_view<TaskGroup<T>>, exec: view<Executor>, fut: F)
        where F: Future<Output = T> + Send + 'static
    pub async fn next(self: mut_view<TaskGroup<T>>) -> Option<Result<T, TaskError>>
    pub async fn join_all(self) -> Result<Vec<T>, TaskError>
    pub fn cancel_all(self: mut_view<TaskGroup<T>>)
}
```

1. **Strict lexical lifetime containment (`REQ-CONC-040`, `REQ-CONC-150`, `AASYNC-63`, `ATASK-09`)**:
   - Child tasks spawned into a `TaskGroup<T>` are owned by the group and MUST NOT outlive the group's scope (`REQ-CONC-040`, `REQ-CONC-150`).
   - Calling `group.join_all().await` awaits all child tasks in the group before returning.
   - If a `TaskGroup<T>` is dropped early (for example, due to an early `?` return or cancellation of the parent task) while child tasks are still active, `Drop` on `TaskGroup<T>` automatically calls `self.cancel_all()` and drains/reclaims all child tasks so zero orphan child tasks survive scope exit (`REQ-CONC-040`, `REQ-CONC-155`).
2. **Sibling cancellation on child failure or panic (`REQ-ASY-019`, `tasks/0620 §20`, `tasks/0836 §13`)**:
   - If any child task in `TaskGroup<T>` panics (`TaskResult.Panicked`) or triggers group failure, `TaskGroup` immediately triggers `self.cancel_source.cancel()`, propagating cooperative cancellation to all remaining sibling tasks, awaits their clean termination and `Future` destructor execution, and deterministically returns the first failure (`Result.Err(TaskError.Panicked(panic_info))`) from `join_all().await`.
   - For fallible tasks returning `Result<V, E>`, `TaskGroup.try_join_all` (or `spawn_result`) similarly cancels remaining siblings upon the first `Result.Err(e)` and awaits all siblings before propagating `Err(e)`.

**AXS-EXEC-021** (Structured handle drop vs explicit `detach()`; `T422`, `REQ-ASY-109`, `REQ-CONC-100`, `REQ-CONC-155`, `REQ-CONC-188`, `REQ-CONC-199`, `0135 §29`, `0136 §19`, `0202 §11–12 AASYNC-64`, `0205 §22, §40 ASCHED-33`, `tasks/0620 §2, §4, §45 ATASK-07..10`).
Axiom makes the ownership relationship between a caller and a spawned task explicit (`REQ-ASY-109`, `REQ-CONC-100`, `REQ-CONC-199`):
1. **Default structured ownership (`REQ-CONC-155`, `REQ-CONC-199`)**: Spawning a task returns a linear `TaskHandle<T>` (or registers it inside a `TaskGroup<T>`). A task is never implicitly detached at spawn time (`REQ-CONC-155`).
2. **Dropping an un-awaited `TaskHandle<T>` without `detach()` (`REQ-ASY-109`, `T422`)**:
   - If a caller drops a `TaskHandle<T>` (or `LocalTaskHandle<T>`) without awaiting `.join()` and without calling `.detach()`, `Drop` on `TaskHandle<T>` requests cooperative cancellation (`FLAG_CANCEL_REQUESTED`) and releases the handle reference so the executor drops the `Future` at its next suspension point (or immediately if `TASK_IDLE`) and reclaims the `TaskControlBlock`.
3. **Explicit `task.detach()` (`REQ-ASY-109`, `REQ-CONC-100`, `REQ-CONC-188`, `AASYNC-64`, `ASCHED-33`, `ATASK-10`)**:
   - When background fire-and-forget execution is intentionally desired, the caller MUST invoke `handle.detach()` explicitly (`REQ-ASY-109`, `REQ-CONC-199`).
   - Calling `handle.detach()` transfers full lifecycle ownership of the task to the `Executor` (`REQ-CONC-100`): the task continues running to completion without cancellation, and upon completion the executor automatically drops the output value and reclaims the `TaskControlBlock`.
   - Detached execution provides **no** implicit completion synchronization (`REQ-CONC-188`); the caller cannot observe the detached task's side effects without an explicit synchronization primitive (such as a channel or atomic release/acquire).

**AXS-EXEC-022** (Prohibition of forced termination & cooperative cancellation invariant; `T422`, `REQ-CONC-149`, `REQ-CONC-155`, `0202 §17–18 AASYNC-59..60`, `0205 §40 ASCHED-34`, `tasks/0620 §21–23, §45 ATASK-08, ATASK-27`).
1. **Forced external termination is forbidden in safe code (`REQ-CONC-149`, `AASYNC-60`, `AFIBER-45`)**:
   - Safe Axiom code provides no `kill_thread()`, `terminate_task()`, or asynchronous stack destruction primitive that forcibly halts a running thread, task, or fiber mid-instruction (`REQ-CONC-149`). Forcibly destroying an active execution context while it holds mutable capabilities (`mut_view<T>`), lock guards, or partially initialized frames would violate `Drop` consistency and memory safety.
2. **Cooperative cancellation at suspension boundaries (`REQ-CONC-155`, `AASYNC-59`, `ASCHED-34`, `ATASK-08`)**:
   - Task cancellation in Axiom is strictly cooperative: requesting cancellation sets `FLAG_CANCEL_REQUESTED` / signals a `CancellationToken` and wakes the target task.
   - The target task observes cancellation either by awaiting `token.cancelled().await` / checking `token.is_cancelled()` or by being dropped while suspended at an `.await` point (`STATE_UNPOLLED` or `STATE_SUSPENDED_k`), where compiler-generated per-state `Drop` glue (`SPEC-33 AXS-ASY-044`) runs synchronous destructors for all live resources in reverse declaration order.
3. **No implicit rollback of committed external side effects (`ATASK-27`, `tasks/0620 §23`, `tasks/0621 §56 SYNC-16`)**:
   - Cancelling a task releases owned local resources via `Drop` but does not roll back already-committed I/O writes, sent channel messages, or completed atomic stores.

**AXS-EXEC-023** (Hierarchical `CancellationSource` and `CancellationToken` in `std/async/cancel.ax`; `T422`, `tasks/0620 §21–22`, `tasks/0836 §G8`).
Module `std.async` (`std/async/cancel.ax`, re-exported from `std/async/mod.ax`) provides explicit value-oriented cancellation capabilities:

```axiom
pub struct CancellationSource {
    state: Arc<CancelState>,
}

@derive(Clone)
pub struct CancellationToken {
    state: Arc<CancelState>,
}

pub struct CancelledFuture {
    state: Arc<CancelState>,
    registered: bool,
}
```

1. **API & hierarchy**:
   - `CancellationSource.new() -> CancellationSource` creates a root cancellation source (`is_cancelled == false`).
   - `source.token() -> CancellationToken` returns a cloneable, `Send + Share` read capability observing the source.
   - `source.child_source() -> CancellationSource` creates a child source linked into the parent's cancellation tree: cancelling the parent source automatically cancels all descendant child sources (`tasks/0620 §21`), whereas cancelling a child source does not cancel its parent or siblings.
   - `source.cancel()` atomically transitions the source (and all descendants in the tree) to the cancelled state (`Release`) and wakes all registered `CancelledFuture` wakers (`idempotent`).
   - `token.is_cancelled(self: view<CancellationToken>) -> bool` performs a non-blocking `Acquire` load of the cancellation state.
   - `token.cancelled(self: view<CancellationToken>) -> CancelledFuture` returns a `Future<Output = ()>` that resolves to `Poll.Ready(())` immediately if already cancelled, or registers the caller's `Waker` and returns `Poll.Pending` until `cancel()` is invoked.
2. **Linearization of completion vs cancellation race (`tasks/0620 §22`)**:
   - When task completion (`Poll.Ready(v)`) races with `cancel()`, the atomic state transition on `TaskHeader.state` (or `CancelState`) defines a single linearizable winner: if `TASK_COMPLETED` commits first, the task result is `TaskResult.Completed(v)`; if cancellation drop commits first, the task result is `TaskResult.Cancelled`. Ambiguous dual states are impossible.

**AXS-EXEC-024** (`Deadline`, `Timeout<F>`, and timeout budget propagation in `std/async/timeout.ax`; `T422`, `REQ-ASY-153`, `REQ-ASY-159`, `tasks/0835`, `tasks/0836`).
Module `std.async` (`std/async/timeout.ax`, re-exported from `std/async/mod.ax`) separates temporal deadlines from task cancellation (`REQ-ASY-153`, `REQ-ASY-159`):

```axiom
@derive(Copy, Clone, Eq, PartialEq, Ord, PartialOrd, Hash)
pub struct Deadline {
    pub deadline_ns: u64,
}

@derive(Copy, Clone, Eq, PartialEq)
pub struct TimeoutError {}

pub struct Timeout<F: Future> {
    fut: F,
    deadline: Deadline,
}

impl Deadline {
    pub fn at_ns(abs_ns: u64) -> Deadline
    pub fn after_ns(duration_ns: u64) -> Deadline
    pub fn after_ms(duration_ms: u64) -> Deadline
    pub fn is_expired(self) -> bool
    pub fn remaining_ns(self) -> u64
    pub fn min(self, other: Deadline) -> Deadline
}

pub fn with_deadline<F: Future>(deadline: Deadline, fut: F) -> Timeout<F>
pub fn with_timeout_ns<F: Future>(duration_ns: u64, fut: F) -> Timeout<F>
pub fn with_timeout_ms<F: Future>(duration_ms: u64, fut: F) -> Timeout<F>
```

1. **Explicit policy type distinct from cancellation (`REQ-ASY-153`, `REQ-ASY-159`)**:
   - `Deadline` represents an absolute monotonic timestamp in nanoseconds (`host.monotonic_ns()`).
   - Propagating a `Deadline` into a child operation narrows the effective budget via `parent_deadline.min(child_deadline)` (`REQ-ASY-153`).
   - `Timeout<F>` implements `Future<Output = Result<F.Output, TimeoutError>>`: on each `poll(cx)`, it first polls `self.fut`; if `self.fut` returns `Poll.Ready(val)`, `Timeout<F>` returns `Poll.Ready(Result.Ok(val))`; if `self.fut` returns `Poll.Pending` and `self.deadline.is_expired()` is `true`, `Timeout<F>` returns `Poll.Ready(Result.Err(TimeoutError {}))` and drops `self.fut` cleanly when `Timeout<F>` is dropped.

**AXS-EXEC-025** (Unified `ResourceGovernor` quota and admission control in `std/async/governor.ax`; `T422`, `REQ-ASY-167`, `tasks/0834 §606.0–25`, `tasks/0835 §607.16, §607.22, §607.29–33`).
Module `std.async` (`std/async/governor.ax`, re-exported from `std/async/mod.ax`) provides `ResourceGovernor` for deterministic accounting, quota enforcement, and admission control across tasks, threads, fibers, and memory (`REQ-ASY-167`, `tasks/0834`):

```axiom
@derive(Copy, Clone, Eq, PartialEq)
pub enum ResourceKind {
    Tasks,
    Threads,
    Fibers,
    MemoryBytes,
    IoOperations,
}

@derive(Copy, Clone, Eq, PartialEq)
pub enum ResourcePressure {
    Normal,
    Warning,
    Critical,
    Exhausted,
}

@derive(Copy, Clone, Eq, PartialEq)
pub enum ResourceError {
    QuotaExceeded(ResourceKind),
    InvalidBudget,
}

pub struct ResourceQuota {
    pub soft_limit: u64,
    pub hard_limit: u64,
}

pub struct ResourceGovernor {
    parent: Option<Arc<ResourceGovernor>>,
    task_quota: ResourceQuota,
    thread_quota: ResourceQuota,
    fiber_quota: ResourceQuota,
    memory_quota: ResourceQuota,
    active_tasks: Atomic<u64>,
    active_threads: Atomic<u64>,
    active_fibers: Atomic<u64>,
    active_memory: Atomic<u64>,
}
```

1. **Hierarchical hard and soft limits (`tasks/0834 §606.4–9, §606.22–25`)**:
   - Every `ResourceGovernor` tracks current usage (`active_tasks`, `active_threads`, `active_fibers`, `active_memory`) against configured `soft_limit` (triggering `ResourcePressure.Warning`) and `hard_limit` (rejecting admission with `Result.Err(ResourceError.QuotaExceeded(kind))`).
   - When a child `ResourceGovernor` is attached to a `parent` governor, acquiring $N$ units charges both the child and all ancestors atomically; a child scope can never exceed its parent's `hard_limit` (`tasks/0834 §606.4, §606.12`).
   - Releasing a resource (or dropping a `ResourceLease` / completing a governed task) decrements the usage counter in reverse hierarchy order (`Release`), ensuring deterministic zero-leak accounting even when tasks panic or are cancelled.

---

## 4. Async-Aware Synchronization Primitives (`std.async.sync`, `std.async.channel`) & Cancellation-Safety Contracts

**AXS-EXEC-030** (Distinction between synchronous blocking primitives and async-aware synchronization primitives; `T421`, `REQ-CONC-049`, `REQ-CONC-147`, `REQ-CONC-184`, `REQ-ASY-054`, `REQ-ASY-129`, `REQ-ASY-130`, `REQ-ASY-165`, `0126 §30–32`, `0127 §51–52`, `0135 §58–60`, `tasks/0620 §31–32 ATASK-25..26`, `tasks/0621 §1–2, §13–17, §56 ASYNC-LOCK-01, SYNC-06..09`).
1. **Separate semantic types (`REQ-CONC-184`, `REQ-ASY-054`, `REQ-ASY-129`, `ATASK-25..26`, `SYNC-08..09`)**:
   - Synchronous primitives in `std.sync` (`Mutex<T>`, `RwLock<T>`, `Condvar`, `Barrier`; `SPEC-32`) park the calling OS thread on contention (`host.futex_wait`), and their guards (`MutexGuard<T>`, `RwLockReadGuard<T>`, `RwLockWriteGuard<T>`) are statically rejected across `.await` (`AX_ASYNC_GUARD_ACROSS_AWAIT`, `SPEC-33 AXS-ASY-035`, `REQ-CONC-147`).
   - When a logical lock, permit, or message wait must span an `.await` suspension boundary without blocking the underlying OS worker thread, programs use the async-aware synchronization primitives in `std.async.sync` and `std.async.channel` (`AsyncMutex<T>`, `AsyncRwLock<T>`, `AsyncSemaphore`, `AsyncSender<T>`, `AsyncReceiver<T>`) (`REQ-ASY-054`, `REQ-ASY-129`, `REQ-ASY-165`).
2. **Mandatory cancellation-safety contract (`REQ-CONC-049`, `REQ-ASY-130`, `tasks/0621 §14, §27, §56 SYNC-12`)**:
   - Because any awaiting `Future` may be dropped while in `Poll.Pending` (due to `Timeout`, `TaskGroup` sibling failure, or `task.cancel()`), every async synchronization primitive MUST define and uphold an exact **cancellation-safety contract** (`REQ-ASY-130`): dropping a waiting `Future` before it is polled to `Poll.Ready` MUST never corrupt the primitive's state, leak permits, lose queued channel messages, or strand a wakeup baton (`SYNC-12`).

**AXS-EXEC-031** (`AsyncMutex<T>`, `AsyncMutexLockFuture<T>`, and `AsyncMutexGuard<T>` in `std/async/sync.ax`; `T421`, `REQ-CONC-049`, `REQ-CONC-147`, `REQ-ASY-054`, `REQ-ASY-129`, `REQ-ASY-130`, `0126 §32`, `0127 §52`, `0135 §59–60`, `tasks/0621 §13–15`).
Module `std.async` (`std/async/sync.ax`, re-exported from `std/async/mod.ax`) defines `AsyncMutex<T>`:

```axiom
pub struct AsyncMutex<T> {
    inner: *mut AsyncMutexInner<T>,
}

pub struct AsyncMutexLockFuture<T> {
    mutex: *mut AsyncMutexInner<T>,
    waiter_id: u64,
}

pub struct AsyncMutexGuard<T> {
    mutex: *mut AsyncMutexInner<T>,
}

impl<T> AsyncMutex<T> {
    pub fn new(val: T) -> AsyncMutex<T>
    pub fn lock(self: view<AsyncMutex<T>>) -> AsyncMutexLockFuture<T>
    pub fn try_lock(self: view<AsyncMutex<T>>) -> Option<AsyncMutexGuard<T>>
}

impl<T> AsyncMutexGuard<T> {
    pub fn get(self: view<AsyncMutexGuard<T>>) -> view<T>
    pub fn get_mut(self: mut_view<AsyncMutexGuard<T>>) -> mut_view<T>
}
```

1. **Trait bounds and `.await`-crossing capability (`REQ-CONC-049`, `REQ-CONC-147`, `REQ-ASY-054`, `REQ-ASY-129`)**:
   - `AsyncMutex<T>` implements `Send` and `Share` iff `T: Send`.
   - `AsyncMutexGuard<T>` is `!Copy`, implements `Drop` (which releases the lock and wakes the next queued waiter with `Release` memory ordering), and—unlike `std.sync.MutexGuard<T>`—is **not** marked `@no_suspend_hold` and implements `Send` iff `T: Send` (`Share` iff `T: Share`).
   - Consequently, `let mut guard = mutex.lock().await` MAY be held across subsequent `.await` points inside an `async fn` (`REQ-ASY-054`), while any `view<T>` or `mut_view<T>` projected via `guard.get()` / `guard.get_mut()` remains confined to a single synchronous segment between `.await` points (`SPEC-33 AXS-ASY-034`, `REQ-CONC-049`).
2. **Waiter cancellation-safety contract (`REQ-ASY-130`, `T421`, `T424`)**:
   - When `AsyncMutexLockFuture<T>.poll(cx)` cannot acquire the lock immediately, it enqueues a waiter node (`waiter_id`, `waker: cx.waker().clone()`, `granted: bool`) into the mutex's FIFO wait queue and returns `Poll.Pending`.
   - When the current lock holder drops its `AsyncMutexGuard<T>`, it either marks the head waiter as `granted = true` and wakes its `Waker` (baton handoff) or clears the `locked` bit and wakes the head waiter.
   - **Critical cancellation invariant**: If a waiting task's `AsyncMutexLockFuture<T>` is dropped (cancelled) before returning `Poll.Ready(guard)`:
     - `Drop` on `AsyncMutexLockFuture<T>` removes its waiter node from the mutex wait queue.
     - If the lock baton had **already** been handed to this waiter (`granted == true`) prior to `Drop` running, `Drop` on `AsyncMutexLockFuture<T>` MUST immediately pass the baton to the next waiter in the queue (and call `wake()` on that next waiter) or unlock the mutex if the queue is empty (`REQ-ASY-130`). This guarantees that cancelling a task while it is waking up from `mutex.lock().await` never deadlocks subsequent tasks.

**AXS-EXEC-032** (`AsyncRwLock<T>`, `AsyncRwLockReadGuard<T>`, and `AsyncRwLockWriteGuard<T>` in `std/async/sync.ax`; `T421`, `tasks/0621 §11–12`).
`AsyncRwLock<T>` provides multi-reader (`view<T>`) or single-writer (`mut_view<T>`) async-aware synchronization:
1. `pub fn new(val: T) -> AsyncRwLock<T>`
2. `pub fn read(self: view<AsyncRwLock<T>>) -> AsyncRwLockReadFuture<T>` and `pub fn try_read(self: view<AsyncRwLock<T>>) -> Option<AsyncRwLockReadGuard<T>>`
3. `pub fn write(self: view<AsyncRwLock<T>>) -> AsyncRwLockWriteFuture<T>` and `pub fn try_write(self: view<AsyncRwLock<T>>) -> Option<AsyncRwLockWriteGuard<T>>`
4. Dropping `AsyncRwLockReadFuture<T>` or `AsyncRwLockWriteFuture<T>` while pending removes the waiter and, if write or read ownership was already granted before poll resumption, wakes the next eligible writer or reader batch without stranding the lock.

**AXS-EXEC-033** (`AsyncSemaphore` and `AsyncSemaphorePermit` in `std/async/sync.ax`; `T421`, `tasks/0621 §16–17`).
`AsyncSemaphore` bounds concurrent access to $N$ permits across tasks without blocking OS threads:

```axiom
pub struct AsyncSemaphore {
    inner: *mut AsyncSemaphoreInner,
}

pub struct AsyncSemaphoreAcquireFuture {
    sem: *mut AsyncSemaphoreInner,
    waiter_id: u64,
}

pub struct AsyncSemaphorePermit {
    sem: *mut AsyncSemaphoreInner,
}

impl AsyncSemaphore {
    pub fn new(permits: usize) -> AsyncSemaphore
    pub fn acquire(self: view<AsyncSemaphore>) -> AsyncSemaphoreAcquireFuture
    pub fn try_acquire(self: view<AsyncSemaphore>) -> Option<AsyncSemaphorePermit>
    pub fn available_permits(self: view<AsyncSemaphore>) -> usize
}
```

1. **Permit ownership & `Drop` (`tasks/0621 §16–17`)**: `AsyncSemaphorePermit` is `!Copy` and `Send`. Dropping an `AsyncSemaphorePermit` either transfers the permit directly to the first queued waiter in `AsyncSemaphoreInner` and wakes its `Waker`, or increments `available_permits` (`Release`).
2. **Cancellation safety (`REQ-ASY-130`)**: If `AsyncSemaphoreAcquireFuture` is dropped while pending after a permit was already assigned to its waiter slot, its `Drop` implementation immediately forwards the permit to the next queued waiter (or increments `available_permits`) so zero permits are ever leaked on cancellation.

**AXS-EXEC-034** (Async channels `AsyncSender<T>`, `AsyncReceiver<T>`, `async_channel_bounded`, and `async_channel_unbounded` in `std/async/channel.ax`; `T421`, `tasks/0278 §22–27`, `tasks/0620 §33–36`, `tasks/0621 §21–27, §56 SYNC-13..15`).
Module `std.async` (`std/async/channel.ax`, re-exported from `std/async/mod.ax`) provides async-aware ownership-transferring channels:

```axiom
pub struct AsyncSender<T> {
    inner: *mut AsyncChannelInner<T>,
}

pub struct AsyncReceiver<T> {
    inner: *mut AsyncChannelInner<T>,
}

pub struct SendFuture<T> {
    inner: *mut AsyncChannelInner<T>,
    item: Option<T>,
    waiter_id: u64,
}

pub struct RecvFuture<T> {
    inner: *mut AsyncChannelInner<T>,
    waiter_id: u64,
}

pub fn async_channel_bounded<T: Send>(capacity: usize) -> (AsyncSender<T>, AsyncReceiver<T>)
pub fn async_channel_unbounded<T: Send>() -> (AsyncSender<T>, AsyncReceiver<T>)
```

1. **Zero-copy ownership transfer & failure preservation (`tasks/0620 §36`, `tasks/0621 §21, §25–26, SYNC-13..14`)**:
   - `tx.send(val)` returns `SendFuture<T>` implementing `Future<Output = Result<(), SendError<T>>>` (where `SendError<T>` is re-exported from `std.sync.channel`, `SPEC-32 AXS-SYNC-040`).
   - When the channel has capacity, `SendFuture.poll` moves `val` directly into the channel ring/queue (`Release`), wakes a waiting receiver's `Waker` if one is registered, and returns `Poll.Ready(Result.Ok(()))`.
   - If all `AsyncReceiver<T>` handles have been dropped, `SendFuture.poll` (and `tx.try_send(val)`) returns `Result.Err(SendError { value: val })`, restoring ownership of `val` to the caller (`SYNC-14`).
2. **Bounded backpressure & send cancellation safety (`tasks/0278 §23`, `tasks/0620 §34–35`, `REQ-ASY-130`)**:
   - When a bounded channel (`capacity >= 1`) is full, `SendFuture.poll(cx)` retains ownership of `val` inside `self.item = Option.Some(val)`, registers `cx.waker().clone()` in the sender wait list, and returns `Poll.Pending`.
   - If `SendFuture<T>` is dropped (cancelled) before `self.item` has been moved into the channel buffer, `Drop` on `SendFuture<T>` unregisters the sender waiter, drops `self.item` cleanly, and (if a receiver had just woken this sender) wakes the next waiting sender so backpressure wakeups are never lost.
3. **Receive & receive cancellation safety (`tasks/0278 §22`, `tasks/0621 §27`, `REQ-ASY-130`)**:
   - `rx.recv()` returns `RecvFuture<T>` implementing `Future<Output = Result<T, RecvError>>`.
   - When the channel buffer is non-empty, `RecvFuture.poll(cx)` pops the oldest item (`Acquire`), wakes a blocked `SendFuture` if one is waiting for capacity, and returns `Poll.Ready(Result.Ok(item))`.
   - When the buffer is empty and at least one `AsyncSender<T>` is alive, `RecvFuture.poll(cx)` registers `cx.waker().clone()` in the receiver wait queue and returns `Poll.Pending`.
   - **Critical receive cancellation invariant (`tasks/0621 §27`)**: Messages remain in the channel queue until a `RecvFuture.poll` actively pops them. Therefore, if a pending `RecvFuture<T>` is dropped (cancelled) before being polled again after a sender enqueues a message, `Drop` on `RecvFuture<T>` unregisters the waiter and forwards any pending wakeup to the next waiting `RecvFuture<T>`—**no queued message is ever lost or dropped when a `RecvFuture<T>` is cancelled**.

---

## 5. Stackful `Fiber<Y, R>` Model, Cooperative Context Switching & `host.fiber_*` Intrinsics (`std.fiber`)

**AXS-EXEC-050** (Stackful `Fiber` vs `Future`, `Task`, and `Thread`; `T423`, `0204 §1–3, §23–25, §31 AFIBER-20..22, AFIBER-40..42`, `tasks/0277 §1–4`).
1. **`Fiber` is a user-space stackful execution context (`AFIBER-20..22`)**:
   - Unlike a `Future<T>` (which is a compiler-synthesized stackless state machine with zero dedicated stack) and unlike an OS `Thread` (which is a kernel-scheduled preemptive execution resource), a `Fiber<Y, R>` (`std.fiber`) owns a dedicated contiguous call stack in user space (`AFIBER-21`, `AFIBER-22`).
   - A running fiber may suspend cooperatively (`yield_val` / `yield_now`) from arbitrarily deep synchronous helper function call chains without marking intermediate functions `async` (`0204 §2–3`, `tasks/0277 §3–4`).
2. **Orthogonality (`AFIBER-40..42`)**:
   - Using `Future` never allocates a `Fiber` (`AFIBER-41`), and creating a `Fiber` never requires `async`/`await` state-machine lowering (`AFIBER-42`).

**AXS-EXEC-051** (Explicit stack storage contract, `FiberBuilder`, and stack lifetime bounds; `T423`, `0204 §4–5, §15–18, §31 AFIBER-23..24, AFIBER-31, AFIBER-35..37, AFIBER-44..45`, `tasks/0277 §6, §12–13`).
1. **Fixed contiguous stack with guard page (`0204 §15–16 AFIBER-35..36`)**:
   - Each `Fiber` executes on a contiguous stack region with a stable virtual address range for the entire lifetime of the fiber (`AFIBER-24`).
   - Default stack sizes are `stack_commit = 65_536` bytes (`64 KiB`) and `stack_reserve = 262_144` bytes (`256 KiB`), configurable via `FiberBuilder.stack_size(commit_bytes, reserve_bytes)` (`0204 §15`). On native targets, the OS places a guard page at the low end of the stack so stack overflow traps deterministically (`AFIBER-35`).
2. **Fiber stack cannot be destroyed while executing (`0204 §18 AFIBER-31, AFIBER-45`, `tasks/0277 §12`)**:
   - The lifetime of a fiber's stack storage MUST strictly enclose the fiber's execution lifetime (`AFIBER-31`). Attempting to destroy or drop a `Fiber` while its state is `Running` (for example, from inside the fiber itself) is a deterministic runtime error/panic; a fiber may only be destroyed when it is in a suspended (`Created` / `Yielded`) or terminal (`Completed` / `Panicked`) state (`0204 §18`, `AFIBER-45`).
3. **Stack capability containment (`0204 §17 AFIBER-44`)**:
   - Safe borrowed capabilities (`view<T>`, `mut_view<T>`) pointing to variables on a fiber's stack are bounded by that stack frame's lexical scope and cannot escape out of the fiber's entry closure (`AFIBER-44`).

**AXS-EXEC-052** (Default thread-pinned affinity (`Fiber: !Send`, `!Share`) and TLS semantics; `T423`, `REQ-CONC-151`, `REQ-CONC-189`, `0204 §11–14, §31 AFIBER-28..30, AFIBER-39`, `tasks/0277 §5`).
1. **Non-migratable by default (`REQ-CONC-151`, `REQ-CONC-189`, `0204 §11–12 AFIBER-28..30`)**:
   - Because a suspended fiber's call stack may hold active frames that depend on the current OS thread's identity, Win32 TEB fiber state, or `@thread_local` storage, `Fiber<Y, R>` is unconditionally `!Send` and `!Share` by default (`impl<Y, R> !Send for Fiber<Y, R> {}`, `impl<Y, R> !Share for Fiber<Y, R> {}`) (`AFIBER-30`).
   - Every `Fiber` records its creation thread ID (`owner_thread = host.thread_current_id()`) and is pinned to that OS thread (`REQ-CONC-151`, `REQ-CONC-189`). Attempting to resume or destroy a fiber from a different OS thread returns an error (`-4` `InvalidInput`) / panics deterministically.
2. **TLS sharing on the host thread (`0204 §13 AFIBER-39`)**:
   - All fibers running cooperatively on OS Thread $A$ share Thread $A$'s `@thread_local` variables (`0204 §13`). Because fiber switching occurs only at explicit cooperative `yield_val` / `yield_now` points and fibers cannot migrate across OS threads, `@thread_local` accesses within a synchronous segment between yields never race across threads.

**AXS-EXEC-053** (`Fiber<Y, R>`, `FiberState<Y, R>`, `FiberBuilder`, and `FiberScheduler` in `std/fiber/mod.ax`; `T423`, `0204 §9–10, §18–20, §31 AFIBER-27, AFIBER-32..34, AFIBER-38`, `tasks/0277 §10–15`).
Module `std.fiber` (`std/fiber/mod.ax`) defines the canonical stackful coroutine and cooperative fiber scheduler API:

```axiom
module std.fiber

@derive(Copy, Clone, Eq, PartialEq, Ord, Hash)
pub struct FiberId {
    pub id: u64,
}

pub enum FiberState<Y, R> {
    Yielded(Y),
    Completed(R),
    Panicked,
}

pub struct FiberBuilder {
    stack_commit: usize,
    stack_reserve: usize,
}

pub struct Fiber<Y, R> {
    raw_handle: i64,
    id: FiberId,
    slot: *mut u8,
}

pub struct FiberScheduler {
    ready_queue: Vec<Fiber<(), ()>>,
}
```

The canonical operations exposed by `std.fiber` are:

| Item / Method | Signature | Semantic Contract |
|---|---|---|
| `FiberBuilder.new` | `pub fn new() -> FiberBuilder` | Creates a default builder (`stack_commit = 65536`, `stack_reserve = 262144`). |
| `FiberBuilder.stack_size` | `pub fn stack_size(self, commit: usize, reserve: usize) -> FiberBuilder` | Sets explicit stack commit and reserve sizes in bytes (`0204 §4–5, §15`). |
| `FiberBuilder.spawn` | `pub fn spawn<F, Y, R>(self, f: F) -> Fiber<Y, R> where F: FnOnce() -> R` | Allocates a fiber control slot and stack via `host.fiber_create` in `Created` state without running `f` until the first `.resume()`. |
| `Fiber.new` / `Fiber.spawn` | `pub fn new<F, Y, R>(f: F) -> Fiber<Y, R> where F: FnOnce() -> R` | Spawns a fiber with default `FiberBuilder` settings. |
| `Fiber.id` | `pub fn id(self: view<Fiber<Y, R>>) -> FiberId` | Returns the unique `FiberId`. |
| `Fiber.is_completed` | `pub fn is_completed(self: view<Fiber<Y, R>>) -> bool` | Returns `true` iff the fiber has returned `Completed` or `Panicked`. |
| `Fiber.resume` | `pub fn resume(self: mut_view<Fiber<Y, R>>) -> FiberState<Y, R>` | Cooperatively switches execution from the caller into `self` (`host.fiber_resume`), returning `FiberState.Yielded(y)` when the fiber calls `yield_val(y)`, or `FiberState.Completed(r)` when `f()` returns `r` (`AFIBER-33`, `AFIBER-34`). |
| `yield_val` | `pub fn yield_val<Y>(val: Y)` | Moves `val: Y` into the active fiber's yield transfer slot and yields control back to the resumer via `host.fiber_yield` (`0204 §9`). |
| `yield_now` | `pub fn yield_now()` | Equivalent to `yield_val(())`; yields a `Fiber<(), R>` back to its resumer or `FiberScheduler` (`AFIBER-27`). |
| `FiberScheduler.new` | `pub fn new() -> FiberScheduler` | Creates a cooperative round-robin scheduler for `Fiber<(), ()>` instances on the current thread (`0204 §10, AFIBER-38`). |
| `FiberScheduler.spawn` | `pub fn spawn<F>(self: mut_view<FiberScheduler>, f: F) where F: FnOnce() -> ()` | Adds a new fiber to the scheduler's ready queue. |
| `FiberScheduler.run` | `pub fn run(self: mut_view<FiberScheduler>)` | Drives all queued fibers in deterministic FIFO round-robin order until every fiber reaches `Completed`, dropping each completed fiber cleanly. |

1. **Deterministic `Drop` cleanup on fiber completion and destruction (`0204 §18–20`, `tasks/0277 §13`)**:
   - When the fiber's entry closure `f()` returns `r: R`, all local variables inside `f()` are dropped in standard reverse lexical declaration order before the fiber trampoline stores `r` and yields terminal control back to the caller (`tasks/0277 §13`).
   - When `Fiber<Y, R>` is dropped (`impl<Y, R> Drop for Fiber<Y, R>`), it invokes `host.fiber_destroy(self.raw_handle)` and frees the control slot.

**AXS-EXEC-054** (Host-interface fiber intrinsics in `std.core.host`; `T423`, `SPEC-04 AXS-EXT-110, AXS-EXT-130`, `ADR-0002`, `0204 §6–8, §26–28 AFIBER-25..26, AFIBER-43`, `tasks/0277 §7–9`).
In accordance with `ADR-0002` and `SPEC-04 AXS-EXT-110`, stackful context creation, switching, and teardown cross four host intrinsics declared in `std/core/host.ax` (`module std.core.host`), implemented natively in `std/sys/windows/fiber.ax` (`__ax_host_fiber_*`) and deterministically in `compiler/interp/oracle.ax` and `compiler/interp/interp.ax`:

```axiom
module std.core.host

@intrinsic
pub unsafe fn fiber_create(entry: fn(*mut u8) -> i64, ctx: *mut u8, stack_commit: usize, stack_reserve: usize) -> i64 {
    0
}

@intrinsic
pub unsafe fn fiber_resume(h: i64, arg: i64, out_val: *mut i64) -> i64 {
    0
}

@intrinsic
pub fn fiber_yield(val: i64) -> i64 {
    0
}

@intrinsic
pub fn fiber_destroy(h: i64) -> i64 {
    0
}
```

The normative contract of each fiber host intrinsic is:

| Intrinsic | Signature | Return & Error Contract |
|---|---|---|
| `host.fiber_create` | `unsafe fn(entry: fn(*mut u8) -> i64, ctx: *mut u8, stack_commit: usize, stack_reserve: usize) -> i64` | Allocates a stackful fiber bound to the calling OS thread that will invoke `entry(ctx)` upon its first `fiber_resume`. `stack_commit == 0` / `stack_reserve == 0` use platform defaults (`64 KiB` / `256 KiB`). Returns handle `h >= 1` on success, `-4` (`InvalidInput`) if `entry` is null, or `-9` (`Other`) on stack allocation failure. |
| `host.fiber_resume` | `unsafe fn(h: i64, arg: i64, out_val: *mut i64) -> i64` | Saves the caller's execution context and switches into suspended fiber `h`, passing `arg` as the return value of `fiber_yield` (on subsequent resumes). When fiber `h` yields via `fiber_yield(v)` or returns `r` from `entry(ctx)`, stores `v` or `r` into `*out_val` (if `out_val != null`) and returns: `0` if `h` yielded (`Yielded`), `1` if `h` returned from `entry` (`Completed`), `2` if `h` panicked (`Panicked`), or `-4` (`InvalidInput`) if `h <= 0`, `h` belongs to a different OS thread, `h` is already `Running`, or `h` has already terminated/been destroyed. |
| `host.fiber_yield` | `fn(val: i64) -> i64` | Suspends the currently executing fiber, stores `val` into the resumer's `*out_val`, switches execution back to the caller that invoked `fiber_resume`, and returns the `arg` passed to the next `fiber_resume` when resumed. Returns `-4` (`InvalidInput`) if called outside an active fiber context (i.e., on the root thread context). |
| `host.fiber_destroy` | `fn(h: i64) -> i64` | Destroys fiber handle `h` and releases its stack and OS/oracle fiber record. Returns `0` on success, or `-4` (`InvalidInput`) if `h <= 0`, `h` belongs to a different thread, `h` was already destroyed, or `h` is currently `Running` (`AFIBER-31`, `AFIBER-45`). |

**AXS-EXEC-055** (Windows x64 native fiber implementation in `std/sys/windows/fiber.ax`; `T423`, `0204 §6–8, §26–28 AFIBER-25..26, AFIBER-43`, `tasks/0277 §7–9`).
On `x86_64-windows` (`std/sys/windows/fiber.ax`), `__ax_host_fiber_*` lowers onto Win32 kernel32 fiber primitives (`@link("kernel32")`):
1. **Thread-to-fiber conversion**: Before switching into a user fiber for the first time on an OS thread, `__ax_host_fiber_resume` checks `IsThreadAFiber()`; if `0`, it calls `ConvertThreadToFiberEx(null, 0)` (or `ConvertThreadToFiber(null)`) and records the root Win32 fiber pointer `GetCurrentFiber()` as the caller's return target.
2. **Fiber creation and trampoline (`CreateFiberEx`)**:
   - `__ax_host_fiber_create` allocates a `WinFiberSlot` storing `entry`, `ctx`, `owner_thread_id = GetCurrentThreadId()`, `caller_win_fiber: *mut u8` (supports nested fiber-resumes-fiber chains), `yield_or_ret: i64`, `resume_arg: i64`, `status: u32` (`0 = Suspended`, `1 = Running`, `2 = Completed`), and `win_fiber: *mut u8`.
   - Calls `CreateFiberEx(stack_commit, stack_reserve, 0, win32_fiber_trampoline, slot_ptr)`.
   - `win32_fiber_trampoline(lpParameter: *mut u8)` invokes `let ret = (slot.entry)(slot.ctx)`, sets `slot.yield_or_ret = ret` and `slot.status = 2` (`Completed`), and calls `SwitchToFiber(slot.caller_win_fiber)` (since a Win32 fiber entrypoint must never return via normal `ret`, `0204 §27–28`).
3. **Context switch (`SwitchToFiber`) and destruction (`DeleteFiber`)**:
   - `__ax_host_fiber_resume` verifies `slot.owner_thread_id == GetCurrentThreadId()` and `slot.status == 0`, saves the current active `WinFiberSlot` pointer and `slot.caller_win_fiber = GetCurrentFiber()`, sets `slot.status = 1`, and calls `SwitchToFiber(slot.win_fiber)`. Win32 `SwitchToFiber` saves and restores all Win64 ABI non-volatile registers (`RBX, RBP, RDI, RSI, R12..R15, XMM6..XMM15, RSP, RIP`) plus the TEB stack base/limit/deallocation pointers in user space without a kernel syscall (`0204 §6, §30`, `tasks/0277 §9`).
   - `__ax_host_fiber_yield(val)` writes `slot.yield_or_ret = val`, sets `slot.status = 0`, and calls `SwitchToFiber(slot.caller_win_fiber)`. When resumed, it returns `slot.resume_arg`.
   - `__ax_host_fiber_destroy(h)` verifies `slot.status != 1` (`Running` check, `AFIBER-31`) and `slot.owner_thread_id == GetCurrentThreadId()`, calls `DeleteFiber(slot.win_fiber)`, and frees `slot`.

**AXS-EXEC-056** (MIR interpreter oracle deterministic stackful fiber simulation; `T423`, `compiler/interp/oracle.ax`, `compiler/interp/interp.ax`, `INV-DET-003`).
In the MIR interpreter (`compiler/interp/`), `host.fiber_*` executes deterministically by maintaining a table of `InterpFiber` records:
1. Each `InterpFiber` stores its own independent call-frame stack (`frames: Vec<InterpFrame>`), `owner_thread_id: u64`, `caller_fiber_id: i64` (`0` when resumed from the thread's root call stack, or `> 0` when resumed from an outer fiber), `state: u32` (`Created`, `Running`, `Yielded`, `Completed`, `Destroyed`), `yield_val: i64`, and `resume_arg: i64`.
2. `host.fiber_resume(h, arg, out_val)` validates `h` (same `owner_thread_id`, not `Running`, not `Completed`/`Destroyed`), swaps the current thread's active `InterpFrame` stack with `fiber.frames`, and runs the interpreter step loop until either:
   - `host.fiber_yield(val)` is executed inside `h`: swaps the caller's `InterpFrame` stack back, writes `val` to `*out_val`, sets `fiber.state = Yielded`, and returns `0`; or
   - the bottom frame `entry(ctx)` of `h` returns `ret`: swaps the caller's `InterpFrame` stack back, writes `ret` to `*out_val`, sets `fiber.state = Completed`, and returns `1`.
3. `host.fiber_destroy(h)` verifies `fiber.state != Running` (`AFIBER-31`) and marks `fiber.state = Destroyed`.

---

## 6. Canonical Positive & Negative Examples

### 6.1 Positive Example 1: `LocalExecutor` with `!Send` (`Rc<T>`) Tasks & `AsyncMutex<T>` Across `.await`
```axiom
module example.local_executor_demo

use std.sync.Rc
use std.async.(LocalExecutor, AsyncMutex, yield_now)

pub async fn increment_local(rc_val: Rc<i64>, lock: Rc<AsyncMutex<i64>>) -> i64 {
    // Acquire AsyncMutexGuard and hold it safely across `.await`:
    let mut guard = lock.get_view().lock().await
    let base = *rc_val.get_view()
    yield_now().await
    *guard.get_mut() = *guard.get() + base
    let out = *guard.get()
    return out
}

pub fn main() -> i32 {
    let mut exec = LocalExecutor.new()
    let shared_rc = Rc.new(10i64)
    let shared_lock = Rc.new(AsyncMutex.new(5i64))

    // `spawn_local` accepts `!Send` futures capturing `Rc<T>`:
    let h1 = exec.spawn_local(increment_local(shared_rc.clone(), shared_lock.clone()))
    let h2 = exec.spawn_local(increment_local(shared_rc, shared_lock))

    let total = exec.run_until(async move {
        let a = h1.await.unwrap_or(0i64)
        let b = h2.await.unwrap_or(0i64)
        return a + b
    })

    if total == 40i64 {
        return 0i32
    }
    return 1i32
}
```

### 6.2 Positive Example 2: Multi-Threaded Work-Stealing `Executor`, `TaskGroup`, and Cooperative `CancellationToken`
```axiom
module example.structured_task_group_demo

use std.async.(Executor, TaskGroup, CancellationToken, yield_now)

pub async fn compute_chunk(id: i64, token: CancellationToken) -> i64 {
    if token.is_cancelled() {
        return 0i64
    }
    yield_now().await
    return id * 10i64
}

pub fn main() -> i32 {
    let exec = Executor.new(4)
    let sum = exec.block_on(async {
        let mut group = TaskGroup.new()
        let tok1 = group.cancellation_token()
        let tok2 = group.cancellation_token()

        group.spawn(view(exec), compute_chunk(1i64, tok1))
        group.spawn(view(exec), compute_chunk(2i64, tok2))

        let results = group.join_all().await
        match results {
            Result.Ok(vec) => return vec[0] + vec[1],
            Result.Err(_) => return -1i64,
        }
    })
    exec.shutdown()
    if sum == 30i64 {
        return 0i32
    }
    return 1i32
}
```

### 6.3 Positive Example 3: Stackful `Fiber<Y, R>` Deep Call-Stack Suspension & Resumption
```axiom
module example.fiber_ping_pong

use std.fiber.(Fiber, FiberState, yield_val)

pub fn deep_helper(step: i64) {
    yield_val(step * 10i64)
}

pub fn main() -> i32 {
    let mut fib: Fiber<i64, i64> = Fiber.new(|| -> i64 {
        deep_helper(1i64)
        deep_helper(2i64)
        return 99i64
    })

    let s1 = fib.resume()
    let s2 = fib.resume()
    let s3 = fib.resume()

    match (s1, s2, s3) {
        (FiberState.Yielded(10i64), FiberState.Yielded(20i64), FiberState.Completed(99i64)) => {
            return 0i32
        }
        _ => return 1i32,
    }
}
```

### 6.4 Negative Example: Passing a `!Send` Future or `Fiber` to Multi-Threaded `Executor.spawn` (`AX_ASYNC_FUTURE_NOT_SEND` / `AX_CONC_NOT_SEND`)
```axiom
module example.reject_non_send_spawn

use std.sync.Rc
use std.async.(Executor, yield_now)

pub async fn non_send_task() -> i32 {
    let local_rc = Rc.new(7i32)
    yield_now().await
    // `local_rc: Rc<i32>` is live across `.await`, so `non_send_task()` is `!Send`:
    return *local_rc.get_view()
}

pub fn bad_cross_thread_spawn(exec: view<Executor>) {
    let _h = exec.spawn(non_send_task()) // ERROR [AX_ASYNC_FUTURE_NOT_SEND]: `Future` is not `Send` (`Rc<i32>` held across `.await`)
}
```

---

## 7. Requirement & Conformance Traceability Matrix

### 7.1 Primary Requirements Covered by `T420` (`covers:`)

| Requirement ID | Summary (`spec/requirements/CATALOG.md`) | Governing Rules in `SPEC-34` |
|---|---|---|
| `REQ-CONC-023` | An async task execution context MUST be managed by an executor and need not correspond 1-to-1 to an OS thread. | `AXS-EXEC-002`, `AXS-EXEC-010`, `AXS-EXEC-011` |
| `REQ-ASY-036` | The language core must not require a specific executor or large runtime, allowing async execution in freestanding and embedded environments. | `AXS-EXEC-001`, `AXS-EXEC-003` |
| `REQ-ASY-040` | A `Future` passed to `spawn` in a multi-threaded executor must satisfy `Send` together with all values live across its suspension points. | `AXS-EXEC-011` |
| `REQ-ASY-051` | Panics within an async computation must be handled according to runtime profile and executor policy, triggering process termination when `panic=abort` is configured. | `AXS-EXEC-005`, `AXS-EXEC-007`, `AXS-EXEC-020` |
| `REQ-ASY-060` | The semantic test oracle must provide a deterministic single-threaded executor to verify async poll order, wake order, cancellation, and drop behavior independently of wall-clock timing. | `AXS-EXEC-016` |
| `REQ-ASY-067` | Rule `AASYNC-23`: A `Future` must not inherently require an executor. | `AXS-EXEC-001`, `AXS-EXEC-002` |
| `REQ-ASY-068` | Rule `AASYNC-24`: An executor must be treated as a library or runtime abstraction rather than a language primitive. | `AXS-EXEC-001`, `AXS-EXEC-002` |
| `REQ-ASY-089` | Invoking an `async fn` shall construct a state machine without automatically spawning a thread or relying on a built-in runtime executor. | `AXS-EXEC-001`, `AXS-EXEC-002` |
| `REQ-ASY-094` | The `?` operator inside an async function shall execute standard `Result` early-exit control flow without interacting with the async executor. | `AXS-EXEC-001` |
| `REQ-ASY-149` | Async functions and `Future` states do not implicitly spawn OS threads or create dedicated executors. | `AXS-EXEC-001`, `AXS-EXEC-002` |
| `REQ-CONC-149` | Forced external thread/task termination is prohibited as a safe primitive to preserve resource `Drop` consistency. | `AXS-EXEC-022`, `AXS-EXEC-051` |
| `REQ-ASY-156` | Async language syntax shall not implicitly link a runtime executor, and thread-safe semantics shall not require a thread runtime when no threads are spawned. | `AXS-EXEC-001` |
| `REQ-CONC-200` | `[ACONCUR-182]` Scheduler implementation is outside Core semantics. | `AXS-EXEC-001`, `AXS-EXEC-012` |
| `REQ-ASY-161` | The compiler must transform `async` and `await` constructs into a state machine based on control-flow and storage transformations rather than a runtime object model, and must not make the executor or runtime a mandatory part of the Core. | `AXS-EXEC-001` |
| `REQ-ASY-162` | The `async` and `await` constructs must be implemented as a compiler transformation of control-flow and storage rather than as a runtime object model, ensuring that the executor or runtime does not become a mandatory part of the Core. | `AXS-EXEC-001` |
| `REQ-ASY-163` | The `Executor` and `Task` components must not be made mandatory parts of the Core, but instead must be treated as a runtime or library subsystem with a clear compiler contract for scheduling and executing `Future`s. | `AXS-EXEC-001`, `AXS-EXEC-002`, `AXS-EXEC-003` |
| `REQ-ASY-164` | Axiom must keep the concepts of `Future` as computation, `Task` as an owned execution instance, and `Executor` as a scheduler completely independent, and must not conflate an asynchronous function directly with a `Task`. | `AXS-EXEC-002` |

### 7.2 Downstream `E11.5` Implementation Requirements Specified by `SPEC-34`

| Consumer Task | Requirement IDs | Governing Rules in `SPEC-34` |
|---|---|---|
| `T421` (`LocalExecutor`, work-stealing `Executor`, `TaskHandle`, atomic `Waker`, `AsyncMutex`, `AsyncSemaphore`, async channels) | `REQ-CONC-034`, `REQ-CONC-035`, `REQ-CONC-049`, `REQ-ASY-037`, `REQ-ASY-041`, `REQ-ASY-054`, `REQ-ASY-076`, `REQ-ASY-086`, `REQ-ASY-102`, `REQ-ASY-108`, `REQ-ASY-129`, `REQ-ASY-130`, `REQ-CONC-130`, `REQ-CONC-147`, `REQ-CONC-148`, `REQ-CONC-184`, `REQ-CONC-190` | `AXS-EXEC-002`..`AXS-EXEC-006`, `AXS-EXEC-010`..`AXS-EXEC-016`, `AXS-EXEC-030`..`AXS-EXEC-034` |
| `T422` (`TaskGroup` structured concurrency, `CancellationToken`, `Deadline`/`Timeout`, `ResourceGovernor`) | `REQ-CONC-040`, `REQ-ASY-019`, `REQ-ASY-109`, `REQ-CONC-100`, `REQ-CONC-150`, `REQ-CONC-155`, `REQ-CONC-188`, `REQ-CONC-199`, `REQ-ASY-153`, `REQ-ASY-159`, `REQ-ASY-167` | `AXS-EXEC-005`, `AXS-EXEC-007`, `AXS-EXEC-020`..`AXS-EXEC-025` |
| `T423` (Stackful `Fiber<Y, R>` runtime, `FiberScheduler` & `host.fiber_*` context switching) | `REQ-CONC-151`, `REQ-CONC-189` | `AXS-EXEC-050`..`AXS-EXEC-056` |
| `T424` (`E11.5` executor benchmarks, fiber & structured-cancellation conformance suite) | `REQ-ASY-165` | `AXS-EXEC-001`..`AXS-EXEC-056` |

---

## 8. Sources

- `spec/SPEC-04-core-extensibility.md` — `AXS-EXT-100` (intrinsic table), `AXS-EXT-110` (host-interface intrinsics `host.fiber_*`), `AXS-EXT-130` (`E11.5` extension points).
- `spec/SPEC-30-concurrency.md` — `AXS-CONC-001`..`AXS-CONC-050` (`ExecutionContext`, `Send`/`Share` auto-traits, closure capture and `Happens-Before` memory model).
- `spec/SPEC-31-atomics.md` — `AXS-ATM-001`..`AXS-ATM-066` (`Atomic<T>`, `Ordering`, and oracle vector-clock synchronization).
- `spec/SPEC-32-threads-sync.md` — `AXS-SYNC-001`..`AXS-SYNC-051` (`std.thread`, `@thread_local`, `Rc`/`Arc`, blocking `Mutex`/`RwLock`, `std.sync.channel`, `host.thread_*` and `host.futex_*`).
- `spec/SPEC-33-async.md` — `AXS-ASY-001`..`AXS-ASY-052` (`async fn`, `.await`, `Future<T>`, `Poll<T>`, `Waker`, `Context`, `block_on`, live-across-await analysis, state-machine lowering, and per-state `Drop` glue).
- `docs/base/specs/0202 - ASYNC-TASK-001 — Axiom TaskFutureScheduler Model.md` — §§1–27 (`AASYNC-51..70`: `Future` vs `Task` vs `TaskHandle`, hot/cold `TaskControlBlock`, `spawn` vs `spawn_local`, `TaskPool`, `TaskStorage`, cooperative cancellation).
- `docs/base/specs/0204 - FIBER-001 — Axiom Stackful Execution.md` — §§1–32 (`AFIBER-20..45`: stackful `Fiber`, explicit stack storage contract, `yield`, non-migratable `!Send` default, TLS interaction, Win64 context switching).
- `docs/base/specs/0205 - SCHEDULER-001.md` — §§1–41 (`ASCHED-20..50`: local queue fast path, work stealing of `Send` tasks, intrusive `TaskHeader` queue linkage, idempotent `wake()`, zero lost wakeups, `DeterministicExecutor`).
- `docs/base/tasks/0277 - BOOTSTRAP-019 — FIBER + SCHEDULER EXECUTION MODEL.md` — §§1–28 (separation of `Thread`, `Fiber`, `Task`, and `Future`; fiber stack lifetime invariants; scheduler work loop).
- `docs/base/tasks/0278 - BOOTSTRAP-020 — CHANNEL + LOCK-FREE RUNTIME PRIMITIVES.md` — §§1–27 (ownership-transferring channels, `SendError<T>` value recovery, bounded backpressure, async send/recv wakeups).
- `docs/base/tasks/0620 - BOOTSTRAP-361 — Axiom Async Executor, Task Model & Structured Concurrency Engine.md` — §§1–46 (`ATASK-01..30`: task lifecycle, structured concurrency scopes, sibling cancellation, explicit `detach`, `spawn_blocking`).
- `docs/base/tasks/0621 - BOOTSTRAP-362 — Axiom Synchronization Primitives & AsyncSync Coordination Engine.md` — §§1–56 (`ASYNC-LOCK-01`, `SYNC-01..29`: `AsyncMutex`, `AsyncRwLock`, `AsyncSemaphore`, async channels, cancellation-safety contracts).
- `docs/base/tasks/0834 - BOOTSTRAP-606.md` — §§606.0–606.25 (`ResourceGovernor`, hierarchical quotas, soft/hard limits, pressure states, and task/thread/memory accounting).
- `docs/base/tasks/0835 - BOOTSTRAP-607.md` & `docs/base/tasks/0836 - BOOTSTRAP-607 — Native Application Scheduling, Threading, Async Runtime & Executor 5.0.md` — Worker deques, global injection queue, fairness quantum, `Deadline`/`Timeout`, and `TaskGroup` failure propagation.
