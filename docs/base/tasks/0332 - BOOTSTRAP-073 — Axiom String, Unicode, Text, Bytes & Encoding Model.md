Tiếp tục.

# BOOTSTRAP-073 — Axiom String, Unicode, Text, Bytes & Encoding Model

**Trạng thái: FROZEN**

Đây là phần cần khóa khá kỹ vì Axiom có mục tiêu **UTF-8 mặc định**, nhưng đồng thời phải đạt hiệu năng gần với C/C++ trong các workload hệ thống.

Nguyên tắc trung tâm:

> **UTF-8 là representation mặc định của text, nhưng Unicode không được biến mọi thao tác byte thành thao tác Unicode đắt đỏ.**

---

# 1. Ba khái niệm phải tách biệt

Axiom Core/Library phân biệt:

```text
Bytes
Str
String
```

### `Bytes`

Dữ liệu byte tùy ý:

```text
0x00 0xFF ...
```

Không có giả định UTF-8.

### `Str`

Text UTF-8 **borrowed/non-owning**.

### `String`

Text UTF-8 **owned**.

Mô hình:

```text
String
   │
   └── view
         ↓
        Str
```

---

# 2. Không dùng `String` cho binary

Không cho phép coi:

```text
String
```

như:

```text
Bytes
```

chỉ bằng cast.

Ví dụ file PNG:

```axiom
let data: Bytes = file.read_all()?
```

không phải:

```axiom
let data: String = file.read_all()?
```

Nếu muốn diễn giải bytes thành UTF-8:

```text
Bytes
  ↓ validate UTF-8
Str/String
```

phải có operation explicit.

---

# 3. UTF-8 là invariant của `Str` và `String`

Nếu:

```text
Str
String
```

tồn tại trong safe code thì dữ liệu phải là UTF-8 hợp lệ.

Do đó compiler/library có thể giả định:

```text
valid UTF-8
```

mà không cần validate lại ở mỗi Unicode operation.

---

# 4. `Bytes → Str`

Có hai trường hợp.

### Validation

```axiom
let text = bytes.as_str()?
```

Compiler/library kiểm tra UTF-8.

### Trusted conversion

```text
unsafe
```

có thể tạo `Str` từ bytes nếu programmer đảm bảo invariant.

Sau unsafe boundary:

```text
UTF-8 invariant
```

được verifier tiếp tục tin tưởng theo contract.

---

# 5. `String → Bytes`

Không cần copy nếu API chỉ yêu cầu borrowed bytes:

```axiom
let bytes = text.as_bytes()
```

Conceptually:

```text
String
 └── view<u8>
```

Nhưng view này vẫn phải tuân thủ lifetime của String.

---

# 6. UTF-8 không phải Unicode character count

Một string:

```text
UTF-8 bytes
```

không đồng nghĩa:

```text
number of user-visible characters
```

Do đó:

```text
length()
```

nên có semantics rõ.

Khuyến nghị:

```text
byte_length()
scalar_length()
```

và nếu cần:

```text
grapheme_length()
```

Không dùng một `length()` mơ hồ cho cả ba.

---

# 7. `String.len`

Để thuận tiện và hiệu năng, `String`/`Str` nên lưu:

```text
byte length
```

không lưu mặc định:

```text
Unicode scalar count
grapheme count
```

Vì byte length là O(1), còn scalar/grapheme count có thể O(n).

---

# 8. UTF-8 indexing

Không cho:

```axiom
text[i]
```

trả Unicode scalar theo nghĩa O(1).

UTF-8 có độ dài biến đổi.

Thay vào đó:

```text
text.byte_at(i)
text.scalar_at(i)
```

với semantics khác nhau.

---

# 9. Byte access

`Str` có thể cung cấp:

```axiom
text.bytes()
```

hoặc:

```axiom
text.as_bytes()
```

trả borrowed byte view.

Không copy.

Ví dụ:

```text
Str
 ↓
view<u8>
```

---

# 10. Scalar iteration

Unicode scalar iteration:

```axiom
for ch in text.scalars() {
    ...
}
```

trả một scalar value.

Compiler/library có thể optimize UTF-8 decoding rất mạnh.

---

# 11. Unicode scalar ≠ grapheme

Ví dụ một ký tự người dùng nhìn thấy có thể gồm nhiều Unicode scalar.

Vì vậy:

```text
Unicode scalar
```

và:

```text
grapheme cluster
```

là hai tầng khác nhau.

---

