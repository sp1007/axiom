# BOOTSTRAP-744 — AXTHREAD

**Namespace:** `AXTHREAD`  
**Phase:** Axiom Civilization Runtime / Native Threading & Structured Concurrency Infrastructure  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET**  
**Depends on:** `AXPROCESS`, `AXCOMPUTE`, `AXSECURITY`, `AXSTORAGE`, `AXNETWORK`, `AXAPPLICATION`

AXTHREAD nằm **trên AXPROCESS** và cung cấp execution model cấp lập trình viên: task, thread pool, fiber, structured concurrency, future/promise, channel và async execution.

Nguyên tắc quan trọng:

> **AXPROCESS quản lý execution primitives của OS/process. AXTHREAD quản lý cách chương trình tổ chức và phối hợp công việc trên các execution primitives đó. AXCOMPUTE quản lý tài nguyên và scheduling vật lý.**

```text
                    AXAPPLICATION
                         │
                         ▼
                      AXPROCESS
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
         OS Threads             Address Space
             │
             ▼
         AXTHREAD
             │
    ┌────────┼─────────┐
    ▼        ▼         ▼
  Tasks    Fibers   Thread Pools
    │        │         │
    ├────────┴─────────┤
    ▼                  ▼
Structured          Futures/
Concurrency         Channels
    │                  │
    └──────────┬───────┘
               ▼
            AXCOMPUTE
```

---

# 744.1 — Mục tiêu

AXTHREAD phải giải quyết được đồng thời hai nhu cầu:

### Low-level

```text
native thread
thread-local execution
affinity
priority
synchronization
```

### High-level

```text
task
async task
fiber
future
promise
channel
task scope
structured concurrency
parallel loop
work stealing
thread pool
pipeline
cancellation
deadline
backpressure
```

Không bắt buộc programmer phải hiểu:

```text
OS scheduler
kernel thread
context switch
TLS ABI
```

để sử dụng concurrency cơ bản.

---

# 744.2 — Không biến AXTHREAD thành AXPROCESS

AXTHREAD **không sở hữu**:

```text
process creation
process address space
process isolation
physical CPU inventory
global system scheduler
kernel scheduling policy
```

AXTHREAD chỉ tạo execution abstraction bên trên chúng.

---

# 744.3 — Ba tầng Execution

Axiom chuẩn hóa ba loại execution:

```text
OS Thread
   ↓
Fiber
   ↓
Task
```

### OS Thread

Execution context có thể được scheduler của OS/AXCOMPUTE trực tiếp schedule.

### Fiber

Execution context nhẹ hơn thread, cooperative switching.

### Task

Đơn vị công việc logic; không nhất thiết có execution context riêng.

---

# 744.4 — Task

```axiom
task {
    id
    scope
    state
    operation
    cancellation
    deadline
    result
}
```

Task là abstraction chính của structured concurrency.

---

# 744.5 — Task Identity

```axiom
task_id
```

`task_id` khác:

```text
thread_id
process_id
application_id
```

Một thread có thể chạy nhiều task theo thời gian.

---

# 744.6 — Task Lifecycle

```text
CREATED
   ↓
READY
   ↓
RUNNING
   ↓
COMPLETED
```

Exceptional:

```text
WAITING
CANCEL_REQUESTED
CANCELLED
FAILED
TIMEOUT
PANICKED
```

---

# 744.7 — Task không đồng nghĩa Thread

Ví dụ:

```text
Thread 1
 ├── Task A
 ├── Task B
 └── Task C

Thread 2
 ├── Task D
 └── Task E
```

Task có thể migrate giữa worker threads nếu execution policy cho phép.

---

# 744.8 — Task Affinity

Mặc định:

```text
task → any compatible worker
```

Có thể yêu cầu:

```text
thread_affine
cpu_affine
numa_affine
device_affine
```

---

# 744.9 — Task Executor

```axiom
executor {
    submit(task)
    cancel(task)
    wait(task)
}
```

Executor chịu trách nhiệm đưa task vào execution queue.

---

# 744.10 — Executor không phải Global Scheduler

Executor quyết định:

```text
task queue
worker selection
local scheduling
```

AXCOMPUTE vẫn sở hữu resource scheduling ở tầng hệ thống.

---

# 744.11 — Thread Pool

```axiom
thread_pool {
    workers
    queue
    policy
    limits
}
```

Thread pool tái sử dụng threads thay vì tạo/destroy thread cho từng task.

---

# 744.12 — Worker

```axiom
worker {
    id
    thread
    executor
    local_queue
    state
}
```

Worker có thể giữ:

```text
local task queue
scratch memory
allocator cache
statistics
```

---

# 744.13 — Global Queue

