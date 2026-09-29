# BOOTSTRAP-748 — AXTASK

**Namespace:** `AXTASK`  
**Phase:** Axiom Civilization Runtime / Native Task, Future, Promise & Structured Execution Runtime  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET**  
**Depends on:** `AXPROCESS`, `AXSYNC`, `AXMEMORY`, `AXCOMPUTE`, `AXIPC`, `AXSTORAGE`, `AXNETWORK`, `AXAPPLICATION`, `AXSECURITY`

AXTASK là tầng **logical execution** nằm trên thread/process primitives.

Mục tiêu:

> Cho phép Axiom viết concurrent/async code với abstraction rất nhỏ, nhưng không biến mỗi task thành một OS thread, không yêu cầu GC, không yêu cầu borrow checker, và không tạo runtime nặng.

Mô hình:

```text
Process
   │
   ├── OS Threads
   │       │
   │       └── AXTASK Scheduler
   │                │
   │                ├── Task A
   │                ├── Task B
   │                ├── Task C
   │                └── Task D
   │
   └── IPC / I/O / GPU / Device
```

---

# 748.1 — Strong Boundary

### AXTASK owns

```text
task
task handle
future
promise
continuation
task group
structured concurrency
task cancellation
task deadline
task-local state
task queues
work stealing
task suspension
task completion
task failure propagation
task supervision
task tracing
task replay
task checkpoint metadata
```

### AXPROCESS owns

```text
process
thread
stack
execution context
TLS
process lifecycle
```

### AXSYNC owns

```text
atomic
mutex
semaphore
event
condition
barrier
wait/wake
fence
```

### AXCOMPUTE owns

```text
CPU topology
scheduler resource policy
CPU allocation
worker capacity
compute resources
```

AXTASK requests execution capacity; AXCOMPUTE controls system-wide resource allocation.

---

# 748.2 — Why Task Exists

Không nên viết:

```text
100000 operations
→ 100000 OS threads
```

Thay vào đó:

```text
100000 tasks
→ small number of worker threads
```

Task là logical unit.

Thread là execution resource.

---

# 748.3 — Task vs Thread

```text
Task
 ├── small metadata
 ├── logical state
 ├── continuation
 └── optional suspended frame

Thread
 ├── stack
 ├── registers
 ├── TLS
 └── OS scheduling context
```

Một thread có thể chạy nhiều task theo thời gian.

---

# 748.4 — Task State

```text
CREATED
   ↓
READY
   ↓
RUNNING
   ↓
SUSPENDED
   ↓
READY
   ↓
COMPLETING
   ↓
COMPLETED
```

Exceptional:

```text
CANCEL_REQUESTED
CANCELLED
FAILED
ABANDONED
```

---

# 748.5 — Task Identity

```axiom
task_id
```

phải:

```text
unique
opaque
generation-safe
```

Không sử dụng stack pointer làm task identity.

---

# 748.6 — Task Handle

```axiom
task_handle<T>
```

là typed opaque handle tới task result.

---

# 748.7 — Task Creation

```axiom
task.spawn(fn)
```

trả:

```text
task_handle<Result>
```

Task creation không mặc định tạo thread.

---

# 748.8 — Lightweight Task

Task metadata mục tiêu:

```text
small
cache-friendly
allocation-minimized
```

Không đặt OS-thread-sized state vào mỗi task.

---

# 748.9 — Task Frame

Task bị suspend cần lưu:

```text
instruction continuation
local state
await state
result/error state
cancellation state
```

Compiler tạo frame tối thiểu theo capture thực tế.

---

# 748.10 — Stackless Task

Default async task ưu tiên:

```text
stackless continuation
```

thay vì mỗi task có stack riêng.

---

# 748.11 — Stackful Task

Một số workload có thể yêu cầu:

```axiom
task.spawn_stackful()
```

cho legacy/native blocking code.

Stackful task có chi phí lớn hơn và không phải default.

---

# 748.12 — Compiler Lowering

Ví dụ:

```axiom
async fn fetch() -> Data {
    let x = await read()
    process(x)
}
```

Compiler transform thành state machine:

```text
STATE_0
   ↓
await read
   ↓
STATE_1
   ↓
process
   ↓
RETURN
```

---

# 748.13 — No Heap-Allocated Continuation by Default

Compiler được phép đặt task frame:

```text
stack
inline parent frame
arena
task pool
```

nếu lifetime cho phép.

---

# 748.14 — Escaping Task

Nếu task outlives caller:

```text
caller
  ↓
spawn
  ↓
task escapes
```

frame phải chuyển sang storage có lifetime phù hợp.

---

# 748.15 — Allocation Elision

Compiler có thể loại bỏ task allocation nếu chứng minh task hoàn thành synchronously hoặc không escape.

---

# 748.16 — Task Group

```axiom
task_group
```

gom nhiều tasks:

```text
group
 ├── task A
 ├── task B
 └── task C
```

---

# 748.17 — Structured Concurrency

Canonical:

```axiom
with task_group group {
    group.spawn(A)
    group.spawn(B)
    group.spawn(C)
}
```

Scope không hoàn thành cho đến khi policy của group được thỏa mãn.

---

# 748.18 — Child Lifetime

Child task mặc định không được silently outlive structured parent group.

---

# 748.19 — Detached Task

Có thể:

```axiom
task.detach(handle)
```

nhưng detached task chuyển sang explicit supervisor ownership.

---

# 748.20 — No Orphan Task

Runtime không để task không có owner/supervisor một cách implicit.

---

# 748.21 — Task Supervision

Supervisor có thể quản lý:

```text
restart
cancel
observe
retry
shutdown
```

---

# 748.22 — Task Failure

Task có thể kết thúc:

```text
SUCCESS
FAILURE
CANCELLED
```

