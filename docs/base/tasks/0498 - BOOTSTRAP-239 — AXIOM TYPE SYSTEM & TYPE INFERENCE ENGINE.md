# BOOTSTRAP-239 — AXIOM TYPE SYSTEM & TYPE INFERENCE ENGINE

**TRẠNG THÁI: FROZEN / COMPLETED**

Đây là một trong những tầng quan trọng nhất của Axiom. Mục tiêu không phải tạo ra type system “càng phức tạp càng tốt”, mà là:

> **Type system đủ mạnh để compiler chứng minh chương trình đúng, nhưng programmer chỉ phải viết lượng type information cần thiết.**

Và giữ nguyên triết lý đã thống nhất:

> **Compiler Complexity Is Not Language Complexity.**

---

# 1. Vai trò của Type System

Pipeline:

```text
AST
 ↓
Name Resolution
 ↓
Resolved AST
 ↓
Type Inference
 ↓
Typed HIR
 ↓
Trait Resolution
 ↓
Ownership / Capability Verification
 ↓
MIR
```

Type system chịu trách nhiệm trả lời:

```text
"Expression này có type gì?"
"Declaration này có type gì?"
"Type A có tương thích với type B không?"
"Generic T có thể là type nào?"
"Operation này có hợp lệ không?"
```

Không chịu trách nhiệm trực tiếp về:

```text
ownership lifetime
drop
alias safety
thread synchronization
machine representation
```

nhưng cung cấp facts cho các tầng đó.

---

# 2. Type identity

Axiom dùng **semantic type identity**, không dùng structural byte layout để xác định type.

Ví dụ:

```axiom
struct UserId(u64)
struct ProductId(u64)
```

Hai type:

```text
UserId ≠ ProductId
```

dù:

```text
size_of(UserId) == size_of(ProductId) == 8
```

Đây là **nominal typing**.

---

# 3. Type categories

TypeDB phải hỗ trợ tối thiểu:

```text
PrimitiveType
StructType
EnumType
TupleType
ArrayType
Slice/ViewType
FunctionType
ClosureType
TypeParameter
AssociatedType
GenericInstance
DynTraitType
NeverType
UnitType
```

và system-level:

```text
RawPointerType
```

---

# 4. Primitive types

Core:

```text
bool

i8  i16  i32  i64
u8  u16  u32  u64

isize
usize

f32
f64
```

Compiler phải coi chúng là semantic types thực sự:

```text
TypeId(I32)
TypeId(U64)
...
```

không phải các string đặc biệt rải rác trong compiler.

---

# 5. Unit

```text
()
```

hoặc syntax canonical tương ứng.

Semantic:

```text
Unit
```

Có đúng một giá trị.

Ví dụ:

```axiom
fn log(x: i32) -> () {
    ...
}
```

---

# 6. Never

```text
never
```

hoặc syntax canonical đã được chốt trong grammar.

Ví dụ:

```axiom
fn abort() -> never {
    panic()
}
```

Never có thể coerce vào mọi expected type vì expression không bao giờ tạo ra value.

```text
never → T
```

là **diverging coercion**, không phải ordinary subtype hierarchy.

---

# 7. Không có universal `Any`

Axiom Core không có:

```text
Any
Object
DynamicObject
null
```

Điều này tránh một escape hatch làm suy yếu static typing.

Khi thực sự cần runtime polymorphism:

```text
dyn Trait
```

được dùng rõ ràng.

---

# 8. Struct type

```axiom
struct Point {
    x: f32
    y: f32
}
```

tạo:

```text
StructType {
    DeclarationId
    Fields
    GenericParameters
    Attributes
}
```

Type identity lấy từ declaration identity.

---

# 9. Generic struct

```axiom
struct Box<T> {
    value: T
}
```

`Box<i32>` và `Box<f32>` là hai **type instances** khác nhau:

```text
GenericInstance(Box, [i32])
GenericInstance(Box, [f32])
```

nhưng cùng generic definition.

---

# 10. Type interning

`TypeDB` phải canonicalize types.

Nếu compiler gặp:

```text
Vec<i32>
```

1000 lần, không tạo 1000 type objects độc lập.

```text
TypeId(Vec<i32>)
```

được intern.

Invariant:

```text
same canonical semantic type
→ same TypeId
```

---

# 11. Type canonicalization

Ví dụ:

```text
type A = B
```

Alias không tạo semantic type mới.

Do đó:

```text
A
B
```

resolve tới cùng underlying type identity.

