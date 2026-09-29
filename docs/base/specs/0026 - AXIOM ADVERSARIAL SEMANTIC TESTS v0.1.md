Tiếp tục. Bây giờ nên làm **Adversarial Semantic Tests v0.1** — không phải test thông thường, mà là bộ test cố tình tìm ra những điểm yếu của mô hình Axiom trước khi viết verifier/backend.

Tôi đề xuất chia thành **10 nhóm**, khoảng 100–150 test lõi.

# AXIOM ADVERSARIAL SEMANTIC TESTS v0.1

Mục tiêu:

> Nếu Axiom vượt qua bộ test này, mô hình ownership/region/view/Drop/concurrency mới đáng tin để đóng băng tiếp.

---

## 1. Ownership cơ bản

### OWN-001 — move đơn

```axiom
let a = make_buffer()
let b = a
use(b)
```

Kỳ vọng:

```text
a → MOVED
b → OWNED
```

Accept.

---

### OWN-002 — use after move

```axiom
let a = make_buffer()
let b = a
use(a)
```

Reject:

```text
AX_OWN_USE_AFTER_MOVE
```

---

### OWN-003 — move twice

```axiom
let a = make_buffer()
let b = a
let c = a
```

Reject.

---

### OWN-004 — Copy không tạo move

```axiom
let a: i32 = 10
let b = a
let c = a
```

Accept.

```text
a = OWNED/COPYABLE
b = independent value
c = independent value
```

---

### OWN-005 — return ownership

```axiom
fn make() -> Buffer {
    let b = create()
    b
}
```

Kỳ vọng:

```text
b → MOVED_TO_RETURN
```

Không Drop `b` lần nữa.

---

# 2. Branching — nơi ownership thường bắt đầu nguy hiểm

### OWN-BRANCH-001

```axiom
let b = create()

if condition {
    consume(b)
}

use(b)
```

Phải reject nếu `condition` có thể true.

Trạng thái sau `if`:

```text
b = MAYBE_MOVED
```

Không được coi là OWNED.

---

### OWN-BRANCH-002

```axiom
let b = create()

if condition {
    consume(b)
} else {
    consume(b)
}
```

Accept.

Bởi mọi path đều consume.

```text
join:
b = MOVED
```

---

### OWN-BRANCH-003

```axiom
let b = create()

if condition {
    consume(b)
}

drop(b)
```

Reject.

---

### OWN-BRANCH-004

```axiom
let b = create()

if condition {
    return b
}

consume(b)
```

Accept.

Path return chuyển ownership cho caller.

Path còn lại consume.

---

# 3. Loop — bài test cực quan trọng

### OWN-LOOP-001

```axiom
let b = create()

while condition {
    consume(b)
}

use(b)
```

Reject.

Vì vòng lặp có thể chạy 0 lần hoặc nhiều lần.

---

### OWN-LOOP-002

```axiom
while condition {
    let b = create()
    consume(b)
}
```

Accept.

Mỗi iteration tạo ownership mới.

---

### OWN-LOOP-003

```axiom
let b = create()

while condition {
    let x = b
}
```

Reject vì iteration thứ hai có thể dùng `b` sau move.

---

### OWN-LOOP-004

```axiom
let b = create()

loop {
    consume(b)
    break
}
```

Accept.

Verifier phải hiểu `break` là terminating path.

---

# 4. Partial Move

Đây là nhóm tôi đặc biệt muốn Axiom kiểm tra kỹ.

```axiom
struct User {
    name: String
    age: i32
}
```

### PARTIAL-001

```axiom
let user = make_user()
let name = user.name

print(user.age)
```

Accept.

Trạng thái:

```text
user
├── name = MOVED
└── age  = OWNED
```

---

### PARTIAL-002

```axiom
let user = make_user()
let name = user.name

use(user)
```

Reject.

`user` không còn là whole value hợp lệ.

---

### PARTIAL-003

```axiom
let user = make_user()
let name = user.name

drop(user)
```

