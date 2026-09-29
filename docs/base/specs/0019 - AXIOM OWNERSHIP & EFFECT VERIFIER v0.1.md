Tiếp tục. Bây giờ ta nên **đóng băng AXIOM OWNERSHIP + EFFECT VERIFIER v0.1**. Đây là phần quyết định Axiom có đạt được mục tiêu “không có borrow syntax nhưng compiler vẫn đảm bảo memory safety” hay không.

Tôi đề xuất một thay đổi quan trọng so với cách mô tả trước: **effect không chỉ là READ/WRITE/MOVE**. Compiler cần biết *đối tượng nào*, *vùng nào*, và *quan hệ alias nào* bị tác động.

# AXIOM OWNERSHIP & EFFECT VERIFIER v0.1

## 1. Ba tầng phân tích

Compiler không nên gom tất cả thành một “borrow checker”.

Tách thành:

```text
                    Typed MIR
                       │
          ┌────────────┼────────────┐
          ▼            ▼            ▼
     Ownership      Access       Effects
       Analysis     Analysis      Analysis
          │            │            │
          └────────────┼────────────┘
                       ▼
                  Verification
                       │
                       ▼
                 VERIFIED MIR
```

### Ownership

Ai sở hữu resource?

### Access

Ai đang đọc/ghi vùng memory nào?

### Effect

Function/call có thể làm gì observable hoặc ảnh hưởng resource nào?

Ba thứ này liên quan nhưng **không đồng nhất**.

---

# 2. Access model

Tầng thấp nhất vẫn chỉ có:

```text
READ
WRITE
MOVE
DROP
```

Nhưng mỗi access phải gắn với một **place/region**.

Ví dụ:

```axiom
p.x
```

có thể được biểu diễn:

```text
PLACE:
    base = p
    projection = field(x)
    region = R17
    access = READ
```

Còn:

```axiom
p.x = 10
```

là:

```text
region = R17
access = WRITE
```

---

# 3. Region hierarchy

Đây là phần rất quan trọng.

Ví dụ:

```axiom
struct Person {
    name: String
    age: i32
}
```

Compiler có thể tạo:

```text
Person
 ├── R1 = entire Person
 ├── R2 = name
 └── R3 = age
```

Do đó:

```axiom
read(person.age)
```

không nhất thiết conflict với:

```axiom
write(person.name)
```

vì:

```text
R3 ≠ R2
```

Trong khi:

```axiom
write(person)
```

conflict với cả:

```text
read(person.age)
read(person.name)
```

vì:

```text
R1 ⊃ R2
R1 ⊃ R3
```

---

# 4. Region relation

Verifier cần tối thiểu bốn quan hệ:

```text
DISJOINT
SAME
CONTAINS
OVERLAPS
```

Ví dụ:

```text
Person
 ├── name
 └── age
```

thì:

```text
name ↔ age       DISJOINT

Person ↔ name    CONTAINS

name ↔ Person    CONTAINED_BY
```

Đối với array/slice:

```text
a[0..10]
a[5..15]
```

có thể:

```text
OVERLAPS
```

Nếu compiler không chứng minh được disjointness:

> phải coi chúng là potentially overlapping.

Đây là nguyên tắc **soundness over optimism**.

---

# 5. Access conflict matrix

Freeze:

| Existing | New | Kết quả |
|---|---|---|
| READ | READ | OK |
| READ | WRITE | ❌ |
| WRITE | READ | ❌ |
| WRITE | WRITE | ❌ |
| MOVE | anything | ❌ |
| DROP | anything | ❌ |
| anything | MOVE | ❌ |
| anything | DROP | ❌ |

Nhưng chỉ conflict nếu regions có thể overlap.

Ví dụ:

```axiom
read(p.age)
write(p.name)
```

→ OK.

```axiom
read(p)
write(p.age)
```

→ conflict.

---

# 6. Ownership state không chỉ nằm ở variable

Ví dụ:

```axiom
let p = Person(...)
```

không chỉ có:

```text
p = OWNED
```

Mà conceptually:

```text
p
├── name → OWNED
└── age  → OWNED
```

Tuy nhiên compiler **không cần expose field ownership cho programmer**.

Đây là internal path-sensitive ownership.

---

# 7. Partial move

Ví dụ:

```axiom
let p = Person(...)

consume(p.name)

print(p.age)
```

Có nên cho phép không?

**Có.**

Nếu `name` là non-Copy owning field và `age` độc lập:

```text
p
├── name → MOVED
└── age  → OWNED
```

thì:

```text
print(p.age)
```

vẫn hợp lệ.

Nhưng:

```axiom
print(p)
```

→ reject vì `p` đã partial-move.

Đây là một khả năng rất đáng có vì nó giúp Axiom tránh các workaround khó chịu.

---

# 8. Partial Drop

Sau:

```axiom
consume(p.name)
```

khi `p` kết thúc scope:

```text
drop(p)
```

không được drop `name` lần nữa.

MIR có thể:

```text
DROP_FIELD_IF_OWNED p.name
DROP_FIELD_IF_OWNED p.age
```

hoặc compiler canonicalize thành một cleanup operation tương đương.

Optimizer có thể loại bỏ các branch nếu ownership state đã biết.

---

# 9. Function effect summary

Bây giờ đến function call.

Ví dụ:

```axiom
fn read_age(p: view<Person>) -> i32 {
    p.age
}
```

Compiler có thể tạo summary:

```text
EFFECT:
    READ(arg0.age)
```

Function:

```axiom
fn set_age(p: mut_view<Person>, x: i32) {
    p.age = x
}
```

summary:

```text
WRITE(arg0.age)
```

Function:

```axiom
fn consume_file(f: File) {
    ...
}
```

summary:

```text
MOVE(arg0)
DROP(arg0)
```

---

# 10. Effect summary không được phụ thuộc implementation detail

Ví dụ:

```axiom
fn sum(v: view<i32>) -> i32
```

Nếu implementation đọc:

```text
v[0]
v[1]
...
```

summary có thể được normalize thành:

```text
READ(arg0)
```

Không cần expose từng array element.

Effect summary phục vụ verifier, không phải profiling.

---

# 11. Unknown effect

Đây là điểm quan trọng khi gọi function bên ngoài compiler knowledge.

Ví dụ:

```axiom
extern @abi(C) fn mystery(...)
```

Compiler không biết function đó làm gì.

Safe default:

```text
UNKNOWN
```

Nếu function nhận raw pointer:

```text
*mut T
```

thì compiler không thể giả định memory không bị sửa.

Ở safe boundary, cần explicit contract/FFI declaration.

Ví dụ conceptually:

```text
extern fn foo(
    p: view<i32>
)
    effects(read p)
```

hoặc ABI metadata tương đương.

Nếu không có contract:

> compiler phải conservatively assume possible effects.

---

# 12. Nhưng không để FFI làm Axiom quá bảo thủ

Unsafe FFI có thể dùng annotation:

```text
@ffi_effects(
    read(arg0),
    write(arg1)
)
extern @abi(C) fn process(...)
```

Đây không phải language programmer-facing effect system bắt buộc.

Nó là **compiler contract**.

Nếu contract sai:

```text
unsafe boundary
```

chịu trách nhiệm.

---

# 13. Conditional effects

Function có thể không phải lúc nào cũng MOVE.

Ví dụ:

```axiom
fn maybe_take(flag: bool, x: Buffer) -> Option<Buffer> {
    if flag {
        Some(x)
    } else {
        None
    }
}
```

Effect không thể chỉ là:

```text
MOVE(x)
```

một cách mù quáng.

Compiler cần path-sensitive state:

```text
flag=true:
    x → MOVED

flag=false:
    x → DROPPED
```

Nếu function trả `Option<Buffer>` thì semantics resource ownership phải được biểu diễn trong return value.

