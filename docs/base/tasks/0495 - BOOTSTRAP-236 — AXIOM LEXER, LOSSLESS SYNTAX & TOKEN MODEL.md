# BOOTSTRAP-236 — AXIOM LEXER, LOSSLESS SYNTAX & TOKEN MODEL

**TRẠNG THÁI: FROZEN / COMPLETED**

Đây là tầng frontend thấp nhất nhưng ảnh hưởng trực tiếp đến **parser, formatter, IDE, incremental compilation, diagnostics và AI tooling**.

Mục tiêu:

> **Lexer không chỉ nhận diện token; nó phải bảo toàn đủ thông tin nguồn để compiler có thể tái dựng cấu trúc và công cụ có thể làm việc mà không cần reparsing toàn bộ file.**

---

# 1. Pipeline frontend chính thức

```text
UTF-8 bytes
    ↓
Source Text
    ↓
Unicode Scalar Processing
    ↓
Lexer
    ↓
Token Stream
    ↓
Lossless Syntax Tree
    ↓
AST
    ↓
Resolver
    ↓
HIR
```

Trong đó:

```text
Token Stream ≠ AST
Lossless Syntax Tree ≠ AST
```

Mỗi tầng có mục đích riêng.

---

# 2. Source representation

Compiler không nên coi source chỉ là:

```text
String
```

mà:

```text
SourceFile {
    file_id
    revision
    text
    encoding
}
```

Axiom source mặc định:

```text
UTF-8
```

---

# 3. UTF-8 invariant

Axiom source compiler phải xác định rõ:

```text
valid UTF-8
```

Nếu source chứa byte sequence không hợp lệ:

```text
LEX-UTF8-001
```

compiler báo lỗi lexical.

Không âm thầm thay thế bằng `�`.

Điều này quan trọng cho:

- source hash
- diagnostics
- source mapping
- reproducible build
- identifier identity

---

# 4. Unicode model

Lexer xử lý:

```text
UTF-8 bytes
      ↓
Unicode scalar values
```

Không coi một Unicode code point là một byte.

Ví dụ:

```text
é
```

có thể chiếm nhiều UTF-8 bytes nhưng vẫn là một Unicode scalar value.

---

# 5. Identifier model

Identifier hỗ trợ Unicode theo quy tắc được định nghĩa rõ.

Ví dụ:

```axiom
let tên = "Axiom"
```

có thể hợp lệ nếu ký tự thuộc identifier class.

Nhưng:

```text
Unicode normalization
```

không được tự động thay đổi identifier spelling.

---

# 6. Identifier identity

Đây là điểm quan trọng.

Hai identifier:

```text
é
é
```

có thể có biểu diễn Unicode khác nhau.

Lexer **không tự NFC-normalize** để biến chúng thành cùng identifier.

Identity dựa trên source scalar sequence theo language specification.

Normalization là vấn đề riêng của text processing.

---

# 7. Token structure

Canonical:

```text
Token {
    kind: TokenKind
    span: SourceSpan
    flags: TokenFlags
}
```

Không lưu text copy trong từng token.

Token tham chiếu source thông qua:

```text
SourceSpan
```

---

# 8. SourceSpan

```text
SourceSpan {
    file: SourceFileId
    start: u32
    end: u32
}
```

Offset tính theo:

```text
UTF-8 byte offset
```

Đây là lựa chọn tốt cho:

- slicing source
- diagnostics
- incremental edits
- parser
- source map

Line/column được tính qua line index.

---

# 9. Line index

Compiler giữ:

```text
LineIndex {
    line_starts
}
```

Ví dụ:

```text
byte offsets:
0
10
25
41
```

Khi diagnostic cần:

```text
line
column
```

compiler binary-search `line_starts`.

Không lưu line/column trong mỗi token.

---

# 10. Token categories

