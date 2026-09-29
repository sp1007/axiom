Tiếp tục với **BOOTSTRAP-607**, lần này tách rõ scheduling khỏi resource governance: 606 quyết định *được phép dùng bao nhiêu*, còn 607 quyết định *công việc nào chạy ở đâu, khi nào và bằng cơ chế nào*.

:::writing{variant="document" id="74162" title="BOOTSTRAP-607 — Native Application Scheduling, Threading, Async Runtime, Executors & Work-Stealing Runtime 5.0"}

# BOOTSTRAP-607
## Native Application Scheduling, Threading, Async Runtime, Executors & Work-Stealing Runtime 5.0

**Status:** Architecture Specification  
**Phase:** Native Runtime / Execution Model  
**Depends on:** BOOTSTRAP-600 → 606

---

# 607.0 — Purpose

BOOTSTRAP-607 defines the Axiom execution and scheduling runtime.

Its responsibility is to transform executable work into actual CPU/GPU execution while respecting:

- resource limits from BOOTSTRAP-606;
- security boundaries from BOOTSTRAP-603;
- service lifecycle from BOOTSTRAP-605;
- IPC from BOOTSTRAP-604;
- configuration from BOOTSTRAP-601;
- diagnostics from BOOTSTRAP-602;
- application state/recovery from BOOTSTRAP-600.

The central separation is:

```text
BOOTSTRAP-606
Resource Governance
        │
        │ "How much?"
        ▼
BOOTSTRAP-607
Scheduling / Execution
        │
        │ "When / where / how?"
        ▼
CPU / OS / GPU
```

---

# 607.1 — Design Goals

Axiom scheduling shall provide:

1. very low scheduling overhead;
2. native OS thread execution;
3. lightweight Axiom tasks;
4. async I/O;
5. work stealing;
6. structured concurrency;
7. cancellation;
8. deadlines;
9. CPU affinity;
10. priority;
11. bounded queues;
12. backpressure;
13. blocking-operation isolation;
14. deterministic shutdown;
15. resource-governor integration;
16. optional real-time scheduling;
17. NUMA awareness;
18. GPU work submission;
19. minimal runtime overhead;
20. no mandatory garbage collector.

---

# 607.2 — Execution Hierarchy

Axiom shall distinguish four levels:

```text
Application
    │
    ▼
Executor
    │
    ▼
Task
    │
    ▼
Execution Context
    │
    ▼
OS Thread
```

GPU introduces another execution domain:

```text
Task
  │
  ├── CPU Executor → CPU Thread
  │
  └── GPU Executor → GPU Queue
```

---

# 607.3 — OS Thread

An OS thread is a platform execution resource.

It has:

```text
ThreadId
Generation
Stack
CPU affinity
Scheduling priority
Resource scope
Execution context
```

Axiom shall not expose platform-specific thread internals in ordinary code.

---

# 607.4 — Axiom Task

A task is the primary unit of logical work.

A task is substantially cheaper than an OS thread.

Conceptually:

```text
Task {
    id
    generation
    state
    priority
    executor
    parent
    resource_scope
    cancellation
    deadline
}
```

---

# 607.5 — Task States

Canonical states:

```text
Created
Queued
Running
Waiting
Sleeping
Blocked
Completed
Failed
Cancelled
```

Transitions:

```text
Created
   ↓
Queued
   ↓
Running
   ├──→ Completed
   ├──→ Failed
   ├──→ Cancelled
   ├──→ Waiting
   ├──→ Sleeping
   └──→ Blocked
```

---

# 607.6 — Task Identity

Task identity:

```text
(TaskId, Generation)
```

Generation prevents stale task handles from referencing a newly reused task slot.

---

# 607.7 — Task Handle

Public task references shall be opaque.

```text
TaskHandle<T>
```

A handle contains no exposed pointer.

Invalid handles produce:

```text
InvalidTaskHandle
```

---

# 607.8 — Executor

An executor owns execution capacity.

```text
Executor {
    id
    policy
    workers
    queues
    resource_scope
}
```

Executors may be:

```text
CpuExecutor
IoExecutor
BlockingExecutor
GpuExecutor
RealtimeExecutor
```

---

# 607.9 — Executor Responsibilities

An executor manages:

- runnable tasks;
- worker threads;
- task queues;
- stealing;
- wakeups;
- task admission;
- shutdown;
- scheduling policy.

The executor does **not** own application business logic.

---

# 607.10 — Default CPU Executor

Every native Axiom application may have a default CPU executor.

Default worker count:

```text
available_cpu_capacity
```

as reported by BOOTSTRAP-606 and the platform.

It shall not blindly create one worker per logical CPU if resource policy prohibits that.

---

# 607.11 — Worker

A worker is an execution loop associated with an executor.

Conceptually:

```text
worker_loop():
    while executor.running:
        task = acquire_local()
        if none:
            task = steal()
        if none:
            wait_for_work()

        execute(task)
```

---

# 607.12 — Local Worker Queue

Each worker should have a local deque.

Typical behavior:

```text
owner:
    push/pop bottom

thieves:
    steal top
```

This minimizes contention.

---

# 607.13 — Work Stealing

When a worker becomes idle:

```text
Worker A
    queue empty
       ↓
Worker B
    queue has work
       ↓
A steals work from B
```

Work stealing shall be bounded and resource-aware.

---

# 607.14 — Why Work Stealing

Work stealing is preferred for general parallel workloads because:

- local scheduling is cheap;
- independent tasks naturally distribute;
- contention is reduced;
- load imbalance can be corrected dynamically.

The implementation shall remain replaceable.

---

# 607.15 — Global Injection Queue

External producers need a safe way to submit tasks.

Axiom shall provide an injection queue:

```text
external producer
       ↓
global injection queue
       ↓
worker
       ↓
local queue
```

The queue must be bounded or governed by BOOTSTRAP-606.

---

# 607.16 — Queue Capacity

Every executor queue shall have a resource limit.

Example:

```text
tasks.max = 100000
queue_bytes.max = 64 MiB
```

An unbounded task queue is forbidden in the core runtime.

---

# 607.17 — Queue Overflow

Possible policies:

```text
Reject
Block
Await
ExecuteInline
Drop
Escalate
```

For normal application tasks:

```text
Reject / Await
```

should be preferred over silent dropping.

---

# 607.18 — Inline Execution

For latency-sensitive or already-saturated executors:

```text
submit()
```

may execute the task inline when explicitly permitted.

This avoids:

```text
enqueue
→ wake worker
→ context switch
→ execute
```

for tiny operations.

---

# 607.19 — Inline Execution Guard

Inline execution must not cause uncontrolled recursion.

The executor shall track:

```text
inline_depth
```

and fall back to queueing beyond a bounded depth.

---

# 607.20 — Task Cost Hint

Tasks may optionally declare:

```text
Tiny
Small
Normal
Large
Blocking
```

This is a scheduling hint.

The scheduler must not depend on the hint for correctness.

---

# 607.21 — Task Priority

Canonical priority levels:

```text
Critical
High
Normal
Low
Background
```

Priority affects scheduling order.

Priority does not grant:

- security capabilities;
- additional resource quota;
- unrestricted CPU;
- memory beyond policy.

---

# 607.22 — Priority and Resource Governor

The scheduler asks:

```text
Can this task run?
```

The governor answers:

```text
Is its resource usage permitted?
```

Therefore:

```text
Priority ≠ Resource Permission
```

---

# 607.23 — Fair Scheduling

Within the same priority class, scheduling should provide fairness.

The scheduler may use:

```text
FIFO
round-robin
weighted fair scheduling
aging
work stealing
```

depending on executor policy.

---

# 607.24 — Priority Aging

Low-priority tasks may gradually gain scheduling eligibility after waiting for a bounded period.

This reduces starvation.

Aging shall not exceed the priority policy's defined maximum.

---

# 607.25 — CPU Affinity

Executors may specify:

```text
allowed_cpus
preferred_cpus
```

Workers shall respect:

```text
security policy
resource policy
executor policy
platform topology
```

---

# 607.26 — Affinity Hierarchy

Effective affinity:

```text
platform
    ∩ deployment
    ∩ resource group
    ∩ executor
    ∩ task
```

An empty intersection is a configuration error.

---

# 607.27 — NUMA Awareness

On NUMA systems, executors may have locality domains:

```text
NumaDomain
```

Tasks may prefer:

```text
memory locality
CPU locality
GPU locality
```

The scheduler should avoid unnecessary migration across NUMA nodes.

---

# 607.28 — NUMA Policy

Possible policies:

```text
Local
Preferred
Interleave
Any
```

The default for latency-sensitive workloads should favor locality.

---

# 607.29 — CPU Cache Locality

The scheduler should prefer keeping a recently runnable task on its previous worker when practical.

This improves:

- cache locality;
- branch predictor locality;
- thread-local state locality.

Correctness must never depend on this behavior.

---

# 607.30 — Task Migration

Tasks may migrate between workers.

Migration should occur when:

```text
worker overloaded
worker idle
affinity changes
NUMA balancing required
executor policy changes
```

---

# 607.31 — Thread Pinning

A task may explicitly request:

```text
pinned_worker
```

but pinning is a scarce resource.

It must consume a resource reservation where appropriate.

---

# 607.32 — OS Thread Pool

Axiom shall not create unnecessary OS threads.

Default model:

```text
many Tasks
        ↓
small number of Workers
        ↓
OS Threads
```

---

# 607.33 — Thread Count Control

Thread creation must go through BOOTSTRAP-606.

Therefore:

```text
spawn worker
     ↓
ResourceGovernor.acquire(Thread)
```

If denied:

```text
executor remains at current capacity
```

rather than bypassing the quota.

---

# 607.34 — Dynamic Worker Scaling

Executors may dynamically scale worker count.

Signals:

```text
queue depth
CPU utilization
task wait time
resource pressure
I/O blocking
```

Scaling must respect:

```text
minimum_workers
maximum_workers
resource quota
```

---

# 607.35 — Worker Idle Timeout

Workers may terminate after being idle for:

```text
idle_timeout
```

except reserved workers.

---

# 607.36 — Reserved Workers

An executor may maintain a minimum worker reserve for latency-sensitive tasks.

Example:

```text
workers:
    minimum = 2
    maximum = 8
    reserved = 1
```

---

# 607.37 — Blocking Operations

Axiom must explicitly distinguish:

```text
nonblocking task
blocking task
```

Blocking code must not silently consume the entire normal executor.

---

# 607.38 — Blocking Executor

A dedicated blocking executor shall exist:

```text
BlockingExecutor
```

Example:

```text
await blocking {
    legacy_file_operation()
}
```

The blocking executor has its own:

```text
thread quota
resource scope
queue quota
priority
```

---

# 607.39 — Blocking Detection

Debug builds may detect a task that blocks inside a normal CPU executor.

Possible diagnostic:

```text
BlockingOperationOnCpuExecutor
```

Production behavior may be configurable.

---

# 607.40 — Async I/O

Axiom shall provide asynchronous I/O abstractions:

```text
AsyncRead
AsyncWrite
AsyncConnect
AsyncAccept
AsyncFile
AsyncSocket
```

Platform adapters translate these into native completion mechanisms.

---

# 607.41 — I/O Completion

Preferred platform-native models include:

```text
Windows → IOCP
Linux → io_uring / epoll / native mechanisms
macOS → kqueue / native mechanisms
Android → platform facilities
iOS → platform facilities
WASM → host callbacks
```

The API must not expose these directly.

---

# 607.42 — Completion Queue

I/O completion events enter the executor through a bounded completion mechanism.

```text
OS completion
      ↓
Axiom I/O backend
      ↓
completion queue
      ↓
task wakeup
```

---

# 607.43 — Async Task

An async function represents resumable work.

Conceptually:

```text
async fn fetch_data(...) -> Result<Data>
```

does not require one OS thread per invocation.

---

# 607.44 — Future

The result of asynchronous execution is represented by:

```text
Future<T>
```

A future is a state machine.

It contains:

```text
state
result
waker
cancellation
deadline
resource_scope
```

---

# 607.45 — No Hidden Heap Requirement

The compiler should lower async functions into explicit state machines.

Where lifetime analysis permits, the state machine may live:

```text
stack
caller-provided storage
inline task storage
```

rather than requiring a heap allocation.

---

# 607.46 — Async State Machine

Conceptually:

```text
Created
 ↓
Poll
 ↓
Pending
 ↓
Wake
 ↓
Poll
 ↓
Ready
```

The executor drives the state machine.

---

# 607.47 — Poll Contract

Conceptually:

```text
Poll<T> {
    Ready(T)
    Pending(Waker)
}
```

A task returning `Pending` must register a valid wakeup source.

---

# 607.48 — Waker

A `Waker` schedules the associated task.

```text
Waker {
    task_id
    generation
    executor_id
}
```

A stale waker shall be rejected.

---

# 607.49 — Wake Coalescing

Multiple wakeups may be collapsed:

```text
wake
wake
wake
wake
```

into:

```text
one runnable event
```

if the task is already queued.

This prevents wake storms.

---

# 607.50 — Wake Storm Protection

The executor shall track:

```text
queued
running
waiting
```

so a task cannot accidentally be queued thousands of times simultaneously.

---

# 607.51 — Async Cancellation

Cancellation shall be explicit.

```text
CancellationToken
```

Cancellation states:

```text
Active
Requested
Cancelled
Completed
```

---

# 607.52 — Cooperative Cancellation

A cancellation request does not forcibly terminate arbitrary CPU code.

Instead:

```text
cancel request
     ↓
task observes
     ↓
cleanup
     ↓
Cancelled
```

This preserves memory/resource safety.

---

# 607.53 — Cancellation Propagation

Structured concurrency shall propagate cancellation:

```text
Parent
  ├── Child A
  ├── Child B
  └── Child C
```

If the parent scope is cancelled:

```text
A → cancel
B → cancel
C → cancel
```

unless explicitly detached.

---

# 607.54 — Detached Tasks

Detached tasks may exist but must explicitly declare lifetime ownership.

Example:

```text
spawn_detached(...)
```

A detached task belongs to an executor/application scope rather than the lexical parent.

Detached work must not silently survive application shutdown.

---

# 607.55 — Structured Concurrency

Default concurrency should be structured.

Conceptual:

```text
scope {
    a = spawn(...)
    b = spawn(...)
    c = spawn(...)

    await a
    await b
    await c
}
```

Leaving the scope requires child tasks to:

```text
complete
cancel
or explicitly detach
```

---

# 607.56 — Child Failure

If one child fails, the structured scope may use policies:

```text
CancelSiblings
Continue
CollectErrors
FailFast
```

The default should be explicitly defined by the language/runtime rather than left ambiguous.

---

# 607.57 — Error Aggregation

Multiple child failures may be collected:

```text
TaskGroupError {
    primary
    secondary[]
}
```

No error should be silently discarded.

---

# 607.58 — Async Exception Boundary

A failed task stores its failure in its future/result.

It must not crash the entire process merely because the task failed.

Process-level termination remains an explicit supervisor/runtime policy.

---

# 607.59 — Deadline

Tasks may specify:

```text
deadline: Time
```

Deadline is absolute monotonic time.

Example:

```text
deadline = now + 500.ms
```

---

# 607.60 — Timeout

Timeout is syntactic sugar over a deadline.

```text
with_timeout(500.ms, operation)
```

shall internally use the same deadline model.

---

# 607.61 — Deadline Propagation

A child task inherits the parent's deadline unless explicitly shortened.

A child may not extend the parent's deadline automatically.

---

# 607.62 — Timer Integration

BOOTSTRAP-606 governs timer resources.

BOOTSTRAP-607 uses timers to wake tasks.

Therefore:

```text
timer request
→ ResourceGovernor admission
→ Timer backend
→ task wakeup
```

---

# 607.63 — Timer Wheel

The runtime may use:

```text
hierarchical timer wheel
```

for large numbers of timers.

Alternative structures may be used if benchmarked superior.

The API remains independent.

---

# 607.64 — Sleeping Tasks

Sleeping shall not occupy an OS thread.

```text
sleep(1.s)
```

should become:

```text
task → Waiting
timer → registered
thread → available
```

---

# 607.65 — Event Waiting

Tasks may wait for:

```text
IPC
I/O
timer
channel
mutex
condition
process
GPU completion
```

without consuming an OS worker thread where the backend supports asynchronous waiting.

---

# 607.66 — Async Mutex

Axiom shall provide async-compatible synchronization:

```text
AsyncMutex
AsyncRwLock
AsyncSemaphore
AsyncEvent
```