Executor có thể có:

```text
global queue
```

dành cho task chưa được worker nhận.

---

# 744.14 — Local Queue

Mỗi worker có:

```text
local deque
```

để giảm contention.

---

# 744.15 — Work Stealing

Worker idle:

```text
Worker A: [A B C D]
Worker B: []
```

có thể steal:

```text
Worker A: [A B]
Worker B: [C D]
```

Work stealing phải là implementation strategy, không phải semantic requirement.

---

# 744.16 — Deterministic Executor

Testing/simulation có:

```axiom
deterministic_executor
```

với:

```text
logical worker
logical clock
controlled scheduling
```

---

# 744.17 — Structured Concurrency

Task phải thuộc một scope:

```axiom
task_scope {
    parent
    children
    cancellation
    deadline
}
```

---

# 744.18 — Task Scope

Ví dụ conceptual:

```axiom
scope {
    spawn(task_a)
    spawn(task_b)
    spawn(task_c)
}
```

Scope kết thúc chỉ khi policy của nó được thỏa mãn.

---

# 744.19 — Child Task Ownership

```text
parent scope
 ├── task A
 ├── task B
 └── task C
```

Child task không được tự ý sống vô hạn ngoài scope trừ khi explicit detached policy.

---

# 744.20 — Detached Task

Axiom cho phép:

```axiom
spawn_detached(task)
```

nhưng detached execution phải explicit.

Điều này tránh việc programmer vô tình tạo background task không có owner.

---

# 744.21 — Scope Cancellation

Khi parent cancel:

```text
Scope
 ├── A
 ├── B
 └── C
```

policy mặc định:

```text
cancel A
cancel B
cancel C
```

---

# 744.22 — Failure Propagation

Structured scope có thể chọn:

```text
fail_fast
collect_all
ignore_child_failure
supervisor
```

---

# 744.23 — Fail Fast

```text
A → FAILED
      ↓
scope cancellation
      ↓
B → CANCELLED
C → CANCELLED
```

---

# 744.24 — Error Collection

```axiom
task_group {
    results
    errors
    cancellations
}
```

cho phép parent nhận toàn bộ kết quả.

---

# 744.25 — Future

```axiom
future<T> {
    state
    result
    error
}
```

States:

```text
PENDING
READY
FAILED
CANCELLED
```

---

# 744.26 — Promise

```axiom
promise<T> {
    set(value)
    fail(error)
    cancel()
}
```

Một promise có thể hoàn thành một future.

---

# 744.27 — Future Await

```axiom
await future
```

Compiler/runtime phải chuyển await thành state machine hoặc continuation phù hợp thay vì tạo OS thread mới.

---

# 744.28 — Async Function

Axiom hỗ trợ:

```axiom
async function fetch_data() -> Result<Data>
```

Semantics:

```text
call
 ↓
task/future
 ↓
await
 ↓
suspend execution
 ↓
resume when ready
```

---

# 744.29 — Async không phải Thread

```text
10000 async tasks
```

không được mặc định tạo:

```text
10000 OS threads
```

---

# 744.30 — Fiber

```axiom
fiber {
    id
    stack
    context
    scheduler
}
```

Fiber là cooperative execution context.

---

# 744.31 — Fiber Switching

```text
Fiber A
   ↓ yield
Fiber B
   ↓ yield
Fiber C
```

Context switching phải tránh kernel transition khi backend cho phép.

---

# 744.32 — Fiber Stack

Hỗ trợ:

```text
fixed stack
segmented stack
growable stack
stack pooling
```

Implementation có thể lựa chọn tùy platform.

---

# 744.33 — Fiber vs Task

```text
Task
 └── may execute on fiber/thread

Fiber
 └── owns execution context + stack

Thread
 └── OS execution context
```

Không được đánh đồng ba khái niệm.

---

# 744.34 — Blocking Isolation

Blocking operation:

```text
file.read()
socket.receive()
database.query()
```

không được block toàn bộ async executor nếu API khai báo operation là blocking.

Runtime có thể chuyển sang:

```text
blocking pool
```

---

# 744.35 — Blocking Pool

```axiom
blocking_pool {
    workers
    max_workers
    queue
}
```

Dùng cho operations không thể async-native.

---

# 744.36 — Async I/O Integration

AXTHREAD tích hợp:

```text
AXNETWORK
AXSTORAGE
AXDATABASE
```

thông qua async completion.

Không tạo thread cho mỗi socket/request nếu native async backend có sẵn.

---

# 744.37 — Event Loop

```axiom
event_loop {
    poll()
    wait()
    dispatch()
}
```

Có thể dùng:

```text
IOCP
epoll
kqueue
io_uring
platform backend
```

