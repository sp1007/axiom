# BOOTSTRAP-127 — Parser, CST/AST & Incremental Syntax Engine

**Trạng thái: FROZEN / COMPLETED**

Mục tiêu của task:

> Parser Axiom phải **deterministic, error-tolerant, incremental, nhanh và không phụ thuộc vào type checker để parse syntax**.

Kiến trúc chốt:

```text
Source
  ↓
Lexer
  ↓
Token + Trivia
  ↓
Green CST
  ↓
Red Syntax Tree
  ↓
AST
  ↓
Name Resolution
  ↓
Type / Trait / Semantic Analysis
```

---

# 1. Không để parser làm semantic analysis

Parser chỉ trả lời:

> “Chuỗi token này có cấu trúc syntax nào?”

Không trả lời:

> “Tên này thuộc type nào?”

Ví dụ:

```ax
foo < bar > baz
```

Parser phải có quy tắc syntax deterministic để tạo cấu trúc hợp lệ; không được gọi type checker chỉ để quyết định cách parse.

---

# 2. Parser architecture

Đề xuất:

```text
Top-level declarations
        │
        ▼
Recursive Descent Parser
        │
        ├── Expression Parser → Pratt / precedence climbing
        ├── Pattern Parser
        ├── Type Parser
        ├── Generic Parser
        └── Attribute Parser
```

Không dùng parser generator làm dependency bắt buộc của compiler.

Có thể dùng grammar generator trong development/testing, nhưng production parser nên là code native của compiler.

---

# 3. Vì sao Recursive Descent

Axiom có nhiều cấu trúc:

```text
fn
struct
enum
trait
impl
comptime
extern
unsafe
match
patterns
generics
attributes
```

Recursive descent cho phép:

- diagnostics tốt;
- recovery tốt;
- incremental parsing;
- debug parser dễ;
- kiểm soát ambiguity;
- code compiler dễ tự host.

---

# 4. Expression parser dùng Pratt

Expression precedence phù hợp với Pratt parser:

```text
primary
postfix
unary
multiplicative
additive
shift
comparison
bitwise
logical
range
assignment
```

Ví dụ:

```ax
a + b * c
```

AST:

```text
      +
     / \
    a   *
       / \
      b   c
```

---

# 5. Precedence table là compiler data

Không hard-code precedence rải rác trong parser.

Concept:

```text
OperatorInfo {
    token
    precedence
    associativity
    kind
}
```

Ví dụ:

```text
* / %       high
+ -         medium
< <= > >=   ...
== !=       ...
&&
||
=           low
```

---

# 6. Assignment

Assignment có precedence thấp:

```ax
a = b + c
```

→

```text
Assign(a, Add(b,c))
```

Không phải:

```text
Add(Assign(a,b),c)
```

---

# 7. Short-circuit operators

`&&` và `||` có syntax expression riêng về mặt lowering.

Parser tạo:

```text
LogicalAnd
LogicalOr
```

chứ không biến chúng thành ordinary bitwise operations.

Sau này HIR/MIR mới biểu diễn control flow tương ứng.

---

# 8. Unary operators

Core:

```ax
-x
!x
~x
```

Raw pointer dereference:

```ax
unsafe {
    *p
}
```

được parser nhận như unary expression; semantic verifier mới xác định rằng dereference yêu cầu unsafe.

Parser không chịu trách nhiệm kiểm tra safety.

---

# 9. Postfix expressions

Một primary có thể nối:

```text
call
index
field
method
await
?
```

Ví dụ:

```ax
foo.bar(x)[i].baz().await?
```

Parser xây expression từ trái sang phải.

---

# 10. Member access

```ax
user.name
```

syntax:

```text
MemberAccess {
    receiver: user
    member: name
}
```

Parser không quyết định `name` là:

- field;
- method;
- associated item;
- extension method.

Đó là resolver.

---

# 11. Method call

```ax
user.greet()
```

AST:

```text
MethodCall {
    receiver: user
    name: greet
    args: []
}
```

Không resolve thành function ở parser phase.

---

# 12. Generic arguments

Axiom cần syntax rõ ràng:

```ax
foo::<i32>(x)
```

