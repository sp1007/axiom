# BOOTSTRAP-389 — Axiom Data-Oriented Runtime, Storage Layout & Automatic Data Structure Optimization Engine

Sau **388 — Distributed Computing**, bước tiếp theo hợp lý là quay lại một vấn đề nền tảng hơn nhưng ảnh hưởng trực tiếp đến hiệu năng của *mọi* domain:

> **Axiom phải cho compiler đủ quyền biến đổi cách dữ liệu được lưu trữ mà không bắt programmer phải chọn thủ công giữa AoS, SoA, AoSoA, packed, tiled, sparse, hot/cold...**

Đây là một phần rất quan trọng nếu mục tiêu của Axiom là **đơn giản hơn C/C++ nhưng vẫn đạt hiệu năng rất cao**.

---

# 1. Vấn đề

C/C++ thường buộc programmer phải quyết định:

```text
struct Particle {
    Vec3 position;
    Vec3 velocity;
    float mass;
}
```

hay:

```text
positions[]
velocities[]
masses[]
```

hay:

```text
x[]
y[]
z[]
```

hay:

```text
tile[]
```

Trong khi algorithm có thể thay đổi theo workload.

Axiom nên cho phép programmer mô tả **logical data**, còn compiler có quyền chọn **physical representation** khi semantics cho phép.

---

# 2. Logical Data vs Physical Layout

Đây trở thành nguyên tắc chính:

```text
Logical Type
      ↓
Layout Analysis
      ↓
Physical Representation
```

Ví dụ:

```text
Particle[]
```

về semantic vẫn là:

```text
array of Particle
```

nhưng machine representation có thể là:

```text
AoS
SoA
AoSoA
tiled
packed
```

---

# 3. AoS

Array of Structures:

```text
[P0][P1][P2][P3]
```

thích hợp khi thường xuyên dùng toàn bộ object.

---

# 4. SoA

Structure of Arrays:

```text
positions[]
velocities[]
mass[]
```

thích hợp khi SIMD/vectorization chỉ cần một số fields.

---

# 5. AoSoA

Kết hợp:

```text
[block0]
  x[]
  y[]
  z[]

[block1]
  x[]
  y[]
  z[]
```

có thể phù hợp SIMD + cache.

---

# 6. Compiler Layout Transformation

Nếu source:

```text
for p in particles {
    p.position += velocity * dt
}
```

compiler có thể nhận:

```text
field access pattern
+
loop
+
SIMD opportunity
```

và chuyển physical representation sang SoA/AoSoA nếu không có observable layout requirement.

---

# 7. Khi nào không được phép?

Nếu programmer yêu cầu:

```text
@repr(C)
```

hoặc:

```text
@repr(packed)
```

hoặc ABI/export yêu cầu layout cụ thể:

```text
external C function
```

thì layout trở thành observable.

Compiler không được tự đổi.

---

# 8. Default Layout

Struct layout mặc định:

```text
compiler-controlled
```

Compiler có thể:

- reorder fields;
- insert padding;
- optimize alignment;
- eliminate fields;
- scalarize;
- split aggregates.

Miễn là không observable.

---

# 9. Address-taking

Nếu programmer lấy địa chỉ field:

```text
unsafe {
    addr_of(x.field)
}
```

layout/location có thể trở thành observable.

Compiler phải giữ các invariants tương ứng.

---

# 10. Field Splitting

Một struct:

```text
Particle {
    position
    velocity
    mass
    debug_info
}
```

có thể được compiler split thành:

```text
hot:
position
velocity
mass

cold:
debug_info
```

nếu semantics cho phép.

---

# 11. Hot/Cold Data

Compiler có thể dùng PGO để phát hiện:

```text
hot fields
cold fields
```

và tối ưu locality.

Không cần programmer annotate.

---

# 12. Dead Field Elimination

Nếu field không bao giờ được đọc trong compiled program:

```text
debug_info
```

có thể bị loại khỏi physical representation nếu không observable.

---

# 13. Scalar Replacement

Struct:

```text
Vec2 {
    x
    y
}
```

có thể biến thành:

```text
register x
register y
```

không cần memory object.

---

# 14. Aggregate Recomposition

Ngược lại, nếu cần memory representation:

```text
x
y
```

có thể được materialize thành struct.

Compiler phải coi:

```text
logical object
```

