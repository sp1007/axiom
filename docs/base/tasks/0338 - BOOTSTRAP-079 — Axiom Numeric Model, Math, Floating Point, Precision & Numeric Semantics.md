# BOOTSTRAP-079 — Axiom Numeric Model, Math, Floating Point, Precision & Numeric Semantics

**Trạng thái: FROZEN**

Mục tiêu của phần này là chốt một vấn đề rất nền tảng: **Axiom phải có semantics số học đủ chặt để compiler tối ưu mạnh, nhưng không biến mọi phép tính thành một hệ thống phức tạp.**

Nguyên tắc:

> **Numeric semantics phải xác định ở mức ngôn ngữ; representation và instruction do backend lựa chọn.**

Và:

> **Không được để “CPU đang dùng instruction gì” quyết định semantics của chương trình.**

---

# 1. Phân tầng numeric model

Axiom chia numeric thành:

```text
Language Core
├── Integer primitives
├── Floating-point primitives
└── basic numeric operators

Core Library
├── numeric traits
├── checked/wrapping/saturating operations
├── math primitives
└── numeric conversions

Standard Library
├── complex
├── decimal
├── random
├── statistics
└── higher-level math

Specialized libraries
├── bigint
├── arbitrary precision
├── tensor
├── symbolic math
└── scientific computing
```

Không đưa toàn bộ toán học vào Core.

---

# 2. Integer types

Core giữ:

```text
i8   i16   i32   i64
u8   u16   u32   u64

isize
usize
```

Đây là các **machine-oriented integer types**.

`isize/usize` phụ thuộc target pointer width.

---

# 3. `i128/u128`

Có thể hỗ trợ ở compiler/library sau, nhưng không cần coi là primitive machine-native trên mọi target.

Nếu target không có native 128-bit integer:

```text
i128
```

có thể lower thành:

```text
2 × i64
```

hoặc sequence tương đương.

Semantics vẫn giống nhau.

---

# 4. Integer overflow

Axiom không dùng mô hình C kiểu:

```text
signed overflow → undefined behavior
```

Đây là quyết định rất quan trọng.

Các phép toán có semantics rõ ràng:

```text
checked
wrapping
saturating
```

Ví dụ:

```ax
a.checked_add(b)
a.wrapping_add(b)
a.saturating_add(b)
```

---

# 5. Ordinary integer operators

Cần phân biệt:

```ax
a + b
```

với:

```ax
a.checked_add(b)
a.wrapping_add(b)
a.saturating_add(b)
```

Đề xuất:

**ordinary arithmetic là checked trong semantic model**, với failure được biểu diễn theo context/compiler-defined arithmetic failure mechanism.

Tuy nhiên, để tránh runtime overhead trong code đã chứng minh không overflow:

```text
compiler:
    prove no overflow
        ↓
    emit native add
```

Nếu không chứng minh được:

```text
checked path
```

Đây là hướng an toàn nhưng vẫn tối ưu tốt.

---

# 6. Nhưng checked arithmetic không nên biến mọi loop thành chậm

Ví dụ:

```ax
for i in 0..n {
    sum += values[i]
}
```

compiler có thể phân tích range:

```text
sum range
values range
loop bounds
```

Nếu overflow không thể xảy ra:

```text
checked add
     ↓
proof
     ↓
plain machine add
```

Không cần programmer viết unsafe.

---

# 7. Overflow failure

Arithmetic failure là một dạng runtime failure, nhưng không nên biến thành exception.

Có thể:

```text
checked arithmetic
    → Result/Option-like explicit operation
```

trong library APIs.

Còn ordinary operators có thể tuân theo build arithmetic profile:

```text
debug
    → checked/trap

release
    → vẫn cùng semantics
```

**Debug/release không được tự ý thay đổi language semantics.**

Do đó profile chỉ được thay đổi implementation strategy nếu observable behavior vẫn tương đương.

---

# 8. Wrapping arithmetic

Wrapping:

```ax
a.wrapping_add(b)
```

có semantic:

```text
mod 2^N
```

Ví dụ `u8`:

```text
255 + 1 → 0
```

Đây rất phù hợp với:

- cryptography
- hashing
- bit manipulation
- codecs
- DSP
- systems programming.

---

# 9. Saturating arithmetic

```ax
a.saturating_add(b)
```

với `u8`:

```text
250 + 20 → 255
```

với signed integer:

```text
MAX + 1 → MAX
MIN - 1 → MIN
```

Compiler có thể dùng native saturation instruction nếu target hỗ trợ.

---

# 10. Carry / borrow arithmetic

System/crypto code cần:

```text
add_with_carry
sub_with_borrow
```

Ví dụ:

```ax
let (r, carry) = add_carry(a, b, carry_in)
```

Đây nên là intrinsic/library primitive.

Không cần thêm operator mới vào language.

---

