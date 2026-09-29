# BOOTSTRAP-365 — Axiom Parallelism, Work Scheduling & Data-Parallel Execution Engine

Sau 364, Axiom đã định nghĩa **execution resource**. Bước tiếp theo hợp lý là định nghĩa **parallelism ở cấp ngôn ngữ/compiler**: khi programmer muốn xử lý hàng triệu phần tử, compiler/runtime phân chia công việc thế nào, khi nào dùng thread, worker, SIMD, GPU, và quan trọng nhất là làm sao **một abstraction parallel có thể được tối ưu thành loop tuần tự, SIMD, thread pool hoặc GPU kernel** mà không thay đổi semantics.

Đây là lớp rất quan trọng cho mục tiêu Axiom: **CPU/GPU + AI/HPC + hiệu năng C/C++ nhưng syntax đơn giản**.

---

## 1. Phân biệt concurrency và parallelism

Axiom phải tách:

```text
Concurrency
    = nhiều computation có thể tiến triển độc lập

Parallelism
    = nhiều computation thực sự được thực thi đồng thời
```

Ví dụ:

```text
async task A
async task B
```

có thể concurrent nhưng chỉ chạy trên một CPU thread.

Ngược lại:

```text
parallel_for(...)
```

mục tiêu là parallel execution.

Compiler không được suy luận:

```text
async == parallel
```

---

# 2. Parallel computation là semantic operation

Axiom cần một abstraction compiler hiểu:

```text
parallel_for
parallel_reduce
parallel_map
parallel_scan
parallel_sort
```

nhưng **không nhất thiết tất cả phải là Core syntax**.

Triết lý:

> Parallelism là semantic capability; syntax có thể nằm trong standard library, nhưng compiler phải nhận diện và tối ưu được các primitive chuẩn.

Ví dụ:

```axiom
parallel_for(0..n, fn(i) {
    out[i] = a[i] + b[i]
})
```

Compiler có thể biến thành:

```text
serial loop
SIMD loop
CPU worker pool
GPU kernel
```

---

# 3. Parallel region

Compiler biểu diễn:

```text
ParallelRegion {
    RegionId
    iteration_space
    body
    captures
    reduction
    dependencies
    execution_policy
}
```

Ví dụ:

```text
for i in 0..n
    out[i] = a[i] + b[i]
```

có iteration domain:

```text
I = {0,1,2,...,n-1}
```

---

# 4. Data independence

Điều quan trọng nhất là xác định:

```text
iteration i
```

có thể chạy độc lập với:

```text
iteration j
```

hay không.

Compiler sử dụng:

- ownership
- capability
- region analysis
- alias analysis
- memory dependence
- effect system

đã có từ các task trước.

---

# 5. Ví dụ hoàn toàn độc lập

```axiom
parallel_for(0..n, fn(i) {
    out[i] = a[i] * 2
})
```

Compiler chứng minh:

```text
write(out[i])
```

và:

```text
write(out[j])
```

disjoint khi:

```text
i != j
```

→ parallel legal.

---

# 6. Ví dụ có race

```axiom
var sum = 0

parallel_for(0..n, fn(i) {
    sum += a[i]
})
```

Các iteration cùng:

```text
READ/WRITE sum
```

→ conflict.

Compiler không tự biến thành atomic:

```text
sum.atomic_add(...)
```

vì đó là thay đổi semantics/performance.

Thay vào đó nhận diện:

```text
Reduction(sum, +)
```

nếu semantics cho phép.

---

# 7. Reduction là semantic primitive

Ví dụ:

```axiom
parallel_reduce(
    0..n,
    init = 0,
    combine = +,
    body = fn(i) => a[i]
)
```

Compiler hiểu:

```text
partial results
      ↓
tree reduction
      ↓
final result
```

Có thể lower thành:

```text
serial
SIMD
thread tree
GPU reduction
```

---

# 8. Reduction operator requirements

Một reduction operator nên có contract:

```text
ReductionOp {
    identity
    combine
    associative
    commutative
}
```

Nếu chỉ associative:

```text
(a+b)+c == a+(b+c)
```

nhưng không commutative:

```text
a+b != b+a
```

thì scheduler vẫn phải giữ ordering phù hợp.

Nếu floating point:

```text
a + b + c
```

không hoàn toàn associative.

