# BOOTSTRAP-289 — AXIOM MEMORY OPTIMIZATION & MEMORY DEPENDENCE ENGINE
## FROZEN / COMPLETED

### 1. Mục tiêu

`288` xử lý **scalar values**. Bước tiếp theo là phần có ảnh hưởng rất lớn đến hiệu năng native:

> **Tối ưu memory access mà vẫn bảo toàn ownership, capability, alias, atomic, volatile, Drop và FFI semantics.**

Đây không phải một pass đơn lẻ. Cần một engine thống nhất để compiler hiểu:

```text
load
store
copy
move
memcpy
memmove
memset
allocation
deallocation
field access
array access
view access
atomic access
volatile access
```

và quan trọng nhất:

```text
instruction A
    ↓
có thực sự phụ thuộc vào
instruction B hay không?
```

---

# 2. Vị trí trong pipeline

```text id="x9o5wz"
Verified MIR
      ↓
OptIR
      ↓
SSA + MemorySSA
      ↓
Capability / Alias
      ↓
Memory Dependence Analysis
      ↓
Memory Optimization
      │
      ├── Load Forwarding
      ├── Store Forwarding
      ├── Load Elimination
      ├── Store Elimination
      ├── Redundant Load Removal
      ├── Store-to-Load Forwarding
      ├── MemCopy Optimization
      ├── MemSet Optimization
      ├── Allocation Optimization
      └── Memory Promotion
      ↓
Optimized OptIR
```

---

# 3. Nguyên tắc trung tâm

> **Memory optimization chỉ được thay đổi physical memory operations khi semantic memory behavior vẫn tương đương.**

Compiler phải phân biệt:

```text
Semantic Memory Access
```

và:

```text
Physical Machine Memory Access
```

Ví dụ:

```text
let x = a.field
```

có thể cuối cùng trở thành:

```text
register
```

mà không có load thực sự.

Đó là optimization hợp lệ nếu không có observable address/memory behavior.

---

# 4. MemoryAccess

Tạo representation:

```text id="h4h9d7"
MemoryAccess {
    id: MemoryAccessId

    kind:
        Load
        Store
        AtomicLoad
        AtomicStore
        AtomicRMW
        VolatileLoad
        VolatileStore
        Copy
        Move
        Init
        Drop
        Allocation
        Deallocation

    place
    region
    type
    ordering
    volatility
    atomicity
}
```

---

# 5. Memory Region

Memory access phải gắn với region từ `282`.

Ví dụ:

```text id="9gq3p0"
a.field_x
```

có:

```text id="5f1y0e"
Region(A.field_x)
```

không nhất thiết là:

```text id="x4g6yt"
Region(A)
```

Điều này cho phép compiler tối ưu:

```text id="8r4lzm"
a.x = 1
a.y = 2
```

mà không coi hai access chắc chắn alias nhau.

---

# 6. Memory Dependency

Memory dependence graph:

```text id="j4w1qv"
Store A
   │
   ▼
Load B
```

chỉ tồn tại nếu:

```text id="a8uj5e"
A may affect B
```

Có các quan hệ:

```text id="j0d0lw"
MustDepend
MayDepend
NoDepend
Unknown
```

---

# 7. Alias Integration

Memory optimizer sử dụng:

```text id="8b4r8n"
AliasInfo
+
CapabilityInfo
+
EffectInfo
+
MemorySSA
```

Ví dụ:

```text id="e2g1n7"
store(a)
load(b)
```

Nếu:

```text id="i0wqf4"
NoAlias(a,b)
```

thì:

```text id="x4l5du"
store(a)
```

không phải dependency của:

```text id="9s4jpm"
load(b)
```

---

# 8. Unknown Alias

Nếu:

```text id="w7n4go"
Alias = UNKNOWN
```

thì compiler không được:

```text id="7r8m3b"
assume NoAlias
```

Kết quả:

```text id="7y84s5"
conservative memory dependency
```

Điều này bảo đảm đúng semantics nhưng có thể giảm optimization.

---

