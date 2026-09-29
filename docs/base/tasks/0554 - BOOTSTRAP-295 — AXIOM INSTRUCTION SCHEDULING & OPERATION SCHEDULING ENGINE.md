# BOOTSTRAP-295 — AXIOM INSTRUCTION SCHEDULING & OPERATION SCHEDULING ENGINE
## FROZEN / COMPLETED

### 1. Mục tiêu

Sau `294`, Axiom đã tối ưu khá sâu ở mức:

```text
Scalar
Memory
Loop
Vector
Inlining
Specialization
Control Flow
```

Nhưng vẫn còn một vấn đề lớn trước khi xuống machine backend:

> **Cùng một tập operation, thứ tự thực thi khác nhau có thể tạo hiệu năng rất khác nhau trên CPU/GPU.**

Ví dụ:

```text
a = load(A)
b = load(B)
c = a + b
d = load(C)
e = d * 4
```

Một thứ tự naïve có thể tạo dependency chain:

```text
load A
   ↓
load B
   ↓
add
   ↓
...
```

Trong khi compiler có thể overlap các load độc lập:

```text
load A ─────────┐
                ├── add
load B ─────────┘

load C ── multiply
```

Mục tiêu `295` là xây **operation scheduler** để tận dụng:

- instruction-level parallelism;
- latency;
- throughput;
- dependency graph;
- memory latency;
- vector operations;
- register pressure;
- branch behavior;

mà **không thay đổi semantics**.

---

# 2. Vị trí

```text
Verified MIR
      ↓
OptIR
      ↓
Scalar
      ↓
Memory
      ↓
Loop
      ↓
Vector
      ↓
Inlining
      ↓
Specialization
      ↓
Control Flow
      ↓
Operation Scheduling       ← 295
      ↓
Target Lowering
      ↓
Machine IR
      ↓
Register Allocation
      ↓
Machine Scheduling
      ↓
Encoder
```

`295` là **target-aware nhưng chưa phải machine instruction scheduler hoàn chỉnh**.

---

# 3. Hai tầng scheduling

Axiom nên phân biệt:

```text
High-Level Operation Scheduling
```

và:

```text
Machine Instruction Scheduling
```

`295` phụ trách tầng đầu:

```text
OptIR operations
```

Backend sau này có thể schedule:

```text
MachineInstruction
```

Điều này tránh việc OptIR phụ thuộc x86/ARM/RISC-V.

---

# 4. Nguyên tắc

> **Scheduler chỉ được phép thay đổi thứ tự những operation mà semantic dependency graph cho phép reorder.**

Không bao giờ:

```text
cost model > semantic dependency
```

---

# 5. Scheduling Unit

```text
ScheduleRegion {
    function
    basic_block
    loop
    region_kind
    operations
    dependencies
    resources
    target_model
}
```

Các region:

```text
BasicBlock
ExtendedBasicBlock
LoopBody
SuperBlock
Trace
```

v1 ưu tiên:

```text
BasicBlock
LoopBody
```

sau đó mở rộng.

---

# 6. Operation Dependency Graph

```text
OperationGraph {
    nodes: Operation
    edges: DependencyEdge
}
```

Dependency edge:

```text
DependencyEdge {
    from
    to
    kind
    latency
    strength
}
```

---

# 7. Dependency Types

```text
DATA
MEMORY
CONTROL
EFFECT
ATOMIC
VOLATILE
PANIC
DROP
OWNERSHIP
CAPABILITY
ABI
```

---

# 8. Data Dependency

Ví dụ:

```text
a = x + y
b = a * 2
```

có:

```text
ADD
 ↓
MUL
```

Scheduler không thể đảo:

```text
MUL
ADD
```

---

# 9. Memory Dependency

Ví dụ:

```text
store(A, 1)
load(A)
```

phải giữ dependency.

Nếu:

```text
store(A, 1)
load(B)
```

và compiler chứng minh:

```text
A DISJOINT B
```

