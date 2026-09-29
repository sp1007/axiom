Tiếp tục chuỗi đặc tả Axiom với **BOOTSTRAP-606**, tập trung xây dựng một Resource Governor thống nhất để toàn bộ runtime dùng chung một mô hình quota/budget thay vì mỗi subsystem tự quản lý tài nguyên riêng.

:::writing{variant="document" id="58341" title="BOOTSTRAP-606 — Native Application Resource Management, Quotas, Budgets, Scheduling & Runtime Resource Governor 5.0"}

# BOOTSTRAP-606
## Native Application Resource Management, Quotas, Budgets, Scheduling & Runtime Resource Governor 5.0

**Status:** Architecture Specification  
**Phase:** Native Runtime / Application Platform  
**Depends on:** BOOTSTRAP-600, 601, 602, 603, 604, 605  
**Primary role:** Unified resource accounting, limits, quotas, reservations, admission control and runtime governance for the entire Axiom application stack.

---

# 606.0 — Purpose

Axiom shall provide one unified **Resource Governor** responsible for controlling, accounting for and coordinating runtime resources used by:

- Application
- Services
- Processes
- Threads
- Tasks
- IPC
- Shared memory
- Files
- Network I/O
- Storage
- GPU
- Timers
- OS handles
- Memory
- CPU
- child processes

The objective is not merely preventing resource exhaustion.

The Resource Governor shall provide:

1. deterministic resource accounting;
2. explicit ownership;
3. hierarchical quotas;
4. hard limits;
5. soft limits;
6. reservations;
7. burst capacity;
8. admission control;
9. pressure detection;
10. resource reclamation;
11. fairness;
12. priority-aware allocation;
13. service isolation;
14. application-level resource budgets;
15. platform-specific enforcement;
16. diagnostic visibility;
17. security integration;
18. supervisor integration.

The architecture shall prevent BOOTSTRAP-601 through BOOTSTRAP-605 from independently inventing incompatible resource-limit systems.

---

# 606.1 — Core Design Principle

Axiom shall use the following hierarchy:

```text
OS / Hardware
      │
      ▼
Platform Resource Adapter
      │
      ▼
Axiom Resource Governor
      │
      ├── Application Budget
      │
      ├── Resource Groups
      │      ├── Service
      │      ├── Process
      │      ├── Worker
      │      └── Task
      │
      ├── CPU
      ├── Memory
      ├── Threads
      ├── Handles
      ├── IPC
      ├── Shared Memory
      ├── GPU
      ├── I/O
      ├── Storage
      ├── Timers
      └── Process Count
      │
      ▼
Runtime / Services / Processes
```

Every resource-consuming subsystem shall report to the same governor.

---

# 606.2 — Resource Classes

Axiom shall define a canonical resource taxonomy.

## 606.2.1 Compute

```text
CPU_TIME
CPU_CORES
CPU_PRIORITY
CPU_AFFINITY
GPU_COMPUTE
GPU_STREAMS
GPU_CONTEXTS
```

## 606.2.2 Memory

```text
VIRTUAL_MEMORY
RESIDENT_MEMORY
SHARED_MEMORY
MAPPED_MEMORY
PINNED_MEMORY
STACK_MEMORY
GPU_MEMORY
```

## 606.2.3 Execution Objects

```text
PROCESS
THREAD
TASK
FIBER
HANDLE
FILE_DESCRIPTOR
ASYNC_OPERATION
```

## 606.2.4 Communication

```text
IPC_CHANNEL
IPC_QUEUE
IPC_MESSAGE
IPC_BYTES
SHARED_BUFFER
SOCKET
```

## 606.2.5 I/O

```text
FILE_IO
NETWORK_IO
DISK_IO
IOPS
BANDWIDTH
```

## 606.2.6 Time/Event

```text
TIMER
EVENT
WAKEUP
SCHEDULED_OPERATION
```

## 606.2.7 Storage

```text
DISK_SPACE
TEMP_SPACE
CACHE_SPACE
PERSISTENT_STORAGE
```

---

# 606.3 — Resource Identity

Every governed resource shall have a typed identity.

Conceptually:

```text
ResourceId<T>
```

Examples:

```text
ResourceId<Cpu>
ResourceId<Memory>
ResourceId<Thread>
ResourceId<IpcChannel>
ResourceId<GpuMemory>
```

Resource IDs shall not expose raw pointers.

A resource identity shall contain sufficient information for safe validation.

Recommended internal representation:

```text
ResourceId {
    index: u32
    generation: u32
}
```

The generation prevents stale-handle reuse.

---

# 606.4 — Resource Scope

Every resource allocation shall belong to a **Resource Scope**.

Canonical scopes:

```text
System
Deployment
Application
ResourceGroup
Service
Process
Worker
Task
```

Example:

```text
System
 └── Deployment
      └── Application
           ├── Service A
           │    ├── Process A1
           │    └── Process A2
           │
           └── Service B
                └── Process B1
```

Resource limits shall normally propagate downward.

A child may never automatically exceed an ancestor's effective hard limit.

---

# 606.5 — Resource Group

Resource groups provide explicit accounting and isolation.

```text
ResourceGroup {
    id: ResourceGroupId
    parent: Option<ResourceGroupId>

    cpu: ResourcePolicy
    memory: ResourcePolicy
    threads: ResourcePolicy
    handles: ResourcePolicy
    ipc: ResourcePolicy
    gpu: ResourcePolicy
    io: ResourcePolicy
    storage: ResourcePolicy
}
```

A group can contain:

- processes;
- services;
- workers;
- tasks.

This permits a complete service tree to share one budget.

---

# 606.6 — Budget

A **Budget** represents how much of a resource may be consumed over a defined accounting period.

Examples:

```text
CpuBudget
MemoryBudget
IoBudget
GpuBudget
StorageBudget
```

CPU budget example:

```text
cpu:
    period = 100ms
    quota = 40ms
```

Meaning:

> The scope may consume approximately 40 ms of CPU execution during each 100 ms accounting period.

---

# 606.7 — Quota

A quota is a maximum resource quantity.

Example:

```text
memory.max = 512 MiB
threads.max = 32
processes.max = 8
ipc.queue.max_bytes = 16 MiB
```

A quota can be:

```text
Hard
Soft
Reserved
Burst
```

---

# 606.8 — Hard Limit

A hard limit shall never be exceeded unless the platform itself cannot enforce the exact boundary.

Examples:

```text
threads <= 32
processes <= 8
memory <= 512 MiB
ipc_bytes <= 16 MiB
```

When allocation would exceed a hard limit, the governor shall reject, block, defer or reclaim according to resource semantics.

It shall never silently exceed the limit.

---

# 606.9 — Soft Limit

Soft limits provide pressure thresholds.

Example:

```text
memory:
    soft = 384 MiB
    hard = 512 MiB
```

At 384 MiB:

```text
pressure = Warning
```

The runtime may:

- trim caches;
- reduce prefetching;
- release idle buffers;
- lower concurrency;
- defer optional operations.

---

# 606.10 — Reservation

A reservation represents resources guaranteed for future use.

Example:

```text
reserve memory 128 MiB
reserve 4 threads
reserve gpu_memory 256 MiB
```

Reservation prevents another scope from consuming resources that have already been promised.

Actual usage remains separately accounted.

```text
reserved != used
```

---

# 606.11 — Burst Capacity

Some resources benefit from controlled temporary bursts.

Example:

```text
memory:
    hard = 512 MiB
    burst = 64 MiB
    burst_duration = 500ms
```

Burst capacity shall:

- be explicitly configured;
- be bounded;
- be observable;
- never violate an ancestor hard limit;
- optionally require a capability.

Burst consumption shall be charged to the requesting scope.

---

# 606.12 — Budget Borrowing

A child resource group may temporarily borrow unused capacity from a parent-managed pool.

Conceptually:

```text
available = parent_limit - committed_usage
```

Borrowing shall never permit:

```text
child_usage > parent_hard_limit
```

Borrowed resources shall be revocable.

This mechanism is useful for:

- temporary CPU spikes;
- compilation;
- rendering;
- network bursts;
- GPU inference;
- file operations.

---

# 606.13 — Resource Policy

Canonical policy:

```text
ResourcePolicy {
    minimum: Quantity
    reserved: Quantity

    soft_limit: Quantity
    hard_limit: Quantity

    burst_limit: Quantity
    burst_window: Duration

    priority: ResourcePriority

    reclaim: ReclaimPolicy
}
```

All fields are optional where a resource does not support them.

---

# 606.14 — Typed Units

Resource quantities shall use strongly typed units.

Examples:

```text
512.MiB
2.GiB

100.ms
2.s

50.MBps
100.MBps

4.threads
2.processes

30.percent
```

The compiler shall reject invalid dimensional operations.

For example:

```text
5.GiB + 10.ms
```

shall be invalid.

---

# 606.15 — CPU Governance

CPU governance shall support:

```text
CPU quota
CPU reservation
CPU weight
CPU priority
CPU affinity
CPU group
CPU burst
CPU accounting
```

Example:

```text
cpu:
    quota = 40%
    reservation = 10%
    weight = 100
```

---

# 606.16 — CPU Accounting

CPU usage shall be measured in CPU time, not wall-clock time.

Conceptually:

```text
cpu_used = sum(thread_cpu_time)
```

For multi-core execution:

```text
8 cores × 100 ms
```

represents up to:

```text
800 ms CPU time
```

during a 100 ms wall-clock interval.

---

# 606.17 — CPU Priority

Axiom shall distinguish:

```text
SchedulingPriority
ResourcePriority
SecurityAuthority
```

These are independent.

High priority shall not automatically grant:

- more memory;
- more capabilities;
- more file access;
- more network access.

This prevents priority escalation from becoming privilege escalation.

---

# 606.18 — CPU Affinity

A process/service may specify:

```text
allowed_cpus
preferred_cpus
```

Example:

```text
cpu.affinity = [2, 3, 4, 5]
```

The governor shall intersect requested affinity with:

```text
deployment policy
security policy
platform constraints
ancestor affinity
```

---

# 606.19 — Memory Governance

Memory shall be accounted by category.

```text
virtual
resident
shared
mapped
stack
pinned
device
```

Axiom shall not treat all memory as interchangeable.

Example:

```text
memory.resident <= 512 MiB
memory.virtual <= 2 GiB
memory.pinned <= 64 MiB
```

---

# 606.20 — Virtual vs Resident Memory

These metrics shall remain separate.

```text
VirtualMemory
```

describes address-space reservation/commit semantics.

```text
ResidentMemory
```

describes physical memory pressure.

A system may have:

```text
virtual = 4 GiB
resident = 400 MiB
```

without contradiction.

---

# 606.21 — Shared Memory Charging

Shared memory requires explicit attribution.

A shared segment shall support policies:

```text
OwnerPays
Proportional
CreatorPays
GroupPays
ExplicitSplit
```

Default:

```text
OwnerPays
```

unless configured otherwise.

This avoids double-charging the same physical pages as if they were independently allocated.

---

# 606.22 — Memory Pressure

Canonical pressure states:

```text
Normal
Warning
High
Critical
Exhausted
```

Transitions shall be observable.

Example:

```text
Normal
   ↓
Warning
   ↓
High
   ↓
Critical
   ↓
Exhausted
```

The governor shall attempt reclamation before forced termination where practical.

---

# 606.23 — Memory Reclamation

Reclaimable resources may include:

```text
cache
prefetch buffers
decoded assets
temporary mappings
unused IPC buffers
idle GPU allocations
compiled transient artifacts
```

Reclamation priority shall be explicit.

```text
ReclaimPriority {
    OptionalCache
    Prefetch
    Temporary
    Idle
    BestEffort
}
```

User-visible persistent state shall not be silently discarded.

---

# 606.24 — Thread Governance

Thread count shall be separately controlled.

```text
threads:
    min = 2
    reserved = 4
    soft = 16
    hard = 32
```

Thread creation shall pass through the governor unless explicitly marked platform-owned.

---

# 606.25 — Task Governance

Axiom tasks are cheaper than OS threads and shall therefore have separate accounting.

```text
tasks.max
tasks.active
tasks.queued
```

A runtime may have:

```text
32 OS threads
10000 tasks
```

without treating those as equivalent resources.

---

# 606.26 — Handle / File Descriptor Governance

Every governed process shall have quotas for:

```text
handles
file descriptors
sockets
events
semaphores
shared memory mappings
IPC endpoints
```

Example:

```text
handles.max = 4096
fds.max = 1024
sockets.max = 256
```

The exact underlying OS mechanism shall be abstracted.

---

# 606.27 — IPC Governance

BOOTSTRAP-604 shall charge:

```text
channels
queues
messages
bytes
pending requests
in-flight operations
shared buffers
```

Example:

```text
ipc:
    channels.max = 128
    queue_bytes.max = 16.MiB
    message_bytes.max = 4.MiB
    pending_requests.max = 1024
```

IPC backpressure shall integrate with the Resource Governor.

---

# 606.28 — Shared Memory Governance

Shared memory shall have:

```text
segment_count
reserved_bytes
committed_bytes
mapped_bytes
pinned_bytes
```

Example:

```text
shared_memory.max = 1.GiB
segments.max = 64
```

Creation shall require both:

```text
security capability
+
resource admission
```

---

# 606.29 — GPU Governance

GPU resources shall be first-class resources.

Supported categories:

```text
GPU device
GPU context
GPU stream
GPU memory
GPU compute time
GPU command queue
GPU mapped/pinned memory
```

Example:

```text
gpu:
    devices = [0]
    memory = 2.GiB
    contexts = 2
    streams = 16
```

---

# 606.30 — GPU Memory

GPU memory shall be separately tracked from CPU memory.

```text
GpuMemory {
    reserved
    allocated
    resident
    mapped
    pinned
}
```

Axiom shall not assume unified memory semantics across platforms.

---

# 606.31 — GPU Scheduling

Where the platform supports GPU scheduling, the governor may specify:

```text
compute_budget
priority
queue_limit
memory_limit
```

Where the platform does not provide hardware-level enforcement, Axiom shall use admission control and cooperative accounting.

It shall clearly report:

```text
Enforced
BestEffort
Unsupported
```

rather than falsely claiming hard enforcement.

---

# 606.32 — I/O Governance

I/O shall be governed using both:

```text
Bandwidth
Operations per second
```

Example:

```text
disk:
    bandwidth = 100.MBps
    iops = 500
```

Network:

```text
network:
    ingress = 20.MBps
    egress = 10.MBps
```

---

# 606.33 — I/O Accounting

Each operation shall be charged according to:

```text
bytes
operation_count
latency
resource_scope
```

Optional accounting:

```text
read_bytes
write_bytes
read_ops
write_ops
```

---

# 606.34 — Storage Quotas

Storage shall support:

```text
persistent
temporary
cache
log
checkpoint
crash-artifact
```

Separate quotas prevent logs or caches from consuming all application storage.

Example:

```text
storage:
    persistent = 10.GiB
    cache = 2.GiB
    logs = 500.MiB
```

---

# 606.35 — Timer Governance

Timers are cheap individually but can become a denial-of-service vector.

Govern:

```text
timers.max
active_timers.max
wakeups.max
high_resolution_timers.max
```

Example:

```text
timers.max = 10000
high_resolution_timers.max = 100
```

---

# 606.36 — Process Governance

BOOTSTRAP-605 shall use:

```text
processes.max
service_instances.max
children.max
```

Process creation requires admission.

The governor shall check:

```text
security capability
resource quota
service policy
deployment policy
ancestor quota
```

---

# 606.37 — Admission Control

Every potentially blocking or expensive resource acquisition shall conceptually follow:

```text
request
   ↓
validate capability
   ↓
resolve scope
   ↓
calculate effective policy
   ↓
check reservation
   ↓
check current usage
   ↓
check ancestor budgets
   ↓
admit / wait / reject
```

The admission result:

```text
Admitted
Wait
Rejected
Degraded
```

---

# 606.38 — Effective Limit

For hierarchical limits:

```text
effective_hard =
    min(
        local_hard,
        parent_effective_hard,
        deployment_hard,
        platform_hard
    )
```

Likewise:

```text
effective_reservation
```

shall never exceed an ancestor's available reservation.

---

# 606.39 — Resource Ownership

Every allocation shall have an owner.

Ownership shall be explicit:

```text
ResourceOwner {
    scope
    service
    process
    generation
}
```

This integrates with BOOTSTRAP-605 process generations.

A restarted process receives a new generation.

Old resources cannot silently become owned by the new process generation.

---

# 606.40 — Attribution of Shared Resources

Shared resources shall support:

```text
PrimaryOwner
SharedOwners
AttributionPolicy
```

For example:

```text
IPC channel
 ├── Service A
 └── Service B
```

The channel itself may belong to Service A while queued messages are charged to both endpoints according to policy.

---

# 606.41 — Resource Tokens

The runtime shall optionally represent scarce resources with tokens.

```text
ResourceToken<T>
```

Example:

```text
GpuStreamToken
ThreadToken
FileDescriptorToken
IpcBufferToken
```

Acquiring a token reserves capacity.

Releasing the token returns capacity.

This makes resource ownership explicit and prevents accidental over-allocation.

---

# 606.42 — RAII-Style Lifetime

Resource tokens should normally use deterministic lifetime semantics.

Conceptually:

```text
with governor.acquire<Thread>(1) as token:
    ...
```

At scope exit:

```text
token.release()
```

The implementation must not require garbage collection.

---

# 606.43 — Resource Leaks

The governor shall detect resources that survive their owning scope.

Examples:

```text
process exited
but resource remains charged
```

This shall be treated as a runtime invariant violation.

Recovery mechanisms may include:

```text
automatic reclamation
forced close
orphan reassignment
diagnostic fault
```

depending on resource type.

---

# 606.44 — Orphan Resources

When an owning process crashes:

```text
Process A generation 7
       ↓ crash
resources become orphaned
```

Supervisor and governor shall reconcile them.

Default:

```text
OS-owned resources
    → released automatically

Axiom-managed resources
    → explicitly reclaimed

persistent resources
    → retained according to policy
```

This integrates with BOOTSTRAP-605 crash recovery.

---

# 606.45 — Pressure Controller

The governor shall expose a unified pressure model:

```text
ResourcePressure {
    resource
    scope
    current
    soft_limit
    hard_limit
    pressure
    trend
}
```

Trend:

```text
Stable
Increasing
Decreasing
Unknown
```

---

# 606.46 — Pressure Responses

Possible responses:

```text
Observe
Notify
Throttle
Defer
Reclaim
ReduceConcurrency
Reject
Suspend
Terminate
```

Responses shall be resource-specific.

Memory pressure may reclaim caches.

CPU pressure may throttle.

Process quota exhaustion may reject creation.

---

# 606.47 — Graceful Degradation

Applications may declare optional workloads.

Example:

```text
workload:
    required = true
```

or:

```text
workload:
    required = false
    priority = low
```

When resources become constrained:

```text
optional work
    ↓
deferred work
    ↓
best-effort work
```

shall yield to required work.

---

# 606.48 — Fairness

The governor shall support weighted fairness.

```text
weight = 100
```

does not mean:

```text
100% CPU
```

It means relative scheduling/allocation weight within the same contention domain.

Example:

```text
Service A weight = 100
Service B weight = 50
```

When both contend for a governed resource, the scheduler may target approximately a 2:1 allocation subject to:

- reservations;
- quotas;
- platform constraints;
- workload availability.

---

# 606.49 — Starvation Prevention

A low-priority scope shall not necessarily be allowed to starve indefinitely.

The governor may implement:

```text
minimum service quantum
aging
bounded waiting
reservation guarantees
```

where supported by the resource.

---

# 606.50 — Priority Inheritance

For resources causing priority inversion, the runtime may support priority inheritance.

This is particularly important for:

```text
mutex
IPC
scheduler queues
resource admission locks
```

Priority inheritance shall not change security capabilities.

---

# 606.51 — No Global Hot-Path Lock

The Resource Governor shall not use one global mutex for all accounting.

Hot-path accounting should use:

```text
atomic counters
per-thread counters
per-core counters
batched aggregation
lock-free or low-contention structures
```

Global coordination may be used only for:

```text
policy changes
snapshot creation
administrative operations
resource-group topology changes
```

---

# 606.52 — Exact vs Sampled Accounting

Resources shall declare accounting precision.

```text
Exact
Bounded
Sampled
Estimated
Unsupported
```

Examples:

```text
thread count = Exact
CPU time = Exact/Batched
resident memory = Platform-dependent
GPU utilization = Platform-dependent
network throughput = Exact/Batched
```

The runtime shall expose the precision in diagnostics.

---

# 606.53 — Accounting Epoch

Resource accounting shall use monotonically increasing epochs.

```text
ResourceEpoch
```

An epoch changes when:

- policy changes;
- scope changes;
- process generation changes;
- accounting snapshot is committed.

This allows deterministic reconciliation.

---

# 606.54 — Resource Snapshot

The governor shall expose immutable snapshots.

```text
ResourceSnapshot {
    epoch
    timestamp
    scope
    usage[]
    reservation[]
    limits[]
    pressure[]
}
```

Snapshots integrate with BOOTSTRAP-600 checkpoint/state infrastructure.

---

# 606.55 — Runtime Configuration

BOOTSTRAP-601 shall define resource policies declaratively.

Example:

```text
resource_policy {
    cpu {
        quota = 50%
        reservation = 10%
    }

    memory {
        soft = 512.MiB
        hard = 768.MiB
    }

    threads {
        hard = 32
    }

    ipc {
        queue_bytes = 16.MiB
    }
}
```

Configuration shall be validated before activation.

---

# 606.56 — Atomic Policy Reload

Policy changes shall follow:

```text
parse
→ validate
→ calculate effective policies
→ validate hierarchy
→ commit
```

If validation fails:

```text
old policy remains active
```

No partially applied resource policy is permitted.

---

# 606.57 — Existing Usage During Limit Reduction

Suppose:

```text
current = 700 MiB
old_limit = 1 GiB
new_limit = 512 MiB
```

The governor shall not pretend the current allocation disappeared.

State becomes:

```text
OverLimit
```

New allocations are restricted.

The governor then applies configured remediation:

```text
reclaim
throttle
drain
terminate
```

according to policy.

---

# 606.58 — Security Integration

BOOTSTRAP-603 shall remain authoritative for permission.

Resource Governor answers:

> "Can this scope consume the resource?"

Security answers:

> "Is this scope authorized to access the resource?"

Both checks are required.

```text
authorize
   +
admit
   =
execute
```

Resource exhaustion must never grant additional security authority.

---

# 606.59 — Capability Integration

Resource-specific capabilities may optionally encode limits.

Example:

```text
Capability<Network>(egress <= 10.MBps)
Capability<Gpu>(memory <= 1.GiB)
Capability<Process>(children <= 4)
```

Capability attenuation may reduce a resource allowance.

A child capability can never increase the parent's authority.

---

# 606.60 — Configuration vs Capability

Configuration defines policy.

Capability defines authority.

Resource Governor defines actual allocation.

Therefore:

```text
Configuration
      ↓
Security Policy
      ↓
Capability
      ↓
Resource Policy
      ↓
Governor
      ↓
Allocation
```

No single layer may bypass another.

---

# 606.61 — Diagnostics Integration

BOOTSTRAP-602 shall receive resource events:

```text
ResourceAllocated
ResourceReleased
QuotaReached
QuotaRejected
BudgetExceeded
PressureChanged
ResourceReclaimed
ResourceLeakDetected
ResourcePolicyChanged
```

Every event should include:

```text
resource
scope
process
generation
usage
limit
policy_epoch
```

No secret values shall be logged.

---

# 606.62 — Metrics

Canonical metrics:

```text
resource_usage
resource_reserved
resource_limit
resource_pressure
resource_admission_total
resource_rejection_total
resource_throttle_total
resource_reclaim_total
resource_wait_total
```

Metrics shall be available per:

```text
application
service
process
resource group
resource type
```

---

# 606.63 — Tracing

Expensive resource operations may generate spans:

```text
resource.acquire
resource.wait
resource.reclaim
resource.throttle
resource.release
```

Tracing shall be optional and removable at compile/link time.

---

# 606.64 — IPC Integration

BOOTSTRAP-604 shall query the governor before:

```text
creating channel
allocating queue
allocating shared buffer
sending large message
creating pending request
mapping shared memory
```

Backpressure shall be represented as a resource condition rather than an ad-hoc IPC mechanism.

---

# 606.65 — Supervisor Integration

BOOTSTRAP-605 shall use the governor for:

```text
process creation
service instance creation
restart admission
thread provisioning
process resource limits
resource pressure recovery
```

A restart shall not occur indefinitely if the resource governor repeatedly rejects the process.

This shall feed the supervisor's crash/restart-loop logic.

---

# 606.66 — Restart Storm Prevention

If:

```text
restart
→ resource rejection
→ restart
→ resource rejection
```

occurs repeatedly, the supervisor shall classify it as a resource-induced failure loop.

It shall apply the existing restart budget.

---

# 606.67 — State Integration

BOOTSTRAP-600 may checkpoint:

```text
resource policy
resource reservations
resource group topology
persistent quota usage
```

Transient counters such as CPU time need not be restored exactly.

Each resource shall declare:

```text
CheckpointMode:
    Persistent
    Reconstruct
    Reset
    Unsupported
```

---

# 606.68 — Crash Recovery

After application restart:

```text
desired resource policy
        ↓
reconstruct scopes
        ↓
recreate reservations
        ↓
reconcile actual usage
        ↓
resume governance
```

Actual OS resource state shall always take precedence over stale persisted counters.

---

# 606.69 — Process Generation Safety

Resource accounting must use:

```text
(ProcessId, Generation)
```

rather than only:

```text
ProcessId
```

This prevents:

```text
old process
  ↓ crash
new process reuses ID
  ↓
old accounting accidentally charged to new process
```

---

# 606.70 — Native API

Struct-only design shall be used.

Example:

```text
struct ResourceGovernor {
    ...
}

fn ResourceGovernor.acquire(
    self,
    request: ResourceRequest
) -> ResourceResult
```

No class hierarchy is required.

---

# 606.71 — Resource Request

```text
struct ResourceRequest {
    resource: ResourceType
    quantity: ResourceQuantity

    scope: ResourceScopeId

    priority: ResourcePriority

    deadline: Option<Time>
    flags: ResourceRequestFlags
}
```

---

# 606.72 — Resource Result

```text
enum ResourceResult<T> {
    Granted(T)
    Wait(WaitToken)
    Rejected(ResourceError)
    Degraded(T)
}
```

---

# 606.73 — Resource Error

Canonical errors:

```text
QuotaExceeded
BudgetExceeded
ReservationUnavailable
AncestorLimitExceeded
PlatformLimit
CapabilityDenied
PolicyDenied
ResourceUnavailable
WouldBlock
DeadlineExceeded
ResourcePressure
Unsupported
InvalidRequest
```

---

# 606.74 — Resource Token API

Example:

```text
fn ResourceGovernor.acquire_thread(
    self,
    scope: ResourceScopeId
) -> Result<ThreadToken>
```

Usage:

```text
thread_token = governor.acquire_thread(scope)?

spawn_worker(thread_token)
```

When the worker terminates:

```text
thread_token.release()
```

---

# 606.75 — Reservation API

```text
fn ResourceGovernor.reserve(
    self,
    request: ResourceReservation
) -> Result<ReservationToken>
```

A reservation token represents a committed future allocation.

---

# 606.76 — Budget API

```text
fn ResourceGovernor.consume(
    self,
    token: ResourceToken,
    amount: ResourceQuantity
) -> Result<BudgetCharge>
```

The implementation shall use fast-path counters where possible.

---

# 606.77 — Resource Policy API

```text
fn ResourceGovernor.policy(
    self,
    scope: ResourceScopeId
) -> ResourcePolicySnapshot
```

Snapshots are immutable.

---

# 606.78 — Reclamation API

```text
fn ResourceGovernor.register_reclaimer(
    self,
    scope: ResourceScopeId,
    reclaimer: ResourceReclaimer
)
```

A reclaimer reports:

```text
estimated_reclaimable
priority
cost
```

The governor may call reclaimers under pressure.

---

# 606.79 — Reclamation Ordering

