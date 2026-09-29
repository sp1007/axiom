# BOOTSTRAP-023 — Object Representation, Layout, ABI & Representation Contracts

Đây là mảnh ghép còn thiếu giữa **semantic type system** và **machine code**.

Mục tiêu của Axiom nên là:

> **Default layout tự do để compiler tối ưu tối đa; representation chỉ bị khóa khi programmer/ABI thực sự cần.**

Nếu khóa layout quá sớm, Axiom sẽ mang theo rất nhiều hạn chế của C. Nếu tự do quá mức mà không có contract rõ ràng, FFI, MMIO, serialization, SIMD và binary ABI sẽ trở nên nguy hiểm.

---

# 1. Tách 4 tầng

Axiom cần phân biệt tuyệt đối:

```text
                Axiom Type
                    │
                    ▼
             Semantic Value
                    │
                    ▼
             Logical Object
                    │
                    ▼
          Physical Representation
                    │
                    ▼
             Machine Layout
```

Ví dụ:

```axiom
struct Vec3 {
    x: f32
    y: f32
    z: f32
}
```

Semantic chỉ nói:

```text
Vec3 có 3 field f32
```

Không mặc định nói:

```text
offset x = 0
offset y = 4
offset z = 8
size = 12
```

Compiler được quyền chọn representation tốt nhất.

---

# 2. Default struct layout: compiler-controlled

Đây là quyết định tôi khuyến nghị giữ rất mạnh.

```axiom
struct Foo {
    a: u8
    b: u64
    c: u16
}
```

Không cam kết:

```text id="3q1x1y"
a offset 0
b offset 8
c offset 16
```

Compiler có thể reorder field:

```text id="zy5k2d"
b
c
a
padding
```

nếu:

- semantic không thay đổi
- không có `@repr`
- không có ABI contract yêu cầu layout.

---

# 3. Tại sao reorder field đáng giá?

Ví dụ:

```axiom
struct Bad {
    a: u8
    b: u64
    c: u8
}
```

Một layout naïve có thể:

```text
1 + 7 padding + 8 + 1 + 7 padding
= 24 bytes
```

Compiler có thể reorder:

```text
b
a
c
padding
```

thành:

```text
8 + 1 + 1 + 6 padding
= 16 bytes
```

Đối với hàng triệu object, khác biệt này rất lớn.

---

# 4. Nhưng compiler không được reorder semantic field

Reorder physical layout không được làm thay đổi:

```axiom
x.a
x.b
x.c
```

hoặc:

```text
field identity
field type
field ownership
field Drop order
field access semantics
```

Physical order và source order là hai thứ khác nhau.

---

# 5. Drop order vẫn deterministic

Ví dụ:

```axiom
struct Foo {
    a: A
    b: B
    c: C
}
```

Mặc dù compiler layout:

```text
b
c
a
```

Drop semantic vẫn:

```text
c
b
a
```

theo declaration/initialization rule đã khóa.

Không được để layout optimization làm thay đổi resource semantics.

---

# 6. `@repr` là representation contract

Axiom cần một cơ chế rõ ràng:

```axiom
@repr(...)
struct Foo {
    ...
}
```

Nhóm contract chính:

```text
@repr(C)
@repr(transparent)
@repr(packed)
@repr(align(N))
```

và có thể mở rộng sau.

---

# 7. `@repr(C)`

`@repr(C)` có nghĩa:

> Layout phải tương thích với C ABI contract tương ứng của target.

Ví dụ:

```axiom
@repr(C)
struct Point {
    x: f32
    y: f32
}
```

Compiler phải xác định:

```text
size
alignment
field offsets
padding
calling convention interaction
```

theo target ABI.

---

# 8. `@repr(C)` không biến Axiom thành C

Ví dụ:

```axiom
@repr(C)
struct Foo {
    value: Option<i32>
}
```

không tự động có nghĩa:

```text
Foo
```

tương thích với một C type tương ứng.