# 11. Integer division

Axiom phải định nghĩa rõ:

```text
division by zero
signed division overflow
negative division
remainder sign
```

Không để target ISA tự quyết định.

Đề xuất:

```text
division by zero → arithmetic trap/failure
```

và:

```text
remainder
```

theo truncation-toward-zero semantics cho signed integer.

---

# 12. Bit operations

Core/library hỗ trợ:

```text
and
or
xor
not
shift
rotate
count_ones
count_zeros
leading_zeros
trailing_zeros
bit_reverse
```

Compiler intrinsic có thể map trực tiếp:

```text
CLZ
CTZ
POPCNT
ROL
ROR
```

---

# 13. Shift semantics

Không cho phép shift amount bất hợp lệ trở thành undefined behavior.

Ví dụ:

```ax
x << n
```

phải có semantics xác định.

Đề xuất:

- checked operator → invalid shift traps/fails;
- wrapping shift APIs → mask shift count theo width.

Ví dụ:

```ax
x.wrapping_shl(n)
```

Điều này đặc biệt hữu ích khi compiler tối ưu bit-level code.

---

# 14. Integer conversion

Không tự động:

```text
i64 → i32
u64 → u8
```

nếu có khả năng mất dữ liệu.

Dùng:

```ax
x as i32
```

cho explicit conversion.

Nhưng `as` phải có semantics rõ ràng theo loại conversion.

---

# 15. Cast và bitcast

Phân biệt:

```text
CAST
BITCAST
```

### Cast

Thay đổi numeric interpretation:

```ax
let y = x as f32
```

### Bitcast

Giữ nguyên bit pattern:

```ax
let y = bitcast<u32>(x)
```

Bitcast yêu cầu:

```text
same size
valid alignment
valid target representation
```

nếu không → compile error hoặc unsafe API tùy trường hợp.

---

# 16. Numeric newtypes

Axiom cho phép:

```ax
struct Meters(f64)
struct Seconds(f64)
struct UserId(u64)
```

Hai type có thể cùng representation:

```text
f64
```

nhưng semantic khác nhau.

Không implicit convert:

```text
Meters + Seconds
```

Đây là một lợi thế lớn cho correctness mà không có runtime overhead.

---

# 17. Floating-point primitive

Core:

```text
f32
f64
```

Đủ cho baseline.

Các loại khác:

```text
f16
bf16
fp8
```

có thể được compiler/library bổ sung khi target support đủ tốt.

Không cần đưa toàn bộ vào semantic Core v1.

---

# 18. Floating-point không phải Real

Axiom không giả định:

```text
f32 == mathematical real
```

Floating point có:

```text
finite values
±0
±∞
NaN
rounding
finite precision
```

Do đó compiler phải giữ semantics IEEE-like ở mức phù hợp với target.

---

# 19. NaN

Axiom phải coi NaN là một giá trị đặc biệt.

Không được giả định:

```text
NaN == NaN
```

là true.

So sánh thông thường tuân floating-point semantics.

Library có thể cung cấp:

```text
is_nan
is_finite
is_infinite
is_normal
```

---

# 20. Signed zero

Phải giữ distinction:

```text
+0.0
-0.0
```

khi observable theo floating semantics.

Compiler không được tự động biến:

```text
-0.0 → +0.0
```

nếu điều đó làm thay đổi observable behavior.

---

# 21. Infinity

Các phép toán với:

```text
+∞
-∞
```

theo floating-point semantics.

Compiler không được coi infinity như integer overflow.

---

# 22. Rounding modes

Axiom cần phân biệt:

```text
default deterministic rounding
```

với:

```text
dynamic FP environment
```

Đề xuất Core mặc định sử dụng rounding mode xác định theo Axiom numeric contract, trong khi dynamic hardware rounding modes là system-level feature.

Lý do:

```text
global mutable FP environment
```

làm optimization cực kỳ khó.

---

# 23. FP environment

Nếu hỗ trợ:

```text
set_rounding_mode(...)
get_rounding_mode(...)
```

thì compiler phải coi nó là observable state.

Không được:

```text
hoist/reorder
```

FP operations qua boundary nếu semantics bị thay đổi.

Do đó đây là system/numeric library capability.

---

# 24. Exceptions / FP flags

Hardware có:

```text
invalid
divide-by-zero
overflow
underflow
inexact
```

Axiom không mặc định biến chúng thành exception.

Nếu cần:

```text
FPStatus
```

là explicit numeric/system API.

---

# 25. Fast floating point

Axiom có hai semantic profile:

```text
Strict FP
Relaxed FP
```

Nhưng **Strict là mặc định**.

Relaxed FP phải được explicit.

Ví dụ conceptually:

```ax
@fast_math
fn calculate(...) -> f32
```

Nó cho compiler quyền:

```text
reassociation
approximation
fused operations
ignoring some NaN/sign-zero distinctions
```