Accept về mặt semantics, nhưng Drop chỉ xử lý phần còn sở hữu.

```text
DROP user.age
```

Không Drop `name`.

---

### PARTIAL-004

```axiom
let user = make_user()
let name = user.name

let age = user.age
```

Accept.

Hai field độc lập.

---

### PARTIAL-005

Nested:

```axiom
struct A {
    b: B
}

struct B {
    x: String
    y: String
}
```

```axiom
let a = make()
let x = a.b.x
use(a.b.y)
```

Accept.

Region:

```text
a.b.x
a.b.y
```

DISJOINT.

Đây là test để đảm bảo region system không chỉ hoạt động ở một cấp.

---

# 5. Field aliasing

### REGION-001

```axiom
fn f(p: mut_view<Person>) {
    write(p.name)
    write(p.age)
}
```

Accept.

Vì:

```text
Person.name
Person.age
```

disjoint.

---

### REGION-002

```axiom
fn f(p: mut_view<Person>) {
    write(p)
    read(p.age)
}
```

Reject.

Whole-object WRITE chứa field READ.

---

### REGION-003

```axiom
fn f(p: view<Person>) {
    read(p.name)
    read(p.age)
}
```

Accept.

---

### REGION-004

```axiom
fn f(p: mut_view<Person>) {
    write(p.name)
    write(p.name)
}
```

Reject nếu hai mutable capabilities cùng sống đồng thời.

Nhưng:

```axiom
write(p.name)
write(p.name)
```

theo tuần tự, không tạo hai view sống đồng thời, có thể Accept.

Điều này buộc verifier phân biệt:

```text
simultaneous capability
```

với:

```text
sequential access
```

---

# 6. View lifetime

Đây sẽ là nhóm quyết định Axiom có thực sự đạt được mục tiêu “không cần borrow checker syntax” hay không.

### VIEW-001

```axiom
let buffer = create()
let v = view(buffer)
use(v)
```

Accept.

---

### VIEW-002

```axiom
let v

{
    let buffer = create()
    v = view(buffer)
}

use(v)
```

Reject.

View outlives owner.

---

### VIEW-003

```axiom
fn get_view(buffer: Buffer) -> view<u8> {
    view(buffer)
}
```

Reject.

Owner bị mất khi function return.

Trừ khi API semantics khác được định nghĩa.

---

### VIEW-004

```axiom
fn get_view(buffer: view<u8>) -> view<u8> {
    buffer
}
```

Accept.

Provenance được truyền tiếp.

---

# 7. View + Vec reallocation

**Đây là một test bắt buộc.**

```axiom
let v = Vec<i32>::new()
push(v, 1)

let view = view(v)

push(v, 2)

use(view)
```

Câu hỏi semantic:

> `push` có thể invalidate view hay không?

Tôi đề xuất v0.1:

**Nếu `push` có khả năng thay đổi storage backing thì compiler phải reject khi view còn sống.**

Tức:

```text
view(v)
   ↓
v.push(...)
```

nếu `push` có WRITE/RELOCATE effect lên region mà view phụ thuộc:

```text
REJECT
```

Nhưng:

```axiom
let view = view(v)
use(view)

push(v, 2)
```

Accept.

Đây chính là lý do cần **effect summary + region/provenance**, chứ chỉ ownership không đủ.

---

# 8. Mutable view + ownership

### VIEW-MUT-001

```axiom
let b = create()

let v = mut_view(b)

use(b)
```

Reject nếu `b` được access trong khi `v` còn active.

---

### VIEW-MUT-002

```axiom
let b = create()

{
    let v = mut_view(b)
    modify(v)
}

use(b)
```

Accept.

Capability kết thúc trước `use(b)`.

---

### VIEW-MUT-003

```axiom
let b = create()

let a = mut_view(b)
let c = mut_view(b)
```

Reject.

---

### VIEW-MUT-004

```axiom
let b = create()

let a = view(b)
let c = view(b)
```

