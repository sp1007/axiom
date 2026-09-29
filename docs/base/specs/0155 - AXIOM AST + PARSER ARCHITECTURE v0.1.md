# AXIOM AST + PARSER ARCHITECTURE v0.1

Đây là phần cần khóa ngay sau Lexer. Tôi đề xuất **không viết một grammar khổng lồ rồi mới code parser**. Ta định nghĩa AST, precedence và các điểm ambiguity trước; sau đó parser có thể triển khai theo vertical slice.

---

# 1. Nguyên tắc AST

AST của Axiom phải nằm giữa:

```text
Source syntax
      ↓
    AST
      ↓
    HIR
      ↓
Typed HIR
```

AST giữ:

- cấu trúc cú pháp
- source spans
- syntax cần cho diagnostics
- attributes
- identifier spelling
- literal spelling

AST **không giữ semantic resolution**.

Ví dụ:

```axiom
foo(x)
```

AST:

```text
Call
├── callee: Name("foo")
└── args
    └── Name("x")
```

chưa được phép biến `foo` thành `FunctionId`.

---

# 2. HIR mới chứa semantic identity

Sau resolver:

```text
Name("foo")
```

→

```text
SymbolId(42)
```

Do đó:

```text
AST = syntax
HIR = resolved semantic structure
```

Đây là boundary rất quan trọng.

---

# 3. AST node identity

Mỗi node có:

```text
AstId
```

Ví dụ:

```text
ExprId
StmtId
TypeSyntaxId
PatternId
ItemId
```

Không dùng pointer làm identity.

Mỗi node cũng giữ:

```text
Span
```

Ví dụ:

```text
Expr {
    id: ExprId
    kind: ExprKind
    span: Span
}
```

---

# 4. AST ownership

AST có thể dùng arena:

```text
AstArena {
    items
    expressions
    statements
    patterns
    types
}
```

Node tham chiếu nhau bằng ID:

```text
ExprId
StmtId
PatternId
TypeSyntaxId
```

Không dùng:

```text
Box<Expr>
Box<Expr>
Box<Expr>
```

làm semantic ownership model.

---

# 5. Top-level grammar

Grammar khái quát:

```text
CompilationUnit
    := ModuleDecl? Item*
```

Item:

```text
Item
    := Function
     | Struct
     | Enum
     | Trait
     | Impl
     | TypeAlias
     | Const
     | Static
     | Module
     | Import
```

---

# 6. Module

```axiom
module math.vector
```

AST:

```text
ModuleDecl {
    path: [Name]
    span
}
```

Không tạo module runtime.

Resolver mới biến:

```text
math.vector
```

thành:

```text
ModuleId
```

---

# 7. Import

```axiom
import math.vector
import math.vector { Vector, dot }
import graphics.opengl as gl
```

AST:

```text
ImportDecl {
    path
    items?
    alias?
}
```

Re-export:

```axiom
pub import graphics.opengl { Buffer }
```

AST giữ:

```text
visibility = Pub
```

---

# 8. Attributes

Ví dụ:

```axiom
@repr(C)
@align(64)
@export("foo")
@kernel
fn foo() {}
```

AST:

```text
Attribute {
    name: Name
    arguments: [AttributeArg]
    span
}
```

Không tạo AST riêng:

```text
ReprCAttribute
KernelAttribute
ExportAttribute
```

Các schema được resolve sau.

---

# 9. Visibility

```text
Visibility
    Private
    Internal
    Public
```

Syntax:

```axiom
pub fn foo() {}
internal fn bar() {}
fn baz() {}
```

AST giữ visibility.

---

# 10. Function AST

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

Conceptual:

```text
Function {
    id
    attributes
    visibility
    name
    generics
    params
    return_type?
    body
}
```

Parameter:

```text
Param {
    name
    type
    span
}
```

Không có:

```text
in
out
borrow
ref
mut_ref
```

Axiom dùng semantic type:

```text
T
view<T>
mut_view<T>
```

---

# 11. Function receiver

