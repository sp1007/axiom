# BOOTSTRAP-222 — AXIOM FRONTEND IMPLEMENTATION SPECIFICATION

**TRẠNG THÁI: FROZEN / COMPLETED**

Mục tiêu của 222 là khóa hoàn toàn frontend từ source text đến **Resolved AST**:

```text
Source
  ↓
UTF-8 validation
  ↓
Lexer
  ↓
Lossless Syntax Tree
  ↓
AST
  ↓
Module/Scope construction
  ↓
Name resolution
  ↓
Method / operator / generic resolution
  ↓
Resolved AST
```

Nguyên tắc quan trọng:

> **Frontend không được suy diễn semantic quá mức. Nó phải bảo toàn thông tin source, nhưng đồng thời phải tạo đủ resolution facts để HIR không phải quay lại đọc syntax mơ hồ.**

---

# 1. Frontend architecture

```text
compiler/
├── source/
├── lexer/
├── syntax/
├── parser/
├── ast/
├── resolve/
└── frontend/
```

Luồng dữ liệu:

```text
SourceFileId
      │
      ▼
TokenStream
      │
      ▼
LosslessSyntaxTree
      │
      ▼
AST
      │
      ├── ModuleTree
      ├── ScopeTree
      └── DeclarationIndex
              │
              ▼
        ResolutionMap
              │
              ▼
        ResolvedAST
```

---

# 2. UTF-8 là boundary đầu tiên

Axiom source mặc định là UTF-8.

Compiler phải validate UTF-8 trước khi lexer chạy.

```text
bytes
 ↓
UTF8 validation
 ↓
Unicode scalar stream
 ↓
lexer
```

Invalid UTF-8:

```text
AXUTF-001
Invalid UTF-8 source encoding
```

Không tự sửa byte.

---

# 3. Character model

Lexer không được dùng “ASCII character” làm abstraction chính.

Các mức:

```text
Byte
UnicodeScalar
GraphemeCluster
```

Lexer chủ yếu cần:

```text
UnicodeScalar
```

Identifier normalization và Unicode security có quy tắc riêng.

---

# 4. Identifier

Canonical identifier:

```text
Identifier {
    symbol: SymbolId
    span: SourceSpan
}
```

`SymbolId` được intern.

Ví dụ:

```axiom
velocity
```

không tạo vô số string `"velocity"` trong compiler.

```text
"velocity"
   ↓
SymbolId(42)
```

---

# 5. Identifier rules

Axiom v1:

- Unicode identifiers được phép.
- chữ cái Unicode và `_` có thể mở đầu theo identifier profile.
- Unicode combining marks phù hợp có thể tiếp tục identifier.
- keyword không phải identifier thông thường trong grammar.
- compiler phải có reserved-word table.

Ví dụ:

```axiom
tốc_độ
Δvalue
数据
```

có thể hợp lệ nếu thỏa identifier profile.

---

# 6. Unicode normalization

Không tự động normalize identifier theo kiểu làm thay đổi source identity.

Compiler phải xác định canonical policy.

Khuyến nghị:

```text
Source spelling
      ↓
preserve exactly

Identifier semantic identity
      ↓
Unicode security/canonical comparison policy
```

Hai identifier nhìn giống nhau nhưng khác scalar sequence phải không được âm thầm hợp nhất nếu policy không cho phép.

---

# 7. Keyword table

Lexer nhận diện:

```text
fn
let
mut
struct
enum
trait
impl
type
const
comptime
if
else
loop
while
for
in
match
break
continue
return
async
await
pub
module
use
extern
unsafe
true
false
```

và các keyword/soft-keyword được khóa trong syntax spec.

Không hard-code keyword logic rải rác trong parser.

---

# 8. Token model

```text
Token {
    kind: TokenKind
    span: SourceSpan
    flags: TokenFlags
}
```

`TokenKind`:

```text
Identifier(SymbolId)

Keyword(Keyword)

IntegerLiteral
FloatLiteral

StringLiteral
ByteStringLiteral
CharLiteral

Punctuation(PunctuationKind)
Operator(OperatorKind)

Newline
Indentation?        // nếu cần parser bookkeeping
EOF
Invalid
```

Axiom không cần indentation-sensitive grammar, nên **Indentation không phải semantic token**.

