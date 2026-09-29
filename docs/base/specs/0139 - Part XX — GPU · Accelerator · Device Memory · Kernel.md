# Part XX — GPU · Accelerator · Device Memory · Kernel

Tiếp tục từ Part XIX. Phần này nên **đóng băng GPU như một execution domain của Axiom**, chứ không biến GPU thành một ngôn ngữ thứ hai.

Nguyên tắc trung tâm:

> **One Language Semantics, Many Execution Domains.**

CPU, GPU, NPU, DSP hay accelerator khác có thể có ABI và giới hạn thực thi khác nhau, nhưng vẫn dùng chung **type system + ownership + capability + synchronization + error model** của Axiom.

---

# XX.1. Mục tiêu

Axiom GPU model phải đạt được:

- GPU kernel là Axiom function có ràng buộc execution domain.
- Không cần ngôn ngữ kernel riêng.
- Ownership/view vẫn có ý nghĩa trên GPU.
- Host ↔ Device transfer phải explicit.
- Không cho kernel vô tình giữ reference tới host memory.
- Không để GPU operation đang chạy bị hủy tài nguyên một cách unsafe.
- GPU synchronization tích hợp với memory model.
- GPU atomics dùng cùng semantics với CPU atomics, bổ sung **scope**.
- Compiler có thể optimize/fuse/vectorize/kernel-specialize.
- Không bắt buộc CUDA/OpenCL runtime.
- Axiom có thể target CUDA/PTX, SPIR-V, Metal, Vulkan, DirectX, ROCm/AMDGCN... thông qua backend.
- Có thể mở rộng sang NPU/DSP/accelerator mà không sửa semantic core.

---

# XX.2. Execution Domain

Axiom phân biệt **nơi code có thể thực thi**.

Khái niệm semantic:

```text
CPU
GPU
DEVICE
KERNEL
HOST
```

Trong đó:

- `CPU`: code chạy trên CPU.
- `GPU`: code chạy trên GPU/device processor.
- `KERNEL`: function có thể được dispatch theo execution grid.
- `HOST`: code điều khiển device từ host.
- `DEVICE`: abstraction tổng quát cho accelerator.

Ví dụ:

```axiom
@kernel
fn add(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
) {
    let i = kernel.global_id(0)

    out[i] = a[i] + b[i]
}
```

Host:

```axiom
fn main() -> Result<(), Error> {
    let a = DeviceBuffer.from([1.0, 2.0, 3.0])
    let b = DeviceBuffer.from([4.0, 5.0, 6.0])

    let out = DeviceBuffer.alloc<f32>(3)

    let event = gpu.dispatch(
        add,
        a.view(),
        b.view(),
        out.mut_view(),
        [3, 1, 1]
    )?

    event.wait()?

    let result = out.read()?

    print(result)

    Ok(())
}
```

Điểm quan trọng:

**`@kernel` không phải magic runtime.**

Nó là semantic declaration để compiler biết function này phải thỏa kernel legality rules.

---

# XX.3. Kernel không phải Thread

GPU kernel invocation khác hoàn toàn:

```text
Thread
Task
Future
Kernel Invocation
```

Kernel có thể tạo ra hàng nghìn/hàng triệu logical execution instances.

Ví dụ:

```axiom
@kernel
fn add(...) {
    let i = kernel.global_id(0)
}
```

Không có nghĩa:

```text
một function call = một OS thread
```

Mà semantic model gần:

```text
dispatch
    ├── invocation 0
    ├── invocation 1
    ├── invocation 2
    ├── ...
    └── invocation N
```

Compiler/backend quyết định mapping thực tế.

---

# XX.4. Kernel Legality

Một `@kernel` không được tùy tiện gọi mọi API của Axiom.

Compiler phải kiểm tra execution-domain legality.

Ví dụ **không hợp lệ**:

```axiom
@kernel
fn bad() {
    File.open("x")?
}
```

```axiom
@kernel
fn bad() {
    Socket.connect(...)
}
```

```axiom
@kernel
fn bad() {
    os.syscall(...)
}
```

```axiom
@kernel
fn bad() {
    Mutex.lock(...)
}
```

trừ khi target/backend có một abstraction tương ứng và function đó được đánh dấu device-compatible.

### Kernel có thể sử dụng

