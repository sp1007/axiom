Tiếp theo chúng ta chốt **AXIOM OWNERSHIP + CAPABILITY ANALYZER v0.1**. Đây là phần rất quan trọng vì nó quyết định Axiom có đạt được mục tiêu **“an toàn bộ nhớ nhưng không bắt lập trình viên học borrow checker”** hay không.

# AXIOM OWNERSHIP + CAPABILITY ANALYZER v0.1

## 1. Ranh giới của subsystem

Pipeline:

```text
Typed HIR
   │
   ├── Ownership Analysis
   ├── Initialization Analysis
   ├── Move Analysis
   ├── Capability / Region Analysis
   ├── Drop Analysis
   ├── Escape Analysis
   └── Concurrency / Send / Share Analysis
             │
             ▼
          MIR v0.1
             │
             ▼
        MIR Verifier
             │
             ▼
       Verified MIR
```

Điểm quan trọng:

> **Ownership Analyzer không phải một “Rust borrow checker” nằm trong compiler.**

Nó là một **semantic dataflow analyzer**.

Lập trình viên không viết:

```text
'a
&'a mut T
where 'a: 'b
```

và cũng không phải suy nghĩ:

> “Lifetime của reference này là bao lâu?”

Thay vào đó compiler tự xây:

```text
Owner
  │
  ├── capability
  │      └── region
  │
  └── lifetime
```

và chỉ báo lỗi khi một invariant thực sự bị vi phạm.

---

# 2. Hai loại state phải tách biệt

Một điểm rất quan trọng để tránh thiết kế analyzer bị rối.

### Semantic ownership state

Đây là trạng thái thật của object:

```text
UNINIT
OWNED
PARTIAL
MOVED
DROPPED
```

### Dataflow analysis state

Để xử lý branch/loop, compiler cần thêm trạng thái “có thể”.

Ví dụ:

```axiom
var x: Buffer

if condition {
    x = create()
}

print(x)
```

Sau `if`, compiler không thể nói đơn giản `x = OWNED`.

Nó cần internal state:

```text
MAYBE_UNINIT
MAYBE_OWNED
MAYBE_MOVED
```

Nhưng:

> **MAYBE_* không phải trạng thái ngôn ngữ.**

Chúng chỉ tồn tại trong analyzer.

---

# 3. Ownership State

Đề xuất lattice:

```text
                 UNKNOWN
                /       \
        MAYBE_UNINIT   MAYBE_OWNED
                           |
                      MAYBE_MOVED
                           |
                    ┌─────────────┐
                    │             │
                  OWNED         PARTIAL
                    │             │
                  MOVED        MOVED_FIELDS
                    │
                 DROPPED
```

Thực tế implementation không cần ép thành một lattice tuyến tính. Tốt hơn là dùng product state:

```text
InitState
    UNINIT
    INIT
    MAYBE_INIT

OwnershipState
    OWNED
    PARTIAL
    MOVED
    DROPPED
    MAYBE_OWNED
    MAYBE_MOVED
```

Điều này giúp compiler phân biệt:

```text
chưa khởi tạo
```

với:

```text
đã khởi tạo nhưng có thể đã move
```

---

# 4. Ownership gắn với Place

Không chỉ local variable.

Compiler cần mô hình:

```text
Place
 ├── Local
 ├── Field
 ├── Index
 └── Deref
```

Ví dụ:

```axiom
var user: User
user.name = "A"
user.age = 20
```

Analyzer có:

```text
Place(user)
Place(user.name)
Place(user.age)
```

Điều này cực kỳ quan trọng cho:

```axiom
let name = user.name
print(user.age)
```

Nếu `User` không có Drop tùy biến, compiler có thể biết:

```text
user.name → MOVED
user.age  → OWNED
```

Toàn bộ `user` chưa bị move.

---

# 5. Move

Quy tắc rất đơn giản:

```text
T : Copy
    → COPY

T : !Copy
    → MOVE
```

Ví dụ:

```axiom
let a = Buffer.create(100)
let b = a
```

Sau:

```text
a = MOVED
b = OWNED
```

Không nhất thiết có `memcpy`.

Đây là semantic transition:

```text
OWNED → MOVED
```

Compiler có thể thực hiện:

```text
register transfer
pointer transfer
SSA rename
memcpy
no physical operation
```

tùy optimization.

---

# 6. Copy

Ví dụ:

```axiom
let a: i32 = 10
let b = a
print(a)
```

`i32 : Copy`.

Do đó:

```text
a = OWNED
b = OWNED
```

Không có ownership transfer.

Nhưng:

> `Copy` là semantic property, không phải “bitwise memcpy được”.

Một type có thể:

```text
bitwise-copyable = true
Copy = false
```

nếu copy nó tạo ra vấn đề tài nguyên.

---

# 7. Clone

Không dùng Copy để biểu diễn deep duplication.

```axiom
let a = buffer
let b = a.clone()
```

Semantic:

```text
a = OWNED
b = OWNED
```

và `clone()` có thể:

```text
allocate
copy memory
duplicate resource
```

Compiler không được giả định nó rẻ.

---

# 8. Initialization Analysis

Ví dụ:

```axiom
var x: i32

if condition {
    x = 10
}

print(x)
```

Compiler kiểm tra:

```text
branch A → x = INIT
branch B → x = UNINIT
```

join:

```text
x = MAYBE_INIT
```

=> lỗi.

Nhưng:

```axiom
var x: i32

if condition {
    x = 10
} else {
    x = 20
}

print(x)
```

join:

```text
INIT + INIT
      ↓
     INIT
```

=> hợp lệ.

---

# 9. Move Analysis cũng phải path-sensitive

Ví dụ:

```axiom
let x = create()

if condition {
    consume(x)
}

print(x)
```

Một path:

```text
x → MOVED
```

Một path:

```text
x → OWNED
```

Join:

```text
x → MAYBE_MOVED
```

Do đó:

```text
print(x)
```

bị từ chối.

Nhưng:

```axiom
let x = create()

if condition {
    consume(x)
} else {
    consume(x)
}
```

Cả hai path đều:

```text
x → MOVED
```

=> hợp lệ nếu sau đó không dùng `x`.

---

# 10. Reinitialization

Một đặc điểm nên có để Axiom thân thiện hơn Rust-style ownership:

```axiom
var x = create()

consume(x)

x = create()

use(x)
```

Sau assignment:

```text
x:
MOVED
  ↓
UNINIT
  ↓
OWNED
```

Do đó dùng lại biến là hợp lệ.

Điều này đặc biệt hữu ích với:

```text
state machines
buffers
resource replacement
temporary objects
```

---

# 11. Partial Move

Ví dụ:

```axiom
struct User {
    name: Text
    age: i32
}
```

```axiom
let user = User {
    name: "Alice",
    age: 20
}

let name = user.name

print(user.age)
```

Compiler:

```text
user.name → MOVED
user.age  → OWNED
user      → PARTIAL
```

`user.age` vẫn dùng được.

---

# 12. Nhưng User-defined Drop thay đổi quy tắc

Ví dụ một resource type:

```axiom
struct File {
    handle: RawHandle
}
```

Nếu có user-defined Drop:

```text
impl Drop for File {
    ...
}
```

thì:

```axiom
let file = File.open()

let h = file.handle
```

không được phép partial move theo cách làm phá vỡ invariant của `Drop`.

Vì destructor vẫn phải nhận một object hợp lệ.

Do đó:

```text
Derived Drop
    → partial move có thể được

User-defined Drop
    → partial move forbidden
```

Đây là một trade-off rất đáng giữ vì nó làm Drop semantics đơn giản.

---

# 13. Capability Model

Axiom không coi `view` đơn giản là:

```text
pointer + length
```

ở tầng semantic.

Nó là:

```text
Capability {
    provenance
    region
    access
    validity
}
```

Ví dụ:

```axiom
fn print_name(name: view<Text>) {
    ...
}
```

Semantic:

```text
provenance = owner
region     = user.name
access     = READ
validity   = until required semantic use ends
```

---

# 14. Hai capability chính

## `view<T>`

```text
READ
```

Có thể duplicate:

```axiom
let a = view(x)
let b = a
```

vì hai capability đều chỉ đọc.

Nhưng đây **không phải `Copy`**.

Nó là property intrinsic của capability.

---

## `mut_view<T>`

```text
WRITE
```

và có tính:

```text
exclusive
```

Không được duplicate semantic capability.

```text
mut_view<T> → MOVE
```

---

# 15. Capability conflict matrix

| A | B | Kết quả |
|---|---|---|
| READ | READ | OK |
| READ | WRITE | ❌ |
| WRITE | READ | ❌ |
| WRITE | WRITE | ❌ |
| MOVE | READ | ❌ |
| MOVE | WRITE | ❌ |
| DROP | READ | ❌ |
| DROP | WRITE | ❌ |

Nhưng có một điều kiện:

> Chỉ conflict nếu regions có thể overlap.

---

# 16. Region Algebra

Compiler cần:

```text
SAME
DISJOINT
CONTAINS
CONTAINED_BY
OVERLAPS
UNKNOWN
```

Ví dụ:

```axiom
user.name
user.age
```

compiler biết:

```text
region(user.name) DISJOINT region(user.age)
```

nên:

```axiom
let a = mut_view(user.name)
let b = mut_view(user.age)
```

có thể hợp lệ.

Đây là một trong những điểm giúp Axiom giảm rất nhiều “borrow checker bureaucracy”.

---

# 17. Unknown không được đoán là Disjoint

Ví dụ:

```axiom
fn get_field(u: mut_view<User>) -> mut_view<Text>
```

Compiler không biết field nào.

Nếu:

```text
region A = UNKNOWN overlap B
```

thì safe code không được phép giả định:

```text
DISJOINT
```

Do đó có thể báo:

```text
AX_VIEW_0001:
cannot create overlapping mutable capabilities
```

Nếu API muốn đảm bảo disjoint, chính abstraction đó phải cung cấp semantic guarantee.

---

# 18. Owner → View

Không cần bắt người dùng viết:

```axiom
view(x)
```

khi chỉ truyền trực tiếp vào function:

```axiom
fn length(x: view<Text>) -> usize

let text = create_text()

length(text)
```

Compiler tự tạo ephemeral capability:

```text
text
  ↓
temporary READ capability
  ↓
length()
  ↓
capability ends
```

Nhưng:

```axiom
let v = text
```

không tự biến thành view.

Muốn giữ view:

```axiom
let v = view(text)
```

Điểm này rất quan trọng:

> **Implicit conversion chỉ được phép khi compiler biết capability không escape.**

---

# 19. Persistent View

```axiom
let v = view(buffer)
```

Compiler tạo:

```text
Owner(buffer)
     │
     └── Capability #17
             region = buffer
             READ
```

Trong khi capability còn live:

```text
buffer
```

không được:

```text
DROP
MOVE
RELOCATE
```

nếu hành động đó làm capability mất validity.

---

# 20. Vector relocation

Ví dụ:

```axiom
let v = Vec<i32>.new()

let x = view(v)

v.push(10)
```

Nếu `push()` có khả năng relocate storage thì:

```text
x → live capability
v.push()
   ↓
MAY_RELOCATE
```

=> compiler phải xử lý.

Có ba khả năng:

1. operation không relocate
2. compiler chứng minh không relocate
3. operation bị từ chối

Không được:

```text
reallocate
↓
dangling x
```

---

# 21. `reserve()` không tạo stable address