---

# 748.23 — Failure Propagation

Trong structured group:

```text
child failure
     ↓
group policy
     ↓
cancel siblings
```

nếu policy là fail-fast.

---

# 748.24 — Group Policies

```text
FAIL_FAST
COLLECT_ALL
IGNORE_FAILURE
FIRST_SUCCESS
QUORUM
```

---

# 748.25 — Failure Policy Is Explicit

Không được mặc định giả định rằng mọi child failure phải crash parent.

---

# 748.26 — Result

```axiom
future<Result>
```

có thể kết thúc bằng:

```text
value
error
cancelled
```

---

# 748.27 — Future

Future đại diện cho:

```text
eventual result
```

Không nhất thiết chứa thread.

---

# 748.28 — Future State

```text
PENDING
RUNNING
READY
FAILED
CANCELLED
```

---

# 748.29 — Promise

Promise là producer side:

```axiom
promise<T>
```

Future là consumer side:

```axiom
future<T>
```

---

# 748.30 — Single Completion

Promise chỉ được complete một lần.

```text
complete(value)
```

hoặc:

```text
fail(error)
cancel()
```

Không được complete lần thứ hai.

---

# 748.31 — Promise/Future Pair

```text
promise<T>
      │
      └── future<T>
```

Promise giữ quyền resolve.

Future chỉ quan sát result.

---

# 748.32 — Future Await

```axiom
let result = await future
```

không block OS thread trong async context.

---

# 748.33 — Blocking Get

Native synchronous code có thể:

```axiom
future.get()
```

nhưng operation này có thể block thread.

API phải phân biệt rõ.

---

# 748.34 — Task Await

```axiom
await task
```

chuyển caller task sang suspended state nếu result chưa sẵn sàng.

---

# 748.35 — Already Ready Fast Path

Nếu future đã completed:

```text
await
 ↓
atomic state check
 ↓
continue immediately
```

Không scheduler round-trip.

---

# 748.36 — Continuation

```axiom
future.then(fn)
```

có thể attach continuation.

Compiler/runtime không bắt buộc heap allocate closure nếu có thể inline.

---

# 748.37 — Continuation Scheduling

Continuation có thể:

```text
RUN_INLINE
RUN_CURRENT_WORKER
RUN_ANY_WORKER
RUN_SPECIFIED_EXECUTOR
```

---

# 748.38 — Inline Continuation

Nếu safe:

```text
future complete
 ↓
execute continuation immediately
```

giảm scheduling overhead.

---

# 748.39 — Continuation Depth

Runtime phải tránh recursive continuation chain tạo stack growth.

---

# 748.40 — Trampoline

Continuation chain dài có thể chuyển sang scheduler queue:

```text
A → B → C → D
```

thay vì recursive calls.

---

# 748.41 — Task Scheduler

AXTASK scheduler quản lý:

```text
ready tasks
suspended tasks
worker queues
task wakeups
continuations
```

---

# 748.42 — Scheduler Boundary

AXTASK không sở hữu:

```text
CPU core allocation
hardware topology
OS thread creation policy
```

những phần đó thuộc AXCOMPUTE/AXPROCESS.

---

# 748.43 — Executor

```axiom
executor
```

là execution context mà task được submit.

---

# 748.44 — Default Executor

Application có:

```axiom
default_executor()
```

được runtime quản lý.

---

# 748.45 — Custom Executor

Có thể tạo:

```axiom
executor.create()
```

với policy:

```text
worker_count
queue_type
affinity_hint
priority
```

---

# 748.46 — Worker Thread

Executor có thể dùng:

```text
N worker threads
```

để chạy nhiều tasks.

---

# 748.47 — Worker Ownership

Worker thread thuộc execution runtime.

Task không sở hữu worker thread.

---

# 748.48 — Work Queue

Mỗi worker có thể có local deque:

```text
worker A
 └── [task][task][task]
```

---

# 748.49 — Work Stealing

Idle worker:

```text
worker B idle
      ↓
steal
      ↓
worker A queue
```

---

# 748.50 — Work-Stealing Direction

Ưu tiên steal task ở đầu phù hợp với deque algorithm để giảm contention.

---

# 748.51 — Local Push/Pop

Owner worker ưu tiên thao tác local queue bằng operations ít synchronization.

---

# 748.52 — Global Injection Queue

External producer có thể submit vào:

```text
global injection queue
```

sau đó worker lấy về local queue.

---

# 748.53 — Queue Sharding

Không sử dụng một global queue cho mọi task nếu contention có thể trở thành bottleneck.

---

# 748.54 — Per-Core Queue

High-throughput profile hỗ trợ:

```text
core
 └── task queue
```

---

# 748.55 — NUMA Queue

NUMA profile có:

```text
NUMA node
 └── worker queues
```

Task ưu tiên chạy gần memory của nó khi có thể.

---

# 748.56 — Task Affinity

Task có thể khai báo:

```axiom
affinity_hint
```

nhưng không ép scheduler vi phạm system resource policy.

---

# 748.57 — Task Priority

```axiom
task.priority
```

có thể là:

```text
BACKGROUND
NORMAL
INTERACTIVE
HIGH
REALTIME
```

`REALTIME` yêu cầu explicit privilege/policy.

---

# 748.58 — Priority Semantics

Priority là scheduling hint/contract.

AXCOMPUTE quyết định CPU scheduling thực tế.

---

# 748.59 — Deadline Task

Task có:

```axiom
deadline
```

để scheduler/runtime biết urgency.

---

# 748.60 — Deadline Propagation

Parent deadline có thể propagate:

```text
parent deadline
       ↓
child task
       ↓
IPC request
       ↓
I/O
```

nhưng child không được tự ý extend parent deadline.

