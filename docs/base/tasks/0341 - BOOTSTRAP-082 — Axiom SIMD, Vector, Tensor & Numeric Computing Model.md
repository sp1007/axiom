# BOOTSTRAP-082 — Axiom SIMD, Vector, Tensor & Numeric Computing Model

**Trạng thái: FROZEN**

Mục tiêu của phần này:

> Axiom phải hỗ trợ từ số học vô hướng → SIMD → matrix/tensor → GPU/ML mà không biến SIMD/tensor thành một “ngôn ngữ thứ hai”, đồng thời không ép mọi chương trình phải mang theo runtime numeric/ML.

Kiến trúc tổng thể:

```text
Scalar Types
    │
    ├── Integer / Float
    │
    ▼
Vector Types
    │
    ├── Portable SIMD
    ├── Target SIMD
    │
    ▼
Matrix / Tensor Library
    │
    ├── CPU
    ├── SIMD
    └── GPU
```

---

# 1. Scalar là nền tảng

Core đã có:

```text
i8  i16  i32  i64
u8  u16  u32  u64
isize usize
f32 f64
```

Không tạo một hệ numeric type hoàn toàn riêng cho SIMD.

Ví dụ:

```ax
let x: f32 = 1.0
```

vẫn là scalar `f32`.

---

# 2. Vector là giá trị, không phải reference

Một vector SIMD:

```text
vector<T, N>
```

là một **value type**.

Ví dụ:

```ax
vector<f32, 4>
```

có semantic tương tự:

```text
[f32; 4]
```

nhưng representation và instruction mapping khác.

---

# 3. SIMD vector không đồng nghĩa array

Đây là distinction quan trọng:

```text
Array<T,N>
    = semantic collection

Vector<T,N>
    = SIMD computation value
```

Ví dụ:

```ax
let a: [f32; 4]
let v: vector<f32, 4>
```

không nhất thiết có cùng ABI.

---

# 4. SIMD không bắt buộc phần cứng SIMD

Nếu target không có native instruction phù hợp:

```text
vector<f32, 4>
```

vẫn có semantic hợp lệ.

Compiler có thể lower thành:

```text
scalar operations
```

hoặc:

```text
software sequence
```

nếu target contract cho phép.

---

# 5. Nhưng target SIMD được phép tối ưu mạnh

Trên CPU hỗ trợ:

```text
SSE
AVX
AVX2
AVX-512
NEON
SVE
RVV
```

compiler có thể map vector operations trực tiếp vào instruction tương ứng.

Không cần programmer viết intrinsic trong trường hợp thông thường.

---

# 6. Portable SIMD

Axiom cung cấp API/library portable:

```ax
vector<f32, 4>
vector<i32, 8>
```

với operations:

```text
add
sub
mul
div
min
max
abs
sqrt
fma
```

và comparison:

```text
eq
lt
le
gt
ge
```

---

# 7. Mask là value

SIMD comparison tạo:

```text
mask<T, N>
```

Ví dụ conceptual:

```ax
let m = a < b
```

`m` không phải `bool`.

Nó là vector predicate.

---

# 8. Mask operations

Có thể:

```text
select(mask, a, b)
any(mask)
all(mask)
none(mask)
```

Ví dụ:

```ax
let result = select(mask, a, b)
```

Compiler có thể lower thành conditional SIMD instruction.

---

# 9. No implicit scalar/vector confusion

Không tự động biến:

```text
f32
```

thành:

```text
vector<f32, 4>
```

hoặc ngược lại.

Broadcast phải là semantic operation:

```ax
vector.splat(x)
```

hoặc API tương đương.

---

# 10. Vector width là type parameter

Conceptually:

```text
vector<T, N>
```

với:

```text
T = element type
N = lane count
```

Điều này cho phép:

```text
vector<f32, 4>
vector<f32, 8>
vector<f32, 16>
```

mà không cần tạo hàng chục primitive type.

---

# 11. Nhưng physical register width khác semantic width

Ví dụ:

```text
vector<f32, 8>
```

có thể:

```text
AVX2 256-bit
```

