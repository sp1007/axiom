Tiếp tục. Đây là phần tôi cho rằng **quan trọng nhất của Axiom**: biến ownership từ một hệ thống mà programmer phải “đấu vật” thành một hệ thống compiler tự quản lý.

# Axiom Ownership UX v0.1

## 1. Nguyên tắc cốt lõi

Axiom không nên cố làm ownership “vô hình hoàn toàn”.

Thay vào đó:

> **Programmer nhìn thấy ai sở hữu resource; compiler tự quản lý khi nào ownership kết thúc, capability sống bao lâu và alias có hợp lệ hay không.**

Có thể tóm tắt:

```text
Programmer:
    "Đây là value của tôi."

Compiler:
    "Tôi tự quyết định lifetime, storage, alias, cleanup."

Programmer không cần:
    lifetime
    borrow annotation
    explicit release
    explicit borrow
    explicit unborrow
```

---

# 2. Case đơn giản nhất

```axiom
let file = File.open("a.txt")?
```

`file` là owner.

Khi scope kết thúc:

```text
file
 ↓
DROP
```

Programmer không viết:

```axiom
file.close()
```

nếu chỉ muốn cleanup.

Tuy nhiên nếu `close()` có thể thất bại:

```axiom
file.close()?
```

là một **business/resource operation**, không phải cleanup bắt buộc.

Đây là distinction rất quan trọng:

```text
close() → có thể thất bại
Drop    → cleanup bắt buộc
```

---

# 3. Move

```axiom
let file1 = open()?
let file2 = file1
```

Compiler biết:

```text
file1: MOVED
file2: OWNED
```

Không cần physical copy.

Nếu `file1` chỉ là SSA value:

```text
register → register
```

thậm chí có thể không có instruction nào.

---

# 4. Nhưng Copy type thì khác

```axiom
let a = 10
let b = a
let c = a
```

`i32` là Copy.

Không có ownership transfer:

```text
a → still valid
b → valid
c → valid
```

Compiler tự quyết định register/stack.

---

# 5. Programmer không cần biết type có Move hay Copy bằng syntax

Ví dụ:

```axiom
fn consume(buffer: Buffer) {
    ...
}

fn inspect(buffer: view<Buffer>) {
    ...
}
```

Caller:

```axiom
let b = Buffer(...)

inspect(b)
consume(b)
```

Compiler:

```text
inspect(b)
    → ephemeral READ capability
    → b remains owner

consume(b)
    → MOVE
    → b becomes MOVED
```

Đây là UX tôi muốn Axiom đạt được.

---

# 6. Function parameter `T` không mặc định là Copy

Đây là điểm phải cực kỳ rõ.

```axiom
fn consume(x: T)
```

không có nghĩa:

```text
copy x
```

Nó có nghĩa:

```text
receive a value
```

Nếu `T: Copy`:

```text
copy
```

Nếu `T: !Copy`:

```text
move
```

Compiler biết dựa trên type.

---

# 7. `view<T>` là cách đọc mà không lấy ownership

```axiom
fn hash(data: view<Buffer>) -> u64 {
    ...
}
```

Caller:

```axiom
let data = Buffer(...)

let h = hash(data)

use(data)
```

hợp lệ.

Không cần:

```axiom
hash(&data)
```

---

# 8. `mut_view<T>` là mutation capability

```axiom
fn normalize(data: mut_view<Buffer>) {
    ...
}
```

Caller:

```axiom
var data = Buffer(...)

normalize(data)
```

Compiler tạo một capability:

```text
data
 └── WRITE capability
       ↓
    normalize()
       ↓
 capability expires
```

Sau call:

```axiom
use(data)
```

hợp lệ.

---

# 9. Capability không phải object runtime

Điểm này rất quan trọng.

```axiom
view<T>
mut_view<T>
```

không có nghĩa phải tạo runtime object:

```text
View {
    pointer
    length
    lifetime
    metadata
}
```

Compiler có thể lower thành:

```text
ptr + len
```

hoặc chỉ:

```text
ptr
```

nếu length compile-time known.

Capability chủ yếu là:

```text
compiler semantic state
```

Không phải runtime machinery.

---

# 10. Nhiều read cùng lúc

