# XXXIX — OWN-001: Place Model + Ownership Dataflow

Đây là bước lõi của Axiom. Ta sẽ thiết kế ownership sao cho **compiler chịu phần khó**, còn programmer không phải viết lifetime/borrow annotation.

Mục tiêu của OWN-001:

```text
Typed HIR
   ↓
CFG
   ↓
Place Graph
   ↓
Initialization / Move Dataflow
   ↓
Ownership Facts
```

Chưa xử lý đầy đủ `view`, `mut_view`, concurrency hay async. Nhưng Place Model phải đủ mạnh để sau này không phải thiết kế lại.

---

## 1. Place là khái niệm trung tâm

Phải phân biệt:

```text
Value
Place
Capability
```

Ví dụ:

```axiom
var x = Vec2 { x: 1.0, y: 2.0 }
```

`x` là **Place** chứa một value.

Khi viết:

```axiom
x
```

trong value context → đọc value từ place.

Khi viết:

```axiom
x.x
```

→ place con của `x`.

Khi viết:

```axiom
x[0]
```

→ place được tạo qua indexing.

Khi viết:

```axiom
*p
```

→ dereferenced place.

---

# 2. Place representation

Chốt:

```text
Place {
    base: PlaceBase
    projections: Vec<Projection>
}
```

Base:

```text
Local(LocalId)
```

Projection:

```text
Field(FieldId)
Index(LocalId / ExprId)
Deref
```

Concept:

```text
x
```

→

```text
Place {
    base: Local(x)
    projections: []
}
```

`x.y`:

```text
Place {
    base: Local(x)
    projections: [
        Field(y)
    ]
}
```

`x.y.z`:

```text
Local(x)
 → Field(y)
 → Field(z)
```

---

# 3. Vì sao Place phải độc lập với HIR expression

Không nên để ownership analyzer tự phân tích AST expression mỗi lần.

Ví dụ:

```axiom
a.b.c = foo()[x].d
```

sau type checking cần semantic representation rõ ràng:

```text
LHS Place:
    Local(a)
      Field(b)
      Field(c)

RHS:
    Call foo()
      Index x
      Field d
```

Ownership analyzer chỉ cần biết:

```text
Place
Value
Move
Copy
Read
Write
```

không cần hiểu syntax.

---

# 4. Place categories

Mỗi expression có thể được phân loại:

```text
ValueExpr
PlaceExpr
```

Ví dụ:

```axiom
x
```

có thể là PlaceExpr nếu cần access.

```axiom
x + y
```

là ValueExpr.

```axiom
x.field
```

là PlaceExpr.

```axiom
foo()
```

là ValueExpr.

---

# 5. Place operations

Ownership phase cần normalize thành các semantic operations:

```text
READ(place)
WRITE(place)
MOVE(place)
COPY(place)
DROP(place)
```

Ví dụ:

```axiom
let y = x
```

nếu `x` không Copy:

```text
MOVE(x)
```

Nếu `x: i32`:

```text
COPY(x)
```

---

# 6. Ownership state

Per place:

```text
UNINIT
OWNED
PARTIAL
MOVED
DROPPED
```

Internal dataflow có thể thêm:

```text
MAYBE_INIT
MAYBE_MOVED
MAYBE_OWNED
```

nhưng những trạng thái này **không xuất hiện trong ngôn ngữ**.

---

# 7. State lattice

Có thể hình dung:

```text
             MAYBE_OWNED
              /       \
          OWNED       PARTIAL
             \         /
              ...
```

Nhưng implementation tốt hơn nên tách:

```text
InitializationState
OwnershipState
```

thay vì cố nhét tất cả vào một enum.

---

# 8. Đề xuất representation

```text
OwnershipState {
    init: InitState
    ownership: OwnershipState
}
```

Init:

```text
Uninitialized
Initialized
MaybeInitialized
```

Ownership:

```text
Owned
Moved
Dropped
MaybeOwned
```

Partial ownership được biểu diễn thêm bằng field tree:

```text
PlaceState {
    Whole: ...
    Fields: ...
}
```

Cách này quan trọng cho partial move.

