# BOOTSTRAP-541 — AI WORKFLOW COMPILER, DAG OPTIMIZATION, DURABLE STATE MACHINE LOWERING, EVENT SOURCING, CHECKPOINT OPTIMIZATION, PARALLEL EXECUTION & NATIVE WORKFLOW RUNTIME

**Trạng thái: COMPLETED / LOCKED**

`BOOTSTRAP-540` đã định nghĩa Workflow DSL/semantic model. `541` biến model đó thành **compiler + execution runtime thực sự**, với mục tiêu workflow có thể được tối ưu gần giống một chương trình Axiom thông thường nhưng vẫn giữ được durability, replay, failure recovery và side-effect semantics.

---

## 541.1 — Kiến trúc tổng thể

```text
                 Workflow Source
                       │
                       ▼
                Workflow AST
                       │
                       ▼
             Semantic Workflow Graph
                       │
          ┌────────────┼─────────────┐
          ▼            ▼             ▼
       Types         Effects       Policies
          │            │             │
          └────────────┼─────────────┘
                       ▼
                  Workflow IR
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   CFG / DAG       State Model     Effect Graph
        │              │              │
        └──────────────┼──────────────┘
                       ▼
                Optimization
                       │
                       ▼
              Execution Plan
                       │
                       ▼
            Durable Workflow Runtime
                       │
       ┌───────────────┼────────────────┐
       ▼               ▼                ▼
   Scheduler       State Store       Event Log
       │               │                │
       └───────────────┼────────────────┘
                       ▼
                 Native Runtime
```

---

# 541.2 — Workflow Compiler ≠ Workflow Runtime

Compiler chịu trách nhiệm:

- semantic validation;
- graph construction;
- lowering;
- optimization;
- static resource analysis;
- execution-plan generation.

Runtime chịu trách nhiệm:

- scheduling;
- state persistence;
- execution;
- recovery;
- cancellation;
- events;
- checkpoints.

Không được trộn hai tầng.

---

# 541.3 — Workflow IR

Workflow IR là representation trung gian giữa semantic graph và runtime plan.

```text
WorkflowIR {
    workflow_id
    version
    inputs
    outputs
    state_schema
    blocks
    nodes
    edges
    effects
    policies
    resources
}
```

---

# 541.4 — Node IR

```text
NodeIR {
    node_id
    opcode
    inputs
    outputs
    state
    effects
    capabilities
    retry_policy
    timeout
    resource_budget
}
```

---

# 541.5 — Edge IR

```text
EdgeIR {
    edge_id
    source
    target
    condition?
    data_dependencies
    control_dependencies
}
```

---

# 541.6 — State IR

Workflow state phải được compiler phân biệt:

```text
LocalState
PersistentState
CheckpointState
ExternalState
DerivedState
```

Không được coi tất cả state là durable.

---

# 541.7 — CFG + DAG

Workflow có hai loại cấu trúc đồng thời:

```text
Control Flow Graph
+
Data Dependency Graph
```

Điều này cho phép compiler biết:

- node nào phải chạy trước;
- node nào có thể chạy song song;
- node nào chỉ là data transformation;
- node nào tạo side effect.

---

# 541.8 — Effect Graph

Compiler xây dựng:

```text
EffectGraph {
    Read
    Write
    Network
    Process
    External
    Irreversible
}
```

Effect graph là barrier đối với optimization.

---

# 541.9 — Pure Node Optimization

Nếu:

```text
A → pure transform → B
```

compiler có thể:

- inline;
- constant-fold;
- fuse;
- eliminate;
- reorder.

---

# 541.10 — Side-effect Barrier

Nếu:

```text
A → external_write → B
```

compiler không được tự ý reorder node xung quanh `external_write`.

---

# 541.11 — Dead Node Elimination

Node không ảnh hưởng tới:

- output;
- persistent state;
- external effect;
- observable event;

có thể bị loại bỏ.

---

# 541.12 — Dead State Elimination

State chỉ được dùng nội bộ và không còn reachable có thể loại bỏ khỏi execution plan.

---

# 541.13 — Constant Folding

Các node thuần và constant được tính trước compile-time nếu semantics cho phép.

---

# 541.14 — Comptime Integration

Workflow compiler có thể dùng 431 để:

- generate schemas;
- generate adapters;
- specialize workflow;
- validate static configuration.

Không được biến runtime external state thành comptime input.

---

# 541.15 — Common Subexpression Elimination

Hai pure nodes:

```text
f(x)
f(x)
```

có thể dùng chung kết quả nếu:

- cùng semantic identity;
- không có hidden effect;
- input tương đương.

---

# 541.16 — Memoization

Pure node có thể cache:

```text
CacheKey =
    NodeSemanticHash
    + InputHash
    + DependencyHash
```

Cache không được làm thay đổi semantics.

---

# 541.17 — Parallelization

Nếu:

```text
A ─┐
   ├─→ D
B ─┤
   │
C ─┘
```

và A/B/C không có xung đột, runtime có thể chạy song song.

---

# 541.18 — Dependency Analysis

Compiler kiểm tra:

```text
Read-after-write
Write-after-read
Write-after-write
Control dependency
Effect dependency
```

---

# 541.19 — Parallel Safety

Hai node chỉ được chạy đồng thời nếu:

```text
Data dependency compatible
+
Effect dependency compatible
+
Capability compatible
+
Resource budget compatible
```

---

# 541.20 — Join Lowering

```text
Parallel
   ↓
Fork
   ↓
Branches
   ↓
Join
```

được hạ thành runtime synchronization primitive.

---

# 541.21 — Join Policies

Runtime hỗ trợ:

```text
All
Any
FirstSuccess
Quorum
Nofail
Custom
```

---

# 541.22 — Failure-Aware Join

Nếu một branch fail, Join phải biết policy:

```text
FailFast
WaitAll
IgnoreFailed
RetryFailed
Compensate
PartialResult
```

---

# 541.23 — Loop Lowering

Workflow loop được lowering thành state machine:

```text
LoopHeader
   ↓
Condition
 ┌─┴─┐
true false
 │    │
Body  Exit
 │
 └──→ LoopHeader
```

---

# 541.24 — Bounded Loop