Chỉ layout của những representation mà ABI định nghĩa mới có contract.

FFI boundary phải xác định type mapping rõ ràng.

---

# 9. `@repr(transparent)`

Dùng cho newtype:

```axiom
@repr(transparent)
distinct UserId: u64
```

Semantic:

```text
UserId
```

vẫn là type khác:

```text
u64
```

nhưng physical representation tương thích với underlying representation trong những ABI contexts được contract cho phép.

Đây là cách cực tốt để có:

```text
type safety
+
zero runtime overhead
```

---

# 10. Newtype không phải alias

Ví dụ:

```axiom
type UserId = u64
```

nếu đây là alias:

```text
UserId == u64
```

Còn:

```axiom
distinct UserId = u64
```

thì:

```text
UserId != u64
```

ở type system.

Nhưng:

```axiom
@repr(transparent)
distinct UserId = u64
```

có thể có representation:

```text
UserId → exactly u64
```

---

# 11. `@repr(packed)`

Đây phải là **unsafe/system-level**.

Ví dụ:

```axiom
@repr(packed)
struct Header {
    tag: u8
    length: u32
}
```

Có thể:

```text
offset(tag) = 0
offset(length) = 1
```

`length` có thể unaligned.

Do đó:

```axiom
let x = header.length
```

không được compiler biến thành một ordinary aligned load nếu target không cho phép.

---

# 12. Packed không được phép phá alignment

Axiom phải xử lý rõ:

```text
packed field
    ↓
possibly unaligned
    ↓
special load/store
```

hoặc compiler reject access nếu target/operation không hỗ trợ.

Không có:

```text
"compiler tự biết chắc hardware chịu được"
```

trong safe semantics.

---

# 13. `@repr(align(N))`

Cho phép yêu cầu minimum alignment:

```axiom
@repr(align(64))
struct CacheLineValue {
    value: u64
}
```

Dùng cho:

- false sharing
- SIMD
- DMA
- hardware
- cache line isolation
- ABI requirements.

Compiler không được hạ alignment xuống thấp hơn contract.

---

# 14. Alignment không đồng nghĩa size

Ví dụ:

```text
align = 64
size  = 64
```

không phải lúc nào cũng bắt buộc.

Semantic:

```text
address % 64 == 0
```

và size do layout algorithm quyết định, subject to ABI/representation constraints.

---

# 15. Layout queries

Axiom cần compile-time:

```axiom
size_of<T>()
align_of<T>()
offset_of<T, field>()
```

Ví dụ:

```axiom
const SIZE = size_of<MyStruct>()
```

Nhưng:

> Chỉ được coi là stable contract nếu representation contract yêu cầu.

Với default struct:

```axiom
size_of<Foo>()
```

vẫn hợp lệ ở compile time.

Nhưng programmer **không được giả định nó giữ nguyên giữa compiler versions/targets** nếu không có ABI/repr contract.

---

# 16. `offset_of` phải chịu cùng quy tắc

Có thể:

```axiom
const O = offset_of<Foo, field>()
```

Nhưng khi source quan sát offset:

```text
representation becomes observable
```

Điều đó không tự động đóng băng layout.

Nếu cần stable layout:

```axiom
@repr(C)
```

hoặc representation contract tương ứng.

---

# 17. Serialization không nên dựa vào raw struct bytes

Đây là điểm quan trọng.

Không nên viết:

```axiom
write_bytes(&foo, size_of<Foo>())
```

để serialize arbitrary Axiom struct.

Vì default layout có thể:

```text
reorder
padding
change
niche
representation
```

Serialization phải dùng explicit format:

```text
encode(foo)
decode(bytes)
```

hoặc một `@repr` contract thích hợp nếu format thực sự là binary layout.

---

# 18. Padding bytes không phải semantic value

Ví dụ:

```text
struct {
    u8
    u64
}
```

có padding.

Padding:

```text
không phải field
không phải value
không phải ownership
```

