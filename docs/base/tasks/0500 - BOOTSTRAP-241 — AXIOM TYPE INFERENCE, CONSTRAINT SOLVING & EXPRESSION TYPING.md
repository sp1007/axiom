# BOOTSTRAP-241 — AXIOM TYPE INFERENCE, CONSTRAINT SOLVING & EXPRESSION TYPING

**TRẠNG THÁI: FROZEN / COMPLETED**

Mục tiêu của task này là đóng băng cơ chế biến AST expression thành **Typed HIR** một cách deterministic, mạnh nhưng không biến Axiom thành dependent-type language.

Nguyên tắc trung tâm:

> **Compiler suy luận tối đa những gì có thể suy luận chắc chắn; programmer chỉ phải ghi những thông tin cần thiết để loại bỏ ambiguity.**

---

# 1. Vị trí trong compiler

```text
AST
 │
 ▼
Name Resolution
 │
 ▼
Expression Type Checker
 │
 ├── Expected-Type Propagation
 ├── Type Inference
 ├── Constraint Generation
 ├── Unification
 ├── Coercion
 ├── Trait Goals
 ├── Projection Normalization
 ├── Overload Resolution
 └── Generic Instantiation
 │
 ▼
Typed HIR
```

Typed HIR là **semantic boundary**.

Sau boundary này, compiler không còn làm việc với expression chưa biết type trong production compilation.

---

# 2. Bidirectional type checking

Axiom sử dụng hai chế độ:

```text
CHECK
INFER
```

### Infer

Compiler tự tìm type:

```axiom
let x = 10
```

suy ra:

```text
x : i32
```

### Check

Compiler đã có expected type:

```axiom
let x: i64 = 10
```

literal được check với:

```text
expected = i64
```

Đây là cơ chế rất quan trọng để giữ inference mạnh nhưng predictable.

---

# 3. Không inference vô hạn

Axiom không cố suy luận mọi thứ.

Ví dụ:

```axiom
let x = []
```

không có đủ thông tin để xác định element type.

→ diagnostic.

Không tự chọn:

```text
Vec<unknown>
Vec<i32>
Vec<u8>
```

---

# 4. Inference variable

Compiler dùng internal variables:

```text
?T0
?T1
?T2
```

Ví dụ:

```axiom
let x = 10
```

ban đầu:

```text
10 : ?T0
```

numeric literal constraint:

```text
?T0 = integer-literal-compatible-type
```

defaulting rule cuối cùng chọn `i32` nếu không có constraint khác.

---

# 5. Constraint graph

Ví dụ:

```axiom
let x = foo(10)
```

có thể tạo:

```text
?T0 = type(10)
?T1 = return_type(foo)
?T1 = type(x)
```

Trait constraints cũng nằm trong graph:

```text
?T0: Display
```

---

# 6. Constraint categories

Axiom v1 có các constraint chính:

```text
TypeEqual(A, B)

Subtype/Compatibility(A, B)
```

Nhưng **không có general subtype hierarchy**.

Do đó compatibility chủ yếu là:

```text
Coercible(A, B)
Assignable(A, B)
```

và:

```text
Implements(T, Trait)

ProjectionEquals(P, T)

ConstEquals(A, B)

WellFormed(T)
```

---

# 7. Unification

Hai type:

```text
?T
i32
```

unify:

```text
?T = i32
```

Hai compound types:

```text
Vec<?T>
Vec<i64>
```

unify:

```text
?T = i64
```

---

# 8. Structural unification

```text
Pair<?A, ?B>
Pair<i32, f64>
```

→

```text
?A = i32
?B = f64
```

---

# 9. Nominal types không unify tùy ý

```axiom
struct UserId(u64)
struct ProductId(u64)
```

Không:

```text
UserId == u64
ProductId == u64
UserId == ProductId
```

dù representation giống nhau.

`@repr(transparent)` chỉ ảnh hưởng representation/ABI, không xóa nominal identity.

---

# 10. Type aliases

```axiom
type UserId = u64
```

là alias.

Do đó:

```text
UserId
```

normalize thành:

```text
u64
```

khác hoàn toàn:

```axiom
struct UserId(u64)
```

---

# 11. Expected type propagation

Ví dụ:

```axiom
let x: i64 = 10
```

thay vì:

```text
literal → i32 → cast → i64
```

compiler có thể check trực tiếp:

```text
expected i64
literal 10
```

để giữ semantic sạch.

---

# 12. Numeric literal inference

Literal integer:

```text
0
1
42
1000
```

ban đầu không nhất thiết gắn ngay `i32`.

