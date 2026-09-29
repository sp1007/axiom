# BOOTSTRAP-459 — GPU COMPUTING, DEVICE MEMORY, KERNEL MODEL, CPU↔GPU EXECUTION & ACCELERATOR ABSTRACTION

**Trạng thái: COMPLETED / LOCKED**

Mục tiêu của 459 là đưa GPU/accelerator vào Axiom như **một execution target native**, không biến GPU thành thành phần bắt buộc của language core hoặc runtime.

Kiến trúc tổng thể:

```text
Axiom Language
      │
      ├── CPU execution
      │
      └── Accelerator API
             │
             ├── GPU
             ├── NPU
             └── future accelerator
                    │
              Device Backend
                    │
       ┌────────────┼────────────┐
       │            │            │
     CUDA         HIP          Metal
       │            │            │
     Vulkan      OpenCL       DirectX
       │
   future native
   Axiom GPU backend
```

Axiom phải cho phép xây dựng GPU runtime/library bằng chính Axiom về lâu dài, nhưng **459 không yêu cầu compiler GPU đầu tiên phải tự hỗ trợ mọi vendor backend**.

---

## 459.1 — Accelerator abstraction

Accelerator là execution device có:

```text id="xq4w8c"
compute capability
memory
queues
command submission
synchronization
kernel execution
```

---

## 459.2 — Device

Conceptual API:

```text id="xw1q4r"
Device
DeviceInfo
DeviceKind
DeviceFeatures
DeviceLimits
```

---

## 459.3 — Device kinds

Foundation cho:

```text id="7u2h5k"
CPU
GPU
NPU
DSP
FPGA
OTHER
```

459 tập trung GPU nhưng abstraction không khóa vào GPU.

---

## 459.4 — Device discovery

Runtime/library có thể enumerate devices.

---

## 459.5 — Device selection

Application chọn device explicit.

Không có implicit GPU selection làm thay đổi semantics.

---

## 459.6 — Device capabilities

Capability query:

```text id="h8c2pq"
max_workgroup_size
max_threads
memory_size
shared_memory_size
subgroup_size
supported_formats
supported_features
```

---

## 459.7 — Capability-driven compilation

Kernel có thể yêu cầu capability cụ thể.

Compiler phải reject target không đáp ứng capability.

---

## 459.8 — Device limits

Limits phải được query runtime.

Không hard-code giới hạn GPU trong language semantics.

---

## 459.9 — Device identity

Device có stable runtime identifier trong phạm vi execution environment.

---

## 459.10 — Multiple GPUs

Một process có thể sử dụng nhiều device.

---

# 459.11 — Device context

Context quản lý:

```text id="4v6v0j"
device
resources
queues
command objects
allocator/provider state
```

---

## 459.12 — Context ownership

Context là resource-owning object theo 423.

---

## 459.13 — Queue

Queue đại diện execution stream/command submission channel.

---

## 459.14 — Queue ordering

Một queue mặc định đảm bảo thứ tự submission theo API contract.

---

## 459.15 — Independent queues

Nhiều queue có thể chạy song song nếu device hỗ trợ.

---

## 459.16 — Queue synchronization

Synchronization giữa queue phải explicit.

---

## 459.17 — Command buffer

Commands có thể được record trước khi submit.

---

## 459.18 — Command buffer ownership

Command buffer có deterministic lifetime.

---

## 459.19 — Command submission

Submission trả về handle/event/fence tùy backend.

---

## 459.20 — No hidden submission

Compiler không tự submit GPU work khi application chưa yêu cầu.

---

# 459.21 — GPU memory model

Device memory được xem là **explicit resource**.

Không coi GPU memory là ordinary CPU heap.

---

## 459.22 — Memory domains

Foundation hỗ trợ:

```text id="6q8m9f"
Host
Device
Shared
Unified
Managed
```

---

## 459.23 — Device allocation

Conceptual:

```text id="w8k3ye"
DeviceBuffer<T>
```

---

## 459.24 — Device buffer ownership

`DeviceBuffer<T>` sở hữu device allocation.

Drop giải phóng resource theo 423.

---

## 459.25 — Device view

Non-owning:

```text id="m6s1q2"
DeviceSlice<T>
```

---

## 459.26 — Device pointer

Device address không mặc định được dùng như CPU pointer.

---

## 459.27 — Address-space distinction

Compiler/IR phải phân biệt:

```text id="x5d7kp"
HostPtr<T>
DevicePtr<T>
SharedPtr<T>
```

nếu target cần distinction.

---

## 459.28 — Pointer provenance

GPU pointer provenance tuân thủ 445.

---

## 459.29 — Device pointer arithmetic

Chỉ được thực hiện trong valid device address space.

---

## 459.30 — Raw device pointer

Raw device pointer operations là unsafe.

---

# 459.31 — Host memory

Host memory sử dụng ownership/allocator 423.

---

## 459.32 — Pinned host memory

Pinned allocation là explicit resource.

---

## 459.33 — Pageable host memory

Ordinary host allocation không tự động trở thành pinned memory.

---

## 459.34 — Shared memory

Shared/unified memory phải có explicit capability.

---

## 459.35 — Coherence

Memory coherence semantics phụ thuộc memory type/backend và phải được API mô tả rõ.

---

## 459.36 — No assumed coherence

Axiom không giả định CPU và GPU luôn nhìn thấy memory changes ngay lập tức.

---

## 459.37 — Memory synchronization

Visibility phải follow explicit synchronization contract.

---

## 459.38 — Memory copy

Explicit operations:

```text id="4j8c6h"
copy_to_device
copy_to_host
copy_device_to_device
```