cho generic function invocation khi cần disambiguation.

Đồng thời cho phép inference:

```ax
foo(x)
```

---

# 13. `::` turbofish

Chốt:

```ax
foo::<i32>(x)
```

là canonical explicit generic call syntax.

Điều này giảm ambiguity giữa:

```text
<
>
```

của comparison và generic arguments.

---

# 14. Type generic arguments

```ax
Vec<i32>
Map<String, User>
Result<Data, Error>
```

Parser đang ở **type context**, vì vậy:

```text
<
>
```

được parse như generic delimiters.

---

# 15. Expression `<` ambiguity

Axiom không nên yêu cầu parser gọi type checker để phân biệt:

```ax
a < b
```

và generic syntax.

Quy tắc:

- trong type grammar → `<...>` generic;
- trong expression grammar → `<` operator;
- generic function invocation trong expression → `::<...>`.

Đây là lựa chọn rất quan trọng để parser đơn giản và deterministic.

---

# 16. Struct literal

Ví dụ:

```ax
User {
    id: 10,
    name: "A",
}
```

AST:

```text
StructLiteral {
    type: User
    fields: [...]
}
```

Parser không cần biết `User` có thật sự là struct.

Nếu không phải struct → semantic diagnostic sau.

---

# 17. Block expression

```ax
{
    let x = 10;
    x + 1
}
```

là expression.

Giá trị của block là expression cuối cùng nếu có:

```ax
let x = {
    10
};
```

---

# 18. Statement termination

Axiom dùng semicolon cho statement khi cần:

```ax
let x = 10;
foo();
```

Nhưng block cuối:

```ax
{
    foo()
}
```

không bắt buộc `;`.

Điều này giữ syntax tương đối gọn nhưng vẫn deterministic.

---

# 19. Dangling semicolon

Cho phép:

```ax
foo();
```

nhưng không tạo semantic khác biệt nếu:

```ax
foo()
```

là valid expression statement.

Formatter canonicalize về một style duy nhất.

---

# 20. `if`

```ax
if condition {
    ...
} else if other {
    ...
} else {
    ...
}
```

`if` là expression:

```ax
let x = if condition {
    1
} else {
    2
};
```

Parser chỉ tạo cây.

Type checker đảm bảo hai branches tương thích.

---

# 21. `match`

```ax
match value {
    Pattern => expr,
    Pattern => expr,
}
```

Mỗi arm:

```text
Pattern
Optional guard
=>
Expression
```

---

# 22. Match guard

Có thể hỗ trợ:

```ax
match x {
    n if n > 0 => positive,
    _ => zero_or_negative,
}
```

Parser tạo:

```text
MatchArm {
    pattern
    guard
    body
}
```

Exhaustiveness thuộc semantic checker.

---

# 23. Pattern parser độc lập

Pattern không nên tái sử dụng expression parser một cách mù quáng.

Có:

```text
Pattern
├── Wildcard
├── Binding
├── Literal
├── Tuple
├── Struct
├── EnumVariant
├── Range
├── Or
├── Reference/View pattern
└── ...
```

---

# 24. Binding pattern

```ax
match x {
    value => ...
}
```

Parser biết đây là binding pattern.

Resolver sau đó xác định binding scope.

---

# 25. Or-pattern

```ax
match x {
    1 | 2 | 3 => ...
}
```

Parser:

```text
OrPattern[
    Literal(1),
    Literal(2),
    Literal(3)
]
```

---

# 26. Range pattern

```ax
match x {
    1..=10 => ...
    _ => ...
}
```

Parser phân biệt:

```text
1..=10
```

với:

```text
1..10
```

và expression range.

---

# 27. Generic type parser

Type grammar:

```text
Type
├── Primitive
├── Path
├── Generic
├── Tuple
├── Array
├── Function
├── View
├── MutView
├── RawPointer
├── dyn Trait
└── never
```

---

# 28. `view<T>` và `mut_view<T>`

Parser xem:

```ax
view<User>
mut_view<User>
```

như type constructors.

Không có:

```ax
User&
User&&
```

trong safe Core.

---

# 29. Raw pointer syntax

```ax
*const T
*mut T
```

