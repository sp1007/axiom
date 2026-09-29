# BOOTSTRAP-176 — Concurrency Runtime, Threading, Synchronization & Scheduler Implementation
**FROZEN / COMPLETED**

Task này không thay đổi semantic concurrency đã đóng băng ở các task trước. Nó chuyển câu hỏi từ:

> “Axiom cho phép concurrency như thế nào?”

sang:

> “Axiom thực thi concurrency đó trên OS/hardware như thế nào mà không kéo theo một runtime nặng?”

Nguyên tắc trung tâm:

> **Concurrency semantics thuộc Axiom; scheduler, thread pool, event loop và runtime policy thuộc library/system layer.**

---

# 176.1. Không có một "Axiom runtime" duy nhất

Một chương trình đơn giản:

```ax
fn main() {
    println("hello");
}
```

không được tự động link:

```text
thread scheduler
async executor
timer wheel
channel runtime
TLS runtime
IO reactor
```

Nếu chương trình chỉ dùng:

```text
CPU + stack + stdout
```

thì binary chỉ nhận các component cần thiết.

---

# 176.2. Ba tầng concurrency

```text
Axiom language semantics
        ↓
Concurrency library
        ↓
Platform runtime/system backend
```

Ví dụ:

```text
spawn(...)
    ↓
std::thread
    ↓
Windows thread / pthread / native OS API
```

Async:

```text
async fn
    ↓
Future
    ↓
executor
    ↓
epoll / IOCP / kqueue / io_uring / platform API
```

---

# 176.3. Thread

Thread là execution domain thật sự.

Semantic object:

```text
ThreadHandle
```

có thể đại diện cho:

```text
OS thread
```

nhưng implementation không bắt buộc 1:1 nếu abstraction cho phép.

---

# 176.4. Thread creation

Conceptually:

```ax
let handle = spawn(fn() {
    work();
});
```

Compiler kiểm tra:

```text
closure captures
    ↓
Send
    ↓
storage/escape
    ↓
thread execution
```

Nếu closure capture một giá trị không `Send`:

```text
compile error
```

---

# 176.5. Thread ≠ async task

Đây là invariant rất quan trọng:

```text
Thread
    = execution resource

Task/Future
    = scheduling abstraction
```

Một thread có thể chạy nhiều tasks.

Một task không nhất thiết tạo OS thread.

---

# 176.6. Thread runtime

Thread component chỉ được link khi cần:

```text
Program
 ├── Thread
 ├── Sync
 └── TLS
```

Nếu không có thread:

```text
Thread runtime = absent
```

---

# 176.7. OS thread abstraction

Axiom không cần expose toàn bộ platform thread internals.

API high-level:

```ax
thread::spawn(...)
thread::join(...)
thread::current()
thread::yield_now()
```

Platform-specific API:

```text
std::os::windows::thread
std::os::linux::thread
...
```

nằm riêng.

---

# 176.8. Thread stack

Thread stack là runtime/platform resource.

Compiler không giả định:

```text
stack size = X
```

trừ khi explicit thread configuration.

---

# 176.9. Stackful vs stackless

Axiom có hai execution abstractions:

```text
OS Thread / Fiber
    = stackful

Future
    = stackless state machine
```

Async mặc định không cần stack riêng.

---

# 176.10. Fiber

Fiber là execution domain tùy chọn:

```text
Fiber
 ├── stack
 ├── execution state
 └── scheduler
```

Compiler/runtime có thể hỗ trợ:

```text
yield
resume
switch
```

nhưng Core không cần fiber primitive.

---

# 176.11. Task

Task là đơn vị scheduler chạy.

```text
Task {
    Future
    state
    scheduler metadata
    cancellation state
}
```

Task không nhất thiết là heap object nếu compiler/runtime có thể stack/inline hóa.

---

# 176.12. Spawn

Có sự khác biệt:

```text
spawn
spawn_local
```

### `spawn`

Yêu cầu:

