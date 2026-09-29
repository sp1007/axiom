# BOOTSTRAP-078 — Axiom SIMD / Vector / Matrix / Tensor Execution Model

**Trạng thái: FROZEN**

Mục tiêu của phần này là để Axiom có thể viết được:

- code scalar thông thường,
- SIMD CPU,
- numerical computing,
- matrix/tensor,
- AI inference/training,
- GPU kernel,

mà **không biến ngôn ngữ thành một DSL toán học riêng** và không bắt programmer phải tự viết intrinsic cho mọi trường hợp.

Nguyên tắc lớn:

> **Scalar là semantic baseline. Vectorization là một execution representation có thể được viết explicit khi cần, nhưng compiler phải tự vectorize scalar code khi có đủ bằng chứng.**

---

# 1. Không biến SIMD thành một ngôn ngữ riêng

Axiom không cần:

```text
vector_language
tensor_language
gpu_language
```

Thay vào đó:

```text
Axiom type system
        │
        ├── Scalar
        ├── SIMD Vector
        ├── Matrix
        └── Tensor library
```

Tất cả vẫn dùng:

- ownership
- capability
- traits
- generics
- comptime
- `@kernel`
- Result/Option
- memory model.

---

# 2. Scalar semantics là nguồn chân lý

Ví dụ:

```ax
fn add(a: f32, b: f32) -> f32 {
    a + b
}
```

Compiler có thể biến thành:

```text
scalar add
    ↓
SIMD add
    ↓
multiple elements / instruction
```

nhưng kết quả phải tuân semantic contract của phép toán.

Do đó SIMD không được tạo ra một bộ semantics mâu thuẫn với scalar.

---

# 3. SIMD Vector là Core type

Nên có một primitive generic dạng:

```text
simd<T, N>
```

Trong đó:

```text
T = element type
N = compile-time lane count
```

Ví dụ:

```ax
simd<f32, 4>
simd<i32, 8>
simd<u8, 16>
```

`N` là compile-time constant.

---

# 4. SIMD không phải Array

Hai type:

```ax
[ f32; 4 ]
```

và:

```ax
simd<f32, 4>
```

không giống nhau.

### Array

```text
data structure
ordered elements
memory representation
indexable
```

### SIMD

```text
machine-oriented vector value
designed for parallel arithmetic
may live entirely in registers
```

Compiler không được mặc định SIMD phải tồn tại trong memory.

---

# 5. SIMD value semantics

`simd<T,N>` là value.

Ví dụ:

```ax
let a: simd<f32, 4>
let b = a
```

Nếu SIMD type thỏa `Copy`, `b` là một value độc lập về semantic.

Không có:

```text
hidden reference
hidden allocation
hidden heap object
```

---

# 6. Lane semantics

SIMD vector có:

```text
lane 0
lane 1
...
lane N-1
```

Các phép toán element-wise:

```ax
a + b
a - b
a * b
a / b
```

được định nghĩa theo từng lane.

Ví dụ semantic:

```text
result[i] = a[i] + b[i]
```

---

# 7. Không yêu cầu hardware có đúng N lanes

Đây là điểm rất quan trọng.

```text
simd<f32, 4>
```

là **semantic vector width**, không nhất thiết là một instruction duy nhất.

Target có thể:

```text
SSE   → 1 instruction
AVX   → 1 instruction
scalar → 4 instructions
```

hoặc target khác có thể split/combine.

Như vậy portable SIMD không bị khóa vào ISA.

---

# 8. Explicit SIMD và hardware SIMD

Có hai mức:

```text
Portable SIMD
    simd<T,N>

Target SIMD
    architecture-specific intrinsic
```

Ví dụ:

```text
axiom.simd
axiom.arch.x86
axiom.arch.arm
axiom.arch.riscv
```

Application code nên ưu tiên portable SIMD.

---

# 9. Target feature

Các ISA feature:

```text
SSE2
AVX
AVX2
AVX-512
FMA
NEON
SVE
RVV
```

không nên trở thành những keyword riêng.

Dùng attribute:

```ax
@target_feature("avx2")
fn process(...) {
    ...
}
```

Compiler kiểm tra:

```text
target supports feature?
call site valid?
dispatch required?
```

---

# 10. Target feature không được âm thầm phá portability

Nếu function yêu cầu:

```ax
@target_feature("avx2")
```

thì binary không được vô tình chạy AVX2 trên CPU không hỗ trợ.

Có ba trường hợp:

```text
compile target fixed
    → caller must satisfy target

multi-target runtime dispatch
    → explicit library mechanism

unsupported
    → compile error
```

Không implicit runtime dispatch trong Core.

---

# 11. SIMD operators

Các operator thông thường:

```ax
+
-
*
/
%
&
|
^
<<
>>
==
<
>
```

có thể được định nghĩa cho SIMD khi semantics hợp lệ.

Kết quả comparison thường là:

```text
simd_mask<N>
```

thay vì:

```text
bool
```

---

# 12. SIMD mask