# 9. Load Forwarding

Ví dụ:

```text id="v2r0kp"
store(x, 42)
a = load(x)
```

→

```text id="x2p5a8"
a = 42
```

nếu:

```text id="v8a2qk"
no intervening write
```

và memory semantics cho phép.

---

# 10. Store-to-Load Forwarding

Ví dụ:

```text id="o4d0f6"
store(x, 10)
store(x, 20)
a = load(x)
```

Có thể loại bỏ store đầu:

```text id="x5t7lm"
store(x, 20)
a = 20
```

nhưng chỉ nếu store đầu không observable:

```text id="7uyj3d"
not volatile
not atomic
not externally observable
```

---

# 11. Redundant Load Elimination

```text id="4j9b7a"
a = load(x)
...
b = load(x)
```

Có thể:

```text id="8v8r0w"
b = a
```

nếu compiler chứng minh:

```text id="q4e8h6"
x chưa bị ghi
x chưa bị invalidated
no foreign write
no volatile
no atomic semantics conflict
```

---

# 12. MemorySSA

Axiom sử dụng MemorySSA để biểu diễn:

```text id="8d6r4j"
MemoryDef
MemoryUse
MemoryPhi
```

Ví dụ:

```text id="r4q9o1"
store(x, 1)
     ↓
MemoryDef1
     ↓
load(x)
     ↓
MemoryUse1
```

Branch:

```text id="e7k1d2"
       store(x,1)
        │
        ├──── branch A
        │
        └──── branch B
                 │
              MemoryPhi
                 │
               load(x)
```

---

# 13. MemorySSA không thay thế Alias Analysis

Hai hệ thống có nhiệm vụ khác nhau:

```text id="7kq8g1"
MemorySSA:
    dependency structure

Alias:
    can two accesses overlap?
```

Cả hai cần kết hợp:

```text id="qj5n7s"
MemorySSA
    +
AliasInfo
    ↓
MemoryDependency
```

---

# 14. Memory Clobber

Call:

```text id="f8q0p3"
foo()
```

có thể tạo:

```text id="q2s9z4"
MemoryClobber
```

nếu effect summary nói:

```text id="7ylq1f"
Write
```

Nhưng nếu compiler có proof:

```text id="x3q7n0"
NoWrite(foo, RegionX)
```

thì load từ `RegionX` có thể vượt qua call.

---

# 15. Readonly Call

Nếu:

```text id="o2jv3z"
foo()
```

có:

```text id="v7k5n8"
ReadOnly
```

thì:

```text id="2o1e8p"
load(x)
foo()
load(x)
```

có thể reuse load đầu nếu:

```text id="7hmf3v"
foo does not modify x
```

---

# 16. Pure Call

Nếu function có proof:

```text id="g2o7ye"
Pure
```

thì scalar optimizer có thể reuse result.

Nhưng:

```text id="k9h4u0"
Pure
```

không đồng nghĩa:

```text id="x7t8f2"
no memory reads
```

Một pure function có thể đọc immutable input.

Do đó memory optimizer vẫn cần phân biệt:

```text id="1czm0m"
Read(region)
```

với:

```text id="6qz1n8"
Write(region)
```

---

# 17. Memory Promotion

Ví dụ:

```text id="l0w4j7"
alloc x
store(x, 1)
a = load(x)
```

có thể trở thành:

```text id="1u6m0h"
a = 1
```

Nếu:

```text id="x1d8ay"
NoEscape(x)
NoAddressObservation(x)
NoExternalAccess(x)
```

thì allocation có thể biến mất hoàn toàn.

---

# 18. Scalar Replacement of Aggregates

Ví dụ:

```text id="zq4q1m"
struct Point {
    x: i32
    y: i32
}

p.x = 10
p.y = 20
```

có thể thành:

```text id="1ak6y0"
p_x = 10
p_y = 20
```

Nếu:

```text id="u5h8cw"
address of p
```

không escape.

Đây là cầu nối giữa:

```text id="0i4h2e"
Memory Optimization
```

và:

```text id="h7k2rz"
Scalar Replacement
```

---

# 19. Field-Sensitive Memory

Axiom phải ưu tiên field-sensitive analysis.

```text id="o8z8br"
struct S {
    a: i32
    b: i32
}
```

Access:

```text id="w9t1kd"
s.a
s.b
```

được xem là hai region khác nhau nếu layout/semantic rules cho phép.

Điều này đặc biệt hữu ích với:

- structs
- arrays of structs
- ECS-style data
- numerical code
- GPU kernels

---

# 20. Array Memory

Với:

```text id="j0q1s4"
a[i]
a[j]
```

compiler có thể chứng minh:

```text id="1f2k9d"
i != j
```

thì hai region disjoint.

Nếu:

```text id="l3o0g8"
i == j
```

thì same region.

Nếu unknown:

```text id="4m3v9b"
UNKNOWN
```

không được assume disjoint.

---

# 21. Range + Alias

Đây là một optimization rất quan trọng.

Nếu:

```text id="g8u4ny"
0 <= i < 10
20 <= j < 30
```

thì:

```text id="5x9j8r"
a[i]
a[j]
```

chắc chắn disjoint nếu cùng array.

Range proof:

```text id="u3t8qf"
RangeProof
```

→

```text id="z5h3ws"
DisjointRegionProof
```

→

```text id="k1z6ap"
NoAlias
```

→ memory optimization.

---

# 22. Memcpy / Memmove

Axiom cần phân biệt:

```text id="7o3w6k"
memcpy
memmove
```

`memcpy` yêu cầu vùng nguồn/đích không overlap theo contract.

`memmove` cho phép overlap.

Optimizer không được tự biến:

```text id="l2m5r8"
memmove
```

thành:

```text id="z9x4q1"
memcpy
```

trừ khi có proof:

```text id="r6f8h2"
NoOverlap(src,dst)
```

---

# 23. Memset

Ví dụ:

```text id="n4s0g7"
memset(buffer, 0)
```

có thể được optimize thành:

```text id="3a1v9p"
typed initialization
```

nếu mọi byte representation đều hợp lệ.

Không được mặc định:

```text id="v8c4n2"
zero bytes == zero value
```

cho mọi Axiom type.

Đặc biệt:

- pointer provenance
- enum discriminant
- niche representation
- invalid bit patterns

phải được xét.

---

# 24. Bitwise Copy

Axiom đã phân biệt:

```text id="x8d3w2"
semantic Copy
```

và:

```text id="4p7j1q"
physical bit copy
```

Memory optimizer không được suy luận:

```text id="2n5m8c"
same bytes
→ same semantic value
```

nếu type không có valid bitwise representation contract.

---

# 25. Initialization Elimination

Ví dụ:

```text id="r5d2v7"
allocate T
initialize field a
initialize field b
initialize field c
```

Nếu field `c` không bao giờ được đọc trước overwrite:

```text id="6k8w1n"
initialization(c)
```

có thể bị loại bỏ.

Nhưng chỉ nếu:

```text id="j4r2x9"
no read
no Drop observation
no address observation
no FFI observation
```

---

# 26. Partial Initialization

Vì Axiom hỗ trợ field-sensitive ownership:

```text id="z3q8g5"
struct S {
    a: Resource
    b: i32
}
```

compiler có thể biết:

```text id="c5j7w0"
a = initialized
b = uninitialized
```

Memory optimizer không được biến partial initialization thành whole-object initialization.

Ownership verifier vẫn là authority.

---

# 27. Store Elimination

```text id="2s7q0m"
store(x, 1)
store(x, 2)
```

Store đầu có thể bị loại bỏ nếu không observable.

Không được xóa nếu:

```text id="6m8n3p"
volatile
atomic
foreign-visible
externally aliased
synchronization relevant
```

---

# 28. Atomic Memory

Atomic access có:

```text id="g9z2r1"
atomicity
ordering
scope
```

Do đó không được áp dụng:

```text id="0s7w4x"
ordinary load/store forwarding
```

