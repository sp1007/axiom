# BOOTSTRAP-386 — Axiom Optimization, Automatic Differentiation Training & AI Execution Graph Engine

Sau **385 — Machine Learning, Neural Network & AI Compute**, bước tiếp theo nên đi sâu vào **AI execution engine**.

385 đã định nghĩa *ML semantics*. 386 tập trung vào vấn đề khó hơn:

> **Làm thế nào để compiler biến một model/training graph cấp cao thành execution plan tối ưu về compute, memory, communication và device — mà không biến Axiom thành một framework ML nặng nề?**

Đây là tầng đặc biệt quan trọng đối với mục tiêu của Axiom: **AI code phải có khả năng đạt hiệu năng native, nhưng programmer không phải tự quản lý kernel, buffer trung gian, memory planner hay GPU scheduling.**

---

# 1. Execution Graph

Model graph và execution graph không hoàn toàn giống nhau.

Ví dụ source:

```text
y = gelu(x @ w + b)
```

Model graph:

```text
MATMUL
   ↓
ADD
   ↓
GELU
```

Execution graph có thể là:

```text
FUSED_GEMM_BIAS_GELU
```

Do đó:

```text
Model Graph
      ↓
Semantic Graph
      ↓
Optimized Execution Graph
```

---

# 2. Execution Node

Mỗi node có:

```text
Operation
Input tensors
Output tensors
Shape
DType
Layout
Device
Storage
Effects
Numerical contract
Cost
Dependencies
```

Compiler không được chỉ nhìn operation name.

---

# 3. Tensor Lifetime

Execution graph phải xác định:

```text
created
used
last_use
released
```

Ví dụ:

```text
A → B → C
```

nếu A không còn được sử dụng sau B, storage của A có thể được tái sử dụng cho C.

---

# 4. Memory Planning

Compiler xây:

```text
TensorLiveRange
```

sau đó giải bài toán:

```text
logical tensors
       ↓
live ranges
       ↓
storage intervals
       ↓
buffer reuse
```

Mục tiêu là giảm peak memory.

---

# 5. Buffer Reuse

Nếu:

```text
A lifetime = [1,4]
B lifetime = [5,8]
```

thì:

```text
storage(A) == storage(B)
```

có thể hợp lệ nếu:

- layout tương thích;
- alignment tương thích;
- size đủ;
- device giống;
- access semantics không xung đột.

Không cần allocate/deallocate thật.

---

# 6. In-place Optimization

Ví dụ:

```text
y = relu(x)
```

có thể trở thành:

```text
relu_inplace(x)
```

chỉ khi:

```text
x
```

không còn cần sau operation và ownership/capability cho phép mutation.

---

# 7. Alias-aware Memory Planning

Không được chỉ dựa vào lifetime.

Compiler phải kết hợp:

```text
Ownership
Capability
Alias Analysis
Escape Analysis
```

Nếu hai tensor có thể alias:

```text
A ↔ B
```

thì không được tái sử dụng storage một cách không an toàn.

---

# 8. View Elimination

Ví dụ:

```text
x.transpose()
.slice()
.reshape()
```

có thể chỉ tạo metadata/view.

Nếu view không observable, compiler có thể trực tiếp tính địa chỉ.

---

# 9. Materialization Boundary

Compiler phải xác định khi nào expression cần materialize.

Ví dụ:

```text
y = (a + b) * c
```

có thể:

```text
load a
load b
add
load c
mul
store y
```

không cần tensor temporary.

---

# 10. Fusion

Các loại fusion:

```text
Elementwise Fusion
Producer-Consumer Fusion
Reduction Fusion
GEMM Epilogue Fusion
Attention Fusion
Convolution Fusion
Vertical Fusion
Horizontal Fusion
```

---

# 11. Fusion không được mù quáng

Fusion có thể làm tăng:

- register pressure;
- instruction count;
- code size;
- occupancy;
- synchronization cost.

Do đó fusion phải qua cost model.

---

# 12. Kernel Selection

Một operation có thể có nhiều implementation:

```text
CPU scalar
CPU SIMD
CPU multithread
GPU generic
GPU tiled
GPU tensor-core
external accelerator
```

Compiler chọn implementation dựa trên:

```text
shape
dtype
layout
device
alignment
hardware features
batch size
numerical contract
```

---

# 13. Kernel Specialization

Ví dụ:

```text
matmul<[1,4096,4096]>
```

có thể được specialize khác:

```text
matmul<[64,4096,4096]>
```

Không nhất thiết dùng một generic kernel.

---

# 14. Shape-specialized Compilation

Nếu shape compile-time known:

```text
Tensor<f16,[1,224,224,3]>
```