Cần primitive:

```text
simd_mask<N>
```

Ví dụ:

```ax
let mask = a > b
```

semantic:

```text
mask[i] = a[i] > b[i]
```

Mask không nhất thiết có representation là `bool` từng byte.

Backend có thể dùng:

```text
predicate registers
bit masks
vector registers
```

---

# 13. Masked operations

SIMD cần:

```text
select
masked_load
masked_store
masked_add
masked_mul
```

Ví dụ conceptually:

```ax
select(mask, a, b)
```

nghĩa:

```text
mask[i] ? a[i] : b[i]
```

Compiler có thể lower thành hardware blend/predicate instruction.

---

# 14. Gather / Scatter

Portable abstraction:

```text
gather(base, indices)
scatter(base, indices, values)
```

Nhưng đây là memory operation, vì vậy phải chịu ownership/capability rules.

Ví dụ:

```ax
fn gather(
    data: view<f32>,
    indices: simd<usize, 8>
) -> simd<f32, 8>
```

Compiler phải kiểm tra range nếu safe API yêu cầu.

---

# 15. Bounds checking

Không muốn SIMD API khiến programmer phải dùng unsafe chỉ để đạt tốc độ.

Ví dụ:

```ax
for i in 0..n {
    out[i] = a[i] + b[i]
}
```

Compiler có thể chứng minh:

```text
0 <= i < n
```

và loại bỏ bounds checks.

Sau đó vectorize.

Đây là một mục tiêu quan trọng:

> **Safe scalar code phải có cơ hội trở thành native SIMD code.**

---

# 16. Auto-vectorization

OptIR đã có:

```text
RangeInfo
AliasInfo
EffectInfo
LoopInfo
```

Nên compiler có đủ dữ liệu để làm:

```text
scalar loop
    ↓
dependence analysis
    ↓
alias analysis
    ↓
range analysis
    ↓
vectorization
```

Ví dụ:

```ax
fn add(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
) {
    for i in 0..out.len() {
        out[i] = a[i] + b[i]
    }
}
```

Nếu verifier chứng minh các region không overlap, compiler có thể vectorize.

---

# 17. Không dùng `restrict` trong source

Đã frozen:

```text
không có source-level restrict trong Core v1
```

Thay vào đó:

```text
ownership
view
mut_view
region analysis
```

cung cấp alias information.

Ví dụ:

```ax
fn add(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
)
```

`mut_view` đã cung cấp thông tin mạnh hơn raw pointer.

---

# 18. Khi alias không chứng minh được

Compiler không được đoán:

```text
a != out
```

Nếu không chứng minh được.

Có ba hướng:

```text
1. runtime versioning
2. scalar fallback
3. explicit unsafe/noalias contract
```

Compiler có thể tự sinh:

```text
if non_overlap:
    SIMD path
else:
    scalar path
```

nếu profitable.

---

# 19. Runtime vectorization versioning

Đây là một tối ưu rất hữu ích.

Ví dụ:

```text
unknown alias
      ↓
runtime overlap check
      ↓
┌───────────────┬──────────────┐
│ disjoint      │ overlapping  │
│ SIMD          │ scalar       │
└───────────────┴──────────────┘
```

Semantics vẫn an toàn.

Không cần bắt programmer viết hai phiên bản.

---

# 20. Reduction

Các phép:

```text
sum
product
min
max
and
or
xor
```

cần reduction primitives.

Ví dụ:

```ax
let total = reduce_add(v)
```

Nhưng floating-point reduction cần đặc biệt cẩn thận.

---

# 21. Floating-point reduction

Không được mặc định:

```text
(a+b)+c == a+(b+c)
```

với floating point.

Do đó compiler không được tùy tiện vectorize/reassociate FP operations nếu semantic profile không cho phép.

Axiom nên có:

```text
strict FP semantics
```

làm mặc định an toàn.

Optimization aggressive có thể được explicit profile/attribute.

---

# 22. Fast math

Không đưa:

```text
-fast-math
```

thành semantic mặc định.

Có thể có:

```ax
@fast_math
```

nhưng đây phải là **semantic-affecting contract**, không chỉ optimization hint.

Nó cho phép compiler thay đổi một số FP assumptions theo contract được định nghĩa rõ.

---

# 23. NaN / infinity

Axiom phải xác định semantics rõ cho:

```text
NaN
+∞
-∞
signed zero
```

và không được coi floating point là integer-like algebra.

SIMD FP giữ cùng semantics cơ bản.

---

# 24. Integer SIMD overflow

Phải kế thừa semantics integer của Axiom:

```text
checked
wrapping
saturating
```

không để CPU instruction tự quyết định.

Ví dụ:

```ax
a.wrapping_add(b)
a.saturating_add(b)
```

có thể lower trực tiếp đến instruction phù hợp.

---

# 25. Saturating arithmetic

Rất hữu ích cho:

- image processing
- audio
- quantized ML
- DSP.

Ví dụ:

```ax
a.saturating_add(b)
```

