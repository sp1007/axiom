# BOOTSTRAP-086 — Axiom Numeric Type, Floating-Point, Precision & Extended Arithmetic Model

**Trạng thái: FROZEN**

Mục tiêu của phần này là chốt **semantic model của số học** để các tầng phía sau — optimizer, SIMD, GPU, AI, scientific computing, financial computing, FFI — không phải tự tạo ra những luật số học khác nhau.

Nguyên tắc:

> **Một phép toán số học phải có semantic rõ ràng trước khi compiler được phép tối ưu nó.**

Đồng thời:

> **Không hy sinh hiệu năng phần cứng chỉ để có một mô hình số học quá trừu tượng.**

---

# 1. Phân tầng kiểu số

Axiom chia numeric types thành:

```text
Core primitive
    ↓
Extended compiler-supported numeric
    ↓
Numeric library
    ↓
Domain-specific numeric
```

### Core

```text
i8   i16   i32   i64
u8   u16   u32   u64
isize
usize

f32
f64
```

### Extended

Có thể hỗ trợ compiler-level:

```text
i128
u128
f16
bf16
```

nhưng không nhất thiết phải là semantic primitive của mọi profile.

### Library

```text
BigInt
BigUint
Decimal
Fixed
Complex
Rational
Interval
```

---

# 2. `i128/u128`

Axiom nên hỗ trợ `i128/u128` trong type system từ sớm.

Lý do:

- cryptography
- hashing
- timestamps/counters
- arbitrary-precision implementation
- compiler internals
- systems programming
- 128-bit arithmetic trên 64-bit CPU

Không yêu cầu CPU phải có native 128-bit register.

Ví dụ:

```ax
let a: u128 = ...
let b: u128 = ...
let c = a * b
```

Compiler có thể hạ thành nhiều instruction.

---

# 3. Wide integer không phải một register

Giống SIMD:

```text
u128
```

là **semantic value**, không phải:

```text
"một thanh ghi 128-bit"
```

Trên x86-64 có thể:

```text
RDX:RAX
```

hoặc stack/register combination.

---

# 4. Integer overflow phải deterministic

Axiom không dùng mô hình C kiểu:

> signed overflow → undefined behavior.

Safe Core phải xác định hành vi.

Có ba semantic families:

```text
checked
wrapping
saturating
```

---

# 5. Checked arithmetic

Ví dụ:

```ax
let x = checked_add(a, b)?
```

hoặc API tương đương.

Kết quả:

```text
Result<T, ArithmeticError>
```

Không silently wrap.

---

# 6. Wrapping arithmetic

Explicit:

```text
wrapping_add
wrapping_sub
wrapping_mul
```

Ví dụ:

```ax
let x = a.wrapping_add(b)
```

Đặc biệt hữu ích cho:

- cryptography
- hash
- bit manipulation
- modular arithmetic
- low-level algorithms.

---

# 7. Saturating arithmetic

```text
saturating_add
saturating_sub
saturating_mul
```

Ví dụ:

```text
u8(250) + 20
```

→ `255`.

Không wrap về `14`.

---

# 8. Ordinary arithmetic

Đây là điểm cần quyết định.

Axiom nên để:

```text
a + b
```

là **checked arithmetic trong safe/debug semantic model**, nhưng release compiler được phép tối ưu nếu compiler chứng minh không overflow.

Tuy nhiên không nên để semantics thay đổi giữa Debug và Release.

Do đó:

```text
a + b
```

phải có **một semantic duy nhất**.

Khuyến nghị:

> Integer overflow trong ordinary arithmetic là **panic/trap**, không UB và không silent wrap.

Compiler có thể loại bỏ check khi chứng minh:

```text
a + b <= MAX
```

---

# 9. Tại sao không mặc định wrapping?

Vì:

```ax
let size = count * element_size
```

nếu wrap có thể tạo:

```text
small allocation
+
large logical access
```

Đây là lớp bug nguy hiểm.

Checked semantics giúp compiler/runtime phát hiện.

---

# 10. Tại sao không dùng Result cho mọi phép cộng?

Vì:

```ax
a + b
```

trả:

```text
Result<T, Error>
```

sẽ làm code cực kỳ nặng.

Do đó ordinary arithmetic:

