# BOOTSTRAP-103 — Axiom Compiler Frontend Architecture

**Trạng thái: FROZEN**

Mục tiêu của frontend Axiom:

> **Syntax đơn giản, deterministic, recoverable, AI-friendly; semantic complexity được chuyển xuống compiler thay vì bắt programmer viết nhiều annotation.**

Pipeline chính:

```text
UTF-8 Source
    ↓
SourceDB
    ↓
Lexer
    ↓
TokenStream
    ↓
Parser
    ↓
AST
    ↓
Declaration Collection
    ↓
Name Resolution
    ↓
Type / Generic Header Resolution
    ↓
HIR
    ↓
Typed HIR
    ↓
MIR
```

Frontend **không được phụ thuộc backend**.

---

# 1. Source là UTF-8 native

Axiom source mặc định:

```text
UTF-8
```

Compiler phải xử lý Unicode ngay từ SourceDB/Lexer.

Nhưng cần phân biệt:

```text
byte offset
Unicode scalar
grapheme
display column
```

Compiler semantic location dùng:

```text
SourceFileId + byte offset
```

Display layer mới chuyển sang column/grapheme.

---

# 2. SourceDB

`SourceDB` là nguồn dữ liệu canonical của frontend.

Concept:

```text
SourceFile {
    SourceFileId
    package
    path
    content
    revision
}
```

Không để parser tự sở hữu string source riêng.

Điều này giúp:

- incremental compilation
- source mapping
- diagnostics
- generated source
- IDE
- AI tooling.

---

# 3. Lexer

Lexer biến:

```text
UTF-8 bytes
```

thành:

```text
TokenStream
```

Lexer không thực hiện:

- name resolution
- type checking
- ownership checking
- macro expansion
- constant evaluation.

---

# 4. Token categories

Các nhóm chính:

```text
Identifier
Keyword
IntegerLiteral
FloatLiteral
StringLiteral
Char/RuneLiteral
Operator
Punctuation
Comment
Whitespace
EOF
Invalid
```

Trivia có thể được giữ trong token stream hoặc side-channel để formatter/IDE sử dụng.

---

# 5. Keywords

Keyword set phải nhỏ và ổn định.

Core hiện tại gồm các nhóm:

```text
fn
struct
enum
trait
impl
let
var
if
else
match
loop
while
for
in
break
continue
return

async
await
comptime
const

import
pub

unsafe
extern

true
false

as
where
move
```

Các từ khóa chưa có semantic contract không nên tùy tiện thêm.

---

# 6. Identifier

Identifier hỗ trợ Unicode.

Ví dụ:

```axiom
let người = 10;
let π = 3.14;
```

nhưng compiler phải định nghĩa normalization policy rõ ràng.

Khuyến nghị:

> **Không Unicode-normalize identifier một cách âm thầm.**

Hai chuỗi Unicode khác nhau về code point không tự động trở thành cùng identifier.

Điều này tránh collision khó nhìn.

---

# 7. Confusable identifiers

Unicode confusable detection là **tooling warning**, không phải semantic normalization.

Ví dụ:

```text
a
а
```

có thể nhìn giống nhau nhưng khác code point.

Compiler vẫn phân biệt.

IDE có thể cảnh báo:

```text
WCONFUSABLE_IDENTIFIER
```

---

# 8. Comments

Comment không có semantic effect.

Các loại:

```text
// line
/* block */
```

Nested block comment nên được hỗ trợ để parser/tooling dễ xử lý:

```text
/* outer
   /* inner */
*/
```

nếu grammar chọn thiết kế này.

Tôi đề xuất **có nested block comments**.

---

# 9. Documentation comments

Documentation nên được lexer/parser nhận biết như trivia có cấu trúc:

```text
/// documentation
```

nhưng declaration semantics vẫn độc lập.

Sau này `axiom doc` lấy documentation từ AST/HIR.

---

# 10. Numeric literals

Hỗ trợ:

```text
123
1_000_000
0xff
0b1010
0o755

3.14
1.0e10
```

Underscore chỉ formatting, không thay đổi giá trị.

Compiler không nên parse literal thành machine type quá sớm.

Ban đầu:

```text
IntegerLiteralSyntax
FloatLiteralSyntax
```

sau đó type checker mới xác định:

```text
i32
u64
f32
...
```

---

# 11. Integer overflow trong literal

Ví dụ:

```axiom
let x: u8 = 300;
```

phải lỗi compile-time.

Không được wrap thành:

```text
44
```

một cách âm thầm.

---

# 12. String literals

Axiom string literal là UTF-8.

Ví dụ:

```axiom
"hello"
"Xin chào"
```

Raw string nên có syntax rõ ràng, ví dụ:

```axiom
r"hello\n"
```

hoặc dạng delimiter mở rộng nếu cần.

Điểm quan trọng:

> Lexer không biến string literal thành heap allocation.

Đó là semantic/layout decision phía sau.

---

# 13. Escape sequences

Các escape cơ bản:

```text
\n
\r
\t
\\
\"
\xNN
\u{...}
```

Unicode escape phải được kiểm tra là Unicode scalar hợp lệ.

---

# 14. Rune/Unicode scalar literal

Nếu Axiom có literal cho Unicode scalar, nó phải khác string:

```text
'a'
'中'
```

nhưng không nhất thiết phải đưa `char` vào Core type.

Có thể map thành library/compiler scalar type.

Điều này giữ đúng quyết định trước:

> Axiom không cần một `char` primitive có semantics mơ hồ.

---

# 15. Operators

Lexer phải tokenize operator deterministic.

Ví dụ:

```text
+
-
*
/
%
==
!=
<
<=
>
>=
&&
||
!
&
|
^
<<
>>
=
+=
-=
*= 
```

Nhưng:

```text
&
```

không được mang semantic "reference" như Rust.

Trong Axiom, access capability dùng:

```text
view<T>
mut_view<T>
```

Raw address dùng:

```text
address_of(x)
```

ở unsafe/system layer.

---

# 16. `::` và `.`

Axiom phân biệt:

```text
Type::associated
module::name
value.method()
```

Ví dụ:

```axiom
std::io::File::open(...)
file.read(...)
```

Parser nhận syntax.

Semantic resolver quyết định chính xác declaration nào.

---

# 17. Grammar không được phụ thuộc name resolution

Một nguyên tắc quan trọng:

```text
Parser
```

không được cần biết:

```text
"Foo là type hay module hay generic?"
```

Parser tạo syntax tree.

Resolver mới quyết định.

Điều này làm frontend deterministic và incremental hơn.

---

# 18. Parser architecture

Khuyến nghị:

> **Recursive descent + Pratt parser cho expressions.**

Không cần parser generator phức tạp cho Core.

Ví dụ:

```text
parse_file()
parse_item()
parse_fn()
parse_struct()
parse_enum()
parse_trait()
parse_impl()
parse_statement()
parse_expression()
parse_pattern()
```

Expression precedence dùng Pratt/precedence climbing.

---

# 19. Expressions

Precedence cần canonical.

Ví dụ:

```axiom
a + b * c
```

luôn:

```text
a + (b * c)
```

Không phụ thuộc parser implementation.

---

# 20. Assignment không phải expression

Đã frozen:

```axiom
x = y;
```

là statement.

Không cho:

```axiom
if (x = y) { ... }
```

Điều này loại bỏ một class bug C/C++.

---

# 21. Boolean conditions

Chỉ `bool`:

```axiom
if x != 0 {
}
```

Không:

```axiom
if x {
}
```

nếu `x` là integer.

Không có C-style truthiness.

---

# 22. Blocks

Block là expression:

```axiom
let x = {
    let a = 10;
    a + 20
};
```

Expression cuối block là result.

Nếu có semicolon:

```axiom
{
    a + 20;
}
```

thì expression trở thành statement và block trả `unit`.

---

# 23. Statements

Core statements:

```text
let
var
assignment
expression statement
return
break
continue
declaration
```

Không thêm hàng loạt special statement nếu expression/function/trait có thể biểu diễn được.

---

# 24. Function declaration

Canonical:

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

Generic:

```axiom
fn max<T: Ord>(a: T, b: T) -> T {
    if a > b { a } else { b }
}
```

Parser giữ generic syntax; resolver/type checker xử lý constraint.

---

# 25. Struct declaration

```axiom
struct Vec2 {
    x: f32,
    y: f32,
}
```

Field identity là tên.

Không coi field order là semantic identity.

---

# 26. Struct literal