```text
Identifier
Keyword
IntegerLiteral
FloatLiteral
StringLiteral
ByteStringLiteral
CharLiteral

Operator
Punctuation

Newline
Indentation
Comment
Whitespace

Unknown
Error
EOF
```

Nhưng cần phân biệt:

> **Semantic tokens** và **trivia**.

---

# 11. Trivia

Trivia gồm:

```text
Whitespace
Comment
```

và các source elements không trực tiếp tạo semantic AST.

Ví dụ:

```axiom
let x = 10    // value
```

Comment phải được giữ trong Lossless Syntax Tree.

---

# 12. Token stream không nhất thiết giữ trivia riêng

Thiết kế tốt:

```text
Token
    semantic token
    leading trivia range
```

hoặc lossless syntax layer giữ trivia.

Mục tiêu tránh:

```text
Parser phải xử lý comment
```

Parser chỉ quan tâm semantic tokens.

---

# 13. Newline

Axiom là language có newline-sensitive statement termination.

Do đó newline phải được lexer nhận diện.

Ví dụ:

```axiom
let x = 10
let y = 20
```

có newline boundary.

---

# 14. Nhưng newline không phải lúc nào cũng statement terminator

Ví dụ:

```axiom
let x =
    foo(
        a,
        b
    )
```

newline bên trong expression không kết thúc statement.

Lexer/parser cần phân biệt:

```text
physical newline
```

và:

```text
semantic statement boundary
```

---

# 15. Newline token

Đề xuất:

```text
NEWLINE
```

được lexer phát ra, nhưng parser quyết định nó có phải statement terminator hay không.

Điều này tốt hơn việc lexer tự quyết định grammar.

---

# 16. Parenthesis suppression

Trong:

```axiom
foo(
    a,
    b
)
```

newline có thể tồn tại trong token stream nhưng parser hiểu rằng:

```text
expression continuation
```

Tương tự:

```text
[
]
(
)
```

không nên khiến newline trở thành statement boundary.

---

# 17. Statement termination rule

Canonical semantic rule:

Statement kết thúc khi:

```text
NEWLINE
```

xuất hiện tại vị trí mà grammar cho phép statement termination.

Hoặc:

```text
}
```

đóng block.

EOF cũng có thể terminate statement cuối nếu grammar cho phép.

---

# 18. Semicolon

Axiom Core canonical không khuyến khích semicolon.

Nhưng compatibility parser có thể chấp nhận:

```axiom
let x = 10;
```

Formatter chuyển thành:

```axiom
let x = 10
```

Semicolon không trở thành semantic construct riêng.

---

# 19. Keywords

Keyword table được compiler-generated/static.

Ví dụ:

```text
fn
let
mut
struct
enum
trait
impl
for
in
if
else
loop
while
match
return
break
continue
pub
module
use
type
const
comptime
async
await
unsafe
extern
```

---

# 20. Keyword không phải identifier

```axiom
let fn = 10
```

→ lexical/syntax error.

Không có context-sensitive keyword ở Core v1 nếu không cần.

---

# 21. Operators

Lexer phải nhận diện:

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
=
+=
-=
*=

&&
||

!
?
..
..=
::

->
=>
```

và các operator được specification cho phép.

---

# 22. Longest-match rule

Ví dụ:

```text
>=
```

phải lex thành:

```text
GE
```

không:

```text
>
=
```

Rule:

> **Lexer luôn chọn token hợp lệ dài nhất tại vị trí hiện tại.**

Ngoại lệ chỉ khi grammar lexical explicitly quy định.

---

# 23. `.` ambiguity

Lexer cần phân biệt:

```text
.
..
..=
```

và decimal:

```text
3.14
```

Lexical state phải xác định deterministic.

---

# 24. Numeric literals

Hỗ trợ:

```text
123
1_000_000

0xff
0b1010
0o755

123u32
123i64

3.14
3.14f32

