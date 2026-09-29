# XXXVIII — TYPE-001: Type Engine + Typed HIR

Đây là bước rất quan trọng vì từ đây Axiom bắt đầu có **semantic type system thật**, thay vì chỉ parse syntax.

Mục tiêu đầu tiên:

```text
fn main() {}

fn main() -> i32 {
    42
}

fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

phải đi được tới **Typed HIR hoàn chỉnh**.

---

## 1. Boundary

```text
HIR
 │
 ├── Type Checker
 │      ├── TypeInterner
 │      ├── Constraint Solver
 │      ├── Literal Inference
 │      └── Call Checking
 │
 ▼
Typed HIR
```

Type checker **không** làm:

```text
Ownership
Capability
Drop
Allocation
MIR
Codegen
```

Đây là điểm cần giữ rất chặt.

---

# 2. `TypeId` là semantic identity

`TypeId` không phải chỉ là enum.

Concept:

```text
TypeId
    ↓
TypeInterner
    ↓
Canonical Type
```

Ví dụ:

```text
i32 → TypeId(4)
u32 → TypeId(5)
f32 → TypeId(6)
```

Hai lần tạo `i32` phải trả cùng `TypeId`.

---

# 3. Type representation

MVP:

```text
Type {
    kind: TypeKind
}
```

`TypeKind`:

```text
Unit
Never
Bool

I8
I16
I32
I64

U8
U16
U32
U64

ISize
USize

F32
F64

Tuple(Vec<TypeId>)
Array(TypeId, usize)

Function(FunctionType)

View(TypeId)
MutView(TypeId)

RawPointer {
    mutable: bool
    pointee: TypeId
}

Named(TypeDefId)
Applied(TypeDefId, Vec<TypeId>)

DynTrait(TraitId, Vec<TypeId>)
```

Sau này có thể thêm:

```text
GenericParam
Projection
InferenceVar
Opaque
```

nhưng inference variables **không được trở thành canonical public TypeId**.

---

# 4. TypeInterner phải phân biệt semantic equality

Ví dụ:

```text
(i32, f32)
```

và:

```text
(i32, f32)
```

phải cùng `TypeId`.

Trong khi:

```text
(i32, f32)
```

và:

```text
(f32, i32)
```

khác.

Concept key:

```text
TypeKey {
    kind
    children
}
```

Hash-consing:

```text
TypeKey → TypeId
```

---

# 5. Primitive types

Axiom không có implicit C-style numeric hierarchy.

Do đó:

```text
i32
u32
f32
f64
```

là các type độc lập.

Không có quy tắc:

```text
i32 → i64
```

tự động.

Không có:

```text
i32 + f32
```

tự nhiên thành `f32`.

Phải cast:

```axiom id="p3a9h2"
(a as f32) + b
```

nếu `b: f32`.

---

# 6. `unit` và `never`

`unit`:

```text
()
```

là type có đúng một giá trị.

Ví dụ:

```axiom id="r9r8dj"
fn hello() {
}
```

return type:

```text
unit
```

`never`:

```text
!
```

không có giá trị.

Ví dụ:

```axiom id="x5r8k0"
panic("failed")
```

có type:

```text
never
```

Do đó:

```axiom id="m7b5zi"
if condition {
    42
} else {
    panic(...)
}
```

có thể có type:

```text
i32
```

vì:

```text
never
```

coerce trong control-flow type checking.

Đây là **semantic compatibility**, không phải numeric conversion.

---

# 7. Numeric literal — quyết định quan trọng

Literal:

```axiom id="q1w0qe"
42
```

không ngay lập tức trở thành `i32`.

Nó trước tiên là:

```text id="9m6oq2"
IntegerLiteral
```

với constraint.

Ví dụ:

```axiom id="a8o8du"
let x: i64 = 42
```

checker thấy:

```text
literal 42
expected i64
```

→ literal được type là `i64`.

Nhưng:

```axiom id="3qj3pd"
let x = 42
```

không có expected type.

Axiom cần một default literal type deterministic.

### Quyết định v0.1

Integer literal mặc định:

```text
i32
```

nếu representable.

Nếu không:

```text
let x = 9_999_999_999_999_999_999
```

→ compile error.

Không tự động nhảy qua:

```text
i64
u64
```

để tránh inference bất ngờ.

---

# 8. Float literal

```text
3.14
```

mặc định:

```text
f64
```

Nếu context:

```axiom id="v6z5h0"
let x: f32 = 3.14
```

thì literal trở thành `f32`.

Nhưng variable:

```axiom id="xy9h8c"
let x: f64 = ...
let y: f32 = x
```

không implicit convert.

---

# 9. Literal overflow

```axiom id="f0g51n"
let x: i8 = 300
```

→ compile error.

Không silently truncate.

Diagnostic:

```text
AX_TYPE_0007
integer literal out of range
```

---

# 10. Boolean

Không có truthiness.

```axiom id="e9q6ct"
if x
```

chỉ hợp lệ nếu:

```text
x : bool
```

Không:

```text
i32 → bool
pointer → bool
```

implicit.

---

# 11. Function type

```text
fn(i32, i32) -> i32
```

representation:

```text
FunctionType {
    params: [i32, i32]
    return_type: i32
}
```

Function declarations có:

```text
FunctionId
```

và type signature.

---

# 12. Function checking

Với:

```axiom id="4fs2vz"
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

