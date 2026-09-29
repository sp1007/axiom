# BOOTSTRAP-409 — Axiom Type System, Type Inference, Generics & Type Identity

Sau **408 — Name Resolution**, bước kế tiếp là **Type System**.

Đây là một trong những phần quan trọng nhất của Axiom vì nó phải đồng thời đạt được:

- hiệu năng gần C/C++
- không cần GC
- không cần borrow checker kiểu Rust ở source level
- không bắt programmer viết lifetime
- hỗ trợ generic mạnh
- hỗ trợ trait
- hỗ trợ ADT/enum
- hỗ trợ AI/ML/tensor
- hỗ trợ compile-time
- hỗ trợ FFI
- hỗ trợ SIMD/GPU
- giữ semantics đủ đơn giản để compiler có thể chứng minh.

Nguyên tắc trung tâm:

> **Axiom có static type system mạnh, nhưng phần lớn thông tin mà compiler có thể suy ra thì programmer không cần viết.**

---

# 1. Mục tiêu Type System

Axiom phải phân biệt rõ:

```text
Type
Type Identity
Type Representation
Type Layout
Type Ownership
Type Capability
Type Effect
ABI
```

Không được trộn chúng thành một khái niệm.

Ví dụ:

```text
Vec3
```

là một type.

Nhưng:

```text
Vec3
```

có thể có:

```text
size = 12
align = 4
layout = [f32,f32,f32]
ownership = value
```

Đây là các semantic properties khác nhau.

---

# 2. Type Identity

Hai type chỉ giống nhau khi compiler xác định chúng cùng identity.

Ví dụ:

```text
struct UserId {
    value: u64
}

struct ProductId {
    value: u64
}
```

Dù layout giống:

```text
u64
```

nhưng:

```text
UserId != ProductId
```

Đây là **nominal typing** cho user-defined types.

---

# 3. Nominal vs Structural

Axiom nên sử dụng mô hình kết hợp:

### Nominal

Dùng cho:

```text
struct
enum
trait
type declarations
```

### Structural

Có thể dùng trong một số compiler-internal constructs:

```text
tuple
function type
array type
view type
generic specialization
```

Ví dụ:

```text
(i32, f32)
```

không cần một declaration riêng.

---

# 4. Primitive Types

Core v0.1:

```text
bool

i8
i16
i32
i64

u8
u16
u32
u64

isize
usize

f32
f64

unit
never
```

Mở rộng compiler infrastructure:

```text
i128
u128
```

được hỗ trợ sớm nếu backend cho phép, nhưng không cần làm tăng surface syntax.

---

# 5. Primitive Type không có Subtyping

Không có:

```text
i32 <: i64
```

theo nghĩa subtype.

Nếu:

```text
let x: i64 = 10;
```

compiler có thể suy literal `10` thành `i64`.

Nhưng:

```text
let a: i32 = 10;
let b: i64 = a;
```

cần conversion rõ ràng.

---

# 6. Numeric Conversion

Không dùng implicit conversion kiểu C:

```text
u32 → i64
f32 → f64
```

một cách tùy tiện.

Axiom phân biệt:

```text
safe widening
explicit conversion
checked conversion
saturating conversion
wrapping conversion
bit reinterpretation
```

Ví dụ conceptual:

```text
x as i64
x.checked_as<i64>()
x.saturating_as<i64>()
x.wrapping_as<i64>()
```

Tên API cuối cùng có thể điều chỉnh, nhưng semantics phải tách biệt.

---

# 7. Integer Overflow

Không để integer overflow phụ thuộc:

```text
optimization level
CPU accident
compiler version
```

Core cần semantics rõ:

```text
checked
wrapping
saturating
```

Ví dụ:

```text
checked_add
wrapping_add
saturating_add
```

Trong arithmetic thông thường, compiler profile có thể chọn trap/check phù hợp nhưng **không được tạo C-style undefined behavior**.

---

# 8. Literal Inference

Ví dụ:

```text
let x = 10;
```

`10` chưa nhất thiết phải cố định `i32` ngay lập tức.

Compiler có thể tạo:

```text
IntegerLiteralType
```

sau đó constraint:

```text
x : ?
```

được resolve theo context.

Ví dụ:

```text
let x: u64 = 10;
```

thì literal trở thành `u64`.

---

# 9. Float Literal

Tương tự:

```text
let x = 1.5;
```