---

# 9. Trivia

Trivia phải được giữ trong lossless layer:

```text
Whitespace
Newline
LineComment
BlockComment
```

Không nhất thiết đưa trivia vào AST.

---

# 10. Newline semantics

Axiom dùng newline-sensitive statement termination.

Nhưng lexer không tự quyết định:

> “newline này chắc chắn kết thúc statement.”

Lexer chỉ emit:

```text
Newline
```

Parser quyết định dựa trên grammar.

Điều này tránh các lỗi kiểu:

```axiom
let x =
    foo()
    + bar()
```

newline không thể tùy tiện cắt expression.

---

# 11. Semicolon

Canonical syntax không cần semicolon.

Parser có thể chấp nhận:

```axiom
let x = 10;
let y = 20;
```

trong compatibility mode.

Formatter chuyển thành:

```axiom
let x = 10
let y = 20
```

Semicolon không nên trở thành semantic AST node nếu chỉ là statement terminator syntax.

---

# 12. Numeric literals

Phải hỗ trợ tối thiểu:

```text
decimal
hex
binary
octal

integer suffix
float suffix

exponent
digit separators
```

Ví dụ:

```axiom
42
1_000_000
0xff
0b1010
0o755

3.14
1.2e-5

42u64
3.14f32
```

Lexer lưu raw spelling.

AST lưu parsed literal representation.

---

# 13. Literal parsing không dùng floating-point host để parse

Ví dụ:

```text
1.0000000000000001
```

không được:

```text
source
→ host f64
→ Axiom f64
```

nếu điều đó làm mất thông tin trước semantic checking.

Literal parser phải tạo:

```text
IntegerLiteralValue
FloatLiteralSyntax
```

sau đó semantic layer mới convert sang target type.

---

# 14. String literals

Axiom cần phân biệt:

```text
StringLiteral
ByteStringLiteral
CharLiteral
```

Ví dụ:

```axiom
"hello"
b"hello"
'a'
```

String escape được parse thành semantic characters/code points sau lexer hoặc literal parser, nhưng raw source vẫn phải giữ trong syntax tree.

---

# 15. Raw strings

Nên hỗ trợ raw string ngay từ frontend architecture:

```axiom
r"c:\temp\file.txt"
```

và delimiter mở rộng nếu cần:

```axiom
r#"..."#
```

Điều này đặc biệt hữu ích cho:

- regex;
- JSON;
- shader;
- embedded source;
- test fixtures.

---

# 16. Comments

Line:

```axiom
// comment
```

Block:

```axiom
/* comment */
```

Block comment nên cho phép nesting:

```axiom
/*
    outer
    /*
        inner
    */
*/
```

Điều này làm lexer đơn giản hơn về mặt deterministic parsing và hữu ích cho tooling.

---

# 17. Operator lexer

Operators phải có bảng canonical:

```text
+
-
*
/
%
==
!=
<
>
<=
>=
&&
||
!
=
+=
-=
*= 
/=
..
..=
.
?
:
::
-> 
=> 
@
|
&
```

Nhưng lexer dùng **maximal munch**.

Ví dụ:

```text
>>=
```

được nhận diện theo operator table thay vì:

```text
>
>
=
```

trừ khi grammar yêu cầu tách.

---

# 18. `>>` trong generic syntax

Frontend phải tránh vấn đề parser kiểu C++ cũ:

```axiom
Vec<Vec<i32>>
```

`>>` ở đây phải có thể được parser hiểu là:

```text
>
>
```

contextually.

Do đó tokenization của shift/operator và generic close phải được thiết kế cùng parser contract.

Không nên làm lexer phụ thuộc semantic type information.

---

# 19. Punctuation

Tách:

```text
(
)
[
]
{
}
,
:
::
.
@
```

khỏi identifier/operator để parser dễ xử lý.

---

# 20. Lossless Syntax Tree

LST là representation chính cho:

- formatter;
- IDE;
- refactoring;
- source-preserving transformations;
- diagnostics.

Cấu trúc:

```text
SyntaxNode {
    kind
    children
    token_range
    source_span
}
```

Token leaf giữ raw source.

---

# 21. Syntax tree không được dùng pointer ownership graph

Không:

```text
Node {
    parent: *Node
    children: Vec<*Node>
}
```

theo kiểu runtime tree.

Dùng:

```text
SyntaxNodeId
SyntaxTokenId
```

và arena/database.

---

# 22. Green/Red tree

Frontend có thể dùng kiến trúc kiểu:

```text
GreenTree
    immutable
    parentless

RedTree
    contextual wrapper
    parent navigation
```

Khuyến nghị Axiom:

> **Green tree là persistent semantic-independent syntax representation.**

Red/context wrappers có thể lazy tạo khi IDE cần.

---

# 23. Incremental parsing

Khi sửa:

```text
foo.ax
```

chỉ vùng syntax bị ảnh hưởng cần parse lại.

Ví dụ:

```text
old tree
       ↓
text edit
       ↓
relex affected region
       ↓
incremental parse
       ↓
reuse unaffected green nodes
```

Không bắt buộc MVP phải tối ưu hoàn hảo, nhưng API phải không khóa đường này.

---

# 24. Parser architecture

Parser dùng Pratt parser hoặc precedence-climbing cho expressions.

```text
parse_expr(min_precedence)
```

Statement/declaration dùng recursive descent.

Do đó:

```text
Declarations → Recursive Descent
Statements   → Recursive Descent
Expressions   → Pratt
Types         → Recursive Descent + postfix handling
Patterns      → Recursive Descent
```

Đây là lựa chọn phù hợp với grammar Axiom hiện tại.

---

# 25. Expression precedence

Phải khóa một bảng duy nhất.

Từ thấp đến cao, khái quát:

```text
assignment
?
||
&&
comparisons
bitwise
shift
range
add/sub
mul/div/mod
unary
postfix
primary
```

Method call/index/field:

```text
foo.bar()
foo[i]
foo.field
```

ở postfix level.

---

# 26. Assignment không phải expression value thông thường

Khuyến nghị:

```axiom
x = y
```

là assignment expression/statement semantic có `unit` result hoặc grammar giới hạn theo statement context.

Không để:

```axiom
let z = (x = y)
```

trở thành cơ chế mặc định kiểu C nếu không có lý do rõ ràng.

Mục tiêu giảm ambiguity và side effects khó đọc.

---

# 27. Blocks

Block:

```axiom
{
    statement
    statement
    expression
}
```

có thể là expression.

Ví dụ:

```axiom
let x = {
    let a = 10
    a * 2
}
```

AST:

```text
BlockExpr {
    statements[]
    tail_expr?
}
```

---

# 28. Function syntax AST

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

AST:

```text
FunctionDecl {
    name
    generics
    params
    return_type
    body
    attributes
    visibility
}
```

---

# 29. Struct AST

```axiom
struct Point {
    x: f32
    y: f32
}
```

AST:

```text
StructDecl {
    name
    generics
    fields[]
    attributes
    visibility
}
```

Field:

```text
FieldDecl {
    name
    type
    attributes
    visibility
}
```

---

# 30. Tuple struct

```axiom
struct UserId(u64)
```

AST dùng cùng semantic declaration family:

```text
StructShape =
    NamedFields
    TupleFields
    Unit
```

Không tạo một “class” đặc biệt.

---

# 31. Enum AST

```axiom
enum Result<T, E> {
    Ok(T)
    Err(E)
}
```

```text
EnumDecl {
    name
    generics
    variants[]
}
```

Variant:

```text
VariantDecl {
    name
    fields
}
```

---

# 32. Trait / impl AST

```axiom
trait Display {
    fn display(self: view<Self>) -> String
}
```

```text
TraitDecl
```

và:

```axiom
impl Display for User {
    fn display(...) { ... }
}
```

```text
ImplDecl {
    trait_path?
    self_type
    generics
    items[]
}
```

---

# 33. Generic parameter AST

```axiom
fn max<T: Ord>(a: T, b: T) -> T
```

```text
GenericParam {
    name
    kind
    bounds[]
}
```

Các kind ban đầu:

```text
Type
Const
```

Lifetime parameter **không tồn tại trong source syntax**.

---

# 34. `where` clause

```axiom
fn foo<T, U>(x: T, y: U)
where
    T: Add<U>
    U: Copy
```

AST:

```text
WhereClause {
    predicates[]
}
```

