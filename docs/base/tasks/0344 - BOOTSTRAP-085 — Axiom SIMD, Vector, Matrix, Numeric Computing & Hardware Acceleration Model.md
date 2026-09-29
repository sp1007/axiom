# BOOTSTRAP-085 — Axiom SIMD, Vector, Matrix, Numeric Computing & Hardware Acceleration Model

**Trạng thái: FROZEN**

Mục tiêu của phần này:

> Axiom phải có khả năng khai thác SIMD/vector hardware mạnh như C/C++ intrinsics, nhưng programmer không phải lập trình bằng một đống intrinsic CPU-specific.

Thiết kế sẽ chia thành:

```text
Axiom semantic vector
        ↓
Portable Vector IR
        ↓
Target Vector IR
        ↓
AVX / AVX2 / AVX-512
NEON / SVE
RVV
GPU
```

Compiler chịu trách nhiệm mapping xuống phần cứng.

---

# 1. Không biến SIMD thành một primitive CPU-specific

Không muốn API kiểu:

```text
_mm256_add_ps(...)
_mm256_mul_ps(...)
_mm512_fmadd_ps(...)
```

trở thành cách lập trình SIMD chính.

Thay vào đó:

```ax
let a: f32x8 = ...
let b: f32x8 = ...

let c = a + b
```

Compiler tự chọn instruction phù hợp.

---

# 2. Vector là semantic type

Axiom phân biệt:

```text
scalar
vector
matrix
tensor
```

Ví dụ:

```text
f32
f32x4
f32x8
f32x16
```

`f32x8` mang semantic:

> 8 lane độc lập của `f32`.

Không nhất thiết có nghĩa nó luôn nằm trong một thanh ghi AVX.

---

# 3. Vector width không đồng nghĩa hardware width

Ví dụ:

```ax
f32x16
```

trên CPU không có register 512-bit có thể được compiler hạ thành:

```text
2 × 256-bit
```

hoặc:

```text
4 × 128-bit
```

nếu semantics cho phép.

---

# 4. Vector type không phải array

Đây là distinction quan trọng:

```text
[T; N]
```

là aggregate/array.

Trong khi:

```text
f32xN
```

là vector computational type.

Array:

```text
a[i]
```

có semantic memory access.

Vector:

```text
v[i]
```

có thể được compiler hạ thành lane operation.

Không được đánh đồng hai loại.

---

# 5. Vector lanes có fixed shape

Core v1 nên giới hạn vector width compile-time:

```text
i8x16
i16x8
i32x4
i64x2

f32x4
f32x8
f64x2
f64x4
```

Compiler có thể hỗ trợ nhiều width hơn tùy target.

---

# 6. Không giới hạn API vào một số width cố định

Library nên expose generic concept:

```text
Vector<T, N>
```

nhưng backend quyết định hardware mapping.

Ví dụ:

```text
Vector<f32, 8>
```

có thể map:

```text
AVX2 register
```

trên x86.

Hoặc:

```text
2 × NEON register
```

trên ARM.

---

# 7. Portable SIMD là abstraction chính

Axiom programmer nên viết:

```ax
fn add<T>(a: Vector<T, 8>, b: Vector<T, 8>) -> Vector<T, 8> {
    a + b
}
```

thay vì:

```text
#ifdef AVX2
...
#ifdef NEON
...
```

Compiler target specialization xử lý backend.

---

# 8. Nhưng phải có native SIMD escape hatch

Portable abstraction không được khóa programmer khỏi hardware.

System layer có thể expose:

```text
x86.avx2
x86.avx512
arm.neon
arm.sve
riscv.vector
```

cho các trường hợp cần instruction cụ thể.

Nhưng đây là **system-level API**.

---

# 9. Target feature

Đã có:

```text
@target_feature
```

Nó phải trở thành semantic contract rõ ràng.

Ví dụ conceptual:

```ax
@target_feature(avx2)
fn process(...) {
    ...
}
```

Compiler được phép sinh AVX2.

---

# 10. Không được gọi function target-specific sai CPU

Nếu:

```text
process()
```

yêu cầu AVX2 nhưng CPU không hỗ trợ, chương trình không được âm thầm chạy instruction không hợp lệ.

Có hai cách:

```text
compile target guarantees AVX2
```

hoặc:

```text
runtime feature dispatch
```

---

# 11. Runtime CPU dispatch

Library có thể cung cấp:

```ax
if cpu_supports(AVX2) {
    process_avx2(...)
} else {
    process_scalar(...)
}
```

Nhưng compiler có thể tối ưu pattern này thành dispatch table.

---

# 12. Không để runtime feature detection lan khắp code

Programmer nên viết:

```text
process()
```

một lần.

Compiler/library có thể tổ chức:

```text
process.scalar
process.avx2
process.avx512
process.neon
```

và dispatch ở boundary.

---

# 13. Comptime target specialization

Nếu target đã biết:

```text
comptime {
    target_features()
}
```

generator có thể chọn implementation.

Nhưng target facts phải là compile-time input.

---

# 14. SIMD operations

Core vector operations cần semantic definitions cho:

```text
add
sub
mul
div
neg
abs
min
max
sqrt
fma
```

và bitwise:

```text
and
or
xor
not
shift
```

---

# 15. Comparison

Vector comparison không trả về `bool`.

Ví dụ:

```text
f32x8 == f32x8
```

→ mask:

```text
mask8
```

---

# 16. Mask là type riêng

Ví dụ:

```text
mask8
```

có 8 logical lanes.

Không nên biểu diễn semantic mask đơn giản như:

```text
boolx8
```

nếu điều đó làm mất distinction giữa:

```text
logical vector
```

và:

```text
hardware predicate/mask
```

---

# 17. Mask operations

Cần:

```text
select(mask, a, b)
any(mask)
all(mask)
none(mask)
count(mask)
```

Ví dụ:

```ax
let m = a < b
let x = select(m, a, b)
```

Compiler có thể sinh:

```text
min instruction
```

hoặc compare + blend.

---

# 18. Branchless code

Mask cho phép:

```ax
let result = select(x > 0, x, -x)
```

Compiler có thể tạo branchless instruction.

Nhưng semantics không bắt buộc branchless.

---

# 19. Compiler được phép chọn branch

Nếu branch nhanh hơn:

```text
if mask...
```

compiler có thể dùng branch.

Programmer viết semantic operation, không viết instruction schedule.

---

# 20. Horizontal operations

Cần hỗ trợ:

```text
reduce_add
reduce_mul
reduce_min
reduce_max
reduce_and
reduce_or
```

Ví dụ:

```ax
sum(v)
```

Compiler chọn tree reduction phù hợp.

---

# 21. Floating-point reduction

Đây là nơi phải cực kỳ cẩn thận.

Floating point:

```text
(a + b) + c
```

không luôn bằng:

```text
a + (b + c)
```

Do đó compiler **không được tự ý reassociate** nếu semantics hiện tại không cho phép.

---

# 22. Fast-math phải explicit

Không mặc định:

```text
fast math
```

Một profile/attribute riêng có thể cho phép:

```text
@fast_math
```

với semantic contract được định nghĩa rõ.

Không được để optimizer tự phá floating-point semantics chỉ vì vectorization.

---

# 23. FMA

Fused multiply-add:

```text
a * b + c
```

không mặc định được biến thành:

```text
fma(a,b,c)
```

nếu kết quả rounding observable khác semantics yêu cầu.

Nếu compiler semantic model cho phép contraction, nó phải được định nghĩa rõ.

---

# 24. Integer overflow

Vector integer phải kế thừa semantic arithmetic model của Axiom:

```text
checked
wrapping
saturating
```

Không tạo một bộ luật khác cho SIMD.

---

# 25. Saturating arithmetic

Đặc biệt hữu ích cho:

```text
u8 image processing
audio
DSP
neural network quantization
```

Ví dụ semantic:

```text
sat_add(a, b)
sat_sub(a, b)
```

Compiler map xuống instruction saturation nếu CPU hỗ trợ.

---

# 26. Widening/narrowing

Các operation:

```text
widen
narrow
pack
unpack
```

phải explicit.

Không tự động biến:

```text
i16x8 → i8x16
```

nếu có mất dữ liệu.

---

# 27. Vector cast vs bitcast

Giống scalar:

```text
cast
```

thay đổi semantic value.

```text
bitcast
```

giữ bit pattern.

Compiler phải kiểm tra:

```text
size
alignment
valid representation
```

---

# 28. Gather/scatter

SIMD memory access cần semantic:

```text
gather
scatter
```

nhưng không phải mọi target đều hỗ trợ hiệu quả.

Portable API có thể tồn tại:

```ax
gather(base, indices)
scatter(base, indices, values)
```