Nếu compiler chứng minh được bound:

```text
max_iterations = N
```

runtime có thể cấp phát metadata cố định.

---

# 541.25 — Unbounded Loop

Unbounded workflow phải có ít nhất một:

- cancellation;
- deadline;
- resource budget;
- external stop condition.

---

# 541.26 — Agent Loop Lowering

Agent node vẫn giữ autonomous loop ở runtime 511/535 nhưng workflow compiler quản lý outer boundary:

```text
Workflow
   ↓
Agent Node
   ↓
Agent Runtime
   ↓
Model / Tool / Memory
```

---

# 541.27 — Await Lowering

Mọi node chờ:

- network;
- tool;
- model;
- human;
- timer;
- event;

được lowering thành continuation/state transition thay vì giữ OS thread.

---

# 541.28 — Continuation

```text
Continuation {
    workflow_id
    state_version
    resume_node
    serialized_state
}
```

---

# 541.29 — Native Stack

Runtime không giữ stack native qua arbitrary long waits.

Điều này tránh:

- thread exhaustion;
- stack retention;
- unnecessary memory.

---

# 541.30 — Durable State Machine

Workflow runtime về bản chất là:

```text
State
+
Event
→
Deterministic Transition
→
New State
```

---

# 541.31 — Event Sourcing

Có thể lưu:

```text
EventLog
```

thay vì snapshot mọi state transition.

---

# 541.32 — Event Record

```text
WorkflowEvent {
    run_id
    sequence
    timestamp
    node_id
    event_type
    payload
    schema_version
    checksum
}
```

---

# 541.33 — Event Ordering

Mỗi workflow run có logical sequence.

Wall-clock timestamp không thay thế sequence ordering.

---

# 541.34 — Event Identity

External events cần:

```text
EventId
SourceId
SourceSequence?
```

để chống duplicate khi cần.

---

# 541.35 — Event Deduplication

Runtime có thể giữ processed-event identity.

---

# 541.36 — Snapshotting

Không cần replay toàn bộ event log nếu có snapshot.

```text
Event 1
Event 2
...
Snapshot N
Event N+1
...
```

---

# 541.37 — Snapshot Format

```text
WorkflowSnapshot {
    workflow_id
    workflow_version
    run_id
    state_schema_version
    state
    event_sequence
    checksum
}
```

---

# 541.38 — Snapshot Consistency

Snapshot phải tương ứng với một logical event position.

---

# 541.39 — Incremental Checkpoint

Compiler/runtime có thể checkpoint sau:

- side effect;
- await;
- human approval;
- expensive computation;
- configured interval.

---

# 541.40 — Checkpoint Optimization

Không cần checkpoint mọi pure node.

Compiler có thể tìm:

```text
Recovery Cost
vs
Checkpoint Cost
```

nhưng đây là optimization policy, không phải semantic assumption.

---

# 541.41 — Recovery Frontier

Runtime xác định node gần nhất có state durable:

```text
Last Durable State
       ↓
Recovery Frontier
       ↓
Replay / Resume
```

---

# 541.42 — Exactly-Once State Transition

Local state transition có thể được commit atomically nếu storage hỗ trợ.

Điều này **không** có nghĩa external side effect là exactly-once.

---

# 541.43 — External Effect

Ví dụ:

```text
send_email()
charge_payment()
create_file()
```

phải có idempotency/operation identity nếu retry có thể xảy ra.

---

# 541.44 — Effect Token

Runtime có thể gắn:

```text
OperationId
```

cho external operation.

---

# 541.45 — Idempotency Store

Có thể lưu:

```text
OperationId → Result
```

để tránh thực hiện lại operation đã được xác nhận.

---

# 541.46 — Unknown External State

Nếu process chết sau khi gửi request nhưng trước khi nhận response:

```text
Unknown
```

Không được tự động kết luận:

```text Success
```

hoặc:

```text Failure
```

---

# 541.47 — Recovery Policy

Unknown external operation có thể:

```text
QueryStatus
Retry
Compensate
AskHuman
Abort
```

---

# 541.48 — Human Recovery

Workflow có thể pause và yêu cầu con người quyết định cách xử lý unknown state.

---

# 541.49 — Durable Timer

Timer lâu dài phải lưu:

```text
deadline
timer_id
workflow_run
```

không dựa vào process memory.

---

# 541.50 — Timer Recovery

Sau restart:

```text persisted deadline
        ↓
current monotonic/wall clock policy
        ↓
resume/expire
```

---

# 541.51 — Event-Driven Resume

Workflow đang `WaitingEvent` không tiêu tốn worker thread.

---

# 541.52 — Queue Integration

Workflow event có thể đến từ:

- Channel;
- Actor;
- Message queue;
- IPC;
- Network;
- Database event.

---

# 541.53 — Backpressure

Nếu workflow intake nhanh hơn processing:

```text
Admission
 ↓
Queue
 ↓
Scheduler
```

với policy rõ ràng.

---

# 541.54 — Queue Policies

```text
Block
Reject
Drop
Coalesce
Priority
DeadLetter
```

---

# 541.55 — Priority

Priority chỉ là scheduler policy; không được làm thay đổi workflow semantics.

---

# 541.56 — Resource-Aware Scheduling

Scheduler xét:

```text
CPU
Memory
GPU
Network
Tool quota
Model quota
Concurrency
Deadline
```

---

# 541.57 — Model Batch Optimization

Các Model nodes tương thích có thể được gom batch.

Điều kiện:

```text
same model contract
compatible preprocessing
compatible device
compatible numerical policy
deadline compatible
```

---

# 541.58 — Tool Batch Optimization

Chỉ batch nếu tool contract khai báo semantics tương ứng.

---

# 541.59 — Request Coalescing

Pure/idempotent requests có thể coalesce.

External side effects mặc định không được coalesce.

---

# 541.60 — Workflow Fusion

Hai pure workflows có thể fuse nếu:

- type-compatible;
- effect-compatible;
- policy-compatible.

---

# 541.61 — Workflow Inlining

Subworkflow có thể inline vào parent execution plan.

Nhưng:

```text
durability boundary
security boundary
capability boundary
```

phải được preserve.

---

# 541.62 — Capability Boundary

