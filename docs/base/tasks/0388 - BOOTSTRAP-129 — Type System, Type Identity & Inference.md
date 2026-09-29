# BOOTSTRAP-129 — Type System, Type Identity & Inference

**Trạng thái: FROZEN / COMPLETED**

Mục tiêu:

> Axiom có type system đủ mạnh để xây compiler, OS, GPU, ứng dụng hiệu năng cao và abstraction hiện đại, nhưng programmer **không phải viết type/lifetime/ownership bureaucracy** mà compiler có thể suy luận an toàn.

Kiến trúc:

```text
Resolved HIR
     │
     ▼
   TypeDB
     │
     ├── Type identity
     ├── Type construction
     ├── Type inference
     ├── Unification
     ├── Generic inference
     ├── Coercion
     ├── Type normalization
     └── Trait constraints
             │
             ▼
       Typed HIR
```

---

# 1. Type ≠ representation

Đây là nguyên tắc nền tảng:

```text
Semantic Type
      ≠
Physical Representation
      ≠
Memory Layout
      ≠
ABI
```

Ví dụ:

```ax
struct UserId(u64);
```

`UserId` có thể có representation giống `u64`, nhưng:

```text
UserId ≠ u64
```

về semantic type.

Compiler có thể tối ưu thành cùng machine representation.

---

# 2. Nominal typing là mặc định

Axiom dùng **nominal type identity** cho user-defined types.

```ax
struct Meter(f64);
struct Second(f64);
```

Dù representation giống nhau:

```text
Meter ≠ Second
```

Điều này ngăn các lỗi rất nguy hiểm trong systems programming.

---

# 3. Primitive types

Core:

```text
bool

i8  i16  i32  i64
u8  u16  u32  u64

isize
usize

f32
f64

unit
never
```

Có thể mở rộng:

```text
i128
u128
f16
bf16
```

mà không phá type-system architecture.

---

# 4. `unit`

```text
unit
```

là type có đúng một giá trị:

```ax
()
```

Function không trả dữ liệu:

```ax
fn log(x: String) {
    ...
}
```

semantic return type:

```text
unit
```

---

# 5. `never`

`never` biểu diễn computation không bình thường kết thúc:

```ax
fn abort() -> never {
    panic("fatal");
}
```

Các expression:

```text
return
break
continue
panic
```

có thể có control-flow type tương thích với `never`.

---

# 6. No `null`

Axiom Core không có:

```text
null
nullptr
nil
```

Thay vào đó:

```ax
Option<T>
```

Ví dụ:

```ax
fn find(id: u64) -> Option<User>
```

Điều này loại bỏ một class lớn của null-dereference.

---

# 7. Algebraic types

Enum là sum type:

```ax
enum Option<T> {
    Some(T),
    None,
}
```

Product type:

```ax
struct User {
    id: u64,
    name: String,
}
```

Do đó:

```text
struct + enum
```

đủ để xây rất nhiều abstraction mà không cần class hierarchy.

---

# 8. `Result`

```ax
enum Result<T, E> {
    Ok(T),
    Err(E),
}
```

Error propagation:

```ax
let x = read()?;
```

được type checker kiểm tra.

---

# 9. Struct là nominal

```ax
struct Point {
    x: f32,
    y: f32,
}
```

Một struct khác:

```ax
struct Position {
    x: f32,
    y: f32,
}
```

không tự động tương thích.

Không có structural typing cho user structs.

---

# 10. Tuple là structural

```ax
(i32, f64)
```

có type identity dựa trên cấu trúc.

Ví dụ:

```text
(i32, f64)
```

ở hai nơi là cùng type.

---

# 11. Arrays

```ax
[i32; 16]
```

Type identity:

```text
Array(element_type, length)
```

nên:

```text
[i32; 16] ≠ [i32; 32]
```

---

# 12. Generic type identity

```ax
Vec<i32>
Vec<f64>
```

là hai concrete types khác nhau:

```text
GenericInstance(Vec, i32)
GenericInstance(Vec, f64)
```

---

# 13. Type interning

TypeDB intern các semantic types:

```text
TypeId
```

Ví dụ:

```text
i32 → TypeId(1)

Vec<i32> → TypeId(100)

Vec<i32> → TypeId(100)
```

