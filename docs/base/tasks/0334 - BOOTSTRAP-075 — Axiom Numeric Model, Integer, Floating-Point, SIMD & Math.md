Tiếp tục.

# BOOTSTRAP-075 — Axiom Numeric Model, Integer, Floating-Point, SIMD & Math

**Trạng thái: FROZEN**

Đây là một phần rất quan trọng đối với mục tiêu hiệu năng của Axiom. Nếu numeric semantics thiết kế không tốt, compiler sẽ phải chọn giữa:

- semantics an toàn nhưng chậm,
- hoặc semantics nhanh nhưng đầy UB kiểu C/C++.

Axiom nên đi hướng thứ ba:

> **Semantics xác định rõ ở source level, nhưng compiler được trao đủ thông tin để tối ưu mạnh mà không cần dựa vào undefined behavior.**

---

# 1. Nguyên tắc tổng quát

Numeric model của Axiom có 4 tầng:

```text
Language semantics
        ↓
Numeric MIR semantics
        ↓
Optimization facts
        ↓
Target machine instructions
```

Ví dụ:

```axiom
let x: i32 = a + b
```

không được phép có nghĩa khác nhau tùy:

```text
-O0
-O2
-O3
```

Nhưng compiler có thể chứng minh rằng phép cộng không overflow và biến nó thành một instruction máy rất nhanh.

---

# 2. Integer types

Core:

```text
i8   i16   i32   i64
u8   u16   u32   u64

isize
usize
```

Các type này có **width xác định**.

Ví dụ:

```text
i32
```

luôn là signed 32-bit integer.

Không phụ thuộc compiler/OS.

---

# 3. `isize` / `usize`

```text
usize
isize
```

có width bằng native pointer width của target.

Ví dụ:

```text
x86-64 → 64 bit
ARM64  → 64 bit
```

Chúng dùng chủ yếu cho:

```text
index
length
capacity
size
pointer-distance
```

---

# 4. Không implicit numeric conversion

Không cho:

```axiom
let x: i64 = some_i32
```

tự động convert nếu semantic conversion có thể mất thông tin.

Phải explicit:

```axiom
let x: i64 = some_i32 as i64
```

Điều này làm code AI-generated dễ kiểm tra hơn.

---

# 5. Không có C-style integer promotion

Không áp dụng kiểu:

```text
u8 + u8 → int
```

một cách ngầm định.

Expression type phải có quy tắc rõ ràng.

Ví dụ:

```axiom
let a: u8 = 10
let b: u8 = 20
let c = a + b
```

`c` có semantic integer type được xác định theo operator/type rules của Axiom, không phụ thuộc “default int” của C.

---

# 6. Arithmetic overflow

Axiom **không sử dụng signed-overflow UB** làm cơ chế optimization.

Đây là một quyết định quan trọng.

Ví dụ:

```axiom
let x: i32 = ...
let y = x + 1
```

Nếu overflow có thể xảy ra, semantics phải xác định.

---

# 7. Default integer arithmetic

Khuyến nghị:

```text
debug/release:
    cùng semantics
```

và phép arithmetic thông thường có semantics **checked**.

Conceptually:

```text
i32::MAX + 1
```

→ runtime arithmetic failure/panic/trap theo profile.

Không:

```text
"compiler được phép giả định overflow không bao giờ xảy ra"
```

như một UB.

---

# 8. Nhưng checked arithmetic không có nghĩa mọi loop chậm

Đây là nơi optimizer của Axiom phát huy tác dụng.

Ví dụ:

```axiom
for i in 0..n {
    ...
}
```

compiler có thể chứng minh range:

```text
0 ≤ i < n
n ≤ MAX
```

và loại bỏ overflow/bounds checks không cần thiết.

Mục tiêu:

```text
safe source
       ↓
proof
       ↓
ordinary machine arithmetic
```

---

# 9. Explicit arithmetic modes

Khi programmer thực sự muốn semantics cụ thể:

```text
checked
wrapping
saturating
```

nên có API/operator rõ ràng.

Ví dụ conceptually:

```axiom
x.checked_add(y)
x.wrapping_add(y)
x.saturating_add(y)
```

Không nên biến operator `+` thành thứ có behavior thay đổi tùy optimization mode.

---

# 10. Wrapping arithmetic

```axiom
x.wrapping_add(y)
```

có semantics modulo 2^N.

Ví dụ `u32`:

```text
MAX + 1 → 0
```

Đặc biệt hữu ích cho:

- cryptography
- hashing
- bit manipulation
- ring counters
- low-level systems
- PRNG

---

# 11. Saturating arithmetic

```axiom
x.saturating_add(y)
```

kết quả bị giới hạn:

```text
MAX + 1 → MAX
MIN - 1 → MIN
```

hữu ích cho:

- image/audio
- DSP
- signal processing
- multimedia
- embedded.

---

# 12. Checked arithmetic

Có thể trả:

```axiom
Option<T>
```

hoặc:

```axiom
Result<T, ArithmeticError>
```

tùy API.

Nhưng để tránh allocation/overhead:

> `checked_*` nên có representation tối ưu và compiler intrinsic tương ứng.

---

# 13. Division

Integer division phải có semantics xác định.

Các trường hợp đặc biệt:

```text
division by zero
MIN / -1
```

không được để thành UB.

Compiler có thể:

```text
panic
trap
```

theo arithmetic failure policy.

---

# 14. Shift

Shift count ngoài width không được để UB.

Ví dụ:

```text
x << n
```

nếu:

```text
n >= bit_width(T)
```

phải có semantics xác định.

Có thể chọn:

```text
panic/trap
```

cho operator mặc định.

Explicit wrapping shift có thể tồn tại:

```text
rotate_left
rotate_right
```

---

# 15. Bit operations

Core/library cung cấp:

```text
and
or
xor
not
shl
shr
rotl
rotr
count_ones
count_zeros
leading_zeros
trailing_zeros
```

Compiler map trực tiếp xuống instruction nếu target hỗ trợ.

---

# 16. Signed right shift

Phải khóa rõ semantics:

```text
i32 >> n
```

là **arithmetic right shift** đối với signed integer.

Unsigned:

```text
u32 >> n
```

là logical right shift.

Không phụ thuộc compiler implementation.

---

# 17. Integer casts

Phân biệt:

```text
numeric cast
bit reinterpretation
```

Ví dụ:

```axiom
x as i64
```

là numeric conversion.

Trong khi:

```text
bitcast<f32>(x)
```

là reinterpretation.

Hai semantic operation hoàn toàn khác nhau.

---

# 18. Numeric narrowing

Ví dụ:

```axiom
let x: i64 = ...
let y = x as i32
```

được phép vì programmer explicit.

Nhưng semantics phải xác định:

- checked conversion
- wrapping/truncating conversion

Không được để implicit.

Có thể cung cấp:

```text
try_as
as
wrapping_as
```

nếu API cần phân biệt.

---

# 19. Boolean không phải integer

Không cho:

```axiom
let x: i32 = true
```

hoặc:

```axiom
if 42 { ... }
```

Boolean là type riêng.

Điều này tiếp tục nguyên tắc:

```text
bool conditions only
```

---

# 20. Floating-point

Core:

```text
f32
f64
```

theo IEEE-754 binary32/binary64 ở mức numeric semantics phù hợp.

Compiler không được âm thầm biến:

```text
f64
```

thành:

```text
f32
```

hoặc ngược lại.

---

# 21. NaN

Axiom phải công nhận NaN là giá trị floating-point hợp lệ.

Không được giả định:

```text
x == x
```

đối với mọi `f32/f64`.

Ví dụ:

```text
NaN != NaN
```

theo ordinary IEEE comparison semantics.

---

# 22. `-0.0`

`+0.0` và `-0.0` có thể có cùng numeric equality nhưng khác representation/sign behavior trong các phép toán.

Compiler không được loại bỏ sign của zero nếu điều đó làm thay đổi observable semantics.

---

# 23. Infinity

```text
+Inf
-Inf
```

là các floating values hợp lệ.

Arithmetic có thể tạo Infinity theo floating semantics.

Không biến mọi floating exceptional condition thành panic.

---

# 24. Floating exceptions

Axiom không nên mặc định dùng:

```text
panic on NaN
panic on Inf
```

vì điều đó không phù hợp numeric computing.

Thay vào đó:

```text
NaN / Inf
```

tuân theo floating-point profile.

---

# 25. Floating-point equality

`==` dùng ordinary numeric equality.

Nếu programmer muốn kiểm tra bit pattern:

```text
bitcast<u32>(x)
```

hoặc API tương đương.

Không đánh đồng:

```text
numeric equality
bitwise equality
```

---

# 26. Floating ordering

Do NaN không có total ordering, không thể giả định:

```text
f32: Ord
```

giống integer.

Có thể có:

```text
PartialOrd<f32>
```

và explicit:

```text
total_order()
```

nếu algorithm cần total ordering.

---

# 27. Fast math

Đây là phần cực kỳ quan trọng.

Không cho compiler mặc định:

```text
-O3 == fast-math
```

Optimization level **không được tự thay đổi floating semantics**.

---

# 28. Fast-math phải explicit

Nếu application cho phép relaxed floating semantics:

```axiom
@fast_math
fn calculate(...) -> f32 {
    ...
}
```

hoặc một mechanism tương đương.

Đây là **semantic contract**, không chỉ optimization hint.

---

# 29. Fast-math cho phép gì?

Tùy profile:

```text
reassociation
contracted operations
less strict NaN handling
less strict signed zero
approximate math
```

nhưng mỗi relaxation phải được định nghĩa.

Không có:

```text
"fast_math = compiler được làm bất cứ thứ gì"
```

---

# 30. FMA

Compiler có thể sử dụng:

```text
a * b + c
```

→ FMA

nếu floating semantics cho phép.

Nếu strict semantics yêu cầu rounding riêng:

```text
mul
round
add
round
```

thì không được tự biến thành FMA.

---

# 31. Math library

Các hàm:

```text
sin
cos
tan
exp
log
sqrt
pow
atan2
```

không cần trở thành language primitives.

Standard/System library cung cấp implementation.

Compiler intrinsic có thể recognize chúng để:

```text
constant fold
instruction selection
vectorize
target-libcall
```

---

# 32. `sqrt`

Nếu target có native instruction:

```text
sqrt
```

backend có thể sử dụng.

Nếu không:

```text
runtime/library implementation
```

được link.

Không bắt mọi chương trình phải link math runtime.

---

# 33. Numeric constants

Literal phải có type inference deterministic.

Ví dụ:

```axiom
let x: i32 = 123
let y: f64 = 123.0
```

Compiler biết rõ.

Không có implicit float→integer.

---

# 34. Integer literal overflow

```axiom
let x: u8 = 300
```

compile-time error.

Compiler không âm thầm truncate.

---

# 35. Constant folding

```axiom
const x = 10 * 20
```

→ compile-time evaluation.

Nhưng:

```text
comptime semantics
```

vẫn phải tuân theo numeric rules.

Không tạo một numeric language riêng.

---

# 36. Generic numeric programming

Traits:

```text
Add
Sub
Mul
Div
BitAnd
BitOr
...
```

có thể cung cấp generic operators.

Nhưng primitive arithmetic có compiler-known semantics.

---

# 37. Operator overloading

Cho phép type tự định nghĩa operator thông qua trait.

Ví dụ:

```axiom
a + b
```

có thể resolve:

```text
Add<T>
```

Nhưng primitive types được compiler recognize.

Không để operator resolution làm mất khả năng tối ưu native.

---

# 38. SIMD là type-level abstraction

Đây là quyết định quan trọng.

Không chỉ có:

```text
f32
f64
```

mà library/compiler có thể hỗ trợ:

```text
Vec<f32, 4>
Vec<f32, 8>
Vec<i32, 8>
```

hoặc syntax tương đương.

Đây là **SIMD vector value**, không phải `Array`.

---

# 39. SIMD vector khác Array

```text
[f32; 4]
```

là 4 phần tử memory aggregate.

Trong khi:

```text
simd<f32, 4>
```

là vector value có semantics cho vector instructions.

Compiler có thể map:

```text
simd<f32, 4>
```

→ XMM register.

---

# 40. Không đảm bảo SIMD width cố định trên mọi target

Một abstraction portable cần phân biệt:

```text
fixed-width SIMD
native-width SIMD
```

Ví dụ:

```text
simd<f32, 4>
```

có semantic width = 4.

Target không hỗ trợ instruction tương ứng có thể:

```text
lower thành scalar
```

hoặc instruction sequence khác.

---

# 41. Portable SIMD

Standard Library cung cấp portable SIMD.

Compiler biết type và operations:

```text
add
sub
mul
div
min
max
shuffle
blend
compare
```

Backend chịu trách nhiệm lowering.

---

# 42. Target SIMD

System/compiler layer có:

```text
x86 SSE
AVX2
AVX-512

ARM NEON
SVE

RISC-V Vector
```

nhưng source program không nên phải phụ thuộc vào assembly instruction names để viết SIMD cơ bản.

---

# 43. Target feature

Có thể:

```axiom
@target_feature("avx2")
fn process(...) {
    ...
}
```

Compiler phải đảm bảo caller không gọi function trên target không hỗ trợ feature nếu contract không thỏa.

---

# 44. Không runtime dispatch mặc định

Axiom không tự động chèn:

```text
CPUID
if AVX2
else SSE
else scalar
```

cho mọi SIMD function.

Nếu cần:

```text
runtime CPU dispatch
```

thì library/system layer thực hiện explicit.

---

# 45. Nhưng compiler có thể hỗ trợ multiversioning

Sau này:

```text
@target_feature
@dispatch
```

có thể tạo:

```text
scalar version
AVX2 version
AVX512 version
```

và dispatcher.

Đây là explicit optimization/system feature.

---

# 46. Auto-vectorization

Đây mới là con đường chính cho programmer.

Ví dụ:

```axiom
fn add(a: view<f32>, b: view<f32>, out: mut_view<f32>) {
    for i in 0..a.len() {
        out[i] = a[i] + b[i]
    }
}
```

Compiler đã có:

```text
contiguous
bounds
region
alias
```

facts.

→ có thể vectorize.

---

# 47. Không cần SIMD source code

Programmer có thể viết:

```text
ordinary loop
```

và compiler biến thành:

```text
AVX2/NEON/SVE/etc.
```

nếu target/config cho phép.

---

# 48. SIMD và alias analysis

Đây là nơi BOOTSTRAP-074 kết nối trực tiếp với 075.

```axiom
out: mut_view<f32>
a: view<f32>
b: view<f32>
```

Nếu compiler prove:

```text
out ∩ a = ∅
out ∩ b = ∅
```

thì loop vectorization an toàn hơn.

---

# 49. SIMD và alignment

Không mặc định yêu cầu programmer viết:

```text
aligned pointer
```

Compiler có thể chọn:

```text
aligned load
unaligned load
peel loop
prologue
```

tùy target.

Nếu programmer thực sự yêu cầu alignment:

```axiom
@align(...)
```

hoặc explicit aligned storage contract.

---

# 50. SIMD mask

Portable SIMD cần mask type:

```text
mask<T, N>
```

để biểu diễn:

```text
compare
select
masked load/store
```

không dùng `bool` scalar array làm semantic substitute.

---

# 51. SIMD comparison

Ví dụ:

```text
a < b
```

trên vector trả mask.

Compiler có thể map trực tiếp vào vector compare instructions.

---

# 52. Horizontal operations

Các phép:

```text
reduce_add
reduce_min
reduce_max
```

nên là library operations.

Compiler có thể map:

```text
horizontal reduction
```

thành tree reduction/vector instruction.

---

# 53. SIMD floating-point semantics

SIMD floating operations phải tuân theo cùng floating profile của scalar:

```text
NaN
Inf
signed zero
rounding
fast-math
```

Không được vì vector mà tự thay đổi semantics.

---

# 54. Matrix/tensor không phải SIMD primitive

```text
Tensor<T>
Matrix<T>
```

là library abstractions.

Chúng có thể sử dụng:

```text
view<T>
SIMD
GPU
BLAS
```

nhưng không thuộc numeric Core.

---

# 55. Big integer

Không đưa:

```text
BigInt
BigFloat
Decimal
```

vào Core primitive.

Library có thể cung cấp:

```text
BigInt
Decimal
Rational
```

với semantics riêng.

---

# 56. Decimal

Financial applications có thể cần:

```text
Decimal
```

nhưng binary floating không phù hợp để đại diện decimal exact.

Đây là library domain type, không thay đổi `f32/f64`.

---

# 57. Fixed-point

Embedded/DSP có thể cần:

```text
Fixed<I,F>
```

library generic.

Compiler có thể specialize và biến thành integer arithmetic.

---

# 58. Complex

```text
Complex<f32>
Complex<f64>
```

là library type.

Compiler có thể scalarize/vectorize/recognize nếu cần.

---

# 59. Numeric layout

Primitive numeric types có representation contract rõ:

```text
u8  = 8-bit unsigned
i8  = 8-bit signed
...
f32 = binary32
f64 = binary64
```

Nhưng generic structs:

```text
Complex<f32>
```

không tự động có stable ABI nếu không có `repr` contract.

---

# 60. Endianness

Numeric value không có “endianness” ở semantic level.

Endianness chỉ xuất hiện khi:

```text
memory representation
serialization
FFI
hardware access
```

Do đó:

```text
u32
```