- arithmetic
- structs
- enums phù hợp
- arrays
- views
- atomics
- local/shared memory
- device functions
- deterministic control flow
- compiler-supported intrinsics
- device-compatible traits/generics
- device math library.

---

# XX.5. Kernel Call Graph

Kernel legality phải được kiểm tra **transitively**.

Ví dụ:

```axiom
@kernel
fn kernel_a() {
    helper()
}

fn helper() {
    File.open("x")
}
```

Không được phép chỉ vì `helper` không có `@kernel`.

Compiler phải phát hiện:

```text
kernel_a
    ↓
helper
    ↓
File.open
    ↓
HOST_ONLY
```

→ compile error.

Do đó mỗi function có thể có semantic execution capability:

```text
HOST_ONLY
DEVICE_ONLY
HOST_DEVICE
KERNEL_ENTRY
```

Một function `HOST_DEVICE` phải có implementation hợp lệ cho cả hai domain.

---

# XX.6. Address Space

GPU memory không đơn giản là một memory pool duy nhất.

Axiom định nghĩa semantic address spaces:

```text
Host
Device
Shared
Local
Private
Constant
External
```

Ý nghĩa:

### Host

CPU-visible memory.

### Device

Device global memory.

### Shared

Memory chia sẻ trong execution group/workgroup.

### Local

Memory local/private theo execution unit, tùy backend.

### Private

Memory riêng của invocation.

### Constant

Read-only constant/device memory.

### External

Memory do hệ thống/device/API bên ngoài quản lý.

---

# XX.7. Address Space Là Type/Capability Property

Compiler phải biết:

```text
view<f32 @device>
view<f32 @shared>
view<f32 @constant>
```

nếu target cần phân biệt address space.

Tuy nhiên syntax `@device` có thể được giấu ở mức API nếu compiler suy ra được.

Điều quan trọng là semantic model phải giữ distinction.

Không được coi:

```text
*mut T @device
```

là tương đương:

```text
*mut T @host
```

---

# XX.8. Device Pointer

Device pointer không được tự động trở thành host pointer.

Ví dụ:

```axiom
let p = device_buffer.ptr()
```

không có nghĩa:

```axiom
let host_p: *mut T = p
```

Conversion giữa address spaces phải:

- được compiler chứng minh an toàn, hoặc
- explicit unsafe/backend operation.

Ví dụ conceptual:

```axiom
unsafe {
    device_addr_cast(...)
}
```

---

# XX.9. DeviceBuffer

GPU memory nên được biểu diễn bằng library abstraction:

```axiom
DeviceBuffer<T>
```

Nó là **owner** của device allocation.

Ví dụ:

```axiom
var buffer = DeviceBuffer.alloc<f32>(1024)
```

Semantic:

```text
DeviceBuffer<T>
    owns
       ↓
device storage
```

Không phải:

```text
DeviceBuffer<T> = raw pointer
```

Raw pointer chỉ là low-level representation.

---

# XX.10. DeviceView

```axiom
DeviceView<T>
```

hoặc semantic tương đương:

```axiom
view<T @device>
```

là non-owning capability.

Ví dụ:

```axiom
@kernel
fn scale(
    data: view<f32>,
    factor: f32
) {
    ...
}
```

Kernel không sở hữu `data`.

Owner nằm ngoài:

```text
DeviceBuffer
      │
      └── DeviceView
              │
              └── Kernel
```

---

# XX.11. Device Mutable View

```axiom
mut_view<T @device>
```

có cùng semantics với `mut_view<T>` trên CPU:

- exclusive write capability
- không Copy theo value semantics
- không được alias với conflicting mutable access
- provenance phải hợp lệ.

Ví dụ:

```axiom
@kernel
fn add(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
)
```

Compiler phải chứng minh:

```text
out ∩ a = ∅
out ∩ b = ∅
```

hoặc API phải cung cấp contract bảo đảm điều đó.

Nếu compiler chỉ biết:

```text
UNKNOWN
```

thì safe kernel phải bị reject hoặc sử dụng abstraction có contract rõ ràng.

---

# XX.12. Host/Device Ownership

Đây là điểm rất quan trọng.

Axiom **không tự động copy memory giữa host và device**.

Ví dụ:

```axiom
let x = [1, 2, 3]
```

