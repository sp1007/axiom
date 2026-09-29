# AXIOM LANGUAGE SPECIFICATION v0.1 — Part II
## Expressions · Operators · Evaluation · Calls · Closures · Control Flow

Part II này chốt một vấn đề rất quan trọng: **một biểu thức Axiom phải có semantics đủ rõ để optimizer có thể tự do tối ưu nhưng không được thay đổi thứ tự observable side effects**.

---

# 1. Expression model

Mọi expression trong Axiom có:

```text
Type
Value semantics
Evaluation effects
Ownership effect
Control-flow behavior
```

Ví dụ:

```axiom
x + y
```

không chỉ có type `T`, mà semantic analysis còn biết:

```text
reads x
reads y
produces T
does not consume x/y
may panic if arithmetic is checked
```

Thông tin này được lưu trong Typed HIR/MIR.

---

# 2. Expression categories

v0.1 phân biệt các nhóm:

```text
Literal
Name
Path
Unary
Binary
Assignment
Call
MethodCall
Field
Index
Range
Array
Tuple
StructLiteral
EnumConstructor
Block
If
Match
Loop
Closure
Await
Cast
View
Move
Unsafe
```

Không cần tạo syntax riêng cho mọi semantic operation.

---

# 3. Value-producing expressions

Expression thông thường tạo một value.

Ví dụ:

```axiom
let x = foo() + 10
```

Compiler phải biết:

```text
foo() → value
10    → value
+     → value
```

Assignment là ngoại lệ:

```axiom
x = 10
```

có type:

```text
()
```

---

# 4. Evaluation order

Đây là quy tắc **normative**:

> **Axiom đánh giá operands từ trái sang phải.**

Ví dụ:

```axiom
foo(a(), b(), c())
```

thứ tự:

```text
a()
→ b()
→ c()
→ foo(...)
```

Không được tự ý đổi thành:

```text
b()
→ c()
→ a()
```

nếu có observable effect.

---

# 5. Nhưng optimizer vẫn được reorder

Compiler MAY reorder machine instructions nếu chứng minh rằng observable semantics không thay đổi.

Ví dụ:

```axiom
let a = x * 2
let b = y * 4
```

có thể được thực thi song song/reordered nếu:

```text
x/y reads không conflict
không side effect
không panic observable difference
```

Do đó:

> **Source evaluation order là semantic order; machine instruction order không nhất thiết giống source order.**

---

# 6. Function argument evaluation

```axiom
foo(a(), b(), c())
```

luôn:

```text
a()
b()
c()
```

theo thứ tự trái → phải.

Điều này áp dụng cho:

```text
function calls
method calls
generic calls
constructor-like aggregate evaluation
```

---

# 7. Short-circuit operators

```axiom
a && b
```

Nếu `a == false`:

```text
b
```

không được evaluate.

Tương tự:

```axiom
a || b
```

Nếu `a == true`:

```text
b
```

không được evaluate.

Đây là semantic requirement, không chỉ optimization.

---

# 8. Boolean operators

`&&`, `||`, `!` chỉ hoạt động trên `bool`.

Không có:

```text
0 → false
1 → true
```

implicit conversion.

---

# 9. Equality

```axiom
a == b
a != b
```

phải resolve tới semantic equality operation phù hợp.

Không có hidden pointer identity.

Đối với user-defined type, equality phải được cung cấp bởi compiler intrinsic hoặc trait phù hợp.

---

# 10. Identity không phải equality

Ví dụ:

```text
Box<User>
```

hai object có thể:

```text
different storage identity
same logical/value content
```

và:

```text
a == b
```

không mặc định có nghĩa:

```text
address(a) == address(b)
```

Physical address identity chỉ thuộc unsafe/system-level semantics.

---

# 11. Comparison

```text
<
<=
>
>=
```

resolve thông qua ordered semantic operation/trait.

Compiler không được tạo implicit conversion chain phức tạp để tìm implementation.

---

