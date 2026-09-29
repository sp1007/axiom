# BOOTSTRAP-132 — Expression Semantics, Evaluation Order & Control Flow

**Trạng thái: FROZEN / COMPLETED**

Mục tiêu của task này là khóa một nguyên tắc rất quan trọng:

> **Cùng một source program phải có cùng semantic evaluation order, bất kể compiler optimization ở mức nào.**

Axiom không đi theo mô hình C/C++ nơi nhiều trường hợp evaluation order khiến programmer phải nhớ các quy tắc phức tạp hoặc rơi vào undefined behavior.

---

# 1. Expression là giá trị + hiệu ứng

Mỗi expression về semantic có:

```text id="x4b6zy"
Expression {
    Type
    ValueSemantics
    Effects
    ControlFlow
    SourceOrigin
}
```

Ví dụ:

```ax
x + y
```

có:

```text
Type   = type của x/y
Effects = Read(x), Read(y)
Control = Continue
```

Trong khi:

```ax
foo()
```

có thể:

```text
Type   = T
Effects = tùy foo
Control = Continue / Panic
```

---

# 2. Expression và statement

Axiom là expression-oriented nhưng không biến mọi thứ thành expression một cách máy móc.

Ví dụ:

```ax
let x = 10;
x + 1;
```

`let` là declaration statement.

`x + 1` là expression statement.

Block:

```ax
{
    let x = 10;
    x + 1
}
```

có giá trị cuối:

```text
1
```

---

# 3. Block expression

Block:

```ax
{
    let x = 10;
    let y = 20;
    x + y
}
```

có type:

```text
i32
```

và value:

```text
30
```

Nếu block kết thúc bằng statement không tạo value:

```ax
{
    let x = 10;
}
```

type:

```text
unit
```

---

# 4. Không có implicit semicolon insertion

Đã frozen từ syntax:

```ax
x + y
```

và:

```ax
x + y;
```

được parser xử lý theo grammar rõ ràng.

Không có heuristic dựa trên newline.

---

# 5. Evaluation order — trái sang phải

Axiom chọn:

> **Subexpressions được evaluate theo thứ tự source từ trái sang phải, trừ những control-flow construct có semantics riêng.**

Ví dụ:

```ax
foo(a(), b(), c())
```

thứ tự:

```text id="5l9v6g"
a()
↓
b()
↓
c()
↓
foo(...)
```

---

# 6. Function arguments

```ax
foo(
    make_a(),
    make_b(),
    make_c(),
)
```

luôn:

```text id="7ml7gq"
make_a
→ make_b
→ make_c
→ call foo
```

Compiler **không được reorder observable side effects**.

---

# 7. Compiler vẫn được optimize

Ví dụ:

```ax
let x = 1 + 2;
```

compiler có thể constant-fold.

Nhưng nếu:

```ax
foo(a(), b())
```

thì không được biến:

```text id="b7m1ef"
b()
→ a()
```

nếu điều đó làm thay đổi observable semantics.

---

# 8. Observable side effect

Effects có thể gồm:

```text id="l2l4vq"
Read
Write
Atomic
Volatile
IO
Allocate
Deallocate
Drop
Panic
Synchronization
ForeignCall
```

Optimizer phải preserve thứ tự cần thiết giữa các effect.

---

# 9. Pure computation

Nếu compiler chứng minh:

```ax
x * 2 + 3
```

không có observable side effect ngoài input reads, nó có thể:

- reorder internal arithmetic;
- vectorize;
- fuse;
- constant-fold;
- eliminate.

Miễn semantic result không thay đổi.

---

# 10. Assignment

```ax
x = expr;
```

semantic:

```text id="98v4nm"
evaluate expr
↓
verify destination
↓
write destination
```

Không evaluate destination sau RHS.

---

# 11. Compound assignment

```ax
x += y;
```

semantic tương đương:

```text id="tnd3a0"
read x
read y
compute
write x
```

nhưng **không phải** textual rewrite thành:

```ax
x = x + y;
```

