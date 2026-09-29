Tiếp tục với **BOOTSTRAP-275 — AXIOM LEXER IMPLEMENTATION SPECIFICATION**.

# BOOTSTRAP-275 — AXIOM LEXER IMPLEMENTATION SPECIFICATION
**STATUS: FROZEN / COMPLETED**

## 1. Mục tiêu

Lexer của Axiom phải là frontend infrastructure có các đặc tính:

- UTF-8 native.
- Offset nội bộ bằng **byte offset**.
- Lossless: không làm mất whitespace/comment/trivia.
- Incremental-friendly.
- Không copy substring không cần thiết.
- Token có source span chính xác.
- Unicode identifier deterministic, locale-independent.
- Newline được giữ thành token.
- Nested block comment.
- Longest-match.
- Recovery có forward progress.
- Không đưa semantic/type knowledge vào lexer.
- Có thể fuzz hàng tỷ input mà không crash/hang.
- Có thể tái sử dụng token/subtree khi source chỉ thay đổi một vùng nhỏ.
- API đủ cụ thể để implementation agent có thể viết lexer ngay.

Kiến trúc:

```text
UTF-8 Source
    │
    ▼
Byte Scanner
    │
    ├── Trivia
    ├── Identifier / Keyword
    ├── Number
    ├── String / Char / Byte
    ├── Operator / Punctuation
    ├── Newline
    └── Recovery
    │
    ▼
Token Stream
    │
    ├── Lossless Syntax
    └── Parser
```

---

# 2. Source model

Lexer nhận:

```text
SourceFile
```

với semantic model:

```text
SourceFile {
    file_id: SourceFileId
    revision: Revision
    text: Utf8Source
    line_index: LineIndex
}
```

`Utf8Source` phải giữ byte buffer gốc.

Không chuyển toàn bộ source sang UTF-32/UTF-16 chỉ để lex.

### 2.1 Byte offset

Mọi `SourceSpan` sử dụng:

```text
start_byte: u32/u64
end_byte:   u32/u64
```

theo half-open interval:

```text
[start, end)
```

Ví dụ:

```text
abc
```

có:

```text
a = [0,1)
b = [1,2)
c = [2,3)
```

### 2.2 Vì sao byte offset là canonical

Byte offset:

- O(1) để slice source.
- tương thích file/OS/network/FFI.
- không phụ thuộc Unicode code point.
- không phụ thuộc grapheme.
- thuận lợi cho incremental parsing.
- thuận lợi cho memory mapping.
- không yêu cầu mỗi token phải chứa string riêng.

Line/column chỉ là **derived information**.

---

# 3. SourceSpan

Canonical:

```text
struct SourceSpan {
    file: SourceFileId
    start: u32
    end: u32
}
```

Invariant:

```text
0 <= start <= end <= source.byte_len
```

Zero-width span hợp lệ:

```text
[start, start)
```

được sử dụng cho:

- missing token recovery
- insertion diagnostic
- EOF
- synthetic syntax nodes.

Không dùng `line,column` làm identity.

---

# 4. LineIndex

Lexer/frontend duy trì:

```text
LineIndex {
    line_starts: Array<u32>
}
```

Ví dụ:

```text
hello\n
world\n
test
```

thì:

```text
line_starts = [0, 6, 12]
```

Line/column được tính từ byte offset.

Column nên được định nghĩa rõ là:

```text
UTF-8 byte column
```

hoặc một display-column API riêng.

Khuyến nghị:

```text
SourcePosition {
    line: u32
    byte_column: u32
}
```

và tooling có thêm:

```text
display_column(...)
```

để xử lý tab/wide Unicode.

**Không được để Unicode display width trở thành semantic source position.**

---

# 5. UTF-8 validation

Axiom source bắt buộc UTF-8 hợp lệ.

Lexer nhận byte input và kiểm tra UTF-8 khi cần.

Input invalid:

```text
0xFF
0xC0 0x80
...
```

không được silently replace bằng `�`.

Kết quả:

```text
LEX-E001 InvalidUtf8
```

Lexer phải:

1. phát hiện lỗi;
2. tạo diagnostic;
3. consume ít nhất một byte;
4. tiếp tục lex.

Không được infinite loop.

---

# 6. Token model

Canonical semantic token:

```text
struct Token {
    kind: TokenKind
    span: SourceSpan
    flags: TokenFlags
}
```

Không lưu:

```text
String text
```

trong mỗi token.

Source text được lấy:

```text
source.slice(token.span)
```

### 6.1 TokenFlags

Có thể gồm:

```text
TokenFlags {
    synthetic
    malformed
    escaped
    preceded_by_whitespace
    preceded_by_newline
}
```

Không nên nhồi semantic information vào flags.

---

# 7. TokenKind

TokenKind được chia nhóm:

```text
TokenKind
├── EOF
├── Error
├── Newline
│
├── Identifier
├── RawIdentifier
├── Keyword(...)
│
├── IntegerLiteral
├── FloatLiteral
├── StringLiteral
├── RawStringLiteral
├── CharLiteral
├── ByteLiteral
├── ByteStringLiteral
│
├── LineComment
├── BlockComment
├── Whitespace
│
├── Punctuation
├── Operator
└── Unknown
```

Có hai cách thiết kế trivia:

### Semantic token stream

Parser chỉ nhận:

```text
Identifier
Keyword
Literal
Operator
Newline
...
```

### Lossless token stream

Giữ:

```text
Whitespace
Comment
Newline
```

Hai view có thể cùng tồn tại.

Khuyến nghị:

```text
RawTokenStream
    ↓
Trivia-filtered TokenStream
```

Không tạo hai lexer khác nhau.

---

# 8. Trivia

Trivia gồm:

- spaces
- tabs
- line comments
- block comments

Whitespace không có semantic meaning trong Core v1 ngoại trừ newline được phát hành thành token riêng.

Ví dụ:

```text
let   x = 10
```

lossless stream:

```text
Keyword(let)
Whitespace
Identifier(x)
Whitespace
=
Whitespace
IntegerLiteral
Newline
```

Parser view:

```text
Keyword(let)
Identifier(x)
=
IntegerLiteral
Newline
```

Formatter/refactoring dùng raw stream.

---

# 9. Newline

Newline là token thực sự:

```text
TokenKind::Newline
```

Nhưng:

> **Lexer không quyết định newline có kết thúc statement hay không.**

Parser quyết định dựa trên grammar.

Hỗ trợ:

```text
\n
\r\n
```

Canonical semantic newline là một token.

`CRLF` được coi là **một newline**, không phải hai token.

Standalone:

```text
\r
```

có thể được hỗ trợ như newline compatibility, nhưng canonical source formatter chuyển về `\n`.

---

# 10. Identifier

Identifier bắt đầu bằng:

```text
Unicode XID_Start
```

hoặc `_`.

Các ký tự tiếp theo:

```text
Unicode XID_Continue
```

hoặc `_`.

Ví dụ hợp lệ:

```text
name
_name
user2
café
ngườiDùng
Δvalue
```

Unicode version phải được **compiler-versioned**.

Không phụ thuộc locale.

---

# 11. Unicode normalization

Axiom **không tự động normalize identifier** trong lexer.

Ví dụ:

```text
é
```

và:

```text
e + combining acute
```

có thể có cùng hình dạng nhưng byte sequence khác nhau.

Lexer giữ nguyên.

Compiler có thể phát diagnostic/tooling warning về confusable identifier, nhưng không thay đổi semantic identity âm thầm.

Điều này tránh:

```text
source spelling
    ≠
compiler spelling
```

một cách khó dự đoán.

---

# 12. Keyword table

Keyword phải được lookup deterministic.

Ví dụ Core v1:

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
fn
for
if
impl
in
let
loop
match
module
mut
pub
return
static
struct
trait
type
unsafe
use
while
where
```

Các keyword mới không được làm thay đổi cách lex identifier đã tồn tại mà không qua language-version rule.

Khuyến nghị lexer implementation:

```text
Identifier scanner
      ↓
keyword lookup
      ↓
Keyword(kind) / Identifier
```

Không có branch riêng cho từng keyword trong scanner.

---

# 13. Raw identifier

Để cho phép identifier trùng keyword trong các trường hợp cần thiết, có thể hỗ trợ:

```text
r#type
r#match
r#async
```

Nếu feature này được giữ trong v1:

```text
r#identifier
```

được lex thành:

```text
RawIdentifier
```

với semantic identifier name:

```text
identifier
```

`r#` là syntax escape, không thuộc semantic name.

---

# 14. Numeric literal scanner

Lexer chỉ xác định **syntactic shape**.

Type checking và range checking diễn ra sau.

Hỗ trợ:

```text
123
1_000_000
0xff
0b1010
0o755
0xFF_FF

1.0
1.5e10
1.5e-10
```

Suffix nếu Axiom giữ syntax này:

```text
42u32
42i64
3.14f32
```

được lex thành một literal token hoặc literal + suffix tùy quyết định AST.

Khuyến nghị:

```text
NumericLiteral {
    base
    digits_span
    fraction_span?
    exponent_span?
    suffix_span?
}
```

Semantic decoding ở AST/HIR.

---

# 15. Numeric underscore

Underscore được phép giữa digit hợp lệ:

```text
1_000
0xff_ff
1_000.25
```

Không hợp lệ:

```text
_100
100_
1__00
0x_FF
```

Lexer có thể phát hiện syntax malformed ngay tại lexical stage.

Diagnostic:

```text
LEX-E010 InvalidNumericLiteral
```