Canonical:

```axiom
let p = Vec2 {
    x: 1.0,
    y: 2.0,
};
```

Không khuyến nghị positional:

```text
Vec2(1, 2)
```

vì field order không phải semantic contract.

Constructor nếu cần:

```axiom
Vec2::new(1, 2)
```

là function.

---

# 27. Struct update

```axiom
let b = Vec2 {
    x: 10,
    ..a
};
```

`..a` tuân theo:

```text
Move
```

hoặc:

```text
Copy
```

semantics.

Không tự Clone.

---

# 28. Enum

```axiom
enum Result<T, E> {
    Ok(T),
    Err(E),
}
```

Parser chỉ xây variants.

Exhaustiveness và payload semantics thuộc HIR/type checker.

---

# 29. Trait

```axiom
trait Display {
    fn display(self: view<Self>);
}
```

Trait declaration không tạo inheritance hierarchy.

---

# 30. Impl

```axiom
impl Display for User {
    fn display(self: view<User>) {
        ...
    }
}
```

Resolver tạo:

```text
TraitImpl
```

và trait solver xử lý constraints.

---

# 31. Associated items

Hỗ trợ:

```axiom
trait Iterator {
    type Item;
    
    fn next(self: mut_view<Self>) -> Option<Self::Item>;
}
```

Parser cần generic syntax đủ mạnh nhưng không encode trait semantics.

---

# 32. Attributes

Ví dụ:

```axiom
@repr(C)
struct Header { ... }

@inline
fn foo() { ... }

@kernel
fn add(...) { ... }
```

Parser tạo:

```text
Attribute {
    name
    arguments
    span
}
```

Attribute registry mới quyết định:

```text
semantic
ABI
optimization
target
tooling
```

---

# 33. Unknown attributes

Core rule:

```text
unknown Core attribute → error
```

ngoại trừ reserved tooling namespace nếu được quy định.

Không để typo:

```axiom
@reprc
```

âm thầm bị bỏ qua.

---

# 34. Generic syntax

Parser phải hỗ trợ:

```axiom
fn foo<T>(x: T) -> T
```

constraints:

```axiom
fn foo<T: Ord + Clone>(x: T)
```

và:

```axiom
fn foo<T>(x: T)
where
    T: Ord + Clone,
{
}
```

`where` là syntax convenience, semantic result giống nhau.

---

# 35. Explicit generic arguments

```axiom
foo::<i32>(10);
```

được giữ vì có những trường hợp inference không đủ.

Nhưng generic arguments nên được compiler infer tối đa.

---

# 36. Type syntax

Core type grammar cần hỗ trợ:

```text
i32
u64
f32

MyType
Foo<T>
[T; N]

(T, U)
fn(T) -> U

view<T>
mut_view<T>

*const T
*mut T
```

và:

```text
dyn Trait
```

ở nơi được phép.

---

# 37. No `&T` parser production

Đây là một quyết định đáng giữ rất chặt.

Parser Axiom Core không cần grammar:

```text
&T
&mut T
```

Do đó compiler architecture không bị kéo vào việc hỗ trợ một alias/reference syntax song song với capability model.

---

# 38. Pattern grammar

Patterns:

```text
_
x
mut x
Some(x)
Ok(value)
Err(e)
Enum::Variant
Struct { x, y }
Struct { x: a, y: b }
(a, b)
[a, b]
```

và range:

```text
1..10
1..=10
```

Pattern không được thực hiện arbitrary code.

---

# 39. Ownership trong pattern là semantic phase

Ví dụ:

```axiom
match value {
    Some(x) => ...
    None => ...
}
```

Parser chỉ biết `Some(x)`.

Resolver/type checker quyết định:

```text
move
copy
view
destructure
partial move
```

---

# 40. Closure syntax

```axiom
|x| x * 2
```

multiple arguments:

```axiom
|x, y| x + y
```

typed:

```axiom
|x: i32| x * 2
```

move closure:

```axiom
move |x| use_owned(x)
```

Compiler tạo anonymous closure type ở HIR.

---

# 41. Closure body

Closure có thể là:

```text
expression
```

hoặc block:

```axiom
|x| {
    let y = x + 1;
    y * 2
}
```

Capture semantics không do parser quyết định.

---

# 42. Async syntax

