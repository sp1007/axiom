# TRAIT-001 — Trait, Generic & Dispatch System

Đây là một trong những phần lõi nhất của Axiom. Tôi đề xuất khóa kiến trúc theo hướng:

> **Struct chứa dữ liệu. Function chứa hành vi. Trait mô tả contract. `impl` gắn hành vi vào type. Generic tạo abstraction tĩnh. `dyn Trait` tạo dispatch động khi programmer thực sự yêu cầu.**

Không cần `class`, không cần inheritance.

---

## 1. Mô hình cơ bản

```axiom
struct Vec2 {
    x: f32
    y: f32
}

fn length(self: Vec2) -> f32 {
    sqrt(self.x * self.x + self.y * self.y)
}
```

Có thể gọi:

```axiom
let v = Vec2{1, 2}
let n = v.length()
```

Nhưng semantic vẫn là:

```axiom
length(v)
```

Method syntax chỉ là syntax sugar.

---

# 2. Trait

Ví dụ:

```axiom
trait Display {
    fn display(self, out: mut_view<Writer>)
}
```

Type thực hiện trait:

```axiom
impl Display for Vec2 {
    fn display(self, out: mut_view<Writer>) {
        ...
    }
}
```

Không có vtable mặc định.

Không có object header.

Không có runtime registration.

---

# 3. Trait không phải class/interface object

Một trait:

```axiom
trait Drawable {
    fn draw(self)
}
```

không biến:

```axiom
struct Sprite
```

thành một object có:

```text
vptr
typeinfo
object header
```

Thay vào đó:

```text
Sprite
   │
   └── impl Drawable
```

chỉ là quan hệ compile-time.

---

# 4. Generic

Ví dụ:

```axiom
fn max<T: Ord>(a: T, b: T) -> T {
    if a > b { a } else { b }
}
```

Compiler có thể specialize:

```text
max<i32>
max<f32>
max<MyType>
```

thành machine code chuyên biệt.

---

# 5. Static dispatch là mặc định

```axiom
fn render<T: Drawable>(x: T) {
    x.draw()
}
```

Nếu gọi:

```axiom
render(sprite)
```

compiler biết `T = Sprite`.

Call có thể trở thành:

```text
call Sprite::draw
```

Không vtable.

Không indirect call bắt buộc.

---

# 6. Monomorphization

Axiom v1 nên dùng:

> **Monomorphization là chiến lược mặc định cho generic.**

Ví dụ:

```axiom
fn sum<T: Add>(...)
```

Compiler tạo specialization cần thiết.

Ưu điểm:

- inline tốt
- constant propagation
- vectorization
- devirtualization
- không cần generic runtime
- không cần runtime type metadata

---

# 7. Nhưng phải kiểm soát code bloat

Monomorphization có nhược điểm:

```text
foo<i32>
foo<i64>
foo<f32>
foo<MyType1>
foo<MyType2>
...
```

binary có thể phình.

Compiler nên có:

```text
generic deduplication
identical-code folding
cross-specialization optimization
```

và sau này có thể hỗ trợ:

```text
generic code sharing
```

ở Machine/LIR layer.

Programmer không phải lựa chọn.

---

# 8. Generic không nhất thiết là type-level explosion

Ví dụ:

```axiom
fn identity<T>(x: T) -> T {
    x
}
```

Nếu machine representation giống nhau, compiler có thể chia sẻ implementation khi semantics cho phép.

Nhưng đây là compiler optimization.

Semantic vẫn là generic static dispatch.

---

# 9. Associated Type

Một trait có thể có type liên quan:

```axiom
trait Iterator {
    type Item

    fn next(self: mut_view<Self>) -> Option<Self.Item>
}
```

Ví dụ:

```axiom
impl Iterator for IntRange {
    type Item = i32

    ...
}
```

Điều này tốt hơn việc phải truyền thêm generic parameter ở mọi nơi.

---

# 10. Associated constants

Có thể hỗ trợ:

```axiom
trait Numeric {
    const ZERO: Self
    const ONE: Self
}
```

Compiler xử lý như compile-time associated value.

