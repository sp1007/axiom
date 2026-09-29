Tiếp tục. Tôi sẽ chốt **Trait & Generic System v0.1** theo hướng Axiom đang đi: **struct + function + trait + generic**, không class/inheritance, nhưng vẫn phải đủ mạnh để xây compiler, GUI, game engine, networking, AI/tensor, OS-level code.

Điểm quan trọng nhất: **trait không được trở thành "class trá hình"**.

# AXIOM TRAIT & GENERIC SYSTEM v0.1

## 1. Vai trò của `struct`, `trait`, `impl`

Ba thứ có trách nhiệm hoàn toàn khác nhau:

```text
struct
    ↓
DATA / REPRESENTATION

trait
    ↓
BEHAVIOR / CONTRACT

impl
    ↓
RELATIONSHIP giữa behavior và type

generic
    ↓
COMPILE-TIME ABSTRACTION
```

Ví dụ:

```axiom
struct Vec2 {
    x: f32
    y: f32
}

trait Length {
    fn length(self: view<Self>) -> f32
}

impl Length for Vec2 {
    fn length(self: view<Vec2>) -> f32 {
        sqrt(self.x * self.x + self.y * self.y)
    }
}
```

Không có:

```text
class Vec2
extends ...
virtual ...
override ...
```

---

# 2. Method thực chất vẫn chỉ là function

Đây là quyết định tôi muốn giữ rất mạnh.

```axiom
fn length(self: view<Vec2>) -> f32
```

thực chất là:

```axiom
fn length(self: view<Vec2>) -> f32
```

và:

```axiom
v.length()
```

compiler resolve thành:

```axiom
length(view(v))
```

Không có method table gắn vào object.

Không có object header.

Không có hidden `this`.

`self` chỉ là **parameter có receiver position**.

---

# 3. Extension method

Điều này giải quyết một vấn đề lớn của mô hình "struct + function".

Ví dụ `Vec<T>` nằm trong stdlib, ta muốn thêm:

```axiom
fn sum(self: view<Vec<i32>>) -> i32
```

Không cần sửa định nghĩa `Vec`.

```axiom
fn sum(self: view<Vec<i32>>) -> i32 {
    ...
}
```

Compiler cho phép:

```axiom
numbers.sum()
```

nếu function được import.

Nhưng tôi đề xuất **extension method phải có namespace/import rõ ràng**.

Không nên để toàn bộ project tự động mở hàng nghìn method.

Ví dụ:

```axiom
import math.geometry
```

sau đó:

```axiom
point.distance(other)
```

Điều này tránh "method pollution".

---

# 4. Method resolution

Đây là phần cần đặc tả cực kỳ rõ.

Khi gặp:

```axiom
x.foo(a, b)
```

compiler tìm theo thứ tự:

```text
1. inherent function của type X
2. trait impl trực tiếp áp dụng cho X
3. imported extension function
4. generic extension phù hợp
```

Nếu có nhiều candidate cùng mức:

```text
ERROR: ambiguous method
```

Không cố đoán.

Ví dụ:

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
impl A for X ...
impl B for X ...
```

thì:

```axiom
x.foo()
```

→ ambiguity.

Programmer phải chỉ rõ:

```axiom
A.foo(x)
```

hoặc syntax tương đương.

Điều này tốt hơn việc tạo một hệ thống overload resolution khổng lồ kiểu C++.

---

# 5. Trait không có dữ liệu

Trait:

```axiom
trait Drawable {
    fn draw(self: view<Self>)
}
```

không thể chứa:

```text
field
constructor state
object storage
```

Nó chỉ mô tả behavior.

Do đó:

```text
struct
    owns representation

trait
    describes behavior