Method syntax:

```axiom
fn length(self: view<Vec>) -> usize
```

AST vẫn chỉ là function bình thường:

```text
Param {
    name = self
    type = view<Vec>
}
```

Resolver/impl checker mới xác định:

> Đây là inherent/trait method.

Điều này giữ một semantic principle rất đẹp:

> **Method không phải một loại function thứ hai.**

---

# 12. Struct AST

```axiom
struct Vec2 {
    x: f32
    y: f32
}
```

```text
StructDecl {
    name
    generics
    fields
    attributes
}
```

Field:

```text
Field {
    name
    type
    visibility
}
```

---

# 13. Tuple struct

Cho phép:

```axiom
struct UserId(u64)
```

AST:

```text
StructDecl {
    kind = Tuple
    fields = [
        Field(anonymous, u64)
    ]
}
```

Không cần syntax riêng trong semantic model.

---

# 14. Unit struct

```axiom
struct Marker
```

→ zero-field struct.

Đây là ZST nếu layout phù hợp.

---

# 15. Enum AST

```axiom
enum Message {
    Quit,
    Text(Text),
    Move { x: i32, y: i32 },
}
```

```text
EnumDecl {
    name
    generics
    variants
}
```

Variant:

```text
Variant {
    name
    kind
}
```

kind:

```text
Unit
Tuple([TypeSyntaxId])
Struct([Field])
```

---

# 16. Trait AST

```axiom
trait Display {
    fn display(self: view<Self>) -> Text
}
```

```text
TraitDecl {
    name
    generics
    supertraits
    associated_types
    items
}
```

Trait method có thể:

- declaration only
- default body

---

# 17. Impl AST

```axiom
impl Display for User {
    ...
}
```

AST:

```text
ImplDecl {
    generics
    trait_type?
    self_type
    items
}
```

Hai dạng:

```axiom
impl Vec2 {
}
```

và:

```axiom
impl Display for Vec2 {
}
```

Không phân biệt bằng hai AST node.

`trait_type == None` nghĩa inherent impl.

---

# 18. Type syntax AST

Đây là phần rất quan trọng.

```text
TypeSyntax
├── Name
├── Tuple
├── Array
├── Function
├── View
├── MutView
├── RawPointer
├── DynTrait
├── ImplTrait
└── AppliedGeneric
```

Ví dụ:

```axiom
view<Vec<i32>>
```

AST:

```text
View(
    AppliedGeneric(
        Vec,
        [i32]
    )
)
```

Resolver/type checker sau đó mới tạo:

```text
TypeId
```

---

# 19. Generic syntax

```axiom
fn max<T: Ord>(a: T, b: T) -> T
```

AST:

```text
GenericParam {
    name = T
    bounds = [Ord]
}
```

Type syntax:

```text
T
```

chỉ là:

```text
Name("T")
```

Resolver xác định nó là `GenericParamId`.

---

# 20. `where`

```axiom
fn foo<T, U>(x: T)
where
    T: Display + Send,
    U: Clone
{
}
```

AST giữ:

```text
WhereClause {
    predicates
}
```

Không normalize constraints trong parser.

Trait solver làm việc đó sau.

---

# 21. Expressions

Đây là trung tâm parser.

Đề xuất:

```text
Expr
├── Literal
├── Name
├── Self
├── Tuple
├── Array
├── StructLiteral
├── Call
├── MethodCall
├── Field
├── Index
├── Unary
├── Binary
├── Cast
├── Range
├── If
├── Match
├── Block
├── Closure
├── Await
├── Try
├── Assignment
└── Parenthesized
```

---

# 22. Literal

```axiom
42
3.14
true
"hello"
b"bytes"
```

AST giữ raw literal:

```text
Literal {
    kind
    span
}
```

Không parse integer value thành machine integer tại AST stage.

---

# 23. Name expression

```axiom
x
foo
Vector
```

AST:

```text
NameExpr {
    name: StringId
    span
}
```

Resolver biến thành semantic reference.