```text
T
```

và overflow:

```text
panic/trap
```

Trong trường hợp cần recoverable arithmetic:

```text
checked_add(...)
```

→ `Option/Result`.

---

# 11. Constant evaluation

Compiler phải phát hiện overflow tại compile-time nếu giá trị đã biết.

Ví dụ:

```ax
const x: u8 = 255 + 1
```

→ compile error.

Không đợi runtime.

---

# 12. Compile-time overflow không phải compiler crash

Phân biệt:

```text
numeric overflow
```

với:

```text
compiler internal overflow/bug
```

Cái đầu là diagnostic bình thường.

Cái sau là ICE.

---

# 13. Division

Integer division:

```text
a / b
```

với:

```text
b == 0
```

→ panic/trap.

Không UB.

---

# 14. Remainder

```text
a % b
```

cũng phải định nghĩa rõ khi:

```text
b == 0
```

→ panic/trap.

---

# 15. Signed division edge case

Ví dụ:

```text
MIN_INT / -1
```

có thể không biểu diễn được.

Axiom không để đây thành UB.

→ arithmetic trap/panic theo ordinary arithmetic semantics.

---

# 16. Integer conversion

Không tự động narrowing:

```text
i64 → i32
```

phải explicit.

Ví dụ:

```ax
let x = value as i32
```

Nhưng `as` cần semantics rõ ràng.

---

# 17. `as` không nên là một phép conversion mơ hồ

Axiom phân biệt:

```text
numeric cast
bitcast
reinterpretation
```

`as` chỉ dành cho **value conversion**.

`bitcast` dành cho bit representation.

Raw reinterpretation thuộc unsafe/system.

---

# 18. Integer → integer

Widen:

```text
i32 → i64
```

có thể explicit nhưng lossless.

Narrow:

```text
i64 → i32
```

phải có conversion semantics xác định.

Không nên để compiler tự đoán programmer muốn:

```text
truncate
checked
saturate
```

---

# 19. Explicit conversion APIs

Có thể có:

```text
to<T>()
checked_as<T>()
wrapping_as<T>()
saturating_as<T>()
```

hoặc equivalent library/compiler intrinsics.

Điểm quan trọng là **semantic intent phải rõ**.

---

# 20. Floating point không giống integer

Axiom không áp dụng integer overflow model cho:

```text
f32
f64
```

Floating-point theo IEEE-style semantics với target-specific details được chuẩn hóa đủ để compiler không tùy tiện thay đổi kết quả.

---

# 21. `f32` và `f64`

Core:

```text
f32
f64
```

là binary floating-point types.

Không có:

```text
float
double
```

alias kiểu C trong Core.

---

# 22. NaN

Axiom phải hỗ trợ NaN.

Nhưng:

```text
NaN == NaN
```

không được mặc định là true.

Numeric equality tuân floating-point semantics.

---

# 23. NaN không phải một giá trị duy nhất

Có thể có nhiều NaN bit patterns.

Do đó:

```text
semantic equality
```

không đồng nghĩa:

```text
bitwise equality
```

Điều này kế thừa representation model đã frozen.

---

# 24. Signed zero

Phải giữ distinction:

```text
+0.0
-0.0
```

khi floating-point operation/observable behavior yêu cầu.

Không được optimizer mặc định coi chúng luôn cùng một bit pattern.

---

# 25. Infinity

Hỗ trợ:

```text
+∞
-∞
```

theo floating-point semantics.

Không coi infinity là panic.

---

# 26. Floating exceptions

Axiom không biến mỗi floating exception thành:

```text
Result
```

hoặc panic mặc định.

Các trạng thái như:

```text
NaN
Infinity
```

là floating values.

Hardware floating exception traps là system-level configuration.

---

# 27. Rounding

Axiom phải có rounding modes.

Tối thiểu:

```text
nearest
toward_zero
toward_positive
toward_negative
```

Có thể expose qua numeric/system API.

---

# 28. Default rounding

Ordinary `f32/f64` operations sử dụng default target-compatible floating-point rounding semantics.

Compiler không được âm thầm thay đổi rounding mode nếu rounding mode observable.

---

# 29. Rounding mode là state nhạy cảm

