Tiếp tục.

# BOOTSTRAP-068 — Axiom Numeric Model, Integer Semantics, Floating-Point & SIMD

**Trạng thái: FROZEN**

Đây là một phần rất quan trọng vì nếu thiết kế numeric model không chặt, các mục tiêu **native performance, vectorization, GPU, ABI, deterministic behavior** sẽ bị ảnh hưởng.

Mục tiêu của Axiom:

> **Hiệu năng native mặc định, semantics rõ ràng, không có undefined behavior kiểu C đối với số nguyên, nhưng cũng không biến mọi phép toán thành checked arithmetic đắt đỏ.**

---

# 1. Hệ kiểu số Core

Giữ hệ thống cơ bản:

```text
Signed:
    i8
    i16
    i32
    i64
    isize

Unsigned:
    u8
    u16
    u32
    u64
    usize

Floating:
    f32
    f64
```

`i128/u128` **không đưa vào Core v1** nhưng thiết kế type system phải cho phép bổ sung sau này.

Không có:

```text
int
uint
float
double
```

là kiểu mơ hồ phụ thuộc target.

Nếu cần alias ở library:

```text
Int = i32
Float = f32
```

nhưng đó chỉ là alias.

---

# 2. Vì sao phải có kích thước cố định?

Axiom cần binary/native/FFI/GPU predictable.

Ví dụ:

```axiom
let a: i32
```

luôn có semantic width 32-bit.

Trong khi:

```axiom
let b: isize
```

phụ thuộc target word size.

Điều này cho phép:

```text
i32 → portable numeric semantics
isize → address/index-sized semantics
```

`usize` đặc biệt phù hợp:

- array index;
- collection length;
- memory size;
- pointer-related arithmetic trong system layer.

---

# 3. Integer không có C-style undefined overflow

Ví dụ:

```axiom
let x: i32 = MAX_I32
let y = x + 1
```

Không được phép có semantics:

> "compiler được phép làm bất cứ điều gì vì signed overflow UB."

Axiom phải định nghĩa rõ.

Nhưng cũng **không nên** biến:

```axiom
x + y
```

thành checked operation bắt buộc trên mọi machine instruction.

Giải pháp:

### Default arithmetic

Phép toán integer thông thường có **defined target-independent semantics** theo arithmetic profile của Axiom.

Compiler phải đảm bảo kết quả theo profile đó.

### Explicit variants

Library/compiler cung cấp:

```text
checked_add
checked_sub
checked_mul

wrapping_add
wrapping_sub
wrapping_mul

saturating_add
saturating_sub
saturating_mul
```

Ví dụ:

```axiom
let x = a.wrapping_add(b)
let y = a.checked_add(b)?
let z = a.saturating_add(b)
```

---

# 4. Quyết định quan trọng: default integer semantics

Tôi đề xuất:

> **Default integer arithmetic là two's-complement modular arithmetic đối với fixed-width integer types.**

Tức:

```text
uN: modulo 2^N
iN: modulo 2^N, diễn giải theo two's complement
```

Ví dụ `u8`:

```text
255 + 1 = 0
```

và `i8`:

```text
127 + 1 = -128
```

Điều này có vài lợi ích:

- không UB;
- machine code tự nhiên;
- tối ưu tốt;
- SIMD-friendly;
- GPU-friendly;
- predictable;
- không cần runtime check mặc định.

Nếu programmer muốn phát hiện overflow:

```axiom
let result = a.checked_add(b)?
```

---

# 5. Không được nhầm `checked` với default safety

Safe code:

```axiom
let x = a + b
```

vẫn an toàn memory-wise.

Overflow không biến thành:

```text
memory corruption
```

hay:

```text
undefined behavior
```

Đây là một quyết định rất quan trọng.

---

# 6. Integer conversion

Không cho phép các conversion nguy hiểm xảy ra âm thầm.

Ví dụ:

```axiom
let x: i64 = 100
let y: i32 = x
```

phải có conversion rõ ràng nếu có khả năng narrowing.

Ví dụ:

```axiom
let y = x as i32
```

`as` là conversion semantic.

Nhưng cần phân biệt:

```text
numeric conversion
bit reinterpretation
```

---

# 7. `as` không phải BITCAST

Ví dụ:

```axiom
let x: i32 = -1
let y = x as u32
```