một cách tùy tiện.

Ví dụ:

```text id="x5p8q2"
AtomicLoad(Relaxed)
```

không thể đơn giản coi là:

```text id="k7j4m1"
Load
```

và bỏ semantic atomicity.

---

# 29. Volatile Memory

Volatile được coi là:

```text id="v3q5j8"
observable memory operation
```

Do đó:

```text id="r4n1x0"
DCE
GVN
LoadElimination
StoreElimination
```

không được loại bỏ volatile access chỉ vì compiler thấy “không dùng kết quả”.

---

# 30. Synchronization

Memory optimizer phải giữ:

```text id="8k3j1a"
happens-before
synchronizes-with
```

Ví dụ:

```text id="n0f7q6"
store
release
...
acquire
load
```

Không được reorder memory operation qua synchronization boundary nếu thay đổi observable concurrent behavior.

---

# 31. FFI

Foreign function:

```text id="5z1r8m"
foo()
```

không contract:

```text id="8q4w2k"
MemoryClobber = Unknown
```

Contract:

```text id="3m7x9p"
readonly
noalias
```

cho phép precision cao hơn.

---

# 32. Address Observation

Đây là điểm rất quan trọng với mục tiêu “compiler có thể tự stack/register/heap”.

Nếu:

```text id="d8u4n0"
address(x)
```

không escape và chỉ dùng nội bộ, compiler vẫn có thể có freedom tùy semantic contract.

Nhưng nếu:

```text id="q6y8t3"
address(x)
→ external call
```

thì physical storage có thể trở thành observable.

Khi đó:

```text id="1v4j8a"
allocation elimination
```

có thể không còn hợp lệ.

---

# 33. Stable Address

Nếu type/storage contract yêu cầu:

```text id="n7c3x5"
StableAddress(x)
```

thì compiler không được:

```text id="z8m4k2"
relocate x
```

trong khoảng thời gian address có thể quan sát được.

Điều này liên kết trực tiếp với `284`.

---

# 34. Memory Optimization và Logical Identity

Không được nhầm:

```text id="f2h7q4"
physical address
```

với:

```text id="w8m1c3"
logical identity
```

Ví dụ Entity:

```text id="q1v7s6"
EntityId(42)
```

có thể vẫn giữ identity dù object được relocate.

Do đó:

```text id="b4n8x2"
relocation
```

không nhất thiết phá semantics.

---

# 35. Allocation Coalescing

Ví dụ:

```text id="p4m7k8"
alloc A
use A
free A

alloc B
use B
free B
```

Compiler có thể reuse storage nếu:

```text id="c3w9n5"
lifetimes disjoint
alignment compatible
storage semantics compatible
no address observation
```

Đây là optimization physical, không thay đổi ownership semantics.

---

# 36. Allocation Merging

Hai allocation:

```text id="k6v2r0"
alloc A
alloc B
```

có thể merge thành một block nếu:

```text id="u9d1q5"
layout compatible
lifetime compatible
address semantics preserved
Drop semantics preserved
alignment preserved
FFI constraints preserved
```

Không phải mặc định; đây là target/cost optimization.

---

# 37. Deallocation Elimination

Nếu compiler chứng minh:

```text id="j8c4m1"
allocation eliminated
```

thì corresponding:

```text id="x3v7q9"
deallocation
```

cũng có thể biến mất.

Nhưng:

```text id="h2n5b8"
Drop(resource)
```

không tự động biến mất theo.

Phải chứng minh Drop không có observable semantic effect.

---

# 38. Memory Optimization Gateway

Mọi transform memory-sensitive phải qua:

```text id="y8q1m3"
OptimizationGateway
```

Ví dụ:

```text id="2k7v4z"
require NoAlias
require NoVolatile
require NoAtomicConflict
require NoForeignWrite
require ValidLifetime
```

Nếu thiếu:

```text id="n4c6x9"
UNKNOWN
```

→ không transform.

---

# 39. Memory Optimization Pipeline