Nếu chương trình có thể thay đổi rounding mode runtime, optimizer phải biết.

Ví dụ:

```text
set_rounding_mode(...)
```

không thể bị coi như một function không có side effect.

---

# 30. Constant folding

Compiler có thể constant-fold:

```ax
const x = 1.5 + 2.5
```

nhưng kết quả compile-time phải tương thích semantic floating-point model.

Không được dùng host compiler floating behavior tùy tiện nếu khác target semantics.

---

# 31. Cross compilation

Đây đặc biệt quan trọng.

Nếu build:

```text
Windows x86-64
```

trên:

```text
ARM64
```

thì `comptime` numeric evaluation phải sử dụng **target semantic model** khi giá trị phụ thuộc target.

Không được để host CPU quyết định semantic result một cách vô tình.

---

# 32. FMA

Axiom phân biệt:

```text
mul + add
```

và:

```text
fma
```

về rounding semantics.

Compiler chỉ fuse khi semantic contract cho phép.

---

# 33. Fast math

Không mặc định.

Một optimization profile có thể cho phép:

```text
@fast_math
```

nhưng phải xác định cụ thể compiler được phép bỏ qua gì:

```text
NaN assumptions
Infinity assumptions
signed zero
reassociation
FMA contraction
reciprocal approximation
```

Không dùng một flag mơ hồ kiểu:

```text
"fast = làm gì cũng được"
```

---

# 34. Floating comparison

Các operation:

```text
==
!=
<
<=
>
>=
```

phải định nghĩa behavior với NaN.

Compiler không được biến unordered comparison thành ordinary integer-like comparison.

---

# 35. Total ordering

Nếu cần sort floating values, numeric comparison không đủ.

Library cần:

```text
total_cmp
```

hoặc equivalent.

Nó định nghĩa thứ tự total phù hợp cho sorting/hash use cases.

---

# 36. Hashing floating-point

Không dùng raw bits một cách mù quáng.

Phải định nghĩa:

```text
NaN
+0
-0
```

được xử lý thế nào.

Hash equality contract phải nhất quán:

```text
a == b → hash(a) == hash(b)
```

nếu numeric equality được dùng.

---

# 37. Decimal

`Decimal` không nên vào Core.

Library type:

```text
Decimal
```

phù hợp cho:

- tài chính
- tiền tệ
- fixed precision
- exact decimal calculations.

---

# 38. Decimal không phải floating point

Không được quảng bá:

```text
Decimal ≈ f64 nhưng chính xác hơn
```

Nó là semantic model khác.

Ví dụ:

```text
0.1 + 0.2
```

có thể có decimal semantics khác hoàn toàn binary floating point.

---

# 39. Fixed-point

Library:

```text
Fixed<I, F>
```

trong đó:

```text
I = integer bits
F = fractional bits
```

Ví dụ:

```text
Fixed<i32, 16>
```

phù hợp:

- embedded
- DSP
- control systems
- deterministic numeric code.

Compiler có thể optimize về integer arithmetic.

---

# 40. Fixed-point phải zero-cost

Nếu:

```text
Fixed<i32, 16>
```

chỉ là semantic wrapper quanh `i32`, compiler có thể erase abstraction.

Không cần object/header/runtime.

---

# 41. Rational

Library:

```text
Rational
```

có thể biểu diễn:

```text
numerator
denominator
```

và normalize theo policy.

Đây là expensive numeric type, không phải primitive.

---

# 42. BigInt

`BigInt` là library type.

Nó có dynamic storage semantics.

Ví dụ:

```text
BigInt
```

có thể internally dùng:

```text
small integer
heap limbs
arena
stack temporary
```

Compiler/library có thể tối ưu.

---

# 43. BigInt không được giả vờ là primitive

Operations có thể allocation.

Programmer cần hiểu đây là:

```text
arbitrary precision
```

và có cost khác primitive integer.

---

# 44. BigInt + ownership

BigInt tuân:

```text
Move
Copy/Clone
Drop
view
```

như mọi owning type.

Compiler có thể eliminate temporary BigInt allocation nếu không observable.

---

# 45. Complex

Library:

```text
Complex<f32>
Complex<f64>
```

có thể được biểu diễn semantic như:

```text
struct {
    re
    im
}
```