không phải “little endian integer”.

---

# 61. Byte conversion

Explicit APIs:

```text
to_le_bytes()
to_be_bytes()
from_le_bytes()
from_be_bytes()
```

để serialization/wire format rõ ràng.

---

# 62. Floating serialization

Tương tự:

```text
f32.to_bits()
f32.from_bits()
```

và explicit byte ordering.

Không dùng numeric cast để biểu diễn bit pattern.

---

# 63. Atomic numeric types

`Atomic<u32>`, `Atomic<i32>` hoặc các atomic primitives tương ứng dùng:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

nhưng atomic semantics tách biệt với numeric arithmetic semantics.

Ví dụ:

```text
atomic_fetch_add
```

là atomic read-modify-write, không chỉ là:

```text
x + 1
```

---

# 64. Atomic overflow

Atomic integer arithmetic phải chỉ rõ semantics.

Ví dụ atomic wrapping increment:

```text
fetch_add
```

có thể có modulo semantics tương ứng với hardware.

Nếu muốn checked atomic operation thì API phải explicit.

---

# 65. Pointer arithmetic không thuộc numeric model

Dù pointer có numeric address ở machine level:

```text
pointer ≠ usize
```

đúng theo BOOTSTRAP-069.

Không cho:

```axiom
let p = address as *mut T
```

trong safe code.

---

# 66. `usize` không phải universal integer

Không nên dùng:

```text
usize
```

cho mọi integer chỉ vì native width.

Use:

```text
u32
u64
```

khi protocol/file/network/hardware specification yêu cầu width cụ thể.

---

# 67. Numeric ABI

Primitive scalar arguments có thể được truyền:

```text
register
stack
vector register
```

theo ABI target.

Numeric semantics không phụ thuộc vào cách truyền.

---

# 68. Optimization hierarchy

Compiler numeric optimization có thể thực hiện:

```text
constant folding
constant propagation
range analysis
overflow proof
strength reduction
division optimization
bit optimization
CSE
vectorization
SIMD lowering
FMA
loop optimization
```

miễn semantics được bảo toàn.

---

# 69. Integer overflow proof

Đây là cơ chế để Axiom vừa safe vừa nhanh.

Ví dụ:

```axiom
for i in 0..100 {
    let x = i * 4
}
```

compiler chứng minh:

```text
0 ≤ i < 100
i * 4 ≤ 396
```

→ `i * 4` không overflow.

Không cần runtime check.

---

# 70. Range facts

OptIR đã có:

```text
RangeInfo
```

từ BOOTSTRAP-056.

Numeric model cung cấp semantics cho các facts này.

Ví dụ:

```text
x ∈ [0, 100]
```

cho phép:

```text
bounds elimination
overflow elimination
switch optimization
SIMD vectorization
```

---

# 71. Checked arithmetic cold path

Nếu compiler không thể prove:

```text
x + y
```

không overflow, có thể generate:

```text
fast path:
    add

cold path:
    arithmetic panic/trap
```

Do đó checked semantics không nhất thiết làm common case chậm.

---

# 72. Đây là một điểm khác biệt quan trọng với C

C có thể đạt performance cao bằng cách cho optimizer dựa vào undefined behavior.

Axiom muốn:

```text
defined semantics
        +
proof-driven optimization
```

Thay vì:

```text
undefined behavior
        +
aggressive assumption
```

---

# 73. Debug và Release

Hai mode:

```text
debug
release
```

không được thay đổi semantic result của numeric operation.

Release có thể:

```text
prove check unnecessary
```

hoặc:

```text
move failure branch cold
```

nhưng nếu failure thực sự xảy ra thì observable semantics vẫn đúng.

---

# 74. `unsafe` không phải fast arithmetic mode

Không cho programmer nghĩ:

```text
unsafe {
    x + y
}
```

có nghĩa:

> bỏ overflow semantics để nhanh hơn.

Unsafe dành cho:

```text
raw memory
machine access
FFI
```

không phải để thay đổi numeric semantics.

---

# 75. Numeric intrinsics

Compiler có thể cung cấp intrinsic cho:

```text
add_with_overflow
sub_with_overflow
mul_with_overflow
leading_zeros
popcount
rotate
fma
sqrt
vector operations
```

nhưng intrinsic phải có semantic specification.

Không cho “compiler magic” không định nghĩa.

---

# 76. Target-specific instruction mapping

Ví dụ:

```text
count_ones
```

có thể thành:

```text
POPCNT
CNT
VPOPCNT
```