nhưng phạm vi phải được định nghĩa chính xác trong spec.

---

# 26. FMA

Một câu hỏi quan trọng:

```text
a * b + c
```

có được tự động thành:

```text
fma(a,b,c)
```

không?

Với strict semantics:

**chỉ khi Axiom semantic model cho phép hoặc kết quả observable tương đương.**

Với relaxed/fast math:

```text
FMA allowed
```

Điều này tránh việc compiler âm thầm thay đổi numeric behavior.

---

# 27. Approximate math

Các hàm:

```text
sin
cos
exp
log
sqrt
```

không nhất thiết có một implementation duy nhất.

Cần phân biệt:

```text
strict_math
fast_math
approx_math
```

Ví dụ:

```text
sqrt
```

có thể map native instruction.

Trong khi:

```text
sin
```

có thể dùng optimized library implementation.

---

# 28. Deterministic math

Nếu ứng dụng yêu cầu reproducibility:

```text
deterministic numeric mode
```

cần kiểm soát:

```text
rounding
reduction order
parallel execution
math library version
target-specific approximations
```

Đặc biệt quan trọng cho:

- simulation
- tests
- ML experiments
- scientific computing.

---

# 29. Determinism không đồng nghĩa bit-identical mọi CPU

Axiom không nên hứa:

```text
same source
→ exact same FP bits on every CPU
```

nếu sử dụng target-specific math.

Muốn stronger guarantee cần explicit deterministic numeric library/profile.

---

# 30. `f16`

`f16` hữu ích cho:

- ML
- graphics
- storage bandwidth.

Nhưng nhiều CPU không xử lý f16 như native scalar arithmetic.

Do đó:

```text
f16 semantic type
```

có thể lower thành:

```text
conversion
SIMD
special instruction
memory representation
```

tùy target.

---

# 31. `bf16`

`bf16` khác `f16` về precision/exponent.

Không được coi:

```text
f16 ≈ bf16
```

về semantics.

Chúng là distinct numeric types.

---

# 32. Quantized integers

Các type như:

```text
i4
u4
i2
u2
```

nên là specialized numeric/storage types.

Không nhất thiết phải là normal scalar machine integers.

Ví dụ:

```text
u4 × u4
```

có thể pack nhiều elements vào một byte/word.

---

# 33. Complex number

Không cần Core primitive.

Library:

```ax
Complex<f32>
Complex<f64>
```

với:

```text
real
imag
abs
arg
conj
```

Compiler có thể scalarize hoặc vectorize.

---

# 34. Decimal

Decimal nên là library type:

```text
Decimal
```

cho:

- tiền tệ
- accounting
- exact decimal computation.

Không dùng binary floating point cho semantic decimal applications.

---

# 35. Fixed-point

System/DSP/embedded code có thể cần:

```text
Fixed<I,F>
```

với:

```text
I = integer bits
F = fractional bits
```

Đây là candidate rất tốt cho const generics.

Ví dụ conceptually:

```ax
Fixed<i32, 16>
```

Compiler có thể erase abstraction hoàn toàn.

---

# 36. Big integer

`BigInt` không nên là Core primitive.

Library:

```text
BigInt
BigUint
```

có dynamic storage.

Ownership/allocator model vẫn áp dụng bình thường.

Compiler không cần biết toàn bộ algorithm.

---

# 37. Arbitrary precision

Có thể:

```text
BigInt
BigFloat
Decimal
Rational
```

nhưng đây là library-level.

Đặc biệt:

```text
BigInt
```

không được giả định:

```text
Copy
```

vì duplicate có thể tốn chi phí lớn.

---

# 38. Numeric traits

Type system nên có traits:

```text
Numeric
Integer
Signed
Unsigned
Float
Real
Complex
```

nhưng tránh tạo hierarchy quá sâu.

Traits chỉ mô tả capabilities.

---

# 39. Operator traits

Các operator:

```text
+
-
*
/
%
```

có thể map qua trait mechanism.

Compiler có thể special-case primitive arithmetic để tránh abstraction overhead.

Ví dụ:

```ax
a + b
```

không nhất thiết tạo dynamic dispatch.

---

# 40. Generic numeric code

Có thể viết:

```ax
fn square<T: Numeric>(x: T) -> T {
    x * x
}
```

Compiler monomorphization:

```text
square<i32>
square<f32>
square<Decimal>
```

và optimize từng specialization.

---

# 41. Generic numeric specialization

Đối với:

```text
T = f32
```

compiler có thể biết:

```text
SIMD-compatible
FMA-compatible
```

và tối ưu.

Đối với:

```text
T = BigInt
```

sẽ gọi library implementation.

Không cần thay đổi source.

---

# 42. Numeric promotion

Không nên có C-style promotion hỗn loạn.

Ví dụ:

```text
u8 + i32
```

không tự âm thầm tạo một type mà programmer không biết.

Có thể có deterministic promotion rules cho các trường hợp an toàn, nhưng conversion mất thông tin phải explicit.

---

# 43. Mixed float/integer

Không implicit:

```text
i32 + f32
```

→ compiler phải yêu cầu conversion.

Ví dụ:

```ax
x as f32 + y
```

Điều này tránh nhiều bug numeric.

---

# 44. Constant evaluation

Comptime phải tính được:

```ax
const PI: f64 = ...
const TABLE = ...
```

Compiler có thể evaluate numeric expressions ở compile time.

Nhưng:

```text
comptime numeric semantics
```

phải giống runtime semantics.

---

# 45. Compile-time overflow

Nếu:

```ax
const x: u8 = 255 + 1
```

thì compiler phải báo lỗi hoặc áp dụng semantics explicit tương ứng.

Không được:

```text
compiler version A → 0
compiler version B → error
```

một cách tùy tiện.

---

# 46. Compile-time floating point

Comptime FP phải cố gắng giữ cùng semantic model với runtime.

Tuy nhiên nếu compiler host không có exact target behavior:

```text
target-specific FP intrinsic
```

phải được đánh dấu không thể evaluate hoặc dùng target-aware implementation.

Không được silently produce host-dependent semantics.

---

# 47. Numeric literals

Literal nên hỗ trợ:

```text
123
123u32
123i64
1.25
1.25f32
0xff
0b1010
0o755
1_000_000
```

Compiler suy luận type khi context rõ.

---

# 48. Literal overflow

```ax
let x: u8 = 300
```

→ compile error.

Không silently truncate.

Nếu muốn:

```ax
let x = 300 as u8
```

thì conversion semantics phải rõ.

---

# 49. Literal exactness

Decimal floating literal:

```ax
0.1
```

không phải binary-exact `0.1`.

Compiler phải parse theo Axiom-defined decimal-to-binary conversion rule.

Không phụ thuộc locale.

---

# 50. Hex floating literals

Có thể hỗ trợ:

```text
0x1.8p+2
```

ở language/library syntax nếu cần exact FP construction.

Điều này hữu ích cho:

- compiler tests
- numerical work
- low-level code.

---

# 51. Numeric equality

Integer:

```text
==
```

có semantic value equality.

Floating:

```text
==
```

tuân FP equality.

Library có thể cung cấp:

```text
approx_equal
ulp_distance
```

cho numerical applications.

Không thay đổi meaning của `==`.

---

# 52. Hashing floating values

Hash của:

```text
NaN
+0
-0
```

cần contract rõ.

Hash equality phải tương thích với equality semantics.

Nếu cần bitwise hashing:

```text
bit_hash
```

là API khác.

---

# 53. Numeric ordering

Floating `NaN` khiến total ordering phức tạp.

Do đó:

```text
Ord<f32>
```

không nên giả định có total order tự nhiên.

Có thể có:

```text
PartialOrd
TotalFloat
```

với explicit NaN ordering.

---

# 54. Sorting floating values

Library có thể cung cấp:

```text
sort_partial
sort_total
```

để programmer chọn semantics.

Không tự quyết định NaN ordering.

---

# 55. Random numbers

Random không thuộc Core.

Standard library:

```text
Random
Rng
```

phân biệt:

```text
pseudo-random
cryptographic random
system random
```

Không dùng một API duy nhất cho mọi trường hợp.

---

# 56. Reproducible random

Comptime/build reproducibility đã có:

```text
Random
```

là external capability.

Runtime RNG có thể explicit seed:

```ax
let rng = Rng.seeded(12345)
```

để reproducible simulations.

---

# 57. Crypto arithmetic

Crypto cần:

```text
wrapping
constant-time operations
fixed-width integer
bit operations
```

Axiom numeric model phải cho phép library viết được chúng mà không bị compiler “tối ưu sai”.

Có thể có system/compiler hints cho constant-time regions sau này.

---

# 58. Constant-time

Không nên đưa một `@constant_time` semantic system quá lớn vào Core v1.

Nhưng compiler phải tránh tự ý biến explicit constant-time primitive thành behavior có observable timing contract bị phá nếu library dùng primitive được thiết kế cho mục đích này.

Crypto library có thể cung cấp specialized operations.

---

# 59. Numeric memory representation

Numeric type semantics khác memory representation.

Ví dụ:

```text
f32
```

có:

```text
semantic value
```

và:

```text
IEEE binary32 representation
```

được target representation contract xác định.

Không được confuse:

```text
value equality
```

với:

```text
bit equality
```

---

# 60. Endianness

Numeric value không có “endianness” ở semantic level.

Endianness chỉ xuất hiện khi:

```text
memory representation
serialization
FFI
device protocol
```

API:

```text
to_le
to_be
from_le
from_be
```