1e10
1.5e-3
```

Underscore chỉ được phép ở vị trí lexical hợp lệ.

---

# 25. Numeric literal không tự overflow

Lexer không cần quyết định:

```text
999999999999999999999999
```

có fit `i32` hay không.

Lexer chỉ tạo:

```text
IntegerLiteral
```

Type/literal semantic phase quyết định range.

Điều này giữ separation:

```text
Lexing
≠
Type checking
```

---

# 26. Literal representation

Không nên parse literal thành machine integer ngay lexer.

Ví dụ:

```text
IntegerLiteral {
    base
    digits
    suffix
    span
}
```

Parser/semantic layer mới convert thành constant value.

---

# 27. String literals

Canonical:

```axiom
"hello"
```

Lexer tạo:

```text
StringLiteral
```

nhưng escape processing cần rõ ràng.

Ví dụ:

```text
\n
\t
\\
\"
\u{...}
```

---

# 28. String source vs value

Không được nhầm:

```text
source representation
```

với:

```text
runtime String value
```

Ví dụ source:

```text
"\n"
```

runtime value có một newline.

AST constant node chứa semantic value sau khi decode.

Lossless tree vẫn giữ source spelling.

---

# 29. Raw strings

Có thể hỗ trợ:

```axiom
r#"hello \n world"#
```

nhưng lexical grammar phải cố định trước khi implementation.

Raw string là syntax convenience, không phải runtime type mới.

---

# 30. Byte strings

Axiom phân biệt:

```axiom
"hello"
```

và:

```axiom
b"hello"
```

String:

```text
Unicode/UTF-8 text
```

Byte string:

```text
Bytes
```

---

# 31. Char literal

Nếu giữ `char` Core:

```axiom
'a'
```

phải đại diện cho:

```text
Unicode scalar value
```

Không phải arbitrary byte.

Byte literal nếu cần:

```axiom
b'a'
```

---

# 32. Comment syntax

Canonical:

```text
// line comment
```

và:

```text
/*
   block comment
*/
```

Block comment nên hỗ trợ nesting nếu muốn compiler/tooling đơn giản hơn khi xử lý generated source:

```text
/*
    outer
    /*
        inner
    */