---

# 748.61 — Timeout

Timeout là convenience:

```text
deadline = now + duration
```

Internal canonical representation là deadline.

---

# 748.62 — Task Cancellation

```axiom
task.cancel()
```

gửi cancellation request.

---

# 748.63 — Cooperative Cancellation

Default:

```text
request cancel
     ↓
task reaches safe point
     ↓
cleanup
     ↓
CANCELLED
```

---

# 748.64 — Cancellation Token

```axiom
cancel_token
```

có thể được truyền tới child operations.

---

# 748.65 — Cancellation Source

```axiom
cancel_source
```

có quyền trigger cancellation.

---

# 748.66 — Token Hierarchy

```text
parent token
      ↓
child token
      ↓
grandchild token
```

Child cancellation không tự động cancel parent.

---

# 748.67 — Cancellation Scope

```axiom
with cancellation_scope(token) {
    ...
}
```

mọi child task trong scope có thể nhận cancellation.

---

# 748.68 — Cancellation Cleanup

Task cancellation phải chạy cleanup handlers theo deterministic lifetime rules.

---

# 748.69 — No Arbitrary Forced Kill

AXTASK không mặc định kill worker thread để cancel task.

---

# 748.70 — Non-Cancellable Region

Một task có thể tạm thời:

```axiom
cancellation.disable()
```

trong critical cleanup.

Scope phải ngắn và explicit.

---

# 748.71 — Cancellation Race

Nếu task complete trước cancellation:

```text
COMPLETED
```

được giữ nguyên.

---

# 748.72 — Cancellation and Future

Future có thể:

```text
cancel producer
```

chỉ nếu future contract cấp quyền đó.

---

# 748.73 — Shared Future

Nhiều consumers cùng await future.

Cancellation của một consumer không mặc định cancel producer.

---

# 748.74 — Reference-Free Future

Future không yêu cầu GC.

Lifetime được quản lý bằng:

```text
task ownership
explicit handles
scope
reference counting where selected
```

---

# 748.75 — Future Memory

Future state nên nhỏ:

```text
state
result pointer/value
waiter list
continuation
```

---

# 748.76 — Result Storage

Small result có thể inline.

Large result sử dụng AXMEMORY-managed storage.

---

# 748.77 — Future Waiters

Waiters có thể được lưu:

```text
intrusive list
```

để tránh allocation.

---

# 748.78 — Completion Fast Path

Nếu không có waiter:

```text
complete
 ↓
store result
 ↓
atomic state
```

không cần scheduler work.

---

# 748.79 — Completion With Waiters

```text
complete
 ↓
publish result
 ↓
wake waiters
 ↓
schedule continuations
```

---

# 748.80 — Future Memory Ordering

Promise completion dùng release.

Future observation dùng acquire.

---

# 748.81 — Future Result Visibility

Nếu consumer observes completed state bằng acquire, result writes trước completion được visible.

---

# 748.82 — Future Double Completion

Runtime debug phải phát hiện:

```text
complete()
complete()
```

---

# 748.83 — Promise Ownership

Promise chỉ nên có một logical completion authority.

Nếu cần multiple producers, dùng explicit arbitration primitive.

---

# 748.84 — Task Group Join

```axiom
group.join()
```

đợi children theo group semantics.

---

# 748.85 — Join Result

Group join có thể trả:

```text
all success
failure collection
cancelled
```

tùy policy.

---

# 748.86 — Fail-Fast Group

```text
child failure
 ↓
cancel siblings
 ↓
wait cleanup
 ↓
return failure
```

---

# 748.87 — Collect-All Group

```text
child A success
child B failure
child C success
      ↓
collect results
```

---

# 748.88 — First-Success Group

Useful cho redundant operations:

```text
A ──┐
B ──┼──→ first success
C ──┘
```

Các task còn lại được cancellation request.

---

# 748.89 — Quorum Group

Group có thể hoàn tất khi đạt:

```text
K successful children
```

---

# 748.90 — Nursery Model

Axiom có thể cung cấp:

```axiom
nursery
```

như structured task group abstraction.

---

# 748.91 — Task Local Storage

Task có:

```axiom
task_local<T>
```

khác TLS của OS thread.

---

# 748.92 — Task Local vs Thread Local

```text
TLS
→ follows thread

Task-local
→ follows logical task
```

Task migration giữa workers không làm mất task-local state.

---

# 748.93 — Task Local Implementation

Task-local state có thể nằm trong task frame nếu compiler biết layout.

---

# 748.94 — Task Context

```axiom
task_context {
    task_id
    parent_id
    cancellation
    deadline
    priority
    executor
}
```

---

# 748.95 — Context Propagation

Task context có thể propagate:

```text
task
 ↓
child task
 ↓
IPC request
 ↓
remote service
```

những field phù hợp.

---

# 748.96 — Security Context

Security authority không được tự động nâng theo child task.

Task context chỉ carry security identity/capability theo AXSECURITY rules.

---

# 748.97 — IPC Integration

```text
await ipc.receive()
```

phải suspend task thay vì block worker thread.

---

# 748.98 — I/O Integration

Async I/O:

```text
submit
 ↓
suspend task
 ↓
OS completion
 ↓
wake task
```

---

# 748.99 — Network Integration

AXNETWORK có thể cung cấp:

```text
future<read_result>
future<write_result>
```

cho AXTASK.

---

# 748.100 — Storage Integration

AXSTORAGE có thể expose asynchronous:

```text
read
write
flush
```

trả task/future.

---

# 748.101 — GPU Integration

GPU submission có thể:

```text
submit
 ↓
GPU fence
 ↓
await fence
 ↓
resume task
```

---

# 748.102 — Media Integration

Media pipeline có thể sử dụng tasks cho:

```text
decode
transform
encode
```

với bounded worker pools.

---

# 748.103 — Audio Integration

Audio realtime tasks phải:

```text
avoid allocation
avoid unbounded blocking
avoid unpredictable locks
```

AXAUDIO có realtime constraints riêng.

---

# 748.104 — Compute Integration

AI/GPU compute task:

```text
task
 ↓
compute submission
 ↓
device event/fence
 ↓
task resume
```

---

# 748.105 — Blocking API Bridge

Legacy blocking operation có thể chạy trên:

```text
blocking_executor
```

để không block async worker pool.

---

# 748.106 — Blocking Pool

Blocking executor có worker policy riêng:

```text
small fixed pool
adaptive pool
bounded pool
```

---

# 748.107 — Blocking Detection

Debug runtime có thể detect task worker gọi blocking API không phù hợp.

---

# 748.108 — Cooperative Yield

```axiom
task.yield()
```

đưa task trở lại scheduler.

---

# 748.109 — Yield Semantics

Yield không đảm bảo task chuyển sang worker khác.

Chỉ cho scheduler opportunity.

---

# 748.110 — Preemption

Task scheduler có thể bị preempt ở thread level.

Stackless task không cần runtime-level preemption để correctness.

---

# 748.111 — Cooperative Suspension

Default async model:

```text
await
yield
blocking operation integration
```

để task suspend explicit.

---

# 748.112 — Task Budget

Task có thể khai báo:

```axiom
cpu_budget
```

cho scheduling/diagnostic purposes.

---

# 748.113 — Fairness

Scheduler phải tránh task producer có thể monopolize executor indefinitely.

---

# 748.114 — Quantum Hint

Task có optional:

```text
quantum_hint
```

nhưng actual thread quantum thuộc AXCOMPUTE/OS.

---

# 748.115 — Work Stealing Policy

Workers ưu tiên:

```text
local work
 ↓
global injection
 ↓
steal
 ↓
park
```

---

# 748.116 — Worker Parking

Khi không có task:

```text
worker
 ↓
spin briefly
 ↓
park
```

---

# 748.117 — Worker Wake

New task:

```text
enqueue
 ↓
wake one suitable worker
```

tránh thundering herd.

---

# 748.118 — Executor Shutdown

```text
RUNNING
 ↓
STOP_ACCEPTING
 ↓
DRAIN
 ↓
CANCEL/FINISH
 ↓
STOP_WORKERS
 ↓
CLOSED
```

---

# 748.119 — Graceful Executor Shutdown

New tasks bị reject.

Existing tasks hoàn thành theo policy.

---

# 748.120 — Immediate Shutdown

```text
STOP_ACCEPTING
 ↓
REQUEST_CANCEL
 ↓
cleanup
 ↓
shutdown
```

Không force-kill arbitrary task frames.

---

# 748.121 — Task Crash

Nếu task phát sinh uncaught failure:

```text
task
 ↓
FAILED
 ↓
supervisor/group
```

Worker thread không nhất thiết crash theo task.

---

# 748.122 — Worker Isolation

Task failure phải không làm hỏng scheduler metadata.

---

# 748.123 — Panic Boundary

Nếu Axiom có panic/exception mechanism, executor phải có task boundary để isolate failure.

---

# 748.124 — Task Exception

Exception không được tự động xuyên qua task boundary như stack-local exception.

Task result phải carry failure state.

---

# 748.125 — Future Error

```axiom
future<T>
```

phải cho phép:

```text
value
error
```

theo language error model.

---

# 748.126 — Task Retry

Retry phải là explicit policy:

```axiom
retry(task, policy)
```

Không tự retry side-effecting operation.

---

# 748.127 — Retry Policy

```text
MAX_ATTEMPTS
BACKOFF
DEADLINE
ERROR_FILTER
JITTER
```

---

# 748.128 — Backoff

```text
immediate
fixed
exponential
deadline-aware
```

---

# 748.129 — Task Dependencies

Task có thể phụ thuộc:

```text
A → B
A → C
B,C → D
```

scheduler có thể represent dependency graph.

---

# 748.130 — Dependency Completion

Task D chỉ ready khi dependencies đạt completion condition.

---

# 748.131 — DAG Execution

Compute pipelines có thể sử dụng:

```text
task graph
```

để giảm synchronization overhead.

---

# 748.132 — Task Graph

```text
       A
      / \
     B   C
      \ /
       D
```

---

# 748.133 — Graph Scheduling

AXTASK có thể schedule graph nodes trực tiếp thay vì tạo nhiều futures wrapper.

---

# 748.134 — Structured Graph Lifetime

Graph owns task nodes.

Khi graph kết thúc, nodes không được leak.

---

# 748.135 — Continuation Graph

Future chain:

```text
A → B → C
```

có thể compiler-optimize thành một state machine.

---

# 748.136 — Async State Machine Fusion

Nếu compiler có đủ visibility:

```text
await A
await B
await C
```

có thể fuse state machines để giảm allocations.

---

# 748.137 — Allocation-Free Async

Mục tiêu:

```text
small async function
→ zero heap allocation
```

nếu lifetime/control-flow cho phép.

---

# 748.138 — Task Frame Size

Compiler phải expose diagnostic:

```text
task frame size
captured locals
spill state
```

để programmer tối ưu.

---

# 748.139 — Large Frame Warning

Task frame quá lớn có thể được cảnh báo vì gây:

```text
cache pressure
memory overhead
```

---

# 748.140 — Frame Placement

Runtime có thể chọn:

```text
stack
inline
pool
arena
heap
```

theo lifetime.

---

# 748.141 — Task Pool

High-throughput executor có thể preallocate task frames.

---

# 748.142 — Slab Allocation