Không cần runtime lookup.

---

# 11. Associated functions

Trait:

```axiom
trait Default {
    fn default() -> Self
}
```

Impl:

```axiom
impl Default for Vec2 {
    fn default() -> Vec2 {
        Vec2{0, 0}
    }
}
```

Gọi:

```axiom
let v = Vec2.default()
```

hoặc:

```axiom
let v = Default::default<Vec2>()
```

Syntax cụ thể có thể chọn sau.

---

# 12. `Self`

Trong trait:

```axiom
trait Clone {
    fn clone(self) -> Self
}
```

`Self` là implementing type.

Không phải dynamic runtime type.

---

# 13. Trait composition

Có thể yêu cầu nhiều trait:

```axiom
fn foo<T: Read + Write + Send>(x: T) {
    ...
}
```

Semantic:

```text
T implements Read
T implements Write
T implements Send
```

Không tạo multiple inheritance.

---

# 14. Supertrait

Có thể:

```axiom
trait Ordered: Eq {
    fn compare(self, other: Self) -> Ordering
}
```

Ý nghĩa:

```text
Ordered requires Eq
```

Không phải inheritance object layout.

Nó chỉ là constraint implication.

---

# 15. Trait inheritance không phải class inheritance

Ví dụ:

```text
Drawable
   ↑
SpriteDrawable
```

không tạo:

```text
SpriteDrawable object
```

hay:

```text
base class storage
```

Nó chỉ tạo quan hệ contract.

Điều này giữ type layout đơn giản.

---

# 16. Extension method

Đây là phần rất quan trọng với triết lý “không class”.

Có:

```axiom
struct String
```

và module khác:

```axiom
fn is_blank(self: StringView) -> bool {
    ...
}
```

Nếu imported:

```axiom
use text_utils.*
```

thì:

```axiom
text.is_blank()
```

hoạt động.

Semantic:

```axiom
is_blank(text)
```

---

# 17. Method resolution

Khóa thứ tự:

```text
1. Inherent function
2. Trait implementation
3. Explicitly imported extension
4. Generic extension
```

Nếu nhiều candidate cùng độ ưu tiên:

```text
compile error: ambiguous method
```

Không âm thầm chọn theo thứ tự import.

---

# 18. Đây chính là cách thay class inheritance

Giả sử trước đây C++:

```cpp
class Animal {
    virtual void speak();
};

class Dog : public Animal {
    void speak() override;
};
```

Axiom:

```axiom
trait Animal {
    fn speak(self)
}

struct Dog {
    ...
}

impl Animal for Dog {
    fn speak(self) {
        ...
    }
}
```

Static dispatch:

```axiom
fn make_speak<T: Animal>(x: T) {
    x.speak()
}
```

`Dog` được chọn compile-time.

---

# 19. Dynamic dispatch

Khi thật sự cần heterogeneous collection:

```axiom
let animals: Vec<dyn Animal>
```

thì programmer **explicitly** yêu cầu dynamic dispatch.

Representation có thể là:

```text
data pointer
vtable pointer
```

nhưng đây là implementation/ABI của `dyn Trait`.

Không đưa vtable vào `Dog`.

---

# 20. `dyn Trait`

Ví dụ:

```axiom
fn run(x: dyn Animal) {
    x.speak()
}
```

Compiler tạo dynamic dispatch.

Cost:

```text
indirect call
possible cache miss
dynamic storage depending on ownership representation
```

Programmer biết mình đang chọn abstraction động.

---

# 21. Không cho implicit conversion thành `dyn Trait`

Không nên:

```axiom
fn foo(x: dyn Animal)

let dog = Dog{}
foo(dog)
```

mà compiler âm thầm:

```text
allocate box
build vtable
```

Đây có thể tạo allocation bất ngờ.

Nên yêu cầu explicit:

```axiom
foo(dyn(dog))
```

hoặc:

```axiom
foo(box_dyn(dog))
```

Syntax cụ thể sẽ khóa ở ownership/trait-object stage.

Nguyên tắc:

> **Dynamic dispatch must be explicit.**