không thể tự nhiên truyền:

```axiom
kernel(x)
```

nếu kernel yêu cầu device memory.

Phải có operation rõ ràng:

```axiom
let d = device.upload(x)?
```

hoặc:

```axiom
let d = DeviceBuffer.from(x)?
```

Điều này làm transfer cost **visible trong semantics**.

---

# XX.13. Transfer Không Phải Copy Value Bình Thường

Host → Device:

```text
Host Value
    ↓
transfer
    ↓
Device Storage
```

không nhất thiết là semantic `Copy<T>`.

Nó là một operation có thể:

- tốn thời gian
- asynchronous
- fail
- phụ thuộc device
- yêu cầu synchronization.

Do đó:

```axiom
device.upload(x)?
```

là operation library/device chứ không phải implicit type conversion.

---

# XX.14. Unified Memory

Axiom có thể hỗ trợ:

```axiom
UnifiedBuffer<T>
```

nhưng **unified address space không đồng nghĩa unified synchronization**.

Ví dụ:

```text
CPU ───────┐
           │
     Unified Memory
           │
GPU ───────┘
```

vẫn cần synchronization trước khi một execution domain đọc dữ liệu mà domain khác vừa ghi.

Không được suy luận:

```text
same address => automatically synchronized
```

---

# XX.15. GPU Event

GPU operation asynchronous:

```axiom
let event = gpu.dispatch(...)
```

trả về:

```axiom
GpuEvent
```

`GpuEvent` là resource/synchronization object.

Ví dụ:

```axiom
let event = gpu.dispatch(kernel, ...)?

event.wait()?
```

hoặc:

```axiom
event.then(...)
```

ở tầng library.

---

# XX.16. Event và Ownership

Đây là invariant rất quan trọng:

```text
DeviceBuffer
     │
     └── in-flight GPU operation
```

Không được:

```axiom
drop(buffer)
```

khi operation vẫn có thể truy cập buffer.

Compiler/library phải đảm bảo một trong các contract:

### Ownership transfer

```text
dispatch
    takes ownership
```

hoặc:

### Event dependency

```text
GpuEvent
    owns/retains operation dependency
```

hoặc:

### Explicit synchronization

```axiom
event.wait()
drop(buffer)
```

Không được có hidden assumption.

---

# XX.17. Relocation và GPU Operation

Tương tự CPU:

```text
DeviceBuffer may relocate
```

nếu storage abstraction cho phép.

Nhưng nếu GPU operation đang giữ capability:

```text
buffer
  ↓
device view
  ↓
in-flight kernel
```

thì relocation phải bị chặn hoặc backend phải update abstraction mà **không làm invalid capability**.

Do đó:

> Relocatable storage cannot invalidate a live capability.

---

# XX.18. GPU Synchronization

GPU synchronization không chỉ là CPU mutex.

Axiom phân biệt:

```text
CPU synchronization
GPU synchronization
Cross-domain synchronization
```

Ví dụ:

```text
Host
  |
  | dispatch
  v
GPU
  |
  | event
  v
Host
```

`GpuEvent` có thể tạo happens-before:

```text
GPU writes
    ↓
event completion
    ↓
host read
```

Nhưng chỉ khi event API contract quy định điều đó.

---

# XX.19. Workgroup / Shared Memory

GPU kernel có execution hierarchy:

```text
Dispatch
 ├── Workgroup
 │    ├── Invocation
 │    ├── Invocation
 │    └── Invocation
 ├── Workgroup
 └── ...
```

Axiom nên expose semantic primitives:

```axiom
kernel.global_id(dim)
kernel.local_id(dim)
kernel.group_id(dim)
kernel.local_size(dim)
kernel.global_size(dim)
```

và:

```axiom
workgroup.barrier()
```

---

# XX.20. Barrier

Barrier là synchronization primitive có scope.

Ví dụ:

```axiom
@kernel
fn reduce(data: mut_view<f32>) {
    let i = kernel.local_id(0)

    ...

    workgroup.barrier()

    ...
}
```

Compiler không được di chuyển memory operation qua barrier nếu làm thay đổi synchronization semantics.

---

# XX.21. Barrier Divergence

Một collective barrier không thể được sử dụng tùy tiện:

```axiom
if condition {
    workgroup.barrier()
}
```

