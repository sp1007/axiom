# BOOTSTRAP-200 — AI, Tensor, Automatic Differentiation & Heterogeneous Computing

**TRẠNG THÁI: FROZEN / COMPLETED**

Mục tiêu:

> **Axiom phải cho phép xây hệ thống AI/ML hiệu năng native trên CPU, GPU và accelerator mà không biến ngôn ngữ thành Python động hoặc bắt buộc một AI runtime khổng lồ.**

Kiến trúc thống nhất:

```text
Axiom
│
├── Scalar
├── SIMD
├── Matrix
├── Tensor
│
├── Automatic Differentiation
│
├── Tensor Graph
│
├── CPU Backend
├── GPU Backend
└── Accelerator Backend
```

---

## 200.1. Tensor không thuộc Core

Core chỉ cần:

```text
array
struct
generic
const
comptime
SIMD primitives
```

`Tensor` là library/compiler-aware abstraction.

Điều này giữ cho:

```text
hello.exe
```

không biết tensor là gì.

---

# 200.2. Tensor là typed value

Conceptually:

```axiom
Tensor<T, Shape, Layout>
```

Ví dụ:

```axiom
Tensor<f32, [32, 768]>
Tensor<f16, [1, 3, 224, 224]>
```

Nhưng không bắt buộc mọi dimension phải compile-time.

---

# 200.3. Static và dynamic shape

Axiom hỗ trợ cả:

```text
StaticShape
DynamicShape
```

Ví dụ:

```axiom
Tensor<f32, [32, 768]>
```

và:

```axiom
Tensor<f32, Dynamic>
```

---

# 200.4. Shape không phải một runtime object bắt buộc

Static shape có thể biến mất hoàn toàn sau compilation.

Ví dụ:

```text
Tensor<f32, [1024, 768]>
```

compiler có thể dùng `1024` và `768` để:

- vectorize
- tile
- specialize
- eliminate bounds checks
- chọn kernel

không cần lưu shape runtime nếu không cần.

---

# 200.5. Dynamic shape

Dynamic tensor giữ:

```text
shape
stride
storage
dtype
device
```

nhưng vẫn là strongly typed.

Không biến thành:

```text
AnyTensor
```

hay dynamic object.

---

# 200.6. Shape arithmetic

Comptime có thể tính:

```text
[N, M] × [M, K] → [N, K]
```

Nếu không hợp lệ:

```text
[N, M] × [K, P]
```

compiler có thể báo lỗi ngay khi các dimension được biết tại compile time.

Nếu dynamic:

```text
runtime shape check
```

được sinh ra.

---

# 200.7. Shape type không được làm compiler quá phức tạp

Chỉ hỗ trợ compile-time shape reasoning ở mức cần thiết.

Không biến type system thành theorem prover.

Mục tiêu:

```text
simple common cases
+
comptime constraints
+
runtime checks when necessary
```

---

# 200.8. Tensor layout

Tensor không chỉ có shape.

Cần:

```text
Shape
Stride
Layout
DType
Storage
Device
```

Ví dụ:

```text
NCHW
NHWC
blocked
contiguous
strided
```

---

# 200.9. View không copy

Các thao tác:

```text
slice
reshape
transpose
narrow
broadcast
```

có thể trả về view nếu layout cho phép.

Không mặc định copy.

---

# 200.10. Tensor view

Conceptually:

```text
TensorView<T, Shape, Layout>
```

là non-owning capability.

Nó tuân theo:

```text
view
mut_view
provenance
region
lifetime
```

đã có trong Axiom.

---

# 200.11. Mutable tensor view

```text
TensorMutView<T>
```

không được phép có overlapping mutable regions nếu compiler không chứng minh an toàn.

Ví dụ:

```text
A[:, 0]
A[:, 1]
```

có thể được chứng minh disjoint.

---

# 200.12. Broadcasting

Broadcasting là semantic operation.

Compiler phải phân biệt:

```text
broadcast view
```

với:

```text
materialized copy
```

