Tiếp tục.

# BOOTSTRAP-055 — Verification Algorithms & Dataflow Engine

Đây là một trong những phần **quan trọng nhất của toàn bộ Axiom**.

Mục tiêu không phải xây một “borrow checker phiên bản khác”, mà là xây một **semantic verifier** có khả năng tự suy luận ownership, capability, lifetime và concurrency từ chương trình mà **không bắt programmer viết lifetime/borrow annotations**.

Nguyên tắc:

> **Programmer mô tả ý định. Compiler suy luận và chứng minh các invariant cần thiết.**

---

# 1. Kiến trúc Verification Engine

Không nên chạy từng checker hoàn toàn độc lập.

Đề xuất:

```text
                    Verified MIR Engine
                           │
          ┌────────────────┼────────────────┐
          │                │                │
     Type Facts       CFG/Dataflow      Storage Facts
          │                │                │
          └────────────────┼────────────────┘
                           │
                    Semantic State
                           │
       ┌───────────┬───────┼────────┬───────────┐
       ▼           ▼       ▼        ▼           ▼
   Ownership   Capability  Drop   Concurrency  Async
       │           │       │        │           │
       └───────────┴───────┼────────┴───────────┘
                           ▼
                    Verification Facts
                           │
                           ▼
                     Verified MIR
```

Các checker chia sẻ facts thay vì mỗi checker tự xây lại CFG/type/lifetime analysis.

---

# 2. CFG là nền tảng

Mọi function được chuyển thành:

```text
BasicBlock {
    statements
    terminator
}
```

Ví dụ:

```axiom
if condition {
    foo()
} else {
    bar()
}

baz()
```

CFG:

```text
        bb0
       /   \
     bb1   bb2
      |     |
     foo   bar
       \   /
        bb3
         |
        baz
         |
       return
```

---

# 3. Dataflow framework chung

Compiler cần một engine generic:

```text
DataflowAnalysis<State>
```

với:

```text
initial_state()
transfer(block, state)
join(a, b)
equals(a, b)
```

Sau đó Ownership, Capability, Drop... có thể sử dụng framework chung.

---

# 4. Forward vs backward analysis

Không phải mọi analysis đều đi cùng hướng.

### Forward

Phù hợp:

```text
ownership state
initialized state
capability creation
storage state
```

### Backward

Phù hợp:

```text
liveness
use-after-last-use
drop placement opportunities
escape analysis
```

Axiom cần cả hai.

---

# 5. Ownership state

Ownership state theo Place:

```text
OwnershipState =
    Uninit
    Owned
    Moved
    PartiallyMoved
    Dropped
```

Ví dụ:

```text
x.a = Owned
x.b = Moved
```

không đồng nghĩa:

```text
x = Moved
```

---

# 6. Ownership tree

Compiler duy trì:

```text
x
├── a
│   └── ...
├── b
└── c
```

State có thể:

```text
x
├── a → Owned
├── b → Moved
└── c → Owned
```

Đây là nền tảng cho partial move.

---

# 7. Move operation

MIR:

```text
y = Move(x)
```

Transfer:

```text
x → Moved
y → Owned
```

Nếu `x` có subplaces:

```text
Move(x.a)
```

chỉ đánh dấu:

```text
x.a → Moved
```

---

# 8. Move toàn object

```text
Move(x)
```

→ toàn bộ subtree của `x` thành moved.

Sau:

```text
use(x)
```

→ error.

---

# 9. Partial move

```text
let y = x.a
use(x.b)
```

hợp lệ nếu `x` có thể partial move.

State:

```text
x.a → Moved
x.b → Owned
```

---

# 10. Partial move + user Drop

Nếu `x` có custom Drop:

```text
struct Resource { ... }
impl Drop for Resource { ... }
```

thì:

```text
Move(x.a)
```

→ reject nếu compiler không thể đảm bảo user Drop semantics.

Đây là quyết định đã freeze.

---

# 11. Copy operation

MIR:

```text
y = Copy(x)
```

chỉ hợp lệ nếu type của `x` có semantic `Copy`.

State:

```text
x → Owned
y → Owned
```

