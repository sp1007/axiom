# BOOTSTRAP-278 — AXIOM TYPE INFERENCE, CONSTRAINT GENERATION & OVERLOAD RESOLUTION
## FROZEN / COMPLETED

Đây là bước nối trực tiếp sau **BOOTSTRAP-277 — Type Representation & Type Interning Engine**.

Mục tiêu của 278 là giải quyết một vấn đề rất quan trọng của Axiom:

> **Programmer viết ít thông tin kiểu, nhưng compiler vẫn phải suy ra đúng, deterministic, nhanh và giải thích được tại sao nó chọn kiểu/hàm đó.**

Axiom không nên biến type inference thành “đoán mò”. Mọi suy luận đều phải trở thành **constraint**, được giải quyết bằng các luật xác định.

---

# 1. Mục tiêu thiết kế

Axiom type inference phải đạt đồng thời:

1. Không bắt programmer ghi type ở mọi nơi.
2. Không có dynamic typing.
3. Không có implicit conversion tùy tiện.
4. Generic inference tự động.
5. Overload resolution deterministic.
6. Trait constraints được tích hợp.
7. Closure có thể suy ra parameter/result.
8. `match`, block, `if`, `?`, `return` đều tham gia constraint system.
9. Compiler giải thích được:
   - biến được suy ra kiểu gì;
   - candidate nào được chọn;
   - candidate nào bị loại;
   - constraint nào thất bại.
10. Không phụ thuộc thứ tự traversal nội bộ hoặc số worker.
11. Không để inference làm thay đổi ownership/capability semantics.

Nguyên tắc:

> **Inference determines what the programmer omitted; it must never invent semantics the programmer did not request.**

---

# 2. Pipeline

```text
Source
  ↓
AST
  ↓
Name Resolution
  ↓
Bidirectional Typing
  ↓
Constraint Generation
  ↓
Constraint Normalization
  ↓
Unification
  ↓
Trait Obligation Solving
  ↓
Associated-Type Resolution
  ↓
Overload Resolution
  ↓
Coercion Insertion
  ↓
Defaulting
  ↓
Generalization / Instantiation
  ↓
Typed HIR
  ↓
Ownership / Capability Verification
```

Quan trọng:

```text
Type Inference
    ≠
Trait Solver
    ≠
Ownership Verifier
    ≠
Overload Resolver
```

Chúng phối hợp nhưng không được nhập thành một subsystem khổng lồ.

---

# 3. Hai chiều typing

Axiom sử dụng **bidirectional typing**:

```text
synthesize:
expression → Type

check:
expression ← ExpectedType
```

Ví dụ:

```ax
let x = 10
```

Compiler synthesize:

```text
10 → ?T
```

sau đó literal constraints xác định:

```text
?T = integer-compatible
```

Trong:

```ax
let x: i32 = 10
```

compiler có expected type:

```text
10 ← i32
```

nên không cần suy đoán rộng.

---

# 4. Khi nào synthesize, khi nào check?

### Synthesize tốt cho:

```ax
foo
x
x.field
a + b
foo()
array[index]
```

### Check tốt cho:

```ax
let x: T = expr

return expr

if cond {
    expr
} else {
    expr
}

match x {
    ...
}

fn foo() -> T {
    expr
}
```

Các expression có expected type phải tận dụng expected type càng sớm càng tốt.

---

# 5. Inference Variable

Inference variable:

```text
?T0
?T1
?T2
...
```

là **compiler-internal**, không phải type của ngôn ngữ.

Ví dụ:

```ax
let x = identity(10)
```

ban đầu:

```text
identity(?A) -> ?A
10            -> ?B
```

Constraint:

```text
?A = ?B
```

Literal:

```text
?B = integer type
```

sau resolution:

```text
?A = ?B = i32
```

nếu default numeric policy chọn `i32`.

Inference variables:

- session-local;
- không được intern vào TypeDB như concrete type;
- không được xuất hiện trong Verified MIR;
- không được xuất hiện trong `.axmeta`.

---

# 6. Constraint model

Constraint cơ bản:

```text
TypeEq(T1, T2)
Subtype(T1, T2)        // không dùng general subtype trong Core
Coerce(T1, T2)
Implements(T, Trait)
ProjectionEq(<T as Trait>::Assoc, U)
Callable(F, Args, Return)
ConstEq(C1, C2)
WellFormed(T)
```

Do Axiom không có general subtype hierarchy, `Subtype` gần như không phải primitive inference chính.

Thay vào đó:

```text
Equality
Coercion
Trait obligation
Callable constraint
Projection constraint
```

là các primitive chính.

---

# 7. Unification

Unification giải:

```text
?T = i32
?A = ?B
Vec<?T> = Vec<i32>
```

Nhưng không được tự động giải:

```text
i32 = i64
```

và cũng không tự động biến:

```text
Array<T, N>
```

thành bất kỳ kiểu nào chỉ vì representation tương thích.

---

# 8. Occurs check

Compiler phải ngăn:

```text
?T = Vec<?T>
```

vì tạo type vô hạn.

Constraint:

```text
?T occurs in Vec<?T>
```

→ inference error.

Invariant:

```text
AINFER-20
Unification must perform occurs-check for recursive inference substitutions.
```

---

# 9. Unification algorithm

Logical algorithm:

```text
unify(A, B):

if A == B:
    success

if A is ?T:
    bind ?T = B

if B is ?T:
    bind ?T = A

if A and B are same type constructor:
    unify corresponding arguments

otherwise:
    fail
```

Nhưng implementation phải xử lý:

- inference variable union;
- occurs check;
- canonical representatives;
- immutable substitution snapshots;
- rollback;
- speculative overload candidates.

---

# 10. Inference không được mutate TypeDB

Ví dụ candidate overload:

```ax
foo(i32)
foo(f64)
```

Compiler thử candidate thứ nhất.

Nếu thất bại, không được để:

```text
?T = i32
```

