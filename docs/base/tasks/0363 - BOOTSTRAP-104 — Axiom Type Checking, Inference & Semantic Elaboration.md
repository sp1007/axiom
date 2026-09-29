# BOOTSTRAP-104 — Axiom Type Checking, Inference & Semantic Elaboration
**FROZEN / COMPLETED**

Đây là một trong những phần quan trọng nhất của compiler Axiom, vì mục tiêu của Axiom là:

> **Programmer viết ít annotation, nhưng compiler phải hiểu chính xác type, ownership, capability, generic, trait và cách gọi hàm.**

Nguyên tắc xuyên suốt:

> **Không bắt programmer khai báo những gì compiler có thể chứng minh chắc chắn. Nhưng compiler tuyệt đối không được “đoán” khi có nhiều nghĩa hợp lệ.**

---

# 1. Pipeline chính

Axiom Type System không làm tất cả trong một bước.

```text
AST
 ↓
Declaration Collection
 ↓
Name Resolution
 ↓
Typed HIR skeleton
 ↓
Type Environment
 ↓
Constraint Generation
 ↓
Type Inference
 ↓
Numeric Literal Resolution
 ↓
Generic Inference
 ↓
Trait Constraint Solving
 ↓
Method / Operator Resolution
 ↓
Coercion / Conversion Resolution
 ↓
Ownership Elaboration
 ↓
Capability Elaboration
 ↓
Closure / Async Elaboration
 ↓
Comptime Elaboration
 ↓
Fully Typed HIR
 ↓
MIR Lowering
```

Điểm quan trọng:

**Type checking xảy ra trước MIR**, nhưng ownership/capability không được biến thành các annotation mà programmer phải viết.

---

# 2. Mức độ type inference

Axiom sử dụng **local bidirectional inference**.

Có hai hướng:

### Synthesizing

Compiler tự suy ra type:

```axiom
let x = 10;
let y = x + 20;
```

Compiler suy ra:

```text
x : integer literal → inferred integer
y : same numeric domain
```

### Checking

Context cung cấp expected type:

```axiom
let x: i32 = 10;
```

Compiler kiểm tra literal `10` có thể biểu diễn bằng `i32`.

---

# 3. Khi nào KHÔNG cần annotation?

Axiom cố gắng infer:

```axiom
let x = Vec3(1, 2, 3);
```

```axiom
let result = calculate(data);
```

```axiom
let value = parse(input)?;
```

```axiom
let f = |x| x * 2;
```

```axiom
let items = [1, 2, 3, 4];
```

Compiler có thể suy ra type từ:

- initializer
- argument
- return context
- operator
- trait constraints
- generic constraints
- pattern
- expected type
- surrounding expression

---

# 4. Khi nào bắt buộc annotation?

Chỉ khi compiler **không thể chứng minh duy nhất một nghĩa hợp lệ**.

Ví dụ:

```axiom
let x = [];
```

Không đủ thông tin để biết:

```text
Array<i32>
Array<f64>
Array<String>
...
```

→ compile error.

Programmer có thể viết:

```axiom
let x: Array<i32> = [];
```

Hoặc:

```axiom
let x = Array<i32>();
```

---

# 5. Không được dùng “best guess”

Đây là invariant rất quan trọng.

Ví dụ:

```axiom
foo(10)
```

Nếu có:

```axiom
foo(i32)
foo(i64)
```

compiler **không tự chọn** một overload dựa trên heuristic.

→ ambiguous.

Điều này đặc biệt quan trọng với AI-generated code.

Compiler phải deterministic:

```text
same source
+ same compiler semantics
+ same target/config
→ same meaning
```

---

# 6. Type inference không được thay đổi ownership semantics

Ví dụ:

```axiom
let a = make_buffer();
let b = a;
```

Nếu `Buffer` là non-Copy owning type:

```text
a → Owned
b ← Move(a)
a → Moved
```

Không được vì inference mà biến thành:

```text
clone(a)
```

hoặc:

```text
Arc(a)
```