Compiler tạo literal constraint.

Ví dụ:

```axiom
let x: u64 = 42
```

→ `42 : u64`.

---

# 13. Numeric defaulting

Nếu không có expected type:

```axiom
let x = 42
```

Axiom v1 default:

```text
i32
```

Tương tự floating literal:

```axiom
let x = 3.14
```

→

```text
f64
```

nếu không có constraint khác.

Defaulting chỉ xảy ra ở **cuối inference**.

---

# 14. Không implicit numeric chain

Ví dụ:

```axiom
let x: f64 = 1
```

được phép bởi literal typing.

Nhưng:

```axiom
let a: i32 = ...
let b: f64 = a
```

không tự động biến thành:

```text
i32 → f64
```

Phải cast:

```axiom
let b = a as f64
```

---

# 15. Boolean

```axiom
if x { ... }
```

yêu cầu:

```text
x : bool
```

Không có truthiness kiểu C:

```text
if 1
if ptr
if object
```

---

# 16. Unit

Expression không trả value hữu ích:

```axiom
fn log() {
    ...
}
```

có:

```text
log() : unit
```

Block:

```axiom
{
    foo()
    bar()
}
```

type là type của final expression.

Nếu không có final expression:

```text
unit
```

---

# 17. Never

Expression:

```axiom
return ...
panic(...)
```

có type:

```text
never
```

`never` có thể flow vào mọi context cần một value type bởi vì expression không bao giờ tạo value.

Ví dụ:

```axiom
let x: i32 =
    if condition {
        42
    } else {
        panic(...)
    }
```

hợp lệ.

---

# 18. If expression

```axiom
let x =
    if cond {
        10
    } else {
        20
    }
```

Compiler tạo constraint:

```text
cond : bool

type(branch1) = ?T
type(branch2) = ?T
```

→ `?T = i32`.

---

# 19. If không có else

```axiom
if cond {
    foo()
}
```

type:

```text
unit
```

Không được dùng như arbitrary value.

---

# 20. Branch với never

```axiom
let x =
    if cond {
        10
    } else {
        panic(...)
    }
```

Compiler bỏ qua `never` khi xác định common type:

```text
x : i32
```

---

# 21. Block typing

```axiom
{
    let a = 10
    let b = 20
    a + b
}
```

type:

```text
i32
```

Final expression là semantic result.

---

# 22. Statement position

Nếu expression có value nhưng được dùng như statement:

```axiom
foo()
42
```

`42` cuối block có giá trị.

Nhưng:

```axiom
foo()
bar()
```

block type:

```text
unit
```

---

# 23. Function return checking

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

compiler check:

```text
type(block) == i32
```

---

# 24. Return

```axiom
return value
```

check:

```text
type(value) coercible-to declared-return-type
```

Không cần inference return type cho function public trong v1.

Khuyến nghị:

> Function return type luôn explicit.

Điều này giúp API stable và diagnostics tốt.

---

# 25. Local function inference

Local closure có thể infer return:

```axiom
let f = |x| x + 1
```

Compiler infer:

```text
F(?T) -> ?U
```

Sau constraint solving:

```text
?T = i32
?U = i32
```

nếu context đủ mạnh.

---

# 26. Closure parameter ambiguity

```axiom
let f = |x| x
```

không có context.

Compiler không nên tự đoán:

```text
i32
```

Có thể giữ polymorphism nội bộ nếu closure nằm trong generic-compatible context, nhưng closure value thông thường cần concrete type trước khi codegen.

Nếu không resolve được:

→ diagnostic.

---

# 27. Generic function call

```axiom
fn max<T: Ord>(a: T, b: T) -> T
```

Call:

```axiom
max(10, 20)
```

Inference:

```text
T = i32
```

Sau đó solver:

```text
i32: Ord
```

→ Proven.

---

# 28. Generic inference từ nhiều arguments

```axiom
fn pair<T>(a: T, b: T) -> Pair<T>
```

```axiom
pair(1, 2)
```

→ `T = i32`.

Nhưng:

```axiom
pair(1, 2.0)
```

→ conflict:

```text
T = i32
T = f64
```

→ type error.

Không tự tìm common supertype.

---

# 29. Generic inference từ return context

```axiom
fn make<T>() -> T
```

```axiom
let x: User = make()
```

Expected type truyền vào:

```text
T = User
```

→ hợp lệ nếu constraints thỏa.

---

# 30. Unused generic parameter

```axiom
fn make<T>() -> T
```

nếu call:

```axiom
make()
```

và không có expected type:

```text
T unresolved
```

