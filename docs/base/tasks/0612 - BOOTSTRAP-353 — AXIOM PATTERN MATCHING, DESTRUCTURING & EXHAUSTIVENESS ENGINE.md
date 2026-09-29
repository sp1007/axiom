# BOOTSTRAP-353 — AXIOM PATTERN MATCHING, DESTRUCTURING & EXHAUSTIVENESS ENGINE

Sau generic/trait solver, bước tiếp theo nên khóa **pattern system**. Đây là phần kết nối trực tiếp giữa `enum`, `Option`, `Result`, struct, tuple, array, ownership, move analysis và control-flow.

Mục tiêu:

> **Pattern matching phải mạnh như một algebraic pattern system hiện đại, nhưng compiler phải biến nó thành CFG/machine code rất đơn giản và không tạo abstraction/runtime overhead không cần thiết.**

---

## 1. Pattern là compile-time structure

Pattern không phải runtime object.

Ví dụ:

```text
match value {
    Some(x) => x,
    None => 0,
}
```

Compiler biến thành:

```text
discriminant test
    ↓
branch
    ↓
bind value
```

Không tồn tại một “Pattern runtime”.

---

# 2. Pattern categories

Core hỗ trợ:

```text
Wildcard
Binding
Literal
Tuple
Struct
Enum
Array
Slice/View
Range
Or-pattern
Reference/View
Guard
```

Ví dụ:

```text
_
x
42
(a, b)
Point { x, y }
Some(x)
[a, b, c]
[head, ..tail]
1..10
A | B
pattern if condition
```

---

# 3. Binding pattern

```text
match x {
    value => ...
}
```

`value` là binding.

Binding mặc định obey ownership semantics.

Ví dụ nếu `x` là non-Copy owning value:

```text
match x {
    value => consume(value)
}
```

thì compiler phải xác định `x` đã bị move.

---

# 4. Match không được tạo copy ngầm

Ví dụ:

```text
struct Big {
    data: Buffer
}

match big {
    Big { data } => use(data)
}
```

Compiler không được tạo:

```text
Big copy
Buffer copy
```

chỉ để destructure.

Destructuring là semantic projection/move/capability operation.

---

# 5. Partial move

Nếu:

```text
struct User {
    id: u64
    name: String
}
```

và:

```text
match user {
    User { name, .. } => consume(name)
}
```

compiler có thể đánh dấu:

```text
user.name = MOVED
```

nhưng:

```text
user.id
```

vẫn có thể hợp lệ nếu ownership rules cho phép.

Đây phải tích hợp trực tiếp với Place Tree của ownership verifier.

---

# 6. Custom Drop

Với type có user-defined destructive Drop:

```text
struct Resource { ... }

impl Drop for Resource { ... }
```

partial move phải bị hạn chế theo memory model đã frozen.

Ví dụ destructuring một field owning có thể không được phép nếu làm `Drop` invariant không còn đúng.

Compiler phải phát hiện trước codegen.

---

# 7. Struct pattern

```text
match p {
    Point { x, y } => ...
}
```

Có thể:

```text
Point {
    x,
    y: yy,
}
```

và:

```text
Point {
    x,
    ..
}
```

`..` nghĩa là bỏ qua các field còn lại.

---

# 8. Tuple pattern

```text
match pair {
    (a, b) => ...
}
```

Không cần tạo tuple temporary.

Compiler trực tiếp map pattern:

```text
pair.field0
pair.field1
```

---

# 9. Enum pattern

Với:

```text
enum Result<T, E> {
    Ok(T),
    Err(E),
}
```

pattern:

```text
Ok(value)
Err(error)
```

compiler kiểm tra discriminant.

Không yêu cầu object header.

---

# 10. Nested pattern

Cho phép:

```text
match result {
    Ok(Some(x)) => ...
    Ok(None) => ...
    Err(e) => ...
}
```

Compiler tạo decision tree tối ưu.

Không nhất thiết nested match phải sinh nested branch đúng như source.

---

# 11. Or-pattern

Ví dụ:

```text
match x {
    0 | 1 | 2 => small(),
    _ => large(),
}
```

Các alternative phải bind **cùng tập biến với type tương thích**.

Ví dụ không hợp lệ:

```text
A(x) | B(y) => ...
```

nếu `x` và `y` không tạo cùng binding environment.

---

# 12. Literal pattern

Hỗ trợ:

```text
0
1
-1
true
false
'A'
"literal"
```

với semantics tương ứng.

String pattern không được mặc định biến thành arbitrary substring matching.

Literal text pattern là exact value/pattern operation.

---

# 13. Range pattern

Ví dụ:

```text
match x {
    0..10 => ...
    10..100 => ...
    _ => ...
}
```

