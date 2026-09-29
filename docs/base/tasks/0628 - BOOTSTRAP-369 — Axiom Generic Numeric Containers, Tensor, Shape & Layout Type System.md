# BOOTSTRAP-369 — Axiom Generic Numeric Containers, Tensor, Shape & Layout Type System

Sau **368 — Numeric/Mathematical Semantics**, bước tiếp theo nên giải quyết lớp mà AI/scientific computing thực sự cần: **Tensor + Shape + Layout + Device + DType**.

Điểm quan trọng: đây **không phải đưa Tensor vào Core**. Ta xây một semantic foundation đủ mạnh để standard library hoặc AI library có thể triển khai Tensor mà compiler vẫn tối ưu được gần như native code.

---

## 1. Mục tiêu

Một tensor Axiom về mặt semantic cần mô tả:

```text
Tensor
 ├── Element type
 ├── Shape
 ├── Strides / Layout
 ├── Storage
 ├── Device
 ├── Ownership
 └── Mutability
```

Ví dụ:

```text
Tensor<f32, [2, 3, 224, 224], GPU>
```

compiler có thể biết:

```text
dtype      = f32
rank       = 4
shape      = [2, 3, 224, 224]
device     = GPU
```

nhưng không nhất thiết phải biết toàn bộ layout nếu layout không phải semantic requirement.

---

# 2. Tensor không phải Array

Axiom đã có:

```text
T[N]
```

cho fixed-size array.

Không được đồng nhất:

```text
Array<T, N>
```

với:

```text
Tensor<T, Shape>
```

Array:

```text
T[N]
```

có semantics:

- contiguous logical sequence
- fixed compile-time size
- value semantics
- inline representation mặc định

Tensor:

```text
Tensor<T, Shape, Layout, Storage>
```

có thể:

- dynamic shape
- non-contiguous
- strided
- device-backed
- shared
- externally allocated

---

# 3. Tensor abstraction

Một conceptual definition:

```text
struct Tensor<
    T,
    Shape,
    Layout,
    Storage
> {
    storage: Storage
    shape: Shape
    layout: Layout
}
```

Nhưng đây chỉ là **semantic model**.

Compiler có thể flatten representation thành:

```text
pointer
lengths
strides
```

hoặc thậm chí specialize toàn bộ thành machine-level structure.

Không có object header bắt buộc.

---

# 4. DType

`T` phải đại diện cho element type.

Ví dụ:

```text
Tensor<f32>
Tensor<f64>
Tensor<i8>
Tensor<bf16>
Tensor<Complex<f32>>
```

Có thể có metadata trait:

```text
trait DType
```

với compile-time properties:

```text
size
alignment
numeric category
precision
machine representation
```

---

# 5. Quantized tensor

Không nên biến:

```text
Tensor<i8>
```

thành quantized tensor tự động.

Có thể:

```text
QuantizedTensor<i8, Scale, ZeroPoint>
```

hoặc:

```text
Tensor<quant<i8, Scale, ZeroPoint>>
```

để phân biệt:

```text
raw i8
```

với:

```text
i8 representing quantized numerical values
```

---

# 6. Shape

Shape là compile-time structure khi có thể.

Ví dụ:

```text
type Image = Tensor<f32, [224, 224, 3]>
```

Compiler biết:

```text
rank = 3
dim[0] = 224
dim[1] = 224
dim[2] = 3
```

---

# 7. Symbolic dimensions

Không phải shape nào cũng constant.

Có thể:

```text
Tensor<f32, [B, 3, H, W]>
```

với:

```text
B
H
W
```

là symbolic dimensions.

Compiler lưu:

```text
ShapeVariable
ShapeConstraint
```

Ví dụ:

```text
H % 16 == 0
W % 16 == 0
```

---

# 8. Shape constraint solver

Thêm compiler subsystem:

```text
ShapeConstraintDB
```

có thể giải:

```text
A = [B, M, N]
B = [B, N, K]
```

suy ra:

```text
MatMul(A, B) = [B, M, K]
```

Nếu:

```text
N != N2
```

compiler báo lỗi ngay khi chứng minh được mismatch.

---

# 9. Runtime shape