với `u8` có semantic:

```text
min(a+b, 255)
```

Compiler chọn hardware instruction nếu có.

---

# 26. Horizontal operations

Các phép:

```text
horizontal_add
horizontal_min
horizontal_max
```

là library/compiler intrinsics.

Không cần tạo syntax riêng.

---

# 27. Shuffle / permute

SIMD cần:

```text
shuffle
permute
extract
insert
broadcast
zip
unzip
transpose
```

nhưng API có thể nằm trong:

```text
axiom.simd
```

Compiler nhận diện intrinsic và lower trực tiếp.

---

# 28. SIMD ABI

SIMD type có ABI target-dependent.

Ví dụ:

```text
simd<f32,4>
```

có thể truyền bằng vector register.

Nhưng:

```text
simd<f32,100>
```

không nhất thiết.

ABI lowering quyết định:

```text
registers
stack
memory
split aggregates
```

Không encode ABI vào semantic type.

---

# 29. SIMD alignment

SIMD value không mặc định yêu cầu alignment đặc biệt nếu compiler giữ trong register.

Khi materialize memory:

```text
alignment
```

phụ thuộc representation.

API explicit:

```text
aligned_load
aligned_store
```

nếu hardware contract cần.

Unaligned load/store phải có semantics rõ ràng.

---

# 30. SIMD load/store

Nên phân biệt:

```text
load
store
masked_load
masked_store
aligned_load
unaligned_load
```

nhưng không nhất thiết tất cả là Core syntax.

Phần lớn nằm trong `axiom.simd`.

---

# 31. Matrix không phải Core primitive

Axiom không nên thêm:

```text
matrix
tensor
```

vào language core.

Lý do:

```text
matrix semantics
shape
stride
layout
broadcast
dtype
device
autodiff
sparse
quantization
```

sẽ làm Core phình rất nhanh.

Matrix/Tensor nên là library abstractions.

---

# 32. Tensor model

Một tensor view nên conceptually có:

```text
TensorView<T, Rank>
    data
    shape
    stride
```

Ví dụ:

```text
TensorView<f32, 4>
```

có:

```text
data: view<f32>
shape: [usize; 4]
stride: [isize; 4]
```

Representation thực tế compiler/library có thể tối ưu.

---

# 33. Không dùng nested view làm tensor

Không nên:

```text
view<view<view<f32>>>
```

để biểu diễn tensor.

Điều đó tạo:

- nhiều indirection
- nested capability complexity
- layout không rõ
- khó vectorize.

Thay vào đó:

```text
TensorView
    ↓
one underlying data region
    +
shape
    +
stride
```

---

# 34. TensorView ownership

Có:

```text
Tensor<T, Rank>
```

owning storage.

và:

```text
TensorView<T, Rank>
```

non-owning.

Tương tự:

```text
TensorMutView<T, Rank>
```

cho mutation.

Đây là library-level abstraction nhưng dùng Core capability semantics.

---

# 35. Contiguous tensor

Tensor có thể có:

```text
Contiguous
NonContiguous
Strided
Broadcasted
```

không nên giả định mọi tensor đều contiguous.

Compiler/library có thể có trait:

```text
Contiguous
```

để specialization.

---

# 36. Shape là compile-time hoặc runtime

Axiom nên hỗ trợ cả:

```text
Tensor<f32, 3>
```

với shape runtime:

```text
[usize; 3]
```

và compile-time shape thông qua const generics:

```text
Tensor<f32, 3, [32,32,64]>
```

nhưng không đưa dependent type theorem system vào Core.

---

# 37. Stride

Stride có thể signed:

```text
isize
```

vì view có thể biểu diễn:

- reverse
- transpose
- subregion.

Nhưng raw stride manipulation phải chịu bounds/provenance checks.

---

# 38. Broadcast

Broadcast view có thể có stride zero:

```text
stride[i] = 0
```

Nhưng mutable broadcast view rất nguy hiểm.

Ví dụ nhiều logical elements map vào cùng một physical location.

Do đó:

```text
read broadcast view
    safe

mutable broadcast view
    restricted
```

trừ khi operation semantics xác định rõ.

---

# 39. Tensor aliasing

Hai TensorView có thể cùng data.

Compiler cần biết:

```text
region
shape
stride
alias relation
```

Không được suy luận disjoint chỉ từ shape.

Ví dụ:

```text
transpose(A)
```

vẫn trỏ cùng storage.

---

# 40. Tensor mutation

`TensorMutView` tương ứng semantic:

```text
exclusive write capability
```

Nếu two tensor views overlap:

```text
write/write
```

→ reject trong safe code.

---

# 41. Parallel tensor operations

Ví dụ:

```ax
parallel_for(...)
```

không phải Core primitive.

Library/runtime có thể cung cấp.

Compiler/verifier vẫn kiểm tra:

```text
Send
Share
region disjointness
```

và scheduler thực hiện parallelism.

---

# 42. Matrix multiplication

Không cần compiler keyword:

```text
matmul
```

Library:

```ax
matmul(a, b, out)
```

Compiler có thể recognize:

```text
matmul
```

và dispatch:

```text
scalar
SIMD
BLAS
GPU
specialized kernel
```

mà API semantic không đổi.

---

# 43. Kernel specialization

Comptime có thể tạo specialization:

```text
f32 × shape × target
```

Ví dụ:

```text
CPU AVX2
CPU AVX512
ARM NEON
GPU
```

Generated code phải quay lại pipeline:

```text
HIR
→ type
→ ownership
→ verification
```

không bypass safety.

---

# 44. CPU ↔ GPU tensor model

Không nên làm:

```text
Tensor<T>
```

vừa là CPU vừa là GPU memory một cách implicit.

Nên phân biệt:

```text
Tensor<T>
DeviceTensor<T>
TensorView<T>
DeviceTensorView<T>
```

hoặc một abstraction có storage-domain parameter ở library level.

---

# 45. Storage domain vẫn là semantic boundary

Ví dụ:

```text
Host memory
Device memory
Shared/Unified memory
External memory
```

khác nhau.

Compiler không tự chèn:

```text
CPU → GPU memcpy
```

chỉ vì type mismatch.

Transfer phải explicit.

---

# 46. Zero-copy tensor

Nếu OS/GPU hỗ trợ:

```text
UnifiedBuffer
MappedBuffer
Pinned/DMA storage
```

library có thể cung cấp zero-copy abstraction.

Nhưng:

```text
zero-copy ≠ always faster
```

đây là implementation/performance property.

---

# 47. SIMD + ownership

SIMD value có thể chứa:

```text
primitive
```

và các type phù hợp khác.

Nhưng không được cho phép:

```text
simd<DropType,N>
```

một cách tùy tiện nếu Drop semantics không xác định rõ.

Ban đầu nên giới hạn SIMD element type:

```text
integer
float
bool/mask
```

và các representation types tương thích.

---

# 48. SIMD generic operations

Có thể:

```ax
fn add<T, N>(a: simd<T,N>, b: simd<T,N>) -> simd<T,N>
```

với trait constraints:

```text
T: SimdElement
```

Compiler specialization tạo native instructions.

---

# 49. Portable SIMD trait

Nên có compiler-known/library trait:

```text
SimdElement
```

và:

```text
SimdLaneCount
```

nhưng không để trait solver phải theorem-prove mọi thứ về vector.

Các property quan trọng là compiler-known facts.

---

# 50. Vector length

`N` phải là compile-time known đối với primitive `simd<T,N>`.

Nếu vector length runtime:

```text
DynamicVector<T>
```

là library type, thường backed by memory.

Không nhầm:

```text
SIMD vector
```

với:

```text
dynamic numeric vector
```

---

# 51. `Vec<T>` ≠ SIMD vector

Tên `Vec` dễ gây nhầm.

Trong Axiom:

```text
Vec<T>
```

= growable collection.

```text
simd<T,N>
```

= fixed-lane vector value.

Documentation/tooling phải giữ distinction này.

---

# 52. SIMD gather và capability

Gather:

```ax
gather(data, indices)
```

cần đảm bảo mỗi index hợp lệ.

Nếu compiler không chứng minh:

```text
index < data.len()
```

safe implementation phải:

```text
checked
```

hoặc có explicit unchecked/unsafe variant.

---

# 53. Scatter aliasing

Scatter phức tạp hơn gather:

```text
scatter(data, indices, values)
```

Nếu:

```text
indices = [1,1,2,2]
```

thì nhiều lanes ghi cùng location.

Safe semantics phải được xác định.

Không để kết quả phụ thuộc instruction ordering một cách vô thức.

---

# 54. Safe scatter

Có thể cung cấp:

```text
scatter_unique
scatter
atomic_scatter
```

trong library.

`scatter_unique` yêu cầu indices không trùng.

`atomic_scatter` yêu cầu element type atomic-compatible.

Ordinary `scatter` phải có deterministic semantic contract hoặc bị hạn chế.

---

# 55. SIMD atomics

Không mặc định mọi vector operation atomic.

```text
simd<T,N>
```

không phải:

```text
Atomic<simd<T,N>>
```

Atomic vector chỉ hỗ trợ nếu target/library contract xác định.

---

# 56. SIMD + memory ordering

Nếu có atomic SIMD:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

phải kế thừa Core memory model.

Không tạo một memory model riêng cho SIMD.

---

# 57. Vector masks và branch

Compiler có thể lower:

```ax
if mask[i] { ... }
```

thành:

```text
predication
mask
branch
```

tùy target.

Không yêu cầu programmer dùng intrinsic.

---

# 58. Vectorization của `if`

Ví dụ:

```ax
for i in 0..n {
    if a[i] > 0 {
        out[i] = a[i]
    } else {
        out[i] = 0
    }
}
```

có thể thành:

```text
compare
mask
select
```

nếu semantics cho phép.

---