Ngược lại:

```axiom
struct A(B)
```

là newtype:

```text
A ≠ B
```

---

# 12. Type alias

```axiom
type UserId = u64
```

là alias.

```text
UserId
```

về semantic typing tương đương:

```text
u64
```

Alias chủ yếu giúp readability/API organization.

---

# 13. Newtype

```axiom
struct UserId(u64)
```

là nominal type mới.

```text
UserId ≠ u64
```

Compiler không implicit convert.

Phải dùng constructor/accessor/cast được định nghĩa.

---

# 14. Tuple

```axiom
(i32, f32, bool)
```

là structural type.

Hai tuple cùng thứ tự type:

```text
(i32, f32)
==
(i32, f32)
```

không cần declaration identity.

---

# 15. Array

Syntax:

```axiom
[4]i32
```

Type gồm:

```text
ArrayType {
    element: i32
    length: 4
}
```

Do đó:

```text
[4]i32 ≠ [8]i32
```

---

# 16. Array length là compile-time value

```axiom
fn sum<const N: usize>(a: [N]i32) -> i32
```

`N` là const generic parameter.

Type identity phụ thuộc vào giá trị:

```text
[N=4]
[N=8]
```

là hai instances khác nhau.

---

# 17. `view<T>`

`view<T>` là capability-bearing semantic type.

```text
view<i32>
```

không phải owner.

Nó chứa semantic information:

```text
element type
read capability
provenance
region
validity
```

Representation có thể chỉ là pointer + length hoặc tối ưu hoàn toàn.

Nhưng type system không được đồng nhất nó với raw pointer.

---

# 18. `mut_view<T>`

```text
mut_view<T>
```

là mutable/exclusive capability.

Type system ghi nhận:

```text
READ + WRITE capability
```

Ownership verifier mới kiểm tra:

```text
exclusive
non-overlap
lifetime
```

Do đó:

```text
Type System
    → mut_view<T> là loại access capability

Capability Verifier
    → capability đó có hợp lệ tại điểm này không
```

---

# 19. Raw pointer

```text
*const T
*mut T
```

là system/unsafe types.

Khác hoàn toàn:

```text
view<T>
mut_view<T>
```

Raw pointer không tự mang safe provenance.

---

# 20. Function type

Ví dụ:

```text
fn(i32, i32) -> i32
```

là type.

Function type semantic gồm:

```text
parameter types
return type
calling/effect information
```

---

# 21. Effects thuộc callable type

Một callable có thể có semantic effects:

```text
Read
Write
Allocate
IO
Panic
Atomic
Synchronize
Foreign
...
```

Do đó type system phải có:

```text
FunctionSignature
EffectSet
```

tách khỏi representation.

---

# 22. Effect polymorphism

Axiom không nên bắt programmer viết effect annotations cho mọi function.

Ví dụ:

```axiom
fn add(a: i32, b: i32) -> i32
```

compiler tự suy ra effect:

```text
Pure
```

Một function đọc file:

```text
Effect = IO + Resource
```

Compiler tính effect từ body và callees.

Annotation chỉ cần khi muốn tạo contract đặc biệt.

---

# 23. Closure type

```axiom
let offset = 10
let f = |x| x + offset
```

Closure có anonymous compiler-generated type:

```text
ClosureType#123
```

không cần programmer đặt tên.

Type chứa:

```text
parameters
return type
capture environment
call traits
effects
```

---

# 24. Closure ≠ function pointer

Capturing closure:

```text
|x| x + offset
```

khác:

```text
fn(i32) -> i32
```

Function pointer không có capture environment.

Non-capturing closure có thể được compiler chuyển thành function pointer nếu semantics cho phép.

---

# 25. Type parameter

```axiom
fn identity<T>(x: T) -> T {
    x
}
```

`T` là:

```text
TypeParameterId
```

Không phải type runtime.

Trong generic body:

```text
T
```

là symbolic type variable.

---

# 26. Generic bounds

```axiom
fn max<T: Ord>(a: T, b: T) -> T
```

Type checker ghi:

```text
T : Ord
```

Trait solver chịu trách nhiệm chứng minh constraint.

Type system không tự implement trait logic.

---

# 27. `Self`

Trong:

```axiom
trait Add {
    fn add(self: Self, other: Self) -> Self
}
```

`Self` là special type parameter.

```text
SelfType(TraitContext)
```

Trong:

```axiom
impl Add for Vec2
```

`Self = Vec2`.

---