Reclaimers shall be sorted by policy:

```text
lowest-value resource
→ cheapest reclamation
→ largest recovery
```

The algorithm shall be deterministic for equal inputs.

---

# 606.80 — Resource Pressure Callback

```text
fn ResourceGovernor.on_pressure(
    self,
    callback: ResourcePressureHandler
)
```

Handlers shall not perform unbounded work inside governor-critical sections.

---

# 606.81 — Blocking Semantics

A resource acquisition may:

```text
return immediately
block
yield
await
fail
```

The governor shall expose the state explicitly.

For async execution:

```text
await governor.acquire_async(...)
```

shall integrate with the future Axiom executor.

---

# 606.82 — Deadline-Aware Acquisition

Every potentially blocking request may specify:

```text
deadline
```

Example:

```text
acquire(
    memory = 64.MiB,
    deadline = now + 50.ms
)
```

Failure after the deadline:

```text
DeadlineExceeded
```

---

# 606.83 — Cancellation

Waiting resource requests shall be cancellable.

```text
WaitToken.cancel()
```

Cancellation must remove the waiter from the governor without leaking reservations.

---

# 606.84 — Fair Wait Queues

Resource waiters should use:

```text
priority
deadline
age
reservation
```

to determine ordering.

The policy must prevent indefinite starvation.

---

# 606.85 — Resource Deadlock Avoidance

The governor shall avoid holding resource locks while waiting for another resource.

Multi-resource acquisition should use a transaction-like admission model:

```text
request all
→ validate all
→ reserve all
→ commit
```

or:

```text
rollback all
```

This prevents partial acquisition deadlocks.

---

# 606.86 — Atomic Multi-Resource Reservation

Example:

```text
reserve {
    cpu = 20%
    memory = 256.MiB
    threads = 4
    gpu_memory = 512.MiB
}
```

Either:

```text
all granted
```

or:

```text
none granted
```

unless the caller explicitly requests best-effort allocation.

---

# 606.87 — Resource Transaction

Conceptual API:

```text
tx = governor.begin()

tx.reserve(cpu, 20.percent)
tx.reserve(memory, 256.MiB)
tx.reserve(threads, 4)

tx.commit()
```

Failure:

```text
tx.rollback()
```

The transaction shall be bounded and unsuitable for arbitrary long-running application work.

---

# 606.88 — Application Resource Classes

Applications may define logical resource groups:

```text
Interactive
Background
Compilation
Rendering
AI
Networking
Storage
```

Example:

```text
group AI {
    gpu_memory = 4.GiB
    cpu = 50%
}
```

---

# 606.89 — Workload Classes

Each workload may specify:

```text
Required
Interactive
Background
BestEffort
Maintenance
```

The governor may use workload class for degradation decisions.

---

# 606.90 — Scheduling Contract

Resource Governor does not replace the scheduler.

Responsibilities:

```text
Governor:
    admission
    accounting
    quotas
    budgets
    pressure
    resource policy

Scheduler:
    execution order
    runnable tasks
    CPU assignment
    wakeups
```

The scheduler consumes governor decisions.

---

# 606.91 — Future Scheduler Boundary

BOOTSTRAP-606 shall expose enough primitives for the next runtime layer:

```text
cpu_budget
cpu_weight
cpu_reservation
priority
affinity
task_admission
thread_admission
```

The detailed executor and scheduler shall be specified separately.

---

# 606.92 — Platform Adapter

Canonical interface:

```text
trait ResourceBackend {
    fn capabilities(...)
    fn read_usage(...)
    fn apply_policy(...)
    fn create_group(...)
    fn destroy_group(...)
}
```

---

# 606.93 — Linux

Where available, integrate with:

```text
cgroups
rlimits
scheduler controls
CPU affinity
memory controls
I/O controls
process limits
```

The backend shall expose enforcement strength.

---

# 606.94 — Windows

Where available, integrate with:

```text
Job Objects
process limits
CPU controls
memory limits
handle/process accounting
affinity
priority
```

The Axiom API shall remain platform-neutral.

---

# 606.95 — macOS

Use native platform mechanisms for:

```text
process limits
resource limits
CPU affinity where supported
memory/resource accounting where available
```

Unsupported enforcement shall be explicitly reported.

---

# 606.96 — Android

The backend shall account for Android lifecycle and OS restrictions.

The application cannot assume unrestricted:

```text
background CPU
background execution
process lifetime
memory
GPU
```

Axiom shall distinguish:

```text
Requested
Granted
Actually Enforced
```

---

# 606.97 — iOS

iOS imposes lifecycle and resource constraints controlled by the OS.

Axiom shall therefore treat:

```text
suspension
termination
memory pressure
background execution
```

as external governor events.

The runtime must not claim application-level control where the OS owns the decision.

---

# 606.98 — WASM

WASM has no universal OS-level resource interface.

The host shall provide resource capabilities.

Example:

```text
WasmResourceHost {
    cpu_budget
    memory_limit
    io_budget
    timers_limit
}
```

Enforcement may therefore be host-defined.

---

# 606.99 — Embedded Systems

On embedded targets:

```text
Process → Task
Thread → RTOS task
File → Device resource
IPC → Queue
```

The same Resource Governor model shall remain usable.

---

# 606.100 — Platform Capability Discovery

The runtime shall expose:

```text
ResourceSupport {
    accounting
    reservation
    soft_limit
    hard_limit
    throttling
    reclamation
}
```

per resource.

Example:

```text
GPU compute quota:
    accounting = Supported
    reservation = Supported
    hard_limit = Unsupported
    throttling = BestEffort
```

---

# 606.101 — Determinism

For identical:

```text
policy
workload
resource availability
platform state
```

governor decisions should be deterministic where platform scheduling permits.

Randomized jitter used for recovery shall remain explicitly isolated from core resource accounting.

---

# 606.102 — Time Source

The governor shall use:

```text
MonotonicClock
```

for:

- CPU budget periods;
- burst windows;
- deadlines;
- throttling;
- pressure sampling.

Wall-clock changes must not break resource accounting.

---

# 606.103 — Resource Clock

Resource accounting shall use an abstract clock:

```text
ResourceClock
```

This enables deterministic testing.

Tests can provide:

```text
FakeResourceClock
```

without sleeping the host.

---

# 606.104 — Configuration Schema

A machine-readable resource manifest shall be defined.

Example:

```text
resource_policy {
    cpu {
        quota = 50%
        reservation = 10%
        weight = 100
    }

    memory {
        soft = 512.MiB
        hard = 1.GiB
    }

    threads {
        hard = 32
    }

    processes {
        hard = 8
    }

    gpu {
        memory = 2.GiB
        streams = 16
    }
}
```

---

# 606.105 — Validation

The compiler/runtime configuration validator shall reject:

```text
soft > hard
reservation > hard
burst > ancestor hard limit
negative quantity
invalid unit
cyclic resource-group hierarchy
invalid inheritance
unknown resource
unsupported mandatory enforcement
```

---

# 606.106 — Inheritance

Default:

```text
child inherits parent policy
```

A child may tighten limits:

```text
parent memory = 1 GiB
child memory = 512 MiB
```

A child cannot automatically relax:

```text
parent memory = 512 MiB
child memory = 1 GiB
```

unless the parent explicitly delegates capacity.

---

# 606.107 — Delegated Capacity

A parent may explicitly delegate a resource budget.

```text
delegate:
    memory = 256.MiB
    threads = 4
```

The child can distribute the delegated capacity among its descendants.

This creates an explicit capacity tree.

---

# 606.108 — Capacity Tree

```text
Application
  1 GiB
    │
    ├── AI Service
    │     512 MiB
    │
    ├── API Service
    │     256 MiB
    │
    └── Worker
          256 MiB
```

The sum of committed child reservations shall not exceed parent capacity.

---

# 606.109 — Resource Accounting Invariant

For every resource:

```text
committed_children
+
unallocated_capacity
<=
parent_capacity
```

Rounding and platform measurement errors shall be explicitly bounded.

---

# 606.110 — Hierarchical Reconciliation

The governor shall periodically or event-drivenly verify:

```text
actual usage
vs
accounted usage
vs
policy
```

Differences shall produce:

```text
ResourceReconciliationEvent
```

---

# 606.111 — Resource Drift

If:

```text
actual > accounted
```

the governor shall classify the resource as:

```text
DriftPositive
```

If:

```text
actual < accounted
```

then:

```text
DriftNegative
```

The correction algorithm must avoid double charging.

---

# 606.112 — Resource Accounting Failure

If exact accounting fails, the governor shall prefer conservative behavior for safety-critical quotas.

Example:

```text
unknown memory usage
```

may temporarily prevent additional allocation rather than permitting unbounded growth.

---

# 606.113 — Security of Resource Metadata

Resource metadata may reveal:

- workload size;
- process activity;
- device availability;
- timing information.

Therefore access to detailed resource diagnostics may require:

```text
Capability<ResourceInspect>
```

Ordinary applications may receive only their own scopes.

---

# 606.114 — Resource Isolation

One service shall not be able to inspect another service's detailed resource usage without authorization.

Supervisor-level monitoring may inspect all services.

---

# 606.115 — Quota Abuse Prevention

A child process must not evade quotas by:

```text
forking/spawning descendants
creating alternate services
creating IPC loops
allocating shared memory elsewhere
using delegated resources without attribution
```

All descendant resource consumption shall ultimately charge an ancestor scope.

---

# 606.116 — IPC Amplification Protection

IPC systems shall account for:

```text
message count
message bytes
queue depth
fan-out
pending requests
```

