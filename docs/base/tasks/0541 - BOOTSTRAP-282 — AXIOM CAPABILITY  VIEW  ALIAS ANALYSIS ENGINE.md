# BOOTSTRAP-282 — AXIOM CAPABILITY / VIEW / ALIAS ANALYSIS ENGINE
## FROZEN / COMPLETED

**Trạng thái:** `FROZEN`  
**Phụ thuộc:** `BOOTSTRAP-274`, `277`, `280`, `281`  
**Vai trò:** cầu nối giữa Ownership → Safety Verification → Alias Analysis → Optimization.

---

# 1. Mục tiêu

BOOTSTRAP-282 chịu trách nhiệm chứng minh:

- `view<T>` có provenance hợp lệ;
- `mut_view<T>` có quyền WRITE hợp lệ;
- capability không vượt quá lifetime của owner;
- capability không tồn tại sau khi owner bị Drop;
- READ/WRITE conflict được phát hiện;
- hai vùng nhớ có thực sự disjoint hay không;
- relocation có làm invalid capability hay không;
- capability qua function call có hợp lệ không;
- capability qua closure/async/thread có hợp lệ không;
- raw pointer chỉ trở thành safe capability khi có contract;
- các fact alias đủ mạnh để optimizer suy ra `NO_ALIAS`.

Nguyên tắc:

> **Programmer expresses access intent; compiler proves alias safety and derives machine-level alias facts.**

---

# 2. Vấn đề mà 282 giải quyết

Cần phân biệt bốn thứ:

```text
Ownership
    ↓
Ai sở hữu value?

Capability
    ↓
Ai được phép truy cập?

Region
    ↓
Truy cập vùng nào?

Alias
    ↓
Hai access có thể trỏ cùng storage không?
```

Không được gộp chúng thành một khái niệm.

---

# 3. Mô hình tổng thể

```text
                 Ownership
                     │
                     ↓
              Storage Identity
                     │
                     ↓
                 Provenance
                     │
             ┌───────┴────────┐
             ↓                ↓
         Capability         Region
             │                │
             └───────┬────────┘
                     ↓
               Alias Analysis
                     │
          ┌──────────┴──────────┐
          ↓                     ↓
       Safety                Optimizer
      Verification           NO_ALIAS
```

---

# 4. Capability là gì?

Capability là quyền truy cập semantic.

Một capability:

```text
Capability {
    id
    provenance
    region
    access
    lifetime
    storage_domain
    execution_domain
}
```

---

# 5. Access mode

Core chỉ cần hai safe access mode chính:

```text
READ
WRITE
```

MOVE và DROP không phải capability access thông thường; chúng là ownership operations.

Do đó:

```text
view<T>      → READ
mut_view<T>  → WRITE
```

---

# 6. `view<T>`

`view<T>`:

- không sở hữu dữ liệu;
- READ-only;
- có thể duplicate;
- không thể outlive provenance;
- không thể tạo WRITE capability;
- không thể dùng để mutate owner.

Ví dụ:

```text
fn print_name(name: view<String>)
```

nhiều caller có thể truyền view cùng một object.

---

# 7. `mut_view<T>`

`mut_view<T>`:

- không sở hữu dữ liệu;
- WRITE capability;
- không được duplicate;
- phải có exclusive access;
- không coexist với conflicting READ capability;
- không coexist với conflicting WRITE capability.

Ví dụ:

```text
fn normalize(x: mut_view<Data>)
```

Compiler phải chứng minh tại call site rằng WRITE capability hợp lệ.

---

# 8. Capability không phải reference

Axiom không dùng:

```text
&T
&mut T
'a
```

làm programmer-facing model.

Thay vào đó:

```text
view<T>
mut_view<T>
```

là semantic access types.

Compiler nội bộ có thể lower chúng thành pointer + metadata.

---

# 9. Representation không bị cố định

Một:

```text
view<T>
```

có thể được machine-lower thành:

```text
pointer
pointer + length
pointer + metadata
register pair
fat pointer
```

tùy type/target.

Không được đưa representation đó vào semantic identity.

---

# 10. Capability provenance

Mỗi safe capability phải có provenance:

```text
Provenance {
    owner
    storage_identity
    origin_region
}
```

Ví dụ:

```text
x
└── x.data
    └── view
```

view này biết nó xuất phát từ:

```text
x.data
```

không phải một địa chỉ tùy ý.

---

# 11. Capability lifetime

Một capability hợp lệ khi:

```text
owner alive
AND
storage valid
AND
region valid
AND
access permission valid
```

Do đó:

```text
drop(owner)
```

khi capability còn sống:

```text
REJECT
```

---

# 12. Lifetime không phải lexical scope

Compiler có thể kết thúc capability sau last use.

Ví dụ:

```text
let v = view(x)

read(v)

mutate(x)
```

Nếu compiler chứng minh `v` không còn được dùng sau `read(v)`:

```text
EndCapability(v)
```

có thể được đặt ngay sau last use.

Khi đó:

```text
mutate(x)
```

hợp lệ.

---

# 13. Đây là điểm khác biệt quan trọng

Không áp dụng máy móc:

```text
v declared in scope
→ v blocks mutation until scope end
```

Axiom sử dụng:

> **semantic last-use lifetime whenever safely provable.**

Điều này giảm restriction mà không cần programmer viết lifetime.

---

# 14. Capability state

```text
CapabilityState {
    capability_id
    provenance
    region
    access
    state
}
```

State:

```text
ACTIVE
ENDED
INVALID
```

`INVALID` là verifier state, không phải runtime state.

---

# 15. Region

Region mô tả vùng storage mà capability có quyền truy cập.

Ví dụ:

```text
struct Pair {
    left: Data
    right: Data
}
```

Compiler tạo:

```text
Pair
├── left
└── right
```

---

# 16. Region relation lattice