thì có thể reorder.

Đây là nơi scheduler sử dụng:

```text
282 Capability
289 MemorySSA
```

---

# 10. Unknown Alias

Nếu:

```text
A MAY_ALIAS B
```

hoặc:

```text
UNKNOWN
```

scheduler không được tự coi:

```text
NoDependency
```

Chỉ:

```text
NO_ALIAS
```

được phép loại memory dependency tương ứng.

---

# 11. Atomic

Ví dụ:

```text
atomic_store(A)
atomic_load(B)
```

không được scheduler đối xử như ordinary load/store.

Cần giữ:

```text
memory_order
synchronizes_with
happens_before
```

semantics.

---

# 12. Volatile

Volatile operations là scheduling barrier theo contract của Axiom.

Compiler không được reorder volatile operation như ordinary memory access.

---

# 13. IO / Foreign

Ví dụ:

```text
write_file()
print()
foreign_call()
```

phải giữ observable ordering theo effect contract.

---

# 14. Drop

Ví dụ:

```text
use(resource)
drop(resource)
```

Không được scheduler chuyển:

```text
drop(resource)
use(resource)
```

Ownership dependency là semantic dependency.

---

# 15. Capability Dependency

Ví dụ:

```text
write(mut_view<A>)
read(view<A>)
```

phải giữ conflict ordering.

Nếu:

```text
A DISJOINT B
```

thì:

```text
write(A)
read(B)
```

có thể độc lập.

---

# 16. Panic Dependency

Nếu:

```text
a = operation_that_may_panic()
b = observable_side_effect()
```

không thể tùy tiện đưa:

```text
b
```

trước `a`.

Panic là observable semantic effect.

---

# 17. Latency

Target model cung cấp:

```text
OperationCost {
    latency
    reciprocal_throughput
    resource_usage
}
```

Ví dụ:

```text
MUL
latency = 3
throughput = 1/cycle
```

chỉ là ví dụ model, không phải Axiom semantic constant.

---

# 18. Latency Hiding

Ví dụ:

```text
a = expensive_op(x)
b = independent_load(B)
c = use(a)
```

scheduler có thể:

```text
expensive_op(x)
load(B)
...
use(a)
```

thay vì chờ `a` ngay lập tức.

---

# 19. Critical Path

Scheduler phải tính:

```text
CriticalPathLength
```

trong dependency DAG.

Các operation nằm trên critical path có priority cao hơn.

---

# 20. Ready Set

Tại mỗi bước:

```text
ReadySet = operations
            whose dependencies
            are already scheduled
```

Scheduler chọn một operation từ:

```text
ReadySet
```

theo cost model.

---

# 21. Priority Model

Có thể dùng:

```text
Priority =
    CriticalPath
    + LatencyReduction
    + ResourceBalance
    + MemoryLatency
    + RegisterPressure
    + BranchPressure
```

Nhưng:

> Cost model chỉ chọn giữa các operation **đã hợp lệ để reorder**.

---

# 22. Register Pressure

Scheduling quá aggressive có thể tạo:

```text
r1 = ...
r2 = ...
r3 = ...
r4 = ...
r5 = ...
```

quá nhiều live values.

Kết quả:

```text
spill
reload
```

có thể khiến code chậm hơn.

Do đó scheduler phải dự đoán:

```text
RegisterPressure
```

---

# 23. Pressure-Aware Scheduling

Scheduler có thể chọn:

```text
Operation A
```

thay vì:

```text
Operation B
```

nếu:

```text
A:
  critical path benefit = high
  register pressure = low
```

so với:

```text
B:
  critical path benefit = medium
  register pressure = high
```

---

# 24. Memory Latency

Load có thể:

```text
L1
L2
L3
RAM
Unknown
```

Compiler thường không biết runtime cache state chính xác.

Do đó target model chỉ cung cấp estimated latency.

PGO có thể bổ sung profile.

Không được coi cache prediction là semantic fact.

---