---

# 24. `self`

```axiom
self
```

có AST node riêng:

```text
SelfExpr
```

hoặc `NameExpr("self")`.

Tôi khuyến nghị **special AST node** để diagnostics và method semantics rõ hơn.

---

# 25. Tuple

```axiom
(a, b)
```

AST:

```text
TupleExpr {
    elements: [ExprId]
}
```

Unit:

```axiom
()
```

→ empty tuple.

---

# 26. Array

```axiom
[1, 2, 3]
```

AST:

```text
ArrayExpr {
    elements
}
```

Repeated array:

```axiom
[0; 1024]
```

AST:

```text
ArrayRepeatExpr {
    value
    count
}
```

---

# 27. Struct literal

```axiom
Vec2 {
    x: 10.0,
    y: 20.0,
}
```

AST:

```text
StructLiteral {
    type_name
    fields
}
```

Field:

```text
FieldInit {
    name
    value
}
```

---

# 28. Field access

```axiom
v.x
```

AST:

```text
FieldExpr {
    base
    field_name
}
```

Không resolve field tại parser.

---

# 29. Tuple field

```axiom
p.0
```

Lexer:

```text
DOT
INT_LITERAL(0)
```

Parser nhận pattern đặc biệt:

```text
TupleFieldExpr {
    base
    index
}
```

Không coi `.0` là float.

---

# 30. Call

```axiom
add(a, b)
```

AST:

```text
CallExpr {
    callee
    args
}
```

Method:

```axiom
v.length()
```

AST có thể là:

```text
MethodCallExpr {
    receiver
    method_name
    args
}
```

hoặc normalize sớm thành Call.

Tôi khuyến nghị **giữ MethodCall trong AST**, bởi diagnostics cần biết source syntax.

HIR có thể normalize thành ordinary function call.

---

# 31. Method semantics

Ví dụ:

```axiom
v.length()
```

AST:

```text
MethodCall(v, length, [])
```

HIR:

```text
Call(
    FunctionId(length),
    [v]
)
```

Nếu trait method:

```text
Call(
    TraitMethodId(...),
    [v]
)
```

Nếu dynamic:

```text
DynamicCall(...)
```

Đây là abstraction boundary rất sạch.

---

# 32. Index

```axiom
a[i]
```

AST:

```text
IndexExpr {
    base
    index
}
```

Range:

```axiom
a[1..4]
```

index expression chính là:

```text
RangeExpr
```

---

# 33. Unary precedence

Unary:

```text
-x
!x
~x
```

AST:

```text
UnaryExpr {
    op
    operand
}
```

Raw pointer syntax:

```text
*ptr
```

có thể là dereference expression.

Semantic safety được type/unsafe checker xử lý sau.

---

# 34. Binary operators

AST:

```text
BinaryExpr {
    left
    op
    right
}
```

Parser dùng Pratt parser.

---

# 35. Precedence table

Tôi đề xuất từ thấp → cao:

```text id="qkhmte"
1   assignment          =
2   logical OR          ||
3   logical AND         &&
4   bitwise OR          |
5   bitwise XOR         ^
6   bitwise AND         &
7   equality             == !=
8   comparison           < <= > >=
9   shifts               << >>
10  additive              + - +% -% +| -|
11  multiplicative        * / % *% *|
12  cast                  as
13  unary                 ! ~ - +
14  postfix               . [] () .await ?
15  primary
```

Có một điều chỉnh quan trọng:

### `as`

Nên có precedence thấp hơn arithmetic nhưng cao hơn assignment.

Ví dụ:

```axiom
x + y as i64
```

được parse:

```text
(x + y) as i64
```

thay vì:

```text
x + (y as i64)
```

Tuy nhiên tôi khuyên **cấm dựa vào precedence này trong style guide**; viết:

```axiom
(x + y) as i64
```

rõ ràng hơn.

---

# 36. `?` postfix

```axiom
foo()?
```

AST:

```text
TryExpr {
    operand
}
```

Nó có precedence postfix.

