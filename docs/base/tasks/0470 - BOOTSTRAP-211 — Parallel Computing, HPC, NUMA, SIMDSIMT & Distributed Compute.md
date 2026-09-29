# BOOTSTRAP-211 — Parallel Computing, HPC, NUMA, SIMD/SIMT & Distributed Compute

**TRẠNG THÁI: FROZEN / COMPLETED**

Mục tiêu của 211 là hợp nhất các cơ chế thực thi mà Axiom đã có thành một mô hình duy nhất:

```text
Scalar
   ↓
SIMD
   ↓
Thread
   ↓
Task/Fiber
   ↓
GPU/SIMT
   ↓
Multi-GPU
   ↓
Distributed Node
```

Nhưng **không biến tất cả thành một abstraction duy nhất**.

Nguyên tắc trung tâm:

> **Computation là semantic operation; execution strategy là compiler/runtime decision khi semantics cho phép.**

---

# 211.1. Execution hierarchy

Axiom có các execution domain:

```text
CPU
 ├── Scalar
 ├── SIMD
 ├── Thread
 ├── Task
 └── Fiber

GPU
 ├── SIMT
 ├── Warp/Wave
 └── Kernel

Distributed
 ├── Node
 ├── Process
 └── Remote Task
```

Mỗi tầng có semantics riêng.

---

# 211.2. Không biến Thread thành abstraction cao nhất

Thread chỉ là một execution mechanism.

Programmer có thể dùng:

```text
Thread
Task
async
parallel_for
```

tùy mức control cần thiết.

---

# 211.3. Parallelism không đồng nghĩa concurrency

Phân biệt:

```text
Concurrency
= nhiều computation có thể tiến triển độc lập

Parallelism
= nhiều computation thực sự chạy đồng thời
```

Compiler/runtime không được đánh đồng hai khái niệm.

---

# 211.4. Data parallelism

API:

```axiom
parallel_for(range, fn(i) {
    ...
})
```

là library abstraction.

Compiler có thể chọn:

```text
single-thread
SIMD
multi-thread
GPU
```

nếu contract cho phép.

---

# 211.5. Parallel loop semantics

Một `parallel_for` phải khai báo/derive được:

```text
iteration independence
memory effects
reduction
ordering
```

---

# 211.6. Không tự động parallelize mọi loop

Ví dụ:

```text
x[i] = x[i-1]
```

có dependency.

Compiler không được tự ý parallelize nếu không chứng minh được equivalence.

---

# 211.7. Independent iterations

Nếu compiler chứng minh:

```text
iteration A
    ≠
iteration B
```

về conflicting writes/reads:

```text
parallelization = legal
```

---

# 211.8. Capability hỗ trợ parallelization

Ví dụ:

```text
mut_view<A>
```

được chia thành:

```text
mut_view<A[0..N/2]>
mut_view<A[N/2..N]>
```

nếu compiler chứng minh DISJOINT.

Đây là một lợi thế lớn của capability model Axiom.

---

# 211.9. Automatic parallelization

Compiler có thể:

```text
loop
 ↓
dependence analysis
 ↓
prove independent
 ↓
vectorize
 ↓
parallelize
```

nhưng:

```text
cannot prove
→ preserve original execution
```

---

# 211.10. Execution policy

Library có thể cung cấp:

```text
Sequential
Parallel
Vectorized
GPU
Auto
```

Ví dụ:

```axiom
for_each(data, parallel, process)
```

hoặc API tương đương.

---

# 211.11. `Auto`

`Auto` có nghĩa:

> compiler/runtime được phép chọn implementation tương đương.

Không có nghĩa:

> luôn chọn GPU hoặc thread.

---

# 211.12. Deterministic parallelism

Có những operation cần giữ deterministic ordering.

Ví dụ:

```text
fold
```

có thể yêu cầu:

```text
ordered
```

---

# 211.13. Parallel reduction

Có thể:

```text
sum_parallel(x)
```

với explicit contract:

```text
associative
commutative
```

nếu muốn reorder.

---

# 211.14. Floating-point reduction

Đối với `f32/f64`:

```text
sum(a,b,c)
```

không mặc định được phép:

```text
(a+b)+c
```

→

```text
a+(b+c)
```

nếu strict FP.

---

# 211.15. Relaxed numerical reduction

Có thể explicit:

```text
parallel_reduce_relaxed()
```

hoặc numerical profile tương đương.

---

# 211.16. SIMD vs threads

Compiler có thể ưu tiên:

```text
SIMD
```

trước khi tạo threads nếu workload nhỏ.

Ví dụ:

```text
N = 32
```

không nhất thiết cần thread pool.

---

# 211.17. Cost model

Parallelization dựa trên:

```text
work
granularity
cache locality
memory bandwidth
CPU topology
SIMD width
thread overhead
```

---

# 211.18. Runtime scheduling

Runtime có thể chọn:

```text
static
dynamic
guided
work-stealing
```

nhưng scheduling policy không thay đổi semantics.

---

# 211.19. Static scheduling

Range được chia trước:

```text
Worker 0 → [0..100]
Worker 1 → [100..200]
...
```

tốt cho workload predictable.

---

# 211.20. Dynamic scheduling

Workers lấy chunk khi hoàn thành.

Phù hợp workload không đồng đều.

---

# 211.21. Work stealing

Task runtime có:

```text
local deque
global queue
steal
```

nhưng đây là runtime implementation.

---

# 211.22. Task

Task là unit execution nhỏ hơn Thread.

Một task có thể:

```text
run
suspend
resume
migrate
complete
cancel
```

theo async/concurrency model.

---

# 211.23. CPU task migration

Task chỉ được migrate nếu:

```text
Send
storage
execution-domain
```

cho phép.

---

# 211.24. Pinned task

Một task có thể có execution-affinity:

```text
PinnedToCPU
PinnedToThread
PinnedToDevice
```

nếu API yêu cầu.

---

# 211.25. CPU affinity

System library có thể:

```text
pin_thread(cpu)
```

nhưng không phải Core primitive.

---

# 211.26. NUMA

Axiom cần explicit NUMA model cho HPC.

Ví dụ:

```text
Node 0
 ├── CPU 0-15
 └── Memory 0

Node 1
 ├── CPU 16-31
 └── Memory 1
```

---

# 211.27. NUMA storage domain

Có thể có metadata:

```text
NumaNodeId
```

nhưng physical placement vẫn là runtime/system policy.

---

# 211.28. NUMA-aware allocation

Library có thể cung cấp:

```text
allocate_on(node)
```

hoặc:

```text
first_touch
interleave
preferred
```

---

# 211.29. NUMA locality

Compiler/tooling có thể báo:

```text
remote_memory_access
```

nhưng không thay đổi semantics.

---

# 211.30. Cache topology

CompilerDB/target metadata có thể biết:

```text
L1
L2
L3
shared cache
cache line size
```

để tối ưu.

---

# 211.31. False sharing

Tooling có thể cảnh báo:

```text
possible false sharing
```

và library có:

```text
@cache_align
```

---

# 211.32. Cache alignment

Concept:

```axiom
@align(cache_line)
struct Counter {
    value: Atomic<u64>
}
```

nhưng `cache_line` phải target-aware.

---

# 211.33. Padding

Compiler có thể tự padding nếu:

```text
@cache_aligned
```

hoặc explicit layout contract.

---

# 211.34. Memory locality

Compiler có thể ưu tiên:

```text
producer → consumer
```

trên cùng NUMA/cache domain.

Đây là optimization, không semantic requirement.

---

# 211.35. Parallel collections

Collections có thể expose:

```text
parallel_iter
parallel_map
parallel_reduce
```

nhưng semantics vẫn dựa trên iterator model 167.

---

# 211.36. Mutable parallel iteration

Compiler cần chứng minh regions disjoint:

```text
A[i]
B[i]
```

hoặc reject.

---

# 211.37. Chunked views

Useful abstraction:

```text
chunks_mut(data, n)
```

trả các disjoint mutable views.

Đây là ví dụ cực mạnh cho Axiom:

```text
mut_view<T>
```

thay thế nhiều pointer/lifetime ceremony.

---

# 211.38. Parallel iterator ownership

`into_parallel_iter` có thể move collection ownership vào executor.