vì compound assignment có thể có semantics đặc biệt với indexing/property access.

---

# 12. Indexing

```ax
a[i]
```

semantic gồm:

```text id="z1ep7m"
evaluate a
evaluate i
check access
perform indexing
```

Nếu `a` là mutable place:

```ax
a[i] = value;
```

thì destination capability phải được verify.

---

# 13. Bounds checking

Safe indexing mặc định phải bảo đảm:

```text id="j4q8yv"
0 <= i < len(a)
```

Compiler có thể eliminate check nếu chứng minh range.

Ví dụ:

```ax
for i in 0..a.len() {
    use(a[i]);
}
```

có thể được bounds-check elimination.

---

# 14. Bounds failure

Không có undefined behavior trong safe Core.

Out-of-bounds có thể:

```text id="4tqf4n"
panic
```

hoặc target/profile-specific trap nếu profile chọn semantics tương ứng.

Nhưng phải được phân loại rõ:

```text
defined failure
```

không phải:

```text
undefined behavior
```

---

# 15. Field access

```ax
user.name
```

resolve:

```text id="xaj3qa"
User
 ↓
FieldId(name)
```

Sau đó:

```text id="0p6vaz"
read Place(user.name)
```

---

# 16. Field assignment

```ax
user.name = value;
```

yêu cầu exclusive mutable access tới field:

```text id="2m1e67"
mut_view(user.name)
```

semantic capability.

Nếu có:

```ax
let r = view(user.name);
user.name = x;
```

trong lúc `r` còn sống:

```text id="3zj0ef"
reject
```

---

# 17. Disjoint fields

Axiom cho phép compiler chứng minh:

```ax
struct Pair {
    a: i32,
    b: i32,
}
```

và:

```text id="n9v9t0"
view(pair.a)
mut_view(pair.b)
```

không conflict.

Đây là field-sensitive capability model đã frozen.

---

# 18. Method call

```ax
user.save()
```

semantic pipeline:

```text id="b8i6kf"
evaluate receiver
↓
resolve method
↓
resolve trait/inherent implementation
↓
evaluate arguments
↓
call
```

Method resolution xảy ra compile-time; receiver evaluation xảy ra runtime/comptime tùy context.

---

# 19. Receiver evaluation

Ví dụ:

```ax
make_user().save()
```

phải:

```text id="d1o5uh"
make_user()
↓
save(...)
```

Temporary receiver tồn tại đủ lâu cho method call.

---

# 20. Method argument order

```ax
user.save(make_a(), make_b())
```

thứ tự:

```text id="8v5qyw"
evaluate user
→ make_a()
→ make_b()
→ invoke save
```

---

# 21. Method dispatch

Nếu:

```ax
fn save<T: Save>(x: T)
```

và `T` concrete:

```text id="j7i4w4"
static dispatch
```

Nếu:

```ax
x: dyn Save
```

thì:

```text id="x5fydy"
dynamic dispatch
```

Không thay đổi evaluation-order semantics.

---

# 22. Temporary values

Axiom phải phân biệt:

```text id="9s4ezo"
semantic lifetime
```

với:

```text id="r7x3f9"
physical storage lifetime
```

Temporary có thể nằm:

```text
register
stack
inline
heap
```

compiler tự quyết định.

---

# 23. Temporary destruction

Nếu temporary có Drop:

```ax
make_resource().use();
```

resource phải được semantic cleanup đúng thời điểm.

Compiler có thể:

```text id="8o9k1g"
extend
shorten
eliminate
```

physical storage lifetime nếu observable semantics không đổi.

---

# 24. Drop order

Với:

```ax
{
    let a = A();
    let b = B();
}
```

semantic Drop:

```text id="xifc2h"
b
↓
a
```

theo reverse initialization/declaration order đã frozen.

---

# 25. Function arguments và Drop

Ví dụ:

```ax
foo(make_a(), make_b());
```

Nếu các temporary cần Drop, compiler phải xác định cleanup order deterministic.

Axiom chọn:

> Temporary resources được cleanup theo reverse order của việc hoàn thành initialization/evaluation, trong phạm vi expression semantics đã xác định.

Compiler phải biểu diễn điều này rõ trong MIR.

---

# 26. `if` là expression

```ax
let x = if condition {
    10
} else {
    20
};
```

type phải unify:

```text id="a5kj3r"
type(10)
=
type(20)
```

hoặc compiler tìm coercion hợp lệ theo type rules.

---

# 27. `if` evaluation

```text id="17osik"
evaluate condition
↓
if true:
    evaluate then
else:
    evaluate else
```

Branch không được evaluate trước.

---

# 28. Không có speculative observable execution

Optimizer có thể speculate machine instructions nếu không thay đổi observable behavior.

Nhưng semantic model vẫn:

```text id="zy9m0q"
only selected branch is evaluated
```

Điều này đặc biệt quan trọng với:

```ax
if cond {
    unsafe_operation()
} else {
    safe_operation()
}
```

---

# 29. `match`

```ax
match value {
    Some(x) => ...
    None => ...
}
```

semantic:

```text id="v6czp4"
evaluate value exactly once
↓
discriminate
↓
select matching arm
↓
evaluate selected arm
```

---

# 30. Match scrutinee ownership

Nếu:

```ax
match resource {
    A(x) => ...
    B(y) => ...
}
```

ownership analysis quyết định:

```text id="9sn9f1"
move
copy
view
destructure
```

Không phải parser quyết định.

---

# 31. Pattern binding

Pattern:

```ax
Some(x)
```

tạo local binding:

```text id="o3q1ae"
x
```

với ownership mode được suy ra từ pattern/context.

---

# 32. Match exhaustiveness

Đã frozen:

```text id="o5f3cv"
match
```

phải exhaustive trong safe code.

Compiler kiểm tra:

```text id="52gq3m"
all constructors covered
```

---

# 33. Match guards

```ax
match x {
    n if n > 0 => ...
    _ => ...
}
```

guard chỉ được evaluate sau khi pattern match.

Thứ tự:

```text id="q3e3nf"
pattern
↓
bindings
↓
guard
↓
body
```

---

# 34. Match guard side effects

Nếu guard có side effect:

```ax
n if check(n)
```

`check(n)` chỉ chạy khi pattern tương ứng match.

Không chạy speculative trên các arm khác.

---

# 35. `loop`

```ax
loop {
    work();
}
```

là control-flow expression có thể có:

```text id="e1cnwz"
never
```

nếu không có reachable `break`.

---

# 36. `break` có value

Axiom nên hỗ trợ:

```ax
let x = loop {
    if done() {
        break 42;
    }
};
```

type của loop:

```text id="5lkgqk"
i32
```

---

# 37. Loop type

Nếu:

```ax
loop {
    continue;
}
```

thì:

```text id="iw6v2p"
never
```

hoặc control-flow diverging expression.

Nếu có `break T`:

```text
loop → T
```

---

# 38. `while`

```ax
while condition {
    body
}
```

là control-flow construct.

Không có giá trị hữu ích:

```text id="j0z0um"
unit
```

trừ semantics tương lai nếu language mở rộng.

---

# 39. `for`

```ax
for x in collection {
    use(x);
}
```

surface syntax.

Semantic lowering có thể tương đương iterator protocol:

```text id="7l0pqq"
into_iter(collection)
↓
next()
↓
match
```

nhưng compiler phải preserve:

- ownership;
- drop;
- evaluation order;
- borrowing/view semantics.

---

# 40. `for` không bắt buộc heap iterator

Iterator abstraction có thể được monomorphize/inlined.

Không tạo:

```text id="9t9q67"
heap object
vtable
```

trừ khi API cụ thể yêu cầu.

---

# 41. `return`

```ax
return expr;
```

semantic:

```text id="f4a4ql"
evaluate expr
↓
cleanup active resources
↓
return
```

Cleanup không được bỏ qua.

---

# 42. Early return

```ax
fn foo() {
    let a = A();

    if fail() {
        return;
    }

    use(a);
}
```

