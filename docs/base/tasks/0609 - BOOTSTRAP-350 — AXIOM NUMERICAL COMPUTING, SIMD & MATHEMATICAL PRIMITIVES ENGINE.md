# BOOTSTRAP-350 — AXIOM NUMERICAL COMPUTING, SIMD & MATHEMATICAL PRIMITIVES ENGINE

## 1. Mục tiêu

Sau `BOOTSTRAP-349`, Axiom đã có nền tảng dữ liệu, buffer, collection, text và zero-copy. Bước tiếp theo nên xây **numeric layer** đủ mạnh để Axiom có thể dùng cho:

- systems programming;
- game/graphics;
- signal/audio processing;
- scientific computing;
- machine learning;
- GPU computing;
- compiler/runtime implementation;
- SIMD/vectorized algorithms.

Mục tiêu không phải biến Core thành một thư viện toán học khổng lồ.

Nguyên tắc:

> **Core định nghĩa semantic của số và vector hóa; Standard Library cung cấp thuật toán toán học.**

---

# 2. Phân tầng

Axiom chia numerical stack thành 4 tầng:

```text
Language Numeric Semantics
        ↓
Machine Numeric / SIMD
        ↓
Numerical Standard Library
        ↓
Domain Libraries
```

### Language Numeric Semantics

Core:

```text
bool
i8 i16 i32 i64
u8 u16 u32 u64
isize usize
f32 f64
```

và:

```text
integer arithmetic
floating arithmetic
casts
overflow
comparison
bit operations
shift
numeric literals
```

### Machine Numeric / SIMD

Compiler hỗ trợ:

```text
vector<T, N>
mask<N>
```

và các primitive SIMD.

### Numerical Standard Library

Cung cấp:

```text
sqrt
sin
cos
tan
exp
log
pow
abs
min
max
clamp
floor
ceil
round
fma
...
```

### Domain libraries

Không thuộc Core:

```text
Matrix
Tensor
FFT
Linear Algebra
Statistics
ML
Signal Processing
Geometry
Physics
```

---

# 3. Numeric type semantics

Axiom không cho phép arithmetic semantics phụ thuộc vào compiler optimization.

Ví dụ:

```text
let a: i32 = ...
let b: i32 = ...

a + b
```

luôn có semantic giống nhau dù compiler bật:

```text
-O0
-O2
-O3
-LTO
-PGO
```

Compiler chỉ được thay đổi implementation khi kết quả quan sát được tương đương.

---

# 4. Integer overflow

Không sử dụng C-style:

> signed overflow = undefined behavior.

Axiom phải có các semantic operation riêng.

Ví dụ:

```text
a + b
a.checked_add(b)
a.wrapping_add(b)
a.saturating_add(b)
```

Semantic:

### Normal arithmetic

```text
a + b
```

Nếu overflow:

```text
panic/trap
```

theo compilation profile.

### Checked

```text
checked_add
```

trả:

```text
Option<T>
```

### Wrapping

```text
wrapping_add
```

thực hiện modulo `2^N`.

### Saturating

```text
saturating_add
```

clamp về min/max.

Compiler được phép biến đổi chúng thành instruction machine tương ứng.

---

# 5. Division

Integer division phải định nghĩa rõ:

```text
a / b
a % b
```

### Divide by zero

Không phải undefined behavior.

Là runtime trap/panic theo profile.

### Signed minimum / -1

Phải có semantic xác định, không được để CPU-specific overflow trở thành undefined behavior.

Compiler có thể:

- trap;
- dùng instruction đặc biệt;
- branch;
- hoặc chứng minh trường hợp không xảy ra.

---

# 6. Floating-point model

Axiom không cố giả vờ rằng floating-point là real number.

Semantic phải phản ánh IEEE-754 và target capability.

Cần định nghĩa:

```text
NaN
+0
-0
+∞
-∞
subnormal
rounding
```

Phân biệt:

```text
numeric equality
bit equality
```

Ví dụ:

```text
NaN != NaN
```

nhưng:

```text
bit_cast<u32>(x)
```

có thể quan sát representation.

---

# 7. Floating-point fast math

Compiler không được tự ý biến:

```text
a + b
```

thành phép toán có semantic khác chỉ vì `fast-math`.

Thay vào đó:

```text
@fast_math
```

hoặc compilation profile tương đương phải là **semantic contract**.

Fast-math có thể cho phép:

```text
reassociation
NaN assumption
infinity assumption
signed-zero relaxation
FMA contraction
approximate transcendental
```

nhưng phải được ghi nhận trong semantic fingerprint/build configuration.

---

# 8. Numeric casts

Không cho phép implicit narrowing nguy hiểm.

Ví dụ:

```text
i64 → i32
f64 → i32
u64 → i16
```

phải explicit.

Các conversion semantic phải phân biệt:

```text
numeric_cast
checked_cast
saturating_cast
wrapping_cast
bit_cast
```

Ví dụ:

```text
x as i32
x.checked_as::<i32>()
x.saturating_as::<i32>()
bit_cast::<u32>(x)
```

`bit_cast` **không phải numeric conversion**.

---

# 9. Generic numeric abstraction

Không hard-code các thuật toán vào compiler.

Compiler chỉ cung cấp primitive traits như:

```text
Add
Sub
Mul
Div
Rem
Neg
BitAnd
BitOr
BitXor
Shl
Shr
Eq
Ord
```

và các numeric capability:

```text
Integer
Signed
Unsigned
Float
Numeric
```

Ví dụ:

```text
fn square<T: Numeric>(x: T) -> T {
    x * x
}
```

Compiler có thể specialize thành:

```text
i32
i64
f32
f64
```

mà không cần dynamic dispatch.

---

# 10. SIMD type

Đây là phần rất quan trọng.

Axiom cần semantic vector type:

```text
vector<f32, 4>
vector<i32, 8>
vector<u8, 16>
```

Ví dụ:

```text
let a: vector<f32, 8>
let b: vector<f32, 8>

let c = a + b
```

Compiler có thể lower thành:

```text
SSE
AVX
AVX2
AVX-512
NEON
SVE
RVV
GPU vector instruction
```

hoặc scalar loop nếu target không có SIMD phù hợp.

---

# 11. SIMD không được gắn cứng vào ISA

Source:

```text
vector<f32, 8>
```

không có nghĩa:

```text
AVX2
```

Nó biểu diễn **semantic vector**.

Target backend quyết định:

```text
native vector width
instruction set
register class
scalar fallback
vector splitting
vector packing
```

Nhờ vậy cùng source có thể compile cho:

```text
x86-64
ARM64
RISC-V
WASM
GPU
```

---

# 12. Mask

SIMD cần mask primitive:

```text
mask<8>
```

Ví dụ:

```text
let m = a > b
let c = select(m, a, b)
```

Semantic:

```text
m[i] == true
    → result[i] = a[i]

m[i] == false
    → result[i] = b[i]
```

Compiler có thể sử dụng:

```text
AVX mask
predication
blend
branch
```

tùy target.

---

# 13. Vector memory operations

Cần phân biệt:

```text
vector_load
vector_store
gather
scatter
```

nhưng programmer không nên phải biết instruction cụ thể.

Các capability đã có từ `BOOTSTRAP-349` phải được tận dụng:

```text
Aligned
Contiguous
LengthKnown
NoAlias
ReadOnly
MutableExclusive
StrideKnown
```

Ví dụ compiler có thể chứng minh:

```text
view<f32>
+ contiguous
+ aligned
+ NoAlias
```

→ vectorize an toàn.

---

# 14. Alignment

Không ép mọi vector phải có alignment cố định.

Compiler biết:

```text
required_alignment
actual_alignment
```

Nếu chứng minh đủ alignment:

```text
aligned_load
```

Nếu không:

```text
unaligned_load
```

Không được biến alignment assumption sai thành UB trong safe code.

---

# 15. Scalar/vector unification

API nên cho phép generic code hoạt động với scalar và vector khi semantic phù hợp.

Ví dụ conceptually:

```text
Numeric
    ├── scalar
    └── vector
```

Nhưng vector không phải subtype runtime của scalar.

Đây là compile-time abstraction.

---

# 16. Math library

Standard Library cung cấp:

### Elementary

```text
abs
min
max
clamp
sign
sqrt
cbrt
hypot
```

### Exponential/logarithmic

```text
exp
exp2
log
log2
log10
pow
```

### Trigonometric

```text
sin
cos
tan
asin
acos
atan
atan2
```

### Hyperbolic

```text
sinh
cosh
tanh
```

### Rounding

```text
floor
ceil
trunc
round
```

### Floating classification

```text
is_nan
is_inf
is_finite
is_normal
is_subnormal
```

---