Compiler fallback có thể scalarize.

---

# 29. Scatter + aliasing

Đây là điểm liên quan trực tiếp capability model.

Ví dụ:

```text
scatter(a, [1, 1], values)
```

có duplicate destination.

Semantics phải xác định rõ.

Không cho compiler giả định các lanes luôn disjoint.

---

# 30. Vector memory operations

Cần:

```text
load
store
masked_load
masked_store
gather
scatter
```

nhưng programmer bình thường nên dùng:

```ax
view[i..]
```

hoặc vectorized loop.

Compiler tự vectorize khi an toàn.

---

# 31. Alignment không bắt buộc cho mọi vector

Một vector có thể được load unaligned nếu target hỗ trợ.

Không biến:

```text
Vector<T,N>
```

thành:

```text
requires N-byte alignment
```

một cách mặc định.

---

# 32. Explicit aligned storage

Khi cần:

```text
@align(64)
struct ...
```

hoặc aligned allocation/storage abstraction.

Alignment là storage/representation contract, không phải intrinsic property của mọi vector operation.

---

# 33. SIMD và view

Ví dụ:

```ax
fn add_arrays(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
) {
    ...
}
```

Compiler có thể vectorize nếu chứng minh:

```text
a
b
out
```

không alias conflicting.

Đây chính là lợi thế của capability model Axiom.

---

# 34. Không cần `restrict`

Axiom không cần programmer viết:

```text
restrict
```

trong code thông thường.

Verifier đã có:

```text
view
mut_view
region analysis
```

và optimizer nhận:

```text
NoAlias
```

khi compiler chứng minh được.

---

# 35. Nhưng unknown alias vẫn phải conservative

Nếu compiler không chứng minh được:

```text
a != out
```

thì không được tự giả định.

Có thể:

```text
reject API
scalarize
runtime alias check
```

tùy abstraction.

---

# 36. Runtime alias check

Compiler có thể tạo:

```text
if regions_disjoint {
    vectorized_path
} else {
    scalar_path
}
```

nếu điều này bảo toàn semantics và đáng giá.

---

# 37. Loop auto-vectorization

Ví dụ:

```ax
for i in 0..n {
    out[i] = a[i] + b[i]
}
```

không cần programmer viết SIMD.

Compiler pipeline:

```text
MIR
 ↓
Loop analysis
 ↓
Range analysis
 ↓
Alias analysis
 ↓
Vectorization
 ↓
Vector IR
```

---

# 38. Vectorization legality

Compiler phải chứng minh:

```text
no illegal dependencies
no conflicting alias
valid bounds
compatible arithmetic semantics
supported target
```

---

# 39. Vectorization profitability

Ngay cả khi vectorization hợp lệ, compiler không nhất thiết vectorize.

Nó đánh giá:

```text
trip count
alignment
instruction cost
remainder cost
branch cost
target width
register pressure
code size
```

---

# 40. Scalar fallback

Loop có remainder:

```text
N = 19
width = 8
```

có thể:

```text
8 + 8 + 3 scalar
```

hoặc masked tail.

Compiler chọn.

---

# 41. Vectorization không thay đổi observable semantics

Đặc biệt với:

```text
volatile
atomic
IO
floating-point
exceptions/traps
```

Compiler phải tuân semantic constraints.

---

# 42. Atomic SIMD

Không được coi:

```text
Vector<Atomic<T>, N>
```

giống ordinary SIMD.

Atomic semantics vẫn phải giữ:

```text
atomicity
ordering
scope
```

Có thể có target-specific atomic vector instructions nhưng đó là specialization.

---

# 43. Volatile SIMD

Volatile operations phải giữ:

```text
observable access
```

Không được vectorize tùy tiện nếu thay đổi số lượng/order observable volatile accesses.

---

# 44. Matrix không phải Core primitive bắt buộc

Axiom nên có:

```text
Vector
```

ở mức compiler/library thấp.

Nhưng:

```text
Matrix
Tensor
```

nên là library abstraction.

---

# 45. Matrix abstraction

Ví dụ:

```text
Matrix<T, Rows, Cols>
```

có thể biểu diễn:

```text
view<T>
+
shape
+
stride/layout
```

hoặc owned storage.

Không cần tạo matrix primitive mới trong language core.

---

# 46. Tensor

Tensor nên tương tự:

```text
Tensor<T, Rank>
TensorView<T, Rank>
```