Accept.

---

### VIEW-MUT-005

```axiom
let b = create()

let a = view(b)
let c = mut_view(b)
```

Reject.

---

# 9. Last-use analysis

Đây là phần giúp Axiom **dễ dùng hơn Rust**.

```axiom
let b = create()

let v = view(b)

use(v)

modify(b)
```

Nếu compiler xác định:

```text
last use(v) = dòng trước
```

thì:

```text
v capability ends
```

và `modify(b)` được Accept.

Không cần programmer viết:

```text
drop(v)
```

hay scope nhân tạo.

Đây là một trong những lợi thế lớn nhất của Axiom.

---

# 10. Closure capture

### CLOSURE-001

```axiom
let buffer = create()

let f = || use(buffer)

f()
```

Compiler có thể capture bằng ownership hoặc view tùy semantics.

Nếu closure không escape:

```text
non-escaping
```

thì có thể tối ưu hoàn toàn closure.

---

### CLOSURE-002

```axiom
let buffer = create()

let f = || use(buffer)

return f
```

Closure escape.

Compiler không thể giữ một view tới local đã chết.

Có thể:

```text
capture by value
```

nếu semantics cho phép.

Hoặc reject nếu API yêu cầu borrowed capture.

---

### CLOSURE-003

```axiom
let buffer = create()

spawn(|| use(buffer))
use(buffer)
```

Phải phân tích capture.

Nếu spawn chuyển ownership:

```text
buffer → MOVED
```

thì `use(buffer)` reject.

---

# 11. Drop adversarial tests

### DROP-001

```axiom
{
    let a = create_a()
    let b = create_b()
}
```

Expected:

```text
DROP b
DROP a
```

---

### DROP-002

```axiom
let a = create_a()
let b = create_b()

return
```

Expected:

```text
DROP b
DROP a
RETURN
```

---

### DROP-003

```axiom
let a = create_a()

if condition {
    return
}

use(a)
```

Path return phải Drop `a`.

---

### DROP-004

```axiom
let a = create_a()

if condition {
    consume(a)
}

drop_scope()
```

Nếu `condition == true`:

```text
do not DROP a again
```

Nếu false:

```text
DROP a
```

---

# 12. Drop + panic

```axiom
let a = create_a()
let b = create_b()

panic()
```

Nếu panic profile là unwind:

```text
DROP b
DROP a
PANIC
```

Nếu abort:

```text
PANIC
```

không được giả định cleanup thông thường.

Nhưng semantics của resource safety phải được freeze rất rõ trước khi test này trở thành normative.

---

# 13. Drop + observable effects

Ví dụ:

```axiom
let f = File.open(...)
return
```

Nếu `Drop<File>` đóng file:

```text
DROP(File)
```

là observable.

Optimizer không được loại bỏ.

Ngược lại một temporary thuần:

```axiom
let p = Point { ... }
return
```

không có Drop effect.

Có thể biến mất hoàn toàn.

---

# 14. Result / error flow

### ERR-001

```axiom
fn f() -> Result<i32, Error> {
    Ok(10)
}
```

---

### ERR-002

```axiom
fn f() -> Result<i32, Error> {
    let x = g()?
    Ok(x)
}
```

MIR phải biểu diễn:

```text
CALL g
BRANCH success/error

success:
    ...

error:
    return error
```

---

### ERR-003

Nếu local resource tồn tại:

```axiom
fn f() -> Result<i32, Error> {
    let file = open()?
    let x = read(file)?
    Ok(x)
}
```

Khi `read` lỗi:

```text
DROP file
RETURN Err
```

Đây là test **Drop + Result propagation**.

---

# 15. Concurrency adversarial

### CONC-001

```axiom
let x = create()
spawn(move || use(x))
```

Nếu `x: Send`:

Accept.

---

### CONC-002

```axiom
let x = create_non_send()
spawn(move || use(x))
```

Reject.

---

### CONC-003

