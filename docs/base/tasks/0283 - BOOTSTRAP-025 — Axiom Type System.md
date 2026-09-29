Tiếp tục.

# BOOTSTRAP-025 — Axiom Type System

Đây là một trong những phần quan trọng nhất của Core. Tôi đề xuất mục tiêu không phải là làm type system "ít tính năng", mà là:

> **Type system đủ mạnh để biểu đạt hệ thống lớn, nhưng không biến programmer thành người giải lifetime/type machinery.**

Axiom nên lấy **struct + enum + trait + generic + function** làm các building block chính.

---

# 1. Mô hình type tổng thể

Axiom có thể chia type thành 6 nhóm:

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
├── Behavioral
│   └── trait
│
├── Callable
│   ├── fn(...)
│   └── closure
│
└── Access / system
    ├── view<T>
    ├── mut_view<T>
    ├── raw pointer
    └── handles
```

Không cần:

```text
class
interface
abstract class
virtual class
Object
Any
null
```

trong Core.

---

# 2. `struct` là aggregate cơ bản

Ví dụ:

```axiom
struct Vec3 {
    x: f32
    y: f32
    z: f32
}
```

Struct có:

- data
- methods
- associated functions
- trait implementations

Nhưng **không có class identity**.

Method:

```axiom
fn length(self: view<Vec3>) -> f32 {
    sqrt(self.x*self.x + self.y*self.y + self.z*self.z)
}
```

gọi:

```axiom
let l = v.length()
```

chỉ là syntax sugar cho:

```axiom
length(v)
```

---

# 3. Không có class inheritance

Axiom không nên có:

```text
class Dog : Animal
```

hay:

```text
class Dog extends Animal
```

Thay vào đó:

```axiom
trait Animal {
    fn speak(self: view<Self>)
}
```

và:

```axiom
struct Dog {
    name: String
}

impl Animal for Dog {
    fn speak(self: view<Dog>) {
        ...
    }
}
```

Composition:

```axiom
struct Dog {
    animal: AnimalData
    ...
}
```

hoặc generic/trait abstraction.

Điều này tránh:

- fragile base class
- implicit object layout
- inheritance diamond
- hidden vtable
- constructor/destructor hierarchy
- virtual dispatch mặc định.

---

# 4. Enum là algebraic data type

Axiom nên có enum mạnh ngay từ Core:

```axiom
enum Option<T> {
    Some(T)
    None
}
```

```axiom
enum Result<T, E> {
    Ok(T)
    Err(E)
}
```

Enum có thể chứa:

- unit
- primitive
- struct
- tuple
- generic type
- nested enum

Ví dụ:

```axiom
enum Shape {
    Point(Vec2)
    Circle { center: Vec2, radius: f32 }
    Rectangle { min: Vec2, max: Vec2 }
}
```

---

# 5. `match` là type-system feature, không phải switch nâng cấp

```axiom
match shape {
    Point(p) => draw_point(p)
    Circle { center, radius } => draw_circle(center, radius)
    Rectangle { min, max } => draw_rect(min, max)
}
```

Compiler bắt buộc exhaustive.

Nếu thêm:

```axiom
Triangle(...)
```

mọi `match` liên quan sẽ được compiler phát hiện.

Đây là một lợi thế lớn so với enum/switch kiểu C.

---

# 6. Không có implicit nullable type

Không có:

```axiom
Player?
```

nếu Core chưa định nghĩa rõ syntax đó.

Mô hình canonical:

```axiom
Option<Player>
```

và:

```axiom
match player {
    Some(p) => ...
    None => ...
}
```

Có thể sau này thêm syntax sugar:

```axiom
Player?
```

nhưng semantic vẫn là:

```axiom
Option<Player>
```

Tôi nghiêng về **không cần syntax sugar trong v1** để Core nhất quán.

---

# 7. Trait không phải class/interface

Trait chỉ mô tả capability/behavior.

```axiom
trait Drawable {
    fn draw(self: view<Self>)
}
```

Type thực hiện:

```axiom
impl Drawable for Sprite {
    fn draw(self: view<Sprite>) {
        ...
    }
}
```

Trait có thể chứa:

- required methods
- default methods
- associated types
- associated constants
- trait constraints

Không chứa object state.

---

# 8. Default method và override

Ví dụ:

```axiom
trait Shape {
    fn area(self: view<Self>) -> f32

