Tiếp tục với **BOOTSTRAP-028 — String, Text, Bytes, Slice & Collection Semantics**.

Đây là phần cần đặc biệt cẩn thận vì `String` là nơi nhiều ngôn ngữ vô tình biến một kiểu dữ liệu tưởng đơn giản thành abstraction nặng. Với Axiom, tôi đề xuất:

> **Bytes là primitive-level data. UTF-8 là mặc định cho text. Unicode processing nâng cao nằm ở library. Không để Unicode runtime machinery trở thành bắt buộc.**

---

# BOOTSTRAP-028 — String, Text, Bytes, Slice & Collection Semantics

## 1. Tách hẳn Bytes và Text

Không dùng một kiểu `String` cho cả:

```text
binary data
text
UTF-8 bytes
C string
serialized data
```

Axiom cần phân biệt:

```text id="u2i9qv"
[u8] / view<[u8]>     → bytes
String                → owned UTF-8 text
view<String>          → read access to String
mut_view<String>      → mutable access nếu API cho phép
```

Và nên có:

```text id="u8z3lo"
str
```

cho string literal / static UTF-8 text view.

---

# 2. `String` mặc định là UTF-8

Ví dụ:

```axiom id="p2r5yx"
let name = "Nguyễn Văn A"
```

là UTF-8 text.

Invariant:

```text id="j8kqz4"
String luôn chứa UTF-8 hợp lệ
```

Điều này cho phép:

- interop web
- JSON
- HTTP
- filesystem hiện đại
- AI/NLP
- tiếng Việt
- đa ngôn ngữ

mà không cần encoding parameter ở mọi API.

---

# 3. Nhưng UTF-8 validation không phải lúc nào cũng cần

Đây là điểm rất quan trọng.

Nếu programmer có:

```axiom id="0qj6d4"
view<[u8]>
```

đó chỉ là bytes.

Không được compiler giả định đó là UTF-8.

Muốn biến thành text:

```axiom id="zq3v1j"
String.from_utf8(bytes)
```

→

```text id="m2g4bw"
Result<String, Utf8Error>
```

Nếu programmer **đã biết chắc** bytes hợp lệ:

```axiom id="g0x0dc"
unsafe String.from_utf8_unchecked(bytes)
```

Như vậy parser/network/file processing có thể kiểm soát validation.

---

# 4. `String` không phải `[u8]`

Dù physical representation có thể là:

```text id="4o1d7u"
pointer + length + capacity
```

semantic type khác nhau:

```text id="b4a9tc"
String != Vec<u8>
```

Vì `String` có invariant:

```text id="4i0baj"
valid UTF-8
```

---

# 5. `String` có thể dùng cùng storage model với Vec

Không cần tạo runtime object riêng.

Conceptually:

```text id="bihb5a"
String
 ├── UTF-8 byte region
 ├── length
 └── capacity
```

Nhưng representation vẫn compiler-controlled.

Compiler có thể:

- stack allocate
- move
- eliminate
- inline
- caller allocate
- heap allocate

tùy escape/storage analysis.

---

# 6. String literal

Literal:

```axiom id="6m6zqd"
"Hello"
```

nên có semantic type:

```text id="mny1zo"
str
```

hoặc tương đương:

```text id="u8s9o6"
view<[utf8]>
```

nhưng tôi đề xuất **`str` là language-level text view type** vì API dễ đọc hơn.

Ví dụ:

```axiom id="7afzv3"
fn print(text: str)
```

Gọi:

```axiom id="j1w8kt"
print("Hello")
```

không allocation.

---

# 7. `str` không ownership

```text id="2gqv3g"
str
```

là non-owning read-only UTF-8 text view.

Nó không giữ ownership của underlying storage.

Ví dụ:

```axiom id="e1cbtj"
fn greet(name: str) {
    println("Hello, " + name)
}
```

String literal có static storage.

String object có storage của chính nó.

---

