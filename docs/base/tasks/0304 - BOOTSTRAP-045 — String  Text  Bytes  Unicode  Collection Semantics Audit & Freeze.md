Tiếp tục.

# BOOTSTRAP-045 — String / Text / Bytes / Unicode / Collection Semantics Audit & Freeze

Đây là phần tưởng nhỏ nhưng thực tế ảnh hưởng trực tiếp đến **hiệu năng, ABI, UTF-8, FFI, slicing, iterator, ownership và AI-generated code**.

Tôi đề xuất Axiom **không dùng một kiểu “string” duy nhất cho mọi tình huống**.

Mô hình nên là:

```text id="0d5e8a"
Bytes        → raw binary
ByteView     → borrowed binary
str          → borrowed UTF-8 text
String       → owned UTF-8 text
CStr        → foreign NUL-terminated text
CString     → owned foreign C text
```

---

# 1. Ba loại dữ liệu nền tảng

Axiom phải phân biệt rõ:

```text id="b9l2s7"
BYTE DATA
TEXT
FOREIGN TEXT
```

Không có implicit conversion giữa chúng.

---

# 2. `u8` là byte

```axiom
let b: u8 = 255
```

`u8` biểu diễn một byte/octet.

Không có ý nghĩa Unicode mặc định.

---

# 3. `view<u8>` là byte view

Ví dụ:

```axiom
fn checksum(data: view<u8>) -> u32
```

Đây là abstraction chính cho:

- binary;
- packet;
- file data;
- memory buffer;
- serialization.

---

# 4. `mut_view<u8>`

```axiom
fn fill(data: mut_view<u8>, value: u8)
```

là exclusive mutable access.

Không copy dữ liệu.

---

# 5. `Bytes`

Tôi đề xuất `Bytes` là owned byte sequence.

Semantic:

```text id="q3a1l2"
owned
growable
binary-safe
```

Có thể dùng:

```axiom
let data = Bytes()
```

---

# 6. `ByteView`

Không nhất thiết cần một primitive type mới.

Alias/library abstraction:

```text id="h9p8r1"
ByteView = view<u8>
```

và:

```text id="5k0s0e"
MutByteView = mut_view<u8>
```

Như vậy Core không phình thêm.

---

# 7. UTF-8 là semantic invariant của `str`

`str` phải luôn chứa:

> **valid UTF-8 sequence.**

Không tồn tại safe `str` chứa malformed UTF-8.

---

# 8. `String`

`String` là:

```text id="b5t1zx"
owned + valid UTF-8
```

Không phải:

```text id="j8q8kl"
char*
```

và không phải C string.

---

# 9. String literal

Literal:

```axiom
let s = "Xin chào"
```

là UTF-8 text literal.

Compiler biết encoding.

---

# 10. Byte literal

Dùng:

```axiom
let b = b"ABC"
```

để tạo raw bytes.

Không có Unicode validity requirement.

---

# 11. C string

FFI dùng syntax riêng, ví dụ:

```text id="m1d8s3"
c"..."
```

hoặc library constructor.

Nhưng semantic phải là:

```text id="z2q9nk"
NUL-terminated foreign string
```

không phải Axiom `String`.

---

# 12. NUL trong String

Axiom `String` **có thể chứa U+0000**.

Ví dụ:

```text id="r8e5wx"
"A\0B"
```

hoàn toàn hợp lệ.

Do đó không thể tự động convert sang C string.

---

# 13. `String.len()`

`len()` phải trả:

> **số byte UTF-8**

Không phải số Unicode scalar.

Ví dụ:

```text id="7yqjkc"
ASCII text      → 1 byte/char
Vietnamese      → có thể nhiều byte
```

Điều này phù hợp với memory/performance model.

---

# 14. `bytes()`

```axiom
s.bytes()
```

trả iterator/view trên UTF-8 bytes.

Không allocation.

---

# 15. `chars()`

```axiom
s.chars()
```

iterate Unicode scalar values.

Không nhất thiết allocation.

---

# 16. `char`

`char` = Unicode scalar value.

Không phải:

```text id="1y5u2k"
UTF-8 byte
grapheme
glyph
```

---

# 17. Grapheme

Một ký tự người dùng nhìn thấy có thể gồm nhiều Unicode scalar values.

Ví dụ:

```text id="uw2d0c"
e + combining accent
```

Do đó:

```text id="k6v8ea"
chars()
```

không đồng nghĩa:

```text
user_visible_characters()
```

---

# 18. Grapheme segmentation