```

Đây là ranh giới cực kỳ quan trọng.

---

# 6. Trait implementation

```axiom
impl Drawable for Circle {
    fn draw(self: view<Circle>) {
        ...
    }
}
```

Một type có thể implement nhiều trait:

```axiom
impl Drawable for Circle
impl Serialize for Circle
impl Comparable for Circle
impl Cloneable for Circle
```

Không có diamond inheritance.

Không có:

```text
Circle → Shape → Object
```

---

# 7. Trait composition

Nếu cần một behavior tổng hợp:

```axiom
trait Shape: Drawable + Transformable {
    ...
}
```

Ý nghĩa:

```text
Shape
requires:
    Drawable
    Transformable
```

Nó **không tạo inheritance hierarchy**.

Đây chỉ là trait constraints.

Ví dụ:

```axiom
fn render<T: Shape>(x: view<T>)
```

compiler hiểu:

```text
T implements Shape
T therefore satisfies Shape's required contracts
```

---

# 8. Generic là compile-time abstraction

Ví dụ:

```axiom
fn max<T: Comparable>(a: T, b: T) -> T {
    if a > b {
        a
    } else {
        b
    }
}
```

Không có runtime generic object.

Compiler:

```text
max<i32>
max<f32>
max<MyType>
```

có thể tạo specialization riêng.

Pipeline:

```text
Generic HIR
      ↓
constraint solving
      ↓
specialization
      ↓
typed MIR
      ↓
optimization
```

---

# 9. Generic không phải C++ macro substitution

Axiom không nên copy mô hình:

```text
template text
    ↓
substitute text
    ↓
parse again
```

Thay vào đó:

```text
source
 ↓
AST
 ↓
HIR
 ↓
generic typed HIR
 ↓
constraint resolution
 ↓
instantiation
 ↓
typed MIR
```

Điều này cho compiler:

- diagnostics tốt hơn
- deterministic hơn
- dễ cache
- dễ IDE tooling
- dễ AI tooling
- không phụ thuộc textual substitution.

---

# 10. Trait constraint

Cú pháp đơn giản:

```axiom
fn sort<T: Comparable>(xs: mut_view<T>)
```

Có thể có nhiều constraint:

```axiom
fn foo<T: A + B + C>(x: T)
```

Nhưng tôi **không muốn** có một hệ thống constraint language quá phức tạp trong v0.1.

Không:

```text
where
    T::Item: Foo<U::Bar>
    U: ...
    associated recursive constraints ...
```

ngay từ đầu.

Nếu cần sau này có:

```axiom
where ...
```

thì bổ sung.

---

# 11. Associated Type

Cái này tôi nghĩ nên có.

Ví dụ:

```axiom
trait Iterator {
    type Item

    fn next(self: mut_view<Self>) -> Option<Self.Item>
}
```

Sau đó:

```axiom
impl Iterator for IntRange {
    type Item = i32
}
```

Compiler biết:

```text
IntRange::Item = i32
```

Generic algorithm:

```axiom
fn consume<I: Iterator>(it: mut_view<I>) {
    ...
}
```

Có thể dùng:

```axiom
I.Item
```

Điều này mạnh hơn việc phải truyền mọi thứ thành generic parameter.

---

# 12. Associated constants

Có thể cần:

```axiom
trait Numeric {
    const ZERO: Self
}
```

và:

```axiom
impl Numeric for i32 {
    const ZERO = 0
}
```

Tôi đề xuất **cho phép**, nhưng compiler nên xử lý như compile-time value.

Không phải runtime static field.

---

# 13. Associated functions

Trait có thể định nghĩa function không có receiver:

```axiom
trait Parseable {
    fn parse(text: view<u8>) -> Result<Self, ParseError>
}
```

Implementation:

```axiom
impl Parseable for User {
    fn parse(text: view<u8>) -> Result<User, ParseError> {
        ...
    }
}
```

Có thể gọi:

```axiom
User.parse(text)
```

nhưng semantic vẫn là trait-associated function, không phải class static method.

---

# 14. Constructor không phải language primitive

Tôi không muốn:

```text
constructor
destructor
new
```

thành một hệ thống đặc biệt.

Struct:

```axiom
struct Point {
    x: f32
    y: f32
}
```

tạo value:

```axiom
let p = Point {
    x: 10
    y: 20
}
```

Nếu cần convenience:

```axiom
fn origin() -> Point {
    Point { x: 0, y: 0 }
}
```

hoặc:

```axiom
impl Point {
    fn origin() -> Point { ... }
}
```

Nhưng đó vẫn chỉ là function.

---

# 15. Đây cũng giải quyết vấn đề "override"

Bạn từng hỏi trước đây:

> Nếu chỉ có struct + function thì override function có sẵn thế nào?

Axiom không dùng override theo kiểu class.

Ví dụ:

```axiom
trait Draw {
    fn draw(self: view<Self>)
}
```

Type A:

```axiom
impl Draw for A {
    fn draw(...) { ... }
}
```

Type B:

```axiom
impl Draw for B {
    fn draw(...) { ... }
}
```

Generic:

```axiom
fn render<T: Draw>(x: view<T>) {
    x.draw()
}
```

Compiler specialization:

```text
render<A> → A::draw
render<B> → B::draw
```

Đây chính là "override" ở compile-time.

Không cần virtual dispatch.

---

# 16. Nhưng nếu cần runtime polymorphism?

Axiom vẫn phải hỗ trợ.

Ví dụ GUI:

```text
Widget
 ├── Button
 ├── Label
 ├── TextBox
 └── Image