có type inference.

Context:

```text
let x: f32 = 1.5;
```

→ `f32`.

Nếu không có context, default type phải deterministic.

Đề xuất:

```text
integer literal → i32
float literal → f64
```

trừ khi compiler có contextual inference.

---

# 10. Bool

`bool` chỉ có:

```text
true
false
```

Không:

```text
0 → false
1 → true
```

implicit.

Không:

```text
pointer → bool
```

trong safe code.

---

# 11. Unit

Function không trả dữ liệu:

```text
fn log(x: Text) {
    ...
}
```

có return type:

```text
unit
```

`unit` là một type thực.

Có một giá trị:

```text
()
```

---

# 12. Never

Function không bao giờ return:

```text
fn panic() -> never
```

`never` có thể coerce vào context cần một type cụ thể:

```text
let x: i32 = if cond {
    10
} else {
    panic()
};
```

Không phải subtype thông thường; đây là **diverging expression rule**.

---

# 13. Tuple

Axiom hỗ trợ tuple:

```text
let p = (10, 20.0);
```

type:

```text
(i32, f64)
```

Tuple là value type.

Có thể:

```text
p.0
p.1
```

Layout mặc định compiler-controlled.

---

# 14. Fixed Array

```text
let a: [i32; 4]
```

là inline value.

Semantics:

```text
length = compile-time constant
```

Không phải dynamic array.

Type identity:

```text
[i32; 4] != [i32; 8]
```

---

# 15. Slice/View

Dynamic sequence access nên dùng view:

```text
view<T>
mut_view<T>
```

Ví dụ:

```text
fn sum(xs: view<i32>) -> i32
```

không ownership.

Đây là type-level capability đã định nghĩa trong memory model.

---

# 16. String Types

Axiom không nên có một `String` mơ hồ.

Ít nhất:

```text
Bytes
Text
```

`Bytes`:

```text
u8 sequence
```

`Text`:

```text
valid Unicode text
```

Compiler không được giả định:

```text
1 byte = 1 character
```

---

# 17. Unicode Validity

Nếu `Text` invariant là valid Unicode:

```text
Text
```

phải luôn giữ invariant đó trong safe code.

Raw bytes:

```text
Bytes
```

có thể chứa bất kỳ byte sequence nào.

Conversion:

```text
Bytes → Text
```

có thể fallible.

---

# 18. Option

Không có `null`.

Thay vào đó:

```text
Option<T>
```

conceptually:

```text
enum Option<T> {
    Some(T)
    None
}
```

Compiler có thể optimize representation:

```text
Option<&T>
```

hoặc handle types bằng niche optimization khi semantics cho phép.

Nhưng optimization không thay đổi semantic model.

---

# 19. Result

Recoverable failure:

```text
Result<T, E>
```

conceptually:

```text
enum Result<T, E> {
    Ok(T)
    Err(E)
}
```

Không cần exception runtime.

Compiler có thể optimize Result như register pair/tag/value tùy target.

---

# 20. Enum là Algebraic Data Type

Ví dụ:

```text
enum Shape {
    Circle(f32)
    Rectangle(f32, f32)
    Point
}
```

type system hiểu:

```text
Shape =
    Circle(f32)
  | Rectangle(f32,f32)
  | Point
```

`match` phải exhaustive.

---

# 21. Exhaustiveness

Ví dụ:

```text
match shape {
    Shape::Point => ...
    Shape::Circle(r) => ...
    Shape::Rectangle(w, h) => ...
}
```

đủ case.

Thiếu:

```text
Rectangle
```

→ compile error.

Compiler có thể dùng decision tree tối ưu khi codegen.

---

# 22. Pattern Type Checking

Pattern không chỉ là syntax.

Compiler kiểm tra:

```text
variant
field count
field types
binding types
guards
exhaustiveness
unreachable patterns
```

Ví dụ:

```text
Some(x)
```

suy ra:

```text
x : T
```

nếu input:

```text
Option<T>
```

---

# 23. Struct Types

Struct là nominal product type:

```text
struct Vec3 {
    x: f32
    y: f32
    z: f32
}
```

Type identity:

```text
StructId
```

Field identity:

```text
FieldId
```

không dựa trên field name đơn thuần.

---

# 24. Layout ≠ Type Identity

Hai struct:

```text
struct A {
    x: u64
    y: u32
}
```

