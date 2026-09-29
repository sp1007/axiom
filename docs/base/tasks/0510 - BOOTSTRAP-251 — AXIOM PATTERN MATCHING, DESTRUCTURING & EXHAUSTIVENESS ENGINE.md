# BOOTSTRAP-251 — AXIOM PATTERN MATCHING, DESTRUCTURING & EXHAUSTIVENESS ENGINE

**TRẠNG THÁI: FROZEN / COMPLETED**

Mục tiêu:

> `match` phải mạnh như pattern matching hiện đại, nhưng không tạo ra một ownership model thứ hai.

Pattern chỉ là **cách quan sát và phân rã value/place**. Mọi Move, Copy, View, Drop, capability và lifetime đều dùng semantic model đã frozen trước đó.

---

# 1. Pattern là semantic projection

Pattern không trực tiếp thao tác memory.

Ví dụ:

```axiom
match value {
    Some(x) => use(x)
    None => ...
}
```

Compiler hiểu:

```text
scrutinee
    ↓
pattern decomposition
    ↓
place projections
    ↓
bindings
    ↓
guard
    ↓
selected arm
```

---

# 2. Các loại pattern Core v1

Axiom hỗ trợ:

```text
Wildcard
Binding
Literal
Tuple
Struct
Enum
Array
Slice
Range
Or
Reference/View capability pattern
```

Không cần pattern macro language.

---

# 3. Wildcard

```axiom
match x {
    _ => ...
}
```

Không tạo binding.

---

# 4. Binding

```axiom
match x {
    value => use(value)
}
```

Binding mặc định tuân theo ownership semantics của value.

Compiler xác định đây là:

```text
Copy
hoặc
Move
```

dựa trên type và usage.

---

# 5. Không implicit clone

Nếu:

```axiom
struct Big {
    data: Vec<u8>
}
```

thì pattern không tự clone.

```axiom
match x {
    Big { data } => ...
}
```

`data` có thể trở thành partial move.

---

# 6. Partial move

Ví dụ:

```axiom
struct User {
    id: u64
    name: String
}

match user {
    User { id, name } => ...
}
```

Nếu `id` Copy và `name` Move:

```text
user.id   → Copy
user.name → Move
```

Verifier phải theo dõi field-level state.

---

# 7. Place tree

Pattern compiler sử dụng Place Model:

```text
user
 ├── .id
 └── .name
```

Không cần tạo object trung gian.

---

# 8. Enum pattern

```axiom
match result {
    Ok(value) => ...
    Err(error) => ...
}
```

Pattern binding tương ứng với payload place.

---

# 9. Tuple pattern

```axiom
match point {
    (x, y) => ...
}
```

semantic projection:

```text
point.0
point.1
```

---

# 10. Struct pattern

```axiom
match p {
    Point { x, y } => ...
}
```

Compiler canonicalize thành field projections.

---

# 11. Field shorthand

```axiom
Point { x, y }
```

tương đương semantic:

```text
x = p.x
y = p.y
```

nhưng không nhất thiết tạo physical copies.

---

# 12. Rename

```axiom
Point { x: px, y: py }
```

Binding name khác field name.

---

# 13. Ignoring fields

```axiom
Point { x, .. } => ...
```

Các field không binding không được tự động Move.

Compiler chỉ tạo access cần thiết.

---

# 14. Explicit binding semantics

Pattern binding có thể conceptually có:

```text
bind by value
bind by read view
bind by mutable view
```

Nhưng **không nên thêm cú pháp `ref`/`&` kiểu Rust vào Core v1**.

Compiler có thể suy ra từ expected usage hoặc API pattern semantics.

---

# 15. View pattern

Khi API yêu cầu đọc payload mà không consume:

```axiom
match value {
    Some(x) => inspect(x)
}
```

compiler có thể giữ owner và cung cấp ephemeral read capability nếu semantic context cho phép.

---

# 16. Nhưng pattern không được tạo alias sống lâu hơn owner

Nếu binding trở thành view:

```text
owner
  ↓
view
```

thì capability verifier quản lý lifetime.

---

# 17. Mutable pattern access

Mutable pattern chỉ hợp lệ khi exclusive access được chứng minh.

