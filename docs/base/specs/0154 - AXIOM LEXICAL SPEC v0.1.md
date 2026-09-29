# AXIOM LEXICAL SPEC v0.1

Ta khóa tiếp **lexer**. Mục tiêu của lexer Axiom không phải chỉ “đọc token”, mà phải tạo một token stream **deterministic, lossless đủ cho diagnostics, không mang semantic interpretation**, và không khiến parser/type system phải sửa lexer về sau.

---

# 1. Lexer boundary

Pipeline:

```text
SourceText
    ↓
UTF-8 validation
    ↓
Lexer
    ↓
TokenStream
    ↓
Parser
    ↓
AST
```

Lexer **không được**:

- resolve identifier
- resolve type
- phân biệt variable/function/type
- infer numeric type
- kiểm tra ownership
- kiểm tra `view`
- kiểm tra trait
- evaluate `comptime`

Ví dụ:

```axiom
Foo<T>(x)
```

Lexer chỉ thấy:

```text
IDENT Foo
<
IDENT T
>
(
IDENT x
)
```

Không được tự quyết định `Foo` là type hay function.

---

# 2. UTF-8 là encoding duy nhất

Axiom source file:

```text
UTF-8
```

Lexer nhận bytes.

Nếu source không phải UTF-8 hợp lệ:

```text
AX_LEX_0001
```

Compiler error.

Không tự động:

- Latin-1 fallback
- Windows-1252 fallback
- locale-dependent decoding

Điều này rất quan trọng cho reproducible builds.

---

# 3. Source là byte-addressed

Lexer làm việc trên:

```text
[u8]
```

và Span:

```text
Span {
    file: FileId
    start: u32
    end: u32
}
```

Các character Unicode có thể dài nhiều byte.

Ví dụ:

```text
α
```

không làm Span chuyển sang “character index”.

Span vẫn:

```text
[start_byte, end_byte)
```

---

# 4. Unicode identifier

Axiom nên hỗ trợ Unicode identifier.

Ví dụ hợp lệ:

```axiom
let tên = "Axiom"
let 用户 = 10
let α = 3.14
```

Nhưng Unicode chỉ áp dụng cho **identifier**, không phải mọi vị trí.

---

# 5. Identifier rule

Đề xuất:

```text
IDENT_START:
    Unicode XID_Start
    hoặc `_`

IDENT_CONTINUE:
    Unicode XID_Continue
```

Do đó:

```text
foo
foo2
_foo
__foo
α
tên
```

có thể hợp lệ.

Nhưng:

```text
2foo
```

không phải identifier.

Nó phải được tokenize thành:

```text
INT("2")
IDENT("foo")
```

---

# 6. Unicode normalization

Đây là vấn đề cần khóa ngay.

**Không tự động normalize identifier thành NFC/NFKC để thay đổi semantic identity.**

Ví dụ hai source spelling Unicode có thể visually giống nhau nhưng byte sequence khác nhau.

Axiom nên chọn:

> Identifier identity dựa trên Unicode scalar sequence sau UTF-8 decoding, không dựa trên glyph rendering.

Có thể compiler tooling cảnh báo confusable characters, nhưng đó là lint/tooling, không phải lexer semantic normalization.

---

# 7. Keyword

Keyword v0.1 chính thức:

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
```

`self` là **special identifier**, không nhất thiết phải coi là keyword thông thường.

---

# 8. Không có `use`

Khóa lại:

```text
use
```

**không phải keyword v0.1.**

Chỉ có:

```axiom
import ...
```

Điều này tránh hai cơ chế import cạnh tranh.

---

# 9. Keyword không được làm identifier

Không hợp lệ:

```axiom
let fn = 10
let struct = 20
let trait = 30
```

Lexer có thể tokenize keyword riêng:

```text
KW_FN
KW_STRUCT
KW_TRAIT
```

Parser sẽ quyết định context hợp lệ hay không.

---

# 10. `true` và `false`

Là keyword/literal token:

```text
TRUE
FALSE
```

Không phải identifier.

```axiom
let x = true
```

→

```text
LET IDENT EQ TRUE
```

---

# 11. Không có `null`

Lexer không có:

```text
NULL
```

`null` nếu xuất hiện chỉ là identifier bình thường:

```axiom
null
```

nhưng vì prelude/core không định nghĩa symbol `null`, resolver sẽ báo undefined symbol.

Tuy nhiên tôi nghiêng về việc **reserved identifier `null`** trong tương lai để tránh library định nghĩa nó làm pseudo-null. Có thể khóa ở v1.0 sau khi quyết định final.

Với v0.1, chưa cần.

---

# 12. Numeric literals

Các dạng:

```text
123
1_000_000

