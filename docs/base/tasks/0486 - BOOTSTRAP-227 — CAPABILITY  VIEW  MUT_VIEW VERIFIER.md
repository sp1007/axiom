# BOOTSTRAP-227 — CAPABILITY / VIEW / MUT_VIEW VERIFIER

**TRẠNG THÁI: FROZEN / COMPLETED**

Đây là phần nối trực tiếp sau Ownership Verifier.

Nếu 226 trả lời:

> **“Ai sở hữu giá trị này?”**

thì 227 trả lời:

> **“Ai được phép truy cập vùng dữ liệu này, theo quyền gì, trong khoảng thời gian nào, và compiler có thể chứng minh các truy cập có xung đột hay không?”**

Đây là cơ chế cho phép Axiom **không cần `&T`, `&mut T`, lifetime annotation**, nhưng vẫn có memory safety và alias analysis đủ mạnh cho tối ưu hóa.

---

# 1. Kiến trúc tổng thể

```text
                    Ownership Verifier
                           │
                           ▼
                 ┌───────────────────┐
                 │ Capability Model  │
                 └─────────┬─────────┘
                           │
          ┌────────────────┼────────────────┐
          ▼                ▼                ▼
      Provenance         Region          Access
          │                │                │
          └────────────────┼────────────────┘
                           ▼
                 Capability Verifier
                           │
            ┌──────────────┼──────────────┐
            ▼              ▼              ▼
        Lifetime        Conflict       Escape
            │              │              │
            └──────────────┼──────────────┘
                           ▼
                    Verified MIR
                           │
                           ▼
                     Alias Analysis
                           │
                           ▼
                     Optimization
```

---

# 2. Capability không phải reference

Đây là một quyết định rất quan trọng.

Axiom **không định nghĩa**:

```text
&T
&mut T
'a
```

như một phần syntax Core.

Thay vào đó compiler có semantic object:

```text
Capability
```

Programmer chỉ thấy:

```axiom
view<T>
mut_view<T>
```

---

# 3. Capability gồm những gì?

Canonical internal representation:

```text
Capability {
    id
    provenance
    region
    access
    lifetime
    storage_domain
    execution_domain
    mutability
    escape
}
```

Trong đó:

```text
provenance
region
access
lifetime
```

là bốn thành phần cốt lõi.

---

# 4. Provenance

Provenance trả lời:

> Capability này xuất phát từ owner/storage nào?

Ví dụ:

```axiom
let user = make_user()
let name = view(user.name)
```

Compiler:

```text
Capability C1
    provenance = user.name
```

Không phải chỉ:

```text
address = 0x12345678
```

---

# 5. Vì sao provenance quan trọng?

Nếu:

```text
p = integer_to_pointer(0x1234)
```

compiler không được tự suy luận:

```text
p points to user
```

Chỉ địa chỉ số không tạo ra safe provenance.

---

# 6. Region

Capability không nhất thiết đại diện toàn bộ object.

Ví dụ:

```axiom
view(user.name)
```

region:

```text
user.name
```

Trong:

```axiom
view(user)
```

region:

```text
user.*
```

---

# 7. Region relation

Axiom sử dụng lattice:

```text
DISJOINT
SAME
CONTAINS
CONTAINED_BY
OVERLAPS
UNKNOWN
```

Ví dụ:

```text
user.name
user.age
```

→ `DISJOINT`.

---

# 8. Nested region

```text
user
└── profile
    ├── name
    └── age
```

Khi có:

```text
view(user.profile)
```

và:

```text
view(user.profile.name)
```

relation:

```text
profile CONTAINS profile.name
```

Hai capability READ có thể cùng tồn tại.

---

# 9. READ capability

```text
view<T>
```

tạo:

```text
Access = READ
```

Nhiều READ capability trên cùng region được phép.

```text
v1 = view(x)
v2 = view(x)
v3 = view(x)
```

hợp lệ nếu tất cả đều READ.

---

# 10. WRITE capability

```text
mut_view<T>
```

tạo:

```text
Access = WRITE
```

WRITE là exclusive.

Không thể có:

```text
READ + WRITE
```

trên vùng có thể overlap.

---

# 11. WRITE + WRITE

Không được:

```text
v1 = mut_view(x)
v2 = mut_view(x)
```

nếu compiler không chứng minh:

```text
region(v1) DISJOINT region(v2)
```

---

# 12. READ + READ

Được:

```text
a = view(x)
b = view(x)
```

và:

```text
use(a)
use(b)
```

---

# 13. WRITE + READ

```text
a = mut_view(x)
b = view(x)
```

→ reject nếu overlap.

---

# 14. DISJOINT exception

Đây là điểm làm Axiom khác một borrow checker đơn giản.

```axiom
let a = mut_view(x.left)
let b = mut_view(x.right)
```

Nếu compiler biết:

```text
x.left ∩ x.right = ∅
```

thì:

```text
WRITE(x.left)
WRITE(x.right)
```

có thể đồng thời tồn tại.

---

# 15. Field-sensitive capability

Ví dụ:

```axiom
struct Pair {
    x: i32
    y: i32
}
```

Compiler biết:

```text
region(p.x)
region(p.y)
```

là disjoint.

Điều này rất quan trọng cho:

- vectorization;
- parallelism;
- function calls;
- struct mutation;
- SIMD;
- GPU.