Dynamic tensor:

```text
Tensor<f32, [dynamic, 224, 224, 3]>
```

có runtime dimension.

Compiler tạo metadata:

```text
shape pointer / inline dimensions
```

tùy rank.

Không cần:

```text
reflection object
```

hay dynamic type system.

---

# 10. Rank

Rank phải là semantic property.

```text
Tensor<f32, []>
```

rank 0.

```text
Tensor<f32, [N]>
```

rank 1.

```text
Tensor<f32, [M, N]>
```

rank 2.

Compiler có thể specialize operations theo rank.

---

# 11. Broadcasting

Broadcasting không nên là magic runtime behavior.

Ví dụ:

```text
A: [B, M, N]
B: [N]
```

có thể broadcast thành:

```text
[B, M, N]
```

nếu broadcasting rule cho phép.

Compiler tạo:

```text
BroadcastProof
```

để chứng minh operation hợp lệ.

---

# 12. Broadcasting không tạo copy

Đây là điểm quan trọng.

```text
A + b
```

với:

```text
A = [1024, 1024]
b = [1024]
```

không nên materialize:

```text
[1024, 1024]
```

cho `b`.

Compiler tạo logical broadcast view:

```text
BroadcastView
```

và kernel đọc:

```text
b[j]
```

thay vì:

```text
b[i][j]
```

---

# 13. Stride model

Tensor không nhất thiết contiguous.

Ví dụ matrix:

```text
shape = [M, N]
stride = [N, 1]
```

row-major.

Column-major:

```text
stride = [1, M]
```

Slice:

```text
A[:, 0]
```

có thể:

```text
shape = [M]
stride = [N]
```

mà không copy dữ liệu.

---

# 14. Tensor View

Nên có semantic:

```text
TensorView<T, Shape, Layout>
TensorMutView<T, Shape, Layout>
```

tương tự:

```text
view<T>
mut_view<T>
```

nhưng chứa metadata shape/stride.

Ví dụ:

```text
let x = tensor.view();
let y = x.slice(...);
```

`y` không sở hữu storage.

---

# 15. Tensor view không được outlive owner

Giống capability system:

```text
Tensor
  ↓
TensorView
```

Compiler tracking:

```text
owner provenance
storage lifetime
shape
layout
access mode
```

Nếu:

```text
let v = tensor.view();
drop(tensor);
use(v);
```

→ reject.

---

# 16. Mutable tensor view

`TensorMutView` là exclusive write capability.

Không cho:

```text
let a = tensor.mut_view();
let b = tensor.mut_view();
```

nếu compiler không chứng minh:

```text
a region ∩ b region = ∅
```

Nhưng:

```text
a = tensor[:, 0]
b = tensor[:, 1]
```

có thể được phép nếu stride/region analysis chứng minh disjoint.

---

# 17. Layout

Layout là một abstraction độc lập với shape.

Có thể:

```text
Contiguous
Strided
RowMajor
ColumnMajor
Blocked
Tiled
Packed
Broadcast
Transposed
```

Không nên biến tất cả thành Core keywords.

---

# 18. Layout algebra

Compiler cần hiểu các transformation:

```text
reshape
transpose
permute
slice
broadcast
expand
squeeze
unsqueeze
flatten
```

Một số chỉ thay đổi metadata.

Ví dụ:

```text
transpose(A)
```

có thể chỉ đổi:

```text
shape
stride
```

không copy.

---

# 19. Reshape

`reshape` chỉ được zero-copy nếu layout cho phép.

Nếu không:

```text
reshape(A)
```

có thể:

```text
ERROR
```

hoặc library API:

```text
reshape_copy(A)
```

Không được implicit copy nếu chi phí observable.

---

# 20. Contiguous

Library có thể:

```text
A.contiguous()
```

Compiler biết:

```text
if already contiguous:
    return view

else:
    allocate + copy
```

Nhưng phải giữ ownership semantics.

---

# 21. Storage domain

Tensor phải tích hợp với task 367:

```text
StorageDomain =
    Host
    Device
    Shared
    External
```

Ví dụ:

```text
Tensor<f32, Shape, GPU>
```

