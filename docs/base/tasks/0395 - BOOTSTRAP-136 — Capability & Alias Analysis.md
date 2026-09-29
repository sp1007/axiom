# BOOTSTRAP-136 — Capability & Alias Analysis

**Trạng thái: FROZEN / COMPLETED**

Đây là lớp nối trực tiếp giữa **memory safety** và **performance** của Axiom.

Mục tiêu:

> Compiler tự suy luận alias/no-alias từ ownership + capability + region + escape facts, thay vì bắt programmer viết `restrict`, lifetime annotation hoặc alias annotation trong phần lớn trường hợp.

---

# 1. Vị trí

```text
MIR
 │
 ▼
Ownership Verification
 │
 ▼
Capability Verification
 │
 ▼
Alias & Region Analysis
 │
 ├── Provenance
 ├── Region
 ├── Overlap
 ├── Mutation
 ├── Escape
 ├── Relocation
 └── Synchronization
 │
 ▼
AliasInfo
 │
 ▼
OptIR
```

---

# 2. Alias không phải một boolean

Không dùng:

```text
alias = true/false
```

Axiom dùng lattice:

```text
NO_ALIAS
MUST_ALIAS
PARTIAL_ALIAS
MAY_ALIAS
UNKNOWN
```

---

# 3. Ý nghĩa

### `NO_ALIAS`

Compiler đã chứng minh hai access region không thể overlap.

### `MUST_ALIAS`

Hai access cùng biểu diễn một region.

### `PARTIAL_ALIAS`

Một phần overlap.

### `MAY_ALIAS`

Có thể overlap.

### `UNKNOWN`

Compiler không đủ thông tin.

Điểm quan trọng:

> **`UNKNOWN` tuyệt đối không được suy thành `NO_ALIAS`.**

---

# 4. Region

Mọi capability có:

```text
RegionId
```

Region không nhất thiết tương ứng một allocation.

Ví dụ:

```ax
mut_view(user.name)
mut_view(user.address)
```

có:

```text
R_name
R_address
```

và:

```text
R_name DISJOINT R_address
```

---

# 5. Region relation

Frozen relations:

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
user
├── name
└── address
```

thì:

```text
Region(user.name)
    DISJOINT
Region(user.address)
```

---

# 6. Region hierarchy

Region có thể tạo tree:

```text
R_user
├── R_id
├── R_name
└── R_address
    ├── R_city
    └── R_country
```

Do đó compiler biết:

```text
R_city CONTAINED_BY R_address
R_address CONTAINED_BY R_user
```

---

# 7. Region không phải lifetime

Hai khái niệm:

```text
Region = vùng dữ liệu
Lifetime = thời gian capability hợp lệ
```

Ví dụ:

```text
R_name
lifetime = [bb2, bb7]
```

---

# 8. Provenance

Capability:

```text
Capability {
    provenance
    region
    access
    lifetime
}
```

Provenance trả lời:

> Capability này bắt nguồn từ storage/owner nào?

---

# 9. Provenance chain

Ví dụ:

```ax
let user = make_user();
let name = view(user.name);
```

compiler có:

```text
user
 ↓
user.name
 ↓