và:

```text
struct B {
    x: u64
    y: u32
}
```

không phải cùng type dù layout giống.

Điều này giúp:

- type safety
- FFI
- ABI
- domain modeling.

---

# 25. Type Alias

Cho phép:

```text
type UserId = u64;
```

nhưng alias không tạo nominal type mới.

Do đó:

```text
UserId == u64
```

semantic identity.

Nếu muốn type mới:

```text
struct UserId {
    value: u64
}
```

---

# 26. Newtype

Newtype là công cụ type safety:

```text
struct UserId(u64)
struct ProductId(u64)
```

Compiler không tự convert.

Có thể cung cấp method:

```text
fn value(self: UserId) -> u64
```

---

# 27. Function Types

Function type:

```text
fn(i32, i32) -> i32
```

là type.

Closure có function-like type riêng:

```text
closure(...)
```

Compiler có thể lower closure thành anonymous struct + function pointer/state machine tùy capture.

---

# 28. Function Type không bao gồm Calling Convention mặc định

Semantic type:

```text
fn(i32) -> i32
```

khác với ABI metadata:

```text
extern("C") fn(i32) -> i32
```

Calling convention phải là một thuộc tính type/ABI khi cần.

---

# 29. Generic Types

Axiom hỗ trợ:

```text
struct Vec<T> {
    data: Buffer<T>
}
```

`T` là type parameter.

Type identity:

```text
Vec<i32>
Vec<f32>
```

là hai specialization semantic khác nhau.

---

# 30. Generic Constraints

Không dùng một hệ thống constraint thứ hai.

Traits là constraint mechanism:

```text
fn sort<T: Comparable>(xs: mut_view<T>)
```

hoặc syntax tương đương.

Compiler phải resolve:

```text
T
 ↓
Comparable<T>
 ↓
implementation
```

---

# 31. Generic Inference

Không bắt programmer viết:

```text
sort<i32>(xs)
```

nếu compiler có thể suy ra.

```text
sort(xs)
```

→ từ `xs: mut_view<i32>`:

```text
T = i32
```

Nhưng nếu ambiguity:

```text
cannot infer T
```

compiler phải báo rõ.

---

# 32. Generic Monomorphization

Axiom ưu tiên static specialization:

```text
sort<i32>
sort<f64>
```

có thể generate machine code riêng.

Ưu điểm:

- optimization
- inlining
- specialization
- no runtime generic dispatch.

Compiler có thể deduplicate identical generated representations khi an toàn.

---

# 33. Generic Code Sharing

Không phải generic nào cũng cần duplicate machine code.

Nếu:

```text
T
```

chỉ được sử dụng trong representation-independent context, compiler có thể share code.

Nhưng semantics vẫn là:

```text
generic type/function
```

không phải dynamic dispatch.

---

# 34. Traits

Trait:

```text
trait Add {
    fn add(self, other: Self) -> Self;
}
```

là behavior contract.

Không phải class.

Không tự tạo object header.

---

# 35. Trait Implementation

```text
impl Add for Vec3 {
    fn add(self, other: Vec3) -> Vec3 {
        ...
    }
}
```

Compiler tạo:

```text
ImplId
```

gắn:

```text
TraitId
TypeId
```

---

# 36. Coherence

Axiom phải có quy tắc rõ để tránh:

```text
trait T
type A
```

có nhiều impl mâu thuẫn.

Đề xuất:

> Một `(Trait, Type)` pair chỉ có tối đa một implementation hợp lệ trong semantic universe.

Ví dụ:

```text
impl Display for User
```

không thể xuất hiện hai lần trong cùng dependency graph.

---

# 37. Orphan Rule

Để giữ coherence:

```text
impl Trait for Type
```

ít nhất một trong hai phải thuộc package hiện tại:

```text
Trait local
hoặc
Type local
```

Nếu cả hai đều foreign:

```text
impl ForeignTrait for ForeignType
```

→ reject.

Có thể có cơ chế explicit extension riêng cho behavior không tạo trait impl.

---

# 38. Trait Default Method

Ví dụ:

```text
trait Printable {
    fn print(self) {
        ...
    }
}
```

Concrete impl có thể override:

```text
impl Printable for User {
    fn print(self) {
        ...
    }
}
```

Không cần:

```text
override
```

vì compiler biết declaration đang satisfy trait member.

---

# 39. Trait Static Dispatch