hoặc compiler có thể split thành hai vector nhỏ hơn.

Do đó:

```text
semantic lane count
```

không nhất thiết bằng:

```text
physical register width
```

---

# 12. Explicit target vector

Khi programmer thực sự cần instruction/width cụ thể, system library có thể cung cấp target-specific types/intrinsics.

Ví dụ conceptual:

```text
x86::avx2::...
arm64::neon::...
```

Đây là system layer.

---

# 13. `@target_feature`

Đã có:

```ax
@target_feature("avx2")
fn process(...) ...
```

Ý nghĩa:

> Function được phép sử dụng feature đó.

Không có nghĩa compiler bắt buộc phải sinh đúng một instruction cụ thể.

---

# 14. Feature compatibility

Nếu function yêu cầu AVX2:

```text
caller
   ↓
function requiring AVX2
```

compiler phải đảm bảo execution environment phù hợp.

Có thể:

```text
compile-time target
```

hoặc:

```text
runtime CPU dispatch
```

nhưng runtime dispatch phải explicit.

---

# 15. No hidden CPU feature probing

Axiom không tự thêm:

```text
CPU detection runtime
dispatch table
```

vào executable nếu chương trình không yêu cầu.

---

# 16. Auto-vectorization

Đây mới là đường chính.

Code:

```ax
for i in 0..n {
    out[i] = a[i] + b[i]
}
```

Compiler có thể nhận ra:

```text
independent iterations
disjoint memory
no observable dependency
```

và vectorize.

---

# 17. Ownership/capability cung cấp alias information

Ví dụ:

```ax
fn add(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
)
```

Nếu verifier chứng minh:

```text
a ∩ out = ∅
b ∩ out = ∅
```

optimizer có thể dùng:

```text
NoAlias
```

nội bộ.

---

# 18. Không có `restrict` bắt buộc

Axiom không cần bắt programmer viết:

```c
float * restrict a
```

trong code thông thường.

Capability system + verifier cung cấp thông tin alias khi có thể chứng minh.

---

# 19. Nếu alias không chứng minh được

Compiler không được giả định:

```text
UNKNOWN == DISJOINT
```

Do đó có thể:

```text
không vectorize
```

thay vì tạo machine code sai.

---

# 20. Runtime alias checks

Compiler có thể chọn:

```text
if ranges_disjoint:
    vectorized path
else:
    conservative path
```

nếu lợi ích đủ lớn.

Đây là optimization.

Không thay đổi semantic result.

---

# 21. SIMD load/store

Portable SIMD library nên có:

```text
load
store
gather
scatter
```

nhưng semantics phải phân biệt:

```text
contiguous
possibly-unaligned
masked
indexed
```

---

# 22. Alignment

Không mặc định yêu cầu programmer manually align mọi SIMD buffer.

Compiler biết:

```text
alignment
layout
target requirements
```

và chọn instruction phù hợp.

Khi API yêu cầu alignment cụ thể, contract phải explicit.

---

# 23. Unaligned access

Unaligned SIMD access có thể là API hợp lệ nếu target hỗ trợ hoặc compiler lower được.

Không được nhầm:

```text
unaligned
```

với:

```text
invalid
```

---

# 24. Gather/scatter

Gather/scatter là operation có semantic cost cao hơn contiguous access.

Compiler không được coi chúng tương đương:

```text
contiguous load
```

cho mục đích performance modelling.

Nhưng correctness vẫn giống semantic indexed access.

---

# 25. SIMD reduction

Hỗ trợ:

```text
sum
min
max
product
```

và các reduction phù hợp.

Compiler có thể thay đổi thứ tự reduction **chỉ khi floating-point semantics cho phép**.

---

# 26. Floating-point semantics

Đây là điểm cực kỳ quan trọng.

Axiom không được mặc định biến:

```text
(a + b) + c
```

thành:

```text
a + (b + c)
```

nếu điều đó thay đổi observable floating-point semantics.

---

# 27. Fast-math phải explicit

Nếu muốn:

```text
reassociation
approximate math
flush-to-zero
contracted operations
```