Compiler không được inline theo cách làm child workflow nhận thêm authority.

---

# 541.63 — Budget Boundary

Child budget không được biến thành parent unlimited budget.

---

# 541.64 — Security Boundary

Out-of-process workflow/tool boundary không được biến mất chỉ vì compiler optimization.

---

# 541.65 — Policy Barrier

Policy-sensitive node là optimization barrier.

---

# 541.66 — Human Approval Barrier

Approval không được optimize away vì compiler thấy điều kiện có vẻ luôn true.

---

# 541.67 — Model Output

Model output được coi là untrusted runtime data.

---

# 541.68 — Tool Output

Tool output cũng là untrusted data.

---

# 541.69 — Prompt Injection Boundary

Compiler/runtime phải giữ:

```text
Policy
≠
Model Output
≠
Tool Output
≠
External Data
```

---

# 541.70 — Workflow Static Security Analysis

Compiler có thể phát hiện:

```text
workflow
 ↓
tool
 ↓
network
 ↓
external write
```

và báo capability chain.

---

# 541.71 — Workflow Effect Inference

Nếu node gọi function có effect:

```text
network
```

thì workflow không thể tự khai báo `pure`.

---

# 541.72 — Effect Propagation

```text
A calls B
B has Write
→ A has Write
```

trừ khi có explicit encapsulation/verified abstraction.

---

# 541.73 — Resource Effect

Compiler có thể propagate:

```text
alloc
block
io
gpu
network
```

metadata từ 433/475/478.

---

# 541.74 — Retry Analysis

Compiler cảnh báo:

```text
non-idempotent effect
+
retry enabled
```

---

# 541.75 — Missing Timeout

External blocking operation không có timeout có thể bị lint/warn hoặc deny theo policy.

---

# 541.76 — Missing Compensation

Critical write có thể yêu cầu compensation theo workflow policy.

---

# 541.77 — State Compaction

Runtime có thể compact event history thành snapshot.

---

# 541.78 — Event Log Retention

Retention policy explicit.

```text
Forever
N days
N events
Until checkpoint
```

---

# 541.79 — Audit Log

Audit history không được tự động xóa chỉ vì execution log compact.

---

# 541.80 — Event Schema Evolution

Event schema integrates 539.

Old events phải vẫn đọc được hoặc có migration.

---

# 541.81 — Workflow Version Pinning

Run sử dụng:

```text WorkflowId + Version
```

không phải latest mặc định.

---

# 541.82 — Execution Plan Identity

```text
ExecutionPlanId =
hash(
    WorkflowSemanticHash
    CompilerVersion
    RuntimeContract
    Target
    OptimizationPolicy
)
```

---

# 541.83 — Plan Cache

Execution plan có thể cache theo identity.

Cache không được thay đổi semantics.

---

# 541.84 — Native Runtime

Runtime được implement bằng Axiom native code và không yêu cầu VM managed.

---

# 541.85 — Runtime Representation

Workflow state có thể dùng:

- stack/local memory cho transient state;
- heap/arena cho runtime state;
- persistent storage cho durable state.

---

# 541.86 — Serialization

Chỉ state crossing durability/process/machine boundary mới bắt buộc serialization.

Pure local transitions không cần serialize.

---

# 541.87 — Zero-Copy

Large payload có thể dùng:

```textObjectRef
SharedBuffer
MemoryMap
```

khi ownership/lifetime đảm bảo.

---

# 541.88 — Large State

Không serialize toàn bộ large tensor/media/file vào event log nếu chỉ cần reference.

---

# 541.89 — Artifact Reference

```text
ArtifactRef {
    id
    hash
    type
    size
    storage
}
```

---

# 541.90 — AI/ML Integration

Workflow compiler có thể optimize:

```text
Model
→ preprocess
→ inference
→ postprocess
```

thành execution group nếu contracts cho phép.

---

# 541.91 — GPU Scheduling

GPU node phải khai báo:

```text device
memory
stream
synchronization
```

---

# 541.92 — CPU/GPU Overlap

Compiler/runtime có thể overlap:

```text
CPU preprocessing
GPU inference
CPU postprocessing
```

nếu dependency graph cho phép.

---

# 541.93 — Async Transfer

Host↔device transfer là graph edge có cost/effect.

---

# 541.94 — Memory Planning

504/505 memory planner có thể reuse buffers giữa workflow AI nodes.

---

# 541.95 — Tensor Lifetime

Tensor buffer chỉ được reuse khi dependency graph chứng minh lifetime kết thúc.

---

# 541.96 — Workflow Profiling

Runtime emits:

```text
queue_time
execution_time
wait_time
checkpoint_time
serialization_time
model_time
tool_time
human_wait_time
```

---

# 541.97 — Critical Path

Compiler có thể tính DAG critical path.

Không được biến critical path thành universal quality score.

---

# 541.98 — Replay Mode

```text
Normal
Record
Replay
Simulation
```

---

# 541.99 — Simulation Mode

Simulation không được thực hiện irreversible external effects.

---

# 541.100 — Fault Injection

Có thể inject:

- node failure;
- timeout;
- network failure;
- tool failure;
- model failure;
- process crash;
- storage failure;
- event duplication;
- event reorder.

---

# 541.101 — Crash Recovery Test

Test có thể crash runtime tại mọi checkpoint boundary.

---

# 541.102 — Deterministic Scheduler

Test runtime hỗ trợ scheduler deterministic.

---

# 541.103 — Virtual Clock

Timer/retry/deadline tests dùng 474 VirtualClock.

---

# 541.104 — Workflow Fuzzing

Fuzz:

- graph;
- state;
- event;
- schema;
- retry;
- cancellation;
- migration.

---

# 541.105 — Graph Validation

Compiler phải reject:

- invalid edge;
- missing target;
- unreachable required output;
- incompatible types;
- cyclic dependency nơi cycle không được phép.

---

# 541.106 — Legal Cycles

Loop/feedback node là cycle hợp lệ.

Cycle implicit do graph construction là error.

---

# 541.107 — Type Checking

Workflow edges phải type-compatible.

---

# 541.108 — State Schema Checking

State transition phải preserve schema invariant.

---

# 541.109 — Migration Checking

Workflow version migration phải được validate bằng 539.