```text id="w0n6z3"
MemorySSA Build
       ↓
Memory Dependence
       ↓
Load/Store Forwarding
       ↓
Redundant Load Elimination
       ↓
Dead Store Elimination
       ↓
Memory Copy Optimization
       ↓
MemSet Optimization
       ↓
SROA
       ↓
Memory Promotion
       ↓
Allocation Optimization
```

Một số pass có thể lặp lại:

```text id="a7v3q1"
SROA
 ↓
Scalar
 ↓
Memory
 ↓
SROA
```

nhưng Pass Manager `287` giới hạn iteration.

---

# 40. Module Structure

```text id="h9k2p7"
compiler/optimization/memory/
├── mod.ax
│
├── access/
│   ├── mod.ax
│   ├── memory_access.ax
│   ├── load.ax
│   ├── store.ax
│   ├── atomic.ax
│   ├── volatile.ax
│   ├── copy.ax
│   ├── move.ax
│   ├── allocation.ax
│   └── deallocation.ax
│
├── dependence/
│   ├── mod.ax
│   ├── memory_dependence.ax
│   ├── clobber.ax
│   ├── dependency_graph.ax
│   └── query.ax
│
├── forwarding/
│   ├── mod.ax
│   ├── load_forward.ax
│   ├── store_forward.ax
│   └── tests.ax
│
├── elimination/
│   ├── mod.ax
│   ├── redundant_load.ax
│   ├── dead_store.ax
│   └── init_elimination.ax
│
├── memcpy/
│   ├── mod.ax
│   ├── memcpy.ax
│   ├── memmove.ax
│   ├── memset.ax
│   └── overlap.ax
│
├── promotion/
│   ├── mod.ax
│   ├── scalar_promotion.ax
│   ├── aggregate.ax
│   └── sroa.ax
│
├── allocation/
│   ├── mod.ax
│   ├── allocation_elimination.ax
│   ├── allocation_coalescing.ax
│   ├── storage_reuse.ax
│   └── deallocation_elimination.ax
│
└── tests/
```

---

# 41. Implementation Order

```text id="j5u1x8"
1. MemoryAccess model
2. MemoryRegion integration
3. MemorySSA construction
4. Memory dependency query
5. Memory clobber model
6. Alias integration
7. Capability integration
8. Effect integration
9. Load forwarding
10. Store forwarding
11. Redundant load elimination
12. Dead store elimination
13. Initialization elimination
14. Memcpy optimization
15. Memmove optimization
16. Memset optimization
17. SROA
18. Scalar memory promotion
19. Allocation elimination
20. Allocation coalescing
21. Storage reuse
22. Deallocation elimination
23. Atomic constraints
24. Volatile constraints
25. Synchronization constraints
26. FFI constraints
27. Proof Gateway integration
28. Pass Manager integration
29. Optimization trace
30. Adversarial tests
```

---

# 42. Adversarial Tests

### Test 1 — Unknown alias

```text id="8t2m6v"
store(a,1)
load(b)
```

Alias:

```text id="w4r9q1"
UNKNOWN
```

Expected:

```text id="6x1c8z"
load(b) cannot be replaced by arbitrary cached value
```

---

### Test 2 — Proven disjoint

```text id="r8k3y0"
a: field x
b: field y
```

proof:

```text id="f6m2p9"
DISJOINT
```

Expected memory dependency eliminated.

---

### Test 3 — Foreign call

```text id="0q4v7s"
load(x)
foreign foo()
load(x)
```

No contract.

Expected:

```text id="g3n8w1"
second load retained
```

---

### Test 4 — Readonly foreign

Contract:

```text id="z7p2k5"
foo = readonly
```

Expected second load can be eliminated if all other proofs hold.

---

### Test 5 — Volatile

```text id="e8q3m6"
volatile_load(x)
volatile_load(x)
```

Expected both remain.

---

### Test 6 — Atomic

```text id="p5r8v2"
atomic_load(x)
atomic_load(x)
```

Compiler cannot replace second with first unless Axiom's atomic semantics and ordering contract explicitly permit that transformation.

