# BOOTSTRAP-368 — Axiom Numeric, Mathematical & Scientific Computing Type System

Sau **367 — GPU/Heterogeneous Compilation**, bước tiếp theo nên khóa nền tảng **numeric computing**. Đây là phần đặc biệt quan trọng với mục tiêu Axiom vì ngôn ngữ không chỉ nhắm hệ thống mà còn muốn hỗ trợ **AI/GPU/CPU/SIMD**.

Mục tiêu không phải tạo một thư viện toán học khổng lồ trong Core, mà là định nghĩa **semantic foundation** để các thư viện như tensor, linear algebra, ML, signal processing… có thể xây bên trên mà không phải chống lại type system/compiler.

---

## 1. Vấn đề cần giải quyết

Các kiểu:

```text
i32
u32
f32
f64
vec<f32, 8>
```

chưa đủ cho scientific computing.

Ta còn cần semantics cho:

```text
complex numbers
vectors
matrices
fixed-point
decimal
half precision
bfloat16
quantized integers
intervals
dual numbers
automatic differentiation
```

Nhưng không nên biến tất cả thành **primitive Core type**.

Nguyên tắc:

> Core định nghĩa semantics cần thiết; thư viện cung cấp domain-specific numeric types.

---

# 2. Numeric hierarchy

Axiom nên có ba tầng:

```text
Machine Numeric
        ↓
Generic Numeric Semantics
        ↓
Domain Numeric Library
```

### Machine Numeric

Core:

```text
i8/i16/i32/i64
u8/u16/u32/u64
isize/usize

f32/f64
```

Extension:

```text
f16
bf16
i128/u128
```

### Generic Numeric

Compiler hiểu concepts như:

```text
Integer
UnsignedInteger
SignedInteger
FloatingPoint
Real
Complex
Numeric
```

nhưng chúng chủ yếu là **traits/constraints**, không phải runtime hierarchy.

### Domain Numeric

Library:

```text
Complex<T>
Rational<T>
Decimal<T>
Fixed<T, FractionBits>
Tensor<T, Shape>
Matrix<T, M, N>
```

---

# 3. Không có “Number” runtime type

Không tạo:

```text
Number
```

theo kiểu:

```text
Number x = 1;
x = 1.2;
```

vì điều này làm mất static information và có thể dẫn đến boxing/dynamic dispatch.

Thay vào đó:

```text
let x: i32 = 1;
let y: f64 = 1.2;
```

Compiler biết chính xác representation.

---

# 4. Numeric traits

Có thể có:

```text
trait Numeric
trait Integer
trait Signed
trait Unsigned
trait Float
trait Exact
trait Approximate
```

Ví dụ:

```text
fn sum<T: Numeric>(a: view<T>) -> T
```

Compiler có thể monomorphize:

```text
sum_i32
sum_f32
sum_f64
```

không cần dynamic dispatch.

---

# 5. Numeric conversion

Đây là phần phải rất chặt.

Không cho:

```text
let x: f32 = i64_value;
```

tự động trong mọi trường hợp.

Các conversion có thể phân thành:

```text
Widen
Narrow
SignednessChange
IntegerToFloat
FloatToInteger
BitCast
NumericCast
SaturatingCast
CheckedCast
```

Ví dụ:

```text
let x = a as f64;
```

là semantic conversion.

---

# 6. Không dùng một `as` cho mọi thứ

Compiler nội bộ phải phân biệt:

```text
NumericCast
BitCast
Reinterpret
```

Dù source syntax có thể đơn giản.

Ví dụ:

```text
let x: u32 = bits as u32;
```

không giống:

```text
let x: f32 = bits bitcast f32;
```

`bitcast` chỉ hợp lệ khi:

```text
size equal
alignment valid
representation permitted
```

và có thể là unsafe ở các trường hợp target-dependent.

---

# 7. Integer overflow

Axiom không được có C-style:

```text
signed overflow = UB
```

Core phải định nghĩa rõ.

Các operation:

```text
add
checked_add
wrapping_add
saturating_add
```

Ví dụ:

```text
let x = a + b;
```

có behavior phụ thuộc **numeric profile**, nhưng semantics phải được freeze.

Khuyến nghị:

- Debug/release không được tự ý thay đổi mathematical meaning.
- Overflow của signed integer mặc định là **panic/trap hoặc checked failure theo profile**, không UB.
- `wrapping_add` luôn modulo.
- `saturating_add` clamp.
- `checked_add` trả `Option<T>`.