phải có target/compiler policy hoặc explicit fast-math contract.

Không tự ý bật trong release build.

---

# 28. FMA

Compiler có thể dùng FMA nếu:

```text
observable floating semantics
```

cho phép.

Nếu semantics yêu cầu strict intermediate rounding thì không được tự ý thay đổi.

---

# 29. Integer SIMD

Integer vector hỗ trợ:

```text
add
sub
mul
bitwise
shift
compare
min/max
```

với semantics giống scalar tương ứng, ngoại trừ lane-wise execution.

---

# 30. Saturating arithmetic

Có thể cung cấp:

```text
saturating_add
saturating_sub
```

cả scalar và SIMD.

Không thay đổi semantics của ordinary `+`.

---

# 31. Wrapping arithmetic

Tương tự:

```text
wrapping_add
wrapping_sub
```

cho những thuật toán cần modulo arithmetic.

---

# 32. Checked SIMD operations

Nếu cần overflow detection:

```text
checked_add
```

có thể trả:

```text
(value, mask)
```

hoặc abstraction tương ứng.

---

# 33. SIMD comparison

Comparison tạo mask:

```text
vector<T,N> × vector<T,N>
        ↓
mask<N>
```

Không trả `[bool; N]` bắt buộc.

Compiler có thể giữ mask trong predicate register.

---

# 34. Shuffle / permute

Portable API nên hỗ trợ:

```text
shuffle
swizzle
permute
broadcast
extract
insert
```

với compile-time index khi có thể.

---

# 35. Compile-time shuffle indices

Nếu index là compile-time constant:

```text
shuffle<0, 3, 2, 1>(v)
```

compiler có thể map trực tiếp target instruction.

Runtime indices thì semantic khác và có thể tốn hơn.

---

# 36. SIMD abstraction must erase

Ví dụ:

```ax
fn add4(a: vector<f32,4>, b: vector<f32,4>) -> vector<f32,4> {
    a + b
}
```

không được tạo:

```text
VectorObject
HeapAllocation
RuntimeDispatch
```

chỉ vì type abstraction.

---

# 37. Generic SIMD

Generic code có thể:

```ax
fn add<T: SimdElement, N>(...)
```

và được specialize.

Không yêu cầu runtime generic metadata.

---

# 38. Tensor không phải Core primitive

Axiom Core không cần:

```text
Tensor
Matrix
NeuralNetwork
```

làm language primitive.

Đây là **Core/Standard/Application library domain**.

---

# 39. Tensor model

Tensor nên được xây trên:

```text
storage
+
element type
+
shape
+
stride
+
capability
```

Conceptual:

```text
TensorView<T, Rank>
```

có thể chứa:

```text
view<T>
shape
stride
```

---

# 40. Không dùng nested `view`

Không biến tensor thành:

```text
view<view<view<f32>>>
```

Điều đó tạo nhiều indirection và semantic complexity.

Thay vào đó:

```text
TensorView<f32, 3>
```

→ một contiguous/raw data capability + metadata.

---

# 41. Contiguous tensor

Tensor có thể có:

```text
shape = [2,3,4]
stride = [12,4,1]
```

cho row-major contiguous storage.

---

# 42. Strided tensor

Tensor view có thể:

```text
shape
stride
offset
```

mà không copy data.

Ví dụ:

```text
transpose
slice
broadcast
reshape
```

có thể chỉ tạo metadata view nếu semantic constraints cho phép.

---

# 43. Tensor view lifetime

Tensor view obeys cùng rule:

```text
owner
 ↓
TensorView
```

owner không được destroy/relocate khi live view còn tồn tại.

---

# 44. Tensor mutation

`TensorView` read-only.

`MutTensorView` mutable/exclusive.

Conceptual:

```text
TensorView<T,R>
MutTensorView<T,R>
```

là library abstractions xây trên capability model.

---

# 45. Tensor aliasing

Hai tensor views:

```text
A
B
```

không mặc định disjoint.

Compiler chỉ được giả định disjoint khi:

```text
capability verifier
```

