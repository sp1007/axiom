Tiếp tục với task kế tiếp trong chuỗi Axiom: **BOOTSTRAP-629**.

:::writing{variant="document" id="58317" title="BOOTSTRAP-629 — Native Distributed Workflow, Jobs, Scheduling, Orchestration, Durable Tasks, Sagas, Compensation & Long-Running Process Runtime 5.0"}

# BOOTSTRAP-629
## Native Distributed Workflow, Jobs, Scheduling, Orchestration, Durable Tasks, Sagas, Compensation & Long-Running Process Runtime 5.0

**Status:** COMPLETE  
**Layer:** Distributed Application Runtime  
**Depends on:** BOOTSTRAP-600 → BOOTSTRAP-628  
**Primary dependencies:** 605, 607, 612, 626, 627, 628  
**Optional integrations:** 619, 622, 623, 624  
**Core principle:** durable distributed execution without requiring Kubernetes, a cloud provider, a message broker, a GC runtime, or a third-party workflow engine.

---

# 1. Purpose

BOOTSTRAP-629 defines Axiom's native runtime for:

- workflows;
- jobs;
- scheduled jobs;
- durable tasks;
- task queues;
- worker pools;
- orchestration;
- long-running processes;
- durable timers;
- signals;
- retries;
- timeouts;
- cancellation;
- compensation;
- Sagas;
- human tasks;
- workflow recovery;
- deterministic replay;
- distributed execution;
- workflow versioning;
- execution history;
- workflow migration;
- failure recovery.

The system is designed for workloads ranging from:

```text
single-machine scheduled task
        ↓
local durable workflow
        ↓
multi-process workflow
        ↓
multi-node distributed workflow
        ↓
months-long business process
```

The runtime must remain useful even when only a small subset is enabled.

---

# 2. Non-Goals

629 does not define:

- a general-purpose distributed database;
- a new network protocol replacing 626;
- a new consensus algorithm replacing 627;
- a new storage engine replacing 611/628;
- a general-purpose actor model;
- a cloud-specific orchestration platform;
- Kubernetes compatibility as a core requirement;
- mandatory GUI tooling;
- mandatory human workflow functionality;
- exactly-once distributed execution;
- distributed ACID transactions.

---

# 3. Architectural Position

```text
                    AXIOM APPLICATION
                           │
                           ▼
              ┌────────────────────────┐
              │       629 WORKFLOW      │
              │        RUNTIME          │
              ├────────────────────────┤
              │ Workflow Engine         │
              │ Job Engine              │
              │ Scheduler               │
              │ Task Queues             │
              │ Workers                 │
              │ Durable Timers          │
              │ Signals                 │
              │ Retry Engine            │
              │ Saga/Compensation       │
              │ Replay/Recovery         │
              └────────────┬───────────┘
                           │
       ┌───────────────────┼────────────────────┐
       ▼                   ▼                    ▼
    627                  628                   626
Coordination        Distributed Data       Network/RPC
       │                   │                    │
       └───────────┬───────┴────────────┬───────┘
                   ▼                    ▼
                  611                  607
              Local Storage         Scheduler
                   │                    │
                   ▼                    ▼
                  605                  606
             Supervision         Resource Governor
```

629 orchestrates execution.

It does **not** own the underlying distributed consensus, network transport, or durable storage mechanisms.

---

# 4. Fundamental Design Principle

Axiom distinguishes:

```text
Workflow decision
Activity execution
Persistent state
Distributed coordination
Worker execution
```

These must never be implicitly conflated.

For example:

```text
workflow:
    if account.balance >= amount:
        charge_card()
```

The `if` decision belongs to the deterministic workflow.

`charge_card()` is an external side effect and therefore belongs to an activity.

Conceptually:

```text
Workflow
    │
    ├── deterministic decision
    │
    └── Activity
            │
            └── external side effect
```

This distinction is fundamental to deterministic replay.

---

# 5. Core Abstractions

629 defines:

```text
Workflow
WorkflowId
WorkflowVersion
WorkflowInstance
WorkflowRun

WorkflowStep
StepId
Activity
ActivityId

Task
TaskId
Job
JobId

Schedule
ScheduleId
Trigger
TriggerId

Worker
WorkerId
WorkerLease

TaskQueue
QueueId
QueuePartition

ExecutionContext

WorkflowState
WorkflowCheckpoint
WorkflowHistory
WorkflowSnapshot

Timer
TimerId
Signal
SignalId

RetryPolicy
TimeoutPolicy
CancellationPolicy

Compensation
CompensationId
Saga
SagaId

HumanTask
HumanTaskId

WorkflowDefinition
WorkflowMigration
WorkflowVersionPolicy
```

Every externally visible identity is generation-safe where required.

---

# 6. Workflow Definition

A workflow is a deterministic executable state machine.

A workflow may contain:

```text
sequence
branch
loop
parallel
join
wait
timer
signal
activity
sub-workflow
compensation
failure handler
retry policy
timeout
cancellation
```

Example:

```text
workflow OrderProcess(order):

    reserve_inventory(order)

    charge_payment(order)

    ship(order)

    notify_customer(order)
```

A more complex workflow:

```text
workflow OrderProcess(order):

    reserve_inventory(order)

    parallel:
        charge_payment(order)
        validate_shipping_address(order)

    join

    if payment_failed:
        compensate_reservation()
        return Failed

    ship(order)

    wait for delivery_confirmation

    notify_customer()
```

---

# 7. Workflow State Machine

Every workflow instance has an explicit lifecycle.

```text
Created
  ↓
Starting
  ↓
Running
  ├── Waiting
  ├── Suspended
  ├── Compensating
  ├── Cancelling
  ├── Failed
  └── Completed
```

Terminal states:

```text
Completed
Failed
Cancelled
Terminated
Abandoned
```

State transitions must be durable.

Invalid transitions must be rejected.

---

# 8. Workflow Identity

A workflow instance is identified by:

```text
WorkflowId
WorkflowVersion
WorkflowInstanceId
WorkflowRunId
Generation
```

These have different meanings.

```text
WorkflowId
    logical workflow definition

WorkflowVersion
    immutable definition version

WorkflowInstanceId
    durable business/process instance

WorkflowRunId
    execution generation

Generation
    fencing/recovery generation
```

