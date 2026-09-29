# BOOTSTRAP-237 — AXIOM PARSER, AST & ERROR-RECOVERY ENGINE

**TRẠNG THÁI: FROZEN / COMPLETED**

Mục tiêu của bước này là biến `TokenStream` thành một cây cú pháp có cấu trúc rõ ràng, nhưng vẫn giữ đúng nguyên tắc:

> **Parser xác định cấu trúc cú pháp; Resolver xác định ý nghĩa tên; Type System xác định kiểu; Verifier xác định tính hợp lệ về ownership/capability.**

Không để parser trở thành một “semantic checker khổng lồ”.

---

# 1. Parser architecture

Pipeline:

```text
Source
  ↓
Lexer
  ↓
TokenStream
  ↓
Lossless Syntax Parser
  ↓
Green Tree
  ↓
AST Lowering
  ↓
Resolver
```

Parser có hai sản phẩm liên quan nhưng khác nhau:

```text
Lossless Syntax Tree
AST
```

---

# 2. Lossless Syntax Tree là parser output chính

Parser phải giữ được cấu trúc nguồn ngay cả khi chương trình có lỗi.

Ví dụ:

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

cây:

```text
Function
├── Keyword(fn)
├── Identifier(add)
├── ParameterList
│   ├── Parameter
│   │   ├── Identifier(a)
│   │   ├── :
│   │   └── Type(i32)
│   ├── ,
│   └── Parameter
├── ->
├── Type(i32)
└── Block
```

---

# 3. AST là semantic-oriented syntax

AST có thể bỏ:

```text
whitespace
comments
redundant punctuation representation
```

nhưng giữ:

```text
source span
expression structure
declaration structure
patterns
types
attributes
```

---

# 4. AST không chứa semantic IDs quá sớm

AST:

```text
Name("foo")
```

không nên ngay lập tức thành:

```text
FunctionId(123)
```

Resolver mới tạo:

```text
NameRef → DeclarationId
```

Điều này giữ frontend stages độc lập.

---

# 5. Top-level grammar

Module:

```text
Module
    := Item*
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
     | ModuleDecl
     | UseDecl
```

---

# 6. Function grammar

Canonical:

```text
fn name<T: Bound>(
    a: Type,
    b: Type
) -> ReturnType {
    body
}
```

Conceptual grammar:

```text
Function
    := "fn" Identifier
       GenericParams?
       ParameterList
       ReturnType?
       WhereClause?
       Block
```

---

# 7. Parameter grammar

```text
Parameter
    := Identifier ":" Type
```

Receiver:

```text
self
self: Type
```

được parser nhận diện syntactically.

Ý nghĩa method sẽ do resolver/behavior model xử lý.

---

# 8. Generic parameter grammar

```text
<T>
<T: Trait>
<T, U>
<T: Trait + OtherTrait>
```

Parser tạo:

```text
GenericParam {
    name
    bounds
}
```

Chưa giải quyết trait.

---

# 9. `where` clause

```axiom
fn process<T>(x: T)
where
    T: Ord
{
    ...
}
```

AST:

```text
WhereClause
├── Predicate
│   ├── Type(T)
│   └── Bound(Ord)
```

---

# 10. Struct grammar

```axiom
struct Point {
    x: f32
    y: f32
}
```

AST:

```text
StructDecl
├── Name
└── Fields
    ├── Field(x, f32)
    └── Field(y, f32)
```

Tuple struct:

```axiom
struct UserId(u64)
```

cũng được parser hỗ trợ.

---

# 11. Enum grammar

```axiom
enum Option<T> {
    Some(T)
    None
}
```

Variant forms:

```text
Unit
Tuple
Struct
```

Ví dụ:

```axiom
enum Message {
    Quit
    Move(x: i32, y: i32)
    Write(text: String)
}
```

---

# 12. Trait grammar

```axiom
trait Display {
    fn display(self: Self) -> String
}
```

AST chỉ biết:

```text
TraitDecl
Methods
AssociatedTypes
AssociatedConstants
Bounds
```

Trait solver xử lý semantic constraints sau.

---

# 13. Impl grammar

```axiom
impl Display for User {
    fn display(self: User) -> String {
        ...
    }
}
```

Parser không quyết định:

```text
"đây có phải implementation hợp lệ không?"
```

Nó chỉ tạo:

```text
ImplDecl {
    TraitPath?
    SelfType
    Items
}
```

---

# 14. Type grammar

Canonical:

```text
Type
    := PrimitiveType
     | Identifier
     | GenericType
     | TupleType
     | ArrayType
     | FunctionType
     | ViewType
     | MutViewType
     | NeverType
```

