# BOOTSTRAP-209 — AI/ML, Tensor, Automatic Differentiation & Heterogeneous Computing

**TRẠNG THÁI: FROZEN / COMPLETED**

Mục tiêu của 209 là để Axiom có thể xây dựng được:

- AI inference
- training
- tensor framework
- automatic differentiation
- custom kernels
- CPU SIMD/GPU acceleration
- quantization
- sparse computation
- distributed training

mà **không biến AI thành thành phần bắt buộc của Core** và không biến Axiom thành một bản sao của PyTorch.

Nguyên tắc trung tâm:

> **Tensor là abstraction của library; Shape/Layout/DType là semantic metadata; Kernel là computation; compiler/backend chịu trách nhiệm tối ưu và chọn CPU/GPU execution.**

---

# 209.1. Không đưa Tensor vào Core

Core chỉ cần những primitive đã có:

```text
Ownership
Capability
Generic
Comptime
SIMD
GPU
Async
Concurrency
Execution Domain
Storage Domain
```

Tensor nằm ở:

```text
Axiom Core
    │
    ├── SIMD
    ├── GPU
    ├── Comptime
    └── Generic
          │
          ▼
      Tensor Library
          │
     ┌────┼────┐
     ▼    ▼    ▼
    CPU  GPU  Accelerator
```

Điều này giữ được chương trình C-like cực nhỏ:

```axiom
fn main() {
    println("hello")
}
```

không kéo theo AI runtime.

---

# 209.2. Tensor không đồng nghĩa với Matrix

Cần phân biệt:

```text
Scalar
Vector
Matrix
Tensor
```

Tensor là N-dimensional array.

Ví dụ:

```text
Tensor<f32, [224,224,3]>
```

---

# 209.3. Shape là semantic metadata

Shape không nên chỉ là runtime `Vec<usize>`.

Compiler cần hiểu:

```text
[Batch, Height, Width, Channels]
```

nếu shape được biết tại compile time.

---

# 209.4. Static shape

Cho phép:

```axiom
Tensor<f32, [3, 224, 224]>
```

Compiler biết:

```text
rank = 3
shape = [3,224,224]
```

và có thể loại bỏ nhiều runtime check.

---

# 209.5. Dynamic shape

Vẫn phải hỗ trợ:

```axiom
Tensor<f32, DynShape>
```

cho model thực tế.

Ví dụ:

```text
batch = dynamic
sequence_length = dynamic
```

---

# 209.6. Shape không nên là type quá nặng

Không biến mọi phép toán tensor thành hệ thống dependent type khổng lồ.

Ví dụ:

```text
A : [M,K]
B : [K,N]
```

có thể được compiler kiểm tra nếu M/K/N known.

Nếu dynamic:

```text
runtime shape check
```

chứ không làm type system trở nên không sử dụng được.

---

# 209.7. Shape constraints

Tensor operation có thể khai báo:

```text
MatMul:
[A,B] × [B,C] → [A,C]
```

Compiler có thể kiểm tra constraint.

---

# 209.8. Layout

Shape chưa đủ.

Tensor cần:

```text
Shape
Stride
Offset
Layout
```

Ví dụ:

```text
NCHW
NHWC
CHWN
```

không nên là các Tensor type hoàn toàn khác nhau.

---

# 209.9. Stride

Một Tensor view có thể:

```text
shape = [3,224,224]
stride = [50176,224,1]
```

hoặc layout khác.

Stride là semantic metadata cần thiết cho zero-copy view.

---

# 209.10. Contiguous

Compiler/library có thể phân biệt:

```text
Contiguous
Strided
Broadcasted
Permuted
Sparse
Opaque
```

để chọn kernel.

---

# 209.11. TensorView

Không cần copy khi slicing:

```axiom
view<Tensor>
```

hoặc semantic equivalent:

```text
TensorView<T>
```

là non-owning.

Nó tuân theo capability model đã frozen.

---

# 209.12. Mutable tensor view

```text
TensorMutView<T>
```

tương ứng với:

```text
mut_view<T>
```

và phải tuân thủ exclusive mutation.

---

# 209.13. Tensor relocation

Nếu Tensor sở hữu storage:

```text
Tensor<T>
```

thì storage có thể relocate.

Một view đang sống sẽ ngăn relocation nếu relocation làm mất provenance.

---

# 209.14. Tensor storage

Tensor có thể nằm ở:

```text
CPU
GPU
Unified
PinnedHost
Mapped
External
```