tùy target.

Programmer không cần biết instruction.

---

# 77. Saturating SIMD

Portable SIMD có thể hỗ trợ:

```text
saturating_add
saturating_sub
```

đặc biệt hữu ích với:

```text
u8
i8
```

image/audio processing.

Nếu target có native saturating instruction, backend sử dụng trực tiếp.

---

# 78. Numeric generics và monomorphization

Ví dụ:

```axiom
fn square<T: Mul>(x: T) -> T {
    x * x
}
```

specialize:

```text
i32
f32
f64
```

Compiler có thể tạo specialized machine code.

Không cần boxed numeric object.

---

# 79. Không có hidden boxing cho numeric generics

Không biến:

```axiom
square(10)
```

thành:

```text
heap allocated Number
virtual dispatch
```

trừ khi programmer explicit dùng dynamic abstraction.

---

# 80. Dynamic numeric dispatch

Nếu thật sự cần:

```text
dyn Numeric
```

thì dynamic dispatch là explicit.

Không phải default.

---

# 81. Numeric types và `Copy`

Primitive numeric values:

```text
i32
u64
f32
f64
```

là `Copy`.

SIMD vector values cũng có thể `Copy` nếu representation/semantics phù hợp.

---

# 82. No implicit narrowing

Đặc biệt:

```text
i64 → i32
f64 → f32
```

không implicit.

Điều này tránh hàng loạt bug numeric khi code được AI sinh tự động.

---

# 83. Float → integer

Phải explicit:

```text
as
try_as
saturating_as
```

tùy semantics.

Phải xác định:

- NaN
- infinity
- out of range
- fractional part

không để target CPU tự quyết định.

---

# 84. Integer → float

Cũng explicit.

Ví dụ:

```text
u64 → f64
```

có thể mất precision.

Compiler không được giả định conversion là exact.

---

# 85. Exactness

Numeric type system không hứa:

```text
u64 → f64 → u64
```

giữ nguyên giá trị.

Nếu programmer cần exact:

```text
checked conversion
```

phải được dùng.

---

# 86. Rounding

Floating rounding mode mặc định phải được định nghĩa rõ.

Axiom có thể chọn target-default/IEEE nearest-even làm baseline.

Các API/system layer có thể expose alternate rounding modes khi target hỗ trợ.

---

# 87. Dynamic rounding mode

Nếu rounding mode là observable machine state, compiler phải model nó.

Không được tự reorder floating operations qua một thay đổi rounding mode nếu làm thay đổi semantics.

---

# 88. Vectorization và reduction

Compiler chỉ được reorder floating reduction:

```text
a + b + c + d
```

khi semantics/profile cho phép.

Strict floating mode:

```text
((a+b)+c)+d
```

không tự động tương đương:

```text
(a+b)+(c+d)
```

---

# 89. Parallel numeric reduction

Tương tự:

```text
parallel sum
```

có thể cho kết quả khác floating strict sequential sum.

Do đó API phải xác định profile:

```text
strict
relaxed/associative
```

Không được âm thầm thay đổi.

---

# 90. Numeric execution domains

Numeric semantics dùng chung cho:

```text
CPU
GPU
SIMD
comptime
```

nhưng backend có thể có target-specific representation.

GPU numeric behavior cần explicit profile khi hardware có khác biệt.

---

# 91. Comptime numeric execution

```axiom
const x = 1000 * 2000
```

phải dùng cùng numeric semantics.

Không được:

```text
comptime overflow = compiler-specific
runtime overflow = khác
```

---

# 92. Comptime floating

Nếu compile-time cần floating math:

```text
const x = sqrt(4.0)
```

reproducibility phải được cân nhắc.

Compiler không nên phụ thuộc vào host floating environment một cách không kiểm soát.

---

# 93. Reproducible numeric compilation

Compiler semantic version + target + numeric profile phải là một phần compilation identity khi numeric behavior phụ thuộc configuration.

Đặc biệt với:

```text
fast-math
target feature
floating profile
```

---

# 94. Machine semantics boundary

Sau:

```text
Verified MIR
```

numeric semantics vẫn còn.

Sau:

```text
Machine IR
```

mới map thành:

```text
ADD
SUB
MUL
FADD
FMA
SIMD
```

Backend không được reinterpret semantics.

---

# 95. Numeric abstraction erasure

Ví dụ:

```axiom
fn square<T: Mul>(x: T) -> T
```

sau specialization có thể trở thành:

```text
single machine MUL
```

Trait/generic machinery biến mất.

---

# 96. Không bắt programmer chọn SIMD

Mục tiêu:

```text
portable Axiom source
        ↓
target analysis
        ↓
auto-vectorization
        ↓
best legal SIMD
```

Explicit SIMD chỉ cần khi programmer muốn kiểm soát algorithm/width.

---

# 97. Performance contract

Axiom không hứa:

> mọi chương trình Axiom luôn nhanh hơn C/C++.

Thay vào đó:

> **Core numeric semantics không áp đặt overhead runtime không cần thiết; compiler có đủ semantic information để tối ưu xuống native arithmetic/SIMD khi target và semantics cho phép.**

Đây là claim có thể bảo vệ được.

---

# 98. Core Numeric Surface

### Core

```text
bool
i8..i64
u8..u64
isize
usize
f32
f64
```

### Compiler-known operations

```text
arithmetic
comparison
bit operations
casts
overflow operations
atomic arithmetic
SIMD primitives
```

### Library

```text
BigInt
Decimal
Rational
Complex
FixedPoint
Math
LinearAlgebra
Tensor
```

### System/compiler

```text
target intrinsics
CPU feature detection
specialized SIMD
rounding control
hardware counters
```

---

# 99. Numeric invariants

## Integer

- **ANUM-20** Fixed-width integer types have target-independent bit widths.
- **ANUM-21** `isize` and `usize` match target pointer width.
- **ANUM-22** Numeric narrowing is never implicit.
- **ANUM-23** Boolean is not implicitly convertible to integer.
- **ANUM-24** C-style integer promotion is not part of Axiom semantics.
- **ANUM-25** Ordinary integer arithmetic has defined overflow behavior.
- **ANUM-26** Signed overflow is not undefined behavior.
- **ANUM-27** Checked arithmetic is the default semantic model where overflow is possible.
- **ANUM-28** Wrapping arithmetic is explicit.
- **ANUM-29** Saturating arithmetic is explicit.
- **ANUM-30** Checked arithmetic may return a failure value or trigger defined arithmetic failure semantics.
- **ANUM-31** Division by zero has defined failure semantics.
- **ANUM-32** Invalid shift counts have defined semantics.
- **ANUM-33** Signed right shift is arithmetic.
- **ANUM-34** Unsigned right shift is logical.
- **ANUM-35** Bit operations have explicit width semantics.
- **ANUM-36** Numeric casts are distinct from bit reinterpretation.
- **ANUM-37** Compile-time numeric literal overflow is a diagnostic.
- **ANUM-38** Release optimization cannot change integer semantics.
- **ANUM-39** Numeric range proofs may eliminate runtime checks.
- **ANUM-40** Overflow checks may be lowered to cold failure paths.

## Floating point

- **ANUM-41** `f32` and `f64` have defined floating representations.
- **ANUM-42** NaN is a valid floating value.
- **ANUM-43** Infinity is a valid floating value.
- **ANUM-44** Signed zero is semantically observable where IEEE behavior observes it.
- **ANUM-45** Floating equality does not imply reflexivity for NaN.
- **ANUM-46** Floating ordering is not assumed to be total.
- **ANUM-47** Floating bit equality is distinct from numeric equality.
- **ANUM-48** Floating operations have a defined default semantic profile.
- **ANUM-49** Optimization level does not implicitly enable fast-math.
- **ANUM-50** Relaxed floating semantics require an explicit contract/profile.
- **ANUM-51** FMA transformation is permitted only when floating semantics allow it.
- **ANUM-52** Floating reassociation is not permitted under strict semantics.
- **ANUM-53** Floating reduction reordering requires appropriate semantic permission.
- **ANUM-54** Float-to-integer conversion is explicit.
- **ANUM-55** Integer-to-float conversion is explicit.
- **ANUM-56** Potential precision loss is not silently hidden by type conversion.
- **ANUM-57** Rounding behavior is defined by the active floating profile.
- **ANUM-58** Observable rounding state constrains optimization.
- **ANUM-59** Comptime numeric semantics match runtime numeric semantics.
- **ANUM-60** Reproducible compilation accounts for target-dependent numeric configuration.

## SIMD