Compiler không phải duy trì giá trị ổn định của padding trừ khi ABI/unsafe representation contract yêu cầu.

Điều này cho phép:

```text
store merging
vectorization
dead padding elimination
```

---

# 19. Bitwise equality ≠ semantic equality

Ví dụ:

```axiom
struct Foo {
    value: f32
}
```

Không nên mặc định:

```text
memcmp(a, b) == 0
```

là:

```text
a == b
```

Đặc biệt với:

```text
NaN
-0.0
padding
niche
enum representation
```

Semantic equality phải đi qua:

```axiom
a == b
```

nếu type hỗ trợ `Eq`.

---

# 20. Bitwise copy ≠ `Copy`

Ta đã khóa trước:

```text
bitwise copyability
        ≠
semantic Copy
```

Ví dụ một representation có thể copy bằng `memcpy`, nhưng object chứa:

```text
resource ownership
```

thì không thể semantic Copy.

Compiler phải phân biệt:

```text
COPY_VALUE
```

với:

```text
RAW_COPY_BYTES
```

---

# 21. Raw byte reinterpretation

Axiom cần một low-level mechanism:

```text
bitcast<T>()
```

nhưng rất hạn chế.

Phân biệt:

```text
CAST
```

với:

```text
BITCAST
```

### CAST

Thay đổi giá trị theo conversion semantics:

```axiom
x as u32
```

### BITCAST

Giữ nguyên bit pattern, thay đổi interpretation.

```text
u32 bits
    ↓ bitcast
f32
```

Phải thỏa:

```text
size
alignment
valid representation
```

---

# 22. Invalid bit patterns

Đây là vấn đề cực quan trọng với enum/Option.

Không phải mọi bit pattern đều là valid Axiom value.

Ví dụ:

```text
Option<bool>
```

compiler có thể dùng niche representation.

Nếu raw bytes tạo ra bit pattern invalid:

```text
bit pattern
    ↓
invalid Axiom value
```

thì safe code không được tạo ra nó.

Do đó:

```axiom
bitcast<SomeType>(bytes)
```

phải có verification hoặc unsafe boundary.

---

# 23. `MaybeUninit`-style abstraction

Axiom sẽ cần một abstraction tương đương nhưng tôi **không muốn đưa nó thành syntax đặc biệt**.

Có thể có library/system type:

```text
Uninit<T>
```

Semantic:

```text
storage exists
value does not yet exist
```

Ví dụ compiler/runtime implementation:

```text
ALLOC<T>
state = UNINITIALIZED

construct(value)
state = INITIALIZED
```

Điều này cực kỳ hữu ích cho:

- arrays
- Vec growth
- allocators
- object pools
- FFI
- placement construction.

---

# 24. Ownership state phải phân biệt UNINIT

MIR đã có:

```text
UNINIT
INIT
MOVED
DROPPED
```

Nên object representation phải dùng lại model này.

Ví dụ:

```text
slot
 ↓
UNINIT
 ↓ construct
INIT
 ↓ move
MOVED
 ↓ reuse
UNINIT
```

Không có chuyện:

```text
MOVED → DROP
```

trừ khi được reinitialized.

---

# 25. Enum representation

Axiom enum là semantic sum type:

```axiom
enum Result<T, E> {
    Ok(T)
    Err(E)
}
```

Default representation:

```text
compiler-controlled
```

Compiler có thể chọn:

```text
tag + payload
```

hoặc:

```text
niche encoding
```

hoặc:

```text
optimized discriminant
```

---

# 26. Niche optimization

Ví dụ:

```text
Option<Box<T>>
```

Nếu null pointer không phải valid Box value:

```text
null
```

có thể đại diện:

```text
None
```

và non-null pointer:

```text
Some(Box<T>)
```

Do đó:

```text
Option<Box<T>>
```

có thể có cùng size với:

```text
Box<T>
```

Đây là **representation optimization**, không phải semantic rule.

---