# 12. Grapheme

Grapheme segmentation thuộc Unicode library, không phải primitive Core.

API:

```text
text.graphemes()
```

có thể sử dụng Unicode segmentation tables.

Không bắt compiler phải chứa toàn bộ Unicode database.

---

# 13. Unicode normalization

Không tự động normalize mọi String.

Ví dụ:

```text
NFC
NFD
NFKC
NFKD
```

là các transformation explicit.

```axiom
let normalized = text.normalize(NFC)?
```

Không:

```text
String assignment
    ↓
automatic normalization
```

vì sẽ tạo chi phí và thay đổi semantics.

---

# 14. Unicode equality

Mặc định:

```text
String == String
```

là equality của UTF-8 text/value theo semantics của chuỗi.

Không tự động:

```text
NFC normalize
```

trước khi so sánh.

Nếu ứng dụng cần canonical equivalence, phải explicit.

---

# 15. Unicode case conversion

Không biến:

```text
to_lower()
```

thành ASCII-only operation.

Phải phân biệt:

```text
ASCII case conversion
Unicode case conversion
locale-sensitive behavior
```

Ví dụ ASCII có fast path rất rẻ.

Unicode full case mapping là library operation.

---

# 16. ASCII fast path

Đây là optimization rất quan trọng.

Compiler/library có thể nhận biết:

```text
UTF-8 ASCII subset
```

vì ASCII byte luôn có high bit bằng 0.

Các operation như:

```text
search
compare
copy
lowercase ASCII
parse
```

có thể có fast path vectorized.

---

# 17. UTF-8 validation

Validation có thể được SIMD/vectorized.

Conceptually:

```text
Bytes
 ↓
UTF-8 validator
 ↓
Str
```

Compiler không cần biết từng Unicode code point ở semantic Core.

Library có thể dùng:

```text
SIMD
```

đã được thiết kế ở BOOTSTRAP-072.

---

# 18. UTF-8 decoder

Decoder phải reject:

```text
overlong encoding
invalid continuation
surrogate encoding
out-of-range scalar
truncated sequence
```

Không được tạo Unicode scalar invalid trong safe API.

---

# 19. Unicode scalar representation

Một Unicode scalar value có thể được biểu diễn bằng:

```text
u32
```

nhưng không phải mọi `u32` đều là valid Unicode scalar.

Do đó nên có nominal type:

```text
Rune
Char
UnicodeScalar
```

Library type.

Không dùng raw `u32` ở mọi Unicode API.

---

# 20. Invalid scalar

Các code point trong surrogate range:

```text
U+D800..U+DFFF
```

không phải Unicode scalar values.

Safe constructor phải reject.

---

# 21. UTF-8 encoding

`Rune → UTF-8` là deterministic.

API:

```text
r.encode_utf8(...)
```

có thể ghi trực tiếp vào caller-provided buffer.

Không cần allocation.

---

# 22. No hidden String allocation

Các operation read-only như:

```text
starts_with
contains
find
compare
parse
```

không được yêu cầu tạo String tạm.

Zero-allocation là default design goal.

---

# 23. Substring

Đây là điểm quan trọng.

Nếu:

```text
String
```

lưu UTF-8 bytes, substring có thể tạo:

```text
Str
```

không copy:

```text
String
 └──────────────┐
                ▼
              Str
```

nhưng chỉ khi boundary nằm đúng UTF-8 scalar boundary nếu API yêu cầu scalar-safe slicing.

---

# 24. Byte slice và text slice khác nhau

Không được nhầm:

```text
bytes[3..8]
```

với:

```text
text[3..8]
```

Byte slicing có thể tạo arbitrary bytes.

Text slicing phải bảo toàn UTF-8 invariant.

Do đó nên có API riêng.

---

# 25. Text slicing

Ví dụ conceptually:

```axiom
let part = text.slice(start, end)?
```

có thể kiểm tra:

```text
start = UTF-8 boundary
end   = UTF-8 boundary
```

Nếu không:

```text
Result / error
```

Không tạo invalid `Str`.

---

# 26. Zero-copy substring lifetime

Nếu:

```axiom
let part = text.slice(...)?
```

thì:

```text
part
```

không được sống lâu hơn owner.

Verifier đã có capability model nên không cần String-specific lifetime system.

---

# 27. String mutation

`String` là owned mutable resource/storage abstraction.

Ví dụ:

```axiom
var text = String("hello")
text.push(...)
```

Mutation có thể relocate internal buffer.

