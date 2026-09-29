# XXXVI — LEX-001: triển khai Lexer Axiom v0.1

Ta tiếp tục từ đúng điểm đã chốt: **Kernel → Lexer → Parser → vertical slice**.

Mục tiêu của Lexer không phải “đọc được source”, mà là tạo một **TokenStream ổn định, deterministic, có span chính xác**, đủ tốt để toàn bộ compiler phía sau không phải quan tâm đến UTF-8 hay lexical recovery nữa.

---

## 1. Boundary chính thức

```text
SourceText
    │
    ├── UTF-8 validation
    │
    ▼
Lexer
    │
    ▼
TokenStream
    │
    ├── Parser
    └── Diagnostics
```

Lexer tuyệt đối không gọi:

```text
Resolver
TypeChecker
TraitSolver
Ownership
MIR
Backend
```

Lexer cũng không được quyết định:

```text
foo       → variable?
foo       → type?
foo       → function?
```

Nó chỉ biết:

> đây là identifier có spelling `foo`.

---

# 2. Token representation

Token nên cực kỳ nhỏ:

```text
Token {
    kind: TokenKind
    span: Span
}
```

Không cần:

```text
Token {
    text: String
}
```

vì:

```text
source[span]
```

đã lấy được raw spelling.

Điều này giảm allocation rất lớn.

---

# 3. TokenKind

Chia thành nhóm.

### Identifier

```text
Identifier
```

### Keywords

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
false
fn
for
if
impl
import
in
let
match
module
pub
return
static
struct
trait
true
type
unsafe
var
where
while
extern
```

Tốt nhất implementation có:

```text
TokenKind::Keyword(Keyword)
```

thay vì 30 enum variant hoàn toàn riêng biệt.

Ví dụ:

```text
Keyword::Fn
Keyword::Struct
Keyword::Trait
```

### Literals

```text
IntLiteral
FloatLiteral
StringLiteral
ByteStringLiteral
```

Lexer không quyết định literal đó có vừa `i32` hay không.

---

# 4. Punctuation/operator

```text
Plus
Minus
Star
Slash
Percent

PlusWrap
MinusWrap
StarWrap

PlusSat
MinusSat
StarSat

Amp
Pipe
Caret
Tilde

AndAnd
OrOr

Shl
Shr

EqEq
NotEq
Lt
LtEq
Gt
GtEq

Assign

Arrow
FatArrow

Dot
Range
RangeInclusive

Question
At
Colon
ColonColon

Comma
Semicolon

LParen
RParen
LBracket
RBracket
LBrace
RBrace
```

EOF:

```text
Eof
```

Lỗi:

```text
Error
```

---

# 5. Không cần token cho whitespace

Ví dụ:

```axiom id="t3l3u6"
let x = 42
```

và:

```axiom id="49wyqb"
let    x     =      42
```

cùng TokenStream semantic.

Whitespace chỉ ảnh hưởng:

- source span
- string literal
- comment handling
- parser recovery nếu cần context

---

# 6. Comment

Axiom v0.1:

```text
// line comment

/*
   block comment
*/
```

Block comment **được phép nested**.

Ví dụ:

```text
/*
    outer
    /*
        inner
    */
    outer
*/
```

Lexer cần counter:

```text
depth = 1

/* → depth += 1
*/ → depth -= 1

depth == 0 → end
```

Không dùng regex.

---

# 7. UTF-8

Lexer đầu tiên phải validate UTF-8.

Input:

```text
fn main() {
    let tiếng_việt = 42
}
```

Identifier Unicode được chấp nhận nếu:

```text
XID_Start
XID_Continue
```

và `_`.

Không normalize Unicode tự động.

Ví dụ hai identifier Unicode có representation khác nhau nhưng canonical-equivalent:

```text
é
e + combining acute
```

không tự động coi là cùng identifier.

Đây là quyết định quan trọng để compiler deterministic.

---

# 8. Identifier algorithm

Conceptual:

```text
if XID_Start(c) || c == '_':
    consume XID_Continue / '_'
```

Sau khi lấy raw identifier:

```text
lookup_keyword(identifier)
```

Nếu trùng keyword:

```text
"fn" → Keyword(Fn)
```

nếu không:

```text
"function_name" → Identifier
```

Không để parser phải kiểm tra string `"fn"`.

---

# 9. Keyword table

Nên dùng generated/static table thay vì chuỗi `if` dài.

Ví dụ concept:

```text
KEYWORDS = {
    "fn": Fn,
    "let": Let,
    "var": Var,
    "struct": Struct,
    ...
}
```

Compiler có thể dùng perfect hash hoặc trie sau này.

MVP:

```text
small deterministic lookup table
```

là đủ.

Không tối ưu sớm.

---

# 10. Number lexer — điểm phải làm rất cẩn thận

Axiom hỗ trợ:

```text
123
1_000_000