Không chia malformed literal thành hàng loạt token gây diagnostic cascade.

---

# 16. Leading-dot float

Khuyến nghị **không hỗ trợ**:

```text
.5
```

để tránh ambiguity với:

```text
object.field
```

Canonical:

```text
0.5
```

Lexer rule:

```text
.123
```

→ `.` + integer

thay vì float.

---

# 17. String literal

Canonical:

```text
"hello"
```

Lexer phải giữ source spelling.

Semantic decoding:

```text
"hello\n"
```

được thực hiện sau lexer.

Token:

```text
StringLiteral
```

Không biến string thành decoded heap string trong lexer.

---

# 18. Escape sequences

Lexer nhận diện escape syntax:

```text
\n
\r
\t
\\
\"
\'
\0
\xNN
\u{NNNN}
```

Nhưng việc chuyển thành semantic Unicode scalar nên nằm trong literal validation stage.

Ví dụ:

```text
"\u{1F600}"
```

Lexer chỉ xác định đây là string literal hợp lệ về mặt lexical structure.

Literal decoder kiểm tra:

- Unicode scalar validity.
- code point range.
- escape legality.
- byte representation.

---

# 19. Raw string

Để tránh escape explosion, hỗ trợ raw strings là hợp lý:

```text
r"hello\n"
```

và nếu cần delimiter:

```text
r#"hello "world""#
```

hoặc một convention tương đương.

Điểm quan trọng:

> Raw-string delimiter phải có rule deterministic và longest-match.

Agent implementation phải khóa syntax chính xác trước khi codegen lexer.

---

# 20. Character literal

Ví dụ:

```text
'a'
'\n'
'\u{1F600}'
```

`char` là Unicode scalar value, không phải byte.

Do đó:

```text
'a'
```

không tương đương:

```text
b'a'
```

---

# 21. Byte literal

```text
b'a'
```

chỉ chứa một byte.

Ví dụ Unicode character vượt quá `0xFF` phải bị reject.

Byte string:

```text
b"hello"
```

cho phép arbitrary byte escapes theo grammar.

---

# 22. Comment

Line comment:

```text
// comment
```

Block comment:

```text
/*
   comment
*/
```

### Nested block comments

Axiom hỗ trợ:

```text
/*
    outer
    /*
        inner
    */
*/
```

Lexer giữ depth:

```text
block_comment_depth
```

Algorithm:

```text
depth = 1

while depth > 0:
    if "/*":
        depth += 1
    else if "*/":
        depth -= 1
    else:
        consume UTF-8 unit
```

EOF khi:

```text
depth > 0
```

→ diagnostic:

```text
LEX-E020 UnterminatedBlockComment
```

Token vẫn phải có span tới EOF.

---

# 23. Longest-match rule

Axiom lexer sử dụng:

> **Maximal munch / longest valid token.**

Ví dụ:

```text
>>=
```

phải ưu tiên token dài hơn nếu operator này tồn tại.

Tương tự:

```text
==
!=
<=
>=
&&
||
-> 
=> 
..
..=
```

Không được tokenize theo kiểu:

```text
>
>
=
```

nếu `>>=` là operator hợp lệ.

Operator table phải là trie hoặc equivalent deterministic matcher.

---

# 24. Operator registry

Lexer không nên hard-code hàng trăm `if`.

Dùng:

```text
OperatorTable
```

có thể compile thành trie:

```text
root
 ├── =
 │    └── =
 ├── <
 │    ├── =
 │    └── <
 ├── >
 │    ├── =
 │    └── >
 └── .
      ├── .
      │    └── =
```

Lookup:

```text
scan_operator(pos) -> longest_match
```

Operator semantic meaning thuộc parser/type system, không lexer.

---

# 25. Delimiters

Canonical punctuation:

```text
(
)
[
]
{
}
,
:
;
.
@
#
```

Dù semicolon không canonical trong Axiom, lexer vẫn có thể lex:

```text
;
```

để compatibility/recovery.

Parser quyết định nó có hợp lệ trong profile hiện tại không.

---

# 26. `@` attributes

Lexer:

```text
@
identifier
```

Parser:

```text
@repr(C)
@derive(...)
@kernel
```

Lexer không hiểu:

```text
repr
derive
kernel
```

là attribute semantics.

---

# 27. `#` và raw syntax

`#` được giữ trong lexer nếu syntax raw string/raw identifier/attribute cần.

Lexer không tự quyết định context.

---

# 28. Lexer state machine

Không dùng regex engine cho toàn bộ lexer.

Khuyến nghị explicit state machine:

```text
LexerState
├── Normal
├── Identifier
├── Number
├── String
├── Char
├── Byte
├── RawString
├── LineComment
├── BlockComment(depth)
└── ErrorRecovery
```

Nhưng implementation có thể tối ưu thành scanner loop với specialized functions.

Public semantics không phụ thuộc implementation strategy.