---

# 16. Slice range

Đối với:

```text
view(array[0..10])
```

region không chỉ là:

```text
array
```

mà là:

```text
array[0:10]
```

---

# 17. Range relation

Ví dụ:

```text
A = [0, 10)
B = [10, 20)
```

→ `DISJOINT`.

```text
A = [0, 10)
B = [5, 20)
```

→ `OVERLAPS`.

```text
A = [0, 20)
B = [5, 10)
```

→ `CONTAINS`.

---

# 18. Unknown range

```axiom
let a = mut_view(buffer[0..n])
let b = mut_view(buffer[i..j])
```

Nếu compiler không biết quan hệ giữa `n`, `i`, `j`:

```text
UNKNOWN
```

Không được tự coi là DISJOINT.

---

# 19. Range proof

Compiler có thể sử dụng Range Analysis:

```text
0 <= i
i < 10
```

để chứng minh:

```text
buffer[i]
```

nằm trong region hợp lệ.

---

# 20. Capability creation

MIR:

```text
MakeView {
    source: Place
    region: Region
    result: CapabilityId
}
```

Ví dụ:

```axiom
let v = view(x)
```

→

```text
C1:
    provenance = x
    region = x.*
    access = READ
```

---

# 21. Mutable capability

```axiom
let v = mut_view(x)
```

→

```text
C2:
    provenance = x
    region = x.*
    access = WRITE
```

---

# 22. Capability lifetime

Capability có lifetime semantic:

```text
start
   │
   ├── use
   ├── use
   └── end
```

Không nhất thiết bằng lexical scope.

---

# 23. Last use

Ví dụ:

```axiom
let v = view(x)

inspect(v)

do_work()
```

Nếu `v` không còn dùng sau:

```text
inspect(v)
```

compiler có thể kết thúc capability tại đó.

---

# 24. Nhưng explicit stored capability

Nếu:

```axiom
let v = view(x)
store(v)
```

capability escape sang storage khác.

Khi đó lifetime không thể tự rút ngắn trước `store`.

---

# 25. Ephemeral implicit conversion

Axiom cho phép:

```axiom
fn inspect(x: view<Data>)

let data = make()
inspect(data)
```

Compiler tạo capability tạm thời:

```text
data
 ↓
C1 READ
 ↓
inspect
 ↓
C1 END
```

Không cần:

```text
let v = view(data)
```

---

# 26. Không implicit escape

Ví dụ:

```axiom
fn get(data: Data) -> view<Field>
```

Compiler không được biến:

```text
return view(data.field)
```

thành capability dangling khi `data` là local owned value bị destroy.

---

# 27. Return view

Nếu:

```axiom
fn first(data: Data) -> view<Item>
```

return capability phải có provenance:

```text
return C {
    provenance = arg0
}
```

Caller phải có owner tương ứng đủ lifetime.

---

# 28. Không cần lifetime syntax

Không viết:

```text
fn first<'a>(x: &'a Data) -> &'a Item
```

Compiler tự xây:

```text
ReturnCapability {
    provenance = arg0
}
```

Đây là một trong những mục tiêu quan trọng nhất của Axiom.

---

# 29. Capability dependency graph

Ví dụ:

```text
Owner X
  │
  ├── C1 view(X.a)
  ├── C2 view(X.b)
  └── C3 mut_view(X.c)
```

Compiler duy trì graph:

```text
X
├── C1
├── C2
└── C3
```

Khi Drop X:

```text
can_drop(X)?
```

chỉ true nếu không còn dependent capability.

---

# 30. Capability end

Capability có thể kết thúc do:

- last use;
- explicit scope end;
- move;
- owner destruction;
- task completion;
- closure destruction;
- future destruction.

---

# 31. Explicit capability destruction

Không cần Core syntax riêng.

Compiler có thể sinh:

```text
EndCapability(C1)
```

khi lifetime kết thúc.

---

# 32. Capability duplication

`view<T>` có thể duplicate:

```axiom
let a = view(x)
let b = a
```

Semantic:

```text
C1 READ
   ├── C2 READ
   └── original C1
```

Không phải Copy của underlying `T`.

---

# 33. Vì sao view không phải Copy?

Vì:

```text
Copy(T)
```

có nghĩa value duplication.

Còn:

```text
view<T>
```

là capability duplication.

Hai khái niệm khác nhau.

---

# 34. `mut_view` không duplicate

```axiom
let a = mut_view(x)
let b = a
```

`a` chuyển sang `b`:

```text
a → MOVED
b → WRITE capability
```

Không tạo hai WRITE capabilities.

---

# 35. Reborrow

Axiom không cần expose `reborrow`.

Compiler có thể nội bộ tạo capability con.

Ví dụ:

```text
mut_view(x)
    ↓
mut_view(x.field)
```

Capability:

```text
C1 WRITE(x)
    ↓
C2 WRITE(x.field)
```

Compiler phải đảm bảo semantics của C1/C2 không tạo conflict.

---

# 36. Nested mutable access

Ví dụ:

```axiom
fn f(x: mut_view<User>) {
    g(x.name)
}
```

`g` nhận:

```text
mut_view<String>
```

Compiler tạo subregion:

```text
User.name
```

---

# 37. Parent capability trong lúc child active

Không nhất thiết phải coi parent capability biến mất.

Nhưng verifier phải ngăn:

```text
C1 WRITE(user)
C2 WRITE(user.name)
```

đồng thời thực hiện các thao tác conflict.

Một mô hình đơn giản:

```text
parent capability suspended
```

trong thời gian child mutable capability active.

---

# 38. Read parent + Write child

```text
view(user)
mut_view(user.name)
```

→ conflict vì parent READ bao phủ child WRITE.

---

# 39. Read sibling + Write sibling

```text
view(user.age)
mut_view(user.name)
```

→ OK nếu field disjoint.

---

# 40. Unknown projection

Nếu:

```axiom
let field = runtime_field()
```

compiler không biết field nào:

```text
region = UNKNOWN
```

WRITE capability sẽ không được coi là disjoint với arbitrary region.

---

# 41. Conservative rule

```text
UNKNOWN overlap
    ≠
DISJOINT
```

Đây là invariant tối quan trọng.

---

# 42. Alias lattice cho optimizer

Capability verifier có thể xuất:

```text
NO_ALIAS
MUST_ALIAS
PARTIAL_ALIAS
MAY_ALIAS
UNKNOWN
```

sang AliasInfo.

---

# 43. NO_ALIAS

Nếu:

```text
mut_view(a)
mut_view(b)
```

và proof:

```text
region(a) DISJOINT region(b)
```

compiler có thể tạo internal fact:

```text
NO_ALIAS
```

---

# 44. Đây chính là `restrict` tự động

Programmer không cần:

```c
restrict
```

Axiom compiler tự suy luận:

```text
verified capability disjointness
        ↓
internal NO_ALIAS
```

---

# 45. Nhưng không phải mọi view đều NoAlias

Ví dụ:

```text
view(x)
view(x)
```

→ MUST_ALIAS hoặc equivalent overlap.

Compiler không được biến thành NO_ALIAS chỉ vì cả hai là read-only.

---

# 46. READ capability và optimization

Nếu:

```text
view(x)
```

và compiler chứng minh không có WRITE capability/foreign effect vào region:

```text
load(x)
```

có thể:

- CSE;
- hoist;
- cache;
- eliminate duplicate loads.

---

# 47. WRITE invalidation

Sau:

```text
mut_view(x)
write(x)
```

các READ facts trên overlapping region phải bị invalidated.

---

# 48. Capability → MemorySSA

Capability facts có thể annotate MemorySSA:

```text
Load(C1.region)
Store(C2.region)
```

Alias verifier quyết định:

```text
may_alias?
```

---

# 49. Owner access

Một owner có thể trực tiếp:

```axiom
x.field
```

Compiler xem đây như capability nội bộ.

Ví dụ:

```text
read x.field
```

tạo semantic READ access.

```text
x.field = value
```

tạo WRITE access.

Programmer không phải viết view.

---

# 50. Đây là điểm giúp syntax đơn giản

Không cần:

```text
&x
&mut x
*deref
```

cho thao tác thông thường.

Compiler tự materialize capability trong MIR khi cần.

---

# 51. Indexing

```axiom
array[i]
```

compiler tạo region:

```text
array[element(i)]
```

Range analysis kiểm tra bounds.

Capability analysis kiểm tra overlap nếu access kéo dài.

---

# 52. Mutable indexing

```axiom
array[i] = value
```

semantic WRITE region:

```text
array[i]
```

Nếu loop:

```axiom
for i in 0..n {
    array[i] = ...
}
```

compiler có thể chứng minh từng iteration region disjoint khi cần.

---

# 53. Iterator

`iter()` tạo READ capability.

`iter_mut()` tạo WRITE capability.

Ví dụ:

```text
Vec
 ↓
iter_mut()
 ↓
Iterator<mut_view<T>>
```

---

# 54. Iterator invalidation

Nếu:

```axiom
let it = vec.iter_mut()
vec.push(x)
```

`push` có thể relocate storage.

Verifier phát hiện:

```text
active capability depends on vec storage
```

→ reject nếu relocation có thể xảy ra.

---

# 55. Reserve

```axiom
vec.reserve(n)
```

không tự đảm bảo mọi future operations sẽ không relocate nếu contract không nói như vậy.

---

# 56. Stable storage

Nếu container có explicit stable-address contract:

```text
StableStorage<T>
```

thì capability có thể survive operations theo contract.

Đây là library semantics, không phải Core pointer semantics.

---

# 57. String

```axiom
let s = String(...)
let v = s.as_str()
```

`v`:

```text
READ capability
region = UTF8 byte storage
```

Nếu:

```axiom
s.push(...)
```

có thể relocate.

Capability verifier phải biết `s.push()` invalidates/blocks dependent views.

---

# 58. String mutation

```axiom
let v = s.as_str()
s.push("abc")
use(v)
```

→ reject nếu mutation có thể invalidate view.

---

# 59. Zero-copy

Nếu:

```text
String → Str
```

thì không cần copy bytes.

Capability chỉ là metadata/access abstraction.

---

# 60. Capability and allocation

Capability không quyết định:

```text
heap vs stack
```

Nó chỉ quyết định:

```text
provenance + region + access + lifetime
```

---

# 61. Owner relocation

Nếu:

```text
Vec storage
```

có thể relocate, compiler xem relocation như operation:

```text
InvalidateDependentCapabilities(storage)
```

---

# 62. Allocation optimization