```

Không biết type cụ thể tại compile time.

Ta cần dynamic dispatch.

Nhưng **dynamic dispatch phải explicit**.

Ví dụ đề xuất:

```axiom
dyn Widget
```

hoặc:

```axiom
WidgetRef
```

Tôi nghiêng về:

```axiom
dyn Widget
```

để thể hiện rõ:

> Đây là runtime polymorphism.

---

# 17. `dyn Trait` không phải object header

Ví dụ:

```axiom
let widgets: Vec<dyn Widget>
```

mỗi element có thể conceptually:

```text
data_ptr
dispatch_ptr
```

hoặc representation khác.

Nhưng:

```text
struct Button
```

vẫn không có:

```text
type_ptr
vtable_ptr
```

trừ khi programmer thực sự chuyển nó thành `dyn Widget`.

Đây là một khác biệt cực lớn với OOP runtime model.

---

# 18. Dynamic dispatch phải trả giá đúng chỗ

Ví dụ:

```axiom
fn draw_widget(w: dyn Widget) {
    w.draw()
}
```

Compiler biết:

```text
DYNAMIC_CALL
```

→ indirect call.

Nhưng:

```axiom
fn draw<T: Widget>(w: view<T>)
```

là:

```text
STATIC_CALL
```

có thể:

- inline
- devirtualize
- specialize
- vectorize
- eliminate hoàn toàn abstraction.

Do đó:

> **Runtime polymorphism explicit; compile-time polymorphism default.**

Tôi nghĩ đây nên là một trong các nguyên tắc lớn của Axiom.

---

# 19. Trait object không được Copy mặc định

Ví dụ:

```axiom
dyn Widget
```

có thể chứa ownership.

Do đó compiler phải biết:

```text
dyn Widget
    Copy?
    Drop?
    Send?
    Share?
```

Không được coi mọi trait object giống nhau.

Nếu trait object sở hữu resource:

```text
!Copy
Drop
```

Nếu nó là shared view:

```text
view<dyn Widget>
```

thì lại là capability không sở hữu.

---

# 20. Generic specialization

Đây là nơi Axiom có thể đạt hiệu năng rất cao.

Ví dụ:

```axiom
fn sum<T: Numeric>(xs: view<T>) -> T
```

Với:

```text
T = i32
```

compiler tạo code tối ưu cho `i32`.

Với:

```text
T = f32
```

code khác.

Nếu `Numeric` cho phép SIMD:

```text
T = f32
```

compiler có thể vectorize.

Không cần runtime generic dispatch.

---

# 21. Nhưng không nên ép monomorphization 100%

Một generic function có thể được sử dụng với:

```text
1000 types
```

Nếu tạo 1000 bản machine code thì binary phình lớn.

Vì vậy compiler nên có chiến lược:

```text
generic
   ↓