Nếu return:

```text id="3fqy1a"
A::drop(a)
```

phải chạy trước khi function exits.

---

# 43. `?` operator

```ax
let x = foo()?;
```

semantic:

```text id="9wnj7u"
evaluate foo()
↓
if success:
    extract value
else:
    perform early return
```

`?` không phải exception.

---

# 44. `?` và Drop

Nếu `foo()` trả lỗi:

```text id="z0a2up"
all currently owned resources
```

phải cleanup đúng trước early return.

---

# 45. `panic`

```ax
panic("error");
```

là diverging control flow:

```text id="8oz3js"
never
```

Panic policy đã frozen:

```text
abort
unwind
custom
```

---

# 46. `panic` không phải Result

Axiom giữ rõ:

```text id="2a2z75"
Result<T,E>
→ recoverable / expected failure

panic
→ violated invariant / unrecoverable failure
```

Không tự động chuyển đổi.

---

# 47. `never`

Expression:

```ax
loop {}
```

hoặc:

```ax
panic(...)
```

có type:

```text id="6f67qt"
never
```

`never` có thể coerce vào context cần một type vì control flow không tiếp tục.

---

# 48. Unreachable

Sau:

```ax
return;
```

hoặc:

```ax
panic(...);
```

statements phía sau unreachable.

Compiler có thể cảnh báo hoặc reject tùy lint/profile, nhưng semantic analyzer phải biết:

```text id="u7em8q"
ControlFlow = Unreachable
```

---

# 49. Short-circuit `&&`

```ax
a && b
```

semantic:

```text id="ml0qmi"
evaluate a
↓
if false → false
else → evaluate b
```

`b` không được evaluate nếu `a == false`.

---

# 50. Short-circuit `||`

```ax
a || b
```

semantic:

```text id="v5m6mg"
evaluate a
↓
if true → true
else → evaluate b
```

---

# 51. `&` và `|` khác `&&` / `||`

Bitwise:

```text id="z7a3v5"
&
|
^
```

có thể evaluate cả hai operands.

Short-circuit:

```text
&&
||
```

là control flow.

---

# 52. Assignment expression

Khuyến nghị Axiom:

```text id="0v8h7d"
assignment is statement-oriented
```

Thay vì cho:

```ax
a = b = c;
```

tạo chuỗi expression có giá trị.

Điều này giảm ambiguity và accidental mutation.

Do đó:

```ax
x = 10;
```

là assignment statement.

---

# 53. Assignment không có value

Ví dụ:

```ax
let x = (y = 10);
```

không hợp lệ trong Core.

Điều này giúp phân biệt rõ:

```text id="3j1qck"
computation
```

và:

```text id="7h6d8c"
mutation
```

---

# 54. Prefix/postfix operators

Ví dụ:

```ax
-x
!x
```

có thể là trait operations.

Nhưng:

```text id="4i9zq8"
++x
x++
```

không cần đưa vào Core.

Khuyến nghị bỏ increment/decrement operators để tránh hidden mutation semantics.

---

# 55. Logical negation

```ax
!x
```

với `bool` là language/operator trait semantic.

Không có truthiness:

```ax
if 1 { ... } // invalid
```

Chỉ:

```text id="s2k7zq"
bool
```

được dùng làm condition.

---

# 56. Numeric overflow

Đã frozen:

Không có C-style signed integer overflow UB.

Các semantics:

```text id="j4n5yw"
checked
wrapping
saturating
```

phải explicit hoặc được API/operator semantics định nghĩa.

---

# 57. Floating-point

Compiler không được tùy ý biến:

```text id="y0m9h2"
f32
```

thành:

```text id="8ib9oq"
f64
```

hoặc thay đổi floating semantics chỉ để tối ưu.

Fast-math/relaxed FP phải là compilation configuration/explicit contract.

---

# 58. Evaluation order và ownership

Ví dụ:

```ax
foo(move(x), view(x))
```

Nếu first argument move `x`, second argument không còn hợp lệ.

Compiler phải reject nếu capability/ownership state không hợp lệ.