# 59. Vectorization của function call

Compiler có thể inline:

```ax
map(a, square)
```

sau đó:

```text
inline
→ loop
→ vectorize
```

Nếu closure/function không có observable side effects cản trở.

Đây là nơi zero-cost abstraction phát huy tác dụng.

---

# 60. Iterator + SIMD

Iterator pipeline:

```ax
a.iter()
 .map(square)
 .filter(...)
 .sum()
```

không được mặc định tạo:

```text
iterator objects
allocations
virtual calls
```

Compiler có thể:

```text
monomorphize
inline
fuse
loopify
vectorize
```

thành một loop.

---

# 61. Parallel iterator

Nếu library có:

```text
parallel_iter()
```

thì compiler/runtime có thể chia region:

```text
[0..N]
 ↓
[0..K]
[K..2K]
...
```

và mỗi worker có capability region riêng.

Ownership/capability model vẫn là nền tảng.

---

# 62. Vectorization + floating point determinism

Parallel/SIMD floating point có thể thay đổi:

```text
reduction order
```

Do đó:

```text
deterministic numeric mode
```

có thể yêu cầu reduction order cố định.

Không nên hứa bit-identical FP nếu program cho phép reassociation.

---

# 63. Quantized AI types

Không cần thêm `fp8`, `bf16`, `int4` vào Core primitive ngay từ đầu.

Có thể có numeric/system types:

```text
bf16
fp16
fp8
i4
u4
```

ở specialized numeric library/compiler intrinsic layer.

Nếu target support tốt, compiler lowers trực tiếp.

---

# 64. Matrix/vector mixed precision

API có thể:

```ax
matmul<f16, f32>(...)
```

hoặc dùng explicit accumulation type.

Điểm quan trọng:

```text
storage type
computation type
accumulation type
```

có thể khác nhau.

Không ép Core numeric model phải chứa toàn bộ AI type universe.

---

# 65. Tensor layout optimization

Compiler/library có thể transform:

```text
NCHW
NHWC
blocked
tiled
packed
```

nhưng layout phải là semantic metadata của Tensor abstraction.

Không được giả định tensor layout chỉ là contiguous row-major.

---

# 66. Tiling

Matrix/tensor compiler optimization có thể:

```text
loop tiling
cache blocking
register blocking
vectorization
unrolling
fusion
```

Đây là compiler optimization.

Không cần programmer viết:

```text
#pragma omp simd
```

cho mọi trường hợp.

---

# 67. Explicit vectorization hint

Có thể có:

```ax
@vectorize
```

nhưng nên coi là **hint/optimization request**, không phải safety mechanism.

Nếu compiler không vectorize được:

```text
diagnostic/explain
```

có thể nói lý do.

Không thay đổi semantics.

---

# 68. Vectorization explanation

Axiom compiler nên hỗ trợ:

```text
axiom explain vectorize
```

Ví dụ:

```text
Loop L42:
    vectorized: yes
    width: 8
    ISA: AVX2
    reason:
        no conflicting writes
        bounds proven
        function inlined
```

Hoặc:

```text
vectorized: no
reason:
    possible alias between a and out
```

Đây rất hữu ích cho cả programmer và AI agent.

---

# 69. SIMD diagnostics machine-readable

Compiler metadata:

```text
VectorizationReport {
    loop_id
    width
    target_feature
    alias_status
    dependence_status
    remainder_strategy
    reason
}
```

AI có thể đọc trực tiếp.

---

# 70. Remainder handling

Nếu:

```text
N % SIMD_WIDTH != 0
```

compiler có thể:

```text
main vector loop
+
scalar remainder
```

hoặc:

```text
masked tail
```

tùy target.

Không cần programmer tự viết tail loop.

---

# 71. Alignment peeling

Nếu alignment không rõ:

```text
prologue
→ aligned/vector loop
→ epilogue
```

có thể được compiler sinh tự động.

---

# 72. Loop dependence

Không vectorize nếu:

```ax
for i in 1..n {
    a[i] = a[i-1] + 1
}
```

có dependency thật.

Compiler không được hy sinh correctness để đạt SIMD.

---

# 73. Reduction dependence

Reduction có thể được vectorize nếu semantics cho phép:

```text
partial sums
→ horizontal reduction
```

và floating-point contract phù hợp.

---

# 74. Memory effects

Foreign call:

```ax
extern "C" fn foo(...)
```

mặc định có conservative memory effects.

Do đó loop chứa foreign call thường khó vectorize.

Nếu FFI contract cho biết:

```text
pure/read-only/noalias
```

thì compiler có thêm cơ hội.

---

# 75. Inline assembly

Inline asm không được tự động vectorize qua.

Compiler phải coi memory/clobber/register dependencies đúng contract.

Nếu programmer khai báo sai:

```text
unsafe
```

trách nhiệm thuộc system code.

---

# 76. SIMD and FFI

Không giả định:

```text
simd<f32,4>
```

có C ABI ổn định trên mọi platform.