---

## 459.39 — Copy async

Async copies có thể được submit vào queue.

---

## 459.40 — Copy completion

Application có thể await/poll event/fence.

---

# 459.41 — Zero-copy

Zero-copy được hỗ trợ khi backend/device capability cho phép.

---

## 459.42 — Zero-copy is optimization

Zero-copy không thay đổi ownership semantics.

---

## 459.43 — Unified memory

Unified memory là explicit allocation strategy.

---

## 459.44 — Managed memory

Managed memory provider chịu trách nhiệm migration/paging nếu backend hỗ trợ.

---

## 459.45 — Explicit prefetch

Managed memory có thể hỗ trợ explicit prefetch.

---

## 459.46 — Memory residency

Residency có thể được query hoặc controlled khi backend cho phép.

---

## 459.47 — Memory mapping

Mapping device memory vào host là capability-dependent.

---

## 459.48 — Device memory alignment

Allocation phải đáp ứng alignment requirements của target.

---

## 459.49 — Device memory size

Size được kiểm tra trước allocation hoặc trả allocation error.

---

## 459.50 — OOM

Device OOM trả typed error.

Không mặc định panic.

---

# 459.51 — Kernel

Kernel là function có execution domain accelerator.

Conceptual:

```text id="c6m2r8"
kernel fn add(a: DeviceSlice<f32>, b: DeviceSlice<f32>, out: DeviceSlice<f32>)
```

---

## 459.52 — Kernel type

Kernel không phải ordinary CPU function.

---

## 459.53 — Kernel invocation

CPU submit kernel thông qua queue/command API.

---

## 459.54 — Kernel arguments

Kernel arguments phải có device-compatible representation.

---

## 459.55 — Kernel ABI

Kernel ABI là ABI riêng của accelerator backend.

---

## 459.56 — Kernel ABI metadata

446 phải expose:

```text id="h2v6tq"
arguments
address spaces
alignment
required features
workgroup constraints
```

---

## 459.57 — Kernel return

Kernel không mặc định return ordinary CPU value.

Kết quả thông thường đi qua:

```text id="6h9zq3"
device memory
event/status
```

---

## 459.58 — Kernel error

Kernel launch/runtime failure trả event/status.

---

## 459.59 — Device-side failure

Backend-specific execution failures phải được surface thành typed diagnostic/error.

---

## 459.60 — Kernel panic

Kernel không được mặc định sử dụng CPU panic/unwind machinery.

---

# 459.61 — Kernel compilation

Kernel được compile cho target accelerator.

---

## 459.62 — Separate target

GPU target là target riêng trong compiler.

---

## 459.63 — Host + device compilation

Một source package có thể chứa:

```text id="t1k9y4"
host code
device code
```

---

## 459.64 — Compilation graph

Compiler build graph phải biểu diễn:

```text id="n3b5k7"
host artifact
device artifact
kernel metadata
binding metadata
```

---

## 459.65 — Kernel specialization

Comptime 431 có thể specialize kernel theo:

```text id="6w3m8a"
data type
tile size
device capability
constant dimensions
```

---

## 459.66 — Kernel generics

Kernel có thể dùng generic type/const parameters nếu backend hỗ trợ.

---

## 459.67 — Monomorphization

Generic kernels được specialize tương tự generic CPU functions.

---

## 459.68 — Code-size control

Compiler phải tránh tạo hàng nghìn kernel variants vô tình.

---

## 459.69 — Explicit specialization

Developer có thể giới hạn supported variants.

---

## 459.70 — Cache

Compiled kernels phải được cache theo:

```text id="d9s4jk"
source semantic hash
dependencies
compiler version
device target
features
specialization constants
```

---

# 459.71 — Kernel execution model

Axiom abstraction sử dụng mô hình:

```text id="4f6q2p"
Grid
  └── Workgroups
        └── Threads/Lanes
              └── Subgroups/Waves
```

Backend có thể map sang vendor terminology.

---

## 459.72 — Global ID

Kernel có API lấy global invocation ID.

---

## 459.73 — Local ID

Kernel có local/workgroup ID.

---

## 459.74 — Group ID

Kernel có workgroup ID.

---

## 459.75 — Global dimensions

1D/2D/3D dispatch.

---

## 459.76 — Local dimensions

Workgroup dimensions được explicit.

---

## 459.77 — Dispatch

Conceptual:

```text id="d4q5x7"
dispatch(kernel, grid, workgroup)
```

---

## 459.78 — Runtime workgroup

Runtime-selected workgroup size được hỗ trợ khi backend cho phép.

---

## 459.79 — Static workgroup

Compile-time fixed workgroup size có thể giúp optimizer.

---

## 459.80 — Workgroup limits

Compiler/runtime validate against device limits.

---

# 459.81 — Subgroups

GPU backend có abstraction cho subgroup/wave/warp.

---

## 459.82 — Subgroup size

Có thể runtime-query hoặc compile-time known tùy backend.

---

## 459.83 — Subgroup operations

Possible operations:

```text id="w9r3n6"
broadcast
shuffle
ballot
vote
reduce
scan
```

---

## 459.84 — Portability

Code không được assume subgroup size cố định trừ khi target contract yêu cầu.

---

## 459.85 — Vendor warp semantics

Vendor-specific warp APIs nằm ở backend-specific namespace.

---

# 459.86 — Kernel local memory

Workgroup/shared memory là explicit resource.

---

## 459.87 — Shared memory declaration

Conceptual:

```text id="m3f8c1"
shared<T, N>
```

---

## 459.88 — Shared memory lifetime

Lifetime bằng execution của workgroup.

---