---

# 7. Copy inference

Compiler tự biết một type có `Copy` hay không.

Ví dụ:

```axiom
let a: i32 = 10;
let b = a;
let c = a;
```

`i32 : Copy`.

Do đó:

```text
a remains valid
b independent value
c independent value
```

Nhưng:

```axiom
let a = String("hello");
let b = a;
print(a);
```

Nếu `String : !Copy`:

```text
a → Owned
b ← Move(a)
a → Moved
```

`print(a)` → error.

Không cần:

```axiom
move a
```

vì Move là semantic mặc định của owning value.

---

# 8. Copy không phải bitwise copy

Compiler không được suy luận:

```text
memcpy-able == Copy
```

Hai khái niệm khác nhau.

Một struct có thể có representation copyable nhưng chứa:

- resource
- ownership
- Drop
- external handle

thì vẫn có thể là `!Copy`.

---

# 9. Clone không được tự động

Nếu type có:

```axiom
impl Clone for Buffer
```

thì:

```axiom
let b = a.clone();
```

được.

Nhưng:

```axiom
let b = a;
```

không tự biến thành Clone.

Điều này tránh việc compiler âm thầm tạo allocation/copy lớn.

---

# 10. `view` inference

Đây là phần rất quan trọng để Axiom tránh pointer/reference syntax.

Ví dụ:

```axiom
fn sum(values: view<i32>) -> i32
```

Có thể gọi:

```axiom
let a = [1, 2, 3, 4];

sum(a);
```

Compiler tự tạo ephemeral capability:

```text
a
 ↓
view<i32>
 ↓
call
 ↓
capability expires
```

Programmer không phải viết:

```axiom
& a
```

hoặc lifetime.

---

# 11. `mut_view`

Ví dụ:

```axiom
fn sort(values: mut_view<i32>)
```

Gọi:

```axiom
sort(data);
```

Compiler kiểm tra:

```text
data
→ exclusive mutable capability
→ sort
→ capability ends
```

Nếu đồng thời có:

```axiom
let r = view(data);
sort(data);
```

và `r` còn live:

```text
READ capability
+
WRITE capability
+
same region
```

→ reject.

---

# 12. Compiler tự suy ra region

Không bắt programmer viết:

```text
view<'a, 'b, T>
```

Thay vào đó compiler nội bộ tạo:

```text
CapabilityId
RegionId
ProvenanceId
AccessMode
Lifetime
```

Ví dụ:

```axiom
fn process(a: mut_view<Vec3>, b: mut_view<Vec3>)
```

Compiler có thể phát hiện:

```text
region(a) DISJOINT region(b)
```

thì hợp lệ.

Nếu:

```text
UNKNOWN overlap
```

thì safe code không được phép giả định chúng độc lập.

---

# 13. Field-sensitive inference

Ví dụ:

```axiom
struct Particle {
    position: Vec3,
    velocity: Vec3,
}
```

Có thể:

```axiom
update_position(p.position);
update_velocity(p.velocity);
```

Compiler nhận biết:

```text
region(position)
DISJOINT
region(velocity)
```

Do đó hai mutable capabilities có thể tồn tại đồng thời nếu chúng không overlap.

Đây là một điểm giúp Axiom đạt hiệu năng cao mà không cần programmer viết borrow annotation.

---

# 14. Numeric literal resolution

Literal ban đầu **không lập tức có concrete type**.

Ví dụ:

```axiom
let x = 10;
```

`10` trước tiên là:

```text
IntegerLiteral(10)
```

Sau constraint solving mới thành:

```text
i32
i64
usize
...
```

Ví dụ:

```axiom
let x: u8 = 10;
```

→ `10 : u8`.

Nhưng:

```axiom
let x: u8 = 300;
```

→ compile error.

Không truncate âm thầm.

---

# 15. Unsuffixed numeric literal

Axiom có default deterministic.

Ví dụ:

```axiom
let x = 10;
```

Compiler dùng default integer type được quy định bởi language specification.