FFI phải explicit representation/ABI.

Ví dụ:

```text
@repr(simd)
```

có thể là future explicit ABI contract.

---

# 77. Native vector intrinsics

System layer có thể expose:

```text
x86.avx2.add_f32
arm.neon.add_f32
riscv.v.add
```

nhưng đây là escape hatch.

Application code ưu tiên:

```text
axiom.simd
```

để giữ portability.

---

# 78. Backend strategy

Compiler vectorization pipeline:

```text
Verified MIR
      ↓
OptIR
      ↓
Loop Analysis
      ↓
Dependence Analysis
      ↓
Alias/Range Analysis
      ↓
Cost Model
      ↓
Vector Plan
      ↓
SIMD OptIR
      ↓
LIR
      ↓
Machine SIMD
```

---

# 79. Cost model

Không phải vectorization luôn nhanh hơn.

Compiler cần cân nhắc:

```text
vector width
instruction count
load/store cost
register pressure
mask cost
gather/scatter cost
code size
target microarchitecture
```

PGO có thể cải thiện quyết định.

---

# 80. Register pressure

SIMD width quá lớn có thể làm:

```text
register spills
```

và khiến code chậm hơn.

Do đó:

```text
AVX-512
```

không phải lúc nào cũng được chọn chỉ vì rộng hơn.

Compiler cost model quyết định.

---

# 81. SLP vectorization

Không chỉ loop vectorization.

Compiler cũng hỗ trợ:

```text
Straight-Line Code
    ↓
Superword Level Parallelism
```

Ví dụ:

```ax
let a = x0 + y0
let b = x1 + y1
let c = x2 + y2
let d = x3 + y3
```

có thể gom thành SIMD.

---

# 82. Interleaving

Compiler có thể tạo nhiều independent vector streams để tận dụng pipeline.

Đây là backend optimization.

Không thay đổi semantics.

---

# 83. Unrolling

Loop unrolling có thể kết hợp:

```text
unroll
+
vectorize
+
software pipelining
```

tùy target.

---

# 84. Matrix intrinsic mapping

Compiler có thể recognize:

```text
dot
matmul
convolution
```

và lower đến:

```text
FMA
AMX
NEON
SVE
RVV
GPU tensor cores
```

nếu library API có semantic contract phù hợp.

---

# 85. Tensor cores

Tensor core không cần trở thành Axiom Core feature.

GPU library có thể expose:

```text
matrix_multiply_accumulate
```

và backend mapping:

```text
CUDA-like tensor core
Metal
other accelerator
```

Axiom semantic model vẫn là:

```text
value
view
storage domain
kernel
```

---

# 86. CPU matrix accelerators

Tương tự:

```text
Intel AMX
ARM SME
future ISA
```

không cần thay đổi language.

Backend/system intrinsic layer mở rộng.

---

# 87. Dynamic CPU dispatch

Không implicit runtime dispatch trong Core.

Library có thể cung cấp:

```text
detect_cpu_features()
```

và function multiversioning.

Ví dụ conceptually:

```text
generic
AVX2
AVX512
NEON
```

Runtime chọn implementation.

ABI/compiler có thể hỗ trợ nhưng semantics vẫn một API.

---

# 88. Multiversioning

Có thể có compiler attribute tương lai:

```ax
@multiversion("avx2", "avx512")
fn process(...)
```

Compiler sinh:

```text
baseline version
feature-specific versions
dispatcher
```

Đây là optimization/system feature, không phải Core semantic requirement.

---

# 89. Tensor memory allocation

Tensor library không được mặc định:

```text
Tensor → heap allocation
```

Có thể:

```text
stack
caller-owned
arena
pool
DeviceBuffer
mapped
external
```

theo storage abstraction.

---

# 90. Temporary tensor elimination

Compiler nên tối ưu:

```ax
c = a + b
d = c * x
```

thành fused operation khi semantics cho phép:

```text
d = (a+b)*x
```

và tránh temporary allocation.

Đây là:

```text
fusion
+
scalar replacement
+
buffer reuse
```

---

# 91. Expression fusion

Lazy tensor APIs có thể tạo expression graph:

```text
a + b * c
```

sau đó compiler/library fuse.

Nhưng không được biến toàn Axiom thành lazy language.

Ordinary eager semantics vẫn là baseline.

---

# 92. Alias-safe tensor fusion

Fusion chỉ được phép nếu:

```text
read/write regions
```

không thay đổi observable result.

Compiler phải dùng capability/alias information.

Không được fusion chỉ vì syntax nhìn giống nhau.

---

# 93. GPU fusion

Cùng nguyên tắc:

```text
Tensor op
 ↓
kernel fusion
```

có thể:

```text
allocate once
load once
compute multiple operations
store once
```

nhưng chỉ khi semantics preserved.

Điều này kết nối trực tiếp `AGPU-69` và `AGPU-100`.

---

# 94. Tensor serialization

Tensor memory representation không đồng nghĩa wire format.

Không được:

```text
save(raw_memory)
```

