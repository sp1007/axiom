Tiếp tục **Consistency Pass v0.1**. Lần này tôi sẽ không thêm feature mới; mục tiêu là tìm chỗ mà các luật hiện tại **đụng nhau hoặc tạo hành vi khó hiểu**.

# AXIOM Consistency Pass v0.1

Ta dùng cùng một nguyên tắc kiểm tra:

> **Source → AST → HIR → Type Check → Ownership/View → Concurrency → Drop → Verified MIR**

Nếu một chương trình không thể đi xuyên qua pipeline này với semantics rõ ràng, spec hiện tại chưa đủ chặt.

---

# 1. Hello World

```axiom
fn main() {
    println("Hello, world!")
}
```

Giả sử `println` là library function:

```axiom
fn println(text: view<Text>)
```

Compiler thấy:

```text
"Hello, world!"
      ↓
Text literal
      ↓
temporary Text
      ↓
view<Text>
      ↓
println()
      ↓
temporary destroyed
```

Không có heap allocation bắt buộc.

### MIR khái niệm

```text
t0 = CONST_TEXT "Hello, world!"
t1 = VIEW t0
CALL println(t1)
DROP t0
RETURN ()
```

### Kết luận

Không có vấn đề.

Nhưng có một điểm cần đóng đinh:

> **Temporary chỉ cần sống đủ lâu để hoàn thành full-expression chứa nó.**

Không được biến thành lifetime kiểu C++ mà programmer phải suy nghĩ.

Thêm:

**AOWN-61 — Temporary Lifetime Is Compiler-Managed**

Temporary value sống đến thời điểm tối thiểu cần thiết để hoàn thành semantic operation; compiler có thể rút ngắn lifetime nếu không quan sát được.

---

# 2. Struct + value semantics

```axiom
struct Point {
    x: i32
    y: i32
}

fn main() {
    let a = Point { x: 10, y: 20 }
    let b = a
}
```

`Point` mặc định có thể là `Copy` nếu tất cả field phù hợp.

```text
a ──COPY──> b
```

Không có alias.

Nếu:

```axiom
struct Buffer {
    data: Vec<u8>
}
```

thì:

```axiom
let a = Buffer { ... }
let b = a
```

là move.

```text
a: OWNED
       │
       └── MOVE ──> b: OWNED

a: MOVED
```

### Điểm quan trọng

Không được để syntax:

```axiom
let b = a
```

thay đổi ý nghĩa tùy compiler optimization.

Ví dụ compiler có thể nhận thấy `a` không dùng nữa và thực hiện physical move bằng cách reuse register/memory.

Đó chỉ là optimization.

Semantic vẫn là:

```text
Copy type → copy semantics
Move type → move semantics
```

Thêm invariant:

**AOWN-62 — Physical Movement Does Not Define Semantic Move**

---

# 3. Method syntax

Ta có:

```axiom
struct Vec2 {
    x: f32
    y: f32
}

fn length(self: view<Vec2>) -> f32 {
    sqrt(self.x * self.x + self.y * self.y)
}
```

Gọi:

```axiom
let v = Vec2 { x: 3.0, y: 4.0 }
let x = v.length()
```

Compiler desugar:

```axiom
length(view(v))
```

Đây là điểm rất tốt vì method không phải primitive compiler concept.

---

## 3.1 Method làm mutation

```axiom
fn normalize(self: mut_view<Vec2>) {
    ...
}
```

Gọi:

```axiom
var v = Vec2 { ... }
v.normalize()
```

Compiler:

```text
v
 ↓
MUT_VIEW
 ↓
normalize()
```

Trong thời gian call:

```text
v = WRITE capability
```

Không được có:

```axiom
let r = view(v)
v.normalize()
use(r)
```

nếu `r` còn sống sau mutation.

Compiler có thể biết `r` đã last-use trước `normalize()` thì cho phép:

```axiom
let r = view(v)
println(r)
v.normalize()
```

Đây chính là:

> lifetime của capability ≠ lifetime của owner.

### Kết luận

Semantics hiện tại nhất quán.

---

# 4. Field access — phát hiện vấn đề quan trọng

Đây là chỗ tôi muốn sửa spec rõ hơn.

Có:

```axiom
struct Config {
    path: Text
}
```

và:

```axiom
fn load(config: view<Config>) {
    File.open(config.path)
}
```

`config` là view.

`config.path` **không được move `Text` ra khỏi Config**.

Nếu không, programmer có thể vô tình lấy ownership từ một non-owning view.

### Quy tắc mới

Field access phụ thuộc vào **capability của base expression**.

| Base | Field access |
|---|---|
| owned `T` | có thể READ / MOVE |
| `view<T>` | READ view/value |
| `mut_view<T>` | READ hoặc WRITE capability |
| raw pointer | unsafe dereference |

Ví dụ:

```axiom
let config: Config = ...
let path = config.path
```

Nếu `Text` non-Copy:

```text
config.path → MOVE
```

`config` trở thành partially moved.

Nhưng:

```axiom
let config: view<Config> = ...
let path = config.path
```

