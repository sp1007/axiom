# BOOTSTRAP-426 — GENERICS, TRAITS, INTERFACES & STATIC/DYNAMIC POLYMORPHISM

Task này khóa phần **abstraction** của Axiom. Mục tiêu là có sức biểu đạt tương đương generics + interfaces/traits hiện đại, nhưng **không cần class hierarchy và không biến virtual dispatch thành chi phí mặc định**.

Kiến trúc nền:

```text
                         Axiom Polymorphism
                                │
                ┌───────────────┴───────────────┐
                ▼                               ▼
          Static polymorphism             Dynamic polymorphism
                │                               │
            Generics                         Interface
            Traits                           VTable
                │                               │
          Monomorphization                  Explicit
                │                          dynamic dispatch
                ▼                               ▼
          Native code                    Native vtable call
```

Nguyên tắc:

> **Static dispatch mặc định. Dynamic dispatch chỉ xuất hiện khi programmer yêu cầu hoặc API boundary cần nó.**

---

## 426.1 — Không có class trong core

Axiom không cần:

```text
class
extends
inherits
virtual method
abstract class
```

Thay vào đó:

```text
struct
fn
trait
impl
interface value
```

Một abstraction:

```text
struct Vec2 {
    x: f32
    y: f32
}

fn length(self: Vec2) -> f32 {
    ...
}
```

đã đủ để tạo method-like behavior.

---

# 426.2 — Generic function

Ví dụ conceptual:

```text
fn max<T>(a: T, b: T) -> T
```

với constraint:

```text
fn max<T: Ordered>(a: T, b: T) -> T
```

Compiler biết chính xác capability cần thiết.

---

# 426.3 — Generic struct

```text
struct Array<T> {
    data: ...
    len: usize
}
```

Không có runtime generic object.

---

# 426.4 — Generic enum

```text
enum Result<T, E> {
    Ok(T)
    Err(E)
}
```

được xây dựng hoàn toàn trên generic type system.

---

# 426.5 — Generic type alias

Cho phép:

```text
type UserResult<T> = Result<T, UserError>
```

Alias không tạo type runtime mới.

---

# 426.6 — Type parameters

Core generic parameter:

```text
<T>
```

có thể đại diện:

```text
type
```

Sau này có thể mở rộng thành:

```text
<const N>
```

hoặc compile-time parameter.

Không cần đưa mọi loại metaprogramming vào generic core.

---

# 426.7 — Const generic parameters

Axiom nên hỗ trợ:

```text
struct Vector<T, const N: usize>
```

để biểu diễn:

```text
Vector<f32, 4>
Matrix<f32, 4, 4>
Array<T, 1024>
```

mà không cần heap.

---

# 426.8 — Compile-time parameters

Một generic parameter có thể được compile-time constant:

```text
fn zeros<const N: usize>() -> Array<f32, N>
```

Compiler specialize theo `N`.

---

# 426.9 — Trait

Trait biểu diễn **capability/behavior contract**, không phải class.

Ví dụ:

```text
trait Add<Rhs> {
    type Output

    fn add(self, rhs: Rhs) -> Output
}
```

---

# 426.10 — Trait implementation

```text
impl Add<Vec2> for Vec2 {
    type Output = Vec2

    fn add(self, rhs: Vec2) -> Vec2 {
        ...
    }
}
```

Không có inheritance.

---

# 426.11 — Trait là contract

Trait có thể yêu cầu:

```text
method
associated type
associated constant
```

nhưng không yêu cầu object header.

---

# 426.12 — Trait constraints

Generic:

```text
fn sort<T: Ordered>(data: []T)
```

nghĩa là compiler chỉ cho instantiate với type đáp ứng `Ordered`.

---

# 426.13 — Multiple constraints

```text
fn process<T: Readable + Writable>(x: T)
```

Compiler resolve toàn bộ constraints compile-time.

---

# 426.14 — Where clauses

Khi constraint phức tạp:

```text
fn foo<T>(x: T)
where
    T: Clone + Send
{
    ...
}
```

`where` chỉ là syntax hỗ trợ readability.

Semantic không khác constraint trực tiếp.

---

# 426.15 — Static dispatch

Generic call:

```text
fn process<T: Processor>(x: T)
```

được compile thành implementation cụ thể:

```text
process_CPU(...)
process_GPU(...)
```

nếu compiler instantiate tương ứng.

Không có vtable call mặc định.

---

# 426.16 — Monomorphization

Axiom ưu tiên monomorphization:

```text
process<i32>
process<f32>
process<MyType>
```

→ specialized native code.

Lợi ích:

```text
inline
constant propagation
dead code elimination
vectorization
register optimization
```

---

# 426.17 — Generic code có thể inline

Ví dụ:

```text
fn square<T: Numeric>(x: T) -> T {
    x * x
}
```

Sau specialization compiler có thể inline hoàn toàn.

---

# 426.18 — Code bloat

Monomorphization có thể tạo code duplication.

Axiom compiler phải có:

```text
generic instance cache
identical code folding
link-time deduplication
cold/hot specialization
```

để hạn chế binary bloat.

---

# 426.19 — Generic instance cache

Nếu source:

```text
foo<i32>
```

được dùng 100 lần, compiler không compile 100 bản.

Một specialization artifact được reuse.

---

# 426.20 — Cross-module generic cache

Compiler build cache có thể lưu:

```text
module
generic definition
type arguments
compiler configuration
target ABI
```

để reuse compiled specialization.

Điều này liên kết trực tiếp với mục tiêu cache của Axiom.

---

# 426.21 — Specialization

Axiom nên cho phép specialized implementation khi cần optimization.

Conceptual:

```text
impl<T> Foo<T> ...
impl Foo<f32> ...
```

Tuy nhiên specialization phải có coherence rules rõ ràng.

---

# 426.22 — Không implicit specialization conflict

Compiler không được tự chọn implementation mơ hồ.

Nếu:

```text
impl<T: A> Foo for T
impl<T: B> Foo for T
```

và một type thỏa cả A+B:

```text
ambiguous
```

→ diagnostic.

---

# 426.23 — Coherence

Axiom phải tránh tình trạng nhiều module có thể tùy ý định nghĩa conflicting implementations cho cùng một pair:

```text
Type
Trait
```

Cần ownership/orphan rule ở mức vừa đủ.

---

# 426.24 — Orphan rule

Khuyến nghị:

Một `impl Trait for Type` phải thuộc ít nhất một trong hai:

```text
trait do current module/package own
type do current module/package own
```

Điều này tránh dependency conflict.

---

# 426.25 — Associated type

Trait:

```text
trait Iterator {
    type Item

    fn next(self: ...)
}
```

Type implement:

```text
impl Iterator for MyCollection {
    type Item = User
}
```

---

# 426.26 — Associated constant

```text
trait Numeric {
    const ZERO: Self
    const ONE: Self
}
```

Compiler có thể specialize constant.

---

# 426.27 — Default implementation

Trait có thể cung cấp:

```text
trait Printable {
    fn print(self) {
        ...
    }
}
```

Type chỉ override nếu cần.

Default implementation là static code, không cần vtable.

---

# 426.28 — Extension behavior

Vì Axiom không có class, trait/impl có thể cung cấp method cho type bên ngoài.

Ví dụ:

```text
impl String {
    fn is_empty(self) -> bool
}
```

hoặc trait-based extension.

Không cần sửa struct declaration.

---

# 426.29 — Struct-first method model

Đây là model đã thống nhất trước:

```text
fn length(self: Vec2) -> f32
```

Compiler cho phép gọi:

```text
v.length()
```

như syntax sugar cho:

```text
length(v)
```

Không có hidden object pointer.

---

# 426.30 — Mutable method

Conceptual:

```text
fn normalize(mut self: Vec2)
```

hoặc reference/view form tương ứng.