```text
Future: Send
```

nếu task có thể migrate giữa workers.

### `spawn_local`

Task không cần `Send` nếu executor đảm bảo:

```text
same execution domain
```

---

# 176.13. Work stealing

Thread pool có thể:

```text
Worker 0 → local deque
Worker 1 → local deque
Worker 2 → local deque
...
```

Worker ưu tiên:

```text
local task
```

khi hết việc:

```text
steal from another worker
```

---

# 176.14. Scheduler không phải semantic authority

Scheduler có thể quyết định:

```text
which task runs first
which worker executes it
when it is migrated
```

nhưng không được thay đổi:

```text
ownership
memory ordering
observable synchronization semantics
```

---

# 176.15. Scheduler nondeterminism

Hai executions:

```text
Task A
Task B
```

có thể chạy theo:

```text
A → B
```

hoặc:

```text
B → A
```

nếu program không tạo ordering constraint.

Axiom không biến scheduler order thành hidden semantic guarantee.

---

# 176.16. Happens-before vẫn là authority

Ví dụ:

```text
send(channel, x)
receive(channel)
```

tạo synchronization relationship theo channel contract.

Scheduler không thể bỏ qua.

---

# 176.17. Mutex

Semantic model:

```text
Mutex<T>
```

có:

```text
lock() -> Guard<T>
```

Guard là ownership-bearing capability.

```text
Guard<T>
    !Copy
    Drop => unlock
```

---

# 176.18. Guard không phải pointer/reference primitive

Programmer dùng:

```ax
let guard = mutex.lock();
guard.update();
```

thay vì:

```text
T*
T&
lifetime
borrow
```

Compiler vẫn internally theo dõi:

```text
capability
provenance
lifetime
```

---

# 176.19. Mutex implementation

Platform implementation có thể dùng:

```text
futex
SRWLock
pthread_mutex
parking lot
spin-then-park
```

nhưng semantic abstraction vẫn:

```text
Mutex<T>
```

---

# 176.20. No universal fairness guarantee

Axiom Core không hứa:

```text
FIFO
fair
starvation-free
```

trừ khi một synchronization primitive cụ thể contract điều đó.

Điều này cho phép runtime chọn implementation phù hợp.

---

# 176.21. RwLock

```text
read → multiple readers
write → exclusive
```

Guard:

```text
ReadGuard<T>
WriteGuard<T>
```

có capability tương ứng:

```text
READ
WRITE
```

---

# 176.22. Semaphore

```text
Semaphore
    ↓
Permit
```

Permit:

```text
!Copy
Drop → release
```

Điều này rất phù hợp với ownership model của Axiom.

---

# 176.23. Condition variable

Semantic:

```text
wait()
```

phải:

```text
release mutex
sleep
reacquire mutex
return
```

Wakeup không đồng nghĩa predicate đã đúng.

Program vẫn phải:

```text
while !condition {
    wait();
}
```

hoặc equivalent abstraction.

---

# 176.24. Atomic

Atomic không phải synchronization object.

```text
Atomic<T>
```

là memory operation primitive.

Các order:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

được giữ nguyên semantics đã đóng băng.

---

# 176.25. Atomic ≠ ordinary mutable view

Không cho phép:

```text
Atomic<T>
    ↓
mut_view<T>
```

một cách implicit.

Nếu làm vậy compiler có thể mất atomicity.

---

# 176.26. Atomic wait/notify

```text
atomic.wait(value)
atomic.notify_one()
```

phải phân biệt:

```text
notification
```

với:

```text
publication/order
```

Notify không tự tạo happens-before nếu memory ordering không tạo nó.

---

# 176.27. Spinlock

Có thể có library:

```text
SpinLock<T>
```

nhưng đây là implementation policy.

Compiler không coi mọi lock là spinlock.

---

# 176.28. Adaptive locking

Runtime có thể:

```text
spin briefly
   ↓
if contention
   ↓
park thread
```

