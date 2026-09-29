# AXIOM LANGUAGE SPECIFICATION v0.1 — Part VIII
## Type System · Layout · Representation · ABI

Phần này khóa một nguyên tắc rất quan trọng:

> **Type semantics, memory representation và ABI là ba lớp khác nhau.**

Axiom phải vừa có type system mạnh, vừa cho compiler tự do tối ưu layout khi ABI không yêu cầu layout cố định.

---

# 1. Ba lớp cần tách biệt

```text
TYPE SEMANTICS
      ↓
DATA REPRESENTATION
      ↓
ABI REPRESENTATION
      ↓
MACHINE REPRESENTATION
```

Ví dụ:

```axiom
struct User {
    id: u64
    active: bool
}
```

Về semantic:

```text
User = { id, active }
```

Nhưng compiler có thể chọn layout tối ưu.

Chỉ khi programmer yêu cầu:

```axiom
@repr(C)
struct User { ... }
```

layout C-compatible mới trở thành contract.

---

# 2. Type identity

Hai type có cùng representation không có nghĩa là cùng type.

```axiom
type UserId = u64
```

là alias:

```text
UserId == u64
```

Trong khi:

```axiom
struct UserId(u64)
struct ProductId(u64)
```

là hai type khác nhau.

Không thể:

```axiom
let p: ProductId = user_id
```

nếu không explicit conversion.

---

# 3. Type alias

```axiom
type UserId = u64
```

không tạo runtime wrapper.

Compiler xem:

```text
UserId
```

và:

```text
u64
```

là cùng semantic type.

---

# 4. Newtype

```axiom
struct UserId(u64)
```

tạo type identity mới.

Nhưng compiler có thể biểu diễn nó giống `u64`.

Nếu không có ABI/representation requirement:

```text
UserId
→ machine u64
```

không có overhead.

---

# 5. Newtype là abstraction rất quan trọng

Thay vì class:

```text
class UserId
```

Axiom dùng:

```axiom
struct UserId(u64)
```

và có thể định nghĩa behavior:

```axiom
impl UserId {
    fn value(self) -> u64 {
        self.0
    }
}
```

---

# 6. Primitive types

Core v0.1:

```text
bool

i8   i16   i32   i64
u8   u16   u32   u64

isize
usize

f32
f64
```

`i128/u128` có thể bổ sung sau mà không phá kiến trúc hiện tại.

---

# 7. `usize` / `isize`

`usize` có kích thước phù hợp pointer width của target.

Ví dụ:

```text
x86-64 → usize = 64-bit
ARM64  → usize = 64-bit
x86-32 → usize = 32-bit
```

Nó dùng cho:

```text
array index
length
allocation size
pointer-sized quantities
```

---

# 8. `u64` không phụ thuộc target

```text
u64
```

luôn có width 64-bit.

Do đó:

```text
usize ≠ u64
```

dù trên máy 64-bit representation có thể giống nhau.

---

# 9. C ABI integer types

FFI cần:

```text
c_int
c_uint
c_long
c_ulong
c_size
...
```

Đây là target-specific aliases/library types.

Không nên dùng `i32` thay thế `c_int` một cách mặc định.

---

# 10. Boolean

`bool` chỉ có:

```text
true
false
```

Không có:

```text
if (42)
```

Axiom không có implicit truthiness.

---

# 11. Integer conversion

Không implicit:

```axiom
let x: i64 = some_i32
```

nếu không có conversion semantics phù hợp.

Phải:

```axiom
let x: i64 = some_i32 as i64
```

---

# 12. Vì sao?

Tránh conversion graph phức tạp:

```text
i8
 ↓
i16
 ↓
i32
 ↓
i64
 ↓
f64
```

Compiler không phải đoán programmer muốn conversion nào.

---

# 13. Numeric literals

Literal:

```axiom
42
```

ban đầu là untyped numeric literal.

Context:

```axiom
let x: u64 = 42
```

cho phép literal được instantiate thành `u64`.