Không nên có semantics kiểu:

```text
reserve(100)
→ địa chỉ vĩnh viễn ổn định
```

`reserve()` chỉ đảm bảo capacity theo contract của collection.

Stable address phải là storage contract riêng.

Điều này cho compiler nhiều freedom hơn.

---

# 22. Escape Analysis

Đây là phần làm Axiom khác biệt mạnh.

Compiler phải tìm xem capability/owner có escape khỏi region hiện tại không.

Các escape boundary:

```text
return
global/static
heap storage
closure capture
spawn
thread migration
async suspension
FFI
unsafe boundary
```

Ví dụ:

```axiom
fn bad() -> view<i32> {
    var x = 10
    view(x)
}
```

`x` chết khi function return.

=> compiler từ chối.

---

# 23. Closure Capture

Ví dụ:

```axiom
let x = create()

let f = || print(x)
```

Compiler phân tích capture.

Có thể chọn:

```text
READ capture
```

nếu chỉ đọc.

Nếu closure mutate:

```axiom
let f = || {
    x.modify()
}
```

cần:

```text
MUT capability
```

Nếu closure cần ownership:

```axiom
let f = move || consume(x)
```

thì:

```text
x → MOVED into closure
```

---

# 24. `move` closure

`move` là một trong số ít trường hợp programmer nói rõ ownership.

```axiom
let task = move || {
    consume(buffer)
}
```

Semantics:

```text
buffer
   ↓
closure environment
   ↓
OWNED
```

Không cần lifetime annotation.

---

# 25. Async

Đây là boundary đặc biệt.

```axiom
async fn process(x: view<Data>) {
    something().await
    use(x)
}
```

Không cho phép view sống qua `.await`.

Lý do không phải vì “Rust-like rule”.

Mà vì Future có thể:

```text
suspend
move
resume
```

và view có thể mất provenance/validity.

Do đó:

```text
view/mut_view
       │
       └── await boundary
                ↓
              FORBIDDEN
```

Trong khi:

```text
owned value
```

có thể được đưa vào Future state machine.

---

# 26. Spawn

```axiom
spawn(move || {
    process(data)
})
```

Compiler kiểm tra environment.

Nếu task có thể chạy trên thread khác:

```text
captured ownership
        ↓
       Send?
```

Nếu không:

```text
AX_SEND_0001
```

Nếu task chỉ chạy local:

```axiom
spawn_local(...)
```

không cần `Send`.

---

# 27. Send và Share

Hai khái niệm phải giữ hoàn toàn riêng:

```text
Send
    ownership có thể chuyển sang execution context khác

Share
    có thể được nhiều execution context đọc/chia sẻ an toàn
```

Ví dụ:

```text
Arc<ImmutableData>
```

có thể:

```text
Share = yes
Send  = yes
```

Nhưng:

```text
non-thread-safe mutable object
```

có thể:

```text
Share = no
```

---

# 28. Unsafe Boundary

Ví dụ:

```axiom
unsafe {
    let p: *mut i32 = ...
    let v = make_mut_view(p, 10)
}
```

Unsafe không có nghĩa:

```text
compiler stop checking
```

Thay vào đó:

```text
unsafe operation
       ↓
trusted semantic precondition
       ↓
safe capability
       ↓
normal verifier resumes
```

Ví dụ capability:

```text
provenance = TRUSTED_UNSAFE
region     = [p, p+10)
access     = WRITE
validity   = contract-defined
```

Sau đó compiler vẫn kiểm tra:

```text
v + another_mut_view
```

có conflict hay không.

---

# 29. Drop Analysis

Drop phải được xử lý sau ownership analysis.

Ví dụ:

```axiom
fn f() {
    let a = create_a()
    let b = create_b()

    work()
}
```

Semantic cleanup:

```text
work()

DROP b
DROP a
```

Mặc định:

> reverse initialization/declaration order.

---

# 30. Early Return

