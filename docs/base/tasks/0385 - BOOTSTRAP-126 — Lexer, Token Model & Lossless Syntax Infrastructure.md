# BOOTSTRAP-126 — Lexer, Token Model & Lossless Syntax Infrastructure

**Trạng thái: FROZEN / COMPLETED**

Mục tiêu:

> Lexer phải nhanh, deterministic, UTF-8 native, incremental-friendly và giữ đủ thông tin để formatter/IDE/AI có thể tái dựng source chính xác.

---

# 1. Vị trí trong compiler

```text
SourceDB
   │
   ▼
UTF-8 Source
   │
   ├── validation
   ├── line index
   └── source revision
          │
          ▼
       Lexer
          │
          ▼
     Token Stream
          │
          ▼
        CST
          │
          ▼
        AST
```

Lexer **không** làm:

- name resolution;
- type checking;
- ownership;
- macro/comptime execution;
- overload resolution.

---

# 2. Source là UTF-8 byte sequence

Axiom source file:

```text
UTF-8 bytes
```

là representation chuẩn.

Compiler phải reject malformed UTF-8 ở source boundary.

Ví dụ:

```text
invalid UTF-8
    ↓
ELEX_INVALID_UTF8
```

Không cố silently repair source.

---

# 3. Byte offset là canonical position

Source position dùng:

```text
SourceOffset = byte offset
```

Không dùng Unicode codepoint index làm identity.

Ví dụ:

```text
"Hello Việt"
```

mỗi character có thể có số byte khác nhau.

Byte offset:

- O(1) tương thích với slice;
- tương thích filesystem/editor APIs;
- không phụ thuộc Unicode decoding khi lưu position.

---

# 4. Line/column là derived information

Không lưu column như semantic identity.

```text
SourceOffset
    ↓
LineIndex
    ↓
line / UTF-16 column / UTF-8 column
```

IDE có thể yêu cầu UTF-16 positions nếu LSP cần.

Compiler không dùng UTF-16 làm canonical coordinate.

---

# 5. SourceSpan

```text
SourceSpan {
    file: SourceFileId,
    start: SourceOffset,
    end: SourceOffset,
}
```

Invariant:

```text
start <= end
```

Empty span hợp lệ cho insertion diagnostic.

---

# 6. Token model

Token nên có representation compact:

```text
Token {
    kind: TokenKind,
    start: u32,
    end: u32,
}
```

hoặc tương đương packed representation.

Không copy nội dung token vào mỗi token.

---

# 7. TokenKind

Phân nhóm:

```text
TokenKind
├── Identifier
├── Keyword
├── IntegerLiteral
├── FloatLiteral
├── CharLiteral
├── StringLiteral
├── ByteLiteral
├── RawStringLiteral
├── Operator
├── Punctuation
├── Error
└── EOF
```

---

# 8. Trivia không phải token semantic

Trivia:

```text
whitespace
line comment
block comment
```

được lưu riêng hoặc trong lossless token stream.

Parser semantic không phải xử lý trivia.

---

# 9. Lossless token stream

CST cần có khả năng giữ:

```text
token
whitespace
comment
source span
```

để:

- formatter;
- refactoring;
- IDE;
- code actions;
- source-preserving transforms.

AST thì không cần giữ toàn bộ trivia.

---

# 10. Token interning

Identifier text không nên được copy lặp lại.

Ví dụ:

```ax id="gjb21s"
user.name;
user.name;
user.name;
```

Lexer có thể tạo:

```text
IdentifierId("user")
IdentifierId("name")
```

thông qua intern table.

Tuy nhiên source span vẫn giữ nguyên.

---

# 11. Keyword recognition

Lexer nhận:

```text
fn
struct
trait
impl
let
var
...
```

thành keyword token.

Identifier:

```text
foo
User
user_name
```

thành Identifier.

Không để parser phải string-compare keyword ở mọi nơi.

---

# 12. Keyword lookup

Không dùng hashmap cho từng token.

Dùng:

```text
perfect hash
switch
trie
length-dispatch
```