Khuyến nghị:

```text
integer literal default → i32
floating literal default → f64
```

nhưng expected context luôn có quyền resolve trước default.

Ví dụ:

```axiom
let x: i64 = 10;
```

→ `10` trở thành `i64`, không phải `i32` rồi cast.

---

# 16. Không có implicit numeric conversion chain

Ví dụ:

```axiom
let x: i64 = some_u8;
```

Không tự động tạo hàng loạt conversion:

```text
u8 → i32 → i64
```

Conversion phải:

- direct
- deterministic
- lossless nếu implicit
- hoặc explicit nếu có khả năng mất dữ liệu.

Ví dụ:

```axiom
let x = value as i64;
```

---

# 17. Operator resolution

Operator không phải magic compiler special case hoàn toàn.

Ví dụ:

```axiom
a + b
```

semantic resolution:

```text
operator+(a, b)
```

thông qua trait/operator mechanism.

Nhưng các operator control-flow như:

```text
&&
||
?
```

có semantic rules riêng vì liên quan đến:

- short circuit
- control flow
- Result/Option propagation.

---

# 18. Operator ambiguity

Nếu:

```axiom
a + b
```

có nhiều implementation cùng match và không thể resolve duy nhất:

```text
EOP_AMBIGUOUS
```

Không dùng:

- declaration order
- import order
- compiler heuristic
- “best looking match”

để quyết định.

---

# 19. Generic inference

Ví dụ:

```axiom
fn max<T: Ord>(a: T, b: T) -> T
```

Gọi:

```axiom
let x = max(10, 20);
```

Compiler:

```text
T = inferred integer type
T : Ord
```

Sau đó generic instance:

```text
max<i32>
```

được tạo nếu default inference dẫn tới `i32`.

---

# 20. Generic inference từ return context

Ví dụ:

```axiom
fn create<T>() -> T
```

Có:

```axiom
let x: String = create();
```

Compiler suy ra:

```text
T = String
```

Không cần:

```axiom
create<String>()
```

---

# 21. Generic ambiguity

Nhưng:

```axiom
let x = create();
```

không có context:

```text
T = ?
```

→ error.

Compiler không được tự chọn `String`.

---

# 22. Associated types

Ví dụ:

```axiom
trait Iterator {
    type Item;

    fn next(self) -> Option<Self::Item>;
}
```

Khi:

```axiom
let x = iterator.next();
```

trait solver phải resolve:

```text
Iterator implementation
→ concrete Self
→ associated Item
→ Option<Item>
```

Associated type resolution là một phần của semantic elaboration.

---

# 23. Trait solver

Trait solver hoạt động theo:

```text
Goal
 ↓
Candidate discovery
 ↓
Unification
 ↓
Constraint propagation
 ↓
Nested goals
 ↓
Coherence
 ↓
Selection
 ↓
Proven / NotProven / Ambiguous / Error
```

Ví dụ:

```text
Goal:
Vec<i32> : Clone
```

solver tìm implementation phù hợp.

---

# 24. Trait solver không được đoán

Có ba trạng thái khác nhau:

```text
PROVEN
NOT_PROVEN
AMBIGUOUS
```

`AMBIGUOUS` không được biến thành `NOT_PROVEN`.

Điều này rất quan trọng đối với generic code.

---

# 25. Trait resolution và method resolution

Với:

```axiom
x.foo()
```

thứ tự:

```text
1. inherent function
2. trait implementation
3. explicitly imported extension
4. generic extension
5. ambiguity/error
```

Đã frozen từ Module/Frontend architecture.

---

# 26. Không có implicit conversion để cứu overload

Ví dụ:

```axiom
foo(i64)
```

và:

```axiom
foo(f64)
```

Gọi:

```axiom
foo(u8_value)
```

Compiler không được thử:

```text
u8 → i64
u8 → f64
```

rồi chọn một cái tùy heuristic.

Nếu có conversion hợp lệ theo rule rõ ràng thì candidate ranking phải deterministic; nếu vẫn không duy nhất → error.

