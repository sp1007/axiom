# BOOTSTRAP-334 — AXIOM BUILD GRAPH EXECUTION, PARALLELISM & DISTRIBUTED COMPILATION ENGINE

Sau 333, dependency/incremental model đã xác định **cái gì cần rebuild**. Bước tiếp theo là đặc tả **cách compiler thực thi build graph đó nhanh, song song, có kiểm soát tài nguyên và có thể phân tán sang nhiều máy**.

Mục tiêu không chỉ là “build song song”, mà là:

> **Compiler phải tự tìm được mức song song tối ưu mà không phá deterministic build, không làm nổ RAM và không làm mất lợi thế incremental compilation.**

---

# 1. Mô hình tổng thể

```text
                Build Graph
                    │
                    ▼
             Dependency Analysis
                    │
                    ▼
             Ready Node Queue
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
       Worker 1  Worker 2  Worker 3
          │         │         │
          └─────────┼─────────┘
                    ▼
              Result Verify
                    │
                    ▼
              Publish Cache
                    │
                    ▼
              Unlock Dependents
```

Không để mỗi compiler pass tự tạo thread pool riêng.

Toàn bộ compiler dùng một **Global Build Scheduler**.

---

# 2. Scheduler là một tầng độc lập

Compiler architecture:

```text
Semantic Engine
      │
      ▼
Build Graph
      │
      ▼
Scheduler
      │
      ├── Local Worker
      ├── Remote Worker
      └── Cache
```

Semantic engine nói:

> Node này có thể chạy.

Scheduler quyết định:

> Chạy ở đâu, lúc nào, với bao nhiêu tài nguyên.

---

# 3. Build Node

Mỗi node:

```text id="f9df5f"
BuildNode {
    id
    kind

    inputs
    dependencies
    outputs

    fingerprint

    cpu_cost
    memory_cost
    io_cost

    target
    capabilities

    priority
    locality
}
```

`cpu_cost` và `memory_cost` là estimate, không phải semantic fact.

---

# 4. Node state

```text id="qvwx1s"
Pending
Ready
Queued
Running
Completed
Cached
Failed
Cancelled
Blocked
```

Transition:

```text id="y3d7ut"
Pending
   ↓
Ready
   ↓
Queued
   ↓
Running
   ↓
Completed
```

Cache hit:

```text id="k0f8z1"
Ready → Cached
```

Dependency failure:

```text id="8t8p9f"
Pending → Blocked
```

---

# 5. Ready Queue

Một node chỉ Ready khi:

```text id="zy9wqn"
all required dependencies completed
```

Không dựa vào source order.

Ví dụ:

```text id="7x3u0v"
A ──→ C
B ──→ C
D ──→ E
```

A và B có thể chạy song song.

D cũng có thể chạy đồng thời.

---

# 6. Critical Path

Scheduler tính:

```text id="x5e6v1"
critical_path_cost(node)
```

Ví dụ:

```text id="e7gh2c"
A(10)
├── B(20)
│    └── D(30)
└── C(5)
```

Critical path:

```text id="zixf4j"
A → B → D = 60
```

Scheduler ưu tiên node trên critical path.

---

# 7. Nhưng không chỉ ưu tiên critical path

Nếu node critical path cần:

```text id="5b0o3e"
8 GB RAM
```

trong khi máy chỉ còn:

```text id="20n8af"
6 GB
```

không được chạy.

Scheduler phải cân bằng:

```text id="3tqj2v"
Criticality
CPU
Memory
IO
Target locality
Cache locality
Remote cost
```

---

# 8. Resource Token Model

Đề xuất:

```text id="9k3n7g"
ResourceBudget {
    cpu_tokens
    memory_tokens
    io_tokens
    gpu_tokens
}
```

Node yêu cầu:

```text id="0yuhmz"
ResourceRequest {
    cpu
    memory
    io
    gpu
}
```

Scheduler chỉ chạy nếu budget đủ.

---

# 9. Memory budget

Đây là yếu tố rất quan trọng với compiler.

Ví dụ:

```text id="ax2m7z"
RAM = 32 GB
```

Không nên:

```text id="0brfvi"
spawn 32 LTO jobs
```

nếu mỗi job cần 4 GB.

Scheduler phải biết:

```text id="sm0h3g"
available_memory
reserved_memory
estimated_peak_memory
```

---

# 10. Memory reservation

Trước khi start node:

```text id="d5g6i7"
reserve(memory_estimate)
```

Nếu không đủ:

```text id="p4w0qz"
queue
```

Sau khi hoàn thành:

```text id="w7q4x8"
release(memory)
```

---

# 11. Dynamic memory adjustment

Estimate có thể sai.

Nếu process thực tế dùng:

```text id="m8g7cc"
2 GB → 5 GB
```

scheduler phải:

```text id="23hslm"
increase reservation
```

hoặc throttle.

Không để compiler tự do OOM cả máy.

---

# 12. Memory pressure modes

```text id="4gkq9h"
Normal
Pressure
Critical
```

### Normal

Parallelism tối đa.

### Pressure

Giảm concurrent memory-heavy jobs.

### Critical

Ưu tiên hoàn thành jobs đang chạy, hạn chế start job mới.

---

# 13. CPU scheduling

CPU token không nhất thiết = hardware thread.

Ví dụ:

```text id="g5azpf"
Compile parsing = 1
Trait solving = 2
LTO = 8
```

Scheduler có thể phân bổ trọng số.

---

# 14. Nested parallelism

Không cho:

```text id="s5k0i6"
Build scheduler
  ↓
Worker
  ↓
LLVM-like pass
  ↓
spawn 16 threads
```

→ oversubscription.

Compiler subsystem phải dùng scheduler chung hoặc cooperative parallelism.

---

# 15. Parallel query evaluation

Compiler query engine hỗ trợ:

```text id="x9fhxw"
query A
query B
query C
```

song song nếu dependency graph cho phép.

Scheduler quản lý chúng như BuildNodes.

---

# 16. Deterministic result ordering

Parallel execution:

```text id="c1r7vi"
B completes first
A completes second
```

không được làm:

```text id="k4c0n8"
symbol ordering = B, A
```

Canonical ordering vẫn dựa trên:

```text id="q0s2l9"
stable IDs
source order
semantic ordering rules
```

---

# 17. Stable IDs

Build node phải dùng stable identity:

```text id="m1axqk"
PackageId
ModuleId
FunctionId
GenericInstanceId
```

không dùng:

```text id="q2xw8c"
thread ID
memory address
execution order
```

để xác định semantic identity.

---

# 18. Parallel diagnostics

Nhiều worker có thể phát hiện lỗi cùng lúc.

Không hiển thị theo completion order.

Compiler sort diagnostics theo:

```text id="v7j3hx"
SourceFile
SourceOffset
DiagnosticSeverity
StableDiagnosticId
```

---

# 19. Diagnostic determinism

Build:

```text id="0n4r8w"
parallel
```

và:

```text id="e1b6ps"
single-thread
```

phải tạo cùng diagnostic set và ordering.

---

# 20. Failure isolation

Một node fail:

```text id="9a8g5h"
TypeCheck(A)
```

chỉ những node phụ thuộc trực tiếp/gián tiếp bị:

```text id="v3i1sz"
Blocked
```

Các node độc lập vẫn chạy nếu policy cho phép.

Điều này hữu ích cho IDE và diagnostic-rich builds.

---

# 21. Fail-fast vs collect-errors

Hai mode:

```text id="9v5p9j"
FailFast
CollectDiagnostics
```

### FailFast

Dừng sớm.

### CollectDiagnostics

Chạy các nhánh độc lập để thu nhiều lỗi.

Không thay đổi semantic correctness.

---

# 22. Cancellation

Build có:

```text id="b6yrw2"
CancellationToken
```

Khi user nhấn Ctrl+C:

```text id="4y4m0k"
Running nodes
    ↓
Cancellation requested
    ↓
cooperative stop
```

Không kill thread giữa một critical section nếu có thể tránh.

---

# 23. Cache-first scheduling

Scheduler nên kiểm tra cache trước:

```text id="x8w1s3"
Ready
 ↓
Cache lookup
 ├── Hit → Cached
 └── Miss → Queue
```

Điều này có thể giảm đáng kể build work.

---

# 24. Cache locality

Nếu nhiều nodes cần artifact từ cùng cache storage:

```text id="6j4g4x"
prefer same worker
```

nếu lợi ích lớn.

Nhưng locality không được thay đổi semantic result.

---

# 25. Remote execution

Remote worker chỉ nhận verified inputs.

```text id="z7o3n2"
Coordinator
   ↓
Input manifest
   ↓
Remote worker
```