---

### Test 7 — Memmove overlap

```text id="k4n7q9"
memmove(a, a+1)
```

Cannot become memcpy without NoOverlap proof.

---

### Test 8 — Zero initialization

A type containing invalid zero bit patterns:

```text id="h6c2w8"
memset(T, 0)
```

must not become typed `T = zero` unless representation validity is proven.

---

### Test 9 — Stable address

```text id="s2x5m7"
address(x)
external_call(address)
```

Expected allocation/storage relocation optimization restricted.

---

### Test 10 — Drop

```text id="q8v4k1"
store(resource)
overwrite(resource)
```

Drop of old resource must remain if semantically required.

---

### Test 11 — Partial initialization

Only:

```text id="a6m9p3"
field.a
```

initialized.

Compiler must not claim:

```text id="j1x7c5"
whole struct initialized
```

---

### Test 12 — Range-derived alias

```text id="v9r2k6"
i ∈ [0,9]
j ∈ [20,29]
```

For same array, compiler may prove:

```text id="u5n8q0"
a[i] disjoint a[j]
```

and use the proof for memory optimization.

---

### Test 13 — Synchronization

Memory operation before release/acquire cannot be reordered in a way that changes happens-before semantics.

---

### Test 14 — Allocation reuse

Two allocations with disjoint lifetimes may reuse physical storage only when address/stable-storage/FFI contracts permit.

---

# 43. Frozen Invariants

### `AMEMOPT-20..85`