282 sử dụng:

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
x.left
x.right
```

→ `DISJOINT`.

```text
x
x.left
```

→ `CONTAINS`.

---

# 17. UNKNOWN cực kỳ quan trọng

Nếu compiler không chứng minh được:

```text
DISJOINT
```

thì **không được giả định disjoint**.

Ví dụ:

```text
fn f(a: mut_view<Data>, b: mut_view<Data>)
```

Nếu compiler không biết `a` và `b` có overlap:

```text
UNKNOWN
```

→ safe call bị reject.

---

# 18. Không có “best effort alias safety”

Không được:

```text
UNKNOWN → probably disjoint
```

vì điều đó phá vỡ memory safety.

Quy tắc:

```text
UNKNOWN
    ↓
cannot prove safety
    ↓
reject / require explicit safe abstraction
```

---

# 19. Region algebra

Compiler phải có các phép:

```text
intersects(A, B)
contains(A, B)
disjoint(A, B)
equivalent(A, B)
```

Kết quả:

```text
Proven
NotProven
Ambiguous
```

---

# 20. Access conflict matrix

| A | B | Conflict |
|---|---|---|
| READ | READ | Không |
| READ | WRITE | Có |
| WRITE | READ | Có |
| WRITE | WRITE | Có |

Ownership operations:

| Operation | Active READ | Active WRITE |
|---|---:|---:|
| READ | OK | Conflict |
| WRITE | Conflict | Conflict |
| MOVE owner | thường conflict | thường conflict |
| DROP owner | conflict | conflict |

---

# 21. READ + READ

```text
let a = view(x)
let b = view(x)

read(a)
read(b)
```

hợp lệ.

Có thể có nhiều READ capability cùng region.

---

# 22. WRITE độc quyền

```text
let a = mut_view(x)
let b = mut_view(x)
```

→ reject.

Vì:

```text
WRITE(x)
WRITE(x)
```

conflict.

---

# 23. READ + WRITE

```text
let r = view(x)
let w = mut_view(x)
```

→ reject nếu hai capability cùng overlap.

Nếu:

```text
r = view(x.left)
w = mut_view(x.right)
```

và compiler chứng minh:

```text
DISJOINT
```

→ hợp lệ.

---

# 24. Field-sensitive aliasing

Đây là một trong các tính năng quan trọng nhất của Axiom.

```text
fn f(x: mut_view<Pair>) {
    ...
}
```

Compiler có thể tạo:

```text
x.left
x.right
```

và biết:

```text
Region(x.left) ∩ Region(x.right) = ∅
```

nếu layout/semantic model đảm bảo.

---

# 25. Nested fields

```text
x.a.b
x.a.c
```

Compiler tiếp tục phân rã region:

```text
x
└── a
    ├── b
    └── c
