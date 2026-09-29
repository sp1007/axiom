:::writing{variant="document" id="58321" title="BOOTSTRAP-607 — Native Application Scheduling, Threading, Async Runtime & Executor 5.0"}

# BOOTSTRAP-607 — Native Application Scheduling, Threading, Async Runtime & Executor 5.0

**Status:** ARCHITECTURE SPECIFICATION  
**Layer:** Native Runtime / Execution  
**Depends on:** BOOTSTRAP-600, 601, 602, 603, 604, 605, 606  
**Primary concern:** CPU execution, OS threads, tasks, async/await, executors, scheduling, I/O waiting and cancellation.

---

## 1. Purpose

BOOTSTRAP-607 defines the Axiom execution engine responsible for deciding:

- which work executes;
- on which worker;
- on which OS thread;
- when work runs;
- when work suspends;
- when work resumes;
- how blocking operations are isolated;
- how asynchronous I/O is integrated;
- how cancellation and deadlines propagate;
- how CPU and resource budgets from BOOTSTRAP-606 are enforced.

The runtime must support both:

```text
Traditional native threading
```

and:

```text
Lightweight Axiom tasks + async/await
```

without forcing applications to use either model exclusively.

The architecture must permit:

```text
Application
 ├── ordinary synchronous function
 ├── OS thread
 ├── lightweight task
 ├── async task
 ├── blocking worker
 ├── I/O operation
 └── GPU operation
```

to coexist.

---

# 2. Design Goals

### G1 — Native performance

Thread execution must map directly to native OS primitives.

### G2 — Cheap tasks

An Axiom task should be substantially cheaper than creating an OS thread.

### G3 — No mandatory GC

The scheduler must not depend on garbage collection.

### G4 — No mandatory borrow checker

Concurrency safety must primarily come from:

- ownership/lifetime rules already defined by Axiom;
- explicit synchronization;
- structured concurrency;
- capability/resource boundaries.

### G5 — Async without callback hell

The language should expose:

```axiom
async function load() -> Data
```

rather than requiring manual callback state machines.

### G6 — Compiler-generated state machines

`async/await` should normally compile into explicit state-machine IR.

The runtime should execute the generated machine rather than implement a heavyweight coroutine object model.

### G7 — Blocking isolation

A blocking syscall must never silently consume an async executor worker indefinitely.

### G8 — Cancellation

Cancellation must be explicit, composable and cooperative.

### G9 — Fairness

A task must not be able to monopolize an executor indefinitely.

### G10 — Resource-aware scheduling

The scheduler must cooperate with BOOTSTRAP-606 rather than bypassing resource limits.

---

# 3. Non-Goals

BOOTSTRAP-607 does not define:

- distributed scheduling;
- cluster scheduling;
- operating-system process orchestration;
- GPU kernel programming language;
- network protocol semantics;
- application-level actor frameworks.

Those belong to higher layers.

---

# 4. Execution Hierarchy

Axiom defines four execution levels.

```text
Application
    │
    ▼
Executor
    │
    ├── Worker
    │      │
    │      └── OS Thread
    │
    └── Task
           │
           ├── synchronous execution
           └── async state machine
```

Conceptually:

```text
OS Thread
   ↓
Worker
   ↓
Executor
   ↓
Task
   ↓
Function / Async State Machine
```

---

# 5. Execution Entities

## 5.1 Thread

A `Thread` represents an OS execution thread.

Properties:

```text
ThreadId
Generation
Name
Priority
Affinity
Stack
ResourceGroup
State
```

Identity:

```text
ThreadKey {
    id: ThreadId
    generation: u32
}
```

Generation prevents stale handles from referring to a recycled OS thread identity.

---

# 6. Thread States

```text
Created
Starting
Running
Parked
Stopping
Stopped
Failed
```

Transitions:

```text
Created → Starting → Running
Running → Parked
Parked → Running
Running → Stopping
Stopping → Stopped
Running → Failed
```

A stopped thread can never become running again.

A new OS thread receives a new generation.

---

# 7. Thread Stack

Each native thread has an explicitly allocated native stack.

Configuration:

```axiom
ThreadOptions {
    stack_size: Bytes
    guard_pages: u32
}
```

Default stack size is platform-specific.

The runtime must not require segmented stacks.

For async tasks, suspension does **not** preserve the native thread stack.

Instead:

```text
async task
    ↓
compiler-generated state machine
    ↓
heap/arena/task-frame storage
```

---

# 8. Task

A `Task` represents schedulable logical work.

A task is not necessarily an OS thread.

A typical executor may contain:

```text
8 OS threads
100,000 tasks
```

provided resource limits permit it.

Task identity:

```text
TaskKey {
    id: TaskId
    generation: u32
}
```

---

# 9. Task States

```text
Created
Queued
Running
Waiting
Sleeping
Completed
Cancelled
Failed
Detached
```

State machine:

```text
Created
   ↓
Queued
   ↓
Running
 ┌─┴─────────────┐
 ▼               ▼
Waiting         Completed
 │
 ▼
Queued

Running → Sleeping → Queued

Running → Failed
Running → Cancelled
```

---

# 10. Task Ownership

Tasks should normally have an owning parent task or executor scope.

Example:

```axiom
async function main() {
    let a = spawn work_a()
    let b = spawn work_b()

    await a
    await b
}
```

The parent owns the lifetime of `a` and `b`.

This produces structured concurrency.

---

# 11. Structured Concurrency

Default rule:

> A child task must not outlive its structured parent scope unless explicitly detached.

Example:

```axiom
async function process() {
    let task = spawn worker()
    await task
}
```

The scope cannot finish while `task` remains active.

---

# 12. Detached Tasks

Detached execution is explicit:

```axiom
detach spawn background_cleanup()
```

A detached task becomes owned by an executor/application scope.

Detached tasks must not silently inherit arbitrary stack-local resources.

Therefore:

```text
stack-local value
       X
       │
       └── cannot outlive parent scope
```

The compiler must reject unsafe lifetime escapes according to the Axiom lifetime/value model.

---

# 13. Task Failure

An uncaught task failure becomes:

```text
TaskFailure {
    task_id
    parent_task_id
    service_id
    process_id
    error
    stack_trace
}
```

For structured children:

```text
child failure
    ↓
parent task cancellation
    ↓
sibling cancellation
    ↓
parent receives failure
```

This is the default failure-propagation policy.

---

# 14. Executor

An `Executor` owns schedulable tasks and workers.

Core structure:

```axiom
struct Executor {
    id: ExecutorId
    workers: WorkerSet
    scheduler: Scheduler
    timers: TimerService
    reactor: IoReactor
    resource_group: ResourceGroup
}
```

Struct-only methods:

```axiom
function Executor.spawn(self: Executor, task: TaskFn) -> JoinHandle
function Executor.shutdown(self: Executor) -> Result
function Executor.stats(self: Executor) -> ExecutorStats
```

---

# 15. Executor Types

Axiom defines four standard executor modes.

### 15.1 CPU executor

Optimized for CPU-bound work.

### 15.2 Async executor

Optimized for large numbers of suspended I/O tasks.

### 15.3 Blocking executor

Dedicated to blocking operations.

### 15.4 Deterministic executor

Used for testing and reproducibility.

Applications may create custom executors.

---

# 16. Worker

A worker is a scheduler entity normally backed by one OS thread.

```axiom
struct Worker {
    id: WorkerId
    thread: ThreadKey
    queue: TaskQueue
    state: WorkerState
}
```

