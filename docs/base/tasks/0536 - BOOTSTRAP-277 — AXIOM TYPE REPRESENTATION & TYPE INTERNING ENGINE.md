# BOOTSTRAP-277 — AXIOM TYPE REPRESENTATION & TYPE INTERNING ENGINE
**STATUS: FROZEN / COMPLETED**

## 1. Mục tiêu

Task này khóa **semantic type engine** của Axiom, làm nền cho:

```text
Name Resolution
      ↓
Type Representation
      ↓
Type Inference
      ↓
Trait Solver
      ↓
Overload Resolution
      ↓
Ownership / Capability Verification
      ↓
Layout / ABI
```

Nguyên tắc trung tâm:

> **Type identity là semantic identity; layout, ABI và machine representation là các lớp phía sau.**

Do đó phải tuyệt đối tránh thiết kế:

```text
TypeId == LayoutId == ABIType == MachineType
```

Thay vào đó:

```text
TypeId
   │
   ├── semantic properties
   │
   ├── generic structure
   │
   └── normalization
          │
          ▼
      LayoutQuery
          │
          ▼
       ABIQuery
          │
          ▼
       MachineType
```

---

# 2. Type system architecture

```text
                         TypeDB
                           │
              ┌────────────┼────────────┐
              ▼            ▼            ▼
        TypeInterner   TypeRelations   TypeNormalization
              │            │            │
              └────────────┼────────────┘
                           ▼
                       TypeId
                           │
             ┌─────────────┼──────────────┐
             ▼             ▼              ▼
        Type Checking   Trait Solver   Ownership
             │
             ▼
        LayoutDB / AbiDB
```

`TypeDB` là authoritative source cho semantic type identity.

---

# 3. TypeId

Canonical:

```text
TypeId
```

là compiler-local typed identifier.

Không dùng:

```text
pointer
string
AST node address
```

làm type identity.

Ví dụ:

```text
i32
User
Vec<i32>
Option<User>
```

mỗi type có `TypeId`.

---

# 4. TypeId ≠ source occurrence

Hai chỗ:

```text
let a: i32
let b: i32
```

có hai source occurrences nhưng cùng semantic:

```text
TypeId(i32)
```

Ngược lại:

```text
struct UserId(u64)
type UserIdAlias = u64
```

không được coi là cùng semantic type.

---

# 5. Type categories

Canonical:

```text
TypeKind
├── Primitive
├── Unit
├── Never
├── Tuple
├── Array
├── Slice
├── View
├── MutView
├── RawPointer
├── Struct
├── Enum
├── Trait
├── DynTrait
├── Function
├── Closure
├── GenericParam
├── AppliedGeneric
├── TypeAlias
├── AssociatedType
├── InferenceVar
└── ErrorType
```

Một số category có thể canonicalize thành dạng khác internally, nhưng semantic distinction phải rõ.

---

# 6. Primitive types

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

Special:

```text
unit
never
```

Future/library/compiler-supported:

```text
i128
u128
f16
bf16
```

không được thiết kế sao cho v1 TypeDB không thể mở rộng.

---

# 7. Primitive type identity

Mỗi primitive là canonical singleton:

```text
TypeId::Bool
TypeId::I32
TypeId::U64
...
```

Không tạo TypeId mới mỗi lần parser gặp `i32`.

---

# 8. Unit

`unit` là type có đúng một semantic value.

```text
()
```

mọi expression không trả giá trị hữu ích có thể có type:

```text
unit
```

Ví dụ:

```text
x = 10
```

assignment expression có:

```text
unit
```

---

# 9. Never

`never` biểu diễn computation không hoàn thành normally:

```text
loop {
}
```

hoặc:

```text
panic(...)
```

có thể có type:

```text
never
```

`never` có quan hệ coercion đặc biệt tới các expected types:

```text
never → T
```

vì expression không tạo runtime value.

Đây là **coercion semantic**, không phải subtype hierarchy tổng quát.

---

# 10. No general subtype system

Axiom không có:

```text
Object
Base
Derived
```

và không xây general subtype lattice.

Các quan hệ kiểu:

```text
never → T
Array<T,N> → view<T>
String → Str
```

là các coercion cụ thể được định nghĩa rõ.

Điều này giữ type solver đơn giản hơn và deterministic hơn.

---

# 11. Struct type

Ví dụ:

```text
struct Point {
    x: f32
    y: f32
}
```

Semantic type:

```text
StructType {
    declaration: DeclarationId
    generic_args: [...]
}
```

`Point` có nominal identity từ `DeclarationId`.

---

# 12. Nominal struct identity

Hai structs:

```text
struct A {
    x: i32
}

struct B {
    x: i32
}
```

không cùng type.

```text
TypeId(A) != TypeId(B)
```

dù layout có thể giống hệt.

---

# 13. Enum type

```text
enum Option<T> {
    Some(T)
    None
}
```

Semantic identity:

```text
EnumType {
    declaration: DeclarationId
    generic_args: [...]
}
```

`Option<i32>` và `Option<f64>` là các applied types khác nhau.

---

# 14. Generic parameter type

Trong:

```text
fn identity<T>(x: T) -> T
```

`T` có:

```text
GenericParamId
```

và type:

```text
GenericParamType {
    param: GenericParamId
}
```

Không dùng symbol string `T` để identity.

---

# 15. Generic parameter identity

Hai functions:

```text
fn a<T>(x: T) {}
fn b<T>(x: T) {}
```

không chia sẻ cùng generic type `T`.

Do đó:

```text
GenericParamId(a.T)
!=
GenericParamId(b.T)
```

Tên `T` chỉ là source spelling.

---

# 16. Applied generic type

Ví dụ:

```text
Vec<i32>
Option<User>
Map<String, i32>
```

semantic:

```text
AppliedType {
    constructor: TypeConstructor
    arguments: [TypeId...]
}
```

Canonical identity:

```text
constructor + canonical arguments
```

---

# 17. Generic constructor

Có thể biểu diễn:

```text
Vec<T>
```

là type constructor:

```text
Vec
```

và:

```text
Vec<i32>
```

là application.

Không nên coi `Vec<i32>` là một declaration mới.

---

# 18. Generic arity

Nếu:

```text
struct Pair<T, U> {}
```

thì:

```text
Pair<i32>
```

→ arity error.

Arity checking xảy ra trước hoặc trong generic application construction.

---

# 19. Type interning

TypeDB có:

```text
TypeInterner
```

Conceptual API:

```text
intern(TypeStructure) -> TypeId
get(TypeId) -> TypeStructure
```

Ví dụ:

```text
intern(Vec<i32>)
```

luôn trả cùng semantic `TypeId` trong một compiler snapshot.

---

# 20. Canonical type key

Interning key:

```text
TypeKey
```

Ví dụ:

```text
Primitive(i32)

Struct(User, [])

Struct(Vec, [i32])

Tuple([i32, f64])

Array(i32, 4)

View(i32)

MutView(i32)

Function([i32, i32], i32, effects)
```

Không chứa:

```text
SourceSpan
AST node address
documentation
comments
layout cache
machine register choice
```

---

# 21. Hash-consing

TypeDB nên sử dụng hash-consing/interning.

Ví dụ:

```text
Vec<i32>
```

được tạo ở 1000 nơi:

```text
TypeId = 42
```

thay vì 1000 objects semantic riêng biệt.

Lợi ích:

- equality nhanh;
- memory thấp;
- cache tốt;
- trait solver nhanh;
- incremental query tốt.

---

# 22. Type equality

Semantic type equality:

```text
same TypeId
```

sau canonicalization.

Không dùng:

```text
structural byte comparison
```

cho mọi type.

Nominal types phải giữ identity.

---

# 23. Alias

```text
type UserId = u64
```

là alias.

Semantic normalization:

```text
UserId → u64
```

nhưng declaration identity của alias vẫn tồn tại cho diagnostics/API/reflection.

---

# 24. Newtype

```text
struct UserId(u64)
```

là nominal distinct type:

```text
UserId != u64
```

Mặc dù:

```text
@repr(transparent)
```

có thể khiến representation/ABI tương đương.

Đây là ví dụ trực tiếp cho:

> semantic type ≠ physical representation.

---

# 25. Alias normalization

Type checker có thể cần:

```text
normalize(UserIdAlias)
```

để lấy:

```text
u64
```

Nhưng normalization không được mutate source AST.

---

# 26. Type normalization

Có hai khái niệm:

### Alias normalization

```text
type A = B
A → B
```

### Associated type normalization

```text
<T as Iterator>::Item
→ concrete type
```

Cả hai phải đi qua TypeDB/TraitDB contracts.

---

# 27. Do not over-normalize

Không được biến:

```text
struct UserId(u64)
```

thành:

```text
u64
```

chỉ vì representation giống nhau.

`repr(transparent)` chỉ ảnh hưởng layout/ABI.

---

# 28. Tuple types

```text
(i32, f64)
```

structural type.

Canonical:

```text
TupleType([i32, f64])
```

Hai tuple cùng element types:

```text
(i32, f64)
(i32, f64)
```

cùng TypeId.

---

# 29. Empty tuple

```text
()
```

canonicalize thành:

```text
unit
```

Không cần tạo TupleType([]) riêng nếu semantic contract chọn unit canonical.

---

# 30. Fixed arrays

Axiom canonical syntax:

```text
[4]i32
```

semantic:

```text
ArrayType {
    element: i32
    length: ConstValue(4)
}
```

Length là compile-time value.

---

# 31. Array length

Không chỉ integer literal.

Có thể:

```text
const N: usize = 4

[N]i32
```

sau comptime evaluation:

```text
N → 4
```

Type identity dùng canonical const value.

---

# 32. Dynamic array

`Vec<T>` không phải Core type.

Nó là library-defined struct.

Điều này rất quan trọng:

```text
[4]i32
```

là Core semantic type.

```text
Vec<i32>
```

là ordinary generic type.

Compiler vẫn có thể optimize `Vec` đặc biệt thông qua known library metadata/intrinsics.

---

# 33. Slice/view types

Canonical:

```text
view<T>
mut_view<T>
```

### `view<T>`

Read-only capability.

### `mut_view<T>`

Exclusive mutable capability.

Chúng là **semantic access types**, không chỉ syntax sugar.

---

# 34. View type identity

```text
view<i32>
```

và:

```text
mut_view<i32>
```

khác nhau.

```text
TypeId(view<i32>)
!=
TypeId(mut_view<i32>)
```

Access semantics không được encode chỉ trong hidden flag.

---

# 35. View is not reference

Axiom không có:

```text
&T
&mut T
```

trong safe Core.

`view<T>` biểu diễn semantic capability:

```text
owner/provenance
+
region
+
READ
+
lifetime
```

Physical representation có thể:

```text
pointer + length
```

nhưng không phải semantic definition.

---

# 36. MutView

`mut_view<T>` mang semantic WRITE capability.

Compiler phải track:

```text
owner
region
access=WRITE
```

và enforce:

```text
no conflicting READ/WRITE
no WRITE/WRITE overlap
```

Type representation alone không đủ để đảm bảo điều này.

---

# 37. Raw pointer types

System layer:

```text
*const T
*mut T
```

TypeDB phải represent:

```text
RawPointerType {
    pointee: TypeId
    mutable: bool
}
```

Raw pointer không có ownership semantics.

---

# 38. Raw pointer vs view

```text
*mut T
```

không tự động convert:

```text
mut_view<T>
```

Phải qua unsafe contract.

```text
unsafe {
    make_mut_view(p, len)
}
```

sau đó verifier tiếp tục track capability.

---

# 39. Function type

Semantic function type:

```text
FunctionType {
    params: [TypeId]
    result: TypeId
    effects: EffectSet
    calling_convention: CallingConvention
}
```

Calling convention có thể mặc định là Axiom.

---

# 40. Effects are part of callable semantics

Theo behavior model:

```text
fn f() -> i32
```

và một function có observable external effects không nên bị coi semantic-equivalent chỉ dựa trên parameter/result types.

Do đó FunctionType phải có hoặc liên kết tới:

```text
EffectSignature
```

Tuy nhiên implementation có thể intern effect set riêng.

---

# 41. Function type ≠ function declaration

```text
fn add(a: i32, b: i32) -> i32
```

có:

```text
FunctionId
```

và:

```text
FunctionType(i32,i32)->i32
```

Hai functions có thể cùng FunctionType nhưng khác DeclarationId.

---

# 42. Function pointer

Nếu Axiom hỗ trợ:

```text
fn(i32) -> i32
```

đây là function-value type.

Function declaration identity không được nhúng vào function type.

---

# 43. Closure type

Mỗi closure expression có anonymous semantic type:

```text
ClosureType {
    closure: ClosureId
}
```

Ví dụ:

```text
let f = |x| x + offset
```

closure type unique.

Hai closure có cùng signature:

```text
|x| x + 1
|x| x * 2
```

không cùng concrete closure type.

---

# 44. Closure callable traits

Closure type có compiler-derived facts:

```text
Fn
FnMut
FnOnce
```

và:

```text
Send
Share
Copy
Drop
```

nếu thích hợp.

Những facts không làm thay đổi closure identity.

---

# 45. Dyn Trait

```text
dyn Display
```

là dynamic trait type.

Semantic:

```text
DynTraitType {
    trait: TraitId
    args: [...]
    auto_properties: [...]
}
```

Dynamic dispatch explicit.

---

# 46. `dyn Trait` ≠ concrete type

Nếu:

```text
User: Display
```

thì:

```text
User
```

không phải:

```text
dyn Display
```

Implicit boxing/erasure không xảy ra.

Phải có explicit coercion/conversion theo ABI/ownership rules.

---

# 47. Trait type

Trait declaration:

```text
trait Display { ... }
```

có:

```text
TraitId
```

Nhưng `Display` như constraint/type context không nhất thiết là runtime value.

TypeDB phải phân biệt:

```text
TraitId
```

và:

```text
DynTraitType
```

---

# 48. Trait object safety

`dyn Trait` legality được TraitDB kiểm tra.

Type construction có thể tạo candidate:

```text
DynTrait(Display)
```

nhưng final validity:

```text
object_safe(Display)
```

được trait solver xác nhận.

---

# 49. Associated type

Ví dụ:

```text
<T as Iterator>::Item
```

semantic:

```text
AssociatedTypeProjection {
    trait: TraitId
    self_type: TypeId
    assoc: AssociatedTypeId
}
```

Đây có thể là unresolved projection cho tới khi trait solver normalize.

---

# 50. Associated type ≠ declaration lookup

`Item` ở:

```text
<T as Iterator>::Item
```

không được resolver xử lý như:

```text
module::Item
```

Resolution layer chỉ tạo qualified semantic reference.

TraitDB/TypeDB hoàn tất projection.

---

# 51. `Self`

Trong:

```text
trait Foo {
    fn clone(self: view<Self>) -> Self
}
```

`Self` là implicit generic-like parameter.

Type:

```text
SelfType
```

gắn với `TraitId`/`ImplId` context.

---

# 52. Recursive types

Ví dụ:

```text
struct Node {
    next: Node
}
```

Type representation có thể xây:

```text
Node
```

reference tới itself.

Nhưng layout:

```text
size(Node)
```

không terminate.

Type well-formedness/layout phase phải reject.

---

# 53. Legal recursive type

```text
struct Node {
    next: Box<Node>
}
```

`Box<Node>` cung cấp indirection.

Type system cho phép recursive semantic graph.

Layout thấy:

```text
Node
 └── Box<Node>
```

với finite representation.

---

# 54. Recursive type graph

TypeDB phải hỗ trợ graph:

```text
Type A
 ↓
Type B
 ↓
Type A
```

Không recursive-expand vô hạn trong `TypeId` construction.

Interned types tham chiếu bằng IDs.

---

# 55. Type well-formedness

Tối thiểu:

```text
TypeWF:
- known declaration
- correct generic arity
- valid generic arguments
- no invalid associated projection
- no invalid raw pointer target
- no invalid dyn trait
- no illegal recursive by-value type
- valid const generic arguments
```

---

# 56. Target-independent TypeId

`TypeId` semantic không phụ thuộc:

```text
x86-64
ARM64
RV64
WASM
```

Ví dụ:

```text
i32
```

là cùng semantic type.

Physical layout:

```text
size
alignment
ABI
register class
```

là target query.

---

# 57. Target-dependent facts

Query:

```text
size_of(TypeId, TargetId)
align_of(TypeId, TargetId)
abi_class(TypeId, TargetId)
```

Không lưu target layout vào TypeId.

---

# 58. DataLayout separation

Architecture:

```text
TypeDB
  ↓
SemanticType
  ↓
LayoutDB.query(TypeId, TargetId)
```

LayoutDB có thể trả:

```text
Layout {
    size
    alignment
    fields
    niche
    scalar_pair
    abi_properties
}
```

Nhưng layout không trở thành semantic type identity.

---

# 59. Representation-changing optimization

Ví dụ:

```text
struct Pair {
    a: i32
    b: i32
}
```

Compiler có thể scalarize:

```text
Pair
→ SSA a
→ SSA b
```

Type vẫn là `Pair`.

Không được để optimization thay đổi TypeId.

---

# 60. Type interning and revisions

Type interner có thể persist qua revisions.

Nếu semantic declaration không đổi:

```text
User
```

có thể reuse TypeId/internal interned node.

Nhưng cross-revision identity không được coi là public stable identity.

---

# 61. ErrorType

Partial Semantic Mode cần:

```text
ErrorType
```

nhưng:

> `ErrorType` không bao giờ là proven valid production type.

Ví dụ:

```text
let x: UnknownType
```

AST recovery:

```text
ErrorType
```

để tiếp tục IDE analysis.

Verified MIR không được chứa unresolved ErrorType.

---

# 62. InferenceVar

Type inference cần:

```text
InferenceVarId
```

Ví dụ:

```text
let x = []
```

có thể tạo:

```text
?T
```

Inference variable.

Nhưng:

```text
InferenceVar
```

không phải language-level type observable trong compiled program.

---

# 63. Inference variable identity

Mỗi inference variable:

```text
InferenceVarId
```

unique trong inference session/query.

Không intern inference variables globally như concrete types.

---

# 64. Type substitution

Generic instantiation:

```text
<T> → <i32>
```

dùng:

```text
Substitution {
    GenericParamId → TypeId
}
```

Ví dụ:

```text
identity<T>
```

instantiate:

```text
T → i32
```

→ function type:

```text
(i32) -> i32
```

---

# 65. Substitution must be immutable

Không mutate generic declaration:

```text
T = i32
```

thay vào đó:

```text
GenericInstanceId
Substitution
```

được tạo.

---

# 66. Generic instance identity

Canonical:

```text
GenericInstance {
    declaration
    substitutions
}
```

Hai lần:

```text
Vec<i32>
```

→ same canonical instance identity.

---

# 67. Type normalization cycle

Associated type normalization có thể tạo:

```text
A::X
→ B::Y
→ A::X
```

Trait solver phải detect cycle.

Cycle không được:

```text
stack overflow
```

và cũng không được tự coi là proven.

---

# 68. Type equality during inference

Phải phân biệt:

```text
TypeEquals
Subtype/Coercible
Unifiable
Assignable
RepresentationallyEquivalent
```

Ví dụ:

```text
UserId
```

và:

```text
u64
```

có thể representation-equivalent nhưng:

```text
TypeEquals = false
```

---

# 69. Coercion

Coercion là relation:

```text
Coerce(T, U)
```

được định nghĩa hữu hạn.

Ví dụ:

```text
never → T
Array<T,N> → view<T>
String → Str
```

Không tạo general implicit conversion graph vô hạn.

---

# 70. Cast

`as`:

```text
x as u64
```

là explicit semantic conversion.

Type checker kiểm tra legality.

TypeDB chỉ represent source/target types.

---

# 71. Bitcast

```text
bitcast<T>(x)
```

cần type facts:

- same size;
- valid alignment;
- representation validity.

Những điều này nằm giữa TypeDB/LayoutDB/Verifier.

Không coi `bitcast` là ordinary coercion.

---

# 72. Type properties

Compiler-derived properties:

```text
TypeProperties {
    Copy
    Drop
    Send
    Share
    Sized
    FfiSafe
    GpuLegal
}
```

Nhưng không nên lưu tất cả như mutable flags trong `Type`.

Mỗi property nên là query/fact:

```text
is_copy(TypeId)
is_send(TypeId)
...
```

để dependency tracking chính xác.

---

# 73. Copy property

`Copy` semantic:

```text
copy(x)
```

không tạo additional ownership obligation.

Type checker/verifier dùng:

```text
Copy(TypeId)
```

để quyết định Move vs Copy semantics.

---

# 74. Drop property

Nếu:

```text
Drop(T)
```

thì:

```text
Copy(T) = false
```

theo frozen ownership rules.

Nhưng `Drop` không đồng nghĩa:

```text
heap allocation
```

---

# 75. Sized

`Sized` nghĩa semantic representation có known compile-time size trong relevant context.

Một số types:

```text
dyn Trait
view<T>
```

có thể có special representation/size rules.

TypeDB phải expose:

```text
sized_status(TypeId)
```

không tự assume mọi type đều Sized.

---

# 76. Unsized types

Nếu Axiom Core cần:

```text
str-like
dyn Trait
```

thì semantic type có thể unsized.

Nhưng chúng thường được accessed qua:

```text
view<T>
```

hoặc explicit dynamic representation.

Do đó unsized không cần programmer-facing pointer complexity.

---

# 77. Type constructor metadata

Declaration metadata:

```text
GenericDeclaration {
    params
    constraints
}
```

Ví dụ:

```text
struct Vec<T> {}
```

TypeDB biết:

```text
constructor = Vec
arity = 1
param kind = Type
```

TraitDB xử lý constraints.

---

# 78. Const generic parameters

Ban đầu hỗ trợ:

```text
const N: usize
```

và scalar types:

```text
bool
integer types
```

Ví dụ:

```text
struct Array<T, const N: usize> {}
```

Type application:

```text
Array<i32, 4>
```

cần canonical const argument.

---

# 79. Const arguments

Không biểu diễn:

```text
"4"
```

như source string.

Dùng:

```text
ConstValue {
    type
    value
}
```

Ví dụ:

```text
4usize
```

