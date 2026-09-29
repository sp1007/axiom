# AXIOM LANGUAGE SPECIFICATION v0.1
# Part XII — Traits · Generics · Method Resolution · Dispatch

Phần này khóa **behavioral type system** của Axiom.

Mục tiêu là giải quyết dứt điểm vấn đề:

> Nếu Axiom không có class/inheritance, thì polymorphism, method override, interface và dynamic dispatch hoạt động thế nào?

Quyết định cốt lõi:

> **Axiom không có method override theo mô hình class inheritance.**
>
> Thay vào đó, Axiom có **trait implementation**, **default behavior**, **static dispatch** và **explicit dynamic dispatch**.

Điều này giữ được polymorphism mà không cần biến mọi object thành một object runtime có vtable.

---

# 1. Trait là behavioral contract

Ví dụ:

```axiom
trait Drawable {
    fn draw(self: view<Self>)
}
```

Trait nói:

```text
Type T
    phải cung cấp
        draw(view<T>)
```

Trait không nói:

```text
T phải kế thừa object nào
```

và cũng không yêu cầu:

```text
object header
vtable pointer
runtime type information
```

---

# 2. Implement trait

```axiom
struct Circle {
    radius: f32
}

impl Drawable for Circle {
    fn draw(self: view<Circle>) {
        ...
    }
}
```

Compiler tạo semantic relationship:

```text
Drawable(Circle)
```

Đây là compile-time fact.

---

# 3. Trait không phải class

Không có:

```text
class Circle : Drawable
```

và:

```text
Drawable* p
```

không tự xuất hiện.

Muốn dynamic dispatch phải yêu cầu rõ:

```axiom
view<dyn Drawable>
```

hoặc:

```axiom
Box<dyn Drawable>
```

---

# 4. Static dispatch mặc định

Ví dụ:

```axiom
fn render<T: Drawable>(x: view<T>) {
    x.draw()
}
```

Khi gọi:

```axiom
render(circle)
```

compiler biết:

```text
T = Circle
```

và có thể tạo:

```text
render<Circle>
```

Sau optimization:

```text
render<Circle>
    ↓
Circle::draw
    ↓
inline
```

Không cần vtable.

---

# 5. Dynamic dispatch phải explicit

Nếu cần heterogeneous collection:

```axiom
let objects: Vec<Box<dyn Drawable>>
```

thì dynamic dispatch được yêu cầu.

Conceptually:

```text
Box<dyn Drawable>
    ├── data pointer
    └── dispatch metadata
```

Không có object header bắt buộc.

---

# 6. `dyn Trait` là dynamic capability/type

```axiom
fn render(x: view<dyn Drawable>) {
    x.draw()
}
```

Ở đây compiler không biết concrete type tại compile site.

Nó sử dụng dispatch metadata.

---

# 7. Static và dynamic dispatch là hai semantic lựa chọn

```axiom
fn draw_static<T: Drawable>(x: view<T>)
```

khác:

```axiom
fn draw_dynamic(x: view<dyn Drawable>)
```

Không có heuristic:

```text
compiler tự quyết định đổi static thành dynamic
```

vì điều đó có thể thay đổi observable semantics như:

- function pointer identity
- dispatch behavior
- code size
- ABI
- performance characteristics

Compiler vẫn có thể **devirtualize** dynamic call khi chứng minh được concrete target mà không thay đổi semantics.

---

# 8. Default trait method

Trait có thể cung cấp implementation mặc định:

```axiom
trait Printable {
    fn print(self: view<Self>) {
        ...
    }
}
```

Type:

```axiom
struct User {
    id: u64
}

impl Printable for User {}
```

`User` sử dụng default implementation.

---

# 9. Trait method override tương đương

Nếu muốn thay default behavior:

```axiom
impl Printable for User {
    fn print(self: view<User>) {
        ...
    }
}
```

đây chính là **thay thế trait implementation mặc định**.

Không phải inheritance override.

Semantic:

```text
Printable::print(User)
```

được resolve tới implementation cụ thể của `User`.

---

# 10. Không có override từng subclass

Không có:

```text
Animal
 ├── Dog
 └── Cat
```

và:

```text
Dog.override speak()
```

Thay vào đó:

```axiom
trait Animal {
    fn speak(self: view<Self>)
}

impl Animal for Dog {
    fn speak(...) { ... }
}

impl Animal for Cat {
    fn speak(...) { ... }
}
```