Waiting must yield the task instead of blocking the worker thread.

---

# 607.67 — Synchronous Mutex

Synchronous primitives remain available:

```text
Mutex
RwLock
Semaphore
Event
```

They are appropriate for short critical sections.

---

# 607.68 — Blocking Mutex Detection

Debug diagnostics may detect prolonged lock ownership or blocking.

Example:

```text
LongCriticalSection
PotentialPriorityInversion
BlockingInsideAsyncTask
```

---

# 607.69 — Priority Inversion

The scheduler/runtime shall cooperate with platform synchronization mechanisms where possible.

For Axiom primitives:

```text
priority inheritance
```

may be enabled.

---

# 607.70 — Deadlock Prevention

Axiom shall not attempt to make arbitrary user locking mathematically deadlock-free.

Instead, runtime facilities provide:

- lock ordering metadata;
- timeout;
- cancellation;
- diagnostics;
- deadlock detection in diagnostic builds.

---

# 607.71 — Executor Isolation

Separate workloads may use separate executors:

```text
InteractiveExecutor
BackgroundExecutor
IoExecutor
BlockingExecutor
GpuExecutor
```

This prevents one workload class from monopolizing another.

---

# 607.72 — Executor Resource Groups

Each executor belongs to a BOOTSTRAP-606 resource scope.

Example:

```text
Application
 ├── InteractiveExecutor
 │     └── CPU budget 50%
 │
 └── BackgroundExecutor
       └── CPU budget 20%
```

---

# 607.73 — Executor Backpressure

When an executor reaches its resource limit:

```text
submit
 ↓
admission
 ↓
accepted
```

or:

```text
submit
 ↓
quota exceeded
 ↓
await / reject
```

Tasks must not silently accumulate forever.

---

# 607.74 — Work-Stealing and Resource Groups

Workers may steal tasks only when permitted by resource policy.

A task belonging to a restricted resource group must not be executed by a worker in a way that bypasses its group's CPU/accounting policy.

---

# 607.75 — Cross-Executor Stealing

Default:

```text
same executor → allowed
different executor → forbidden
```

unless explicitly configured.

This keeps workload isolation predictable.

---

# 607.76 — Executor Affinity

An executor can define:

```text
cpu_set
numa_nodes
priority
resource_scope
```

Tasks submitted to that executor inherit these constraints unless explicitly narrowed.

---

# 607.77 — Task Migration Between Executors

A task may migrate if:

```text
executor policy permits
resource scopes compatible
security policy permits
task not pinned
```

Migration must preserve:

```text
cancellation
deadline
resource ownership
priority
```

---

# 607.78 — Thread-Local Storage

Axiom may provide:

```text
ThreadLocal<T>
```

but task migration means thread-local state must not be treated as task-local state.

For async workflows:

```text
TaskLocal<T>
```

should be available.

---

# 607.79 — Task Local Context

Task-local state may contain:

```text
correlation_id
locale
diagnostic_context
cancellation
deadline
resource_scope
```

This integrates with BOOTSTRAP-602.

---

# 607.80 — Context Propagation

When spawning a child:

```text
parent context
      ↓
child context
```

selected context fields propagate.

Sensitive capabilities must not automatically propagate unless explicitly delegated according to BOOTSTRAP-603.

---

# 607.81 — Security Context

The scheduler shall not use ordinary task-local context as a security authority.

Security capabilities remain opaque and explicit.

---

# 607.82 — CPU Yield

A task may voluntarily yield:

```text
yield()
```

The scheduler places it back into an appropriate runnable queue.

---

# 607.83 — Cooperative Long Tasks

Long CPU tasks should periodically provide scheduling points when practical.

Example:

```text
for item in data {
    process(item)

    if scheduler.should_yield():
        yield()
}
```

---

# 607.84 — Preemption

OS threads remain preemptively scheduled by the OS.

Axiom tasks are primarily cooperatively suspended at:

- await;
- yield;
- blocking boundary;
- synchronization wait;
- explicit scheduler point.

The runtime must not claim that every arbitrary task is safely preemptible at instruction granularity.

---

# 607.85 — CPU-Bound Task Isolation

A long-running CPU task may be marked:

```text
cpu_bound
```

The executor can dedicate workers or scheduling policy accordingly.

---

# 607.86 — Real-Time Executor

Axiom may expose an optional:

```text
RealtimeExecutor
```

for supported platforms.

Features:

```text
deadline
priority
CPU affinity
bounded allocations
preallocated queues
```

Real-time guarantees shall only be claimed when the underlying platform can provide them.

---

# 607.87 — Real-Time Restrictions

Inside a strict real-time scope, the runtime may forbid:

```text
unbounded allocation
blocking I/O
dynamic resource discovery
unbounded locks
unbounded queue growth
```

---

# 607.88 — Real-Time Resource Reservation

Realtime execution shall require BOOTSTRAP-606 reservations.

Example:

```text
cpu reservation = 1 core
thread reservation = 2
memory reservation = 64 MiB
```

---

# 607.89 — Energy-Aware Scheduling

On mobile/embedded platforms, scheduler decisions may incorporate:

```text
thermal pressure
battery state
energy class
```

from BOOTSTRAP-606.

---

# 607.90 — GPU Executor

GPU work shall use an executor abstraction.

```text
GpuExecutor {
    device
    queues
    resource_scope
}
```

---

# 607.91 — GPU Task

A GPU task may contain:

```text
kernel
buffers
dependencies
stream
deadline
resource_scope
```

The scheduler submits it to a GPU queue.

---

# 607.92 — CPU/GPU Dependency

Example:

```text
CPU Task A
     ↓
GPU Task B
     ↓
CPU Task C
```

The scheduler shall represent these dependencies without blocking an OS worker unnecessarily.

---

# 607.93 — GPU Completion

GPU completion should wake dependent CPU tasks through an event/completion mechanism.

```text
GPU complete
    ↓
event
    ↓
waker
    ↓
CPU task runnable
```

---

# 607.94 — GPU Backpressure

GPU submission shall obey:

```text
queue depth
GPU memory
GPU contexts
GPU streams
compute budget
```

from BOOTSTRAP-606.

---

# 607.95 — Dependency Graph

Tasks may declare dependencies:

```text
A → B
A → C
B,C → D
```

The scheduler shall not run D until B and C complete.

---

# 607.96 — DAG Execution

Independent tasks may execute concurrently.

```text
       A
      / \
     B   C
      \ /
       D
```

Axiom should support efficient DAG execution without requiring a general-purpose graph runtime for ordinary tasks.

---

# 607.97 — Task Continuation

A future may register a continuation:

```text
future.then(fn)
```

The continuation becomes a normal scheduled task.

---

# 607.98 — Continuation Executor

A continuation may specify:

```text
same executor
specific executor
caller executor
default executor
```

The default shall avoid unexpected blocking.

---

# 607.99 — Inline Continuation

Very small continuations may run inline under executor policy.

Again, bounded recursion is required.

---

# 607.100 — Async Channels

Axiom shall provide:

```text
Channel<T>
```

with bounded capacity.

Operations:

```text
send
receive
try_send
try_receive
close
```

---

# 607.101 — Channel Backpressure

When full:

```text
send
→ Pending
```

or:

```text
send
→ Rejected
```

according to policy.

No implicit unlimited growth.

---

# 607.102 — Channel Scheduling

Channel readiness wakes waiting tasks.

A send should wake a waiting receiver.

A receive should wake a waiting sender when capacity becomes available.

---

# 607.103 — Select / Wait-All

Async tasks should support waiting on multiple operations.

Conceptually:

```text
select {
    network = socket.receive()
    timer = sleep(1.s)
    ipc = channel.receive()
}
```

Only one branch wins unless explicitly using `join`.

---

# 607.104 — Select Cancellation

Losing operations must be cancelled or safely detached according to their semantics.

No resource leak is permitted.

---

# 607.105 — Join

`join` waits for multiple tasks:

```text
join(a, b, c)
```

The caller yields rather than blocking an OS thread.

---

# 607.106 — Race

A `race` waits for the first completion.

Remaining tasks are cancelled by default unless explicitly retained.

---

# 607.107 — Task Group

Conceptual:

```text
group {
    spawn(a)
    spawn(b)
    spawn(c)
}
```

Group lifetime owns child tasks.

---

# 607.108 — Task Scope Lifetime

A task cannot outlive a structured scope unless:

```text
detach
```