0xff
0b1010
0o755
```

Không có leading-zero octal.

Do đó:

```text
0123
```

là decimal `123`, không phải octal.

---

# 11. Raw literal spelling phải được giữ

Lexer chỉ xác định:

```text
IntLiteral
```

không biến ngay:

```text
1_000
```

thành số binary.

Token vẫn:

```text
IntLiteral
span = ...
```

Type checker/constant evaluator mới diễn giải.

Điều này cho phép diagnostic tốt:

```text
integer literal does not fit i32
```

và vẫn biết source viết thế nào.

---

# 12. Float detection

Các case:

```text
1.0
0.5
42.25
```

là float.

Nhưng:

```text
1..10
```

phải là:

```text
IntLiteral(1)
Range(..)
IntLiteral(10)
```

không phải:

```text
FloatLiteral(1.)
```

Đây là một trong những lexer tests bắt buộc.

---

# 13. Lookahead rule cho `.`

Lexer gặp:

```text
1.
```

phải xem context tiếp theo.

Nếu:

```text
1..10
```

→ range.

Nếu:

```text
1..=10
```

→ inclusive range.

Nếu:

```text
1.5
```

→ float.

Nếu:

```text
foo.bar
```

→ dot.

Algorithm concept:

```text
digit
  ↓
digits
  ↓
'.'
  ├── next == '.' → integer + range
  ├── next == digit → float
  └── otherwise → integer + dot/context
```

---

# 14. String literal

```axiom id="2h4t0r"
"hello"
```

→ `StringLiteral`.

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

Lexer cần kiểm:

- escape hợp lệ
- Unicode scalar hợp lệ
- `\u{...}` hợp lệ
- string đóng đúng

Nhưng lexer chưa biến thành `Text`.

Nó chỉ ghi:

```text
StringLiteral
```

---

# 15. Byte string

```text
b"hello"
```

→ `ByteStringLiteral`.

Khác:

```text
"hello"
```

→ `StringLiteral`.

Byte string không được chứa Unicode character trực tiếp ngoài phạm vi byte hợp lệ theo rule đã đóng.

---

# 16. String interpolation

Nếu giữ interpolation trong v0.1 như đã thiết kế, lexer phải có state machine.

Ví dụ concept:

```text
"hello {name}"
```

Token:

```text
StringStart
StringText("hello ")
InterpolationStart
Identifier(name)
InterpolationEnd
StringEnd
```

Không tokenize toàn bộ string thành một token duy nhất.

---

# 17. Lexer state machine

Không viết lexer thành một hàm khổng lồ.

Nên chia:

```text
Lexer
├── Cursor
├── whitespace
├── comment
├── identifier
├── number
├── string
├── byte_string
├── operator
└── diagnostics
```

State:

```text
Normal
String
Interpolation
BlockComment
```

---

# 18. Cursor

`Cursor` chịu trách nhiệm rất thấp tầng:

```text
peek()
peek_n(n)
advance()
consume_if(c)
position()
eof()
slice(start, end)
```

Nó làm việc với byte offset.

UTF-8 decoding chỉ được thực hiện khi cần đọc Unicode scalar.

---

# 19. Lexer không được tạo substring

Sai:

```text
text.substring(start, end)
```

rồi:

```text
HashMap<String, Keyword>
```

cho mỗi identifier.

Đúng:

```text
Span
 ↓
source slice
 ↓
lookup
```

Nếu keyword lookup cần string tạm thời, implementation có thể dùng temporary slice/string view; không lưu allocation trong Token.

---

# 20. Error recovery

Lexer không được dừng compiler ở lỗi đầu tiên.

Ví dụ:

```axiom id="7xjv6b"
fn main() {
    let x = "abc
    let y = 42
}
```

Lexer phát:

```text
AX_LEX_0001 unterminated string literal
```

sau đó cố gắng tìm:

```text
newline / quote / EOF
```

để tiếp tục.

---

# 21. Stable diagnostics

Đề xuất mã:

```text
AX_LEX_0001 Invalid UTF-8
AX_LEX_0002 Invalid identifier character
AX_LEX_0003 Unterminated block comment
AX_LEX_0004 Unterminated string literal
AX_LEX_0005 Invalid escape sequence
AX_LEX_0006 Invalid Unicode escape
AX_LEX_0007 Invalid byte string
AX_LEX_0008 Invalid numeric literal
AX_LEX_0009 Invalid operator
```

Message có thể thay đổi.

Code không đổi.

---

# 22. Lexer invariants

Bổ sung vào SPEC/implementation contract:

```text
ALEX-41
Lexer never performs semantic name resolution.

