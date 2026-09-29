Được. Từ đây tôi sẽ coi **“tự động tiếp tục” là quy tắc của phiên thiết kế Axiom**: hoàn thành một mảng thì tự chuyển sang mảng kế tiếp, không hỏi lại. Tôi sẽ chỉ dừng khi phần thiết kế đã đi đến điểm cần một quyết định nền tảng từ bạn hoặc chuỗi kiến trúc đã hoàn tất.

---

# Axiom Object Identity & Graph Model v0.1

Đây là bài test rất quan trọng.

Memory model hiện tại xử lý rất tốt:

```text
value
owner
view
mut_view
Box
Vec
Arena
Pool
```

Nhưng systems programming còn có:

```text
Tree
Graph
Linked List
Intrusive List
Self-referential object
Entity
ECS
AST
Scene Graph
```

Nếu thiết kế sai ở đây, chúng ta sẽ lại bị kéo về:

```text
&T
&mut T
lifetime
Pin<T>
GC
Rc cycle
```

Tôi muốn tránh điều đó.

---

# 1. Phải phân biệt Value Identity và Storage Identity

Đây là khái niệm mới cần đưa vào Axiom.

## Value

```axiom
let a = Vec2(10, 20)
```

`a` là value.

Nếu Copy:

```axiom
let b = a
```

thì:

```text
a ≠ b
```

theo identity.

Chúng chỉ có cùng giá trị.

---

## Storage identity

Ngược lại:

```axiom
let node = Box.new(Node(...))
```

object có một storage identity.

Ví dụ conceptual:

```text
Storage #42
    Node
```

Move:

```axiom
let x = node
```

không tạo object mới.

```text
x ───────→ Storage #42
```

Do đó:

> **Value identity và storage identity là hai thứ khác nhau.**

Đây là nền tảng để xây graph.

---

# 2. `Box<T>` là object identity primitive

`Box<T>` chính là abstraction đơn giản nhất cho:

> một object có ownership riêng và storage identity ổn định.

Ví dụ:

```axiom
struct Node {
    value: i32
}

let n = Box.new(Node(10))
```

Ta có:

```text
n
│
└── owns ──> Storage #1
                 │
                 └── Node
```

Không cần `Object` base class.

Không cần object header.

Không cần GC.

---

# 3. Tree

Tree có thể được viết:

```axiom
struct Node {
    value: i32
    left: Option<Box<Node>>
    right: Option<Box<Node>>
}
```

Đây là một trường hợp rất đẹp.

```text
             Box<Node>
                 │
                 ▼
                10
              /    \
             /      \
         Box<Node> Box<Node>
            5          20
```

Mỗi child có ownership rõ ràng.

Không cần reference.

Không cần lifetime.

---

# 4. Recursive type

Axiom cần rule:

```text
struct Node {
    next: Node
}
```

không có finite representation.

→ compile error.

Nhưng:

```axiom
struct Node {
    next: Option<Box<Node>>
}
```

hợp lệ.

Compiler nhìn thấy:

```text
Node
 └── Box<Node>
       └── Node
```

và recursion bị phá bởi indirection.

---

# 5. Linked List

Có thể viết:

```axiom
struct ListNode<T> {
    value: T
    next: Option<Box<ListNode<T>>>
}
```

Nhưng đây là singly-owned linked list.

Rất an toàn.

---

# 6. Doubly linked list

Đây mới là bài test.

Muốn:

```text
A ⇄ B ⇄ C
```

thì `A` sở hữu B và B lại cần trỏ về A.

Không thể:

```axiom
struct Node {
    next: Option<Box<Node>>
    prev: Option<Box<Node>>
}
```

vì tạo hai owner.

Và Axiom **không nên giải quyết bằng cách đưa borrow/lifetime syntax vào Core**.

---

# 7. Dùng stable handles thay vì references

Đây là hướng tôi khuyên dùng.

```axiom
struct Node {
    value: i32
    next: Option<NodeId>
    prev: Option<NodeId>
}
```

Storage:

```text
Pool<Node>
```

và:

```text
NodeId
```

là handle.

Ví dụ:

```text
Pool
┌─────┬─────┬─────┐
│ #12 │ #31 │ #57 │
│  A  │  B  │  C  │
└─────┴─────┴─────┘

A.next = #31
B.prev = #12
B.next = #57
C.prev = #31
```

Không có pointer graph trong safe code.