---

# 541.110 — Durable Boundary

Compiler phải đánh dấu:

```text
Durable
NonDurable
```

cho state/node boundaries.

---

# 541.111 — Failure Atomicity

Runtime phải xác định rõ mỗi transition thuộc:

```text
NotStarted
Running
Committed
Failed
Unknown
```

---

# 541.112 — Side Effect Commit

External effect chỉ được xem là committed khi provider xác nhận theo contract.

---

# 541.113 — Retry After Crash

Retry policy phải biết trạng thái side effect:

```textUnknown → query/recover
```

không blind retry mặc định.

---

# 541.114 — Compensation Execution

Compensation là workflow action độc lập, có:

- capability;
- retry;
- timeout;
- audit.

---

# 541.115 — Compensation Failure

Compensation failure tạo trạng thái riêng, không giả vờ workflow đã rollback.

---

# 541.116 — Pause

Workflow có thể pause mà không mất durable state.

---

# 541.117 — Resume

Resume phải dùng exact version/compatible migration.

---

# 541.118 — Cancellation During Side Effect

Cancellation không được giả định external operation đã bị hủy nếu provider chưa xác nhận.

---

# 541.119 — Graceful Shutdown

Runtime:

```text
stop intake
→ finish/abort according to policy
→ checkpoint
→ persist
→ shutdown
```

---

# 541.120 — Forced Shutdown

Forced termination có thể để state ở `Unknown`; recovery xử lý sau.

---

# 541.121 — Multi-Process Runtime

Workflow workers có thể phân tán qua processes.

---

# 541.122 — Distributed State

Distributed durable state có thể dùng 502.

---

# 541.123 — Leader

Workflow scheduler leader không được tự động có application authority.

---

# 541.124 — Scheduler Failure

Một scheduler failure không được làm mất durable workflow state.

---

# 541.125 — Duplicate Worker

Multiple workers phải có claim/lease/fencing semantics.

---

# 541.126 — Work Claim

```text
RunId
NodeId
Attempt
Lease
Epoch
```

---

# 541.127 — Stale Worker

Worker với stale epoch không được commit state.

---

# 541.128 — Fencing

Fencing token được dùng khi backend cần bảo vệ against stale worker.

---

# 541.129 — Workflow Sharding

Workflow runs có thể partition theo:

- tenant;
- workflow;
- run;
- key.

---

# 541.130 — Ordering Key

Một workflow family có thể yêu cầu serialized execution theo key.

---

# 541.131 — Concurrency Policy

```text
AllowMany
Single
PerKey
Bounded
```

---

# 541.132 — Admission

534/536 admission control được áp dụng trước scheduling.

---

# 541.133 — Tenant Isolation

Workflow state/cache/log/tool/model access phải obey tenant boundary.

---

# 541.134 — Secret State

Secrets không được xuất hiện plaintext trong event log/debug trace mặc định.

---

# 541.135 — Redaction

Sensitive fields có schema metadata.

---

# 541.136 — Access-Controlled Replay

Replay phải obey current authorization và historical data policy.

---

# 541.137 — Historical Policy

Historical events vẫn chịu data retention/privacy policy.

---

# 541.138 — Workflow Compiler API

```text
compile_workflow(source)
check_workflow(source)
explain_plan(workflow)
optimize_workflow(workflow)
build_plan(workflow)
validate_replay(run)
```

---

# 541.139 — Runtime API

```text
start(run)
pause(run)
resume(run)
cancel(run)
inspect(run)
checkpoint(run)
replay(run)
recover(run)
```

---

# 541.140 — Explainability

Queries:

```text
why_parallel(node)
why_serial(node)
why_checkpoint(node)
why_retry(node)
why_persist(node)
why_not_fused(node)
why_not_cached(node)
why_waiting(run)
why_failed(run)
```

---

# 541.141 — Evidence

Compiler explanation phải chỉ ra:

- dependency;
- effect;
- policy;
- capability;
- resource;
- type;
- durability boundary.

---

# 541.142 — Optimization Evidence

Compiler không được nói “optimized” nếu không có transformation record.

---

# 541.143 — Transformation Record

```text
OptimizationRecord {
    before
    transformation
    after
    reason
    evidence
}
```

---

# 541.144 — Semantic Preservation

Mỗi optimization phải có semantic precondition.

---

# 541.145 — Unknown Optimization

Nếu compiler không chứng minh được điều kiện, giữ nguyên graph.

---

# 541.146 — No Unsafe Guess

Compiler không được optimize dựa trên assumption không được khai báo.

---

# 541.147 — Runtime Adaptive Optimization

Runtime có thể thay scheduler/batching/cache policy mà không thay semantic behavior.

---

# 541.148 — Profile-Guided Workflow Optimization

481/476 profile data có thể guide optimization.

Profile stale phải được phát hiện.

---

# 541.149 — Cost Model

Cost model có thể dự đoán:

- latency;
- resource;
- memory;
- checkpoint cost.

Nhưng prediction không phải guarantee.

---

# 541.150 — Continuous Optimization

Production runtime có thể collect local profile nếu user/deployment policy cho phép.

Không automatic telemetry.

---

# 541.151 — Workflow Artifact

Build output:

```text
.workflow
.workflow.meta
.workflow.plan
.workflow.debug
```

Tên cụ thể có thể thay đổi, nhưng semantic separation bắt buộc.

---

# 541.152 — Native Embedding

Workflow plan có thể được embed trực tiếp vào Axiom executable.

---

# 541.153 — Runtime Pruning

Nếu application chỉ dùng ephemeral workflow:

```text
durable store
event sourcing
distributed scheduler
```

không được kéo vào binary nếu không cần.

---

# 541.154 — Freestanding

Workflow runtime không bắt buộc cho freestanding Axiom.

---

# 541.155 — WASM

Workflow runtime có thể chạy trong WASM nếu platform capabilities đáp ứng.

---

# 541.156 — Resource Limits

Runtime phải enforce:

```text max_nodes
max_steps
max_event_size
max_state_size
max_parallelism
max_retries
max_runtime
```

---

# 541.157 — Infinite Growth

Event/state growth phải có retention/compaction policy.

---

# 541.158 — Large Event

