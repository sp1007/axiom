Tiếp tục. Đây là phần tôi cho rằng phải **khóa rất chặt** trước khi đi sâu hơn vào syntax/compiler implementation:

# Axiom Execution Semantics & Optimization Contract v0.1

Mục tiêu:

> **Một chương trình Axiom phải có semantics xác định đủ rõ để compiler có thể tối ưu cực mạnh mà không được “đoán” sai hành vi quan sát được.**

Đồng thời Axiom không nên rơi vào cái bẫy của C/C++:

```text
"compiler được phép làm bất cứ gì vì chương trình đã UB"
```

nhưng cũng không nên biến mọi lỗi thành runtime checking khiến hiệu năng giảm.

---

# 1. Ba trạng thái phải phân biệt

Axiom nên phân biệt:

```text
DEFINED
PANIC/TRAP
INVALID PROGRAM
```

Ví dụ:

```text
x + y
```

có semantics rõ ràng.

```text
array[i]
```

với `i >= len`:

```text
PANIC / TRAP
```

Còn:

```text
unsafe dereference dangling pointer
```

là:

```text
INVALID UNSAFE PROGRAM
```

Compiler không cần bảo toàn một kết quả cụ thể cho trường hợp programmer đã phá invariant unsafe.

---

# 2. Không dùng UB cho safe code

Đây nên là invariant rất mạnh:

> **Safe Axiom code không được có undefined behavior do các lỗi mà compiler có thể xác định theo language semantics.**

Ví dụ:

| Tình huống | Axiom |
|---|---|
| signed overflow | defined checked/wrapping/saturating semantics |
| division by zero | trap |
| out-of-bounds | panic/trap |
| use-after-move | compile error |
| use-after-drop | compile error |
| dangling view | compile error |
| data race | compile error |
| invalid match | compile error |
| `unreachable()` reached | trap |
| invalid raw pointer dereference | unsafe responsibility |

Điều này rất khác C.

---

# 3. Nhưng không phải mọi lỗi đều runtime-check

Ví dụ:

```axiom
let x = a[i];
```

Compiler có thể:

```text
if can prove i < len
    → remove bounds check
```

Nếu không chứng minh:

```text
→ generate bounds check
```

Do đó:

```text
Safety guarantee ≠ mandatory runtime overhead
```

Đây là nguyên tắc rất quan trọng.

---

# 4. Evaluation order

Tôi đề xuất:

> **Axiom có evaluation order xác định.**

Không để compiler tùy ý đánh giá:

```axiom
f() + g()
```

theo bất kỳ thứ tự nào.

Ví dụ quyết định:

```text
left-to-right
```

thì:

```text
f()
↓
g()
↓
+
```

là semantics.

---

# 5. Vì sao không để unspecified order?

Nếu cho:

```text
f() + g()
```

có thể chạy:

```text
f → g
```

hoặc:

```text
g → f
```

thì:

```text
IO
global state
atomic
panic
allocation
```

trở nên khó reasoning.

Axiom muốn deterministic compiler nên tốt hơn là khóa order.

---

# 6. Nhưng evaluation order không có nghĩa compiler phải giữ instruction order

Ví dụ:

```axiom
let x = pure_a();
let y = pure_b();
return x + y;
```

Compiler có thể:

```text
compute in parallel
reorder
inline
vectorize
```

nếu observable behavior không thay đổi.

Semantic order là thứ người lập trình nhìn thấy; machine schedule là implementation.

---

# 7. Observable behavior

Compiler phải bảo toàn observable behavior.

Tôi đề xuất định nghĩa gồm:

```text
program return value
stdout/stderr/explicit IO
filesystem/network operations
volatile operations
atomic synchronization effects
FFI effects
panic/trap behavior
externally observable memory
program termination
```

Internal:

```text
register allocation
stack layout
temporary values
allocation count
function inlining
```

không phải observable mặc định.

---

# 8. Allocation không mặc định observable

Ví dụ:

```axiom
let x = Box::new(42);
return *x;
```

Nếu address không escape:

```text
Box allocation
```

có thể biến thành:

```text
return 42
```

hoàn toàn hợp lệ.

Đây là:

```text
allocation elimination
```

---

# 9. Nhưng address escape thì khác

```axiom
let x = Box::new(42);
let p = address_of(x);
external(p);
```

Bây giờ address trở thành observable.

Compiler không thể tùy tiện:

```text
heap → register
```

nếu phá semantics của `p`.

Đây chính là:

> **Address observability creates a storage contract.**

---

# 10. Side effects

Axiom effect system đã có:

```text
PURE
READ
WRITE
ALLOC
DROP
IO
ATOMIC
SYNC
SPAWN
SUSPEND
PANIC
UNSAFE
FFI
UNKNOWN
```

Compiler dùng effect information để biết phép reorder nào hợp lệ.

Ví dụ:

```text
PURE + PURE
```

có thể reorder.

Nhưng:

```text
IO + IO
```

phải giữ observable order.

---

# 11. Pure function

```axiom
fn square(x: i64) -> i64 {
    x * x
}
```

Nếu compiler xác định:

```text
PURE
```

thì có thể:

```text
constant fold
CSE
inline
DCE
vectorize
compile-time execute
```

---

# 12. `PURE` không nên là programmer annotation bắt buộc

Compiler tự infer:

```text
Effects(f)
```

từ MIR.

Điều này phù hợp nguyên tắc:

> **Compiler Complexity Is Not Language Complexity.**

Không bắt programmer viết:

```text
@pure
@readonly
@noalloc
```

cho mọi function.

---

# 13. FFI là boundary

Ví dụ:

```axiom
extern "C" fn foo(...)
```

Nếu không có contract:

```text
Effects(foo) = UNKNOWN
```

Compiler phải conservative.

Nếu sau này có contract:

```text
@pure
@reads(...)
@writes(...)
```

optimizer có thêm freedom.

---

# 14. Integer semantics

Đây là phần cần quyết định kỹ.

Axiom không nên có:

```text
signed integer overflow = UB
```

như C/C++.

Nhưng cũng không nên khiến **mọi phép cộng** thành runtime checked operation.

---

# 15. Tôi đề xuất ba semantic families

### Checked

```text
add_checked(a, b)
```

trả:

```text
Option<T>
```

hoặc `Result`.

### Wrapping

```text
add_wrap(a, b)
```

modulo `2^N`.

### Saturating

```text
add_sat(a, b)
```

clamp về min/max.

---

# 16. Còn operator `+`?

Đây là điểm cần chọn.

Tôi đề xuất:

> **Default integer arithmetic là checked/fatal-on-overflow theo execution profile, nhưng compiler được phép loại bỏ check khi chứng minh overflow không thể xảy ra.**

Ví dụ:

```axiom
let x = a + b;
```

conceptually:

```text
ADD_CHECKED
```

Nếu overflow:

```text
PANIC/TRAP
```

Nhưng:

```axiom
for i in 0..100 {
    sum += i;
}
```

compiler chứng minh range:

```text
sum <= 4950
```

và biến thành:

```text
ADD
```

không check.

---

# 17. Tại sao chọn checked default?

Vì:

```text
silent integer corruption
```

rất nguy hiểm.

Đặc biệt trong:

- image processing;
- financial logic;
- geometry;
- allocation size;
- array indexing;
- security code.

Axiom không nên bắt programmer nhớ:

```text
"integer này có thể overflow không?"
```

mỗi lần viết `+`.

---

# 18. Nhưng có thể có compile profile

Ví dụ:

```text
--overflow=panic
--overflow=wrap
```

Tôi **không khuyến khích global semantic switch** làm cùng source code có semantics khác nhau quá lớn.

Tốt hơn:

```text
+       checked
+%      wrapping
+|      saturating
```

hoặc intrinsic/library API.

Syntax cụ thể chưa cần khóa ngay.

---

# 19. Tôi nghiêng về explicit operators

Ví dụ:

```axiom
a + b      // checked
a +% b     // wrapping
a +| b     // saturating
```

Tương tự:

```text
-%
*%
```

và:

```text
+|
-|
*|
```

Lợi ích:

```text
hot low-level code
```

có thể yêu cầu wrapping mà không cần function call.

Compiler map trực tiếp thành machine instruction.

---

# 20. Division

```axiom
x / y
```

nếu:

```text
y == 0
```

→ `TRAP`.

Không phải UB.

Compiler có thể prove:

```text
y != 0
```

→ bỏ check.

---

# 21. Signed division overflow

Ví dụ minimum signed integer chia `-1`.

Trên một số CPU, trường hợp này gây machine exception.

Axiom nên định nghĩa:

```text
TRAP
```

không UB.

Backend map trực tiếp nếu target có trap semantics tương thích.