# 12. Operator resolution

Operator resolution phải deterministic.

Ví dụ:

```axiom
a + b
```

conceptually:

```text
resolve Add for type(a), type(b)
```

Compiler phải tìm **một semantic implementation duy nhất**.

Nếu:

```text
0 implementation
```

→ error.

Nếu:

```text
>1 viable implementation
```

→ ambiguity error.

Không thử lần lượt các conversion "có vẻ hợp lý".

---

# 13. Primitive operators

Primitive numeric operations được compiler-known.

Ví dụ:

```axiom
let x = a + b
```

với:

```text
a: i32
b: i32
```

không cần instantiate một generic library trait chỉ để thực hiện phép cộng.

Compiler có thể biểu diễn trực tiếp bằng MIR arithmetic instruction.

---

# 14. User-defined operators

User-defined type có thể implement operator traits.

Ví dụ conceptual:

```axiom
trait Add<Rhs> {
    type Output
    fn add(self: view<Self>, rhs: view<Rhs>) -> Self.Output
}
```

Tên chính xác của built-in operator traits sẽ được chuẩn hóa trong Standard Trait Specification, nhưng semantics phải tương đương.

---

# 15. Không có implicit mixed numeric operator

Ví dụ:

```axiom
let a: u32 = 10
let b: u64 = 20

let c = a + b
```

→ compile error.

Phải:

```axiom
let c = (a as u64) + b
```

---

# 16. Arithmetic operators

Checked:

```text
+
-
*
```

Wrapping:

```text
+%
-%
*%
```

Saturating:

```text
+|
-|
*|
```

Đây là **ba semantic operations khác nhau**.

Compiler không được quyết định dựa trên build mode.

---

# 17. Division and remainder

```text
/
%
```

integer division/remainder phải có semantics xác định.

Division by zero:

```text
panic/trap
```

không phải UB.

---

# 18. Unary operators

```text
-x
+x
!x
~x
```

`!` chỉ dành cho boolean.

`~` là bitwise complement đối với integer-compatible types.

`-` phải obey overflow semantics của type.

---

# 19. Shift

```axiom
x << n
x >> n
```

Shift semantics phải được xác định cho shift count ngoài range.

Axiom v0.1 chọn:

> **Invalid shift count trong safe code là runtime failure, không UB.**

Compiler MAY prove count hợp lệ và loại bỏ check.

---

# 20. Bounds checking

Index:

```axiom
a[i]
```

safe indexing.

Nếu:

```text
i >= length
```

→ panic/trap.

Compiler MAY loại bỏ bounds check nếu chứng minh:

```text
0 <= i < length
```

---

# 21. Unsafe indexing

Unsafe/system API MAY cung cấp unchecked access.

Conceptual:

```axiom
unsafe {
    a.get_unchecked(i)
}
```

Điều kiện validity trở thành programmer responsibility.

Nhưng compiler vẫn kiểm tra các semantic invariant khác.

---

# 22. Index operator

Indexing user-defined type được resolve qua indexing protocol/trait.

Ví dụ:

```axiom
buffer[i]
```

có thể tạo:

```text
view<T>
```

hoặc:

```text
mut_view<T>
```

tùy access context.

Compiler phải preserve capability semantics.

---

# 23. Mutable indexing

Ví dụ:

```axiom
var a = [1, 2, 3]

a[0] = 10
```

Compiler semantic model:

```text
exclusive write capability to region a[0]
```

Không nhất thiết tạo một `mut_view` runtime object.

---

# 24. Overlapping indexing

Ví dụ:

```axiom
var a = ...
let x = mut_view(a[0..4])
let y = mut_view(a[2..6])
```

→ safe code phải reject nếu compiler không thể chứng minh regions disjoint.

Nếu:

```text
[0..4]
[4..8]
```

→ DISJOINT.

Do đó có thể hợp lệ.

---

# 25. Field access

```axiom
object.field
```

là place/value access tùy context.