Nếu compiler chứng minh capability không escape:

```text
heap allocation
```

có thể được loại bỏ.

Nhưng capability semantics vẫn phải đúng trước optimization.

---

# 63. Closure capture

Closure giữ:

```text
view<T>
```

thì closure environment sở hữu capability.

Graph:

```text
Owner X
   ↑
Capability C
   ↑
Closure F
```

`F` không thể outlive X.

---

# 64. Closure escape

Nếu:

```axiom
return || inspect(view(x))
```

và x local:

```text
ClosureEscape = ReturnEscape
CapabilityEscape = ReturnEscape
OwnerLifetime < CapabilityLifetime
```

→ reject.

---

# 65. Closure move

Nếu closure capture owned value:

```text
move x
```

đây là Ownership Verifier.

Nếu capture view:

```text
capture capability
```

đây là Capability Verifier.

Hai hệ thống phối hợp.

---

# 66. Async view

```axiom
let v = view(x)
await foo()
use(v)
```

Không tự động reject mọi trường hợp.

Compiler phải hỏi:

```text
x storage có stable qua suspension?
v provenance có valid?
Future có thể migrate?
x có thể bị mutated/dropped?
```

---

# 67. Default rule

Nếu không có explicit storage/execution contract chứng minh an toàn:

```text
view/mut_view live across await
```

→ reject.

---

# 68. Owned value across await

```axiom
let x = make()
await foo()
use(x)
```

được phép nếu x có thể trở thành field của Future state.

Không cần Pin.

---

# 69. Stable address across await

Nếu một API yêu cầu địa chỉ ổn định:

```text
StableAddress<T>
```

thì storage contract phải bảo đảm điều đó.

Compiler không mặc định rằng mọi Future state có stable physical address.

---

# 70. Spawn

Một capability không thể tùy ý gửi sang thread/task khác.

Ví dụ:

```text
spawn(|| use(view(x)))
```

Nếu view chỉ thuộc stack của caller:

```text
reject
```

vì capability lifetime không đủ.

---

# 71. Send capability

Mặc định:

```text
view<T>
```

không đồng nghĩa `Send`.

Compiler cần xem:

```text
provenance
storage domain
execution domain
T
```

---

# 72. Share

Một READ capability có thể được share nếu underlying storage và type contract cho phép.

Ví dụ immutable shared object:

```text
Arc<T>
   ↓
view<T>
```

có thể được đọc concurrent.

---

# 73. Mutable capability qua thread

```text
mut_view<T>
```

không tự động `Send`.

Nếu transfer ownership của region:

```text
channel.send(owner)
```

thì ownership verifier xử lý.

---

# 74. Mutex

Mutex guard có thể cung cấp:

```text
mut_view<T>
```

trong thời gian guard sống.

Graph:

```text
Mutex<T>
   ↓ lock
Guard
   ↓
WRITE capability
```

Drop Guard:

```text
WRITE capability ends
unlock
```

---

# 75. Không có data race

Nếu safe code tạo:

```text
WRITE(C1)
WRITE(C2)
```

hoặc:

```text
READ(C1)
WRITE(C2)
```

với overlapping region mà không có synchronization:

```text
reject
```

---

# 76. Atomic exception

`Atomic<T>` không tạo ordinary `mut_view<T>`.

Atomic access dùng:

```text
AtomicLoad
AtomicStore
AtomicRMW
```

với memory ordering.

---

# 77. Volatile

Volatile access cũng không giống ordinary WRITE.

```text
VolatileLoad
VolatileStore
```

có effect semantics riêng.

---

# 78. FFI

Foreign function:

```text
extern "C"
```

nếu nhận raw pointer:

```text
*p
```

không tự tạo safe capability.

Safe wrapper:

```text
unsafe boundary
     ↓
contract
     ↓
MakeView / MakeMutView
     ↓
normal verifier
```

---

# 79. Unsafe capability creation

Ví dụ system API:

```text
unsafe fn from_raw(...)
```

có thể establish:

```text
provenance = trusted external storage
region = specified
access = READ
validity = contract
```

Nhưng compiler phải lưu fact này.

---

# 80. Unsafe không xóa capability

Sai:

```text
unsafe { ... }
```

→ reset verifier.

Đúng:

```text
unsafe operation
   ↓
trusted fact
   ↓
normal capability verification
```

---

# 81. Device/GPU

`DeviceView<T>` cùng triết lý:

```text
provenance
region
access
storage domain = Device
execution domain = GPU
```

Không được coi DeviceView là CPU pointer.

---

# 82. GPU mutable view

```text
DeviceMutView<T>
```

vẫn có WRITE exclusivity.

GPU threads có thể truy cập song song chỉ khi:

- disjoint;
- atomic;
- synchronization;
- explicit race-safe abstraction.

---

# 83. Host/device boundary

Capability không tự crossing:

```text
Host → Device
```

Phải có explicit transfer hoặc unified-memory contract.

---

# 84. Capability and RenderGraph

RenderGraph có thể dùng cùng model:

```text
Texture A
 ├── READ Pass1
 ├── WRITE Pass2
 └── READ Pass3
```

Compiler/library biết dependency.

Có thể suy ra barrier.

---

# 85. Capability and zero-copy networking

Network buffer:

```text
Owned NetworkBuffer
   ↓
view
   ↓
socket.send(...)
```