Compiler có thể scalarize/vectorize.

Không cần runtime object.

---

# 46. Complex arithmetic

Operations:

```text
+
-
*
/
abs
conj
sqrt
exp
log
sin
cos
```

thuộc numeric library.

Compiler có thể intrinsic hóa các operation phổ biến.

---

# 47. Complex SIMD

Có thể biểu diễn:

```text
Complex<f32>x4
```

hoặc library abstraction tương đương.

Compiler có thể tối ưu thành interleaved/deinterleaved SIMD tùy backend.

---

# 48. Numeric traits

Standard numeric layer nên có các traits khái quát:

```text
Add
Sub
Mul
Div
Rem
Neg
Ord
Eq
Hash
Zero
One
```

nhưng không được ép mọi numeric type phải implement mọi trait.

Ví dụ:

```text
f32
```

có:

```text
Eq
```

về syntax, nhưng total ordering cần abstraction khác.

---

# 49. Generic numeric programming

Cho phép:

```ax
fn square<T: Mul>(x: T) -> T {
    x * x
}
```

Compiler monomorphization:

```text
T = i32
T = f32
T = f32x8
```

→ specialization.

---

# 50. Numeric concepts không cần class hierarchy

Không cần:

```text
Number
  ├── Integer
  ├── Float
  └── Decimal
```

Trait system đã đủ.

---

# 51. `Numeric` trait nếu cần chỉ là convenience

Library có thể định nghĩa:

```text
Numeric
```

nhưng không biến nó thành một hierarchy bắt buộc.

---

# 52. Compile-time numeric constants

Axiom nên cho:

```text
const
comptime
```

xử lý numeric values.

Ví dụ:

```ax
const WIDTH = 1024
const SCALE = 0.25
```

---

# 53. Generic const parameters

Đã frozen hỗ trợ scalar:

```text
Vector<T, N>
Array<T, N>
Matrix<T, R, C>
```

với:

```text
N
R
C
```

compile-time constants.

---

# 54. Không biến const generics thành dependent types

Axiom không cần theorem proving kiểu:

```text
N + M = K
```

trong type system v1.

Chỉ cần đủ cho:

```text
array sizes
vector widths
matrix dimensions
fixed-point parameters
```

---

# 55. Shape checking

Tensor library có thể dùng const parameters:

```text
Matrix<f32, 4, 4>
```

và kiểm tra:

```text
Matrix<4, 4> × Matrix<4, 8>
```

tại compile-time nếu API được thiết kế phù hợp.

Nhưng không yêu cầu full dependent typing.

---

# 56. Numeric literals

Axiom nên hỗ trợ:

```text
42
42u32
42i64

3.14
3.14f32
3.14f64
```

Compiler suy luận literal type từ context.

---

# 57. Integer literal overflow

```text
let x: u8 = 300
```

→ compile error.

Không silent truncation.

---

# 58. Floating literal precision

```text
let x: f32 = 0.1
```

Compiler phải convert literal theo target `f32` semantic.

Không giữ nó vô tình ở `f64` rồi truncate sau.

---

# 59. Hex/binary/octal

Hỗ trợ:

```text
0xFF
0b101010
0o755
```

với suffix nếu cần.

Đây là đặc biệt hữu ích cho system programming.

---

# 60. Numeric separators

Cho phép:

```text
1_000_000
0xFF_FF
3.141_592
```

Chỉ là syntax sugar.

---

# 61. No implicit integer ↔ float conversion

Không:

```text
i32 + f32
```

một cách implicit.

Phải explicit.

---

# 62. No implicit signed ↔ unsigned conversion

Không tự động:

```text
i32 → u32
```

vì semantic range khác nhau.

---

# 63. Generic arithmetic conversion

Compiler không thực hiện conversion chain:

```text
u8 → i32 → f64 → ...
```

để làm overload resolution.

Điều này giữ deterministic type inference.

---

# 64. Numeric promotion

Axiom **không áp dụng C-style default promotions**.

Ví dụ:

```text
u8 + u8
```

có semantic result xác định theo operator/type rules, không tự động biến thành một chuỗi promotion không kiểm soát.

---

# 65. Operator result type

Mỗi numeric operator phải có compiler-resolvable signature.