Read:

```axiom
let x = object.field
```

có thể:

- Copy nếu field: Copy;
- Move nếu owned non-Copy.

Write:

```axiom
object.field = value
```

yêu cầu exclusive write access.

---

# 26. Field-level alias analysis

Compiler được phép nhận biết:

```axiom
user.name
user.age
```

là DISJOINT nếu layout/field semantics chứng minh được.

Vì vậy:

```text
mutate(user.name)
mutate(user.age)
```

có thể coexist.

Không cần borrow syntax.

---

# 27. Range expressions

```axiom
0..10
```

= half-open:

```text
0 <= x < 10
```

```axiom
0..=10
```

= inclusive:

```text
0 <= x <= 10
```

---

# 28. Open-ended ranges

Hỗ trợ:

```axiom
a[..]
a[..4]
a[1..]
a[1..=4]
```

Range expression itself không nhất thiết allocate.

Compiler/library có thể biểu diễn range bằng vài scalar values.

---

# 29. Range không mặc định là collection

```axiom
0..1_000_000_000
```

không tạo billion-element array.

Nó là range descriptor/iterator abstraction.

---

# 30. Function call

```axiom
foo(a, b)
```

resolution:

```text
resolve foo
→ resolve generic arguments
→ resolve parameter types
→ evaluate arguments left-to-right
→ capability/ownership verification
→ call
```

---

# 31. Passing by value

```axiom
fn consume(x: Buffer)
```

Nếu `Buffer` không Copy:

```axiom
consume(buffer)
```

→ Move.

Sau đó:

```axiom
use(buffer)
```

→ compile error.

---

# 32. Passing `view`

```axiom
fn print(x: view<User>)
```

cho phép:

```axiom
print(user)
```

Compiler tạo ephemeral read capability.

Không cần:

```axiom
print(view(user))
```

cho trường hợp parameter đã yêu cầu `view<T>`.

---

# 33. Passing `mut_view`

```axiom
fn update(x: mut_view<User>)
```

cho phép:

```axiom
update(user)
```

Compiler tạo ephemeral exclusive-write capability.

Trong thời gian call:

```text
owner access
+
other conflicting capability
```

bị chặn.

---

# 34. Explicit view binding

Khi muốn lưu capability:

```axiom
let v = view(user)
```

hoặc:

```axiom
let v = mut_view(user)
```

Đây là **explicit**, vì compiler không được âm thầm tạo escaping capability.

---

# 35. Return value ownership

```axiom
fn make() -> Buffer {
    ...
}
```

return:

```text
transfers semantic ownership
```

Không có copy bắt buộc.

Ví dụ:

```axiom
let x = make()
```

`x` trở thành owner.

---

# 36. Return view

Có thể:

```axiom
fn name(x: view<User>) -> view<Text>
```

nhưng capability returned phải có provenance hợp lệ.

Compiler phải chứng minh returned view không vượt owner.

Ví dụ nguy hiểm:

```axiom
fn bad() -> view<i32> {
    let x = 10
    view(x)
}
```

→ compile error.

---

# 37. `Copy`

Nếu type `T: Copy`:

```axiom
let b = a
```

trong value context có thể tạo semantic duplicate.

Nhưng:

> Copy không yêu cầu physical memory copy.

Compiler có thể:

```text
register reuse
constant propagation
scalar replacement
```

miễn semantics đúng.

---

# 38. `Move`

Nếu type không Copy:

```axiom
let b = a
```

là Move.

Move chỉ là:

```text
ownership state transition
```

không phải:

```text
memcpy
```

---

# 39. `Clone`

`Clone` khác `Copy`.

```axiom
let b = a.clone()
```

có thể:

- allocate;
- deep-copy;
- duplicate resource;
- perform arbitrary computation;
- fail nếu API định nghĩa như vậy.

Không có guarantee zero-cost.

---

# 40. `drop`

Explicit:

```axiom
drop(x)
```

kết thúc ownership của `x`.