specialization
   ├── specialized
   └── shared implementation
```

Ví dụ compiler có thể merge các instantiation có cùng ABI/code shape.

Đây là **implementation detail**, không phải semantic rule.

---

# 22. Coherence / orphan rule

Cần giải quyết vấn đề:

```text
trait từ module A
type từ module B
implementation ở module C
```

Nếu cho phép tự do:

```axiom
impl ForeignTrait for ForeignType
```

hai package có thể tạo conflicting impl.

Tôi đề xuất rule đơn giản:

> Một `impl Trait for Type` phải thuộc về module sở hữu `Trait` hoặc module sở hữu `Type`.

Ví dụ:

```text
MyType       ← tôi sở hữu
ForeignTrait ← người khác
```

→ tôi có thể implement.

Nhưng:

```text
ForeignType
ForeignTrait
```

→ không được.

Đây là orphan rule.

---

# 23. Không cho specialization tùy tiện trong source v0.1

C++ có:

```text
template specialization
partial specialization
SFINAE
concepts
overload tricks
```

Axiom không nên bê nguyên hệ thống đó.

Compiler có thể internally specialize:

```text
generic → specialized MIR
```

nhưng programmer chưa cần viết:

```axiom
impl<T> Foo<T> ...
impl Foo<i32> ...
```

trong Core v0.1.

Nếu sau này cần, ta thiết kế một hệ thống specialization có kiểm soát.

---

# 24. Operator overloading

Có thể dùng trait:

```axiom
trait Add<Rhs> {
    type Output

    fn add(self: Self, rhs: Rhs) -> Self.Output
}
```

Sau đó:

```axiom
a + b
```

resolve:

```text
Add::add(a, b)
```

Nhưng tôi muốn giới hạn operator.

Không cho programmer tạo operator mới:

```text
<~>
%%>
!!! 
```

vì sẽ phá readability.

Chỉ các operator ngôn ngữ định nghĩa mới được overload.

---

# 25. Equality

Tôi vẫn giữ nguyên quyết định trước:

```axiom
a == b
```

không tự động có nghĩa là byte comparison của struct.

Một type phải implement:

```axiom
trait Equatable<Rhs = Self> {
    fn equals(...)
}
```

Compiler có thể tự derive nếu muốn:

```axiom
@derive(Equatable)
struct Point { ... }
```

Nhưng `derive` là tooling/compiler facility, không cần macro system lớn.

---

# 26. Ordering

Không nên ép mọi type có `<`.

Có:

```axiom
trait Comparable {
    fn compare(...) -> Ordering
}
```

với:

```axiom
enum Ordering {
    Less
    Equal
    Greater
}
```

`<`, `>`, `<=`, `>=` có thể dựa trên trait.

Float cần xử lý riêng vì NaN.

Không được giả định mọi `f32` có total ordering.

---

# 27. `Copy`, `Drop`, `Send`, `Share` không phải trait thường

Điểm này phải được bảo vệ rất chặt.

Không:

```axiom
trait Copy {}
```

theo nghĩa library trait thông thường.

Compiler phải biết:

```text
Copy
Drop
Send
Share
Sized
```

là **type properties**.

Lý do:

```text
trait
    → behavior

property
    → compiler semantic fact
```

Nếu biến `Copy` thành trait thông thường, compiler sẽ khó đảm bảo invariant ownership.

---

# 28. Property propagation

Ví dụ:

```axiom
struct Point {
    x: f32
    y: f32
}
```

Compiler:

```text
Point
    Copy
    !Drop
    Sized
```

Nếu:

```axiom
struct User {
    id: u64
    name: String
}
```

thì:

```text
User
    !Copy
    Drop
    Sized
