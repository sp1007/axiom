Tiếp tục.

# BOOTSTRAP-040 — GPU / Device Execution Model Audit & Freeze

Mục tiêu của phần này là để Axiom có **GPU programming như một phần tự nhiên của ngôn ngữ**, nhưng không biến Core thành một ngôn ngữ CUDA/HLSL riêng.

Nguyên tắc:

> **GPU là một Execution Domain + Storage Domain mới, không phải một ngôn ngữ mới.**

---

# 1. Mô hình tổng thể

Axiom thống nhất:

```text id="g6rj1a"
                    Axiom Program
                         │
             ┌───────────┴───────────┐
             │                       │
          CPU Domain              GPU Domain
             │                       │
       Thread/Fiber/Task          Kernel
             │                       │
        Host Storage            Device Storage
```

Cùng một semantic nền:

```text id="7h2k9c"
Type
Ownership
Capability
Synchronization
Memory ordering
```

nhưng GPU có thêm các constraint đặc thù.

---

# 2. `@kernel`

GPU entry point:

```axiom id="g1q8dx"
@kernel
fn add(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
) {
    ...
}
```

`@kernel` không phải optimization hint.

Nó là:

> **Execution-domain contract.**

---

# 3. Kernel không phải function bình thường

Một function:

```axiom id="x3m7fy"
fn foo() { ... }
```

có thể sử dụng host facilities phù hợp.

Kernel:

```axiom id="5f4jtp"
@kernel fn foo() { ... }
```

phải satisfy GPU legality rules.

---

# 4. Kernel legality

Compiler kiểm tra:

```text id="6k2q9d"
@kernel
   │
   ├── type legality
   ├── ownership legality
   ├── capability legality
   ├── address-space legality
   ├── synchronization legality
   └── target feature legality
```

---

# 5. Kernel không được gọi arbitrary OS API

Không cho trong GPU kernel:

```text id="z9m5ba"
File
Socket
OS syscall
blocking Mutex
arbitrary process API
host pointer dereference
```

trừ khi target-specific GPU abstraction định nghĩa rõ.

---

# 6. Kernel không có arbitrary host access

Ví dụ:

```text id="3x7yq1"
Host pointer
     ↓
GPU kernel
```

không được tự động hợp lệ.

Phải thông qua explicit device memory abstraction.

---

# 7. Storage Domains

Axiom GPU model phân biệt:

```text id="f4o3xs"
Host
Device
Shared
Local
Private
Constant
External
```

Đây là **Storage Domains**.

---

# 8. Host memory

```text id="r7v4mc"
Host
```

CPU-accessible memory.

GPU không mặc định được phép dereference host storage.

---

# 9. Device memory

```text id="q1j9ea"
Device
```

GPU-accessible storage.

CPU không mặc định được phép dereference trực tiếp nếu backend không hỗ trợ.

---

# 10. Shared memory

```text id="2kv1xq"
Shared
```

thường dùng cho nhóm execution units/workgroup.

Lifetime và synchronization phụ thuộc kernel execution contract.

---

# 11. Local memory

```text id="6ap7wr"
Local
```

storage private cho execution unit/lane/thread tùy GPU backend.

---

# 12. Private memory

```text id="n0v8s5"
Private
```

private state của một GPU execution instance.

---

# 13. Constant memory

```text id="s2x9el"
Constant
```

read-only GPU-accessible data theo backend.

---

# 14. External memory

```text id="7p2w3f"
External
```

dùng cho:

- mapped memory
- imported resources
- graphics APIs
- foreign device resources

phải có explicit ownership contract.

---

# 15. `DeviceBuffer<T>`

Library abstraction:

```axiom id="r9m4dt"
let a = DeviceBuffer<f32>::new(1024)
```

Semantics:

> owned device storage.

Không phải:

> chắc chắn một physical allocation duy nhất.

Backend có thể dùng:

```text id="9b6s2c"
VRAM
unified memory
pinned host memory
mapped memory
pool
```

nếu semantic contract cho phép.

---

# 16. DeviceView

Có thể có:

```text id="0s8r8x"
DeviceView<T>
```