---

# 22. Shift

Shift amount ngoài range cũng phải defined.

Ví dụ `u32`:

```text
x << 32
```

Tôi đề xuất:

```text
shift operator = checked shift amount
```

→ trap nếu amount >= 32.

Wrapping shift có API/operator riêng.

Lý do: tránh phụ thuộc CPU:

```text
x86 masks shift count
ARM có semantics khác
```

Axiom source không nên thay đổi theo CPU.

---

# 23. Bit operations

Bitwise:

```text
&
|
^
~
```

luôn defined trên integer.

Không có vấn đề overflow.

---

# 24. Floating point

Đây là một vùng phải khác integer.

IEEE-754 semantics nên là baseline cho:

```text
f32
f64
```

Bao gồm:

```text
NaN
+∞
-∞
signed zero
rounding
```

Compiler không được mặc định coi:

```text
x == x
```

luôn true với float.

---

# 25. Fast math

Nếu sau này có:

```text
--fast-math
```

thì đây phải là **explicit non-default optimization profile**.

Không được mặc định phá:

```text
NaN
infinity
signed zero
```

để đổi lấy vài % performance.

---

# 26. Floating-point equality

```axiom
NaN != NaN
```

theo IEEE semantics.

Nếu cần total ordering:

```text
total_cmp()
```

là library/intrinsic.

---

# 27. Memory bounds

Safe:

```axiom
a[i]
```

compiler đảm bảo:

```text
0 <= i < len
```

Nếu không prove:

```text
runtime check
```

failure:

```text
panic/trap
```

---

# 28. Out-of-bounds không phải UB

Đây là invariant:

> **Safe out-of-bounds access has a defined failure mode.**

Compiler có thể:

```text
bounds check
```

hoặc:

```text
prove impossible → remove check
```

---

# 29. Bounds check elimination

Ví dụ:

```axiom
fn sum(a: view<i64>) -> i64 {
    var s = 0;
    for i in 0..a.len() {
        s += a[i];
    }
    s
}
```

Compiler biết:

```text
0 <= i < len
```

nên:

```text
a[i]
```

không cần bounds check.

Đây là nơi Axiom có thể đạt performance rất gần raw C loop mà vẫn giữ safe semantics.

---

# 30. `unsafe` unchecked access

Nếu programmer thực sự biết:

```text
i < len
```

có thể dùng:

```text
unsafe {
    a.get_unchecked(i)
}
```

Nhưng compiler không được tự động assume mọi unsafe access là valid cho các phần khác.

---

# 31. `unreachable()`

```axiom
unreachable()
```

type:

```text
never
```

Semantics:

```text
TRAP
```

nếu execution thực sự tới đó.

Compiler có thể dùng nó để:

```text
remove branch
prove unreachable
optimize switch
```

---

# 32. `never`

Ví dụ:

```axiom
fn fail() -> never {
    panic("fatal")
}
```

Có thể dùng ở mọi nơi cần type:

```text
T
```

vì:

```text
never <: control-flow inhabitance
```

nhưng không nên biến thành general subtype system.

Nó chỉ là bottom-like control-flow type.

---

# 33. `panic`

Panic:

```text
language-level abnormal termination
```

không phải:

```text
Result
```

và không phải:

```text
exception object
```

---

# 34. Panic profile

Có hai profile chính:

```text
panic=abort
panic=unwind
```

### Abort

```text
cleanup
 ↓
terminate
```

runtime cực nhỏ.

### Unwind

```text
panic
 ↓
cleanup stack/state
 ↓
unwind
```

cần metadata/runtime support.

---

# 35. Không có catch trong Core v0.1

Tôi vẫn giữ quyết định:

```text
try/catch exception
```

không có.

Nếu muốn recoverable:

```text
Result<T,E>
```

Nếu muốn abnormal termination:

```text
panic
```

---

# 36. Cleanup trước panic

Ví dụ:

```axiom
fn foo() {
    let file = open();
    panic("bad");
}
```

Nếu `file` đã owned:

```text
panic
 ↓
cleanup file
 ↓
abort/unwind
```

Drop semantics vẫn được đảm bảo.

---

# 37. Panic trong Drop

Đây là vùng nguy hiểm.

Tôi đề xuất:

> **`Drop` không được dùng để tạo recoverable failure.**

Nếu Drop panic:

```text
panic during cleanup
```