```axiom
fn f() -> Result<()> {
    let a = create_a()
    let b = create_b()

    if error {
        return Err(...)
    }

    Ok(())
}
```

Compiler biến thành semantic cleanup:

```text
if error {
    DROP b
    DROP a
    return Err(...)
}
```

Không cần programmer viết cleanup.

---

# 31. Partial Move + Drop

Nếu:

```text
user.name → MOVED
user.age  → OWNED
```

thì Drop không được drop `name` lần nữa.

Compiler tạo:

```text
DROP_IF_OWNED(user.name)
DROP_IF_OWNED(user.age)
```

hoặc tối ưu thành control flow tương đương.

---

# 32. Explicit `drop`

Cho phép:

```axiom
let file = open()

use(file)

drop(file)

other_work()
```

Semantic:

```text
file:
OWNED
 ↓
DROPPED
```

Sau đó:

```axiom
use(file)
```

=> lỗi.

Nhưng:

```text
drop()
```

không đồng nghĩa bắt buộc:

```text
free()
```

Nó chỉ hoàn thành **resource lifetime**.

---

# 33. Allocation và Drop vẫn tách nhau

Ví dụ Arena:

```text
Arena lifetime
    │
    ├── Object A
    ├── Object B
    └── Object C
```

Drop object:

```text
resource cleanup
```

không nhất thiết:

```text
individual deallocation
```

Arena có thể giải phóng toàn bộ storage sau.

Điều này cho phép:

```text
Drop semantics
```

và:

```text
Memory allocator semantics
```

độc lập.

---

# 34. MIR Facts

Ownership analyzer không nên trực tiếp sinh machine code.

Nó xuất ra các facts:

```text
OwnershipFact
CapabilityFact
DropFact
EscapeFact
ConcurrencyFact
```

Ví dụ:

```text
OwnershipFact {
    place: user.name,
    state: MOVED,
    span: ...
}
```

```text
CapabilityFact {
    id: Cap17,
    provenance: user,
    region: user.name,
    access: READ,
    start: ...
    end: ...
}
```

Sau đó MIR lowering dùng facts này.

---

# 35. CFG

Analyzer bắt buộc phải xây Control Flow Graph:

```text
        Entry
          │
          ▼
       condition
       /       \
      /         \
 branch A     branch B
      \         /
       \       /
         Join
          │
          ▼
         Exit
```

Mỗi basic block có:

```text
IN state
instructions
OUT state
```

Loops cần fixed-point:

```text
header
  ↑  │
  │  ▼
body
  └──┘
```

Không được dùng một pass tuyến tính đơn giản.

---

# 36. Analysis Order

Tôi đề xuất thứ tự chính thức:

```text
1. Build CFG
2. Build Place graph
3. Initialization analysis
4. Ownership / Move analysis
5. Capability creation
6. Region analysis
7. Capability liveness
8. Alias/conflict analysis
9. Escape analysis
10. Closure capture analysis
11. Async boundary analysis
12. Send/Share analysis
13. Drop analysis
14. Produce Ownership Facts
15. Lower to MIR
```

Một số bước có thể chạy song song hoặc iterate, nhưng semantic dependency nên giữ như trên.

---

# 37. Không runtime overhead

Toàn bộ:

```text
Ownership
Capability
Region
Move
Drop planning
Escape
Send
Share
```

đều là compile-time.

Sau Verified MIR:

```text
ownership metadata
capability metadata
region graph
```

có thể bị erase.

Không có:

```text
GC
runtime borrow checker
reference counting mặc định
fat object header
ownership runtime
```

---

# 38. Diagnostics

Nên chuẩn hóa từ đầu.

### Ownership

```text
AX_OWN_0001  use after move
AX_OWN_0002  use before initialization
AX_OWN_0003  value moved more than once
AX_OWN_0004  invalid partial move
AX_OWN_0005  use of dropped value
```

### Capability