Đây không phải implicit conversion của một runtime value.

---

# 14. Default numeric type

Nếu không có constraint:

```axiom
let x = 42
```

v0.1 có thể default:

```text
i32
```

Tương tự floating literal:

```axiom
let x = 1.5
```

default:

```text
f64
```

---

# 15. Float

`f32`/`f64` có semantics IEEE-like phù hợp target.

Axiom không mặc định bật:

```text
fast-math
```

vì fast-math có thể thay đổi observable numerical behavior.

---

# 16. Unit

```axiom
()
```

là giá trị duy nhất của:

```text
unit
```

Function:

```axiom
fn log(x: i32) {
    ...
}
```

có return type semantic:

```text
unit
```

---

# 17. Never

`never` biểu diễn computation không return bình thường.

Ví dụ:

```axiom
fn fail() -> never {
    panic("fatal")
}
```

`never` có thể coerce vào context cần một type vì computation không tạo value.

Ví dụ:

```axiom
let x: i32 =
    if condition {
        42
    } else {
        fail()
    }
```

---

# 18. Tuple

```axiom
let p = (10, 20)
```

type:

```text
(i32, i32)
```

Truy cập:

```axiom
p.0
p.1
```

Tuple không có field name.

---

# 19. Struct

```axiom
struct Vec2 {
    x: f32
    y: f32
}
```

là aggregate type có named fields.

Struct không có class identity.

---

# 20. Struct behavior

Behavior nằm trong function/trait:

```axiom
impl Vec2 {
    fn length(self: view<Self>) -> f32 {
        ...
    }
}
```

Call:

```axiom
v.length()
```

chỉ là syntax sugar cho:

```axiom
length(view(v))
```

theo receiver semantics.

---

# 21. Class không tồn tại trong Core

Không có:

```text
class
inheritance
virtual method table by default
object header
```

Điều này không làm Axiom yếu hơn.

Behavior được tách khỏi data.

---

# 22. Trait

Trait mô tả behavioral contract:

```axiom
trait Display {
    fn display(self: view<Self>) -> Text
}
```

Type thực hiện trait:

```axiom
impl Display for User {
    ...
}
```

---

# 23. Trait không có object header

Static dispatch:

```axiom
fn print<T: Display>(x: view<T>) {
    ...
}
```

có thể monomorphize trực tiếp.

Không cần:

```text
object header
vtable pointer
runtime type ID
```

---

# 24. `dyn Trait`

Dynamic dispatch phải explicit:

```axiom
dyn Display
```

Conceptually:

```text
data pointer
+
dispatch pointer
```

Không yêu cầu object header.

---

# 25. Ownership của dyn Trait

Các khái niệm độc lập:

```text
Box<dyn Display>
```

→ owning dynamic object.

```text
view<dyn Display>
```

→ non-owning capability.

Do đó:

```text
dynamic dispatch
≠
ownership
```

---

# 26. `impl Trait`

Ví dụ:

```axiom
fn make_service() -> impl Service {
    ConcreteService {}
}
```

`impl Service` là static opaque abstraction.

Không phải dynamic dispatch.

Compiler vẫn biết concrete implementation trong compilation context.

---

# 27. Public `impl Trait`

Nếu public API trả:

```axiom
pub fn make() -> impl Service
```

concrete type có thể được ẩn khỏi source API nhưng semantic contract vẫn phải xác định.

Không được dùng `impl Trait` để tạo runtime dynamic dispatch ngầm.

---

# 28. Generic type

```axiom
struct Box<T> {
    value: T
}
```

`Box<i32>` và:

```text
Box<f64>
```

là các instantiated types khác nhau.

Compiler có thể monomorphize.

---

# 29. Monomorphization

Ví dụ:

```axiom
fn max<T: Ord>(a: T, b: T) -> T
```

compiler có thể tạo:

```text
max<i32>
max<u64>
max<MyType>
```

chỉ khi thực sự cần.

---

# 30. Code sharing