---

# 22. `dyn Trait` và ownership

Cần phân biệt:

```text
dyn Trait
Box<dyn Trait>
view<dyn Trait>
Arc<dyn Trait>
```

Không nên để `dyn Trait` tự mang ownership semantics.

Ví dụ:

```axiom
Box<dyn Drawable>
```

= owning dynamic object.

```axiom
view<dyn Drawable>
```

= non-owning dynamic capability.

```axiom
Arc<dyn Drawable>
```

= shared ownership.

Đây là cách rất sạch.

---

# 23. Vtable

Vtable chỉ tồn tại khi dynamic dispatch.

Ví dụ conceptually:

```text
DrawableVTable:
    draw
    ...
```

Có thể chứa metadata cần thiết cho:

- dispatch
- drop
- size/alignment nếu dynamic ownership cần
- future ABI operations

Nhưng **không mặc định chứa RTTI đầy đủ**.

---

# 24. Runtime type information

Axiom không có:

```text
Object
Any
dynamic_cast
```

trong safe core.

Nếu cần runtime type inspection:

```axiom
dyn Trait
```

có thể cung cấp explicit capability hoặc standard-library RTTI abstraction sau này.

Không tự động đưa RTTI vào mọi object.

---

# 25. Override — giải quyết dứt điểm

Với Axiom không có class, “override” thực chất có hai trường hợp.

### Trường hợp 1 — static replacement

Trait implementation:

```axiom
trait Draw {
    fn draw(self)
}

impl Draw for Dog {
    fn draw(self) {
        ...
    }
}
```

Đây chính là implementation của contract.

Không có `override` keyword cần thiết.

### Trường hợp 2 — dynamic override

Nếu:

```axiom
dyn Draw
```

và object là `Dog`, vtable trỏ tới:

```text
Dog::draw
```

Đây là dynamic override.

---

# 26. Không cho hai impl cùng trait/type

Không được:

```axiom
impl Draw for Dog { ... }
impl Draw for Dog { ... }
```

trong cùng coherent program.

Nếu không, static dispatch và dynamic dispatch đều trở nên ambiguous.

---

# 27. Coherence

Axiom cần quy tắc:

> Một `(Trait, Type)` pair chỉ có một implementation hợp lệ trong toàn bộ coherent program.

Ví dụ:

```axiom
impl MyTrait for MyType
```

chỉ nên được phép nếu:

- trait thuộc current package/module, hoặc
- type thuộc current package/module.

Đây là phiên bản đơn giản của orphan/coherence rule.

---

# 28. Vì sao cần coherence?

Nếu package A:

```axiom
impl Display for Vec
```

package B:

```axiom
impl Display for Vec
```

package C import cả hai.

Compiler không thể biết:

```text
Display<Vec>
```

là implementation nào.

Coherence giải quyết từ gốc.

---

# 29. Generic implementation

Cho phép:

```axiom
impl<T: Display> Display for Box<T> {
    ...
}
```

Compiler áp dụng khi constraint thỏa.

Nhưng vẫn phải đảm bảo không overlap với implementation cụ thể khác.

---

# 30. Specialization

Đây là phần nguy hiểm.

Ví dụ:

```axiom
impl<T> Foo for T { ... }

impl Foo for i32 { ... }
```

Nếu cho phép unrestricted specialization, coherence trở nên cực kỳ phức tạp.

Khuyến nghị:

### v1.0

Có:

```text
generic impl
concrete impl
```

nhưng **không cho specialization tùy ý**.

Sau này mới nghiên cứu specialization có kiểm soát.

---

# 31. Operator overloading

Không nên hardcode:

```text
+
-
*
/
==
<
```

cho mọi type.

Có thể ánh xạ tới trait:

```text
Add
Sub
Mul
Div
Eq
Ord
```

Ví dụ:

```axiom
impl Add for Vec2 {
    fn add(self, rhs: Vec2) -> Vec2 {
        ...
    }
}
```

Sau đó:

```axiom
a + b
```

là syntax sugar.

---

# 32. Operator phải có semantics rõ