chứng minh hoặc abstraction cung cấp contract.

---

# 46. Broadcasting

Broadcasting là library semantic.

Ví dụ:

```text
[4,1] + [1,8]
```

→ `[4,8]`.

Không cần compiler biến broadcasting thành một type-system theorem phức tạp.

---

# 47. Shape metadata

Ban đầu shape có thể là:

```text
runtime values
```

nhưng nếu compile-time known:

```text
Tensor<f32, [4,8]>
```

có thể được library/compiler specialize.

---

# 48. Static shape

Static shape giúp:

```text
loop unrolling
SIMD
tiling
stack allocation
GPU specialization
```

nhưng không bắt buộc.

---

# 49. Dynamic shape

Tensor runtime:

```text
shape: view<usize>
```

vẫn hợp lệ.

Compiler có thể optimize hot dimensions khi runtime profiling/guards cho phép.

---

# 50. Matrix

Matrix nên là specialization của tensor semantics, không cần primitive riêng trong Core.

Ví dụ:

```text
Matrix<T, M, N>
```

có thể là library type.

---

# 51. Matrix multiplication

Library có thể cung cấp:

```text
matmul(A, B)
```

và backend chọn:

```text
scalar
SIMD
BLAS
GPU
```

theo build/runtime policy.

---

# 52. No mandatory BLAS dependency

Axiom Standard Library không được yêu cầu:

```text
OpenBLAS
MKL
Accelerate
cuBLAS
```

để chương trình numeric cơ bản compile.

Các backend ngoại vi là optional integration.

---

# 53. But external acceleration is allowed

Application có thể chọn:

```text
Axiom implementation
```

hoặc:

```text
foreign optimized backend
```

qua FFI.

FFI ownership/ABI rules vẫn áp dụng.

---

# 54. Tensor storage domains

Tensor không nhất thiết nằm trên CPU RAM.

Library có thể có:

```text
CpuTensor
DeviceTensor
UnifiedTensor
ExternalTensor
```

hoặc abstraction tương ứng.

---

# 55. CPU/GPU distinction

Một:

```text
TensorView<f32>
```

không tự động trở thành GPU view.

GPU phải dùng storage domain phù hợp:

```text
DeviceView<T>
```

---

# 56. Host ↔ Device transfer

Transfer explicit:

```text
to_device()
to_host()
copy_to()
```

hoặc async variants.

Không tự động copy một tensor qua PCIe chỉ vì function cần nó.

---

# 57. Zero-copy GPU

Nếu hardware/storage domain cho phép:

```text
UnifiedBuffer
```

có thể tránh copy.

Nhưng unified memory không tự động đồng nghĩa với synchronization.

---

# 58. Tensor kernels

GPU kernel:

```ax
@kernel
fn add(
    a: DeviceView<f32>,
    b: DeviceView<f32>,
    out: DeviceMutView<f32>
)
```

phải tuân:

```text
AGPU
ownership
capability
synchronization
```

---

# 59. CPU tensor kernels

Cùng algorithm có thể có CPU implementation:

```ax
fn add_cpu(...)
```

Compiler có thể vectorize.

Không cần viết hai ngôn ngữ khác nhau.

---

# 60. Unified algorithm source

Lý tưởng:

```text
Tensor operation
      ↓
backend selection
      ├── scalar CPU
      ├── SIMD CPU
      └── GPU
```

Semantic operation giữ nguyên.

---

# 61. Explicit backend specialization

Nếu programmer muốn ép:

```text
CPU
GPU
AVX2
NEON
CUDA-like device
```

thì đây là library/build/system concern.

Không làm thay đổi Core type semantics.

---

# 62. Kernel fusion

Compiler/library backend có thể fuse:

```text
A * B
+
C
```

thành một kernel.

Nhưng chỉ khi:

```text
observable semantics
ownership
aliasing
synchronization
floating semantics
```

được bảo toàn.

---

# 63. Tensor expression templates không cần thiết

Axiom không cần C++-style:

```text
expression template
```

để đạt zero-cost abstraction.