A retry or worker restart must not silently create a new logical workflow instance.

---

# 9. Workflow Version

Workflow definitions are immutable after publication.

Example:

```text
OrderWorkflow@1
OrderWorkflow@2
OrderWorkflow@3
```

Running instances are normally pinned to their original version.

Migration requires explicit policy.

```text
WorkflowVersionPolicy:
    Pinned
    Compatible
    Migratable
```

No implicit source-code replacement is allowed to alter running workflows.

---

# 10. Deterministic Workflow Execution

Workflow decision code must be deterministic.

Forbidden inside deterministic workflow code:

```text
random()
system_time()
read_file()
network_request()
database_write()
environment_variable()
process_id()
thread_id()
GPU query
OS device query
```

Instead:

```text
now()
random()
activity(...)
signal(...)
```

must pass through deterministic runtime boundaries.

For example:

```text
t = workflow.now()
```

returns a workflow time derived from recorded execution state.

---

# 11. Side Effects

All external side effects are activities.

Examples:

```text
send_email()
charge_payment()
write_file()
publish_event()
call_http()
invoke_gpu()
access_camera()
start_process()
```

The workflow engine records:

```text
ActivityScheduled
ActivityStarted
ActivityCompleted
ActivityFailed
```

Replay uses the recorded activity result rather than executing the activity again.

---

# 12. Activity Model

An activity is executable work outside deterministic workflow evaluation.

Conceptual signature:

```text
activity<TInput, TOutput>(
    input: TInput,
    context: ActivityContext
) -> Result<TOutput, Error>
```

Activities may:

- access network;
- access files;
- access devices;
- access databases;
- call other services;
- perform CPU work;
- perform GPU work.

Activities are subject to:

- capabilities;
- resource budgets;
- timeouts;
- retries;
- cancellation;
- worker policies.

---

# 13. Activity Idempotency

Default distributed execution semantics are:

```text
AT_LEAST_ONCE
```

Therefore an activity may execute more than once.

Every retryable side-effecting activity should support an idempotency key.

Example:

```text
idempotency_key =
    hash(WorkflowInstanceId, StepId, ActivityAttemptGroup)
```

The external service may use that key to deduplicate operations.

Axiom does not claim exactly-once execution merely because an operation has an idempotency key.

---

# 14. Exactly-Once Semantics

629 explicitly does **not** guarantee global exactly-once execution.

Instead:

```text
durable state
+
at-least-once delivery
+
idempotent activity
+
deduplication
+
fencing
```

provide practical exactly-once *effects* where the external system supports them.

This distinction must be visible in the API and documentation.

---

# 15. Workflow History

Every durable workflow maintains an append-only logical history.

Example:

```text
WorkflowStarted
ActivityScheduled
ActivityStarted
ActivityCompleted
TimerCreated
TimerFired
SignalReceived
StepCompleted
WorkflowCheckpointed
WorkflowCompleted
```

History is stored through:

```text
629
 ↓
628
 ↓
612
 ↓
611
```

The workflow runtime does not require a proprietary storage engine.

---

# 16. Workflow Snapshot

Long workflows cannot replay unlimited history forever.

Therefore 629 supports:

```text
History
+
Snapshot
+
History after snapshot
```

A snapshot contains:

```text
WorkflowVersion
SchemaFingerprint
State
CompletedStepSet
PendingTimers
PendingActivities
PendingSignals
CompensationState
ReplayPosition
```

Snapshots must be immutable once committed.

---

# 17. Replay

Recovery process:

```text
load latest snapshot
        ↓
load subsequent history
        ↓
replay deterministic decisions
        ↓
reconstruct pending work
        ↓
resume execution
```

Replay must not repeat external side effects.

---

# 18. Replay Determinism Rule

For identical:

```text
WorkflowVersion
InitialState
History
```

the workflow engine must produce identical:

```text
next state
next commands
next timers
next activities
```

Any nondeterministic API used inside a workflow is a compiler/runtime error where statically detectable.

---

# 19. Durable Timer

Timers must survive:

- process crash;
- worker restart;
- machine restart;
- coordinator restart;
- node failure.

Example:

```text
workflow.wait(Duration.days(30))
```

must not require a process to remain alive for 30 days.

The runtime stores:

```text
TimerId
Deadline
WorkflowInstanceId
Generation
Status
```

---

# 20. Timer Semantics

Timer clock domain must be explicit.

Supported:

```text
MonotonicDuration
WallClockInstant
CalendarTime
```

Long-running schedules use wall-clock/calendar semantics.

Timeouts use monotonic time where possible.

This avoids confusing:

```text
"run after 10 minutes"
```

with:

```text
"run at 09:00 local time"
```

---

# 21. Job Model

A job is a unit of independently schedulable work.

```text
Job:
    JobId
    Payload
    Queue
    Priority
    Schedule
    RetryPolicy
    TimeoutPolicy
    ResourcePolicy
    CapabilityPolicy
```

Jobs may be:

```text
one-shot
periodic
scheduled
event-triggered
manually triggered
workflow-generated
```

---

# 22. Task Model

A task is a concrete execution request.

```text
Task:
    TaskId
    JobId
    WorkflowInstanceId?
    StepId?
    QueueId
    Attempt
    Lease
    Deadline
    Priority
```

A job can create many tasks.

A workflow step can create one or more tasks.

---

# 23. Task Queue

629 defines durable task queues.

Operations:

```text
enqueue()
receive()
lease()
ack()
nack()
delay()
dead_letter()
requeue()
```

Queue properties:

```text
durable
bounded
partitioned
ordered
priority-aware
backpressure-aware
```

---

# 24. Queue Delivery

Supported semantics:

```text
AtLeastOnce
AtMostOnce
BestEffort
```

Exactly-once queue delivery is not a core semantic.

The default is:

```text
AtLeastOnce
```

because durability and failure recovery are more important than pretending duplicates cannot occur.

---

# 25. Task Lease

A worker receives a lease.

```text
TaskLease:
    TaskId
    WorkerId
    LeaseId
    Expiration
    Generation
```

A worker must renew long-running tasks.

If the lease expires:

```text
task becomes eligible for reassignment
```