ALEX-42
Lexer never performs type inference.

ALEX-43
Lexer never performs ownership analysis.

ALEX-44
Every emitted token has a valid source span.

ALEX-45
Token spans are byte ranges into the original source.

ALEX-46
Lexer output is deterministic.

ALEX-47
Whitespace and comments do not alter token semantics.

ALEX-48
Unicode identifier identity is based on original decoded scalar sequence.

ALEX-49
Lexer does not implicitly normalize identifiers.

ALEX-50
Numeric interpretation beyond lexical classification is deferred.

ALEX-51
Range syntax is distinguished from floating-point syntax.

ALEX-52
Lexer recovery is deterministic.

ALEX-53
Lexer never allocates token-owned source text unnecessarily.

ALEX-54
Keyword recognition is lexical, not semantic.

ALEX-55
String escape validation is deterministic.

ALEX-56
Nested block comments are supported.

ALEX-57
Lexer diagnostics use stable diagnostic codes.
```

---

# 23. Test matrix

Không chỉ test vài token.

### Basic

```text
fn
let
var
struct
enum
trait
impl
```

### Identifier

```text
foo
_foo
foo123
_
tiếngViệt
Δvalue
```

### Numbers

```text
0
42
1_000
0xff
0b1010
0o755
1.0
0.5
1..10
1..=10
```

### Operators

```text
+
+%
+|
==
!=
<=
>=
&&
||
<<
>>
->
=>
::
```

### Strings

```text
"hello"
"hello\nworld"
"\u{1F600}"
b"abc"
```

### Comments

```text
// comment

/*
 comment
*/

/*
 outer
 /*
 nested
 */
*/
```

---

# 24. Golden token tests

Ví dụ:

```axiom id="04u7k3"
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

Golden:

```text
Keyword(Fn)
Identifier
LParen
Identifier
Colon
Identifier
Comma
Identifier
Colon
Identifier
RParen
Arrow
Identifier
LBrace
Identifier
Plus
Identifier
RBrace
Eof
```

Mỗi token:

```text
kind
start
end
```

được kiểm.

---

# 25. Fuzz test Lexer

Ngay từ đầu nên có:

```text
random bytes
random Unicode
random operators
random nested comments
random strings
random numbers
```

Invariant:

> Lexer không được crash.

Các input không hợp lệ chỉ được:

```text
diagnostic
Error token
EOF
```

chứ không:

```text
segmentation fault
panic compiler
infinite loop
```

---

# 26. Lexer performance

Lexer là hot path.

Mục tiêu:

```text
O(n)
```

với:

```text
n = source bytes
```

Không được:

```text
O(n²)
```

do substring/re-tokenization.

Sau này có thể SIMD/parallel lex file-level, nhưng v0.1 chưa cần.

---

# 27. Sau Lexer: Parser

Ngay khi `LEX-001` xanh, chuyển sang:

# `PARSE-001 — Pratt + Recursive Descent`

Kiến trúc:

```text
Parser
├── cursor
├── items
├── types
├── expressions
├── statements
├── patterns
├── attributes
├── precedence
├── recovery
└── tests
```

Parser nhận:

```text
TokenStream
```

và trả:

```text
AST
```

---

# 28. AST không được chứa semantic identity

Ví dụ parser gặp:

```axiom id="jy4t0a"
foo(x)
```

AST:

```text
CallExpr {
    callee: NameExpr("foo")
    args: [NameExpr("x")]
}
```

Không được parser tự quyết:

```text
FunctionId(17)
```

Đó là resolver.

---

# 29. AST IDs

Mỗi node:

```text
AstNode {
    id: ExprId
    span: Span
    kind: ExprKind
}
```

hoặc tương đương typed arenas:

```text
ExprArena
StmtArena
PatternArena
ItemArena
TypeSyntaxArena
```

Không dùng raw pointer identity.

---

# 30. Parser expression engine