## 459.89 — Shared memory visibility

Visibility giữa lanes cần barrier/synchronization phù hợp.

---

## 459.90 — Shared memory size

Compiler/runtime phải validate against device limit.

---

## 459.91 — Private memory

Per-invocation locals thuộc private address space.

---

## 459.92 — Constant memory

Backend có thể map read-only data vào constant/uniform memory.

---

## 459.93 — Read-only memory

Kernel có thể mark read-only buffers để optimizer tận dụng.

---

## 459.94 — Restrict/noalias

Explicit alias contracts có thể cho phép optimization.

---

## 459.95 — Alias safety

Compiler không tự suy diễn `noalias` nếu không chứng minh được.

---

# 459.96 — GPU synchronization

Synchronization gồm:

```text id="h3r6q8"
workgroup barrier
subgroup synchronization
device fence
queue synchronization
event
host wait
```

---

## 459.97 — Workgroup barrier

Barrier đồng bộ invocations trong workgroup.

---

## 459.98 — Barrier legality

Barrier placement phải tuân thủ backend execution rules.

---

## 459.99 — Divergent barrier

Compiler phải detect hoặc reject barrier usage không hợp lệ khi target semantics yêu cầu uniform control flow.

---

## 459.100 — Memory barrier

Memory visibility và execution synchronization được phân biệt.

---

# 459.101 — GPU atomics

GPU hỗ trợ atomic operations tương ứng target.

---

## 459.102 — Atomic types

Các integer widths được backend hỗ trợ.

---

## 459.103 — Atomic memory ordering

GPU memory ordering có thể khác CPU 424.

Axiom phải biểu diễn semantic ordering và lower theo backend.

---

## 459.104 — Atomic scope

Có thể có scope:

```text id="5z2q8f"
subgroup
workgroup
device
system
```

---

## 459.105 — Scope portability

Không phải mọi backend hỗ trợ mọi scope.

---

## 459.106 — Unsupported atomic

Compiler báo lỗi thay vì silently emulate nếu semantics yêu cầu capability không tồn tại.

---

## 459.107 — Atomic float

Optional capability.

---

## 459.108 — Compare-exchange

CAS semantics phải explicit.

---

## 459.109 — Lock-free assumption

Không mặc định atomic operation là lock-free.

---

## 459.110 — GPU race safety

Safe GPU API phải hạn chế các memory races có thể chứng minh được; low-level raw kernels có thể yêu cầu explicit unsafe/capability contract.

---

# 459.111 — GPU unsafe boundary

Kernel code có thể đánh dấu:

```text id="c5m7w2"
unsafe
```

cho low-level operations.

---

## 459.112 — Unsafe kernel

Unsafe không vô hiệu hóa type checking.

---

## 459.113 — Device pointer dereference

Raw device pointer dereference là unsafe.

---

## 459.114 — Out-of-bounds

Safe device buffer indexing phải bounds-check hoặc được compiler chứng minh an toàn.

---

## 459.115 — Bounds elimination

Optimizer có thể loại bỏ bounds checks.

---

## 459.116 — Race contracts

Kernel APIs có thể express contracts về disjoint regions.

---

## 459.117 — Ownership of kernel arguments

Device buffers passed to kernel phải obey lifetime until execution completion.

---

## 459.118 — Lifetime enforcement

Compiler/library API phải ngăn release resource trước khi dependent command hoàn tất trong safe abstraction.

---

## 459.119 — Explicit unsafe escape

Developer có thể bypass tracking bằng unsafe.

---

## 459.120 — Async ownership

Async command dependencies được tích hợp với ownership model.

---

# 459.121 — GPU events

Event biểu diễn completion/dependency point.

---

## 459.122 — Event states

Conceptual:

```text id="7u4j3k"
Pending
Complete
Failed
```

---

## 459.123 — Event wait

CPU có thể await event.

---

## 459.124 — Event polling

Non-blocking poll được hỗ trợ.

---

## 459.125 — Event chaining

Một GPU command có thể depend trên event khác.

---

## 459.126 — Cross-queue dependency

Supported khi backend cho phép.

---

## 459.127 — Cross-device dependency

Không assume direct dependency giữa devices.

---

## 459.128 — CPU dependency

CPU task có thể depend trên GPU completion.

---

## 459.129 — GPU dependency

GPU command có thể depend trên previous GPU/host-visible synchronization primitive khi backend hỗ trợ.

---

## 459.130 — No implicit blocking

GPU API không được âm thầm block CPU trừ API được định nghĩa là blocking.

---

# 459.131 — GPU async integration

GPU execution tích hợp với 424.

---

## 459.132 — Async submit

Conceptual:

```text id="8q5j1v"
await queue.submit(...)
```

---

## 459.133 — Async transfer

Memory transfer có thể là Future.

---

## 459.134 — Async kernel

Kernel completion có thể được await.

---

## 459.135 — Cancellation

Submitted GPU work cancellation phụ thuộc backend.

---

## 459.136 — Cancellation semantics

Axiom không giả định mọi GPU command có thể cancel.

---

## 459.137 — Cancellation request

Nếu backend không cancel được, cancellation chỉ ngăn awaiting task tiếp tục chứ không necessarily stop device execution.

---

## 459.138 — Resource cleanup

Dropped async GPU resources follow completion dependency.

---

## 459.139 — Executor independence

GPU API không yêu cầu một executor cụ thể.

---

## 459.140 — Blocking GPU APIs

Synchronous convenience APIs có thể tồn tại và được đánh dấu `@blocking`.

---

# 459.141 — Command graph

GPU workload có thể được biểu diễn thành dependency graph:

```text id="f2q7m1"
upload
   ↓
kernel A
   ↓
kernel B ──→ copy
   ↓
kernel C
```

---

## 459.142 — Graph optimization

Runtime có thể reorder independent commands khi semantics cho phép.

---

## 459.143 — Graph capture

Backend có thể hỗ trợ command graph capture.

---

## 459.144 — Graph compilation

Repeated graph có thể được compile/cache.

---

## 459.145 — Graph specialization

Static shapes/constants có thể specialize graph.

---

## 459.146 — Graph ownership

Graph owns referenced commands/resources or explicit dependency handles.

---

## 459.147 — Graph lifetime

Graph không được outlive required resources.

---

## 459.148 — Graph execution

Graph submission returns completion handle.

---

## 459.149 — Graph failure

Failure identifies node/resource where backend can provide it.

---

## 459.150 — Graph portability

Graph is optional abstraction; simple queue submission remains fundamental.

---

# 459.151 — CPU/GPU synchronization contract

CPU writes:

```text id="9z2q4c"
CPU write
   ↓
transfer/visibility operation
   ↓
GPU read
```

GPU writes:

```text id="v4m8p2"
GPU write
   ↓
completion/visibility
   ↓
CPU read
```

---

## 459.152 — Synchronization visibility

Completion is not automatically equivalent to every possible cache-coherency guarantee; backend memory model defines required operations.

---

## 459.153 — Host read before completion

Safe abstraction must reject/await such access.

---

## 459.154 — Host write during GPU use

Safe abstraction must prevent conflicting mutable access.

---

## 459.155 — Read-only concurrent access

Concurrent read-only access may be allowed.

---

## 459.156 — Multiple queues

Mutable access across queues requires explicit dependency.

---

## 459.157 — Memory ownership state

Runtime/resource layer may track:

```text id="g8f3q5"
HostOwned
DeviceOwned
Shared
InFlight
```

---

## 459.158 — In-flight resource

Resource cannot be destroyed while command references it.

---

## 459.159 — Reference counting

Internal runtime may use reference counting for asynchronous resource tracking, but this is not language-level GC.

---

## 459.160 — Deterministic resource completion

Public ownership semantics remain deterministic.

---

# 459.161 — Kernel language subset

Kernel code must use a GPU-compatible subset.

---

## 459.162 — Unsupported features

Depending on backend, kernels may not use:

```text id="5r9c2n"
OS I/O
filesystem
threads
dynamic library loading
arbitrary syscalls
CPU runtime APIs
```

---

## 459.163 — Heap allocation

Kernel heap allocation is not assumed.

---

## 459.164 — Kernel allocation

If target supports device allocation, it must be explicit.

---

## 459.165 — Recursion

Kernel recursion is disabled by default unless target/compiler proves/supports it.

---

## 459.166 — Function calls

Static function calls within kernels are supported.

---

## 459.167 — Dynamic dispatch

`dyn Trait` is not assumed available in kernels.

---

## 459.168 — Generic kernels

Generics can be monomorphized.

---

## 459.169 — Comptime kernel configuration

Preferred mechanism for static configuration.

---

## 459.170 — Exceptions

Kernel exceptions/unwind are not supported by default.

---

# 459.171 — Kernel control flow

Normal:

```text id="8s2k6v"
if
match
loop
while
for
```

may be supported where backend permits.

---

## 459.172 — Divergence

Compiler understands divergent control flow for optimization/legal synchronization.

---

## 459.173 — Branch optimization

Backend may use predication or native branch based on target.

---

## 459.174 — Uniformity analysis

Compiler should track values known uniform across workgroup/subgroup when useful.

---

## 459.175 — Divergence metadata

446 exposes divergence analysis where available.

---

## 459.176 — Barrier analysis

Compiler uses divergence information to validate barriers.

---

## 459.177 — Loop optimization

GPU loops use target-specific cost models.

---

## 459.178 — Unrolling

Compile-time/static loops may be unrolled.

---

## 459.179 — Tile loops

Comptime can generate tiled kernels.

---

## 459.180 — Specialization constants

Runtime specialization constants may be supported by backend.

---

# 459.181 — GPU SIMD/SIMT

Axiom does not equate SIMD and SIMT.

---

## 459.182 — Vector type in kernel

`vec<T,N>` remains explicit SIMD value.

---

## 459.183 — Invocation parallelism

Kernel invocation parallelism is separate from vector operations.

---

## 459.184 — Subgroup vectorization

Backend may combine vector and subgroup execution.

---

## 459.185 — Portable semantics

Program semantics remain independent of warp/wave implementation.

---

## 459.186 — Warp size assumptions

Must be explicit target contract.

---

## 459.187 — Occupancy

Occupancy is optimization concern, not language semantic.

---

## 459.188 — Register pressure

Compiler may expose register-pressure diagnostics.

---

## 459.189 — Shared memory pressure

Compiler may expose shared-memory usage.

---

## 459.190 — Kernel resource report

AI tooling can query:

```text id="e3v8x2"
register usage
shared memory
threads/workgroup
binary size
required features
```

---

# 459.191 — Shader vs compute

Axiom distinguishes:

```text id="x2k5q8"
compute kernel
vertex shader
fragment/pixel shader
geometry/tessellation where supported
```

---

## 459.192 — Graphics shader

Graphics shader support belongs graphics subsystem.

---

## 459.193 — Compute foundation

Compute kernels use 459.

---

## 459.194 — Shader I/O

Graphics subsystem defines stage inputs/outputs.

---

## 459.195 — Uniforms

Uniform/resource binding metadata is explicit.

---

## 459.196 — Resource binding