Ví dụ:

```text
i32 + i32 → i32
f32 + f32 → f32
f32x8 + f32x8 → f32x8
```

---

# 66. Mixed-width vector arithmetic

Không tự động:

```text
f32x4 + f32x8
```

phải explicit broadcast/convert/reshape.

---

# 67. Broadcast

Library/compiler primitive:

```text
broadcast(x, N)
```

ví dụ:

```text
f32 → f32x8
```

được semantic rõ ràng.

Compiler có thể biến thành hardware broadcast instruction.

---

# 68. Reduction

Đã xác định ở SIMD:

```text
reduce_add
reduce_min
reduce_max
...
```

Floating reduction phải giữ ordering semantics.

---

# 69. Numerical determinism

Axiom cần phân biệt:

```text
semantic deterministic
```

với:

```text
bitwise deterministic
```

Một parallel reduction có thể cần policy rõ ràng nếu user yêu cầu bitwise reproducibility.

---

# 70. Deterministic numeric profile

Library/toolchain có thể cung cấp profile:

```text
reproducible
```

với các constraint:

- fixed rounding
- fixed reduction order
- deterministic random seed
- controlled math implementation
- controlled parallel reduction.

Không bắt mọi chương trình trả giá performance cho điều này.

---

# 71. Normal numeric profile

Mặc định ưu tiên:

```text
correct semantics
+
native performance
```

Không ép deterministic parallel floating reduction nếu semantics API không yêu cầu.

---

# 72. Approximate math

Các hàm:

```text
sin
cos
exp
log
sqrt
```

cần phân biệt:

```text
correct/standard
approximate/fast
```

Compiler có thể dùng hardware approximation khi contract cho phép.

---

# 73. `sqrt`

`sqrt` cần semantic rõ ràng cho:

```text
negative
NaN
+0
-0
Infinity
```

không được biến thành generic `panic` vì negative.

Floating domain có NaN.

---

# 74. Math library không nằm trong compiler core

Compiler chỉ cần recognize/intrinsic hóa những operation quan trọng.

Phần lớn:

```text
sin
cos
tan
exp
log
gamma
erf
```

thuộc numeric library.

---

# 75. Hardware math

Compiler có thể map:

```text
sqrt
fma
abs
min
max
```

thành instruction native.

Không cần runtime call nếu target có instruction phù hợp.

---

# 76. Math library ABI

Math library phải có target implementations:

```text
x86
ARM
RISC-V
WASM
GPU
```

nhưng API semantic thống nhất.

---

# 77. GPU numeric semantics

GPU không được tự tạo arithmetic semantics khác một cách âm thầm.

Nhưng GPU target có thể có:

```text
fast approximation
lower precision
flush-to-zero
```

chỉ khi execution profile/API contract cho phép.

---

# 78. `f16` và `bf16`

Nên hỗ trợ ở extended numeric layer.

Đặc biệt:

```text
f16
bf16
```

rất quan trọng cho:

- GPU
- AI
- inference
- memory bandwidth.

---

# 79. `bf16` không phải `f16`

Phải là hai type distinct.

Không implicit convert.

---

# 80. Precision conversion

Explicit:

```text
f32 → f16
f32 → bf16
f16 → f32
```

Compiler có thể map native conversion instruction.

---

# 81. AI numeric types

Kiến trúc phải mở cho:

```text
fp8
int4
uint4
int2
```

nhưng không cần đưa tất cả vào Core v1.

Đây là **numeric extension mechanism**.

---

# 82. Packed integer types

Các type nhỏ như:

```text
u4
i4
```

có thể có semantic packed representation.

Nhưng phải phân biệt:

```text
semantic 4-bit value
```

với:

```text
u8 containing a value <= 15
```

---

# 83. Compiler intrinsic numeric operations

Compiler intrinsic registry có thể bổ sung:

```text
mul_wide
add_carry
sub_borrow
leading_zeros
trailing_zeros
popcount
byte_swap
rotate
bit_reverse
```

Các operation này cực kỳ quan trọng cho systems/crypto.

---

# 84. Carry/borrow

Ví dụ conceptual:

```text
add_carry(a, b, carry)
```

→:

```text
(value, carry_out)
```

