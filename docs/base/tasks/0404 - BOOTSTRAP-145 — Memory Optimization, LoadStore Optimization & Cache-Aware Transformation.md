# BOOTSTRAP-145 — Memory Optimization, Load/Store Optimization & Cache-Aware Transformation

**Trạng thái: FROZEN / COMPLETED**

Đây là một bước rất quan trọng với mục tiêu của Axiom: **không chỉ tối ưu CPU instructions mà phải tối ưu cả đường đi của dữ liệu qua memory hierarchy**.

Quyết định kiến trúc chính:

> **Axiom cho phép compiler tối ưu physical data layout và memory access pattern khi layout không phải observable contract.**

Nhưng semantic struct, FieldId, ownership, Drop order, ABI và FFI contract **không được thay đổi**.

---

# 1. Vị trí trong pipeline

```text
Verified MIR
      ↓
SSA + MemorySSA
      ↓
AliasInfo
EffectInfo
EscapeInfo
RangeInfo
      ↓
Load/Store Analysis
      ↓
Memory Dependence Analysis
      ↓
Memory Optimization
      ↓
Cache-Aware Optimization
      ↓
Loop / SIMD Optimization
      ↓
Optimized OptIR
      ↓
ABI MIR
```

---

# 2. Memory semantics ≠ physical memory layout

Axiom phải phân biệt:

```text
Semantic Object
      ↓
Representation
      ↓
Layout
      ↓
Memory Access Pattern
      ↓
Physical Cache Behavior
```

Compiler được phép tối ưu tầng dưới nếu tầng trên không bị thay đổi.

---

# 3. Ví dụ struct

Source:

```ax
struct Particle {
    x: f32,
    active: bool,
    y: f32,
    z: f32,
}
```

Semantic:

```text
Particle.x
Particle.active
Particle.y
Particle.z
```

không thay đổi.

Physical layout mặc định có thể được compiler sắp xếp lại để giảm padding/cache waste.

---

# 4. Nhưng `@repr(C)` thì khác

```ax
@repr(C)
struct Particle {
    ...
}
```

là representation contract.

Compiler không được tùy ý reorder field.

---

# 5. FFI boundary

Nếu struct đi qua:

```text
extern "C"
```

thì layout phải tuân thủ ABI contract.

Memory optimization bên trong không được vượt qua boundary đó.

---

# 6. MemorySSA

MemorySSA biểu diễn:

```text
MemoryDef
MemoryUse
MemoryPhi
```

Ví dụ:

```ax
a[0] = 10;
x = a[0];
```

Compiler biết:

```text
Store(a[0])
      ↓
Load(a[0])
```

và có thể forward:

```text
x = 10
```

---

# 7. Redundant load elimination

```ax
x = a[i];
y = a[i];
```

Nếu giữa hai load không có write có thể ảnh hưởng:

```text
x = a[i]
y = x
```

---

# 8. Alias proof

Điều này phụ thuộc:

```text
AliasInfo
+
EffectInfo
+
MemorySSA
```

Nếu một function call có thể ghi `a`:

```text
load
call
load
```

không được mặc định reuse load trước đó.

---

# 9. Region-sensitive invalidation

Nếu call chỉ ghi:

```text
b
```

và:

```text
a ∩ b = ∅
```

thì load từ `a` có thể vẫn hợp lệ.

Đây là nơi `mut_view` + AliasInfo mang lại lợi ích lớn.

---

# 10. Store-to-load forwarding

```ax
a[i] = x;
y = a[i];
```

→

```ax
y = x;
```

nếu representation và memory semantics cho phép.

---

# 11. Dead store elimination

```ax
a[i] = 1;
a[i] = 2;
```

Nếu store đầu tiên không observable:

```text
store 1
```

có thể bị loại bỏ.

---

# 12. Không xóa volatile store

```text
volatile_store(...)
```

là observable.

Do đó DSE không được loại bỏ.

---

# 13. Không xóa atomic store tùy tiện

Atomic có:

```text
atomicity
ordering
synchronization
```

nên MemoryOptimizer phải hiểu semantics.

---

# 14. Store merging

Ví dụ:

```text
a[0] = x;
a[1] = y;
a[2] = z;
a[3] = w;
```

có thể được gom thành vector/store rộng hơn nếu:

- alignment hợp lệ;
- không alias conflict;
- ordering được giữ;
- target hỗ trợ.

---

# 15. Partial store

Không được merge:

```text
byte store
```

thành:

```text
word store
```

nếu word store ghi đè vùng memory khác có observable meaning.

Alias/range analysis phải chứng minh.

---

# 16. Load widening

Các load nhỏ liên tiếp có thể được chuyển thành load rộng hơn:

```text
u8 + u8 + u8 + u8
```

→ vector/word load.

Chỉ khi extra bytes không tạo observable access violation.

---

# 17. Memory access legality

Compiler phải phân biệt:

```text
semantic bytes accessed
```

với:

```text
physical machine load width
```

Không được đọc ngoài vùng hợp lệ chỉ vì machine instruction thuận tiện.

---

# 18. Scalar replacement of aggregates

Ví dụ:

```ax
struct Point {
    x: f32,
    y: f32,
}

let p = Point { x: 1, y: 2 };
use(p.x);
```

Compiler có thể biến thành:

```text
p.x → SSA value
p.y → SSA value
```

và không cần materialize `Point`.

---

# 19. SROA

```text
Aggregate
    ↓
Field decomposition
    ↓
Scalar SSA values
```

Điều này đặc biệt hữu ích với:

- structs;
- tuples;
- small arrays;
- temporary objects;
- closure environments.

---

# 20. Ownership không cản SROA

Semantic:

```text
Move(p)
```

vẫn tồn tại.

Nhưng physical:

```text
x
y
```

có thể được truyền bằng registers.

---

# 21. Drop-aware SROA

Nếu struct có:

```text
Drop
```

compiler phải bảo đảm:

```text
Drop order
Drop exactly once
Partial move semantics
```

---

# 22. Trivial Drop

Nếu fields đều trivial:

```text
Drop(p)
```

có thể hoàn toàn biến mất.

---

# 23. Memory promotion

Một allocation:

```text
Box<T>
```

có thể được chuyển:

```text
heap
→ stack
→ registers
→ SSA
```

nếu EscapeAnalysis cho phép.

---

# 24. Allocation elimination

Nếu:

```ax
let p = Box::new(Point(...));
use(p);
```

và address/identity không escape:

```text
allocation
```

có thể biến mất hoàn toàn.

---

# 25. Memory-to-register promotion

Local memory:

```text
stack slot
```

có thể chuyển:

```text
register
```

nếu không có observable address.

---

# 26. Address-taken local

Nếu:

```ax
address_of(x)
```

và address không escape:

compiler vẫn có thể giữ stack/register với temporary materialization.

Nếu address escape:

```text
ExternalEscape / ReturnEscape / HeapEscape
```

thì constraint mạnh hơn.

---

# 27. Stable address

Nếu type/storage yêu cầu stable address:

```text
StableAddress
```

thì compiler không được:

```text
move
scalarize
relocate
```

theo cách thay đổi observable address.

---

# 28. `Vec` relocation

```ax
let v = Vec::new();
```

có thể relocate khi grow.

Active view:

```text
view(v)
```

ngăn relocation trong lifetime cần thiết.

---

# 29. Memory dependence graph

Compiler xây:

```text
MemoryDependenceGraph
```

với các relation:

```text
RAW
WAR
WAW
MayAlias
MustAlias
NoAlias
Unknown
```

---

# 30. NoAlias

Nếu:

```text
A ∩ B = ∅
```

compiler có thể optimize chúng độc lập.

Nguồn proof:

```text
Capability
Range
Allocation identity
Field identity
```

---

# 31. Unknown

Nếu:

```text
UNKNOWN
```

compiler giữ conservative dependency.

Không biến UNKNOWN thành:

```text
NO_ALIAS
```

---

# 32. Loop memory optimization

Loop:

```ax
for i in 0..n {
    x = a[i];
    y = invariant;
}
```

Nếu `invariant` không bị loop ghi:

```text
load invariant
```

có thể hoist.

---

# 33. Memory versioning

Nếu không biết call có ghi memory hay không:

```text
load
call
load
```

compiler có thể tạo runtime guard hoặc giữ load.

---

# 34. Memory versioning + effect

EffectSummary có thể nói:

```text
foo:
    Write region B
```

Nếu current load là region A:

```text
A ∩ B = ∅
```

load không bị invalidated.

---

# 35. Cache locality

Compiler có thể phân tích:

```text
access stride
working set
reuse
temporal locality
spatial locality
```

---

# 36. AoS vs SoA

Đây là điểm rất đáng chú ý với Axiom.

Semantic:

```ax
struct Particle {
    x: f32,
    y: f32,
    z: f32,
    velocity: f32,
}
```

Compiler có thể nhận thấy workload:

```text
for p in particles {
    sum += p.x;
}
```

và tối ưu layout/access pattern nếu **storage layout không observable**.

---

# 37. Nhưng không tự động phá semantic identity

Compiler không được làm thay đổi:

```text
p.x
p.y
p.z
p.velocity
```

hoặc Drop/ownership semantics.

Chỉ physical representation được biến đổi.

---

# 38. Data-oriented optimization

Axiom compiler có thể hướng tới:

```text
AoS
↓
Field extraction
↓
Scalar replacement / packed representation
↓
SoA-like physical access
```

nhưng đây là optimization nâng cao và phải có proof rằng identity/address/layout không observable.

---

# 39. Không cần thêm ngôn ngữ DOD riêng

Đây là một lợi thế.

Programmer không nhất thiết phải viết:

```text
ComponentArray
```

chỉ để compiler hiểu dữ liệu.

Nhưng explicit data-oriented containers vẫn có thể tồn tại trong std khi cần kiểm soát layout.

---

# 40. Cache-aware tiling

Nested loop:

```ax
for i in 0..N {
    for j in 0..N {
        ...
    }
}
```

có thể biến thành tiled loops để giảm cache misses.

---

# 41. Cache tiling legality

Tiling phải giữ:

```text
dependency
ordering
atomicity
volatile
Drop
observable effects
```

---

# 42. Prefetch

Compiler có thể tạo:

```text
prefetch
```

nếu:

```text
stride predictable
working set large
latency hidden
```

nhưng prefetch không phải semantic operation.

---

# 43. Prefetch failure

Nếu target không hỗ trợ:

```text
→ bỏ prefetch
```

Không ảnh hưởng semantics.

---

# 44. NUMA

Trong server/high-performance mode, compiler/runtime có thể biết:

```text
NUMA domains
```

nhưng NUMA placement không nên trở thành hidden semantic requirement của Core.

---

# 45. Thread-local memory

TLS có storage semantics riêng:

```text
Thread → TLS instance
```

Optimizer không được biến TLS thành global ordinary memory.

---

# 46. Device memory

GPU/device storage:

```text
DEVICE
```

không được tự động chuyển thành:

```text
HOST
```

---

# 47. Unified memory

Nếu API khai báo unified memory:

```text
HOST + DEVICE
```

thì compiler/runtime vẫn phải giữ coherence semantics.

---

# 48. External memory

Memory từ:

- OS;
- mmap;
- DMA;
- device;
- foreign library

là `EXTERNAL`.

Compiler phải conservative trừ khi có contract.

---

# 49. FFI memory

Foreign call:

```text
extern fn foo(...)
```

không được mặc định coi là:

```text
pure
```

hoặc:

```text
readonly
```

nếu không có ABI/effect contract.

---

# 50. `memcpy` recognition

Compiler có thể nhận:

```text
copy bytes
```

và lower thành:

```text
rep movsb
vector copy
optimized loop
```

tùy target.

---

# 51. Copy semantics

Compiler phải phân biệt:

```text
semantic Copy<T>
```

với:

```text
physical memcpy
```

Copy trait không bắt buộc machine-level memcpy.

---

# 52. Move semantics

Move:

```text
x → y
```

có thể trở thành:

```text
register rename
```

hoặc:

```text
no physical operation
```

---

# 53. Clone

Clone là semantic operation.

Compiler chỉ được eliminate/inline Clone nếu chứng minh semantics tương đương.

---

# 54. Memory initialization elimination

Nếu:

```text
allocate buffer
initialize all
overwrite all before read
```

compiler có thể bỏ initialization đầu tiên.

Ví dụ:

```text
zero memory
→ immediately overwrite every byte
```

có thể bỏ zeroing nếu không observable và memory safety vẫn được bảo đảm.

---

# 55. Không được bỏ initialization khi observable