với metadata:

```text
data
shape
stride
layout
```

---

# 47. Không dùng nested view

Không nên biến tensor thành:

```text
view<view<view<T>>>
```

Điều này tạo nhiều lớp capability/indirection không cần thiết.

Thay vào đó:

```text
TensorView<T, Rank>
    data: view<T>
    shape
    stride
```

---

# 48. Tensor ownership

Có thể:

```text
Tensor<T>
```

owned storage.

Hoặc:

```text
TensorView<T, Rank>
```

non-owning.

Compiler áp dụng capability/lifetime model hiện tại.

---

# 49. Contiguous tensor

Compiler có thể biết:

```text
contiguous
```

từ type/metadata hoặc prove tại compile time.

Khi đó có thể hạ thành linear vectorized loop.

---

# 50. Strided tensor

Ví dụ transpose:

```text
TensorView
stride != contiguous
```

Compiler không được giả định contiguous.

Library có thể cung cấp specialization cho common layouts.

---

# 51. Matrix multiplication

Không cần hard-code:

```text
matmul
```

vào language.

Library:

```text
matmul(A, B)
```

có thể dispatch:

```text
scalar
SIMD
BLAS
GPU
specialized kernel
```

theo target/runtime policy.

---

# 52. Hardware acceleration abstraction

Axiom nên có tầng:

```text
Scalar
SIMD
CPU specialized
GPU
Accelerator
```

nhưng semantic model thống nhất.

---

# 53. Không biến GPU thành SIMD

GPU có:

```text
execution domain
storage domain
synchronization
kernel launch
```

khác CPU SIMD.

Do đó:

```text
Vector<T,N>
```

không đồng nghĩa GPU vector.

---

# 54. CPU/GPU shared high-level API

Library có thể:

```text
Tensor
```

và chọn backend:

```text
CPU
GPU
```

nhưng semantics về ownership vẫn giữ.

---

# 55. Backend selection

Có thể có:

```text
TensorBackend
```

library abstraction.

Core không cần biết:

```text
CUDA
ROCm
Metal
DirectML
```

là gì.

System layer mới cung cấp backend-specific API.

---

# 56. SIMD target families

Axiom backend nên có target feature database:

```text
x86:
  SSE2
  SSE4.2
  AVX
  AVX2
  AVX512...

ARM:
  NEON
  SVE
  SVE2

RISC-V:
  V
  Zve...
```

Compiler database quản lý compatibility.

---

# 57. Feature dependency

Ví dụ:

```text
AVX2
```

có dependency trên các feature ISA cần thiết.

Compiler không để target configuration tạo instruction set không hợp lệ.

---

# 58. `@target_feature` inheritance

Nếu function A gọi function B:

```text
B requires AVX2
```

compiler phải kiểm tra call context.

Không cho một function generic target-neutral gọi code AVX2 một cách vô điều kiện.

---

# 59. Feature-aware specialization

Generic:

```ax
fn process<T>(x: T) ...
```

có thể có target-specialized implementation.

Compiler có thể chọn:

```text
scalar implementation
SIMD implementation
```

mà không thay đổi public API.

---

# 60. Dispatch ABI

Nếu runtime dispatch cần function pointers:

```text
scalar_fn
avx2_fn
avx512_fn
```

thì function pointer ABI phải tương thích.

Compiler không được giả định mọi target-specialized function có cùng ABI nếu contract không đảm bảo.

---

# 61. CPU detection

CPU detection nên nằm ở:

```text
System/Platform Library
```

Compiler có thể optimize static target.

Không đưa toàn bộ CPUID/OS feature detection vào Core.

---

# 62. Compile-time target facts

Compiler biết:

```text
architecture
OS
ABI
enabled features
vector widths
endianness
alignment
```

và expose qua compile-time reflection/config.

---

# 63. Numeric types

Core hiện có:

```text
i8..i64
u8..u64
f32
f64
```

SIMD không nên tự tạo:

```text
half
bfloat16
fp8
```

vào Core ngay.

Những type này có thể nằm trong numeric library/system layer.

---

# 64. Nhưng compiler phải có khả năng mở rộng

Compiler backend có thể hỗ trợ:

```text
f16
bf16
fp8
i128
```

khi library/type system bổ sung.

Không thiết kế SIMD engine chỉ cho `f32/f64`.

---

# 65. Quantized computing

AI workloads cần:

```text
i8
u8
i16
bf16
f16
```