Không chuyển ownership.

---

# 12. Clone

```text
y = Call Clone::clone(x)
```

là ordinary function semantics.

Compiler không giả định cost = 0.

---

# 13. Drop analysis

Drop analysis phải biết:

```text
x = Owned
x = Moved
x = PartiallyMoved
x = Dropped
```

Chỉ value còn resource obligation mới cần Drop.

---

# 14. Drop insertion

Ví dụ:

```axiom
fn f() {
    let a = A()
    let b = B()

    work()
}
```

MIR semantic:

```text
work()
```

Drop elaboration:

```text
work()
Drop(b)
Drop(a)
Return
```

---

# 15. Return

```axiom
fn f() -> A {
    let x = A()
    return x
}
```

Không:

```text
Drop(x)
Return x
```

mà:

```text
Move(x)
Return
```

Ownership chuyển cho caller.

---

# 16. `?`

```axiom
let x = foo()?
```

Nếu Err:

```text
cleanup locals
return Err
```

Nếu Ok:

```text
initialize x
continue
```

Drop verifier phải kiểm tra cả hai CFG paths.

---

# 17. Panic

Panic edge:

```text
normal
panic
```

Nếu unwind:

```text
panic edge
    ↓
drop initialized resources
    ↓
unwind
```

Nếu abort:

```text
panic
 ↓
abort
```

không cần resource cleanup semantics sau process termination.

---

# 18. Capability state

Capability state khác ownership.

Ví dụ:

```text
x: Owned
v: READ capability
```

có thể đồng thời tồn tại.

Capability:

```text
Capability {
    id
    provenance
    region
    access
    lifetime
}
```

---

# 19. Capability creation

```axiom
let v = view(x)
```

MIR:

```text
MakeView {
    owner: x
    region: Whole(x)
    access: Read
}
```

Verifier:

```text
x valid
region valid
```

→ create capability.

---

# 20. Read capabilities

Nhiều:

```text
view<T>
```

có thể coexist:

```text
v1 → READ(x)
v2 → READ(x)
v3 → READ(x)
```

Không conflict.

---

# 21. Mutable capability

```text
mut_view<T>
```

tạo:

```text
WRITE(x)
```

Không được tồn tại đồng thời:

```text
READ(x)
WRITE(x)
```

hoặc:

```text
WRITE(x)
WRITE(x)
```

nếu regions có thể overlap.

---

# 22. Region relation

Checker gọi:

```text
region_relation(r1, r2)
```

trả:

```text
DISJOINT
SAME
CONTAINS
CONTAINED_BY
OVERLAPS
UNKNOWN
```

---

# 23. Field disjointness

Ví dụ:

```axiom
struct Pair {
    a: i32
    b: i32
}
```

Compiler có thể prove:

```text
region(Pair.a)
∩
region(Pair.b)
= ∅
```

Do đó:

```text
mut_view(x.a)
mut_view(x.b)
```

có thể cùng tồn tại.

---

# 24. Array index

Ví dụ:

```axiom
mut_view(a[0])
mut_view(a[1])
```

Compiler chỉ prove DISJOINT nếu index facts chứng minh:

```text
0 != 1
```

Nếu:

```text
mut_view(a[i])
mut_view(a[j])
```

mà không biết `i != j`:

```text
UNKNOWN
```

→ không được coi là disjoint.

---

# 25. Range regions

Ví dụ:

```text
mut_view(a[0..10])
mut_view(a[10..20])
```

Compiler có thể prove:

```text
DISJOINT
```

nếu range semantics rõ ràng.

---

# 26. Capability expiration

Capability không cần programmer viết:

```text
'a
```

Compiler tìm last use.

Ví dụ:

```axiom
let v = view(x)
read(v)
mutate(x)
```

Sau `read(v)`:

```text
v
```

không còn live.

Mutation được phép.

---

# 27. Đây là điểm khác borrow checker truyền thống

Programmer không cần:

```text
drop(v)
```

chỉ để compiler biết lifetime kết thúc.

Compiler có thể xác định:

```text
last_use(v)
```