Semantic ownership được kế thừa từ BOOTSTRAP-423.

---

# 426.31 — Method resolution

Khi gặp:

```text
x.foo()
```

compiler tìm theo thứ tự deterministic:

```text
1. inherent function của type
2. applicable trait implementation
3. imported extension
```

Nếu nhiều candidate cùng phù hợp:

```text
ambiguity diagnostic
```

Không runtime lookup.

---

# 426.32 — Override

Không có class virtual override.

Thay vào đó:

```text
trait Drawable {
    fn draw(self)
}
```

và:

```text
impl Drawable for Button {
    fn draw(self) { ... }
}
```

implementation này là behavior của `Button`.

---

# 426.33 — "Override" default trait method

Nếu trait có:

```text
fn draw(self) {
    default_draw()
}
```

type có thể định nghĩa implementation riêng.

Compiler chọn implementation ở compile time khi static dispatch.

---

# 426.34 — Dynamic dispatch

Khi cần runtime polymorphism:

```text
Drawable interface
```

có thể tạo interface value:

```text
drawable: dyn Drawable
```

Representation:

```text
data pointer
vtable pointer
```

theo BOOTSTRAP-422.

---

# 426.35 — Vtable

Vtable tối thiểu:

```text
VTable {
    drop
    method_1
    method_2
    ...
}
```

Có thể chứa metadata:

```text
size
alignment
type identity
```

nếu abstraction cần.

Không có universal object header.

---

# 426.36 — Explicit dynamic dispatch

Code:

```text
fn render(x: dyn Drawable)
```

là signal rõ rằng dynamic dispatch có thể xảy ra.

Code:

```text
fn render<T: Drawable>(x: T)
```

là static dispatch.

AI và programmer đều dễ nhận biết.

---

# 426.37 — No accidental virtual dispatch

Axiom không tự động biến:

```text
fn render<T: Drawable>
```

thành:

```text
vtable call
```

Static generic là default.

---

# 426.38 — Interface object construction

Conceptual:

```text
d := Drawable(button)
```

Compiler tạo:

```text
data = &button
vtable = Button.Drawable.vtable
```

Không clone object nếu không yêu cầu.

---

# 426.39 — Owned interface object

Có thể có:

```text
Box<dyn Drawable>
```

cho owned dynamic polymorphism.

Representation:

```text
heap object
+
vtable
```

Allocation chỉ xảy ra vì `Box` abstraction yêu cầu.

---

# 426.40 — Borrowed interface object

Có thể có dynamic view:

```text
dyn Drawable
```

mà không ownership transfer.

Nó chỉ giữ:

```text
data pointer
vtable pointer
```

Lifetime được xử lý theo view rules từ 423.

---

# 426.41 — Interface object size

Interface value thường là:

```text
2 machine words
```

trên native targets:

```text
data pointer
vtable pointer
```

nhưng ABI không được hard-code rằng mọi interface luôn đúng 2 words.

---

# 426.42 — Object safety

Trait có thể không phù hợp dynamic dispatch nếu chứa:

```text
generic methods
Self-sized returns
compile-time-only parameters
```

Compiler phải diagnostic khi programmer yêu cầu dynamic interface không hợp lệ.

---

# 426.43 — Generic + dynamic interoperability

Có thể:

```text
fn process<T: Drawable>(x: T)
```

và:

```text
fn process_dynamic(x: dyn Drawable)
```

cùng tồn tại.

Một abstraction static, một abstraction dynamic.

---

# 426.44 — Type erasure

Dynamic interface là một hình thức type erasure:

```text
ConcreteType
    ↓
dyn Trait
```

Nhưng vtable giữ đủ operation contract.

Không cần runtime reflection đầy đủ.

---

# 426.45 — Existential values

`dyn Trait` được xem là existential:

```text
"some unknown concrete type implementing Trait"
```

Compiler không cần biết concrete type tại call site.

---

# 426.46 — Generic constraints vs interface values

So sánh:

```text
T: Drawable
```