tùy implementation.

Với keyword set nhỏ, compiler có thể dùng length + byte comparison rất nhanh.

---

# 13. Unicode identifiers

Identifier bắt đầu bằng Unicode XID_Start:

```text
XID_Start
```

tiếp theo:

```text
XID_Continue*
```

`_` được hỗ trợ theo identifier rules riêng.

Ví dụ:

```ax id="fbxj5k"
struct NgườiDùng {
    tên: String,
}
```

hợp lệ.

---

# 14. Unicode normalization

Lexer/compiler dùng:

```text
NFC
```

làm canonical normalization policy cho identifiers.

Nhưng source text gốc vẫn được giữ nguyên để diagnostics/formatting.

Tức là:

```text
source spelling
≠
semantic identifier key
```

khi normalization cần thiết.

---

# 15. Unicode confusable warning

Compiler không tự động reject mọi Unicode confusable.

Ví dụ:

```text
Latin a
Cyrillic а
```

có thể trông giống nhau nhưng khác identifier.

Compiler nên có diagnostic tooling:

```text
WIDENT_CONFUSABLE
```

nhưng không thay đổi semantics.

---

# 16. Reserved keywords

Keyword không thể dùng trực tiếp làm identifier:

```ax id="p2f0y1"
let fn = 10;
```

→ error.

Escaped identifier syntax có thể được dành chỗ cho tương lai, nhưng **không cần đưa vào Core v0.1**.

---

# 17. Integer literal

Forms:

```ax id="m3u6i1"
123
1_000
0xff
0b1010
0o755
```

Suffix:

```ax id="c6ot5f"
123u8
123i64
123usize
```

---

# 18. Underscore trong number

Cho phép:

```ax id="hpk0lb"
1_000_000
0xff_ff
0b1111_0000
```

Nhưng không:

```text id="f1v7v8"
_123
123_
0x_ff
```

nếu grammar không định nghĩa hợp lệ.

Lexer phải reject malformed separator placement.

---

# 19. Integer overflow trong literal

Ví dụ:

```ax id="8f3ujy"
let x: u8 = 999;
```

Lexer vẫn nhận literal hợp lệ.

Type checker/constant evaluator báo:

```text
EINT_LITERAL_OVERFLOW
```

Không biến lexer thành type checker.

---

# 20. Float literal

Ví dụ:

```ax id="gnn9uv"
1.0
0.5
1e10
1.0e-5
1.0f32
```

Parser/literal validator phải phân biệt:

```text
1.
```

với:

```text
1..10
```

Grammar phải deterministic.

---

# 21. Range ambiguity

Ví dụ:

```ax id="1m2f8y"
1..10
```

tokenization:

```text
Integer(1)
DotDot
Integer(10)
```

không:

```text
Float(1.)
Dot
Integer(10)
```

Lexer ưu tiên multi-character punctuation/range token khi context phù hợp theo lexical grammar.

---

# 22. Character literal

```ax id="z7t9t4"
'a'
'\n'
'\u{1F600}'
```

Phải chứa đúng một Unicode scalar value sau escape processing.

Sai:

```text
''
'ab'
'\u{110000}'
```

→ lexical error.

---

# 23. Byte literal

```ax id="30ecsv"
b'a'
b'\n'
```

chỉ chứa một byte.

Unicode character ngoài byte range:

```ax id="ckqj8d"
b'ế'
```

→ error.

---

# 24. String literal

```ax id="pf4o9n"
"hello"
```

Lexer kiểm tra:

- closing quote;
- escape validity;
- malformed UTF-8 trong source;
- literal syntax.

Semantic String type do later phase xác định.

---

# 25. Escape sequences

Core:

```text id="r6s2bl"
\n
\r
\t
\\
\"
\'
\0
\u{HEX}
```

Không nên có hàng chục escape legacy kiểu C nếu không cần.

---

# 26. Unicode escape

Canonical:

```ax id="rjjj1p"
"\u{1F600}"
```

Không:

```text id="y4x3xw"
\uD800
```

