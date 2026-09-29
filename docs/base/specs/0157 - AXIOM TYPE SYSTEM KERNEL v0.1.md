# AXIOM TYPE SYSTEM KERNEL v0.1

Bây giờ đi vào phần quan trọng nhất sau resolver: **type system kernel**.

Mục tiêu của Axiom không phải là có type system “càng thông minh càng tốt”, mà là:

> **Type system đủ mạnh để compiler chứng minh chương trình an toàn, nhưng không biến source code thành một bài toán type-level programming.**

Ta tiếp tục giữ nguyên nguyên tắc:

> **Compiler có thể phức tạp. Programmer không cần nhìn thấy sự phức tạp đó.**

---

# 1. Kiến trúc Type System

Pipeline:

```text
Resolved HIR
    │
    ▼
Type Environment
    │
    ├── Type Interner
    ├── Type Equality
    ├── Generic Substitution
    ├── Type Inference
    ├── Constraint Generation
    └── Constraint Solving
            │
            ▼
       Typed HIR
```

Không để type checker trực tiếp thao tác với AST.

---

# 2. TypeId là trung tâm

Compiler không nên truyền type dưới dạng cây object:

```text
Type {
    kind: ...
    ...
}
```

khắp compiler.

Dùng:

```text
TypeId
```

Ví dụ:

```text id="m5k8r2"
TypeId(1)  → i32
TypeId(2)  → f32
TypeId(3)  → Vec2
TypeId(4)  → Option<i32>
TypeId(5)  → fn(i32) -> i32
```

Mọi compiler subsystem chỉ cần giữ `TypeId`.

---

# 3. Type interning

Hai lần gặp:

```axiom id="x4m7q2"
Option<i32>
```

phải cho cùng canonical type:

```text id="j8v3n1"
TypeId(42)
```

không:

```text id="p6c9y4"
TypeId(42)
TypeId(93)
```

cho cùng semantic type.

---

# 4. Type representation

Conceptual:

```text id="c2x7m8"
TypeKind
├── Primitive
├── Struct
├── Enum
├── Tuple
├── Array
├── Function
├── Closure
├── View
├── MutView
├── RawPointer
├── GenericParam
├── AppliedGeneric
├── DynTrait
├── ImplTrait
├── TypeAlias
├── Never
├── Unit
└── InferenceVar
```

Nhưng implementation có thể canonicalize alias/applied types thành representation hiệu quả hơn.

---

# 5. Type identity

Axiom phân biệt:

```text
type identity
representation
storage
value
```

Ví dụ:

```axiom id="z5m2q8"
type UserId = u64
struct ProductId(u64)
```

Ta có:

```text
UserId     ≡ u64
ProductId  ≠ u64
```

`UserId` là alias.

`ProductId` là newtype.

---

# 6. Type equality

Cần phân biệt:

### Syntactic equality

```text
Vec<i32>
Vec<i32>
```

### Semantic equality

```text
type A = Vec<i32>
type B = A
```

`A` và `B` phải resolve về cùng semantic type.

---

# 7. Type aliases không tạo type mới

```axiom id="r4y8n2"
type Meters = f64
```

Compiler:

```text
Meters
 ↓
f64
```

Không tạo runtime wrapper.

Nếu cần wrapper:

```axiom id="q7m3x9"
struct Meters(f64)
```

---

# 8. Primitive types

v0.1:

```text id="w1k9s4"
bool

i8 i16 i32 i64
u8 u16 u32 u64

isize usize

f32 f64

unit
never
```

Không implicit promotion.

Ví dụ:

```axiom id="h5v8q1"
let x: i32 = 10
let y: i64 = x
```

→ lỗi.

Phải:

```axiom id="b8x2m6"
let y: i64 = x as i64
```

---

# 9. Không có conversion graph

Đây là quyết định rất quan trọng.

Không có hệ thống:

```text
i32 → i64 → f64 → ...
```

để compiler tự tìm đường conversion.

Axiom:

```text id="c9m4x2"
conversion = explicit semantic operation
```