→ diagnostic.

---

# 31. Explicit generic arguments

Axiom cho phép disambiguation:

```axiom
make<User>()
```

hoặc dạng canonical tương đương mà grammar đã frozen.

Explicit generic arguments **không phải bypass inference**; chúng cung cấp constraints ban đầu.

---

# 32. Function overload

Axiom **không nên có arbitrary function overloading theo tên** trong Core v1.

Ví dụ không cho:

```axiom
fn foo(i32)
fn foo(f64)
```

cùng namespace chỉ vì parameter types khác nhau.

Điều này làm name resolution và diagnostics phức tạp.

---

# 33. Generic thay cho overload

Dùng:

```axiom
fn foo<T: Numeric>(x: T)
```

hoặc trait dispatch.

---

# 34. Operator resolution

Operator:

```axiom
a + b
```

được semantic hóa thành trait operation tương ứng.

Conceptually:

```text
Add::add(a, b)
```

Type inference xác định:

```text
type(a)
type(b)
result type
```

sau đó Trait Solver resolve implementation.

---

# 35. Không resolve operator trước type inference

Sai:

```text
operator "+"
↓
choose Add<i32>
```

Đúng:

```text
expression operands
↓
infer types
↓
candidate Add implementations
↓
solve constraints
↓
select implementation
```

---

# 36. Method call

```axiom
x.foo(a)
```

không trực tiếp được coi là một function symbol.

Pipeline:

```text
x
↓
infer receiver type
↓
discover method candidates
↓
filter visibility
↓
trait solver
↓
generic inference
↓
select candidate
↓
canonical callable
```

---

# 37. Field access

```axiom
x.name
```

resolver xác định `x`.

Type checker xác định:

```text
type(x)
```

sau đó lookup field.

Không gọi trait method nếu field tồn tại.

Field và method namespace được phân biệt.

---

# 38. Indexing

```axiom
a[i]
```

có semantic protocol tương ứng, ví dụ `Index`.

Compiler check:

```text
type(a)
type(i)
result type
```

Bounds safety được verifier/optimizer xử lý ở MIR.

---

# 39. Slice

```axiom
a[start:end]
```

expected result thường là view hoặc collection API tương ứng tùy receiver.

Không tự động copy dữ liệu chỉ vì slicing.

---

# 40. Struct literal

```axiom
Point {
    x: 1
    y: 2
}
```

Expected type hoặc explicit constructor identity phải xác định:

```text
Point
```

Sau đó từng field được check.

---

# 41. Không infer struct identity từ field names

Nếu:

```axiom
struct A { x: i32 }
struct B { x: i32 }
```

thì:

```axiom
{ x: 1 }
```

không tự chọn `A` hoặc `B`.

Expected type phải xác định.

---

# 42. Enum constructor

```axiom
Some(10)
```

compiler cần biết enum constructor identity.

Nếu có nhiều `Some` candidate:

```text
Option::Some
Other::Some
```

resolution không được đoán.

---

# 43. Pattern typing

Pattern:

```axiom
match x {
    Some(v) => ...
    None => ...
}
```

type của `x` phải được biết trước khi pattern binding được type-check.

Pipeline:

```text
scrutinee type
↓
pattern constructor lookup
↓
pattern field binding
↓
branch environment
```

---

# 44. Match branch type

Tất cả branch phải có compatible result:

```axiom
match x {
    A => 10
    B => 20
}
```

→ `i32`.

Nếu:

```axiom
A => 10
B => "hello"
```

→ type error.

---

# 45. Match + never

```axiom
match x {
    Some(v) => v
    None => panic(...)
}
```

Nếu `v : i32`:

```text
match : i32
```

---

# 46. `?` operator

```axiom
let x = foo()?
```

Type checker phải biết:

```text
foo() : Result<T, E>
```

hoặc Option-compatible context.

Result propagation tạo constraint cho enclosing function return.

---

# 47. Không implicit error conversion tùy tiện

Nếu:

```text
foo() : Result<T, E1>
function : Result<U, E2>
```

thì E1→E2 chỉ hợp lệ nếu có conversion contract rõ ràng.

Không tạo chuỗi conversion vô hạn.

---

# 48. Coercion engine

Coercion là một hệ thống riêng:

```text
CoercionEngine
```

không phải Trait Solver tổng quát.

Các coercion Core:

```text
owner → ephemeral view<T>
owner → ephemeral mut_view<T>
Array → view<T>
mutable capability → read capability
never → T
```

và các coercion compiler-defined khác đã được frozen.

---

# 49. Coercion không chain vô hạn