Không implicit clone toàn bộ collection.

---

# 211.39. Closure capture

Parallel closure capture được compiler phân tích:

```text
read capture
write capture
move capture
```

và kiểm tra Send/Share.

---

# 211.40. Shared state

Parallel code không được tự động tạo mutable global sharing.

Explicit:

```text
Atomic
Mutex
RwLock
Channel
```

---

# 211.41. Atomics

Đã có atomic model:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

211 không thay đổi semantics.

---

# 211.42. Parallel atomic operations

Compiler có thể lower:

```text
Atomic<u64>
```

thành:

```text
lock-free instruction
```

nếu target hỗ trợ.

---

# 211.43. Lock-free

Library có thể cung cấp:

```text
LockFreeQueue
MPSC
MPMC
```

nhưng không yêu cầu compiler phải chứng minh algorithm lock-free.

---

# 211.44. Wait-free

Tương tự, đây là algorithmic property.

Tooling có thể ghi metadata:

```text
WaitFree
LockFree
Blocking
```

---

# 211.45. Barrier

Parallel barrier:

```text
Barrier
```

có semantics synchronization rõ ràng.

Không dùng barrier thay thế ownership.

---

# 211.46. Latch

One-shot completion:

```text
Latch
```

phù hợp fork/join.

---

# 211.47. Fork/join

Concept:

```text
fork
 ├── task A
 ├── task B
 └── task C
      ↓
     join
```

Join thiết lập synchronization.

---

# 211.48. Structured parallelism

Mặc định ưu tiên:

```text
scope
 ├── child
 ├── child
 └── child
     ↓
 scope exit waits
```

Detach phải explicit.

---

# 211.49. Cancellation

Parallel task cancellation:

```text
cooperative
```

không cưỡng ép kill thread.

---

# 211.50. Failure propagation

Structured parallel scope cần policy:

```text
fail-fast
collect-all
cancel-siblings
ignore
```

---

# 211.51. Panic/error

Task failure không nhất thiết crash toàn process.

API quyết định:

```text
Result
panic
abort
```

---

# 211.52. Task groups

Có thể:

```text
TaskGroup
```

library abstraction trên structured concurrency.

---

# 211.53. CPU thread pool

Runtime optional:

```text
ThreadPool
```

và không phải mọi Axiom program đều link nó.

---

# 211.54. Work scheduler

Scheduler có thể dùng:

```text
global queue
local queues
work stealing
priority
affinity
```

---

# 211.55. Priority

Task priority là scheduling hint.

Không đảm bảo real-time scheduling nếu OS không cung cấp.

---

# 211.56. Real-time

Axiom có thể có profile:

```text
realtime
```

với hạn chế:

```text
no allocation
bounded latency
no blocking
```

tùy platform.

---

# 211.57. Hard vs soft real-time

Compiler không tuyên bố hard real-time chỉ vì profile.

Hardware/OS guarantees phải đủ.

---

# 211.58. SIMD

SIMD model đã có ở 168.

211 bổ sung execution policy:

```text
scalar
vector
parallel
```

---

# 211.59. SIMT

GPU model:

```text
thread
warp/wave
block/workgroup
grid
```

được coi là GPU execution semantics.

---

# 211.60. CPU/GPU abstraction

Không giả định:

```text
GPU thread == CPU thread
```

Chúng có execution semantics khác nhau.

---

# 211.61. Kernel parallelism

GPU kernel:

```text
@kernel
```

có logical invocation IDs:

```text
global_id
local_id
group_id
```

---

# 211.62. GPU divergence

Compiler có thể phân tích branch divergence.

Không coi divergence là correctness problem.

Nó là performance property.

---

# 211.63. Warp-level operations

GPU library có thể expose:

```text
shuffle
ballot
vote
warp_reduce
```

nhưng target-specific.

---

# 211.64. Portable GPU abstraction

High-level code nên dùng:

```text
parallel_reduce
```

khi portable behavior cần thiết.

Warp-specific API nằm ở backend extension.

---

# 211.65. Task graph

HPC/AI execution có thể biểu diễn:

```text
A
├── B
├── C
└── D
    ↓
    E
```