Nếu:

```text
let v = text.as_str()
```

đang sống, operation có khả năng relocate phải bị chặn.

Đây là chính xác invariant `AVERIFY-47` / `AMEM-24`.

---

# 28. Capacity

`String` có thể có:

```text
length
capacity
```

như `Vec`.

Nhưng:

```text
reserve()
```

không đảm bảo stable address.

Nếu cần stable storage:

```text
StableBox
```

hoặc explicit storage abstraction.

---

# 29. String growth

Compiler/library có thể sử dụng:

```text
geometric growth
small-string optimization
arena
custom allocator
```

nhưng đây là implementation strategy.

Không đưa allocator vào semantics của `String`.

---

# 30. Small String Optimization

Axiom `String` có thể dùng SSO:

```text
String
 ├── inline short text
 └── dynamic storage for longer text
```

Programmer không cần biết.

Nhưng nếu `address_of()` được expose qua unsafe/system API, storage contract trở nên observable.

---

# 31. Empty String

Empty string:

```text
""
```

là valid UTF-8.

Không cần allocation.

Có thể dùng canonical zero-length representation.

---

# 32. String literal

Literal:

```axiom
let s = "Hello"
```

nên mặc định là borrowed immutable text:

```text
Str
```

hoặc compile-time text literal type có thể coerce thành `Str`.

Không tạo heap allocation runtime.

---

# 33. String literal lifetime

Literal có program lifetime:

```text
static storage
```

nên:

```axiom
let s = "hello"
```

có thể tồn tại suốt program.

---

# 34. Raw string

Nên hỗ trợ raw string syntax để giảm escaping:

```text
r"c:\temp\file.txt"
```

hoặc delimiter variant sau này.

Đây là syntax convenience, không thay đổi String semantics.

---

# 35. Multiline strings

Hỗ trợ:

```text
"""..."""
```

là hợp lý.

Nhưng compiler phải định nghĩa rõ:

- newline;
- indentation;
- escape;
- UTF-8.

Không để tooling tự đoán.

---

# 36. Bytes literal

Binary data cần literal riêng:

```text
b"\x00\xFF"
```

hoặc byte-array literal.

Kết quả:

```text
Bytes
```

không phải `String`.

---

# 37. C string

Không dùng `String` trực tiếp làm C string.

C string có:

```text
NUL terminator
```

và có thể không phải UTF-8.

Library wrapper:

```text
CString
CStr
```

được dùng tại FFI.

---

# 38. CStr

`CStr` là borrowed representation:

```text
CStr
```

không sở hữu.

Có thể chứa:

```text
UTF-8 + NUL
```

nếu wrapper contract yêu cầu.

---

# 39. CString

`CString` owned C-compatible string.

Constructor phải kiểm tra embedded NUL nếu API yêu cầu C string thông thường.

```text
String
   ↓
CString::new(...)
   ↓
Result
```

---

# 40. OS string

Không giả định mọi OS dùng UTF-8 internally.

Windows và các API legacy có thể có representation khác.

Do đó system library có thể có:

```text
OsString
OsStr
```

tách khỏi portable `String`.

---

# 41. Path

Không nên coi:

```text
Path = String
```

một cách tuyệt đối.

Nên có:

```text
Path
PathBuf
```

với platform-specific encoding semantics.

Ví dụ:

```text
PathBuf
```

là owned path.

---

# 42. Network protocol

Network packet là:

```text
Bytes
```

không phải String.

Parser explicit:

```text
Bytes
 ↓
parse
 ↓
ProtocolMessage
```

Text field trong protocol mới decode UTF-8 nếu protocol yêu cầu.

---

# 43. Serialization

Memory representation:

```text
String
```

không phải wire representation.

Serialization:

```text
String
 ↓
UTF-8 bytes
 ↓
wire format
```

là explicit.

---

# 44. UTF-16

Không đưa UTF-16 vào core text representation.

Library có:

```text
Utf16
```

hoặc encoding functions.

Đặc biệt useful cho Windows APIs.

---

# 45. UTF-32

Tương tự:

```text
UTF-32
```

là encoding/library concern.

Unicode scalar có thể dùng `u32`-backed representation nhưng không có nghĩa toàn bộ String dùng UTF-32.

---

# 46. Encoding abstraction

Standard library có thể có:

```text
Encoding
Encoder
Decoder
```

nhưng không cần biến mọi String thành generic:

```text
String<UTF8>
```