*/
```

Nếu chọn hỗ trợ nesting, đây phải là lexical rule chính thức.

**Khuyến nghị: hỗ trợ nested block comments.**

---

# 33. Comment preservation

Lossless syntax giữ:

```text
comment span
```

để:

- formatter
- documentation extraction
- IDE
- refactoring
- source transformation
- AI context

không làm mất comment.

---

# 34. Doc comments

Không tạo một lexical language thứ hai.

Ví dụ:

```text
/// Adds two numbers.
```

Lexer vẫn có thể trả:

```text
LineComment
```

Documentation extractor nhận diện prefix:

```text
///
```

và chuyển thành documentation metadata.

---

# 35. Invalid characters

Ví dụ:

```text
let x = §
```

Lexer không crash.

Tạo:

```text
Unknown
```

hoặc:

```text
LexError
```

với span chính xác.

Parser tiếp tục recovery.

---

# 36. Error recovery

Input:

```axiom
fn main( {
    let x =
}
```

Lexer vẫn phải tiến tới EOF.

Không được:

```text
panic
exit process
```

chỉ vì một ký tự malformed.

---

# 37. Lossless Syntax Tree

Đây là representation quan trọng:

```text
GreenNode
GreenToken
```

theo mô hình immutable tree.

Ví dụ:

```text
Function
├── fn
├── Identifier(main)
├── ParameterList
│   └── ...
├── Block
│   ├── {
│   ├── Statement
│   └── }
└── ...
```

---

# 38. Green tree / red tree

Khuyến nghị:

```text
Green Tree
    immutable
    parentless
    compact
    shareable

Red Tree
    parent/context aware
    lazily constructed
    IDE-friendly
```

Green tree rất phù hợp incremental compiler.

---

# 39. Incremental editing

User sửa:

```text
x = 10
```

thành:

```text
x = 100
```

compiler không nên parse lại toàn bộ file nếu không cần.

Flow:

```text
Text Edit
 ↓
Incremental Lex
 ↓
Changed Token Region
 ↓
Incremental Syntax Reparse
 ↓
Reuse unchanged Green Nodes
```

---

# 40. Token reuse

Token IDs không nhất thiết phải ổn định tuyệt đối giữa revision.

Semantic IDs:

```text
DeclarationId
TypeId
FunctionId
```

mới là identity quan trọng.

Tuy nhiên syntax nodes có thể sử dụng stable/reused green-node identity để giảm work.

---

# 41. Syntax tree immutability

Green tree:

```text
immutable
```

Khi edit:

```text
old tree
```

vẫn tồn tại nếu cần cho incremental query.

Revision mới:

```text
new tree
```

chia sẻ unchanged subtrees.

---

# 42. Parser contract

Parser nhận:

```text
TokenStream
```

và trả:

```text
SyntaxTree
```

Parser không được:

```text
resolve names
type check
trait solve
ownership check
```

---

# 43. Lexer state

Lexer state tối thiểu:

```text
LexerCursor
LexicalMode
SourcePosition
```

Lexical mode cần cho:

```text
normal
string
raw string
char
comment
```

Không để state phụ thuộc vào semantic type system.

---

# 44. Lexer deterministic

Cùng:

```text
source bytes
```

phải cho cùng:

```text
TokenKinds
Spans
Literal contents
```

Không phụ thuộc:

```text
locale
machine
thread scheduling
hash randomization
```

---

# 45. Lexer performance

Lexer phải được thiết kế cho:

```text
GB-scale source trees
```

về architecture, dù file thông thường nhỏ.

Ưu tiên:

```text
linear O(n)
single forward scan
zero allocation where possible
slice-based literals
ASCII fast path
Unicode slow path
```

---

# 46. ASCII fast path

Identifier/operator/keyword scanning phần lớn source thường là ASCII.

Lexer có thể:

```text
ASCII fast path
```

và chỉ chuyển Unicode path khi gặp byte >= `0x80`.

Điều này cải thiện throughput mà không thay đổi semantics.

---

# 47. Keyword lookup

Không nên:

```text
if token == "fn"
else if token == "let"
else if token == "mut"
...
```

dài hàng trăm nhánh.

Dùng:

```text
perfect hash
static trie
generated lookup table
```

tùy implementation.

---

# 48. Lexer allocation policy

Không copy:

```text
identifier text
literal text
comment text
```

mỗi lần.

Token chỉ giữ:

```text
span
```

và source text là backing storage.

AST semantic nodes chỉ copy khi thật sự cần intern.

---

# 49. Identifier interning

Sau resolution/type phases, identifier names có thể được intern:

```text
SymbolId
```

Ví dụ:

```text
"println"
```

chỉ có một canonical interned representation trong CompilerDB revision.

---

# 50. Token flags

TokenFlags có thể chứa:

```text
HasEscape
HasSuffix
ContainsUnicode
PrecededByWhitespace
FollowedByWhitespace
Synthetic
Recovered
```

Nhưng:

> Không đưa thông tin semantic vào TokenFlags.

Ví dụ không:

```text
IsMutableVariable
IsType
IsTrait
```

vì lexer không biết.

---

# 51. Synthetic tokens

Parser recovery có thể tạo:

```text
SyntheticToken
```

Ví dụ thiếu:

```text
)
```

AST có thể tiếp tục phân tích.

Nhưng synthetic token:

```text
không có source span thật
```

và phải được đánh dấu:

```text
Synthetic
```

---

# 52. Synthetic source

Diagnostics phải biết:

```text
real source
vs
recovered/synthetic
```

AI/compiler API cũng phải expose certainty:

```text
Confirmed
Recovered
Incomplete
```

phù hợp với BOOTSTRAP-191.

---

# 53. Parser never trusts recovery as proof

Ví dụ:

```text
missing `}`
```

parser có thể tạo block đóng giả.

Nhưng compiler:

```text
Partial AST
```

không thể:

```text
Codegen
```

---

# 54. Formatter

Formatter lấy:

```text
Lossless Syntax Tree
```

chứ không lấy AST.

Vì AST đã mất:

```text
comments
original trivia
some syntactic choices
```

Formatter có thể:

```text
canonical formatting
```

nhưng vẫn bảo toàn comments/doc comments.

---

# 55. Refactoring

IDE refactoring nên thao tác trên:

```text
SyntaxTree
+
semantic spans
```

thay vì string replacement.

Ví dụ rename:

```text
FunctionId
```

→ tất cả semantic references.

Không rename comment/string literal nhầm thành identifier.

---

# 56. AI context

AI tooling có thể yêu cầu:

```text
ax context function Foo
```

Compiler trả:

```text
source
syntax
declaration
type
ownership
effects
references
diagnostics
```

Lossless syntax là nền tảng để tạo context chính xác.

---

# 57. Source map

Source span phải có thể đi:

```text
Source
 ↓