Không dựa vào runtime.

---

# 59. Evaluation order và mutability

Ví dụ:

```ax
foo(read(x), mutate(x))
```

nếu read capability còn sống qua mutation:

```text id="3qk6gk"
capability conflict
```

phải bị verifier phát hiện.

---

# 60. Evaluation order và views

```ax
let v = view(x);
foo(v, mut_view(x));
```

không hợp lệ nếu `v` vẫn live khi mutable access xảy ra.

Evaluation order không thể dùng để “lách” capability model.

---

# 61. Async `.await`

`await` là control-flow boundary.

```ax
let x = foo().await;
```

semantic:

```text id="n3n5k4"
evaluate foo()
↓
poll future
↓
if Pending:
    suspend
↓
resume
↓
obtain Ready(x)
```

---

# 62. Await không phải function call bình thường

Compiler phải biết:

```text id="h4d7ay"
SuspensionPointId
```

và kiểm tra state sống qua suspension.

---

# 63. View qua await

Nếu:

```ax
let v = view(x);
foo(v).await;
```

compiler phải reject nếu view không có execution/storage contract cho việc sống qua suspension.

Đây là async verifier rule đã frozen.

---

# 64. Comptime expression

Cùng expression semantics được dùng trong comptime:

```ax
comptime {
    let x = calculate();
}
```

nhưng effects bị giới hạn bởi comptime capability environment.

Ví dụ:

```text id="psu5xw"
ReadSource
ReadMetadata
```

được phép theo capability policy.

---

# 65. Unsafe expression

Unsafe không thay đổi evaluation order.

Ví dụ:

```ax
unsafe {
    *ptr
}
```

vẫn:

```text id="m73d8n"
evaluate ptr
↓
perform unsafe dereference
```

Unsafe chỉ thay đổi verification responsibility.

---

# 66. Foreign calls

```ax
extern fn c_func(...);

c_func(a(), b());
```

vẫn:

```text id="uw3gcv"
a()
→ b()
→ foreign call
```

Nhưng compiler áp dụng FFI effect contract bảo thủ.

---

# 67. Volatile

```text id="6u1jwp"
volatile_read
volatile_write
```

là observable machine effects.

Optimizer không được:

- eliminate;
- merge;
- reorder;

nếu vi phạm volatile semantics.

---

# 68. Atomic

Atomic operations có memory ordering riêng:

```text id="h7gr6x"
Relaxed
Acquire
Release
AcqRel
SeqCst
```

Evaluation order source-level vẫn deterministic.

Memory ordering là semantic synchronization layer riêng.

---

# 69. Compiler optimization boundary

Có hai thứ khác nhau:

```text id="q2f7k0"
Source evaluation order
```

và:

```text id="j5x1m7"
Machine instruction order
```

Compiler được reorder machine instructions nếu:

```text id="z2p4jb"
observable semantics
```

không thay đổi.

---

# 70. HIR representation

HIR nên biểu diễn expression semantic rõ ràng:

```text id="4p9fif"
Expr =
    Literal
    Name
    Unary
    Binary
    Call
    MethodCall
    Field
    Index
    Assign
    If
    Match
    Loop
    Break
    Return
    Block
    Await
    Cast
    Bitcast
    Unsafe
    Comptime
```

---

# 71. HIR không encode machine layout

Ví dụ:

```ax
x + y
```

HIR không biết:

```text
ADD eax, ebx
```

HIR chỉ biết:

```text
Binary(Add, x, y)
```

Machine selection xảy ra rất xa phía sau.

---

# 72. MIR lowering

Ví dụ:

```ax
let x = foo(a(), b());
```

có thể hạ thành:

```text
t0 = call a()
t1 = call b()
t2 = call foo(t0, t1)
x  = move t2
```

với cleanup/capability metadata đầy đủ.

---

# 73. Explicit sequencing trong MIR

MIR là nơi expression evaluation order trở nên explicit.

Điều này rất quan trọng cho:

- verifier;
- Drop;
- ownership;
- async;
- optimizer;
- debugging.