# 27. Programmer không được phụ thuộc niche mặc định

Không nên cho phép:

```text
"Option<Box<T>> luôn 8 bytes"
```

trừ khi ABI/representation contract đảm bảo.

Compiler có thể thay đổi niche strategy.

---

# 28. Discriminant

Compiler internal enum representation có thể có:

```text
discriminant
```

nhưng programmer chỉ nên quan sát qua:

```axiom
match
```

hoặc compile-time reflection/query được định nghĩa.

Raw discriminant access chỉ system/representation-level.

---

# 29. Struct field address

Một field:

```axiom
x.field
```

có logical identity.

Địa chỉ:

```axiom
address_of(x.field)
```

là machine-level observation.

Nếu programmer expose address:

```text
layout/address becomes observable
```

compiler phải tôn trọng các constraints tương ứng.

Nhưng điều đó **không nên tự động đóng băng toàn bộ struct layout** nếu chỉ một field address được quan sát.

---

# 30. ABI layout vs internal layout

Đây là một trong những nguyên tắc quan trọng nhất:

```text
Axiom internal ABI
        ≠
C ABI
        ≠
wire format
        ≠
GPU layout
```

Mỗi boundary có contract riêng.

Ví dụ:

```text
Internal Axiom
→ optimized

extern "C"
→ C ABI

@repr(C)
→ C layout

network packet
→ explicit serialization format

GPU buffer
→ GPU layout contract
```

Không dùng một layout cho tất cả.

---

# 31. ABI là contract ở function boundary

Ví dụ:

```axiom
fn add(a: i32, b: i32) -> i32
```

Axiom ABI có thể truyền:

```text
register
```

C ABI trên một target cũng có thể dùng register.

Nhưng không được giả định hai ABI luôn giống nhau.

Do đó:

```axiom
extern "C" fn c_add(...)
```

là explicit boundary.

---

# 32. Axiom ABI có quyền tối ưu mạnh hơn C ABI

Ví dụ:

```axiom
struct Vec4 {
    x: f32
    y: f32
    z: f32
    w: f32
}
```

Internal ABI có thể:

```text
pass in SIMD register
```

hoặc:

```text
two registers
```

hoặc:

```text
sret
```

tùy target.

Programmer không cần biết.

---

# 33. C ABI phải đóng băng representation

Nếu:

```axiom
@repr(C)
struct CPoint {
    x: f32
    y: f32
}
```

và:

```axiom
extern "C" fn foo(p: CPoint)
```

thì compiler phải dùng C ABI layout/calling convention.

Không được optimizer tự ý:

```text
reorder fields
change argument ABI
```

---

# 34. `extern "C"` không đủ cho arbitrary Axiom type

Không nên cho:

```axiom
extern "C" fn foo(x: String)
```

mà compiler tự đoán.

String có thể chứa:

```text
pointer
length
capacity
allocator identity
ownership
UTF-8 invariant
```

C không biết semantic đó.

Compiler nên reject hoặc yêu cầu explicit FFI representation.

Ví dụ:

```axiom
extern "C" fn foo(ptr: *const u8, len: usize)
```

trong unsafe/system API.

---

# 35. FFI-safe type set

Axiom nên có khái niệm compiler-known:

```text
FFI-safe
```

Ví dụ:

```text
bool?      target ABI dependent
integers
floats
pointers
@repr(C) structs
@repr(transparent) newtypes
C-compatible enums
```

Còn:

```text
Vec
String
Arc
Mutex
closure
Future
trait object
```

không FFI-safe mặc định.

---

# 36. Function pointers và closures

Function pointer:

```axiom
fn(i32) -> i32
```

có ABI contract.

Closure:

```axiom
|x| x + offset
```

là object gồm:

```text
environment
+
call behavior
```

Không được mặc định tương đương C function pointer.

Non-capturing closure có thể decay thành function pointer nếu ABI/semantics cho phép.

Capturing closure cần explicit adapter nếu truyền qua FFI.