---

# 9. Ví dụ cơ bản

```axiom
let x = Vec2 { x: 1.0, y: 2.0 }
let y = x
```

Sau declaration:

```text
x = OWNED
```

Sau:

```text
let y = x
```

nếu `Vec2` không Copy:

```text
x = MOVED
y = OWNED
```

Nếu tiếp:

```axiom
print(x)
```

→

```text
AX_OWN_0001
use of moved value
```

---

# 10. Copy

Primitive:

```text
i32
f64
bool
```

là Copy.

```axiom
let x = 42
let y = x
let z = x
```

không làm:

```text
x = MOVED
```

mà:

```text
COPY(x)
COPY(x)
```

x vẫn:

```text
OWNED
```

---

# 11. Move không phải physical copy

Đây là invariant rất quan trọng.

```axiom
let y = x
```

semantic:

```text
ownership(x) → MOVED
ownership(y) → OWNED
```

không có nghĩa machine code phải:

```text
memcpy(x, y)
```

Compiler có thể:

```text
register move
SSA rename
eliminate storage
```

Miễn observable semantics giống nhau.

---

# 12. Partial move

Ví dụ:

```axiom
struct User {
    name: Text
    age: i32
}
```

```axiom
let user = User { ... }
let name = user.name
```

Nếu `Text` !Copy:

```text
user.name → MOVED
user.age  → OWNED
```

Whole `user` trở thành:

```text
PARTIAL
```

Không được:

```axiom
print(user.name)
```

nhưng có thể:

```axiom
print(user.age)
```

---

# 13. Place tree

Đây là representation phù hợp:

```text
User
├── name : MOVED
└── age  : OWNED
```

Khi move whole object:

```text
User
├── name : MOVED
└── age  : MOVED
```

→:

```text
User = MOVED
```

---

# 14. Custom Drop

Axiom đã chốt:

> user-defined/custom Drop không cho partial move.

Ví dụ:

```axiom
struct File {
    handle: ...
}

impl Drop for File {
    ...
}
```

Nếu:

```axiom
let h = file.handle
```

→ compiler reject.

Lý do:

compiler không thể cho phép object tồn tại trong trạng thái partial rồi user-defined destructor chạy với invariant không rõ.

---

# 15. Compiler-derived Drop

Với compiler-generated Drop, partial move có thể được hỗ trợ.

Ví dụ:

```text
struct S {
    a: String
    b: String
}
```

Nếu compiler biết destructor chính xác:

```text
drop(a) if owned
drop(b) if owned
```

thì partial move an toàn.

---

# 16. Ownership transfer qua function

```axiom
fn consume(x: Text) {
}

fn main() {
    let s = ...
    consume(s)
}
```

Call semantic:

```text
MOVE(s)
CALL consume
```

sau call:

```text
s = MOVED
```

Không cần programmer viết:

```text
move s
```

vì parameter type `Text` đã biểu thị ownership transfer.

---

# 17. `view<T>` không Move

```axiom
fn print(x: view<Text>) {
}
```

call:

```axiom
print(s)
```

không chuyển ownership của `s`.

Semantic:

```text
CAPABILITY READ(s)
CALL print
```

Capability analysis xử lý chi tiết hơn.

Ownership state của `s` vẫn:

```text
OWNED
```

---

# 18. Receiver ownership

Với:

```axiom
fn consume(self: Text)
```

call:

```axiom
x.consume()
```

semantic receiver:

```text
MOVE(x)
```

Trong khi:

```axiom
fn length(self: view<Text>) -> usize
```

thì:

```text
READ/CAPABILITY(x)
```

Đây là lý do method syntax không cần class.

---

# 19. Assignment

```axiom
var x = Text(...)
var y = Text(...)

x = y
```

Nếu `Text` !Copy:

```text
DROP/replace old x
MOVE(y → x)
```

Compiler phải đảm bảo old `x` được cleanup trước khi overwritten.

Semantic sequence:

```text
DESTROY_OR_REPLACE(x)
MOVE(y, x)
```

MIR sau này sẽ biểu diễn chi tiết hơn.

---

