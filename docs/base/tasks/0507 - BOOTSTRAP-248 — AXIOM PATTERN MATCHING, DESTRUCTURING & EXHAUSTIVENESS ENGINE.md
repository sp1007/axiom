# BOOTSTRAP-248 — AXIOM PATTERN MATCHING, DESTRUCTURING & EXHAUSTIVENESS ENGINE

**TRẠNG THÁI: FROZEN / COMPLETED**

Pattern matching của Axiom không chỉ là cú pháp `match`. Nó là một **semantic decomposition engine** nối trực tiếp:

```text
Pattern
  ↓
Place / Value decomposition
  ↓
Ownership / Initialization
  ↓
Capability
  ↓
Type narrowing
  ↓
Exhaustiveness
  ↓
Control Flow
  ↓
MIR
```

Nguyên tắc trung tâm:

> **Pattern không tự tạo ra ownership semantics mới. Nó chỉ biểu diễn cách chương trình quan sát, destructure hoặc chuyển giao quyền sở hữu của một giá trị đã tồn tại.**

---

# 1. Match là expression

```axiom
let result = match value {
    0 => "zero"
    1 => "one"
    _ => "other"
}
```

`match` có một semantic type.

Các arm phải có type tương thích.

---

# 2. Scrutinee được evaluate đúng một lần

```axiom
match expensive() {
    A => ...
    B => ...
}
```

`expensive()` chỉ được gọi một lần.

Semantic order:

```text
evaluate scrutinee
→ establish value/place state
→ test patterns
→ select arm
→ evaluate arm body
```

---

# 3. Pattern không re-evaluate scrutinee

Compiler không được biến:

```text
match x
```

thành nhiều lần đọc `x` nếu việc đó làm thay đổi observable behavior.

---

# 4. Pattern categories

Axiom hỗ trợ:

```text
Wildcard
Binding
Literal
Range
Tuple
Struct
Enum
Array
Slice
Or-pattern
Nested pattern
```

---

# 5. Wildcard

```axiom
match x {
    _ => ...
}
```

Wildcard không bind và không consume value theo semantic ownership.

---

# 6. Binding pattern

```axiom
match value {
    x => use(x)
}
```

`x` nhận toàn bộ matched value theo ownership rules.

Nếu value là non-Copy owning value, binding mặc định có thể là Move.

---

# 7. Copy binding

Với type `Copy`:

```axiom
match value {
    x => ...
}
```

binding có thể tạo value copy theo semantic `Copy`.

Không tạo alias mutable.

---

# 8. Explicit view binding

Khi chỉ muốn đọc:

```axiom
match value {
    x => {
        let v = view(x)
        ...
    }
}
```

hoặc pattern binding có modifier tương ứng nếu syntax extension được chuẩn hóa sau này.

Core principle:

> **Read-only observation không được vô tình trở thành ownership transfer.**

---

# 9. Literal pattern

```axiom
match x {
    0 => ...
    42 => ...
    _ => ...
}
```

Literal pattern kiểm tra equality theo semantic comparison phù hợp.

---

# 10. Numeric pattern

Compiler phải áp dụng numeric literal typing rules.

Không cho literal pattern mơ hồ tạo implicit narrowing nguy hiểm.

---

# 11. Range pattern

```axiom
match x {
    0..10 => ...
    _ => ...
}
```

Axiom canonical:

```text
start..end
```

là half-open.

```text
start..=end
```

là inclusive.

---

# 12. Range exhaustiveness

Compiler phải hiểu domain của type.

Ví dụ với:

```text
u8
```

thì:

```axiom
0..=255
```

cover toàn bộ domain.

---

# 13. Range overflow

Range pattern không được silently overflow.

Nếu bounds không representable hoặc semantics ambiguous:

→ compile error.

---

# 14. Boolean pattern

```axiom
match enabled {
    true => ...
    false => ...
}
```

đây là exhaustive.

---

# 15. Enum pattern

Ví dụ:

```axiom
enum Option<T> {
    Some(T)
    None
}
```

Pattern:

```axiom
match value {
    Some(x) => ...
    None => ...
}
```

---

# 16. Enum payload ownership

Nếu:

```axiom
Option<String>
```

và:

```axiom
Some(x)
```

`x` có thể Move payload.

Sau match, compiler phải biết chính xác trạng thái của original place.

---

# 17. Partial move qua enum

Ví dụ:

```axiom
enum Message {
    Text(String)
    Number(i32)
}
```

Trong:

```axiom
match message {
    Text(s) => consume(s)
    Number(n) => ...
}
```

chỉ payload của variant được chọn tồn tại trong arm.

---

# 18. Unselected variants

Payload của các variant khác không phải runtime-live value.

Compiler không được giả định chúng đã được initialize.

---

# 19. Exhaustiveness của enum

Compiler biết danh sách variant từ type definition.

```text
Option
 ├── Some
 └── None
```

Nếu thiếu `None`:

```text
non-exhaustive match
```

trừ khi có wildcard/covering pattern.

---

# 20. Struct pattern

```axiom
struct Point {
    x: i32
    y: i32
}
```

Có thể:

```axiom
match p {
    Point { x, y } => ...
}
```

---

# 21. Struct field binding

Mỗi field binding được resolver ánh xạ tới một `Place`.

```text
p
├── p.x
└── p.y
```

Đây là điểm nối trực tiếp với **BOOTSTRAP-244 Place Model**.

---

# 22. Partial struct destructuring

```axiom
match p {
    Point { x, .. } => ...
}
```

chỉ destructure `x`.

`y` vẫn thuộc ownership state của `p`, tùy binding semantics.

---

# 23. Partial move

Ví dụ:

```axiom
struct User {
    name: String
    age: i32
}
```

```axiom
match user {
    User { name, .. } => consume(name)
}
```

semantic state có thể là:

```text
user.name → Moved
user.age  → Owned
```

---

# 24. Parent object sau partial move

Không thể sử dụng toàn bộ:

```axiom
use(user)
```

nếu `user.name` đã Move.

Nhưng:

```axiom
use(user.age)
```

có thể hợp lệ nếu compiler chứng minh field vẫn initialized.

---

# 25. Drop sau partial move

Compiler Drop verifier phải drop:

```text
user.age
```

nhưng **không drop `user.name` lần nữa**.

---

# 26. Custom Drop restriction

Nếu struct có user-defined/custom Drop, partial move phải bị hạn chế theo rule đã frozen.

Lý do:

custom Drop có thể cần toàn bộ object invariant.

---

# 27. Compiler-derived Drop

Với compiler-derived Drop, field-sensitive partial move có thể được hỗ trợ.

---

# 28. Tuple pattern

```axiom
let pair = (10, 20)

match pair {
    (x, y) => ...
}
```

Place tree:

```text
pair
├── pair.0
└── pair.1
```

---

# 29. Nested patterns

```axiom
match value {
    Some((x, y)) => ...
    None => ...
}
```

Compiler recursively decomposes:

```text
value
→ Some payload
→ tuple
→ field 0 / field 1
```

---

# 30. Nested ownership

Mỗi level phải giữ ownership state.

Không được coi toàn bộ pattern là một operation “Move everything”.

---

# 31. Array pattern

Fixed arrays:

```axiom
let a: [4]i32 = ...
```

có thể pattern:

```axiom
match a {
    [a, b, c, d] => ...
}
```

---

# 32. Array exhaustiveness

Array pattern phải cover đúng cardinality.

---

# 33. Slice pattern

Slice/view patterns:

```axiom
match xs {
    [] => ...
    [first, ..rest] => ...
}
```

được phép nếu semantics được định nghĩa qua view decomposition.

---

# 34. Slice ownership

Destructuring một `view<T>` không tạo ownership của underlying storage.

Đây là điểm rất quan trọng:

```text
view<T>
→ capability decomposition
```

không:

```text
view<T>
→ ownership transfer
```

---

# 35. Mutable view pattern

`mut_view<T>` vẫn giữ exclusive capability.

Pattern không được duplicate capability.

---

# 36. Overlapping view pattern

Nếu pattern tạo ra:

```text
mut_view(a)
mut_view(b)
```

và compiler không chứng minh:

```text
DISJOINT(a,b)
```

→ reject.

---

# 37. Or-pattern

Ví dụ:

```axiom
match x {
    0 | 1 => ...
    _ => ...
}
```

Hai pattern cùng dẫn tới một arm.

---

# 38. Binding consistency trong OR-pattern

Nếu:

```axiom
0 | x => ...
```

thì binding environment không đồng nhất.

Core v1 nên **reject**.

Mọi alternative trong một OR-pattern phải tạo binding environment tương thích.

---

# 39. Binding type consistency

Ví dụ:

```text
Some(x) | Other(x)
```

`x` phải có cùng semantic type và ownership/capability mode.

---

# 40. Binding ownership consistency

Nếu một alternative Move `x` nhưng alternative kia chỉ Copy/View `x`:

→ reject.

Không được tạo ownership semantics phụ thuộc vào pattern branch.

---

# 41. Guard

Ví dụ:

```axiom
match x {
    Some(n) if n > 10 => ...
    Some(_) => ...
    None => ...
}
```

Guard được evaluate **sau khi pattern match thành công**.

---

# 42. Guard không tạo exhaustiveness coverage

Đây là rule rất quan trọng.

```axiom
match x {
    Some(n) if n > 10 => ...
    None => ...
}
```

không exhaustive cho `Some(n)` còn lại.

---

# 43. Guard không dùng để chứng minh exhaustive

Compiler không được giả định:

```text
n > 10
```

đã cover variant `Some`.

---

# 44. Guard effects

Guard là expression bình thường.

Nếu guard có:

```text
IO
atomic
panic
```

effects phải được giữ.

---

# 45. Guard ordering

Trong:

```axiom
A if condition1 => ...
A if condition2 => ...
A => ...
```

compiler evaluate theo source arm order.

Optimization chỉ được reorder khi observable semantics không đổi.

---

# 46. Unreachable arm

Ví dụ:

```axiom
match b {
    true => ...
    false => ...
    _ => ...
}
```

`_` unreachable.

Compiler nên diagnostic.

---

# 47. Unreachable không nhất thiết là hard error

Đề xuất:

```text
warning
```

mặc định.

Có thể trở thành error trong strict lint profile.

---

# 48. Earlier arm wins

Nếu hai patterns overlap:

```axiom
match x {
    _ => first
    10 => second
}
```

arm `10` unreachable.

Không có backtracking.

---

# 49. Pattern decision tree

Compiler có thể lower:

```text
match x {
    0 => A
    1 => B
    2 => C
    _ => D
}
```

thành jump table, binary search, branch tree...

Nhưng semantic order vẫn được giữ.

---

# 50. Pattern compiler

Architecture:

```text
Parsed Pattern
      ↓
Pattern HIR
      ↓
Typed Pattern
      ↓
Pattern Matrix
      ↓
Exhaustiveness Analysis
      ↓
Unreachable Analysis
      ↓
Decision Tree
      ↓
MIR CFG
```

---

# 51. Pattern Matrix

Compiler nội bộ có thể dùng pattern matrix:

```text
columns = scrutinee components
rows    = match arms
```

để thực hiện exhaustiveness/redundancy analysis.

---

# 52. Constructor space

Pattern compiler phải biết constructor space của type:

```text
bool → {true,false}
enum → variants
tuple → product
struct → fields
integer → value domain
```

---

# 53. Product types

Struct/tuple là product:

```text
A × B
```

Pattern decomposition recurse vào từng component.

---

# 54. Sum types

Enum là sum:

```text
A + B + C
```

Exhaustiveness phải cover từng constructor.

---

# 55. Integer domains

Integer type có finite domain.

Ví dụ:

```text
u8 = 0..=255
```

