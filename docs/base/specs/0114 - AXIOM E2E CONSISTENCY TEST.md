Tiếp tục. Bây giờ chuyển sang **End-to-End Consistency Test**. Tôi sẽ không thêm feature mới; mục tiêu là kiểm tra xem các luật đã chốt có thực sự ghép lại thành một ngôn ngữ có thể implement được hay không.

# AXIOM E2E CONSISTENCY TEST

Ta dùng một tiêu chuẩn rất nghiêm:

> Với mỗi chương trình, compiler phải suy ra được semantics từ source mà không cần heuristic hoặc “đoán ý định”.

---

# 1. Program A — Hello World

```axiom
fn main() {
    println("Hello, world!")
}
```

Pipeline:

```text
Source
  ↓
AST
  ↓
Call println
  ↓
String literal → Text
  ↓
implicit temporary view<Text>
  ↓
CALL println
  ↓
DROP temporary
  ↓
return ()
```

MIR:

```text
t0 = CONST_TEXT "Hello, world!"
t1 = VIEW t0
CALL println(t1)
DROP t0
RETURN ()
```

Optimization có thể biến toàn bộ thành:

```text
CALL println(const_data)
RETURN
```

Không cần:

- heap
- GC
- runtime object
- reference counting
- exception runtime.

**Kết quả: PASS.**

---

# 2. Program B — Struct + method

```axiom
struct Vec2 {
    x: f32
    y: f32
}

impl Vec2 {
    fn length(self: view<Self>) -> f32 {
        sqrt(self.x * self.x + self.y * self.y)
    }
}

fn main() {
    let v = Vec2 { x: 3.0, y: 4.0 }
    let x = v.length()
    println(x)
}
```

Method:

```text
v.length()
```

desugar:

```text
length(view(v))
```

Ownership:

```text
v = OWNED
```

Trong `length`:

```text
view(v)
```

là ephemeral capability.

Sau call:

```text
view(v) → dead
v → OWNED
```

Không có borrow/lifetime syntax.

### Machine optimization

Compiler có thể inline:

```text
sqrt(v.x*v.x + v.y*v.y)
```

và thậm chí scalarize `v`.

**PASS.**

---

# 3. Program C — Generic + trait

```axiom
trait AddOne {
    fn add_one(self: view<Self>) -> Self
}

fn twice<T: AddOne>(x: T) -> T {
    x.add_one().add_one()
}
```

Có một điểm semantic cần sửa nhẹ.

Nếu:

```text
T
```

không `Copy`, `view<Self>` không thể trả owning `Self` mà không có copy/clone contract.

Do đó trait này phải là:

```axiom
trait AddOne: Copy {
    fn add_one(self: view<Self>) -> Self
}
```

hoặc API phải consume:

```axiom
trait AddOne {
    fn add_one(self) -> Self
}
```

Tôi thích phương án thứ hai hơn cho generic value transformations.

Ví dụ:

```axiom
trait AddOne {
    fn add_one(self) -> Self
}
```

thì:

```text
x
 ↓ MOVE
add_one
 ↓
new T
 ↓
add_one
```

Không cần `Copy`.

### Phát hiện

Surface syntax hiện tại chưa quy định đủ rõ **receiver ownership mode**.

Chúng ta đang có:

```text
self
self: view<Self>
self: mut_view<Self>
```

Đây thực tế rất tốt:

| Receiver | Meaning |
|---|---|
| `self` | consume/move |
| `self: view<Self>` | read |
| `self: mut_view<Self>` | mutate |

### Quyết định

Đây là **ba receiver modes chính thức**.

**AMETHOD-22 — Receiver Mode Is Explicit In Function Type**

---

# 4. Program D — Vec + view

```axiom
fn sum(v: view<i32>) -> i32 {
    var result = 0

    for x in v {
        result += x
    }

    result
}
```

Caller:

```axiom
let values = Vec.from([1, 2, 3])
let result = sum(values)
```

Implicit owner → view chỉ xảy ra ở call boundary:

```text
values
  ↓
view(values)
  ↓
sum
```

Sau call:

```text
view dead
values still OWNED
```

### PASS

Điểm quan trọng:

```text
sum(values)
```

không biến `values` thành moved value.

---

# 5. Program E — mut_view

```axiom
fn sort(v: mut_view<i32>) {
    ...
}

fn main() {
    var values = Vec.from([3, 1, 2])

    sort(values)

    println(values)
}
```

Trong `sort`:

```text
values
 ↓
WRITE capability
```

Sau return:

```text
WRITE capability ends
values OWNED
```

Sau đó read:

```text
view(values)
```

hợp lệ.

### PASS

---

# 6. Program F — conflicting views

```axiom
var data = Buffer(...)

let a = view(data)
let b = mut_view(data)

use(a)
use(b)
```

