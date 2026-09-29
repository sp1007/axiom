# AXIOM LANGUAGE SPECIFICATION v0.1
# Part XIII — Patterns · Destructuring · Match Semantics

Phần này khóa semantics của pattern matching, đặc biệt là điểm giao nhau giữa:

- `struct`
- `enum`
- `Option`
- `Result`
- Move
- Copy
- Drop
- `view`
- `mut_view`
- partial move
- exhaustiveness

Nguyên tắc:

> **Pattern chỉ mô tả cách phân rã giá trị/capability; nó không tạo ra một ownership model thứ hai.**

---

# 1. Pattern là compile-time structure

Ví dụ:

```axiom
match message {
    Message.Quit => ...
    Message.Text(text) => ...
    Message.Move { x, y } => ...
}
```

Pattern được compiler phân tích trước runtime.

Runtime chỉ thực hiện:

```text
evaluate scrutinee
→ determine variant/tag
→ destructure required fields
→ execute selected arm
```

---

# 2. Các loại pattern v0.1

Axiom hỗ trợ:

```text
Wildcard
Binding
Literal
Tuple
Struct
Enum variant
Array
Range
Or-pattern
Nested pattern
```

Ví dụ:

```axiom
match value {
    0 => ...
    1..=10 => ...
    (x, y) => ...
    Point { x, y } => ...
    Some(x) => ...
    _ => ...
}
```

---

# 3. Wildcard

```axiom
match x {
    0 => ...
    _ => ...
}
```

`_` không tạo binding.

Khác:

```axiom
x => ...
```

`x` tạo binding.

---

# 4. Binding pattern

```axiom
match point {
    Point { x, y } => ...
}
```

`x` và `y` là bindings.

Binding mặc định theo semantics của scrutinee:

```text
owned value
    → có thể move

view
    → tạo view/binding không sở hữu

Copy type
    → có thể copy nếu context yêu cầu value
```

Compiler không được mặc định tạo clone.

---

# 5. Move trong pattern

Ví dụ:

```axiom
struct User {
    id: u64
    name: String
}

let user = User {
    id: 1,
    name: "A"
}

match user {
    User { name, .. } => use(name)
}
```

Nếu `name: String` là non-Copy, pattern binding `name` có thể move field đó.

Sau match:

```text
user.id
```

vẫn hợp lệ.

Nhưng:

```text
user.name
```

không còn hợp lệ.

Đây là **partial move**.

---

# 6. Partial move

Axiom cho phép partial move đối với type phù hợp.

Ví dụ:

```axiom
let user = User {
    id: 10,
    name: "Hùng"
}

let name = user.name
print(user.id)
```

Sau đó semantic state:

```text
user:
    id   = OWNED
    name = MOVED
```

Không được:

```axiom
print(user.name)
```

---

# 7. Struct có custom Drop

Nếu:

```axiom
struct Resource {
    handle: Handle
}

impl Drop for Resource {
    fn drop(self: mut_view<Self>) {
        ...
    }
}
```

thì:

```text
partial move
```

bị cấm.

Ví dụ:

```axiom
let x = resource.handle
```

→ compile error nếu việc này tạo partial move của `Resource`.

Lý do: compiler không thể để user-defined destructor nhận một object đã bị phá cấu trúc một cách tùy ý.

---

# 8. Derived Drop và partial move

Nếu Drop semantics được compiler derive/compose và compiler biết chính xác field nào còn owned:

```text
struct A {
    a: String
    b: File
}
```

compiler có thể quản lý:

```text
a → moved
b → still owned
```

và chỉ drop `b`.

Điều này phù hợp với:

> **Compiler-managed lifetime, không phải programmer-written lifetime.**

---

# 9. Binding bằng `let`

Pattern cũng được phép trong `let`:

```axiom
let Point { x, y } = point
```

Đây là **irrefutable pattern** nếu compiler biết `point` chắc chắn là `Point`.

---

# 10. Refutable pattern

Pattern có thể thất bại:

```axiom
let Some(x) = value
```

nếu `value: Option<T>`.

Đây là refutable pattern.

Không được phép dùng trong plain `let` v0.1.

Compiler yêu cầu:

```axiom
match value {
    Some(x) => ...
    None => ...
}
```

hoặc API tương ứng.

---

# 11. Irrefutable pattern

Pattern chắc chắn match:

```axiom
let Point { x, y } = point
```

là irrefutable.

Các binding đơn giản:

```axiom
let x = value
```

luôn irrefutable.

---

# 12. Pattern trong function parameters

Có thể hỗ trợ:

```axiom
fn length(Point { x, y }: Point) -> f32 {
    ...
}
```

nhưng semantics phải tương đương với destructuring tại function entry.

Không tạo cơ chế ownership mới.

Nếu pattern có thể fail thì không được phép ở parameter của function thông thường.

---

# 13. Tuple pattern

```axiom
let (x, y) = point
```

Nested:

```axiom
let (x, (y, z)) = value
```

Ownership được áp dụng đệ quy.

---

# 14. Struct pattern

```axiom
match user {
    User {
        id,
        name,
    } => ...
}
```

Có thể bỏ field:

```axiom
User { id, .. }
```

`..` nghĩa:

> các field còn lại không được binding bởi pattern.

Nó **không có nghĩa là tự động drop ngay tại pattern**.

---

# 15. Enum pattern

```axiom
match result {
    Result.Ok(value) => ...
    Result.Err(error) => ...
}
```

hoặc:

```axiom
match message {
    Message.Move { x, y } => ...
}
```