    fn describe(self: view<Self>) {
        println("shape")
    }
}
```

Concrete implementation:

```axiom
impl Shape for Circle {
    fn area(self: view<Circle>) -> f32 {
        ...
    }

    fn describe(self: view<Circle>) {
        println("circle")
    }
}
```

`describe()` được xem là **override của default implementation**.

Không cần:

```text
override
virtual
final
```

trong Core.

Compiler biết dựa vào trait implementation.

Nếu muốn IDE hỗ trợ phát hiện typo, compiler/tooling có thể báo:

```text
warning: this method overrides trait default implementation
```

nhưng đó là tooling, không cần thêm keyword.

---

# 9. Generic là abstraction chính

Ví dụ:

```axiom
struct Vec<T> {
    data: ...
}
```

và:

```axiom
fn max<T: Ord>(a: T, b: T) -> T {
    if a > b { a } else { b }
}
```

Generic phải là **compile-time abstraction**.

Mục tiêu:

```text
Vec<i32>
Vec<f32>
Vec<MyStruct>
```

có thể được specialize thành code cụ thể.

---

# 10. Monomorphization là default

Ví dụ:

```axiom
fn add<T: Add>(a: T, b: T) -> T
```

với:

```axiom
add(1, 2)
add(1.0, 2.0)
```

compiler có thể tạo:

```text
add<i32>
add<f32>
```

rồi inline/specialize.

Không cần generic runtime machinery.

Điều này phù hợp mục tiêu:

> **Abstraction disappears after compilation.**

---

# 11. Nhưng không nên bắt mọi generic phải duplicate code

Compiler có thể thực hiện:

```text
monomorphization
       ↓
representation analysis
       ↓
identical-code folding
       ↓
deduplication
```

Nếu:

```text
Foo<A>
Foo<B>
Foo<C>
```

có cùng machine representation và cùng semantics cần thiết, compiler có thể chia sẻ implementation.

Do đó:

> Monomorphization là semantic compilation strategy, không phải yêu cầu binary phải nhân bản code.

---

# 12. Trait constraint

Ví dụ:

```axiom
fn sort<T: Ord>(items: mut_view<[T]>) {
    ...
}
```

hoặc nhiều trait:

```axiom
fn save<T: Serialize + Debug>(value: view<T>) {
    ...
}
```

Compiler giải quyết trait obligation tại compile time.

Không có runtime interface lookup nếu không yêu cầu dynamic dispatch.

---

# 13. Associated type

Đây là feature rất đáng có.

```axiom
trait Iterator {
    type Item

    fn next(self: mut_view<Self>) -> Option<Self::Item>
}
```

Implementation:

```axiom
impl Iterator for IntRange {
    type Item = i32