Task metadata có thể sử dụng AXMEMORY slab allocator.

---

# 748.143 — Task Recycling

Completed frame có thể recycle nếu ABI/lifetime an toàn.

---

# 748.144 — ABA Protection

Task IDs/queue nodes phải dùng generation/sequence khi recycled.

---

# 748.145 — Handle Safety

Stale task handle không được truy cập task mới chỉ vì object address được reuse.

---

# 748.146 — Task Completion Storage

Result phải tồn tại đủ lâu cho valid future consumers.

---

# 748.147 — Future Ownership

Future handle có explicit ownership semantics:

```text
move
share
borrow
```

theo Axiom type/lifetime model.

---

# 748.148 — Shared Future

Nếu nhiều consumers:

```axiom
shared_future<T>
```

result storage được giữ cho đến khi cuối consumer release.

---

# 748.149 — No Mandatory Reference Counting

Shared future không bắt buộc dùng atomic refcount nếu compiler/runtime có structured ownership alternative.

---

# 748.150 — Intrusive Lifetime

Internal task runtime có thể dùng intrusive counters để giảm allocation.

---

# 748.151 — Cancellation Tree

```text
Root
 ├── A
 │   ├── A1
 │   └── A2
 └── B
```

Cancel Root có thể propagate toàn subtree.

---

# 748.152 — Cancellation Complexity

Propagation phải tránh:

```text
O(N²)
```

trên task tree lớn.

---

# 748.153 — Bulk Cancellation

Cancellation tree nên hỗ trợ:

```text
mark subtree cancelled
```

sau đó tasks observe lazily.

---

# 748.154 — Deadline Tree

Deadline propagation cũng nên sử dụng compact parent-derived metadata.

---

# 748.155 — Task Local Cancellation Check

Hot loop có thể dùng:

```axiom
if token.is_cancelled() {
    return cancelled
}
```

Atomic read phải cheap.

---

# 748.156 — Cancellation Callback

Optional callback:

```axiom
token.on_cancel(fn)
```

nhưng callback storage không được bắt buộc cho basic token.

---

# 748.157 — Callback Allocation

Small callback có thể inline nếu compiler biết size.

Large callback sử dụng AXMEMORY-managed storage.

---

# 748.158 — Task Synchronization

AXTASK sử dụng AXSYNC:

```text
atomic
event
futex-like wait
mutex
```

không tự implement competing synchronization primitives.

---

# 748.159 — Future Waiter Synchronization

Future completion:

```text
release result
 ↓
atomic state
 ↓
wake waiters
```

---

# 748.160 — Scheduler Queue Synchronization

Worker deque có thể dùng:

```text
lock-free
or
minimal lock
```

theo executor profile.

---

# 748.161 — MPSC Injection

External submitters có thể push tasks vào MPSC injection queue.

---

# 748.162 — Worker Deque

Owner operations optimized.

Stealers synchronize only when necessary.

---

# 748.163 — Work-Stealing Fairness

Stealing phải có randomized/rotating victim selection hoặc equivalent policy để tránh hot-spot.

---

# 748.164 — Deterministic Scheduler

Production scheduler có thể non-deterministic.

Test scheduler có:

```text
fixed worker count
fixed scheduling seed
recorded choices
```

---

# 748.165 — Deterministic Replay

Record:

```text
task creation
task ready
worker assignment
await
wake
completion
cancellation
```

---

# 748.166 — Replay Scope

Replay guarantees logical scheduler behavior within declared simulation model.

Không đảm bảo exact hardware timing.

---

# 748.167 — Task Tracing

```axiom
task_trace_event {
    timestamp
    task_id
    parent_id
    worker_id
    state
    operation
}
```

---

# 748.168 — Task Metrics

Theo dõi:

```text
created
completed
failed
cancelled
queue_wait
run_time
suspend_time
steal_count
migration_count
```

---

# 748.169 — Task Migration

Task có thể migrate giữa worker threads.

Task-local state phải giữ nguyên.

---

# 748.170 — Thread Affinity Interaction

Nếu task có hard affinity, scheduler phải respect.

Nếu chỉ hint, scheduler có thể migrate.

---

# 748.171 — NUMA Migration

Task carrying large memory footprint nên ưu tiên local NUMA node.

---

# 748.172 — NUMA Memory Hint

Task metadata có thể chứa:

```text
preferred_node
memory_region
```

AXMEMORY thực hiện placement.

---

# 748.173 — Task Priority Inversion

Task waiting on resource owned by lower-priority task phải expose dependency cho scheduling policy khi platform hỗ trợ.

---

# 748.174 — Async Mutex

Higher-level async runtime có thể implement:

```axiom
async_mutex
```

bằng AXSYNC wait primitives.

---

# 748.175 — Async Semaphore

```axiom
async_semaphore
```

không block worker thread khi permits unavailable.

---

# 748.176 — Async Event

```axiom
async_event
```

resume task thay vì wake blocked OS thread.

---

# 748.177 — Async Condition

Condition wait có thể:

```text
release async mutex
 ↓
suspend task
 ↓
resume
 ↓
reacquire
```

---

# 748.178 — Async Lock Ownership

Async mutex ownership thuộc task, không phải worker thread.

---

# 748.179 — Thread/Task Lock Distinction

```text
thread_mutex
→ owner = thread

async_mutex
→ owner = task
```

Không được thay thế lẫn nhau.

---

# 748.180 — Blocking Detection

Nếu async task giữ thread mutex rồi `await`, debug runtime có thể cảnh báo vì worker migration có thể làm ownership semantics sai.

---

# 748.181 — Async Critical Section

Không được giữ async mutex qua arbitrary await nếu protocol không cho phép.

Tooling có thể cảnh báo:

```text
lock
 ↓
await
 ↓
unlock
```