Generic + MIR + optimizer + SSA đã cung cấp nền tảng tốt hơn.

---

# 64. Lazy tensor expressions

Có thể có library abstraction:

```text
lazy expression
```

nhưng nó phải là ordinary Axiom generic/trait code.

Compiler có thể inline/eliminate abstraction.

---

# 65. No mandatory tensor runtime

Chương trình:

```ax
fn main() {
    let x: f32 = 1.0
}
```

không link:

```text
tensor runtime
SIMD runtime
ML runtime
```

---

# 66. Numeric traits

Library nên có traits kiểu:

```text
Add
Sub
Mul
Div
Neg
Ord
Eq
Numeric
Float
Integer
SimdElement
```

nhưng không tạo hierarchy khổng lồ.

---

# 67. Operator semantics

Đã frozen:

```text
a + b
```

là trait-based operator semantics.

Do đó SIMD:

```text
a + b
```

có thể dùng cùng syntax.

---

# 68. Numeric literal typing

Literal:

```ax
1
1.0
```

không được tùy tiện trở thành bất kỳ numeric type nào mà không có inference rules deterministic.

Generic numeric APIs phải có conversion rõ ràng.

---

# 69. No implicit lossy conversion

Ví dụ:

```text
f64 → f32
i64 → i32
```

không implicit nếu có thể mất dữ liệu.

SIMD cũng vậy:

```text
vector<f64,N>
→ vector<f32,N>
```

phải explicit.

---

# 70. Integer-to-float conversion

Cũng explicit khi semantics có thể mất precision.

Ví dụ:

```ax
x as f32
```

hoặc conversion API tương ứng.

---

# 71. Numeric casts

Phân biệt:

```text
numeric conversion
```

với:

```text
bitcast
```

Đã khóa từ representation model.

---

# 72. SIMD bitcast

Có thể:

```text
bitcast<vector<u32,4>, vector<f32,4>>
```

nếu:

```text
size
alignment
valid representation
```

được đảm bảo.

Không phải numeric conversion.

---

# 73. Endianness

SIMD register value không tự mang semantic endian.

Endian chỉ trở thành vấn đề khi:

```text
load/store
serialization
FFI
memory representation
```

---

# 74. SIMD memory ordering

SIMD ordinary load/store:

```text
ordinary memory semantics
```

Không tự trở thành atomic.

Atomic vector operations chỉ tồn tại khi target/library hỗ trợ và semantic contract explicit.

---

# 75. Atomic vector

Không mặc định yêu cầu mọi:

```text
vector<T,N>
```

có:

```text
Atomic<vector<T,N>>
```

Atomicity phụ thuộc target/type support.

---

# 76. SIMD + concurrency

Vectorization không được biến:

```text
ordinary memory
```

thành concurrent-safe memory.

Optimizer vẫn phải bảo toàn:

```text
memory model
```

---

# 77. SIMD + volatile

Volatile vector operations phải giữ:

```text
volatile semantics
```

và không được gom/reorder như ordinary arithmetic.

---

# 78. SIMD + unsafe

Target intrinsics có thể yêu cầu:

```text
unsafe
```

nếu chúng expose machine-level assumptions.

Portable SIMD API nên cố gắng giữ safe.

---

# 79. Compiler intrinsic boundary

Intrinsics thuộc:

```text
compiler/system layer
```

không phải tất cả đều được expose trực tiếp cho programmer.

Portable API là preferred interface.

---

# 80. Machine-specific escape hatch

Khi cần instruction rất đặc biệt:

```text
target intrinsic
inline asm
```

vẫn có.

Nhưng đây là low-level escape hatch.

---

# 81. Vector ABI

ABI của:

```text
vector<T,N>
```

phụ thuộc target.

Compiler có thể truyền bằng:

```text
register
multiple registers
stack
indirect
```

theo ABI.

---

# 82. Vector layout

Không mặc định coi vector:

```text
vector<f32,4>
```

là:

```text
@repr(C) [f32;4]
```

trừ khi representation contract yêu cầu.

---

# 83. Interop vector

Nếu FFI cần vector ABI cụ thể:

```text
@repr(C)
```

hoặc explicit system representation.

Không tự suy luận từ semantic vector type.

---

# 84. Tensor ABI

Tensor type không FFI-safe mặc định.

C ABI wrapper nên dùng:

```text
pointer
length
shape pointer
rank
stride
```

với contract rõ ràng.

---

# 85. No hidden allocator in tensor

Creating:

```text
TensorView
```

không allocation.

Creating:

```text
Tensor
```

may allocate theo library semantics.

Compiler vẫn có thể eliminate allocation nếu storage semantics cho phép.

---

# 86. Tensor ownership

Owning tensor:

```text
Tensor<T>
```

là owner.

View:

```text
TensorView<T,R>
```

không owner.

Move/Drop semantics như collection.

---

# 87. Tensor clone

Tensor duplication:

```text
clone()
```

có thể copy toàn bộ underlying elements.

Không bao giờ giả định clone chỉ copy metadata.

---

# 88. Tensor view clone/copy

View capability semantics khác:

```text
TensorView
```

có thể tạo thêm read capabilities khi compiler chứng minh lifetime/provenance.

Không biến thành ownership.

---

# 89. Tensor mutation and broadcasting

Broadcasted mutable views phải cực kỳ chặt.

Ví dụ:

```text
shape [4,1]
broadcast → [4,8]
```

nhiều logical positions có thể map cùng physical element.

Không được tạo:

```text
mut_view
```

mang nhiều write aliases đến cùng storage nếu API không có special semantics.

---

# 90. Reduction and parallelism

Reduction có thể chạy parallel nếu operation có semantic properties phù hợp.

Ví dụ integer sum có thể có defined associative/wrapping semantics.

Floating-point reduction phải tuân floating-point policy.

---

# 91. Parallel tensor execution

Parallel tensor library phải kiểm tra:

```text
Send
Share
capability
disjointness
synchronization
```

Không được mặc định:

```text
parallel = safe
```

---

# 92. Automatic parallelization

Compiler có thể tự parallelize loop khi chứng minh:

```text
independent iterations
```

nhưng parallel execution là optimization trừ khi source/library semantics yêu cầu deterministic ordering.

---

# 93. Determinism

Axiom phân biệt:

```text
semantic determinism
```

với:

```text
floating-point reproducibility
```

Parallel floating reduction có thể cần explicit deterministic mode.

---

# 94. Numeric reproducibility

Build/test systems nên có policy:

```text
strict
reproducible
fast
```

nhưng đây là compilation/runtime policy, không làm thay đổi Core numeric semantics âm thầm.

---

# 95. Performance hierarchy

Axiom numeric stack:

```text
scalar
  ↓
compiler auto-vectorization
  ↓
portable SIMD
  ↓
target SIMD/intrinsics
  ↓
tensor library
  ↓
GPU
  ↓
external accelerators
```

Programmer chỉ xuống tầng thấp hơn khi thực sự cần kiểm soát.

---

# 96. Zero-cost goal

Các abstraction:

```text
Vector
Mask
Iterator
TensorView
StaticShape
Generic numeric algorithm
```

không được mặc định tạo:

```text
heap allocation
virtual dispatch
runtime type metadata
object header
```

---

# 97. Compiler optimization opportunities

OptIR nên có:

```text
VectorInfo
ReductionInfo
MemoryAccessInfo
AlignmentInfo
StrideInfo
ShapeInfo
TargetFeatureInfo
```

để optimizer có đủ dữ liệu.

---

# 98. AI-friendly numeric model

Compiler có thể expose:

```text
explain vectorization
explain missed-vectorization
explain alias block
explain alignment
explain target feature
explain tensor fusion
```

Ví dụ:

```text
vectorization rejected:
  reason = POSSIBLE_ALIAS
  region A = [0,n)
  region B = [0,n)
  proof = UNKNOWN
```

Điều này rất hữu ích cho AI agent.

---

# 99. Core boundary

Axiom Core chỉ cần biết những primitive cần thiết cho semantic correctness.

