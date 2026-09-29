:::writing{variant="document" id="74163" title="BOOTSTRAP-608 — Native Synchronization, Atomics, Channels, Lock-Free Structures & Concurrency Memory Semantics 5.0"}

# BOOTSTRAP-608 — Native Synchronization, Atomics, Channels, Lock-Free Structures & Concurrency Memory Semantics 5.0

**Status:** ARCHITECTURE SPECIFICATION  
**Layer:** Core Concurrency / Native Runtime  
**Depends on:** BOOTSTRAP-600 → 607  
**Primary concern:** Synchronization, atomicity, memory ordering, blocking/wakeup, channels, lock-free algorithms and concurrent memory reclamation.

---

# 1. Purpose

BOOTSTRAP-608 defines the synchronization foundation used by Axiom applications, the runtime, executors, IPC, resource governor and compiler-generated concurrent code.

It answers:

- How do threads communicate safely?
- How are shared values synchronized?
- What does `atomic` mean in Axiom?
- What memory ordering guarantees exist?
- How are mutexes implemented?
- How do tasks wait without wasting CPU?
- How do channels provide backpressure?
- How can lock-free data structures safely reclaim memory?
- How are deadlocks detected?
- How does the compiler map concurrency semantics to native CPUs?

The architecture must provide both:

```text
simple application-level synchronization
```

and:

```text
low-level primitives suitable for implementing the Axiom runtime itself.
```

---

# 2. Design Goals

## G1 — Native semantics

Axiom synchronization primitives must map efficiently to:

- x86-64;
- ARM64;
- ARM32 where supported;
- RISC-V;
- WASM atomics;
- future architectures through compiler backends.

## G2 — Explicit semantics

Concurrency behavior must never depend on undocumented runtime behavior.

## G3 — Cheap uncontended operations

The common case:

```text
lock
critical section
unlock
```

must avoid a kernel transition.

## G4 — Efficient contention handling

Contended operations should transition to native OS wait mechanisms rather than spin indefinitely.

## G5 — Async compatibility

Synchronization must support both:

```text
thread blocking
```

and:

```text
task suspension
```

where appropriate.

## G6 — No mandatory GC

Concurrent memory management must work without tracing GC.

## G7 — No mandatory borrow checker

Synchronization safety must not require a global borrow-checking model.

## G8 — Precise memory model

The compiler must know exactly which operations establish:

```text
happens-before
```

relationships.

## G9 — Lock-free building blocks

Axiom must expose sufficient primitives to build:

- queues;
- rings;
- schedulers;
- allocators;
- channels;
- concurrent maps;
- reference counters.

## G10 — Resource integration

Synchronization resources are subject to BOOTSTRAP-606.

---

# 3. Non-Goals

This specification does not define:

- distributed consensus;
- transactional databases;
- distributed locks;
- cluster coordination;
- actor semantics;
- language-level parallel collection algorithms.

Those may be higher-level libraries.

---

# 4. Concurrency Model

Axiom recognizes:

```text
Thread concurrency
Task concurrency
Interrupt/event concurrency
GPU concurrency
IPC concurrency
```

All synchronization ultimately operates on a defined shared-memory or message-passing boundary.

---

# 5. Core Principle

Axiom follows:

```text
Shared mutable state
        ↓
must have an explicit synchronization strategy
```

The compiler should make synchronization visible rather than introducing hidden synchronization behind ordinary field access.

---

# 6. Data Access Categories

A value is conceptually one of:

```text
Immutable
Thread-local
Task-local
Synchronized shared
Atomic shared
Externally synchronized
Unsafe shared
```

The type/semantic system may use metadata to distinguish these categories.

---

# 7. Ordinary Shared Memory

Ordinary memory access:

```axiom
x = value
value = x
```

does not automatically become atomic.

If multiple threads access `x` concurrently and at least one modifies it, synchronization is required.

---

# 8. Atomic Values

Axiom provides:

```axiom
Atomic<T>
```

for supported atomic types.

Example:

```axiom
let counter: Atomic<u64> = 0
counter.fetch_add(1, AcqRel)
```

---

# 9. Supported Atomic Types

The minimum required set:

```text
Atomic<bool>
Atomic<u8>
Atomic<u16>
Atomic<u32>
Atomic<u64>
Atomic<i8>
Atomic<i16>
Atomic<i32>
Atomic<i64>
Atomic<usize>
Atomic<isize>
```

128-bit atomics are optional and target-dependent.

---

# 10. Atomic Pointer/Handle Values

Raw application pointers are not the preferred concurrency interface.

Instead, generation-safe handles may be atomic:

```text
Atomic<Handle<T>>
```

where the representation is compiler/runtime-defined.

---

# 11. Atomic Operations

Required:

```text
load
store
exchange
compare_exchange
compare_exchange_weak
fetch_add
fetch_sub
fetch_and
fetch_or
fetch_xor
```

Optional target-specific:

```text
fetch_max
fetch_min
```

---

# 12. Memory Orders

Axiom defines:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

These have semantics corresponding to the Axiom memory model.

---

# 13. Relaxed

`Relaxed` provides:

- atomicity;
- modification-order participation;
- no synchronization with unrelated memory.

Example:

```axiom
counter.fetch_add(1, Relaxed)
```

is suitable for statistical counters where ordering is irrelevant.

---

# 14. Release

A release operation prevents prior relevant memory operations from being reordered after publication.

Conceptually:

```text
write data
    ↓
Release store
```

---

# 15. Acquire

An acquire operation prevents subsequent relevant operations from being reordered before acquisition.

Typical pattern:

```text
producer:
    write data
    release(flag)

consumer:
    acquire(flag)
    read data
```

The consumer can then observe the published data according to the Axiom happens-before rules.

---

# 16. AcqRel

`AcqRel` combines:

```text
Acquire
+
Release
```

and is appropriate for read-modify-write operations requiring both directions.

---

# 17. Sequential Consistency

`SeqCst` provides the strongest ordering model.

Axiom defines one global total order for sequentially consistent operations consistent with their happens-before relationships.

It is correct but may be more expensive than weaker orders.

---

# 18. Default Atomic Ordering

Axiom must **not** silently assume `SeqCst` for every operation.

Default APIs should require explicit ordering where ambiguity would matter.

For convenience APIs, a high-level operation may define its own documented order.