Đây là **ad-hoc polymorphism có kiểm soát**.

---

# 11. Một type có thể implement nhiều trait

```axiom
struct User {
    id: u64
}

impl Printable for User { ... }
impl Serializable for User { ... }
impl Comparable for User { ... }
impl Hashable for User { ... }
```

Không có giới hạn "single inheritance".

---

# 12. Trait có thể phụ thuộc trait khác

```axiom
trait Ordered: Comparable + Equatable {
    ...
}
```

Có nghĩa:

```text
Ordered(T)
requires
Comparable(T)
Equatable(T)
```

Không tạo inheritance của data.

Đây là **behavioral constraint composition**.

---

# 13. Trait inheritance không phải type inheritance

Nếu:

```axiom
trait Ordered: Comparable
```

thì:

```text
Ordered(T)
⇒ Comparable(T)
```

nhưng không có:

```text
Ordered object
is a
Comparable object
```

theo object layout.

Nó chỉ là relationship trong type system.

---

# 14. Supertrait method

Ví dụ:

```axiom
trait Comparable {
    fn compare(self: view<Self>, other: view<Self>) -> i32
}

trait Ordered: Comparable {
    fn less(self: view<Self>, other: view<Self>) -> bool {
        self.compare(other) < 0
    }
}
```

`less` có thể sử dụng contract của `Comparable`.

---

# 15. Associated types

Trait có thể khai báo associated type:

```axiom
trait Iterator {
    type Item

    fn next(self: mut_view<Self>) -> Option<Self.Item>
}
```

Implementation:

```axiom
impl Iterator for IntRange {
    type Item = i32

    ...
}
```

Compiler biết:

```text
Iterator::Item(IntRange) = i32
```

---

# 16. Associated type không phải runtime metadata

`Item` ở trên không yêu cầu:

```text
type descriptor
runtime type object
reflection table
```

nếu không có explicit runtime reflection.

Nó là compile-time relationship.

---

# 17. Generic function

```axiom
fn max<T: Ord>(a: T, b: T) -> T {
    if a > b { a } else { b }
}
```

Compiler cần chứng minh:

```text
T: Ord
```

rồi resolve operator tương ứng.

---

# 18. Generic type

```axiom
struct Pair<A, B> {
    first: A
    second: B
}
```

Sử dụng:

```axiom
let p = Pair {
    first: 10,
    second: 20.0
}
```

Compiler suy ra:

```text
Pair<i32, f64>
```

---

# 19. Generic parameter mặc định Sized

```axiom
fn process<T>(x: T) {
    ...
}
```

tương đương semantic:

```text
T: Sized
```

Nếu cần unsized:

```axiom
fn process<T: ?Sized>(x: view<T>) {
    ...
}
```

---

# 20. Generic constraints

Có thể viết:

```axiom
fn send<T: Serialize + Send>(x: T) {
    ...
}
```

hoặc:

```axiom
fn send<T>(x: T)
where
    T: Serialize + Send
{
    ...
}
```

Hai syntax biểu diễn cùng semantic constraint.

---

# 21. Constraint không phải runtime check

```axiom
T: Send
```

không tạo:

```text
if runtime_is_send(T)
```

Compiler phải chứng minh constraint tại compile time.

---

# 22. Auto trait derivation

Các trait hệ thống như:

```text
Copy
Send
Share
Sized
```

có thể được compiler tự suy ra khi các field thỏa điều kiện.

Ví dụ:

```axiom
struct Point {
    x: i32
    y: i32
}
```

compiler có thể suy ra:

```text
Copy
Send
Share
Sized
```

nếu các điều kiện tương ứng được thỏa.

---

# 23. User-defined trait implementation không tự động

Nếu:

```axiom
trait Serializable {
    fn serialize(...)
}
```

thì compiler không tự đoán rằng mọi struct đều Serializable.

Có thể dùng:

```axiom
@derive(Serializable)
struct User {
    ...
}
```

nếu trait hỗ trợ compiler-derived implementation.

---

# 24. `@derive` không phải macro

`@derive(Serializable)` là compiler semantic operation.

Nó không chạy một textual macro.

Compiler biết:

```text
trait
fields
types
constraints
```

và sinh implementation có cấu trúc.

---

# 25. Method resolution

Khi viết:

```axiom
x.foo()
```

compiler resolve theo thứ tự:

```text
1. Inherent method
2. Applicable trait implementation
3. Explicitly imported extension method
4. Generic extension fallback
```

Đây là thứ tự deterministic.

---

# 26. Inherent method thắng trait method

Ví dụ:

```axiom
struct User {}

impl User {
    fn print(self: view<User>) {
        ...
    }
}

trait Printable {
    fn print(self: view<Self>)
}

impl Printable for User {
    fn print(self: view<User>) {
        ...
    }
}
```

Khi:

```axiom
user.print()
```

→ inherent method được chọn.

---

# 27. Không silently override inherent method bằng extension

Ví dụ package khác:

```axiom
fn print(self: view<User>) {
    ...
}
```

không được phép âm thầm thay đổi:

```text
user.print()
```

nếu inherent method đã tồn tại.

Nếu ambiguity hoặc conflict:

```text
compile error
```

---

# 28. Explicit qualification

Có thể gọi trait method rõ ràng:

```axiom
Printable.print(user)
```

hoặc syntax tương đương được chọn trong grammar cuối.

Điều này rất quan trọng khi nhiều traits có cùng method name.

---

# 29. Ambiguous method resolution

Nếu:

```axiom
trait A {
    fn foo(self: view<Self>)
}

trait B {
    fn foo(self: view<Self>)
}
```

và:

```axiom
impl A for User {}
impl B for User {}
```

thì:

```axiom
user.foo()
```

→ compile error nếu cả hai đều applicable.

Compiler không tự chọn dựa trên:

- import order
- source order
- package order
- "gần nhất"
- heuristic

---

# 30. Explicit qualification giải quyết ambiguity

Programmer có thể chỉ rõ trait:

```axiom
A.foo(user)
```

hoặc:

```axiom
B.foo(user)
```

Không cần đổi tên method chỉ để giải quyết namespace collision.

---

# 31. Extension methods

Một package có thể thêm behavior cho type mà không sửa type:

```axiom
fn magnitude(self: view<Vec2>) -> f32 {
    ...
}
```

Sau khi import:

```axiom
import math.extensions
```

có thể:

```axiom
v.magnitude()
```

Semantic vẫn là ordinary function call.

---

# 32. Extension không thay đổi type

Extension:

```text
không
├── thêm field
├── thêm storage
├── thêm vtable
├── sửa layout
└── sửa type identity
```

Nó chỉ mở rộng name resolution.

---

# 33. Foreign type / foreign trait coherence

Không cho phép:

```text
trait của package A
type của package B
```

được implement tùy ý bởi package C.

Rule:

```text
trait local
OR
type local
```

mới được phép implement.

---

# 34. Coherence

Ví dụ package `graphics` định nghĩa:

```axiom
trait Render {}
```

package `engine` định nghĩa:

```axiom
struct Mesh {}
```

package thứ ba không được:

```axiom
impl Render for Mesh {}
```

nếu cả trait và type đều foreign.

Lý do:

- tránh conflicting implementations
- method resolution deterministic
- dependency order không thay đổi semantics

---

# 35. Orphan rule

Quy tắc:

```text
At least one of:
    Trait is local
    Type is local
```

được gọi là coherence/orphan rule.

Đây là **compile-time rule**, không runtime mechanism.

---

# 36. Specialization

Axiom v0.1 **không cho user-defined specialization**.

Không cho:

```axiom
impl<T> Foo for T { ... }

impl Foo for i32 { ... } // override generic impl
```

nếu điều này tạo overlap.

---

# 37. Vì sao không specialization trong v0.1?

Specialization dễ làm method/trait resolution phụ thuộc vào:

```text
which impl is more specific?
```

và có thể gây:

```text
semantic instability
compile-order sensitivity
coherence problems
code generation explosion
```

Axiom ưu tiên deterministic semantics.

---

# 38. Compiler vẫn được specialization

Compiler có thể tối ưu:

```text
generic T
```

thành specialized machine code.

Nhưng programmer không được quan sát việc đó.

Ví dụ:

```text
T = i32
```

compiler có thể inline/vectorize.

Không được phép semantics thay đổi vì optimization.

---

# 39. Specialization Is Not Observable

Hai chương trình:

```text
generic implementation
```

và:

```text
specialized machine implementation
```

phải có cùng observable semantics.

Compiler không thể cho phép:

```text
if specialized then different behavior
```

chỉ vì optimization.

---

# 40. Generic monomorphization

Default strategy:

```text
Generic Source
      ↓
constraint resolution
      ↓
concrete instantiation
      ↓
MIR
      ↓
optimization
```

Ví dụ:

```text
max<i32>
max<f32>
max<MyType>
```

có thể tạo các MIR instances riêng.

---

# 41. Code sharing

Compiler vẫn có thể merge code khi representation/semantics cho phép.

Ví dụ:

```text
T = different types
```

nhưng machine representation tương thích.

Compiler có thể chia sẻ implementation.

Programmer không cần biết.

---

# 42. Generic code không yêu cầu runtime type information

Ví dụ:

```axiom
fn add<T: Add>(a: T, b: T) -> T
```

không tự mang:

```text
TypeInfo*
```

vào runtime.

Nếu implementation có thể static resolve, toàn bộ type metadata biến mất.

---

# 43. `impl Trait`

Ví dụ:

```axiom
fn make_shape() -> impl Drawable {
    Circle { radius: 1.0 }
}
```

`impl Drawable` nghĩa:

> hàm trả về một concrete type bí mật nhưng statically known.

Nó **không phải dynamic dispatch**.

---

# 44. `impl Trait` return

Compiler vẫn biết concrete type.

Ví dụ semantic:

```text
make_shape()
    → Circle
```

nhưng caller không cần biết source-level identity của Circle.

Không cần vtable.

---

# 45. `dyn Trait`

Ngược lại:

```axiom
fn make_shape() -> Box<dyn Drawable>
```

cho phép concrete type runtime thay đổi.

Ví dụ:

```text
Circle
Square
Triangle
```

cùng nằm trong:

```text
Vec<Box<dyn Drawable>>
```

Dynamic dispatch là explicit.

---

# 46. `dyn Trait` object safety

Không phải trait nào cũng có thể trở thành `dyn Trait`.

Ví dụ trait có method:

```axiom
trait Bad {
    fn create() -> Self
}
```

không phù hợp dynamic object nếu method yêu cầu biết concrete `Self` theo cách không thể biểu diễn qua dynamic boundary.

Compiler phải kiểm tra object safety.

---

# 47. Object-safe trait

Một trait usable as `dyn Trait` phải đáp ứng object-safety rules.

Các rule chính:

- dispatchable methods phải có representation khả thi qua dynamic receiver
- không yêu cầu concrete `Self` ở return/argument nếu không thể erase
- generic methods không được dynamic dispatch trực tiếp
- associated type constraints phải có dynamic interpretation nếu được expose
- static-only methods không trở thành dynamic dispatch automatically

---

# 48. Dynamic dispatch ABI

Conceptually:

```text
dyn Trait
├── data_ptr
└── dispatch_ptr
```

Dispatch metadata có thể chứa:

```text
method pointers
drop function
size/alignment metadata
associated dynamic metadata
```

Representation thực tế target-dependent.

Không được coi đây là stable ABI trừ khi explicit ABI contract.

---

# 49. Ownership và `dyn Trait`

Hai thứ độc lập:

```text
Box<dyn Trait>
```

= owning dynamic object.

```text
view<dyn Trait>
```

= non-owning dynamic capability.

Có thể có:

```text
Arc<dyn Trait>
```

= shared owning dynamic object.

Không có một "object pointer" primitive duy nhất.

---

# 50. Dynamic dispatch không yêu cầu heap

Ví dụ:

```axiom
fn draw(x: view<dyn Drawable>) {
    x.draw()
}
```

không yêu cầu heap.

Caller có thể có object trên:

```text
stack
arena
static
embedded storage
device memory
```

miễn representation contract phù hợp.

---

# 51. Dynamic object không đồng nghĩa dynamic allocation

Đây là distinction quan trọng:

```text
dynamic dispatch
≠
heap allocation
```

Có thể có:

```text
stack object
   ↓
view<dyn Trait>
   ↓
dynamic call
```

---

# 52. Dynamic dispatch và optimizer

Nếu compiler biết:

```text
dyn Trait
```

chỉ có một possible implementation trong toàn compilation unit/link graph và devirtualization không thay đổi observable semantics, compiler có thể biến:

```text
dynamic call
```

thành:

```text
direct call
```

Nhưng semantics vẫn được định nghĩa là dynamic dispatch.

---

# 53. Trait implementation selection

Với:

```axiom
fn render<T: Drawable>(x: view<T>)
```

compiler phải resolve:

```text
Drawable(T)
```