không chỉ là:

```text
Tensor<f32>
```

mà storage provenance được compiler biết.

---

# 22. Device là type-level khi có thể

Có thể:

```text
Tensor<f32, S, Host>
Tensor<f32, S, Device<Gpu>>
```

Điều này cho phép compiler reject:

```text
host_kernel(device_tensor)
```

nếu API yêu cầu host tensor.

---

# 23. Nhưng không bắt buộc device phải static

Runtime device:

```text
DeviceHandle
```

vẫn cần tồn tại.

Ví dụ:

```text
let device = choose_device();
let tensor = Tensor.allocate(device, shape);
```

Khi device không biết compile-time, compiler vẫn đảm bảo:

```text
ownership
storage validity
```

nhưng device dispatch xảy ra runtime.

---

# 24. Tensor transfer

Không implicit:

```text
GPU tensor → CPU tensor
```

Phải có:

```text
to_host()
to_device()
copy_to(device)
```

và những operation này tạo execution dependency.

---

# 25. Zero-copy interop

Nếu external resource có compatible storage:

```text
ExternalBuffer
```

có thể tạo:

```text
TensorView
```

không copy.

Nhưng phải có contract:

```text
external ownership
alignment
size
lifetime
storage domain
mutability
```

Nếu contract không chứng minh được → unsafe hoặc reject.

---

# 26. Tensor indexing

Compiler phải hỗ trợ indexing semantic:

```text
A[i]
A[i, j]
A[i, j, k]
```

nhưng không nhất thiết mỗi indexing tạo function call.

Compiler lowering:

```text
offset =
    i0 * stride0 +
    i1 * stride1 +
    ...
```

sau đó bounds check.

Nếu compiler chứng minh bounds:

```text
check eliminated
```

---

# 27. Bounds elimination

Ví dụ:

```text
for i in 0..N {
    out[i] = input[i];
}
```

nếu:

```text
len(out) >= N
len(input) >= N
```

compiler có thể biến thành raw machine indexing.

Đây là một trong các cơ chế giúp Tensor abstraction vẫn đạt performance native.

---

# 28. Tensor iteration

Không nên tạo iterator object bắt buộc.

```text
for x in tensor {
    ...
}
```

có thể lower thành:

```text
pointer + stride
```

hoặc:

```text
vectorized loop
```

hoặc:

```text
GPU kernel
```

tùy backend.

---

# 29. Tensor operation fusion

Ví dụ:

```text
y = relu(a * b + c)
```

Naive:

```text
t1 = a * b
t2 = t1 + c
y  = relu(t2)
```

Fusion compiler có thể tạo:

```text
y[i] = max(a[i] * b[i] + c[i], 0)
```

trong một kernel.

Task 367 cung cấp GPU kernel fusion foundation; task 369 bổ sung:

```text
TensorGraph
TensorOp
TensorFusion
```

---

# 30. Tensor expression graph

Compiler/library có thể biểu diễn:

```text
A
├── Mul
│    ├── B
│    └── C
└── Add
```

nhưng không bắt buộc runtime graph.

Có hai mode:

### Eager

```text
A * B
```

thực thi ngay.

### Compile-time/static graph

Compiler thấy toàn expression và fuse.

Không cần dynamic graph runtime nếu programmer không yêu cầu.

---

# 31. Materialization

Tensor expression:

```text
A * B + C
```

không nhất thiết có storage.

Compiler có thể giữ:

```text
ExpressionNode
```

đến khi:

```text
materialize()
```

hoặc assignment:

```text
D = A * B + C;
```

lúc đó tạo output storage.

---

# 32. Temporary elimination

Ví dụ:

```text
let x = A * B;
let y = x + C;
```

Nếu `x` không observable ngoài expression:

```text
x
```

có thể bị eliminate.

Compiler dùng:

```text
EscapeAnalysis
OwnershipAnalysis
TensorGraphAnalysis
```

để quyết định.

---

# 33. In-place operation

Tensor API cần phân biệt:

```text
C = A + B
```

và:

```text
A += B
```

In-place operation yêu cầu exclusive write capability.

Compiler có thể optimize:

```text
C = A + B
```

