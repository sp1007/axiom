# BOOTSTRAP-223 — AXIOM TYPE SYSTEM IMPLEMENTATION SPECIFICATION

**TRẠNG THÁI: FROZEN / COMPLETED**

Đây là phần cực kỳ quan trọng. Type System của Axiom không chỉ trả lời:

> “Giá trị này có kiểu gì?”

mà còn phải tạo ra **semantic facts** để các phase sau dùng:

```text
Type
Copy / Move
Drop
Sized
Send
Share
FfiSafe
GpuLegal
CapabilityKind
Layout requirements
Effect constraints
```

Nhưng cần giữ một nguyên tắc:

> **Type system xác định khả năng và thuộc tính của kiểu; ownership verifier mới xác định trạng thái sở hữu cụ thể của từng value/place.**

---

# 1. Kiến trúc Type System

```text
ResolvedAST
     │
     ▼
 Type Checker
     │
     ├── TypeDB
     ├── TraitDB
     ├── GenericDB
     ├── ConstDB
     └── PropertyDB
     │
     ▼
Typed HIR
```

Không để TypeDB phụ thuộc MIR.

---

# 2. TypeDB

TypeDB là semantic database trung tâm cho type.

```text
TypeDB
├── primitive types
├── tuple types
├── array types
├── struct types
├── enum types
├── function types
├── closure types
├── generic parameters
├── generic instances
├── trait objects
├── view types
├── mut_view types
├── pointer types
├── never/unit
└── type variables
```

---

# 3. TypeId

Mọi semantic type được định danh bằng:

```text
TypeId
```

Không dùng:

```text
String
```

làm type identity.

Ví dụ:

```text
i32       → TypeId(1)
f32       → TypeId(2)
Point     → TypeId(100)
Vec<i32>  → TypeId(101)
```

---

# 4. Type interning

Các type immutable có thể intern:

```text
make_array(i32, 4)
```

nhiều lần phải trả cùng semantic TypeId trong cùng compiler revision.

Ví dụ:

```text
Array<i32,4>
```

không tạo hàng nghìn object semantic giống nhau.

---

# 5. Type representation

```text
TypeKind =
    Primitive
    Tuple
    Array
    Struct
    Enum
    Function
    Closure
    GenericParam
    GenericInstance
    TraitObject
    View
    MutView
    RawPointer
    Unit
    Never
    TypeVar
    Error
```

---

# 6. PrimitiveType

```text
PrimitiveType =
    Bool
    I8
    I16
    I32
    I64
    U8
    U16
    U32
    U64
    Isize
    Usize
    F32
    F64
```

Các type mở rộng như:

```text
i128
u128
f16
bf16
```

có thể được thêm mà không phá TypeDB architecture.

---

# 7. Unit và Never

`unit`:

```text
unit
```

là kiểu có một giá trị duy nhất.

`never`:

```text
never
```

không có value.

Ví dụ:

```axiom
fn abort() -> never {
    panic("fatal")
}
```

`never` có thể coerce vào context cần type khác vì control flow không tiếp tục.

---

# 8. Type equality

Axiom cần phân biệt:

```text
Type Identity
Type Compatibility
Type Coercibility
Representation Compatibility
ABI Compatibility
```

Không được gộp thành một `is_same_type()`.

---

# 9. Nominal types

Các declaration:

```axiom
struct UserId(u64)
struct ProductId(u64)
```

là hai type khác nhau.

Dù representation giống nhau:

```text
UserId ≠ ProductId
```

Đây là cách tránh lỗi nhầm semantic identifier.

---

# 10. Type alias

```axiom
type UserId = u64
```

là alias.

```text
UserId == u64
```

về type identity.

Khác với:

```axiom
struct UserId(u64)
```

là newtype.

---

# 11. Tuple type

```axiom
(i32, f32, bool)
```

semantic representation:

```text
TupleType {
    elements: [TypeId, TypeId, TypeId]
}
```

Tuple là structural type.

---

# 12. Array type

Canonical:

```axiom
[4]i32
```

Type:

```text
ArrayType {
    element: TypeId
    length: ConstValue
}
```

Hai array:

```text
[4]i32
[8]i32
```

là hai type khác nhau.

---

# 13. Array length là compile-time value

```axiom
const N = 4

let a: [N]i32
```

`N` phải resolve thành compile-time constant.

Không dùng runtime integer làm array type parameter trong Core v1.

---

# 14. Struct type

```text
StructType {
    declaration: DeclarationId
    substitutions: GenericSubstitution
}
```

Ví dụ:

```axiom
struct Point<T> {
    x: T
    y: T
}
```

```text
Point<i32>
Point<f32>
```

là hai `GenericInstance`.

---

# 15. Enum type

```text
EnumType {
    declaration: DeclarationId
    substitutions
}
```

Ví dụ:

```axiom
Option<i32>
Option<String>
```

khác nhau.

---

# 16. Function type

```text
fn(i32, i32) -> i32
```

semantic:

```text
FunctionType {
    params[]
    return_type
    calling_convention
    effects
}
```

Không đưa function declaration identity vào function type.

Hai function khác nhau có thể cùng function type.

---

# 17. Function type và ABI

Function type semantic không đồng nghĩa ABI signature.

Ví dụ:

```text
fn(i64) -> i64
```

có thể ABI khác nhau trên:

```text
x86-64
AArch64
WASM
```

ABI lowering xử lý việc đó sau.

---

# 18. Closure type

Mỗi closure có anonymous semantic type:

```text
ClosureType {
    closure_id
    parameters
    return_type
    captures
}
```

Closure không phải struct source-level thông thường, nhưng compiler có thể lower nó thành environment struct + function.

---

# 19. Closure capture

Compiler phân tích:

```text
CaptureMode =
    ByValue
    ByView
    ByMutView
```

Ví dụ:

```axiom
let offset = 10

let f = |x| x + offset
```

compiler có thể xác định:

```text
capture offset → ByValue
```

Programmer không cần viết lifetime.

---

# 20. Capture property

Closure type phải expose:

```text
CaptureSet
```

để verifier sau này biết:

```text
value live
view live
mutable capability live
```

---

# 21. `view<T>`

`view<T>` là một **capability type**, không phải ordinary pointer alias.

```text
ViewType {
    element: TypeId
}
```

Semantic:

```text
view<T>
```

cho phép READ.

---

# 22. `mut_view<T>`

```text
MutViewType {
    element: TypeId
}
```

Semantic:

```text
mut_view<T>
```

cho phép WRITE và READ theo exclusive capability.

---

# 23. View type không encode lifetime

Không có:

```text
view<'a, T>
```

trong source.

TypeDB cũng không cần expose lifetime parameter.

Lifetime/provenance được verifier theo dõi tại **capability instance**.

Đây là một điểm rất quan trọng để giữ ngôn ngữ đơn giản.

---

# 24. Type-level capability vs instance capability

Ví dụ:

```axiom
fn read(x: view<i32>)
```

TypeDB biết:

```text
READ capability
```

Nhưng khi:

```axiom
read(view(a))
```

compiler phải tạo:

```text
CapabilityId
```

và verifier theo dõi:

```text
owner = a
region = a
lifetime = call
```

---

# 25. Raw pointer type

```axiom
*const i32
*mut i32
```

TypeDB:

```text
RawPointerType {
    element
    mutable
}
```

Nhưng type này không có safe capability.

---

# 26. Pointer semantics

```text
*const T
```

không đồng nghĩa:

```text
view<T>
```

và:

```text
*mut T
```

không đồng nghĩa:

```text
mut_view<T>
```

Conversion cần unsafe contract.

---

# 27. Generic parameter

```axiom
fn identity<T>(x: T) -> T
```

`T`:

```text
GenericParamType {
    GenericParamId
}
```

Không resolve `T` thành `Any`.

---

# 28. Type variable

Type inference sử dụng:

```text
TypeVarId
```

Ví dụ:

```axiom
let x = identity(42)
```

trước inference:

```text
T = ?T0
```

sau inference:

```text
T = i32
```

---

# 29. Type variable state

```text
TypeVarState =
    Unbound
    Bound(TypeId)
    Error
```

Không cho cycle:

```text
T = Vec<T>
```

trừ khi semantic type system có explicit recursive type mechanism.

---

# 30. Unification

API:

```text
unify(TypeId, TypeId)
```

Các trường hợp:

```text
i32 ~ i32       → success
i32 ~ f32       → failure
T ~ i32         → bind T=i32
Vec<T> ~ Vec<i32> → bind T=i32
```

---

# 31. Occurs check

Phải chống:

```text
T = Vec<T>
```

trong inference thông thường.

Nếu gặp:

```text
T occurs in Vec<T>
```

→ type error.

---

# 32. Constraint graph

Inference không nên thực hiện bằng recursion đơn giản.

Compiler xây:

```text
ConstraintGraph
```

Node:

```text
TypeVar
ConcreteType
```

Edge:

```text
Equal
Subtype?          // chỉ nếu subsystem thực sự cần
Coerce
TraitBound
```

Axiom Core không có general subtype hierarchy, nên `Subtype` không phải edge phổ biến.

---

# 33. Type inference

Inference pipeline:

```text
ResolvedAST
      ↓
Create type variables
      ↓
Generate constraints
      ↓
Solve equality
      ↓
Solve trait obligations
      ↓
Apply coercions
      ↓
Default literals
      ↓
Generalize where allowed
      ↓
Typed HIR
```

---

# 34. Literal inference

Ví dụ:

```axiom
let x = 42
```

Không nhất thiết lập tức chọn `i32` ở lexer.

Literal semantic node:

```text
IntegerLiteral
```

Type inference xem context.

Nếu không có context, Axiom cần một default literal policy cố định.

Khuyến nghị:

```text
integer → i32
float → f64
```

trừ khi suffix/context xác định khác.

---

# 35. Numeric coercion

Không cho:

```axiom
let x: i64 = 42
```

bị coi là runtime cast.

Đây là literal typing.

Nhưng:

```axiom
let a: i32 = ...
let b: i64 = a
```

phải explicit:

```axiom
let b = a as i64
```

---

# 36. No implicit numeric conversion chains

Không:

```text
i32
 ↓
i64
 ↓
f64
```

chỉ vì function yêu cầu `f64`.

Điều này giúp inference deterministic và tránh loss precision.

---

# 37. Coercion engine

API:

```text
coerce(source, expected)
```

chỉ cho các coercion được định nghĩa.

Ví dụ:

```text
String → Str
Array<T,N> → view<T>
owner → ephemeral view<T>
mut_view<T> → view<T>
never → T
```

Không arbitrary conversion.

---

# 38. View coercion

Nếu:

```axiom
fn sum(a: view<i32>) -> i32
```

gọi:

```axiom
sum(array)
```

Type checker có thể ghi:

```text
ImplicitViewCoercion
```

vào Typed HIR.

Nhưng capability verifier vẫn phải kiểm tra lifetime/provenance.

---

# 39. `mut_view → view`

Được phép:

```text
mut_view<T>
   ↓
view<T>
```

vì giảm quyền.

Ngược lại:

```text
view<T>
   ↓
mut_view<T>
```

không bao giờ safe coercion.

---

# 40. Copy property

TypeDB phải query được:

```text
is_copy(TypeId)
```

Nhưng:

```text
Copy
```

không phải subtype.

Đó là **type property/semantic trait**.

---

# 41. Copy derivation

Compiler có thể derive Copy nếu:

```text
all fields Copy
+
no Drop obligation
+
no non-copy semantic resource
```

Ví dụ:

```axiom
struct Point {
    x: i32
    y: i32
}
```

có thể Copy.

---

# 42. Copy không có nghĩa memcpy

Type system chỉ xác nhận:

```text
copy(x)
```

có semantics duplicate value.