```text
AX_VIEW_0001  conflicting mutable capability
AX_VIEW_0002  capability escapes owner
AX_VIEW_0003  capability crosses await
AX_VIEW_0004  storage may relocate while capability is live
AX_VIEW_0005  invalid capability provenance
```

### Drop

```text
AX_DROP_0001  invalid destruction state
AX_DROP_0002  resource may be dropped twice
AX_DROP_0003  dependent capability remains live
```

### Concurrency

```text
AX_SEND_0001   value is not Send
AX_SHARE_0001  value is not Share
AX_CONC_0001   conflicting concurrent access
```

---

# 39. Diagnostic phải giải thích “tại sao”

Không chỉ:

```text
error: use after move
```

Mà compiler nên có structured diagnostic:

```text
AX_OWN_0001: use after move

value `buffer` was moved here
    --> main.ax:12:18

    consume(buffer)
            ^^^^^^

value is used again here
    --> main.ax:15:11

    print(buffer)
          ^^^^^^

move reason:
    parameter `consume` takes ownership
```

Machine-readable JSON:

```json
{
  "code": "AX_OWN_0001",
  "severity": "error",
  "primary_span": "...",
  "related_spans": ["..."],
  "facts": {
    "place": "buffer",
    "move_kind": "ownership_transfer"
  }
}
```

Điều này rất tốt cho AI coding agent.

---

# 40. Invariants mới

### Ownership

```text
AOWN-30  Every owned value has a unique active ownership state.
AOWN-31  Moved values cannot be read.
AOWN-32  Moved values cannot be moved again.
AOWN-33  Dropped values cannot be used.
AOWN-34  Uninitialized values cannot be read.
AOWN-35  Reinitialization may restore ownership after move.
AOWN-36  Copy does not transfer ownership.
AOWN-37  Clone is explicit duplication.
AOWN-38  Partial move preserves ownership of unmoved fields.
AOWN-39  User-defined Drop forbids invalid partial move.
AOWN-40  Analysis is path-sensitive at control-flow joins.
```

### Capability

```text
ACAP-40  view<T> is read-only.
ACAP-41  mut_view<T> is exclusive write capability.
ACAP-42  READ+READ is permitted.
ACAP-43  READ+WRITE conflict is rejected.
ACAP-44  WRITE+WRITE conflict is rejected.
ACAP-45  Unknown overlap cannot be assumed disjoint.
ACAP-46  Capability validity depends on provenance.
ACAP-47  Capability cannot transfer ownership.
ACAP-48  Owner cannot invalidate a live capability.
ACAP-49  Relocation cannot invalidate a live capability.
ACAP-50  Persistent views require explicit capability construction.
```

### Drop

```text
ADROP-30  Drop is deterministic.
ADROP-31  Drop order is deterministic.
ADROP-32  Moved fields are not dropped.
ADROP-33  Uninitialized fields are not dropped.
ADROP-34  Early exit performs required cleanup.
ADROP-35  Drop does not propagate recoverable errors.
ADROP-36  Drop does not imply deallocation.
```

### Escape

```text
AESCAPE-20  Dangling capabilities are rejected.
AESCAPE-21  View return requires valid provenance.
AESCAPE-22  View cannot escape its owner lifetime.
AESCAPE-23  View cannot cross forbidden suspension boundaries.
AESCAPE-24  Closure capture is ownership-checked.
AESCAPE-25  Thread migration is Send-checked.
```

---

# 41. Một quyết định kiến trúc rất quan trọng

Tôi đề xuất **không gọi subsystem này là Borrow Checker** trong source tree.

Nên dùng:

```text
compiler/
├── ownership/
├── capability/
├── drop/
└── verifier/
```

Không:

```text
borrow_checker/
```

Vì về mặt thiết kế Axiom đang làm thứ rộng hơn:

```text
Ownership
+ Initialization
+ Capability
+ Region
+ Alias
+ Escape
+ Drop
+ Concurrency
```