Compiler có thể reason về range coverage.

---

# 56. Large integer domains

Không cần enumerate từng integer.

Pattern compiler dùng interval/range reasoning.

---

# 57. Signed integer domain

Ví dụ `i8`:

```text
-128..=127
```

range analysis phải tránh overflow trong compiler reasoning.

---

# 58. Exhaustiveness of ranges

```axiom
match x {
    0..=127 => ...
    128..=255 => ...
}
```

exhaustive cho `u8`.

---

# 59. Floating-point patterns

Đây là vùng đặc biệt.

Do:

```text
NaN
-0.0
multiple NaN representations
```

nên Core v1 nên **hạn chế float literal pattern**.

Đề xuất:

- không cho range exhaustiveness trên float;
- equality semantics phải explicit;
- wildcard vẫn cover remaining domain.

---

# 60. NaN

Không được coi:

```text
NaN == NaN
```

là true chỉ để làm exhaustiveness đơn giản.

Pattern compiler phải tôn trọng floating semantics.

---

# 61. String patterns

Core v1 không nên đưa regex/string-pattern engine vào pattern core.

String matching nên là library/algorithm layer.

---

# 62. Byte/string literals

Exact literal pattern có thể được hỗ trợ nếu semantics và hashing/equality rõ ràng.

---

# 63. Option special case

Không có magic semantic riêng cho `Option`.

Compiler nhận biết:

```text
enum Option<T>
```

và xử lý như enum bình thường.

Library convenience có thể thêm syntax/helper sau này.

---

# 64. Result special case

Tương tự:

```text
enum Result<T,E>
```

không cần special-case trong semantic kernel.

---

# 65. Pattern typing

Pattern được type-check trong context của scrutinee.

Ví dụ:

```text
scrutinee : Option<i32>
```

thì:

```text
Some(x)
```

suy ra:

```text
x : i32
```

---

# 66. Generic enum pattern

```axiom
fn unwrap<T>(x: Option<T>) -> T {
    match x {
        Some(v) => v
        None => panic()
    }
}
```

Pattern typing hoạt động với substituted generic type.

---

# 67. Generic pattern specialization

Sau instantiation:

```text
Option<T>
```

→

```text
Option<String>
```

ownership của payload được resolve cụ thể.

---

# 68. Pattern + trait

Pattern matching enum không cần trait dispatch.

Nhưng literal equality của custom types chỉ được phép nếu language semantics định nghĩa rõ.

Core v1 nên giữ pattern matching predictable và compiler-known.

---

# 69. No arbitrary overloaded pattern semantics

Không cho mỗi type tự định nghĩa:

```text
match x {
    CustomPattern(...) => ...
}
```

thông qua arbitrary runtime function.

Điều đó làm exhaustiveness không thể chứng minh.

---

# 70. Pattern constructors are structural

Pattern constructor phải được compiler resolve từ:

```text
enum variant
struct
tuple
array
```

hoặc compiler-known primitives.

---

# 71. Pattern namespaces

Variant names được resolve theo declaration identity, không theo text guessing.

---

# 72. Struct field shorthand

```axiom
Point { x, y }
```

tương đương binding field names.

Resolver xác định:

```text
x → Point.x
y → Point.y
```

---

# 73. Rename binding

```axiom
Point { x: px, y: py }
```

field là `x`, local binding là `px`.

---

# 74. Ignoring fields

```axiom
Point { x, .. }
```

các field còn lại không được bind.

Không có ownership transfer nếu chúng không được destructure.

---

# 75. Explicit field order

Pattern struct không phụ thuộc field declaration order.

```axiom
Point { y, x }
```

semantic mapping vẫn:

```text
y → Point.y
x → Point.x
```

---

# 76. Tuple positional order

Tuple pattern có order cố định:

```text
(a,b,c)
```

→ `.0`, `.1`, `.2`.

---

# 77. Pattern evaluation

Pattern matching có thể có runtime tests:

```text
literal comparison
range comparison
tag test
length test
```

Compiler được phép optimize chúng.

---

# 78. Destructuring itself is not always a copy

Ví dụ:

```axiom
Point { x, y }
```

không nhất thiết physical-copy cả `Point`.

Compiler có thể tạo bindings trực tiếp từ places.

---

# 79. Pattern lowering to places

Ví dụ:

```axiom
Point { x, y } => ...
```

có thể lower:

```text
x = place(p.x)
y = place(p.y)
```

rồi ownership operation quyết định:

```text
Copy
Move
View
```

---

# 80. Pattern binding mode

Đề xuất semantic model:

```text
BindMove
BindCopy
BindView
BindMutView
```

Nhưng syntax Core v1 chỉ cần expose các trường hợp cần thiết.

Compiler internally giữ binding mode.

---

# 81. Default binding

Đối với owning value:

```text
binding → Move
```

đối với Copy value:

```text
binding → Copy
```

Điều này phù hợp với value semantics của Axiom.

---

# 82. No hidden clone

Pattern không bao giờ implicit gọi:

```text
clone()
```

---

# 83. View pattern

Nếu pattern chỉ cần inspect:

```text
view<T>
```

compiler dùng capability thay vì ownership.

---

# 84. Mut view pattern

Mutation trong match arm phải có exclusive capability.

---

# 85. Capability lifetime

Binding view chỉ sống trong scope cần thiết.

Không được escape khỏi owner.

---

# 86. Pattern + return view

Ví dụ conceptual:

```axiom
fn get(x: mut_view<Struct>) -> view<i32> {
    match x {
        ...
    }
}
```

returned view phải preserve provenance.

Compiler không được tạo view từ temporary payload đã kết thúc lifetime.

---

# 87. Pattern + temporary

```axiom
match make_value() {
    ...
}
```

scrutinee temporary có lifetime đủ dài cho toàn bộ match.

Sau match:

```text
temporary cleanup
```

được thực hiện.

---

# 88. Pattern + Drop

Nếu binding Move một Drop-bearing field:

```text
field → moved
```

field đó không được Drop tại scope kết thúc.

Remaining fields vẫn Drop.

---

# 89. Pattern + panic

Nếu arm panic:

compiler phải thực hiện cleanup của các values/capabilities đã live tại điểm đó.

---

# 90. Pattern + `?`

Trong match arm:

```axiom
Some(x) => foo(x)?
```

propagation tạo CFG edge tới enclosing function exit.

Ownership cleanup phải được elaborated.

---

# 91. Pattern + break/continue

Trong loop:

```axiom
for x in xs {
    match x {
        ... => break
    }
}
```

break phải chạy cleanup của arm-local values trước khi thoát.

---

# 92. Match arm scopes

Mỗi arm có semantic scope riêng:

```text
scrutinee scope
 ├── arm 1 scope
 ├── arm 2 scope
 └── arm 3 scope
```

Bindings chỉ tồn tại trong arm tương ứng.

---

# 93. Arm initialization

Compiler phải prove tất cả local variables được dùng trong arm đã initialize.

---

# 94. Binding collision

Pattern:

```axiom
Point { x, x }
```

không hợp lệ.

Một field không thể bind hai lần theo cách tạo ownership conflict.

---

# 95. Duplicate move

Pattern không được:

```text
move p.x
move p.x
```

---

# 96. Copy repeated

Nếu `p.x: Copy`, nhiều Copy reads có thể hợp lệ.

---

# 97. View repeated

Multiple read views có thể tồn tại.

Multiple mutable views chỉ hợp lệ nếu disjoint.

---

# 98. Pattern aliasing

Ví dụ hai pattern bindings cùng refer đến một place:

```text
x → p.a
y → p.a
```

nếu cả hai Move:

→ reject.

Nếu Copy:

→ hợp lệ nếu `Copy`.

---

# 99. Pattern matrix + ownership

Exhaustiveness analysis chỉ trả lời:

```text
which values are covered?
```

Ownership verifier trả lời:

```text
what happens to each place?
```

Hai hệ thống phải tách biệt.

---

# 100. Không để exhaustiveness engine quyết định ownership

Đây là architectural boundary quan trọng.

```text
PatternCompiler
       ↓
Pattern facts
       ↓
OwnershipVerifier
```

không gộp thành một engine khổng lồ.

---

# 101. Pattern facts

MIR/Typed HIR có thể lưu:

```text
PatternFact {
    Constructor
    TestedPlace
    RefinedType
    BindingPlaces
    BindingModes
}
```

---

# 102. Type narrowing

Pattern có thể refine type/state.

Ví dụ:

```text
Option<T>
```

sau:

```text
Some(x)
```

trong arm:

```text
scrutinee is Some
x : T
```

---

# 103. State refinement

Enum tag có thể trở thành known fact trong arm.

Compiler optimizer có thể tận dụng:

```text
variant = Some
```

để eliminate repeated tag checks.

---

# 104. Null elimination

Vì Axiom safe Core không có nullable pointer/null semantics:

`Option<T>` là explicit sum type.

Pattern:

```text
Some
None
```

là semantic tag matching.

---

# 105. Niche optimization

Compiler có thể represent:

```text
Option<NonNullLike>
```

bằng niche encoding.

Nhưng pattern semantics không thay đổi.

---

# 106. Pattern representation independence

Source:

```text
Some(x)
```

không quy định:

```text
tag + payload
```

physical layout cụ thể.

Layout subsystem quyết định.

---

# 107. Match lowering

Ví dụ:

```axiom
match result {
    Ok(x) => use(x)
    Err(e) => recover(e)
}
```

MIR conceptual:

```text
switch_tag result
    case Ok  → BB_ok
    case Err → BB_err
```

---

# 108. Decision tree optimization

Compiler có thể chuyển:

```text
many literal arms
```

thành:

```text
jump table
binary search
range tree
bit test
```

tùy target.

---

# 109. Semantic arm order remains

Nếu patterns/guards có observable effects:

compiler phải preserve semantics.

---

# 110. Pure pattern tests

Tag tests/literal integer tests thường pure.

Compiler có thể reorder pure tests miễn result không thay đổi.

---

# 111. Guard barrier

Guard có effect là semantic barrier.

Compiler không được tự do reorder guard evaluation qua external effects.

---

# 112. Match with references

Axiom không có source-level `&T`, `&mut T`.

Pattern semantics cũng không thêm reference syntax mới.

---

# 113. Raw pointer patterns

Raw pointers là unsafe/system values.

Pattern matching chúng như machine values được phép trong unsafe/system layer, nhưng không tự tạo safe provenance.

---

# 114. Pointer null pattern

Không có null trong safe Core.

Raw-pointer null checks thuộc unsafe/system boundary.

---

# 115. Pattern + unsafe

Unsafe trong arm không bypass:

```text
ownership
initialization
drop
capability
```

verifier.

---

# 116. Pattern + comptime

Comptime pattern matching sử dụng cùng semantic pattern engine.

Không tạo một pattern language khác.

---

# 117. Pattern + const evaluation

Nếu scrutinee là compile-time known:

```text
const X = ...
```

compiler có thể resolve match tại compile time.

Nhưng semantic exhaustiveness vẫn được kiểm tra.

---

# 118. Pattern + generic const

```axiom
fn foo<const N: usize>(x: usize) -> bool {
    match x {
        0..N => true
        _ => false
    }
}
```

Nếu range semantics cho phép dependent bound, compiler dùng const facts.

Nếu không đủ proof:

→ runtime comparison.

Không đoán.

---

# 119. Pattern + optimization

Sau semantic verification:

```text
Pattern Facts
→ RangeInfo
→ Branch Simplification
→ Jump Table
→ Dead Arm Elimination
```

---

# 120. Unreachable arm optimization

Arm đã proven unreachable có thể bị loại khỏi machine code.

Nhưng diagnostic vẫn có thể được phát ra từ semantic stage.

---

