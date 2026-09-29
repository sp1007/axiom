# AXIOM LANGUAGE SPECIFICATION v0.1
# Part XI — Struct · Enum · Algebraic Data · Layout · Identity

Part X đã khóa function/callable model. Bây giờ khóa **data model** của Axiom.

Quyết định trung tâm:

> **Struct là aggregate primitive. Function là behavior primitive. Trait là contract primitive.**

Không cần class, object header hay inheritance để xây dựng phần lớn mô hình dữ liệu của một hệ thống hiện đại.

---

# 1. Struct là aggregate chính

Cú pháp:

```axiom
struct Vec2 {
    x: f32
    y: f32
}
```

Struct biểu diễn một tập field có type xác định.

```axiom
let p = Vec2 {
    x: 10.0,
    y: 20.0
}
```

Struct không tự động có:

- object header
- vtable
- GC metadata
- runtime type ID
- reference count

---

# 2. Struct không có inheritance

Không có:

```text
class A extends B
```

và:

```text
super
base
virtual inheritance
```

Thay vào đó:

```axiom
trait Drawable {
    fn draw(self: view<Self>)
}

impl Drawable for Circle {
    ...
}
```

Behavior reuse thông qua trait/composition.

---

# 3. Data và behavior tách biệt

```axiom
struct Vec2 {
    x: f32
    y: f32
}

fn length(self: view<Vec2>) -> f32 {
    ...
}
```

Có thể gọi:

```axiom
v.length()
```

nhưng semantic vẫn là:

```axiom
length(view(v))
```

Không có hidden `this` pointer/object machinery.

---

# 4. Inherent implementation

Có thể định nghĩa behavior trực tiếp:

```axiom
impl Vec2 {
    fn length(self: view<Vec2>) -> f32 {
        ...
    }

    fn zero() -> Vec2 {
        Vec2 {
            x: 0.0,
            y: 0.0
        }
    }
}
```

`zero()` là associated function.

```axiom
let p = Vec2.zero()
```

---

# 5. Struct identity

Mỗi struct declaration tạo một type identity riêng.

```axiom
struct UserId {
    value: u64
}

struct ProductId {
    value: u64
}
```

Dù layout giống nhau:

```text
UserId ≠ ProductId
```

Không thể:

```axiom
let p: ProductId = user_id
```

một cách implicit.

Đây là lý do newtype hữu ích để ngăn nhầm lẫn semantic.

---

# 6. Type alias

Ngược lại:

```axiom
type UserId = u64
```

không tạo type mới.

```text
UserId == u64
```

về type identity.

Alias dùng cho:

- readability
- API naming
- generic simplification
- platform types

không dùng để tạo type safety mới.

---

# 7. Tuple struct

Axiom hỗ trợ tuple struct:

```axiom
struct Color(u8, u8, u8, u8)
```

Sử dụng:

```axiom
let c = Color(255, 0, 0, 255)
```

Field truy cập:

```axiom
c.0
c.1
```

Tuple struct vẫn là distinct type.

---

# 8. Unit struct

Có thể có struct không chứa field:

```axiom
struct Marker
```

Giá trị:

```axiom
let m = Marker
```

Đây là Zero-Sized Type nếu không có hidden semantic state.

---

# 9. Zero-Sized Types

ZST được hỗ trợ.

Ví dụ:

```axiom
struct Phantom
```

có thể có:

```text
size = 0
```

Compiler không cần cấp storage vật lý.

Nhưng type vẫn có semantic identity.

---

# 10. ZST và arrays

Ví dụ:

```axiom
Array<Phantom, 1000000>
```

không nhất thiết chiếm memory proportional to 1,000,000.

Compiler có thể biểu diễn bằng zero bytes.

---

# 11. ZST and identity

ZST không có nghĩa mọi instance có storage identity riêng.

Nếu programmer cần identity, phải dùng:

- handle
- address
- explicit storage abstraction

Không được suy luận identity từ value của ZST.

---

# 12. Field initialization

Struct literal phải khởi tạo đầy đủ field bắt buộc:

```axiom
Vec2 {
    x: 1.0,
    y: 2.0
}
```

Thiếu field:

```axiom
Vec2 {
    x: 1.0
}
```

→ compile error.

Không có implicit zero-initialization trong ordinary struct construction.