Cần định nghĩa rõ:

```text
0..10
```

là:

```text
[0, 10)
```

và nếu cần inclusive:

```text
0..=10
```

Range bounds phải cùng domain hoặc được resolve qua explicit conversion.

---

# 14. Exhaustiveness

Đây là chức năng compiler bắt buộc.

Ví dụ:

```text
enum Color {
    Red,
    Green,
    Blue,
}

match c {
    Red => ...
    Green => ...
}
```

→ compile error vì `Blue` chưa được xử lý.

Không dựa vào runtime default branch.

---

# 15. Exhaustiveness algorithm

Compiler xây:

```text
PatternMatrix
```

và thực hiện coverage analysis.

Conceptually:

```text
Patterns
    ↓
Constructor Decomposition
    ↓
Specialization
    ↓
Uncovered Pattern Search
    ↓
Exhaustive / NonExhaustive
```

Có thể sử dụng algorithm kiểu Maranget nhưng implementation phải phù hợp với Axiom type/ownership model.

---

# 16. Uncovered-pattern diagnostic

Thay vì:

```text
non-exhaustive match
```

compiler nên chỉ ra:

```text
missing case:
    Some(None)
```

hoặc:

```text
missing enum constructor:
    Color::Blue
```

Structured diagnostic chứa:

```text
MissingPattern
PatternPath
Constructor
SourceSpan
```

AI tooling có thể tự động sửa.

---

# 17. Unreachable pattern

Ví dụ:

```text
match x {
    _ => foo(),
    10 => bar(),
}
```

`10` unreachable.

Compiler báo:

```text
unreachable pattern
```

Không được âm thầm bỏ pattern rồi làm programmer tưởng nó hoạt động.

---

# 18. Pattern priority

Pattern được xét theo source order khi semantics yêu cầu.

Ví dụ:

```text
match x {
    0 => a(),
    _ => b(),
}
```

`_` không được compiler đổi lên trước.

Nhưng sau khi chứng minh equivalence, compiler có thể optimize decision tree.

---

# 19. Guards

Ví dụ:

```text
match x {
    n if n > 10 => large(),
    n => normal(),
}
```

Guard không nên được coi là constructor coverage hoàn toàn.

Vì:

```text
n > 10
```

có thể là runtime predicate.

Do đó:

> Guard không tự động đóng góp đầy đủ vào exhaustiveness proof.

Ví dụ:

```text
match x {
    n if n > 0 => positive(),
}
```

vẫn thiếu trường hợp khác.

---

# 20. Guard binding semantics

Binding trong guard phải giữ capability hợp lệ.

Ví dụ:

```text
match buffer {
    b if b.len() > 0 => ...
}
```

Nếu `b` là owning move, compiler không được cho phép guard tạo alias ngoài ownership rules.

---

# 21. `Option`

Pattern:

```text
Some(x)
None
```

phải được compiler tối ưu rất mạnh.

Ví dụ:

```text
Option<Box<T>>
```

có thể dùng niche representation.

Không cần:

```text
tag + object
```

nếu representation có thể encode `None` bằng niche.

---

# 22. `Result`

Pattern:

```text
Ok(v)
Err(e)
```

là core control-flow primitive quan trọng.

Syntax:

```text
match result {
    Ok(v) => ...
    Err(e) => ...
}
```

và:

```text
result?
```

phải lower về cùng semantic model.

---

# 23. `?` operator

`?` không phải exception.

Ví dụ:

```text
let x = read()?;
```

semantic:

```text
match read() {
    Ok(v) => v,
    Err(e) => return Err(e),
}
```

Compiler có thể lower trực tiếp thành branch.

---

# 24. Pattern + capability

Đây là điểm đặc biệt quan trọng của Axiom.

Ví dụ:

```text
match value {
    Some(x) => ...
}
```

compiler phải xác định `x` là:

```text
Move
Copy
view
mut_view
```

tùy pattern/context.

Pattern matching không được trở thành loophole để tạo nhiều aliases.

---

# 25. `view` pattern

Cho phép destructuring read-only view:

```text
match view(point) {
    Point { x, y } => ...
}
```

`x`, `y` phải là read capabilities hoặc copied values tùy type.

Không được move từ một view.

---

# 26. `mut_view` pattern

Với:

```text
mut_view<Point>
```

pattern có thể tạo mutable field capabilities:

```text
Point {
    x,
    y,
}
```

nhưng compiler phải đảm bảo:

```text
x
```

và:

```text
y
```

không tạo conflict ngoài region rules.

Disjoint fields có thể được sử dụng đồng thời.

---

# 27. Array patterns

Fixed array:

```text
let a: [i32; 4]

match a {
    [a, b, c, d] => ...
}
```