```axiom
let a = view(data)
let b = view(data)

inspect(a)
inspect(b)
```

hợp lệ.

Compiler:

```text
READ
READ
```

→ không conflict.

---

# 11. Read + write

```axiom
let a = view(data)
let b = mut_view(data)
```

Nếu hai capability cùng active và vùng có thể overlap:

```text
ERROR
```

Không cần programmer viết lifetime để giải quyết.

Compiler tìm last-use:

```axiom
let a = view(data)

inspect(a)

mutate(data)
```

Sau `inspect(a)`, nếu `a` không còn dùng:

```text
a capability → EXPIRED
```

`mutate(data)` hợp lệ.

Đây là điểm Axiom có thể tạo UX tốt hơn rất nhiều so với việc programmer phải manually reason về lifetime.

---

# 12. Compiler phải dùng last-use analysis

Ví dụ:

```axiom
let v = view(data)

println(v)

mutate(data)
```

Compiler thấy:

```text
last use(v) = println(v)
```

nên:

```text
after println:
    v → EXPIRED
```

Không cần giữ borrow đến hết lexical scope.

Đây nên là **semantic lifetime**, không phải lexical lifetime.

---

# 13. Nhưng nếu view escape thì khác

Ví dụ:

```axiom
let v = view(data)

store(v)
```

Nếu `store()` khiến `v` escape:

```text
v → ESCAPED
```

thì compiler không thể đơn giản expire sau call.

Nếu `store()` cố giữ view vượt quá lifetime của `data`, compiler reject.

---

# 14. Return view

Đây là case rất quan trọng:

```axiom
fn first(data: view<Array<i32>>) -> view<i32> {
    ...
}
```

Nếu returned region nằm trong input:

```text
input region
    └── returned region
```

→ hợp lệ.

Nhưng:

```axiom
fn bad() -> view<i32> {
    let x = 10
    return view(x)
}
```

→ compile error.

Compiler biết:

```text
x lifetime < returned capability lifetime
```

---

# 15. Không cần lifetime annotation

Không:

```axiom
fn first<'a>(data: &'a [i32]) -> &'a i32
```

Chỉ:

```axiom
fn first(data: view<Array<i32>>) -> view<i32>
```

Compiler tự chứng minh provenance.

Đây chính là một trong những điểm khác biệt lớn của Axiom.

---

# 16. Struct chứa resource

```axiom
struct User {
    name: Text
    avatar: File
}
```

`User` là owning aggregate.

Khi:

```axiom
let user = load_user()
```

thì:

```text
User
├── name → OWNED
└── avatar → OWNED
```

Khi scope kết thúc:

```text
drop avatar
drop name
drop user
```

theo dependency/initialization semantics.

---

# 17. Partial move

Ví dụ:

```axiom
let user = User {
    name: Text(...),
    avatar: File(...)
}

let avatar = user.avatar
```

Nếu `avatar` !Copy:

```text
user.name   → OWNED
user.avatar → MOVED
user         → PARTIAL
```

Compiler không được drop `avatar` lần nữa khi `user` chết.

Nhưng vẫn phải drop:

```text
user.name
```

Đây là lý do ownership state phải là **field tree**, không chỉ một bit `owned/moved`.

---

# 18. Partial move + method

Sau:

```axiom
let avatar = user.avatar
```

không được:

```axiom
use(user)
```

nếu `use` yêu cầu toàn bộ `User`.

Nhưng có thể:

```axiom
use(user.name)
```

nếu field đó vẫn valid.

Đây là behavior rất mạnh nhưng compiler có thể tự xử lý.

---

# 19. Assignment vào resource

Ví dụ:

```axiom
var file = open_a()?

file = open_b()?
```

Semantic:

```text
evaluate RHS
validate destination
drop old file
move new file into destination
```

Không được drop `file` trước khi RHS thành công.

Nếu:

```axiom
open_b()?
```

trả `Err`:

```text
old file vẫn còn nguyên
```

Đây là một invariant rất quan trọng.

---

# 20. Self-assignment

```axiom
file = file
```

Với non-Copy resource, tôi đề xuất **compile error**.

Không cần cố tạo semantic đặc biệt.