vì surrogate không phải Unicode scalar value.

---

# 27. Raw strings

Ví dụ:

```ax id="i5b9f7"
r"C:\Users\Test"
```

Raw string không interpret escapes.

Multiline raw string có thể hỗ trợ delimiter count nếu cần cho source containing quotes.

---

# 28. String interpolation

Lexer phải recognize interpolation boundaries nếu Axiom dùng:

```ax id="f2e2m9"
"Hello {name}"
```

Nhưng không nên biến lexer thành expression parser.

Kiến trúc:

```text
StringStart
Text
InterpolationStart
...
InterpolationEnd
StringEnd
```

Parser xử lý expression bên trong.

---

# 29. Nested interpolation

Ví dụ:

```ax id="31ckha"
"Result: {foo(bar(x))}"
```

Lexer/parser phải xử lý brace nesting chính xác.

---

# 30. Comments

Line:

```text id="wzsy2u"
// comment
```

kết thúc bởi newline hoặc EOF.

Block:

```text id="6i5xkc"
/* comment */
```

có thể multiline.

---

# 31. Nested block comments

Axiom cho phép:

```ax id="yyodq8"
/*
    outer
    /*
        inner
    */
*/
```

Lexer duy trì depth:

```text id="h0k79a"
depth += 1
depth -= 1
```

EOF khi depth > 0:

```text id="h7xq8s"
ELEX_UNTERMINATED_BLOCK_COMMENT
```

---

# 32. Doc comments

Doc comment:

```ax id="1oyb1d"
/// User representation.
struct User {
}
```

hoặc:

```ax id="q2x2zz"
/**
 * User representation.
 */
```

được giữ như structured documentation trivia.

Compiler có thể attach doc comment vào declaration.

---

# 33. Comments không thay đổi semantics

Trừ doc comments/tooling metadata:

```text id="0g1q1a"
comment
```

không ảnh hưởng:

- type;
- ownership;
- ABI;
- optimization;
- binary.

---

# 34. Operators

Lexer phải nhận maximal operator token.

Ví dụ:

```text id="0p8kga"
==
!=
<=
>=
&&
||
<<
>>
+=
-=
*=
/=
%=
..
..=
```

Parser quyết định precedence.

---

# 35. `->`

Function return:

```ax id="6p6g9g"
fn add(a: i32) -> i32
```

Lexer nhận `->` là một token.

---

# 36. `::`

Path separator:

```ax id="yukd9v"
std::io::File
```

một punctuation token.

---

# 37. `=>`

Match arm:

```ax id="1a7q9n"
x => value
```

một token.

---

# 38. `@`

Attribute:

```ax id="r6j9o0"
@repr(C)
```

một token riêng.

---

# 39. Lifetime syntax không tồn tại

Lexer không cần semantic token riêng cho:

```text id="1d49cr"
'a
```

vì Axiom Core không có programmer-written lifetime syntax.

Apostrophe chỉ cần phục vụ:

- char literal;
- future reserved syntax nếu cần.

---

# 40. Label

Nếu dùng:

```ax id="t0s9r8"
'outer: loop {
}
```

lexer có thể tạo:

```text id="b6e5a2"
Char-like apostrophe
Identifier
Colon
```

Parser phân biệt label context.

Không cần lifetime token.

---

# 41. Punctuation set

Core:

```text id="e8u8ws"
(
)
{
}
[
]
<
>
,
.
:
;
::
@
#
?
!
=
+
-
*
/
%
&
|
^
~
```

Parser quyết định semantic meaning.

---

# 42. Token categories không quá granular

Không tạo hàng trăm token types nếu parser có thể xử lý từ:

```text id="x9u5ms"
Operator
```

Nhưng các token ảnh hưởng grammar trực tiếp nên riêng:

```text id="q10m6w"
Identifier
Integer
Float
String
Char
Keyword
EOF
```

và multi-character punctuation.

---

# 43. Lexer state machine

Lexer nên là deterministic state machine:

```text id="4m2q3m"
Normal
 ├── Identifier
 ├── Number
 ├── String
 ├── Char
 ├── Comment
 └── Operator
```

Không backtracking lớn.

---

# 44. Zero-copy principle

Token:

```text id="i3z9js"
start/end
```

không copy literal source.

Parser có thể lấy:

```text id="m0k0yo"
source[start..end]
```

khi cần.

Identifier interning là exception có chủ đích.

---

# 45. Literal representation

Sau lexer:

```text id="kqv53p"
IntegerLiteral {
    span
    radix
    digits
    suffix
}
```

Không nhất thiết convert ngay thành arbitrary-precision integer.

Constant evaluator/type checker xử lý numeric value.

---

# 46. Numeric literal normalization

Ví dụ:

```ax id="p6bmy8"
1_000
```

semantic digits:

```text id="0t9y5v"
1000
```

nhưng source spelling vẫn:

```text id="5y8j1a"
1_000
```

để formatter/diagnostics.

---

# 47. Token stream API

Concept:

```text id="g1s2n4"
TokenStream {
    tokens
    trivia
    source_revision
}
```

Operations:

```text id="r6z7e3"
peek()
peek_n()
consume()
expect()
checkpoint()
restore()
```

Parser có thể checkpoint cho limited grammar ambiguity.

Không cho arbitrary parser backtracking toàn source.

---

# 48. CST

Concrete Syntax Tree giữ:

```text id="pfh6wx"
Token
Trivia
Grouping
SourceSpan
ErrorNodes
```

CST cần lossless.

Ví dụ formatter có thể reconstruct:

```text id="7r9f4s"
source
```

từ CST/token source relationship.

---

# 49. AST

AST bỏ:

```text id="j6gk2d"
whitespace
ordinary comments
redundant parentheses
```

nhưng giữ:

```text id="v8f9z3"
source span
doc comments
semantic attributes
```

khi cần.

---

# 50. Green tree / red tree

Đề xuất sử dụng kiến trúc **green tree** tương tự các compiler IDE hiện đại:

```text id="g4f7pl"
GreenNode
    immutable
    parentless
    reusable

RedNode
    parent/context
    source navigation
```

Lợi ích:

- structural sharing;
- incremental parsing;
- cheap snapshots;
- IDE.

Nhưng Axiom chỉ lấy architecture concept, không phụ thuộc thư viện.

---

# 51. Incremental lexing

Khi sửa:

```text id="a8w3s0"
let value = 100;
```

thành:

```text id="x5j1la"
let value = 1000;
```

không lex lại toàn bộ project.

Chỉ relex vùng bị ảnh hưởng.

---

# 52. Lexical resynchronization

Incremental lexer:

```text id="s3a4n1"
old tokens
    ↓
find edit region
    ↓
relex
    ↓
find synchronization point
    ↓
reuse unchanged suffix
```

Synchronization point có thể là token boundary an toàn.

---

# 53. Comment/string caveat

Nếu edit xảy ra trong:

```ax id="xw0e5k"
/*
   ...
*/
```

hoặc:

```ax id="zj0bqf"
"...."
```

lexer có thể phải relex tới delimiter kết thúc.

Do đó incremental lexer không được giới hạn cứng theo line.

---

# 54. Unterminated construct

Ví dụ user đang gõ:

```ax id="e6qg6f"
let x = "hello
```

IDE mode:

```text id="0a1e7p"
StringLiteral(Error)
```

và tiếp tục tokenize phía sau theo recovery strategy.

Batch compiler:

```text id="m1q7b3"
ELEX_UNTERMINATED_STRING
```

---

# 55. Error token

Lexer không crash.

Ví dụ:

```text id="6pl6xq"
Unknown character
Malformed escape
Invalid number
Unterminated string
Unterminated comment
```

→ `ErrorToken`.

Compiler tiếp tục parse nếu có thể.

---

# 56. Invalid UTF-8 khác lexical error

Malformed UTF-8:

```text id="9a2u2f"
Source boundary failure
```

khác:

```text id="9jv4nz"
invalid identifier
invalid escape
```