Ví dụ conceptual:

```text
mut_match x {
    ...
}
```

**không nên thêm keyword này trong Core v1**.

Thay vào đó mutable access xuất hiện khi matching một `mut_view<T>` hoặc context đã có mutable capability.

---

# 18. `match` scrutinee evaluation

Scrutinee được evaluate **một lần**.

```axiom
match expensive() {
    A => ...
    B => ...
}
```

Không gọi `expensive()` lại cho từng arm.

---

# 19. Evaluation order

```text
scrutinee
↓
pattern decision
↓
binding
↓
guard
↓
body
```

---

# 20. Guards

```axiom
match x {
    n if n > 10 => ...
    n => ...
}
```

Guard chỉ được evaluate sau khi pattern match.

---

# 21. Guard không mở rộng pattern coverage

Đây là quy tắc rất quan trọng.

```axiom
match x {
    n if n > 0 => ...
}
```

Không được coi là đã cover toàn bộ integer domain.

---

# 22. Vì sao?

Guard có thể là arbitrary runtime expression.

Compiler không cần theorem prover để quyết định:

```text
n > 0
```

bao phủ domain nào.

---

# 23. Exhaustiveness

Compiler phải chứng minh:

```text
mọi value có thể xuất hiện
```

đều có một arm hợp lệ.

---

# 24. Exhaustiveness của enum

```axiom
enum Color {
    Red
    Green
    Blue
}

match c {
    Red => ...
    Green => ...
    Blue => ...
}
```

Exhaustive.

---

# 25. Missing variant

```axiom
match c {
    Red => ...
}
```

→ compile error.

---

# 26. Wildcard

```axiom
match c {
    Red => ...
    _ => ...
}
```

Exhaustive.

---

# 27. Unreachable arm

```axiom
match c {
    _ => ...
    Red => ...
}
```

`Red` unreachable.

Compiler diagnostic.

---

# 28. Literal patterns

```axiom
match n {
    0 => ...
    1 => ...
    _ => ...
}
```

Compiler hiểu finite covered values.

---

# 29. Boolean

```axiom
match flag {
    true => ...
    false => ...
}
```

Exhaustive.

---

# 30. Integer ranges

```axiom
match n {
    0..=9 => ...
    _ => ...
}
```

Range pattern có semantics rõ ràng.

---

# 31. Half-open range

```axiom
0..10
```

nghĩa:

```text
0 <= x < 10
```

---

# 32. Range overflow

Compiler phải validate range boundaries theo target/type semantics.

Không cho wraparound silently.

---

# 33. Character ranges

Có thể:

```axiom
match c {
    'a'..='z' => ...
    _ => ...
}
```

với Unicode scalar semantics.

---

# 34. String patterns

**Không đưa arbitrary regex/string pattern vào Core v1.**

String matching thuộc library/compile-time generation.

---

# 35. Array patterns

```axiom
match arr {
    [a, b, c, d] => ...
}
```

chỉ match array có đúng length.

---

# 36. Slice patterns

```axiom
match values {
    [first, .., last] => ...
}
```

áp dụng cho view/slice-like sequence.

---

# 37. Rest pattern

```text
..
```

đại diện phần còn lại.

Nó không tự động clone phần còn lại.

---

# 38. Rest binding

```axiom
[first, middle @ .., last]
```

có thể được hỗ trợ nếu grammar/type semantics cần, nhưng representation phải là view hoặc ownership transfer rõ ràng.

---

# 39. Khuyến nghị v1

Cho phép:

```text
[first, .., last]
```

nhưng hạn chế complex rest binding cho đến khi semantics thật sự cần.

Điều này giữ compiler implementation gọn hơn.

---

# 40. Tuple nested patterns

```axiom
match x {
    (Some(a), (b, c)) => ...
    _ => ...
}
```

Compiler tạo recursive pattern tree.

---

# 41. Nested struct

```axiom
Point {
    x: 0
    y: y
}
```

hoặc nested pattern tương ứng.

---

# 42. Pattern AST

Không nên flatten pattern ngay parser.

AST:

```text
Pattern
├── Wildcard
├── Binding
├── Literal
├── Tuple
├── Struct
├── Enum
├── Array
├── Slice
├── Range
└── Or
```

---

# 43. Typed Pattern

Sau type checking:

```text
TypedPattern
```

phải biết:

```text
scrutinee Type
projection Place
binding Type
binding mode
Move/Copy/View
coverage
```

---

# 44. Pattern compiler

Sau semantic validation:

```text
TypedPattern
      ↓
Pattern Matrix
      ↓
Usefulness Analysis
      ↓
Decision Tree
      ↓
MIR CFG
```

---

# 45. Pattern Matrix

Compiler có thể dùng algorithm kiểu pattern matrix để xử lý:

```text
enum
tuple
struct
literal
range
wildcard
```

một cách thống nhất.

---

# 46. Decision tree

Ví dụ:

```axiom
match x {
    Some(0) => A
    Some(n) => B
    None => C
}
```

có thể lower thành conceptually:

```text
switch variant(x)
 ├── Some
 │    └── switch payload
 │         ├── 0 → A
 │         └── otherwise → B
 └── None → C
```

Không cần tạo nested runtime objects.

---

# 47. Optimization

Decision tree có thể tối ưu thành:

```text
jump table
binary search
range check
branch chain
bit test
lookup table
```

tùy target.

---

# 48. Semantics không phụ thuộc decision tree

Source semantics vẫn:

```text
first matching arm
```

Decision tree chỉ là implementation.

---

# 49. OR-pattern

```axiom
match x {
    0 | 1 | 2 => ...
    _ => ...
}
```

---

# 50. OR-pattern bindings

Các alternative phải tạo binding set tương thích.

Sai:

```text
Some(x) | None
```

nếu `x` chỉ tồn tại trong một alternative.

---

# 51. Binding consistency

Nếu:

```text
A(x) | B(x)
```

thì `x` phải có semantic type/capability tương thích ở cả hai branch.

---

# 52. Ownership trong OR-pattern

Compiler không được coi một alternative là Move và alternative khác là Copy nếu binding contract không nhất quán.

Phải canonicalize thành semantics an toàn chung.

---

# 53. Match arm scope

Mỗi arm có scope riêng.

```axiom
match x {
    A(a) => ...
    B(b) => ...
}
```

`a` không tồn tại trong `B`.

---

# 54. Drop trong arm

Nếu arm binding sở hữu value:

```text
arm scope exit
→ deterministic Drop
```

---

# 55. Partial move across arm

Nếu scrutinee bị partial move trong một arm:

compiler phải merge ownership states sau `match`.

Ví dụ:

```text
before:
user = Owned

arm A:
user.name = Moved

arm B:
user = Owned
```

sau merge:

```text
user = PartiallyMoved
```

nếu cả hai path reachable và state khác nhau.

---

# 56. Match expression result

```axiom
let result = match x {
    A => 10
    B => 20
}
```

Mỗi arm phải produce compatible result type.

---

# 57. Ownership merge

Nếu arm trả owner:

```text
A => make_a()
B => make_b()
```

result ownership là unified output.

---

# 58. Drop merge

Compiler phải đảm bảo:

```text
exactly one semantic cleanup
```

cho mỗi ownership path.

---

# 59. Diverging arm

```axiom
match x {
    A => panic("bad")
    B => 42
}
```

`panic` có type `never`.

---

# 60. `never` trong pattern typing

Arm có `never` không yêu cầu unify với ordinary value theo cách thông thường.

---

# 61. `break`/`return` trong arm

```axiom
match x {
    A => return 1
    B => 2
}
```

cleanup của arm và enclosing scopes phải được verifier xử lý.

---

# 62. `?` trong arm

```axiom
match result {
    Ok(x) => x
    Err(e) => return Err(e)
}
```

ownership propagation bình thường.

---

# 63. Pattern + view

Nếu:

```axiom
fn inspect(x: view<User>) { ... }
```

và match owner chỉ đọc:

compiler có thể lower access thành ephemeral capability.

Không tạo copy User.

---

# 64. Pattern + mutable view

Nếu matching:

```text
mut_view<User>
```

bindings mutable phải obey exclusive capability.