# 25. Load Scheduling

Ví dụ:

```text
x = load(A)
y = load(B)
z = x + y
```

scheduler có thể phát hành:

```text
load(A)
load(B)
add
```

để overlap latency.

---

# 26. Store Scheduling

Store có thể gây:

```text
memory dependency
alias uncertainty
ordering constraints
```

nên conservative hơn load.

---

# 27. Store-to-Load

Ví dụ:

```text
store(A, x)
load(A)
```

MemorySSA có thể biết:

```text
load depends on store
```

Không được reorder.

---

# 28. Independent Memory Operations

Nếu:

```text
A NO_ALIAS B
```

thì:

```text
store(A)
load(B)
```

có thể được reorder nếu các effect khác cũng cho phép.

---

# 29. Loop Scheduling

Trong loop:

```text
for i {
    a = load(A[i])
    b = load(B[i])
    c = a + b
}
```

scheduler có thể tạo:

```text
load A[i]
load B[i]
load A[i+1]
load B[i+1]
add i
add i+1
```

nếu loop transformation/semantic legality cho phép.

Tuy nhiên đây phải phối hợp với:

```text
290 Loop
291 Vectorization
```

không được tự ý tạo loop transformation phá invariant của loop optimizer.

---

# 30. Software Pipelining

Có thể hỗ trợ framework:

```text
iteration N
iteration N+1
iteration N+2
```

được overlap.

Ví dụ:

```text
load N
compute N-1
store N-2
```

Đây là nền tảng cho:

```text
modulo scheduling
software pipelining
```

về sau.

---

# 31. Không đưa Software Pipelining thành Core Semantic

Đây là optimization.

Source:

```text
for ...
```

vẫn giữ semantics thông thường.

Compiler chỉ biến đổi machine execution.

---

# 32. Vector Operation Scheduling

Vector operation:

```text
vector_load
vector_mul
vector_add
vector_store
```

có resource/latency model riêng.

Ví dụ:

```text
vector_load
      ↓
vector_mul
      ↓
vector_add
```

Scheduler phải biết:

```text
vector register pressure
load/store bandwidth
execution ports/resources
```

nếu target model cung cấp.

---

# 33. Scalar + Vector Mixing

Không nên coi:

```text
scalar operation
vector operation
```

là hai thế giới hoàn toàn độc lập.

Có thể overlap:

```text
vector load
scalar address calculation
vector arithmetic
scalar loop control
```

nếu dependency cho phép.

---

# 34. Reduction

Ví dụ:

```text
sum += a[i]
```

vectorizer có thể tạo:

```text
vsum0
vsum1
vsum2
vsum3
```

Scheduler có thể interleave các reduction chains để giảm dependency depth.

Nhưng:

```text
strict FP
```

không được phép tự ý thay đổi reduction order nếu semantics không cho phép.

---

# 35. Integer Reduction

Với wrapping integer semantics:

```text
sum = wrapping_add(sum, x)
```

scheduler có thể reorder nếu semantic operation là associative trong mode tương ứng.

Nhưng checked arithmetic có thể có panic:

```text
checked_add
```

nên không được dùng cùng assumption.

---

# 36. Floating-Point Reduction

Strict:

```text
a + b + c
```

không được tùy tiện biến thành:

```text
(a + c) + b
```

chỉ vì scheduler thấy độc lập.

Fast-FP mới có thể cho phép reorder nếu contract quy định.

---

# 37. Branch Scheduling

Trong basic block:

```text
compare
branch
```

branch dependency không thể bị phá.

Nhưng các operation độc lập trước branch có thể được schedule để giảm branch latency.

---

# 38. Branch + Load

Ví dụ:

```text
if cond {
    use(load(A))
}
```

`294` có thể quyết định if-conversion.

Nếu vẫn còn branch, `295` chỉ được hoist load nếu:

```text
speculation proof
```

từ `294` cho phép.

Scheduler không tự tạo speculation proof.

---