Large payload có thể externalize thành ArtifactRef.

---

# 541.159 — Event Integrity

Event log hỗ trợ checksum/hash chain nếu audit integrity yêu cầu.

---

# 541.160 — Durable Storage

Workflow state store phải có explicit durability semantics từ 455.

---

# 541.161 — Crash Consistency

State + checkpoint metadata phải có crash-consistent commit.

---

# 541.162 — Backup

Workflow durable state có thể backup/restore.

---

# 541.163 — Restore Identity

Restore phải giữ hoặc remap:

```text WorkflowId
RunId
EventSequence
Version
```

theo explicit policy.

---

# 541.164 — Cross-Version Replay

Replay old run against newer workflow phải yêu cầu compatibility/migration.

---

# 541.165 — Cross-Version Debugging

Debug artifact phải chứa workflow version + execution plan identity.

---

# 541.166 — Compiler/Runtime Compatibility

Execution plan chỉ được chạy trên runtime contract tương thích.

---

# 541.167 — Plan Invalidity

Runtime phải reject incompatible execution plan thay vì cố chạy.

---

# 541.168 — Native Performance

Transient workflow nodes nên có overhead thấp:

```textfunction call
state transition
queue operation
```

không cần managed VM.

---

# 541.169 — Hot Path

Runtime hot path không được serialize state nếu node không crossing durability boundary.

---

# 541.170 — Allocation Policy

Runtime allocator có thể dùng arena/pool để giảm allocation.

---

# 541.171 — No GC Requirement

Workflow runtime không được yêu cầu garbage collector.

---

# 541.172 — Ownership

Runtime state/resource ownership tuân 423.

---

# 541.173 — Cleanup

Node cancellation/failure phải chạy cleanup.

---

# 541.174 — Resource Leak

Static/runtime diagnostics phát hiện leaked workflow resources.

---

# 541.175 — Native Thread Usage

Async waits không được giữ OS thread nếu không cần.

---

# 541.176 — Blocking Node

Blocking node phải khai báo và scheduler phân loại.

---

# 541.177 — Realtime Boundary

Realtime workflow không tự động được áp dụng cho ordinary workflows.

---

# 541.178 — Realtime Node

Node có thể khai báo realtime constraints nhưng phải tuân 461.

---

# 541.179 — AI Model Cancellation

Model request cancellation phải propagate tới serving layer 529.

---

# 541.180 — Tool Cancellation

Tool cancellation phải propagate tới 513/535.

---

# 541.181 — Human Cancellation

Human task cancellation phải invalidate pending approval nếu policy yêu cầu.

---

# 541.182 — Approval Token

Approval token gắn với:

```text
WorkflowRun
Node
Action
PolicyVersion
CapabilitySet
Expiration
```

---

# 541.183 — Approval Replay

Historical approval không tự động authorize a different action.

---

# 541.184 — Model Decision

Model-generated decision không phải policy decision.

---

# 541.185 — Policy Evaluation

Policy engine có final authority over controlled side effects.

---

# 541.186 — Audit

Policy decision phải có provenance khi audit yêu cầu.

---

# 541.187 — Testing Oracle

Workflow tests có thể assert:

- state;
- event;
- output;
- effect;
- capability;
- retry;
- timing;
- resource.

---

# 541.188 — Property Testing

Các invariant của workflow có thể được kiểm tra bằng property tests.

---

# 541.189 — Model Mock

Model output phải có deterministic fixture trong deterministic test.

---

# 541.190 — Tool Mock

Tool mock phải khai báo effect tương ứng với real tool.

---

# 541.191 — Replay Fidelity

Replay report phải phân biệt:

```textExact
Equivalent
Partial
NonReplayable
```

---

# 541.192 — Non-Replayable

Irreversible external side effects có thể làm run không replayable hoàn toàn.

---

# 541.193 — Workflow Diff

Compiler có semantic diff giữa Workflow v1/v2.

---

# 541.194 — Workflow Migration

State migration dùng 539.

---

# 541.195 — Migration Checkpoint

Trước migration production state có thể checkpoint.

---

# 541.196 — Rollback

Rollback phải restore compatible state hoặc dùng reverse migration.

---

# 541.197 — No Silent Upgrade

Running workflow không tự động đổi version.

---

# 541.198 — Deployment Integration

534 quyết định fleet placement; 541 tạo execution plan.

---

# 541.199 — Registry Integration

533 cung cấp immutable workflow/model/tool artifacts.

---

# 541.200 — Final Hard Invariant

**Workflow compiler/runtime của Axiom phải biến Workflow Graph thành execution plan native, typed, effect-aware, durable và recoverable; compiler được phép fuse, parallelize, cache, batch và tối ưu mạnh đối với các phần có thể chứng minh an toàn, nhưng tuyệt đối không được làm mất semantic boundary của state, side effect, capability, policy, durability, approval, cancellation hoặc external uncertainty. Runtime phải hỗ trợ crash recovery, checkpoint, event/snapshot, deterministic replay, distributed execution và resource governance mà không biến GC, VM, scheduler hoặc durable storage thành dependency bắt buộc của mọi Axiom application.**

**BOOTSTRAP-541 hoàn tất / LOCKED.**

---

# BOOTSTRAP-542 — AI WORKFLOW DISTRIBUTED EXECUTION, DURABLE STATE STORE, EVENT LOG, WORKER COORDINATION, EXACTLY-ONCE STATE COMMIT, LEASE/FENCING & GLOBAL WORKFLOW RECOVERY

**Trạng thái: COMPLETED / LOCKED**

`541` đã tạo compiler/runtime đơn máy. `542` mở rộng execution engine thành **distributed durable workflow substrate**, tập trung vào vấn đề khó nhất của workflow production: nhiều worker, crash, duplicate execution, stale worker, network partition và durable state.

```text
                 Workflow Control Plane
                         │
                         ▼
                  Workflow Registry
                         │
                         ▼
                  Durable State Store
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
           Worker A   Worker B   Worker C
              │          │          │
              └──────────┼──────────┘
                         ▼
                    Event Log
                         │
              ┌──────────┼──────────┐
              ▼          ▼          ▼
          Scheduler    Recovery   Replay
```

## 542.1 — Worker ≠ Workflow Run