Bindings must be represented in compiled metadata.

---

## 459.197 — Descriptor abstraction

Axiom may provide backend-neutral resource binding abstraction.

---

## 459.198 — Descriptor layout

Backend validates descriptor/resource compatibility.

---

## 459.199 — Texture

Texture is graphics library resource, not generic `DeviceBuffer`.

---

## 459.200 — Sampler

Sampler is explicit GPU resource.

---

# 459.201 — GPU compilation backends

Initial architecture permits:

```text id="j5k8s3"
SPIR-V
DXIL
Metal shader representation
CUDA/PTX
HIP
OpenCL
```

depending backend.

---

## 459.202 — Backend independence

Axiom semantic GPU IR must not directly encode one vendor API.

---

## 459.203 — GPU IR

Introduce:

```text id="p4n8r2"
Axiom GPU IR
```

between semantic lowering and vendor backend.

---

## 459.204 — GPU IR properties

GPU IR includes:

```text id="q8w5k3"
address spaces
workgroup operations
barriers
atomics
subgroups
resource bindings
specialization constants
```

---

## 459.205 — GPU IR validation

IR verifier validates:

- address spaces;
- barrier legality;
- types;
- resource access;
- atomics;
- unsupported operations.

---

## 459.206 — Lowering

```text
HIR
 ↓
GPU MIR
 ↓
GPU LIR
 ↓
Vendor/portable backend
```

---

## 459.207 — CPU/GPU shared frontend

Parser/type system/trait/comptime infrastructure is shared.

---

## 459.208 — Target-specific semantic validation

GPU restrictions are checked after target context is known.

---

## 459.209 — No separate language required

Axiom does not require a second source language for compute kernels.

---

## 459.210 — Backend replacement

A vendor backend can be replaced without changing Axiom kernel source semantics.

---

# 459.211 — External GPU APIs

Initial implementation may call vendor/system APIs through FFI 451.

---

## 459.212 — No compiler dependency

Using a GPU driver API at runtime is not equivalent to depending on an external compiler.

---

## 459.213 — Runtime backend

Axiom can ship a runtime backend that submits precompiled kernels.

---

## 459.214 — Driver dependency

GPU execution necessarily depends on the operating system/device driver where applicable.

---

## 459.215 — Native Axiom backend

Long-term Axiom can emit its own GPU intermediate/native artifact when target specification permits.

---

## 459.216 — CUDA compatibility

CUDA is an interoperability target, not a language requirement.

---

## 459.217 — Metal compatibility

Metal is an interoperability target, not a language requirement.

---

## 459.218 — Vulkan compatibility

Vulkan compute is a backend/interoperability target.

---

## 459.219 — DirectX compatibility

DirectX compute is a backend/interoperability target.

---

## 459.220 — Backend abstraction

All external backends implement common device/kernel/queue/memory contracts.

---

# 459.221 — GPU error model

Errors divide into:

```text id="7q3m5n"
compile-time
device-discovery
allocation
submission
execution
synchronization
resource
driver/backend
```

---

## 459.222 — Compile errors

Unsupported kernel constructs are compile-time errors.

---

## 459.223 — Capability errors

Missing device capability returns typed error.

---

## 459.224 — Allocation errors

Device allocation failure returns `Result`.

---

## 459.225 — Submission errors

Queue submission can fail before execution.

---

## 459.226 — Execution errors

Async event can transition to Failed.

---

## 459.227 — Device loss

Device loss is recoverable only if backend permits; API must represent it explicitly.

---

## 459.228 — Timeout

Timeout is separate from execution failure.

---

## 459.229 — No hidden panic

GPU failure does not automatically panic ordinary user code.

---

## 459.230 — Debug mode

Debug builds may add validation layers/instrumentation.

---

# 459.231 — GPU debugging

Compiler/runtime supports:

```text id="4s8m2q"
kernel source mapping
device stack/source information where supported
resource tracking
dispatch tracing
```

---

## 459.232 — Kernel source mapping

GPU machine/IR instructions map back to Axiom source.

---

## 459.233 — Debug symbols

GPU debug metadata is separate artifact.

---

## 459.234 — Debug validation

Optional runtime validates:

```text id="7m3k9v"
buffer bounds
resource binding
synchronization
device capabilities
```

---

## 459.235 — Sanitization

GPU sanitizer/debug instrumentation is backend-specific.

---

## 459.236 — Race detection

GPU race detection is optional tooling.

---

## 459.237 — Profiling

Profiler can capture:

```text id="n5q8x1"
kernel duration
transfer duration
queue idle time
memory throughput
occupancy
```

---

## 459.238 — Timeline

CPU/GPU events share timestamp correlation when backend supports it.

---

## 459.239 — AI diagnostics

446 exposes GPU performance/debug metadata.

---

## 459.240 — Optimization query

AI tooling can query:

```text id="r2x6k9"
why is kernel slow?
why was occupancy reduced?
why wasn't shared memory used?
why was vectorization rejected?
```

---

# 459.241 — Tensor integration

Tensor library from 458 may use:

```text id="j3q7v5"
CPU memory
GPU memory
shared memory
```

---

## 459.242 — Tensor device type

Conceptual:

```text id="n6p4s8"
Tensor<T, Shape, Device>
```

---

## 459.243 — Device transfer

Explicit:

```text id="a5v9k2"
tensor.to(device)
```

---

## 459.244 — Async tensor transfer

Can return Future.

---

## 459.245 — Kernel-backed tensor operations

Tensor library can dispatch Axiom kernels.

---

## 459.246 — Vendor libraries

