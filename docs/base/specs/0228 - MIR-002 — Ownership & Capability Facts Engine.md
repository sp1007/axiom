Tiếp tục với **MIR-002 — Ownership & Capability Facts Engine**. Đây thực sự là “bộ não” giúp Axiom đạt mục tiêu: **safety kiểu systems language nhưng không bắt programmer viết lifetime/borrow annotation**.

# MIR-002 — Ownership & Capability Facts Engine

## 1. Mục tiêu

Axiom không nên có:

```text
'a
'b
where 'a: 'b
&'a T
&'a mut T
```

trong source.

Nhưng compiler vẫn phải biết:

```text
Ai sở hữu object?
Capability nào đang tồn tại?
Capability đó trỏ vào đâu?
Nó còn hợp lệ không?
Có alias không?
Có conflict không?
Object có thể bị move/drop không?
Storage có thể relocate không?
```

Vì vậy:

```text
Source
  ↓
MIR
  ↓
Facts Engine
  ↓
Proof / Verification
```

---

# 2. Facts Engine không phải Borrow Checker

Đây là một distinction quan trọng.

Borrow checker truyền thống thường có mô hình:

```text
reference
lifetime
borrow
region
```

rất gần với abstraction mà programmer nhìn thấy.

Axiom thì:

```text
Source
  ↓
ownership semantics
  ↓
compiler facts
```

Facts Engine là **internal semantic analysis**.

Programmer chỉ thấy lỗi ở mức:

```text
cannot mutate x while a read view is active
```

chứ không thấy:

```text
lifetime parameter mismatch 'a / 'b
```

---

# 3. Fact model

Mỗi semantic entity có ID ổn định trong một compilation unit:

```text
OwnerId
ValueId
PlaceId
CapabilityId
RegionId
StorageId
ProvenanceId
BlockId
```

Ví dụ:

```text
x
 ↓
ValueId V12
 ↓
OwnerId O3
 ↓
StorageId S8
 ↓
Region R4
```

---

# 4. ValueId

`ValueId` đại diện cho một logical value trong MIR.

Ví dụ:

```text
let x = foo()
```

có thể:

```text
V10 = result of foo()
```

Sau optimization:

```text
V10
```

có thể bị eliminate.

Do đó `ValueId` không phải runtime object ID.

---

# 5. PlaceId

`PlaceId` biểu diễn vị trí storage semantic.

Ví dụ:

```text
x.a.b[i]
```

có thể:

```text
P1 = x
P2 = P1.a
P3 = P2.b
P4 = P3[i]
```

Nhưng compiler có thể canonicalize projection tree để không tạo object runtime nào.

---

# 6. Ownership state

Mỗi owning place có trạng thái:

```text
UNINITIALIZED
OWNED
PARTIALLY_MOVED
MOVED
DROPPED
INVALID
```

`INVALID` chủ yếu dành cho compiler-internal state/error recovery.

Safe MIR hợp lệ không được kết thúc ở trạng thái invalid.

---

# 7. Ví dụ Move

```text
let a = Foo()
let b = a
use(b)
```

Facts:

```text
V1 owns Foo
       ↓ move
V2 owns Foo

V1 = MOVED
V2 = OWNED
```

Không cần physical copy.

---

# 8. Copy

```text
let a = 10
let b = a
```

Facts:

```text
V1 = OWNED
V2 = OWNED
```

và:

```text
Type(a): Copy
```

Source vẫn valid.

---

# 9. Partial move

```text
struct User {
    name: String
    age: u32
}

let name = user.name
print(user.age)
```

Fact tree:

```text
user
├── name → MOVED
└── age  → OWNED
```

`user` không bị đánh dấu MOVED toàn bộ.

---

# 10. Drop state

Ownership state và Drop state phải tách nhau.

Ví dụ:

```text
x: String
```

có:

```text
Ownership = OWNED
DropObligation = ACTIVE
```

Sau:

```text
drop(x)
```

thành:

```text
Ownership = DROPPED
DropObligation = COMPLETE
```

---

# 11. Capability

Capability là quyền truy cập, không phải ownership.

Ví dụ:

```text
let v = view(x)
```

Facts:

```text
Owner:
    x

Capability:
    C1
    owner = x
    region = Region(x)
    access = READ
```