Không tạo object type duplicate cho cùng semantic type.

---

# 14. Type identity không dùng pointer identity

Không:

```text
type_a == type_b
```

dựa vào memory address.

Compiler dùng canonical `TypeId`/interning key.

Điều này quan trọng cho:

- incremental compiler;
- cache;
- parallel compilation;
- deterministic build;
- self-hosting.

---

# 15. Type aliases

```ax
type UserId = u64;
```

là alias.

Do đó:

```text
UserId == u64
```

về semantic identity.

Không tạo type mới.

---

# 16. Newtype

```ax
struct UserId(u64);
```

là type mới:

```text
UserId ≠ u64
```

nhưng:

```text
@repr(transparent)
```

có thể đảm bảo representation/ABI contract phù hợp.

---

# 17. Alias vs newtype

Quy tắc rất rõ:

```text
type A = B
```

→ alias.

```text
struct A(B)
```

→ nominal newtype.

Không có “một chút khác nhau” giữa hai khái niệm.

---

# 18. Type constructors

TypeDB biểu diễn:

```text
Primitive
Struct
Enum
Tuple
Array
Function
Closure
View
MutView
RawPointer
DynTrait
GenericParam
AssociatedType
TypeAlias
Never
Unit
```

Mỗi constructor có semantic rules riêng.

---

# 19. `view<T>`

```ax
view<User>
```

là non-owning read capability.

Nó không phải ordinary reference syntax.

Semantic properties:

```text
Owner: external
Access: READ
Ownership: none
```

---

# 20. `mut_view<T>`

```ax
mut_view<User>
```

là exclusive mutable capability:

```text
Access: WRITE
Ownership: none
```

Compiler kiểm tra alias/lifetime.

---

# 21. `view<T>` không phải `Copy`

Mặc dù nhiều read views có thể tồn tại:

```text
view<T>
```

không phải Copy semantic trait.

Khả năng duplicate read capability đến từ capability rules.

Điều này tránh trộn:

```text
value copying
```

với:

```text
capability duplication
```

---

# 22. `mut_view<T>` không duplicable

Không thể tạo hai mutable views chồng lấn:

```text
mut_view<T>
mut_view<T>
```

nếu compiler không chứng minh disjointness.

---

# 23. Function types

```ax
fn(i32, i32) -> i32
```

là function pointer/callable type.

Không bao gồm environment.

---

# 24. Closure types

```ax
|x| x + y
```

mỗi closure expression có anonymous unique type.

Concept:

```text
ClosureType {
    identity
    parameter_types
    return_type
    captures
}
```

---

# 25. Closure identity

Hai closure:

```ax
let a = |x| x + 1;
let b = |x| x + 1;
```

không có cùng anonymous type mặc dù source giống nhau.

Compiler có thể merge machine code nếu safe.

Semantic type vẫn distinct.

---

# 26. Non-capturing closure

```ax
let f = |x: i32| x + 1;
```

nếu không capture environment, có thể coerce thành:

```text
fn(i32) -> i32
```

khi context yêu cầu.

Đây là zero-cost semantic coercion.

---

# 27. Capturing closure

```ax
let n = 10;
let f = |x| x + n;
```

có environment.

Không tự động convert thành ordinary function pointer.

Compiler có thể stack/inline/heap eliminate environment tùy escape analysis.

---

# 28. Generic parameters

```ax
fn max<T>(a: T, b: T) -> T
```

`T` là type variable:

```text
GenericParamId
```

trong type inference context.

---

# 29. Unification

Ví dụ:

```ax
fn identity<T>(x: T) -> T

identity(10)
```

constraint:

```text
T = i32
```

Type solver unify:

```text
T ↔ i32
```

---

# 30. Bidirectional inference

Axiom nên dùng **bidirectional type inference** thay vì cố inference mọi thứ theo một hướng.

Hai hoạt động:

```text
infer(expression)
check(expression, expected_type)
```

Điều này đặc biệt hữu ích cho:

- closures;
- generic calls;
- function returns;
- literals;
- overloaded operators.

---

# 31. Ví dụ inference

```ax
let x = 10;
```

Infer:

```text
literal → default integer type → i32
```

nếu không có contextual constraint.

---

# 32. Contextual inference