Worker không cần quyền đọc project host filesystem.

---

# 26. Remote execution request

```text id="v3l8wq"
ExecutionRequest {
    node_id
    input_artifacts
    compiler_artifact
    target
    configuration
    capability_policy
    resource_limit
}
```

---

# 27. Remote result

```text id="o7q6ns"
ExecutionResult {
    node_id
    outputs
    output_fingerprints
    diagnostics
    proof_metadata
    attestation
}
```

Coordinator verify toàn bộ.

---

# 28. Remote worker isolation

Worker nên chạy:

```text id="l6b6k2"
sandbox
```

và chỉ thấy:

```text id="e6fjw8"
/input
/work
/output
```

Không thấy host environment.

---

# 29. Remote cache vs remote execution

Hai khái niệm riêng:

```text id="j1a2xx"
Remote Cache
```

→ lấy result đã có.

```text id="q8svv7"
Remote Execution
```

→ yêu cầu worker tính result.

Pipeline:

```text id="ynqf8j"
Cache?
 ├── yes → download
 └── no
      ↓
Remote execution?
 ├── yes → execute
 └── no → local
```

---

# 30. Cost model

Scheduler cần ước lượng:

```text id="7v5f2q"
LocalCost
RemoteTransferCost
RemoteExecutionCost
CacheLookupCost
```

Ví dụ node nhỏ:

```text id="2e5n7q"
1 KB input
5 ms compile
```

không đáng remote.

Node lớn:

```text id="9j1q4p"
2 GB input
30 sec compile
```

có thể đáng.

---

# 31. Remote scheduling policy

Các policy:

```text id="e4h6fr"
LocalOnly
RemoteOnly
LocalPreferred
RemotePreferred
Adaptive
```

Default:

```text id="1k5l2x"
Adaptive
```

---

# 32. Target-aware workers

Worker phải advertise:

```text id="d8g2hf"
WorkerCapabilities {
    host
    supported_targets
    CPUFeatures
    memory
    GPU
    compiler_versions
}
```

Không gửi node ARM64 cho worker không có target support.

---

# 33. Compiler binary distribution

Remote worker phải sử dụng compiler artifact đúng:

```text id="4fhv3x"
CompilerFingerprint
```

Không được:

```text id="5m6h8y"
"worker có compiler Axiom"
```

mà phải:

```text id="3drx6f"
compiler semantic identity = required identity
```

---

# 34. Toolchain dependency

Nếu build node cần:

```text id="93b7m4"
protoc
```

worker phải có đúng tool:

```text id="k7e6c1"
ToolFingerprint
```

hoặc tool artifact được gửi cùng request.

---

# 35. Distributed build determinism

Nếu worker A hoặc B thực hiện cùng node:

```text id="gr5t8n"
same inputs
same semantic compiler
same target
```

phải tạo:

```text id="s8d8h4"
same semantic fingerprint
```

Nếu binary reproducibility yêu cầu:

```text id="f8w5m1"
same artifact bytes
```

---

# 36. Worker failure

Worker có thể:

```text id="j7q9j8"
timeout
crash
network disconnect
OOM
invalid result
```

Coordinator:

```text id="7q4o8z"
verify result
```

Nếu thất bại:

```text id="m6f4t2"
retry
```

hoặc:

```text id="l5s7c2"
fallback local
```

---

# 37. Retry determinism

Retry không được tạo duplicate semantic side effects.

Build node nên ideally:

```text id="o6x1e0"
pure with respect to declared inputs
```

Build nodes có side effects phải có explicit capability and transaction semantics.

---

# 38. Idempotent node

Node:

```text id="k6m0q7"
F(inputs) → outputs
```

là lý tưởng.

Nếu chạy hai lần:

```text id="5w8m1f"
F(X) = Y
F(X) = Y
```

Điều này làm remote retry/cache an toàn.

---

# 39. Non-idempotent build operations

Nếu build script:

```text id="6q0u8w"
write external database
```

thì không được coi là ordinary cacheable BuildNode.

Nó phải được đánh dấu:

```text id="l3b9j5"
NonHermetic
NonCacheable
ExternalSideEffect
```

và policy có thể cấm.

---

# 40. Resource-aware graph partitioning

Distributed scheduler có thể partition graph:

```text id="e8u5z1"
Package A → Worker 1
Package B → Worker 2
Package C → Worker 3
```

nhưng cố gắng minimize cross-worker artifact transfer.