Library có thể định nghĩa:

```text
Quantized<T, Scale>
```

hoặc specialized numeric types.

Compiler có thể lower xuống SIMD instructions.

---

# 66. No hidden numeric conversion

Ví dụ:

```text
f32x8 + i32x8
```

không tự động chuyển kiểu.

Phải explicit.

Điều này giữ consistency với scalar type system.

---

# 67. Vector generic traits

Operators có thể dùng trait:

```text
Add
Sub
Mul
Div
```

nhưng compiler nên recognize các vector operations để tránh abstraction overhead.

---

# 68. Trait abstraction vẫn zero-cost

Ví dụ:

```ax
fn add<T: Add>(a: T, b: T) -> T
```

với concrete `f32x8`.

Monomorphization:

```text
T = f32x8
```

→ vector operation.

Không cần dynamic dispatch.

---

# 69. `dyn` vector operation

Có thể tồn tại nhưng thường không tối ưu cho hot numeric loop.

Axiom không cấm.

Programmer chọn dynamic abstraction khi thực sự cần.

---

# 70. SIMD and closure

Một closure:

```ax
map(|x| x * 2)
```

có thể được compiler vectorize sau inline.

Không cần API riêng:

```text
simd_map(...)
```

cho mọi trường hợp.

---

# 71. Iterator + SIMD

Iterator abstraction:

```ax
a.iter().map(...).collect()
```

có thể được optimizer fuse và vectorize nếu semantics cho phép.

Đây là một mục tiêu zero-cost abstraction quan trọng.

---

# 72. Iterator không đảm bảo SIMD

Không nên hứa:

```text
iterator = SIMD
```

Compiler chỉ vectorize khi legality + profitability đạt yêu cầu.

---

# 73. Explicit vector loop

Khi programmer muốn kiểm soát:

```ax
for v in vector_chunks(a, 8) {
    ...
}
```

library có thể cung cấp.

Đây vẫn là portable abstraction.

---

# 74. Portable SIMD fallback

Nếu target không có vector hardware:

```text
f32x8
```

có thể được scalarized.

Semantics giữ nguyên.

Performance giảm, nhưng program vẫn đúng.

---

# 75. Vector ABI

Vector type không nên có ABI ổn định mặc định.

ABI classification target-specific.

Ví dụ:

```text
f32x4
```

có thể truyền:

```text
register
multiple registers
stack
```

tùy target ABI.

---

# 76. FFI SIMD

Không tự động cho phép:

```text
extern "C" fn foo(v: f32x8)
```

trừ khi target C ABI contract xác định representation.

Nếu cần:

```text
@repr(...)
```

hoặc system-specific vector ABI.

---

# 77. Vector layout

Semantic vector:

```text
f32x8
```

có logical lane order:

```text
lane 0 ... lane 7
```

Nhưng physical register encoding vẫn backend-specific.

---

# 78. Endianness

Lane order không được nhầm với byte endianness.

Memory representation:

```text
store vector
```

phải có defined lane/byte semantics.

Serialization vẫn là abstraction riêng.

---

# 79. Shuffle

SIMD cần:

```text
shuffle
permute
swizzle
extract
insert
broadcast
```

Portable operations nên có semantic definition.

Compiler chọn instruction sequence.

---

# 80. Variable shuffle

Một số CPU có:

```text
variable permute
```

Portable API có thể hỗ trợ.

Target không có → compiler fallback.

---

# 81. Masked operations

Ví dụ:

```text
masked_load(mask, ptr)
masked_store(mask, ptr, values)
```

Semantics phải quy định rõ lane không active:

```text
not accessed
```

để optimizer không biến nó thành full memory access.

---

# 82. Fault suppression

Masked load đặc biệt quan trọng.

Nếu mask lane = false:

```text
memory location of that lane
```

không được truy cập semantically.

Điều này cho phép safe vectorized tail processing.

---

# 83. Bounds checking + SIMD

Compiler có thể chứng minh vector load nằm trong range.

Nếu không:

```text
masked operation
```

hoặc scalar remainder.

Không tự biến out-of-bounds thành undefined behavior trong safe code.

---

# 84. Unsafe unchecked vector memory

System layer có thể cung cấp:

```text
unsafe load_unchecked(...)
```

nhưng semantics giống unchecked array access:

> programmer chịu trách nhiệm.

---

# 85. Prefetch

Prefetch không nên là ordinary semantic memory read.