Variant payload được destructure theo ownership rules thông thường.

---

# 16. Nested enum pattern

```axiom
match response {
    Some(Result.Ok(value)) => ...
    Some(Result.Err(error)) => ...
    None => ...
}
```

Compiler phải phân tích ownership của toàn bộ pattern tree.

---

# 17. Pattern không tự Copy

Ví dụ:

```axiom
struct Data {
    buffer: Buffer
}
```

Không được:

```text
pattern binding
    ↓
tự động clone buffer
```

Nếu `Buffer` non-Copy:

```text
binding
→ Move
```

nếu context yêu cầu owned value.

Muốn copy:

```axiom
let copy = buffer.clone()
```

hoặc dùng capability:

```axiom
let v = view(buffer)
```

---

# 18. `view` pattern

Ví dụ:

```axiom
fn inspect(data: view<Data>) {
    match data {
        Data { field, .. } => ...
    }
}
```

Ở đây pattern không move `field`.

Binding là capability đọc.

Conceptually:

```text
view<Data>
    ↓ projection
view<FieldType>
```

nếu field có thể được view.

---

# 19. `mut_view` pattern

```axiom
fn modify(data: mut_view<Data>) {
    match data {
        Data { field, .. } => {
            field = ...
        }
    }
}
```

Binding mutable phải giữ exclusive capability.

Compiler không được tạo:

```text
mut_view<Data>
+
mut_view<Field>
+
mut_view<Data>
```

một cách conflicting.

---

# 20. Capability projection

Pattern projection:

```text
view<Struct>
    ↓
view<Field>
```

là capability projection.

Nó không transfer ownership.

Tương tự:

```text
mut_view<Struct>
    ↓
mut_view<Field>
```

chỉ hợp lệ khi exclusive access vẫn được đảm bảo.

---

# 21. Disjoint fields

Ví dụ:

```axiom
struct Point {
    x: i32
    y: i32
}
```

Compiler có thể chứng minh:

```text
x region
    DISJOINT
y region
```

Do đó:

```axiom
let Point { x, y } = mut_view(point)
```

có thể cho phép hai mutable projections độc lập nếu chúng không escape theo cách gây overlap.

---

# 22. Pattern không thay đổi provenance

Nếu:

```text
view<User>
```

được destructure thành:

```text
view<String>
```

thì provenance vẫn là:

```text
owner → User → name
```

Không được coi field view là một ownership object độc lập.

---

# 23. Match trên owned value

```axiom
match user {
    User { name } => use(name)
}
```

có thể move `name`.

Sau match compiler theo dõi:

```text
user.name = MOVED
```

Đây là lý do pattern system phải tích hợp trực tiếp với MIR ownership state.

---

# 24. Match trên `view`

```axiom
match view(user) {
    User { name } => inspect(name)
}
```

không move `user.name`.

Sau match:

```text
user
    vẫn OWNED
```

---

# 25. Match trên `mut_view`

```axiom
match mut_view(user) {
    User { name } => modify(name)
}
```

exclusive capability vẫn thuộc semantic scope của match.

Không được trả capability ra ngoài owner lifetime.

---

# 26. Match arm là scope

Mỗi arm tạo semantic scope riêng:

```axiom
match value {
    Some(x) => {
        use(x)
    }

    None => {
        ...
    }
}
```

Binding `x` không tồn tại ngoài arm.

---

# 27. Drop của binding trong arm

Nếu binding sở hữu resource:

```axiom
match value {
    Some(resource) => {
        use(resource)
    }
    None => {}
}
```

resource được drop cuối arm nếu chưa moved.

Compiler phải đảm bảo:

```text
arm exit
    ↓
drop live owned bindings
```

---

# 28. Match arm return

Nếu arm:

```axiom
Some(x) => return process(x)
```

thì cleanup phải chạy trước function return.

MIR:

```text
match
 ↓
move x
 ↓
call process
 ↓
cleanup
 ↓
return
```

hoặc compiler có thể reorder khi semantics được bảo toàn.

---

# 29. Pattern guard

Axiom v0.1 nên hỗ trợ:

```axiom
match value {
    Some(x) if x > 10 => ...
    Some(x) => ...
    None => ...
}
```

Guard là boolean expression runtime.

---

# 30. Guard không được move binding

Ví dụ:

```axiom
match value {
    Some(x) if consume(x) => ...
}
```

Nếu `consume(x)` move `x`, compiler sẽ gặp vấn đề vì guard có thể fail và match phải tiếp tục arm khác.

Do đó:

> **Pattern guard chỉ được READ binding hoặc thực hiện mutation được phép; không được consume/move binding theo cách làm mất giá trị trước khi arm được chọn.**

Đây là rule rất quan trọng.

---

# 31. Guard và side effects

Guard có thể có side effects nếu expression thông thường cho phép.

Nhưng compiler phải đánh giá guard theo thứ tự source semantics.

Không được reorder guard với pattern selection nếu làm thay đổi observable side effects.

---

# 32. Or-pattern

Có thể:

```axiom
match value {
    0 | 1 => ...
    2 | 3 => ...
    _ => ...
}
```

Các alternative phải tạo binding tương thích.

---

# 33. Binding consistency trong or-pattern

Không được:

```axiom
Some(x) | None => ...
```

vì một alternative tạo `x`, alternative kia không.

Compiler reject.

Tương tự:

```text
Some(x: T)
|
Some(y: U)
```

phải có binding semantics tương thích.

---

# 34. Range pattern

Integer:

```axiom
match x {
    0..10 => ...
    10..=20 => ...
    _ => ...
}
```

Axiom giữ semantics range thống nhất:

```text
a..b
```

là half-open:

```text
[a, b)
```

và:

```text
a..=b
```

là inclusive:

```text
[a, b]
```

---

# 35. Range pattern phải finite/exhaustive

Compiler chỉ thực hiện exhaustiveness reasoning đầy đủ với type có domain mà compiler có thể mô hình hóa.

Ví dụ integer:

```text
0..=255
```

có thể hiểu rõ.

Floating-point range pattern không nằm trong Core v0.1.

---

# 36. Literal pattern

```axiom
match status {
    0 => ...
    1 => ...
    _ => ...
}
```

Equality semantics của literal pattern là semantic equality phù hợp với type.

Không dùng arbitrary overloaded `==` trong pattern matching nếu điều đó làm exhaustiveness không quyết định được.

Pattern matching phải dựa trên semantics compiler biết.

---

# 37. Exhaustiveness

Compiler phải đảm bảo:

```axiom
match option {
    Some(x) => ...
    None => ...
}
```

đầy đủ.

Nhưng:

```axiom
match option {
    Some(x) => ...
}
```

→ compile error.

---

# 38. Unreachable arm

```axiom
match value {
    _ => ...
    Some(x) => ...
}
```

`Some(x)` unreachable.

Compiler nên báo:

```text
warning/error
```

Quyết định v0.1:

> **Unreachable match arm là compile-time error**, không chỉ warning.

Lý do: nó gần như chắc chắn là bug logic và làm semantics của pattern source gây hiểu nhầm.

---

# 39. Exhaustiveness không dựa vào `_` để bỏ qua type checking

Ví dụ:

```axiom
match value {
    _ => process(value)
}
```

`_` làm match exhaustive nhưng không làm compiler bỏ qua:

- ownership
- type checking
- capability rules
- Drop rules

---

# 40. Enum exhaustiveness

```axiom
enum State {
    Ready,
    Running,
    Failed(Error),
}
```

Compiler biết toàn bộ variants.

```axiom
match state {
    State.Ready => ...
    State.Running => ...
    State.Failed(e) => ...
}
```

exhaustive.

Nếu thêm variant:

```text
State.Cancelled
```

các match exhaustive cũ phải được compiler phát hiện khi recompilation.

---

# 41. Non-exhaustive public enums

Để hỗ trợ ABI/library evolution, Axiom có thể cần:

```axiom
@non_exhaustive
pub enum State { ... }
```

Khi đó external package không được exhaustive-match mà không có fallback.

Ví dụ:

```axiom
match state {
    State.Ready => ...
    _ => ...
}
```

Đây là một điểm cần giữ trong v0.1 nếu package ecosystem hướng tới versioning nghiêm túc.

---

# 42. Struct pattern và private fields

Nếu:

```axiom
pub struct User {
    pub id: u64
    private_token: Token
}
```

package bên ngoài không được:

```axiom
User { private_token, .. }
```

Visibility áp dụng cho pattern projection.

Có thể expose constructor/pattern API bằng các public methods/functions.

---

# 43. Match trên `dyn Trait`

Không thể pattern-match arbitrary concrete type của:

```axiom
dyn Trait
```

trừ khi trait cung cấp explicit type identity/downcast mechanism.

Axiom không có implicit RTTI.

Nếu cần:

```text
dyn Trait
    ↓
explicit Any/type-id API
```

phải opt-in.

---

# 44. No implicit downcast

Không có:

```axiom
if x is Dog {
    x.bark()
}
```

cho arbitrary `dyn Animal`.

Phải có explicit API nếu muốn downcast.

Điều này giữ:

```text
dyn Trait
```

là abstraction thực sự, không phải class hierarchy trá hình.

---

# 45. Pattern + `Option`

`Option<T>` là enum:

```axiom
enum Option<T> {
    None,
    Some(T)
}
```

Do đó:

```axiom
match value {
    Some(x) => ...
    None => ...
}
```

không cần compiler magic riêng.

Compiler có thể optimize representation bằng niche optimization.

---

# 46. Pattern + `Result`

Tương tự:

```axiom
enum Result<T, E> {
    Ok(T),
    Err(E)
}
```

`match` không cần biết `Result` là "error type".

Đây là lợi ích của algebraic data types.

---

# 47. `?` và pattern semantics

:

```axiom
let value = operation()?
```

conceptually tương đương:

```axiom
match operation() {
    Ok(value) => value
    Err(error) => return Err(error)
}
```

nhưng compiler lowering trực tiếp có thể tối ưu hơn.

Ownership của `error` và `value` vẫn theo pattern semantics.

---

# 48. Match không tạo heap allocation

Pattern matching trên:

```text
struct
enum
tuple
array
Option
Result
```

không yêu cầu allocation.

Compiler có thể lower thành:

```text
switch
branch
conditional move
load
```

---

# 49. Enum layout và match

Compiler có thể dùng:

```text
tag
niche
bit pattern
jump table
branch tree
conditional select
```

tùy target.

Source semantics không phụ thuộc layout cụ thể.

---

# 50. Optimization

Compiler có thể:

```text
eliminate redundant discriminant loads
combine branches
jump-table lowering
branch prediction optimization
constant-fold patterns
remove impossible arms
```

miễn observable semantics giữ nguyên.

---

# 51. Pattern ownership matrix