Syntax
 ↓
AST
 ↓
HIR
 ↓
MIR
 ↓
Machine
```

Mọi transformation cần preserve provenance.

---

# 58. Lexer test matrix

Phải có:

```text
ASCII identifiers
Unicode identifiers
keywords
operators
numbers
strings
chars
bytes
comments
nested comments
newline
CRLF
LF
EOF
invalid UTF-8
invalid escapes
invalid numbers
unknown characters
very long identifiers
very long literals
```

---

# 59. Line endings

Axiom source phải chấp nhận ít nhất:

```text
LF
CRLF
```

Compiler canonical internal newline representation có thể là:

```text
LF
```

nhưng source span vẫn map chính xác về byte offsets.

---

# 60. BOM

Nếu hỗ trợ UTF-8 BOM:

```text
EF BB BF
```

phải quy định rõ.

Khuyến nghị:

> chấp nhận UTF-8 BOM ở đầu file và coi nó là source encoding marker, không phải token semantic.

Không cho BOM giữa file.

---

# 61. EOF

Lexer luôn phát:

```text
EOF
```

với span zero-width:

```text
[start=end=file_length]
```

Điều này đơn giản hóa parser.

---

# 62. Empty file

Empty file là valid lexical input:

```text
EOF
```

Parser quyết định nó có hợp lệ như module rỗng hay không.

---

# 63. Whitespace

Whitespace bao gồm các ký tự được language specification xác định.

Không mặc định:

```text
mọi Unicode whitespace
```

đều được xem giống nhau nếu điều đó gây ambiguity.

Khuyến nghị:

- ASCII space
- tab
- CR/LF
- một tập Unicode whitespace được quy định rõ

nhưng parser không được phụ thuộc locale.

---

# 64. Tabs

Formatter có thể canonicalize indentation thành spaces.

Nhưng parser không nên biến tab thành semantic indentation vì Axiom không phải Python-style indentation language.

Newline là syntax boundary; block structure vẫn dùng:

```text
{ }
```

---

# 65. No indentation semantics

Đây là quyết định rõ ràng:

```text
Axiom indentation = formatting
Axiom braces = syntax
```

Do đó:

```text
if x {
    foo()
}
```

và indentation khác nhau vẫn cùng semantic structure.

---

# 66. Lexical ambiguity principle

Nếu một ambiguity có thể giải quyết ở parser:

```text
lexer không overfit
```

Ví dụ lexer không cần hiểu:

```text
generic < T >
```

là generic syntax.

Nó chỉ lex:

```text
<
Identifier
>
```

Parser/resolver xử lý context.

---

# 67. Lexer semantic firewall

Lexer **không biết**:

```text
TypeDB
TraitDB
Ownership
Capability
ABI
Target
```

Lexer chỉ biết:

```text
characters
lexical grammar
source spans
```

Đây là một boundary rất quan trọng.

---

# 68. Formal lexer contract

```text
Lex : UTF8Source → TokenStream
```

Tính chất:

```text
Deterministic
Linear
Loss-aware
Span-preserving
Error-recovering
Locale-independent
```

---

# 69. Lexer correctness

Invariant:

```text
LEX-20
Valid UTF-8 source produces a deterministic token stream.