Nếu memory:

- exposed;
- volatile;
- security contract;
- FFI;
- debug/security semantics

thì không được tự ý bỏ.

---

# 56. Zeroing/security

Axiom nên phân biệt:

```text
semantic initialization
```

và:

```text
security zeroization
```

Một API như:

```text
secure_zero()
```

phải được compiler coi là observable/system operation.

---

# 57. Dead memory

Nếu allocation chỉ chứa dead data:

```text
allocation
write
never read
```

có thể loại bỏ toàn bộ.

Nhưng không nếu:

```text
Drop
IO
volatile
foreign
observable allocation identity
```

---

# 58. Allocation identity

Nếu programmer/library quan sát identity:

```text
Handle
pointer equality
stable address
```

compiler không được merge/eliminate allocation tùy tiện.

---

# 59. Escape + memory optimization

Nếu:

```text
NoEscape
```

thì compiler có rất nhiều freedom:

```text
heap → stack → register → SSA
```

Nếu:

```text
ExternalEscape
```

freedom giảm mạnh.

---

# 60. Memory optimizer và concurrency

Không được reorder memory operation qua:

```text
Acquire
Release
AcqRel
SeqCst
Mutex
Channel
Fence
```

nếu làm thay đổi happens-before.

---

# 61. Relaxed atomics

Relaxed vẫn atomic.

Compiler có thể reorder theo memory model nhưng không thể biến thành ordinary non-atomic operation.

---

# 62. Volatile

Volatile access là observable machine interaction.

Do đó:

```text
CSE
DSE
hoisting
vectorization
merging
```

đều phải tuân thủ volatile semantics.

---

# 63. Compiler barrier

Compiler barrier:

```text
```

khác CPU fence.

Optimizer phải hiểu đúng loại barrier.

---

# 64. Memory effect taxonomy

Memory optimizer sử dụng:

```text
READ
WRITE
ATOMIC
VOLATILE
ALLOCATE
DEALLOCATE
DROP
IO
SYNCHRONIZE
FOREIGN
```

từ EffectSystem.

---

# 65. Load/store motion

Một load/store chỉ được di chuyển nếu:

```text
Alias legality
+
Effect legality
+
MemorySSA legality
+
Control-flow legality
+
Ownership/Drop legality
```

---

# 66. Cache optimization không được thành semantics

Compiler có thể thay:

```text
cache-friendly layout
```

nhưng programmer không được phụ thuộc vào layout mặc định.

Nếu muốn phụ thuộc:

```ax
@repr(C)
```

hoặc explicit storage/layout contract.

---

# 67. Đây là điểm rất quan trọng

Axiom có thể có:

```text
default:
    compiler-owned layout

explicit:
    stable layout contract
```

Do đó:

```text
performance
+
FFI
+
low-level control
```

không cần hy sinh abstraction.

---

# 68. Data layout specialization

Generic:

```ax
fn process<T>(items: view<T>)
```

có thể có representation specialization dựa trên:

```text
T size
alignment
fields
Copy/Drop
vectorizability
```

nhưng semantic generic contract vẫn giữ nguyên.

---

# 69. Structure splitting

Nếu struct:

```text
hot fields
cold fields
```

compiler có thể tách physical storage:

```text
HotPart
ColdPart
```

nếu address/layout/ABI không observable.

---

# 70. Hot/cold data

Profile-guided optimization có thể xác định:

```text
frequently accessed fields
rarely accessed fields
```

để cải thiện cache locality.

---

# 71. False sharing

Concurrent structures có thể được layout với padding/alignment nhằm giảm false sharing nếu compiler/library có đủ contract.

Explicit:

```text
@align(...)
```

vẫn là cách kiểm soát khi programmer cần đảm bảo.

---

# 72. Cache-line assumptions

Không đưa cache line size thành semantic Core constant.

TargetInfo cung cấp cho optimizer:

```text
cache line
L1/L2/L3 estimates
```

nhưng đây là optimization information.

---

# 73. Memory optimizer và SIMD

Hai subsystem phối hợp:

```text
Memory access analysis
        ↓
contiguous access
        ↓
Vectorizer
```

Nếu memory pattern xấu:

```text
gather/scatter
```

có thể được cân nhắc.

---

# 74. Memory optimizer và Loop optimizer

