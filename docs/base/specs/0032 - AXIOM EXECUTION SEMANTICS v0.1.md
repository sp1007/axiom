Tiếp tục. Ta đi vào **AXIOM EXECUTION SEMANTICS v0.1** và lần này nên cố gắng đóng các điểm có thể gây “semantic drift” cho compiler agent.

# AXIOM EXECUTION SEMANTICS v0.1

Mục tiêu của phần này là mọi expression/instruction đều có câu trả lời chính xác cho:

```text
Giá trị là gì?
Được đánh giá theo thứ tự nào?
Có tạo/mất ownership không?
Có side effect không?
Có thể panic/trap không?
Có observable behavior nào không?
```

---

# 1. Evaluation model

Axiom sử dụng:

> **Deterministic left-to-right evaluation**

Ví dụ:

```axiom
foo(a(), b(), c())
```

thứ tự:

```text
a()
↓
b()
↓
c()
↓
foo(...)
```

Không được phép để optimizer biến thành:

```text
b()
c()
a()
```

nếu điều đó thay đổi observable semantics.

Tuy nhiên optimizer vẫn có thể reorder các operation **nếu chứng minh observable behavior không thay đổi**.

---

# 2. Đây không có nghĩa mọi instruction native đều chạy left-to-right

Ví dụ:

```axiom
let x = a + b
```

sau optimization có thể CPU thực hiện instruction theo cách khác.

Axiom chỉ quy định:

```text
semantic evaluation order
```

không quy định:

```text
machine instruction execution order
```

miễn là observable semantics được bảo toàn.

---

# 3. Function arguments

```axiom
foo(
    make_a(),
    make_b(),
    make_c()
)
```

semantic:

```text
make_a
→ make_b
→ make_c
→ call foo
```

Nếu `make_a()` move ownership:

```text
foo(move(a), mutate(b))
```

thì ownership state sau mỗi expression phải được cập nhật trước expression tiếp theo.

---

# 4. Short-circuit

`&&`:

```axiom
a && b
```

semantic:

```text
evaluate a

if a == false:
    result = false
else:
    evaluate b
```

`||`:

```axiom
a || b
```

semantic:

```text
evaluate a

if a == true:
    result = true
else:
    evaluate b
```

Do đó:

```axiom
false && dangerous()
```

không gọi `dangerous()`.

---

# 5. `if` expression

Axiom nên coi `if` là expression:

```axiom
let x =
    if cond {
        10
    } else {
        20
    }
```

Hai branch phải có type tương thích:

```text
T
T
↓
T
```

Nếu:

```text
i32
String
```

=> type error.

---

# 6. Branch ownership

Ví dụ:

```axiom
let x = Resource()

let y =
    if cond {
        move x
    } else {
        Resource()
    }
```

Sau expression:

```text
x = MOVED
```

trên **mọi path**.

Compiler phải merge ownership state.

---

# 7. Assignment

Đây là một điểm cần freeze.

Axiom:

```axiom
x = value
```

không đơn giản là:

```text
STORE
```

Nếu `x` hiện đang sở hữu một resource:

```text
x = ResourceA
x = ResourceB
```

thì assignment thứ hai phải resolve ownership của `ResourceA`.

Semantic:

```text
evaluate RHS
↓
obtain new value
↓
resolve old value
↓
store new value
```

---

# 8. Thứ tự assignment

Ta nên freeze:

> **RHS được evaluate trước khi old destination bị destroyed.**

Ví dụ:

```axiom
x = make_value()
```

semantic:

```text
tmp = make_value()
DROP old x
MOVE tmp → x
```

Không:

```text
DROP x
tmp = make_value()
```

Lý do rất quan trọng:

```axiom
x = transform(x)
```

phải có khả năng đọc `x` để tạo RHS trước khi thay thế `x`.

---

# 9. Assignment tự gán

```axiom
x = x
```

Nếu `x` là non-Copy owning value thì không thể hiểu là:

```text
MOVE x → x
```

vì source và destination cùng một ownership location.

Do đó semantic rule:

> Self-assignment của non-Copy value phải được compiler xử lý như một trường hợp đặc biệt hoặc bị reject nếu không thể chứng minh semantics hợp lệ.

Tôi nghiêng về:

```text
x = x
```

với owning non-Copy:

**compile-time error**.

Với Copy:

```text
x = x
```

có thể hợp lệ.

Điều này tránh rất nhiều ambiguity.

---

# 10. Assignment vào field

```axiom
p.name = new_name
```

semantic:

```text
evaluate new_name
↓
resolve old p.name
↓
DROP old p.name
↓
MOVE new_name → p.name
```