thành chính xác một implementation.

Các trạng thái:

```text
PROVEN
DISPROVEN
AMBIGUOUS
OVERFLOW
```

---

# 54. Ambiguous trait resolution

Nếu compiler không biết implementation nào phù hợp:

```text
AMBIGUOUS
```

→ compile error.

Không thử random candidate.

Không phụ thuộc:

```text
source order
package order
compiler hash order
```

---

# 55. Trait solver overflow

Nếu resolution vượt:

```text
depth
steps
recursive cycle
```

thì:

```text
OVERFLOW
```

→ compile error.

Không được treo compiler vô hạn.

---

# 56. Recursive trait constraints

Ví dụ:

```text
A<T> requires B<T>
B<T> requires A<T>
```

solver phải phát hiện cycle.

Không được tạo infinite recursion.

---

# 57. Method resolution và generic inference

Ví dụ:

```axiom
x.foo(y)
```

compiler không được chọn method trước rồi ép type inference vào kết quả.

Quá trình phải deterministic:

```text
name lookup
→ candidate set
→ receiver compatibility
→ generic constraint solving
→ exact applicable candidate
→ ambiguity check
→ selected function
```

---

# 58. Không có implicit conversion để cứu method resolution

Ví dụ:

```axiom
fn foo(x: i64)
fn foo(x: f64)
```

và:

```axiom
foo(1)
```

không được giải quyết bằng một hệ thống conversion ranking phức tạp.

Numeric literal inference phải xác định expected type nếu context rõ.

Nếu không rõ:

```text
compile error
```

---

# 59. Operator overloading

Operators là syntax sugar cho trait operations.

Ví dụ conceptually:

```text
a + b
```

resolve thành:

```text
Add.add(a, b)
```

nhưng compiler có thể lower trực tiếp thành machine instruction.

---

# 60. Operator overloading không tạo magic semantics

Nếu type định nghĩa:

```axiom
impl Add for Vector {
    ...
}
```

thì:

```axiom
a + b
```

là ordinary trait call semantic.

Không có special hidden behavior.

---

# 61. Built-in primitive operators

Primitive:

```text
i32 + i32
f32 * f32
```

được compiler intrinsic xử lý.

Không nhất thiết instantiate generic trait machinery nếu compiler có primitive lowering.

Semantic vẫn tương thích với operator model.

---

# 62. Equality

`==` phải có semantic contract rõ ràng.

Không tự động có:

```text
pointer identity
object identity
deep equality
```

cho mọi type.

Type phải cung cấp equality semantics phù hợp hoặc compiler intrinsic cho primitive.

---

# 63. Hashing

Hash cũng không phải implicit universal behavior.

Nếu cần:

```axiom
trait Hash {
    fn hash(self: view<Self>, state: mut_view<Hasher>)
}
```

thì container yêu cầu:

```text
T: Hash
```

Compiler không tự đoán hash của arbitrary struct trừ khi `@derive(Hash)`.

---

# 64. Trait coherence và package version

Package A:

```text
trait T
```

package B:

```text
struct S
```

package C không được thêm:

```text
impl T for S
```

vì nếu nhiều dependency khác nhau cùng làm vậy, semantics của `S.method()` sẽ trở nên dependency-graph-dependent.

Coherence ngăn điều này.

---

# 65. Trait implementation là một phần public API

Nếu package public:

```axiom
impl Serialize for User
```

thì implementation đó là semantic API information.

Nó có thể ảnh hưởng:

```text
method resolution
generic satisfaction
overload availability
derived behavior
```

Do đó semantic interface fingerprint phải chứa public trait implementations.

---

# 66. Không có "monkey patching"

Không có cơ chế kiểu:

```text
thay method của type khác
```

ở runtime hoặc package import.

Muốn behavior khác:

```text
wrapper
newtype
trait
explicit function
```

phải được sử dụng.

---

# 67. Newtype để thay behavior

Ví dụ không muốn sửa `u64`:

```axiom
struct UserId(u64)
```

sau đó:

```axiom
impl Display for UserId {
    ...
}
```

Ta có behavior riêng nhưng type safety vẫn rõ.

Đây là thay thế rất mạnh cho một số use case thường cần inheritance/extension hack.

---

# 68. Wrapper/composition thay inheritance

Thay vì:

```text
class AdvancedLogger extends Logger
```

dùng:

```axiom
struct AdvancedLogger {
    inner: Logger
    ...
}
```