có thể dẫn đến deadlock tùy GPU execution model.

Compiler nên reject khi có thể chứng minh barrier divergence không hợp lệ.

Nếu backend không đủ khả năng chứng minh, API có thể yêu cầu explicit uniformity contract.

Ví dụ conceptual:

```axiom
@uniform
if condition {
    workgroup.barrier()
}
```

`@uniform` chỉ nên được thêm nếu thực sự cần; không biến annotation thành cơ chế "tin compiler".

---

# XX.22. GPU Atomic

Axiom dùng cùng semantic:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

nhưng GPU có thêm:

```text
scope
```

Ví dụ:

```text
Workgroup
Device
System
```

Conceptual:

```axiom
atomic_add(
    x,
    1,
    order = Relaxed,
    scope = Device
)
```

Scope **không thay thế ordering**.

Nó trả lời:

> Atomic operation có hiệu lực tới execution domain nào?

Ordering trả lời:

> Các memory effects được sắp xếp thế nào?

---

# XX.23. GPU Atomic và Ordinary Memory

Không được:

```axiom
atomic_store(&x, 1)
```

sau đó coi:

```axiom
view(x)
```

là ordinary mutable memory mà không có synchronization contract.

Invariant vẫn giữ nguyên:

> Atomic storage cannot be accessed through ordinary mutable capability.

---

# XX.24. Kernel ABI

Host ABI và kernel ABI là hai contract khác nhau.

Host:

```text
Axiom ABI
C ABI
system ABI
```

Kernel:

```text
GPU kernel ABI
```

Kernel ABI có thể encode:

- parameter address spaces
- scalar layout
- vector layout
- descriptor/buffer binding
- shared memory requirements
- workgroup size
- alignment
- resource bindings.

Ví dụ backend có thể biến:

```axiom
fn add(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
)
```

thành descriptor layout tương ứng với target.

Nhưng đây là **ABI lowering**, không thay đổi source semantics.

---

# XX.25. Kernel Parameter Restrictions

Kernel parameter phải có representation mà target hỗ trợ.

Không thể tùy tiện:

```axiom
@kernel
fn f(x: SomeHugeDynamicTraitObjectWithHostRuntimeState)
```

nếu backend không thể represent.

Compiler phải kiểm tra:

```text
Kernel ABI Compatibility
```

trước code generation.

---

# XX.26. Function Pointers / Closures trong Kernel

Không nên mặc định cấm mọi function pointer/closure.

Thay vào đó:

```text
device-compatible function pointer
```

là target capability.

Nếu GPU target không hỗ trợ:

```axiom
@kernel
fn f(callback: fn(i32) -> i32)
```

→ compile error.

Không phải language error.

Điều này rất quan trọng cho tính mở rộng.

---

# XX.27. Dynamic Allocation trong Kernel

Core semantics không yêu cầu GPU kernel phải có heap.

Nếu target hỗ trợ device allocation:

```axiom
DeviceBox<T>
```

có thể được library/backend cung cấp.

Nếu không:

```text
@kernel allocation
```

→ compile error.

Không được âm thầm chuyển allocation về host.

---

# XX.28. Recursion

Recursion trong kernel:

```axiom
@kernel
fn f(...) {
    f(...)
}
```

không phải semantic violation tự thân.

Nhưng backend có thể yêu cầu:

- bounded recursion
- no recursion
- special stack support.

Do đó đây là:

```text
target capability constraint
```

chứ không phải một thay đổi trong core language.

---

# XX.29. GPU Error Model

GPU operation có thể fail:

```axiom
gpu.dispatch(...) -> Result<GpuEvent, GpuError>
```

Recoverable device/API errors:

```text
Result
```

Kernel runtime failure:

```text
panic/trap
```

Không có exception/unwind trên GPU.

Ví dụ:

```axiom
if i >= data.len {
    panic("invalid index")
}
```

Backend có thể lower thành:

```text
trap
```

hoặc device-specific failure mechanism.

Semantics vẫn là **non-recoverable invocation failure**.

---

# XX.30. GPU Panic Scope

GPU panic không mặc định có nghĩa:

```text
kill entire host process
```

Target profile phải định nghĩa scope:

```text
invocation
workgroup
dispatch
device queue
process
```

