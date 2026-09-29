# XXXVII — PARSE-001: AST + Parser Axiom v0.1

Ta đi tiếp đúng chuỗi implementation. Mục tiêu của bước này là:

```text
fn main() {}
```

đi qua:

```text
TokenStream
    ↓
Parser
    ↓
AST
    ↓
Resolver
    ↓
HIR
```

và **AST không được mang semantic của resolver/type checker vào trong**.

---

## 1. AST architecture

AST là syntax representation.

```text
TokenStream
      ↓
    Parser
      ↓
      AST
      ↓
   Resolver
      ↓
     HIR
```

AST cần giữ:

- cấu trúc cú pháp
- source span
- syntax spelling cần thiết cho diagnostics
- attributes
- generic syntax
- unresolved names

AST **không** giữ:

- `FunctionId`
- `TypeId` semantic
- `SymbolId`
- ownership state
- trait obligations
- capability
- MIR
- ABI

---

# 2. AST storage

Dùng typed arena.

```text
AstDatabase
├── items: ItemArena
├── exprs: ExprArena
├── stmts: StmtArena
├── patterns: PatternArena
├── types: TypeSyntaxArena
├── attributes: AttributeArena
└── paths: PathArena
```

Các ID:

```text
ItemId
ExprId
StmtId
PatternId
TypeSyntaxId
AttributeId
PathId
```

Không dùng raw pointer.

---

# 3. Node header

Mỗi node phải có:

```text
AstNode {
    id
    span
}
```

Concept:

```text
Expr {
    id: ExprId
    span: Span
    kind: ExprKind
}
```

Tương tự:

```text
Stmt
Item
Pattern
TypeSyntax
```

Điều này giúp diagnostic sau này luôn quay lại source chính xác.

---

# 4. Top-level AST

```text
CompilationUnit {
    module_decl: ModuleDecl?
    items: Vec<ItemId>
    span: Span
}
```

`module_decl` có thể là:

```axiom
module math.vector
```

Items:

```text
Function
Struct
Enum
Trait
Impl
TypeAlias
Const
Static
Module
Import
```

---

# 5. Function AST

```text
FunctionAst {
    name: Identifier
    generics: GenericParamList?
    params: Vec<ParamAst>
    return_type: TypeSyntaxId?
    body: BlockAst?
    attributes: Vec<AttributeId>
    visibility: VisibilitySyntax
    is_async: bool
}
```

Ví dụ:

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

AST concept:

```text
Function
├── name = "add"
├── params
│   ├── a : i32
│   └── b : i32
├── return = i32
└── body
```

Không biết `i32` là `TypeId(7)` ở đây.

---

# 6. `main` không phải keyword

Đây là chủ ý.

```axiom
fn main() {}
```

`main` là:

```text
Identifier("main")
```

chứ không phải:

```text
Keyword(Main)
```

Việc `main` có ý nghĩa entry point thuộc compiler/driver/build profile.

---

# 7. Parameter AST

```text
ParamAst {
    name: PatternId
    type: TypeSyntaxId
    span: Span
}
```

MVP chỉ cho parameter pattern đơn giản:

```axiom
fn foo(x: i32)
```

Pattern phức tạp có thể được mở rộng theo grammar đã đóng, nhưng không cần tạo semantic ownership ở parser.

---

# 8. Block AST

```text
BlockAst {
    statements: Vec<StmtId>
    tail: ExprId?
    span: Span
}
```

Điểm này rất quan trọng.

```axiom
{
    let x = 10
    x + 1
}
```

được biểu diễn:

```text
statements:
    let x = 10

tail:
    x + 1
```

Không cần một node `ImplicitReturn`.

Return semantics thuộc HIR/MIR.

---

# 9. Empty block

```axiom
{}
```

AST:

```text
Block {
    statements = []
    tail = none
}
```

Type checker sau này quyết định:

```text
{}
```

có type:

```text
unit
```

---

# 10. Statements

MVP:

```text
Let
Var
Expr
Return
Break
Continue
While
For
```

Ví dụ:

```axiom
let x = 42
```

AST:

```text
LetStmt {
    pattern
    type_annotation?
    initializer?
}
```

`var` tương tự nhưng semantic mutability sẽ được xác định sau.

---

# 11. Expression AST

Core:

```text
Literal
Name
Self
Tuple
Array
StructLiteral
EnumLiteral

Call
MethodCall
Field
Index

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

Parentheses:

```axiom
(a + b)
```

không nhất thiết cần semantic node riêng.

Parser có thể tạo:

```text
Binary(a, +, b)
```

và span vẫn bao gồm parentheses nếu cần diagnostic.

Nếu cần preserve exact syntax cho formatter, đó là một concern khác; AST semantic parser không nên phình vì formatter.

---

# 12. Literal AST

```text
Literal {
    kind
    span
}
```

Literal kind:

```text
Bool
Integer
Float
String
Bytes
```

Integer vẫn giữ raw source span.

Type checker mới xử lý:

```text
42
```

thành:

```text
i32
```

hay type khác dựa trên context.

---

# 13. Name AST

```text
NameExpr {
    name: StringId
    span: Span
}
```

Không:

```text
SymbolId
```

vì resolver chưa chạy.

---

# 14. Path AST

Ví dụ:

```axiom
math.vector.Vec2
```

AST:

```text
Path {
    segments: [
        "math",
        "vector",
        "Vec2"
    ]
}
```

Path resolution thuộc resolver.

---

# 15. Type syntax

```text
TypeSyntax {
    Named
    Tuple
    Array
    Function
    View
    MutView
    RawPointer
    DynTrait
    ImplTrait
    AppliedGeneric
}
```

Ví dụ:

```axiom
view<Vec2>
```

AST:

```text
View(
    Named("Vec2")
)
```

chứ chưa phải semantic capability.

---

# 16. `view` là syntax type đặc biệt

Parser nhận:

```axiom
view<Vec2>
```

thành:

```text
TypeSyntax::View(Vec2)
```

Sau này type checker biến thành:

```text
TypeId::View(TypeId::Vec2)
```

Ownership/capability analyzer mới kiểm:

- provenance
- lifetime
- conflict
- escape

Ba tầng hoàn toàn tách biệt.

---

# 17. Pratt parser

Expression parser:

```text
parse_expression(min_precedence)
```

Concept:

```text
lhs = parse_prefix()

while precedence(peek_operator) >= min_precedence:
    op = consume()
    rhs = parse_expression(next_precedence)
    lhs = Binary(lhs, op, rhs)

return lhs
```

Postfix được xử lý trước binary precedence.

---

# 18. Prefix parser

Prefix:

```text
!
~
-
+
```

và:

```text
await
```

nếu grammar cần.

Ví dụ:

```axiom
-a * b
```

AST:

```text
(-a) * b
```

---

# 19. Postfix parser

Sau primary:

```text
foo
```

parser loop:

```text
foo(...)
foo.bar
foo[0]
foo.await
foo?
```

Concept:

```text
parse_primary()
    ↓
loop:
    if "(" → Call
    if "." → Field / Await
    if "[" → Index
    if "?" → Try
```

Ví dụ:

```axiom
foo.bar()[0].x?
```

được xây dần từ trái sang phải.

---

# 20. Method call

```axiom
v.length()
```

AST vẫn có:

```text
MethodCall {
    receiver = v
    method = "length"
    args = []
}
```

Không parser-lower ngay thành:

```text
length(v)
```

Lý do:

Resolver cần biết:

- inherent method
- trait method
- extension method
- generic extension

Sau method resolution mới normalize thành semantic call.

---

# 21. Generic call

```axiom
max<i32>(a, b)
```

AST cần giữ:

```text
Call {
    callee
    generic_args
    args
}
```

Parser không giải quyết `i32` là type gì.

---

# 22. Generic ambiguity

Case:

```axiom
foo<Bar>(x)
```

Parser context phải cho phép generic arguments.

Nhưng:

```axiom
a < b > c
```

là binary comparisons.

Không được sửa lexer để phân biệt.

Parser phải có context:

```text
identifier
    ↓
potential generic argument list
    ↓
