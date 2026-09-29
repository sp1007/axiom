# BOOTSTRAP-133 — Pattern Matching, Destructuring & Exhaustiveness

**Trạng thái: FROZEN / COMPLETED**

Pattern trong Axiom không chỉ là cú pháp của `match`. Nó là cơ chế semantic để:

```text
enum
struct
tuple
array
Option
Result
destructuring
ownership
partial move
control flow
```

có thể kết hợp với nhau mà không cần thêm một hệ thống pattern riêng cho từng loại.

Nguyên tắc:

> **Pattern chỉ phân tích cấu trúc giá trị; ownership/capability verifier quyết định cách giá trị đó được lấy ra.**

---

# 1. Pattern không phải expression

Ví dụ:

```ax
match value {
    Some(x) => use(x),
    None => fallback(),
}
```

`Some(x)` là:

```text
Pattern
```

không phải expression tạo `Some`.

---

# 2. Pattern có semantic type

Mỗi pattern được kiểm tra against một scrutinee type:

```text
Pattern
    ↓
Expected Type
    ↓
Pattern Type Checking
```

Ví dụ:

```ax
let x: Option<i32>;

match x {
    Some(v) => ...
    None => ...
}
```

`Some(v)` phải tương thích:

```text
Option<i32>
```

---

# 3. Các pattern Core

Axiom v0.1 hỗ trợ:

```text
Wildcard
Binding
Literal
Tuple
Struct
EnumVariant
Array
Slice/View
Range
OrPattern
```

và pattern nesting.

---

# 4. Wildcard

```ax
match x {
    _ => ...
}
```

`_`:

- không tạo binding;
- không move giá trị;
- không copy giá trị;
- chỉ chứng minh rằng phần còn lại được xử lý.

---

# 5. Binding pattern

```ax
match x {
    Some(value) => ...
}
```

`value` là một local declaration mới.

```text
Pattern
  ↓
Binding
  ↓
LocalId
```

---

# 6. Binding không mặc định là reference

Axiom không dùng mô hình:

```text
ref x
&x
```

làm cơ chế destructuring cơ bản.

Compiler suy ra semantic access mode từ context.

---

# 7. Binding mode

Internal pattern binding có thể có:

```text
MOVE
COPY
READ_VIEW
MUT_VIEW
```

Nhưng đây là **compiler semantic state**, không phải nhất thiết là syntax programmer phải viết.

---

# 8. Ví dụ Move

Nếu:

```ax
struct User {
    name: String,
    id: u64,
}

let user = User { ... };

match user {
    User { name, id } => ...
}
```

Nếu `String` là non-Copy owning value, `name` có thể được move ra.

`id` có thể Copy.

---

# 9. Partial move

Sau:

```ax
let user = User { ... };

let name = match user {
    User { name, .. } => name
};
```

semantic state có thể là:

```text
user.name → MOVED
user.id   → OWNED
```

Không được đọc toàn bộ `user` sau đó.

---

# 10. Partial move và Drop

Nếu `User` có compiler-derived Drop, field-sensitive partial move có thể được hỗ trợ.

Compiler biết:

```text
name moved
id remaining
```

và chỉ cleanup phần còn sở hữu.

---

# 11. Custom Drop

Nếu:

```ax
struct Resource { ... }

impl Drop for Resource {
    ...
}
```

thì partial move phải bị hạn chế theo rule đã frozen.

Khuyến nghị:

```text
custom Drop
→ whole-value ownership
→ no arbitrary partial move
```

Điều này tránh phá invariant của user-defined destructor.

---

# 12. Tuple pattern

```ax
let pair = (10, 20);

match pair {
    (a, b) => ...
}
```

pattern tương ứng:

```text
TuplePattern[
    Binding(a),
    Binding(b)
]
```

---

# 13. Nested pattern

```ax
match result {
    Ok(Some(value)) => ...
    Ok(None) => ...
    Err(error) => ...
}
```

Pattern tree:

```text
Ok
└── Some
    └── value
```

Compiler không cần flatten thành syntax đặc biệt.

---

# 14. Struct pattern

```ax
match user {
    User {
        id,
        name,
    } => ...
}
```

Field matching theo:

```text
FieldId
```

không theo field position.

---

# 15. Field order không ảnh hưởng pattern

Với:

```ax
struct User {
    id: u64,
    name: String,
}
```

pattern:

```ax
User {
    name,
    id,
}
```

hoàn toàn hợp lệ.

Điều này phù hợp với việc default struct layout không stable.

---

# 16. `..`

Cho phép bỏ qua các field:

```ax
User {
    id,
    ..
}
```

`..` có nghĩa:

> Các field còn lại không được bind.

Không có nghĩa là copy phần còn lại.

---

# 17. Missing fields

Nếu struct có:

```ax
User {
    id,
    name,
}
```

pattern:

```ax
User {
    id,
}
```

chỉ hợp lệ nếu syntax semantics cho phép implicit remaining fields.

Khuyến nghị:

> Với struct pattern, nếu không dùng `..`, phải chỉ rõ toàn bộ fields cần match.

Điều này giúp pattern exhaustive và refactor-safe.

---

# 18. Struct evolution

Nếu thêm:

```ax
email: String
```

vào struct, pattern cũ:

```ax
User {
    id,
    name,
}
```

sẽ báo lỗi nếu không có:

```ax
User {
    id,
    name,
    ..
}
```

Đây là chủ ý: compiler giúp phát hiện API/schema change.

---

# 19. Enum variant pattern

```ax
enum Shape {
    Circle(f64),
    Rectangle(f64, f64),
}
```

Pattern:

```ax
match shape {
    Shape::Circle(r) => ...
    Shape::Rectangle(w, h) => ...
}
```

---

# 20. Unit variants

```ax
enum Status {
    Ready,
    Running,
    Done,
}
```

pattern:

```ax
Status::Ready
```

không tạo binding.

---

# 21. Named enum fields

Axiom hỗ trợ:

```ax
enum Message {
    Text { value: String },
    Number { value: i64 },
}
```

pattern:

```ax
Message::Text { value } => ...
```

---

# 22. Tuple enum fields

```ax
enum Result<T, E> {
    Ok(T),
    Err(E),
}
```

pattern:

```ax
Ok(value)
Err(error)
```

---

# 23. Literal pattern

```ax
match x {
    0 => ...
    1 => ...
    _ => ...
}
```

Literal phải tương thích type.

Không có implicit numeric conversion tùy tiện.

---

# 24. Boolean patterns

```ax
match enabled {
    true => ...
    false => ...
}
```

Compiler biết đây là exhaustive.

---

# 25. Character patterns

```ax
match c {
    'a' => ...
    'b' => ...
    _ => ...
}
```

Character là Unicode scalar value theo Core syntax.

---

# 26. Range pattern

Ví dụ:

```ax
match x {
    0..=9 => ...
    _ => ...
}
```

Range pattern được kiểm tra theo type.

Không cho range mơ hồ giữa signed/unsigned.

---

# 27. Range semantics

`0..9` và `0..=9` phải khác nhau rõ:

```text
0..9
→ upper exclusive

0..=9
→ upper inclusive
```

Không phụ thuộc implementation.

---

# 28. Range overflow

Ví dụ:

```ax
u8: 0..=255
```

hợp lệ.

Nhưng:

```ax
u8: 0..=256
```

phải diagnostic compile-time.

Không âm thầm wrap.

---

# 29. Or-pattern

Axiom có thể hỗ trợ:

```ax
match x {
    0 | 1 | 2 => ...
    _ => ...
}
```

Semantics:

```text
pattern A
OR
pattern B
OR
pattern C
```

---

# 30. Binding consistency trong OR-pattern

Không cho:

```ax
x | y
```

nếu một arm bind `x`, arm kia bind `y`.

Các alternatives phải tạo cùng binding set:

```text
same binding names
same semantic types
compatible ownership modes
```

Ví dụ hợp lệ:

```ax
Some(x) | Another(x) => ...
```

nếu `x` có cùng semantic binding type/mode.

---

# 31. Pattern guard

```ax
match x {
    Some(n) if n > 10 => ...
    Some(n) => ...
    None => ...
}
```

Guard:

```text
pattern match
↓
bind variables
↓
evaluate guard
↓
body
```

