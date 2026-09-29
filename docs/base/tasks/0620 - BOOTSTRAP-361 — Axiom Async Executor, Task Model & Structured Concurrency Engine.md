# BOOTSTRAP-361 — Axiom Async Executor, Task Model & Structured Concurrency Engine

`BOOTSTRAP-360` đã định nghĩa **Future và state machine**. Bước này đi tiếp lên tầng execution: làm thế nào Future thực sự được chạy, lập lịch, đánh thức và kết thúc.

Điểm quan trọng: **Executor/Task không được kéo vào Core bắt buộc.** Đây là runtime/library subsystem có compiler contract rõ ràng.

---

## 1. Phân tách 3 khái niệm

Axiom phải giữ ba khái niệm độc lập:

```text
Future
    = computation

Task
    = owned execution instance

Executor
    = scheduler
```

Không được đồng nhất:

```text
async fn → Task
```

Mà:

```text
async fn()
    ↓
Future<T>
    ↓
spawn(...)
    ↓
Task<T>
    ↓
Executor
```

Ví dụ:

```axiom
let f = download();
```

chỉ tạo Future.

```axiom
let task = spawn(f);
```

mới tạo execution instance.

---

# 2. Task là ownership boundary

Một `Task<T>` đại diện cho:

> một Future đã được giao cho executor chịu trách nhiệm tiến hành.

Task có ownership semantics.

Ví dụ:

```axiom
let task = spawn(work());
```

sau đó:

```axiom
let result = await task;
```

là chờ task hoàn thành.

Nếu task handle bị drop:

```axiom
drop(task);
```

thì **không mặc định có nghĩa task bị terminate**.

Task execution ownership thuộc executor.

Nếu muốn cancellation:

```axiom
task.cancel();
```

phải là API explicit.

---

# 3. Structured Concurrency

Axiom nên ưu tiên structured concurrency.

Ví dụ:

```axiom
scope {
    let a = spawn(work_a());
    let b = spawn(work_b());

    ...
}
```

scope phải có execution contract xác định:

```text
scope exit
    ↓
children completed
```

hoặc:

```text
scope exit
    ↓
cancel children
    ↓
wait children
```

Không được để child task “rơi” ngoài scope một cách ngầm định.

---

# 4. Detached task

Nếu programmer thật sự muốn task sống độc lập:

```axiom
detach(spawn(background_work()));
```

thì đây phải là hành động explicit.

Semantics:

```text
structured task
    → owned by scope

detached task
    → transferred to executor/application lifetime
```

Điều này tránh bug kiểu:

```text
function returns
    ↓
background task secretly survives
```

---

# 5. Task lifecycle

Task state semantic:

```text
CREATED
   ↓
READY
   ↓
RUNNING
   ↓
WAITING
   ↓
READY
   ↓
RUNNING
   ↓
COMPLETED
```

Có thể thêm:

```text
CANCELLING
CANCELLED
PANICKED
```

Nhưng đây là **execution state**, không phải Future semantic state.

Future vẫn chỉ cần:

```text
Ready
Pending
```

---

# 6. Task ≠ Future state

Future:

```text
state machine
```

Task:

```text
executor-owned execution record
```

Task có thể chứa:

```text
Future state
scheduler metadata
waker identity
completion result
cancellation state
```

nhưng implementation có thể fuse/eliminate các thành phần này.

Không bắt buộc:

```text
Task object
+ Future object
+ Waker object
```

là ba allocation riêng.

---

# 7. Executor abstraction

Executor chịu trách nhiệm:

```text
submit task
poll task
park task
wake task
schedule task
complete task
```

Core không quy định:

- thread pool;
- event loop;
- work stealing;
- single thread;
- multi thread;
- realtime scheduler.

Đó là execution policy.

---

# 8. Executor có thể có nhiều implementation

Ví dụ:

```text
SingleThreadExecutor
ThreadPoolExecutor
WorkStealingExecutor
IOExecutor
RealtimeExecutor
GPUExecutor
EmbeddedExecutor
DeterministicExecutor
```