```axiom
foo()?.bar
```

→

```text
Field(
    Try(
        Call(foo)
    ),
    bar
)
```

---

# 37. `.await`

```axiom
future.await
```

AST:

```text
AwaitExpr {
    operand
}
```

Không phải keyword `await` đứng độc lập.

Lexer vẫn tokenize `await` keyword để hỗ trợ diagnostics/grammar nếu cần.

---

# 38. Assignment

```axiom
x = value
```

AST:

```text
AssignExpr {
    target
    value
}
```

Semantic result:

```text
unit
```

Không có compound assignment v0.1.

---

# 39. If expression

```axiom
if x > 0 {
    foo()
} else {
    bar()
}
```

AST:

```text
IfExpr {
    condition
    then_block
    else_branch?
}
```

`else if`:

```text
else if ...
```

được parse thành nested `IfExpr`.

---

# 40. Match expression

```axiom
match value {
    Message.Quit => foo(),
    Message.Text(text) => bar(text),
    _ => baz(),
}
```

AST:

```text
MatchExpr {
    scrutinee
    arms
}
```

Arm:

```text
MatchArm {
    pattern
    guard?
    body
}
```

Exhaustiveness không thuộc parser.

---

# 41. Pattern AST

```text
Pattern
├── Wildcard
├── Name
├── Literal
├── Tuple
├── Struct
├── EnumVariant
├── Array
├── Range
└── Or
```

Ví dụ:

```axiom
Message.Text(text)
```

→

```text
EnumPattern {
    path
    fields
}
```

Resolver/type checker xác định variant.

---

# 42. Closure

```axiom
|a, b| a + b
```

AST:

```text
ClosureExpr {
    params
    return_type?
    body
    move
}
```

`move`:

```axiom
move |x| x + 1
```

là syntax.

Capture semantics không nằm trong parser.

---

# 43. Block

```axiom
{
    let x = 1
    x + 2
}
```

AST:

```text
Block {
    statements
    tail_expr?
}
```

Đây là expression.

---

# 44. Statement

```text
Stmt
├── Let
├── Var
├── ExprStmt
├── Return
├── Break
├── Continue
└── Item
```

---

# 45. Let

```axiom
let x = 42
```

AST:

```text
LetStmt {
    pattern
    type?
    initializer?
}
```

Có thể:

```axiom
let x: i32 = 42
```

hoặc:

```axiom
let x = 42
```

---

# 46. `var`

```axiom
var x = 42
```

AST dùng cùng node:

```text
BindingStmt {
    mutable: true
}
```

Như vậy HIR không cần hai semantic concepts:

```text
let
var
```

chỉ cần:

```text
Binding {
    mutability
}
```

Đây là ví dụ tốt của nguyên tắc:

> Một câu hỏi semantic → một mechanism.

---

# 47. Return

```axiom
return value
```

AST:

```text
ReturnStmt {
    value?
}
```

`return` không phải expression.

---

# 48. Break

Theo freeze:

> `break` không có value trong v0.1.

Do đó:

```axiom
break
```

hợp lệ.

```axiom
break 42
```

parser error.

Không cần thiết kế loop value semantics ngay.

---

# 49. Continue

```axiom
continue
```

không có value.

---

# 50. Semicolon parsing

Vì semicolon optional, parser phải xác định statement boundary.

Ví dụ:

```axiom
let x = 1
let y = 2
```

Parser nhận biết `let` bắt đầu statement mới.

Nhưng:

```axiom
foo
(bar)
```

không được tự ý quyết định là hai statement nếu grammar cho phép continuation.

Do đó:

> **Newline không phải semantic token, nhưng parser vẫn có thể truy cập source span/newline information khi cần disambiguation.**

Tuy nhiên không nên dùng newline như ASI.

---

# 51. Generic `<` ambiguity

Đây là vấn đề lớn nhất của parser.

Ví dụ:

```axiom
foo<Bar>(x)
```

`<` có thể là:

```text
generic arguments
```