Không flatten vào generic parameter nếu cần giữ source structure cho formatter.

---

# 35. Pattern AST

```text
Pattern =
    Wildcard
    Binding
    Literal
    Tuple
    Struct
    EnumVariant
    Array
    Range
    Or
```

Ví dụ:

```axiom
match value {
    Some(x) => x
    None => 0
}
```

Pattern tree được preserve riêng.

---

# 36. Name resolution architecture

Sau AST:

```text
AST
 ↓
Module tree
 ↓
Scope graph
 ↓
Declaration index
 ↓
Name resolution
```

Không resolve bằng cách search toàn bộ AST mỗi lần.

---

# 37. Module tree

Ví dụ:

```text
module app
├── main
├── graphics
│   ├── render
│   └── texture
└── math
```

Mỗi module:

```text
ModuleId
ParentModuleId
Children[]
Declarations[]
Imports[]
Visibility
```

---

# 38. Scope tree

Scope kinds:

```text
ModuleScope
FunctionScope
BlockScope
LoopScope
MatchArmScope
ClosureScope
ComptimeScope
PatternScope
```

Mỗi scope:

```text
ScopeId
ParentScopeId
Bindings
```

---

# 39. Declaration index

Mỗi declaration được indexed:

```text
Name
Namespace
DeclarationId
Visibility
Module
SourceSpan
```

Axiom nên có namespace distinction cho:

```text
Type namespace
Value namespace
Module namespace
Trait namespace
```

để tránh ambiguity không cần thiết.

---

# 40. Name resolution

Lookup:

```text
lookup(scope, name, namespace)
```

thứ tự:

```text
local scope
 ↓
parent scope
 ↓
function/module imports
 ↓
module
 ↓
package exports
```

Không tìm kiếm global universe một cách mơ hồ.

---

# 41. Shadowing

Cho phép:

```axiom
let x = 10

{
    let x = 20
    print(x)
}
```

inner `x` thắng outer `x`.

Nhưng:

```text
shadowing ≠ mutation
```

và mỗi binding có `DeclarationId` khác.

---

# 42. Duplicate declarations

Cùng scope:

```axiom
let x = 1
let x = 2
```

nếu grammar/semantic policy không cho phép shadowing cùng scope:

```text
ARESOLVE-001
Duplicate binding
```

Không tự chọn declaration sau.

---

# 43. Imports

Ví dụ:

```axiom
use math::sqrt
use graphics::render::Renderer
```

AST:

```text
UseDecl {
    path
    alias?
    import_kind
}
```

Import kinds:

```text
Single
Group
Glob
```

Nếu Axiom Core không muốn glob ở initial version thì library/tooling có thể giới hạn; nhưng resolver architecture vẫn phải có explicit import set.

---

# 44. Import cycle

Module import cycle không nhất thiết là package dependency cycle.

Ví dụ:

```text
A → B
B → A
```

có thể được phép nếu semantic dependency không tạo initialization cycle.

Resolver phải phân biệt:

```text
Name dependency
Type dependency
Initialization dependency
Package dependency
```

Không dùng một graph cho tất cả.

---

# 45. Visibility

Resolution phải kiểm tra:

```text
private
pub(module)
pub(package)
pub
```

Visibility là semantic fact.

Không để HIR phải tự kiểm tra lại visibility.

---

# 46. Method resolution

Axiom method syntax:

```axiom
v.length()
```

semantic lookup:

```text
1. inherent function
2. trait method
3. imported extension method
4. generic extension
```

Nếu có nhiều candidate cùng mức:

```text
ambiguity
```

Không heuristic.

---

# 47. Inherent methods

```axiom
impl Vec2 {
    fn length(self: Vec2) -> f32 { ... }
}
```

Method table:

```text
MethodKey {
    receiver_type
    method_name
}
```

---

# 48. Trait methods

```axiom
impl Length for Vec2 {
    fn length(self: Vec2) -> f32
}
```

Resolver tạo:

```text
MethodCandidate {
    function_id
    source_trait?
    receiver_adjustment
    generic_substitutions
}
```

Trait solving thực sự thuộc BOOTSTRAP-224, nhưng frontend phải tạo candidate set.

---

# 49. Extension methods

Nếu:

```axiom
use math::VectorExt
```