---

# 37. Trait object representation

`dyn Trait` là explicit dynamic representation.

Conceptually:

```text
data pointer
+
dispatch metadata
```

Nhưng:

> layout cụ thể không phải semantic API trừ khi ABI contract yêu cầu.

Không nên cho programmer assume:

```text
dyn Trait = {ptr, vtable}
```

ở safe language level.

Đó là implementation model.

---

# 38. No mandatory object header

Axiom tiếp tục giữ:

```text
object
≠
header
```

Một struct bình thường không tự động có:

```text
type_id
refcount
vtable
GC mark
mutex
```

Nếu cần:

```text
Arc
dyn Trait
GC-like external runtime
```

thì abstraction tự chứa metadata.

---

# 39. Generic layout

Ví dụ:

```axiom
struct Pair<T, U> {
    first: T
    second: U
}
```

Mỗi instantiation có thể có layout khác:

```text
Pair<u8,u64>
Pair<u64,u8>
Pair<Vec,u32>
```

Compiler có thể monomorphize và optimize layout.

Không có requirement rằng:

```text
Pair<T,U>
```

phải có một universal runtime representation.

---

# 40. ZST

Zero-sized types vẫn được hỗ trợ.

Ví dụ:

```axiom
struct Marker {}
```

có thể:

```text
size = 0
alignment = 1
```

hoặc target/compiler-specific constraints nếu ABI yêu cầu.

ZST không nhất thiết cần unique physical address.

---

# 41. Empty structs và address identity

Hai ZST:

```axiom
a: Marker
b: Marker
```

không nên mặc định có distinct physical storage.

Nếu programmer cần stable identity:

```text
storage identity
```

phải được yêu cầu explicitly.

Đây là một nơi Axiom khác C/C++ khá rõ.

---

# 42. Arrays

```axiom
[T; N]
```

semantic:

```text
N elements
same type
ordered indexing
```

Default representation có thể là contiguous inline storage vì đây là semantic cần thiết cho array.

Do đó:

```text
sizeof([T;N]) = N * sizeof(T)
```

với các alignment/padding rules thích hợp.

Khác với struct, thứ tự element không thể reorder.

---

# 43. Slice/View representation

`view<T>` semantic:

```text
contiguous readable region
length
provenance
```

Machine representation thường:

```text
pointer + length
```

nhưng đây vẫn là ABI implementation detail.

`mut_view<T>` tương tự nhưng có exclusive-write capability.

Compiler có thể optimize:

```text
pointer + known length
```

thành:

```text
pointer + constant
```

hoặc eliminate length nếu bounds proof đầy đủ.

---

# 44. Pointer provenance

Raw pointer:

```text
*const T
*mut T
```

phải có provenance semantics.

Không nên định nghĩa:

```text
integer address
=
valid pointer
```

Ví dụ:

```axiom
let n: usize = 0x1234
```

không tự động biến thành:

```text
*mut Foo
```

trong safe code.

Numeric address manipulation thuộc unsafe/system domain.

---

# 45. Integer ↔ pointer conversion

Có thể hỗ trợ ở unsafe:

```axiom
ptr as usize
usize as *mut T
```

nhưng compiler phải coi:

```text
provenance
alignment
validity
lifetime
address-space
```

là programmer responsibility.

Điều này đặc biệt quan trọng cho:

- MMIO
- kernel
- embedded
- OS
- custom allocator.

---

# 46. Device/GPU layout

GPU storage không nên dùng mặc định Axiom struct layout nếu shader/driver yêu cầu layout khác.

Ví dụ:

```text
CPU struct
       ↓
GPU buffer
```

cần explicit contract:

```text
Std430
Std140
Metal layout
D3D layout
CUDA layout
custom packed layout
```

Có thể sau này:

```axiom
@repr(gpu(...))
```

nhưng không cần khóa syntax ngay trong Core.

---

# 47. Serialization representation

Tương tự:

```text
@repr(C)
```

không nên được dùng làm universal serialization system.

Nên có:

```text
BinaryEncode
BinaryDecode
```

hoặc comptime derive:

```axiom
@derive(BinaryEncode, BinaryDecode)
```

Compiler/std có thể generate serializer biết:

```text
field order
endianness
integer width
padding
version
optional fields
```

---

# 48. Endianness

Axiom default semantic integer không phụ thuộc endian.

Target có:

```text
little
big
```

Representation-sensitive code phải explicit:

```axiom
to_le()
to_be()
from_le()
from_be()
```

Compiler có thể optimize trên target native endian.

---

# 49. `@repr(C)` + endian

`@repr(C)` không tự quyết định network byte order.

C layout:

```text
field offsets
alignment
ABI
```

khác:

```text
wire endian
```

Không trộn hai khái niệm.

---

# 50. Representation contracts có hierarchy

Tôi đề xuất:

```text
Default
  ↓
Target representation
  ↓
Explicit @repr
  ↓
ABI contract
  ↓
Unsafe machine-level observation
```

Càng xuống thấp:

```text
compiler freedom ↓
programmer responsibility ↑
```

Đây là một nguyên tắc rất đẹp cho Axiom.

---

# 51. Representation Contract Matrix

| Representation | Reorder field | Change size | Change alignment | Stable ABI |
|---|---:|---:|---:|---:|
| Default | Có | Có | Có | Không |
| `@repr(C)` | Không | Theo C ABI | Theo C ABI | Có, trong contract |
| `@repr(transparent)` | Không | Theo underlying | Theo contract | Có |
| `@repr(packed)` | Không | Contract | Giảm theo packed | Có |
| `@repr(align(N))` | Có thể | Có thể | ≥ N | Có alignment |
| GPU explicit | Theo GPU contract | Theo contract | Theo contract | Theo target |
| Wire format | Theo schema | Theo schema | Theo schema | Có |

---

# 52. Representation và optimizer

Compiler phải biết distinction:

```text
Semantic Value
```

và:

```text
Representation Observation
```

Ví dụ optimizer có thể:

```text
struct scalarize
```

nếu:

```text
address không observable
representation không observable
ABI không yêu cầu aggregate
```

Nhưng nếu:

```text
@repr(C)
extern fn(...)
```

thì phải materialize representation đúng contract.

---

# 53. ABI lowering pipeline

Tôi đề xuất pipeline chính thức:

```text
Typed MIR
   ↓
Semantic Optimization
   ↓
Representation Analysis
   ↓
Layout
   ↓
ABI Classification
   ↓
ABI MIR
   ↓
LIR
```

Không làm layout quá sớm.

Đây là điểm rất quan trọng.

Nếu layout xảy ra ngay sau type checking, compiler sẽ khó scalarize/reorder/eliminate storage.

---

# 54. ABI Classification

ABI layer quyết định:

```text
PASS_REG
PASS_STACK
PASS_INDIRECT
SRET
SPLIT
COERCE
RETURN_REG
RETURN_MEMORY
```

Ví dụ:

```axiom
fn f(x: SmallStruct) -> SmallStruct
```

có thể trở thành:

```text
register → register
```

hoặc:

```text
hidden sret pointer
```

tùy target.

---

# 55. Internal ABI không cần C compatibility

Axiom compiler có thể có:

```text
Axiom ABI
```

tối ưu cho:

```text
Axiom ↔ Axiom
```

và:

```text
C ABI
```

cho:

```text
Axiom ↔ C
```

Điều này cho phép Axiom:

- optimize aggregate passing
- specialize generics
- pass niche values efficiently
- use target-specific registers
- tail-call optimize

mà không bị C ABI trói buộc.

---

# 56. Stable ABI cho Axiom libraries

Một vấn đề khác:

Nếu:

```text
libA.ax
```

được build bằng compiler 1.0 rồi application build bằng compiler 1.1,