Backend quyết định có thực sự copy memory hay không.

---

# 43. Clone

`Clone` khác `Copy`.

```axiom
let b = a.clone()
```

luôn là explicit semantic duplication.

Có thể:

- allocate;
- deep copy;
- duplicate external resource theo contract;
- hoặc cheap copy.

Compiler không giả định.

---

# 44. Drop property

```text
has_drop(TypeId)
```

Nếu type có Drop obligation:

```text
Copy forbidden
```

---

# 45. Drop composition

Struct:

```axiom
struct A {
    x: File
    y: Socket
}
```

compiler suy ra:

```text
A has Drop obligation
```

ngay cả khi user không viết `Drop`.

---

# 46. User-defined Drop

Nếu Axiom cho custom destructor trait/implementation:

```text
impl Drop for T
```

thì type property:

```text
CustomDrop
```

và verifier phải áp dụng restriction:

```text
no partial move
```

như memory model đã khóa.

---

# 47. Sized

Type system cần property:

```text
Sized
```

Các type có size compile-time:

```text
i32
Point
[i32; 4]
```

View thường có representation size cố định.

Một số dynamic/unsized abstraction có thể xuất hiện về sau.

---

# 48. Không dùng `Sized` để ép mọi thứ

Compiler không được biến:

```text
unsized
```

thành:

```text
boxed automatically
```

nếu API không yêu cầu.

Không implicit allocation.

---

# 49. Send / Share

TypeDB query:

```text
is_send(T)
is_share(T)
```

Đây là semantic properties.

Ví dụ:

```text
i32 → Send, Share
Rc<T> → không Send qua thread
Arc<T> → Send nếu T thỏa điều kiện
```

Chi tiết được TraitDB/Concurrency verifier hoàn tất.

---

# 50. Send ≠ Share

Type system phải giữ hai facts riêng:

```text
Send(T)
Share(T)
```

Không có:

```text
Send(T) ⇒ Share(T)
```

---

# 51. FfiSafe

Property:

```text
FfiSafe<ABI>
```

Không phải mọi struct đều tự động FFI-safe.

Ví dụ:

```axiom
@repr(C)
struct Point {
    x: f32
    y: f32
}
```

có thể đáp ứng C ABI representation requirements.

---

# 52. GpuLegal

GPU type property:

```text
GpuLegal<Profile>
```

Nhưng `GpuLegal` không chỉ là type property.

Nó còn phụ thuộc:

```text
execution domain
storage domain
operation set
address space
```

Do đó TypeDB chỉ cung cấp phần type-level facts; GPU verifier hoàn tất legality.

---

# 53. Trait facts

Type system không hard-code:

```text
T + U
```

thành phép cộng machine-level.

Nó tạo:

```text
TraitObligation {
    trait = Add
    self_type = T
    args = U
}
```

Trait solver quyết định.

---

# 54. Operator typing

```axiom
a + b
```

→ tạo obligation:

```text
Add<a, b>
```

Sau trait resolution:

```text
Output = R
```

thì expression type là:

```text
R
```

---

# 55. Built-in operator exceptions

Một số operator không nên qua trait:

```text
&&
||
```

vì chúng có short-circuit control-flow semantics.

Comparison/indexing có thể dùng trait hoặc compiler-known protocols tùy Core contract.

---

# 56. Generic instantiation

Ví dụ:

```axiom
fn identity<T>(x: T) -> T
```

call:

```axiom
identity(10)
```

compiler tạo:

```text
GenericInstance {
    declaration = identity
    substitutions = [T → i32]
}
```

---

# 57. Generic instance identity

Hai call:

```text
identity(10)
identity(20)
```

cùng:

```text
identity<i32>
```

semantic instance.

Compiler có thể reuse codegen.

---

# 58. Monomorphization

Default implementation strategy:

```text
Generic<T>
   ↓
Concrete Instances
   ↓
monomorphized code
```

Nhưng compiler có thể code-share khi ABI/layout cho phép.

Không biến monomorphization thành semantic requirement.

