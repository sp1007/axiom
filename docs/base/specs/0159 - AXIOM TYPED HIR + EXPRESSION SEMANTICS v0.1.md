# AXIOM TYPED HIR + EXPRESSION SEMANTICS v0.1

Đây là bước **đóng frontend semantic**. Sau phần này, Axiom sẽ có:

```text id="9r5k2m"
Source
 ↓
Lexer
 ↓
Parser
 ↓
AST
 ↓
Resolver
 ↓
HIR
 ↓
Type Checker
 ↓
Trait Solver
 ↓
Method Resolution
 ↓
Typed HIR
```

và Typed HIR sẽ là input chính cho **Ownership + Capability + Drop → MIR**.

Mục tiêu ở đây là: **mọi expression phải có nghĩa xác định, type xác định và không còn ambiguity**.

---

# 1. Typed HIR là gì?

AST:

```axiom id="7f3k2q"
x.foo(a + b)
```

chỉ nói programmer viết gì.

Typed HIR phải biết:

```text id="x8m4q1"
Call
├── callee = FunctionId(42)
├── receiver = LocalId(7)
├── arg0
│   └── Binary(Add)
│       ├── LocalRef(a) : i32
│       └── LocalRef(b) : i32
│       └── type = i32
└── result = Text
```

Không còn:

```text
"foo"
"a"
"b"
```

là những string cần lookup lại.

---

# 2. Typed HIR node

Mỗi expression:

```text id="p6v2m8"
HirExpr {
    id: ExprId
    kind: HirExprKind
    type: TypeId
    span: Span
}
```

Ví dụ:

```text id="c4n7x1"
ExprId(42)
kind = LocalRef(LocalId(7))
type = TypeId(i32)
```

---

# 3. Không dùng type trực tiếp trong AST

AST:

```text id="q9m3x7"
NameExpr("x")
```

Typed HIR:

```text id="z2v8k4"
LocalRef(LocalId(7), TypeId(12))
```

Điều này cho phép toàn bộ backend bỏ qua source names.

---

# 4. Expression classification

Typed HIR chia expression thành:

```text id="k5x8q2"
Literal
LocalRef
GlobalRef
TypeRef
Tuple
Array
Struct
Enum
Field
Index
Call
MethodCall
Unary
Binary
Cast
Range
If
Match
Block
Closure
Await
Try
Assignment
```

Sau đó một số node được normalize trước MIR.

---

# 5. Literal

```axiom id="q8m3x1"
42
```

Typed HIR:

```text id="a7v2n9"
Literal {
    value = 42
    type = i32
}
```

Nếu:

```axiom id="y3k8m2"
let x: i64 = 42
```

thì:

```text id="m5q1x7"
Literal {
    value = 42
    type = i64
}
```

Không có runtime cast.

---

# 6. Bool

```axiom id="n8v2q4"
true
```

→ `bool`.

Không có truthiness.

Do đó:

```axiom id="g4x7m1"
if 1 {
}
```

→ compile error.

---

# 7. Text và Bytes

```axiom id="h3q8m2"
"hello"
```

→ `Text`.

```axiom id="f7x2n5"
b"hello"
```

→ `Bytes`.

Không implicit:

```text id="c9m4v8"
Text ↔ Bytes
```

---

# 8. Local reference

```axiom id="p5x7m3"
x
```

HIR:

```text id="y8q2m6"
LocalRef(LocalId(3))
```

type đã gắn:

```text id="j4m8x1"
type = TypeId(...)
```

---

# 9. Global reference

Ví dụ:

```axiom id="x2m7q4"
PI
```

HIR:

```text id="n8v3m5"
GlobalRef(ConstId(10))
```

hoặc:

```text id="q1x6k8"
StaticRef(StaticId(10))
```

Không dùng chung với LocalRef.

---

# 10. Assignment

```axiom id="m8x4q1"
x = y
```

Typed HIR:

```text id="f3n7k2"
Assignment {
    target = Place(LocalId(x))
    value = LocalRef(y)
}
```

Result type:

```text id="z6q2m8"
unit
```

---

# 11. Assignment không phải expression value