Nếu muốn duplicate:

```axiom
file = file.clone()
```

Nếu muốn move:

```text
không có lý do hợp lệ để self-move
```

Compiler reject.

---

# 21. Conditional move

Ví dụ:

```axiom
let file = open()?

if condition {
    consume(file)
}

use(file)
```

Compiler phải phân tích cả hai nhánh:

```text
branch A:
    file → MOVED

branch B:
    file → OWNED
```

Merge:

```text
file → MAYBE_MOVED
```

Do đó:

```axiom
use(file)
```

→ compile error.

Đây là **dataflow analysis**, không phải programmer burden.

---

# 22. Nhưng compiler không nên quá bảo thủ

Ví dụ:

```axiom
if condition {
    consume(file)
    return
}

use(file)
```

Compiler có thể chứng minh:

```text
branch where file moved
    → function terminated

branch continuing
    → file still owned
```

nên:

```axiom
use(file)
```

hợp lệ.

Đây là lý do verifier phải hiểu CFG và terminal control flow.

---

# 23. Loop move

Case:

```axiom
let x = resource()

while condition {
    consume(x)
}
```

Compiler phải phát hiện:

```text
iteration 1 → x moved
iteration 2 → x unavailable
```

→ reject.

Nhưng:

```axiom
while condition {
    let x = resource()
    consume(x)
}
```

hợp lệ.

---

# 24. Collection iteration

Đây là nơi UX cần tốt.

Không muốn programmer phải viết:

```axiom
for x in &mut vec
```

Axiom:

```axiom
for x in mut_view(vec) {
    ...
}
```

hoặc tốt hơn, với `for` compiler/library semantics:

```axiom
for x in vec {
    ...
}
```

Compiler phải biết iteration đang:

```text
borrow/read
```

hay:

```text
move elements
```

dựa trên iterator implementation.

---

# 25. Vì vậy `for` không mặc định có một ownership meaning duy nhất

Ví dụ:

```axiom
for x in view(data) {
    ...
}
```

→ read.

```axiom
for x in mut_view(data) {
    ...
}
```

→ mutable access.

```axiom
for x in data {
    ...
}
```

có thể consume/iterate theo semantic của `IntoIterator`.

Điều này làm iterator abstraction mạnh mà không cần syntax ownership riêng.

---

# 26. Closure capture

Ví dụ:

```axiom
let buffer = Buffer(...)

let f = || {
    inspect(buffer)
}
```

Compiler thấy closure cần READ capability.

Nếu closure không escape owner:

```text
buffer
 ↓
closure
 ↓
READ capability
```

có thể scalarize/eliminate.

Nếu closure escape:

```text
closure → stored elsewhere
```

compiler phải đảm bảo `buffer` sống đủ lâu.

---

# 27. Closure mutation

```axiom
var counter = 0

let f = || {
    counter += 1
}
```

Compiler cần exclusive mutation capability.

Nếu `f` có thể chạy đồng thời:

```text
counter
 ↓
MUTABLE capture
```

thì concurrency verifier phải kiểm tra.

Ví dụ:

```axiom
spawn(f)
spawn(f)
```

không được tự động biến thành safe concurrent mutation.

---

# 28. Move closure

Khi programmer viết:

```axiom
let task = move || {
    process(buffer)
}
```

ý nghĩa là:

> Closure phải sở hữu captured `buffer`.

Sau đó:

```axiom
use(buffer)
```

→ invalid.

Đây là một trong số rất ít nơi tôi muốn `move` xuất hiện trong syntax.

---

# 29. Async

Ví dụ:

```axiom
async fn process(buffer: Buffer) {
    inspect(buffer)
    await something()
    use(buffer)
}
```

`buffer` phải sống qua suspension point.

Compiler biến async function thành state machine:

```text
State0:
    buffer
    ↓
await
    ↓
State1:
    buffer
```

Ownership verifier không cần lifetime annotation.

Nó chỉ cần biết:

```text
buffer is live across SUSPEND
```

---

# 30. `mut_view` qua `await`

Tôi vẫn giữ restriction v0.1:

```axiom
async fn foo(data: mut_view<Data>) {
    mutate(data)
    await something()
}
```