# 8. Có nên cho `view<String>`?

Không nên dùng:

```axiom id="j7p2f0"
view<String>
```

làm text slice phổ biến.

`view<T>` là capability view tới **object T**.

Còn:

```text id="brkhk5"
str
```

là **text sequence view**.

Tương tự:

```text id="e5k7pf"
view<[u8]>
```

là byte sequence.

Đây là hai abstraction khác nhau.

---

# 9. Slice sequence

Axiom nên có syntax:

```text id="d4t1ze"
view<[T]>
mut_view<[T]>
```

cho contiguous element sequence.

Ví dụ:

```axiom id="k82j3a"
fn sum(xs: view<[i32]>) -> i32
```

Đây là abstraction canonical cho:

- array slice
- vector slice
- buffer region
- mapped memory
- packet data
- GPU buffer view.

---

# 10. Slice không ownership

```text id="2vmy1p"
view<[T]>
```

chỉ có:

```text id="1pgyo4"
provenance
region
length
access capability
```

Không có ownership.

---

# 11. Slice có thể được tạo bằng range

```axiom id="6tup7f"
let middle = view(values[10..20])
```

hoặc nếu compiler cho syntax trực tiếp:

```axiom id="r2c9y8"
let middle = values[10..20]
```

với expected type `view<[T]>`.

Tôi đề xuất:

```text id="e2m8tw"
values[a..b]
```

→ slice/view khi context yêu cầu.

Còn:

```text id="6p6e9x"
values[i]
```

→ element access.

---

# 12. Mutable slice

```axiom id="y8r6pa"
let part = mut_view(values[10..20])
```

Compiler kiểm tra region:

```text id="53kt3d"
[10,20)
```

Không cho phép overlapping `mut_view`.

---

# 13. Array

Array:

```axiom id="qz10yw"
let values: [i32; 4] = [1, 2, 3, 4]
```

có:

- fixed length
- contiguous representation
- inline value semantics
- known compile-time size.

Array không cần heap.

---

# 14. Array và slice khác nhau

```text id="9xvlyp"
[i32; 1024]
```

= object/value.

```text id="l91y5v"
view<[i32]>
```

= capability tới region.

Ví dụ:

```axiom id="yqwj9d"
fn process(data: view<[i32]>) { ... }

let a: [i32; 1024]
process(a)
```

không copy 1024 integers.

Compiler tạo ephemeral view.

---

# 15. `Vec<T>`

`Vec<T>` là dynamic sequence.

Semantic:

```text id="s7w4zv"
Vec<T>
 ├── logical sequence
 ├── length
 ├── capacity
 └── storage identity
```

Physical:

```text id="n9zj37"
pointer + len + cap
```

chỉ là một implementation possibility.

---

# 16. `Vec` có thể relocate

Ví dụ:

```axiom id="sv5eob"
var v = Vec<i32>()
v.push(1)
v.push(2)
```

Nếu capacity hết:

```text id="fyw7cu"
old storage
    ↓
new storage
    ↓
move elements
```

Đây là hợp lệ.

Do đó:

```axiom id="5z8o4n"
view(v[0])
```

đang live có thể ngăn operation có khả năng relocate.

---

# 17. `reserve()` không đảm bảo stable address

```axiom id="9q5jsa"
v.reserve(1000)
```

chỉ đảm bảo semantic capacity đủ theo API contract.

Không được hiểu:

```text id="t3ng2g"
"address của v[0] sẽ vĩnh viễn ổn định"
```

Nếu cần stable address:

```text id="5j4i9x"
Pool<T>
StableVec<T>
Box<T>
```

hoặc storage abstraction khác.

---

# 18. `Vec` move không copy toàn bộ

```axiom id="bx7zv1"
let a = v
```

nếu `Vec<T>` owning/non-Copy:

```text id="y5h1s6"
ownership state:
v → moved
a → owner
```

Không bắt buộc copy elements.

Đây là `AMEM-27`.