view
```

Capability provenance:

```text
name_view → user.name → user
```

---

# 10. Raw pointer provenance

Raw pointer:

```text
*mut T
```

không tự có safe provenance.

Một integer:

```text
u64
```

cũng không tự biến thành valid pointer.

---

# 11. Pointer equality không đủ để chứng minh alias

Hai pointer có cùng numeric address trong một context không tự động cung cấp toàn bộ semantic provenance.

Compiler phải phân biệt:

```text
machine address
```

và:

```text
safe memory capability
```

---

# 12. `mut_view` tạo alias restriction

Nếu:

```ax
let a = mut_view(x);
let b = mut_view(x);
```

thì:

```text
R_a SAME R_b
```

→ conflict.

Nếu:

```ax
let a = mut_view(x.left);
let b = mut_view(x.right);
```

và fields disjoint:

```text
R_a DISJOINT R_b
```

→ hợp lệ.

---

# 13. READ + READ

```text
view(x)
view(x)
```

có thể cùng tồn tại:

```text
READ + READ = allowed
```

nếu không có mutation/invalidating event.

---

# 14. READ + WRITE

```text
view(x)
mut_view(x)
```

→ conflict nếu overlap.

---

# 15. WRITE + WRITE

```text
mut_view(x)
mut_view(x)
```

→ conflict nếu overlap.

---

# 16. Partial overlap

Ví dụ:

```ax
let a = mut_view(buffer[0..100]);
let b = mut_view(buffer[50..150]);
```

Compiler chứng minh:

```text
[0,100)
overlap
[50,150)
```

→ conflict.

---

# 17. Adjacent range

```text
[0,100)
[100,200)
```

→:

```text
DISJOINT
```

Không phải overlap.

---

# 18. Unknown runtime index

```ax
let a = mut_view(buffer[i..i+10]);
let b = mut_view(buffer[j..j+10]);
```

nếu không biết quan hệ `i` và `j`:

```text
UNKNOWN
```

→ không được coi là disjoint.

---

# 19. Range reasoning

Compiler có thể dùng `RangeInfo`:

```text
i ∈ [0,10]
j ∈ [20,30]
```

để chứng minh:

```text
i ≠ j
```

và có thể chứng minh disjoint nếu bounds đủ mạnh.

---

# 20. Alias + bounds analysis

Do đó:

```text
AliasAnalysis
       ↑