Broadcast không tự động tạo một tensor khổng lồ.

---

# 200.13. Tensor ownership

Tensor sở hữu storage:

```text
Tensor
 └── Storage
```

Move:

```text
a → b
```

chuyển ownership.

Copy chỉ xảy ra nếu type có semantic `Copy`, điều này thường **không áp dụng cho tensor storage lớn**.

---

# 200.14. Clone

Explicit:

```axiom
b = a.clone()
```

nếu cần duplicate dữ liệu.

Compiler không được tự ý biến Move thành Clone.

---

# 200.15. Device-aware Tensor

Tensor có storage domain:

```text
CPU
GPU
NPU
External
Unified
```

Ví dụ concept:

```text
Tensor<f32> @ CPU
Tensor<f32> @ GPU
```

Không implicit transfer.

---

# 200.16. CPU → GPU

Phải explicit:

```text
tensor.to(device)
```

hoặc async:

```text
tensor.to_async(device)
```

Compiler có thể eliminate transfer nếu chứng minh resource đã ở đúng device.

---

# 200.17. Device placement

Graph runtime có thể quyết định:

```text
A → CPU
B → GPU
C → GPU
```

nhưng semantic transfer vẫn phải được biểu diễn.

Không được che giấu một PCIe transfer đắt tiền sau một phép toán tưởng như đơn giản.

---

# 200.18. Tensor operation model

Các operator cơ bản:

```text
add
sub
mul
div
matmul
conv
reduce
reshape
transpose
softmax
normalize
```

được xây dưới dạng generic functions/traits.

Không cần built-in syntax cho từng operator.

---

# 200.19. Operator traits

Conceptually:

```axiom
trait Add<T> {
    type Output
    fn add(...)
}
```

Nhưng compiler có thể nhận diện các operation quan trọng để optimize.

---

# 200.20. Operator fusion

Ví dụ:

```text
y = relu(a * b + c)
```

thay vì:

```text
matmul
 ↓
temporary
 ↓
add
 ↓
temporary
 ↓
relu
```

compiler/graph optimizer có thể tạo:

```text
fused kernel
```

---

# 200.21. Eager execution

Axiom hỗ trợ eager semantics:

```axiom
let y = relu(x);
```

và operation thực hiện ngay nếu API chọn eager tensor.

Đây là semantic model đơn giản.

---

# 200.22. Lazy graph

Framework có thể có:

```text
GraphTensor
```

hoặc:

```text
TensorGraph
```

để xây computation graph.

Ví dụ:

```text
Input
 ↓
MatMul
 ↓
Add
 ↓
ReLU
 ↓
Output
```

Graph là library abstraction, không phải language semantics.

---

# 200.23. Eager và graph không được nhập nhằng

```text
Tensor<T>
```

và:

```text
GraphTensor<T>
```

nên là những semantic types khác nhau.

Điều này tránh tình trạng:

```text
x + y
```

lúc thì thực hiện ngay, lúc thì tạo node graph mà programmer không biết.

---

# 200.24. Graph compilation

Graph:

```text
Graph
 ↓
Shape inference
 ↓
Constant folding
 ↓
Dead node elimination
 ↓
Operator fusion
 ↓
Memory planning
 ↓
Device placement
 ↓
Kernel selection
 ↓
CompiledGraph
```

---

# 200.25. CompiledGraph

Sau compilation:

```text
CompiledGraph
```

có thể được cache.

Cache identity bao gồm:

```text
graph fingerprint
+
dtype
+
shape
+
device
+
features
+
compiler version
+
optimization profile
```

---

# 200.26. Memory planning

Graph:

```text
A
 ↓
B
 ↓
C
```

nếu `A` không còn dùng sau B, memory của A có thể được reuse cho C.

Đây là:

```text
liveness-based tensor memory planning
```

tương tự register/allocation optimization của compiler.

---

# 200.27. Tensor allocation elimination

Nếu tensor trung gian không escape:

```text
A → B → C
```