hoặc equivalent.

---

# 61. Numeric serialization

Không được:

```text
write(memory_of(f32))
```

và giả định portable file format.

Serialization phải explicit.

---

# 62. SIMD integration

Các numeric types phù hợp có thể làm:

```text
simd<f32,N>
simd<i32,N>
```

với semantics được định nghĩa từ scalar.

`f16/bf16` chỉ được SIMD nếu compiler/backend có representation support.

---

# 63. Tensor integration

Tensor library có thể:

```text
Tensor<f32>
Tensor<f16>
Tensor<bf16>
Tensor<i8>
```

nhưng:

```text
Tensor<Decimal>
Tensor<BigInt>
```

cũng có thể tồn tại nếu library implementation hỗ trợ.

Core không cần biết Tensor.

---

# 64. Matrix multiplication numeric contract

Ví dụ:

```text
f16 × f16 → f32
```

cần biểu diễn rõ:

```text
input type
input type
accumulation type
output type
```

Không dựa vào implicit promotion.

---

# 65. Numeric optimization hierarchy

Compiler có thể:

```text
scalar
 ↓
constant folding
 ↓
algebraic simplification
 ↓
strength reduction
 ↓
SIMD
 ↓
FMA
 ↓
target intrinsic
```

nhưng mỗi bước phải preserve numeric semantics.

---

# 66. Algebraic optimization không được tùy tiện

Không được luôn luôn biến:

```text
x * 0 → 0
```

với floating point.

Vì:

```text
NaN
∞
-0
```

có thể làm kết quả khác.

Do đó optimizer phải có **Numeric Semantic Facts**.

---

# 67. Integer algebraic optimization

Integer wrapping cũng cần cẩn thận.

Ví dụ:

```text
(x + y) - y
```

có thể không bằng:

```text
x
```

nếu semantics checked và overflow có thể xảy ra.

Nếu compiler chứng minh no-overflow:

```text
safe simplification
```

Nếu wrapping semantics:

```text
modular algebra
```

có thể áp dụng luật tương ứng.

---

# 68. Range analysis

OptIR đã có:

```text
RangeInfo
```

Nó trở thành nền tảng cho numeric optimization:

```text
range
→ overflow proof
→ bounds elimination
→ branch elimination
→ vectorization
```

Đây là điểm kết nối trực tiếp giữa BOOTSTRAP-079 và BOOTSTRAP-056.

---

# 69. Numeric effect model

Compiler cần phân biệt:

```text
Pure numeric
FP environment
volatile
atomic
IO
foreign math
```

Ví dụ:

```text
sin(x)
```

có thể là pure semantic operation nhưng implementation có thể gọi runtime/library.

Optimizer vẫn có thể inline/specialize nếu contract cho phép.

---

# 70. Math library ABI

Axiom không cần phụ thuộc libc `libm`.

Long-term:

```text
axiom.math
```

có thể tự triển khai:

```text
sqrt
sin
cos
exp
log
pow
atan2
...
```

và compiler/linker chỉ link những function thực sự dùng.

Điều này phù hợp mục tiêu:

> không có mandatory third-party runtime/library dependency.

---

# 71. Target math implementation

Compiler có thể chọn:

```text
native instruction
Axiom math implementation
optimized polynomial
vector math
GPU implementation
```

miễn semantics contract được giữ.

---

# 72. Vector math

Library có thể cung cấp:

```text
sin(simd<f32,N>)
cos(simd<f32,N>)
exp(simd<f32,N>)
```

Compiler có thể lower thành vector math.

Strictness phải được giữ theo numeric profile.

---

# 73. GPU numeric semantics

GPU numeric execution phải dùng cùng semantic foundations:

```text
integer
float
overflow
NaN
rounding
atomic
```

nhưng target-specific limitations phải explicit.

Không tạo một numeric language riêng cho GPU.

---

# 74. Cross-target numeric differences

Axiom không giả định mọi target có cùng:

```text
instruction
precision
denormal handling
FP performance
```

Nhưng language semantics vẫn phải ổn định.

Target implementation chỉ được khác khi specification cho phép implementation-defined behavior.

---

# 75. Implementation-defined numeric behavior

Một số thứ có thể target-dependent:

```text
performance
instruction selection
extended precision
FP environment details
SIMD width
hardware acceleration
```

Nhưng phải phân biệt:

```text
semantic difference
```

với:

```text
implementation detail
```

---

# 76. Precision annotations

Không cần:

```text
@precision(...)
```

trong Core v1.

Type đã là precision contract:

```text
f32
f64
f16
bf16
```

Algorithm-specific precision thuộc library abstraction.

---

# 77. Numeric conversion API

Library nên có các dạng:

```text
try_convert
saturating_convert
wrapping_convert
exact_convert
```

Ví dụ:

```ax
x.try_as<u8>()
x.saturating_as<u8>()
```

Không ép một `as` syntax phải gánh tất cả semantics.

---

# 78. Exact numeric conversion

Ví dụ:

```text
f64 → i32
```

có thể thất bại nếu:

```text
NaN
∞
fractional
out of range
```

`exact_convert` phải kiểm tra đầy đủ.

---

# 79. Numeric literals + generic inference

Ví dụ:

```ax
let x = 10
```

không nên mặc định thành một type quá lớn chỉ vì compiler tiện.

Context:

```ax
let x: u8 = 10
```

→ `u8`.

Generic context:

```ax
max(10, 20)
```

→ inference phải deterministic.

Nếu không đủ thông tin:

```text
compile diagnostic
```

thay vì đoán tùy compiler version.

---

# 80. Const generic numeric values

Const generic hỗ trợ:

```text
N: usize
```

hoặc scalar compile-time values.

Ví dụ:

```ax
simd<f32, 8>
Array<u8, 1024>
```

Không mở rộng thành dependent type system.

---

# 81. Numeric layout in structs

Numeric fields có thể được reorder bởi default struct layout.

Ví dụ:

```ax
struct Data {
    a: u8
    b: f64
}
```

không đảm bảo C-compatible layout.

Nếu cần:

```ax
@repr(C)
```

---

# 82. Atomic numeric types

Core/library:

```text
Atomic<u32>
Atomic<i64>
```

khi target support.

Semantics:

```text
numeric value
+
atomic access model
```

không phải SIMD semantics.

---

# 83. Atomic floating point

Không mặc định hỗ trợ:

```text
Atomic<f32>
```

trên mọi target.

Nếu target/library có implementation:

```text
compare_exchange loop
```

hoặc hardware primitive.

Semantic availability phải explicit.

---

# 84. Numeric error taxonomy

Phân biệt:

```text
integer overflow
division by zero
invalid conversion
FP NaN
FP infinity
allocation failure for BigInt
math domain error
```

Không gom tất cả thành một “number error”.

---

# 85. Math domain errors

Ví dụ:

```text
sqrt(-1)
log(-1)
```

với `f64`.

Nếu math API dùng IEEE behavior:

```text
NaN
```

thì không nhất thiết trả `Result`.

Nếu API yêu cầu domain checking:

```text
sqrt_exact
```

có thể trả:

```text
Result
```

Semantics do API chọn.

---

# 86. Numeric API design

Nguyên tắc:

```text
primitive operation
    → direct machine semantics

checked operation
    → explicit failure

approximate operation
    → explicit approximation contract

exact operation
    → explicit correctness contract
```

Không overload một function với quá nhiều hidden behavior.

---

# 87. Compiler numeric facts

Compiler nên lưu:

```text
NumericFacts {
    bit_width
    signedness
    range
    overflow_mode
    fp_kind
    rounding
    fast_math
    vectorizable
    target_features
}
```

OptIR sử dụng chúng.

---

# 88. Numeric proof

Verifier/optimizer có thể chứng minh:

```text
NoOverflow
NoDivisionByZero
Finite
NonNaN
Aligned
RangeWithin
```

Các facts này:

```text
verified fact
```

không phải programmer assertion.

Optimizer không được tự tạo fact nếu chưa chứng minh.

---

# 89. Numeric optimization explanation

Axiom nên hỗ trợ:

```text
axiom explain numeric
```

Ví dụ:

```text
operation:
    checked_add

optimized:
    native ADD

reason:
    range analysis proves result ∈ i32
```

Hoặc:

```text
FMA not applied
reason:
    strict floating-point semantics
```

Điều này rất hữu ích cho AI-assisted development.

---

# 90. BigInt optimization

Compiler có thể inline small BigInt operations nếu library representation/ABI cho phép.

Nhưng không được giả định:

```text
BigInt = primitive
```

Library vẫn sở hữu semantic implementation.

---

# 91. Decimal optimization

Compiler có thể recognize:

```text
Decimal
```

và optimize nếu type/library cung cấp intrinsic contracts.

Nhưng semantics decimal vẫn thuộc type/library.

---

# 92. Rational

Có thể:

```text
Rational<Int>
```

với numerator/denominator.

Normalization:

```text
gcd
sign
zero denominator
```

là library semantics.

Không cần Core support.

---

# 93. Numeric algorithm contracts

Các algorithm library có thể có:

```text
exact
approximate
deterministic
parallel
fast
```

contracts.

Nhưng đây không phải một global effect system.

---

# 94. Compiler và hardware differences

Compiler không được biến:

```text
CPU có FMA
```

thành:

```text
Axiom semantics = FMA
```

Hardware là implementation target.

---

# 95. Numeric testing

Conformance suite phải có:

```text
integer overflow
division
conversion
NaN
infinity
signed zero
rounding
FMA
reduction
SIMD equivalence
comptime/runtime equivalence
```