compiler có thể loại bỏ rất nhiều:

```text
dynamic shape checks
generic indexing
runtime dispatch
```

---

# 15. Partial Dynamic Shape

Nếu:

```text
Tensor<f16,[B,224,224,3]>
```

chỉ B dynamic.

Compiler vẫn specialize toàn bộ phần còn lại.

---

# 16. Shape Guards

Nếu runtime shape có thể phân nhánh:

```text
if B == 1
    specialized_kernel
else
    generic_kernel
```

Compiler có thể tạo:

```text
shape guard
      ↓
fast path
      ↓
fallback
```

---

# 17. Kernel Cache

Compilation của model lớn có thể rất tốn thời gian.

Compiler cần cache:

```text
KernelCacheKey
```

gồm:

```text
operation
shape
dtype
layout
device
ISA
compiler version
optimization profile
numerical contract
```

---

# 18. Persistent Compilation Artifact

Kernel đã compile có thể lưu trong artifact:

```text
.axobj
.axmodel
```

hoặc format tương lai.

Build sau không cần compile lại nếu semantic inputs không thay đổi.

---

# 19. Training Step Graph

Training:

```text
forward
   ↓
loss
   ↓
backward
   ↓
gradient accumulation
   ↓
optimizer
```

có thể được biểu diễn thành một execution graph duy nhất.

---

# 20. Forward/Backward Fusion

Ví dụ:

```text
forward operation
       ↓
saved activation
       ↓
backward
```

compiler có thể quyết định:

```text
save
vs
recompute
```

---

# 21. Activation Checkpointing

Không nhất thiết lưu mọi activation.

Compiler có thể chọn:

```text
store activation
```

hoặc:

```text
recompute activation
```

dựa trên:

```text
memory pressure
compute cost
device
```

---

# 22. Automatic Checkpoint Placement

Đây là optimization problem:

```text
minimize:
    peak memory + recompute cost
```

subject to:

```text
correctness
numerical contract
execution dependency
```

---

# 23. Gradient Rematerialization

Nếu:

```text
A
 ↓
B
 ↓
C
```

và backward cần A nhưng A không được lưu, compiler có thể recompute:

```text
A
 ↓
B
 ↓
C
```

tại backward.

Không cần programmer viết checkpoint thủ công.

---

# 24. Common Subexpression Across Training

Forward/backward graph có thể có computation trùng nhau.

Compiler có thể CSE nếu:

- pure;
- same inputs;
- same numerical contract;
- no observable effect.

---

# 25. Gradient Fusion

Ví dụ nhiều gradient:

```text
dW1
dW2
dW3
```

có thể fuse reduction nếu:

```text
layout
device
lifetime
numerical semantics
```

cho phép.

---

# 26. Gradient Bucketing

Distributed training có thể gom:

```text
grad1
grad2
grad3
...
```

thành communication bucket.

Mục tiêu:

```text
communication startup overhead ↓
overlap compute/communication ↑
```

---

# 27. Communication Scheduling

Compiler tạo dependency graph:

```text
compute
  ↓
gradient ready
  ↓
all-reduce
  ↓
optimizer
```

Có thể overlap các nhánh độc lập.

---

# 28. Distributed Execution Graph

Execution graph phải chứa:

```text
Device
Worker
Communication Edge
Synchronization Edge
Memory Edge
Compute Edge
```

Ví dụ:

```text
GPU0 compute
     ↓
AllReduce
 ↙       ↘
GPU1     GPU2
```

---

# 29. Device Placement

Compiler có thể phân tích:

```text
CPU
GPU0
GPU1
GPU2
```

và chọn placement.

Nhưng placement tự động chỉ được phép nếu semantics không yêu cầu một placement cụ thể.

---

# 30. Transfer Optimization

Compiler có thể biến:

```text
CPU → GPU
compute
GPU → CPU
```

thành:

```text
CPU → GPU
          ↘
          compute
          ↘
         output
```

và overlap transfer với compute.

---

# 31. Transfer Elimination

Nếu output cuối cùng vẫn ở GPU:

```text
GPU compute
→ CPU copy
→ GPU compute
```

có thể được biến thành:

```text
GPU compute
→ GPU compute
```

nếu CPU observation không tồn tại.

---

# 32. Unified Memory

Unified memory không nên trở thành semantic assumption.

Nó chỉ là một storage/placement strategy.

Axiom semantics vẫn phải phân biệt:

```text
logical tensor
```

với:

```text
physical storage location
```

---

# 33. CPU/GPU Graph Partitioning

Graph:

```text
A → B → C → D
```

có thể thành:

```text
CPU:
A

GPU:
B → C → D
```

nếu transfer cost hợp lý.

---

# 34. Auto Execution Policy

Compiler có thể lựa chọn:

```text
scalar
SIMD
parallel CPU
GPU
distributed
```

dựa trên cost model.

Nhưng:

```text
auto
```

không được tự ý thay đổi numerical semantics.

---

# 35. Numerical Contract

Execution optimizer phải biết:

```text
Strict
Relaxed
Approximate
```

Ví dụ fusion reduction trong Strict mode có thể bị cấm nếu làm thay đổi kết quả observable.

---

# 36. Deterministic Mode

Training có thể yêu cầu:

```text
deterministic
```

Khi đó compiler phải kiểm soát:

```text
reduction order
RNG
atomic accumulation
collective ordering
kernel algorithm
```

---

# 37. Fast Math

Một model có thể cho phép:

```text
fast_math
```

Compiler khi đó được phép:

- reassociate;
- approximate transcendental;
- FMA;
- reduced precision;
- algorithm substitution.

Nhưng phải nằm trong contract.

---

# 38. Automatic Batch Optimization

Nếu inference được gọi nhiều lần:

```text
infer(x1)
infer(x2)
infer(x3)
```

runtime/executor có thể batch:

```text
infer([x1,x2,x3])
```

chỉ khi API contract cho phép batching.

Đây là optimization ở execution layer, không phải thay đổi semantics của một lời gọi đơn lẻ.

---

# 39. Dynamic Batching

Serving workload có thể dùng:

```text
request queue
batch formation
deadline
priority
```

Đây là runtime capability, không phải Core.

---

# 40. Streaming Inference

Model graph có thể có state:

```text
input_t
state_t
    ↓
output_t
state_t+1
```

Compiler phải phân biệt:

```text
persistent state
temporary state
```

để không reset state giữa các lần gọi.

---

# 41. Stateful Model

Ví dụ RNN:

```text
h_next = model(x, h)
```

State ownership rõ ràng.

Không có hidden global model state.

---

# 42. KV Cache

Transformer inference có thể có:

```text
KVCache
```

được biểu diễn như explicit owned storage.

Compiler có thể:

- preallocate;
- resize;
- ring-buffer;
- shard;
- map GPU memory.

---

# 43. Memory Arena cho Model

Execution graph có thể dùng một execution arena:

```text
request
    ↓
temporary buffers
    ↓
release all
```

Không cần individual heap allocation cho từng tensor.

Đây đặc biệt phù hợp với triết lý Axiom:

> lifetime được compiler biết, storage strategy được compiler lựa chọn.

---

# 44. Static Memory Planning

Với graph static, compiler có thể tính trước:

```text
Buffer 0
Buffer 1
Buffer 2
...
```

và tạo một fixed memory plan.

Inference runtime khi đó gần như:

```text
input
→ kernels
→ output
```

không có allocator.

---

# 45. Realtime AI

Với model có static shape:

```text
RealtimeInference
```

có thể yêu cầu:

```text
no allocation
no blocking
bounded execution
fixed memory
```

Compiler kiểm chứng những constraint này.

---

# 46. AI Execution Contract

Compiler representation:

```text
AiExecutionContract {
    shape_policy
    numerical_policy
    memory_policy
    device_policy
    allocation_policy
    determinism_policy
    latency_policy
    parallel_policy
}
```

---

# 47. Cost Model

Cost model phải tính:

```text
FLOPs
memory traffic
cache
register pressure
SIMD width
GPU occupancy
kernel launch
PCIe transfer
NVLink/other interconnect
communication
allocation
synchronization
```

Không chỉ dùng FLOPs.

---

# 48. Multi-objective Optimization

Một execution plan có thể tối ưu theo:

```text
latency
throughput
memory
energy
binary size
determinism
```

Không có một cost function duy nhất cho mọi trường hợp.

---

# 49. User-selected Objective

Library/API có thể khai báo:

```text
latency
throughput
memory
balanced
```

Compiler dùng nó như optimization objective.

---

# 50. Profile-guided AI Optimization

PGO có thể thu thập:

```text
shape frequency
kernel time
memory bandwidth
cache misses
GPU occupancy
batch distribution
```

Sau đó specialize execution graph.

---

# 51. Runtime Adaptation

Dynamic model có thể có vài execution plan:

```text
small_batch_plan
medium_batch_plan
large_batch_plan
```

runtime chọn bằng guard.

---

# 52. Graph Compilation Boundary

Một graph có thể được compile thành:

```text
CompiledGraph
```

nhưng đây là library abstraction.

Không cần runtime VM.

---

# 53. Static Graph