---

# 14. Return ownership

Ví dụ:

```axiom
fn make() -> Buffer
```

return value:

```text
OWNED
```

Caller:

```axiom
let x = make()
```

→ ownership transfer:

```text
callee result → x
```

Không có implicit copy.

---

# 15. Borrow/view qua function return

Ví dụ:

```axiom
fn first(v: view<i32>) -> view<i32> {
    v
}
```

Điều này phải được phép:

```text
input view
    ↓
output view
```

nhưng output provenance phải gắn với input:

```text
result.region = input.region
result.provenance = arg0
```

Do đó:

```axiom
fn bad() -> view<i32> {
    let x = [1,2,3]
    first(view(x))
}
```

vẫn reject.

Không được để function call “che giấu” dangling view.

---

# 16. Đây là nơi `view` trở thành capability

Tôi nghĩ đây là mô hình rất phù hợp với Axiom:

```text
OWN
 │
 ├── creates ──> view<T>
 │
 └── creates ──> mut_view<T>
```

`view<T>` không phải “con trỏ an toàn” đơn thuần.

Nó là:

> **quyền truy cập có giới hạn vào một region trong thời gian compiler chứng minh được.**

Do đó:

```text
view<T>
```

có:

```text
provenance
region
access = READ
```

và:

```text
mut_view<T>
```

có:

```text
provenance
region
access = WRITE
```

---

# 17. Closure capture

Đây là test rất quan trọng.

```axiom
fn test() {
    let x = Buffer.new()

    let f = || {
        use(x)
    }

    f()
}
```

Compiler biến closure environment thành conceptually:

```text
struct ClosureEnv {
    x: Buffer
}
```

Capture mode:

```text
MOVE
VIEW
MUT_VIEW
COPY
```

được compiler suy ra.

---

# 18. Closure không escape

Ví dụ:

```axiom
let x = 10

let f = || x + 1

f()
```

Compiler hoàn toàn có thể biến thành:

```text
x + 1
```

không closure allocation.

Không được để semantic requirement:

```text
"closure phải tồn tại như object"
```

---

# 19. Closure escape

Ví dụ:

```axiom
fn make() -> Fn() {
    let x = Buffer.new()

    || use(x)
}
```

Nếu closure sở hữu `x`:

```text
closure
 └── x: OWNED
```

thì hợp lệ nếu function type cho phép owning closure.

Không cần lifetime annotation.

---

# 20. Closure capture bằng view

```axiom
fn make() {
    let x = Buffer.new()

    let f = || read(x)

    ...
}
```

Compiler có thể chọn:

```text
capture x by view
```

nếu không cần ownership.

Nhưng nếu `f` escape scope của `x`:

```text
f → escapes
x → dies
```

→ compiler phải reject hoặc chọn capture-by-value nếu semantics cho phép.

Đây là một ví dụ rất hay cho nguyên tắc:

> **Capture mode là compiler decision khi semantics cho phép, không phải programmer phải viết mọi thứ.**

---

# 21. Loops

Ownership verifier phải là dataflow analysis.

Ví dụ:

```axiom
while condition {
    consume(x)
}
```

Sau iteration đầu:

```text
x = MOVED
```

Iteration thứ hai:

```text
consume(x)
```

→ reject.

Compiler không được chỉ kiểm tra syntax tree một lần.

---

# 22. Loop với reinitialization

Nhưng:

```axiom
while condition {
    let x = make_buffer()
    consume(x)
}
```

→ hợp lệ.

Mỗi iteration:

```text
UNINIT
 ↓
OWNED
 ↓
MOVED
 ↓
iteration end
```

Resource được cleanup đúng mỗi iteration.

---

# 23. Loop + view

```axiom
while condition {
    let v = view(data)
    process(v)
}
```

→ hợp lệ.

View hết semantic lifetime khi không còn cần thiết.

Không cần chờ lexical block nếu compiler chứng minh last-use sớm hơn.