```

Compiler derive dựa trên fields.

Tương tự:

```text
Send(User)
```

nếu tất cả thành phần thỏa điều kiện.

Nhưng `Share` phải thận trọng hơn.

---

# 29. Không suy ra `Share` chỉ từ immutable

Ví dụ:

```axiom
struct Counter {
    value: Atomic<i32>
}
```

có thể Share.

Nhưng:

```axiom
struct UnsafeCellLike {
    ...
}
```

không nhất thiết.

Do đó:

```text
immutable ≠ Share
```

Đây là điểm rất quan trọng cho concurrency.

---

# 30. Generic + ownership

Generic function phải giữ nguyên ownership semantics.

```axiom
fn consume<T>(x: T) {
    ...
}
```

Nếu T non-Copy:

```axiom
let a = Resource()
consume(a)
```

→ `a` moved.

Nếu T Copy:

```axiom
let a = Point(...)
consume(a)
```

→ copy semantics.

Không cần generic function viết:

```text
<T: Copy>
```

trừ khi nó **thực sự cần copy**.

Ví dụ:

```axiom
fn duplicate<T: Copy>(x: T) -> (T, T)
```

Nếu không có `Copy` constraint:

```axiom
fn duplicate<T>(x: T) -> (T, T)
```

→ compile error vì không thể dùng `x` hai lần.

Đây là cách generic ownership rất tự nhiên.

---

# 31. Generic inference

Ví dụ:

```axiom
let x = max(10, 20)
```

Compiler suy ra:

```text
T = integer type
```

Nhưng nếu:

```axiom
let x = max(...)
```

không đủ information:

```text
AMBIGUOUS TYPE
```

Không nên có hàng loạt defaulting rules khó đoán.

---

# 32. Generic function vs overload

Tôi muốn Axiom ưu tiên:

```axiom
fn min<T: Comparable>(a: T, b: T)
```

thay vì:

```text
min(i32)
min(i64)
min(f32)
min(f64)
...
```

Nhưng overload vẫn cần cho những API có semantic khác nhau.

Ví dụ:

```axiom
read(view<u8>)
read(File)
read(Socket)
```

Tuy nhiên overload resolution nên cực kỳ đơn giản:

```text
exact match
→ generic match
→ explicit conversion
→ otherwise ambiguity/error
```

Không có implicit conversion chain dài.

---

# 33. Không có implicit user-defined conversion

Tôi đề xuất **cấm hoàn toàn** trong v0.1.

Ví dụ không:

```axiom
Meters → Feet → f32
```

tự động.

Phải:

```axiom
meters.to_feet()
```

hoặc:

```axiom
Feet.from(meters)
```

Điều này giúp:

- type inference deterministic
- overload resolution đơn giản
- compiler nhanh
- code dễ đọc
- AI dễ hiểu.

---

# 34. Generic compile-time computation

Axiom có thể hỗ trợ:

```axiom
fn zeros<T, N>() -> Array<T, N>
```

với `N` compile-time.

Nhưng tôi **không muốn biến generic system thành dependent type system**.

Không:

```text
arbitrary type-level programming
proof language
type-level recursion
```

trong Core v0.1.

Compile-time constants đủ cho phần lớn systems programming.

---

# 35. Generic parameter categories

Tôi đề xuất chỉ cần:

```text
Type parameter
Value parameter
```

Ví dụ:

```axiom
Array<T, N>
```

Trong đó:

```text
T = type
N = compile-time value
```

Sau này có thể thêm:

```text
const
```

syntax rõ ràng.

---

# 36. Generic bounds phải được kiểm tra trước MIR

Pipeline:

```text
Generic source
       ↓
AST
       ↓
HIR
       ↓
name resolution
       ↓
type resolution
       ↓
trait solving
       ↓
generic instantiation
       ↓