Điều này tránh hidden initialization cost.

---

# 13. Field order in source

Source declaration:

```axiom
struct User {
    id: u64
    name: Text
    age: u32
}
```

không mặc định đóng băng physical layout.

Compiler có thể reorder field để:

- giảm padding
- cải thiện alignment
- tối ưu cache
- vectorize
- giảm object size

trừ khi layout contract yêu cầu khác.

---

# 14. `@repr(C)`

Nếu cần layout C:

```axiom
@repr(C)
struct User {
    id: u64
    age: u32
}
```

thì field order/alignment/layout tuân theo C ABI contract.

Đây là semantic ABI boundary.

Compiler không được reorder theo optimization tự do nữa.

---

# 15. `@repr(transparent)`

Newtype:

```axiom
@repr(transparent)
struct UserId(u64)
```

cam kết representation tương thích với underlying field trong những ABI contexts mà transparent representation áp dụng.

Nhưng:

```text
UserId
```

vẫn khác:

```text
u64
```

về type identity.

---

# 16. Packed representation

```axiom
@repr(packed)
struct Header {
    tag: u8
    value: u32
}
```

cho phép layout không có alignment padding theo contract.

Nhưng field access không được tạo ra một invalid aligned machine access trong safe semantics.

Compiler phải:

```text
unaligned load/store
```

hoặc yêu cầu unsafe access tùy target/type.

---

# 17. Alignment

```axiom
@align(64)
struct CacheLine {
    ...
}
```

yêu cầu alignment contract.

Compiler phải đảm bảo mọi valid storage location của type đáp ứng alignment.

Không được dùng `@align` để tạo một type representation không thể thực hiện trên target.

---

# 18. Field visibility

Ví dụ:

```axiom
pub struct User {
    pub id: u64
    name: Text
}
```

Code bên ngoài package chỉ truy cập:

```axiom
user.id
```

Không truy cập:

```axiom
user.name
```

nếu `name` private.

---

# 19. Private field không phải encapsulated object

Private field chỉ là **visibility rule**.

Nó không tạo:

- runtime getter
- runtime metadata
- virtual dispatch
- object boundary

Compiler vẫn tối ưu field access như bình thường.

---

# 20. Constructor không phải language primitive

Axiom không có:

```text
new User(...)
constructor User(...)
```

Constructor chỉ là ordinary function:

```axiom
impl User {
    fn create(id: u64) -> User {
        User {
            id: id,
            name: ...
        }
    }
}
```

Điều này giữ function model thống nhất.

---

# 21. Field update

Axiom hỗ trợ field update syntax:

```axiom
let updated = User {
    ...old,
    age: 20
}
```

Semantic phải rõ ràng về ownership.

Nếu `old` không Copy:

```text
fields not explicitly replaced
    → moved into updated
```

Các field bị thay thế:

```text
old.age
    → Drop nếu cần
    → replaced
```

---

# 22. Field update không clone ngầm

Ví dụ:

```axiom
let new_user = User {
    ...old,
    name: new_name
}
```

không có implicit:

```text
clone(old.id)
clone(old.other_field)
```

Nếu field non-Copy thì move.

---

# 23. Partial move

Struct:

```axiom
struct User {
    name: Text
    age: u32
}
```

cho phép:

```axiom
let name = user.name
```

và sau đó:

```axiom
print(user.age)
```

nếu semantic state còn hợp lệ.

Compiler ownership state có thể là:

```text
User
├── name → MOVED
└── age  → OWNED
```

---

# 24. Custom Drop và partial move

Nếu:

```axiom
struct Resource {
    handle: Handle
}

impl Drop for Resource {
    fn drop(self: mut_view<Self>) {
        ...
    }
}
```

thì:

```axiom
let h = resource.handle
```

→ không cho partial move.

Lý do: custom Drop có thể cần invariant của toàn object.

---

# 25. Derived Drop

Nếu compiler tự sinh destructor semantics từ fields:

```text
Resource
  ├── field A: Drop
  └── field B: Drop
```

compiler có thể tracking partial move field-by-field.

Ví dụ:

```text
A → MOVED
B → DROP
```

---

# 26. Enum là algebraic data type

Ví dụ:

```axiom
enum Message {
    Quit,
    Text(Text),
    Move {
        x: i32,
        y: i32
    }
}
```

