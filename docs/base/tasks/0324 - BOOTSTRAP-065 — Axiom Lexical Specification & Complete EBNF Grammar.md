Tiếp tục.

# BOOTSTRAP-065 — Axiom Lexical Specification & Complete EBNF Grammar

Mục tiêu của 065 là biến surface syntax của 064 thành **một grammar có thể đưa thẳng cho lexer/parser implementation**.

Một quyết định quan trọng: **EBNF là specification**, không nhất thiết parser implementation phải là parser generator. Parser của Axiom có thể dùng recursive-descent + Pratt parser/precedence climbing nếu phù hợp.

---

# 1. Kiến trúc lexical pipeline

Đề xuất:

```text
UTF-8 Source
    ↓
Unicode validation
    ↓
Lexer
    ↓
Token stream
    ↓
Parser
    ↓
AST
```

Lexer **không hiểu ownership, type, trait, ABI...**

Ví dụ:

```axiom
let x = foo<Bar>(value)
```

lexer chỉ cần nhận biết:

```text
LET
IDENT(x)
EQUAL
IDENT(foo)
LT
IDENT(Bar)
GT
LPAREN
IDENT(value)
RPAREN
```

Việc `<Bar>` là generic argument hay toán tử `<` thuộc parser/resolver, không phải lexer.

---

# 2. UTF-8 source

Axiom source file mặc định là UTF-8.

Quy tắc:

```text
valid UTF-8 → compile
invalid UTF-8 → lexical diagnostic
```

Không có implicit Latin-1/Windows-1252 interpretation.

---

# 3. Unicode identifiers

Identifier nên tuân theo Unicode XID:

```text
XID_Start XID_Continue*
```

cho phép:

```axiom
let tên = "Axiom"
let 用户 = 10
```

Nhưng formatter/linter có thể khuyến nghị ASCII cho public API.

Không cho phép:

```text
emoji
combining sequence bất thường
Unicode confusable
```

một cách tùy tiện trong tooling.

Compiler phải normalize identifier theo một quy tắc xác định, tốt nhất là **NFC**, trước khi so sánh semantic identity.

---

# 4. Whitespace

Whitespace gồm:

```text
space
tab
CR
LF
Unicode whitespace được cho phép theo lexical specification
```

Whitespace thông thường không có semantic meaning.

Axiom **không phải indentation-sensitive language**.

---

# 5. Newline

Newline được lexer giữ lại dưới dạng:

```text
NEWLINE
```

hoặc equivalent trivia information để parser có thể phân biệt:

```axiom
foo
(bar)
```

với các trường hợp cần statement termination.

Nhưng newline **không tự động kết thúc expression**.

Ví dụ hợp lệ:

```axiom
let x =
    foo(
        a,
        b
    )
```

---

# 6. Statement termination

Axiom sử dụng cơ chế:

```text
newline-sensitive automatic termination
+
explicit semicolon
```

Nhưng chỉ khi parser xác định token trước đó có khả năng kết thúc statement.

Ví dụ:

```axiom
let x = 10
let y = 20
```

được hiểu như:

```text
let x = 10
NEWLINE
let y = 20
```

Trong:

```axiom
let x =
    10 +
    20
```

newline không kết thúc statement.

---

# 7. Semicolon

`;` vẫn là token hợp lệ:

```axiom
let x = 10;
let y = 20;
```

Điều này đặc biệt hữu ích cho generated code và một số trường hợp parser ambiguity.

---

# 8. Comments

```text
// line comment

/*
   block comment
*/
```

Block comment nên **nest được**:

```axiom
/*
    outer
    /*
        inner
    */
*/
```

Điều này giúp comment code lớn an toàn hơn.

---

# 9. Documentation comments

```axiom
/// Documentation
```

và:

```axiom
/**
 * Documentation
 */
```

được lexer/parser ghi nhận cho documentation system.

Không phải semantic declaration.

---

# 10. Keywords

Frozen keyword set:

```text
as
async
await
break
comptime
const
continue
else
enum
extern
false
fn
for
if
impl
import
in
let
loop
match
mod
pub
return
struct
trait
true
type
unsafe
var
while
```

Không có:

```text
class
new
delete
throw
catch
finally
override
virtual
public
private
protected
```

---

# 11. Identifier vs keyword

Lexer nhận:

```text
foo
Foo
_foo
foo123
```

nhưng:

```text
fn
struct
trait
```

được tokenize thành keyword.

Reserved keyword không được dùng trực tiếp làm identifier.

---

# 12. Raw identifier

Tôi đề xuất **không đưa raw identifier vào Core v1**.

Ví dụ:

```text
r#type
```

không cần thiết ở giai đoạn đầu.

Nếu sau này FFI cần truy cập symbol/field trùng keyword, có thể bổ sung một cơ chế escaped identifier.

Lý do:

> Đừng thêm syntax chỉ vì “có thể một ngày nào đó cần”.

---

# 13. Integer literals

Các dạng:

```axiom
123
1_000_000
0xff
0b1010
0o755
```

Cho phép `_` để readability.

Không có implicit octal kiểu:

```text
0755
```

để tránh ambiguity.

---

# 14. Integer literal typing

Literal:

```axiom
42
```

không nhất thiết mặc định `i32` ngay ở lexer.

Parser tạo:

```text
IntegerLiteral(42)
```

Type inference quyết định type sau.

Ví dụ:

```axiom
let x: u64 = 42
```

→ `u64`.

---

# 15. Overflow literal

Nếu literal không biểu diễn được trong type được chọn:

```axiom
let x: u8 = 1000
```

→ compile-time diagnostic.

Không wrap silently.

---

# 16. Float literals

```axiom
1.0
3.14159
1e10
1.5e-3
```

Hex float **không cần Core v1**.

Có thể bổ sung system/compiler extension sau.

---

# 17. Character literal

```axiom
'a'
'中'
'\n'
```

Character là một Unicode scalar value.

Không phải arbitrary byte.

---

# 18. Byte literal

Để xử lý binary:

```axiom
b'a'
b'\xFF'
```

Byte literal có type:

```text
u8
```

---

# 19. String literal

```axiom
"hello"
"Xin chào"
```

UTF-8 semantic text.

Escape:

```text
\n
\r
\t
\\
\"
\0
\xNN
\u{NNNN}
```

---

# 20. Raw string

Nên hỗ trợ vì rất hữu ích cho:

- regex;
- JSON;
- paths;
- source generation;
- AI-generated code.

Ví dụ:

```axiom
r"hello\nworld"
```

→ `\n` không được interpret.

---

# 21. Multiline string

```axiom
"""
line 1
line 2
line 3
"""
```

Rất hữu ích cho:

- SQL;
- shader;
- templates;
- generated source;
- prompts.

Đề xuất có trong Core syntax.

---

# 22. Raw multiline string

Có thể:

```axiom
r"""
hello
\n
"""
```

hoặc delimiter mở rộng nếu sau này cần.

---

# 23. Boolean literals

```axiom
true
false
```

---

# 24. Null

Không có:

```axiom
null
nil
nullptr
```

trong safe Core.

Absence:

```axiom
Option<T>
```

---

# 25. Punctuation

Core punctuation:

```text
(
)
[
]
{
}

,
.
:
;
?
!
_

@
```

---