Graph scheduler có thể chạy independent nodes song song.

---

# 211.66. Dependency graph

Task dependency là semantic ordering:

```text
B depends on A
```

không cần explicit mutex.

---

# 211.67. Resource dependency

Task graph có thể track:

```text
Read(A)
Write(B)
Read(C)
```

để tự suy ra dependency.

---

# 211.68. Compiler task graph

Compiler có thể build graph từ effects:

```text
Task A: Write X
Task B: Read X
```

→ dependency.

---

# 211.69. Parallel effect analysis

Nếu:

```text
A: Read X
B: Write Y
```

và X/Y proven disjoint:

```text
A || B
```

---

# 211.70. Unknown alias

Nếu:

```text
X ↔ Y
```

unknown:

```text
cannot prove independent
```

không tự động parallelize.

---

# 211.71. Memory bandwidth

Cost model cần phân biệt:

```text
compute-bound
memory-bound
latency-bound
communication-bound
```

---

# 211.72. Roofline-style analysis

Tooling có thể hiển thị:

```text
FLOPs
bytes moved
arithmetic intensity
estimated bandwidth
```

để AI/programmer tối ưu.

---

# 211.73. NUMA + GPU

Topology có thể:

```text
CPU0
 └── GPU0
CPU1
 └── GPU1
```

Compiler/runtime nên biết locality.

---

# 211.74. PCIe topology

Device metadata có thể mô tả:

```text
CPU ↔ PCIe ↔ GPU
```

và peer-to-peer capabilities.

---

# 211.75. GPU peer memory

Nếu GPU0/GPU1 hỗ trợ:

```text
PeerAccess
```

runtime có thể tránh host round-trip.

---

# 211.76. Multi-GPU

Mỗi GPU là execution/storage domain:

```text
DeviceId
```

Tensor/device ownership phải rõ.

---

# 211.77. Distributed execution

Distributed compute:

```text
Node
 ├── CPU
 ├── GPU
 └── Memory
```

mỗi node có execution/storage domains riêng.

---

# 211.78. Remote value

Không cho:

```text
remote<T>
```

trở thành magical pointer.

Remote data phải explicit:

```text
RPC
Channel
DistributedBuffer
```

---

# 211.79. Distributed ownership

Local ownership transfer:

```text
Move
```

khác distributed transfer:

```text
Serialize
Send
Deserialize
```

---

# 211.80. Zero-copy distributed transfer

Có thể nếu:

```text
SharedMemory
RDMA
DMA
```

và contract cho phép.

Không mặc định.

---

# 211.81. RDMA

RDMA buffer:

```text
RegisteredBuffer
```

có lifetime dependency tới completion.

Axiom ownership rất phù hợp để mô hình hóa điều này.

---

# 211.82. MPI-like model

Có thể xây:

```text
Communicator
Rank
Request
Collective
```

trên networking layer.

Không cần MPI semantics trong Core.

---

# 211.83. Collective

```text
Broadcast
Reduce
AllReduce
AllGather
Scatter
Gather
Barrier
```

---

# 211.84. Distributed synchronization

Không coi:

```text
Barrier
```

là memory fence cho tất cả memory domains.

Mỗi execution/storage domain phải có semantics riêng.

---

# 211.85. Distributed failure

Node failure là external/distributed error:

```text
NodeLost
Timeout
Partition
RemoteError
```

không phải memory panic.

---

# 211.86. Failure detector

Distributed runtime có thể dùng:

```text
Heartbeat
Phi accrual
Timeout
```

library layer.

---

# 211.87. Distributed task cancellation

Cancel remote task không nhất thiết kill remote process.

Semantics phải explicit.

---

# 211.88. HPC scheduler integration

Có thể hỗ trợ:

```text
SLURM
Kubernetes
PBS
```

qua platform/runtime adapters.

---

# 211.89. Job vs Task

Phân biệt:

```text
Job
Task
Process
Thread
```

tránh tạo một abstraction universal.

---

# 211.90. Resource scheduling

Scheduler có thể nhận:

```text
CPU count
GPU count
memory
NUMA node
network
```

làm resource constraints.

---

# 211.91. Accelerator scheduling