nhưng storage domain phải explicit.

---

# 209.15. Device Tensor

Ví dụ:

```text
DeviceTensor<f32>
```

không được implicit đọc như CPU memory.

Phải có operation tương ứng:

```text
copy_to_host()
copy_to_device()
```

hoặc backend-specific transfer.

---

# 209.16. Zero-copy

Compiler có thể loại bỏ transfer nếu:

```text
same storage domain
compatible layout
compatible lifetime
compatible capability
```

Nhưng zero-copy là **optimization/proven property**, không phải assumption.

---

# 209.17. DType

Không chỉ:

```text
f32
f64
```

mà tensor library cần:

```text
f16
bf16
i8
u8
i4
u4
fp8
```

tùy target.

---

# 209.18. DType ≠ Axiom primitive type

Ví dụ:

```text
Tensor<fp8>
```

có thể là storage format.

Không nhất thiết Core phải có:

```text
fp8
```

như một scalar language type ngay từ đầu.

---

# 209.19. Quantized Tensor

Semantic metadata:

```text
Quantization
    dtype
    scale
    zero_point
    axis
```

để compiler/kernel biết cách diễn giải.

---

# 209.20. Tensor ownership

Tensor là ordinary owning value:

```text
Tensor<T>
```

có thể Move.

Không implicit shared mutable state.

---

# 209.21. Tensor Copy

Tensor lớn không được implicit Copy.

```text
Tensor<T>
```

thông thường:

```text
!Copy
```

Copy logic phải explicit:

```text
clone()
```

hoặc:

```text
copy_to(...)
```

---

# 209.22. Tensor expression

API có thể viết:

```axiom
C = A * B + D
```

nhưng compiler/library nên có khả năng biểu diễn expression graph:

```text
Mul(A,B)
   ↓
Add(_,D)
```

---

# 209.23. Expression templates không phải bắt buộc

Axiom không cần ép programmer dùng expression-template syntax.

Compiler có thể tạo intermediate representation trực tiếp.

---

# 209.24. Tensor IR

Compiler có thể có:

```text
TensorIR
```

sau semantic MIR:

```text
MIR
 ↓
Tensor Analysis
 ↓
TensorIR
 ↓
Kernel IR
 ↓
CPU/GPU backend
```

TensorIR không thay thế MIR.

---

# 209.25. Tensor operation

Các primitive:

```text
Add
Sub
Mul
Div
MatMul
Conv
Reduce
Transpose
Reshape
Broadcast
Gather
Scatter
Softmax
Norm
```

được biểu diễn ở library/compiler interface.

---

# 209.26. Broadcasting

Broadcasting phải có deterministic rules.

Ví dụ:

```text
[32,128]
+
[128]
=
[32,128]
```

Shape inference có thể kiểm tra compile-time nếu đủ thông tin.

---

# 209.27. Broadcast không copy

Broadcast view có thể biểu diễn stride bằng zero hoặc semantic equivalent.

Compiler không được biến broadcasting thành allocation/copy nếu không cần.

---

# 209.28. Reshape

Reshape chỉ zero-copy nếu layout cho phép.

Nếu không:

```text
reshape → copy
```

hoặc yêu cầu contiguous storage.

---

# 209.29. Transpose

Transpose thường chỉ tạo view:

```text
shape'
stride'
```

Không cần copy.

---

# 209.30. Materialization

Khi operation yêu cầu contiguous memory:

```text
materialize()
```

có thể tạo storage mới.

Đây phải là explicit semantic possibility để programmer/tooling biết.

---

# 209.31. Lazy vs eager

Tensor library có thể hỗ trợ cả:

```text
Eager Tensor
Lazy Graph
```

nhưng semantic result phải tương đương trong profile tương ứng.

---

# 209.32. Graph

Graph biểu diễn:

```text
Input
 ↓
Conv
 ↓
Relu
 ↓
MatMul
 ↓
Output
```

Graph là library/compiler abstraction.

---

# 209.33. Graph optimization

Compiler/framework có thể:

```text
constant folding
operator fusion
dead node elimination
layout propagation
memory reuse
kernel selection
```

---

# 209.34. Kernel fusion

Ví dụ:

```text
A * B
 ↓
Add(C)
 ↓
Relu
```

có thể trở thành một kernel.

Điều này đặc biệt quan trọng cho GPU.

---

# 209.35. Fusion không thay đổi semantics

Fusion chỉ được thực hiện nếu:

```text
observable behavior
floating-point profile
aliasing
effects
exceptions/errors
```