Worker states:

```text
Starting
Running
Parking
Parked
Stopping
Stopped
```

---

# 17. Scheduler Architecture

Default scheduler:

```text
                    Global Queue
                        │
          ┌─────────────┼─────────────┐
          ▼             ▼             ▼
       Worker 0      Worker 1      Worker 2
       Local Q       Local Q       Local Q
          ↕             ↕             ↕
       stealing      stealing      stealing
```

Each worker owns a local deque.

Benefits:

- reduced contention;
- cache locality;
- scalable task submission;
- efficient child-task execution.

---

# 18. Local Queue

Default policy:

```text
owner:
    LIFO

thief:
    FIFO
```

The worker executes recently-created tasks first.

Other workers steal older tasks.

This generally improves locality while preventing abandoned old work.

---

# 19. Global Queue

The global queue handles:

- external submissions;
- cross-executor submissions;
- overflow;
- tasks with explicit global scheduling requirements.

The global queue must be bounded or governed by BOOTSTRAP-606.

---

# 20. Work Stealing

If a worker has no local task:

```text
1. check local queue
2. check global queue
3. inspect I/O completions
4. inspect timers
5. steal from another worker
6. park
```

Victim selection should avoid deterministic hot spots.

Possible implementation:

```text
pseudo-random victim
+
topology-aware preference
```

Deterministic mode replaces randomness with a deterministic sequence.

---

# 21. CPU Topology

The scheduler may detect:

```text
CPU package
NUMA node
physical core
logical CPU
performance class
```

The information becomes:

```axiom
CpuTopology
```

The scheduler may use topology to improve locality.

Correctness must never depend on topology information.

---

# 22. NUMA

NUMA-aware scheduling is optional.

Default behavior:

```text
task → worker local node
```

Memory placement may remain controlled by the memory/resource subsystem.

Axiom must not require NUMA APIs.

---

# 23. Worker Parking

When no work exists:

```text
worker
  ↓
short spin
  ↓
yield
  ↓
park
```

The spin duration should be adaptive.

Parking must use native OS primitives rather than busy-waiting indefinitely.

---

# 24. Worker Wakeup

Submitting work to a parked executor:

```text
enqueue task
      ↓
wake one worker
```

If work exceeds available workers:

```text
wake additional workers
```

Wakeups must be coalesced to avoid thundering-herd behavior.

---

# 25. Fairness

A task cannot indefinitely monopolize a worker.

For CPU tasks, the runtime tracks:

```text
execution time
queue wait time
preemption/yield count
```

A task exceeding its scheduling quantum should:

```text
yield
```

or, for compiler-generated safe points:

```text
scheduler checkpoint
```

The scheduler must not asynchronously terminate arbitrary native code.

---

# 26. Cooperative CPU Yield

Axiom provides:

```axiom
yield()
```

and:

```axiom
await yield()
```

depending on execution context.

The compiler may insert safe scheduler checkpoints into:

- async state machines;
- generated loops when enabled;
- runtime-managed execution regions.

It must not silently insert expensive checks into every instruction.

---

# 27. Priority

Task priority:

```text
Critical
High
Normal
Low
Background
```

Priority is a scheduling hint, not a security authority.

A task cannot use:

```axiom
priority = Critical
```

to bypass resource limits.

---

# 28. Priority Inversion

Synchronization primitives must support priority inheritance or priority-aware mitigation where the platform provides it.

At minimum:

```text
high-priority waiter
        ↓
low-priority lock owner
        ↓
temporary priority boost
```

The exact mechanism is platform-specific.

---

# 29. Resource Governor Integration

Every executor and worker belongs to a BOOTSTRAP-606 resource group.

```text
Application
   │
ResourceGroup
   │
Executor
   │
Worker
   │
Task
```

CPU consumption is charged to the logical owner.

---

# 30. Task Resource Attribution

For:

```text
Task A
 └── CPU
```

CPU accounting charges Task A's resource group.

For a task performing IPC:

```text
Task A
 └── IPC
      └── ResourceGroup A
```

Shared resources use defined attribution rules rather than double-counting.

---

# 31. CPU Budget

BOOTSTRAP-606 may specify:

```axiom
CpuBudget {
    period: Duration
    quota: CpuTime
}
```

When exhausted:

```text
task remains logically runnable
        ↓
scheduler throttles execution
        ↓
budget replenishes
```

The runtime must not busy-spin waiting for budget replenishment.

---

# 32. Thread Quota

Executor creation is rejected when:

```text
current_threads + requested_threads > hard_limit
```

Soft limits produce diagnostics or admission pressure.

---

# 33. Task Quota

Tasks are counted separately from threads.

Example:

```text
max_tasks = 100_000
```

This protects the process from accidental task explosions.

---

# 34. Task Frame

An async function is lowered into a state machine.

Example conceptual transformation:

```axiom
async function fetch() -> Data
```

becomes approximately:

```text
FetchState {
    state
    local_1
    local_2
    pending_operation
}
```

with:

```text
poll(FetchState)
```

The exact ABI is compiler-defined.

---

# 35. Async State Machine ABI

Every generated async state machine provides:

```text
poll()
drop()
cancel()
```

Conceptually:

```text
PollResult =
    Pending
    Ready(Value)
    Failed(Error)
```

No general-purpose coroutine runtime is required.

---

# 36. Suspension

At:

```axiom
let x = await io_operation()
```

the compiler generates:

```text
save live locals
save state number
register continuation
return Pending
```

When the operation completes:

```text
resume state machine
```

---

# 37. No Native Stack Preservation

The default async runtime does not save the entire native stack.

Therefore:

```text
async task
```

can support very large numbers of suspended tasks without allocating one native stack per task.

---

# 38. Async Allocation Policy

A simple async function should avoid unnecessary heap allocation.

Possible implementation:

```text
caller-owned frame
```

for directly awaited operations.

A detached task may require:

```text
executor-owned task frame
```

The compiler chooses the smallest valid representation.

---

# 39. JoinHandle

```axiom
struct JoinHandle<T> {
    task: TaskKey
}
```

Operations:

```axiom
function JoinHandle.await(self) -> Result<T>
function JoinHandle.cancel(self)
function JoinHandle.is_done(self) -> bool
```

A join handle does not itself own an OS thread.

---

# 40. Cancellation

Axiom defines:

```axiom
struct CancelToken {
    source: CancelSource
}
```

Cancellation is cooperative.

Propagation:

```text
parent cancelled
      ↓
child token cancelled
      ↓
awaiting operation notified
      ↓
task resumes
      ↓
task returns Cancelled
```

---

# 41. Cancellation Safety

Cancellation must occur at defined cancellation points.

Typical cancellation points:

- `await`;
- channel wait;
- timer wait;
- I/O wait;
- semaphore wait;
- explicit `check_cancel()`;
- executor yield.

The runtime must not arbitrarily interrupt native instructions.

---

# 42. Non-Cancellable Region

Some operations require atomic completion.

Axiom provides:

```axiom noncancelable {
    commit_transaction()
}
```

The region should be short.

The cancellation request remains pending and becomes observable after the region.

---

# 43. Deadlines

Cancellation and timeout are separate concepts.

```axiom
await operation()
    with deadline = now() + 5s
```

The runtime represents:

```text
Deadline
```

rather than creating one OS timer per operation where unnecessary.

---

# 44. Timer Service