# 28. Associated types

```axiom
trait Iterator {
    type Item

    fn next(self: mut_view<Self>) -> Option<Self::Item>
}
```

`Self::Item` là:

```text
AssociatedTypeRef
```

chưa nhất thiết biết concrete type trong generic context.

Trait solver/type normalization giải quyết sau.

---

# 29. Type normalization

Ví dụ:

```text
<T as Iterator>::Item
```

có thể normalize thành:

```text
i32
```

nếu compiler đã chứng minh:

```text
impl Iterator for Foo {
    type Item = i32
}
```

Type checker cần canonical normalization query:

```text
normalize(Type)
```

---

# 30. Type equality

Axiom phân biệt:

```text
Definitional equality
Semantic equality
Representation equality
```

Ví dụ:

```text
type A = B
```

→ semantic same type.

Nhưng:

```text
struct A(B)
```

→ semantic different type dù representation có thể identical.

---

# 31. Representation equality không tạo type equality

Nếu:

```text
size_of(A) == size_of(B)
align_of(A) == align_of(B)
```

thì:

```text
A ≠ B
```

trừ explicit conversion.

Điều này cực kỳ quan trọng cho optimization và FFI safety.

---

# 32. Generic type variables

Inference dùng:

```text
TypeVar
```

Ví dụ:

```axiom
let x = identity(42)
```

ban đầu:

```text
T = ?
```

Argument:

```text
42 : integer literal type
```

constraint:

```text
T ~ type_of(42)
```

Sau literal inference:

```text
T = i32
```

nếu context không yêu cầu type khác.

---

# 33. Unification

Core inference engine dùng unification.

Ví dụ:

```text
T
~
Vec<U>
```

gán:

```text
T := Vec<U>
```

Ví dụ:

```text
Vec<T>
~
Vec<i32>
```

suy ra:

```text
T := i32
```

---

# 34. Occurs check

Không cho:

```text
T = Vec<T>
```

nếu tạo recursive infinite type.

Compiler:

```text
OccursCheck(T, Vec<T>) → failure
```

Diagnostic phải giải thích cycle.

---

# 35. Constraint representation

Inference không nên chỉ mutate type variables.

Dùng constraint graph:

```text
TypeVariable
Constraint
    ↓
Unification
    ↓
Normalization
    ↓
Trait constraints
    ↓
Solved Type
```

Điều này rất phù hợp incremental compilation.

---

# 36. Expected-type propagation

Ví dụ:

```axiom
let x: f64 = 10
```

Expected type:

```text
f64
```

được truyền vào literal.

Do đó:

```text
10 → f64
```

không mặc định i32 trước rồi mới cast.

---

# 37. Bidirectional inference

Axiom nên dùng mô hình:

```text
Infer
Check
```

thay vì inference một chiều.

Ví dụ:

```axiom
let x: Vec<f64> = make_vec(...)
```

Compiler **check** RHS against expected type.

Trong:

```axiom
let x = make_vec(...)
```

compiler **infer** type từ expression.

Đây là cân bằng tốt giữa usability và compiler determinism.

---

# 38. Function call inference

```axiom
max(a, b)
```

Pipeline:

```text
resolve max
 ↓
instantiate generic parameters
 ↓
create type variables
 ↓
infer argument types
 ↓
generate constraints
 ↓
solve constraints
 ↓
trait solve
 ↓
check return type
```

---

# 39. No arbitrary backtracking

Type inference không được thử hàng nghìn interpretation rồi chọn “có vẻ đúng”.

Nếu nhiều solution hợp lệ:

```text
Ambiguous
```

Compiler yêu cầu annotation/context.

Điều này giúp compile time predictable.

---

# 40. Numeric literals

Literal syntax ban đầu có symbolic type:

```text
IntegerLiteral
FloatLiteral
```

Ví dụ:

```axiom
let x = 10
```

Compiler phải áp dụng defaulting rule deterministic.

Khuyến nghị:

```text
integer literal default → i32
floating literal default → f64
```

trừ khi expected type hoặc constraint xác định type khác.

---

# 41. Không implicit numeric chain

Không cho:

```text
i32 → i64 → f64 → ...
```

tự động qua nhiều bước.

Ví dụ:

```axiom
let x: f64 = integer_value
```

chỉ hợp lệ nếu coercion rule trực tiếp cho phép hoặc programmer cast.

Không tạo chain:

```text
i32 → i64 → f64
```

---

# 42. Coercion