khác:

```text
physical storage
```

---

# 15. Arrays

Array logical semantics:

```text
Array<T,N>
```

không bắt buộc physical contiguous nếu language contract không yêu cầu address-level representation.

Tuy nhiên indexing semantics vẫn phải có predictable complexity.

---

# 16. Contiguous Requirement

Khi API cần contiguous memory:

```text
contiguous_view<T>
```

phải có explicit storage/layout contract.

Compiler có thể materialize một contiguous representation nếu cần.

---

# 17. Views

View có:

```text
base
offset
shape
stride
layout
capability
```

nhưng representation có thể tối giản.

---

# 18. Stride Analysis

Compiler có thể phát hiện:

```text
stride = 1
```

và biến indexing thành pointer increment.

Nếu bounds proof tồn tại, bounds check có thể biến mất.

---

# 19. Affine Index Analysis

Ví dụ:

```text
A[i * 4 + j]
```

compiler nhận dạng affine access.

Có thể tối ưu:

```text
loop interchange
tiling
vectorization
prefetch
```

---

# 20. Layout Transformation

Các semantic transformations:

```text
transpose
reshape
permute
tile
pack
unpack
```

có thể là:

```text
zero-copy view
```

hoặc:

```text
materialized transformation
```

tùy layout.

---

# 21. Layout Specialization

Generic function:

```text
fn process<T>(x: Tensor<T>)
```

có thể specialize:

```text
contiguous
strided
blocked
```

nếu PGO/static information cho phép.

---

# 22. Data Structure Specialization

Không chỉ layout.

Ví dụ logical collection:

```text
Set<T>
```

có thể implementation:

```text
hash table
tree
sorted vector
bitset
```

tùy constraints.

Nhưng semantic behavior phải giống nhau.

---

# 23. Collection Representation

Axiom nên phân biệt:

```text
Abstract Data Semantics
```

và:

```text
Concrete Storage Representation
```

Compiler/library có thể specialize concrete representation.

---

# 24. Small Collection Optimization

Ví dụ collection nhỏ có thể được:

```text
inline
```

thay vì heap allocation.

Không cần programmer chọn `SmallVec`.

Compiler có thể làm nếu representation không observable.

---

# 25. Stack Promotion

Dynamic collection chỉ chứa số lượng nhỏ:

```text
N <= threshold
```

có thể được stack/local promoted nếu escape analysis chứng minh an toàn.

---

# 26. Heap Elimination

Ví dụ:

```text
create vector
fill
sum
discard
```

compiler có thể scalarize/eliminate toàn bộ allocation.

---

# 27. Arena Promotion

Nhiều objects cùng lifetime:

```text
request lifetime
```

có thể được đưa vào một arena.

Thay vì:

```text
alloc
alloc
alloc
free
free
free
```

thành:

```text
arena_begin
...
arena_reset
```

nếu semantics tương đương.

---

# 28. Pool Specialization

Nếu compiler thấy:

```text
same-size allocation
high frequency
same lifetime pattern
```

có thể chọn pool allocator.

Đây là optimization phía dưới abstraction.

---

# 29. Fragmentation Optimization

Flat address space không tự giải quyết fragmentation.

387/389 nên bổ sung:

```text
allocation topology
+
lifetime clustering
+
size classes
+
arena/pool selection
```

để compiler/runtime giảm fragmentation.

---

# 30. Lifetime Clustering

Nếu objects:

```text
A
B
C
```

thường được tạo/hủy cùng nhau:

```text
A lifetime ≈ B lifetime ≈ C lifetime
```

compiler/runtime có thể đặt chúng trong cùng region.

---

# 31. Region Allocation

Semantic model:

```text
Region
 ├── object A
 ├── object B
 └── object C
```

Destroy region:

```text
drop all
```

nhưng resource Drop order vẫn phải đúng.

---

# 32. Region ≠ GC

Region allocation không phải tracing GC.

Không scan graph object.

Lifetime đã được xác định bởi ownership/analysis.

---

# 33. Resource-aware Region

Không phải mọi Drop type đều có thể gom region tùy ý.

Compiler phải giữ:

```text
Drop ordering
external effects
resource dependencies
```

---

# 34. Data Placement

Compiler có thể phân loại:

```text
READ_MOSTLY
WRITE_HEAVY
TEMPORARY
PERSISTENT
STREAMING
RANDOM_ACCESS
SEQUENTIAL
```