Nếu backend không hỗ trợ fine-grained recovery, profile có thể quy định:

```text
dispatch failure
```

và host quan sát qua:

```axiom
event.wait() -> Result<_, GpuError>
```

---

# XX.31. Device Resource Drop

`Drop` của device resource:

```axiom
drop(buffer)
```

không được phép phá hỏng operation đang chạy.

Do đó:

```text
Drop(buffer)
```

phải thỏa:

```text
no live device operation depends on buffer
```

hoặc library abstraction phải retain resource cho tới completion.

Đây là cùng một ownership rule, không phải GPU-specific hack.

---

# XX.32. Kernel Capture

Kernel không được capture arbitrary host state:

```axiom
var x = File.open(...)
 
@kernel
fn k() {
    use(x)
}
```

Compiler phải reject.

Kernel closure nếu được hỗ trợ phải có:

```text
DeviceSend
DeviceCopy
```

hoặc tương đương device-compatible capability.

---

# XX.33. Accelerator Generalization

Đây là điểm tôi khuyên **không khóa Axiom vào GPU**.

Semantic abstraction:

```text
Device
Queue
Buffer
View
Kernel
Event
Fence
```

GPU chỉ là một implementation.

Có thể có:

```text
CpuDevice
GpuDevice
NpuDevice
DspDevice
FpgaDevice
CustomDevice
```

Ví dụ:

```axiom
let device = Device.default()?

let buffer = device.alloc<f32>(1024)?

let event = device.dispatch(kernel, ...)?
```

API cấp cao có thể generic:

```axiom
fn execute<D: Device>(device: D, ...)
```

---

# XX.34. Kernel Fusion

Compiler được phép biến:

```text
kernel A
    ↓
kernel B
    ↓
kernel C
```

thành:

```text
fused kernel ABC
```

nếu observable semantics không thay đổi.

Điều này có thể giảm:

- memory round-trip
- dispatch overhead
- synchronization
- temporary buffers.

Nhưng fusion không được thay đổi:

- atomic ordering
- visible writes
- synchronization
- error behavior
- externally observable side effects.

---

# XX.35. Device Memory Optimization

Compiler có thể:

```text
global → shared
shared → register
temporary → register
remove allocation
combine transfers
eliminate transfer
vectorize
tile
fuse
specialize
```

miễn semantics được bảo toàn.

Đặc biệt:

> Device memory placement là optimization freedom trừ khi storage/address-space contract làm nó observable.

---

# XX.36. Kernel Specialization

Generic:

```axiom
@kernel
fn map<T: Numeric>(...)
```

có thể được specialize:

```text
f32
f64
i32
...
```

Compiler specialization không được observable.

Điều này kế thừa:

`AGENERIC-20 — Specialization Is Not Observable`.

---

# XX.37. CPU/GPU Shared Semantic Model

Ví dụ:

```axiom
fn process(
    input: view<f32>,
    output: mut_view<f32>
) {
    ...
}
```

cùng một semantic abstraction có thể được lower thành:

```text
CPU function
```

hoặc:

```text
GPU kernel
```

nếu function thỏa execution constraints.

Đây là mục tiêu lớn:

```text
              Axiom Semantics
                    │
        ┌───────────┼───────────┐
        ↓           ↓           ↓
       CPU         GPU         NPU
        │           │           │
      ABI₁        ABI₂        ABI₃
```

Không:

```text
Axiom language
CUDA language
NPU language
```

---

# XX.38. GPU và Ownership

Các invariant ownership cơ bản vẫn giữ nguyên:

```text
Owner destruction cannot invalidate live capability.
Capability does not transfer ownership.
Move does not imply physical copy.
Copy does not imply shared mutable alias.
```

Điểm này giúp compiler không phải xây một memory-safety model riêng cho GPU.

---

# XX.39. GPU và Async

Hai khái niệm:

```text
async function
GPU dispatch
```

không đồng nhất.

GPU dispatch có thể trả:

```axiom
GpuEvent
```

Async wrapper có thể:

```axiom
async fn compute(...) -> Result<Output, Error>
```

và await:

```axiom
let result = compute(...).await?
```

Lowering có thể là:

```text
async state machine
       ↓
GPU dispatch
       ↓
event
       ↓
suspend
       ↓
event completion
       ↓
resume
```