```ax
let x: u64 = 10;
```

Expected type:

```text
u64
```

được truyền xuống literal.

Không cần cast:

```ax
10 as u64
```

---

# 33. Numeric literal inference

Literal ban đầu có semantic category:

```text
IntegerLiteral
FloatLiteral
```

không lập tức hard-code machine type.

Sau constraint solving:

```text
10 → i32
10u64 → u64
1.0 → f64
1.0f32 → f32
```

---

# 34. Không implicit numeric conversion

Axiom không cho:

```ax
let x: i64 = some_i32;
```

tự động convert.

Phải explicit:

```ax
let x: i64 = some_i32 as i64;
```

Điều này rất quan trọng cho systems programming.

---

# 35. Narrowing

```ax
let x: u8 = value as u8;
```

`as` phải có semantics rõ ràng.

Không để cast tùy compiler.

Ví dụ integer narrowing có thể chọn:

```text
checked
wrapping
saturating
```

theo explicit operation.

---

# 36. Cast vs bitcast

Hai semantic operation khác nhau:

```text
CAST
BITCAST
```

`cast` thay đổi semantic value theo conversion rule.

`bitcast` giữ bit pattern.

---

# 37. Bitcast requirements

```text
bitcast<T>(x)
```

chỉ hợp lệ khi:

- kích thước tương thích;
- alignment hợp lệ;
- representation hợp lệ;
- semantics cho phép.

Không biến `bitcast` thành “escape hatch” tùy tiện.

---

# 38. Coercion rất hạn chế

Axiom nên có một tập coercion nhỏ:

```text
noncapturing closure → fn pointer
array → view khi context yêu cầu
owner → ephemeral view argument
transparent representation ở ABI boundary phù hợp
never → expected type
```

Không có implicit conversion chain.

---

# 39. Owner → view

Ví dụ:

```ax
fn sum(xs: view<i32>) -> i32
```

gọi:

```ax
let a: [i32; 4] = [1,2,3,4];

sum(a);
```

compiler có thể tạo ephemeral view.

Programmer không phải viết:

```ax
sum(view(a));
```

trừ khi muốn **lưu view**.

---

# 40. Stored view phải explicit

```ax
let v = view(a);
```

để lưu capability.

Điều này giúp compiler biết rõ khi một capability có thể escape.

---

# 41. Type checking không tự động kiểm tra lifetime

Lifetime không phải type parameter bình thường.

Compiler capability analysis riêng:

```text
TypeDB
+
CapabilityDB
```

Không biến type system thành borrow checker syntax.

---

# 42. `dyn Trait`

```ax
dyn Display
```

là dynamic trait object type.

Khác:

```text
Display
```

là trait itself.

---

# 43. Static dispatch mặc định

```ax
fn print<T: Display>(x: T)
```

mặc định static/generic dispatch.

Compiler có thể monomorphize.

---

# 44. Dynamic dispatch explicit

```ax
fn print(x: dyn Display)
```

chỉ khi programmer yêu cầu dynamic polymorphism.

Không tự động biến mọi trait thành vtable.

---

# 45. `dyn Trait` representation

Implementation có thể:

```text
data pointer
+
vtable pointer
```

nhưng đó là representation/ABI.

Semantic definition chỉ là:

```text
dynamic dispatch capability
```

---

# 46. Dyn safety

Không phải trait nào cũng object-safe.

Ví dụ generic method không thể trivially trở thành vtable entry.

Trait solver/object-safety checker xử lý sau type formation.

---

# 47. Generic type constraints

```ax
fn sort<T>(x: mut_view<Vec<T>>)
where
    T: Ord
```

Type inference tạo constraints:

```text
T: Ord
```

Trait solver xử lý.

---

# 48. Associated types

```ax
trait Iterator {
    type Item;
}
```

`T::Item` là associated type projection.

TypeDB representation:

```text
ProjectionType {
    self_type: T
    trait: Iterator
    assoc: Item
}
```

---

# 49. Type normalization

Ví dụ trait implementation:

```ax
impl Iterator for MyIter {
    type Item = i32;
}
```

sau normalization:

```text
MyIter::Item
→ i32
```

nếu compiler chứng minh impl duy nhất.

---

# 50. Type normalization không phải textual substitution