---

# 29. Zero-copy design

Token:

```text
Token {
    kind
    span
}
```

không chứa string.

Identifier lookup có thể dùng:

```text
SymbolId
```

sau khi token được intern.

Quan trọng:

> Lexer không cần intern mọi identifier.

Hai tầng:

```text
Token
  ↓
identifier text span
  ↓
SymbolInterner
```

Parser/resolver quyết định khi nào cần `SymbolId`.

Điều này giúp lexer nhanh và giảm memory.

---

# 30. Token interning

Keyword:

```text
keyword enum
```

không cần interner.

Identifier có thể intern thành:

```text
SymbolId
```

nhưng source span vẫn giữ nguyên.

Không dùng interned string làm source provenance.

---

# 31. Token identity

Token identity **không phải**:

```text
pointer address
```

Không phải:

```text
String object identity
```

Canonical:

```text
SourceFileId + Revision + Span + TokenKind
```

Trong incremental engine có thể có `TokenId` riêng.

---

# 32. Incremental lexing

Đây là phần rất quan trọng cho IDE/AI.

Khi source thay đổi:

```text
old source
    ↓
edit [start,end)
    ↓
new source
```

Không lex lại toàn bộ file nếu không cần.

Lexer phải hỗ trợ checkpoint:

```text
LexerCheckpoint {
    byte_offset
    lexical_state
}
```

Thông thường checkpoint tại newline.

Ví dụ sửa:

```text
line 100
```

lexer có thể:

1. tìm checkpoint trước edit;
2. restore state;
3. lex lại từ đó;
4. tìm synchronization point;
5. reuse token suffix nếu state + source boundary tương đương.

---

# 33. Incremental synchronization

Có thể sync khi:

```text
same lexical state
+
same source bytes
+
same token sequence boundary
```

Ví dụ source sau edit trở lại giống old source từ:

```text
line 110
```

thì suffix token có thể reuse.

Không được reuse chỉ vì byte text giống nhau nếu lexical state khác.

Ví dụ cực quan trọng:

```text
/*
...
```

Một edit phía trước có thể làm thay đổi block-comment state hàng trăm dòng phía sau.

---

# 34. Lexer checkpoint state

Checkpoint phải chứa tối thiểu:

```text
LexState {
    mode
    block_comment_depth
    raw_string_delimiter
}
```

Nếu lexer grammar tương lai thêm state thì checkpoint version phải được cập nhật.

---

# 35. Error recovery

Lexer không được dừng tại lỗi đầu tiên.

Ví dụ:

```text
let x = "unterminated
let y = 10
```

Lexer phải có chiến lược recovery để không biến toàn bộ file thành một string vô hạn.

Ví dụ:

- EOF → terminate string.
- newline → tùy string grammar, có thể recover.
- invalid escape → consume escape unit và tiếp tục.
- invalid UTF-8 → consume minimal invalid byte sequence.

---

# 36. Forward progress invariant

Đây là invariant cực quan trọng:

```text
LEX-RECOVERY-01
Every lexer iteration either:
    advances input
or
    terminates.
```

Không được:

```text
pos_next == pos_current
```

trong vòng lặp vô hạn.

Fuzzer phải test invariant này.

---

# 37. Unknown characters

Ví dụ:

```text
§
```

nếu chưa có grammar tương ứng.

Lexer:

```text
Unknown
```

hoặc:

```text
ErrorToken
```

với diagnostic.

Không được tự động bỏ ký tự.

Lossless syntax yêu cầu source vẫn reconstruct được.

---

# 38. Synthetic token

Lexer chủ yếu tạo token từ source thật.

Parser mới chủ yếu tạo synthetic tokens:

```text
MissingCloseParen
MissingBrace
```

Synthetic token:

```text
synthetic = true
span = [position, position)
```

Không bao giờ nhầm với source token.

---

# 39. Lexer diagnostics

Diagnostic phải structured:

```text
Diagnostic {
    code
    severity
    primary_span
    secondary_spans
    message
    notes
    fixes
}
```

Ví dụ:

```text
LEX-E001 InvalidUtf8
LEX-E002 InvalidCharacter
LEX-E003 UnterminatedString
LEX-E004 InvalidEscape
LEX-E005 InvalidCharLiteral
LEX-E006 InvalidByteLiteral
LEX-E007 InvalidNumericLiteral
LEX-E008 InvalidIdentifier
LEX-E009 UnexpectedEndOfInput
LEX-E020 UnterminatedBlockComment
```

Mã diagnostic ổn định.

---

# 40. Lexer diagnostics không được semantic hóa

Không báo:

```text
"unknown type"
```

từ lexer.

Lexer chỉ báo:

```text
invalid lexical form
```

Resolver/typechecker xử lý:

```text
unknown type
unknown symbol
trait not implemented
```

---

# 41. Literal decoding architecture