Nhưng GPU operation không bắt buộc phải sử dụng async runtime.

---

# XX.40. Memory Ordering Across CPU/GPU

Cross-domain synchronization phải explicit.

Ví dụ:

```text
CPU WRITE
   ↓
upload
   ↓
GPU READ
```

và:

```text
GPU WRITE
   ↓
event
   ↓
CPU READ
```

phải có synchronization edges.

Compiler không được giả định:

```text
launch() => immediately completed
```

hay:

```text
wait() => only scheduling event
```

Semantic contract của event phải định nghĩa happens-before.

---

# XX.41. Negative Examples

### Host pointer vào kernel

```axiom
fn main() {
    var x = 10

    gpu.dispatch(k, &x)
}
```

Nếu `k` yêu cầu device memory:

```text
ERROR:
host capability cannot satisfy device capability
```

---

### Device view sống lâu hơn owner

```axiom
let v = buffer.view()

drop(buffer)

gpu.dispatch(k, v)
```

→ reject.

---

### In-flight use rồi free

```axiom
let event = gpu.dispatch(k, buffer.view())?

drop(buffer)

event.wait()?
```

→ reject nếu contract không transfer/retain ownership.

---

### Atomic/ordinary alias

```axiom
atomic_store(x, 1)

let m = mut_view(x)
```

→ reject nếu `x` là atomic storage.

---

### Host-only API trong kernel

```axiom
@kernel
fn k() {
    print("hello")
}
```

→ reject nếu `print` là host-only.

---

# XX.42. Optimization Rules

Compiler **được phép**:

- eliminate kernel temporaries
- fuse kernels
- vectorize
- unroll
- tile
- move data between legal address spaces
- register promote
- eliminate redundant synchronization khi chứng minh không observable
- eliminate redundant transfers khi ownership/synchronization cho phép
- specialize kernels
- inline device functions
- reorder independent operations.

Compiler **không được**:

- bỏ atomic ordering
- bỏ required barrier
- biến asynchronous operation thành synchronous observable behavior
- free resource trước khi operation hoàn tất
- tạo host/device alias trái phép
- bỏ required transfer
- thay đổi error semantics
- thay đổi externally observable synchronization.

---

# XX.43. ABI Rules

Kernel ABI phải freeze các thông tin cần thiết:

```text
parameter representation
address space
alignment
resource binding
scalar/vector layout
workgroup requirements
calling convention
```

Nhưng implementation vẫn tự do tối ưu bên trong kernel.

Host ABI không tự động áp dụng cho device.

---

# XX.44. Normative Invariants

Bổ sung bộ invariant chính thức:

### Execution

**AGPU-24 — GPU Is An Execution Domain, Not A Separate Language**

GPU code sử dụng cùng semantic core của Axiom.

**AGPU-25 — Kernel Entry Is Explicit**

GPU dispatch không xảy ra implicit từ function call.

**AGPU-26 — Kernel Legality Is Checked Transitively**

Một kernel không được gọi dependency host-only.

**AGPU-27 — Execution Domain Is A Semantic Property**

Function/device compatibility là compiler-visible semantic property.

### Memory

**AGPU-28 — Device Memory Ownership Is Explicit**

Device allocation phải có owner/storage contract rõ ràng.

**AGPU-29 — Device Views Do Not Transfer Ownership**

`view`/`mut_view` trên device không sở hữu storage.

**AGPU-30 — Host And Device Address Spaces Are Distinct**

Không implicit cast giữa host/device pointers.

**AGPU-31 — Address-Space Conversion Is Explicit**

Conversion phải được compiler chứng minh hoặc nằm trong unsafe/system abstraction.

**AGPU-32 — Live Device Capabilities Block Invalid Resource Destruction**

Owner không được bị destroy khi device capability còn live.

**AGPU-33 — In-Flight Operations Must Retain Valid Resources**

GPU operation không được truy cập resource đã mất hiệu lực.

**AGPU-34 — Relocation Cannot Invalidate Live Device Capabilities**

Relocatable device storage phải tôn trọng capability lifetime.

### Transfer

**AGPU-35 — Host/Device Transfer Is Explicit**

Không có implicit host-device transfer.

**AGPU-36 — Transfer Is Not Ordinary Value Copy**

Transfer có resource/time/failure semantics riêng.