nhưng đây là implementation detail.

---

# 744.38 — Timer Scheduler

Task có thể chờ:

```axiom
sleep(duration)
sleep_until(deadline)
```

Timer phải được multiplex thay vì tạo OS timer/thread cho từng task.

---

# 744.39 — Timer Wheel

Backend có thể sử dụng:

```text
timer wheel
heap
hierarchical timer
platform timer
```

Semantics phải giống nhau.

---

# 744.40 — Channel

```axiom
channel<T> {
    send(value)
    receive()
    close()
}
```

Channel là primitive giao tiếp task.

---

# 744.41 — Channel Modes

```text
unbounded
bounded
rendezvous
single_producer
multi_producer
single_consumer
multi_consumer
```

---

# 744.42 — Bounded Channel

```text
capacity = N
```

Khi đầy:

```text
send → WAITING
```

hoặc:

```text
send → WOULD_BLOCK
```

tùy API.

---

# 744.43 — Backpressure

Pipeline:

```text
Producer
   ↓
Channel
   ↓
Consumer
```

Consumer chậm → channel đầy → producer bị backpressured.

Không được tự động tăng memory vô hạn.

---

# 744.44 — Select / Wait Set

Axiom hỗ trợ:

```axiom
select {
    receive(channel_a)
    receive(channel_b)
    await future
    timer
}
```

---

# 744.45 — Channel Closure

```text
OPEN
 ↓
CLOSING
 ↓
CLOSED
```

Close phải đánh thức waiter phù hợp.

---

# 744.46 — Broadcast

Có thể có:

```axiom
broadcast<T>
```

cho one-to-many notification.

Broadcast semantics phải phân biệt channel queue semantics.

---

# 744.47 — Task Local Storage

```axiom
task_local<T>
```

khác:

```text
thread_local<T>
```

Task-local state phải được lưu cùng logical task context.

---

# 744.48 — Context Propagation

Một task có thể mang:

```text
deadline
cancellation
trace_id
security context reference
locale
request metadata
```

Nhưng security authority không được tự động tăng khi context được propagate.

---

# 744.49 — Cancellation Token

```axiom
cancellation_token {
    is_cancelled()
    throw_if_cancelled()
}
```

---

# 744.50 — Cancellation Source

```axiom
cancellation_source {
    token()
    cancel()
}
```

---

# 744.51 — Hierarchical Cancellation

```text
Application
 └── Request Scope
      ├── Task A
      │    └── Task A1
      └── Task B
```

Cancel Request Scope → toàn subtree nhận cancellation.

---

# 744.52 — Cancellation Safety

Một task đang giữ:

```text
lock
file transaction
database transaction
shared state
```

không được bị terminate tùy tiện bởi cooperative cancellation.

Cancellation chỉ trở thành effective tại safe cancellation points hoặc operation có semantics an toàn.

---

# 744.53 — Deadline Propagation

```text
parent deadline
      ↓
child deadline
```

Child không được tự động vượt quá parent deadline.

Có thể có explicit detached execution với deadline riêng.

---

# 744.54 — Task Priority

```text
background
normal
interactive
latency_sensitive
deadline_sensitive
```

Priority chỉ là scheduling hint.

---

# 744.55 — Priority Inheritance

Task đang giữ resource có thể được runtime/backend hỗ trợ priority inheritance thông qua synchronization primitives.

---

# 744.56 — Parallel For

Native primitive:

```axiom
parallel_for(
    begin,
    end,
    body
)
```

Compiler/runtime có thể:

```text
partition
batch
schedule
vectorize
parallelize
```

---

# 744.57 — Parallel Reduce

```axiom
parallel_reduce(
    range,
    initial,
    operation
)
```

Reduction operation phải khai báo semantics đủ để compiler đảm bảo tính hợp lệ.

---

# 744.58 — Task Granularity

Runtime phải hỗ trợ batching:

```text
100000 tiny tasks
```

không được mặc định tạo 100000 queue operations nếu compiler/runtime có thể fuse hoặc batch.

---

# 744.59 — Task Fusion

Compiler có thể fuse:

```text
Task A → Task B
```

nếu không phá:

```text
ordering
synchronization
cancellation
observability
```

---

# 744.60 — Task Inlining

Task nhỏ có thể chạy inline:

```text
spawn(task)
```

có thể được thực hiện ngay trên current worker nếu policy cho phép.

Semantic identity của task vẫn phải được giữ khi observable.

---

# 744.61 — Continuation

Future có thể có:

```axiom
future.then(fn)
```

Compiler có thể lower thành continuation thay vì thread.

---

# 744.62 — Future Composition