→ **không cho phép capability mutable view sống qua await** trong safe Core v0.1.

Lý do rất đơn giản:

```text
mut_view
    ↓
exclusive access
    ↓
SUSPEND
```

có thể giữ exclusive access trong khi task bị scheduler chuyển sang nơi khác.

Ta chưa cần giải bài toán này ở v0.1.

Programmer có thể:

```axiom
mutate(data)

drop/expire capability

await something()

mutate(data)
```

Compiler có thể tạo hai capability độc lập.

---

# 31. Thread spawn

Ví dụ:

```axiom
let buffer = Buffer(...)

spawn(|| {
    process(buffer)
})
```

Compiler thấy closure capture `buffer`.

Nếu task chạy độc lập:

```text
buffer
 ↓
MOVE into closure
 ↓
task owns buffer
```

Sau đó caller không còn owner.

Đây là behavior tự nhiên.

---

# 32. Không cho closure “lén” borrow local rồi escape

Ví dụ:

```axiom
fn bad() {
    let data = Data(...)

    spawn(|| {
        inspect(data)
    })
}
```

Nếu closure chỉ READ capture nhưng thread sống độc lập:

compiler phải xử lý capture semantics.

Nếu closure giữ borrowed view:

```text
task lifetime > data lifetime
```

→ reject.

Compiler có thể giải quyết bằng cách capture **value** nếu capture semantics cho phép, hoặc yêu cầu programmer viết:

```axiom
spawn(move || {
    inspect(data)
})
```

Đây là một trường hợp mà explicit `move` có giá trị rất lớn.

---

# 33. Shared ownership

Nếu programmer thật sự muốn nhiều execution contexts cùng sở hữu:

```axiom
let shared = Arc(data)
```

thì semantics thay đổi rõ:

```text
Arc<Data>
```

là shared ownership abstraction.

Không phải:

```text
compiler tự động biến Data thành reference counted
```

Điều này rất quan trọng cho performance predictability.

---

# 34. `Arc<T>` không tự biến `T` thành mutable-safe

Ví dụ:

```axiom
Arc<Data>
```

chỉ giải quyết:

```text
ownership
```

Không giải quyết:

```text
concurrent mutation
```

Muốn mutate:

```axiom
Arc<Mutex<Data>>
```

hoặc atomic abstraction phù hợp.

Compiler không tự thêm mutex.

---

# 35. Drop trong nested structures

Ví dụ:

```axiom
{
    let a = ResourceA()
    let b = ResourceB()
    let c = ResourceC()
}
```

Mặc định:

```text
c.drop()
b.drop()
a.drop()
```

Nếu dependency analysis yêu cầu thứ tự khác để đảm bảo correctness, compiler phải tôn trọng semantic dependency.

Nhưng programmer không cần viết cleanup.

---

# 36. Early return

```axiom
fn foo() -> Result<()> {
    let a = ResourceA()
    let b = ResourceB()

    if error() {
        return Err(...)
    }

    Ok(())
}
```

Compiler tạo:

```text
error:
    drop b
    drop a
    return Err
```

Không cần:

```axiom
defer
finally
```

---

# 37. Panic

Nếu:

```axiom
panic("bad")
```

thì cleanup phải tuân theo panic profile.

`--panic=abort`:

```text
panic
 ↓
process termination
```

Không cần unwind runtime.

`--panic=unwind`:

```text
panic
 ↓
unwind
 ↓
Drop active resources
```

Do đó panic mode là **backend/runtime policy**, không thay đổi ownership semantics.

---

# 38. Một điểm rất quan trọng: Drop không được có ownership ambiguity

Không cho:

```axiom
impl Drop for Resource {
    fn drop(self: Resource) -> Result<()> {
        ...
    }
}
```

Drop không trả recoverable error.

Chỉ:

```axiom
impl Drop for Resource {
    fn drop(self: Resource) {
        ...
    }
}
```

Nếu operation có thể fail:

```axiom
resource.close()?
```

trước khi scope kết thúc.

---

# 39. Ownership không nên trở thành “borrow checker ẩn” mà programmer vẫn phải debug

Đây là thách thức lớn nhất.

Compiler error phải nói:

```text
AX_VIEW_0001

cannot mutably access `data`

an active read capability exists:
    `view` created at line 12
    last use: line 18

mutable access requested at line 20

help:
    move the mutation after the last use of `view`
```

Không nên:

```text
error: lifetime mismatch
'a does not outlive 'b
```

Axiom không expose lifetime model.

---

# 40. Diagnostics nên mô tả semantic event

Ví dụ:

```axiom
let view = view(data)
mutate(data)
```

Không nên nói:

> borrowed value does not live long enough

Nên:

```text
`data` cannot be mutably accessed here.

A read capability created by `view(data)` is still active.

Last required use:
    line 8

Mutable access:
    line 9
```

Đây là một khác biệt UX cực lớn.

---

# 41. Ownership state machine

Tôi đề xuất compiler dùng state:

```text
UNINIT
   ↓
OWNED
   ├── COPY ─────→ OWNED
   ├── MOVE ─────→ MOVED
   ├── VIEW ─────→ OWNED + READ_CAP
   ├── MUT_VIEW ─→ OWNED + WRITE_CAP
   └── DROP ─────→ DROPPED

OWNED
   ↓ partial move
PARTIAL
   ├── remaining fields
   └── moved fields

PARTIAL
   ↓ all fields moved
MOVED
```

Capability độc lập:

```text
ABSENT
  ↓
ACTIVE
  ↓ last-use
EXPIRED
```

Đây chính là mô hình mà verifier đã có; giờ chúng ta đang làm nó trở nên hợp lý ở source level.

---

# 42. Tôi đề xuất thêm một khái niệm: Semantic Ownership Boundary

Một API có thể được nhìn theo ba dạng:

```text
T
view<T>
mut_view<T>
```

và chỉ ba dạng này tạo thành **ownership boundary cơ bản**.

| Parameter | Ý nghĩa |
|---|---|
| `T` | nhận value / ownership theo Copy/Move |
| `view<T>` | đọc không lấy ownership |
| `mut_view<T>` | exclusive mutation |

Đây có thể trở thành một trong những nguyên tắc nhận diện Axiom.

---

# 43. Không cần `out` parameter

Ví dụ C++:

```text
void make(Data* out)
```

Axiom:

```axiom
fn make() -> Data
```

Compiler có thể lower thành:

```text
caller-allocated return storage
```

không có copy thực tế.

Nếu cần nhiều output:

```axiom
fn parse() -> (Header, Body)
```

Compiler có thể:

```text
construct directly into caller storage
```

Do đó không cần:

```text
out T
inout T
```

trong Core.

---

# 44. Không cần pointer để tối ưu return

Ví dụ:

```axiom
fn create() -> HugeStruct
```

semantic:

```text
return HugeStruct
```

ABI có thể:

```text
caller allocates return storage
callee constructs there
```

Source không cần biết.

Đây chính là abstraction erasure hoạt động đúng cách.

---

# 45. Ownership + optimizer

Ownership information không chỉ để safety.

Ví dụ:

```axiom
fn process(x: mut_view<Data>) {
    x.a += 1
    x.b += 2
}
```

Compiler biết trong phạm vi này:

```text
exclusive WRITE
```

nên có thể suy luận alias restrictions.

Điều này hỗ trợ:

```text
vectorization
load/store elimination
register promotion
reordering
```

mà không cần programmer viết `restrict`.

---

# 46. Nhưng compiler không được biến ownership thành hidden semantic assumption

Nếu unsafe raw pointer tồn tại:

```axiom
unsafe {
    ...
}
```

compiler phải thận trọng.

Safe alias facts chỉ được dùng khi chúng thực sự được chứng minh.

Do đó:

```text
safe capability
    → strong alias facts

unknown raw pointer
    → conservative alias assumptions
```

---

# 47. Một quyết định rất quan trọng: không có `borrow()` API trong Core

Không nên có:

```axiom
borrow(x)
borrow_mut(x)
release_borrow(x)
```

vì đó là compiler machinery bị leak ra source.

Chỉ cần:

```axiom
view(x)
mut_view(x)
```

khi programmer cần **lưu capability**.

---

# 48. Ownership UX cuối cùng