để tránh syscall khi critical section ngắn.

Không thay đổi semantic model.

---

# 176.29. Parking

Scheduler/runtime có thể có:

```text
Park
Unpark
```

primitive nội bộ.

Đây là mechanism, không phải Core language feature.

---

# 176.30. Channel

Channel là ownership transfer abstraction:

```text
Sender<T>
Receiver<T>
```

Send:

```text
T ownership
    ↓
channel
    ↓
receiver
```

Không cần clone.

---

# 176.31. Channel message

Nếu:

```text
let x = LargeObject;
tx.send(x);
```

ownership chuyển sang receiver.

```text
x
```

không còn hợp lệ.

Physical implementation có thể:

```text
move
pointer swap
ring-buffer slot
register/stack optimization
```

---

# 176.32. Bounded channel

Mặc định implementation nên ưu tiên bounded channel khi có thể:

```text
ring buffer
```

để kiểm soát:

```text
memory growth
cache locality
backpressure
```

---

# 176.33. Channel variants

Library có thể specialize:

```text
SPSC
MPSC
SPMC
MPMC
```

Compiler/runtime có thể chọn implementation dựa trên type/usage.

API semantics không đổi.

---

# 176.34. Channel ordering

Guarantee:

```text
same sender
→ FIFO
```

không nhất thiết:

```text
global ordering
```

giữa nhiều senders.

---

# 176.35. Async channel

Async channel không tạo OS thread cho mỗi wait.

Flow:

```text
send
 ↓
queue
 ↓
wake waiting task
 ↓
executor schedules task
```

---

# 176.36. Waker

Waker là scheduling notification mechanism.

```text
Future::poll()
    ↓
Pending(waker)
```

Khi I/O/event sẵn sàng:

```text
wake()
```

Scheduler đưa task trở lại READY.

---

# 176.37. Waker không chạy Future

`wake()` chỉ:

```text
notify scheduler
```

Không có semantics:

```text
wake() == execute_now()
```

---

# 176.38. Waker idempotence

Nhiều wake:

```text
wake()
wake()
wake()
```

không được yêu cầu tạo ba task execution.

Scheduler có thể coalescing:

```text
WAITING → READY
```

một lần.

---

# 176.39. Executor state machine

Conceptually:

```text
CREATED
   ↓
READY
   ↓
RUNNING
   ↓
┌───────┬──────────┐
↓       ↓          ↓
READY  WAITING   COMPLETED
         │
         └── wake → READY
```

Cancellation là state khác.

---

# 176.40. Future polling

Future phải được poll độc quyền:

```text
poll(&mut future)
```

Không được hai workers cùng poll một Future nếu không có explicit synchronization abstraction.

---

# 176.41. Future migration

Nếu Future:

```text
Send
```

thì scheduler có thể:

```text
Worker 1
   ↓
Worker 2
```

Nếu không:

```text
spawn_local
```

và task pinned vào execution domain phù hợp.

---

# 176.42. Future state

Compiler transform:

```ax
async fn foo() {
    let x = load().await;
    process(x);
}
```

thành semantic state machine:

```text
State0
State1 { x }
State2
Completed
```

Chỉ values live across await trở thành state fields.

---

# 176.43. Executor storage

Future/task storage có thể:

```text
stack
inline
arena
pool
heap
```

Compiler/runtime chọn tùy abstraction.

Không có rule:

```text
async = heap allocation
```

---

# 176.44. Stack pinning

Future không mặc định yêu cầu stable address.

Nếu một Future cần stable address:

```text
explicit storage contract
```

mới ngăn relocation.

Không đưa `Pin<T>` vào Core.

---

# 176.45. Async I/O architecture

Axiom nên hỗ trợ abstraction:

```text
Async IO
    ↓
OS completion mechanism
```

platform backend:

```text
Linux
 ├── io_uring
 ├── epoll
 └── ...
 
Windows
 └── IOCP
 
macOS
 └── kqueue / platform APIs
```