Mặc định:

```text
fn render<T: Renderable>(x: T)
```

được static dispatch.

Không có vtable bắt buộc.

Đây là đường đi chính để đạt zero-cost abstraction.

---

# 40. Dynamic Trait

Chỉ khi programmer yêu cầu:

```text
dyn Renderable
```

compiler mới tạo dynamic dispatch representation.

Conceptually:

```text
data pointer
vtable pointer
```

nhưng representation cụ thể vẫn thuộc ABI.

---

# 41. Trait Object không phải Object Base Class

Không có:

```text
Object
```

base class.

`dyn Trait` chỉ là:

> runtime representation cho một trait contract được chọn dynamic dispatch.

---

# 42. Associated Types

Trait:

```text
trait Iterator {
    type Item;

    fn next(self) -> Option<Self::Item>;
}
```

Associated type được resolve theo:

```text
ImplId + AssociatedTypeId
```

Ví dụ:

```text
Iterator::Item
```

không phải global type.

---

# 43. Associated Constants

Có thể:

```text
trait Numeric {
    const ZERO: Self;
}
```

Compiler xử lý tương tự associated item.

---

# 44. Trait Bounds

Ví dụ:

```text
fn max<T: Ord>(a: T, b: T) -> T
```

constraint graph:

```text
T
 ↓
Ord(T)
```

Resolver/type checker phải chứng minh tồn tại implementation.

---

# 45. Where Constraints

Khi constraint phức tạp:

```text
fn foo<T, U>(x: T)
where
    T: Convert<U>,
    U: Numeric
```

Compiler tạo constraint graph:

```text
T ──Convert──▶ U
U ──Numeric──▶ true
```

Không dùng textual matching.

---

# 46. Associated Type Equality

Compiler cần hỗ trợ constraint:

```text
T::Item = U
```

ở mức type relation.

Điều này cần thiết cho:

- iterator
- serialization
- tensor
- async
- generic algorithms.

---

# 47. Type Inference Engine

Đề xuất constraint-based inference:

```text
expression
 ↓
type variables
 ↓
constraints
 ↓
unification
 ↓
trait solving
 ↓
resolved types
```

Ví dụ:

```text
let x = foo(10);
```

Compiler tạo:

```text
T1 = type(foo result)
T2 = type(10)
```

sau đó giải constraint.

---

# 48. Unification

Nếu:

```text
T1 = T2
```

compiler unify.

Nếu:

```text
Vec<T1> = Vec<i32>
```

suy:

```text
T1 = i32
```

Nếu:

```text
Vec<T1> = Option<i32>
```

→ type mismatch.

---

# 49. Occurs Check

Inference phải ngăn type vô hạn:

```text
T = Vec<T>
```

trừ khi language có explicit recursive type mechanism.

Compiler phải detect:

```text
infinite type
```

thay vì loop vô hạn.

---

# 50. Type Inference Boundary

Không nên inference vô hạn xuyên toàn program.

Inference tốt nhất theo:

```text
expression
statement
function body
```

Public API nên có type signature xác định.

Ví dụ:

```text
pub fn foo(x) = ...
```

có thể được compiler infer nội bộ, nhưng interface artifact phải materialize đầy đủ type.

---

# 51. Public Generic API

Interface artifact phải chứa:

```text
generic parameters
bounds
associated types
effects
capabilities
ABI-relevant information
```

Không được chỉ ghi:

```text
foo(...)
```

---

# 52. Type Normalization

Compiler cần canonicalize:

```text
type aliases
generic substitutions
associated types
const generic values
```

để:

```text
Vec<Alias>
```

có thể normalize về:

```text
Vec<RealType>
```

khi cần so sánh.

---

# 53. Type Equality

Có nhiều loại equality:

```text
Definitional Equality
Semantic Equality
Representation Equality
ABI Equality
```

Ví dụ:

```text
type A = u64
```

thì:

```text
A
```

definitional equal `u64`.

Nhưng:

```text
struct B(u64)
```

representation có thể giống `u64`, semantic type khác.

---

# 54. Type Layout Query

Compiler cung cấp:

```text
size_of<T>()
align_of<T>()
```

ở comptime.

Và:

```text
offset_of<T, field>()
```

nếu layout được phép quan sát.

Nếu struct layout compiler-controlled:

```text
offset
```

chỉ ổn định khi representation contract yêu cầu.