Không thực hiện:

```text
replace "T::Item" with "i32"
```

bằng string.

TypeDB tạo canonical semantic type.

---

# 51. Recursive types

```ax
enum Node {
    Empty,
    Next(Box<Node>),
}
```

Type checker cho phép recursion qua indirection.

Nhưng:

```ax
struct Node {
    next: Node,
}
```

có infinite size.

→ reject.

---

# 52. Recursive type algorithm

TypeDB cần cycle detection:

```text
Node
 ↓
Field next
 ↓
Node
```

Sau đó phân biệt:

```text
finite recursive type
```

với:

```text
infinite-size recursive type
```

---

# 53. `Box<T>`

`Box<T>` là library type nhưng compiler biết các semantic properties cần thiết:

```text
Owned
Move-only
Drop
Stable address only when address becomes observable
```

Không biến `Box` thành built-in syntax.

---

# 54. `Option<Box<T>>`

Type:

```text
Option<Box<T>>
```

được phép compiler tối ưu niche representation.

Semantic type vẫn đúng:

```text
Some(Box<T>)
None
```

Không để programmer phụ thuộc vào niche layout trừ khi ABI/representation contract cho phép.

---

# 55. `Copy`

Compiler-known trait:

```text
Copy
```

Nếu type là Copy:

```ax
let b = a;
```

không consume `a`.

Nếu không:

```text
Move
```

---

# 56. `Clone`

```text
Clone
```

khác `Copy`.

```ax
let b = a.clone();
```

có thể tốn chi phí.

Không compiler tự chèn `clone()` để làm code compile.

---

# 57. `Drop`

Type có deterministic cleanup:

```text
Drop
```

không được `Copy`.

Compiler tracks cleanup independently from type representation.

---

# 58. `Send`

```text
Send
```

là semantic property:

> value có thể chuyển ownership sang execution domain khác.

Không có nghĩa:

```text
Share
```

---

# 59. `Share`

```text
Share
```

nghĩa là type có thể được shared theo concurrency semantics của Axiom.

Không tự động có nghĩa mutable.

---

# 60. Type property lattice

Compiler có thể derive:

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

Đây không phải tất cả đều là ordinary user traits.

Một số là compiler-known semantic properties.

---

# 61. Sized

Most ordinary types:

```text
Sized
```

Có thể có unsized/dynamically sized types sau này.

Core v0.1 nên giữ unsized model đơn giản.

---

# 62. Unsized types

Khuyến nghị:

> Core v0.1 không expose arbitrary user-defined DST.

Chỉ các compiler-known forms:

```text
dyn Trait
view<T>
mut_view<T>
```

có thể có dynamically-sized/metadata-carrying representation.

Giảm đáng kể complexity.

---

# 63. Slice/view type

`view<T>` có semantic metadata:

```text
provenance
length
access
```

Physical representation có thể là:

```text
pointer + length
```

nhưng không phải semantic requirement.

---

# 64. `view<T>` với fixed array

```ax
let a: [i32; 4] = ...;
let v: view<i32> = a;
```

compiler tạo capability.

Length có thể được compile-time known và optimizer có thể specialize.

---

# 65. Type inference cho view

Nếu:

```ax
fn sum(x: view<i32>)
```

và:

```ax
sum(array);
```

expected parameter type cung cấp context.

Compiler tạo implicit ephemeral view.

---

# 66. Function return inference

Axiom có thể infer return type:

```ax
fn square(x: i32) {
    x * x
}
```

và suy ra:

```text
i32
```

Tuy nhiên khuyến nghị:

> Public APIs nên cho phép/khuyến nghị explicit return type.

Không bắt buộc compiler.

---

# 67. Why explicit public signatures?

Giúp:

- API readability;
- ABI stability;
- diagnostics;
- compile-time boundaries;
- AI understanding;
- incremental compilation.

Local functions vẫn có thể tận dụng inference.

---

# 68. Closure parameter inference

```ax
let f = |x| x + 1;
```

Nếu context không đủ, compiler có thể infer `x` từ usage.

Ví dụ:

```ax
let f: fn(i32) -> i32 = |x| x + 1;
```

→ `x: i32`.

---

# 69. Ambiguous inference

```ax
let f = |x| x;
```