và implement các traits cần thiết.

Nếu cần expose behavior:

```axiom
impl AdvancedLogger {
    fn log(...) { ... }
}
```

Không có fragile base-class problem.

---

# 69. Dynamic plugin architecture

Axiom vẫn hỗ trợ plugin architecture:

```text
Plugin ABI
    ↓
extern "C"
    ↓
function table
    ↓
dyn-like dispatch
```

Nhưng plugin ABI phải explicit.

Không giả định Axiom internal trait ABI là stable giữa compiler versions.

---

# 70. C ABI và trait

Không được:

```text
extern "C" fn f(x: dyn Trait)
```

một cách implicit.

Dynamic trait representation không phải C ABI.

Phải tạo explicit ABI wrapper:

```axiom
extern "C" fn plugin_draw(handle: *mut c_void) -> i32
```

hoặc một `#[repr(C)]` function table.

---

# 71. Trait + FFI

Trait implementation có thể wrap FFI:

```axiom
trait File {
    fn read(...)
}
```

và:

```axiom
impl File for NativeFile {
    ...
}
```

nhưng ownership/resource contracts phải được biểu diễn rõ.

Trait không tự che giấu FFI safety obligations.

---

# 72. Generic ABI boundary

Không nên expose:

```axiom
@export("foo")
fn process<T>(x: T)
```

như một native ABI symbol chung.

Generic phải được instantiate hoặc wrapper.

Ví dụ:

```axiom
@export("process_i32")
extern "C" fn process_i32(x: i32) { ... }
```

---

# 73. Trait dispatch matrix

Axiom có bốn trường hợp chính:

| Abstraction | Dispatch | Runtime metadata |
|---|---|---|
| `fn f(x: Concrete)` | direct | không |
| `fn f<T: Trait>(x: T)` | static | không |
| `fn f(x: impl Trait)` | static | không |
| `fn f(x: dyn Trait)` | dynamic | có |

Và ownership độc lập:

| Type | Ownership |
|---|---|
| `T` | owned value |
| `view<T>` | read capability |
| `mut_view<T>` | write capability |
| `Box<T>` | owned storage |
| `Box<dyn Trait>` | owned dynamic object |
| `view<dyn Trait>` | borrowed/read dynamic capability |

---

# 74. Không có class hierarchy nhưng vẫn có polymorphism

Axiom có:

```text
Parametric polymorphism
    ↓
generics

Ad-hoc polymorphism
    ↓
traits

Dynamic polymorphism
    ↓
dyn Trait

Composition polymorphism
    ↓
struct + delegation

Compile-time polymorphism
    ↓
comptime
```

Do đó loại bỏ class không có nghĩa loại bỏ polymorphism.

---

# 75. Method "override" trong Axiom

Ta có thể trả lời chính xác câu hỏi trước đây:

### Class language

```text
Base.foo()
    ↓ override
Derived.foo()
```

### Axiom

```text
trait Foo {
    fn foo(...)
}

impl Foo for Base {
    ...
}

impl Foo for Derived {
    ...
}
```

Static:

```text
T: Foo
```

→ compiler chọn implementation của concrete `T`.

Dynamic:

```text
dyn Foo
```

→ dispatch metadata chọn implementation tương ứng.

**Không cần inheritance để đạt behavior polymorphism.**

---

# 76. Default implementation "override"

Nếu:

```axiom
trait Foo {
    fn foo(self: view<Self>) {
        default_behavior()
    }
}
```

và:

```axiom
impl Foo for A {}
```

thì `A` dùng default.

Nếu:

```axiom
impl Foo for B {
    fn foo(self: view<B>) {
        custom_behavior()
    }
}
```

thì B dùng custom implementation.

Đây là dạng "override" duy nhất ở trait level mà Axiom Core v0.1 cần.

---

# 77. Không cho implementation inheritance

Không có:

```text
impl Derived for Base
```

theo nghĩa "Derived kế thừa toàn bộ implementations".

Nếu cần behavior chung:

```axiom
fn common(...)
```

hoặc trait default method.

---

# 78. Trait dispatch không ảnh hưởng ownership

Ví dụ:

```axiom
fn consume<T: Drawable>(x: T) {
    ...
}
```

`T` vẫn là owned value.

Trait chỉ mô tả behavior.

Có thể:

```text
T
view<T>
mut_view<T>
Box<T>
Box<dyn Trait>
```

