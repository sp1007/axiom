Tiếp tục.

# BOOTSTRAP-072 — Axiom Numeric Model, SIMD & Floating-Point Semantics

**Trạng thái: FROZEN**

Đây là phần rất quan trọng vì Axiom hướng tới cả **systems + GPU + AI/numerical computing**. Nếu numeric semantics không chặt ngay từ đầu, sau này rất dễ phải phá ABI, optimizer hoặc tensor model.

Mục tiêu:

> **Integer phải predictable. Floating-point phải có profile rõ ràng. SIMD phải là first-class capability nhưng không biến Core thành một tập intrinsic của từng CPU.**

---

# 1. Numeric type model

Core v1:

```text
bool

i8   i16   i32   i64
u8   u16   u32   u64

isize
usize

f32
f64
```

Chưa bắt buộc:

```text
i128
u128
f16
bf16
```

nhưng architecture phải cho phép bổ sung mà không phá type system.

---

# 2. Không có implicit numeric conversion nguy hiểm

Ví dụ:

```axiom
let x: i32 = 10
let y: i64 = x
```

Có thể cho phép widening conversion an toàn nếu specification xác định rõ.

Nhưng:

```axiom
let x: i64 = ...
let y: i32 = x
```

phải explicit:

```axiom
let y = x as i32
```

Không có C-style silent truncation.

---

# 3. Numeric conversion ≠ bit reinterpretation

Hai khái niệm hoàn toàn khác:

```text
CAST
BITCAST
```

### Cast

Thay đổi giá trị theo semantic numeric conversion.

```text
i32 → f32
i64 → i32
```

### Bitcast

Giữ nguyên bit pattern và thay đổi interpretation.

```text
u32 ↔ f32
```

chỉ hợp lệ nếu representation contract cho phép.

---

# 4. Integer overflow

Axiom **không dùng C-style signed overflow UB**.

Ví dụ:

```axiom
let x: i32 = max_i32
let y = x + 1
```

Không được biến thành:

```text
"compiler được phép làm bất kỳ thứ gì"
```

---

# 5. Ba arithmetic modes

Core nên cung cấp ba semantics rõ ràng:

```text
checked
wrapping
saturating
```

Ví dụ conceptually:

```axiom
x.checked_add(y)?
x.wrapping_add(y)
x.saturating_add(y)
```

Arithmetic operator bình thường:

```axiom
x + y
```

dùng **profile-defined default**, và compiler phải giữ semantics đó.

---

# 6. Default integer arithmetic

Khuyến nghị freeze:

```text
normal arithmetic
    ↓
checked semantics
```

trong debug/profile semantics.

Nhưng để release không tạo overhead ngoài mong muốn, compiler có thể chứng minh overflow impossible và loại check.

Nếu không chứng minh được, semantics vẫn phải được giữ.

Một profile có thể chọn trapping arithmetic nếu specification định nghĩa rõ.

Điểm quan trọng:

> **Optimization level không được thay đổi nghĩa của `+`.**

---

# 7. Wrapping arithmetic

Dùng khi programmer thực sự muốn modulo arithmetic:

```axiom
let x = a.wrapping_add(b)
```

Đặc biệt hữu ích cho:

- cryptography;
- hash;
- bit manipulation;
- ring counters;
- low-level algorithms.

---

# 8. Saturating arithmetic

Ví dụ:

```axiom
let x = a.saturating_add(b)
```

Kết quả dừng tại:

```text
MIN
MAX
```

rất hữu ích cho:

- image processing;
- DSP;
- audio;
- ML quantization;
- SIMD.

---

# 9. Overflow checking có thể được optimizer loại bỏ

Ví dụ:

```axiom
let x: u32 = 10
let y: u32 = x + 20
```

compiler biết chắc không overflow.

Machine code có thể chỉ còn:

```text
add
```

Không cần runtime check.

Đây là một ví dụ trực tiếp của:

```text
semantic safety
      ↓
proof
      ↓
optimization
      ↓
zero overhead
```

---

# 10. Division

Integer division phải có semantics xác định.

Với:

```text
x / y
```

nếu:

```text
y == 0
```

đây là runtime failure/trap theo numeric failure profile, không phải UB trong safe Core.

Compiler có thể chứng minh:

```text
y != 0
```

và loại check.

---

# 11. Signed division edge case

Trường hợp:

```text
MIN_INT / -1
```

có thể không biểu diễn được.

Axiom phải định nghĩa rõ:

```text
trap / checked failure
```

không để backend tự quyết định.

---

# 12. Remainder

`%` phải theo integer division semantics đã định nghĩa.

Không được để:

```text
CPU behavior
```

tự trở thành language semantics.

---

# 13. Shift

Axiom phải tránh UB kiểu C.

```axiom
x << n
x >> n
```

Nếu:

```text
n >= bit_width
```

phải có semantics xác định.

Khuyến nghị:

```text
normal shift → checked/trapping
```

và explicit:

```text
wrapping_shift_left
wrapping_shift_right
```

nếu cần machine-level semantics.

---

# 14. Logical vs arithmetic right shift

Unsigned:

```text
u >> n
```

logical shift.

Signed:

```text
i >> n
```

arithmetic shift.

Không phụ thuộc implementation-defined behavior.

---

# 15. Bit operations

Core/library nên có:

```text
and
or
xor
not
count_ones
count_zeros
leading_zeros
trailing_zeros
rotate_left
rotate_right
```

Compiler có thể map trực tiếp xuống instruction:

```text
POPCNT
LZCNT
TZCNT
ROL/ROR
CLZ/CTZ
```

khi target hỗ trợ.

---

# 16. Endianness

Numeric value trong Axiom không có "native endian" ở semantic level.

Endianness chỉ xuất hiện khi:

```text
value
 ↓
bytes
```

Ví dụ:

```text
to_le_bytes()
to_be_bytes()
from_le_bytes()
from_be_bytes()
```

Không để serialization phụ thuộc CPU endian mặc định.

---

# 17. Floating-point philosophy

Axiom không nên giả định:

```text
f32/f64 = mathematical real
```

Chúng là finite IEEE-style floating-point values với special values.

Có:

```text
NaN
+Infinity
-Infinity
+0
-0
```

nếu profile hỗ trợ IEEE semantics.

---

# 18. NaN

Không được coi:

```text
NaN == NaN
```

là true trong ordinary floating comparison.

Ordering cũng cần phân biệt:

```text
partial comparison
total ordering
```

---

# 19. Floating equality

Compiler không được biến:

```axiom
a == b
```

thành một phép toán toán học tùy ý.

Phải giữ:

- NaN behavior;
- signed zero behavior;
- selected floating profile.

---

# 20. `-0.0`

Axiom phải bảo tồn semantic distinction của:

```text
+0.0
-0.0
```

khi operation observable.

Không được optimizer tự động canonicalize nếu điều đó thay đổi observable result.

---

# 21. NaN payload

Không nên guarantee payload preservation trong Core arithmetic.

Nhưng cũng không được giả định mọi NaN giống nhau nếu representation-level operation yêu cầu payload.

Do đó:

```text
numeric semantics
≠
bitwise identity
```

như representation model đã freeze.

---

# 22. Fast math

Đây là điểm đặc biệt quan trọng.

**Không có fast-math mặc định.**

Compiler không được tự ý biến:

```text
(a + b) + c
```

thành:

```text
a + (b + c)
```

nếu floating semantics thay đổi.

---

# 23. Fast-math phải explicit

Có thể có compilation/profile option:

```text
fast-math
```

nhưng nó phải là **semantic compilation mode/contract rõ ràng**, không phải optimizer heuristic âm thầm.

Ví dụ:

```text
@fast_math
fn compute(...)
```

có thể được bổ sung ở attribute/system layer.

Nhưng Core v1 nên chưa cần surface syntax nếu chưa đủ specification.

---

# 24. Floating-point optimization

Compiler vẫn được:

```text
inline
CSE
constant-fold
vectorize
FMA
```

nếu semantics cho phép.

Ví dụ:

```text
a * b + c
```

không tự động thành FMA nếu profile yêu cầu strict operation semantics và FMA tạo khác biệt observable.

---

# 25. FMA

Có thể cung cấp explicit:

```text
mul_add(a, b, c)
```

để programmer yêu cầu fused multiply-add semantics.

Compiler map:

```text
FMA
```