Coercion là conversion compiler-controlled, semantics-preserving hoặc explicitly safe.

Core:

```text
Owner → ephemeral view
Array → view
String → Str
never → T
```

Một số coercions khác có thể được thêm nhưng phải đóng whitelist.

---

# 43. Cast

```axiom
x as i64
```

là explicit cast.

Type checker kiểm tra primitive cast rules.

Không dùng `as` để bypass nominal type safety tùy tiện.

---

# 44. Bitcast

Bitcast là operation khác cast.

```text
BITCAST(A → B)
```

chỉ hợp lệ nếu:

```text
size compatible
alignment valid
representation valid
```

và semantic operation được đánh dấu appropriately.

---

# 45. `Option`

```text
Option<T>
```

là ordinary generic enum:

```text
enum Option<T> {
    Some(T)
    None
}
```

Không phải compiler magic nullable pointer.

Compiler có thể tối ưu niche representation.

---

# 46. `Result`

```text
Result<T, E>
```

ordinary generic enum.

`?` được type checker xử lý thông qua Result/Option propagation rules.

---

# 47. No null

Type system không có:

```text
null : arbitrary T
```

Do đó không tồn tại implicit nullability.

Nếu cần absence:

```text
Option<T>
```

---

# 48. `dyn Trait`

```text
dyn Display
```

là explicit dynamic trait type.

Semantically:

```text
DynTraitType {
    TraitId
    object_safe_contract
}
```

Representation có thể là:

```text
data pointer + vtable
```

nhưng đó là ABI detail.

---

# 49. `dyn Trait` không phải subtype

Axiom không xây type hierarchy:

```text
ConcreteType <: Trait
```

theo kiểu OO.

Thay vào đó:

```text
T implements Trait
```

là trait solver fact.

---

# 50. Trait object safety

Trước khi:

```text
dyn Trait
```

được phép, compiler kiểm tra object safety.

Ví dụ trait có generic method không object-safe theo rule tương ứng:

```text
dyn Trait
```

→ error nếu không thể tạo dynamic callable contract.

---

# 51. Trait bounds

```axiom
fn print<T: Display>(x: T)
```

tạo constraint:

```text
Implements(T, Display)
```

Trait solver giải quyết.

Nếu:

```text
Proven
```

tiếp tục.

Nếu:

```text
NotProven
```

diagnostic.

Nếu:

```text
Ambiguous
```

không được codegen.

---

# 52. Type facts

TypeDB phải expose compiler-known predicates:

```text
IsCopy<T>
IsDrop<T>
IsSend<T>
IsShare<T>
IsSized<T>
IsFfiSafe<T, ABI>
IsGpuLegal<T>
```

Nhưng đây là **facts**, không nhất thiết đều là ordinary user traits.

---

# 53. `Copy`

```text
Copy<T>
```

là semantic property.

Không đồng nghĩa:

```text
memcpy(T)
```

Compiler có thể copy bằng register, vector instruction, SSA value, v.v.

---

# 54. `Drop`

Nếu type có Drop obligation:

```text
Drop<T>
```

thì:

```text
!Copy<T>
```

được enforced.

Type system cung cấp fact; ownership verifier dùng nó để quyết định Move/Drop.

---

# 55. Send / Share

Compiler derive:

```text
Send<T>
Share<T>
```

từ cấu trúc type + component facts + explicit contracts.

Không cho programmer tùy ý viết:

```text
unsafe impl Send
```

để ép compiler tin một claim sai.

System boundary có trusted mechanisms riêng.

---

# 56. Sized

Generic parameter mặc định có thể yêu cầu:

```text
Sized
```

nếu cần compile-time known layout.

Các unsized/dynamic forms:

```text
dyn Trait
view<T>
```

có semantics riêng.

---

# 57. Type layout không thuộc Type Equality

Type checker hỏi:

```text
AreTypesEqual(A, B)?
```

Layout engine hỏi:

```text
LayoutOf(A)?
```

Hai query độc lập.

Đây là một quyết định kiến trúc quan trọng.

---

# 58. Type inference không suy đoán representation

Ví dụ:

```axiom
struct Meter(f64)
struct Second(f64)
```

Compiler không suy:

```text
Meter ~ f64
```

chỉ vì representation giống.

Do đó các generic/math abstractions an toàn hơn.

---

# 59. Function argument checking

Với:

```axiom
fn add(a: i32, b: i32) -> i32
```

call:

```axiom
add(x, y)
```

checker:

```text
type(x) compatible i32
type(y) compatible i32
```

Mỗi argument tạo constraint riêng.

---

# 60. Receiver checking

```axiom
v.length()
```

sau method resolution:

```text
length(v)
```

Type checker kiểm tra receiver với first parameter:

```text
v : Vec2
expected : Vec2
```

Nếu method cần:

```text
mut_view<Vec2>
```

compiler tạo capability requirement cho ownership verifier.

---

# 61. Generic receiver

```axiom
fn length<T: Metric>(self: T)
```

method resolution có thể tạo:

```text
T = Vec2
Implements(Vec2, Metric)
```

Trait solver chứng minh constraint.

---

# 62. Type inference và ownership không trộn lẫn

Ví dụ:

```axiom
let b = a
```

Type inference:

```text
type(b) = type(a)
```

Ownership verifier:

```text
a → Move
```

Nếu:

```axiom
let b = a.clone()
```

Type inference:

```text
clone(a) : T
```

Ownership:

```text
a remains valid
```

Hai tầng rõ ràng.

---

# 63. Type inference và capability

```axiom
fn read(v: view<i32>)
```

call:

```axiom
read(x)
```

Type checker xác định:

```text
expected type = view<i32>
```

Coercion engine tạo:

```text
x → ephemeral view<i32>
```

Capability verifier mới kiểm tra lifetime/provenance.

---

# 64. Type checking block expression

```axiom
{
    let x = 10
    x + 1
}
```

Block type = type của final expression:

```text
i32
```

Nếu không có final value:

```text
()
```

---

# 65. If expression

```axiom
if cond {
    10
} else {
    20
}
```

hai branches phải có compatible type:

```text
i32
i32
```

→ result `i32`.

---

# 66. Branch type mismatch

```axiom
if cond {
    10
} else {
    "hello"
}
```

→ error.

Axiom không tự tạo:

```text
Any
```

để chứa hai type.

---

# 67. `never` branch

```axiom
if cond {
    return 10
} else {
    20
}
```

`return` có type `never`.

Do đó:

```text
never
i32
```

→ block expression `i32`.

---

# 68. Match typing

Mỗi arm:

```text
Pattern
Guard
Body
```

body phải unify thành cùng result type.

Ví dụ:

```axiom
match x {
    Some(v) => v
    None => 0
}
```

nếu `v : i32`:

```text
match : i32
```

---

# 69. Generic inference through match

Pattern có thể tạo constraints.

```axiom
match value {
    Some(x) => x
    None => default()
}
```

`Option<T>` và return type của `default()` cùng constrain `T`.

---

# 70. Recursive types

Direct infinite-size:

```axiom
struct Node {
    next: Node
}
```

phải reject vì layout vô hạn.

Nhưng:

```axiom
struct Node {
    next: Box<Node>
}
```

có thể hợp lệ.

Type checker phát hiện recursive type; Layout checker xác định finite representation.

---

# 71. Recursive generic constraints

Type solver phải phát hiện cycles:

```text
T → U
U → T
```

Nếu cycle chỉ là equivalent constraints:

```text
T = U
```

merge.

Nếu tạo infinite expansion:

```text
T = Vec<T>
```

reject.

---

# 72. Type substitution

Generic instantiation:

```text
foo<T>
```

với:

```text
T = i32
```

tạo substitution:

```text
Substitution {
    T → i32
}
```

Không mutate generic definition.

---

# 73. Generic instance identity

```text
GenericInstanceId {
    GenericDefinitionId
    TypeArguments
    ConstArguments
}
```

Ví dụ:

```text
Vec<i32>
```

có identity canonical.

---

# 74. Monomorphization

Backend có thể generate:

```text
Vec_i32
Vec_f64
```

nhưng đây là codegen representation.

Semantic type vẫn:

```text
GenericInstance(Vec, i32)
```

---

# 75. Code sharing

Compiler không bắt buộc tạo một machine copy cho mỗi generic instance.

Có thể:

```text
monomorphize
```

hoặc:

```text
share code
```

nếu representation/effects/optimization cho phép.

Type system không phụ thuộc chiến lược codegen.

---

# 76. Type inference algorithm

Đề xuất pipeline:

```text
1. Create inference context
2. Introduce type variables
3. Collect constraints
4. Apply expected types
5. Unify obvious equalities
6. Normalize aliases/associated types
7. Invoke trait solver
8. Apply permitted coercions
9. Resolve literals
10. Check remaining constraints
11. Generalize where allowed
12. Produce Typed HIR
```

