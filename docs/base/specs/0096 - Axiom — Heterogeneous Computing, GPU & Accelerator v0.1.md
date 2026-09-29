Tiếp tục.

# Axiom — Heterogeneous Computing, GPU & Accelerator v0.1

Sau SIMD, đây là nơi cần **giữ kỷ luật kiến trúc**. Nếu đưa GPU vào Core quá sâu, Axiom sẽ biến thành một ngôn ngữ GPU. Nếu đẩy hết sang FFI, Axiom lại mất khả năng tối ưu và kiểm tra an toàn.

Tôi đề xuất ranh giới:

> **GPU execution là một execution domain; memory/address space là một semantic property; API GPU là library/platform layer.**

---

# 1. Không coi GPU là “CPU nhanh hơn”

CPU:

```text
thread
 └── function
      └── memory
```

GPU:

```text
device
 ├── kernel
 │    ├── workgroup
 │    │    ├── invocation
 │    │    └── invocation
 │    └── ...
 ├── device memory
 ├── shared/local memory
 └── synchronization
```

Vì vậy:

```text
fn
```

và:

```text
kernel
```

không nên bị đánh đồng.

---

# 2. Kernel nên là execution annotation

Có thể có:

```axiom
@kernel
fn add(
    input: view<f32>,
    output: mut_view<f32>
) {
    let i = gpu.global_id_x()

    if i < input.len() {
        output[i] = input[i] * 2.0
    }
}
```

Nhưng:

```text
@kernel
```

không nên tạo một ngôn ngữ con riêng.

Nó nói:

> Hàm này có thể được compile cho một execution target khác.

---

# 3. GPU backend không nhất thiết phải hiểu toàn bộ Axiom

Pipeline:

```text
Axiom
  ↓
Typed HIR
  ↓
MIR
  ↓
GPU legality analysis
  ↓
GPU Kernel IR
  ↓
SPIR-V / DXIL / Metal / native GPU backend
```

Một kernel chỉ được phép sử dụng subset phù hợp với GPU target.

Ví dụ có thể cấm:

```text
File
Socket
OS syscall
dynamic allocation
arbitrary pointer
blocking mutex
```

trong kernel.

---

# 4. Đây không phải runtime error

Nếu viết:

```axiom
@kernel
fn foo() {
    File.open(...)
}
```

compiler phải báo:

```text
AX_GPU_0001:
operation is not available in GPU execution domain
```

Không nên đợi đến runtime.

---

# 5. Execution domain

Tôi đề xuất compiler có concept nội bộ:

```text
ExecutionDomain:
    CPU
    GPU
    Device
    Kernel
    Host
```

Programmer chỉ cần thấy annotation/API cần thiết.

Compiler dùng domain để kiểm tra:

```text
call legality
memory legality
synchronization
available types
available intrinsics
```

---

# 6. Không đưa `GPU` thành primitive type

Không nên có:

```text
gpu_int
gpu_float
gpu_pointer
```

thành một hệ type riêng.

Thay vào đó:

```text
Type
+
AddressSpace
+
ExecutionDomain
```

là metadata/compiler semantics.

---

# 7. Address space thực sự quan trọng

GPU thường có:

```text
Private
Local
Workgroup
Storage
Uniform
Constant
Device
Shared
```

Axiom nên có semantic address-space model nội bộ:

```text
AddressSpace:
    Host
    Device
    Shared
    Local
    Private
    Constant
    External
```

Nhưng không nhất thiết programmer phải viết address-space annotation mọi nơi.

---

# 8. Vì sao address space cần semantic?

Ví dụ:

```axiom
view<f32>
```

trên CPU nghĩa là vùng memory CPU-accessible.

Nhưng GPU có thể có:

```text
device memory
```

không thể dereference từ CPU.

Compiler phải phân biệt:

```text
host view
device view
```

ở boundary.

---

# 9. Tôi đề xuất typed device buffer

Library:

```axiom
let gpu_data = DeviceBuffer<f32>.allocate(1024)
```

Sau đó:

```axiom
gpu_data.view()
```

không phải là CPU `view<f32>` thông thường.

Có thể có:

```text
DeviceView<T>
```

hoặc một abstraction tương đương.

Điểm quan trọng:

> **Không cho phép implicit device pointer → host pointer.**

---

# 10. Host/device transfer

API:

```axiom
let device = DeviceBuffer<f32>.upload(data)?
```

và:

```axiom
let data = device.download()?
```

Compiler biết đây là:

```text
HOST → DEVICE
DEVICE → HOST
```

operation có cost rất lớn.

---

# 11. Không cố “zero-cost” transfer

Transfer GPU ↔ CPU là observable cost.

Không thể compiler xóa:

```text
upload
download
```

chỉ vì abstraction.

Nhưng compiler có thể:

- batch transfer
- eliminate redundant transfer
- overlap transfer + execution
- reuse buffer
- fuse kernels.

---

# 12. Kernel arguments

Ví dụ:

```axiom
launch(add, input, output, n)
```

compiler/runtime có thể biến thành:

```text
kernel descriptor
argument buffer
dispatch dimensions
synchronization
```

Không cần programmer tự serialize từng argument.

---

# 13. Kernel launch là asynchronous

GPU:

```text
launch()
```

thường không đồng nghĩa:

```text
kernel finished
```

Do đó API nên trả:

```text
GpuEvent
```

hoặc:

```text
Future<T>
```

nhưng semantics phải phân biệt với CPU async.

Ví dụ:

```axiom
let event = gpu.launch(add, ...)
event.wait()?
```

---

# 14. GPU Future không phải CPU Future

Không nên để:

```text
Future<T>
```

ngầm có nghĩa:

> CPU thread đang chờ GPU.

GPU operation có execution domain riêng.

Có thể có:

```text
GpuFuture<T>
```

library abstraction, sau đó adapter sang async CPU.

---

# 15. Synchronization

GPU synchronization có nhiều cấp:

```text
lane
warp/subgroup
workgroup
device
host
```

Không nên biến tất cả thành:

```text
Mutex
```

vì semantics khác hoàn toàn.

---

# 16. Workgroup barrier

Ví dụ:

```axiom
gpu.barrier()
```

đây là compiler intrinsic.

Compiler phải biết:

```text
barrier = control + memory ordering
```

chứ không phải function call bình thường.

---

# 17. Atomics trên GPU

Axiom đã có atomic model.

Do đó GPU có thể map:

```axiom
Atomic<u32>.fetch_add(...)
```

sang:

```text
GPU atomic instruction
```

Nhưng memory scope có thể cần thêm:

```text
Invocation
Workgroup
Device
System
```

---

# 18. Scope không nên phá Core atomic model

Thay vì thêm hàng chục atomic types:

```text
WorkgroupAtomic
DeviceAtomic
SystemAtomic
...
```

tôi đề xuất atomic operation có **scope parameter/semantic metadata** trong GPU library.

Ví dụ conceptually:

```text
atomic.load(Acquire, Workgroup)
atomic.store(Release, Device)
```

Core CPU vẫn chỉ cần ordering cơ bản.

---

# 19. Shared memory

GPU local/shared memory cực kỳ quan trọng cho performance.

Có thể có:

```axiom
let tile = workgroup.alloc<f32, 256>()
```

nhưng đây là GPU library/compiler intrinsic.

Compiler biết lifetime:

```text
kernel invocation
       ↓
workgroup
       ↓
release
```

---

# 20. Không dùng heap allocator thông thường trong GPU kernel

Không nên mặc định hỗ trợ:

```axiom
Vec.new()
Box.new()
```

trong kernel.

Nếu GPU backend hỗ trợ device allocation:

```text
DeviceArena
DeviceAllocator
```

thì đó là explicit capability.

---

# 21. GPU ownership

Điểm này rất hợp với Axiom.

Ví dụ:

```text
DeviceBuffer<T>
```

là owner.

Khi launch:

```axiom
gpu.launch(kernel, buffer)
```

compiler/runtime có thể xác định:

```text
kernel READ
buffer owner remains host-side
```

Nhưng nếu kernel WRITE:

```text
buffer = device mutable capability
```

host không được đồng thời mutate.

---

# 22. Host/device race

Ví dụ nguy hiểm:

```text
CPU writes buffer
GPU simultaneously reads buffer
```

Axiom nên không cho safe code làm điều này nếu synchronization/provenance không chứng minh được.

Conceptually:

```text
CPU WRITE
      │
      ├── transfer/sync ──→
      │
GPU READ
```

Execution dependency trở thành một phần của capability state.

---

# 23. GPU event là synchronization capability

Ví dụ:

```axiom
let event = gpu.launch(write_kernel, buffer)

event.wait()?

buffer.read()
```

`wait()` tạo happens-before:

```text
GPU WRITE
    ↓
EVENT SIGNAL
    ↓
CPU READ
```

Compiler/runtime có thể dùng information đó.

---

# 24. Kernel fusion

Đây là optimization rất đáng giá.

```axiom
kernel A → buffer → kernel B
```

Nếu:

```text
A writes X
B immediately reads X
```

compiler có thể:

```text
A + B
 ↓
fused kernel
```

nếu semantics cho phép.

Đây là ví dụ mạnh của:

> Abstraction Erasure.

---

# 25. Nhưng không ép compiler fuse

Fusion có thể làm:

- register pressure tăng
- occupancy giảm
- code size tăng
- synchronization thay đổi.

Do đó:

```text
fusion = optimizer decision
```