BLAS/cuBLAS/rocBLAS/Metal Performance Shaders/etc. can be optional providers through FFI.

---

## 459.247 — Provider abstraction

High-level tensor operation can choose:

```text id="w8k4q6"
Axiom kernel
vendor library
CPU implementation
```

without changing public semantics.

---

## 459.248 — Provider selection

Provider selection is explicit/configurable.

---

## 459.249 — No hidden GPU

High-level library must not silently move data to GPU unless API explicitly permits automatic placement.

---

## 459.250 — Explicit device policy

Applications can choose:

```text id="u4n7m2"
CPU
GPU
AUTO
```

at library layer.

---

# 459.251 — Multi-GPU

Multiple devices can be represented independently.

---

## 459.252 — Peer-to-peer

P2P transfer is optional capability.

---

## 459.253 — Device topology

Runtime can expose device topology.

---

## 459.254 — Device affinity

Work can be explicitly assigned to a device.

---

## 459.255 — Multi-device synchronization

Cross-device events require backend support.

---

## 459.256 — Distributed GPU

Distributed multi-node GPU is outside core 459.

---

## 459.257 — CPU affinity

CPU worker affinity follows 424/441.

---

## 459.258 — NUMA + GPU

NUMA-aware GPU allocation belongs platform/runtime layer.

---

## 459.259 — Unified scheduler

A higher-level scheduler may coordinate CPU/GPU tasks.

---

## 459.260 — Scheduler is library-level

No mandatory global scheduler.

---

# 459.261 — GPU memory allocator

Allocator abstraction follows 423.

---

## 459.262 — Device allocator

Conceptual:

```text id="s5n8q2"
DeviceAllocator
```

---

## 459.263 — Memory pool

GPU memory pools are optional optimization.

---

## 459.264 — Arena

Arena-style device allocation can be implemented.

---

## 459.265 — Suballocation

Runtime can suballocate large device blocks.

---

## 459.266 — Fragmentation

Allocator can use pools/segregated blocks to reduce fragmentation.

---

## 459.267 — Defragmentation

Moving device allocations requires explicit ownership/synchronization.

---

## 459.268 — Memory compaction

Not automatic language behavior.

---

## 459.269 — Allocation telemetry

Runtime can expose allocation statistics.

---

## 459.270 — Binary size

GPU capability code is linked/pruned independently.

---

# 459.271 — Kernel ABI and FFI

External kernels may be imported.

---

## 459.272 — External kernel metadata

Imported kernels require explicit:

```text id="j6r2w8"
argument types
binding
address spaces
workgroup requirements
ABI
```

---

## 459.273 — Foreign kernel safety

Unknown foreign kernels are unsafe/untrusted boundaries.

---

## 459.274 — Kernel ownership annotations

External kernel APIs can express resource ownership requirements.

---

## 459.275 — Callback

GPU completion callbacks must obey 424 foreign-thread/reentrancy rules.

---

## 459.276 — Device handles

Foreign device handles use owned/borrowed/raw semantics.

---

## 459.277 — Handle conversion

Raw handle conversion is unsafe.

---

## 459.278 — Backend ABI version

Runtime/backend compatibility must be versioned.

---

## 459.279 — Driver ABI

Driver ABI is platform/backend concern.

---

## 459.280 — Semantic metadata

GPU ABI/resource metadata integrates with 446.

---

# 459.281 — Security

GPU inputs are potentially untrusted.

---

## 459.282 — Bounds validation

Safe GPU APIs enforce resource bounds.

---

## 459.283 — Driver boundary

GPU driver is external trust boundary according to 445.

---

## 459.284 — Kernel isolation

GPU kernel does not gain arbitrary OS access merely because it is native.

---

## 459.285 — Device reset

Application must handle device reset/loss.

---

## 459.286 — Resource limits

GPU applications should enforce memory/dispatch limits for untrusted workloads.

---

## 459.287 — Shader sandbox

Browser/WASM/WebGPU environments provide their own sandbox model.

---

## 459.288 — Native GPU

Native GPU execution is not considered sandboxed.

---

## 459.289 — JIT kernels

Runtime-generated GPU code requires explicit executable-code capability.

---

## 459.290 — W^X

Executable device code follows backend/platform security policy.

---

# 459.291 — Build model

Package can declare:

```text id="m7q4v8"
host targets
device targets
required features
kernel artifacts
```

---

## 459.292 — Cross compilation

Host compiler can build device artifacts for another accelerator target.

---

## 459.293 — Offline build

Precompiled kernels may be packaged.

---

## 459.294 — Source distribution

Source packages can include kernel source.

---

## 459.295 — Binary distribution

Binary packages can include target-specific kernel artifacts.

---

## 459.296 — Kernel cache

Cache identity follows 431/432/446.

---

## 459.297 — Reproducibility

Kernel compilation should be deterministic given identical compiler/backend inputs.

---

## 459.298 — Backend version

Backend/compiler version participates in artifact identity.

---

## 459.299 — Device-specific compilation

Runtime JIT specialization may produce separately cached artifacts.

---

## 459.300 — Artifact provenance

GPU artifacts record source/compiler/backend/device-target provenance.

---

# 459.301 — Freestanding

Axiom can compile GPU kernels without CPU standard runtime.

---

## 459.302 — Embedded accelerator

The same abstraction can represent embedded accelerators.

---

## 459.303 — OS independence

GPU semantic IR does not require an OS.

---

## 459.304 — Driver-free theoretical target

Axiom's accelerator abstraction does not require a particular host driver architecture.

---

## 459.305 — Runtime-free kernel

A GPU kernel itself should avoid dependence on Axiom host runtime.

---