SIMD/tensor implementation chủ yếu nằm ở:

```text
Core
  ↓
Core Numeric Library
  ↓
Standard Numeric Library
  ↓
Target/System Backend
```

Không biến Core thành ML framework.

---

# 100. Frozen Invariants — `ANUM-20..100`

**ANUM-20** — Scalar numeric types are fundamental Axiom values.

**ANUM-21** — SIMD vectors are value-semantic types.

**ANUM-22** — SIMD vector semantics are distinct from array semantics.

**ANUM-23** — SIMD vector width is a semantic lane count.

**ANUM-24** — Physical register width is an implementation property.

**ANUM-25** — A SIMD vector does not require a native SIMD instruction set.

**ANUM-26** — Unsupported SIMD operations may be lowered to scalar or alternative target sequences.

**ANUM-27** — Portable SIMD does not require runtime dispatch.

**ANUM-28** — Target-specific SIMD is an explicit system/backend facility.

**ANUM-29** — Target feature requirements are explicit contracts.

**ANUM-30** — CPU feature probing is not implicitly added to programs.

**ANUM-31** — SIMD masks are semantic predicate values.

**ANUM-32** — SIMD comparison produces mask semantics.

**ANUM-33** — Scalar-to-vector broadcast is explicit.

**ANUM-34** — Vector-to-scalar extraction is explicit.

**ANUM-35** — SIMD arithmetic follows corresponding scalar arithmetic semantics per lane.

**ANUM-36** — SIMD arithmetic does not silently change overflow semantics.

**ANUM-37** — Saturating arithmetic is explicit.

**ANUM-38** — Wrapping arithmetic is explicit.

**ANUM-39** — Checked arithmetic is explicit.

**ANUM-40** — SIMD bitwise operations preserve bit-level semantics.

**ANUM-41** — Numeric conversion is distinct from bitcast.

**ANUM-42** — SIMD bitcast requires valid representation constraints.

**ANUM-43** — Floating-point reassociation is not implicitly permitted.

**ANUM-44** — Fast-math behavior requires an explicit semantic or compilation contract.

**ANUM-45** — FMA contraction must respect floating-point semantics.

**ANUM-46** — SIMD memory operations obey the ordinary Axiom memory model unless explicitly atomic/volatile.

**ANUM-47** — SIMD operations do not imply synchronization.

**ANUM-48** — SIMD operations do not imply atomicity.

**ANUM-49** — Volatile SIMD access remains volatile.

**ANUM-50** — Atomic SIMD access is supported only where an explicit target/library contract exists.

**ANUM-51** — Safe SIMD APIs must preserve capability rules.

**ANUM-52** — Unsafe target intrinsics may expose machine-specific preconditions.

**ANUM-53** — Auto-vectorization is an optimization.

**ANUM-54** — Auto-vectorization must preserve observable semantics.

**ANUM-55** — Auto-vectorization may use proven alias information.

**ANUM-56** — UNKNOWN aliasing cannot be treated as DISJOINT.

**ANUM-57** — Runtime alias checks may be introduced as an optimization when semantics are preserved.

**ANUM-58** — Alignment assumptions must be proven or explicitly contracted.

**ANUM-59** — Unaligned access is distinct from invalid access.

**ANUM-60** — Gather/scatter semantics are distinct from contiguous memory access.

**ANUM-61** — SIMD abstractions should be erasable by optimization.

**ANUM-62** — SIMD generic abstractions use ordinary Axiom generics and traits.

**ANUM-63** — SIMD does not require runtime generic metadata.

**ANUM-64** — Tensor is not a mandatory Core language primitive.

**ANUM-65** — Tensor abstractions are primarily library facilities.

**ANUM-66** — Tensor views are built from data capabilities plus shape/stride metadata.

**ANUM-67** — Tensor views do not require nested view objects.

**ANUM-68** — Tensor views do not own their underlying storage.

**ANUM-69** — Tensor view lifetime follows capability provenance.

**ANUM-70** — Tensor mutation requires exclusive mutable capability.

**ANUM-71** — Tensor aliasing is not assumed disjoint without proof.