| Scrutinee | Binding | Semantics |
|---|---|---|
| `T`, `T: Copy` | value | Copy nếu cần |
| `T`, non-Copy | value | Move |
| `T`, Drop | field move theo Drop rules |
| `view<T>` | binding | Read capability |
| `mut_view<T>` | binding | Mutable capability |
| `dyn Trait` | dynamic capability | Không concrete destructuring |
| raw pointer | unsafe | Explicit dereference |

---

# 52. Pattern invariants

### APATTERN-20 — Pattern Destructuring Preserves Ownership Semantics

Pattern không tạo ownership model mới.

### APATTERN-21 — Owned Non-Copy Binding Moves

Binding value từ owned non-Copy source là move.

### APATTERN-22 — Copy Binding May Copy

Type `Copy` có thể được copy.

### APATTERN-23 — View Binding Does Not Transfer Ownership

View pattern chỉ tạo capability.

### APATTERN-24 — Mutable View Projection Preserves Exclusivity

Không tạo overlapping mutable capabilities.

### APATTERN-25 — Partial Move Is Explicitly Tracked

Compiler theo dõi field-level ownership.

### APATTERN-26 — User Drop Forbids Partial Move

Custom Drop type không được partial move.

### APATTERN-27 — Irrefutable Patterns Only In Irrefutable Contexts

Plain `let` không nhận pattern có thể fail.

### APATTERN-28 — Match Arms Are Independent Scopes

Bindings chỉ sống trong arm.

### APATTERN-29 — Match Cleanup Is Deterministic

Owned values được cleanup đúng semantics.

### APATTERN-30 — Guard Cannot Consume Preselected Binding

Guard không được move value mà match có thể cần cho alternative processing.

### APATTERN-31 — Or-Pattern Bindings Must Be Consistent

Mọi alternative phải cung cấp compatible bindings.

### APATTERN-32 — Match Is Exhaustive

Safe `match` phải cover domain.

### APATTERN-33 — Unreachable Match Arms Are Errors

Arm không bao giờ được chọn là compile-time error.

### APATTERN-34 — Exhaustiveness Is Type-Aware

Compiler sử dụng type/domain information.

### APATTERN-35 — Pattern Matching Does Not Require Allocation

Pattern lowering không yêu cầu heap.

### APATTERN-36 — Pattern Matching Does Not Imply RTTI

Enum/struct matching compile-time.

### APATTERN-37 — Dynamic Trait Does Not Permit Implicit Downcast

Downcast phải explicit.

### APATTERN-38 — Private Fields Cannot Be Destructured Externally

Visibility áp dụng cho pattern projection.

### APATTERN-39 — Pattern Semantics Are Independent Of Enum Physical Layout

Niche/tag representation là compiler freedom.

### APATTERN-40 — `?` Preserves Pattern Ownership Semantics

Error/value propagation không tạo ownership exception.

---

# Part XIV — Functions · Closures · Calls · Evaluation Order

Bây giờ cần khóa một phần cực kỳ quan trọng khác:

> **Axiom thực sự đánh giá expression theo thứ tự nào?**

Đây là nền tảng để compiler có thể aggressive optimization mà không biến chương trình thành hành vi khó đoán.

---

## 1. Function là behavior primitive

```axiom
fn add(a: i32, b: i32) -> i32 {
    a + b
}
```

Function không thuộc object.

Method:

```axiom
fn length(self: view<Vec2>) -> f32
```

chỉ là syntax sugar.

---

# 2. Method call lowering

```axiom
v.length()
```

semantic tương đương:

```axiom
length(v)
```

với receiver mode phù hợp.

Không có hidden `this` pointer đặc biệt.

---

# 3. Function arguments được evaluate deterministic

Ví dụ:

```axiom
foo(a(), b())
```

Axiom phải khóa evaluation order.

Đề xuất:

> **Arguments được evaluate từ trái sang phải.**

```text
a()
↓
b()
↓
foo(...)
```

Đây là lựa chọn quan trọng để loại bỏ kiểu ambiguity của C/C++.

---

# 4. Receiver được evaluate trước arguments

```axiom
object.method(a(), b())
```

thứ tự:

```text
object
↓
a()
↓
b()
↓
method
```

Method resolution là compile-time; runtime receiver evaluation vẫn theo thứ tự trên.

---

# 5. Binary operators

```axiom
a + b
```

evaluation:

```text
a
↓
b
↓
operator
```

Không được evaluate `b` trước `a`.

---

# 6. `&&` và `||`

Short-circuit bắt buộc.

```axiom
a && b
```

nếu `a == false`:

```text
b
```

không được evaluate.

Tương tự:

```axiom
a || b
```

nếu `a == true`, `b` không evaluate.

---

# 7. `if`

```axiom
if condition {
    a()
} else {
    b()
}
```

luôn:

```text
condition
↓
chỉ một branch
```

Branch còn lại không được evaluate.

---

# 8. `match`

Scrutinee evaluate đúng một lần:

```axiom
match get_value() {
    ...
}
```

`get_value()` chỉ chạy một lần.

Compiler không được duplicate observable evaluation.

---

# 9. Assignment

```axiom
x = expression
```

semantic:

```text
evaluate target place
↓
evaluate RHS
↓
perform assignment
```

Target evaluation và RHS evaluation phải tuân deterministic ordering.

---

# 10. Move expression

```axiom
let y = x
```

nếu `x` non-Copy:

```text
ownership(x)
→ MOVED
ownership(y)
→ OWNED
```

Physical copy không bắt buộc.

---

# 11. Copy expression

Nếu:

```text
T: Copy
```