và capability hết hiệu lực semantic tại đó.

`drop(v)` chỉ cần nếu user muốn kết thúc explicit sớm.

---

# 28. Capability liveness

Dùng backward dataflow:

```text
LiveCapabilities(point)
```

Một capability live nếu có future use hoặc dependency.

---

# 29. Owner destruction

Nếu:

```text
v = view(x)
```

đang live:

```text
drop(x)
```

→ reject.

Nếu `v` dead:

```text
drop(x)
```

→ hợp lệ.

---

# 30. Vec relocation

Compiler biểu diễn:

```text
VecPush
```

với effect:

```text
MayRelocate(storage_region)
```

Nếu active capability phụ thuộc region:

```text
v → region(Vec.data)
```

thì:

```text
VecPush
```

→ reject nếu relocation có thể xảy ra.

---

# 31. Không cần biết implementation malloc

Đây là điều quan trọng.

Verifier chỉ cần biết:

```text
operation may invalidate storage identity
```

Không cần biết `malloc/realloc`.

---

# 32. Non-relocating Vec operation

Ví dụ:

```text
v[i] = value
```

không relocate.

Nếu capability region không conflict:

→ có thể hợp lệ.

---

# 33. `reserve`

```text
reserve(n)
```

có thể relocate.

Do đó active views vẫn có thể block.

Không coi capacity như permanent guarantee.

---

# 34. Stable storage

Storage contract:

```text
StableAddress
```

thì operation không được invalidate address theo contract.

---

# 35. Escape analysis

Compiler cần backward/forward escape analysis.

Ví dụ:

```axiom
fn f() {
    let x = Buffer(...)
    use(x)
}
```

Nếu x không escape:

```text
heap → stack/register
```

có thể.

---

# 36. View escape

Ví dụ:

```axiom
fn f(x: Buffer) -> view<u8> {
    return view(x)
}
```

không hợp lệ vì view provenance thuộc local owner `x`.

Compiler không thể để caller nhận dangling capability.

---

# 37. Valid returned view

Có thể:

```axiom
fn first(x: view<Array>) -> view<Item>
```

nếu returned capability provenance nằm trong input capability.

Đây là capability subregion propagation.

---

# 38. View × caller owner

Ví dụ:

```axiom
fn first(x: view<Array>) -> view<Item>
```

caller:

```axiom
let a = Array(...)
let b = first(a.view())
```

`b` phụ thuộc:

```text
a
```

compiler phải giữ dependency.

---

# 39. Send analysis

`Send` được query:

```text
is_send(TypeId)
```

nhưng với capability:

```text
is_send(capability)
```

phải xét:

```text
provenance
storage domain
access mode
```

---

# 40. View sang thread

Ví dụ:

```text
view(x)
   ↓
spawn
```

Compiler cần chứng minh:

```text
owner remains alive
storage is accessible from destination domain
read access is valid concurrently
```

Nếu không:

→ reject.

---

# 41. Owned value sang thread

```text
spawn(move || process(x))
```

thì:

```text
x ownership
 ↓
Move
 ↓
destination execution domain
```

và:

```text
is_send(x.type)
```

phải true.

---

# 42. Share analysis

`Share<T>` kiểm tra:

```text
multiple concurrent access
```

nhưng không tự cấp write.

Ví dụ:

```text
Arc<T>
```

nếu `T: Share`:

```text
READ
READ
READ
```

được phép.

---

# 43. `Arc<Mutex<T>>`

Compiler thấy:

```text
Arc
 ↓
Mutex
 ↓
Guard
```

Guard tạo:

```text
WRITE capability
```

và lock synchronization tạo ordering.

---

# 44. Lock guard

Guard:

```text
!Copy
Drop
```

Drop semantics:

```text
unlock
```

Nhưng đây là library-defined Drop behavior.

---

# 45. Guard × await

```axiom
let guard = lock.lock()
await something()
use(guard)
```

default:

```text
reject
```

vì sync guard không được giữ qua suspension.

Nếu AsyncMutex:

```text
await lock.lock()
```

→ khác abstraction.

---

# 46. Await boundary checker

Tại mỗi:

```text
Suspend(SuspensionPointId)
```

compiler tính:

```text
LiveLocals
LiveCapabilities
LiveGuards
```

và kiểm tra.

---

# 47. Rule tại await

Owned:

```text
Send requirement if future may migrate
```

View:

```text
must have valid cross-await storage contract
```

Sync guard:

```text
reject
```

trừ explicit supported abstraction.

---

# 48. GPU boundary

Kernel launch:

```text
host → GPU
```

compiler kiểm tra:

```text
storage domain
execution domain
Send-like transfer
capability validity
```

---

# 49. In-flight operation

Sau:

```text
launch(buffer)
```

compiler/runtime tạo logical dependency:

```text
GpuOp #17
    owns/retains
    buffer storage
```

Do đó:

```text
drop(buffer)
```

không thể làm storage invalid trước completion.

---

# 50. FFI boundary

Raw pointer:

```text
*mut T
```

được coi:

```text
unsafe machine-level value
```

Không tự động trở thành capability.

---

# 51. Unsafe conversion

Một unsafe wrapper có thể establish:

```text
pointer
 ↓
trusted provenance
 ↓
mut_view<T>
```

Sau đó capability verifier hoạt động bình thường.

---

# 52. Unsafe không tạo “magic mode”

Không:

```text
unsafe {
    everything_is_valid
}
```

Mà:

```text
unsafe operation
 ↓
specific trusted fact
 ↓
normal verifier resumes
```

---

# 53. FFI aliasing

Foreign pointer aliasing mặc định:

```text
UNKNOWN
```

Compiler không assume disjoint.

Nếu wrapper API cung cấp explicit safe contract:

```text
non-overlapping slices
```

thì wrapper có thể establish capability facts.

---

# 54. Comptime verifier

Comptime cũng chạy:

```text
Type
Ownership
Capability
Drop
```

giống runtime.

Khác ở:

```text
external capability sandbox
```

---

# 55. Comptime resource

```axiom
comptime {
    let x = Resource()
}
```

Drop trong compiler execution environment.

Không leak thành runtime ownership.

---

# 56. Verification phases

Đề xuất thứ tự:

```text
1. Type verification
2. CFG construction
3. Initialization analysis
4. Ownership analysis
5. Capability/region analysis
6. Drop analysis
7. Send/Share analysis
8. Async boundary analysis
9. GPU legality
10. FFI legality
11. Final semantic verification
```

---

# 57. Có thể chạy parallel ở đâu?

Sau khi CFG/type facts có:

```text
Ownership
Capability
Drop
```

có thể chạy nhiều phần song song.

Nhưng một số dependency tồn tại:

```text
Ownership
   ↓
Drop

Capability
   ↓
Concurrency

Async
   ↓
Send analysis
```

---

# 58. Verification result

Compiler tạo:

```text
VerificationResult {
    status
    facts
    diagnostics
}
```

Status:

```text
Verified
Rejected
InternalError
```

`InternalError` ≠ user program error.

---

# 59. ICE

Nếu compiler gặp trạng thái không thể xảy ra theo invariant:

```text
ICE
```

Không biến thành:

```text
user semantic error
```

Điều này rất quan trọng để debug compiler.

---

# 60. Verification facts

Ví dụ:

```text
Fact {
    kind: ProvenDisjoint
    region_a
    region_b
}
```

hoặc:

```text
Fact {
    kind: ValueIsSend
    type
}
```

Optimizer có thể sử dụng những facts này.

---

# 61. Fact provenance

Mỗi fact nên biết:

```text
FactId
Source
Confidence
Dependencies
```

Ví dụ:

```text
ProvenDisjoint
because:
    field_a != field_b
```

AI tooling có thể giải thích.

---

# 62. Không dùng “confidence score”

Compiler facts phải:

```text
PROVEN
NOT_PROVEN
```

không có:

```text
87% likely disjoint
```

Compiler semantics phải deterministic.

---

# 63. Alias analysis

Sau capability verification:

```text
KnownDisjoint
KnownSame
KnownOverlap
Unknown
```

được chuyển thành alias facts.