Executor không cần biết semantic details của từng OS ở high level.

---

# 176.46. Reactor vs proactor

Runtime có thể sử dụng:

```text
Reactor
```

hoặc:

```text
Proactor
```

hoặc hybrid.

Không đưa lựa chọn này vào Core.

---

# 176.47. Timer

Async timer là runtime/library component:

```text
sleep(duration)
timeout(future)
interval(...)
```

Implementation có thể:

```text
timer wheel
min heap
OS timer
hierarchical wheel
```

---

# 176.48. Timer không tạo thread bắt buộc

Không được:

```text
sleep async
→ create thread
```

mặc định.

Executor/timer runtime có thể multiplex nhiều timers.

---

# 176.49. Cancellation

Cancellation là explicit control mechanism:

```text
CancellationToken
CancellationSource
```

Future có thể observe:

```text
is_cancelled()
```

hoặc return cancellation error.

---

# 176.50. Cancellation ≠ panic

Ba trạng thái:

```text
success
failure
cancelled
```

không nên nhập thành một semantic state.

Ví dụ:

```text
Result<T, Error>
```

và cancellation policy có thể là:

```text
Cancelled
```

trong error domain.

---

# 176.51. Dropping Future

Drop Future:

```text
Future
 ↓
Drop
```

không mặc định nghĩa:

```text
cancel external operation
```

Nếu I/O đang chạy, resource operation có contract riêng.

---

# 176.52. Structured concurrency

Axiom runtime nên ưu tiên:

```text
scope {
    spawn(task1);
    spawn(task2);
}
```

Scope không kết thúc cho tới khi child tasks:

```text
complete
cancel
propagate failure
```

theo contract.

---

# 176.53. Detached task

Detached execution phải explicit:

```text
detach(handle)
```

Không để:

```text
spawn(...)
```

ngầm tạo task sống vô thời hạn mà programmer không biết.

---

# 176.54. JoinHandle

`JoinHandle<T>` là capability quan sát execution.

Có thể:

```text
await
join
cancel
inspect status
```

tùy API.

Dropping handle không nhất thiết terminate task.

---

# 176.55. Child failure

Structured task group có policy:

```text
fail-fast
collect-all
ignore
custom
```

Đây là library semantics, không phải Core panic semantics.

---

# 176.56. Scheduler queues

Worker:

```text
LocalDeque
```

Global:

```text
GlobalInjectQueue
```

Remote wake:

```text
RemoteQueue
```

Có thể dùng lock-free queue hoặc mutex queue tùy target/profile.

---

# 176.57. Scheduler affinity

Task có thể có:

```text
AnyWorker
PinnedWorker
CPUSet
NUMANode
GPUDevice
ExecutionDomain
```

Nhưng mặc định:

```text
AnyWorker
```

nếu `Send`.

---

# 176.58. NUMA

Runtime có thể hỗ trợ:

```text
NUMA affinity
local allocation
worker placement
```

nhưng không đưa NUMA semantics vào Core.

---

# 176.59. Priority

Task priority:

```text
high
normal
low
```

là scheduler policy.

Không tạo memory ordering semantics.

---

# 176.60. Real-time execution

Một runtime profile có thể yêu cầu:

```text
real-time
```

và cấm:

```text
unbounded allocation
blocking locks
unbounded scheduler latency
```

Nhưng đây là execution profile, không phải Core semantics.

---

# 176.61. Deterministic executor

Testing runtime nên có:

```text
DeterministicExecutor
```

cho phép kiểm soát:

```text
task scheduling
wake ordering
timer advancement
```

nhằm test concurrency reproducibly.

---

# 176.62. Deterministic scheduler không thay đổi production semantics

Nó chỉ là testing implementation.

Production:

```text
real scheduler
```

vẫn phải tuân thủ semantic memory/concurrency model.

---

# 176.63. Race detection

Compiler đã đảm bảo safe data race absence trong safe code.