---

# 8. Đây là một pattern rất quan trọng cho Axiom

> **Ownership tạo storage. Handle tạo identity/reference.**

Ví dụ:

```text
Pool<Node>
    │
    ├── owns Node #12
    ├── owns Node #31
    └── owns Node #57

NodeId
    │
    ├── refers #12
    ├── refers #31
    └── refers #57
```

Đây là cách xử lý graph rất mạnh mà không cần GC.

---

# 9. Nhưng `NodeId` không được chỉ là `usize`

Không nên:

```axiom
type NodeId = usize
```

vì như vậy compiler không biết:

```text
NodeId
```

có phải index vào Pool hay không.

Nên là newtype:

```axiom
struct NodeId {
    index: u32
    generation: u32
}
```

Representation có thể tối ưu.

Semantic identity riêng.

---

# 10. Generation chống stale handle

Ví dụ:

```text
slot 5:
generation = 7
Node A
```

Release:

```text
slot 5:
generation = 8
free
```

Handle cũ:

```text
NodeId(5, 7)
```

không còn hợp lệ.

Handle mới:

```text
NodeId(5, 8)
```

không trùng.

Trong debug:

```text
old_handle → invalid
```

Trong safe API, việc truy cập phải được kiểm tra.

---

# 11. Có cần runtime generation check luôn không?

Không nhất thiết.

Đây là **library semantic**, không phải Core memory safety primitive.

Có thể có:

```text
Debug:
    generation checking

Release:
    optimized according to API contract
```

Nhưng nếu API hứa `get(id)` là safe và `id` có thể stale, release vẫn phải bảo toàn safety.

Có thể trả:

```axiom
Option<view<Node>>
```

và compiler có thể optimize check khi chứng minh được.

---

# 12. Pool API

Một thiết kế ban đầu:

```axiom
let pool = Pool<Node>.new()

let a = pool.insert(Node(...))
let b = pool.insert(Node(...))

pool.get(a)
pool.get_mut(a)

pool.remove(a)
```

`insert()`:

```text
Node → Pool ownership
       ↓
NodeId
```

Không trả ownership của Node.

---

# 13. Graph

Graph trở nên rất tự nhiên:

```axiom
struct Vertex {
    value: Data
    edges: Vec<VertexId>
}

let graph = Pool<Vertex>.new()
```

hoặc:

```axiom
struct Edge {
    from: VertexId
    to: VertexId
}
```

Storage:

```text
Vertices
    #1
    #2
    #3

Edges
    #10 → #1 → #2
    #11 → #2 → #3
```

Không cần:

```text
*mut Vertex
```

trong safe code.

---

# 14. Nhưng pointer vẫn phải tồn tại

Axiom là systems language.

Do đó:

```axiom
unsafe {
    let p: *mut Node = ...
}
```

vẫn được phép.

Raw pointer phù hợp với:

- intrusive list
- kernel
- OS structures
- C ABI
- device driver
- lock-free algorithms
- memory mapped structures.

Nhưng đó là **unsafe zone**.

---

# 15. Intrusive linked list

Ví dụ kernel-style:

```axiom
struct Node {
    value: i32
    next: *mut Node
    prev: *mut Node
}
```

Đây là hợp lệ trong `unsafe`.

Compiler không thể tự chứng minh toàn bộ invariant:

```text
next.prev == this
prev.next == this
```

Programmer chịu trách nhiệm.

---

# 16. Nhưng unsafe không nên tắt compiler

Đã chốt trước đó:

```text
unsafe ≠ disable compiler
```

Compiler vẫn kiểm tra:

- type
- ABI
- layout
- alignment khi có thể
- initialization
- syntax
- calling convention
- representation rules.

Unsafe chỉ nói:

> programmer chịu trách nhiệm cho các invariant ngoài khả năng chứng minh của compiler.

---

# 17. Self-referential object

Đây là trường hợp khó:

```axiom
struct SelfRef {
    value: i32
    ptr: *const i32
}
```

Nếu:

```axiom
let x = SelfRef(...)
```

và `ptr` trỏ vào `x.value`, sau đó `x` bị move:

```text
x → storage A

move x → storage B
```

pointer có thể dangling.

Axiom không nên cho safe code tạo tình huống này.

---

# 18. Stable storage giải quyết self-reference

Nếu object cần địa chỉ ổn định:

```axiom
let x = Box.new(SelfRef(...))
```