---

# 65. Index patterns

Không hỗ trợ arbitrary dynamic index trong pattern:

```text
[x[i]]
```

Core v1 không coi pattern là general computation.

---

# 66. Slice pattern runtime cost

Slice patterns phải define bounds checks.

Compiler có thể eliminate nếu length known.

---

# 67. Array known length

```axiom
[4]i32
```

pattern:

```text
[a,b,c,d]
```

có thể compile thành direct projections.

---

# 68. Dynamic view

```text
view<i32>
```

pattern `[a,b,..]` cần runtime length check.

---

# 69. Pattern matching on references

Không có `&T` safe syntax.

Raw pointer matching là unsafe/system.

---

# 70. Null pointer pattern

Không có trong safe Core.

---

# 71. Option thay thế null

```axiom
match ptr_option {
    Some(p) => ...
    None => ...
}
```

---

# 72. Pattern on newtype

```axiom
struct UserId(u64)
```

có thể destructure theo tuple/newtype representation semantics.

---

# 73. Representation independence

Pattern semantics không được phụ thuộc vào physical layout trừ khi explicit `repr` contract.

---

# 74. Enum niche optimization

Compiler có thể encode:

```text
Option<&T>
```

bằng niche representation.

Pattern semantics vẫn chỉ thấy:

```text
Some
None
```

---

# 75. Exhaustiveness algorithm

Coverage domain conceptually:

```text
Constructors
+
Intervals
+
Tuple products
+
Struct products
```

Compiler tính:

```text
covered
uncovered
useful
redundant
```

---

# 76. Usefulness

Mỗi arm được kiểm tra:

```text
Does this pattern match any value not already covered?
```

Nếu không:

```text
unreachable pattern
```

---

# 77. Guard handling

Guarded arm không hoàn toàn consume coverage domain.

Ví dụ:

```axiom
match x {
    Some(n) if n > 0 => ...
    None => ...
}
```

vẫn thiếu:

```text
Some(n <= 0)
```

---

# 78. Multiple guards

Compiler không cần chứng minh guard relations.

---

# 79. Constant guard

Nếu guard là compile-time known false/true, optimizer/comptime có thể simplify sau semantic analysis.

Nhưng exhaustiveness semantics vẫn phải sound.

---

# 80. Exhaustiveness before optimization

Đây là invariant:

```text
Pattern correctness
→ semantic checking
→ optimization
```

Không được dùng optimizer để “vô tình” chứng minh pattern exhaustive.

---

# 81. Match lowering to MIR

MIR có thể dùng:

```text
SwitchInt
SwitchEnum
SwitchRange
Test
Guard
```

hoặc canonical branch CFG.

---

# 82. Semantic MIR không phụ thuộc backend

MIR không encode:

```text
x86 jump table
ARM branch table
```

---

# 83. Backend optimization

Sau đó target backend quyết định:

```text
branch chain
jump table
CMOV
bit test
lookup
```

---

# 84. Pattern decision cost

Compiler có thể optimize:

```text
common prefix
shared tests
branch probability
range density
```

nếu semantic behavior preserved.

---

# 85. Side effects trong patterns

Pattern itself phải không có arbitrary side effects.

Ví dụ:

```text
pattern = function call
```

không được phép.

---

# 86. Why?

Nếu pattern gọi function:

```text
match x {
    expensive_test() => ...
}
```

thì exhaustive analysis trở nên khó và evaluation order phức tạp.

---

# 87. Guards are where computation belongs

Nếu cần dynamic condition:

```axiom
match x {
    value if predicate(value) => ...
}
```

Pattern structural, guard computational.

---

# 88. Pattern range values

Range endpoints phải là compile-time values.

---

# 89. Pattern constants

```axiom
const MIN = 0
const MAX = 10

match x {
    MIN..=MAX => ...
}
```

Compiler evaluate constants trước pattern analysis.

---

# 90. Type restrictions

Pattern literal phải coercible/compatible với scrutinee type theo conversion rules.

Không dùng arbitrary conversion chains.

---

# 91. Float patterns

Core v1 **không khuyến nghị exhaustive floating-point literal/range pattern semantics** vì:

- NaN;
- signed zero;
- FP equality.

Có thể cho limited equality patterns nhưng exhaustive coverage phải dùng wildcard/structural domain rõ ràng.

---

# 92. NaN

Không được giả định:

```text
x == x
```

với floating point.

---

# 93. Boolean-like enums

Compiler có thể optimize enum/bool patterns thành bit tests.

---

# 94. Pattern and Copy

Nếu binding type `Copy`:

```text
binding = semantic copy
```

không consume owner.

---

# 95. Pattern and Move

Nếu non-Copy owner binding:

```text
binding = Move
```

source place becomes moved.

---

# 96. Pattern and Clone

Pattern never invokes Clone implicitly.

---

# 97. Pattern and Drop

Compiler không được Drop moved binding twice.

---

# 98. Pattern and capability

Nếu binding là view:

```text
binding capability
→ provenance = scrutinee
```

---

# 99. Capability expiration

Khi arm scope kết thúc:

```text
ephemeral capability
→ expired
```

---

# 100. Match result capability

Nếu match trả về view:

```axiom
fn first(x: view<Array>) -> view<Item> {
    match ... {
       ...
    }
}
```

compiler phải chứng minh returned capability provenance valid.

---

# 101. No escaping local arm

Không được:

```text
match temporary {
    ...
    return view(local_inside_arm)
}
```

nếu provenance không outlive return.

---

# 102. Match + async

Pattern bindings sống qua `.await` phải obey async state-machine rules.

---

# 103. Example

```axiom
async fn process(x: Result<Data, Error>) -> Result<(), Error> {
    match x {
        Ok(data) => consume_async(data).await
        Err(e) => Err(e)
    }
}
```

`data` sống qua await → phải được lưu trong Future state nếu cần.

---

# 104. Guards + await

Không cho await trực tiếp trong pattern guard nếu Core v1 muốn giữ guard semantics synchronous.

Đề xuất:

```text
guard = synchronous expression
```

Async computation phải diễn ra trong arm body.

---

# 105. Match + GPU

GPU kernels có thể dùng restricted pattern matching.

Compiler kiểm tra GPU legality.

---

# 106. GPU restriction

Không cho pattern compiler tạo implicit dynamic allocation trong kernel.

---

# 107. Pattern + FFI enum

`extern C` enum representation phải obey ABI contract.

Exhaustiveness chỉ exhaustive nếu ABI domain thực sự closed.

---

# 108. C enum

C enums có thể chứa integer values ngoài named enumerators.

Do đó FFI representation không được tự động coi là Axiom closed enum.

---

# 109. Safe FFI wrapper

Wrapper có thể convert:

```text
C integer
→ validated Axiom enum
```

với `Result`.

---

# 110. Pattern metadata

Typed pattern cần expose cho tooling:

```text
PatternId
covered domain
bindings
ownership effect
capabilities
source span
```

---

# 111. AI diagnostic

Compiler có thể trả:

```text
MATCH-E001
missing pattern
```

và:

```text
MATCH-E002
unreachable pattern
```

---

# 112. Explain exhaustiveness

Ví dụ:

```text
ax explain match
```

có thể nói:

```text
covered:
    None
    Some(n > 0)

not covered:
    Some(n <= 0)
```

Nếu guard không thể chứng minh chính xác, compiler có thể giải thích ở mức structural:

```text
Some(_)
```

chưa covered.

---

# 113. Pattern proof

Verifier không cần theorem prover tổng quát.

Pattern engine chỉ tạo facts:

```text
variant = Some
field type = T
literal constraint = ...
range constraint = ...
```

---

# 114. Ownership proof

Pattern engine output:

```text
BindingPlan
```

ví dụ:

```text
user.name → Move
user.id   → Copy
```

Ownership verifier consume plan.

---

# 115. Capability proof

Tương tự:

```text
field x → READ capability
field y → WRITE capability
```

Capability verifier kiểm tra conflict.

---

# 116. Pattern engine không tự quyết định safety

Nó tạo semantic facts.

Verifier là authority.

---

# 117. Compiler architecture

Thêm:

```text
PatternDB
PatternTypeDB
PatternCoverageDB
PatternBindingDB
PatternDecisionDB
```

vào `CompilerDB`.

---

# 118. Pipeline

```text
AST Pattern
    ↓
Pattern Resolution
    ↓
Typed Pattern
    ↓
Binding Plan
    ↓
Coverage / Usefulness
    ↓
Ownership/Capability Integration
    ↓
Decision Tree
    ↓
MIR CFG
```

---

# 119. Incremental compilation

Thay đổi một arm:

```text
pattern subtree
```

không cần recompile toàn function nếu dependency graph cho phép.

---

# 120. Pattern fingerprints

Compiler có thể cache:

```text
PatternFingerprint
CoverageFingerprint
DecisionTreeFingerprint
```

---

# 121. Determinism

Pattern resolution không phụ thuộc:

```text
hash-map iteration order
parallel scheduling
optimization level
```

---

# 122. Error recovery

Partial syntax:

```axiom
match x {
    Some( =>
}
```

parser tạo recovery node.

Pattern engine không tạo Verified MIR.

---

# 123. Partial Semantic Mode

IDE vẫn có thể biết:

```text
expected enum variants
possible bindings
field names
```

nhưng không coi partial pattern exhaustive.

---

# 124. Pattern completion

IDE/AI có thể đề xuất:

```text
Red
Green
Blue
```

dựa trên TypeDB.

---

# 125. Exhaustiveness suggestion

Compiler có thể cung cấp machine-readable fix:

```text
AddMissingPattern(VariantId)
```

để AI/IDE tự sửa.

---

# 126. Nhưng compiler không auto-change source silently

Repair là tooling action.

---

# 127. Stable diagnostics

Diagnostic code:

```text
AMATCH-E001 MissingPattern
AMATCH-E002 UnreachablePattern
AMATCH-E003 InconsistentBinding
AMATCH-E004 InvalidRange
AMATCH-E005 InvalidPatternType
AMATCH-E006 MoveConflict
AMATCH-E007 CapabilityConflict
AMATCH-E008 PatternGuardRestriction
AMATCH-E009 NonExhaustiveMatch
AMATCH-E010 PatternGenerationCycle
```

---

# 128. Formal semantic rule

Cho:

```text
match e {
    p1 if g1 => e1
    ...
    pn if gn => en
}
```

semantic evaluation:

```text
v = eval(e)

for i = 1..n:
    if match(v, pi):
        establish bindings
        if gi == true:
            eval(ei)
            stop
```

Nhưng `match(v, pi)` là pure structural pattern operation.

---

# 129. Ownership-aware formalization

Pattern matching không nhất thiết consume `v`.

Nó tạo:

```text
BindingPlan(v, p)
```

sau đó semantic ownership operation xác định:

```text
Copy
Move
View
```

---

# 130. Đây là điểm kiến trúc quan trọng

Không nên định nghĩa:

```text
match = hidden move
```

hay:

```text
match = hidden borrow
```

Mà:

> **Pattern matching xác định các places được bind; ownership model xác định binding operation.**

Điều này giữ cho toàn bộ hệ thống nhất quán.

---

# 131. Pattern → Place

Ví dụ:

```axiom
Some(User { id, name })
```

canonicalize:

```text
scrutinee
 └─ variant Some
     └─ payload
         └─ id
         └─ name
```

---

# 132. Pattern → Ownership

Nếu:

```text
id: u64       Copy
name: String  Move
```

BindingPlan:

```text
id   = Copy(place.id)
name = Move(place.name)
```

---

# 133. Pattern → Capability

Nếu contextual read:

```text
id = Read(place.id)
```

Nếu mutable context:

```text
id = Write(place.id)
```

sau khi verifier chứng minh exclusive access.

---

# 134. Pattern → Drop

Sau arm:

```text
Drop remaining owned places
```

theo ownership state.

---

# 135. Pattern → MIR

Ví dụ:

```text
SwitchEnum
    Some → BB_some
    None → BB_none
```

và:

```text
BB_some:
    x = Move(scrutinee.payload)
```

hoặc:

```text
x = Copy(scrutinee.payload)
```

tùy type semantics.

---