Example:

```axiom
counter.increment()
```

could have a documented relaxed semantic.

---

# 19. Compiler Memory Model

The compiler must preserve:

```text
program order
+
synchronization order
+
atomic modification order
```

as defined by the language memory model.

Compiler optimizations must never introduce an observable execution forbidden by the model.

---

# 20. Data Race

A data race occurs when:

```text
two concurrent accesses
+
same memory location
+
at least one write
+
no valid synchronization
```

A data race on ordinary memory is undefined behavior unless the enclosing operation is explicitly marked unsafe.

---

# 21. Atomic Race-Free Rule

Concurrent accesses to an `Atomic<T>` are race-free with respect to the atomic object itself.

The associated non-atomic data still requires synchronization.

---

# 22. Synchronization Objects

Axiom provides:

```text
Mutex<T>
RwLock<T>
Semaphore
Event
Condition
Barrier
Latch
Once
```

---

# 23. Mutex

Core abstraction:

```axiom
struct Mutex<T> {
    state: MutexState
    value: T
}
```

API:

```axiom
function Mutex.lock(self) -> MutexGuard<T>
function Mutex.try_lock(self) -> Result<MutexGuard<T>>
function Mutex.lock_async(self) -> AsyncResult<MutexGuard<T>>
```

---

# 24. MutexGuard

The guard represents temporary ownership of the protected value.

Conceptually:

```axiom
let guard = mutex.lock()
guard.value += 1
```

The guard is released when its lexical scope ends.

---

# 25. Guard Lifetime

The compiler should ensure that a normal guard cannot accidentally cross an `await`.

Example:

```text
lock
 ↓
await
```

should normally be rejected because the task could migrate to another worker while holding the lock.

Explicit asynchronous lock semantics use a task-compatible guard.

---

# 26. Async Mutex

An async mutex suspends a task rather than blocking its OS worker.

```axiom
let guard = await mutex.lock_async()
```

Waiting tasks are maintained in an ordered/bounded waiter structure.

---

# 27. Async Mutex Rules

An async mutex:

- must not block an executor worker;
- must wake exactly one eligible waiter on unlock;
- must support cancellation;
- must avoid unbounded waiter allocation where possible.

---

# 28. Mutex Fast Path

Uncontended:

```text
CAS unlocked → locked
```

No kernel call.

Contended:

```text
short adaptive spin
 ↓
native wait primitive
```

---

# 29. Adaptive Spinning

Axiom may briefly spin when:

- owner is running;
- expected lock hold time is short;
- CPU topology makes spinning useful.

It must stop spinning under:

- excessive contention;
- resource pressure;
- single-core execution;
- background/energy-constrained mode.

---

# 30. OS Wait Primitive

The implementation should use the cheapest platform-native wait mechanism.

Examples include:

```text
Windows:
    WaitOnAddress / SRW/condition primitives

Linux:
    futex

macOS:
    ulock/condition mechanisms

WASM:
    atomic wait where supported
```

The exact backend remains platform-specific.

---

# 31. RWLock

`RwLock<T>` supports:

```text
multiple readers
one writer
```

API:

```axiom
read()
try_read()
write()
try_write()
read_async()
write_async()
```

---

# 32. Writer Starvation

The default implementation must use a defined fairness policy.

Recommended default:

```text
writer-preferred once a writer is queued
```

This prevents continuous readers from starving writers.

The policy must be documented and configurable where useful.

---

# 33. Semaphore

A semaphore represents a count of permits.

```axiom
struct Semaphore {
    permits: Atomic<usize>
}
```

Operations:

```axiom
acquire()
try_acquire()
release(n)
acquire_async()
```

---

# 34. Resource Integration

Semaphore permits may represent:

```text
connections
GPU slots
worker slots
file operations
memory buffers
```

For system resources, BOOTSTRAP-606 remains authoritative.

---

# 35. Event

An `Event` wakes one or more waiters.

Modes:

```text
AutoReset
ManualReset
```

Example:

```axiom
event.wait()
event.signal()
```

---

# 36. Condition Variable

A condition variable allows:

```text
wait until predicate becomes true
```

Pattern:

```axiom
lock(mutex)

while !condition() {
    cond.wait(mutex)
}

use_data()
```

The predicate must always be checked after wakeup.

---

# 37. Spurious Wakeups

The API explicitly permits spurious wakeups where mapped platform primitives do.

Therefore:

```text
wait()
```

never guarantees that the desired condition is true.

---

# 38. Barrier

A barrier waits until a fixed participant count reaches the synchronization point.

```axiom
barrier.wait()
```

The barrier may optionally support reusable phases.

---

# 39. Latch

A latch starts with a count:

```text
count = N
```

Each completion decrements it:

```text
count -= 1
```

Waiters continue when:

```text
count == 0
```

Unlike a reusable barrier, a latch is normally one-shot.

---

# 40. Once

A `Once` primitive guarantees one-time initialization.

```axiom
once.call(init)
```

All successful callers observe the initialized state according to acquire/release semantics.

---

# 41. Deadlock

Deadlock occurs when tasks/threads form a cycle of waiting dependencies.

Example:

```text
A waits B
B waits A
```

Axiom does not promise automatic deadlock prevention for arbitrary locks.

---

# 42. Lock Ordering

Higher-level APIs may declare lock ordering:

```text
@lock_order(10)
Mutex A

@lock_order(20)
Mutex B
```

The compiler/runtime can diagnose:

```text
B → A
```

when:

```text
A → B
```

is declared as the required order.

---

# 43. Deadlock Detection

Debug builds may maintain a wait-for graph:

```text
Thread
  ↓
Lock
  ↓
Owner
```

Cycle detection produces diagnostic information.

Production tracking is optional.

---

# 44. Priority Inheritance

Mutexes may support priority inheritance.

When:

```text
High priority task
       ↓
waiting for
       ↓
Low priority owner
```

the owner may temporarily inherit the higher scheduling priority.

This integrates with BOOTSTRAP-607.

---

# 45. Priority Ceiling

For specialized realtime applications, Axiom may support a priority-ceiling mode.

It requires appropriate scheduling capabilities.

---

# 46. SpinLock

A spin lock is available only as an explicit low-level primitive:

```axiom
SpinLock
```

It should be used for extremely short critical sections.

The API/documentation should warn against using it around:

- I/O;
- allocation;
- arbitrary function calls;
- `await`;
- long computations.

---

# 47. Interrupt-Safe Synchronization

Embedded profiles may expose:

```text
InterruptLock
AtomicInterruptGuard
```

only when the target platform supports them.

These are not portable general-purpose locks.

---

# 48. Atomic Flag

A minimal primitive:

```axiom
AtomicFlag
```

supports:

```text
test_and_set
clear
```

and is useful for:

- once initialization;
- simple spin locks;
- low-level runtime state.

---

# 49. Channels

Channels are the preferred synchronization mechanism when shared mutable state can be replaced with message passing.

```axiom
Channel<T>
```

supports:

```text
send
receive
try_send
try_receive
send_async
receive_async
```

---

# 50. Channel Ownership

A channel contains:

```text
buffer
sender state
receiver state
waiter lists
closure state
resource group
```

Channel handles are generation-safe.

---

# 51. Bounded Channel

```axiom
Channel<T>.bounded(1024)
```

When full:

```text
send()
```

blocks/suspends according to execution context.

---

# 52. Unbounded Channel

An unbounded channel is logically unbounded but physically constrained by:

```text
BOOTSTRAP-606 memory limits
```

Therefore it can return:

```text
ResourceDenied
```

rather than consuming unlimited memory.

---

# 53. Channel Closure

A sender may close its side.

When all senders disappear:

```text
receiver
 ↓
Closed
```

If buffered messages remain:

```text
receive()
```

continues until the buffer is empty.

---

# 54. Channel Backpressure

Bounded channels are the preferred mechanism for applying backpressure.

Example:

```text
producer
   ↓
bounded channel
   ↓
consumer
```

The producer automatically slows when the consumer cannot keep up.

---

# 55. Multi-Producer

A channel may support multiple producers.

The implementation must ensure:

```text
one message
→ one successful receive
```

for ordinary channels.

---

# 56. Multi-Consumer

Multiple consumers may receive from the same channel.

The channel must define ordering semantics.

---

# 57. Ordering

For a single producer:

```text
send(A)
send(B)
```

must be observed as:

```text
A
B
```

unless the channel explicitly uses an unordered mode.

For multiple producers, global order is not generally defined unless the channel provides serialization.

---

# 58. Select/Wait Set

Axiom should provide a unified wait mechanism:

```axiom
select {
    case x = await ch1.receive()
    case y = await ch2.receive()
    case _ = await timer.after(1s)
}
```

This lowers into a runtime wait-set representation.

---

# 59. Wait Set

A wait set can contain:

```text
channel
event
timer
I/O operation
cancellation token
```

The runtime waits for the first ready condition.

---

# 60. Wait-Set Race

When multiple events become ready simultaneously:

```text
```

the implementation must choose one according to defined selection semantics.

Deterministic executor mode must use deterministic selection.

---

# 61. Lock-Free Structures

Axiom provides primitive support for lock-free structures but does not require every standard container to be lock-free.

Possible primitives:

```text
Atomic
AtomicFlag
Atomic<Handle>
MemoryFence
```

---

# 62. Memory Fence

A low-level fence is available:

```axiom
fence(Acquire)
fence(Release)
fence(SeqCst)
```

Most application code should prefer atomic operations over standalone fences.

---

# 63. Compare-and-Exchange

CAS is the primary lock-free primitive:

```axiom
compare_exchange(
    expected,
    desired,
    success_order,
    failure_order
)
```

The compiler maps it to the target ISA.

---

# 64. Weak CAS

`compare_exchange_weak` may fail spuriously.

It is intended for loops:

```axiom
while !atomic.compare_exchange_weak(...) {
    retry
}
```

---

# 65. ABA Problem

A lock-free algorithm may observe:

```text
A → B → A
```

and incorrectly conclude that nothing changed.

Axiom provides generation-tagged handles to mitigate ABA:

```text
(index, generation)
```

rather than relying on raw pointer equality.

---

# 66. Tagged Atomic Handle

Conceptual:

```axiom
Atomic<Handle<T>>
```

where:

```text
Handle<T> = index + generation
```

This is the preferred lock-free reference mechanism for runtime-managed objects.

---

# 67. Hazard Pointers

For pointer-based low-level structures, Axiom runtime may provide:

```text
HazardDomain
HazardSlot
```

A thread announces objects it may dereference.

Objects are reclaimed only after no hazard references remain.

---

# 68. Epoch Reclamation

Alternative:

```text
EpochDomain
EpochGuard
```

Readers enter an epoch.

Retired objects are reclaimed only after all relevant readers have advanced.

---

# 69. Reclamation Strategy

Axiom should not mandate one global reclamation algorithm.

Supported runtime strategies:

```text
Generation handles
Reference counting
Hazard pointers
Epoch reclamation
Owner-based reclamation
```

The data structure selects the appropriate strategy.

---

# 70. Reference Counting

Reference counting is allowed for explicit ownership scenarios.

It is **not** the default memory-management model of Axiom.

Atomic reference counts use:

```text
fetch_add
fetch_sub
```

with appropriate ordering.

---

# 71. Cycle Handling

Reference counting does not automatically solve cycles.

Higher-level containers must use:

```text
weak handles
explicit ownership
acyclic graphs
```

where cycles matter.

Axiom does not introduce a mandatory cycle-detecting GC.

---

# 72. Concurrent Queue

The runtime should implement at least:

```text
MPSC queue
MPMC queue
SPSC ring buffer
```

using the primitives defined here.

---

# 73. SPSC Ring Buffer

Single-producer/single-consumer ring buffer can use:

```text
producer index
consumer index
```

with acquire/release ordering.

No CAS is necessary in the common design.

---

# 74. MPSC Queue

Multiple producers use atomic tail acquisition.

The consumer side may remain single-consumer for efficiency.

---

# 75. MPMC Queue

Multiple producers and consumers require stronger coordination.

The implementation must define:

- sequence counters;
- ownership;
- ABA strategy;
- memory reclamation.

---

# 76. Lock-Free Guarantee

If a structure is documented as:

```text
lock-free
```

at least one concurrent operation must make progress in a finite number of steps independent of another stalled thread, according to the formal definition used by the implementation.

The documentation must not use "lock-free" merely to mean "usually fast."

---

# 77. Wait-Free Guarantee

If documented as:

```text
wait-free
```

every operation must complete within a bounded number of its own steps.

Wait-free algorithms should be reserved for specialized primitives.

---

# 78. Progress Classes

Axiom recognizes:

```text
Blocking
Obstruction-free
Lock-free
Wait-free
```

APIs must state which guarantee applies.

---

# 79. Atomic Alignment

Atomic values must satisfy target-specific alignment requirements.

The compiler lays out:

```text
Atomic<T>
```

with sufficient alignment.

Misaligned atomic storage must be rejected or lowered safely according to target capabilities.

---

# 80. False Sharing

Axiom may provide:

```axiom
CacheAligned<T>
```

for low-level structures.

Example:

```axiom
struct Counters {
    producer: CacheAligned<Atomic<u64>>
    consumer: CacheAligned<Atomic<u64>>
}
```

---

# 81. Cache-Line Padding

Cache alignment is an optimization, not a semantic requirement.

The compiler may remove unnecessary padding when ABI constraints permit.

---

# 82. Synchronization and Memory Model

Lock operations establish synchronization automatically.

Conceptually:

```text
unlock
  Release

lock
  Acquire
```

for the same mutex.

Therefore data protected by a mutex becomes visible to a later lock holder.

---

# 83. RwLock Memory Semantics

Writer unlock publishes writes.

A later reader lock acquires those writes.

Readers must not modify protected data unless the API explicitly allows interior atomic mutation.

---

# 84. Semaphore Memory Semantics

Successful acquire after a corresponding release establishes the defined synchronization relation for the protected resource.

---

# 85. Channel Memory Semantics

Sending a message publishes the message contents.

Receiving the message acquires the message publication.

Therefore:

```text
producer writes message
send(message)
       ↓
receive()
       ↓
consumer reads message
```

is synchronized.

---

# 86. Event Memory Semantics

Signal/wait operations establish a defined release/acquire relationship.

An event is not merely a wakeup mechanism.

---

# 87. Condition Variable Semantics

Condition variables synchronize through the associated mutex.

Correct pattern:

```text
lock
check predicate
wait
reacquire
check predicate
```

---

# 88. Synchronization Resource Accounting

Each synchronization object may consume:

```text
memory
OS wait structures
kernel handles
waiter slots
```

These are accounted under BOOTSTRAP-606 where applicable.

---

# 89. Waiter Limits

A synchronization primitive may impose:

```text
max_waiters
```

to protect against resource exhaustion.

When exceeded:

```text
ResourceDenied
```

may be returned.

---

# 90. Cancellation of Waiters

Async waits support cancellation.

Example:

```axiom
await mutex.lock_async(token)
```

If cancellation wins the race:

```text
Cancelled
```

is returned.

The mutex must not accidentally grant ownership to the cancelled waiter.

---

# 91. Waiter State Machine

Every async waiter follows:

```text
Created
Queued
Woken
Cancelled
Granted
Completed
```

Only one terminal transition is allowed.

---

# 92. Wakeup Race

If:

```text
unlock
```

and:

```text
cancel
```

occur simultaneously, exactly one operation claims the waiter.

The other observes terminal state.

---

# 93. Lost Wakeup Prevention

The implementation must atomically establish:

```text
waiter registration
+
condition check
```

before sleeping.

This is essential for all wait primitives.

---

# 94. Native Wait/Notify

Where possible, Axiom uses:

```text
atomic state
+
OS wait/notify
```

rather than a heavyweight kernel object for every logical waiter.

---

# 95. Async vs Blocking Wait

A primitive must distinguish:

```text
lock()
```

from:

```text
lock_async()
```

because:

```text
lock()
```

may block an OS thread, while:

```text
lock_async()
```

suspends a logical task.

---

# 96. Incorrect Async Blocking

Diagnostics should detect or warn about:

```text
mutex.lock()
```

inside async code when static analysis knows the lock may contend.

The compiler should suggest:

```text
mutex.lock_async()
```

when appropriate.

---

# 97. Synchronous Context Using Async Primitive

Async locks may also be used from synchronous code through:

```text
blocking_wait
```

but this must be explicit.

The runtime must avoid accidental executor deadlocks.

---

# 98. Executor Interaction

BOOTSTRAP-607 uses:

```text
Mutex
Semaphore
Event
Channel
WaitSet
```

for worker scheduling and task coordination.

BOOTSTRAP-608 must not create a second incompatible scheduler.

---

# 99. Scheduler Queue Integration

Executor local queues may use specialized lock-free structures.

These structures can assume:

```text
known producer/consumer patterns
```

and therefore optimize beyond general MPMC channels.

---

# 100. IPC Integration

BOOTSTRAP-604 may use:

```text
Atomic
Mutex
Semaphore
Event
RingBuffer
```

for shared-memory IPC.

IPC synchronization must additionally obey capability/security rules from BOOTSTRAP-603.

---

# 101. Shared Memory Integration

Shared-memory structures require explicit synchronization.

Mapping memory does not automatically make accesses safe.

Example:

```text
SharedBuffer
+
SharedAtomic
```

must use a compatible memory model.

---

# 102. Cross-Process Atomics

Cross-process atomicity is platform-dependent.

Axiom must not guarantee it merely because:

```text
Atomic<T>
```

works between threads.

A shared-memory API must explicitly declare:

```text
process_shared = supported/unsupported
```

for each target.

---

# 103. Process-Shared Mutex

Where supported:

```axiom
ProcessMutex
```

may synchronize across processes.

Where unsupported, the API returns an explicit capability/platform error.

---

# 104. Security

Synchronization primitives do not themselves grant authority.

A task holding:

```text
Mutex
```

does not gain:

```text
filesystem capability
network capability
process capability
```

---

# 105. Capability Transfer

A synchronization object shared through IPC must be accompanied by the required capability/handle transfer rules from BOOTSTRAP-603/604.

---

# 106. Resource Governor Interaction

Under resource pressure:

```text
```

the runtime may limit:

- waiter allocation;
- channel growth;
- new synchronization objects;
- blocking worker creation.

Existing synchronization semantics must remain correct.

---

# 107. Memory Pressure

If a task cannot allocate a waiter record:

```text
```

the operation should fail or use a bounded fallback.

It must never corrupt the synchronization primitive.

---

# 108. Diagnostics

BOOTSTRAP-602 can record:

```text
lock contention
lock hold duration
wait duration
queue depth
semaphore saturation
channel backlog
deadlock candidates
atomic retry count
CAS failure count
```

These should be sampled or disabled in low-overhead builds.

---

# 109. Lock Identity

Every diagnostic-enabled synchronization object may have:

```text
SyncObjectId
Generation
Type
ResourceGroup
CreationLocation
```

This enables precise diagnostics without exposing raw memory addresses.

---

# 110. Contention Tracing

A diagnostic event:

```text
LOCK_WAIT
```

may include:

```text
object_id
task_id
worker_id
wait_duration
owner_id
```

Sensitive application data must not be included.

---

# 111. Deadlock Report

A debug report may resemble:

```text
Potential deadlock

Task A
  waits: Mutex 12
  owns:  Mutex 17

Task B
  waits: Mutex 17
  owns:  Mutex 12
```

The runtime reports evidence rather than asserting that every detected cycle necessarily represents an application deadlock.

---

# 112. Deterministic Scheduler Integration

BOOTSTRAP-607's deterministic executor controls:

```text
lock acquisition ordering
task wake ordering
channel selection
timer ordering
```

where multiple choices are otherwise valid.

---

# 113. Concurrency Model Testing

A deterministic test can explore:

```text
T1: write A
T2: read A
T1: unlock
T2: lock
```

and verify allowed/forbidden outcomes.

---

# 114. Stress Testing

Required tests include:

```text
10M atomic operations
high-contention mutex
reader/writer contention
channel saturation
mass cancellation
mass waiter wakeup
worker migration
executor shutdown
cross-thread task completion
```

Exact scale is target-dependent.

---

# 115. Fuzzing

Fuzz:

```text
lock/unlock sequences
CAS loops
channel send/receive/close
wait/cancel races
barrier participant counts
semaphore release/acquire
```

Invalid API sequences must return controlled errors or trigger documented programmer-error behavior.

---

# 116. Model Checking

Small-state model checking should verify:

```text
no double grant
no lost wakeup
no double completion
no channel duplication
no channel message loss within defined semantics
no impossible lock state
```

---

# 117. Memory Model Tests

Compiler/runtime test suites must validate:

```text
Acquire
Release
AcqRel
SeqCst
Relaxed
```

on all supported architectures.

Tests should include weak-memory targets such as ARM64.

---

# 118. Architecture Litmus Tests

Axiom should maintain a litmus-test suite covering:

```text
Store Buffering
Load Buffering
Message Passing
IRIW
CAS ordering
publication
```

The expected results are derived from the Axiom memory model.

---

# 119. Compiler Reordering Tests

Compiler optimizations must not invalidate synchronization.

Tests should compile concurrent programs at:

```text
O0
O1
O2
O3
LTO
PGO
```

and verify allowed semantics.

---

# 120. Atomic ABI

The compiler defines canonical ABI representations for:

```text
Atomic<T>
```

including:

```text
size
alignment
lock-free status
required runtime fallback
```

---

# 121. Non-Lock-Free Atomics

Some target/type combinations may not have native lock-free instructions.

Axiom may implement them using a runtime fallback.

Example:

```text
Atomic<128-bit>
```

may use a hidden runtime lock.

The type metadata must expose:

```text
is_lock_free()
```

where meaningful.

---

# 122. No False Lock-Free Claims

The compiler must never label an implementation lock-free if it internally depends on a blocking global lock.

---

# 123. Atomic Initialization

Static atomic objects are initialized without requiring runtime startup where possible.

This supports:

```text
static Atomic<u64>
```

in early runtime initialization.

---

# 124. Constant Initialization

If an atomic can be represented entirely by constant initialization, the compiler should emit it directly into the binary.

---

# 125. Mutex Initialization

A statically initialized mutex should not require dynamic initialization.

Example:

```axiom
static GLOBAL_LOCK: Mutex<State>
```

must be supported where `State` initialization is constant.

---

# 126. Destruction

Synchronization objects with static lifetime should not require shutdown code unless they contain dynamically allocated resources.

This improves native binary simplicity.

---

# 127. Panic Safety

If Axiom's failure mechanism unwinds or aborts through a critical section:

```text
```

the mutex must not remain permanently locked if the language guarantees cleanup.

The exact behavior follows the language's resource-cleanup semantics.

---

# 128. Async Guard Cleanup

An async synchronization guard must release ownership when the task is cancelled or fails, provided the guard's ownership semantics permit cleanup.

---

# 129. No Await While Ordinary Mutex Held

Default compiler rule:

```text
ordinary MutexGuard
    ↓
await
```

is invalid.

This is a semantic safety rule designed to prevent executor starvation/deadlock.

---

# 130. Explicit Override

Low-level runtime code may use:

```axiom
unsafe {
    await while_holding_lock()
}
```

only when the developer explicitly assumes responsibility.

The compiler should emit a diagnostic.

---

# 131. Synchronization Ownership

Synchronization objects themselves are values.

No raw pointer is required in ordinary code.

Example:

```axiom
let lock = Mutex<State>.new(state)
```

Methods use the first parameter convention:

```axiom
function lock(self: Mutex<State>) -> MutexGuard<State>
```

---

# 132. No Classes

All synchronization primitives use Axiom's struct-only model.

There are no special synchronization classes.

Example:

```axiom
struct Mutex<T> { ... }

function lock(self: Mutex<T>) -> MutexGuard<T>
```

---

# 133. Trait Integration

Axiom may define traits such as:

```text
Send
Sync
AtomicCompatible
Waitable
```

These are semantic traits, not classes.

---

# 134. `Send`

A type implementing `Send` may be transferred between execution contexts according to Axiom ownership rules.

---

# 135. `Sync`

A type implementing `Sync` may be safely shared according to its documented synchronization semantics.

The exact trait inference rules belong to the core type/semantic specification.

---

# 136. Non-Send Types

A value tied to:

```text
UI thread
specific OS thread
device context
thread-local state
```

may be marked non-Send.

The compiler should prevent accidental migration.

---

# 137. Thread-Affine Types

A type can declare:

```text
ThreadAffine
```

meaning it must remain on its owning thread.

This integrates with BOOTSTRAP-607 affinity scheduling.

---

# 138. Task-Affine Types

Some resources may be task-local rather than thread-local.