```

→ `DISJOINT`.

---

# 26. Array ranges

Với:

```text
a[0..10]
a[20..30]
```

compiler có thể suy ra:

```text
DISJOINT
```

nếu index/range facts đủ mạnh.

Ví dụ:

```text
a[i]
a[j]
```

nếu:

```text
i != j
```

được proven:

```text
DISJOINT
```

---

# 27. Unknown indices

```text
a[i]
a[j]
```

nếu không biết quan hệ:

```text
UNKNOWN
```

Không được coi là disjoint.

---

# 28. Range analysis integration

282 lấy facts từ:

```text
RangeAnalysis
```

Ví dụ:

```text
0 <= i < 10
20 <= j < 30
```

→ region disjoint.

Do đó:

```text
mut_view(a[i])
mut_view(a[j])
```

có thể hợp lệ.

---

# 29. Alias lattice

Alias result:

```text
NO_ALIAS
MUST_ALIAS
PARTIAL_ALIAS
MAY_ALIAS
UNKNOWN
```

Đây là **optimizer-facing alias lattice**.

Không được nhầm với semantic region relation.

---

# 30. Region → Alias

Ví dụ:

```text
DISJOINT
```

có thể derive:

```text
NO_ALIAS
```

Nhưng:

```text
UNKNOWN
```

không bao giờ derive:

```text
NO_ALIAS
```

---

# 31. Capability-derived noalias

Nếu:

```text
a: mut_view<T>
b: mut_view<T>
```

và compiler chứng minh:

```text
region(a) DISJOINT region(b)
```

thì optimizer nhận:

```text
NO_ALIAS(a,b)
```

mà programmer không cần viết:

```text
restrict
```

---

# 32. Đây là mục tiêu quan trọng

Axiom có thể đạt:

```text
source simplicity
+
safe aliasing
+
optimizer-friendly noalias
```

mà không cần:

```text
lifetime syntax
borrow syntax
restrict syntax
```

---

# 33. Internal `NoAlias`

`NO_ALIAS` là compiler fact.

Không phải programmer-facing type.

Ví dụ:

```text
mut_view<A>
mut_view<B>
```

không có keyword:

```text
noalias
```

trừ system/FFI layer nếu cần.

---

# 34. Dynamic dispatch

Capability facts phải được conservative qua:

```text
dyn Trait
```

Nếu compiler không biết implementation cụ thể:

```text
alias effect = UNKNOWN
```

trừ khi trait contract cung cấp đủ guarantee.

---

# 35. Function summaries

Mỗi function cần alias/capability summary:

```text
CapabilitySummary {
    reads
    writes
    consumed
    returned_views
    retained_capabilities
    escaped_capabilities
    alias_relations
}
```

Ví dụ:

```text
fn sum(a: view<Array>, b: view<Array>)
```

có:

```text
reads(a)
reads(b)
retains = none
```

---

# 36. Mutable function summary

```text
fn add(
    a: view<f32>,
    b: view<f32>,
    out: mut_view<f32>
)
```

summary:

```text
READ  a
READ  b
WRITE out
```

Compiler phải chứng minh các conflict cần thiết.

---

# 37. Returned view

Ví dụ:

```text
fn name(x: view<User>) -> view<str>
```

returned capability:

```text
provenance = x
region = x.name
```

Không được biến thành:

```text
global
```

hay:

```text
independent owner
```

---

# 38. Capability retention

Một function có thể lưu capability:

```text
struct Context {
    buffer: view<u8>
}
```

Nếu storage contract cho phép.

Khi đó summary phải nói:

```text
retains argument capability
```

và EscapeAnalysis xử lý lifetime.

---

# 39. Không implicit escape

Một call:

```text
foo(view(x))
```

mặc định là ephemeral.

Compiler không được mặc định rằng:

```text
foo stores view forever
```

trừ khi function contract yêu cầu.

---

# 40. Nhưng compiler cũng không đoán nguy hiểm

Nếu callee ABI/FFI không rõ:

```text
unknown retention
```

→ safe code không được cho phép escape tùy tiện.

---

# 41. `view` storage

Nếu:

```text
let v = view(x)
```

thì `v` là capability value.

Nó có thể physically chỉ là:

```text
pointer
```

nhưng semantic state vẫn gồm:

```text
provenance
region
access
lifetime
```

---

# 42. Capability duplication

`view<T>` có thể duplicate:

```text
let a = view(x)
let b = a
```

semantic:

```text
READ capability #1
READ capability #2
```

Cả hai cùng provenance.

Không tạo ownership mới.

---

# 43. `mut_view` move

```text
let a = mut_view(x)
let b = a
```

semantic:

```text
a = Ended/Moved
b = Active WRITE
```

không duplicate WRITE capability.

---

# 44. Không Copy mut_view

`mut_view<T>` không implement semantic `Copy`.

Điều này đảm bảo:

```text
let a = mut_view(x)
let b = a
```

là transfer, không duplication.

---

# 45. Capability End

MIR:

```text
MakeView
MakeMutView
EndCapability
```

`EndCapability` là semantic event.

Optimizer có thể bỏ nếu capability representation không observable, nhưng semantic validity phải được giữ.

---

# 46. Capability and owner Move

Nếu:

```text
x: Owned
v: view(x)
```

thì:

```text
move(x)
```

chỉ hợp lệ nếu move không phá provenance contract.

Default:

```text
live capability + potentially relocating owner
→ reject
```

---

# 47. Capability and Drop

```text
drop(x)
```

requires:

```text
no live dependent capability
```

trừ explicit stable/external storage contract.

---

# 48. Capability and relocation

Ví dụ:

```text
Vec<T>
```

có thể relocate.

Nếu:

```text
v = view(vec)
```

thì:

```text
vec.push(...)
```

chỉ hợp lệ nếu:

```text
operation proven non-relocating
```

hoặc:

```text
v ended
```

---

# 49. Reserve không tạo stable address

```text
vec.reserve(1000)
```

không tự động nghĩa:

```text
stable_address_forever
```

vì ownership/storage abstraction không cam kết điều đó.

Stable address phải là contract riêng.

---

# 50. Box

`Box<T>` có thể có stable storage contract tùy API.

Ownership transfer:

```text
Box<T> → Box<T>
```

không nhất thiết move underlying object physically.

Capability engine chỉ quan tâm contract.

---

# 51. Handle

Logical Handle:

```text
Handle<T>
```

không phải capability trực tiếp.

Ví dụ:

```text
Handle<Entity>
```

có thể resolve thành storage tại runtime.

Sau resolve:

```text
handle
 ↓
lookup
 ↓
view/mut_view
```

capability engine chỉ kiểm tra capability được tạo bởi API.

---

# 52. Raw pointer

Raw pointer:

```text
*const T
*mut T
```

không có safe provenance tự động.

Integer:

```text
usize
```

không tự động trở thành valid pointer.

---

# 53. Raw pointer → view

Chỉ unsafe/system contract mới được:

```text
raw pointer
    ↓
trusted validation
    ↓
view<T>
```

Contract phải thiết lập:

```text
valid address
correct alignment
valid T representation
valid lifetime
valid provenance
access permission
```

---

# 54. Unsafe không phá capability engine

Không được:

```text
unsafe { everything_is_valid = true }
```

Thay vào đó:

```text
unsafe operation
      ↓
trusted facts
      ↓
normal capability verifier resumes
```

---

# 55. Integer pointer conversion

```text
let addr: usize = ...
let p = addr as *mut T
```

vẫn là raw pointer unsafe.

Compiler không suy luận:

```text
valid provenance
```

từ integer.

---

# 56. Volatile

Volatile access:

```text
volatile_load
volatile_store
```

không được tối ưu như ordinary load/store.

Capability vẫn có:

```text
READ / WRITE
```

nhưng effect system đánh dấu:

```text
VOLATILE
```

---

# 57. Atomic

Atomic access cũng giữ capability semantics.

```text
AtomicLoad
AtomicStore
AtomicRMW
```

nhưng không biến:

```text
Atomic<T>
```

thành ordinary:

```text
mut_view<T>
```

---

# 58. Thread transfer

Capability không được tự do vượt execution domain.

Ví dụ:

```text
view(x)
```

đưa vào worker phải thỏa:

```text
provenance storage
Send capability contract
```

Mặc định borrowed local capability không được gửi sang thread khác nếu owner/storage không có contract.

---

# 59. Send capability

Có thể có API:

```text
send(view)
```

nhưng compiler cần biết:

```text
view is valid in destination execution domain
```

Không chỉ:

```text
T: Send
```

vì capability itself cũng có lifetime/provenance.

---

# 60. Async

Capability qua `.await`:

```text
view(x)
await future
use(view)
```

mặc định:

```text
REJECT
```

vì execution/storage state có thể thay đổi.

Explicit contract mới cho phép.

---

# 61. Capability qua closure

Nếu closure không escape:

```text
use(|| read(v))
```

compiler có thể giữ capability local.

Nếu closure escape:

```text
return closure
```

phải phân tích:

```text
capability escape
owner lifetime
storage lifetime
```

---

# 62. Callback

Foreign callback:

```text
register(callback)
```

có thể giữ callback indefinitely.

Do đó borrowed capability capture:

```text
view(local)
```

không được phép escape nếu contract không đảm bảo lifetime.

---

# 63. Alias graph

Compiler xây:

```text
AliasGraph {
    nodes: CapabilityId / Place
    edges: AliasRelation
}
```

Ví dụ:

```text
a ──NO_ALIAS── b
a ──MAY_ALIAS─ c
d ──MUST_ALIAS─ e
```

---

# 64. Alias graph không phải ownership graph

Ownership:

```text
owner → moved-to
```

Capability:

```text
capability → provenance
```

Alias:

```text
region A ↔ region B
```

Ba graph riêng.

---

# 65. Capability graph

```text
CapabilityGraph {
    capability
    owner
    region
    parent_capability
    derived_region
    access
}
```

Ví dụ:

```text
owner x
 ├── view(x)
 │    └── view(x.name)
 └── mut_view(x.age)