mà không thay đổi bản chất ownership rules.

---

# 79. Trait dispatch không tạo implicit lifetime machinery

Compiler vẫn thực hiện:

```text
ownership analysis
capability analysis
escape analysis
```

nhưng programmer không phải viết:

```text
'a
'b
where 'a: 'b
```

Trait system không làm Axiom quay lại mô hình lifetime annotation.

---

# 80. Generic + capability

Ví dụ:

```axiom
fn sort<T: Ord>(data: mut_view<T>) {
    ...
}
```

Compiler phải đồng thời chứng minh:

```text
T: Ord
data: WRITE capability
```

Trait resolution và ownership verification là hai hệ thống phối hợp nhưng độc lập.

---

# 81. Trait + Send/Share

Ví dụ:

```axiom
fn spawn_worker<T: Send>(value: T) {
    ...
}
```

`Send` là capability/property của type.

Không có runtime test.

Nếu `T` chứa:

```text
raw unsafe state
non-Send resource
```

compiler reject safe transfer nếu contract không thỏa.

---

# 82. Trait solver không được trở thành "AI"

Trait resolution phải deterministic.

Compiler không được:

```text
guess
search arbitrary code
execute runtime
ask LLM
```

để quyết định trait satisfaction.

AI tooling có thể đề xuất sửa code, nhưng compiler semantics phải độc lập hoàn toàn.

---

# 83. Trait solver architecture

Đề xuất:

```text
Constraint
    ↓
Normalize
    ↓
Candidate lookup
    ↓
Coherence filtering
    ↓
Unification
    ↓
Associated-type normalization
    ↓
Recursive obligations
    ↓
PROVEN / DISPROVEN / AMBIGUOUS / OVERFLOW
```

Có:

```text
cache
depth limit
step limit
cycle detection
```

---

# 84. Không có implicit conversion trong trait solving

Compiler không được biến:

```text
T: TraitA
```

thành:

```text
convert T → U
then U: TraitA
```

trừ khi conversion đó được yêu cầu explicit trong source.

Điều này tránh trait resolution trở thành một hệ thống search vô hạn.

---

# 85. Generic constraint normalization

Ví dụ:

```axiom
fn foo<T>()
where
    T: Iterator,
    T.Item: Display
```

compiler phải resolve:

```text
T: Iterator
```

sau đó:

```text
Iterator::Item(T)
```

và tiếp:

```text
Iterator::Item(T): Display
```

Tất cả compile-time.

---

# 86. GAT/HKT

Không đưa vào v0.1:

```text
GAT
HKT
dependent types
type-level computation tổng quát
```

Lý do không phải vì chúng "xấu", mà vì chúng làm trait solver phức tạp đáng kể trong khi chưa cần thiết cho core systems language.

Có thể bổ sung sau nếu có use case thực tế.

---

# 87. Trait invariants

### ATRAIT-20 — Trait And Type Are Distinct Semantic Entities

Trait không phải class.

### ATRAIT-21 — Traits Define Behavioral Contracts

Trait mô tả behavior requirements.

### ATRAIT-22 — Trait Implementation Is A Compile-Time Relationship

`impl` không mặc định tạo runtime metadata.

### ATRAIT-23 — Inherent Methods Have Priority

Inherent method thắng trait/extension method.

### ATRAIT-24 — Method Resolution Is Deterministic

Không phụ thuộc source/import order.

### ATRAIT-25 — Ambiguous Method Resolution Is An Error

Compiler không chọn arbitrary candidate.

### ATRAIT-26 — Dynamic Dispatch Is Explicit

Chỉ `dyn Trait` yêu cầu dynamic dispatch.

### ATRAIT-27 — Static Trait Dispatch Is The Default

Generic/impl Trait sử dụng static dispatch.

### ATRAIT-28 — Default Trait Methods Are Overridable By Implementation

Concrete impl có thể cung cấp implementation riêng.

### ATRAIT-29 — Class Inheritance Does Not Exist

Không có inheritance-based method override.

### ATRAIT-30 — Trait Composition Does Not Imply Data Inheritance

Supertrait chỉ là behavioral constraint.

### ATRAIT-31 — Coherence Prevents Conflicting Foreign Implementations

Foreign-for-foreign impl bị cấm.

### ATRAIT-32 — Specialization Is Not User-Observable

Optimization không thay đổi semantics.

### ATRAIT-33 — User Specialization Is Not Core v0.1