Nhưng:

```text
Drop != necessarily deallocate
```

Ví dụ Arena-backed object có thể chỉ giải phóng logical resource/state.

---

# 41. Drop và expression evaluation

Compiler phải đảm bảo:

```axiom
foo(make_a(), make_b())
```

nếu `make_a()` thành công và `make_b()` panic:

```text
a
```

vẫn được cleanup đúng.

Do evaluation order deterministic nên cleanup cũng deterministic.

---

# 42. `?`

Ví dụ:

```axiom
fn load() -> Result<Data, Error> {
    let file = open()?
    let data = read(file)?
    Ok(data)
}
```

`?` semantic equivalent:

```text
evaluate expression
→ if success, extract value
→ if failure, cleanup live owned values
→ return failure
```

Không phải exception.

---

# 43. `?` với `Result`

Nếu:

```text
expr: Result<T, E2>
function return: Result<U, E1>
```

compiler chỉ được dùng conversion trực tiếp được phép:

```text
E2 → E1
```

theo constrained error conversion rule.

Không chạy arbitrary conversion chain.

---

# 44. `?` với `Option`

```axiom
fn find() -> Option<User> {
    let user = lookup()?
    Some(user)
}
```

`None` propagate.

Không chuyển `None` thành `panic`.

---

# 45. `panic`

`panic(...)` có type:

```text
never
```

và không normal-return.

Panic phải trigger cleanup theo configured panic strategy.

---

# 46. `unreachable`

```axiom
unreachable()
```

cũng có:

```text
never
```

Compiler có thể dùng assumption rằng path không normal-return.

Nếu execution thực sự tới đó → trap/panic theo profile.

---

# 47. `assert`

```axiom
assert(x > 0)
```

runtime check.

Không được coi là compiler proof.

Ví dụ:

```axiom
assert(i < a.len)
a[i]
```

compiler MAY prove/reuse assertion.

Nhưng:

```text
debug_assert
```

không được dùng làm safety guarantee khi release build loại bỏ nó.

---

# 48. Blocks and ownership

Block tạo scope semantic.

```axiom
{
    let x = make()
    use(x)
}
```

cuối block:

```text
x
→ Drop nếu cần
```

Compiler MAY shorten physical lifetime nếu không observable.

---

# 49. Last-use optimization

Ví dụ:

```axiom
let file = open()?
read(file)?
compute()
```

Nếu `file` không còn dùng sau `read`, compiler MAY semantic-drop `file` ngay sau last use, **nếu Drop semantics cho phép và không thay đổi observable behavior**.

Đây là một optimization quan trọng.

---

# 50. `break`

v0.1:

```axiom
break
```

không có value.

Loop:

```axiom
while condition {
    if done {
        break
    }
}
```

có type:

```text
()
```

Không có:

```axiom
break 42
```

trong v0.1.

---

# 51. `continue`

```axiom
continue
```

kết thúc iteration hiện tại.

Trước khi chuyển sang iteration tiếp theo, compiler phải thực hiện cleanup của các local có lifetime kết thúc tại iteration boundary.

---

# 52. `while`

```axiom
while condition {
    body()
}
```

`condition` phải là `bool`.

Không có implicit truthiness.

Loop có type `()`.

---

# 53. `for`

```axiom
for x in items {
    use(x)
}
```

semantic sugar cho iterator protocol.

Compiler có thể lower thành loop/MIR trực tiếp.

Không bắt buộc tạo iterator object runtime nếu optimizer có thể eliminate.

---

# 54. Closure

Syntax:

```axiom
|x, y| x + y
```

Type conceptually:

```text
Fn<(T,T), R>
```

nhưng closure type concrete có thể compiler-private.

---

# 55. Closure capture

Compiler tự phân tích capture.

Ví dụ:

```axiom
let x = 10

let f = || x + 1
```

`x` chỉ cần read access.

Không cần programmer viết borrow annotation.

---

# 56. Mutable capture