là type syntax hợp lệ nhưng thuộc unsafe/system semantics.

Parser vẫn parse bình thường.

Safety verifier xử lý sau.

---

# 30. Function types

Ví dụ:

```ax
fn(i32, i32) -> i32
```

là function type.

Parser phải phân biệt:

```ax
fn foo(...)
```

declaration

với:

```ax
fn(i32) -> i32
```

type.

---

# 31. Tuple types

```ax
(i32, f64, String)
```

Empty tuple:

```ax
()
```

là `unit`.

Single-element tuple cần comma:

```ax
(i32,)
```

khác:

```ax
(i32)
```

là parenthesized type/expression.

---

# 32. Array type

```ax
[i32; 16]
```

AST/type syntax:

```text
ArrayType {
    element: i32
    length: 16
}
```

Length phải là compile-time evaluable semantic expression.

---

# 33. Generic declaration

```ax
fn max<T: Ord>(a: T, b: T) -> T
```

Parser:

```text
GenericParams
 └── T
     └── constraint Ord
```

---

# 34. `where`

Cho constraint phức tạp:

```ax
fn foo<T, U>(x: T)
where
    T: Iterator<Item = U>,
    U: Display,
{
}
```

Parser tạo structured constraints.

Không giữ `where` dưới dạng raw text.

---

# 35. Trait bounds

```ax
T: Display + Clone
```

AST:

```text
Bounds[
    Display,
    Clone
]
```

---

# 36. Associated type constraint

```ax
T: Iterator<Item = i32>
```

Parser phải hỗ trợ:

```text
AssociatedConstraint {
    trait: Iterator
    name: Item
    value: i32
}
```

---

# 37. Struct declaration

```ax
struct User {
    id: u64,
    name: String,
}
```

Parser giữ field order trong CST/AST.

Semantic layout có thể reorder sau, trừ khi `repr` contract.

---

# 38. Tuple struct

Nếu muốn giữ syntax đơn giản:

```ax
struct UserId(u64);
```

được hỗ trợ.

Semantic type vẫn nominal.

---

# 39. Enum

```ax
enum Result<T, E> {
    Ok(T),
    Err(E),
}
```

Variants có thể:

```text
unit
tuple
struct-like
```

---

# 40. Trait

```ax
trait Display {
    fn display(self: view<Self>) -> String;
}
```

Parser chỉ xây declaration.

Trait coherence/object-safety là semantic phase.

---

# 41. Impl

```ax
impl Display for User {
    fn display(self: view<Self>) -> String {
        ...
    }
}
```

Inherent impl:

```ax
impl User {
    fn id(self: view<Self>) -> u64 {
        self.id
    }
}
```

---

# 42. Override

Không cần:

```ax
override fn ...
```

Concrete implementation cùng signature/name thỏa trait method sẽ override default implementation theo semantic rules đã frozen.

Parser không cần keyword `override`.

---

# 43. Function declaration

Canonical:

```ax
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

Parser giữ:

```text
name
generic params
parameters
return type
where clauses
attributes
body
```

---

# 44. Receiver syntax

Các receiver semantic:

```ax
self: Self
self: view<Self>
self: mut_view<Self>
```

Ví dụ:

```ax
fn read(self: view<Self>) -> i32
fn set(self: mut_view<Self>, x: i32)
fn consume(self: Self)
```

---

# 45. Method sugar

Call:

```ax
x.read()
```

không phải syntax riêng ở semantic level.

Parser tạo method-call node.

Resolver sau đó tìm:

```text
inherent
trait
extension
generic extension
```

theo rules đã frozen.

---

# 46. `let` và `var`

```ax
let x = 10;
var y = 20;
```

Parser phân biệt rõ.

Không dùng:

```text
mut
```

làm modifier chính cho local variable.

---

# 47. Explicit type annotation

```ax
let x: i32 = 10;
```

AST:

```text
Let {
    pattern: x
    type: i32
    initializer: 10
}
```

---

# 48. Ownership operations

Không đưa borrow syntax vào parser.

Move có thể được biểu diễn semantic bằng ordinary use.

Ví dụ:

```ax
let b = a;
```

type/ownership analysis quyết định:

```text
Copy
hoặc
Move
```

Không cần:

```ax
move(a)
```

cho ordinary ownership transfer.

---

# 49. Explicit clone

Costly duplication phải rõ ràng:

```ax
let b = a.clone();
```

Parser chỉ coi `clone` là method call.

Trait `Clone` được resolve semantic.

---

# 50. Explicit view construction

```ax
let r = view(x);
let w = mut_view(x);
```

Parser ordinary function-call syntax.

Compiler builtin/library semantics xử lý sau.

---

# 51. Attribute parser

```ax
@repr(C)
@inline
@target_feature("avx2")
```

Parser tạo:

```text
Attribute {
    name
    arguments
    span
}
```

Không parse từng attribute thành grammar riêng.

---

# 52. Attribute arguments

Các dạng:

```ax
@inline
@repr(C)
@align(64)
@export("foo")
@cfg(target_os = "windows")
```

parser có generic attribute argument representation.

Compiler semantic registry validate sau.

---

# 53. Unknown attribute

Parser vẫn parse:

```ax
@foo(...)
```

Semantic phase quyết định:

```text
known
unknown
tooling namespace
```

Điều này giúp parser forward-compatible.

---

# 54. `async`

```ax
async fn fetch(...) -> Data {
    ...
}
```

Parser đánh dấu:

```text
FunctionModifiers {
    async: true
}
```

Không lower Future ở parser.

---

# 55. `await`

```ax
let x = future.await;
```

AST:

```text
Await {
    operand: future
}
```

Semantic/lowering xác định suspension point.

---

# 56. `comptime`

```ax
comptime fn make_value() -> i32 {
    ...
}
```

và:

```ax
let x = comptime {
    ...
};
```

Parser chỉ ghi nhận compile-time construct.

Sandbox/capability là semantic/compiler execution layer.

---

# 57. `unsafe`

```ax
unsafe {
    ...
}
```

hoặc:

```ax
unsafe fn read(...)
```

Parser tạo unsafe marker.

Verifier mới kiểm tra safety boundary.

---

# 58. `extern`

Ví dụ:

```ax
extern "C" {
    fn malloc(size: usize) -> *mut u8;
}
```

Parser giữ ABI string.

FFI validator kiểm tra:

- ABI;
- FFI-safe types;
- ownership contract.

---

# 59. Imports

Canonical:

```ax
import std::io::File;
```

Alias:

```ax
import std::io::File as IoFile;
```

Grouped:

```ax
import std::io::{File, Reader, Writer};
```

Core v1 không cần wildcard import.

---

# 60. Module declarations

```ax
module myapp::network;
```

hoặc module structure được xác định từ package filesystem/build manifest.

Không nên yêu cầu programmer lặp lại path nếu compiler đã có package/module graph.

---

# 61. Parser error recovery

Parser phải **recover nhiều lỗi trong một lần compile**.

Ví dụ:

```ax
fn foo( {
    let x =
    let y = ;
}
```

Không dừng ngay lỗi đầu tiên.

---

# 62. Synchronization tokens

Parser recovery có thể sync tại:

```text id="s8z5xq"
;
}
)
]
,
fn
struct
enum
trait
impl
```

Tùy grammar context.

---

# 63. Recovery không tạo semantic false proof

Parser có thể tạo:

```text
ErrorNode
```

nhưng:

```text
ErrorNode != valid AST
```

Semantic checker không được coi ErrorNode là valid expression/type.

---

# 64. Expected-token diagnostics

Parser có structured error:

```json
{
  "code": "EPARSE_EXPECTED_TOKEN",
  "expected": ["Identifier", "("],
  "found": "BraceClose"
}
```

Human message được sinh từ structured data.

---

# 65. Parser checkpoints

Parser có:

```text
checkpoint()
restore()
```

nhưng chỉ dùng cho ambiguity cục bộ.

Không được dùng arbitrary backtracking trên cả file.

---

# 66. Why limited backtracking

Nếu parser thử mọi khả năng:

```text
A
→ B
→ C
→ D
→ ...
```

complexity có thể tăng mạnh.

Axiom grammar phải được thiết kế để ambiguity nhỏ và local.

---

# 67. Generic ambiguity strategy

Đây là một quyết định quan trọng:

```text
foo::<T>()
```

được ưu tiên cho generic invocation.

Trong type position:

```text
Vec<T>
```

là generic type.

Trong expression:

```text
a < b
```

là comparison.

Không dùng speculative type checking.

---

# 68. Closure syntax

Canonical:

```ax
|x, y| x + y
```

Mutable capture không cần keyword riêng nếu compiler inference đủ.

Explicit move closure:

```ax
move |x| x + captured
```

Parser tạo:

```text
Closure {
    modifiers
    params
    body
}
```

Capture mode được compiler suy luận.

---

# 69. Async closure

```ax
async |x| {
    await_something(x).await
}
```

Parser có modifier.

Lowering tạo Future state machine sau.

---

# 70. Loop syntax

```ax
loop {
    ...
}
```

```ax
while condition {
    ...
}
```

```ax
for item in items {
    ...
}
```

`for` được desugar ở HIR, không phải parser.

---

# 71. Break value

```ax
let result = loop {
    if ready {
        break value;
    }
};
```

AST:

```text
Break {
    label?
    value?
}
```

---

# 72. Labels

```ax
'outer: loop {
    loop {
        break 'outer;
    }
}
```

Parser hỗ trợ label syntax.

Semantic resolver xác định label target.

---

# 73. `return`

```ax
return value;
```

AST:

```text
Return(value?)
```

Drop/cleanup được xử lý ở MIR.

---

# 74. `?`

```ax
let x = read()?.parse()?;
```

Parser tạo postfix `Try` node.

HIR lowerer mới chuyển nó thành Result/Option control flow.

---

# 75. No parser-level implicit conversions

Parser không bao giờ tạo:

```text
ImplicitCast
```

Semantic phase mới quyết định những conversion nào được language cho phép.

Axiom tránh implicit conversion chains.

---

# 76. CST → AST

CST:

```text
tokens + trivia + syntax nodes
```

AST:

```text
semantic syntax
```

Ví dụ:

```ax
(((a + b)))
```

CST giữ parentheses.

AST có thể chỉ giữ:

```text
Add(a,b)
```

nhưng SourceSpan phải vẫn map được về source.

---

# 77. Parentheses

Parentheses không làm mất source mapping.

Ví dụ AST node:

```text
Add(a,b)
```

có source span bao phủ:

```text
((a + b))
```

nếu diagnostic cần.

---

# 78. Syntax identity

Green nodes immutable.

Nếu revision chỉ thay:

```text
100 → 101
```

các subtree trước/sau không thay đổi có thể reuse.

---

# 79. Incremental parser

Pipeline:

```text
Old CST
   │