Enum có thể chứa:

```text
unit variant
tuple payload
struct payload
```

---

# 27. Enum variant là type constructor

Conceptually:

```text
Message.Quit
Message.Text(Text)
Message.Move { x, y }
```

Mỗi variant tạo một constructor trong algebraic data model.

---

# 28. Enum không phải C enum

Axiom:

```axiom
enum Message {
    Quit,
    Text(Text)
}
```

không có nghĩa:

```text
enum Message {
    Quit = 0,
    Text = 1
}
```

theo C.

Nó là tagged/sum type.

Nếu cần C enum:

```axiom
@repr(C)
enum Color {
    Red,
    Green,
    Blue
}
```

với các giới hạn C-ABI tương ứng.

---

# 29. Discriminant

Enum conceptually có discriminant:

```text
Message
   ├── Quit
   ├── Text
   └── Move
```

Nhưng discriminant representation là compiler-controlled.

Compiler có thể:

- explicit tag
- niche
- pointer niche
- optimized encoding

miễn semantic behavior giữ nguyên.

---

# 30. Niche optimization

Ví dụ:

```axiom
Option<Box<T>>
```

compiler có thể biểu diễn:

```text
None = null pointer
Some(x) = non-null pointer
```

mà không cần thêm discriminant byte.

Đây là optimization.

Programmer không được phụ thuộc vào representation trừ khi explicit ABI/repr contract cho phép.

---

# 31. `Option<T>`

`Option<T>` là:

```axiom
enum Option<T> {
    None,
    Some(T)
}
```

Không có `null` trong safe core.

```axiom
let value: Option<i32> = Option.Some(10)
```

---

# 32. `Result<T,E>`

```axiom
enum Result<T, E> {
    Ok(T),
    Err(E)
}
```

là ordinary enum.

Không cần:

```text
exception object
runtime error table
heap allocation
```

để sử dụng `Result`.

---

# 33. Enum ownership

Ví dụ:

```axiom
let result: Result<Buffer, Error> = ...
```

nếu:

```text
Ok(Buffer)
```

thì Buffer ownership nằm trong enum.

Pattern:

```axiom
match result {
    Ok(buffer) => consume(buffer)
    Err(error) => handle(error)
}
```

move payload theo pattern semantics.

---

# 34. Enum partial payload access

Không thể truy cập payload trước khi biết variant.

Không có:

```axiom
result.value
```

nếu `value` chỉ tồn tại ở `Ok`.

Phải:

```axiom
match result {
    Ok(value) => ...
    Err(error) => ...
}
```

Compiler có exhaustive knowledge.

---

# 35. Match exhaustiveness

Compiler phải phát hiện:

```axiom
match result {
    Ok(value) => ...
}
```

là thiếu:

```text
Err
```

→ compile error nếu match được yêu cầu exhaustive.

---

# 36. Wildcard exhaustive

```axiom
match result {
    Ok(value) => ...
    _ => ...
}
```

được coi là exhaustive.

Compiler có thể cảnh báo unreachable arm nếu arm sau không bao giờ match.

---

# 37. Unreachable variants

Ví dụ:

```axiom
match x {
    _ => foo()
    Some(v) => bar()
}
```

`Some(v)` unreachable.

Compiler phải diagnostic.

---

# 38. Enum layout

Compiler được phép tối ưu:

```text
size
alignment
tag position
payload position
niche
```

trừ khi:

```text
@repr(...)
```

đóng băng một ABI representation.

---

# 39. Recursive enums

Trực tiếp:

```axiom
enum List<T> {
    Nil,
    Cons(T, List<T>)
}
```

không có finite size.

→ compile error.

Phải có indirection:

```axiom
enum List<T> {
    Nil,
    Cons(T, Box<List<T>>)
}
```

hoặc handle/arena representation.

---

# 40. Recursive structs

Tương tự:

```axiom
struct Node {
    next: Node
}
```

→ compile error.

Phải:

```axiom
struct Node {
    next: Option<Box<Node>>
}
```

hoặc:

```axiom
struct Node {
    next: Option<NodeHandle>
}
```

---

# 41. Why no implicit indirection

Axiom không tự biến:

```axiom
next: Node
```

thành:

```text
Box<Node>
```

vì điều đó thay đổi:

- size
- ownership
- allocation
- identity
- performance