# 20. Uninitialized variable

Axiom có:

```axiom
var x: Text
```

nếu language cho phép declaration không initializer trong semantic subset.

State:

```text
x = UNINIT
```

Sau:

```axiom
x = create_text()
```

→

```text
x = OWNED
```

Không được:

```axiom
print(x)
```

trước assignment.

---

# 21. Branch join

Ví dụ:

```axiom
var x: Text

if condition {
    x = make_text()
}
print(x)
```

Sau branch:

```text
condition=true:
    x = OWNED

condition=false:
    x = UNINIT
```

Join:

```text
x = MAYBE_INITIALIZED
```

→ compiler reject use.

Đây là lý do ownership phải là dataflow analysis.

---

# 22. Valid branch

```axiom
var x: Text

if condition {
    x = make_text()
} else {
    x = make_other_text()
}

print(x)
```

Cả hai path:

```text
OWNED
```

join:

```text
OWNED
```

→ valid.

---

# 23. Move trên branch

```axiom
let x = make_text()

if condition {
    consume(x)
}

print(x)
```

Path 1:

```text
x → MOVED
```

Path 2:

```text
x → OWNED
```

Join:

```text
MAYBE_MOVED
```

→ reject.

---

# 24. CFG

Ownership không chạy trực tiếp trên AST.

Ta cần CFG:

```text
CFG {
    blocks
    entry
    exits
}
```

Ví dụ:

```axiom
if cond {
    foo()
} else {
    bar()
}
```

CFG:

```text
       Entry
         |
       cond
      /    \
   then    else
      \    /
       Join
        |
      Exit
```

Mỗi block có:

```text
instructions
predecessors
successors
```

---

# 25. CFG builder

Đầu tiên không cần MIR.

Có thể tạo:

```text
HIR-CFG
```

hoặc trực tiếp CFG intermediate.

Nhưng tôi khuyến nghị:

```text
Typed HIR
   ↓
ControlFlowGraph
   ↓
Ownership Analyzer
```

sau đó:

```text
Ownership Facts
   ↓
MIR Lowering
```

Điều này giúp diagnostics ownership còn giữ được source expression rõ ràng.

---

# 26. Ownership event extraction

Từ Typed HIR:

```axiom
let y = x
```

tạo event:

```text
MOVE(x)
INIT(y)
```

Từ:

```axiom
foo(x)
```

nếu parameter `x: T`:

```text
MOVE(x)
```

Nếu parameter `view<T>`:

```text
READ_CAPABILITY(x)
```

Nếu `mut_view<T>`:

```text
WRITE_CAPABILITY(x)
```

Ownership analyzer không tự đoán dựa trên function name.

Nó dựa trên **typed signature**.

---

# 27. Event categories

```text
INIT(place)
READ(place)
COPY(place)
MOVE(place)
WRITE(place)
DROP(place)

CREATE_VIEW(place)
CREATE_MUT_VIEW(place)

RETURN(place)
CAPTURE(place)
AWAIT
SPAWN
```

Ở OWN-001 chỉ cần:

```text
INIT
READ
COPY
MOVE
WRITE
DROP
RETURN
```

---

# 28. Dataflow algorithm

Forward dataflow:

```text
EntryState
    ↓
process block
    ↓
ExitState
    ↓
successors
    ↓
join
    ↓
repeat until fixed point
```

Pseudo:

```text
worklist = [entry]

while worklist not empty:
    block = pop()

    in_state = join(predecessor.exit_states)

    out_state = transfer(block, in_state)

    if out_state changed:
        push successors
```

Loops cần fixed-point.

---

# 29. Join operation

Ví dụ:

```text
OWNED + OWNED = OWNED
```

```text
MOVED + MOVED = MOVED
```

```text
OWNED + MOVED = MAYBE_MOVED
```

```text
INIT + UNINIT = MAYBE_INIT
```

Nhưng diagnostics cần phân biệt:

```text
MAYBE_MOVED
```

với:

```text
MOVED
```

để message chính xác.

---

# 30. Definite ownership

Một operation yêu cầu ownership:

```text
MOVE(x)
DROP(x)
READ(x)
```