## 459.306 — Minimal kernel ABI

Kernel artifact contains only required device code/metadata.

---

## 459.307 — Host runtime separation

Host application may omit GPU runtime entirely if no GPU feature is used.

---

## 459.308 — Feature linking

GPU libraries are linked only when referenced.

---

## 459.309 — Dead GPU code elimination

Unused kernels/device providers can be removed.

---

## 459.310 — Binary-size contract

Ordinary CPU programs must not acquire GPU runtime merely because Axiom supports GPU.

---

# 459.311 — AI-friendly GPU metadata

Compiler records:

```text id="r8m4x1"
kernel
device target
resource arguments
memory spaces
required features
dispatch shape
workgroup shape
shared memory
register usage
synchronization
atomic operations
host/device dependencies
```

---

## 459.312 — Dependency graph

AI can query:

```text id="q5n7z2"
which CPU function launches this kernel?
which buffer feeds this kernel?
which kernels depend on this buffer?
```

---

## 459.313 — Memory graph

Compiler/tooling can expose:

```text id="h4s9p6"
HostBuffer
   ↓ transfer
DeviceBuffer
   ↓
Kernel
   ↓
DeviceBuffer
   ↓ transfer
HostBuffer
```

---

## 459.314 — Synchronization graph

AI tooling can inspect dependency and synchronization edges.

---

## 459.315 — Capability graph

Tooling can query why a kernel requires a particular GPU feature.

---

## 459.316 — Optimization graph

Kernel performance diagnostics integrate with 450.

---

## 459.317 — Build graph

Host/device artifacts integrate with 432.

---

## 459.318 — Debug graph

Kernel source mapping integrates with 440.

---

## 459.319 — Security graph

Device unsafe operations integrate with 445.

---

## 459.320 — Semantic graph

GPU semantics integrate with 446.

---

# 459.321 — GPU testing

Tests include:

```text id="x8q3m5"
kernel correctness
memory transfer
synchronization
atomicity
device capability
multi-queue
multi-device
```

---

## 459.322 — CPU reference implementation

Every portable kernel should ideally have a CPU reference implementation for testing where practical.

---

## 459.323 — Differential testing

GPU result can be compared against CPU reference.

---

## 459.324 — Floating tolerance

GPU floating results may use explicit tolerance.

---

## 459.325 — Deterministic kernels

Kernels requiring deterministic output must avoid uncontrolled race/order dependence.

---

## 459.326 — Race tests

Intentional race tests belong unsafe/debug test suite.

---

## 459.327 — Memory tests

Boundary and alignment tests required.

---

## 459.328 — Device matrix

CI should test available representative backends.

---

## 459.329 — Backend conformance

Every backend must satisfy common semantic test suite.

---

## 459.330 — Missing hardware

Tests must support capability-based skipping without silently marking unsupported semantics as passed.

---

# 459.331 — GPU benchmarking

Measure separately:

```text id="e7k2p4"
kernel latency
kernel throughput
transfer latency
transfer bandwidth
end-to-end latency
memory usage
compilation time
binary size
```

---

## 459.332 — Transfer-aware benchmark

GPU benchmark must distinguish kernel-only from end-to-end performance.

---

## 459.333 — Warmup

JIT/cache warmup must be reported separately.

---

## 459.334 — Cold-start

Cold compilation/startup benchmark is separate.

---

## 459.335 — Synchronization cost

Synchronization overhead must be measurable.

---

## 459.336 — CPU baseline

Relevant GPU workloads should include CPU baseline.

---

## 459.337 — No aggregate score

450's rule remains: do not collapse unrelated metrics into a universal performance score.

---

## 459.338 — Correctness gate

Performance result is invalid if output correctness fails.

---

## 459.339 — Device record

Benchmark records GPU model/driver/backend/features.

---

## 459.340 — AI benchmark analysis

AI tooling can correlate:

```text id="v3m6q8"
source
kernel
IR
device
runtime timeline
performance
```

---

# 459.341 — Initial implementation strategy

**Stage 1**

CPU-side API:

```text id="k4x8s2"
Device
Buffer
Queue
Event
Kernel
```

with one backend.

---

## 459.342 — Stage 2

Add:

```text id="u6p3n9"
device memory
async copy
kernel dispatch
basic synchronization
```

---

## 459.343 — Stage 3

Add Axiom GPU IR.

---

## 459.344 — Stage 4

Add portable/vendor backends.

---

## 459.345 — Stage 5

Add kernel optimization:

```text id="m8q2r5"
constant folding
inlining
vectorization
tiling
shared-memory optimization
register allocation
```

---

## 459.346 — Stage 6

Add profiler/debugger integration.

---

## 459.347 — Stage 7

Add tensor/ML integration.

---

## 459.348 — Stage 8

Add native Axiom-authored accelerator runtime/backend where practical.

---

## 459.349 — Stage 9

Add multi-GPU scheduling/library abstractions.

---

## 459.350 — Stage 10

Validate against complete Axiom compiler/bootstrap pipeline.

---

# 459.351 — Hard invariants