Monomorphization không bắt buộc compiler phải sinh một bản machine code cho từng type.

Compiler có thể phát hiện:

```text
max<u32>
max<UserId>
```

có representation/semantics tương đương phù hợp và share code.

Đây là implementation optimization.

---

# 31. Generic semantics không phụ thuộc optimization

Programmer không được viết logic phụ thuộc:

```text
"compiler có specialize hay không"
```

Ví dụ specialization không được thay đổi behavior.

---

# 32. Associated type

```axiom
trait Iterator {
    type Item

    fn next(self: mut_view<Self>) -> Option<Self.Item>
}
```

Associated type là compile-time relation.

Không phải runtime type metadata.

---

# 33. Sized

Generic parameter mặc định:

```text
T: Sized
```

Ví dụ:

```axiom
fn process<T>(x: T)
```

ngầm yêu cầu T có compile-time-known size phù hợp ordinary value storage.

---

# 34. `?Sized`

Có thể cho phép abstraction nhận unsized type:

```text
T: ?Sized
```

Nhưng unsized values không thể tồn tại như ordinary inline value nếu representation không xác định.

Chúng thường đi qua:

```text
view<T>
Box<T>
dyn Trait
```

hoặc abstraction tương đương.

---

# 35. View với unsized type

Một:

```text
view<T>
```

có thể tham chiếu đến unsized `T`.

Representation sẽ cần metadata nếu cần.

Ví dụ:

```text
view<dyn Trait>
```

conceptually:

```text
data pointer
+
metadata/dispatch pointer
```

---

# 36. Array

```axiom
Array<T, N>
```

có size:

```text
N * sizeof(T)
```

với alignment/layout thích hợp.

Array là inline value.

---

# 37. Array không tự decay thành pointer

Khác C:

```text
Array<T,N>
```

không tự động biến thành:

```text
T*
```

Khi cần view:

```axiom
view(array)
```

hoặc:

```axiom
array[..]
```

---

# 38. View

`view<T>` là non-owning capability.

Representation phổ biến:

```text
pointer
```

nhưng semantic model không bắt buộc đúng một machine representation.

---

# 39. Sequence view

Khi cần length:

```text
view<T>
```

có thể biểu diễn logical region:

```text
pointer + length
```

hoặc compiler intrinsic tương đương.

Điều quan trọng là semantic contract:

```text
owner
region
access
validity
```

---

# 40. `mut_view<T>`

`mut_view<T>` là exclusive write capability.

Không Copy.

Assignment:

```axiom
let b = a
```

với `mut_view` là capability move.

---

# 41. Slice syntax

```axiom
a[1..4]
```

tạo view/capability theo context.

Ví dụ:

```axiom
fn process(x: view<i32>) { ... }

process(a[1..4])
```

không cần allocation.

---

# 42. Enum

```axiom
enum Message {
    Quit,
    Text(Text),
    Move { x: i32, y: i32 },
}
```

là algebraic data type.

Mỗi value có:

```text
discriminant
+
variant payload
```

theo semantic model.

---

# 43. Enum layout không cố định

Compiler được phép chọn:

```text
tag + payload
```

hoặc tối ưu layout nếu ABI không bị freeze.

Ví dụ:

```text
niche optimization
```

---

# 44. Option

```axiom
Option<T>
```

conceptually:

```text
Some(T)
None
```

Nhưng representation có thể được tối ưu.

Ví dụ pointer-like T có thể dùng null/niche nội bộ.

Programmer không được phụ thuộc vào representation đó.

---

# 45. `Option<NonNull<T>>`

Compiler có thể encode:

```text
None
```

bằng một invalid/niche value nếu type semantics cho phép.

Nhưng:

> Đây là compiler representation optimization, không phải `null` trở thành safe value trong Axiom.

---

# 46. Result

```axiom
Result<T, E>
```

conceptually:

```text
Ok(T)
Err(E)
```

có thể được layout tối ưu giống enum.

Không cần heap.

---

# 47. Enum discriminant

Programmer không được giả định:

```text
Message.Quit == 0
```

trừ khi representation được explicit.

Nếu cần C-like numeric representation:

```axiom
@repr(C)
```

hoặc representation contract phù hợp.

---

# 48. Recursive types

Không cho phép recursive inline layout vô hạn:

```axiom
struct Node {
    next: Node
}
```

→ reject.

Phải có finite indirection:

```axiom
struct Node {
    next: Option<Box<Node>>
}
```

---

# 49. Recursive enum

Đây cũng áp dụng:

```axiom
enum Tree {
    Leaf(i32),
    Node(Tree, Tree),
}
```

→ representation vô hạn.

Cần:

```axiom
enum Tree {
    Leaf(i32),
    Node(Box<Tree>, Box<Tree>),
}
```

---

# 50. Zero-sized types

Axiom hỗ trợ ZST:

```text
struct Marker {}
```

size semantic:

```text
0
```

nhưng vẫn có type identity.

Compiler có thể không allocate physical bytes cho ZST.

---

# 51. ZST và identity

Nếu programmer cần stable storage identity:

```text
Marker
```

không tự tạo physical address độc nhất.

Storage identity chỉ có ý nghĩa khi storage contract yêu cầu.

---

# 52. Empty struct

```axiom
struct Unit {}
```

khác:

```text
()
```

về type identity nhưng có thể có cùng representation size.

---

# 53. Alignment

Mỗi type có:

```text
size
alignment
```

Compiler có thể padding aggregate để thỏa alignment.

---

# 54. Padding

Ví dụ:

```axiom
struct S {
    a: u8
    b: u64
}
```

không có guarantee:

```text
sizeof(S) == 9
```

Compiler có thể đặt padding.

---

# 55. Field order

Với ordinary struct:

```text
struct S {
    a: u8
    b: u64
}
```

field order là semantic field identity:

```text
s.a
s.b
```

nhưng physical order không nhất thiết là source order nếu ABI/layout chưa freeze.

Compiler có thể reorder fields để giảm padding.

---

# 56. Khi nào field order phải cố định?

Khi dùng:

```axiom
@repr(C)
```

hoặc representation contract tương đương.

Khi đó layout phải obey C ABI rules.

---

# 57. `@repr(C)`

```axiom
@repr(C)
struct Point {
    x: f32
    y: f32
}
```

yêu cầu C-compatible layout.

Điều này hữu ích cho:

```text
FFI
shared memory
hardware structures
stable binary interfaces
```

---

# 58. `@repr(transparent)`

Dùng cho single-field wrapper:

```axiom
@repr(transparent)
struct UserId(u64)
```

Cho phép ABI-compatible representation với underlying field trong những context được representation contract cho phép.

---

# 59. `@repr(packed)`

Có thể hỗ trợ:

```axiom
@repr(packed)
struct Header {
    ...
}
```

nhưng đây là unsafe/system-level.

Lý do:

```text
packed field
→ misaligned address
```

Không được tạo aligned reference/capability sai.

Compiler phải:
- generate unaligned access, hoặc
- yêu cầu unsafe/system access.

---

# 60. `@align`

```axiom
@align(64)
struct CacheAligned<T> {
    value: T
}
```

yêu cầu minimum alignment.

Alignment không được nhỏ hơn ABI requirement của field theo cách tạo invalid layout.

---

# 61. Layout query

Compiler/tooling nên cung cấp:

```text
axiom inspect layout Type
```

Ví dụ:

```text
Type: User
size: 24
align: 8

field id:
    offset: 0

field name:
    offset: 8
```

Điều này rất quan trọng cho systems programming.

---

# 62. Layout không phải ABI

Một type có:

```text
size = 16
```

không có nghĩa:

```text
FFI ABI = 16-byte value
```

ABI còn phụ thuộc:
- calling convention
- registers
- stack
- return convention
- aggregate classification.

---

# 63. Calling convention

Axiom có:

```text
axiom
C
system
```

ở v0.1.

Có thể thêm:

```text
stdcall
fastcall
vectorcall
wasm
aapcs
...
```

khi target yêu cầu.

---

# 64. Native Axiom ABI

`axiom` ABI là compiler-defined native ABI.

Ưu tiên:

```text
performance
register passing
target optimization
```

Không đảm bảo stable binary compatibility giữa compiler versions nếu không có explicit ABI version.

---

# 65. C ABI

```axiom
extern "C" fn add(a: i32, b: i32) -> i32
```

yêu cầu C calling convention.

Nếu export:

```axiom
@export("add")
extern "C" fn add(...) -> ...
```

thì symbol có external linkage.

---

# 66. `pub` không đồng nghĩa exported symbol

```axiom
pub fn foo()
```

chỉ có nghĩa public source API.

Không tự động:

```text
ELF exported symbol
PE export
Mach-O external API
```

Muốn linker-visible:

```axiom
@export("foo")
```

---

# 67. Function pointer

Function type:

```text
fn(i32, i32) -> i32
```

có thể được biểu diễn bằng machine function pointer khi phù hợp.

Nhưng function pointer ABI phải xác định calling convention.

---

# 68. Closure

Closure:

```axiom
|x| x + offset
```

conceptually:

```text
environment
+
call operation
```

Compiler có thể biểu diễn thành:

```text
struct Environment
+
function pointer
```

nhưng không bắt buộc nếu closure không escape.

---

# 69. Non-capturing closure

Closure không capture:

```axiom
|x| x + 1
```

có thể lower thành function pointer.

Capturing closure:

```axiom
|x| x + offset
```

không tự động chuyển thành C function pointer.

---

# 70. C callback

Muốn truyền callback C:

```text
extern "C" fn(...)
```

Capturing closure không thể implicit convert.

Phải dùng explicit context:

```text
callback function pointer
+
void* context
```

hoặc wrapper abstraction.

---

# 71. `dyn Trait` ABI

Conceptually:

```text
dyn Trait
=
data pointer
+
dispatch metadata
```

Nhưng exact layout không phải stable ABI nếu không có explicit representation contract.

---

# 72. Generic ABI

Generic function:

```axiom
fn foo<T>(x: T)
```

không tự có stable external ABI cho mọi T.

Nếu cần FFI:

```text
monomorphic wrapper
+
explicit repr
```

là cách an toàn.

---

# 73. `extern "C"` generic

Không cho:

```axiom
extern "C" fn foo<T>(x: T)
```

trở thành C ABI trực tiếp nếu representation của T chưa được xác định.

Compiler phải yêu cầu constraints/representation đủ mạnh hoặc reject.

---

# 74. Aggregate return

Ví dụ:

```axiom
fn make_vec() -> Vec4
```

ABI có thể trả bằng:

```text
registers
hidden return pointer
stack
```

tùy target và ABI.

Programmer không cần biết.

---

# 75. Caller-allocated return

Compiler có thể lower:

```text
return LargeStruct
```

thành:

```text
caller provides result storage
callee initializes it
```

nếu ABI yêu cầu.

Đây là implementation detail.

---

# 76. Move và ABI return

```axiom
fn make() -> LargeResource
```

không có nghĩa:

```text
physical copy
```

Return là:

```text
semantic ownership transfer
```

ABI có thể dùng:

```text
register
sret
caller allocation
```

mà không thay đổi semantic Move.

---

# 77. Copy và ABI

`Copy` cũng không bắt buộc physical copy.

Compiler có thể:
- truyền register
- scalarize
- eliminate duplicate
- reuse value

miễn là value semantics đúng.

---

# 78. `bit_cast`

Axiom hỗ trợ explicit bit reinterpretation:

```axiom
let bits = bit_cast<u32>(float_value)
```

Điều kiện:
- source/destination representation compatible về size/alignment/bit semantics
- không phải semantic conversion.

---

# 79. `as`

```axiom
x as u64
```

là semantic conversion.

Ví dụ:

```text
i32 → i64
f32 → f64
enum → integer
```