chỉ hợp lệ khi state chứng minh được:

```text
OWNED
```

hoặc Copy/read capability tương ứng.

Nếu:

```text
MAYBE_MOVED
```

→ compile error.

Không speculative.

---

# 31. Place conflict

Hai places:

```text
x.a
x.b
```

không nhất thiết conflict.

Region relation:

```text
DISJOINT
```

nếu fields khác nhau và compiler biết chúng độc lập.

Trong OWN-001 chỉ cần field-tree ownership.

Capability analyzer sau này sẽ tổng quát thành region algebra:

```text
SAME
DISJOINT
CONTAINS
CONTAINED_BY
OVERLAPS
UNKNOWN
```

---

# 32. Index projection

```axiom
a[i]
```

không thể luôn biết static field identity.

Place:

```text
Local(a)
  Index(i)
```

Nếu `i` runtime:

```text
region = UNKNOWN
```

Capability phase sẽ xử lý alias conflict thận trọng.

Ownership phase chủ yếu cần biết:

- đọc/move element
- write element
- container mutation interaction

---

# 33. Dereference

```axiom
*p
```

là:

```text
Deref
```

Nhưng raw pointer dereference thuộc unsafe.

Ownership analyzer không được giả định raw pointer an toàn chỉ vì có Place.

Unsafe boundary sẽ cung cấp trusted capability/provenance sau này.

---

# 34. Return

```axiom
fn foo() -> Text {
    let x = make_text()
    x
}
```

`x` được move ra caller:

```text
MOVE(x)
RETURN
```

Không drop `x` sau return.

Đây là invariant quan trọng cho Drop elaboration.

---

# 35. Early return

```axiom
fn foo() -> Text {
    let a = ...
    let b = ...

    if cond {
        return a
    }

    use(b)
}
```

Trên return path:

```text
MOVE(a)
DROP(b)
RETURN
```

Nếu `b` không moved.

Ownership analyzer phải tạo facts để Drop elaborator làm chính xác.

---

# 36. Loop

Ví dụ:

```axiom
var x = ...

while cond {
    use(x)
}
```

CFG có back-edge.

Dataflow phải converge.

Không được đơn giản hóa loop thành một lần phân tích.

---

# 37. Diagnostics

Chốt nhóm:

```text
AX_OWN_0001
use after move

AX_OWN_0002
use before initialization

AX_OWN_0003
double move

AX_OWN_0004
partial move

AX_OWN_0005
invalid use of partially moved value

AX_OWN_0006
drop of uninitialized value

AX_OWN_0007
drop of moved value

AX_OWN_0008
move from non-movable place
```

Sau này view/capability:

```text
AX_VIEW_0001...
```

không trộn vào ownership diagnostics.

---

# 38. Diagnostic quality

Ví dụ:

```axiom
let x = make_text()
consume(x)
print(x)
```

Không chỉ báo:

```text
use after move
```

Nên chỉ:

```text
error[AX_OWN_0001]: use of moved value `x`
  --> main.ax:3:11
   |
1  | let x = make_text()
   |     - value initialized here
2  | consume(x)
   |         - value moved here
3  | print(x)
   |       ^ value used here after move
```

Các span này được lấy từ Typed HIR/CFG event provenance.

---

# 39. Ownership Facts

Ownership analyzer không sửa Typed HIR.

Nó trả:

```text
OwnershipFacts {
    locals
    places
    events
    states
    moves
    drops
    returns
}
```

Ví dụ:

```text
Local x:
    init = block0:2
    move = block0:4
    state_after = MOVED
```

MIR lowering sử dụng facts này.

---

# 40. OWN-001 test suite

### Copy

```axiom
fn main() {
    let x = 42
    let y = x
    let z = x
}
```

→ valid.

---

### Move

```axiom
fn consume(x: Text) {}

fn main() {
    let x = make_text()
    consume(x)
    consume(x)
}
```

→ `AX_OWN_0003`.

---

### Branch

```axiom
var x: Text

if cond {
    x = make_text()
} else {
    x = make_text()
}

consume(x)
```

→ valid.