Đây là một nơi nên **không over-engineer**.

`String` mặc định UTF-8 là đủ.

---

# 47. Parser/decoder streaming

Đối với network/file lớn:

```text
Decoder
```

có thể nhận:

```text
view<u8>
```

từng chunk.

Không yêu cầu toàn bộ input nằm trong một String.

---

# 48. Streaming UTF-8

UTF-8 sequence có thể bị cắt giữa hai chunk.

Decoder phải giữ trạng thái tối thiểu:

```text
partial sequence state
```

qua các lần gọi.

Đây là library state machine, không cần compiler special case.

---

# 49. String iteration performance

Iterator:

```axiom
for c in text.scalars() {
    ...
}
```

phải là zero-cost abstraction mục tiêu.

Compiler có thể inline:

```text
UTF-8 decode loop
```

và vectorize các phần phù hợp.

---

# 50. String search

API:

```text
find
contains
starts_with
ends_with
```

nên làm việc trực tiếp trên UTF-8 bytes khi semantics cho phép.

Ví dụ tìm ASCII substring trong UTF-8 text:

```text
UTF-8 byte search
```

hoàn toàn hợp lệ vì ASCII byte sequence không xuất hiện giả trong continuation bytes theo cách phá boundary.

Nhưng Unicode-aware search phải dùng scalar/grapheme semantics khi cần.

---

# 51. Search semantics

Phải phân biệt:

```text
byte search
Unicode scalar search
grapheme search
locale-aware search
```

Không để `find()` mơ hồ.

Khuyến nghị API tên rõ ràng hoặc overload theo needle type.

---

# 52. Regex

Regex không phải Core.

Community/standard library có thể implement:

```text
Regex
```

trên `Str`/`Bytes`.

Compiler không cần regex engine.

---

# 53. Unicode database

Không nhúng toàn bộ Unicode database vào mọi executable.

Nếu program không dùng Unicode-heavy functionality:

```text
runtime/binary
```

không nên bị kéo theo hàng MB dữ liệu Unicode.

---

# 54. Selective Unicode linking

Dependency graph:

```text
String core
    ↓
UTF-8 primitives
```

rất nhỏ.

Các module như:

```text
unicode::normalize
unicode::grapheme
unicode::case
unicode::collation
```

được link khi dùng.

---

# 55. ASCII-only programs

Một chương trình:

```axiom
print("Hello")
```

không cần:

```text
full Unicode runtime
```

UTF-8 representation vẫn đúng nhưng implementation có thể cực kỳ nhỏ.

---

# 56. Unicode version

Unicode algorithms/data có version.

Build metadata phải ghi:

```text
Unicode data version
```

khi output phụ thuộc vào Unicode tables.

Điều này quan trọng cho reproducible build.

---

# 57. Unicode compatibility

Không đảm bảo mọi Unicode version cho cùng một grapheme/case/normalization result.

Do đó các library algorithms phải ghi rõ Unicode data version.

---

# 58. Compile-time String

Comptime có thể xử lý:

```axiom
const NAME = "Axiom"
```

như compile-time UTF-8 value.

Generated code có thể materialize static bytes.

Không cần runtime allocation.

---

# 59. Compile-time UTF-8 validation

String literal phải được compiler validate.

Do đó:

```text
literal
```

đã là valid UTF-8.

Invalid source encoding là compiler diagnostic.

---

# 60. Identifier Unicode

Axiom source cho phép Unicode identifiers theo syntax baseline.

Nhưng nên phân biệt:

```text
source identifier
```

và:

```text
user-facing text
```

Unicode normalization của identifier phải được specification định nghĩa để tránh hai tên nhìn giống nhau nhưng khác code point gây collision.

---

# 61. Identifier normalization

Khuyến nghị:

> **Không tự động Unicode-normalize identifier spelling.**

Thay vào đó compiler có thể cảnh báo:

```text
visually-confusable identifier
```

ở tooling/lint level.

Semantic identity vẫn dựa trên exact normalized source representation theo lexical specification.

---

# 62. Case-sensitive identifiers

Axiom giữ:

```text
foo != Foo
```

Không case-fold identifier.

Đây là cách đơn giản nhất cho compiler và AI tooling.

---

# 63. String equality performance

`String == String` có thể:

```text
length compare
↓
byte compare
```

và compiler/library có thể SIMD optimize.

Không cần decode Unicode nếu semantics là exact UTF-8 string equality.

---

# 64. Hashing

Hash của `String` dựa trên UTF-8 bytes.