Compiler:

```text
a = READ
b = WRITE
```

và capability overlap:

```text
Region(a) OVERLAPS Region(b)
```

→ reject.

Nhưng:

```axiom
let a = view(data)
use(a)

let b = mut_view(data)
use(b)
```

→ PASS.

Không cần explicit lifetime.

Compiler dùng last-use.

---

# 7. Program G — Partial move

```axiom
struct User {
    name: Text
    age: i32
}

fn main() {
    let user = User {
        name: "Alice",
        age: 20
    }

    let name = user.name
    println(user.age)
}
```

Sau field move:

```text
user:
    name = MOVED
    age  = OWNED
```

`user.age` hợp lệ.

`user.name`:

```text
ERROR AX_MOVE_...
```

Scope end:

```text
DROP name
DROP user.age
```

Không double-drop.

### PASS.

---

# 8. Program H — Partial move + custom Drop

```axiom
struct User {
    name: Text
    file: File
}

impl Drop for User {
    ...
}
```

Sau đó:

```axiom
let name = user.name
```

→ reject.

Đây là restriction đã thống nhất:

```text
custom Drop
    +
partial move
    =
forbidden
```

### PASS.

---

# 9. Program I — Result + ?

```axiom
fn load(path: view<Text>) -> Result<Text, Error> {
    let file = File.open(path)?
    let data = file.read_all()?
    Ok(data)
}
```

Nếu `read_all()` trả `Err`:

```text
DROP file
RETURN Err(...)
```

Nếu thành công:

```text
file
 ↓
scope end
 ↓
DROP
```

### Không có exception.

### Không có hidden cleanup runtime.

### PASS.

---

# 10. Program J — Async

```axiom
async fn load(path: Text) -> Result<Bytes, Error> {
    let request = make_request(path)

    let response = request.send().await?

    response.read_all().await?
}
```

State machine:

```text
State0:
    path
    request

await send()
    ↓

State1:
    response
```

`request` không còn cần sau await → không lưu.

`path` có thể được consume vào request và cũng biến mất.

Future state tối thiểu.

### PASS.

---

# 11. Async + view

```axiom
async fn process(data: view<Bytes>) {
    inspect(data)
    await something()
}
```

Compiler thấy:

```text
data last-use
      ↓
before await
```

→ PASS.

Nhưng:

```axiom
async fn process(data: view<Bytes>) {
    await something()
    inspect(data)
}
```

→ reject.

### PASS.

---

# 12. Async + owned state

```axiom
async fn process(data: Bytes) {
    await something()
    consume(data)
}
```

Compiler:

```text
data
 ↓
owned by Future
 ↓
await
 ↓
resume
 ↓
consume
```

Nếu Future bị drop khi suspended:

```text
DROP data
```

### PASS.

---

# 13. Spawn

```axiom
fn start(data: Buffer) {
    spawn(move || {
        process(data)
    })
}
```

Ownership:

```text
start.data
   ↓ MOVE
closure.data
   ↓ MOVE
task.state
```

Nếu task migratable:

```text
task: Send
```

Compiler kiểm tra.

### PASS.

---

# 14. Spawn + borrowed data

```axiom
fn start(data: Buffer) {
    spawn(|| {
        process(data)
    })
}
```

Nếu closure giữ capability vào `data`:

```text
data lifetime = start()
closure lifetime > start()
```

→ reject.

Compiler không cần nói:

```text
borrowed value does not live long enough
```

theo kiểu lifetime syntax.

Diagnostic có thể nói đơn giản:

```text
AX_VIEW_0007:
captured view may outlive its owner
```

### PASS.

---

# 15. Channel

```axiom
let (tx, rx) = channel<Buffer>()

spawn(move || {
    tx.send(buffer)?
})

let buffer = rx.receive()?
```

Ownership:

```text
buffer
 ↓
channel
 ↓
consumer
```

Không copy.

### PASS.

---

# 16. Atomic

```axiom
static COUNTER: Atomic<u64> = Atomic.init(0)

fn increment() {
    COUNTER.fetch_add(1, Relaxed)
}
```

No ordinary mutable view.

Atomic operation có semantics riêng.

### PASS.

---

# 17. Unsafe

```axiom
unsafe fn from_raw(
    ptr: *const u8,
    len: usize
) -> view<u8> {
    ...
}
```

Boundary:

```text
raw pointer
   ↓
unsafe validation
   ↓
view
```

Sau đó compiler tracking bình thường.

Nếu:

```axiom
let v = from_raw(ptr, len)
```

thì `v` vẫn là capability mà verifier phải theo dõi.

### PASS.

---

# 18. FFI

```axiom
extern "C" fn c_process(
    ptr: *const u8,
    len: usize
) -> i32
```