---

# 77. Không generalize tùy tiện

Axiom nên tránh Hindley-Milner unrestricted inference trong mọi context.

Generic declarations phải explicit:

```axiom
fn identity<T>(x: T) -> T
```

Local inference được mạnh:

```axiom
let x = ...
```

nhưng compiler không tự biến một function monomorphic thành generic API.

Điều này giúp ABI/API predictable.

---

# 78. Local inference

Cho phép:

```axiom
let x = Vec::new()
```

nếu context đủ xác định.

Nếu không:

```text
cannot infer type parameter
```

Compiler đề xuất:

```text
Vec<i32>
```

nhưng không tự chọn arbitrary type.

---

# 79. Ambiguous inference

Ví dụ:

```axiom
let x = Vec::new()
```

nếu `Vec::new()` không có đủ context để biết `T`:

```text
T = ?
```

→ compile error:

```text
type parameter T cannot be inferred
```

Đây là **ambiguity**, không phải defaulting tùy tiện.

---

# 80. Trait solver interface

Type system gọi:

```text
solve(TraitPredicate)
```

kết quả:

```text
Proven
NotProven
Ambiguous
Error
```

Trait solver đã được tách thành subsystem.

---

# 81. Type normalization query

```text
normalize(TypeId)
```

ví dụ:

```text
Alias
AssociatedType
Projection
```

→ canonical type.

Query phải memoized.

---

# 82. Type comparison

Không dùng một hàm:

```text
equals()
```

duy nhất.

Cần:

```text
is_same_type
is_assignable
can_coerce
can_cast
can_bitcast
implements_trait
layout_compatible
abi_compatible
```

Đây là cách tránh một lượng lớn bug compiler.

---

# 83. Assignability

Axiom không có subtype hierarchy tổng quát.

Do đó assignment compatibility đến từ:

```text
same type
explicitly allowed coercion
never
specific semantic conversion
```

không phải:

```text
A <: B
```

một cách tùy tiện.

---

# 84. Method type checking

Method resolution trả:

```text
MethodCandidate {
    FunctionId
    receiver_mode
    substitutions
    trait_source
}
```

Type checker chọn candidate sau khi constraints được solve.

---

# 85. Trait ambiguity

Nếu:

```text
TraitA::foo
TraitB::foo
```

đều thỏa:

```text
x: T
```

thì result:

```text
Ambiguous
```

không để optimizer quyết định.

---

# 86. Coherence

Type system phụ thuộc coherence rules đã đóng băng:

```text
impl Trait for Type
```

không được tạo xung đột giữa package/module không hợp lệ.

Điều này giúp trait resolution deterministic.

---

# 87. Orphan rule

Không cho arbitrary package inject implementation vào hai foreign types/traits.

Mục tiêu:

```text
same program
→ same trait meaning
```

không phụ thuộc import order.

---

# 88. Type aliases và public API

Nếu:

```axiom
pub type UserId = u64
```

public API về semantic type vẫn là `u64`.

Nếu:

```axiom
pub struct UserId(u64)
```

API expose nominal type `UserId`.

ABI engine xử lý representation riêng.

---

# 89. `@repr(transparent)`

Newtype:

```axiom
@repr(transparent)
struct UserId(u64)
```

có ABI contract tương thích underlying representation theo rule `repr(transparent)`.

Nhưng:

```text
UserId != u64
```

vẫn giữ nguyên.

---

# 90. Type system và ABI

Type checker chỉ nói:

```text
Function(i32) -> i64
```

ABI layer sau đó quyết định:

```text
register
stack
return register
calling convention
alignment
aggregate passing
```

Không để ABI logic chui vào inference.

---

# 91. Type system và layout

Tương tự:

```text
TypeDB
   ↓
LayoutDB
```

TypeDB không hard-code:

```text
struct = C layout
```

Default layout compiler-controlled.

---

# 92. Type system và GPU

GPU legality là predicate:

```text
IsGpuLegal<T>
```

Ví dụ:

```axiom
@kernel
fn add(a: view<f32>, ...)
```

type checker xác định types.

GPU legality checker xác định:

```text
được phép tồn tại trong kernel không?
```

---

# 93. Type system và comptime

Comptime values vẫn dùng cùng TypeDB:

```text
const x: i32 = 10
```

không tạo một “comptime type system” thứ hai.

Điều này cực kỳ quan trọng để giảm compiler complexity.

---

# 94. Type system và reflection