Task có thể yêu cầu:

```text
GPU
NPU
CPU feature
memory
```

---

# 211.92. Execution placement

Placement:

```text
CPU
GPU
NUMA
Node
```

có thể là compiler/runtime decision nếu operation portable.

---

# 211.93. Placement annotation

Nếu programmer bắt buộc:

```text
@device(gpu0)
```

đây là explicit contract.

---

# 211.94. Data placement

Tensor:

```text
@device(gpu)
```

hoặc device-owned storage.

---

# 211.95. Automatic placement

Graph runtime/compiler có thể chọn:

```text
CPU vs GPU
```

dựa trên cost model.

---

# 211.96. Placement correctness

Performance có thể khác.

Semantics không được khác ngoài numerical profile.

---

# 211.97. Parallel compiler analysis

Compiler pipeline:

```text
MIR
 ↓
Ownership
 ↓
Capability
 ↓
Effect
 ↓
Dependence Analysis
 ↓
Parallelism Analysis
 ↓
SIMD
 ↓
CPU Parallel
 ↓
GPU
 ↓
Distributed
```

Không phải tất cả chương trình đều đi qua mọi bước.

---

# 211.98. Optimization hierarchy

Một computation có thể trải qua:

```text
Scalar
 ↓
SIMD
 ↓
Thread
 ↓
NUMA
 ↓
GPU
 ↓
Multi-GPU
 ↓
Distributed
```

nhưng mỗi bước chỉ được áp dụng nếu legality/cost model cho phép.

---

# 211.99. Compiler không được "đoán an toàn"

Nguyên tắc:

```text
PROVEN
    → optimize

UNKNOWN
    → preserve semantics
```

Đặc biệt với:

```text
alias
race
ordering
numerical reduction
remote effects
```

---

# 211.100. Parallelism invariants — `APAR`

### `APAR-20`
Concurrency and parallelism shall remain distinct semantic concepts.

### `APAR-21`
Execution domain shall remain distinct from ownership.

### `APAR-22`
Parallel execution shall not weaken ownership verification.

### `APAR-23`
Parallel mutable access requires proven disjointness or explicit synchronization.

### `APAR-24`
Unknown aliasing shall never be treated as independent parallel access.

### `APAR-25`
Compiler-derived parallelism shall preserve observable semantics.

### `APAR-26`
Automatic loop parallelization shall require dependence analysis.

### `APAR-27`
Parallel reduction shall have explicit ordering semantics.

### `APAR-28`
Strict floating-point reductions shall preserve required ordering.

### `APAR-29`
Relaxed numerical reductions shall require explicit permission.

### `APAR-30`
SIMD transformations shall preserve semantics.

### `APAR-31`
SIMT execution shall remain distinct from CPU threading.

### `APAR-32`
GPU warp-level behavior shall not be assumed portable unless explicitly declared.

### `APAR-33`
Task migration shall obey Send and storage/execution-domain rules.

### `APAR-34`
Pinned execution shall be explicit where required.

### `APAR-35`
Structured parallel scopes shall not implicitly detach child tasks.

### `APAR-36`
Detached execution shall be explicit.

### `APAR-37`
Parallel cancellation shall be cooperative by default.

### `APAR-38`
Task failure propagation shall have explicit policy.

### `APAR-39`
Thread pools shall remain optional runtime components.

### `APAR-40`
Scheduling policy shall not change program semantics.

### `APAR-41`
NUMA placement shall remain a performance/storage policy unless explicitly observable.

### `APAR-42`
NUMA-aware allocation shall preserve ownership semantics.

### `APAR-43`
Cache topology may guide optimization but shall not change semantics.

### `APAR-44`
Cache alignment shall be explicit when part of a performance contract.

### `APAR-45`
False-sharing diagnostics shall remain tooling/performance diagnostics.

### `APAR-46`
Task graphs shall encode explicit dependency semantics.

### `APAR-47`
Resource dependencies may be inferred from verified effect information.

### `APAR-48`
Parallel task scheduling shall respect resource dependencies.

### `APAR-49`
Independent regions may execute concurrently when capability analysis proves disjointness.

### `APAR-50`
Parallel iterators shall preserve iterator ownership semantics.