```axiom
var count = 0

let mut f = || {
    count = count + 1
}
```

Compiler nhận biết closure cần exclusive mutation capability.

Nếu closure sống lâu hơn owner hoặc gây conflict:

→ compile error hoặc yêu cầu ownership transfer phù hợp.

---

# 57. `move` closure

Explicit:

```axiom
let f = move || {
    use(resource)
}
```

`move` yêu cầu captured owned values được chuyển ownership vào closure environment.

Sau đó source không còn sở hữu chúng.

---

# 58. Closure environment

Conceptually:

```text
closure =
    environment
    +
    call entry
```

Nhưng representation không cố định.

Compiler có thể:

```text
heap allocate
stack allocate
inline
scalarize
eliminate
```

nếu semantics không yêu cầu stable storage.

---

# 59. Capturing closure → function pointer

Không implicit convert:

```text
capturing closure
→ plain fn pointer
```

vì closure có environment.

Một non-capturing closure MAY coerce sang function pointer nếu ABI/function type tương thích.

---

# 60. Closure ABI

Closure representation **không phải stable ABI**.

Nếu cần FFI callback:

```text
extern "C" fn(...)
```

và explicit context pointer/API.

Không truyền capturing closure trực tiếp sang C ABI.

---

# 61. Async expression

```axiom
let future = fetch()
let result = future.await
```

`.await` là explicit suspension point.

Nếu Future chưa Ready:

```text
suspend
```

Nếu Ready:

```text
continue
```

---

# 62. `.await` precedence

Postfix operations bind trước binary operators.

Ví dụ:

```axiom
fetch().await?
```

được hiểu:

```text
(fetch().await)?
```

không phải:

```text
fetch().(await?)
```

---

# 63. Capability qua await

v0.1 cấm:

```text
view<T> sống qua await
mut_view<T> sống qua await
```

Compiler phải reject nếu capability vẫn live tại suspension point.

Ví dụ:

```axiom
let v = view(buffer)

some_async().await

use(v)
```

→ compile error.

Cách an toàn:

```axiom
{
    let v = view(buffer)
    use(v)
}

some_async().await
```

---

# 64. Owned value qua await

Owned value **được phép** sống qua await.

Ví dụ:

```axiom
let data = load()
let result = fetch(data).await
```

nếu ownership/Send rules cho phép.

Compiler chỉ lưu state thực sự live qua suspension.

---

# 65. Async không đồng nghĩa thread

```axiom
async fn foo()
```

không có nghĩa:

```text
new OS thread
```

Async là control-flow/state-machine abstraction.

Executor quyết định scheduling.

---

# 66. Async state machine

Compiler MAY lower:

```axiom
async fn foo() { ... }
```

thành:

```text
Future<StateMachine>
```

State machine chứa chỉ các giá trị cần sống qua suspension.

Dead locals phải được loại bỏ khỏi state machine nếu không observable.

---

# 67. No heap guarantee

Async Future:

```text
MUST NOT inherently require heap allocation
```

Compiler MAY:

```text
stack
inline
arena
heap
```

tùy caller/storage semantics.

---

# 68. Dynamic call

```axiom
object.draw()
```

nếu static type biết concrete implementation:

```text
direct/static dispatch
```

Nếu:

```axiom
view<dyn Draw>
```

thì:

```text
dynamic dispatch
```

explicit từ type.

---

# 69. No hidden dynamic dispatch

Trait usage:

```axiom
fn draw<T: Draw>(x: view<T>)
```

không tự động trở thành vtable dispatch.

Compiler có thể monomorphize.

Dynamic dispatch chỉ xảy ra khi abstraction là `dyn Trait` hoặc explicit dynamic mechanism.

---

# 70. Expression effect model

Để hỗ trợ optimizer và AI tooling, Typed HIR/MIR SHOULD track effect categories:

```text
READ
WRITE
MOVE
ALLOC
DEALLOC
DROP
CALL
PANIC
TRAP
ATOMIC
VOLATILE
SUSPEND
FFI
IO
```

Đây không phải source-level effect system.

Programmer không phải khai báo:

```text
throws
allocates
reads
```

trừ các ABI/system annotations cần thiết.

---

# 71. Effect information là compiler fact

Ví dụ:

```axiom
x + y
```

compiler có thể biết:

```text
READ x
READ y
MAY_PANIC arithmetic
```

AI/IDE có thể truy vấn thông tin này.

Nhưng programmer không phải viết effect annotation.

---

# 72. Evaluation order và optimizer

Optimizer được phép:

```text
inline
constant-fold
dead-code eliminate
CSE
LICM
vectorize
reassociate
instruction reorder
```

chỉ khi không thay đổi:

```text
return value
memory effects
Drop
panic/trap behavior
atomic ordering
volatile behavior
FFI behavior
observable allocation/storage contract
```

---

# 73. Observable side effect

Một operation được coi là observable nếu có thể ảnh hưởng semantic behavior thông qua:

```text
IO
volatile
FFI
atomic synchronization
observable memory
panic/trap
Drop side effect
explicit address/storage identity
```

Pure computation không cần giữ source instruction order.

---

# 74. `Drop` là observable

Ví dụ:

```axiom
let a = Resource(...)
let b = compute()
```

nếu `Resource.Drop` có observable release semantics, compiler không được tùy tiện reorder/drop sớm nếu làm thay đổi observable behavior.

Tuy nhiên compiler có thể shorten lifetime khi chứng minh semantics vẫn tương đương.

---

# 75. Function purity không phải source annotation

v0.1 **không yêu cầu**:

```text
pure fn
impure fn
```

Compiler tự phân tích.

Điều này tránh việc programmer phải maintain một effect type system phức tạp chỉ để tối ưu.

---

# 76. Semantic invariant — Expressions

### AEXPR-20
Every expression has one resolved semantic type.

### AEXPR-21
Expression evaluation order is deterministic.

### AEXPR-22
Function arguments are evaluated left-to-right.

### AEXPR-23
Short-circuit operators do not evaluate skipped operands.

### AEXPR-24
Assignment has unit type.

### AEXPR-25
Safe indexing is bounds-checked.

### AEXPR-26
Bounds checks may be eliminated only when validity is proven.

### AEXPR-27
Numeric conversions are explicit.

### AEXPR-28
Operator resolution is deterministic.

### AEXPR-29
Implicit conversion graphs do not participate in operator resolution.

### AEXPR-30
Move is an ownership-state transition.

### AEXPR-31
Copy is semantic value duplication.

### AEXPR-32
Clone is explicit potentially-expensive duplication.

### AEXPR-33
Returning an owned value transfers semantic ownership.

### AEXPR-34
Returned capabilities must have valid provenance.

### AEXPR-35
`?` is control-flow propagation.

### AEXPR-36
`panic` has `never` type.

### AEXPR-37
`break` has no value in v0.1.

### AEXPR-38
Async suspension is explicit.

### AEXPR-39
Capabilities cannot cross `.await` in v0.1.

### AEXPR-40
Owned values may cross `.await` subject to concurrency rules.

### AEXPR-41
Capturing closures own/manage their capture environment according to inferred capture semantics.

### AEXPR-42
Capturing closures cannot implicitly become plain function pointers.

### AEXPR-43
Dynamic dispatch requires explicit dynamic type semantics.

### AEXPR-44
Optimizer transformations must preserve observable expression semantics.

### AEXPR-45
Source evaluation order is independent from machine instruction order.

---

# 77. Negative test suite

Compiler conformance MUST include cases such as:

```axiom
let x: u8 = 300
```

→ numeric literal overflow.

```axiom
let x: u32 = 1
let y: u64 = 2
let z = x + y
```

→ mixed numeric types.

```axiom
if 1 {
}
```

→ non-bool condition.