Tất cả đều thực thi cùng Future semantic.

---

# 9. Waker model

Khi Future trả:

```text
Pending
```

nó phải có cơ chế để báo:

> “hãy poll tôi lại khi điều kiện tiến triển đã xảy ra.”

Waker là scheduling capability.

Không được hiểu:

```text
wake = execute immediately
```

mà:

```text
wake = make runnable
```

Executor quyết định khi nào poll.

---

# 10. Wake phải idempotent

Nếu:

```text
wake()
wake()
wake()
```

ba lần trước khi task chạy lại, executor không được bắt buộc tạo ba lần execution.

Semantic:

```text
WAITING → READY
```

nhiều wake liên tiếp vẫn có thể chỉ cần một ready queue entry.

---

# 11. Lost Wake Prevention

Đây là invariant rất quan trọng.

Trình tự:

```text
Future checks condition
Future registers waker
condition changes
wake()
Future returns Pending
```

có thể gây lost wake nếu implementation sai.

Executor/Future protocol phải đảm bảo registration và state transition có ordering phù hợp.

Compiler không tự sửa được bug này.

Do đó Async API contract phải có:

```text
poll registration protocol
```

rõ ràng.

---

# 12. Poll contract

Một Future `poll` phải tuân:

```text
poll(&mut state, context)
    → Ready(T)
    → Pending
```

Nếu trả `Pending`, Future phải:

- không mất ownership state;
- không làm hỏng invariant;
- có thể được poll lại;
- không yêu cầu executor poll liên tục nếu không có wake.

---

# 13. Poll không được block

Executor async thông thường yêu cầu:

```text
poll()
```

không blocking.

Không được:

```text
poll()
    ↓
sleep(1 second)
```

trừ khi executor profile đặc biệt định nghĩa blocking semantics.

Blocking I/O phải được:

- OS async API;
- reactor;
- worker pool;
- dedicated blocking executor;

xử lý bên ngoài Future semantic.

---

# 14. Blocking isolation

Library có thể cung cấp:

```axiom
spawn_blocking(fn() -> T)
```

để đưa blocking computation vào worker pool.

Nhưng:

```text
async fn
```

không tự biến blocking call thành async.

Đây là điểm rất quan trọng để tránh một ngôn ngữ “async” nhưng runtime thực tế vẫn bị block.

---

# 15. Executor và Send

Nếu executor cho phép task migrate:

```text
Worker A
   ↓
WAIT
   ↓
Worker B
```

thì Task/Future state phải thỏa:

```text
Send
```

Nếu executor single-thread/local:

```text
spawn_local
```

có thể bỏ yêu cầu `Send`.

Compiler kiểm tra dựa trên execution contract.

---

# 16. Task migration

Task có thể được migration nếu:

```text
Future state: Send
Waker state: Send
Executor metadata: Send
```

Nếu có local-only state:

```text
PinnedExecution
```

executor không được migrate.

---

# 17. Work Stealing

Work-stealing là implementation strategy, không phải semantic feature.

Ví dụ:

```text
Worker A deque
Worker B deque

A idle
 ↓
steal task
```

Compiler không cần biết task được steal.

Chỉ cần execution contract:

```text
Task may migrate
```

và Send verification.

---

# 18. Queue semantics

Executor cần scheduler queue abstraction.

Core semantic không bắt buộc queue ordering.

Executor có thể:

```text
FIFO
LIFO
priority
deadline
work stealing
fair queue
```

Tuy nhiên nếu application cần deterministic ordering, executor phải cung cấp explicit deterministic mode.

---

# 19. Structured task tree

Structured concurrency có thể biểu diễn:

```text
Root Task
├── Child A
│   ├── Child A1
│   └── Child A2
└── Child B
```

Parent scope không hoàn thành trước khi children hoàn tất hoặc được cancellation theo contract.

Compiler/library có thể giữ:

```text
TaskScope
```

nhưng đây là runtime/library abstraction, không phải Core object model.

---

# 20. Error propagation

Nếu child task trả:

```text
Result<T, E>
```

parent có thể:

```axiom
let a = await child_a?;
```

Nếu child panic:

```text
panic
```

thì propagation policy của structured scope phải xác định.

Một mô hình đơn giản:

```text
child failure
    ↓
scope failure
    ↓
cancel siblings
    ↓
await sibling termination
    ↓
propagate failure
```

Nhưng đây là **library policy**, không phải hard-coded Core semantics.

---

# 21. Cancellation tree

Structured tasks có thể có:

```text
CancellationScope
```

Ví dụ:

```text
Parent cancellation
       ↓
  ┌────┴────┐
 Child A   Child B
    ↓         ↓
 cancelled cancelled
```

Cancellation token nên được thiết kế như capability/value, không phải global flag.

---

# 22. Cancellation race

Các trạng thái:

```text
COMPLETED
CANCELLED
PANICKED
```

có thể race.

Executor phải định nghĩa winner semantics.

Ví dụ:

```text
task completes
cancel requested
```

nếu completion đã linearized trước cancellation:

```text
COMPLETED
```

Nếu cancellation linearized trước:

```text
CANCELLED
```

Không được có trạng thái mơ hồ.

---

# 23. Cancellation không rollback side effects

Ví dụ:

```axiom
await send_packet();
```

Nếu cancellation xảy ra sau khi packet đã gửi, cancellation không “undo” packet.

Đây là nguyên tắc:

> Cancellation là control-flow/resource policy, không phải transaction rollback.

Nếu cần rollback, application phải dùng transaction abstraction.

---

# 24. Task result ownership

Khi task hoàn thành:

```text
Task<T>
    ↓
Result<T>
```

ownership của `T` phải chuyển sang consumer.

Không copy ngầm.

Ví dụ:

```text
worker
   ↓ Move
completion storage
   ↓ Move
awaiting task
```

Compiler có thể tối ưu thành direct result slot.

---

# 25. Task result storage

Không bắt buộc:

```text
heap allocation
```

Nếu parent và child có thể được compiler/runtime fusion:

```text
child result
    ↓
parent local
```

có thể dùng caller-provided storage.

---

# 26. Task fusion

Compiler/runtime có thể phát hiện:

```axiom
await spawn(f());
```

và nếu task không escape:

```text
spawn
 ↓
executor enqueue
 ↓
dequeue
 ↓
poll
```

có thể được optimize thành:

```text
direct execution of f()
```

nếu không thay đổi observable scheduling semantics.

Đây là một optimization quan trọng cho async abstraction.

---

# 27. Task allocation elimination

Nếu:

```axiom
let task = spawn_local(f());
let x = await task;
```

task không escape và executor cho phép synchronous/local optimization:

```text
Task allocation
```

có thể biến mất.

Không được mặc định heap allocate mọi task.

---

# 28. Executor context

Future poll nhận một execution context conceptually:

```text
PollContext {
    waker
    cancellation
    executor_caps
}
```

Nhưng không nhất thiết physical struct.

Compiler/runtime có thể truyền các thành phần cần thiết riêng lẻ.

---

# 29. Async-local storage

Một executor có thể cung cấp:

```text
TaskLocal<T>
```

khác với:

```text
ThreadLocal<T>
```

Task-local state phải obey task ownership/lifetime.

Không nên làm task-local thành hidden global mutable state trong Core.

---

# 30. Thread-local ≠ Task-local

Ví dụ:

```text
Task migrates:
Worker A → Worker B
```

Thread-local state thay đổi.

Task-local state phải giữ nguyên nếu abstraction yêu cầu.

Do đó:

```text
TLS
```

và:

```text
TaskLocal
```

là hai storage domains khác nhau.

---

# 31. Async synchronization

Mutex:

```text
Mutex<T>
```

và async mutex:

```text
AsyncMutex<T>
```

không nên là cùng một abstraction.

`MutexGuard`:

```text
cannot cross await
```

mặc định.

`AsyncMutexGuard`:

```text
may cross await
```

nếu implementation và capability contract cho phép.

---