has explicitly transferred ownership.

---

# 607.109 — Resource Scope Binding

Every task shall belong to a resource scope.

Default:

```text
task → executor scope
```

or:

```text
task → parent task scope
```

according to API.

This ensures task execution is chargeable to a known resource owner.

---

# 607.110 — Task Resource Override

A task may use a narrower resource scope:

```text
spawn_in(scope, task)
```

It cannot use a scope with greater authority without explicit capability.

---

# 607.111 — CPU Accounting

CPU time shall be charged to:

```text
task
→ executor
→ service
→ application
```

according to BOOTSTRAP-606 attribution rules.

---

# 607.112 — Async Wait Accounting

A task waiting on I/O should not be charged as consuming CPU.

The scheduler distinguishes:

```text
Running
Waiting
Blocked
```

---

# 607.113 — Blocked Worker Accounting

An OS thread blocked in a legacy operation continues consuming a thread resource.

The runtime may move blocking work to `BlockingExecutor`.

---

# 607.114 — Scheduler Metrics

Required metrics:

```text
runnable_tasks
running_tasks
waiting_tasks
worker_count
idle_workers
steal_count
queue_depth
task_latency
task_wait_time
executor_rejections
wakeups
context_switches
```

---

# 607.115 — Scheduler Diagnostics

BOOTSTRAP-602 shall support events:

```text
TaskCreated
TaskStarted
TaskCompleted
TaskFailed
TaskCancelled
TaskBlocked
TaskWoken
TaskMigrated
TaskStolen
WorkerCreated
WorkerDestroyed
ExecutorSaturated
```

High-frequency events may be sampled.

---

# 607.116 — Scheduler Tracing

Optional spans:

```text
task.execute
task.wait
task.wake
task.steal
task.migrate
io.await
gpu.await
```

---

# 607.117 — Task Latency

Scheduler shall distinguish:

```text
queue_delay
execution_time
wait_time
blocked_time
```

Example:

```text
total_latency =
queue_delay
+
execution_time
+
wait_time
```

---

# 607.118 — Scheduler Starvation Detection

Diagnostic builds may detect:

```text
task waiting too long while runnable
```

and emit:

```text
PossibleSchedulerStarvation
```

---

# 607.119 — Executor Saturation

If:

```text
runnable_tasks >> worker_capacity
```

the executor enters:

```text
Saturated
```

state.

The governor may then:

```text
increase workers
throttle producers
reject work
```

according to resource limits.

---

# 607.120 — Scheduler Pressure

Scheduler pressure states:

```text
Normal
Busy
Saturated
Overloaded
```

These are independent from memory/CPU pressure.

---

# 607.121 — Producer Backpressure

When an executor is saturated:

```text
producer
    ↓
submit
    ↓
admission
    ↓
await/reject
```

rather than:

```text
submit
→ infinite queue
```

---

# 607.122 — Scheduler Fairness Across Services

If multiple services share an executor, each service's resource scope remains visible.

Scheduling must not allow one service to bypass its BOOTSTRAP-606 CPU budget simply because it submits more tasks.

---

# 607.123 — Service Executor Isolation

A service may receive:

```text
dedicated executor
```

when strong isolation is required.

Otherwise:

```text
shared executor
```

may be used for efficiency.

---

# 607.124 — Executor Selection

Default task placement:

```text
explicit executor
        ↓
task-local executor
        ↓
service executor
        ↓
application default executor
```

---

# 607.125 — Blocking Executor Selection

Blocking operations should automatically target:

```text
BlockingExecutor
```

when the compiler/runtime can identify them.

Explicit annotations may override detection.

---

# 607.126 — Compiler Async Lowering

The compiler shall transform:

```text
async fn foo()
```

into a state machine represented in compiler IR.

States correspond to suspension points.

---

# 607.127 — Suspension Point

At:

```text
await operation
```

the compiler generates:

```text
save state
register continuation
return Pending
```

---

# 607.128 — Resume Point

When the awaited operation completes:

```text
waker
 ↓
task queued
 ↓
state machine resumes
```

---

# 607.129 — Async Frame Layout

The compiler shall calculate:

```text
locals live across await
```

and place only those values in the async frame.

This minimizes memory.

---

# 607.130 — Stack vs Heap Async Frames

Possible storage:

```text
inline
stack
caller-owned
heap
arena
```

The compiler/runtime should choose the cheapest safe representation.

---

# 607.131 — Frame Ownership

Every async frame has deterministic ownership.

No GC is required.

A completed or cancelled frame is released exactly once.

---

# 607.132 — Pinning

An async frame may be marked internally as immovable if required by generated state-machine references.

This is an implementation detail.

Ordinary Axiom programmers should not need to manipulate raw pointers to async frames.

---

# 607.133 — Async Frame Safety

The compiler must ensure values live across suspension remain valid.

Invalid lifetime transitions are compile-time errors.

---

# 607.134 — Await Safety

The compiler shall prevent use of invalidated state after suspension.

This is part of language semantic analysis, not a runtime garbage collector.

---

# 607.135 — No Mandatory Borrow Checker

Axiom async safety shall not require a Rust-style general borrow checker.

The compiler may perform targeted lifetime/state-machine validation necessary for generated async frames.

---

# 607.136 — Scheduler ABI

Axiom async ABI shall define:

```text
FutureHeader
TaskFrame
PollResult
Waker
ExecutorContext
```

These must have stable internal conventions.

---

# 607.137 — Native ABI

Native synchronous functions remain ordinary ABI-compatible functions.

Async functions are represented as generated state-machine objects/functions.

The compiler may provide optimized synchronous fast paths when no suspension occurs.

---

# 607.138 — Async Elision

If static analysis proves:

```text
no actual suspension
```

the compiler may optimize an async function into direct execution.

---

# 607.139 — Small Future Optimization

Small future/task states may be stored inline.

Large states may use external storage.

Thresholds are implementation-defined and benchmark-driven.

---

# 607.140 — Scheduler Fast Path

Common case:

```text
submit tiny task
```

should ideally perform:

```text
allocate/obtain task storage
→ push local queue
→ return
```

without entering the OS scheduler.

---

# 607.141 — Wake Fast Path

If target worker is already active:

```text
wake
→ push queue
```

without an OS wakeup when possible.

---

# 607.142 — Worker Wakeup

If no worker is available:

```text
wake
→ platform event/futex/condition mechanism
```

The exact primitive is platform-specific.

---

# 607.143 — Sleep Strategy

Idle workers may use:

```text
spin
→ yield
→ park
```

with bounded escalation.

---

# 607.144 — Adaptive Spinning

Very short idle periods may justify spinning.

Long idle periods should park the thread to conserve CPU and energy.

Policy may depend on:

```text
work arrival rate
CPU pressure
thermal pressure
energy profile
```

---

# 607.145 — Scheduler Tuning

Runtime configuration may expose:

```text
spin_budget
park_timeout
steal_attempts
worker_min
worker_max
```

These are implementation-level settings and should not normally appear in application code.

---

# 607.146 — Work-Stealing Randomization

Victim selection may use a lightweight pseudo-random strategy to avoid synchronized stealing.

The randomness must not affect correctness.

---

# 607.147 — Deterministic Scheduler Mode

Tests shall support:

```text
DeterministicExecutor
```

with:

- deterministic worker count;
- deterministic queue ordering;
- deterministic virtual clock;
- deterministic wakeups.

This enables reproducible concurrency tests.

---

# 607.148 — Race Testing

A scheduler test mode shall intentionally vary:

```text
task ordering
wake timing
worker assignment
stealing
cancellation
```

to expose races.

---

# 607.149 — Stress Testing

Required stress scenarios:

```text
1 million small tasks
mass cancellation
high wake rate
deep task trees
executor saturation
worker churn
I/O completion storms
GPU completion storms
mixed blocking/nonblocking work
```

---

# 607.150 — Deadlock Detection

Diagnostic runtime may construct a wait graph:

```text
Task A waits B
Task B waits C
Task C waits A
```

and report a cycle.

This is diagnostic only unless a safe automatic recovery policy exists.

---

# 607.151 — Wait Graph

Nodes:

```text
Task
Thread
Resource
```

Edges:

```text
waits_for
owns
holds
```

This integrates with BOOTSTRAP-606.

---

# 607.152 — Priority Inversion Detection

The runtime may report:

```text
High task
    ↓ waits
Low task
    ↓ holds
resource
```