thành in-place nếu chứng minh:

```text
C aliases A
```

được phép bởi semantics.

Không được tự ý alias output chỉ vì tiết kiệm allocation.

---

# 34. Aliasing contract

Ví dụ:

```text
fn add(
    a: TensorView<f32>,
    b: TensorView<f32>,
    out: TensorMutView<f32>
)
```

Compiler cần chứng minh:

```text
out ∩ a = ∅
out ∩ b = ∅
```

nếu kernel yêu cầu no-overlap.

Nếu không chứng minh được:

```text
compile error
```

hoặc API phải sử dụng abstraction hỗ trợ overlap.

---

# 35. Reduction

Tensor:

```text
sum(A, axis=1)
```

shape:

```text
[B, M, N]
```

→

```text
[B, M]
```

Compiler phải track shape transformation.

Có:

```text
ReductionShapeProof
```

và:

```text
ReductionNumericalProof
```

---

# 36. Matrix multiplication

Một API:

```text
matmul(A, B)
```

có thể được compiler specialize theo:

```text
dtype
shape
layout
device
target features
```

Ví dụ:

```text
f32 × f32
```

có thể lower:

```text
CPU SIMD
AVX2
AVX512
GPU tensor core
```

mà source API không thay đổi.

---

# 37. Tensor Core / accelerator

Không hard-code:

```text
CUDA Tensor Core
```

vào language.

Semantic operation:

```text
matrix_multiply_accumulate
```

backend có thể map thành:

```text
FMA
SIMD
Tensor Core
NPU instruction
```

nếu numerical contract cho phép.

---

# 38. Autodiff integration

Tensor library có thể định nghĩa:

```text
requires_grad
```

nhưng compiler không cần hiểu ML framework.

Compiler chỉ cần hỗ trợ:

```text
comptime transformation
generic differentiation types
expression graphs
```

sau này có thể xây:

```text
@differentiate
fn loss(...)
```

ở library/compiler extension layer.

---

# 39. Tensor serialization

Không đưa serialization vào Core.

Tensor metadata cần đủ để library serialize:

```text
dtype
shape
layout
storage
device
```

nhưng file format:

```text
safetensors
onnx
custom
```

là library/toolchain layer.

---

# 40. Tensor compiler database

Bổ sung:

```text
TensorDB
TensorTypeDB
TensorElementTypeDB
TensorShapeDB
TensorDimensionDB
TensorShapeConstraintDB
TensorRankDB
TensorLayoutDB
TensorStrideDB
TensorViewDB
TensorMutViewDB
TensorStorageDB
TensorDeviceDB
TensorIndexDB
TensorBroadcastDB
TensorTransposeDB
TensorReshapeDB
TensorSliceDB
TensorReduceDB
TensorMatmulDB
TensorExpressionDB
TensorGraphDB
TensorFusionDB
TensorMaterializationDB
TensorAliasDB
TensorInplaceDB
TensorKernelDB
TensorSpecializationDB
TensorCostModelDB
TensorProofDB
```

---

# 41. MIR additions

Thêm các semantic operation:

```text
TENSOR_CREATE
TENSOR_VIEW
TENSOR_MUT_VIEW

TENSOR_INDEX
TENSOR_SLICE
TENSOR_RESHAPE
TENSOR_TRANSPOSE
TENSOR_PERMUTE
TENSOR_BROADCAST

TENSOR_LOAD
TENSOR_STORE

TENSOR_REDUCE
TENSOR_MATMUL

TENSOR_TRANSFER
TENSOR_CONTIGUOUS

TENSOR_MATERIALIZE
TENSOR_FUSE
```

Compiler sau đó lower các operation này về:

```text
scalar
SIMD
parallel CPU
GPU
accelerator
```

---

# 42. Tensor proof

Mỗi operation quan trọng có thể có:

```text
TensorShapeProof
TensorBoundsProof
TensorLayoutProof
TensorAliasProof
TensorStorageProof
TensorDeviceProof
TensorNumericalProof
TensorFusionProof
```

Ví dụ:

```text
TensorShapeProof:

A = [B, M, N]
C = [B, N, K]

matmul(A,C)
=> [B,M,K]
```

