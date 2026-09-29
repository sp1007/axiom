# BOOTSTRAP-387 — Axiom Compiler-Assisted Optimization & Global Resource Scheduling Engine

Sau **386 — AI Execution Graph**, bước tiếp theo nên giải quyết một vấn đề rộng hơn AI:

> **Axiom cần một cơ chế tối ưu toàn cục có thể phối hợp CPU, SIMD, GPU, memory, parallelism, async và communication thay vì mỗi subsystem tự tối ưu riêng.**

Nếu không có tầng này, chúng ta sẽ có rất nhiều optimizer tốt nhưng dễ “đánh nhau”:

```text
Tensor optimizer      → muốn fuse
SIMD optimizer        → muốn tách loop
GPU optimizer         → muốn tile
Parallel optimizer    → muốn chia worker
Memory optimizer      → muốn materialize/reuse
Async optimizer       → muốn overlap
AI optimizer          → muốn checkpoint/recompute
```

387 xây **Global Resource Scheduling / Execution Planning** để tất cả cùng tối ưu trên một semantic model chung.

---

# 1. Nguyên tắc trung tâm

Compiler không tối ưu từng instruction độc lập.

Nó tối ưu:

```text
Computation
+
Memory
+
Parallelism
+
Device
+
Synchronization
+
Communication
+
Numerical Contract
```

thành một **Global Execution Plan**.

---

# 2. Global Execution Plan

Đề xuất IR/compiler artifact:

```text
AEP — Axiom Execution Plan
```

Pipeline:

```text
Source
  ↓
AST/HIR
  ↓
MIR
  ↓
Domain IR
  ├─ Tensor
  ├─ AI
  ├─ GPU
  ├─ Parallel
  └─ Async
  ↓
AEP
  ↓
Machine/GPU/Runtime lowering
```

AEP không thay thế MIR.

Nó là tầng planning.

---

# 3. AEP chứa gì?

Một execution plan có:

```text
ComputeNode
MemoryNode
TransferNode
ParallelRegion
SynchronizationEdge
DeviceAssignment
StorageAssignment
SchedulingConstraint
CostEstimate
Proof
```

---

# 4. Compute Node

Ví dụ:

```text
GEMM
CONV
FFT
REDUCE
ELEMENTWISE
LOAD
STORE
```

Mỗi node có:

```text
inputs
outputs
device
dtype
shape
layout
cost
dependencies
```

---

# 5. Resource Model

Compiler phải biết computation tiêu thụ:

```text
CPU cores
SIMD registers
GPU SM/CU
GPU registers
shared memory
device memory
host memory
bandwidth
cache
network/interconnect
```

Resource model target-dependent.

---

# 6. Resource Constraint

Ví dụ GPU kernel cần:

```text
registers = 64/thread
shared_memory = 32 KB/block
threads = 256
```

Compiler phải biết occupancy bị ảnh hưởng thế nào.

---

# 7. CPU Resource Model

CPU planning xem xét:

```text
cores
logical CPUs
vector width
register pressure
L1/L2/L3
memory bandwidth
NUMA
```

Không nhất thiết expose tất cả cho programmer.

---

# 8. NUMA-aware Scheduling

Nếu dữ liệu nằm:

```text
NUMA node 0
```

thì compiler/runtime có thể ưu tiên worker trên node 0.

Nhưng semantics không phụ thuộc NUMA.

---

# 9. Memory Bandwidth

Một computation có thể:

```text
low FLOP
high memory traffic
```

thì tăng worker không nhất thiết tăng performance.

Cost model phải nhận biết memory-bound workload.

---

# 10. Compute-bound

Ngược lại:

```text
high FLOP
low memory traffic
```

có thể cần:

```text
SIMD
GPU
more parallelism
```

---

# 11. Roofline-style Cost Model

Compiler có thể dùng:

```text
arithmetic intensity
peak compute
memory bandwidth
```

để ước lượng bottleneck.

Không coi đây là runtime semantics.

---

# 12. Scheduling Objective

AEP hỗ trợ mục tiêu:

```text
Latency
Throughput
Memory
Energy
Binary Size
Determinism
```

Một program có thể chọn execution profile.

---

# 13. Latency Profile

Ưu tiên:

```text
launch overhead ↓
synchronization ↓
tail latency ↓
```

Có thể không dùng GPU cho workload quá nhỏ.

---

# 14. Throughput Profile

Ưu tiên:

```text
batching
parallelism
GPU occupancy
pipeline
```

---

# 15. Memory Profile

Ưu tiên:

```text
peak memory ↓
buffer reuse ↑
recompute nếu rẻ
```

