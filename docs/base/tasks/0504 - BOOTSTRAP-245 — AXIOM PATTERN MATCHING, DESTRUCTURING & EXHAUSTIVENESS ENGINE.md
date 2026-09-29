# BOOTSTRAP-245 — AXIOM PATTERN MATCHING, DESTRUCTURING & EXHAUSTIVENESS ENGINE

**TRẠNG THÁI: FROZEN / COMPLETED**

Đây là phần nối trực tiếp **Type System → Place Model → Ownership → Control Flow → MIR**.

Mục tiêu:

> `match` phải mạnh như algebraic pattern matching hiện đại, nhưng pattern không được tạo ra hidden copy, hidden allocation, hidden borrow hoặc phá vỡ ownership/capability model.

---

# 1. Pattern không phải một kiểu expression riêng

Pattern là một **destructuring specification** dùng để kiểm tra và bind một value/place.

Pipeline:

```text
Scrutinee
   ↓
Pattern
   ↓
Pattern Matrix
   ↓
Constructor Analysis
   ↓
Binding / Place Projection
   ↓
Ownership + Capability Check
   ↓
Exhaustiveness
   ↓
Typed HIR
   ↓
MIR CFG
```

---

# 2. Các loại pattern Core

Axiom v1 hỗ trợ:

```text
Wildcard
Literal
Binding
Tuple
Struct
Enum variant
Array
Slice
Range
Or-pattern
```

Ví dụ:

```axiom
match x {
    0 => ...
    1 => ...
    n => ...
}
```

---

# 3. Wildcard

```axiom
match value {
    _ => ...
}
```

`_`:

- không bind tên
- không tạo copy
- không tạo ownership transition
- chỉ chứng minh pattern khớp.

---

# 4. Binding

```axiom
match value {
    x => use(x)
}
```

Binding mặc định tuân theo **value access semantics**.

Nếu `value` là Copy:

```text
Copy
```

Nếu non-Copy:

```text
Move
```

nhưng compiler được phép tối ưu physical representation.

---

# 5. Đây là điểm quan trọng

Axiom **không có hidden borrow trong pattern binding**.

Ví dụ:

```axiom
struct User {
    name: String
    age: u32
}

let user = make_user()

match user {
    User { name, age } => ...
}
```

Nếu `name` được bind như owning `String`:

```text
user.name → Move
user.age  → Copy
```

Không có implicit clone.

---

# 6. Pattern binding có thể chỉ truy cập Place

Compiler không nhất thiết materialize value ngay.

Ví dụ:

```axiom
match user {
    User { age } => age + 1
}
```

có thể biểu diễn:

```text
user.age
   ↓
READ
   ↓
SSA/register
```

không cần copy toàn struct.

---

# 7. `match` scrutinee

Scrutinee được evaluate trước:

```axiom
match make_user() {
    ...
}
```

Semantics:

```text
evaluate make_user()
        ↓
obtain scrutinee
        ↓
pattern selection
        ↓
selected arm
```

Chỉ một arm được thực thi.

---

# 8. Ownership của scrutinee

Compiler xác định access mode dựa trên pattern.

Ví dụ:

```axiom
match user {
    User { name } => consume(name)
}
```

có thể consume field `name`.

Nếu pattern cần toàn bộ value:

```axiom
match user {
    u => consume(u)
}
```

→ Move toàn bộ `user`.

---

# 9. Partial move trong match

Ví dụ:

```axiom
match user {
    User { name, age } => consume(name)
}
```

sau arm:

```text
user.name = Moved
user.age  = Valid
```

Nếu `user` không còn được dùng, compiler có thể kết thúc lifetime.

---

# 10. Match join point

Đây là vấn đề khó.

```axiom
let mut user = make_user()

match condition {
    true => consume(user.name)
    false => use(user.age)
}

use(user.age)
```

Compiler phải merge ownership state từ hai CFG branches.

```text
Branch A:
name = Moved
age  = Valid

Branch B:
name = Valid
age  = Valid
```

Join:

```text
name = MaybeMoved
age  = Valid
```

→ sử dụng `user.name` sau match có thể bị reject.

---

# 11. Ownership state lattice

Pattern verifier sử dụng cùng ownership lattice:

```text
UNINIT
INIT
MOVED
PARTIAL
DROPPED
MAYBE_MOVED
ERROR
```

`MAYBE_MOVED` là trạng thái control-flow join nội bộ.

---

# 12. Destructuring struct

```axiom
match point {
    Point { x, y } => ...
}
```

pattern:

```text
Struct(Point)
├── x → binding
└── y → binding
```

Mỗi binding gắn với Place projection:

```text
point.x
point.y
```

---

# 13. Struct field shorthand

Nếu tên binding trùng field:

```axiom
Point { x, y }
```

tương đương semantic với:

```axiom
Point { x: x, y: y }
```

nhưng chỉ một pattern AST representation canonical.

---

# 14. Rename

```axiom
Point {
    x: px,
    y: py
}
```

→

```text
px → point.x
py → point.y
```

---

# 15. Partial struct pattern

```axiom
Point { x, .. }
```

chỉ kiểm tra/bind `x`.

Các field khác không bị implicit Move.

Đây là quy tắc rất quan trọng.

---

# 16. Enum pattern

```axiom
enum Result<T, E> {
    Ok(T)
    Err(E)
}
```

Pattern:

```axiom
match result {
    Ok(value) => ...
    Err(error) => ...
}
```

Compiler biết variant constructor:

```text
Ok
Err
```

---

# 17. Variant payload projection

```text
result
  ↓
Downcast(Ok)
  ↓
Field(0)
```

Đây chính là Place Model từ BOOTSTRAP-244.

---

# 18. Wrong variant access

Không được:

```text
result.Ok.value
```

nếu `result` chưa được chứng minh là `Ok`.

Pattern/match mới tạo refinement:

```text
Inside Ok arm:
    result ∈ Ok
```

---

# 19. Enum refinement

Ví dụ:

```axiom
match result {
    Ok(x) => use(x)
    Err(e) => use(e)
}
```

Trong arm:

```text
Ok arm:
    result.variant = Ok
    x = result.payload
```

---

# 20. Nested patterns

```axiom
match result {
    Ok(User { name, age }) => ...
    Err(e) => ...
}
```

Pattern tree:

```text
Ok
└── User
    ├── name
    └── age
```

Compiler recursively lowers thành Place projections.

---

# 21. Tuple patterns

```axiom
match pair {
    (a, b) => ...
}
```

→

```text
pair.0
pair.1
```

---

# 22. Nested tuple

```axiom
match x {
    (a, (b, c)) => ...
}
```

→

```text
x.0
x.1.0
x.1.1
```

---

# 23. Array patterns

Axiom hỗ trợ fixed array patterns:

```axiom
match a {
    [first, second, third] => ...
}
```

với:

```text
[3]T
```

Compiler biết kích thước compile-time.

---

# 24. Array rest

Có thể:

```axiom
[first, .., last]
```

nhưng phần `..` không tạo owning copy.

Nếu cần access phần giữa, compiler tạo view/capability thích hợp.

---

# 25. Slice patterns

Với:

```text
view<T>
```

có thể pattern:

```axiom
match data {
    [] => ...
    [x] => ...
    [first, ..] => ...
}
```

Đây là pattern runtime vì length không biết compile-time.

---

# 26. Slice binding

```axiom
[first, rest @ ..] => ...
```

`rest` semantic là view/capability vào phần còn lại, không phải clone.

Lifetime phụ thuộc scrutinee capability.

---

# 27. Binding mode

Axiom tránh Rust-style syntax:

```text
ref
ref mut
```

Thay vào đó **type context quyết định access intent**.

Ví dụ API cần view thì pattern binding có thể được contextually typed thành view.

Không có:

```axiom
ref x
```

trong Core v1.

---

# 28. Literal pattern

```axiom
match code {
    200 => ok()
    404 => missing()
    _ => other()
}
```

Literal phải có equality semantics phù hợp.

Không được dùng arbitrary runtime overloaded equality để làm pattern matching trong Core.

---

# 29. Numeric range

```axiom
match x {
    0..10 => ...
    _ => ...
}
```

Canonical semantics:

```text
0 <= x < 10
```

Inclusive:

```axiom
0..=10
```

→

```text
0 <= x <= 10
```

---

# 30. Range pattern validity

Compiler phải kiểm tra:

```text
type compatibility
range ordering
representable bounds
```

Ví dụ range đảo:

```axiom
10..0
```

→ compile error.

Không tạo runtime surprise.

---

# 31. Character ranges

```axiom
match c {
    'a'..='z' => ...
    _ => ...
}
```

được phép nếu type pattern hỗ trợ ordered scalar semantics.

---

# 32. Or-pattern

```axiom
match x {
    0 | 1 | 2 => small()
    _ => other()
}
```

Tất cả alternatives phải bind **cùng tập tên với type tương thích**.

---

# 33. Invalid or-pattern

Không cho:

```axiom
match x {
    Some(a) | None => ...
}
```

vì arm thứ nhất bind `a`, arm thứ hai không.

---

# 34. Nested or-pattern

Có thể:

```axiom
match x {
    Some(0 | 1) => ...
    None => ...
}
```

Compiler expand pattern matrix nội bộ.

---

# 35. Pattern guards

Axiom hỗ trợ:

```axiom
match x {
    n if n > 10 => big()
    _ => other()
}
```

Guard là runtime condition.

---

# 36. Guard không đóng góp exhaustiveness

Ví dụ:

```axiom
match x {
    n if n > 10 => ...
    0 => ...
}
```

không chứng minh mọi integer đã được cover.

Vì guard có thể false.

Compiler vẫn cần:

```text
fallback
```

hoặc chứng minh exhaustiveness độc lập.

---

# 37. Guard ownership

Guard được evaluate với binding đã được tạo theo semantic rules.

Nếu binding là owning Move, guard sử dụng binding theo ownership.

Compiler không clone chỉ để phục vụ guard.

---

# 38. Guard side effects

Guard là expression bình thường nên có thể có effects.

Evaluation order:

```text
scrutinee
→ pattern test
→ bindings
→ guard
→ body
```

Nếu guard false, compiler thử arm tiếp theo.

---

# 39. Pattern ordering

Arms được kiểm tra theo source order.

```axiom
match x {
    _ => first()
    0 => second()
}
```

Arm `0` unreachable.

Compiler phải cảnh báo/error tùy diagnostic level; Core semantics xác định arm đầu tiên bắt tất cả.

---

# 40. Unreachable pattern

Ví dụ:

```axiom
match x {
    Some(_) => ...
    Some(1) => ...
    None => ...
}
```

`Some(1)` unreachable.

Diagnostic:

```text
PATTERN_UNREACHABLE
```

---

# 41. Exhaustiveness

`match` phải exhaustive nếu biểu thức không có explicit fallback semantics.

Ví dụ:

```axiom
match option {
    Some(x) => ...
    None => ...
}
```

complete.

---

# 42. Missing variant

```axiom
match result {
    Ok(x) => ...
}
```

→ error:

```text
missing pattern: Err(_)
```

Diagnostic phải chỉ rõ constructor bị thiếu.

---

# 43. Exhaustiveness không dựa vào runtime

Compiler quyết định statically đối với closed enums.

Không cần:

```text
default:
panic
```

để bù cho compiler thiếu khả năng phân tích.

---

# 44. Integer exhaustiveness

Integer domain quá lớn để enumerate.

```axiom
match x {
    0 => ...
    1 => ...
}
```

→ thiếu:

```text
_
```

Compiler dùng interval coverage.

---

# 45. Boolean

```axiom
match x {
    true => ...
    false => ...
}
```

exhaustive.

Nếu:

```axiom
match x {
    true => ...
}
```

→ thiếu `false`.

---

# 46. Option

`Option<T>` là enum:

```axiom
None
Some(T)
```

Exhaustiveness engine xử lý như enum bình thường.

---

# 47. Result

```axiom
match r {
    Ok(x) => ...
    Err(e) => ...
}
```

exhaustive.

Không cần special-case semantics.

---

# 48. Never type

Nếu:

```axiom
let x: never = ...
```

không có reachable value.

Match trên `never` có thể được coi là exhaustive với zero arms về mặt semantic.

---

# 49. Pattern matrix

Exhaustiveness engine sử dụng conceptual matrix:

```text
Pattern Matrix
        ↓
Constructor specialization
        ↓
Witness generation
        ↓
Coverage proof
```

Witness là một giá trị mẫu chứng minh pattern còn thiếu.

---

# 50. Missing-pattern witness

Ví dụ:

```axiom
match result {
    Ok(_) => ...
}
```

compiler có thể sinh witness:

```text
Err(_)
```

Diagnostic:

```text
non-exhaustive match
missing pattern: Err(_)
```

---

# 51. Nested witness

Ví dụ:

```axiom
match x {
    Some(Ok(_)) => ...
    None => ...
}
```

missing:

```text
Some(Err(_))
```

Diagnostic phải thể hiện nested constructor.

---

# 52. Pattern usefulness

Mỗi arm được kiểm tra:

```text
Useful?
```

Nếu không:

```text
unreachable
```

Điều này dùng cùng pattern matrix engine với exhaustiveness.

---

# 53. Pattern compiler không được dựa vào optimizer

Pattern checking phải hoàn thành **trước optimization**.

Không được:

```text
optimizer proves branch impossible
→ semantic compiler accepts invalid match
```

---

# 54. `if` vs `match`

`if`:

```axiom
if condition { ... }
```

không cần exhaustiveness.

`match`:

```axiom
match value { ... }
```

có constructor coverage semantics.

---

# 55. `if let`

Axiom v1 có thể hỗ trợ syntactic sugar:

```axiom
if let Some(x) = value {
    ...
}
```

nhưng semantic canonicalization:

```text
match value {
    Some(x) => body
    _ => unit
}
```