Such values cannot be freely transferred to another task.

---

# 139. Synchronization Trait Examples

Conceptual:

```axiom
trait Send {}
trait Sync {}
trait ThreadAffine {}
trait TaskAffine {}
```

The compiler uses these as semantic constraints.

---

# 140. Atomic Trait

A type is atomically usable only if its representation satisfies:

```text
known size
known alignment
supported atomic operations
```

The compiler rejects unsupported atomic types unless a runtime-backed atomic implementation exists.

---

# 141. Channel Type Safety

A channel:

```axiom
Channel<T>
```

transfers ownership of `T`.

If `T` is not `Send`, cross-thread channel transmission is rejected.

---

# 142. Mutex Type Safety

A `Mutex<T>` may protect any valid `T`.

However, transferring the mutex itself between threads requires the appropriate synchronization traits.

---

# 143. RwLock Safety

Concurrent readers require `T` to satisfy the required shared-access trait.

Writers require exclusive access.

---

# 144. Atomic Memory Layout

The compiler must prevent accidental field tearing for atomic types.

An atomic operation always accesses the entire atomic value according to its declared width.

---

# 145. Partial Access

Applications cannot take a normal field reference into an atomic object and then mutate it non-atomically.

The compiler must reject representation-breaking access.

---

# 146. Channel Serialization

Channels transfer typed values directly in-process.

No serialization is required.

IPC channels from BOOTSTRAP-604 are separate and may serialize/encode values.

---

# 147. Same-Process Zero Copy

A channel may transfer:

```text
OwnedBuffer
SharedBuffer
Handle<T>
```

without copying payload bytes.

Lifetime remains explicit.

---

# 148. MPSC Optimization

If the compiler can prove:

```text
one producer
```

it may select an SPSC implementation automatically.

Such specialization must preserve the channel's public semantics.

---

# 149. Static Concurrency Optimization

The compiler may detect:

```text
single-thread execution
```

and replace some synchronization with simpler operations when it can prove no concurrent access exists.

This must not alter behavior if concurrency is introduced dynamically.

---

# 150. Thread Sanitizer Integration

Axiom toolchains should support a race-detection instrumentation mode.

The implementation may integrate with platform/compiler sanitizer infrastructure while keeping the normal runtime dependency-free.

---

# 151. Lock Sanitizer

A diagnostic mode can track:

```text
lock acquisition order
unlock correctness
recursive locking
double unlock
```

---

# 152. Channel Sanitizer

Debug mode can detect:

```text
use after close
double close
invalid sender
invalid receiver
message lifecycle errors
```

---

# 153. Atomic Sanitizer

Diagnostics may report:

```text
unexpected CAS failure rate
contention
misaligned access
unsupported atomic width
```

---

# 154. API Error Semantics

Typical errors:

```text
WouldBlock
Cancelled
Closed
Timeout
ResourceDenied
InvalidState
InvalidHandle
Unsupported
```

---

# 155. Non-Blocking API

Every blocking primitive should expose a `try_` form when meaningful.

Example:

```axiom
mutex.try_lock()
semaphore.try_acquire()
channel.try_send()
channel.try_receive()
```

This allows scheduler/runtime internals to avoid unintended blocking.

---

# 156. Timeout API

Blocking primitives may expose:

```text
lock_until(deadline)
acquire_until(deadline)
receive_until(deadline)
```

These integrate with BOOTSTRAP-607's timer service.

---

# 157. Timeout + Cancellation

Operations may accept both:

```text
deadline
+
CancelToken
```

The first terminal condition wins.

---

# 158. Wait Outcome

A common result type:

```text
WaitResult =
    Acquired
    Timeout
    Cancelled
    Closed
```

can reduce duplicated runtime logic.

---

# 159. Fairness Policy

Each synchronization primitive must document whether it provides:

```text
FIFO fairness
bounded fairness
weak fairness
no fairness guarantee
```

The implementation must not imply FIFO behavior unless guaranteed.

---

# 160. Channel Fairness

A bounded channel should avoid indefinite starvation among waiting senders/receivers.

A fair queue is preferred unless a specialized performance mode is explicitly selected.

---

# 161. Semaphore Fairness

The default semaphore may use FIFO waiter order where practical.

Under high contention, exact ordering may be relaxed to improve throughput.

The semantic contract must state the actual guarantee.

---

# 162. Mutex Fairness

Axiom does not require strict FIFO mutex acquisition because that can reduce performance.

It does require that the implementation not intentionally create unbounded starvation under its documented fairness policy.

---

# 163. Scheduler Interaction

Synchronization wakeups must submit resumed tasks to the appropriate executor.

Example:

```text
mutex unlock
 ↓
wake task
 ↓
executor.enqueue(task)
```

The unlock path should avoid running arbitrary user code synchronously.

---

# 164. Wakeup Coalescing

If multiple signals happen before a worker wakes:

```text
```

the runtime should coalesce unnecessary wakeups.

---

# 165. Thundering Herd Prevention

A single-resource wake should normally wake:

```text
one waiter
```

rather than all waiters.

Broadcast is reserved for conditions where multiple waiters may legitimately proceed.

---

# 166. Event Broadcast

Manual-reset events may wake multiple waiters.

The runtime should avoid repeatedly issuing unnecessary OS wakeups after the event is already signaled.

---

# 167. Condition Broadcast

`notify_all()` is available.

It is intended for predicates where many waiters may become eligible.

---

# 168. Lock Upgrade/Downgrade

`RwLock` may support:

```text
read → write upgrade
write → read downgrade
```

Upgrade must define behavior when multiple readers attempt upgrade simultaneously.

Default recommendation:

```text
upgrade may fail
```

rather than silently deadlock.

---

# 169. Recursive Mutex

Recursive mutexes are not the default.

A separate:

```text
RecursiveMutex<T>
```

may be provided for compatibility with APIs requiring recursion.

Normal `Mutex` should detect accidental recursive locking in diagnostics.

---

# 170. Reentrant Async Locks

Async recursive locking is discouraged because task ownership and cancellation semantics become complex.

Axiom does not require it in the core runtime.

---

# 171. Barrier Failure

If a participant is cancelled or fails, a reusable barrier must have an explicit failure policy.

Possible state:

```text
Broken
```

so remaining waiters do not deadlock indefinitely.

---

# 172. Semaphore Closure