Đây là một optimization rất quan trọng:

```text
lexical lifetime
      ≠
semantic lifetime
```

---

# 24. Last-use analysis

Ví dụ:

```axiom
let a = make_buffer()

use(a)

do_other_work()
```

Sau:

```text
use(a)
```

nếu `a` không còn được sử dụng:

```text
semantic lifetime(a) ends
```

Compiler có thể Drop sớm:

```text
use(a)
drop(a)

do_other_work()
```

miễn semantics cho phép.

Điều này có thể cải thiện memory pressure đáng kể.

---

# 25. Nhưng Drop timing không được tùy tiện

Đây là ranh giới cực kỳ quan trọng.

Compiler **có thể** kéo Drop sớm nếu:

```text
resource lifetime semantics
```

cho phép.

Nhưng không được thay đổi observable resource behavior.

Ví dụ nếu programmer có:

```text
File
Socket
Mutex guard
```

thì thời điểm release có thể observable.

Do đó Axiom cần một khái niệm nội bộ:

```text
DROP_OBSERVABLE
```

Nếu resource semantics yêu cầu lexical/specified lifetime, optimizer không được tùy ý kéo Drop vượt qua observable boundary.

---

# 26. Điều này dẫn tới Resource Effect

Function/type có thể có resource semantics:

```text
DROP
DROP_OBSERVABLE
```

Ví dụ:

```text
MutexGuard
```

release mutex khi Drop → observable synchronization effect.

Compiler không được biến:

```text
lock
work
drop
```

thành:

```text
lock
drop
work
```

chỉ vì “ownership đã hết”.

---

# 27. Vì vậy Effect System v0.1 nên có 2 lớp

### Semantic effects

Compiler bắt buộc hiểu:

```text
READ
WRITE
MOVE
DROP
ALLOC
SUSPEND
```

### Observable effects

Optimizer phải bảo toàn:

```text
IO
ATOMIC
SYNC
VOLATILE
FFI
PANIC
TRAP
RESOURCE_RELEASE
```

Ta có:

```text
                     EFFECT
                       │
            ┌──────────┴──────────┐
            ▼                     ▼
       INTERNAL               OBSERVABLE
       semantic                semantic
            │                     │
      optimization           preservation
        allowed                required
```

---

# 28. Concurrency effects

Function:

```axiom
fn increment(x: mut_view<i32>)
```

summary:

```text
WRITE(arg0)
```

Nếu gọi từ hai contexts mà alias:

```text
R1 == R2
```

thì:

```text
WRITE(R1)
WRITE(R2)
```

→ race.

Nếu nằm dưới Mutex:

```text
LOCK
WRITE
UNLOCK
```

thì synchronization establishes happens-before.

---

# 29. Atomics

Atomic operation không được xử lý như ordinary `LOAD/STORE`.

MIR:

```text
ATOMIC_LOAD
ATOMIC_STORE
ATOMIC_RMW
ATOMIC_CAS
```

phải mang:

```text
memory_order
```

ví dụ:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

Optimizer không được biến atomic thành ordinary load/store nếu làm thay đổi concurrency semantics.

---

# 30. `Send` checking

Định nghĩa freeze:

```text
Send(T)
=
T có thể chuyển ownership sang execution context khác
mà không tạo ra unsafe shared mutable state.
```

Ví dụ:

```text
i32       → Send
String    → Send nếu backing storage transferable
Mutex<T>  → Send theo primitive semantics
raw ptr   → không mặc định Send
```

Không nên chỉ có rule:

```text
"mọi pointer = !Send"
```

vì có thể có system abstraction chứng minh pointer ownership hợp lệ.

---

# 31. `Share`

Freeze:

```text
Share(T)
=
T có thể được immutable-share giữa contexts
mà không phá memory/concurrency safety.
```

Do đó:

```text
Send(T) ≠ Share(T)
```

Một type có thể:

```text
Send = yes
Share = no
```