Không nên:

```text
Lexer → decoded runtime String
```

Mà:

```text
Lexer
   ↓
LiteralToken
   ↓
LiteralDecoder
   ↓
TypedLiteral
```

Ví dụ:

```text
"hello\n"
```

Token giữ:

```text
span = [0,8)
```

Decoder tạo semantic value:

```text
StringLiteralValue
```

sau đó HIR/const evaluator quyết định materialization.

---

# 42. Numeric decoding architecture

Tương tự:

```text
Token
 ↓
NumericLiteralSyntax
 ↓
LiteralParser
 ↓
ArbitraryPrecisionIntermediate
 ↓
Type-directed conversion
 ↓
Typed constant
```

Không nên decode trực tiếp vào `u64` trong lexer.

Lý do:

```text
999999999999999999999999999999999
```

có thể hợp lệ về lexical syntax nhưng vượt type.

Lexer không nên biết target type.

---

# 43. Source slices

API:

```text
source.slice(span) -> &[u8]
source.text(span) -> Utf8Slice
```

`Utf8Slice` phải bảo đảm span nằm trên UTF-8 boundary nếu API yêu cầu text.

Raw byte slice có thể không cần boundary.

---

# 44. Lexer API

Implementation-ready API đề xuất:

```text
struct Lexer<'src> {
    source: &'src Utf8Source
    position: u32
    state: LexState
    diagnostics: DiagnosticSink
}
```

Nhưng đây chỉ là implementation model.

Axiom compiler internal không bắt buộc dùng reference syntax giống Rust.

API logic:

```text
Lexer::new(source)
Lexer::next()
Lexer::checkpoint()
Lexer::restore(checkpoint)
Lexer::lex_all()
Lexer::lex_incremental(old_tokens, edit)
```

Kết quả:

```text
LexResult {
    tokens
    diagnostics
    line_index_delta
}
```

---

# 45. Iterator interface

Lexer nên expose iterator-like API:

```text
next() -> Token
```

với:

```text
EOF
```

là token hợp lệ.

Parser không nên gọi lexer bằng:

```text
while !lexer.eof()
```

rồi lại gọi thêm lần nữa.

EOF phải có semantic identity ổn định.

---

# 46. Parser token view

Parser cần:

```text
peek()
peek_n(n)
consume()
expect(kind)
at(kind)
eat(kind)
```

và trivia-aware behavior:

```text
peek_nontrivia()
consume_nontrivia()
```

Nhưng không nên để parser tự scan whitespace.

Lexer/token layer chịu trách nhiệm cung cấp filtered view.

---

# 47. Newline-aware parser API

Parser có thể hỏi:

```text
has_line_break_before(token)
```

hoặc token flag:

```text
preceded_by_newline
```

Điều này hữu ích cho statement termination mà không phải quét ngược source.

---

# 48. Lexer performance

Mục tiêu:

```text
O(n)
```

trong source size.

Không:

```text
O(n²)
```

do substring allocation hoặc repeated Unicode normalization.

Khuyến nghị:

- byte scanner.
- ASCII fast path.
- UTF-8 decode chỉ khi gặp non-ASCII.
- operator trie.
- keyword perfect hash/hash table.
- zero-copy spans.
- bump/arena allocation cho temporary lexer structures.
- SIMD scanning có thể là optimization implementation detail.
- incremental reuse.

---

# 49. ASCII fast path

Phần lớn source là ASCII.

Lexer có thể xử lý nhanh:

```text
if byte < 0x80:
    fast ASCII path
else:
    Unicode decoder
```

Ví dụ identifier:

```text
foo_bar123
```

không cần gọi Unicode library cho từng byte.

Unicode identifier boundary chỉ cần Unicode processing khi byte >= 0x80.

---

# 50. Unicode version pinning

Compiler phải có:

```text
UnicodeVersion
```

gắn với compiler semantic version.

Nếu Unicode XID tables thay đổi, compiler semantic version phải phản ánh thay đổi.

Điều này quan trọng cho:

- reproducible builds;
- incremental cache;
- package semantic fingerprint;
- cross-machine consistency.

---

# 51. Lexer configuration

Lexer không nên phụ thuộc runtime configuration.

Một số lexical configuration có thể phụ thuộc:

```text
LanguageVersion
CompatibilityMode
```

Ví dụ:

```text
semicolon compatibility
```

Nhưng target CPU/GPU không được thay đổi lexical grammar.

---

# 52. Language version

Tokenization phải deterministic theo:

```text
LanguageVersion
```

Ví dụ future:

```text
v1:
keyword foo = identifier

v2:
foo = keyword
```

thì semantic compiler version/version gate phải phân biệt.

Không silently thay đổi lexer giữa patch compiler versions.

---

# 53. Lossless tree integration

Pipeline:

```text
Source
  ↓
Raw Tokens
  ↓
Green Tree
  ↓
AST
```