Một workflow run có thể được thực hiện bởi nhiều worker theo thời gian.

## 542.2 — Worker Identity

```text
WorkerId
ProcessId
NodeId
Epoch
Capabilities
```

## 542.3 — Run Ownership

Một node attempt có owner/lease rõ ràng.

## 542.4 — Lease

```text
Lease {
    owner
    run
    node
    attempt
    expiry
    epoch
}
```

## 542.5 — Fencing Token

Mọi write quan trọng có thể yêu cầu fencing token.

Worker cũ không thể commit sau khi lease đã bị thu hồi.

## 542.6 — Stale Worker

```text
Worker A epoch=10
Worker B epoch=11
```

A không được commit state nếu epoch 10 đã invalid.

## 542.7 — Claim

Node execution claim phải atomic khi backend hỗ trợ.

## 542.8 — Attempt Identity

Mỗi retry:

```text
RunId + NodeId + AttemptId
```

khác nhau.

## 542.9 — State Version

State update dùng optimistic version:

```text
expected_version
new_version
```

## 542.10 — Compare-and-Swap

Backend có thể dùng CAS để bảo vệ concurrent state transitions.

## 542.11 — Event Sequence

Mỗi run có monotonically increasing logical event sequence.

## 542.12 — Duplicate Event

Duplicate event không được tạo duplicate state transition nếu transition yêu cầu idempotency.

## 542.13 — Event Dedup Store

EventId có thể được lưu với processing status.

## 542.14 — Event Processing

```text
Received
Claimed
Applied
Committed
```

được phân biệt.

## 542.15 — Commit Boundary

State transition và event acknowledgement phải có rõ semantics.

## 542.16 — Transactional State/Event

Nếu storage hỗ trợ transaction, state update + event append có thể commit atomically.

## 542.17 — Outbox

External notification có thể dùng outbox:

```text
State Commit
     ↓
Outbox Record
     ↓
Delivery Worker
```

## 542.18 — Outbox ≠ External Exactly-Once

Outbox chỉ bảo đảm local durable intent, không bảo đảm provider external xử lý exactly once.

## 542.19 — Inbox

External event consumer có thể dùng inbox/dedup.

## 542.20 — At-Least-Once

Default distributed delivery semantics không được giả vờ exactly-once.

## 542.21 — Exactly-Once State Transition

Có thể đạt trong phạm vi transactional state store nếu transaction semantics cho phép.

## 542.22 — External Effect

External effect vẫn cần idempotency key hoặc provider transaction semantics.

## 542.23 — Unknown Result

Crash giữa request và response → Unknown.

## 542.24 — Recovery Resolver

Unknown external effect:

```textQuery
Retry
Compensate
Human
Abort
```

## 542.25 — Worker Crash

Run state vẫn durable.

## 542.26 — Scheduler Crash

Work claims survive/recover theo lease.

## 542.27 — Storage Failure

Runtime không được báo committed nếu storage chưa xác nhận durability semantics.

## 542.28 — Network Partition

Không được coi partition là worker death ngay lập tức.

## 542.29 — Lease Expiration

Lease expiration chỉ là failure-detection evidence; fencing bảo vệ correctness.

## 542.30 — Clock Safety

Lease sử dụng server-side monotonic/deadline semantics nơi có thể; không dựa mù quáng vào wall clock.

## 542.31 — Leader Election

Distributed scheduler leader có:

```textterm
epoch
fencing
```

## 542.32 — Scheduler Split Brain

Stale leader không được commit scheduler-owned state.

## 542.33 — Work Stealing

Worker có thể claim pending work.

## 542.34 — Backpressure

Global queue có giới hạn.

## 542.35 — Fairness

Scheduler có tenant/workflow fairness policies.

## 542.36 — Priority

Priority không bypass security/capability constraints.

## 542.37 — Resource Reservation

Worker claim có thể reserve CPU/GPU/memory quota.

## 542.38 — GPU Placement

AI workflow node có thể yêu cầu:

```textGPU type
VRAM
backend
features
```

## 542.39 — Device Loss

GPU/device loss đưa attempt vào explicit failure/recovery state.

## 542.40 — Retry Classification

Retryable ≠ all failures.

## 542.41 — Retry Budget

Global + workflow + node budgets.

## 542.42 — Exponential Backoff

Bounded.

## 542.43 — Jitter

Optional để tránh thundering herd.

## 542.44 — Retry Storm Protection

Scheduler có admission control.

## 542.45 — Poison Node

Repeated failure có thể chuyển node/workflow sang paused/manual-review policy.

## 542.46 — Dead Letter

Unprocessable event có dead-letter path.

## 542.47 — Dead Letter ≠ Loss

Dead-letter record phải durable theo policy.

## 542.48 — Workflow Queue

Queue entry:

```text
RunId
NodeId
Attempt
Priority
Deadline
Capabilities
```

## 542.49 — Queue Visibility

Claimed work có visibility timeout/lease.

## 542.50 — Cancellation

Cancelled run không nhận work mới.

## 542.51 — Running Cancellation

Running worker nhận cancellation signal.

## 542.52 — Forced Cancellation

External side effect vẫn có thể Unknown.

## 542.53 — Durable Cancellation

Cancellation state persisted.

## 542.54 — Pause

Scheduler không dispatch node mới.

## 542.55 — Resume

Resume sử dụng current compatible workflow version.

## 542.56 — Migration

Migration requires 539 compatibility.

## 542.57 — Global State Store

Store:

```textRunState
NodeState
WorkflowState
Checkpoint
Lease
Event
Outbox
Inbox
```

## 542.58 — State Partitioning

Partition theo RunId/tenant/workflow.

## 542.59 — Hot Partition

Runtime phải có policy phát hiện hotspot.

## 542.60 — Replication

State store có thể dùng 502 replication.

## 542.61 — Durability

`Committed` phải map tới documented storage durability level.

## 542.62 — Applied ≠ Durable

Applied state in memory chưa phải durable state.

## 542.63 — Durable ≠ Replicated

Local durable chưa nhất thiết replicated.

## 542.64 — Replicated ≠ Committed

Replication protocol semantics vẫn phải explicit.

## 542.65 — Event Log