Compiler **không được mặc định** coi floating-point `+` là mathematically associative.

---

# 9. Fast math là policy riêng

Có thể có:

```text
@fast_math
```

hoặc execution policy tương tự.

Khi programmer explicit cho phép relaxed numerical semantics, compiler mới được:

```text
reassociate
vectorize
parallel_reduce
fuse
```

theo contract đó.

Không tự phá IEEE semantics chỉ vì muốn nhanh.

---

# 10. Map

```axiom
parallel_map(input, fn(x) => ...)
```

semantic:

```text
one output
per input element
```

Nếu body không có side effect observable và output độc lập:

```text
map → SIMD → GPU
```

là hợp lệ.

---

# 11. Filter

```text
parallel_filter
```

khó hơn vì output length thay đổi.

Compiler có thể dùng:

```text
predicate
 ↓
prefix sum
 ↓
scatter
```

hoặc sequential fallback.

Đây là ví dụ:

> High-level parallel abstraction không cần programmer biết thuật toán machine-level.

---

# 12. Scan

```text
parallel_scan
```

có dependency giữa prefix values:

```text
x0
x0+x1
x0+x1+x2
...
```

Compiler không thể xử lý như independent map.

Nhưng có parallel scan algorithms.

Do đó compiler cần nhận diện:

```text
ScanPattern
```

riêng.

---

# 13. Chunking

Parallel iteration space:

```text
0..N
```

có thể chia:

```text
chunk 0
chunk 1
chunk 2
...
```

Scheduler có thể chọn:

```text
static
dynamic
guided
work-stealing
```

đây là **execution policy**, không phải source semantics.

---

# 14. Static scheduling

Ví dụ:

```text
N = 1,000,000
workers = 8
```

chia:

```text
worker 0 → [0,125000)
worker 1 → [125000,250000)
...
```

Ưu:

- predictable
- ít scheduling overhead
- cache locality tốt

Nhược:

- workload imbalance.

---

# 15. Dynamic scheduling

Workers lấy chunk khi hoàn thành.

Tốt với:

```text
variable-cost iterations
```

nhưng có scheduling overhead.

Compiler/runtime chọn tùy cost model.

---

# 16. Work stealing

Executor có:

```text
local deque
```

worker khác có thể steal task.

Đây là runtime implementation.

Không thay đổi semantic ordering trừ khi programmer yêu cầu deterministic order.

---

# 17. Determinism

Axiom phải phân biệt:

```text
Deterministic computation
```

và:

```text
Nondeterministic scheduling
```

Parallel execution không được tự động làm mất deterministic semantics.

Nếu operation vốn deterministic:

```text
parallel_map(...)
```

thì kết quả phải deterministic.

---

# 18. Ordered side effects

Ví dụ:

```axiom
parallel_for(0..n, fn(i) {
    print(i)
})
```

`print` là side effect.

Nếu parallel primitive không định nghĩa ordering:

```text
output order
```

không được giả định.

Compiler phải:

- reject,
- serialize,
- hoặc yêu cầu explicit unordered execution.

Không âm thầm hứa thứ tự.

---

# 19. Parallel execution policy

Axiom có thể có:

```text
ExecutionPolicy {
    sequential
    simd
    parallel
    gpu
    auto
}
```

Ví dụ:

```axiom
for_each(data, body, policy = auto)
```

`auto` cho phép compiler chọn.

---

# 20. `auto` không được thay đổi semantics

Nếu:

```text
auto
```

chọn:

```text
serial
SIMD
threads
GPU
```

kết quả observable phải phù hợp semantic contract.

Nếu operation phụ thuộc:

```text
thread_id
timing
unordered side effects
```

thì compiler không thể tùy ý chuyển execution domain.

---

# 21. SIMD là một loại parallelism

Axiom phải coi:

```text
SIMD
```

là execution domain/subdomain chứ không phải một API hoàn toàn tách biệt.

Ví dụ:

```axiom
parallel_for(0..n, fn(i) {
    out[i] = a[i] + b[i]
})
```

có thể lower:

```text
scalar
    ↓
vector width 4
vector width 8
vector width 16
```

tùy CPU.

---

# 22. Vectorization legality

Compiler kiểm tra:

```text
memory dependence
aliasing
control flow
reduction
exceptions/panic
volatile
atomic
function calls
```

Nếu loop có:

```text
volatile_store
```