---

# 19. `Vec` clone mới copy elements

```axiom id="c5zh3q"
let b = a.clone()
```

có thể:

```text id="m2t6jp"
allocate
copy/move-clone each element
```

Cost explicit.

---

# 20. Collection allocator không nằm trong type mặc định

Không:

```text id="fdp8o8"
Vec<T, Allocator>
```

làm API phổ biến.

Mặc định:

```text id="1q6yif"
Vec<T>
```

Nếu cần allocator đặc biệt:

```text id="1q5x4r"
ArenaVec<T>
PoolVec<T>
```

hoặc API construction/config.

Điều này giữ type signatures đơn giản.

---

# 21. `Buffer<T>`

Nên phân biệt:

```text id="e6p4ya"
Vec<T>
Buffer<T>
```

### Vec

Collection semantics:

```text id="9jgz2k"
push
pop
insert
remove
iteration
```

### Buffer

Raw storage semantics:

```text id="0g7w6y"
resize storage
reserve bytes
read/write region
possibly uninitialized storage
```

`Buffer<u8>` đặc biệt hữu ích cho:

- networking
- file I/O
- compression
- serialization
- GPU transfer
- image/audio.

---

# 22. Uninitialized storage

Compiler/runtime đã cần concept này từ representation model.

Nên có library/system abstraction:

```text id="04m6b8"
Uninit<T>
```

hoặc:

```text id="42o0l1"
RawBuffer
```

để xử lý:

```text id="3n6e4r"
allocate
initialize subset
assume initialized
```

Không cho safe code đọc uninitialized memory.

MIR tracking:

```text id="7j3b8d"
UNINIT
INIT
MOVED
DROPPED
```

---

# 23. Bytes

Canonical binary APIs nên dùng:

```axiom id="bh3n1c"
view<[u8]>
mut_view<[u8]>
Vec<u8>
Buffer<u8>
```

Không cần tạo `Bytes` primitive trong Core.

Library có thể thêm:

```text id="7q0o7x"
Bytes
BytesMut
```

nếu ecosystem cần.

---

# 24. C string

C string không nên giả vờ là `String`.

Có thể có system type:

```text id="7a4n1c"
CStr
CString
```

hoặc:

```text id="6skx4r"
view<c_char>
```

với explicit NUL semantics.

Ví dụ FFI:

```axiom id="a2x6r9"
extern "C" fn puts(s: *const u8)
```

Wrapper:

```axiom id="f5c1nd"
fn puts(text: str) {
    ...
}
```

wrapper chịu trách nhiệm encoding + NUL.

---

# 25. Không có null-terminated String mặc định

`String`:

```text id="t5p1vx"
"hello"
```

không cần:

```text id="5d8t1c"
'h'
'e'
'l'
'l'
'o'
'\0'
```

ở cuối.

Length được lưu semantic/representation.

Điều này tránh:

- O(n) length
- embedded NUL ambiguity
- C-style string bugs.

---

# 26. Embedded NUL

UTF-8 String có thể chứa U+0000.

Ví dụ:

```text id="u6t3x2"
"abc\0def"
```

vẫn là valid text.

Khi chuyển sang C string:

```text id="qj0v8s"
CString::from(str)
```

có thể reject embedded NUL.

---

# 27. Unicode model

Đây là chỗ tôi đề xuất **không đưa Unicode grapheme processing vào Core**.

Core chỉ cần:

```text id="8ny2wr"
String = valid UTF-8
```

Library cung cấp:

```text id="l8x7e1"
Unicode scalar iteration
grapheme clusters
normalization
case mapping
collation
locale
```

Lý do:

Unicode là một domain rất lớn và thay đổi theo Unicode version.

Không nên bắt mọi binary Axiom link Unicode runtime.

---

# 28. Nhưng có nên có `char`?

Có.

Nhưng tôi đề xuất:

```text id="g6j6pj"
char = Unicode scalar value
```