Optimizer sử dụng:

```text
KnownDisjoint
```

nhưng không tự tạo safety guarantee mới.

---

# 64. Lifetime inference

Axiom không cần source lifetime annotations.

Compiler tính:

```text
definition point
uses
moves
drops
escapes
suspension
execution-domain transfer
```

→ semantic lifetime.

---

# 65. Lifetime không phải một scalar

Không nên mô hình:

```text
lifetime = integer
```

Mà:

```text
Lifetime =
    CFG region
    +
    provenance
    +
    storage contract
```

Một capability có thể sống qua nhiều basic blocks nhưng không phải “một con số”.

---

# 66. Storage lifetime vs resource lifetime

Ví dụ:

```text
Resource
```

có thể:

```text
resource lifetime
```

kết thúc trước:

```text
memory allocation lifetime
```

Ví dụ allocator arena giữ memory nhưng resource đã Drop.

Do đó verifier phải phân biệt.

---

# 67. Escape analysis × Drop

Nếu object stack-promoted:

```text
resource lifetime
```

vẫn không thay đổi.

Chỉ physical storage thay đổi.

---

# 68. Escape analysis × stable address

Nếu address observable:

```text
escape = true
```

storage promotion bị hạn chế.

---

# 69. Escape analysis × view

Nếu view escape:

```text
owner storage
```

phải escape đủ lâu hoặc API contract phải đảm bảo lifetime.

---

# 70. Recursive data structures

Ví dụ:

```text
struct Node {
    next: Option<Box<Node>>
}
```

Type checker xử lý recursive nominal type.

Ownership verifier chỉ quan tâm runtime ownership graph.

Không cần GC.

---

# 71. Cyclic ownership

Safe owning values không tự nhiên tạo cycle nếu chỉ Move ownership.

Cycle chỉ xuất hiện qua explicit shared constructs:

```text
Arc
```

hoặc logical handles.

Cycle detection/reclamation là library semantics.

---

# 72. Generation handles

Verifier không coi:

```text
Handle<T>
```

là lifetime capability.

Khi resolve:

```text
Handle
 ↓
lookup
 ↓
capability
```

thì capability verification mới bắt đầu.

---

# 73. Data race detection

Axiom không cố chứng minh mọi race động bằng static theorem proving.

Thay vào đó:

```text
ordinary shared access
+
conflicting mutation
+
no synchronization
```

→ static rejection khi compiler có thể establish conflict.

Unsafe có thể tạo trusted boundary.

---

# 74. Atomic exception

Atomic operation:

```text
AtomicLoad
AtomicStore
AtomicCAS
```

được verifier công nhận là synchronization-aware.

Nhưng:

```text
Atomic<T>
```

không biến thành:

```text
ordinary T
```

---

# 75. Volatile

Volatile không tạo happens-before.

Do đó:

```text
volatile write
```

không làm:

```text
other thread read
```

safe synchronization.

---

# 76. GPU barrier

Tương tự:

```text
barrier()
```

chỉ establish ordering trong scope contract.

Không tự chuyển ownership.

---

# 77. Channel

Channel send:

```text
send(x)
```

là ownership transfer.

Nếu thành công:

```text
sender loses x
receiver owns x
```

Nếu fail:

```text
send(x) -> Err(x)
```

ownership trả lại sender.

---

# 78. Zero-copy channel

Verifier không yêu cầu:

```text
clone(x)
```

để gửi.

Ownership move là semantic primitive.

Implementation có thể queue pointer/storage handle nếu contract cho phép.

---

# 79. Verification và optimization

Sau:

```text
Verified MIR
```

optimizer có thể dùng facts:

```text
NoAlias
NoDanglingCapability
KnownBounds
Send
StableAddress
NoEscape
```

Nhưng các facts phải có provenance.

---

# 80. Đây là kiến trúc cốt lõi của Axiom

Từ đó có thể diễn đạt compiler safety bằng một câu:

> **Axiom không bắt programmer chứng minh lifetime; Axiom biến lifetime, ownership, aliasing và concurrency thành bài toán dataflow trên MIR.**