# 39. Scheduler Không Được Tự Ý Speculate

Đây là invariant quan trọng:

```text
Scheduler
```

không được biến:

```text
conditional operation
```

thành:

```text
unconditional operation
```

trừ khi có:

```text
SpeculationProof
```

đã được xác lập bởi control/effect/memory analysis.

---

# 40. Target Model

```text
TargetScheduleModel {
    operation_cost
    resource_classes
    resource_capacity
    latency
    throughput
    register_cost
    branch_cost
    vector_cost
    memory_cost
}
```

Target model không chứa semantics.

---

# 41. CPU Target

Ví dụ model có thể mô tả:

```text
ALU
FPU
Load
Store
Branch
Vector
Special
```

nhưng Axiom optimizer không hard-code:

```text
x86 port 0
x86 port 1
```

ở semantic scheduler.

---

# 42. GPU Target

GPU scheduling model khác:

```text
warp/wave
occupancy
register pressure
shared memory
latency hiding
divergence
```

Do đó GPU scheduler phải dùng:

```text
GpuScheduleModel
```

riêng.

---

# 43. Occupancy

GPU:

```text
register usage ↑
```

có thể làm:

```text
occupancy ↓
```

Một transformation làm giảm instruction count nhưng tăng register pressure có thể không có lợi.

Cost model phải nhìn cả hai.

---

# 44. Async

Async state machine:

```text
poll
 ↓
state switch
 ↓
operation
 ↓
return Pending
```

Scheduler không được reorder qua:

```text
Suspend
```

nếu operation có observable state/capability/drop semantics.

---

# 45. Suspension Barrier

`Suspend` được coi là semantic boundary.

Các value:

```text
live across await
```

phải giữ đúng state-machine semantics.

---

# 46. Thread / Synchronization

Không được reorder qua:

```text
Mutex
Atomic
Fence
Channel
Join
```

nếu làm thay đổi:

```text
happens-before
synchronizes-with
```

---

# 47. Relaxed Atomic

Ngay cả:

```text
Relaxed
```

không có nghĩa:

```text
ordinary memory operation
```

Scheduler phải giữ atomicity và các semantics tương ứng.

---

# 48. FFI

Foreign call là scheduling barrier theo contract.

Nếu contract khai báo:

```text
pure
read-only
no-memory-effect
```

thì scheduler có thể có thêm freedom.

Nếu không có contract:

```text
conservative
```

---

# 49. Effect Summary Integration

Scheduler sử dụng:

```text
EffectSummary
```

để phân loại:

```text
Pure
Read
Write
Atomic
Volatile
IO
Foreign
Synchronize
Panic
```

Không xây một effect system thứ hai.

---

# 50. MemorySSA Integration

Scheduler query:

```text
MemorySSA
+
AliasInfo
+
Capability
```

để biết:

```text
Can A move before B?
```

Không tự xây MemoryDependencyGraph riêng biệt nếu có thể derive từ MemorySSA.

---

# 51. Ownership Integration

Scheduler không được reorder:

```text
Move
Drop
```

một cách làm thay đổi semantic lifetime.

Ví dụ:

```text
move(x)
use(x)
```

đã invalid.

Ownership verifier vẫn là authority.

---

# 52. Capability Integration

Nếu:

```text
mut_view<A>
```

đang active:

```text
write(A)
```

không thể reorder qua operation conflict với `A`.

---

# 53. Schedule Legality

```text
ScheduleLegality {
    data_dependency
    memory_dependency
    effect_dependency
    ownership_dependency
    capability_dependency
    control_dependency
    atomic_dependency
    panic_dependency
    async_dependency
    gpu_dependency
    abi_dependency
}
```

---

# 54. Scheduling Algorithm

v1:

```text
Build DAG
    ↓
Compute critical path
    ↓
Build ready set
    ↓
Score candidates
    ↓
Select operation
    ↓
Update dependencies
    ↓
Update register-pressure estimate
    ↓
Repeat
```