rò rỉ sang candidate thứ hai.

Do đó overload solving sử dụng:

```text
InferenceSnapshot
```

hoặc equivalent rollback mechanism.

```text
Snapshot S0
    ↓
try candidate A
    ↓
failure
    ↓
rollback S0

try candidate B
```

---

# 11. Numeric literal inference

Đây là phần rất quan trọng.

Ví dụ:

```ax
let x = 10
```

Không nên ngay lập tức cố định `10` thành machine type chỉ vì parser thấy integer.

Literal ban đầu có semantic category:

```text
IntegerLiteral(10)
```

và tạo constraint:

```text
?T supports integer literal 10
```

Nếu expected type:

```ax
let x: u64 = 10
```

→ `u64`.

Nếu:

```ax
let x: i16 = 10
```

→ `i16`.

Nếu không có contextual constraint:

```ax
let x = 10
```

Axiom cần default deterministic.

### V0.1 default

Đề xuất:

```text
integer literal → i32
floating literal → f64
```

nếu không có constraint mạnh hơn.

Nhưng:

```ax
let x: u8 = 300
```

phải lỗi compile-time vì literal không representable trong `u8`.

Không silently wrap.

---

# 12. Numeric literal không phải implicit numeric conversion

Ví dụ:

```ax
let a: i32 = 10
let b: i64 = a
```

Không được tự động coi:

```text
i32 → i64
```

là inference.

Phải explicit:

```ax
let b: i64 = a as i64
```

hoặc một conversion mechanism đã được Core xác định.

Điều này giữ cho inference không biến thành implicit conversion engine.

---

# 13. Floating literals

```ax
let x = 1.5
```

→ default:

```text
f64
```

Nếu:

```ax
let x: f32 = 1.5
```

literal được kiểm tra trực tiếp theo `f32`.

Nếu precision loss có ý nghĩa semantic, compiler phải kiểm tra literal representability theo policy của numeric system.

---

# 14. Generic inference

Ví dụ:

```ax
fn identity<T>(x: T) -> T {
    x
}

let x = identity(42)
```

Constraints:

```text
identity<?T>(?A)
42 → ?B

?A = ?B
```

sau đó:

```text
?B = i32
```

→

```text
T = i32
return = i32
```

---

# 15. Generic inference từ nhiều argument

```ax
fn pair<T>(a: T, b: T) -> Pair<T>
```

:

```ax
pair(10, 20)
```

→

```text
T = i32
```

Nhưng:

```ax
pair(10, 20u64)
```

không tự động:

```text
T = i64
```

hoặc:

```text
T = u64
```

Nếu hai literal có contextual compatibility khác nhau thì solver phải xác định rõ. Nếu không có conversion rule hợp lệ:

```text
type mismatch
```

---

# 16. Generic inference có expected return type

Ví dụ:

```ax
fn make<T>() -> T

let x: Vec<i32> = make()
```

Expected type truyền ngược:

```text
make<?T>() -> ?T
expected = Vec<i32>

?T = Vec<i32>
```

→ generic được suy ra dù không có argument.

Đây là một lý do bidirectional typing rất quan trọng.

---

# 17. Partial inference

Cho phép:

```ax
let x = foo::<_, i32>(value)
```

Nếu Axiom surface syntax hỗ trợ explicit generic arguments, `_` có nghĩa:

```text
infer this argument
```

Ví dụ:

```ax
foo::<u32, _>(x)
```

Compiler chỉ suy ra các parameter còn thiếu.

---

# 18. Constraint priority

Không phải constraint nào cũng ngang nhau.

Thứ tự ưu tiên:

```text
1. Explicit programmer type
2. Exact type equality
3. Expected type
4. Generic structural constraints
5. Trait obligations
6. Finite coercions
7. Literal defaulting
```

Mục đích:

> Compiler không được “sáng tạo” một conversion để làm chương trình compile khi programmer đã cung cấp thông tin rõ ràng.

---

# 19. Coercion

Coercion là một hệ thống **finite và explicit trong compiler specification**.

Các coercion Core ban đầu:

```text
never → T
Array<T,N> → view<T>
String → Str
```

có thể có thêm những coercion đã được frozen ở các spec trước.

Không có:

```text
i32 → i64
f32 → f64
T → dyn Trait
```

một cách tùy tiện.

Đặc biệt:

```text
coercion ≠ conversion ≠ cast ≠ bitcast
```

---

# 20. Coercion insertion

Ví dụ:

```ax
fn sum(x: view<i32>) -> i32
```

gọi:

```ax
let a: [4]i32 = ...
sum(a)
```

Compiler:

```text
Array<i32,4>
    ↓
coercion
    ↓
view<i32>
```

Typed HIR phải lưu coercion explicit:

```text
Call(
    sum,
    MakeViewCoercion(a)
)
```

Không để coercion chỉ tồn tại trong inference state.

---

# 21. Overload resolution

Axiom cho phép overload có kiểm soát.

Ví dụ:

```ax
fn print(x: i32)
fn print(x: f64)
fn print(x: Str)
```

Call:

```ax
print(42)
```

Candidate set:

```text
print(i32)
print(f64)
print(Str)
```

Inference + contextual typing:

```text
42 → i32
```

Candidate:

```text
print(i32)
```

được chọn.

---

# 22. Candidate collection

Overload resolver **không tự tìm mọi function trong toàn bộ chương trình**.

Candidate source được giới hạn:

```text
1. lexical scope
2. module imports
3. inherent functions/methods
4. visible trait implementations
5. explicitly imported extension methods
6. language-defined operators
```

Điều này tránh:

- compile-time explosion;
- accidental ambiguity;
- namespace pollution.

---

# 23. Overload candidate record

Mỗi candidate:

```text
OverloadCandidate {
    declaration: FunctionId
    receiver: optional Type
    generic_params: ...
    instantiated_type: optional FunctionType
    constraints: ...
    coercions: ...
    trait_obligations: ...
    applicability: ...
    rejection_reason: ...
}
```