---

# 16. Energy Profile

Nếu target hỗ trợ telemetry/model:

```text
energy/op
memory energy
transfer energy
```

compiler có thể chọn execution plan phù hợp.

---

# 17. Binary Size Profile

Có thể ưu tiên:

```text
generic kernel
ít specialization
ít multiversion
```

thay vì generate hàng trăm specialized kernels.

---

# 18. Multi-objective Cost

Không phải lúc nào compiler có một optimum duy nhất.

AEP dùng:

```text
CostVector {
    latency
    throughput
    memory
    energy
    code_size
}
```

và execution policy quyết định weighting/constraints.

---

# 19. Hard Constraints vs Soft Objectives

Rất quan trọng.

Ví dụ:

```text
max_memory = 512 MB
```

là **hard constraint**.

Trong khi:

```text
prefer latency
```

là **soft objective**.

Compiler không được vượt hard constraint để đạt score tốt hơn.

---

# 20. Execution Contracts

AEP nhận:

```text
ExecutionContract
```

ví dụ:

```text
no_alloc
max_memory
deterministic
realtime
gpu_required
cpu_only
latency_bound
```

---

# 21. Realtime Contract

Nếu function yêu cầu realtime:

```text
@realtime
```

compiler phải kiểm tra:

```text
allocation
blocking
unbounded loop
unknown synchronization
unbounded recursion
dynamic dispatch
```

theo profile.

---

# 22. No-allocation Proof

Compiler cần chứng minh:

```text
NoAllocationProof
```

cho execution region.

Nếu không chứng minh được:

```text
compile error
```

trong strict realtime profile.

---

# 23. Bounded Execution

Có thể yêu cầu:

```text
bounded
```

Compiler kiểm tra hoặc conservatively reject:

```text
unbounded loop
unbounded queue
unbounded retry
```

nếu execution contract yêu cầu hard bound.

---

# 24. Blocking Analysis

AEP tích hợp Effect System:

```text
MayBlock
NonBlocking
AsyncSuspend
IO
```

Scheduler không được đưa blocking operation vào execution path yêu cầu nonblocking.

---

# 25. Async + CPU Parallelism

Ví dụ:

```text
async fn process()
```

bên trong có:

```text
parallel_for(...)
```

AEP phải tránh:

```text
task explosion
thread explosion
worker oversubscription
```

---

# 26. Oversubscription

Ví dụ:

```text
8 CPU workers
```

mỗi worker lại spawn:

```text
8 workers
```

Không nên thành 64 worker nếu không có lý do.

AEP có global worker/resource budget.

---

# 27. Parallel Budget

Execution context có thể có:

```text
ParallelBudget {
    max_workers
    max_nested_parallelism
    cpu_quota
    gpu_quota
}
```

Runtime có thể điều chỉnh physical scheduling mà không đổi semantics.

---

# 28. GPU Launch Budget

GPU kernel launch có overhead.

Compiler có thể fuse:

```text
kernel A
kernel B
kernel C
```

thành:

```text
kernel ABC
```

nếu cost model cho thấy có lợi.

---

# 29. Launch vs Fusion Tradeoff

Fusion có thể giảm launch nhưng tăng:

```text
register pressure
code size
occupancy loss
```

AEP quyết định dựa trên toàn graph.

---

# 30. Pipeline Scheduling

Ví dụ:

```text
CPU preprocess
      ↓
GPU inference
      ↓
CPU postprocess
```

AEP có thể pipeline:

```text
sample 1: CPU → GPU → CPU
sample 2:       CPU → GPU → CPU
sample 3:             CPU → GPU → CPU
```

---

# 31. Double Buffering

Compiler có thể tạo:

```text
Buffer A → GPU
Buffer B → CPU fill
```

sau đó swap.

Nếu storage/lifetime cho phép.

---

# 32. Triple Buffering

Đối với streaming workload:

```text
Input
Compute
Output
```

có thể dùng 3 buffer.

Không cần programmer tự quản lý.

---

# 33. Producer/Consumer Scheduling

AEP biểu diễn:

```text
Producer
   ↓
Buffer
   ↓
Consumer
```

và tối ưu:

- buffering;
- synchronization;
- locality;
- backpressure.

---

# 34. Backpressure

Async/channel pipeline phải có bounded capacity nếu declared.

Compiler/runtime không được âm thầm biến bounded queue thành unbounded queue vì có thể thay đổi memory semantics.

---

# 35. Memory Prefetch

Compiler có thể chèn:

```text
PREFETCH
```

nếu target hỗ trợ.

Đây là optimization, không phải semantic operation của source.

