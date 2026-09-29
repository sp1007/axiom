# TYPE-001 — Type System & Representation

Đây là lớp nền dưới `Trait`, `Collection`, `Ownership` và `ABI`. Tôi đề xuất Axiom dùng:

> **Nominal types cho semantic identity + structural reasoning nội bộ cho layout/optimization.**

Tức là programmer không phải đối mặt với type-system quá phức tạp, nhưng compiler vẫn có đủ thông tin để tối ưu representation rất mạnh.

---

## 1. Phân tầng type system

Axiom nên chia type thành 4 nhóm:

```text
Type
├── Primitive
│   ├── bool
│   ├── integers
│   ├── floats
│   └── unit / never
│
├── Aggregate
│   ├── struct
│   ├── tuple
│   └── array
│
├── Algebraic
│   └── enum
│
└── Abstraction
    ├── generic
    ├── trait
    ├── dyn Trait
    ├── view<T>
    ├── mut_view<T>
    └── opaque types
```

Không có:

```text
Object
Any
null
class hierarchy
```

trong safe core.

---

# 2. Nominal typing

Hai struct có cùng field vẫn là hai type khác nhau:

```axiom
struct Point {
    x: f32
    y: f32
}

struct Vector {
    x: f32
    y: f32
}
```

Không được tự động:

```text
Point == Vector
```

dù representation giống nhau.

Điều này rất quan trọng để tránh bug semantic.

```axiom
fn move(p: Point)
```

không nhận `Vector` chỉ vì layout giống nhau.

---

# 3. Nhưng compiler vẫn được phép coi chúng giống nhau ở machine level

Sau khi type checking hoàn tất:

```text
Point
Vector
```

có thể cùng trở thành:

```text
{ f32, f32 }
```

nếu observable semantics không phân biệt representation.

Đây là:

> **Nominal source semantics, structural machine optimization.**

---

# 4. Type alias

Alias không tạo type mới:

```axiom
type UserId = u64
```

Do đó:

```axiom
let a: UserId = 10
let b: u64 = a
```

hợp lệ.

Alias chủ yếu phục vụ:

- readability
- API
- generic specialization naming
- FFI
- platform abstraction

---

# 5. Newtype

Nếu muốn semantic distinction:

```axiom
type UserId = distinct u64
```

hoặc syntax tương đương.

Khi đó:

```text
UserId != u64
```

ở type system.

Nhưng representation mặc định vẫn có thể là:

```text
u64
```

Không có runtime wrapper bắt buộc.

Đây là abstraction rất đáng có.

---

# 6. `distinct` là công cụ quan trọng

Ví dụ:

```axiom
type Meters = distinct f64
type Seconds = distinct f64
```

Không cho:

```axiom
meters + seconds
```

trừ khi trait tương ứng tồn tại.

Machine code vẫn có thể là:

```text
f64
```

Zero-cost semantic safety.

---

# 7. Transparent representation

Đối với newtype:

```axiom
type UserId = distinct u64
```

mặc định compiler có thể đảm bảo representation tương đương underlying type trong các ABI context thích hợp.

Nếu cần explicit FFI guarantee:

```axiom
@repr(transparent)
type UserId = distinct u64
```

Tôi khuyến nghị `transparent` phải là semantic ABI guarantee, không chỉ optimization hint.

---

# 8. Primitive integer types

Giữ:

```text
i8  i16  i32  i64
u8  u16  u32  u64
isize
usize
```

v1.0.

`i128/u128` có thể hỗ trợ sau khi backend/runtime/compiler đủ ổn định.

---

# 9. `usize` / `isize`

`usize` dùng cho:

- indexing
- collection length
- pointer-sized quantities
- memory size
- ABI sizes

Không nên dùng `u64` cho mọi thứ.

Ví dụ:

```axiom
fn get(v: view<T>, i: usize)
```

---

# 10. Không có implicit numeric widening tùy tiện

Ví dụ:

```axiom
let x: i32 = ...
let y: i64 = x
```

Có thể cho phép nếu conversion an toàn theo semantics đã khóa, nhưng tôi khuyến nghị:

> **Numeric conversion phải rõ ràng khi có khả năng thay đổi representation/range.**

Ví dụ:

```axiom
let y = x as i64
```

Điều này tránh những bug kiểu C:

```text
signed → unsigned
unsigned → signed
narrowing
promotion
```

---

# 11. Conversion categories

Nên phân biệt:

```text
as
bitcast
```

### `as`

Semantic numeric conversion:

```axiom
x as i64
```

### `bitcast`

Giữ nguyên bit pattern, đổi type.

```axiom
bitcast<u32>(f32_value)
```

Đây là operation cấp thấp và có thể yêu cầu `unsafe` tùy type.

Không được dùng `as` để âm thầm biến thành bit reinterpretation.

---

# 12. Float

Core:

```text
f32
f64
```

Theo IEEE-754 semantics phù hợp target.

Cần quy định rõ:

- NaN
- ±Infinity
- signed zero
- rounding
- comparisons

Đặc biệt:

```text
NaN != NaN
```

theo floating-point semantics.

---

# 13. Float equality

Không được mặc định coi:

```axiom
f32 == f32
```

là equivalence relation theo toán học.

Trait `Eq` cho floating-point cần cân nhắc vì NaN.

Có thể tách:

```text
PartialEq
Eq
```

hoặc semantics tương đương.

Khuyến nghị:

```text
f32: PartialEq
f32: PartialOrd
```

nhưng không phải `Eq`/`Ord` thông thường.

Nếu cần total ordering:

```text
TotalF32
```

hoặc wrapper.

---

# 14. `bool`

`bool` chỉ có:

```text
true
false
```

Không tự động coi integer là bool.

Không:

```axiom
if x { ... }
```

nếu `x: i32`.

Phải:

```axiom
if x != 0 { ... }
```

Điều này giúp type system đơn giản và tránh C-style bugs.

---

# 15. `unit`

```text
unit
```

là type có đúng một value:

```axiom
()
```

Function không trả dữ liệu:

```axiom
fn log(msg: StringView) -> unit
```

có thể bỏ `-> unit`:

```axiom
fn log(msg: StringView)
```

---

# 16. `never`

```text
never
```

là type không có value.

Ví dụ:

```axiom
fn abort() -> never
```

Các control-flow operation:

```text
panic()
trap()
abort()
```

có thể có type `never`.

Điều này giúp CFG reasoning rất mạnh.

Ví dụ:

```axiom
let x = if condition {
    10
} else {
    panic()
}
```

Branch `panic()` có `never`, nên toàn expression có thể có type `i32`.

---

# 17. Tuple

Axiom nên hỗ trợ tuple:

```axiom
let x = (10, "hello", true)
```

Type:

```text
(i32, String, bool)
```

Tuple là anonymous structural aggregate.

Không có method namespace riêng.

---

# 18. Tuple không phải struct

```text
(i32, i32)
```

và:

```axiom
struct Point {
    x: i32
    y: i32
}
```

không phải cùng type.

Nhưng compiler có thể có representation giống nhau.

---

# 19. Array

```axiom
[T; N]
```

là fixed-size homogeneous aggregate.

`N` là compile-time constant.

Ví dụ:

```axiom
[i32; 4]
```

Layout:

```text
T T T T
```

không có header.

---

# 20. Zero-sized types

Axiom nên hỗ trợ ZST:

```axiom
struct Marker {}
```

size semantic:

```text
sizeof(Marker) == 0
```

Compiler không cần cấp byte storage nếu address identity không được yêu cầu.

---

# 21. ZST và ownership

Một ZST vẫn có semantic ownership.

Ví dụ:

```axiom
struct Token {}

fn consume(t: Token)
```

Move vẫn có ý nghĩa ở type system dù không có physical bytes.

Điều này tránh việc compiler biến mất semantic state.

---

# 22. Enum — algebraic data type

Ví dụ:

```axiom
enum Option<T> {
    Some(T),
    None,
}
```

Enum là **sum type**.

Struct là product type.

```text
struct → AND
enum   → OR
```

Đây là nền tảng rất mạnh cho Axiom.

---

# 23. Enum representation

Compiler tự chọn:

```text
tag + payload
```

hoặc tối ưu bằng niche.

Ví dụ:

```text
Option<&T>
```

có thể dùng:

```text
null = None
non-null = Some
```

nếu representation/provenance semantics cho phép.

Programmer không được phụ thuộc vào encoding mặc định.

---

# 24. Explicit enum representation

Khi cần ABI:

```axiom
@repr(C)
enum ErrorCode {
    ...
}
```