đây là **numeric conversion** với semantics đã định nghĩa.

Trong khi:

```axiom
bitcast<f32>(x)
```

là:

> giữ nguyên bit pattern, thay đổi interpretation.

Hai operation không được nhập làm một.

---

# 8. Signed / unsigned mixing

Không nên cho:

```axiom
let a: i32
let b: u32

let c = a + b
```

tự động chọn một conversion "thông minh".

Phải có type rõ ràng.

Ví dụ:

```axiom
let c = a as i64 + b as i64
```

hoặc conversion phù hợp.

Lý do:

> implicit integer promotion là một trong những nguồn bug khó phát hiện của C/C++.

---

# 9. Constant arithmetic

Compiler phải tính compile-time nếu operand là constant:

```axiom
const SIZE = 1024 * 1024
```

nhưng semantics phải giống runtime arithmetic.

Không được có:

```text
runtime arithmetic ≠ comptime arithmetic
```

nếu cùng type/profile.

---

# 10. Compile-time overflow

Nếu expression được yêu cầu compile-time:

```axiom
const x: u8 = 255 + 1
```

thì vẫn áp dụng semantics integer đã định nghĩa.

Nếu expression nằm trong context yêu cầu constant hợp lệ mà kết quả không phù hợp type/conversion contract, compiler diagnostic phải rõ ràng.

Comptime không phải một numeric language riêng.

---

# 11. Integer division

Cần định nghĩa rõ:

```text
/
%
```

đối với signed integers.

Axiom chọn semantics:

> Signed division truncates toward zero.

Ví dụ về mặt toán học:

```text
-7 / 3 = -2
-7 % 3 = -1
```

và invariant:

```text
a == (a / b) * b + (a % b)
```

trong các trường hợp division hợp lệ.

---

# 12. Division by zero

Không được undefined.

```axiom
let x = a / 0
```

là runtime failure theo panic/trap profile.

Compiler phát hiện được constant zero:

```text
compile-time diagnostic
```

nếu expression compile-time known.

Không cần exception.

---

# 13. MIN / -1

Trường hợp:

```text
MIN_INT / -1
```

không thể biểu diễn trong signed type.

Axiom phải định nghĩa rõ và không cho phép UB.

Tôi đề xuất:

> signed division overflow sử dụng arithmetic failure/trap semantics, không wrap âm thầm.

Lý do: khác với `+`, `-`, `*`, division overflow thường là programmer error và không map tự nhiên vào một hardware integer operation thống nhất.

Nếu muốn modular arithmetic:

```axiom
wrapping_div(...)
```

có thể tồn tại ở library/system nếu cần.

---

# 14. Shift

Các operation:

```text
<<
>>
```

phải có semantics defined.

Shift amount nằm ngoài range width không được trở thành target-dependent behavior.

Tôi đề xuất:

```text
0 <= shift < bit_width
```

là semantic requirement của normal shift.

Nếu compiler không chứng minh:

```text
shift < width
```

thì runtime check.

Có API:

```text
wrapping_shift_left
wrapping_shift_right
```

nếu cần semantics đặc biệt.

---

# 15. Bit operations

Core nên hỗ trợ:

```text
&
|
^
~
```

và library/intrinsic:

```text
count_ones
count_zeros
leading_zeros
trailing_zeros
rotate_left
rotate_right
byte_swap
reverse_bits
```

Compiler có thể map trực tiếp tới:

```text
POPCNT
LZCNT
TZCNT
ROL/ROR
REV
```

hoặc instruction tương ứng target.

---

# 16. Boolean không phải integer

Không cho:

```axiom
let x: i32 = true
```

hoặc:

```axiom
if 1 { ... }
```

Chỉ:

```axiom
if condition { ... }
```

với `condition: bool`.

Điều này làm control-flow predictable và loại bỏ nhiều implicit conversion của C.

---

# 17. Floating-point

Axiom hỗ trợ:

```text
f32
f64
```

với semantics dựa trên IEEE-754 phù hợp target.

Các khái niệm:

```text
+0
-0
NaN
+∞
-∞
subnormal
```

phải được giữ khi profile yêu cầu.

Không được compiler mặc định giả định:

```text
x + 0 == x
```

nếu `NaN` hoặc signed zero làm phép biến đổi đó thay đổi observable behavior.