Các field khác của `p` không bị ảnh hưởng.

---

# 11. Assignment và active view

Ví dụ:

```axiom
let v = view(p.name)
p.name = new_name
```

`v` là:

```text
READ(p.name)
```

assignment cần:

```text
WRITE(p.name)
```

=> conflict.

Reject.

Nhưng:

```axiom
let v = view(p.name)
p.age = 20
```

nếu field disjoint:

```text
READ(p.name)
WRITE(p.age)
```

=> hợp lệ.

---

# 12. Assignment có thể gây relocation

Ví dụ:

```axiom
vec = new_vec
```

Nếu `vec` là `Vec<T>`, assignment có thể thay đổi storage identity.

Nhưng vì view `v` đang phụ thuộc vào `vec`, việc:

```axiom
vec = new_vec
```

phải được xem như:

```text
WRITE(vec)
MAY_RELOCATE(vec.storage)
```

và conflict với active view.

---

# 13. Numeric types

Core v0.1:

```text
i8
i16
i32
i64

u8
u16
u32
u64

isize
usize

f32
f64
```

Không có implicit narrowing.

Ví dụ:

```axiom
let x: i32 = 100
let y: i8 = x
```

=> reject.

Phải explicit:

```axiom
let y: i8 = x as i8
```

Nhưng `as` cần được phân biệt rõ giữa:

```text
numeric conversion
```

và:

```text
bit reinterpretation
```

Tôi đề xuất **không dùng `as` cho reinterpretation**.

---

# 14. Numeric conversion

Nên có ba semantics riêng:

```text
convert
checked_convert
reinterpret
```

Ví dụ conceptual:

```axiom
x as i8
```

là numeric conversion.

Còn:

```axiom
reinterpret<i32>(x)
```

là bit reinterpretation và chỉ safe khi representation phù hợp.

Raw reinterpretation nên thuộc unsafe/system-level.

---

# 15. Integer overflow

Đây là điểm phải freeze.

Axiom **không dùng C-style signed overflow UB**.

Có ba operation:

```text
checked
wrapping
saturating
```

### Checked

```text
127_i8 + 1
```

=> overflow result.

### Wrapping

```text
127_i8 + 1
```

=> `-128`.

### Saturating

```text
127_i8 + 1
```

=> `127`.

---

# 16. Default integer arithmetic

Tôi đề xuất:

> **Default integer arithmetic là checked trong safe code.**

Ví dụ:

```axiom
let x: i8 = 127
let y = x + 1
```

=> runtime overflow behavior xác định.

Không UB.

Tùy profile, overflow có thể:

```text
panic
```

nhưng không được trở thành machine-level UB.

---

# 17. Wrapping và saturating

Nên có operation rõ ràng:

```axiom
x.wrapping_add(y)
x.saturating_add(y)
x.checked_add(y)
```

hoặc compiler intrinsic tương đương.

Điểm quan trọng là semantic distinction phải tồn tại trong MIR:

```text
INTEGER_ADD_CHECKED
INTEGER_ADD_WRAP
INTEGER_ADD_SAT
```

Không để optimizer phải đoán từ syntax.

---

# 18. Division

Integer division:

```text
a / b
```

Nếu:

```text
b == 0
```

=> panic/trap theo execution profile, nhưng **không UB**.

Trường hợp:

```text
MIN_INT / -1
```

cũng phải deterministic.

Tôi đề xuất:

```text
checked arithmetic → panic
```

để thống nhất.

---

# 19. Remainder

```axiom
a % b
```

`b == 0`:

```text
panic
```

Không UB.

Sign semantics phải được freeze theo integer division rule.

---

# 20. Shift

Đây cũng là nơi C/C++ có rất nhiều ambiguity.

Axiom nên quy định:

```text
x << n
x >> n
```

với:

```text
n >= bit_width
```

là deterministic.

Tôi đề xuất:

```text
safe shift:
    invalid shift count → panic
```

Không cho phép:

```text
CPU-specific masking
```

tự trở thành semantics.

Ví dụ `u8 << 8` không được phụ thuộc CPU.

---

# 21. Bitwise

Các operation:

```text
&
|
^
~
```

làm việc trên integer representation.

Không implicit convert giữa signed/unsigned để thực hiện bitwise.

Ví dụ:

```text
i32 & u32
```

=> type error trừ khi explicit conversion.

Điều này tránh hàng loạt lỗi C/C++ integer promotion.

---

# 22. Comparisons

Integer:

```text
==
!=
<
<=
>
>=
```

phải cùng semantic domain.

Không tự động:

```text
i32 < u32
```

nếu không có conversion rõ ràng.