đặc biệt với exclusive ownership.

---

# 32. Shared mutable state

Axiom không cấm shared mutable state về mặt vật lý.

Nó yêu cầu:

```text
explicit synchronization
```

Ví dụ:

```text
Arc<Mutex<T>>
```

hoặc atomic abstraction.

Compiler không cần hiểu mọi Mutex implementation nếu library cung cấp trusted semantic contract.

---

# 33. Trusted library boundary

Đây là điều rất cần cho mục tiêu “compiler nhỏ nhưng language mạnh”.

Không thể hardcode:

```text
Mutex
Channel
Arc
Vec
HashMap
```

tất cả vào compiler.

Thay vào đó:

```text
compiler-known semantic properties
+
library contracts
```

Ví dụ:

```text
Mutex<T>
    Send
    Share
    synchronization boundary
```

Compiler biết **contract**, không cần biết implementation.

---

# 34. Generic ownership

Ví dụ:

```axiom
fn consume<T>(x: T) {
    use(x)
}
```

Không thể biết `T` Copy hay Move tại generic definition.

Compiler phải type-check theo capability:

```text
T
├── Copy ?
├── Drop ?
├── Send ?
├── Share ?
└── Sized ?
```

Nếu function yêu cầu ownership-consuming operation:

```text
consume<T>
```

thì nó phải hợp lệ cho cả `Copy` và non-Copy.

`Copy` chỉ thay đổi cách compiler thực hiện việc transfer.

---

# 35. Generic constraint

Nếu function cần Share:

```axiom
fn read_parallel<T: Share>(x: T) {
    ...
}
```

compiler yêu cầu:

```text
Share(T) = true
```

Đây là constraint semantics, không phải runtime check.

---

# 36. Trait dispatch + ownership

Static dispatch:

```axiom
trait Processor {
    fn process(self: mut_view<Self>)
}
```

Generic:

```axiom
fn run<T: Processor>(x: mut_view<T>) {
    x.process()
}
```

Specialization:

```text
run<FileProcessor>
```

→ direct call.

Ownership verifier phải chạy **sau type/trait resolution**, trước optimization.

Không được để dynamic dispatch làm mất safety information.

---

# 37. Dynamic dispatch

Nếu programmer explicit:

```text
dyn Processor
```

runtime representation có thể:

```text
data pointer
dispatch pointer
```

Nhưng:

```text
dyn Processor
```

phải vẫn mang semantic information về:

```text
ownership
access
Send
Share
```

Ví dụ dynamic object không tự nhiên trở thành `Share`.

---

# 38. Verifier algorithm

Tôi đề xuất compiler v0.1 dùng dataflow fixpoint:

```text
MIR CFG
   ↓
initial state
   ↓
forward dataflow
   ↓
merge states at join
   ↓
iterate until fixed point
   ↓
verify accesses
   ↓
verify cleanup
   ↓
VERIFIED
```

State conceptually:

```text
VerifierState {
    locals
    ownership
    initialization
    regions
    active_views
    effects
    cleanup
    concurrency
}
```

---

# 39. Merge state

Ví dụ:

```text
       bb0
      /   \
    bb1   bb2
      \   /
       bb3
```

Nếu:

```text
bb1: x = OWNED
bb2: x = MOVED
```

thì tại `bb3`:

```text
x = ?
```

Không được coi là OWNED.

Trạng thái phải trở thành:

```text
MAYBE_OWNED
```

và nếu `use(x)` yêu cầu OWNED:

→ reject.

---

# 40. Các trạng thái internal

Không nhất thiết chỉ:

```text
UNINIT
OWNED
MOVED
DROPPED
```

Verifier nên có:

```text
UNINIT
OWNED
PARTIAL
MOVED
DROPPED
MAYBE_OWNED
MAYBE_MOVED
```

Nhưng đây là **implementation state**, không phải language semantics mới.

Semantics vẫn chỉ có:

```text
valid
invalid
```

---