Axiom gọi:

```text
raw ABI
```

Không tự động chuyển:

```text
view<Text>
```

thành C pointer.

Wrapper:

```axiom
fn process(data: view<Bytes>) -> Result<(), Error> {
    ...
}
```

có thể thực hiện conversion an toàn.

### PASS.

---

# 19. Recursive type

```axiom
struct Node {
    value: i32
    next: Option<Box<Node>>
}
```

Layout finite.

Drop:

```text
Node
 ↓
Box
 ↓
Node
 ↓
...
```

Compiler có thể generate iterative drop nếu recursion depth lớn để tránh stack overflow trong destructor implementation.

Đây là implementation optimization, không thay đổi semantics.

### PASS.

---

# 20. Graph

```axiom
let graph = Graph<Node>::new()

let a = graph.add(Node(...))
let b = graph.add(Node(...))

graph.connect(a, b)
graph.connect(b, a)
```

Ownership:

```text
graph
 ├── Node A
 └── Node B

a = Handle<Node>
b = Handle<Node>
```

Không có ownership cycle.

Nếu node bị remove:

```text
generation++
```

handle cũ trở thành stale.

### PASS.

---

# 21. Public API

```axiom
struct InternalState {
    ...
}

trait Service {
    ...
}

pub fn create() -> impl Service {
    ...
}
```

Hợp lệ nếu `Service` public.

Concrete `InternalState` private không lộ ra.

Nếu:

```axiom
pub fn create() -> InternalState
```

→ reject.

### PASS.

---

# 22. `@repr(C)`

```axiom
@repr(C)
struct CConfig {
    version: u32
    flags: u32
    data: *const u8
}
```

Compiler phải giữ C-compatible layout.

Nhưng:

```axiom
struct Internal {
    ...
}
```

không có layout promise.

### PASS.

---

# 23. GPU

Ví dụ conceptually:

```axiom
@kernel
fn add(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
) {
    ...
}
```

Kernel verifier phải kiểm tra:

```text
a → READ
b → READ
out → WRITE
```

Nếu compiler không chứng minh:

```text
out ∩ a = ∅
out ∩ b = ∅
```

thì kernel safe API không được chấp nhận.

Hoặc API phải biểu diễn non-overlap contract.

Điều này cho thấy GPU thực sự dùng cùng capability model.

### PASS.

---

# 24. Phát hiện quan trọng từ E2E

Qua 23 chương trình, có một điểm cần bổ sung:

## Capability provenance phải là first-class compiler concept.

Compiler cần biết:

```text
view<T>
```

đến từ đâu.

Ví dụ:

```text
owner A
  ↓
view A.field
  ↓
view A.field.subfield
```

Nếu chỉ lưu:

```text
pointer + length
```

thì verifier không đủ thông tin để chứng minh lifetime/aliasing.

Do đó MIR cần metadata:

```text
CapabilityId
OwnerId
Region
Access
Provenance
```

Ví dụ:

```text
VIEW %v1
    owner=%obj3
    region=%obj3.field[2]
    access=READ
```

Sau lowering sang LIR:

```text
ptr + len
```

metadata có thể bị erase.

### Invariant mới

**ACAP-20 — Every Safe View Has Compiler-Tracked Provenance**

**ACAP-21 — Capability Provenance May Be Erased After Verification**

---

# 25. Phát hiện thứ hai: "last-use" không chỉ là optimization

Trước đây ta coi:

```text
last-use
```

chủ yếu là optimization.

Thực ra nó là **semantic input cho capability validity**.

Ví dụ:

```axiom
let x = view(v)
use(x)
v.push(1)
```

`push` hợp lệ vì capability `x` đã kết thúc.

Vì vậy compiler phải có:

```text
semantic liveness
```

trước Verified MIR.

Nhưng vẫn cần phân biệt:

```text
semantic lifetime
```

với:

```text
physical register lifetime
```

### Invariant

**ACAP-22 — Capability Lifetime Is Determined Semantically Before Physical Optimization**

---

# 26. Phát hiện thứ ba: `view` không nhất thiết phải là sequence

Đây là một refinement quan trọng.

Ban đầu ta mô tả:

```text
view<T>
```

như contiguous view.

Nhưng qua:

```text
user.profile.name
mutex guard
packed field
GPU buffer
external memory
```

thấy rõ hơn:

> `view<T>` là **non-owning typed capability**, không phải đơn thuần "slice".

Một sequence view chỉ là một specialization/use case:

```text
view<T>
```

với extent.

Ví dụ:

```text
view<User>
view<Text>
view<i32>
view<Array<T,N>>
```

đều có thể tồn tại.

### Đề nghị terminology chính thức

```text
view<T>
```

= typed read capability.

```text
mut_view<T>
```

= typed exclusive-write capability.