---

# 59. Specialization

Axiom v1:

```text
No arbitrary specialization
```

để tránh trait solver ambiguity và coherence complexity.

Compiler optimization có thể specialize internally nếu semantics giữ nguyên.

---

# 60. Generic recursion

Trait/type solver phải giới hạn:

```text
recursive type expansion
trait recursion
generic instantiation depth
```

Nếu vượt resource limit:

```text
AXTYPE-xxx
```

Không crash compiler.

---

# 61. Type normalization

Compiler cần:

```text
normalize(TypeId)
```

để resolve:

- aliases;
- associated types;
- generic substitutions;
- compiler-known projections.

Ví dụ:

```text
type UserId = u64
```

normalize:

```text
UserId → u64
```

nhưng:

```text
struct UserId(u64)
```

không normalize thành `u64`.

---

# 62. Associated type

Trait:

```axiom
trait Iterator {
    type Item
}
```

Projection:

```text
<T as Iterator>::Item
```

TypeDB có:

```text
AssociatedTypeProjection {
    trait
    self_type
    assoc
}
```

Trait solver giải projection.

---

# 63. Type normalization phải lazy

Không eagerly expand toàn bộ generic type graph.

Nếu:

```text
Vec<Vec<Vec<...>>>
```

compiler chỉ normalize khi query cần.

Điều này quan trọng cho memory/compiler performance.

---

# 64. Trait object

```axiom
dyn Display
```

là explicit type-erasure.

TypeDB:

```text
TraitObjectType {
    trait
    associated_bindings
}
```

Dynamic dispatch không được tự xuất hiện chỉ vì generic solver khó.

---

# 65. `dyn Trait` không đồng nghĩa heap

`dyn Trait` có thể có representation:

```text
data pointer
metadata/vtable pointer
```

nhưng việc heap allocation hay không phụ thuộc storage context.

Không có implicit `new`.

---

# 66. Object safety / dyn legality

Không phải trait nào cũng có thể:

```text
dyn Trait
```

Trait solver/type checker phải validate object compatibility.

Các method generic hoặc Self-sensitive semantics có thể làm trait không dyn-compatible tùy rules.

---

# 67. Type inference và method resolution

Flow:

```text
v.length()
```

không được resolve chỉ bằng syntax.

Compiler:

```text
type(v)
 ↓
candidate methods
 ↓
instantiate candidate
 ↓
generate trait obligations
 ↓
solve
 ↓
choose exactly one
```

---

# 68. Recursive type checking

Compiler phải hỗ trợ declaration-level cycles hợp lệ:

```axiom
struct Node {
    next: Box<Node>
}
```

nhưng không:

```axiom
struct Node {
    next: Node
}
```

nếu semantic layout vô hạn.

Type checking và layout checking là hai phase khác nhau.

---

# 69. Recursive function

```axiom
fn factorial(n: i32) -> i32 {
    if n == 0 {
        1
    } else {
        n * factorial(n - 1)
    }
}
```

type checker resolve declaration signature trước body.

Do đó recursive call biết return type.

---

# 70. Type checking phases

Khuyến nghị:

```text
Phase A
Declaration signatures

Phase B
Type declarations

Phase C
Generic declarations

Phase D
Trait/impl headers

Phase E
Function bodies

Phase F
Inference solving

Phase G
Coercion insertion

Phase H
Typed HIR emission
```

---

# 71. Không type-check function body trước signature

Điều này cho phép:

```axiom
fn a() -> i32 {
    b()
}

fn b() -> i32 {
    42
}
```

không phụ thuộc declaration order nếu module semantics cho phép.

---

# 72. Type checking result

```text
TypedExpr {
    expr_id
    type_id
    coercions[]
    obligations[]
}
```

Không cần copy toàn bộ expression AST.

Có thể dùng:

```text
ExprId → TypeId
```

và side tables.

---

# 73. Typed HIR

Typed HIR phải đủ information để HIR → MIR không quay lại type inference.

Ví dụ:

```text
Call {
    function = FunctionId
    substitutions = ...
    args = ...
    return_type = TypeId
}
```

---

# 74. Type checking error

Diagnostic phải chỉ rõ:

```text
expected type
actual type
source expression
inference path
coercion candidates
relevant trait obligation
```

Ví dụ conceptually:

```text
expected: view<Point>
found: i32

required by:
    parameter 1 of draw_point(...)
```

---

# 75. Error propagation

Một type error không được tạo hàng trăm diagnostics giả.

Compiler dùng:

```text
ErrorType
```

để tiếp tục analysis cục bộ.

Nhưng:

```text
ErrorType
```

không được satisfy arbitrary trait/type proof.

---

# 76. Type facts database

Đề xuất:

```text
TypeFacts {
    copy
    drop
    sized
    send
    share
    ffi_safe
    gpu_legal
    trivially_relocatable
    has_identity
}
```

Một số facts có thể là tri-state:

```text
Proven
NotProven
Unknown
```

đặc biệt trong Partial Mode.

---

# 77. `trivially_relocatable`

Đây là property đáng đưa vào compiler nội bộ.

Nó không có nghĩa:

```text
Copy
```

Một type có thể:

```text
Move
```

nhưng vẫn cho phép physical relocation vì không có stable-address invariant.

Điều này hỗ trợ optimizer mạnh.

---

# 78. Copy / Move / Relocate

Ba semantic concepts phải độc lập:

```text
Copy
Move
Physical Relocation
```

Ví dụ:

```text
Move String
```

không nhất thiết copy bytes.

Compiler có thể relocate storage.

---

# 79. Type layout query

TypeDB không tự tính layout cuối cùng.

API:

```text
layout_of(TypeId, TargetId)
```

delegates to:

```text
LayoutDB
```

Điều này giữ semantic type và physical layout độc lập.

---

# 80. Type → Layout boundary

```text
TypeDB
   ↓
LayoutDB
   ↓
AbiDB
```

Không:

```text
TypeDB → x86 register
```

---

# 81. Generic layout

`Vec<T>` không cần biết layout cụ thể khi generic source được type-check.

Monomorphization:

```text
Vec<i32>
```

mới query:

```text
LayoutDB(Vec<i32>, target)
```

---

# 82. Type cache

Cache key:

```text
TypeQueryKey {
    revision
    expression/declaration
    expected_type?
    generic_environment
    target_context?
}
```

Không cache dựa trên source line đơn thuần.

---

# 83. Incremental invalidation

Nếu:

```axiom
struct Point {
    x: i32
    y: i32
}
```

đổi thành:

```axiom
struct Point {
    x: i64
    y: i32
}
```

phải invalidate:

```text
Point TypeId/fingerprint
 ↓
dependent expressions
 ↓
generic instances
 ↓
layout
 ↓
ABI
 ↓
codegen
```

Không rebuild unrelated modules.

---

# 84. Semantic fingerprint

Type fingerprint phải phân biệt:

```text
source identity
semantic identity
representation identity
ABI identity
```

Ví dụ thay field order có thể:

```text
semantic type fingerprint = unchanged
representation fingerprint = changed
```

nếu semantic field identity vẫn giữ nguyên.

---

# 85. Type system performance

Các yêu cầu:

```text
type interning
substitution interning
constraint memoization
trait obligation memoization
lazy normalization
incremental inference
parallel independent function checking
```

Trait solver và type inference là hai nơi dễ trở thành bottleneck nhất.

---

# 86. Type solver parallelism

Các function độc lập:

```text
f()
g()
h()
```

có thể type-check song song nếu không có dependency.

CompilerDB revision model đảm bảo deterministic kết quả.

---

# 87. Determinism

Hash-map iteration order không được quyết định:

```text
type candidate
trait candidate
overload winner
diagnostic order
```

Mọi tie phải có semantic ordering hoặc trở thành ambiguity.

---

# 88. Type-system API tối thiểu