không phải byte.

Kích thước có thể là 32 bit.

Ví dụ:

```axiom id="0e5x9x"
let c: char = 'Đ'
```

String iteration:

```axiom id="j7qk1v"
for c in text.chars() {
    ...
}
```

có thể decode UTF-8.

---

# 29. `u8` vẫn là byte

Không biến `u8` thành character.

```text id="yg9qsr"
u8 = byte
char = Unicode scalar
String = UTF-8 sequence
```

Rõ ràng.

---

# 30. Grapheme không phải char

Ví dụ một ký tự người dùng nhìn thấy có thể gồm nhiều Unicode scalar.

Do đó:

```text id="7a17dw"
text.len()
```

nên trả về **byte length** nếu API là storage-level.

Còn:

```text id="2i4v1s"
text.chars().count()
```

là scalar count.

Và:

```text id="x0lq38"
text.graphemes().count()
```

là grapheme count.

Không nên có một `String.length` duy nhất rồi thay đổi ý nghĩa theo locale.

---

# 31. Tôi đề xuất `String.len()` = bytes

Đây là lựa chọn performance-oriented.

```axiom id="0y6jce"
let n = text.len()
```

→ số byte UTF-8.

Vì:

- O(1)
- phù hợp storage
- phù hợp I/O
- phù hợp network
- phù hợp FFI.

Nếu cần character count:

```axiom id="x4q0a9"
text.chars().count()
```

Nếu grapheme:

```axiom id="s4m2m6"
text.graphemes().count()
```

---

# 32. Index String trực tiếp

Tôi đề xuất **không cho**:

```axiom id="yd6q5q"
text[i]
```

trả `char`.

Vì `i` là byte offset nhưng UTF-8 character có độ dài 1–4 byte.

Thay:

```axiom id="4c7h9g"
text.byte_at(i)
```

hoặc:

```axiom id="r8z2kq"
text.chars().nth(i)
```

Điều này tránh abstraction giả rằng Unicode string là fixed-width array.

---

# 33. UTF-8 slicing

Không cho phép tùy tiện:

```axiom id="f6m0q4"
text[1..5]
```

nếu boundary không phải UTF-8 code-point boundary.

API có thể:

```axiom id="q0a3j7"
text.slice(byte_start, byte_end)
    -> Result<str, Utf8BoundaryError>
```

Nếu compiler có thể chứng minh boundary hợp lệ thì check có thể được eliminate.

---

# 34. Unsafe UTF-8 slicing

System code có thể:

```axiom id="z3q2k1"
unsafe {
    text.slice_unchecked(start, end)
}
```

Nhưng đây là exceptional.

---

# 35. String concatenation

Không nên để:

```axiom id="s9c7r2"
a + b + c + d
```

tạo nhiều allocation trung gian bắt buộc.

Compiler có thể biến thành:

```text id="x4c5kn"
compute total size
allocate once
copy a
copy b
copy c
copy d
```

hoặc dùng `StringBuilder`.

Operator semantics vẫn là concatenate.

---

# 36. Formatting

Đây là nơi **comptime** rất mạnh.

Ví dụ:

```axiom id="1e8b3x"
format("x={}, y={}", x, y)
```

compiler có thể parse format string tại compile time.

Sai:

```axiom id="q4m5g6"
format("x={} {}", x)
```

→ compile-time diagnostic.

Không cần parser format runtime cho literal.

Dynamic format string vẫn có runtime path nếu API cho phép.

---

# 37. Collection iteration

Iterator trait:

```axiom id="w5v4xe"
trait Iterator {
    type Item

    fn next(self: mut_view<Self>) -> Option<Self.Item>
}
```

`for` có thể lower thành:

```text id="m2u3pl"
loop {
    match iterator.next() {
        Some(x) => body
        None => break
    }
}
```

Sau monomorphization/inlining, toàn bộ có thể biến thành native loop.

---