```text
Loop
 ↓
access pattern
 ↓
Memory optimization
 ↓
Vectorization
 ↓
Cache transform
```

Không nên coi các pass hoàn toàn độc lập.

---

# 75. Memory optimizer và Escape

```text
NoEscape
```

→ stack/register/scalarization.

```text
ReturnEscape
```

→ caller allocation có thể dùng.

```text
ExternalEscape
```

→ conservative.

---

# 76. Memory optimizer và ABI

Trước ABI:

```text
```

compiler có freedom rất lớn.

Sau ABI:

```text
```

representation đã trở thành contract.

Do đó phần lớn physical memory transformation nên hoàn thành **trước ABI lowering**, ngoại trừ target/backend transformations.

---

# 77. Representation boundary

```text
Semantic OptIR
       ↓
Memory Optimization
       ↓
Representation Selection
       ↓
Layout
       ↓
ABI
```

---

# 78. Không optimize xuyên FFI contract

Ví dụ:

```ax
extern "C" fn consume(p: *mut T);
```

compiler không được scalarize object mà FFI expects contiguous representation.

---

# 79. Inspection

Axiom nên hỗ trợ:

```text
axc inspect memory foo
axc inspect loads foo
axc inspect stores foo
axc inspect alias foo
axc inspect layout foo
axc inspect cache foo
```

---

# 80. Ví dụ explain

```text
Load #17

Original:
    a[i]

Status:
    redundant load eliminated

Reason:
    MemorySSA defining access = Load #12
    no intervening write
    region unchanged
```

---

# 81. Cache explanation

```text
Loop #4

Transformation:
    tiled 32 × 32

Reason:
    estimated working set exceeds L1
    reuse across inner dimension
    dependency proof valid
```

---

# 82. Khi không tối ưu

```text
Structure splitting rejected

Reason:
    address escapes through FFI
```

hoặc:

```text
Store widening rejected

Reason:
    adjacent byte region may be observable
```

---

# 83. Invariants đã khóa

### `AMEMOPT-20`
Memory optimization preserves semantic memory behavior.

### `AMEMOPT-21`
Semantic object identity is distinct from physical memory layout.

### `AMEMOPT-22`
Default layouts are compiler-controlled unless explicitly contracted.

### `AMEMOPT-23`
Explicit representation contracts constrain memory optimization.

### `AMEMOPT-24`
`@repr(C)` preserves required C-compatible layout.

### `AMEMOPT-25`
FFI-visible layouts cannot be arbitrarily transformed.

### `AMEMOPT-26`
MemorySSA is the authoritative optimization model for memory dependencies.

### `AMEMOPT-27`
Memory optimizations consume AliasInfo and EffectInfo.

### `AMEMOPT-28`
Unknown aliasing remains conservative.

### `AMEMOPT-29`
NoAlias requires compiler proof.

### `AMEMOPT-30`
Redundant loads may be eliminated only when invalidation is disproven.

### `AMEMOPT-31`
Store-to-load forwarding requires valid memory dependence.

### `AMEMOPT-32`
Dead stores may be eliminated only when unobservable.

### `AMEMOPT-33`
Volatile operations are never treated as ordinary memory operations.

### `AMEMOPT-34`
Atomic operations preserve atomicity and ordering semantics.

### `AMEMOPT-35`
Synchronization boundaries constrain memory motion.

### `AMEMOPT-36`
Foreign calls are conservative without verified contracts.

### `AMEMOPT-37`
Memory effects are region-sensitive where proven.

### `AMEMOPT-38`
Field-sensitive alias analysis may enable independent memory optimization.

### `AMEMOPT-39`
Range-sensitive alias analysis may enable access widening.

### `AMEMOPT-40`
Access widening cannot access semantically invalid memory.

### `AMEMOPT-41`
Physical load width does not redefine semantic access width.

### `AMEMOPT-42`
SROA preserves aggregate semantics.

### `AMEMOPT-43`
SROA preserves ownership semantics.

### `AMEMOPT-44`
SROA preserves Drop semantics.

### `AMEMOPT-45`
Memory promotion requires valid escape analysis.

### `AMEMOPT-46`
Allocation elimination requires allocation identity to be unobservable.

### `AMEMOPT-47`
Stable-address contracts prevent invalid promotion.