```text
type_of(expr)
type_of_place(place)
unify(a, b)
is_equal(a, b)
normalize(t)
coerce(a, b)

is_copy(t)
has_drop(t)
is_sized(t)
is_send(t)
is_share(t)
is_ffi_safe(t)
is_gpu_legal(t)

instantiate(t, substitutions)
layout_of(t, target)
```

---

# 89. Acceptance test — basic

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

Expected:

```text
a : i32
b : i32
a+b : i32
return : i32
```

---

# 90. Acceptance test — inference

```axiom
fn identity<T>(x: T) -> T {
    x
}

fn main() -> i32 {
    identity(42)
}
```

Expected:

```text
T = i32
identity<i32> : fn(i32) -> i32
```

---

# 91. Acceptance test — newtype

```axiom
struct UserId(u64)
struct ProductId(u64)
```

Expected:

```text
UserId != ProductId
```

and:

```axiom
fn f(x: UserId) {}

let p: ProductId = ...
f(p)
```

must fail.

---

# 92. Acceptance test — views

```axiom
fn inspect(p: view<Point>) {}

let point = Point { ... }

inspect(point)
```

Expected Typed HIR:

```text
MakeEphemeralView(point)
Call(inspect, ...)
```

Không tạo raw pointer.

---

# 93. Acceptance test — mutability

```axiom
fn modify(p: mut_view<Point>) {}

let point = Point { ... }

modify(point)
```

Compiler tạo mutable capability.

Nếu một conflicting capability đang live:

```text
reject
```

Capability verifier chịu trách nhiệm cuối cùng.

---

# 94. Acceptance test — Copy

```axiom
struct Point {
    x: i32
    y: i32
}

let a = Point { ... }
let b = a
```

Nếu `Point: Copy`, semantic result:

```text
a remains valid
b independent value
```

Nếu `Point: !Copy`, result:

```text
a moved
b owns value
```

---

# 95. Acceptance test — Drop

```axiom
let file = open(...)
```

Type system:

```text
File: Drop
File: !Copy
```

Ownership verifier sau đó quyết định vị trí cleanup.

---

# 96. Acceptance test — Send/Share

```text
Arc<T>
```

không tự imply:

```text
T: mutable Share
```

Type facts phải phản ánh chính xác.

---

# 97. Acceptance test — coercion

```axiom
fn read(s: Str) {}

let s: String = ...
read(s)
```

Valid:

```text
String → Str
```

nhưng:

```axiom
let s2 = ...
```

không được giữ một `Str` escaping nếu owner không đủ lifetime.

Phần sau verifier bắt.

---

# 98. Acceptance test — invalid numeric

```axiom
let a: i32 = ...
let b: i64 = a
```

phải fail.

```axiom
let b = a as i64
```

valid.

---

# 99. Acceptance test — ambiguous generic

Nếu call không đủ thông tin để infer:

```text
T = ?
```

và nhiều instantiation hợp lệ:

```text
AXTYPE-AMBIGUOUS
```

Không default tùy tiện.

---

# 100. Type system boundary

Đầu vào:

```text
ResolvedAST
```

Đầu ra:

```text
TypedHIR
+
TypeFacts
+
TraitObligations
+
CoercionFacts
+
GenericInstances
```

Sau phase này:

```text
No unresolved ordinary expression types
```

ngoại lệ chỉ là recovery/partial mode.

---

# 101. Invariants của BOOTSTRAP-223