---

# 18. Fast math không được mặc định

Đây là điểm rất quan trọng cho compiler optimizer.

Axiom mặc định:

```text
IEEE-aware semantics
```

Compiler **không tự ý** biến:

```text
(a + b) + c
```

thành:

```text
a + (b + c)
```

nếu điều đó thay đổi floating-point semantics.

Fast-math phải là explicit profile/attribute/build contract.

Ví dụ về sau:

```text
@fast_math
```

hoặc compiler profile tương đương.

Nhưng nó phải là **semantic contract**, không chỉ optimization hint.

---

# 19. Floating-point determinism

Không hứa rằng:

> mọi CPU/GPU luôn cho bit-identical floating-point result.

Vì:

- instruction set khác nhau;
- FMA;
- rounding mode;
- extended precision;
- GPU floating semantics.

Thay vào đó Axiom định nghĩa:

```text
language semantics
+
target floating profile
```

và explicit strict/deterministic modes nếu application yêu cầu.

---

# 20. FMA

Compiler có thể dùng:

```text
a * b + c
```

→ FMA

**chỉ khi profile/semantics cho phép**.

Trong strict FP:

```text
mul
add
```

và:

```text
fma
```

có thể khác kết quả.

Không được âm thầm thay đổi.

---

# 21. Rounding mode

Core không cần biến rounding mode thành một object phức tạp.

Nhưng numeric model phải có concept:

```text
rounding mode
```

cho target/profile cần thiết.

Standard library có thể cung cấp APIs:

```text
round
floor
ceil
trunc
```

và system layer cho dynamic hardware rounding control.

---

# 22. NaN semantics

Không dùng:

```text
NaN == NaN
```

như equality thông thường nếu IEEE comparison semantics yêu cầu false.

Do đó:

```text
numeric equality
```

và:

```text
total ordering
```

là hai concept khác nhau.

Library có thể cung cấp:

```text
total_cmp
```

để sorting.

Điều này đặc biệt quan trọng cho:

- sort;
- ordered collections;
- generic `Ord`;
- deterministic algorithms.

---

# 23. Numeric traits

Operators nên đi qua trait model đã freeze.

Ví dụ conceptually:

```text
Add<T>
Sub<T>
Mul<T>
Div<T>
Rem<T>
BitAnd<T>
BitOr<T>
BitXor<T>
Shl<T>
Shr<T>
```

Nhưng primitive numeric operations có thể được compiler lower trực tiếp.

Do đó:

```axiom
a + b
```

không đồng nghĩa với:

```text
runtime virtual function call
```

Generic code vẫn có thể monomorphize.

---

# 24. SIMD

Không nên đưa:

```text
float4
float8
float16
```

thành một đống primitive Core.

Thay vào đó:

```text
SIMD<T, N>
```

là library/compiler-recognized abstraction.

Ví dụ:

```axiom
let a: SIMD<f32, 8>
let b: SIMD<f32, 8>

let c = a + b
```

Compiler có thể map:

```text
SIMD<f32, 8>
```

→ AVX/AVX2/AVX-512

hoặc:

```text
ARM NEON/SVE
RISC-V Vector
GPU vector representation
```

tùy target.

---

# 25. SIMD width không nhất thiết bằng hardware width

Đây là điểm quan trọng.

```text
SIMD<f32, 8>
```

không nhất thiết có một physical register chứa chính xác 8 phần tử.

Backend có thể:

```text
8 × f32
↓
1 × 256-bit vector
```

hoặc:

```text
2 × 128-bit vectors
```

hoặc scalarize nếu target không hỗ trợ.

Semantic vector length vẫn là 8.

---

# 26. Portable SIMD và target intrinsics

Hai tầng:

```text
Portable SIMD
    ↓
SIMD<T,N>
```

và:

```text
Target Intrinsics
    ↓
x86 / ARM / RISC-V specific
```

Portable SIMD ưu tiên portability.

Target intrinsic dành cho programmer cần machine-specific behavior.

---

# 27. SIMD mask

Nên có:

```text
Mask<N>
```

và operations kiểu:

```text
select(mask, a, b)
```

để compiler có thể map:

```text
blend
masked load/store
predication
vector compare
```

Không cần ép programmer sử dụng assembly.

---

# 28. SIMD và alias analysis