nếu conversion được định nghĩa.

---

# 80. `bit_cast` khác `as`

```text
as
    semantic conversion

bit_cast
    same bits, different interpretation
```

Không được dùng `bit_cast` để lách type safety.

---

# 81. Pointer conversion

Raw pointer conversion:

```text
addr_cast
ptr_cast
```

là unsafe/system-level khi có thể tạo invalid pointer semantics.

Không có implicit:

```text
T → *mut T
```

---

# 82. Không có unrestricted `transmute`

Axiom không đưa:

```text
transmute<T,U>
```

vào Core.

Thay bằng các operation có semantics cụ thể:

```text
bit_cast
ptr_cast
addr_cast
reinterpret_bytes
```

Mỗi operation có điều kiện rõ ràng.

---

# 83. Representation stability

Mặc định:

```text
Axiom ABI
```

có thể thay đổi layout trong compiler version.

Muốn ổn định:

```text
@repr(C)
@repr(transparent)
explicit ABI
```

hoặc representation contract trong tương lai.

---

# 84. Niche optimization

Compiler được phép tối ưu enum representation.

Ví dụ:

```text
Option<Box<T>>
```

có thể dùng một niche của pointer để biểu diễn `None`.

Không có object header bổ sung chỉ để lưu Option tag nếu không cần.

---

# 85. Enum niche không observable

Programmer không được dựa vào:

```text
sizeof(Option<Box<T>>)
```

bằng một giá trị cụ thể trừ khi representation contract đảm bảo.

Compiler có thể thay đổi layout giữa versions.

---

# 86. `repr(C)` enum

C-compatible enum không giống Axiom algebraic enum.

Cần phân biệt:

```text
Axiom enum
```

và:

```text
C enum representation
```

Nếu payload variants tồn tại, representation cần explicit C-compatible layout abstraction.

Không được giả định mọi Axiom enum tự động là C enum.

---

# 87. Union

Union nên bị giới hạn trong v0.1.

Có thể có system-level:

```text
union
```

nhưng access active variant không được giả định an toàn nếu compiler không biết discriminant.

Do đó union nằm ở unsafe/system territory.

---

# 88. Type inference

Axiom hỗ trợ inference:

```axiom
let x = Vec2 {
    x: 1.0,
    y: 2.0
}
```

compiler suy ra type.

Nhưng inference phải deterministic.

---

# 89. Không inference vô hạn

Nếu compiler gặp:

```text
T: TraitA
T: TraitB
```

nhưng không đủ thông tin xác định T:

```text
AMBIGUOUS
```

→ compile error.

Không đoán.

---

# 90. Generic inference

Ví dụ:

```axiom
max(10, 20)
```

compiler có thể suy ra:

```text
T = i32
```

từ literal defaulting nếu không có context khác.

Nhưng:

```text
foo()
```

với T chưa xác định:

```text
cannot infer type
```

---

# 91. No implicit coercion graph

Axiom không có:

```text
T1 → T2 → T3 → ...
```

với hàng chục conversion rules.

Điều này giúp:
- compiler đơn giản hơn
- diagnostics rõ hơn
- AI tooling dễ hơn
- generic resolution deterministic hơn.

---

# 92. Trait operator

Operators có thể resolve qua compiler-known traits:

```text
+
-
*
/
==
<
...
```

Ví dụ:

```text
a + b
```

resolve tới một operation phù hợp.

Nếu có nhiều ứng viên:

```text
ambiguous
```

→ compile error.

---

# 93. Không overload theo conversion

Nếu có:

```text
fn foo(i32)
fn foo(f64)
```

thì:

```axiom
foo(x)
```

không được compiler tự convert `x` sang một overload chỉ vì nó "gần nhất".

Conversion phải explicit.

---

# 94. Layout của trait

Trait declaration không tự tạo storage.

Ví dụ:

```axiom
trait Drawable {
    fn draw(...)
}
```

không làm mọi `T: Drawable` có thêm:

```text
vtable pointer
```

Static dispatch không cần.

---

# 95. Dynamic trait object

Chỉ:

```text
dyn Drawable
```

mới cần dynamic dispatch representation.

Do đó abstraction cost rất rõ ràng:

```text
T: Drawable
    → static

dyn Drawable
    → dynamic
```

---

# 96. Function ABI và closure ABI

Closure ABI không stable.

Nếu cần stable callback ABI:

```text
extern "C" fn(...)
```

hoặc explicit callback struct.

---

# 97. Type layout queries

Compiler should expose:

```text
size_of<T>()
align_of<T>()
layout_of<T>()
```

với distinction:

```text
compile-time query
runtime query
```

`size_of<T>()` có thể compile-time nếu T sized.

Không cần runtime reflection.

---

# 98. Compile-time layout

Ví dụ:

```axiom
const SIZE = size_of<MyStruct>()
```

compiler có thể evaluate tại compile time.

Nếu type không có known size:

```text
compile error
```

---

# 99. Runtime reflection không mặc định

Axiom không tạo:

```text
TypeInfo
FieldInfo
MethodInfo
```

cho mọi object.

Nếu application cần runtime reflection:

```text
explicit metadata
```

phải được yêu cầu.

---

# 100. Type system freeze

Đến đây type model có cấu trúc:

```text
                 TYPE
                  │
       ┌──────────┼──────────┐
       │          │          │
    Primitive   Aggregate   Behavior
       │          │          │
       │       ┌──┼──┐     Trait
       │       │  │  │
       │     Struct Enum Tuple
       │
       └──────────────┐
                      │
                   Generic
                      │
               ┌──────┴──────┐
               │             │
            Static         Dynamic
          impl Trait      dyn Trait
```

và representation:

```text
TYPE SEMANTICS
      ↓
LAYOUT
      ↓
REPRESENTATION
      ↓
ABI
      ↓
MACHINE CODE
```

---

# 101. Normative invariants

### ATYPE-20
Type identity is distinct from representation identity.

### ATYPE-21
Type aliases do not create new type identity.

### ATYPE-22
Newtypes create distinct type identity.

### ATYPE-23
Implicit numeric conversion does not exist.

### ATYPE-24
Numeric literal inference is distinct from runtime conversion.

### ATYPE-25
`usize` is target pointer-width dependent.

### ATYPE-26
Fixed-width integer types have target-independent width.

### ATYPE-27
`bool` has no implicit numeric truthiness.

### ATYPE-28
`unit` is a real type with one value.

### ATYPE-29
`never` represents non-returning computation.

### ATYPE-30
Structs are value aggregates, not classes.

### ATYPE-31
Traits define behavior independently from object storage.

### ATYPE-32
Static trait dispatch does not require a vtable.

### ATYPE-33
Dynamic dispatch requires explicit `dyn Trait`.

### ATYPE-34
`impl Trait` is static abstraction.

### ATYPE-35
Generic semantics do not depend on specialization.

### ATYPE-36
Recursive value types require finite representation.

### ATYPE-37
ZSTs have semantic type identity without requiring physical storage.

### ATYPE-38
Ordinary struct layout is compiler-controlled.

### ATYPE-39
Explicit representation attributes constrain layout.

### ATYPE-40
`@repr(C)` establishes C-compatible representation.

### ATYPE-41
`@repr(transparent)` establishes transparent wrapper representation where valid.

### ATYPE-42
Packed representation cannot create invalid aligned safe access.

### ATYPE-43
Enum layout is compiler-controlled unless explicitly represented.

### ATYPE-44
Niche optimization is not observable without a representation contract.

### ATYPE-45
ABI representation is distinct from source type semantics.

### ATYPE-46
Move does not imply physical copy.

### ATYPE-47
Copy does not imply physical copy.

### ATYPE-48
Aggregate return does not imply heap allocation.

### ATYPE-49
Generic types do not automatically have stable external ABI.

### ATYPE-50
Closure ABI is not a stable FFI ABI.