as:

```text
PotentialPriorityInversion
```

---

# 607.153 — Cancellation Safety

Cancellation shall not release a resource still in active use.

Cancellation sequence:

```text
request
→ operation acknowledges
→ cleanup
→ resource release
→ task cancelled
```

---

# 607.154 — Forced Cancellation

Forced cancellation shall be restricted to operations that explicitly support safe interruption.

Arbitrary native code must not be asynchronously killed at an arbitrary instruction.

---

# 607.155 — Shutdown

Executor shutdown modes:

```text
Drain
Cancel
Immediate
```

---

# 607.156 — Drain Shutdown

```text
stop accepting new work
→ execute queued work
→ finish running work
→ release workers
```

---

# 607.157 — Cancel Shutdown

```text
stop accepting new work
→ request cancellation
→ drain cleanup
→ terminate remaining executor work
```

---

# 607.158 — Immediate Shutdown

Immediate shutdown is reserved for emergency/runtime failure scenarios.

The runtime must still preserve resource accounting and diagnostics as far as possible.

---

# 607.159 — Application Shutdown

Shutdown ordering:

```text
Supervisor
 ↓
Executors stop admission
 ↓
Services drain
 ↓
Tasks cancel/complete
 ↓
I/O completes/cancels
 ↓
Workers exit
 ↓
Resource scopes close
```

This integrates with BOOTSTRAP-605.

---

# 607.160 — Executor Failure

If an executor encounters an internal failure:

```text
executor → Failed
```

The supervisor/diagnostics layer is notified.

Tasks may:

```text
retry
migrate
fail
```

according to policy.

---

# 607.161 — Task Retry

Retry shall be explicit.

```text
retry_policy {
    max_attempts
    backoff
    deadline
}
```

Retries consume resources and must be charged normally.

---

# 607.162 — Retry Storm Prevention

Retries shall respect:

```text
deadline
resource budget
retry budget
supervisor restart policy
```

---

# 607.163 — Async Retry Example

Conceptually:

```text
retry {
    await network_request()
}
max_attempts = 3
```

The scheduler remains responsible only for execution; retry semantics remain a higher-level library facility.

---

# 607.164 — I/O Cancellation

Cancellation of I/O must use the platform's native cancellation mechanism where supported.

If cancellation cannot be physically interrupted:

```text
task cancellation
```

may occur while the underlying I/O completes in the background.

The runtime must safely discard or route its completion.

---

# 607.165 — Late Completion

A late completion must validate:

```text
operation_id
generation
state
```

before touching task state.

Stale completion:

```text
Ignored
```

rather than memory corruption.

---

# 607.166 — Operation Identity

Async operations use:

```text
(OperationId, Generation)
```

for stale completion protection.

---

# 607.167 — I/O Resource Charging

Outstanding I/O operations count toward BOOTSTRAP-606:

```text
async_operations.max
```

This prevents unlimited outstanding I/O.

---

# 607.168 — File I/O Scheduling

Large file operations may be divided into bounded operations.

The runtime shall avoid blocking an executor worker for huge synchronous transfers.

---

# 607.169 — Network I/O

Sockets should use asynchronous readiness/completion.

A task awaiting a socket does not consume an OS worker.

---

# 607.170 — IPC I/O

BOOTSTRAP-604 IPC completion should integrate directly with the async executor.

No separate user-visible thread is required per IPC channel.

---

# 607.171 — Process Waiting

Waiting for a child process shall be asynchronous.

Conceptually:

```text
await process.wait()
```

The task yields until the supervisor/platform reports completion.

---

# 607.172 — Supervisor Integration

BOOTSTRAP-605 may submit lifecycle events into an executor:

```text
process_started
process_exited
health_changed
restart_requested
```

The supervisor must maintain a control executor isolated from ordinary application workload.

---

# 607.173 — Supervisor Control Executor

The supervisor should reserve:

```text
minimum worker capacity
memory
event queue
```

through BOOTSTRAP-606.

Application workload cannot consume the supervisor's emergency control capacity.

---

# 607.174 — Security Integration

Scheduling operations requiring elevated platform authority must use capabilities.

Examples:

```text
set_cpu_affinity
set_realtime_priority
create_worker_outside_scope
inspect_other_executor
```

Normal task scheduling needs no privileged capability.

---

# 607.175 — Priority Security Boundary

An application cannot use:

```text
Critical priority
```

to obtain:

```text
admin capability
filesystem capability
debug capability
```

---

# 607.176 — Resource Scope Propagation

Every task has a resource scope.

Executor migration must preserve it.

Therefore:

```text
Task A
scope = ServiceA
worker = CPU4
```

migrating to:

```text
worker = CPU7
```

still charges:

```text
ServiceA
```

---

# 607.177 — Diagnostic Context Propagation

Task execution shall preserve BOOTSTRAP-602 correlation context.

Example:

```text
request_id
trace_id
span_id
```

must follow asynchronous continuations.

---

# 607.178 — Configuration

BOOTSTRAP-601 may configure:

```text
executor {
    min_workers
    max_workers
    queue_size
    priority
    affinity
    idle_timeout
}
```

Invalid configuration remains atomically rejected.

---

# 607.179 — Runtime Reconfiguration

Some scheduler settings may change at runtime:

```text
worker maximum
queue limits
priority
affinity
```

Policy changes must be applied safely.

---

# 607.180 — Immutable Execution Policies

Active task state should not depend on mutable global configuration.

Executor policy changes apply through versioned snapshots.

---

# 607.181 — Policy Epoch

Each executor has:

```text
ExecutorPolicyEpoch
```

Tasks observe the policy relevant to their scheduling decision.

---

# 607.182 — Compiler Scheduling Metadata

The compiler may emit:

```text
@cpu_bound
@blocking
@realtime
@io
@gpu
@priority(...)
```

These are declarations/hints subject to runtime policy.

---

# 607.183 — Blocking Annotation

Example:

```text
@blocking
fn legacy_database_call(...)
```

The compiler can automatically route calls through the blocking boundary where safe.

---

# 607.184 — Async Function Syntax

Core syntax should remain simple:

```text
async fn load() -> Result<Data> {
    let response = await request()
    return await decode(response)
}
```

The syntax is language-level; runtime scheduling is handled by the executor.

---

# 607.185 — Spawn Syntax

Conceptual:

```text
let task = spawn(async {
    await work()
})
```

---

# 607.186 — Structured Spawn

```text
task_scope {
    let a = spawn(work_a())
    let b = spawn(work_b())

    await a
    await b
}
```

The scope owns both tasks.

---

# 607.187 — Explicit Executor

```text
spawn_on(io_executor, work())
```

The API must make cross-executor execution explicit.

---

# 607.188 — Task Priority

```text
spawn(
    priority = High,
    work()
)
```

Priority is bounded by executor and security policy.

---

# 607.189 — Deadline

```text
spawn(
    deadline = now + 1.s,
    work()
)
```

The task cannot extend its inherited parent deadline.

---

# 607.190 — Cancellation

```text
scope.cancel()
```

propagates cancellation to children.

---

# 607.191 — Executor API

Struct-only API:

```text
struct Executor {
    ...
}

fn Executor.spawn<T>(
    self,
    task: TaskFn<T>
) -> TaskHandle<T>
```

---

# 607.192 — Task API

```text
struct TaskHandle<T> {
    ...
}

fn TaskHandle.await(
    self
) -> Result<T>
```

---

# 607.193 — Cancellation API

```text
struct CancellationToken {
    ...
}

fn CancellationToken.cancel(self)
fn CancellationToken.is_cancelled(self) -> bool
```

---

# 607.194 — Executor Shutdown API

```text
fn Executor.shutdown(
    self,
    mode: ShutdownMode
) -> Result
```

---

# 607.195 — Async Mutex API

```text
struct AsyncMutex<T> {
    ...
}

async fn AsyncMutex.lock(
    self
) -> Guard<T>
```

The guard releases deterministically.

---

# 607.196 — Channel API

```text
struct Channel<T> {
    ...
}

async fn Channel.send(self, value: T)
async fn Channel.receive(self) -> Option<T>
```

---

# 607.197 — Scheduler Backend

Canonical abstraction:

```text
trait SchedulerBackend {
    fn create_worker(...)
    fn destroy_worker(...)
    fn set_affinity(...)
    fn set_priority(...)
    fn park(...)
    fn wake(...)
}
```