---

# 55. Layout Attributes

FFI hoặc serialization có thể yêu cầu:

```text
@repr(C)
@repr(packed)
@repr(transparent)
```

Các attribute này phải được compiler hiểu.

Không cho package tự định nghĩa semantics của:

```text
@repr(...)
```

nếu không có compiler extension contract.

---

# 56. Transparent Representation

Newtype:

```text
struct UserId(u64)
```

có thể yêu cầu:

```text
@repr(transparent)
```

để ABI tương thích với:

```text
u64
```

nhưng chỉ khi compiler chứng minh representation contract.

---

# 57. Type Capability Separation

Ví dụ:

```text
view<T>
mut_view<T>
Box<T>
Arc<T>
```

không chỉ là generic wrappers.

Type system phải biết các semantic markers:

```text
ownership
copyability
drop
capability
storage
```

Nhưng chúng không được biến thành subtype hierarchy.

---

# 58. Copy

Một type có thể implement:

```text
Copy
```

nếu semantics cho phép.

Compiler phải kiểm tra:

```text
no Drop obligation
no unique ownership invariant broken by copy
```

Copyability là semantic trait/property.

---

# 59. Move

Type checker đánh dấu:

```text
value state
```

nhưng ownership analysis ở phase sau mới kiểm tra flow đầy đủ.

Type system chỉ cần biết:

```text
T is movable
T is copyable
T has drop obligation
```

---

# 60. Type + Effect

Function type không chỉ:

```text
(args) -> result
```

mà semantic metadata có thể gồm:

```text
effects
capabilities
async
unsafe
```

Ví dụ:

```text
fn read() -> Result<Bytes, IOError>
```

có thể có:

```text
Effect: Filesystem.Read
Capability: Filesystem
```

Nhưng effect system được resolve ở phase riêng, không nhồi tất cả vào nominal TypeId.

---

# 61. Type + Async

```text
async fn foo() -> i32
```

không đơn giản là:

```text
fn() -> i32
```

Semantic function declaration có:

```text
Async = true
Return = i32
```

và lowering sau đó tạo Future/Task representation.

---

# 62. Type + GPU

```text
@kernel fn add(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
)
```

type system kiểm tra type compatibility.

GPU legality nằm ở:

```text
KernelCapabilityAnalysis
```

không phải tạo một type system thứ hai.

---

# 63. Type + Address Space

GPU:

```text
DeviceView<T>
```

có storage/address-space metadata.

Không cho:

```text
HostView<T>
```

tự động trở thành:

```text
DeviceView<T>
```

nếu transfer không xảy ra.

---

# 64. Type Cast vs Reinterpret

Phải phân biệt:

```text
numeric conversion
```

với:

```text
bit reinterpretation
```

Ví dụ:

```text
f32 → i32
```

có thể là numeric conversion.

Trong khi:

```text
reinterpret_bits<f32, i32>
```

giữ nguyên bit pattern.

Đây là hai semantics hoàn toàn khác nhau.

---

# 65. Generic Constants

Axiom có thể hỗ trợ const generic:

```text
struct Matrix<T, const N: usize> {
    data: [T; N]
}
```

Compiler identity:

```text
Matrix<f32, 4>
Matrix<f32, 8>
```

khác nhau.

Const value phải được compile-time evaluate.

---

# 66. Shape Types

Về sau tensor:

```text
Tensor<f32, [M, N]>
```

có thể dùng const/type-level values.

Không cần tạo một type-system thứ hai cho tensor.

Tensor shape constraints đi qua generic/const constraint engine.

---

# 67. Type-Level Computation

Không nên biến Axiom thành dependently typed language đầy đủ.

Core chỉ cần:

```text
compile-time constants
generic parameters
const expressions
associated types
trait constraints
```

đủ mạnh để xây:

- tensor
- SIMD
- units
- arrays
- embedded abstractions.

---

# 68. Recursive Types

Recursive type phải có indirection/storage boundary.

Ví dụ:

```text
struct Node {
    next: Box<Node>
}
```

hợp lệ.

Nhưng:

```text
struct Node {
    next: Node
}
```

→ infinite size.

Compiler diagnostic phải nói rõ:

```text
recursive type has infinite size
```

---

# 69. Sizedness

Compiler cần internal concept:

```text
Sized
Unsized
```

Không nhất thiết expose quá nhiều syntax.

