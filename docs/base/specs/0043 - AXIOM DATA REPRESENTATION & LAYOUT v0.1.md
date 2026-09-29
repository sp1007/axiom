Tiếp tục. Phần này tôi nghĩ nên **khóa DATA REPRESENTATION + STRUCT/ENUM LAYOUT v0.1** trước khi sang thư viện. Nó trực tiếp quyết định binary size, cache locality, ABI, FFI và khả năng optimizer tự do tối ưu.

# AXIOM DATA REPRESENTATION & LAYOUT v0.1

## 1. Nguyên tắc nền tảng

Axiom phải phân biệt 4 tầng:

```text
Semantic Type
      ↓
Logical Representation
      ↓
ABI Representation
      ↓
Machine Representation
```

Ví dụ:

```axiom
struct Point {
    x: f32
    y: f32
}
```

Semantically:

```text
Point = { x: f32, y: f32 }
```

Nhưng compiler **không bắt buộc** phải lưu đúng:

```text
offset(x) = 0
offset(y) = 4
size = 8
```

trừ khi programmer yêu cầu một representation cụ thể.

---

# 2. Default layout: compiler-controlled

Mặc định:

```text
struct Point
```

có:

```text
layout = implementation-defined
```

Compiler được phép:

- reorder fields
- padding
- alignment
- scalar replacement
- register promotion
- eliminate field
- pack representation nếu semantic vẫn đúng.

Nhưng có một điều kiện cực quan trọng:

> Programmer không được phép quan sát layout mặc định.

---

# 3. Khi nào layout trở thành observable?

Layout trở thành semantic/ABI contract khi programmer làm những việc như:

```text
FFI
raw pointer
address arithmetic
serialization bằng memory bytes
DMA
mmap
hardware register
```

Lúc đó phải dùng explicit representation.

---

# 4. `repr(C)`

Ví dụ:

```axiom
@repr(C)
struct Point {
    x: f32
    y: f32
}
```

Lúc này:

```text
Point
↓
C-compatible layout
↓
C ABI
```

Compiler không được tùy ý reorder field.

---

# 5. Không nên có `repr(C)` trong semantic Core quá sâu

`repr(C)` là một **representation attribute**, không phải type-system concept.

Tức:

```text
struct semantics
```

vẫn giống nhau.

Chỉ ABI lowering thay đổi:

```text
Typed MIR
 ↓
ABI lowering
 ↓
repr(C)
```

---

# 6. Field order

Default:

```axiom
struct Example {
    a: u8
    b: u64
    c: u8
}
```

không đảm bảo:

```text
a
padding
b
c
```

Compiler có thể reorder để giảm padding.

Ví dụ:

```text
b
a
c
```

có thể nhỏ hơn.

---

# 7. Nhưng có một vấn đề

Nếu compiler reorder field, programmer vẫn phải có cách viết:

```axiom
p.a
p.b
p.c
```

Compiler giải quyết bằng semantic field identity.

Field name không đồng nghĩa với physical offset trong source-level semantics.

---

# 8. Tại sao tôi ủng hộ compiler-controlled layout?

Vì nó cho optimizer freedom:

```text
struct {
    bool
    i64
    bool
}
```

có thể được layout tối ưu.

Đặc biệt generic structs:

```axiom
struct Pair<T, U> {
    first: T
    second: U
}
```

có thể có layout khác nhau cho:

```text
Pair<u8,u64>
Pair<u64,u8>
```

---

# 9. Nhưng ABI stability?

Default Axiom ABI:

> Không cam kết layout ổn định giữa compiler versions.

Nếu cần stable ABI:

```axiom
@repr(C)
```

hoặc future:

```text
@repr(axiom_v1)
```

cho ABI versioned.

---

# 10. `@repr(packed)`

Có thể hỗ trợ:

```axiom
@repr(packed)
struct Header {
    ...
}
```

nhưng:

> `packed` là unsafe/system-level.

Vì unaligned access có thể gây:

- hardware fault
- performance penalty
- undefined machine behavior ở một số target nếu không được xử lý.

Compiler phải không cho safe code tự tạo reference/view tới field misaligned.