```axiom
let x = shared_readable()

spawn(|| read(x))
spawn(|| read(x))
```

Nếu `Share(x)`:

Accept.

---

### CONC-004

```axiom
let x = shared_mutable()

spawn(|| write(x))
spawn(|| write(x))
```

Reject nếu không có synchronization.

---

### CONC-005

```axiom
let mutex = Mutex(...)
spawn(|| {
    let guard = mutex.lock()
    write(guard)
})
```

Phải bảo đảm `guard` Drop/unlock trên mọi terminating path.

Đặc biệt:

```text
panic
return
error propagation
```

đều phải unlock đúng semantics.

---

# 16. Async adversarial

### ASYNC-001

```axiom
async fn f() {
    let x = create()
    await something()
    use(x)
}
```

`x` phải sống qua suspension.

---

### ASYNC-002

```axiom
async fn f() {
    let x = create()
    await something()
    consume(x)
}
```

Accept.

---

### ASYNC-003

```axiom
async fn f() {
    let x = create()
    let v = view(x)

    await something()

    use(v)
}
```

Accept **chỉ khi** async frame giữ owner `x` sống xuyên suspension.

---

### ASYNC-004

Async task migrates thread:

```text
x across await
```

Nếu task cần `Send`, compiler phải kiểm tra.

---

# 17. Unsafe boundary

Đây là test để đảm bảo:

> `unsafe` không biến Axiom thành “mọi thứ đều hợp lệ”.

Ví dụ:

```axiom
unsafe {
    let p: *mut i32 = ...
}
```

Raw pointer được phép.

Nhưng:

```axiom
let x: i32 = "hello"
```

vẫn phải type error.

Unsafe chỉ bypass **memory safety proof**, không bypass type system.

---

# 18. FFI

### FFI-001

```axiom
@repr(C)
struct Point {
    x: i32
    y: i32
}
```

Phải có layout tương thích C.

---

### FFI-002

Foreign function nhận:

```text
*mut T
```

phải đi qua unsafe boundary hoặc API contract tương ứng.

---

### FFI-003

Opaque foreign type không được compiler tự giả định:

```text
Copy
Drop
Send
Share
```

nếu chưa có contract.

Đây là chỗ rất dễ gây memory unsafety.

---

# 19. Optimizer adversarial

Sau này rất quan trọng.

### OPT-001

```axiom
let x = 10
let y = x + 20
return y
```

Native code có thể chỉ còn:

```text
return 30
```

Nhưng semantics không đổi.

---

### OPT-002

```axiom
let b = create()
use(b)
```

Nếu allocation không observable:

```text
ALLOC
DROP
```

có thể bị loại bỏ hoặc stack-promote.

---

### OPT-003

```axiom
let f = File.open(...)
return
```

Không được loại bỏ Drop nếu close observable.

---

### OPT-004

Bounds:

```axiom
let a = array
let x = a[3]
```

Nếu compiler chứng minh `3 < N`,:

```text
BOUNDS_CHECK
```

có thể biến mất.

Interpreter vẫn phải cho cùng kết quả.

---

# 20. Test quan trọng nhất: Semantic Equivalence

Cuối cùng mỗi chương trình test nên có:

```text id="f5n6d9"
SOURCE
EXPECTED ACCEPT/REJECT
EXPECTED DIAGNOSTIC
EXPECTED OBSERVABLE RESULT
EXPECTED EVENTS
```

Ví dụ:

```text id="e4olq8"
TEST: partial_move_001

SOURCE:
    let p = make_person()
    let name = p.name
    print(p.age)

EXPECT:
    ACCEPT

OBSERVABLE:
    stdout = "..."

EVENTS:
    DROP(p.age)
    no DROP(p.name)
```

---

# 21. Tôi muốn thêm một nguyên tắc rất quan trọng

Bộ test **không nên test implementation**.

Không viết:

```text
EXPECT MIR:
    %17 = ...
    %18 = ...
    %19 = ...
```

trừ một số test compiler-level đặc biệt.