Compiler có thể map xuống:

```text
ADC
SBB
```

hoặc tương đương ARM/RISC-V.

---

# 85. Wide multiplication

Ví dụ:

```text
mul_wide(u64, u64)
```

→:

```text
(u128)
```

hoặc high/low halves.

Rất hữu ích cho hash/crypto/BigInt.

---

# 86. Bit operations không phải arithmetic hacks

Axiom nên cung cấp semantic operations cho:

```text
popcount
clz
ctz
rotate_left
rotate_right
reverse_bits
reverse_bytes
```

Compiler target-lower.

---

# 87. Division optimization

Compiler có thể biến:

```text
x / constant
```

thành multiplication/shift sequence nếu semantics preserved.

Programmer không cần tự tối ưu.

---

# 88. Constant modulus

Tương tự:

```text
x % constant
```

có thể được strength-reduced.

---

# 89. BigInt optimization

Compiler có thể inline/specialize:

```text
BigInt
```

operations khi size known.

Ví dụ small BigInt có thể scalarize.

---

# 90. Decimal optimization

Decimal operations có thể dùng:

```text
hardware decimal
integer arithmetic
SIMD
```

tùy target.

Semantic abstraction không phụ thuộc implementation.

---

# 91. Numerical overflow và memory safety

Compiler phải đặc biệt lưu ý các biểu thức:

```text
length * element_size
```

vì overflow có thể dẫn tới memory-safety issue.

Checked ordinary arithmetic + range analysis là một lợi thế lớn.

---

# 92. Range analysis

OptIR có:

```text
RangeInfo
```

đã frozen.

Compiler có thể chứng minh:

```text
0 <= i < n
```

và loại bỏ:

```text
bounds check
overflow check
```

khi proof hợp lệ.

---

# 93. Overflow check elimination

Ví dụ:

```ax
for i in 0..100 {
    let x = i + 1
}
```

compiler biết:

```text
i ∈ [0,99]
```

→ `i + 1` không overflow.

Không cần runtime check.

---

# 94. Numeric semantics + performance

Điểm quan trọng:

> Checked arithmetic **không đồng nghĩa chương trình chậm**.

Compiler có thể loại bỏ checks khi proof được.

Do đó thiết kế:

```text
safe semantics
+
aggressive proof
```

thay vì:

```text
unsafe semantics
+
hope programmer knows
```

phù hợp Axiom.

---

# 95. Unsafe numeric operations

System layer có thể cung cấp:

```text
unchecked_add
unchecked_div
unchecked_cast
```

nhưng chỉ khi programmer thực sự cần machine-level behavior.

Không biến chúng thành default.

---

# 96. Numeric memory representation

Numeric semantic type:

```text
i32
f32
```

có representation contract target-aware.

FFI yêu cầu explicit ABI/representation.

Không tự động coi mọi extended numeric type là C-compatible.

---

# 97. Numeric serialization

Không serialize bằng cách:

```text
memcpy(&value)
```

trừ khi representation contract yêu cầu.

Wire format phải explicit:

```text
to_le
to_be
encode
decode
```

---

# 98. Numeric + SIMD + GPU

Ba tầng phải dùng cùng semantic foundation:

```text
Scalar Numeric
      ↓
SIMD Numeric
      ↓
GPU Numeric
```

Không tạo ba hệ thống arithmetic độc lập.

GPU/SIMD chỉ thêm:

```text
execution width
storage domain
target capabilities
```

---

# 99. Core không nên phình thành thư viện toán học

Core chỉ cần đủ:

```text
primitive types
operators
conversion rules
overflow semantics
floating semantics
compile-time numeric semantics
intrinsics contract
```

Còn:

```text
BigInt
Decimal
Complex
Matrix
Tensor
FFT
BLAS
statistics
```

để library.

---

# 100. Frozen Invariants — `ANUM-20..100`

**ANUM-20** — Numeric types have explicit semantic definitions independent of physical representation.

**ANUM-21** — Core integer types are `i8..i64`, `u8..u64`, `isize`, and `usize`.

**ANUM-22** — `f32` and `f64` are Core floating-point types.

**ANUM-23** — `i128` and `u128` are supported by the type system without requiring native 128-bit registers.