compiler có thể:

- fuse
- scalarize
- reuse buffer
- eliminate allocation

---

# 200.28. Automatic Differentiation

Axiom hỗ trợ AD ở library/compiler layer.

Hai mode:

```text
Forward Mode
Reverse Mode
```

---

# 200.29. Forward AD

Ví dụ concept:

```text
Dual<T>
```

mang:

```text
value
derivative
```

Có thể phù hợp cho:

- ít input
- nhiều output
- Jacobian-vector product

---

# 200.30. Reverse AD

Graph:

```text
forward
 ↓
record operations
 ↓
backward
```

phù hợp deep learning.

Không bắt buộc GC.

Tape/graph storage là explicit resource.

---

# 200.31. Gradient là value

Gradient không phải magic hidden mutable state.

Conceptually:

```text
Gradient<T>
```

hoặc:

```text
TensorGradient
```

tuân theo ownership bình thường.

---

# 200.32. Gradient accumulation

Nếu:

```text
z = f(x) + g(x)
```

gradient của `x` cần accumulate.

Framework quản lý:

```text
gradient buffer
```

với ownership/synchronization rõ ràng.

---

# 200.33. `requires_grad`

Không cần biến thành dynamic runtime flag nếu compile-time biết.

Có thể có type-level differentiation:

```text
Differentiable<T>
```

hoặc compiler-generated derivative.

---

# 200.34. AD compiler transformation

Compiler có thể biến:

```text
fn f(x: Tensor<f32>) -> Tensor<f32>
```

thành:

```text
f
df/dx
```

nhưng generated function phải:

```text
resolve
typecheck
ownership verify
capability verify
GPU verify
```

như code bình thường.

---

# 200.35. AD không bypass compiler

Đây là invariant quan trọng.

Không cho:

```text
AD engine
 ↓
raw generated machine code
```

bỏ qua Axiom verifier.

---

# 200.36. Differentiability traits

Một function có thể được AD nếu operations bên trong có derivative rule.

Nếu gặp:

```text
File.read()
```

thì không có derivative semantics.

Compiler báo:

```text
operation is not differentiable
```

---

# 200.37. Custom derivative

Framework có thể cung cấp:

```text
derivative_of
```

nhưng derivative implementation vẫn phải được compiler verify.

---

# 200.38. Stop-gradient

Có semantic operation:

```text
stop_gradient(x)
```

để ngăn gradient propagation.

Không phải ownership operation.

---

# 200.39. In-place mutation

AI framework thường muốn:

```text
x += y
```

Axiom phải xử lý bằng capability/alias rules.

Nếu tensor có unique mutable ownership:

```text
mut_view<x>
```

in-place có thể hợp lệ.

Nếu có live read views:

```text
reject
```

hoặc materialize/copy theo API contract.

---

# 200.40. In-place không được tự động copy

Axiom không được âm thầm:

```text
x += y
```

thành:

```text
new_x = clone(x)
...
```

chỉ để tránh ownership conflict.

Nếu API yêu cầu copy thì copy phải có semantic reason/explicit abstraction.

---

# 200.41. Tensor mutation và async

Tensor view không được sống qua `.await` nếu storage có thể thay đổi/relocate.

Tensor owner có thể sống qua await nếu thỏa điều kiện Send/storage.

---

# 200.42. CPU vectorization

Tensor kernels CPU sử dụng:

```text
SIMD
loop optimization
tiling
cache optimization
parallel execution
```

Compiler backend tận dụng `ANUM` đã khóa.

---

# 200.43. GPU kernel

Tensor operation có thể lower thành:

```text
@kernel
```

hoặc specialized backend kernel.

---

# 200.44. NPU/accelerator

Axiom không giả định accelerator là GPU.

Execution domain có thể mở rộng:

```text
CPU
GPU
NPU
TPU-like accelerator
DSP
FPGA
```

Storage/synchronization contract tương ứng.

---

# 200.45. Accelerator backend

Conceptually:

```text
AcceleratorDevice
AcceleratorBuffer
AcceleratorEvent
AcceleratorKernel
```

nhưng framework có thể unify API nơi semantics tương thích.

---

# 200.46. Quantization

Dtype:

```text
f32
f16
bf16
fp8
i8
u8
i4
```

là library/compiler-supported numeric types.

Không phải mọi type đều cần Core primitive ngay từ đầu.

---

# 200.47. Quantization semantics

Không cho implicit:

```text
f32 → i8
```

nếu có thay đổi semantic đáng kể.

Phải explicit:

```text
quantize
dequantize
```

---

# 200.48. Mixed precision

Graph có thể:

```text
weights: f16
accumulator: f32
output: f16
```

Compiler biết các type chính xác.

---

# 200.49. Tensor memory format

Compiler có thể chọn:

```text
NCHW
NHWC
blocked
tiled
```

nếu observable semantics không thay đổi.

Physical layout được tách khỏi logical tensor semantics khi API không expose layout.

---

# 200.50. Layout transformation

Nếu backend cần:

```text
NCHW → NHWC
```

compiler/runtime có thể insert conversion.

Tooling phải cho developer biết conversion đó tồn tại vì nó có thể có cost lớn.

---

# 200.51. Operator selection

Ví dụ `matmul` có thể chọn:

```text
naive
SIMD
BLAS
GPU
tensor core
NPU
```

nhưng Axiom package/framework không được giả định một backend duy nhất.

---

# 200.52. External accelerator libraries

Interop với:

```text
CUDA
ROCm
oneDNN
vendor NPU
```

được thực hiện qua FFI/plugin contracts.

Không trở thành dependency bắt buộc của Axiom.

---

# 200.53. BLAS-style backend

Một tensor library có thể dùng external BLAS nếu user chọn.

Nhưng:

```text
Axiom language
```

không phụ thuộc BLAS.

---

# 200.54. Model representation

AI model có thể là:

```text
struct
tensor
graph
parameter set
```

Không cần class hierarchy.

---

# 200.55. Parameter ownership

Model:

```text
Model
 └── Parameters
       ├── Weight
       ├── Bias
       └── ...
```

Model sở hữu parameters.

Optimizer có thể nhận:

```text
mut_view<Parameters>
```

nếu ownership/capability cho phép.

---

# 200.56. Optimizer

SGD/Adam/etc. là library algorithms.

Không cần compiler intrinsic.

---

# 200.57. Training loop

Có thể viết gần native:

```axiom
for batch in dataset {
    let output = model.forward(batch)
    let loss = loss_fn(output, target)

    let gradients = backward(loss)
    optimizer.step(model, gradients)
}
```

Nhưng semantics vẫn:

```text
ordinary functions
ownership
iterators
async
GPU
tensor
```

không phải dynamic Python objects.

---

# 200.58. Inference

Inference profile có thể loại bỏ:

```text
autodiff
gradient buffers
training graph
optimizer
```

nếu không sử dụng.

---

# 200.59. Dead stripping AI runtime

Model inference binary chỉ cần:

```text
Tensor
selected kernels
allocator
GPU backend
model data
```

không cần training runtime.

---

# 200.60. Model serialization

Model format tách khỏi Tensor semantics.

Có:

```text
Axiom Model Format
```

hoặc adapters:

```text
ONNX
Safetensors
GGUF
vendor formats
```

---

# 200.61. Safe model loading

Model file là external input.

Parser phải:

```text
validate
bounds-check
validate dtype
validate shape
validate offsets
```

trước khi biến thành safe tensor/resource.

---

# 200.62. Memory-mapped model

Large model có thể sử dụng:

```text
MemoryMappedFile
```

và lazy/mapped storage.

Nhưng file mapping là OS resource, không phải Tensor Core primitive.

---

# 200.63. Zero-copy model loading

Nếu format/layout tương thích:

```text
model file
 ↓
mapped memory
 ↓
Tensor view
```

có thể zero-copy.

Nếu không tương thích, explicit conversion.