```axiom
all(futures)
any(futures)
race(futures)
map(future)
flat_map(future)
```

---

# 744.63 — Error Semantics

Task failure phải là data có thể truyền:

```text
future<T>
   ↓
Result<T, E>
```

Không yêu cầu exception-based async control flow.

---

# 744.64 — Panic Boundary

Một task panic:

```text
task → FAILED/PANICKED
```

không được mặc định làm crash process.

Process termination chỉ xảy ra theo panic policy.

---

# 744.65 — Panic Policy

```text
abort_process
fail_task
supervisor
custom_handler
```

---

# 744.66 — Supervisor Tasks

Supervisor scope:

```text
Supervisor
 ├── Worker A
 ├── Worker B
 └── Worker C
```

Một worker chết không nhất thiết làm toàn scope chết.

---

# 744.67 — Worker Restart

```text
Worker A
   ↓
FAILED
   ↓
supervisor
   ↓
restart
```

Restart policy:

```text
never
once
limited
always_with_backoff
```

---

# 744.68 — Restart Backoff

```text
initial_delay
maximum_delay
multiplier
jitter_policy
retry_limit
```

Random jitter phải được injectable trong deterministic simulation.

---

# 744.69 — Thread Pool Scaling

Pool có thể:

```text
grow
shrink
maintain fixed size
```

theo workload.

Không được vượt quota của `AXPROCESS`/`AXCOMPUTE`.

---

# 744.70 — Worker Parking

Worker idle có thể:

```text
park
```

thay vì busy-spin liên tục.

---

# 744.71 — Adaptive Spinning

Synchronization/queue implementation có thể:

```text
spin briefly
 ↓
yield
 ↓
park
```

để giảm latency mà không đốt CPU vô ích.

---

# 744.72 — CPU Locality

Worker nên ưu tiên:

```text
local queue
local CPU
local NUMA memory
```

trước khi steal từ remote worker.

---

# 744.73 — NUMA-aware Executor

Executor có thể có:

```text
NUMA worker group
```

để giữ task/data cùng locality.

---

# 744.74 — GPU Task

AXTHREAD có thể submit logical task tới:

```text
CPU
GPU
NPU
```

nhưng execution/resource semantics thuộc `AXCOMPUTE`.

---

# 744.75 — Device Affinity

```axiom
task {
    device = cpu
}
```

hoặc:

```axiom
task {
    device = gpu
}
```

đây là execution hint/constraint, không phải direct hardware ownership.

---

# 744.76 — Work Graph

Task dependencies:

```text
A ──┬──> C
    │
B ──┘

C ──> D
```

Có thể biểu diễn:

```axiom
task_graph {
    nodes
    dependencies
}
```

---

# 744.77 — Dependency Scheduling

Task chỉ READY khi dependency hoàn thành.

```text
A completed
B completed
      ↓
C becomes READY
```

---

# 744.78 — Cycle Detection

Task graph không được có cycle nếu graph được khai báo là DAG.

Runtime/compiler phải phát hiện cycle trước execution nếu graph static.

---

# 744.79 — Streaming Pipeline

```text
Source
  ↓
Decode
  ↓
Transform
  ↓
Encode
  ↓
Sink
```

Mỗi stage có thể là task group/channel.

Backpressure phải lan truyền ngược.

---

# 744.80 — Pipeline Cancellation

Cancel pipeline:

```text
Source
 ↓
Stage A
 ↓
Stage B
 ↓
Sink
```

cancellation phải propagate theo direction được định nghĩa.

---

# 744.81 — Batch Execution

Runtime hỗ trợ:

```axiom
submit_batch(tasks)
```

để giảm synchronization/queue overhead.

---

# 744.82 — Task Pool

Task descriptors có thể được pool:

```text
allocate task descriptor
 ↓
execute
 ↓
recycle
```

Tránh heap allocation cho từng task ngắn.

---

# 744.83 — Scratch Storage

Worker có thể có:

```text
worker_scratch
task_scratch
```

với lifetime rõ ràng.

Không được biến scratch memory thành implicit shared mutable state.

---

# 744.84 — Realtime Task

Realtime task có:

```text
deadline
period
latency_budget
```

nhưng AXTHREAD không tự đảm bảo realtime nếu underlying platform/resource scheduler không cung cấp guarantee.

---

# 744.85 — Periodic Task

```axiom
periodic_task {
    period
    deadline
    start_policy
}
```

Start policies:

```text
fixed_rate
fixed_delay
```

---

# 744.86 — Missed Deadline

Policy:

```text
skip
run_late
cancel
coalesce
report
```

---

# 744.87 — Fairness

Executor phải có policy chống starvation.

