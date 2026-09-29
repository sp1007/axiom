# BOOTSTRAP-138 — Escape Analysis, Allocation Promotion & Storage Optimization

**Trạng thái: FROZEN / COMPLETED**

Đây là task đặc biệt quan trọng đối với mục tiêu của Axiom:

> **Programmer không phải quyết định stack/heap/register. Compiler quyết định storage tối ưu nhất dựa trên semantic lifetime, escape và observable address.**

Điều này giúp Axiom tránh một lỗi thiết kế phổ biến: đồng nhất **“owned value” = “heap allocation”**.

---

## 1. Nguyên tắc nền tảng

Axiom tách:

```text
Ownership
    ≠
Storage
```

Một:

```ax id="qj6m5h"
Box<T>
```

mang semantic ownership của dynamic storage, nhưng compiler vẫn có thể eliminate/promote allocation nếu **không có observable semantic requirement buộc storage phải tồn tại độc lập**.

---

# 2. Escape Analysis trả lời gì?

Compiler cần biết:

```text
Value này có thể thoát khỏi phạm vi hiện tại không?
```

Và cụ thể hơn:

```text id="3cgj9u"
NoEscape
ArgumentEscape
ReturnEscape
HeapEscape
ThreadEscape
ExternalEscape
UnknownEscape
```

---

# 3. Escape không phải lifetime

Ví dụ:

```ax id="4x1m7c"
let x = make();
use(x);
```

`x` có lifetime trong scope nhưng:

```text id="4t7xg2"
Escape = NoEscape
```

Compiler có thể rút ngắn physical storage lifetime xuống đúng vùng cần thiết.

---

# 4. Escape state

Frozen:

```text id="q7a5f2"
NoEscape
ArgumentEscape
ReturnEscape
HeapEscape
ThreadEscape
ExternalEscape
UnknownEscape
```

Có thể biểu diễn thêm provenance của escape.

---

# 5. `NoEscape`

Ví dụ:

```ax id="f4ub0k"
fn distance(a: Point, b: Point) -> f32
```

Nếu tất cả dữ liệu chỉ được sử dụng trong function:

```text id="7v9k8c"
NoEscape
```

Compiler có thể:

- register;
- stack;
- SSA;
- scalarize.

---

# 6. Argument escape

```ax id="v0m0sq"
fn consume(x: T)
```

Nếu callee không giữ `x`:

```text id="2s0z8h"
ArgumentEscape
```

không nhất thiết có nghĩa heap allocation.

Nó chỉ nói:

> Giá trị được truyền qua function boundary.

---

# 7. Return escape

```ax id="j5wq7e"
fn make() -> T
```

return value có:

```text id="s6v9cd"
ReturnEscape
```

nhưng physical implementation có thể là:

```text id="x5k1fa"
register return
sret
caller allocation
move
```

---

# 8. Heap escape

Nếu:

```ax id="jjx7do"
store_global(x)
```

thì `x` có thể:

```text id="5v0jtt"
HeapEscape / ExternalEscape
```

tùy abstraction.

Compiler không được stack-promote nếu điều đó làm thay đổi observable semantics.

---

# 9. Thread escape

Ví dụ:

```ax id="5z8trm"
spawn(move || use(x));
```

`x`:

```text id="m4x9t7"
ThreadEscape
```

và phải thỏa:

```text id="uh1qtx"
Send
```

nếu execution domain yêu cầu.

---

# 10. External escape

Ví dụ:

```ax id="b8n2vq"
extern_use(address_of(x));
```

nếu foreign code có thể giữ address:

```text id="m2s7v5"
ExternalEscape
```

Physical storage không được tự động biến mất khi caller scope kết thúc.

---

# 11. Unknown escape

Nếu compiler không biết:

```ax id="jz1z8f"
unknown_call(x)
```

thì:

```text id="m4z2cj"
UnknownEscape
```

và dùng conservative assumption.