Điều này giúp tooling biết lỗi nằm ở source encoding hay language syntax.

---

# 57. Incremental lexer correctness

Incremental result phải semantic-equivalent với full lex:

```text id="tq9xj1"
Lex(full source after edit)
==
Lex(incrementally updated source)
```

không chỉ “gần giống”.

---

# 58. Lexer benchmark

Compiler phải có benchmark cho:

```text id="b7m0w5"
small files
large files
generated code
Unicode-heavy source
comment-heavy source
string-heavy source
long identifiers
large numeric literals
```

---

# 59. Memory efficiency

Mục tiêu token footprint thấp.

Ví dụ một token semantic cơ bản:

```text id="4y0g1k"
kind + start + length
```

có thể nằm trong 8–16 bytes tùy target.

Không nên:

```text id="0e9br2"
heap allocate every token
```

---

# 60. Parallel lexing

Một file đơn thường lexer tuần tự vì state dependency.

Nhưng nhiều files:

```text id="r7w9mg"
file A ─┐
file B ─┼→ parallel lexer
file C ─┘
```

CompilerDB có thể lex package files song song.

---

# 61. Source line index

SourceDB duy trì newline index:

```text id="9e6j6k"
[0, 12, 30, 47, ...]
```

cho phép:

```text id="h2h8r3"
offset → line
```

nhanh bằng binary search hoặc chunked index.

---

# 62. CRLF normalization

Source semantics phải coi:

```text id="q8c3w1"
LF
CRLF
```

đều là line endings hợp lệ.

Nhưng source-preserving layer phải biết spelling gốc nếu formatter/patch cần.

---

# 63. Unicode newline

Không nên mở rộng quá nhiều newline semantics.

Core canonical line terminators:

```text id="e5a1vu"
LF
CRLF
```

Các Unicode separators có thể được xử lý như whitespace nếu spec yêu cầu, nhưng không tự động biến thành statement boundary.

---

# 64. Token source identity

Mỗi token thuộc:

```text id="5f8y01"
SourceFileId
SourceRevision
```

Không reuse token từ revision cũ mà không xác minh revision compatibility.

---

# 65. CST persistence

CST có thể được cache:

```text id="k2y1v8"
SourceHash
LexerVersion
SyntaxVersion
```

Nếu tất cả match:

```text id="s5g6fj"
reuse CST
```

---

# 66. Syntax version

Cache syntax phải có:

```text id="n4r8zs"
SyntaxSemanticVersion
```

Thay đổi grammar/lexer:

```text id="k7q1fz"
invalidate syntax cache
```

nhưng có thể vẫn giữ source/build cache khác nếu tương thích.

---

# 67. Lexer diagnostics

Stable codes:

```text id="4e2j5c"
ELEX_INVALID_UTF8
ELEX_INVALID_CHAR
ELEX_INVALID_ESCAPE
ELEX_INVALID_NUMBER
ELEX_UNTERMINATED_STRING
ELEX_UNTERMINATED_CHAR
ELEX_UNTERMINATED_COMMENT
ELEX_INVALID_IDENTIFIER
```

---

# 68. AI-readable lexer events

Compiler có thể expose:

```json id="4b20c9"
{
  "kind": "ELEX_INVALID_ESCAPE",
  "span": {
    "file": 12,
    "start": 105,
    "end": 108
  },
  "expected": "unicode escape"
}
```

AI không cần parse human prose.

---

# 69. Lexer invariants

### `ALEX-20`
Source encoding is UTF-8.

### `ALEX-21`
Malformed UTF-8 is rejected deterministically.

### `ALEX-22`
Canonical source positions use byte offsets.

### `ALEX-23`
Line/column information is derived from source offsets.

### `ALEX-24`
Tokens never own duplicated source text unnecessarily.

### `ALEX-25`
Tokenization is deterministic.

### `ALEX-26`
Longest-match rules are deterministic.

### `ALEX-27`
Keyword recognition is deterministic.

### `ALEX-28`
Unicode identifiers follow Unicode XID rules.