    fn next(...) -> Option<i32> {
        ...
    }
}
```

Lợi ích:

- giảm generic parameter explosion
- API dễ đọc
- phù hợp collection/iterator/device/async abstractions.

---

# 14. Associated const

Cũng nên có:

```axiom
trait Numeric {
    const ZERO: Self
    const ONE: Self
}
```

hoặc:

```axiom
trait Packet {
    const HEADER_SIZE: usize
}
```

Compiler có thể materialize giá trị trực tiếp.

Không cần runtime lookup.

---

# 15. Associated function

Ví dụ:

```axiom
trait FromBytes {
    fn from_bytes(data: view<[u8]>) -> Result<Self, Error>
}
```

Không có `self`.

Gọi:

```axiom
let x = MyType.from_bytes(data)
```

Semantic:

```text
FromBytes::from_bytes::<MyType>(data)
```

---

# 16. Newtype

Axiom nên có cách tạo type khác biệt mà **không tạo runtime wrapper bắt buộc**.

Ví dụ:

```axiom
type UserId = newtype u64
type Meter = newtype f32
type Second = newtype f64
```

Sau đó:

```axiom
let user: UserId = 10
let time: Second = 10
```

không được tự động interchange.

Nhưng representation có thể giống:

```text
UserId → u64
Meter  → f32
Second → f64
```

Compiler có thể erase wrapper.

Đây là cực kỳ hữu ích để tránh bug semantic mà không phải trả runtime cost.

---

# 17. `type alias` khác `newtype`

Cần phân biệt:

```axiom
type UserId = u64
```

và:

```axiom
type UserId = newtype u64
```

### Alias

Hai tên cùng một type:

```text
UserId == u64
```

### Newtype

Type hoàn toàn khác:

```text
UserId != u64
```

nhưng có thể cùng representation.

Đây là distinction bắt buộc.

---

# 18. Tuple

Nên hỗ trợ:

```axiom
let p = (10, 20)
```

và:

```axiom
fn minmax(values: view<[i32]>) -> (i32, i32)
```

Tuple là anonymous aggregate.

Không cần tạo struct cho những trường hợp nhỏ.

Nhưng tuple không nên trở thành substitute cho mọi struct vì struct có semantic field names.

---

# 19. Function type

Ví dụ:

```axiom
type Comparator<T> = fn(view<T>, view<T>) -> Ordering
```

Function pointer là first-class value.

Có thể truyền:

```axiom
sort(values, compare_int)
```

Function pointer không có ownership complexity đặc biệt.

---

# 20. Closure

Closure là type compiler-generated.

```axiom
let factor = 10

let f = |x: i32| x * factor
```

Compiler xác định capture:

```text
factor
  ↓
capture by value
```

hoặc nếu semantics cho phép:

```text
capture by view
capture by mutable capability
```

Người dùng không phải viết lifetime.

Closure có thể được:

- inline
- specialize
- stack-store
- caller-store
- heap-store

tùy escape analysis.

---

# 21. Closure không đồng nhất function pointer

```text
fn(...) -> T
```

và:

```text
closure
```

khác nhau.

Một closure có capture cần environment.

Ví dụ:

```axiom
let x = 10
let f = |a| a + x
```

không thể tự nhiên trở thành:

```text
fn(i32) -> i32
```

vì `x` phải ở đâu đó.

Compiler có thể optimize closure thành function + environment.

Nếu closure không capture:

```axiom
let f = |x: i32| x * 2
```

compiler có thể cho phép decay thành function pointer khi ABI/context cho phép.

---

# 22. `dyn Trait`

Static dispatch:

```axiom
fn draw<T: Drawable>(x: view<T>) {
    x.draw()
}
```

Dynamic dispatch:

```axiom
fn draw(x: view<dyn Drawable>) {
    x.draw()
}
```

Sự khác biệt phải cực kỳ rõ.

### Generic

```text
compile-time specialization
```

### `dyn Trait`

```text
runtime polymorphism
```

`dyn Trait` **không phải object/class**.

Nó chỉ là một dynamic capability representation.

Compiler có thể implement bằng:

```text
data pointer + vtable
```

nhưng đây là implementation detail.

Không bắt buộc mọi struct có vtable/object header.

---

# 23. Dynamic dispatch phải explicit

Không được:

```axiom
trait Drawable { ... }