hoặc compiler/library biểu diễn bằng capability tương đương:

```text id="n2l6va"
device view<T>
```

Mục tiêu là giữ triết lý:

```text id="c9h4be"
view<T>
mut_view<T>
```

nhưng thêm storage/execution domain.

---

# 17. Không nên tạo hàng loạt pointer types

Không muốn:

```text id="4l5c0u"
HostPtr<T>
DevicePtr<T>
SharedPtr<T>
LocalPtr<T>
ConstantPtr<T>
...
```

ở safe application level.

Thay vào đó:

```text id="c6f1r9"
Capability
+
StorageDomain
```

compiler theo dõi.

Raw device pointer chỉ dành cho system/unsafe layer.

---

# 18. Kernel parameter

Ví dụ:

```axiom id="9yd9r4"
@kernel
fn add(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
)
```

compiler phải biết:

```text id="a1j3s7"
a → Device storage
b → Device storage
out → Device storage
```

nếu kernel ABI yêu cầu.

Không thể truyền arbitrary host view.

---

# 19. Host → Device

Ví dụ:

```axiom id="m4w8ae"
let d = DeviceBuffer::upload(host_data)
```

conceptually:

```text id="c0x7fh"
Host ownership
       │
       │ transfer/copy
       ▼
Device storage
```

Transfer operation có semantics rõ ràng.

---

# 20. Device → Host

```axiom id="z1k5pt"
let result = d.download().await?
```

là explicit.

Không tự động:

```text id="2zq7ab"
device memory
 ↓
magic CPU access
```

---

# 21. Zero-copy

Nếu hardware hỗ trợ:

```text id="w7k8s1"
UnifiedBuffer
```

có thể tránh physical copy.

Nhưng:

> unified memory không có nghĩa automatic synchronization.

---

# 22. `UnifiedBuffer<T>`

Có thể có library abstraction:

```text id="n4s7dq"
UnifiedBuffer<T>
```

cho memory accessible từ cả host/device.

Nhưng compiler/runtime vẫn phải theo dõi:

```text id="x7d2pk"
ownership
access
synchronization
in-flight operations
```

---

# 23. GPU launch

Conceptually:

```axiom id="r5z9e4"
let event = launch(
    add,
    grid,
    block,
    args
)
```

trả:

```text id="f4w7ak"
GpuEvent
```

---

# 24. GPU execution là async

Kernel launch thường không đồng nghĩa kernel đã hoàn thành.

Do đó:

```text id="v6n3qr"
launch()
```

→ operation in-flight.

---

# 25. `GpuEvent`

`GpuEvent` là synchronization/completion capability.

```text id="1p8m2h"
GpuEvent
    │
    ├── wait()
    ├── poll()
    └── await
```

API cụ thể thuộc runtime/library.

---

# 26. Buffer lifetime

Ví dụ:

```axiom id="j2m5qx"
let buffer = DeviceBuffer(...)
let event = launch(kernel, buffer)

drop(buffer)
```

không hợp lệ nếu kernel còn sử dụng buffer.

---

# 27. In-flight operation giữ capability

Conceptually:

```text id="7f3kqa"
DeviceBuffer
      │
      ├── host capability
      │
      └── in-flight GPU capability
```

Buffer không được reclaim cho tới khi operation không còn phụ thuộc vào nó.

---

# 28. Đây không phải GC

Runtime chỉ duy trì:

```text id="2b6s5k"
explicit operation lifetime
```

Không tracing object graph.

---

# 29. GPU ownership transfer

Có thể:

```text id="3m8jvf"
DeviceBuffer
    │ Move
    ▼
GPU operation
```

Sau Move, host code không được sử dụng ownership đó nếu không có abstraction cho phép.

---

# 30. Host ownership và GPU capability

Có thể có:

```text id="5w4k6x"
DeviceView
```

là non-owning capability.

Không biến thành:

```text id="6j9b1s"
DeviceBuffer
```

---

# 31. GPU views

Tương tự CPU:

```text id="e7h2n8"
device view<T>
device mut_view<T>
```

conceptually.

Read:

```text id="j8s2dp"
many readers
```

Write:

```text id="a3l9wv"
exclusive writer
```

---

# 32. GPU aliasing

Nếu:

```text id="5u8q1e"
a: mut_view<f32>
b: mut_view<f32>
```

compiler không chứng minh được disjoint:

```text id="q4j6z9"
UNKNOWN
```

→ kernel safe code bị reject hoặc phải dùng explicit concurrent-access abstraction.

---

# 33. Why this matters

Nếu bỏ rule này:

```text id="w2p9r7"
out[i] = ...
```

có thể race.

Axiom không muốn:

```text id="e7d4hc"
GPU race = programmer's problem by default
```

trong safe code.

---

# 34. GPU indexing

Kernel cần execution index.

Ví dụ API có thể cung cấp:

```text id="r6c8wx"
global_id()
local_id()
group_id()
global_size()
local_size()
```

nhưng đây là GPU library/compiler intrinsic.

Không cần tạo syntax riêng:

```text id="c7m3x9"
thread.x
block.y
warp.z
```

ở Core.

---

# 35. Target abstraction

Backend mapping:

```text id="2y8fkc"
global_id()
     ↓
CUDA
SPIR-V
Metal
DirectX
Vulkan
ROCm
...
```

tùy target.

---

# 36. GPU intrinsics

Intrinsic registry có:

```text id="m5q7vz"
name
signature
safety
execution domain
storage domain
target constraints
lowering
```

đúng theo BOOTSTRAP-036.

---

# 37. GPU barrier

GPU có synchronization scope.

Ví dụ conceptually:

```text id="n9k2ha"
workgroup_barrier()
```

Compiler phải biết scope:

```text id="q1c7wv"
lane
subgroup
workgroup
device
system
```

---

# 38. Không đưa GPU scopes vào CPU Atomic API

CPU:

```text id="5r0k3d"
Relaxed
Acquire
Release
...
```

GPU có thêm:

```text id="8x2v1k"
scope
```

nhưng đây là extension của GPU atomic model.

---

# 39. GPU Atomic

Conceptually:

```axiom id="f9t2wm"
atomic_add(
    counter,
    1,
    order = Relaxed,
    scope = Workgroup
)
```

Compiler validates:

```text id="z3y7ps"
storage domain
execution domain
atomic type
scope
target support
```

---

# 40. CPU code không cần GPU scope

CPU Core vẫn chỉ thấy:

```text id="6x5j8n"
Atomic<T>
```

GPU API mới expose additional scope where needed.

---

# 41. GPU synchronization

GPU barrier không nhất thiết tạo CPU↔GPU synchronization.

Ví dụ:

```text id="j5r1tq"
workgroup_barrier()
```

chỉ có ý nghĩa trong workgroup.

---

# 42. CPU/GPU synchronization

Host:

```text id="q9m7sz"
launch(kernel)
```

Device:

```text id="f2k5xy"
kernel completes
```

Host cần:

```text id="c7n3vp"
GpuEvent.wait()
```

hoặc await.

---

# 43. Event completion

Completion tạo synchronization edge:

```text id="5u8gk2"
GPU writes
      ↓
kernel complete
      ↓
event wait
      ↓
CPU reads
```

đây là explicit synchronization.

---

# 44. Launch không tự synchronize

```text id="w5d2pa"
launch()
```

không có nghĩa:

```text id="1q7hcz"
CPU immediately sees device writes
```

---

# 45. Unified memory vẫn cần synchronization

Ví dụ:

```text id="a6q1cv"
CPU writes
 ↓
launch
 ↓
GPU reads
```

cần synchronization/publication theo backend semantics.

---

# 46. GPU kernel cannot arbitrary await

Một GPU kernel không thể:

```text id="x4v7qn"
await socket.read()
```

Kernel phải obey execution-domain legality.

---

# 47. GPU Future

Host API có thể trả:

```text id="t7q9kp"
GpuEvent
```

hoặc Future wrapping event.

Nhưng GPU kernel itself không nhất thiết là Axiom async Future.

---

# 48. Kernel compilation

Pipeline:

```text id="m0w4cz"
Axiom source
      ↓
Typed HIR
      ↓
Kernel legality
      ↓
GPU MIR
      ↓
GPU lowering
      ↓
SPIR-V / DXIL / PTX / Metal IR / ...
```

---

# 49. Không cần GPU-specific language frontend

Đây là mục tiêu quan trọng.

Không:

```text id="z6f1ra"
Axiom CPU parser
+
CUDA parser
+
HLSL parser
+
...
```

Chỉ:

```text id="2x4k9p"
Axiom frontend
```

sau đó backend khác nhau.

---

# 50. Kernel restricted subset

GPU backend có thể reject:

```text id="6q8s3n"
unsupported dynamic allocation
unsupported recursion
unsupported OS call
unsupported trait object
unsupported exception/unwind
```

nhưng semantics của language vẫn thống nhất.

---

# 51. Dynamic allocation trong kernel

MVP:

```text id="p5c7jw"
No arbitrary dynamic allocation
```

trong GPU kernel.

Lý do:

- target diversity
- predictable performance
- allocator complexity.

Specialized device allocator có thể bổ sung sau.

---

# 52. Recursion

MVP nên:

```text id="h7q2cm"
reject unbounded recursion
```

trừ compiler có thể chứng minh bounded/target supports it.

---

# 53. Dynamic dispatch

Không mặc định cho phép:

```text id="u5x3kw"
dyn Trait
```

trong kernel.

Static dispatch/generic monomorphization ưu tiên.

---

# 54. Closures

Capturing closures trong GPU kernel chỉ hợp lệ nếu:

```text id="n1w8sf"
capture state
```

đều GPU-compatible.

Không được capture:

```text id="p4s6tm"
Host file handle
Socket
Mutex
arbitrary pointer
```

---

# 55. GPU Send/Share

Có thể xem:

```text id="f3x9mb"
Host → Device
```

là execution/storage-domain transfer.

Không nhất thiết dùng nguyên xi `Send`, bởi GPU có semantics khác.

Nhưng triết lý vẫn:

```text id="v8q1yc"
ownership/capability transfer
```

được explicit.

---

# 56. Device capability

Compiler internal capability có thể chứa:

```text id="k6r3dp"
storage_domain = Device
region
access = READ/WRITE
provenance
execution_domain
```

Do đó verifier biết:

```text id="q8w4mn"
GPU may access this region
```

---

# 57. Host pointer provenance

Không cho:

```text id="t1z5vk"
u64 address
 ↓
GPU pointer
```

trong safe code.

Numeric address không tự trở thành valid device capability.

---

# 58. Unsafe GPU pointer

System-level code có thể:

```text id="n5x7pc"
raw device pointer
```

nhưng phải establish:

- address space
- alignment
- bounds
- lifetime
- ownership/access contract.

Sau đó safe capability verification resumes.

---

# 59. External GPU resources

Graphics API:

```text id="e6s2yk"
VkBuffer
MTLBuffer
ID3D12Resource
CUDA allocation
```

không được giả định là Axiom `DeviceBuffer`.

Wrapper phải establish explicit contract.

---

# 60. External ownership

Ví dụ:

```text id="r4q7wd"
foreign GPU object
```

có thể:

```text id="e2m9vz"
OwnedByForeign
Borrowed
OwnedByAxiom
Shared
```

ABI wrapper phải thể hiện rõ.

---

# 61. Device allocator

Không đưa allocator vào Core type parameter:

```text id="d8y2hr"
DeviceBuffer<T, MyGpuAllocator>
```

mặc định.

Library có thể expose custom allocator khi cần.

---

# 62. Pooling

Runtime có thể:

```text id="f7m2kq"
DevicePool
```

để giảm allocation overhead.

Semantics vẫn:

```text id="t5r8xb"
owned storage
```

---

# 63. Kernel fusion

Compiler có thể:

```text id="m2n7qc"
kernel A
   ↓
kernel B
```

→ fused kernel nếu semantics không đổi.

Đây là optimization.

---

# 64. Tensor specialization

Comptime có thể generate:

```text id="h8c4vn"
matmul<M,N,K>
```

và GPU compiler optimize:

```text id="y7f2jp"
tile size
vector width
shared memory
unrolling
```