# 41. Diagnostic

Đây là chỗ Axiom có thể tốt hơn Rust/C++ rất nhiều.

Thay vì:

```text
borrowed value does not live long enough
```

Axiom nên nói:

```text
AX_VIEW_0007

view may outlive its owner

view:
    x_view

owner:
    buffer

owner lifetime:
    local scope [12..18]

view escapes through:
    return value

suggestion:
    return an owning Buffer instead
```

AI agent và IDE đều có thể parse JSON:

```json
{
  "code": "AX_VIEW_0007",
  "kind": "dangling_view",
  "owner": "buffer",
  "view": "x_view",
  "owner_scope": "...",
  "view_escape": "return"
}
```

---

# 42. Freeze invariant

Tôi đề xuất thêm nhóm invariant chính thức:

```text
AOV-01
Every safe memory access has a valid ownership/access proof.

AOV-02
Every owning value has exactly one active ownership state.

AOV-03
A moved value cannot be read, written, moved, or dropped again.

AOV-04
A dropped value cannot be accessed.

AOV-05
A safe view cannot outlive its provenance.

AOV-06
Conflicting accesses require disjoint regions or explicit synchronization.

AOV-07
Partial moves are tracked structurally.

AOV-08
Cleanup is complete on every terminating control-flow path.

AOV-09
Function summaries are conservative.

AOV-10
Unknown unsafe/FFI effects cannot be assumed harmless.

AOV-11
Send and Share are independent properties.

AOV-12
Async state surviving suspension obeys its execution-context requirements.

AOV-13
Optimizer cannot invalidate a verified ownership/access proof.

AOV-14
Observable resource effects must be preserved.

AOV-15
Verifier semantics do not depend on a specific backend.
```

---

# 43. Điều quan trọng nhất tôi muốn khóa

Axiom **không có “borrow checker” như một feature ngôn ngữ**.

Thay vào đó có:

```text
                 Axiom compiler
                       │
            ┌──────────┼──────────┐
            ▼          ▼          ▼
        Ownership    Regions    Effects
            │          │          │
            └──────────┼──────────┘
                       ▼
                    Verifier
```

Programmer chỉ nhìn thấy:

```text
owning value
view
mut_view
unsafe
Send
Share
```

Compiler mới nhìn thấy:

```text
regions
provenance
dataflow
partial moves
effect summaries
alias sets
cleanup graph
escape graph
```

Đây chính là cách đạt mục tiêu ban đầu của bạn:

> **Ngôn ngữ có thể mạnh và compiler rất phức tạp, nhưng programmer không phải gánh sự phức tạp đó.**

---

## Và sau bước này, Axiom đã có một “semantic engine” khá hoàn chỉnh

```text
SOURCE
  │
  ▼
TYPE SYSTEM
  │
  ▼
OWNERSHIP
  │
  ├── MOVE
  ├── COPY
  ├── DROP
  └── PARTIAL MOVE
  │
  ▼
REGION / ALIAS
  │
  ├── READ
  ├── WRITE
  ├── VIEW
  └── MUT_VIEW
  │
  ▼
EFFECT
  │
  ├── INTERNAL
  └── OBSERVABLE
  │
  ▼
CONCURRENCY
  │
  ├── Send
  ├── Share
  ├── Atomic
  └── Sync
  │
  ▼
VERIFIER
  │
  ▼
VERIFIED MIR
```

**Bây giờ tôi sẽ không thêm feature ngôn ngữ nữa.** Bước kế tiếp hợp lý là lấy toàn bộ hệ thống trên và thiết kế **10 chương trình “adversarial”** — những chương trình cố tình phá ownership/view/Drop/Send/async/aliasing — rồi mô phỏng chính xác **AST → HIR → MIR → verifier state → accept/reject** cho từng chương trình. Đây sẽ là bài kiểm tra xem semantics Axiom có thực sự kín hay vẫn còn lỗ hổng trước khi bắt đầu code compiler.