Nhưng vẫn còn vấn đề:

> làm thế nào khởi tạo pointer trỏ vào chính object?

Đây là nơi tôi **không muốn đưa `Pin<T>` vào Core**.

Thay vào đó, self-reference thật sự là **system-level unsafe pattern**.

Safe code nên ưu tiên:

```axiom
struct SelfRef {
    value: i32
    self_id: NodeId
}
```

hoặc handle.

---

# 19. Đây là một nguyên tắc quan trọng

> **Safe Axiom ưu tiên identity bằng handle hơn identity bằng address.**

Address identity là:

```text
unsafe/system
```

Handle identity là:

```text
safe/library
```

Điều này đặc biệt phù hợp với:

- game engine
- ECS
- GUI
- compiler
- database
- scene graph.

---

# 20. ECS

Axiom có thể hỗ trợ ECS rất tốt mà không cần language feature đặc biệt.

Ví dụ conceptual:

```text
Entity
 └── EntityId

Component storage
 ├── Position
 ├── Velocity
 ├── Health
 └── Transform
```

Mỗi component storage:

```text
Vec<Position>
Vec<Velocity>
Vec<Health>
```

hoặc sparse-set/pool.

`EntityId` là identity.

Không có object graph.

---

# 21. Đây cũng là lý do không cần class

Một class kiểu:

```text
class Entity
    position
    velocity
    health
```

không phải abstraction bắt buộc.

Axiom có thể biểu diễn:

```text
EntityId
+
Position
+
Velocity
+
Health
```

và behavior:

```axiom
fn update(entity: EntityId, world: mut_view<World>)
```

hoặc extension methods.

Đây là data-oriented design tự nhiên.

---

# 22. Object-oriented programming vẫn có thể tồn tại

Không có class không có nghĩa không có object-oriented style.

Ví dụ:

```axiom
struct Player {
    health: i32
}

fn damage(self: mut_view<Player>, amount: i32) {
    self.health -= amount
}
```

gọi:

```axiom
player.damage(10)
```

Method syntax vẫn có.

Nhưng:

```text
data
+
behavior
```

không cần một class object model.

---

# 23. Dynamic identity

Nếu cần heterogeneous objects:

```text
dyn Trait
```

đã có trong baseline.

Ví dụ:

```axiom
trait Drawable {
    fn draw(self: view<Self>)
}
```

Storage:

```text
Box<dyn Drawable>
```

có thể dùng.

Representation:

```text
data pointer
+
dispatch pointer
```

Không cần object header.

---

# 24. Graph + trait

Có thể:

```axiom
struct Node {
    id: NodeId
    kind: NodeKind
}
```

hoặc:

```axiom
Pool<Box<dyn Node>>
```

tùy nhu cầu.

Static dispatch vẫn được ưu tiên.

---

# 25. Circular ownership

Axiom cần một rule cực rõ:

### Safe ownership graph

Ownership graph phải có chủ sở hữu rõ ràng.

Ví dụ:

```text
Box<A>
 └── Box<B>
      └── Box<C>
```

OK.

### Cyclic ownership

```text
A owns B
B owns A
```

không được biểu diễn bằng owning types trực tiếp.

Dùng:

```text
handles
Arc/Weak
Pool IDs
```

tùy semantics.

---

# 26. `Weak`

Khi có:

```axiom
Arc<Node>
```

và graph có cycle:

```text
A → B → A
```

có thể cần:

```axiom
Weak<Node>
```

để phá ownership cycle.

Nhưng `Weak` là library abstraction.

Không phải memory primitive.

---

# 27. Axiom không cần GC để xử lý graph

Đây là một kết quả quan trọng.

Có ba lựa chọn:

```text
Tree:
    Box ownership

Graph:
    Pool + Handle

Shared graph:
    Arc + Weak

Systems graph:
    raw pointers unsafe
```

Không cần tracing GC.

---

# 28. `Handle<T>` có nên là Core?

Tôi nghiêng về:

**Không.**

`Handle<T>` là một family của library abstractions.

Core chỉ cần:

```text
ownership
storage identity
provenance
capability
```

Pool có thể tự định nghĩa:

```axiom
struct NodeId ...
```

hoặc:

```axiom
PoolHandle<T>
```

Compiler không cần hiểu NodeId.

---

# 29. Nhưng compiler cần hiểu storage identity

Đây là distinction:

```text
Compiler knows:
    storage identity

Compiler does NOT need to know:
    NodeId
    EntityId
    AssetId
    TextureHandle
    FileId
```

Những cái sau là application-level concepts.

---

# 30. Object identity model hoàn chỉnh

Tôi đề xuất chốt:

```text
                 IDENTITY
                    │
         ┌──────────┴──────────┐
         │                     │
      VALUE                 STORAGE
         │                     │
    Copy / Move          stable allocation
                               │
                      ┌────────┼────────┐
                      │        │        │
                     Box     Arena     Pool
                                         │
                                       Handle
```

Raw pointer:

```text
unsafe address identity
```

---

# 31. Invariants

Thêm:

**AID-01 — Value Identity**  
Copyable values have independent value identity.

**AID-02 — Storage Identity**  
Owning dynamic storage may have stable storage identity.

**AID-03 — Ownership Acyclicity**  
Safe direct ownership cannot form an unbounded ownership cycle.

**AID-04 — Recursive Indirection**  
Recursive types require finite representation through indirection.

**AID-05 — Handle Identity**  
Library handles may represent stable logical identity without exposing addresses.

**AID-06 — Handle Safety**  
Safe handle APIs cannot produce use-after-release.

**AID-07 — Generation Safety**  
Reused storage slots must not make stale handles valid accidentally.

**AID-08 — Raw Pointer Isolation**  
Address-based object identity is unsafe/system-level.

**AID-09 — Stable Storage Contract**  
Objects requiring stable address must use storage with an explicit stability guarantee.

**AID-10 — No Pin Primitive**  
Core does not require a general programmer-facing pin/lifetime system.

**AID-11 — Graph Without GC**  
Safe graphs can be represented using handles, ownership containers, or explicit shared ownership.

**AID-12 — Identity Abstraction Erasure**  
Handle abstractions may compile to integers, indices, pointers, or other representations when semantics permit.

---

# Và từ đây xuất hiện một insight khá lớn

Axiom đang có **hai cách xây cấu trúc dữ liệu**:

### Ownership-oriented

```text
Box
Arena
Vec
```

Phù hợp:

```text
tree
hierarchy
nested data
RAII resources
```

### Identity-oriented

```text
Pool
Handle
EntityId
```

Phù hợp:

```text
graph
ECS
scene
compiler IR
UI tree with cross-links
database indexes
```

Đây là điều tôi cho rằng rất tốt: **không cố bắt mọi cấu trúc dữ liệu phải trở thành một bài toán ownership/reference giống nhau.**

---

# Tự động chuyển task kế tiếp: Error/Resource/RAII model

Phần memory đã khá hoàn chỉnh. Task kế tiếp cần chốt là **Resource Management + RAII + Error Handling + Cancellation**, vì đây là nơi `Drop`, `close()`, `Result`, `panic`, async và OS resources giao nhau.

## 1. Quy tắc cốt lõi

Axiom nên phân biệt tuyệt đối:

```text
Drop
    = guaranteed cleanup

close()
    = fallible business/resource operation
```

Ví dụ:

```axiom
let file = File.open(path)?

file.write(data)?
file.close()?
```

Nếu programmer quên `close()`:

```text
scope exit
    ↓
Drop(file)
```

vẫn giải phóng resource.

---

## 2. Drop không được là error channel

Không:

```axiom
fn Drop.drop(self) -> Result
```

vì sẽ tạo:

```text
cleanup
  ↓
error
  ↓
cleanup of error
  ↓
another error
```

rất phức tạp.

`Drop` phải:

```text
deterministic
non-recoverable
non-fallible
```

---

## 3. Resource có hai phase

Ví dụ file:

```text
OPEN
  │
  ├── read/write
  │
  ├── close() → CLOSED
  │
  └── scope exit → Drop
```

`close()` có thể fail.

`Drop` thì không.

---

## 4. `close()` thành công rồi Drop không được double-close

Compiler/library resource state phải đảm bảo:

```text
OPEN → close() → CLOSED
```

sau đó:

```text
Drop
```

không thực hiện OS close lần nữa.

Có thể dùng:

```text
resource state
```

ở compiler/library implementation.

Không cần programmer gọi:

```text
release_borrow()
```

hay:

```text
destroy()
```

---

## 5. `?` là cơ chế chính

Ví dụ:

```axiom
fn read_config(path: Text) -> Result<Config, Error> {
    let f = File.open(path)?
    let data = f.read_all()?
    return Config.parse(data)?
}
```

Khi `?` return error:

```text
Config.parse
    ↓ error
cleanup
    ↓
data
    ↓
f
    ↓
return error
```

Compiler tự lower cleanup.

---

## 6. Điều này phải hoạt động với mọi control flow

```axiom
if condition {
    return error
}
```

hoặc:

```axiom
while condition {
    if stop {
        break
    }
}
```

hoặc:

```axiom
match result {
    Ok(x) => ...
    Err(e) => return e
}
```

Drop vẫn deterministic.

---

## 7. Panic

Axiom giữ:

```text
panic = exceptional terminal/control-flow event
```

nhưng **không có general exception system**.

Hai profile:

```text
--panic=abort
--panic=unwind
```

`abort`:

```text
panic
 ↓
cleanup policy
 ↓
terminate
```

`unwind`:

```text
panic
 ↓
unwind frames
 ↓
Drop
 ↓
terminate/catch boundary if supported
```

Tôi không khuyến nghị `try/catch` trong Core v0.1.

---

## 8. Cancellation

Đây là phần quan trọng với async.

Cancellation không nên là:

```text
forced destructor
```

mà:

```text
cooperative cancellation
```

Task có thể thấy:

```axiom
if cancel.is_requested() {
    return Err(Cancelled)
}
```

hoặc executor inject cancellation point.

---

## 9. Resource Drop khi async task bị cancel

State machine:

```text
async function
       ↓
state object
       ↓
local resources
```

Nếu task bị hủy:

```text
task cancellation
      ↓
drop state
      ↓
drop owned resources
```

Nhưng không được tự ý chạy arbitrary user code ở một thread khác trong trạng thái không an toàn.

Cancellation semantics cần được library/executor kiểm soát.

---

## 10. `defer` chưa cần

Tôi tiếp tục giữ quyết định:

> Không có `defer` trong Core v0.1.

Vì `Drop + block scope + Result` đã giải quyết phần lớn cleanup.

Nếu sau này có use case cho cleanup không gắn với ownership:

```text
defer
```

có thể là syntax sugar compile-time.

Không cần quyết định ngay.

---

# 11. Resource abstraction tổng thể

Axiom lúc này có mô hình:

```text
              RESOURCE
                  │
        ┌─────────┴─────────┐
        │                   │
    guaranteed          fallible
    cleanup             operation
        │                   │
       Drop              close()
        │                   │
    no Result             Result
```

Đây là một boundary tôi muốn **đóng băng**.

---

## 12. Invariants mới

**ARES-01 — Deterministic Cleanup**  
Owned resources are cleaned deterministically.

**ARES-02 — Drop Is Cleanup**  
Drop represents guaranteed cleanup, not business logic.

**ARES-03 — Drop Is Non-Fallible**  
Drop cannot propagate recoverable errors.

**ARES-04 — Explicit Fallible Close**  
Fallible shutdown is represented by an explicit operation.

**ARES-05 — No Double Release**  
Successful explicit release prevents duplicate resource destruction.

**ARES-06 — Cleanup on Structured Exit**  
Return/break/continue/error propagation execute required cleanup.

**ARES-07 — Cleanup on Panic**  
Configured panic semantics preserve required cleanup.

**ARES-08 — Cancellation Safety**  
Cancelled async state releases owned resources correctly.

**ARES-09 — No Mandatory Exception Runtime**  
Error handling does not require a general exception runtime.

**ARES-10 — Error Propagation Erasure**  
`?` is compile-time/control-flow sugar and can disappear completely in optimized machine code.

---

## Điểm dừng logic tiếp theo

Memory + identity + resource management đã nối thành:

```text
Value
  ↓
Ownership
  ↓
Storage
  ↓
Capability
  ↓
Identity
  ↓
Resource lifetime
  ↓
Error cleanup
```

Task kế tiếp tôi sẽ tự chuyển sang **Concurrency sâu hơn: Thread + Channel + Atomics + Lock-free + Send/Share + async state machine**, đặc biệt giải quyết câu hỏi rất quan trọng của Axiom:

> **Làm thế nào có concurrency mạnh mà không cần GC, không cần runtime bắt buộc, không bắt programmer viết lifetime/borrow, nhưng vẫn bảo đảm data-race safety và cho phép code lock-free hiệu năng cao?**