This prevents:

```text
small request
→ huge queued work
```

from bypassing quotas.

---

# 606.117 — Network Amplification Protection

Network operations shall support separate:

```text
request count
bytes
connections
pending operations
```

The governor may reject new connections before bandwidth is exhausted.

---

# 606.118 — Storage Amplification Protection

Compressed or indirect storage shall be charged against actual resource consumption where practical.

Axiom shall not assume:

```text
logical_size == physical_size
```

for caches, compression or sparse files.

---

# 606.119 — Compiler Integration

The compiler shall support resource metadata annotations.

Example:

```text
@resource(cpu = "low")
fn background_task(...)
```

or:

```text
@requires_resource(gpu_memory = 512.MiB)
fn infer(...)
```

These annotations are declarative hints unless the target backend can enforce them.

---

# 606.120 — Compile-Time Resource Metadata

Compiled artifacts may contain:

```text
resource_requirements
resource_capabilities
resource_profiles
```

Example:

```text
requirements {
    gpu = optional
    gpu_memory = 512.MiB
    threads = 4
}
```

---

# 606.121 — Link-Time Resource Metadata

The linker may merge requirements:

```text
module A
module B
module C
    ↓
application requirements
```

The result shall be deterministic.

Unused modules shall not contribute requirements if dead-stripped.

---

# 606.122 — Dead Resource Elimination

If a feature is not referenced:

```text
GPU runtime
IPC runtime
storage governor
```

shall not necessarily be linked into a minimal executable.

The linker should eliminate unused runtime components.

---

# 606.123 — Runtime Optionality

Resource Governor itself shall have tiers:

```text
MinimalGovernor
StandardGovernor
FullGovernor
```

Minimal targets may omit:

- tracing;
- detailed metrics;
- advanced GPU accounting;
- expensive reconciliation.

Core safety guarantees remain intact.

---

# 606.124 — No Mandatory Garbage Collector

Resource governance shall use deterministic ownership.

It shall not depend on:

```text
GC
tracing heap
borrow checker
runtime pointer scanning
```

for basic resource correctness.

---

# 606.125 — Memory-Safe Handles

Internal resource references shall use:

```text
index + generation
```

or equivalent validated handles.

A stale handle shall produce:

```text
InvalidResourceHandle
```

rather than accessing arbitrary memory.

---

# 606.126 — Resource Governor Internal Architecture

Recommended implementation:

```text
ResourceGovernor
│
├── PolicyManager
│
├── ScopeTree
│
├── AccountingEngine
│
├── AdmissionEngine
│
├── ReservationManager
│
├── BudgetManager
│
├── PressureManager
│
├── ReclaimManager
│
├── WaitQueueManager
│
├── PlatformBackend
│
├── MetricsAdapter
│
└── DiagnosticsAdapter
```

---

# 606.127 — Fast Path

Common operation:

```text
charge resource
```

should approximately be:

```text
load counter
→ compare limit
→ atomic update
→ return
```

No heap allocation should be required.

---

# 606.128 — Slow Path

Slow path may perform:

```text
policy lookup
hierarchy traversal
reclamation
waiting
platform synchronization
diagnostics
```

The common case must avoid these operations.

---

# 606.129 — Resource Policy Cache

Effective policy may be cached per:

```text
ResourceScope
ResourceType
PolicyEpoch
```

When policy changes:

```text
epoch++
```

Old cache entries become invalid.

---

# 606.130 — Per-Core Accounting

For extremely high-frequency resources such as CPU time, the governor may use:

```text
per-core counters
```

followed by aggregation.

This avoids global contention.

---

# 606.131 — Batched Charging

Small repeated operations may be accumulated locally:

```text
local = +4 KiB
local = +8 KiB
local = +16 KiB
```

and periodically committed.

The batch size shall be bounded so a hard quota cannot be violated beyond the documented accounting tolerance.

---

# 606.132 — Quota Overshoot Bound

For batched accounting:

```text
overshoot <= configured accounting_granularity
```

Hard-limit resources requiring exact enforcement shall not use an unsafe batching strategy.

---

# 606.133 — Resource Governor Thread Safety

The governor shall support concurrent:

```text
allocation
release
policy updates
process exits
scope destruction
pressure events
```

without corrupting accounting.

---

# 606.134 — Scope Destruction

When a scope disappears:

```text
verify active resources
→ reclaim/release
→ detach children
→ finalize accounting
→ mark generation closed
```

A scope cannot be reused with the same generation.

---

# 606.135 — Resource Group Lifecycle

States:

```text
Created
Active
Draining
Closed
```

New allocations are forbidden in:

```text
Draining
Closed
```

Existing work is allowed to finish during `Draining` subject to policy.

---

# 606.136 — Service Lifecycle Integration

BOOTSTRAP-605 service states map to resource behavior:

```text
Starting
    → allocation permitted

Ready
    → normal allocation

Running
    → normal allocation

Degraded
    → optional workloads may be throttled

Stopping
    → new allocations restricted

Stopped
    → allocations denied
```

---

# 606.137 — Resource Drain

Before service shutdown:

```text
stop new admissions
→ drain pending operations
→ release resources
→ close scope
```

This integrates with BOOTSTRAP-605 graceful shutdown.

---

# 606.138 — Forced Termination

If resource exhaustion requires termination:

```text
resource pressure
→ reclaim
→ degrade
→ stop optional services
→ graceful stop
→ force termination
```

The action must follow configured policy and security authority.

---

# 606.139 — Recovery Priority

Recovery shall normally preserve:

```text
critical system services
required application services
interactive workload
background workload
best-effort workload
```

This is a policy mechanism, not a guarantee against OS-level termination.

---

# 606.140 — Resource Dependency

Some resources depend on others.

Example:

```text
GPU stream
    requires GPU context
    requires GPU device

IPC request
    requires channel
    requires queue capacity

Thread
    requires process
    requires CPU capacity
```

The governor shall understand dependency declarations.

---

# 606.141 — Resource Dependency Graph

Resource dependencies shall be represented explicitly.

```text
ResourceNode
ResourceDependency
```

The graph shall be validated for cycles where cycles would make admission impossible.

---

# 606.142 — Admission Transaction with Dependencies

Example:

```text
request GPU stream
```

may require:

```text
GPU device
GPU context
GPU memory
GPU stream
```

The governor shall atomically reserve all required resources.

---

# 606.143 — Resource Release Ordering

Dependencies shall be released in reverse order.

```text
stream
→ context
→ device reservation
```

This avoids dangling dependent resources.

---

# 606.144 — Resource Budgets for Services

BOOTSTRAP-605 service manifest shall be extended:

```text
service {
    name = "worker"

    resources {
        cpu = 30%
        memory = 512.MiB
        threads = 8
        processes = 2
        ipc = 8.MiB
    }
}
```

---

# 606.145 — Resource Budgets for Processes

Process policy:

```text
process {
    memory = 256.MiB
    threads = 4
    handles = 1024
    gpu_memory = 512.MiB
}
```

Supervisor applies the policy during process creation.

---

# 606.146 — Resource Budget for Restart

Restart admission may require temporary additional capacity:

```text
old instance draining
+
new instance starting
```

Therefore rolling restart shall reserve temporary overlap capacity.

Example:

```text
steady = 512 MiB
restart_peak = 1 GiB
```

The supervisor must verify the peak budget before launching the replacement.

---

# 606.147 — Deployment Integration

BOOTSTRAP-601 deployment manifest may specify:

```text
application_resources
service_resources
deployment_resources
```

Deployment resources establish the outer boundary.

---

# 606.148 — Deployment-Level Limit

Example:

```text
deployment:
    memory = 4.GiB
    cpu = 4 cores
    processes = 32
```

All applications inside the deployment must remain within this boundary.

---

# 606.149 — Multi-Application Deployment

For:

```text
Deployment
 ├── App A
 ├── App B
 └── App C
```

capacity may be:

```text
shared
partitioned
reserved
delegated
```

The deployment policy determines the model.

---

# 606.150 — Resource Reservations Across Services

A critical service may reserve:

```text
CPU
memory
threads
IPC
```

so optional services cannot consume all capacity.

This is the main mechanism for protecting critical workloads.

---

# 606.151 — No Automatic Global Overcommit

The governor shall not assume unlimited overcommit.

For each resource it shall declare:

```text
OvercommitAllowed
OvercommitForbidden
PlatformDefined
```

Memory may permit virtual overcommit while hard resident memory remains bounded.

---

# 606.152 — Resource Availability

Availability shall be represented separately from limits.

```text
configured_limit
committed
used
available
```

Example:

```text
limit = 1 GiB
reserved = 256 MiB
used = 128 MiB
available = 640 MiB
```

---

# 606.153 — Resource Forecasting

The governor may optionally estimate:

```text
time_to_quota
projected_usage
pressure_trend
```

These are advisory.

They shall never replace hard accounting.

---

# 606.154 — Adaptive Throttling

Applications may opt into adaptive throttling.

Example:

```text
cpu.adaptive = true
```

The governor may adjust:

```text
worker concurrency
background rate
I/O rate
GPU queue depth
```

within declared bounds.

---

# 606.155 — Application Feedback

The governor shall expose:

```text
ResourcePressureEvent
```

Applications may respond voluntarily.

This provides a cooperative layer above hard enforcement.

---

# 606.156 — Resource-Aware Worker Pools

Future executor implementations can query:

```text
available_cpu
available_threads
pressure
```

to size worker pools.

This avoids creating excessive threads merely because hardware exposes many cores.

---