---

# 32. Guard không đóng góp exhaustiveness

Ví dụ:

```ax
match x {
    Some(n) if n > 0 => ...
}
```

không cover toàn bộ `Some`.

Vì compiler không coi arbitrary runtime boolean guard là exhaustive proof.

---

# 33. Exhaustiveness

Đây là một trong những trách nhiệm chính của pattern checker.

Ví dụ:

```ax
enum Bool {
    False,
    True,
}
```

```ax
match x {
    Bool::False => ...
}
```

→ thiếu `True`.

---

# 34. Exhaustiveness không chỉ dành cho enum

Compiler phải xử lý:

```text
bool
enum
tuple
struct
Option
nested patterns
integer ranges
char ranges
array patterns
slice patterns
```

---

# 35. Usefulness algorithm

Pattern checker nên sử dụng một mô hình semantic tương tự **pattern matrix / usefulness analysis**:

```text
PatternMatrix
      ↓
Constructor specialization
      ↓
Reachable constructors
      ↓
Covered space
      ↓
Missing space
```

Không hard-code từng enum.

---

# 36. Constructor abstraction

Mỗi pattern type có tập constructor.

Ví dụ:

```text
Option<T>
Constructors:
    Some
    None
```

Bool:

```text
true
false
```

Tuple:

```text
single tuple constructor
```

Struct:

```text
single struct constructor
```

---

# 37. Nested exhaustiveness

Ví dụ:

```ax
match x {
    Some(true) => ...
    Some(false) => ...
    None => ...
}
```

Compiler phải hiểu:

```text
Option
 ├── Some
 │    ├── true
 │    └── false
 └── None
```

và kết luận exhaustive.

---

# 38. Unreachable pattern

```ax
match x {
    _ => ...
    Some(v) => ...
}
```

`Some(v)` unreachable.

Compiler nên diagnostic:

```text
E_PATTERN_UNREACHABLE
```

warning/error tùy lint policy.

---

# 39. Duplicate patterns

```ax
match x {
    Some(v) => ...
    Some(v) => ...
}
```

arm thứ hai unreachable.

Không cần runtime check.

---

# 40. Redundant wildcard

```ax
match b {
    true => ...
    false => ...
    _ => ...
}
```

`_` unreachable.

Compiler pode báo warning.

---

# 41. Pattern checker phải phân biệt unreachable và invalid

```text
invalid:
    pattern không type-correct

unreachable:
    pattern hợp lệ nhưng không bao giờ được chọn
```

Hai diagnostics khác nhau.

---

# 42. Ownership trong pattern

Đây là điểm quan trọng.

Pattern checker xác định:

```text
shape
bindings
coverage
```

Ownership verifier xác định:

```text
move/copy/view
```

Không trộn hai subsystem.

---

# 43. Pattern context

Compiler truyền vào:

```text
PatternContext {
    scrutinee_type
    access_mode
    ownership_state
    capability_state
}
```

---

# 44. Matching owned value

```ax
let result = get_result();

match result {
    Ok(value) => use(value),
    Err(error) => log(error),
}
```

Nếu `result` bị consumed, sau match:

```text
result → MOVED
```

không được dùng tiếp.

---

# 45. Matching view

```ax
let r = view(result);

match r {
    ...
}
```

Pattern phải giữ read-only capability.

Không được tự động biến:

```text
view<T>
```

thành:

```text
owned T
```

---

# 46. Matching mut_view

Nếu:

```ax
let r = mut_view(x);
```

pattern có thể mutate field nếu pattern semantics cho phép.

Nhưng không được duplicate `mut_view`.

---

# 47. Destructuring let

Pattern không chỉ dùng trong `match`.

Axiom hỗ trợ:

```ax
let (x, y) = pair;
```

và:

```ax
let User { id, name } = user;
```

---

# 48. Destructuring ownership

```ax
let User { name, .. } = user;
```

có thể tạo partial move.

Verifier cập nhật place tree:

```text
user.name → MOVED
user.id   → OWNED
```

---

# 49. Destructuring và immutable `let`

`let` immutable không có nghĩa value không thể bị move.

Ví dụ:

```ax
let user = make_user();

let name = user.name;
```