phải trở thành:

```text
config.path
   ↓
view<Text>
```

hoặc một read operation thích hợp nếu API yêu cầu value.

Không được tạo owning `Text`.

---

# 5. View → field → nested field

Ví dụ:

```axiom
struct User {
    profile: Profile
}

struct Profile {
    name: Text
}
```

```axiom
fn print_name(user: view<User>) {
    println(user.profile.name)
}
```

Compiler phải truyền capability:

```text
view<User>
    ↓
view<Profile>
    ↓
view<Text>
```

Không cần tạo object tạm.

MIR có thể đơn giản là:

```text
VIEW_FIELD user.profile
VIEW_FIELD profile.name
CALL println
```

Optimizer có thể biến thành một pointer+offset operation.

### Thêm invariant

**AVIEW-19 — Capability-Preserving Field Projection**

Field projection từ `view<T>` hoặc `mut_view<T>` không tạo ownership mới; nó tạo capability phù hợp trên vùng field.

---

# 6. Partial Move

Ví dụ:

```axiom
struct User {
    name: Text
    age: i32
}
```

```axiom
var u = User {
    name: "Alice",
    age: 20
}

let name = u.name
println(u.age)
```

`Text` non-Copy.

Sau:

```axiom
let name = u.name
```

state:

```text
u:
    name → MOVED
    age  → OWNED
```

Do đó:

```axiom
println(u.age)
```

hợp lệ.

Nhưng:

```axiom
println(u.name)
```

không hợp lệ.

Và:

```axiom
println(u)
```

cũng không hợp lệ vì toàn bộ `u` không còn fully-owned.

---

# 7. Partial Move + Drop

Đây là nơi semantics Drop phải thật chính xác.

```axiom
struct User {
    name: Text
    file: File
}
```

Giả sử cả hai đều `Drop`.

```axiom
var u = User {
    name: ...,
    file: ...
}

let name = u.name
```

Khi scope kết thúc:

```text
u.name → MOVED
u.file → OWNED
```

Compiler **không được Drop `u.name` lần nữa**.

Nó phải tạo:

```text
DROP u.file
```

chứ không phải:

```text
DROP u
```

nếu implementation của `Drop` có semantics phụ thuộc toàn bộ object.

Đây dẫn tới một quy tắc quan trọng.

---

## 7.1 User-defined Drop và partial move

Nếu Axiom cho phép:

```axiom
impl Drop for User {
    fn drop(self: ...) { ... }
}
```

thì partial move trở nên phức tạp.

Vì:

```text
u.name moved
u.file alive
```

nhưng `Drop(User)` có thể muốn truy cập `name`.

Do đó tôi đề xuất **v0.1 đóng luật này như sau**:

### Quy tắc

Một type có user-defined `Drop`:

> **không được phép partial-move field trực tiếp.**

Ví dụ:

```axiom
let name = u.name
```

sẽ bị từ chối nếu `User` có custom Drop.

Nhưng field có thể được lấy thông qua view:

```axiom
let name = view(u.name)
```

nếu API phù hợp.

Điều này đơn giản hơn rất nhiều cho compiler và programmer.

Các type chỉ có compiler-derived destruction vẫn cho partial move bình thường.

---

### Vì sao đây là lựa chọn tốt?

Nếu cố cho phép cả hai:

```text
custom Drop
+
partial move
```

compiler phải sinh "partial destructor state machine":

```text
drop(User,
     name_alive = false,
     file_alive = true,
     ...)
```

Điều đó làm semantics Drop phức tạp không cần thiết.

Axiom đang hướng tới:

> **compiler mạnh, syntax đơn giản**

nên không đáng để đưa complexity này ra toàn hệ thống.

Thêm:

**ADROP-12 — User Drop Types Forbid Partial Move**

**ADROP-13 — Compiler-Derived Drop Types May Support Partial Move**

**ADROP-14 — Moved Fields Are Never Dropped**

---

# 8. `view` không phải reference syntax

Một điểm khác cần đóng đinh.

Không nên có:

```axiom
ref<T>
& T
&T
borrow<T>
```

ở surface language.

Chỉ có:

```axiom
view<T>
mut_view<T>
```

Điều này khiến programmer chỉ phải hiểu hai khái niệm:

```text
T         ownership/value
view<T>   read capability
mut_view<T> write capability
```

Compiler vẫn có thể có nội bộ:

```text
BorrowRegion
Lifetime
Provenance
AliasSet
```

nhưng đó là compiler machinery.

Đúng với nguyên tắc:

> **Compiler Complexity Is Not Language Complexity.**

---

# 9. Generic

```axiom
fn first<T>(items: view<T>) -> T {
    items[0]
}
```

Ở đây có một vấn đề:

`view<T>` chỉ cung cấp read access.

Nhưng return `T` yêu cầu tạo một value.

Điều đó chỉ hợp lệ nếu `T: Copy`.

Do đó:

```axiom
fn first<T: Copy>(items: view<T>) -> T {
    items[0]
}
```

hoặc API phải trả:

```axiom
fn first<T>(items: view<T>) -> view<T>
```

nếu semantic muốn trả capability.

Như vậy compiler không được âm thầm biến:

```text
view<T>
```

thành:

```text
owned T
```

cho non-Copy type.

### Quy tắc

**AVIEW-20 — View Cannot Produce Ownership Without A Valid Copy/Clone Operation**

Nếu `T: Copy`:

```text
view<T> → copied T
```

Nếu không:

```text
view<T> → view<T>
```

hoặc explicit:

```text
clone(...)
```

---

# 10. `Vec<T>` — relocation

Đây là test rất quan trọng với memory model.

```axiom
var v = Vec<i32>()
v.push(10)

let x = view(v)
v.push(20)
```

Nếu `push(20)` cần relocate buffer thì `x` sẽ dangling.

Axiom không thể chỉ nói:

> "Vec có thể relocate."

Mà phải có compile-time rule.

### Trường hợp 1

```axiom
let x = view(v)
println(x)
v.push(20)
```

Compiler thấy:

```text
x last-use
   ↓
before push
```

=> hợp lệ.

### Trường hợp 2

```axiom
let x = view(v)
v.push(20)
println(x)
```

`push` có thể relocate.

=> compiler phải reject, hoặc API phải chứng minh operation không relocate.

---

## 10.1 `reserve`

Không nên coi:

```axiom
v.reserve(1000)
```

là:

> "Từ đây pointer/view sẽ luôn stable."

Reserve chỉ là capacity guarantee.

Nếu storage contract cần stable address:

```text
Box
Pool
Arena
StableVec
Handle
```

phải là abstraction khác.

Đây là một điểm rất quan trọng vì nó giữ cho `Vec` implementation tự do.

---

# 11. `Vec` + `mut_view`

Ví dụ:

```axiom
var v = Vec<i32>()

fn modify(x: mut_view<i32>) {
    x[0] = 100
}

modify(mut_view(v))
v.push(20)
```

Sau khi `modify` return:

```text
mut_view capability → expired
```

nên `push` được phép.

Nhưng:

```axiom
let x = mut_view(v)
v.push(20)
use(x)
```

phải bị reject.

Đây là cùng một rule, không cần rule riêng cho Vec.

> **Relocation là một dạng mutation làm thay đổi validity của dependent capability.**

---

# 12. Kết quả của Consistency Pass #1

Sau 12 test đầu tiên, tôi thấy memory/ownership model hiện tại **không cần thay đổi kiến trúc**, nhưng cần thêm các quy tắc chính thức:

### Ownership

**AOWN-61** — Temporary Lifetime Is Compiler-Managed  
**AOWN-62** — Physical Movement Does Not Define Semantic Move

### View

**AVIEW-19** — Capability-Preserving Field Projection  
**AVIEW-20** — View Cannot Produce Ownership Without Valid Copy/Clone

### Drop

**ADROP-12** — User Drop Types Forbid Partial Move  
**ADROP-13** — Compiler-Derived Drop Types May Support Partial Move  
**ADROP-14** — Moved Fields Are Never Dropped

### `Vec` / relocation

Các invariant AMEM-22/23/24 đã có đủ nền tảng:

```text
relocatable storage
       +
active dependent view
       ↓
relocation forbidden while capability is live
```

Không cần một `Pin` primitive.

---

# 13. Một kết luận kiến trúc khá quan trọng

Sau consistency pass này, mô hình Axiom đang hình thành rất rõ:

```text
             VALUE
               │
        ┌──────┴──────┐
        │             │
     OWNED          COPY
        │
        │
   ┌────┴─────┐
   │          │
 MOVE       DROP
   │
   ▼
 MOVED

OWNED
  │
  ├── view<T>       READ capability
  │
  └── mut_view<T>   WRITE capability
```

Và:

```text
Storage
  │
  ├── relocatable
  ├── stable
  ├── arena
  ├── pool
  ├── static
  ├── TLS
  ├── external
  └── device
```

**Hai trục này độc lập.**

Đây chính là điểm khiến Axiom tránh được một lượng lớn complexity của các language khác:

> **Ownership không quyết định storage.  
> Storage không quyết định syntax.  
> View biểu diễn capability, không phải một kiểu "con trỏ nâng cao".**

---

# 14. Tiếp tục consistency pass

Nhóm tiếp theo sẽ kiểm tra những chỗ dễ phá vỡ model này hơn:

```text
13. Result + ?
14. Result + Drop
15. async + view
16. async + owned state
17. spawn + closure capture
18. Send / Share
19. MutexGuard → view/mut_view
20. Channel ownership
21. Atomic + aliasing
22. unsafe pointer → view
23. FFI ownership
24. extern C + Drop
25. comptime + ownership
26. recursive Box
27. Handle + generation
28. dyn Trait
29. public API + private type
30. impl Trait
```

Đặc biệt **async + view + Send + Drop** sẽ là bài test khó nhất, vì nếu thiết kế không chặt ở đây thì toàn bộ ownership model có thể phát sinh ngoại lệ.