Nếu send async:

```text
buffer ownership/capability
```

phải sống đến completion event.

---

# 86. Capability and database page

```text
PageHandle
   ↓
PageView
```

PageView giữ dependency trên page pin/storage contract.

Eviction không thể xảy ra khi active mutable/read capability yêu cầu resident storage.

---

# 87. Capability and serialization

```text
decode_view(bytes)
```

trả capability vào byte storage.

Nếu bytes owner bị Drop:

```text
view invalid
```

→ verifier reject.

---

# 88. Capability and mmap

Memory-mapped region:

```text
MapHandle
   ↓
view<T>
```

unmap là:

```text
destroy provenance
```

Không thể unmap khi safe capability còn live.

---

# 89. Capability and process resources

Không chỉ memory.

Mô hình này có thể áp dụng semantic capability cho:

- file;
- socket;
- GPU resource;
- database page;
- mapped memory;
- external device.

Nhưng không biến tất cả thành một Core `Capability` type.

---

# 90. Compiler internal only

`Capability` là compiler semantic object.

Programmer không cần:

```text
CapabilityId
RegionId
ProvenanceId
```

---

# 91. Capability state

Đề xuất:

```text
CapabilityState {
    id: CapabilityId
    owner: OwnerId
    provenance: Provenance
    region: Region
    access: READ | WRITE
    start: ProgramPoint
    end: ProgramPoint
    escape: EscapeState
    storage: StorageDomain
    execution: ExecutionDomain
}
```

---

# 92. Region representation

Không nên lưu region như string:

```text
"user.field"
```

Mà:

```text
Region {
    base: Place
    projection: ProjectionSet
    range: optional RangeExpr
}
```

---

# 93. Projection

Ví dụ:

```text
x.a.b[3].field
```

có:

```text
Field(a)
Field(b)
Index(3)
Field(field)
```

---

# 94. Symbolic range

```text
buffer[i..j]
```

region chứa:

```text
Range {
    start = i
    end = j
}
```

Range analysis có thể refine.

---

# 95. Region normalization

Compiler cần canonicalize:

```text
x.a
x.a[0..n]
x.a.field
```

để relation solver hoạt động ổn định.

---

# 96. Region solver

API:

```text
RegionRelation relate(A, B)
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

Không được trả heuristic result.

---

# 97. Proof sources

Region solver có thể dùng:

```text
Type layout
Field identity
Range analysis
Pattern facts
Bounds facts
Constant evaluation
Comptime facts
Container contracts
```

---

# 98. Không dùng physical address

Hai object có địa chỉ:

```text
A = 0x1000
B = 0x2000
```

không phải cơ sở semantic để chứng minh lifetime/ownership.

Physical addresses chỉ xuất hiện trong unsafe/system layer.

---

# 99. Alias facts

Capability verifier xuất:

```text
AliasFact {
    region_a
    region_b
    relation
    proof
}
```

Ví dụ:

```text
x.left DISJOINT x.right
proof = StructFieldDisjoint
```

---

# 100. Proof provenance

Mỗi important fact nên có:

```text
Fact {
    proposition
    source
    confidence
    dependencies
}
```

Ví dụ:

```text
NO_ALIAS
source = field-disjointness
depends = TypeLayout(Point)
```

Điều này rất hữu ích cho `ax explain`.

---

# 101. Optimizer không tự tạo safety proof

Opt pass có thể dùng:

```text
NO_ALIAS
```

nhưng không tự biến:

```text
UNKNOWN
```

thành:

```text
NO_ALIAS
```

nếu không có semantic proof.

---

# 102. Capability verifier trước optimization

Pipeline:

```text
MIR
 ↓
Ownership
 ↓
Capability
 ↓
Effect
 ↓
Verified MIR
 ↓
AliasInfo
 ↓