---

# 12. Escape lattice

Không nên biến escape thành một boolean.

Compiler cần partial order về mức độ quan sát/khả năng thoát:

```text id="8q1s7n"
NoEscape
    ↓
ArgumentEscape
    ↓
ReturnEscape
    ↓
External/Thread/Heap
    ↓
UnknownEscape
```

Nhưng đây cũng không phải total order tuyệt đối; một giá trị có thể đồng thời có nhiều escape edges.

Do đó implementation nên dùng **EscapeSet + reachability facts**.

---

# 13. Escape graph

Ví dụ:

```text id="fl5h1p"
x
 ↓
closure
 ↓
spawn
 ↓
task
```

Compiler tạo:

```text id="a4n5kd"
x → closure → task → ThreadEscape
```

---

# 14. Allocation graph

Một allocation:

```ax id="d6q3f1"
let x = Box::new(Point{...});
```

có:

```text id="i8j4xa"
Allocation A
    owner = x
```

Nếu:

```text id="a2g0ez"
A → NoEscape
```

allocation có khả năng được eliminate/promote.

---

# 15. Stack promotion

Ví dụ:

```ax id="r8k7g1"
fn foo() -> i32 {
    let x = Box::new(42);
    *x
}
```

Semantically có owned dynamic object.

Nhưng nếu address không escape:

```text id="b3x0q9"
Box allocation
    ↓
Stack/SSA promotion
```

có thể loại bỏ heap allocation hoàn toàn.

---

# 16. Scalar replacement

Nếu:

```ax id="7i1x8e"
Box<Point>
```

với:

```text id="g4h5p2"
Point.x
Point.y
```

được truy cập độc lập và address không observable:

```text id="3k7m9d"
Box<Point>
    ↓
x SSA
y SSA
```

---

# 17. Allocation elimination

Nếu object:

```text id="h0n3q7"
never escapes
never address-observed
identity unobservable
```

thì:

```text id="f9u3m2"
ALLOC
DROP
```

có thể hoàn toàn biến mất.

---

# 18. Observable allocation identity

Không được eliminate nếu chương trình quan sát identity.

Ví dụ abstraction:

```ax id="y7m2pk"
same_storage(a, b)
```

hoặc stable handle semantics.

Nếu identity observable:

```text id="c3x9r1"
allocation identity = semantic
```

→ allocation phải được preserve hoặc thay bằng storage có semantics tương đương.

---

# 19. Address observability

`address_of(x)` là unsafe/system.

Nếu address:

```text id="2x8d1j"
never escapes
```

compiler có thể vẫn optimize storage.

Nếu address:

```text id="r9m4x2"
stored externally
```

thì stable address trở thành semantic requirement.

---

# 20. Stable address

Axiom không mặc định:

```text id="w7c1m4"
Box<T> = permanently stable physical address
```

Stable address phải là explicit contract.

Ví dụ abstraction:

```text id="4m8y1n"
StableBox<T>
```

có semantics khác `Box<T>`.

---

# 21. Relocation

Nếu:

```text id="2k7r9v"
Vec<T>
```

có active view:

```text id="8m4p1q"
view(vec)
```

thì operation có khả năng reallocate phải bị verifier chặn hoặc contract phải bảo đảm không relocation.

Escape analysis không được override capability validity.

---

# 22. Escape ≠ capability lifetime

Một value có:

```text id="q4r6n0"
NoEscape
```

nhưng có active view.

Ví dụ:

```ax id="x2m9c4"
let x = make();
let v = view(x);
use(v);
```

Compiler phải xét:

```text id="1k5v8s"
Capability lifetime
```

trước khi physical storage được kết thúc.

---

# 23. Ownership + Escape

Ownership verifier nói:

```text id="m5y2v9"
x owns A
```

Escape analysis nói:

```text id="a9q6k1"
A does not escape
```

Storage optimizer có thể quyết định:

```text id="k7r3p0"
A → stack
```

hoặc:

```text id="v2m8q4"
A → register/SSA
```

---

# 24. Capability + Escape

Nếu:

```text id="c8v2r1"
view(A)
```

escape qua return:

```ax id="m4s7z0"
return view(A)
```

thì:

```text id="j1q9p5"
A must outlive returned capability
```

Nếu A là local temporary không thể outlive caller:

```text id="z6h2n8"
compile error
```

---

# 25. Return view

Ví dụ hợp lệ:

```ax id="f0k4m6"
fn first(x: view<Vec<T>>) -> view<T>
```

returned capability phải preserve provenance:

```text id="d5x8p2"
returned view
    ↓
input provenance
```

Compiler không được biến nó thành view của temporary khác.

---

# 26. Caller allocation

Return:

```ax id="c9m1v7"
LargeStruct
```

không nhất thiết cần callee allocate.

ABI lowering có thể:

```text id="g6q3w8"
caller allocates result storage
callee initializes it
```

Escape analysis hỗ trợ quyết định điều này.

---

# 27. Return Value Optimization

Axiom không cần source-level RVO rule.

Semantic:

```text id="r2h7p4"
return value
```

Compiler tự chọn:

```text id="v8x3k1"
register
sret
caller storage
move
```

Miễn observable semantics giữ nguyên.

---

# 28. Move không đồng nghĩa physical copy

Ví dụ:

```ax id="j4q8s1"
let b = make();
let c = b;
```

nếu `b` move:

```text id="a7n5m2"
ownership(b) → ownership(c)
```

không bắt buộc:

```text id="p6w2r9"
memcpy
```

Escape analysis + ABI có thể thực hiện zero-copy transfer.

---

# 29. Closure environment

Closure:

```ax id="f3k7n1"
let f = || use(x);
```

nếu:

```text id="z5q2m8"
f NoEscape
```

environment có thể:

```text id="c8r4v0"
inline
stack
SSA
```

Nếu:

```text id="n2h6y7"
f ThreadEscape
```

environment phải tồn tại đủ lâu và thỏa Send.

---

# 30. Closure heap allocation không bắt buộc

Đây là điểm quan trọng:

```text id="0p7m4s"
closure
≠
heap object
```

Capturing closure chỉ là semantic aggregate:

```text id="e6k1q3"
Code + Environment
```

Physical storage do compiler quyết định.

---

# 31. Async Future

Future:

```ax id="v5n8k2"
async fn foo()
```

chỉ cần lưu những locals live across suspension.

Escape analysis có thể xác định:

```text id="s1m6q9"
Future never escapes
```

→ state machine có thể stack/register allocate.

---

# 32. Future escapes

Nếu:

```ax id="y3k8p0"
spawn(foo())
```

Future:

```text id="a5q7r2"
ThreadEscape
```

có thể cần runtime-managed storage.

Nhưng vẫn không có nghĩa bắt buộc heap:

```text id="d9m4x6"
executor-owned arena
stackful task
inline task storage
```

đều có thể là implementation.

---

# 33. Async state minimization

Escape + liveness:

```text id="j7q2n5"
local A
local B
local C
```

Nếu chỉ B sống qua await:

```text id="v4m9x1"
Future state:
    B
```

A/C được loại khỏi state machine.

---

# 34. Thread creation

```ax id="s8x3k2"
spawn(move || work(x))
```

Nếu `x` move vào task:

```text id="q1m7v5"
ownership transfer
```

Escape analysis không được biến thành shared alias.

---

# 35. Arc

```ax id="h2p6r8"
Arc<T>
```

đã có shared ownership semantics.

Escape analysis không được “tối ưu hóa” Arc thành unique ownership nếu semantic observable reference-counting behavior có thể được quan sát.

Nếu refcount hoàn toàn unobservable:

```text id="m8q3v1"
implementation may optimize internals
```