Do đó không cần semantic subsystem riêng.

---

# 56. `while let`

Tương tự:

```axiom
while let Some(x) = next() {
    use(x)
}
```

lower thành loop + match.

---

# 57. `let` pattern

Axiom cho phép pattern trong binding:

```axiom
let (x, y) = pair
```

Nhưng `let` pattern phải **irrefutable**.

---

# 58. Refutable pattern trong `let`

Không hợp lệ:

```axiom
let Some(x) = value
```

vì `value` có thể là `None`.

Phải dùng:

```axiom
if let Some(x) = value {
    ...
}
```

hoặc `match`.

---

# 59. Irrefutable patterns

Các pattern như:

```text
_
x
(x, y)
Point { x, y }
```

là irrefutable khi type đảm bảo constructor duy nhất phù hợp.

---

# 60. Refutable patterns

Ví dụ:

```text
Some(x)
0
true
Some(_)
```

nếu scrutinee type có nhiều khả năng.

---

# 61. Binding type inference

```axiom
let (x, y) = point
```

compiler lấy:

```text
x: type(point.0)
y: type(point.1)
```

Không cần annotation.

---

# 62. Pattern type mismatch

```axiom
let (x, y) = 42
```

→ type error.

Pattern engine không cố đoán programmer muốn gì.

---

# 63. Constructor namespace

Enum constructor resolution phải deterministic.

Ví dụ:

```axiom
use Result::Ok
```

hoặc qualified:

```axiom
Result::Ok(x)
```

Không dùng heuristic giữa nhiều constructor trùng tên.

---

# 64. Struct pattern resolution

```axiom
Point { x, y }
```

resolver xác định:

```text
Point → StructId
x → FieldId
y → FieldId
```

Pattern AST không giữ string lookup sau resolution.

---

# 65. Pattern + Place Model

Đây là phần trung tâm.

Ví dụ:

```axiom
match user {
    User {
        address: Address {
            city
        }
    } => ...
}
```

compiler tạo:

```text
Place(user)
  → Field(address)
  → Field(city)
```

Binding:

```text
city → Place(user.address.city)
```

Không có temporary `Address` object.

---

# 66. Pattern + Move

```axiom
match user {
    User { address } => consume(address)
}
```

→

```text
Move(user.address)
```

không phải:

```text
Copy(user.address)
```

nếu `Address` non-Copy.

---

# 67. Pattern + Copy

Nếu:

```text
age: u32
```

```axiom
User { age }
```

có thể:

```text
Copy(user.age)
```

---

# 68. Pattern + view

Nếu context yêu cầu:

```axiom
fn print_name(x: view<String>)
```

pattern/binding có thể được dùng để tạo ephemeral view tới field thay vì Move.

Compiler không cần:

```text
clone String
```

---

# 69. Pattern + mut_view

Trong mutable context:

```axiom
fn update(user: mut_view<User>) {
    match user {
        User { age } => age = 20
    }
}
```

`age` phải được xử lý như mutable capability derived from:

```text
user.age
```

với exclusive access.

---

# 70. Capability splitting

Pattern có thể split capability:

```text
mut_view<User>
        ↓
mut_view<user.name>
mut_view<user.age>
```

nếu fields disjoint.

Đây là compiler-internal capability derivation.

---

# 71. Không tạo hai mutable alias

Pattern:

```axiom
match user {
    User { a, b } => ...
}
```

không được biến thành hai mutable capabilities nếu `a` và `b` có overlap.

Field projections thường chứng minh được disjoint.

---

# 72. Array pattern + capability

```axiom
match mut_view(array) {
    [first, second, ..] => ...
}
```

compiler có thể derive:

```text
first → element 0
second → element 1
rest → range 2..n
```

Các region này disjoint.

---

# 73. Pattern + Drop

Owning binding trong arm:

```axiom
match user {
    User { name } => consume(name)
}
```

Sau arm:

```text
name → consumed
```

Compiler phải đảm bảo remaining fields được cleanup đúng cách.

---

# 74. Arm-local bindings

Binding chỉ tồn tại trong arm:

```axiom
match x {
    Some(v) => use(v)
    None => ...
}
```

`v` không tồn tại sau `match`.

Không có lifetime complexity cho programmer.

---

# 75. Match result ownership

```axiom
let name = match user {
    User { name } => name
}
```

`name` trở thành owner ngoài match.

Compiler phải propagate ownership:

```text
user.name
   ↓ Move
arm result
   ↓
name
```

---

# 76. Match arm type unification

Tất cả reachable arms phải có compatible result type.

```axiom
let x = match condition {
    true => 10
    false => 20
}
```

→ `x: i32`.

---

# 77. Block arm