---

# 24. Candidate applicability

Một candidate có thể:

```text
Applicable
NotApplicable
Ambiguous
Error
```

Ví dụ:

```ax
foo(10)
```

Candidate:

```text
foo(i32)   → applicable
foo(Str)   → rejected: argument mismatch
foo<T>(T)  → applicable
```

Sau đó ranking quyết định candidate nào cụ thể hơn.

---

# 25. Overload ranking

Axiom không sử dụng “điểm số heuristic” không deterministic.

Thay vào đó sử dụng **partial ordering theo luật**.

Ưu tiên:

```text
1. Exact match
2. Match after inference
3. Non-coercive generic match
4. Finite implicit coercion
5. More specific concrete signature
6. More constrained generic signature
```

Nếu hai candidate vẫn tương đương:

```text
AMBIGUOUS
```

Không được chọn dựa trên:

- declaration order;
- hash order;
- file order;
- worker completion order.

---

# 26. Ví dụ ambiguity

```ax
fn foo<T>(x: T)
fn foo<T: Numeric>(x: T)
```

Call:

```ax
foo(10)
```

Nếu cả hai đều applicable và trait solver chứng minh `i32: Numeric`, candidate thứ hai cụ thể hơn.

→ chọn candidate constrained.

Nhưng nếu:

```ax
fn foo<T: A>(x: T)
fn foo<T: B>(x: T)
```

và `T` thỏa cả A và B nhưng không có ordering:

```text
AMBIGUOUS OVERLOAD
```

Compiler không đoán.

---

# 27. Trait obligations trong inference

Generic function:

```ax
fn add<T: Add>(a: T, b: T) -> T
```

Call:

```ax
add(x, y)
```

inference tạo:

```text
?T = type(x)
?T = type(y)

Implements(?T, Add)
```

Sau khi unification:

```text
Implements(i32, Add)
```

Trait solver xử lý obligation.

---

# 28. Inference không tự giải trait

Đây là boundary quan trọng:

```text
Inference:
    ?T = i32

Trait Solver:
    i32 implements Add
```

Không để TypeInference tự chứa logic trait solver đầy đủ.

Hai subsystem gọi nhau thông qua CompilerDB queries.

---

# 29. Associated type constraints

Ví dụ:

```ax
fn convert<T: Iterator>(x: T) -> T.Item
```

Compiler có projection:

```text
<T as Iterator>::Item
```

Nếu context:

```ax
let x: i32 = convert(iter)
```

constraint:

```text
<T as Iterator>::Item = i32
```

Trait solver + associated-type normalization giải projection.

---

# 30. Closure parameter inference

Ví dụ:

```ax
let xs = [1, 2, 3]

let ys = xs.map(|x| x * 2)
```

Compiler chưa biết `x`.

Từ `map` candidate:

```text
map<F>(..., F)
```

và trait/callable constraints:

```text
F: Fn(i32) -> ?R
```

closure parameter:

```text
x : i32
```

body:

```text
x * 2 → i32
```

→

```text
closure : fn(i32) -> i32
```

---

# 31. Closure capture inference

Capture mode không thuộc type inference đơn thuần.

Inference chỉ xác định:

```text
captured variable exists
```

Sau đó closure/capture analysis quyết định:

```text
ByValue
ByView
ByMutView
```

dựa trên usage và ownership rules.

Do đó:

```text
TypeInference
      ↓
ClosureAnalysis
      ↓
OwnershipVerification
```

---

# 32. Closure return inference

```ax
let f = |x: i32| {
    x * x
}
```

Body expression synthesize:

```text
i32 * i32 → i32
```

→ closure result:

```text
i32
```

Nếu nhiều control paths:

```ax
let f = |x| {
    if x > 0 {
        x
    } else {
        0
    }
}
```

branches:

```text
?T
?T
```

→ unify.

---

# 33. Return type inference

Axiom cho phép:

```ax
fn square(x: i32) {
    x * x
}
```

Compiler suy ra:

```text
-> i32
```

nếu syntax này được giữ trong canonical grammar.

Nhưng nếu function có nhiều return:

```ax
fn foo(x: i32) {
    if x > 0 {
        return x
    }

    return 0
}
```

constraints:

```text
return_type = i32
```

Nếu:

```ax
return x
return "hello"
```

→ mismatch.

---

# 34. `return` và Never

```ax
fn foo() -> i32 {
    if condition {
        return 10
    }

    panic("error")
}
```

`panic` có type:

```text
never
```

Do:

```text
never → T
```

nên branch vẫn hợp lệ.

---

# 35. Block expression typing

Block:

```ax
{
    let x = 10
    x + 2
}
```

type của block = type expression cuối:

```text
i32
```

Block:

```ax
{
    let x = 10
}
```

type:

```text
unit
```

Nếu:

```ax
{
    foo()
    bar()
}
```

thì `bar()` xác định block result.

---

# 36. `if` expression

```ax
let x = if cond {
    10
} else {
    20
}
```

constraints:

```text
cond : bool
branch1 : ?T
branch2 : ?T
```

→

```text
?T = i32
```

Nếu:

```ax
if cond { 10 } else { "x" }
```

→ error.

Không tự tạo:

```text
Any
```

hay union type runtime.

---

# 37. `match`

```ax
let x = match value {
    A => 10,
    B => 20,
}
```

mỗi arm tạo:

```text
ArmType_i
```

Tất cả phải unify thành result type.

Ngoài type inference, exhaustiveness checker xử lý:

```text
patterns
coverage
unreachable arms
```

Hai hệ thống độc lập.

---

# 38. Match với Never

```ax
match x {
    Some(v) => v,
    None => panic("missing")
}
```

Nếu `v: i32`:

```text
i32
never
```

→ result:

```text
i32
```

nhờ `never → T`.

---

# 39. `?` operator

`?` không phải magic exception.

Nó được typing thông qua `Result` / `Option` protocol đã được định nghĩa.