unless a fencing mechanism prevents stale execution from committing results.

---

# 26. Fencing

Every worker execution receives a fencing token.

Example:

```text
FenceToken = 9182
```

A newer execution may receive:

```text
FenceToken = 9183
```

Storage or service-side commit operations can reject stale tokens.

This prevents:

```text
old worker
    ↓
network partition
    ↓
new worker executes
    ↓
old worker returns
    ↓
old worker overwrites new result
```

---

# 27. Worker Model

A worker advertises:

```text
WorkerId
Generation
Version
Capabilities
Target
Architecture
ResourceGroup
ConcurrencyLimit
Health
Queues
```

Example:

```text
Worker:
    target = x86_64-windows
    capabilities = [gpu, ffmpeg-provider, filesystem]
    queues = ["video"]
    max_concurrency = 4
```

Workers must never gain capabilities merely by claiming them.

Actual capabilities come from 603.

---

# 28. Worker Registration

Lifecycle:

```text
Discovered
Registering
Ready
Serving
Draining
Stopping
Disconnected
Failed
```

Worker registration is lease-based.

Expired registrations are removed automatically.

---

# 29. Worker Selection

Task routing considers:

```text
queue
capability
target
architecture
resource availability
priority
locality
affinity
worker health
tenant policy
```

The scheduler must not route work to a worker that lacks required capability.

---

# 30. Worker Affinity

Optional affinity:

```text
None
Workflow
Partition
DataLocality
Device
Session
```

Affinity is a preference unless explicitly marked mandatory.

Mandatory affinity can cause a task to remain queued when no matching worker exists.

---

# 31. Retry Policy

Retry configuration:

```text
max_attempts
initial_delay
max_delay
backoff
jitter
retryable_errors
non_retryable_errors
retry_budget
```

Example:

```text
RetryPolicy:
    max_attempts = 5
    backoff = Exponential
    initial_delay = 1s
    max_delay = 60s
    jitter = Full
```

---

# 32. Retry Budget

Retry storms are prohibited.

Budgets can be applied to:

```text
workflow
job
queue
tenant
service
worker
application
```

The Resource Governor 606 supplies quota/budget primitives.

---

# 33. Timeout Model

Separate timeout types:

```text
ScheduleToStartTimeout
StartToCloseTimeout
HeartbeatTimeout
WorkflowTimeout
QueueVisibilityTimeout
LeaseTimeout
```

They must not be conflated.

---

# 34. Heartbeats

Long-running activities can emit:

```text
heartbeat(progress)
```

Heartbeat state can contain:

```text
progress
checkpoint marker
estimated stage
custom status
```

Heartbeat data is bounded and rate-limited.

---

# 35. Cancellation

Cancellation propagates through:

```text
Workflow
    ↓
Step
    ↓
Task
    ↓
Activity
```

Cancellation is cooperative unless the platform provides safe termination.

A cancellation request does not imply that external side effects have been undone.

---

# 36. Cancellation Policy

Each workflow may specify:

```text
CancelImmediately
CancelAtCheckpoint
FinishCurrentActivity
Compensate
ManualResolution
```

The policy must be explicit.

---

# 37. Saga Model

A Saga represents a sequence of business operations with compensating operations.

Example:

```text
reserve_inventory
charge_payment
create_shipment
```

Compensations:

```text
release_inventory
refund_payment
cancel_shipment
```

A compensation is not a database rollback.

It is another business operation.

---

# 38. Compensation Ordering

Default order:

```text
reverse dependency order
```

Example:

```text
A
B
C
```

compensates:

```text
C'
B'
A'
```

unless an explicit dependency graph specifies otherwise.

---

# 39. Compensation Failure

Compensation can fail.

States:

```text
CompensationPending
Compensating
CompensationRetrying
CompensationFailed
Compensated
ManualInterventionRequired
```

The runtime must not silently discard a failed compensation.

---

# 40. Nested Sagas

Sagas may contain child Sagas.

A child may expose:

```text
commit
compensate
failed
```

to the parent.

Nested compensation order follows explicit dependency semantics.

---

# 41. Workflow Parallelism

Workflow execution supports:

```text
parallel
join
race
any
all
quorum
```

Example:

```text
parallel:
    A()
    B()
    C()

join all
```

The runtime records branch identities so replay remains deterministic.

---

# 42. Join Semantics

Supported join policies:

```text
All
Any
FirstSuccess
FirstCompletion
Quorum
NOfM
```

Timeout behavior must be explicitly defined.

---

# 43. Sub-Workflows

A workflow may invoke another workflow.

```text
parent
    └── child workflow
```

Policies:

```text
WaitForCompletion
FireAndForget
ContinueAsynchronously
CancelWithParent
Independent
```

Detached workflows must be explicit.

---

# 44. Signals

A signal is a durable external input to a workflow.

Examples:

```text
payment_confirmed
customer_approved
device_ready
human_decision
```

Signals are persisted before acknowledgement.

Duplicate signals must be deduplicable through:

```text
SignalId
IdempotencyKey
```

---

# 45. Signal Ordering

Ordering can be specified per:

```text
workflow instance
signal type
partition
source
```

Global ordering is not assumed.

---

# 46. External Events

External events may originate from:

```text
626 network
628 event log
IPC 604
device 614
media 616
GUI 619
plugin 623
script 624
```

629 normalizes them into durable workflow signals/events.

---

# 47. Human Tasks

Human tasks are optional.

A human task contains:

```text
HumanTaskId
Assignee
CandidateGroup
Payload
Deadline
EscalationPolicy
ClaimState
ResultSchema
```

Lifecycle:

```text
Created
Assigned
Claimed
Completed
Rejected
Expired
Escalated
Cancelled
```

The core runtime does not depend on GUI.

619/622 can provide a user interface.

---

# 48. Schedule Model

Supported schedule types:

```text
At
After
Every
Cron
Calendar
EventTriggered
Manual
```

Example:

```text
schedule daily_report:
    every day at 08:00
```

---

# 49. Time Zones

Schedules must explicitly define timezone.

Examples:

```text
UTC
Asia/Ho_Chi_Minh
America/New_York
```

Timezone database version is recorded with the schedule when reproducibility requires it.

---

# 50. DST Handling