# 26. Operators

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
=
+=
-=
*=
/=
%=
&=
|=
^=
<<
>>
<<=
>>=
&
|
^
~
```

---

# 27. Compound punctuation

Generic:

```text
<
>
```

Range:

```text
..
..=
```

Path:

```text
.
```

Attribute:

```text
@
```

Không cần:

```text
::
```

cho normal source syntax.

---

# 28. Operator precedence

Từ cao xuống thấp:

```text
1. postfix
2. unary
3. multiplicative
4. additive
5. shift
6. relational
7. equality
8. bitwise AND
9. bitwise XOR
10. bitwise OR
11. logical AND
12. logical OR
13. range
14. assignment
```

---

# 29. Postfix

Cao nhất:

```text
x(...)
x[...]
x.field
x?.field      // nếu sau này optional chaining được thêm
```

Tuy nhiên tôi **không freeze `?.` ở v1**.

---

# 30. Unary

```text
-x
+x
!x
~x
```

Dereference:

```text
*x
```

nhưng raw-pointer dereference chỉ hợp lệ trong unsafe/system semantics.

---

# 31. Multiplication

```text
*
/
%
```

left associative.

---

# 32. Addition

```text
+
-
```

left associative.

---

# 33. Shift

```text
<<
>>
```

left associative.

---

# 34. Relational

```text
<
<=
>
>=
```

---

# 35. Equality

```text
==
!=
```

---

# 36. Bitwise

```text
&
^
|
```

---

# 37. Logical

```text
&&
||
```

Short-circuit.

---

# 38. Range

```text
a..b
a..=b
```

Range có precedence thấp hơn logical expression nhưng cao hơn assignment.

---

# 39. Assignment

```text
=
+=
-=
*=
/=
%=
&=
|=
^=
<<=
>>=
```

right associative.

---

# 40. `?`

`?` là postfix control-flow operator nhưng có semantic đặc biệt.

```axiom
foo()?
```

Parser xử lý như postfix operator.

Verifier/type checker xử lý Result/Option propagation.

---

# 41. Generic ambiguity

Một vấn đề quan trọng:

```axiom
foo<Bar>(x)
```

`<` có thể là less-than.

Không để lexer quyết định.

Parser có contextual parsing:

```text
expression `<` expression
```

vs:

```text
generic argument list
```

Resolver/type parser có thể disambiguate khi cần.

---

# 42. Generic declaration

```text
fn foo<T>(...)
struct Vec<T>
trait Iterator<T>
```

---

# 43. Generic type

```axiom
Vec<i32>
Option<String>
Result<Data, Error>
```

---

# 44. Nested generic

```axiom
Vec<Option<Result<Data, Error>>>
```

Parser phải xử lý `>>` đúng ngữ cảnh.

Lexer có thể tokenize `>>` thành shift operator; parser có thể split contextual token khi đang parse generic arguments.

---

# 45. Type grammar

Core:

```text
Type
  = PrimitiveType
  | NamedType
  | GenericType
  | TupleType
  | ArrayType
  | ViewType
  | MutViewType
  | RawPointerType
  | FunctionType
  | DynTraitType
  | NeverType
  | UnitType
```

---

# 46. Primitive types

```text
bool
i8 i16 i32 i64
u8 u16 u32 u64
isize usize
f32 f64
```

---

# 47. Tuple type

```axiom
(i32, f32)
```

Một phần tử:

```axiom
(i32,)
```

Empty tuple:

```axiom
()
```

là `unit`.

---

# 48. Array type

```axiom
[i32; 10]
```

---

# 49. View type

```axiom
view<T>
```

---

# 50. Mutable view

```axiom
mut_view<T>
```

---

# 51. Raw pointer

```axiom
*const T
*mut T
```

---

# 52. Function type

```axiom
fn(i32, i32) -> i32
```

---

# 53. Dynamic trait type

```axiom
dyn Drawable
```

và:

```axiom
dyn Iterator<Item = u8>
```

nếu associated constraints cần syntax này.

---

# 54. Never

```axiom
never
```

Tôi đề xuất có keyword `never` thay vì ký hiệu `!` cho type.

Ví dụ:

```axiom
fn abort() -> never
```

Trong expression:

```text
!
```

vẫn chỉ là logical NOT.

Điều này tránh overload ký hiệu.

---

# 55. Declaration grammar

Khung:

```text
Declaration
  = ModuleDecl
  | ImportDecl
  | ConstDecl
  | StructDecl
  | EnumDecl
  | TraitDecl
  | ImplDecl
  | TypeDecl
  | FunctionDecl