Không nên cho phép programmer redefine:

```text
&&
||
```

thành function bình thường vì chúng có short-circuit semantics.

Tương tự:

```text
=
.
::
?
await
```

không phải operator overload tùy ý.

Chỉ các operator phù hợp mới map vào trait.

---

# 33. Generic constraints và inference

Cho phép:

```axiom
fn equal<T: Eq>(a: T, b: T) -> bool
```

và:

```axiom
equal(1, 2)
```

compiler suy ra:

```text
T = i32
```

Nhưng nếu:

```axiom
equal(a, b)
```

mà nhiều candidate:

```text
compile error
```

Không suy đoán tùy tiện.

---

# 34. Type inference không được làm mất tính dễ đọc

Axiom có thể infer:

```axiom
let x = foo()
```

nhưng không nên biến compiler thành theorem prover.

Khi inference thất bại:

```text
error AXTYPE...
cannot infer type T
```

và diagnostic phải chỉ rõ constraint chain.

Đây rất phù hợp với mục tiêu AI-friendly compiler.

---

# 35. Generic bounds có thể kiểm tra compile-time

Ví dụ:

```axiom
fn sort<T: Ord>(x: mut_view<T>)
```

Compiler biết:

```text
T must implement Ord
```

Không cần runtime check.

---

# 36. Trait method có thể có default implementation

Ví dụ:

```axiom
trait Eq {
    fn eq(self, other: Self) -> bool
}

trait Ne: Eq {
    fn ne(self, other: Self) -> bool {
        !self.eq(other)
    }
}
```

Impl chỉ cần:

```axiom
impl Eq for User {
    ...
}
```

`Ne` có thể được cung cấp từ default implementation.

Đây là code reuse compile-time.

Không phải vtable inheritance.

---

# 37. Default method và override

Nếu trait có:

```axiom
trait Printable {
    fn print(self) {
        ...
    }
}
```

Type có thể override:

```axiom
impl Printable for User {
    fn print(self) {
        ...
    }
}
```

Đây chính là “override method” theo nghĩa trait.

Không cần class.

---

# 38. Static vs dynamic default

Ngay cả default trait method:

```axiom
fn print(...)
```

vẫn static dispatch nếu generic.

Chỉ khi:

```axiom
dyn Printable
```

mới đi qua vtable.

---

# 39. Trait object safety

Không phải trait nào cũng có thể trở thành `dyn Trait`.

Ví dụ trait:

```axiom
trait Factory {
    fn create<T>() -> T
}
```

không thể đơn giản biểu diễn bằng một vtable cố định.

Do đó compiler phải kiểm tra **dyn-compatible/object-safe**.

Các nguyên tắc ban đầu:

Một method của `dyn Trait` phải có dispatchable ABI xác định mà không cần generic method-level type unknown.

---

# 40. `Self` trong trait object

Method:

```axiom
fn clone(self) -> Self
```

không trực tiếp compatible với:

```text
dyn Trait
```

vì `Self` runtime-size unknown.

Có thể thay bằng:

```axiom
fn clone_box(self) -> Box<dyn Trait>
```

nếu library muốn dynamic cloning.

---

# 41. Generic và dynamic dispatch có thể kết hợp

```axiom
fn process<T: Drawable>(x: T)
```

static.

Trong function:

```axiom
let x: Box<dyn Drawable>
```

dynamic.

Không có vấn đề.

---

# 42. Trait bound không phải inheritance

```axiom
T: Drawable
```

không nói:

```text
T IS-A Drawable object
```

Nó nói:

```text
T satisfies Drawable contract
```

Điều này quan trọng về mặt thiết kế ngôn ngữ.

---

# 43. Negative impl

v1.0 không cần:

```axiom
impl !Send for T
```

Như memory/concurrency design trước đó:

`Send`, `Share` chủ yếu do compiler derive từ type semantics.

Các ngoại lệ đặc biệt có thể được compiler/library đánh dấu bằng intrinsic/internal mechanism.

Không mở thêm một hệ thống trait complexity chỉ để hỗ trợ negative impl ngay từ đầu.