Thuộc Unicode library:

```text id="y1n2w0"
Unicode.Grapheme
```

Không thuộc Core.

---

# 19. Unicode normalization

Không tự động normalize String.

Ví dụ:

```text id="6qz2pd"
NFC
NFD
NFKC
NFKD
```

là explicit operations.

---

# 20. Không implicit normalization

Nếu compiler tự normalize runtime strings sẽ:

- tốn CPU;
- thay đổi byte representation;
- gây bất ngờ;
- ảnh hưởng hashing/equality.

Axiom không làm vậy.

---

# 21. String equality

Mặc định:

> equality dựa trên semantic Unicode string representation hiện có, không tự động normalization.

Nói cách khác, hai chuỗi có encoding sequence khác nhau không tự động bằng nhau chỉ vì có thể normalize thành cùng text.

---

# 22. String hashing

Hash mặc định dựa trên byte representation/defined text representation.

Normalization phải explicit trước khi hash nếu ứng dụng yêu cầu canonical equivalence.

---

# 23. UTF-8 slicing

Không được cắt `String` tùy ý theo byte rồi tạo `str` nếu boundary nằm giữa UTF-8 sequence.

Ví dụ semantic:

```text id="q9o4g8"
s[byte_range]
```

phải:

- kiểm tra boundary;
- hoặc trả `Result`;
- hoặc dùng API scalar/grapheme-aware.

---

# 24. Không panic mặc định khi slicing runtime

Tôi đề xuất API:

```text id="k1b6yw"
s.slice(range) -> Result<str, StringError>
```

cho dynamic range.

---

# 25. Checked indexing

```text id="9c5c7j"
s[i]
```

nên chỉ được phép nếu compiler chứng minh index hợp lệ và boundary phù hợp.

Nếu không:

```text
panic/trap
```

theo indexing contract.

---

# 26. Unchecked slicing

Có thể có:

```text id="6n7v2h"
unsafe fn slice_unchecked(...)
```

nhưng caller chịu trách nhiệm:

- bounds;
- UTF-8 boundaries.

---

# 27. String mutation

String là owned value.

Có thể:

```axiom
var s = String("abc")
s.push(...)
```

Compiler quản lý exclusive mutation.

---

# 28. `String` không phải fixed capacity

Có thể grow.

Representation không được public.

---

# 29. Small String Optimization

SSO được phép.

Ví dụ implementation có thể lưu short strings inline.

Nhưng:

> **SSO không phải semantic contract.**

---

# 30. String relocation

String storage có thể relocate khi grow.

Live `view` phụ thuộc vào String sẽ ngăn relocation không an toàn.

Điều này kế thừa:

```text
AMEM-24
AMEM-71
```

---

# 31. `String.reserve()`

`reserve(n)` chỉ đảm bảo capacity theo contract.

Không được biến thành:

> permanent stable address.

Muốn stable address phải dùng storage abstraction phù hợp.

---

# 32. `String` → `str`

Có thể tạo borrowed view:

```axiom
let text: str = view(s)
```

hoặc compiler có thể cho ephemeral conversion khi function yêu cầu `view<str>` theo implicit owner→view rule.

---

# 33. Không implicit escaping

Ví dụ:

```axiom
fn bad() -> str {
    let s = String("hello")
    return view(s)
}
```

phải bị compiler reject.

---

# 34. Return text

Nếu muốn trả owned:

```axiom
fn make() -> String
```

Không allocation bắt buộc ngoài semantic dynamic-storage contract của `String`.

---

# 35. String literals

Literal có thể được compiler đặt vào read-only static storage.

Không allocation runtime.

---

# 36. Static string view

Ví dụ:

```text id="u1y0h8"
const greeting = "Hello"
```

có thể reference static storage.

---

# 37. String concatenation

Không nên tạo semantics kiểu:

```text
a + b
```

= bắt buộc một allocation nào đó.

Compiler/library có thể optimize.

---

# 38. Formatting

Ví dụ:

```text id="4z8h2a"
format("x = {}", x)
```

là library functionality.

Compiler có thể optimize format string tại compile time.

---

# 39. Compile-time formatting

Vì Axiom có `comptime`, format string có thể được parse tại compile time.

Ví dụ conceptually:

```text
format! / comptime formatting
```

không cần procedural macro.

---

# 40. No macro requirement

Formatting không cần một macro language riêng.

Typed comptime generation là hướng ưu tiên.

---

# 41. String conversion

Không tự động:

```text id="4p2m7k"
i32 → String
```