### `ALEX-29`
Identifier normalization follows the defined normalization policy.

### `ALEX-30`
Original source spelling remains available for diagnostics/tooling.

### `ALEX-31`
Trivia is preserved in the lossless syntax layer.

### `ALEX-32`
Trivia does not affect ordinary semantic parsing.

### `ALEX-33`
Nested block comments are supported.

### `ALEX-34`
Unterminated lexical constructs produce structured diagnostics.

### `ALEX-35`
Lexer errors cannot cause uncontrolled compiler crashes.

### `ALEX-36`
Numeric literal validation is separated from numeric type inference.

### `ALEX-37`
Literal source spelling remains recoverable.

### `ALEX-38`
Raw strings do not interpret escape sequences.

### `ALEX-39`
Character literals contain exactly one valid Unicode scalar value.

### `ALEX-40`
Byte literals contain exactly one valid byte.

### `ALEX-41`
String interpolation does not require the lexer to parse embedded expressions.

### `ALEX-42`
Incremental lexing is equivalent to complete lexing.

### `ALEX-43`
Incremental lexing may extend beyond the edited region to a safe resynchronization point.

### `ALEX-44`
Lexer state cannot leak between unrelated source files.

### `ALEX-45`
CST is lossless with respect to supported source syntax.

### `ALEX-46`
AST may discard non-semantic trivia.

### `ALEX-47`
Source spans remain valid for the corresponding source revision.

### `ALEX-48`
Syntax cache identity includes lexer/syntax version.

### `ALEX-49`
Parallel lexing of independent files is semantically deterministic.

### `ALEX-50`
Lexer diagnostics use stable machine-readable codes.

### `ALEX-51`
UTF-8 byte offset is the canonical compiler coordinate system.

### `ALEX-52`
IDE coordinate conversions are derived rather than semantic.

### `ALEX-53`
Lexer does not perform type checking.

### `ALEX-54`
Lexer does not perform name resolution.

### `ALEX-55`
Lexer does not execute comptime code.

### `ALEX-56`
Lexer does not infer ownership semantics.

### `ALEX-57`
Lossless syntax infrastructure must support deterministic formatting.

### `ALEX-58`
Incremental syntax updates must preserve unchanged subtree identity where possible.

### `ALEX-59`
Compiler snapshots may reuse immutable syntax structures across revisions.

### `ALEX-60`
Lexer memory usage must remain approximately linear in source size.

---

# 70. Frontend hiện tại

Sau BOOTSTRAP-126:

```text
                    SourceDB
                       │
                 UTF-8 validation
                       │
                    Lexer
                       │
                 Token + Trivia
                       │
                ┌──────▼──────┐
                │ Lossless CST│
                └──────┬──────┘
                       │
                 Incremental
                    Parser
                       │
                       ▼
                      AST
                       │
                    Resolver
                       │
                    TypeDB
                       │
                  Trait Solver
                       │
                    Comptime
                       │
                      HIR
                       │
                      MIR
```

Một điểm đáng chú ý: **Axiom giờ đã có đủ architecture để compiler IDE và compiler batch dùng chung một syntax database**, thay vì phải xây lại parser riêng cho IDE.

---

# BOOTSTRAP-127 — Parser, CST/AST & Incremental Syntax Engine

Task tiếp theo sẽ khóa tầng parser:

```text
Token Stream
     ↓
CST / Green Tree
     ↓
AST
     ↓
Syntax lowering
```

Tập trung vào:

- grammar implementation;
- recursive-descent vs Pratt parser;
- parsing expression precedence;
- generic/type ambiguity;
- `<` là comparison hay generic argument;
- `foo::<T>()`;
- struct literal vs block;
- closure parsing;
- pattern parser;
- attribute parser;
- error recovery;
- parser checkpoints;
- incremental parsing;
- green-tree structural sharing;
- CST → AST lowering;
- source-preserving transformations;
- formatter;
- và cách đảm bảo **parser không bao giờ phải “đoán” semantic intent của programmer**.