`C1` không sở hữu x.

---

# 12. Capability types

Axiom có hai loại chính:

```text
view<T>
mut_view<T>
```

Semantics:

```text
view<T>
    READ
    duplicable

mut_view<T>
    WRITE
    exclusive
    move-only
```

---

# 13. READ capability

Có thể:

```text
let a = view(x)
let b = a
let c = a
```

Compiler có thể biểu diễn:

```text
C1
C2
C3
```

tất cả:

```text
access = READ
region = Region(x)
```

Không conflict.

---

# 14. WRITE capability

```text
let a = mut_view(x)
```

tạo:

```text
C1:
    access = WRITE
    exclusive = true
```

Không được tạo:

```text
view(x)
mut_view(x)
```

đồng thời nếu vùng có thể overlap.

---

# 15. Region

Mỗi capability có region.

Ví dụ:

```text
x.a
```

có:

```text
Region(x.a)
```

và:

```text
x.b
```

có:

```text
Region(x.b)
```

Compiler có thể chứng minh:

```text
Region(x.a) DISJOINT Region(x.b)
```

---

# 16. Region relation

Giữ hệ thống đã thiết kế:

```text
DISJOINT
SAME
CONTAINS
OVERLAPS
CONTAINED_BY
UNKNOWN
```

Ví dụ:

```text
x
├── a
└── b
```

thì:

```text
Region(x.a) DISJOINT Region(x.b)
```

nếu layout/semantic projection đảm bảo hai field khác nhau.

---

# 17. Conflict matrix

| Existing | New READ | New WRITE | MOVE | DROP |
|---|---:|---:|---:|---:|
| READ | OK | ❌ | ❌ | ❌ |
| WRITE | ❌ | ❌ | ❌ | ❌ |
| MOVE | ❌ | ❌ | ❌ | ❌ |
| DROP | ❌ | ❌ | ❌ | ❌ |

Nhưng chỉ conflict khi region có thể overlap.

---

# 18. Disjoint field access

Ví dụ:

```text
fn update(x: mut_view<Pair>) {
    let a = mut_view(x.a)
    let b = mut_view(x.b)

    ...
}
```

Có thể hợp lệ:

```text
C1 WRITE Region(a)
C2 WRITE Region(b)
```

vì:

```text
a ∩ b = ∅
```

Đây là điểm Axiom có thể vừa an toàn vừa rất linh hoạt.

---

# 19. Unknown overlap

Ví dụ compiler gặp:

```text
some_dynamic_projection(x)
```

và không biết vùng trả về có overlap không.

Facts:

```text
Region(A) UNKNOWN Region(B)
```

Không được tự suy luận:

```text
DISJOINT
```

Nếu cả hai là WRITE:

```text
compile error
```

trừ khi API cung cấp semantic contract chứng minh disjointness.

---

# 20. Provenance

Region chưa đủ.

Compiler còn phải biết:

```text
Capability này xuất phát từ storage nào?
```

Ví dụ:

```text
x → storage S1
```

thì:

```text
view(x)
```

có:

```text
Provenance = S1
```

---

# 21. Vì sao provenance quan trọng?

Nếu:

```text
let p: *mut T = ...
```

trong unsafe code,

compiler không thể chỉ nhìn:

```text
address = 0x1234
```

rồi coi đó là safe capability.

Raw address và semantic storage identity khác nhau.

---

# 22. Unsafe → safe capability

Ví dụ conceptual:

```text
unsafe {
    let p = raw_pointer(...)
    let v = assume_valid_view(p, len)
}
```

Compiler tạo:

```text
Capability C1
    provenance = trusted S?
    region = supplied region
    access = READ
```

Từ đây safe verifier hoạt động trở lại.

Nhưng programmer đã chịu trách nhiệm cho precondition.

---

# 23. Capability validity

Capability có trạng thái:

```text
VALID
INVALID
CONSUMED
```

Ví dụ owner bị drop:

```text
x → DROP
```

thì mọi capability phụ thuộc x:

```text
C1
C2
C3
```

phải không còn live.

Nếu còn:

```text
compile error
```

---

# 24. Nhưng làm sao compiler biết capability còn live?