Axiom không cho:

```axiom id="j7x3m2"
let y = x = 10
```

vì assignment trả `unit`.

Nếu muốn:

```axiom id="k4m8q2"
x = 10
let y = x
```

---

# 12. Immutable assignment

```axiom id="v8x2m5"
let x = 10
x = 20
```

Type checker phát hiện binding immutable.

Diagnostic:

```text id="g5m9q1"
AX_TYPE_0012
cannot assign to immutable binding
```

Ownership verifier không cần xử lý lỗi này.

---

# 13. `var`

```axiom id="q2m7x8"
var x = 10
x = 20
```

Binding metadata:

```text id="a8x3m5"
mutability = Mutable
```

Type vẫn:

```text id="c7m2q4"
i32
```

---

# 14. Field access

```axiom id="r4x8m2"
user.name
```

Resolver/type checker:

```text id="j6q3n8"
User
 └── field name → FieldId(7)
```

HIR:

```text id="p5m9x2"
Field {
    base = LocalRef(user)
    field = FieldId(7)
    type = Text
}
```

Không lookup `"name"` nữa.

---

# 15. Field access là Place-capable

Đây là chuẩn bị cho ownership.

```axiom id="w3m7q1"
user.name
```

có thể được sử dụng làm:

```text id="x8q2m4"
READ
MOVE
WRITE
VIEW
```

tùy context.

Do đó HIR cần distinction:

```text id="e5m8x2"
Value expression
Place expression
```

---

# 16. Place

Axiom nên có semantic concept:

```text id="n4q7x8"
Place
```

không nhất thiết expose syntax.

Các expression có thể tạo Place:

```text id="d2m8q1"
Local
Field
Index
Deref
```

Ownership/MIR sẽ dùng Place.

---

# 17. Index

```axiom id="k7x3m9"
a[i]
```

Typed HIR:

```text id="r8m2q5"
Index {
    base = ...
    index = ...
    element_type = T
}
```

Type của expression là `T`.

---

# 18. Bounds check

Type checker không quyết định runtime bounds.

MIR lowering tạo semantic operation:

```text id="f3q8m1"
BOUNDS_CHECK
```

Nếu compiler chứng minh index hợp lệ, optimizer có thể loại bỏ.

Nếu không:

```text id="x7m2n5"
runtime check
```

---

# 19. Index assignment

```axiom id="g8q2m4"
a[i] = x
```

target là Place:

```text id="m5x7q2"
IndexPlace
```

sau đó ownership/capability checker kiểm tra mutation.

---

# 20. Struct literal

```axiom id="z4m8q1"
User {
    name: "A",
    age: 20
}
```

HIR:

```text id="v7q2m9"
StructLiteral {
    type = User
    fields:
        FieldId(name) → Text
        FieldId(age)  → i32
}
```

Field order không quyết định semantic identity.

---

# 21. Missing field

```axiom id="p3m8x7"
User {
    name: "A"
}
```

nếu `age` bắt buộc:

```text id="c9q4m2"
AX_TYPE_0015
missing field `age`
```

Không implicit zero-init.

---

# 22. Extra field

```axiom id="y8m3q1"
User {
    name: "A",
    age: 20,
    unknown: true
}
```

→ compile error.

---

# 23. Enum construction

```axiom id="x5q8m2"
Message.Text("hello")
```

HIR:

```text id="j7m4q9"
EnumConstruct {
    enum = Message
    variant = Text
    payload = Text
}
```

---

# 24. Pattern matching

```axiom id="q2x7m8"
match message {
    Message.Quit => ...
    Message.Text(x) => ...
}
```

Typed HIR phải biết:

```text id="m8q3x1"
variant = VariantId(Quit)
variant = VariantId(Text)
x = PatternBinding(LocalId(...))
```

Không còn string-based variant resolution.

---

# 25. Pattern binding

Ví dụ:

```axiom id="b7x2m8"
Message.Text(x)
```

`x` là một local binding mới.

Scope:

```text id="r4m9q1"
MatchArmScope
```

Chỉ tồn tại trong arm.

---

# 26. Match arm scope

