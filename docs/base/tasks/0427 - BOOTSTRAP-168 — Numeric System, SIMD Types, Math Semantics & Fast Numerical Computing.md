# BOOTSTRAP-168 — Numeric System, SIMD Types, Math Semantics & Fast Numerical Computing
**STATUS: FROZEN / COMPLETED**

> **Axiom phải có hệ thống số đủ mạnh cho systems programming, scientific computing, graphics, DSP, AI/ML và GPU, nhưng không biến mọi khái niệm toán học thành language primitive.**

Quyết định kiến trúc quan trọng nhất:

> **Scalar numeric types thuộc Core. Vector/SIMD types là compiler-aware library types với semantic contract đặc biệt. Matrix/Tensor là library abstraction, không phải Core primitive.**

Cách này giữ Core gọn nhưng compiler vẫn có thể sinh SIMD/machine code cực thấp tầng.

---

# 1. Phân tầng hệ thống số

```text
Axiom Core
│
├── Integer
│   ├── i8/i16/i32/i64
│   ├── u8/u16/u32/u64
│   ├── isize/usize
│   └── future i128/u128
│
├── Floating Point
│   ├── f32
│   └── f64
│
├── Special
│   ├── bool
│   ├── char
│   └── unit/never
│
└── Numeric semantics
        │
        ▼
std::simd
        │
        ├── Vector
        ├── Mask
        ├── Swizzle
        └── Reduction
        │
        ▼
std::math
        │
        ├── scalar math
        ├── transcendental
        ├── complex
        └── numerical algorithms
        │
        ▼
std::matrix / std::tensor
        │
        ├── Matrix
        ├── Tensor
        ├── BLAS-like
        └── GPU kernels
```

---

# 2. Scalar integer types

Core giữ:

```text
i8   i16   i32   i64
u8   u16   u32   u64
isize usize
```

Đây là các semantic primitive.

Không có:

```text
int
uint
```

với kích thước thay đổi theo target.

---

# 3. `isize` / `usize`

Dùng cho:

- indexing;
- lengths;
- offsets;
- sizes;
- platform-sized quantities.

Ví dụ:

```ax
let n: usize = xs.len();
```

Không tự động convert giữa:

```text
usize ↔ i32
```

---

# 4. Integer conversion

Axiom không cho phép chuỗi implicit conversion kiểu C:

```text
u32 → i64 → f64 → ...
```

Một conversion phải có semantic rõ.

Ví dụ:

```ax
let x: i64 = value as i64;
```

---

# 5. Narrowing conversion

```ax
let x: i32 = big as i32;
```

là explicit.

Semantics của conversion phải được định nghĩa rõ:

- checked;
- wrapping;
- saturating;

không được phụ thuộc undefined behavior.

---

# 6. Integer overflow

Không có signed-integer UB kiểu C/C++.

Axiom phân biệt:

```text
checked
wrapping
saturating
```

Ví dụ conceptual:

```ax
x.checked_add(y)
x.wrapping_add(y)
x.saturating_add(y)
```

---

# 7. Ordinary arithmetic

Đối với operation thông thường:

```ax
x + y
```

semantics phải xác định rõ theo build/profile.

Đề xuất:

> **Debug/safe profile có thể trap hoặc báo overflow; release không được âm thầm biến thành undefined behavior.**

Optimizer được phép loại bỏ overflow check khi chứng minh overflow không thể xảy ra.

---

# 8. Wrapping arithmetic

Cho systems/crypto/bit manipulation:

```ax
x.wrapping_add(y)
```

có semantics modulo `2^N`.

Compiler có thể map trực tiếp sang native integer instruction.

---

# 9. Saturating arithmetic

```ax
x.saturating_add(y)
```

cho:

- DSP;
- image processing;
- audio;
- signal processing;
- embedded.

Target có instruction saturation thì sử dụng trực tiếp.

---

# 10. Checked arithmetic

```ax
x.checked_add(y)
```

trả:

```text
Option<T>
```

hoặc tương đương semantic checked result.

Compiler có thể lower thành:

```text
add
+
overflow flag
```

không cần function call.

---

# 11. Integer division

Division phải có semantics rõ với:

```text
x / 0
```

và:

```text
MIN / -1
```