Đây là phần quan trọng.

Không cần source lifetime.

Compiler dùng:

```text
Control Flow Graph
+
Data Flow
+
Use/Def
+
Capability dependency
```

Ví dụ:

```text
let v = view(x)
use(v)
drop(x)
```

`v` có last use trước `drop(x)`.

Compiler có thể shorten:

```text
Capability lifetime:
creation → last_use(v)
```

Không phải:

```text
scope_end
```

---

# 25. Lifetime trong Axiom

Axiom vẫn có **lifetime**, nhưng:

> lifetime là compiler fact, không phải programmer syntax.

Ví dụ:

```text
let v = view(x)
foo(v)
bar()
```

Nếu `v` không dùng sau `foo(v)`:

```text
C1 lifetime ends here
```

ngay sau call.

---

# 26. Đây là lifetime shortening

Facts:

```text
Lexical scope:
    ────────────────────────

Actual capability lifetime:
    ───────
```

Compiler được phép kết thúc capability sớm.

Điều này tăng optimization freedom.

---

# 27. Owner lifetime cũng vậy

Ví dụ:

```text
let x = LargeObject()
use(x)
```

sau `use(x)` nếu không còn observable destructor effect:

```text
x lifetime
→ shortened
```

Nhưng nếu `Drop` có observable behavior:

```text
drop timing
```

phải giữ đúng semantic destruction point.

---

# 28. Resource lifetime khác memory lifetime

Ví dụ:

```text
File
```

Drop:

```text
close(fd)
```

Memory chứa wrapper có thể chết.

Nhưng:

```text
resource lifetime
```

là semantics riêng.

Do đó:

```text
Value lifetime
Resource lifetime
Memory lifetime
```

phải được phân biệt.

---

# 29. StorageId

`StorageId` biểu diễn storage identity.

Ví dụ:

```text
Box<T>
```

có storage:

```text
S1
```

Một `view` vào Box:

```text
C1 → S1
```

Nếu compiler stack-promote Box:

```text
S1:
heap → stack
```

thì `StorageId` vẫn là semantic identity nội bộ trong analysis.

Sau optimization có thể erase.

---

# 30. Relocation

Đây là nơi Facts Engine kết nối với `Vec`.

Ví dụ:

```text
let v = Vec(...)
let view = view(v)
v.push(...)
```

`push` có thể relocate storage.

Compiler thấy:

```text
C1 depends on S1
```

và:

```text
push may_relocate(S1)
```

Do đó:

```text
reject
```

nếu `view` còn live.

---

# 31. Nếu `reserve`?

```text
v.reserve(100)
```

không mặc định tạo:

```text
StableAddress
```

Vì reserve chỉ thay đổi capacity guarantee theo semantic API.

Đã freeze:

> `reserve` không phải stable-address guarantee.

---

# 32. Stable address

Nếu programmer thực sự cần:

```text
stable address
```

thì phải dùng abstraction có storage contract tương ứng:

```text
Box
Pool
Slab
Arena
StableBuffer
```

tùy API semantics.

---

# 33. Escape facts

Compiler cần theo dõi:

```text
NO_ESCAPE
LOCAL_ESCAPE
CALL_ESCAPE
THREAD_ESCAPE
GLOBAL_ESCAPE
UNKNOWN
```

Ví dụ:

```text
fn foo(x: mut_view<T>) {
    bar(x)
}
```

Nếu `bar` không lưu capability:

```text
CALL_ESCAPE = false
```

Compiler có thể tiếp tục.

---

# 34. Interprocedural escape

Nếu:

```text
fn bar(v: mut_view<T>) {
    global = v
}
```

thì:

```text
v → GLOBAL_ESCAPE
```

và nếu API không cho phép capability escape:

```text
compile error
```

---

# 35. Đây là nơi function contracts xuất hiện

Axiom không cần source effect system tổng quát.

Compiler có thể internally infer:

```text
bar:
    consumes READ capability
    does not retain
```

hoặc:

```text
bar:
    may retain capability
```

Nhưng programmer không cần viết:

```text
bar<'a>(...)
```

---

# 36. Function summary

Mỗi function sau analysis có semantic summary:

```text
FunctionSummary {
    inputs
    outputs

    ownership_effects
    capability_effects
    escape_effects

    may_panic
    may_suspend
    execution_domain

    allocation_facts
    resource_facts
}
```

Đây là compiler artifact.

---

# 37. Ví dụ summary

```text
fn sum(v: view<i32>) -> i32
```

compiler có thể suy ra:

```text
Input:
    C1 READ

Escape:
    NONE

Mutation:
    NONE

Suspend:
    NO

Ownership:
    DOES_NOT_CONSUME

Return:
    i32 independent of v
```

---

# 38. Function trả view

```text
fn first(v: view<T>) -> view<T>
```

summary:

```text
Return capability
    provenance = input capability
    region ⊆ input region
```

Do đó caller biết:

```text
result cannot outlive source
```

mà programmer không phải viết lifetime.

---

# 39. Function trả owner

```text
fn make() -> Box<T>
```

summary:

```text
Return:
    OWNS storage
    independent of input
```

Nếu:

```text
fn extract(v: view<T>) -> T
```

thì compiler phải chứng minh returned T không chứa reference/capability tới `v`, hoặc return type phải encode storage-independent ownership.

---

# 40. Capability cannot become ownership

Đây là invariant cực kỳ quan trọng.

```text
view<T>
```

không thể:

```text
return as T
```

trừ khi có:

```text
copy/clone/materialize
```

operation rõ ràng.

Không được:

```text
view → owner
```

một cách ngầm định.

---

# 41. Capability cannot outlive owner

```text
let v = view(x)
drop(x)
use(v)
```

Facts Engine:

```text
owner lifetime < capability lifetime
```

→ reject.

---

# 42. Capability cannot silently change access mode

```text
view<T>
```

không tự biến thành:

```text
mut_view<T>
```

Phải có operation tạo quyền WRITE và verifier kiểm tra exclusivity.

---

# 43. `mut_view` move semantics

```text
let a = mut_view(x)
let b = a
```

không phải Copy.

Facts:

```text
C1 → MOVED
C2 → VALID
```

Có nghĩa quyền WRITE được chuyển.

---

# 44. READ duplication

Ngược lại:

```text
let a = view(x)
let b = a
```

có thể tạo hai READ capabilities.

Không cần:

```text
Clone
```

vì duplication của read capability là semantic primitive.

---

# 45. Capability conflict graph

Compiler có thể duy trì graph:

```text
C1 READ R1
C2 READ R1
C3 WRITE R1
```

Edges:

```text
C1 ── conflict ── C3
C2 ── conflict ── C3
C1 ── compatible ─ C2
```

Nếu:

```text
C3
```

được tạo trong thời gian C1/C2 còn live:

```text
error
```

---

# 46. Không cần pairwise checking mãi mãi

Compiler thực tế không nên so sánh mọi capability với mọi capability.

Có thể dùng:

```text
Region tree
interval/range abstraction
SSA/dataflow
liveness sets
```

để giảm complexity.

MVP có thể dùng conservative algorithm.

Sau này tối ưu.

---

# 47. Region abstraction

Với contiguous storage:

```text
Region {
    base
    offset
    length
}
```

compiler semantic model không nhất thiết phải là physical pointer arithmetic.

Ví dụ:

```text
a[10..20]
```

có:

```text
Region(base=a, [10,20))
```

và:

```text
a[30..40)
```

→ DISJOINT.

---

# 48. Dynamic index

```text
a[i..j]
a[k..m]
```

nếu compiler không biết:

```text
j <= k
```

thì:

```text
UNKNOWN / MAY_OVERLAP
```

không tự assume disjoint.

---

# 49. Range analysis giúp tối ưu

Nếu compiler chứng minh:

```text
i < 10
j >= 20
```

thì có thể suy ra:

```text
Region(i-range) DISJOINT Region(j-range)
```

và cho phép concurrent/mutable access.

Đây là nơi:

```text
Ownership analysis
+
Range analysis
```

kết hợp rất mạnh.

---

# 50. Place projection + region

Ví dụ:

```text
x.a
x.b
```

compiler biết field offset/layout.

Nếu `a` và `b` là distinct fields:

```text
DISJOINT
```

không cần runtime check.

---

# 51. Array element

```text
a[i]
a[j]
```