System intrinsic:

```text
prefetch(ptr)
```

có thể là optimization hint.

Nếu CPU không hỗ trợ → no-op.

---

# 86. Cache hints

Tương tự:

```text
cache_hint
streaming_store
```

system/compiler intrinsics.

Không được thay đổi language memory semantics.

---

# 87. Non-temporal operations

Có thể expose:

```text
store_streaming
```

nhưng đây là target/system abstraction.

Không biến thành semantic property của `mut_view`.

---

# 88. SIMD + volatile

Không cho:

```text
vectorized volatile IO
```

trừ khi API định nghĩa rõ exact access semantics.

MMIO cần system-level abstraction.

---

# 89. Vector atomic

Nếu target có vector atomics:

```text
AtomicVector<T,N>
```

có thể là library/system abstraction.

Không thay đổi:

```text
Atomic<T>
```

semantic contract.

---

# 90. Register pressure

Vectorization có thể làm tăng register pressure.

Optimizer phải cân nhắc:

```text
vector width
unroll factor
register pressure
spill cost
```

Không phải width càng lớn càng tốt.

---

# 91. Vector width selection

Compiler có thể chọn:

```text
AVX2 256-bit
```

thay vì:

```text
AVX512 512-bit
```

nếu profitability model cho rằng tốt hơn.

Semantics không thay đổi.

---

# 92. Code size

AVX-512 specialization có thể làm binary lớn hơn.

Axiom binary-size optimizer có thể chọn:

```text
single generic implementation
```

hoặc:

```text
multiversioning
```

tùy build profile.

---

# 93. Multiversioning

Compiler/library có thể tạo:

```text
foo.scalar
foo.avx2
foo.avx512
```

và một dispatcher.

Đây là optimization/ABI mechanism, không phải semantic feature của function.

---

# 94. LTO + SIMD

LTO có thể phát hiện:

```text
caller knows target feature
```

và eliminate dispatch.

Ví dụ:

```text
main compiled for AVX2
```

→ direct call AVX2 version.

---

# 95. PGO + SIMD

PGO có thể quyết định:

```text
hot loop → vectorize
cold loop → scalar
```

nhưng PGO không được thay đổi semantics.

---

# 96. Matrix/tensor compiler optimization

OptIR có thể bổ sung:

```text
ShapeInfo
StrideInfo
LayoutInfo
VectorWidthInfo
```

nhưng đây là optimization facts.

Không cần đưa toàn bộ tensor theorem proving vào language core.

---

# 97. Future accelerator abstraction

Kiến trúc phải mở cho:

```text
CPU
GPU
NPU
DSP
FPGA
AI accelerator
```

nhưng không hard-code chúng vào Core.

Mỗi accelerator là:

```text
execution/storage backend
```

với semantic contract riêng.

---

# 98. Final architecture

```text
                 Axiom Numeric Code
                         │
          ┌──────────────┼──────────────┐
          │              │              │
       Scalar         Vector         Tensor
          │              │              │
          │       Portable SIMD      Library
          │              │              │
          └──────────────┼──────────────┘
                         ▼
                      OptIR
                         │
              ┌──────────┴──────────┐
              │                     │
        Auto-vectorize       Explicit vector
              │                     │
              └──────────┬──────────┘
                         ▼
                  Target Vector IR
                         │
          ┌──────────────┼───────────────┐
          ▼              ▼               ▼
        x86            ARM             RISC-V
      AVX/AVX2       NEON/SVE            V
          │              │               │
          └──────────────┼───────────────┘
                         ▼
                   Machine IR
```

GPU đi qua backend riêng:

```text
Verified MIR
     ↓
GPU lowering
     ↓
GPU Machine IR
```

không giả vờ GPU là CPU SIMD.

---

# 99. Những gì Axiom **không** làm

Axiom v1 không:

- bắt programmer viết intrinsic CPU-specific trong code thông thường;
- mặc định bật fast-math;
- mặc định reassociate floating point;
- giả định mọi vector width đều tương ứng một hardware register;
- giả định array = SIMD vector;
- giả định `view` luôn contiguous tensor;
- giả định aliasing disjoint khi chưa chứng minh;
- biến atomic/volatile thành SIMD memory;
- đưa matrix/tensor vào language Core;
- yêu cầu GPU để dùng vector;
- yêu cầu runtime SIMD library khổng lồ.

---

# 100. Frozen Invariants — `ASIMD-20..100`