Ví dụ compiler không thử:

```text
A → B → C → D → E
```

một cách tùy tiện.

Chỉ whitelist conversion/coercion edges.

---

# 50. Explicit cast

```axiom
x as f64
```

được type-check trực tiếp.

Không chạy generic overload resolution để tìm một conversion ngẫu nhiên.

---

# 51. `as` không phải `From`

```text
as
```

là primitive/compiler-defined cast.

```text
From/Into/TryFrom
```

là trait/library conversion.

Hai cơ chế không được trộn.

---

# 52. Closure typing

Closure:

```axiom
|x, y| x + y
```

internal:

```text
ClosureType {
    Params: [?T0, ?T1]
    Return: ?T2
    Captures: [...]
}
```

Sau inference:

```text
(?T0, ?T1) -> ?T2
```

---

# 53. Capture typing

```axiom
let offset = 10
let f = |x| x + offset
```

closure environment chứa semantic capture của `offset`.

Capture mode do ownership analysis xác định.

Type inference chỉ xác định type.

Hai phase không được nhập thành một mechanism mơ hồ.

---

# 54. Function pointer vs closure

```text
fn(i32) -> i32
```

khác:

```text
closure type
```

Capturing closure không tự decay thành function pointer.

Noncapturing closure có thể được compiler chuyển thành function pointer khi ABI/semantic context cho phép.

---

# 55. Async expression typing

```axiom
async fn foo() -> i32
```

function's logical result:

```text
Future<i32>
```

`await`:

```text
foo().await
```

cho:

```text
i32
```

Trait/async machinery được resolver + lowering xử lý sau typing.

---

# 56. `await` không thay đổi ordinary type inference rules

Ví dụ:

```axiom
let x = foo().await
```

infer:

```text
foo() : Future<?T>
await : ?T
x : ?T
```

---

# 57. Generic async

```axiom
async fn map<T, U, F>(...)
where
    F: Fn(T) -> U
```

Type inference resolve generic parameters trước khi async lowering hoàn thiện.

---

# 58. Comptime typing

```axiom
const X: i32 = 10
```

normal type checker xử lý.

Sau đó comptime evaluator thực thi value.

Không có type checker riêng cho comptime.

---

# 59. Compile-time type equality

```axiom
comptime {
    ...
}
```

có thể query:

```text
size_of<T>()
align_of<T>()
```

và compiler lấy TypeDB/LayoutDB facts.

---

# 60. Generic trait constraints trong inference

Ví dụ:

```axiom
fn print<T: Display>(x: T)
```

call:

```axiom
print(user)
```

Inference:

```text
T = User
```

Constraint:

```text
User: Display
```

→ Trait Solver.

---

# 61. Associated type inference

```axiom
fn first<I: Iterator>(x: I) -> I::Item
```

Call context:

```axiom
let x: i32 = first(iter)
```

Compiler có:

```text
I = type(iter)
I::Item = i32
```

Projection normalization/trait solver kiểm tra consistency.

---

# 62. Ambiguous associated type

Nếu:

```text
I::Item
```

chưa resolve được:

```text
I::Item = ?
```

không tự chọn type.

→ unresolved/ambiguous diagnostic.

---

# 63. Trait method generic inference

```axiom
trait Convert {
    fn convert<T>(self: view<Self>) -> T
}
```

Call:

```axiom
let x: String = value.convert()
```

expected type cung cấp:

```text
T = String
```

Sau đó solver kiểm tra constraints.

---

# 64. Inference order

Axiom sử dụng logical constraint solving, không phụ thuộc thứ tự expression được visited.

Có thể implementation dùng worklist:

```text
Generate constraints
        ↓
Normalize
        ↓
Unify
        ↓
Resolve traits
        ↓
Apply resulting facts
        ↓
Repeat until fixed point
```

---

# 65. Fixed point

Inference kết thúc khi:

```text
ConstraintSet_new == ConstraintSet_old
```

hoặc tất cả inference variables đã:

```text
Resolved
```

---

# 66. Không dùng “thử tất cả kiểu”

Không được implement kiểu:

```text
try i8
try i16
try i32
try i64
try u8
...
```

cho mọi expression.

Điều đó gây compile-time explosion và diagnostics kém.

Inference phải dựa trên constraints.

---

# 67. Candidate ranking

Khi có nhiều candidate conversion/method/trait:

```text
Exact
↓
Known coercion
↓
Generic instantiation
↓
Trait candidate
```

nhưng ranking phải được formalize.

Không được:

```text
first match wins
```

---

# 68. Ambiguity là lỗi semantic