không mặc định disjoint.

Nếu:

```text
i != j
```

được chứng minh:

```text
DISJOINT
```

Nếu không:

```text
UNKNOWN
```

---

# 52. Unsafe boundary

Unsafe có thể tạo:

```text
RawPointer
```

Facts:

```text
provenance = UNKNOWN
```

Nếu programmer chuyển nó thành safe capability:

```text
assume_valid
```

thì tạo:

```text
TrustedCapability
```

với preconditions đã được compiler/API ghi nhận.

---

# 53. Nhưng unsafe không lan truyền vô hạn

Ví dụ:

```text
unsafe {
    let p = ...
    let v = assume_valid_view(p)
}

safe_function(v)
```

`safe_function` không cần trở thành `unsafe`.

Nó nhận một capability đã được establish.

Đây là nguyên tắc:

> **Unsafe boundary establishes facts; safe verification resumes afterward.**

---

# 54. Thread migration

Facts Engine cũng theo dõi:

```text
ExecutionDomain
```

Ví dụ:

```text
spawn(move || use(x))
```

nếu task chuyển thread:

```text
x: Send
```

phải được chứng minh.

Nếu x:

```text
Rc<T>
```

thì:

```text
Rc !Send
```

→ reject.

---

# 55. Share

Nếu nhiều thread có:

```text
view(x)
```

thì:

```text
T: Share
```

phải được chứng minh.

`Send` và `Share` không gộp thành một property.

---

# 56. Async suspension

Facts Engine đánh dấu:

```text
SuspensionPoint S1
```

và snapshot:

```text
LiveValues
LiveCapabilities
LiveLocks
```

Trước `await`:

```text
C1 READ
C2 WRITE
L1 MutexGuard
```

Sau await:

compiler kiểm tra từng item có được phép tồn tại không.

---

# 57. Ví dụ lock

```text
let guard = mutex.lock()
foo().await
```

`MutexGuard` synchronous không được sống qua await.

Facts:

```text
L1 = synchronous lock
S1 = suspension
```

→ reject.

Không cần programmer biết lý do bằng lifetime syntax.

Diagnostic:

```text
AXxxxx: synchronous lock guard cannot remain active across await
```

---

# 58. Owned value qua await

```text
let x = LargeObject()
foo(x).await
use(x)
```

Nếu `x` là owned value và Future/state machine có thể chứa nó:

```text
valid
```

Compiler đưa x vào async state.

---

# 59. Capability live-set

Tại mỗi program point:

```text
LiveCapabilities(P)
```

Ví dụ:

```text
P1: {}
P2: {C1}
P3: {C1}
P4: {}
```

C1 lifetime:

```text
P2 → P3
```

Không phải toàn lexical scope.

---

# 60. Ownership live-set

Tương tự:

```text
LiveOwners(P)
```

nhưng ownership có thể tồn tại dù không có active capability.

Ví dụ:

```text
x owned
```

không đồng nghĩa:

```text
x borrowed
```

---

# 61. Drop eligibility

`drop(x)` chỉ hợp lệ nếu:

```text
Ownership(x) = OWNED
```

và:

```text
DependentCapabilities(x) = ∅
```

Nếu còn capability:

```text
error
```

---

# 62. Relocation eligibility

Storage có thể relocate nếu:

```text
NoStableAddressContract
AND
NoDependentCapability
AND
NoRawAddressObservation
AND
NoInFlightOperation
```

Đây là một invariant cực mạnh.

---

# 63. I/O kết nối trực tiếp

Ví dụ:

```text
async_read(buffer)
```

OS operation đang sử dụng buffer.

Facts:

```text
Operation O1
    depends_on Storage S1
```

Do đó:

```text
dealloc(S1)
relocate(S1)
```

bị cấm cho tới completion/cancellation-safe point.

---

# 64. GPU cũng dùng cùng mô hình

Kernel:

```text
@kernel fn add(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
)
```

Facts:

```text
C1 READ DeviceStorage S1
C2 READ DeviceStorage S2
C3 WRITE DeviceStorage S3
```

Kernel launch:

```text
Operation G1
    depends_on S1,S2,S3
```

Host không được deallocate/move storage khi G1 còn in-flight.

---