Ví dụ:

```ax
fn load() -> Result<Data, Error> {
    let x = read()?
    process(x)
}
```

`read()`:

```text
Result<T, E>
```

`?`:

```text
success → T
failure → propagated Result
```

Compiler phải tạo constraint rằng enclosing function return type tương thích với propagated failure.

---

# 40. `?` không dùng overload tùy tiện

Không được để:

```text
?
```

gọi arbitrary user-defined magic conversion mà không có semantic protocol.

Core semantics phải biết:

```text
Result
Option
```

và extension mechanism nếu sau này được mở rộng phải vẫn đi qua typed protocol.

---

# 41. Expected type propagation qua `?`

Ví dụ:

```ax
fn foo() -> Result<i32, MyError>
```

và:

```ax
let x: i32 = read()?
```

Compiler biết:

```text
success type = i32
```

nên inference ngược vào `read()`.

---

# 42. Method resolution

Với:

```ax
x.foo(a)
```

resolver/inference phải phân biệt:

```text
inherent method
trait method
extension function
```

Pipeline:

```text
Resolve receiver type
        ↓
Collect candidates
        ↓
Infer receiver / generic args
        ↓
Check arguments
        ↓
Trait obligations
        ↓
Rank candidates
        ↓
Select
```

---

# 43. Receiver là implicit first parameter

Axiom:

```ax
fn length(self: Vec2) -> f32
```

method call:

```ax
v.length()
```

semantic call:

```ax
length(v)
```

Inference xử lý `self` như argument đầu tiên.

Điều này giữ cho:

> **Struct + function** vẫn là primitive của Axiom, không cần class method machinery.

---

# 44. Method mutability

Ví dụ:

```ax
fn clear(self: mut Vec)
```

hoặc canonical mutable receiver syntax theo grammar Axiom.

Call:

```ax
v.clear()
```

Inference xác định function candidate.

Nhưng capability verifier mới quyết định:

```text
v có WRITE capability phù hợp không?
```

Type inference không được tự biến READ thành WRITE.

---

# 45. Trait method ambiguity

Ví dụ:

```ax
trait A {
    fn foo(self)
}

trait B {
    fn foo(self)
}
```

và type implement cả hai.

```ax
x.foo()
```

→ ambiguous nếu không có resolution rule xác định.

Programmer có thể disambiguate bằng fully qualified syntax:

```ax
A::foo(x)
B::foo(x)
```

Cách này phù hợp với triết lý Axiom:

> Compiler tự động khi không mơ hồ; explicit khi có nhiều nghĩa hợp lệ.

---

# 46. Overload + generic + trait

Ví dụ:

```ax
fn process<T>(x: T)
fn process<T: Numeric>(x: T)
fn process(x: Str)
```

Call:

```ax
process(10)
```

Resolver:

```text
candidate #1 generic       applicable
candidate #2 Numeric       applicable
candidate #3 Str           rejected
```

Trait solver chứng minh:

```text
i32: Numeric
```

Ranking chọn candidate cụ thể hơn.

---

# 47. Deterministic resolution

Candidate ordering nội bộ có thể khác nhau do parallel compiler.

Do đó resolver phải canonicalize:

```text
CandidateKey =
    declaration semantic identity
    + specialization relation
    + conversion class
    + instantiated signature
```

Kết quả không phụ thuộc:

```text
hash table order
thread order
filesystem order
module scan order
```

---

# 48. Ambiguity phải là first-class result

Không được:

```text
Option<FunctionId>
```

đơn giản.

Phải có:

```text
OverloadResult =
    Selected(FunctionId, SelectionEvidence)
    NoMatch(RejectionSet)
    Ambiguous(CandidateSet, ComparisonEvidence)
    Error(DiagnosticId)
```

Điều này cực kỳ quan trọng cho AI tooling.

---

# 49. Selection evidence

Compiler có thể lưu:

```text
SelectionEvidence {
    selected: FunctionId
    candidates: [...]
    eliminated: [...]
    constraints: [...]
    coercions: [...]
    trait_proofs: [...]
    specificity_relation: [...]
}
```

AI/compiler UI có thể trả lời:

> Vì sao compiler chọn function này?

thay vì chỉ:

```text
ambiguous call
```

---

# 50. Diagnostic example

Thay vì:

```text
error: ambiguous call
```

Axiom có thể báo:

```text
Cannot resolve call to `foo`.

Candidate 1:
    foo(i32)
    applicable: exact match

Candidate 2:
    foo<T: Numeric>(T)
    applicable: exact match
    T = i32
    constraint: i32 implements Numeric

Candidate 3:
    foo(Str)
    rejected:
    argument 1 has type i32, expected Str

Candidates 1 and 2 have equivalent conversion cost.
Neither candidate is more specific under the current overload rules.

Help:
    specify the desired function explicitly.
```

Đây là **structured diagnostic**, không phải compiler text hard-coded.

---

# 51. Type inference diagnostics

Ví dụ:

```ax
let x = []
```

Nếu empty array không có expected type:

```text
Cannot infer element type of empty array.

The expression:
    []

has no element value from which its type can be inferred.

Provide an expected type, for example:
    let x: [0]i32 = []
```

Canonical syntax thực tế sẽ tuân theo grammar frozen.

---

# 52. Inference variable finalization

Trước khi Typed HIR hoàn tất:

```text
No unresolved inference variable may remain
```

ngoại lệ:

- ErrorType trong partial semantic mode;
- IDE incomplete program mode.

Production compilation:

```text
?T remaining
```

→ diagnostic.

---

# 53. Defaulting

Defaulting chỉ xảy ra ở cuối inference.

Ví dụ:

```ax
let x = 42
```

trình tự:

```text
literal constraint
    ↓
context search
    ↓
generic constraints
    ↓
trait constraints
    ↓
coercion possibilities
    ↓
default numeric type
```

Không default quá sớm.

---

# 54. Không generalize local variables tùy tiện