Calendar schedules define behavior for:

```text
missing local time
duplicated local time
timezone rule change
```

Policies:

```text
Skip
ShiftForward
ShiftBackward
RunOnce
RunTwice
```

No implicit interpretation.

---

# 51. Missed Schedules

If the runtime is unavailable:

```text
Skip
CatchUp
Coalesce
BoundedCatchUp
```

Example:

```text
every 1 minute
runtime offline 2 hours
```

must not automatically create 120 executions unless configured.

---

# 52. Schedule Deduplication

Each generated execution receives:

```text
ScheduleId
OccurrenceId
```

The same occurrence must not create duplicate logical executions.

---

# 53. Distributed Scheduler

Schedules are coordinated through 627.

Only one active scheduler generation should own a partition at a time.

Ownership:

```text
partition
    ↓
lease
    ↓
fencing token
```

A stale scheduler cannot publish new schedule executions after losing ownership.

---

# 54. Scheduler Sharding

Schedules can be partitioned by:

```text
ScheduleId hash
tenant
namespace
workflow
```

Partitions may migrate between nodes.

Migration must be fenced.

---

# 55. Backpressure

When workers cannot keep up:

```text
queue depth ↑
        ↓
admission control
        ↓
rate limiting
        ↓
schedule coalescing
        ↓
priority handling
```

The runtime must not create unbounded in-memory task queues.

---

# 56. Priority

Task priorities are advisory unless the policy explicitly requires strict priority.

Supported:

```text
Critical
High
Normal
Low
Background
```

Starvation prevention is required.

---

# 57. Resource Governance

Every workflow/task can be associated with a resource scope:

```text
Workflow
Job
Tenant
Queue
Worker
Application
```

Resource classes come from 606:

```text
CPU
Memory
Threads
GPU
Network
Storage
IPC
Handles
Task count
```

---

# 58. Capability Propagation

Workflow capabilities are not automatically expanded.

A workflow may only use capabilities granted by:

```text
603 Security Boundary
627 Identity
```

An activity receives an attenuated capability set.

Example:

```text
Workflow capability:
    filesystem:/data

Activity capability:
    filesystem:/data/orders/read
```

---

# 59. Secret Handling

Secrets must not be stored as ordinary workflow state.

Forbidden:

```text
state.api_password = "..."
```

Preferred:

```text
state.api_key = SecretHandle(...)
```

Workflow history must never contain plaintext secret material.

---

# 60. Security Context

Every task execution carries:

```text
PrincipalId
TenantId?
CapabilitySet
SecurityPolicyFingerprint
WorkflowInstanceId
TraceId
```

Authorization is revalidated at execution boundaries.

---

# 61. Distributed Coordination

629 uses 627 for:

```text
leader election
partition ownership
leases
fencing
membership
coordination
```

629 does not implement its own consensus subsystem.

---

# 62. Data Persistence

629 stores durable workflow data through 628.

Logical stores:

```text
WorkflowHistoryStore
WorkflowSnapshotStore
TaskQueueStore
ScheduleStore
SignalStore
WorkerLeaseStore
CompensationStore
DeadLetterStore
```

These may map onto shared 628 infrastructure.

---

# 63. Large Data Rule

Workflow state must remain bounded.

Large payloads should use:

```text
628 distributed object/data store
613 CAS
611 filesystem
```

and workflow state contains:

```text
ObjectId
ContentHash
SchemaFingerprint
```

rather than the entire payload.

---

# 64. State Schema Evolution

Workflow state has:

```text
SchemaId
SchemaVersion
SchemaFingerprint
```

Migration uses 612 schema migration facilities.

Running workflows must never be silently decoded using an incompatible schema.

---

# 65. Workflow History Compaction

History can be compacted when:

```text
snapshot committed
+
all required readers advanced
+
retention policy permits deletion
```

Compaction must preserve enough information for:

```text
audit
recovery
replay
debugging
```

according to configured retention.

---

# 66. Dead-Letter Queue

Tasks that exceed retry policy enter:

```text
DeadLetter
```

A dead-letter record contains:

```text
TaskId
WorkflowInstanceId?
Attempts
LastError
LastWorker
HistoryReference
PayloadReference
Timestamp
```

Manual replay is supported.

---

# 67. Poison Task Protection

A permanently failing task must not consume infinite resources.

Policies include:

```text
MaxAttempts
RetryBudget
DeadLetter
Quarantine
ManualApproval
```

---

# 68. Failure Scenarios

629 must handle:

```text
worker crash
worker restart
network partition
scheduler crash
coordinator failover
storage failure
duplicate task
late activity result
expired lease
clock changes
process restart
machine reboot
partial deployment
workflow version change
```

---

# 69. Late Result Handling

Suppose:

```text
Worker A
    lease expires

Worker B
    executes task

Worker A
    eventually returns
```

Worker A's result must be rejected if its fencing token is stale.

---

# 70. Coordinator Failure

If the workflow coordinator fails:

```text
persisted workflow state
        ↓
new coordinator generation
        ↓
lease acquisition
        ↓
snapshot/history replay
        ↓
resume
```

No duplicate logical workflow instance may be created.

---

# 71. Network Partition

During a partition:

```text
old owner
```

must eventually lose authority through lease/fencing.

The system may temporarily be unable to progress.

It must not allow conflicting owners to commit indefinitely.

---

# 72. Worker Drain

Worker shutdown:

```text
Serving
   ↓
Draining
   ↓
finish or checkpoint
   ↓
release leases
   ↓
Stopped
```

Unfinished tasks are requeued according to lease semantics.

---

# 73. Workflow Suspension

A workflow can be:

```text
Paused
Suspended
```

Suspension prevents new work while preserving durable state.

Existing activities may:

```text
finish
cancel
or be allowed according to policy
```

---

# 74. Workflow Termination

Termination is stronger than cancellation.

```text
Cancel
```

means cooperative stop.

```text
Terminate
```

means the runtime stops scheduling further workflow work and records the termination.

External effects already performed are not automatically undone.

---

# 75. Abandonment

Abandonment is explicit.

It means:

```text
runtime stops ownership
```

while retaining historical information.

This is intended for manual external recovery scenarios.

---

# 76. Recovery Modes

Supported:

```text
Automatic
Manual
ObserveOnly
ReplayOnly
Repair
```

No dangerous automatic compensation should occur without policy.

---

# 77. Workflow Migration

Migration is permitted only at safe checkpoints.

A migration descriptor defines:

```text
from_version
to_version
state_transform
compatibility_rules
```

Migration must be deterministic.

---

# 78. Activity Versioning

Activities are versioned independently from workflows.

Example:

```text
ChargeCard@1
ChargeCard@2
```

Existing workflows can remain pinned to a compatible activity version.

---

# 79. Deployment Strategy

629 supports:

```text
parallel versions
rolling worker deployment
drain old workers
workflow pinning
activity compatibility windows
```

Deployment itself belongs to higher-level package/distribution systems.

---

# 80. Durable Job Scheduling

A job can survive:

```text
process restart
node restart
worker replacement
application upgrade
```

because the logical job exists independently from a process.

---

# 81. Local Mode

629 must support a local mode:

```text
single process
single storage
single scheduler
single worker pool
```

without requiring distributed infrastructure.

Profile:

```text
AXWORKFLOW_LOCAL
```

---

# 82. Durable Local Mode

Adds:

```text
611 storage
612 serialization
durable history
durable timers
recovery
```

Profile:

```text
AXWORKFLOW_DURABLE
```

---

# 83. Distributed Mode

Adds:

```text
626
627
628
distributed workers
partition ownership
replicated workflow state
```

Profile:

```text
AXWORKFLOW_DISTRIBUTED
```

---

# 84. Full Mode

Includes:

```text
workflows
jobs
scheduler
queues
workers
durable timers
signals
sagas
human tasks
distributed execution
observability
security
resource governance
```

Profile:

```text
AXWORKFLOW_FULL
```

---

# 85. Compiler Metadata

Compiler annotations:

```text
@workflow
@activity
@task
@schedule
@signal
@compensate
@deterministic
@side_effect
@retry
@timeout
@human_task
@subworkflow
```

Generated metadata:

```text
.axworkflow
.axtask
.axschedule
.axactivity
.axsaga
```

---

# 86. Static Analysis

The compiler should detect:

```text
workflow → forbidden OS call
workflow → network access
workflow → filesystem access
workflow → nondeterministic random
workflow → unbounded state
activity → missing idempotency declaration
retryable side effect → unsafe retry
workflow version → incompatible state schema
compensation → missing failure policy
```

Warnings can become errors under strict profiles.

---

# 87. IR Integration

Workflow IR contains explicit operations:

```text
workflow.begin
workflow.state.load
workflow.state.store

activity.schedule
activity.await
activity.result

timer.create
timer.await
signal.await

task.enqueue
task.await

parallel.begin
parallel.join

saga.begin
saga.compensate

workflow.checkpoint
workflow.complete
workflow.fail
```

---

# 88. Deterministic IR

The compiler marks deterministic regions.

Example:

```text
workflow.begin deterministic
```

Forbidden operations are rejected inside the region unless explicitly represented as recorded workflow operations.

---

# 89. Activity IR

Activity execution is represented separately:

```text
activity.call
```

with metadata:

```text
capabilities
retry policy
timeout
resource policy
idempotency
version
```

---

# 90. Runtime API

Struct-only API:

```text
struct WorkflowEngine {
    coordinator: CoordinatorHandle
    store: WorkflowStore
    scheduler: WorkflowScheduler
}

struct WorkflowHandle {
    id: WorkflowInstanceId
    generation: u64
}

struct TaskHandle {
    id: TaskId
    generation: u64
}
```

No mandatory classes are required.

---

# 91. Workflow API

Example:

```text
fn WorkflowEngine.start<T>(
    definition: WorkflowDefinition<T>,
    input: T
) -> Result<WorkflowHandle, WorkflowError>
```

---

# 92. Workflow Control

```text
engine.pause(workflow)
engine.resume(workflow)
engine.cancel(workflow)
engine.terminate(workflow)
engine.signal(workflow, signal)
engine.inspect(workflow)
```

---

# 93. Task API

```text
queue.enqueue(task)
queue.lease(worker)
queue.heartbeat(lease)
queue.ack(lease)
queue.nack(lease)
queue.dead_letter(lease)
```

All ownership-sensitive operations validate generation/fencing.

---

# 94. Schedule API

```text
scheduler.register(schedule)
scheduler.pause(schedule)
scheduler.resume(schedule)
scheduler.remove(schedule)
scheduler.trigger(schedule)
scheduler.inspect(schedule)
```

---

# 95. Activity Context

```text
struct ActivityContext {
    task_id: TaskId
    workflow_id: WorkflowInstanceId?
    attempt: u32
    deadline: Instant?
    cancel: CancelToken
    capabilities: CapabilitySet
    resources: ResourceScope
    trace: TraceContext
}
```

---

# 96. Workflow Context

```text
struct WorkflowContext {
    instance_id: WorkflowInstanceId
    version: WorkflowVersion
    state: WorkflowState
    history_position: u64
    deterministic_time: WorkflowTime
}
```

The context must not expose unrestricted OS facilities.

---

# 97. Workflow Event Model

Canonical events include:

```text
WorkflowStarted
WorkflowResumed
WorkflowPaused
WorkflowCancelled
WorkflowTerminated

ActivityScheduled
ActivityCompleted
ActivityFailed

TaskQueued
TaskLeased
TaskCompleted
TaskFailed

TimerCreated
TimerFired

SignalReceived

CompensationScheduled
CompensationCompleted
CompensationFailed

WorkflowCheckpointed
WorkflowCompleted
WorkflowFailed
```

---

# 98. Event Identity

Every event contains:

```text
EventId
WorkflowInstanceId
Generation
Sequence
Timestamp
SchemaFingerprint
```

Events must be uniquely identifiable.

---

# 99. Idempotent Event Processing

Consumers maintain:

```text
last_processed_sequence
```

or equivalent deduplication state.

Duplicate delivery must not cause duplicate logical transitions.

---

# 100. Outbox Integration

When application state and event publication must be coordinated:

```text
local transaction
    ├── state update
    └── outbox record
```

628 outbox facilities can publish the event after commit.

629 must not invent distributed two-phase commit.

---