thì extension methods của module/trait đó được đưa vào candidate set.

Không scan toàn package universe.

Đây vừa nhanh vừa tránh ambiguity.

---

# 50. Operator resolution

Ví dụ:

```axiom
a + b
```

Frontend normalize thành:

```text
operator candidate
```

không trực tiếp biến thành hard-coded function name nếu trait resolution chưa hoàn tất.

HIR cuối cùng sẽ chứa resolved operator function.

---

# 51. Generic function call

```axiom
max::<i32>(a, b)
```

AST giữ explicit generic arguments.

Nếu:

```axiom
max(a, b)
```

AST không tự điền `i32`.

Type inference/resolution phase sẽ tạo substitution:

```text
T = i32
```

---

# 52. Generic ambiguity

Ví dụ có thể suy ra:

```text
T = ?
```

Nếu nhiều substitution hợp lệ:

```text
AMBIGUOUS
```

Không chọn candidate dựa trên declaration order.

---

# 53. Overload model

Axiom không nên biến overload thành một hệ thống dynamic dispatch phức tạp.

Function names có thể overload nếu spec cho phép, nhưng resolver phải tạo:

```text
CandidateSet
```

và chọn duy nhất dựa trên deterministic ranking:

```text
exact match
safe coercion
generic instantiation
trait-based conversion
```

Nếu hòa:

```text
compile error
```

---

# 54. Coercion không thuộc lexer/parser

Ví dụ:

```axiom
foo(string)
```

và argument là `String`.

Việc:

```text
String → Str
```

là semantic coercion.

Frontend chỉ giữ expression structure.

Type system quyết định coercion.

---

# 55. `view` syntax

```axiom
let p = view(point)
```

AST:

```text
ViewExpr {
    operand
    mutable: false
}
```

Không biến thành raw pointer.

---

# 56. Implicit ephemeral view

```axiom
fn print_point(p: view<Point>)

print_point(point)
```

AST vẫn có argument:

```text
NameExpr(point)
```

Type checker/HIR mới tạo:

```text
MakeView(point)
```

Điều này rất quan trọng:

> Lexer/parser không được biết ownership/capability semantics.

---

# 57. Raw pointer syntax

```axiom
*const T
*mut T
```

được parser như type syntax.

Deref:

```axiom
*p
```

là unary expression.

Field:

```axiom
p->field
```

là postfix syntax.

Unsafe verification thuộc semantic verifier.

---

# 58. Attribute syntax

Generic attribute AST:

```text
Attribute {
    path
    arguments
    span
}
```

Ví dụ:

```axiom
@repr(C)
@derive(Clone)
@kernel
@cfg(windows)
```

Parser không hard-code toàn bộ semantics của attributes.

Semantic registry xử lý:

```text
AttributeKind
```

---

# 59. Attribute registry

Compiler-known attributes:

```text
repr
abi
target
cfg
derive
kernel
constant_time
export
```

Unknown attribute:

- error nếu không được phép;
- hoặc preserve nếu extension/profile cho phép.

Không được silently ignore attribute semantic.

---

# 60. Resolved AST

AST:

```text
NameExpr {
    name = "x"
}
```

Resolved AST:

```text
ResolvedNameExpr {
    declaration = LocalId(...)
}
```

Tức là HIR không phải lookup tên lần nữa.

---

# 61. ResolutionMap

Không nhất thiết phải copy toàn bộ AST.

Có thể:

```text
ExprId → Resolution
PatternId → BindingResolution
PathId → DeclarationId
CallId → CandidateSet / ResolvedFunction
```

AST + ResolutionMap = Resolved AST semantic view.

Điều này tiết kiệm memory.

---

# 62. Frontend invariants

Sau resolution:

```text
Every resolved name → exactly one semantic declaration
```

ngoại lệ:

```text
unresolved recovery node
```

chỉ tồn tại Partial Semantic Mode.

Production compiler không cho unresolved nodes đi vào Verified MIR.

---

# 63. Partial program semantics

IDE có thể có:

```text
let x =
```

AST:

```text
MissingExpr
```

Resolver:

```text
Incomplete
```

Type:

```text
Unknown
```

Nhưng:

```text
Unknown ≠ valid type
```

Không được compile executable.

---