Điều này cho:

```text
deterministic representation
fast hashing
no Unicode decode
```

Nhưng hash algorithm cụ thể có thể thay đổi theo library/version nếu API không cam kết stable hash.

Nếu cần stable wire hash, phải dùng explicit algorithm.

---

# 65. Security-sensitive Unicode

Một số thao tác như:

```text
case folding
normalization
confusable detection
```

có security implications.

Không tự động áp dụng vào parser/URL/path.

Application library quyết định policy.

---

# 66. Text vs user-visible text

Axiom không giả định:

```text
Unicode scalar = character
```

hoặc:

```text
String = user-visible text
```

`String` chỉ đảm bảo Unicode text representation.

UI libraries chịu trách nhiệm grapheme/rendering.

---

# 67. Text rendering

Font shaping:

```text
OpenType
HarfBuzz-like functionality
glyph shaping
BiDi
```

không thuộc Core.

System/application libraries.

---

# 68. Bidirectional text

Unicode BiDi là library functionality.

Compiler không cần biết.

---

# 69. Locale

Không có global implicit locale trong Core.

Operations như:

```text
lowercase
sort
format
```

nếu locale-sensitive phải nhận locale/context explicit.

Điều này tránh global mutable state và concurrency problems.

---

# 70. Formatting

Một hệ thống format có thể xây trên traits:

```text
Display
Debug
Format
```

nhưng đây là library.

Compiler chỉ hỗ trợ:

```text
comptime formatting generation
```

nếu sau này cần tối ưu.

---

# 71. String formatting allocation

Formatter có thể hỗ trợ:

```text
write_to(mut_view<Buffer>)
```

để tránh allocation.

Ví dụ:

```text
format_into(buffer, value)
```

là preferred low-level path.

---

# 72. `String` ownership model

`String`:

```text
Owned
!Copy
Drop
```

Copy toàn bộ text phải explicit:

```text
string.clone()
```

---

# 73. `Str` capability model

`Str` về semantic level là:

```text
read-only text view
```

Nó có thể được xem như specialized library representation dựa trên Core capability model.

Không cần thêm lifetime syntax.

---

# 74. Mutable text view

Không nên có:

```text
mut_Str
```

trong Core.

Mutation UTF-8 rất dễ phá invariant.

Thay vào đó:

```text
mut_view<u8>
```

chỉ ở low-level APIs, hoặc `String` mutation APIs tự đảm bảo UTF-8.

---

# 75. Unsafe UTF-8 mutation

System programmer có thể sửa raw bytes:

```text
String
 ↓
unsafe bytes access
 ↓
mut_view<u8>
```

Sau đó programmer phải re-establish:

```text
valid UTF-8
```

trước khi safe code sử dụng String như text.

Không để unsafe mutation âm thầm phá invariant.

---

# 76. UTF-8 invariant recovery

Conceptually:

```text
mutate bytes
      ↓
validate
      ↓
Str/String
```

hoặc unsafe trusted contract.

Đây là cùng pattern:

```text
raw pointer
 ↓
unsafe
 ↓
safe capability
```

đã freeze ở memory model.

---

# 77. String FFI

Portable:

```text
String
```

không tự động FFI-safe.

C ABI:

```text
CString
CStr
```

System ABI:

```text
OsString
```

Foreign UTF-16:

```text
Utf16 buffer
```

Mỗi boundary explicit.

---

# 78. ABI representation

Default String representation không stable.

Compiler có thể thay đổi:

```text
pointer
length
capacity
inline representation
```

miễn semantic/ABI contract không yêu cầu.

`String` không tự động `@repr(C)`.

---

# 79. FFI-compatible text

Nếu cần C-compatible:

```text
@repr(C)
struct CStringView {
    ptr: *const u8
    len: usize
}
```

là một explicit boundary type.

Không biến `Str` thành C ABI chỉ vì nó có vẻ giống pointer+length.

---

# 80. Text and ownership across FFI

Foreign function nhận:

```text
CStringView
```

không tự có quyền free memory.

Ownership contract phải nói rõ:

```text
borrowed
owned
caller-owned
callee-owned
```

đúng theo BOOTSTRAP-041.

---

# 81. String interning

Không phải Core semantic.

Compiler có thể intern:

```text
compile-time literals
identifiers
```

nhưng runtime `String` không mặc định intern.

Application có thể dùng:

```text
InternPool
Symbol
Atom
```

---

# 82. String interning + logical identity