Điều này giúp tránh những bug kiểu:

```text
A → B → C
```

mà programmer không biết compiler đã làm gì.

---

# 10. Numeric literals là ngoại lệ có kiểm soát

```axiom id="q8n3m5"
let x: i32 = 42
let y: i64 = 42
let z: f32 = 42
```

`42` không có type cố định ngay khi lexer đọc nó.

Type checker nhìn expected type.

Do đó:

```text
42
```

có thể trở thành:

```text
i32
i64
u32
f32
...
```

nếu literal biểu diễn được giá trị.

Đây là **literal inference**, không phải implicit conversion.

---

# 11. Literal overflow

```axiom id="p4y7c8"
let x: u8 = 300
```

→ compile error.

Không wrap silently.

Ví dụ:

```text
AX_TYPE_0008
integer literal out of range
```

---

# 12. Inference variable

Khi gặp:

```axiom id="s6m2x8"
let x = foo()
```

compiler có thể tạo:

```text
T0
```

sau đó:

```text
foo() : T0
```

Các constraint tiếp tục được thêm.

---

# 13. Constraint model

Ví dụ:

```axiom id="v8q3n5"
let x = 10
let y: i64 = x
```

constraints:

```text
T_x = type(10)
T_x = i64
```

solver phát hiện:

```text
type(10) = i64
```

nếu literal hợp lệ.

---

# 14. Unification

Axiom cần unification nhưng **không nên expose unification cho programmer**.

Ví dụ:

```axiom id="c4x7m1"
fn identity<T>(x: T) -> T {
    x
}

let x = identity(42)
```

Constraint:

```text
T = type(42)
```

→ `T = i32` chẳng hạn theo default/inference rule.

---

# 15. Default integer type

Nếu integer literal không có expected type:

```axiom id="y9m2q6"
let x = 42
```

cần deterministic default.

Tôi đề xuất:

```text id="m8x4v1"
integer literal → i32
```

nếu giá trị biểu diễn được.

Nếu không:

```axiom id="n2q7k5"
let x = 5000000000
```

compiler có thể chọn `i64` nếu literal inference policy cho phép.

Tuy nhiên để semantics cực kỳ deterministic, tốt hơn là:

> **Unconstrained integer literal mặc định `i32`; nếu không biểu diễn được thì compile error.**

Muốn `i64`:

```axiom id="f3m8x2"
let x: i64 = 5_000_000_000
```

hoặc:

```axiom id="j6q4v9"
let x = 5_000_000_000 as i64
```

Tôi chọn cách thứ nhất: **không tự nhảy type theo magnitude**.

---

# 16. Float literal

```axiom id="k5r8m2"
let x = 1.5
```

default:

```text
f64
```

Nếu expected:

```axiom id="v7x3q1"
let x: f32 = 1.5
```

→ `f32`.

---

# 17. Type checking expressions

Ví dụ:

```axiom id="m2y8p4"
a + b
```

Type checker:

```text
type(a)
type(b)
operator(+)
```

sau đó xác định semantics.

Không resolver overload theo tên `+`.

Operator được xử lý qua language-defined operator semantics / trait machinery ở phase type/trait.

---

# 18. Assignment

```axiom id="x8q4m2"
x = y
```

yêu cầu:

```text
type(y) assignable-to type(x)
```

Không có implicit numeric conversion.

---

# 19. Mutability là type property hay binding property?

Đây là chỗ cần phân biệt.

```axiom id="f6m2z8"
let x = ...
var y = ...
```

`let`/`var` không tạo hai type.

Ví dụ:

```text
x : i32
y : i32
```

Nhưng binding state:

```text
x → immutable
y → mutable
```

Do đó:

> **Mutability của local binding không nằm trong `TypeId`.**

Nó nằm trong HIR binding metadata / ownership environment.

---

# 20. `const` cũng không phải type mới

```axiom id="j3x7n2"
const PI: f64 = 3.14
```

Type:

```text
f64
```