---

# 74. Expression effects

HIR/MIR nên có effect summary:

```text
Read
Write
Move
Drop
Allocate
Panic
Atomic
Volatile
IO
Foreign
Synchronize
```

Không nhất thiết expose toàn bộ effect system cho programmer.

Compiler tự suy ra.

---

# 75. Không cần source-level effect annotations

Axiom không cần bắt programmer viết:

```ax
fn foo() effects(IO, Alloc, Panic)
```

ở Core v0.1.

Compiler có thể derive effect summary.

Đây là đúng triết lý:

> **Compiler Complexity Is Not Language Complexity.**

---

# 76. Pure optimization

Nếu compiler chứng minh expression:

```text
x * 2 + 1
```

không có side effect:

```text id="up9p3u"
CSE
constant folding
vectorization
reassociation
```

có thể được áp dụng.

---

# 77. Reassociation

Ví dụ:

```text id="2n1k1x"
(a + b) + c
```

không mặc nhiên tương đương:

```text
a + (b + c)
```

với floating point.

Do đó reassociation phải tuân thủ type/FP semantic rules.

---

# 78. Integer algebra

Với integer không overflow UB, compiler chỉ được reassociate nếu semantics cho phép.

Ví dụ checked arithmetic:

```text id="a6n8xm"
a + b
```

có thể panic.

Do đó:

```text id="qv8j20"
(a + b) + c
```

không luôn tương đương:

```text id="7y70n0"
a + (b + c)
```

nếu overflow behavior observable.

---

# 79. Control-flow simplification

Compiler có thể biến:

```ax
if true {
    foo();
} else {
    bar();
}
```

thành:

```ax
foo();
```

vì branch condition compile-time known.

---

# 80. Nhưng semantics là nguồn chân lý

Tất cả optimization phải tuân:

```text id="9g1yjr"
Source Semantics
      ↓
HIR
      ↓
MIR
      ↓
Verified MIR
      ↓
Optimization
```

Không được định nghĩa semantics ngược lại từ optimizer.

---

# 81. Invariants

### `AEXPR-20`
Every expression has a deterministic semantic type.

### `AEXPR-21`
Expression semantics include observable effects.

### `AEXPR-22`
Evaluation order is deterministic.

### `AEXPR-23`
Ordinary subexpressions evaluate left-to-right.

### `AEXPR-24`
Function arguments evaluate left-to-right.

### `AEXPR-25`
Method receiver evaluates before method arguments.

### `AEXPR-26`
Compiler optimization cannot alter observable evaluation order.

### `AEXPR-27`
Expression evaluation never depends on hash-map iteration order.

### `AEXPR-28`
Assignment evaluates its RHS before performing the write.

### `AEXPR-29`
Assignment is not an ordinary value-producing expression in Core v0.1.

### `AEXPR-30`
Field access resolves to stable FieldId.

### `AEXPR-31`
Indexing evaluates container before index.

### `AEXPR-32`
Safe indexing cannot produce undefined behavior.

### `AEXPR-33`
Bounds checks may be eliminated only after proof.

### `AEXPR-34`
Temporary values have deterministic semantic destruction.

### `AEXPR-35`
Physical storage lifetime may differ from semantic lifetime.

### `AEXPR-36`
Drop order is deterministic.

### `AEXPR-37`
`if` evaluates only its selected branch.

### `AEXPR-38`
`match` evaluates its scrutinee exactly once.

### `AEXPR-39`
Only the selected match arm is evaluated.

### `AEXPR-40`
Match guards execute only after their pattern matches.

### `AEXPR-41`
Match must be exhaustive in safe Core.

### `AEXPR-42`
`loop` may produce a value through `break`.

### `AEXPR-43`
`break` transfers control without violating cleanup semantics.

### `AEXPR-44`
`return` evaluates its result before cleanup.

### `AEXPR-45`
Early return executes required cleanup.

### `AEXPR-46`
`?` is structured early return, not exception handling.

### `AEXPR-47`
`panic` has diverging `never` semantics.