Ví dụ:

```axiom
foo(x)
```

nếu có hai callable candidates hoàn toàn hợp lệ và không có rule phân biệt:

```text
AmbiguousCall
```

Không chọn candidate đầu tiên.

---

# 69. Type inference không sửa source

Compiler không tự biến:

```axiom
foo(x)
```

thành:

```axiom
bar(x)
```

chỉ vì `bar` “có vẻ phù hợp”.

AI/tooling có thể đề xuất sửa, nhưng production compiler phải deterministic.

---

# 70. Error recovery

Trong Partial Semantic Mode:

```text
ErrorType
```

có thể tiếp tục type-check phần còn lại.

Ví dụ:

```axiom
let x = missing_name
let y = 42
```

`x` có ErrorType nhưng `y` vẫn được type-check.

---

# 71. ErrorType không phải real type

`ErrorType`:

```text
recovery-only
```

không thể:

```text
enter Verified MIR
satisfy trait goal
prove ownership
prove ABI
```

---

# 72. Type inference failure categories

Diagnostic phân biệt:

```text
TypeMismatch
UnresolvedType
AmbiguousType
InvalidCoercion
InvalidCast
UnsatisfiedTrait
AmbiguousTrait
AmbiguousCall
ProjectionFailure
ProjectionAmbiguity
GenericArgumentMismatch
```

---

# 73. Source diagnostic example

Ví dụ:

```axiom
let x: i32 = "hello"
```

không chỉ:

```text
type mismatch
```

mà semantic diagnostic:

```text
expected: i32
found: Str/string literal
conversion: no implicit coercion exists
suggestion: explicit parsing/conversion if intended
```

---

# 74. Type checking pipeline hoàn chỉnh

```text
check_expr(expr, expected?)
        │
        ├── literal
        ├── name
        ├── unary
        ├── binary
        ├── call
        ├── method
        ├── field
        ├── index
        ├── slice
        ├── struct
        ├── enum
        ├── closure
        ├── block
        ├── if
        ├── match
        ├── loop
        ├── await
        ├── cast
        └── comptime
        │
        ▼
ConstraintSet
        │
        ▼
Normalize
        │
        ▼
Unify
        │
        ▼
Trait Solver
        │
        ▼
Coercion
        │
        ▼
Fully Typed Expression
```

---

# 75. Typed HIR

AST:

```text
CallExpr
 ├── NameExpr("max")
 ├── Literal(10)
 └── Literal(20)
```

Typed HIR:

```text
Call {
    FunctionId: max::<i32>
    Args: [
        Literal<i32>(10),
        Literal<i32>(20)
    ]
    ResultType: i32
}
```

Sau bước này backend semantic không cần đoán `max` là gì nữa.

---

# 76. Typed HIR phải explicit

Typed HIR nên chứa:

```text
resolved DeclarationId
resolved TypeId
resolved Trait/Impl where needed
resolved GenericInstanceId
resolved coercions
resolved associated projections
resolved callable identity
```

Điều này cực kỳ quan trọng cho AI tooling và incremental compiler.

---

# 77. Type identity

Mỗi resolved type dùng:

```text
TypeId
```

được intern trong TypeDB.

Ví dụ:

```text
i32
Vec<i32>
Option<User>
fn(i32)->f64
view<User>
```

mỗi type canonical có identity ổn định trong compiler revision.

---

# 78. Type normalization

Trước khi so sánh type:

```text
Alias
Projection
Generic substitution
```

được normalize theo context.

Ví dụ:

```text
type Id = u64

Id
```

→ `u64`.

Nhưng:

```text
struct Id(u64)
```

→ giữ nominal identity.

---

# 79. Recursive types

Type:

```axiom
struct Node {
    next: Option<Box<Node>>
}
```

được phép vì có indirection.

Nhưng:

```axiom
struct Node {
    next: Node
}
```

→ infinite-size type.

Diagnostic phải xảy ra tại layout/type well-formedness.

---

# 80. Sized constraint

Mặc định generic type:

```text
T
```

phải có known size nếu được dùng ở vị trí yêu cầu sized representation.

Unsized/view-like semantics phải explicit.

Axiom có thể dùng:

```text
?Sized
```

hoặc cơ chế tương đương nếu cần sau khi grammar/trait system hoàn thiện, nhưng không nên thêm syntax nếu không cần.

---

# 81. Type inference và ownership tách biệt

Ví dụ:

```axiom
let b = a
```

Type inference chỉ biết:

```text
type(b) = type(a)
```

Move semantics được quyết định ở ownership verification.