let x = some_sprite
x.draw()
```

rồi compiler tự biến mọi thứ thành virtual dispatch.

Nếu static type biết `Sprite`, compiler gọi trực tiếp.

Nếu muốn dynamic:

```axiom
let x: dyn Drawable = ...
```

Khi đó runtime dispatch là một phần semantics.

Điều này cực kỳ quan trọng cho performance.

---

# 24. Type inference

Axiom nên có inference mạnh nhưng **không phải kiểu "compiler đoán mọi thứ bằng heuristic"**.

Ví dụ:

```axiom
let x = 10
```

compiler có thể suy ra default integer type theo literal rules.

```axiom
let p = Point {
    x: 10.0,
    y: 20.0
}
```

rõ ràng.

Generic:

```axiom
let x = Vec::new()
```

nếu không đủ thông tin:

```text
error: cannot infer type parameter T
```

Không đoán ngẫu nhiên.

---

# 25. Không có implicit conversion tùy tiện

Đây là điểm tôi đề xuất rất mạnh.

Không cho:

```text
i32 → f64
u64 → i32
f64 → i32
```

một cách tự động trong mọi context.

Dùng:

```axiom
let x = value as f64
```

hoặc API chuyển đổi tương ứng.

Điều này tránh hàng loạt bug C/C++.

---

# 26. Nhưng literal phải thông minh

Không nên bắt:

```axiom
let x: i32 = 10
```

phải viết:

```axiom
let x: i32 = 10i32
```

Literal được type-check theo expected type.

```axiom
let a: u8 = 100
let b: f32 = 1.5
```

được.

Nhưng:

```axiom
let a: u8 = 1000
```

compile error.

Không silently truncate.

---

# 27. Numeric conversion

Nên phân biệt:

```text
safe widening
checked narrowing
wrapping conversion
saturating conversion
reinterpretation
```

Ví dụ:

```axiom
let x: i64 = u32_value as i64
```

nếu hợp lệ.

Narrow:

```axiom
let x: u8 = value.try_as<u8>()?
```

Wrapping:

```axiom
let x = value.wrapping_as<u8>()
```

Saturating:

```axiom
let x = value.saturating_as<u8>()
```

Không gom tất cả thành một cast mơ hồ.

---

# 28. Operator overloading

Nên có nhưng thông qua trait.

Ví dụ:

```axiom
trait Add<Rhs = Self> {
    type Output

    fn add(self, rhs: Rhs) -> Self.Output
}
```

Sau đó:

```axiom
a + b
```

là syntax sugar.

Các operator:

```text
+
-
*
/
%
==
!=
<
<=
>
>=
&
|
^
<<
>>
[]
()
```

có thể map tới compiler-known traits/protocols.

Nhưng một số operator như:

```text
&&
||
```

không nên là ordinary overload vì có short-circuit semantics.

---

# 29. `[]` và indexing

Có thể dùng trait:

```axiom
Index
IndexMut
```

nhưng compiler cần phân biệt:

```axiom
array[i]
view[i]
map[key]
```

và preserve bounds/safety semantics.

Ví dụ:

```axiom
values[i]
```

safe indexing phải kiểm tra bounds hoặc được compiler chứng minh redundant.

Unchecked:

```axiom
unsafe {
    values.get_unchecked(i)
}
```

là system escape.

---

# 30. `Copy`, `Clone`, `Drop`

Đây là ba semantic hoàn toàn khác nhau.

### Copy

```text
cheap semantic duplication
```

Ví dụ:

```axiom
let b = a
```

với `Copy` → cả hai hợp lệ.

### Move

```text
ownership transfer
```

### Clone

```text
explicit potentially expensive duplication
```

```axiom
let b = a.clone()
```

### Drop

```text
deterministic cleanup
```

Không được:

```text
Copy + Drop
```

theo semantics đã chốt.

---

# 31. `Send` và `Share`

Cũng là traits/capabilities đặc biệt compiler-known.

```text
Send
    ownership can cross execution domain

Share
    concurrent shared access is semantically valid
```

Compiler tự derive khi có thể.

Không bắt programmer viết:

```text
unsafe impl Send ...
```

cho các type thông thường.

Unsafe/manual implementation chỉ dành cho low-level abstractions thực sự cần thiết.

---

# 32. Trait implementation coherence

Đây là vấn đề compiler phải chốt.

Tôi đề xuất rule kiểu:

> Một cặp `(Trait, Type)` chỉ có một canonical implementation trong một compilation universe.

Không cho nhiều package cùng tạo:

```axiom
impl Foo for Bar
```

một cách không kiểm soát.

Nếu không, method/operator resolution sẽ trở nên không deterministic.

---

# 33. Specialization

Tôi **không đưa full arbitrary specialization vào Core v1**.

Có thể có:

```text
monomorphization
inlining
constant propagation
dead-code elimination
```

nhưng chưa cho programmer:

```axiom
impl<T> Foo for T
impl Foo for SpecialType
```

với hệ thống ưu tiên phức tạp tùy ý.

Lý do: specialization dễ tạo coherence và dispatch ambiguity rất lớn.

Có thể thêm **compiler-controlled specialization** sau.

---

# 34. Type equality

Compiler cần phân biệt:

```text
nominal identity
structural identity
representation identity
```

Axiom nên ưu tiên **nominal typing** cho user-defined types.

Ví dụ:

```axiom
struct Meters {
    value: f32
}