# 32. Không giữ sync lock qua await

Ví dụ:

```axiom
let guard = mutex.lock();
await network();
modify(data);
```

reject mặc định.

Lý do:

```text
thread blocked by logical async suspension
```

có thể tạo deadlock/starvation.

Compiler diagnostic:

```text
error AASYNC-...
synchronous lock guard is live across await
```

Nếu abstraction đặc biệt đảm bảo an toàn, nó phải có execution contract riêng.

---

# 33. Async channel

Channel là abstraction đặc biệt phù hợp async.

```axiom
let (tx, rx) = channel();

spawn(producer(tx));

let x = await rx.receive();
```

`receive()` trả Future.

Không cần:

```text
thread per receive
```

Waker được đăng ký khi channel empty.

Khi sender gửi:

```text
channel state
   ↓
wake receiver
```

---

# 34. Bounded channel

Axiom nên ưu tiên bounded channel:

```text
capacity = N
```

vì:

- kiểm soát memory;
- backpressure;
- predictable performance.

Unbounded channel phải là explicit abstraction.

---

# 35. Async backpressure

Nếu queue đầy:

```text
send()
```

có thể trả:

```text
Pending
```

và task được wake khi có capacity.

Đây là cách async scheduler kết hợp tự nhiên với ownership:

```text
send(buffer)
```

có thể transfer ownership khi accepted.

---

# 36. Zero-copy channel

Nếu:

```text
send(Buffer)
```

thì ownership có thể:

```text
Producer
   ↓ Move
Channel
   ↓ Move
Consumer
```

Không cần copy buffer.

Đây là một trong những lợi thế quan trọng của Axiom ownership model.

---

# 37. Executor memory ordering

Scheduler queue cần atomic/synchronization semantics.

Ví dụ work stealing:

```text
producer
   ↓
publish task
   ↓ Release
queue
   ↓ Acquire
worker
```

Phải sử dụng memory ordering đã định nghĩa trong concurrency model.

Không tạo memory model riêng cho async.

---

# 38. Executor shutdown

Executor cần lifecycle:

```text
RUNNING
    ↓
STOP_REQUESTED
    ↓
DRAINING
    ↓
STOPPED
```

Policy có thể:

```text
drain existing tasks
cancel tasks
reject new tasks
wait
```

nhưng phải explicit.

---

# 39. Runtime-free programs

Chương trình:

```axiom
fn main() {
    ...
}
```

không sử dụng async:

→ không link executor.

Chương trình:

```axiom
async fn main() {
    ...
}
```

cần executor, nhưng executor có thể là:

- standard library;
- embedded runtime;
- application runtime;
- user-defined executor.

Không có monolithic Axiom runtime bắt buộc.

---

# 40. Deterministic executor

Standard tooling nên có executor deterministic cho test:

```text
Task A
Task B
Task C
```

Scheduler có thể kiểm soát:

```text
virtual time
wake order
poll order
task interleaving
```

Điều này cực kỳ hữu ích cho testing race/async logic.

Nhưng deterministic scheduler không thay đổi language semantics.

---

# 41. Executor instrumentation

Compiler/runtime tooling nên có:

```text
task creation
task wake
task poll
task suspend
task resume
task completion
task cancellation
```

events.

Profiler có thể hiển thị:

```text
Task A
  running 2.3 ms
  waiting 17.4 ms
  running 0.2 ms
```

Không cần runtime introspection trong release binary nếu không bật.

---

# 42. CompilerDB

Thêm:

```text
ExecutorDB
ExecutorProfileDB
TaskDB
TaskStateDB
TaskScopeDB
TaskSpawnDB
TaskCancellationDB
TaskWakeDB
TaskMigrationDB
TaskCompletionDB
WakerDB
PollContextDB
AsyncSchedulerDB
AsyncChannelDB
AsyncSynchronizationDB
AsyncRuntimeDB
```

Các query:

```text
task_contract(FunctionId)
task_send(TaskId)
task_migration(TaskId)
task_scope(TaskId)
task_cancellation(TaskId)
executor_requirements(TaskId)
async_runtime_requirements(ModuleId)
```