**ASIMD-20** — Vector types have explicit semantic lane structure.

**ASIMD-21** — Vector types are distinct from arrays.

**ASIMD-22** — Vector width does not imply a particular physical register width.

**ASIMD-23** — Compiler may split a logical vector across multiple hardware registers.

**ASIMD-24** — Compiler may scalarize a vector when required by target or profitability.

**ASIMD-25** — Portable SIMD is the primary programmer-facing SIMD abstraction.

**ASIMD-26** — Target-specific SIMD intrinsics belong to system/compiler layers.

**ASIMD-27** — Native SIMD escape hatches must preserve Axiom semantic contracts.

**ASIMD-28** — Vector operators preserve ordinary Axiom type semantics.

**ASIMD-29** — Vector arithmetic does not introduce an independent numeric semantics model.

**ASIMD-30** — Vector integer overflow follows Axiom integer overflow semantics.

**ASIMD-31** — Checked, wrapping and saturating vector arithmetic are semantically distinct.

**ASIMD-32** — Vector comparisons produce mask semantics.

**ASIMD-33** — Masks are distinct semantic values from ordinary scalar booleans.

**ASIMD-34** — Masked inactive lanes do not perform semantic memory accesses.

**ASIMD-35** — Gather and scatter preserve explicit memory access semantics.

**ASIMD-36** — Scatter operations may not assume lane destinations are disjoint.

**ASIMD-37** — Vector casts and vector bitcasts are distinct.

**ASIMD-38** — Bitcasts require valid size/alignment/representation conditions.

**ASIMD-39** — Horizontal reductions have explicitly defined ordering semantics.

**ASIMD-40** — Floating-point reductions may not arbitrarily reassociate operations.

**ASIMD-41** — Fast-math or relaxed floating-point transformations require explicit semantic permission.

**ASIMD-42** — FMA contraction must preserve the defined floating-point semantic contract.

**ASIMD-43** — Vectorization must preserve observable floating-point behavior under the active profile.

**ASIMD-44** — SIMD alignment is not implicitly a universal storage requirement.

**ASIMD-45** — Explicit alignment is a representation/storage contract.

**ASIMD-46** — SIMD loads/stores may use unaligned access when target semantics permit.

**ASIMD-47** — Unsafe unchecked SIMD memory access remains explicitly unsafe.

**ASIMD-48** — SIMD optimization may consume compiler-proven capability facts.

**ASIMD-49** — Proven disjoint regions may enable internal no-alias optimization.

**ASIMD-50** — Unknown aliasing cannot be treated as disjoint.

**ASIMD-51** — Compiler may use runtime alias checks when semantics and profitability permit.

**ASIMD-52** — Auto-vectorization requires legality analysis.

**ASIMD-53** — Auto-vectorization also requires profitability analysis.

**ASIMD-54** — Vectorization is an optimization unless explicitly required by a semantic API.

**ASIMD-55** — Scalar fallback is permitted for unsupported targets or remainder regions.

**ASIMD-56** — Vectorization cannot change ownership semantics.

**ASIMD-57** — Vectorization cannot change capability validity.

**ASIMD-58** — Vectorization cannot change synchronization semantics.

**ASIMD-59** — Atomic accesses cannot be silently converted into ordinary vector accesses.

**ASIMD-60** — Volatile accesses cannot be arbitrarily vectorized.

**ASIMD-61** — Atomic and volatile semantics remain distinct from SIMD semantics.

**ASIMD-62** — Vector types have target-dependent default ABI classification.

**ASIMD-63** — Vector ABI representation is not stable without an explicit representation/ABI contract.

**ASIMD-64** — FFI vector passing requires an applicable ABI contract.

**ASIMD-65** — Vector lane order is distinct from byte endianness.

**ASIMD-66** — Shuffle and permutation operations have explicit lane semantics.

**ASIMD-67** — Compiler may lower portable shuffle operations to target-specific instructions or sequences.

**ASIMD-68** — Prefetch is an optimization/system operation, not an ordinary semantic load.

**ASIMD-69** — Cache hints do not alter ordinary Axiom memory semantics.

**ASIMD-70** — Non-temporal memory operations require explicit system/compiler semantics.

**ASIMD-71** — Target feature requirements are explicit compiler contracts.

**ASIMD-72** — Code requiring unavailable target features cannot execute through an incompatible target path.