Runtime tooling vẫn có thể cung cấp:

```text
race detector
```

để phát hiện:

```text
unsafe bugs
FFI bugs
runtime bugs
```

Tooling không thay đổi semantics.

---

# 176.64. Deadlock detection

Deadlock không nhất thiết là language error.

Runtime/tooling có thể detect:

```text
lock graph
cycle
```

nhưng Core không hứa compile-time phát hiện mọi deadlock.

---

# 176.65. Lock ordering

Library có thể hỗ trợ:

```text
LockClass
LockOrder
```

để tooling phân tích.

Không cần programmer viết lifetime/borrow annotation.

---

# 176.66. Atomic reference counting

`Arc<T>` implementation:

```text
strong count
weak count
```

dùng atomic operations.

Nhưng:

```text
Arc<T>
```

không biến T thành mutable shared object.

---

# 176.67. Arc + Mutex

Pattern:

```text
Arc<Mutex<T>>
```

semantic:

```text
Arc
 = shared ownership

Mutex
 = synchronized mutable access
```

Hai mechanism độc lập.

---

# 176.68. Rc + RefCell-like designs

Axiom không cần copy Rust API 1:1.

Có thể có:

```text
Rc<T>
LocalCell<T>
```

nhưng compiler capability system nên chịu trách nhiệm càng nhiều càng tốt.

Không khuyến khích runtime borrow checking cho ordinary code nếu compile-time proof có thể làm được.

---

# 176.69. Shared immutable optimization

Nếu compiler chứng minh:

```text
Arc<T>
```

không có mutation và ownership không observable theo cách cần refcount, có thể tối ưu một số operation.

Nhưng không được biến shared semantics thành unique nếu identity/refcount observation là observable.

---

# 176.70. Executor memory allocation

Executor không được mặc định:

```text
one malloc per task
```

Runtime có thể dùng:

```text
slab
arena
object pool
intrusive queue
inline task storage
```

tùy Future/task shape.

---

# 176.71. Task allocation elimination

Nếu:

```text
spawn_local(...)
```

được compiler chứng minh bounded/nonescaping và executor API cho phép inline execution, task allocation có thể loại bỏ.

Nếu task detached/escapes:

```text
heap/arena/pool
```

có thể cần.

---

# 176.72. Async runtime components

Không phải một monolithic async runtime.

Có thể link:

```text
AsyncCore
Executor
Timer
IO
Network
Cancellation
```

độc lập.

---

# 176.73. Thread runtime components

Tương tự:

```text
Thread
TLS
Sync
Scheduler
CPU affinity
NUMA
```

chỉ link khi cần.

---

# 176.74. Shutdown

Runtime phải có explicit lifecycle:

```text
START
  ↓
RUNNING
  ↓
QUIESCING
  ↓
SHUTDOWN
```

Không phụ thuộc vào hidden global destructors.

---

# 176.75. Process exit

Nếu `main` return:

```text
runtime shutdown
 ↓
required cleanup
 ↓
exit code
```

Runtime component finalization phải deterministic.

---

# 176.76. Thread shutdown

Programmer không được mặc định có:

```text
global thread termination
```

Nếu structured threads còn sống:

```text
scope
```

phải quản lý lifecycle.

Detached threads là explicit policy.

---

# 176.77. TLS

TLS component chỉ link khi:

```text
thread_local
```

hoặc runtime component yêu cầu.

TLS initialization/finalization target-specific.

---

# 176.78. Thread-local Drop

Nếu TLS object có Drop:

```text
thread exit
 ↓
TLS cleanup
```

phải đảm bảo deterministic semantics.

Ordering giữa TLS destructors và foreign runtime destructors là platform-specific ABI contract.

---

# 176.79. Signals

OS signal:

```text
SIGINT
SIGTERM
SEH
Mach exceptions
```

không phải panic.

System layer chuyển chúng thành:

```text
signal handler
fault handler
termination event
```

theo platform.

---