# 38. Iterator không cần heap

Một iterator:

```axiom id="f4c2qx"
RangeIterator {
    current: usize
    end: usize
}
```

có thể nằm hoàn toàn trong registers.

Không:

```text id="e1h9vy"
Box<Iterator>
vtable
heap allocation
```

trừ khi programmer explicit yêu cầu dynamic iterator.

---

# 39. Dynamic iterator

Nếu thực sự cần:

```text id="4y5s4a"
dyn Iterator
```

thì dynamic dispatch/storage cost là explicit.

Một lần nữa:

```text id="2r3j1h"
generic Iterator → static/zero-cost
dyn Iterator     → dynamic
```

---

# 40. Collection API không được ép allocator semantics

Ví dụ:

```axiom id="p8k2v1"
Vec<T>
```

không cần expose:

```text id="f9d2k7"
allocator()
raw_capacity()
raw_pointer()
```

trong normal API.

System API có thể expose khi cần.

Điều này giữ abstraction sạch.

---

# 41. Một điểm quan trọng: `String` không nên là "Unicode object"

Tôi muốn đóng băng nguyên tắc:

```text id="5h8x4v"
String
  =
  valid UTF-8 byte sequence
```

Không:

```text id="c0w7qy"
String
  =
  Unicode runtime object
  +
  locale
  +
  grapheme engine
  +
  normalization
  +
  allocator
```

Những thứ sau thuộc library:

```text id="5f2lq8"
Unicode
Regex
Grapheme
Locale
Collation
Normalization
```

---

# 42. Điều này đặc biệt tốt cho Axiom AI/NLP

Với mục tiêu AI của Axiom:

```text id="2m3t7x"
String
 ↓
UTF-8
 ↓
[u8]
 ↓
tokenizer/parser
 ↓
Tensor / GPU
```

chuyển đổi rất rõ.

Không có abstraction Unicode nặng đứng giữa.

---

# 43. Invariants BOOTSTRAP-028

```text id="0x7k2p"
ASTR-20  Bytes and Text are distinct semantic domains.

ASTR-21  String represents valid UTF-8 text.

ASTR-22  Vec<u8> does not imply valid UTF-8.

ASTR-23  String is distinct from Vec<u8>.

ASTR-24  str is a non-owning UTF-8 text view.

ASTR-25  str does not imply allocation.

ASTR-26  String ownership is deterministic.

ASTR-27  UTF-8 validation occurs when arbitrary bytes become String.

ASTR-28  from_utf8 may return recoverable validation failure.

ASTR-29  unchecked UTF-8 construction is unsafe.

ASTR-30  String length is byte length.

ASTR-31  Unicode scalar count is a separate operation.

ASTR-32  Grapheme count is a separate library operation.

ASTR-33  u8 represents bytes, not Unicode characters.

ASTR-34  char represents a Unicode scalar value.

ASTR-35  String indexing does not implicitly return char by byte offset.

ASTR-36  UTF-8 slicing requires valid code-point boundaries.

ASTR-37  Invalid UTF-8 boundaries are rejected in safe APIs.

ASTR-38  C strings are distinct from Axiom String.

ASTR-39  Axiom String does not require NUL termination.

ASTR-40  Embedded NUL is valid UTF-8 String content.

ASTR-41  C-string conversion may reject embedded NUL.

ASTR-42  Unicode normalization is not a Core String invariant.

ASTR-43  Locale and collation are library semantics.

ASTR-44  Unicode runtime machinery is not mandatory for basic String use.

ASTR-45  Array is a fixed-size contiguous value.

ASTR-46  view<[T]> is a non-owning contiguous sequence capability.

ASTR-47  mut_view<[T]> is an exclusive mutable sequence capability.

ASTR-48  Vec<T> is a dynamic sequence abstraction.

ASTR-49  Vec storage may relocate.

ASTR-50  Vec reserve does not imply stable address.

ASTR-51  Live dependent capabilities prevent invalid Vec relocation.

ASTR-52  Vec move transfers ownership without required element copy.

ASTR-53  Vec clone explicitly duplicates elements.

ASTR-54  Collection allocator choice is not part of ordinary collection type semantics.

ASTR-55  Specialized storage collections may expose explicit allocation contracts.

ASTR-56  Buffer represents storage-oriented semantics distinct from Vec collection semantics.

ASTR-57  Uninitialized storage cannot be read by safe code.

ASTR-58  Iterator abstraction does not imply allocation.

ASTR-59  Generic iteration is statically specialized when possible.

ASTR-60  Dynamic iteration requires explicit dynamic representation.

ASTR-61  for lowering preserves iterator semantics.

ASTR-62  Bounds checks may be eliminated when proven unnecessary.

ASTR-63  Formatting of compile-time literals may be checked at compile time.

ASTR-64  String concatenation does not require intermediate allocation when optimization can eliminate it.

ASTR-65  Physical String/Vec representation is compiler-controlled.

ASTR-66  String storage location is not part of ordinary value semantics.

ASTR-67  Text semantics are independent from allocator strategy.

ASTR-68  Byte semantics are independent from Unicode semantics.

ASTR-69  Collection operations preserve ownership/capability rules.

ASTR-70  Serialization representation is distinct from String/collection memory representation.
```

