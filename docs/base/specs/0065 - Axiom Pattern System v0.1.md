Tiếp tục với **Pattern Matching + ADT + Destructuring**. Đây là một bài test rất tốt cho toàn bộ thiết kế hiện tại của Axiom: type system, ownership, partial move, Drop, region và MIR.

# Axiom Pattern System v0.1

Tôi đề xuất nguyên tắc:

> **Pattern chỉ là cách phân rã giá trị; nó không tạo ra một hệ thống object/lifetime mới.**

Có 4 nhóm pattern chính:

```text
Pattern
├── Literal
├── Binding
├── Tuple / Struct
├── Enum
└── Wildcard
```

Sau này có thể thêm range, OR-pattern, guard.

---

# 1. Binding pattern

```axiom
let x = 42;
```

`x` là binding pattern.

Trong:

```axiom
match value {
    x => ...
}
```

`x` có nghĩa:

```text
match mọi giá trị
↓
bind toàn bộ value vào x
```

Không phải wildcard.

---

# 2. Wildcard

```axiom
match result {
    Ok(x) => x,
    _ => 0,
}
```

`_`:

```text
match
↓
không bind
↓
không tạo ownership mới
```

Đây là khác biệt quan trọng với:

```axiom
x => ...
```

---

# 3. Tuple destructuring

```axiom
let point = (10, 20);

let (x, y) = point;
```

Nếu tuple là Copy:

```text
point
 ├── x copy
 └── y copy
```

Nếu chứa resource:

```axiom
let x = (file, socket);
let (f, s) = x;
```

thì đây là **move/destructure**, không phải copy.

---

# 4. Partial move qua pattern

Ví dụ:

```axiom
struct User {
    name: Text
    file: File
}

let user = get_user();

let User { name, .. } = user;
```

Nếu `name` là non-Copy:

```text
user
├── name  → MOVED
└── file  → OWNED
```

Sau đó:

```axiom
use(name);
use(user.file);
```

có thể hợp lệ.

Nhưng:

```axiom
use(user);
```

→ lỗi vì `user` đã **PARTIAL**.

Điều này hoàn toàn khớp ownership tree hiện tại.

---

# 5. Struct pattern

Ví dụ:

```axiom
struct Point {
    x: i64
    y: i64
}
```

Có thể:

```axiom
let Point { x, y } = p;
```

hoặc:

```axiom
let Point { x, .. } = p;
```

hoặc:

```axiom
let Point { x: px, y: py } = p;
```

Tên binding khác tên field:

```text id="r7y3p1"
field x
   ↓
binding px
```

---

# 6. Enum pattern

Ví dụ:

```axiom
enum Option<T> {
    Some(T),
    None
}
```

Pattern:

```axiom
match value {
    Some(x) => use(x),
    None => fallback(),
}
```

Compiler biết:

```text
Some
 └── payload T

None
 └── no payload
```

---

# 7. Ownership trong enum

Đây là phần quan trọng.

```axiom
let x: Option<File> = Some(file);
```

ownership:

```text
Option<File>
└── Some
     └── File OWNED
```

Sau:

```axiom
match x {
    Some(f) => use(f),
    None => ...
}
```

branch `Some`:

```text
x.Some.File
      ↓
     MOVE
      ↓
      f
```

Sau đó `x` không còn sở hữu `File`.

Compiler phải tránh:

```text
drop(f)
drop(x.Some.File)
```

hai lần.

---

# 8. Match không được làm mất ownership information

Một lỗi thiết kế dễ xảy ra là compiler lowering:

```text
match enum
↓
switch tag
```

rồi quên semantic ownership.

Axiom phải làm:

```text
Typed HIR
   ↓
Pattern/Ownership analysis
   ↓
MIR
```

chứ không phải:

```text
Pattern
↓
switch
```

đơn thuần.

---

# 9. Match có thể move hoặc inspect

Tôi đề xuất compiler phân biệt:

```text
MATCH_READ
MATCH_MOVE
```

Ví dụ:

```axiom
match x {
    Some(_) => ...
    None => ...
}
```