---

# 27. Coercion model

Axiom nên có **rất ít coercion built-in**.

Cho phép các coercion semantic rõ ràng như:

```text
Array<T> → view<T>
Array<T> → mut_view<T>
```

trong call argument context.

Không cho phép một chuỗi coercion tùy ý.

Đặc biệt không:

```text
T
→ reference
→ pointer
→ integer
→ another type
```

---

# 28. Option

Không có:

```axiom
let x: String = maybe_string;
```

nếu:

```text
maybe_string : Option<String>
```

Programmer phải xử lý:

```axiom
match maybe_string {
    Some(x) => ...
    None => ...
}
```

hoặc API tương ứng.

Compiler không tự unwrap.

---

# 29. Result

Tương tự:

```axiom
let x = parse(input)?;
```

`?` được elaboration thành semantic control flow tương đương:

```text
Ok(value)
    → continue

Err(error)
    → propagate
```

Không phải exception.

---

# 30. Closure inference

Ví dụ:

```axiom
let f = |x| x * 2;
```

Compiler phải giải constraint:

```text
x : ?
x * 2 → operator constraint
```

Nếu context không đủ:

```axiom
let f = |x| x;
```

thì closure có thể giữ type parameter nội bộ tùy thiết kế generic closure, nhưng **không được biến thành một dynamic universal function**.

Khuyến nghị:

> Closure type được compiler tạo tự động; programmer không phải viết closure type.

---

# 31. Capture inference

Compiler tự phân tích capture:

```axiom
let x = 10;

let f = || print(x);
```

→ read capture.

Nếu:

```axiom
let f = || modify(x);
```

→ mutable capture nếu semantics cho phép.

Nếu closure giữ ownership:

```axiom
let f = move || consume(resource);
```

→ ownership capture.

Không cần programmer khai báo environment struct.

Compiler tạo anonymous environment type.

---

# 32. Async type inference

```axiom
async fn load() -> Data
```

Semantic type:

```text
Future<Data>
```

Nhưng programmer không cần viết:

```axiom
Future<Data>
```

khi khai báo `async fn`.

Compiler-generated Future type là anonymous compiler type.

---

# 33. Await và capability inference

Đây là điểm rất quan trọng.

Ví dụ:

```axiom
async fn process(data: mut_view<Data>) {
    await something();
    use(data);
}
```

Compiler phát hiện:

```text
mut_view<Data>
live across suspension
```

→ không cho phép nếu storage/execution contract không chứng minh được an toàn.

Compiler không yêu cầu:

```text
'lifetime
Pin
Send annotation
```

mà tự phân tích.

---

# 34. Future Send inference

Compiler kiểm tra các state fields sống qua suspension.

Ví dụ:

```text
Future state:
    String       → Send
    Arc<Data>     → Send
    Rc<Data>      → !Send
```

Nếu Future được:

```axiom
spawn(future)
```

thì solver yêu cầu:

```text
Future : Send
```

Nếu không:

```text
spawn_local(...)
```

có thể phù hợp.

---

# 35. Comptime inference

Comptime sử dụng **chính type system của Axiom**.

Ví dụ:

```axiom
const SIZE = 1024;

comptime {
    generate_table(SIZE);
}
```

Không có một type system thứ hai.

Compiler vẫn kiểm tra:

```text
type
ownership
capability
visibility
trait
resource rules
```

---

# 36. Ownership elaboration

Sau khi type inference hoàn tất, compiler tạo semantic ownership state.

Ví dụ:

```axiom
let a = make();
let b = a;
use(b);
```

Elaboration:

```text
a : Owned<T>

b = Move(a)

a : Moved
b : Owned<T>

use(b)
```

---

# 37. Ownership không phải type annotation

Không tạo syntax như:

```text
Owned<T>
Borrowed<'a, T>
MutableBorrow<'a, T>
```

trong source language.

Đó là **compiler semantic state**.

Điều này giữ cho source language đơn giản.

---

# 38. Capability elaboration