Dùng Pratt parser.

Precedence đã đóng:

```text
assignment
||
&&
|
^
&
== !=
< <= > >=
<< >>
+ - +% -% +| -|
* / % *% *|
as
unary
postfix
primary
```

Ví dụ:

```text
a + b * c
```

AST:

```text
a + (b * c)
```

không phải:

```text
(a + b) * c
```

---

# 31. Postfix chain

Parser phải hỗ trợ:

```axiom id="3i5k0w"
foo.bar()[x].field.await?
```

theo chuỗi:

```text
primary
  ↓
field
  ↓
call
  ↓
index
  ↓
field
  ↓
await
  ↓
try
```

Không nên tạo parser riêng cho từng combination.

---

# 32. Generic ambiguity

Đây là parser trap quan trọng:

```axiom id="e4s8d1"
foo<Bar>(x)
```

versus:

```axiom id="2k1qce"
a < b > c
```

Lexer không giải quyết.

Parser dùng context để xác định `<` là:

```text
less-than
```

hay:

```text
generic argument delimiter
```

Không hack lexer bằng cách tạo:

```text
GenericOpen
GenericClose
```

vì điều đó làm lexical layer biết syntax semantics.

---

# 33. Parser milestone

```text
PARSE-001
empty function

PARSE-002
function parameters/return

PARSE-003
let/var

PARSE-004
expressions

PARSE-005
struct/enum

PARSE-006
match/patterns

PARSE-007
generics

PARSE-008
traits/impl

PARSE-009
closures

PARSE-010
async/await

PARSE-011
unsafe/raw pointers

PARSE-012
error recovery
```

---

# 34. Nhưng không đợi Parser hoàn thiện mới chạy compiler

Ngay:

```text
PARSE-001
```

phải nối:

```text
AST
 ↓
Resolver
 ↓
HIR
```

và build:

```text
fn main() {}
```

Ngay khi:

```text
PARSE-002
```

thì nối:

```text
fn main() -> i32 { 42 }
```

Ngay khi:

```text
PARSE-004
```

thì:

```text
fn main() -> i32 {
    20 + 22
}
```

được đưa tới MIR/backend.

Đây là cách Axiom tránh “frontend hoàn hảo nhưng compiler không chạy được”.

---

# 35. Vertical slice hiện tại

Sau LEX-001 + PARSE-001, target là:

```text
fn main() {}
```

```text
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
TypeCheck
 ↓
Ownership
 ↓
MIR
 ↓
Verifier
 ↓
LIR
 ↓
MachineIR
 ↓
ELF
 ↓
axiom-link
 ↓
hello
```

Sau PARSE-002:

```text
fn main() -> i32 {
    42
}
```

Sau PARSE-004:

```text
fn main() -> i32 {
    20 + 22
}
```

Sau đó mới mở rộng:

```text
let
var
if
while
struct
enum
match
function calls
```

---

# 36. Một thay đổi nhỏ nhưng rất quan trọng với implementation

Ta nên tạo một **Compiler Contract Test** xuyên suốt:

```text
tests/compiler/vertical/
├── 001_empty_main.ax
├── 002_return_42.ax
├── 003_add.ax
├── 004_locals.ax
└── manifest.toml
```

Mỗi test lưu:

```text
source
expected diagnostics
expected HIR
expected MIR
expected LIR
expected exit code
```

Không nhất thiết mọi tầng đều có golden ngay lập tức.

Nhưng với các milestone nền tảng:

```text
AST
HIR
MIR
```

nên có golden.

---

# 37. Chuỗi tiếp theo đã được chốt

Sau `LEX-001`:

```text
LEX-001
  ↓
PARSE-001
  ↓
AST-001
  ↓
RESOLVE-001
  ↓
HIR-001
  ↓
TYPE-001
  ↓
OWN-001
  ↓
MIR-001
  ↓
VERIFY-001
  ↓
LIR-001
  ↓
X86-001
  ↓
ELF-001
  ↓
LINK-001
  ↓
VS-001
```

Sau khi `fn main(){}` chạy thật, ta sẽ không quay lại thiết kế tổng thể nữa; từ đó mỗi bước là **code contract + invariant + test + vertical integration**.

**Bước kế tiếp trực tiếp là `PARSE-001`: chốt cấu trúc AST arena, grammar item-level, Pratt parser và parser recovery đủ để biên dịch `fn main() {}` — sau đó nối ngay sang Resolver/HIR thay vì dừng ở parser.**