Platform implementation remains separate.

---

# 607.198 — Platform Thread Backend

Required adapters:

```text
Windows
Linux
macOS
Android
iOS
WASM
Embedded
```

---

# 607.199 — Windows

Use native:

```text
threads
wait primitives
IOCP
affinity APIs
priority APIs
```

where available.

---

# 607.200 — Linux

Use native:

```text
pthread
futex
epoll/io_uring
CPU affinity
scheduler interfaces
```

where available.

---

# 607.201 — macOS

Use native:

```text
pthread
kqueue
dispatch/native mechanisms
CPU topology
```

where appropriate.

Axiom must not require Foundation or another third-party runtime layer for the core scheduler.

---

# 607.202 — Mobile

Mobile schedulers must respect:

```text
OS lifecycle
background restrictions
thermal pressure
process suspension
```

---

# 607.203 — WASM

WASM execution may map:

```text
Axiom Task
→ host event loop
```

or:

```text
Axiom Worker
→ Web Worker / host thread
```

depending on host capabilities.

---

# 607.204 — Embedded

The backend may map:

```text
Axiom worker
→ RTOS task
```

or implement a cooperative executor where no preemptive OS exists.

---

# 607.205 — Scheduler Capability Discovery

Runtime shall expose:

```text
SchedulerCapabilities {
    preemption
    threads
    async_io
    cpu_affinity
    priority
    realtime
    numa
    gpu
}
```

Unsupported capabilities are explicit.

---

# 607.206 — Scheduler Fallback

If native async I/O is unavailable:

```text
async I/O
→ bounded blocking executor
```

may be used.

The runtime must label this as:

```text
Fallback
```

because performance/semantics differ.

---

# 607.207 — No Hidden Thread Explosion

Axiom runtime shall never create one OS thread per:

```text
task
socket
timer
future
IPC channel
```

unless explicitly requested.

---

# 607.208 — Scheduler Memory Footprint

Each task should have compact metadata.

The runtime should avoid:

```text
large task objects
per-task heavyweight synchronization
mandatory heap allocation
```

for trivial tasks.

---

# 607.209 — Small Task Optimization

Tiny tasks may use:

```text
inline storage
task-object pooling
worker-local allocation
```

provided lifetime remains deterministic.

---

# 607.210 — Task Pool

Executors may maintain local task pools.

Pool ownership is:

```text
worker
executor
resource scope
```

according to implementation.

---

# 607.211 — Pool Limits

Task pools are governed resources.

They cannot grow without bound.

---

# 607.212 — Queue Allocation

Queue memory must be charged to the executor's resource scope.

---

# 607.213 — Scheduler Recursion Protection

Recursive spawning must not create unbounded stack depth.

The scheduler may flatten nested submissions into queues.

---

# 607.214 — Tail Scheduling

When a task completes and immediately produces a continuation, the scheduler may run the continuation directly.

This is an optimization.

---

# 607.215 — Continuation Locality

A continuation should prefer the same worker when that improves cache locality and does not violate policy.

---

# 607.216 — False Sharing Avoidance

Internal worker metadata should be laid out to minimize false sharing.

This is an implementation requirement for high-performance targets.

---

# 607.217 — Atomic Memory Ordering

Scheduler atomics shall use the weakest memory ordering sufficient for correctness.

Implementation shall document synchronization boundaries.

---

# 607.218 — Lock-Free Requirement

The entire scheduler does not need to be completely lock-free.

Instead:

```text
hot local queues
→ low contention
```

is preferred.

Locks may be used for:

- executor administration;
- shutdown;
- policy changes;
- rare slow paths.

---

# 607.219 — Global Scheduler Lock

A single global scheduler mutex governing every task is forbidden.

---

# 607.220 — Worker Locality

Each worker owns local scheduling state whenever practical.

This reduces synchronization overhead.

---

# 607.221 — Cross-Worker Coordination

Cross-worker operations use:

```text
atomic state
bounded queues
event wakeups
work stealing
```

rather than global locking.

---

# 607.222 — Scheduler Correctness

Mandatory invariants:

1. a task is never simultaneously owned by two executors;
2. a task cannot run after completion;
3. a cancelled task cannot resume after cancellation completion;
4. stale wakeups cannot access a reused task;
5. worker count never exceeds resource policy;
6. executor queues remain bounded;
7. task resource ownership remains stable during migration;
8. task deadlines never move later implicitly;
9. child tasks cannot outlive structured scopes;
10. shutdown eventually terminates owned workers.

---

# 607.223 — Async Correctness

Mandatory invariants:

1. a future completes at most once;
2. a waker cannot resurrect a completed task;
3. a cancellation request is idempotent;
4. a late I/O completion cannot mutate freed task state;
5. async frames are released exactly once;
6. every `Pending` operation has a valid wakeup path;
7. task state is valid across every suspension point.

---

# 607.224 — Resource Governor Invariants

BOOTSTRAP-607 shall inherit:

```text
BOOTSTRAP-606 invariants
```

in particular:

```text
no quota bypass
no resource leak
no stale generation ownership
no unbounded queue
no unauthorized priority escalation
```

---

# 607.225 — Scheduler Testing

Required unit tests:

```text
task lifecycle
queue operations
stealing
wake
sleep
deadline
cancellation
priority
affinity
executor shutdown
```

---

# 607.226 — Concurrency Testing

Required stress tests:

```text
many producers
many workers
mass wakeups
mass cancellation
task migration
queue contention
worker churn
```

---

# 607.227 — Deterministic Virtual Time

Tests shall support:

```text
clock.advance(100.ms)
```

without sleeping the host.

Timers and deadlines then advance deterministically.

---

# 607.228 — Deterministic Executor

Example:

```text
executor = DeterministicExecutor(
    workers = 4
)
```

The test may explicitly choose which worker/task executes next.

---

# 607.229 — Model Checking

Small scheduler state machines should be suitable for exhaustive exploration of:

```text
wake
cancel
complete
migrate
shutdown
```

interleavings.

---

# 607.230 — Fuzzing

Fuzz:

```text
task submission
task cancellation
wake ordering
I/O completions
timer events
executor shutdown
resource quota changes
```

---

# 607.231 — Race Detector Integration

Debug builds should optionally integrate with:

```text
Axiom synchronization metadata
```

to detect races involving Axiom-managed synchronization.

The core runtime must not require a third-party race detector.

---

# 607.232 — Failure Injection

Inject:

```text
worker creation failure
thread creation failure
I/O registration failure
I/O completion delay
queue allocation failure
timer registration failure
GPU submission failure
executor crash
resource quota exhaustion
```

---

# 607.233 — Executor Crash Recovery

If an executor fails internally:

```text
detect
→ stop admission
→ recover runnable tasks
→ release workers
→ rebuild executor
→ requeue recoverable tasks
```

Only tasks whose state is provably recoverable may be requeued.

---

# 607.234 — Task Recovery

Tasks shall declare:

```text
Recoverable
NonRecoverable
```

A non-recoverable task must fail rather than execute twice.

---

# 607.235 — Exactly-Once Execution

The scheduler shall not claim exactly-once execution across crashes.

Within one healthy runtime, however:

```text
task execution state
```

must prevent accidental duplicate execution.

---

# 607.236 — Idempotency

Higher-level application operations requiring retry safety should use explicit idempotency mechanisms.

The scheduler itself does not invent business-level idempotency.

---

# 607.237 — Scheduler State Checkpoint

BOOTSTRAP-600 may checkpoint:

```text
executor configuration
persistent task metadata
```

but ordinary in-memory task execution stacks are not assumed checkpointable.

---

# 607.238 — Restart Semantics

After application restart:

```text
old transient tasks
→ lost
```

unless explicitly persisted through an application-level durable job system.

---

# 607.239 — Durable Jobs

A higher-level runtime may build:

```text
DurableJob
```

on top of:

```text
BOOTSTRAP-600 state
+
607 executor
```

This is not part of the minimal scheduler.

---

# 607.240 — Scheduler and Persistence

Persistence must never silently turn every task into a durable task.

Durability is opt-in.

---

# 607.241 — Scheduler and IPC

IPC handlers should execute as tasks.

```text
IPC message
 ↓
decode
 ↓
spawn/queue task
 ↓
execute
 ↓
response
```

IPC queues remain governed by BOOTSTRAP-604/606.

---

# 607.242 — IPC Handler Isolation