**AGPU-37 — Unified Memory Does Not Imply Synchronization**

Cùng address space không đồng nghĩa happens-before.

### Synchronization

**AGPU-38 — GPU Synchronization Is Explicit**

Barrier/event/fence semantics phải được biểu diễn trong program hoặc abstraction contract.

**AGPU-39 — Device Events Establish Synchronization Only According To Their Contract**

Không suy đoán semantics của event.

**AGPU-40 — GPU Barriers Have Explicit Scope**

Barrier chỉ đồng bộ execution scope mà contract quy định.

**AGPU-41 — Collective Barriers Require Valid Convergence**

Kernel không được tạo invalid divergent collective synchronization.

### Atomics

**AGPU-42 — GPU Atomics Reuse Axiom Ordering Semantics**

GPU không có memory model hoàn toàn khác ở semantic level.

**AGPU-43 — GPU Atomic Scope Is Additional To Ordering**

Scope và ordering là hai dimensions khác nhau.

**AGPU-44 — Atomic Storage Cannot Be Accessed As Ordinary Mutable Storage**

Không có implicit atomic→`mut_view`.

### ABI

**AGPU-45 — Kernel ABI Is Distinct From Host ABI**

Device calling convention/layout là contract riêng.

**AGPU-46 — Kernel Parameters Must Be Device-Representable**

Unsupported representations bị compile error.

**AGPU-47 — Kernel ABI Does Not Alter Source Semantics**

ABI lowering chỉ là representation lowering.

### Error

**AGPU-48 — Recoverable Device Failure Uses Result**

Host-visible device/API failures là `Result`.

**AGPU-49 — Kernel Trap Is Distinct From Recoverable Device Error**

Trap/panic không tự động trở thành Result.

**AGPU-50 — GPU Has No Implicit Exception/Unwind Runtime**

Không có exception runtime bắt buộc trên device.

### Optimization

**AGPU-51 — Kernel Fusion Must Preserve Observable Semantics**

**AGPU-52 — Device Placement Is Optimizable Unless Observable**

**AGPU-53 — Transfer Elimination Requires Semantic Proof**

**AGPU-54 — Synchronization Cannot Be Weakened By Optimization**

**AGPU-55 — Atomic Semantics Cannot Be Weakened By Optimization**

### Generalization

**AGPU-56 — Accelerator Model Is Generalized Beyond GPU**

GPU chỉ là một execution backend.

**AGPU-57 — Device APIs Must Preserve Common Ownership Semantics**

**AGPU-58 — Device APIs Must Preserve Common Capability Semantics**

**AGPU-59 — Device Execution Must Not Introduce A Second Ownership Model**

**AGPU-60 — One Language Semantics, Many Execution Domains**

---

# XX.45. Chốt Part XX

Sau phần này, mô hình Axiom đã có:

```text
CPU
 │
 ├── Thread
 ├── Task
 └── Async
       
Accelerator
 │
 ├── Device
 ├── Queue
 ├── Buffer
 ├── Kernel
 └── Event
       
Memory
 │
 ├── Host
 ├── Device
 ├── Shared
 ├── Local
 ├── Private
 ├── Constant
 └── External
```

nhưng tất cả vẫn quay về một semantic foundation:

```text
Type
Ownership
Capability
Lifetime
Synchronization
Error
ABI
```

Đây là điểm rất quan trọng cho mục tiêu ban đầu của Axiom: **không hy sinh hiệu năng thấp tầng để có abstraction cao tầng**, nhưng cũng không bắt programmer phải học hai hoặc ba memory models khác nhau.

---

# Part XXI — Comptime · Reflection · Compile-Time Programming

Phần tiếp theo nên xử lý một vấn đề cực quan trọng đối với Axiom:

> **Làm sao có metaprogramming mạnh như Rust/modern C++ nhưng không biến compiler thành một mớ macro/plugin khó kiểm soát?**

Hướng đã chọn trước đó là:

```text
const
comptime
@derive
compile-time reflection
generated artifacts
```

thay vì macro language tự do.

Đích đến là:

```text
Source
  ↓
Normal type system
  ↓
Normal ownership rules
  ↓
Normal MIR
  ↓
Compile-time execution
```

tức là **comptime không phải một ngôn ngữ thứ hai**.