**ANUM-24** — Wide integers are semantic values, not physical register requirements.

**ANUM-25** — Integer overflow is never undefined behavior in safe Core arithmetic.

**ANUM-26** — Checked, wrapping, and saturating arithmetic are distinct semantics.

**ANUM-27** — Ordinary integer arithmetic has deterministic overflow behavior.

**ANUM-28** — Ordinary integer overflow results in arithmetic failure through the defined panic/trap mechanism.

**ANUM-29** — Recoverable arithmetic overflow may use explicit checked operations returning `Option` or `Result`.

**ANUM-30** — Wrapping arithmetic is explicit.

**ANUM-31** — Saturating arithmetic is explicit.

**ANUM-32** — Compile-time integer overflow is a compile-time diagnostic.

**ANUM-33** — Integer division by zero is deterministic arithmetic failure.

**ANUM-34** — Signed division overflow is deterministic arithmetic failure.

**ANUM-35** — Numeric narrowing conversions are not implicit.

**ANUM-36** — Signed/unsigned conversions are not implicitly inserted.

**ANUM-37** — Integer/float conversions are not implicitly inserted.

**ANUM-38** — Numeric casts are distinct from bitcasts.

**ANUM-39** — Bitcasts require valid representation conditions.

**ANUM-40** — Axiom does not use uncontrolled C-style numeric promotion.

**ANUM-41** — Operator resolution is deterministic.

**ANUM-42** — Numeric literals are checked against their resolved type.

**ANUM-43** — Integer literals cannot silently truncate.

**ANUM-44** — Floating literals are converted according to their resolved floating type.

**ANUM-45** — Floating-point semantics preserve NaN behavior.

**ANUM-46** — Floating-point semantics preserve signed-zero distinctions where observable.

**ANUM-47** — Floating-point infinity is a valid numeric value.

**ANUM-48** — Floating-point NaN is not equal to itself under ordinary numeric equality.

**ANUM-49** — Floating-point semantic equality is distinct from bitwise equality.

**ANUM-50** — Floating-point total ordering is a separate operation from numeric ordering.

**ANUM-51** — Floating-point hashing must respect the applicable equality contract.

**ANUM-52** — Floating-point rounding semantics are explicit.

**ANUM-53** — Compiler transformations must preserve observable rounding semantics.

**ANUM-54** — Compile-time floating evaluation must respect the target semantic model when target-dependent.

**ANUM-55** — FMA and separate multiply/add have distinct rounding semantics.

**ANUM-56** — FMA contraction requires applicable semantic permission.

**ANUM-57** — Fast-math is not enabled by default.

**ANUM-58** — Fast-math permissions must define their semantic relaxations.

**ANUM-59** — Compiler optimization may not silently assume absence of NaN or infinity.

**ANUM-60** — Floating-point reassociation requires explicit semantic permission.

**ANUM-61** — Standard floating operations may be mapped to native hardware instructions when semantics permit.

**ANUM-62** — Approximate math operations are distinct from ordinary correctly-specified math operations.

**ANUM-63** — Decimal arithmetic is distinct from binary floating-point arithmetic.

**ANUM-64** — Decimal arithmetic belongs to the numeric library layer.

**ANUM-65** — Fixed-point arithmetic belongs to the numeric library layer.

**ANUM-66** — Fixed-point representations may compile to ordinary integer operations.

**ANUM-67** — Arbitrary-precision integers belong to the library layer.

**ANUM-68** — `BigInt` follows ordinary Axiom ownership and lifetime semantics.

**ANUM-69** — BigInt allocation is not semantically required for every operation.

**ANUM-70** — Compiler optimization may scalarize or eliminate temporary arbitrary-precision storage when semantics permit.

**ANUM-71** — Complex numbers belong to the numeric library layer.

**ANUM-72** — Complex numeric types may be represented as scalar aggregates and optimized accordingly.

**ANUM-73** — Numeric traits provide generic arithmetic without requiring a numeric class hierarchy.

**ANUM-74** — Generic numeric code may be monomorphized and specialized.

**ANUM-75** — Numeric generic abstractions do not require dynamic dispatch by default.

**ANUM-76** — Const generic numeric parameters remain compile-time abstractions.