canonical.

---

# 80. Type fingerprints

Type semantic fingerprint:

```text
TypeFingerprint
```

được xây từ canonical semantic structure.

Ví dụ:

```text
Struct(
    package identity,
    declaration semantic identity,
    generic args
)
```

Không hash:

```text
memory address
layout cache
machine register allocation
```

---

# 81. Public type fingerprint

Public ABI/API fingerprint phải có thêm:

```text
package identity
declaration identity
public generic structure
repr/ABI contracts when relevant
```

để binary compatibility kiểm tra chính xác.

---

# 82. TypeDB API

Implementation-ready:

```text
type_of_expr(...)
type_of_decl(...)
type_kind(TypeId)
type_args(TypeId)
type_constructor(TypeId)
type_params(DeclarationId)
normalize(TypeId)
substitute(TypeId, Substitution)
is_equal(a, b)
can_coerce(a, b)
is_copy(T)
is_drop(T)
is_send(T)
is_share(T)
is_sized(T)
is_ffi_safe(T, ABI)
is_gpu_legal(T, Target)
```

---

# 83. Canonical construction API

Không cho compiler subsystem tự tạo `TypeId` bằng cách:

```text
TypeId(random_integer)
```

Mọi concrete type phải đi qua:

```text
TypeDB.intern(...)
```

Inference variables là ngoại lệ có allocator riêng.

---

# 84. TypeDB storage

Kiến trúc:

```text
TypeDB
├── TypeInterner
├── TypeStorage
├── GenericInstanceDB
├── SubstitutionDB
├── TypeNormalizationDB
├── TypePropertyQueries
├── TypeFingerprintDB
└── InferenceSessionDB
```

Tất cả nằm dưới CompilerDB query infrastructure.

Không tạo cache độc lập ngoài dependency system.

---

# 85. Type normalization query

```text
normalize(TypeId) -> NormalizedType
```

`NormalizedType` có thể:

```text
Known(TypeId)
Unresolved(TypeId)
Ambiguous
Cycle
Error
```

Partial Semantic Mode không được biến:

```text
Unresolved
```

thành:

```text
Known
```

---

# 86. Type relation engine

Tạo một abstraction:

```text
TypeRelation
├── Equal
├── Unify
├── Coerce
├── Castable
├── Bitcastable
└── RepresentationallyEquivalent
```

Mỗi relation có preconditions riêng.

Không có một function khổng lồ:

```text
is_compatible(a,b)
```

vì dễ làm semantics mơ hồ.

---

# 87. Unification

Type inference sử dụng:

```text
unify(?T, i32)
```

→:

```text
?T := i32
```

nhưng:

```text
unify(i32, f64)
```

→ failure.

Unification không tự áp dụng arbitrary coercions.

---

# 88. Coercion ≠ unification

Ví dụ:

```text
let x: view<i32> = array
```

có thể:

```text
Array<i32,N>
→ view<i32>
```

nhưng inference không được coi:

```text
Array<i32,N> == view<i32>
```

---

# 89. Type inference interaction

Pipeline:

```text
Resolve names
     ↓
Construct initial types
     ↓
Create inference variables
     ↓
Generate constraints
     ↓
Unify
     ↓
Apply coercions
     ↓
Trait obligations
     ↓
Defaulting / finalization
     ↓
Fully typed HIR
```

TypeDB cung cấp type representation; inference engine giải constraints.

---

# 90. Type defaulting

Nếu:

```text
let x = 42
```

không có contextual type, Axiom cần deterministic literal default rule.

Ví dụ có thể:

```text
integer literal default → i32
float literal default → f64
```

Đây là language semantic decision.

Không để target CPU quyết định.

---

# 91. Numeric literals are not immediately typed

Lexer tạo:

```text
IntegerLiteral
```

Type inference có thể xem:

```text
IntegerLiteralValue(42)
```

với expected type.

Điều này cho phép:

```text
let x: u64 = 42
```

mà không cần cast.

---

# 92. Type error

Compiler diagnostic:

```text
TYPE-E001 TypeMismatch
```

phải chứa:

```text
expected
found
source spans
constraint path
```

Ví dụ:

```text
expected:
    u64

found:
    String
```

và explanation:

```text
assignment requires destination type
```

---

# 93. Type explanation

AXCP:

```text
explain_type(TypeId)
explain_type_mismatch(...)
explain_coercion(...)
explain_normalization(...)
```

AI có thể nhận:

```text
Type:
    Vec<i32>

Constructor:
    Vec<T>

T:
    i32

Properties:
    Drop
    Send
    !Copy

Layout:
    target-dependent
```

---

# 94. Type and ownership separation

`TypeDB` nói:

```text
Vec<i32> is !Copy
```

Ownership verifier nói:

```text
this particular value of Vec<i32> has been moved
```

Không trộn:

```text
Type property
```

với:

```text
Value state
```

---

# 95. Type and capability separation

Type:

```text
view<i32>
```

nói đây là capability-bearing type.

Nhưng verifier vẫn phải track:

```text
which owner
which region
which lifetime
```

TypeDB không lưu runtime/source-specific capability state.

---

# 96. Type and layout separation

Ví dụ:

```text
struct S {
    a: u8
    b: u64
}
```

TypeDB:

```text
S
```

LayoutDB:

```text
size
alignment
offset(a)
offset(b)
padding
```

Target khác nhau có thể layout khác.

---

# 97. Type and ABI separation

```text
fn f(S) -> S
```

TypeDB:

```text
FunctionType(S) -> S
```

ABI DB có thể quyết định:

```text
pass by registers
pass indirectly
sret
aggregate split
```

Type system không chứa ABI calling convention details.

---

# 98. Type and GPU separation