```

---

# 56. Module

```text
module path ;
```

Ví dụ:

```axiom
module graphics.render
```

---

# 57. Import

```text
import path
import path as identifier
```

---

# 58. Const

```text
const identifier : Type = Expression
```

---

# 59. Struct

```text
struct Identifier GenericParams? WhereClause? StructBody
```

---

# 60. Struct body

```text
{
    Field*
}
```

Field:

```text
visibility? identifier : Type
```

---

# 61. Tuple struct

```text
struct Identifier GenericParams? (TypeList?) ;
```

Ví dụ:

```axiom
struct UserId(u64)
```

---

# 62. Enum

```text
enum Identifier GenericParams? WhereClause? {
    Variant*
}
```

---

# 63. Enum variants

```axiom
Red
Green
Blue
```

or:

```axiom
Some(T)
```

or:

```axiom
User {
    id: u64
    name: String
}
```

---

# 64. Trait

```text
trait Identifier GenericParams? WhereClause? {
    TraitItem*
}
```

---

# 65. Impl

```text
impl GenericParams? Type
impl GenericParams? Trait for Type
```

---

# 66. Function

```text
visibility?
async?
unsafe?
fn Identifier GenericParams? Parameters ReturnType? WhereClause? FunctionBody
```

---

# 67. Parameter

```text
identifier : Type
```

Receiver:

```text
self
view<Self>
mut_view<Self>
Self
```

Surface shorthand có thể được resolver xử lý.

---

# 68. Method

Không có grammar riêng.

Đây là chủ ý.

```axiom
impl Vec {
    fn length(self: view<Self>) -> usize {
        ...
    }
}
```

vẫn chỉ là FunctionDecl bên trong impl.

---

# 69. Attribute grammar

```text
Attribute
    = @ Identifier AttributeArgs?
```

Arguments:

```text
@export("foo")
@align(64)
@cfg(target = "x86_64")
```

Nested metadata nếu cần.

---

# 70. Comptime grammar

```text
comptime Block
```

và:

```text
comptime fn ...
```

---

# 71. Async grammar

```text
async fn ...
```

Không có:

```text
async {
}
```

? Tôi đề xuất **có**.

```axiom
let result = async {
    foo().await
}
```

Nó tạo anonymous Future.

---

# 72. Unsafe grammar

```text
unsafe Block
```

và:

```text
unsafe fn ...
```

---

# 73. FFI grammar

```text
extern StringLiteral FunctionDecl
```

hoặc:

```text
extern StringLiteral {
    ForeignItem*
}
```

Ví dụ:

```axiom
extern "C" {
    fn malloc(size: usize) -> *mut u8
}
```

---

# 74. Statements

```text
Statement
    = LetStmt
    | VarStmt
    | ConstStmt
    | ExpressionStmt
    | ReturnStmt
    | BreakStmt
    | ContinueStmt