→ compile-time knowledge.

```text
dyn Drawable
```

→ runtime knowledge.

Đây là distinction quan trọng trong Axiom.

---

# 426.47 — Trait inheritance

Traits có thể compose:

```text
trait Animal
trait Mammal: Animal
```

nhưng đây là **trait requirement**, không phải class inheritance.

Một struct vẫn chỉ là struct.

---

# 426.48 — Multiple trait implementation

```text
struct Image

impl Drawable for Image
impl Serializable for Image
impl Hashable for Image
```

Không có diamond inheritance.

---

# 426.49 — Trait composition

Generic:

```text
fn save<T: Drawable + Serializable>(x: T)
```

có thể yêu cầu nhiều capabilities.

---

# 426.50 — Trait aliases

Có thể định nghĩa:

```text
trait Persistable = Serializable + StorageCompatible
```

để giảm verbosity.

Không cần runtime representation riêng.

---

# 426.51 — Operator traits

Operators nên map về traits/functions.

Ví dụ:

```text
a + b
```

→ conceptually:

```text
add(a, b)
```

với `Add` trait.

Compiler có thể inline hoàn toàn.

---

# 426.52 — Equality

```text
a == b
```

→ `Equal`/`Eq` capability.

Compiler có thể special-case primitive types.

---

# 426.53 — Ordering

```text
a < b
```

→ `Ordered` capability.

Generic algorithms có thể yêu cầu constraint.

---

# 426.54 — Conversion

Traits:

```text
From<T>
Into<T>
TryFrom<T>
TryInto<T>
```

có thể cung cấp conversion semantics.

Implicit conversion phải rất hạn chế để tránh ambiguity/performance surprises.

---

# 426.55 — Numeric traits

Có thể có:

```text
Numeric
Integer
Float
Signed
Unsigned
```

nhưng primitive operations nên compiler-known.

Không bắt programmer đi qua dynamic dispatch.

---

# 426.56 — Iterator trait

Standard library:

```text
trait Iterator {
    type Item
    fn next(self) -> Option<Item>
}
```

Compiler có thể optimize:

```text
map
filter
fold
```

thành loop native nếu generic/static.

---

# 426.57 — Iterator fusion

Code:

```text
data
    .map(...)
    .filter(...)
    .map(...)
    .sum()
```

không được mặc định tạo:

```text
temporary collection
```

Compiler/library design phải cho phép fusion thành một loop.

---

# 426.58 — Async traits

Trait có thể mô tả async behavior:

```text
trait AsyncReader {
    async fn read(...) -> Result<...>
}
```

Compiler phải lower async method thành future-producing operation.

---

# 426.59 — Send/Share traits

Concurrency model 424 dùng traits:

```text
trait Send
trait Share
```

Compiler có thể auto-derive khi field capabilities phù hợp.

---

# 426.60 — Drop trait

Memory model 423 cần một semantic capability:

```text
trait Drop
```

hoặc compiler intrinsic equivalent.

Ví dụ:

```text
impl Drop for File {
    fn drop(self) {
        close(self.handle)
    }
}
```

Tên cuối cùng có thể là `Drop` hoặc `Destructor`, nhưng semantics phải thống nhất.

---

# 426.61 — Trait method receiver

Với struct-first design, receiver có thể là:

```text
self
view self
mut self
```

hoặc equivalent syntax.

Điều này kết nối trực tiếp với ownership.

---

# 426.62 — No hidden `this`

Compiler không tạo:

```text
this pointer
object header
class metadata
```

cho ordinary struct method.

`self` chỉ là parameter đầu tiên.

---

# 426.63 — ABI of generic functions

Generic static functions sau monomorphization có ABI giống ordinary function.

Ví dụ:

```text
foo<i32>
```

sau specialization trở thành native function bình thường.

---

# 426.64 — Generic ABI boundary

Không nên export generic function trực tiếp qua C ABI:

```text
extern "c" fn foo<T>(...)
```

vì C ABI không hiểu generic parameters.