Không được để backend ISA quyết định ngẫu nhiên semantic.

---

# 12. Integer remainder

```text
x % y
```

phải có contract nhất quán cho signed integers.

Optimizer không được thay đổi semantics chỉ vì target có instruction khác.

---

# 13. Bit operations

Core cần hỗ trợ:

```text
&
|
^
~
<<
>>
```

và các semantic operations:

```text
rotate_left
rotate_right
count_ones
count_zeros
leading_zeros
trailing_zeros
byte_swap
```

---

# 14. Shift semantics

Shift amount ngoài width phải có defined behavior.

Không dựa vào:

```text
x86 behavior
```

hay:

```text
ARM behavior
```

để định nghĩa language semantics.

Compiler có thể loại check nếu range analysis chứng minh shift hợp lệ.

---

# 15. Floating-point primitive

Core:

```text
f32
f64
```

là đủ cho v0.1.

Không đưa hàng loạt:

```text
f16
bf16
f128
decimal128
```

vào Core ngay từ đầu.

Nhưng type-system/ABI architecture không nên ngăn chúng trở thành extension.

---

# 16. Floating-point semantics

Đây là điểm cực kỳ quan trọng.

Axiom không được mặc định coi:

```text
a + b + c
```

tương đương:

```text
a + (b + c)
```

vì floating-point không associative.

---

# 17. Strict FP

Default:

```text
strict floating semantics
```

Compiler phải bảo toàn:

- rounding;
- NaN behavior;
- infinity;
- signed zero;
- observable FP exceptions nếu profile yêu cầu.

---

# 18. Fast math

Cho phép explicit profile/attribute:

```text
@fast_math
```

hoặc build mode tương đương.

Khi đó compiler có thể:

- reassociate;
- approximate transcendental;
- ignore signed-zero distinctions trong phạm vi contract;
- dùng reciprocal approximation;
- FMA transformation;
- vector-friendly transformations.

Nhưng:

> `fast_math` là semantic contract, không chỉ optimization hint.

---

# 19. Không dùng `-O3` để thay đổi FP semantics

Điều này phải đóng băng.

```text
-O0
-O2
-O3
```

không được tự động chuyển:

```text
strict FP → fast FP
```

Nếu muốn fast math phải explicit.

---

# 20. NaN

Axiom phải định nghĩa rõ các operation liên quan NaN.

Đặc biệt:

```text
NaN == NaN
```

không mặc định trở thành true chỉ vì container cần equality.

Do đó:

```text
f32
```

không nhất thiết implement `Eq` theo semantic thông thường.

---

# 21. Numeric traits

Standard library cung cấp:

```text
trait Numeric
trait Integer
trait Signed
trait Unsigned
trait Floating
trait Add
trait Sub
trait Mul
trait Div
trait Rem
trait BitAnd
trait BitOr
trait BitXor
trait Shl
trait Shr
```

Compiler biết các primitive implementations.

---

# 22. Operators

```ax
a + b
```

có thể semantic tương ứng:

```text
Add::add(a, b)
```

nhưng compiler primitive lowering có thể bypass function call.

Không tạo runtime dispatch.

---

# 23. Generic arithmetic

Ví dụ:

```ax
fn square<T: Mul>(x: T) -> T {
    x * x
}
```

có thể specialize thành machine arithmetic.

Không cần boxing.

---

# 24. Numeric literals

Ví dụ:

```ax
42
3.14
```

được contextual typing.

Default đã chốt:

```text
integer → i32
float → f64
```

nếu không có context.

---

# 25. Literal suffix

Cho phép:

```ax
42u8
42i64
3.14f32
```

Không cần syntax đặc biệt cho mọi numeric type.

---

# 26. Compile-time numeric evaluation

```ax
const N: usize = 1024 * 4;
```

được evaluate ở compile time.

Comptime có thể làm:

```ax
comptime {
    ...
}
```

với cùng numeric semantics.

---

# 27. SIMD — quyết định kiến trúc

**Không đưa `f32x8`, `i32x16` thành hàng loạt primitive Core types.**

Thay vào đó:

```text
std::simd::Vector<T, N>
```

là abstraction compiler-aware.

Ví dụ:

```ax
let a: Vector<f32, 8>;
```

---

# 28. Vì sao không đưa SIMD types vào Core?