```axiom
match x {
    Some(v) => {
        let y = process(v)
        y + 1
    }
    None => 0
}
```

Final expression của block là arm result.

---

# 78. Diverging arm

```axiom
match x {
    Some(v) => v
    None => panic("missing")
}
```

`panic` → `never`.

Type join:

```text
T + never → T
```

---

# 79. Match CFG

MIR không nhất thiết giữ pattern syntax.

Ví dụ:

```axiom
match result {
    Ok(x) => foo(x)
    Err(e) => bar(e)
}
```

có thể lower:

```text
switch result.tag
 ├── Ok  → project payload → foo
 └── Err → project payload → bar
```

---

# 80. Decision tree optimization

Compiler có thể biến:

```text
match x {
    0 => ...
    1 => ...
    2 => ...
    ...
}
```

thành:

```text
jump table
```

hoặc:

```text
binary search
```

hoặc:

```text
branch chain
```

mà không thay đổi semantic order cần thiết.

---

# 81. Pattern test order

Pattern matching có semantic matching order nhưng compiler có thể tối ưu decision tree nếu:

```text
no observable difference
```

và guards/effects được bảo toàn.

---

# 82. Guards hạn chế reordering

Ví dụ:

```axiom
match x {
    0 if check_a() => ...
    0 if check_b() => ...
    _ => ...
}
```

`check_a()` và `check_b()` có thể có effects.

Compiler phải giữ semantics.

---

# 83. Pure patterns

Pattern test thuần:

```text
enum tag
integer comparison
struct constructor
```

có thể tối ưu rất mạnh.

---

# 84. Pattern cannot execute arbitrary user code

Core pattern semantics không gọi:

```text
user-defined == 
```

để quyết định pattern.

Điều này đảm bảo:

```text
determinism
exhaustiveness
compiler reasoning
```

---

# 85. Pattern matching and floating point

Không dùng arbitrary `NaN` equality để tạo exhaustiveness giả.

Floating-point literal patterns cần semantic rule rõ ràng từ Numeric subsystem.

`NaN` phải được xử lý riêng vì equality semantics không phải equivalence thông thường.

---

# 86. String patterns

Axiom v1 **không đưa general regex/string-pattern matching vào Core**.

String matching nâng cao thuộc library.

Core chỉ cần literal/pattern semantics đủ để compiler reasoning.

---

# 87. User-defined pattern protocol

Không đưa pattern trait kiểu:

```text
Pattern<T>
```

vào Core v1.

Lý do:

```text
arbitrary user code
→ exhaustiveness không thể chứng minh tổng quát
→ pattern semantics trở nên opaque
```

Library có thể cung cấp parser/matcher riêng.

---

# 88. Exhaustiveness phải compiler-known

Closed enum:

```text
enum Color {
    Red
    Green
    Blue
}
```

compiler biết toàn bộ constructors.

Nếu package khác không thể thêm variant:

→ exhaustive analysis ổn định.

---

# 89. Open/dynamic types

`dyn Trait` không có closed constructor set.

Không cho giả định exhaustive dựa trên runtime type.

---

# 90. Pattern matching dynamic trait

Có thể explicit runtime downcast nếu metadata/runtime facility cung cấp:

```text
dyn Trait
    ↓
runtime type test
```

nhưng đây là dynamic operation, không phải Core exhaustive enum matching.

---

# 91. Pattern + generic type

```axiom
fn unwrap<T>(x: Option<T>) -> T {
    match x {
        Some(v) => v
        None => panic(...)
    }
}
```

pattern engine hoạt động với generic `T` mà không cần biết representation của `T`.

---

# 92. Generic enum specialization

Compiler biết constructor:

```text
Option::Some
Option::None
```

nhưng payload type có thể là generic.

MIR projection vẫn type-safe.

---

# 93. Pattern + zero-cost abstraction

```axiom
match option {
    Some(x) => x + 1
    None => 0
}
```

có thể compile thành:

```text
tag test
conditional branch
```

không cần runtime pattern object.

---

# 94. Pattern + niche optimization

Nếu ABI/layout compiler chọn:

```text
Option<NonNull<T>>
```

có thể encode:

```text
None
```

bằng niche.

Pattern semantics không phụ thuộc representation.

---

# 95. Pattern + representation independence

Exhaustiveness dựa trên **semantic constructors**, không dựa vào:

```text
enum tag integer value
```

vì layout có thể thay đổi.

---

# 96. Pattern + ABI

`@repr(C)` enum có thể có representation contract riêng.

Pattern compiler vẫn dùng semantic variant IDs.

ABI lowering sau đó mới map sang tag/payload representation.

---

# 97. Pattern + FFI

Foreign tagged unions không tự động trở thành Axiom enum.

FFI wrapper phải khai báo semantic representation/validity.