---

# 36. Cache Blocking

Loop:

```text
for i
 for j
  for k
```

có thể tile:

```text
for ii
 for jj
  for kk
```

để tăng locality.

Đã có Loop/Tensor/Linear Algebra optimizer, nhưng AEP quyết định global strategy.

---

# 37. Fusion Across Domain

Ví dụ:

```text
Vision:
resize
 ↓
normalize

Tensor:
 ↓
conv

AI:
 ↓
activation
```

AEP có thể nhận toàn bộ pipeline và fuse nếu representation cho phép.

---

# 38. Zero-copy Pipeline

Ví dụ:

```text
Camera buffer
 ↓
ImageView
 ↓
TensorView
 ↓
GPU kernel
```

Compiler phải ưu tiên giữ cùng storage.

Không tạo:

```text
Image copy
Tensor copy
GPU copy
```

nếu không cần.

---

# 39. Storage Domain Planning

AEP phải biết:

```text
HOST
DEVICE
SHARED
PINNED
MAPPED
LOCAL
EXTERNAL
```

và chọn transfer.

---

# 40. External Resource

Camera, file mapping, GPU surface, DMA buffer có thể là:

```text
ExternalStorage
```

với explicit lifetime/ownership contract.

---

# 41. Ownership-aware Scheduling

Nếu:

```text
producer owns buffer
```

và transfer ownership sang consumer:

```text
producer → consumer
```

thì không cần copy.

Đây là điểm Axiom có lợi thế lớn nhờ ownership semantics.

---

# 42. Move-based Dataflow

Ví dụ:

```text
buffer → GPU upload
```

có thể semantic là:

```text
MOVE buffer
```

thay vì:

```text
COPY buffer
```

nếu source không cần buffer nữa.

---

# 43. Read-only Sharing

Nếu nhiều consumers chỉ đọc:

```text
view<T>
```

có thể chia sẻ mà không copy.

---

# 44. Mutable Partitioning

Một tensor:

```text
T
```

có thể chia:

```text
mut_view<T>[0..N/2]
mut_view<T>[N/2..N]
```

nếu compiler chứng minh disjoint.

Cho phép parallel zero-copy.

---

# 45. Synchronization Elimination

Nếu ownership chứng minh:

```text
worker A owns region A
worker B owns region B
```

thì compiler có thể loại bỏ lock không cần thiết.

---

# 46. Lock Coarsening/Elimination

Nếu lock vẫn cần, compiler có thể tối ưu:

```text
lock
small operation
unlock
lock
small operation
unlock
```

thành một vùng lock lớn hơn nếu semantics và contention model cho phép.

Không được làm thay đổi fairness/observable synchronization nếu API contract coi đó là observable.

---

# 47. Atomic Optimization

Atomic có thể được loại bỏ nếu compiler chứng minh object:

```text
thread-local
```

và không escape.

Ví dụ:

```text
Atomic<i32>
```

nhưng object chỉ tồn tại trong một thread.

Machine code có thể dùng ordinary integer operations nếu memory semantics observable-equivalent.

---

# 48. Escape-aware Parallelization

Nếu object không escape parallel region:

```text
local accumulator
```

compiler có thể biến thành:

```text
worker-local accumulator
```

sau đó reduce.

---

# 49. Automatic Reduction Recognition

Loop:

```text
sum += x[i]
```

compiler nhận:

```text
Reduction
```

và có thể chọn:

```text
SIMD
parallel reduction
GPU reduction
```

theo numerical contract.

---

# 50. Automatic Device Offload

Với:

```text
@auto
```

hoặc execution policy tương đương, compiler có thể chọn GPU.

Nhưng phải có:

```text
GPU legality proof
transfer cost
kernel cost
```

---

# 51. Small Workload Avoidance

Nếu:

```text
N = 32
```

GPU launch có thể đắt hơn CPU.

AEP chọn CPU nếu contract cho phép.

---

# 52. Runtime Guarded Plan

Compiler có thể tạo:

```text
if N < threshold
    CPU
else
    GPU
```

threshold có thể đến từ cost model.

---

# 53. Multi-version Execution Plan

Có thể tạo:

```text
generic
AVX2
AVX512
GPU
```

và dispatch runtime.

---

# 54. Cache-aware Specialization

Nếu profile cho thấy:

```text
N = 1024
```

chiếm đa số workload, PGO có thể specialize execution plan cho N=1024.

Fallback vẫn phải tồn tại nếu input khác.

---

# 55. PGO Integration

AEP có thể nhận profile:

```text
ExecutionProfile
```

gồm:

```text
shape histogram
branch frequency
kernel timing
memory traffic
device utilization
cache misses
```

---

# 56. Online Adaptation

Runtime có thể cập nhật:

```text
KernelSelection
BatchSize
WorkerCount
```

nhưng chỉ trong những phạm vi contract cho phép.

---

# 57. Deterministic Scheduling

Một execution profile có thể yêu cầu deterministic scheduling.

Compiler/runtime khi đó không được dùng:

```text
unordered reduction
race-dependent scheduling
nondeterministic algorithm
```

nếu chúng ảnh hưởng observable result.

---

# 58. Debugging

AEP phải map được:

```text
Source
 ↓
HIR
 ↓
MIR
 ↓
Domain IR
 ↓
AEP Node
 ↓
Kernel
 ↓
Machine instruction
```

Debugger có thể trả lời:

> “Tại sao operation này chạy trên GPU?”

hoặc:

> “Tại sao tensor này bị copy?”

---

# 59. Optimization Explanation

Compiler diagnostic có thể hiển thị:

```text
Fusion:
  accepted

Reason:
  producer-consumer compatible
  same device
  same dtype
  no alias conflict
  numerical contract permits fusion

Estimated:
  -1 kernel launch
  -1 temporary buffer
```

Đây rất phù hợp với mục tiêu **AI-friendly compiler** của Axiom.

---

# 60. Global Optimization Database

Bổ sung:

```text id="1qgq9y"
ExecutionPlanDB
ExecutionNodeDB
ExecutionEdgeDB
ExecutionResourceDB
ExecutionConstraintDB
ExecutionObjectiveDB
ExecutionContractDB

ResourceDB
CpuResourceDB
CpuCoreDB
CpuCacheDB
CpuBandwidthDB
GpuResourceDB
GpuComputeUnitDB
GpuRegisterDB
GpuSharedMemoryDB
GpuBandwidthDB
GpuOccupancyDB
NumaResourceDB
InterconnectDB

SchedulingDB
ScheduleDB
ScheduleNodeDB
ScheduleEdgeDB
ScheduleDependencyDB
ScheduleBarrierDB
SchedulePipelineDB
ScheduleBufferingDB
SchedulePrefetchDB

ResourceBudgetDB
ParallelBudgetDB
GpuBudgetDB
MemoryBudgetDB
LatencyBudgetDB

MemoryPlanDB
StoragePlanDB
BufferPlanDB
BufferReuseDB
ZeroCopyDB
TransferPlanDB

FusionPlanDB
KernelPlanDB
KernelVariantDB
KernelDispatchDB

RealtimeDB
BoundedExecutionDB
NoAllocationDB
BlockingAnalysisDB

CostModelDB
CostVectorDB
RooflineDB
BandwidthModelDB
LatencyModelDB
EnergyModelDB

PGODB
ExecutionProfileDB
AdaptivePlanDB

DeterministicScheduleDB
GlobalOptimizationDB
GlobalOptimizationProofDB
GlobalVerificationDB
```

---

# 61. AEP operations

AEP không phải source-visible syntax.

Compiler IR operations:

```text id="0v8f4v"
PLAN_BEGIN
PLAN_END

RESOURCE_ACQUIRE
RESOURCE_RELEASE

DEVICE_ASSIGN
WORKER_ASSIGN
NUMA_ASSIGN

BUFFER_ASSIGN
BUFFER_REUSE
BUFFER_ALIAS

TRANSFER_SCHEDULE
TRANSFER_ELIMINATE

FUSE_GROUP
FUSE_SPLIT

KERNEL_ASSIGN
KERNEL_VARIANT
KERNEL_DISPATCH

PARALLEL_SCHEDULE
PARALLEL_PARTITION
PARALLEL_REDUCE

PIPELINE_BEGIN
PIPELINE_STAGE
PIPELINE_BUFFER
PIPELINE_END

PREFETCH
CACHE_TILE

SYNC_SCHEDULE
SYNC_ELIMINATE

SHAPE_GUARD
PROFILE_GUARD

PLAN_SELECT
PLAN_FALLBACK
```

---

# 62. Proof System

Mỗi transformation quan trọng cần proof:

```text
ExecutionEquivalenceProof
ResourceFeasibilityProof
MemoryPlanProof
BufferReuseProof
ZeroCopyProof
FusionProof
KernelSelectionProof
DevicePlacementProof
TransferEliminationProof
SynchronizationProof
ParallelScheduleProof
PipelineProof
RealtimeProof
BoundedExecutionProof
NoAllocationProof
DeterminismProof
CostModelProof
ProfileSpecializationProof
```

---

# 63. AEP Verification