Nếu Core chứa:

```text
f32x2
f32x4
f32x8
f32x16
...
```

sẽ nhanh chóng thành:

```text
x86 types
ARM types
RISC-V types
GPU types
```

và language semantics bị ISA contamination.

---

# 29. `Vector<T, N>`

Semantic:

```text
N lanes
element type T
```

Không nhất thiết physical representation phải là một register.

Compiler có thể lower thành:

- SIMD register;
- multiple registers;
- scalar sequence;
- stack object.

---

# 30. SIMD width không phải semantic identity

```text
Vector<f32, 8>
```

có 8 logical lanes.

Nhưng target có thể:

```text
AVX2
AVX-512
NEON
SVE
RVV
```

với physical representation khác nhau.

---

# 31. Dynamic vector length

Đối với ISA như SVE/RVV, physical vector length có thể runtime-dependent.

Không ép Core phải có:

```text
Vector<f32, hardware_vector_width>
```

Compiler/backend xử lý riêng.

Có thể có abstraction:

```text
Vector<T, N>
```

và:

```text
ScalableVector<T>
```

ở std::simd.

---

# 32. Fixed SIMD vector

```ax
let x: Vector<f32, 4>;
```

có semantic 4 lanes.

Compiler có thể map:

```text
x86 SSE
ARM NEON
```

hoặc scalar fallback.

---

# 33. SIMD fallback

Không có target SIMD?

Compiler có thể lower:

```text
Vector<f32, 4>
```

thành scalar operations nếu semantics cho phép.

Do đó source không phụ thuộc ISA.

---

# 34. SIMD operations

API:

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

và:

```text
shuffle
swizzle
extract
insert
broadcast
```

---

# 35. Mask

Cần type:

```text
Mask<N>
```

ví dụ:

```ax
let m: Mask<8>;
```

Semantic:

```text
N boolean lanes
```

Không phải `Vector<bool,N>` đơn thuần.

---

# 36. Masked operation

Ví dụ:

```text id="b0a8u7"
select(mask, a, b)
```

Compiler có thể map:

```text
blend
predication
masked instruction
```

hoặc scalar branches.

---

# 37. SIMD comparison

```ax
let m = a < b;
```

trả:

```text
Mask<N>
```

không phải single `bool`.

---

# 38. Horizontal reduction

```text id="g0b13r"
reduce_add
reduce_min
reduce_max
```

phải là explicit semantic operation.

Compiler có thể dùng tree reduction hoặc horizontal instruction.

---

# 39. Floating reduction

Đây là điểm quan trọng.

```text id="5e0f3g"
reduce_add(Vector<f32, 8>)
```

nếu strict FP:

→ thứ tự phép cộng phải được định nghĩa.

Nếu muốn arbitrary reassociation:

```text id="m0g4f7"
fast_reduce_add
```

hoặc fast-math contract.

---

# 40. SIMD + ownership

`Vector<T,N>` là ordinary value.

Không có hidden heap.

Có thể:

```text id="q6w8th"
register
stack
SSA
```

và thường được scalarized/register allocated.

---

# 41. SIMD + Copy

Một vector primitive có thể implement `Copy`.

Nhưng semantic `Copy` vẫn theo Core.

Không có requirement physical register copy.

---

# 42. SIMD + GPU

Không dùng cùng một semantic abstraction để giả vờ CPU SIMD và GPU thread vector là cùng thứ.

Phân biệt:

```text
CPU SIMD
GPU execution lanes
GPU vector types
```

GPU có execution-domain semantics riêng đã frozen.

---

# 43. Matrix

Matrix không thuộc Core.

Standard library:

```text
Matrix<T, R, C>
```

hoặc dynamic-shape abstraction.

---

# 44. Matrix storage

Phải phân biệt:

```text
RowMajor
ColumnMajor
Strided
Blocked
```

Đây là **representation/storage contract**.

---

# 45. Matrix semantic value

Một matrix có semantic:

```text
R × C values
```

không nhất thiết source code phải biết pointer/stride.

---

# 46. Matrix views

Có thể:

```text
MatrixView<T>
MutMatrixView<T>
```

về semantic tương tự:

```text
view<T>
mut_view<T>
```

nhưng bổ sung:

```text
shape
stride
layout
```