---

# 43. Compiler/runtime contract

Compiler phải xuất ra metadata:

```text
TaskRequirements {
    send
    share
    migratable
    local_only
    cancellation_safe
    blocking
    runtime_features
}
```

Executor dùng metadata để reject configuration không hợp lệ.

Ví dụ:

```text
Future requires Send
Executor is local-only
```

không phải lỗi.

Ngược lại:

```text
Future !Send
Executor requires migration
```

→ compile-time/API-level error.

---

# 44. Blocking annotation

Compiler có thể suy luận:

```text
MayBlock
NonBlocking
UnknownBlocking
```

Từ call graph.

Ví dụ:

```axiom
async fn f() {
    blocking_io();
}
```

có thể diagnostic:

```text
warning:
blocking operation occurs inside async execution
```

Nếu API contract yêu cầu nonblocking:

```text
error
```

Đây là effect analysis, không phải một async-specific type.

---

# 45. Structured concurrency invariants

Đóng băng:

```text
ATASK-01
Future is a computation, not an execution instance.

ATASK-02
Task represents an execution instance.

ATASK-03
Executor is responsible for scheduling tasks.

ATASK-04
Creating a Future does not spawn execution.

ATASK-05
spawn explicitly transfers a Future to executor execution.

ATASK-06
Task ownership is explicit.

ATASK-07
Dropping a Task handle does not implicitly terminate execution.

ATASK-08
Cancellation is explicit.

ATASK-09
Structured child tasks obey their parent scope contract.

ATASK-10
Detached execution must be explicit.

ATASK-11
Executor migration requires Send-compatible state.

ATASK-12
Local execution may avoid Send requirements.

ATASK-13
Waker notification is not immediate execution.

ATASK-14
Waker notification is idempotent.

ATASK-15
Executor must prevent lost wakeups.

ATASK-16
Future polling must obey the Future poll contract.

ATASK-17
Ordinary async poll operations must not block.

ATASK-18
Blocking work requires an explicit blocking execution path.

ATASK-19
Task result ownership is transferred, not implicitly copied.

ATASK-20
Task result storage does not require mandatory heap allocation.

ATASK-21
Task creation does not require mandatory heap allocation.

ATASK-22
Task fusion is permitted when semantics remain equivalent.

ATASK-23
Task allocation elimination is permitted when the task does not escape.

ATASK-24
Task-local storage differs from thread-local storage.

ATASK-25
Synchronous guards cannot cross await by default.

ATASK-26
Async synchronization uses explicit async-aware abstractions.

ATASK-27
Async cancellation does not imply rollback of external side effects.

ATASK-28
Executor scheduling does not define language-level memory semantics.

ATASK-29
Async execution reuses Axiom ownership, capability and memory models.

ATASK-30
Programs not using async do not depend on an async executor.
```

---

## 46. Kiến trúc async hoàn chỉnh sau 360–361

Bây giờ tầng async của Axiom được chia rất sạch:

```text
                 ┌──────────────────────┐
                 │      async fn        │
                 └──────────┬───────────┘
                            ↓
                       Future<T>
                            │
                    BOOTSTRAP-360
                            ↓
                    State Machine
                            │
                            ↓
                         Poll()
                            │
                     Pending / Ready
                            │
                            ↓
                 ┌──────────────────────┐
                 │       Task           │
                 └──────────┬───────────┘
                            │
                    BOOTSTRAP-361
                            ↓
                       Executor
                            │
             ┌──────────────┼──────────────┐
             ↓              ↓              ↓
          ThreadPool     EventLoop     LocalExecutor
```

Trong khi đó:

```text
Ownership
    ↓
Cleanup Engine
    ↓
Future State Cleanup

Capability
    ↓
Send / Share
    ↓
Task Migration

Memory Model
    ↓
Executor Queue Synchronization
```

Tức là **không tạo một “async universe” riêng**. Async chỉ sử dụng những semantic primitive Axiom đã xây dựng trước đó.