Nếu không có context, type của `x` chưa xác định.

Compiler phải báo:

```text
ETYPE_AMBIGUOUS
```

thay vì đoán arbitrary type.

---

# 70. Numeric defaulting

Để code đơn giản:

```ax
let x = 1;
```

default:

```text
i32
```

```ax
let x = 1.0;
```

default:

```text
f64
```

Chỉ áp dụng khi constraint solving không cung cấp type khác.

---

# 71. Boolean không convertible sang integer

Không:

```ax
let x: i32 = true;
```

Không có C-style truthiness.

---

# 72. Integer không convertible sang bool

Không:

```ax
if x { ... }
```

trừ khi `x: bool`.

Nếu muốn:

```ax
if x != 0 { ... }
```

---

# 73. Generic inference

```ax
fn identity<T>(x: T) -> T

let x = identity(42);
```

constraint:

```text
T = i32
```

→ `identity<i32>`.

---

# 74. Multiple constraints

```ax
fn foo<T: Add + Clone>(x: T)
```

Type solver phải tạo:

```text
T: Add
T: Clone
```

Không chọn một trait rồi bỏ trait còn lại.

---

# 75. Type inference boundary

Inference không được lan vô hạn qua toàn chương trình.

Boundary:

```text
module
function
generic invocation
comptime evaluation
```

giúp diagnostics và compile time kiểm soát được.

---

# 76. Type error localization

Ví dụ:

```ax
let x: i32 = "hello";
```

Compiler nên report:

```text
expected: i32
found: String
```

tại assignment hoặc expression có source span chính xác.

---

# 77. Constraint graph

Type inference nội bộ:

```text
TypeVar T1
TypeVar T2

T1 = i32
T2 = Vec<T1>
T3 = fn(T2) -> T1
```

sau solving:

```text
T1 = i32
T2 = Vec<i32>
T3 = fn(Vec<i32>) -> i32
```

---

# 78. Union-find

Unification có thể dùng:

```text
Union-Find
```

cho type variables.

Nhưng TypeDB phải đảm bảo deterministic canonicalization.

---

# 79. Occurs check

Ví dụ constraint:

```text
T = Vec<T>
```

không được unify thành infinite type.

→ occurs-check failure.

---

# 80. Trait solver boundary

Type inference tạo goal:

```text
T: Ord
```

không tự implement trait solver logic.

Nó query:

```text
TraitDB.solve(goal)
```

Kết quả:

```text
Proven
NotProven
Ambiguous
Error
```

đã frozen.

---

# 81. Type error vs trait error

Ví dụ:

```ax
foo(x)
```

Nếu `foo` cần:

```text
T: Display
```

nhưng `x` không thỏa.

Đây không phải:

```text
EUNRESOLVED_NAME
```

mà là trait/type constraint failure.

Diagnostics phải giữ distinction.

---

# 82. Type aliases don't create new traits

```ax
type UserId = u64;
```

Không thể implement trait như một type mới độc lập.

`UserId` vẫn là `u64`.

Muốn semantic identity mới:

```ax
struct UserId(u64);
```

---

# 83. Newtype enables separate implementations

```ax
struct UserId(u64);

impl Display for UserId {
    ...
}
```

Đây là lý do newtype tồn tại.

---

# 84. Orphan/coherence

Trait implementation:

```ax
impl Trait for Type
```

phải tuân coherence/orphan rules.

Resolver xác định:

```text
TraitId
TypeId
```

Trait checker quyết định legality.

---

# 85. Generic type equality

```text
Vec<i32>
```

so với:

```text
Vec<i32>
```

→ same canonical TypeId.

Nhưng:

```text
Vec<i32>
Vec<i64>
```

→ distinct.

---

# 86. Function type equality

```text
fn(i32) -> i32
```

same function type nếu parameter/return ABI-independent semantic type giống nhau.

Calling convention là ABI property riêng.

---

# 87. ABI calling convention không nằm hoàn toàn trong TypeId

Hai function có semantic type:

```text
fn(i32) -> i32
```

nhưng:

```text
extern "C" fn(i32) -> i32
```

có ABI contract khác.

Do đó ABI metadata cần nằm ngoài semantic function type hoặc là một explicit function-type modifier tùy ABI model.

---