Nếu application cần:

```text
Symbol
```

thì đây là logical identity abstraction.

Không được coi:

```text
pointer equality
```

là String equality.

---

# 83. No hidden reference counting

`String` không tự động dùng:

```text
Rc
Arc
```

để share storage.

Nếu cần sharing:

```text
Arc<str>
```

hoặc library abstraction tương tự.

---

# 84. Immutable shared strings

Có thể có:

```text
Arc<Str>
```

hoặc:

```text
SharedString
```

cho nhiều thread.

Ownership/concurrency semantics do `Arc`/library đảm nhận.

---

# 85. Mutable shared String

Không có:

```text
Arc<String>
```

rồi mặc định cho nhiều thread mutation.

Phải:

```text
Arc<Mutex<String>>
```

hoặc một concurrent string abstraction cụ thể.

---

# 86. Path and String

Không implicit convert:

```text
Path ↔ String
```

nếu platform representation không tương thích.

Các conversion có thể trả:

```text
Result
```

hoặc explicit lossy conversion.

---

# 87. Lossy conversion

Ví dụ foreign bytes → text:

```text
decode_lossy()
```

phải nói rõ rằng invalid sequences được thay thế.

Không để:

```text
decode()
```

âm thầm thay thế invalid data.

---

# 88. Encoding errors

Normal decoder:

```text
decode(...) -> Result<String, EncodingError>
```

Lossy decoder:

```text
decode_lossy(...) -> String
```

Hai semantics tách biệt.

---

# 89. Performance target

Axiom text stack phải đạt:

```text
ASCII:
    near raw byte processing

UTF-8:
    no mandatory heap allocation

read-only:
    zero-copy where possible

Unicode-heavy:
    optimized library implementation

FFI:
    explicit and predictable
```

---

# 90. Không biến Unicode thành compiler runtime

Compiler chỉ cần hiểu:

```text
UTF-8 source
Unicode identifiers
String literal encoding
```

Không cần embed:

```text
Unicode normalization engine
grapheme database
locale database
font shaping
```

vào compiler executable/runtime application.

---

# 91. Layering

Final architecture:

```text
                 Axiom Core
                     │
              UTF-8 invariants
                     │
              Core Library
          ┌──────────┼──────────┐
          │          │          │
        Bytes       Str       String
          │          │          │
          └──────────┼──────────┘
                     │
             Unicode Library
       ┌─────────────┼─────────────┐
       │             │             │
   Grapheme       Normalize       Case
       │             │             │
       └─────────────┼─────────────┘
                     │
             System/Application
        Path / Locale / UI / Font / FFI
```

---

# 92. Một quyết định rất quan trọng

Axiom **không nên có `char` primitive theo nghĩa C/C++**.

Thay vào đó:

```text
u8
Rune / UnicodeScalar
Str
String
```

có semantics khác nhau.

Điều này loại bỏ rất nhiều nhầm lẫn giữa:

```text
byte
code point
character
text
```

---

# 93. API model đề xuất

Các primitive/library operation quan trọng:

```text
Bytes
    len()
    get()
    slice()
    as_str()
    ...

Str
    byte_len()
    scalar_len()
    bytes()
    scalars()
    graphemes()
    slice()
    find()
    contains()
    ...

String
    new()
    push()
    push_str()
    reserve()
    clear()
    as_str()
    as_bytes()
    clone()
    ...
```

Tên chính xác có thể chỉnh trong Standard Library API audit sau này.

---

# 94. Ví dụ idiomatic

```axiom
fn greet(name: Str) -> String {
    var result = String("Hello, ")
    result.push_str(name)
    result.push('!')
    return result
}
```

Semantics:

```text
name
  ↓
borrowed text capability

result
  ↓
owned mutable String

return
  ↓
Move String
```

Không GC.

Không lifetime syntax.

Không hidden allocation ngoài những gì `String` thực sự cần.

---

# 95. Ví dụ zero-copy parser

```axiom
fn parse_header(data: view<u8>) -> Result<Header, ParseError> {
    ...
}
```

Nếu header chứa text:

```text
view<u8>
    ↓ validate UTF-8
Str
    ↓
Header
```

Không cần tạo String.

---

# 96. Ví dụ network

```axiom
let packet = socket.read_all()?
let message = Message.parse(packet)?
```

`packet` là `Bytes`.

Parser quyết định field nào là:

```text
u32
bytes
Str
```

không có implicit decoding.

---