Timers use a centralized timer subsystem.

Possible implementation:

```text
timer wheel
```

for large numbers of timers, with a heap or hierarchical wheel depending on workload.

Required properties:

- monotonic clock;
- bounded overhead;
- cancellation;
- deadline ordering;
- efficient bulk timers.

---

# 45. Timer Integration

```text
Task
 ↓
TimerService
 ↓
timer expires
 ↓
enqueue task
 ↓
Executor
```

Timer expiration never executes arbitrary user code directly from the timer interrupt context.

---

# 46. I/O Reactor

Axiom defines:

```axiom trait IoReactor {
    function submit(...)
    function cancel(...)
    function poll(...)
}
```

Platform backends include:

### Windows

IOCP.

### Linux

epoll and optionally io_uring.

### macOS

kqueue.

### Android

native platform facilities plus supported Linux mechanisms.

### iOS

native asynchronous APIs mapped through the platform adapter.

### WASM

host-provided asynchronous callbacks/promises.

### Embedded

host/platform-defined event source.

---

# 47. Reactor vs Proactor

The abstraction must support both:

```text
Reactor:
    readiness notification
```

and:

```text
Proactor:
    completion notification
```

Therefore the common abstraction is:

```text
AsyncOperation
```

rather than exposing epoll/io_uring/IOCP semantics directly to application code.

---

# 48. I/O Completion

Conceptual flow:

```text
Task
 ↓
submit I/O
 ↓
Pending
 ↓
OS
 ↓
completion
 ↓
IoReactor
 ↓
enqueue continuation
 ↓
Worker
 ↓
Task resumes
```

---

# 49. Blocking Operations

Axiom distinguishes:

```text
async operation
```

from:

```text
blocking operation
```

Blocking operations must be submitted to a blocking executor.

Example:

```axiom
await blocking {
    legacy_library_call()
}
```

---

# 50. Blocking Executor

The blocking executor has its own:

- worker pool;
- thread quota;
- CPU budget;
- queue;
- admission control.

It must not silently consume all async workers.

---

# 51. Blocking Pool Growth

Default:

```text
minimum workers
maximum workers
idle timeout
```

Growth occurs only when:

```text
queued blocking work > available blocking workers
```

and BOOTSTRAP-606 permits additional threads.

---

# 52. Blocking Pool Protection

If maximum blocking workers are exhausted:

```text
new blocking task → queued
```

rather than:

```text
create unlimited threads
```

This prevents thread explosions.

---

# 53. Synchronization

BOOTSTRAP-607 consumes synchronization primitives from the concurrency subsystem.

Required primitives include:

```text
Mutex
RwLock
Semaphore
Event
Condition
Barrier
Latch
Atomic
Channel
```

The detailed primitive ABI may be split into a subsequent specification.

---

# 54. Atomic Operations

Axiom supports:

```text
load
store
exchange
compare_exchange
fetch_add
fetch_sub
fetch_and
fetch_or
fetch_xor
```

Memory order:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

The compiler maps these to the target ISA.

---

# 55. Lock-Free Scheduler Structures

The scheduler should use:

- atomic indices;
- per-worker deques;
- low-contention wakeup state;
- bounded queues where possible.

A global mutex must not guard every task submission or execution.

---

# 56. Channels

Channels provide message-oriented synchronization.

Core forms:

```text
Unbounded
Bounded
SingleProducer
MultiProducer
SingleConsumer
MultiConsumer
```

However, "unbounded" is still subject to BOOTSTRAP-606 resource limits.

---

# 57. Backpressure

A bounded channel:

```axiom
channel<T>(capacity: 1024)
```

must provide:

```text
send()
try_send()
receive()
try_receive()
```

and async forms:

```text
send_async()
receive_async()
```

When full:

```text
sender waits
```

rather than allocating unlimited memory.

---

# 58. Async Channel Wakeups

Channel operations integrate with task scheduling.

```text
send
 ↓
enqueue receiver continuation
 ↓
worker executes receiver
```

No polling loop should be required.

---

# 59. Thread-Local Storage

Axiom provides:

```axiom thread_local<T>
```

for data tied to an OS thread.

Thread-local state must not be confused with task-local state.

---

# 60. Task-Local Context

Async execution also requires task-local state:

```text
TaskLocal<T>
```

Examples:

- correlation ID;
- trace context;
- locale;
- request metadata;
- cancellation token.

When a task migrates between workers:

```text
worker-local state ≠ task-local state
```

Task-local context follows the task.

---

# 61. Diagnostics Integration

Every task may carry:

```text
TaskId
ParentTaskId
ExecutorId
WorkerId
TraceId
SpanId
ServiceId
ResourceGroupId
```

BOOTSTRAP-602 can therefore report:

```text
task queue latency
task execution time
await latency
I/O latency
worker utilization
blocked-worker count
task cancellation
executor saturation
```

---

# 62. Deadlock Diagnostics

Debug/diagnostic builds may construct a wait graph:

```text
Task A → Mutex X
Task B → Mutex Y
Task C → Task A
```

Potential cycles are reported.

The runtime must not add expensive graph tracking to production unless explicitly enabled.

---

# 63. Starvation Detection

Diagnostics can detect:

```text
task waiting unusually long
```

based on configurable thresholds.

Report:

```text
queue age
priority
resource throttling
lock wait
I/O wait
worker availability
```

The system should identify possible causes rather than claiming that a particular cause is always responsible.

---

# 64. Configuration

BOOTSTRAP-601 supplies:

```text
executor.worker_count
executor.max_tasks
executor.queue_capacity
executor.policy
executor.spin_duration
blocking.min_workers
blocking.max_workers
blocking.idle_timeout
timer.granularity
scheduler.priority_enabled
```

Configuration is loaded once into an immutable runtime snapshot.

---

# 65. Dynamic Configuration

Changes that cannot safely occur live are deferred until executor recreation.

Examples:

```text
worker stack size
```

Changes that can safely occur live:

```text
queue limit
diagnostic sampling
priority policy
```

must use atomic configuration snapshots.

---

# 66. Service Lifecycle Integration

BOOTSTRAP-605 controls:

```text
start
ready
stop
restart
```

BOOTSTRAP-607 controls the execution infrastructure used by the service.

Startup:

```text
Supervisor
 ↓
Service
 ↓
Executor
 ↓
Workers
 ↓
Service initialization task
 ↓
Ready
```

---

# 67. Shutdown

Shutdown sequence:

```text
Supervisor requests drain
        ↓
stop accepting new tasks
        ↓
cancel structured children
        ↓
finish allowed work
        ↓
cancel remaining waits
        ↓
stop I/O
        ↓
stop workers
        ↓
Executor stopped
```

---

# 68. Drain Mode

Executor states:

```text
Running
Draining
Stopped
```

During draining:

```text
new application tasks → rejected
existing tasks → allowed to finish according to policy
```

---

# 69. Shutdown Deadline

The supervisor supplies:

```text
shutdown deadline
```

When deadline expires:

```text
cooperative cancellation
        ↓
forced executor termination
```

Native thread termination must be avoided where possible because arbitrary thread termination can leave locks/resources inconsistent.

---

# 70. Crash Handling

If a worker encounters an unrecoverable process fault:

```text
BOOTSTRAP-602 crash handler
        ↓
process diagnostics
        ↓
BOOTSTRAP-605 supervisor
        ↓
service recovery
```

The executor itself must not attempt to continue from arbitrary memory corruption.