```axiom id="v8m3x2"
match value {
    Some(x) => x,
    None => 0,
}
```

`x` chỉ visible ở:

```text id="f2q7m8"
Some(x) => x
```

Không tồn tại trong arm khác.

---

# 27. If expression

```axiom id="g3m8x2"
if condition {
    a
} else {
    b
}
```

Type checker:

```text id="n7q2m5"
condition : bool
type(a) == type(b)
```

result:

```text id="x4m8q1"
type(if) = type(a)
```

---

# 28. If không có else

```axiom id="p8x3m6"
if condition {
    foo()
}
```

chỉ hợp lệ nếu expression có type:

```text id="j4q7m2"
unit
```

Ví dụ:

```axiom id="w6m2x8"
if condition {
    42
}
```

→ lỗi vì expression có thể không produce value.

Điều này giúp Axiom tránh những quy tắc implicit khó hiểu.

---

# 29. Block expression

```axiom id="a7m4x8"
{
    let x = 10
    x + 1
}
```

type của block = type final expression.

Nếu block kết thúc bằng declaration/statement:

```text id="q2x8m3"
unit
```

---

# 30. `return`

```axiom id="x8m2q4"
return value
```

HIR:

```text id="f7m3x9"
Return {
    value
}
```

Không phải ordinary value expression.

Control flow lowering xử lý sau.

---

# 31. `break`

Axiom đã khóa:

> `break` không có value.

Do đó:

```axiom id="m5q8x2"
let x = while cond {
    break
}
```

không được suy ra value từ `break`.

`while` có type:

```text id="r7x3m1"
unit
```

---

# 32. `continue`

Tương tự:

```text id="p4m8x2"
continue
```

là control-flow transfer, không phải value.

---

# 33. While

```axiom id="q7x2m8"
while condition {
    work()
}
```

yêu cầu:

```text id="n3m6x1"
condition : bool
body : unit-compatible
```

result:

```text id="v8q2m5"
unit
```

---

# 34. For

```axiom id="x4m7q2"
for x in items {
    use(x)
}
```

Typed HIR vẫn giữ:

```text id="c8m2n7"
For {
    pattern
    iterable
    body
}
```

nhưng đã xác định:

```text id="j5q8m1"
iterable type
iterator type
item type
```

Trait solver xác định các relation cần thiết.

---

# 35. Range

```axiom id="r3m8x2"
0..10
```

không phải magic array.

HIR:

```text id="f7q2m9"
Range {
    start = 0
    end = 10
    inclusive = false
}
```

Type được xác định bởi endpoint + expected context.

---

# 36. Call

```axiom id="y8m3q1"
foo(a, b)
```

HIR:

```text id="k2x7m5"
Call {
    callee = FunctionId(42)
    args = [...]
    result_type = ...
}
```

Function signature đã biết.

---

# 37. Argument checking

Ví dụ:

```axiom id="p6m2x8"
fn foo(a: i32, b: f32) {}
```

call:

```axiom id="v3q8m1"
foo(1, 2)
```

`1` → `i32`.

Nhưng `2` không tự convert thành `f32` nếu context đã yêu cầu `f32`? Đây là điểm cần phân biệt.

Numeric literal **có thể được infer theo expected parameter type**, nên:

```text id="g7m4x2"
2 → f32
```

là hợp lệ.

Đây vẫn là literal inference, không phải numeric conversion.

---

# 38. Variable argument không tự convert

```axiom id="q8m3x1"
var x: i32 = 2
foo(x)
```

nếu `foo` yêu cầu `f32`:

→ lỗi.

Phải:

```axiom id="m4x7q2"
foo(x as f32)
```

---

# 39. Method call

AST:

```text id="x7m2q8"
v.length()
```

Typed HIR sau method resolution:

```text id="n3q8m5"
MethodCall {
    resolved_function = FunctionId(77)
    receiver = ...
    args = [...]
    type = f32
}
```

Có thể normalize tiếp thành:

```text id="j5m8x2"
Call(FunctionId(77), [receiver])
```

Tôi khuyến nghị **normalize trước MIR**, nhưng giữ `MethodCall` metadata để diagnostics/debug.