---

# 200.64. Distributed AI

Distributed execution không thuộc Core.

Library có:

```text
Process
Network
Channel
SharedMemory
Collective
```

dựa trên concurrency/IPC model đã khóa.

---

# 200.65. Distributed tensor

Tensor có thể có:

```text
Shard
Replica
Partition
```

và communication:

```text
all_reduce
all_gather
broadcast
reduce_scatter
```

nhưng đây là library semantics.

---

# 200.66. Ownership trong distributed system

`Send` không có nghĩa:

```text
network serialization
```

đã được định nghĩa ở IPC/FFI architecture.

Distributed transfer cần:

```text
serialize
copy
ownership protocol
```

explicit.

---

# 200.67. AI graph + async

Graph execution có thể trả:

```text
Future<Tensor>
```

hoặc:

```text
GpuEvent
```

depending on abstraction.

Không biến mọi Tensor operation thành implicit Future.

---

# 200.68. Compilation tiers

AI workload có thể chạy:

```text
Tier 0: eager
Tier 1: specialized kernel
Tier 2: graph optimized
Tier 3: fully compiled model
```

Mỗi tier giữ cùng semantic result contract.

---

# 200.69. AOT model compilation

Model có thể compile thành:

```text
.axmodel
```

chứa:

```text
graph
weights
kernel artifacts
metadata
target information
```

hoặc binary package tùy distribution layer.

---

# 200.70. JIT

JIT là optional runtime capability.

Không đưa JIT vào mọi Axiom executable.

---

# 200.71. Comptime model specialization

Nếu shape/parameters biết compile-time:

```text
comptime
```

có thể generate specialized implementation.

Ví dụ:

```text
MatMul<768, 768, 3072>
```

có thể tạo specialized kernel.

---

# 200.72. Runtime specialization

Nếu shape chỉ biết runtime:

```text
dispatcher
```

chọn kernel phù hợp.

Ví dụ:

```text
N=32 → kernel_A
N=128 → kernel_B
N=dynamic → generic
```

---

# 200.73. AI compiler boundary

AI compiler có thể tối ưu:

```text
Graph
 ↓
Tensor IR
 ↓
Kernel IR
 ↓
GPU/CPU backend
```

nhưng semantic source remains Axiom.

---

# 200.74. Tensor IR

Đề xuất thêm một IR chuyên dụng:

```text
TensorIR
```

nằm giữa high-level graph và kernel MIR:

```text
Axiom
 ↓
Typed HIR
 ↓
MIR
 ↓
Tensor Graph
 ↓
TensorIR
 ↓
Kernel MIR
 ↓
Machine/GPU
```

TensorIR chỉ được tạo khi workload cần tensor optimization.

---

# 200.75. TensorIR không thay thế MIR

MIR vẫn là semantic authority.

TensorIR là optimization representation.

Nếu TensorIR transformation sai:

```text
reference semantics
```

vẫn là authority.

---

# 200.76. Fusion legality

Fusion chỉ được thực hiện nếu:

```text
effects
ownership
alias
numerical contract
device dependencies
```

cho phép.

Không fuse chỉ vì operation nhìn có vẻ độc lập.

---

# 200.77. Numerical equivalence

Ví dụ:

```text
(a + b) + c
```

không mặc định tương đương:

```text
a + (b + c)
```

với floating point.

Fusion/reassociation chỉ được phép nếu:

```text
strict FP
```

cho phép hoặc developer chọn relaxed/fast-math semantics.

---

# 200.78. Autodiff + numerical semantics

Generated derivative cũng phải tuân theo numerical profile.

Không được coi derivative là phép biến đổi toán học trừu tượng rồi bỏ qua floating-point semantics.

---

# 200.79. AI debugging

CompilerDB có thể expose:

```text
ax explain tensor
ax explain kernel
ax explain graph
ax explain allocation
ax explain transfer
```

Ví dụ:

```text
Tensor transfer:
CPU → GPU
reason: operation requires GPU storage

Allocation:
temporary buffer 16 MB
lifetime: node 12 → node 17

Fusion:
matmul + bias + relu
status: applied
```

Đây rất phù hợp với AI agent.

---

# 200.80. AI compiler interface

AI agent không cần đọc toàn bộ graph/source để biết vấn đề.

Có thể query:

```text
Type
Shape
Layout
Device
Ownership
Capability
Effect
Transfer
Kernel
Fusion
Allocation
```

và compiler trả structured facts.

---

# 200.81. AI-native optimization loop

Axiom có thể hỗ trợ:

```text
AI agent
   ↓
query compiler
   ↓
identify bottleneck
   ↓
propose source change
   ↓
compile
   ↓
benchmark
   ↓
compare
   ↓
accept/reject
```

Compiler vẫn là authority.

AI không được tự sửa semantic facts.

---

# 200.82. Không biến AI optimization thành magic

Axiom không nên có:

```text
@ai_optimize
```

mà thay đổi semantics không thể đoán.

AI chỉ sử dụng:

```text
CompilerDB
Optimization Explorer
Benchmark
Profile
```

---

# 200.83. Tensor memory safety

Các lỗi như:

```text
out-of-bounds
use-after-free
double free
overlapping mutable views
invalid device resource
```

phải tuân verifier.

GPU code cũng không phải ngoại lệ.

---

# 200.84. Accelerator safety

External accelerator có thể không có đầy đủ memory safety.

Boundary:

```text
unsafe/external contract
```

phải thiết lập preconditions.

Sau đó safe abstraction trở lại verifier.

---

# 200.85. Tensor invariants — `ATENSOR`

### `ATENSOR-20`
Tensor is a library/compiler-aware abstraction, not a mandatory Core type.

### `ATENSOR-21`
Tensor storage shall obey Axiom ownership semantics.

### `ATENSOR-22`
Tensor views shall obey Axiom capability and provenance semantics.

### `ATENSOR-23`
Static shape information may participate in compile-time verification.

### `ATENSOR-24`
Dynamic shapes shall remain type-safe and receive runtime validation where required.

### `ATENSOR-25`
Shape incompatibility shall be diagnosed at compile time whenever provable.

### `ATENSOR-26`
Tensor layout shall be explicitly represented when observable.

### `ATENSOR-27`
Logical tensor semantics shall remain distinct from physical storage layout.

### `ATENSOR-28`
Tensor views shall not implicitly copy data.

### `ATENSOR-29`
Tensor storage shall not be implicitly transferred between devices.

### `ATENSOR-30`
Tensor mutation shall obey capability exclusivity.

### `ATENSOR-31`
Tensor cloning shall be explicit unless semantic Copy is independently established.

### `ATENSOR-32`
Broadcasting shall not implicitly materialize full storage.

### `ATENSOR-33`
Eager tensors and graph tensors shall have distinct semantics.

### `ATENSOR-34`
Graph optimization shall preserve observable tensor semantics.

### `ATENSOR-35`
Graph memory planning may reuse storage only after lifetime compatibility is proven.

### `ATENSOR-36`
Operator fusion shall preserve ownership, effects, synchronization and numerical semantics.

### `ATENSOR-37`
Floating-point reassociation shall obey the selected numerical contract.

### `ATENSOR-38`
Automatic differentiation shall generate ordinary verifiable Axiom semantics.

### `ATENSOR-39`
Generated derivative code shall pass normal type, ownership and capability verification.

### `ATENSOR-40`
Stop-gradient shall be explicit.

### `ATENSOR-41`
Gradient accumulation shall obey ordinary ownership and concurrency rules.

### `ATENSOR-42`
Tensor operations shall support CPU and accelerator backends without changing language semantics.

### `ATENSOR-43`
GPU tensor execution shall use the established GPU resource/synchronization model.

### `ATENSOR-44`
Accelerator interop shall use explicit foreign-resource contracts.

### `ATENSOR-45`
Quantization and reduced-precision conversions shall be explicit where semantic information is lost.