Axiom phải phân biệt:

```text
local inference
generic declaration
```

Ví dụ:

```ax
let x = identity
```

không mặc định biến local thành:

```text
forall T. T -> T
```

trừ khi language rule về polymorphic values xác định rõ.

Đề xuất Core v0.1:

> **Generic polymorphism được tạo tại declaration boundary, không tự động generalize mọi local inference result.**

Điều này giúp type system đơn giản và predictable.

---

# 55. Generic function instantiation

Khi gọi:

```ax
identity(42)
```

compiler tạo:

```text
GenericInstanceId
```

với substitution:

```text
T = i32
```

TypeDB:

```text
identity<i32>
```

được canonicalize/intern.

---

# 56. Generic instance cache

CompilerDB query:

```text
instantiate(FunctionId, GenericArguments)
```

phải dùng query engine của BOOTSTRAP-274.

Không tạo cache riêng trong inference subsystem.

---

# 57. Type inference và ownership

Ví dụ:

```ax
let y = consume(x)
```

Inference xác định:

```text
consume : fn(T) -> U
T = type(x)
```

Nhưng:

```text
x bị Move
```

là ownership semantics.

Do đó:

```text
Inference → Typed expression
Ownership → access mode
```

Không để inference tự đánh dấu `x` là moved.

---

# 58. Type inference và capability

```ax
fn read(x: view<T>)
fn write(x: mut_view<T>)
```

Inference có thể chọn:

```text
view<T>
```

hoặc:

```text
mut_view<T>
```

nhưng capability verifier quyết định conversion/creation có hợp lệ không.

Không được:

```text
view<T> → mut_view<T>
```

chỉ vì overload resolver thấy function cần mutable access.

---

# 59. Type inference và `dyn Trait`

Concrete type không tự động trở thành:

```text
dyn Trait
```

trong mọi context.

Nếu Axiom cho phép coercion cụ thể:

```text
T → dyn Trait
```

thì phải là một coercion rule explicit được frozen.

Mặc định:

```text
generic/static dispatch
```

được ưu tiên hơn dynamic dispatch.

---

# 60. Inference + dynamic dispatch

Ví dụ:

```ax
fn render(x: dyn Renderable)
```

call:

```ax
render(circle)
```

Nếu language rule cho phép concrete→dyn coercion:

```text
circle
   ↓ explicit dyn coercion
dyn Renderable
```

Typed HIR phải ghi rõ boundary.

Không để backend tự suy ra dynamic dispatch.

---

# 61. Operator inference

Operators được xử lý như typed operations.

Ví dụ:

```ax
a + b
```

resolution:

```text
Add::add(a, b)
```

theo operator protocol.

Nhưng built-in arithmetic có thể được compiler lower trực tiếp.

Inference cần xác định:

```text
operand types
result type
trait/builtin candidate
```

Backend không tham gia overload resolution.

---

# 62. Short-circuit operators

```ax
a && b
a || b
```

không phải ordinary function call vì có evaluation-order semantics.

Inference:

```text
a : bool
b : bool
result : bool
```

nhưng AST/HIR giữ chúng là special expressions.

---

# 63. Indexing

```ax
x[i]
```

có thể resolve theo:

```text
Index
```

protocol hoặc built-in array/view indexing.

Constraint:

```text
index type valid
result type = element/reference/view semantic
```

Capability semantics được xử lý sau.

---

# 64. Field access

```ax
x.field
```

field type được resolver/type engine lấy trực tiếp từ nominal type.

Không phải overload.

Nếu:

```text
x : ?T
```

compiler trước tiên phải resolve `?T` đủ để biết field set.

Nếu không:

```text
cannot infer receiver type
```

---

# 65. Error recovery

Trong IDE:

```ax
let x: = foo()
```

không được làm inference engine crash.

Có thể dùng:

```text
ErrorType
ErrorInferenceVar
```

nhưng:

```text
ErrorType
```

không được lọt vào Verified MIR.

---

# 66. Constraint graph

Implementation nên biểu diễn inference dưới dạng graph:

```text
?T0 ─── equality ─── ?T1
 │
 ├── implements Numeric
 │
 └── coercible-to view<?T2>
```

Mỗi constraint có provenance:

```text
ConstraintId
SourceSpan
OriginExpression
```

Ví dụ:

```text
Constraint #42
origin: `x + 1`
requires: x type supports Add
```

---

# 67. Constraint provenance

Mỗi constraint:

```text
Constraint {
    kind
    operands
    origin_span
    origin_node
    priority
}
```

Điều này cho phép diagnostic:

```text
expected i32 here
because this expression must match
the return type declared on line ...
```

và AI có thể truy vấn trực tiếp.

---

# 68. Constraint normalization

Trước solver:

```text
TypeEq(?A, Alias<T>)
```

→ normalize alias.

```text
Implements(?T, Trait)
```

→ trait obligation.

```text
ProjectionEq(...)
```

→ associated-type obligation.

Không để từng subsystem tự normalize theo cách khác nhau.

---

# 69. Solver phases

Đề xuất:

```text
Phase 1:
    collect local constraints

Phase 2:
    structural unification

Phase 3:
    propagate expected types

Phase 4:
    resolve generic applications

Phase 5:
    solve trait obligations

Phase 6:
    normalize associated types

Phase 7:
    overload resolution

Phase 8:
    insert legal coercions

Phase 9:
    numeric/default finalization

Phase 10:
    final WF check
```

Một số phase có thể iterate đến fixed point.

---

# 70. Không dùng brute-force inference

Compiler không được thử mọi combination:

```text
candidate × generic × coercion × trait
```

vô hạn.

Phải có:

- candidate pruning;
- canonical types;
- memoized trait queries;
- inference snapshots;
- constraint normalization;
- deterministic search;
- recursion/depth limits.

---

# 71. Trait solver interaction

Inference gửi:

```text
Obligation {
    TraitId
    SelfType
    Arguments
    SourceSpan
}
```