trong mọi context.

Dùng explicit formatting/conversion trait.

---

# 42. `Display` / `Debug`

Có thể dùng traits:

```text id="z4n9w3"
Display
Debug
```

Standard Library.

---

# 43. Bytes ↔ String

Bytes → String:

```text id="m9e0c2"
String::from_utf8(bytes)
```

trả:

```text
Result<String, Utf8Error>
```

---

# 44. Không unchecked conversion safe

Không được:

```text id="2s6h0f"
Bytes → String
```

mà không validate UTF-8.

---

# 45. Unsafe UTF-8 construction

System API có thể:

```text id="q8c2y7"
from_utf8_unchecked(...)
```

nếu caller đảm bảo invariant.

---

# 46. UTF-8 invariant sau unsafe

Quan trọng:

Unsafe boundary tạo `String`/`str` thì sau boundary compiler lại xem object là:

```text id="r8a7k4"
VALID UTF-8
```

nếu API contract nói như vậy.

---

# 47. `String` FFI

Không tự động pass:

```text
String
```

qua C ABI.

Phải explicit:

```text id="6m7x0a"
CStr
CString
```

hoặc pointer + length ABI.

---

# 48. C string ownership

Phải xác định:

```text id="s8z5t4"
Borrowed
OwnedByAxiom
OwnedByForeign
```

theo FFI ownership rules.

---

# 49. `CStr`

`CStr` là borrowed foreign string.

Invariant:

```text id="m6q3py"
valid address
NUL termination
foreign ABI contract
```

Không nhất thiết valid UTF-8.

---

# 50. `CString`

Owned C-compatible string.

Có thể enforce:

> không chứa interior NUL nếu API yêu cầu C-string semantics.

---

# 51. OS strings

Không phải mọi OS đều nên ép UTF-8.

Axiom cần abstraction:

```text id="5e6y8p"
OsString
OsStr
```

cho platform-native filenames/environment/process arguments.

---

# 52. Linux/Unix

UTF-8 convention phổ biến nhưng OS-level path thực chất byte sequence.

Không nên giả định mọi filename là valid Unicode.

---

# 53. Windows

Windows APIs có native UTF-16 interfaces.

Standard Library có thể chuyển đổi ở boundary.

---

# 54. `Path`

`Path` không nên chỉ là `String`.

Nó phải giữ platform semantics.

```text id="r2w5wq"
Path
PathBuf
```

---

# 55. `PathBuf`

Owned path.

Có thể dùng platform-native representation.

---

# 56. Collections

Bây giờ đến collection semantics.

Core collection protocol nên xoay quanh:

```text id="z2g7m4"
Iterator
IntoIterator
```

và views.

---

# 57. `Vec<T>`

Semantic:

```text id="j7a2p0"
owned
ordered
contiguous
variable length
```

---

# 58. `Vec` indexing

```axiom
v[i]
```

bounds-checked safe.

Compiler có thể eliminate check.

---

# 59. `Vec.get()`

API an toàn explicit:

```text id="q0e4q9"
v.get(i) -> Option<view<T>>
```

hoặc tương ứng với value/reference semantics của API.

---

# 60. `Vec.push`

```text id="n5z3l1"
push(T)
```

moves value vào vector.

Không copy nếu T không Copy.

---

# 61. `Vec.pop`

```text id="7u1j2s"
pop() -> Option<T>
```

ownership trả lại caller.

---

# 62. `Vec` relocation

`push` có thể relocate storage.

Nếu có live:

```text id="m5f9xq"
view(v)
```

thì operation có thể bị reject nếu relocation có thể invalidate view.

---

# 63. `reserve`

Có thể chuẩn bị capacity.

Nhưng:

```text id="b7k4w8"
reserve(n)
```

không tạo stable-address guarantee.

---

# 64. `Vec.as_view`

```text id="4z9j6m"
v.as_view()
```

→ `view<T>`.

---

# 65. `Vec.as_mut_view`

```text id="6c8x3n"
v.as_mut_view()
```

→ `mut_view<T>`.

Compiler enforce exclusivity.

---

# 66. Collection iteration

```axiom
for x in v {
    ...
}
```

ownership semantics phải rõ:

```text id="m4q8o0"
consume v
```

nếu iterator consumes collection.

---

# 67. Borrowed iteration

Có thể:

```text id="v3n8r2"
for x in view(v) { ... }
```

để read.

---

# 68. Mutable iteration

```text id="h9p0w5"
for x in mut_view(v) { ... }
```