1. GPU is not part of mandatory language runtime.
2. CPU-only programs do not link GPU runtime automatically.
3. Accelerator abstraction is not vendor-specific.
4. GPU is an execution target, not a separate programming language requirement.
5. Device is an explicit resource.
6. Device ownership follows 423.
7. Device memory is explicit.
8. Host/device address spaces are distinguishable where required.
9. Raw device pointers are unsafe.
10. Device buffers have deterministic lifetime.
11. GPU resources cannot safely be destroyed while in-flight commands depend on them.
12. CPU/GPU synchronization is explicit.
13. Memory coherence is never assumed universally.
14. Host/device transfers are explicit unless an explicit higher-level abstraction chooses otherwise.
15. Zero-copy is an optimization/capability, not semantic requirement.
16. Unified/managed memory is explicit.
17. Device OOM is typed failure.
18. Queue submission is explicit.
19. GPU APIs do not silently block.
20. Async GPU operations integrate with 424.
21. GPU cancellation semantics are explicit.
22. Kernel is distinct from ordinary CPU function.
23. Kernel ABI is separate from CPU ABI.
24. Kernel arguments have explicit device-compatible representation.
25. Kernel resource ownership is tracked.
26. Kernel bounds safety follows 445.
27. Unsafe kernel operations remain explicit.
28. Kernel execution failure is represented explicitly.
29. GPU panic/unwind is not mandatory.
30. Kernel heap allocation is not assumed.
31. Kernel OS APIs are unavailable unless target explicitly provides them.
32. Kernel generics use static specialization.
33. Kernel comptime uses 431.
34. Kernel code-size explosion must be controlled.
35. GPU dispatch supports explicit grid/workgroup dimensions.
36. Workgroup limits are target capability.
37. Subgroup semantics are distinct from SIMD.
38. Warp/wave size cannot be assumed portably.
39. Divergent barrier usage must be detected where required.
40. GPU atomics obey target-supported memory/scope semantics.
41. Atomic support is capability-dependent.
42. GPU race freedom is not magically guaranteed for arbitrary unsafe kernels.
43. Command dependencies are explicit.
44. Events/fences represent completion explicitly.
45. CPU/GPU synchronization must integrate with ownership.
46. Command graphs are optional.
47. GPU IR is independent of a single vendor.
48. Host and device compilation share Axiom frontend infrastructure.
49. GPU backend is separate from CPU backend.
50. External GPU APIs are FFI/backend dependencies, not compiler dependencies.
51. Axiom can eventually implement GPU runtime/backend itself.
52. CUDA is optional.
53. HIP is optional.
54. Metal is optional.
55. Vulkan is optional.
56. DirectX is optional.
57. SPIR-V is an interoperability target, not the language semantic model.
58. Vendor-specific optimizations remain backend-specific.
59. GPU capabilities are queryable.
60. Device selection is explicit.
61. Multiple GPUs are supported by abstraction.
62. Peer-to-peer is optional.
63. GPU memory allocators follow 423.
64. GPU memory pools are optional.
65. Device defragmentation is never hidden.
66. Kernel compilation is cacheable.
67. Kernel artifact identity includes compiler/backend/target information.
68. GPU artifacts are reproducible when backend inputs are deterministic.
69. GPU artifacts carry provenance metadata.
70. GPU debug info is separate from release artifacts.
71. GPU source mapping integrates with 440.
72. GPU performance metadata integrates with 450.
73. GPU semantic metadata integrates with 446.
74. GPU security boundaries integrate with 445.
75. GPU package artifacts integrate with 447.
76. GPU build graph integrates with 432.
77. Tensor libraries may build on 459.
78. ML is not part of language core.
79. Vendor math libraries can be optional providers.
80. Automatic CPU↔GPU data movement is not hidden by default.
81. Device placement is explicit at low level.
82. Higher-level libraries may offer explicit `AUTO` policies.
83. CPU reference implementations should be used for correctness testing where practical.
84. GPU numerical correctness must account for floating-point differences.
85. Benchmarks separate transfer and kernel costs.
86. JIT warmup is reported separately.
87. GPU benchmark records hardware/backend/driver information.
88. No universal GPU performance score is defined.
89. Unsupported target capability produces explicit diagnostic.
90. GPU runtime may be entirely absent from a binary.
91. Freestanding GPU kernels do not require host runtime.
92. Embedded accelerators can reuse the abstraction.
93. Accelerator semantics must remain independent of OS.
94. No hidden GPU threads are introduced into CPU applications.
95. No hidden GPU allocation is introduced by ordinary CPU code.
96. No hidden GPU synchronization is introduced by ordinary CPU code.
97. AI tooling can inspect GPU memory/dependency/synchronization graphs.
98. AI tooling can query kernel resource usage and optimization decisions.
99. GPU code must remain compatible with Axiom ownership, error, type, ABI and metadata systems.
100. **Axiom's GPU model must provide a first-class path from ordinary high-performance CPU code to native accelerator kernels without sacrificing explicit ownership, predictable performance, portability, or the no-hidden-runtime principles established by the previous bootstrap tasks.**

**BOOTSTRAP-459 hoàn tất.**

---

# BOOTSTRAP-460 — GRAPHICS, RENDERING PIPELINE, GPU RESOURCE MODEL, SHADER SYSTEM & CROSS-PLATFORM 2D/3D FOUNDATION

Task kế tiếp sẽ xây tầng graphics trên 459:

```text
Axiom
 │
 ├── CPU
 │
 └── GPU / Accelerator
        │
        ├── Compute
        └── Graphics
               │
               ├── Buffer
               ├── Texture
               ├── Sampler
               ├── Shader
               ├── Pipeline
               ├── Render Pass
               ├── Command Buffer
               ├── Frame Graph
               └── Swapchain
```

460 sẽ khóa kiến trúc cho **2D + 3D rendering**, shader language/model, resource binding, render pipeline, frame graph, textures, meshes, materials, command recording, synchronization, swapchain, window integration, cross-platform graphics backend, compute/graphics interop, GPU-driven rendering, batching, instancing, indirect draw, ray tracing abstraction và nền tảng để sau này xây GUI/game/3D engine trên Axiom mà không nhét graphics vào language core.