Đặc biệt có golden tests cho edge cases.

---

# 96. Differential numeric testing

Có thể so sánh:

```text
reference interpreter
vs
native O0
vs
native O3
vs
SIMD
vs
GPU
```

với numeric tolerance phù hợp.

Nhưng exact operations phải exact.

---

# 97. Numeric semantics và optimization levels

Phải giữ:

```text
-O0
-O1
-O2
-O3
-LTO
-PGO
```

cùng semantic result.

Chỉ khác nếu programmer explicit chọn relaxed/approximate numeric contract.

---

# 98. Numeric semantics và reproducibility

Semantic fingerprint cần bao gồm các numeric contracts có ảnh hưởng:

```text
FP mode
math mode
target
target features
numeric library version
```

nếu chúng ảnh hưởng generated result.

---

# 99. Numeric Core boundary

Core chỉ cần giữ:

```text
bool
integer
float
numeric operators
conversion
basic bit operations
```

Không thêm:

```text
BigInt
Decimal
Complex
Tensor
Matrix
Rational
```

vào Core.

Điều này giữ Core đủ mạnh nhưng không bị phình.

---

# 100. Frozen invariants

## Numeric Model — `ANUM-20..100`

**ANUM-20** — Numeric semantics are defined independently of machine instruction selection.

**ANUM-21** — Integer primitives have explicit fixed-width semantics.

**ANUM-22** — `isize` and `usize` are target-sized integers.

**ANUM-23** — Signed integer overflow is not C-style undefined behavior.

**ANUM-24** — Checked arithmetic has explicit failure semantics.

**ANUM-25** — Wrapping arithmetic has modular semantics.

**ANUM-26** — Saturating arithmetic has bounded semantics.

**ANUM-27** — Carry and borrow operations are explicit numeric primitives.

**ANUM-28** — Division-by-zero behavior is defined.

**ANUM-29** — Signed division semantics are defined.

**ANUM-30** — Shift behavior is defined.

**ANUM-31** — Bit operations have explicit semantics.

**ANUM-32** — Numeric narrowing conversions are not implicit.

**ANUM-33** — Numeric casts and bitcasts are distinct.

**ANUM-34** — Bitcasts require valid representation conditions.

**ANUM-35** — Numeric newtypes preserve semantic type distinction.

**ANUM-36** — Equal physical representation does not imply equal numeric type.

**ANUM-37** — `f32` and `f64` have explicit floating-point semantics.

**ANUM-38** — Floating point is not mathematical real arithmetic.

**ANUM-39** — NaN semantics are defined.

**ANUM-40** — Infinity semantics are defined.

**ANUM-41** — Signed-zero semantics are preserved where observable.

**ANUM-42** — Floating-point equality follows defined FP semantics.

**ANUM-43** — Floating-point total ordering requires explicit semantics.

**ANUM-44** — Floating-point hashing is compatible with its equality contract.

**ANUM-45** — Default floating-point semantics are strict.

**ANUM-46** — Relaxed/fast floating-point semantics require explicit contract.

**ANUM-47** — Floating-point reassociation requires semantic permission.

**ANUM-48** — FMA transformation must preserve the active numeric contract.

**ANUM-49** — Dynamic floating-point environment is not implicit ordinary state.

**ANUM-50** — Rounding-mode changes are explicit system/numeric operations.

**ANUM-51** — Floating-point status flags are explicit system/numeric state.

**ANUM-52** — Math functions have explicit accuracy/semantic contracts.

**ANUM-53** — Approximate math is distinct from strict math.

**ANUM-54** — Deterministic numeric execution is an explicit stronger contract.

**ANUM-55** — Cross-target floating-point execution is not assumed bit-identical by default.

**ANUM-56** — Numeric literals have deterministic typing rules.

**ANUM-57** — Numeric literal overflow is diagnosed.

**ANUM-58** — Decimal floating literals have deterministic conversion semantics.

**ANUM-59** — Compile-time numeric evaluation follows runtime numeric semantics.

**ANUM-60** — Compile-time numeric overflow is diagnosed or follows explicit arithmetic semantics.

**ANUM-61** — Numeric range analysis may prove overflow absence.

**ANUM-62** — Proven no-overflow operations may lower to native arithmetic.

**ANUM-63** — Optimizer may not assume algebraic identities that violate active numeric semantics.

**ANUM-64** — Floating-point algebraic transformations respect NaN, infinity and signed-zero semantics.

**ANUM-65** — Integer algebraic transformations respect overflow mode.

**ANUM-66** — Numeric optimization uses compiler-proven facts.

**ANUM-67** — Numeric facts are distinct from programmer assertions.

**ANUM-68** — `f16` has semantics distinct from `f32`.

**ANUM-69** — `bf16` has semantics distinct from `f16`.