---

# 15. Generic type

```axiom
Vec<i32>
Option<String>
Result<User, Error>
```

AST:

```text
TypeApplication {
    base: Vec
    arguments: [i32]
}
```

---

# 16. Array type

Axiom canonical:

```axiom
[4]i32
```

AST:

```text
ArrayType {
    length: 4
    element: i32
}
```

Length expression được semantic const evaluator xử lý sau.

---

# 17. Function type

Ví dụ:

```axiom
fn(i32, i32) -> i32
```

AST:

```text
FunctionType {
    parameters
    return_type
}
```

Effects có thể được gắn ở semantic type layer thay vì làm grammar quá nặng.

---

# 18. `view`

```axiom
view<T>
```

và:

```axiom
mut_view<T>
```

là type syntax hợp lệ.

Không dùng:

```text
&T
&mut T
```

trong Core.

---

# 19. Pointer syntax

Raw pointers:

```axiom
*const T
*mut T
```

Parser nhận dạng chúng.

Nhưng unsafe legality không thuộc parser.

---

# 20. Expressions

Expression grammar là phần quan trọng nhất.

Các nhóm:

```text
Literal
Name
Path
Tuple
Array
StructLiteral
Unary
Binary
Call
MethodCall
Index
Slice
Field
If
Match
Loop
While
For
Block
Closure
Await
Cast
Try
```

---

# 21. Pratt parser

Khuyến nghị dùng **Pratt parser** cho binary/unary/postfix expressions.

Nó xử lý tốt:

```text
a + b * c
a == b && c != d
foo(a)[i].field
```

mà không cần grammar recursion cực lớn.

---

# 22. Precedence

Canonical precedence từ thấp đến cao:

```text
Assignment
Logical OR
Logical AND
Equality
Comparison
Bitwise OR
Bitwise XOR
Bitwise AND
Shift
Additive
Multiplicative
Unary
Postfix
Primary
```

Các chi tiết operator-specific phải được đóng băng trong grammar table.

---

# 23. Associativity

Ví dụ:

```text
a - b - c
```

parse:

```text
(a - b) - c
```

không:

```text
a - (b - c)
```

Assignment nếu hỗ trợ:

```text
a = b = c
```

phải có associativity được specification quy định, không để parser implementation tự chọn.

---

# 24. Unary operators

```text
-x
+x
!x
~x
```

và unsafe dereference:

```text
*x
```

AST:

```text
UnaryExpr {
    operator
    operand
}
```

---

# 25. Dereference

Parser có thể parse:

```axiom
*p
```

nhưng:

```text
unsafe required
```

là semantic verification concern.

Parser không được reject nó chỉ vì chưa thấy `unsafe`.

Điều này giúp AST biểu diễn được chương trình không hợp lệ.

---

# 26. Postfix chain

Parser phải xử lý:

```axiom
object.field
object.method()
object[i]
object[a..b]
object(...)
```

và chain:

```axiom
a.foo(x)[i].bar()
```

thành một postfix chain.

---

# 27. Method call

```axiom
point.length()
```

AST:

```text
MethodCall {
    receiver: point
    method: length
    arguments: []
}
```

Resolver sau đó canonicalize:

```text
length(point)
```

nếu method resolution thành công.

---

# 28. Function call

```axiom
foo(a, b)
```

AST:

```text
Call {
    callee: foo
    args: [a, b]
}
```

---

# 29. Index

```axiom
a[i]
```

AST:

```text
Index {
    base: a
    index: i
}
```

Compiler semantics sau này có thể lower thành indexing trait/library protocol.

---

# 30. Slice

Canonical:

```axiom
a[start..end]
```

AST:

```text
Slice {
    base
    start?
    end?
    inclusive
}
```

Ví dụ:

```text
a[..]
a[..n]
a[n..]
a[n..m]
a[n..=m]
```

---

# 31. Field access

```axiom
point.x
```

AST:

```text
FieldAccess {
    base
    field_name
}
```

Resolver kiểm tra field tồn tại.

---

# 32. Block expressions

Block:

```axiom
{
    let x = 10
    x + 20
}
```

là expression.

AST:

```text
BlockExpr {
    statements
    tail_expression?
}
```

---

# 33. Semicolon/newline

Canonical Axiom:

```axiom
let x = 10
let y = 20
```

Parser nhìn `NEWLINE` như potential terminator.

Nhưng:

```axiom
let x =
    foo()
```

không được kết thúc ở newline sau `=`.