# 176.80. Async signal safety

Signal handler không được tự động gọi arbitrary Axiom code nếu runtime chưa thiết kế safe async-signal semantics.

Một signal-safe API subset nên tồn tại ở system layer.

---

# 176.81. Interrupt execution domain

Embedded/kernel profile có thể có:

```text
Interrupt
```

execution domain.

Compiler kiểm tra:

```text
interrupt-safe function
```

với restrictions riêng.

Không cần đưa interrupt semantics vào desktop Core.

---

# 176.82. GPU scheduler

GPU launch:

```text
launch(kernel)
```

trả:

```text
GpuEvent
```

CPU executor không tự coi GPU execution là OS task.

GPU execution domain riêng.

---

# 176.83. CPU/GPU synchronization

`GpuEvent` có thể trở thành awaitable:

```text
await event
```

nhưng bridge phải tạo synchronization contract:

```text
GPU completion
    ↓
host visibility
```

Không được coi `await` tự động là full memory fence cho mọi memory.

---

# 176.84. Executor API

Conceptual:

```text
trait Executor {
    fn spawn<T: Future + Send>(...)
    fn block_on<T>(...)
}
```

Nhưng trait này là library abstraction.

Core chỉ hiểu:

```text
async fn
Future
await
```

---

# 176.85. Executor replacement

Program có thể chọn:

```text
SingleThreadExecutor
ThreadPoolExecutor
IOExecutor
DeterministicExecutor
EmbeddedExecutor
GPU-aware Executor
```

mà language semantics không thay đổi.

---

# 176.86. No mandatory async runtime

Một chương trình có:

```ax
async fn foo() -> i32 { ... }
```

nhưng không gọi:

```text
executor
```

vẫn compile được nếu API usage phù hợp.

Calling async function chỉ tạo Future.

---

# 176.87. Blocking async boundary

Runtime có thể cung cấp:

```text
block_on(future)
```

để bridge synchronous world.

Không để compiler tự động spawn executor.

---

# 176.88. Blocking detection

Runtime/tooling có thể warn:

```text
blocking syscall inside async task
```

nhưng không nhất thiết là compiler semantic error.

Một profile strict có thể biến nó thành error nếu contract yêu cầu.

---

# 176.89. Async-aware synchronization

Không dùng:

```text
MutexGuard
```

qua:

```text
await
```

theo default.

Thay vào đó:

```text
AsyncMutex
AsyncRwLock
```

có guard semantics tương thích suspension.

---

# 176.90. AsyncMutex implementation

Có thể:

```text
waiter queue
 ↓
task parked
 ↓
unlock
 ↓
wake next task
```

Không park OS thread nếu không cần.

---

# 176.91. Backpressure

Async runtime/library nên hỗ trợ:

```text
bounded channel
semaphore
buffer limit
concurrency limit
```

để tránh:

```text
unbounded task explosion
```

Đây là runtime/application policy.

---

# 176.92. Work stealing và cache locality

Scheduler không nên steal tùy tiện nếu task đang giữ state locality lớn.

Cost model có thể cân nhắc:

```text
task size
CPU affinity
cache locality
NUMA locality
wake source
```

để giảm migration cost.

---

# 176.93. Task migration

Migration có cost:

```text
cache loss
NUMA effects
TLS differences
```

nhưng semantic ownership vẫn hợp lệ nếu task `Send`.

Compiler/runtime có thể tối ưu migration.

---

# 176.94. Task-local storage

Task-local data khác TLS:

```text
OS Thread TLS
    ≠
Task-local
```

Task-local có thể migrate giữa workers.

Do đó task-local state phải đi cùng Future/task state.

---

# 176.95. Task-local API

Library:

```text
TaskLocal<T>
```

không phải Core global.

Nếu task migrate:

```text
TaskLocal<T>
```

migrate cùng task.

---

# 176.96. Context propagation

Logging/tracing/request IDs có thể dùng task-local context.

Nhưng:

```text
task context
```

không nên được triển khai bằng hidden global mutable state.

---

# 176.97. Scheduler observability

Compiler/runtime tooling có thể expose:

```text
task id
worker id
queue latency
wake count
poll count
migration count
```

cho profiler.

Không đưa metadata này vào semantics.

---

# 176.98. Runtime tracing

Có thể:

```text
AXIOM_TRACE_RUNTIME
```

build feature để collect:

```text
spawn
wake
poll
park
unpark
lock
unlock
channel
```

Release build strip hoàn toàn.

---

# 176.99. Performance counters

Runtime có thể đo:

```text
context switch
lock contention
queue contention
task migration
cache miss
```

kết hợp PGO/profiling.

Profile không thay đổi semantics.

---

# 176.100. Compiler/runtime division

Điểm cuối cùng:

```text
Compiler
├── proves Send/Share
├── proves capability safety
├── lowers async
├── lowers atomics
├── verifies await
└── generates ABI

Runtime
├── schedules
├── allocates task storage
├── parks/wakes
├── interfaces OS
├── executes Future
└── provides policy
```

Compiler **không** cần biết scheduler implementation cụ thể.

---

# 176.101. Architecture tổng thể

```text
                         Axiom Program
                              │
                    ┌─────────┴─────────┐
                    ↓                   ↓
                  Thread              Async
                    │                   │
                    ↓                   ↓
                 Send/Share          Future
                    │                   │
                    ↓                   ↓
                OS Thread           Executor
                    │              ┌────┴────┐
                    │              ↓         ↓
                    │           Scheduler    IO
                    │              │         │
                    └──────┬───────┴─────────┘
                           ↓
                     Platform Layer
                           │
            ┌──────────────┼──────────────┐
            ↓              ↓              ↓
          Linux          Windows        macOS
```

---

# 176.102. Các invariant đóng băng

### Runtime

- **ARUNTIME-CONCUR-20** — Không có monolithic concurrency runtime bắt buộc.
- **ARUNTIME-CONCUR-21** — Runtime components được link theo nhu cầu.
- **ARUNTIME-CONCUR-22** — Scheduler không phải semantic authority.
- **ARUNTIME-CONCUR-23** — Runtime implementation không được thay đổi ownership/capability semantics.
- **ARUNTIME-CONCUR-24** — Thread runtime và async executor là các components độc lập.

### Threads

- **ATHREAD-20** — Thread là execution domain.
- **ATHREAD-21** — Cross-thread ownership transfer yêu cầu Send.
- **ATHREAD-22** — Thread != async task.
- **ATHREAD-23** — Detached execution phải explicit.
- **ATHREAD-24** — Thread lifecycle phải được quản lý deterministic.
- **ATHREAD-25** — Thread stack là platform/runtime resource.

### Scheduler

- **ASCHED-20** — Scheduler order không trở thành hidden semantic guarantee.
- **ASCHED-21** — Work stealing không được phá Send/Share semantics.
- **ASCHED-22** — Task migration phải giữ execution/storage contracts.
- **ASCHED-23** — Scheduler có thể tối ưu locality/affinity.
- **ASCHED-24** — Scheduler có thể nondeterministic trong production.
- **ASCHED-25** — Deterministic scheduler phải tồn tại cho conformance/testing.

### Async

- **AASYNC-RUNTIME-20** — Async không tự tạo OS thread.
- **AASYNC-RUNTIME-21** — Future không tự tạo executor.
- **AASYNC-RUNTIME-22** — `spawn` và `spawn_local` có execution guarantees khác nhau.
- **AASYNC-RUNTIME-23** — Waker chỉ notification, không phải execution.
- **AASYNC-RUNTIME-24** — Multiple wakeups có thể được coalesce.
- **AASYNC-RUNTIME-25** — Future polling phải exclusive.
- **AASYNC-RUNTIME-26** — Future state chỉ chứa semantic live-across-await values.
- **AASYNC-RUNTIME-27** — Dropping Future không mặc định cancel external operation.
- **AASYNC-RUNTIME-28** — Cancellation khác panic.
- **AASYNC-RUNTIME-29** — Async runtime không bắt buộc heap allocation cho mọi Future.