# 97. Ví dụ FFI

```axiom
extern "C" fn api_name(name: *const u8) -> i32
```

ở boundary raw pointer.

Wrapper safe:

```text
CStr
 ↓
validated UTF-8
 ↓
Str
```

nếu API contract yêu cầu UTF-8.

---

# 98. Compiler optimization

Compiler được phép:

```text
inline UTF-8 decoder
remove redundant validation
vectorize ASCII scan
SIMD UTF-8 validation
eliminate temporary String
scalarize String metadata
```

nhưng chỉ khi semantics được bảo toàn.

---

# 99. Runtime footprint

Một chương trình chỉ sử dụng:

```text
Bytes
Str
String
```

không nên tự động link:

```text
full Unicode database
locale
grapheme engine
regex
font engine
```

Dependency graph quyết định.

---

# 100. Frozen Invariants — `ATEXT-20..100`

### Representation

- **ATEXT-20** `Bytes` represents arbitrary byte data.
- **ATEXT-21** `Str` represents borrowed valid UTF-8 text.
- **ATEXT-22** `String` represents owned valid UTF-8 text.
- **ATEXT-23** Binary data is not implicitly text.
- **ATEXT-24** UTF-8 validity is an invariant of safe `Str` and `String`.
- **ATEXT-25** UTF-8 representation is distinct from Unicode scalar semantics.
- **ATEXT-26** Unicode scalar semantics are distinct from grapheme semantics.
- **ATEXT-27** Text representation is distinct from wire/serialization representation.
- **ATEXT-28** Default String representation is not a stable ABI contract.
- **ATEXT-29** String does not require a GC header or runtime object header.
- **ATEXT-30** String does not require reference counting.

### Ownership / capability

- **ATEXT-31** `String` is normally non-Copy and owns its storage.
- **ATEXT-32** `Str` is non-owning.
- **ATEXT-33** `Str` cannot outlive its source storage.
- **ATEXT-34** String mutation cannot invalidate live safe text capabilities.
- **ATEXT-35** String relocation is blocked while dependent capabilities require stable storage.
- **ATEXT-36** String growth does not imply stable address.
- **ATEXT-37** String duplication is explicit.
- **ATEXT-38** Shared String storage requires explicit shared ownership.
- **ATEXT-39** Shared mutable String requires explicit synchronization.

### UTF-8

- **ATEXT-40** UTF-8 decoding rejects invalid sequences in checked APIs.
- **ATEXT-41** Overlong UTF-8 encodings are invalid.
- **ATEXT-42** UTF-8 encoded surrogate values are invalid.
- **ATEXT-43** Out-of-range Unicode scalar values are invalid.
- **ATEXT-44** Truncated UTF-8 sequences are invalid.
- **ATEXT-45** Valid UTF-8 can be represented as `Str` without copying.
- **ATEXT-46** Bytes-to-Str conversion is explicit.
- **ATEXT-47** Trusted UTF-8 construction requires an explicit unsafe boundary.
- **ATEXT-48** Safe verification resumes after valid UTF-8 invariant establishment.
- **ATEXT-49** Lossy decoding is distinct from checked decoding.
- **ATEXT-50** UTF-8 validation may be vectorized.

### Indexing / slicing

- **ATEXT-51** Byte length is O(1) for ordinary String/Str representations.
- **ATEXT-52** Unicode scalar count is not required to be O(1).
- **ATEXT-53** Grapheme count is not required to be O(1).
- **ATEXT-54** Byte indexing is distinct from scalar indexing.
- **ATEXT-55** UTF-8 text slicing must preserve UTF-8 validity.
- **ATEXT-56** Arbitrary byte slicing does not automatically produce valid text.
- **ATEXT-57** Zero-copy text slicing is permitted.
- **ATEXT-58** Text slice lifetime follows source storage lifetime.
- **ATEXT-59** Scalar iteration may be zero-allocation.
- **ATEXT-60** Grapheme iteration is a Unicode library operation.

### Unicode

- **ATEXT-61** Unicode normalization is explicit.
- **ATEXT-62** String operations do not implicitly normalize text.
- **ATEXT-63** Unicode case mapping is explicit.
- **ATEXT-64** Locale-sensitive behavior is explicit.
- **ATEXT-65** Unicode scalar values are distinct from arbitrary `u32`.
- **ATEXT-66** Unicode grapheme clusters are distinct from Unicode scalars.
- **ATEXT-67** BiDi processing is not a Core primitive.
- **ATEXT-68** Font shaping is not a Core primitive.
- **ATEXT-69** Full Unicode databases are not mandatory runtime components.
- **ATEXT-70** Unicode library data is selectively linked when required.