không phải semantic requirement.

---

# 26. Tensor/matrix

Không nên đưa:

```text
Matrix
Tensor
TensorCore
```

vào Core.

Library có thể cung cấp:

```text
Tensor<T, Shape>
Matrix<T,R,C>
```

và compiler có thể recognize các pattern.

Ví dụ:

```axiom
C = A.matmul(B)
```

có thể lower:

```text
CPU SIMD
GPU
AMX
TensorCore
Accelerator
```

---

# 27. Accelerator model

Axiom nên có abstraction tổng quát hơn GPU:

```text
Device
Queue
Buffer
Kernel
Event
```

GPU chỉ là một implementation.

Sau này có:

```text
NPU
TPU
DSP
FPGA
AI accelerator
```

mà không cần thay đổi Core language.

---

# 28. Device abstraction

Conceptually:

```axiom
trait Device {
    fn allocate<T>(...)
    fn upload<T>(...)
    fn launch(...)
    fn synchronize(...)
}
```

Nhưng kernel compilation vẫn compiler-aware.

Trait chỉ quản lý host-side API.

---

# 29. Không biến dynamic dispatch thành GPU dispatch

Ví dụ:

```text
dyn Device
```

có thể dùng host-side.

Nhưng kernel:

```text
@kernel fn ...
```

nên static compile.

GPU kernel không nên phụ thuộc runtime virtual dispatch nếu không explicit.

---

# 30. GPU error model

Kernel có thể:

- trap
- out-of-bounds
- device lost
- launch failure
- synchronization failure.

Không nên dùng exception.

API:

```text
Result<T, GpuError>
```

và kernel safety được compiler kiểm tra trước.

---

# 31. GPU bounds checking

Safe kernel:

```axiom
if i < xs.len() {
    out[i] = xs[i]
}
```

Compiler có thể prove:

```text
i < len
```

và loại bounds check.

Nếu compiler không prove được:

```text
bounds check
```

vẫn giữ.

---

# 32. Pointer trong GPU

Raw GPU pointer chỉ ở system layer:

```text
unsafe
```

Không nên để:

```text
*mut T
```

tự động mang nghĩa host/device.

Pointer phải có provenance/address-space metadata nội bộ.

---

# 33. Serialization

Không nên gửi một Axiom struct arbitrary sang GPU bằng cách:

```text
memcpy(&struct)
```

và giả định layout.

Chỉ khi:

```text
@repr(...)
```

hoặc device-compatible representation được xác định.

---

# 34. GPU layout types

Library có thể có:

```text
StorageBuffer<T>
Uniform<T>
DeviceArray<T>
```

với representation contract.

Ví dụ:

```text
GPU std140/std430
Metal layout
HLSL structured buffer
```

không nên trở thành language-wide layout rules.

---

# 35. Shader interoperability

Axiom có thể compile kernel tới:

```text
SPIR-V
DXIL
Metal
CUDA/PTX
native GPU backend
```

nhưng **không nên phụ thuộc một backend duy nhất**.

Architecture:

```text
Axiom Kernel IR
       ↓
 ┌─────┼─────┬─────┐
SPIR-V DXIL Metal PTX
```

---

# 36. Kernel IR

Nên có một IR riêng:

```text
KIR
```

hoặc mở rộng LIR.

Tôi nghiêng về:

```text
MIR
 ↓
Domain Analysis
 ↓
GPU-LIR / CPU-LIR
```

thay vì tạo một frontend GPU riêng.

---

# 37. Execution model trong compiler

Pipeline:

```text
Source
 ↓
AST
 ↓
HIR
 ↓
Typed HIR
 ↓
Execution-domain analysis
 ↓
MIR
 ├───────────────┐
 │               │
CPU             GPU
 │               │
CPU LIR         GPU LIR
 │               │
Machine IR      GPU backend
```

Điều này rất quan trọng để tránh:

```text
Axiom CPU compiler
Axiom GPU compiler
Axiom shader compiler
```

thành ba hệ thống khác nhau.

---

# 38. Heterogeneous ownership

Một object không thể đồng thời có hai owner ở:

```text
host
device
```

nếu memory thực sự khác nhau.

Do đó:

```text
HostBuffer<T>
DeviceBuffer<T>
```

là hai storage semantics khác nhau.

Transfer:

```text
HostBuffer<T>
    ↓ upload
DeviceBuffer<T>
```

là explicit semantic transition/copy.

---

# 39. Unified memory

Một số platform có shared/unified memory.

Không nên phá abstraction.

Có thể:

```text
UnifiedBuffer<T>
```

library type.

Compiler biết:

```text
host + device accessible
```

và runtime quản lý coherence theo platform.

---

# 40. Zero-copy

Zero-copy chỉ là một implementation possibility.

Source:

```axiom
upload(buffer)
```

có thể trên platform A:

```text
copy
```

platform B:

```text
map/pin
```

platform C:

```text
zero-copy
```

API semantics không thay đổi.

---

# 41. DMA

DMA nên nằm system/platform layer.

Nhưng compiler/runtime có thể biết:

```text
DMA operation
```

là asynchronous memory transfer.

Nó tạo synchronization edge:

```text
source
 ↓
DMA
 ↓
event
 ↓
destination
```

---

# 42. Unified memory model

Từ CPU atomic + GPU synchronization, ta có thể mở rộng Axiom thành:

```text
Memory Object
     │
     ├── ownership
     ├── region
     ├── address space
     ├── execution domain
     └── synchronization state
```

Đây là **compiler-internal model**, không phải programmer phải quản lý tất cả.

---

# 43. Nguyên tắc cực kỳ quan trọng

Không nên tạo:

```text
HostView
DeviceView
SharedView
LocalView
ConstantView
...
```

thành hàng chục primitive language types.

Nếu làm vậy, programmer sẽ quay lại đúng vấn đề mà Axiom muốn loại bỏ:

> quá nhiều loại reference/pointer.

Thay vào đó:

```text
view<T>
```

là abstraction chính.

Compiler gắn:

```text
AddressSpace
ExecutionDomain
```

ở phía sau.

---

# 44. GPU invariants

Chốt:

```text
AGPU-01   GPU Is A Separate Execution Domain
AGPU-02   GPU Does Not Define A Separate Core Language
AGPU-03   Kernel Is Explicit
AGPU-04   Kernel Legality Is Compile-Time Checked
AGPU-05   Device Memory Is Not Implicit Host Memory
AGPU-06   Host/Device Transfer Is Explicit
AGPU-07   Device Allocation Is Not Mandatory
AGPU-08   GPU Synchronization Is Explicit
AGPU-09   GPU Atomics Reuse Axiom Atomic Semantics
AGPU-10   GPU Memory Scope Is Explicit Where Required
AGPU-11   Safe Host/Device Races Are Prevented
AGPU-12   GPU Events Establish Synchronization Edges
AGPU-13   Kernel Launch Does Not Imply Immediate Completion
AGPU-14   GPU Future Is Distinct From CPU Thread Execution
AGPU-15   Kernel Fusion Is An Optimization
AGPU-16   GPU Layout Contracts Are Explicit
AGPU-17   Raw Device Pointers Are System-Level
AGPU-18   GPU Allocation Is Not A Language Primitive
AGPU-19   Tensor/Matrix APIs Are Library-Level
AGPU-20   Accelerators Share The Device Abstraction
AGPU-21   GPU Backends Are Replaceable
AGPU-22   Kernel Compilation Shares Axiom Frontend
AGPU-23   Safe GPU Bounds Checks May Be Optimized Away
AGPU-24   Unified Memory Is An Explicit Storage Abstraction
AGPU-25   Zero-Copy Is An Optimization/Platform Property
AGPU-26   DMA Is A System/Platform Capability
AGPU-27   GPU Abstractions Must Not Leak Pointer Complexity
AGPU-28   Host/Device Ownership Remains Deterministic
```

---

# 45. Một thay đổi kiến trúc đáng ghi nhận

Sau phần này, mô hình Axiom đã mở rộng từ:

```text
CPU language
```

thành:

```text
                    Axiom
                      │
          ┌───────────┼───────────┐
          │           │           │
         CPU         GPU      Accelerator
          │           │           │
       SIMD        Kernel       Kernel
          │           │           │
       threads     workgroups    device
```

nhưng **frontend/type system/ownership model vẫn dùng chung**.

Đây là hướng tốt hơn nhiều so với việc tạo một DSL GPU riêng.

---

# Tiếp tục → OS, Freestanding, Embedded và Hardware

Bước tiếp theo tôi đề xuất là một phần còn quan trọng hơn GPU đối với mục tiêu ban đầu của Axiom:

## **OS & Platform Abstraction**

Ta cần quyết định chính xác Axiom sẽ xử lý:

- Windows
- Linux
- macOS
- iOS
- Android
- WASM
- bare-metal
- kernel
- embedded
- UEFI
- bootloader
- interrupt
- syscall
- MMIO
- TLS
- process
- thread
- dynamic library
- static linking

như thế nào **mà không biến Core thành một đống platform-specific API**.

Đặc biệt sẽ phải chốt kiến trúc:

```text
Axiom Core
      ↓
Axiom System ABI
      ↓
Platform Layer
      ↓
OS / Firmware / Bare Metal
```

và đây cũng là bước cần thiết để tiến tới mục tiêu **Axiom tự tạo native `.exe`, ELF, Mach-O mà cuối cùng không cần C compiler/linker bên ngoài**.