**ASIMD-73** — Runtime CPU dispatch is a library/compiler mechanism.

**ASIMD-74** — Target multiversioning must preserve a common semantic contract.

**ASIMD-75** — Target-specialized implementations may be selected at compile time or runtime.

**ASIMD-76** — LTO may eliminate unnecessary target dispatch when target facts are known.

**ASIMD-77** — PGO may influence vectorization and specialization but not semantics.

**ASIMD-78** — SIMD specialization must preserve ABI contracts at externally visible boundaries.

**ASIMD-79** — Vector generic abstractions may be fully monomorphized and optimized away.

**ASIMD-80** — Trait-based vector operations must not impose mandatory dynamic dispatch.

**ASIMD-81** — Closure and iterator abstractions may be vectorized after semantic verification.

**ASIMD-82** — Iterator abstraction does not itself guarantee vectorization.

**ASIMD-83** — Matrix abstractions belong primarily to library layers.

**ASIMD-84** — Tensor abstractions belong primarily to library layers.

**ASIMD-85** — Tensor views may combine a contiguous data view with shape and stride metadata.

**ASIMD-86** — Tensor semantics must not require nested view types.

**ASIMD-87** — Contiguous tensor layout must be explicitly known or proven before linearization.

**ASIMD-88** — Strided tensor access cannot be assumed contiguous.

**ASIMD-89** — Matrix/tensor ownership follows Axiom ownership semantics.

**ASIMD-90** — Matrix/tensor views follow Axiom capability semantics.

**ASIMD-91** — CPU SIMD and GPU execution are distinct execution mechanisms.

**ASIMD-92** — GPU vectorization does not redefine CPU SIMD semantics.

**ASIMD-93** — Numeric acceleration APIs may target CPU, GPU or other accelerators without changing core ownership semantics.

**ASIMD-94** — Accelerator-specific APIs belong outside the minimal language core.

**ASIMD-95** — Extended numeric types may be introduced through library/compiler integration without redesigning SIMD semantics.

**ASIMD-96** — Quantized numeric computation may use SIMD-specialized library types.

**ASIMD-97** — Compiler target databases must model instruction-set feature compatibility.

**ASIMD-98** — Optimization may select different vector widths without changing program semantics.

**ASIMD-99** — SIMD abstractions should disappear into native instructions whenever observable semantics permit.

**ASIMD-100** — Axiom SIMD exists to expose hardware performance without exposing unnecessary hardware complexity to the programmer.

---

## Kiến trúc Axiom hiện đã đạt một điểm khá quan trọng

Ta đang có một chuỗi rất hợp lý:

```text
Language
   ↓
Ownership
   ↓
Capability
   ↓
Verification
   ↓
OptIR
   ↓
Alias / Range / Escape
   ↓
Auto-vectorization
   ↓
Portable SIMD
   ↓
Target SIMD
   ↓
Machine IR
   ↓
Native code
```

Điểm đáng chú ý là **`view/mut_view` + capability verifier giờ không chỉ giải quyết memory safety**. Nó trở thành **nguồn thông tin tối ưu hóa cho compiler**.

Ví dụ:

```ax
fn saxpy(
    x: view<f32>,
    y: view<f32>,
    out: mut_view<f32>
) {
    for i in 0..out.length() {
        out[i] = x[i] * 2.0 + y[i]
    }
}
```

Nếu verifier chứng minh được ba vùng không overlap:

```text
x ───── READ
y ───── READ
out ─── WRITE
```

thì OptIR có thể tự suy ra:

```text
NoAlias(x, out)
NoAlias(y, out)
```

→ vectorize  
→ AVX2/AVX-512/NEON/SVE/RVV  
→ không cần `restrict`, không cần intrinsic.

Đây chính là hướng mà Axiom nên theo: **programmer viết semantic intent, compiler chịu trách nhiệm biến nó thành machine-level performance.**

### Bước tiếp theo

**BOOTSTRAP-086 — Axiom Numeric Types, Floating-Point Semantics, Decimal/Fixed-Point, Complex, BigInt và Precision Model.**

Phần đó sẽ quyết định sâu hơn về một vấn đề rất quan trọng: **Axiom phải định nghĩa số học chính xác đến mức nào**, đặc biệt là `f32/f64`, overflow, NaN, signed zero, FMA, rounding, `decimal`, fixed-point, `complex`, `i128/u128`, BigInt và các kiểu số phục vụ AI/financial/scientific computing.