Graph partition objective:

```text id="f3z2j7"
minimize:
    transfer_cost
    critical_path
    memory_pressure
```

---

# 41. Build waves

Có thể chia graph thành waves:

```text id="8t7h5x"
Wave 0:
 A B C

Wave 1:
 D E

Wave 2:
 F
```

Nhưng scheduler không nhất thiết phải chờ toàn bộ wave.

Node-ready scheduling tốt hơn barrier toàn wave.

---

# 42. Work stealing

Local workers có thể dùng:

```text id="5r1d0q"
work stealing
```

nhưng semantic result không phụ thuộc execution order.

Mỗi worker lấy node từ queue.

---

# 43. Priority classes

```text id="d2r4g1"
Interactive
Incremental
Normal
Background
CI
Release
```

Ví dụ IDE:

```text id="9l0e2v"
Interactive
```

được ưu tiên hơn background optimization.

---

# 44. IDE mode

Khi user đang gõ:

```text id="m2h3i4"
full optimization = low priority
diagnostics = high priority
```

Compiler có thể:

```text id="y9c5r0"
cancel stale codegen
preserve semantic query
```

để phản hồi nhanh.

---

# 45. Release mode

Release:

```text id="a6j8c2"
LTO
PGO
vectorization
binary optimization
```

được ưu tiên.

Scheduler có thể dùng nhiều CPU/RAM hơn.

---

# 46. Memory reclamation

Sau khi node hoàn thành:

```text id="h8d3q1"
AST temporary
HIR temporary
MIR temporary
```

có thể release nếu không còn dependency.

Build scheduler nên phối hợp với CompilerDB để:

```text id="p3m4k9"
retain
release
spill
reload
```

semantic data.

---

# 47. Spill to disk

Nếu RAM pressure cao:

```text id="7s9c4v"
cold query result
```

có thể spill disk.

Nhưng spilled result phải:

```text id="f4k2h0"
hash verified
fingerprint verified
```

---

# 48. Persistent compiler daemon

`axiomd` có thể giữ:

```text id="r4t6u8"
CompilerDB
QueryCache
ArtifactCache
TargetDB
```

trong memory giữa các builds.

Điều này giúp:

```text id="4x6v9n"
rebuild after small edit
```

rất nhanh.

Nhưng daemon crash:

> không được làm mất semantic correctness.

Persistent state chỉ là cache.

---

# 49. Build session

Mỗi build:

```text id="z7q3s8"
BuildSession {
    session_id
    root_package
    target
    profile
    policy
    graph
    scheduler
    diagnostics
}
```

Build session có lifecycle:

```text id="j9f1w5"
Created
Planning
Executing
Finalizing
Completed
Failed
Cancelled
```

---

# 50. Observability

Scheduler cần metrics:

```text id="x0b8n2"
total_nodes
cache_hits
cache_misses
parallelism
peak_memory
critical_path
local_time
remote_time
transfer_time
scheduler_wait
```

Compiler có thể xuất:

```text id="e4v6t2"
axiom build --stats
```

---

# 51. Build trace

Machine-readable:

```text id="y7q1m4"
build.trace
```

mỗi event:

```text id="c2n8v5"
timestamp
node
worker
state
duration
resource
cache
fingerprint
```

Timestamp chỉ dùng observability, không tham gia semantic fingerprint.

---

# 52. Explain scheduler

CLI:

```text id="j4k8p0"
axiom build --explain-schedule
```

Ví dụ:

```text id="2v6m1r"
foo.mir
  priority: critical-path
  memory: 420 MB
  CPU: 2
  worker: local-2
  cache: miss
```

Rất hữu ích để tối ưu compiler.

---

# 53. CompilerDB additions

```text id="v1k4n7"
BuildSchedulerDB
WorkerDB
ResourceDB
ExecutionDB
RemoteExecutionDB
BuildSessionDB
BuildTraceDB
BuildMetricsDB
CancellationDB
SpillDB
```

---

# 54. APIs

```text id="w8j3c6"
create_build_session()

plan_build_graph()
compute_ready_nodes()

schedule_node()
schedule_parallel()
schedule_remote()

reserve_resources()
release_resources()

register_worker()
query_worker_capabilities()

submit_remote_execution()
verify_remote_result()

cancel_build()
retry_node()
fallback_local()

spill_result()
restore_result()

collect_build_metrics()
export_build_trace()
explain_schedule()
```