LEX-21
Token spans are exact UTF-8 byte ranges.

LEX-22
Lexing does not perform semantic name resolution.

LEX-23
Lexing does not perform type inference.

LEX-24
Lexing does not perform ownership analysis.

LEX-25
Lexing preserves sufficient source information for lossless syntax reconstruction.

LEX-26
Lexer uses deterministic longest-match tokenization.

LEX-27
Lexical errors do not require process termination.

LEX-28
Lexer recovery must make forward progress.

LEX-29
Lexer must preserve exact literal source spelling through source spans.

LEX-30
Literal semantic decoding is distinct from source representation.

LEX-31
Numeric range validity is not a lexical responsibility.

LEX-32
Unicode identifier handling is deterministic and locale-independent.

LEX-33
Identifier normalization is not implicitly applied by the lexer.

LEX-34
Comments and relevant trivia remain available to lossless tooling.

LEX-35
Newline recognition is distinct from statement-termination determination.

LEX-36
Indentation is not semantic block structure.

LEX-37
Synthetic recovery tokens are explicitly marked as synthetic.

LEX-38
Recovered syntax cannot establish production semantic validity.

LEX-39
Token representation must avoid unnecessary source-text duplication.

LEX-40
Lexer output must be deterministic across platforms.

LEX-41
CRLF and LF handling must preserve source-span correctness.

LEX-42
EOF is represented explicitly.

LEX-43
Lexer complexity must remain independent of semantic type information.

LEX-44
Lossless syntax must support formatter and source-preserving refactoring.

LEX-45
Incremental lexing must permit reuse of unchanged source regions.

LEX-46
Syntax-tree reuse must not alter semantic identity.

LEX-47
Source provenance must survive lexical and syntax transformations.

LEX-48
Malformed source must remain representable in Partial Semantic Mode.

LEX-49
No partial lexical recovery may be treated as semantic proof.

LEX-50
The lexical layer must remain replaceable without changing Axiom semantics.
```

---

# 70. Kiến trúc frontend sau BOOTSTRAP-236

Đã có một foundation khá chắc:

```text
                 SourceDB
                    │
                    ▼
                UTF-8 Text
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
               AST Builder
                    │
                    ▼
                Resolver
                    │
                    ▼
                   HIR
```

Trong đó:

```text
Lexer
```

không bị kéo semantic complexity vào.

Nhưng:

```text
Lossless Syntax
```

đủ mạnh để phục vụ **compiler + IDE + formatter + refactoring + AI**.

---

# TASK TIẾP THEO

## **BOOTSTRAP-237 — AXIOM PARSER, AST & ERROR-RECOVERY ENGINE**

Bước tiếp theo sẽ thiết kế parser thực sự:

```text
TokenStream
     ↓
Grammar
     ↓
Recursive / Pratt / precedence parser
     ↓
Lossless Syntax Tree
     ↓
AST
```

và đặc biệt sẽ đóng đinh:

- expression grammar
- precedence/associativity
- generic-vs-comparison ambiguity
- method/call/index/slice parsing
- block expressions
- pattern grammar
- `if`/`match`/`loop`
- closure syntax
- type grammar
- generic/where grammar
- attribute grammar
- module/import grammar
- parser recovery
- error-tolerant IDE parsing
- **không để parser recovery làm thay đổi semantics của chương trình hợp lệ**.