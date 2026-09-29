# BOOTSTRAP-232 — AXIOM BEHAVIOR MODEL
## Functions, Methods, Traits, Generics, Closures & Dynamic Dispatch

**TRẠNG THÁI: FROZEN / COMPLETED**

Mục tiêu của task này là hoàn thiện mô hình behavior của Axiom mà **không cần class/inheritance/virtual mặc định**, nhưng vẫn có đủ:

- method
- override
- polymorphism
- generic programming
- static dispatch
- dynamic dispatch
- closures
- function pointers
- trait objects
- zero-cost abstraction

Nguyên tắc trung tâm:

> **Behavior thuộc về function/trait, không thuộc về object/class hierarchy.**

Và:

> **Static dispatch là mặc định. Dynamic dispatch chỉ xuất hiện khi programmer hoặc ABI thực sự yêu cầu.**

---

# 1. Behavior model tổng thể

Axiom có 6 mức abstraction:

```text
Function
   ↓
Inherent Method
   ↓
Trait Implementation
   ↓
Generic Function
   ↓
Static Polymorphism
   ↓
Dynamic Polymorphism
```

Trong đó:

```text
Function
```

là primitive.

Method chỉ là syntax sugar.

Trait là contract.

Generic là compile-time abstraction.

`dyn Trait` mới là runtime polymorphism.

---

# 2. Function là primitive behavior

Ví dụ:

```axiom
fn distance(a: Point, b: Point) -> f32 {
    ...
}
```

Semantics:

```text
FunctionId
ParameterTypes
ReturnType
Effects
ABI
GenericParameters
Body
```

Không tồn tại concept:

```text
function belongs to object
```

---

# 3. Method chỉ là sugar

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
v.length()
```

Compiler canonicalize thành:

```axiom
length(v)
```

Không có:

```text
this
vtable
hidden object header
```

trừ khi một abstraction khác thực sự yêu cầu.

---

# 4. `self` không phải magic object reference

`self` chỉ là tên parameter có convention đặc biệt.

Các dạng:

```axiom
fn f(self: T)
fn f(self: mut_view<T>)
fn f(self: view<T>)
fn f(self: T, ...)
```

tương ứng với:

```text
owned receiver
mutable receiver capability
read receiver capability
```

---

# 5. Receiver resolution

Khi compiler gặp:

```axiom
x.foo(a)
```

nó tìm theo thứ tự:

```text
1. Inherent function
2. Trait implementation
3. Imported extension
4. Generic extension
```

Nếu có nhiều candidate cùng mức:

```text
compile error: ambiguous method
```

Không chọn theo thứ tự import ngẫu nhiên.

---

# 6. Inherent methods

```axiom
struct Vec2 {
    x: f32
    y: f32
}

fn length(self: view<Vec2>) -> f32 {
    ...
}
```

Method này thuộc namespace behavior của `Vec2`, nhưng vẫn chỉ là function.

Compiler representation:

```text
FunctionId::length
ReceiverType = Vec2
```

---

# 7. Không có method table mặc định

Struct:

```axiom
struct Point {
    x: i32
    y: i32
}
```

không chứa:

```text
vtable*
type_info*
object_header*
class_pointer*
```

Representation có thể chỉ là:

```text
x
y
```

---

# 8. Trait

Trait định nghĩa behavior contract:

```axiom
trait Drawable {
    fn draw(self: view<Self>)
}
```

Trait không tự động tạo object representation.

Nó tạo:

```text
TraitId
MethodSet
AssociatedTypes
AssociatedConstants
Constraints
DefaultImplementations
```

---

# 9. Implementation

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

Compiler tạo relation:

```text
Circle ──implements──> Drawable
```

---

# 10. Trait implementation không phải inheritance

Không có:

```text
Circle : Shape
```

theo kiểu class hierarchy.

Thay vào đó:

```text
Circle implements Drawable
Circle implements Area
Circle implements Serializable
Circle implements Send
```

Các contracts độc lập.

---

# 11. Một type có thể implement nhiều trait

```axiom
impl Drawable for Circle { ... }
impl Area for Circle { ... }
impl Clone for Circle { ... }
impl Debug for Circle { ... }
```

Không có diamond inheritance.

---

# 12. Trait composition

Generic function:

```axiom
fn render<T: Drawable>(x: T) {
    x.draw()
}
```

được hiểu là:

```text
T must have a valid Drawable implementation
```

Không cần runtime type checking.

---

# 13. Static dispatch

Với:

```axiom
fn render<T: Drawable>(x: T) {
    x.draw()
}
```

compiler có thể instantiate:

```text
render<Circle>
render<Rectangle>
render<Sprite>
```

và mỗi instance gọi implementation cụ thể.

---

# 14. Monomorphization

Conceptual:

```text
render<T>
```

↓

```text
render_Circle
render_Rectangle
render_Sprite
```

Compiler có thể inline:

```text
render_Circle
    ↓