Không cần runtime reflection.

---

# 65. GPU memory coalescing

Đây là optimizer concern.

Axiom semantics không encode:

```text id="p4v7dk"
"thread 0 accesses x"
```

theo cách làm compiler không tối ưu được.

Compiler/backend chịu trách nhiệm mapping.

---

# 66. GPU barriers và ownership

Barrier không tạo ownership transfer.

Ví dụ:

```text id="k1r4ms"
barrier()
```

không biến:

```text id="9w2jtc"
view
```

thành owner.

Nó chỉ synchronization.

---

# 67. GPU race

Safe kernel không được có conflicting unsynchronized access.

Ví dụ:

```text id="s3k7qp"
thread A → write X
thread B → write X
```

→ invalid nếu không có atomic/synchronization abstraction phù hợp.

---

# 68. Atomics và race

Nếu:

```text id="r2j5wm"
Atomic<T>
```

thì concurrent atomic accesses hợp lệ theo atomic semantics.

Nhưng:

```text id="z9q3hk"
Atomic<T>
+
ordinary T access
```

không tự động an toàn.

---

# 69. GPU `mut_view`

Một `mut_view` vẫn là exclusive write capability.

Nếu nhiều GPU lanes cần mutate cùng region:

```text id="6p1mrx"
ordinary mut_view
```

không đủ.

Phải dùng:

```text id="v7q4sn"
Atomic
```

hoặc specialized parallel-write abstraction.

---

# 70. Parallel output

Một abstraction tương lai có thể biểu diễn:

```text id="h3q6yt"
disjoint_parallel_view<T>
```

nhưng **không đưa vào Core v1 ngay**.

Compiler hiện tại cố prove disjoint regions.

---

# 71. GPU `for`

Kernel có thể dùng:

```axiom id="w8x4pk"
for i in range(0, n) {
    ...
}
```

Compiler/backend parallelization phụ thuộc kernel launch model.

Không biến `for` thành GPU thread loop tự động trong Core semantics.

---

# 72. Explicit kernel execution

Muốn GPU execution:

```text id="n6v3sq"
@kernel
```

và explicit launch.

Không:

```text id="q7m1tx"
compiler tự quyết định đưa function lên GPU
```

vì đây sẽ thay đổi:

- execution semantics
- memory domain
- synchronization
- performance
- external side effects.

---

# 73. GPU specialization

Compiler có thể auto-specialize kernel:

```text id="s9k2vh"
T
M
N
K
target features
```

nhưng semantics không thay đổi.

---

# 74. GPU error model

Kernel không nên dùng:

```text id="z4p7wc"
OS exception
```

MVP:

```text id="r8k3mb"
panic/trap
```

hoặc kernel status/result abstraction do backend cung cấp.

---

# 75. Bounds checking

Safe:

```axiom id="u6n2fq"
out[i]
```

compiler phải prove/check bounds.

GPU backend có thể eliminate check nếu proof tồn tại.

Unsafe unchecked access vẫn có thể tồn tại ở system layer.

---

# 76. Kernel panic

Nếu target không support unwind:

```text id="b3v6nx"
panic → device trap/status
```

Không yêu cầu GPU unwinder.

---

# 77. Device failure

GPU launch có thể fail:

```text id="x9f2rv"
launch(...) -> Result<GpuEvent, GpuError>
```

Đây là host-side recoverable failure.

Không nhầm với kernel computation panic/trap.

---

# 78. GPU event lifetime

`GpuEvent` là resource.

Drop không được:

```text id="z1m7qc"
free event
```

khi runtime vẫn cần nó để observe completion.

Runtime đảm bảo lifecycle.

---

# 79. Multiple GPU devices

Axiom nên hỗ trợ:

```text id="m4q8wk"
DeviceId
```

và explicit:

```text id="t9x2js"
DeviceBuffer @ DeviceId
```

ở library level.

Không hard-code:

```text id="b7r1kp"
GPU 0
```

vào Core.

---

# 80. Peer-to-peer GPU

Nếu backend hỗ trợ:

```text id="h5n8vx"
Device A → Device B
```

thì transfer là explicit operation.