Đây là semantic boundary phải explicit.

---

# 42. Handle-based recursive structures

Cho graph/tree lớn:

```axiom
struct Node {
    value: Value
    children: view<NodeHandle>
}
```

hoặc collection:

```text
Arena<Node>
```

và:

```text
NodeHandle
```

để biểu diễn logical identity.

Đây phù hợp với mô hình:

```text
Value Identity
Storage Identity
Logical Identity
```

đã khóa trước đó.

---

# 43. Three identities

Axiom chính thức phân biệt:

### Value Identity

```text
"giá trị này là gì?"
```

### Storage Identity

```text
"vùng storage này là vùng nào?"
```

### Logical Identity

```text
"entity/object này là object nào?"
```

Ví dụ ECS:

```axiom
let entity: EntityId = world.spawn(...)
```

`EntityId` là logical identity.

Không cần giữ raw address.

---

# 44. Struct không tự có object identity

Hai values:

```axiom
let a = Vec2 { x: 1, y: 2 }
let b = Vec2 { x: 1, y: 2 }
```

không có semantic identity riêng ngoài value semantics.

```text
a == b
```

có thể true.

Không có hidden object identity.

---

# 45. Box tạo storage identity

```axiom
let a = Box.new(Value(...))
```

`Box<T>` là owning dynamic-storage abstraction.

Storage identity tồn tại vì Box contract yêu cầu.

Nhưng compiler vẫn có thể eliminate allocation nếu:

```text
address not observable
storage identity not externally observable
```

---

# 46. Stable address

Nếu programmer cần:

```axiom
let p = addr_of(box)
```

hoặc truyền address ra FFI, stable-address contract trở nên observable.

Compiler không còn tự do relocate object.

Đây là:

> **Stable address is an explicit storage contract.**

---

# 47. Union

Axiom có thể hỗ trợ restricted union ở system layer:

```axiom
unsafe union RawValue {
    i: i32
    f: f32
}
```

Union không có automatic variant tracking.

Do đó safe union access cần explicit validity contract.

Không đưa unrestricted union vào safe Core semantics.

---

# 48. Bitfields

Bitfield không phải Core struct feature v0.1.

Nếu cần:

```text
network packet
hardware register
C ABI
binary protocol
```

sử dụng:

```text
system representation API
```

hoặc compiler extension/attribute được định nghĩa rõ.

Không biến struct semantics thành một hệ thống layout DSL khổng lồ.

---

# 49. Struct layout and optimization

Ví dụ:

```axiom
struct Particle {
    position: Vec3
    velocity: Vec3
    mass: f32
}
```

compiler có thể:

```text
AoS
register scalarization
field reordering
dead-field elimination
```

**chỉ khi semantic/storage/ABI contract cho phép.**

Nếu programmer cần chính xác memory layout:

```axiom
@repr(C)
```

hoặc explicit system representation.

---

# 50. Generic structs

```axiom
struct Pair<A, B> {
    first: A
    second: B
}
```

Generic type được compile-time instantiate.

Không cần runtime type descriptors cho ordinary operations.

---

# 51. Generic layout

`Pair<i32, i64>` và `Pair<i64, i32>` có thể có layout khác nhau.

Compiler biết concrete types sau monomorphization.

Không được expose layout stable qua generic ABI nếu chưa có explicit representation contract.

---

# 52. Unsized fields

Ordinary struct field mặc định phải có known representation size.

Ví dụ:

```axiom
struct Bad {
    data: dyn Trait
}
```

không hợp lệ nếu `dyn Trait` là unsized.

Phải dùng:

```axiom
struct Good {
    data: Box<dyn Trait>
}
```

hoặc:

```axiom
struct Good {
    data: view<dyn Trait>
}
```

---

# 53. `Sized`

Generic parameter mặc định:

```text
T: Sized
```

Ví dụ:

```axiom
struct Container<T> {
    value: T
}
```

yêu cầu T có finite representation.

Nếu abstraction cần unsized:

```text
T: ?Sized
```

phải explicit.

---

# 54. `view<T>` and unsized T

Một `view<T>` có thể trỏ tới unsized semantic type vì view representation mang metadata cần thiết.

Ví dụ:

```axiom
fn render(x: view<dyn Renderable>) { ... }
```

Conceptually:

```text
data pointer
metadata/dispatch pointer
```