```

Declarations được parse ở declaration context.

---

# 75. Let

```text
let Pattern TypeAnnotation? = Expression
```

---

# 76. Var

```text
var Pattern TypeAnnotation? = Expression
```

---

# 77. Return

```axiom
return
return expression
```

---

# 78. Break

```axiom
break
break label
break expression
break label expression
```

---

# 79. Continue

```axiom
continue
continue label
```

---

# 80. If

```text
if Expression Block
if Expression Block else Block
if Expression Block else if ...
```

---

# 81. Match

```text
match Expression {
    Pattern Guard? => ExpressionOrBlock
}
```

---

# 82. Loop

```text
loop Label? Block
```

---

# 83. While

```text
while Expression Block
```

---

# 84. For

```text
for Pattern in Expression Block
```

---

# 85. Expressions

Core expression categories:

```text
Literal
Name
Path
Tuple
Array
StructLiteral
Call
Index
Field
Unary
Binary
Assignment
If
Match
Loop
Block
Closure
AsyncBlock
Await
```

---

# 86. Struct literal

```axiom
Point {
    x: 10
    y: 20
}
```

---

# 87. Array literal

```axiom
[1, 2, 3, 4]
```

Repeated:

```axiom
[0; 1024]
```

---

# 88. Tuple literal

```axiom
(10, 20)
```

Unit:

```axiom
()
```

---

# 89. Closure

```axiom
|x, y| x + y
```

or:

```axiom
|x: i32, y: i32| -> i32 {
    x + y
}
```

---

# 90. Move closure

```axiom
move |x| {
    use(x)
}
```

---

# 91. Await

Parser:

```text
PostfixExpression . await
```

Surface:

```axiom
future.await
```

---

# 92. Field access

```axiom
user.name
```

Method call:

```axiom
user.save()
```

---

# 93. Index

```axiom
array[index]
```

---

# 94. Explicit view

```axiom
view(value)
mut_view(value)
```

Đây là ordinary function-like syntax.

Không cần:

```text
&value
&mut value
```

---

# 95. Explicit drop

```axiom
drop(value)
```

ordinary library/compiler-recognized operation.

---

# 96. Full simplified EBNF

Đây là skeleton grammar mà compiler team có thể bắt đầu triển khai:

```text
Program         ::= Item*

Item            ::= Attribute* Visibility?
                    (ModuleDecl
                    | ImportDecl
                    | ConstDecl
                    | StructDecl
                    | EnumDecl
                    | TraitDecl
                    | ImplDecl
                    | TypeDecl
                    | FunctionDecl
                    | ExternDecl)

ModuleDecl      ::= "module" Path Terminator

ImportDecl      ::= "import" Path ("as" Identifier)? Terminator

ConstDecl       ::= "const" Identifier ":" Type "=" Expression Terminator

TypeDecl        ::= "type" Identifier GenericParams? "=" Type Terminator

StructDecl      ::= "struct" Identifier GenericParams?
                    (StructBody | TupleStructBody)

StructBody      ::= "{" Field* "}"

TupleStructBody ::= "(" TypeList? ")" Terminator

EnumDecl        ::= "enum" Identifier GenericParams?
                    "{" Variant* "}"

Variant         ::= Identifier
                  | Identifier "(" TypeList? ")"
                  | Identifier StructBody

TraitDecl       ::= "trait" Identifier GenericParams?
                    WhereClause? "{" TraitItem* "}"

ImplDecl        ::= "impl" GenericParams?
                    (Type | Trait "for" Type)
                    WhereClause? "{" Item* "}"

FunctionDecl    ::= "async"? "unsafe"? "fn"
                    Identifier GenericParams?
                    Parameters ReturnType?
                    WhereClause? Block?

Parameters      ::= "(" ParameterList? ")"

ParameterList   ::= Parameter ("," Parameter)* ","?

Parameter       ::= Identifier ":" Type
                  | Receiver

Receiver        ::= "self"
                  | "view" "<" "Self" ">"
                  | "mut_view" "<" "Self" ">"
                  | "Self"

ReturnType     ::= "->" Type

GenericParams   ::= "<" GenericParamList ">"

GenericParamList ::= GenericParam ("," GenericParam)* ","?

GenericParam    ::= Identifier
                  | Identifier ":" TraitBounds

TraitBounds     ::= TraitBound ("+" TraitBound)*

WhereClause     ::= "where" WherePredicate ("," WherePredicate)*

WherePredicate  ::= Type ":" TraitBounds

Type            ::= PrimitiveType
                  | PathType
                  | GenericType
                  | TupleType
                  | ArrayType
                  | ViewType
                  | MutViewType
                  | RawPointerType
                  | FunctionType
                  | DynTraitType
                  | "never"

ViewType        ::= "view" "<" Type ">"

MutViewType     ::= "mut_view" "<" Type ">"

RawPointerType  ::= "*const" Type
                  | "*mut" Type

FunctionType    ::= "fn" Parameters ReturnType?

TupleType       ::= "(" TypeList? ")"

ArrayType       ::= "[" Type ";" Expression "]"

DynTraitType    ::= "dyn" Path