# 65. Đây là lợi thế của một Facts Engine thống nhất

Không cần:

```text
MemoryChecker
GpuMemoryChecker
AsyncMemoryChecker
IoMemoryChecker
ThreadMemoryChecker
```

mỗi cái có một ownership system khác nhau.

Tất cả đều dùng:

```text
SemanticFactsEngine
```

với:

```text
Owner
Capability
Region
Provenance
Storage
Operation
ExecutionDomain
```

---

# 66. Algorithm tổng quát

MVP có thể làm theo pipeline:

```text
1. Build CFG
2. Build use-def chains
3. Build Place projections
4. Infer ownership transitions
5. Infer capability creation/consumption
6. Compute capability liveness
7. Build region relations
8. Infer escape
9. Infer Send/Share
10. Analyze suspension
11. Analyze Drop dependencies
12. Verify conflicts
13. Produce function summary
```

---

# 67. Sau đó chạy fixed-point interprocedural

Ví dụ:

```text
foo → bar → baz
```

Ban đầu summary chưa hoàn chỉnh.

Compiler:

```text
baz summary
    ↓
bar summary
    ↓
foo summary
```

Nếu recursive call:

```text
foo → foo
```

dùng fixed-point iteration.

---

# 68. Không cần phân tích toàn bộ project mỗi lần

Function summary được cache:

```text
FunctionId
+
GenericArguments
+
TargetABI
+
RelevantSemanticInputs
```

→ summary cache.

Điều này kết nối với incremental compilation.

---

# 69. Generic function

```text
fn foo<T>(x: T)
```

Facts phụ thuộc vào:

```text
T: Copy?
T: Send?
T: Drop?
```

Trait solver đã resolve constraint.

Compiler có thể instantiate summary cho:

```text
foo<i32>
foo<String>
foo<MyType>
```

hoặc dùng polymorphic summary nếu có thể.

---

# 70. Function summary không phải ABI

Đây là internal compiler metadata.

Không nên biến binary ABI thành:

```text
ownership metadata
capability metadata
```

trừ khi dynamic/runtime feature thực sự cần.

Safe static semantics nên erase.

---

# 71. Khi nào Facts phải tồn tại runtime?

Chỉ khi semantics yêu cầu.

Ví dụ:

```text
Arc
Mutex
Channel
Future
```

bản thân runtime abstraction có state.

Nhưng:

```text
view
mut_view
ownership fact
region fact
```

thường không cần runtime metadata.

---

# 72. Diagnostic generation

Facts Engine không nên trả:

```text
borrow error
```

mà diagnostic semantic:

```text
AX0207: cannot mutate `x` while a read view is active
```

Kèm:

```text
active view created here
mutation attempted here
```

Compiler có source spans:

```text
x ────────────────┐
                  │
view(x)            │
                  │
                  └── mutation
```

AI agent cũng dễ parse.

---

# 73. Diagnostic machine-readable

Mỗi error:

```text
{
    code: "AX0207",
    severity: "error",
    primary_span: ...,
    related_spans: [...],
    facts: {
        access: "WRITE",
        conflict: "READ",
        region: "..."
    }
}
```

Human message và machine data tách nhau.

---

# 74. Quan trọng: không expose implementation detail

Không báo:

```text
RegionId R37 conflicts with Capability C12
```

cho programmer mặc định.

Nên báo:

```text
`x` is still being read through `v`
```

Mở rộng `--explain` mới có internal details.

---

# 75. Facts Engine architecture

Tôi đề xuất:

```text
compiler/
└── facts/
    ├── value.rs
    ├── place.rs
    ├── ownership.rs
    ├── capability.rs
    ├── region.rs
    ├── provenance.rs
    ├── storage.rs
    ├── escape.rs
    ├── concurrency.rs
    ├── suspension.rs
    ├── drop.rs
    ├── summary.rs
    ├── conflict.rs
    ├── dataflow.rs
    └── engine.rs
```

Tên file chỉ minh họa; implementation cuối có thể dùng Axiom khi compiler self-host.

---

# 76. Fact database

Có thể hình dung:

```text
FactDB
├── Values
├── Places
├── Owners
├── Capabilities
├── Regions
├── Provenances
├── Storages
├── Operations
├── Suspensions
└── FunctionSummaries
```