và quan trọng nhất:

> **Không có borrow syntax trong ngôn ngữ.**

---

# 42. Cấu trúc implementation

```text
compiler/ownership/
├── state.ax
├── place.ax
├── init.ax
├── move.ax
├── dataflow.ax
├── join.ax
├── diagnostics.ax
└── tests/

compiler/capability/
├── capability.ax
├── provenance.ax
├── region.ax
├── conflict.ax
├── liveness.ax
├── escape.ax
├── alias.ax
├── diagnostics.ax
└── tests/

compiler/drop/
├── drop_plan.ax
├── order.ax
├── elaborate.ax
├── cleanup.ax
└── tests/
```

Nếu compiler còn viết bằng C/Rust ở bootstrap phase thì cấu trúc module vẫn giữ nguyên về mặt architecture.

---

# 43. Bộ test tối thiểu OWN-001

Phải có test trước khi làm MIR.

### Ownership

```text
ownership/copy_basic
ownership/move_basic
ownership/use_after_move
ownership/double_move
ownership/reinitialize_after_move
ownership/branch_maybe_move
ownership/branch_definite_move
ownership/uninitialized
```

### Partial move

```text
ownership/partial_move
ownership/partial_move_nested
ownership/partial_move_with_derived_drop
ownership/partial_move_user_drop_error
```

### Capability

```text
capability/read_read
capability/read_write_error
capability/write_write_error
capability/disjoint_fields
capability/unknown_overlap_error
capability/view_escape_error
capability/mut_view_move
```

### Drop

```text
drop/basic
drop/reverse_order
drop/early_return
drop/partial_move
drop/moved_field_not_dropped
drop/explicit_drop
```

### Async/concurrency

```text
async/view_across_await_error
async/owned_across_await
concurrency/send
concurrency/not_send
concurrency/share
```

---

# 44. Oracle phải kiểm tra analyzer

Đây là điểm tôi muốn giữ rất chặt.

Không chỉ:

```text
Source → Compiler → Binary
```

mà:

```text
Source
   │
   ├── Typed HIR
   │
   ├── Ownership Analyzer
   │       ↓
   │   Ownership Facts
   │
   ├── Oracle Semantic Model
   │
   └── Native execution
```

Ví dụ Oracle có thể biết:

```text
buffer:
    allocated
    owned
    moved
    dropped
```

và kiểm tra compiler:

```text
compiler MIR
      ==
oracle semantic events
```

Điều này giúp phát hiện những bug cực nguy hiểm như:

```text
compiler nghĩ đã move
runtime lại drop hai lần
```

---

# 45. Milestone chính thức

Tôi chốt:

```text
OWN-001
Basic ownership dataflow

OWN-002
Place + field ownership

OWN-003
Move/Copy/Clone

OWN-004
Partial move

OWN-005
Drop planning

CAP-001
view/mut_view capability

CAP-002
Region algebra

CAP-003
Conflict analysis

CAP-004
Capability liveness

CAP-005
Escape analysis

CONC-001
Send/Share checks

ASYNC-001
Await boundary checks

VERIFY-001
Ownership/capability verification
```

Sau khi `OWN-001 → VERIFY-001` hoàn thành, **không nên tiếp tục bổ sung thêm tính năng ngôn ngữ**.

Bước tiếp theo hợp lý là xây:

# **AXIOM MIR v0.1 + VERIFIED MIR CONTRACT**

Đây mới là “xương sống” của compiler.

Ta sẽ chốt chính xác:

```text
Typed HIR
    ↓
Ownership/Capability Facts
    ↓
MIR
    ↓
Verified MIR
    ↓
Optimization
```

và đặc biệt xác định **Place, SSA/value, memory, Drop, capability, branch, call, async, atomic, allocation** biểu diễn thế nào trong MIR mà **không làm mất semantic information trước khi verifier xác nhận**.