Typed MIR
```

MIR không nên chứa:

```text
"maybe this trait exists"
```

MIR phải là:

```text
fully resolved
```

hoặc explicit dynamic dispatch.

Điều này rất quan trọng đối với **Verified MIR**.

---

# 37. Trait solver không nên trở thành logic engine

Đây là một cảnh báo kiến trúc.

Nếu cho:

```text
recursive associated types
higher-ranked constraints
arbitrary implication
recursive trait bounds
```

thì trait solving có thể trở thành một theorem prover.

Tôi muốn v0.1 giới hạn:

```text
finite trait graph
nominal types
explicit impl
simple generic constraints
associated types
deterministic resolution
```

Compiler có thể mạnh bên trong, nhưng language semantics phải giữ giới hạn.

---

# 38. Tổng kết mô hình

Axiom sẽ có:

```text
                 TYPE
                  │
        ┌─────────┴─────────┐
        │                   │
     STRUCT              ENUM
        │
        │ data
        ↓
     TRAIT
        │
        │ behavior
        ↓
      IMPL
        │
        ↓
    GENERIC
        │
        ↓
   STATIC DISPATCH
```

và khi thật sự cần:

```text
TYPE
 ↓
dyn Trait
 ↓
DYNAMIC DISPATCH
```

Không có class hierarchy ở bất kỳ đâu.

---

# 39. Các invariant mới nên freeze

Tôi đề xuất thêm:

```text
ATG-01
Structs own data representation.

ATG-02
Traits define behavior/contracts, not object storage.

ATG-03
Impl connects a trait to a type.

ATG-04
Method syntax is syntactic sugar for function dispatch.

ATG-05
Static dispatch is the default.

ATG-06
Dynamic dispatch is explicit.

ATG-07
Dynamic dispatch does not impose metadata on ordinary values.

ATG-08
Generic abstraction is compile-time oriented.

ATG-09
Generic instantiation must resolve to typed semantics before Verified MIR.

ATG-10
Copy/Drop/Send/Share/Sized are compiler-known type properties, not ordinary behavioral traits.

ATG-11
No implicit user-defined conversions.

ATG-12
Ambiguous trait/method resolution is a compile-time error.

ATG-13
Foreign-trait + foreign-type implementations are forbidden.

ATG-14
Generic specialization may change machine representation but not semantics.

ATG-15
Trait resolution must be deterministic.

ATG-16
Trait solving must not require runtime reflection.

ATG-17
Generic code does not imply runtime generic metadata.

ATG-18
Operator overloading uses predefined operators only.

ATG-19
Generic ownership follows instantiated type properties.

ATG-20
A trait implementation cannot redefine core ownership semantics.
```

## Một điểm tôi muốn thay đổi so với nhiều ngôn ngữ hiện đại

Axiom **không cần class để có polymorphism**, nhưng cũng **không nên cực đoan loại bỏ mọi dynamic dispatch**.

Ta có hai tầng rất rõ:

```text
                    POLYMORPHISM
                         │
             ┌───────────┴───────────┐
             │                       │
        STATIC                    DYNAMIC
        default                   explicit
             │                       │
       generic + trait           dyn Trait
             │                       │
      compile-time                runtime
      specialization             dispatch table
```

Điều này cho phép cùng một ngôn ngữ viết:

```text
OS/kernel-level code
        ↓
static dispatch
        ↓
zero runtime overhead
```

nhưng cũng:

```text
GUI/game/editor/plugin architecture
        ↓
dyn Trait
        ↓
runtime polymorphism
```

mà **không bắt mọi struct phải trở thành object**.

---

### Bước tiếp theo

Sau khi trait/generic đã tương đối rõ, phần tôi cho rằng cần thiết kế tiếp là **module/package/build/link system**. Đây mới là phần quyết định Axiom có thực sự đạt mục tiêu:

```text
source
 → package
 → dependency
 → compilation unit
 → incremental compilation
 → object
 → linker
 → EXE / ELF / Mach-O / WASM
```

đồng thời phải giải quyết **ABI, symbol visibility, generic instantiation giữa package, FFI, cross-compilation và reproducible build** mà không biến Axiom thành một hệ thống build quá nặng.