Optimization
```

Không đảo thứ tự.

---

# 103. Optimization có thể refine lifetime

Sau Verified MIR:

```text
last_use analysis
```

có thể rút ngắn capability lifetime.

Nhưng phải preserve semantic validity.

---

# 104. Capability elimination

Nếu:

```text
view(x)
inspect(v)
```

không escape:

compiler có thể eliminate physical capability object hoàn toàn.

Thậm chí không có runtime representation.

---

# 105. Đây là zero-cost view

`view<T>` có thể compile thành:

```text
pointer + length
```

hoặc:

```text
pointer
```

hoặc hoàn toàn scalarized.

Semantics không phụ thuộc representation.

---

# 106. Mut_view

Tương tự:

```text
mut_view<T>
```

không bắt buộc có runtime object.

Compiler có thể chỉ sử dụng pointer/register metadata nội bộ.

---

# 107. No runtime borrow checker

Verifier chạy compile-time.

Binary không chứa:

```text
borrow table
ownership table
capability registry
```

trừ khi một library/system abstraction thực sự cần runtime metadata.

---

# 108. Capability lifetime và runtime cost

Mặc định:

```text
Capability creation
Capability end
```

không có runtime cost.

Chúng là semantic compiler facts.

---

# 109. Dynamic cases

Nếu runtime không chứng minh được disjointness:

Axiom không tự động thêm runtime check trong Core.

Có hai hướng:

```text
reject
```

hoặc library API explicit:

```text
split_checked(...)
```

trả Result.

---

# 110. Ví dụ split

```axiom
let (a, b) = buffer.split_at(i)?
```

Library contract có thể establish:

```text
a = [0,i)
b = [i,n)
```

Do đó:

```text
a DISJOINT b
```

sau khi thành công.

---

# 111. Đây là cách Axiom xử lý dynamic disjointness

Không cần syntax:

```text
unsafe borrow split
```

Library tạo semantic proof.

---

# 112. Parallel loops

Ví dụ:

```axiom
parallel_for(chunks, |chunk| {
    process(chunk)
})
```

Nếu `chunks` tạo disjoint views:

```text
chunk_i DISJOINT chunk_j
```

compiler/runtime có thể chạy song song an toàn.

---

# 113. Không mặc định parallel

Axiom không tự biến mọi loop thành parallel.

Parallelism là explicit abstraction.

Capability system chỉ cung cấp proof rằng parallel execution **có thể hợp lệ**.

---

# 114. Vectorization

Nếu loop:

```text
for i in 0..n {
    a[i] = b[i] + c[i]
}
```

compiler có thể chứng minh:

```text
write(a[i])
read(b[i])
read(c[i])
```

không overlap nếu provenance/region khác nhau.

→ vectorization.

---

# 115. Nếu có overlap

Ví dụ:

```text
a = b[1..]
b = b[..n-1]
```

compiler có thể phát hiện overlap.

Không được tự vectorize nếu thay đổi ordering semantics.

---

# 116. Capability và strict aliasing

Axiom không cần mô hình C strict-aliasing kiểu programmer phải hiểu.

Compiler có semantic region/provenance rõ hơn.

---

# 117. `reinterpret`

Unsafe:

```text
reinterpret<T>(p)
```

không tự tạo valid `view<T>`.

Cần proof:

- alignment;
- size;
- initialization;
- representation;
- provenance;
- validity.

---

# 118. Bitcast

`bitcast<T>` khác capability creation.

Nó thay đổi type interpretation theo representation rules.

Nếu kết quả tạo capability thì phải reverify.

---

# 119. Uninitialized memory

`Uninit<T>` không được tạo:

```text
view<T>
```

safe.

Phải chứng minh initialization trước.

---

# 120. Partial initialization

Ví dụ aggregate:

```text
x.a initialized
x.b uninitialized
```

`view(x)` toàn object:

```text
reject
```

nếu T yêu cầu fully initialized.

`view(x.a)`:

```text
OK
```

---

# 121. Field capability

Đây là một ưu điểm lớn của field-sensitive model:

```text
view(x.a)
```

không cần chờ:

```text
x.b
```

initialized.

---

# 122. But aggregate Drop

Nếu `x` có Drop, compiler phải đảm bảo partial initialization có valid cleanup strategy.

Nếu custom Drop không hỗ trợ partial initialization:

```text
reject
```

hoặc require full initialization before ownership enters normal state.

---

# 123. Capability and Drop

Invariant:

```text
LiveCapability(C, R)
+
Owner(X)
+
R ⊆ X
```

thì:

```text
Drop(X)
```

không hợp lệ.

---

# 124. Capability and relocation

Nếu:

```text
C → storage X
```

và operation:

```text
Relocate(X)
```

thì relocation chỉ hợp lệ nếu:

```text
C does not require stable address
```

hoặc capability contract được cập nhật an toàn.

---

# 125. Default assumption

Để đơn giản:

> **Active view blocks potentially invalidating relocation.**

Compiler có thể tối ưu nếu biết relocation không xảy ra.

---

# 126. Example

```axiom
let v = view(vec)
vec.push(x)
```

Nếu `push` may reallocate:

```text
reject
```

Nếu compiler chứng minh capacity đủ:

```text
no relocation
```

→ có thể accept.

---

# 127. Nhưng compiler không được dựa vào implementation accident

Nếu Vec API contract chỉ nói:

```text
push may relocate
```

thì một internal optimizer fact:

```text
current_capacity > len
```

có thể cho phép operation hiện tại không relocate.

Nhưng API semantics phải nhất quán với fact đó.

---

# 128. Capability invalidation API

Library operation có thể khai báo:

```text
Invalidates:
    READ_CAPABILITY(region)
    WRITE_CAPABILITY(region)
    STORAGE_ADDRESS
```

Compiler dùng contract này.

---

# 129. Collection contract

Ví dụ:

```text
Vec.push:
    may_reallocate = true
    invalidates_address_dependent_views = true
```

`Vec.set(i,x)`:

```text
may_reallocate = false
invalidates_existing_views = false
```

nếu contract bảo đảm.

---

# 130. Capability contract không phải macro

Nó là compiler-known semantic metadata.

Có thể được biểu diễn bằng trait/attribute/compiler intrinsic tùy subsystem.

---

# 131. Generic functions

Generic:

```axiom
fn process<T>(x: mut_view<T>)
```

không biết layout T.

Nhưng biết:

```text
WRITE capability
provenance
lifetime
```

đủ để verifier hoạt động.

---

# 132. Trait constraints

Một trait có thể yêu cầu:

```text
StableStorage
NoRelocation
```

hoặc library-specific semantic property.

Compiler phải tránh biến arbitrary trait method thành trusted no-alias nếu chưa có contract.

---

# 133. Trusted contracts

Một số low-level library primitive cần compiler trust.

Ví dụ:

```text
slice::split_at_mut
```

có thể là trusted intrinsic/verified implementation.

Contract phải được kiểm thử và có semantic specification.

---

# 134. Trusted không có nghĩa unsafe mọi nơi

Trusted implementation có thể nằm trong std/system library.

User vẫn sử dụng API safe.

---

# 135. Capability verifier và unsafe

Flow:

```text
unsafe raw pointer
       ↓