- **ANUM-61** SIMD vector values are distinct from fixed arrays.
- **ANUM-62** SIMD types have explicit lane count and element type.
- **ANUM-63** Portable SIMD is distinct from target-specific intrinsics.
- **ANUM-64** Unsupported SIMD operations may lower to scalar or synthesized code.
- **ANUM-65** SIMD lowering preserves scalar numeric semantics.
- **ANUM-66** SIMD masks are distinct from scalar booleans.
- **ANUM-67** SIMD comparison produces mask semantics.
- **ANUM-68** SIMD reductions preserve the active floating/integer semantic profile.
- **ANUM-69** SIMD alignment is not implicitly required unless contracted.
- **ANUM-70** Target SIMD features require target legality.
- **ANUM-71** Target-feature annotations are explicit contracts.
- **ANUM-72** Runtime CPU dispatch is not implicit.
- **ANUM-73** Auto-vectorization is permitted when semantic and target conditions are satisfied.
- **ANUM-74** Auto-vectorization may consume proven alias/disjointness facts.
- **ANUM-75** SIMD abstraction may be erased into native vector instructions.

## Optimization

- **ANUM-76** Numeric optimization cannot manufacture safety facts.
- **ANUM-77** Range analysis may prove overflow impossible.
- **ANUM-78** Range analysis may eliminate redundant bounds checks.
- **ANUM-79** Integer strength reduction must preserve defined overflow semantics.
- **ANUM-80** Integer constant folding follows language semantics.
- **ANUM-81** Floating constant folding follows the active floating profile.
- **ANUM-82** Generic numeric code may be monomorphized.
- **ANUM-83** Primitive numeric generics do not require boxing.
- **ANUM-84** Numeric operators may use compiler-known lowering.
- **ANUM-85** Intrinsics have specified semantic behavior.
- **ANUM-86** Backend instruction selection cannot reinterpret numeric semantics.
- **ANUM-87** Atomic arithmetic is distinct from ordinary arithmetic.
- **ANUM-88** Atomic ordering is preserved independently of numeric optimization.
- **ANUM-89** Numeric operations remain valid across CPU, GPU and comptime domains subject to domain-specific profiles.
- **ANUM-90** Unsafe is not a general numeric optimization mode.

## ABI / system

- **ANUM-91** Numeric ABI classification is target-specific.
- **ANUM-92** Numeric semantic types are distinct from their ABI locations.
- **ANUM-93** Endianness is a representation/serialization property, not a numeric value property.
- **ANUM-94** Byte conversion is explicit.
- **ANUM-95** Pointer values are not ordinary integers.
- **ANUM-96** `usize` is not a substitute for fixed-width protocol integers.
- **ANUM-97** Hardware-specific numeric behavior belongs to system/compiler layers unless explicitly standardized.
- **ANUM-98** Big integer/decimal/fixed-point types are library abstractions.
- **ANUM-99** Numeric abstraction can be erased without mandatory runtime overhead.
- **ANUM-100** Numeric semantics are invariant across optimization levels unless an explicit semantic profile says otherwise.

---

# Điểm rất đáng giá của BOOTSTRAP-075

Sau 075, Axiom có một chuỗi khá mạnh:

```text
Safe numeric semantics
        ↓
Range analysis
        ↓
Overflow proof
        ↓
Bounds proof
        ↓
Alias/capability proof
        ↓
Loop analysis
        ↓
Auto-vectorization
        ↓
SIMD
        ↓
Native instructions
```

Tức là thay vì thiết kế:

```text
"cho phép UB để đạt tốc độ"
```

Axiom thiết kế:

```text
"cho compiler nhiều proof hơn để đạt tốc độ"
```

Đây phù hợp trực tiếp với triết lý đã khóa trước đó:

> **Compiler Complexity Is Not Language Complexity.**

và:

> **Safe source không đồng nghĩa với runtime overhead bắt buộc.**

---

## Chuỗi kiến trúc tiếp theo

Sau numeric model, phần còn thiếu khá lớn là **I/O và OS resource model**. Theo roadmap ban đầu, đây chính là:

# BOOTSTRAP-076 — Axiom I/O, File, Socket, Process, OS Handle & Resource Model

Sẽ khóa các vấn đề như:

```text
File
Directory
Socket
Pipe
Process
Thread
Event
Timer
MMap
OS Handle
GPU Resource
```

đặc biệt là một câu hỏi rất quan trọng đối với triết lý Axiom:

> **Làm thế nào quản lý hàng triệu loại resource của OS bằng Move + Drop + Result mà không cần GC, không cần hidden runtime, không cần reference-counting mặc định, nhưng vẫn dùng async/IOCP/epoll/kqueue/IO_uring/GPU một cách hiệu quả?**