### Synchronization

- **ASYNC-LOCK-20** — Sync guards là ownership-bearing capabilities.
- **ASYNC-LOCK-21** — Guards không Copy.
- **ASYNC-LOCK-22** — Guard Drop giải phóng lock/permit theo contract.
- **ASYNC-LOCK-23** — Sync guard không được crossing await mặc định.
- **ASYNC-LOCK-24** — Async-aware synchronization là abstraction riêng.
- **ASYNC-LOCK-25** — Fairness không được giả định nếu primitive không contract.

### Channels

- **ACHAN-20** — Channel là ownership-transfer boundary.
- **ACHAN-21** — Send không implicit clone.
- **ACHAN-22** — Per-sender FIFO nếu primitive contract yêu cầu.
- **ACHAN-23** — Không có global ordering mặc định giữa senders.
- **ACHAN-24** — Bounded channels phải hỗ trợ backpressure.
- **ACHAN-25** — Async channel wake task, không tạo thread cho mỗi message.

### Memory model

- **AMEMCONCUR-20** — Scheduler không thay đổi happens-before semantics.
- **AMEMCONCUR-21** — Notify không tự tạo publication.
- **AMEMCONCUR-22** — Atomic ordering được giữ qua runtime/backend.
- **AMEMCONCUR-23** — Foreign synchronization phải được map hoặc conservative.
- **AMEMCONCUR-24** — Volatile không được optimize như ordinary memory.

---

# BOOTSTRAP-176 hoàn tất

Đến đây Axiom đã tách được ba thứ mà nhiều ngôn ngữ trộn lẫn:

```text
Language semantics
        │
        ↓
Execution abstraction
        │
        ↓
Runtime implementation
```

Ví dụ:

```text
async/await
```

là **language semantic mechanism**.

```text
Future
```

là **execution abstraction**.

```text
Tokio-like executor / IOCP / epoll / io_uring / thread pool
```

là **runtime implementation**.

Điều này cho phép Axiom có thể chạy:

```text
┌─────────────────────────────────────┐
│ tiny freestanding program           │
│ no threads                          │
│ no async                            │
│ no runtime                          │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ high-performance server             │
│ thread pool                         │
│ async IO                            │
│ work stealing                      │
│ channels                            │
└─────────────────────────────────────┘

┌─────────────────────────────────────┐
│ embedded/kernel                     │
│ custom scheduler                    │
│ interrupts                          │
│ no libc                             │
│ no heap                             │
└─────────────────────────────────────┘
```

mà **cùng một language semantics** vẫn được giữ nguyên.

---

# BOOTSTRAP-177 — Memory Allocator, Heap Architecture, Arenas, Pools & Allocation Strategy

Task kế tiếp nên đi sâu vào phần rất quan trọng với mục tiêu ban đầu của bạn: **làm sao Axiom đạt hiệu năng cao mà không bắt programmer phải quản lý `malloc/free`, nhưng cũng không áp đặt GC/RC/heap runtime**.

Sẽ khóa:

```text
Allocator abstraction
        ↓
System allocator
Arena
Pool
Slab
Region
Stack allocation
Inline allocation
Small-object allocation
Thread-local allocator
NUMA allocator
Custom allocator
GPU/device allocator
Allocation elision
Stack promotion
Object lifetime
Fragmentation
Cache locality
Alignment
Allocation failure
```

Đặc biệt cần giải quyết dứt điểm câu hỏi trước đây của bạn:

> **“Mô hình bộ nhớ phẳng có thực sự làm giảm fragmentation và tăng performance, hay Axiom nên dùng một mô hình semantic khác nhưng vẫn cho phép compiler tạo ra layout gần như flat-memory?”**