### ATYPE-51
Unrestricted transmutation is not part of Core.

### ATYPE-52
Pointer conversion is explicit and restricted.

### ATYPE-53
Runtime type metadata is not generated by default.

### ATYPE-54
Type inference is deterministic.

### ATYPE-55
Ambiguous type inference is a compile-time error.

### ATYPE-56
Operator resolution cannot depend on implicit conversion ranking.

---

# 102. Một điểm rất đáng chú ý cho mục tiêu "nhanh hơn C/C++"

Axiom hiện có thể cho compiler nhiều freedom hơn Rust ở một số điểm layout:

```text
ordinary struct
    ↓
compiler may reorder fields
    ↓
reduce padding
```

và:

```text
enum
    ↓
niche optimization
```

và:

```text
generic
    ↓
monomorphize / share / specialize
```

và:

```text
ownership/capability
    ↓
no hidden GC
no hidden RC
no mandatory object header
```

Do đó high-level syntax không nhất thiết tạo overhead runtime.

---

# 103. Nhưng không nên biến mọi layout thành "compiler tùy ý"

Có những boundary mà programmer cần kiểm soát:

```text
FFI
hardware
shared memory
serialization
network protocol
file format
stable plugin ABI
```

Khi đó phải explicit:

```text
@repr(C)
@repr(transparent)
@repr(packed)
@align
explicit serialization
explicit ABI
```

Đây chính là nguyên tắc:

> **Explicit at semantic boundaries, implicit within the compiler.**

---

# 104. Một quyết định quan trọng cho Axiom

Tôi đề xuất **không cho programmer mặc định yêu cầu field offset/layout cụ thể bằng syntax riêng** ngoài representation attributes.

Tức là không tạo một hệ thống phức tạp kiểu:

```text
@field_offset(...)
@bitfield(...)
@manual_layout(...)
@stable_layout(...)
```

trong Core v0.1.

System layer có thể bổ sung sau.

Lý do:

```text
ordinary program
→ compiler owns layout

ABI/system boundary
→ @repr(...)
```

đủ cho phần lớn trường hợp.

---

# 105. Trạng thái của Axiom sau Part VIII

Hiện tại phần nền tảng đã khá hoàn chỉnh:

```text
Part I    Core philosophy
Part II   Surface language
Part III  Ownership / Capability
Part IV   Memory / Allocation
Part V    Concurrency
Part VI   Async
Part VII  Atomic memory model
Part VIII Type / Layout / ABI
```

Cấu trúc semantic hiện tại:

```text
             SOURCE
                │
                ▼
              TYPES
                │
        ┌───────┴────────┐
        │                │
    OWNERSHIP        CAPABILITY
        │                │
        └───────┬────────┘
                │
             STORAGE
                │
        ┌───────┴────────┐
        │                │
     EXECUTION      REPRESENTATION
        │                │
   ┌────┼────┐       ┌───┴───┐
 Thread Task GPU   Layout   ABI
   │     │    │       │       │
   └─────┼────┘       └───┬───┘
         │                │
    Synchronization       │
         │                │
    ┌────┼────┐           │
 Channel Lock Atomic      │
         │                │
         └───────┬────────┘
                 ▼
            MACHINE CODE
```

Điểm quan trọng nhất: **không có subsystem nào cần phá ownership model hiện tại để hoạt động.**

---

# AXIOM LANGUAGE SPECIFICATION v0.1 — Part IX
## Expressions · Evaluation · Operators · Conversion · Pattern Semantics

Tiếp theo cần khóa **expression semantics** thật chặt trước khi viết grammar/compiler implementation, đặc biệt:

```text
evaluation order
short-circuit
function arguments
field/index evaluation
operator overloading
assignment
move expressions
Copy expressions
pattern matching
destructuring
temporary lifetime
implicit view creation
`?`
panic
never
comptime evaluation
```

Đây là phần sẽ quyết định Axiom có thực sự **deterministic và dễ compiler hóa** hay không.