RangeAnalysis
```

có dependency.

Nhưng:

```text
RangeAnalysis
```

không được tự tạo ownership proof.

---

# 21. Field-sensitive aliasing

Thay vì:

```text
user MAY_ALIAS user
```

compiler phân biệt:

```text
user.id
user.name
user.address
```

Điều này cho phép:

```text
mutate user.id
```

mà không invalidate read-only access tới:

```text
user.name
```

nếu semantics chứng minh fields độc lập.

---

# 22. Array aliasing

Fixed array:

```text
[a, b, c]
```

có region:

```text
R[0]
R[1]
R[2]
```

Compiler có thể chứng minh:

```text
R[0] DISJOINT R[1]
```

---

# 23. Dynamic arrays

`Vec<T>`:

```text
Vec<T>
```

có:

```text
storage
length
capacity
```

Region của elements:

```text
R_elements
```

---

# 24. Vec relocation

Một mutation như:

```ax
vec.push(x);
```

có thể reallocate.

Nếu:

```text
active view(vec)
```

đang tồn tại và relocation có thể xảy ra:

```text
reject
```

hoặc API phải cung cấp contract chứng minh operation không invalidating view.

---

# 25. `reserve` không phải stable address

Ngay cả:

```ax
vec.reserve(100);
```

không tự tạo vĩnh viễn:

```text
StableAddress
```

Compiler chỉ có thể dùng thông tin mà API contract thực sự đảm bảo.

---

# 26. Allocation identity

Mỗi storage instance semantic có identity:

```text
AllocationIdentity
```

Ví dụ:

```text
Box<T>
Arena allocation
Static
TLS
DeviceBuffer
External memory
```

Alias analysis không được nhầm:

```text
same type
```

với:

```text
same allocation
```

---

# 27. Distinct allocations

Nếu:

```ax
let a = Box::new(x);
let b = Box::new(y);
```

và compiler biết chúng là hai allocations khác nhau:

```text
allocation(a) != allocation(b)
```

thì các regions mặc định có thể được chứng minh disjoint, trừ trường hợp abstraction explicitly shares storage.

---

# 28. `Arc`

Với:

```ax
Arc<T>
```

nhiều handles có thể trỏ tới cùng logical allocation:

```text
h1 ─┐
h2 ─┼──> allocation A
h3 ─┘
```

Do đó:

```text
h1.T
h2.T
```

có thể:

```text
MUST_ALIAS
```

về storage region.

---

# 29. Arc không cho mutable alias tự do

`Arc<T>` chỉ giải quyết shared ownership.

Nếu cần mutation:

```text
Arc<Mutex<T>>
Arc<RwLock<T>>
Arc<Atomic<T>>
```

verifier sử dụng synchronization contract của abstraction.

---

# 30. Rc

`Rc<T>` có shared ownership nhưng không được Send.

Do đó:

```text
Rc<T>
```

không tự nhiên tạo cross-thread alias.

---

# 31. Handle

Handle:

```text
EntityId
```

không phải memory capability.

Ví dụ:

```ax
let id = entity.id;
```

hai handle cùng value không cho compiler kết luận:

```text
same live object
```

trừ khi API semantics định nghĩa điều đó.

---

# 32. Logical identity vs storage identity

Axiom giữ ba lớp:

```text
Value Identity
Storage Identity
Logical Identity
```

Alias analysis chủ yếu quan tâm:

```text
Storage Identity
```

trong khi application semantics có thể dùng:

```text
Logical Identity
```

---

# 33. Closure capture

Closure:

```ax
let f = || use(x);
```

compiler phải biết capture là:

```text
MOVE
COPY
READ capability
WRITE capability
```

Alias information của closure environment phụ thuộc capture mode.

---

# 34. Closure escape

Nếu closure không escape:

```text
NoEscape
```

compiler có thể scalarize environment.

Nếu:

```text
ThreadEscape
```

các captured capabilities/values phải thỏa concurrency rules.

---

# 35. Function call

Call là một alias barrier **chỉ khi cần thiết**.

Không mặc định:

```text
call foo()
→ invalidate everything
```

Axiom muốn phân tích effect/contract.

---

# 36. Function effect summary

Compiler tạo summary:

```text
FunctionEffect {
    Reads
    Writes
    Allocates
    Deallocates
    Synchronizes
    MayEscape
    Foreign
}
```

Ví dụ:

```text
foo(view<A>)
```

có thể chỉ:

```text
READ A
```

---

# 37. No hidden `restrict`

Programmer không cần:

```text
fn foo(a: &mut T, b: &mut T)
```

hoặc:

```text
restrict
```

để compiler có thể suy ra noalias.

Nếu capability semantics chứng minh:

```text
A DISJOINT B
```

compiler tự tạo internal:

```text
NoAlias(A,B)
```

---

# 38. Internal NoAlias

`NoAlias` là optimizer fact:

```text
NoAlias {
    RegionA
    RegionB
    ValidRange
}
```

Không phải source-level type.

---

# 39. NoAlias validity interval

Một noalias proof không nhất thiết sống cả function.

Ví dụ:

```text
bb1 → bb5
```

chỉ valid trong region/lifetime cụ thể.

Do đó:

```text
NoAliasFact {
    regions
    program_point_range
}
```

---

# 40. Invalidation

NoAlias fact phải invalidate khi:

```text
owner changes
capability changes
unknown call
escape
reallocation
synchronization boundary
unsafe operation
```

tùy contract.

---

# 41. Unsafe

Unsafe pointer manipulation:

```ax
unsafe {
    p = ...
}
```

có thể làm alias trở nên:

```text
UNKNOWN
```

nếu compiler không có contract đủ mạnh.

Unsafe không tự động cho:

```text
NO_ALIAS
```

---

# 42. FFI

Foreign call:

```text
extern "C" fn mutate(...)
```

nếu không có contract:

```text
Alias = UNKNOWN
Effects = conservative
```

Compiler không được giả định foreign code “không đụng gì”.

---

# 43. FFI contract

Có thể có metadata:

```text
@ffi_contract(
    reads = [0],
    writes = [1],
    noalias = [0,1]
)
```

nhưng chỉ nếu ABI/tooling contract chính thức định nghĩa semantics.

Nếu không chứng minh được:

```text
UNKNOWN
```

---

# 44. External memory

Memory mapped:

```text
ExternalMemory
```

có thể alias bất kỳ external region nào được contract cho phép.

Compiler phải conservative.

---

# 45. Volatile

Volatile operation không được CSE/reorder như ordinary memory access.

Ví dụ:

```text
VolatileLoad(addr)
```

có effect:

```text
VOLATILE
```

và alias analysis không được loại bỏ access chỉ vì giá trị dường như giống nhau.

---

# 46. Atomic

Atomic memory có thêm synchronization semantics.

Alias analysis vẫn có thể biết:

```text
same atomic location
```

nhưng optimizer không được biến atomic thành ordinary access.

---

# 47. Mutex

Mutex guard tạo synchronization-backed capability.

Ví dụ:

```text
guard = lock(mutex)
```

sau lock:

```text
guard.capability
```

cho phép access protected region.

Khi guard drop:

```text
unlock
```

và capability kết thúc.

---

# 48. Lock aliasing

Hai mutex guards trên cùng mutex:

```text
lock(m)
lock(m)
```

không phải alias violation đơn thuần; nó là synchronization/locking semantics.

Do đó AliasAnalysis và SyncAnalysis phối hợp nhưng không gộp thành một subsystem.

---

# 49. RwLock

Read guards:

```text
R
R
R
```

có thể cùng tồn tại.

Write guard:

```text
W
```

exclusive.

Đây tương ứng với capability access modes:

```text
READ
WRITE
```

nhưng synchronization implementation là library/runtime concern.

---

# 50. Async

Sau:

```text
await
```

compiler phải recompute hoặc preserve relevant alias facts.

Không được giả định toàn bộ alias state vẫn valid nếu suspension có thể cho execution khác mutate shared storage.

---

# 51. Thread

Cross-thread Send:

```text
Move(value)
```

chuyển ownership.

Nếu shared:

```text
Arc<T>
```

alias analysis biết multiple storage capabilities có thể cùng trỏ allocation.

Synchronization contract quyết định access validity.

---

# 52. GPU

GPU domain:

```text
Host
Device
Shared
```

là những storage domains riêng.

`DeviceBuffer` và host allocation không được coi là cùng region chỉ vì chúng chứa cùng logical data.

---

# 53. Host/device copy

```text
copy_host_to_device()
```

tạo semantic transfer:

```text
HostRegion
      ↓ copy