---

# 748.182 — Task Safety Annotation

```axiom
@must_not_await
critical_section()
```

Compiler/tooling dùng để kiểm tra.

---

# 748.183 — Sendability

Task arguments có thể yêu cầu:

```text
Sendable
```

nếu task có thể migrate sang worker khác.

---

# 748.184 — Shared Data

Shared mutable data phải có explicit synchronization contract.

---

# 748.185 — Immutable Data

Immutable data có thể truyền giữa tasks mà không cần lock.

---

# 748.186 — Ownership Transfer

Task spawn có thể move ownership:

```axiom
spawn(move buffer)
```

sau đó caller không còn quyền mutable access.

Đây là ownership convention, không yêu cầu borrow checker toàn ngôn ngữ.

---

# 748.187 — Task Message Passing

Task communication ưu tiên:

```text
future
channel
message
```

thay vì shared mutable state.

AXIPC sở hữu process-crossing channels; task-local channels có thể là lighter AXTASK abstraction.

---

# 748.188 — Local Task Channel

```axiom
task_channel<T>
```

có thể lower thành:

```text
in-process queue
```

không cần process-level IPC.

---

# 748.189 — Task Channel Optimization

Nếu producer/consumer topology được compiler biết:

```text
SPSC
```

có thể được chọn thay vì MPMC.

---

# 748.190 — Async Channel

Channel có:

```text
send_async()
receive_async()
```

và backpressure.

---

# 748.191 — Channel Backpressure

Policy:

```text
WAIT
DROP
REJECT
COALESCE
```

tương tự AXIPC nhưng lightweight.

---

# 748.192 — Task Supervision Tree

```text
Application
    │
    └── Supervisor
          ├── Service A
          │     ├── Task 1
          │     └── Task 2
          └── Service B
```

---

# 748.193 — Supervisor Strategy

```text
ONE_FOR_ONE
ONE_FOR_ALL
REST_FOR_ONE
STOP
```

---

# 748.194 — Restart Limit

Supervisor phải có:

```text
max_restarts
restart_window
backoff
```

để tránh crash loop.

---

# 748.195 — Task Checkpoint

Checkpoint metadata có thể lưu:

```text
task identity
logical state
await point
deadline
supervisor relation
```

---

# 748.196 — Arbitrary Task Memory Snapshot

Không mặc định checkpoint arbitrary suspended machine state.

Chỉ hỗ trợ nếu compiler/runtime/platform backend có explicit resumable-state contract.

---

# 748.197 — Serializable Task

Task có thể khai báo:

```axiom
@checkpointable
```

Compiler yêu cầu state frame serializable.

---

# 748.198 — Resume

Checkpointable task:

```text
checkpoint
 ↓
process restart
 ↓
restore task state
 ↓
resume
```

Chỉ replay external side effects khi protocol hỗ trợ idempotency/recovery.

---

# 748.199 — AI Boundary

AI được phép:

```text
analyze task traces
suggest worker count
detect scheduler contention
identify oversized task frames
suggest task partitioning
analyze cancellation trees
suggest NUMA placement
identify blocking-in-async errors
```

AI không được:

```text
bypass cancellation authority
execute protected tasks
grant capabilities
disable sandbox
force-kill protected workers
alter security context
```

---

# 748.200 — Formal Invariants

```text
TASK-INV-01   Every task has a unique logical identity.
TASK-INV-02   Task identity is distinct from worker-thread identity.
TASK-INV-03   Creating a task does not implicitly require creating an OS thread.
TASK-INV-04   A task has exactly one terminal completion state.
TASK-INV-05   A promise cannot complete more than once.
TASK-INV-06   Future observation synchronizes with published task result.
TASK-INV-07   Ready tasks cannot be silently lost from scheduler queues.
TASK-INV-08   Suspended tasks retain all state required for valid continuation.
TASK-INV-09   Task migration does not invalidate task-local state.
TASK-INV-10   Task handles cannot resolve to a recycled task without generation validation.

TASK-INV-11   Structured child tasks remain associated with their owning task group.
TASK-INV-12   A structured task group cannot complete before its required children reach terminal/group-defined states.
TASK-INV-13   Detached tasks require explicit detached ownership/supervision.
TASK-INV-14   Child failure propagation follows the declared group policy.
TASK-INV-15   Cancellation is a request unless an explicit stronger contract exists.
TASK-INV-16   Cancellation cannot retroactively change a completed task into CANCELLED.
TASK-INV-17   Child cancellation cannot implicitly cancel its parent.
TASK-INV-18   Parent cancellation may propagate to descendants according to scope policy.
TASK-INV-19   A deadline cannot be silently extended by a child task.
TASK-INV-20   Retry requires an explicit retry/idempotency policy.

TASK-INV-21   Awaiting a task in async context does not block the worker thread.
TASK-INV-22   Blocking operations execute on an appropriate blocking executor when required.
TASK-INV-23   Task synchronization uses AXSYNC primitives rather than hidden global locks.
TASK-INV-24   Async synchronization ownership is distinct from OS-thread synchronization ownership.
TASK-INV-25   Task frame lifetime remains valid while an escaping continuation can execute.
TASK-INV-26   Task frame reclamation cannot occur while a valid handle or continuation still references it.
TASK-INV-27   Work stealing cannot execute a task concurrently on two workers unless explicitly designed for concurrent execution.
TASK-INV-28   Scheduler queue operations preserve task ownership/lifetime.
TASK-INV-29   Scheduler migration preserves task semantics.
TASK-INV-30   Worker shutdown does not silently discard owned tasks.

TASK-INV-31   Task priority cannot bypass AXSECURITY authority.
TASK-INV-32   Realtime task priority cannot be granted without required system policy.
TASK-INV-33   Task context propagation cannot increase security authority.
TASK-INV-34   Task checkpoints cannot restore unauthorized capabilities.
TASK-INV-35   Replay does not imply exact hardware timing determinism.
TASK-INV-36   Diagnostic instrumentation cannot alter correctness semantics.
TASK-INV-37   Task tracing cannot automatically expose protected payload data.
TASK-INV-38   AI task analysis cannot bypass runtime security boundaries.
TASK-INV-39   Scheduler optimization cannot violate task deadlines/affinity contracts that are declared hard constraints.
TASK-INV-40   Uncontended task/future operations must avoid unnecessary heap allocation, kernel transitions, and global synchronization.
```