không được vectorize tùy tiện.

Nếu có atomic:

```text
atomic_add
```

phải giữ atomic semantics.

---

# 23. GPU lowering

Một parallel region có thể:

```text
CPU
 ↓
GPU
```

nếu:

- body GPU-legal;
- captures nằm trong valid storage domain;
- function calls GPU-legal;
- no host-only effects;
- synchronization hợp lệ;
- data transfer contract tồn tại.

Compiler tạo:

```text
GPUKernelRegion
```

rồi chuyển sang GPU backend.

---

# 24. CPU/GPU unified semantic source

Ví dụ:

```axiom
parallel_for(0..n, fn(i) {
    out[i] = relu(a[i])
})
```

không cần:

```text
CUDA code
OpenCL code
CPU code
```

ở source level.

Compiler có thể chọn backend.

Đây là một trong những lợi thế quan trọng của Axiom cho AI/HPC.

---

# 25. Nhưng GPU không được là “magic CPU”

Nếu function:

```axiom
fn body(i) {
    read_file()
}
```

thì:

```text
policy = gpu
```

phải bị reject.

Compiler không được cố “dịch” filesystem API thành GPU code.

---

# 26. Capture semantics

Parallel closure capture vẫn tuân theo 356.

Ví dụ:

```axiom
let scale = 2

parallel_for(0..n, fn(i) {
    out[i] = a[i] * scale
})
```

`scale` immutable:

```text
READ capture
```

có thể replicate.

Nhưng:

```axiom
var counter = 0

parallel_for(...) {
    counter += 1
}
```

là mutable shared capture → conflict.

---

# 27. Parallel ownership transfer

Có thể chuyển ownership vào mỗi worker nếu partition được.

Ví dụ:

```text
buffer
 ↓
partition
 ↓
worker A owns chunk A
worker B owns chunk B
```

Đây là cách Axiom tránh lock.

---

# 28. Partition type

Compiler internal:

```text
Partition<T> {
    source_region
    partitions[]
    disjoint_proof
}
```

Nếu chứng minh:

```text
partition[i] ∩ partition[j] = ∅
```

thì mỗi worker có thể nhận:

```text
mut_view<T>
```

riêng.

---

# 29. Zero-copy parallelism

Mục tiêu:

```text
parallel_for(buffer)
```

không tạo:

```text
N copies
```

Thay vào đó:

```text
owner
 ├── view chunk A
 ├── view chunk B
 ├── view chunk C
 └── ...
```

và compiler proof đảm bảo disjointness.

---

# 30. False sharing

Ownership có thể chứng minh logical disjoint:

```text
a[0]
a[1]
```

nhưng hardware vẫn có thể đặt chúng cùng cache line.

Do đó:

```text
logical independence
```

không đồng nghĩa:

```text
hardware performance independence
```

Compiler cost model có thể padding/alignment khi profitable.

---

# 31. Cache-aware partitioning

Compiler/runtime có thể dùng:

```text
CacheLineSize
NUMANode
MemoryLocality
WorkingSet
```

để chọn chunk.

Đây là optimization, không semantic requirement.

---

# 32. Parallel nested execution

Ví dụ:

```text
parallel_for A
    parallel_for B
```

không được mặc định tạo:

```text
threads × threads
```

vì dễ oversubscription.

Executor có thể:

```text
flatten
fuse
reuse worker pool
```

nếu semantics giữ nguyên.

---

# 33. Parallel region fusion

Hai loops:

```axiom
parallel_for(...) {
    b[i] = f(a[i])
}

parallel_for(...) {
    c[i] = g(b[i])
}
```

có thể fuse thành:

```text
parallel_for(...) {
    let t = f(a[i])
    c[i] = g(t)
}
```

nếu:

- không có observable ordering;
- no conflicting side effects;
- memory semantics giữ nguyên.

Đây là một optimization rất quan trọng cho GPU và cache.

---

# 34. Parallel region tiling

Compiler có thể biến:

```text
for i
    for j
        ...
```

thành:

```text
tile(i,j)
```

để cải thiện:

- cache locality
- vectorization
- GPU shared memory
- NUMA locality.

Source semantics không thay đổi.

---

# 35. Reduction tree

Ví dụ:

```text
[a,b,c,d,e,f,g,h]
```

có thể:

```text
a+b
c+d
e+f
g+h

(a+b)+(c+d)
(e+f)+(g+h)

final
```

Compiler cần lưu:

```text
ReductionTree
```

để debug/profiling và numerical verification.

---

# 36. Exception/Panic trong parallel region

Axiom không dùng C++ exception propagation ngầm.

Nếu worker panic:

```text
worker panic
```

parallel operation phải có policy:

```text
ABORT
CANCEL_REMAINING
COLLECT
PROPAGATE
```

Default library policy có thể là:

```text
PROPAGATE + CANCEL_REMAINING
```

nhưng semantic policy phải explicit trong API contract.

---

# 37. Cancellation

Nếu một parallel region bị cancel:

```text
cancel
 ↓
workers observe cancellation
 ↓
stop at safe points
 ↓
cleanup
```

Không kill worker thread giữa instruction.

---

# 38. Resource cleanup

Parallel closure có:

```text
capture
```

và có thể:

```text
Drop
```

Mỗi worker instance phải cleanup đúng ownership.

Compiler không được tạo double drop nếu closure được replicated.

---

# 39. Worker-local state

Compiler có thể nhận diện:

```text
worker-local
```

temporary.

Ví dụ reduction partial:

```text
partial_sum
```

mỗi worker có một instance.

Không cần:

```text
Atomic
Mutex
```

cho worker-local state.

---

# 40. Parallel memory proof

Mỗi parallel region tạo:

```text
ParallelProof
```

gồm:

```text
IterationSpace
AccessSummary
RegionRelations
CrossIterationDependencies
ReductionFacts
SynchronizationFacts
ExecutionPolicy
```

Compiler kết luận:

```text
PARALLEL_SAFE
SERIAL_ONLY
REQUIRES_SYNC
REQUIRES_REDUCTION
GPU_ILLEGAL
UNKNOWN
```

---

# 41. Cost model

Parallelization không phải lúc nào cũng có lợi.

Compiler tính:

```text
estimated_work
estimated_memory_traffic
spawn_cost
scheduling_cost
vector_width
cache_cost
NUMA_cost
GPU_transfer_cost
```

Ví dụ loop chỉ:

```text
N = 10
```

thì:

```text
serial
```

có thể nhanh hơn.

Loop lớn:

```text
N = 100,000,000
```

có thể chọn:

```text
SIMD + threads
```

---

# 42. Adaptive execution

`auto` policy có thể chọn runtime strategy:

```text
small N → serial
medium N → SIMD
large N → threads + SIMD
huge GPU-friendly N → GPU
```

Nếu threshold phụ thuộc runtime data, decision có thể được runtime specialization.

---

# 43. Profile-guided parallelism

PGO có thể cung cấp:

```text
average N
branch probability
memory bandwidth
worker scaling
GPU transfer cost
```

cho Parallel Cost Model.

Không thay đổi source semantics.

---

# 44. Deterministic scheduler

Testing profile có thể yêu cầu:

```text
DeterministicParallelExecutor
```

để tái hiện:

```text
task ordering
chunk ordering
worker scheduling
```

nhất có thể.

Đây là công cụ testing, không phải requirement production.

---

# 45. Parallel debugging

Debugger phải biết:

```text
ParallelRegionId
IterationId
WorkerId
ThreadId
TaskId
```

Ví dụ:

```text
worker 3
parallel region #17
iteration 48291
```

để debug.

---

# 46. CompilerDB additions

365 bổ sung:

```text
ParallelDB
ParallelRegionDB
IterationSpaceDB
ParallelBodyDB
ParallelCaptureDB
ParallelAccessDB
ParallelProofDB
ParallelDependenceDB
ParallelReductionDB
ParallelMapDB
ParallelScanDB
ParallelFilterDB
ParallelPartitionDB
ParallelScheduleDB
ParallelWorkerDB
ParallelPolicyDB
ParallelCostModelDB
ParallelTargetDB
ParallelCpuDB
ParallelSimdDB
ParallelGpuDB
ParallelFusionDB
ParallelTilingDB
ParallelDeterminismDB
ParallelCancellationDB
ParallelPanicDB
ParallelDebugDB
```

---

# 47. MIR additions

Thêm các semantic MIR operations:

```text
PARALLEL_BEGIN
PARALLEL_END

PARALLEL_FOR
PARALLEL_MAP
PARALLEL_REDUCE
PARALLEL_SCAN

ITERATION_SPLIT
ITERATION_CHUNK

WORKER_LOCAL
PARTITION_VIEW

REDUCE_INIT
REDUCE_COMBINE
REDUCE_FINALIZE

PARALLEL_CANCEL_CHECK
```

Sau semantic verification, chúng có thể lower thành:

```text
serial loop
SIMD loop
worker tasks
GPU dispatch
```

---

# 48. Parallel lowering pipeline

```text
Source
  ↓
Parallel API / syntax
  ↓
ParallelRegion
  ↓
IterationSpace Analysis
  ↓
Capture Analysis
  ↓
Memory Dependence
  ↓
Race Verification
  ↓
Reduction Detection
  ↓
Parallel Proof
  ↓
Cost Model
  ↓
Execution Policy
  ↓
┌───────────────┬─────────────┬────────────┐
│ Serial        │ CPU SIMD    │ CPU Threads│
└───────────────┴─────────────┴────────────┘
                         │
                         └──── GPU
```

Đây là một điểm rất quan trọng: **parallelism được quyết định sau semantic analysis**, không phải ngay tại parser.

---

# 49. Invariants

Đóng băng:

### `APAR-01`
Concurrency and parallelism are distinct semantics.

### `APAR-02`
Future does not imply parallel execution.

### `APAR-03`
Parallel execution requires a verified execution contract.

### `APAR-04`
Independent iterations may execute concurrently.

### `APAR-05`
Unknown cross-iteration memory dependence is not assumed safe.

### `APAR-06`
READ/READ iteration access is non-conflicting.

### `APAR-07`
Conflicting writes require disjointness, synchronization, or reduction semantics.

### `APAR-08`
Parallel reduction must preserve the declared reduction contract.

### `APAR-09`
Floating-point associativity is not assumed by default.

### `APAR-10`
Relaxed numerical semantics require explicit policy.

### `APAR-11`
Parallel map preserves its declared element correspondence.

### `APAR-12`
Parallel scan preserves scan semantics.

### `APAR-13`
Parallel filter preserves element order when ordered semantics are requested.

### `APAR-14`
Unordered side effects must not be presented as ordered.

### `APAR-15`
`auto` execution policy cannot change observable semantics.

### `APAR-16`
SIMD transformation must preserve memory semantics.

### `APAR-17`
GPU lowering requires GPU legality.

### `APAR-18`
Host-only effects cannot silently execute on GPU.

### `APAR-19`
Parallel captures obey normal closure ownership semantics.

### `APAR-20`
Disjoint partitioning may replace synchronization with ownership.

### `APAR-21`
Parallel execution must not implicitly copy large data.

### `APAR-22`
Worker-local state does not require cross-worker synchronization.

### `APAR-23`
Nested parallelism must not imply unbounded worker creation.

### `APAR-24`
Parallel region fusion is legal only when observable semantics are preserved.

### `APAR-25`
Parallel tiling may alter physical execution but not semantic results.

### `APAR-26`
Cancellation is cooperative.

### `APAR-27`
Panic propagation in parallel execution follows an explicit policy.

### `APAR-28`
Resource cleanup remains ownership-correct under parallel execution.

### `APAR-29`
Parallel optimization may select serial execution when it is semantically equivalent and cheaper.

### `APAR-30`
Parallel execution abstractions must not impose a mandatory global runtime.

---

## Kiến trúc Axiom lúc này

Sau 365, ta có một chuỗi khá mạnh:

```text
                 Axiom Program
                       │
            ┌──────────┴──────────┐
            │                     │
       Sequential            Parallel
            │                     │
          Scalar        ┌─────────┼──────────┐
                        │         │          │
                       SIMD     CPU        GPU
                                Threads
                                  │
                              Workers
                                  │
                                Tasks
```

Trong đó **một source abstraction có thể được compiler tự động hạ xuống nhiều execution strategy khác nhau**.

Đây chính là nền tảng để sau này Axiom có thể hướng tới kiểu:

```axiom
parallel_for(0..N) {
    out[i] = model(x[i])
}
```

nhưng compiler có đủ thông tin để quyết định:

```text
N nhỏ       → scalar
N vừa       → SIMD
N lớn       → CPU workers + SIMD
N rất lớn   → GPU
```

mà programmer không phải viết riêng 4 phiên bản code.