Compile-time:

```text
Type
```

là semantic compiler value.

Runtime type descriptor chỉ tồn tại nếu metadata/runtime reflection được yêu cầu.

Không có:

```text
Type
```

runtime object mặc định.

---

# 95. Type errors phải structured

Diagnostic:

```text
TypeMismatch {
    expected: TypeId
    found: TypeId
    expression: SourceSpan
    coercion_attempts: [...]
    constraints: [...]
}
```

Ví dụ AI tooling có thể hỏi:

```text
ax explain type-error
```

và compiler trả dependency graph của constraint.

---

# 96. Ví dụ diagnostic

Thay vì:

```text
type mismatch
```

Axiom nên đưa:

```text
expected: view<f32>
found: String

required coercion:
    String → Str

available:
    String → Str
    String → view<u8>

reason:
    expected element type f32 does not match u8
```

Đây chính là **proof-oriented diagnostic**.

---

# 97. Type inference data structure

Đề xuất:

```text
InferenceContext
├── TypeVariables
├── UnionFind
├── Constraints
├── ExpectedTypes
├── CoercionConstraints
├── TraitGoals
├── LiteralConstraints
├── ProjectionConstraints
└── Diagnostics
```

Union-Find rất phù hợp cho unification.

---

# 98. Incremental TypeDB

Queries:

```text
infer_expression(ExpressionId, ExpectedType)
check_function(FunctionId)
normalize_type(TypeId)
solve_type_relation(A, B)
instantiate_generic(GenericInstanceId)
```

Memoized theo CompilerDB revision.

---

# 99. Parallel type checking

Các function độc lập có thể type-check song song nếu dependency graph cho phép.

```text
Function A ─┐
Function B ─┼── parallel
Function C ─┘
```

Trait queries và shared TypeDB phải deterministic.

---

# 100. Type inference correctness boundary

Chỉ khi:

```text
All constraints solved
+
No ambiguity
+
All types well-formed
+
All coercions legal
+
All trait obligations resolved
```

mới tạo:

```text
Typed HIR
```

Nếu còn:

```text
Unknown
Incomplete
Ambiguous
```

thì chỉ được Partial Semantic Mode.

Không được đi tới Verified MIR.

---

# 101. Compiler architecture sau 239

```text
                 AST
                  │
                  ▼
              Resolver
                  │
                  ▼
          Resolved AST
                  │
                  ▼
       ┌─────────────────────┐
       │   Type System       │
       │                     │
       │ TypeDB              │
       │ Inference           │
       │ Unification         │
       │ Normalization       │
       │ Coercion            │
       └──────────┬──────────┘
                  │
                  ▼
              Trait Solver
                  │
                  ▼
              Typed HIR
                  │
                  ▼
                 MIR
```

Điểm quan trọng:

> **Type System không cần biết code sẽ chạy trên stack, heap, register, CPU hay GPU.**

Nó chỉ mô tả semantic type. Những tầng sau mới quyết định representation.

---

# 102. Bộ invariants đóng băng