### `ATENSOR-46`
Mixed precision shall retain explicit operand and accumulation types.

### `ATENSOR-47`
AI runtime components shall be optional and removable when unused.

### `ATENSOR-48`
Inference builds shall be able to exclude training/autodiff components.

### `ATENSOR-49`
Model loading shall validate external data before exposing safe tensor resources.

### `ATENSOR-50`
Memory mapping shall remain an explicit storage/resource abstraction.

### `ATENSOR-51`
Distributed tensor movement shall not be confused with local ownership transfer.

### `ATENSOR-52`
TensorIR shall be an optimization representation, not the semantic authority.

### `ATENSOR-53`
Tensor optimizations shall remain subject to compiler correctness validation.

### `ATENSOR-54`
AI tooling shall expose structured tensor/compiler facts.

### `ATENSOR-55`
Tensor compilation and kernel artifacts shall participate in deterministic cache identity.

### `ATENSOR-56`
Axiom shall support static and dynamic tensor shapes without requiring a dynamic object model.

### `ATENSOR-57`
Axiom shall support CPU, GPU and accelerator execution under one semantic resource model.

### `ATENSOR-58`
AI functionality shall not require a mandatory garbage collector.

### `ATENSOR-59`
AI functionality shall not require a mandatory global runtime.

### `ATENSOR-60`
Axiom AI abstractions shall preserve native compilation and zero-cost abstraction goals wherever semantics permit.

---

# Kiến trúc AI cuối cùng

```text
                         AXIOM
                           │
             ┌─────────────┴─────────────┐
             │                           │
          Ordinary                    Tensor
          Program                       │
                                        ▼
                               Tensor / Graph API
                                        │
                         ┌──────────────┼──────────────┐
                         ▼              ▼              ▼
                       CPU            GPU           Accelerator
                         │              │              │
                         └──────────────┼──────────────┘
                                        ▼
                                  TensorIR
                                        │
                              ┌─────────┴─────────┐
                              ▼                   ▼
                         Kernel MIR          Graph Runtime
                              │                   │
                              ▼                   ▼
                           Native              Async
                           Machine             Execution
```

Điểm tôi đánh giá là quan trọng nhất của thiết kế này:

> **Axiom không cần trở thành “Python nhưng nhanh hơn”.**

Thay vào đó, AI code vẫn là **code Axiom bình thường**:

```text
strong typing
+
ownership
+
capability
+
generic
+
comptime
+
SIMD
+
GPU
+
Tensor library
+
compiler optimization
```

Vì vậy cùng một compiler có thể đi từ:

```text
C-like systems code
       ↓
SIMD
       ↓
GPU kernel
       ↓
Tensor
       ↓
Autodiff
       ↓
AI model
```

mà không phải chuyển sang một execution model hoàn toàn khác.

---

# BOOTSTRAP-201 — Audio, DSP, Signal Processing & Media Pipeline

**TRẠNG THÁI: NEXT**

Sau graphics + AI, một mảng rất đáng khóa tiếp theo là **audio/media**, vì nó sẽ quyết định Axiom có đủ khả năng làm:

```text
game engine
DAW
TTS
STT
audio editor
video editor
codec
streaming
real-time DSP
AI audio
```

hay không.

Phần 201 sẽ tập trung vào:

```text
AudioBuffer
Sample
Channel
Frame
Stream
DSP
SIMD DSP
FFT
Filter
Resampler
Mixer
Audio Graph
Real-time Thread
Lock-free Ring Buffer
Codec
Video Frame
Media Pipeline
GPU Video
Hardware Encoder/Decoder
```

Đặc biệt sẽ phải giải quyết một vấn đề rất quan trọng đối với triết lý Axiom:

> **Làm thế nào để compiler hiểu real-time constraints đủ sâu để tránh allocation, lock, blocking và GC-like behavior trong audio callback, nhưng không biến realtime programming thành một đống annotation/lifetime bureaucracy.**