# 88. FFI-safe type

Type system có property:

```text
FfiSafe
```

nhưng:

```text
String
Vec<T>
Arc<T>
Future<T>
dyn Trait
```

không tự động FFI-safe.

FFI checker dùng representation + ownership contract.

---

# 89. GPU legality

TypeDB cũng có thể query:

```text
is_gpu_legal(TypeId)
```

Nhưng GPU legality không làm thay đổi type identity.

Ví dụ:

```text
Vec<f32>
```

vẫn cùng type; kernel checker chỉ quyết định nó có được phép tồn tại trong kernel context hay không.

---

# 90. Type context

Compiler cần explicit context:

```text
TypeContext {
    expected_type
    generic_environment
    trait_environment
    execution_domain
    comptime_mode
}
```

giúp inference không phải dùng global mutable state.

---

# 91. Type checking pipeline

```text
Resolved HIR
    │
    ▼
Collect type constraints
    │
    ▼
Infer local types
    │
    ▼
Unify
    │
    ├── Type normalization
    ├── Coercion
    └── Trait obligations
             │
             ▼
        Trait Solver
             │
             ▼
       Typed HIR
```

---

# 92. Type checking order

Không nên type-check strictly source order.

Ví dụ:

```ax
fn a() -> i32 { b() }
fn b() -> i32 { 10 }
```

Declaration signatures đã biết.

Compiler có thể type-check functions độc lập/parallel.

---

# 93. Parallel type checking

Sau declaration/interface collection:

```text
foo()
bar()
baz()
```

có thể type-check song song nếu dependency query engine quản lý đúng.

Kết quả phải deterministic.

---

# 94. Type errors không làm crash solver

Một invalid constraint:

```text
i32 + String
```

phải trở thành diagnostic state.

Không để solver panic.

---

# 95. Error recovery trong type system

Type checker có thể dùng:

```text
ErrorType
```

để tiếp tục phân tích:

```ax
let x = invalid();
let y = x.foo();
let z = y.bar();
```

Một error không gây hàng trăm lỗi cascading vô nghĩa.

---

# 96. ErrorType không phải valid type

`ErrorType` chỉ là internal recovery sentinel.

Không được:

- codegen;
- ABI lowering;
- optimization;

cho function chứa unresolved semantic errors.

---

# 97. Type identity và optimization

Optimization có thể thấy:

```text
Meter
```

và:

```text
u64
```

cùng representation.

Nhưng không được bỏ semantic distinction trước khi type checking hoàn tất.

---

# 98. Type identity và zero-cost abstraction

Newtype:

```ax
struct UserId(u64);
```

có thể compile thành:

```text
u64
```

không object header.

Nhưng compiler vẫn đảm bảo:

```text
UserId != u64
```

ở source semantics.

Đây chính là abstraction erasure.

---

# 99. Type system và AI

Compiler có thể expose:

```text
axc inspect type UserId
```

trả:

```json
{
  "kind": "struct",
  "nominal": true,
  "fields": [
    {"name":"0","type":"u64"}
  ],
  "repr": "transparent"
}
```

AI không cần đoán semantics từ source text.

---

# 100. Type invariants

### `ATYPE-20`
User-defined types are nominal by default.

### `ATYPE-21`
Primitive types have stable semantic identities.

### `ATYPE-22`
Tuple types are structural.

### `ATYPE-23`
Array type identity includes element type and length.

### `ATYPE-24`
Generic type identity includes canonical generic arguments.

### `ATYPE-25`
Type aliases do not create new nominal identities.

### `ATYPE-26`
Newtypes create distinct nominal identities.

### `ATYPE-27`
Semantic type identity is independent of physical representation.

### `ATYPE-28`
Type identity never depends on process memory addresses.

### `ATYPE-29`
Types are canonicalized/interned where practical.

### `ATYPE-30`
`unit` has exactly one semantic value.

### `ATYPE-31`
`never` represents non-returning computation.

### `ATYPE-32`
The safe Core has no null type/value.

### `ATYPE-33`
Absence is represented by `Option`.

### `ATYPE-34`
Failure is represented by `Result` or explicit fatal semantics.

### `ATYPE-35`
`view<T>` is non-owning read capability.

### `ATYPE-36`
`mut_view<T>` is non-owning exclusive mutable capability.