Không yêu cầu fairness tuyệt đối vì có thể ảnh hưởng latency/performance.

---

# 744.88 — Blocking Detection

Debug/runtime instrumentation có thể phát hiện:

```text
async task
   ↓
blocking syscall
```

và cảnh báo.

Không nhất thiết bật trong production.

---

# 744.89 — Thread Pinning

Một task có thể yêu cầu:

```text
same_thread
```

khi sử dụng:

```text
thread-affine API
TLS-dependent state
graphics context
audio realtime context
```

---

# 744.90 — Thread Affinity Contract

Task thread affinity phải explicit.

Không được silently migrate task nếu migration phá semantics.

---

# 744.91 — Async Resource Ownership

Async operation phải giữ resource reference hợp lệ cho tới completion/cancellation.

```text
buffer
socket
file
GPU resource
```

không được bị giải phóng trước completion.

---

# 744.92 — Lifetime Token

Runtime có thể dùng:

```axiom
lifetime_token
```

để giữ resource alive trong asynchronous operation.

Đây **không phải borrow checker**.

Đây là runtime ownership primitive explicit.

---

# 744.93 — No Mandatory GC

AXTHREAD không yêu cầu garbage collector.

Task/future/channel phải có lifetime:

```text
explicit
scope-owned
reference-counted where needed
arena-owned
```

theo từng abstraction.

---

# 744.94 — No Mandatory Borrow Checker

Compiler không cần borrow checker để thực hiện AXTHREAD.

Data-race safety được cung cấp qua:

```text
atomic
synchronization
ownership APIs
immutable data
channels
structured scopes
```

---

# 744.95 — Race Detection

Development tooling có thể cung cấp:

```text
race detector
lock-order detector
deadlock detector
```

nhưng không nằm trên production hot path.

---

# 744.96 — Data Race Model

Axiom phải phân biệt:

```text
data race
logical race
deadlock
livelock
starvation
```

Compiler không bắt buộc phải reject toàn bộ các trường hợp runtime không thể chứng minh an toàn.

---

# 744.97 — Memory Visibility

Task synchronization phải tạo memory ordering tương ứng.

Ví dụ:

```text
producer
    write data
    release
       ↓
channel
       ↓
consumer
    acquire
    read data
```

---

# 744.98 — Async Channel Zero-Copy

Large object transfer có thể sử dụng:

```text
buffer handle
shared memory
ownership transfer
```

thay vì copy payload.

---

# 744.99 — Distributed Task Boundary

AXTHREAD có thể map logical tasks lên distributed execution nhưng:

```text
local task
```

và:

```text
remote task
```

phải khác semantics.

Distributed execution thuộc `AXCOMPUTE`/`AXNETWORK`.

---

# 744.100 — Remote Task

Nếu remote execution được hỗ trợ:

```axiom
remote_task {
    node
    code
    inputs
    outputs
    deadline
}
```

Phải explicit serialization/protocol/security boundary.

Không được biến local task thành RPC một cách âm thầm.

---

# 744.101 — Security Context

Task có thể mang security context reference nhưng:

```text
spawn()
```

không được tự động cấp thêm authority.

---

# 744.102 — Capability Propagation

Child task chỉ nhận:

```text
parent capabilities
```

hoặc subset explicit.

Không được tự động nâng quyền.

---

# 744.103 — Task Isolation

Một task failure phải cô lập ở:

```text
task
```

nếu policy cho phép.

Không được implicit crash:

```text
executor
process
application
```

---

# 744.104 — Executor Isolation

Một task có thể chạy trong executor riêng:

```text
application
 ├── UI executor
 ├── IO executor
 ├── compute executor
 └── blocking executor
```

---

# 744.105 — Priority Classes

Executor có thể phân loại:

```text
UI
audio
network
storage
background
compute
```

Nhưng realtime guarantees vẫn phụ thuộc AXCOMPUTE/platform.

---

# 744.106 — Audio Integration

AXAUDIO có thể yêu cầu dedicated realtime execution.

AXTHREAD không được đưa allocation/blocking operations vào audio callback path.

---

# 744.107 — Graphics Integration

AXGRAPHICS có thể yêu cầu:

```text
render thread
GPU submission thread
```

Task migration phải tôn trọng graphics context affinity.

---

# 744.108 — Database Integration

AXDATABASE có thể sử dụng:

```text
query executor
transaction task
connection pool
```

nhưng transaction semantics vẫn thuộc database layer.

---

# 744.109 — Network Integration

AXNETWORK có thể sử dụng:

```text
event loop
IO executor
connection task
stream task
```

---

# 744.110 — Trace Model

```axiom
thread_trace_event {
    timestamp
    worker
    task
    event
}
```