thì:

```axiom
let y = x
```

có thể semantic copy.

Compiler vẫn có thể giữ một physical register/value nếu observable semantics giống nhau.

---

# 12. Function return

```axiom
fn make() -> String {
    let s = ...
    s
}
```

semantic:

```text
s ownership
↓
return ownership
```

Không yêu cầu heap allocation.

---

# 13. Caller-allocated return

Compiler có thể lower:

```text
make() -> LargeStruct
```

thành:

```text
caller provides return storage
callee initializes it
```

nếu ABI/optimization cho phép.

Đây là compiler freedom, không phải source-level semantics.

---

# 14. Closure

```axiom
let add = |a, b| a + b
```

Closure là function + captured environment nếu có.

Conceptually:

```text
Closure
├── code
└── environment
```

Nhưng compiler có thể loại bỏ environment hoàn toàn nếu closure không capture.

---

# 15. Non-capturing closure

```axiom
let f = |x| x + 1
```

có thể lower thành ordinary function pointer nếu ABI/context cho phép.

Không cần allocation.

---

# 16. Capturing closure

```axiom
let offset = 10

let add = |x| x + offset
```

Closure captures `offset`.

Compiler xác định capture mode.

---

# 17. Capture by value

Nếu closure cần ownership:

```axiom
move || use(resource)
```

thì ownership của `resource` được transfer vào closure.

Sau đó:

```text
resource = MOVED
```

---

# 18. Capture by view

Nếu closure chỉ đọc:

```axiom
|| inspect(data)
```

compiler có thể capture capability thay vì owner, nhưng chỉ khi lifetime của closure không vượt owner.

Nếu escape:

```text
owner
↓
closure
```

thì compiler phải chứng minh capability validity.

Nếu không chứng minh được:

```text
compile error
```

Không sinh lifetime syntax cho programmer.

---

# 19. Mutable capture

Nếu closure cần mutation:

```axiom
var counter = 0

let increment = || {
    counter = counter + 1
}
```

compiler phải tạo exclusive mutable access phù hợp.

Nếu closure escape hoặc chạy concurrent:

```text
ordinary mutable capture
```

không tự động trở thành thread-safe.

Phải dùng synchronization/atomic abstraction.

---

# 20. `move` closure

```axiom
move || use(data)
```

`move` là explicit ownership transfer vào closure.

Điều này rất hữu ích cho:

```text
thread spawn
async task
deferred callback
```

---

# 21. Closure type identity

Hai closure:

```axiom
let a = |x| x + 1
let b = |x| x + 1
```

không mặc định cùng concrete type.

Compiler tạo anonymous closure types.

Có thể coerce sang common function representation nếu semantics cho phép.

---

# 22. Closure ABI

Closure ABI nội bộ không stable.

Conceptually:

```text
closure
    data pointer
    call function
```

nhưng compiler có thể:

```text
inline
scalarize
specialize
remove environment
```

---

# 23. Function pointer

Function pointer là runtime value:

```text
fn(i32) -> i32
```

Có thể:

```axiom
let f = add
f(1, 2)
```

Function pointer không phải closure.

Closure có environment; function pointer không.

---

# 24. Closure to function pointer

Chỉ closure **không capture** mới có thể chuyển thành function pointer nếu type context cho phép.

Capturing closure không thể tự mất environment.

---

# 25. Dynamic callable abstraction

Nếu cần heterogeneous callable values:

```text
dyn Callable(...)
```

có thể được xây dựng bằng trait.

Không cần tạo "function object" primitive.

---

# 26. Recursion

Function có thể gọi chính nó:

```axiom
fn factorial(n: u64) -> u64 {
    if n == 0 {
        1
    } else {
        n * factorial(n - 1)
    }
}
```

Compiler không được giả định tail-call.

Nếu target/ABI cho phép, tail-call optimization có thể được thực hiện khi semantics không thay đổi.

---

# 27. Tail-call optimization

Nếu:

```axiom
fn f(...) {
    return g(...)
}
```

compiler có thể reuse stack frame.

Nhưng source program không được phụ thuộc vào:

```text
stack frame existence
```

trừ unsafe/debug/explicit introspection mechanisms.

---

# 28. `return`

`return expression`:

```text
evaluate expression
↓
cleanup live locals
↓
transfer ownership of return value
↓
return
```

---

# 29. `return` trong closure

Return bên trong closure trả về closure, không phải enclosing function.

```axiom
let f = |x| {
    if x < 0 {
        return 0
    }

    x
}
```

---

# 30. `break` / `continue`

`break` thoát loop.

`continue` chuyển đến next iteration.

Cả hai đều phải cleanup các local values không còn sống trước khi control-flow chuyển.

---

# 31. `defer` không có trong Core

Không thêm:

```text
defer
```

vào language core.

Cleanup đã được compiler quản lý bởi Drop.

Nếu cần arbitrary deferred action:

```text
scope guard
```

có thể được library xây dựng bằng Drop.

---

# 32. Function effect không implicit runtime feature

Axiom có thể internally track effects:

```text
IO
ALLOC
PANIC
ASYNC
ATOMIC
UNSAFE
```

nhưng v0.1 không biến toàn bộ effect system thành source annotation bắt buộc.

Compiler dùng effect facts cho:

- optimization
- diagnostics
- async legality
- comptime
- safety verification

---

# 33. Pure function không mặc định

Không mặc định:

```text
fn foo(...)
```

là pure.

Function có thể:

```text
IO
mutate
allocate
panic
```

nếu API/ownership cho phép.