Event log append-only logical sequence.

## 542.66 — Compaction

Snapshot + log compaction.

## 542.67 — Audit Retention

Audit policy độc lập event-compaction policy.

## 542.68 — Event Integrity

Checksum/hash optional.

## 542.69 — Corrupt Event

Recovery phải detect và fail safely.

## 542.70 — Snapshot Validation

Snapshot có:

```textchecksum
schema version
workflow version
event position
```

## 542.71 — Snapshot Install

Atomic.

## 542.72 — Snapshot Recovery

Load snapshot → replay remaining events.

## 542.73 — Partial Snapshot

Không được xem là valid snapshot.

## 542.74 — Recovery Checkpoint

Recovery records progress.

## 542.75 — Replay Idempotency

Replay không thực hiện external effects mặc định.

## 542.76 — Simulation

Replay/simulation sử dụng mock effect providers.

## 542.77 — Historical Model

Historical model version phải được giữ hoặc migrated artifact phải tồn tại.

## 542.78 — Historical Tool

Tool response provenance được giữ.

## 542.79 — Historical Policy

Policy version được giữ.

## 542.80 — Historical Approval

Approval context được giữ.

## 542.81 — Distributed Trace

RunId/NodeId/AttemptId map sang 475/481 trace IDs.

## 542.82 — Cross-Worker Trace

Worker migration không làm mất logical trace identity.

## 542.83 — Worker Metrics

Track:

- queue wait;
- execution;
- retries;
- lease;
- checkpoint;
- state store latency.

## 542.84 — Workflow Metrics

Track:

- active runs;
- completed;
- failed;
- cancelled;
- paused;
- waiting;
- recovery;
- replay.

## 542.85 — Cost Attribution

CPU/GPU/model/tool/storage cost gắn RunId.

## 542.86 — Tenant Accounting

Usage attribution theo tenant.

## 542.87 — Security

Worker chỉ nhận capability cần cho assigned node.

## 542.88 — Capability Attenuation

Scheduler không cấp capability rộng hơn workflow manifest.

## 542.89 — Secret Delivery

Secret không nằm trong queue payload plaintext mặc định.

## 542.90 — Worker Isolation

Untrusted tool/model execution có thể chạy process/WASM sandbox.

## 542.91 — Worker Authentication

Workers phải authenticate với control/state plane.

## 542.92 — Authorization

Worker được authorize theo role/capability.

## 542.93 — Node Assignment

Assignment kiểm tra:

```text capability
resource
policy
version
device
tenant
```

## 542.94 — Worker Draining

Draining worker không nhận new work.

## 542.95 — Worker Shutdown

Current safe work được checkpoint/released theo policy.

## 542.96 — Worker Replacement

Replacement worker có thể resume leased/recoverable work.

## 542.97 — Duplicate Execution

Duplicate attempts có thể xảy ra trong distributed failure.

Correctness không được phụ thuộc vào assumption “never duplicate”.

## 542.98 — Idempotent Node

Node contract có thể khai báo idempotent.

## 542.99 — Non-Idempotent Node

Retry phải qua policy/compensation/recovery.

## 542.100 — Node Transaction

Node có thể có local transaction boundary.

## 542.101 — Workflow Transaction

Workflow transaction không biến toàn bộ external world thành ACID transaction.

## 542.102 — Saga

Compensation chain có thể implement Saga semantics.

## 542.103 — Saga State

Compensation progress durable.

## 542.104 — Compensation Retry

Compensation có retry policy riêng.

## 542.105 — Compensation Failure

Explicit `CompensationFailed`.

## 542.106 — Human Escalation

Compensation failure có thể escalate.

## 542.107 — Global Deadline

Run deadline propagates tới workers/nodes.

## 542.108 — Deadline Enforcement

Scheduler không dispatch expired work.

## 542.109 — Clock Skew

Distributed deadlines phải account for clock uncertainty.

## 542.110 — Monotonic Local Timing

Local timeout dùng monotonic clock.

## 542.111 — Persistent Deadline

Durable deadline lưu canonical timestamp/clock semantics.

## 542.112 — Timer Service

Timer service có durable schedule.

## 542.113 — Duplicate Timer

Timer event phải idempotent.

## 542.114 — Missed Timer

Policy:

```textSkip
CatchUp
Coalesce
```

## 542.115 — Recurring Timer

Schedule identity + occurrence identity.

## 542.116 — Event Trigger

Trigger identity chống duplicate.

## 542.117 — Global Event Ordering

Không giả định global ordering nếu transport không cung cấp.

## 542.118 — Per-Key Ordering

Có thể yêu cầu ordering theo key.

## 542.119 — Causal Ordering

Có thể lưu causality metadata.

## 542.120 — Cross-Region

Cross-region workflow semantics phải explicit.

## 542.121 — Regional Failure

Run có thể migrate region nếu state/capability policy cho phép.

## 542.122 — Data Locality

Workflow data residency policy được enforce.

## 542.123 — Tenant Locality

Tenant-specific placement constraints.

## 542.124 — Disaster Recovery

State store backup/restore.

## 542.125 — Recovery Point

RPO explicit.

## 542.126 — Recovery Time

RTO là deployment/system target, không semantic guarantee.

## 542.127 — Backup Verification

Backup phải có restore validation.

## 542.128 — Cross-Version Restore

Restore validates workflow/runtime/schema compatibility.

## 542.129 — Immutable Event History

Published audit history không mutate tùy ý.

## 542.130 — Event Redaction

Privacy deletion có thể require cryptographic/data-layer strategy thay vì sửa lịch sử tùy tiện.

## 542.131 — PII

PII classification tích hợp 528.

## 542.132 — Data Retention

Workflow state/event retention policy explicit.

## 542.133 — Deletion Impact

Xóa data phải biết downstream workflow/run dependencies.

## 542.134 — Access-Controlled Inspection

Inspect workflow chỉ thấy data mà caller có quyền.

## 542.135 — AI Debugger

AI query:

```textwhy_stuck
why_retried
why_duplicate
why_not_scheduled
why_recovered
why_fenced
why_unknown
```

## 542.136 — Evidence Graph

Explanation gồm:

```textRun
→ Node
→ Attempt
→ Worker
→ Lease
→ Event
→ State
```