DeviceRegion
```

Hai region vẫn distinct.

---

# 54. GPU kernel

Kernel:

```ax
@kernel
fn add(a: view<f32>, b: view<f32>, out: mut_view<f32>)
```

compiler phải chứng minh:

```text
out
```

không conflict với read regions nếu semantics API yêu cầu non-overlap.

Nếu unknown:

```text
reject
```

hoặc dùng API explicitly hỗ trợ overlap.

---

# 55. Alias + vectorization

Nếu:

```text
a NO_ALIAS b
```

compiler có thể vectorize:

```text
for i:
    a[i] += b[i]
```

mà không cần giả định dynamic alias.

Nếu:

```text
UNKNOWN
```

compiler phải:

- giữ scalar path;
- runtime-check alias;
- hoặc không vectorize.

---

# 56. Runtime alias checks

Axiom có thể cho optimizer tạo:

```text
if disjoint(a,b) {
    optimized vector loop
} else {
    conservative loop
}
```

Đây là optimization.

Không thay đổi safe semantics.

---

# 57. Alias checks không phải safety checks

Điểm quan trọng:

```text
runtime alias check
```

có thể tối ưu performance.

Nhưng nếu source safe semantics **không cho phép** hai mutable capabilities overlap, compiler không được biến lỗi compile-time thành runtime check.

---

# 58. Safe semantics vs optimization speculation

Phân biệt:

```text
Safety proof:
    required

Optimization proof:
    optional