# 121. Match result merging

Nếu tất cả arms trả cùng constant:

```axiom
match x {
    A => 1
    B => 1
}
```

optimizer có thể simplify.

---

# 122. Match + ownership phi

Nếu mỗi arm tạo ownership state khác nhau:

MIR cần merge states tại join point.

Ví dụ:

```text
BB_A:
    x moved
    goto join

BB_B:
    x owned
    goto join
```

Verifier phải xác định trạng thái hợp lệ trước khi join.

---

# 123. Ownership join rule

Ownership state tại CFG join phải là conservative meet/join.

Không được chọn trạng thái thuận tiện hơn.

---

# 124. Example

```axiom
let x = get();

match flag {
    true => consume(x)
    false => use(x)
}
```

Sau match:

```text
x = potentially moved
```

nên:

```axiom
use(x)
```

sau đó phải bị reject.

---

# 125. Match with exhaustive consuming branches

```axiom
match x {
    A => consume(x)
    B => consume(x)
}
```

sau match:

```text
x = Moved
```

---

# 126. Match returning ownership

```axiom
let y = match x {
    A => transform(x)
    B => transform(x)
}
```

ownership của returned value được hợp nhất tại join.

---

# 127. Partial initialization in patterns

Compiler phải hỗ trợ:

```text
some fields initialized
some fields uninitialized
```

trong construction/destructuring lowering nếu language construct cho phép.

---

# 128. Pattern assignment

Destructuring assignment nếu hỗ trợ:

```axiom
(a, b) = pair
```

phải dùng cùng pattern semantics nhưng destination ownership rules khác binding.

Core v1 nên giữ semantic machinery sẵn sàng dù syntax có thể giới hạn.

---

# 129. Pattern declaration

```axiom
let (a, b) = pair
```

là pattern binding trong declaration.

---

# 130. Let-pattern verification

`let` pattern phải là **irrefutable**.

Ví dụ:

```axiom
let Some(x) = value
```

không hợp lệ nếu `Some` không phải guaranteed constructor.

Có thể có future `let else`, nhưng không cần thêm semantic complexity vào Core nếu chưa cần.

---

# 131. Irrefutable patterns

Ví dụ:

```text
_
x
(a,b)
Point { x, y }
```

là irrefutable khi type/layout guarantees phù hợp.

---

# 132. Refutable patterns

Ví dụ:

```text
Some(x)
0
true
A | B
```

có thể fail.

Chỉ được dùng trong conditional matching contexts như `match`.

---

# 133. Pattern context legality

Compiler kiểm tra:

```text
let pattern → irrefutable
match arm → refutable allowed
```

---

# 134. Pattern typing before exhaustiveness

Pipeline:

```text
Parse
→ Resolve
→ Type Pattern
→ Infer bindings
→ Validate ownership modes
→ Exhaustiveness
→ Unreachable
```

---

# 135. Exhaustiveness after type normalization

Generic associated types phải được normalize trước khi phân tích domain.

---

# 136. Trait-associated enum-like types

Compiler chỉ dùng constructor knowledge khi semantic type thực sự là known enum/closed type.

Không dựa vào trait metadata để giả định closed-world.

---

# 137. Open polymorphism

`dyn Trait` không có finite constructor set.

Do đó pattern matching trực tiếp theo concrete dynamic types không phải Core pattern mechanism.

---

# 138. Dynamic downcast

Nếu cần:

```text
dyn Trait → concrete type
```

phải explicit runtime metadata/downcast mechanism.

Không implicit pattern match trên mọi possible dynamic type.

---

# 139. Exhaustiveness and dyn Trait

Không thể yêu cầu exhaustive match trên open dynamic trait object.

---

# 140. Pattern matching vs visitor

Không cần class visitor pattern.

Enum + match là closed polymorphism primitive.

---

# 141. Struct inheritance không tồn tại

Do không có class inheritance, pattern exhaustiveness của struct không cần reason về subclass.

---

# 142. Stable ABI and pattern

Pattern semantics không expose enum physical tag layout.

Stable ABI enum layout chỉ được expose khi explicit ABI representation contract.

---

# 143. FFI enums

Foreign enums phải có FFI contract.

Không mặc định áp dụng Axiom exhaustiveness assumptions nếu foreign domain có unknown values.

---

# 144. Non-exhaustive foreign enum

Nếu external ABI có thể thêm value:

compiler phải yêu cầu fallback handling.

---

# 145. Pattern diagnostics

Ví dụ:

```text
non-exhaustive match
missing:
    None
```

Hoặc range:

```text
non-exhaustive match
uncovered domain:
    128..=255
```

---

# 146. Redundancy diagnostics

Ví dụ:

```text
unreachable pattern
this arm is already covered by:
    _
```

Compiler nên chỉ rõ arm trước đó.

---

# 147. Ownership diagnostic trong pattern

Ví dụ:

```text
cannot use `user` after destructuring moved field `user.name`
```

kèm place tree:

```text
user.name → Moved
user.age  → Owned
```

---

# 148. AI Explain

```text
ax explain pattern <span>
```

có thể trả:

```text
Scrutinee:
    user : User

Matched constructor:
    User

Bindings:
    name → Move user.name
    age  → Copy user.age

After arm:
    user.name = Moved
    user.age  = Owned
```

---

# 149. Pattern compiler data model

Đề xuất:

```text
PatternId
PatternKind
ConstructorId
PatternPlace
BindingId
BindingMode
RefinementFacts
Guard
SourceSpan
```

---

# 150. Pattern matrix data model

```text
PatternMatrix {
    columns
    rows
    constructors
    usefulness
    coverage
}
```

---

# 151. Usefulness analysis

Mỗi arm được kiểm tra:

```text
Does this arm match any value not already covered?
```

Nếu không:

```text
unreachable
```

---

# 152. Coverage analysis

Sau tất cả arms:

```text
Does uncovered space remain?
```

Nếu có:

```text
non-exhaustive
```

---