Nếu toàn bộ model compile-time known:

```text
model → native code
```

Không cần graph interpreter.

---

# 54. Dynamic Graph

Nếu graph được tạo runtime:

```text
GraphBuilder
→ Graph
→ Compile
→ Execute
```

thì graph metadata tồn tại runtime.

Đây là explicit dynamic mode.

---

# 55. No Mandatory Graph Runtime

Điều này rất quan trọng.

Code:

```text
fn add(a: f32, b: f32) -> f32 {
    a + b
}
```

không được biến thành:

```text
ExprNode
GraphNode
RuntimeTensor
```

chỉ vì Axiom có AI engine.

Graph representation chỉ xuất hiện khi semantic/programming model yêu cầu hoặc compiler cần internal representation.

---

# 56. AI Compiler IR

Đề xuất thêm:

```text
AIR
```

**Axiom AI IR**

AIR nằm giữa Tensor/Expression semantics và execution lowering:

```text
Typed Tensor Graph
        ↓
       AIR
        ↓
Execution Graph
        ↓
Kernel IR
        ↓
GPU/SIMD/Machine IR
```

AIR giữ:

```text
shape
dtype
layout
device
storage
operation
gradient relation
numerical contract
```

nhưng không phải runtime object.

---

# 57. AIR Operations

```text
AI_INPUT
AI_OUTPUT
AI_PARAMETER

AI_ADD
AI_MUL
AI_MATMUL
AI_CONV
AI_REDUCE
AI_SOFTMAX
AI_NORMALIZE
AI_ATTENTION

AI_GRAD
AI_LOSS
AI_OPTIMIZE

AI_FUSE
AI_RESHAPE
AI_TRANSPOSE
AI_LAYOUT_CAST

AI_TRANSFER
AI_SHARD
AI_COLLECTIVE

AI_ALLOC
AI_FREE
AI_REUSE
```

---

# 58. AIR → MIR

Sau optimization:

```text
AIR
 ↓
memory planning
 ↓
fusion
 ↓
device placement
 ↓
kernel selection
 ↓
MIR
```

AIR không đi trực tiếp xuống machine code.

---

# 59. CompilerDB

Bổ sung:

```text
AIExecutionDB
AIExecutionGraphDB
AIExecutionNodeDB
AIExecutionEdgeDB
AIExecutionPlanDB
AIExecutionContractDB

AIMemoryPlanDB
AIMemoryRegionDB
AIBufferDB
AIBufferReuseDB
AITensorLifetimeDB
AIInplaceDB

AIFusionDB
AIFusionGroupDB
AIFusionCandidateDB
AIFusionProofDB

AIKernelDB
AIKernelVariantDB
AIKernelSelectionDB
AIKernelSpecializationDB
AIKernelCacheDB

AIShapeSpecializationDB
AIShapeGuardDB
AIShapeDispatchDB

AITrainingGraphDB
AIForwardGraphDB
AIBackwardGraphDB
AIActivationDB
AICheckpointDB
AIRematerializationDB
AIGradientScheduleDB

AIDistributedGraphDB
AIDevicePlacementDB
AIDevicePartitionDB
AICommunicationDB
AIBucketingDB
AICollectiveScheduleDB
AITransferDB
AITransferOptimizationDB

AIStreamingDB
AIStateDB
AIKVCacheDB
AIBatchingDB

AIRealtimeDB
AIDeterminismDB
AINumericalDB
AICostModelDB
AIPgoDB
AIRuntimePlanDB
AIDebugDB
AIProfileDB
AIProofDB
AIVerificationDB
```

---

# 60. AIR Proofs

```text
AIShapeProof
AIDTypeProof
AILayoutProof
AIDeviceProof
AIStorageProof

AITensorLifetimeProof
AIBufferReuseProof
AIAliasProof
AIInplaceProof

AIFusionProof
AIKernelSelectionProof
AIKernelSpecializationProof

AIGradientProof
AIRematerializationProof
AICheckpointProof

AITransferProof
AIDevicePlacementProof
AICommunicationProof
AICollectiveProof

AINumericalProof
AIDeterminismProof
AIMemoryProof
AIPerformanceProof

AIRealtimeProof
AIStaticMemoryProof
AINoAllocationProof
```

---

# 61. MIR additions