Đủ đơn giản để triển khai trước.

Sau đó có thể thêm:

```text
list scheduling
bottom-up scheduling
top-down scheduling
bidirectional scheduling
modulo scheduling
```

---

# 55. Determinism

Nếu hai operation có cùng score:

```text
tie-break
```

phải deterministic:

```text
OperationId
SourceOrder
stable priority
```

Không phụ thuộc:

```text
thread scheduling
hash-map iteration
worker count
```

---

# 56. Scheduling Cost

Cost model phải có:

```text
estimated_latency
estimated_throughput
critical_path
resource_pressure
register_pressure
code_size
branch_pressure
memory_pressure
```

Không dùng một scalar score duy nhất nếu có thể giữ vector cost nội bộ.

---

# 57. Register Pressure Feedback

Sau scheduling sơ bộ:

```text
pressure > threshold
```

scheduler có thể rollback và chọn thứ tự khác.

Không được đợi đến register allocator mới phát hiện mọi vấn đề.

---

# 58. Register Allocator Không Thuộc 295

`295` chỉ dự đoán:

```text
register pressure
```

Register allocation thật:

```text
virtual register
 ↓
liveness
 ↓
allocation
 ↓
spill
 ↓
physical register
```

sẽ thuộc backend/compiler backend task riêng.

---

# 59. Spill-Aware Feedback

Sau khi register allocation tồn tại, backend có thể yêu cầu:

```text
reschedule
```

nếu spill quá lớn.

Nhưng phải có boundary rõ:

```text
OptIR Scheduler
Machine Scheduler
```

không tạo vòng lặp vô hạn giữa hai subsystem.

---

# 60. Scheduling Barrier

Một số operation tạo barrier:

```text
volatile
foreign unknown
strong synchronization
opaque asm
certain atomic operations
suspend
```

Barrier semantics phải được khai báo explicit.

---

# 61. Inline Assembly

Nếu Axiom có:

```text
asm(...)
```

thì compiler phải biết:

```text
inputs
outputs
clobbers
memory
flags
ordering
```

Nếu thiếu contract:

```text
conservative barrier
```

---

# 62. No Reordering Across Observable Effects

Ví dụ:

```text
print("A")
print("B")
```

không được scheduler biến thành:

```text
print("B")
print("A")
```

chỉ vì cost model.

---

# 63. Exception/Panic Ordering

Ví dụ:

```text
a()
b()
```

nếu `a` có thể panic:

```text
b()
```

không được chạy trước `a()` nếu điều đó thay đổi observable behavior.

---

# 64. Scheduling + Inlining

Sau `292`:

```text
call foo
```

có thể biến thành body.

Scheduler nên chạy **sau** inline/specialization để thấy toàn bộ operations.

Điều này giúp:

```text
load
load
compute
```

được schedule cùng nhau thay vì bị chia bởi call boundary.

---

# 65. Scheduling + Specialization

`293` có thể chứng minh:

```text
mode == 0
```

Sau specialization, một số branch biến mất.

Scheduler chạy sau đó sẽ có DAG nhỏ hơn.

---

# 66. Scheduling + Control Optimization

`294` có thể biến:

```text
branch
```

thành:

```text
select
```

`295` sau đó có thể schedule:

```text
select
```

với các independent operations.

---

# 67. Scheduling + Vectorization

`291` tạo:

```text
VectorizationPlan
```

và vector transform tạo vector operations.

`295` có thể tối ưu:

```text
vector load
vector arithmetic
scalar control
reduction
```

nhưng không thay đổi vector legality.

---

# 68. Optimization Gateway

Mỗi scheduling transform phải có:

```text
SchedulingPlan {
    region
    original_order
    new_order
    dependencies
    required_proofs
    invalidated_analyses
}
```

Sau đó:

```text
Validate
Commit
```

---

# 69. Proof Dependencies

Ví dụ reorder:

```text
load(B)
```

trước:

```text
store(A)
```

cần proof:

```text
NoAlias(A, B)
```

Scheduling plan phải giữ reference đến proof đó.

Nếu proof stale:

```text
reject / rebuild
```

---

# 70. Diagnostics

Compiler có thể trả:

```text
Why wasn't operation moved?
```

Ví dụ:

```text
Cannot move Load(B) before Store(A)

Reason:
  Memory dependency exists
  Alias relation: MAY_ALIAS
  Required proof: NO_ALIAS(A, B)
```

Đây rất phù hợp với mục tiêu AI-native compiler của Axiom.

---

# 71. Module Structure

```text id="s1w8m4"
compiler/optimization/schedule/
├── mod.ax
│
├── graph/
│   ├── mod.ax
│   ├── dependency.ax
│   ├── dag.ax
│   ├── cycle.ax
│   └── region.ax
│
├── analysis/
│   ├── critical_path.ax
│   ├── latency.ax
│   ├── throughput.ax
│   ├── resource.ax
│   ├── register_pressure.ax
│   └── memory_pressure.ax
│
├── legality/
│   ├── data.ax
│   ├── memory.ax
│   ├── effect.ax
│   ├── ownership.ax
│   ├── capability.ax
│   ├── atomic.ax
│   ├── panic.ax
│   ├── async.ax
│   └── gpu.ax
│
├── algorithm/
│   ├── list.ax
│   ├── top_down.ax
│   ├── bottom_up.ax
│   ├── bidirectional.ax
│   └── modulo.ax
│
├── cost/
│   ├── model.ax
│   ├── cpu.ax
│   ├── gpu.ax
│   ├── pgo.ax
│   └── register_pressure.ax
│
├── transform/
│   ├── reorder.ax
│   ├── block.ax
│   ├── loop.ax
│   └── rollback.ax
│
├── target/
│   ├── schedule_model.ax
│   ├── resource.ax
│   └── operation_cost.ax
│
└── tests/
```

---

# 72. Implementation Order

```text
1. SchedulingRegion
2. DependencyEdge
3. Operation DAG
4. Data dependency extraction
5. Memory dependency integration
6. Effect dependency integration
7. Ownership dependency integration
8. Capability dependency integration
9. Atomic/volatile barriers
10. Panic dependency
11. Async dependency
12. GPU dependency
13. Critical-path analysis
14. Latency model
15. Throughput model
16. Resource model
17. Register-pressure estimation
18. Ready-set scheduler
19. Top-down scheduling
20. Bottom-up scheduling
21. Deterministic tie-breaking
22. Cost model
23. CPU target model
24. GPU target model
25. Loop scheduling
26. Vector operation scheduling
27. Reduction scheduling
28. Scheduling proof objects
29. OptimizationGateway integration
30. Analysis invalidation
31. Debug/source mapping
32. optimization remarks
33. PGO integration
34. adversarial tests
```

---

# 73. Adversarial Tests

### Test 1 — Independent arithmetic

```text
a = x + y
b = u * v
c = a + b
```

`a` và `b` có thể được schedule độc lập.

### Test 2 — Data dependency

```text
a = x + y
b = a * 2
```

không được reorder `b` trước `a`.

### Test 3 — Alias

```text
store(A)
load(B)
```

với `UNKNOWN` alias → không được tùy tiện reorder.

### Test 4 — Proven disjoint

```text
store(A)
load(B)
```

với `DISJOINT` → có thể reorder nếu các effect khác cho phép.

### Test 5 — Volatile

Không reorder volatile operations.

### Test 6 — Atomic

Giữ ordering semantics.

### Test 7 — Panic

Không chạy operation observable trước một operation có thể panic nếu thứ tự thay đổi semantics.

### Test 8 — Drop

Không reorder qua semantic Drop boundary sai cách.

### Test 9 — Capability

Không tạo conflicting mutable accesses.

### Test 10 — Register pressure

Scheduler không được tối ưu latency bằng cách tạo spill explosion.