---

# 43. Invariants

### `ATENSOR-01`
Tensor không phải Core runtime object bắt buộc.

### `ATENSOR-02`
Tensor element type phải được xác định statically khi generic instantiation được resolve.

### `ATENSOR-03`
Shape là semantic metadata và phải được compiler tracking.

### `ATENSOR-04`
Compile-time shape mismatch phải được phát hiện trước runtime.

### `ATENSOR-05`
Dynamic shape phải được kiểm tra runtime khi cần.

### `ATENSOR-06`
Broadcasting không được tạo implicit full-size copy.

### `ATENSOR-07`
View không sở hữu storage.

### `ATENSOR-08`
Tensor view không được outlive storage owner.

### `ATENSOR-09`
Mutable tensor view là exclusive write capability.

### `ATENSOR-10`
Compiler chỉ cho phép overlapping mutable views khi abstraction explicitly cho phép.

### `ATENSOR-11`
Stride/layout phải được bảo toàn khi observable.

### `ATENSOR-12`
Reshape không được giả định zero-copy nếu layout không cho phép.

### `ATENSOR-13`
Tensor indexing phải obey bounds semantics.

### `ATENSOR-14`
Bounds check có thể bị loại bỏ khi compiler có proof.

### `ATENSOR-15`
Tensor transformation không được implicit materialize dữ liệu nếu chi phí/side effect observable.

### `ATENSOR-16`
Host/device storage phải được phân biệt.

### `ATENSOR-17`
Host/device transfer không được implicit trong safe tensor operations.

### `ATENSOR-18`
External tensor memory phải có ownership/lifetime/storage contract.

### `ATENSOR-19`
Tensor device information có thể static hoặc dynamic.

### `ATENSOR-20`
Dynamic device selection không được phá memory safety.

### `ATENSOR-21`
Tensor expression temporaries có thể được eliminated khi semantics tương đương.

### `ATENSOR-22`
Kernel fusion phải giữ shape, alias, synchronization và numerical semantics.

### `ATENSOR-23`
In-place tensor operations yêu cầu write capability hợp lệ.

### `ATENSOR-24`
Compiler không được tự ý biến out-of-place operation thành aliasing operation nếu semantics thay đổi.

### `ATENSOR-25`
Reduction phải giữ numerical contract.

### `ATENSOR-26`
Matmul specialization phải giữ dtype/shape/numerical semantics.

### `ATENSOR-27`
Tensor abstraction phải có thể lower xuống scalar/SIMD/CPU parallel/GPU.

### `ATENSOR-28`
Tensor metadata không được yêu cầu runtime object nếu compiler có thể encode bằng static information.

### `ATENSOR-29`
Tensor compiler transformations phải quay lại ownership/memory/numeric verification.

### `ATENSOR-30`
Tensor subsystem phải mở rộng được sang accelerator và storage domain mới mà không thay đổi Core ownership/memory model.

---

# 44. Kiến trúc sau 369

Axiom hiện bắt đầu có một pipeline rất mạnh cho AI/scientific workloads:

```text
                  Axiom Source
                       │
                 Generic Types
                       │
             Numeric Semantics
                       │
             Tensor / Shape IR
                       │
          ┌────────────┼────────────┐
          │            │            │
       Scalar         SIMD       Parallel
          │            │            │
          └────────────┼────────────┘
                       │
                    GPU/ACC
                       │
               Kernel Fusion
                       │
              Target Specialization
                       │
                Native Machine Code
```

Điểm đáng chú ý là **Tensor không trở thành một “framework riêng” nằm ngoài compiler**. Nó vẫn tuân thủ toàn bộ nền tảng Axiom đã xây:

```text
Ownership
Capability
Lifetime
Memory Safety
Numeric Semantics
Parallelism
SIMD
GPU
Comptime
Optimization
```

Do đó về sau một câu rất cao cấp như:

```text
C = relu(A @ B + bias)
```

vẫn có thể cuối cùng trở thành một kernel machine-level gần như:

```text
load
FMA
max
store
```

mà programmer không cần viết pointer, lifetime, SIMD intrinsic, CUDA kernel hay manual memory management.