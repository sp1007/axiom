Tiếp tục thì tôi sẽ chuyển ngay từ **Semantic Freeze → Conformance Suite**. Đây là bước biến Axiom từ “một thiết kế ngôn ngữ” thành **một specification mà compiler agent có thể thực thi mà không tự bịa semantics**.

# AXIOM-CONFORMANCE-TESTS v0.1

Tôi đề xuất bộ test đầu tiên gồm **72 test**, chia thành 10 nhóm.

```text
tests/
├── syntax/
├── types/
├── ownership/
├── views/
├── drop/
├── traits/
├── generics/
├── concurrency/
├── errors/
└── abi/
```

Mỗi test không chỉ kiểm tra compile/pass/fail.

Nó phải kiểm tra 4 tầng:

```text
SOURCE
  ↓
EXPECTED SEMANTICS
  ↓
EXPECTED MIR PROPERTY
  ↓
EXPECTED RESULT
```

---

# 1. Format chuẩn của một test

Ví dụ `ownership/move_basic.ax`.

```axiom
// TEST: OWN_MOVE_001
// EXPECT: REJECT
// ERROR: AX_OWN_0001

fn consume(x: Vec<i32>) {}

fn main() {
    let data = Vec.new<i32>()

    consume(data)

    print(data)
}
```

Metadata machine-readable:

```text
TEST_ID      = OWN_MOVE_001
CATEGORY     = ownership
EXPECT       = reject
DIAGNOSTIC   = AX_OWN_0001
```

Compiler phải xuất diagnostic ổn định.

---

# 2. Ownership test matrix

### OWN_MOVE_001 — basic move

```axiom
let a = make_buffer()
consume(a)
use(a)
```

→ reject.

### OWN_MOVE_002 — move twice

```axiom
consume(a)
consume(a)
```

→ reject.

### OWN_MOVE_003 — move into return

```axiom
fn take() -> Buffer {
    let x = make_buffer()
    x
}
```

→ accept.

Ownership:

```text
x: OWNED
return: MOVE
x: MOVED
```

### OWN_MOVE_004 — branch

```axiom
if condition {
    consume(a)
}

use(a)
```

Compiler phải xử lý cả hai control-flow paths.

Nếu `condition` có thể true:

→ reject.

### OWN_MOVE_005 — both branches consume

```axiom
if condition {
    consume(a)
} else {
    consume(a)
}
```

→ accept nếu sau `if`, `a` không được sử dụng.

Điểm này rất quan trọng:

> Ownership là **control-flow sensitive**, không phải lexical.

---

# 3. Copy

### COPY_001

```axiom
let a: i32 = 10
let b = a
print(a)
print(b)
```

→ accept.

### COPY_002

Struct:

```axiom
struct Point {
    x: i32
    y: i32
}
```

Nếu `Point` được compiler xác định `Copy`:

```axiom
let a = Point{1, 2}
let b = a
print(a.x)
```

→ accept.

### COPY_003

Struct chứa resource:

```axiom
struct FileData {
    file: File
}
```

→ không được tự động trở thành `Copy`.

---

# 4. View

Đây là nhóm tôi muốn test kỹ nhất.

### VIEW_001

```axiom
fn sum(v: view<i32>) -> i32 {
    ...
}

fn main() {
    var a = [1, 2, 3]
    sum(view(a))
}
```

→ accept.

### VIEW_002 — return local view

```axiom
fn bad() -> view<i32> {
    var a = [1, 2, 3]
    view(a)
}
```

→ reject.

### VIEW_003 — mutable view

```axiom
fn fill(v: mut_view<i32>) {
    v[0] = 42
}
```

→ accept.

### VIEW_004 — read + mutable

```axiom
let r = view(a)
let w = mut_view(a)
```

→ reject nếu hai view overlap.

### VIEW_005 — two reads

```axiom
let a = view(data)
let b = view(data)

read(a)
read(b)
```

→ accept.

---

# 5. View + reallocation

Đây là test **cực kỳ quan trọng**.

```axiom
var v = Vec.new<i32>()

v.push(1)

let x = view(v)

v.push(2)

use(x)
```

Compiler phải xem `push` là operation có khả năng invalidate storage.

→ reject nếu không chứng minh được storage không thay đổi.

Nhưng:

```axiom
var v = Vec.with_capacity<i32>(100)

let x = view(v)

v.push(1)

use(x)
```

không nhất thiết reject.

Nếu compiler chứng minh:

```text
capacity >= required capacity
```

thì `x` vẫn hợp lệ.

Điều này đưa đến một nguyên tắc rất mạnh:

> **Axiom kiểm tra khả năng invalidation, không kiểm tra tên operation một cách máy móc.**

---

# 6. Drop

### DROP_001

```axiom
{
    let a = A()
    let b = B()
}
```

Expected semantic order:

```text
drop(b)
drop(a)
```