Các type như:

```text
[T; N]
struct
tuple
enum
```

thường statically sized.

Một số dynamic/view types có representation đặc biệt.

---

# 70. Type Erasure

Type erasure chỉ xảy ra explicit:

```text
dyn Trait
```

hoặc compiler-internal optimization.

Không implicit:

```text
Any
Object
boxed universal value
```

trong Core.

---

# 71. `Any`

Không đưa:

```text
Any
```

vào Core.

Nếu cần runtime heterogeneous storage:

```text
DynamicValue
```

là library/runtime abstraction.

Điều này giữ Core deterministic và tránh runtime type metadata bắt buộc.

---

# 72. Null

Không có:

```text
null
nil
nullptr
```

trong safe Core.

Pointer null chỉ tồn tại trong:

```text
unsafe
FFI
raw pointer
```

---

# 73. Variance

Compiler cần xác định variance cho generic type nội bộ:

```text
Covariant
Contravariant
Invariant
```

Đặc biệt quan trọng cho:

```text
view<T>
mut_view<T>
dyn Trait
function types
```

Không cần bắt programmer khai báo variance trong v0.1 nếu compiler có thể suy ra.

---

# 74. Type Compatibility Algorithm

Khi compiler kiểm tra:

```text
expected: T
actual: U
```

thứ tự:

```text
1. exact type equality
2. type alias normalization
3. inference variable unification
4. allowed language conversion
5. generic constraint
6. trait-based conversion nếu explicit
7. reject
```

Không tự động thử hàng chục conversion mơ hồ.

---

# 75. No Implicit User Conversion

Nếu user định nghĩa:

```text
impl Convert<User> for Account
```

compiler không tự động chèn conversion mọi nơi.

Phải có syntax/API rõ ràng:

```text
account.to_user()
```

hoặc conversion protocol compiler-defined.

Điều này tránh hidden work và ambiguity.

---

# 76. Type Inference Diagnostics

Thay vì:

```text
type mismatch
```

compiler nên nói:

```text
expected: Vec<i32>
found: Vec<f32>

because:
    parameter `x` requires T = i32
    argument expression inferred T = f32
```

405/407 cho phép IDE/AI truy vấn chính dependency chain này.

---

# 77. Type Query API

CompilerDB expose:

```text
type_of(ExpressionId)
type_of(SymbolId)
normalize(TypeId)
layout_of(TypeId)
implements(TypeId, TraitId)
associated_type(...)
generic_constraints(...)
conversion_candidates(...)
```

AI/IDE sử dụng cùng query.

---

# 78. Type IR

Đề xuất **ATYPE** làm canonical type representation:

```text
Primitive
Tuple
Array
Struct
Enum
Function
Closure
GenericParam
GenericApply
TraitObject
View
MutView
Box
Reference/RawPointer
TypeAlias
AssociatedType
Never
Unit
ConstDependent
```

`ATYPE` không phải source syntax.

Nó là semantic canonical form.

---

# 79. Type Interning

CompilerDB nên intern type nodes.

Ví dụ:

```text
i32
```

chỉ có một canonical:

```text
TypeId(i32)
```

Trong một semantic universe.

Tương tự:

```text
Vec<i32>
```

được intern.

Điều này làm:

```text
Type equality
```

gần như:

```text
TypeId == TypeId
```

sau canonicalization.

---

# 80. Type Cache

Query:

```text
type_of(expr)
```

có thể cache.

Khi declaration không đổi:

```text
TypeId
```

được reuse.

Đây là một trong những lợi ích lớn nhất của CompilerDB.

---

# 81. Type Solver Architecture

```text
Expression
   ↓
Constraint Generation
   ↓
Constraint Graph
   ↓
Unification
   ↓
Generic Substitution
   ↓
Trait Solver
   ↓
Associated Type Normalization
   ↓
Type Normalization
   ↓
Resolved Type
```

Trait solver phải là một subsystem riêng nhưng dùng chung ATYPE.

---

# 82. Không để Trait Solver thành Prolog tùy tiện

Trait system phải có termination strategy.

Compiler không được phép:

```text
trait A<T>: B<T>
trait B<T>: A<T>
```

làm solver chạy vô hạn.

Phải có:

```text
cycle detection
depth/complexity control
canonical goals
memoization
```

---

# 83. Type Error Recovery

Nếu:

```text
foo(unknown)
```

không resolve được type, compiler tạo:

```text
ErrorType
```

thay vì phá toàn bộ inference graph.

Nhưng:

```text
ErrorType
```

không được coi là một type hợp lệ để codegen.

---

# 84. Type Error ≠ Compiler Error

Phải phân biệt:

```text
TypeError
InferenceFailure
TraitFailure
Ambiguity
CompilerBug
```

CompilerDB lưu provenance riêng.

---

# 85. Type Proof

Mỗi resolved expression có thể có:

```text
TypeProof
```

Ví dụ:

```text
foo(x)
```

proof:

```text
x : i32
foo : fn(i32) -> f64
therefore foo(x) : f64
```

Proof tree có thể được nén.

---

# 86. Bộ invariant ATYPE

Đóng băng 30 invariant:

### ATYPE-01
Mọi semantic type phải có TypeId.

### ATYPE-02
TypeId phải canonical trong semantic universe.

### ATYPE-03
Type identity không phụ thuộc source spelling.

### ATYPE-04
Nominal user types phải giữ identity riêng.

### ATYPE-05
Structural compiler types phải có canonical representation.

### ATYPE-06
Type alias không tạo nominal identity mới.

### ATYPE-07
Newtype tạo nominal identity mới.

### ATYPE-08
Primitive types phải có semantics deterministic.

### ATYPE-09
Implicit numeric narrowing không được phép.

### ATYPE-10
Numeric conversion phải có semantics xác định.

### ATYPE-11
Bit reinterpretation phải khác numeric conversion.

### ATYPE-12
Integer overflow semantics không phụ thuộc optimization level.

### ATYPE-13
`null` không tồn tại trong safe Core.

### ATYPE-14
`Option<T>` là cơ chế biểu diễn absence trong safe Core.

### ATYPE-15
`Result<T,E>` là cơ chế recoverable failure chuẩn.

### ATYPE-16
Enum pattern matching phải exhaustive khi semantics yêu cầu.

### ATYPE-17
Recursive type phải có finite representation.

### ATYPE-18
Generic identity phải bao gồm type arguments.

### ATYPE-19
Const-generic identity phải bao gồm const arguments.

### ATYPE-20
Generic inference phải deterministic.

### ATYPE-21
Inference phải có occurs-check.

### ATYPE-22
Public APIs phải có fully resolved interface types.

### ATYPE-23
Trait implementation phải coherent.

### ATYPE-24
Orphan implementation phải bị giới hạn.

### ATYPE-25
Static trait dispatch là mặc định.

### ATYPE-26
Dynamic dispatch chỉ xuất hiện khi semantics yêu cầu.

### ATYPE-27
Trait object không được yêu cầu object header cho mọi type.

### ATYPE-28
Type errors phải có provenance đủ để giải thích.

### ATYPE-29
Type solver không được phụ thuộc text substitution.

### ATYPE-30
Type System không được tự ý thay đổi ownership, capability hoặc ABI semantics; nó chỉ cung cấp type facts cho các subsystem tương ứng.

---

# 87. Kiến trúc sau BOOTSTRAP-409

Axiom compiler hiện có một semantic chain rõ ràng:

```text
Source
  │
  ▼
Lexer / Parser
  │
  ▼
Module / Scope / Symbol Resolution
  │
  ▼
Resolved HIR
  │
  ▼
ATYPE
  │
  ├── Type Inference
  ├── Generic Resolution
  ├── Trait Solver
  ├── Associated Type Resolution
  └── Type Normalization
  │
  ▼
Typed HIR
  │
  ▼
Ownership / Capability / Effect
  │
  ▼
MIR
```

Và trong CompilerDB:

```text
                 CompilerDB
                     │
        ┌────────────┼────────────┐
        ▼            ▼            ▼
    SymbolDB      TypeDB       TraitDB
        │            │            │
        └────────────┼────────────┘
                     ▼
                 Typed HIR
                     │
                     ▼
                  MIR DB
```

Điểm quan trọng nhất của 409 là Axiom **không cần lựa chọn giữa "type system đơn giản" và "type system mạnh"**. Nó có thể có type system khá mạnh ở bên trong compiler, nhưng giấu phần lớn complexity khỏi programmer thông qua inference, canonicalization và compiler diagnostics.

**BOOTSTRAP-409 — SPECIFIED / FROZEN**.