Ví dụ:

```axiom
fn process(data: mut_view<Data>)
```

Compiler nội bộ:

```text
CapabilityId = C1
Owner = data-source
Region = R1
Access = WRITE
Lifetime = call scope
```

Sau verification, representation có thể trở thành:

```text
pointer + length
```

hoặc representation khác.

Nhưng semantic capability có thể bị erase.

---

# 39. Ownership + capability + type là ba lớp khác nhau

Đây là điểm cần frozen rõ ràng:

```text
Type
  ↓
"cái này là gì?"

Ownership
  ↓
"ai sở hữu nó?"

Capability
  ↓
"ai được truy cập vùng nào và bằng quyền gì?"
```

Ví dụ:

```text
Vec<i32>
Owned
WRITE capability
```

không phải một khái niệm duy nhất.

---

# 40. Type identity không phụ thuộc representation

Ví dụ:

```axiom
struct UserId {
    value: u64
}
```

và:

```axiom
type UserId = u64;
```

không giống nhau.

`struct UserId` là nominal type.

Compiler không được merge semantic identity chỉ vì:

```text
size_of(UserId) == 8
```

---

# 41. Recursive type checking

By-value recursion:

```axiom
struct Node {
    next: Node
}
```

→ reject vì kích thước vô hạn.

Nhưng:

```axiom
struct Node {
    next: Box<Node>
}
```

hợp lệ.

Không cần programmer-facing pointer.

---

# 42. Trait recursion

Compiler cần phát hiện cycle:

```text
A requires B
B requires C
C requires A
```

Trait solver phải:

- memoize goals
- detect cycles
- có recursion depth limit
- phân biệt cycle hợp lệ và cycle không resolve được.

Không được để trait resolution chạy vô hạn.

---

# 43. Type equality

Axiom phân biệt:

```text
Definitional Equality
Structural Equality
Nominal Equality
Representation Equality
```

Ví dụ hai struct có cùng fields không có nghĩa là cùng type.

---

# 44. Never type

```axiom
fn abort() -> never
```

`never` có thể coerce vào control-flow context phù hợp.

Ví dụ:

```axiom
let x = if condition {
    value
} else {
    abort()
};
```

Type của expression là type của branch còn lại.

---

# 45. Unit type

Function không return value:

```axiom
fn log(msg: Str) {
    ...
}
```

có:

```text
return type = unit
```

`unit` là type thật, nhưng compiler có thể erase representation.

---

# 46. Type inference phải deterministic

Một source không được có:

```text
compiler A → i32
compiler B → i64
```

chỉ vì implementation khác nhau.

Semantic resolution phải được specification định nghĩa.

---

# 47. Error recovery

Type checker không được dừng ngay lỗi đầu tiên.

Ví dụ:

```axiom
let a: i32 = "hello";
let b = unknown();
let c = a + b;
```

Compiler nên tạo structured diagnostics:

```text
ETypeMismatch
EResolveUndefined
ETypeInferenceFailure
```

và sử dụng `ErrorType` để hạn chế cascade.

Không sinh 50 lỗi giả từ một lỗi gốc.

---

# 48. Structured type errors

Diagnostic nội bộ:

```text
TypeError {
    code
    source_span
    expected
    actual
    context
    candidates
    constraints
    notes
    related_spans
}
```

Ví dụ AI tooling có thể lấy:

```text
expected: mut_view<Data>
actual: view<Data>
reason: write capability required
```

thay vì chỉ:

```text
type mismatch
```

---

# 49. Compiler explanation

Axiom compiler nên hỗ trợ semantic explanation:

```text
axiom explain type x
axiom explain call foo(...)
axiom explain move x
axiom explain capability data
axiom explain trait Iterator
```

Ví dụ:

```text
x : Buffer
ownership : moved
moved-from-by : b = x
source : line 42
```

Đây là một lợi thế lớn cho AI agent.

---

# 50. Type checking không được phụ thuộc optimizer

Type checker không được nói:

> “Optimizer chắc chắn loại bỏ allocation nên cho phép.”

Sai.

Semantic validity phải độc lập:

```text
-O0
-O1
-O2
-O3
```

đều phải reject/accept giống nhau.

Optimization chỉ được exploit facts đã được chứng minh.

---

# 51. Type checking không được phụ thuộc target khi không cần

Ví dụ:

```axiom
let x: i32 = 10;
```

phải có semantic giống nhau trên:

```text
x86-64
ARM64
RISC-V
```

Ngoại trừ những phần thực sự target-dependent như:

```text
usize
isize
alignment
ABI
SIMD
target features
```

---

# 52. Type inference và ABI tách biệt

Ví dụ:

```axiom
fn foo(x: Vec3) -> Vec3
```

Type checker chỉ cần biết:

```text
Vec3
```

Không cần biết:

```text
register nào
stack nào
XMM hay GPR
```

ABI lowering xảy ra sau semantic optimization.

---

# 53. Type inference và storage tách biệt

```axiom
let x = BigStruct(...);
```

Type checker không quyết định:

```text
stack
heap
register
inline
arena
```

Đây là nhiệm vụ của later compiler stages.

---

# 54. Type inference và allocation tách biệt

```axiom
let x = Box::new(value);
```

Type checker hiểu:

```text
Box<T>
ownership
Drop
Send/Share
```

nhưng không quyết định allocation thực tế.

Optimizer có thể phát hiện:

```text
Box does not escape
address not observed
```

và eliminate allocation.

---

# 55. Trait object

`dyn Trait` là explicit.

Ví dụ:

```axiom
let x: dyn Drawable = shape;
```

compiler biết programmer yêu cầu dynamic dispatch.

Không tự biến:

```text
T
```

thành:

```text
dyn Trait
```

để giải quyết generic/type mismatch.

---

# 56. Generic static dispatch mặc định

```axiom
fn draw<T: Drawable>(x: T)
```

→ static dispatch.

```axiom
fn draw(x: dyn Drawable)
```

→ dynamic dispatch.

Do đó abstraction không tự tạo:

- vtable
- allocation
- object header
- runtime dispatch

nếu không được yêu cầu.

---

# 57. Type inference + specialization

Sau khi resolve:

```text
T = ConcreteType
```

compiler có thể:

```text
monomorphize
specialize
inline
devirtualize
share code
```

nhưng những việc này thuộc Generic/Optimization Engine, không thuộc semantic meaning.

---

# 58. GPU type checking

`@kernel` tạo một semantic execution domain riêng.

Compiler kiểm tra:

```text
type legality
storage domain
address space
Send/Share requirements
atomic rules
capability rules
GPU ABI
```

Ví dụ:

```axiom
@kernel
fn add(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
)
```

được kiểm tra bằng cùng core type/capability system.

Nhưng GPU legality là một constraint bổ sung.

---

# 59. FFI type checking

Compiler phải kiểm tra:

```text
Axiom type
↓
FFI-safe?
↓
ABI-compatible?
↓
representation-compatible?
↓
ownership contract?
```

Ví dụ:

```axiom
extern "C" fn foo(x: String)
```

không tự động hợp lệ chỉ vì `String` là type hợp lệ.

---

# 60. Comptime type checking

Code:

```axiom
comptime {
    generate_type();
}
```

sau khi sinh declaration phải quay lại pipeline:

```text
Generated HIR
 ↓
Resolution
 ↓
Type checking
 ↓
Trait solving
 ↓
Ownership
 ↓
Verification
```

Không có đường tắt.

---

# 61. Không cho generated code bypass type checker

Đây là invariant bảo mật/compiler integrity rất quan trọng:

> **Generated code có cùng semantic obligations như source code.**

Không có:

```text
comptime → inject unchecked HIR
```

---

# 62. Type inference architecture

Đề xuất internal structures:

```text
InferenceContext
 ├── TypeVariables
 ├── IntegerVariables
 ├── FloatVariables
 ├── RegionVariables
 ├── CapabilityVariables
 ├── GenericVariables
 ├── TraitGoals
 ├── EqualityConstraints
 ├── SubstitutionMap
 └── Diagnostics
```

---

# 63. Constraint types

Các constraint cơ bản:

```text
Equal(T1, T2)
Implements(T, Trait)
Assignable(T1, T2)
Convertible(T1, T2)
Copy(T)
Drop(T)
Send(T)
Share(T)
Sized(T)
FFISafe(T)
GPULegal(T)
RegionOutlives(R1, R2)
Disjoint(R1, R2)
CapabilityCompatible(C1, C2)
```

---

# 64. Constraint solving theo phase

Không nên giải tất cả ngay lập tức.

```text
Phase 1
Name constraints

Phase 2
Type equality

Phase 3
Generic constraints

Phase 4
Trait constraints

Phase 5
Conversion/coercion

Phase 6
Ownership

Phase 7
Capability

Phase 8
Closure/async/comptime
```

Như vậy diagnostics tốt hơn và tránh dependency cycle không cần thiết.

---

# 65. Một nguyên tắc quan trọng: delay commitment

Ví dụ:

```axiom
let x = 10;
foo(x);
```

Không nên quyết định `10 = i32` ngay tại parser hoặc literal parser.

Compiler giữ:

```text
IntegerLiteral(10)
T0
```

sau đó:

```text
foo(T)
```

mới cung cấp constraint.

Điều này làm inference mạnh hơn nhưng vẫn deterministic.

---

# 66. Nhưng không delay vô hạn

Inference phase phải có boundary rõ ràng.

Khi kết thúc function body:

```text
all unconstrained inference variables
```

phải:

- default theo rule
- hoặc diagnostic

Không để unresolved type variable trôi xuống MIR.

---

# 67. Fully Typed HIR

Sau BOOTSTRAP-104, HIR phải đảm bảo:

```text
Every expression has TypeId
Every declaration has resolved type
Every call has resolved FunctionId
Every generic call has substitutions
Every operator has resolved implementation
Every conversion is explicit in HIR
Every closure has compiler-generated type
Every async function has Future type
Ownership actions are elaborated
Capability actions are elaborated
```

Đây là boundary rất quan trọng.

---

# 68. HIR trước và sau elaboration

### HIR ban đầu

```axiom
let y = foo(x + 1);
```

### Fully Typed HIR

Conceptually:

```text
Local y : TypeId#42

Call
  FunctionId#17
  args:
    BinaryOp(Add)
      x : TypeId#41
      IntegerLiteral(1) : i32
  result : TypeId#42
```

và ownership/capability metadata đi kèm.

---

# 69. MIR không được tự suy type

Sau boundary này:

> **MIR không phải nơi type inference lần hai.**

MIR có thể thực hiện các validation nội bộ, nhưng semantic type đã được resolve.

Điều này giúp pipeline:

```text
Frontend semantics
      ↓
stable Typed HIR
      ↓
MIR
```

rõ ràng.

---

# 70. Invariants — BOOTSTRAP-104

Đề xuất freeze các invariant sau:

### `ATYPE-80`
Every expression reaching Fully Typed HIR has a resolved semantic type.

### `ATYPE-81`
Type inference is deterministic.

### `ATYPE-82`
Unconstrained inference variables must resolve by specified defaults or produce diagnostics.

### `ATYPE-83`
Inference never invents implicit ownership transfer, clone, allocation, synchronization, or dynamic dispatch.

### `ATYPE-84`
Copy semantics are type properties, not representation properties.

### `ATYPE-85`
Move semantics are ownership state transitions.

### `ATYPE-86`
Clone is never inserted implicitly.

### `ATYPE-87`
View creation may be implicit only for non-escaping call argument adaptation.

### `ATYPE-88`
Escaping views require explicit semantic construction and valid provenance.

### `ATYPE-89`
Capability validity is checked independently from physical representation.

### `ATYPE-90`
Unknown aliasing cannot be inferred as disjoint.