**ANUM-72** — Tensor broadcasting cannot create invalid overlapping mutable capabilities.

**ANUM-73** — Static tensor shapes may enable specialization.

**ANUM-74** — Dynamic tensor shapes remain valid.

**ANUM-75** — Matrix abstractions may be implemented as tensor/library specializations.

**ANUM-76** — Matrix multiplication is a library semantic operation.

**ANUM-77** — Numeric libraries do not require external BLAS/ML runtimes.

**ANUM-78** — External numeric backends may be integrated explicitly through FFI/system APIs.

**ANUM-79** — Tensor storage domains are explicit.

**ANUM-80** — CPU tensor storage and device tensor storage are distinct domains.

**ANUM-81** — Host/device transfer is explicit.

**ANUM-82** — Unified memory does not imply synchronization.

**ANUM-83** — GPU tensor operations follow GPU ownership and capability rules.

**ANUM-84** — Tensor kernels are ordinary Axiom functions subject to execution-domain constraints.

**ANUM-85** — CPU and GPU numeric implementations may share semantic APIs.

**ANUM-86** — Kernel fusion is an optimization subject to semantic preservation.

**ANUM-87** — Tensor expression abstractions must not impose mandatory allocation or dispatch.

**ANUM-88** — Tensor ownership follows ordinary Move/Copy/Clone/Drop semantics.

**ANUM-89** — Tensor cloning may duplicate underlying data and is explicit.

**ANUM-90** — Tensor view duplication does not create ownership.

**ANUM-91** — Numeric conversions that may lose information are explicit.

**ANUM-92** — Vector ABI is target-dependent unless an explicit representation contract exists.

**ANUM-93** — Tensor types are not FFI-safe by default.

**ANUM-94** — FFI tensor wrappers must expose explicit pointer/shape/stride/ownership contracts.

**ANUM-95** — Numeric abstractions must not introduce a mandatory numeric runtime.

**ANUM-96** — Numeric execution may specialize across scalar, SIMD and GPU backends.

**ANUM-97** — Parallel numeric execution must preserve ownership, capability and concurrency semantics.

**ANUM-98** — Floating-point reproducibility policies must not silently alter Core semantics.

**ANUM-99** — Numeric abstractions should be zero-cost where the target and observable semantics permit.

**ANUM-100** — SIMD, tensor and numeric optimization cannot change Axiom semantic correctness.

---

## Một quyết định kiến trúc quan trọng đã được khóa

Axiom **không** đi theo hướng:

```text
Language Core
 ├── Tensor primitive
 ├── Matrix primitive
 ├── GPU primitive
 ├── Neural Network primitive
 ├── BLAS runtime
 └── ML runtime
```

mà:

```text
                Axiom Core
                    │
       ┌────────────┼────────────┐
       ▼            ▼            ▼
    Scalar        SIMD        Capability
       │            │            │
       └────────────┼────────────┘
                    ▼
             Numeric Library
                    │
              Tensor Library
                    │
        ┌───────────┴───────────┐
        ▼                       ▼
       CPU                     GPU
   scalar/SIMD             Device kernels
```

Điều này rất phù hợp với mục tiêu ban đầu của Axiom: **một ngôn ngữ systems mạnh nhưng không bị biến thành framework**.

### Bước tiếp theo

Sau numeric model, còn một mảng rất lớn trước khi chuyển sang giai đoạn “spec gần hoàn chỉnh”:

**BOOTSTRAP-083 — Axiom Compile-Time/Runtime Security, Safety Profiles, Capability Security & Sandboxing**

Nó sẽ khóa các vấn đề như:

- safe / unsafe / trusted boundary;
- sandbox;
- capability-based security;
- process isolation;
- memory safety vs security;
- FFI trust boundary;
- privilege separation;
- syscall security;
- secure handles;
- secret/memory wiping;
- constant-time cryptographic code;
- side-channel considerations;
- embedded/freestanding security;
- GPU/device security;
- và cách Axiom tránh biến `unsafe` thành một “lỗ thủng toàn bộ hệ thống”.