---

# 98. Pattern + unsafe

Unsafe có thể tạo invalid enum representation.

Khi đó safe pattern matching chỉ được phép sau khi invariant đã được establish.

Unsafe không cho compiler bỏ exhaustive checking.

---

# 99. Diagnostics

Pattern diagnostics nên structured:

```text
PATTERN_NON_EXHAUSTIVE
PATTERN_UNREACHABLE
PATTERN_TYPE_MISMATCH
PATTERN_BINDING_MISMATCH
PATTERN_DUPLICATE_BINDING
PATTERN_INVALID_RANGE
PATTERN_GUARD_NOT_EXHAUSTIVE
PATTERN_MOVE_CONFLICT
PATTERN_CAPABILITY_CONFLICT
```

---

# 100. AI/compiler explanation

Compiler phải trả lời được:

```text
Why is this match non-exhaustive?
```

Ví dụ:

```text
missing constructor:
    Result::Err

witness:
    Err(_)

scrutinee type:
    Result<i32, Error>
```

---

# 101. Explain move

Nếu:

```axiom
match user {
    User { name } => consume(name)
}

print(user.name)
```

compiler có thể giải thích:

```text
user.name was moved in match arm #1
therefore user.name is unavailable after the match
```

---

# 102. Explain partial move

Diagnostic graph:

```text
user.name
   ↓
pattern binding `name`
   ↓
Move
   ↓
user becomes partially moved
   ↓
later access rejected
```

---

# 103. Pattern checking architecture

```text
PatternAST
    ↓
PatternResolver
    ↓
TypedPattern
    ↓
PatternConstructor Analysis
    ↓
Pattern Matrix
    ├── Usefulness
    └── Exhaustiveness
    ↓
Binding Planner
    ↓
Place Projection
    ↓
Ownership/Capability Access Plan
    ↓
Typed HIR
```

---

# 104. Binding Planner

Binding planner quyết định mỗi binding:

```text
Binding {
    name
    type
    source_place
    access_mode
    ownership_effect
    capability
}
```

Ví dụ:

```text
name:
    source = user.name
    type = String
    access = MOVE
```

---

# 105. Pattern-to-MIR lowering

Ví dụ:

```axiom
match x {
    Some(v) => foo(v)
    None => bar()
}
```

MIR conceptual:

```text
bb0:
    switch_variant x
        Some → bb1
        None → bb2

bb1:
    v = Move(x.payload)
    call foo(v)
    goto bb3

bb2:
    call bar()
    goto bb3
```

---

# 106. No hidden temporary

Không:

```text
tmp = clone(x.payload)
v = tmp
```

trừ khi semantic type thực sự yêu cầu Copy/Clone.

---

# 107. Pattern bindings and SSA

Optimizer có thể trực tiếp map:

```text
v
```

vào:

```text
SSA payload
```

nếu ownership semantics cho phép.

---

# 108. Pattern + destruction

Nếu enum payload owning:

```text
Some(String)
```

và match:

```axiom
Some(s) => consume(s)
```

payload ownership chuyển sang `s`.

Nếu arm kết thúc mà `s` vẫn owned:

```text
Drop(s)
```

theo ordinary Drop rules.

---

# 109. Unmatched values

Nếu match branch không selected:

Không có Drop cho payload branch không được activate.

Chỉ scrutinee's actual active value phải được cleanup.

---

# 110. Enum discriminant

Compiler có semantic operation:

```text
VariantTest
```

không bắt buộc load physical discriminant nếu representation cho phép khác.

---

# 111. Pattern engine + constant propagation

Sau semantic checking:

```axiom
match true {
    true => foo()
    false => bar()
}
```

optimizer có thể eliminate `false` branch.

Không được dùng optimization để thay thế semantic validation.

---

# 112. Pattern engine + `@cfg`

`@cfg` có thể loại bỏ arm trước semantic analysis.

Sau đó pattern set còn lại phải exhaustive.

Ví dụ target-specific enum variants phải được resolve theo configuration trước exhaustiveness.

---

# 113. Generic pattern coverage

Compiler có thể cache pattern coverage theo:

```text
TypeId
PatternShape
GenericConstraints
```

để incremental compilation nhanh.

---

# 114. Incremental pattern analysis

Thay đổi body của arm không nên buộc re-run toàn bộ module nếu:

```text
pattern shape
scrutinee type
constructor set
```

không đổi.

---

# 115. Parallel checking

Các pattern arms có thể được phân tích song song sau khi:

```text
scrutinee type
constructor environment
```

đã resolved.

Diagnostic ordering vẫn deterministic theo source order.

---

# 116. Formal model

Pattern matching semantic function:

```text
match : Value × Pattern → MatchResult
```