Green tree giữ:

- token kind
- token text/span
- trivia
- child nodes
- missing/synthetic nodes.

AST chỉ giữ semantic-relevant structure.

Ví dụ:

```text
let /*comment*/ x = 1
```

AST:

```text
LetDecl(
    name=x,
    initializer=1
)
```

Green tree giữ comment.

---

# 54. Formatter requirement

Formatter không được phụ thuộc AST để tái tạo source nguyên bản.

Phải dùng lossless tree/token trivia.

Do đó có thể:

```text
parse
→ format
```

mà không mất:

- comments;
- attributes;
- source trivia;
- unknown/recovery information.

---

# 55. Lexer + AI tooling

CompilerDB nên expose:

```text
token_at(SourceFileId, byte_offset)
tokens_in(SourceSpan)
lexical_context(SourceSpan)
```

AI agent có thể hỏi:

```text
"Token này là gì?"
```

mà không phải parse lại file.

Structured response:

```text
TokenFact {
    kind
    span
    source_text
    lexical_state
    synthetic
    diagnostics
}
```

AI không được sửa token database trực tiếp.

---

# 56. Fuzzing

Lexer phải có fuzz target:

```text
fuzz_lexer_random_bytes
fuzz_lexer_valid_utf8
fuzz_lexer_edit_sequences
fuzz_lexer_nested_comments
fuzz_lexer_numeric_literals
fuzz_lexer_strings
fuzz_lexer_unicode_identifiers
fuzz_lexer_operator_sequences
```

Property:

```text
never crash
never hang
always terminate
never out-of-bounds
always forward progress
```

---

# 57. Lossless round-trip property

Với source hợp lệ hoặc partially recovered:

```text
tokens_to_source(lex(source))
```

phải giữ được source bytes nguyên bản trong raw/lossless mode.

Đặc biệt:

```text
comments
spaces
tabs
newlines
literal spelling
identifier spelling
unknown characters
```

không được tự ý biến đổi.

---

# 58. Incremental equivalence

Test:

```text
lex(old_source)
apply_edit
incremental_lex(old_tokens, edit)
```

phải tương đương:

```text
lex(new_source)
```

về semantic token stream.

Lossless token spans sẽ khác do offset shift là bình thường; token kinds/source slices phải tương đương.

---

# 59. Lexer correctness hierarchy

Lexer correctness được kiểm tra theo thứ tự:

```text
1. Memory safety
2. Termination
3. UTF-8 correctness
4. Token boundary correctness
5. Longest-match correctness
6. Lossless preservation
7. Diagnostic correctness
8. Incremental equivalence
9. Performance
```

Performance không được phép đánh đổi 1–8.

---

# 60. Không semantic speculation

Lexer tuyệt đối không làm:

```text
type inference
trait lookup
name resolution
ownership
constant evaluation
macro expansion
```

Ví dụ:

```text
foo<T>
```

lexer chỉ biết:

```text
Identifier
<
Identifier
>
```

Parser/resolver quyết định đây là generic syntax hay comparison tùy grammar/context.

---

# 61. Lexer boundary contract

Lexer cung cấp cho parser:

```text
Token kind
Source span
Raw source spelling
Trivia
Newline information
Lexical diagnostics
```

Lexer **không** cung cấp:

```text
Type
Symbol resolution
Ownership
Trait
ABI
Effect
```

Đây là boundary bắt buộc.

---

# 62. CompilerDB integration

Thêm:

```text
LexerDB
```

hoặc tốt hơn, không tạo subsystem database riêng nếu không cần.

CompilerDB query:

```text
raw_tokens(SourceFileId, Revision)
semantic_tokens(SourceFileId, Revision)
line_index(SourceFileId, Revision)
lex_diagnostics(SourceFileId, Revision)
```

Query dependencies:

```text
SourceFile
LanguageVersion
LexerGrammarVersion
```

Khi source không đổi:

```text
cache hit
```

Khi chỉ source file khác thay đổi:

```text
không invalidate lexer của file này
```

---

# 63. Fingerprint

Lexical fingerprint:

```text
LexFingerprint =
    hash(
        source_content
        language_version
        lexer_semantic_version
    )
```

Không đưa:

```text
worker_count
memory_address
process_id
```

vào fingerprint.

---

# 64. Parallel lexing

Các source file độc lập có thể lex song song:

```text
file A ─┐
file B ─┼→ Lexer queries
file C ─┤
file D ─┘
```

Semantic output phải deterministic bất kể worker count.

Một file đơn lẻ có thể incremental; chưa cần parallelize từng byte range trong v1.

---

# 65. Lexer memory strategy

Lexer không cần giữ allocation lớn.

Khuyến nghị:

```text
Source bytes
    │
    ├── Token arena/index
    ├── Diagnostics arena
    └── LineIndex
```