# 136. Không tạo temporary nếu không cần

Compiler có thể direct-bind:

```text
register ← payload
```

---

# 137. Register allocation

Pattern semantics không yêu cầu memory object.

Backend có thể:

```text
payload register
→ comparison
→ branch
```

---

# 138. Zero-cost abstraction

Pattern matching phải compile thành machine code tương đương với code branch thủ công khi optimizer có đủ facts.

---

# 139. Pattern optimization example

```axiom
match x {
    0 => 1
    1 => 2
    2 => 3
    _ => 0
}
```

có thể thành jump table hoặc arithmetic transform nếu semantics giữ nguyên.

---

# 140. No optimizer dependency

Ngay cả `-O0` cũng phải đúng semantics.

---

# 141. Final architecture

```text
                  PATTERN ENGINE
                        │
                        ▼
                Typed Pattern
                        │
             ┌──────────┼──────────┐
             ▼          ▼          ▼
         Coverage    Binding     Guard
         Analysis      Plan     Analysis
             │          │          │
             └──────────┼──────────┘
                        ▼
              Ownership/Capability
                     Verifier
                        │
                        ▼
                 Decision Tree
                        │
                        ▼
                      MIR
                        │
                        ▼
                    OptIR
```

---

# 142. Frozen invariants

```text
AMATCH-20
Pattern matching is a structural value decomposition mechanism.

AMATCH-21
Patterns do not constitute a separate ownership system.

AMATCH-22
Pattern bindings are resolved into Places.

AMATCH-23
Ownership semantics determine whether bindings Copy or Move.

AMATCH-24
Pattern matching never implies implicit Clone.

AMATCH-25
Pattern matching never creates hidden shared mutable aliases.

AMATCH-26
Pattern bindings participate in normal capability verification.

AMATCH-27
Pattern-derived views cannot outlive their provenance.

AMATCH-28
Partial moves are field-sensitive.

AMATCH-29
Custom Drop restrictions apply to pattern partial moves.

AMATCH-30
Moved pattern bindings cannot be dropped twice.

AMATCH-31
Scrutinee expressions are evaluated exactly once.

AMATCH-32
Pattern selection is deterministic.

AMATCH-33
Pattern evaluation has no arbitrary user-defined side effects.

AMATCH-34
Guards are evaluated only after structural pattern success.

AMATCH-35
Guards do not automatically establish exhaustiveness coverage.

AMATCH-36
Exhaustiveness is checked before optimization.

AMATCH-37
Unreachable patterns are diagnosed.

AMATCH-38
OR-pattern bindings must be semantically compatible.

AMATCH-39
Range patterns use defined numeric semantics.

AMATCH-40
Range endpoints are compile-time values.

AMATCH-41
Integer range overflow is rejected or explicitly represented, never silently wrapped.

AMATCH-42
Floating-point NaN semantics are not assumed to form an ordinary exhaustive equality domain.

AMATCH-43
Array patterns respect fixed array length.

AMATCH-44
Slice patterns perform required runtime bounds checks.

AMATCH-45
Known-length patterns may eliminate runtime length checks.

AMATCH-46
Rest patterns do not implicitly clone remaining elements.

AMATCH-47
Pattern scopes are lexical and arm-local.

AMATCH-48
Pattern bindings obey ordinary Drop semantics.

AMATCH-49
Pattern-generated cleanup is verified by the ownership verifier.

AMATCH-50
Match expression result types are unified across reachable arms.

AMATCH-51
Diverging arms have type never.

AMATCH-52
Return, break, continue and ? inside arms preserve ordinary cleanup semantics.

AMATCH-53
Returned views from match preserve provenance.

AMATCH-54
Pattern matching cannot produce dangling capabilities.

AMATCH-55
Pattern lowering is independent of target-specific branch instructions.

AMATCH-56
Decision-tree optimization cannot alter matching semantics.

AMATCH-57
Pattern coverage does not depend on optimizer behavior.

AMATCH-58
Pattern resolution is independent of source/import iteration order.

AMATCH-59
Pattern resolution is deterministic under parallel compilation.

AMATCH-60
Pattern coverage analysis is incrementally cacheable.

AMATCH-61
Pattern compiler may lower to switch, branch tree, jump table, range test or equivalent machine structure.

AMATCH-62
Physical representation of enums does not alter pattern semantics.

AMATCH-63
Enum niche optimization is invisible to pattern semantics.

AMATCH-64
C ABI enumerations are not assumed to be closed Axiom enums.

AMATCH-65
FFI enum values require explicit validation before closed-enum pattern semantics.

AMATCH-66
Pattern diagnostics expose missing and unreachable coverage structurally.

AMATCH-67
Partial semantic pattern analysis never produces Verified MIR.

AMATCH-68
AI tooling may consume pattern coverage facts but cannot override them.

AMATCH-69
Pattern bindings are represented by stable compiler semantic IDs.

AMATCH-70
Pattern provenance is preserved into MIR diagnostics.

AMATCH-71
Pattern matching obeys async live-state verification.

AMATCH-72
Pattern matching obeys GPU legality when used in GPU code.

AMATCH-73
Pattern matching obeys FFI safety contracts at foreign boundaries.

AMATCH-74
Pattern generation cannot bypass ownership or capability verification.

AMATCH-75
Pattern matching is a zero-cost abstraction target.

AMATCH-76
Pattern semantics are independent of physical storage placement.

AMATCH-77
Pattern semantics are independent of register allocation.

AMATCH-78
Pattern semantics are independent of optimization level.

AMATCH-79
Every accepted pattern program has a defined semantic execution path.

AMATCH-80
Every exhaustive match has compiler-verven coverage proof.

AMATCH-81
No UNKNOWN coverage fact may be treated as exhaustive.

AMATCH-82
No UNKNOWN alias fact may be treated as disjoint during pattern binding.

AMATCH-83
Pattern ownership state is merged through normal dataflow rules.

AMATCH-84
Pattern capability state is merged through normal capability dataflow rules.

AMATCH-85
Pattern decision trees preserve source arm priority.

AMATCH-86
Pattern guards cannot reorder observable effects.

AMATCH-87
Pattern matching does not implicitly allocate.

AMATCH-88
Pattern matching does not implicitly invoke runtime reflection.

AMATCH-89
Pattern matching does not require a mandatory runtime.

AMATCH-90
Pattern matching is part of the Semantic Oracle.
```