được bảo toàn.

---

# 209.36. Floating-point semantics

AI workloads thường cần fast math.

Axiom giữ nguyên nguyên tắc:

```text
Strict FP
```

là mặc định.

Có thể explicit:

```text
@fast_math
```

hoặc profile tương đương.

---

# 209.37. Fast-math

Fast-math có thể cho phép:

```text
reassociation
approximate reciprocal
approximate exp
FMA transformations
reduced NaN guarantees
```

nhưng đây là semantic profile rõ ràng.

---

# 209.38. Deterministic AI

Cần phân biệt:

```text
Semantic determinism
Numerical determinism
Hardware determinism
Distributed determinism
```

GPU parallel reduction có thể không bitwise deterministic.

Không được tuyên bố deterministic tuyệt đối chỉ vì cùng input.

---

# 209.39. Reduction

Ví dụ:

```text
sum(x)
```

có thể có nhiều execution order.

Strict mode:

```text
preserve defined order
```

Relaxed parallel mode:

```text
allow reassociation
```

---

# 209.40. Automatic Differentiation

Axiom hỗ trợ:

```text
AD
```

ở library/compiler layer.

Không cần syntax riêng bắt buộc.

---

# 209.41. Forward-mode AD

Concept:

```text
dual(x, dx)
```

Compiler/library có thể transform:

```text
f(x)
```

thành:

```text
(f(x), df/dx)
```

---

# 209.42. Reverse-mode AD

Graph:

```text
forward graph
      ↓
tape / graph
      ↓
backward graph
```

phù hợp neural-network training.

---

# 209.43. AD transformation

Compiler có thể tạo:

```text
Primal
Tangent
Adjoint
```

thay vì programmer tự viết backward.

---

# 209.44. AD phải hiểu ownership

Generated backward graph phải tuân theo:

```text
Ownership
Drop
Capability
Async
GPU
```

không tạo alias nguy hiểm.

---

# 209.45. Mutation trong AD

Mutable operations có thể làm reverse-mode khó.

Compiler cần phân biệt:

```text
Pure
Read-only
In-place
Stateful
```

---

# 209.46. Mutation legality

Nếu compiler không thể bảo toàn gradient semantics:

```text
reject
```

thay vì âm thầm tạo gradient sai.

---

# 209.47. Custom gradient

Library có thể khai báo:

```text
@custom_gradient
```

với forward/backward implementation.

Compiler vẫn kiểm tra type/ownership/ABI.

---

# 209.48. Gradient metadata

Một operation có thể cung cấp:

```text
Differentiable
NonDifferentiable
CustomDerivative
StopGradient
```

---

# 209.49. Stop gradient

Explicit:

```text
stop_gradient(x)
```

để ngắt AD graph.

---

# 209.50. Higher-order differentiation

Kiến trúc AD không được hard-code chỉ một derivative level.

Có thể:

```text
grad(grad(f))
jacobian(f)
hessian(f)
jvp(f)
vjp(f)
```

ở library/compiler layer.

---

# 209.51. Sparse tensors

Hỗ trợ:

```text
COO
CSR
CSC
BSR
Compressed
BlockSparse
```

nhưng representation là library-level.

---

# 209.52. Sparse semantics

Sparse tensor phải giữ:

```text
logical shape
storage format
indices
values
```

khác dense tensor.

---

# 209.53. Sparse zero semantics

`missing element = zero` là semantic contract của sparse representation nếu format yêu cầu.

---

# 209.54. Memory planning

Graph compiler có thể phân tích:

```text
Tensor lifetime
```

và reuse storage:

```text
A ──────┐
        └─ storage 1
B ──────┘

C ──────┐
        └─ storage 1
```

nếu lifetime không overlap.

---

# 209.55. Memory reuse

Compiler có thể biến:

```text
allocate A
free A
allocate B
```

thành cùng physical buffer.

Ownership semantics không thay đổi.

---

# 209.56. In-place operation

Ví dụ:

```text
relu_inplace(x)
```

chỉ hợp lệ khi capability analysis chứng minh không có conflicting views.

---

# 209.57. Gradient memory planning

Training graph cần phân biệt:

```text
Forward lifetime
Backward lifetime
Saved activation
Gradient
Parameter
Optimizer state
```

Compiler có thể tối ưu storage.

---

# 209.58. Activation checkpointing

Có thể trade:

```text
compute ↔ memory
```

bằng recomputation.

Đây là optimization, không semantic language feature.