precondition contract
       ↓
safe capability
       ↓
ordinary verifier
```

Đây là mô hình thống nhất.

---

# 136. GPU

GPU capability:

```text
DeviceView<T>
DeviceMutView<T>
```

phải có:

```text
StorageDomain = Device
```

Không thể implicit convert:

```text
DeviceView<T> → view<T>
```

nếu không có unified-memory contract.

---

# 137. Async

Capability state across await phải được đưa vào Future layout:

```text
Future {
    owned_fields
    capability_dependencies
}
```

Nếu capability không hợp lệ qua suspension:

```text
reject
```

---

# 138. FFI

Foreign function contract có thể nói:

```text
borrowed for duration of call
```

hoặc:

```text
retains pointer after return
```

Nếu foreign API retain pointer:

```text
Escape = ExternalEscape
```

Compiler phải giữ owner/capability đủ lifetime.

---

# 139. External escape

Ví dụ C API:

```text
register_callback(ptr)
```

nếu C giữ `ptr`:

```text
CapabilityEscape = ExternalEscape
```

Safe wrapper phải cung cấp ownership/lifetime abstraction.

---

# 140. Không đoán FFI behavior

Nếu compiler không biết C function giữ pointer hay không:

```text
UNKNOWN
```

→ safe wrapper không được cấp capability semantics quá mạnh.

---

# 141. Capability error

Ví dụ:

```axiom
let v = view(x)
drop(x)
```

Diagnostic:

```text
ACAP-01:
cannot destroy owner while dependent view is active

owner:
    x

active capability:
    v

capability region:
    x.*
created:
    line 3

destruction:
    line 4
```

---

# 142. Alias error

```axiom
let a = mut_view(x)
let b = view(x)
```

Diagnostic:

```text
ACAP-02:
conflicting access capabilities

a:
    WRITE x.*

b:
    READ x.*

regions:
    OVERLAP
```

---

# 143. Unknown overlap

```axiom
let a = mut_view(buf[i..j])
let b = mut_view(buf[k..m])
```

Diagnostic:

```text
ACAP-03:
cannot prove regions are disjoint

required:
    DISJOINT

known:
    UNKNOWN
```

Đây là điểm quan trọng: compiler giải thích **thiếu proof gì**, thay vì nói chung chung “borrow error”.

---

# 144. Explain capability

API:

```text
ax explain capability v
```

có thể trả:

```text
Capability:
    access = WRITE
    provenance = buffer
    region = buffer[0..1024]

Created:
    foo.ax:18

Ends:
    foo.ax:27

Escape:
    NoEscape

Conflicts:
    none
```

---

# 145. AI context

AI có thể nhận structured facts:

```text
{
  "capability": "C17",
  "access": "WRITE",
  "region": "buffer[0..n]",
  "escape": "NoEscape",
  "conflicts": []
}
```

Không cần AI suy luận memory safety từ source text.

---

# 146. Compiler proof cache

Capability proofs có thể cache theo:

```text
FunctionFingerprint
+
TypeFingerprint
+
LayoutFingerprint
+
TargetSemanticFingerprint
```

---

# 147. Optimization independence

Capability correctness phải đúng ở:

```text
-O0
-O1
-O2
-O3
-Os
-LTO
-PGO
```

Không được:

```text
-O3 → suddenly safe
```

hoặc:

```text
-O0 → reject
-O3 → accept
```

nếu source semantics giống nhau.

---

# 148. Optimization benefit

Ngược lại:

```text
Verified capability facts
```

có thể làm:

```text
-O3
```

mạnh hơn C trong một số trường hợp vì compiler có semantic information rõ ràng mà programmer không phải viết `restrict`.

Đây là mục tiêu thiết kế, không phải blanket performance guarantee.

---

# 149. Runtime overhead

Default:

```text
view<T>
mut_view<T>
```

không có runtime borrow checking.

Không có:

```text
runtime borrow table
runtime lifetime object
runtime lock
```

trừ khi abstraction thực sự cần.

---

# 150. Capability model tổng hợp

```text
                    OWNER
                      │
                 provenance
                      │
                      ▼
                ┌───────────┐
                │ Capability│
                └─────┬─────┘
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
     Region          Access        Lifetime
       │              │              │
       │          READ / WRITE       │
       │              │              │
       └──────────────┼──────────────┘
                      ▼
                 Conflict?
                      │
             ┌────────┴────────┐
             │                 │
            NO                YES
             │                 │
             ▼                 ▼
         Verified            Reject
             │
             ▼
         Alias Facts
             │
             ▼
        Optimization
```

---

# 151. Frozen invariants

```text
ACAP-20
Every safe capability has explicit compiler-tracked provenance.

ACAP-21
Every safe capability has an explicit semantic region.

ACAP-22
Every safe capability has an explicit access mode.

ACAP-23
READ capabilities may coexist when provenance and validity permit.

ACAP-24
WRITE capabilities are exclusive over overlapping regions.