Không giả định mọi device có cùng address space.

---

# 81. Multi-GPU synchronization

`GpuEvent`/device synchronization abstraction phải encode:

```text id="p6c3zr"
device scope
storage ownership
completion
```

---

# 82. GPU ↔ CPU channel

Không đưa Channel<T> thông thường trực tiếp vào GPU kernel.

Có thể có:

```text id="j7w4ks"
DeviceQueue
MappedRingBuffer
GpuChannel
```

ở runtime/library layer.

Semantics vẫn dựa trên ownership + synchronization.

---

# 83. Device-side allocation future

Nếu sau này cần:

```text id="g4n9pq"
device_alloc<T>()
```

nó phải là explicit device allocator.

Không thay đổi Core `Box<T>` semantics thành GPU-specific.

---

# 84. `Box<T>` trên GPU

Không nên cho rằng:

```text id="b9x3mc"
Box<T> = host heap
```

hoặc:

```text id="p5w7zs"
Box<T> = device heap
```

`Box` là owned dynamic-storage semantic.

Device-specific allocation cần explicit abstraction.

---

# 85. ABI

Kernel ABI là:

```text id="k6q2vn"
target/backend-specific
```

Không dùng Axiom normal function ABI một cách giả định.

Compiler tạo explicit:

```text id="s4j9bc"
GPU ABI lowering
```

---

# 86. GPU binary

Một executable có thể chứa:

```text id="n7c4yx"
CPU code
+
GPU binary/code object
```

hoặc external device binary.

Linker/package system quản lý.

---

# 87. Lazy GPU compilation

Library có thể compile/load GPU kernel runtime nếu cần.

Nhưng đó là runtime policy.

Static GPU compilation vẫn là primary path cho predictable deployment.

---

# 88. Comptime + GPU

Đây là nơi BOOTSTRAP-037 kết hợp rất tốt:

```text id="z8m4qy"
comptime
   ↓
kernel specialization
   ↓
GPU lowering
```

Ví dụ:

```text id="u2n6sx"
M = 128
N = 128
K = 64
```

→ compiler generate specialized kernel.

---

# 89. Reflection + GPU

Compile-time reflection có thể inspect:

```text id="q6x3mk"
struct Tensor {
    ...
}
```

và generate GPU layouts.

Runtime reflection không bắt buộc.

---

# 90. GPU code generation

Generated GPU code vẫn phải:

```text id="a7m2pv"
type-check
ownership-check
capability-check
GPU-legality-check
```

Không có trusted generated kernel bypass.

---

# 91. GPU memory layout

CPU:

```text id="c5j9vz"
@repr(C)
```

không tự động có nghĩa GPU layout compatible.

GPU cần explicit representation contract khi backend yêu cầu.

Ví dụ future:

```text id="r4y8sw"
@repr(gpu(...))
```

nhưng syntax cụ thể chưa cần freeze.

---

# 92. Serialization ≠ GPU layout

Không dùng:

```text id="f8q2nm"
wire format
```

làm GPU memory layout.

Ba lớp vẫn tách:

```text id="n3v7cx"
semantic value
memory representation
wire representation
```

---

# 93. GPU pointer provenance

Device pointer có provenance:

```text id="w6r1kp"
device allocation
+
region
+
address space
+
lifetime
```

Numeric conversion không đủ để tạo safe capability.

---

# 94. Unsafe GPU operations

Unsafe có thể dùng:

```text id="z7q3mv"
raw device pointer
pointer arithmetic
external resource handle
unaligned access
volatile MMIO/device access
```

nhưng phải establish contract.

---

# 95. GPU safe boundary

Sau:

```text id="m5k8xb"
unsafe device operation
```

compiler trở lại tracking:

```text id="q2v6nt"
provenance
bounds
alignment
lifetime
access
```

nếu unsafe operation tạo safe capability.

---

# 96. Performance philosophy

GPU model của Axiom không nên ép programmer vào:

```text id="s4m8jq"
manual lifetime
manual borrow
manual address-space pointer conversions
manual synchronization everywhere
```

Compiler/runtime abstraction phải gánh phần lớn complexity.

---