```

---

# 66. Capability derivation

Từ:

```text
view(x)
```

có thể derive:

```text
view(x.field)
```

với:

```text
region(child) ⊆ region(parent)
access(child) <= access(parent)
```

Không thể derive WRITE từ READ.

---

# 67. Access monotonicity

Cho phép:

```text
WRITE capability
→ READ sub-capability
```

nếu semantics cho phép.

Không cho:

```text
READ
→ WRITE
```

mà không có explicit owner authorization.

---

# 68. Capability narrowing

```text
mut_view<User>
```

có thể tạo:

```text
mut_view<User.name>
```

vì region nhỏ hơn.

Nhưng phải đảm bảo:

```text
no conflicting active capability
```

---

# 69. Reborrowing

Axiom có thể có semantic equivalent của reborrow nhưng programmer không cần syntax riêng.

Ví dụ:

```text
fn process(x: mut_view<Data>) {
    helper(x.field)
    ...
}
```

Compiler tự tạo temporary sub-capability:

```text
x
 ↓
x.field WRITE
 ↓
End
 ↓
x WRITE resumes
```

---

# 70. Đây là cách giảm borrow-checker bureaucracy

Programmer không phải viết:

```text
&mut x.field
'a
```

Compiler quản lý capability subdivision.

---

# 71. Capability suspension

Trong nested call:

```text
outer(mut_view x)
    helper(mut_view x.field)
```

capability parent có thể tạm thời:

```text
SUSPENDED
```

trong vùng child:

```text
WRITE(x)
  ↓
SUSPENDED
WRITE(x.field)
  ↓
END
WRITE(x) resumes
```

Không phải runtime state bắt buộc.

---

# 72. Region containment

Nếu:

```text
A CONTAINS B
```

thì WRITE(B) có thể conflict với READ(A).

Ví dụ:

```text
view(user)
mut_view(user.name)
```

→ conflict.

---

# 73. Disjoint regions

Nếu:

```text
A DISJOINT B
```

thì:

```text
mut_view(A)
mut_view(B)
```

có thể coexist.

---

# 74. Same region

```text
view(x)
mut_view(x)
```

→ `SAME`.

→ conflict.

---

# 75. Partial overlap

Ví dụ:

```text
view(x[0..10])
mut_view(x[5..20])
```

→ `OVERLAPS`.

→ conflict.

---

# 76. Unknown

```text
view(a[i])
mut_view(a[j])
```

nếu không biết `i` và `j`:

```text
UNKNOWN
```

→ conflict trong safe mode.

---

# 77. Safe abstraction có thể establish disjointness

Thay vì annotation:

```text
restrict
```

Axiom library có thể cung cấp abstraction:

```text
split_at_mut(...)
```

semantic contract:

```text
return regions are DISJOINT
```

Compiler kiểm tra implementation của abstraction.

Caller nhận:

```text
mut_view<A>
mut_view<B>
```

với proven:

```text
DISJOINT
```

---

# 78. Đây là cơ chế quan trọng

Axiom không cần đưa hàng loạt alias annotation vào ngôn ngữ.

Thay vào đó:

```text
safe library abstraction
       ↓
formal semantic contract
       ↓
compiler-proven capability relation
       ↓
NO_ALIAS
```

---

# 79. Contract không phải lời nói suông

Một API không được chỉ viết:

```text
@noalias
```

và compiler tin mù quáng trong safe code.

Contract phải được:

```text
proven by implementation
```

hoặc:

```text
unsafe trusted boundary
```

---

# 80. Unsafe contract

System API có thể establish:

```text
DISJOINT(A,B)
```

nhưng phải đánh dấu trusted/unsafe boundary.

Sau đó downstream safe code được kiểm tra dựa trên fact đó.

---

# 81. FFI

C ABI function:

```text
extern fn foo(*mut T, *mut T)
```

mặc định:

```text
alias = UNKNOWN
```

Không tự suy ra noalias.

---

# 82. FFI noalias

Nếu C API thực sự yêu cầu noalias:

```text
@noalias
```

có thể tồn tại ở **FFI/system layer**.

Nhưng đây là explicit contract, không phải safe Core mặc định.

---

# 83. FFI contract

```text
FfiCapabilityContract {
    read_regions
    write_regions
    alias_constraints
    lifetime_constraints
    ownership_transfer
    retention
}
```

---

# 84. ABI boundary

Capability metadata không nhất thiết tồn tại trong machine ABI.

Ví dụ:

```text
view<T>
```

có thể ABI:

```text
ptr + len
```

Semantic provenance chỉ là compiler fact.

---

# 85. Dynamic library boundary

Khi compiler không có body của function:

```text
foo(view<T>)
```

phải có:

```text
.axmeta
```

hoặc FFI contract.

Nếu thiếu:

```text
conservative
```

---

# 86. Generic capability

Generic:

```text
fn process<T>(x: mut_view<T>)
```

không cần biết physical representation của T.

Capability semantics dựa trên:

```text
TypeId
Layout-independent region model
```

---

# 87. Generic associated regions

Trait/API có thể define semantic region operations.

Ví dụ conceptually:

```text
Collection<T>::split(...)
```

trả về hai capability có relation:

```text
DISJOINT
```

---

# 88. Alias analysis và optimizer

Sau verification:

```text
CapabilityFacts
     ↓