để mutate.

Compiler đảm bảo mỗi iteration capability hợp lệ.

---

# 69. No iterator boxing

Iterator chain:

```text id="n4x6p2"
v.iter()
  .map(...)
  .filter(...)
  .take(...)
```

không yêu cầu heap hoặc dynamic dispatch.

---

# 70. Iterator object representation

Mỗi adapter là compiler-generated/generic struct.

Optimizer có thể inline toàn bộ chain.

---

# 71. HashMap

`HashMap<K,V>` là library.

Không phải Core.

---

# 72. HashMap semantics

Phải xác định:

- ownership;
- key equality;
- hashing;
- mutation;
- iteration ordering.

Default iteration ordering **không được coi là stable** trừ khi API contract nói rõ.

---

# 73. Hash function

Không nhất thiết dùng một hash algorithm cố định toàn hệ thống.

Có thể có:

```text id="w8m3j2"
DefaultHasher
SipHash
FastHasher
StableHasher
```

tùy use case.

---

# 74. Deterministic hashing

Compiler/build tooling có thể yêu cầu stable hash.

Runtime HashMap không nhất thiết deterministic giữa process nếu randomized hashing được sử dụng.

---

# 75. BTreeMap

Library.

Useful khi cần:

```text id="y8k3v4"
ordered iteration
range queries
```

---

# 76. Set

`HashSet<T>` / `BTreeSet<T>` là wrappers/library types.

Không cần language primitive.

---

# 77. Deque

`Deque<T>` có thể là ring-buffer based.

Không expose representation.

---

# 78. Linked list

Không nên đưa vào Core.

Nếu ecosystem thực sự cần:

```text id="c9q2a5"
LinkedList
IntrusiveList
```

là library.

---

# 79. Intrusive collections

Rất phù hợp systems programming.

Có thể dùng explicit storage identity/unsafe.

Không cần language feature mới.

---

# 80. Collection allocation

Collection APIs phải công khai semantic:

```text id="p4y7d1"
may_allocate
may_reallocate
may_relocate
```

khi relevant.

Không được giấu những behavior quan trọng này.

---

# 81. Stable-address collections

Nếu cần:

```text id="s3x8v6"
Pool
Slab
Arena
```

thay vì ép `Vec` thành stable storage.

---

# 82. `Vec` không phải entity store

Đây là điểm rất hợp với memory model trước.

Nếu application cần stable identity:

```text id="a7n5c4"
Handle<T>
GenerationHandle<T>
```

thay vì lưu raw pointer.

---

# 83. Zero-sized types

Collections phải hỗ trợ ZST.

Ví dụ:

```text id="e4q2h9"
Vec<Unit>
```

không được yêu cầu physical byte cho từng element.

---

# 84. Alignment

Collections phải tôn trọng `align_of<T>`.

Allocator/backend chịu trách nhiệm storage alignment.

---

# 85. Panic trong collection

Out-of-bounds indexing có thể panic.

Nhưng API `get` trả `Option`.

Đây là pattern thống nhất:

```text id="z9u1p4"
convenient indexing → panic on invalid
explicit checked API → Result/Option
unsafe API → caller responsibility
```

---

# 86. String indexing

Không nên cho phép semantics kiểu:

```axiom
s[i] -> char
```

vì ambiguity byte/scalar/grapheme.

Thay vào đó:

```text id="n2w6x8"
byte_at()
char_at()
graphemes()
```

hoặc iterator.

---

# 87. Collection indexing protocol

Có thể có trait:

```text id="g5m2k7"
Index
IndexMut
```

nhưng semantic của bounds/panic vẫn được chuẩn hóa.

---

# 88. Generic collection algorithms

Các thuật toán:

```text id="k3p9q1"
sort
search
partition
reverse
copy
fill
```

hoạt động trên `view`/iterator khi có thể.

Không yêu cầu collection cụ thể.

---

# 89. Memory copy

Low-level APIs:

```text id="p1q8v5"
copy
copy_nonoverlap
move
fill
```

compiler intrinsic/library.

---

# 90. Alias semantics của copy

`copy_nonoverlap` chỉ safe nếu capability/region verifier chứng minh không overlap.

Nếu không:

```text id="t6w4n3"
unsafe
```

hoặc API khác.

---

# 91. Serialization

Serialization nên operate trên:

```text id="u7r0e5"
view<u8>
mut_view<u8>
```

và typed values.

Không cần compiler serialization magic.

---

# 92. Binary parser

Parser APIs có thể giữ:

```text id="m5j7k2"
ByteView
offset
Result
```

để tránh allocation.

---

# 93. Text parser

Text parser:

```text id="q8v3n1"
view<str>
```

hoặc `str`.

---

# 94. Streaming

String/Bytes APIs nên hỗ trợ streaming:

```text id="e2r6y9"
read chunk
process
reuse buffer
```

không bắt buộc load toàn bộ file vào memory.

---

# 95. Long-running server

Điều này quan trọng cho mục tiêu systems:

```text id="j6p4w8"
read → process → reuse buffer
```

tránh allocation mỗi request.

---

# 96. UTF-8 validation cost

Validation chỉ bắt buộc khi tạo safe `String/str` từ untrusted bytes.

Sau khi invariant được established:

```text id="f8k2m5"
String operations
```

không cần revalidate mọi lần.

---

# 97. Compiler optimization

Compiler có thể biết:

```text id="q2m7v6"
literal is valid UTF-8
```

nên literal construction không cần runtime validation.

---

# 98. Constant folding

Ví dụ:

```text id="w4n8k0"
"abc".len()
```

có thể tính compile time.

---

# 99. Unicode tables

Unicode tables không nên hard-code toàn bộ compiler nếu không cần.

Standard Unicode library có versioned data.

---

# 100. Freeze model

Từ đây semantic model là:

```text id="n8s4x2"
u8
 │
 ├── view<u8> ─────── ByteView
 │
 └── Bytes

UTF-8
 │
 ├── str
 │
 └── String

Foreign text
 │
 ├── CStr / CString
 └── OsStr / OsString

Collections
 │
 ├── Vec
 ├── Deque
 ├── HashMap
 ├── HashSet
 ├── BTreeMap
 └── BTreeSet
```

---

# BOOTSTRAP-045 — Invariants