đến TraitDB.

Kết quả:

```text
Proven
NotProven
Ambiguous
Error
```

`Ambiguous` không được coi là `Proven`.

---

# 72. Delayed obligations

Nếu:

```ax
fn foo<T: Add>(x: T)
```

và tại thời điểm hiện tại:

```text
?T: Add
```

chưa thể quyết định.

Không reject ngay nếu `?T` còn inference.

Đưa vào:

```text
PendingObligation
```

Sau unification mới solve.

---

# 73. Nhưng không delay vô hạn

Nếu cuối inference:

```text
?T: Add
```

vẫn unresolved:

```text
cannot infer type satisfying Add
```

Compiler phải báo lỗi.

---

# 74. Ambiguous trait obligation

Ví dụ nhiều impl có thể phù hợp nhưng solver không xác định:

```text
TraitResolution = Ambiguous
```

Overload resolver không được tự chọn.

---

# 75. Recursive inference

Compiler phải hỗ trợ recursive generic constraints nhưng có cycle detection.

Ví dụ:

```text
?A = Wrapper<?B>
?B = Wrapper<?A>
```

→ infinite type → reject.

Trait cycle:

```text
A<T> requires B<T>
B<T> requires A<T>
```

được xử lý bởi Trait Solver cycle semantics, không phải Unifier.

---

# 76. Inference depth limit

Compiler phải có giới hạn cho:

```text
generic nesting
trait recursion
projection normalization
overload recursion
```

Nếu vượt:

```text
compiler semantic limit exceeded
```

không được stack overflow/ICE.

---

# 77. Compiler invariant

Một chương trình hợp lệ sau inference phải có:

```text
Every expression has a resolved semantic type.
Every generic parameter has a concrete inference result.
Every overload call has exactly one selected declaration.
Every trait obligation is proven.
Every coercion is explicit in Typed HIR.
No unresolved inference variable reaches Verified MIR.
```

---

# 78. Typed HIR output

Ví dụ:

```ax
let x = identity(10)
```

Typed HIR phải gần như:

```text
Let
  name: x
  type: i32

  Call
    function: identity<i32>
    args:
      IntegerLiteral
        type: i32
        value: 10

    result: i32
```

Không còn:

```text
?T
```

---

# 79. Coercion trong Typed HIR

```ax
sum(array)
```

sau typing:

```text
Call sum
    arg:
        Coerce
            from: [4]i32
            to: view<i32>
            expression: array
```

Do đó các compiler stage sau không phải đoán lại semantics.

---

# 80. Inference query API

TypeDB/CompilerDB nên expose:

```text
infer_expr(ExpressionId, ExpectedType?)
infer_function(FunctionId)
infer_call(CallId)
resolve_overload(CallSiteId)
resolve_method(MethodCallId)
solve_constraints(InferenceSessionId)
normalize_type(TypeId)
```

Tất cả là CompilerDB queries.

---

# 81. AI-native inference API

Compiler có thể expose:

```text
why_type(ExpressionId)
why_overload(CallSiteId)
show_constraints(ExpressionId)
show_trait_obligations(ExpressionId)
show_coercions(ExpressionId)
explain_ambiguity(CallSiteId)
```

Ví dụ:

```text
why_type(x)
```

trả về structured graph:

```text
x
↓
initialized from identity(10)
↓
10 defaults to i32
↓
identity<T>(T) => T
↓
T = i32
↓
x : i32
```

Đây là một trong các điểm Axiom có thể vượt các compiler truyền thống về AI integration.

---

# 82. Error codes

Đề xuất nhóm:

```text
AINFER-001  unresolved inference variable
AINFER-002  conflicting type constraints
AINFER-003  occurs-check failure
AINFER-004  numeric literal mismatch
AINFER-005  cannot infer generic argument
AINFER-006  no overload candidate
AINFER-007  ambiguous overload
AINFER-008  invalid coercion
AINFER-009  unresolved trait obligation
AINFER-010  ambiguous trait obligation
AINFER-011  associated type mismatch
AINFER-012  cannot infer closure parameter
AINFER-013  inconsistent branch types
AINFER-014  invalid return type
AINFER-015  invalid ? propagation
AINFER-016  inference depth exceeded
```

---

# 83. Performance architecture

Inference là một trong những nơi dễ làm compiler chậm.

Phải sử dụng:

```text
TypeId interning
Canonical type keys
Union-find / substitution structures
Constraint deduplication
Query memoization
Trait result caching
Candidate pruning
Incremental invalidation
Parallel independent inference sessions
```

Không dùng string-based type comparison.

---

# 84. Parallelism

Các function/module độc lập có thể inference song song.

Nhưng kết quả:

```text
must equal single-threaded result
```

Không được để candidate selection phụ thuộc completion order.

---

# 85. Incremental compilation

Nếu sửa:

```ax
fn foo(x: i32) -> i32
```

thành:

```ax
fn foo(x: i64) -> i64
```

chỉ các query phụ thuộc semantic fingerprint của `foo` phải invalidate.

Không rebuild toàn bộ TypeDB.

---

# 86. Inference fingerprint

Inference result có thể fingerprint:

```text
InferenceFingerprint {
    expression semantic identity
    expected type
    resolved names
    generic substitutions
    trait obligations
    coercions
    compiler semantic version
}
```

Không đưa physical TypeId vào persistent fingerprint nếu TypeId chỉ compiler-local.

---

# 87. Interaction với BOOTSTRAP-277

Quan hệ chính thức:

```text
TypeDB
  │
  ├── TypeId
  ├── TypeInterner
  ├── TypeRelations
  └── TypeProperties
       ↑
       │
TypeInference
       │
       ├── InferenceVar
       ├── Constraints
       ├── Substitution
       └── ExpectedType
       │
       ↓
TraitDB
       │
       ↓
Typed HIR
```

278 **không được tạo một type identity system thứ hai**.

---