AliasFacts
     ↓
OptIR
```

Optimizer có thể dùng:

```text
NO_ALIAS
MUST_ALIAS
```

để:

```text
load/store forwarding
CSE
LICM
vectorization
store elimination
dependency reduction
```

---

# 89. NO_ALIAS là proof, không assumption

Invariant:

```text
NO_ALIAS
```

chỉ được tạo từ:

```text
proven DISJOINT
```

hoặc explicit trusted contract.

Không được tạo từ:

```text
heuristic
probability
optimizer guess
```

---

# 90. Alias facts không thay đổi semantics

Optimizer có thể sử dụng:

```text
NO_ALIAS
```

nhưng không được thay đổi capability semantics.

Nếu optimization transform tạo access mới:

```text
reverify legality
```

hoặc dùng transformation proof tương ứng.

---

# 91. Capability invalidation

Các operation có thể invalidate capability:

```text
Drop(owner)
relocate(storage)
deallocate(storage)
external invalidation
```

Compiler phải model chúng.

---

# 92. Relocation event

MIR/storage layer có thể biểu diễn:

```text
Relocate(storage)
```

hoặc implicit effect từ operation.

Capability engine kiểm tra:

```text
live capability
+
relocatable storage
=
invalid
```

---

# 93. Allocation replacement

Một operation:

```text
reallocate(buffer)
```

có effect:

```text
STORAGE_MAY_MOVE
```

Nếu view còn live:

```text
reject
```

hoặc API phải guarantee:

```text
NO_RELOCATE
```

---

# 94. Escape

Capability escape classes:

```text
NoEscape
ArgumentEscape
ReturnEscape
HeapEscape
ThreadEscape
ExternalEscape
UnknownEscape
```

282 tạo capability facts; EscapeAnalysis quyết định mức escape.

---

# 95. Capability lifetime inference

Compiler có thể tính:

```text
birth = MakeView
last_use = final access
end = EndCapability
```

Nếu không có explicit storage contract khác.

---

# 96. Explicit stored view

Khi programmer cố ý lưu:

```text
let context = Context {
    data: view(x)
}
```

compiler phải coi capability là persistent trong object.

Lifetime trở thành:

```text
Context lifetime
```

và owner phải sống đủ lâu.

---

# 97. Không cho self-invalidating structure

Ví dụ conceptually:

```text
struct Context {
    owner: Buffer
    view: view<u8>
}
```

nếu view trỏ vào `owner` bên trong chính struct và struct có thể relocate:

→ cần xử lý đặc biệt.

Mặc định không được giả định self-reference safe.

---

# 98. Self-referential storage

Core không cần hỗ trợ implicit self-referential types.

Muốn có:

```text
stable self-reference
```

phải dùng explicit stable-storage abstraction.

Điều này tránh `Pin<T>` trở thành Core complexity.

---

# 99. Async self-reference

Tương tự, compiler-generated Future không được tự động tạo self-referential safe capability.

Nếu state machine relocation có thể xảy ra:

```text
borrow across self-relocation
```

→ reject.

---

# 100. Capability + async contract

Chỉ cho phép capability qua await khi:

```text
owner storage stable
AND
capability remains valid
AND
execution-domain transition safe
```

được chứng minh.

---

# 101. Capability + GPU

Capability phải chứa:

```text
StorageDomain
ExecutionDomain
```

Ví dụ:

```text
DeviceView<f32>
```

không tự động trở thành:

```text
Host view<f32>
```

---

# 102. Host/device aliasing

Host và Device storage mặc định:

```text
different storage domains
```

không được suy ra alias chỉ vì cùng logical buffer.

Unified memory phải có explicit contract.

---

# 103. GPU mutable view

GPU:

```text
mut_view<T>
```

vẫn có exclusive semantics.

Nếu hai kernels cùng WRITE overlap mà không có synchronization contract:

```text
reject
```

hoặc explicit unsafe/atomic abstraction.

---

# 104. Atomic capability

Atomic operation không yêu cầu exclusive `mut_view` theo cách ordinary mutation yêu cầu, vì synchronization semantics khác.

Ví dụ:

```text
Atomic<T>
```

có:

```text
Atomic capability
```

nhưng không biến thành ordinary mutable capability.

---

# 105. Volatile capability

Volatile:

```text
READ/WRITE
```

nhưng effect:

```text
VOLATILE
```

Ngăn compiler coi nó như ordinary memory.

---

# 106. Capability effects

Mỗi capability operation có effect:

```text
READ
WRITE
CREATE
END
ESCAPE
RELOCATE
```

Effect system có thể consume những facts này.

---

# 107. Dataflow state

```text
CapabilityAnalysisState {
    active: CapabilitySet
    regions: RegionMap
    provenance: ProvenanceMap
    relations: RegionRelationMap
    escapes: EscapeMap
}
```

---

# 108. Join

Capability join phải conservative.

Ví dụ:

```text
cap A active
cap A inactive
```

→:

```text
MaybeActive
```

Nếu cần proof rằng capability tồn tại:

```text
reject / path refine
```

---

# 109. Capability set compression

Dùng:

```text
CapabilityId
RegionId
BitSet<CapabilityId>
```

thay vì object graph đầy đủ tại mọi block.

---

# 110. Region interning

Region expressions được canonicalize:

```text
RegionKey {
    root
    projections
    range
}
```

Hai expression semantic giống nhau:

```text
same RegionId
```

---

# 111. Region normalization

Ví dụ:

```text
x.a.b
x.a
```

normalize thành tree relation:

```text
x.a.b ⊂ x.a
```

giúp query containment nhanh.

---

# 112. Range region

Region có thể chứa:

```text
ArrayRange {
    base
    start
    end
}
```

với bounds là symbolic expressions.

Range solver cung cấp:

```text
disjoint
overlap
containment
```

---

# 113. Symbolic regions

Nếu:

```text
a[i]
a[i+1]
```

compiler có thể prove:

```text
DISJOINT
```

nếu element width/range semantics chứng minh không overlap.

Không cần runtime alias check trong trường hợp proof compile-time đủ mạnh.

---

# 114. Runtime-dependent alias

Nếu chỉ runtime mới biết:

```text
i == j?
```

compiler không được giả vờ biết.

Có thể:

1. reject safe operation;
2. dùng API có runtime validation;
3. dùng unsafe contract;
4. thiết kế abstraction chuyển proof thành runtime check.

---

# 115. Dynamic split abstraction

Ví dụ:

```text
split_at_mut(buffer, index)
```

có thể:

```text
runtime validate index
```

sau đó trả:

```text
mut_view<A>
mut_view<B>
```

với semantic contract:

```text
DISJOINT
```

Proof boundary nằm trong implementation.

---

# 116. Đây là hướng rất mạnh cho Axiom

Thay vì ép compiler chứng minh mọi thứ từ source:

```text
library abstractions
+
compiler-known semantic contracts
+
unsafe trusted kernels
```

cho phép xây API mạnh mà Core vẫn đơn giản.

---

# 117. Capability contract

Một contract có thể mô tả:

```text
CapabilityContract {
    input_regions
    output_regions
    region_relations
    access_modes
    lifetime_relation
    storage_requirements
    execution_requirements
}
```

---

# 118. Contract hierarchy

Ba mức:

```text
LEVEL 1
Compiler-proven