---

# 47. Tensor

Tensor cũng là library abstraction:

```text
Tensor<T, Shape, Device>
```

Có thể hỗ trợ:

```text
CPU
GPU
```

và storage domain đã chốt.

---

# 48. Tensor compiler integration

Compiler không cần biết toàn bộ machine learning semantics.

Nhưng cần hiểu:

```text
shape
stride
contiguity
alignment
device
alias
```

khi các property được compiler-readable.

---

# 49. Shape types

Có thể hỗ trợ compile-time shape:

```ax
Tensor<f32, [3, 224, 224]>
```

để compiler biết dimensions.

Dynamic shape:

```ax
Tensor<f32, DynamicShape>
```

vẫn hợp lệ.

---

# 50. Shape checking

Nếu:

```ax
A: Matrix<f32, 4, 8>
B: Matrix<f32, 8, 16>
```

thì:

```ax
A * B
```

có thể được kiểm tra compile time.

Kết quả:

```text
Matrix<f32, 4, 16>
```

---

# 51. Dynamic matrix dimensions

Nếu dimensions runtime:

```text id="w1ppkx"
A: Matrix<f32>
B: Matrix<f32>
```

thì runtime shape check có thể cần.

Compiler có thể eliminate check khi chứng minh dimensions tương thích.

---

# 52. BLAS-like operations

Standard library/package có thể cung cấp:

```text
dot
matmul
gemv
gemm
axpy
reduce
```

và map tới:

- own implementation;
- SIMD;
- GPU;
- platform libraries.

Nhưng Core không phụ thuộc BLAS.

---

# 53. External numerical libraries

FFI layer có thể bind:

```text
MKL
OpenBLAS
Accelerate
cuBLAS
...
```

nhưng Axiom standard semantics không phụ thuộc chúng.

Nếu muốn binary không phụ thuộc third-party:

→ Axiom implementation riêng vẫn khả thi.

---

# 54. Math functions

`std::math`:

```text
sqrt
sin
cos
tan
exp
log
pow
atan2
floor
ceil
round
```

Compiler có thể:

- intrinsic;
- hardware instruction;
- optimized approximation;
- lib implementation.

---

# 55. Math accuracy

Không nên hứa:

> mọi target cho kết quả bit-identical.

Thay vào đó mỗi math function có contract:

```text
accuracy class
special-value behavior
rounding behavior
```

---

# 56. Deterministic math

Có thể có profile:

```text
strict
deterministic
fast
```

### Strict

Tối đa fidelity theo defined FP semantics.

### Deterministic

Yêu cầu kết quả nhất quán theo specified implementation/target profile.

### Fast

Cho phép approximation/reassociation theo contract.

---

# 57. Cross-platform determinism

Không nên tuyên bố:

```text
sin(x)
```

bit-identical trên mọi CPU nếu implementation không đảm bảo.

Nếu ứng dụng cần deterministic simulation:

→ sử dụng deterministic math package/profile có contract riêng.

---

# 58. Complex numbers

Không cần Core.

```text
Complex<T>
```

library type.

Compiler có thể scalarize:

```text
real
imag
```

và vectorize.

---

# 59. Quaternion

Cũng là library type:

```text
Quaternion<T>
```

Không cần language primitive.

---

# 60. Fixed-point

Không cần Core primitive.

Có thể:

```text
Fixed<I, F>
```

trong numeric library.

Compiler specialization có thể biến thành integer arithmetic.

---

# 61. Decimal

Tương tự:

```text
Decimal<N>
```

library abstraction.

Không làm Core phình ra.

---

# 62. Big integer

```text
BigInt
```

library.

Physical representation có thể heap-backed, inline-small, limb array...

Không phải Core numeric primitive.

---

# 63. Numeric abstraction và zero-cost

Ví dụ:

```ax
fn dot<T: Numeric>(
    a: view<T>,
    b: view<T>
) -> T
```

specialize thành machine arithmetic.

Nếu `T=f32`:

```text
SIMD f32
```

Nếu `T=i32`:

```text
integer SIMD
```

Nếu `T=BigInt`:

```text
library operations
```

Không cần runtime polymorphism.

---

# 64. `Numeric` không nên quá lớn

Không tạo một trait:

```text
Numeric:
    + - * / %
    sqrt
    sin
    cos
    ...
```

vì các type không nhất thiết hỗ trợ mọi operation.

Thay vào đó compositional traits:

```text
Add
Mul
Div
Floating
Integer
Signed
...
```

---

# 65. Saturating/checked traits

Có thể có:

```text
CheckedAdd
SaturatingAdd
WrappingAdd
```

hoặc compiler-known operations.

Không overload cùng `+` theo profile.

---

# 66. Numeric literals + generic code

Ví dụ:

```ax
fn distance<T: Floating>(x: T, y: T) -> T {
    let d = x - y;
    sqrt(d * d)
}
```

Literal/contextual typing phải resolve deterministic.

---

# 67. Compile-time vector generation

Comptime có thể tạo:

```text id="tq9o0x"
Vector<f32, 16>
```

lookup tables, constants, coefficients.

Compiler execution environment không trở thành runtime dependency.

---

# 68. Lookup tables

Ví dụ DSP:

```text id="h5z4se"
const SIN_TABLE = comptime generate_table(...);
```

kết quả có thể materialize thành `.rodata`.

Không cần runtime initialization.

---

# 69. Numeric constants

Compiler phải phân biệt:

```text id="12oz5x"
semantic constant
```

với:

```text id="j2nvjv"
physical representation
```

Ví dụ `NaN` payload không nhất thiết là semantic identity.

---

# 70. Endianness

Numeric values trong Axiom không có endian semantics ở source level.

Endian chỉ xuất hiện khi:

```text id="3jv73p"
memory representation
serialization
FFI
hardware register
```

Ví dụ:

```ax
write_u32_le(x)
write_u32_be(x)
```

---

# 71. Volatile numeric access

Hardware register:

```text id="d4w91n"
volatile_load
volatile_store
```

không được optimizer loại bỏ/reorder tùy ý.

Volatile khác atomic.

---

# 72. Atomic numeric types

```text id="g5v9z8"
Atomic<T>
```

chỉ cho các T được phép.

Atomic semantics:

```text id="x3smnd"
Relaxed
Acquire
Release
AcqRel
SeqCst
```

đã frozen trong concurrency model.

---

# 73. Atomic SIMD

Không mặc định:

```text id="6v4h2c"
Atomic<Vector<T,N>>
```

chỉ vì vector tồn tại.

Atomicity là property của operation/hardware contract.

Nếu target hỗ trợ vector atomics, specialized library/API có thể cung cấp.

---

# 74. Numeric + GPU

GPU numeric types dùng lại:

```text
i32
u32
f32
f64
```

khi target hỗ trợ.

Compiler GPU backend chịu trách nhiệm:

```text
legalization
precision
address space
instruction selection
```

---

# 75. GPU FP semantics

Không tự động áp strict CPU FP semantics nếu GPU ABI/ISA có khác biệt.

`@kernel` compilation profile phải xác định:

```text
precision
rounding
fast math
denorm behavior
```

---

# 76. SIMD alignment

Compiler không yêu cầu programmer viết alignment cho ordinary vectors.

Compiler biết:

```text
alignment
alias
layout
```

và chọn:

```text
aligned load
unaligned load
```

phù hợp.

---

# 77. Explicit alignment

Nếu programmer yêu cầu:

```ax
@align(64)
struct Data { ... }
```

thì đó là representation contract.

Compiler phải tôn trọng.

---

# 78. SIMD aliasing

Compiler không được giả định:

```text
Vector pointers don't alias
```

chỉ vì vector.

Alias proof vẫn đến từ:

```text
capability
region
ownership
```

---

# 79. SIMD and view

Có thể:

```ax
fn add(
    a: view<Vector<f32, 8>>,
    b: view<Vector<f32, 8>>,
    out: mut_view<Vector<f32, 8>>
)
```

nhưng thường API tốt hơn là:

```ax
fn add(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
)
```

và compiler tự vectorize.

Đây là điểm triết lý quan trọng:

> **SIMD type dùng khi programmer thực sự muốn semantic vector operations; không cần ép programmer viết SIMD để có SIMD machine code.**

---

# 80. Auto-vectorization vẫn là default path

Code:

```ax
for i in 0..n {
    out[i] = a[i] + b[i];
}
```