Do đó parser có state:

```text
CanEndStatement
```

được suy ra từ grammar context.

---

# 34. Không biến indentation thành grammar

Ví dụ:

```axiom
if x {
    foo()
}
```

block structure đến từ:

```text
{ }
```

không từ spaces.

Điều này làm parser đơn giản và formatter tự do.

---

# 35. `if`

```axiom
if condition {
    ...
} else if other {
    ...
} else {
    ...
}
```

AST:

```text
IfExpr {
    condition
    then_branch
    else_branch?
}
```

---

# 36. `match`

```axiom
match x {
    Some(v) => foo(v)
    None => bar()
}
```

AST:

```text
MatchExpr {
    scrutinee
    arms
}
```

Mỗi arm:

```text
Pattern
Guard?
Arrow
Expression
```

---

# 37. Pattern grammar

Pattern groups:

```text
Wildcard
Identifier
Literal
Tuple
Struct
EnumVariant
Array
Range
OrPattern
```

Ví dụ:

```axiom
Some(x)
Point { x, y }
(a, b)
0..10
```

---

# 38. Pattern parser không kiểm tra exhaustiveness

Ví dụ:

```axiom
match x {
    Some(v) => v
}
```

parser vẫn tạo AST.

Exhaustiveness checker sau đó phát:

```text
pattern not exhaustive
```

---

# 39. `loop`

```axiom
loop {
    ...
}
```

AST:

```text
LoopExpr {
    body
}
```

---

# 40. `while`

```axiom
while condition {
    ...
}
```

AST:

```text
WhileExpr {
    condition
    body
}
```

---

# 41. `for`

```axiom
for x in values {
    use(x)
}
```

Parser tạo:

```text
ForExpr {
    pattern
    iterable
    body
}
```

Lowering thành iterator protocol là HIR concern.

---

# 42. `break` / `continue`

```axiom
break
continue
```

có thể mang value nếu specification cho phép.

Ví dụ:

```axiom
loop {
    if done {
        break result
    }
}
```

Nếu Core v1 hỗ trợ block expression + loop value, parser phải giữ value expression.

---

# 43. Closure

```axiom
|x| x + 1
```

hoặc:

```axiom
|x, y| {
    x + y
}
```

AST:

```text
ClosureExpr {
    parameters
    body
}
```

Capture mode chưa quyết định ở parser.

---

# 44. Async

```axiom
async fn foo() {
    ...
}
```

và:

```axiom
value.await
```

parser nhận syntax.

Async lowering diễn ra sau HIR.

---

# 45. Try operator

```axiom
result?
```

AST:

```text
TryExpr {
    operand
}
```

Không parse thành exception.

---

# 46. Cast

```axiom
value as i64
```

AST:

```text
CastExpr {
    value
    target_type
}
```

CAST vs BITCAST được semantic/type checker quyết định.

---

# 47. Attributes

```axiom
@repr(C)
struct Foo { ... }
```

AST:

```text
Attribute {
    path
    arguments
}
```

Parser không biết `repr` có hợp lệ không.

Attribute resolver/semantic checker chịu trách nhiệm.

---

# 48. Attribute grammar

Canonical:

```text
@name
@name(...)
@path::name(...)
```

Arguments có thể là:

```text
literal
identifier/path
type
key=value
```

nhưng không nên biến attributes thành một procedural macro language.

---

# 49. Visibility

Parser nhận:

```text
pub
pub(module)
pub(package)
```

và gắn visibility syntax vào declaration.

Resolver kiểm tra visibility semantics.

---

# 50. Module/import

```axiom
module graphics::render
```

và:

```axiom
use graphics::render::Renderer
```

AST giữ path segment nguyên vẹn.

Resolution xảy ra sau.

---

# 51. Generic ambiguity

Ví dụ:

```axiom
foo<T>(x)
```

Parser phải có khả năng phân biệt:

```text
generic arguments
```

với:

```text
comparison operators
```

mà không dựa vào semantic type lookup quá sớm.

---

# 52. Parser contextual lookahead

Axiom có thể dùng bounded lookahead.

Ví dụ:

```text
identifier < ...
```

parser kiểm tra cấu trúc token phía sau để xác định syntactic production.

Không được:

```text
"đi hỏi TypeDB để parse"
```

nếu có thể tránh.

---

# 53. Parser ambiguity rule

Nếu grammar cho phép hai parse hợp lệ:

```text
P1
P2
```

thì phải:

1. thiết kế grammar để loại ambiguity, hoặc
2. quy định precedence/associativity/lookahead rõ ràng.