### Test 11 — Strict FP

Không reorder phép toán FP nếu thay đổi kết quả observable.

### Test 12 — Wrapping arithmetic

Không dùng associativity không hợp lệ.

### Test 13 — Vector reduction

Không đổi reduction order trong strict FP.

### Test 14 — Async

Không reorder qua `Suspend` sai semantics.

### Test 15 — GPU

Scheduler CPU model không được áp dụng cho GPU.

### Test 16 — FFI

Unknown foreign call giữ conservative ordering.

### Test 17 — Determinism

Kết quả giống nhau với:

```text
1 worker
2 workers
8 workers
```

### Test 18 — Proof invalidation

Nếu alias proof bị invalidated, schedule phụ thuộc proof đó phải bị hủy/recompute.

---

# 74. Frozen Invariants

### `ASCHED-20..100`

```text
ASCHED-20 — Scheduling Preserves Axiom Observable Semantics
ASCHED-21 — Scheduling Operates Only On Valid IR
ASCHED-22 — Scheduling May Reorder Only Independent Operations
ASCHED-23 — Data Dependencies Must Be Preserved
ASCHED-24 — Memory Dependencies Must Be Preserved
ASCHED-25 — Effect Dependencies Must Be Preserved
ASCHED-26 — Ownership Dependencies Must Be Preserved
ASCHED-27 — Capability Dependencies Must Be Preserved
ASCHED-28 — Atomic Semantics Must Be Preserved
ASCHED-29 — Volatile Semantics Must Be Preserved
ASCHED-30 — Synchronization Ordering Must Be Preserved
ASCHED-31 — Panic Ordering Must Be Preserved
ASCHED-32 — Drop Ordering Must Be Preserved Where Observable
ASCHED-33 — Async Suspension Boundaries Must Be Preserved
ASCHED-34 — GPU Execution Semantics Must Be Preserved
ASCHED-35 — Foreign Call Contracts Must Be Preserved
ASCHED-36 — UNKNOWN Alias Must Not Be Treated As NO_ALIAS
ASCHED-37 — NO_ALIAS Requires A Valid Proof
ASCHED-38 — Speculative Motion Requires A Valid Speculation Proof
ASCHED-39 — Scheduler Must Not Invent Semantic Proofs
ASCHED-40 — Cost Models Cannot Override Legality
ASCHED-41 — Latency Is An Optimization Property
ASCHED-42 — Throughput Is An Optimization Property
ASCHED-43 — Resource Models Are Target-Specific
ASCHED-44 — Target Models Must Not Define Language Semantics
ASCHED-45 — Register Pressure Must Be Considered
ASCHED-46 — Scheduling Must Not Require A Particular Register Allocator
ASCHED-47 — Scheduling Must Not Depend On Undefined Behavior
ASCHED-48 — Strict FP Ordering Must Be Preserved
ASCHED-49 — Fast-FP Reordering Requires Explicit Fast-FP Semantics
ASCHED-50 — Integer Overflow Semantics Must Be Preserved
ASCHED-51 — Wrapping Arithmetic Must Not Use Invalid Mathematical Assumptions
ASCHED-52 — Checked Arithmetic Failure Semantics Must Be Preserved
ASCHED-53 — Saturating Arithmetic Must Be Preserved
ASCHED-54 — Vector Operation Semantics Must Be Preserved
ASCHED-55 — Vector Reduction Ordering Must Respect FP Semantics
ASCHED-56 — Loop-Carried Dependencies Must Be Preserved
ASCHED-57 — Software Pipelining Must Preserve Loop Semantics
ASCHED-58 — Scheduling Must Respect Existing Vectorization Legality
ASCHED-59 — Scheduling Must Not Create New Safe Aliasing
ASCHED-60 — Scheduling Must Respect Capability Provenance
ASCHED-61 — Scheduling Must Respect Stable-Address Contracts
ASCHED-62 — Scheduling Must Respect Logical Identity
ASCHED-63 — Scheduling Must Respect ABI Boundaries
ASCHED-64 — Scheduling Must Respect Async State Contracts
ASCHED-65 — Scheduling Must Respect GPU Storage Domains
ASCHED-66 — Scheduling Must Respect GPU Execution Domains
ASCHED-67 — Scheduling Regions Must Have Explicit Boundaries
ASCHED-68 — Suspend Is A Semantic Scheduling Boundary
ASCHED-69 — Unknown Foreign Calls Are Conservative Scheduling Barriers
ASCHED-70 — Unknown Inline Assembly Is Conservative
ASCHED-71 — Scheduling Must Be Deterministic
ASCHED-72 — Worker Count Must Not Change Semantic Scheduling Legality
ASCHED-73 — Profile Data May Affect Profitability Only
ASCHED-74 — Cache Presence Must Not Change Correctness
ASCHED-75 — Scheduling Must Use OptimizationGateway
ASCHED-76 — Scheduling Plans Must Record Required Proofs
ASCHED-77 — Stale Proofs Cannot Authorize Scheduling
ASCHED-78 — Invalidated Analyses Must Not Be Reused
ASCHED-79 — Scheduling Transformations Must Be Transactional
ASCHED-80 — Failed Scheduling Must Preserve Valid Prior IR
ASCHED-81 — Scheduling Must Preserve Source Provenance
ASCHED-82 — Debug Mapping Must Survive Scheduling
ASCHED-83 — Scheduling Decisions Must Be Explainable
ASCHED-84 — Scheduling Must Not Force A Specific ISA
ASCHED-85 — CPU And GPU Scheduling Models Must Remain Distinct
ASCHED-86 — Register Pressure Must Not Override Semantic Legality
ASCHED-87 — Memory Latency Estimates Are Not Semantic Facts
ASCHED-88 — Branch Prediction Data Is Not Semantic
ASCHED-89 — Scheduling Is Optional
ASCHED-90 — Failure To Schedule Optimally Is Never A Correctness Error
ASCHED-91 — Scheduling Must Integrate With MemorySSA
ASCHED-92 — Scheduling Must Integrate With Alias Analysis
ASCHED-93 — Scheduling Must Integrate With Effect Analysis
ASCHED-94 — Scheduling Must Integrate With Ownership Verification
ASCHED-95 — Scheduling Must Integrate With Capability Verification
ASCHED-96 — Scheduling Must Integrate With Loop Analysis
ASCHED-97 — Scheduling Must Integrate With Vectorization
ASCHED-98 — Scheduling Must Integrate With Inlining/Specialization
ASCHED-99 — Scheduling Must Not Change Program Semantics
ASCHED-100 — Scheduling Is A Physical Performance Optimization, Not A Language Semantic
```

---

## 75. Vị trí mới của compiler

Axiom hiện có chuỗi tối ưu hóa ngày càng gần tới backend:

```text
                Verified MIR
                     │
                     ▼
                  OptIR
                     │
       ┌─────────────┼─────────────┐
       ▼             ▼             ▼
    Scalar        Memory          CFG
       │             │             │
       └──────┬──────┴──────┬──────┘
              ▼             ▼
            Loop       Specialization
              │             │
              └──────┬──────┘
                     ▼
                 Inlining
                     │
                     ▼
              Vectorization
                     │
                     ▼
              Control Flow
                     │
                     ▼
              Scheduling
                     │
                     ▼
             Target Lowering
```

Điểm quan trọng của `295` là từ đây compiler bắt đầu chuyển từ:

> **“Chương trình này nên được biến đổi semantic như thế nào?”**

sang:

> **“Các operation đã được chứng minh hợp lệ này nên được tổ chức thực thi thế nào để CPU/GPU khai thác tối đa phần cứng?”**

Đây là ranh giới rất quan trọng trước khi bước vào **machine-level backend, register allocation và instruction selection**.

**BOOTSTRAP-295 hoàn tất và được đóng băng.**