### `APAR-51`
Chunked mutable iteration shall produce disjoint capabilities.

### `APAR-52`
Work stealing shall not alter semantic ordering guarantees where ordering is observable.

### `APAR-53`
Distributed execution shall remain distinct from local memory concurrency.

### `APAR-54`
Distributed value transfer shall not be confused with local Move.

### `APAR-55`
Remote execution shall never imply a remote raw pointer.

### `APAR-56`
Zero-copy distributed execution requires explicit storage/completion contracts.

### `APAR-57`
RDMA buffers shall remain live until operation completion.

### `APAR-58`
Collective operations shall define completion and synchronization semantics.

### `APAR-59`
Distributed failure shall be represented separately from local memory failure.

### `APAR-60`
Execution placement shall not alter semantic results outside the active numerical profile.

### `APAR-61`
Automatic placement shall be an optimization/runtime decision unless explicitly constrained.

### `APAR-62`
GPU/CPU placement shall respect storage-domain rules.

### `APAR-63`
Multi-GPU execution shall treat devices as distinct execution/storage domains.

### `APAR-64`
Peer GPU memory access shall require explicit platform capability.

### `APAR-65`
HPC scheduling metadata shall not become mandatory Core semantics.

### `APAR-66`
Parallel execution shall not require garbage collection.

### `APAR-67`
Parallel execution shall not require a monolithic runtime.

### `APAR-68`
Parallel runtime components shall be tree-shakeable.

### `APAR-69`
Parallel compiler transformations shall declare legality conditions.

### `APAR-70`
Failed parallelism proofs shall preserve the original valid execution strategy.

---

# 211.101. Điểm quan trọng nhất của 211

Axiom hiện có thể tiến tới một mô hình rất mạnh:

```text
                  ONE COMPUTATION
                        │
          ┌─────────────┼──────────────┐
          ▼             ▼              ▼
        Scalar         SIMD          GPU
          │             │              │
          └──────┬──────┴──────┬───────┘
                 ▼             ▼
              Threads        Tasks
                 │             │
                 └──────┬──────┘
                        ▼
                     NUMA
                        │
                        ▼
                   Multi-GPU
                        │
                        ▼
                    Network
                        │
                        ▼
                  Distributed
```

Nhưng semantic model vẫn chỉ dựa trên:

```text
Ownership
Capability
Effect
Synchronization
Execution Domain
Storage Domain
```

Đây chính là điều giúp Axiom tránh phải có:

```text
thread pointer
GPU pointer
distributed pointer
tensor pointer
NUMA pointer
```

cho từng domain.

---

# Một kết luận kiến trúc đáng giữ

Tới đây có thể đóng băng một nguyên tắc rất quan trọng cho Axiom:

> **Parallelism là property của computation; không phải một loại dữ liệu mới.**

Ví dụ cùng một function:

```axiom
fn process(x: f32) -> f32 {
    ...
}
```

có thể được compiler sử dụng trong:

```text
scalar loop
SIMD loop
parallel CPU loop
GPU kernel
distributed batch
```

**nếu compiler chứng minh representation và execution contract tương thích.**

Programmer không cần viết năm phiên bản algorithm chỉ vì phần cứng khác nhau.

---

# BOOTSTRAP-212 — Real-Time, Embedded, Kernel/OS Development & Bare-Metal Axiom

**TRẠNG THÁI: NEXT**

Đây là bước rất quan trọng để kiểm tra xem toàn bộ architecture hiện tại có thực sự đạt mục tiêu **systems language** hay không.

212 sẽ thiết kế:

```text
Bare Metal
Bootloader
Firmware
Microcontroller
Interrupt
Exception
MMIO
DMA
Device Driver
Kernel
Scheduler
Page Tables
Virtual Memory
Physical Memory
Cache/TLB
Atomic/Barrier
Embedded
RTOS
No-OS
No-Allocator
No-Runtime
No-Std
```

và câu hỏi trung tâm:

> **Axiom có thể viết bootloader, firmware, device driver và kernel hoàn toàn bằng chính Axiom mà không bị Core/Runtime/GC/OS assumptions kéo ngược lên hay không?**