Không dùng:

```text
random parser choice
```

---

# 54. Error recovery architecture

Parser cần:

```text
RecoveryCursor
ErrorNode
MissingToken
SkippedTokens
```

Mục tiêu:

> Một lỗi cú pháp không nên khiến 100 lỗi tiếp theo chỉ là hậu quả giả.

---

# 55. Recovery strategy

Ba chiến lược:

```text
Insertion
Deletion
Synchronization
```

### Insertion

Thiếu:

```text
)
```

parser tạo synthetic token.

### Deletion

Token thừa:

```text
)
```

parser bỏ qua trong recovery node.

### Synchronization

Khi không hiểu expression:

```text
```

nhảy tới token an toàn:

```text
}
NEWLINE
,
)
```

---

# 56. Recovery cost

Không được recovery quá “thông minh”.

Parser không nên sửa source hàng chục cách rồi chọn phương án “có vẻ đúng”.

Chỉ sử dụng deterministic recovery.

---

# 57. Causal diagnostics

Ví dụ:

```axiom
fn foo(
    x: i32
{
```

Diagnostic root:

```text
expected ')'
```

Các lỗi sau có thể đánh dấu:

```text
dependent on previous parse error
```

thay vì phát 30 lỗi độc lập.

---

# 58. Error node

AST có:

```text
ErrorExpr
ErrorType
ErrorPattern
ErrorItem
```

nhưng các node này chỉ tồn tại Partial Semantic Mode.

Production compiler không được để chúng vào Verified MIR.

---

# 59. Missing token

Ví dụ:

```axiom
foo(a, b
```

parser có thể tạo:

```text
Call
├── foo
├── (
├── a
├── ,
├── b
└── MissingToken(")")
```

IDE vẫn có thể hiểu phần lớn file.

---

# 60. Recovery source spans

Synthetic token:

```text
span = zero-width insertion point
```

Ví dụ:

```text
foo(a, b
       ^
```

diagnostic có thể highlight vị trí thiếu `)`.

---

# 61. AST source provenance

Mọi AST node:

```text
AstNode {
    kind
    span
}
```

đều có source span.

Derived nodes có thể có:

```text
origin_span
```

nếu được sinh trong lowering.

---

# 62. AST arena

AST node nên được lưu trong arena:

```text
AstArena
```

và reference bằng:

```text
AstNodeId
```

thay vì pointer ownership phức tạp.

Điều này cũng phù hợp với CompilerDB.

---

# 63. AST IDs

```text
AstNodeId
ExprId
StmtId
TypeSyntaxId
PatternId
ItemId
```

Có thể là typed generational/index IDs.

---

# 64. Parser performance

Mục tiêu:

```text
O(n)
```

với:

- single token stream
- bounded lookahead
- arena allocation
- no recursive copying of subtrees
- immutable green tree reuse

Parser recursion depth phải được bảo vệ trước source cực sâu.

---

# 65. Deep nesting

Input:

```text
((((((((...
```

không được khiến compiler stack overflow một cách dễ dàng.

Parser có thể:

```text
explicit parser stack
```

hoặc giới hạn nesting và phát diagnostic rõ ràng.

---

# 66. Incremental parser

Khi token region thay đổi:

```text
old GreenTree
      +
changed tokens
      ↓
reparse smallest affected node
```

Các subtree không bị ảnh hưởng được reuse.

---

# 67. AST lowering incremental

AST không nhất thiết rebuild toàn bộ.

CompilerDB query:

```text
AST(ModuleId)
```

có thể reuse các declaration nodes chưa thay đổi.

---

# 68. Parser determinism

Cùng token stream:

```text
T
```

phải luôn tạo:

```text
SyntaxTree(T)
```

giống nhau về semantic structure.

Không phụ thuộc:

```text
thread scheduling
hash iteration
memory addresses
```

---

# 69. Parser testing

Bắt buộc:

```text
valid syntax
invalid syntax
recovery
nested structures
deep expressions
generic ambiguity
Unicode identifiers
newline rules
comments
attributes
patterns
closures
async
raw pointers
types
```

---

# 70. Parser fuzzing

Fuzzer phải có:

```text
random bytes
valid token sequences
mutated valid programs
random nesting
random delimiter deletion
random token insertion
```

Mục tiêu đầu tiên:

> **Parser không crash.**

Sau đó:

> recovery phải tiến tới EOF.

---

# 71. Round-trip property

Với source hợp lệ:

```text
Source
 ↓
Lexer
 ↓
Parser
 ↓
Lossless Tree
 ↓
Reconstruct
```