---

# 23. Float semantics

`f32`, `f64` phải dựa trên IEEE-754 ở mức representation/operations cơ bản.

Nhưng cần phân biệt:

```text
NaN
+0
-0
Infinity
```

Đặc biệt:

```axiom
NaN == NaN
```

không được trả `true` nếu đang dùng IEEE equality semantics.

Do đó:

```text
x == x
```

không nhất thiết là true đối với float.

---

# 24. Float ordering

Không nên giả vờ rằng mọi float đều có total order.

Ví dụ:

```text
NaN < 1.0
```

không phải true.

Nếu cần total ordering:

```text
TotalFloat
```

có thể là library abstraction/trait.

---

# 25. Floating-point optimization

Axiom không nên mặc định cho optimizer phép:

```text
(a + b) + c
```

thành:

```text
a + (b + c)
```

nếu floating-point semantics có thể thay đổi.

Reassociation chỉ được phép dưới:

```text
fast_math
```

hoặc profile/attribute explicit.

Đây là một điểm cực kỳ quan trọng nếu Axiom hướng tới numerical computing.

---

# 26. Boolean

`bool` chỉ có:

```text
true
false
```

Không implicit:

```text
0 → false
1 → true
```

và:

```text
pointer → bool
```

cũng không implicit.

Điều này giúp type system sạch hơn C/C++.

---

# 27. Equality của struct

Không tự động có:

```text
==
```

cho mọi struct chỉ vì layout giống nhau.

Nếu muốn:

```axiom
a == b
```

struct phải implement trait tương ứng, ví dụ:

```text
trait Eq
```

Compiler có thể derive:

```text
derive Eq
```

ở library/language extension sau này.

---

# 28. Assignment vs initialization

Phân biệt:

```axiom
let x = value
```

với:

```axiom
x = value
```

Initialization:

```text
UNINIT → OWNED
```

Assignment:

```text
OWNED → DROP old → OWNED new
```

Đây là hai MIR semantics khác nhau.

---

# 29. Partial initialization

Ví dụ compiler lowering:

```axiom
var p: Person
p.name = ...
p.age = ...
```

Nếu Axiom cho phép local aggregate declaration chưa initialized, verifier theo dõi:

```text
p.name = INIT
p.age = UNINIT
p = PARTIAL_INIT
```

Không được:

```axiom
use(p)
```

trước khi toàn bộ required fields initialized.

---

# 30. Definite initialization

Rule:

> Safe code chỉ được đọc một place nếu place đó chắc chắn initialized trên mọi path tới điểm đọc.

Ví dụ:

```axiom
var x: i32

if cond {
    x = 10
}

print(x)
```

=> reject.

Merge:

```text
INIT + UNINIT = MAYBE_INIT
```

`LOAD(x)` yêu cầu:

```text
INIT
```

---

# 31. Nhưng partial field initialization hợp lệ

```axiom
var p: Person

p.name = "A"
p.age = 20

use(p)
```

Nếu cả hai field đã initialized:

```text
p = INIT
```

Compiler có thể canonicalize initialization state.

---

# 32. Array initialization

Fixed array:

```axiom
let a = [1, 2, 3, 4]
```

toàn bộ initialized.

Nếu:

```axiom
var a: Array<i32, 100>
```

thì tùy semantics của declaration.

Không được giả định:

```text
a[0] = 0
```

đồng nghĩa toàn array initialized.

Verifier có thể theo dõi initialization ở cấp aggregate hoặc element khi cần.

---

# 33. Indexing

Safe:

```axiom
a[i]
```

semantic:

```text
check i < length
```

Nếu compiler proof được:

```text
0 <= i < length
```

MIR có thể eliminate:

```text
BOUNDS_CHECK
```

sau Verified MIR.

Nhưng semantics vẫn là bounds-safe.

---

# 34. Negative index

Với:

```text
Array<T,N>
Vec<T>
view<T>
```

index là `usize` hoặc domain tương ứng.

Không có Python-style:

```text
a[-1]
```

trong core.

Nếu muốn negative indexing có thể làm library operation.

---

# 35. Function calls

Call semantic:

```text
evaluate callee
evaluate arguments left-to-right
validate ownership transfer
enter function
execute
return value
```

Static call:

```text
CALL function_id
```

Dynamic:

```text
DYNAMIC_CALL dispatch_value
```

---

# 36. Recursive call

Không có giới hạn semantic đặc biệt.

```axiom
fn factorial(n: u64) -> u64 {
    if n == 0 {
        1
    } else {
        n * factorial(n - 1)
    }
}
```

Runtime stack/stack overflow là execution concern.