Source edit
   │
Incremental lexer
   │
changed token range
   │
reparse smallest affected ancestor
   │
reuse unchanged green subtrees
   │
New CST
```

Không parse lại toàn bộ file nếu không cần.

---

# 80. Incremental parse correctness

Phải đảm bảo:

```text
Parse(full new source)
==
Parse(incremental(old source, edit))
```

ở semantic CST/AST level.

Trivia identity có thể khác nếu implementation cho phép, nhưng source semantics phải giống.

---

# 81. Structural sharing

Ví dụ:

```ax
fn a() {}
fn b() {}
fn c() {}
```

sửa body `b`.

Tree:

```text
old:
Root
├── a ─────────┐
├── b          │ reused
└── c ─────────┘

new:
Root'
├── a ─────────┘ reused
├── b'          changed
└── c ─────────┘ reused
```

---

# 82. Parser memory architecture

Green tree nodes nên compact.

Không:

```text
heap allocation per tiny syntax object
```

nếu có thể tránh.

Arena/chunk allocation phù hợp.

---

# 83. Red tree

Red tree cung cấp:

```text
parent
children
source range
semantic navigation
```

nhưng không cần duplicate toàn bộ green node data.

---

# 84. AST memory lifetime

AST có thể được intern/arena allocate theo revision.

Không yêu cầu AST object sống vĩnh viễn.

CompilerDB giữ logical identity nếu cần incremental reuse.

---

# 85. Formatter

Formatter nên chạy trên CST/AST có source metadata, không parse source thành text rồi format lại bằng regex.

Pipeline:

```text
Source
 ↓