Đây chính là hướng để đạt mục tiêu:

```text
simple source
+
native performance
+
memory safety
+
no GC
+
no borrow syntax
```

mà không cần biến ngôn ngữ thành một hệ thống lifetime annotation phức tạp.

---

# 81. Frozen invariants — BOOTSTRAP-055

```text id="v0w1u4"
AVERIFY-20   Semantic verification is performed over CFG-based MIR.
AVERIFY-21   Verification uses shared compiler dataflow infrastructure.
AVERIFY-22   Ownership state is tracked at Place granularity.
AVERIFY-23   Ownership state distinguishes Uninit, Owned, Moved, PartiallyMoved and Dropped.
AVERIFY-24   Whole-place moves invalidate the entire owned subtree.
AVERIFY-25   Partial moves invalidate only the moved place subtree.
AVERIFY-26   Copy requires semantic Copy capability.
AVERIFY-27   Clone is explicit semantic duplication.
AVERIFY-28   Moved values cannot be read, moved, copied or dropped as if still owned.
AVERIFY-29   Drop obligations follow verified ownership state.
AVERIFY-30   Return transfers ownership without implying physical allocation.
AVERIFY-31   Early failure paths perform required cleanup.
AVERIFY-32   Panic cleanup follows the selected panic/unwind profile.
AVERIFY-33   User-defined Drop restricts partial moves.
AVERIFY-34   Capability state is distinct from ownership state.
AVERIFY-35   Capabilities contain provenance, region, access and lifetime information.
AVERIFY-36   Read capabilities may coexist when their regions are valid.
AVERIFY-37   Conflicting mutable capabilities are rejected.
AVERIFY-38   Read/write conflicts are rejected when regions may overlap.
AVERIFY-39   Write/write conflicts are rejected when regions may overlap.
AVERIFY-40   UNKNOWN region overlap cannot be treated as DISJOINT.
AVERIFY-41   Field-level disjointness may establish independent mutable capabilities.
AVERIFY-42   Proven index/range facts may establish region disjointness.
AVERIFY-43   Capability lifetime is inferred from dataflow and use.
AVERIFY-44   Programmer lifetime annotations are not required.
AVERIFY-45   Explicit drop may terminate an owned value or capability early where valid.
AVERIFY-46   Owner destruction is forbidden while dependent capabilities remain live.
AVERIFY-47   Relocation-capable operations cannot invalidate live dependent capabilities.
AVERIFY-48   Reserve does not establish permanent storage stability.
AVERIFY-49   Stable-address contracts constrain relocation.
AVERIFY-50   Escape analysis determines whether storage may be promoted or eliminated.
AVERIFY-51   Observable address identity prevents invalid storage promotion.
AVERIFY-52   Returned capabilities must preserve valid provenance.
AVERIFY-53   Capabilities cannot escape beyond their valid owner/storage lifetime.
AVERIFY-54   Execution-domain transfer requires appropriate Send semantics.
AVERIFY-55   Capability transfer across execution domains requires valid provenance and storage-domain semantics.
AVERIFY-56   Share does not imply mutable sharing.
AVERIFY-57   Synchronization is required for conflicting concurrent ordinary accesses.
AVERIFY-58   Mutex/RwLock guards establish synchronization-backed access capabilities.
AVERIFY-59   Synchronization guards cannot cross await unless explicitly designed for async execution.
AVERIFY-60   Await boundaries trigger live-state and capability verification.
AVERIFY-61   Future migration requires Send validity for retained state.
AVERIFY-62   Local execution may permit non-Send Future state where execution remains local.
AVERIFY-63   Async suspension does not automatically establish synchronization.
AVERIFY-64   GPU execution-domain boundaries require storage and capability verification.
AVERIFY-65   In-flight GPU operations retain required storage lifetime.
AVERIFY-66   GPU barriers do not transfer ownership.
AVERIFY-67   Foreign raw pointers are unsafe machine-level values, not safe capabilities.
AVERIFY-68   Unsafe pointer-to-capability conversion establishes explicit trusted preconditions.
AVERIFY-69   Safe verification resumes after an unsafe boundary for established contracts.
AVERIFY-70   Foreign aliasing is conservatively unknown unless an explicit contract proves otherwise.
AVERIFY-71   Comptime uses the same core ownership and capability semantics.
AVERIFY-72   Comptime external capabilities are checked separately from language safety.
AVERIFY-73   Generated code is fully reverified.
AVERIFY-74   Atomic operations are represented distinctly from ordinary accesses.
AVERIFY-75   Atomic operations preserve ordering and scope semantics.
AVERIFY-76   Volatile operations do not imply synchronization.
AVERIFY-77   GPU barriers do not imply ownership transfer.
AVERIFY-78   Channel send transfers ownership.
AVERIFY-79   Failed channel send returns ownership to the sender.
AVERIFY-80   Verification facts are explicit compiler facts.
AVERIFY-81   Verification facts have provenance where practical.
AVERIFY-82   Compiler semantic facts are deterministic, not probabilistic.
AVERIFY-83   Optimizers may consume proven verification facts.
AVERIFY-84   Optimizers cannot manufacture safety facts without valid proof.
AVERIFY-85   Lifetime is represented as CFG/provenance/storage semantics rather than a programmer-visible scalar annotation.
AVERIFY-86   Resource lifetime is distinct from physical memory lifetime.
AVERIFY-87   Storage optimization cannot alter resource lifetime semantics.
AVERIFY-88   Logical handles are not automatically capabilities.
AVERIFY-89   Handle resolution must establish valid access capability.
AVERIFY-90   Dataflow analyses may run in parallel where dependencies permit.
AVERIFY-91   Verification results distinguish user rejection from compiler internal failure.
AVERIFY-92   Internal compiler errors are not silently converted to user semantic errors.
AVERIFY-93   Verified MIR is produced only after required semantic invariants are established.
AVERIFY-94   Later transformations must preserve established semantic invariants.
AVERIFY-95   Verification state is independent from physical machine representation.
```