Compiler có thể optimize khi chứng minh overflow impossible.

---

# 8. Unsigned integer

Unsigned integer có semantics modulo:

```text
u32::MAX + 1
```

tương đương:

```text
0
```

ở wrapping operation.

Nhưng ordinary `+` vẫn nên giữ semantic profile rõ ràng thay vì dựa vào việc programmer phải nhớ implicit wrapping.

---

# 9. Floating-point không phải real number

Đây là invariant quan trọng.

Axiom không được coi:

```text
f32
```

là mathematical ℝ.

Có:

```text
NaN
+∞
-∞
-0
rounding
```

Do đó compiler không được tự động áp dụng:

```text
x + y == y + x
```

hoặc:

```text
(a + b) + c == a + (b + c)
```

cho floating point.

---

# 10. Floating-point semantics

Compiler phải có:

```text
FpEnvironment
```

gồm:

```text
rounding mode
exception behavior
NaN behavior
signed zero behavior
denormal behavior
```

Không nhất thiết tất cả đều configurable ở source v1, nhưng semantic model phải tồn tại.

---

# 11. Fast math

Không được âm thầm bật fast math.

Có explicit policy:

```text
@fast_math
```

hoặc function/profile:

```text
fast_math {
    ...
}
```

cho phép:

```text
reassociation
approximate transcendental
ignore signed zero
relaxed NaN handling
```

tùy mức độ.

Ví dụ:

```text
@fast_math
fn dot(...)
```

cho phép vectorizer thực hiện reduction aggressive hơn.

---

# 12. Numerical contract

Task 365 đã có:

```text
Strict
Relaxed
Approximate
```

Numeric engine phải formalize chúng.

### Strict

Giữ semantics floating-point nghiêm ngặt.

### Relaxed

Cho phép một số reassociation/target-specific transformation.

### Approximate

Cho phép approximation đã được định nghĩa.

Compiler không được tự chuyển:

```text
Strict → Relaxed
```

chỉ vì optimization nhanh hơn.

---

# 13. F16 và BF16

Axiom nên hỗ trợ semantic type:

```text
f16
bf16
```

nếu target/backend hỗ trợ.

Nhưng:

```text
f16
```

và:

```text
bf16
```

không được coi là cùng type.

Chúng có:

```text
different precision
different exponent/mantissa
different numerical behavior
```

---

# 14. Hardware support

Nếu CPU không có native `f16` arithmetic:

```text
f16 + f16
```

vẫn phải có semantics.

Compiler có thể lower thành:

```text
f32 conversion
compute
f16 conversion
```

hoặc library emulation.

Như vậy:

> Type semantics độc lập hardware capability.

---

# 15. Quantized numeric types

AI cần:

```text
i4
u4
i8
u8
```

nhưng không nhất thiết đưa tất cả thành ordinary scalar machine types.

Nên có semantic extension:

```text
quant<T, Scale, ZeroPoint>
```

hoặc library:

```text
QInt8
QUInt8
```

Compiler có thể nhận biết metadata:

```text
scale
zero_point
range
```

và tối ưu tensor kernels.

---

# 16. Packed numeric types

Không nhầm:

```text
i4
```

với:

```text
packed_i4x8
```

Một cái là scalar semantic type.

Một cái là packed representation.

Compiler cần distinction:

```text
ScalarType
PackedType
VectorType
TensorType
```

---

# 17. Complex numbers

Không cần primitive:

```text
complex64
complex128
```

trong Core.

Library có thể định nghĩa:

```text
struct Complex<T> {
    re: T
    im: T
}
```

với operators:

```text
+
-
*
/
```

Compiler vẫn có thể optimize thành native complex instructions nếu target hỗ trợ.

Đây là ví dụ điển hình của:

> abstraction without mandatory runtime representation.

---

# 18. Fixed-point

Có thể:

```text
Fixed<i32, 16>
```

nghĩa:

```text
16 fractional bits
```

Compiler hiểu arithmetic semantics nhưng representation là integer.

Ví dụ:

```text
Fixed<i32, 16>
```

có:

```text
storage = i32
scale = 2^-16
```

Không cần runtime metadata cho scale vì scale là compile-time parameter.

---

# 19. Decimal

`Decimal` không nên là Core primitive.

Library có thể định nghĩa:

```text
Decimal<Precision, Scale>
```

hoặc implementation-specific representation.

Điều này giữ Core nhỏ nhưng không hạn chế financial/scientific applications.

---

# 20. Rational