### `AEXPR-48`
`&&` and `||` are short-circuit control-flow operators.

### `AEXPR-49`
Short-circuit operands are not eagerly evaluated.

### `AEXPR-50`
Bitwise operators are distinct from logical short-circuit operators.

### `AEXPR-51`
Conditions require `bool`; implicit truthiness is forbidden.

### `AEXPR-52`
Integer overflow semantics are defined, not C-style signed-overflow UB.

### `AEXPR-53`
Floating-point optimization must respect configured FP semantics.

### `AEXPR-54`
Unsafe does not alter evaluation-order semantics.

### `AEXPR-55`
Foreign calls preserve source evaluation order.

### `AEXPR-56`
Volatile operations retain their observable ordering semantics.

### `AEXPR-57`
Atomic operations preserve their memory-order semantics.

### `AEXPR-58`
Ownership verification applies to expression evaluation.

### `AEXPR-59`
Capability verification applies to expression evaluation.

### `AEXPR-60`
A live capability cannot be invalidated by expression reordering.

### `AEXPR-61`
Await is an explicit suspension boundary.

### `AEXPR-62`
Values and capabilities crossing await are verified.

### `AEXPR-63`
Comptime uses the same basic expression semantics under restricted capabilities.

### `AEXPR-64`
HIR preserves semantic expression structure.

### `AEXPR-65`
MIR makes relevant evaluation order explicit.

### `AEXPR-66`
Optimizer may reorder only when semantic effects permit it.

### `AEXPR-67`
Optimization cannot introduce observable side effects absent from source semantics.

### `AEXPR-68`
Optimization cannot remove required observable side effects.

### `AEXPR-69`
Semantic behavior does not depend on optimization level.

### `AEXPR-70`
Expression lowering is deterministic.

### `AEXPR-71`
Compiler diagnostics distinguish type errors from control-flow errors.

### `AEXPR-72`
Compiler recovery cannot emit final machine code from invalid expression semantics.

### `AEXPR-73`
Expression semantics remain independent of target machine representation.

### `AEXPR-74`
Equivalent clean and incremental compilation produces equivalent expression semantics.

### `AEXPR-75`
Verified MIR is the correctness boundary before expression optimization.

---

# Frontend semantic layer hiện tại

Sau BOOTSTRAP-132:

```text id="3y4x0w"
Source
  │
  ▼
Lexer
  │
  ▼
CST
  │
  ▼
AST
  │
  ├── Declaration Collection
  │
  ├── Module / Scope
  │
  └── Name Resolution
          │
          ▼
      Typed HIR
          │
          ├── Type System
          ├── Trait Solver
          ├── Const Evaluation
          ├── Comptime
          └── Expression Semantics
                    │
                    ▼
                   MIR
                    │
                    ▼
               Verification
```

Đây là một mốc quan trọng: **type, trait, name và expression semantics hiện đã tách thành các subsystem khá sạch**, giúp compiler có thể mạnh hơn mà syntax của Axiom vẫn tương đối đơn giản.

---

# BOOTSTRAP-133 — Pattern Matching, Destructuring & Exhaustiveness

Task kế tiếp sẽ khóa riêng **pattern system**, vì pattern là điểm giao giữa:

```text
enum
struct
tuple
array
Option
Result
ownership
partial move
match
```

và đặc biệt phải giải quyết:

- literal patterns;
- variable binding;
- `_`;
- tuple/struct patterns;
- enum patterns;
- nested patterns;
- `Some(x)` / `Err(e)`;
- ranges;
- OR-pattern;
- guards;
- `ref`-like semantics nhưng **không đưa borrow syntax vào source**;
- move/copy/view semantics trong destructuring;
- partial move;
- match ergonomics;
- exhaustiveness;
- unreachable arms;
- usefulness algorithm;
- pattern lowering xuống MIR;
- interaction với Drop;
- interaction với `view` / `mut_view`;
- diagnostics cho pattern;
- compile-time pattern checking.

**BOOTSTRAP-133 là task tiếp theo.**