Pipeline:

```text
Domain IR
    ↓
AEP construction
    ↓
Resource verification
    ↓
Memory verification
    ↓
Synchronization verification
    ↓
Numerical verification
    ↓
Execution equivalence
    ↓
Target lowering
```

AEP optimizer **không được phép tự coi optimization là đúng** chỉ vì cost model cho rằng nó tốt.

---

# 64. Global Invariants

### `AEXEC-01`
AEP phải preserve semantic behavior của source program.

### `AEXEC-02`
AEP không được trở thành runtime requirement nếu execution plan có thể compile tĩnh.

### `AEXEC-03`
Mọi resource assignment phải target-valid.

### `AEXEC-04`
Mọi memory plan phải preserve ownership/lifetime.

### `AEXEC-05`
Buffer reuse chỉ hợp lệ khi lifetimes không conflict.

### `AEXEC-06`
Zero-copy phải preserve storage provenance.

### `AEXEC-07`
Move-based transfer không được làm mất ownership semantics.

### `AEXEC-08`
Read-only sharing phải preserve capability semantics.

### `AEXEC-09`
Mutable partitioning phải có disjointness proof.

### `AEXEC-10`
Synchronization elimination phải có equivalence proof.

### `AEXEC-11`
Atomic elimination chỉ được phép khi memory semantics observable-equivalent.

### `AEXEC-12`
Parallel scheduling phải preserve data-race freedom.

### `AEXEC-13`
Parallel reduction phải preserve declared numerical contract.

### `AEXEC-14`
GPU offload phải có kernel legality proof.

### `AEXEC-15`
Device placement phải preserve storage and synchronization semantics.

### `AEXEC-16`
Transfer elimination phải chứng minh boundary không observable.

### `AEXEC-17`
Fusion phải preserve effects, aliasing và numerical semantics.

### `AEXEC-18`
Fusion không được vượt resource hard constraints.

### `AEXEC-19`
Kernel specialization phải có fallback hoặc complete input coverage.

### `AEXEC-20`
Shape guards phải preserve semantics cho mọi path.

### `AEXEC-21`
Pipeline scheduling phải preserve dependency edges.

### `AEXEC-22`
Double/triple buffering phải preserve ownership và lifetime.

### `AEXEC-23`
Backpressure semantics không được bị thay đổi bởi optimization.

### `AEXEC-24`
Realtime plan phải chứng minh declared realtime constraints.

### `AEXEC-25`
No-allocation profile phải chứng minh không có allocation path.

### `AEXEC-26`
Bounded profile phải chứng minh declared execution bounds.

### `AEXEC-27`
Deterministic profile phải preserve declared deterministic behavior.

### `AEXEC-28`
PGO optimization không được làm sai input ngoài profile.

### `AEXEC-29`
Cost model chỉ quyết định implementation, không quyết định semantics.

### `AEXEC-30`
Mọi global optimization phải có thể truy nguyên từ source → proof → generated execution.

---

# 65. Vị trí của BOOTSTRAP-387

Đây là tầng hợp nhất rất quan trọng:

```text
                         Axiom Source
                              │
             ┌────────────────┼────────────────┐
             │                │                │
           CPU              Tensor             AI
             │                │                │
           SIMD             GPU             Robotics
             │                │                │
             └────────────────┼────────────────┘
                              │
                             MIR
                              │
                     Domain-specific IR
                              │
                              ▼
                            AEP
                  ┌───────────┼───────────┐
                  │           │           │
               Memory      Compute     Scheduling
                  │           │           │
                  ├──── Device ──────────┤
                  │           │           │
                  └──── Synchronization ─┘
                              │
                       Global Cost Model
                              │
                              ▼
                     Execution Plan
                              │
              ┌───────────────┼────────────────┐
              │               │                │
             CPU             GPU          Distributed
              │               │                │
             SIMD          Kernels        Communication
              └───────────────┼────────────────┘
                              ▼
                         Machine IR
                              │
                         Native Code
```

**Điểm cốt lõi của 387:** từ đây compiler Axiom không còn có các optimizer hoạt động như những “ốc đảo” độc lập. Tensor, AI, SIMD, GPU, parallelism, async, memory và native backend đều có thể cung cấp thông tin cho **một execution planner chung**, trong khi **ownership + capability + numerical contract + effect system vẫn là lớp bảo đảm correctness**.

Điều này đặc biệt quan trọng với mục tiêu của Axiom: programmer viết computation ở mức cao, còn compiler có quyền thay đổi **cách thực thi** gần như hoàn toàn miễn là vẫn chứng minh được **semantic equivalence**.