Nếu `_` không cần payload:

```text
x
↓
inspect discriminant
```

không nhất thiết move payload.

Nhưng:

```axiom
match x {
    Some(v) => consume(v),
    None => ...
}
```

thì payload được move.

Đây là một optimization + ownership distinction rất quan trọng.

---

# 10. Có thể match bằng view

Ví dụ:

```axiom
fn inspect(v: view<Option<User>>) {
    match v {
        Some(user) => inspect_user(user),
        None => ...
    }
}
```

Ở đây không được move `User`.

Pattern phải tạo:

```text
view<User>
```

hoặc read capability tới payload.

Do đó pattern semantics phụ thuộc access mode của scrutinee:

```text
OWNED
READ VIEW
MUT VIEW
```

---

# 11. `mut_view` + pattern

Ví dụ:

```axiom
fn modify(v: mut_view<User>) {
    match v {
        User { age, .. } => {
            age = age + 1;
        }
    }
}
```

Compiler phải tạo:

```text
mut_view(age)
```

không move `age` khỏi User.

Vì vậy pattern destructuring không đồng nghĩa với move.

---

# 12. Đây là abstraction rất quan trọng

Có ba semantic operations:

```text id="q5p3zy"
DESTRUCTURE_MOVE
DESTRUCTURE_READ
DESTRUCTURE_WRITE
```

Ví dụ:

```text
Owned User
   │
   └── pattern
         │
         ├── move field
         ├── read field
         └── mutable access field
```

Compiler phải biết pattern đang làm gì.

---

# 13. Wildcard phải thực sự bỏ qua dữ liệu

Ví dụ:

```axiom
match user {
    User { name: _, .. } => ...
}
```

Không nên tạo:

```text
temporary name
```

nếu không cần.

Compiler có thể chỉ đọc/skip field.

Đây là một ví dụ nhỏ nhưng quan trọng cho mục tiêu zero-cost.

---

# 14. Exhaustiveness

Compiler phải chứng minh mọi trường hợp được xử lý.

Ví dụ:

```axiom
enum State {
    Idle,
    Running,
    Stopped
}
```

Nếu:

```axiom
match state {
    Idle => ...
    Running => ...
}
```

→ lỗi:

```text
AX_MATCH_0001
non-exhaustive pattern
missing: Stopped
```

---

# 15. Wildcard làm match exhaustive

```axiom
match state {
    Idle => ...
    _ => ...
}
```

→ exhaustive.

Nhưng compiler vẫn có thể cảnh báo pattern không thể xảy ra nếu biết statically.

---

# 16. Unreachable pattern

Ví dụ:

```axiom
match state {
    _ => 1,
    Idle => 2,
}
```

`Idle` không bao giờ tới.

Compiler có thể:

```text
warning AX_MATCH_0002
unreachable pattern
```

Không nhất thiết error trong v0.1, nhưng tôi nghiêng về warning mặc định.

---

# 17. OR-pattern

Có thể hỗ trợ:

```axiom
match state {
    Idle | Stopped => 0,
    Running => 1,
}
```

Semantic:

```text
Idle OR Stopped
      ↓
same arm
```

Nhưng binding phải đồng nhất.

Không cho:

```axiom
Some(x) | None => ...
```

vì branch thứ hai không có `x`.

Compiler báo:

```text
inconsistent bindings
```

---

# 18. Match guard

Sau này có thể:

```axiom
match x {
    Some(v) if v > 10 => ...
    Some(v) => ...
    None => ...
}
```

Guard là runtime condition.

Điểm quan trọng:

> **Guard không được dùng để chứng minh exhaustiveness.**

Ví dụ:

```axiom
match x {
    Some(v) if v > 10 => ...
}
```

vẫn không exhaustive vì `v <= 10` chưa được cover.

---

# 19. Range pattern

Có thể hỗ trợ:

```axiom
match x {
    0..=9 => digit(),
    10..=99 => two_digit(),
    _ => other(),
}
```

Compiler có thể lower thành:

```text
cmp
branch
```