---

# 748.201 — Native API

```axiom
spawn()
spawn_with_options()

create_task_group()
group_spawn()
group_join()
group_cancel()

detach()

create_future()
create_promise()

future_get()
future_try_get()
future_await()

promise_complete()
promise_fail()
promise_cancel()

future_then()
future_map()
future_flat_map()
future_timeout()

create_cancel_source()
cancel()
cancel_token()
is_cancelled()

create_executor()
executor_submit()
executor_shutdown()
executor_join()

task_yield()
task_current()
task_id()

task_set_priority()
task_set_deadline()
task_set_affinity()

create_task_channel()
channel_send()
channel_try_send()
channel_receive()
channel_try_receive()

async_mutex()
async_semaphore()
async_event()

create_supervisor()
supervisor_start()
supervisor_stop()
supervisor_restart()

start_task_trace()
stop_task_trace()

capture_task_snapshot()
restore_task_checkpoint()

create_task_simulator()
inject_task_fault()
replay_task_trace()

query_task_stats()
query_executor_stats()
query_worker_stats()
```

---

# 748.202 — Spawn Options

```axiom
task_options {
    priority
    deadline
    affinity
    executor
    cancellation_token
    parent_group
    stack_mode
    checkpointable
}
```

Mọi field đều optional.

---

# 748.203 — Default Spawn

```axiom
let task = spawn(work)
```

Compiler/runtime chọn:

```text
default executor
normal priority
parent cancellation scope
no dedicated stack
```

---

# 748.204 — Explicit Spawn

```axiom
let task = spawn_with_options(
    work,
    {
        executor: io_executor,
        priority: NORMAL,
        deadline: deadline
    }
)
```

---

# 748.205 — Canonical Flow: Basic Async

```text
id="n0y9r4"
spawn
  ↓
READY
  ↓
worker executes
  ↓
await I/O
  ↓
SUSPENDED
  ↓
I/O completion
  ↓
READY
  ↓
worker executes continuation
  ↓
COMPLETED
```

---

# 748.206 — Canonical Flow: Future

```text
Producer
   │
   ▼
Promise<T>
   │
   └──────────────┐
                  ▼
               Future<T>
                  │
                  ▼
                await
                  │
             ┌────┴────┐
             ▼         ▼
          PENDING     READY
             │          │
             └──wake────┘
```

---

# 748.207 — Canonical Flow: Structured Concurrency

```text
group
 │
 ├── spawn A
 ├── spawn B
 └── spawn C
       │
       ▼
   group.join
       │
       ├── all success
       ├── fail-fast
       └── collect-all
```

---

# 748.208 — Canonical Flow: Fail-Fast

```text
A ─────────────── SUCCESS
B ─── FAILURE
C ─────────────── RUNNING
        │
        ▼
cancel C
        │
        ▼
wait cleanup
        │
        ▼
group FAILURE
```

---

# 748.209 — Canonical Flow: Work Stealing

```text
Worker A
 ┌──────────────┐
 │ A B C D E    │
 └──────────────┘
       │
       │ A executes
       ▼

Worker B
       │
       │ idle
       ▼
    steal E
       │
       ▼
Worker B executes E
```

---

# 748.210 — Canonical Flow: Async I/O

```text
Task
 │
 ▼
submit I/O
 │
 ▼
suspend
 │
 ├────────────── OS/device
 │
 ▼
completion event
 │
 ▼
wake task
 │
 ▼
resume continuation
```

---

# 748.211 — Canonical Flow: Cancellation

```text
Parent
  │
  ▼
cancel_source.cancel()
  │
  ▼
token
  │
  ├──── Task A
  ├──── Task B
  └──── Task C
          │
          ▼
       safe point
          │
          ▼
       cleanup
          │
          ▼
      CANCELLED
```

---

# 748.212 — Canonical Flow: Deadline

```text
parent deadline
       │
       ▼
child task
       │
       ▼
IPC request
       │
       ▼
I/O
       │
       ▼
same monotonic deadline domain
```

---

# 748.213 — Canonical Flow: Blocking Operation

```text
Async Task
    │
    ▼
blocking operation detected/declared
    │
    ▼
blocking executor
    │
    ▼
worker thread
    │
    ▼
operation
    │
    ▼
future completion
    │
    ▼
async task resumes
```

---

# 748.214 — Canonical Flow: Task Checkpoint

```text
@checkpointable task
       │
       ▼
compiler-generated state frame
       │
       ▼
checkpoint
       │
       ▼
persist logical state
       │
       ▼
process restart
       │
       ▼
restore
       │
       ▼
resume
```

---

# 748.215 — Canonical Flow: GPU Task

```text
Task
 │
 ▼
submit compute
 │
 ▼
GPU queue
 │
 ▼
GPU fence
 │
 ▼
await fence
 │
 ▼
task suspended
 │
 ▼
fence signaled
 │
 ▼
task resumes
```

---

# 748.216 — Compiler Contract

Compiler phải hiểu:

```text
async
await
spawn
task frame
future
promise
cancellation point
task-local
scoped task group
```