Circle.draw()
```

và loại bỏ abstraction hoàn toàn.

---

# 15. Nhưng không bắt buộc duplicate code

Monomorphization có thể gây code bloat.

Axiom compiler được phép sử dụng:

```text
Monomorphization
Code sharing
Outline common body
Hybrid generic lowering
```

miễn semantic contract giữ nguyên.

---

# 16. Generic dispatch không phải dynamic dispatch

Đây là distinction quan trọng:

```axiom
fn f<T: Trait>(x: T)
```

khác:

```axiom
fn f(x: dyn Trait)
```

Cái đầu:

```text
compile-time type
```

Cái sau:

```text
runtime polymorphism
```

---

# 17. `dyn Trait`

Dynamic polymorphism được biểu diễn rõ ràng:

```axiom
fn draw_any(x: dyn Drawable) {
    x.draw()
}
```

Đây mới là nơi compiler cần dynamic dispatch.

---

# 18. `dyn Trait` không phải object class

Nó là:

```text
type-erased value
+
trait capability
```

Không tạo inheritance tree.

---

# 19. Runtime representation

Một `dyn Trait` có thể được biểu diễn conceptually:

```text
(data pointer, dispatch metadata)
```

Metadata có thể chứa:

```text
method pointers
type metadata
drop function
size
alignment
```

Nhưng representation này là ABI/compiler detail.

---

# 20. Không phải mọi `dyn Trait` đều cần heap

Ví dụ:

```axiom
let x: dyn Drawable = circle
```

không có nghĩa:

```text
heap allocation
```

Compiler có thể sử dụng:

```text
stack storage
inline storage
caller storage
existing allocation
```

nếu ABI cho phép.

---

# 21. Boxing chỉ khi cần

Nếu dynamic value cần stable ownership/storage:

```axiom
let x = Box(circle)
```

mới tạo explicit owned dynamic storage abstraction.

Dynamic dispatch và heap allocation là **hai vấn đề khác nhau**.

---

# 22. Fat representation không phải object header

`dyn Trait` có thể có metadata bên ngoài value.

Ví dụ conceptual:

```text
DynValue {
    data: pointer
    metadata: vtable pointer
}
```

Struct `Circle` vẫn không có object header.

---

# 23. Trait object safety

Không phải trait nào cũng tự động usable as `dyn Trait`.

Ví dụ method:

```axiom
trait Factory {
    fn create<T>() -> T
}
```

không có runtime representation đơn giản cho dynamic dispatch.

Compiler phải reject:

```text
dyn Factory
```

nếu trait không satisfy dynamic-object contract.

---

# 24. Object-safe trait

Trait usable as `dyn Trait` phải có:

- dynamically representable receiver
- known ABI
- no unresolved generic method at runtime
- associated-type constraints resolvable
- dispatchable method signature

---

# 25. Generic method trong trait

```axiom
trait Transform {
    fn transform<T>(self, x: T)
}
```

trait vẫn có thể tồn tại.

Nhưng:

```text
dyn Transform
```

không nhất thiết hỗ trợ method generic.

Có thể:

```text
trait exists
generic static use valid
dyn Trait use rejected
```

---

# 26. Associated type

```axiom
trait Iterator {
    type Item

    fn next(self: mut_view<Self>) -> Option<Self::Item>
}
```

Với generic:

```axiom
fn consume<I: Iterator>(x: I)
```

compiler biết:

```text
I::Item
```

compile time.

---

# 27. Dynamic associated type

Nếu dùng:

```axiom
dyn Iterator
```

compiler cần xác định associated type:

```axiom
dyn Iterator<Item = i32>
```

hoặc một cơ chế tương đương.

Nếu không xác định được → type incomplete.

---

# 28. Default trait method

```axiom
trait Printable {
    fn print(self: view<Self>) {
        ...
    }
}
```

Concrete type có thể không override.

Compiler dùng default implementation.

---

# 29. Override

Không cần:

```text
override
virtual
final
```

Ví dụ:

```axiom
trait Printable {
    fn print(self: view<Self>) {
        default_print(self)
    }
}