Events:

```text
task_create
task_start
task_suspend
task_resume
task_complete
task_fail
task_cancel
worker_steal
worker_park
worker_wake
channel_send
channel_receive
await
wake
deadline_miss
```

---

# 744.111 — Trace Sampling

Production:

```text
OFF
SAMPLED
ERROR_ONLY
FULL
```

---

# 744.112 — Deterministic Replay

Replay cần ghi:

```text
task ordering
logical synchronization events
external input
timers
randomness
```

Không tuyên bố bit-exact CPU execution nếu hardware/FP environment không được kiểm soát.

---

# 744.113 — Simulation

```axiom
thread_simulation {
    tasks
    workers
    queues
    dependencies
    virtual_time
}
```

Có thể mô phỏng:

```text
contention
starvation
queue saturation
deadline misses
failure
cancellation
```

---

# 744.114 — Digital Twin

Thread runtime digital twin phải biểu diễn:

```text
workers
queues
tasks
dependencies
resource usage
latency
```

không nhất thiết mô phỏng instruction-level CPU.

---

# 744.115 — Performance Architecture

AXTHREAD hot path phải ưu tiên:

```text
lock-free / low-lock queues
per-worker local queues
work stealing
task descriptor pooling
cache locality
NUMA locality
batched submission
inline execution
zero-copy payloads
```

---

# 744.116 — Hot Path Allocation

Không được bắt buộc heap allocation khi:

```text
spawn tiny task
queue task
wake worker
complete task
```

Runtime phải có fast path sử dụng pool/inline storage.

---

# 744.117 — Cold Path

Heap allocation có thể chấp nhận ở:

```text
executor creation
pool resizing
diagnostics
trace initialization
rare failure
dynamic configuration
```

---

# 744.118 — Queue Representation

Implementation ưu tiên:

```text
dense arrays
ring buffers
intrusive nodes
generation counters
```

thay vì object graph nặng.

---

# 744.119 — False Sharing

Worker/task metadata phải có tùy chọn padding/alignment khi cần để tránh false sharing.

---

# 744.120 — Cache Locality

Task descriptor nên giữ:

```text
hot state
```

tách khỏi:

```text
cold diagnostics
debug metadata
trace metadata
```

---

# 744.121 — Context Switch Cost

Fiber/task switching phải cố gắng tránh:

```text
kernel transition
full process context switch
```

khi không cần.

---

# 744.122 — Compiler Integration

Compiler phải hiểu:

```text
async
await
spawn
parallel_for
task scope
channel
```

đủ để lower trực tiếp xuống AXTHREAD primitives.

---

# 744.123 — Async State Machine

Compiler có thể lower:

```axiom
async fn foo()
```

thành:

```text
state machine
+
continuation
+
future
```

không cần hidden OS thread.

---

# 744.124 — Stackless Async

Default async execution nên ưu tiên:

```text
stackless state machine
```

khi function có thể compile theo model này.

---

# 744.125 — Stackful Fiber

Fiber dành cho trường hợp:

```text
legacy blocking-style code
coroutine requiring stack
user-space scheduler
```

---

# 744.126 — API Layering

API hierarchy:

```text
Low level
    AXPROCESS thread

Mid level
    AXTHREAD executor
    AXTHREAD fiber

High level
    task
    async
    future
    channel
    structured scope

Parallel
    parallel_for
    task graph
```

---

# 744.127 — Error Handling

AXTHREAD APIs phải phân biệt:

```text
invalid argument
resource exhausted
deadline expired
cancelled
closed
would block
executor stopped
task failed
system failure
```

---

# 744.128 — Executor Shutdown

```text
RUNNING
   ↓
STOP_REQUESTED
   ↓
DRAINING
   ↓
STOPPED
```

---

# 744.129 — Shutdown Policies

```text
drain
cancel_pending
cancel_all
immediate
```

---

# 744.130 — Shutdown Safety

Executor không được giải phóng worker/task resources trước khi:

```text
active tasks
pending tasks
callbacks
futures
```

đã được xử lý theo shutdown policy.

---

# 744.131 — Thread Runtime Security

Không cho task:

```text
change protected thread priority
escape CPU quota
map arbitrary process memory
transfer arbitrary capability
```

nếu không có authority từ AXSECURITY.

---

# 744.132 — Observability

Runtime phải cung cấp:

```text
active task count
queued task count
worker utilization
steal count
wake count
park count
queue latency
task latency
deadline misses
cancellation count
failure count
```

---

# 744.133 — Native API