có thể move `name` nếu type semantics cho phép.

`let` chỉ ngăn mutation.

---

# 50. `var` và destructuring

```ax
var point = (10, 20);

let (x, y) = point;
```

các binding mới immutable dù source `point` mutable.

Mutability là property của binding/capability, không tự động truyền từ source.

---

# 51. Array pattern

Axiom có thể hỗ trợ fixed array:

```ax
let values: [i32; 3];

match values {
    [a, b, c] => ...
}
```

Đây là exhaustive vì length known.

---

# 52. Array length mismatch

```ax
[i32; 3]
```

không match:

```ax
[a, b]
```

nếu pattern semantics yêu cầu exact fixed-array length.

---

# 53. Slice/view pattern

Với:

```ax
view<T>
```

length runtime.

Có thể hỗ trợ:

```ax
match items {
    [] => ...
    [first, rest @ ..] => ...
}
```

nhưng slice pattern system phức tạp hơn fixed array.

---

# 54. Khuyến nghị slice pattern v0.1

Nên hỗ trợ tối thiểu:

```text
[]
[first, ..]
[.., last]
[first, middle @ .., last]
```

nếu implementation không làm solver quá phức tạp.

Không cần hàng loạt syntax pattern nâng cao.

---

# 55. Binding `@`

Ví dụ:

```ax
Some(value @ 1..=10)
```

có nghĩa:

```text
match subpattern
+
bind matched value
```

Nếu đưa vào Core, binding consistency phải được verifier xử lý.

---

# 56. Có nên có `@` trong v0.1?

Khuyến nghị:

> **Có thể hỗ trợ, nhưng không cần thiết để compiler bootstrap.**

Nó có utility cao nhưng không ảnh hưởng nền tảng type system.

---

# 57. Pattern range và integer types

Pattern:

```ax
0..=100
```

phải được contextual typing:

```text
expected type = u8
```

thì literal được interpret là `u8`.

Không default `i32` một cách mù quáng nếu expected pattern type đã biết.

---

# 58. Pattern inference

Ví dụ:

```ax
match x {
    Some(v) => ...
}
```

`Some` resolve từ expected type của `x`.

Nếu `x` chưa có type đủ để resolve:

```text
ambiguous pattern
```

---

# 59. Pattern constructor resolution

`Some` có thể được resolve:

```text
Option<T>::Some
```

thông qua type context.

Không scan toàn bộ enum variants trong workspace.

---

# 60. Pattern + generic enum

```ax
fn unwrap<T>(x: Option<T>) -> T {
    match x {
        Some(v) => v,
        None => panic(...),
    }
}
```

Pattern checker biết:

```text
T
```

là generic parameter nhưng không cần concrete type.

---

# 61. Pattern + associated type

Nếu:

```ax
T::Item
```

xuất hiện trong pattern type, trait solver phải normalize trước khi pattern checker cần constructor information.

Pipeline:

```text
Type normalization
↓
Pattern checking
```

---

# 62. Pattern + `never`

Không có constructor.

Ví dụ:

```ax
fn impossible(x: never) {
    match x {
        ...
    }
}
```

Compiler biết branch unreachable vì `never` không có value.

---

# 63. Pattern + unit

```ax
match x {
    () => ...
}
```

Unit chỉ có một possible value.

Do đó pattern này exhaustive.

---

# 64. Pattern + structs

Struct không có variant alternatives.

Do đó:

```ax
User { id, name }
```

là constructor duy nhất.

Nếu field subpattern exhaustive thì whole struct exhaustive.

---

# 65. Pattern + private fields

Một module bên ngoài không được destructure private fields.

Ví dụ:

```ax
pub struct User {
    pub id: u64,
    secret: u64,
}
```

external module:

```ax
match user {
    User { id, .. } => ...
}
```

có thể hợp lệ.

Nhưng:

```ax
User { secret, .. } => ...
```

→ visibility error.

---

# 66. Public struct evolution

Đây là lý do `..` hữu ích.

Library có thể thêm private/public fields mà code downstream sử dụng:

```ax
User { id, .. }
```

vẫn có thể ổn định hơn full destructuring.

---

# 67. Pattern không bypass visibility