---

# 44. Core collection model lúc này

Axiom đã có một hierarchy khá sạch:

```text id="f9n2gc"
                    SEQUENCE
                       │
          ┌────────────┼────────────┐
          │            │            │
       Array          Vec         Buffer
     fixed-size     dynamic      storage
          │            │            │
          └────────────┼────────────┘
                       │
                  view<[T]>
                  mut_view<[T]>
                       │
                       ▼
                    Iterator
```

Text tách riêng:

```text id="x6c4jv"
             TEXT
               │
         ┌─────┴─────┐
       str          String
     borrowed       owned
         │             │
         └──── UTF-8 ──┘
```

Bytes:

```text id="q2j5b8"
[u8]
view<[u8]>
mut_view<[u8]>
Vec<u8>
Buffer<u8>
```

Không có sự nhập nhằng giữa **memory**, **bytes**, **text**, **Unicode character**.

---

# 45. Một quyết định rất đáng giữ

Tôi đặc biệt khuyến nghị Axiom **không có `String` indexing theo character**.

Đừng làm:

```axiom id="d5v6xz"
text[5]
```

với kỳ vọng:

```text
"ký tự thứ 5"
```

Bởi vì với UTF-8:

```text
byte index
≠
Unicode scalar index
≠
grapheme index
```

Ba khái niệm này phải được giữ riêng.

Điều này vừa đúng Unicode vừa giúp compiler tối ưu tốt hơn.

---

# 46. Core hiện đã gần đủ "ngôn ngữ"

Sau BOOTSTRAP-028, Axiom đã có:

```text id="6t6e6b"
TYPE
MEMORY
POINTER
FUNCTION
CONTROL FLOW
STRING
BYTES
SLICE
COLLECTION
ITERATOR
CONCURRENCY
ASYNC
ABI
```

Phần còn thiếu lớn trước khi đi vào **Standard Library architecture** là một thứ rất quan trọng:

# **BOOTSTRAP-029 — Module, Package, Namespace, Visibility & Build Semantics**

Ta cần chốt:

- `module`
- `import`
- `use`
- `pub`
- `private`
- package
- dependency
- package identity
- version
- workspace
- circular dependency
- initialization
- static initialization
- compile units
- incremental compilation
- module interface
- symbol visibility
- binary exports
- package cache
- dependency reproducibility
- cross compilation
- build profiles
- feature flags
- `@cfg`
- comptime configuration
- và quan trọng nhất: **Axiom build system có cần trở thành một "cargo/cmake" khổng lồ hay chỉ cần một compiler + module/package model rất gọn.**