từ static analysis + profile.

---

# 35. Cache Locality

Data layout optimizer tối ưu:

```text
spatial locality
temporal locality
working set
cache line utilization
```

---

# 36. False Sharing

Parallel structures có thể được layout:

```text
worker0 data | worker1 data
```

với padding/alignment nếu compiler chứng minh false sharing có thể gây cost đáng kể.

Không thay đổi logical semantics.

---

# 37. Alignment

Compiler có thể chọn:

```text
16
32
64
128
```

alignment theo target/vectorization.

Nhưng explicit ABI alignment là hard constraint.

---

# 38. Packed Representation

Packed data:

```text
bit fields
u4
i4
bool arrays
quantized values
```

có thể giảm memory.

Access cost phải được cost model tính.

---

# 39. Bit Packing

Ví dụ:

```text
bool[1024]
```

có thể physical là:

```text
128 bytes
```

nếu API không yêu cầu từng bool là byte-addressable.

---

# 40. Packed Access

Compiler có thể vectorize:

```text
unpack
compute
repack
```

hoặc sử dụng target bit instructions.

---

# 41. Tagged Representation

Enum:

```text
Option<T>
```

không nhất thiết luôn cần explicit tag + payload.

Compiler có thể niche-optimize nếu safe và ABI không exposed.

---

# 42. Enum Layout Optimization

Ví dụ:

```text
Option<Pointer>
```

có thể dùng representation đặc biệt nếu target/provenance semantics cho phép.

Nhưng semantic null-pointer rules của Axiom vẫn phải được giữ.

---

# 43. Sum Type Packing

Compiler có thể tối ưu:

```text
enum {
    A
    B
    C
}
```

bằng tag representation nhỏ nhất đủ biểu diễn variants.

---

# 44. Pointer-free Identity

Logical handles:

```text
EntityId
NodeId
ParticleId
```

không cần physical pointer.

Cho phép compiler/data-oriented engine di chuyển storage mà identity vẫn ổn định.

---

# 45. Generational Handle

Đối với dynamic collections:

```text
Handle {
    index
    generation
}
```

có thể phát hiện stale handles.

Đây là library semantic, không phải raw pointer.

---

# 46. Handle Storage Optimization

Compiler có thể biết handle:

```text
index + generation
```

và pack thành một integer nếu ABI cho phép.

---

# 47. Sparse/Dense Hybrid

Một logical collection có thể chuyển giữa:

```text
dense
sparse
paged
chunked
```

nếu API semantics cho phép.

---

# 48. Adaptive Data Structure

Runtime có thể monitor:

```text
lookup/write ratio
size
density
locality
```

và chuyển representation.

Nhưng việc chuyển đổi phải giữ logical identity và active view contracts.

---

# 49. Active View Constraint

Nếu:

```text
view<T>
```

đang active và storage transformation làm invalid view:

```text
AoS → SoA
```

thì không được chuyển đổi trong thời gian view còn hợp lệ.

Đây là điểm memory/capability model trực tiếp bảo vệ data-oriented optimization.

---

# 50. Compiler-generated Layout Descriptor

Nếu representation dynamic:

```text
LayoutDescriptor
```

có thể mô tả:

```text
shape
stride
field offsets
storage domain
```

Nhưng descriptor chỉ tồn tại runtime nếu thực sự cần.

Static layouts compile away.

---

# 51. Layout ABI

ABI phải phân biệt:

```text
Axiom semantic layout
```

và:

```text
C ABI layout
```

`@repr(C)` là boundary.

---

# 52. FFI

Khi truyền:

```text
struct
```

sang C:

```text
@repr(C)
```

layout bị freeze.

Compiler không được SoA transform crossing FFI boundary.

---

# 53. Serialization

Serialization format cũng là observable representation.

Compiler không được tự đổi wire format.

Internal representation vẫn có thể khác serialized representation.

---

# 54. Persistent Storage

Database/file formats là external ABI.

Axiom internal layout optimization không được phá vỡ chúng.

---

# 55. Profile-guided Layout

PGO có thể cho compiler biết:

```text
field A read 1B times
field B read 1K times
field C rarely read
```

và optimize physical layout.

---

# 56. Cross-function Layout Optimization

Nếu toàn bộ call graph biết được:

```text
struct S
```

chỉ được dùng nội bộ, compiler có thể optimize layout xuyên function boundary.

Đây là nơi Whole Program Optimization 321 + PGO + 389 phối hợp.

---

# 57. Generic Layout Specialization

Generic:

```text
fn process<T>(data: Collection<T>)
```

có thể có variants:

```text
small
large
contiguous
sparse
SIMD-friendly
```

nếu cost model thấy cần.

---

# 58. Layout Decision

Compiler có thể đánh giá:

```text
AoS:
  object locality ↑
  field scan ↓

SoA:
  SIMD ↑
  selected-field bandwidth ↓

AoSoA:
  SIMD ↑
  layout complexity ↑
```

Không có layout luôn tốt nhất.

---

# 59. Layout Cost Model

```text
LayoutCost {
    memory_size
    bandwidth
    cache_miss
    vectorization
    gather_scatter
    branch_cost
    conversion_cost
    code_size
}
```

---

# 60. Global Data-Oriented Optimization

Cuối cùng:

```text
Source logical data
        ↓
Ownership
        ↓
Lifetime analysis
        ↓
Access pattern analysis
        ↓
Layout analysis
        ↓
Profile
        ↓
Cost model
        ↓
Physical representation
```

---

# 61. CompilerDB

Bổ sung:

```text
DataLayoutDB
LogicalLayoutDB
PhysicalLayoutDB
LayoutTransformDB
LayoutConstraintDB
LayoutObservationDB
LayoutAbiDB

AoSLayoutDB
SoALayoutDB
AoSoALayoutDB
TiledLayoutDB
BlockedLayoutDB
PackedLayoutDB

FieldLayoutDB
FieldOffsetDB
FieldAlignmentDB
FieldPaddingDB
FieldSplittingDB
HotColdFieldDB

DataAccessPatternDB
AffineAccessDB
StrideAnalysisDB
ContiguousAnalysisDB
LocalityDB
CacheWorkingSetDB

DataPlacementDB
DataTemperatureDB
DataLifetimeClusterDB

CollectionRepresentationDB
CollectionSpecializationDB
SmallCollectionDB
DenseRepresentationDB
SparseRepresentationDB
AdaptiveRepresentationDB

RegionAllocationDB
RegionLifetimeDB
ArenaOptimizationDB
PoolOptimizationDB
AllocationEliminationDB
StackPromotionDB
HeapPromotionDB

PackingDB
BitPackingDB
TaggedRepresentationDB
EnumLayoutDB
NicheOptimizationDB

HandleDB
HandleRepresentationDB
GenerationDB

LayoutPGODB
LayoutCostModelDB
LayoutSpecializationDB
LayoutVerificationDB
DataOrientedOptimizationDB
DataLayoutProofDB
```

---

# 62. MIR additions

```text
LAYOUT_QUERY
LAYOUT_TRANSFORM
LAYOUT_REINTERPRET

FIELD_SPLIT
FIELD_MERGE

ARRAY_TO_SOA
SOA_TO_ARRAY
AOSOA_PACK
AOSOA_UNPACK

TILE_DATA
UNTILE_DATA
PACK_DATA
UNPACK_DATA

BITPACK
BITUNPACK

BUFFER_REUSE
STORAGE_REMAP

REGION_BEGIN
REGION_END
REGION_ALLOC
REGION_RESET

POOL_ALLOC
POOL_RELEASE

STACK_PROMOTE
HEAP_ELIMINATE

HANDLE_CREATE
HANDLE_VALIDATE
HANDLE_RESOLVE
HANDLE_INVALIDATE
```

Các operation này chủ yếu là **compiler IR**, không nhất thiết xuất hiện trong source.

---

# 63. Proof System

```text
LayoutEquivalenceProof
LayoutAbiProof
FieldLayoutProof
FieldAccessProof
AoSToSoAProof
SoAToAoSoAProof

ContiguousProof
StrideProof
AffineAccessProof
CacheLayoutProof

DataPlacementProof
LifetimeClusterProof
RegionAllocationProof
ArenaOptimizationProof
PoolOptimizationProof

AllocationEliminationProof
StackPromotionProof

BitPackingProof
EnumLayoutProof
NicheOptimizationProof

HandleSafetyProof
HandleGenerationProof

LayoutSpecializationProof
AdaptiveRepresentationProof

FFILayoutProof
SerializationLayoutProof

DataRaceLayoutProof
LayoutOwnershipProof
LayoutCapabilityProof
LayoutNumericalProof
```