Compiler biết số phần tử compile time.

Không cần bounds check trong destructuring.

---

# 28. Slice/view patterns

Ví dụ:

```text
match xs {
    [] => ...
    [x] => ...
    [first, ..rest] => ...
}
```

`rest` phải là view/capability, không phải implicit copy.

Ví dụ:

```text
[head, ..tail]
```

có thể semantic:

```text
head = xs[0]
tail = xs[1..]
```

với lifetime gắn với `xs`.

---

# 29. Mutable slice pattern

```text
match xs {
    [head, ..tail] => {
        modify(head)
        modify(tail)
    }
}
```

Compiler phải prove `head` và `tail` disjoint.

Đây là một use case rất tốt cho region analysis đã frozen.

---

# 30. String pattern

Không đưa full regex vào pattern system.

Core chỉ cần:

```text
"text literal"
```

và text structural operations.

Regex:

```text
regex(...)
```

là library.

Tránh biến pattern compiler thành regex engine.

---

# 31. Binding modifiers

Axiom nên giữ syntax đơn giản.

Không cần:

```text
ref
ref mut
&
&
mut
```

như nhiều ngôn ngữ.

Compiler suy luận binding mode từ expected ownership/access context.

Khi cần explicit semantic:

```text
view(x)
mut_view(x)
```

đã có primitive rõ ràng.

---

# 32. Pattern type checking

Mỗi pattern có expected type:

```text
PatternCheck(
    pattern,
    expected_type,
    capability_context
)
```

Kết quả:

```text
PatternBindingEnvironment
CoverageConstructor
MoveSet
CapabilitySet
```

Không để pattern checker tự tạo một ownership model riêng.

---

# 33. Pattern lowering

Ví dụ:

```text
match value {
    Some(x) => f(x),
    None => g(),
}
```

lower:

```text
match discriminant(value) {
    Some => {
        let x = project(value.payload)
        f(x)
    }

    None => {
        g()
    }
}
```

sau đó MIR CFG:

```text
        entry
          │
     discriminant
       /       \
    Some       None
      │          │
   project       g
      │          │
      f──────────┘
```

---

# 34. Decision tree optimization

Compiler có thể reorder **tests**, không reorder observable side effects.

Pattern tests thuần:

```text
discriminant
integer compare
range compare
bit test
```

có thể được tối ưu thành:

```text
jump table
binary search
decision tree
bitmask
lookup table
branchless select
```

tùy target.

---

# 35. Jump table

Ví dụ:

```text
match opcode {
    0 => f0(),
    1 => f1(),
    2 => f2(),
    3 => f3(),
    ...
}
```

compiler có thể generate:

```text
jump_table[index]
```

thay vì chuỗi branch.

---

# 36. Branchless match

Ví dụ numeric pattern đơn giản:

```text
match x {
    0 => 0,
    1 => 1,
    _ => 2,
}
```

có thể lower thành arithmetic/select.

Không cần preserve source branching structure.

---

# 37. Pattern + const generics

Ví dụ:

```text
match array {
    [a, b, c, d] => ...
}
```

với:

```text
Array<T, 4>
```

compiler có compile-time shape information.

Với:

```text
Array<T, N>
```

có thể sử dụng const constraints khi cần.

---

# 38. Pattern + generics

Một pattern:

```text
Some(x)
```

có thể kiểm tra với:

```text
Option<T>
```

mà không cần biết `T` concrete.

Pattern coverage trên generic enum vẫn phải chính xác.

---

# 39. Pattern + traits

Pattern không nên gọi arbitrary trait method để quyết định constructor.

Ví dụ:

```text
match x {
    pattern => ...
}
```

không được ngầm gọi:

```text
PartialEq
Hash
Compare
```

trừ khi syntax explicitly yêu cầu.

Điều này giữ pattern matching:

> structural và predictable.

---

# 40. Custom pattern matching

Không đưa procedural pattern/macro system vào Core v1.

Sau này có thể có typed compile-time extension.

Nhưng pattern semantics cơ bản phải do compiler kiểm soát để đảm bảo:

- exhaustiveness;
- ownership;
- capability;
- optimization;
- diagnostics.

---

# 41. Pattern diagnostics

Compiler phải có structured diagnostics:

```text
NonExhaustiveMatch
UnreachablePattern
InvalidPattern
BindingMismatch
MoveInPattern
BorrowConflictInPattern
GuardNotExhaustive
PatternTypeMismatch
```

Ví dụ AI tooling nhận:

```text
Missing:
    Result::Err(_)
```

có thể tự động đề xuất branch.

---

# 42. CompilerDB additions