hoặc jump table.

Nhưng range pattern nên chỉ cho các type có ordering semantics rõ ràng:

```text
integers
possibly char
```

Không nên tự động cho mọi type có `<`.

---

# 20. Pattern compilation

Compiler frontend:

```text
match expression {
    pattern => body
}
```

↓

Pattern matrix / decision tree:

```text
                    scrutinee
                       │
                     tag?
                  /    |    \
                Some  None  ...
                 │
               payload
```

↓

MIR:

```text
SWITCH
BRANCH
FIELD_PLACE
ENUM_TAG
ENUM_PAYLOAD
```

↓

Optimizer:

```text
jump table
branch chain
range check
CMOV
```

Tất cả đều không cần runtime pattern engine.

---

# 21. `match` expression

Tôi đề xuất `match` là expression:

```axiom
let x = match state {
    Idle => 0,
    Running => 1,
    Stopped => 2,
};
```

Type của toàn match phải thống nhất:

```text
arm1 : i64
arm2 : i64
arm3 : i64

match : i64
```

---

# 22. `never` giải quyết match rất đẹp

Ví dụ:

```axiom
let x = match state {
    Idle => 0,
    Running => calculate(),
    Stopped => panic("invalid"),
};
```

Types:

```text
Idle      → i64
Running   → i64
Stopped   → never
```

Result:

```text
match : i64
```

Không cần special case.

---

# 23. Unit match

Nếu tất cả branches không trả value:

```axiom
match event {
    Start => start(),
    Stop => stop(),
}
```

thì:

```text
match : unit
```

Compiler có thể eliminate result.

---

# 24. Pattern binding mutability

Tôi đề xuất binding tuân theo declaration semantics.

Ví dụ:

```axiom
let Point { x, y } = p;
```

`x`, `y` immutable.

Muốn mutable:

```axiom
var Point { x, y } = p;
```

hoặc syntax khác nếu sau này thấy cần.

Nhưng tôi không muốn pattern tự có modifier riêng kiểu:

```text
ref
ref mut
move
```

như một số ngôn ngữ.

Axiom cố gắng để:

```text
ownership mode
+
binding declaration
```

quyết định semantics.

---

# 25. `let` pattern và `match` pattern dùng cùng engine

Đây là quyết định kiến trúc rất đáng giá.

Không tạo:

```text
LetPatternCompiler
MatchPatternCompiler
```

riêng biệt.

Thay vào đó:

```text
Pattern AST
    ↓
Pattern Type Checker
    ↓
Pattern Ownership Analyzer
    ↓
Pattern Lowerer
```

Dùng cho:

```text
let
match
if let
while let
for
```

---

# 26. `if let`

Có thể có syntax sugar:

```axiom
if let Some(x) = value {
    use(x);
}
```

semantic:

```axiom
match value {
    Some(x) => { use(x); }
    _ => {}
}
```

Compiler không cần feature engine riêng.

---

# 27. `while let`

Tương tự:

```axiom
while let Some(x) = iterator.next() {
    use(x);
}
```

semantic:

```text
loop
 ↓
next()
 ↓
match
 ├── Some → body → loop
 └── None → exit
```

Đây là một abstraction rất hợp với Iterator.

---

# 28. `for`

`for` cũng nên là abstraction, không phải primitive machine loop duy nhất.

```axiom
for x in collection {
    use(x);
}
```

có thể lower thành Iterator protocol:

```text
loop {
    match iterator.next() {
        Some(x) => body,
        None => break,
    }
}
```

Sau monomorphization/inlining:

```text
for
 ↓
iterator abstraction
 ↓
machine loop
```

có thể hoàn toàn biến mất.

---

# 29. Nhưng array/vector nên có fast path

Compiler có thể nhận biết:

```axiom
for x in array {
}
```

và generate:

```text
index loop
```

nếu tốt hơn.

Đây là ví dụ:

> Library semantics trước, compiler optimization sau.

Không cần biến `for` thành một đống special-case syntax.

---

# 30. Pattern + partial move + Drop