```text
AI_GRAPH_BEGIN
AI_GRAPH_END

AI_NODE
AI_EDGE

AI_MEMORY_PLAN_BEGIN
AI_MEMORY_PLAN_END

AI_BUFFER_ALLOC
AI_BUFFER_REUSE
AI_BUFFER_RELEASE

AI_FUSE_BEGIN
AI_FUSE_END

AI_KERNEL_SELECT
AI_KERNEL_SPECIALIZE
AI_KERNEL_CACHE

AI_SHAPE_GUARD
AI_SHAPE_DISPATCH

AI_CHECKPOINT
AI_RECOMPUTE

AI_DEVICE_PLACE
AI_DEVICE_TRANSFER

AI_COMM_BEGIN
AI_ALL_REDUCE
AI_ALL_GATHER
AI_REDUCE_SCATTER
AI_COMM_END

AI_BATCH
AI_UNBATCH

AI_STREAM_STATE
AI_KV_CACHE

AI_EXECUTION_PLAN
AI_EXECUTE
```

---

# 62. Invariants

### `AIAI-01`
AIR phải preserve semantics của typed tensor graph.

### `AIAI-02`
AIR không được trở thành runtime requirement của static AI code.

### `AIAI-03`
Shape information phải được preserve cho tới khi không còn cần thiết.

### `AIAI-04`
Static shape phải cho phép specialization.

### `AIAI-05`
Dynamic shape phải có validation hoặc guard tương ứng.

### `AIAI-06`
Memory planner phải preserve tensor lifetime.

### `AIAI-07`
Buffer reuse chỉ hợp lệ khi live ranges không xung đột.

### `AIAI-08`
Buffer reuse phải kiểm tra layout, alignment, device và storage domain.

### `AIAI-09`
In-place transformation phải preserve ownership/capability semantics.

### `AIAI-10`
Fusion phải preserve numerical semantics theo declared contract.

### `AIAI-11`
Fusion phải preserve observable effects.

### `AIAI-12`
Kernel selection phải preserve operation semantics.

### `AIAI-13`
Kernel specialization phải preserve generic fallback semantics.

### `AIAI-14`
Shape guards phải dispatch tới implementation semantic-equivalent.

### `AIAI-15`
Kernel cache identity phải bao gồm mọi semantic input ảnh hưởng machine result.

### `AIAI-16`
Backward graph phải preserve AD semantics.

### `AIAI-17`
Rematerialization phải preserve primal semantics.

### `AIAI-18`
Checkpoint elimination không được làm mất giá trị cần cho backward.

### `AIAI-19`
Gradient fusion phải preserve accumulation semantics.

### `AIAI-20`
Distributed execution phải preserve declared collective semantics.

### `AIAI-21`
Device transfer không được làm mất ownership/storage provenance.

### `AIAI-22`
Transfer elimination chỉ hợp lệ khi không có observable host/device boundary.

### `AIAI-23`
Device placement optimization phải preserve synchronization semantics.

### `AIAI-24`
Communication/computation overlap phải preserve happens-before.

### `AIAI-25`
Deterministic mode phải preserve declared deterministic contract.

### `AIAI-26`
Static-memory execution phải chứng minh mọi temporary storage.

### `AIAI-27`
Realtime/no-allocation profile phải được compiler verify.

### `AIAI-28`
Cost-model optimization không được thay đổi semantics.

### `AIAI-29`
PGO specialization phải preserve correctness của non-profiled inputs thông qua guard/fallback.

### `AIAI-30`
Nếu AI execution engine không được sử dụng, compiler không được tạo AI runtime dependency.

---

# 63. Kiến trúc sau BOOTSTRAP-386

Đến đây Axiom bắt đầu có một pipeline AI khá mạnh:

```text
                 Axiom Source
                      │
              Typed Tensor Ops
                      │
            Model / Training Graph
                      │
                      ▼
                    AIR
                      │
        ┌─────────────┼─────────────┐
        │             │             │
   Shape Solver    AD Graph    Numerical Contract
        │             │             │
        └─────────────┼─────────────┘
                      ▼
             Execution Graph
                      │
        ┌─────────────┼──────────────┐
        │             │              │
 Memory Planning   Fusion       Device Placement
        │             │              │
        └─────────────┼──────────────┘
                      ▼
                Kernel Selection
                      │
             ┌────────┴────────┐
             │                 │
           SIMD               GPU
             │                 │
             └────────┬────────┘
                      ▼
                     MIR
                      │
                Native Backend
```

Điểm đáng chú ý là **AIR không phải một “Python graph runtime”**. Nó là compiler IR có đủ thông tin để compiler thực hiện những tối ưu mà lập trình viên rất khó hoặc không nên tự làm: **memory planning, tensor reuse, fusion, rematerialization, kernel specialization, device placement và communication scheduling**.

Điều này rất phù hợp với triết lý cốt lõi của Axiom:

> **Lập trình viên mô tả computation; compiler chịu trách nhiệm biến computation đó thành execution plan hiệu quả.**