# 17. FMA

Axiom cần semantic primitive:

```text
fma(a, b, c)
```

khác với:

```text
a * b + c
```

vì FMA có một lần rounding.

Compiler **không được tự động coi hai biểu thức này giống nhau** trong strict floating-point mode.

Trong fast-math mode, contraction có thể được cho phép.

---

# 18. Math implementation tiers

Không bắt buộc mọi target phải có cùng implementation.

Ví dụ:

```text
sqrt
```

có thể được lower thành:

```text
CPU instruction
runtime intrinsic
compiler builtin
software implementation
```

Nhưng public semantic phải ổn định theo numerical contract.

---

# 19. Determinism

Axiom phải phân biệt:

```text
Strict FP
Fast FP
Reproducible FP
```

### Strict FP

Ưu tiên semantic IEEE/target-defined chính xác.

### Fast FP

Cho phép optimization mạnh hơn.

### Reproducible FP

Cho phép project yêu cầu kết quả ổn định hơn giữa:

```text
machines
threads
optimization levels
```

trong phạm vi contract được định nghĩa.

Không được hứa rằng mọi floating calculation trên mọi GPU/CPU sẽ có bit-identical result nếu hardware semantics khác nhau.

---

# 20. Reduction

Đặc biệt quan trọng cho SIMD/GPU:

```text
sum(view<f32>)
```

không mặc định được coi là associative.

Vì:

```text
(a + b) + c
```

có thể khác:

```text
a + (b + c)
```

Do đó cần phân biệt:

```text
strict_reduce
fast_reduce
deterministic_reduce
```

Điều này ngăn compiler tự ý reorder floating-point reduction.

---

# 21. Matrix/Tensor không đưa vào Core

Axiom **không** đưa:

```text
Matrix
Tensor
Vector3
Quaternion
Complex
```

vào language core.

Chúng là library types.

Ví dụ:

```text
struct Vec3 {
    x: f32
    y: f32
    z: f32
}
```

hoặc:

```text
Tensor<T, Shape, Device>
```

được xây bằng:

```text
struct
generic
const parameters
view
mut_view
Buffer
SIMD
GPU
```

Điều này giữ Core sạch nhưng không hạn chế khả năng numerical computing.

---

# 22. Const dimensions

Khi const generic đã có, library có thể định nghĩa:

```text
Matrix<T, const R: usize, const C: usize>
```

và:

```text
Vector<T, const N: usize>
```

Compiler có thể biết:

```text
N
R
C
```

tại compile time.

Từ đó tối ưu:

```text
unrolling
SIMD
stack allocation
register allocation
bounds elimination
```

---

# 23. Numerical safety

Không để numerical library phá vỡ memory model.

Ví dụ:

```text
matmul(a, b, out)
```

phải mô tả aliasing.

Nếu:

```text
out
```

có thể overlap:

```text
a
```

thì implementation không được giả định NoAlias.

Nếu API yêu cầu disjoint:

```text
matmul_into(
    a: view<T>,
    b: view<T>,
    out: mut_view<T>
)
```

compiler phải chứng minh hoặc abstraction phải cung cấp contract.

---

# 24. Compiler integration

Thêm vào CompilerDB:

```text
NumericTypeDB
NumericSemanticsDB
OverflowModeDB
FloatingPointModeDB
MathIntrinsicDB
SIMDTypeDB
SIMDTargetDB
SIMDInstructionDB
MaskTypeDB
VectorizationDB
ReductionDB
NumericCastDB
ConstantFoldingDB
FastMathDB
NumericalReproducibilityDB
```

---

# 25. Optimization integration

Numerical semantics phải kết nối trực tiếp với optimizer:

```text
Typed MIR
    ↓
Numeric Analysis
    ↓
Range Analysis
    ↓
Overflow Analysis
    ↓
SIMD Analysis
    ↓
Vectorization
    ↓
Target Legalization
```

Compiler có thể chứng minh:

```text
0 <= i < 1024
```

→ loại bounds check.

Có thể chứng minh:

```text
regions disjoint
```

→ vectorize.

Có thể chứng minh:

```text
alignment >= 32
```

→ dùng aligned vector load.

Có thể chứng minh:

```text
overflow impossible
```

→ dùng native arithmetic mà không cần runtime check.

---

# 26. Numerical provenance

Optimization remark cần giải thích được:

```text
vectorized loop
```

vì:

```text
- contiguous memory proven
- noalias proven
- trip count known
- alignment proven
```

hoặc tại sao **không** vectorize:

```text
- possible alias
- floating reduction requires strict ordering
- target lacks instruction
- runtime trip count too small
```

Đây là phần rất quan trọng đối với AI compiler tooling.

---

# 27. GPU integration

Numeric/SIMD layer phải dùng chung semantic với GPU.

Ví dụ:

```text
vector<f32, 4>
```

không tạo một numeric model riêng cho GPU.

GPU backend chỉ thay đổi:

```text
execution domain
storage domain
instruction set
memory model
```

Các primitive:

```text
add
mul
fma
min
max
mask
reduce
```

có semantic chung khi phù hợp.

---

# 28. Numerical ABI

ABI phải định nghĩa cách truyền:

```text
scalar
vector
mask
small aggregate numeric type
```

Ví dụ vector có thể được truyền:

```text
register
multiple registers
stack
memory
```

tùy target ABI.

Source-level vector type không được phụ thuộc vào một ABI cụ thể.

---

# 29. Invariants

Đóng băng các invariant chính:

```text
ANUM-01
Numeric operations have deterministic language-level semantics.

ANUM-02
Signed integer overflow is never implicit undefined behavior.

ANUM-03
Narrowing numeric conversion is explicit.

ANUM-04
Numeric conversion and bit reinterpretation are distinct operations.

ANUM-05
Floating-point semantics are explicit.

ANUM-06
Fast-math is an explicit semantic/compilation contract.

ANUM-07
Strict floating-point mode forbids unsound reassociation.

ANUM-08
SIMD types are target-independent semantic types.

ANUM-09
SIMD lowering is target-specific.

ANUM-10
Mask operations have defined lane semantics.

ANUM-11
Safe SIMD operations cannot violate memory safety.

ANUM-12
Alignment assumptions require proof or explicit unsafe contract.

ANUM-13
Vectorization may rely on verified capability/alias facts.

ANUM-14
UNKNOWN aliasing cannot be treated as NoAlias.

ANUM-15
Floating reduction ordering is semantically significant in strict mode.

ANUM-16
FMA semantics are distinct from multiply followed by add.

ANUM-17
Scalar and vector operations may share generic abstractions without runtime subtype semantics.

ANUM-18
Math library algorithms are not language-core primitives unless required for semantic correctness.

ANUM-19
Numerical libraries cannot bypass ownership/capability verification.

ANUM-20
GPU numerical operations reuse compatible Axiom numeric semantics.

ANUM-21
Numeric ABI is target-specific but source semantics are target-independent.

ANUM-22
Optimization cannot change strict numerical results.

ANUM-23
Constant folding must preserve numerical semantics.

ANUM-24
NaN, signed zero and infinity behavior must remain observable where the language permits observation.

ANUM-25
Reproducible numerical execution is a separate contract from ordinary execution.

ANUM-26
Compiler diagnostics can explain why numeric optimization/vectorization succeeded or failed.

ANUM-27
Numeric abstractions must permit zero-cost specialization.

ANUM-28
No mandatory numerical runtime is introduced.

ANUM-29
Scalar fallback must exist where target SIMD support is unavailable.

ANUM-30
Numerical domain libraries remain outside the language Core.
```

---

# 30. DoD

`BOOTSTRAP-350` chỉ hoàn thành khi Axiom có:

- numeric semantic specification;
- integer overflow model;
- division model;
- floating-point model;
- numeric conversion model;
- bit-cast model;
- strict/fast/reproducible FP;
- numeric traits;
- SIMD semantic type;
- mask;
- vector memory operations;
- target-independent SIMD lowering;
- alignment semantics;
- reduction semantics;
- FMA semantics;
- numerical optimization contracts;
- numerical ABI;
- compiler numeric analysis;
- SIMD/vectorization integration;
- GPU numeric integration;
- numerical diagnostics/provenance;
- conformance tests cho numeric semantics;
- differential tests giữa scalar/SIMD implementation;
- target tests cho x86/ARM/RISC-V/WASM;
- overflow/floating-point edge-case tests;
- reproducibility tests.

**Kết quả kiến trúc quan trọng:** Axiom lúc này không chỉ là systems language có memory model mạnh, mà đã có nền móng để xây **graphics, audio, scientific computing, ML và GPU library** mà không cần biến các domain đó thành tính năng đặc biệt của ngôn ngữ.