struct User {
    id: u64
}

impl Printable for User {
    fn print(self: view<User>) {
        print_user(self)
    }
}
```

Implementation cụ thể **replaces the default implementation**.

---

# 30. Override semantics

Compiler resolution:

```text
Concrete impl method
        ↓
if absent
        ↓
trait default method
```

Không tồn tại runtime virtual override nếu function được static dispatch.

---

# 31. Đây là “override” thực sự

Ví dụ:

```axiom
fn f<T: Printable>(x: T) {
    x.print()
}
```

với:

```text
User → own implementation
Product → default implementation
```

Compiler specialization sẽ chọn đúng implementation.

Không cần vtable.

---

# 32. No inheritance override

Axiom không có:

```text
Base
  ↑
Derived
```

nên không có vấn đề:

```text
Base::foo
Derived::foo
super.foo()
```

theo kiểu class.

---

# 33. Gọi default implementation

Nếu cần gọi implementation mặc định:

```axiom
Printable::print_default(self)
```

hoặc compiler/library-defined trait-qualified syntax.

Đây là trait dispatch, không phải superclass dispatch.

---

# 34. Trait specialization

Không nên cho arbitrary specialization trong v1.

Ví dụ:

```axiom
impl<T> Foo for T
impl Foo for i32
```

có thể gây overlap.

Do đó:

> **Coherence + overlap checking là bắt buộc.**

---

# 35. Coherence

Compiler phải đảm bảo không tồn tại hai implementation hợp lệ cạnh tranh cho cùng:

```text
Trait × Type
```

trừ các specialization rules được language cho phép.

---

# 36. Orphan rule

Package không được tùy ý implement foreign trait cho foreign type.

Ví dụ conceptual:

```text
foreign package:
    trait Foo

foreign package:
    struct Bar
```

package thứ ba không thể tự tạo:

```text
impl Foo for Bar
```

nếu không sở hữu một phía theo coherence rule.

---

# 37. Extension methods

Nếu muốn thêm method cho type foreign:

```axiom
fn clamp(self: f32, min: f32, max: f32) -> f32
```

có thể import:

```axiom
use math::Clamp
```

Method vẫn là function.

Không modify type.

---

# 38. Method ambiguity

Nếu import:

```text
A.foo
B.foo
```

và cả hai đều match:

```axiom
x.foo()
```

→ compile error.

Có thể gọi fully qualified:

```axiom
A::foo(x)
B::foo(x)
```

---

# 39. Function pointer

Function không capture environment:

```axiom
fn add(a: i32, b: i32) -> i32
```

có thể chuyển thành:

```text
fn(i32, i32) -> i32
```

function pointer representation target-dependent.

---

# 40. Capturing closure

```axiom
let offset = 10

let add = |x| x + offset
```

Closure semantic type chứa environment.

Conceptual:

```text
Closure {
    captured offset
    invoke function
}
```

---

# 41. Closure không phải object

Closure là compiler-generated anonymous struct + function.

Ví dụ conceptual:

```text
struct Closure_17 {
    offset: i32
}