LEVEL 2
Library semantic contract proven by compiler

LEVEL 3
Unsafe trusted contract
```

Safe Core không có:

```text
unverified assertion
```

---

# 119. Capability contract fingerprint

Contract tham gia:

```text
semantic fingerprint
```

nếu thay đổi contract có thể thay đổi caller safety/codegen.

---

# 120. Query API

CompilerDB cung cấp:

```text
capability_state(function, block, capability)

capability_provenance(capability)

capability_region(capability)

region_relation(a, b)

alias_relation(a, b)

active_capabilities(function, location)

why_capability_invalid(...)

why_regions_not_disjoint(...)

noalias_facts(function)
```

---

# 121. AI diagnostics

AI có thể hỏi:

```text
why can these two views not coexist?
```

Compiler trả structured answer:

```text
{
  "left": "x[0..10]",
  "right": "x[i..i+20]",
  "relation": "UNKNOWN",
  "reason": [
      "i is not range-constrained"
  ],
  "possible_resolution": [
      "prove range",
      "use checked split abstraction",
      "move operation into unsafe boundary"
  ]
}
```

---

# 122. Không chỉ báo lỗi

Compiler nên giải thích:

```text
known
proven
unknown
conflicting
```

Đây là phần quan trọng cho AI-generated code.

---

# 123. Incremental

Nếu thay đổi:

```text
range proof i
```

chỉ invalidate:

```text
RegionRelation(i, ...)
AliasFacts(dependent)
```

không cần chạy lại toàn bộ compiler.

---

# 124. Parallel

Các function độc lập:

```text
f1
f2
f3
f4
```

có thể phân tích song song.

Region interning/query infrastructure phải thread-safe nhưng deterministic.

---

# 125. Cache

Cache key cần chứa:

```text
MIR fingerprint
Type fingerprint
Capability contract fingerprint
Range facts fingerprint
Target/storage domain
Compiler semantic version
```

---

# 126. Không cache theo physical pointer

Không dùng:

```text
memory address of compiler object
```

làm semantic cache identity.

Theo BOOTSTRAP-274:

```text
semantic identity != physical address
```

---

# 127. Ownership integration

282 query:

```text
is_owner_alive(provenance)
```

từ 281.

Nếu:

```text
owner = Moved
```

capability dependent phải invalid.

---

# 128. Drop integration

281 tạo:

```text
Drop(owner)
```

282 phải xác nhận:

```text
dependent capabilities = none
```

trước khi Drop được Verified.

---

# 129. Escape integration

282 xuất:

```text
capability escape facts
```

EscapeAnalysis dùng để quyết định:

```text
stack
heap
stable storage
caller allocation
```

---

# 130. Optimization integration

282 xuất:

```text
NO_ALIAS
MUST_ALIAS
READ_ONLY
WRITE_EXCLUSIVE
NO_ESCAPE
STABLE_REGION
```

cho OptIR.

---

# 131. Không xuất UNKNOWN thành optimizer assumption

Optimizer có thể nhận:

```text
UNKNOWN
```

nhưng không được biến nó thành:

```text
NO_ALIAS
```

---

# 132. Safe mode

Trong safe Core:

```text
unknown overlap
→ reject conflicting operation
```

Trong unsafe:

```text
unknown overlap
→ allowed only within unsafe operation/contract
```

Nhưng downstream safe capability vẫn phải có proof.

---

# 133. Unsafe raw pointer aliasing

Hai raw pointers có thể alias tùy ý trong unsafe.

Nhưng khi chuyển thành:

```text
mut_view<T>
```

compiler cần contract:

```text
exclusive region
```

Nếu không:

```text
cannot construct safe mut_view
```

---

# 134. Unsafe doesn't poison entire function

Ví dụ:

```text
unsafe {
    raw pointer manipulation
}

safe_operation(x)
```

Không biến toàn bộ function thành “unsafe mode”.

Verifier trở lại normal semantics sau boundary.

---

# 135. Capability verifier boundary

```text
Raw Pointer
     ↓