Token chỉ khoảng:

```text
kind + span + flags
```

nên memory footprint thấp.

Với file lớn:

```text
10 MB source
```

không được tạo:

```text
10 MB duplicated token strings
```

---

# 66. EOF semantics

EOF token:

```text
Token {
    kind: EOF
    span: [source_len, source_len)
}
```

EOF luôn tồn tại.

Repeated:

```text
next()
next()
next()
```

sau EOF vẫn trả EOF, không advance.

---

# 67. Error token semantics

Error token phải có non-zero span nếu có source byte lỗi.

Ví dụ:

```text
?
```

nếu `?` thực ra hợp lệ thì không error.

Nếu byte không hợp lệ:

```text
Error(span=[x,x+1))
```

Sau đó lexer tiếp tục từ:

```text
x+1
```

---

# 68. Malformed strings

Ví dụ:

```text
"abc\q"
```

Lexer có thể tạo:

```text
StringLiteral
```

kèm diagnostic `InvalidEscape`, hoặc `ErrorToken`, tùy literal grammar.

Khuyến nghị giữ **một token literal duy nhất** nếu có thể để parser recovery tốt hơn.

---

# 69. Malformed numbers

Ví dụ:

```text
123abc
```

Cần grammar decision rõ.

Khuyến nghị lexer:

```text
IntegerLiteral(123)
Identifier(abc)
```

nếu không có numeric suffix syntax tương ứng.

Nhưng:

```text
123u32
```

nếu suffix hợp lệ thì một numeric literal.

Do đó numeric scanner phải có suffix table.

---

# 70. Lexical grammar source of truth

Không hard-code lexer rule rải rác.

Tạo bảng/spec:

```text
LexicalGrammar {
    keywords
    operators
    punctuation
    numeric_rules
    string_rules
    identifier_rules
    comment_rules
    whitespace_rules
}
```

Implementation có thể generate:

```text
keyword table
operator trie
character classes
```

từ canonical grammar data.

---

# 71. Testing matrix

Ít nhất:

### ASCII

```text
let x = 1
fn main() {}
```

### Unicode

```text
let người = "Hà Nội"
let Δ = 10
```

### Comments

```text
// ...
/* ... */
/* /* nested */ */
```

### Strings

```text
"hello"
"hello\nworld"
"\u{1F600}"
```

### Numbers

```text
0
123
1_000
0xff
0b1010
1.25
1e10
1.2e-3
```

### Operators

```text
a+b
a==b
a!=b
a<=b
a>=b
a&&b
a||b
a..b
a..=b
```

### Recovery

```text
"unterminated
/*
invalid
```

### Incremental

- insert
- delete
- replace
- multiline comment crossing edit
- raw string delimiter crossing edit.

---

# 72. Conformance tests

Mỗi lexical rule phải có:

```text
valid examples
invalid examples
boundary examples
Unicode examples
incremental examples
```

Golden test:

```text
source → expected token sequence
```

Ví dụ:

```text
let x = 42
```

expected:

```text
KW_LET
IDENTIFIER("x")
EQUAL
INTEGER("42")
NEWLINE
EOF
```

Raw token test additionally kiểm tra:

```text
WHITESPACE
```

---

# 73. Critical invariants

Đóng băng các invariant:

```text
ALEX-20
Lexer operates on UTF-8 source bytes.

ALEX-21
SourceSpan uses byte offsets.

ALEX-22
SourceSpan is half-open.

ALEX-23
Invalid UTF-8 is diagnosed and never silently replaced.

ALEX-24
Lexer does not perform semantic name resolution.

ALEX-25
Lexer does not perform type checking.

ALEX-26
Lexer preserves source spelling through spans.

ALEX-27
Raw/lossless tokenization preserves trivia.

ALEX-28
Newline is represented explicitly.

ALEX-29
Newline does not itself define statement semantics.

ALEX-30
Identifier classification is deterministic and locale-independent.

ALEX-31
Unicode identifier rules are versioned.

ALEX-32
Identifier normalization is not performed implicitly.

ALEX-33
Keyword recognition occurs after identifier scanning.

ALEX-34
Operators obey longest-match semantics.

ALEX-35
Malformed input must not cause lexer nontermination.

ALEX-36
Every recovery step makes forward progress unless EOF is reached.

ALEX-37
Nested block comments are supported.

ALEX-38
Literal decoding is separate from tokenization.

ALEX-39
Numeric range/type validation is outside the lexer.

ALEX-40
Token representation does not require duplicated source strings.

ALEX-41
Token source identity is represented through SourceSpan.

ALEX-42
EOF is a stable zero-width token.

ALEX-43
Synthetic tokens are explicitly distinguishable from source tokens.

ALEX-44
Lexer diagnostics are structured compiler diagnostics.

ALEX-45
Lexer has no dependency on target CPU/ABI.

ALEX-46
Incremental lexing is semantically equivalent to full lexing.

ALEX-47
Incremental reuse requires equivalent lexical state.

ALEX-48
Unicode/version changes participate in lexical cache identity.

ALEX-49
Lexer results are deterministic independent of worker count.

ALEX-50
Lossless tokenization preserves source information required by formatter and refactoring.

ALEX-51
Lexer never creates ownership/type/trait semantic facts.

ALEX-52
Lexer implementation must remain memory-safe and bounds-safe.

ALEX-53
Lexer fuzzing must guarantee termination.

ALEX-54
Lexer cache entries are revision-dependent.

ALEX-55
Lexer semantic state is owned by CompilerDB/query infrastructure.

ALEX-56
Parser and semantic layers cannot reinterpret malformed lexical bytes as valid source.

ALEX-57
Recovery must not fabricate semantic tokens indistinguishable from real source tokens.

ALEX-58
Source provenance remains available for every non-synthetic token.

ALEX-59
Token ordering follows source byte ordering.

ALEX-60
The lexical grammar is independent of physical code-generation strategy.
```