---

# 209.59. Kernel abstraction

Kernel:

```axiom
@kernel
fn add(...)
```

đã được xác định trong GPU architecture.

AI kernel chỉ là một loại GPU/CPU computation.

---

# 209.60. CPU kernel

Không ép mọi tensor operation lên GPU.

Backend có thể chọn:

```text
Scalar CPU
SIMD CPU
GPU
NPU
DSP
Accelerator
```

---

# 209.61. Kernel selection

Selection dựa trên:

```text
shape
dtype
layout
target
CPU features
GPU features
memory locality
cost model
```

---

# 209.62. Kernel specialization

Ví dụ:

```text
matmul<f32, 128x128>
```

có thể được specialize.

Dynamic shape vẫn có fallback.

---

# 209.63. Comptime shape specialization

Nếu shape known:

```text
comptime
```

có thể generate optimized kernel.

Generated code phải quay lại compiler verifier.

---

# 209.64. Tensor layout specialization

Compiler có thể specialize:

```text
NCHW
NHWC
blocked
packed
```

để tối ưu cache/vectorization.

---

# 209.65. CPU vectorization

Tensor compiler có thể lower:

```text
TensorOp
 ↓
LoopNest
 ↓
SIMD
```

sử dụng SIMD infrastructure đã frozen.

---

# 209.66. GPU lowering

```text
TensorOp
 ↓
KernelIR
 ↓
GPU MIR
 ↓
SPIR-V/DXIL/MSL/WGSL/native
```

tận dụng GPU architecture 199.

---

# 209.67. Accelerator backend

Không hard-code CUDA.

Backend abstraction:

```text
CPU
CUDA
ROCm
Metal
DirectML
Vulkan
WebGPU
NPU
Custom accelerator
```

---

# 209.68. CUDA

CUDA có thể là backend/platform integration.

Không trở thành Axiom language primitive.

---

# 209.69. ROCm

Tương tự:

```text
ROCm/HIP
```

là backend ecosystem.

---

# 209.70. Unified accelerator interface

High-level Tensor API có thể:

```text
Tensor.to(device)
```

nhưng underlying execution domain vẫn explicit.

---

# 209.71. Device ownership

Device:

```text
Device
```

là resource.

Tensor giữ dependency tới Device/storage khi cần.

---

# 209.72. Device synchronization

GPU event:

```text
GpuEvent
```

đã có từ 199.

Tensor async operation có thể:

```text
Future<Tensor>
```

hoặc một operation handle tùy API.

---

# 209.73. Async tensor operations

Không được hiểu:

```text
tensor.matmul()
```

luôn synchronous.

API phải phân biệt:

```text
sync
async
queued
```

---

# 209.74. Stream

GPU stream/queue là execution resource:

```text
ComputeStream
```

và có ordering semantics.

---

# 209.75. Tensor transfer

Ví dụ:

```text
copy_async(device_tensor, host_buffer)
```

phải giữ source/destination sống tới completion.

Axiom ownership system đã đủ để compiler kiểm tra.

---

# 209.76. Distributed tensors

Distributed tensor có:

```text
global shape
local shard
placement
process/device topology
```

---

# 209.77. Sharding

Các kiểu:

```text
DataParallel
TensorParallel
PipelineParallel
SequenceParallel
```

là library/framework abstractions.

---

# 209.78. Collective communication

Primitive:

```text
AllReduce
AllGather
ReduceScatter
Broadcast
AllToAll
```

dựa trên networking architecture.

---

# 209.79. Distributed synchronization

Không coi distributed communication là ordinary memory synchronization.

Phải phân biệt:

```text
Thread happens-before
GPU synchronization
Network ordering
Distributed consistency
```

---

# 209.80. Distributed training

Training framework có thể xây trên:

```text
Tensor
GPU
Async
Network
Collective
Ownership
```

không cần language-level distributed object.

---

# 209.81. Model representation

Model có thể là:

```text
Module
Parameter
Buffer
Graph
```

nhưng `Module` không phải Core class.

Struct + traits là đủ.

---

# 209.82. Parameter

Parameter là tensor có gradient/state semantics.

Ví dụ:

```text
Parameter<f32>
```

library type.

---

# 209.83. Optimizer

Optimizer:

```text
SGD
Adam
AdamW
LAMB
```

là ordinary Axiom library code.

---

# 209.84. Training loop

Không cần compiler magic:

```axiom
for batch in dataset {
    loss = model.forward(batch)
    loss.backward()
    optimizer.step()
}
```