---

# 55. Implementation tree

```text id="x5c7n9"
compiler/
└── scheduler/
    ├── graph/
    ├── ready_queue/
    ├── priority/
    ├── resource/
    ├── memory/
    ├── cpu/
    ├── critical_path/
    ├── local/
    ├── remote/
    ├── worker/
    ├── retry/
    ├── cancellation/
    ├── spill/
    ├── metrics/
    └── trace/
```

---

# 56. Invariants

```text id="ASCHED-01"
Build execution must respect the dependency graph.

ASCHED-02
A node may execute only after all required dependencies are valid.

ASCHED-03
Parallel execution must not alter semantic results.

ASCHED-04
Diagnostic ordering must be deterministic.

ASCHED-05
Scheduler resource limits must be enforced.

ASCHED-06
Memory-heavy jobs must participate in memory reservation.

ASCHED-07
Nested uncontrolled parallelism is forbidden.

ASCHED-08
Critical-path optimization must never violate dependency ordering.

ASCHED-09
Cache lookup must occur before unnecessary execution.

ASCHED-10
Remote execution requires verified inputs.

ASCHED-11
Remote results require independent verification.

ASCHED-12
Worker identity and compiler identity must be explicit.

ASCHED-13
Target compatibility must be verified before remote execution.

ASCHED-14
Toolchain dependencies must be fingerprinted.

ASCHED-15
Worker failure must not corrupt build state.

ASCHED-16
Retries must preserve semantic determinism.

ASCHED-17
Cacheable build nodes should be idempotent.

ASCHED-18
Non-hermetic side-effecting nodes must not be silently cached.

ASCHED-19
Cancellation must not corrupt persistent compiler state.

ASCHED-20
Incremental and clean builds must remain semantically equivalent.

ASCHED-21
Scheduler heuristics must never become semantic rules.

ASCHED-22
Execution order must never define declaration or symbol identity.

ASCHED-23
Remote and local execution must share the same semantic verification boundary.

ASCHED-24
Resource estimation may be inaccurate but must never justify violating hard resource limits.

ASCHED-25
Build tracing and metrics must not influence compilation semantics.

ASCHED-26
Interactive builds must be able to prioritize semantic diagnostics over expensive optimization.

ASCHED-27
Release builds may allocate more resources without changing semantics.

ASCHED-28
Spilled compiler state must remain fingerprint-verifiable.

ASCHED-29
Persistent daemon state is cache, never semantic authority.

ASCHED-30
The scheduler is an execution optimizer, not a language-semantic component.
```

---

# 57. Definition of Done

BOOTSTRAP-334 hoàn thành khi Axiom có:

- Global Build Scheduler.
- Ready queue.
- Dependency-aware scheduling.
- Critical-path scheduling.
- CPU resource model.
- Memory resource model.
- IO/GPU resource model.
- Memory reservation.
- Memory-pressure handling.
- Nested parallelism control.
- Parallel query execution.
- Deterministic diagnostics.
- Failure isolation.
- Fail-fast / collect-diagnostics.
- Cancellation.
- Cache-first scheduling.
- Cache locality.
- Local execution.
- Remote execution.
- Remote cache.
- Worker capability discovery.
- Compiler/toolchain fingerprint verification.
- Remote sandbox.
- Retry/fallback.
- Idempotent build-node model.
- Non-hermetic node classification.
- Graph partitioning.
- Work stealing.
- Priority classes.
- IDE scheduling mode.
- Release scheduling mode.
- Memory reclamation.
- Compiler-state spilling.
- Persistent compiler daemon.
- Build sessions.
- Build tracing.
- Scheduler metrics.
- Explainable scheduling.
- Integration với Incremental-333.
- Build Sandbox-331.
- Artifact-332.
- Package-329.
- Proof/Verification Engine.
- CompilerDB.

### Nguyên tắc khóa

> **Axiom không coi “parallelism” là `spawn N threads`. Nó coi build là một bài toán scheduling trên một dependency DAG có ràng buộc CPU, RAM, I/O, target, cache và trust.**

Và một nguyên tắc quan trọng khác:

> **Local build, remote build, cached build và distributed build đều phải đi qua cùng một semantic verification boundary.**

Như vậy, việc chuyển một compilation job từ máy của bạn sang một worker khác chỉ là **thay đổi nơi tính toán**, không phải thay đổi ý nghĩa chương trình.