```text
ATYPE-IMPLEMENT-20
Every semantic type has stable TypeId identity.

ATYPE-IMPLEMENT-21
Type identity is distinct from physical representation.

ATYPE-IMPLEMENT-22
Nominal newtypes remain distinct even when representation-compatible.

ATYPE-IMPLEMENT-23
Aliases do not create new semantic type identity.

ATYPE-IMPLEMENT-24
Type interning is deterministic.

ATYPE-IMPLEMENT-25
Type inference never invents implicit general subtype relationships.

ATYPE-IMPLEMENT-26
Unification performs occurs-check where recursive inference could arise.

ATYPE-IMPLEMENT-27
Numeric conversion is never introduced as an arbitrary implicit coercion.

ATYPE-IMPLEMENT-28
Only specification-defined coercions may be inserted implicitly.

ATYPE-IMPLEMENT-29
view<T> represents read capability semantics, not raw pointer semantics.

ATYPE-IMPLEMENT-30
mut_view<T> represents exclusive mutable capability semantics.

ATYPE-IMPLEMENT-31
Lifetime/provenance of capability instances is not encoded as programmer-visible lifetime syntax.

ATYPE-IMPLEMENT-32
Copy, Move and physical relocation are distinct concepts.

ATYPE-IMPLEMENT-33
Drop-bearing types cannot be Copy.

ATYPE-IMPLEMENT-34
Send and Share are independent semantic properties.

ATYPE-IMPLEMENT-35
FFI safety is distinct from ordinary type compatibility.

ATYPE-IMPLEMENT-36
GPU legality is distinct from ordinary type validity.

ATYPE-IMPLEMENT-37
Function type identity is distinct from ABI representation.

ATYPE-IMPLEMENT-38
Generic instances have deterministic semantic identity.

ATYPE-IMPLEMENT-39
Generic inference cannot silently select among ambiguous substitutions.

ATYPE-IMPLEMENT-40
Trait obligations remain explicit facts until solved.

ATYPE-IMPLEMENT-41
ErrorType may support recovery but never proves arbitrary semantic constraints.

ATYPE-IMPLEMENT-42
Typed HIR contains sufficient type information for later lowering without repeating inference.

ATYPE-IMPLEMENT-43
Type normalization is lazy and deterministic.

ATYPE-IMPLEMENT-44
Type queries are incrementally cacheable.

ATYPE-IMPLEMENT-45
Type-system results do not depend on backend implementation details.

ATYPE-IMPLEMENT-46
Type facts are semantic facts, not optimization permissions.

ATYPE-IMPLEMENT-47
Physical layout is delegated to LayoutDB.

ATYPE-IMPLEMENT-48
Type-checking behavior is deterministic independent of hash iteration order.

ATYPE-IMPLEMENT-49
Production Typed HIR contains no unresolved ordinary type variables.

ATYPE-IMPLEMENT-50
Type-system failures cannot silently degrade into unsafe semantics.
```

---

# Kiến trúc Axiom lúc này

Đã hoàn thành:

```text
217 Surface Syntax
218 Compiler Implementation Blueprint
221 Compiler Implementation Contract
222 Frontend
223 Type System
```

Có một điểm rất đáng chú ý:

```text
                  TYPE SYSTEM
                       │
       ┌───────────────┼────────────────┐
       ↓               ↓                ↓
   Type Facts       Trait Goals      Generic Facts
       │               │                │
       └───────────────┼────────────────┘
                       ↓
                   Typed HIR
                       ↓
                      MIR
                       ↓
            Ownership / Capability
```

**223 không giải quyết trait logic hoàn chỉnh.** Nó chỉ tạo obligations và Type facts.

Vì vậy bước kế tiếp tự nhiên là phần khó nhất tiếp theo:

# BOOTSTRAP-224 — AXIOM TRAIT SOLVER & GENERIC CONSTRAINT ENGINE

Task này sẽ đặc tả đến mức implementation được:

```text
TraitDB
TraitGoal
ImplCandidate
CandidateSelection
Unification
Substitution
Associated Types
Associated Constants
Default Methods
Coherence
Orphan Rules
Negative reasoning
Auto traits
Cycle Detection
Recursive Obligations
Projection
Generic Constraints
Operator Resolution
Method Resolution
Dyn Trait Compatibility
Monomorphization Interface
Specialization Boundaries
```

Đặc biệt sẽ phải khóa một vấn đề nền tảng của Axiom:

```text
T: Trait
```

được compiler chứng minh **như thế nào**, và làm sao trait solver đủ mạnh cho generic programming nhưng **không biến Axiom thành một hệ thống type-level quá phức tạp và chậm**.