```text
PatternDB
PatternTypeDB
PatternBindingDB
PatternMatrixDB
PatternCoverageDB
PatternDecisionTreeDB
PatternLoweringDB
ExhaustivenessDB
UnreachablePatternDB
GuardDB
DestructureDB
MatchOptimizationDB
PatternDiagnosticDB
```

---

# 43. MIR additions

MIR cần hỗ trợ trực tiếp:

```text
SWITCH_INT
SWITCH_ENUM
SWITCH_RANGE
SWITCH_BOOL
PROJECT_FIELD
PROJECT_INDEX
PROJECT_VARIANT
SLICE_PROJECT
BIND
```

Sau optimization chúng có thể được hạ xuống CFG thông thường.

---

# 44. Ownership integration

Pattern checker phải xuất:

```text
PatternMoveSet
PatternCopySet
PatternBorrowSet
PatternDropSet
```

Ví dụ:

```text
match x {
    Struct { field } => consume(field)
}
```

produces:

```text
MoveSet = { x.field }
```

Ownership verifier tiếp tục xử lý.

---

# 45. Exhaustiveness + ownership

Coverage checking và ownership checking là hai vấn đề khác nhau.

Không được trộn:

```text
PatternCoverage
```

với:

```text
OwnershipState
```

Một match có thể:

```text
exhaustive = true
ownership = invalid
```

hoặc:

```text
exhaustive = false
ownership = valid
```

Compiler phải report đúng nguyên nhân.

---

# 46. Invariants

```text
APAT-01
Pattern matching is compile-time structural semantics.

APAT-02
Pattern matching does not require runtime pattern objects.

APAT-03
All match expressions are exhaustiveness checked.

APAT-04
Exhaustiveness is type-aware.

APAT-05
Guards do not automatically establish exhaustiveness.

APAT-06
Unreachable patterns are diagnosed.

APAT-07
Pattern order is semantically significant where patterns overlap.

APAT-08
Compiler may optimize pattern decision trees when semantics are preserved.

APAT-09
Destructuring does not imply hidden copies.

APAT-10
Pattern bindings obey ownership semantics.

APAT-11
Pattern matching can move individual fields when permitted.

APAT-12
Custom Drop restrictions apply to destructuring.

APAT-13
Patterns cannot create invalid aliases.

APAT-14
View patterns cannot move from non-owning capabilities.

APAT-15
Mutable view patterns obey region disjointness.

APAT-16
Slice rest bindings preserve provenance and lifetime.

APAT-17
Fixed-size array patterns use compile-time shape information.

APAT-18
Enum patterns use semantic discriminants, not mandatory object headers.

APAT-19
Option/Result patterns must permit zero-cost representation.

APAT-20
Pattern matching does not implicitly invoke arbitrary user-defined comparison.

APAT-21
Pattern coverage is distinct from ownership verification.

APAT-22
Pattern type checking is deterministic.

APAT-23
Or-patterns require compatible binding environments.

APAT-24
Range semantics are explicit.

APAT-25
Never-returning branches participate in coverage/CFG reasoning.

APAT-26
Pattern lowering produces ordinary verified control flow.

APAT-27
Pattern optimization cannot change observable evaluation order.

APAT-28
Pattern diagnostics are structured.

APAT-29
Pattern semantics are independent of optimization level.

APAT-30
All pattern-generated MIR must pass normal verification before optimization.
```

---

# 47. Definition of Done

`BOOTSTRAP-353` hoàn thành khi compiler có:

- literal patterns;
- wildcard/binding;
- tuple patterns;
- struct patterns;
- enum patterns;
- nested patterns;
- or-patterns;
- range patterns;
- array patterns;
- slice/view patterns;
- guards;
- exhaustive match;
- unreachable-pattern detection;
- partial move;
- ownership-aware destructuring;
- capability-aware destructuring;
- generic pattern checking;
- const-generic patterns;
- `Option`/`Result` optimization;
- decision-tree generation;
- jump-table generation;
- branchless pattern optimization;
- pattern MIR;
- structured diagnostics;
- conformance/fuzz tests cho coverage + ownership interaction.

### Điểm kiến trúc quan trọng

Sau task này, một đoạn như:

```text
match packet {
    Header { kind: Request, payload } => handle(payload),
    Header { kind: Response, payload } => respond(payload),
    _ => ignore(),
}
```

không cần runtime reflection, object hierarchy, RTTI hay dynamic dispatch.

Compiler có thể biến trực tiếp thành:

```text
load discriminant
→ compare
→ branch/jump-table
→ project payload
→ ownership/capability verification
→ native code
```

Đây là một trong những cơ chế giúp Axiom vừa **biểu đạt rất cao ở source level**, vừa giữ được mục tiêu **native performance và binary nhỏ**.