---

# 44. Trait auto-derivation

Compiler có thể tự derive:

```text
Copy
Send
Share
```

khi các field thỏa điều kiện.

Ví dụ:

```axiom
struct Point {
    x: i32
    y: i32
}
```

compiler biết:

```text
Point: Copy
Point: Send
Point: Share
```

không cần programmer viết boilerplate.

---

# 45. `Drop` và trait

Một type có semantic Drop:

```text
!Copy
```

được compiler bảo đảm.

Trait system không được cho phép:

```text
Copy + Drop
```

xung đột.

---

# 46. Trait dispatch và binary size

Compiler nên có nhiều mức tối ưu:

```text
source generic
      ↓
monomorphization
      ↓
specialization
      ↓
inline
      ↓
dedup / merge
      ↓
machine optimization
```

Nếu specialization quá giống nhau:

```text
fold identical implementations
```

có thể giảm binary size.

---

# 47. ABI của `dyn Trait`

Dynamic trait object cần ABI ổn định **chỉ khi programmer yêu cầu stable ABI/FFI**.

Axiom internal ABI có thể thay đổi.

Nếu:

```axiom
@repr(C)
```

thì phải xác định rõ:

```text
data pointer
vtable pointer
calling convention
layout
```

---

# 48. Không có object header

Một:

```axiom
Box<dyn Trait>
```

có thể conceptually:

```text
┌───────────────┐
│ data pointer  │
│ vtable pointer│
└───────────────┘
```

Nhưng:

```axiom
Box<Concrete>
```

không tự nhiên có vtable pointer.

Đây là điểm giúp concrete types rất nhẹ.

---

# 49. Trait system không được trở thành runtime

Compiler có thể xây:

```text
Trait Solver
```

rất phức tạp.

Nhưng executable cuối cùng chỉ chứa:

```text
code actually needed
```

Trait metadata compile-time được loại bỏ nếu không cần runtime.

Đây là **Abstraction Erasure**.

---

# 50. Trait solver

Kiến trúc compiler nên có một subsystem:

```text
Trait Solver
 ├── type equality
 ├── trait satisfaction
 ├── associated type resolution
 ├── impl lookup
 ├── generic constraint solving
 └── coherence checking
```

Nó hoạt động trước MIR verification.

Không để backend phải hiểu trait.

---

# 51. Dispatch resolution pipeline

Ví dụ:

```axiom
x.draw()
```

Compiler:

```text
1. resolve x type
2. inherent method lookup
3. trait candidate lookup
4. extension lookup
5. generic constraints
6. ambiguity check
7. select implementation
8. lower static/dynamic dispatch
```

Sau bước này:

```text
draw(x)
```

đã được resolve.

MIR không cần hiểu “method”.

---

# 52. Đây là kiến trúc tôi khuyến nghị khóa

```text
                    TRAIT SYSTEM
                         │
          ┌──────────────┼──────────────┐
          │              │              │
       Contract        Generic       Extension
          │              │              │
        impl          static call      method sugar
          │              │
          └───────┬──────┘
                  │
             Dispatch
             /       \
        Static       Dynamic
          │             │
      direct call     vtable
```

Class hierarchy hoàn toàn không cần thiết.

---

# 53. TRAIT-001 invariants

Khóa:

```text
ATRAIT-20  Structs own data; traits define behavior contracts.
ATRAIT-21  Traits do not imply object headers.
ATRAIT-22  Trait implementation is explicit through impl.
ATRAIT-23  Static dispatch is the default.
ATRAIT-24  Generic functions use static dispatch by default.
ATRAIT-25  Monomorphization is the initial generic compilation strategy.
ATRAIT-26  Compiler may share identical generic implementations.
ATRAIT-27  Dynamic dispatch requires explicit dyn semantics.
ATRAIT-28  Dynamic dispatch may use vtables.
ATRAIT-29  Concrete types do not carry vtables unless required by representation.
ATRAIT-30  dyn Trait does not imply ownership.
ATRAIT-31  Ownership is supplied by Box/Arc/etc.
ATRAIT-32  Trait object compatibility is compile-time checked.
ATRAIT-33  Trait methods with incompatible dynamic ABI cannot be dynamically dispatched.
ATRAIT-34  One coherent (Trait, Type) implementation exists.
ATRAIT-35  Overlapping impls are rejected.
ATRAIT-36  Generic impls must satisfy coherence.
ATRAIT-37  Unrestricted specialization is not part of v1.0.
ATRAIT-38  Associated types are compile-time resolved.
ATRAIT-39  Associated constants are compile-time resolved unless explicitly runtime-valued.
ATRAIT-40  Default trait methods may be overridden by an impl.
ATRAIT-41  Override does not imply class inheritance.
ATRAIT-42  Extension methods are ordinary functions with method syntax.
ATRAIT-43  Method resolution is deterministic.
ATRAIT-44  Ambiguous method resolution is a compile error.
ATRAIT-45  Operator overloading uses trait mechanisms.
ATRAIT-46  Control-flow operators cannot be arbitrarily overloaded.
ATRAIT-47  Generic constraints are statically checked.
ATRAIT-48  Trait metadata is compile-time only unless explicitly required.
ATRAIT-49  Trait abstraction may be completely erased after compilation.
ATRAIT-50  Generic dispatch must not require a mandatory runtime.
ATRAIT-51  Trait solver operates before machine lowering.
ATRAIT-52  MIR does not depend on unresolved trait dispatch.
ATRAIT-53  Auto traits may be compiler-derived.
ATRAIT-54  Copy and Drop semantics remain mutually constrained.
ATRAIT-55  Send and Share may be automatically derived.
ATRAIT-56  Trait bounds do not create subtype relationships.
ATRAIT-57  Dynamic trait objects are explicit abstraction boundaries.
ATRAIT-58  Stable trait-object ABI requires explicit ABI contract.
ATRAIT-59  Generic specialization must preserve observable semantics.
ATRAIT-60  Trait dispatch cannot silently introduce dynamic allocation.
```

---

# 54. Một thay đổi quan trọng đối với câu hỏi “override”

Với kiến trúc này, tôi **không khuyến nghị có keyword `override` trong Axiom v1**.

Ví dụ:

```axiom
trait Render {
    fn render(self)
}

impl Render for Button {
    fn render(self) {
        ...
    }
}
```

và:

```axiom
trait Render {
    fn render(self) {
        default_render(self)
    }
}

impl Render for Button {
    fn render(self) {
        custom_render(self)
    }
}
```

Compiler tự biết implementation sau là implementation cụ thể thay thế default.

Nếu programmer muốn compiler cảnh báo rằng họ **đang intended override**, có thể thêm attribute/tooling sau:

```axiom
@override
fn render(...)
```

nhưng nó không cần có semantic weight.

---

# 55. Kiến trúc này đạt đúng mục tiêu ban đầu của bạn

Axiom không cần:

```text
class
inheritance
virtual keyword
override keyword
vptr trong mọi object
RTTI trong mọi object
```

nhưng vẫn có đủ:

```text
data abstraction
behavior abstraction
code reuse
generic programming
static polymorphism
dynamic polymorphism
extension methods
default methods
override
operator overloading
```

và quan trọng nhất:

> **Phần lớn polymorphism bị xóa hoàn toàn trước khi tới machine code.**

---

## Task tiếp theo: TYPE-001 — Type System & Representation

Bây giờ trait đã được khóa, phần tiếp theo cần giải quyết **type system ở mức thấp hơn**, đặc biệt:

- primitive types
- integer semantics
- float semantics
- `unit` / `never`
- tuples
- arrays
- structs
- enums
- recursive types
- zero-sized types
- nullable/niche representation
- type aliases vs newtypes
- transparent types
- layout
- alignment
- padding
- `repr`
- packed structs
- bitfields
- SIMD/vector types
- opaque types
- ABI representation
- type identity
- structural vs nominal typing

Đây sẽ là bước quyết định Axiom có thể vừa **đơn giản ở source level**, vừa cho compiler quyền kiểm soát layout gần với C/ASM hay không.