hoặc representation tương đương.

Khi đó compiler phải tuân ABI contract.

---

# 25. Enum discriminant

Có thể cho:

```axiom
enum Color {
    Red = 1,
    Green = 2,
    Blue = 3,
}
```

nhưng cần phân biệt:

```text
semantic discriminant
machine representation
```

Nếu enum có explicit representation:

```axiom
@repr(u8)
```

thì size/encoding bị ràng buộc.

---

# 26. Enum exhaustive matching

```axiom
match color {
    Color.Red => ...
    Color.Green => ...
    Color.Blue => ...
}
```

Compiler phải kiểm tra exhaustiveness.

Nếu enum non-exhaustive từ external ABI/package thì phải có fallback mechanism.

---

# 27. Pattern matching là type-system feature

Pattern:

```axiom
match value {
    Some(x) => ...
    None => ...
}
```

không phải runtime reflection.

Compiler resolve pattern statically.

Sau MIR:

```text
switch discriminant
```

và tối ưu như switch/branch bình thường.

---

# 28. Recursive types

Không cho recursive value trực tiếp:

```axiom
struct Node {
    next: Node
}
```

vì size vô hạn.

Phải dùng indirection:

```axiom
struct Node {
    next: Option<Box<Node>>
}
```

hoặc:

```axiom
next: Option<Handle<Node>>
```

Điều này khiến storage identity explicit.

---

# 29. Recursive enum

Ví dụ:

```axiom
enum List<T> {
    Nil,
    Cons(T, Box<List<T>>),
}
```

hợp lệ.

Compiler tính size dựa trên `Box`, không phải expand vô hạn.

---

# 30. Opaque type

Axiom cần opaque type cho abstraction boundary:

```axiom
opaque FileHandle
```

Module bên ngoài biết:

```text
FileHandle exists
```

nhưng không biết representation.

Điều này cực kỳ hữu ích cho:

- OS handles
- GPU resources
- FFI
- compiler internals
- ABI boundaries

---

# 31. Opaque type không đồng nghĩa heap object

```axiom
opaque FileHandle
```

không nói:

```text
heap
pointer
object
```

Nó chỉ nói:

> Representation không thuộc API contract.

---

# 32. Type layout

Đây là điểm Axiom nên mạnh hơn nhiều ngôn ngữ high-level.

Mặc định:

```text
layout = compiler controlled
```

Compiler có thể:

- reorder fields
- eliminate padding khi có thể
- optimize aggregate representation
- scalarize
- split aggregates
- pack values vào registers

miễn observable semantics không đổi.

---

# 33. Nhưng struct layout có một ngoại lệ lớn

Nếu programmer viết:

```axiom
@repr(C)
struct Foo {
    ...
}
```

thì:

```text
field order
alignment
padding
size
ABI
```

phải tuân contract tương ứng.

---

# 34. `repr` categories

Khuyến nghị ban đầu:

```text
@repr(C)
@repr(transparent)
@repr(packed)
@repr(align(N))
```

Không mở hàng chục `repr` ngay từ đầu.

### `repr(C)`

C-compatible layout.

### `repr(transparent)`

Một field/underlying representation.

### `repr(packed)`

Giảm/eliminate alignment padding; unsafe/system-level.

### `repr(align(N))`

Yêu cầu alignment tối thiểu.

---

# 35. Packed struct

```axiom
@repr(packed)
struct Header {
    tag: u8
    size: u32
}
```

Có thể khiến:

```text
size
```

không aligned.

Access trực tiếp có thể gây:

- unaligned access
- trap trên một số architecture
- performance degradation

Do đó packed access nên bị giới hạn/đòi hỏi unsafe khi tạo reference-like capability tới field không aligned.

---

# 36. Alignment

Mỗi type có:

```text
size
alignment
```

Compiler đảm bảo storage phù hợp.

Ví dụ:

```text
f64 → alignment target-dependent
```

Không hardcode universal alignment.

---

# 37. `sizeof`

Axiom nên có compile-time:

```axiom
sizeof<T>()
alignof<T>()
```

và có thể:

```axiom
size_of(value)
```

nhưng nên compile-time nếu type statically known.

---

# 38. Layout introspection

Comptime có thể hỏi:

```axiom
comptime {
    sizeof<MyStruct>()
    alignof<MyStruct>()
}
```