---

# 55. Field projection

```axiom
user.name
```

giữ provenance.

Nếu:

```axiom
let v = view(user)
```

thì:

```axiom
v.name
```

là sub-region capability:

```text
provenance = user
region = name field
access = READ
```

Không tạo ownership.

---

# 56. Disjoint fields

Compiler có thể chứng minh:

```axiom
let a = mut_view(user.name)
let b = mut_view(user.age)
```

không conflict nếu fields thực sự disjoint.

Do đó Axiom không cần cấm mọi simultaneous mutable access.

Rule là:

> **Conflict depends on region overlap, not merely on same owner.**

---

# 57. Same field conflict

Ngược lại:

```axiom
let a = mut_view(user.name)
let b = mut_view(user.name)
```

→ compile error.

Vì:

```text
region(a) == region(b)
access(a) = WRITE
access(b) = WRITE
```

---

# 58. Unknown overlap

Nếu compiler không chứng minh được:

```text
region A DISJOINT region B
```

thì safe code không được giả định chúng disjoint.

Ví dụ hai dynamic slices:

```axiom
a = buffer.subslice(...)
b = buffer.subslice(...)
```

nếu ranges có thể overlap:

```text
UNKNOWN
```

→ simultaneous mutable capabilities bị từ chối nếu abstraction không cung cấp proof.

---

# 59. Struct and methods

Struct vẫn có thể có hàng trăm methods mà không trở thành class.

```axiom
impl Image {
    fn resize(self: mut_view<Self>, w: usize, h: usize) { ... }
    fn save(self: view<Self>, path: view<Text>) -> Result<(), Error> { ... }
}
```

Compiler vẫn có thể inline toàn bộ.

Không có virtual method mặc định.

---

# 60. Trait implementation

```axiom
trait Serialize {
    fn serialize(self: view<Self>) -> Bytes
}

impl Serialize for User {
    fn serialize(self: view<User>) -> Bytes {
        ...
    }
}
```

Trait implementation là compile-time relationship.

Không tự tạo vtable.

---

# 61. Dynamic trait storage

Chỉ khi:

```axiom
Box<dyn Serialize>
```

hoặc:

```axiom
view<dyn Serialize>
```

thì dynamic dispatch representation xuất hiện.

Do đó:

```text
trait
≠
vtable
```

và:

```text
struct
≠
object
```

---

# 62. Struct/Enum semantic invariants

### ADATA-20 — Struct Is The Primary Aggregate

Struct là aggregate primitive của Axiom.

### ADATA-21 — Struct Has No Implicit Object Header

Không có hidden header.

### ADATA-22 — Struct Has No Implicit Inheritance

Inheritance không phải Core construct.

### ADATA-23 — Behavior Is Separate From Data

Function/trait cung cấp behavior.

### ADATA-24 — Method Syntax Is Function Sugar

Method không tạo hidden object dispatch.

### ADATA-25 — Newtype Creates Distinct Type Identity

Tuple/newtype struct tạo type mới.

### ADATA-26 — Type Alias Preserves Type Identity

Alias không tạo type mới.

### ADATA-27 — Struct Construction Is Explicit

Không có implicit field initialization.

### ADATA-28 — Field Visibility Is Compile-Time

Visibility không tạo runtime mechanism.

### ADATA-29 — Ordinary Struct Layout Is Compiler-Controlled

Layout không stable nếu không có representation contract.

### ADATA-30 — `repr(C)` Freezes C-Compatible Layout

C ABI representation là explicit.

### ADATA-31 — Packed Access Preserves Alignment Safety

Packed representation không cho phép compiler tạo invalid safe access.

### ADATA-32 — ZST Has Semantic Identity But No Required Storage

Zero-sized type không cần physical storage.

### ADATA-33 — Recursive Inline Types Must Have Finite Representation

Recursive infinite layout bị reject.

### ADATA-34 — Indirection Is Explicit

Compiler không tự thêm Box/heap indirection.

### ADATA-35 — Enum Is A Sum Type

Enum biểu diễn algebraic alternatives.

### ADATA-36 — Enum Representation Is Compiler-Controlled

Discriminant encoding không observable mặc định.

### ADATA-37 — Niche Optimization Is Permitted

Compiler có thể dùng invalid/niche representation.