Thay vào đó export instantiated concrete functions:

```text
foo_i32
foo_f64
```

hoặc explicit wrapper.

---

# 426.65 — Dynamic interface ABI

Nếu export interface qua native ABI:

```text
data pointer
vtable pointer
```

phải có ABI versioning.

Vtable layout phải stable trong cùng ABI version.

---

# 426.66 — Vtable ownership

Vtable là static immutable data.

Không cần allocation.

Interface object có thể:

```text
data = existing object
vtable = static table
```

---

# 426.67 — Vtable deallocation

`drop` slot trong vtable cho phép:

```text
Box<dyn Trait>
```

destroy concrete object mà không biết concrete type.

Đây là một trong những lý do dynamic interface cần vtable.

---

# 426.68 — Vtable metadata

Vtable có thể chứa:

```text
drop_fn
size
align
type_id
method pointers
```

Chỉ những metadata thực sự cần mới emitted.

Không bắt buộc RTTI.

---

# 426.69 — RTTI

Axiom không có mandatory RTTI.

Type identity có thể được:

```text
compile-time only
```

hoặc explicitly requested:

```text
TypeId
```

Dynamic reflection là library/runtime feature.

---

# 426.70 — Reflection

Không đưa full reflection vào core.

Nếu cần:

```text
type_name
field metadata
method metadata
```

compiler có thể emit optional metadata section.

Binary production có thể strip.

---

# 426.71 — Generic reflection

Không yêu cầu runtime metadata cho mọi generic instantiation.

Chỉ emit metadata khi:

```text
reflection requested
debugger requested
serialization metadata requested
```

---

# 426.72 — Serialization

Serialization nên dùng trait:

```text
trait Serialize
trait Deserialize
```

thay vì compiler-generated universal object system.

Compiler có thể hỗ trợ derive/code generation.

---

# 426.73 — Derive

Axiom nên có mechanism:

```text
derive(Serializable, Hashable, Debug)
```

Compiler sinh implementation.

Đây là compile-time generation, không phải runtime reflection.

---

# 426.74 — AI-friendly generics

Syntax phải rõ:

```text
fn sort<T: Ordered>(items: []T)
```

tốt hơn một hệ thống generic có nhiều implicit magic.

Compiler diagnostic nên nói:

```text
T does not implement Ordered
required by sort<T>
```

---

# 426.75 — Generic error diagnostics

Khi lỗi sâu:

```text
foo<Bar<Baz<Qux>>>
```

compiler phải hiển thị:

```text
required:
    T: Serializable

found:
    MyType

missing:
    Serialize
```

thay vì chỉ báo một internal compiler error.

---

# 426.76 — Static dispatch performance contract

Generic/static dispatch có thể:

```text
inline
devirtualize
constant-fold
vectorize
```

mà không cần runtime dispatch.

---

# 426.77 — Dynamic dispatch performance contract

Dynamic interface:

```text
x.draw()
```

có cost:

```text
load vtable
load function pointer
indirect call
```

Compiler không được giả vờ đây là zero-cost.

Nhưng nếu concrete type có thể được chứng minh tại compile time, compiler được phép devirtualize.

---

# 426.78 — Devirtualization

Ví dụ:

```text
fn render(x: dyn Drawable)
```

nếu call site biết:

```text
x = Button
```

compiler có thể biến:

```text
vtable call
```

thành:

```text
Button.draw()
```

nếu không phá semantics.

---

# 426.79 — Interface in collections

Có thể:

```text
items: []dyn Drawable
```

nhưng mỗi element là interface representation.

Có thể dùng:

```text
[]Box<dyn Drawable>
```

nếu collection cần ownership.

---

# 426.80 — No universal object allocation

Ví dụ:

```text
struct Button
```

không tự động:

```text
heap allocate
vtable allocate
RTTI allocate
```

chỉ vì nó implements trait.

---

# 426.81 — Trait dispatch and FFI

FFI C function có thể nhận function pointer.