nếu target hỗ trợ.

---

# 26. Floating-point profiles

Kiến trúc nên có:

```text
Strict
Relaxed
Fast
```

nhưng **Core v1 chỉ freeze Strict**.

Future profiles có thể được thêm mà không phá language.

Strict:

```text
reproducible semantics
NaN rules
signed-zero rules
rounding rules
observable FP behavior
```

được xác định.

---

# 27. Rounding

Core numeric library có thể cung cấp:

```text
round
floor
ceil
trunc
```

và conversion operations phải xác định behavior khi value nằm ngoài representable range.

---

# 28. Float → integer

Không implicit.

Ví dụ:

```axiom
let x: f64 = 3.14
let y = x as i32
```

phải có semantics rõ:

```text
truncate toward zero
```

và out-of-range:

```text
checked failure/trap
```

hoặc explicit saturating conversion.

Có thể có:

```text
to_int()
to_int_checked()
to_int_saturating()
```

---

# 29. Integer → float

Explicit hoặc widening-safe conversion tùy rule.

Điểm quan trọng:

```text
i64 → f32
```

có thể mất precision.

Do đó không coi đây là mathematically lossless chỉ vì range của exponent đủ lớn.

---

# 30. Decimal/fixed point

Không đưa decimal vào Core v1.

Nhưng library có thể xây:

```text
Decimal
Fixed<N>
QFormat
```

trên integer.

Điều này giữ Core nhỏ nhưng không khóa capability.

---

# 31. `usize` / `isize`

Dùng cho:

```text
index
length
allocation size
pointer-distance-like values
```

và target pointer width.

Ví dụ:

```text
x86-64 → usize = 64-bit
ARM64 → usize = 64-bit
```

Không được giả định `usize == u64` portable.

---

# 32. Index semantics

Array/vector indexing dùng `usize`.

```axiom
let x = values[i]
```

Safe indexing:

```text
bounds check
```

nếu compiler chưa chứng minh.

---

# 33. Bounds-check elimination

Compiler có thể chứng minh:

```axiom
for i in 0..n {
    use(values[i])
}
```

với:

```text
0 <= i < n
n <= values.length
```

thì remove bounds checks.

Không cần:

```text
unsafe
```

để đạt performance.

Đây là một điểm cốt lõi của Axiom.

---

# 34. Unchecked access

Khi programmer biết invariant nhưng compiler không chứng minh được:

```text
unsafe
```

API có thể cung cấp:

```text
get_unchecked(i)
```

hoặc tương đương.

Unsafe chỉ bypass check cụ thể; không tắt toàn bộ verifier.

---

# 35. SIMD model

SIMD không nên là:

```text
__m128
__m256
__m512
```

là toàn bộ language design.

Thay vào đó:

```text
Vector<T, N>
```

là abstraction.

Ví dụ:

```text
Vector<f32, 4>
Vector<i32, 8>
```

---

# 36. Vector là value

`Vector<T,N>` có value semantics.

```text
let a = ...
let b = a
```

nếu type thỏa Copy.

Không có heap allocation mặc định.

Representation có thể là:

```text
register
stack
memory
```

theo backend.

---

# 37. SIMD width

`N` là logical lane count.

Physical mapping:

```text
Vector<f32,4>
   ↓
SSE / NEON / scalar

Vector<f32,8>
   ↓
AVX2 / NEON multiple vectors / scalar

Vector<f32,16>
   ↓
AVX-512 / multiple registers
```

Không để source code phụ thuộc một ISA cụ thể.

---

# 38. Portable SIMD

Library có thể định nghĩa:

```text
Vector<T, N>
Mask<N>
```

với operations:

```text
add
sub
mul
div
min
max
select
compare
shuffle
reduce
```

Compiler vectorizer có thể lower xuống target-native SIMD.

---

# 39. Target SIMD

System layer cung cấp:

```text
x86::...
arm::...
riscv::...
```

cho các instruction đặc biệt.

Target intrinsics cần explicit target feature.

---

# 40. Target feature

Ví dụ conceptually:

```text
@target_feature("avx2")
```

Compiler kiểm tra target support.

Không được sinh instruction mà deployment target không hỗ trợ.

---

# 41. Portable SIMD fallback

Một generic implementation:

```text
Vector<T, N>
```

phải có thể compile trên target không có native vector width tương ứng.

Backend có thể:

```text
vectorize
multi-register
scalarize
```

mà không thay đổi semantics.

---

# 42. Mask

SIMD comparison trả:

```text
Mask<N>
```

không phải `Vector<bool,N>` theo nghĩa ordinary integer vector.

Ví dụ:

```text
mask = a > b
result = select(mask, a, b)
```

Backend có thể dùng native predicate/mask registers.

---

# 43. SIMD gather/scatter

Có thể hỗ trợ trong library:

```text
gather
scatter
```

nhưng semantics phải rõ về:

- bounds;
- duplicate indices;
- alias;
- ordering.

Đặc biệt scatter với duplicate indices không được giả định ordering tùy ý nếu semantics không quy định.

---

# 44. SIMD memory access

```text
load
store
```

phải tách:

```text
aligned
unaligned
```

nếu target semantics cần.

Nhưng ordinary `Vector` load/store không nên bắt programmer quản lý alignment bằng pointer bureaucracy.

Compiler biết layout.

---

# 45. Vector alignment

Default alignment compiler-controlled.

Nếu cần explicit:

```text
@align(N)
```

đã có trong representation contracts.

---

# 46. SIMD + ownership

Ví dụ:

```axiom
fn add(
    a: view<Vector<f32, 8>>,
    b: view<Vector<f32, 8>>,
    out: mut_view<Vector<f32, 8>>
)
```

alias verifier áp dụng bình thường.

Không cần một hệ thống alias riêng cho SIMD.

---

# 47. Auto-vectorization

Axiom optimizer có thể tự biến:

```axiom
for i in 0..n {
    out[i] = a[i] + b[i]
}
```

thành vector loop nếu chứng minh:

```text
bounds
alias safety
dependence
target legality
```

Đây chính là nơi ownership + capability model đem lại lợi ích lớn.

---

# 48. Vectorization không được tạo race

Nếu:

```text
a
b
out
```

có overlap không xác định:

```text
UNKNOWN
```

optimizer không được tự coi chúng là disjoint.

Không cần programmer viết `restrict`.

---

# 49. Explicit no-alias future

Nếu sau này cần API chuyên biệt:

```text
@noalias
```

có thể là contract.

Nhưng Core v1 không cần.

Ownership/capability proof là nguồn alias information chính.

---

# 50. Integer SIMD overflow

Vector integer arithmetic phải tuân cùng semantics scalar:

```text
checked
wrapping
saturating
```

Ví dụ:

```text
Vector<u8,16>.saturating_add(...)
```

rất hữu ích cho image processing.

Không được để SIMD instruction tự quyết định language semantics.

---

# 51. Floating SIMD

`Vector<f32,N>` dùng cùng floating semantics với `f32`.

Không được có:

```text
scalar f32 = strict
SIMD f32 = fast math
```

một cách ngầm định.

---

# 52. Tensor boundary

Tensor **không phải Core primitive**.

Nó là Standard/Application/ML library abstraction:

```text
Tensor<T, Shape, Layout>
```

có thể xây trên:

```text
Buffer<T>
view<T>
Vector<T,N>
DeviceBuffer<T>
```

---

# 53. Tensor có thể compile-time specialize

Ví dụ:

```text
Tensor<f32, [1024, 1024]>
```

compiler/comptime có thể biết shape.

Nhưng không biến toàn bộ tensor algebra thành dependent type theorem system.

Shape parameters ban đầu có thể giới hạn ở:

```text
integer const parameters
```

đã có trong generic model.

---

# 54. Matrix/vector

Library có thể cung cấp:

```text
Vec<N,T>
Mat<R,C,T>
```

nhưng tránh xung đột tên với `view`, `Vector`.

Đây là domain library, không phải semantic primitive.

---

# 55. GPU numeric model

GPU dùng cùng:

```text
i/u/f
Vector
atomic
```

semantics ở mức Axiom.

Backend chịu trách nhiệm lower sang:

```text
CUDA-like ISA
SPIR-V
DXIL
Metal
```

hoặc target tương ứng.

Không tạo một ngôn ngữ GPU thứ hai.

---

# 56. FP16 / BF16