```

Nếu safety không chứng minh được:

```text
reject
```

Nếu optimization không chứng minh được:

```text
just optimize less
```

---

# 59. Escape và alias

Nếu:

```text
x
↓
unknown external call
```

thì:

```text
x = EXTERNAL_ESCAPE
```

và alias assumptions có thể phải giảm.

---

# 60. Stack local

Nếu:

```text
x
```

không escape:

```text
NoEscape
```

và một object khác không có capability/provenance vào `x`, compiler có thể chứng minh:

```text
x NO_ALIAS external storage
```

---

# 61. Scalar replacement

Nếu:

```ax
struct Point {
    x: f32,
    y: f32,
}
```

không address-taken:

```text
Point
```

có thể thành:

```text
SSA x
SSA y
```

Alias analysis giúp chứng minh không có hidden access tới aggregate.

---

# 62. Address-taken

Nếu:

```text
address_of(x)
```

và address escape:

```text
ExternalEscape
```

compiler phải thận trọng hơn.

Nếu address không escape:

```text
NoEscape
```

scalarization vẫn có thể xảy ra.

---

# 63. Provenance-aware aliasing

Hai raw pointers:

```text
p
q
```

không được đánh giá chỉ bằng type:

```text
*p: T
*q: T
```

Compiler cần provenance/region information.

---

# 64. Same allocation, different regions

Một allocation:

```text
A
```

có:

```text
A[0..10]
A[10..20]
```

Hai regions có thể:

```text
DISJOINT
```

dù cùng allocation.

Đây là lý do region analysis quan trọng hơn allocation identity đơn thuần.

---

# 65. Nested regions

Nếu:

```text
R_child CONTAINED_BY R_parent
```

thì:

```text
WRITE R_parent
```

có thể invalidate reads trên `R_child`.

Nhưng:

```text
WRITE R_other
```

nếu disjoint thì không.

---

# 66. Mutation invalidation

Khi có:

```text
WRITE(R)
```

compiler tìm các live capabilities:

```text
C1 READ(R1)
C2 READ(R2)
...
```

và kiểm tra:

```text
R overlaps R1?
R overlaps R2?
```

Nếu có conflict:

```text
reject
```

hoặc capability phải đã hết lifetime.

---

# 67. Capability splitting

Một `mut_view<T>` có thể được split:

```text
mut_view(array)
       ↓
mut_view(first_half)
mut_view(second_half)
```

chỉ nếu compiler/library contract chứng minh:

```text
DISJOINT
```

Đây là cơ chế rất hữu ích cho parallelism.

---

# 68. Capability join

Sau khi hai disjoint capabilities hết lifetime:

```text
C1
C2
```

owner có thể trở lại trạng thái toàn quyền:

```text
owner
```

không cần runtime operation.

---

# 69. Parallel iteration

Đây là cơ sở để sau này std có thể xây:

```text
parallel_for_each
```

mà compiler biết:

```text
iteration 1 → R1
iteration 2 → R2
```

và chứng minh:

```text
R1 DISJOINT R2
```

Nếu không chứng minh được, API phải dùng synchronization/atomic abstraction.

---

# 70. Alias facts tới OptIR

Verified MIR xuất:

```text
AliasInfo {
    facts[]
}
```

Ví dụ:

```text
R1 NO_ALIAS R2
R3 MUST_ALIAS R4
R5 MAY_ALIAS R6
```

OptIR sử dụng trực tiếp.

---

# 71. Alias facts không thay semantics

Nếu optimizer bỏ:

```text
load x
```

vì NoAlias/CSE và sau đó proof sai, đây là compiler bug.

AliasInfo phải có provenance:

```text
FactOrigin
```

để debug miscompilation.

---

# 72. Alias explanation

CLI:

```text
axc inspect alias foo.ax
```

có thể hiển thị:

```text
R1 = user.name
R2 = user.address

relation:
    DISJOINT

reason:
    distinct struct fields
```

---

# 73. AI-readable alias explanation

Structured event:

```json
{
  "relation": "DISJOINT",
  "left": "user.name",
  "right": "user.address",
  "proof": "FIELD_DISJOINT",
  "origin": "APAT-33"
}
```

Agent có thể hiểu tại sao compiler cho phép optimization.

---

# 74. Alias analysis không phải borrow checker

Đây là distinction quan trọng.

Borrow/capability verification hỏi:

> Có được phép access không?

Alias optimization hỏi:

> Hai access có quan hệ gì để tối ưu?

Pipeline:

```text
Safety verifier
     ↓
proven facts
     ↓
Alias analysis
     ↓
optimization
```

Không đảo ngược.

---

# 75. Analysis levels

Axiom nên có ba tầng:

```text
Level 1 — Structural
    fields
    allocations
    projections