# 64. Diagnostic codes frontend

Đề xuất:

```text
AXUTF-xxx    UTF-8
AXLEX-xxx    Lexer
AXPARSE-xxx  Parser
AXNAME-xxx   Name resolution
AXMOD-xxx    Module
AXVIS-xxx    Visibility
AXPATH-xxx   Path
AXMETHOD-xxx Method resolution
AXGEN-xxx    Generic resolution
```

Code ổn định, message có thể thay đổi.

---

# 65. Frontend testing

Cấu trúc:

```text
tests/frontend/
├── lexer/
├── parser/
├── syntax/
├── ast/
├── modules/
├── names/
├── imports/
├── methods/
├── generics/
├── visibility/
└── recovery/
```

---

# 66. Lexer tests

Phải có:

```text
ASCII identifiers
Unicode identifiers
keywords
numbers
floats
strings
escapes
raw strings
comments
nested comments
operators
newlines
invalid UTF-8
invalid literals
```

---

# 67. Parser tests

Positive:

```text
functions
structs
enums
traits
impl
generics
where
match
loops
closures
async
comptime
attributes
unsafe
FFI
GPU annotations
```

Negative:

```text
missing brace
missing type
missing expression
invalid pattern
unclosed string
bad generic
bad attribute
```

---

# 68. Lossless round-trip test

Một test cực kỳ quan trọng:

```text
source
 ↓
parse
 ↓
lossless tree
 ↓
reconstruct source
```

phải:

```text
reconstructed_source == original_source
```

ít nhất trong canonical lossless mode.

Đây là invariant mạnh cho formatter/IDE.

---

# 69. Formatter test

Formatter:

```text
source
 ↓
AST/LST
 ↓
format
 ↓
parse
```

phải giữ semantic identity.

Không chỉ so sánh text.

Test:

```text
parse(source)
→ semantic fingerprint A

format(source)
→ parse
→ semantic fingerprint B

A == B
```

---

# 70. Name resolution test

Ví dụ:

```axiom
let x = 10

{
    let x = 20
    use(x)
}
```

phải chứng minh:

```text
use(x)
→ inner x
```

không chỉ kiểm tra output.

---

# 71. Method resolution test

Phải test:

```text
inherent wins
trait candidate
extension candidate
generic extension
ambiguity
visibility
generic receiver
```

---

# 72. Frontend performance

MVP:

```text
lex: O(n)
parse: O(n)
scope construction: O(n)
declaration indexing: O(n)
```

Resolver thường:

```text
O(n log n)
```

hoặc gần O(n) với interned symbols/hash maps.

Không scan toàn AST cho mỗi name lookup.

---

# 73. Incremental frontend

Khi thay đổi một function body:

```text
source edit
 ↓
lex affected region
 ↓
parse affected syntax
 ↓
reuse unchanged syntax nodes
 ↓
rebuild affected AST
 ↓
invalidate affected scopes/resolution
```

Declaration signatures không đổi thì downstream semantic cache có thể tiếp tục sử dụng.

---

# 74. Frontend không được biết backend

Frontend tuyệt đối không import:

```text
backend
object
linker
register allocator
```

Dependency:

```text
lexer
 ↓
syntax
 ↓
parser
 ↓
AST
 ↓
resolve
 ↓
types
```

không:

```text
frontend → x86
```

---

# 75. Frontend boundary

Sau 222, boundary chính thức là:

```text
ResolvedAST
```

Invariant:

```text
Syntax complete
+
Names resolved
+
Visibility checked
+
Imports resolved
+
Method/operator candidate resolution prepared
+
Generic paths resolved
```

Nhưng **type inference chưa hoàn tất**.

---

# 76. Điều frontend KHÔNG được làm

Frontend không được:

```text
infer ownership
infer Copy
infer Drop
infer Send
infer Share
perform alias analysis
choose memory layout
generate machine code
```

Những việc đó thuộc semantic/compiler backend tương ứng.

---

# 77. Frontend → Type System boundary

Input:

```text
ResolvedAST
```

Output tiếp theo:

```text
TypedHIR
```

Type checker chịu trách nhiệm:

```text
type inference
unification
generic substitution
coercion
trait obligations
operator typing
closure typing
view typing
ownership-relevant type properties
```