và lower chúng thành runtime intrinsics.

---

# 748.217 — Async Lowering

Compiler transformation:

```text
async fn
   ↓
control-flow analysis
   ↓
suspension points
   ↓
state frame
   ↓
continuation states
   ↓
AXTASK ABI
```

---

# 748.218 — Suspension Point

Mỗi `await` có thể tạo state transition:

```text
STATE_N
   ↓
register continuation
   ↓
SUSPEND
```

---

# 748.219 — Spill Analysis

Compiler chỉ spill locals sống qua await.

Ví dụ:

```axiom
let a = calculate()
let b = await io()
use(a, b)
```

`a` phải survive await.

Các locals chết trước await không cần spill.

---

# 748.220 — Frame Layout

Compiler sinh:

```text
task_frame {
    state
    result
    cancellation
    locals_live_across_await
}
```

---

# 748.221 — Frame ABI

Frame ABI phải stable trong cùng compiler/runtime generation.

---

# 748.222 — ABI Version

```text
AXTASK_FRAME_ABI_1
```

version được embed vào compiled artifact metadata.

---

# 748.223 — Binary Compatibility

Dynamic library async functions phải preserve compatible future/task ABI.

---

# 748.224 — Generic Futures

Generic:

```axiom
future<T>
```

được monomorphize hoặc dùng compact ABI representation tùy compiler optimization.

---

# 748.225 — Boxing Avoidance

Small future result không được bắt buộc boxing.

---

# 748.226 — Result ABI

Compiler biết:

```text
T size
T alignment
move semantics
drop/cleanup semantics
```

để store result trực tiếp.

---

# 748.227 — Zero-Copy Result

Large result có thể được returned bằng:

```text
move
buffer ownership transfer
```

thay vì copy.

---

# 748.228 — Future Combinators

Compiler/runtime hỗ trợ:

```text
map
flat_map
join
select
race
timeout
retry
```

---

# 748.229 — Select

```axiom
select {
    case await A:
    case await B:
    case await C:
}
```

resume khi một future ready.

---

# 748.230 — Select Cancellation

Loser futures không tự động cancel producer trừ khi select policy yêu cầu.

---

# 748.231 — Race

```text
A ──┐
B ──┼──→ first completion
C ──┘
```

---

# 748.232 — Join Futures

```axiom
join(A, B, C)
```

có thể compiler-specialize thành compact task graph.

---

# 748.233 — All/Any

```text
all
any
first_success
quorum
```

là combinator primitives.

---

# 748.234 — Timeout

```axiom
await future.with_deadline(deadline)
```

timeout không mặc định kill underlying operation.

---

# 748.235 — Timeout vs Cancellation

```text
timeout
→ caller stops waiting

cancel
→ request producer to stop
```

Hai semantics phải tách biệt.

---

# 748.236 — Task Detach Semantics

Detached task phải có:

```text
owner/supervisor
result disposal policy
failure reporting policy
shutdown policy
```

---

# 748.237 — Unobserved Failure

Detached task failure phải được:

```text
reported
logged
supervised
```

theo application policy.

Không silently disappear.

---

# 748.238 — Executor Isolation

Application có thể tạo executor riêng để isolate:

```text
CPU-heavy
I/O-heavy
realtime
background
```

---

# 748.239 — Executor Quotas

Executor có:

```text
max_workers
max_tasks
queue_capacity
CPU_budget
```

---

# 748.240 — Definition of Done

```text
BOOTSTRAP-748
STATUS: COMPLETE / FROZEN

AXTASK
 ├── Task Identity
 ├── Task Lifecycle
 ├── Lightweight Task
 ├── Stackless Task
 ├── Stackful Task
 ├── Compiler State Machine
 ├── Task Frame
 ├── Future
 ├── Promise
 ├── Continuation
 ├── Structured Concurrency
 ├── Task Group
 ├── Nursery
 ├── Detached Task
 ├── Task Supervision
 ├── Cancellation
 ├── Cancellation Token
 ├── Cancellation Tree
 ├── Deadline
 ├── Timeout
 ├── Task Local
 ├── Executor
 ├── Worker Pool
 ├── Work Stealing
 ├── Injection Queue
 ├── Per-Core Queue
 ├── NUMA Scheduling
 ├── Task Priority
 ├── Task Affinity
 ├── Async I/O
 ├── IPC Integration
 ├── Network Integration
 ├── Storage Integration
 ├── GPU Integration
 ├── Media Integration
 ├── Audio Integration
 ├── Async Synchronization
 ├── Task Channels
 ├── Failure Propagation
 ├── Retry
 ├── Task DAG
 ├── Future Combinators
 ├── Checkpoint
 ├── Deterministic Replay
 ├── Tracing
 ├── Contention Diagnostics
 ├── Compiler Integration
 ├── ABI
 ├── FFI
 ├── PE64
 ├── ELF
 ├── Mach-O
 ├── Android/iOS
 ├── WASM
 ├── Embedded
 ├── AI Boundary
 ├── 40 Formal Invariants
 └── Task Runtime 5.0
```

**BOOTSTRAP-748 / AXTASK — ARCHITECTURAL BASELINE FROZEN.**

---

# BOOTSTRAP-749 — AXASYNC

**Native Async I/O & Completion Runtime — OS completion ports, I/O submission/completion, asynchronous file and network operations, device I/O, timers, event sources, completion queues, polling, readiness/completion distinction, zero-copy buffers, cancellation, deadlines, vectored I/O, scatter/gather, batching, registered buffers, IO rings, completion tokens, AXTASK integration, AXIPC integration, AXNETWORK integration, AXSTORAGE integration, AXMEMORY integration, realtime I/O, deterministic I/O simulation, I/O tracing, fault injection và Async I/O Runtime 5.0.**