---

# 11. `@align`

Cho phép explicit alignment:

```axiom
@align(64)
struct CacheLine {
    ...
}
```

Có giá trị cho:

- SIMD
- cache line
- DMA
- lock-free structures
- hardware.

Nhưng không nên lạm dụng.

---

# 12. `size_of` và `align_of`

Nên có intrinsic:

```axiom
size_of<T>()
align_of<T>()
```

Nhưng chỉ trả kết quả compile-time khi T đã known.

Ví dụ:

```axiom
const SIZE = size_of<Point>()
```

---

# 13. Không nên cho runtime reflection mặc định

Không cần:

```text
object.size
object.fields
object.type_name
```

vì sẽ kéo metadata runtime.

Compile-time reflection có thể tồn tại:

```text
type_info<T>()
```

nếu compiler có thể evaluate.

---

# 14. Field offset

Tương tự:

```text
offset_of<T, field>()
```

chỉ nên có khi representation đã explicit hoặc compiler cho phép expose layout.

Nếu gọi trên default struct:

```text
offset_of<Point, x>
```

thì việc này biến layout thành observable.

Có hai lựa chọn:

### Option A

Cho phép và compiler phải freeze layout của type.

### Option B

Chỉ cho phép với `@repr(...)`.

Tôi chọn **B**.

Nó giữ optimizer freedom.

---

# 15. Struct không có hidden metadata

Đây là invariant cực mạnh:

```text
struct Point
```

không tự động có:

```text
type pointer
refcount
GC header
vtable pointer
object header
```

Một:

```text
Point { f32, f32 }
```

có thể thực sự chỉ là:

```text
8 bytes
```

nếu target/layout phù hợp.

---

# 16. Empty struct

Axiom nên hỗ trợ:

```axiom
struct Marker {}
```

Có thể là ZST:

```text
size = 0
```

hoặc ABI-required minimum size trong một số context.

Semantic identity vẫn tồn tại.

---

# 17. Zero-sized type

ZST hữu ích cho:

```text
Marker
Phantom<T>
type-level tags
generic policies
```

Không cần allocation.

---

# 18. Struct field access

```axiom
p.x
```

ban đầu là:

```text
PLACE
```

Không tự load.

Nếu:

```axiom
let x = p.x
```

thì:

```text
p.x
↓
READ
↓
VALUE
```

Nếu:

```axiom
p.x = 10
```

thì:

```text
p.x
↓
WRITE PLACE
```

---

# 19. Method không phải field

Nếu:

```axiom
p.length()
```

compiler không tìm:

```text
p.length field
```

trừ khi type có field thực sự.

Resolution:

```text
field lookup
method lookup
trait lookup
extension lookup
```

phải deterministic.

---

# 20. Struct destructuring

```axiom
let Point { x, y } = p
```

về semantic tương đương:

```text
move p.x → x
move p.y → y
```

nếu không-Copy.

Nếu Point Copy:

```text
copy p.x
copy p.y
```

---

# 21. Partial destructuring

```axiom
let Point { x, .. } = p
```

chỉ consume/read `x`.

Sau đó:

```text
p
├── x → MOVED
└── y → OWNED
```

Đây là một tính năng rất đáng giá vì phù hợp ownership model hiện tại.

---

# 22. Mutable destructuring

```axiom
var Point { x, y } = ...
```

không cần tạo reference.

Compiler có thể bind trực tiếp tới fields hoặc local temporaries tùy optimization.

---

# 23. Tuple layout

Tuple:

```axiom
let x = (a, b, c)
```

là structural type:

```text
(T1, T2, T3)
```

Default layout compiler-controlled.

Không có field name:

```text
.0
.1
.2
```

có thể là syntax projection.

---

# 24. Array layout

Array:

```axiom
Array<T, N>
```

semantic:

```text
N elements of T
```

Default representation phải contiguous.

Đây là nơi tôi muốn khác struct.

> Array layout **phải contiguous**.

Vì nếu không, các semantics như indexing, view, FFI và SIMD sẽ mất ý nghĩa.

---

# 25. Array size

```axiom
let a: [i32; 4]
```