Các pass query:

```text
facts.owner_of(place)
facts.capability(cap)
facts.region_of(cap)
facts.may_overlap(a,b)
facts.can_move(place)
facts.can_drop(place)
facts.can_relocate(storage)
facts.is_send(value)
facts.is_share(value)
```

---

# 77. Không cho optimization tự sửa Facts tùy ý

Optimization không nên làm:

```text
facts.remove(C1)
```

một cách tùy tiện.

Thay vào đó:

```text
MIR transformation
      ↓
Facts invalidated
      ↓
recompute / incrementally update
      ↓
verify
```

Điều này tránh compiler bug cực khó debug.

---

# 78. Facts có provenance của chính nó

Một fact có thể ghi:

```text
Fact:
    A DISJOINT B

Source:
    struct field distinction

Confidence:
    PROVEN
```

hoặc:

```text
Source:
    unsafe trusted contract
```

Điều này hữu ích cho debugging/compiler development.

---

# 79. Proof levels

Tôi đề xuất nội bộ chỉ cần 3 mức:

```text
PROVEN
TRUSTED
UNKNOWN
```

### PROVEN

Compiler chứng minh.

### TRUSTED

Xuất phát từ explicit unsafe/ABI/platform contract.

### UNKNOWN

Không đủ thông tin.

Không có:

```text
probably
maybe
likely
```

trong safety verification.

---

# 80. TRUSTED không có nghĩa SAFE

Đây là distinction rất quan trọng.

```text
unsafe contract
```

có thể tạo:

```text
TRUSTED capability
```

nhưng compiler không chứng minh tính đúng đắn của contract.

Nó chỉ nói:

> Programmer đã vượt qua boundary chịu trách nhiệm.

---

# 81. Optimization chỉ được dùng fact phù hợp

Ví dụ:

```text
PROVEN NoAlias
```

→ optimizer được dùng.

`TRUSTED NoAlias`:

→ có thể dùng, nhưng nếu contract sai thì programmer đã vi phạm unsafe precondition.

`UNKNOWN NoAlias`:

→ không được dùng.

---

# 82. Đây là cách Axiom cân bằng performance và safety

```text
SAFE
    compiler proves

UNSAFE
    programmer establishes

OPTIMIZER
    consumes facts
```

Không cần:

```text
GC
```

và không cần:

```text
programmer-written borrow checker
```

---

# 83. Invariant quan trọng nhất

> **Không có semantic fact nào được tạo chỉ vì optimizer muốn nó tồn tại.**

Ví dụ optimizer không được nói:

```text
"nếu coi hai pointer không alias thì code nhanh hơn"
```

rồi tự tạo:

```text
NoAlias
```

Facts phải có nguồn gốc.

---

# 84. Facts lifecycle

```text
Source
 ↓
Infer
 ↓
Prove / Trust
 ↓
Verify
 ↓
Optimize
 ↓
Invalidate stale facts
 ↓
Recompute if needed
 ↓
Lower
 ↓
Erase
```

---

# 85. Frozen invariants