và giả định file portable.

Serialization phải explicit:

```text
dtype
shape
stride/layout
endianness
version
```

---

# 95. Tensor FFI

FFI tensor không tự động truyền:

```text
Tensor<T>
```

qua C ABI.

C-facing API nên là:

```text
data pointer
rank
shape pointer
stride pointer
dtype
```

với explicit ownership/lifetime.

---

# 96. SIMD safety

SIMD không tạo một bypass safety.

Các invariant vẫn áp dụng:

```text
bounds
ownership
capability
alias
atomic
volatile
FFI
```

Ví dụ masked load không được dùng mask để che một pointer hoàn toàn invalid nếu API semantics không cho phép.

---

# 97. Unsafe SIMD

Unsafe có thể cung cấp:

```text
unchecked_load
unchecked_store
raw intrinsic
target-specific instruction
```

nhưng unsafe không tắt verifier toàn bộ.

---

# 98. Compiler fallback

Một mục tiêu quan trọng:

```text
portable Axiom code
      ↓
best available target implementation
```

Nếu target không có SIMD:

```text
scalar fallback
```

Nếu có:

```text
SIMD
```

Nếu GPU:

```text
GPU kernel
```

Không yêu cầu thay đổi source semantics.

---

# 99. Core boundary

Sau BOOTSTRAP-078, Core chỉ cần thêm một lượng nhỏ primitive semantic:

```text
simd<T,N>
simd_mask<N>
```

và compiler concepts:

```text
SimdElement
vector operations
target features
```

Còn:

```text
Tensor
Matrix
BLAS
NN
autodiff
quantization
sparse tensor
```

để library.

Đây là ranh giới rất quan trọng để Axiom không trở thành “AI language”.

---

# 100. Frozen invariants

## SIMD / Vector / Tensor — `ASIMD-20..100`

**ASIMD-20** — Scalar semantics are the semantic baseline for vectorization.

**ASIMD-21** — SIMD is not a separate source language.

**ASIMD-22** — SIMD vectors are value-semantic values.

**ASIMD-23** — `simd<T,N>` is distinct from `[T;N]`.

**ASIMD-24** — SIMD width is a semantic lane count, not necessarily a physical instruction width.

**ASIMD-25** — Backend may split or combine SIMD operations.

**ASIMD-26** — SIMD does not imply memory allocation.

**ASIMD-27** — SIMD does not imply heap storage.

**ASIMD-28** — SIMD values may remain entirely in registers.

**ASIMD-29** — SIMD element semantics follow Axiom scalar type semantics.

**ASIMD-30** — Element-wise arithmetic preserves lane correspondence.

**ASIMD-31** — SIMD comparisons produce mask semantics.

**ASIMD-32** — SIMD masks are distinct semantic values.

**ASIMD-33** — Mask representation is target-dependent.

**ASIMD-34** — Masked operations preserve ordinary capability rules.

**ASIMD-35** — Gather operations require valid element access.

**ASIMD-36** — Scatter operations require defined alias semantics.

**ASIMD-37** — Scatter aliasing cannot be assumed disjoint.

**ASIMD-38** — SIMD atomics are distinct from ordinary SIMD operations.

**ASIMD-39** — SIMD atomics reuse the Axiom memory model.

**ASIMD-40** — SIMD does not weaken ownership verification.

**ASIMD-41** — SIMD does not weaken capability verification.

**ASIMD-42** — SIMD does not weaken bounds verification.

**ASIMD-43** — SIMD does not weaken alias verification.

**ASIMD-44** — Portable SIMD is preferred over target-specific intrinsics.

**ASIMD-45** — Target-specific SIMD is isolated in system/compiler layers.

**ASIMD-46** — Target features require explicit contracts.

**ASIMD-47** — Unsupported target features cannot silently execute.

**ASIMD-48** — Runtime dispatch is not implicit Core behavior.

**ASIMD-49** — Multiversioning is an explicit optimization/system mechanism.

**ASIMD-50** — Auto-vectorization is a compiler optimization.

**ASIMD-51** — Safe scalar code may be automatically vectorized.

**ASIMD-52** — Proven disjoint capabilities may provide internal NoAlias facts.

**ASIMD-53** — Unknown aliasing cannot become NoAlias without proof.

**ASIMD-54** — Runtime alias versioning may be used when profitable.

**ASIMD-55** — Vectorization cannot change observable semantics.

**ASIMD-56** — Bounds checks may be eliminated only by proof.

**ASIMD-57** — Scalar remainder handling is compiler-generated when required.

**ASIMD-58** — Masked tails are compiler-generated when profitable.

**ASIMD-59** — Alignment peeling may be compiler-generated.

**ASIMD-60** — SIMD alignment is distinct from semantic vector type identity.

**ASIMD-61** — SIMD ABI is target-specific.

**ASIMD-62** — SIMD ABI compatibility does not imply semantic type compatibility.

**ASIMD-63** — SIMD FFI requires explicit ABI/representation contracts.