Không gộp hai hệ thống thành một.

---

# 82. Type inference và capability tách biệt

```axiom
foo(x)
```

Typing xác định:

```text
foo(view<T>)
```

Capability verifier mới quyết định:

```text
x → ephemeral read capability
```

và lifetime.

---

# 83. Type inference và layout tách biệt

Compiler không cần biết:

```text
size_of(T)
alignment
padding
register class
```

để resolve ordinary type expressions.

Layout phase sau đó mới xử lý.

---

# 84. Type inference và optimization tách biệt

Inference không dựa trên:

```text
inline
constant folding
target instruction
vectorization
```

Một program phải có cùng semantic typing ở:

```text
-O0
-O2
-Osize
-PGO
```

---

# 85. Inference và target

Thông thường:

```text
let x = 42
```

→ `i32`

không thay đổi theo CPU.

Những type phụ thuộc target phải có explicit target semantics, ví dụ:

```text
usize
isize
SIMD width
ABI-specific types
```

Compiler lấy TargetSpec facts.

---

# 86. Inference caching

Cache key có thể gồm:

```text
ExpressionFingerprint
ExpectedType
GenericEnvironment
ModuleEnvironment
TraitEnvironment
FeatureSet
CompilerSemanticVersion
```

Result:

```text
TypedExpression
ConstraintSummary
Diagnostics
```

---

# 87. Incremental invalidation

Thay đổi:

```text
fn unrelated() ...
```

không được khiến toàn bộ expressions re-type-check.

Dependency graph:

```text
Expression
 ↓
DeclarationId
 ↓
TypeId / TraitId / ImplId
```

giúp invalidation chính xác.

---

# 88. Parallel type checking

Các function độc lập có thể type-check song song.

Ví dụ:

```text
foo()
bar()
baz()
```

nếu không phụ thuộc semantic declarations chưa hoàn thành.

Kết quả phải deterministic.

---

# 89. Type checker không tự sửa declaration graph

Nếu type checker phát hiện:

```text
foo → bar
bar → foo
```

thì resolver/module graph đã chịu trách nhiệm xử lý declaration cycle.

Type checker chỉ xử lý semantic type dependencies.

---

# 90. Recursive generic constraints

Ví dụ:

```text
T: A
A<T>: B
B: C
```

solver/type inference phải sử dụng canonical goals và cycle detection của Trait Solver.

Không tạo solver riêng.

---

# 91. Constraint phases

Đề xuất implementation:

```text
Phase 1:
    Local syntax typing

Phase 2:
    Type unification

Phase 3:
    Generic inference

Phase 4:
    Projection normalization

Phase 5:
    Trait solving

Phase 6:
    Coercion insertion

Phase 7:
    Final type validation

Phase 8:
    Typed HIR emission
```

Không nhất thiết mỗi phase là pass riêng; đây là semantic ordering.

---

# 92. Typed HIR invariants

Khi expression đã vào Typed HIR:

```text
Every Name → DeclarationId
Every Expression → TypeId
Every Call → Callable Identity
Every Generic Instance → Resolved Substitution
Every Trait Obligation → Proven
Every Coercion → Explicit HIR node
Every Projection → Normalized or explicitly deferred where legal
```

Không còn “compiler đoán tiếp” ở MIR.

---

# 93. Coercion được materialize trong HIR

Ví dụ:

```axiom
foo(string)
```

nếu parameter yêu cầu `Str`:

AST:

```text
Call(foo, string)
```

Typed HIR:

```text
Call(
    foo,
    Coerce(
        StringToStr,
        string
    )
)
```

Điều này cực kỳ quan trọng cho optimizer và verifier.

---

# 94. Move không phải coercion

```axiom
let b = a
```

không tạo:

```text
MoveCoercion
```

Move là semantic ownership operation được biểu diễn ở MIR.

---

# 95. Trait obligation trong Typed HIR

Ví dụ:

```axiom
max(a, b)
```

sau inference:

```text
T = i32
```

Typed HIR có thể giữ:

```text
GenericInstance:
    max::<i32>

ResolvedTraitFacts:
    i32: Ord
```

sau đó MIR không cần chạy Trait Solver lại.

---

# 96. Error boundary

```text
AST
 ↓
Typed HIR
```

là boundary:

```text
No unresolved ordinary type
No unresolved name
No unresolved generic callable
No ambiguous method
No unresolved required trait goal
```

ngoại trừ các symbolic constructs được thiết kế riêng cho later lowering.

---

# 97. Không đưa inference vào MIR

MIR phải nhận:

```text
fully typed semantic operations
```

Ví dụ không có:

```text
Add(unknown, unknown)
```

mà:

```text
Add<i32>
```

hoặc semantic operation đã resolve.

---

# 98. Formal typing judgment

Axiom có thể mô hình hóa:

```text
Γ ⊢ e ⇒ T
```

nghĩa:

> trong environment Γ, expression `e` infer ra type T.

Check:

```text
Γ ⊢ e ⇐ T
```

nghĩa:

> expression `e` được kiểm tra với expected type T.

Đây là nền tảng formal semantics rất sạch.

---

# 99. Constraint judgment

Ví dụ:

```text
Γ ⊢ e ⇒ T | C
```

expression tạo:

```text
T
+
constraints C
```

Sau solver:

```text
Solve(C) = Proven
```

thì Typed HIR được tạo.

---

# 100. Completion criteria

Task 241 chỉ được coi là hoàn thành khi compiler test chứng minh:

```text
✓ literals
✓ variables
✓ blocks
✓ if
✓ match
✓ functions
✓ generics
✓ closures
✓ operators
✓ method calls
✓ associated types
✓ casts
✓ coercions
✓ Option/Result/?
✓ async/await
✓ comptime expressions
✓ ambiguous inference
✓ trait obligations
✓ projection normalization
✓ ErrorType recovery
✓ deterministic diagnostics
```

---

# 101. Invariants đóng băng

```text id="f7p2qs"
ATYPEINF-20
Axiom uses bidirectional type checking.

ATYPEINF-21
Expression typing has distinct Infer and Check modes.

ATYPEINF-22
Inference uses explicit inference variables.

ATYPEINF-23
Inference is constraint-driven rather than exhaustive type guessing.

ATYPEINF-24
Type unification is deterministic.

ATYPEINF-25
Nominal types never unify merely because their representations match.

ATYPEINF-26
Type aliases normalize to their aliased identity.

ATYPEINF-27
Newtypes preserve distinct nominal identity.

ATYPEINF-28
Expected types propagate into expression checking.

ATYPEINF-29
Numeric literal defaulting occurs only after ordinary constraints are exhausted.

ATYPEINF-30
Integer literals default to i32 when unconstrained.

ATYPEINF-31
Floating literals default to f64 when unconstrained.

ATYPEINF-32
Boolean conditions require bool.

ATYPEINF-33
Blocks derive their value type from their final expression.

ATYPEINF-34
Blocks without a value expression have type unit.

ATYPEINF-35
Never expressions may inhabit arbitrary expected value contexts.

ATYPEINF-36
If branches must produce compatible types.

ATYPEINF-37
Match branches must produce compatible types.

ATYPEINF-38
Function return types are checked against declared return types.

ATYPEINF-39
Public function APIs do not depend on uncontrolled return-type inference.

ATYPEINF-40
Generic inference uses constraints from arguments and expected results.

ATYPEINF-41
Unresolved generic parameters produce diagnostics.

ATYPEINF-42
Generic inference never invents arbitrary common supertypes.

ATYPEINF-43
Axiom v1 has no arbitrary function overloading by parameter signature.

ATYPEINF-44
Operator resolution occurs after operand typing.

ATYPEINF-45
Method resolution occurs after receiver typing.

ATYPEINF-46
Field lookup is distinct from method lookup.

ATYPEINF-47
Struct literal identity must be semantically determined.

ATYPEINF-48
Enum constructor identity must be semantically determined.

ATYPEINF-49
Pattern typing occurs after scrutinee typing.

ATYPEINF-50
The ? operator requires a compatible Result/Option propagation context.

ATYPEINF-51
Implicit numeric conversion is not general coercion.

ATYPEINF-52
Explicit casts are distinct from trait-based conversions.

ATYPEINF-53
Coercions are whitelist-defined semantic conversions.

ATYPEINF-54
Coercion resolution cannot perform unbounded conversion chains.

ATYPEINF-55
Owner-to-ephemeral-view conversion is represented explicitly in Typed HIR.

ATYPEINF-56
Move semantics are distinct from type coercion.

ATYPEINF-57
Ownership verification is separate from type inference.

ATYPEINF-58
Capability verification is separate from type inference.

ATYPEINF-59
Layout computation is separate from type inference.

ATYPEINF-60
Optimization cannot determine source-level typing.

ATYPEINF-61
Type inference is independent of optimization level.

ATYPEINF-62
Type inference is independent of machine instruction selection.

ATYPEINF-63
Trait obligations generated by inference are solved by the canonical Trait Solver.

ATYPEINF-64
Associated type projections are canonical semantic type expressions.

ATYPEINF-65
Projection normalization is deterministic.

ATYPEINF-66
Ambiguous projections are never silently selected.

ATYPEINF-67
Ambiguous calls are compile-time errors.

ATYPEINF-68
Ambiguous type variables are compile-time errors when required for code generation.

ATYPEINF-69
The compiler never resolves ambiguity using source order.

ATYPEINF-70
The compiler never resolves ambiguity using implementation discovery order.

ATYPEINF-71
ErrorType exists only for Partial Semantic Mode.

ATYPEINF-72
ErrorType cannot satisfy production semantic obligations.

ATYPEINF-73
Typed HIR contains resolved DeclarationIds.

ATYPEINF-74
Typed HIR contains resolved TypeIds.

ATYPEINF-75
Typed HIR contains explicit generic substitutions.

ATYPEINF-76
Typed HIR materializes semantic coercions.

ATYPEINF-77
Production Typed HIR contains no unresolved ordinary name.

ATYPEINF-78
Production Typed HIR contains no unresolved ordinary type.

ATYPEINF-79
Production Typed HIR contains no unresolved required trait obligation.

ATYPEINF-80
Inference is deterministic across compilation order.

ATYPEINF-81
Independent inference tasks may execute in parallel.

ATYPEINF-82
Incremental inference results are cacheable.

ATYPEINF-83
Inference caches depend on semantic environment fingerprints.

ATYPEINF-84
Unrelated declaration changes do not invalidate unrelated inference results.

ATYPEINF-85
Constraint solving reaches a deterministic fixed point.

ATYPEINF-86
Compiler resource exhaustion is distinct from semantic ambiguity.

ATYPEINF-87
Resource exhaustion cannot produce a false successful typing result.

ATYPEINF-88
Type diagnostics preserve source and semantic provenance.

ATYPEINF-89
Type diagnostics expose expected type, found type and relevant constraints where available.

ATYPEINF-90
AI tooling consumes compiler-produced type facts rather than reimplementing inference.

ATYPEINF-91
Generated code passes the same type inference and checking pipeline.

ATYPEINF-92
Comptime expressions use the same type system.

ATYPEINF-93
GPU expressions use the same foundational type inference.

ATYPEINF-94
FFI expressions use the same type system plus explicit ABI contracts.

ATYPEINF-95
No inference mechanism may bypass the semantic verifier.

ATYPEINF-96
Inference complexity must not introduce mandatory runtime machinery.

ATYPEINF-97
Static generic inference does not imply dynamic dispatch.

ATYPEINF-98
Type inference does not determine physical storage location.

ATYPEINF-99
Type inference does not determine allocation strategy.

ATYPEINF-100
Typed HIR is the semantic typing boundary before MIR construction.
```