A service may specify:

```text
handler_executor
```

so expensive IPC handlers cannot monopolize unrelated application tasks.

---

# 607.243 — IPC Handler Backpressure

If the handler executor is saturated:

```text
IPC queue
→ backpressure
```

rather than unlimited task creation.

---

# 607.244 — Network Server Model

A native Axiom server should support:

```text
event-driven socket
→ async task
→ bounded worker pool
```

rather than:

```text
one thread per connection
```

as the default.

---

# 607.245 — High-Performance Server Path

The optimized path:

```text
socket event
 ↓
parse
 ↓
small task
 ↓
worker local queue
 ↓
response
```

should avoid unnecessary heap allocation and context switching.

---

# 607.246 — Scheduler and Memory

Task frames, queues, synchronization objects and worker metadata are charged to BOOTSTRAP-606.

The scheduler cannot allocate outside its declared memory budget.

---

# 607.247 — Scheduler and GPU

GPU queues and task frames are governed separately.

CPU workers waiting for GPU completion should yield.

---

# 607.248 — Scheduler and Diagnostics

Diagnostics must preserve:

```text
task_id
generation
executor
worker
resource_scope
trace_id
```

without exposing internal pointers.

---

# 607.249 — Scheduler and Configuration

Configuration shall support:

```text
default_executor
worker_limits
queue_limits
scheduling_policy
affinity
priority
blocking_executor
```

---

# 607.250 — Scheduler and Security

Scheduler operations are subject to BOOTSTRAP-603.

Particularly:

```text
realtime scheduling
CPU affinity
cross-process scheduling
resource inspection
```

---

# 607.251 — Scheduler and Supervisor

Supervisor owns lifecycle.

Executor owns execution.

Therefore:

```text
Supervisor:
    start/stop/restart service

Executor:
    execute tasks inside service
```

Neither subsystem should absorb the other's responsibilities.

---

# 607.252 — Scheduler and Resource Governor

The complete execution decision is:

```text
Task Ready
    ↓
Security validation
    ↓
Resource admission
    ↓
Executor eligibility
    ↓
Priority/fairness
    ↓
Worker selection
    ↓
Execution
```

---

# 607.253 — Scheduler Policy

The scheduler shall expose policy objects:

```text
SchedulingPolicy {
    priority
    fairness
    affinity
    locality
    stealing
    preemption
}
```

Policies are composable but must have defined precedence.

---

# 607.254 — Scheduling Policy Precedence

Recommended:

```text
Security
→ Resource limits
→ Hard affinity
→ Realtime constraints
→ Deadline
→ Priority
→ Fairness
→ Locality optimization
```

---

# 607.255 — Deadline Scheduling

Optional executor policy:

```text
EarliestDeadlineFirst
```

may be used for deadline-oriented workloads.

It must still respect:

```text
resource quota
security
CPU availability
```

---

# 607.256 — Deadline Miss

If a task misses its deadline:

```text
DeadlineMissed
```

is emitted.

The scheduler does not automatically kill the task unless configured.

---

# 607.257 — Deadline Cancellation

An executor may configure:

```text
on_deadline_miss = cancel
```

for appropriate workloads.

---

# 607.258 — Latency vs Throughput

Executor profiles may target:

```text
Latency
Throughput
Balanced
Energy
Realtime
```

These are policies, not guarantees.

---

# 607.259 — Adaptive Scheduling

The scheduler may dynamically adjust:

```text
worker count
steal aggressiveness
spin duration
queue strategy
```

based on workload.

Adaptation must stay within resource policy.

---

# 607.260 — Scheduler Observability

An administrator should be able to inspect:

```text
axiom scheduler tree
axiom scheduler workers
axiom scheduler queues
axiom scheduler tasks
axiom scheduler pressure
```

without exposing unauthorized application data.

---

# 607.261 — AI-Readable Scheduler Metadata

Compiled artifacts may contain:

```text
execution {
    async_functions
    blocking_functions
    cpu_bound_functions
    gpu_functions
    resource_requirements
}
```

This helps compiler tools and AI agents understand concurrency behavior.

---

# 607.262 — Compiler Optimization

The compiler may optimize:

```text
spawn + immediately await
```

into direct execution when semantics permit.

---

# 607.263 — Future Elimination

If a future is provably consumed immediately:

```text
future = spawn(foo)
await future
```

the compiler may optimize it toward:

```text
foo()
```

provided observable scheduling semantics are preserved or explicitly permitted by the language.

---

# 607.264 — Async Fusion

Adjacent async state-machine segments may be fused where this reduces overhead and does not change externally observable behavior.

---

# 607.265 — Task Batching

Multiple tiny tasks may be batched.

Example:

```text
1000 tiny tasks
```

may execute through:

```text
one worker batch
```

while preserving required ordering semantics.

---

# 607.266 — Vectorized Work

Higher-level libraries may submit data-parallel work as one task rather than millions of tiny tasks.

The scheduler should not be responsible for SIMD generation; the compiler handles that.

---

# 607.267 — Parallel Loop

Axiom should eventually expose:

```text
parallel_for(range, fn)
```

implemented on top of executors.

It should use chunking to prevent excessive task creation.

---

# 607.268 — Parallel Reduction

Likewise:

```text
parallel_reduce(...)
```

can use:

```text
divide
→ execute
→ reduce
```

through the scheduler.

---

# 607.269 — Work Granularity

Parallel APIs should expose or infer:

```text
grain_size
```

so very small work units are not scheduled independently.

---

# 607.270 — Scheduler Runtime Tiers

Three runtime tiers:

```text
MinimalExecutor
StandardExecutor
AdvancedExecutor
```

Minimal:

```text
single/multi-thread
basic queue
basic async
```

Standard:

```text
work stealing
async I/O
timers
structured concurrency
```

Advanced:

```text
NUMA
GPU
realtime
adaptive scheduling
advanced telemetry
```

Unused tiers should be dead-stripped.

---

# 607.271 — Single-Thread Mode

Axiom shall support:

```text
SingleThreadExecutor
```

for:

- embedded;
- tests;
- WASM;
- deterministic applications;
- tiny utilities.

No unnecessary worker threads are created.

---

# 607.272 — Multi-Thread Mode

Standard native applications may use:

```text
N workers
```

where:

```text
N <= ResourceGovernor thread limit
```

---

# 607.273 — Executor Hierarchy

Executors may be nested:

```text
Application Executor
 ├── Service Executor A
 └── Service Executor B
```

Nested executors inherit resource restrictions.

---

# 607.274 — Executor Ownership

An executor has one owner:

```text
Application
Service
ResourceGroup
```

It cannot silently move between scopes.

---

# 607.275 — Executor Destruction

Before executor destruction:

```text
stop admission
→ resolve/cancel tasks
→ drain queues
→ release workers
→ release resource tokens
```

---

# 607.276 — Resource Leak Detection

After shutdown:

```text
active_tasks == 0
workers == 0
queue_depth == 0
resource_tokens == 0
```

unless explicitly persistent.

---

# 607.277 — Scheduler Error Model

Canonical errors:

```text
ExecutorClosed
QueueFull
TaskCancelled
DeadlineExceeded
ResourceDenied
WorkerUnavailable
Unsupported
InvalidTaskHandle
StaleTaskGeneration
ExecutorFailed
```

---

# 607.278 — ABI / FFI

Axiom async runtime shall expose a C-compatible bridge only when explicitly requested.

Foreign code should not need to understand internal executor structures.

---

# 607.279 — FFI Blocking Boundary

Foreign functions marked blocking:

```text
@blocking
extern fn legacy_call(...)
```

shall execute through the blocking executor when invoked asynchronously.

---

# 607.280 — FFI Callback Boundary

Foreign callbacks entering Axiom must use a safe scheduler entry point.

```text
axiom_schedule(callback)
```

rather than directly mutating scheduler internals.

---

# 607.281 — Callback Lifetime

Foreign callbacks must hold an explicit task/resource handle.

No callback may reference a destroyed task.

---

# 607.282 — No Hidden Runtime Thread

FFI integration must not secretly create permanent threads unless configured.

---

# 607.283 — Runtime Initialization

Initialization:

```text
platform discovery
→ ResourceGovernor
→ scheduler backend
→ executors
→ I/O backend
→ timer backend
→ diagnostics
```

---

# 607.284 — Runtime Initialization Failure

If mandatory scheduler infrastructure fails:

```text
application startup fails
```

with BOOTSTRAP-602 diagnostics.

---

# 607.285 — Runtime Shutdown

Shutdown is reverse initialization:

```text
stop admissions
→ stop I/O submissions
→ drain/cancel tasks
→ stop executors
→ release scheduler resources
→ finalize diagnostics
```

---

# 607.286 — Scheduler Bootstrap Resource Reservation

The runtime reserves enough capacity for:

```text
control executor
timer service
I/O completion
shutdown
diagnostics
```

through BOOTSTRAP-606.

---

# 607.287 — Emergency Scheduler Capacity

A small control capacity must remain protected from normal application tasks.

This allows:

```text
shutdown
crash reporting
resource recovery
supervisor control
```

even under heavy application load.

---

# 607.288 — Performance Targets

The architecture targets:

```text
local task enqueue:
O(1) expected

local dequeue:
O(1)

work stealing:
O(1) expected

task wake:
O(1) expected

task metadata:
small constant overhead

worker scaling:
O(number of workers)
```

Exact latency targets shall be benchmarked per platform rather than hard-coded into the language specification.

---

# 607.289 — Context-Switch Minimization

The runtime should minimize:

```text
OS thread wakeups
OS context switches
cross-core migration
heap allocation
global synchronization
```

---

# 607.290 — Benchmark Suite

Required benchmark categories:

```text
task spawn
task completion
await
wake
channel send/receive
mutex contention
work stealing
parallel loop
async socket
async file
timer
GPU completion
worker scaling
NUMA migration
```

---

# 607.291 — Benchmark Comparisons

The runtime should compare against representative native approaches such as:

```text
OS thread pool
native async API
simple work queue
```

Benchmark results must report:

```text
throughput
latency
CPU
memory
scaling
```

without embedding assumptions into the specification.

---

# 607.292 — Scheduler Invariant: Boundedness

No core scheduler structure may grow without a defined bound.

This includes:

```text
task queues
completion queues
timer registrations
worker counts
waiter lists
diagnostic events
```

---

# 607.293 — Scheduler Invariant: Ownership

Every task has exactly one logical owner at a time:

```text
Created
Queued
Running
Waiting
Completed
```

Ownership transitions are atomic from the scheduler's perspective.

---

# 607.294 — Scheduler Invariant: Single Execution

At most one worker may execute a task at a time.

---

# 607.295 — Scheduler Invariant: Completion

A task transitions to terminal state exactly once:

```text
Completed
Failed
Cancelled
```

---

# 607.296 — Scheduler Invariant: Wake Safety

A wake event for a completed/stale task shall have no effect.

---

# 607.297 — Scheduler Invariant: Resource Safety

Worker creation, task queues and task execution remain inside BOOTSTRAP-606 limits.

---

# 607.298 — Scheduler Invariant: Shutdown

Once executor admission is closed:

```text
no new task
```

may enter the executor except explicitly authorized shutdown/recovery tasks.

---

# 607.299 — Acceptance Criteria

BOOTSTRAP-607 is architecturally complete when:

1. OS thread model is defined.
2. Axiom task model is defined.
3. task states are defined.
4. task generations are defined.
5. executor model is defined.
6. worker model is defined.
7. local queues are defined.
8. work stealing is defined.
9. global injection queue is defined.
10. bounded queue policy is defined.
11. task priorities are defined.
12. fairness is defined.
13. CPU affinity is defined.
14. NUMA locality is defined.
15. worker scaling is defined.
16. blocking executor is defined.
17. async I/O boundary is defined.
18. future model is defined.
19. poll/waker model is defined.
20. async frame lowering is defined.
21. stack/heap async frame options are defined.
22. cancellation is defined.
23. structured concurrency is defined.
24. detached tasks are defined.
25. deadline propagation is defined.
26. timer integration is defined.
27. async synchronization is defined.
28. channels are defined.
29. select/join/race semantics are defined.
30. GPU executor is defined.
31. CPU/GPU dependency handling is defined.
32. task/resource ownership is defined.
33. task/resource accounting is defined.
34. scheduler/security boundary is defined.
35. scheduler/resource-governor integration is defined.
36. supervisor integration is defined.
37. IPC integration is defined.
38. diagnostics integration is defined.
39. configuration integration is defined.
40. state/recovery boundary is defined.
41. deterministic executor is defined.
42. deterministic virtual time is defined.
43. fuzzing is defined.
44. fault injection is defined.
45. shutdown semantics are defined.
46. executor failure handling is defined.
47. stale completion safety is defined.
48. FFI blocking boundary is defined.
49. minimal runtime tier is defined.
50. dead stripping is defined.
51. performance architecture is defined.
52. boundedness invariants are defined.
53. scheduler correctness invariants are defined.
54. async correctness invariants are defined.
55. acceptance tests are defined.

---

# 607.300 — Final Architecture

The combined execution architecture is now:

```text
                         ┌─────────────────────────┐
                         │      BOOTSTRAP-601      │
                         │ Config / Deployment     │
                         └───────────┬─────────────┘
                                     │
                         ┌───────────▼─────────────┐
                         │      BOOTSTRAP-603      │
                         │ Security / Capability   │
                         └───────────┬─────────────┘
                                     │
                         ┌───────────▼─────────────┐
                         │      BOOTSTRAP-606      │
                         │   RESOURCE GOVERNOR     │
                         │                         │
                         │ quota / budget          │
                         │ reservation             │
                         │ pressure                │
                         │ admission               │
                         └───────────┬─────────────┘
                                     │
                         ┌───────────▼─────────────┐
                         │      BOOTSTRAP-607      │
                         │   EXECUTION RUNTIME     │
                         │                         │
                         │ Scheduler               │
                         │ Executors               │
                         │ Work Stealing           │
                         │ Tasks                   │
                         │ Async/Await             │
                         │ I/O                     │
                         │ Timers                  │
                         │ Blocking Pool           │
                         │ GPU Executor            │
                         └──────┬────────┬─────────┘
                                │        │
                     ┌──────────┘        └──────────┐
                     ▼                              ▼
              ┌─────────────┐                ┌─────────────┐
              │ CPU Workers │                │ GPU Queues  │
              └──────┬──────┘                └──────┬──────┘
                     │                              │
                     ▼                              ▼
                CPU / OS                        GPU Device


   BOOTSTRAP-604 → IPC / Async I/O
   BOOTSTRAP-605 → Process / Service Lifecycle
   BOOTSTRAP-602 → Diagnostics / Tracing
   BOOTSTRAP-600 → State / Checkpoint / Recovery
```

---

# 607.301 — Architectural Boundary

The most important separation is now:

```text
600 = What state survives?

601 = What configuration applies?

602 = What happened?

603 = What is authorized?

604 = How do isolated components communicate?

605 = Which processes/services should exist?

606 = How many resources may they consume?

607 = Which work executes, when, and where?
```

This separation prevents the runtime from becoming a single monolithic subsystem.

---

# 607.302 — Completion Status

**BOOTSTRAP-607 — COMPLETE**

The Axiom runtime now has a complete foundational execution model covering:

```text
OS threads
tasks
executors
workers
work stealing
bounded queues
priorities
fairness
affinity
NUMA
async/await
futures
wakers
cancellation
deadlines
timers
async synchronization
channels
structured concurrency
blocking isolation
async I/O
GPU execution
task dependencies
scheduler recovery
resource governance
security
diagnostics
supervision
configuration
state
testing
```

The next logical architecture layer is:

# BOOTSTRAP-608
## Native Application Synchronization, Atomics, Locks, Channels, Concurrent Collections & Lock-Free Runtime Primitives 5.0

Scope:

```text
Atomic operations
Memory ordering
Mutex
RwLock
SpinLock
Semaphore
Event
Condition
Barrier
Latch
Async synchronization
Channels
Concurrent queues
Concurrent hash maps
Lock-free structures
Wait/notify
Futex-like primitives
Priority inversion
Deadlock diagnostics
ABA protection
Hazard-safe reclamation
Generation handles
CPU memory model
NUMA synchronization
GPU/CPU synchronization
Compiler memory barriers
```

The key boundary continues naturally:

```text
BOOTSTRAP-607
    = scheduling and executing work

BOOTSTRAP-608
    = safely coordinating concurrent work
```

:::

**BOOTSTRAP-607 đã hoàn tất. Chuỗi tiếp theo là BOOTSTRAP-608.**