```axiom
create_executor()
destroy_executor()

create_thread_pool()
resize_thread_pool()

spawn()
spawn_detached()

create_task_scope()
cancel_scope()

await()
yield_task()

sleep()
sleep_until()

create_future()
create_promise()

future_all()
future_any()
future_race()

create_channel()
send()
receive()
close_channel()

select()

parallel_for()
parallel_reduce()

create_task_graph()
submit_graph()

create_fiber()
switch_fiber()
yield_fiber()

create_cancellation_source()
get_cancellation_token()
cancel()

create_periodic_task()

set_task_priority()
set_task_affinity()
set_task_deadline()

get_task_state()
get_executor_stats()

start_thread_trace()
stop_thread_trace()

create_deterministic_executor()
record_schedule()
replay_schedule()

create_thread_simulation()
```

---

# 744.134 — Canonical Flow: Structured Concurrency

```text
scope
 │
 ├── spawn A
 ├── spawn B
 └── spawn C
       │
       ▼
   await scope
       │
       ├── A complete
       ├── B complete
       └── C complete
              │
              ▼
          scope exits
```

---

# 744.135 — Canonical Flow: Async I/O

```text
async task
    ↓
network read
    ↓
submit async I/O
    ↓
task suspended
    ↓
kernel/event backend
    ↓
completion
    ↓
future ready
    ↓
task resumed
```

Không cần giữ OS thread blocked trong thời gian chờ.

---

# 744.136 — Canonical Flow: Work Stealing

```text
Worker A
[A B C D]

Worker B
[]

Worker B steals
     ↓

Worker A
[A B]

Worker B
[C D]
```

---

# 744.137 — Canonical Flow: Cancellation

```text
Scope
 ├── A
 ├── B
 └── C
      │
 cancel()
      ↓
token = cancelled
      ↓
A/B/C observe
      ↓
cleanup
      ↓
completion
```

---

# 744.138 — Canonical Flow: Failure

```text
Task A
  ↓
FAILED
  ↓
Scope policy
  ├── fail_fast
  │      ↓
  │   cancel siblings
  │
  └── collect_all
         ↓
      continue
```

---

# 744.139 — Canonical Flow: Backpressure

```text
Producer
    ↓
bounded channel
    ↓
Consumer
    ↓
slow

channel full
    ↓
producer waits
    ↓
consumer consumes
    ↓
producer resumes
```

---

# 744.140 — Canonical Flow: Parallel Loop

```text
range [0..N]
      ↓
partition
      ↓
task batches
 ┌────┼────┐
 ▼    ▼    ▼
 T1   T2   T3
 │    │    │
 └────┼────┘
      ▼
   completion
```

---

# 744.141 — Formal Invariants

```text
THR-INV-01   Every task has a stable task identity.
THR-INV-02   Task identity is distinct from thread identity.
THR-INV-03   Thread identity is distinct from process identity.
THR-INV-04   A task does not imply creation of an OS thread.
THR-INV-05   Task ownership is explicit.
THR-INV-06   Structured child tasks belong to an explicit scope.
THR-INV-07   Detached tasks require explicit detachment.
THR-INV-08   Task migration cannot violate explicit affinity.
THR-INV-09   Async suspension does not imply blocked OS thread.
THR-INV-10   Async state remains valid until completion/cancellation.

THR-INV-11   Cancellation is distinct from forced termination.
THR-INV-12   Parent cancellation propagates according to scope policy.
THR-INV-13   Child cancellation cannot implicitly grant authority.
THR-INV-14   Child deadlines cannot silently exceed parent deadlines.
THR-INV-15   Failed tasks have explicit failure state.
THR-INV-16   Task failure does not implicitly terminate unrelated tasks.
THR-INV-17   Panic policy is explicit.
THR-INV-18   Executor shutdown policy is explicit.
THR-INV-19   Executor shutdown cannot silently abandon owned tasks.
THR-INV-20   Blocking operations cannot silently block the async executor indefinitely.

THR-INV-21   Channel capacity semantics are explicit.
THR-INV-22   Bounded channels provide explicit backpressure.
THR-INV-23   Channel closure wakes affected waiters.
THR-INV-24   Future completion occurs at most once.
THR-INV-25   Promise completion occurs at most once.
THR-INV-26   Await observes a consistent completion state.
THR-INV-27   Synchronization establishes required memory visibility.
THR-INV-28   Task-local state is distinct from thread-local state.
THR-INV-29   Work stealing cannot duplicate task execution.
THR-INV-30   Task queues preserve required ordering semantics.

THR-INV-31   Task resource ownership remains valid through asynchronous completion.
THR-INV-32   Zero-copy transfer requires valid buffer ownership.
THR-INV-33   Task scheduling cannot bypass AXCOMPUTE resource policy.
THR-INV-34   Task execution cannot bypass AXSECURITY authority.
THR-INV-35   Deterministic execution is isolated from production scheduling.
THR-INV-36   Replay cannot mutate production execution state.
THR-INV-37   Disabled tracing cannot require full tracing overhead.
THR-INV-38   Production task hot paths do not require heap allocation.
THR-INV-39   Thread pools cannot exceed explicit process/resource limits.
THR-INV-40   Identical deterministic task inputs and scheduling decisions produce identical logical task state.
```