Trong đó:

```text
MatchResult =
    Fail
  | Success(Bindings)
```

với binding map:

```text
Name → Place/Value Access
```

---

# 117. Exhaustiveness formalization

Một pattern set `P` exhaustive trên domain `D` khi:

```text
∀v ∈ D:
    ∃p ∈ P:
        matches(v,p)
```

Guard không được coi là unconditional coverage.

---

# 118. Usefulness formalization

Pattern `p` hữu ích nếu tồn tại witness:

```text
∃v ∈ D:
    matches(v,p)
    &&
    ¬covered_by_previous_patterns(v)
```

Nếu không:

```text
unreachable
```

---

# 119. Ownership formalization

Binding:

```text
b := bind(p, source_place)
```

có access mode:

```text
READ
COPY
MOVE
VIEW
MUT_VIEW
```

được suy ra từ:

```text
type
context
pattern form
expected type
ownership state
capability state
```

---

# 120. Core invariants — FROZEN

```text
APATTERN-20
Pattern matching is a compile-time semantic mechanism over typed values and Places.

APATTERN-21
Patterns do not require runtime pattern objects.

APATTERN-22
Pattern matching is deterministic.

APATTERN-23
Pattern evaluation does not implicitly clone values.

APATTERN-24
Wildcard patterns do not create bindings or ownership transitions.

APATTERN-25
Pattern bindings have explicit compiler-derived access semantics.

APATTERN-26
Copyable bindings use Copy semantics where value extraction is required.

APATTERN-27
Non-Copy owning bindings use Move semantics unless contextual capability access is explicitly established.

APATTERN-28
Pattern binding never silently performs Clone.

APATTERN-29
Struct patterns resolve fields by semantic FieldId.

APATTERN-30
Tuple patterns resolve tuple projections by index.

APATTERN-31
Enum patterns resolve variants by semantic VariantId.

APATTERN-32
Nested patterns recursively compose Place projections.

APATTERN-33
Partial struct patterns do not implicitly access unspecified fields.

APATTERN-34
Enum payload access requires successful variant refinement.

APATTERN-35
Pattern bindings are scoped to their matching arm or enclosing binding construct.

APATTERN-36
Owning pattern bindings participate in ordinary Drop semantics.

APATTERN-37
Partial moves produced by patterns follow the ownership verifier.

APATTERN-38
Custom destructive Drop restrictions apply to pattern destructuring.

APATTERN-39
Pattern branches participate in ownership-state dataflow joins.

APATTERN-40
A value may not be used after a pattern-induced move.

APATTERN-41
A pattern may derive capabilities from an existing valid capability.

APATTERN-42
Pattern-derived mutable capabilities must obey exclusivity.

APATTERN-43
Disjoint field/element pattern regions may be independently accessed.

APATTERN-44
Unknown overlapping pattern regions are never assumed disjoint.

APATTERN-45
Slice rest bindings are views/capabilities when represented non-owningly.

APATTERN-46
Slice rest bindings do not implicitly clone the remaining elements.

APATTERN-47
Array pattern semantics preserve fixed-size array semantics.

APATTERN-48
Range patterns use defined ordering and interval semantics.

APATTERN-49
Invalid or reversed range patterns are compile-time errors.

APATTERN-50
Or-pattern alternatives must have compatible binding sets.

APATTERN-51
Pattern guards do not establish exhaustiveness coverage.

APATTERN-52
Pattern guards execute only after their pattern has matched.

APATTERN-53
Pattern arm ordering is semantically observable when guards/effects are involved.

APATTERN-54
Unreachable patterns are diagnosed deterministically.

APATTERN-55
Closed enums require exhaustive matching unless an unconditional covering pattern exists.

APATTERN-56
Boolean matching requires coverage of both semantic boolean values.

APATTERN-57
Integer exhaustiveness is established through domain/range reasoning.

APATTERN-58
`Option` and `Result` use ordinary enum exhaustiveness semantics.

APATTERN-59
The `never` type has an empty value domain.

APATTERN-60
Refutable patterns are forbidden in irrefutable binding contexts.

APATTERN-61
`if let` and `while let`, if provided, lower to ordinary match/control-flow semantics.

APATTERN-62
Pattern exhaustiveness is checked before optimization.

APATTERN-63
Pattern usefulness is checked before optimization.

APATTERN-64
Optimizer transformations cannot justify otherwise invalid pattern semantics.

APATTERN-65
Pattern representation is independent of enum physical layout.

APATTERN-66
Enum niche optimization does not change pattern semantics.

APATTERN-67
ABI representation does not redefine semantic constructors.

APATTERN-68
Foreign tagged representations require explicit FFI contracts before safe pattern interpretation.

APATTERN-69
Unsafe construction of invalid representations does not disable safe pattern verification.

APATTERN-70
Dynamic trait objects do not provide closed constructor sets for exhaustive matching.

APATTERN-71
Runtime type tests are distinct from Core enum pattern matching.

APATTERN-72
User-defined arbitrary runtime pattern protocols are not part of Core v1.

APATTERN-73
Pattern matching must not depend on arbitrary overloaded equality.

APATTERN-74
Pattern matching preserves required expression evaluation and effect ordering.

APATTERN-75
Pattern lowering produces ordinary typed control flow and Place accesses.

APATTERN-76
Pattern lowering may eliminate intermediate objects when semantic identity permits.

APATTERN-77
Pattern payload extraction may be lowered directly to SSA/register values.

APATTERN-78
Pattern matching may use jump tables, decision trees, branches, or equivalent representations after semantic verification.

APATTERN-79
Pattern optimization must preserve guard/effect ordering.

APATTERN-80
Pattern diagnostics expose missing constructors, witnesses, bindings, and ownership causes.

APATTERN-81
Pattern analysis may be incremental and cached.

APATTERN-82
Pattern analysis may execute in parallel while preserving deterministic diagnostics.

APATTERN-83
Pattern-generated code re-enters ordinary ownership, capability, effect, and control-flow verification.

APATTERN-84
Generated/comptime patterns cannot bypass semantic verification.

APATTERN-85
Pattern semantics are independent of optimization level.

APATTERN-86
Pattern semantics are independent of physical storage location.

APATTERN-87
Pattern semantics preserve ownership and capability provenance.

APATTERN-88
Pattern destructuring never introduces hidden heap allocation.

APATTERN-89
Pattern destructuring never introduces hidden Clone operations.

APATTERN-90
Pattern matching integrates directly with the Axiom Place Model.

APATTERN-91
Pattern matching integrates directly with ownership dataflow.

APATTERN-92
Pattern matching integrates directly with capability analysis.

APATTERN-93
Pattern matching integrates directly with Drop elaboration.

APATTERN-94
Pattern matching integrates directly with MIR CFG construction.

APATTERN-95
Pattern matching is a semantic transformation, not merely syntax sugar.

APATTERN-96
Axiom pattern semantics remain valid across CPU, GPU, async, FFI, and freestanding profiles subject to their respective legality contracts.

APATTERN-97
Pattern matching cannot create safe data races.

APATTERN-98
Pattern-derived views cannot outlive their provenance.

APATTERN-99
Pattern-derived mutable access cannot coexist with conflicting safe capabilities.

APATTERN-100
No pattern optimization may violate observable behavior, ownership, initialization, capability, provenance, or cleanup semantics.
```