Đây là nơi mô hình `view` của Axiom phát huy tác dụng.

Ví dụ:

```axiom
fn add(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
)
```

Nếu verifier chứng minh:

```text
a DISJOINT out
b DISJOINT out
```

optimizer có thể tạo vector loop.

Nếu:

```text
UNKNOWN
```

thì không được tự suy đoán no-alias.

Compiler có thể:

- version loop;
- runtime alias check;
- scalar fallback;
- hoặc không vectorize.

Không cần `restrict` trong source language v1.

---

# 29. Auto-vectorization

Programmer không cần viết:

```text
@vectorize
```

cho loop thông thường.

Compiler phân tích:

```text
loop
range
dependence
alias
alignment
target
cost model
```

và tự vectorize nếu có lợi.

Ví dụ:

```axiom
for i in 0..n {
    c[i] = a[i] + b[i]
}
```

có thể trở thành SIMD.

Nếu không vectorize được, semantics vẫn giống nhau.

---

# 30. Alignment

Default:

> compiler tự quản lý alignment.

Programmer không phải viết alignment cho mọi array.

Khi cần contract:

```axiom
@align(64)
struct ...
```

hoặc storage abstraction tương ứng.

`@align` đã thuộc representation/system model.

Unsafe packed access phải tuân thủ alignment rules.

---

# 31. Numeric literals

Axiom cần inference rõ.

Ví dụ:

```axiom
let x = 10
```

compiler chọn default integer type theo deterministic rule.

Tôi đề xuất:

```text
integer literal default = i32
floating literal default = f64
```

nếu không có expected type.

Nhưng trong:

```axiom
let x: u64 = 10
```

literal được type-check trực tiếp thành `u64`, không phải:

```text
i32 → u64
```

rồi mới convert.

Điều này giúp tránh overflow/conversion không cần thiết trong generic/comptime code.

---

# 32. Generic numeric code

Không cần language-level numeric tower.

Ví dụ:

```axiom
fn sum<T: Add<T> + Zero>(values: view<T>) -> T
```

nhưng standard library nên cung cấp các trait tổng hợp tiện dụng như:

```text
Integer
SignedInteger
UnsignedInteger
Float
Number
```

Các trait này là library/compiler-known constraints, không phải subtype hierarchy.

---

# 33. Decimal / BigInt

Không đưa vào Core.

Nếu cần:

```text
Decimal
BigInt
BigDecimal
Rational
Complex
```

→ Standard/community library.

Nhưng compiler phải hỗ trợ:

```text
operator traits
generic specialization
comptime
```

để các type này có syntax tự nhiên.

---

# 34. Complex number

Tương tự:

```text
Complex<f32>
Complex<f64>
```

library type.

Compiler có thể tối ưu struct:

```text
{ re, im }
```

và vectorize nếu phù hợp.

Không cần primitive `complex128`.

---

# 35. GPU numeric semantics

GPU kernel sử dụng cùng numeric type system:

```text
i32
u32
f32
f64
SIMD
```

nhưng target GPU có thể giới hạn một số type.

Nếu target không hỗ trợ:

```text
f64
```

compiler phải báo target legality hoặc lower theo contract.

Không silently thay:

```text
f64 → f32
```

---

# 36. Numeric ABI

ABI classification phụ thuộc target.

Ví dụ:

```text
i32
i64
f32
f64
SIMD
```

có thể được truyền:

- register;
- vector register;
- stack;
- multiple registers.

Numeric semantic type không bị thay đổi bởi ABI lowering.

---

# 37. Performance model

Axiom không cam kết:

> `i32` luôn nhanh hơn `i64`.

Mà cam kết:

> Không thêm abstraction overhead nếu semantics không yêu cầu.

Compiler có thể dùng:

```text
register width
instruction availability
vector width
target cost model
```

để tối ưu.

Ví dụ trên x86-64, một phép toán `i32` có thể dùng native 32-bit instruction dù machine word là 64-bit.

---

# 38. Overflow và optimizer

Vì default integer arithmetic là defined modular arithmetic, optimizer **không được** giả định:

```text
x + 1 > x
```

đúng với unsigned.

Ví dụ:

```axiom
let y = x + 1

if y > x {
    ...
}
```

với `u32`, compiler phải tôn trọng wraparound.