fn Closure_17_call(self: view<Closure_17>, x: i32) -> i32
```

Compiler có thể eliminate toàn bộ abstraction.

---

# 42. Capture mode inference

Compiler xác định:

```text
READ capture
MUTATE capture
MOVE capture
```

theo actual usage.

Không yêu cầu programmer viết capture mode trong trường hợp bình thường.

---

# 43. Closure capture ownership

Nếu closure cần giữ ownership:

```axiom
let task = || use(buffer)
```

compiler xác định `buffer` phải được captured by move nếu semantic usage yêu cầu.

Không implicit clone.

---

# 44. Closure escape

Compiler kiểm tra:

```text
NoEscape
ReturnEscape
HeapEscape
ThreadEscape
AsyncEscape
```

Closure environment được storage-promote khi cần.

---

# 45. Closure allocation

Một closure:

```axiom
map(data, |x| x * 2)
```

không được mặc định heap allocate.

Compiler có thể:

```text
inline
stack
register
SSA
specialize
```

và thường loại bỏ environment object hoàn toàn.

---

# 46. Closure as generic parameter

API:

```axiom
fn map<I, F>(iter: I, f: F)
where F: Fn(...)
```

là static dispatch.

Đây là zero-cost route.

---

# 47. Closure as `dyn Fn`

Nếu thực sự cần runtime polymorphism:

```axiom
dyn Fn(i32) -> i32
```

thì dynamic dispatch có thể xuất hiện.

---

# 48. Async closure

Async closure có thể lower thành:

```text
closure environment
+
Future state machine
```

Compiler chỉ lưu các giá trị sống qua suspension.

---

# 49. Function effects

Behavior model phải giữ effect information:

```text
fn f(...) -> T
```

có thể có:

```text
Pure
Read
Write
Allocate
IO
Atomic
Sync
Panic
Unsafe
Foreign
Async
GPU
```

Generic code phải verify effect compatibility.

---

# 50. Function type

Function type semantic identity bao gồm:

```text
Parameter types
Return type
Calling convention
Effects
Safety
Asyncness
Execution domain
```

Không chỉ đơn giản là:

```text
(T1,T2) -> T3
```

ở compiler internal level.

---

# 51. `unsafe fn`

```axiom
unsafe fn read_raw(p: *const u8) -> u8
```

unsafe là property của callable contract.

Caller phải cross unsafe boundary.

---

# 52. `async fn`

```axiom
async fn fetch() -> Result<Data, Error>
```

không phải function:

```text
fn() -> Data
```

mà semantic return là Future producing result.

---

# 53. Generic async

```axiom
async fn process<T: Read>(x: T)
```

generic constraints được resolve trước async lowering.

---

# 54. Trait method dispatch pipeline

Khi compiler gặp:

```axiom
x.draw()
```

pipeline:

```text
Resolve receiver type
       ↓
Find candidates
       ↓
Select trait/inherent implementation
       ↓
Determine static/dynamic dispatch
       ↓
Type/effect/ownership checking
       ↓
HIR Call
       ↓