unsafe validation
     ↓
trusted capability creation
     ↓
Capability verifier
     ↓
safe code
```

---

# 136. Compiler implementation

Module:

```text id="m4fqk5"
compiler/
└── analysis/
    └── capability/
        ├── mod.ax
        ├── capability.ax
        ├── capability_id.ax
        ├── access.ax
        ├── provenance.ax
        ├── region.ax
        ├── region_id.ax
        ├── region_tree.ax
        ├── relation.ax
        ├── relation_solver.ax
        ├── capability_state.ax
        ├── capability_lifetime.ax
        ├── capability_derive.ax
        ├── capability_end.ax
        ├── view.ax
        ├── mut_view.ax
        ├── alias.ax
        ├── alias_graph.ax
        ├── noalias.ax
        ├── range_integration.ax
        ├── ownership_integration.ax
        ├── escape_integration.ax
        ├── async.ax
        ├── concurrency.ax
        ├── gpu.ax
        ├── ffi.ax
        ├── unsafe.ax
        ├── contract.ax
        ├── summary.ax
        ├── diagnostics.ax
        ├── query.ax
        └── tests/
```

---

# 137. Implementation order

```text
01  CapabilityId
02  AccessMode
03  Provenance
04  RegionId
05  RegionKey
06  Region interning
07  Region tree
08  Region containment
09  Region relation
10  Capability state
11  MakeView
12  MakeMutView
13  EndCapability
14  capability lifetime
15  field-sensitive regions
16  array ranges
17  range integration
18  capability joins
19  alias lattice
20  alias graph
21  noalias derivation
22  ownership integration
23  Drop integration
24  relocation integration
25  function summaries
26  generic summaries
27  closure
28  async
29  Send/Share
30  GPU
31  FFI
32  unsafe contracts
33  escape integration
34  CompilerDB queries
35  incremental cache
36  parallel analysis
37  diagnostics
38  property tests
39  fuzzing
40  Verified-MIR integration
```

---

# 138. Test matrix

## Basic

```text
read/read
read/write
write/write
same region
disjoint fields
nested fields
```

## Lifetime

```text
owner drop with view
owner move with view
view last-use
view return
view escape
```

## Region

```text
same
contains
contained_by
disjoint
overlap
unknown
```

## Arrays

```text
constant indices
known ranges
symbolic ranges
overlap ranges
unknown indices
```

## Storage

```text
Vec relocation
Box
stable storage
arena
pool
static
TLS
device
external
```

---

# 139. Adversarial tests

Bắt buộc:

```text
deep nested regions
10000 fields
large arrays
symbolic index expressions
deep CFG
nested mutable views
closure escape chains
async suspension chains
recursive generic functions
FFI boundaries
unsafe capability construction
GPU host/device transitions
```

---

# 140. Soundness properties

Property-based tests:

```text
DISJOINT → no conflicting safe access
UNKNOWN → never upgraded to DISJOINT without proof
READ + READ → valid
READ + WRITE overlap → invalid
WRITE + WRITE overlap → invalid
owner Drop + live capability → invalid
capability after owner destruction → invalid
mut_view duplication → invalid
raw pointer → safe capability without contract → invalid
```

---

# 141. Optimizer properties

```text
Proven DISJOINT → may derive NO_ALIAS
UNKNOWN → cannot derive NO_ALIAS
NO_ALIAS derivation does not depend on -O level
Alias facts remain semantically valid after optimization
```

---

# 142. Determinism

Hai compiler execution:

```text
workers = 1
workers = 32
```

phải tạo cùng:

```text
region relations
capability validity
alias facts
diagnostics
semantic fingerprints
```

---

# 143. Frozen Invariants — ACAPENG

```text
ACAPENG-20
Capability analysis operates on semantic MIR facts.

ACAPENG-21
A capability has provenance, region, access mode and validity information.

ACAPENG-22
view<T> represents non-owning READ capability.

ACAPENG-23
mut_view<T> represents non-owning exclusive WRITE capability.

ACAPENG-24
view<T> does not transfer ownership.

ACAPENG-25
mut_view<T> does not transfer ownership of its referent.

ACAPENG-26
mut_view<T> cannot be semantically duplicated.

ACAPENG-27
view<T> may be duplicated as independent READ capabilities.

ACAPENG-28
READ/READ access may coexist.

ACAPENG-29
Overlapping READ/WRITE access conflicts.

ACAPENG-30
Overlapping WRITE/WRITE access conflicts.

ACAPENG-31
Capability validity cannot exceed provenance validity.

ACAPENG-32
Owner destruction with a live dependent capability is invalid.

ACAPENG-33
Owner relocation that invalidates a live capability is invalid.

ACAPENG-34
Stable-address behavior requires an explicit storage contract.

ACAPENG-35
Capability lifetime may end at semantic last use when proven safe.

ACAPENG-36
Lexical scope does not inherently determine capability lifetime.

ACAPENG-37
Capability lifetime inference must preserve observable semantics.

ACAPENG-38
Region identity is distinct from physical memory address.

ACAPENG-39
Region relations are semantic facts.

ACAPENG-40
The region relation set includes DISJOINT, SAME, CONTAINS, CONTAINED_BY, OVERLAPS and UNKNOWN.

ACAPENG-41
UNKNOWN region relation must never be treated as DISJOINT without additional proof.

ACAPENG-42
Field-sensitive regions are supported.

ACAPENG-43
Nested field regions are supported.

ACAPENG-44
Array/range regions may participate in alias proofs.

ACAPENG-45
Range facts may establish region disjointness.

ACAPENG-46
Symbolic alias relations must be proven, not guessed.

ACAPENG-47
Capability derivation may narrow a region.

ACAPENG-48
Capability derivation cannot increase READ permission to WRITE.

ACAPENG-49
A WRITE capability may produce narrower access capabilities only under valid rules.

ACAPENG-50
Parent capabilities may be temporarily suspended during exclusive sub-capability use.