**ASIMD-64** — SIMD floating-point operations follow Axiom floating semantics.

**ASIMD-65** — Floating-point reassociation requires an explicit semantic allowance.

**ASIMD-66** — Fast-math behavior is not the default semantic model.

**ASIMD-67** — SIMD integer overflow follows Axiom overflow semantics.

**ASIMD-68** — Saturating operations have explicit saturating semantics.

**ASIMD-69** — Reduction order is semantically relevant where numeric semantics require it.

**ASIMD-70** — Auto-vectorization must respect reduction semantics.

**ASIMD-71** — Matrix is not a Core primitive type.

**ASIMD-72** — Tensor is not a Core primitive type.

**ASIMD-73** — Tensor abstractions belong to library layers.

**ASIMD-74** — Tensor views use one underlying data region plus shape/stride metadata.

**ASIMD-75** — Nested views are not the default tensor representation.

**ASIMD-76** — Tensor ownership is explicit.

**ASIMD-77** — Tensor views are non-owning capabilities.

**ASIMD-78** — Mutable tensor views provide exclusive write capability.

**ASIMD-79** — Tensor aliasing follows ordinary capability rules.

**ASIMD-80** — Tensor shape does not prove non-aliasing.

**ASIMD-81** — Tensor stride is explicit semantic metadata.

**ASIMD-82** — Strided views may be non-contiguous.

**ASIMD-83** — Broadcast read views may alias the same physical element.

**ASIMD-84** — Mutable broadcast views require explicit safe semantics.

**ASIMD-85** — Tensor storage domain is explicit.

**ASIMD-86** — Host and device tensor storage are not implicitly interchangeable.

**ASIMD-87** — CPU/GPU transfer is explicit.

**ASIMD-88** — Zero-copy is an optimization/storage property, not a semantic assumption.

**ASIMD-89** — Tensor operations may specialize by shape, dtype and target.

**ASIMD-90** — Generic tensor specialization preserves semantic verification.

**ASIMD-91** — Tensor fusion is legal only when observable semantics are preserved.

**ASIMD-92** — Kernel fusion follows the same semantic rule.

**ASIMD-93** — Temporary tensor allocation may be eliminated when unobservable.

**ASIMD-94** — Iterator pipelines may be fused and vectorized.

**ASIMD-95** — Parallel vector/tensor execution requires Send/Share and capability correctness.

**ASIMD-96** — SIMD/GPU optimization cannot manufacture safety facts.

**ASIMD-97** — Compiler vectorization decisions are explainable and machine-readable.

**ASIMD-98** — Portable code may fall back to scalar execution.

**ASIMD-99** — Target optimization must not require source-level algorithm duplication.

**ASIMD-100** — SIMD, matrix and tensor optimization preserve Axiom ownership, capability, memory, concurrency, ABI, GPU and numeric semantics.

---

# Kiến trúc sau khi freeze

Axiom hiện đã có một đường rất đẹp từ code bình thường đến phần cứng:

```text
                  Axiom Source
                       │
             ┌─────────┴─────────┐
             │                   │
          Scalar              Explicit SIMD
             │                   │
             └─────────┬─────────┘
                       ↓
                  Verified MIR
                       ↓
                     OptIR
                       │
          ┌────────────┼─────────────┐
          ↓            ↓             ↓
      Scalar       SIMD CPU      Tensor/GPU
          │            │             │
          └────────────┼─────────────┘
                       ↓
                    Axiom LIR
                       ↓
                 Machine IR
                       ↓
          ┌────────────┼────────────┐
          ↓            ↓            ↓
        x86          ARM          RISC-V
       AVX2/512      NEON/SVE        RVV
```

Điểm tôi đánh giá **quan trọng nhất** ở thiết kế này là Axiom không buộc người dùng phải chọn giữa:

> “ngôn ngữ dễ viết” **hay** “ngôn ngữ có khả năng đạt hiệu năng native”.

Một đoạn code an toàn, thông thường:

```ax
for i in 0..n {
    out[i] = a[i] * scale + b[i]
}
```

có thể đi qua:

```text
bounds proof
→ alias proof
→ loop analysis
→ vectorization
→ FMA
→ AVX2/AVX512/NEON/SVE/RVV
```

mà **source vẫn chỉ là Axiom bình thường**.

Đó chính là hướng phù hợp với mục tiêu ban đầu của Axiom: **compiler phức tạp ở bên trong, nhưng complexity đó không được đẩy lên programmer.**

### Bước tiếp theo

**BOOTSTRAP-079 — Axiom Numeric Model, Math, Floating Point, Big Integer, Decimal & Precision Semantics**

Phần này sẽ giải quyết một vấn đề còn quan trọng hơn SIMD: **chính xác về số học** — integer overflow, `f16/f32/f64`, `bf16`, FP environment, NaN, rounding, deterministic math, decimal/fixed-point, big integer, complex number, arbitrary precision và cách compiler vừa đảm bảo semantics vừa tối ưu xuống hardware.