MIR Call
```

---

# 55. Static dispatch representation

```text
Call {
    FunctionId = Circle::draw
}
```

Không còn trait lookup ở runtime.

---

# 56. Dynamic dispatch representation

```text
DynCall {
    TraitId
    MethodId
    Receiver
}
```

ABI lowering sau đó quyết định:

```text
vtable lookup
itable
direct cached target
devirtualized direct call
```

---

# 57. Devirtualization

Ngay cả khi source dùng:

```axiom
dyn Drawable
```

compiler có thể phát hiện runtime type luôn là:

```text
Circle
```

và biến:

```text
dynamic call
```

thành:

```text
direct call
```

nếu proof hợp lệ.

---

# 58. Nhưng semantics không phụ thuộc optimization

Nếu compiler không chứng minh được:

```text
dynamic target = Circle
```

thì giữ dynamic dispatch.

Không được đoán.

---

# 59. Vtable layout

Vtable không thuộc Core language semantics.

ABI layer có thể định nghĩa:

```text
drop
size
align
method_0
method_1
...
```

hoặc một representation khác.

---

# 60. Trait object lifetime

`dyn Trait` vẫn tuân ownership/capability.

Ví dụ:

```text
dyn Trait
```

không có nghĩa value tự sống mãi.

Nếu chứa view:

```text
dyn Trait containing view
```

provenance phải được giữ.

---

# 61. Dynamic trait object không bypass ownership

Không được:

```text
Box<dyn Trait>
```

rồi lấy object ra sau khi owner chết.

Verifier vẫn theo dõi:

```text
owner
capability
storage
lifetime
```

---

# 62. Trait object + Send

Không mặc định:

```text
dyn Trait
```

có thể chuyển thread.

Phải satisfy:

```text
dyn Trait + Send
```

theo type-system contract.

---

# 63. Trait object + Share

Tương tự:

```text
dyn Trait + Share
```

chỉ hợp lệ nếu underlying representation và trait contract đáp ứng Share.

---

# 64. Dynamic mutable access

`dyn Trait` không tự cho phép mutable access.

Nếu method yêu cầu:

```text
mut_view<Self>
```

caller phải có exclusive capability.

---

# 65. Dynamic dispatch + GPU

GPU kernel không nên phụ thuộc arbitrary `dyn Trait`.

GPU legality có thể giới hạn:

```text
no dynamic allocation
no unsupported dynamic dispatch
no runtime metadata
```

Static trait dispatch là route chính.

---

# 66. Generics + ABI

Generic internal functions không cần stable ABI.

Ví dụ:

```axiom
fn max<T: Ord>(a: T, b: T) -> T
```

compiler tự specialize.

Nếu muốn expose generic API qua stable ABI, phải có explicit ABI strategy.

---

# 67. Stable ABI boundary

Không được expose compiler-specific generic representation qua:

```text
@abi(stable)
```

trừ khi ABI contract định nghĩa rõ.

Thông thường:

```text
generic internal
```

→ erased/wrapped concrete ABI boundary.

---

# 68. Trait ABI

Stable dynamic trait ABI cần versioning:

```text
TraitAbiId
Version
MethodSet
CallingConvention
Layout
ErrorContract
PanicContract
```

Nếu method thêm vào trait stable:

```text
ABI version changes
```

hoặc compatibility mechanism explicit.

---

# 69. No implicit dynamic dispatch

Điều này cực kỳ quan trọng.

Nếu programmer viết:

```axiom
fn draw<T: Drawable>(x: T)
```

compiler **không được** tự biến thành:

```text
vtable dispatch
```

chỉ để giảm codegen complexity.

Static semantics phải được giữ.

---

# 70. Dynamic dispatch phải explicit

Canonical:

```axiom
fn draw(x: dyn Drawable)
```

hoặc API/ABI abstraction tương đương.

Programmer nhìn source và biết:

> đây là dynamic polymorphism.

---

# 71. Generic constraints không phải inheritance constraints

```axiom
T: Drawable + Send + Clone
```

nghĩa:

```text
T satisfies three independent contracts
```

Không tạo hierarchy.

---

# 72. Trait inheritance

Axiom có thể cho phép trait supertraits:

```axiom
trait Shape: Drawable + Sized {
    ...
}
```

nhưng semantic meaning là:

```text
Shape requires Drawable
Shape requires Sized
```

Không phải class inheritance.

---

# 73. Trait upcasting

Nếu:

```text
Shape: Drawable
```

thì:

```text
dyn Shape
```

có thể chuyển thành:

```text
dyn Drawable
```

nếu ABI/object-safety contract cho phép.

Đây là **trait capability conversion**, không phải object inheritance.

---

# 74. Downcast

Dynamic trait có thể cần:

```text
dyn Drawable
    ↓
Circle
```

Nhưng downcast không được tự động.

Cần explicit runtime type mechanism:

```text
Any / TypeId / metadata
```

ở library/reflection layer.

---

# 75. Downcast không thuộc safe Core primitive

Core chỉ đảm bảo:

```text
dyn Trait
```

dispatch đúng contract.

Type inspection là reflection/runtime metadata concern.

---

# 76. Operator overloading

Operators map tới traits/functions.

Ví dụ:

```axiom
a + b
```

→ semantic `Add::add(a,b)`.

Compiler vẫn xử lý:

```text
short-circuit && ||
```

như language primitives.

---

# 77. Indexing

```axiom
x[i]
```

có thể resolve tới indexing trait.

Compiler vẫn kiểm tra:

```text
bounds
capability
ownership
```

---

# 78. Call operator

Closure:

```axiom
f(x)
```

được canonicalize tới callable protocol.

Compiler phân biệt:

```text
Function
FunctionPointer
Closure
DynCallable
```

---

# 79. No universal `Object`

Axiom không cần:

```text
Object
Any
BaseObject
```

Mọi polymorphism được giải quyết bằng:

```text
Generic
Trait
dyn Trait
```

---

# 80. Type erasure

Khi cần:

```text
dyn Trait
```

là explicit type erasure.

Compiler phải biết:

```text
original concrete type
trait contract
dispatch metadata
ownership
storage
```

---

# 81. Type erasure không clone

Ví dụ:

```axiom
let d: dyn Drawable = circle
```

không được implicit:

```text
circle.clone()
```

Nếu cần duplicate:

```axiom
circle.clone()
```

hoặc trait phải cung cấp cloning semantics.

---

# 82. Dynamic collection

Ví dụ:

```axiom
let items: Vec<dyn Drawable>
```

cần representation rõ ràng.

Có thể:

```text
Vec<Box<dyn Drawable>>
```

hoặc inline dynamic-object representation.

Nhưng **heap allocation chỉ xuất hiện nếu chosen storage abstraction yêu cầu**.

---

# 83. Better default for heterogeneous collections

Với các object có kích thước khác nhau:

```text
Vec<dyn Trait>
```

compiler/library có thể dùng:

```text
boxed
arena
small-buffer
indirect
```

implementation strategy.

Không ép language Core chọn một layout duy nhất.

---

# 84. Heterogeneous enum alternative

Nếu tập hợp type known compile time:

```axiom
enum Shape {
    Circle(Circle)
    Rect(Rectangle)
    Triangle(Triangle)
}
```

thường không cần dynamic dispatch.

Compiler biết tất cả variants.

---

# 85. Enum vs dyn Trait

```text
enum
```

→ closed set, static dispatch possible.

```text
dyn Trait
```

→ open set, runtime polymorphism.

Đây là distinction quan trọng cho thiết kế API.

---

# 86. Generic vs enum vs dyn

```text
Generic:
    compile-time open abstraction