Compile-time evaluation là property của declaration/evaluation, không phải một `ConstF64` type.

---

# 21. `static`

```axiom id="q5m8v3"
static GLOBAL: i32 = 10
```

Type vẫn:

```text
i32
```

Storage identity/lifetime được xử lý ở storage/ABI layer.

---

# 22. Struct type

```axiom id="p7x3m4"
struct Vec2 {
    x: f32
    y: f32
}
```

Canonical:

```text id="v8n2q6"
StructType {
    StructId
}
```

Không embed toàn bộ field types vào mọi `TypeId`.

Struct declaration đã có semantic identity.

---

# 23. Generic struct

```axiom id="r2m7x8"
struct Vec<T> {
    data: ...
}
```

`Vec<i32>`:

```text id="c5q9n1"
AppliedType {
    definition: Vec
    args: [i32]
}
```

`Vec<f32>`:

```text id="z4m6x2"
AppliedType {
    definition: Vec
    args: [f32]
}
```

Hai type khác nhau.

---

# 24. Canonicalization

```text id="h8v3q2"
Vec<i32>
type A = Vec<i32>
type B = A
```

sau canonicalization:

```text
A → Vec<i32>
B → Vec<i32>
```

cùng `TypeId`.

---

# 25. Generic substitution

Ví dụ:

```axiom id="m4x7q1"
fn identity<T>(x: T) -> T
```

Instantiation:

```text id="q8n3v5"
T := i32
```

function semantic instance:

```text
identity<i32>
```

Type checker sử dụng substitution environment:

```text
T → i32
```

---

# 26. Substitution không mutate type

Không sửa:

```text
T
```

thành:

```text
i32
```

global.

Thay vào đó:

```text id="f2m7x8"
Substitution {
    GenericParam(T) → i32
}
```

Điều này rất quan trọng cho parallel compilation.

---

# 27. Function type

```axiom id="w3q8m1"
fn(i32, i32) -> i32
```

canonical:

```text id="x5n2v7"
FunctionType {
    params: [i32, i32]
    result: i32
    effects: ...
}
```

Nhưng **chưa thêm effect system**.

Vì vậy v0.1:

```text
FunctionType {
    params
    result
}
```

là đủ.

---

# 28. `void` không tồn tại

Axiom dùng:

```text id="a7m4q9"
unit = ()
```

Function không trả value:

```axiom id="c3x8n2"
fn log(x: Text) {
    ...
}
```

semantic return type:

```text
unit
```

Không tạo `void`.

---

# 29. Never

```axiom id="q6m1x8"
never
```

là bottom-like control-flow type.

Ví dụ:

```axiom id="y4v7m3"
fn panic_now() -> never {
    panic()
}
```

`never` có thể coerce vào context cần type:

```text
never → T
```

vì expression không tiếp tục bình thường.

---

# 30. If expression

```axiom id="p8x3m7"
let x =
    if cond {
        10
    } else {
        20
    }
```

Type constraint:

```text
type(then) = type(else)
```

→ `i32`.

Không cho:

```axiom id="v2m6q8"
if cond {
    10
} else {
    "hello"
}
```

trừ khi một abstraction/type relation hợp lệ được định nghĩa rõ ràng.

---

# 31. Match

```axiom id="n5x8q3"
match value {
    A => 10,
    B => 20,
}
```

Các arm phải có compatible result type.

`match` cũng phải exhaustive, nhưng exhaustiveness thuộc pattern/type checking phase.

---

# 32. Tuple

```axiom id="x3q7m1"
(i32, f32, bool)
```

canonical tuple type:

```text id="c8v2n6"
Tuple [
    i32,
    f32,
    bool
]
```

Tuple structural equality.

---

# 33. Array

```text id="g4m8q2"
Array<i32, 4>
```

Type identity gồm:

```text
element type
length
```

Do đó:

```text
Array<i32, 4>
≠
Array<i32, 8>
```

---

# 34. View types

Đây là phần đặc biệt của Axiom.

```text id="j7x3m8"
view<T>
mut_view<T>
```