# 606.157 — Resource-Aware Async Runtime

The future async runtime shall use governor signals to:

```text
limit concurrent tasks
limit outstanding I/O
limit queued work
delay optional work
```

This avoids unbounded async queues.

---

# 606.158 — Backpressure Contract

Every potentially unbounded producer shall have one of:

```text
bounded queue
quota
blocking
await
drop policy
rejection
```

No core Axiom runtime subsystem shall silently create an unlimited queue.

---

# 606.159 — Queue Policy

Queues shall declare:

```text
max_items
max_bytes
overflow_policy
```

Overflow policy:

```text
Reject
Block
DropNewest
DropOldest
Coalesce
Escalate
```

Default for reliable IPC:

```text
Block / Reject
```

not silent loss.

---

# 606.160 — Resource Limits and Security Limits

Security policy may define stricter limits than ordinary configuration.

For example:

```text
deployment memory = 1 GiB
security sandbox memory = 512 MiB
application request = 768 MiB
```

Effective limit:

```text
512 MiB
```

---

# 606.161 — Resource Capability Delegation

A service may receive:

```text
Capability<ResourceBudget>
```

allowing it to delegate only the explicitly granted capacity.

Example:

```text
Application
    ↓ delegate 256 MiB
Worker Service
    ↓ delegate 128 MiB
Worker Process
```

---

# 606.162 — Revocation

When a delegated resource capability is revoked:

```text
new allocations denied
existing allocations remain until policy-defined remediation
```

The runtime shall not arbitrarily corrupt active operations merely because policy changed.

---

# 606.163 — Resource Revocation Modes

```text
DenyNew
Throttle
Drain
Reclaim
Terminate
```

The policy selects the appropriate mode.

---

# 606.164 — Resource Governance Events

Canonical event sequence:

```text
Requested
Validated
Reserved
Allocated
Consumed
PressureChanged
Throttled
Released
Reclaimed
Closed
```

Each event has a monotonically increasing sequence number within its scope.

---

# 606.165 — Auditability

Administrative changes shall be auditable:

```text
policy changed
reservation delegated
quota reduced
resource group created
resource group destroyed
manual throttle
manual override
```

---

# 606.166 — Manual Override

Privileged administrators may override ordinary resource policy only through an explicit capability.

```text
Capability<ResourceOverride>
```

Every override shall be logged.

---

# 606.167 — Override Expiration

Overrides should support:

```text
expiration
scope
reason
operator identity
```

Permanent unrestricted override should not be the default.

---

# 606.168 — Testing Architecture

The governor shall be testable without real resource exhaustion.

Required test doubles:

```text
FakeResourceBackend
FakeClock
FakeCpuCounter
FakeMemoryBackend
FakeGpuBackend
FakeProcessBackend
FakeIpcBackend
```

---

# 606.169 — Deterministic Resource Tests

Tests shall simulate:

```text
quota exhaustion
pressure transitions
reservation conflicts
resource leaks
process crashes
service restart
policy reload
deadline expiry
cancellation
```

without relying on wall-clock sleeps.

---

# 606.170 — Property Testing

Properties:

```text
usage never becomes negative
child committed capacity <= parent capacity
released resource eventually becomes available
generation prevents stale ownership
hard quota is never exceeded beyond documented tolerance
reservation cannot exceed parent capacity
```

---

# 606.171 — Fuzzing

Fuzz:

```text
resource manifests
quota values
hierarchy trees
multi-resource transactions
policy updates
resource events
platform backend reports
```

Targets:

```text
overflow
underflow
integer wrap
deadlock
race
stale handle
double release
double charge
```

---

# 606.172 — Fault Injection

Inject:

```text
OS allocation failure
GPU allocation failure
counter corruption
process crash
IPC disconnect
backend timeout
policy reload race
resource backend unavailable
```

The governor must recover without corrupting accounting.

---

# 606.173 — Integer Safety

All resource arithmetic shall use checked arithmetic.

Dangerous operations:

```text
quota + burst
child_sum + reservation
bytes * count
time * frequency
```

shall detect overflow.

---

# 606.174 — Precision

Resource counters shall use appropriate widths.

Recommended minimum:

```text
u64
```

for:

- bytes;
- CPU nanoseconds;
- operation counts;
- handles;
- sequence numbers.

Long-lived systems must not overflow under normal operation.

---

# 606.175 — ABI Stability

Public resource structures shall use versioned layouts where ABI exposure is required.

Internal structures may evolve without ABI guarantees.

Machine-readable manifests shall contain:

```text
schema_version
```

---

# 606.176 — AI-Readable Resource Metadata

Compiled artifacts should expose a structured resource summary:

```text
resources {
    cpu {
        required
        optional
    }

    memory {
        peak_estimate
        runtime_dynamic
    }

    gpu {
        optional
        memory_estimate
    }
}
```

This assists future Axiom tooling and AI agents in understanding executable requirements.

---

# 606.177 — Resource Inspection CLI

The native toolchain should eventually provide:

```text
axiom resource list
axiom resource inspect
axiom resource tree
axiom resource usage
axiom resource policy
axiom resource pressure
```

Example conceptual output:

```text
Application: MyApp

CPU       31%
Memory    422 MiB / 1 GiB
Threads   12 / 32
IPC       2.1 MiB / 16 MiB
GPU       742 MiB / 2 GiB

Pressure:
CPU       Normal
Memory    Warning
GPU       Normal
```

---

# 606.178 — Runtime Introspection API

```text
fn ResourceGovernor.snapshot(
    self,
    scope: ResourceScopeId
) -> ResourceSnapshot
```

Snapshot data shall be immutable.

---

# 606.179 — Minimal Embedded API

For constrained targets:

```text
ResourceGovernor.init()
ResourceGovernor.limit()
ResourceGovernor.used()
ResourceGovernor.acquire()
ResourceGovernor.release()
```

Advanced telemetry may be compiled out.

---

# 606.180 — Resource Governor Bootstrap

The governor itself shall start in phases:

```text
Phase 1:
platform discovery

Phase 2:
system limits

Phase 3:
deployment policy

Phase 4:
application scopes

Phase 5:
service/process scopes

Phase 6:
normal runtime
```

No application resource allocation shall occur before its governing scope exists.

---

# 606.181 — Startup Failure

If mandatory resource policy cannot be established:

```text
application startup fails
```

The failure shall be reported through BOOTSTRAP-602.

---

# 606.182 — Runtime Failure

If the governor encounters an internal consistency failure:

```text
fail closed for protected resources
```

rather than allowing uncontrolled allocation.

---

# 606.183 — Governor Self-Protection

The governor shall reserve internal resources for itself:

```text
control memory
diagnostic buffer
emergency event buffer
control threads/tasks
```

This ensures resource exhaustion cannot completely disable governance.

---

# 606.184 — Emergency Reserve

A small emergency reserve shall be protected from ordinary allocations.

It may be used for:

```text
diagnostics
shutdown
crash reporting
resource reconciliation
recovery
```

This integrates with BOOTSTRAP-602.

---

# 606.185 — Resource Exhaustion Sequence

Recommended sequence:

```text
Normal
 ↓
Soft Limit
 ↓
Pressure
 ↓
Throttle
 ↓
Reclaim
 ↓
Admission Reject
 ↓
Drain Optional Work
 ↓
Stop Optional Services
 ↓
Graceful Recovery
 ↓
Force Action
```

The exact path is resource/policy dependent.

---

# 606.186 — No Silent Kill

The governor shall never silently terminate a process because of resource pressure.

Termination must generate:

```text
ResourceTerminationRequested
```

and integrate with supervisor diagnostics.

---

# 606.187 — Resource Kill Reason

If termination occurs:

```text
reason = ResourceExhaustion
resource = Memory
scope = ServiceA
usage = ...
limit = ...
policy_epoch = ...
```

This allows BOOTSTRAP-602 to explain the failure.

---

# 606.188 — Resource Governance and Crash Diagnosis

A crash record should include:

```text
resource pressure state
recent quota violations
recent throttling
recent allocation failures
```

This helps distinguish:

```text
software crash
resource exhaustion
OS termination
policy rejection
```

---

# 606.189 — Resource Governor and Logging

Logging itself consumes resources.

Therefore logging shall have:

```text
log buffer quota
disk quota
CPU budget
emergency reserve
```

This prevents diagnostics from becoming the cause of resource exhaustion.

---

# 606.190 — Resource Governor and Checkpointing

Checkpoint storage shall have a dedicated budget.

A checkpoint must not consume the entire application's ordinary storage quota.

---

# 606.191 — Resource Governor and Configuration

Configuration reload must reserve enough resources for:

```text
parse
validate
new policy snapshot
old/new transition
```

Large configurations cannot bypass quotas merely because they are configuration data.

---

# 606.192 — Resource Governor and IPC

Governor events may themselves use IPC.

Therefore the governor shall avoid depending exclusively on ordinary application IPC for emergency control.

A minimal local control path must remain available.

---

# 606.193 — Resource Governor and Security

Resource Governor shall never become a security bypass.

Forbidden:

```text
resource override
→ implicit file permission
```

or:

```text
high CPU priority
→ privileged capability
```

---

# 606.194 — Resource Governor and FFI

Foreign libraries may allocate resources outside Axiom's direct control.

FFI boundaries shall therefore support:

```text
external resource declaration
resource attribution
resource reservation
cleanup callback
```

Best-effort accounting shall be reported explicitly.

---

# 606.195 — External Library Isolation

A service using an external library should preferably run inside its own resource scope.

This prevents uncontrolled library allocations from consuming the entire application budget.