Đây là test quan trọng nhất.

```axiom
struct User {
    name: Text
    file: File
    age: i32
}
```

Code:

```axiom
let user = get_user();

match user {
    User { name, .. } => {
        println(name);
    }
}
```

Nếu `name` là non-Copy:

```text
before match:

user
├── name  OWNED
├── file  OWNED
└── age   OWNED
```

Trong branch:

```text
user
├── name  MOVED → name
├── file  OWNED
└── age   OWNED
```

Sau branch:

```text
drop file
drop age
```

Không drop `name` qua `user`.

Nếu `name` cũng được drop:

```text
drop name
```

ở nơi nó hiện đang thuộc ownership.

Đây là **ownership relocation**, không phải copy.

---

# 31. Match trên borrowed view

```axiom
fn inspect(u: view<User>) {
    match u {
        User { name, age } => {
            print(name);
            print(age);
        }
    }
}
```

Không có ownership transfer:

```text
User
├── name READ
└── age READ
```

Capabilities chỉ tồn tại trong arm/scope cần thiết.

---

# 32. Match trên `mut_view`

```axiom
fn update(u: mut_view<User>) {
    match u {
        User { age, .. } => {
            age = age + 1;
        }
    }
}
```

Semantic:

```text
User
└── age WRITE
```

Không cần tạo một `User` mới.

Compiler có thể generate trực tiếp:

```text
load age
add 1
store age
```

---

# 33. Một invariant quan trọng được thêm

### APM-01 — Pattern Does Not Change Ownership Semantics

Pattern chỉ phân rã/quan sát/di chuyển capability; không tạo ownership model mới.

### APM-02 — Pattern Access Is Explicit Internally

Mọi binding pattern phải được phân loại:

```text
READ
MOVE
WRITE
```

### APM-03 — Exhaustive Match

Safe match phải cover mọi reachable constructor/value.

### APM-04 — No Double Drop Through Pattern

Moved/destructured fields không được drop từ owner cũ.

### APM-05 — Pattern Lowering Preserves Provenance

Destructured views vẫn giữ provenance của owner.

### APM-06 — Guard Does Not Prove Exhaustiveness

Runtime guard không được dùng để chứng minh pattern coverage.

### APM-07 — Pattern Abstraction Erasure

Pattern syntax không tồn tại trong final binary nếu không có observable consequence.

---

# 34. Sau phần này, tôi thấy mô hình Axiom đã có một tính chất rất tốt

Ta không có hàng loạt hệ thống độc lập:

```text
memory system
pattern memory system
async memory system
closure memory system
match memory system
```

mà tất cả đều dùng:

```text
                 TYPE
                   │
              PLACE / VALUE
                   │
             REGION / PROVENANCE
                   │
            CAPABILITY ACCESS
                   │
        ┌──────────┼───────────┐
       READ       WRITE       MOVE
        │           │           │
        └───────────┼───────────┘
                    │
               OWNERSHIP
                    │
                 DROP
```

Pattern chỉ tạo ra các `Place` mới.

Closure capture cũng tạo ra `Place`/capture state.

View cũng tạo capability.

Async chỉ kéo một số ownership state qua `SUSPEND`.

Concurrency chỉ kiểm tra capability khi crossing execution context.

Đây là kiến trúc tôi đánh giá rất đáng giữ.

---

# Bước tiếp theo

Tôi sẽ đi tiếp sang **Generic + Trait Solver v0.1 ở mức sâu hơn**, nhưng lần này không chỉ bàn syntax. Cần chốt 5 vấn đề có thể quyết định Axiom có bị phình thành C++ thứ hai hay không:

```text
1. Generic type inference
2. Trait constraint solving
3. Associated types
4. Operator overloading
5. Monomorphization vs code sharing
```

Đặc biệt tôi muốn thiết kế **trait solver bounded và deterministic**, để Axiom có generic mạnh nhưng **không trở thành một theorem prover**, đồng thời compiler vẫn có thể compile nhanh và AI agent có thể hiểu chính xác tại sao một generic call được hoặc không được.