nhưng vẫn phải bảo toàn Arc's semantic contract.

---

# 36. Rc/Arc cycle

Escape analysis không phải garbage collector.

Nếu:

```text id="k4x9p2"
Rc A → B
Rc B → A
```

cycle semantics thuộc shared ownership abstraction.

Compiler không tự reclaim.

---

# 37. Global/static

Storage:

```text id="p3v7n1"
STATIC
TLS
```

không phải ordinary local escape.

Nếu local value được lưu vào static:

```text id="m6q2x8"
External/GlobalEscape
```

storage phải có program lifetime semantics.

---

# 38. Thread-local

TLS:

```text id="r9k4c6"
per-thread storage
```

escape không có nghĩa global sharing.

Compiler cần giữ:

```text id="b2n8q5"
ThreadStorageIdentity
```

riêng.

---

# 39. Arena allocation

Arena:

```ax id="a7f3m9"
let arena = Arena::new();
let x = arena.alloc(T);
```

`x` phụ thuộc lifetime của arena.

Escape analysis phải xây:

```text id="v1q8k4"
x → arena
```

Nếu `x` escape khỏi arena lifetime:

```text id="s5m2r7"
reject
```

---

# 40. Pool/slab

Pool có thể reuse physical storage.

Do đó:

```text id="j3n7x0"
storage address
```

có thể thay đổi identity theo allocation epoch.

Compiler không được giả định stable address nếu abstraction không cung cấp.

---

# 41. Generation handles

Nếu application dùng:

```text id="c4p8m2"
EntityId(index, generation)
```

đây là logical identity.

Escape analysis không được nhầm:

```text id="k9r1v6"
Handle
```

với:

```text id="q7m3x5"
Storage capability
```

---

# 42. Escape + alias

Nếu value escape:

```text id="z8n4q1"
x → external
```

alias assumptions phải giảm.

Ví dụ:

```text id="w2m7c9"
NO_ALIAS(x, y)
```

có thể không còn valid sau external call nếu foreign code có thể obtain x.

---

# 43. Escape + Effect

Nếu function:

```text id="u5q8r3"
FOREIGN + WRITE_EXTERNAL
```

escape analysis phải conservative.

Nếu function:

```text id="f1n6m4"
PURE
```

thì không thể tự nhiên làm local object escape qua hidden side effect.

Đây là lợi ích của Effect System.

---

# 44. Escape + Alias + Effect

Ba subsystem tạo thành:

```text id="s7k2p9"
Ownership
    ↓
Capability
    ↓
Alias ←→ Effect
    ↓
Escape
    ↓
Storage Optimization
```

Escape refinement dựa trên alias/effect information.

---

# 45. Allocation promotion

Compiler có thể promote:

```text id="x4m8q2"
Heap
 ↓
Arena
 ↓
Stack
 ↓
Register
 ↓
SSA
```

nhưng chỉ nếu semantic contract vẫn đúng.

---

# 46. Không phải mọi allocation đều có thể promote

Không promote nếu:

```text id="p9r3k7"
stable address required
external escape
thread escape requiring independent storage
observable allocation identity
foreign ownership
device storage
OS resource
```

---

# 47. Device allocation

```ax id="m6q1v8"
DeviceBuffer<T>
```

không được stack-promote thành CPU memory.

Storage domain là semantic.

```text id="j2x7n5"
CPU storage != Device storage
```

---

# 48. External resource

Ví dụ file handle:

```ax id="g8r4p2"
File
```

không phải ordinary memory allocation.

Drop semantics có thể:

```text id="k3m9x1"
close OS resource
```

Do đó storage optimization phải tôn trọng Effect/Drop.

---

# 49. Storage classes

Compiler internal:

```text id="w5n2q7"
REGISTER
STACK
INLINE
STATIC
TLS
HEAP
ARENA
POOL
DEVICE
EXTERNAL
```