**ANUM-70** — Specialized low-precision types do not require Core machine-native support.

**ANUM-71** — Quantized integer types may be library/compiler specializations.

**ANUM-72** — Complex numbers are library abstractions.

**ANUM-73** — Decimal arithmetic is a library abstraction.

**ANUM-74** — Fixed-point arithmetic is a library abstraction.

**ANUM-75** — Arbitrary-precision integers are library abstractions.

**ANUM-76** — Arbitrary-precision values do not imply Copy semantics.

**ANUM-77** — Numeric traits describe capabilities rather than deep type hierarchies.

**ANUM-78** — Generic numeric code uses static specialization by default.

**ANUM-79** — Numeric operator abstraction may be erased by monomorphization/inlining.

**ANUM-80** — Implicit mixed signed/unsigned numeric conversions are restricted.

**ANUM-81** — Implicit integer/float conversions are restricted.

**ANUM-82** — Exact numeric conversions have explicit failure semantics.

**ANUM-83** — Saturating numeric conversions are explicit.

**ANUM-84** — Wrapping numeric conversions are explicit.

**ANUM-85** — Numeric representation is distinct from numeric value semantics.

**ANUM-86** — Endianness is a representation/serialization concern, not a numeric value property.

**ANUM-87** — Numeric serialization requires explicit representation semantics.

**ANUM-88** — SIMD numeric semantics derive from scalar numeric semantics.

**ANUM-89** — GPU numeric semantics derive from Axiom numeric semantics subject to target contracts.

**ANUM-90** — Atomic numeric operations use the Axiom atomic memory model.

**ANUM-91** — Atomicity does not alter ordinary numeric value semantics.

**ANUM-92** — Numeric target features are explicit.

**ANUM-93** — Hardware acceleration cannot silently redefine language semantics.

**ANUM-94** — Numeric library implementations may specialize by target.

**ANUM-95** — Math libraries need not depend on external C math libraries.

**ANUM-96** — Numeric semantics participate in incremental compilation fingerprints when relevant.

**ANUM-97** — Numeric optimization decisions are explainable.

**ANUM-98** — Numeric conformance includes edge-case and cross-optimization tests.

**ANUM-99** — Optimization levels preserve numeric semantics unless an explicit relaxed contract applies.

**ANUM-100** — All numeric, SIMD, tensor, GPU and math optimizations preserve the active Axiom numeric contract.

---

# Một quyết định kiến trúc rất quan trọng

Sau BOOTSTRAP-078 + 079, Axiom đã hình thành một chuỗi khá mạnh:

```text
          Axiom source
               │
               ▼
        Numeric semantics
               │
       ┌───────┴────────┐
       ▼                ▼
    Scalar             SIMD
       │                │
       └───────┬────────┘
               ▼
        Range / Alias /
        Numeric analysis
               │
               ▼
             OptIR
               │
       ┌───────┼──────────┐
       ▼       ▼          ▼
     scalar   AVX/NEON    GPU
       │       │          │
       └───────┼──────────┘
               ▼
         Native machine
```

Điều này có một hệ quả rất đáng giá:

### Programmer không cần viết code “cho CPU”.

Ví dụ:

```ax
fn sum(values: view<f32>) -> f32 {
    var total = 0.0
    for x in values {
        total += x
    }
    total
}
```

vẫn là **một semantic program duy nhất**.

Compiler có thể chọn:

```text
scalar
→ SIMD
→ FMA
→ unroll
→ vector reduction
```

hoặc GPU/library implementation khi abstraction phía trên cho phép.

Đây là hướng phù hợp với mục tiêu Axiom hơn việc nhồi hàng trăm intrinsic vào language syntax.

---

## Bước tiếp theo: BOOTSTRAP-080

Chuỗi kiến trúc hiện đã đi qua:

```text
076  Resource / I/O
077  FFI / System ABI
078  SIMD / Vector / Tensor
079  Numeric / Precision
```

Bước tiếp theo hợp lý là:

# **BOOTSTRAP-080 — Axiom Security, Safety, Undefined Behavior & Trusted Unsafe Model**

Đây là phần rất quan trọng trước khi đi sâu hơn vào compiler/frontend.

Nó sẽ chốt:

- chính xác **safe Axiom đảm bảo những gì**;
- danh sách UB còn lại;
- provenance;
- invalid pointer;
- integer-to-pointer;
- uninitialized memory;
- data race;
- atomic race;
- lifetime;
- type punning;
- invalid enum;
- invalid UTF-8;
- FFI violation;
- `unsafe` contract;
- trusted boundary;
- optimizer được phép giả định gì;
- sanitizer/debug mode;
- `panic` vs `trap` vs hardware fault;
- và đặc biệt **làm thế nào để Axiom vừa an toàn hơn C/C++ nhưng không biến thành Rust với một borrow checker lộ thiên**.