Axiom có thể chuyển trait method/static function thành callback khi ABI compatible.

Dynamic interface không tự động map thành C ABI.

---

# 426.82 — Function pointer vs interface

Function pointer:

```text
fn(T) -> R
```

chỉ chứa code address nếu không capture.

Closure:

```text
code + environment
```

Dynamic interface:

```text
object + vtable
```

Ba representation này phải được phân biệt.

---

# 426.83 — Closure traits

Có thể có capabilities:

```text
Fn
FnMut
FnOnce
```

hoặc Axiom-equivalent:

```text
Callable
MutableCallable
ConsumingCallable
```

Chúng map vào ownership semantics.

---

# 426.84 — FnOnce

Closure consuming captured resource:

```text
closure()
```

có thể consume environment.

Phù hợp với:

```text
thread.spawn(move closure)
```

---

# 426.85 — FnMut

Closure có mutable captured state.

Compiler phải đảm bảo invocation semantics phù hợp ownership.

---

# 426.86 — Fn

Read-only closure có thể invoke nhiều lần.

Không cần heap allocation nếu closure không escape.

---

# 426.87 — Generic closure optimization

Nếu function nhận:

```text
fn apply<F: Callable>(f: F)
```

compiler có thể monomorphize closure.

Không có indirect call.

---

# 426.88 — Dynamic closure

Nếu cần runtime callback collection:

```text
Box<dyn Callable>
```

có thể dùng vtable.

Explicit dynamic cost.

---

# 426.89 — Trait object auto traits

`Send`/`Share` properties của:

```text
dyn Trait
```

phải phụ thuộc concrete object's capabilities.

Ví dụ một interface object chỉ được gửi thread nếu underlying object là `Send`.

---

# 426.90 — Generic bounds and ownership

```text
fn consume<T>(x: T)
```

mặc định có thể consume/move `x`.

Nếu function chỉ cần view:

```text
fn inspect<T>(x: view T)
```

không lấy ownership.

Exact syntax sẽ được khóa ở ownership/type syntax task.

---

# 426.91 — Generic bounds and Copy

Nếu function cần duplicate:

```text
fn duplicate<T: Copy>(x: T) -> ...
```

compiler không tự copy arbitrary resource types.

---

# 426.92 — Generic bounds and Clone

Nếu cần deep duplication:

```text
fn duplicate<T: Clone>(x: T)
```

gọi explicit clone semantics.

---

# 426.93 — Generic bounds and Drop

Generic code phải có khả năng cleanup:

```text
T: Drop
```

hoặc compiler biết generic `T` có destructor automatically.

Drop glue phải được specialize.

---

# 426.94 — Generic layout

Compiler phải biết:

```text
size_of<T>
align_of<T>
```

ở mỗi specialization.

Do đó generic struct có thể compile thành compact native layout.

---

# 426.95 — Generic optimization

Compiler được phép specialize:

```text
Array<T>
```

theo:

```text
T size
T alignment
T Copy
T Drop
```

để loại bỏ unnecessary operations.

---

# 426.96 — Generic code generation strategy

Axiom compiler nên hỗ trợ hai chiến lược:

```text
Monomorphization
        +
Shared generic implementation
```

Monomorphization là default cho performance-critical native code.

Shared implementation có thể được dùng khi:

```text
code size
compile time
ABI
```

có lợi.

---

# 426.97 — Linker deduplication

Nếu hai modules tạo identical specialization:

```text
foo<i32>
foo<i32>
```

linker/compiler artifact system có thể merge.

Điều này kết nối trực tiếp với BOOTSTRAP-420.

---

# 426.98 — Hard invariants

BOOTSTRAP-426 khóa:

1. Không có class hierarchy trong core.
2. Struct là fundamental aggregate/object-like type.
3. Function có `self` là method-like function.
4. Trait biểu diễn capability/behavior contract.
5. Generic là static polymorphism mặc định.
6. Static generic được ưu tiên monomorphization.
7. Dynamic polymorphism phải explicit.
8. Dynamic interface dùng data pointer + vtable hoặc target-equivalent representation.
9. Không có hidden object header.
10. Không có mandatory RTTI.
11. Không có mandatory virtual dispatch.
12. Trait implementation không tạo runtime overhead nếu static.
13. Generic constraints được kiểm tra compile-time.
14. Associated types/constants được hỗ trợ.
15. Trait default implementation được hỗ trợ.
16. Trait composition được hỗ trợ.
17. Operator/conversion/iteration có thể xây bằng traits.
18. Closure có ownership-aware callable semantics.
19. `Send`/`Share` integrate với trait system.
20. Generic code phải tương thích ABI/native backend.
21. Generic C FFI phải instantiate thành concrete ABI.
22. Compiler phải hỗ trợ generic specialization/cache.
23. Linker được phép deduplicate identical generic code.
24. Dynamic interface ABI phải versionable.
25. Reflection/RTTI chỉ là optional metadata.

---

# 426.99 — Final architecture

Axiom abstraction stack:

```text
                         TYPE
                          │
              ┌───────────┴───────────┐
              ▼                       ▼
           STRUCT                    ENUM
              │                       │
              └──────────┬────────────┘
                         ▼
                       TRAIT
                         │
             ┌───────────┴───────────┐
             ▼                       ▼
          GENERIC                 INTERFACE
             │                       │
             ▼                       ▼
      MONOMORPHIZATION            VTABLE
             │                       │
             ▼                       ▼
       STATIC NATIVE             DYNAMIC NATIVE
          CALL                     CALL
```

Đây là kiến trúc rất quan trọng đối với mục tiêu ban đầu của Axiom:

```text
C-like data representation
+
C++-level zero-cost abstraction
+
modern trait/generic system
+
explicit dynamic dispatch
-
class hierarchy
-
mandatory GC
-
mandatory virtual dispatch
```

---

# BOOTSTRAP-427 — MODULES, PACKAGES, NAMESPACE, VISIBILITY & BUILD GRAPH

Sau type/generic system, phần cần khóa tiếp theo là **module/package system**. Đây là nền móng để compiler có thể xây project lớn, cache từng module, parallel compilation và cuối cùng self-host Axiom.

## 427.1 — Module goals

Axiom module system phải:

```text
427.1    module goals
427.2    source files
427.3    modules
427.4    packages
427.5    project
427.6    namespaces
427.7    imports
427.8    exports
427.9    visibility
427.10   public/private
427.11   package visibility
427.12   module visibility
427.13   symbol qualification
427.14   aliases
427.15   re-export
427.16   cyclic imports
427.17   module initialization
427.18   package metadata
427.19   dependency graph
427.20   versioning
427.21   semantic version constraints
427.22   lockfile
427.23   local dependencies
427.24   system dependencies
427.25   native libraries
427.26   C interoperability
427.27   generated sources
427.28   build scripts
427.29   compiler plugins
427.30   procedural generation
427.31   macro boundary
427.32   compile-time execution
427.33   module interface files
427.34   precompiled modules
427.35   incremental compilation
427.36   dependency fingerprints
427.37   parallel compilation
427.38   deterministic builds
427.39   package cache
427.40   source maps
427.41   diagnostics
427.42   IDE/LSP integration
427.43   AI-readable module metadata
427.44   security/trust model
427.45   offline builds
427.46   vendoring
427.47   bootstrap compiler interaction
427.48   native artifact interaction
427.49   conformance tests
427.50   final module/package contract
```

Điểm đặc biệt của **427** sẽ là kết nối trực tiếp với mục tiêu Axiom đã đặt từ đầu:

```text
source unchanged
       ↓
fingerprint unchanged
       ↓
reuse compiled module
       ↓
reuse generic specializations
       ↓
reuse native artifacts
```

tức **incremental compilation và build cache sẽ trở thành một phần kiến trúc compiler**, chứ không phải một tiện ích build bên ngoài.