Nhưng không nên cho runtime reflection mặc định.

---

# 39. Field offset

Chỉ exposed khi representation contract cho phép.

Ví dụ:

```axiom
@repr(C)
struct Header { ... }
```

có thể dùng:

```axiom
offset_of(Header, size)
```

cho systems/FFI tooling.

Struct bình thường không được phụ thuộc field offset.

---

# 40. SIMD types

Không nên biến:

```text
f32x4
i32x8
```

thành những primitive semantic riêng biệt quá sớm.

Nên có compiler/library abstraction:

```axiom
simd<f32, 4>
```

hoặc intrinsic/vector types.

Backend biết:

```text
SSE
AVX
AVX2
AVX-512
NEON
SVE
```

và chọn instruction phù hợp.

---

# 41. SIMD không được làm type system phụ thuộc CPU

Code:

```axiom
Vec4<f32>
```

không nên chỉ compile được trên AVX.

Compiler có thể lower thành:

```text
scalar
SSE
AVX
NEON
...
```

tùy target.

Nếu programmer yêu cầu instruction cụ thể:

```axiom
@target_feature("avx2")
```

thì đó là explicit target contract.

---

# 42. Bitfields

Không nên đưa bitfield syntax phức tạp vào Core v1.

Dùng:

```axiom
u32
```

và helper:

```text
mask
shift
```

hoặc một future packed/bitfield library.

Lý do: ABI bitfield giữa C compiler/architecture không thống nhất.

Nếu FFI cần C bitfield, phải có target-specific ABI handling.

---

# 43. Pointer types

Core semantic:

```text
*const T
*mut T
```

nhưng raw pointer là unsafe-level concept.

Pointer:

- không sở hữu mặc định
- không đảm bảo valid
- không tự tạo lifetime
- không tự tạo capability

---

# 44. Pointer ≠ `view<T>`

Đây phải được khóa rất rõ.

```text
*const T
```

là machine-level address/provenance value.

```text
view<T>
```

là safe semantic READ capability.

Conversion:

```text
raw pointer
    ↓ unsafe validation
view<T>
```

có thể tồn tại.

Chiều ngược lại:

```text
view<T>
    ↓
raw pointer
```

phải đi qua unsafe nếu exposing address.

---

# 45. Function types

Ví dụ:

```axiom
fn(i32, i32) -> i32
```

là function type.

Function pointer:

```axiom
*fn(i32, i32) -> i32
```

hoặc syntax tương đương.

Closure type khác function pointer nếu closure captures state.

---

# 46. Closure representation

Closure:

```axiom
let add = |x| x + offset
```

semantic là anonymous struct chứa capture state + callable behavior.

Compiler có thể:

```text
closure
 ↓
struct captures
 ↓
specialized function
```

Không bắt buộc heap.

---

# 47. Capturing closure và function pointer

Closure không capture:

```axiom
let f = |x: i32| x * 2
```

có thể decay thành function pointer nếu context yêu cầu.

Closure capture:

```axiom
let f = |x| x + offset
```

không thể tự động thành plain function pointer vì cần environment.

Có thể dùng:

```text
dyn Fn
```

nếu muốn dynamic callable.

---

# 48. Generic function type

Generic function:

```axiom
fn foo<T>(x: T)
```

không phải một runtime function object có type variable.

Compiler instantiate khi cần.

---

# 49. Type identity

Type identity cần phân biệt:

```text
Alias
Newtype
Generic instantiation
Anonymous tuple
Closure
Opaque
Trait object
```

Đề xuất:

```text
alias        → same type
distinct     → new nominal type
struct       → nominal
enum         → nominal
tuple        → structural
array        → structural by T,N
function     → structural signature
closure      → unique anonymous nominal type
```

Điều này khá cân bằng.

---

# 50. Type equality

Compiler cần internal notion:

```text
TypeEqual
TypeCompatible
RepresentationCompatible
ABICompatible
```

Không gom tất cả thành một `==`.

Ví dụ:

```text
Point != Vector
```

nhưng:

```text
repr(Point) == repr(Vector)
```

có thể đúng.

---

# 51. Type inference

Inference nên dựa trên constraint solving:

```text
x = foo(y)
```

Compiler tạo:

```text
T1 = type(x)
T2 = type(y)
foo : T2 -> T1
```