checker tạo environment:

```text
a → i32
b → i32
```

Sau đó:

```text
a + b
```

operator resolver thấy:

```text
lhs = i32
rhs = i32
operator = +
```

→ result:

```text
i32
```

Block:

```text
i32
```

Function return:

```text
i32
```

→ valid.

---

# 13. Operator typing

Đừng hard-code toàn bộ vào parser.

Type checker có semantic operator table:

```text
BinaryOpRule
{
    operator
    lhs_type
    rhs_type
    result_type
    semantic_kind
}
```

Ví dụ:

```text
i32 + i32 → i32
i64 + i64 → i64
f32 + f32 → f32
f64 + f64 → f64
```

Nhưng:

```text
i32 + f32
```

→ error.

---

# 14. Checked/wrapping/saturating arithmetic

Ba operator này là semantic khác nhau:

```text
+
+%
+|
```

Ví dụ:

```text
i32 + i32
```

→ checked arithmetic.

```text
i32 +% i32
```

→ wrapping.

```text
i32 +| i32
```

→ saturating.

Type result đều:

```text
i32
```

nhưng `ArithmeticKind` khác.

Typed HIR nên giữ:

```text
BinaryExpr {
    op: Add
    arithmetic_semantics: Checked
}
```

hoặc normalized equivalent.

Không được để optimizer suy đoán `+` có thể biến thành wrapping.

---

# 15. Assignment

```axiom id="9b1d3x"
x = 42
```

Type của toàn expression:

```text
unit
```

Không phải `i32`.

Đây là invariant:

```text
ATHIR-24
Assignment has type unit.
```

---

# 16. Function call

```axiom id="u3v8w9"
add(20, 22)
```

Resolver đã xác định:

```text
add → FunctionId(7)
```

Type checker lấy signature:

```text
(i32, i32) -> i32
```

rồi kiểm:

```text
20 → i32
22 → i32
```

result:

```text
i32
```

---

# 17. Argument checking

Sai:

```axiom id="xg5m1m"
add(20, 2.5)
```

vì:

```text
expected i32
found f64
```

Không tự động:

```text
2.5 → i32
```

---

# 18. Return checking

```axiom id="q9t0t3"
fn foo() -> i32 {
    42
}
```

valid.

Nhưng:

```axiom id="z9k7u4"
fn foo() -> i32 {
    ()
}
```

→:

```text
AX_TYPE_0001
return type mismatch
expected i32
found unit
```

---

# 19. Implicit final expression

```axiom id="2xqk4e"
fn foo() -> i32 {
    42
}
```

được semantic tương đương:

```text
return 42
```

nhưng HIR không nhất thiết phải tạo `ReturnExpr`.

Block có:

```text
tail = 42
```

Type checker:

```text
BlockType = type(tail)
```

---

# 20. Block không có tail

```axiom id="z8y1v7"
{
    let x = 42
}
```

Type:

```text
unit
```

vì declaration cuối không phải expression value.

---

# 21. `if`

```axiom id="d5m8c4"
if cond {
    1
} else {
    2
}
```

Checker:

```text
cond : bool
then : i32
else : i32
```

→ result `i32`.

---

# 22. `if` không có else

```axiom id="8d7q5e"
if cond {
    foo()
}
```

Chỉ hợp lệ nếu branch:

```text
unit
```

hoặc tương thích với unit semantics.

Ví dụ:

```text
if cond {
    42
}
```

→ error vì expression có thể cần một value nhưng không có else.

---

# 23. `never`

```axiom id="3b4r0w"
if cond {
    42
} else {
    panic(...)
}
```

Checker:

```text
i32
never
```