Nếu programmer muốn compiler được phép giả định không overflow, dùng:

```text
checked/preconditioned arithmetic abstraction
```

hoặc optimizer có proof từ range analysis.

Không được dùng UB làm optimization trick.

---

# 39. Integer range analysis

Ngược lại, compiler có thể tự chứng minh:

```text
0 <= x < 100
```

và từ đó tối ưu:

```text
x + 1
```

hoặc:

```text
array[x]
```

mà không cần runtime check.

Đây nối trực tiếp với `BOOTSTRAP-055/056/067`.

---

# 40. Numeric semantic layers

Kiến trúc cuối cùng:

```text
                    Numeric Type
                         │
        ┌────────────────┼────────────────┐
        │                │                │
     Integer          Floating          SIMD
        │                │                │
  fixed width       IEEE/profile      SIMD<T,N>
        │                │                │
        └────────────────┼────────────────┘
                         │
                  Typed MIR operation
                         │
                  Range / Alias facts
                         │
                    Optimization
                         │
                  Target lowering
                         │
        ┌────────────────┼────────────────┐
        │                │                │
       x86              ARM             RISC-V
        │                │                │
      SIMD             NEON/SVE         Vector
```

---

# Frozen Invariants — `ANUM-20..100`

### Numeric types

- **ANUM-20** Fixed-width integer types have defined widths.
- **ANUM-21** `isize` and `usize` are target-word-sized integer types.
- **ANUM-22** Integer type identity includes signedness and width.
- **ANUM-23** Floating type identity includes precision.
- **ANUM-24** Core v1 includes `i8..i64`, `u8..u64`, `isize`, `usize`, `f32`, `f64`.
- **ANUM-25** Additional numeric types may be added without changing existing type semantics.

### Integer semantics

- **ANUM-26** Integer arithmetic has defined semantics.
- **ANUM-27** Integer arithmetic does not rely on C-style signed-overflow UB.
- **ANUM-28** Fixed-width integer arithmetic uses two's-complement modular semantics.
- **ANUM-29** Unsigned arithmetic is modulo `2^N`.
- **ANUM-30** Signed overflow does not invalidate program semantics.
- **ANUM-31** Checked arithmetic is explicit.
- **ANUM-32** Wrapping arithmetic is explicit.
- **ANUM-33** Saturating arithmetic is explicit.
- **ANUM-34** Overflow mode is not silently changed by optimization.
- **ANUM-35** Integer conversion semantics are explicit.
- **ANUM-36** Implicit narrowing conversions are forbidden.
- **ANUM-37** Signed/unsigned mixing does not perform arbitrary implicit conversion.
- **ANUM-38** `as` represents numeric conversion, not bit reinterpretation.
- **ANUM-39** `bitcast` is distinct from numeric conversion.
- **ANUM-40** Bitcast requires valid size/alignment/representation conditions.

### Division and shifts

- **ANUM-41** Signed division truncates toward zero.
- **ANUM-42** Division by zero is a defined runtime failure.
- **ANUM-43** Compile-time division by zero is a compiler diagnostic.
- **ANUM-44** Signed division overflow is defined failure behavior.
- **ANUM-45** Shift operations have defined valid ranges.
- **ANUM-46** Invalid shift amounts cannot create undefined behavior.
- **ANUM-47** Explicit wrapping shift operations may be provided.
- **ANUM-48** Bit operations preserve fixed-width semantics.

### Boolean

- **ANUM-49** `bool` is distinct from integer types.
- **ANUM-50** Integer values do not implicitly convert to `bool`.
- **ANUM-51** Boolean values do not implicitly convert to integers.

### Floating point

- **ANUM-52** `f32` and `f64` follow defined floating-point profiles.
- **ANUM-53** NaN semantics are preserved according to the active profile.
- **ANUM-54** Signed zero is observable where floating semantics require it.
- **ANUM-55** Infinity semantics are preserved.
- **ANUM-56** Compiler cannot assume ordinary algebraic identities that violate the active floating profile.
- **ANUM-57** Fast-math is not the default semantic mode.
- **ANUM-58** Fast-math requires an explicit semantic contract/profile.
- **ANUM-59** FMA transformation is permitted only when semantics allow it.
- **ANUM-60** Floating optimization cannot silently change required observable results.
- **ANUM-61** Floating determinism is defined relative to language and target profiles.
- **ANUM-62** Exact cross-target bit identity is not implicitly guaranteed.