struct Seconds {
    value: f32
}
```

dù layout giống nhau:

```text
Meters != Seconds
```

Không tự động interchange.

Điều này an toàn hơn structural typing toàn phần.

---

# 35. Structural typing chỉ dùng ở nơi phù hợp

Tuple:

```axiom
(i32, f32)
```

có structural identity tự nhiên.

Anonymous closure type cũng compiler-generated.

Nhưng user-defined:

```text
struct A
struct B
```

không tự động cùng type chỉ vì cùng fields.

---

# 36. Type erasure phải explicit

Không có:

```axiom
Any
Object
```

để nhét mọi thứ vào runtime container.

Nếu cần:

### Compile-time generic

```axiom
<T>
```

### Dynamic trait

```axiom
dyn Trait
```

### Raw bytes

```axiom
view<[u8]>
```

### Type-erased handle

library abstraction.

Như vậy programmer phải chọn abstraction phù hợp.

---

# 37. Type system pipeline

Compiler nên xử lý:

```text
Source
  ↓
Parse
  ↓
Name resolution
  ↓
Generic parameter collection
  ↓
Type inference
  ↓
Trait obligation solving
  ↓
Coercion checking
  ↓
Ownership/capability checking
  ↓
Monomorphization / dynamic dispatch resolution
  ↓
Typed HIR
```

Sau đó mới:

```text
Typed HIR
   ↓
MIR
```

Không để backend phải hiểu generic/trait semantics.

---

# 38. Type-system invariants

Đề xuất đóng băng:

```text
ATYPE-20  Axiom uses static typing.

ATYPE-21  User-defined types are nominal.

ATYPE-22  Struct is the primary aggregate type.

ATYPE-23  Enum is the primary algebraic sum type.

ATYPE-24  Trait defines behavior, not object identity.

ATYPE-25  Traits do not require object headers.

ATYPE-26  Class inheritance is not part of Core.

ATYPE-27  Generic abstraction is compile-time by default.

ATYPE-28  Generic specialization does not imply runtime generic metadata.

ATYPE-29  Monomorphization may be optimized and deduplicated.

ATYPE-30  Trait constraints are statically resolved when possible.

ATYPE-31  Associated types are compile-time type members.

ATYPE-32  Associated constants are compile-time values unless explicitly materialized.

ATYPE-33  Associated functions do not require an object instance.

ATYPE-34  Default trait methods may be overridden by concrete implementations.

ATYPE-35  Override does not require an override keyword.

ATYPE-36  Dynamic dispatch requires explicit dynamic representation.

ATYPE-37  dyn Trait does not imply class semantics.

ATYPE-38  Dynamic dispatch representation is compiler-controlled.

ATYPE-39  Function pointers are distinct from capturing closures.

ATYPE-40  Non-capturing closures may decay to compatible function pointers.

ATYPE-41  Closure representation is compiler-controlled.

ATYPE-42  Closure captures are ownership/capability checked.

ATYPE-43  Type aliases preserve type identity.

ATYPE-44  Newtypes create distinct nominal types.

ATYPE-45  Newtype representation may be erased when unobservable.

ATYPE-46  Tuple types are structural aggregates.

ATYPE-47  User-defined structs are not structurally interchangeable.

ATYPE-48  Implicit numeric narrowing is forbidden.

ATYPE-49  Numeric conversion semantics are explicit.

ATYPE-50  Literal typing uses expected-type context where unambiguous.