### `ATYPE-37`
View semantics are distinct from ownership semantics.

### `ATYPE-38`
`view<T>` is not equivalent to semantic `Copy`.

### `ATYPE-39`
`mut_view<T>` cannot be freely duplicated.

### `ATYPE-40`
Function types do not contain closure environments.

### `ATYPE-41`
Capturing closures have distinct environment-bearing types.

### `ATYPE-42`
Noncapturing closures may coerce to compatible function types.

### `ATYPE-43`
Generic parameters are explicit type variables.

### `ATYPE-44`
Type inference uses deterministic unification.

### `ATYPE-45`
Type inference supports contextual expected types.

### `ATYPE-46`
Ambiguous inference is diagnosed rather than guessed.

### `ATYPE-47`
Numeric defaulting occurs only when constraints leave a numeric type unresolved.

### `ATYPE-48`
Implicit numeric conversion is not generally permitted.

### `ATYPE-49`
Boolean and integer types are not implicitly interchangeable.

### `ATYPE-50`
Implicit coercions are a small explicitly defined set.

### `ATYPE-51`
Cast and bitcast have distinct semantics.

### `ATYPE-52`
Bitcast requires valid representation conditions.

### `ATYPE-53`
`dyn Trait` is explicit dynamic dispatch.

### `ATYPE-54`
Static generic dispatch is the default.

### `ATYPE-55`
Trait objects do not introduce hidden vtables into ordinary concrete types.

### `ATYPE-56`
Associated types are represented as semantic projections.

### `ATYPE-57`
Type normalization is semantic, not textual substitution.

### `ATYPE-58`
Recursive types must have finite physical representation.

### `ATYPE-59`
Infinite-size recursive types are rejected.

### `ATYPE-60`
`Copy`, `Clone`, `Drop`, `Send`, and `Share` are distinct semantic properties.

### `ATYPE-61`
A `Drop` type cannot be `Copy`.

### `ATYPE-62`
`Send` does not imply `Share`.

### `ATYPE-63`
`Share` does not imply mutable concurrent access.

### `ATYPE-64`
Type inference does not perform ownership verification.

### `ATYPE-65`
Type inference does not execute comptime code.

### `ATYPE-66`
Trait solving is a separate semantic subsystem.

### `ATYPE-67`
Type errors must not cause uncontrolled compiler failure.

### `ATYPE-68`
ErrorType is never valid input to final code generation.

### `ATYPE-69`
Type checking is independent of target machine optimization.

### `ATYPE-70`
Type checking is deterministic under parallel execution.

### `ATYPE-71`
Incremental type checking is semantically equivalent to clean type checking.

### `ATYPE-72`
Type information exposed to AI/IDE tools uses stable semantic identities.

---

# 101. Kiến trúc semantic đã hình thành

Axiom frontend bây giờ có ranh giới rất sạch:

```text
                    SOURCE
                       │
                    Lexer
                       │
                     CST
                       │
                     AST
                       │
                Name Resolution
                       │
                Resolved HIR
                       │
        ┌──────────────┼──────────────┐
        │              │              │
      TypeDB        TraitDB        ConstDB
        │              │              │
        └──────────────┼──────────────┘
                       │
                 Typed HIR
                       │
                  Comptime
                       │
                    HIR
                       │
                    MIR
```

Đặc biệt, **TypeDB không nên trở thành một “god object”**. Nó chỉ trả lời các câu hỏi về type. Ownership, capability, trait solving, const evaluation và concurrency vẫn là các subsystem riêng.

---

# BOOTSTRAP-130 — Trait System, Trait Solver & Static/Dynamic Polymorphism

Task tiếp theo sẽ khóa phần khó nhất ngay sau TypeDB:

```text
Typed HIR
   │
   ├── Trait obligations
   │
   ▼
Trait Solver
   │
   ├── impl selection
   ├── associated types
   ├── default methods
   ├── generic constraints
   ├── coherence
   ├── specialization
   ├── operator traits
   ├── Auto/marker properties
   └── dyn Trait / object safety
```

Đây là task quan trọng vì nó quyết định Axiom có đạt được ý tưởng **“không cần class/inheritance nhưng vẫn có polymorphism mạnh”** hay không.