Enum:
    compile-time closed alternatives

dyn Trait:
    runtime open abstraction
```

Ba cơ chế bổ sung nhau.

---

# 87. Closure vs trait object

```text
F: Fn(...)
```

→ static.

```text
dyn Fn(...)
```

→ dynamic.

Closure itself không yêu cầu vtable.

---

# 88. Method syntax remains ergonomic

Programmer có thể viết:

```axiom
mesh.render()
file.read(buffer)
tensor.reshape(shape)
```

nhưng compiler vẫn thấy:

```text
render(mesh)
read(file, buffer)
reshape(tensor, shape)
```

---

# 89. Đây giúp Axiom tránh “class trap”

Class thường gom:

```text
data
identity
inheritance
dispatch
allocation
lifetime
```

vào một abstraction.

Axiom tách:

```text
data      → struct
behavior  → function
contract  → trait
ownership → ownership
identity  → value/storage/logical identity
dispatch  → static/dynamic explicitly
storage   → Box/Vec/etc.
```

Do đó compiler có thể optimize từng phần độc lập.

---

# 90. Behavior lowering

Compiler architecture:

```text
Surface Method Call
        ↓
Method Resolution
        ↓
Canonical Function Call
        ↓
Trait Resolution
        ↓
Generic Instantiation
        ↓
Static/Dynamic Dispatch Selection
        ↓
Typed HIR
        ↓
MIR
```

---

# 91. Function specialization

Compiler có thể specialize theo:

```text
type
constant
target feature
effect
capability
execution domain
```

Ví dụ:

```text
sort<T>
```

→ integer-specialized implementation.

---

# 92. Specialization phải preserve coherence

Không được tạo specialization làm thay đổi:

```text
which trait implementation is selected
```

một cách phụ thuộc optimization level.

Trait resolution phải deterministic **trước optimization**.

---

# 93. Inlining

Function/method/trait/generic call đều có thể inline.

Nhưng:

```text
inline
```

là optimization, không phải semantic dispatch mechanism.

---

# 94. Recursive functions

Function có thể recursive:

```axiom
fn factorial(n: u64) -> u64 {
    if n <= 1 {
        1
    } else {
        n * factorial(n - 1)
    }
}
```

Compiler không được giả định tail-call trừ khi ABI/target contract cho phép.

---

# 95. Tail calls

Có thể có semantic/ABI operation:

```text
tail_call
```

ở backend.

Không cần Core syntax.

---

# 96. First-class functions

Function values có thể được truyền:

```axiom
fn apply(f: fn(i32) -> i32, x: i32) -> i32 {
    f(x)
}
```

Function pointer không capture environment.

---

# 97. Closure conversion

Compiler:

```text
closure
```

→

```text
environment struct
+
invoke function
```

sau đó optimizer có thể:

```text
inline
scalarize
eliminate environment
```

---

# 98. Recursive closure

Recursive closure cần explicit finite representation hoặc named function.

Compiler không được tạo infinite-size type.

---

# 99. Trait solver integration

Behavior model phụ thuộc TraitDB:

```text
Goal:
    T: Drawable