---

## Một kết luận kiến trúc quan trọng

Đến đây Axiom đã có một mô hình khá sạch:

```text
             VALUE
               │
             PLACE
               │
        ┌──────┴──────┐
        │             │
      PATTERN       ACCESS
        │             │
   decomposition   view/mut_view
        │             │
        └──────┬──────┘
               ▼
          OWNERSHIP
               │
          CAPABILITY
               │
           VERIFIER
               │
             MIR
```

Tức là **pattern không tự quản lý memory**. Nó chỉ nói:

> “Tôi muốn lấy phần nào của value.”

Còn compiler đã có sẵn Place/Ownership/Capability Verifier quyết định việc lấy đó là `Copy`, `Move`, `READ`, `WRITE` hay bị từ chối.

Đây chính là cách tránh việc Axiom rơi vào tình trạng mỗi feature (`match`, iterator, async, closure, GPU...) lại phát minh một cơ chế memory safety riêng.

---

# BOOTSTRAP-252 — AXIOM CLOSURES, CAPTURE ANALYSIS & FIRST-CLASS CALLABLES

Task kế tiếp sẽ hoàn thiện một phần rất quan trọng của language:

```text
closures
capture inference
capture by value / move / read / mutable access
closure environment
closure identity
Fn / FnMut / FnOnce-like callable capabilities
function pointer
non-capturing closure → function pointer
closure → dyn callable
closure ownership
closure Drop
closure + async
closure + Send/Share
closure allocation elimination
closure environment layout
closure ABI
generic closure specialization
closure in iterators
closure in comptime
```

Đặc biệt sẽ chốt cách Axiom đạt được **lambda/closure mạnh nhưng không cần object/class/runtime allocation**, và cách compiler có thể biến phần lớn closure thành **ordinary function + hidden environment struct**, sau đó tối ưu environment ra khỏi memory hoàn toàn khi có thể.