có thể terminate immediately hoặc policy-specific.

Tốt nhất standard library thiết kế Drop để không panic.

---

# 38. `close() -> Result`

Ví dụ file:

```axiom
let file = File.open(...)?;
...
file.close()?;
```

Nếu programmer không gọi `close()`:

```text
Drop
```

chỉ làm best-effort resource release.

Điều này đã phù hợp với resource model trước đó.

---

# 39. Trap

`trap` là machine/environment boundary.

Ví dụ:

```text
division by zero
invalid instruction
explicit trap
hardware fault
```

Không tự động chuyển thành:

```text
Result
```

---

# 40. `Result` vẫn là ordinary data

```axiom
enum Result<T,E> {
    Ok(T)
    Err(E)
}
```

Compiler có thể:

```text
niche-optimize
register-return
eliminate branches
```

nếu có thể.

Không có exception allocation.

---

# 41. `?`

```axiom
let x = foo()?;
```

lower thành:

```text
call foo
 ↓
switch
 ├── Ok → continue
 └── Err → cleanup → return Err
```

Không có stack unwinding.

---

# 42. Optimization contract

Đây là phần quan trọng nhất.

Compiler được phép:

```text
inline
devirtualize
specialize
constant-fold
CSE
DCE
LICM
vectorize
unroll
fuse
split
reorder
scalarize
eliminate allocation
eliminate bounds checks
eliminate drops
```

**nếu observable semantics giữ nguyên.**

---

# 43. Drop elimination

Ví dụ:

```axiom
let x = Trivial{};
```

Nếu:

```text
Drop(x)
```

không có observable effect:

```text
DROP
```

có thể bị eliminate.

Nhưng nếu Drop:

```text
IO
SYNC
FFI
```

thì không được.

Effect system xác định điều này.

---

# 44. Dead store

```axiom
var x = 1;
x = 2;
return x;
```

Store `1` có thể bị loại bỏ.

Nếu:

```text
volatile_write
```

thì không.

---

# 45. Common subexpression

```axiom
let a = f(x);
let b = f(x);
```

Nếu `f` pure:

```text
call f once
```

Nếu `f` có IO:

```text
must preserve two calls
```

---

# 46. Reordering

Ví dụ:

```axiom
let a = pure1();
io();
let b = pure2();
```

Compiler có thể thực hiện `pure1/pure2` ở vị trí khác nếu không ảnh hưởng observable result.

Nhưng:

```text
IO1
IO2
```

phải giữ order.

---

# 47. Atomic reordering

Atomic có memory ordering riêng.

Ví dụ:

```text
Release
Acquire
```

backend không được tự ý biến:

```text
Acquire
```

thành:

```text
Relaxed
```

chỉ vì nhanh hơn.

---

# 48. Volatile ordering

Volatile operations phải giữ semantics của volatile accesses.

Compiler không được:

```text
remove
merge
invent
```

volatile accesses tùy tiện.

---

# 49. Unsafe code và optimization

Đây là chỗ cần cực kỳ rõ.

Nếu programmer viết unsafe và phá invariant:

```text
dangling pointer
alias violation
invalid alignment
```

compiler **không cần bảo toàn hành vi đó**.

Nhưng compiler không được lấy một unsafe operation hợp lệ và tùy tiện coi nó invalid.

---

# 50. Unsafe contract

Có thể coi mỗi unsafe operation có precondition:

```text
read<T>(p)
requires:
    valid(p)
    aligned(p)
    initialized(p)
    readable(p)
```

Nếu programmer thỏa precondition:

```text
operation has defined semantics
```

Nếu không:

```text
invalid unsafe program
```

---

# 51. Đây là mô hình tốt hơn UB mơ hồ

Thay vì:

```text
"anything can happen"
```

ta có:

```text
unsafe operation
     ↓
explicit preconditions
     ↓
programmer responsibility
     ↓
compiler may optimize assuming preconditions
```

Ví dụ:

```text
*mut T
```

dereference hợp lệ nếu programmer đảm bảo allocation/alignment/lifetime.

Compiler có quyền tận dụng assumption đó.

---

# 52. Vì vậy Axiom vẫn có optimizer mạnh

Nếu:

```axiom
unsafe {
    assume(i < len);
    ...
}
```

thì compiler có thể bỏ bounds check.

Nhưng tôi không muốn một intrinsic `assume()` tùy tiện ở safe code.