```text id="7d6z4n"
AFACT-20 — Facts Are Compiler Semantic State

AFACT-21 — Facts Are Not Source-Level Lifetime Syntax

AFACT-22 — Ownership Facts Track Resource Authority

AFACT-23 — Capability Facts Track Access Authority

AFACT-24 — Capability Does Not Imply Ownership

AFACT-25 — Provenance Identifies Semantic Storage Origin

AFACT-26 — Regions Describe Access Scope

AFACT-27 — Region Relations Must Be Conservative

AFACT-28 — UNKNOWN Cannot Be Treated As DISJOINT

AFACT-29 — READ Capabilities May Coexist

AFACT-30 — WRITE Capabilities Require Exclusivity

AFACT-31 — Capability Lifetime Is Compiler-Inferred

AFACT-32 — Capability Lifetime May Be Shortened

AFACT-33 — Owner Lifetime Must Dominate Dependent Capability Lifetime

AFACT-34 — Drop Requires Ownership And No Dependent Capability

AFACT-35 — Move Transfers Ownership

AFACT-36 — Copy Preserves Independent Value Semantics

AFACT-37 — Partial Moves Are Field-Aware

AFACT-38 — Relocation Requires No Dependent Stable Capability

AFACT-39 — Stable Address Is An Explicit Contract

AFACT-40 — Escape Analysis Is Part Of Semantic Analysis

AFACT-41 — Function Summaries Capture Relevant Semantic Facts

AFACT-42 — Function Summaries Are Not ABI Metadata

AFACT-43 — Send And Share Are Distinct Facts

AFACT-44 — Suspension Analysis Uses Capability And Ownership Facts

AFACT-45 — In-Flight Operations Create Storage Dependencies

AFACT-46 — Unsafe May Establish Trusted Facts

AFACT-47 — Trusted Facts Are Not Compiler-Proven Facts

AFACT-48 — Unknown Facts Cannot Satisfy Safety Proofs

AFACT-49 — Optimizers May Consume Facts But Cannot Invent Safety Facts

AFACT-50 — Invalidated Facts Must Not Survive Semantic Transformation

AFACT-51 — Every Optimization-Relevant Fact Has A Provenance

AFACT-52 — Facts May Be Erased After Their Semantic Obligations End

AFACT-53 — Runtime Metadata Is Not Required For Static Facts

AFACT-54 — Facts Engine Is Shared Across Memory, Async, IO, GPU And Concurrency

AFACT-55 — Safe Verification Resumes After Unsafe Boundaries

AFACT-56 — Diagnostics Must Explain Semantic Conflicts In Source Terms

AFACT-57 — Internal Fact IDs Are Not Programmer-Facing Semantics

AFACT-58 — Fact Analysis Must Be Deterministic

AFACT-59 — Function Summary Computation Must Reach A Stable Fixed Point

AFACT-60 — Cached Facts Must Be Invalidated By Relevant Semantic Changes
```

---

# 86. Một ví dụ hoàn chỉnh

Source:

```text
fn process(x: Data) -> i32 {
    let v = view(x.values)

    let sum = sum_values(v)

    x.update()

    sum
}
```

Facts ban đầu:

```text
x
└── values
```

Sau:

```text
v = view(x.values)
```

ta có:

```text
Owner:
    x

Capability:
    C1
    READ
    Region(x.values)
```

Call:

```text
sum_values(v)
```

nếu summary nói:

```text
does not retain v
```

thì sau call:

```text
C1 lifetime ends
```

Do đó:

```text
x.update()
```

hợp lệ.

---

Nếu source là:

```text
let v = view(x.values)
store_global(v)
x.update()
```

Facts:

```text
C1
    READ
    GLOBAL_ESCAPE
```

→ compiler phát hiện view escape.

Nếu ngôn ngữ/API không cho phép:

```text
error
```

---

# 87. Và đây chính là điểm tôi muốn giữ cho Axiom

Không thiết kế:

```text
Axiom = Rust nhưng bỏ lifetime syntax
```

Mà thiết kế:

```text
Axiom
    = value semantics
    + ownership semantics
    + capability semantics
    + compiler-inferred lifetime
    + conservative alias analysis
    + explicit unsafe
```

Đó là kiến trúc khác hẳn.

---

# 88. Một hệ quả rất tốt

Với mô hình này, programmer có thể viết code gần C:

```text
fn process(a: mut_view<Data>) {
    ...
}
```

nhưng compiler bên dưới có thể có analysis phức tạp gần với một hệ thống ownership/region/escape checker rất mạnh.

**Complexity nằm trong compiler, không nằm trong syntax của Axiom.**

---

# 89. Bước tiếp theo

Phần semantic core tiếp theo nên là:

# **ERROR/PANIC/UNWIND-001**

Phần này trước đây ta đã đánh dấu còn thiếu.

Cần chốt dứt điểm:

```text
Result<T,E>
Option<T>

?
try

panic()
trap()
abort()

Drop
close()

unwind
abort profile

async cancellation

FFI exception boundary

OS error

fatal runtime failure
```

Đặc biệt phải giải quyết một câu hỏi rất quan trọng cho Axiom:

> **Làm thế nào để `Result` cực kỳ rẻ, panic/unwind là optional, nhưng Drop vẫn deterministic trong mọi đường thoát — mà không biến compiler thành một hệ thống exception phức tạp như C++?**