```axiom
async fn fetch() -> Result<Data, Error> {
    ...
}
```

và:

```axiom
let x = fetch().await?;
```

Parser đánh dấu:

```text
AwaitExpr
AsyncFn
```

Async lowering xảy ra sau HIR.

---

# 43. Comptime syntax

```axiom
const SIZE: usize = 1024;
```

và:

```axiom
comptime {
    ...
}
```

hoặc:

```axiom
comptime fn make_value() -> usize {
    ...
}
```

Parser không thực thi comptime.

---

# 44. `@cfg`

Ví dụ:

```axiom
@cfg(target_os = "windows")
fn foo() { ... }
```

`@cfg` được xử lý **trước normal name resolution** theo invariant đã frozen.

---

# 45. Import syntax

```axiom
import std::io::File;
```

hoặc:

```axiom
import std::io::{File, Socket};
```

alias:

```axiom
import graphics::Color as GColor;
```

Parser tạo Import AST.

Resolver biến nó thành:

```text
DeclarationId
```

---

# 46. No wildcard import Core v1

Không:

```axiom
import std::io::*;
```

Điều này giúp:

- IDE rõ ràng
- AI dễ phân tích
- diagnostics tốt
- namespace deterministic
- giảm accidental collisions.

---

# 47. Parser recovery

Parser phải recover từ:

```axiom
fn foo(
    let x = ;
    ...
```

thay vì dừng ngay token đầu tiên.

Recovery strategies:

```text
missing token insertion
token deletion
synchronization
synthetic nodes
```

Nhưng synthetic nodes phải đánh dấu:

```text
is_recovered = true
```

---

# 48. Synchronization points

Các điểm recovery tốt:

```text
;
}
)
]
,
```

và declaration keywords:

```text
fn
struct
enum
trait
impl
import
```

Mục tiêu:

> một lỗi syntax không phá toàn bộ file.

---

# 49. AST design

AST nên giữ syntax information đủ cho:

- diagnostics
- formatter
- IDE
- documentation
- source-to-source tooling.

Nhưng AST **không phải semantic IR**.

Ví dụ AST có:

```text
NameExpr("foo")
```

HIR mới có:

```text
ResolvedDeclExpr(DeclarationId=...)
```

---

# 50. AST node IDs

Mỗi node:

```text
AstNodeId
```

Không dùng memory address làm identity.

Ví dụ:

```text
AstNode {
    id
    kind
    span
    children
}
```

---

# 51. HIR không giữ syntax noise

AST:

```text
foo::<i32>(x)
```

HIR có thể canonicalize thành:

```text
Call {
    function: ResolvedDecl(foo)
    generic_args: [i32]
    args: [x]
}
```

Các syntax sugar khác cũng canonicalize.

---

# 52. Method call desugaring

Source:

```axiom
v.length()
```

HIR:

```text
Call(
    resolved_function = length,
    receiver = v
)
```

Semantic function:

```axiom
fn length(self: view<Vec<T>>) -> usize
```

Parser không cần biết đây là method.

Resolver/method lookup mới biết.

---

# 53. `?` desugaring

Source:

```axiom
read()?
```

HIR canonicalizes thành semantic control flow tương đương:

```text
match result {
    Ok(v) => v,
    Err(e) => return Err(e)
}
```

Nhưng compiler có thể giữ `Try` node cho optimization/diagnostics trước khi lowering.

---

# 54. `for` desugaring

Source:

```axiom
for x in items {
    use(x);
}
```

HIR canonicalizes qua:

```text
IntoIterator
Iterator::next
match
```

Nhưng không nhất thiết materialize toàn bộ desugared source AST.

Một semantic HIR node:

```text
ForLoop
```

có thể được lower trực tiếp.

---

# 55. `if let`

```axiom
if let Some(x) = value {
    use(x);
}
```

có thể lower thành match CFG.

---

# 56. Canonical HIR

HIR nên có ít construct hơn AST.

Ví dụ:

```text
AST:
    MethodCall
    For
    IfLet
    ? 
    StructUpdate
```

HIR:

```text
Call
Match
Branch
ControlFlow
Aggregate
Move
Copy
MakeView
MakeMutView
```

nhưng vẫn giữ source provenance.

---

# 57. HIR semantic explicitness

Đây là nơi triết lý Axiom thể hiện rõ:

```text
Programmer writes:
    v.length()

HIR understands:
    call length(v)

Programmer writes:
    items[i]

HIR understands:
    indexing capability + bounds semantics

Programmer writes:
    x?

HIR understands:
    Result/Option propagation
```

Compiler hiểu nhiều hơn programmer phải viết.

---

# 58. Resolver phases

Resolver không nên là một bước khổng lồ.

Tách:

```text
1. Collect declarations
2. Build module scopes
3. Resolve imports
4. Resolve names
5. Resolve associated paths
6. Resolve methods
7. Resolve trait candidates
8. Resolve generic references
```

Mỗi query incremental.

---

# 59. Declaration collection

Trước khi resolve body:

```text
struct A ...
fn foo ...
trait X ...
```

được collect.

Điều này cho phép:

```axiom
fn a() {
    b();
}

fn b() {
}
```

không cần declaration order đặc biệt.

---

# 60. Recursive declarations

Function recursion:

```axiom
fn factorial(n: u64) -> u64 {
    ...
}
```

được hỗ trợ.

Type recursion by value:

```axiom
struct Node {
    next: Node
}
```

bị reject vì infinite size.

Indirection:

```axiom
struct Node {
    next: Option<Box<Node>>
}
```

được phép.

---

# 61. Scope tree

Compiler tạo:

```text
ScopeId
```

cho:

```text
module
function
block
match arm
loop
closure
comptime block
```

Name lookup:

```text
local scope
→ parent scope
→ module
→ imports
→ prelude
```

theo rules đã frozen.

---

# 62. Shadowing

Axiom nên cho phép local shadowing:

```axiom
let x = 1;

{
    let x = 2;
}
```

nhưng compiler có thể warning nếu cấu hình strict.

Import shadowing phải xử lý nghiêm ngặt hơn.

---

# 63. Declaration identity

Sau resolution:

```text
foo
```

không còn là string.

Nó trở thành:

```text
DeclarationId(1234)
```

Đây là một trong những điểm quan trọng nhất để compiler/AI không bị phụ thuộc text matching.

---

# 64. Generic header resolution trước body

Ví dụ:

```axiom
fn max<T: Ord>(a: T, b: T) -> T
```

compiler cần resolve:

```text
T
Ord
a
b
return type
```

trước khi type-check body.

---

# 65. Trait solver không thuộc parser

Parser không được biết:

```text
T: Ord
```

có satisfied hay không.

Nó chỉ tạo constraint syntax.

Trait solver hoạt động trên HIR/type facts.

---

# 66. AST → HIR source mapping

Mỗi HIR node nên có:

```text
SourceSpanId
AstNodeId?
Origin
```

để diagnostics quay lại source.

Generated HIR cũng giữ provenance:

```text
generated by comptime
generated by derive
source declaration
```

---

# 67. Error-tolerant HIR

IDE cần HIR ngay cả khi code chưa compile hoàn chỉnh.

Ví dụ:

```axiom
let x: Foo = bar.
```

AST có thể recovery.

HIR có:

```text
ErrorExpr
ErrorType
```

nhưng giữ phần semantic đã biết.

---

# 68. `ErrorType`

Compiler có:

```text
TypeId::Error
```

để không cascade:

```text
Foo unknown
→ x unknown
→ x + y unknown
→ return unknown
→ ...
```

thành 50 errors.

Thay vào đó root diagnostic là:

```text
ERESOLVE_UNDEFINED
```

---

# 69. Frontend query architecture

CompilerDB:

```text
parse(file)
ast(file)
collect_declarations(module)
resolve_imports(module)
resolve_name(expr)
resolve_type(type_syntax)
resolve_method(call)
lower_hir(function)
type_check(function)
```

Các query cache theo revision.

---

# 70. Parallel frontend

Các module độc lập có thể parse/resolve song song.

Nhưng kết quả phải deterministic.

Không để:

```text
thread scheduling
```

thay đổi:

- DeclarationId assignment semantic identity
- diagnostic ordering
- resolution result
- generated output.

IDs có thể là internal allocation IDs khác nhau nếu semantic fingerprints không phụ thuộc số ID; canonical serialization phải normalize chúng.

---

# 71. Formatter

Formatter **không thuộc parser semantics**.

CLI:

```bash
axiom fmt
```

hoạt động trên AST/trivia.

Formatter không được thay đổi:

```text
AST semantic meaning
```

---

# 72. AI-friendly canonical syntax

Axiom nên ưu tiên syntax có một cách viết canonical.

Ví dụ:

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

hơn là cho phép 5 syntax tương đương.

Ít syntax alias:

> AI generation dễ hơn, parser đơn giản hơn, diagnostics ổn định hơn.

---

# 73. Nhưng không over-constrain programmer

Canonical syntax không có nghĩa cấm tất cả sugar.

Ví dụ:

```text
method call
for
if let
?
```

vẫn nên tồn tại vì chúng giảm cognitive load mà không tạo semantic ambiguity.

Nguyên tắc:

> **Sugar được phép khi có một canonical semantic expansion rõ ràng.**

---

# 74. Frontend correctness boundary

Frontend phải đảm bảo:

```text
Source
→ AST
→ Resolved HIR
```

không làm mất semantic information.

Sau HIR:

```text
HIR → MIR
```

mới bắt đầu biến đổi control-flow/ownership/capability thành representation phù hợp verification.

---

# 75. Frontend không được "optimize"

Không nên:

```text
parser
→ constant folding
→ dead code elimination
→ inlining
```

Frontend chỉ canonicalize syntax.

Optimization bắt đầu sau verified semantic representation.

Điều này giữ architecture sạch:

```text
parse ≠ optimize
```

---

# 76. Lexer/parser security

Malformed input phải chịu được:

```text
huge identifier
huge nesting
huge literal
invalid UTF-8
invalid escape
deep expression
```

Compiler có configurable resource limits.

Không để stack overflow từ source bình thường biến thành uncontrolled compiler crash.

---

# 77. Frontend fuzzing

Hai tầng:

```text
random bytes
→ lexer/parser
```

và:

```text
grammar-aware source
→ AST
→ resolver
```

Invariant:

```text
never memory-unsafe
never uncontrolled crash
```

và diagnostics deterministic.

---

# 78. AST canonical serialization

Nên có:

```bash
axiom dump-ast file.ax
axiom dump-hir file.ax
```

Machine format:

```text
JSON
```

hoặc binary semantic format.

AI agent có thể hỏi compiler:

```text
"declaration này resolve tới đâu?"
```

thay vì parse source bằng chính nó.

---

# 79. Frontend API cho AI

Có thể có:

```bash
axiom inspect symbol ...
axiom inspect type ...
axiom inspect ast ...
axiom inspect hir ...
axiom inspect references ...
```

Ví dụ:

```text
axiom inspect symbol foo
```

trả:

```text
DeclarationId
kind
module
visibility
signature
generic parameters
traits
source span
```

---

# 80. Frontend pipeline hoàn chỉnh

```text
                 UTF-8 Source
                       │
                       ▼
                   SourceDB
                       │
                       ▼
                    Lexer
                       │
                       ▼
                  TokenStream
                       │
                       ▼
                    Parser
                       │
                       ▼
                      AST
                       │
             ┌─────────┴─────────┐
             │                   │
         diagnostics          tooling
             │
             ▼
       Declaration Collection
             │
             ▼
        Module / Scope Graph
             │
             ▼
        Import Resolution
             │
             ▼
         Name Resolution
             │
             ▼
       Type / Generic Headers
             │
             ▼
                    HIR
             │
             ▼
              Typed HIR
             │
             ▼
       Ownership/Capability/
       Trait/Async/Comptime facts
             │
             ▼
                   MIR
```

---

# 81. Những thứ frontend tuyệt đối không làm

Frontend không được tự quyết định:

```text
stack vs heap
register allocation
instruction selection
SIMD
inlining
GC
physical address
ABI register assignment
machine layout
```

Ngoại lệ là các **semantic contracts** cần thiết để type/representation resolution hoạt động, nhưng physical lowering vẫn thuộc backend.

---

# 82. Frozen invariants