Nó nên là explicit unsafe/system primitive.

---

# 53. `assume`

Có thể có:

```text
unsafe assume(condition)
```

Semantic:

```text
nếu condition false
→ program invalid
```

Compiler được phép sử dụng assumption.

Đây là công cụ rất mạnh cho:

- allocator;
- SIMD;
- compiler-generated code;
- hand-optimized kernels.

Nhưng nên rất hiếm trong application code.

---

# 54. Memory model và compiler alias assumptions

Safe:

```text
mut_view<A>
mut_view<B>
```

nếu verifier chứng minh disjoint.

Optimizer có thể assume:

```text
A ∩ B = ∅
```

Unsafe raw pointers:

```text
*p
*q
```

không tự động có noalias.

Compiler phải conservative trừ khi contract nói khác.

---

# 55. Điều này tránh một vấn đề của C

C compiler thường phải dựa vào:

```text
restrict
strict aliasing
effective type
```

Axiom có thể lấy alias facts từ:

```text
ownership
view
mut_view
region
```

ngay từ semantic layer.

---

# 56. Memory model tổng quát

Tôi đề xuất:

```text
SAFE:
    compiler knows ownership + regions

UNSAFE:
    programmer provides machine-level invariants

OPTIMIZER:
    may exploit proven/declared invariants
```

Không cần một aliasing type system phức tạp ở source.

---

# 57. Compiler correctness contract

Một compiler Axiom hợp lệ phải thỏa:

```text
For every valid program P:

Semantics(P)
    ==
Semantics(Compile(P))
```

với mọi observable behavior được language định nghĩa.

Có thể khác:

```text
performance
layout
instruction sequence
allocation strategy
```

---

# 58. Semantic Oracle trở thành cực kỳ quan trọng

Pipeline:

```text
Source
  ↓
Typed MIR
  ↓
Verified MIR
  ├──────────────┐
  ↓              ↓
Oracle        Optimizer
  │              ↓
  │            LIR
  │              ↓
  │           Machine
  │              ↓
  └──── compare ─┘
```

Test:

```text
OracleResult == NativeResult
```

trên hàng triệu generated programs.

---

# 59. Optimization correctness testing

Không chỉ test source.

Có thể:

```text
P
 ↓
MIR
 ↓
O0 → result A
O1 → result B
O2 → result C
```

yêu cầu:

```text
A == B == C
```

trừ những differences được định nghĩa như timing/IO scheduling.

Đây sẽ là nền tảng cực mạnh cho compiler AI-generated.

---

# 60. Differential backend testing

Ví dụ:

```text
Verified MIR
 ├── Oracle Interpreter
 ├── x86-64 backend
 ├── ARM64 backend
 └── WASM backend
```

Tất cả phải cùng semantic result.

Backend không được trở thành source of truth.

---

# 61. Undefined behavior policy

Tôi đề xuất Axiom chỉ có **hai nguồn invalidity chính**:

### Compile-time invalidity

```text
ownership violation
type error
trait ambiguity
invalid layout
invalid safe access
```

→ compiler reject.

### Unsafe invariant violation

```text
invalid raw pointer
invalid alignment
invalid provenance
invalid FFI contract
```

→ programmer responsibility.

Safe language không dựa vào UB để optimize.

---

# 62. Một điểm tôi muốn thay đổi nhẹ so với thiết kế trước

Trước đây ta nói:

```text
signed overflow = checked/wrapping/saturating
```

Tôi nghĩ nên **chính thức hóa thành operator families**, thay vì compiler profile.

Ví dụ:

```text
a + b       checked
a +% b      wrapping
a +| b      saturating
```

Tương tự:

```text
a - b
a -% b
a -| b

a * b
a *% b
a *| b
```

Compiler có thể lower:

```text
+%
```

thẳng thành CPU `ADD`.

Không có runtime cost.

---

# 63. Bounds cũng có ba mức tương tự

Normal:

```text
a[i]
```

checked.

Unsafe:

```text
a.get_unchecked(i)
```

unchecked.

Có thể compiler intrinsic:

```text
assume(i < len)
```

cho specialized kernels.

Như vậy programmer có cả:

```text
safe correctness
```

và:

```text
maximum low-level control
```

---

# 64. Toàn bộ execution contract