Tương tự:

```text
Rational<i64>
```

có thể là:

```text
struct Rational<T> {
    numerator: T
    denominator: T
}
```

Compiler có thể inline toàn bộ abstraction.

---

# 21. Mathematical constants

Compiler/comptime nên hỗ trợ:

```text
comptime PI
comptime E
comptime SQRT_2
```

nhưng không nhất thiết phải là compiler keywords.

Standard numeric library cung cấp:

```text
math.pi
math.e
```

Comptime evaluation cho phép:

```text
const x = sin(math.pi / 4);
```

nếu function được phép chạy trong comptime.

---

# 22. Transcendental functions

Các hàm:

```text
sin
cos
tan
exp
log
sqrt
pow
```

phải có numerical contract.

Ví dụ:

```text
sqrt(f32)
```

không đảm bảo bit-identical giữa mọi architecture nếu profile cho phép approximate behavior.

Nếu cần reproducibility:

```text
@strict_fp
```

hoặc library function tương ứng.

---

# 23. Vector + Numeric integration

Task 366 có:

```text
vec<f32, N>
```

Numeric engine phải định nghĩa operator semantics:

```text
vec + vec
vec * scalar
vec * vec
dot
reduce_sum
```

Nhưng không nên mặc định:

```text
vec * vec = dot
```

Vì:

```text
elementwise multiplication
```

và:

```text
dot product
```

là hai phép toán khác nhau.

---

# 24. Matrix

Matrix nên là library abstraction:

```text
Matrix<T, M, N>
```

có thể có representation:

```text
row-major
column-major
blocked
packed
```

Compiler không nên hard-code một layout duy nhất.

Layout trở thành type/attribute khi observable:

```text
Matrix<T, M, N, Layout>
```

hoặc library policy.

---

# 25. Tensor

Đây là phần quan trọng với AI.

Không nên làm:

```text
Tensor
```

thành Core primitive.

Nên có generic library abstraction:

```text
Tensor<T, Shape, Layout, Device>
```

Ví dụ:

```text
Tensor<f32, [1, 224, 224, 3], GPU>
```

Compiler có thể thấy:

```text
shape
dtype
layout
storage domain
```

ở compile time.

---

# 26. Shape là type-level information

Có thể:

```text
Tensor<f32, [M, N]>
```

và compiler biết:

```text
M × N
```

Nếu:

```text
Matrix<A, M, N>
Matrix<B, N, K>
```

thì:

```text
matmul(A, B)
```

trả:

```text
Matrix<T, M, K>
```

Compiler reject:

```text
Matrix<T, M, N>
×
Matrix<T, X, K>
```

khi:

```text
N != X
```

nếu các dimensions compile-time known.

---

# 27. Dynamic shapes

Không phải shape nào cũng biết compile-time.

Cho phép:

```text
Tensor<f32, dynamic_shape>
```

Khi đó compiler/runtime phải thực hiện:

```text
shape check
```

nhưng vẫn giữ:

```text
dtype
ownership
storage domain
```

an toàn.

---

# 28. Shape specialization

Comptime có thể specialize:

```text
Tensor<f32, [128, 128]>
```

thành kernel tối ưu.

Nhưng:

```text
Tensor<f32, [dynamic, dynamic]>
```

vẫn chạy được.

Compiler có thể tạo:

```text
generic kernel
specialized kernel
```

và runtime dispatch.

---

# 29. Automatic differentiation foundation

Axiom không cần đưa AD vào Core syntax.

Nhưng Numeric engine phải không ngăn:

```text
Dual<T>
```

hoặc:

```text
Dual<T, N>
```

library type.

Ví dụ:

```text
struct Dual<T> {
    value: T
    derivative: T
}
```

Nếu operators được generic:

```text
fn square<T: Numeric>(x: T) -> T {
    x * x
}
```

thì `Dual<f32>` có thể tự động hoạt động.

Compiler có thể inline toàn bộ.

---

# 30. Symbolic numeric computation

Tương tự:

```text
Symbol<T>
```

có thể được library xây dựng.

Không cần compiler hiểu symbolic algebra trong Core.

Comptime/reflection sau này có thể hỗ trợ tối ưu.

---

# 31. Numerical reduction

Reduction:

```text
sum
product
min
max
dot
norm
```

phải có explicit numerical semantics.

Ví dụ:

```text
sum(view<f32>)
```

không mặc định được reorder tùy ý.

Parallel reduction có thể:

```text
(a+b)+c
```

thay bằng:

```text
a+(b+c)
```

chỉ khi numerical contract cho phép.

---

# 32. Deterministic numerical mode

Scientific/AI workloads đôi khi cần reproducibility.

Axiom nên có profile:

```text
@deterministic
```

đảm bảo các operation thuộc contract không phụ thuộc:

```text
thread scheduling
GPU lane order
SIMD reduction order
```

Compiler có thể phải trả cost performance.

Đây là trade-off explicit.

---

# 33. Math error handling

Không dùng exception mặc định.

Ví dụ:

```text
sqrt_checked(x)
```

có thể:

```text
Result<f64, MathError>
```

Trong khi:

```text
sqrt(x)
```

theo IEEE semantics có thể trả:

```text
NaN
```

Đây là distinction:

```text
numerical domain error
vs
program failure
```

---

# 34. Numeric ABI

Numeric ABI phải định nghĩa:

```text
scalar layout
vector layout
complex layout
aggregate layout
calling convention
return convention
alignment
```

Ví dụ `Complex<f32>` có thể ABI-compatible với:

```text
{ f32, f32 }
```

nhưng compiler không được mặc định expose representation nếu type không `repr(C)`.

---

# 35. Numeric specialization

Generic:

```text
fn dot<T: Float>(...)
```

có thể generate:

```text
dot_f32
dot_f64
dot_f16
bf16
```

và target-specific:

```text
AVX2
AVX512
NEON
SVE
GPU
```

Compiler có thể chọn implementation dựa trên:

```text
type
target
numerical contract
shape
alignment
```

---

# 36. Numeric cost model

Thêm:

```text
NumericCostModel
```

để ước lượng:

```text
latency
throughput
precision conversion
memory traffic
vector width
FMA availability
transcendental cost
GPU transfer
```

Ví dụ:

```text
f32 → f64
```

có cost khác nhau trên từng target.

---

# 37. FMA

Compiler có thể biến:

```text
a * b + c
```

thành:

```text
fma(a, b, c)
```

chỉ khi numerical contract cho phép.

Trong strict floating-point mode, nếu kết quả khác semantics yêu cầu thì không được tự động fuse.

---

# 38. Approximate functions

Library có thể cung cấp:

```text
fast_sin
fast_cos
fast_exp
fast_log
```

thay vì bắt compiler đoán.

Như vậy programmer có lựa chọn:

```text
sin(x)
```

hoặc:

```text
fast_sin(x)
```

và compiler vẫn có thể inline/vectorize cả hai.

---

# 39. Numeric safety và overflow proofs

Compiler có thể chứng minh:

```text
0 <= x < 100
0 <= y < 100
```

nên:

```text
x + y
```

không overflow `u8`.

Sau đó bỏ runtime check.

Đây là ví dụ quan trọng của Axiom philosophy:

```text
Source:
    safe arithmetic

Compiler:
    prove safe

Machine:
    raw fast instruction
```

---

# 40. CompilerDB

Task 368 bổ sung:

```text
NumericDB
NumericTypeDB
IntegerTypeDB
FloatTypeDB
IntegerSemanticsDB
FloatSemanticsDB
OverflowDB
NumericConversionDB
NumericCastDB
BitCastDB
RoundingDB
FloatingPointEnvironmentDB
FastMathDB
NumericalContractDB
PrecisionDB
QuantizationDB
FixedPointDB
ComplexDB
RationalDB
DecimalDB
NumericConstantDB
MathFunctionDB
TranscendentalDB
NumericReductionDB
NumericVectorDB
NumericMatrixDB
NumericTensorDB
ShapeDB
ShapeConstraintDB
DynamicShapeDB
NumericSpecializationDB
NumericCostModelDB
NumericAbiDB
NumericDeterminismDB
NumericProofDB
```

---

# 41. MIR additions

Bổ sung semantic operations:

```text
INT_ADD
INT_SUB
INT_MUL
INT_DIV

INT_CHECKED_ADD
INT_CHECKED_SUB
INT_CHECKED_MUL

INT_WRAPPING_ADD
INT_WRAPPING_SUB
INT_WRAPPING_MUL

INT_SATURATING_ADD
INT_SATURATING_SUB
INT_SATURATING_MUL

FLOAT_ADD
FLOAT_SUB
FLOAT_MUL
FLOAT_DIV
FLOAT_FMA

FLOAT_SQRT
FLOAT_EXP
FLOAT_LOG
FLOAT_SIN
FLOAT_COS

NUMERIC_CAST
NUMERIC_CHECKED_CAST
NUMERIC_SATURATING_CAST
BIT_CAST

NUMERIC_REDUCE
NUMERIC_DOT
NUMERIC_CONVERT_PRECISION
```