---

# 102. Kiến trúc Axiom sau 241

Chúng ta hiện đã có một chuỗi khá hoàn chỉnh:

```text
Lexer
  ↓
Parser
  ↓
Name Resolution
  ↓
Type System
  ↓
Trait Solver
  ↓
Type Inference
  ↓
Typed HIR
  ↓
MIR
  ↓
Ownership / Capability Verification
  ↓
Optimization
  ↓
ABI
  ↓
LIR
  ↓
Machine Code
```

Điểm quan trọng là **không còn cần thêm một “magic inference engine” nào nữa**. Type inference chỉ tạo constraint; Trait Solver giải trait; Ownership verifier giải ownership; Capability verifier giải access/lifetime.

Mỗi hệ thống có một trách nhiệm rõ ràng.

---

## TASK TIẾP THEO

### **BOOTSTRAP-242 — AXIOM CONVERSION, COERCION & OVERLOAD/OPERATOR RESOLUTION ENGINE**

Task tiếp theo sẽ đóng băng sâu hơn phần hiện mới được 241 sử dụng:

```text
Expression
    ↓
Type
    ↓
Coercion
    ↓
Operator
    ↓
Method
    ↓
Generic
    ↓
Trait
    ↓
Callable
```

Đặc biệt cần giải quyết thật chặt:

- khi nào `String → Str` được implicit;
- khi nào `Array → view`;
- `mut_view → view`;
- numeric literal vs numeric cast;
- operator `+ - * / == < []`;
- method candidate ranking;
- trait method vs inherent method;
- extension method;
- generic method;
- coercion + generic inference;
- tránh conversion-chain explosion;
- tránh ambiguity;
- và quan trọng nhất: **compiler phải “thông minh” nhưng programmer không phải viết thêm syntax để giúp compiler**.