Kiến trúc phải để type system mở:

```text
f16
bf16
```

nhưng chưa nhất thiết freeze Core v1.

Lý do:

- target support khác nhau;
- arithmetic semantics khác;
- ABI;
- GPU semantics;
- promotion rules.

Nên đưa vào **Numeric Extension** sau khi base floating model ổn định.

---

# 57. `f16` không nên tự động promote mọi nơi

Khi bổ sung:

```text
f16
bf16
```

phải định nghĩa rõ:

```text
storage type
arithmetic type
accumulation type
```

đặc biệt cho ML.

Ví dụ matrix multiplication có thể:

```text
f16 inputs
f32 accumulation
f16 output
```

nhưng đây là explicit library/kernel semantics, không phải hidden conversion.

---

# 58. Determinism

Axiom phải phân biệt:

```text
language deterministic
```

với:

```text
parallel numerical reduction
```

Ví dụ:

```text
sum([a,b,c,d])
```

trên parallel GPU có thể có thứ tự khác.

Floating-point result có thể khác nếu reduction ordering khác.

Do đó numerical library phải chọn explicit policy:

```text
deterministic reduction
```

hoặc:

```text
parallel relaxed reduction
```

Core không giả vờ rằng mọi parallel FP reduction luôn bit-identical.

---

# 59. Constant folding

Comptime có thể evaluate:

```text
const x = 3.14 * 2.0
```

nhưng kết quả phải theo cùng numeric semantics được specification định nghĩa.

Compiler không được dùng host CPU's floating behavior một cách vô điều kiện rồi coi đó là Axiom result.

---

# 60. Host/target numeric difference

Comptime:

```text
host CPU
```

runtime:

```text
target CPU/GPU
```

có thể khác.

Do đó numeric evaluation phải có target-aware semantics khi kết quả phụ thuộc target.

Đây nối trực tiếp với `BOOTSTRAP-037` về Comptime host/target.

---

# 61. Constant overflow

Ví dụ:

```axiom
const x: u8 = 300
```

phải là compiler diagnostic.

Không silently wrap.

Nếu muốn:

```axiom
const x: u8 = 300 as u8
```

thì conversion semantics phải xác định.

---

# 62. Numeric literals

Compiler phải infer literal type theo context nhưng không được để inference mơ hồ.

Ví dụ:

```axiom
let x: i32 = 10
```

→ `10` là i32.

Trong context:

```axiom
let x: u64 = 10
```

→ `10` là u64.

Nếu không có context:

```axiom
let x = 10
```

phải có default literal type deterministic.

---

# 63. Numeric literal default

Khuyến nghị:

```text
integer literal → i32
floating literal → f64
```

nếu không có context.

Nhưng compiler có thể diagnose overflow thay vì tự chọn type lớn hơn.

Ví dụ:

```text
let x = 999999999999999999999
```

không tự động nhảy sang arbitrary precision integer.

---

# 64. Big integer

`BigInt` là library type.

Không phải primitive.

Comptime có thể hỗ trợ arbitrary precision internally nếu cần để tính toán compiler, nhưng runtime `BigInt` là explicit type.

---

# 65. `bool` không phải integer

Không cho:

```axiom
let x: i32 = true
```

hoặc:

```axiom
if 1 { ... }
```

Không có C truthiness.

Điều này đặc biệt quan trọng khi compiler tự vectorize/control-flow.

---

# 66. Numeric generic constraints

Trait system cung cấp domain constraints:

```text
Add
Sub
Mul
Div
Ord
```

Nhưng primitive operators có compiler-known fast paths.

Ví dụ:

```axiom
fn add<T: Add>(a: T, b: T) -> T
```

có thể specialize thành native integer/SIMD instruction.

---

# 67. Operator semantics

Operator:

```text
+
-
*
/
%
```

được trait-based về mặt abstraction, nhưng compiler có built-in semantics cho primitives.

Điều này cho phép:

```text
generic abstraction
+
zero-cost primitive lowering
```

---

# 68. No implicit promotion chain

Tránh C/C++ kiểu:

```text
u8
→ int
→ unsigned int
→ long
→ ...
```

Axiom chỉ áp dụng conversion rules đã định nghĩa.

Điều này giúp:

- compiler;
- AI;
- static analysis;
- code generation

đều deterministic hơn.

---

# 69. Numeric ABI

ABI classification phải phân biệt:

```text
scalar
vector
aggregate
```

Ví dụ:

```text
Vector<f32,4>
```

có thể đi qua SIMD registers nếu target ABI cho phép.

Nhưng source semantics không phụ thuộc việc nó nằm ở register hay stack.

---

# 70. Numeric representation

Default:

```text
semantic value
    ≠
physical bits
```

Ngoại lệ:

```text
@repr(C)
@repr(transparent)
bitcast
FFI
serialization
```

có thể tạo representation contract.

---

# Frozen Invariants — `ANUM-20..100`

### Integer

- **ANUM-20** Integer types have explicit width semantics.
- **ANUM-21** Signed and unsigned integers are distinct types.
- **ANUM-22** `usize` and `isize` are target pointer-width types.
- **ANUM-23** Boolean is not an integer.
- **ANUM-24** Implicit numeric narrowing is forbidden.
- **ANUM-25** Numeric conversion and bit reinterpretation are distinct.
- **ANUM-26** Signed overflow is not C-style undefined behavior.
- **ANUM-27** Integer arithmetic has defined overflow semantics.
- **ANUM-28** Checked arithmetic is supported.
- **ANUM-29** Wrapping arithmetic is explicit.
- **ANUM-30** Saturating arithmetic is explicit.
- **ANUM-31** Compiler may eliminate proven overflow checks.
- **ANUM-32** Optimization cannot alter overflow semantics.
- **ANUM-33** Division by zero has defined failure semantics.
- **ANUM-34** Signed division edge cases have defined semantics.
- **ANUM-35** Shift counts have defined semantics.
- **ANUM-36** Signed right shift is arithmetic.
- **ANUM-37** Unsigned right shift is logical.
- **ANUM-38** Bit operations have explicit semantics.
- **ANUM-39** Endianness is a byte-representation concern.
- **ANUM-40** Native endianness does not alter numeric value semantics.

### Floating point

- **ANUM-41** `f32` and `f64` have defined floating-point semantics.
- **ANUM-42** NaN behavior is explicitly defined.
- **ANUM-43** Signed zero is semantically relevant where observable.
- **ANUM-44** Infinity is explicitly represented where supported.
- **ANUM-45** Floating equality preserves NaN semantics.
- **ANUM-46** Floating ordering distinguishes partial ordering from total ordering.
- **ANUM-47** Floating bit identity is distinct from numeric equality.
- **ANUM-48** Default floating semantics are not fast-math.
- **ANUM-49** Compiler cannot reassociate floating operations unless permitted by the active semantic profile.
- **ANUM-50** FMA behavior is explicit.
- **ANUM-51** Rounding behavior is defined.
- **ANUM-52** Float-to-integer conversion has defined range behavior.
- **ANUM-53** Integer-to-float conversion has defined precision behavior.
- **ANUM-54** Fast-math is not implicit.
- **ANUM-55** Floating optimization cannot silently change observable semantics.
- **ANUM-56** Comptime floating evaluation follows Axiom numeric semantics.
- **ANUM-57** Host floating behavior cannot silently redefine target semantics.

### SIMD

- **ANUM-58** SIMD vectors are ordinary semantic values.
- **ANUM-59** SIMD values require no heap allocation by default.
- **ANUM-60** `Vector<T,N>` is portable across targets.
- **ANUM-61** Physical SIMD width is a backend concern.
- **ANUM-62** Portable SIMD may scalarize when required.
- **ANUM-63** Target SIMD intrinsics are explicit system/compiler abstractions.
- **ANUM-64** Target feature requirements are explicit.
- **ANUM-65** SIMD arithmetic follows scalar numeric semantics.
- **ANUM-66** SIMD integer overflow behavior is explicit.
- **ANUM-67** SIMD floating semantics match scalar floating semantics unless an explicit profile says otherwise.
- **ANUM-68** SIMD masks are distinct semantic values.
- **ANUM-69** SIMD memory access obeys Axiom bounds and capability rules.
- **ANUM-70** SIMD aliasing uses the same capability/alias model as scalar memory.
- **ANUM-71** Auto-vectorization requires legal dependence/alias/range conditions.
- **ANUM-72** Auto-vectorization cannot assume UNKNOWN regions are disjoint.
- **ANUM-73** SIMD optimization cannot alter ownership semantics.
- **ANUM-74** SIMD optimization cannot alter memory-ordering semantics.
- **ANUM-75** Gather/scatter semantics explicitly define bounds and duplicate-index behavior.