A semaphore is normally not closable.

If resource ownership is revoked, the higher-level resource manager handles revocation.

---

# 173. Once Failure

If initialization fails:

```text
```

the `Once` state must specify whether subsequent calls retry or observe permanent failure.

Default:

```text
retry after failure
```

unless explicitly configured as permanent.

---

# 174. Lock Hierarchy Metadata

Compiler metadata may encode:

```text
AXLOCK {
    object
    rank
    source_location
}
```

Debug runtime uses it for lock-order validation.

---

# 175. Async Waiter Storage

Waiters should preferably use:

```text
executor/task frame storage
```

rather than separate heap allocations where the compiler can prove safe lifetime.

---

# 176. Fast Wake Path

If the waiting task remains on the same worker:

```text
wake
```

may directly enqueue into that worker's local queue.

Cross-worker wake uses the appropriate remote submission path.

---

# 177. Same-Worker Optimization

The scheduler may resume a ready task immediately after releasing a synchronization primitive when safe and profitable.

It must not execute arbitrary user code recursively inside the synchronization operation if that could create unbounded call depth.

---

# 178. Deferred Wake

An implementation may instead enqueue the waiter and return immediately.

This is the preferred safe default for complex wakeups.

---

# 179. Memory Reclamation and Waiters

A synchronization object cannot be destroyed while waiters still reference it.

Ownership must enforce:

```text
object lifetime
>
waiter lifetime
```

---

# 180. Destruction Rules

Destroying a synchronization object with active waiters is normally a programmer error.

Debug builds should report:

```text
SyncObjectDestroyedWhileWaited
```

Release behavior must be defined rather than left as accidental memory corruption.

---

# 181. Safe Destruction Pattern

Preferred:

```text
close
cancel waiters
join/drain
destroy
```

This integrates with structured concurrency.

---

# 182. Runtime Internal Use

BOOTSTRAP-608 primitives are used by:

```text
BOOTSTRAP-607 Executor
BOOTSTRAP-606 Resource Governor
BOOTSTRAP-605 Supervisor
BOOTSTRAP-604 IPC
BOOTSTRAP-602 Diagnostics
```

Therefore they must not depend on higher application-level modules.

---

# 183. Dependency Rule

Allowed:

```text
608
 ↓
platform primitives
compiler atomics
memory model
```

Higher runtime layers may consume 608.

BOOTSTRAP-608 must not depend on:

```text
service supervisor
application framework
GUI
network stack
```

---

# 184. Minimal Synchronization Runtime

The smallest Axiom executable requiring synchronization should be able to link:

```text
atomic
mutex
wait/notify
```

without pulling in:

```text
IPC
networking
GPU
full diagnostics
```

---

# 185. Static Linking

Synchronization runtime components should be statically linkable.

Unused primitives must be removable through:

```text
section GC
LTO
dead code elimination
```

---

# 186. Dynamic Libraries

When Axiom builds a shared library, synchronization ABI must remain stable according to the declared ABI version.

---

# 187. ABI Versioning

Runtime synchronization ABI includes:

```text
version
target
atomic ABI
sync object ABI
wait ABI
```

ABI changes require explicit versioning.

---

# 188. FFI

C-compatible wrappers may expose:

```text
axiom_mutex
axiom_atomic_u64
axiom_channel
```

but the native Axiom representation remains preferred.

---

# 189. FFI Lock Ownership

A foreign function must not unlock an Axiom mutex unless it receives an explicitly compatible ABI handle.

The runtime must reject mismatched ownership.

---

# 190. Foreign Threads

Foreign threads must register with the runtime before participating in task-aware synchronization where required.

This follows BOOTSTRAP-607's external thread attachment model.

---

# 191. Platform Backend Interface

Core synchronization uses platform traits:

```axiom
trait AtomicBackend
trait WaitBackend
trait ThreadSyncBackend
trait ProcessSyncBackend
```

Platform implementations remain replaceable.

---

# 192. Backend Selection

Compile time:

```text
target architecture
+
OS
+
available CPU instructions
```

selects the backend.

Runtime detection may select optional instruction paths.

---

# 193. CPU Feature Optimization

If supported:

```text
x86:
    CMPXCHG
    XADD
    WAITPKG

ARM:
    LDXR/STXR
    WFE/SEV

RISC-V:
    AMO
```

The compiler may emit specialized paths.

---

# 194. Portable Fallback

Every required synchronization operation must have a portable fallback using:

```text
atomic primitives
+
OS wait facilities
```

where native specialized instructions are unavailable.

---

# 195. Memory Barrier Cost

The compiler should use the weakest memory order required by the program semantics.

Library authors must avoid unnecessary `SeqCst`.

---

# 196. Compiler Intrinsics

Low-level Axiom code may access:

```text
atomic_load
atomic_store
atomic_cas
fence
cpu_pause
cpu_yield
```

through stable compiler intrinsics.

---

# 197. Unsafe Concurrency

Unsafe code may access raw memory and custom synchronization.

However:

```text
unsafe
```

does not disable atomic hardware semantics.

The compiler still must generate the requested memory order.

---

# 198. Compile-Time Diagnostics

Examples:

```text
AX60801:
data race candidate

AX60802:
await while holding synchronous mutex

AX60803:
atomic width unsupported

AX60804:
invalid memory order

AX60805:
non-Send value transferred across task boundary

AX60806:
synchronization object destroyed while active
```

---

# 199. Invalid Memory Orders

Examples rejected:

```text
store(..., Acquire)
load(..., Release)
```

because these combinations are semantically invalid for the corresponding operation.

The compiler should report the error rather than silently changing the requested ordering.

---

# 200. Final Architecture

```text
                         Axiom Concurrency
                                │
             ┌──────────────────┼──────────────────┐
             │                  │                  │
          Atomics          Synchronization       Channels
             │                  │                  │
      ┌──────┼──────┐      ┌────┼────┐       ┌─────┼─────┐
      │      │      │      │    │    │       │     │     │
   Memory   CAS   Fence   Mutex RWLock Sem  SPSC  MPSC  MPMC
    Order                 Event Cond  Barrier
      │
      ▼
 Compiler Memory Model
      │
      ▼
 Native ISA
      │
 ┌────┼─────────────┬─────────────┐
 ▼    ▼             ▼             ▼
x86  ARM           RISC-V        WASM
```