Không có:

```text
unsafe match private_field
```

Unsafe không biến private thành accessible.

Visibility là compile-time semantic boundary riêng.

---

# 68. Pattern và `Copy`

Nếu type:

```text
Copy
```

pattern binding có thể lấy value mà không consume owner.

Ví dụ:

```ax
let x: i32 = 10;

match x {
    n => ...
}

use(x);
```

`x` vẫn valid.

---

# 69. Pattern và non-Copy

Với:

```ax
let x: String;
```

binding:

```ax
match x {
    value => ...
}
```

có thể consume `x`.

Sau đó `x` không được dùng.

---

# 70. Pattern và Clone

Pattern không tự gọi:

```text
Clone::clone
```

Nếu muốn duplicate:

```ax
let y = x.clone();
```

phải explicit.

Đây là invariant quan trọng để tránh hidden cost.

---

# 71. Pattern không tự tạo heap

Destructuring:

```ax
let User { id, name } = user;
```

không tự tạo:

```text
heap object
```

hay temporary allocation.

Compiler có thể scalarize fields.

---

# 72. Pattern lowering

Ví dụ:

```ax
match result {
    Ok(v) => use(v),
    Err(e) => recover(e),
}
```

MIR có thể:

```text
switch discriminant(result)
    case Ok:
        project result.value
        ...
    case Err:
        project result.error
        ...
```

---

# 73. Enum discriminant

Compiler có thể dùng:

```text
integer tag
niche
pointer nullability
```

hoặc representation khác.

Pattern semantics không phụ thuộc physical discriminant representation.

---

# 74. Pattern + niche optimization

Ví dụ:

```text
Option<Box<T>>
```

có thể có niche representation.

Pattern checker chỉ biết:

```text
Some
None
```

Không biết machine representation.

---

# 75. Match optimization

Compiler có thể lower:

```text
match x {
    1 => ...
    2 => ...
    3 => ...
    _ => ...
}
```

thành:

- branch chain;
- jump table;
- binary search;
- decision tree.

Miễn semantics giữ nguyên.

---

# 76. Pattern decision tree

Internal IR có thể:

```text
PatternDecisionTree
```

trước khi lower MIR.

Ví dụ:

```text
check tag
 ├── Some
 │    └── check value
 └── None
```

Giúp optimizer và codegen độc lập pattern syntax.

---

# 77. Pattern compilation không được làm mất Drop

Khi pattern destructure:

```ax
match resource {
    Resource { handle } => ...
}
```

compiler phải biết field nào:

```text
moved
borrowed/viewed
copied
untouched
```

để drop elaboration chính xác.

---

# 78. Pattern failure và cleanup

Nếu pattern matching có temporary values, khi branch không match:

```text
temporary cleanup
```

phải xảy ra đúng semantics.

Compiler không được tạo leak chỉ vì pattern decision tree.

---

# 79. Pattern guards và side effects

Compiler không được reorder:

```ax
match x {
    A if check_a() => ...
    B if check_b() => ...
}
```

thành:

```text
check_b()
→ check_a()
```

nếu cả hai có side effects.

Pattern matching semantics giữ arm order.

---

# 80. Arm order

Nếu nhiều arm đều có thể match:

```ax
match x {
    Some(_) => A,
    Some(1) => B,
}
```

arm thứ hai unreachable.

Axiom không dùng “best pattern match”.

Pattern order là semantic.

---

# 81. Không có implicit backtracking side effects

Pattern matching itself không gọi arbitrary user code ngoại trừ explicit guards/destructuring mechanisms được định nghĩa.

Do đó compiler có thể tối ưu decision tree mà không tạo hidden side effects.

---

# 82. Exhaustiveness algorithm architecture

Đề xuất:

```text
PatternChecker
    │
    ├── TypePatternInfo
    ├── ConstructorDB
    ├── PatternMatrix
    ├── Usefulness
    ├── Exhaustiveness
    └── UnreachableArm
```

`ConstructorDB` biết:

```text
Type
 ↓
Constructors
 ↓
Fields / payload types
```

---

# 83. ConstructorDB

Ví dụ:

```text
Option<T>
    Some(T)
    None

Result<T,E>
    Ok(T)
    Err(E)

Bool
    false
    true
```

Đối với struct:

```text
User
    User { id: u64, name: String }
```

---

# 84. Pattern checker không phụ thuộc layout

Không dùng:

```text
offset_of
sizeof
memory tag
```

để quyết định exhaustiveness.

Đây là semantic type property.

---

# 85. Compiler diagnostics

Ví dụ:

```text
error[E_PATTERN_NONEXHAUSTIVE]:
pattern does not cover all possible values

missing:
    None

help:
    add an arm matching `None`
```

Với nested pattern:

```text
missing:
    Some(false)
```

Diagnostic nên càng cụ thể càng tốt.

---

# 86. AI-readable diagnostics

Structured:

```json
{
  "code": "E_PATTERN_NONEXHAUSTIVE",
  "scrutinee_type": "Option<bool>",
  "covered": [
    "Some(true)"
  ],
  "missing": [
    "Some(false)",
    "None"
  ]
}
```

Agent có thể tự sửa code đáng tin cậy hơn.

---

# 87. Pattern cache

Pattern checking có thể memoize theo:

```text
PatternAST
+
ExpectedType
+
TraitNormalizationState
+
VisibilityContext
```

nhưng phải invalidate nếu type/enum declaration thay đổi.

---

# 88. Incremental enum change

Nếu:

```ax
enum Status {
    Ready,
    Done,
}
```

thêm:

```ax
Running,
```

mọi match exhaustive trên `Status` có thể bị ảnh hưởng.

Compiler dependency graph phải track:

```text
Status constructor set
```

---

# 89. Semantic fingerprint

Enum fingerprint phải chứa constructor set:

```text
Status {
    Ready
    Running
    Done
}
```

Thay đổi variant → interface fingerprint change nếu enum public.

---

# 90. Pattern system và AI-friendly language

Pattern syntax:

```ax
match value {
    Some(x) => ...
    None => ...
}
```

có một lợi thế lớn cho AI:

```text
constructor
→ binding
→ body
```

rất explicit và dễ phân tích AST.

Không cần nhiều hidden object model.

---

# 91. Invariants

### `APAT-20`
Patterns are structural matching constructs, not ordinary expressions.

### `APAT-21`
Every pattern is checked against an expected semantic type.

### `APAT-22`
Pattern checking is distinct from ownership verification.

### `APAT-23`
Pattern checking is distinct from trait solving.

### `APAT-24`
Wildcard patterns create no binding.

### `APAT-25`
Pattern bindings create stable LocalIds.

### `APAT-26`
Pattern bindings do not implicitly create references.

### `APAT-27`
Binding access mode is determined semantically.

### `APAT-28`
Move, Copy, view and mut_view semantics are verified independently.

### `APAT-29`
Partial moves are field-sensitive where permitted.

### `APAT-30`
Custom Drop restricts partial moves.

### `APAT-31`
Pattern matching never implicitly clones values.

### `APAT-32`
Pattern matching never implicitly allocates.

### `APAT-33`
Struct patterns identify fields by FieldId, not physical position.

### `APAT-34`
Struct field order does not affect pattern semantics.

### `APAT-35`
Enum variants have stable VariantIds.

### `APAT-36`
Enum representation is independent of pattern semantics.

### `APAT-37`
Literal patterns require type-compatible literals.

### `APAT-38`
Range patterns have explicit inclusive/exclusive semantics.

### `APAT-39`
Range bounds cannot silently overflow.

### `APAT-40`
Or-pattern alternatives must have compatible bindings.

### `APAT-41`
Pattern guards do not contribute to exhaustiveness proofs.

### `APAT-42`
Only a matched arm evaluates its guard/body.

### `APAT-43`
Match arm order is deterministic.

### `APAT-44`
Unreachable patterns are diagnosable.

### `APAT-45`
Invalid patterns and unreachable patterns are distinct diagnostics.

### `APAT-46`
Exhaustiveness is checked semantically.

### `APAT-47`
Exhaustiveness does not depend on physical representation.

### `APAT-48`
Nested patterns are recursively checked.

### `APAT-49`
Pattern constructor sets are derived from semantic types.