vẫn là abstraction ưu tiên.

Compiler có thể biến nó thành:

```text
AVX2/AVX-512/NEON/SVE/RVV
```

tùy target.

---

# 81. Explicit SIMD dùng khi cần

Ví dụ:

- algorithm yêu cầu lane semantics;
- shuffle;
- swizzle;
- horizontal operation;
- crypto primitive;
- DSP kernel;
- target-specific vector behavior.

---

# 82. Intrinsics

Không cấm intrinsic.

Nhưng intrinsic nằm ở:

```text
std::arch
std::simd
unsafe/system
```

không phải ordinary programming path.

---

# 83. Target-specific SIMD

Có thể:

```ax
@target_feature("avx2")
fn fast_path(...) { ... }
```

đã phù hợp với target-feature model.

Compiler đảm bảo không emit instruction nếu target không hỗ trợ.

---

# 84. Runtime dispatch

Nếu binary hỗ trợ nhiều CPU:

```text
generic path
+
AVX2 path
+
AVX-512 path
```

runtime dispatch là system/library concern.

Compiler có thể hỗ trợ multiversioning.

---

# 85. Numeric performance hierarchy

Axiom sẽ có:

```text
Scalar source
      ↓
Generic numeric code
      ↓
Inlining
      ↓
Constant propagation
      ↓
Loop optimization
      ↓
Scalar evolution
      ↓
Alias analysis
      ↓
Auto-vectorization
      ↓
SIMD
      ↓
Microarchitecture scheduling
      ↓
Machine code
```

Trong trường hợp phù hợp, programmer không cần biết SIMD tồn tại.

---

# 86. Core không trở thành “math language”

Không đưa vào Core:

```text
Matrix
Tensor
Complex
BigInt
Decimal
Quaternion
Polynomial
Rational
```

Chúng là library abstractions.

Core chỉ cung cấp semantic foundations.

---

# 87. Nhưng compiler phải “numeric-aware”

Compiler vẫn phải hiểu:

- integer overflow;
- FP semantics;
- vector operations;
- masks;
- atomic numeric operations;
- alignment;
- target features;
- fast-math contract.

Đây là compiler intelligence, không phải language surface complexity.

---

# 88. Numeric representation

Pipeline:

```text
Semantic Numeric Type
        ↓
Representation
        ↓
Target Numeric Type
        ↓
Vectorization
        ↓
Machine Numeric Instruction
```

Không để source-level type phụ thuộc trực tiếp ISA.

---

# 89. Numeric ABI

ABI classification đã có từ BOOTSTRAP-108.

Scalar:

```text
i32
i64
f32
f64
```

có thể truyền register.

Vector:

```text
Vector<T,N>
```

ABI target-dependent.

Không đóng băng physical register class ở Core.

---

# 90. Numeric debugging

`axdbg` phải hiển thị semantic:

```text
x = 3.14f32
```

thay vì chỉ:

```text
xmm3 = 0x...
```

Nhưng có thể inspect cả hai:

```text
axc inspect value x
axc inspect representation x
```

---

# 91. Numeric optimization explanation

Ví dụ:

```text id="7q9u2p"
axc explain vectorize foo
```

có thể nói:

```text
Loop vectorized.

Element type:
    f32

Vector width:
    8

Alias:
    proven disjoint

Bounds:
    proven

Floating-point mode:
    strict

Reduction:
    not present

Target:
    AVX2
```

Rất hữu ích cho AI agent.

---

# 92. Numeric benchmark suite

Conformance/performance test nên có:

```text
integer add/mul/div
overflow
shift
bit operations
float arithmetic
NaN
Inf
signed zero
rounding
FMA
vector arithmetic
masked operations
reductions
matrix multiplication
dot product
```

---

# 93. Security considerations

Không cho optimizer biến:

```text
constant-time arithmetic
```

thành code có data-dependent branch nếu function đang nằm dưới explicit security contract.

Điều này nối trực tiếp BOOTSTRAP-161.

---

# 94. Crypto arithmetic

Crypto có thể cần:

```text
wrapping
constant-time
wide integers
bit operations
```

Axiom Core + std primitives phải đủ để xây crypto library mà không cần compiler special case cho từng algorithm.

---

# 95. Numeric portability

Source:

```ax
let x: i32 = ...
```