---

# 74. Implementation structure

Agent có thể triển khai trực tiếp theo cấu trúc:

```text
compiler/
└── frontend/
    └── lexer/
        ├── mod.ax
        ├── source.ax
        ├── span.ax
        ├── line_index.ax
        ├── token.ax
        ├── token_kind.ax
        ├── trivia.ax
        ├── unicode.ax
        ├── identifier.ax
        ├── number.ax
        ├── string.ax
        ├── char.ax
        ├── comment.ax
        ├── operator.ax
        ├── state.ax
        ├── lexer.ax
        ├── incremental.ax
        ├── diagnostics.ax
        └── tests/
            ├── basic/
            ├── unicode/
            ├── literals/
            ├── comments/
            ├── operators/
            ├── recovery/
            ├── incremental/
            └── fuzz/
```

Tên file chỉ là recommendation; semantic architecture mới là normative.

---

# 75. Implementation order

Agent không nên code tất cả cùng lúc.

Thứ tự:

```text
1. SourceFile / SourceSpan
2. LineIndex
3. TokenKind
4. ASCII scanner
5. Whitespace/Newline
6. Identifier/Keyword
7. Operators/Punctuation
8. Numeric literals
9. String/Char/Byte literals
10. Comments
11. Recovery
12. Lossless token stream
13. Diagnostics
14. Incremental checkpoints
15. Incremental lexing
16. Token interning
17. CompilerDB integration
18. Fuzzing
19. Performance benchmark
20. Conformance freeze
```

---

# 76. Benchmark targets

Lexer benchmark phải đo riêng:

```text
MB/s
tokens/s
allocations/source-MB
peak memory
incremental edit latency
```

Dataset:

```text
small source
medium project
large generated source
Unicode-heavy source
comment-heavy source
literal-heavy source
```

Không dùng một benchmark duy nhất để kết luận.

---

# 77. Kết luận kiến trúc

Lexer Axiom nên giữ nguyên nguyên tắc lớn của toàn compiler:

> **Frontend giữ thông tin đầy đủ; semantic layer thêm meaning; optimizer không được cần quay lại đoán source.**

Do đó:

```text
Raw Source
    ↓
Lossless Lexer
    ↓
Lossless Green Tree
    ↓
Semantic AST
    ↓
HIR
```

thay vì:

```text
Source
 ↓
Lexer làm mất trivia
 ↓
Parser cố đoán lại
 ↓
Formatter cố reconstruct source
```

Thiết kế này đặc biệt phù hợp với mục tiêu Axiom về **IDE + refactoring + compiler incremental + AI-native tooling**.

**BOOTSTRAP-275 được xem là FROZEN/COMPLETED.**

### Task kế tiếp

**BOOTSTRAP-276 — AXIOM NAME RESOLUTION, MODULE GRAPH & SYMBOL SYSTEM**

Sẽ khóa toàn bộ:

- module/package namespace;
- `use/import`;
- `pub`, `pub(module)`, `pub(package)`;
- lexical scope;
- item scope;
- local scope;
- shadowing;
- overload/function namespace;
- type namespace;
- value namespace;
- trait/impl namespace;
- associated item lookup;
- module cycles;
- symbol IDs;
- unresolved/ambiguous symbols;
- import aliases;
- glob import nếu có;
- qualified path;
- method/extension resolution boundary;
- cross-package symbol resolution;
- incremental symbol graph;
- CompilerDB `DeclarationDB/SymbolDB/ModuleDB`;
- deterministic resolution;
- AI query API cho symbol graph.

Đây là bước rất quan trọng trước khi đi sâu hơn vào **type inference + expression typing + ownership**, vì từ đây compiler mới có một **symbol graph hoàn chỉnh** để tất cả semantic phase phía sau dùng chung.