Thay vào đó:

```text
EXPECT SEMANTICS:
    p.name = MOVED
    p.age = OWNED
```

hoặc:

```text
EXPECT PROPERTY:
    contains MOVE
    contains DROP
    no invalid access
```

hoặc:

```text
EXPECT RUNTIME:
    stdout == "42"
```

Như vậy sau này optimizer thay đổi MIR hoàn toàn, test vẫn còn giá trị.

---

# 22. Cấu trúc test chính thức

Tôi đề xuất:

```text
tests/
├── syntax/
├── type/
├── ownership/
│   ├── move/
│   ├── copy/
│   ├── branch/
│   ├── loop/
│   └── partial_move/
├── region/
│   ├── field/
│   ├── view/
│   ├── mut_view/
│   └── invalidation/
├── drop/
├── closure/
├── traits/
├── generics/
├── result/
├── panic/
├── concurrency/
├── async/
├── ffi/
├── unsafe/
├── abi/
├── optimizer/
└── differential/
```

Và:

```text
tests/differential/
    interpreter/
    native/
```

---

# 23. Một điểm tôi muốn sửa nhẹ trong kiến trúc trước đó

Sau khi nhìn qua adversarial tests, có một kết luận khá quan trọng:

**`view` không nên chỉ được xem là một kiểu dữ liệu.**

Nó phải được xem đồng thời là:

```text
view<T>
    │
    ├── Type
    ├── Provenance
    ├── Region
    ├── Access capability
    └── Lifetime relation
```

Trong source code, programmer chỉ thấy:

```axiom
view<T>
mut_view<T>
```

Nhưng trong compiler:

```text
ViewCapability {
    type
    provenance
    region
    access
    validity
}
```

Điều này cho phép chúng ta đạt mục tiêu ban đầu:

> **Không bắt programmer học borrow checker, nhưng compiler vẫn có thể thực hiện một hệ thống ownership/alias analysis mạnh.**

---

# 24. Và đây là kiến trúc Axiom hiện tại

Sau bước này, toàn bộ hệ thống bắt đầu có hình dạng khá rõ:

```text
                    AXIOM
                       │
                       ▼
                    Parser
                       │
                       ▼
                      HIR
                       │
            ┌──────────┴──────────┐
            │                     │
        Type System          Trait Resolution
            │                     │
            └──────────┬──────────┘
                       ▼
                      MIR
                       │
        ┌──────────────┼──────────────┐
        ▼              ▼              ▼
   Ownership       Capability       Effects
   Analysis         Analysis        Analysis
        └──────────────┼──────────────┘
                       ▼
                 Verified MIR
                       │
             ┌─────────┴─────────┐
             ▼                   ▼
       Semantic Oracle        Optimizer
             │                   │
        MIR Interpreter          ▼
             │                  LIR
             │                   │
             │             Machine Backend
             │                   │
             └───────┬───────────┘
                     ▼
               Native Program
```

Đây là điểm mà Axiom bắt đầu có một **compiler architecture thực sự**, thay vì chỉ là tập hợp feature.

## Bước kế tiếp tôi đề xuất

Không nên thêm feature ngôn ngữ nữa ngay lúc này.

Ta nên chuyển sang **`Axiom Ownership/Region Verifier v0.1`** và đặc tả nó thành một thuật toán thực sự:

```text
MIR CFG
 ↓
Definite Initialization
 ↓
Ownership Dataflow
 ↓
Region/Place Analysis
 ↓
Capability Conflict Detection
 ↓
View Provenance
 ↓
Drop/Resource Analysis
 ↓
Effect Verification
 ↓
Concurrency Verification
 ↓
VERIFIED MIR
```

Quan trọng nhất là ta sẽ làm rõ **thuật toán merge state tại CFG join, loop fixed-point, last-use, partial move và region overlap**. Đây chính là “bộ não” cho phép Axiom có memory safety mạnh mà **không bắt người lập trình viết lifetime/borrow annotation**.