Nếu cần compile-time execution, compiler kiểm tra capability/effect restrictions riêng.

---

# 34. `unsafe fn`

```axiom
unsafe fn read(ptr: *const u8) -> u8
```

caller phải explicit:

```axiom
unsafe {
    read(ptr)
}
```

Unsafe là semantic boundary.

---

# 35. Unsafe không thay đổi evaluation order

Ngay cả:

```axiom
unsafe {
    foo(a(), b())
}
```

vẫn:

```text
a()
↓
b()
↓
foo()
```

Unsafe chỉ thay đổi proof obligations cụ thể.

---

# 36. Panic trong expression

```axiom
let x = array[index]
```

Nếu index out of bounds:

```text
panic/trap
```

không phải undefined behavior trong safe code.

---

# 37. Evaluation order invariants

### AEXPR-20 — Evaluation Order Is Deterministic

### AEXPR-21 — Function Arguments Evaluate Left-To-Right

### AEXPR-22 — Receiver Evaluates Before Method Arguments

### AEXPR-23 — Binary Operands Evaluate Left-To-Right

### AEXPR-24 — Boolean Operators Short-Circuit

### AEXPR-25 — `if` Evaluates Exactly One Branch

### AEXPR-26 — Match Scrutinee Evaluates Once

### AEXPR-27 — Move Is An Ownership Transition

### AEXPR-28 — Copy Is Semantic Value Duplication

### AEXPR-29 — Return Transfers Owned Result

### AEXPR-30 — Return Cleanup Is Deterministic

### AEXPR-31 — Closure Capture Obeys Ownership Rules

### AEXPR-32 — Capturing Closure Cannot Outlive Its Captured Capability

### AEXPR-33 — `move` Closure Transfers Ownership

### AEXPR-34 — Mutable Closure Capture Requires Exclusive Access

### AEXPR-35 — Concurrent Closure Capture Must Satisfy Concurrency Contracts

### AEXPR-36 — Non-Capturing Closure May Erase To Function Pointer

### AEXPR-37 — Capturing Closure Does Not Implicitly Become Function Pointer

### AEXPR-38 — Closure ABI Is Compiler-Controlled

### AEXPR-39 — Tail-Call Optimization Is Semantics-Preserving

### AEXPR-40 — Unsafe Does Not Disable Evaluation Semantics

### AEXPR-41 — Safe Bounds Failure Is Defined

---

# Part XV — Statements · Loops · Control Flow · CFG

Tiếp theo, Axiom cần khóa **control-flow semantics** ở cấp compiler IR.

Đây là bước quan trọng vì từ đây có thể định nghĩa chính xác:

```text
Source
  ↓
AST
  ↓
HIR
  ↓
MIR CFG
```

mà không còn ambiguity về:

- `if` expression
- loop
- `break`
- `continue`
- `return`
- unreachable code
- definite initialization
- Drop trên mọi control-flow edge
- cleanup khi branch
- cleanup khi loop
- panic edge
- `?` edge
- `await` edge
- divergence (`never`)
- unreachable blocks

---

## 1. Control flow là graph

Ví dụ:

```axiom
if condition {
    foo()
} else {
    bar()
}

baz()
```

MIR conceptually:

```text
        condition
        /       \
      foo       bar
        \       /
          join
            |
           baz
            |
          return
```

Compiler không được dựa vào indentation/source order để suy luận cleanup.

---

## 2. Block expression

```axiom
let x = {
    let a = 10
    let b = 20
    a + b
}
```

Block có value:

```text
x = 30
```

---

## 3. Empty block

```axiom
{}
```

có type:

```text
unit
```

---

## 4. `if` expression

```axiom
let x =
    if condition {
        10
    } else {
        20
    }
```

Hai branch phải có compatible result type.

---

## 5. `if` không có else

```axiom
if condition {
    do_work()
}
```

Trong statement context:

```text
type = unit
```

Trong value context, nếu không có else:

```text
compile error
```

nếu compiler không thể coi kết quả là `unit`.

---

## 6. Loop

```axiom
while condition {
    work()
}
```

loop expression trong v0.1 có type:

```text
unit
```

Không có:

```text
break value
```

---

## 7. `break` không có value

```axiom
break
```

không:

```axiom
break 42
```

v0.1.

Điều này giữ CFG đơn giản.

---

## 8. `continue`

```axiom
while condition {
    if skip {
        continue
    }

    work()
}
```

Compiler phải cleanup local values trước khi quay lại loop header.

---

## 9. Loop cleanup

Ví dụ:

```axiom
while condition {
    let resource = acquire()

    if done {
        break
    }

    use(resource)
}
```

Nếu `break`:

```text
resource
↓
Drop
↓
exit loop
```

Không được leak.

---

## 10. Continue cleanup

```axiom
while condition {
    let resource = acquire()

    if skip {
        continue
    }
}
```

`resource` phải được drop trước next iteration.

---

## 11. Return cleanup

```axiom
fn f() -> i32 {
    let resource = acquire()

    return 10
}
```

semantic:

```text
evaluate 10
↓
Drop(resource)
↓
return 10
```

---

## 12. Panic cleanup

Nếu panic strategy là unwind:

```text
panic
↓
cleanup owned resources
↓
unwind
```

Nếu abort:

```text
panic
↓
terminate
```

và runtime tối thiểu có thể không cần unwind machinery.

---

## 13. `never`

```axiom
fn fail() -> never {
    panic("fail")
}
```

`never` có thể coerce vào mọi expected control-flow type vì expression không hoàn thành bình thường.