ACAPENG-51
Capability suspension does not create runtime ownership state by itself.

ACAPENG-52
Returned capabilities preserve provenance.

ACAPENG-53
Escaping capabilities require valid storage/lifetime contracts.

ACAPENG-54
A stored capability extends the required lifetime of its provenance.

ACAPENG-55
Closure captures participate in capability lifetime analysis.

ACAPENG-56
Async suspension participates in capability lifetime analysis.

ACAPENG-57
Borrowed capabilities cannot cross execution domains without a valid contract.

ACAPENG-58
GPU capabilities include explicit storage/execution domain information.

ACAPENG-59
Host and device capabilities do not implicitly alias.

ACAPENG-60
Unified storage requires an explicit semantic contract.

ACAPENG-61
Atomic access is distinct from ordinary mutable capability semantics.

ACAPENG-62
Volatile access is distinct from ordinary memory access semantics.

ACAPENG-63
Raw pointers do not automatically constitute safe capabilities.

ACAPENG-64
Integer values do not automatically establish pointer provenance.

ACAPENG-65
Raw pointer to safe capability conversion requires a trusted contract.

ACAPENG-66
Unsafe boundaries do not disable subsequent capability verification.

ACAPENG-67
FFI capability behavior is conservative unless an explicit contract exists.

ACAPENG-68
FFI alias guarantees require explicit representation in the FFI contract.

ACAPENG-69
Function capability summaries explicitly describe reads, writes, retention and returned capabilities.

ACAPENG-70
Capability summaries participate in incremental semantic dependency tracking.

ACAPENG-71
Capability facts are distinct from ownership facts.

ACAPENG-72
Capability facts are distinct from physical representation.

ACAPENG-73
Capability facts are distinct from ABI representation.

ACAPENG-74
Alias analysis is a consumer of proven capability/region facts.

ACAPENG-75
NO_ALIAS is a proof-derived compiler fact.

ACAPENG-76
NO_ALIAS may be derived from proven DISJOINT regions.

ACAPENG-77
UNKNOWN aliasing must never produce NO_ALIAS.

ACAPENG-78
Optimizer heuristics cannot establish safe aliasing facts.

ACAPENG-79
Alias facts cannot weaken memory safety.

ACAPENG-80
Capability verification is independent of optimization level.

ACAPENG-81
Capability verification is deterministic.

ACAPENG-82
Parallel capability analysis must equal serial semantic results.

ACAPENG-83
Capability analysis is dependency-driven under CompilerDB.

ACAPENG-84
Region identities are canonicalized and interned where practical.

ACAPENG-85
Capability identities use typed compiler identifiers.

ACAPENG-86
Capability state does not depend on compiler object memory addresses.

ACAPENG-87
Capability diagnostics preserve source provenance.

ACAPENG-88
Capability diagnostics expose region/provenance causes.

ACAPENG-89
Capability facts are available to AI tooling through structured CompilerDB queries.

ACAPENG-90
AI-generated capability assertions cannot bypass verification.

ACAPENG-91
Safe library abstractions may establish proven region relations through verified implementations.

ACAPENG-92
Trusted unsafe contracts may establish capability preconditions only at explicit unsafe boundaries.

ACAPENG-93
Trusted contracts must not silently alter ordinary safe semantics.

ACAPENG-94
Capability invalidation is explicit in semantic analysis.

ACAPENG-95
Relocation effects participate in capability validity.

ACAPENG-96
Drop verification consumes capability liveness facts.

ACAPENG-97
Ownership verification consumes capability conflict facts.

ACAPENG-98
Escape analysis consumes capability escape facts.

ACAPENG-99
Optimization consumes capability-derived alias facts without redefining capability semantics.

ACAPENG-100
Only capability-verified MIR may enter the optimization pipeline.
```

---

# 144. Kết quả sau BOOTSTRAP-282

Axiom hiện có ba lớp rất rõ:

```text
                 VALUE
                   │
                   ↓
             ┌───────────┐
             │ Ownership │
             └─────┬─────┘
                   │
                   ↓
             ┌───────────┐
             │Capability │
             └─────┬─────┘
                   │
                   ↓
             ┌───────────┐
             │   Alias   │
             └─────┬─────┘
                   │
                   ↓
             ┌───────────┐
             │ Optimizer │
             └───────────┘
```

Và đây chính là điểm mà thiết kế Axiom bắt đầu có lợi thế rất rõ:

```text
Programmer:
    view(x)
    mut_view(x)

Compiler:
    provenance
    lifetime
    region
    overlap
    alias
    noalias
    relocation
    escape
    synchronization
```

Programmer **không cần viết**:

```text
&x
&mut x
'a
'b
restrict
noalias
lifetime constraints
```

nhưng optimizer vẫn có thể nhận được:

```text
NO_ALIAS
READ_ONLY
WRITE_EXCLUSIVE
NON_ESCAPING
STABLE_REGION
```

khi compiler thực sự chứng minh được.

Đây là nền tảng quan trọng để Axiom vừa **dễ viết hơn C++/Rust ở tầng ownership**, vừa giữ được khả năng tối ưu rất sâu.

**BOOTSTRAP-282 — FROZEN.**

### Tiếp theo trong chuỗi kiến trúc

**BOOTSTRAP-283 — AXIOM EFFECT SYSTEM & SIDE-EFFECT ANALYSIS ENGINE**

Sẽ khóa cách compiler biết chính xác một function có thể:

```text
READ
WRITE
ALLOCATE
DEALLOCATE
DROP
PANIC
IO
ATOMIC
VOLATILE
SYNCHRONIZE
BLOCK
SPAWN
AWAIT
FOREIGN
GPU
```

và dùng các effect này để phục vụ **DCE, CSE, LICM, inlining, async lowering, parallelization, vectorization và binary-size optimization** mà không cần biến effect system thành một đống annotation phiền phức cho programmer.