Compiler/framework có thể optimize graph phía dưới.

---

# 209.85. Inference

Inference không cần kéo training runtime.

Build system có thể chỉ link:

```text
Tensor
Inference
CPU/GPU backend
```

---

# 209.86. Quantized inference

Compiler có thể specialize:

```text
INT8
INT4
FP8
```

và chọn hardware instructions.

---

# 209.87. Mixed precision

Một graph có thể:

```text
weights = bf16
accumulator = f32
```

type system/operation metadata phải biểu diễn được.

---

# 209.88. Automatic mixed precision

Có thể là optimization policy:

```text
AMP
```

nhưng phải có numerical contract.

Không tự động đổi precision trong strict numerical mode.

---

# 209.89. Tensor error semantics

Shape mismatch:

```text
ShapeMismatch
```

là Result/error.

Không phải memory safety violation.

---

# 209.90. Invalid device operation

Ví dụ device lost:

```text
DeviceLost
```

là explicit error.

---

# 209.91. Out-of-memory

OOM policy phụ thuộc runtime/profile:

```text
Result
panic
abort
device error
```

Không hard-code một policy duy nhất.

---

# 209.92. Tensor serialization

Tensor persistence phải dùng architecture 207:

```text
Semantic Tensor
      ↓
Wire/Persistent Representation
```

Không serialize raw pointer/device handle.

---

# 209.93. Model checkpoint

Checkpoint cần fingerprint:

```text
ModelSchemaFingerprint
TensorLayoutFingerprint
DType
Version
```

để phát hiện incompatibility.

---

# 209.94. Compiler introspection

CompilerDB có thể trả:

```text
tensor shape
layout
dtype
device
kernel
fusion
memory allocation
transfer
vectorization
```

---

# 209.95. AI-native diagnostics

Ví dụ:

```text
ax explain tensor
ax explain kernel
ax explain fusion
ax explain allocation
ax explain transfer
ax explain gradient
```

AI agent có thể query semantic facts thay vì đọc toàn bộ framework source.

---

# 209.96. Kernel explanation

Compiler có thể nói:

```text
MatMul
→ GPU kernel
→ tiled 128x128
→ shared memory
→ FP16 input
→ FP32 accumulator
→ fused bias
```

theo machine-readable representation.

---

# 209.97. Allocation explanation

Ví dụ:

```text
Tensor A
allocation #17
storage = GPU
lifetime = node 4..8
reused by Tensor C
```

Điều này cực kỳ hữu ích cho AI compiler tooling.

---

# 209.98. Graph compilation cache

Compiled tensor kernels có fingerprint:

```text
source
shape
dtype
layout
target
device
features
compiler version
optimization profile
```

để cache.

---

# 209.99. No mandatory AI runtime

Một chương trình Axiom không dùng Tensor:

```text
```

không được link:

```text
Tensor runtime
CUDA runtime
AD runtime
AI allocator
```

---

# 209.100. No mandatory Python dependency

Axiom AI stack phải có khả năng chạy native:

```text
Axiom
  ↓
native executable
  ↓
CPU/GPU
```

Python có thể là interoperability/tooling layer, không phải prerequisite.

---

# 209.101. Python interoperability

Có thể generate:

```text
Python bindings
```

từ Axiom metadata.

Nhưng Axiom semantics không phụ thuộc Python.

---

# 209.102. Framework interoperability

Có thể FFI:

```text
PyTorch
ONNX
TensorFlow
CUDA
ROCm
```

nhưng wrapper phải qua FFI contract.

---

# 209.103. ONNX

ONNX có thể là interchange representation:

```text
Axiom Tensor Graph
      ↕
     ONNX
```

không phải compiler IR duy nhất.

---

# 209.104. Graph import

Imported graph phải được validate:

```text
types
shapes
layouts
operations
device constraints
```

trước khi executable.

---

# 209.105. Graph export

Axiom model có thể export metadata/graph nhưng không cần expose compiler internals.

---

# 209.106. AI compiler boundary

Kiến trúc cuối:

```text
Axiom Source
     │
     ▼
Typed HIR
     │
     ▼
MIR
     │
     ├───────────────┐
     ▼               ▼
Normal Code       Tensor Ops
                     │
                     ▼
                 Tensor IR
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
         CPU         GPU      Accelerator
          │          │          │
         SIMD      Kernel       Backend
```

---

# 209.107. Automatic differentiation boundary

AD không tạo một compiler khác:

```text
Axiom
  ↓
Typed program
  ↓
AD transformation
  ↓
ordinary Axiom IR
  ↓
normal verification
  ↓
normal optimization
```

Đây là điểm rất quan trọng.

---

# 209.108. AI code generation

AI-generated tensor/kernel code:

```text
AI
 ↓
Axiom source
 ↓
CompilerDB
 ↓
Type checking
 ↓
Ownership
 ↓
GPU legality
 ↓
Tensor verification
 ↓
Codegen
```

AI **không được cấp quyền bypass compiler**.

---

# 209.109. Tensor safety

Compiler phải ngăn:

```text
out-of-bounds
invalid stride
invalid shape assumptions
use-after-device-free
device/host misuse
overlapping mutable tensor views
```

trong safe code.

---

# 209.110. Unsafe tensor kernels

Low-level kernels có thể dùng:

```text
unsafe
```

nhưng khi tạo safe Tensor API phải thiết lập:

```text
bounds
alignment
shape
stride
storage
synchronization
```

và verifier tiếp tục hoạt động sau boundary.

---

# 209.111. AI-specific effect system

Tensor operation có thể có effects:

```text
ReadTensor
WriteTensor
Allocate
DeviceTransfer
KernelLaunch
Synchronize
Random
```

để compiler biết operation nào có thể reorder/fuse.

---

# 209.112. Randomness in ML

Phân biệt:

```text
SecureRandom
MLRandom
DeterministicRandom
```

ML random không được dùng làm cryptographic random.

---

# 209.113. Reproducible training

Build/runtime metadata có thể ghi:

```text
seed
algorithm
device
kernel version
dtype
numerical profile
```

nhưng không hứa bitwise determinism nếu backend không cung cấp.

---

# 209.114. Compiler autotuning

Compiler/framework có thể benchmark:

```text
tile size
vector width
kernel variant
memory strategy
```

và lưu result vào tuning cache.

---

# 209.115. Autotuning không thay đổi semantics

Tuning chỉ được chọn giữa những implementation đã verified.

---

# 209.116. Profile-guided tensor optimization

PGO có thể giúp:

```text
kernel selection
fusion
layout
memory placement
```

nhưng không thay đổi language semantics.

---

# 209.117. Kernel cache

Kernel cache identity phải bao gồm:

```text
Target
Device
Driver/backend version
Compiler semantic version
Shape
DType
Layout
Kernel source fingerprint
Optimization profile
```

---

# 209.118. Memory allocator

Tensor allocator có thể dùng:

```text
arena
pool
buddy
caching allocator
device allocator
```

nhưng đây là library/runtime policy.

---

# 209.119. Memory planner

Graph executor có thể quản lý:

```text
logical tensor lifetime
physical buffer lifetime
```

Hai thứ này không được nhầm lẫn.

---

# 209.120. Tensor identity

Phân biệt:

```text
Tensor value
Tensor storage
Tensor logical identity
```

giống memory/storage model:

```text
Memory Address
    ≠
Tensor Storage
    ≠
Tensor Identity
```

---

# 209.121. AI graph identity

Node ID là logical identity:

```text
NodeId
TensorId
ParameterId
```

không dựa vào memory address.

---

# 209.122. In-place alias analysis

Compiler dùng capability regions:

```text
A: WRITE region [0..100]
B: READ region [100..200]
```

có thể chạy song song nếu proof disjoint.

---

# 209.123. Parallel tensor operations

Compiler có thể parallelize:

```text
for i ...
```

nếu ownership/effect/alias analysis chứng minh an toàn.

---

# 209.124. GPU race verification

GPU kernels dùng cùng semantic model:

```text
READ
WRITE
Atomic
Barrier
```

đã định nghĩa trong 199.

---

# 209.125. Tensor + async

Tensor operation pending giữ ownership/capability cần thiết cho tới completion.

Không cho:

```text
free buffer
    ↓
pending GPU operation
```

trong safe code.

---

# 209.126. Tensor + networking

Distributed Tensor có thể truyền:

```text
NetworkBuffer
```

zero-copy nếu storage contract cho phép.

---

# 209.127. Tensor + serialization

Checkpoint/network protocol không được assume memory layout là wire layout.

---

# 209.128. Tensor + filesystem

Memory-mapped tensor có thể:

```text
MappedTensor
```

nhưng persistent representation vẫn phải có format contract.

---

# 209.129. Tensor + GPU storage

Persistent GPU memory không mặc định được serialize bằng device pointer.