### `APAT-50`
`never` has no possible constructors.

### `APAT-51`
Unit has exactly one semantic value.

### `APAT-52`
Fixed-size array patterns respect array length.

### `APAT-53`
Slice/view patterns respect runtime length semantics.

### `APAT-54`
Private fields cannot be destructured across visibility boundaries.

### `APAT-55`
Pattern matching cannot bypass visibility.

### `APAT-56`
Pattern matching preserves ownership invariants.

### `APAT-57`
Pattern matching preserves capability invariants.

### `APAT-58`
Pattern matching preserves Drop semantics.

### `APAT-59`
Pattern lowering cannot introduce hidden cloning.

### `APAT-60`
Pattern lowering cannot introduce hidden allocation.

### `APAT-61`
Enum discriminant representation is an implementation detail.

### `APAT-62`
Match optimization cannot alter arm semantics.

### `APAT-63`
Guard evaluation order is preserved.

### `APAT-64`
Pattern decision trees preserve observable behavior.

### `APAT-65`
Pattern checking terminates for recursive/nested inputs.

### `APAT-66`
Pattern diagnostics identify missing constructors where possible.

### `APAT-67`
Pattern diagnostics have stable machine-readable codes.

### `APAT-68`
Pattern checking is incrementally cacheable.

### `APAT-69`
Enum constructor changes invalidate affected exhaustiveness queries.

### `APAT-70`
Clean and incremental pattern checking are semantically equivalent.

### `APAT-71`
Pattern analysis is deterministic.

### `APAT-72`
Pattern analysis may execute in parallel where independent.

### `APAT-73`
Pattern-generated bindings enter ordinary name/type resolution.

### `APAT-74`
Pattern-generated MIR enters normal ownership/capability verification.

### `APAT-75`
No invalid or unverified pattern semantics may reach final code generation.

---

# Trạng thái frontend sau BOOTSTRAP-133

```text
                         SOURCE
                           │
                           ▼
                         Lexer
                           │
                           ▼
                          CST
                           │
                           ▼
                          AST
                           │
                  Declaration Collection
                           │
                           ▼
                    Module / Scope Graph
                           │
                           ▼
                    Name Resolution
                           │
              ┌────────────┼────────────┐
              │            │            │
            TypeDB       TraitDB      ConstDB
              │            │            │
              └────────────┼────────────┘
                           ▼
                      Typed HIR
                           │
             ┌─────────────┼──────────────┐
             │             │              │
        Expressions     Patterns       Comptime
             │             │              │
             └─────────────┼──────────────┘
                           ▼
                          MIR
                           │
                           ▼
                       Verification
```

Đến đây Axiom đã khóa được gần như toàn bộ **semantic frontend cơ bản**:

- type;
- trait;
- name;
- module;
- visibility;
- expression;
- control flow;
- pattern;
- ownership/capability;
- comptime.

Điều này cho phép chuyển sang phần rất quan trọng tiếp theo: **MIR và semantics của place/memory operations**.

---

# BOOTSTRAP-134 — MIR Semantic Model, Places, Values & Memory Operations

Task kế tiếp sẽ thiết kế chi tiết representation trung gian quan trọng nhất của Axiom:

```text
Typed HIR
    │
    ▼
   MIR
    │
    ├── Place
    ├── Operand
    ├── RValue
    ├── Statement
    ├── Terminator
    ├── Storage
    ├── Move
    ├── Copy
    ├── Drop
    ├── View
    ├── MutView
    ├── Load/Store
    ├── Atomic
    ├── Call
    ├── Branch
    └── Await
```

Đặc biệt sẽ khóa:

- Place projection;
- field/index/deref projection;
- value vs place;
- Move/Copy semantics;
- initialization state;
- partial move;
- drop flags;
- storage lifetime;
- capability representation;
- load/store;
- memory effects;
- address-taking;
- raw pointer boundary;
- aggregate construction;
- enum discriminant;
- function call ABI-neutral form;
- cleanup blocks;
- panic/unwind edges;
- async suspension;
- GPU operations;
- FFI;
- MIR invariants;
- MIR verifier boundary;
- SSA conversion về sau.

**BOOTSTRAP-134 là task tiếp theo.**