```axiom
let a = [1, 2, 3]
let x = a[10]
```

→ runtime bounds failure.

```axiom
let x = foo()
use(x)
use(x)
```

→ depends on `x: Copy`; otherwise second use after move is error if first use consumes it.

```axiom
fn bad() -> view<i32> {
    let x = 10
    view(x)
}
```

→ dangling capability.

```axiom
let v = view(buffer)
await_task().await
use(v)
```

→ capability across await.

```axiom
let f = move || resource
use(resource)
```

→ moved capture.

```axiom
break 10
```

→ invalid in v0.1.

---

# 78. MIR lowering examples

### Checked addition

Source:

```axiom
let c = a + b
```

Conceptual MIR:

```text
%a = READ a
%b = READ b
%c = ADD_CHECKED %a, %b
```

### Wrapping:

```axiom
let c = a +% b
```

→

```text
%c = ADD_WRAP %a, %b
```

### Saturating:

```axiom
let c = a +| b
```

→

```text
%c = ADD_SAT %a, %b
```

Ba operations này không được compiler trộn semantics.

---

# 79. Call lowering

Source:

```axiom
let x = foo(a(), b())
```

MIR conceptual:

```text
%a = CALL a
%b = CALL b
%x = CALL foo(%a, %b)
```

Nếu `b()` panic:

```text
%x
```

chưa tồn tại.

Nhưng mọi resource đã tạo thành công trước đó phải được cleanup.

---

# 80. View lowering

Source:

```axiom
print(user)
```

với:

```axiom
fn print(x: view<User>)
```

conceptually:

```text
%cap = VIEW_READ user
CALL print(%cap)
END_CAP %cap
```

`%cap` không cần tồn tại ở runtime.

Compiler có thể trực tiếp truyền:

```text
pointer + metadata
```

hoặc thậm chí chỉ truyền scalar fields nếu ABI/optimization cho phép.

---

# 81. Capability erasure

Sau verifier:

```text
Ownership
Capability provenance
Borrow/lifetime proof
```

có thể được erase khỏi release machine representation.

Điều này cực kỳ quan trọng đối với mục tiêu hiệu năng của Axiom:

```text
compiler checks complexity
        ↓
machine code
        ↓
không nhất thiết còn runtime cost
```

---

# 82. Part II — kết luận

Đến đây chúng ta đã khóa được một nền tảng quan trọng:

```text
SOURCE
  │
  ├─ deterministic evaluation
  │
  ├─ explicit conversion
  │
  ├─ explicit ownership transitions
  │
  ├─ explicit capability boundaries
  │
  ├─ explicit dynamic dispatch
  │
  └─ explicit async suspension
          │
          ▼
       TYPED HIR
          │
          ▼
        MIR
          │
          └── verifier có thể chứng minh
                    │
                    ▼
              capability/ownership
              có thể bị erase
```

Điểm đáng chú ý là Axiom hiện **không cần borrow checker syntax**, nhưng compiler vẫn có đủ thông tin để thực hiện những proof tương đương ở cấp semantic.

---

# 83. Tiếp theo — Part III

Bây giờ đến phần quan trọng nhất của toàn bộ ngôn ngữ:

## **AXIOM LANGUAGE SPECIFICATION v0.1 — Part III**
### Ownership · Capability · Move · Copy · View · Mut View · Drop · Lifetime

Phần này sẽ chốt normative toàn bộ memory model, bao gồm cả những case khó nhất:

```text
partial move
nested struct
array element move
field move
pattern move
return
early return
panic
? propagation
closure capture
async state
Vec relocation
Arena
Box
stable address
view invalidation
mut_view conflict
aliasing
custom Drop
derived Drop
Drop order
explicit drop()
```

và đặc biệt sẽ trả lời dứt khoát câu hỏi nền tảng của Axiom:

> **Làm thế nào để có safety của ownership/borrow checking nhưng programmer gần như không phải "lập trình bằng con trỏ và lifetime".**