`f32` cùng semantic type trên CPU/GPU.

GPU backend có:

```text
GpuLegal(f32)
GpuLayout(S)
```

nhưng không tạo:

```text
GpuF32
```

trừ khi semantic distinction thực sự cần.

---

# 99. Type graph

CompilerDB có thể maintain:

```text
TypeGraph
```

edges:

```text
contains
generic_argument
associated_projection
alias_target
function_parameter
function_result
field_type
variant_payload
```

Phục vụ:

- dependency analysis;
- recursive type checking;
- diagnostics;
- IDE;
- incremental compilation.

---

# 100. Type dependency cycles

Graph cycle không luôn là lỗi.

Ví dụ:

```text
Box<Node>
```

hợp lệ.

Nhưng:

```text
Node contains Node by value
```

không hợp lệ vì finite layout không tồn tại.

Do đó cycle legality thuộc **size/representation analysis**, không chỉ graph cycle detection.

---

# 101. Type construction algorithm

Khi gặp:

```text
Option<User>
```

resolver/type checker:

```text
Option → DeclarationId
User   → DeclarationId
```

TypeDB:

```text
Option + [UserType]
    ↓
canonical TypeKey
    ↓
intern
    ↓
TypeId
```

Không tạo anonymous struct.

---

# 102. Type alias example

```text
type UserId = u64

fn get(x: UserId) {}
```

Resolution:

```text
UserId → TypeAliasDecl
```

TypeDB:

```text
TypeId(UserIdAlias)
```

Normalization:

```text
UserIdAlias → u64
```

Type equality sau normalization:

```text
UserId == u64
```

theo alias semantics.

---

# 103. Newtype example

```text
struct UserId(u64)
```

TypeDB:

```text
UserId ≠ u64
```

Ngay cả:

```text
@repr(transparent)
```

cũng không thay đổi equality.

---

# 104. Generic example

```text
fn first<T>(x: view<T>) -> T
```

Trong generic body:

```text
T = GenericParamType(T)
```

Call:

```text
first<i32>(...)
```

instantiation:

```text
T → i32
```

Function instance:

```text
first<i32>
```

---

# 105. Trait bound example

```text
fn max<T: Ord>(a: T, b: T) -> T
```

TypeDB:

```text
T : GenericParam
```

TraitDB:

```text
Ord(T)
```

Type inference:

```text
T := i32
```

Trait solver:

```text
Proven Ord(i32)
```

Ba hệ thống phối hợp nhưng không nhập thành một subsystem.

---

# 106. Closure example

```text
let offset = 10

let f = |x| x + offset
```

TypeDB tạo:

```text
ClosureType(ClosureId #1)
```

CaptureDB:

```text
offset: READ
```

Inference:

```text
x : ?T
offset : integer
```

Type constraints xác định final closure callable type.

---

# 107. Dyn trait example

```text
let x: dyn Display = ...
```

TypeDB:

```text
DynTrait(Display)
```

TraitDB:

```text
Display object-safe?
```

ABI/representation:

```text
dynamic trait representation
```

Ownership/capability:

```text
does x own?
can x be shared?
```

được xử lý bởi các subsystem tương ứng.

---

# 108. Type cache correctness

Type interning cache phải invalidate khi semantic declaration thay đổi.

Ví dụ:

```text
struct User {
    id: u64
}
```

đổi thành:

```text
struct User {
    id: u64
    name: String
}
```

`User` semantic fingerprint thay đổi.

TypeId có thể được reused internally only if compiler revision model guarantees coherent meaning; otherwise revision-scoped TypeId.

Khuyến nghị:

> **TypeId is valid within a CompilerDB snapshot/revision domain.**

---

# 109. Persistent identity

Không dùng TypeId làm `.axmeta` public identity.

`.axmeta` dùng:

```text
TypeFingerprint
Declaration identity
Package identity
```

TypeId chỉ là compiler-local handle.

---

# 110. TypeDB and query engine

Ví dụ:

```text
type_of_expression(ExpressionId)
```

dependencies:

```text
Expression syntax
Resolution result
Expected type
Generic environment
Trait obligations
Literal context
```

Query engine từ BOOTSTRAP-274 tự track dependencies.

Type checker không tự tạo cache riêng.

---

# 111. Parallelism

Các type queries độc lập có thể chạy song song.

Ví dụ:

```text
fn a() -> i32
fn b() -> String
fn c() -> Vec<f64>
```

có thể type-check parallel.

Interning phải thread-safe nhưng semantic result deterministic.

---

# 112. Type interner synchronization

Có thể dùng:

- sharded maps;
- concurrent hash map;
- per-worker local interner + deterministic merge;
- arena + canonical hash table.

Implementation choice.

Invariant:

```text
same canonical TypeKey
→ same semantic Type identity
```

trong một snapshot.

---

# 113. Type database must not know machine code

TypeDB không được import:

```text
x86 register allocator
ARM instruction selector
ELF relocation
```

Target layout queries đi qua:

```text
LayoutDB
AbiDB
TargetDB
```

---

# 114. Error handling

Type queries trả:

```text
TypeResult
├── Known(TypeId)
├── Unknown
├── Ambiguous
├── Error(TypeErrorId)
└── Incomplete
```

Không dùng `null`.

---

# 115. Partial Semantic Mode

Ví dụ:

```text
fn foo(x: UnknownType) {}
```

IDE có thể tạo:

```text
UnknownType
```

để tiếp tục:

```text
foo(...)
```

nhưng:

```text
Verified MIR
```

không được chứa unresolved type.

---

# 116. Type well-formedness boundary

Pipeline:

```text
AST
 ↓
Resolution
 ↓
Type Construction
 ↓
Type WF
 ↓
Inference
 ↓
Trait Constraints
 ↓
Fully Typed HIR
```

Không cho invalid TypeId đi sâu vào backend.

---

# 117. Type lowering

Sau type checking:

```text
Typed HIR
    ↓
Semantic Type
    ↓
Layout Query
    ↓
ABI Classification
    ↓
ABI MIR
```

Đây chính là boundary đã khóa trong architecture trước.

---

# 118. Required implementation modules

Khuyến nghị:

```text
compiler/
└── semantic/
    └── types/
        ├── mod.ax
        ├── type_id.ax
        ├── type_kind.ax
        ├── primitive.ax
        ├── nominal.ax
        ├── generic.ax
        ├── tuple.ax
        ├── array.ax
        ├── view.ax
        ├── pointer.ax
        ├── function.ax
        ├── closure.ax
        ├── dyn_trait.ax
        ├── projection.ax
        ├── inference.ax
        ├── substitution.ax
        ├── normalization.ax
        ├── interner.ax
        ├── relations.ax
        ├── properties.ax
        ├── fingerprint.ax
        ├── well_formed.ax
        └── tests/
```

---

# 119. Implementation order

Agent nên làm:

```text
1. TypeId
2. TypeKind
3. Primitive singleton types
4. TypeInterner
5. Nominal struct/enum
6. Generic parameters
7. Generic applications
8. Tuple/Array
9. View/MutView
10. Raw pointers
11. Function types
12. Closure types
13. DynTrait
14. Associated projections
15. Type aliases
16. Substitution
17. Normalization
18. Type relations
19. Type properties
20. Type fingerprints
21. Well-formedness
22. CompilerDB integration
23. Incremental tests
24. Fuzz/property tests
```

---

# 120. Conformance tests

### Primitive identity

```text
i32 == i32
i32 != u32
```

### Nominal

```text
A != B
```

### Alias

```text
type A = i32
A == i32
```

### Newtype

```text
struct A(i32)
A != i32
```

### Generic

```text
Vec<i32> == Vec<i32>
Vec<i32> != Vec<u32>
```

### Arrays

```text
[4]i32 != [8]i32
```

### Views

```text
view<i32> != mut_view<i32>
```

### Functions

```text
(i32)->i32 != (f64)->f64
```

### Closure

Hai closure expression khác nhau → distinct concrete closure types.

### Recursive

```text
Box<Node> valid
Node { next: Node } invalid
```

---

# 121. Adversarial tests

Phải test:

```text
deep generic nesting
Vec<Vec<Vec<...>>>
deep aliases
alias cycles
associated-type cycles
recursive types
large tuples
large generic substitutions
large const generic values
many inference variables
massive trait projections
dyn trait combinations
```

Mục tiêu:

```text
no stack overflow
no exponential accidental behavior
no infinite normalization
no nondeterministic TypeId semantics
```

---

# 122. Alias cycles

Ví dụ:

```text
type A = B
type B = A
```

Normalization:

```text
A → B → A
```

phải phát hiện cycle:

```text
TYPE-E020 CyclicTypeAlias
```

Không recurse vô hạn.

---

# 123. Generic recursive aliases

Ví dụ:

```text
type A<T> = B<T>
type B<T> = A<T>
```

phải detect canonical cycle theo:

```text
TypeAliasDeclaration
+
GenericSubstitution
```

không chỉ string name.

---

# 124. Type interner invariants

```text
A type key has one canonical TypeId within a coherent compiler snapshot.

Interning does not depend on source span.

Interning does not depend on worker count.

Interning does not depend on memory address.

Interning does not encode target layout.

Interning does not encode register allocation.

Interning does not erase nominal identity.
```

---

# 125. Frozen invariants