# 88. Interaction với BOOTSTRAP-130 Trait Solver

Trait solver là authority cho:

```text
Implements(T, Trait)
AssociatedType(T, Trait)
```

Inference chỉ tạo obligations.

```text
Inference:
    "T must implement Add"

Trait Solver:
    "yes/no/ambiguous"
```

---

# 89. Interaction với BOOTSTRAP-135 Ownership

Sau inference:

```text
Call foo(x)
```

đã biết:

```text
foo : fn(T) -> U
T = MyType
```

nhưng ownership verifier mới xác định:

```text
x READ?
x MOVE?
x WRITE?
```

Đây là boundary bắt buộc.

---

# 90. Interaction với ABI

Inference tuyệt đối không biết:

```text
register
stack slot
calling convention physical register
struct ABI classification
```

Nó chỉ xác định:

```text
semantic function type
```

ABI xảy ra sau.

---

# 91. Interaction với optimization

Inference không được tối ưu:

```text
i32 → machine register
```

hoặc:

```text
closure → function pointer
```

Đó là backend/optimization.

Inference chỉ xác định semantic type.

---

# 92. Core principle

Một distinction rất quan trọng được frozen:

```text
Inference answers:
"What type/function does this source expression mean?"

Optimization answers:
"How can that meaning be implemented efficiently?"
```

Không trộn hai câu hỏi.

---

# 93. Surface syntax mục tiêu

Axiom có thể cho phép code rất gọn:

```ax
fn square(x: i32) {
    x * x
}

let a = square(10)

let b = if a > 10 {
    a
} else {
    0
}

let c = values.map(|x| x * 2)
```

Compiler vẫn tạo đầy đủ:

```text
types
generic substitutions
trait obligations
coercions
ownership facts
capability facts
ABI information
```

Programmer không phải viết tất cả.

Đây chính xác là triết lý:

> **Compiler Complexity Is Not Language Complexity.**

---

# 94. Frozen invariants — BOOTSTRAP-278

```text
AINFER-20
Type inference is deterministic.

AINFER-21
Inference variables are compiler-internal.

AINFER-22
Inference variables are session-scoped.

AINFER-23
Inference variables cannot enter Verified MIR.

AINFER-24
Inference uses bidirectional typing.

AINFER-25
Expected types propagate into expressions where semantically valid.

AINFER-26
Explicit programmer types have priority over weaker inferred constraints.

AINFER-27
Unification uses structural equality.

AINFER-28
Unification performs occurs-check.

AINFER-29
Unification does not perform arbitrary numeric conversion.

AINFER-30
Inference does not invent subtype relationships.

AINFER-31
Coercion rules are finite and explicitly specified.

AINFER-32
Coercion is distinct from cast.

AINFER-33
Coercion is distinct from bitcast.

AINFER-34
Numeric literals remain inference candidates until contextual constraints are exhausted.

AINFER-35
Integer literal defaulting is deterministic.

AINFER-36
Floating literal defaulting is deterministic.

AINFER-37
Out-of-range literals are compile-time errors where representability is statically known.

AINFER-38
Generic arguments may be inferred from argument types.

AINFER-39
Generic arguments may be inferred from expected result types.

AINFER-40
Explicit generic arguments constrain inference.

AINFER-41
Inference does not mutate TypeDB identity.

AINFER-42
Speculative inference supports rollback or isolated snapshots.

AINFER-43
Overload candidates are collected from semantically defined scopes only.

AINFER-44
Overload resolution is deterministic.

AINFER-45
Overload resolution is independent of declaration traversal order.

AINFER-46
Overload resolution is independent of worker completion order.

AINFER-47
Overload ranking uses specified semantic ordering rather than arbitrary scores.

AINFER-48
Equivalent candidates produce ambiguity rather than arbitrary selection.

AINFER-49
Ambiguity is a first-class compiler result.

AINFER-50
Every selected overload records selection evidence.

AINFER-51
Rejected overload candidates retain structured rejection reasons.

AINFER-52
Trait obligations are delegated to the Trait Solver.

AINFER-53
Inference may create pending trait obligations.

AINFER-54
Pending obligations must resolve before production typing completes.

AINFER-55
Ambiguous trait obligations are not treated as proven.

AINFER-56
Associated-type constraints are represented explicitly.

AINFER-57
Associated-type normalization uses the authoritative Type/Trait databases.

AINFER-58
Closure parameter inference is constraint-driven.

AINFER-59
Closure return inference is constraint-driven.

AINFER-60
Closure capture mode is resolved outside basic type inference.

AINFER-61
Return type inference unifies all reachable value returns.

AINFER-62
Block expression type is determined by its semantic result expression.

AINFER-63
Unit is the type of value-less blocks.

AINFER-64
Never can coerce to any expected type.

AINFER-65
Branch result types must be compatible under specified coercion rules.

AINFER-66
Match arm result types participate in common result typing.

AINFER-67
Match exhaustiveness is separate from type inference.

AINFER-68
`?` typing follows the specified Result/Option semantics.

AINFER-69
`?` cannot silently invent arbitrary error conversions.

AINFER-70
Method resolution treats receiver resolution as part of overload candidate formation.

AINFER-71
Inherent methods have defined precedence over extension candidates.

AINFER-72
Trait method ambiguity is diagnosed explicitly.

AINFER-73
Fully-qualified calls provide explicit disambiguation.

AINFER-74
Operators participate in typed operation resolution.

AINFER-75
Short-circuit operators retain special evaluation semantics.

AINFER-76
Field access is not arbitrary overload resolution.

AINFER-77
Type inference does not determine ownership state.

AINFER-78
Type inference does not determine capability validity.

AINFER-79
Type inference does not perform ABI lowering.

AINFER-80
Type inference does not perform machine representation selection.

AINFER-81
Unresolved inference variables produce diagnostics in production compilation.

AINFER-82
IDE partial-program mode may use ErrorType for recovery.

AINFER-83
ErrorType cannot enter Verified MIR.

AINFER-84
Inference constraints carry source provenance.

AINFER-85
Constraint diagnostics are structured data.

AINFER-86
Inference queries use CompilerDB query infrastructure.

AINFER-87
Inference caches are dependency-driven.

AINFER-88
Inference results are semantically deterministic across parallel execution.

AINFER-89
Inference supports incremental invalidation.

AINFER-90
Inference does not create independent semantic type identities.

AINFER-91
Generic instantiations use canonical TypeDB representations.

AINFER-92
Trait solver results are queried through the shared semantic database.

AINFER-93
Inference cycle detection is distinct from language recursion semantics.

AINFER-94
Inference depth limits cannot cause compiler memory corruption or undefined behavior.

AINFER-95
Compiler semantic failures are represented as structured diagnostics.

AINFER-96
Overload resolution must terminate for finite program input under configured semantic limits.

AINFER-97
Defaulting occurs only after stronger constraints have been exhausted.

AINFER-98
Coercions inserted during inference are explicit in Typed HIR.

AINFER-99
Typed HIR contains no unresolved production inference variables.

AINFER-100
Inference preserves the semantic meaning of source code independently of optimization level.
```