---

# Mốc 055 đã giải quyết vấn đề khó nhất

Đến đây, mô hình Axiom đã có câu trả lời tương đối hoàn chỉnh cho câu hỏi ban đầu của bạn:

> **“Không dùng GC, không bắt programmer viết borrow/lifetime, vậy làm sao vẫn an toàn?”**

Bằng:

```text
                 Axiom source
                      │
                      ▼
                    Typed
                      │
                      ▼
                     MIR
                      │
          ┌───────────┴───────────┐
          ▼                       ▼
     Ownership                 Capability
       Dataflow                  Dataflow
          │                       │
          ├──────────┬────────────┤
          ▼          ▼            ▼
        Drop      Lifetime     Aliasing
          │          │            │
          └──────────┼────────────┘
                     ▼
                Concurrency
                     │
             ┌───────┴────────┐
             ▼                ▼
           Async             GPU
             │                │
             └───────┬────────┘
                     ▼
                 FFI checks
                     │
                     ▼
              VERIFIED MIR
```

**Không GC. Không hidden reference counting. Không lifetime syntax. Không borrow syntax.**

Compiler làm phần khó.

---

## BOOTSTRAP-056 — Axiom Optimization IR & Alias/Memory Optimization

Bước tiếp theo hợp lý nhất là chuyển sang mặt còn lại của bài toán:

> Sau khi compiler **đã chứng minh** ownership/capability/lifetime, làm sao tận dụng những proof đó để Axiom thực sự đạt hiệu năng C/C++?

056 sẽ khóa:

- Alias analysis dựa trên capability
- Memory dependence
- Escape analysis
- Scalar replacement
- Stack/register promotion
- Allocation elimination
- Bounds-check elimination
- Loop optimization
- Auto-vectorization
- SIMD
- Inlining/devirtualization
- Generic specialization
- Closure optimization
- Async state optimization
- Load/store optimization
- `noalias` nội bộ nhưng **không cần `restrict` trong source**
- Memory effects
- Pure/read/write classification ở IR
- LTO
- PGO
- Và đặc biệt: **làm sao compiler tận dụng safety proof mà không biến programmer thành người phải viết optimization annotations**.