→ `i32`.

Nhưng:

```axiom id="3z4g1f"
if cond {
    42
} else {
    "hello"
}
```

→ error:

```text
i32 vs Text
```

---

# 24. Tuple type

```axiom id="7r9n2a"
let p = (10, 20.0)
```

Type:

```text
(i32, f64)
```

Canonical:

```text
TypeId
  ↓
Tuple[
    I32,
    F64
]
```

Tuple index:

```axiom id="3f0k8j"
p.0
```

→ `i32`.

---

# 25. Array type

```axiom id="f5t0a3"
let a = [1, 2, 3]
```

Inference:

```text
Array<i32, 3>
```

Fixed size là một phần semantic type.

```text
Array<i32, 3>
```

khác:

```text
Array<i32, 4>
```

---

# 26. Array fill

```axiom id="r1q4y6"
[0; 1024]
```

→:

```text
Array<i32, 1024>
```

hoặc type context quyết định element type.

---

# 27. View types

```text
view<T>
mut_view<T>
```

Type checker chỉ xác định:

```text
view<Vec2>
```

là type hợp lệ.

Nó chưa kiểm:

- owner tồn tại
- capability live
- lifetime
- overlap

Đó là capability analyzer.

---

# 28. Raw pointer

```text
*const T
*mut T
```

Type checker tạo:

```text
RawPointer {
    mutable: false
    pointee: T
}
```

nhưng thao tác dereference sẽ yêu cầu unsafe ở semantic safety phase.

Type checking và unsafe checking là hai lớp khác nhau.

---

# 29. Cast

`as` có category.

Ví dụ:

```axiom id="g2r6d4"
x as i64
```

Type checker phân loại:

```text
NumericCast
```

Nếu:

```text
*const T as *const U
```

→ PointerCast.

Không cho:

```text
arbitrary type A as type B
```

---

# 30. `bit_cast`

Không dùng chung logic với `as`.

```text
bit_cast<T>(x)
```

yêu cầu:

```text
size_of(Source) == size_of(Target)
```

và representation rules tương ứng.

Đây là semantic intrinsic riêng.

---

# 31. Type compatibility

Cần phân biệt:

```text
Type Equality
Type Compatibility
Type Conversion
```

Ví dụ:

```text
i32 == i32
```

true.

```text
never compatible with i32
```

true trong control-flow context.

Nhưng:

```text
i32 compatible with i64
```

false.

Không dùng một hàm `is_compatible()` khổng lồ cho mọi trường hợp.

Nên tách:

```text
same_type()
can_coerce()
can_cast()
can_unify()
```

---

# 32. Inference engine

MVP cần inference variables nội bộ.

Ví dụ:

```axiom id="f9j3tr"
let x = 42
```

checker concept:

```text
x : ?T
literal 42 : IntegerLiteral(?T)
```

Sau defaulting:

```text
?T → i32
```

Inference variables:

```text
InferTypeVar
```

không được đưa vào final Typed HIR.

Final HIR chỉ chứa canonical `TypeId`.

---

# 33. Constraint system

MVP:

```text
Constraint
├── Equal(Type, Type)
├── Assignable(Type, Type)
├── NumericLiteralFits(Literal, Type)
└── Callable(FunctionType, Args)
```

Sau khi solve:

```text
all inference vars resolved
```

Nếu còn unresolved:

```text
AX_TYPE_0009
cannot infer type
```

---

# 34. Không xây Hindley-Milner đầy đủ

Axiom không cần type inference kiểu functional language toàn diện.

Mục tiêu:

> inference vừa đủ để code gọn, nhưng không làm semantics mơ hồ.

Do đó:

```text
let x = 42
```

dễ.

Nhưng:

```text
let x = some_generic_complex_expression
```

nếu không thể suy luận deterministic → yêu cầu annotation.

Đây là lựa chọn tốt cho compiler performance và diagnostics.

---

# 35. Typed HIR representation

Sau type checking:

```text
TypedExpr {
    id: ExprId
    kind: TypedExprKind
    type_id: TypeId
    span: Span
}
```

Ví dụ:

```axiom id="pjf4w9"
a + b
```

→

```text
Binary {
    op: AddChecked
    lhs: LocalRef(a)
    rhs: LocalRef(b)
    type: I32
}
```

---

# 36. Typed HIR không mutable

Một khi:

```text
HIR → Typed HIR
```

hoàn thành:

> Typed HIR là immutable semantic snapshot.

Ownership analyzer không sửa nó.

Nó tạo facts:

```text
OwnershipFacts
CapabilityFacts
```

và MIR mới.

---

# 37. Type diagnostics

Chốt nhóm đầu:

```text
AX_TYPE_0001
Type mismatch

AX_TYPE_0002
Invalid operand types

AX_TYPE_0003
Invalid condition type

AX_TYPE_0004
Invalid return type

AX_TYPE_0005
Invalid function argument

AX_TYPE_0006
Invalid cast

AX_TYPE_0007
Literal out of range

AX_TYPE_0008
Invalid assignment target

AX_TYPE_0009
Cannot infer type

AX_TYPE_0010
Invalid array element type
```

---

# 38. Type invariants

```text
ATYPE-20
Every canonical semantic type has exactly one TypeId.

ATYPE-21
TypeIds are deterministic within a compilation semantic context.

ATYPE-22
Primitive types have no implicit numeric hierarchy.

ATYPE-23
Implicit numeric conversions are forbidden.

ATYPE-24
Explicit casts are required for numeric conversion.

ATYPE-25
Integer literal defaulting is deterministic.

ATYPE-26
Float literal defaulting is deterministic.

ATYPE-27
Literal overflow is a compile-time error.

ATYPE-28
Boolean conditions require bool.

ATYPE-29
Assignment has type unit.

ATYPE-30
Function argument types are checked exactly after permitted literal inference.

ATYPE-31
Function return type is checked against block result.

ATYPE-32
Never may satisfy compatible control-flow result types.

ATYPE-33
Tuple element types are ordered and canonical.

ATYPE-34
Array length is part of array type identity.

ATYPE-35
View and mut_view are distinct types.

ATYPE-36
Raw pointer mutability is part of pointer type identity.

ATYPE-37
Cast categories remain semantically distinct.

ATYPE-38
Inference variables cannot escape into final Typed HIR.

ATYPE-39
Typed HIR contains canonical TypeIds only.

ATYPE-40
Type checking is target-independent unless the type is explicitly target-defined.

ATYPE-41
Type checking performs no ownership verification.

ATYPE-42
Type checking performs no physical allocation.

ATYPE-43
Type checking is deterministic.

ATYPE-44
Type checking does not mutate completed HIR.

```

---

# 39. TYPE-001 acceptance tests

### Test 1

```axiom id="i0y6u6"
fn main() {}
```

Expected:

```text
main : () -> unit
```

---

### Test 2

```axiom id="u7jq2b"
fn main() -> i32 {
    42
}
```

Expected:

```text
main : () -> i32
```

---

### Test 3

```axiom id="7y5w2k"
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

Expected:

```text
add : (i32, i32) -> i32
```

---

### Test 4

```axiom id="m6x1k2"
fn main() -> i32 {
    add(20, 22)
}
```

Expected:

```text
i32
```

---

### Negative 1

```axiom id="d2z7q5"
fn main() -> i32 {
    3.14
}
```

Error:

```text
AX_TYPE_0004
```

---

### Negative 2

```axiom id="k8n4c1"
fn main() {
    if 42 {
    }
}
```

Error:

```text
AX_TYPE_0003
```

---

### Negative 3

```axiom id="b7n1v8"
fn add(a: i32, b: i32) -> i32 {
    a + (b as f32)
}
```

Error:

```text
AX_TYPE_0002
```

---

# 40. Vertical Slice sau TYPE-001

Bây giờ:

```text
fn main() -> i32 {
    42
}
```

đã đi được tới:

```text
Source
 ↓
Lexer
 ↓
Parser
 ↓
AST
 ↓
Resolver
 ↓
HIR
 ↓
Type Checker
 ↓
Typed HIR
```

Bước tiếp theo **không nên nhảy ngay sang backend**.

Ta đi vào phần đặc biệt của Axiom:

# `OWN-001 — Ownership Dataflow`

Đây là nơi kiến trúc khác Rust bắt đầu thể hiện rõ.

Axiom sẽ **không có lifetime syntax**, không có:

```text
'a
&'a
&mut
```

và cũng không bắt programmer viết borrow checker annotations.

Thay vào đó compiler sẽ xây:

```text
Typed HIR
   ↓
CFG
   ↓
Place Graph
   ↓
Ownership Dataflow
   ↓
Capability Analysis
   ↓
Drop Analysis
   ↓
MIR
```

Và việc đầu tiên cần chốt là **Place model** — `Local`, `Field`, `Index`, `Deref` — vì toàn bộ move/partial-move/view/Drop về sau đều phụ thuộc vào nó.