Không phải tất cả đều source-visible.

---

# 50. Storage decision

Compiler có thể thực hiện:

```text id="a8q3m6"
Semantic object
      ↓
Escape
      ↓
Address observability
      ↓
Capability constraints
      ↓
Identity constraints
      ↓
Effect/Drop constraints
      ↓
Storage selection
```

---

# 51. Address stability

Một object chỉ cần stable address khi semantics thực sự yêu cầu.

Ví dụ:

```text id="m7x1p4"
address exposed
address stored
FFI retains pointer
self-referential storage contract
OS/device API requires stable mapping
```

---

# 52. Self-referential objects

Nếu abstraction cho phép:

```text id="q5r8n2"
object contains pointer to itself
```

compiler phải thấy stable-address requirement.

Core không cần `Pin<T>` syntax.

Thay vào đó:

```text id="u3k7m9"
storage contract = StableAddress
```

là semantic property của abstraction.

---

# 53. Relocation barrier

Nếu object có:

```text id="c6p2x8"
StableAddress
```

optimizer không được:

```text id="v9m4q1"
move
compact
reallocate
scalarize
```

theo cách thay đổi address semantics.

---

# 54. Allocation lifetime shortening

Nếu object không escape:

```text id="r2x6m8"
semantic lifetime:
    [entry, exit]

physical lifetime:
    [first_use, last_use]
```

Compiler có thể rút ngắn physical lifetime.

Điều này hỗ trợ register reuse và stack slot reuse.

---

# 55. Stack slot reuse

Hai objects:

```text id="h7q3m1"
A lifetime [1,5]
B lifetime [6,10]
```

có thể dùng cùng stack slot.

Không có alias vì lifetime không overlap.

---

# 56. Register reuse

Tương tự:

```text id="w4n8p2"
SSA value A dead
SSA value B born
```

có thể dùng cùng physical register.

Ownership semantics không thay đổi.

---

# 57. Memory fragmentation

Escape analysis không trực tiếp “giải quyết fragmentation”.

Fragmentation phụ thuộc allocator/lifetime pattern.

Nhưng Axiom cho phép:

```text id="j6m2q9"
arena
pool
stack promotion
allocation elimination
```

nên có nhiều công cụ giảm fragmentation mà không ép một memory model duy nhất.

---

# 58. Flat address space

Axiom vẫn có:

```text id="b9x4m7"
flat virtual address model
```

ở machine/native level.

Nhưng:

```text id="r3k8q1"
flat address space
≠
one universal allocator
```

Escape/storage optimization vẫn quyết định cách memory được sử dụng.

---

# 59. Interprocedural escape

Compiler truyền escape summary qua function boundaries:

```text id="s8m2v5"
FunctionSummary {
    parameter_escape[]
    return_provenance
    captured_escape
    global_escape
    thread_escape
    external_escape
}
```

---

# 60. Call graph SCC

Recursion:

```text id="k4q9n1"
foo → bar
↑     ↓
└─────┘
```

phải xử lý theo strongly connected components.

Mỗi SCC chạy fixed-point escape analysis.

---

# 61. Generic escape

Generic:

```ax id="d5m8r2"
fn process<T>(x: T)
```

escape của `x` phụ thuộc:

- body;
- trait methods;
- closure;
- specialization;
- dynamic dispatch.

Compiler giữ summary theo generic instance khi cần.

---

# 62. Effect-driven escape refinement

Nếu callee:

```text id="q1x7m4"
PURE
```

thì nó không thể lưu `x` vào global/external state.

Nếu:

```text id="n6r3p8"
WRITE_EXTERNAL
```

thì có thể.

Đây là một refinement rất mạnh.

---

# 63. FFI escape

Không contract:

```text id="u9k5m2"
extern foo(x)
```

→ conservative.

Contract:

```text id="w4p7q1"
does_not_retain_pointer
```

có thể cho phép storage optimization.