---

# 606.196 — Native Library ABI

Axiom-native libraries may declare:

```text
resource requirements
resource cleanup hooks
resource ownership rules
```

The linker can merge these declarations.

---

# 606.197 — Plugin Isolation

Plugins shall receive a separate resource scope by default.

Example:

```text
Application
 └── PluginGroup
      ├── Plugin A
      └── Plugin B
```

A plugin must not inherit unlimited application capacity.

This complements BOOTSTRAP-603 sandboxing.

---

# 606.198 — Plugin Failure

Plugin resource exhaustion shall preferably affect only:

```text
plugin scope
```

rather than the entire application.

The supervisor may terminate/restart the plugin according to BOOTSTRAP-605.

---

# 606.199 — Resource Profiles

Axiom shall support predefined profiles:

```text
Desktop
Server
Mobile
Embedded
WASM
GPUCompute
Interactive
Background
```

Profiles are configuration templates, not hard-coded behavior.

---

# 606.200 — Example Desktop Profile

```text
profile Desktop {
    cpu {
        adaptive = true
    }

    memory {
        pressure_notifications = true
    }

    io {
        background_throttle = true
    }
}
```

---

# 606.201 — Example Server Profile

```text
profile Server {
    cpu {
        reservations = true
    }

    memory {
        hard_limits = true
    }

    process {
        strict_limits = true
    }
}
```

---

# 606.202 — Example GPU Profile

```text
profile GPUCompute {
    gpu {
        memory_tracking = true
        stream_limits = true
        context_limits = true
    }
}
```

---

# 606.203 — Resource Policy Compilation

Configuration compiler shall transform:

```text
human-readable policy
```

into:

```text
canonical ResourcePolicyIR
```

This IR can then be embedded into the executable or deployment manifest.

---

# 606.204 — Resource Policy IR

Conceptual:

```text
ResourcePolicyIR {
    schema
    scope_id
    parent_id

    resource_rules[]
    inheritance
    reservations
    delegation
    enforcement
}
```

The IR must be deterministic.

---

# 606.205 — Link-Time Validation

The linker shall detect:

```text
conflicting resource declarations
impossible reservations
unsupported mandatory resource requirements
duplicate scope IDs
invalid hierarchy
```

before producing the final executable.

---

# 606.206 — Runtime Validation

Runtime must still validate external deployment policy.

Compiled metadata cannot override deployment restrictions.

---

# 606.207 — Resource Governor Versioning

Resource policies shall contain:

```text
schema_version
policy_version
runtime_compatibility
```

Backward-compatible policy changes should not require recompilation where possible.

---

# 606.208 — Backward Compatibility

New resource classes may be added without invalidating old binaries.

Unknown resource types should produce:

```text
UnsupportedResource
```

rather than memory corruption or silent unlimited allocation.

---

# 606.209 — Resource Naming

Canonical resource names shall be stable:

```text
cpu.time
cpu.weight
memory.virtual
memory.resident
memory.shared
thread.count
process.count
handle.count
ipc.queue_bytes
gpu.memory
io.read_bytes
io.write_bytes
storage.bytes
timer.count
```

---

# 606.210 — Resource Unit Normalization

All internal accounting shall normalize to canonical units.

Examples:

```text
memory → bytes
CPU time → nanoseconds
bandwidth → bytes/sec
count → integer
duration → nanoseconds
```

Human-friendly units are compiler/parser syntax only.

---

# 606.211 — Resource Counter Semantics

Counters shall explicitly declare:

```text
monotonic
current
peak
rate
budget
quota
```

Example:

```text
memory.current
memory.peak
io.read_bytes
cpu.time
```

No ambiguous "usage" field.

---

# 606.212 — Peak Tracking

The governor may track:

```text
peak resident memory
peak virtual memory
peak GPU memory
peak queue depth
peak thread count
```

Peak counters reset only through explicit administrative operation or lifecycle boundary.

---

# 606.213 — Rate Limits

Rate resources use sliding or periodic windows.

Examples:

```text
network.bytes_per_second
disk.iops
gpu.commands_per_second
```

The window mechanism must be documented.

---

# 606.214 — Token Bucket

Rate-limited resources may use a bounded token bucket:

```text
capacity
refill_rate
current_tokens
```

The bucket must itself have a maximum capacity.

No unlimited burst accumulation is permitted.

---

# 606.215 — CPU Budget Model

CPU quotas may use:

```text
period
quota
```

while weighted fairness uses:

```text
weight
```

Reservations use:

```text
minimum_guaranteed_share
```

These concepts must not be conflated.

---

# 606.216 — Resource Arbitration Order

Recommended order:

```text
security
→ hard limits
→ reservations
→ required workload
→ priority
→ fairness
→ best effort
```

No scheduling preference can override security or hard resource boundaries.

---

# 606.217 — Required vs Best Effort

Example:

```text
Database request = Required
Thumbnail generation = BestEffort
```

Under pressure:

```text
thumbnail generation
```

may be delayed while:

```text
database request
```

continues within its declared budget.

---

# 606.218 — Resource Admission Hints

Applications may provide:

```text
latency_sensitive
throughput_sensitive
energy_sensitive
background
```

These are scheduling hints, not security permissions.

---

# 606.219 — Energy Budget

Mobile/embedded targets may expose:

```text
energy_budget
thermal_pressure
```

as optional resource dimensions.

These are not mandatory in the core desktop resource model.

---

# 606.220 — Thermal Pressure

Platform adapters may report:

```text
Normal
Warm
Hot
Critical
```

The governor can recommend:

```text
reduce CPU
reduce GPU
reduce background work
```

This is particularly useful on mobile.

---

# 606.221 — Battery-Aware Workloads

A workload may declare:

```text
energy_class = BestEffort
```

The governor may defer it under battery/thermal pressure.

---

# 606.222 — Resource Policy Priority

When multiple policies apply:

```text
OS
→ Deployment
→ Security
→ Application
→ Resource Group
→ Service
→ Process
→ Task
```

the most restrictive effective policy applies unless explicit delegation exists.

---

# 606.223 — Policy Conflict

If two policies conflict:

```text
stricter effective limit
```

wins for resource safety.

For required reservations, startup shall fail if they cannot be satisfied.

---

# 606.224 — Resource Policy Explainability

The runtime shall be able to explain:

```text
Why was this allocation rejected?
```

Example:

```text
Request:
    128 MiB

Rejected because:
    Process limit = 512 MiB
    current = 450 MiB
    request = 128 MiB
    ancestor limit = 512 MiB
```

This is important for diagnostics and AI tooling.

---

# 606.225 — Explain API

```text
fn ResourceGovernor.explain(
    self,
    request: ResourceRequest
) -> AdmissionExplanation
```

The explanation must not reveal unauthorized policy information.

---

# 606.226 — Resource Policy Dry Run

Deployment tools may execute:

```text
axiom resource validate
```

without launching the application.

It should detect:

```text
unsatisfied reservations
quota conflicts
unsupported platform requirements
```

---

# 606.227 — Resource Budget Planning

Build/deployment tooling may calculate:

```text
minimum
expected
peak
```

for each resource.

Example:

```text
memory:
    minimum = 128 MiB
    expected = 384 MiB
    peak = 768 MiB
```

These values are metadata, not runtime guarantees unless explicitly configured as limits.

---

# 606.228 — Runtime Resource Contract

Axiom shall distinguish:

```text
Requirement
Reservation
Limit
Observed Usage
```

Example:

```text
Requirement: GPU
Reservation: 512 MiB
Limit: 2 GiB
Observed: 740 MiB
```

---

# 606.229 — Resource Contract Violation

If a required resource becomes unavailable:

```text
ResourceContractViolation
```

is emitted.

Supervisor may apply recovery according to service policy.

---

# 606.230 — Resource Governor and Service Health

Health checks may include resource conditions:

```text
Healthy
Degraded due to CPU pressure
Degraded due to memory pressure
Unhealthy due to quota exhaustion
```

These statuses integrate with BOOTSTRAP-605.

---

# 606.231 — Resource-Based Health Checks

Example:

```text
health {
    memory_pressure < Critical
    queue_depth < 90%
}
```

The service itself defines semantic health.

The governor only provides measurements.

---

# 606.232 — Resource Pressure Propagation

Pressure may propagate upward:

```text
Process
 ↓
Service
 ↓
Application
 ↓
Deployment
```

This allows supervisors to understand whether a local resource issue threatens the application.

---

# 606.233 — Pressure Isolation

Pressure should not automatically propagate from one sibling:

```text
Service A
```

to:

```text
Service B
```

unless they share a constrained ancestor resource.

---

# 606.234 — Bulkhead Model

Applications may create isolated groups:

```text
CriticalGroup
BackgroundGroup
PluginGroup
```

Each gets separate resource capacity.

This reduces cascading resource failures.

---

# 606.235 — Circuit Breaker Integration

When a service repeatedly exhausts a resource:

```text
healthy
→ pressured
→ resource failures
→ circuit open
```

BOOTSTRAP-605 may temporarily stop sending work to the service.

---

# 606.236 — Queue Admission and Circuit Breaker

Requests should be rejected before queues become catastrophically full.

Example:

```text
queue usage > 90%
```

may trigger:

```text
backpressure
```

before:

```text
queue usage = 100%
```

---

# 606.237 — Resource Governor and Application State

Resource state may be included in checkpoints:

```text
current policy
resource group topology
persistent reservations
```

but not transient OS handles.

---

# 606.238 — Resource Rehydration

After restore:

```text
persistent policy
→ recreate scopes
→ recreate reservations
→ reacquire actual resources
```

Failed resource acquisition shall be explicit.

---

# 606.239 — No False Restore

A restored application shall never assume:

```text
GPU context
thread
file descriptor
IPC channel
```

still exists merely because it existed in a checkpoint.

---

# 606.240 — Resource Reacquisition

Transient resources must be recreated through normal:

```text
security
+
admission
+
allocation
```

paths.

---

# 606.241 — Resource Limits on Checkpoint Restore

Restoration itself consumes resources.

The governor shall budget:

```text
checkpoint memory
decode buffers
temporary storage
worker threads
```

during restore.

---

# 606.242 — Resource Governor and Crash Reporting

Crash reporting shall have a reserved emergency path.

At minimum:

```text
emergency memory
emergency storage
emergency logging buffer
```

shall remain available where platform permits.

---

# 606.243 — Minimal Crash Path

The emergency path must avoid:

```text
heap allocation
complex locks
unbounded logging
network dependency
```

where possible.

---

# 606.244 — Resource Governor and Observability Limits

Metrics and tracing must themselves obey:

```text
memory quota
CPU budget
storage quota
event-rate limits
```

Telemetry cannot be unlimited.

---

# 606.245 — Event Rate Limiting

A noisy resource event source shall be bounded.

Example:

```text
quota_rejected > 10000/s
```

may be aggregated.

Instead of 10,000 log records:

```text
QuotaRejected:
    count = 10000
```

---

# 606.246 — Aggregated Diagnostics

The governor shall support aggregation by:

```text
resource
scope
error
time window
```

to minimize overhead.

---

# 606.247 — Resource Telemetry Sampling

High-frequency resources may expose:

```text
sample_rate
aggregation_interval
```

while exact counters remain available for critical limits.

---

# 606.248 — Runtime Overhead Target

Normal resource accounting should target:

```text
near O(1)
```

for local allocation/release decisions.

Hierarchical policy resolution should be cached.

Administrative operations may be:

```text
O(number_of_scopes)
```

or equivalent.

---

# 606.249 — Memory Overhead

Governor metadata should scale approximately with:

```text
O(scopes + governed resources + waiters)
```

and not with every individual allocation when aggregation is sufficient.

---

# 606.250 — No Per-Allocation Heap Requirement

A high-frequency allocation should not require a heap allocation solely for governor bookkeeping.

---

# 606.251 — Resource Event Buffer

Events may use bounded ring buffers.

When full:

```text
aggregate
drop low-priority events
retain critical events
```

Critical resource/security events must have reserved capacity.

---

# 606.252 — Resource Governor API Surface

Core API should remain small:

```text
create_scope
destroy_scope

policy
snapshot

reserve
acquire
release
consume

pressure
reclaim

wait
cancel

explain
```

Everything else should be layered.

---

# 606.253 — Core vs Extended Runtime

**Core:**

```text
CPU
memory
threads
processes
handles
basic IPC
```

**Extended:**

```text
GPU
thermal
energy
advanced telemetry
adaptive policies
forecasting
```

This preserves portability.

---

# 606.254 — Resource Governor Invariants

The following are mandatory:

1. usage cannot become negative;
2. resources cannot be released twice;
3. stale generations cannot own resources;
4. child capacity cannot exceed delegated parent capacity;
5. hard limits cannot be silently bypassed;
6. security cannot be bypassed by resource priority;
7. reservations cannot exceed available parent capacity;
8. policy updates are atomic;
9. resource transactions are all-or-nothing;
10. cancellation cannot leak reservations;
11. process crash cannot permanently leak transient resources;
12. resource accounting must remain internally consistent;
13. unsupported enforcement must be reported;
14. diagnostics cannot require unlimited resources;
15. emergency resources remain available according to platform capability.

---

# 606.255 — Acceptance Criteria

BOOTSTRAP-606 is considered architecturally complete when:

1. CPU quotas are defined.
2. CPU reservations are defined.
3. CPU weights are defined.
4. CPU affinity boundary is defined.
5. memory categories are separated.
6. memory hard limits are defined.
7. memory pressure is defined.
8. thread quotas are defined.
9. task quotas are defined.
10. process quotas integrate with BOOTSTRAP-605.
11. handle quotas are defined.
12. FD quotas are defined.
13. IPC quotas integrate with BOOTSTRAP-604.
14. shared-memory charging is defined.
15. GPU resources are modeled.
16. GPU enforcement strength is explicit.
17. I/O bandwidth is modeled.
18. IOPS is modeled.
19. storage quotas are modeled.
20. timer quotas are modeled.
21. hierarchical scopes are defined.
22. reservations are defined.
23. soft limits are defined.
24. hard limits are defined.
25. burst capacity is defined.
26. delegation is defined.
27. borrowing is bounded.
28. pressure levels are defined.
29. reclamation is defined.
30. admission control is defined.
31. fairness is defined.
32. starvation prevention is defined.
33. multi-resource transactions are defined.
34. resource ownership is generation-safe.
35. policy reload is atomic.
36. configuration integration with BOOTSTRAP-601 is defined.
37. security integration with BOOTSTRAP-603 is defined.
38. diagnostics integration with BOOTSTRAP-602 is defined.
39. IPC integration with BOOTSTRAP-604 is defined.
40. supervisor integration with BOOTSTRAP-605 is defined.
41. state/checkpoint integration with BOOTSTRAP-600 is defined.
42. platform adapters are defined.
43. unsupported platform enforcement is explicit.
44. compiler metadata is defined.
45. linker resource metadata is defined.
46. dead stripping is defined.
47. no GC dependency exists.
48. no global hot-path lock is required.
49. deterministic testing infrastructure is defined.
50. fuzzing and fault injection are defined.
51. resource leaks are detectable.
52. crash recovery is defined.
53. emergency reserves are defined.
54. telemetry itself is bounded.
55. resource policy explanation is defined.

---

# 606.256 — Final Architecture

The resulting Axiom runtime architecture becomes:

```text
                         ┌───────────────────────────┐
                         │     BOOTSTRAP-601         │
                         │ Config / Deployment       │
                         └─────────────┬─────────────┘
                                       │
                         ┌─────────────▼─────────────┐
                         │     BOOTSTRAP-603         │
                         │ Security / Capabilities   │
                         └─────────────┬─────────────┘
                                       │
                         ┌─────────────▼─────────────┐
                         │      RESOURCE GOVERNOR    │
                         │       BOOTSTRAP-606       │
                         │                           │
                         │ Policy                    │
                         │ Accounting                │
                         │ Admission                 │
                         │ Reservations              │
                         │ Budgets                   │
                         │ Quotas                   │
                         │ Pressure                  │
                         │ Reclamation               │
                         │ Fairness                  │
                         └─────────────┬─────────────┘
                                       │
          ┌────────────────────────────┼────────────────────────────┐
          │                            │                            │
          ▼                            ▼                            ▼
       CPU/Memory                  IPC/GPU                      I/O/Storage
          │                            │                            │
          └────────────────────────────┼────────────────────────────┘
                                       │
                         ┌─────────────▼─────────────┐
                         │     BOOTSTRAP-605         │
                         │ Supervisor / Services     │
                         └─────────────┬─────────────┘
                                       │
                         ┌─────────────▼─────────────┐
                         │      Axiom Processes      │
                         │      Services / Tasks     │
                         └───────────────────────────┘

      BOOTSTRAP-600 → State / Checkpoints / Recovery
      BOOTSTRAP-602 → Diagnostics / Metrics / Crash
      BOOTSTRAP-604 → IPC / Shared Memory
```

The critical architectural decision is that **resource governance becomes a shared platform primitive**, rather than a collection of independent limits scattered across memory, IPC, processes, GPU and services.

---

# 606.257 — Relationship to Previous Bootstrap Layers

```text
600 State
    ↓
601 Configuration
    ↓
602 Diagnostics
    ↓
603 Security
    ↓
604 IPC
    ↓
605 Process/Service Supervision
    ↓
606 Resource Governance
```

BOOTSTRAP-606 does not replace those layers.

It provides the common resource substrate they all consume.

---

# 606.258 — Completion Status

**BOOTSTRAP-606 — COMPLETE**

Architecture now defines:

```text
Resource identity
Resource ownership
Resource scopes
Resource groups
Budgets
Quotas
Reservations
Delegation
Burst
Borrowing
Admission
Accounting
Pressure
Reclamation
Fairness
CPU
Memory
Threads
Processes
Handles
IPC
Shared memory
GPU
I/O
Storage
Timers
Platform enforcement
Security integration
Configuration integration
Diagnostics integration
State integration
Supervisor integration
Compiler/linker integration
Testing
```

The next architectural layer is therefore:

# BOOTSTRAP-607
## Native Application Scheduling, Threading, Async Runtime, Executors & Work-Stealing Runtime 5.0

Primary scope:

```text
OS threads
Axiom tasks
fibers
executors
work queues
work stealing
CPU scheduling
priority
affinity
async/await
futures
cancellation
deadlines
timers
I/O completion
blocking isolation
structured concurrency
parallelism
NUMA awareness
GPU task submission
resource-governor integration
```

The key boundary is:

```text
BOOTSTRAP-606
    = "How much resource may this workload consume?"

BOOTSTRAP-607
    = "How is that workload actually scheduled and executed?"
```

:::

**BOOTSTRAP-606 đã hoàn tất.** Chuỗi kiến trúc tiếp theo là **BOOTSTRAP-607 — Scheduling, Threading, Async Runtime, Executors & Work-Stealing**.