### ADATA-38 — Option Is An Ordinary Enum

`Option<T>` không cần null runtime primitive.

### ADATA-39 — Result Is An Ordinary Enum

`Result<T,E>` không cần exception runtime.

### ADATA-40 — Pattern Access Requires Variant Knowledge

Payload không được truy cập nếu variant chưa được xác định.

### ADATA-41 — Enum Payload Ownership Is Tracked

Move/Copy/Drop áp dụng cho payload.

### ADATA-42 — Match Does Not Duplicate Payload

Pattern không clone ngầm.

### ADATA-43 — Partial Move Is Field-Precise

Ownership tracking có thể xuống tới field.

### ADATA-44 — Custom Drop Forbids Partial Move

User-defined Drop yêu cầu toàn-object integrity.

### ADATA-45 — Field Projection Preserves Provenance

Projection không mất capability provenance.

### ADATA-46 — Disjoint Field Capabilities May Coexist

Các vùng không overlap có thể truy cập đồng thời.

### ADATA-47 — Unknown Overlap Is Not Assumed Disjoint

Compiler không đoán alias safety.

### ADATA-48 — Storage Identity Is Not Value Identity

Struct value không tự có object identity.

### ADATA-49 — Box Provides Explicit Storage Identity

Dynamic owning storage là explicit abstraction.

### ADATA-50 — Stable Address Requires Storage Contract

Address stability không tự tồn tại.

### ADATA-51 — Logical Identity Is Library-Level

Handle/EntityId là logical identity, không phải address.

### ADATA-52 — Generic Layout Is Type-Dependent

Concrete generic instantiation quyết định representation.

### ADATA-53 — Unsized Fields Require Explicit Indirection

Không embed unsized dynamic type trực tiếp.

### ADATA-54 — Dynamic Trait Representation Is Explicit

`dyn Trait` mới yêu cầu dynamic representation.

### ADATA-55 — Union Is Not Ordinary Safe Sum Type

Union không thay thế enum.

### ADATA-56 — Bitfields Are Not Core Struct Semantics

Binary layout complexity nằm ở system/representation layer.

---

# 63. Data model của Axiom hiện tại

Đến đây data model có thể biểu diễn:

```text
                    Data
                      │
          ┌───────────┴───────────┐
          │                       │
       Product                  Sum
          │                       │
       struct                    enum
          │                       │
   ┌──────┼──────┐          ┌─────┼─────┐
   │      │      │          │     │     │
 value  tuple   ZST       unit  tuple  struct
```

Trong đó ownership nằm **trên value**, không nằm trong class hierarchy.

---

# 64. Điểm quan trọng đối với mục tiêu "nhanh hơn C/C++"

Axiom hiện không ép programmer phải trả giá runtime cho abstraction:

```text
struct
    ↓
plain data

method
    ↓
function

trait
    ↓
static dispatch

generic
    ↓
compile-time specialization

enum
    ↓
optimized tagged/niche representation

closure
    ↓
compiler-generated environment

Box
    ↓
only when storage semantics require

dyn Trait
    ↓
only when dynamic dispatch required
```

Do đó đường đi tối ưu nhất vẫn có thể là:

```text
Axiom source
   ↓
Typed HIR
   ↓
MIR
   ↓
ownership/capability verification
   ↓
scalarization / inlining / specialization
   ↓
machine code
```

không cần một object runtime phổ quát.

---

# Part XII — Traits · Generics · Method Resolution · Dispatch

Phần kế tiếp sẽ khóa nốt **behavioral type system**, đặc biệt là vấn đề bạn đã hỏi trước đây:

> Nếu không có class và method thực chất là function có `self` ở đầu, thì **override** sẽ hoạt động thế nào?

Đây là lúc phải phân biệt rất rõ:

```text
1. Inherent method
2. Trait implementation
3. Extension method
4. Generic method
5. Static dispatch
6. Dynamic dispatch
7. Method replacement/override
8. Default trait method
9. Specialization
10. Coherence
```

Và tôi sẽ chốt một nguyên tắc quan trọng:

> **Axiom không có "override method" theo nghĩa class inheritance.**

Thay vào đó sẽ có **trait implementation selection** và **explicit dynamic dispatch**.

Điều này cho phép đạt được behavior polymorphism mà không mang theo toàn bộ complexity của class/vtable/inheritance.