Nhưng contract phải được kiểm chứng/được trust boundary định nghĩa rõ ràng.

---

# 64. Compiler cannot optimize against unknown behavior

Nếu:

```text id="m3x8r6"
UnknownEscape
```

compiler không được tự suy:

```text id="v7q2n9"
Stack
```

chỉ vì “có vẻ không cần heap”.

---

# 65. Escape diagnostics

Ví dụ:

```ax id="h2m6q8"
fn foo() -> view<i32> {
    let x = make();
    return view(x);
}
```

diagnostic:

```text id="q9r3v1"
E_CAPABILITY_LIFETIME

returned view may outlive its owner

owner:
    local x

capability:
    view(x)

required:
    returned capability provenance must outlive caller
```

Không cần `'a` lifetime syntax.

---

# 66. Explain storage decision

CLI:

```text id="a7m4q9"
axc inspect storage foo
```

có thể:

```text
x:
    semantic storage = owned
    escape = NoEscape
    address = not observable
    allocation = eliminated
    physical storage = SSA

buffer:
    escape = ReturnEscape
    storage = caller-allocated
```

---

# 67. AI-readable storage facts

`.axmeta`/`.axmir` có thể chứa:

```json id="k5x9r3"
{
  "value": "x",
  "escape": "NoEscape",
  "address_observable": false,
  "allocation_eliminated": true,
  "physical_storage": "SSA"
}
```

Agent có thể hiểu tại sao compiler không tạo heap allocation.

---

# 68. Optimization boundary

Escape analysis:

```text id="n2m7q4"
may suggest
```

nhưng Verified MIR:

```text id="r8x3k1"
defines legal semantics
```

Optimizer không được dùng một escape guess để phá safety.

---

# 69. Safety vs optimization proof

Hai loại proof:

```text id="q4v9m6"
Safety proof:
    must be valid

Optimization proof:
    optional
```

Nếu escape không biết:

```text id="c7x2n8"
do less optimization
```

Không phải:

```text id="m1r5q9"
change semantics
```

---

# 70. Escape analysis và compiler pipeline

Pipeline hoàn chỉnh:

```text id="z6p2r8"
Typed HIR
   ↓
MIR
   ↓
Ownership
   ↓
Capability
   ↓
Drop
   ↓
Alias
   ↓
Effect
   ↓
Escape
   ↓
Verified MIR + analysis facts
   ↓
OptIR
   ↓
Storage Promotion
   ↓
SSA / MemorySSA
```

---

# 71. Escape Analysis Data Model

Đề xuất:

```text id="y8m3q6"
EscapeInfo {
    value_escape: Map<ValueId, EscapeSet>
    allocation_escape: Map<AllocationId, EscapeSet>

    address_observable: Set<ValueId>
    stable_address: Set<AllocationId>

    return_provenance: Map<ReturnId, Provenance>
    thread_transfer: Set<ValueId>
    external_escape: Set<ValueId>

    provenance: EscapeOrigin
}
```

---

# 72. Allocation decision model

```text id="p4x7m1"
StorageDecision {
    semantic_storage
    physical_storage
    address_stability
    allocation_required
    promotion_allowed
    reason
}
```

---

# 73. Storage decision priority

Compiler nên kiểm tra theo thứ tự:

```text id="c9r2v5"
1. Semantic storage-domain requirement
2. Ownership/capability validity
3. Stable-address requirement
4. Observable identity
5. Escape
6. Effect/Drop
7. ABI constraints
8. Optimization opportunity
```

Điều này tránh việc optimizer “đè” lên semantic requirements.

---

# 74. Determinism

Cùng:

```text id="w7m3q9"
source
target
compiler version
configuration
```

phải cho cùng semantic escape analysis.

Physical register/stack layout có thể thay đổi giữa optimization strategies, nhưng không được thay đổi program semantics.

---

# 75. Incremental

Thay đổi:

```text id="n5q8x2"
function foo
```

chỉ invalidate các caller phụ thuộc:

```text id="r3m7k1"
EscapeSummary(foo)
```

Không rebuild toàn bộ workspace.

---

# 76. Parallel

Các SCC/function không phụ thuộc có thể chạy song song.

Kết quả phải deterministic.

---

# 77. Invariants

### `AESCAPE-20`
Escape analysis is distinct from ownership.

### `AESCAPE-21`
Escape analysis is distinct from lifetime.

### `AESCAPE-22`
Escape analysis is distinct from capability validity.

### `AESCAPE-23`
Escape analysis is distinct from physical storage selection.

### `AESCAPE-24`
Escape states include `NoEscape`, `ArgumentEscape`, `ReturnEscape`, `HeapEscape`, `ThreadEscape`, `ExternalEscape`, and `UnknownEscape`.

### `AESCAPE-25`
Escape analysis tracks provenance of escaping values.

### `AESCAPE-26`
Escape analysis tracks allocation escape separately from value escape.

### `AESCAPE-27`
Unknown escape is conservative.

### `AESCAPE-28`
Unknown escape may not be treated as no escape.

### `AESCAPE-29`
A value that escapes to another execution domain must satisfy required Send semantics.

### `AESCAPE-30`
A capability escaping through return must preserve valid provenance.

### `AESCAPE-31`
A returned capability cannot outlive its owner.

### `AESCAPE-32`
Escape analysis cannot invalidate capability verification.

### `AESCAPE-33`
No-escape values may be promoted to stack, registers, inline storage, or SSA when semantics permit.

### `AESCAPE-34`
Heap allocation is not implied solely by ownership semantics.

### `AESCAPE-35`
Allocation elimination is permitted when allocation identity is unobservable and all semantic obligations are preserved.

### `AESCAPE-36`
Observable allocation identity prevents invalid allocation elimination or merging.

### `AESCAPE-37`
Stable-address contracts prevent storage promotion or relocation that changes observable address semantics.

### `AESCAPE-38`
Address observability is distinct from merely taking an internal address.

### `AESCAPE-39`
Non-escaping address-taking may still permit storage optimization.

### `AESCAPE-40`
Externally retained addresses require stable storage semantics.

### `AESCAPE-41`
Reallocation cannot invalidate live capabilities.

### `AESCAPE-42`
Escape analysis cooperates with alias analysis.

### `AESCAPE-43`
Escape analysis cooperates with effect analysis.

### `AESCAPE-44`
Escape analysis cooperates with capability analysis.

### `AESCAPE-45`
Escape analysis cooperates with concurrency analysis.

### `AESCAPE-46`
Escape analysis cooperates with async state analysis.

### `AESCAPE-47`
Escape analysis cooperates with GPU storage-domain analysis.

### `AESCAPE-48`
Foreign calls are conservative unless an explicit verified contract exists.

### `AESCAPE-49`
Device storage cannot be promoted into incompatible host storage.

### `AESCAPE-50`
External resources are not ordinary promotable allocations.

### `AESCAPE-51`
Caller allocation is an ABI optimization and does not change semantic ownership.

### `AESCAPE-52`
Move does not imply physical copying.

### `AESCAPE-53`
Return does not imply physical copying.

### `AESCAPE-54`
Closure environments participate in escape analysis.

### `AESCAPE-55`
Future state participates in escape analysis.

### `AESCAPE-56`
Only state live across suspension must become persistent Future state.

### `AESCAPE-57`
Escape analysis supports recursive call graphs through fixed-point analysis.

### `AESCAPE-58`
Escape summaries are incrementally cacheable.

### `AESCAPE-59`
Independent escape analyses may execute in parallel.

### `AESCAPE-60`
Escape results are deterministic.

### `AESCAPE-61`
Escape facts preserve source provenance.

### `AESCAPE-62`
Storage decisions are explainable.