lookahead
```

và nếu không parse hợp lệ thì quay về operator interpretation theo grammar.

---

# 23. Assignment

```axiom
x = 42
```

AST:

```text
Assignment {
    target: ExprId
    value: ExprId
}
```

Parser cho phép syntax.

Type checker sau này đảm bảo target là valid place và mutable.

Parser không biết:

```text
x
```

có phải mutable không.

---

# 24. `if`

```axiom
if condition {
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
    else_expr?
}
```

`else if` có thể chỉ là:

```text
else_expr = IfExpr(...)
```

không cần AST node riêng.

---

# 25. `match`

AST:

```text
MatchExpr {
    scrutinee
    arms: Vec<MatchArm>
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

Pattern vẫn là syntax.

Exhaustiveness thuộc semantic checker.

---

# 26. Pattern AST

```text
Wildcard
Name
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
Message.Move { x, y }
```

AST vẫn giữ unresolved path/variant.

Resolver sau đó biến thành:

```text
VariantId
FieldId
```

---

# 27. Closure AST

```axiom
|a, b| a + b
```

AST:

```text
Closure {
    capture_mode?
    params
    body
}
```

`move`:

```axiom
move |a| a + x
```

AST:

```text
Closure {
    explicit_move = true
}
```

Nhưng capture thật sự là:

```text
READ
MUTATE
MOVE
```

do ownership/capture analysis xác định.

---

# 28. Parser error recovery

Parser phải có synchronization points:

```text
}
)
]
;
```

và item keywords:

```text
fn
struct
enum
trait
impl
import
module
const
static
```

Nếu gặp:

```axiom
fn main( {
```

không được dừng compiler ngay lập tức.

Nó phát diagnostic:

```text
AX_PARSE_0001
```

sau đó recover về:

```text
)
```

hoặc:

```text
{
```

tùy context.

---

# 29. Parser diagnostics

Đề xuất:

```text id="7mof4y"
AX_PARSE_0001 Unexpected token
AX_PARSE_0002 Expected token
AX_PARSE_0003 Unterminated block
AX_PARSE_0004 Invalid expression
AX_PARSE_0005 Invalid type
AX_PARSE_0006 Invalid pattern
AX_PARSE_0007 Invalid generic argument list
AX_PARSE_0008 Invalid attribute
AX_PARSE_0009 Missing expression
AX_PARSE_0010 Invalid item
```

---

# 30. Parser invariants

```text id="f1h3ap"
APAR-24
Parser consumes only TokenStream and produces AST.

APAR-25
Parser never performs name resolution.

APAR-26
Parser never performs type checking.

APAR-27
Parser never performs ownership analysis.

APAR-28
Every AST node has a valid Span.

APAR-29
AST semantic identity is represented by typed AST IDs.

APAR-30
Parser preserves unresolved names.

APAR-31
Parser does not assign SymbolId.

APAR-32
Parser does not assign TypeId.

APAR-33
Expression precedence is deterministic.

APAR-34
Postfix operators associate left-to-right.

APAR-35
Parser recovery is deterministic.

APAR-36
Parser errors cannot silently become valid semantic constructs.

APAR-37
AST construction does not require target information.

APAR-38
AST construction does not require package resolution.

APAR-39
AST preserves source spans for all semantic syntax.

APAR-40
Parentheses do not alter semantic precedence.

APAR-41
Method-call syntax remains distinguishable until resolution.
```

---

# 31. AST golden test đầu tiên

Input:

```axiom
fn main() {}
```

Expected:

```text id="wqq7l7"
CompilationUnit
└── Function
    ├── name: "main"
    ├── params: []
    ├── return: none
    └── body
        ├── statements: []
        └── tail: none
```

Không có:

```text
FunctionId
TypeId
SymbolId
```

---

# 32. AST golden thứ hai

```axiom
fn main() -> i32 {
    42
}
```

Expected:

```text id="h4r8qf"
Function
├── name: main
├── return:
│   └── NamedType(i32)
└── body
    └── tail:
        └── IntegerLiteral(42)
```

---

# 33. AST golden thứ ba

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

```text id="6qzuwk"
Function add
├── Param a : i32
├── Param b : i32
├── Return i32
└── Body
    └── Binary(+)
        ├── Name(a)
        └── Name(b)
```

Đây sẽ là input quan trọng cho Resolver.

---

# 34. Bây giờ nối sang Resolver — không chờ parser hoàn chỉnh

Đây là bước rất quan trọng về kiến trúc.

Resolver nhận:

```text
AST
 +
SourceDatabase
 +
Package/Module graph
```

và tạo:

```text
Resolved AST / HIR
```

Resolver bắt đầu bằng **declaration collection**.

---

# 35. Resolver Phase 1 — collect declarations

Với:

```axiom
fn add() {}
fn main() {}
```

pass đầu tiên tạo:

```text
SymbolTable
├── add → SymbolId(1)
└── main → SymbolId(2)
```

Chưa resolve body.

Điều này cho phép:

```axiom
fn main() {
    add()
}

fn add() {}
```

hoạt động bình thường.

---

# 36. Resolver Phase 2 — resolve bodies

Khi vào:

```axiom
fn main() {
    add()
}
```

resolver tìm:

```text
add
```

theo thứ tự:

```text
local binding
↓
parameter
↓
current module
↓
explicit imports
↓
public/package re-export
↓
prelude
```

và cuối cùng:

```text
Name("add")
```

được biến thành:

```text
ResolvedName::Function(FunctionId)
```

---

# 37. Scope tree

Resolver cần:

```text
Scope
├── parent
├── bindings
└── kind
```

Scope kinds:

```text
Module
Function
Block
Closure
MatchArm
Loop
```

Ví dụ:

```axiom
fn main() {
    let x = 10

    {
        let y = x
    }
}
```

scope:

```text
Function
└── Block
    ├── x
    └── Block
        └── y
```

Lookup `y`:

```text
inner block
→ function block
→ module
```

---

# 38. Resolver không kiểm type

Ví dụ:

```axiom
let x = foo(42)
```

Resolver chỉ cần:

```text
foo → FunctionId
```

Nó không cần biết:

```text
42 : i32?
foo expects f64?
```

Đó là type checker.

---

# 39. Resolver output

HIR:

```text
Call {
    callee: Function(FunctionId(7))
    args: [
        Literal(42)
    ]
}
```

Đây là bước semantic identity đầu tiên.

---

# 40. `fn main(){}` HIR

AST:

```text
Function
    name = "main"
```

Resolver:

```text
SymbolId(main)
```

HIR:

```text
Function {
    function_id: FunctionId(...)
    params: []
    body: Block([])
}
```

Vẫn chưa có:

```text
ownership
MIR
machine code
```

---

# 41. HIR normalization

Một số syntax sugar được normalize ở đây.

Ví dụ method:

```axiom
v.length()
```

sau method resolution:

```text
Call(
    FunctionId(length),
    [v]
)
```

Nhưng trước khi trait/method resolution hoàn tất, HIR có thể giữ metadata:

```text
ResolvedMethodCall {
    receiver
    function_id
    dispatch_kind
}
```

để diagnostics/debugging.

---

# 42. HIR invariants

```text id="p4e5ax"
AHIR-20
Every HIR node has a typed HIR ID.

AHIR-21
Ordinary resolved names reference semantic identities.

AHIR-22
No unresolved ordinary identifier remains after resolution.

AHIR-23
Source spans are preserved.

AHIR-24
AST syntax-only details may be normalized when semantics are preserved.

AHIR-25
HIR does not perform ownership verification.

AHIR-26
HIR does not perform capability verification.

AHIR-27
HIR does not decide physical storage.

AHIR-28
HIR is target-independent.

AHIR-29
Resolver is deterministic.

AHIR-30
Declaration collection precedes body resolution.

AHIR-31
Forward function references are supported.

AHIR-32
Mutual recursion is supported where declarations permit it.

AHIR-33
Visibility is checked after candidate lookup.

AHIR-34
Ambiguous resolution is a compile-time error.

AHIR-35
Resolver does not infer runtime behavior.
```

---

# 43. Vertical Slice VS-001 bây giờ đã có hình dạng hoàn chỉnh

```text
fn main() {}
```

đi qua:

```text
Source
  ↓
Lexer
  ↓
TokenStream
  ↓
Parser
  ↓
AST
  ↓
Declaration Collector
  ↓
Resolver
  ↓
HIR
```

Tiếp theo:

```text
HIR
 ↓
Type Checker
 ↓
Typed HIR
 ↓
Ownership
 ↓
MIR
```

---

# 44. Type Checker tối thiểu cho VS-001

`fn main() {}` cần được type-check thành:

```text
FunctionType {
    params: []
    return: Unit
}
```

Body:

```text
BlockType = Unit
```

Do đó:

```text
main : () -> unit
```

Đây là semantic contract đầu tiên của function.

---

# 45. Typed HIR

```text
Function main
type: () -> unit

Body
type: unit
```

Không cần runtime metadata.

Sau đó Ownership analyzer:

```text
main
    no locals
    no moves
    no views
    no drops
```

MIR:

```text
BB0:
    RETURN unit
```

Verifier:

```text
VALID
```

LIR:

```text
RETURN
```

x86:

```text
xor eax, eax
ret
```

và cuối cùng linker/startup.

---

# 46. Điều quan trọng nhất đã đạt được

Chúng ta đang giữ được boundary:

```text
Lexer
  lexical

Parser
  syntax

Resolver
  identity

TypeChecker
  type

Ownership
  ownership

Capability
  alias/access

MIR
  execution semantics

Verifier
  semantic proof

Optimizer
  performance

LIR
  machine-neutral codegen

Backend
  machine representation

Linker
  binary composition
```

Không có subsystem nào “biết quá nhiều”.

Đây chính là thứ sẽ giúp Axiom sau này có thể:

- tự host
- incremental compile
- parallel compile
- IDE/LSP
- AI tooling
- nhiều backend
- nhiều OS
- không phụ thuộc LLVM về lâu dài.

---

## Bước tiếp theo đã được chốt: `TYPE-001 + TYPED-HIR-001`

Ta sẽ triển khai **type system engine tối thiểu nhưng thật**, bắt đầu bằng:

```text
Unit
Never
Bool
I8..I64
U8..U64
ISize
USize
F32
F64
Tuple
Function
```

sau đó xử lý chính xác:

```axiom
fn main() {}
fn main() -> i32 { 42 }
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

và đặc biệt chốt **type inference của numeric literal**, implicit conversion, function call checking và representation của `TypeId` trước khi bước vào Ownership/MIR.