ATYPE-51  Overflow behavior is defined, not accidental.

ATYPE-52  Operator overloading is trait-based.

ATYPE-53  Short-circuit logical operators are not ordinary overloads.

ATYPE-54  Copy is distinct from Clone.

ATYPE-55  Copy is distinct from Move.

ATYPE-56  Drop is distinct from memory deallocation.

ATYPE-57  Copy types cannot have semantic Drop obligations.

ATYPE-58  Send and Share are compiler-recognized semantic capabilities.

ATYPE-59  Send does not imply Share.

ATYPE-60  Share does not imply mutable sharing.

ATYPE-61  Trait implementation resolution is deterministic.

ATYPE-62  Trait coherence prevents ambiguous implementations.

ATYPE-63  Full arbitrary specialization is not Core v1.

ATYPE-64  Type inference is deterministic.

ATYPE-65  Failed inference produces a compile-time diagnostic.

ATYPE-66  Type erasure requires an explicit abstraction.

ATYPE-67  Any/Object is not a required Core type.

ATYPE-68  Option represents safe absence.

ATYPE-69  Result represents recoverable operation failure.

ATYPE-70  Match is exhaustively checked.

ATYPE-71  Generic and trait metadata need not exist at runtime.

ATYPE-72  Type semantics are resolved before backend lowering.
```

---

# 39. Một quyết định quan trọng: không biến Trait thành "interface C++"

Đây là điểm tôi muốn nhấn mạnh.

Axiom không nên đi theo:

```text
class
  ↓
interface
  ↓
virtual method
  ↓
object
  ↓
heap
```

Mà nên đi theo:

```text
struct
   +
trait
   +
generic
   +
explicit dyn
```

Ví dụ:

```axiom
fn render<T: Renderable>(x: view<T>) {
    x.render()
}
```

Compiler có thể biến toàn bộ thành static call.

Chỉ khi programmer viết:

```axiom
fn render(x: view<dyn Renderable>) {
    x.render()
}
```

mới cần runtime dispatch.

Đây là một trong những yếu tố giúp Axiom đạt mục tiêu **"abstraction cao nhưng binary vẫn giống code viết bằng C/ASM"**.

---

# 40. Type system hiện tại đã đủ để xây phần lớn Core

Sau BOOTSTRAP-025, mô hình cơ bản đã trở thành:

```text
                    TYPE
                     │
       ┌─────────────┼─────────────┐
       │             │             │
    STRUCT         ENUM          TRAIT
       │             │             │
       └───────┬─────┴──────┬──────┘
               │            │
             GENERIC       dyn
               │            │
         compile-time    runtime
         specialization   dispatch
               │
               ▼
          machine code
```

Kết hợp với phần trước:

```text
TYPE
 │
 ├── VALUE
 │
 ├── OWNERSHIP
 │
 ├── view / mut_view
 │
 ├── STORAGE
 │
 ├── SEND / SHARE
 │
 └── ABI REPRESENTATION
```

Đây là một nền khá mạnh mà không cần class, GC, borrow syntax hay runtime object model.

---

## Bước tiếp theo: BOOTSTRAP-026

Sau Type System, tôi đề xuất **không nhảy ngay sang standard library**.

Phần còn thiếu rất quan trọng là:

# **BOOTSTRAP-026 — Function, Method, Call & Evaluation Semantics**

Ta sẽ chốt:

- function declaration
- parameter passing
- `self`
- method resolution
- extension method
- generic function
- overload
- default argument có nên có hay không
- named argument
- variadic function
- closure call
- function pointer call
- evaluation order
- argument evaluation order
- return semantics
- `defer` có nên tồn tại không
- `?` operator
- panic/Result control flow
- tail call
- ABI calling convention
- `extern`
- `@inline`
- `@noinline`
- `@cold`
- `@noreturn`
- `@export`
- `@syscall`
- và đặc biệt **làm sao để function call trong Axiom vừa đơn giản như scripting language nhưng compiler vẫn tối ưu xuống machine code cực thấp**.