nếu Axiom dùng syntax này, semantic size:

```text
4 × size_of<i32>
```

Có thể nằm:

- register
- stack
- inline parent
- static
- compiler-eliminated

nhưng logical representation là contiguous.

---

# 26. Slice/view

```axiom
view<T>
```

là view của contiguous region.

Conceptually:

```text
(data, length)
```

nhưng ABI không bắt buộc representation chính xác nếu không exposed.

---

# 27. `mut_view<T>`

Conceptually:

```text
(data, length, WRITE capability)
```

Capability không nhất thiết nằm trong runtime object.

Thông thường:

```text
pointer + length
```

là đủ.

Compiler verifier giữ:

```text
provenance
region
access
```

ở compile-time.

---

# 28. Đây là điểm rất quan trọng về performance

Axiom không nên tạo:

```text
ViewObject {
    ptr
    len
    lifetime
    owner_id
    runtime_metadata
}
```

cho mỗi view.

Thay vào đó:

```text
semantic:
    provenance + capability

machine:
    ptr + len
```

Phần semantic metadata biến mất sau verification.

Đây chính xác là kiểu **zero-cost abstraction** mà Axiom nên hướng tới.

---

# 29. Enum representation

Ví dụ:

```axiom
enum Result<T, E> {
    Ok(T)
    Err(E)
}
```

Semantic:

```text
tag + payload
```

nhưng physical representation compiler-controlled.

Compiler có thể dùng:

```text
tag + payload
```

hoặc niche optimization.

---

# 30. Niche optimization

Ví dụ:

```text
Option<*const T>
```

có thể biểu diễn:

```text
null = None
non-null = Some(ptr)
```

Nhưng raw pointer null chỉ là representation/unsafe boundary.

Ở semantic layer:

```text
Option<Pointer>
```

vẫn là:

```text
Some
None
```

không có “null value” trong safe type semantics.

---

# 31. `Option<bool>`

Compiler có thể pack:

```text
None
Some(false)
Some(true)
```

vào 2 bits hoặc byte tùy target.

Không được programmer dựa vào representation mặc định.

---

# 32. Enum discriminant

Compiler tự chọn:

```text
u8
u16
u32
...
```

tùy số variant và payload.

Nhưng:

```text
@repr(C)
```

sẽ tạo C-compatible enum representation theo rule tương ứng.

---

# 33. Enum payload không được đọc sai variant

```axiom
match x {
    Some(v) => use(v)
}
```

Compiler đảm bảo tag check.

Raw reinterpretation:

```text
reinterpret<OtherEnum>(x)
```

phải unsafe.

---

# 34. `match` optimization

Compiler có thể biến:

```axiom
match enum {
    A => ...
    B => ...
    C => ...
}
```

thành:

```text
jump table
branch chain
conditional move
```

tùy profile.

Semantics không đổi.

---

# 35. Enum + ownership

```axiom
enum Value {
    Number(i64)
    Text(String)
}
```

`Value` phải có:

```text
Drop
!Copy
```

vì một variant chứa String.

Khi:

```axiom
match value {
    Text(s) => ...
}
```

ownership của payload được chuyển theo pattern.

---

# 36. Drop của enum

Compiler không thể:

```text
Drop(Number)
→ Drop payload
```

nếu payload không Drop.

Và:

```text
Drop(Text)
→ Drop String
```

phải đúng variant.

Có thể dùng:

```text
tag-dispatch
```

hoặc optimized drop glue.

---

# 37. Drop glue

Đây là compiler-generated code:

```text
Drop<T>
```

không nhất thiết user viết.

Ví dụ:

```text
User
 ├─ String
 ├─ Buffer
 └─ i32
```

compiler sinh logical cleanup:

```text
Drop(Buffer)
Drop(String)
```

và optimizer có thể inline/eliminate.

---

# 38. Generic struct layout

```axiom
struct Pair<A, B> {
    first: A
    second: B
}
```

Không có một layout universal.

Ví dụ:

```text
Pair<u8,u64>
Pair<u64,u8>
```

có thể có layout khác.

Generic specialization phải được phép ảnh hưởng representation.