```text id="w8s2c4"
ATEXT-20   u8 represents raw byte data, not Unicode text.
ATEXT-21   view<u8> represents borrowed byte data.
ATEXT-22   mut_view<u8> represents exclusive mutable byte access.
ATEXT-23   Bytes represents owned binary data.
ATEXT-24   str represents valid UTF-8 borrowed text.
ATEXT-25   String represents owned valid UTF-8 text.
ATEXT-26   Safe str cannot contain malformed UTF-8.
ATEXT-27   Safe String cannot contain malformed UTF-8.
ATEXT-28   String literals are UTF-8.
ATEXT-29   Byte literals represent raw bytes.
ATEXT-30   Axiom String is not a C string.
ATEXT-31   Axiom String may contain U+0000.
ATEXT-32   C strings require explicit FFI representation.
ATEXT-33   String length is measured in UTF-8 bytes.
ATEXT-34   char represents a Unicode scalar value.
ATEXT-35   char is not a grapheme cluster.
ATEXT-36   Grapheme segmentation is library functionality.
ATEXT-37   Unicode normalization is explicit.
ATEXT-38   String operations do not implicitly normalize text.
ATEXT-39   String equality does not implicitly perform Unicode normalization.
ATEXT-40   String hashing does not implicitly normalize text.
ATEXT-41   UTF-8 slicing must preserve code-point boundaries.
ATEXT-42   Safe dynamic slicing cannot construct invalid str.
ATEXT-43   Unchecked UTF-8 slicing is unsafe.
ATEXT-44   String mutation requires appropriate ownership/capability.
ATEXT-45   String growth may relocate storage.
ATEXT-46   Live views constrain legal String relocation.
ATEXT-47   String reserve does not guarantee stable address.
ATEXT-48   String representation is implementation-defined.
ATEXT-49   Small-string optimization is permitted but not semantic.
ATEXT-50   String literals need not allocate runtime storage.
ATEXT-51   Owner-to-view conversion follows capability rules.
ATEXT-52   Borrowed text cannot outlive its owner.
ATEXT-53   Bytes-to-String conversion validates UTF-8 in safe code.
ATEXT-54   Unchecked UTF-8 construction is unsafe.
ATEXT-55   Valid UTF-8 invariant resumes after a trusted unsafe boundary.
ATEXT-56   String does not implicitly cross C ABI.
ATEXT-57   CStr is distinct from str.
ATEXT-58   CString is distinct from String.
ATEXT-59   Foreign string ownership is explicit.
ATEXT-60   OS-native text representation is distinct from Unicode text semantics where required.
ATEXT-61   Path semantics are platform-aware.
ATEXT-62   Path is not necessarily String.
ATEXT-63   PathBuf owns path storage.
ATEXT-64   Unicode algorithms beyond validity are library functionality.
ATEXT-65   Formatting is library functionality.
ATEXT-66   Formatting may use comptime optimization.
ATEXT-67   String conversion is explicit where representation changes.
ATEXT-68   Vec<T> is an owned ordered contiguous sequence.
ATEXT-69   Vec<T> may grow and relocate.
ATEXT-70   Vec<T> does not guarantee stable addresses.
ATEXT-71   Vec indexing performs safe bounds validation unless proven unnecessary.
ATEXT-72   Vec.get provides explicit checked access.
ATEXT-73   Vec.push moves non-Copy values into storage.
ATEXT-74   Vec.pop transfers ownership to the caller.
ATEXT-75   Live dependent views constrain Vec relocation.
ATEXT-76   Vec reserve does not guarantee stable addresses.
ATEXT-77   Vec representation is implementation-defined.
ATEXT-78   Vec does not require a specific allocator representation.
ATEXT-79   Iterator is a library abstraction.
ATEXT-80   Iterator chains need not allocate.
ATEXT-81   Iterator chains use static dispatch by default.
ATEXT-82   Generic iterator adapters may be fully optimized away.
ATEXT-83   Collection iteration has explicit ownership semantics.
ATEXT-84   Consuming iteration may move collection elements.
ATEXT-85   Borrowed iteration uses non-owning capabilities.
ATEXT-86   Mutable iteration uses exclusive capabilities.
ATEXT-87   HashMap is a library abstraction.
ATEXT-88   HashMap iteration order is not stable unless explicitly contracted.
ATEXT-89   Hashing behavior is library-defined unless a stable hash is explicitly selected.
ATEXT-90   BTreeMap provides ordered collection semantics.
ATEXT-91   HashSet and BTreeSet are library abstractions.
ATEXT-92   Deque is a library abstraction.
ATEXT-93   Linked-list structures are not Core requirements.
ATEXT-94   Intrusive collections may use explicit storage identity and unsafe APIs.
ATEXT-95   Collection APIs must expose semantically relevant allocation behavior.
ATEXT-96   Collection APIs must not hide semantically relevant relocation behavior.
ATEXT-97   Stable storage should use explicit stable-storage abstractions.
ATEXT-98   Logical identity should use handles rather than physical addresses where appropriate.
ATEXT-99   Collections support zero-sized element types.
ATEXT-100  Collections respect target alignment requirements.
ATEXT-101  Safe collection copy operations must respect capability/alias rules.
ATEXT-102  Serialization operates on explicit byte/text representations.
ATEXT-103  Binary parsing does not require String conversion.
ATEXT-104  Text parsing uses valid UTF-8 semantics.
ATEXT-105  Streaming APIs can operate on reusable buffers.
ATEXT-106  UTF-8 validation is not repeated after a valid invariant is established.
ATEXT-107  Compile-time-known UTF-8 literals need no runtime validation.
ATEXT-108  Constant string operations may be evaluated at compile time.
ATEXT-109  Unicode data versioning is library-defined.
ATEXT-110  Text, byte, and foreign-string semantics remain distinct.
```

### Một quyết định đáng chú ý

Tôi **không đề xuất thêm `StringView`, `Slice`, `ByteSlice`, `MutableSlice` thành hàng loạt primitive mới**.

Axiom đã có capability model:

```text
view<T>
mut_view<T>
```

nên tận dụng nó:

```text
view<u8>      → bytes
view<str>     → text
mut_view<u8>  → mutable bytes
mut_view<str> → mutable text
```

Như vậy syntax vẫn đơn giản nhưng không hy sinh semantic precision.

---

## Bước tiếp theo

Sau String/Collection, phần còn thiếu rất quan trọng là:

# **BOOTSTRAP-046 — Standard Traits & Fundamental Protocols**

Sẽ freeze các protocol nền tảng như:

```text
Copy
Clone
Drop
Send
Share
Eq
Ord
Hash
Display
Debug
Default
Iterator
IntoIterator
Index
IndexMut
Add/Sub/Mul/Div
BitAnd/BitOr
...
```

Đặc biệt cần giải quyết một vấn đề rất quan trọng của ý tưởng **“struct + function”** mà bạn đã đặt ra từ đầu:

> **Axiom sẽ override/extend behavior như thế nào mà không cần class/inheritance, nhưng vẫn tránh trait system trở nên phức tạp như Rust?**

Phần đó nên được thiết kế ngay sau đây.