không nên mặc định mọi internal Axiom ABI đều stable.

Có thể có:

```text
Axiom ABI version
```

hoặc:

```text
stable extern ABI
```

cho binary distribution.

Ban đầu nên:

> **Stable C ABI first; stable Axiom ABI only after explicit ABI versioning design.**

Điều này giảm bootstrap complexity.

---

# 57. Object file symbol ABI

Tên function:

```axiom
fn foo(...)
```

không nhất thiết xuất hiện symbol là:

```text
foo
```

Compiler cần deterministic mangling:

```text
_axiom_...
```

bao gồm khi cần:

```text
module
type parameters
generic instantiation
ABI
```

Nhưng:

```text
@export("foo")
```

có thể freeze external symbol.

---

# 58. Public ≠ exported

Tiếp tục nguyên tắc:

```text
pub
```

chỉ có nghĩa:

```text
visible to source modules/packages
```

Không có nghĩa:

```text
ELF/PE/Mach-O exported symbol
```

Muốn export:

```axiom
@export("my_api")
pub extern "C" fn ...
```

hoặc contract tương ứng.

---

# 59. Dynamic libraries

Shared library ABI phải freeze:

```text
symbol
calling convention
layout
alignment
ownership
allocation domain
error model
threading assumptions
```

Đặc biệt:

```text
Axiom allocator
≠
foreign allocator
```

Không được:

```text
malloc() in DLL A
free() in DLL B
```

trừ khi ABI contract explicitly guarantees compatible allocator ownership.

---

# 60. Representation + allocator ownership

Ví dụ:

```axiom
extern "C" fn create() -> *mut Foo
```

phải có contract:

```text
who allocates?
who frees?
which allocator?
which ABI?
alignment?
lifetime?
```

Không được để FFI "đoán".

Đây nối trực tiếp với BOOTSTRAP-022.

---

# 61. Core principle mới

Tôi đề xuất khóa:

> **Representation is private unless explicitly contracted.**

Nghĩa là:

```text
Default Axiom type
    ↓
semantic identity
    ↓
representation private
```

Chỉ khi programmer viết:

```text
@repr(...)
extern
FFI
ABI
unsafe representation API
```

thì physical representation mới trở thành contract.

---

# 62. Invariants BOOTSTRAP-023