# 101. Inbox Integration

Incoming events can use:

```text
Inbox
+
IdempotencyKey
+
WorkflowSignal
```

to prevent duplicate processing.

---

# 102. Distributed Workflow Transaction Boundary

A workflow is **not** an ACID transaction.

The system explicitly distinguishes:

```text
ACID local transaction
Saga
workflow
distributed transaction
```

Distributed transactions are outside the mandatory core.

---

# 103. Optional TCC Boundary

Higher-level modules may implement:

```text
Try
Confirm
Cancel
```

using workflow activities.

629 provides orchestration but does not require TCC.

---

# 104. Optional Human Escalation

A failed compensation may produce:

```text
HumanTask
```

Example:

```text
CompensationFailed
    ↓
CreateHumanTask
    ↓
AwaitDecision
```

This is optional.

---

# 105. Observability

Every workflow operation carries:

```text
WorkflowId
InstanceId
RunId
StepId
TaskId
WorkerId
TraceId
SpanId
TenantId?
```

Metrics:

```text
workflow_started
workflow_completed
workflow_failed
workflow_duration
queue_depth
queue_latency
task_attempts
task_failures
retry_count
compensation_count
compensation_failures
timer_lag
worker_utilization
workflow_replay_time
```

---

# 106. Diagnostics

602 integration provides:

```text
structured events
tracing
logs
crash diagnostics
```

Workflow diagnostics must distinguish:

```text
workflow failure
activity failure
worker failure
scheduler failure
storage failure
coordination failure
```

---

# 107. Workflow Inspection

The runtime can expose:

```text
current state
current step
pending activities
pending timers
pending signals
worker assignment
retry count
history position
version
resource usage
```

Sensitive payloads are redacted.

---

# 108. Resource Limits

Limits include:

```text
max workflow state
max history size
max events
max parallel branches
max pending activities
max timers
max signals
max retries
max task queue depth
max workflow duration
```

All limits are configurable.

---

# 109. Tenant Isolation

Optional tenant scopes:

```text
Tenant
    ├── workflows
    ├── queues
    ├── schedules
    └── workers
```

Resource budgets and capabilities can be tenant-scoped.

---

# 110. Rate Limiting

Rate limits can apply to:

```text
workflow starts
activity calls
queue enqueue
signals
schedule triggers
worker execution
tenant
endpoint
```

---

# 111. Admission Control

Before starting work:

```text
security check
resource check
queue capacity check
worker availability
policy check
```

If rejected:

```text
Rejected
Deferred
Queued
```

must be explicit.

---

# 112. Fairness

The scheduler supports fairness dimensions:

```text
tenant
workflow
queue
priority
worker
resource group
```

A large workflow must not automatically monopolize the entire worker fleet.

---

# 113. Starvation Prevention

The scheduler may use:

```text
aging
weighted fair scheduling
quota rotation
deadline priority
```

Policies must be deterministic enough for diagnostics.

---

# 114. Long-Running Workflow

A workflow may logically execute for:

```text
seconds
minutes
days
months
years
```

No OS process lifetime is implied.

Durability is provided by:

```text
state
history
snapshot
timer
coordination
```

---

# 115. Workflow Garbage Collection

This is **not language garbage collection**.

Workflow data reclamation means:

```text
history retention
snapshot retention
completed workflow cleanup
dead-letter cleanup
timer cleanup
```

It must use explicit retention policies.

---

# 116. Retention Policies

Examples:

```text
KeepForever
KeepFor(Duration)
KeepLast(N)
DeleteAfterExport
ArchiveThenDelete
```

---

# 117. Archival

Completed workflow histories can be exported to:

```text
611
613
628
```

using content-addressed immutable storage.

Archive references contain:

```text
ContentHash
SchemaFingerprint
WorkflowVersion
```

---

# 118. Deterministic Testing

629 provides:

```text
FakeClock
FakeWorker
FakeQueue
FakeCoordinator
FakeStore
DeterministicScheduler
FaultInjector
ReplayRunner
```

Tests must be able to simulate failures deterministically.

---

# 119. Failure Injection

Injectable failures:

```text
worker crash
network timeout
network partition
duplicate delivery
lost acknowledgement
lease expiration
storage failure
coordinator failure
timer delay
clock jump
partial response
duplicate signal
```

---

# 120. Replay Testing

A recorded history can be replayed against a new workflow binary.

The system detects:

```text
decision mismatch
state schema mismatch
event mismatch
activity command mismatch
```

---

# 121. Workflow Compatibility Test

Before deployment:

```text
old history
+
new workflow version
```

can be replayed.

Any nondeterministic divergence is reported.

---

# 122. Security Testing

Required tests include:

```text
capability escalation
stale worker fencing
unauthorized signal
unauthorized workflow control
secret leakage
history tampering
replay attack
duplicate task
tenant isolation
queue poisoning
```

---

# 123. Queue Security

A task queue must enforce:

```text
enqueue capability
consume capability
inspect capability
admin capability
dead-letter capability
replay capability
```

These are distinct permissions.

---

# 124. Workflow Control Security

Separate permissions:

```text
Start
Inspect
Signal
Pause
Resume
Cancel
Terminate
Migrate
Replay
Repair
Delete
```

No generic "workflow admin" permission is required internally.

---

# 125. Audit

Security-sensitive operations produce audit events:

```text
workflow_started
workflow_cancelled
workflow_terminated
workflow_migrated
task_replayed
dead_letter_replayed
capability_denied
manual_compensation
```

---

# 126. Package Integration

Workflow definitions can be packaged through 613/625.

Package may contain:

```text
workflow metadata
activity binaries
schemas
configuration
capability declarations
version metadata
```

Executable code remains subject to 623 trust rules.

---

# 127. Plugin Integration

623 plugins may register:

```text
ActivityProvider
WorkflowProvider
QueueProvider
ScheduleProvider
HumanTaskProvider
```

Provider capabilities must be explicitly declared.

---

# 128. Script Integration

624 scripts may create:

```text
workflow
job
schedule
signal
```

but scripts remain subject to:

```text
capability
resource
timeout
sandbox
```

policies.

---

# 129. GUI Integration

619/622 may provide:

```text
Workflow Monitor
Task Monitor
Worker Monitor
Schedule Editor
History Viewer
Saga Inspector
Human Task UI
```

629 remains usable without GUI.

---

# 130. CLI Integration

Native tooling may expose:

```text
axiom workflow list
axiom workflow inspect
axiom workflow start
axiom workflow signal
axiom workflow cancel

axiom task list
axiom task retry
axiom task replay

axiom worker list

axiom schedule list
axiom schedule trigger
```

---

# 131. AI-Readable Metadata

Workflow metadata must be machine-readable.

Example:

```text
.axworkflow
```

contains:

```text
workflow identity
version
state schema
steps
activities
signals
timers
retry policies
timeouts
capabilities
resource requirements
compensation graph
dependencies
```

This allows Axiom tooling and AI agents to inspect workflow behavior without parsing implementation source.

---

# 132. Static Workflow Graph

Compiler emits an optional graph:

```text
Start
  ↓
Reserve
  ↓
Parallel
 ┌───────┴────────┐
Payment       Address
 └───────┬────────┘
         ↓
       Ship
         ↓
       Done
```

The graph is diagnostic metadata, not necessarily the runtime representation.

---

# 133. Runtime Optimization

The compiler/runtime may optimize:

```text
state transitions
small workflow states
timer registration
queue operations
event encoding
snapshot creation
replay
```

Simple local workflows should have near-native overhead.

---

# 134. Allocation Rules

The core workflow engine should avoid:

```text
per-event heap allocation
per-task reflection
global locks
mandatory garbage collection
```

Use:

```text
arenas
object pools
slab allocation
inline small objects
ring buffers
persistent storage batches
```

where beneficial.

---

# 135. Hot Path

Hot paths include:

```text
task enqueue
task lease
task completion
workflow event append
timer lookup
signal delivery
worker heartbeat
```

These should avoid global mutexes.

---

# 136. Batching

Supported batching:

```text
event append
task enqueue
ack
heartbeat
snapshot write
replication
```

Batching must not violate ordering or durability semantics.

---

# 137. Backpressure Propagation

Backpressure should propagate:

```text
worker
 ↓
task queue
 ↓
workflow
 ↓
event source
```

rather than allowing unlimited buffering.

---

# 138. Offline Workers

Workers may temporarily operate with constrained connectivity only when the task semantics permit it.

A disconnected worker must not continue indefinitely using an expired lease.

---

# 139. Mobile

On mobile:

```text
long-running OS process
```

cannot be assumed.

629 maps durable work onto platform-supported background execution mechanisms.

If execution is interrupted:

```text
persisted workflow
    ↓
later resume
```

---

# 140. WASM

WASM mode delegates:

```text
persistent storage
timers
network
worker execution
```

to the host capability layer.

No direct OS assumptions.

---

# 141. Embedded

Embedded mode may reduce the system to:

```text
TaskQueue
Scheduler
Timer
Persistence
WorkflowState
```

with distributed functionality removed.

---

# 142. Minimal Runtime Profiles

Profiles:

```text
AXWORKFLOW_NONE
AXWORKFLOW_LOCAL
AXWORKFLOW_DURABLE
AXWORKFLOW_SCHEDULE
AXWORKFLOW_QUEUE
AXWORKFLOW_DISTRIBUTED
AXWORKFLOW_SAGA
AXWORKFLOW_HUMAN
AXWORKFLOW_FULL
```

Unused components must be dead-strippable.

---

# 143. ABI

Public workflow ABI uses:

```text
stable scalar types
stable handles
versioned structs
function tables
schema IDs
```

Compiler-private runtime structures must not cross plugin boundaries.

---

# 144. FFI

Foreign activity providers can implement:

```text
ActivityProvider ABI
```

but FFI remains outside deterministic workflow code.

---

# 145. Crash Recovery Invariant

After process/node failure:

```text
durable workflow state
+
durable history
+
valid coordination ownership
```

must be sufficient to reconstruct the workflow.

---

# 146. No Duplicate Ownership Invariant

At any logical instant after successful fencing:

```text
only current owner may commit
```

workflow/task state transitions.

---

# 147. No Hidden Side Effect Invariant

Deterministic workflow execution must not silently perform external side effects.

---

# 148. Replay Invariant

Replay of identical history must produce identical workflow decisions.

---

# 149. Idempotency Invariant

Any operation exposed as retryable must explicitly define its idempotency semantics.

---

# 150. Cancellation Invariant

Cancellation must never be represented as automatic rollback of external effects.

---

# 151. Compensation Invariant

Compensation is an independent business operation and may fail.

---

# 152. Timer Invariant

Durable timers survive runtime process failure.

---

# 153. State Invariant

Workflow state must have a schema fingerprint.

---

# 154. Security Invariant

Workflow execution cannot acquire additional capabilities merely by scheduling an activity.

---

# 155. Resource Invariant

A workflow cannot bypass Resource Governor limits through retries or parallel branches.

---

# 156. Queue Invariant

An expired lease cannot authorize a stale worker to commit new state.

---

# 157. Version Invariant

Changing workflow source code cannot implicitly alter already-running workflow instances.

---

# 158. Storage Invariant

Workflow history must be durable before the runtime acknowledges a durable transition.

---

# 159. Ordering Invariant

Ordering guarantees are scoped and explicit.

The system never implies global ordering where none exists.

---

# 160. Failure Invariant

No failure path may silently convert:

```text
Failed
```

into:

```text
Completed
```

---

# 161. Resource Isolation Invariant

One tenant/workflow cannot consume unlimited queue, CPU, memory, network, or worker resources.

---

# 162. Deterministic Clock Invariant

Workflow time is obtained only through the workflow runtime.

---

# 163. Randomness Invariant

Workflow randomness must be deterministic or recorded.

---

# 164. Signal Invariant

Signals are durable before they are acknowledged.

---

# 165. Migration Invariant

Workflow migration must explicitly identify source and destination schema/version.

---

# 166. Security Boundary

```text
Workflow
   │
   ├── deterministic logic
   │
   └── Activity
          │
          └── Capability boundary
                │
                ├── Network
                ├── Storage
                ├── Device
                ├── Process
                └── External Service
```

This prevents workflow code from becoming an implicit privileged execution context.

---