Compiler backend sau đó mới lower xuống instruction.

---

# 42. Proof structures

Numeric verification cần:

```text
NumericProof
OverflowProof
ConversionProof
PrecisionProof
FloatingPointProof
ReductionProof
DeterminismProof
ShapeProof
```

Ví dụ:

```text
OverflowProof {
    operation: ADD
    type: u32
    range_a: [0, 100]
    range_b: [0, 200]
    max: 300
    representable: true
}
```

Compiler có thể loại bỏ check.

---

# 43. Invariants

### `ANUM-01`
Mỗi numeric primitive có semantics xác định độc lập target.

### `ANUM-02`
Compiler không được biến signed overflow thành UB.

### `ANUM-03`
Wrapping arithmetic có semantics modulo rõ ràng.

### `ANUM-04`
Checked arithmetic phải báo overflow theo Result/Option semantics.

### `ANUM-05`
Saturating arithmetic phải clamp theo representable range.

### `ANUM-06`
Numeric conversion không được implicit gây mất thông tin mà không có semantic permission.

### `ANUM-07`
Bitcast khác numeric conversion.

### `ANUM-08`
Floating-point không được coi là mathematical real.

### `ANUM-09`
NaN, infinity và signed zero phải được bảo toàn theo floating-point profile.

### `ANUM-10`
Compiler không được tự ý reassociate floating-point strict operations.

### `ANUM-11`
Fast-math transformation phải nằm trong explicit numerical contract.

### `ANUM-12`
F16 và BF16 là các numeric types khác nhau.

### `ANUM-13`
Numeric type semantics không phụ thuộc việc target có hardware support hay không.

### `ANUM-14`
Unsupported hardware phải có valid lowering hoặc compile-time error.

### `ANUM-15`
Vector arithmetic phải giữ lane semantics.

### `ANUM-16`
Elementwise multiplication không đồng nghĩa dot product.

### `ANUM-17`
Parallel reduction không được tự ý thay đổi numerical semantics.

### `ANUM-18`
Floating-point associativity không được giả định.

### `ANUM-19`
Deterministic numerical mode phải kiểm soát reduction/order semantics thuộc contract.

### `ANUM-20`
Complex/Rational/Fixed/Decimal có thể được implement bằng library type mà không cần runtime hierarchy.

### `ANUM-21`
Numeric generic specialization phải giữ nguyên semantics của generic function.

### `ANUM-22`
Compile-time numeric parameters không tạo runtime metadata nếu không observable.

### `ANUM-23`
Shape constraints có thể được kiểm tra tại compile time khi đủ thông tin.

### `ANUM-24`
Dynamic shape phải được kiểm tra runtime khi compile-time proof không tồn tại.

### `ANUM-25`
Tensor type không phải Core runtime primitive bắt buộc.

### `ANUM-26`
Numeric cost model không được thay đổi observable numerical semantics.

### `ANUM-27`
FMA transformation phải tuân numerical contract.

### `ANUM-28`
Numeric optimization không được bypass ownership, bounds hoặc memory verification.

### `ANUM-29`
Target-specific numeric instructions phải có semantic-equivalence proof.

### `ANUM-30`
Numeric subsystem phải hỗ trợ CPU, SIMD, GPU và accelerator mà không tạo một numeric semantics riêng cho từng backend.

---

# 44. Vị trí sau task 368

Sau task này, ba tầng quan trọng đã nối với nhau:

```text
             Numeric Semantics
                    │
                    ▼
             Generic Algorithms
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
        Scalar     SIMD      Tensor
          │         │         │
          └────┬────┴────┬────┘
               ▼         ▼
              CPU       GPU
               │         │
               └────┬────┘
                    ▼
             Native Hardware
```

Đặc biệt, Axiom giờ có nền tảng để sau này xây:

```text
Tensor
Linear Algebra
BLAS-like API
FFT
Signal Processing
Image Processing
Automatic Differentiation
Neural Network
Quantization
Scientific Computing
```

mà **không cần nhồi các khái niệm này vào language core**.

Điểm kiến trúc quan trọng nhất của 368 là:

> **Axiom Core không cần biết AI là gì. Nhưng compiler phải hiểu đủ sâu numeric semantics để một thư viện AI có thể đạt hiệu năng native.**