Type system phải coi chúng là semantic types, không phải syntax sugar của pointer.

```text
view<i32>
```

khác:

```text
*i32
```

và:

```text
mut_view<i32>
```

khác:

```text
view<i32>
```

---

# 35. View không phải ownership

```axiom id="v4m9x2"
fn sum(xs: view<i32>) -> i32
```

`xs` không sở hữu array.

Type checker có thể biết capability semantics, nhưng ownership verifier mới kiểm tra lifetime/provenance.

---

# 36. Mut view không phải “mutable type”

`mut_view<T>` nghĩa:

```text
exclusive write capability
```

Không phải:

```text
T is mutable
```

Ví dụ:

```axiom id="k8q3m5"
fn fill(xs: mut_view<i32>) {}
```

function có quyền mutate vùng nhớ được capability đại diện.

---

# 37. Raw pointer

```text id="f5x2m8"
*const T
*mut T
```

là machine-level types.

Type system vẫn biểu diễn chúng.

Nhưng safety verifier yêu cầu unsafe context cho operations tương ứng.

---

# 38. Pointer không phải capability

```text id="r8m3q7"
*mut T
```

chỉ là raw pointer.

Không mặc nhiên chứng minh:

- valid
- aligned
- initialized
- live
- unique
- dereferenceable

Đây là boundary cực kỳ quan trọng.

---

# 39. `dyn Trait`

```axiom id="m6x9q2"
dyn Display
```

là dynamic trait type.

Semantic:

```text
data representation
+
dispatch metadata
```

Nhưng TypeId chỉ cần:

```text id="k3v8n5"
DynTraitType {
    TraitId
    ...
}
```

ABI layer mới quyết định representation.

---

# 40. `impl Trait`

```axiom id="q4m7x2"
fn make() -> impl Display
```

không phải dynamic dispatch.

Nó là **opaque static type**.

Compiler biết concrete type ở compilation boundary thích hợp.

---

# 41. Không để `impl Trait` thành “magic generic”

Semantics cần distinction:

```text id="v7n3m8"
generic<T: Trait>
```

caller quyết định T.

Trong:

```text id="c8x2q5"
fn make() -> impl Trait
```

callee quyết định một concrete hidden type.

Hai abstraction khác nhau.

---

# 42. Closure type

```axiom id="h4m8x1"
|x| x + 1
```

mỗi closure có semantic anonymous type.

Không cần programmer đặt tên.

Compiler:

```text id="z7q3m9"
ClosureType(FunctionId/ClosureId)
```

Closure có:

```text
capture environment
parameter types
return type
```

---

# 43. Closure capture không phải type inference duy nhất

Ví dụ:

```axiom id="x5m2q8"
let x = 10
let f = || x
```

Closure capture `x`.

Ownership/capture mode được compiler phân tích riêng.

Type system biết closure signature.

Capture semantics thuộc closure/ownership analysis.

---

# 44. Type inference boundary

Đây là nguyên tắc tôi muốn khóa:

> **Inference chỉ suy ra những gì compiler có thể xác định một cách deterministic từ local constraints.**

Không suy luận:

- từ runtime values
- từ optimization
- từ machine target
- từ overload heuristics
- từ linker
- từ code generation.

---

# 45. No implicit coercion

Axiom không có hệ thống coercion rộng.

Có thể có một số **built-in semantic adjustments**:

```text
never → T
array → ephemeral view<T> khi parameter yêu cầu
```

nhưng đây là language-defined coercion, không phải general conversion graph.

---

# 46. Owner → view

Đây là một ngoại lệ quan trọng:

```axiom id="b3x8m5"
fn sum(x: view<i32>) {}

var a = [1, 2, 3]
sum(a)
```

Compiler cho phép implicit ephemeral owner→view.

Nhưng:

```axiom id="n7m2q4"
let v = a
```

không biến `v` thành view.

Nó là value semantics bình thường.

Muốn view:

```axiom id="x9q4m6"
let v = view(a)
```

---