# 97. Nhưng semantic boundary vẫn explicit

Programmer phải biết:

```text id="e8x2vy"
CPU
vs
GPU
```

và:

```text id="k4m7sd"
Host storage
vs
Device storage
```

và:

```text id="v5q1cz"
launch
vs
completion
```

Đây là những thứ compiler không thể tự giấu mà không làm semantics trở nên khó đoán.

---

# 98. GPU Core boundary

Core chỉ cần biết:

```text id="a1y6tp"
@kernel
ExecutionDomain
StorageDomain
device capability
atomic scope primitives
```

Còn:

```text id="e7p3qm"
CUDA
Vulkan
Metal
DirectX
ROCm
```

ở backend/runtime layer.

---

# 99. GPU architecture

Pipeline cuối:

```text id="g3v9xs"
                 Axiom
                   │
             Typed HIR/MIR
                   │
          ┌────────┴────────┐
          │                 │
         CPU               GPU
          │                 │
       CPU LIR          GPU MIR
          │                 │
       x86/ARM          target backend
```

Một frontend, nhiều backend.

---

# 100. Invariants AGPU — Freeze

Giữ các invariant cũ:

```text id="r7n3vw"
AGPU-20   GPU is an explicit execution domain.
AGPU-21   GPU storage is an explicit storage domain.
AGPU-22   @kernel establishes GPU execution legality.
AGPU-23   Async device operations explicitly establish resource lifetime.
AGPU-24   Host storage is not implicitly device-accessible.
AGPU-25   Device storage is not implicitly host-accessible.
AGPU-26   Device views preserve storage-domain identity.
AGPU-27   Device views cannot outlive device storage.
AGPU-28   Device ownership transfer is explicit.
AGPU-29   Host/device transfer is explicit.
AGPU-30   Unified memory does not imply automatic synchronization.
AGPU-31   Device allocation is not mandatory physical VRAM allocation.
AGPU-32   Device allocation strategy is runtime/backend policy.
AGPU-33   GPU kernels cannot arbitrarily invoke host facilities.
AGPU-34   GPU kernel legality is compiler verified.
AGPU-35   GPU intrinsics are compiler-registered semantics.
AGPU-36   GPU intrinsics are target validated.
AGPU-37   GPU barriers have explicit execution scope.
AGPU-38   GPU atomic operations have explicit applicable scope.
AGPU-39   Dropping a device resource cannot invalidate an in-flight operation.
AGPU-40   Unified memory does not eliminate synchronization.
AGPU-41   GPU execution does not imply host synchronization.
AGPU-42   Kernel launch does not imply kernel completion.
AGPU-43   GPU completion establishes explicit synchronization.
AGPU-44   GPU race freedom follows ownership/capability/synchronization rules.
AGPU-45   Device pointers have explicit provenance.
AGPU-46   Numeric addresses do not automatically become safe device pointers.
```

Bổ sung:

```text id="9d2v7m"
AGPU-47   GPU execution is not a separate source language.

AGPU-48   GPU kernels use the Axiom type system.

AGPU-49   GPU kernels use Axiom ownership semantics.

AGPU-50   GPU kernels use Axiom capability semantics.

AGPU-51   GPU kernels use GPU-specific legality rules.

AGPU-52   Host and device storage domains remain explicitly distinguishable.

AGPU-53   Storage domain is distinct from execution domain.

AGPU-54   DeviceBuffer represents owned device-storage semantics.

AGPU-55   DeviceBuffer does not require a particular physical allocation strategy.

AGPU-56   DeviceView is non-owning.

AGPU-57   Device mutable views are exclusive unless a concurrent-access abstraction is used.

AGPU-58   Unknown device-region overlap cannot be assumed disjoint.

AGPU-59   GPU safe code cannot contain conflicting unsynchronized accesses.

AGPU-60   GPU atomic access does not make ordinary conflicting access safe.

AGPU-61   GPU barriers do not transfer ownership.

AGPU-62   GPU barriers synchronize only within their defined scope.

AGPU-63   GPU events represent explicit completion/synchronization state.

AGPU-64   GPU event completion does not imply unrelated synchronization.

AGPU-65   In-flight GPU operations retain required storage lifetime.

AGPU-66   GPU operation cancellation cannot reclaim storage prematurely.

AGPU-67   GPU launch is distinct from GPU completion.

AGPU-68   GPU launch may be asynchronous.

AGPU-69   GPU backend may specialize kernels without changing semantics.

AGPU-70   Kernel fusion is permitted when observable semantics are preserved.

AGPU-71   GPU loop parallelization is an optimization unless explicitly represented by kernel execution semantics.

AGPU-72   GPU dynamic allocation is not required by Core.

AGPU-73   GPU dynamic allocation, when supported, is an explicit runtime/library capability.

AGPU-74   GPU dynamic dispatch is not required by Core.

AGPU-75   Static dispatch is preferred for GPU kernels.

AGPU-76   Captured GPU closure state must satisfy GPU legality.

AGPU-77   Host-only capabilities cannot implicitly enter GPU execution.

AGPU-78   Device-only capabilities cannot implicitly enter host execution.

AGPU-79   Unsafe device access must establish explicit machine-level preconditions.

AGPU-80   Safe verification resumes after a valid unsafe device boundary.

AGPU-81   GPU ABI is explicit and target-specific.

AGPU-82   Ordinary Axiom ABI is not automatically a GPU kernel ABI.

AGPU-83   GPU layout is distinct from CPU layout unless explicitly contracted.

AGPU-84   @repr(C) does not automatically define every GPU layout.

AGPU-85   GPU binary artifacts are independently target-lowered.

AGPU-86   CPU-only programs do not require GPU runtime components.

AGPU-87   GPU runtime components are independently linkable.

AGPU-88   GPU failure is distinct from ordinary host panic.

AGPU-89   Host-side GPU API failures may use Result.

AGPU-90   GPU kernel trap/panic follows target-supported failure semantics.

AGPU-91   GPU kernels do not require a host unwinder.

AGPU-92   GPU execution may be freestanding from the host runtime.

AGPU-93   Multiple GPU devices require explicit device identity.

AGPU-94   Device-to-device transfers are explicit.

AGPU-95   External GPU resources require explicit ownership contracts.

AGPU-96   Foreign GPU handles are not automatically Axiom DeviceBuffer values.

AGPU-97   Comptime-generated GPU code is re-verified.

AGPU-98   Generic GPU specialization is compile-time.

AGPU-99   GPU specialization does not imply runtime reflection.

AGPU-100  GPU optimization cannot change ownership, synchronization, or observable semantics.
```

---

# Kiến trúc GPU đã freeze

Đến đây GPU của Axiom có thể tóm lại thành:

```text id="s8g3vx"
                   CPU
                    │
              Host Storage
                    │
             explicit transfer
                    │
                    ▼
                  GPU
                    │
                @kernel
                    │
       ┌────────────┼────────────┐
       │            │            │
    Device       Shared       Private
    Storage      Storage      Storage
       │
       ▼
    GpuEvent
       │
       ▼
   completion
       │
       ▼
      CPU
```

Và quan trọng nhất:

```text id="7t1m8q"
Ownership
    +
Capability
    +
Execution Domain
    +
Storage Domain
    +
Synchronization
```

được dùng chung cho CPU, async, thread, fiber và GPU.

Như vậy Axiom không cần tạo một hệ thống memory/lifetime hoàn toàn mới chỉ vì có GPU.

---

## Tiếp theo: BOOTSTRAP-041

Bước tiếp theo hợp lý là **Generic/Type-System ↔ GPU/Async/Concurrency Integration Audit** rồi mới đi sâu vào **Module / Package / Build System**.

Tuy nhiên có một phần còn quan trọng hơn cần chốt trước khi bước sang package system: **BOOTSTRAP-041 — FFI / Native Boundary Audit & Freeze**, vì mục tiêu Axiom là tự tạo EXE/ELF/Mach-O/iOS/Android/WASM và không phụ thuộc compiler/thư viện bên thứ ba. Phần này sẽ đóng toàn bộ biên giới giữa Axiom và C ABI, system ABI, shared/static library, syscall, callback, allocator và foreign ownership.