Level 2 — Semantic
    capabilities
    provenance
    ownership

Level 3 — Numeric
    ranges
    indices
    symbolic constraints
```

Ba tầng phối hợp.

---

# 76. Conservative fallback

Khi không chứng minh được:

```text
NO_ALIAS
```

thì:

```text
MAY_ALIAS
```

hoặc:

```text
UNKNOWN
```

Không crash, không assume.

---

# 77. Alias lattice

Đề xuất ordering:

```text
              UNKNOWN
             /       \
        MAY_ALIAS   PARTIAL_ALIAS
          /              \
    MUST_ALIAS         ...
          \
        NO_ALIAS
```

Tuy nhiên đây không phải một lattice tuyến tính hoàn toàn; implementation nên dùng **relation domain** thay vì ép tất cả vào một total order.

Điều này tránh làm mất thông tin.

---

# 78. Region constraint solver

Internal constraints:

```text
R1 ⊥ R2
R3 = R4
R5 ⊂ R6
R7 overlaps R8
```

Solver resolve từ:

- field structure;
- array ranges;
- ownership;
- allocation identity;
- capabilities;
- contracts.

---

# 79. Không cần source-level region syntax

Programmer không phải viết:

```text
region<'a>
where R1 != R2
```

trong Core.

Đây là compiler internal reasoning.

---

# 80. Khi nào programmer cần can thiệp?

Chỉ khi compiler không thể chứng minh.

Khi đó có ba hướng:

```text
1. thay đổi API/algorithm để semantics rõ hơn
2. dùng abstraction có contract
3. unsafe
```

Không thêm hàng loạt annotation vào ngôn ngữ chỉ để làm compiler dễ hơn.

---

# 81. Invariants

### `AALIAS-20`
Alias analysis operates on semantic regions, not raw source syntax.

### `AALIAS-21`
Every capability has provenance and region information.

### `AALIAS-22`
Region identity is distinct from lifetime.

### `AALIAS-23`
Region identity is distinct from allocation identity.

### `AALIAS-24`
Logical identity is distinct from storage identity.

### `AALIAS-25`
Alias relations include `NO_ALIAS`, `MUST_ALIAS`, `PARTIAL_ALIAS`, `MAY_ALIAS`, and `UNKNOWN`.

### `AALIAS-26`
Unknown aliasing is never treated as no-alias.

### `AALIAS-27`
Safe mutable capabilities are exclusive over overlapping regions.

### `AALIAS-28`
Read-only capabilities may coexist when their access modes do not conflict.

### `AALIAS-29`
Disjoint regions may be accessed independently.

### `AALIAS-30`
Field-sensitive alias analysis is supported.

### `AALIAS-31`
Range-sensitive alias analysis may refine region overlap.

### `AALIAS-32`
Array ranges use half-open interval semantics internally.

### `AALIAS-33`
Adjacent non-overlapping ranges are recognized as disjoint.

### `AALIAS-34`
Unknown dynamic indices are not assumed disjoint.

### `AALIAS-35`
Allocation identity may establish disjointness when semantics prove distinct storage.

### `AALIAS-36`
Shared ownership may establish storage aliasing.

### `AALIAS-37`
Shared ownership does not imply mutable access.

### `AALIAS-38`
Raw pointers do not automatically establish safe alias facts.

### `AALIAS-39`
Integer addresses do not establish safe provenance.

### `AALIAS-40`
Unsafe operations may reduce alias certainty to unknown.

### `AALIAS-41`
Unsafe operations may establish stronger alias facts only through explicit trusted contracts.

### `AALIAS-42`
Foreign calls are conservative unless an explicit contract exists.

### `AALIAS-43`
Volatile accesses cannot be treated as ordinary memory operations.

### `AALIAS-44`
Atomic accesses preserve atomic semantics independently of alias optimization.

### `AALIAS-45`
Synchronization semantics are distinct from alias relations.

### `AALIAS-46`
Reallocation invalidates dependent storage capabilities.

### `AALIAS-47`
Stable-address contracts prevent transformations that would invalidate exposed addresses.

### `AALIAS-48`
Capability splitting requires proof of disjointness.

### `AALIAS-49`
Capability joining is valid only after dependent capabilities cease to be live.

### `AALIAS-50`
No-alias facts have explicit validity/provenance.

### `AALIAS-51`
No-alias facts are invalidated when their semantic preconditions cease to hold.

### `AALIAS-52`
Alias facts may be consumed by optimization but cannot redefine safety semantics.

### `AALIAS-53`
Safety verification precedes optimization alias analysis.

### `AALIAS-54`
Optimization may use alias facts but may not manufacture safety proofs.

### `AALIAS-55`
Failed optimization alias proofs only reduce optimization opportunities.

### `AALIAS-56`
Failed safety proofs reject safe code.

### `AALIAS-57`
Alias analysis is deterministic.

### `AALIAS-58`
Alias analysis is incrementally cacheable.

### `AALIAS-59`
Independent alias queries may execute in parallel.

### `AALIAS-60`
Alias facts preserve source provenance.

### `AALIAS-61`
Alias explanations are available to compiler tooling.

### `AALIAS-62`
Alias analysis can cooperate with range analysis.

### `AALIAS-63`
Alias analysis can cooperate with escape analysis.

### `AALIAS-64`
Alias analysis can cooperate with concurrency analysis.

### `AALIAS-65`
Alias analysis can cooperate with GPU domain analysis.

### `AALIAS-66`
Alias analysis can cooperate with FFI contracts.

### `AALIAS-67`
Safe semantics do not depend on optimizer-generated runtime alias checks.

### `AALIAS-68`
Runtime alias checks may only be used as optional optimization guards.

### `AALIAS-69`
Compiler-generated alias facts are not exposed as unsafe programmer assertions.

### `AALIAS-70`
Alias analysis must never weaken an already-proven safety invariant.

---

# Axiom hiện đã có một vòng khép kín rất quan trọng

```text
                  ┌──────────────┐
                  │     HIR      │
                  └──────┬───────┘
                         ↓
                  ┌──────────────┐
                  │     MIR      │
                  └──────┬───────┘
                         ↓
              ┌─────────────────────┐
              │   SAFETY VERIFIER   │
              │                     │
              │ Ownership           │
              │ Initialization      │
              │ Drop                │
              │ Capability         │
              └─────────┬───────────┘
                        ↓
                 ┌─────────────┐
                 │ Alias/Region│
                 │   Analysis  │
                 └──────┬──────┘
                        ↓
                 ┌─────────────┐
                 │  Verified   │
                 │     MIR     │
                 └──────┬──────┘
                        ↓
                    OptIR