**ANUM-77** — Const generics do not imply a general dependent type system.

**ANUM-78** — Vector numeric semantics extend scalar numeric semantics rather than replacing them.

**ANUM-79** — SIMD arithmetic preserves scalar arithmetic contracts lane-wise unless explicitly defined otherwise.

**ANUM-80** — Vector overflow semantics remain explicit.

**ANUM-81** — Vector floating-point semantics preserve applicable scalar floating-point rules.

**ANUM-82** — Reduction operations have explicit ordering semantics.

**ANUM-83** — Parallel numeric execution does not silently change required deterministic semantics.

**ANUM-84** — Reproducible numeric execution may be provided as an explicit profile or contract.

**ANUM-85** — Default numeric execution does not impose unnecessary reproducibility costs.

**ANUM-86** — `f16` and `bf16` are distinct numeric types when supported.

**ANUM-87** — Precision conversions between floating types are explicit.

**ANUM-88** — Extended low-precision AI numeric types may be added without redesigning the Core numeric model.

**ANUM-89** — Packed low-bit numeric types are semantically distinct from larger storage types.

**ANUM-90** — Numeric bit operations have explicit semantic intrinsics.

**ANUM-91** — Carry and borrow operations are available as low-level numeric primitives where supported.

**ANUM-92** — Wide multiplication may expose high and low result components without requiring a wide physical register.

**ANUM-93** — Numeric range analysis may eliminate proven overflow and bounds checks.

**ANUM-94** — Unsafe unchecked arithmetic is an explicit low-level facility.

**ANUM-95** — Numeric representation and serialization representation are distinct.

**ANUM-96** — Numeric FFI representation requires an applicable ABI/representation contract.

**ANUM-97** — Numeric semantics are shared across CPU, SIMD, GPU and accelerator layers unless an explicit target contract states otherwise.

**ANUM-98** — Hardware-specific numeric optimizations cannot change the defined semantic result.

**ANUM-99** — Numeric abstractions may be erased completely when their semantics are preserved.

**ANUM-100** — Axiom numeric design prioritizes deterministic semantics, explicit precision/overflow behavior, and native hardware performance without exposing unnecessary machine complexity.

---

## Một quyết định quan trọng đã được chốt

Axiom hiện có một mô hình rất mạnh:

```text
                  Numeric Semantics
                         │
        ┌────────────────┼────────────────┐
        │                │                │
     Integer          Float            Extended
        │                │                │
 checked/wrap/sat   IEEE-style       BigInt/Decimal/
        │           NaN/∞/-0         Fixed/Complex
        │                │
        └────────────────┼────────────────┘
                         ↓
                    RangeInfo
                         ↓
                  Optimization
                         ↓
             ┌───────────┼───────────┐
             ↓           ↓           ↓
          Scalar        SIMD        GPU
             ↓           ↓           ↓
                  Native Machine
```

Điều này cũng giải quyết một vấn đề trước đây của Axiom: **safety không nhất thiết phải trả giá bằng performance**.

Ví dụ compiler nhìn thấy:

```ax
for i in 0..n {
    out[i] = a[i] + b[i]
}
```

và có thể chứng minh:

```text
0 ≤ i < n
a[i] valid
b[i] valid
out[i] valid
a/b/out non-conflicting
i + 1 không overflow
```

thì toàn bộ:

```text
bounds checks
overflow checks
ownership abstractions
view abstractions
iterator abstractions
```

có thể biến mất khỏi machine code.

Đây chính là mô hình **"prove first, erase later"** mà Axiom đang hình thành.

---

# Bước kiến trúc tiếp theo

**BOOTSTRAP-087 — Axiom Compile-Time Evaluation, Constant Propagation & Partial Evaluation Deep Model**

Phần này sẽ đi sâu hơn BOOTSTRAP-037:

```text
const
comptime
const generic
compile-time reflection
generated declarations
compile-time resource/capability
incremental cache
cross-compilation
partial evaluation
constant folding
specialization
compile-time diagnostics
```

và đặc biệt chốt **ranh giới giữa `const`, `comptime`, optimizer và runtime** để compiler có thể thực hiện partial evaluation rất mạnh mà không biến Axiom thành một ngôn ngữ có “hai thế giới” tách biệt.