```text
                   SOURCE
                      │
                      ▼
              DEFINED SEMANTICS
                      │
         ┌────────────┼────────────┐
         │            │            │
      normal        panic         trap
         │            │            │
         └────────────┼────────────┘
                      │
                 OBSERVABLE
                  BEHAVIOR
                      │
                      ▼
                 OPTIMIZER
                      │
       ┌──────────────┼──────────────┐
       │              │              │
   eliminate       reorder        specialize
   allocation      operations     representation
       │              │              │
       └──────────────┼──────────────┘
                      ▼
                MACHINE CODE
```

Optimizer có thể thay đổi **implementation**, không thay đổi semantic contract.

---

# 65. Execution invariants mới

### ASEM-01 — Deterministic Evaluation
Evaluation order được xác định.

### ASEM-02 — No Safe UB
Safe code không dựa trên undefined behavior.

### ASEM-03 — Defined Failure
Các lỗi runtime của safe semantics có failure mode xác định.

### ASEM-04 — Observable Behavior Preservation
Optimization phải bảo toàn observable behavior.

### ASEM-05 — Allocation Is Not Observable by Default
Allocation strategy không phải semantic observation trừ khi address/storage contract được expose.

### ASEM-06 — Pure Reordering
Pure operations có thể reorder.

### ASEM-07 — Effect Preservation
Side effects phải giữ semantic ordering.

### ASEM-08 — Atomic Ordering Preservation
Memory ordering không được compiler tự ý weaken.

### ASEM-09 — Volatile Preservation
Volatile access không được optimize như ordinary memory.

### ASEM-10 — Unsafe Preconditions
Unsafe operations có explicit machine-level preconditions.

### ASEM-11 — No Universal Transmute
Representation conversion phải explicit.

### ASEM-12 — Optimization Freedom
Compiler được tự do thay đổi representation khi semantics không thay đổi.

### ASEM-13 — Checked-by-default Safety
Safe bounds/arithmetic operations có defined failure.

### ASEM-14 — Check Elimination
Compiler có thể loại bỏ safety checks khi proof đủ mạnh.

### ASEM-15 — Explicit Fast Paths
Wrapping/unchecked/system operations cho phép low-level code yêu cầu semantics phù hợp.

---

# 66. Điều này đưa Axiom tới một điểm khá quan trọng

Ta có thể mô tả triết lý hiệu năng của Axiom bằng:

```text
Safety cost ≠ runtime cost
```

Ví dụ:

```text
Axiom source
    ↓
bounds safety
    ↓
range analysis
    ↓
proof: i < len
    ↓
bounds check eliminated
    ↓
raw load
```

Hoặc:

```text
Axiom
    ↓
ownership analysis
    ↓
prove unique mutable access
    ↓
noalias fact
    ↓
vectorization
```

Hoặc:

```text
Box<T>
    ↓
escape analysis
    ↓
doesn't escape
    ↓
stack/register promotion
    ↓
no heap allocation
```

Đây chính xác là hướng tôi nghĩ phù hợp với mục tiêu của bạn:

> **Không cố làm compiler đơn giản bằng cách bắt programmer làm công việc của compiler.**

Compiler có thể rất phức tạp; **ngôn ngữ vẫn giữ trải nghiệm đơn giản**.

---

## Bước tiếp theo

Tới đây các mảnh lớn đã bắt đầu ghép thành một hệ thống:

```text
STRUCT / ENUM
      ↓
VALUE / OWNERSHIP
      ↓
VIEW / REGION
      ↓
POINTER / UNSAFE
      ↓
LAYOUT / ABI
      ↓
FUNCTION / CLOSURE
      ↓
THREAD / ASYNC
      ↓
EFFECT / EXECUTION
      ↓
OPTIMIZATION
```

Phần tiếp theo tôi đề xuất là **Type System hoàn chỉnh**, nhưng không phải chỉ nói lại `struct/trait/generic`.

Ta cần khóa những thứ hiện còn ảnh hưởng trực tiếp đến compiler:

```text
type inference
numeric literals
generic inference
associated types
trait constraints
coherence
operator overload
implicit conversions
newtype
tuple
unit / never
function types
closure types
dyn Trait
type aliases
const generics
variance có cần không?
subtyping có cần không?
existential types
opaque types
recursive types
```

Đặc biệt tôi muốn xử lý **numeric literals + conversion + generic inference** thật kỹ, vì đây là nơi một ngôn ngữ “đơn giản” rất dễ vô tình trở thành một hệ thống type inference phức tạp kiểu C++/Rust/Swift.