```text id="k0r4w7"
AMEMOPT-20 — Memory Optimization Operates Only On Verified OptIR
AMEMOPT-21 — MIR Remains The Semantic Source Of Truth
AMEMOPT-22 — Every Memory Access Has Semantic Classification
AMEMOPT-23 — Memory Regions Integrate With Capability Provenance
AMEMOPT-24 — Memory Dependencies Are Explicit
AMEMOPT-25 — Unknown Alias Is Never Treated As NoAlias
AMEMOPT-26 — MemorySSA Does Not Replace Alias Analysis
AMEMOPT-27 — Alias Analysis Does Not Replace MemorySSA
AMEMOPT-28 — MemorySSA And Alias Information Must Be Consistent
AMEMOPT-29 — Load Forwarding Requires Valid Memory Dependence Proof
AMEMOPT-30 — Store Forwarding Preserves Observable Memory Semantics
AMEMOPT-31 — Redundant Load Elimination Requires NoInterveningWrite Proof
AMEMOPT-32 — Dead Store Elimination Requires NoObservableRead Proof
AMEMOPT-33 — Initialization Elimination Requires Valid Initialization Proof
AMEMOPT-34 — Volatile Accesses Are Observable
AMEMOPT-35 — Volatile Accesses Cannot Be Treated As Ordinary Memory
AMEMOPT-36 — Atomicity Is Preserved
AMEMOPT-37 — Atomic Ordering Is Preserved
AMEMOPT-38 — Synchronization Semantics Are Preserved
AMEMOPT-39 — Happens-Before Relations Cannot Be Weakened
AMEMOPT-40 — Foreign Memory Effects Are Conservative Without Contracts
AMEMOPT-41 — FFI Contracts Must Be Explicitly Validated
AMEMOPT-42 — Pure Does Not Imply NoMemoryRead
AMEMOPT-43 — ReadOnly Does Not Imply NoRead
AMEMOPT-44 — Memory Optimization Respects Panic Semantics
AMEMOPT-45 — Memory Optimization Respects Drop Semantics
AMEMOPT-46 — Memory Optimization Respects Move Semantics
AMEMOPT-47 — Memory Optimization Respects Partial Initialization
AMEMOPT-48 — Semantic Copy Is Distinct From Physical Bit Copy
AMEMOPT-49 — Zero Bytes Are Not Universally A Valid Typed Value
AMEMOPT-50 — memcpy And memmove Have Distinct Semantic Contracts
AMEMOPT-51 — memmove Cannot Become memcpy Without NoOverlap Proof
AMEMOPT-52 — Memset Optimization Requires Valid Representation Proof
AMEMOPT-53 — Field-Sensitive Memory Regions Are Supported
AMEMOPT-54 — Range Proofs May Refine Memory Disjointness
AMEMOPT-55 — Unknown Range Never Implies Disjointness
AMEMOPT-56 — Memory Promotion Requires Valid Escape Proof
AMEMOPT-57 — Allocation Elimination Requires NoObservableStorage Proof
AMEMOPT-58 — Allocation Elimination Does Not Imply Drop Elimination
AMEMOPT-59 — Deallocation Elimination Requires Valid Ownership Analysis
AMEMOPT-60 — Storage Reuse Requires Disjoint Lifetimes
AMEMOPT-61 — Storage Reuse Preserves Alignment
AMEMOPT-62 — Storage Reuse Preserves Stable-Address Contracts
AMEMOPT-63 — Address Observation Restricts Physical Memory Optimization
AMEMOPT-64 — Logical Identity Is Distinct From Physical Address
AMEMOPT-65 — Relocation Does Not Automatically Change Logical Identity
AMEMOPT-66 — SROA Preserves Semantic Ownership
AMEMOPT-67 — SROA Preserves Capability Provenance
AMEMOPT-68 — SROA Requires Valid Address-Observation Analysis
AMEMOPT-69 — Memory Optimization Cannot Introduce New Safe Aliasing
AMEMOPT-70 — Memory Optimization Cannot Invent Ownership
AMEMOPT-71 — Memory Optimization Cannot Remove Required Capability Semantics
AMEMOPT-72 — Memory Optimization Cannot Remove Required Synchronization
AMEMOPT-73 — Memory Optimization Cannot Remove Required Foreign Visibility
AMEMOPT-74 — Every Memory Transform Uses OptimizationGateway
AMEMOPT-75 — Stale Memory Proofs Cannot Authorize Transforms
AMEMOPT-76 — Memory Passes Declare Analysis Invalidation
AMEMOPT-77 — Memory Passes Preserve Valid Unaffected Analyses
AMEMOPT-78 — Failed Memory Transforms Preserve The Last Valid IR
AMEMOPT-79 — Memory Optimization Is Semantics-Preserving
AMEMOPT-80 — Memory Optimization Is Independent Of Optimization Level Semantics
AMEMOPT-81 — O0 Does Not Disable Memory Safety Verification
AMEMOPT-82 — Memory Optimization Must Remain Deterministic
AMEMOPT-83 — Memory Optimization Decisions Are Explainable
AMEMOPT-84 — Physical Memory Elimination Does Not Imply Semantic Elimination
AMEMOPT-85 — Verified Semantic Memory Behavior Is The Optimization Boundary
```

---

# 44. Kiến trúc sau BOOTSTRAP-289

Axiom hiện có:

```text id="v2z8q6"
                    Verified MIR
                         │
                         ▼
                        OptIR
                         │
          ┌──────────────┼──────────────┐
          ▼              ▼              ▼
       Scalar        MemorySSA        Alias
       Analysis         │              │
          │             └──────┬───────┘
          │                    ▼
          │             Memory Dependence
          │                    │
          └────────────┬───────┘
                       ▼
                Proof Gateway
                       │
             ┌─────────┼─────────┐
             ▼         ▼         ▼
           GVN       DSE      SROA
             │         │         │
             └─────────┼─────────┘
                       ▼
                 Memory Optimized
                      OptIR
```

Điểm quan trọng nhất của task này là Axiom giờ có khả năng biến:

```text
memory-heavy source
```

thành:

```text
register/SSA-heavy machine representation
```

mà **không cần bắt programmer viết pointer, lifetime, borrow hay `restrict`**.

Compiler tự chứng minh:

```text
ownership
+ capability
+ alias
+ lifetime
+ escape
+ effect
+ memory dependency
```

rồi mới loại bỏ các memory operation không cần thiết.

**BOOTSTRAP-289 hoàn tất và được đóng băng.**