---

# 78. Frontend implementation milestone

**Milestone F1:**

```axiom
fn main() -> i32 {
    42
}
```

→ parsed → resolved.

**Milestone F2:**

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

→ operator candidate resolved.

**Milestone F3:**

```axiom
struct Point {
    x: i32
    y: i32
}
```

→ declaration/index/resolution.

**Milestone F4:**

```axiom
module math
use math::add
```

→ module/import resolution.

**Milestone F5:**

```axiom
trait Length { ... }
impl Length for Vec2 { ... }
```

→ candidate set.

---

# 79. Frontend acceptance gate

Không được chuyển sang Type System implementation hoàn chỉnh nếu chưa đạt:

```text
✓ UTF-8 correctness
✓ lexer conformance
✓ lossless parse round-trip
✓ AST construction
✓ syntax recovery
✓ module tree
✓ scope tree
✓ declaration index
✓ import resolution
✓ visibility
✓ name resolution
✓ method candidate discovery
✓ generic path resolution
✓ deterministic output
✓ incremental invalidation baseline
✓ structured diagnostics
```

---

# 80. Invariants của BOOTSTRAP-222

```text
AFRONT-20
Axiom source is UTF-8 by default.

AFRONT-21
Invalid UTF-8 is rejected before semantic compilation.

AFRONT-22
Lexing is deterministic and context-independent except for explicitly defined lexical modes.

AFRONT-23
The lossless syntax representation preserves source text and trivia.

AFRONT-24
Parser recovery never silently invents semantic declarations.

AFRONT-25
Newline termination is determined by grammar, not by the lexer alone.

AFRONT-26
Identifiers have stable interned semantic identity.

AFRONT-27
Source spelling remains recoverable for diagnostics and tooling.

AFRONT-28
AST nodes retain source provenance.

AFRONT-29
Every production semantic name resolves to exactly one declaration.

AFRONT-30
Ambiguous resolution is an error, never a heuristic choice.

AFRONT-31
Visibility is checked during resolution.

AFRONT-32
Method lookup uses the specified deterministic candidate order.

AFRONT-33
Generic syntax is preserved separately from inferred substitutions.

AFRONT-34
Parser and lexer do not perform ownership or alias analysis.

AFRONT-35
Implicit view creation is a semantic lowering operation, not a parser operation.

AFRONT-36
Raw pointer syntax does not grant safe pointer semantics.

AFRONT-37
Partial-program Unknown/Incomplete facts cannot satisfy production semantic proofs.

AFRONT-38
Lossless parse/print preserves source identity.

AFRONT-39
Formatting must preserve semantic identity.

AFRONT-40
Frontend output is deterministic for identical source and configuration.

AFRONT-41
Frontend has no dependency on target machine backend.

AFRONT-42
Resolved AST must not require repeated global name lookup by later phases.

AFRONT-43
Semantic recovery nodes cannot reach Verified MIR.

AFRONT-44
Incremental frontend invalidation follows dependency boundaries rather than rebuilding the entire project by default.
```

---

# Trạng thái chuỗi hiện tại

Ta đã khóa:

```text
217 Surface Syntax
        ↓
218 Compiler Implementation Blueprint
        ↓
220 CompilerDB / Internal Data Model
        ↓
221 Compiler Implementation Contract
        ↓
222 Frontend Implementation
```

Bây giờ có thể đi sâu vào **phần trung tâm của Axiom**.

# BOOTSTRAP-223 — AXIOM TYPE SYSTEM IMPLEMENTATION

Task tiếp theo sẽ khóa **TypeDB + type inference + unification + coercion + generic instantiation + function/closure types + struct/enum types + `view<T>`/`mut_view<T>` types + `Copy/Clone/Drop/Send/Share` properties**.

Đặc biệt 223 sẽ giải quyết một vấn đề rất quan trọng:

```text
        Source
          ↓
     Resolved AST
          ↓
   ┌───────────────┐
   │ Type Inference │
   └───────┬───────┘
           ↓
      Typed HIR
           ↓
   semantic properties
           ↓
 Copy / Move / Drop
 Send / Share
 View / MutView
```

và khóa chính xác **compiler tự suy ra bao nhiêu**, còn **lập trình viên tuyệt đối không phải viết gì**.