### Numeric operators

- **ANUM-63** Numeric operators participate in the trait system.
- **ANUM-64** Primitive numeric operators may be compiler-lowered directly.
- **ANUM-65** Generic numeric operations may be monomorphized.
- **ANUM-66** Operator abstraction does not imply runtime dispatch.
- **ANUM-67** Numeric traits do not form a subtype hierarchy.

### SIMD

- **ANUM-68** SIMD is distinct from scalar numeric types.
- **ANUM-69** Portable SIMD is a library/compiler abstraction.
- **ANUM-70** SIMD semantic width is independent of physical register width.
- **ANUM-71** SIMD may be lowered to one or multiple physical registers.
- **ANUM-72** SIMD may scalarize when required.
- **ANUM-73** SIMD masks have explicit semantics.
- **ANUM-74** Portable SIMD is distinct from target-specific intrinsics.
- **ANUM-75** Target intrinsics are target-specific operations.
- **ANUM-76** SIMD operations preserve numeric semantics.
- **ANUM-77** SIMD lowering may use target-specific instructions.
- **ANUM-78** SIMD does not imply heap allocation.
- **ANUM-79** SIMD does not imply dynamic dispatch.
- **ANUM-80** SIMD values follow normal ownership/value semantics.

### Optimization

- **ANUM-81** Range analysis may eliminate redundant numeric checks.
- **ANUM-82** Range analysis may eliminate bounds checks.
- **ANUM-83** Alias analysis may enable numeric vectorization.
- **ANUM-84** Proven disjoint views may enable SIMD optimization.
- **ANUM-85** Unknown aliasing cannot be assumed disjoint.
- **ANUM-86** Optimizer cannot use undefined overflow assumptions absent from Axiom semantics.
- **ANUM-87** Optimization preserves integer overflow behavior.
- **ANUM-88** Optimization preserves floating-point profile semantics.
- **ANUM-89** Vectorization preserves observable numeric semantics.
- **ANUM-90** Scalar and SIMD implementations are semantically equivalent under the active profile.

### GPU / ABI

- **ANUM-91** GPU kernels use the same numeric type system.
- **ANUM-92** GPU target legality may restrict supported numeric operations.
- **ANUM-93** GPU lowering cannot silently change numeric type semantics.
- **ANUM-94** Numeric ABI classification is target-specific.
- **ANUM-95** ABI lowering cannot change numeric type identity.
- **ANUM-96** Numeric types have no mandatory runtime representation object.
- **ANUM-97** SIMD ABI representation is target-specific.
- **ANUM-98** Numeric semantics remain independent from physical register allocation.
- **ANUM-99** Numeric optimization cannot manufacture semantic overflow assumptions.
- **ANUM-100** All numeric transformations preserve the active Axiom numeric profile.

---

## Một quyết định đặc biệt quan trọng

Có một điểm tôi muốn nhấn mạnh: **không nên copy mô hình C/C++ về undefined behavior để lấy thêm optimization freedom**.

Axiom có thể đạt optimization rất mạnh bằng nguồn thông tin khác:

```text
Ownership
   +
Capability
   +
Range Analysis
   +
Alias Analysis
   +
Escape Analysis
   +
Constant Propagation
   +
Profile/Target Information
```

thay vì:

```text
"compiler được phép giả định programmer không bao giờ overflow"
```

Ví dụ C có thể tối ưu dựa trên signed-overflow UB, nhưng Axiom có thể dùng **range proof** để đạt cùng loại tối ưu trong những trường hợp compiler thực sự chứng minh được.

Đó phù hợp hơn với triết lý đã freeze:

> **Không dùng undefined behavior để thay thế cho compiler analysis.**

---

### Chuỗi kiến trúc tiếp theo

Sau numeric model, bước hợp lý tiếp theo là:

**`BOOTSTRAP-069 — Axiom Memory Intrinsics, Atomics, Volatile, Bit Operations & Low-Level Machine Access`**

Phần đó sẽ chốt ranh giới giữa **safe high-level Axiom** và **machine-level systems programming**, đặc biệt là `atomic`, `volatile`, memory barriers, endian, unaligned access, raw memory copy, DMA/MMIO và inline assembly.