# 153. Complexity

Exhaustiveness algorithm phải tránh exponential blowup khi có nested patterns lớn.

Compiler có:

```text
pattern_depth_limit
pattern_matrix_limit
coverage_budget
```

---

# 154. Resource limits

Resource exhaustion không được biến thành:

```text
“match is exhaustive”
```

Nếu compiler không chứng minh được:

→ diagnostic/compile failure.

---

# 155. Conservative rule

> **Không chứng minh được exhaustive ≠ exhaustive.**

Đây là invariant quan trọng tương tự UNKNOWN aliasing.

---

# 156. Unknown pattern facts

Partial Semantic Mode có thể hiển thị:

```text
exhaustiveness = Unknown
```

nhưng Complete Semantic Mode không cho codegen.

---

# 157. Pattern engine incremental

Thay đổi một arm chỉ invalidate phần pattern matrix liên quan nếu có thể.

---

# 158. Pattern source mapping

Mỗi semantic pattern giữ source span.

Debugger có thể hiển thị:

```text
current match arm
current constructor
current binding
```

---

# 159. Pattern + optimizer debug

Nếu jump table/decision tree được tạo, debug mapping vẫn map về source arm.

---

# 160. Pattern codegen

Pattern lowering không bắt buộc tạo temporary.

Compiler có thể đọc trực tiếp:

```text
tag
field
length
```

từ source place.

---

# 161. Pattern + SIMD

Numeric match có thể được optimized bằng SIMD/table lookup nếu semantics preserved.

---

# 162. Pattern + GPU

GPU pattern matching phải obey GPU legality.

Không có dynamic allocation/runtime reflection chỉ vì match.

---

# 163. Pattern + async

Pattern local bindings live across `.await` phải obey ordinary async state-machine ownership rules.

---

# 164. Pattern + Send

Nếu a matched binding sống qua await và Future được Send:

binding phải thỏa Send requirements.

---

# 165. Pattern + Drop across await

Drop-bearing values captured by async state machine follow normal state-field lifetime.

---

# 166. Pattern + iterator

Pattern trong:

```axiom
for (x, y) in pairs {
    ...
}
```

dùng cùng pattern engine.

---

# 167. Pattern + closure

Closure parameter patterns có thể dùng subset pattern grammar.

Ví dụ:

```axiom
|(x, y)| x + y
```

Binding semantics vẫn giống let-pattern.

---

# 168. Pattern + function parameters

Function parameter destructuring nếu hỗ trợ cũng phải dùng cùng pattern model.

---

# 169. One Pattern Engine

Axiom nên **không** có ba hệ thống riêng cho:

```text
match
let destructuring
for destructuring
closure parameters
```

Mà:

```text
                Pattern Engine
                /     |      \
             match   let     params
                      |
                     for
```

---

# 170. Context-specific legality

Cùng một Pattern AST nhưng context quyết định:

```text
irrefutable?
guard allowed?
refutable?
ownership mode?
```

---

# 171. Pattern ownership is not syntax sugar only

Đây là nơi Axiom khác đáng kể so với một parser đơn giản.

Pattern là semantic operation trên Place graph.

---

# 172. Pattern → Place operations

Ví dụ:

```axiom
Point { x, y }
```

có thể lower thành conceptual:

```text
x ← Move p.x
y ← Move p.y
```

hoặc:

```text
x ← Copy p.x
y ← Copy p.y
```

tùy type.

---

# 173. No hidden copies

Compiler không được biến Move thành Copy chỉ để làm code compile.

---

# 174. No hidden clone

Compiler không gọi Clone để satisfy pattern.

---

# 175. Capability decomposition

Với:

```text
view<Point>
```

pattern có thể produce:

```text
view<i32>(p.x)
view<i32>(p.y)
```

nếu provenance và regions hợp lệ.

---

# 176. Mutable decomposition

Với:

```text
mut_view<Point>
```

có thể produce:

```text
mut_view<i32>(p.x)
mut_view<i32>(p.y)
```

nếu compiler chứng minh fields disjoint.

---

# 177. Unknown overlap

Nếu type/layout abstraction không chứng minh field disjoint:

→ conservative reject mutable simultaneous capabilities.

---

# 178. Pattern and logical identity

Destructuring không tạo Logical Identity mới.

Binding chỉ tham chiếu/own semantic component.

---

# 179. Pattern and physical layout

Compiler không được giả định:

```text
field x = byte offset 0
```

trừ khi layout contract yêu cầu.

---

# 180. Pattern and repr(C)

`@repr(C)` có thể làm field layout predictable cho FFI/system, nhưng pattern semantics vẫn dựa trên field identity.

---

# 181. Pattern and packed structs

`@repr(packed)` field access có alignment implications.

Pattern accessing packed fields có thể yêu cầu unsafe/system semantics tùy target/operation.

---

# 182. Pattern and uninitialized memory

Không được pattern-match một field chưa initialized.

---

# 183. Pattern and invalid enum discriminant

Safe code không thể có invalid enum discriminant.

Nếu unsafe constructs foreign/invalid memory:

→ validation contract required before safe pattern matching.

---

# 184. Pattern and raw bytes

`bitcast`/reinterpretation không tự tạo valid enum.

`Uninit`/raw memory phải được initialized and validated before semantic enum use.

---

# 185. Pattern verification boundary

```text
Pattern
 ↓
Typed Pattern
 ↓
Pattern Facts
 ↓
Ownership/Capability Verification
 ↓
Verified MIR
```

---

# 186. Pattern optimization boundary

Chỉ sau Verified MIR:

```text
Decision tree
jump table
branch elimination
range simplification
tag elimination
```

---

# 187. Pattern semantic oracle

Reference interpreter phải execute match theo:

```text
scrutinee once
arm order
pattern semantics
guard order
binding ownership
drop cleanup
```

---

# 188. Differential testing

Test:

```text
reference interpreter
vs
MIR interpreter
vs
optimized native
```

---