CST
 ↓
Formatting IR
 ↓
Canonical output
```

---

# 86. Formatter không thay đổi semantics

Invariant:

```text
parse(format(source))
```

phải semantic-equivalent với:

```text
parse(source)
```

trừ source vốn invalid.

---

# 87. Canonical formatting

Axiom nên có formatter chuẩn:

```text
ax fmt
```

và một canonical style.

Không cần để compiler semantic phụ thuộc formatting.

---

# 88. Formatter stability

Phải có:

```text
fmt(fmt(source)) == fmt(source)
```

đối với valid source.

Đây là test cực kỳ quan trọng.

---

# 89. AST transformation

Refactoring như rename:

```text
foo → bar
```

không nên search/replace string.

IDE query:

```text
References(FunctionId)
```

sau đó sửa exact source spans.

---

# 90. AI source transformation

AI agent có thể yêu cầu:

```text
rename symbol DeclarationId(42)
```

thay vì:

```text
replace every "foo"
```

Giảm mạnh nguy cơ sửa nhầm identifier.

---

# 91. Parser API

Concept:

```text
Parser {
    tokens: TokenStream
    cursor: TokenIndex
    diagnostics: DiagnosticSink
}
```

Các hàm:

```text
parse_file()
parse_item()
parse_expr()
parse_type()
parse_pattern()
parse_stmt()
parse_attribute()
parse_generic_args()
```

---

# 92. Parser không được biết TypeDB

Đây là boundary quan trọng:

```text
Parser
   X
TypeDB
```

Parser chỉ biết:

```text
Token
SyntaxKind
GrammarContext
```

Điều này giúp:

- test parser độc lập;
- incremental parser;
- deterministic behavior;
- bootstrap dễ.

---

# 93. Semantic ambiguity giải quyết sau parser

Ví dụ:

```ax
foo.bar
```

có thể là:

- field;
- method reference;
- associated item;
- extension method.

Parser không cần quyết định.

---

# 94. Syntax ambiguity phải giải quyết ở grammar

Ví dụ:

```ax
a < b
```

không được để type checker quyết định nó là generic expression.

Nếu grammar gặp ambiguity thật sự:

> sửa grammar hoặc thêm explicit syntax.

Không đẩy complexity sang semantic phase.

---

# 95. Parser fuzzing

Parser phải được fuzz bằng:

```text
random bytes
random UTF-8
random tokens
random valid ASTs
mutated valid programs
```

Invariant:

> Không input nào được gây uncontrolled compiler crash.

---

# 96. Round-trip testing

Test:

```text
source
 → CST
 → source
```

phải bảo toàn source trong lossless mode.

Với canonical formatter:

```text
source
 → parse
 → format
 → parse
```

phải semantic-equivalent.

---

# 97. AST pretty printer

Compiler cần:

```text
axc inspect ast file.ax
```

cho:

- compiler developers;
- AI agents;
- tests;
- debugging.

---

# 98. CST pretty printer

Có thêm:

```text
axc inspect cst file.ax
```

để debug grammar/incremental parser.

---

# 99. Parser test layers

```text
Lexer tests
     ↓
Token tests
     ↓
CST tests
     ↓
AST tests
     ↓
Parser diagnostics
     ↓