---

# 71. IPC Integration

BOOTSTRAP-604 operations can return asynchronous handles.

Example:

```axiom
let message = await channel.receive()
```

Flow:

```text
IPC
 ↓
OS event
 ↓
IoReactor
 ↓
Task continuation
```

Backpressure is enforced by BOOTSTRAP-604 + BOOTSTRAP-606.

---

# 72. Zero-Copy Integration

When IPC supplies a shared buffer:

```text
SharedBuffer
 ↓
Task
```

the task receives a resource handle rather than copying payload bytes.

Lifetime remains governed by the buffer ownership rules.

---

# 73. State/Checkpoint Integration

BOOTSTRAP-600 cannot snapshot arbitrary running task stacks.

Therefore checkpointing occurs at safe quiescence points.

A service may request:

```text
executor.quiesce()
```

The executor:

```text
stop new work
 ↓
wait for tasks to reach safe points
 ↓
flush I/O state
 ↓
checkpoint application state
```

Tasks that cannot reach a safe point are reported.

---

# 74. GPU Execution

CPU and GPU execution are separate scheduling domains.

```text
CPU Executor
     │
     └── GPU submission
             ↓
        GPU Executor
             ↓
        GPU Stream
```

A CPU worker must not remain blocked waiting for a GPU operation when asynchronous completion is possible.

---

# 75. GPU Task

Conceptual API:

```axiom
let result = await gpu.submit(kernel)
```

GPU resources are charged to BOOTSTRAP-606.

Required accounting:

```text
VRAM
GPU context
stream
command queue
kernel time where measurable
```

---

# 76. CPU/GPU Synchronization

Preferred:

```text
GPU event
 ↓
completion callback/event
 ↓
resume task
```

rather than:

```text
CPU busy wait
```

---

# 77. Security Integration

Thread creation, affinity and priority changes are capability-controlled where required by BOOTSTRAP-603.

Example:

```text
ThreadCapability
CpuAffinityCapability
SchedulingPriorityCapability
```

Untrusted code cannot self-grant elevated scheduling authority.

---

# 78. Resource Capability Checks

Before:

```text
create worker
```

the executor checks:

```text
Thread capability
ResourceGroup quota
```

Before:

```text
GPU submission
```

it checks:

```text
GPU capability
GPU budget
```

Before:

```text
I/O operation
```

it checks:

```text
I/O capability
resource budget
```

---

# 79. Platform Mapping — Windows

Primary mechanisms:

```text
CreateThread
Threadpool APIs where appropriate
Waitable objects
IOCP
native synchronization
thread affinity APIs
priority APIs
```

Axiom should prefer native facilities where they provide better integration.

---

# 80. Platform Mapping — Linux

Possible mechanisms:

```text
pthread
futex
epoll
io_uring
eventfd
timerfd
sched APIs
CPU affinity
cgroup integration
```

The runtime must gracefully fall back when optional kernel facilities are unavailable.

---

# 81. Platform Mapping — macOS

Use:

```text
pthread
Grand Central Dispatch integration where useful
kqueue
mach/native synchronization where required
native QoS
```

The abstraction must remain Axiom-owned.

---

# 82. Android

Android imposes application lifecycle and background-execution restrictions.

Axiom therefore maps:

```text
Executor
Worker
Task
```

onto Android-supported execution facilities.

The runtime must not assume unrestricted background threads.

---

# 83. iOS

The runtime must respect:

- application lifecycle;
- background execution restrictions;
- system scheduling;
- energy constraints.

The Axiom scheduler may reduce or suspend execution according to platform lifecycle signals.

---

# 84. WASM

WASM execution depends on host capabilities.

Possible model:

```text
Axiom Task
 ↓
WASM state machine
 ↓
host async event
 ↓
resume
```

If threads are unavailable:

```text
single-thread executor
```

remains valid.

---

# 85. Embedded

Axiom supports a reduced execution profile:

```text
single worker
static task storage
static queues
no dynamic thread creation
```

This permits the same execution model on constrained systems.

---

# 86. Single-Thread Executor

A single-thread executor is a first-class configuration.

```text
Executor
 └── Worker 0
```

This is useful for:

- embedded;
- WASM;
- deterministic tests;
- GUI event loops.

Async still works because tasks can suspend/resume cooperatively.

---

# 87. GUI Integration

GUI applications may use:

```text
GuiExecutor
```

with:

```text
UI thread
```

as a special executor.

Background tasks can submit:

```axiom
ui.post(...)
```

No background worker may directly manipulate UI state unless the platform explicitly permits it.

---

# 88. External Event Loops

Axiom allows integration with external event loops through:

```axiom trait EventSource {
    function poll(...)
    function wake(...)
}
```

Examples:

```text
GUI loop
embedded loop
host application loop
foreign runtime loop
```

---

# 89. FFI Threads

Foreign code may create threads outside the Axiom runtime.

Such threads must attach explicitly:

```axiom
Thread.attach_external()
```

Attachment establishes:

- diagnostics context;
- resource accounting where possible;
- TLS;
- capability context;
- runtime registration.

---

# 90. Foreign Async Runtime

Axiom does not assume that a foreign async runtime can directly resume Axiom state machines.

Adapters must explicitly bridge:

```text
ForeignFuture
 ↕
AxiomFuture
```

---

# 91. ABI

The stable native ABI for async boundaries must not expose implementation-specific scheduler structures.

FFI should use:

```text
opaque handles
callbacks
explicit completion objects
```

rather than requiring foreign code to understand Axiom task frames.

---

# 92. Compiler IR

The compiler introduces execution-related IR operations:

```text
task.spawn
task.await
task.cancel
task.detach
task.yield

executor.submit
executor.shutdown

io.submit
io.await

timer.await
sync.wait
sync.signal
```

---

# 93. Async Lowering

Input:

```axiom
async function foo() {
    let a = await read()
    return transform(a)
}
```

Compiler pipeline:

```text
AST
 ↓
Semantic async analysis
 ↓
Coroutine/state-machine transformation
 ↓
Axiom IR
 ↓
native lowering
```

The state machine contains only variables live across suspension points.

---

# 94. Frame Optimization

The compiler should:

- eliminate dead locals;
- split state frames;
- avoid storing values that do not cross suspension;
- use stack storage when provably safe;
- inline trivial futures;
- eliminate unnecessary task allocation.

---

# 95. Async Fusion

When:

```axiom
await foo()
```

is immediately awaited by the caller, the compiler may fuse state machines.

Goal:

```text
fewer allocations
fewer scheduler transitions
fewer continuation objects
```

This is an optimization, not a semantic requirement.

---

# 96. Synchronous Fast Path

If an async operation completes immediately:

```text
submit
 ↓
Ready
```

the runtime should continue synchronously without:

```text
queue
→ worker
→ dequeue
```

unless scheduling semantics require a yield.

This is critical for low-latency async code.

---

# 97. Task Allocation Fast Path

Task frames should preferably come from:

```text
worker-local allocator
```

or:

```text
executor arena
```

where lifetime permits.

Cross-thread freeing must remain safe.

---

# 98. No Hidden GC Requirement

Task-frame lifetime is governed by:

```text
ownership
join handle
parent scope
executor ownership
reference counts only where explicitly required
```

No tracing garbage collector is required.

---

# 99. Task Handle Safety

Handles use:

```text
index + generation
```

rather than raw pointers exposed to application code.

Stale handles produce:

```text
InvalidHandle
```

rather than undefined access.

---

# 100. Memory Visibility

Scheduler queues, task states and synchronization primitives must establish the required memory-ordering semantics.

For example:

```text
producer writes task data
Release
    ↓
queue publication
    ↓
Acquire
    ↓
consumer reads task data
```

The compiler must not reorder operations across defined synchronization boundaries.

---

# 101. Deterministic Executor

Testing requires:

```axiom DeterministicExecutor
```

Features:

- single logical scheduler;
- deterministic task IDs;
- deterministic queue order;
- deterministic timer clock;
- controlled task interleaving;
- explicit scheduling points.

This allows reproducible concurrency tests.

---

# 102. Virtual Clock

The deterministic executor provides:

```axiom clock.advance(10ms)
```

Timers should fire without waiting for real time.

This eliminates slow timing-based tests.

---

# 103. Fault Injection

The scheduler must support controlled faults:

```text
worker creation failure
queue full
thread quota exceeded
CPU budget exhausted
I/O completion failure
timer failure
task cancellation
worker crash
executor shutdown
```

---

# 104. Testing Model

Required test classes:

### Unit tests

Each scheduler component independently.

### Stress tests

Millions of task submissions.

### Race tests

Concurrent submission/stealing/cancellation.

### Fuzz tests

Random task state transitions.

### Model tests

Small deterministic scheduling state spaces.

### Performance tests

Task creation, await, wakeup, queue operations.

---

# 105. Required Stress Scenarios

At minimum:

```text
1M task submissions
100K suspended tasks
mass cancellation
worker churn
executor restart
queue saturation
blocking-pool saturation
timer storm
I/O completion storm
priority inversion
nested task trees
deep structured concurrency
```

Exact maximum values remain platform-dependent.

---

# 106. Cancellation Race Tests

Test:

```text
cancel before spawn
cancel during queueing
cancel while running
cancel during await
cancel simultaneously with completion
cancel after completion
parent cancellation during child creation
```

The resulting state must always be valid.

---

# 107. Completion Race

If:

```text
I/O completion
```

and:

```text
cancellation
```

occur simultaneously, exactly one terminal state wins.

The losing event becomes an ignored/stale event.

No double-resume is permitted.

---

# 108. Double Resume Prevention

Every async frame has an execution-state guard.

Invariant:

```text
one continuation
→ at most one active execution
```

Concurrent completion notifications must be coalesced or rejected.

---

# 109. Executor Shutdown Race

Test:

```text
spawn
cancel
shutdown
completion
```

in every meaningful ordering.

No task may:

```text
resume after executor destruction
```

---

# 110. Queue Capacity

Every queue has explicit capacity semantics.

A queue cannot silently grow without BOOTSTRAP-606 accounting.

When capacity is reached:

```text
reject
wait
spill to governed storage
```

according to queue policy.

---

# 111. Admission Control

Before accepting work:

```text
Executor
 ↓
ResourceGovernor
 ↓
quota check
 ↓
queue admission
```

This prevents resource exhaustion from occurring after work has already been accepted.

---

# 112. Scheduling Domains

Axiom supports independent scheduling domains:

```text
CPU
Blocking
I/O
GPU
GUI
```

Each has different execution characteristics.

A task may transition between domains explicitly.

---

# 113. Domain Transition

Example:

```axiom
await blocking {
    read_legacy_file()
}
```

means:

```text
CPU/async task
 ↓
Blocking domain
 ↓
completion
 ↓
CPU/async domain
```

---

# 114. Work Classification

Tasks may declare:

```text
CPU
IO
Blocking
GPU
Mixed
```

The compiler/runtime may infer this for built-in operations.

Explicit classification overrides inference.

---

# 115. Misclassification Protection

If a supposedly async task blocks repeatedly, diagnostics should report:

```text
possible blocking operation on async worker
```

The runtime may optionally migrate the operation only when safe.

It must not transparently move arbitrary code between threads because thread affinity/TLS may matter.

---

# 116. Thread Affinity

Tasks may request:

```text
AnyWorker
SameWorker
SpecificWorker
SpecificThread
UIThread
CpuSet
```

These are explicit scheduling constraints.

---

# 117. Affinity Restrictions

Affinity is subordinate to:

```text
Security policy
Resource limits
Platform restrictions
Executor availability
```

A request for an unavailable CPU set must fail clearly.

---

# 118. Thread Naming

Thread names are diagnostic metadata.

Example:

```text
axiom.app.worker.03
axiom.app.io.01
axiom.app.blocking.02
```

Names should be deterministic where possible.

---

# 119. Worker Statistics

Each worker exposes:

```text
busy_time
idle_time
queue_depth
tasks_executed
tasks_stolen
tasks_submitted
park_count
wake_count
```

Metrics feed BOOTSTRAP-602.

---

# 120. Executor Statistics

```text
active_workers
queued_tasks
running_tasks
waiting_tasks
completed_tasks
failed_tasks
cancelled_tasks
average_queue_latency
average_task_runtime
```

Statistics are optional and may be compiled out.

---

# 121. Scheduler Tracing

When enabled:

```text
TASK_CREATE
TASK_QUEUE
TASK_START
TASK_YIELD
TASK_WAIT
TASK_WAKE
TASK_COMPLETE
TASK_FAIL
TASK_CANCEL
TASK_STEAL
WORKER_PARK
WORKER_WAKE
```

These become structured diagnostic events.

---

# 122. Binary Size

The runtime must be modular.

If an application only uses:

```text
synchronous threads
```

then unused:

```text
async reactor
timer wheel
GPU executor
```

should be removable by linker dead stripping.

---

# 123. Minimal Runtime Profile

For tiny native programs:

```text
Axiom Minimal Runtime
 ├── thread
 ├── basic synchronization
 └── scheduler
```

No:

```text
IPC
network
GPU
full diagnostics
full async reactor
```

unless referenced.

---

# 124. Full Runtime Profile

Server/desktop applications may enable:

```text
threads
async
I/O
timers
IPC
GPU
diagnostics
resource governor
supervision
```

---

# 125. Runtime Initialization

Startup order:

```text
Security
 ↓
Configuration
 ↓
Resource Governor
 ↓
Diagnostics
 ↓
Timer
 ↓
I/O Reactor
 ↓
Executors
 ↓
Workers
 ↓
Application
```

---

# 126. Runtime Shutdown

Reverse dependency order:

```text
Application
 ↓
Executors drain
 ↓
I/O reactor
 ↓
Timer
 ↓
Diagnostics flush
 ↓
Resource Governor
 ↓
Runtime
```

---

# 127. Error Model

Scheduler APIs return:

```text
SpawnError
QueueFull
ResourceDenied
ThreadLimit
ExecutorStopped
Cancelled
DeadlineExceeded
IoError
InvalidHandle
```

Task failures are separate from executor infrastructure errors.

---

# 128. Panic/Exception Boundary

If Axiom supports panic/unrecoverable failure:

```text
task panic
 ↓
task boundary
 ↓
JoinHandle receives failure
```

A panic must not corrupt executor scheduler state.

Runtime scheduler internals must use carefully constrained failure handling.

---

# 129. Service-Level Failure

An uncaught failure in a service's main task may trigger:

```text
BOOTSTRAP-605 service failure
```

The supervisor then applies its configured recovery policy.

The executor itself does not decide whether a process should restart.

---

# 130. Security Boundary

Scheduling is divided into:

```text
ordinary scheduling hints
```

and:

```text
privileged scheduling operations
```

The former may be freely requested.

The latter require capabilities.

---

# 131. Capability Examples

```axiom
ThreadCapability
PriorityCapability
AffinityCapability
RealtimeSchedulingCapability
HighResolutionTimerCapability
```

Capability checks happen at privileged operation boundaries.

---

# 132. Realtime Scheduling

Realtime priority is not part of ordinary task priority.

It requires:

```text
RealtimeSchedulingCapability
```

and platform support.

The application must also satisfy resource constraints.

---

# 133. High-Resolution Timers

High-resolution timers may consume additional OS resources and energy.

They therefore integrate with:

```text
TimerCapability
ResourceGovernor
```

Applications cannot assume nanosecond-resolution behavior.

---

# 134. Energy Awareness

On mobile platforms, scheduler policy may incorporate:

```text
foreground/background state
power mode
thermal state
```

provided by the platform adapter.

Correctness must not depend on these signals.

---

# 135. Backpressure Across Layers

Axiom enforces:

```text
Producer
 ↓
Task Queue
 ↓
Executor
 ↓
I/O
 ↓
IPC
 ↓
Shared Memory
```

Every stage may apply bounded admission.

This prevents one queue from shifting unlimited pressure to another subsystem.

---

# 136. Unified Cancellation Tree

Cancellation follows:

```text
Application
   ↓
Service
   ↓
Executor
   ↓
Parent Task
   ↓
Child Task
   ↓
I/O Operation
```

Cancellation may propagate downward.

It must not implicitly propagate upward unless the structured-concurrency failure policy specifies it.

---

# 137. Error vs Cancellation

These are distinct:

```text
Failed
Cancelled
DeadlineExceeded
```

A cancellation request is not automatically an application error.

---

# 138. Timeout Semantics

A timeout is represented as:

```text
DeadlineExceeded
```

and may optionally trigger cancellation.

The API must make this distinction explicit.

---

# 139. Task Groups

Axiom provides:

```axiom
TaskGroup
```

for structured concurrency.

Example:

```axiom
async function process() {
    let group = task_group()

    group.spawn(load_a())
    group.spawn(load_b())
    group.spawn(load_c())

    await group.join()
}
```

Default behavior:

```text
one child fails
→ cancel remaining children
→ wait for them
→ return failure
```

---

# 140. Supervised Task Groups

Higher-level services may use:

```text
supervised task group
```

where child failures are reported without automatically terminating siblings.

This belongs above the primitive executor but uses the same task model.

---

# 141. Executor Composition

Executors can be composed:

```text
Application Executor
 ├── CPU
 ├── Async I/O
 ├── Blocking
 └── GPU
```

Each executor can have its own resource group while inheriting application-level limits.

---

# 142. Hierarchical Resource Scheduling

Example:

```text
Application
  quota: 8 CPU cores
      │
      ├── Service A: 4
      │    ├── CPU executor
      │    └── blocking executor
      │
      └── Service B: 4
           └── CPU executor
```

BOOTSTRAP-606 arbitrates the actual resource allocation.

---

# 143. Fairness Between Services

The scheduler must not let one service consume all shared executor resources when separate resource groups exist.

Policies may include:

```text
weighted fair scheduling
quota-based scheduling
priority-aware scheduling
```

The selected policy is configuration, not a language semantic requirement.

---

# 144. Fairness Between Tasks

Within one group, the executor uses bounded fairness.

Long-running CPU work should periodically yield.

I/O-bound tasks should not be delayed behind a large CPU queue when sufficient workers exist.

---

# 145. Scheduler Policy Interface

```axiom
trait SchedulerPolicy {
    function select_next(...)
    function on_submit(...)
    function on_complete(...)
    function on_worker_idle(...)
}
```

The default policy remains work-stealing.

---

# 146. Custom Scheduler

Custom policies are allowed but must not bypass:

```text
Security
ResourceGovernor
Cancellation
Executor lifecycle
```

A custom scheduler cannot create unrestricted workers.

---

# 147. Runtime Invariants

### INV-1

No task executes concurrently on two workers unless explicitly designed as parallel work.

### INV-2

A completed task cannot resume.

### INV-3

A cancelled task cannot resume after terminal cancellation.

### INV-4

An executor cannot accept work after entering stopped state.

### INV-5

No worker exceeds its resource-group thread limit.

### INV-6

No queue bypasses resource accounting.

### INV-7

A detached task has explicit ownership.

### INV-8

No arbitrary thread is asynchronously killed.

### INV-9

Every task completion is observed at most once.

### INV-10

A stale task handle cannot access a recycled task.

### INV-11

I/O completion cannot double-resume a task.

### INV-12

Shutdown eventually reaches a terminal state unless the OS itself prevents progress.

---

# 148. Performance Targets

The implementation should target:

```text
OS thread creation:
    native-equivalent overhead

task creation:
    O(1) amortized

local task submission:
    O(1)

local task pop:
    O(1)

work stealing:
    O(1) amortized

timer insertion:
    O(1) amortized for wheel implementation

task wakeup:
    O(1) amortized

scheduler contention:
    independent of total task count in the common local-queue case
```

Exact numerical benchmarks are platform-specific and belong to implementation validation.

---

# 149. Hot-Path Rules

The scheduler hot path must avoid:

```text
global mutex
system call per task
heap allocation per await
logging per task
capability lookup through complex maps
```

unless explicitly required.

---

# 150. Cache Locality

Prefer:

```text
worker-local queue
worker-local allocator
worker-local scheduler state
```

before shared global structures.

---

# 151. False Sharing

Scheduler structures must use cache-line-aware layout where beneficial.

Frequently modified worker state should not unnecessarily share cache lines.

---

# 152. Memory Reclamation

Scheduler nodes use:

```text
ownership
generation handles
epoch/hazard mechanisms
or deferred worker-local reclamation
```

as appropriate.

No tracing GC is required.

---

# 153. Async Frame Reclamation

A frame is destroyed only after:

```text
task terminal state
+
no outstanding join/operation ownership
```

Foreign I/O completions must hold explicit references to the frame/resource state they may resume.

---

# 154. Stale Completion Protection

Each asynchronous operation receives:

```text
OperationId
Generation
```

A completion for an obsolete operation is ignored.

This prevents:

```text
cancel
reuse memory
old completion
→ resume new task
```

---

# 155. I/O Cancellation

If the OS supports cancellation:

```text
cancel OS operation
```

If not:

```text
mark operation cancelled
ignore late completion
```

The runtime must never pretend cancellation is instantaneous when the platform cannot provide it.

---

# 156. Blocking FFI

Foreign calls that may block should use:

```axiom blocking { ... }
```

or an explicitly configured blocking function annotation.

Compiler metadata may mark known APIs:

```text
@blocking
```

---

# 157. Compiler Diagnostics

The compiler should warn when:

```text
blocking API
```

is called directly from an async context where the API is known to block.

Example:

```text
warning AX60701:
blocking operation inside async task
```

The warning should be suppressible when intentional.

---

# 158. Async Safety Metadata

Functions can carry:

```text
@async_safe
@blocking
@cpu_bound
@io_bound
```

These are metadata hints.

They must not replace actual runtime resource enforcement.

---

# 159. API Surface

Minimal public primitives:

```axiom
Executor
Worker
Task
TaskGroup
JoinHandle
CancelSource
CancelToken
Timer
IoReactor
Channel
Mutex
Semaphore
Thread
```