phải bảo toàn source tương đương byte-level trong lossless representation.

Với formatter:

```text
Source
 ↓
Parse
 ↓
Format
 ↓
Parse
```

phải bảo toàn semantic AST tương đương.

---

# 72. Parser ↔ AST invariant

```text
PARSE-20
Every valid token sequence accepted by the grammar has a deterministic parse.

PARSE-21
Parser structure is independent of semantic name resolution.

PARSE-22
Parser structure is independent of type inference.

PARSE-23
Parser structure is independent of ownership verification.

PARSE-24
Parser preserves exact source spans.

PARSE-25
Lossless syntax preserves sufficient information for source reconstruction.

PARSE-26
AST preserves all semantic-relevant syntax.

PARSE-27
Trivia does not alter AST semantics.

PARSE-28
Comments do not alter program semantics.

PARSE-29
Newline termination is grammar-sensitive rather than indentation-sensitive.

PARSE-30
Indentation does not define block structure.

PARSE-31
Operator precedence and associativity are deterministic.

PARSE-32
Expression parsing uses a formally defined precedence model.

PARSE-33
Postfix expressions associate deterministically.

PARSE-34
Generic syntax ambiguity must be resolved by grammar/contextual syntax, not semantic guessing.

PARSE-35
Pattern syntax is parsed independently from exhaustiveness verification.

PARSE-36
Attribute syntax is parsed independently from attribute semantic validation.

PARSE-37
Method syntax is parsed independently from method resolution.

PARSE-38
Raw pointer syntax is parsed independently from unsafe verification.

PARSE-39
Async syntax is parsed independently from async legality verification.

PARSE-40
Recovery must make forward progress.

PARSE-41
Recovery must be deterministic.

PARSE-42
Synthetic tokens must be explicitly marked.

PARSE-43
Recovery nodes cannot establish production semantic validity.

PARSE-44
Diagnostics should distinguish root syntax errors from dependent recovery errors.

PARSE-45
Parser errors must not crash the compiler.

PARSE-46
Deep nesting must be bounded or handled safely.

PARSE-47
Incremental parsing must reuse unaffected syntax subtrees where possible.

PARSE-48
AST lowering must preserve source provenance.

PARSE-49
Equivalent valid source must produce semantically equivalent ASTs.

PARSE-50
Formatter round-tripping must preserve semantic structure.

PARSE-51
Lossless reconstruction must preserve source representation.

PARSE-52
Parser behavior must be deterministic across platforms.

PARSE-53
Parser must not silently reinterpret malformed source as valid source.

PARSE-54
Partial syntax is valid only inside Partial Semantic Mode.

PARSE-55
Production code generation requires complete syntax.

PARSE-56
Parser implementation must remain replaceable without changing language semantics.
```

---

# 73. Frontend sau 237

Axiom frontend hiện có architecture:

```text
                    SourceDB
                       │
                       ▼
                   UTF-8 text
                       │
                       ▼
                     Lexer
                       │
                       ▼
                  TokenStream
                       │
                       ▼
              Lossless Green Tree
                       │
                       ▼
                     AST
                       │
                       ▼
                  Declaration
                   Resolution
                       │
                       ▼
                      HIR
```

Và boundary rất rõ:

```text
Lexer
  → syntax

Parser
  → structure

Resolver
  → identity

Type System
  → types

Trait Solver
  → behavior constraints

MIR
  → executable semantics

Verifier
  → legality
```

Đây là separation rất quan trọng để compiler không biến thành một khối logic khó bảo trì.

---

# TASK TIẾP THEO

## **BOOTSTRAP-238 — AXIOM NAME RESOLUTION, MODULE SYSTEM & SYMBOL GRAPH**

Bước tiếp theo sẽ giải quyết một trong những phần dễ trở thành “mớ spaghetti” nhất của compiler:

```text
AST
 ↓
Module Graph
 ↓
Namespaces
 ↓
Imports
 ↓
Exports
 ↓
Name Resolution
 ↓
Overload/Method Candidate Discovery
 ↓
DeclarationId
 ↓
Semantic Symbol Graph
```

Đặc biệt sẽ đóng đinh:

- module/package boundary
- `use`
- `pub`
- `pub(module)`
- `pub(package)`
- private symbols
- type/value/trait namespaces
- shadowing
- local scope
- block scope
- generic scope
- associated items
- extension methods
- import cycles
- re-export
- ambiguous names
- declaration identity
- symbol graph
- incremental resolution
- **không cho resolver “đoán” symbol khi có nhiều candidate hợp lệ**.