### DROP_002 — early return

```axiom
fn test() {
    let a = A()

    if condition {
        return
    }

    use(a)
}
```

Trước return:

```text
drop(a)
return
```

### DROP_003 — branch initialization

```axiom
let x

if condition {
    x = Resource()
}
```

Compiler phải theo dõi:

```text
false → UNINIT
true  → OWNED
```

Không được drop `x` trên path chưa initialized.

---

# 7. Traits

### TRAIT_001

```axiom
trait Drawable {
    fn draw(self: view<Self>)
}
```

```axiom
impl Drawable for Circle {
    ...
}
```

→ accept.

### TRAIT_002 — static dispatch

```axiom
fn render<T: Drawable>(x: T) {
    x.draw()
}
```

Compiler phải có khả năng specialize:

```text
render<Circle>
```

thành direct call.

Không được mặc định tạo vtable.

### TRAIT_003 — ambiguity

Nếu hai extension methods cùng match:

```text
foo(A)
foo(A)
```

→ deterministic ambiguity diagnostic.

Không được chọn “theo thứ tự import”.

---

# 8. Generics

### GENERIC_001

```axiom
fn identity<T>(x: T) -> T {
    x
}
```

```axiom
identity(10)
identity("hello")
```

→ specialize.

### GENERIC_002 — constraint

```axiom
fn max<T: Comparable>(a: T, b: T) -> T
```

Truyền type không implement `Comparable`.

→ reject.

### GENERIC_003 — generic ownership

```axiom
fn consume<T>(x: T) {
    ...
}
```

Nếu `T` không `Copy`, việc sử dụng `x` sau move phải tuân theo ownership của T.

---

# 9. Error semantics

### ERROR_001

```axiom
fn open() -> Result<File, Error>
```

Caller phải xử lý `Result` theo semantics đã định.

### ERROR_002

```axiom
let x = result?
```

`?` phải lower thành control flow tương đương.

Không được tạo hidden exception.

Semantic:

```text
Ok(v)
 ↓
continue

Err(e)
 ↓
return Err(e)
```

### ERROR_003 — panic

```axiom
panic("failure")
```

→ abnormal control flow.

Không phải `Result`.

---

# 10. Arithmetic

Đây là một phần tôi muốn **khóa kỹ hơn trước khi compiler implementation**, vì hiện tại semantics đã nói “không UB” nhưng vẫn cần xác định operation profile.

Axiom cần phân biệt:

```text
checked
wrapping
saturating
```

Ví dụ:

```axiom
let x = checked_add(a, b)
let y = wrapping_add(a, b)
let z = saturating_add(a, b)
```

Tôi khuyên **không dùng một phép `+` có behavior thay đổi theo optimization level**.

`+` phải có semantics deterministic.

Compiler có thể prove rằng overflow không xảy ra và biến:

```text
checked_add
```

thành một instruction bình thường.

---

# 11. Concurrency

### CONC_001 — Send

```axiom
let buffer = Buffer.new()

spawn(move buffer)
```

→ nếu `Buffer: Send`, accept.

Sau đó:

```axiom
use(buffer)
```

→ reject vì ownership đã chuyển.

### CONC_002 — Share

Hai execution contexts cùng đọc immutable data.

→ accept nếu type đáp ứng Share semantics.

### CONC_003 — race

Hai task cùng mutable access:

```axiom
spawn(move {
    data[0] = 1
})

spawn(move {
    data[0] = 2
})
```

Nếu ownership model không cho phép → reject.

### CONC_004 — Mutex

```axiom
lock(data)
data.value += 1
unlock(data)
```

→ accept nếu abstraction cung cấp safe synchronization.

---

# 12. Async

### ASYNC_001

```axiom
async fn work() {
    let data = make_buffer()

    await something()

    use(data)
}
```

Compiler phải đưa `data` vào async state machine nếu cần.

Semantic:

```text
before await:
    data OWNED

suspend:
    data remains alive

resume:
    data OWNED

end:
    DROP data
```

### ASYNC_002

Task có thể migrate giữa threads:

```text
task → thread A
      ↓
await
      ↓
thread B
```

→ captured state phải đáp ứng `Send`.

Nếu local executor:

```text
spawn_local(...)
```

thì requirement có thể khác.

---

# 13. ABI

### ABI_001

```axiom
@repr(C)
struct Point {
    x: f32
    y: f32
}
```

→ C-compatible layout.

### ABI_002

Native struct:

```axiom
struct Point {
    x: f32
    y: f32
}
```

Không được test physical field order như một guarantee.

### ABI_003

```axiom
extern @abi(C) fn foo(...)
```

→ calling convention phải là C ABI.

---

# 14. Allocation optimization

Một test rất quan trọng:

```axiom
fn make_point() -> Point {
    Point{10, 20}
}
```

Không được test:

```text
"Point phải nằm stack"
```

hay:

```text
"Point phải được allocate"
```

Thay vào đó test:

```text
semantic result == Point{10,20}
```

Compiler được phép:

```text
stack
register
caller allocation
return registers
```

Đây là cách conformance suite **không khóa compiler vào implementation**.

---

# 15. Tôi đề xuất thêm một loại test đặc biệt: `INVARIANT`

Không chỉ:

```text
PASS
FAIL
```

mà:

```text
INVARIANT
```

Ví dụ:

```text
TEST: OWN_MOVE_001
EXPECT: REJECT

INVARIANT:
    no READ after MOVE
```

hoặc:

```text
TEST: VIEW_002
EXPECT: REJECT

INVARIANT:
    view lifetime <= owner lifetime
```

hoặc:

```text
TEST: ABI_001
EXPECT: PASS

INVARIANT:
    repr(C) layout compatible with target C ABI
```

Điều này cực kỳ hữu ích cho AI agent.

---

# 16. Bộ test phải có 3 tầng

Tôi sẽ không chỉ tạo source test.

### Tier 1 — Semantic tests

```text
source → accept/reject
```

### Tier 2 — IR tests

```text
source → MIR
```

Kiểm tra:

```text
MOVE
DROP
VIEW
BRANCH
SUSPEND
ATOMIC
```

### Tier 3 — executable tests

```text
source
 ↓
MIR
 ↓
machine code
 ↓
execute
 ↓
expected output
```

Ví dụ:

```text
tests/
├── semantic/
├── mir/
└── runtime/
```

---

# 17. Và thêm một nguyên tắc cực kỳ quan trọng

**Không được snapshot toàn bộ MIR để kiểm tra compiler.**

Nếu snapshot:

```text
EXPECTED MIR:
t1 = ALLOC stack
t2 = LOAD ...
```

thì compiler sẽ bị khóa vào implementation.

Thay vào đó kiểm tra semantic properties:

```text
must_contain MOVE
must_contain DROP
must_not_contain invalid_access
must_preserve evaluation_order
```

Ví dụ:

```text
// EXPECT_MIR
contains: MOVE(data)
contains: DROP(data)
not_contains: USE_AFTER_MOVE
```

Optimizer sau này thay đổi MIR vẫn không phá test.

---

# 18. Cấu trúc repository Axiom nên chuyển thành

```text
axiom/
│
├── spec/
│   ├── CORE.md
│   ├── SEMANTICS.md
│   ├── MEMORY.md
│   ├── TYPES.md
│   ├── CONCURRENCY.md
│   ├── ABI.md
│   ├── ERRORS.md
│   └── FREEZE-v0.1.md
│
├── tests/
│   ├── semantic/
│   │   ├── syntax/
│   │   ├── types/
│   │   ├── ownership/
│   │   ├── views/
│   │   ├── drop/
│   │   ├── traits/
│   │   ├── generics/
│   │   ├── concurrency/
│   │   ├── async/
│   │   ├── errors/
│   │   └── abi/
│   │
│   ├── mir/
│   └── runtime/
│
├── compiler/
│   ├── lexer/
│   ├── parser/
│   ├── ast/
│   ├── hir/
│   ├── types/
│   ├── ownership/
│   ├── mir/
│   ├── verifier/
│   ├── optimizer/
│   ├── lir/
│   └── backend/
│
└── tools/
    └── ax-test/
```

---

## Quan trọng nhất: từ đây Axiom có một “tam giác bất biến”

```text
                  SPEC
                   ▲
                   │
                   │
             CONFORMANCE
             TEST SUITE
             ▲       ▲
             │       │
             │       │
          COMPILER ──┘
```

**Spec nói compiler phải làm gì.**

**Test suite biến spec thành thứ có thể kiểm chứng.**

**Compiler không được tự định nghĩa semantics.**

Nếu compiler implementation gặp trường hợp chưa có trong spec:

```text
STOP
 ↓
classify
 ↓
clarification / implementation detail / semantic change
```

Không được để AI agent tự “đoán”.

---

### Bước tiếp theo tôi đề xuất

Sau bộ **72 test v0.1**, chúng ta nên làm một việc còn quan trọng hơn viết parser:

**thiết kế `AXIOM SEMANTIC IR / MIR v0.1` hoàn chỉnh.**

Cụ thể sẽ khóa:

```text
Value
Place
Move
Copy
View
MutView
Drop
Ownership state
Basic block
Branch
Phi
Call
Return
Alloc
Dealloc
Load
Store
Atomic
Spawn
Suspend
Resume
Panic
Trap
```

và quan trọng nhất là **ownership state machine + cleanup/drop elaboration + verifier rules**.

Nếu phần này được thiết kế đúng, sau đó AI agent có thể bắt đầu xây compiler mà **không cần tiếp tục suy đoán semantics của Axiom**.