### `ATYPE-91`
Numeric literals remain unresolved until sufficient type constraints exist.

### `ATYPE-92`
Literal overflow is a compile-time error.

### `ATYPE-93`
Implicit numeric conversion chains are forbidden.

### `ATYPE-94`
Generic inference must produce one unique substitution or a diagnostic.

### `ATYPE-95`
Trait resolution distinguishes Proven, NotProven, Ambiguous, and Error.

### `ATYPE-96`
Ambiguous trait/method/operator resolution is a compile-time error.

### `ATYPE-97`
Method resolution follows the specified deterministic precedence.

### `ATYPE-98`
Dynamic dispatch is never introduced implicitly.

### `ATYPE-99`
Closure capture modes are compiler-inferred.

### `ATYPE-100`
Async Future state requirements are compiler-inferred.

### `ATYPE-101`
Send/Share properties are compiler-derived and never assumed from syntax alone.

### `ATYPE-102`
Comptime code uses the same core type and ownership semantics.

### `ATYPE-103`
Generated declarations re-enter normal semantic checking.

### `ATYPE-104`
Type checking does not depend on optimization level.

### `ATYPE-105`
Type checking does not depend on physical storage strategy.

### `ATYPE-106`
Type checking does not decide machine ABI or register allocation.

### `ATYPE-107`
Fully Typed HIR contains no unresolved semantic overloads.

### `ATYPE-108`
MIR lowering must not silently introduce unresolved type inference.

### `ATYPE-109`
Compiler diagnostics must preserve the constraints and source provenance that caused a type error.

### `ATYPE-110`
The compiler may perform more internal inference than the programmer can explicitly express.

---

# 71. Kết quả cuối cùng của BOOTSTRAP-104

Ta đã đạt được mô hình khá mạnh:

```text
Programmer
    │
    │ viết
    ▼
simple source
    │
    ▼
Compiler
 ├── type inference
 ├── generic inference
 ├── trait solving
 ├── overload resolution
 ├── numeric resolution
 ├── ownership inference
 ├── capability inference
 ├── closure capture inference
 ├── async state inference
 ├── Send/Share inference
 └── GPU/FFI/comptime constraints
    │
    ▼
Fully Typed + Semantically Elaborated HIR
    │
    ▼
MIR
```

Đây chính là hướng **“compiler hiểu nhiều hơn programmer phải viết”** mà Axiom đang theo đuổi.

---

# BOOTSTRAP-105 — Semantic HIR → MIR Lowering & Control/Dataflow Construction

Bước tiếp theo nên khóa **MIR**, vì hiện tại chúng ta đã có:

```text
103 Frontend
104 Type checking + inference + semantic elaboration
```

nhưng chưa có một định nghĩa hoàn chỉnh về cách source-level semantics biến thành **IR thực thi trung gian**.

Phạm vi BOOTSTRAP-105 nên giải quyết:

```text
Fully Typed HIR
       ↓
Desugaring completion
       ↓
Control-flow construction
       ↓
Place / Operand construction
       ↓
Ownership state transitions
       ↓
Capability operations
       ↓
Drop points
       ↓
Closure lowering
       ↓
Async lowering
       ↓
Pattern lowering
       ↓
Comptime materialization
       ↓
MIR
```

Đặc biệt cần khóa những vấn đề rất quan trọng:

- MIR instruction set chính xác
- SSA hay non-SSA ở giai đoạn đầu
- `Place` / projection
- `Move` / `Copy`
- `Load` / `Store`
- `Drop`
- `StorageLive` / `StorageDead`
- capability creation/release
- `view` / `mut_view`
- CFG
- phi values
- `match`
- loop
- closure environment
- function call
- indirect/dynamic call
- async suspension point
- panic/unwind edges
- allocation semantic ops
- atomic/volatile
- GPU operations
- FFI calls
- source mapping
- làm sao MIR vẫn **đơn giản nhưng đủ mạnh để toàn bộ optimizer/backend phía sau sử dụng**.