Stack overflow không được biến thành undefined behavior.

Nó có thể:

```text
panic
trap
OS failure
```

tùy execution target/profile, nhưng phải có documented target semantics.

---

# 37. Global initialization

Đây là phần cần cẩn thận.

Axiom nên tránh C++-style:

```text
global constructor order across modules
```

vì cực kỳ phức tạp.

Đề xuất:

### Constant global

```axiom
const MAX: i32 = 100
```

compile-time.

### Immutable static

```axiom
static CONFIG: Config = ...
```

nếu compile-time constructible.

### Runtime initialization

Dùng explicit function:

```axiom
init()
```

hoặc library mechanism.

Không có implicit arbitrary global constructor execution trong Core v0.1.

Điều này làm startup deterministic hơn rất nhiều.

---

# 38. Thread-local

Thread-local là storage class:

```text
@thread_local
static x: T
```

Semantics:

```text
mỗi execution context có một instance
```

Drop của TLS cần được xử lý bởi target/runtime layer nếu platform hỗ trợ destruction.

Core chỉ quy định ownership/resource semantics.

---

# 39. Static mutable data

Safe mutable global:

```text
static mut
```

không nên tồn tại như một primitive dễ dùng.

Nếu mutable global được phép, nó phải yêu cầu synchronization hoặc unsafe.

Tôi đề xuất:

```text
safe shared mutable static
    → phải thông qua synchronization abstraction
```

Raw mutable static:

```text
unsafe
```

---

# 40. `const` vs `static`

Nên freeze:

```text
const
```

= compile-time value, không phải storage identity.

```text
static
```

= storage identity có lifetime toàn chương trình.

Do đó:

```text
const X
```

có thể inline/eliminate.

`static` có address identity nếu semantics yêu cầu.

---

# 41. Address identity

Một value bình thường không được mặc định có stable address.

Compiler có thể:

```text
register
stack
inline
scalarize
```

Nếu programmer cần:

```text
stable address
```

thì phải dùng abstraction có semantic requirement, ví dụ:

```text
Box<T>
```

hoặc explicit storage API.

Đây là điểm cực quan trọng để Axiom không bị buộc vào stack/heap model.

---

# 42. Observable boundary

Ta nên chính thức freeze nhóm operation sau là observable:

```text
IO
VOLATILE
ATOMIC
SYNCHRONIZATION
FFI
RESOURCE_RELEASE
PANIC
TRAP
EXPLICIT_ADDRESS
```

Optimizer không được thay đổi thứ tự/tần suất theo cách thay đổi semantics của chúng.

---

# 43. Pure arithmetic không observable theo bản thân nó

Ví dụ:

```axiom
let x = (a + b) * c
```

compiler có thể:

```text
constant fold
strength reduce
vectorize
fuse
```

nếu semantic result giống nhau.

---

# 44. Nhưng timing không phải mặc định observable

Axiom không bảo đảm:

```text
"chương trình chạy chính xác N cycles"
```

Nếu programmer cần timing-sensitive operation:

```text
volatile
hardware counter
atomic
```

phải explicit.

Nếu không, optimizer có toàn quyền tối ưu.

---

# 45. `volatile`

`volatile` không phải:

```text
"đừng optimize toàn bộ surrounding code"
```

Nó chỉ biểu thị memory operation có observable side effect và không được eliminate/reorder vượt qua các semantic constraints thích hợp.

MIR:

```text
VOLATILE_LOAD
VOLATILE_STORE
```

riêng biệt.

---

# 46. Atomic

Atomic operation cũng không phải volatile.

Ví dụ:

```text
ATOMIC_LOAD
ATOMIC_STORE
ATOMIC_RMW
ATOMIC_CAS
```

kèm:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

Atomic semantics sẽ được formalize riêng ở concurrency spec.

---

# 47. `assert`

```axiom
assert(x > 0)
```

là semantic operation.

Không được optimizer xóa trong release build chỉ vì:

```text
"debug"
```

Nếu muốn bỏ:

```axiom
debug_assert(...)
```

Đây là hai semantics khác nhau.

---

# 48. `unreachable`

```axiom
unreachable()
```

là programmer assertion rằng control flow không thể tới đây.

Nếu execution tới:

```text
TRAP
```

hoặc panic profile được quy định rõ.

Optimizer được phép sử dụng unreachable để suy luận control flow.

Nhưng nếu programmer đưa assertion sai, đó là lỗi của program.

---

# 49. `panic` vs `unreachable`

```text
panic
```

= một semantic execution path có thể xảy ra.

```text
unreachable
```

= assertion rằng path không thể xảy ra.