sau đó trait/type constraints giải quyết.

Không cần Hindley-Milner đầy đủ.

Axiom là systems language, nên annotation vẫn có chỗ đứng.

---

# 52. Generic inference không xuyên qua runtime boundary

Ví dụ dynamic:

```axiom
dyn Trait
```

không được cố suy luận thành generic concrete type.

Dynamic boundary là boundary thực sự.

---

# 53. Type erasure

Compiler có thể erase:

```text
generic parameters
trait metadata
phantom types
newtype wrappers
```

nếu runtime semantics không cần.

Ví dụ:

```axiom
type UserId = distinct u64
```

machine-level:

```text
u64
```

nhưng compiler vẫn giữ type identity cho static checking.

---

# 54. Phantom types

Nên hỗ trợ nhẹ:

```axiom
struct Handle<T> {
    raw: u64
}
```

nếu `T` chỉ dùng ở type-level.

Compiler không cần lưu `T` runtime.

Ví dụ:

```axiom
Handle<Texture>
Handle<Mesh>
```

có cùng representation:

```text
u64
```

nhưng không thể truyền nhầm.

Đây là abstraction rất hữu ích cho systems programming.

---

# 55. Zero-cost type safety

Đây là một mục tiêu rất mạnh:

```text
UserId
Meters
Seconds
Handle<Texture>
Handle<Mesh>
```

có thể hoàn toàn biến mất ở binary.

Nhưng compiler vẫn ngăn:

```text
TextureHandle → MeshHandle
```

Đây chính là thứ Axiom nên làm tốt.

---

# 56. Type layout và optimizer

Pipeline:

```text
Typed HIR
   ↓
type checking
   ↓
layout computation
   ↓
MIR
   ↓
representation optimization
   ↓
LIR
```

Layout không nhất thiết phải cố định quá sớm.

Compiler có thể trì hoãn representation decision tới khi biết:

- target
- ABI
- escape
- optimization
- SIMD
- register pressure

---

# 57. Nhưng ABI boundary đóng layout

Ví dụ:

```axiom
@repr(C)
extern "C" fn foo(x: Foo)
```

lúc này `Foo` phải có ABI layout xác định.

Do đó:

```text
Internal type
       │
       ├── ordinary use → compiler freedom
       │
       └── ABI boundary → representation frozen
```

---

# 58. Type-level constants

Axiom cần compile-time constants:

```axiom
const PAGE_SIZE: usize = 4096
```

và generic const parameters có thể hỗ trợ ở mức cần thiết:

```axiom
Array<T, N>
```

nhưng không nên biến compile-time system thành một ngôn ngữ theorem proving.

---

# 59. Generic const parameter

`N` trong:

```axiom
[T; N]
```

là compile-time value.

v1.0 chỉ cần hỗ trợ những dạng constant đủ cho:

- array length
- alignment
- SIMD width
- buffer capacity
- compile-time configuration

Không cần arbitrary dependent types.

---

# 60. Không đưa dependent type vào Axiom

Không cần:

```text
Vector<T, N>
```

và bắt compiler chứng minh mọi phép toán số học trên `N`.

Có thể hỗ trợ generic constants, nhưng type system không trở thành dependent type system đầy đủ.

Điều này giữ compiler và programmer đơn giản.

---

# 61. Type-001 invariant set

Khóa:

```text
ATYPE-20  Primitive types have defined semantics.
ATYPE-21  Safe integers do not rely on C-style implicit UB.
ATYPE-22  Numeric narrowing requires explicit conversion.
ATYPE-23  Bit reinterpretation is distinct from numeric conversion.
ATYPE-24  bool is not implicitly interchangeable with integers.
ATYPE-25  unit has exactly one value.
ATYPE-26  never has no values and represents non-returning control flow.
ATYPE-27  Struct types are nominal.
ATYPE-28  Enum types are nominal.
ATYPE-29  Tuple types are structural.
ATYPE-30  Array identity depends on element type and compile-time length.
ATYPE-31  Type aliases do not create new types.
ATYPE-32  Distinct/newtype declarations create nominal types.
ATYPE-33  Newtypes may have transparent representation.
ATYPE-34  Zero-sized types are supported.
ATYPE-35  ZST semantic ownership remains meaningful.
ATYPE-36  Enum is an algebraic sum type.
ATYPE-37  Struct is an aggregate/product type.
ATYPE-38  Enum layout is compiler-controlled unless explicitly represented.
ATYPE-39  Niche optimization may be used when semantics permit.
ATYPE-40  Match exhaustiveness is statically checked.
ATYPE-41  Recursive value types require finite indirection.
ATYPE-42  Opaque types hide representation across abstraction boundaries.
ATYPE-43  Default struct layout is compiler-controlled.
ATYPE-44  @repr(C) establishes C-compatible representation.
ATYPE-45  @repr(transparent) establishes underlying representation compatibility.
ATYPE-46  @repr(packed) may create unaligned fields and is unsafe-sensitive.
ATYPE-47  @repr(align(N)) establishes minimum alignment.
ATYPE-48  ABI boundaries constrain representation.
ATYPE-49  Internal representation may be optimized freely when unobservable.
ATYPE-50  Raw pointers are distinct from safe capabilities.
ATYPE-51  Function types are distinct from capturing closure types.
ATYPE-52  Non-capturing closures may decay to function pointers where valid.
ATYPE-53  Capturing closures require environment representation.
ATYPE-54  Phantom type parameters may erase completely at runtime.
ATYPE-55  Generic type identity remains statically meaningful after runtime erasure.
ATYPE-56  Generic const parameters are compile-time values, not runtime fields by default.
ATYPE-57  Axiom does not require full dependent typing.
ATYPE-58  SIMD/vector types are target-lowerable abstractions.
ATYPE-59  CPU-specific vector instructions require explicit target capability when necessary.
ATYPE-60  Type identity is distinct from representation identity.
ATYPE-61  Representation compatibility does not imply semantic type compatibility.
ATYPE-62  Compiler may optimize equivalent representations.
ATYPE-63  Layout is frozen when required by ABI.
ATYPE-64  Ordinary source types do not expose physical field layout by default.
ATYPE-65  Runtime reflection is not required by the Core.
```

---

# 62. Bây giờ mô hình type của Axiom đã khá hoàn chỉnh

Có thể hình dung:

```text
                         TYPE
                           │
       ┌───────────────────┼───────────────────┐
       │                   │                   │
   Primitive            Aggregate          Algebraic
       │                   │                   │
  int/float/bool      struct/tuple/array      enum
       │                   │                   │
       └───────────────────┴───────────────────┘
                           │
                     Abstraction
                           │
       ┌──────────────┬────┼─────┬──────────────┐
       │              │    │     │              │
    distinct        generic trait  dyn         opaque
       │              │    │     │
   zero-cost       static │ dynamic
                         dispatch
```

Điểm rất đáng giá là **không cần class/object type** mà vẫn có đủ khả năng abstraction.

---

# 63. Một quyết định cần khóa ngay

Tôi đề xuất Axiom **không dùng structural typing cho struct**.

Không:

```text
struct A { x: i32 }
struct B { x: i32 }

fn foo(x: { x: i32 })
```

rồi tự nhận cả A/B.

Thay vào đó:

```text
nominal type
+
trait contract
```

Nếu hai type có cùng hành vi, định nghĩa trait:

```axiom
trait HasX {
    fn x(self) -> i32
}
```

rồi:

```axiom
impl HasX for A { ... }
impl HasX for B { ... }
```

Đây là mô hình rõ ràng hơn cho một systems language.

---

# 64. Bước tiếp theo: ABI-001

Sau `TYPE-001`, task tiếp theo nên là:

## **ABI-001 — ABI, Calling Convention & Binary Interface**

Phần này sẽ khóa:

- Axiom ABI
- C ABI
- system ABI
- function calling convention
- return-value ABI
- struct passing
- aggregate return
- `sret`
- register vs stack arguments
- variadic functions
- symbol naming
- name mangling
- visibility/export
- DLL/SO/DYLIB
- static library
- executable
- TLS
- unwind ABI
- panic ABI
- `extern`
- `@repr(C)`
- cross-language FFI
- stable ABI
- versioning
- endian
- target triples
- PE/ELF/Mach-O
- Windows/Linux/macOS/iOS/Android/WASM

Đây là bước bắt buộc trước khi thiết kế **LIR/Machine ABI/Native Backend**, vì Axiom đặt mục tiêu cuối cùng là **tự sinh native executable mà không phụ thuộc compiler bên thứ ba**.