ACAP-25
READ + WRITE conflicts are rejected for overlapping regions.

ACAP-26
WRITE + WRITE conflicts are rejected for overlapping regions.

ACAP-27
view<T> is a READ capability, not a value-copy semantic.

ACAP-28
mut_view<T> is a WRITE capability and is nonduplicable.

ACAP-29
Capability duplication never duplicates ownership.

ACAP-30
Capability lifetime cannot exceed its provenance lifetime.

ACAP-31
Capability validity is independent of optimization level.

ACAP-32
Unknown region overlap is never treated as disjoint.

ACAP-33
Disjoint regions may carry independent mutable capabilities.

ACAP-34
Field-sensitive regions are supported.

ACAP-35
Range-sensitive regions are supported where provable.

ACAP-36
Returned views preserve provenance.

ACAP-37
Escaping views preserve their required owner/storage dependency.

ACAP-38
A local owner cannot be destroyed while a dependent capability escapes beyond it.

ACAP-39
A capability cannot outlive storage invalidation.

ACAP-40
Potentially relocating storage cannot relocate while dependent stable-address capabilities require the old address.

ACAP-41
Implicit owner→ephemeral-view conversion cannot create an escaping capability.

ACAP-42
Raw pointers do not automatically create safe capabilities.

ACAP-43
Unsafe operations may establish trusted capability preconditions.

ACAP-44
Safe verification resumes after unsafe capability creation.

ACAP-45
Capability facts may be exported to AliasInfo.

ACAP-46
Verified disjoint capability regions may become internal NO_ALIAS facts.

ACAP-47
UNKNOWN alias state never becomes NO_ALIAS without a new proof.

ACAP-48
Capability analysis is deterministic.

ACAP-49
Capability analysis is independent of optimization level.

ACAP-50
Capability analysis is shared across CPU, async, GPU, FFI and storage domains.

ACAP-51
GPU capabilities retain explicit storage/execution domains.

ACAP-52
Host/device capability conversion is never implicit without an explicit storage contract.

ACAP-53
Safe concurrent access requires valid synchronization or disjointness.

ACAP-54
Atomic access does not create ordinary mutable capabilities.

ACAP-55
Volatile access is distinct from ordinary capability access.

ACAP-56
FFI capabilities require explicit contracts when lifetime or retention crosses the boundary.

ACAP-57
Capability state is compiler semantic state by default and has no mandatory runtime representation.

ACAP-58
Capability proof failures produce structured diagnostics.

ACAP-59
Capability facts are explainable through CompilerDB/AXCP.

ACAP-60
Generated code must pass the same capability verifier.

ACAP-61
Comptime capability operations obey the same semantic safety rules.

ACAP-62
Capability elimination is permitted after semantic verification when no observable behavior is changed.

ACAP-63
Capability semantics do not imply heap allocation.

ACAP-64
Capability semantics do not imply reference counting.

ACAP-65
Capability semantics do not imply garbage collection.
```

---

# 152. Kết quả sau 226 + 227

Axiom hiện có một memory model khá khác biệt:

```text
                 Axiom Memory Safety
                         │
             ┌───────────┴───────────┐
             │                       │
        Ownership                Capability
             │                       │
       "Ai sở hữu?"             "Ai truy cập?"
             │                       │
    ┌────────┼────────┐        ┌─────┼─────┐
    │        │        │        │     │     │
   Move    Copy     Drop     READ  WRITE Region
                              │     │     │
                              └─────┼─────┘
                                    │
                               Alias Proof
                                    │
                                    ▼
                               Optimization
```

Và programmer-facing syntax vẫn rất đơn giản:

```axiom
fn process(data: Data) {
    inspect(data)
    modify(data)
}
```

Không cần:

```text
&T
&mut T
'a
'a: 'b
borrow(...)
deref(...)
```

nhưng compiler bên dưới vẫn có đủ thông tin để kiểm tra ownership, lifetime, aliasing và tạo `NO_ALIAS` facts.

---

# 153. Một điểm kiến trúc rất quan trọng

Sau task này có thể chốt một nguyên tắc lớn cho Axiom:

> **Axiom không loại bỏ ownership/borrowing; Axiom loại bỏ việc bắt programmer phải trực tiếp quản lý phần lớn bookkeeping của ownership/borrowing.**

Đây chính là hướng phù hợp với mục tiêu ban đầu của bạn:

**compiler có thể phức tạp hơn, nhưng ngôn ngữ không nhất thiết phải phức tạp theo.**

---

# BOOTSTRAP-228 — EFFECT SYSTEM & SIDE-EFFECT VERIFIER

Task tiếp theo sẽ nối ownership + capability với một vấn đề còn thiếu:

> **Compiler phải biết một function thực sự có thể làm gì đối với thế giới bên ngoài.**

Không chỉ:

```text
read/write memory
```

mà cả:

```text
Allocate
Deallocate
Drop
IO
File
Socket
Network
Atomic
Synchronize
Foreign
GPU
Panic
Unwind
Process
Environment
Comptime
```

Đặc biệt 228 sẽ quyết định **effect system của Axiom có được programmer viết ra hay để compiler tự suy luận**, và làm thế nào để effect information vừa đủ mạnh cho optimizer/LTO/AI tooling nhưng **không biến function signature thành một “bãi annotation” mới**.