Do đó optimizer được phép dùng `unreachable` mạnh hơn `panic`.

---

# 50. Một điểm rất quan trọng về optimizer

Sau khi freeze execution semantics:

```text
Source
 ↓
Verified MIR
```

là **behavioral contract**.

Optimizer được phép biến:

```text
A → B
```

chỉ nếu:

```text
Observable(A) == Observable(B)
```

Đây là định nghĩa đúng của:

> zero-cost abstraction

Không phải:

> compiler được phép làm bất cứ thứ gì miễn nhanh hơn.

---

# 51. Execution Semantics invariant mới

Tôi đề xuất bổ sung:

### AES-18 — Deterministic Evaluation

Các expression có observable interactions được evaluate theo left-to-right semantics.

### AES-19 — No Implicit Integer UB

Safe integer operations không được dựa trên undefined overflow behavior.

### AES-20 — Explicit Numeric Conversion

Không có implicit narrowing conversion.

### AES-21 — Deterministic Invalid Arithmetic

Divide-by-zero, invalid shift và checked overflow có behavior xác định.

### AES-22 — Initialization Safety

Safe code không được đọc uninitialized value.

### AES-23 — Replacement Semantics

Assignment evaluates RHS before replacing/dropping destination.

### AES-24 — Observable Drop Ordering

Observable resource release phải giữ semantic ordering.

### AES-25 — Floating-Point Contract

Optimizer không được thay đổi floating-point semantics trừ khi fast-math semantics được explicit.

### AES-26 — Explicit Address Identity

Ordinary values không có stable address guarantee nếu type/storage abstraction không yêu cầu.

### AES-27 — Optimization Equivalence

Optimizer chỉ được thay đổi behavior trong phạm vi observable semantics được bảo toàn.

---

# 52. Một vấn đề còn lại: `Copy` và assignment

Ví dụ:

```axiom
let a: i32 = 10
let b = a
```

`i32` Copy:

```text
a = OWNED
b = COPY(a)
a = OWNED
b = OWNED
```

Nhưng:

```axiom
let a = Buffer(...)
let b = a
```

là:

```text
MOVE(a → b)
```

Do đó:

```text
let
```

không có một semantics duy nhất.

Nó phụ thuộc property `Copy`.

---

# 53. Đây là một ưu điểm lớn của model hiện tại

Syntax đơn giản:

```axiom
let b = a
```

nhưng compiler biết:

```text
Copy type
    → copy

Non-Copy type
    → move
```

Programmer không cần:

```text
clone()
move()
borrow()
```

ở mọi nơi.

Nếu muốn explicit assertion, ta vẫn có:

```axiom
let b = move(a)
```

nhưng không bắt buộc.

---

# 54. `clone` phải là explicit

Nếu type có:

```text
Clone
```

thì:

```axiom
let b = clone(a)
```

tạo resource/value mới.

Không nên để:

```text
let b = a
```

tự động clone non-Copy.

Nếu không, compiler mất tính predictable và có thể vô tình tạo allocation/copy lớn.

---

# 55. Đây là ranh giới rất đẹp

```text
let b = a
```

= semantic transfer/copy dựa trên **Copy property**.

```text
let b = clone(a)
```

= programmer explicitly yêu cầu tạo value/resource mới.

```text
let v = view(a)
```

= programmer explicitly yêu cầu non-owning capability.

Ba thứ hoàn toàn khác nhau:

```text
COPY
MOVE
VIEW
```

---

# 56. Từ đây Execution Semantics đã đủ để Oracle bắt đầu có tính normative

Nhưng còn **một phần lớn cuối cùng trước khi đóng Core v0.1**:

```text
          Execution
              │
      ┌───────┴────────┐
      │                │
   single-thread    concurrency
                       │
              ┌────────┴────────┐
              │                 │
            Thread            Async
              │                 │
           Send/Share       Suspend
              │                 │
              └────────┬────────┘
                       ↓
                    Atomics
```

Vì Axiom đặt mục tiêu **performance mạnh nhưng không bắt programmer quản lý lifetime/borrow thủ công**, phần concurrency phải đặc biệt cẩn thận.

Bước tiếp theo nên là **`AXIOM CONCURRENCY MEMORY MODEL v0.1`**, trong đó ta cần chốt một vấn đề rất quan trọng:

> **Axiom có nên áp dụng “data-race-free by construction” cho safe code, nhưng vẫn cho phép low-level atomic lock-free programming mà không biến toàn bộ compiler thành Rust-style borrow checker hay không?**

Tôi nghĩ đây là nơi Axiom có thể tạo ra khác biệt đáng kể so với Rust/C++ nếu thiết kế đúng.