Ví dụ:

```axiom
let x: i32 = if condition {
    10
} else {
    fail()
}
```

hợp lệ.

---

## 14. Unreachable

Sau:

```axiom
return
```

code tiếp theo unreachable.

Compiler có thể:

```text
error
warning
```

Quyết định:

> **Unreachable code do control-flow chắc chắn kết thúc nên là diagnostic warning mặc định, không phải semantic error.**

Nhưng code không được ảnh hưởng runtime semantics vì không bao giờ thực thi.

---

## 15. Definite initialization

Compiler phải chứng minh variable được initialize trước use.

Sai:

```axiom
let x: i32
print(x)
```

→ compile error.

---

## 16. Branch initialization

```axiom
let x: i32

if condition {
    x = 10
} else {
    x = 20
}

print(x)
```

có thể hợp lệ nếu Axiom cho phép declaration-before-assignment.

Tuy nhiên để giữ language đơn giản, **khuyến nghị v0.1 không cho uninitialized local `let`**.

Dùng:

```axiom
let x =
    if condition { 10 }
    else { 20 }
```

hoặc:

```axiom
var x = 0
```

Do đó:

> `let` phải được initialize tại declaration.

---

## 17. `var`

```axiom
var x = 0
x = 10
```

`var` luôn initialized.

Không có uninitialized safe local.

Unsafe/system code có thể dùng uninitialized storage primitive nếu thật sự cần.

---

## 18. Why this matters

Điều này loại bỏ một lớp lớn:

```text
definite initialization analysis
```

khỏi programmer-visible semantics.

Compiler vẫn có thể có internal uninitialized MIR state cho:

- stack slots
- aggregate construction
- ABI return buffers
- optimization

nhưng source language không expose nó.

---

# 19. Partial struct initialization

Source:

```axiom
let p = Point {
    x: 10,
    y: 20
}
```

luôn fully initialized.

Không có:

```axiom
Point {
    x: 10
}
```

với `y` tự động zero.

---

# 20. Array initialization

```axiom
let a = [0; 1024]
```

là explicit initialization.

Không có implicit uninitialized safe array.

---

# 21. CFG merge

Nếu:

```axiom
if condition {
    ...
} else {
    ...
}
```

mọi ownership state tại join phải compatible.

Compiler phải merge:

```text
OWNED
MOVED
PARTIAL
DROPPED
```

theo dataflow rules.

Nếu một path move value nhưng path khác không:

```text
subsequent use
```

có thể trở thành invalid nếu không có common valid state.

---

# 22. Example

```axiom
let x = get()

if condition {
    consume(x)
}

use(x)
```

Compiler reject vì:

```text
path A: x = MOVED
path B: x = OWNED
join: incompatible
```

---

# 23. Conditional ownership

Có thể rewrite:

```axiom
let x = get()

if condition {
    consume(x)
}
```

thành:

```axiom
if condition {
    let x = get()
    consume(x)
} else {
    let x = get()
    use(x)
}
```

nhưng compiler không tự rewrite source semantics kiểu này.

Programmer phải làm rõ ownership boundary.

---

# 24. Drop at CFG join

Nếu value vẫn owned trên tất cả paths:

```text
join
↓
drop once
```

Nếu moved trên một path:

```text
drop only on paths where still owned
```

MIR phải biểu diễn rõ.

---

# 25. `DROP_IF_OWNED`

Đây là lý do MIR của Axiom cần instruction:

```text
DROP_IF_OWNED
```

hoặc equivalent ownership-aware cleanup lowering.

Ví dụ:

```text
path A:
    x = OWNED
    DROP x

path B:
    x = MOVED
    no drop
```

---

# 26. `?` control flow

```axiom
let x = foo()?
bar(x)
```

CFG:

```text
foo
 |
 +---- Ok ---> x → bar
 |
 +---- Err --> cleanup → return
```

Cleanup trên error edge bắt buộc.

---

# 27. `break` control-flow edge

Loop:

```text
header
  |
 body
  |
  +---- continue ---> header
  |
  +---- break ------> exit
```

Mỗi edge có cleanup set riêng.

---

# 28. `continue` và capability

Nếu:

```axiom
while condition {
    let v = mut_view(buffer)

    continue
}
```

capability `v` phải kết thúc trước continue.

Không được mang mutable capability sang iteration mới.

---

# 29. Loop-carried values

Compiler có thể internally tạo phi nodes:

```text
x₀
 ↓
loop
 ↓
x₁
 ↘
```

nhưng source language không cần phi syntax.

---

# 30. `for`

```axiom
for x in items {
    use(x)
}
```

semantic lowering conceptually:

```text
iterator = items.into_iterator()

while true {
    match iterator.next() {
        Some(x) => ...
        None => break
    }
}
```

Đây là semantic model.

Compiler có thể lower trực tiếp mà không tạo iterator object runtime nếu optimization cho phép.

---

# 31. Iterator ownership

`for` phải xác định rõ:

```text
iterate owned collection
```

có thể consume collection.

Ví dụ:

```axiom
for x in vector {
    ...
}
```

có thể move vector vào iterator.

Trong khi:

```axiom
for x in view(vector) {
    ...
}
```

chỉ đọc.

---

# 32. Mutable iteration

```axiom
for x in mut_view(vector) {
    modify(x)
}
```

mỗi iteration có mutable capability phù hợp.

Compiler phải đảm bảo capability của iteration trước kết thúc trước iteration tiếp theo nếu cần.

---