**AFRONT-20** — Source Is UTF-8  
**AFRONT-21** — Source Identity Is Independent Of Physical Memory Address  
**AFRONT-22** — Semantic Source Coordinates Use Stable Byte Offsets  
**AFRONT-23** — Display Coordinates Are A Rendering Concern  
**AFRONT-24** — Lexer Does Not Perform Semantic Name Resolution  
**AFRONT-25** — Lexer Does Not Perform Type Checking  
**AFRONT-26** — Lexer Produces A Deterministic Token Stream  
**AFRONT-27** — Invalid UTF-8 Is Diagnosed Deterministically  
**AFRONT-28** — Numeric Literal Syntax Is Distinguished From Numeric Type Semantics  
**AFRONT-29** — Literal Overflow Is Diagnosed Before Silent Truncation  
**AFRONT-30** — String Literals Are UTF-8 Values  
**AFRONT-31** — String Literals Do Not Imply Heap Allocation  
**AFRONT-32** — Unicode Identifier Normalization Is Not Implicit  
**AFRONT-33** — Unicode Confusables Do Not Change Identifier Identity  
**AFRONT-34** — Confusable Detection Is Tooling/Diagnostic Policy  
**AFRONT-35** — Comments Have No Program Semantic Effect  
**AFRONT-36** — Documentation Comments Preserve Declaration Association  
**AFRONT-37** — Operators Have Deterministic Lexical Boundaries  
**AFRONT-38** — Assignment Is Not An Expression  
**AFRONT-39** — Boolean Conditions Require Bool  
**AFRONT-40** — Parser Does Not Depend On Name Resolution  
**AFRONT-41** — Parser Does Not Depend On Type Inference  
**AFRONT-42** — Parser Uses A Deterministic Grammar  
**AFRONT-43** — Expression Precedence Is Language-Defined  
**AFRONT-44** — Block Expressions Have Deterministic Value Semantics  
**AFRONT-45** — Struct Field Identity Is Name-Based  
**AFRONT-46** — Positional Struct Construction Is Not Required By Core Syntax  
**AFRONT-47** — Struct Update Follows Move/Copy Semantics  
**AFRONT-48** — Enum Syntax Does Not Define Physical Representation  
**AFRONT-49** — Trait Syntax Does Not Imply Inheritance  
**AFRONT-50** — Impl Syntax Does Not Imply Object Headers  
**AFRONT-51** — Generic Syntax Is Resolved Semantically After Parsing  
**AFRONT-52** — Attributes Are Structured Compiler Metadata  
**AFRONT-53** — Unknown Core Attributes Produce Diagnostics  
**AFRONT-54** — Pattern Syntax Is Distinct From Pattern Ownership Semantics  
**AFRONT-55** — Closure Syntax Is Distinct From Closure Capture Semantics  
**AFRONT-56** — Async Syntax Is Distinct From Async Lowering  
**AFRONT-57** — Comptime Syntax Does Not Execute During Parsing  
**AFRONT-58** — @cfg Selection Precedes Normal Name Resolution  
**AFRONT-59** — Import Syntax Does Not Resolve Itself  
**AFRONT-60** — Wildcard Imports Are Not Core Syntax  
**AFRONT-61** — AST Preserves Required Source Provenance  
**AFRONT-62** — AST Identity Uses Stable Compiler IDs  
**AFRONT-63** — AST Is Distinct From Semantic HIR  
**AFRONT-64** — HIR Canonicalizes Approved Syntax Sugar  
**AFRONT-65** — HIR Does Not Need To Preserve Surface Sugar Semantics  
**AFRONT-66** — HIR Preserves Source Provenance  
**AFRONT-67** — Method Calls Resolve To Semantic Functions  
**AFRONT-68** — `?` Has A Canonical Semantic Expansion  
**AFRONT-69** — `for` Has A Canonical Iterator Semantics  
**AFRONT-70** — `if let` Has A Canonical Pattern/Control-Flow Semantics  
**AFRONT-71** — No General `&T` Reference Syntax Exists In Core  
**AFRONT-72** — Raw Pointer Syntax Is Restricted To Unsafe/System Contexts  
**AFRONT-73** — Name Resolution Produces DeclarationId-Based References  
**AFRONT-74** — Declaration Collection Precedes Body Resolution  
**AFRONT-75** — Declaration Order Does Not Define Visibility Within A Module  
**AFRONT-76** — Scope Identity Is Independent Of Source Text Identity  
**AFRONT-77** — Import Resolution Is Incremental  
**AFRONT-78** — Name Resolution Is Deterministic  
**AFRONT-79** — Ambiguous Resolution Produces Explicit Diagnostics  
**AFRONT-80** — Type Resolution Is Separate From Parsing  
**AFRONT-81** — Trait Solving Is Separate From Parsing  
**AFRONT-82** — Ownership Semantics Are Not Determined By Parser Alone  
**AFRONT-83** — Capability Semantics Are Not Determined By Parser Alone  
**AFRONT-84** — Generated HIR Preserves Generation Provenance  
**AFRONT-85** — Recovered AST Nodes Are Marked As Recovered  
**AFRONT-86** — Parser Recovery Must Not Invent Source Semantics  
**AFRONT-87** — Parser Recovery Should Minimize Cascading Diagnostics  
**AFRONT-88** — ErrorType And ErrorDeclaration May Poison Invalid Semantic Paths  
**AFRONT-89** — Poisoned Nodes Must Not Produce Arbitrary Secondary Errors  
**AFRONT-90** — Frontend Queries Are Incrementally Cacheable  
**AFRONT-91** — Frontend Queries Are Deterministic  
**AFRONT-92** — Parallel Frontend Evaluation Is Semantically Equivalent To Serial Evaluation  
**AFRONT-93** — Semantic IDs Must Not Depend On Thread Scheduling  
**AFRONT-94** — Formatter Does Not Define Language Semantics  
**AFRONT-95** — Canonical Formatting Does Not Change Semantics  
**AFRONT-96** — AI Tooling Uses Semantic Compiler Queries  
**AFRONT-97** — AI Tooling Must Not Need To Reimplement Name Resolution  
**AFRONT-98** — AST/HIR Inspection Is Machine-Readable  
**AFRONT-99** — Frontend Does Not Perform Backend Optimization  
**AFRONT-100** — Frontend Must Remain Independent Of Target Machine Instruction Selection  
**AFRONT-101** — Frontend Must Remain Independent Of Register Allocation  
**AFRONT-102** — Frontend Must Remain Independent Of Physical Storage Placement  
**AFRONT-103** — Frontend Must Remain Usable In Freestanding Builds  
**AFRONT-104** — Frontend Must Not Require A Monolithic Runtime  
**AFRONT-105** — Malformed Source Must Not Cause Uncontrolled Compiler Failure  
**AFRONT-106** — Lexer And Parser Are Fuzz-Testable In Isolation  
**AFRONT-107** — Frontend Resource Limits Are Explicit  
**AFRONT-108** — Frontend Diagnostics Use The Structured Diagnostic Model  
**AFRONT-109** — Frontend Source Mapping Is Bidirectional  
**AFRONT-110** — Frontend Is The Sole Authority For Source-to-HIR Structural Meaning  