hoặc:

```text
comparison
```

Axiom tránh ambiguity bằng cách **không cho parser đoán semantic type quá sớm**.

Parser có thể dùng token context:

```text
identifier + < ... > + (
```

để parse generic-call syntax.

Nhưng:

```axiom
a < b > c
```

vẫn binary operators.

---

# 52. Không dùng lexer hack

Không biến:

```text
foo<Bar>
```

thành một token đặc biệt.

Lexer không biết `foo` là generic function.

Parser chịu trách nhiệm.

---

# 53. Generic type syntax

```axiom
Vec<i32>
Map<Text, i32>
view<Vec<i32>>
```

Parser:

```text
TypeApplication {
    base
    arguments
}
```

---

# 54. `dyn Trait`

```axiom
dyn Display
```

AST:

```text
DynTraitType {
    trait_type
}
```

Không resolve trait tại parser.

---

# 55. `impl Trait`

```axiom
impl Iterator
```

AST:

```text
ImplTraitType {
    bounds
}
```

Type checker mới xác định opaque type semantics.

---

# 56. Raw pointers

```axiom
*const T
*mut T
```

AST:

```text
RawPointerType {
    mutability
    pointee
}
```

Parser không đánh dấu unsafe.

Unsafe checker làm việc sau.

---

# 57. View types

```axiom
view<T>
mut_view<T>
```

AST:

```text
ViewType {
    mutable
    element
}
```

HIR:

```text
TypeId(View(...))
```

---

# 58. Function types

Ví dụ:

```axiom
fn(i32, i32) -> i32
```

AST:

```text
FunctionType {
    params
    return_type
}
```

Closure type syntax không cần xuất hiện trực tiếp.

---

# 59. Type path

Axiom cần support qualified names:

```text
math.vector.Vec2
```

hoặc:

```text
math::vector::Vec2
```

Ở đây tôi khuyên **chọn một syntax duy nhất**.

Với module syntax hiện tại:

```axiom
module math.vector
```

thì nên dùng:

```axiom
math.vector.Vec2
```

cho consistency.

`::` chỉ dùng cho **explicit semantic qualification**, nếu thực sự cần.

Như vậy:

```text
.
```

= member/module path

```text
::
```

= explicit associated/trait qualification.

---

# 60. Explicit trait qualification

Ví dụ:

```axiom
<T as Display>::display(x)
```

Đây là syntax mạnh nhưng phức tạp.

Tôi đề xuất **không đưa dạng này vào v0.1 parser ban đầu**.

Thay vào đó:

```axiom
Display::display(x)
```

và resolver/type checker xác định trait.

Nếu cần disambiguation:

```axiom
<T as Trait>
```

có thể bổ sung khi trait resolution implementation tới.

Điều này giữ parser MVP nhỏ hơn.

---

# 61. AST → HIR normalization

Đây là nơi Axiom bắt đầu trở nên rất sạch.

Ví dụ source:

```axiom
v.length()
```

AST:

```text
MethodCall(
    receiver = Name(v),
    name = length
)
```

HIR:

```text
Call(
    resolved_function = FunctionId(42),
    args = [LocalId(v)]
)
```

---

# 62. `if`

AST:

```text
IfExpr
```

HIR có thể vẫn giữ:

```text
IfExpr
```

vì semantic control flow chưa cần hạ xuống MIR ngay.

---

# 63. `for`

Surface:

```axiom
for x in items {
    use(x)
}
```

AST:

```text
ForStmt {
    pattern
    iterable
    body
}
```

HIR có thể lower thành iterator semantics:

```text
loop {
    match iterator.next() {
        ...
    }
}
```

nhưng **không nên lower ngay thành MIR**.

---

# 64. `async`

AST:

```text
AsyncFunction
AwaitExpr
```

HIR:

```text
AsyncFunction
Await
```

MIR lowering mới tạo state machine.

Điều này giữ AST/HIR dễ hiểu.

---

# 65. Unsafe

```axiom
unsafe {
    *ptr
}
```