### `AESCAPE-63`
Storage decisions may be inspected through compiler tooling.

### `AESCAPE-64`
Escape facts may feed optimization but cannot redefine semantics.

### `AESCAPE-65`
Optimization failure only reduces optimization opportunities.

### `AESCAPE-66`
Safety failure remains a compilation error.

### `AESCAPE-67`
Optimization level cannot alter escape semantics.

### `AESCAPE-68`
Physical storage lifetime may be shorter than semantic scope when unobservable.

### `AESCAPE-69`
Physical storage reuse cannot create semantic aliasing.

### `AESCAPE-70`
Allocation elimination cannot invalidate ownership, capability, Drop, or identity semantics.

### `AESCAPE-71`
Arena and pool storage obey their explicit lifetime contracts.

### `AESCAPE-72`
Shared ownership semantics are preserved even when physical representation is optimized.

### `AESCAPE-73`
Escape analysis does not act as a garbage collector.

### `AESCAPE-74`
Escape analysis does not require programmer-written annotations for ordinary cases.

### `AESCAPE-75`
The optimizer must preserve all observable storage-domain semantics.

### `AESCAPE-76`
Verified MIR remains the correctness boundary.

### `AESCAPE-77`
Escape analysis cannot manufacture safety proofs.

### `AESCAPE-78`
Storage promotion is valid only when all semantic preconditions are proven.

### `AESCAPE-79`
Escape information must participate in the build/cache fingerprint when it affects generated artifacts.

### `AESCAPE-80`
Compiler internal errors are distinct from user-level escape diagnostics.

---

# Kết quả quan trọng của BOOTSTRAP-138

Axiom hiện có đủ nền tảng để thực hiện một mô hình rất mạnh:

```text
             SOURCE
                │
                ▼
        ┌───────────────┐
        │    OWNERSHIP  │
        └───────┬───────┘
                ▼
        ┌───────────────┐
        │  CAPABILITY   │
        └───────┬───────┘
                ▼
        ┌───────────────┐
        │     ALIAS     │
        └───────┬───────┘
                ▼
        ┌───────────────┐
        │     EFFECT    │
        └───────┬───────┘
                ▼
        ┌───────────────┐
        │     ESCAPE    │
        └───────┬───────┘
                ▼
        ┌───────────────┐
        │ STORAGE OPT   │
        └───────┬───────┘
                ▼
       ┌──────────────────┐
       │      OptIR       │
       └──────────────────┘
```

Điều này củng cố một quyết định rất quan trọng của Axiom:

> **Không cần ép programmer chọn stack hay heap. Không cần bắt programmer viết lifetime. Không cần bắt programmer viết borrow checker syntax. Không cần `restrict`. Không cần `pure`.**

Compiler có thể tự suy luận phần lớn.

---

# BOOTSTRAP-139 — SSA, MemorySSA & Unified Dataflow Optimization IR

Task tiếp theo sẽ chuyển từ **“compiler biết chương trình làm gì”** sang **“compiler biểu diễn chương trình thế nào để tối ưu cực mạnh”**.

Trọng tâm:

```text
Verified MIR
      │
      ├── Ownership facts
      ├── Capability facts
      ├── AliasInfo
      ├── EffectInfo
      ├── EscapeInfo
      └── RangeInfo
             │
             ▼
          SSA IR
             │
             ▼
        MemorySSA
             │
             ▼
           OptIR
```

Đặc biệt sẽ khóa cách Axiom xử lý:

- SSA values;
- phi nodes;
- memory versions;
- load/store;
- alias-aware MemorySSA;
- partial aggregates;
- struct field SSA;
- arrays;
- loops;
- mutation;
- ownership moves;
- Drop;
- atomics/volatile;
- function calls;
- async state;
- GPU memory;
- và quan trọng nhất: **làm sao có SSA cực mạnh mà không phá semantics ownership/capability của MIR**.