---

# 209.130. Tensor + FFI

Foreign tensor handle:

```text
ForeignTensor
```

phải khai báo:

```text
ownership
device
layout
dtype
lifetime
synchronization
```

---

# 209.131. Tensor + ABI

Không đưa Tensor ABI nội bộ vào stable Axiom ABI mặc định.

Stable APIs nên dùng explicit opaque/descriptor contracts.

---

# 209.132. Model plugins

AI model/plugin có thể dùng:

```text
@abi(stable)
```

với opaque model handle.

Không yêu cầu public Tensor representation ổn định.

---

# 209.133. AI model loading

Model loader phải phân biệt:

```text
trusted model
untrusted model
```

Model file không được mặc định được thực thi như code.

---

# 209.134. Serialization security

Model/checkpoint parser phải chịu:

```text
bounds checks
resource limits
schema validation
```

theo serialization architecture 207.

---

# 209.135. No hidden execution

Loading tensor/model data không được implicit execute arbitrary code.

---

# 209.136. Compiler-level tensor invariants

### `ATENSOR-20`
Tensor shall remain a library/compiler abstraction above Core.

### `ATENSOR-21`
Tensor ownership shall follow Axiom ownership semantics.

### `ATENSOR-22`
Large tensors shall not implicitly become Copy values.

### `ATENSOR-23`
Tensor views shall obey capability provenance and lifetime rules.

### `ATENSOR-24`
Mutable tensor views shall obey exclusive mutation semantics.

### `ATENSOR-25`
Shape, stride and layout shall remain distinguishable semantic metadata.

### `ATENSOR-26`
Static shape information may be used for compile-time verification.

### `ATENSOR-27`
Dynamic shapes shall remain supported.

### `ATENSOR-28`
Unknown runtime shape information shall not be treated as compile-time proof.

### `ATENSOR-29`
Broadcasting shall have deterministic semantics.

### `ATENSOR-30`
Reshape shall avoid copying when representation permits.

### `ATENSOR-31`
Transpose shall support zero-copy views where legal.

### `ATENSOR-32`
Implicit tensor materialization shall not occur merely because an operation can be expressed as a view.

### `ATENSOR-33`
DType shall remain distinct from storage allocation.

### `ATENSOR-34`
Quantization metadata shall remain explicit.

### `ATENSOR-35`
Host/device storage domains shall remain distinct.

### `ATENSOR-36`
Host/device transfers shall not occur implicitly when they create observable cost or synchronization.

### `ATENSOR-37`
Zero-copy optimization shall require valid ownership, capability and representation proof.

### `ATENSOR-38`
Tensor kernels shall obey GPU legality rules.

### `ATENSOR-39`
Tensor kernels shall obey CPU/GPU memory safety rules.

### `ATENSOR-40`
Tensor fusion shall preserve observable semantics.

### `ATENSOR-41`
Tensor optimization shall preserve floating-point profile semantics.

### `ATENSOR-42`
Strict floating-point mode shall not permit arbitrary reassociation.

### `ATENSOR-43`
Relaxed numerical profiles shall be explicit.

### `ATENSOR-44`
Automatic differentiation shall lower to ordinary verified compiler representations.

### `ATENSOR-45`
Generated derivative code shall pass ownership and capability verification.

### `ATENSOR-46`
Mutation shall not silently invalidate automatic differentiation semantics.

### `ATENSOR-47`
Custom derivatives shall declare their semantic contract.

### `ATENSOR-48`
Stop-gradient shall be explicit.

### `ATENSOR-49`
Higher-order differentiation shall be representable without redesigning Core.

### `ATENSOR-50`
Sparse tensor formats shall remain library-level representations.

### `ATENSOR-51`
Tensor memory planning may reuse physical storage only when logical lifetimes do not overlap incompatibly.

### `ATENSOR-52`
In-place tensor operations shall require valid exclusive capability.

### `ATENSOR-53`
Tensor execution shall support CPU, SIMD, GPU and accelerator backends.

### `ATENSOR-54`
Backend selection shall not change semantic results outside the active numerical profile.

### `ATENSOR-55`
GPU/accelerator execution shall have explicit completion semantics.

### `ATENSOR-56`
Pending device operations shall retain required storage/capabilities.

### `ATENSOR-57`
Distributed tensor operations shall distinguish network ordering from local memory synchronization.

### `ATENSOR-58`
Collective communication shall remain a library/distributed-system abstraction.