---

# 64. Invariants

### `ALAYOUT-01`
Logical data semantics không được phụ thuộc physical layout nếu layout không observable.

### `ALAYOUT-02`
Compiler được phép thay đổi AoS/SoA/AoSoA khi không có layout observation.

### `ALAYOUT-03`
`@repr(C)` phải freeze C-compatible layout.

### `ALAYOUT-04`
FFI boundary không được bị layout transformation xuyên qua.

### `ALAYOUT-05`
Serialization format phải được bảo toàn.

### `ALAYOUT-06`
Address-observable operations phải được tôn trọng.

### `ALAYOUT-07`
Field splitting phải preserve field semantics.

### `ALAYOUT-08`
Hot/cold splitting phải preserve ownership và Drop order.

### `ALAYOUT-09`
Scalar replacement phải preserve observable identity khi identity observable.

### `ALAYOUT-10`
Allocation elimination chỉ hợp lệ khi allocation không observable.

### `ALAYOUT-11`
Stack promotion phải preserve lifetime và escape semantics.

### `ALAYOUT-12`
Region allocation phải preserve destruction order.

### `ALAYOUT-13`
Region allocation không được biến resource lifetime thành GC semantics.

### `ALAYOUT-14`
Pool allocation phải preserve object initialization/destruction semantics.

### `ALAYOUT-15`
Buffer reuse phải preserve capability validity.

### `ALAYOUT-16`
Active views không được bị invalidated bởi layout transformation.

### `ALAYOUT-17`
Layout transformation phải preserve bounds.

### `ALAYOUT-18`
Stride transformation phải preserve logical indexing.

### `ALAYOUT-19`
Bit packing phải preserve logical value semantics.

### `ALAYOUT-20`
Enum representation optimization phải preserve discriminant semantics.

### `ALAYOUT-21`
Niche optimization không được tạo invalid safe values.

### `ALAYOUT-22`
Handle representation optimization phải preserve logical identity.

### `ALAYOUT-23`
Generational handles phải phát hiện stale identity theo contract.

### `ALAYOUT-24`
Adaptive representation không được invalidate live capabilities.

### `ALAYOUT-25`
Data layout optimization không được tạo data race.

### `ALAYOUT-26`
Layout optimization phải preserve alignment requirements.

### `ALAYOUT-27`
SIMD-friendly layout phải preserve numerical semantics.

### `ALAYOUT-28`
PGO layout specialization phải có valid fallback/guard khi cần.

### `ALAYOUT-29`
Cost model chỉ được chọn physical representation, không thay đổi logical semantics.

### `ALAYOUT-30`
Nếu layout optimization không đem lại lợi ích hoặc không chứng minh được legality, compiler phải giữ representation hợp lệ thay vì tạo semantic risk.

---

# 65. Ý nghĩa đối với triết lý Axiom

Đây là một bước rất quan trọng vì nó giải quyết trực tiếp một điểm yếu của các ngôn ngữ systems truyền thống.

Programmer không nên phải suy nghĩ liên tục:

```text
"AoS hay SoA?"
"heap hay stack?"
"arena hay pool?"
"copy hay move?"
"có nên align 64 byte?"
"có cần padding?"
"có cần small-vector?"
```

Thay vào đó:

```text
Programmer:
    mô tả dữ liệu + semantics

Compiler:
    ownership
    lifetime
    alias
    access pattern
    layout
    allocation
    cache
    SIMD
    parallelism
    device
    cost
```

và cuối cùng:

```text
Logical Data
      ↓
Physical Data
      ↓
Native Machine Representation
```

Điều này **không làm Axiom thành một ngôn ngữ “magic” không thể đoán được**, vì mọi thay đổi quan trọng đều phải bị ràng buộc bởi semantic contracts và compiler có thể giải thích:

```text
Why AoS → SoA?
Why heap → stack?
Why buffer reused?
Why allocation eliminated?
Why padding inserted?
Why field split?
```

Đây chính là hướng phù hợp với nguyên tắc đã hình thành từ đầu dự án:

> **Compiler phải thông minh hơn programmer, nhưng không được mơ hồ hơn programmer.**