0xff
0b1010
0o755

3.14
1.0
1e10
1.5e-3
```

Cho phép `_` để readability:

```axiom
1_000_000
0xff_ff
3.141_592
```

---

# 13. Integer literal

Token:

```text
INT_LITERAL
```

Lexer giữ **text gốc**.

Ví dụ:

```axiom
1_000_000
```

token chứa:

```text
raw = "1_000_000"
```

Không nên parse thành `u64` ngay trong lexer.

Lý do:

```text
let x: u128 = 340282366920938463463374607431768211455
```

và compiler bootstrap ban đầu có thể chưa có arbitrary-width integer parser hoàn chỉnh.

Lexer chỉ xác định:

> Đây là integer literal hợp lệ.

Literal typing thuộc type checker.

---

# 14. Integer bases

### Decimal

```text
123
1_234
```

### Hex

```text
0xFF
0xff
0x12_ab
```

### Binary

```text
0b1010
0b1010_0011
```

### Octal

```text
0o755
0o7_55
```

Không hỗ trợ:

```text
0123
```

như octal C.

Nó là decimal `123`.

---

# 15. Leading zero

```axiom
000123
```

vẫn là decimal integer.

Không có semantic octal dựa trên leading zero.

---

# 16. Invalid numeric literals

Ví dụ:

```text
0x
0b
0o
```

phải tạo:

```text
AX_LEX_0010
```

thay vì tokenize thành:

```text
INT(0)
IDENT(x)
```

Lý do là user rõ ràng đang viết một numeric literal nhưng sai.

Tương tự:

```text
1__000
```

nên là lexical error nếu underscore placement không hợp lệ.

---

# 17. Float literals

Các dạng:

```text
1.0
0.5
10.0
1e10
1E10
1.5e-3
```

Phải có một quy tắc rõ:

```text
digits "." digits?
```

hoặc exponent.

Đề xuất:

```text
1.
```

**được phép** là float literal.

Nhưng:

```text
1..10
```

phải được tokenize:

```text
INT(1)
RANGE
INT(10)
```

không phải float `1.` + `.10`.

Đây là một điểm lexer phải xử lý bằng maximal munch + lookahead.

---

# 18. Range ambiguity

Axiom có:

```text
0..10
0..=10
```

Do đó:

```text
1..2
```

→

```text
INT_LITERAL("1")
RANGE
INT_LITERAL("2")
```

và:

```text
1..=2
```

→

```text
INT_LITERAL("1")
RANGE_INCLUSIVE
INT_LITERAL("2")
```

Trong khi:

```text
1.5
```

→ FLOAT.

---

# 19. Numeric suffix

Tôi **không khuyến nghị** syntax kiểu:

```text
123u32
123i64
1.0f32
```

ở v0.1.

Không cần thiết vì expected type + `as` đã đủ cho phần lớn trường hợp:

```axiom
let x: u32 = 123
let y: f32 = 1.0
```

Nếu sau này cần suffix, có thể thêm mà không phá semantic model, nhưng chưa đưa vào Core.

---

# 20. Numeric inference

Lexer không biết:

```text
123
```

là:

```text
i32
u64
usize
```

Type checker quyết định dựa trên context.

Ví dụ:

```axiom
let x: u64 = 123
```

literal được instantiate thành `u64`.

Không phải implicit numeric conversion.

---

# 21. Character literal

Tôi đề xuất **không có `char` literal trong Core v0.1**.

Không:

```axiom
'a'
```

Thay vào đó:

```axiom
"a"
```

là `Text`.

Nếu cần Unicode scalar:

```text
Char
```

sẽ là library/core type được thiết kế sau, với syntax có thể bổ sung.

Lý do: `char` thường tạo ra nhiều câu hỏi không đáng có ở giai đoạn đầu:

- Unicode scalar hay code unit?
- escape semantics
- normalization
- UTF-8 conversion
- invalid scalar
- ABI

Không nên làm lexer phức tạp chỉ để có `'a'`.

---

# 22. String literal

```axiom
"hello"
```

→

```text
STRING_LITERAL
```

Semantic type:

```text
Text
```

theo surface spec.

---

# 23. Byte string

```axiom
b"hello"
```

→

```text
BYTE_STRING_LITERAL
```

semantic type:

```text
Bytes
```

Điều này rất quan trọng cho systems programming.

Ví dụ:

```axiom
b"\x48\x65\x6c\x6c\x6f"
```

không phải Unicode Text.

---

# 24. Escape sequences

String hỗ trợ tối thiểu:

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

Ví dụ:

```axiom
"hello\n"
"\u{1F600}"
b"\xFF\x00"
```

`u{...}` dành cho Unicode scalar.

Compiler phải reject scalar invalid.

---

# 25. Byte string escape

`b"..."` không được phép chứa arbitrary Unicode trực tiếp nếu byte representation không rõ ràng.

Đề xuất:

```axiom
b"ABC"
b"\xFF\x00"
```

Byte string là sequence byte.

Nếu muốn UTF-8 bytes từ Text:

```text
text.as_bytes()
```

là semantic/library operation.

---

# 26. String interpolation

Axiom có:

```axiom
"Hello, {name}"
```

Lexer không nên biến toàn bộ interpolation thành một token.

Có hai hướng.

### Không tốt

```text
STRING_INTERPOLATED
```

với lexer tự parse expression.

### Tốt hơn

Lexer có string mode:

```text
STRING_START
STRING_TEXT("Hello, ")
INTERPOLATION_START
IDENT(name)
INTERPOLATION_END
STRING_END
```

Như vậy expression bên trong `{...}` sử dụng **chính lexer/parser của Axiom**.

---

# 27. Nested interpolation

Cho phép expression bình thường:

```axiom
"result = {foo(x + y)}"
```

Lexer chuyển giữa:

```text
STRING
NORMAL
STRING
```

Parser xử lý expression.

---

# 28. Escaped `{`

Nếu muốn literal `{`:

```axiom
"hello \{ world"
```

Tôi đề xuất **không dùng escape riêng** mà dùng:

```axiom
"hello {{ world"
```

hoặc ngược lại.

Nhưng đây là syntax chưa cần khóa ngay.

Tôi nghiêng về quy tắc đơn giản hơn:

```text
\{
\}
```

để nhất quán với string escape.

Vậy:

```axiom
"hello \{name\}"
```

là text literal, không interpolation.

---

# 29. Comments

Line comment:

```axiom
// comment
```

đến hết newline.

Block comment:

```axiom
/*
    comment
*/
```

---

# 30. Nested block comments

**Cho phép.**

Ví dụ:

```axiom
/*
    outer
    /*
        inner
    */
    outer
*/
```

Đây là một lựa chọn rất đáng giá cho tooling/generated code.

Lexer duy trì:

```text
block_comment_depth
```

---

# 31. Unterminated comment

```axiom
/*
hello
```

→

```text
AX_LEX_0020
```

với span từ `/*` đến EOF.

---

# 32. Whitespace

Whitespace gồm:

- space
- tab
- CR
- LF
- Unicode whitespace theo quy tắc xác định

Nhưng để tránh ambiguity, tôi đề xuất lexer chỉ coi ASCII:

```text
' '
'\t'
'\n'
'\r'
```

là lexical whitespace trong v0.1.

Unicode whitespace khác có thể bị reject hoặc treated as invalid character.

Điều này làm source deterministic hơn.

---

# 33. Newline

Newline **không phải token semantic**.

Ví dụ:

```axiom
let x =
    10
```

hợp lệ.

Không có automatic semicolon insertion.

Axiom sử dụng:

> **Whitespace-insensitive, semicolon-optional syntax.**

---

# 34. Semicolon

Semicolon:

```text
;
```

được hỗ trợ như statement separator.

Ví dụ:

```axiom
let x = 1;
let y = 2;
```

và:

```axiom
let x = 1
let y = 2
```

đều hợp lệ.

Parser quyết định statement boundary dựa trên grammar.

---

# 35. Không dùng semicolon insertion kiểu JavaScript

Đây là điểm quan trọng.

Axiom **không** có:

```text
ASI
```

kiểu JavaScript.

Lexer không tự chèn `;`.

Điều này tránh các lỗi cực kỳ khó đoán.

---

# 36. Operators

Operator tokens:

```text
+
-
*
/
%
&
|
^
~
<<
>>
!
&&
||
==
!=
<
<=
>
>=
=
```

Assignment:

```text
=
```

Không có:

```text
++
--
+=
-=
*=
/=
```

ở v0.1.

Điều này giữ grammar đơn giản.

---

# 37. Arithmetic overflow operators

Axiom có:

```text
+
-
*
```

checked semantics.

Wrapping:

```text
+%
-%
*%
```

Saturating:

```text
+|
-|
*|
```

Lexer phải tokenize chúng thành operator riêng.

Ví dụ:

```axiom
a +% b
```

→

```text
IDENT
PLUS_WRAP
IDENT
```

Không phải:

```text
PLUS
PERCENT
```

---

# 38. Bitwise

```text
&
|
^
~
<<
>>
```

Nhưng chú ý:

```text
&&
||
```

là boolean logical operators.

Lexer phải maximal-munch:

```text
&&
```

trước:

```text
&
```

---

# 39. Comparison

```text
==
!=
<
<=
>
>=
```

Maximal munch:

```text
<=
```

không được thành:

```text
<
=
```

---

# 40. Arrow operators

```text
->
=>
```

Ví dụ:

```axiom
fn foo() -> i32
```

và pattern/function-related syntax sau này có thể dùng:

```text
=>
```

Lexer chỉ tokenizes.

---

# 41. Range operators

```text
..
..=
```

Tokens:

```text
RANGE
RANGE_INCLUSIVE
```

Ví dụ:

```axiom
0..10
0..=10
```

---

# 42. Punctuation

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
@
?
```

Ngoài ra:

```text
_
```

là identifier hoặc special token tùy lexer design.

Tôi khuyến nghị:

```text
_
```

là `IDENT("_")`.

Parser/pattern system sẽ hiểu wildcard `_`.

Điều này tránh tạo một lexical special case không cần thiết.

---

# 43. `@`

Attributes:

```axiom
@repr(C)
@align(64)
@export("foo")
@kernel
```

Lexer:

```text
AT
IDENT
```

Không tạo riêng:

```text
ATTRIBUTE_REPR
ATTRIBUTE_ALIGN
```

Attribute semantics thuộc attribute parser/resolver.

---

# 44. `?`

Token:

```text
QUESTION
```

Ví dụ:

```axiom
foo()?.bar?
```

Lexer không biết nó là:

- Result propagation
- Option propagation

Type checker quyết định.

---

# 45. `::` có nên có?

Tôi đề xuất **có**.

Ví dụ cần explicit qualification:

```axiom
Trait::method(x)
```

hoặc:

```axiom
module::name
```

Lexer:

```text
COLON_COLON
```

Điều này rất hữu ích cho:

- trait qualification
- associated item
- namespace qualification
- disambiguation

---

# 46. `.`

Dot có nhiều semantic role:

```axiom
x.field
x.method()
Message.Quit
foo.await
```

Lexer chỉ:

```text
DOT
```

Parser/type system quyết định.

---

# 47. `..` vs `.`

Maximal munch:

```text
...
```

Hiện tại không có spread/ellipsis syntax.

Do đó:

```text
...
```

→ lexical error.

Không nên vô tình tokenize:

```text
.
.
.
```

nếu chưa có semantic.

---

# 48. `#`

Không phải Core syntax.

Do đó:

```text
#
```

→ lexical error.

Attributes dùng:

```text
@
```

không phải `#[...]`.

Điều này làm Axiom syntax khác Rust một cách có chủ đích.

---

# 49. Raw strings

Tôi đề xuất **không đưa raw string vào v0.1**.

Không:

```text
r"..."
```

Ban đầu chỉ cần:

```text
"..."
b"..."
```

Nếu sau này cần regex/path-heavy syntax thì có thể thêm.

---

# 50. Token structure

Token nên có:

```text
Token {
    kind: TokenKind
    span: Span
}
```

Không nhất thiết lưu string value trong token.

Ví dụ:

```text
Token {
    kind: IDENT
    span: [10, 15]
}
```

Parser dùng SourceDatabase để lấy text:

```text
span_text(token.span)
```

---

# 51. TokenKind

Conceptual:

```text
TokenKind
├── EOF
│
├── IDENT
├── INT_LITERAL
├── FLOAT_LITERAL
├── STRING_LITERAL
├── BYTE_STRING_LITERAL
│
├── TRUE
├── FALSE
├── KEYWORDS...
│
├── PLUS
├── MINUS
├── STAR
├── SLASH
├── PERCENT
├── PLUS_WRAP
├── MINUS_WRAP
├── STAR_WRAP
├── PLUS_SAT
├── MINUS_SAT
├── STAR_SAT
├── AMP
├── PIPE
├── CARET
├── TILDE
├── SHL
├── SHR
├── NOT
├── AND_AND
├── OR_OR
├── EQ_EQ
├── NOT_EQ
├── LT
├── LT_EQ
├── GT
├── GT_EQ
├── EQ
├── ARROW
├── FAT_ARROW
├── RANGE
├── RANGE_EQ
│
├── LPAREN
├── RPAREN
├── LBRACKET
├── RBRACKET
├── LBRACE
├── RBRACE
├── COMMA
├── DOT
├── COLON
├── COLON_COLON
├── SEMICOLON
├── AT
├── QUESTION
│
└── ERROR
```

---

# 52. Lexer state machine

Không nên viết lexer như một đống regex độc lập.

Nên là deterministic state machine:

```text
Normal
 ├── identifier
 ├── number
 ├── string
 ├── byte string
 ├── operator
 ├── punctuation
 ├── whitespace
 ├── line comment
 └── block comment

String
 ├── text
 ├── escape
 ├── interpolation
 └── end

Interpolation
 └── Normal
```

---

# 53. Maximal munch

Lexer luôn ưu tiên token dài nhất hợp lệ.

Ví dụ:

```text
===
```

Không có `===`.

Nên:

```text
==
=
```

Ví dụ:

```text
<=
```

→ một token.

```text
..
```

→ một token.

```text
..=
```

→ một token.

---

# 54. Nhưng maximal munch không phải “đọc càng dài càng tốt”

Ví dụ:

```text
1..10
```

không được đọc:

```text
1.
```

rồi còn:

```text
.10
```

Lexer cần contextual lexical rule:

```text
digits "." "." → integer + range
```

Trong khi:

```text
digits "." digit → float
```

Đây là một trong những test bắt buộc.

---

# 55. Error recovery

Lexer không được dừng ngay ở lỗi đầu tiên.

Ví dụ:

```axiom
let x = "abc
let y = 10
let z = @@@
```

nên cố recover để parser/IDE có thêm diagnostics.

Nhưng recovery phải deterministic.

---

# 56. Error token

Lexer có:

```text
ERROR
```

với diagnostic đi kèm.

Ví dụ:

```text
AX_LEX_0001
invalid UTF-8
```

hoặc:

```text
AX_LEX_0031
unterminated string
```

Parser có thể tiếp tục sau recovery boundary.

---

# 57. Lexer errors không được đoán semantic

Ví dụ:

```axiom
let x = 999999999999999999999999999999
```

không phải lexer error chỉ vì vượt `u64`.

Lexer chỉ biết đó là integer literal.

Type checker mới quyết định literal có representable trong inferred type hay không.

---

# 58. Golden test format

Nên có test:

```text
tests/lexer/
├── identifiers.ax
├── numbers.ax
├── strings.ax
├── comments.ax
├── operators.ax
├── ranges.ax
├── attributes.ax
├── unicode.ax
└── errors/
```

Mỗi test có expected token stream.

Ví dụ:

```text
SOURCE:
let x = 1..=10
```

Expected:

```text
KW_LET
IDENT("x")
EQ
INT("1")
RANGE_INCLUSIVE
INT("10")
EOF
```

---

# 59. Lexer conformance invariants

Khóa bộ đầu tiên:

```text
ALEX-20
Lexer is deterministic.

ALEX-21
Lexer operates on validated UTF-8 source.

ALEX-22
Token spans use byte offsets.

ALEX-23
Lexer does not perform semantic name resolution.

ALEX-24
Lexer does not perform type inference.

ALEX-25
Lexer does not perform ownership analysis.

ALEX-26
Identifier identity is distinct from symbol identity.

ALEX-27
Unicode identifiers use defined XID rules.

ALEX-28
Identifier normalization does not silently alter semantic identity.

ALEX-29
Keywords cannot be used as ordinary identifiers.

ALEX-30
Numeric literal interpretation is deferred beyond lexical classification.

ALEX-31
Numeric literal overflow is not a lexical semantic decision.

ALEX-32
Nested block comments are supported.

ALEX-33
Unterminated lexical constructs produce deterministic diagnostics.

ALEX-34
String interpolation reuses normal expression lexing.

ALEX-35
Longest valid operator token is selected.

ALEX-36
Range syntax is lexically distinguished from floating-point syntax.

ALEX-37
Whitespace does not create semantic tokens.

ALEX-38
Newline does not perform automatic semicolon insertion.

ALEX-39
Lexer recovery is deterministic.

ALEX-40
Token identity does not depend on host memory addresses.
```

---

# 60. Lexer API

API tối thiểu:

```text
Lexer {
    source: SourceText
    position: u32
    state: LexerState
}
```

```text
next() -> Token
peek() -> Token
```

Hoặc tốt hơn:

```text
TokenStream {
    tokens
    diagnostics
}
```

Parser có thể consume:

```text
peek()
bump()
expect(kind)
eat(kind)
```

---

# 61. Không tokenize thành AST

Đây là boundary cần giữ rất chặt.

Không làm:

```text
lexer.parse_integer()
lexer.resolve_keyword_context()
lexer.parse_attribute()
```

Lexer chỉ:

```text
bytes → tokens
```

Parser:

```text
tokens → syntax tree
```

Resolver:

```text
syntax tree → semantic identity
```

Type checker:

```text
semantic tree → typed semantics
```

---

# 62. Lexer implementation milestone

Agent có thể triển khai ngay:

```text
compiler/
└── lexer/
    ├── token.ax
    ├── lexer.ax
    ├── cursor.ax
    ├── escape.ax
    ├── unicode.ax
    ├── diagnostics.ax
    └── tests/
```

Nếu compiler hiện tại chưa viết bằng Axiom thì implementation language tùy bootstrap stage.

Quan trọng là **test behavior**, không phụ thuộc implementation language.

---

# 63. Vertical slice đầu tiên sau lexer

Ngay sau lexer, không nên viết toàn bộ parser một lần.

Làm vertical slice:

```text
fn main() {}
```

Pipeline:

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
TypeChecker
 ↓
MIR
 ↓
Verifier
 ↓
Oracle
```

Sau đó:

```text
let x = 42
```

rồi:

```text
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

Rồi mới mở rộng grammar.

---

# 64. Parser architecture tiếp theo

Parser nên là **recursive descent + Pratt parser cho expressions**.

Tôi không khuyến nghị parser generator ở giai đoạn này.

Kiến trúc:

```text
Parser
├── items
├── modules
├── functions
├── structs
├── enums
├── traits
├── impls
├── statements
├── patterns
├── types
└── expressions
       └── Pratt parser
```

Điểm này rất hợp với Axiom vì expression grammar có:

```text
?
.await
method()
index[]
field.
binary operators
casts
ranges
closures
if expressions
match expressions
```

và Pratt parser giúp precedence rõ ràng.

---

# 65. Một quyết định tiếp theo cần khóa trước parser

Có một thứ **không nên để parser tự phát triển tùy ý**:

> **AST không phải bản sao của syntax.**

AST nên là syntax tree đã loại bỏ những thứ parser không cần giữ semantic-wise, nhưng vẫn giữ đủ source spans và syntax information cho diagnostics.

Sau AST sẽ có:

```text
AST
 ↓
Resolver
 ↓
HIR
```

Trong HIR:

```text
IDENT "foo"
```

được chuyển thành:

```text
SymbolId(...)
```

Đây sẽ là bước tiếp theo quan trọng nhất.

**Vì vậy sau Lexer, ta sẽ khóa `AXIOM AST + Parser Architecture v0.1`, bao gồm grammar EBNF thực tế, Pratt precedence table, parsing ambiguity (`<` generic vs comparison), `if/match`, closures, attributes, `impl Trait/dyn Trait`, và AST ID/span model.**