TypeList        ::= Type ("," Type)* ","?

Block           ::= "{" StatementOrExpression* "}"

Statement       ::= LetStmt
                  | VarStmt
                  | ReturnStmt
                  | BreakStmt
                  | ContinueStmt
                  | ExpressionStmt

LetStmt         ::= "let" Pattern TypeAnnotation?
                    "=" Expression Terminator

VarStmt         ::= "var" Pattern TypeAnnotation?
                    "=" Expression Terminator

ReturnStmt      ::= "return" Expression? Terminator

BreakStmt       ::= "break" Label? Expression? Terminator

ContinueStmt    ::= "continue" Label? Terminator

ExpressionStmt  ::= Expression Terminator

Expression      ::= AssignmentExpression

AssignmentExpression
                ::= LogicalExpression
                    AssignmentOperator AssignmentExpression
                  | LogicalExpression

LogicalExpression
                ::= RangeExpression
                    ("&&" | "||") RangeExpression

RangeExpression ::= EqualityExpression
                    (RangeOperator EqualityExpression)?

EqualityExpression
                ::= RelationalExpression
                    (("==" | "!=") RelationalExpression)*

RelationalExpression
                ::= BitOrExpression
                    (("<" | "<=" | ">" | ">=")
                     BitOrExpression)*

BitOrExpression ::= BitXorExpression
                    ("|" BitXorExpression)*

BitXorExpression ::= BitAndExpression
                     ("^" BitAndExpression)*

BitAndExpression ::= ShiftExpression
                     ("&" ShiftExpression)*

ShiftExpression ::= AddExpression
                    (("<<" | ">>") AddExpression)*

AddExpression   ::= MulExpression
                    (("+" | "-") MulExpression)*

MulExpression   ::= UnaryExpression
                    (("*" | "/" | "%") UnaryExpression)*

UnaryExpression ::= ("!" | "~" | "+" | "-" | "*")
                    UnaryExpression
                  | PostfixExpression

PostfixExpression
                ::= PrimaryExpression
                    Postfix*

Postfix         ::= Arguments
                  | "[" Expression "]"
                  | "." Identifier
                  | "." "await"
                  | "?"

Arguments       ::= "(" ArgumentList? ")"

ArgumentList    ::= Expression ("," Expression)* ","?

PrimaryExpression
                ::= Literal
                  | Path
                  | TupleLiteral
                  | ArrayLiteral
                  | StructLiteral
                  | Block
                  | IfExpression
                  | MatchExpression
                  | LoopExpression
                  | ClosureExpression
                  | AsyncExpression

IfExpression    ::= "if" Expression Block
                    ("else" (IfExpression | Block))?

MatchExpression ::= "match" Expression
                    "{" MatchArm* "}"

MatchArm        ::= Pattern Guard? "=>" ExpressionOrBlock

Guard           ::= "if" Expression

LoopExpression  ::= "loop" Block
                  | "while" Expression Block
                  | "for" Pattern "in" Expression Block

ClosureExpression
                ::= "move"? "|" ParameterList? "|"
                    ReturnType? (Expression | Block)

AsyncExpression ::= "async" Block

Pattern         ::= Identifier
                  | "_"
                  | Literal
                  | TuplePattern
                  | StructPattern
                  | VariantPattern
                  | RangePattern

Attribute       ::= "@" Identifier AttributeArguments?

AttributeArguments
                ::= "(" AttributeArgumentList? ")"

ExternDecl      ::= "extern" StringLiteral
                    (FunctionDecl | "{" Item* "}")

Visibility      ::= "pub"

Label           ::= "'" Identifier

Terminator      ::= ";" | ImplicitTerminator
```

Đây là **grammar architecture**, chưa phải grammar parser implementation cuối cùng. Những phần như automatic terminator, generic disambiguation và pattern parsing cần được formalize thêm trong parser specification.

---

# 97. Parser strategy

Tôi đề xuất:

```text
Lexer
  ↓
Token stream
  ↓