---

# 39. Nhưng source semantics phải invariant

Dù layout thay đổi:

```axiom
p.first
```

vẫn luôn truy cập logical field `first`.

Không được để generic specialization làm thay đổi observable semantic.

---

# 40. Packed generic types

Nếu:

```axiom
@repr(packed)
struct Packet<T> {
    ...
}
```

thì compiler phải kiểm tra:

- alignment
- field access
- FFI
- unsafe boundaries.

Không được để safe `view<T>` trỏ tới misaligned field.

---

# 41. Stable address

Default:

```text
Point
```

không có stable address.

Compiler được:

```text
stack → register
stack → different stack slot
heap → scalar
```

miễn observable semantics không đổi.

---

# 42. Khi address được lấy

Ví dụ unsafe:

```axiom
let p = unsafe { &raw(x) }
```

thì address trở thành observable.

Compiler phải biết:

```text
x storage identity exposed
```

và không được optimize theo cách phá vỡ contract.

Đây là lý do chúng ta đã đặt nguyên tắc:

> **Address is semantic only when explicitly exposed.**

---

# 43. Address exposure nên cực kỳ rõ

Tôi đề xuất sau này có API/system primitive kiểu:

```text
raw_ptr(x)
```

hoặc:

```text
addr_of(x)
```

chỉ trong unsafe.

Không nên có implicit:

```text
&x
```

vì nó làm programmer tưởng rằng mọi value đều có stable address.

---

# 44. Field address

```axiom
unsafe {
    raw_ptr(person.age)
}
```

Compiler biết field address đã observable.

Nếu struct layout default và field offset chưa stable, operation này nên yêu cầu explicit representation hoặc compiler-generated temporary semantics.

Tôi nghiêng về:

> Raw address của field chỉ hợp lệ với storage/layout có address contract rõ ràng.

---

# 45. Serialization

Không được:

```text
serialize(struct)
=
memcpy(&struct, sizeof(struct))
```

đối với default representation.

Phải có:

```text
Serialize trait
```

hoặc explicit binary representation.

Điều này tránh việc compiler reorder field phá serialization.

---

# 46. Byte view

Một abstraction kiểu:

```text
view<u8>
```

của arbitrary typed value không nên tự động được phép.

Vì:

```text
padding
endianness
niche
uninitialized bytes
pointer provenance
```

có thể khiến byte representation không phải semantic representation.

Nếu cần:

```text
bytes_of<T>()
```

phải là explicit unsafe/system API với rules rất rõ.

---

# 47. SIMD

Không cần nhét SIMD vector types khắp Core.

Có thể có:

```text
Vec4<f32>
```

là ordinary struct/array.

SIMD native:

```text
simd<f32, 4>
```

nên nằm trong intrinsic/library layer.

Compiler có thể auto-vectorize:

```text
for ...
```

mà không cần programmer dùng SIMD.

---

# 48. Bitfields

Không nên có bitfield syntax trong Core v0.1.

Ví dụ:

```text
u8 a:3
u8 b:5
```

rất phụ thuộc ABI/compiler/endianness.

Nếu cần:

```text
BitField
```

library/system abstraction hoặc explicit packed representation.

---

# 49. Union

Đây là một điểm cần quyết định.

C union:

```text
union {
    int x;
    float y;
}
```

không an toàn.

Tôi đề xuất:

> **Không có untagged union trong safe Core.**

Thay vào đó:

```text
enum
```

cho safe tagged union.

Raw C union chỉ qua:

```text
@repr(C)
extern type
```

hoặc unsafe/system construct.

---

# 50. Nếu cần zero-cost tagged union

`enum` vẫn có thể compile thành C-like union:

```text
tag
payload
```

hoặc niche.

Không cần programmer-facing `union`.

---

# 51. Bit reinterpretation

Không dùng:

```text
as
```

cho reinterpretation.

Ví dụ:

```text
f32 as u32
```

là numeric conversion.

Còn:

```text
reinterpret<u32>(float)
```

là bit reinterpretation.

Có thể unsafe hoặc safe trong những trường hợp compiler chứng minh representation-compatible, nhưng v0.1 tôi đề xuất **unsafe/system**.