---

# 95. Implementation structure

Đề xuất source tree:

```text
compiler/
└── semantic/
    └── inference/
        ├── mod.ax
        ├── inference_var.ax
        ├── inference_session.ax
        ├── constraint.ax
        ├── constraint_origin.ax
        ├── substitution.ax
        ├── unify.ax
        ├── occurs_check.ax
        ├── expected_type.ax
        ├── synthesize.ax
        ├── check.ax
        ├── literals.ax
        ├── generic_infer.ax
        ├── callable.ax
        ├── closure_infer.ax
        ├── return_infer.ax
        ├── branch_infer.ax
        ├── match_infer.ax
        ├── question_mark.ax
        ├── coercion.ax
        ├── overload.ax
        ├── candidate.ax
        ├── ranking.ax
        ├── method_resolution.ax
        ├── operator_resolution.ax
        ├── trait_obligation.ax
        ├── projection.ax
        ├── defaulting.ax
        ├── normalization.ax
        ├── diagnostics.ax
        ├── explanation.ax
        ├── fingerprint.ax
        └── tests/
```

---

# 96. Implementation order

Compiler agent nên thực hiện đúng thứ tự:

```text
1. InferenceVar
2. InferenceSession
3. Substitution
4. Constraint representation
5. Constraint provenance
6. Unification
7. Occurs check
8. ExpectedType
9. Synthesized typing
10. Checked typing
11. Numeric literals
12. Generic inference
13. Function/call constraints
14. Return inference
15. Block/if typing
16. Match typing
17. Closure typing
18. Trait obligations
19. Associated projections
20. Coercion insertion
21. Candidate collection
22. Overload ranking
23. Method resolution
24. Operator resolution
25. `?` typing
26. Defaulting
27. Typed HIR emission
28. Diagnostic explanation
29. CompilerDB integration
30. Incremental tests
31. Parallel determinism tests
32. Fuzz/property tests
```

---

# 97. Bộ test bắt buộc

### Basic

```ax
let x = 10
let x: i64 = 10
let x = 1.5
```

### Generic

```ax
identity(10)
identity("hello")
pair(1, 2)
```

### Expected type

```ax
let x: Vec<i32> = make()
```

### Branch

```ax
if cond { 1 } else { 2 }
```

### Never

```ax
if cond { return 1 } else { panic() }
```

### Closure

```ax
values.map(|x| x * 2)
```

### Overload

```ax
foo(10)
foo("hello")
```

### Ambiguity

```ax
foo(x)
```

với hai candidate ngang nhau.

### Trait

```ax
fn f<T: Numeric>(x: T)
f(10)
```

### Associated type

```ax
Iterator<Item = i32>
```

### Coercion

```ax
array → view
```

### Failure

```ax
let x = []
```

nếu không có contextual type.

---

# 98. Adversarial tests

Bắt buộc có:

```text
recursive generic types
deep nested generics
trait cycles
projection cycles
thousands of overload candidates
large candidate ambiguity
numeric literal boundary values
conflicting expected types
closure inference cycles
nested match
nested ? propagation
generic + overload + trait combination
parallel inference
incremental edit
cancelled query
invalid cache
```

Đặc biệt:

```text
compile with 1 worker
compile with N workers
```

phải cho semantic result giống nhau.

---

# 99. Kết quả cuối của BOOTSTRAP-278

Sau task này, Axiom đã có chuỗi:

```text
Lexer
  ↓
Parser
  ↓
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
Typed HIR
  ↓
Ownership / Capability
```

Trong đó **TypeDB + Inference + TraitDB** tạo thành semantic type engine hoàn chỉnh:

```text
             ┌─────────────────┐
             │     TypeDB      │
             │ canonical types │
             └────────┬────────┘
                      │
             ┌────────▼────────┐
             │   InferenceDB   │
             │ constraints     │
             │ unification     │
             │ expected types  │
             └───────┬─────────┘
                     │
          ┌──────────┴──────────┐
          │                     │
 ┌────────▼────────┐   ┌────────▼────────┐
 │    TraitDB      │   │ OverloadResolver│
 │ obligations     │   │ candidates      │
 │ projections     │   │ ranking         │
 └────────┬────────┘   └────────┬────────┘
          │                     │
          └──────────┬──────────┘
                     ↓
               Typed HIR
```

### Trạng thái: **FROZEN / COMPLETED**

Và điểm quan trọng nhất của 278 là Axiom giờ có thể đạt được điều mà ta đã đặt ra từ đầu: **syntax có thể rất gọn, nhưng semantic information mà compiler thu được vẫn cực kỳ đầy đủ**. Programmer không phải viết type/trait/conversion/capture information một cách máy móc; compiler suy ra chúng bằng một hệ thống constraint có thể kiểm chứng và giải thích được.