---

# 40. Unary operators

```axiom id="q2m8x3"
-x
!x
~x
```

Type checker kiểm tra operator semantics.

Ví dụ:

```text id="x8m4q1"
!x
```

yêu cầu `x : bool`.

Không:

```axiom id="v5q7m2"
!42
```

---

# 41. Binary operators

```axiom id="m3x8q2"
a + b
```

type checking:

```text id="p7m2x9"
lhs type
rhs type
operator semantics
result type
```

Không có automatic numeric promotion.

---

# 42. Arithmetic overflow

Đã freeze:

```text id="g4x8m1"
+  -  *
```

checked.

```text id="q2m7x5"
+% -% *%
```

wrapping.

```text id="v8x3m2"
+| -| *|
```

saturating.

Typed HIR phải giữ chính xác operator kind:

```text id="f5m8q1"
BinaryOp::CheckedAdd
BinaryOp::WrappingAdd
BinaryOp::SaturatingAdd
```

Không normalize tất cả thành `Add`.

---

# 43. Division

`/` có semantic failure nếu divisor bằng zero.

Safe semantics:

```text id="m7q2x8"
division by zero → panic/trap
```

Optimizer chỉ được bỏ check nếu chứng minh divisor khác zero.

---

# 44. Comparison

```axiom id="x8m3q2"
a < b
```

result:

```text id="k5m7q1"
bool
```

Các type cần comparable theo language/trait semantics.

Không tạo một universal `Object.compare`.

---

# 45. Equality

```axiom id="p2m8x4"
a == b
```

không có universal runtime reflection.

Compiler resolve equality semantics qua built-in/trait mechanism được định nghĩa.

---

# 46. Cast

```axiom id="r7m3x8"
x as i64
```

Typed HIR:

```text id="q4m8x2"
Cast {
    source = ...
    target = i64
    cast_kind = Numeric
}
```

Các cast categories nên explicit:

```text id="x5m2q7"
NumericCast
PointerCast
BitCast
```

`bit_cast` là node riêng.

---

# 47. `bit_cast`

```axiom id="j8m3x1"
bit_cast<u32>(x)
```

không phải numeric conversion.

Nó yêu cầu:

```text id="v7q2m5"
same size
valid representation requirements
```

và có semantic rules riêng.

---

# 48. Không có unrestricted transmute

Không có:

```text id="g2x8m4"
transmute<T, U>(x)
```

với arbitrary types.

Điều này bảo vệ type system khỏi việc biến mọi abstraction boundary thành loophole.

---

# 49. `?`

Ví dụ:

```axiom id="p8m2x7"
let x = foo()?
```

Typed HIR:

```text id="x4q7m1"
Try {
    operand = Call(...)
    success_type = T
    error_type = E
}
```

Type checker biết outer function phải compatible:

```text id="m6x3q8"
Result<T, E_outer>
```

hoặc Option tương ứng.

---

# 50. `?` không phải exception

MIR lowering:

```text id="k7m2x5"
call foo()
    ↓
inspect discriminant
    ↓
success → continue
error   → cleanup + return
```

Không có hidden stack unwinding.

---

# 51. `?` và Drop

Ví dụ:

```axiom id="r3m8q2"
let resource = acquire()?
```

nếu sau đó một `?` fail:

```text id="x7q2m5"
resource
```

phải được cleanup trước khi return.

Nhưng Typed HIR chỉ biểu diễn control flow semantics.

Drop elaboration làm việc sau.

---

# 52. `await`

```axiom id="m8x3q2"
fetch().await
```

Typed HIR:

```text id="q7m2n5"
Await {
    future = Call(...)
    output_type = T
}
```

Type checker kiểm tra Future relation.

---

# 53. View không được qua await

Axiom đã khóa:

```text id="v4m8q2"
view<T>
mut_view<T>
```

không được sống qua `.await`.

Điều này không nhất thiết báo lỗi ở type checking.

Ownership/capability analysis sẽ kiểm tra:

```text id="x8q3m7"
capability live across suspension?
```

Nếu có:

```text id="f5m2q9"
error
```