# 33. Nested loops

```axiom
while a {
    while b {
        if done {
            break
        }
    }
}
```

`break` chỉ thoát loop gần nhất.

Không có labeled break trong v0.1 trừ khi sau này chứng minh cần thiết.

Nếu cần nested-loop exit:

```axiom
return
```

hoặc helper function.

---

# 34. `match` trong loop

Mọi cleanup của match arm phải hoàn thành trước control-flow chuyển:

```text
match
 ↓
arm
 ↓
cleanup
 ↓
continue/break/normal
```

---

# 35. Async suspension

`.await` tạo control-flow suspension point.

Mọi local sống qua suspension phải được đưa vào async state machine.

Nhưng:

```text
view<T>
mut_view<T>
```

không được sống qua `.await` trong v0.1.

Do đó async state machine chỉ giữ:

```text
owned values
```

hoặc các explicitly allowed async-safe state.

---

# 36. Panic edge trong CFG

Mỗi potentially panicking operation conceptually có exceptional edge:

```text
normal continuation
panic/trap
```

Optimizer có thể outline panic path.

---

# 37. Bounds check

```axiom
array[i]
```

MIR:

```text
bounds_check(i, len)
↓
load
```

Nếu compiler chứng minh:

```text
0 <= i < len
```

có thể xóa check.

---

# 38. Bounds check không được biến thành UB

Nếu compiler không chứng minh:

```text
bounds safe
```

thì giữ check.

Không được bỏ check chỉ vì "likely safe".

---

# 39. CFG và optimizer

Optimizer có quyền:

```text
merge blocks
split blocks
hoist computations
sink computations
remove branches
vectorize
inline
tail-call
```

nhưng phải bảo toàn:

- evaluation order observable
- side effects
- ownership cleanup
- panic/trap behavior
- atomic ordering
- volatile
- FFI contracts

---

# 40. Control-flow invariants

### ACFG-20 — Control Flow Is Represented As A Graph

### ACFG-21 — `let` Is Always Initialized

### ACFG-22 — Safe Locals Are Never Uninitialized

### ACFG-23 — Every Exit Edge Performs Required Cleanup

### ACFG-24 — `break` Performs Required Cleanup

### ACFG-25 — `continue` Performs Required Cleanup

### ACFG-26 — `return` Performs Required Cleanup

### ACFG-27 — Panic Cleanup Depends On Panic Strategy

### ACFG-28 — Ownership State Must Agree At CFG Joins

### ACFG-29 — Partial Move State Is Dataflow-Tracked

### ACFG-30 — `?` Creates Explicit Success/Error Control Flow

### ACFG-31 — Loop-Carried Ownership Is Verified

### ACFG-32 — `for` Preserves Iterator Ownership Semantics

### ACFG-33 — Match Arm Cleanup Completes Before Control Transfer

### ACFG-34 — Await Cannot Preserve Ordinary Views In v0.1

### ACFG-35 — Potential Bounds Failure Is Defined

### ACFG-36 — Bounds Checks May Be Eliminated Only When Proven

### ACFG-37 — `never` Is Diverging Control Flow

### ACFG-38 — Unreachable Code Cannot Affect Runtime Semantics

### ACFG-39 — Optimized CFG Must Preserve Observable Semantics

### ACFG-40 — Safe Source Has No Uninitialized Local State

---

# Trạng thái sau Part XV

Đến đây Axiom đã khóa khá sâu phần **front-end semantic core**:

```text
                    AXIOM
                      │
       ┌──────────────┼──────────────┐
       │              │              │
     Types         Behavior       Control Flow
       │              │              │
   struct/enum      trait          if/match
   tuple            generic        loops
   Option/Result    closure        return
   Copy/Drop        dyn Trait      break
       │              │              │
       └──────────────┼──────────────┘
                      │
                Ownership
                      │
             view / mut_view
                      │
                  Capability
                      │
                   MIR CFG
```

Điểm quan trọng là các phần này **không tạo nhiều hệ thống độc lập**.

Ví dụ:

```text
match
 ↓
pattern
 ↓
move
 ↓
ownership state
 ↓
Drop
 ↓
CFG edge
```

hay:

```text
trait
 ↓
method resolution
 ↓
generic constraint
 ↓
static/dynamic dispatch
 ↓
ABI
```

đều nối vào cùng semantic model.

---

# Part XVI — Async · Futures · Coroutines · Cancellation

Phần kế tiếp cần khóa một chủ đề rất dễ làm một ngôn ngữ trở nên nặng nề:

> **async không được biến thành một runtime bắt buộc.**

Axiom sẽ phân biệt hoàn toàn:

```text
async language semantics
≠
executor
≠
thread
≠
OS event loop
≠
network runtime
```

Và cần khóa:

```text
Future semantics
state machine lowering
.await
suspension
owned values across await
view/mut_view restriction
Send across await
drop Future
cancellation
structured concurrency
executor
waker
poll
pin/stable address
async Drop
panic in async
Result + async
GPU async event
FFI async boundary
```

Đặc biệt sẽ phải giải quyết dứt điểm câu hỏi:

> **Axiom có cần `Pin`/pinning như Rust không, hay compiler/state-machine lowering có thể loại bỏ hoàn toàn khái niệm này khỏi source language?**

Hướng hiện tại của Axiom là **không đưa `Pin<T>` vào Core**; stable address chỉ tồn tại khi storage contract yêu cầu. Điều này phù hợp trực tiếp với nguyên tắc:

> **Compiler Complexity Is Not Language Complexity.**