**BOOTSTRAP-103: FROZEN.**

---

# BOOTSTRAP-104 — Axiom Type Checking, Inference & Semantic Elaboration

Bước tiếp theo là **type system thực sự chạy như thế nào**.

Đây sẽ là một trong những phần lõi nhất của compiler, vì Axiom muốn:

```text
static typing
+
ít annotation
+
không implicit conversion nguy hiểm
+
generic/trait mạnh
+
ownership/capability inference
```

Pipeline dự kiến:

```text
Typed HIR
   ↓
Type Environment
   ↓
Constraint Generation
   ↓
Type Inference
   ↓
Trait Constraint Solving
   ↓
Numeric Literal Resolution
   ↓
Generic Substitution
   ↓
Method / Operator Resolution
   ↓
Ownership / Capability Elaboration
   ↓
Fully Typed HIR
```

Đặc biệt BOOTSTRAP-104 sẽ khóa các vấn đề dễ khiến Axiom trở nên **quá giống Rust/C++ hoặc quá phức tạp** nếu thiết kế không cẩn thận:

- type inference đến mức nào;
- khi nào compiler phải yêu cầu annotation;
- generic inference;
- overload/operator resolution;
- `Copy` inference;
- `Move` inference;
- `view` / `mut_view` inference;
- numeric literals;
- coercion;
- `Option`/`Result`;
- associated types;
- trait solver;
- ambiguity;
- recursive types;
- closure type inference;
- async Future type inference;
- comptime type inference;
- và đặc biệt **compiler phải tự làm ownership/capability analysis đến đâu mà programmer không cần viết lifetime/borrow annotations**.