---

# 54. Owned value được qua await

```axiom id="j7m3x2"
var buffer = make_buffer()

await_work().await

use(buffer)
```

có thể hợp lệ nếu ownership/state-machine semantics cho phép.

Compiler có thể biến `buffer` thành field của async state machine.

---

# 55. Closure

```axiom id="q8m2x4"
|x| x + 1
```

Typed HIR:

```text id="m3x7q1"
Closure {
    ClosureId
    params
    body
    captures
    function_type
}
```

---

# 56. Closure capture

Compiler xác định:

```text id="v7q2m8"
CaptureMode
├── Read
├── Mutable
└── Move
```

Nhưng đây là ownership analysis.

Typed HIR có thể lưu **capture candidates**, sau ownership verifier mới freeze capture mode.

---

# 57. `move` closure

```axiom id="x4m8q2"
move || use(data)
```

Typed HIR ghi:

```text id="j7q3m1"
explicit_move_capture = true
```

Ownership verifier buộc capture bằng ownership transfer.

---

# 58. Closure type identity

Hai closure:

```axiom id="m8q2x4"
|| 1
|| 1
```

không mặc nhiên cùng type.

Mỗi closure expression có anonymous identity.

Nếu cần abstraction:

```text id="q7m3x8"
fn(...) -> ...
```

hoặc trait/function interface.

---

# 59. `async fn`

```axiom id="p2x8m4"
async fn fetch() -> Data
```

Type-level semantic:

```text id="f7m3q2"
Future<Output = Data>
```

Nhưng Future cụ thể là anonymous compiler-generated state-machine type.

Không cần expose type name.

---

# 60. `panic`

```axiom id="x8m2q3"
panic("bad")
```

semantic result:

```text id="m4q7x1"
never
```

Panic strategy:

```text id="q3m8x2"
abort
```

hoặc:

```text id="v7x2m5"
unwind
```

được xác định ở compilation profile.

---

# 61. `unreachable`

```axiom id="j8m3q2"
unreachable()
```

→ `never`.

Optimizer có thể dùng:

```text id="p5q7x1"
UNREACHABLE
```

ở MIR.

---

# 62. `assert`

```axiom id="m2x8q4"
assert(condition)
```

type requirement:

```text id="g7m3q2"
condition : bool
```

failure:

```text id="q8x2m5"
panic
```

`debug_assert` có semantics profile-dependent nhưng không được dùng làm safety proof.

---

# 63. Type checking sequence

Một function được check:

```text id="r4m8x2"
1. Create local environment
2. Bind parameters
3. Check body
4. Generate constraints
5. Solve local inference
6. Resolve trait obligations
7. Resolve methods
8. Normalize associated types
9. Verify return type
10. Produce Typed HIR
```

---

# 64. Typed HIR phải immutable

Sau khi:

```text id="x7m3q2"
Typed HIR
```

đã hoàn thành, các phase sau không được sửa semantic type của node.

Nếu cần transform:

```text id="q8m2x5"
Typed HIR
 ↓
MIR
```

tạo representation mới.

Không mutate ngược Typed HIR.

---

# 65. Vì sao điều này quan trọng?

Nếu ownership checker có thể thay đổi type:

```text id="m3x7q8"
type checker
↔ ownership
↔ trait solver
↔ HIR mutation
```

compiler trở thành một dependency cycle rất khó debug.

Axiom nên:

```text id="v8q2m1"
Type facts → immutable
Ownership facts → immutable
Capability facts → immutable
```

sau khi phase hoàn thành.

---

# 66. Typed HIR invariant