Semantic integration
```

Không dùng semantic compiler để test mọi parser rule.

---

# 100. Parser invariants

### `APARSE-20`
Parsing is deterministic.

### `APARSE-21`
Parser does not require type checking to construct ordinary syntax.

### `APARSE-22`
Parser does not perform ownership analysis.

### `APARSE-23`
Parser does not perform trait solving.

### `APARSE-24`
Parser does not execute comptime code.

### `APARSE-25`
Expression precedence is explicitly defined.

### `APARSE-26`
Operator associativity is explicitly defined.

### `APARSE-27`
Generic invocation syntax is unambiguous.

### `APARSE-28`
`::<...>` is the explicit generic argument syntax for expression calls.

### `APARSE-29`
Type grammar and expression grammar have distinct generic contexts.

### `APARSE-30`
Parser does not use speculative semantic resolution to resolve ordinary syntax.

### `APARSE-31`
Parser backtracking is bounded and local.

### `APARSE-32`
Parser supports structured error recovery.

### `APARSE-33`
Parser errors use stable diagnostic codes.

### `APARSE-34`
Error nodes cannot become semantic proof.

### `APARSE-35`
CST is lossless for supported source syntax.

### `APARSE-36`
AST may discard non-semantic syntax trivia.

### `APARSE-37`
Source spans remain available after syntax lowering.

### `APARSE-38`
Incremental parsing is semantically equivalent to full parsing.

### `APARSE-39`
Unchanged syntax subtrees may be structurally shared.

### `APARSE-40`
Green syntax nodes are immutable.

### `APARSE-41`
Parser snapshots can coexist across source revisions.

### `APARSE-42`
Formatter output parses successfully.

### `APARSE-43`
Formatting does not change program semantics.

### `APARSE-44`
Formatting is idempotent.

### `APARSE-45`
Refactoring operates on semantic identities rather than textual name matching.

### `APARSE-46`
Parser does not resolve field-vs-method semantics.

### `APARSE-47`
Parser does not determine overload resolution.

### `APARSE-48`
Parser does not determine implicit conversions.

### `APARSE-49`
Parser handles Unicode identifiers according to lexer rules.

### `APARSE-50`
Parser supports the complete Core surface grammar.

### `APARSE-51`
Parser fuzzing must not produce uncontrolled compiler crashes.

### `APARSE-52`
AST inspection is deterministic.

### `APARSE-53`
CST inspection is deterministic.

### `APARSE-54`
Parser behavior is independent of compiler optimization level.

### `APARSE-55`
Parser implementation does not depend on third-party parser runtime.

### `APARSE-56`
Parser can operate independently of target backend.

### `APARSE-57`
Parser diagnostics are machine-readable.

### `APARSE-58`
Syntax ambiguities are resolved by grammar rules or explicit syntax, not arbitrary guessing.

### `APARSE-59`
Incremental parsing may reparse beyond the direct edit when required for correctness.

### `APARSE-60`
Full parsing and incremental parsing must produce equivalent semantic syntax trees.

---

# 101. Frontend architecture sau BOOTSTRAP-127

Đến đây frontend đã khá rõ:

```text
                         SourceDB
                            │
                     UTF-8 / Revision
                            │
                         Lexer
                            │
                    Token + Trivia
                            │
                   Incremental Lexer
                            │
                      Green CST
                            │
                      Red Syntax
                            │
                         AST
                            │
                    ┌───────┴────────┐
                    │                │
               Name Resolver     IDE Queries
                    │
                    ▼
                 TypeDB
                    │
               Trait Solver
                    │
                 ConstDB
                    │
                Comptime
                    │
                    ▼
                   HIR
                    │
                    ▼
                   MIR
```

Điểm quan trọng là **parser và lexer đã trở thành tầng hoàn toàn độc lập với semantic compiler**. Điều này rất có lợi cho Axiom self-hosting và AI tooling.

---

# BOOTSTRAP-128 — Name Resolution, Scope Graph & Symbol Semantics

Bước tiếp theo là tầng ngay sau AST:

```text
AST
 ↓
Module graph
 ↓
Scope graph
 ↓
Name resolution
 ↓
Resolved AST/HIR
```

Task 128 sẽ khóa:

- lexical scope;
- module scope;
- import scope;
- visibility;
- `pub`;
- aliases;
- shadowing;
- declaration order;
- forward declarations;
- recursive functions/types;
- associated items;
- trait namespaces;
- type namespace vs value namespace;
- generic parameter scope;
- pattern binding scope;
- closure capture scope;
- `comptime` scope;
- ambiguity resolution;
- import cycles;
- extension-method visibility;
- symbol identity;
- hygiene/namespace isolation cho generated code;
- và cách compiler trả lời chính xác câu hỏi:

> **“Tên `foo` tại vị trí này chính xác đang trỏ tới declaration nào?”**