---

### Maybe move

```axiom
let x = make_text()

if cond {
    consume(x)
}

consume(x)
```

→ error.

---

### Partial move

```axiom
struct S {
    a: Text
    b: i32
}

let s = ...
let a = s.a
use(s.b)
```

→ valid nếu `S` compiler-derived Drop.

---

### Whole partial object

```axiom
use(s)
```

→ error.

---

### Custom Drop

```axiom
impl Drop for S {
    ...
}

let a = s.a
```

→ `AX_OWN_0004`.

---

# 41. Ownership invariants

```text
AOWN-23
Every owned value has a compiler-tracked ownership state.

AOWN-24
Move transitions ownership without requiring physical copying.

AOWN-25
Copy does not invalidate the source.

AOWN-26
Use after definite move is rejected.

AOWN-27
Use after possible move is rejected.

AOWN-28
Uninitialized values cannot be read, moved, or dropped.

AOWN-29
Double move is rejected.

AOWN-30
Drop requires a definitely initialized, non-moved value.

AOWN-31
Partial move is tracked per place projection.

AOWN-32
Compiler-derived Drop may support partial move.

AOWN-33
User-defined Drop forbids partial move.

AOWN-34
Moved fields are not dropped.

AOWN-35
Returned/moved values are not dropped by the source scope.

AOWN-36
Ownership joins are deterministic.

AOWN-37
Ownership analysis reaches a fixed point for loops.

AOWN-38
Ownership analysis is independent of optimization level.

AOWN-39
Ownership analysis is independent of physical storage placement.

AOWN-40
Ownership analysis does not require programmer lifetime annotations.

AOWN-41
Ownership analysis does not imply heap allocation.

AOWN-42
Ownership analysis does not generate machine code.

AOWN-43
Ownership facts preserve source provenance for diagnostics.
```

---

# 42. Điểm khác biệt quan trọng với Rust

Axiom không nói:

```text
"borrow checker, nhưng compiler tự viết"
```

Mô hình thực sự là:

```text
Ownership
+
Capability
+
Escape
+
Drop
+
Concurrency
```

là **các phân tích semantic riêng biệt**, cùng chia sẻ Place/CFG infrastructure.

Điều này quan trọng vì:

```text
Move
```

khác:

```text
Read capability
```

khác:

```text
Mutable capability
```

khác:

```text
Send
```

khác:

```text
Share
```

Không gom tất cả vào một “borrow checker khổng lồ”.

---

# 43. Sau OWN-001: Capability-001

Ngay sau ownership cơ bản, bước tiếp theo là:

```text
CAP-001
```

với hai loại:

```text
view<T>
mut_view<T>
```

Ta sẽ xây:

```text
Typed HIR
   ↓
Ownership Facts
   ↓
Capability Creation
   ↓
Provenance
   ↓
Region
   ↓
Liveness
   ↓
Conflict
   ↓
Escape
```

và chốt một vấn đề rất quan trọng:

> **Axiom cho phép compiler tự tạo capability tạm thời khi truyền owner vào `view<T>`/`mut_view<T>`, nhưng không cho phép việc đó âm thầm tạo ra một capability có thể escape.**

Ví dụ:

```axiom
fn print(x: view<Text>) {}

fn main() {
    let s = ...
    print(s)       // implicit ephemeral view: OK
}
```

nhưng:

```axiom
let v = s          // không tự động thành view
```

không được phép.

Muốn persistent capability:

```axiom
let v = view(s)
```

Sau đó compiler phải chứng minh:

```text
owner(s)
    │
    └── live capability v
```

và **không được phép**:

```text
drop(s)
move(s)
relocate(s)
```

trong khi `v` còn sống.

Đây sẽ là phần quyết định Axiom có đạt được mục tiêu **“pointer/reference bureaucracy thấp nhưng vẫn memory-safe và tối ưu mạnh”** hay không.

Bước kế tiếp là **CAP-001: Capability + Region + Liveness**, rồi ngay sau đó **DROP-001 → MIR-001**, để vertical slice `fn main() -> i32 { 42 }` có thể đi tới machine code.