AST:

```text
UnsafeBlock {
    body
}
```

Không disable parser/type checker.

---

# 66. Comptime

```axiom
comptime {
    ...
}
```

AST:

```text
ComptimeBlock
```

hoặc:

```text
ComptimeExpr
```

Parser chỉ nhận syntax.

Capability checking nằm trong comptime semantic phase.

---

# 67. Parser architecture

Đề xuất code structure:

```text id="ez4kl0"
parser/
├── parser.ax
├── cursor.ax
├── items.ax
├── types.ax
├── expressions.ax
├── statements.ax
├── patterns.ax
├── attributes.ax
├── precedence.ax
├── recovery.ax
└── tests/
```

Không nên có:

```text
parser/ownership.ax
parser/typecheck.ax
```

Parser không biết ownership/type semantics.

---

# 68. Pratt parser

Core:

```text
parse_expr(min_precedence)
```

Algorithm conceptual:

```text id="a2mljj"
left = parse_prefix()

while next token is postfix or binary operator:
    if precedence < min_precedence:
        break

    op = consume()
    right = parse_expr(next_precedence)

    left = Binary(left, op, right)

return left
```

Postfix:

```text
()
[]
.
?
.await
```

được xử lý ở precedence cao nhất.

---

# 69. Prefix parser

Prefix:

```text id="4x7qjl"
literal
identifier
self
(
[
{
if
match
|
-
+
!
~
unsafe
comptime
```

mỗi loại dispatch tới parser tương ứng.

---

# 70. AST invariants

Khóa:

```text id="ez7f5y"
AAST-20
AST represents syntax, not semantic resolution.

AAST-21
Every AST node has a source span.

AAST-22
AST identity is distinct from source byte address.

AAST-23
AST references use typed IDs.

AAST-24
AST does not perform type inference.

AAST-25
AST does not perform ownership analysis.

AAST-26
AST does not perform trait resolution.

AAST-27
AST preserves syntax required for diagnostics.

AAST-28
AST may normalize purely syntactic sugar only when source mapping remains recoverable.

AAST-29
Semantic identity is established only after resolution.

AAST-30
AST literals preserve source spelling until semantic literal interpretation.

AAST-31
Method-call syntax remains distinguishable before semantic lowering.

AAST-32
Attribute syntax remains schema-neutral before semantic validation.
```

---

# 71. Parser invariants

```text id="8z5j4a"
APARSE-20
Parser consumes only lexer tokens.

APARSE-21
Parser does not resolve names.

APARSE-22
Parser does not infer types.

APARSE-23
Parser does not perform ownership checks.

APARSE-24
Expression precedence is deterministic.

APARSE-25
Generic syntax is resolved by parser context, not lexer hacks.

APARSE-26
Newline does not implement automatic semicolon insertion.

APARSE-27
Parser error recovery is deterministic.

APARSE-28
Parser preserves source spans for recovered nodes.

APARSE-29
Unsupported syntax produces structured diagnostics.

APARSE-30
Parser behavior does not depend on hash-map iteration order.
```

---

# 72. Parser vertical slice

Đừng triển khai toàn bộ ngay.

### Slice 1

```axiom
fn main() {}
```

Phải đi được:

```text
Lexer
 ↓
Parser
 ↓
AST
```

### Slice 2

```axiom
fn main() {
    let x = 42
}
```

### Slice 3

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

### Slice 4

```axiom
struct Vec2 {
    x: f32
    y: f32
}
```

### Slice 5

```axiom
enum Option<T> {
    None,
    Some(T),
}
```

### Slice 6

```axiom
match x {
    Option.Some(v) => v,
    Option.None => 0,
}
```

### Slice 7

```axiom
fn foo<T: Display>(x: T) -> T {
    x
}
```

### Slice 8

```axiom
async fn foo() {
    bar().await
}
```

---

# 73. Parser test đặc biệt cần có

Đây là nhóm test tôi muốn agent viết **trước khi mở rộng parser**:

```text id="58i6wz"
1 + 2 * 3
a < b
a <= b
a == b
a && b || c

foo(x)
foo<T>(x)
foo.bar()
foo.bar<T>(x)

a[0]
a[1..4]
a[1..=4]

(x)
(x, y)
()

if x { y } else { z }

match x {
    A => 1,
    B(v) => v,
}

|x| x + 1
move |x| x

x?
x?.foo()
foo().await

Vec<i32>
view<Vec<i32>>
mut_view<f32>
*const i32
*mut i32
```

Đặc biệt:

```text id="n4r9l7"
1..10
1.0
foo<Bar>(x)
a < b > c
```

đây là những điểm dễ làm parser sai.

---

# 74. Một thay đổi tôi khuyến nghị so với thiết kế ban đầu

Tôi muốn **không đưa quá nhiều sugar vào parser v0.1**.

Cụ thể chưa cần:

```text id="u4f4qf"
compound assignment
++
--
ternary
pipeline
spread
optional chaining syntax riêng
macro syntax
pattern guards phức tạp
raw strings
char literals
```

Không phải vì Axiom “yếu”.

Mà vì:

> **Mỗi syntax mới là một semantic surface mới phải duy trì suốt vòng đời ngôn ngữ.**

Axiom nên có core syntax nhỏ nhưng semantic capability mạnh.

---

# 75. Grammar EBNF khung v0.1

Khung parser có thể bắt đầu bằng:

```text id="tx7k9c"
compilation_unit
    = module_decl? item* ;

item
    = attribute* visibility?
      (function
      | struct
      | enum
      | trait
      | impl
      | type_alias
      | const_decl
      | static_decl
      | module_decl
      | import_decl) ;

function
    = "fn" identifier generic_params?
      "(" parameters? ")"
      return_type?
      where_clause?
      block ;

struct
    = "struct" identifier generic_params?
      struct_body ;

enum
    = "enum" identifier generic_params?
      "{" enum_variant* "}" ;

trait
    = "trait" identifier generic_params?
      supertraits?
      where_clause?
      "{" trait_item* "}" ;

impl
    = "impl" generic_params?
      trait_type? "for" type
      where_clause?
      "{" impl_item* "}" ;

type
    = path
    | tuple_type
    | array_type
    | function_type
    | view_type
    | mut_view_type
    | raw_pointer_type
    | dyn_trait_type
    | impl_trait_type ;

block
    = "{" statement* expression? "}" ;
```

Expression grammar để Pratt parser xử lý.

---

# 76. Một điểm rất quan trọng: AST không phải API ổn định

Ta không nên cam kết:

```text
AST layout
```

là public compiler API.

Chỉ cam kết:

```text
Source semantics
HIR semantics
MIR semantics
Diagnostics schema
```

AST có thể thay đổi implementation.

Điều này cho compiler freedom.

---

# 77. Boundary sau Parser

Sau khi parser hoàn thành:

```text
Source
 ↓
Lexer
 ↓
AST
```

ta chuyển sang:

```text
AST
 ↓
Name Resolver
 ↓
HIR
```

Đây là nơi Axiom bắt đầu xử lý câu hỏi:

> **“Tên này thực sự là cái gì?”**

Ví dụ:

```axiom
fn foo() {
    let x = 10
    x
}
```

Resolver phải biến:

```text
"foo"
"x"
```

thành:

```text
FunctionId(...)
LocalId(...)
```

và giải quyết:

- scope
- shadowing
- module
- imports
- re-exports
- generic parameters
- `self`
- trait names
- associated names
- ambiguity.

**Bước tiếp theo là `AXIOM NAME RESOLUTION + HIR v0.1`**, và đây thực chất là semantic subsystem đầu tiên của compiler. Sau đó mới tới Type System; tôi sẽ thiết kế luôn **scope tree + module graph + symbol resolution algorithm + shadowing rules + import resolution + HIR normalization + unresolved-name diagnostics**, thay vì chỉ mô tả resolver chung chung.