### Performance / ABI

- **ANUM-76** Bounds checks may be eliminated by proof.
- **ANUM-77** Unchecked numeric/memory operations are explicit unsafe mechanisms.
- **ANUM-78** Numeric abstractions may lower directly to machine instructions.
- **ANUM-79** Numeric wrappers do not require runtime allocation.
- **ANUM-80** Numeric wrappers do not require dynamic dispatch.
- **ANUM-81** Numeric representation is distinct from numeric semantics.
- **ANUM-82** ABI classification is target-specific.
- **ANUM-83** Vector ABI classification is target-specific.
- **ANUM-84** Register vs memory placement does not alter numeric semantics.
- **ANUM-85** Numeric literals have deterministic inference.
- **ANUM-86** Literal overflow is diagnosed rather than silently widening.
- **ANUM-87** Default integer and floating literal types are deterministic.
- **ANUM-88** Big integer is a library type, not a Core primitive.
- **ANUM-89** Decimal/fixed-point arithmetic is a library abstraction.
- **ANUM-90** `f16`/`bf16` can be added without redesigning the numeric model.
- **ANUM-91** Mixed-precision arithmetic requires explicit library/kernel semantics.
- **ANUM-92** Tensor types are library abstractions.
- **ANUM-93** Matrix types are library abstractions.
- **ANUM-94** GPU numeric execution uses Axiom numeric semantics.
- **ANUM-95** GPU numeric lowering is target-specific.
- **ANUM-96** Parallel floating reductions may require explicit determinism policy.
- **ANUM-97** Deterministic numeric execution is distinct from deterministic scheduling.
- **ANUM-98** Comptime numeric results participate in target-aware dependency identity.
- **ANUM-99** Numeric semantics are preserved across MIR, ABI, SIMD, GPU and FFI lowering.
- **ANUM-100** Numeric optimization may remove overhead only when observable numeric semantics remain unchanged.

---

## Một quyết định quan trọng cho Axiom

Đến đây Axiom bắt đầu có một chuỗi rất mạnh:

```text
                  SOURCE
                    │
          ┌─────────┴─────────┐
          │                   │
      Ownership            Numeric
      Capability           Semantics
          │                   │
          └─────────┬─────────┘
                    ▼
               Verified MIR
                    │
             ┌──────┴──────┐
             │             │
          Alias          Range
           Proof          Proof
             │             │
             └──────┬──────┘
                    ▼
                 OptIR
                    │
          ┌─────────┼─────────┐
          ▼         ▼         ▼
       Scalar     SIMD       GPU
```

Điều này có nghĩa **SIMD/GPU không cần một hệ thống type/safety hoàn toàn khác**.

Một vòng lặp Axiom bình thường:

```axiom
for i in 0..n {
    out[i] = a[i] + b[i]
}
```

có thể bắt đầu là scalar semantic MIR, sau đó compiler chứng minh:

```text
bounds ✓
ownership ✓
alias ✓
dependence ✓
overflow semantics ✓
```

rồi tự chuyển thành SIMD/GPU code.

Đây là hướng rất phù hợp với mục tiêu của bạn: **lập trình viên viết code đơn giản, còn compiler gánh phần phức tạp.**

### Tiếp theo

`BOOTSTRAP-073` nên chốt **Axiom String, Unicode, Text, Bytes & Encoding Model**.

Phần này đặc biệt đáng làm kỹ vì Axiom có mục tiêu **UTF-8 mặc định + AI + multilingual + networking + FFI**. Nó sẽ quyết định:

```text
Str
String
Bytes
view<u8>
Unicode scalar
grapheme
UTF-8 validation
indexing
substring
normalization
case conversion
ASCII fast path
zero-copy text
FFI/C string
```

và quan trọng nhất: **không để Unicode biến mọi thao tác String thành chậm**, đồng thời vẫn giữ UTF-8 an toàn.