### `ATENSOR-59`
Tensor serialization shall use explicit wire/persistent representation contracts.

### `ATENSOR-60`
Raw device pointers shall never become persistent tensor identity.

### `ATENSOR-61`
Tensor graph node identity shall be logical rather than address-based.

### `ATENSOR-62`
Tensor operations shall expose relevant compiler effects.

### `ATENSOR-63`
Tensor compiler optimizations shall declare and preserve their legality conditions.

### `ATENSOR-64`
Autotuning shall only select verified implementations.

### `ATENSOR-65`
Kernel caches shall include all semantics-relevant target and compiler inputs.

### `ATENSOR-66`
AI runtime components shall be optional and tree-shakeable.

### `ATENSOR-67`
Axiom programs not using AI/Tensor functionality shall not require an AI runtime.

### `ATENSOR-68`
Axiom AI functionality shall not require Python.

### `ATENSOR-69`
Foreign tensor integrations shall use explicit FFI contracts.

### `ATENSOR-70`
Untrusted model files shall not implicitly execute arbitrary code.

### `ATENSOR-71`
AI-generated code shall pass the same compiler verification as human-written code.

### `ATENSOR-72`
CompilerDB shall expose tensor, kernel, shape, layout and optimization facts.

### `ATENSOR-73`
Tensor diagnostics shall be available in both human-readable and machine-readable forms.

### `ATENSOR-74`
Tensor compilation shall preserve source-to-kernel provenance.

### `ATENSOR-75`
Tensor backend failures shall not silently weaken safety guarantees.

### `ATENSOR-76`
AI numerical nondeterminism shall be explicitly distinguishable from language nondeterminism.

### `ATENSOR-77`
Distributed training shall not introduce implicit ownership or synchronization semantics into Core.

### `ATENSOR-78`
Tensor abstractions shall remain compatible with freestanding/native Axiom programs.

### `ATENSOR-79`
Tensor functionality shall not require garbage collection.

### `ATENSOR-80`
Tensor functionality shall not require a monolithic runtime.

---

# Kiến trúc AI cuối cùng của Axiom

Sau 209, bức tranh đã khá rõ:

```text
                    AXIOM
                      │
       ┌──────────────┼───────────────┐
       │              │               │
     CPU            GPU          Accelerator
       │              │               │
     SIMD          Kernel           Backend
       │              │               │
       └──────────────┼───────────────┘
                      │
                  Tensor IR
                      │
             ┌────────┴────────┐
             │                 │
          Tensor             AD Graph
             │                 │
             └────────┬────────┘
                      │
                 AI Library
                      │
        ┌─────────────┼─────────────┐
        │             │             │
      Train        Inference     Distributed
```

Điểm quan trọng là **Axiom không trở thành "ngôn ngữ AI"**.

Nó trở thành một **systems language có đủ semantic infrastructure để AI framework được xây dựng trực tiếp trên nó**.

---

# Một quyết định kiến trúc rất đáng chú ý

Đến đây Axiom đã có một nguyên tắc xuyên suốt:

```text
Language Core
      ↓
Semantic IR
      ↓
Domain-specific IR
      ↓
Backend
```

Ví dụ:

```text
Ordinary code
    → MIR
    → OptIR
    → Machine IR

Tensor code
    → MIR
    → TensorIR
    → KernelIR
    → GPU/CPU backend

Shader
    → MIR
    → GPU MIR
    → Shader backend

Async
    → MIR
    → Coroutine state machine

AD
    → MIR
    → generated derivative MIR
```

**Không tạo một compiler riêng cho từng domain.**

Đây là một trong những điểm có thể giúp Axiom vừa mạnh vừa giữ compiler architecture thống nhất.

---

## BOOTSTRAP-210 — Scientific Computing, Numerical Methods, Complex Numbers & High-Performance Math

**TRẠNG THÁI: NEXT**

Phần tiếp theo nên xử lý sâu hơn tầng toán học bên trên Tensor:

```text
Complex
Quaternion
Interval Arithmetic
Big Integer
Big Float
Rational
Polynomial
FFT
BLAS
LAPACK
Sparse Linear Algebra
ODE/PDE
Optimization
Statistics
Probability
Numerical Stability
Automatic Precision
Scientific Simulation
```

và quan trọng nhất:

> **Làm thế nào để Axiom có một numeric/scientific stack đủ mạnh cho AI, simulation, physics, engineering và HPC mà không biến mọi kiểu số thành Core primitive hoặc làm mất hiệu năng native.**