```text id="p5m8x2"
ATHIR-20
Every typed expression has a canonical TypeId.

ATHIR-21
Every resolved name reference uses semantic identity.

ATHIR-22
Typed HIR contains no unresolved ordinary identifier references.

ATHIR-23
Typed HIR contains source spans for all diagnostics-relevant nodes.

ATHIR-24
Assignment has unit result type.

ATHIR-25
Condition expressions require bool.

ATHIR-26
If branches have compatible result types.

ATHIR-27
While and break have no value semantics.

ATHIR-28
Match arms have compatible result types.

ATHIR-29
Function calls reference resolved FunctionIds.

ATHIR-30
Method calls reference resolved method candidates after method resolution.

ATHIR-31
Field access references FieldIds.

ATHIR-32
Enum construction references VariantIds.

ATHIR-33
Numeric literals use deterministic contextual inference.

ATHIR-34
Variables are not implicitly numerically converted.

ATHIR-35
Checked, wrapping and saturating arithmetic remain semantically distinct.

ATHIR-36
Cast semantics are explicit.

ATHIR-37
bit_cast is distinct from semantic conversion.

ATHIR-38
Try expressions preserve Result/Option semantics.

ATHIR-39
Await expressions preserve Future semantics.

ATHIR-40
Typed HIR does not perform ownership verification.

ATHIR-41
Typed HIR does not perform capability verification.

ATHIR-42
Typed HIR does not perform physical storage allocation.

ATHIR-43
Typed HIR is immutable after semantic completion.
```

---

# 67. Expression semantic invariants

```text id="q8m3x2"
AEXPR-20
Every expression has exactly one semantic type.

AEXPR-21
Every expression has deterministic evaluation semantics.

AEXPR-22
Evaluation order is deterministic.

AEXPR-23
Implicit conversions are limited to explicitly specified coercions.

AEXPR-24
Runtime values do not participate in static name resolution.

AEXPR-25
Runtime values do not participate in static type identity.

AEXPR-26
Storage placement does not affect expression type.

AEXPR-27
Optimization does not alter expression semantics.

AEXPR-28
Control-flow expressions preserve their declared result semantics.

AEXPR-29
Place expressions preserve their identity for later ownership analysis.

AEXPR-30
Value expressions do not implicitly create persistent capabilities.
```

---

# 68. Một ví dụ xuyên suốt

Source:

```axiom id="j7m3x8"
fn sum(a: i32, b: i32) -> i32 {
    let x = a + b

    if x > 0 {
        x
    } else {
        0
    }
}
```

Resolver:

```text id="q2m8x4"
sum → FunctionId(1)
a   → LocalId(1)
b   → LocalId(2)
x   → LocalId(3)
```

Type checker:

```text id="v8x3m2"
a : i32
b : i32

a + b : i32

x : i32

x > 0 : bool

then : i32
else : i32

if : i32

return : i32
```

Typed HIR:

```text id="m4q7x1"
Function sum : fn(i32, i32) -> i32

Body
├── Binding x : i32
│   └── CheckedAdd
│       ├── LocalRef(a) : i32
│       └── LocalRef(b) : i32
│
└── If : i32
    ├── GreaterThan : bool
    │   ├── LocalRef(x) : i32
    │   └── Literal(0) : i32
    │
    ├── LocalRef(x) : i32
    └── Literal(0) : i32
```

Đây là input rất sạch cho MIR.

---

# 69. Frontend semantic freeze

Đến đây frontend đã đạt:

```text id="x8m2q4"
LEXICAL
   ✓

SYNTAX
   ✓

NAME RESOLUTION
   ✓

HIR
   ✓

TYPE SYSTEM
   ✓

TRAITS
   ✓

METHOD RESOLUTION
   ✓

TYPED HIR
   ✓
```

Tiếp theo chúng ta mới bước vào phần đặc biệt của Axiom:

# **OWNERSHIP + CAPABILITY ANALYZER v0.1**

Đây sẽ không phải Rust Borrow Checker.

Kiến trúc nên là:

```text id="q7m3x8"
Typed HIR
     │
     ▼
Ownership State Analysis
     │
     ▼
Capability / Region Analysis
     │
     ▼
Move Analysis
     │
     ▼
Drop Analysis
     │
     ▼
Escape Analysis
     │
     ▼
Concurrency / Send / Share Checks
     │
     ▼
MIR
```

Điểm quan trọng nhất cần giữ: **programmer không viết lifetime, không viết borrow annotation, không viết ownership annotation**. Compiler tự dựng ownership state và capability graph từ Typed HIR, rồi chỉ báo lỗi khi chương trình thực sự vi phạm semantic rule.