# 167. Final Architecture

```text
                         AXIOM APPLICATION
                                │
                                ▼
                  ┌──────────────────────────┐
                  │          629             │
                  │ DISTRIBUTED WORKFLOW     │
                  │        RUNTIME           │
                  ├──────────────────────────┤
                  │ Workflow Engine           │
                  │ Job Engine                │
                  │ Scheduler                 │
                  │ Task Queues               │
                  │ Worker Runtime             │
                  │ Durable Timers             │
                  │ Signals                    │
                  │ Retry/Timeout              │
                  │ Saga/Compensation          │
                  │ Human Tasks                │
                  │ Replay/Recovery            │
                  │ Version/Migration          │
                  └─────────────┬────────────┘
                                │
          ┌─────────────────────┼──────────────────────┐
          │                     │                      │
          ▼                     ▼                      ▼
        627                   628                    626
   Coordination          Distributed Data       Network Services
          │                     │                      │
          ▼                     ▼                      ▼
        605                   612                    609
   Supervision          Serialization             Sockets
          │                     │
          ▼                     ▼
        607                   611
   Scheduler/Async         Storage
          │
          ▼
        606
   Resource Governor

Security:
603 + 610

Diagnostics:
602

Configuration:
601

State:
600
```

---

# 168. Canonical Data Flow

```text
Schedule/Event/Manual Start
             │
             ▼
      Workflow Instance
             │
             ▼
      Deterministic Engine
             │
       ┌─────┴─────┐
       │           │
       ▼           ▼
    Decision     Activity
       │           │
       │           ▼
       │      Task Queue
       │           │
       │           ▼
       │         Worker
       │           │
       │           ▼
       └────── Result
             │
             ▼
       Durable History
             │
             ▼
       Snapshot/Replay
```

---

# 169. Acceptance Criteria

The implementation is considered complete only when all of the following classes are validated.

## Workflow

- workflow creation;
- workflow versioning;
- deterministic execution;
- branching;
- loops;
- parallel branches;
- joins;
- sub-workflows;
- cancellation;
- termination;
- suspension;
- resumption.

## Durability

- durable history;
- snapshots;
- replay;
- process restart;
- machine restart;
- coordinator failover;
- state migration.

## Activities

- scheduling;
- execution;
- timeout;
- heartbeat;
- cancellation;
- retry;
- idempotency;
- fencing.

## Scheduling

- immediate jobs;
- delayed jobs;
- recurring jobs;
- calendar schedules;
- timezone handling;
- DST handling;
- missed schedule policies;
- duplicate occurrence prevention.

## Distributed Execution

- worker registration;
- worker lease;
- worker failure;
- worker replacement;
- queue partitioning;
- scheduler ownership;
- fencing;
- network partition;
- coordinator failover.

## Queue

- durable enqueue;
- lease;
- ack;
- nack;
- delayed task;
- dead-letter;
- replay;
- ordering;
- backpressure.

## Saga

- compensation;
- reverse compensation;
- nested saga;
- compensation retry;
- manual intervention.

## Security

- capability enforcement;
- tenant isolation;
- secret protection;
- unauthorized signal rejection;
- unauthorized workflow control;
- stale-worker rejection.

## Resource Governance

- CPU limits;
- memory limits;
- queue limits;
- task limits;
- retry budgets;
- worker concurrency;
- tenant quotas.

## Diagnostics

- workflow tracing;
- task tracing;
- worker metrics;
- queue metrics;
- retry metrics;
- compensation metrics;
- replay diagnostics;
- audit events.

## Compiler

- `@workflow`;
- `@activity`;
- `@task`;
- `@schedule`;
- `@signal`;
- `@compensate`;
- deterministic API validation;
- generated metadata;
- workflow graph;
- schema fingerprints.

## Testing

- deterministic replay;
- fault injection;
- duplicate delivery;
- lease expiration;
- coordinator failure;
- worker crash;
- timer recovery;
- network partition;
- storage failure;
- version migration;
- compensation failure;
- security fuzzing;
- queue stress;
- scheduler stress.

**Target: ≥180 acceptance criteria across implementation, integration, reliability, security, performance and tooling.**

---

# 170. Performance Targets

For local execution:

```text
minimal workflow:
    near-native state-machine overhead

simple task enqueue:
    O(1) amortized

task lease:
    O(1) amortized

event append:
    O(1) amortized

timer insertion:
    O(log n) or better

workflow replay:
    O(history length)
```

The implementation should avoid:

```text
mandatory GC
reflection
global locks
per-step heavyweight objects
```

---

# 171. Core Design Decisions

The following decisions are frozen for Axiom 629:

1. **Workflow execution is deterministic.**
2. **External side effects are activities.**
3. **At-least-once execution is the default.**
4. **Exactly-once global execution is not promised.**
5. **Idempotency and fencing provide safe effects.**
6. **Durable timers do not require persistent processes.**
7. **Workflow history is durable.**
8. **Snapshots bound replay cost.**
9. **Workflow versioning is explicit.**
10. **Compensation is not rollback.**
11. **Distributed workflows are not distributed ACID transactions.**
12. **627 owns distributed coordination.**
13. **628 owns distributed durable data.**
14. **626 owns network services.**
15. **607 owns local execution scheduling.**
16. **606 owns resource governance.**
17. **603 owns capability security.**
18. **602 owns diagnostics.**
19. **No cloud vendor is required.**
20. **No third-party workflow engine is required.**

---

# 172. Task Completion

**BOOTSTRAP-629 — COMPLETE**

Axiom now has a coherent native execution stack from:

```text
machine
 ↓
process
 ↓
thread/task
 ↓
synchronization
 ↓
network
 ↓
distributed coordination
 ↓
distributed data
 ↓
durable workflow
 ↓
long-running business process
```

The next architectural layer should therefore address the **distributed compute/worker execution model itself**, rather than duplicating workflow functionality.

**NEXT TASK: BOOTSTRAP-630 — Native Distributed Compute, Worker Pool, Remote Execution, Placement, Load Balancing, Resource-Aware Dispatch & Cluster Execution Runtime 5.0**
:::

BOOTSTRAP-629 đã hoàn tất và chuỗi được nối tự động sang **BOOTSTRAP-630**.