---

# 160. Example — Basic Parallel Tasks

```axiom
async function main() {
    let a = spawn compute_a()
    let b = spawn compute_b()

    let x = await a
    let y = await b

    return x + y
}
```

The compiler and scheduler may execute `a` and `b` concurrently.

---

# 161. Example — Blocking Isolation

```axiom
async function load_config() -> Config {
    return await blocking {
        legacy_read_config()
    }
}
```

The blocking call uses the blocking executor.

---

# 162. Example — Cancellation

```axiom
async function worker(token: CancelToken) {
    while !token.is_cancelled() {
        let item = await queue.receive(token)
        process(item)
    }
}
```

---

# 163. Example — Deadline

```axiom
let result =
    await fetch()
    with deadline = now() + 2s
```

---

# 164. Example — Task Group

```axiom
async function download_all() {
    let group = task_group()

    group.spawn(download(a))
    group.spawn(download(b))
    group.spawn(download(c))

    await group.join()
}
```

---

# 165. Example — Explicit Thread

```axiom
let thread = Thread.spawn(worker_function)

thread.join()
```

This bypasses lightweight task scheduling when direct OS-thread semantics are required.

---

# 166. Example — Affinity

```axiom
let worker = Thread.spawn(
    options = ThreadOptions {
        affinity: CpuSet.single(3)
    },
    function = realtime_worker
)
```

The request remains subject to capabilities and resource policy.

---

# 167. Example — Channel

```axiom
let channel = Channel<int>.bounded(1024)

spawn producer(channel)
spawn consumer(channel)
```

The channel's memory usage is charged to its resource group.

---

# 168. Compiler Responsibilities

The compiler must:

1. recognize async functions;
2. construct state machines;
3. determine live values across suspension;
4. lower `await`;
5. emit scheduler metadata;
6. validate async/blocking boundaries;
7. preserve memory-order semantics;
8. emit task/resource metadata;
9. eliminate unused runtime features.

---

# 169. Runtime Responsibilities

The runtime must:

1. schedule tasks;
2. manage workers;
3. manage executors;
4. handle timers;
5. integrate I/O;
6. manage cancellation;
7. enforce executor resource limits;
8. coordinate shutdown;
9. expose diagnostics;
10. preserve task/frame lifetime correctness.

---

# 170. Linker Responsibilities

The linker may:

```text
detect async usage
detect timer usage
detect I/O usage
detect blocking pool usage
detect GPU executor usage
```

and retain only required runtime modules.

---

# 171. Generated Metadata

A compiled module may contain:

```text
AXEXEC {
    async_functions
    blocking_functions
    scheduler_requirements
    thread_requirements
    resource_requirements
    capability_requirements
}
```

This metadata is machine-readable and AI-readable.

---

# 172. Static Validation

The compiler/linker should reject impossible deployment requirements such as:

```text
requires 16 workers
platform profile max = 4
```

when the requirement is declared as hard.

---

# 173. Runtime Validation

Runtime validates:

```text
actual platform
available CPU
resource quotas
capabilities
executor configuration
```

before creating workers.

---

# 174. Configuration Example

```text
executor:
    cpu:
        workers: auto
        max_tasks: 100000
        policy: work_stealing

    blocking:
        min_workers: 1
        max_workers: 32

    timer:
        resolution: 1ms
```

The exact serialized format is governed by BOOTSTRAP-601.

---

# 175. Observability Example

A diagnostic record may contain:

```text
task_id=18291
parent=18280
executor=cpu
worker=3
queue_wait=42us
run_time=81us
await_time=4.2ms
state=completed
resource_group=service.api
```

No secret values should be emitted.

---

# 176. Debugger Integration

Debugger support should expose:

```text
threads
workers
tasks
task states
await locations
executor queues
locks
channels
resource groups
```

This should not require modifying program semantics.

---

# 177. Task Backtrace

For suspended tasks, diagnostics should show:

```text
Task 18291
    suspended at:
        foo.ax:82
        await socket.receive()
```

The compiler emits async source-location metadata.

---

# 178. Crash Backtrace

A native worker crash still uses the native stack mechanism of BOOTSTRAP-602.

Async metadata can reconstruct logical task context around the native stack.

---

# 179. Reproducibility

Deterministic mode should support:

```text
same program
same seed
same virtual clock
same task submission order
→ same scheduler decision sequence
```

This is primarily for tests and debugging.

Production work stealing remains free to optimize scheduling.

---

# 180. Formal State Model

Executor:

```text
ExecutorState =
    Created
    Starting
    Running
    Draining
    Stopped
    Failed
```

Worker:

```text
WorkerState =
    Starting
    Running
    Parking
    Parked
    Stopping
    Stopped
```

Task:

```text
TaskState =
    Created
    Queued
    Running
    Waiting
    Sleeping
    Completed
    Failed
    Cancelled
    Detached
```

---

# 181. State Transition Validation

Every transition is checked against the legal transition table.

Illegal transitions become internal runtime errors.

Example:

```text
Completed → Running
```

is invalid.

---

# 182. Generation Safety

Objects reused from pools must increment generation:

```text
Task 10 generation 3
```

after destruction:

```text
Task 10 generation 4
```

A handle to generation 3 becomes invalid.

---

# 183. Resource Cleanup

Terminal task cleanup order:

```text
cancel pending operations
 ↓
release task-local resources
 ↓
release task frame
 ↓
release task handle state
 ↓
return scheduler resources
```

Foreign operations must not retain destroyed state.

---

# 184. Failure Isolation

A task failure must not corrupt:

```text
worker queue
executor state
timer subsystem
I/O reactor
resource accounting
```

A worker may continue after an ordinary task failure.

---

# 185. Worker Failure

A genuine worker/runtime failure triggers:

```text
diagnostics
 ↓
worker isolation
 ↓
executor health evaluation
 ↓
BOOTSTRAP-605 notification
```

The process may be terminated if runtime invariants are compromised.

---

# 186. Resource Pressure

When BOOTSTRAP-606 reports:

```text
Normal
Warning
High
Critical
Emergency
```

the scheduler can progressively:

```text
reduce worker creation
reject detached tasks
delay background tasks
throttle CPU work
cancel optional work
```

It must not silently cancel critical application work unless policy explicitly permits it.

---

# 187. Background Priority

Background tasks are suitable for:

```text
cache cleanup
prefetch
analytics
maintenance
```

They should yield to foreground/normal workloads under pressure.

---

# 188. Admission Under Pressure

The scheduler may reject:

```text
new detached background tasks
```

while continuing already accepted critical tasks.

This policy is configured at the service/resource level.

---

# 189. No Hidden Thread Creation

Calling:

```axiom
spawn(...)
```

must not unexpectedly create one OS thread per task.

The default meaning is:

```text
submit lightweight task to executor
```

Explicit:

```axiom
Thread.spawn(...)
```

creates an OS thread.

---

# 190. Async Semantic Guarantee

`await` means:

> suspend the logical task until the awaited operation reaches a completion state.

It does **not** mean:

> create another thread.

---

# 191. Parallelism Semantic Guarantee

`spawn` means concurrent schedulability.

Actual simultaneous execution depends on:

```text
worker count
CPU availability
resource limits
OS scheduling
```

---

# 192. Structured Concurrency Guarantee

For a structured task group:

```text
scope exit
```

implies:

```text
all child tasks completed or were cancelled and joined
```

---

# 193. Executor API Contract

Minimum:

```axiom
function Executor.create(options) -> Result<Executor>
function Executor.spawn(fn) -> Result<JoinHandle>
function Executor.spawn_detached(fn) -> Result<TaskHandle>
function Executor.shutdown(mode) -> Result
function Executor.stats() -> ExecutorStats
```

---

# 194. Thread API Contract

Minimum:

```axiom
function Thread.spawn(fn, options) -> Result<Thread>
function Thread.join() -> Result
function Thread.detach() -> Result
function Thread.current() -> ThreadKey
```

---

# 195. Cancellation API Contract

```axiom
function CancelSource.create() -> CancelSource
function CancelSource.cancel()
function CancelSource.token() -> CancelToken

function CancelToken.is_cancelled() -> bool
function CancelToken.throw_if_cancelled() -> Result
```

---

# 196. Timer API Contract

```axiom
function sleep(duration) -> AsyncResult
function sleep_until(deadline) -> AsyncResult
function timer.after(duration) -> Timer
function Timer.cancel()
```

---

# 197. I/O API Contract

```axiom
function IoReactor.submit(operation) -> IoHandle
function IoHandle.await() -> Result
function IoHandle.cancel()
```

---

# 198. Acceptance Criteria

BOOTSTRAP-607 is complete only if:

1. OS threads have stable generation-safe identities.
2. Thread lifecycle is explicitly modeled.
3. Lightweight tasks are distinct from threads.
4. Tasks have generation-safe identities.
5. Task state transitions are validated.
6. Structured concurrency exists.
7. Detached tasks are explicit.
8. Child failure propagation is defined.
9. Executor lifecycle is defined.
10. Worker lifecycle is defined.
11. Per-worker task queues exist.
12. Work stealing is defined.
13. Global submission is defined.
14. Worker parking/wakeup is defined.
15. Fairness is defined.
16. Priority semantics are defined.
17. Priority cannot bypass security/resource limits.
18. CPU resource accounting integrates with 606.
19. Thread quotas integrate with 606.
20. Task quotas integrate with 606.
21. Async functions lower to state machines.
22. Suspension does not require native-stack preservation.
23. Async allocation optimization is defined.
24. Synchronous async fast paths are defined.
25. Cancellation is explicit.
26. Cancellation propagation is defined.
27. Cancellation races are defined.
28. Deadlines are defined.
29. Centralized timer management is defined.
30. I/O reactor abstraction supports reactor/proactor systems.
31. Windows backend is defined.
32. Linux backend is defined.
33. macOS backend is defined.
34. Android/iOS constraints are represented.
35. WASM execution is supported.
36. Blocking work has a separate executor.
37. Blocking worker growth is resource-governed.
38. Task-local context is distinct from TLS.
39. IPC integration is defined.
40. GPU execution is separated from CPU scheduling.
41. GUI-thread integration is defined.
42. FFI thread attachment is defined.
43. Executor shutdown/draining is defined.
44. Supervisor integration is defined.
45. Diagnostics integration is defined.
46. Deterministic scheduling exists for tests.
47. Fault injection exists.
48. Stale completion/double resume is prevented.
49. Runtime components can be dead-stripped.
50. No mandatory GC is introduced.
51. No mandatory borrow-checker dependency is introduced.
52. Raw pointer semantics are not required by the scheduler API.
53. Resource capability checks are integrated.
54. Scheduler hot paths avoid mandatory global locking.
55. The architecture can run with a single worker.
56. The architecture can scale to multiple workers.
57. Resource pressure can throttle admission.
58. Scheduler state cannot outlive executor ownership.
59. Async frames cannot be destroyed while an operation can resume them.
60. The architecture is implementable without a third-party runtime.

---

# 199. Final Architecture

```text
                    ┌─────────────────────────┐
                    │   Axiom Application     │
                    └────────────┬────────────┘
                                 │
                         Structured Tasks
                                 │
                    ┌────────────▼────────────┐
                    │       Executors          │
                    ├─────────────────────────┤
                    │ CPU                      │
                    │ Async / I/O              │
                    │ Blocking                 │
                    │ GPU                      │
                    │ GUI                      │
                    │ Deterministic            │
                    └────────────┬────────────┘
                                 │
                     ┌───────────▼───────────┐
                     │      Scheduler         │
                     │ work stealing          │
                     │ fairness               │
                     │ priority               │
                     │ admission              │
                     └───────────┬───────────┘
                                 │
                    ┌────────────▼────────────┐
                    │         Workers          │
                    │ local queues             │
                    │ parking/wakeup           │
                    └────────────┬────────────┘
                                 │
                           Native Threads
                                 │
              ┌──────────────────┼──────────────────┐
              ▼                  ▼                  ▼
           OS CPU            I/O Reactor          GPU
              │                  │                  │
              └──────────────────┼──────────────────┘
                                 │
        ┌────────────────────────┼────────────────────────┐
        │                        │                        │
   BOOTSTRAP-606          BOOTSTRAP-603          BOOTSTRAP-604
 Resource Governor          Security              IPC/Shared Mem
        │                        │                        │
        └────────────────────────┼────────────────────────┘
                                 │
                         BOOTSTRAP-605
                      Process/Service Supervisor
                                 │
                         BOOTSTRAP-602
                    Diagnostics/Observability
                                 │
                         BOOTSTRAP-601
                   Configuration/Deployment
                                 │
                         BOOTSTRAP-600
                    State/Checkpoint/Recovery
```

---

# 200. Architectural Conclusion

BOOTSTRAP-607 establishes the execution foundation of Axiom without forcing a single concurrency style.

The intended model is:

```text
OS Thread
    = expensive, explicit native execution resource

Task
    = cheap logical unit of execution

async/await
    = compiler-generated state machine

Executor
    = scheduler + workers

I/O
    = event/completion-driven

Blocking
    = isolated execution domain

Cancellation
    = explicit + cooperative

Resource control
    = BOOTSTRAP-606

Security
    = BOOTSTRAP-603

Lifecycle
    = BOOTSTRAP-605
```

The critical architectural decision is that **Axiom does not make threads and async competing language models**.

Instead:

```text
Thread
  ↓
Worker
  ↓
Executor
  ↓
Task
  ↓
async state machine
```

forms one unified execution hierarchy.

This preserves the ability to write low-level native threaded code while making high-concurrency applications possible without one OS thread per operation.

**BOOTSTRAP-607: COMPLETED.**

---

# Next Architecture Task

**BOOTSTRAP-608 — Native Synchronization, Atomics, Channels, Lock-Free Structures & Concurrency Memory Semantics 5.0**

Scope:

```text
Atomics
Memory Ordering
Mutex
RWLock
Semaphore
Event
Condition Variable
Barrier
Latch
Channels
Wait Sets
Lock-Free Structures
Wait-Free Operations
Spin Locks
Futex/OS Wait Primitives
Priority Inheritance
Deadlock Detection
ABA Protection
Hazard/Epoch Reclamation
Concurrency Diagnostics
Deterministic Concurrency Testing
```

This task will formalize the low-level synchronization layer that BOOTSTRAP-607 consumes, including the exact memory-ordering and lock-free rules needed for a compiler implementation.
:::

Đã hoàn tất **BOOTSTRAP-607**. Chuỗi kiến trúc tiếp tục sang **BOOTSTRAP-608** như đã xác định ở cuối spec.