# 189. Metamorphic tests

Ví dụ có thể kiểm tra semantic-equivalent rewrites:

```text
match x {
    A => f()
    B => f()
}
```

vs equivalent normalized decision tree.

---

# 190. Adversarial ownership tests

Bắt buộc:

```text
partial move
nested move
move + copy
move + view
multiple view
multiple mut_view
Drop after partial move
panic after partial move
return after partial move
```

---

# 191. Exhaustiveness test suite

Bắt buộc:

```text
bool
Option
Result
nested enum
nested tuple
struct
integer ranges
overlapping ranges
OR-patterns
guards
wildcard
unreachable arms
generic enums
```

---

# 192. Fuzz pattern compiler

Fuzzer tạo:

```text
random nested patterns
random constructors
random ranges
random OR-patterns
random guards
```

sau đó so sánh:

```text
exhaustiveness result
reference evaluator
```

---

# 193. Pattern compiler correctness

Pattern lowering phải preserve:

```text
selected arm
binding values
ownership state
capability state
effects
drop behavior
```

---

# 194. Formal model

Formal semantics có thể định nghĩa:

```text
⟨P, V, Σ⟩ → MatchResult
```

trong đó:

```text
P = pattern
V = scrutinee value/state
Σ = semantic environment
```

---

# 195. Match result

Conceptual:

```text
Match
├── Fail
└── Success {
      bindings
      refinements
      ownership transitions
      capability transitions
   }
```

---

# 196. Guard semantics

```text
PatternSuccess
   ↓
Bind
   ↓
EvaluateGuard
   ├── false → next arm
   └── true  → arm body
```

---

# 197. Failed pattern does not leak ownership

Pattern testing không được Move resource rồi sau đó fail và để ownership state sai.

Compiler phải model pattern tests như:

```text
non-consuming inspection
```

cho đến khi arm được selected, trừ semantics explicitly requiring consuming operation.

---

# 198. Binding only after selection

Đây là rule quan trọng:

> **Pattern testing và binding ownership transition là hai phase semantic khác nhau.**

---

# 199. Pattern test may inspect

Tag/range/field tests có thể đọc value.

Read capability conflict rules vẫn áp dụng.

---

# 200. FROZEN INVARIANTS

```text
APATTERN-20
Match is an expression.

APATTERN-21
The scrutinee is evaluated exactly once.

APATTERN-22
Scrutinee evaluation precedes pattern selection.

APATTERN-23
Pattern evaluation order is deterministic.

APATTERN-24
Only the selected arm body is evaluated.

APATTERN-25
Pattern matching does not implicitly clone values.

APATTERN-26
Pattern matching does not implicitly allocate.

APATTERN-27
Pattern semantics are independent of physical representation.

APATTERN-28
Pattern matching uses the ordinary Axiom ownership model.

APATTERN-29
Pattern matching uses the ordinary Axiom capability model.

APATTERN-30
Pattern decomposition operates on semantic places.

APATTERN-31
Struct fields are resolved by field identity.

APATTERN-32
Tuple components are resolved positionally.

APATTERN-33
Enum constructors are resolved by declaration identity.

APATTERN-34
Enum pattern matching is exhaustive over the known closed constructor set.

APATTERN-35
Non-exhaustive matches are rejected in Complete Semantic Mode.

APATTERN-36
A wildcard covers all remaining values allowed by its type.

APATTERN-37
Unreachable patterns are diagnosed.

APATTERN-38
An earlier matching arm takes precedence over later overlapping arms.

APATTERN-39
A guard does not contribute to exhaustiveness coverage.

APATTERN-40
A guard is evaluated only after its pattern matches.

APATTERN-41
Guard evaluation follows ordinary expression effect semantics.

APATTERN-42
OR-pattern alternatives must produce compatible binding environments.

APATTERN-43
OR-pattern alternatives must agree on binding types.

APATTERN-44
OR-pattern alternatives must agree on binding ownership modes.

APATTERN-45
OR-pattern alternatives must agree on capability modes.

APATTERN-46
Literal patterns use defined type-specific equality semantics.

APATTERN-47
Integer range patterns use defined integer domain semantics.

APATTERN-48
Range pattern bounds must be semantically valid and representable.

APATTERN-49
Range analysis must not rely on overflowing arithmetic.

APATTERN-50
Floating-point exhaustiveness must account for NaN and signed-zero semantics.

APATTERN-51
Core v1 does not require arbitrary user-defined pattern semantics.

APATTERN-52
Pattern constructors are compiler-resolvable semantic constructors.

APATTERN-53
Struct destructuring may be partial.

APATTERN-54
Partial destructuring preserves ownership state of unbound fields.

APATTERN-55
Partial moves are tracked at place granularity.

APATTERN-56
Moved fields are never dropped again.

APATTERN-57
Remaining initialized fields remain independently usable when legal.

APATTERN-58
Custom Drop restricts partial moves according to the Drop contract.

APATTERN-59
Compiler-derived Drop may support field-sensitive partial moves.

APATTERN-60
Pattern bindings follow Copy/Move semantics without implicit Clone.

APATTERN-61
Copy bindings do not create shared mutable aliases.

APATTERN-62
Move bindings consume their source place.

APATTERN-63
View bindings do not acquire ownership of the underlying storage.

APATTERN-64
MutView bindings remain exclusive capabilities.

APATTERN-65
Multiple mutable pattern capabilities require proven disjointness.

APATTERN-66
Unknown overlap is never treated as disjoint.

APATTERN-67
Pattern-created views cannot outlive their provenance.

APATTERN-68
Pattern-created capabilities cannot outlive their owner.

APATTERN-69
Pattern matching cannot read uninitialized data.

APATTERN-70
Pattern matching cannot consume an already moved place.

APATTERN-71
Pattern matching cannot create duplicate ownership.

APATTERN-72
Pattern matching cannot create duplicate mutable capability.

APATTERN-73
Failed pattern tests do not cause observable ownership transfer.

APATTERN-74
Binding ownership transitions occur only for the selected successful match.

APATTERN-75
Pattern matching preserves deterministic Drop semantics.

APATTERN-76
Every match arm has an independent semantic scope.

APATTERN-77
Arm-local bindings do not escape their arm unless explicitly returned/transferred.

APATTERN-78
Return, break, continue, ?, and panic from an arm perform required cleanup.

APATTERN-79
Match joins require valid ownership state at CFG merge points.

APATTERN-80
A potentially moved value cannot be used after the match unless reinitialized or otherwise proven valid.

APATTERN-81
Irrefutable patterns are required in irrefutable contexts.

APATTERN-82
Refutable patterns are permitted in refutable matching contexts.

APATTERN-83
Pattern typing precedes exhaustiveness analysis.

APATTERN-84
Type normalization precedes dependent pattern analysis.

APATTERN-85
Generic pattern matching uses substituted concrete semantic types.

APATTERN-86
Generic specialization cannot alter pattern semantics.

APATTERN-87
Pattern matching on dyn Trait does not provide closed-world exhaustiveness.

APATTERN-88
Dynamic downcasting requires an explicit runtime mechanism.

APATTERN-89
FFI enum exhaustiveness requires an explicit foreign-domain contract.

APATTERN-90
Invalid foreign enum values cannot be silently treated as valid Axiom variants.

APATTERN-91
Niche optimization cannot alter pattern semantics.

APATTERN-92
Physical enum tag layout is not part of pattern semantics unless explicitly exposed.

APATTERN-93
Pattern lowering may use direct place access.

APATTERN-94
Pattern lowering need not materialize intermediate copies.

APATTERN-95
Pattern decision trees may be optimized after semantic verification.

APATTERN-96
Jump tables, branch trees, and binary searches are implementation choices.

APATTERN-97
Optimization cannot change selected-arm semantics.

APATTERN-98
Optimization cannot reorder observable guard effects.

APATTERN-99
Pattern facts feed range, branch, alias, ownership, and capability analysis.

APATTERN-100
Pattern analysis must not bypass the ownership/capability verifier.

APATTERN-101
Pattern analysis must not treat unknown information as proof.

APATTERN-102
Exhaustiveness failure due to compiler resource limits is not equivalent to exhaustive proof.

APATTERN-103
Pattern analysis must be deterministic.

APATTERN-104
Pattern compilation may execute incrementally and in parallel.

APATTERN-105
Parallel pattern compilation must produce deterministic semantic results.

APATTERN-106
Pattern diagnostics retain source provenance.

APATTERN-107
Pattern diagnostics distinguish non-exhaustiveness from unreachable arms.

APATTERN-108
Pattern diagnostics can expose binding ownership transitions.

APATTERN-109
Pattern diagnostics can expose capability transitions.

APATTERN-110
Pattern diagnostics can expose uncovered constructor/range space.

APATTERN-111
Pattern lowering preserves source-to-machine debug mapping.

APATTERN-112
Pattern matching uses the same semantic engine across match, destructuring, iteration, and closure parameters where applicable.

APATTERN-113
Context-specific legality is separated from common Pattern representation.

APATTERN-114
Comptime pattern matching uses the same core pattern semantics.

APATTERN-115
GPU pattern matching obeys GPU legality rules.

APATTERN-116
Async pattern bindings obey ordinary suspension and ownership rules.

APATTERN-117
Send requirements for pattern bindings are preserved across async suspension.

APATTERN-118
Unsafe pattern operations do not disable unrelated semantic verification.

APATTERN-119
Reference and MIR interpreters must agree on pattern semantics.

APATTERN-120
Optimized native execution must preserve reference pattern semantics.
```