TraitSolver:
    candidate impl
    where constraints
    associated types
    coherence
```

Kết quả:

```text
Proven
NotProven
Ambiguous
Error
```

Không fallback sang runtime guessing.

---

# 100. Final architecture

```text
                    ┌───────────────┐
                    │    struct     │
                    └───────┬───────┘
                            │
                     data/value type
                            │
             ┌──────────────┴──────────────┐
             ↓                             ↓
       inherent fn                    trait impl
             │                             │
             └──────────────┬──────────────┘
                            ↓
                    generic function
                            │
                 ┌──────────┴──────────┐
                 ↓                     ↓
          static dispatch       explicit dyn Trait
                 │                     │
                 ↓                     ↓
             direct call          dynamic call
                 │                     │
                 └──────────┬──────────┘
                            ↓
                        optimizer
                            ↓
                     machine code
```

---

# 101. Frozen invariants

```text
ABEH-20
Functions are the fundamental behavior primitive.

ABEH-21
Methods are syntactic sugar over functions.

ABEH-22
A method receiver is an ordinary semantic parameter.

ABEH-23
Structs do not implicitly contain method tables.

ABEH-24
Structs do not implicitly contain object headers.

ABEH-25
Traits define behavior contracts rather than class inheritance.

ABEH-26
A type may implement multiple independent traits.

ABEH-27
Trait implementation does not imply object inheritance.

ABEH-28
Generic trait bounds are compile-time constraints.

ABEH-29
Static dispatch is the default dispatch mechanism.

ABEH-30
Generic dispatch does not imply runtime dispatch.

ABEH-31
Monomorphization may eliminate generic abstraction overhead.

ABEH-32
The compiler may use code sharing to reduce generic code bloat.

ABEH-33
Dynamic dispatch requires an explicit dynamic abstraction.

ABEH-34
dyn Trait represents runtime trait-based polymorphism.

ABEH-35
dyn Trait does not imply heap allocation.

ABEH-36
Dynamic dispatch does not imply an object header in the underlying concrete type.

ABEH-37
Dynamic trait representation is an ABI/compiler concern.

ABEH-38
Trait object safety is checked statically.

ABEH-39
Non-object-safe traits cannot be used as dyn Trait unless an explicit adapter exists.

ABEH-40
Default trait methods may be replaced by concrete implementations.

ABEH-41
Concrete replacement of a trait default does not require an override keyword.

ABEH-42
Trait implementation selection is deterministic.

ABEH-43
Trait resolution occurs before optimization.

ABEH-44
Optimization cannot change trait implementation semantics.

ABEH-45
Coherence prevents conflicting trait implementations.

ABEH-46
Specialization must not introduce optimization-dependent semantic ambiguity.

ABEH-47
Extension methods are functions and do not mutate the extended type definition.

ABEH-48
Ambiguous method resolution is a compile-time error.

ABEH-49
Fully qualified function or trait syntax can disambiguate method calls.

ABEH-50
Closures are compiler-generated callable values with explicit captured state.

ABEH-51
Closure capture mode is inferred from semantic use.

ABEH-52
Closure capture never implicitly clones an owned value.

ABEH-53
Closure environments obey normal ownership and capability verification.

ABEH-54
Closure allocation is not mandatory.

ABEH-55
Capturing closures may be stack, inline, register, heap, arena, or otherwise optimized.

ABEH-56
Closure abstraction may be completely eliminated by optimization.

ABEH-57
Function pointers do not contain captured environments.

ABEH-58
Capturing closures are distinct from ordinary function pointers.

ABEH-59
Noncapturing closures may be converted to compatible function pointers when safe.

ABEH-60
dyn callable values use explicit runtime polymorphism.

ABEH-61
Trait objects obey ordinary ownership rules.

ABEH-62
Trait objects obey ordinary capability rules.

ABEH-63
Trait objects do not implicitly become Send.

ABEH-64
Trait objects do not implicitly become Share.

ABEH-65
Dynamic trait values do not implicitly clone underlying values.

ABEH-66
Trait upcasting is an explicit type-system conversion.

ABEH-67
Downcasting requires explicit runtime type information.

ABEH-68
Downcasting is not an implicit safe Core operation.