phải có semantics ổn định trên:

```text
x86-64
ARM64
RISC-V
WASM
```

Compiler xử lý khác biệt backend.

---

# 96. Numeric target extensions

Future có thể thêm:

```text
i128
u128
f16
bf16
f128
decimal
```

mà không phá Core architecture.

---

# 97. `i128/u128`

Không nhất thiết cần hardware register.

Compiler có thể lower:

```text
128-bit
```

thành nhiều machine instructions.

Đây chính là lý do semantic type không đồng nghĩa machine register.

---

# 98. `f16/bf16`

Có thể hỗ trợ ở:

```text
std::numeric
std::simd
std::gpu
```

trước khi trở thành universal Core primitive.

---

# 99. Numeric semantic hierarchy

Đóng khung:

```text
Semantic Type
    ↓
Numeric Trait
    ↓
Generic Algorithm
    ↓
Concrete Specialization
    ↓
Scalar/SIMD Representation
    ↓
Target Instruction
```

---

# 100. Frozen invariants

### `ANUM-20`
Scalar integer types are Core semantic primitives.

### `ANUM-21`
Scalar floating-point types are Core semantic primitives.

### `ANUM-22`
`isize` and `usize` are target-sized semantic integer types.

### `ANUM-23`
Numeric types have stable semantic identities independent of physical representation.

### `ANUM-24`
Implicit numeric conversion chains are not permitted.

### `ANUM-25`
Narrowing numeric conversions are explicit.

### `ANUM-26`
Integer overflow has defined semantics.

### `ANUM-27`
Signed integer overflow is never undefined behavior.

### `ANUM-28`
Checked arithmetic is explicit.

### `ANUM-29`
Wrapping arithmetic has modulo semantics.

### `ANUM-30`
Saturating arithmetic is explicit.

### `ANUM-31`
Shift operations have defined language semantics independent of target ISA behavior.

### `ANUM-32`
Division-by-zero behavior is defined by the language/runtime profile.

### `ANUM-33`
Bit operations have defined width semantics.

### `ANUM-34`
Floating-point semantics are distinct from integer semantics.

### `ANUM-35`
Strict floating-point semantics are preserved unless an explicit relaxed contract applies.

### `ANUM-36`
Optimization level alone cannot enable fast-math semantics.

### `ANUM-37`
NaN, infinity and signed-zero behavior are governed by the active FP semantic profile.

### `ANUM-38`
Floating-point reassociation requires an appropriate semantic contract.

### `ANUM-39`
Numeric literals have deterministic contextual typing.

### `ANUM-40`
Numeric literals support explicit type suffixes.

### `ANUM-41`
Compile-time numeric evaluation uses the same semantic arithmetic rules.

### `ANUM-42`
SIMD is not a collection of ISA-specific Core primitive types.

### `ANUM-43`
`Vector<T,N>` is a compiler-aware library abstraction.

### `ANUM-44`
Logical vector width is distinct from physical register width.

### `ANUM-45`
SIMD vectors may lower to registers, multiple registers, scalar operations or other target representations.

### `ANUM-46`
SIMD types do not imply heap allocation.

### `ANUM-47`
SIMD masks are distinct semantic lane-mask values.

### `ANUM-48`
Masked operations preserve inactive-lane semantics.

### `ANUM-49`
SIMD comparison produces lane masks rather than scalar booleans.

### `ANUM-50`
SIMD reductions have explicitly defined ordering/precision semantics.

### `ANUM-51`
Strict floating-point reductions cannot silently reassociate.

### `ANUM-52`
Fast reductions may use relaxed semantics only under explicit contract.

### `ANUM-53`
Auto-vectorization does not require programmer-written SIMD types.

### `ANUM-54`
Auto-vectorization does not require pointer arithmetic.

### `ANUM-55`
Auto-vectorization does not require programmer-written `restrict`.

### `ANUM-56`
SIMD alias assumptions must originate from verified alias analysis.

### `ANUM-57`
SIMD alignment assumptions must be proven or explicitly contracted.

### `ANUM-58`
Target-specific SIMD instructions require appropriate target-feature support.

### `ANUM-59`
Unsupported SIMD targets may use scalar or alternate legal lowering.

### `ANUM-60`
Matrix is a library abstraction, not a Core primitive.