Integrated with:

```text
BOOTSTRAP-607
    Scheduler / Executor
          │
          ▼
BOOTSTRAP-608
    Synchronization
          │
    ┌─────┼──────┐
    ▼     ▼      ▼
  606   604     603
Resource IPC   Security
```

---

# 201. Core Concurrency Philosophy

Axiom's concurrency model is therefore:

```text
                 ┌───────────────┐
                 │ Immutable Data│
                 └───────┬───────┘
                         │
             no synchronization needed
                         │
        ┌────────────────┴────────────────┐
        ▼                                 ▼
   Message Passing                  Shared State
        │                                 │
     Channel                        Synchronization
        │                                 │
        │                  ┌──────────────┼──────────────┐
        │                  ▼              ▼              ▼
        │                Mutex          Atomic         RwLock
        │                  │              │
        └──────────────────┴──────────────┘
                         │
                  Memory Model
                         │
                         ▼
                    Native CPU
```

The language should encourage **ownership transfer and message passing for complex concurrent workflows**, while still exposing efficient shared-memory primitives for performance-critical code.

---

# 202. Key Architectural Decisions

### Decision 1

No mandatory GC is introduced by concurrency.

### Decision 2

No mandatory borrow checker is introduced by concurrency.

### Decision 3

Atomic operations have explicit memory-order semantics.

### Decision 4

Ordinary memory is not automatically atomic.

### Decision 5

Synchronous locks and asynchronous locks are distinct operations.

### Decision 6

`await` while holding an ordinary synchronous lock is rejected by default.

### Decision 7

Channels provide a first-class alternative to shared mutable state.

### Decision 8

Lock-free structures are supported but not universally required.

### Decision 9

Generation-safe handles are preferred over exposed raw pointers for runtime-managed concurrent objects.

### Decision 10

Memory reclamation strategies remain implementation-selectable.

### Decision 11

Synchronization resources participate in the unified BOOTSTRAP-606 resource model.

### Decision 12

The compiler is responsible for lowering atomics and memory orders directly to the target architecture.

---

# 203. Acceptance Criteria

BOOTSTRAP-608 is complete when:

1. Axiom defines its atomic memory model.
2. Relaxed ordering is defined.
3. Acquire ordering is defined.
4. Release ordering is defined.
5. AcqRel ordering is defined.
6. SeqCst ordering is defined.
7. Atomic operations are specified.
8. CAS semantics are specified.
9. Weak CAS semantics are specified.
10. Atomic alignment is specified.
11. Unsupported atomic widths are handled.
12. Memory fences are specified.
13. Mutex is specified.
14. Async mutex is specified.
15. RWLock is specified.
16. Semaphore is specified.
17. Event is specified.
18. Condition variable is specified.
19. Barrier is specified.
20. Latch is specified.
21. Once initialization is specified.
22. Blocking and async waiting are distinguished.
23. Cancellation races are specified.
24. Timeout behavior is specified.
25. Lost wakeups are prevented.
26. Double wake/grant is prevented.
27. Channel semantics are specified.
28. Bounded channel backpressure is specified.
29. Channel closure is specified.
30. Message ordering is specified.
31. Select/wait-set semantics are specified.
32. SPSC structures are supported.
33. MPSC structures are supported.
34. MPMC structures are supported.
35. ABA mitigation is specified.
36. Memory reclamation is specified.
37. Hazard pointers are supported as an option.
38. Epoch reclamation is supported as an option.
39. Generation-safe handles are supported.
40. Lock-free semantics are formally defined.
41. Wait-free semantics are formally defined.
42. Priority inversion handling is integrated.
43. Deadlock diagnostics are specified.
44. Lock-order diagnostics are specified.
45. Task/worker wakeups integrate with BOOTSTRAP-607.
46. Resource accounting integrates with BOOTSTRAP-606.
47. Capability semantics remain compatible with BOOTSTRAP-603.
48. Shared-memory IPC integrates with BOOTSTRAP-604.
49. Diagnostics integrate with BOOTSTRAP-602.
50. Static linking/dead stripping are supported.
51. FFI ABI is defined.
52. Deterministic concurrency testing is supported.
53. Weak-memory architecture tests are required.
54. Race/stress/fuzz tests are required.
55. No mandatory GC is introduced.
56. No mandatory borrow checker is introduced.
57. No raw pointer API is required for ordinary concurrent application code.
58. Struct-only Axiom API is supported.
59. Synchronization objects have safe lifetime rules.
60. The specification is sufficient to implement the first native synchronization runtime.

---

# 204. Completion Status

**BOOTSTRAP-608 — COMPLETED**

The Axiom runtime now has a defined foundation for:

```text
600  State / Checkpoint / Recovery
601  Configuration / Secrets / Deployment
602  Diagnostics / Crash / Observability
603  Security / Capabilities / Permissions
604  IPC / Shared Memory / Message Transport
605  Process / Service Supervision
606  Resources / Quotas / Budgets / Governor
607  Scheduling / Threads / Async / Executors
608  Synchronization / Atomics / Channels / Memory Semantics
```

The next layer can therefore build networking and higher-level communication without having to redefine thread synchronization or memory-ordering semantics.

---

# Next Architecture Task

**BOOTSTRAP-609 — Native Networking, Sockets, DNS, TLS Boundary, HTTP Transport & Network I/O Runtime 5.0**

Scope:

```text
Network Address Model
IPv4 / IPv6
TCP
UDP
QUIC boundary
Unix Domain Sockets
Windows Named/Native Sockets
Socket Lifecycle
Async Socket I/O
DNS Resolver
Connection Pooling
Backpressure
Zero-Copy Network Buffers
Network Resource Budgets
Capabilities
TLS abstraction boundary
Certificate/Trust abstraction
Proxy support
HTTP transport foundation
WebSocket foundation
Multicast/Broadcast
Network diagnostics
Network fault injection
WASM networking host boundary
Mobile networking constraints
```

**BOOTSTRAP-609** sẽ xây lớp networking native trên nền `607 + 608`, đồng thời giữ TLS/HTTP ở ranh giới module để Axiom core không bị khóa vào một thư viện mạng bên thứ ba.
:::

Đã hoàn tất **BOOTSTRAP-608**. Chuỗi kiến trúc tự động chuyển sang **BOOTSTRAP-609**.