---

# Kiến trúc Pattern Engine hoàn chỉnh

```text
                         PATTERN SOURCE
                               │
                               ▼
                         Pattern AST
                               │
                               ▼
                         Pattern HIR
                               │
                    ┌──────────┴──────────┐
                    ▼                     ▼
              Pattern Typing        Name Resolution
                    │                     │
                    └──────────┬──────────┘
                               ▼
                       Typed Pattern
                               │
                               ▼
                     Pattern Matrix
                      /            \
                     ▼              ▼
              Exhaustiveness     Usefulness
                     │              │
                     └──────┬───────┘
                            ▼
                      Pattern Facts
                            │
              ┌─────────────┼─────────────┐
              ▼             ▼             ▼
          Ownership     Capability      Type Refinement
              │             │             │
              └─────────────┼─────────────┘
                            ▼
                         MIR CFG
                            │
                            ▼
                      Verified MIR
                            │
                            ▼
                    Decision Tree Opt
                            │
                            ▼
                    Target Codegen
```

Điểm tôi muốn giữ rất chắc ở đây là **Pattern Engine không được biến thành một “mini type system thứ hai”**. Nó chỉ tạo ra các facts; Type System, Ownership Verifier, Capability Verifier và Optimizer vẫn giữ trách nhiệm riêng.

---

## Chuỗi kiến trúc tiếp theo

### **BOOTSTRAP-249 — AXIOM EFFECT SYSTEM & EFFECT INFERENCE**

Đây là bước tiếp theo rất quan trọng.

Chúng ta sẽ formalize:

```text
pure
read
write
allocate
deallocate
drop
panic
IO
volatile
atomic
synchronize
blocking
async
foreign
GPU
process
filesystem
network
comptime
unsafe
```

và quan trọng hơn:

> **Effect phải vừa đủ mạnh để compiler biết điều gì không được reorder/eliminate, nhưng không biến Axiom thành một ngôn ngữ mà programmer phải viết hàng đống effect annotation.**

Nó sẽ nối trực tiếp:

```text
Expression
→ Function
→ Generic
→ Trait
→ MIR
→ Optimizer
→ Async
→ Concurrency
→ FFI
→ GPU
```

và quyết định rất nhiều khả năng **aggressive optimization mà vẫn giữ đúng semantics**.