```

Điểm rất đáng chú ý là kiến trúc này cho phép Axiom đạt một mục tiêu khó:

> **Safe-by-default nhưng không cần GC, không cần runtime reference counting mặc định, không cần borrow syntax, và vẫn cung cấp thông tin alias đủ mạnh cho optimizer.**

---

# BOOTSTRAP-137 — Effect System, Side Effects & Function Purity Model

Task tiếp theo sẽ khóa một phần còn thiếu để optimizer có thể hiểu **function call thực sự làm gì**:

```text
Function
   │
   ├── Read
   ├── Write
   ├── Allocate
   ├── Deallocate
   ├── Drop
   ├── Atomic
   ├── Volatile
   ├── IO
   ├── Synchronize
   ├── Panic
   ├── Foreign
   ├── GPU
   └── Async/Suspend
        ↓
     EffectSet
```

Đặc biệt sẽ giải quyết một vấn đề quan trọng của Axiom:

**Có cần bắt programmer viết `pure`, `const`, `readonly`, `noexcept`, `noalias`... hay compiler có thể tự suy luận phần lớn những thứ đó?**

Mục tiêu dự kiến là:

> **Compiler tự derive effect summary; programmer chỉ cần annotation khi semantic contract thực sự cần thiết.**

Điều này sẽ nối trực tiếp **AliasInfo + EffectInfo + Optimization** thành một hệ thống hoàn chỉnh.