---

# 744.142 — Completion Criteria

`BOOTSTRAP-744` phải freeze:

1. Task identity.
2. Task lifecycle.
3. Executor.
4. Thread pool.
5. Worker.
6. Local queue.
7. Global queue.
8. Work stealing.
9. Task scheduling.
10. Structured concurrency.
11. Task scopes.
12. Detached tasks.
13. Failure propagation.
14. Future.
15. Promise.
16. Async.
17. Await.
18. Continuation.
19. Future composition.
20. Error propagation.
21. Panic boundary.
22. Supervisor tasks.
23. Restart policy.
24. Backoff.
25. Fiber.
26. Fiber stack.
27. Fiber switching.
28. Stackless async.
29. Blocking isolation.
30. Blocking pool.
31. Event loop.
32. Async I/O.
33. Timers.
34. Channels.
35. Bounded channels.
36. Backpressure.
37. Broadcast.
38. Select/wait-set.
39. Channel closure.
40. Cancellation source.
41. Cancellation token.
42. Hierarchical cancellation.
43. Deadline propagation.
44. Task priority.
45. Parallel-for.
46. Parallel-reduce.
47. Task granularity.
48. Task fusion.
49. Task inlining.
50. Task graphs.
51. Dependency scheduling.
52. Pipeline execution.
53. CPU affinity.
54. NUMA affinity.
55. Device affinity.
56. Thread affinity.
57. Realtime task contract.
58. Periodic task.
59. Deadline-miss policy.
60. Fairness.
61. Blocking detection.
62. Lifetime token.
63. No mandatory GC.
64. No mandatory borrow checker.
65. Race/deadlock diagnostics.
66. Memory visibility.
67. Zero-copy task communication.
68. Remote task boundary.
69. Security context propagation.
70. Executor isolation.
71. AXAUDIO integration.
72. AXGRAPHICS integration.
73. AXDATABASE integration.
74. AXNETWORK integration.
75. Trace model.
76. Deterministic replay.
77. Simulation.
78. Digital twin.
79. Performance architecture.
80. Compiler integration.
81. Async state-machine lowering.
82. Hot-path allocation policy.
83. Queue architecture.
84. Shutdown semantics.
85. Resource limits.
86. Security boundary.
87. Observability.
88. Native API.
89. Canonical flows.
90. 40 formal invariants.

---

# 744.143 — Definition of Done

```text
BOOTSTRAP-744
STATUS: COMPLETE / FROZEN

AXTHREAD
 ├── Task Runtime
 ├── Executor
 ├── Thread Pool
 ├── Work Stealing
 ├── Structured Concurrency
 ├── Task Scope
 ├── Cancellation
 ├── Deadline
 ├── Future / Promise
 ├── Async / Await
 ├── Continuations
 ├── Fiber
 ├── Event Loop
 ├── Async I/O
 ├── Timer Runtime
 ├── Channel
 ├── Backpressure
 ├── Select
 ├── Supervisor
 ├── Parallel Execution
 ├── Task Graph
 ├── Pipeline
 ├── CPU / NUMA Affinity
 ├── Device Affinity
 ├── Realtime Contract
 ├── Blocking Isolation
 ├── Zero-Copy Communication
 ├── Compiler Lowering
 ├── Security Integration
 ├── Deterministic Scheduling
 ├── Replay
 ├── Simulation
 ├── Telemetry
 ├── Performance Fast Path
 ├── Native API
 ├── 40 Formal Invariants
 └── Thread & Concurrency Runtime 5.0
```

**BOOTSTRAP-744 / AXTHREAD — ARCHITECTURAL BASELINE FROZEN.**

---

# BOOTSTRAP-745 — AXMEMORY

**Native Memory & Virtual Memory Runtime — virtual address spaces, physical-page abstraction, page tables, mappings, heaps, arenas, pools, slab allocation, thread-local allocation, large pages, NUMA memory, shared memory, memory-mapped files, copy-on-write, guard pages, memory protection, executable memory, DMA/device memory, pinned memory, memory pressure, reclamation, compaction policy, fragmentation control, allocation tracing, memory debugging, deterministic allocation, persistent/mapped memory, zero-copy, memory accounting, memory simulation và Memory Runtime 5.0.**