Sequence APIs có thêm extent:

```text
view<T> + length
```

nhưng representation là implementation detail.

Điều này tốt hơn nhiều so với biến `view<T>` thành "slice type".

---

# 27. Phát hiện thứ tư: Receiver `self` thực sự rất đẹp

Ba dạng:

```axiom
fn f(self)
fn f(self: view<Self>)
fn f(self: mut_view<Self>)
```

đã đủ để biểu diễn:

```text
consume
read
mutate
```

Đây nên là **canonical ownership vocabulary của method API**.

Không cần:

```text
&self
&mut self
self by value
```

và cũng không cần lifetime annotation.

---

# 28. E2E verdict

Sau 23 chương trình:

| Domain | Kết quả |
|---|---|
| Value semantics | PASS |
| Move/Copy | PASS |
| Partial move | PASS |
| Drop | PASS |
| Views | PASS |
| Mutation | PASS |
| Result/`?` | PASS |
| Async | PASS |
| Spawn | PASS |
| Send/Share | PASS |
| Channel | PASS |
| Atomic | PASS |
| Unsafe | PASS |
| FFI | PASS |
| Generic | PASS |
| Traits | PASS |
| Enum/match | PASS |
| Closure | PASS |
| Static | PASS |
| ABI | PASS |
| Recursive data | PASS |
| Graph/Handle | PASS |
| GPU | PASS |

**Không phát hiện contradiction kiến trúc.**

Nhưng có ba refinement cần đưa vào spec:

```text
ACAP-20
ACAP-21
ACAP-22
```

và một clarification:

```text
view<T> = typed non-owning capability
```

thay vì coi nó chỉ là slice.

---

# 29. Bây giờ chuyển sang Semantic Freeze

Tôi cho rằng chúng ta đã đủ điều kiện để bắt đầu **Semantic Freeze v0.1**.

Nhưng trước khi gọi nó là frozen, cần làm một việc cực kỳ quan trọng:

## Tách toàn bộ specification thành 5 tầng

### Layer 1 — Language Semantics

Những thứ programmer có quyền dựa vào:

```text
types
values
ownership
move/copy
view
mutation
drop
control flow
match
result
panic
traits
generic
async semantics
concurrency safety
unsafe boundary
```

### Layer 2 — Compiler Semantics

Compiler bắt buộc phải duy trì:

```text
provenance
region
capability
ownership state
drop state
trait resolution
effect/concurrency facts
```

### Layer 3 — Optimization

Compiler **được phép**:

```text
inline
scalarize
eliminate allocation
eliminate bounds check
monomorphize
specialize
reorder
vectorize
merge/split storage
eliminate closure
eliminate Future
```

miễn semantics giữ nguyên.

### Layer 4 — Representation / ABI

Chỉ cố định khi có contract:

```text
@repr(C)
@repr(transparent)
extern "C"
@align
@export
```

### Layer 5 — Implementation

Hoàn toàn không phải language guarantee:

```text
LLVM
custom backend
SSA
register allocator
GC-like internal algorithm
arena compiler allocation
specific machine instruction
specific stack layout
```

---

# 30. Nguyên tắc freeze quan trọng nhất

Từ giờ trở đi, nếu một đề xuất mới muốn thêm vào Axiom, phải trả lời:

> **Nó thay đổi Layer 1 hay chỉ là Layer 2–5?**

Nếu chỉ là:

```text
"compiler có thể làm X"
```

thì **không được biến nó thành language feature** trừ khi programmer cần semantic guarantee.

Ví dụ:

> "Compiler có thể tự phát hiện allocation không cần thiết."

→ optimizer.

Không cần:

```text
@stack
```

trong language.

> "Object này phải có stable address."

→ semantic requirement.

Lúc đó mới cần một abstraction/storage contract.

Đây chính là cách tránh Axiom dần biến thành một ngôn ngữ có hàng trăm annotation tối ưu hóa.

---

## Bước tiếp theo

Tôi sẽ tiếp tục với **Semantic Freeze Audit**: đi xuyên toàn bộ các invariant `AMEM`, `AOWN`, `AVIEW`, `ADROP`, `AFERR`, `AMOD`, `ASURF`, `AASYNC`, `ACONC`, `AATOM`, `AFFI`, `AABI`, `ACOMP`, `AGPU` và phát hiện:

1. invariant nào trùng;
2. invariant nào mâu thuẫn;
3. invariant nào đang thiếu định nghĩa;
4. thuật ngữ nào đang được dùng với nhiều nghĩa;
5. cái gì thực sự là **language guarantee**;
6. cái gì phải chuyển xuống compiler/implementation.

Sau audit đó, ta sẽ có một **semantic core đóng băng thực sự**, thay vì chỉ có một danh sách feature dài.