```text id="4v7nq2"
AREPR-20 — Semantic type identity is distinct from physical representation.
AREPR-21 — Default struct layout is compiler-controlled.
AREPR-22 — Default field order is not an ABI guarantee.
AREPR-23 — Physical field reordering cannot change semantic field identity.
AREPR-24 — Drop order is independent of physical field layout.
AREPR-25 — Padding is not a semantic field.
AREPR-26 — Padding bytes have no default semantic value.
AREPR-27 — Semantic equality is distinct from bytewise equality.
AREPR-28 — Bitwise copyability does not imply Copy.
AREPR-29 — Raw bit representation is distinct from semantic value representation.
AREPR-30 — Invalid bit patterns cannot be created by safe code.
AREPR-31 — Enum representation is compiler-controlled by default.
AREPR-32 — Niche optimization is a representation optimization.
AREPR-33 — Niche layout is not stable without an explicit contract.
AREPR-34 — Array element order is semantically fixed.
AREPR-35 — Array representation is contiguous unless an explicit future abstraction says otherwise.
AREPR-36 — view<T> representation is implementation-controlled.
AREPR-37 — mut_view<T> representation is implementation-controlled.
AREPR-38 — Raw pointers carry machine-level provenance requirements.
AREPR-39 — Integer values are not automatically valid pointers.
AREPR-40 — @repr(C) establishes a C-compatible representation contract.
AREPR-41 — @repr(C) does not imply universal serialization compatibility.
AREPR-42 — @repr(transparent) preserves distinct type identity.
AREPR-43 — @repr(transparent) may preserve ABI representation of its underlying type.
AREPR-44 — @repr(packed) may create unaligned fields.
AREPR-45 — Packed access must respect target alignment semantics.
AREPR-46 — @repr(align(N)) establishes a minimum alignment contract.
AREPR-47 — Representation contracts constrain optimizer freedom.
AREPR-48 — Representation observation is distinct from semantic access.
AREPR-49 — size_of is compile-time information.
AREPR-50 — offset_of is compile-time information.
AREPR-51 — Representation stability requires an explicit contract.
AREPR-52 — Internal Axiom ABI is distinct from C ABI.
AREPR-53 — FFI ABI must be explicit.
AREPR-54 — Arbitrary Axiom types are not implicitly FFI-safe.
AREPR-55 — Foreign allocation ownership must be explicit.
AREPR-56 — Foreign exceptions cannot cross Axiom ABI implicitly.
AREPR-57 — Public visibility does not imply binary export.
AREPR-58 — Binary export requires an explicit symbol contract.
AREPR-59 — Generic instantiations may have distinct physical representations.
AREPR-60 — Capturing closures are not ordinary C function pointers.
AREPR-61 — Dynamic trait representation is implementation-controlled unless ABI-frozen.
AREPR-62 — No ordinary Axiom object requires a hidden object header.
AREPR-63 — Representation optimization may erase semantic aggregates.
AREPR-64 — ABI lowering occurs after semantic optimization.
AREPR-65 — ABI classification is target-specific.
AREPR-66 — Stable external ABI requires explicit versioning/contract.
AREPR-67 — Axiom ABI is not automatically stable across compiler versions.
AREPR-68 — Wire representation is distinct from memory representation.
AREPR-69 — Endianness is a representation property, not a semantic integer property.
AREPR-70 — GPU layout is a distinct representation domain.
AREPR-71 — Serialization must not depend on unspecified default layout.
AREPR-72 — Representation is private unless explicitly contracted.
```

---

# 63. Sau BOOTSTRAP-023, Axiom đã có 3 lớp rất rõ

```text
                 SEMANTIC
                    │
      ┌─────────────┼──────────────┐
      │             │              │
 Ownership      Capability     Memory Model
      │             │              │
      └─────────────┼──────────────┘
                    ↓
              OBJECT MODEL
                    ↓
             REPRESENTATION
                    ↓
                  ABI
                    ↓
             MACHINE CODE
```

Điều này giải quyết một mâu thuẫn mà nhiều ngôn ngữ systems gặp phải:

### Nếu representation luôn tự do

→ tối ưu tốt nhưng FFI khó.

### Nếu representation luôn cố định

→ FFI dễ nhưng compiler bị trói.

Axiom chọn:

> **Tự do mặc định, contract khi cần.**

---

## Một quyết định tôi đặc biệt khuyến nghị giữ

Đừng biến:

```text
struct
```

thành một "memory layout declaration".

`struct` trước hết là:

> **semantic aggregate type.**

Còn:

```text
@repr(C)
@repr(packed)
@repr(align)
extern
```

mới nói:

> **physical representation phải tuân theo contract này.**

Đây là nền tảng để compiler có thể thực hiện những optimization rất mạnh mà programmer vẫn có một escape hatch hoàn chỉnh cho:

- C ABI
- OS structures
- network packets
- hardware registers
- SIMD
- GPU buffers
- shared-memory IPC
- binary file formats
- embedded systems.

---

### Bước tiếp theo hợp lý

Sau khi **memory + allocation + representation + ABI** đã được nối thành một hệ thống, phần tiếp theo nên là:

**BOOTSTRAP-024 — Pointer, Reference, Handle & Access Syntax**

Đây sẽ là chỗ quyết định trực tiếp UX của Axiom: **programmer thực tế có phải nhìn thấy `*`, `&`, pointer/reference, dereference, lifetime... thường xuyên hay không**, và làm sao giữ được toàn bộ sức mạnh C/C++ nhưng code hằng ngày vẫn đơn giản.