---

# 52. Endianness

Integer semantic:

```text
u32
```

không có “little endian type”.

Endian chỉ xuất hiện khi chuyển:

```text
integer
↔
bytes
```

Ví dụ library:

```text
to_le_bytes()
to_be_bytes()
from_le_bytes()
```

Đây là cách sạch hơn rất nhiều.

---

# 53. Data representation invariant set

Tôi đề xuất đóng băng:

### ADR-01
Default struct layout is compiler-controlled.

### ADR-02
Default layout is not ABI-stable.

### ADR-03
Programmer-visible field identity is independent of physical offset.

### ADR-04
`repr(C)` establishes C-compatible representation.

### ADR-05
Packed representation is unsafe/system-level.

### ADR-06
Explicit alignment is supported.

### ADR-07
No mandatory object header.

### ADR-08
No implicit runtime type pointer.

### ADR-09
No implicit vtable.

### ADR-10
No implicit reference counter.

### ADR-11
Arrays are logically contiguous.

### ADR-12
Views are logically contiguous capabilities.

### ADR-13
View lifetime/provenance metadata need not exist at runtime.

### ADR-14
Enum representation is compiler-controlled unless explicit representation is specified.

### ADR-15
Niche optimization is allowed.

### ADR-16
Default struct address stability is not guaranteed.

### ADR-17
Exposing an address creates an explicit storage contract.

### ADR-18
Raw byte serialization of arbitrary structs is not semantically valid by default.

### ADR-19
Safe untagged unions are not Core v0.1.

### ADR-20
Bit reinterpretation is distinct from numeric conversion.

### ADR-21
Endianness is a byte-representation concern.

### ADR-22
ZSTs are supported.

### ADR-23
Generic specialization may produce distinct physical layouts.

### ADR-24
Physical layout changes cannot alter semantic field/type behavior.

---

# 55. Bây giờ có một bức tranh khá hoàn chỉnh

Ta đang có:

```text
                    AXIOM
                      │
          ┌───────────┴───────────┐
          │                       │
       SEMANTICS             REPRESENTATION
          │                       │
    ┌─────┼─────┐          ┌──────┼──────┐
    │     │     │          │      │      │
  Type  Owner Control    Struct  Enum   Array
    │     │     │          │      │      │
    └─────┼─────┘          └──────┼──────┘
          │                       │
          └──────────┬────────────┘
                     ▼
                    MIR
                     │
             Verification
                     │
                Verified MIR
                     │
              Optimization
                     │
                ABI Lowering
                     │
                Machine Code
```

Điểm đáng chú ý là **Axiom không cần object model** để có abstraction mạnh.

Nó có:

```text
struct
enum
trait
generic
closure
view
ownership
```

nhưng vẫn có thể compile một struct đơn giản thành dữ liệu rất gần với C:

```text
struct Vec3 {
    x: f32
    y: f32
    z: f32
}
```

→ có thể chỉ là 12 bytes dữ liệu thuần, không header, không GC, không vtable, không hidden pointer.

---

## Một quyết định tiếp theo tôi muốn khóa

Sau phần representation, tôi nghĩ **không nên nhảy ngay vào String/Vec**.

Có một vấn đề còn quan trọng hơn đối với mục tiêu “nhanh bằng/hơn C/C++”:

# **AXIOM MEMORY ACCESS + POINTER + ALIASING + OPTIMIZER CONTRACT**

Cụ thể phải giải quyết:

```text
raw pointer
pointer provenance
view
mut_view
restrict-like optimization
alias analysis
load/store reordering
volatile
atomic
alignment
bounds checks
memcpy/memmove/memset
SIMD
noalias
escape analysis
stack promotion
```

Đây chính là nơi quyết định Axiom có thể đạt **zero-cost ownership + compiler-managed safety mà không phải trả giá runtime** hay không.

Và cũng là chỗ cần giải quyết câu hỏi trước đây của bạn về **“flat memory model có thực sự nhanh hơn không?”** — vì câu trả lời nằm ở alias analysis và locality nhiều hơn bản thân flat address space.