```text
ATYPE-20
Every semantic type has a compiler-local TypeId.

ATYPE-21
Type identity is distinct from source occurrence identity.

ATYPE-22
Type identity is distinct from physical representation.

ATYPE-23
Type identity is distinct from target-specific layout.

ATYPE-24
Type identity is distinct from ABI classification.

ATYPE-25
Primitive types have canonical identities.

ATYPE-26
Nominal struct types are identified by declaration identity.

ATYPE-27
Nominal enum types are identified by declaration identity.

ATYPE-28
Type aliases do not create distinct nominal types.

ATYPE-29
Newtypes create distinct nominal types.

ATYPE-30
Transparent representation does not erase nominal type identity.

ATYPE-31
Generic parameter identity uses GenericParamId.

ATYPE-32
Generic application identity is constructor plus canonical arguments.

ATYPE-33
Concrete generic types are interned.

ATYPE-34
Equivalent canonical type structures produce equivalent interned types.

ATYPE-35
Tuple types are structural.

ATYPE-36
Fixed arrays encode element type and compile-time length.

ATYPE-37
Array length participates in type identity.

ATYPE-38
view<T> and mut_view<T> are distinct semantic types.

ATYPE-39
Raw pointers are distinct from safe views.

ATYPE-40
Raw pointer types carry no ownership semantics.

ATYPE-41
Function declaration identity is distinct from function type identity.

ATYPE-42
Function effects participate in callable semantic contracts.

ATYPE-43
Each closure expression has a distinct concrete closure type.

ATYPE-44
dyn Trait is explicit dynamic type erasure.

ATYPE-45
Concrete types do not implicitly become dyn Trait.

ATYPE-46
Trait object safety is validated outside basic type construction.

ATYPE-47
Associated type projections are distinct from ordinary name lookup.

ATYPE-48
Self is represented as a semantic type parameter in its defining context.

ATYPE-49
Recursive semantic type graphs are supported.

ATYPE-50
Infinite-size by-value recursive types are rejected.

ATYPE-51
Indirection can make recursive types representable.

ATYPE-52
Type aliases are normalized without mutating source syntax.

ATYPE-53
Alias normalization detects cycles.

ATYPE-54
Associated-type normalization detects cycles.

ATYPE-55
Inference variables are distinct from concrete interned language types.

ATYPE-56
Inference variables are session-scoped.

ATYPE-57
Substitution is explicit and immutable.

ATYPE-58
Const generic arguments are canonical compile-time values.

ATYPE-59
Type equality is distinct from coercibility.

ATYPE-60
Type equality is distinct from representational equivalence.

ATYPE-61
Unification does not implicitly perform arbitrary coercion.

ATYPE-62
Coercion rules are explicit and finite.

ATYPE-63
Type properties are compiler-derived semantic facts.

ATYPE-64
Copy is distinct from Drop.

ATYPE-65
Send is distinct from Share.

ATYPE-66
Type properties do not encode individual value ownership state.

ATYPE-67
Type properties do not encode individual capability provenance.

ATYPE-68
ErrorType exists only for partial/error recovery.

ATYPE-69
ErrorType cannot enter Verified MIR.

ATYPE-70
Unknown type information is never treated as proven.

ATYPE-71
Type fingerprints are deterministic.

ATYPE-72
Type fingerprints do not depend on physical memory addresses.

ATYPE-73
Type fingerprints do not depend on worker count.

ATYPE-74
TypeIds are compiler-local identities.

ATYPE-75
TypeIds are not persistent ABI identities.

ATYPE-76
Persistent metadata uses semantic fingerprints/declaration identities.

ATYPE-77
TypeDB is the authoritative owner of semantic type identity.

ATYPE-78
All concrete TypeIds are created through canonical TypeDB construction.

ATYPE-79
Type interning is deterministic.

ATYPE-80
Type interning is independent of target machine.

ATYPE-81
TypeDB does not contain machine register allocation decisions.

ATYPE-82
TypeDB does not contain object-file representation decisions.

ATYPE-83
Target-dependent size/alignment is queried through LayoutDB.

ATYPE-84
Target-dependent ABI classification is queried through AbiDB.

ATYPE-85
Semantic type identity remains stable under physical optimization.

ATYPE-86
SSA scalarization does not change semantic TypeId.

ATYPE-87
GPU legality is a separate semantic property query.

ATYPE-88
FFI safety is a separate semantic property query.

ATYPE-89
Type normalization preserves nominal identity.

ATYPE-90
Type relation operations are explicit and distinct.

ATYPE-91
Resolution, typing, trait solving and ownership remain separate compiler responsibilities.

ATYPE-92
Type queries use CompilerDB query infrastructure.

ATYPE-93
Type caches are dependency-driven.

ATYPE-94
Full and incremental type construction are semantically equivalent.

ATYPE-95
Parallel type queries are deterministic.

ATYPE-96
Invalid type states cannot cross the production semantic boundary.

ATYPE-97
Type well-formedness is checked before Verified MIR.

ATYPE-98
No subsystem may invent an independent TypeId identity system.

ATYPE-99
Type representation is independent of Axiom runtime presence.

ATYPE-100
Type semantics do not require garbage collection, object headers or mandatory runtime support.
```

---

# 126. Kiến trúc compiler sau BOOTSTRAP-277

Đến đây frontend/semantic pipeline đã thành:

```text
Source
  ↓
Lexer
  ↓
Lossless Syntax
  ↓
Parser
  ↓
AST
  ↓
Module / Declaration Collection
  ↓
Name Resolution
  ↓
Type Representation / Interning
  ↓
Type Inference
  ↓
Trait Constraints
  ↓
Method / Overload Resolution
  ↓
Typed HIR
  ↓
Ownership / Capability Verification
  ↓
MIR
```

Và các database:

```text
CompilerDB
├── SourceDB
├── SyntaxDB
├── ModuleDB
├── DeclarationDB
├── SymbolDB
├── ScopeDB
├── ImportDB
├── ResolutionDB
├── TypeDB                 ← 277
├── TraitDB
├── GenericDB
├── ConstDB
├── ComptimeDB
├── HIRDB
├── MIRDB
├── VerificationDB
├── LayoutDB
├── AbiDB
├── CodegenDB
└── BuildDB
```

Điểm đáng chú ý là **TypeDB không chứa layout**, và **TypeDB cũng không chứa ownership state của từng value**. Đây là ba tầng độc lập:

```text
             TYPE
              │
       "Cái này là gì?"
              │
              ▼
           VALUE
              │
       "Value này đang
        owned/moved?"
              │
              ▼
         CAPABILITY
              │
       "Ai được access
        vùng nào?"
              │
              ▼
          LAYOUT/ABI
              │
       "Máy thực tế biểu
        diễn nó thế nào?"
```

Đây là cách giữ được mục tiêu của Axiom: **ngôn ngữ có semantic model mạnh, nhưng programmer không phải gánh complexity của compiler.**

### Task kế tiếp: **BOOTSTRAP-278 — AXIOM TYPE INFERENCE, CONSTRAINT GENERATION & OVERLOAD RESOLUTION**

Task này sẽ giải quyết phần thực sự “thông minh” của type system:

- bidirectional typing;
- expected type;
- inference variables;
- constraint generation;
- unification;
- numeric literal inference;
- generic inference;
- coercion insertion;
- overload candidate collection;
- overload ranking;
- ambiguity;
- method resolution;
- trait obligations;
- associated type constraints;
- closure parameter inference;
- return type inference;
- `?` typing;
- `match` branch type unification;
- block expression typing;
- deterministic inference;
- diagnostics giải thích **tại sao compiler chọn type/function đó**.