# 47. `mut_view`

Tương tự:

```axiom id="f8m3q1"
fn fill(x: mut_view<i32>) {}

var a = [0, 0, 0]

fill(a)
```

implicit temporary capability được phép.

Nhưng binding:

```axiom id="r5x8n2"
let v = mut_view(a)
```

là explicit.

---

# 48. Type checking không hoàn toàn là ownership checking

Ví dụ:

```axiom id="k3m7q9"
let v = view(a)
drop(a)
```

Type system có thể thấy:

```text
v : view<T>
a : T
```

nhưng việc:

```text
a bị destroy trong khi v còn live
```

là **capability/ownership verifier**.

Do đó không nhồi tất cả vào type checker.

---

# 49. Type Environment

Type checker cần environment:

```text id="w8m2x5"
TypeEnv {
    locals
    generic_params
    functions
    structs
    enums
    traits
    associated_types
}
```

Nhưng các declaration đã được resolver xác định bằng IDs.

---

# 50. Typed HIR

Sau type checking:

```text id="p6x3m8"
Expr {
    kind: ...
    type: TypeId
}
```

Ví dụ:

```axiom id="g8q2m4"
a + b
```

HIR:

```text
Binary(Add)
├── lhs: LocalRef(a) : i32
├── rhs: LocalRef(b) : i32
└── type: i32
```

Từ đây MIR lowering dễ hơn rất nhiều.

---

# 51. Constraint solver

Không cần một theorem prover.

v0.1 chỉ cần:

```text id="x4m8q2"
Equality
Subtype/coercion (rất hạn chế)
Trait obligations
Generic substitution
Associated type normalization
```

và solver state:

```text id="n7q3m5"
PROVEN
DISPROVEN
AMBIGUOUS
OVERFLOW
```

Đã freeze trước đây.

---

# 52. Type error phải deterministic

Ví dụ:

```axiom id="c5m9x1"
let x: i32 = true
```

Không:

```text
expected something numeric maybe
```

Mà:

```text
AX_TYPE_0001
expected i32
found bool
```

Diagnostic có:

```text
primary span
expected type
found type
related spans
```

---

# 53. Type error không phụ thuộc optimization

Ví dụ compiler:

```text
-O0
-O2
-O3
```

phải produce cùng semantic type result.

Không được:

```text
-O3 → accepted
-O0 → rejected
```

---

# 54. Type system và target independence

```axiom id="m8q4x2"
i32
```

luôn là semantic 32-bit signed integer.

Không:

```text
Windows i32 = 32
Linux i32 = 64
```

Target-specific representation chỉ xuất hiện ở ABI/backend.

---

# 55. Type layout tách khỏi type identity

Ví dụ:

```text id="z3m7q8"
struct Vec2 {
    x: f32
    y: f32
}
```

Type identity:

```text
StructId(42)
```

Layout:

```text
Layout {
    size
    align
    fields
    offsets
}
```

được tính bởi layout engine sau.

---

# 56. Type system không biết register allocation

`i32` có thể nằm:

```text
register
stack
memory
SIMD register
```

Type system không quan tâm.

Đó là backend.

---

# 57. Type System Invariants

Khóa:

```text id="s7x3m9"
ATYPE-20
Every semantic type has a canonical TypeId.

ATYPE-21
Equivalent aliases resolve to the same semantic type.

ATYPE-22
Newtypes have distinct type identity.

ATYPE-23
Type equality is deterministic.

ATYPE-24
Type checking is independent of optimization level.

ATYPE-25
Type semantics are independent of storage placement.

ATYPE-26
Type semantics are independent of register allocation.

ATYPE-27
Implicit numeric conversion does not exist.

ATYPE-28
Numeric literal inference is distinct from numeric conversion.

ATYPE-29
Integer literal overflow is a compile-time error.

ATYPE-30
Floating literal defaulting is deterministic.

ATYPE-31
Inference variables are compiler-internal.

ATYPE-32
Inference cannot depend on runtime values.

ATYPE-33
Generic substitution does not mutate canonical generic types.

ATYPE-34
Function types have explicit parameter and result types.

ATYPE-35
Unit is the type of no-value-returning functions.

ATYPE-36
Never represents non-returning control flow.

ATYPE-37
View and MutView are distinct semantic types.

ATYPE-38
Raw pointers are distinct from capabilities.

ATYPE-39
DynTrait is distinct from ImplTrait.

ATYPE-40
Closure types are distinct semantic types.

ATYPE-41
Binding mutability is not part of ordinary value type identity.

ATYPE-42
Const-ness is not a separate runtime value type.

ATYPE-43
Static storage is not a distinct value type.

ATYPE-44
Type checking does not perform ownership verification.

ATYPE-45
Type checking does not perform capability verification.

ATYPE-46
Type checking does not depend on machine code generation.

ATYPE-47
Type errors are deterministic.

ATYPE-48
Unresolved names do not become dynamic types.

ATYPE-49
General implicit conversion graphs do not exist.

ATYPE-50
Coercions are explicitly enumerated language rules.
```

---

# 58. Compiler implementation

Cấu trúc:

```text
compiler/typeck/
├── type.rs
├── type_id.rs
├── interner.rs
├── primitive.rs
├── equality.rs
├── normalize.rs
├── substitute.rs
├── infer.rs
├── constraints.rs
├── unify.rs
├── coercion.rs
├── literals.rs
├── function.rs
├── expressions.rs
├── patterns.rs
├── generics.rs
├── environment.rs
├── diagnostics.rs
└── tests/
```

Core data:

```text id="m3q7x9"
TypeId
TypeKind
TypeInterner
TypeEnv
InferenceVar
Constraint
Substitution
```

---

# 59. Type checking algorithm

Một function:

```axiom id="n4x8m2"
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

pipeline:

```text id="q7m2v5"
1. create function TypeEnv
2. bind a : i32
3. bind b : i32
4. expected return = i32
5. type-check a
6. type-check b
7. resolve +
8. infer result
9. compare result with i32
10. produce Typed HIR
```

---

# 60. Milestone TYPE-001

Trước trait solver, trước ownership, trước MIR:

### Phải hoàn thành:

```text id="f8m3q1"
TypeId
TypeInterner
Primitive types
Tuple
Array
Function types
Struct references
Enum references
Generic parameters
Type aliases
Newtypes
Inference variables
Literal inference
Unification
Explicit casts
Never/unit
View/MutView types
Raw pointer types
```

Test:

```text
i32 == i32
i32 != i64

type A = i32
A == i32

struct UserId(i32)
UserId != i32

Option<i32> == Option<i32>
Option<i32> != Option<u32>

fn(i32) -> i32
```

---

# 61. Thứ tự sau TYPE-001

Không nên nhảy ngay vào ownership.

Thứ tự hợp lý là:

```text
TYPE-001
Type Kernel
   ↓
TYPE-002
Expression Type Checking
   ↓
TYPE-003
Generic Substitution
   ↓
TYPE-004
Trait Solver
   ↓
TYPE-005
Method Resolution
   ↓
TYPE-006
Associated Types
   ↓
TYPE-007
impl Trait / dyn Trait
   ↓
TYPE-008
Typed HIR Freeze
   ↓
OWNERSHIP
```

Và **Trait Solver** sẽ là phần tiếp theo đặc biệt quan trọng, vì nó quyết định cách Axiom xử lý:

```axiom
T: Ord
T: Copy
T: Send
T: Share
```

mà không rơi vào tình trạng compiler phải giải một hệ thống trait quá phức tạp như Rust/Scala/Haskell.

Tôi đề xuất tiếp theo khóa **AXIOM TRAIT SOLVER v0.1 + METHOD RESOLUTION**, đồng thời thiết kế giới hạn solver ngay từ đầu để bảo đảm: **không có infinite type recursion, không có compiler hang, không có “magic” overload resolution và mọi ambiguity đều trở thành lỗi compile-time xác định được.**