### `AMEMOPT-48`
Active capabilities constrain relocation.

### `AMEMOPT-49`
Initialization elimination requires valid semantic initialization proof.

### `AMEMOPT-50`
Security zeroization is distinct from ordinary initialization.

### `AMEMOPT-51`
Observable zeroization cannot be removed.

### `AMEMOPT-52`
Cache optimization is not semantic behavior.

### `AMEMOPT-53`
Cache-aware transformations require dependency legality.

### `AMEMOPT-54`
Loop tiling preserves observable execution semantics.

### `AMEMOPT-55`
Structure splitting requires layout/address observability analysis.

### `AMEMOPT-56`
AoS/SoA physical transformation is permitted only when semantic identity is preserved.

### `AMEMOPT-57`
Hot/cold field separation cannot violate ABI contracts.

### `AMEMOPT-58`
Cache-line information is target optimization data, not Core semantic data.

### `AMEMOPT-59`
Prefetch is non-semantic optimization.

### `AMEMOPT-60`
Unsupported prefetch targets simply omit prefetch optimization.

### `AMEMOPT-61`
Memory optimization cooperates with SIMD optimization.

### `AMEMOPT-62`
Memory optimization cooperates with loop optimization.

### `AMEMOPT-63`
Memory optimization cooperates with escape analysis.

### `AMEMOPT-64`
Memory optimization occurs primarily before ABI lowering.

### `AMEMOPT-65`
Backend memory optimization must preserve ABI contracts.

### `AMEMOPT-66`
Device memory remains in its declared storage domain.

### `AMEMOPT-67`
External memory remains conservative without explicit contracts.

### `AMEMOPT-68`
TLS semantics cannot be replaced with ordinary global storage.

### `AMEMOPT-69`
Concurrent memory transformations preserve happens-before semantics.

### `AMEMOPT-70`
Memory optimization cannot weaken synchronization guarantees.

### `AMEMOPT-71`
Optimization cannot create safety proofs.

### `AMEMOPT-72`
Failed memory optimization proofs only reduce optimization opportunity.

### `AMEMOPT-73`
Memory transformations are deterministic.

### `AMEMOPT-74`
Memory analyses are incrementally cacheable.

### `AMEMOPT-75`
Memory analyses may run in parallel.

### `AMEMOPT-76`
Memory transformations preserve source provenance.

### `AMEMOPT-77`
AI/compiler tooling can explain memory optimization.

### `AMEMOPT-78`
Optimized memory operations remain valid Verified-MIR implementations.

### `AMEMOPT-79`
No mandatory runtime memory machinery is introduced by optimization.

### `AMEMOPT-80`
Verified MIR remains the semantic authority.

---

# Một kết quả quan trọng cho triết lý Axiom

Đến đây Axiom có thể có chuỗi:

```text
Source
  ↓
safe abstraction
  ↓
ownership/capability proof
  ↓
alias proof
  ↓
escape proof
  ↓
MemorySSA
  ↓
SROA
  ↓
load/store optimization
  ↓
loop optimization
  ↓
SIMD
  ↓
cache optimization
  ↓
machine code
```

Tức là programmer **không cần viết code thấp cấp chỉ để giúp compiler hiểu alias/lifetime/layout**.

Compiler tự làm phần khó.

---

# BOOTSTRAP-146 — Data Layout Optimization & Data-Oriented Compilation

Bước kế tiếp nên tách riêng vấn đề **data layout** khỏi memory optimization.

Đây là nơi Axiom có thể xây một khả năng khá mạnh:

```text
Semantic Struct
       ↓
Layout Analysis
       ↓
Field Hotness
       ↓
Padding Optimization
       ↓
Field Reordering
       ↓
Structure Splitting
       ↓
AoS ↔ SoA-like transformation
       ↓
Hot/Cold Separation
       ↓
Vector-friendly Layout
       ↓
Cache-friendly Layout
       ↓
Representation Selection
```

Điểm cần khóa tiếp theo là **compiler được phép thay đổi layout đến mức nào mà programmer vẫn có cảm giác đang làm việc với một `struct` bình thường**, và khi nào `@repr(C)`, `@repr(transparent)`, `@repr(packed)` hoặc stable-address/FFI contract biến layout thành thứ không còn được phép tối ưu.