Không có overlapping user impl.

### ATRAIT-34 — Trait Resolution Is Finite

Solver phải có giới hạn.

### ATRAIT-35 — Solver Overflow Is A Compile Error

Không infinite search.

### ATRAIT-36 — Generic Constraints Are Compile-Time

Không runtime trait checks mặc định.

### ATRAIT-37 — Associated Types Are Compile-Time Relations

Không tạo runtime metadata mặc định.

### ATRAIT-38 — `impl Trait` Is Static

Không phải dynamic dispatch.

### ATRAIT-39 — `dyn Trait` Is Dynamic

Dynamic dispatch là explicit.

### ATRAIT-40 — Dynamic Trait Does Not Imply Heap Allocation

Heap chỉ là một storage strategy.

### ATRAIT-41 — Ownership And Dispatch Are Orthogonal

`Box<dyn Trait>` và `view<dyn Trait>` có semantics khác nhau.

### ATRAIT-42 — Trait Objects Require Object Safety

Không phải trait nào cũng có thể dynamic dispatch.

### ATRAIT-43 — Dynamic Representation Is Not A Stable ABI By Default

Trait-object ABI không tự trở thành FFI ABI.

### ATRAIT-44 — Operator Resolution Is Trait-Based Or Intrinsic

Không có hidden overload system.

### ATRAIT-45 — Implicit Conversion Cannot Resolve Trait Ambiguity

Conversion phải explicit.

### ATRAIT-46 — Extension Methods Do Not Mutate Type Identity

Extension chỉ ảnh hưởng name resolution.

### ATRAIT-47 — Extension Methods Cannot Silently Replace Inherent Methods

Không monkey patch.

### ATRAIT-48 — Public Trait Implementations Are API Surface

Chúng ảnh hưởng semantic interface.

### ATRAIT-49 — Generic Code Does Not Require Runtime Type Metadata

Monomorphization/static dispatch có thể xóa toàn bộ metadata.

### ATRAIT-50 — Compiler Specialization Is Semantics-Preserving

Optimization không được observable qua semantics.

---

# 88. Kết quả của thiết kế này

Axiom hiện có một mô hình khá khác C++:

```text
C++
│
├── class
├── inheritance
├── virtual
├── templates
├── overload
├── RTTI
└── object lifetime machinery
```

Axiom:

```text
Axiom
│
├── struct          → data
├── function        → behavior
├── trait           → contract
├── generic         → static polymorphism
├── dyn Trait       → dynamic polymorphism
├── composition     → reuse
├── Box             → storage identity
├── Handle          → logical identity
└── compiler        → lifetime/alias/optimization machinery
```

Điểm rất đáng giá là **programmer không phải chọn giữa "đơn giản" và "mạnh"**.

Một chương trình đơn giản:

```axiom
struct Vec2 {
    x: f32
    y: f32
}

fn length(v: view<Vec2>) -> f32 {
    sqrt(v.x * v.x + v.y * v.y)
}
```

có thể compile gần như trực tiếp thành machine code.

Nhưng khi cần abstraction phức tạp:

```text
generic
+
trait
+
associated type
+
dynamic dispatch
+
ownership
+
concurrency
+
FFI
```

Axiom vẫn có semantic machinery đủ mạnh.

---

# Part XIII — Patterns · Destructuring · Match Semantics

Phần tiếp theo cần khóa **pattern system**, bởi vì hiện tại Axiom đã có:

```text
struct
enum
Option
Result
ownership
Move
Copy
view
mut_view
Drop
match
```

Nếu pattern semantics không được khóa kỹ, đây sẽ là nơi dễ xuất hiện bug lớn nhất của compiler.

Phần XIII sẽ chốt:

```text
let patterns
match patterns
struct destructuring
tuple destructuring
enum destructuring
nested patterns
wildcard
binding modes
move vs copy trong pattern
view pattern
refutable / irrefutable pattern
match guard
exhaustiveness
unreachable arm
partial move
Drop interaction
borrow/view interaction
pattern matching trên dyn Trait
```

Đặc biệt sẽ phải giải quyết một vấn đề quan trọng:

> `match user` có được phép **move một field**, trong khi vẫn sử dụng các field còn lại của `user` hay không?

Câu trả lời sẽ được thiết kế thống nhất với **AOWN + ACAP + ADATA**, thay vì tạo thêm một cơ chế lifetime/borrow riêng.