ABEH-69
Enum-based closed polymorphism remains distinct from dyn Trait.

ABEH-70
Generic abstraction represents compile-time polymorphism.

ABEH-71
Enum abstraction represents closed-set polymorphism.

ABEH-72
dyn Trait represents runtime open-set polymorphism.

ABEH-73
Function effects are part of the compiler semantic model.

ABEH-74
Unsafe is part of callable semantic contracts.

ABEH-75
Async is part of callable semantic contracts.

ABEH-76
GPU execution restrictions are part of callable semantic contracts.

ABEH-77
Function types include sufficient ABI and semantic information for correct lowering.

ABEH-78
Stable ABI cannot expose unspecified generic or trait-object representation.

ABEH-79
Stable dynamic trait interfaces require explicit ABI contracts.

ABEH-80
Vtable representation is not part of portable Core semantics.

ABEH-81
Compiler devirtualization is legal only when the dynamic target is proven.

ABEH-82
Failure to prove devirtualization preserves dynamic dispatch.

ABEH-83
Dynamic dispatch may be optimized away without changing semantics.

ABEH-84
Static dispatch must never silently become dynamic dispatch.

ABEH-85
Generic code cannot implicitly allocate solely because of polymorphism.

ABEH-86
Dynamic polymorphism cannot implicitly introduce cloning.

ABEH-87
Method syntax must canonicalize to ordinary callable semantics.

ABEH-88
Receiver ownership and capability requirements participate in method resolution.

ABEH-89
Trait-associated types are compile-time semantic entities unless explicitly erased.

ABEH-90
Axiom has no universal Object or class root type.
```

---

# 102. Kết luận kiến trúc

Đây là điểm rất quan trọng đối với mục tiêu ban đầu của Axiom.

Axiom không loại bỏ OOP bằng cách làm language yếu đi.

Nó **tách OOP thành những primitive nhỏ hơn**:

| Nhu cầu | Axiom |
|---|---|
| Data | `struct` |
| Method | function + receiver |
| Interface | `trait` |
| Inheritance-like behavior | trait composition |
| Override | concrete trait impl thay default |
| Generic polymorphism | generics |
| Runtime polymorphism | `dyn Trait` |
| Object identity | explicit storage/logical identity |
| Allocation | `Box`, collections, allocator |
| Closure | compiler-generated environment |
| Virtual call | explicit dynamic dispatch |
| Multiple behavior | multiple traits |
| Downcast | explicit runtime metadata |
| Class hierarchy | **không cần** |

Điểm mạnh nhất là **overhead không xuất hiện chỉ vì programmer sử dụng abstraction**.

Một đoạn:

```axiom
fn render<T: Drawable>(x: T) {
    x.draw()
}
```

có thể cuối cùng trở thành gần như:

```text
direct call
→ inline
→ dead code elimination
→ machine instructions
```

Trong khi:

```axiom
fn render(x: dyn Drawable)
```

thực sự yêu cầu runtime polymorphism thì compiler mới giữ dispatch machinery.

Đây phù hợp trực tiếp với triết lý:

> **Abstraction should disappear when its runtime semantics are not required.**

---

# TASK TIẾP THEO

## **BOOTSTRAP-233 — Axiom Formal Semantic Kernel & Operational Semantics**

Đây là task rất quan trọng trước khi chuyển mạnh sang implementation.

Mục tiêu là xây **“luật vật lý” chính thức của Axiom**, thay vì tiếp tục chỉ mô tả architecture.

Sẽ formalize:

```text
Program State
Value
Place
Storage
Ownership
Capability
Region
Environment
Expression Evaluation
Move
Copy
Drop
Function Call
Method Call
Trait Resolution
Generic Instantiation
Pattern Match
Result/Option
Panic
Async Suspension
Concurrency
Atomic
Unsafe Boundary
Comptime
FFI
```

và đặc biệt tạo mô hình:

```text
Source
  ↓
Small-step / Big-step semantics
  ↓
MIR semantics
  ↓
Verified MIR
  ↓
Optimization preservation
```

để sau đó **`ax-ref` reference interpreter có thể được viết trực tiếp từ Formal Semantic Kernel**, thay vì compiler team tự đoán semantics trong quá trình implement.

Đây sẽ là một trong những specification quan trọng nhất của toàn bộ Axiom.