```text
ATYPE-20
Every semantic type has a canonical TypeId.

ATYPE-21
Nominal types are identified by declaration identity.

ATYPE-22
Type aliases do not create new nominal types.

ATYPE-23
Newtypes create distinct nominal types.

ATYPE-24
Representation equality does not imply type equality.

ATYPE-25
Type layout is independent of semantic type equality.

ATYPE-26
Primitive types have compiler-known canonical identities.

ATYPE-27
Tuple types are structurally identified.

ATYPE-28
Array type identity includes element type and compile-time length.

ATYPE-29
Generic instances are canonically identified by definition and arguments.

ATYPE-30
Type interning must not create duplicate canonical semantic types.

ATYPE-31
Type variables are compiler-internal inference entities.

ATYPE-32
Unification must perform occurs checking.

ATYPE-33
Infinite recursive types are rejected unless represented through finite indirection.

ATYPE-34
Type inference is deterministic.

ATYPE-35
Type inference must not use probabilistic or AI-based selection.

ATYPE-36
Ambiguous inference is not silently defaulted except for explicitly defined literal defaults.

ATYPE-37
Expected-type propagation is supported.

ATYPE-38
Inference and checking are bidirectional.

ATYPE-39
Generic declarations are not implicitly generalized from monomorphic implementations.

ATYPE-40
Generic inference does not alter generic declaration identity.

ATYPE-41
Associated types require trait/type-system normalization.

ATYPE-42
Trait obligations are solved by the trait solver, not lexical resolution.

ATYPE-43
Type normalization is canonical and memoizable.

ATYPE-44
Never can coerce to every expected type without forming a subtype hierarchy.

ATYPE-45
Option and Result are ordinary algebraic types.

ATYPE-46
Null is not a universal Core type.

ATYPE-47
view<T> is distinct from raw pointers.

ATYPE-48
mut_view<T> is distinct from ordinary T and view<T>.

ATYPE-49
Raw pointers do not imply safe ownership or provenance.

ATYPE-50
Closure types are distinct semantic callable types.

ATYPE-51
Capturing closures are distinct from function pointers.

ATYPE-52
Noncapturing closure conversion to function pointer is permitted only when semantics allow.

ATYPE-53
Function effects are represented independently from physical representation.

ATYPE-54
Copy, Drop, Send, Share, Sized, FfiSafe and GpuLegal are distinct semantic properties.

ATYPE-55
Drop-bearing types cannot be Copy.

ATYPE-56
Send does not imply Share.

ATYPE-57
Share does not imply mutable sharing.

ATYPE-58
Coercions are compiler-defined and bounded.

ATYPE-59
Implicit conversion chains are forbidden.

ATYPE-60
Cast and bitcast have distinct semantics.

ATYPE-61
Bitcast requires representation validity according to its contract.

ATYPE-62
Type checking does not determine physical ABI lowering.

ATYPE-63
Type checking does not determine storage allocation strategy.

ATYPE-64
Type checking does not perform ownership verification.

ATYPE-65
Type checking does not perform synchronization verification.

ATYPE-66
Type checking does not infer GPU legality unless explicitly queried.

ATYPE-67
Comptime uses the same semantic TypeDB as runtime code.

ATYPE-68
Runtime reflection is not implied by compile-time type information.

ATYPE-69
Type errors preserve source provenance.

ATYPE-70
Type constraints are inspectable by compiler tooling.

ATYPE-71
Type inference queries are incrementally cacheable.

ATYPE-72
Independent type-checking work may execute in parallel deterministically.

ATYPE-73
No unresolved or ambiguous type may enter production Typed HIR.

ATYPE-74
Partial semantic type information cannot establish production correctness.

ATYPE-75
Type identity is independent of source spelling aliases and import paths.

ATYPE-76
Type identity is independent of optimization level.

ATYPE-77
Generic instance identity is independent of code-generation strategy.

ATYPE-78
Trait implementation selection cannot depend on import order.

ATYPE-79
Type-system behavior is specified independently from compiler implementation details.

ATYPE-80
Only formally defined type relations may permit assignment or coercion.
```

---

# 103. Một quyết định quan trọng vừa được củng cố

Sau 239, kiến trúc Axiom có một separation rất sạch:

```text
                SEMANTIC
                   │
        ┌──────────┴──────────┐
        │                     │
   Type Identity         Value Semantics
        │                     │
        ▼                     ▼
   Type System           Ownership
        │                 Capability
        │                 Drop
        ▼                     │
      Traits                   │
        │                     │
        └──────────┬──────────┘
                   ▼
                MIR
                   │
                   ▼
             Representation
                   │
                   ▼
                  ABI
                   │
                   ▼
              Machine Code
```

Như vậy programmer không cần biết:

```text
register nào
stack frame nào
pointer nào
heap block nào
vtable nằm đâu
```

trong phần lớn code.

Nhưng compiler vẫn có đủ semantic information để tối ưu xuống machine code rất thấp tầng.

---

## TASK TIẾP THEO

### **BOOTSTRAP-240 — AXIOM TRAIT SYSTEM, TRAIT SOLVER & GENERIC CONSTRAINT ENGINE**

Đây sẽ là phần nối trực tiếp với 239 và Behavior Model 232.

Sẽ đóng băng chi tiết:

```text
trait
impl
generic bounds
associated type
associated const
associated function
Self
supertrait
default method
coherence
orphan rule
trait specialization
negative reasoning
auto traits
trait object
dyn Trait
trait upcasting
projection
normalization
recursive constraints
candidate selection
ambiguity
solver caching
incremental trait solving
```

Đặc biệt sẽ phải giải quyết một câu hỏi rất quan trọng cho Axiom:

> **Làm sao có trait/generic đủ mạnh để thay thế phần lớn nhu cầu inheritance + overload + interface, nhưng Trait Solver vẫn nhanh, deterministic và không trở thành “compiler within compiler” quá nặng?**