---

# Kiến trúc hiện tại

Sau 245, frontend semantic core đã có cấu trúc rất mạnh:

```text
                    Axiom Source
                         │
              ┌──────────▼──────────┐
              │ Lexer / Parser      │
              └──────────┬──────────┘
                         ▼
                    Resolution
                         │
                         ▼
                  Type Inference
                         │
                         ▼
                Expression Semantics
                         │
            ┌────────────┼────────────┐
            ▼            ▼            ▼
        Type System    Place       Patterns
            │            │            │
            └────────────┼────────────┘
                         ▼
                 Ownership / Drop
                         │
                  Capability / Alias
                         │
                         ▼
                       MIR
                         │
                         ▼
                  Verified MIR
                         │
                         ▼
                       OptIR
```

Điểm rất đáng chú ý: **Pattern Engine không phải một subsystem cô lập**. Nó trực tiếp sử dụng `Place`, `Ownership`, `Capability`, `Type`, `Control Flow`. Đây là cách tránh việc sau này compiler có hàng loạt hệ thống semantics chồng chéo.

---

# TASK TIẾP THEO

## **BOOTSTRAP-246 — AXIOM CLOSURES, CAPTURE ANALYSIS & FIRST-CLASS CALLABLES**

Phần tiếp theo sẽ giải quyết sâu:

```text
|x| x + y
```

và các vấn đề khó hơn:

```text
closure
capture
capture-by-value
capture-by-view
capture-by-mut_view
capture inference
closure environment
closure identity
Fn / FnMut / FnOnce
function pointer
non-capturing closure
closure → dyn Fn
closure → generic callable
closure escaping
closure + async
closure + Send/Share
closure + thread spawn
closure + GPU
closure allocation elimination
closure ABI
closure lifetime
```

Đặc biệt, chúng ta sẽ giữ nguyên triết lý của Axiom:

> **Programmer viết closure tự nhiên; compiler tự quyết định capture, environment layout, stack/register/heap allocation và có thể loại bỏ hoàn toàn closure nếu có thể.**