## 542.137 — No Fabricated Causality

Correlation không được trình bày như causal proof.

## 542.138 — Deterministic Distributed Test

Có deterministic:

```textscheduler
message delivery
clock
worker failure
storage failure
```

## 542.139 — Partition Test

Simulate network partitions.

## 542.140 — Duplicate Test

Inject duplicate event/work.

## 542.141 — Reordering Test

Inject event reorder.

## 542.142 — Crash Test

Crash worker at every critical boundary.

## 542.143 — Fencing Test

Verify stale worker cannot commit.

## 542.144 — Lease Race Test

Test concurrent expiration/reassignment.

## 542.145 — Storage Race Test

Test concurrent state transitions.

## 542.146 — Property

Invariant:

```textat most one valid owner
```

ở mỗi fencing epoch.

## 542.147 — State Monotonicity

State transitions không được quay ngược trừ explicit recovery/migration.

## 542.148 — Event Sequence Monotonicity

Committed sequence không được giảm.

## 542.149 — Attempt Identity

Mỗi attempt có unique identity.

## 542.150 — Run Identity

RunId stable qua worker migration.

## 542.151 — Node Identity

NodeId stable trong workflow version.

## 542.152 — Version Identity

Workflow version immutable.

## 542.153 — Plan Identity

Execution plan hash stable cho cùng inputs/compiler/runtime contract.

## 542.154 — Worker Capability

Worker capability snapshot được ghi nhận tại assignment.

## 542.155 — Device Identity

GPU/device assignment recorded.

## 542.156 — Model Identity

Model version/variant recorded.

## 542.157 — Tool Identity

Tool version/protocol recorded.

## 542.158 — Policy Identity

Policy version recorded.

## 542.159 — Configuration Identity

Runtime config fingerprint recorded.

## 542.160 — Build Identity

Runtime/compiler build ID recorded.

## 542.161 — Reproducibility

Run manifest đủ để tái dựng environment khi artifacts còn tồn tại.

## 542.162 — Unknown Preservation

Unknown external state không bị chuyển thành success chỉ để workflow tiến tiếp.

## 542.163 — Failure Evidence

Failure giữ error/call stack/node/attempt/worker provenance.

## 542.164 — Recovery Evidence

Recovery giữ nguyên nhân/state transition evidence.

## 542.165 — Rollback

Rollback deployment không rewind external effects.

## 542.166 — Migration

Migration state phải explicit.

## 542.167 — Running Version

Run không tự đổi version.

## 542.168 — Runtime Compatibility

Worker runtime phải tương thích execution plan.

## 542.169 — Backend Compatibility

Model/tool backend phải compatible.

## 542.170 — Native Runtime

Distributed workflow runtime không cần VM managed.

## 542.171 — No GC

Distributed workflow runtime không yêu cầu GC.

## 542.172 — No Hidden Threads

Chờ durable workflow không giữ thread vô ích.

## 542.173 — No Hidden Network

Ephemeral local workflow không tự động cần network.

## 542.174 — No Hidden Storage

Non-durable workflow không tự động cần persistent DB.

## 542.175 — Runtime Pruning

Chỉ link distributed components khi application sử dụng.

## 542.176 — Freestanding

Freestanding application có thể loại toàn bộ workflow distributed stack.

## 542.177 — WASM

Distributed workflow APIs obey WASM host capability restrictions.

## 542.178 — Resource Quotas

Global worker fleet có quotas.

## 542.179 — Queue Quotas

Per-tenant/per-workflow queue limits.

## 542.180 — State Quotas

Per-run state/event limits.

## 542.181 — Payload Limits

Event/payload size limits.

## 542.182 — Retry Limits

Attempt limits.

## 542.183 — Concurrency Limits

Per-run/per-workflow/per-tenant limits.

## 542.184 — GPU Quotas

GPU concurrency/memory quotas.

## 542.185 — Model Quotas

Inference token/request quotas integrate 529/534.

## 542.186 — Tool Quotas

Tool call quotas integrate 535.

## 542.187 — Admission

Over-quota work rejected/queued according to policy.

## 542.188 — Fair Scheduling

Scheduler can prevent one tenant starving others.

## 542.189 — Priority Inversion

Resource dependencies can be surfaced.

## 542.190 — Deadlock

Workflow graph deadlocks should be statically detected where possible.

## 542.191 — Distributed Deadlock

Dynamic resource deadlock is runtime-detectable where instrumentation permits.

## 542.192 — Worker Affinity

Session/state locality can influence placement.

## 542.193 — Cache Affinity

Model/KV/resource cache locality can influence scheduling.

## 542.194 — Placement Failure

No suitable worker → explicit `Unschedulable`.

## 542.195 — Unschedulable Explanation

Explain missing:

```textresource
capability
policy
quota
version
device
```

## 542.196 — Autoscaling Integration

534 controls fleet scaling; 542 reports pending demand/resource state.

## 542.197 — Control/Data Plane Separation

Workflow execution data plane không được phụ thuộc vào UI/control-plane presentation.

## 542.198 — Registry Failure

Already-running workflows may continue if required artifacts are locally cached and policy permits.

## 542.199 — Registry Unavailability

Không tự động làm mất durable state.

## 542.200 — Final Hard Invariant

**Distributed Workflow Runtime của Axiom phải coi crash, duplicate, retry, stale worker, network partition, delayed response và external Unknown state là các trạng thái bình thường cần được mô hình hóa; durable state transition phải có identity/version/fencing rõ ràng, event/snapshot phải recoverable và replayable, còn external side effect không được giả vờ exactly-once nếu provider không cung cấp semantics đó. Hệ thống phải scale từ một process lên nhiều worker/region mà không đưa distributed scheduler, database hoặc network thành dependency bắt buộc của workflow local.**

**BOOTSTRAP-542 hoàn tất / LOCKED.**

### Tiếp theo

**`BOOTSTRAP-543 — AI WORKFLOW OBSERVABILITY, EXECUTION HISTORY, EVENT REPLAY, TIME-TRAVEL DEBUGGING, CAUSAL TRACE, COST ATTRIBUTION & AI-ASSISTED ROOT-CAUSE ANALYSIS`**