Axiom programmer sẽ suy nghĩ chủ yếu bằng:

```text
"Đây là value của tôi."
"Function này chỉ đọc nó."
"Function này sửa nó."
"Function này nhận ownership."
"Task này nhận ownership."
"Muốn shared ownership → Arc."
"Muốn raw memory → unsafe."
```

Không cần suy nghĩ liên tục:

```text
lifetime 'a
borrow 'b
reborrow
variance
NLL
region
outlives
```

Compiler vẫn làm toàn bộ công việc đó bên dưới.

---

# 49. Tôi sẽ đóng băng thêm các invariant

### AOWN-01 — Value Ownership

Mọi non-Copy value có một owner duy nhất trong safe execution state.

### AOWN-02 — Copy Explicit By Type

Copyability là property của type.

### AOWN-03 — Move Is Semantic

Move không yêu cầu physical memory copy.

### AOWN-04 — View Is Non-Owning

`view<T>` không chuyển ownership.

### AOWN-05 — MutView Is Exclusive

`mut_view<T>` yêu cầu exclusive write capability trên vùng tương ứng.

### AOWN-06 — Compiler Lifetime Inference

Programmer không viết lifetime annotations.

### AOWN-07 — Semantic Last Use

Capability có thể hết hiệu lực tại semantic last-use, không nhất thiết lexical scope.

### AOWN-08 — Escape Safety

Capability không được escape vượt owner lifetime.

### AOWN-09 — Partial Ownership

Partial move được hỗ trợ.

### AOWN-10 — Conditional Ownership

CFG/dataflow quyết định `MAYBE_MOVED`/`MAYBE_OWNED`.

### AOWN-11 — Deterministic Drop

Owned resources được cleanup deterministically.

### AOWN-12 — Drop Is Not Fallible

Recoverable cleanup failure phải dùng explicit operation.

### AOWN-13 — Explicit Shared Ownership

Shared ownership phải được biểu diễn bằng type/library abstraction.

### AOWN-14 — Send/Share Separation

Ownership transfer và shared access là hai property khác nhau.

### AOWN-15 — Async Ownership

Values sống qua `await` được compiler quản lý trong async state machine.

### AOWN-16 — Unsafe Boundary

Unsafe có thể phá các proof assumptions nhưng không biến type system thành dynamic.

### AOWN-17 — Ownership Diagnostics

Diagnostic mô tả capability/ownership event thay vì expose compiler-internal lifetime notation.

### AOWN-18 — No Programmer Borrow Protocol

Compiler-managed ownership không được yêu cầu programmer gọi borrow/release thủ công.

---

## Điểm rất đáng chú ý

Sau khi chạy qua các case khó nhất, mô hình này cho thấy một điều:

**Axiom thực tế không cần “reference type” trong semantic core.**

Ta chỉ cần:

```text
T
view<T>
mut_view<T>
*T          // unsafe
addr        // unsafe/system
```

và:

```text
Box<T>
Arc<T>
...
```

là library abstractions.

Đây là một kết quả khá mạnh so với hướng ban đầu của chúng ta. Nó có nghĩa **“reference/pointer” không còn là một khái niệm mà programmer phải dùng thường xuyên để quản lý lifetime**. Compiler vẫn có thể dùng pointer/reference ở MIR/LIR/machine level.

### Kiến trúc lúc này rất đẹp:

```text
SOURCE
────────────────────────────────
T          view<T>       mut_view<T>
│             │              │
│             └──────┬───────┘
│                    │
└──────────────┬─────┘
               ↓
       Ownership / Capability
               ↓
             MIR
               ↓
       pointer / address
               ↓
             LIR
               ↓
        machine registers
        memory addresses
```

**Programmer không cần biết representation để sử dụng ownership.**

---

Phần tiếp theo tôi muốn đi sâu vào là **`Memory Allocation + Collections + Stable Address`**. Đây là chỗ nối trực tiếp với câu hỏi trước của bạn về **flat memory model, fragmentation, heap/stack/arena/pool**. Ta cần chốt chính xác `Box`, `Vec`, `Arena`, `Pool`, relocation, pinning/stable address và allocator API sao cho vừa đơn giản cho programmer vừa không hy sinh hiệu năng.