### Performance

- **ATEXT-71** ASCII processing may use specialized fast paths.
- **ATEXT-72** String equality may operate directly on UTF-8 bytes.
- **ATEXT-73** String search may operate directly on UTF-8 bytes where semantics permit.
- **ATEXT-74** String APIs do not imply allocation unless required by semantics.
- **ATEXT-75** Formatting APIs may support caller-provided buffers.
- **ATEXT-76** UTF-8 decoding may be SIMD optimized.
- **ATEXT-77** String temporary allocations may be eliminated when unobservable.
- **ATEXT-78** String metadata may be scalarized or register allocated.
- **ATEXT-79** SSO is an implementation strategy, not semantic behavior.
- **ATEXT-80** Allocator strategy is not part of ordinary String type semantics.

### FFI / platform

- **ATEXT-81** `String` is not automatically C-ABI compatible.
- **ATEXT-82** `CStr` and `CString` are explicit FFI abstractions.
- **ATEXT-83** Embedded NUL semantics are explicit for C strings.
- **ATEXT-84** `OsStr`/`OsString` may represent platform-native text semantics.
- **ATEXT-85** `Path` is distinct from ordinary `String`.
- **ATEXT-86** UTF-16 is an encoding/library concern.
- **ATEXT-87** UTF-32 is an encoding/library concern.
- **ATEXT-88** Foreign ownership of text buffers is explicit.
- **ATEXT-89** Foreign allocation domains are never guessed.
- **ATEXT-90** Raw text pointers at FFI boundaries are unsafe/system-level values.

### Comptime / compiler

- **ATEXT-91** String literals are compile-time UTF-8 values.
- **ATEXT-92** String literals require valid source encoding.
- **ATEXT-93** Compile-time text may materialize static runtime storage without heap allocation.
- **ATEXT-94** Unicode-dependent compile-time results participate in build identity where relevant.
- **ATEXT-95** Compiler Unicode support is distinct from application Unicode runtime support.
- **ATEXT-96** Identifier Unicode semantics are distinct from text normalization semantics.
- **ATEXT-97** Identifier case sensitivity is deterministic.
- **ATEXT-98** Unicode optimization cannot change text semantics.
- **ATEXT-99** Text semantics are preserved across MIR, ABI, FFI and serialization boundaries.
- **ATEXT-100** UTF-8 is the default Axiom text representation without making Unicode-heavy runtime functionality mandatory.

---

## Một điểm tôi muốn giữ rất chắc ở đây

Axiom **không nên đi theo hướng**:

```text
String
  ↓
Unicode object
  ↓
Character objects
  ↓
GC
```

mà nên là:

```text
String
 ├── pointer/storage
 ├── byte length
 └── capacity
       │
       ▼
     UTF-8 bytes
       │
       ├── byte view
       ├── scalar iterator
       └── grapheme iterator
```

Tức là **representation vẫn cực kỳ gần với C**, nhưng semantic safety cao hơn:

```text
C:
char* + length
     ↓
programmer tự chịu trách nhiệm

Axiom:
String/Str
     ↓
UTF-8 invariant
     ↓
compiler verifies lifetime/capability
```

Đây chính xác là triết lý Axiom mà chúng ta đã xây từ đầu:

> **Không làm ngôn ngữ phức tạp hơn chỉ để compiler dễ viết; hãy để compiler gánh phần phức tạp mà programmer không cần nhìn thấy.**

---

### Bước tiếp theo: `BOOTSTRAP-074`

Phần tiếp theo hợp lý nhất là **Axiom Collections & Iterator Model**.

Nó sẽ khóa kiến trúc cho:

```text
Array
Vec
Slice/View
String
HashMap
HashSet
Deque
Queue
Stack
BTree
Iterator
IntoIterator
Lazy iterator
Parallel iterator
Collection ownership
Mutation
Relocation
Small-vector
Arena-backed collection
```

Đặc biệt sẽ phải giải quyết một vấn đề chúng ta đã chạm tới trước đó:

> **`view<T>` chính xác đại diện cho collection/slice như thế nào, nested/multidimensional data ra sao, và làm thế nào để `Vec<T>`, Array, String, Tensor và GPU buffer dùng chung capability model mà không phải tạo ra 5 loại reference khác nhau.**