### `ANUM-61`
Tensor is a library abstraction, not a Core primitive.

### `ANUM-62`
Matrix/tensor storage layout is explicit when layout affects semantics.

### `ANUM-63`
Matrix views use ordinary Axiom capability semantics.

### `ANUM-64`
Tensor storage domains remain compatible with the GPU/storage-domain model.

### `ANUM-65`
Compile-time dimensions may participate in type checking.

### `ANUM-66`
Runtime dimensions require runtime validation unless statically proven.

### `ANUM-67`
Math library functions have explicit numerical behavior contracts.

### `ANUM-68`
Cross-platform numerical behavior is not assumed bit-identical unless explicitly contracted.

### `ANUM-69`
Deterministic numerical computation may use specialized library/profile contracts.

### `ANUM-70`
Complex, quaternion, fixed-point, decimal and big-integer types remain library abstractions.

### `ANUM-71`
Generic numeric algorithms are statically specialized where profitable.

### `ANUM-72`
Numeric traits are compositional rather than one universal monolithic `Numeric` interface.

### `ANUM-73`
Operator overloading does not require runtime dispatch.

### `ANUM-74`
Primitive numeric operations may bypass generic trait call representation during lowering.

### `ANUM-75`
Numeric generic abstractions remain subject to ordinary ownership/capability verification.

### `ANUM-76`
Atomic numeric operations follow the global Axiom memory model.

### `ANUM-77`
Volatile numeric operations remain distinct from atomic operations.

### `ANUM-78`
Endian semantics apply to representation/serialization/hardware boundaries, not ordinary numeric values.

### `ANUM-79`
Numeric representations may be transformed aggressively when semantic and ABI contracts permit.

### `ANUM-80`
Numeric optimizations cannot weaken memory safety, concurrency safety or security contracts.

### `ANUM-81`
Constant-time contracts constrain numeric optimization.

### `ANUM-82`
Numeric optimization decisions are inspectable by compiler tooling.

### `ANUM-83`
Numeric semantics are independent of physical register selection.

### `ANUM-84`
Numeric semantics are independent of target microarchitecture.

### `ANUM-85`
Future numeric extensions must integrate through the existing type/representation/ABI architecture rather than introducing ISA-specific semantic primitives.

---

# Quyết định quan trọng nhất của BOOTSTRAP-168

Axiom **không nên trở thành Rust/C++ + một đống SIMD primitive**.

Mô hình cuối cùng nên là:

```text
                    Axiom Core
                       │
              ┌────────┴────────┐
              │                 │
            Scalar            Generic
              │                 │
       i32/f32/f64/...     Numeric Traits
              │                 │
              └────────┬────────┘
                       ▼
                  std::simd
                       │
              Vector / Mask / Swizzle
                       │
                       ▼
                Compiler Vector IR
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
        Auto Vectorization    Explicit SIMD
             │                   │
             └─────────┬─────────┘
                       ▼
                Target Backend
                       │
        AVX2 / AVX-512 / NEON / SVE / RVV
```

Còn:

```text
Matrix
Tensor
Complex
Quaternion
BigInt
Decimal
FixedPoint
```

đều nằm phía library.

**Như vậy programmer có thể viết loop scalar rất đơn giản, compiler tự biến nó thành SIMD; nhưng khi cần kiểm soát lane-level, programmer vẫn có `Vector<T,N>` mà không cần chui xuống pointer/intrinsic/assembly.**

---

# BOOTSTRAP-169 — String, Unicode, Text, Encoding & Internationalization

Bước kế tiếp nên chốt **hệ thống text/string**. Đây cũng là một phần Core rất dễ thiết kế sai.

Cần giải quyết dứt điểm:

```text
String
Str
Bytes
char
Unicode scalar
grapheme cluster
UTF-8
UTF-16
UTF-32
C string
OS string
file/network encoding
normalization
case conversion
locale
```

Đặc biệt Axiom đã chọn **UTF-8 mặc định**, nên bước này cần đảm bảo UTF-8 vừa **an toàn**, vừa **không khiến mọi thao tác chuỗi bị chậm**, đồng thời vẫn hỗ trợ trực tiếp FFI/Windows/Linux/macOS/iOS/Android và compiler tooling.