Recursive-descent declaration/type parser
  +
Pratt parser cho expression
  +
Pattern parser
```

Không nên cố nhồi toàn bộ language vào một grammar generator.

Lý do:

- error recovery tốt hơn;
- diagnostics tốt hơn;
- generic `< >` dễ xử lý;
- attribute dễ mở rộng;
- pattern ownership không cần parser biết semantic;
- AI-generated malformed code dễ recover.

---

# 98. Error recovery

Parser phải **không dừng ngay tại lỗi đầu tiên**.

Ví dụ:

```axiom
fn foo(
    x: i32
    y: i32
}

fn bar() {
    ...
}
```

Parser nên báo lỗi `foo`, nhưng vẫn tìm:

```text
fn bar
```

để tiếp tục phân tích.

Synchronization points:

```text
}
;
fn
struct
enum
trait
impl
import
```

---

# 99. Parser không làm semantic verification

Parser chỉ trả:

```text
AST
```

Không được:

```text
parser → ownership check
parser → type inference
parser → trait solving
```

Pipeline giữ nguyên:

```text
Lexer
 ↓
Parser
 ↓
AST
 ↓
Resolver
 ↓
Type System
 ↓
HIR
 ↓
MIR
 ↓
Verification
```

---

# 100. Frozen invariants — BOOTSTRAP-065

```text
ALEX-20   Axiom source files are UTF-8.
ALEX-21   Invalid UTF-8 is a lexical error.
ALEX-22   Identifier matching uses defined Unicode normalization.
ALEX-23   Identifier syntax follows Unicode identifier rules.
ALEX-24   Unicode identifiers are semantic identifiers, not display aliases.
ALEX-25   ASCII identifiers remain valid.
ALEX-26   Public API naming conventions are tooling concerns.
ALEX-27   Whitespace has no ordinary semantic meaning.
ALEX-28   Axiom is not indentation-sensitive.
ALEX-29   Newline information may be retained for statement termination.
ALEX-30   Newline cannot terminate an expression where continuation is syntactically valid.
ALEX-31   Explicit semicolon remains valid.
ALEX-32   Automatic statement termination is parser-defined.
ALEX-33   Nested block comments are supported.
ALEX-34   Documentation comments are preserved as metadata.
ALEX-35   Core keyword set is explicitly registered.
ALEX-36   Unregistered reserved keywords are not implicitly introduced.
ALEX-37   Raw identifiers are not required by Core v1.
ALEX-38   Integer literals support decimal, binary, octal and hexadecimal forms.
ALEX-39   Integer separators using underscore are supported.
ALEX-40   Implicit legacy octal syntax is not supported.
ALEX-41   Integer literal overflow is a compile-time diagnostic.
ALEX-42   Integer literal typing is resolved after lexical parsing.
ALEX-43   Floating literals support decimal/exponent notation.
ALEX-44   Character literals represent Unicode scalar values.
ALEX-45   Byte literals represent u8 values.
ALEX-46   String literals represent UTF-8 text semantics.
ALEX-47   Escape sequences are explicitly defined.
ALEX-48   Raw strings are supported.
ALEX-49   Multiline strings are supported.
ALEX-50   Boolean literals are true and false.
ALEX-51   Null is not a safe Core literal.
ALEX-52   Absence is represented through Option.
ALEX-53   Operator tokens are explicitly registered.
ALEX-54   Operator precedence is fixed by the language specification.
ALEX-55   Binary arithmetic operators are left associative unless explicitly specified otherwise.
ALEX-56   Assignment operators are right associative.
ALEX-57   Logical && and || are short-circuit operators.
ALEX-58   Range operators have defined precedence.
ALEX-59   ? is a postfix propagation operator.
ALEX-60   Cast and bitcast syntax remain semantically distinct.
ALEX-61   Generic parsing is contextual and does not rely on lexer-only disambiguation.
ALEX-62   Shift tokens may be contextually split while parsing generic arguments.
ALEX-63   Type syntax is explicit and parseable independently.
ALEX-64   view<T> is a Core type syntax.
ALEX-65   mut_view<T> is a Core type syntax.
ALEX-66   Raw pointer syntax is restricted semantically to unsafe/system contexts.
ALEX-67   Function types use fn(...) -> T syntax.
ALEX-68   dyn Trait explicitly represents dynamic trait abstraction.
ALEX-69   never is the explicit Never type.
ALEX-70   Unit is represented by ().
ALEX-71   struct is the primary aggregate declaration syntax.
ALEX-72   enum is the primary algebraic sum-type declaration syntax.
ALEX-73   trait is the primary behavior abstraction syntax.
ALEX-74   impl is the primary implementation syntax.
ALEX-75   Methods share function grammar with ordinary functions.
ALEX-76   Method semantics are resolved after parsing.
ALEX-77   let denotes immutable binding syntax.
ALEX-78   var denotes mutable binding syntax.
ALEX-79   Ownership transfer is not encoded through punctuation.
ALEX-80   Lifetime annotations are absent from Core syntax.
ALEX-81   Borrow annotations are absent from Core syntax.
ALEX-82   Class syntax is absent from Core.
ALEX-83   Exception hierarchy syntax is absent from Core.
ALEX-84   Closure syntax explicitly identifies closure expressions.
ALEX-85   move closure syntax explicitly requests ownership capture.
ALEX-86   async syntax represents control-flow abstraction.
ALEX-87   await syntax represents suspension.
ALEX-88   spawn remains a library/runtime operation.
ALEX-89   unsafe block syntax marks an unsafe boundary.
ALEX-90   unsafe function syntax marks an unsafe callable contract.
ALEX-91   extern syntax marks foreign ABI boundaries.
ALEX-92   ABI identity is not inferred from arbitrary syntax.
ALEX-93   Attributes use @ syntax.
ALEX-94   Attribute semantics come from the registered attribute system.
ALEX-95   Unknown semantic attributes produce diagnostics.
ALEX-96   Parser output is syntactic AST, not verified semantic IR.
ALEX-97   Parser does not perform ownership verification.
ALEX-98   Parser does not perform trait solving.
ALEX-99   Parser must support structured error recovery.
ALEX-100  Lexer/parser behavior is deterministic.
```

---

## Một điểm tôi muốn khóa thêm

Sau 065, Axiom đã có ba tầng rất rõ:

```text
                PROGRAMMER
                    │
                    ▼
          ┌──────────────────┐
          │ Surface Syntax   │
          │  BOOTSTRAP-064   │
          └────────┬─────────┘
                   │
                   ▼
          ┌──────────────────┐
          │ Lexer / Parser   │
          │  BOOTSTRAP-065   │
          └────────┬─────────┘
                   │
                   ▼
          ┌──────────────────┐
          │ Semantic System  │
          │  020 → 063       │
          └──────────────────┘
```

Và điều này rất quan trọng với mục tiêu **AI-friendly**:

AI có thể sinh:

```axiom
var users = Vec<User>.new()

for user in users {
    println(user.name)
}
```

mà không phải đồng thời “suy nghĩ” về:

```text
lifetime
borrow region
alias lifetime
drop scope
reference qualifier
```

Compiler vẫn làm toàn bộ việc đó phía dưới.

---

### Mốc kế tiếp: **BOOTSTRAP-066 — Axiom Standard Syntax Patterns & Idiomatic Programming Model**

Bước này không nên nhảy ngay vào compiler implementation. Sau khi grammar đã freeze, cần xác định **“cách viết Axiom chuẩn”**: constructor/initialization, method/extension method, collections, error handling, ownership transfer, views, traits, generics, callbacks/closures, async, concurrency, FFI và module organization.

Mục tiêu là tránh tình trạng **grammar hợp lệ nhưng code Axiom thực tế lại rườm rà**, đồng thời dùng các pattern này làm cơ sở cho **Axiom Core/Std examples + compiler dogfooding + AI code generation**.