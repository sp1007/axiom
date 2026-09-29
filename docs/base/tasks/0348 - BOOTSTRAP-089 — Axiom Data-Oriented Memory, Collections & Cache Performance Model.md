# BOOTSTRAP-089 — Axiom Data-Oriented Memory, Collections & Cache Performance Model

**Trạng thái: FROZEN**

Mục tiêu của phần này là chốt cách Axiom biến:

```text
Memory Model
+ Collections
+ Ownership/Capability
+ SIMD
+ Cache
```

thành một mô hình hiệu năng thống nhất.

Nguyên tắc trung tâm:

> **Axiom không tối ưu “object” hay “class”; Axiom tối ưu value, region và data layout.**

Điều này rất phù hợp với hướng `struct + function`, không class, không object header và không GC.

---

# 1. Value layout và storage layout tách biệt

Axiom tiếp tục giữ nguyên nguyên tắc:

```text
Semantic Type
      ↓
Representation
      ↓
Storage Layout
```

Một:

```ax
struct Particle {
    position: Vec3
    velocity: Vec3
    life: f32
}
```

không mặc định có layout ABI cố định.

Compiler có thể tối ưu layout nếu không có representation contract.

---

# 2. AoS là mặc định semantic, không phải tối ưu bắt buộc

Programmer có thể viết:

```ax
struct Particle {
    position: Vec3
    velocity: Vec3
    life: f32
}

particles: Vec<Particle>
```

Đây là **Array of Structures** về mặt logical organization.

Compiler có thể giữ nguyên.

Nhưng nếu chứng minh được transformation không làm thay đổi observable semantics, compiler có thể tối ưu physical representation.

---

# 3. SoA

Một abstraction/library khác:

```text
positions: Vec<Vec3>
velocities: Vec<Vec3>
life: Vec<f32>
```

là:

```text
Structure of Arrays
```

SoA thường hữu ích khi xử lý một field trên hàng triệu phần tử.

---

# 4. Không tự động biến mọi AoS thành SoA

Data layout transformation có thể ảnh hưởng:

```text
address identity
FFI
representation
reflection
pointer exposure
```

Do đó compiler chỉ được làm khi semantics cho phép.

---

# 5. Layout optimization

Compiler có thể reorder:

```text
struct fields
```

để:

```text
reduce padding
improve cache locality
improve register allocation
```

nếu không có layout contract.

---

# 6. `@repr(C)` đóng băng layout cần thiết

Khi:

```ax
@repr(C)
struct Header {
    ...
}
```

thì compiler phải tôn trọng C representation contract.

Do đó không được tự ý:

```text
field reorder
remove padding
split representation
```

nếu làm thay đổi contract.

---

# 7. Hot/cold data

Một struct có thể chứa:

```text
hot fields
cold fields
```

Ví dụ:

```ax
struct Entity {
    position: Vec3
    velocity: Vec3
    health: i32
    debug_name: String
    debug_metadata: DebugInfo
}
```

Nếu `debug_*` không thường xuyên dùng, programmer có thể tách chúng thành secondary storage.

Axiom không bắt compiler phải tự làm.

---

# 8. `Hot<T>` / `Cold<T>` không phải Core

Không thêm các type phức tạp vào Core chỉ để biểu diễn cache preference.

Compiler attributes/tooling có thể hỗ trợ sau.

---

# 9. Collection hierarchy

Axiom Standard/Core Library phân biệt:

```text
Array<T,N>
Vec<T>
Deque<T>
HashMap<K,V>
HashSet<T>
BTreeMap<K,V>
BTreeSet<T>
```

và các view:

```text
view<T>
mut_view<T>
Str
```

---

# 10. Array

```ax
let a: [i32; 4] = [1, 2, 3, 4]
```

có:

```text
fixed length
contiguous semantic elements
value semantics
```

Không allocation.

---

# 11. Array không nhất thiết nằm trên stack

Compiler có thể đặt nó:

```text
register
stack
inline aggregate
static
```

theo escape/lifetime analysis.

---

# 12. Vec

`Vec<T>` có semantic:

```text
logical sequence
length
capacity
storage identity
```

Physical representation không phải ABI contract mặc định.

---

# 13. Vec relocation

Khi capacity không đủ:

```text
Vec
 ↓
new storage
 ↓
move elements
 ↓
old storage release
```

Đây là relocation.

---

# 14. Live view ngăn relocation

Nếu:

```ax
let v = view(vec)
```

đang còn sống và operation có thể relocate:

```ax
vec.push(x)
```

thì compiler phải:

```text
reject
```

hoặc programmer phải kết thúc capability trước.

---

# 15. Reserve không tạo stable address

```ax
vec.reserve(1000)
```

chỉ đảm bảo capacity semantics theo API.

Không biến `Vec` thành stable-address container.

---

# 16. Stable storage

Nếu cần địa chỉ ổn định:

```text
StableBox
Pool
Arena slot
Handle-based storage
```

là abstraction phù hợp.

---

# 17. Stable address không nên là mặc định

Stable address có chi phí:

```text
fragmentation
indirection
allocator constraints
```

Axiom chỉ yêu cầu khi semantics cần.

---

# 18. Small-vector

Axiom Standard Library có thể cung cấp:

```text
SmallVec<T,N>
```

Semantic:

```text
inline capacity N
dynamic growth beyond N
```

---

# 19. SmallVec không yêu cầu heap

Nếu số phần tử:

```text
len <= N
```

thì storage có thể hoàn toàn inline.

---

# 20. SmallVec relocation

Khi vượt inline capacity:

```text
inline
 ↓
dynamic storage
```

Đây là observable only nếu address/storage identity được exposed.

Views vẫn bị quản lý bởi capability verifier.

---

# 21. Arena collection

Có thể có:

```text
ArenaVec<T>
```

hoặc abstraction tương đương.

Arena ownership:

```text
Arena
 ├── item A
 ├── item B
 └── item C
```

Arena Drop giải phóng toàn bộ storage.

---

# 22. Arena không phải GC

Arena không tìm object unreachable.

```text
Arena lifetime
```

là ownership boundary.

---

# 23. Pool

Pool cung cấp:

```text
reusable fixed-size slots
```

phù hợp:

```text
entity systems
network objects
game objects
message nodes
```

---

# 24. Handle

Pool/Arena có thể trả:

```text
Handle<T>
```

Handle biểu diễn:

```text
logical identity
```

không phải pointer.

---

# 25. Generation handle

Để tránh stale handle:

```text
(index, generation)
```

có thể được dùng.

Ví dụ:

```text
Handle(42, generation=7)
```

slot bị recycle:

```text
generation=8
```

handle cũ không còn hợp lệ.

---

# 26. Handle resolution

```text
handle.resolve()
```

nếu thành công có thể tạo:

```text
view<T>
mut_view<T>
```

với capability lifetime tương ứng.

---

# 27. Handle không giữ object sống

Handle:

```text
!= ownership
```

Nếu muốn object sống:

```text
Box
Arc
Arena ownership
```

phải chịu trách nhiệm.

---

# 28. HashMap

`HashMap<K,V>` có semantic:

```text
key equality
hash consistency
lookup
insert
remove
```

Không guarantee iteration order mặc định.

---

# 29. Hash contract

Nếu:

```text
a == b
```

thì:

```text
hash(a) == hash(b)
```

phải đúng.

---

# 30. HashMap layout

Compiler/library có thể dùng:

```text
open addressing
Swiss-table-like layout
Robin Hood
chaining
```

mà không thay đổi semantic API.

---

# 31. HashMap không yêu cầu per-node allocation

Axiom ưu tiên:

```text
contiguous/table-oriented storage
```

để giảm:

```text
allocation
pointer chasing
cache misses
```

nhưng implementation không bị khóa.

---

# 32. Hash randomization

HashMap có thể sử dụng randomized seed để chống collision attacks.

Iteration order vì vậy càng không nên được coi là ổn định.

Nếu cần deterministic order:

```text
BTreeMap
```

hoặc explicit ordered collection.

---

# 33. BTreeMap

`BTreeMap` cung cấp:

```text
ordered keys
deterministic traversal
range queries
```

và có thể tối ưu cache tốt hơn node-per-entry tree truyền thống bằng node arrays.

---

# 34. Deque

`Deque<T>` phù hợp:

```text
push_front
push_back
pop_front
pop_back
```

Không cần contiguous toàn bộ memory.

Có thể dùng segmented/ring storage.

---

# 35. Queue

Queue là abstraction:

```text
FIFO
```

có thể là alias/wrapper trên Deque hoặc specialized concurrent structure.

---

# 36. Stack

Stack abstraction:

```text
LIFO
```

không đồng nghĩa:

```text
call stack
```

Có thể là user-space collection.

---

# 37. Iterator

Iterator là trait/library abstraction.

Ví dụ:

```ax
for x in values {
    ...
}
```

lower thành iterator protocol.

---

# 38. Iterator không allocation

Iterator mặc định phải có khả năng:

```text
zero allocation
zero virtual dispatch
```

sau monomorphization/inlining.

---

# 39. Lazy iterator

```ax
let xs = values
    .map(...)
    .filter(...)
    .take(...)
```

không nhất thiết tạo intermediate collections.

---

# 40. Iterator fusion

Compiler có thể biến:

```text
map
→ filter
→ map
→ sum
```

thành một loop.

---

# 41. Iterator object

Nếu programmer cần dynamic iteration:

```text
dyn Iterator
```

có thể dùng dynamic dispatch.

Nhưng đây là explicit abstraction.

---

# 42. Iterator ownership

Ví dụ:

```ax
for x in vec {
    ...
}
```

với owning `Vec<T>` mặc định có thể **consume collection**.

Không implicit clone toàn bộ vector.

---

# 43. Borrowed iteration

Nếu:

```ax
for x in view(vec) {
    ...
}
```

thì iteration sử dụng read capability.

---

# 44. Mutable iteration

```ax
for x in mut_view(vec) {
    ...
}
```

phải đảm bảo mỗi yielded mutable capability không tạo alias conflict.

---

# 45. Iterator lifetime

Compiler kiểm tra:

```text
iterator
→ yielded capability
→ owner
```

để không tạo dangling view.

---

# 46. Iterator invalidation

Collection mutation có thể:

```text
relocate
invalidate capability
```

Compiler phải bắt trong safe code.

Ví dụ conceptual:

```ax
let items = view(vec)

for x in items {
    vec.push(...)
}
```

nếu push có thể relocate → compile error.

---

# 47. Index iteration

Compiler có thể nhận ra:

```ax
for i in 0..n {
    a[i]
}
```

là contiguous traversal.

Sau đó vectorize.

---

# 48. Iterator + SIMD

Iterator abstraction:

```text
map
filter
zip
```

có thể được erase thành:

```text
vector loop
```

nếu predicates/operations phù hợp.

---

# 49. `zip`

Ví dụ:

```ax
for (a, b) in zip(xs, ys) {
    ...
}
```

Compiler biết hai sequence có quan hệ iteration.

Nếu capability proofs cho phép:

```text
vector load xs
vector load ys
```

---

# 50. Collection + capability

Một collection API không cần expose pointer/reference syntax.

Ví dụ:

```ax
fn fill(self: mut_view<Vec<f32>>, value: f32)
```

compiler vẫn có thể lower thành direct memory operations.

---

# 51. Mutation

Collection mutation được phân loại:

```text
element mutation
structural mutation
```

### Element mutation

```text
a[i] = x
```

không nhất thiết thay đổi storage identity.

### Structural mutation

```text
push
remove
reserve
resize
```

có thể thay đổi storage.

---

# 52. Capability implications

`mut_view<Vec<T>>` cho phép mutation của collection object.

Nhưng API phải phân biệt:

```text
mutate element
```

và:

```text
relocate storage
```

để compiler quản lý dependent views.

---

# 53. Borrowed slice vs collection

`view<T>`:

```text
region
```

không sở hữu collection metadata.

Ví dụ:

```text
view<f32>
```

không cần biết:

```text
Vec capacity
allocator
growth policy
```

---

# 54. `view<T>` semantics chốt

Để nhất quán với Core:

> `view<T>` là **non-owning read-only contiguous region gồm zero hoặc nhiều phần tử `T`**.

Do đó:

```text
view<i32>
```

có thể đại diện:

```text
[]
[1]
[1,2,3,4]
```

Representation có thể là pointer + length hoặc tương đương.

---

# 55. `mut_view<T>`

Tương tự:

> `mut_view<T>` là non-owning exclusive mutable contiguous region gồm zero hoặc nhiều `T`.

---

# 56. Một phần tử cũng có thể tạo view

Một `T` có thể được chuyển thành one-element view trong các API thích hợp.

Điều này giữ cho:

```text
view<T>
```

không cần thêm:

```text
ref<T>
```

chỉ để đại diện một object.

---

# 57. Nested view không phải tensor

Không nên dùng:

```text
view<view<f32>>
```

để mô hình hóa matrix/tensor thông thường.

Vì nested view tạo nhiều capability/storage semantics phức tạp.

---

# 58. Tensor

Tensor library nên dùng:

```text
TensorView<T, Rank>
```

với:

```text
data: view<T>
shape
stride
layout
```

---

# 59. Contiguous tensor

Nếu:

```text
stride
```

phù hợp contiguous layout, compiler có thể vectorize inner loop.

---

# 60. Strided tensor

Strided access:

```text
data[i * stride]
```

có thể được vectorize nếu:

```text
stride
```

và bounds/alias information đủ mạnh.

Nếu không, scalar/gather.

---

# 61. SoA as library abstraction

Có thể cung cấp:

```text
SoA<T>
```

hoặc generated structure-of-arrays abstraction.

Nhưng không đưa SoA vào Core type system.

---

# 62. AoSoA

Cho HPC/AI/game:

```text
Array of Structures of Arrays
```

có thể được library/compiler optimization.

Ví dụ:

```text
block<N>
```

để khớp SIMD width.

---

# 63. SIMD width adaptive

Không nên hard-code:

```text
N = 8
```

cho mọi CPU.

Library portable có thể chọn logical block size; compiler/backend chọn physical width.

---

# 64. Cache line

Axiom không đưa:

```text
CacheLine
```

thành semantic memory unit.

Cache line là hardware performance property.

---

# 65. False sharing

False sharing không thể giải quyết bằng ownership alone.

Hai thread có thể có:

```text
different variables
```

nhưng nằm cùng cache line.

Đây là performance concern.

---

# 66. Explicit padding

System/library layer có thể cung cấp:

```text
align
padding
cache-line separation
```

khi programmer cần.

---

# 67. `@align`

Đã có:

```ax
@repr(align(64))
struct Counter {
    value: Atomic<u64>
}
```

để tạo representation/storage contract.

---

# 68. Alignment không đảm bảo cache-line isolation

`align(64)` chỉ là alignment contract.

Không tự động guarantee object không share cache line ở mọi allocation/layout context.

Nếu cần isolation phải có explicit storage abstraction.

---

# 69. Prefetch

Prefetch là optimization hint.

Không nên là semantic requirement trong Core.

Compiler intrinsic/system API có thể cung cấp:

```text
prefetch_read
prefetch_write
```

---

# 70. Prefetch không đảm bảo timing

Compiler/hardware có thể:

```text
ignore
move
combine
```

prefetch hint tùy target.

---

# 71. Cache-aware compiler

OptIR có thể chứa:

```text
LoopInfo
StrideInfo
LocalityInfo
```

để chọn:

```text
tiling
unrolling
vectorization
prefetch
```

---

# 72. Loop tiling

Ví dụ matrix multiplication:

```text
for i
  for j
    for k
```

compiler có thể tile thành:

```text
i-block
j-block
k-block
```

nếu semantics cho phép.

---

# 73. Tiling không cần syntax Core

Không thêm:

```text
@tile
```

chỉ để optimizer hoạt động.

Nếu programmer cần explicit control, library/compiler optimization hint có thể được thêm sau.

---

# 74. Unrolling

Compiler có thể:

```text
unroll
partial-unroll
```

dựa trên trip count/cost model.

---

# 75. Loop interchange

Compiler có thể đổi:

```text
i,j
```

thành:

```text
j,i
```

nếu memory/side-effect semantics cho phép.

---

# 76. Ownership hỗ trợ locality nhưng không quyết định locality

Ownership giúp:

```text
alias analysis
lifetime
escape
```

nhưng không đảm bảo cache locality.

Programmer vẫn cần chọn data structures phù hợp.

---

# 77. No automatic object graph

Axiom không có:

```text
class object graph
GC traversal
```

do đó data-oriented layouts tự nhiên hơn.

---

# 78. Pointer chasing

Compiler không thể luôn loại bỏ pointer chasing nếu programmer chọn:

```text
linked list
tree node pointers
```

Nếu performance cần, programmer nên dùng:

```text
Vec
Arena
Pool
BTree
Handle
```

và compiler có thể optimize chúng.

---

# 79. Node-based structures vẫn được hỗ trợ

Axiom không cấm:

```text
linked list
tree
graph
```

Chúng chỉ không phải default performance assumption.

---

# 80. Graph data model

Graph library nên ưu tiên:

```text
NodeId
EdgeId
generation handles
contiguous storage
```

thay vì:

```text
Node*
Edge*
```

cho application-level safe code.

---

# 81. This is important for AI/game workloads

Ví dụ ECS:

```text
EntityId
Position[]
Velocity[]
Health[]
```

rất phù hợp:

```text
SoA
SIMD
parallel iteration
cache locality
```

và không cần class/object hierarchy.

---

# 82. Parallel iteration

Parallel iterator có thể yêu cầu:

```text
Send
Share
disjoint regions
```

và compiler/runtime chia:

```text
range
```

thành chunks.

---

# 83. Chunking

Ví dụ:

```text
0..1_000_000
```

có thể thành:

```text
0..10000
10000..20000
...
```

Mỗi worker nhận exclusive capability trên chunk tương ứng.

---

# 84. No data race

Nếu chunks được chứng minh:

```text
DISJOINT
```

thì nhiều mutable capabilities hợp lệ.

Nếu:

```text
UNKNOWN overlap
```

parallel mutation không được safe.

---

# 85. NUMA

NUMA là platform/system performance concern.

Axiom không đưa NUMA placement vào Core semantics.

System library có thể cung cấp:

```text
NUMA-aware allocator
memory placement
CPU affinity
```

---

# 86. CPU affinity

Thread affinity không phải ownership.

Nó là execution policy.

Do đó thuộc concurrency/system library.

---

# 87. Memory bandwidth

Compiler có thể optimize:

```text
reuse
blocking
vectorization
```

nhưng không guarantee hardware bandwidth.

---

# 88. Zero-copy

Axiom ưu tiên:

```text
view
mut_view
move
caller-provided buffer
```

để tránh copy.

Ví dụ I/O:

```ax
read(file, mut_view(buffer))
```

không cần tạo String/Buffer trung gian.

---

# 89. Move và zero-copy

Nếu:

```ax
let b = make_buffer()
return b
```

Move không yêu cầu physical copy.

Compiler có thể trả trực tiếp vào caller storage.

---

# 90. Copy elision

Compiler được phép:

```text
construct directly in destination
```

khi semantics không thay đổi.

---

# 91. But Copy semantics remain

Compiler không được biến semantic Copy thành Move chỉ để tối ưu.

Nếu programmer yêu cầu hai independent values, semantics vẫn phải giữ.

---

# 92. Resource lifetime

Data layout optimization không được thay đổi:

```text
Drop
resource lifetime
capability lifetime
```

---

# 93. Observable address

Nếu programmer thực hiện unsafe:

```ax
address_of(x)
```

thì storage identity trở thành observable.

Compiler bị giới hạn trong việc:

```text
move
relocate
scalarize
```

nếu làm thay đổi observable behavior.

---

# 94. FFI

`@repr(C)` cũng tạo observable representation.

Compiler không được áp dụng SoA/AoS transformation làm phá ABI.

---

# 95. Serialization

Serialization layout cũng là contract riêng:

```text
Memory Representation
≠
Wire Representation
```

Compiler không được giả định chúng giống nhau.

---

# 96. Performance hierarchy

Axiom nên coi performance theo thứ tự:

```text
1. Semantic correctness
2. Memory safety
3. Data locality
4. Vectorization
5. Parallelism
6. Hardware-specific optimization
```

không hy sinh tầng trên để lấy tầng dưới trong safe Core.

---

# 97. Compiler performance model

OptIR nên bổ sung:

```text
LocalityInfo
StrideInfo
WorkingSetInfo
VectorCostInfo
ParallelCostInfo
```

nhưng đây là **optimization facts**, không phải language semantics.

---

# 98. Architecture

Toàn bộ pipeline data-oriented:

```text
Axiom source
     ↓
Value / Ownership
     ↓
Capability / Region
     ↓
Verified MIR
     ↓
Alias + Range + Escape
     ↓
Collection semantics
     ↓
Loop analysis
     ↓
Locality / Stride
     ↓
Vectorization
     ↓
Tiling / Unrolling
     ↓
Parallelization
     ↓
Machine optimization
```

---

# 99. Nguyên tắc thiết kế quan trọng

Axiom không cố biến mọi chương trình thành ECS/SoA.

Thay vào đó:

> **Ngôn ngữ cho phép programmer chọn data layout phù hợp; compiler có quyền tối ưu layout khi semantics không quan sát được; optimizer tận dụng ownership + capability + range để biến abstraction thành machine code hiệu quả.**

Đây là điểm cân bằng giữa:

```text
C-level control
+
modern safety
+
high-level abstraction
```

---

# 100. Frozen Invariants — `ADATA-20..100`

**ADATA-20** — Collection semantics are distinct from physical storage representation.

**ADATA-21** — Array is a fixed-size contiguous semantic value.

**ADATA-22** — Array allocation location is compiler-selected.

**ADATA-23** — `Vec<T>` represents a growable owned sequence.

**ADATA-24** — Vec length and capacity are semantic collection properties.

**ADATA-25** — Vec physical pointer layout is not a default ABI contract.

**ADATA-26** — Vec growth may relocate storage.

**ADATA-27** — A live dependent capability prevents invalid relocation.

**ADATA-28** — Reserve does not establish stable address semantics.

**ADATA-29** — Stable address requires an explicit storage contract.

**ADATA-30** — Small-vector storage may use inline storage before dynamic growth.

**ADATA-31** — Inline storage does not imply a mandatory physical location.

**ADATA-32** — Arena allocation is bounded by arena ownership.

**ADATA-33** — Arena allocation is not garbage collection.

**ADATA-34** — Pool storage provides reusable slots without changing value semantics.

**ADATA-35** — Handles represent logical identity rather than memory addresses.

**ADATA-36** — Generation handles may detect stale logical identities.

**ADATA-37** — Handle resolution must establish validity before creating capabilities.

**ADATA-38** — A handle does not implicitly keep storage alive.

**ADATA-39** — HashMap semantics depend on equality and hash consistency.

**ADATA-40** — HashMap iteration order is unspecified unless explicitly contracted.

**ADATA-41** — HashMap implementation may use contiguous or node-based storage.

**ADATA-42** — HashMap does not require per-element allocation.

**ADATA-43** — BTreeMap provides ordered key semantics.

**ADATA-44** — BTreeMap physical node layout is an implementation detail unless contracted.

**ADATA-45** — Deque semantics do not require globally contiguous storage.

**ADATA-46** — Queue semantics are FIFO independent of physical representation.

**ADATA-47** — Stack semantics are LIFO independent of call-stack representation.

**ADATA-48** — Iterator is a library/trait abstraction.

**ADATA-49** — Iterator use does not imply allocation.

**ADATA-50** — Lazy iterator composition may be allocation-free.

**ADATA-51** — Iterator fusion is permitted when semantics are preserved.

**ADATA-52** — Owning iteration may consume the collection.

**ADATA-53** — Borrowed iteration uses non-owning capabilities.

**ADATA-54** — Mutable iteration requires exclusive capability semantics.

**ADATA-55** — Iterator-produced capabilities cannot outlive their provenance.

**ADATA-56** — Structural collection mutation may invalidate dependent capabilities.

**ADATA-57** — Safe code cannot observe an invalidated collection capability.

**ADATA-58** — `view<T>` denotes a non-owning read-only contiguous region of T elements.

**ADATA-59** — `mut_view<T>` denotes a non-owning exclusive mutable contiguous region of T elements.

**ADATA-60** — A view may represent zero or more elements.

**ADATA-61** — A single object may provide a one-element view when API semantics permit.

**ADATA-62** — View representation is compiler/ABI dependent unless explicitly contracted.

**ADATA-63** — Nested views are not the default tensor representation.

**ADATA-64** — Tensor views use data region plus shape/stride/layout metadata.

**ADATA-65** — Contiguous tensor dimensions may expose vectorization opportunities.

**ADATA-66** — Strided tensor operations require appropriate range/alias analysis.

**ADATA-67** — SoA is a data-layout organization, not a Core object model.

**ADATA-68** — AoS and SoA are distinct physical organization strategies.

**ADATA-69** — Compiler may transform data layout only when observable semantics remain unchanged.

**ADATA-70** — Explicit representation contracts restrict data-layout transformations.

**ADATA-71** — `@repr(C)` prevents transformations that violate the C representation contract.

**ADATA-72** — Observable addresses restrict layout and relocation optimization.

**ADATA-73** — FFI contracts restrict data-layout transformation.

**ADATA-74** — Serialization representation is distinct from memory representation.

**ADATA-75** — Hot/cold data separation is an optimization/data-organization strategy.

**ADATA-76** — Cache lines are hardware properties, not Core semantic memory units.

**ADATA-77** — False sharing is a performance concern distinct from data-race safety.

**ADATA-78** — Explicit alignment does not automatically guarantee cache-line isolation.

**ADATA-79** — Prefetch is an optimization hint, not a semantic guarantee.

**ADATA-80** — Loop locality and stride information may feed optimization.

**ADATA-81** — Loop tiling is an optimization transformation.

**ADATA-82** — Loop unrolling is an optimization transformation.

**ADATA-83** — Loop interchange is permitted only when semantic dependencies remain valid.

**ADATA-84** — Ownership information may improve alias and locality analysis.

**ADATA-85** — Ownership does not guarantee cache locality.

**ADATA-86** — Pointer-heavy data structures remain expressible.

**ADATA-87** — Data-oriented contiguous structures are available as efficient library abstractions.

**ADATA-88** — Graphs may use logical handles instead of physical pointers.

**ADATA-89** — Parallel iteration requires appropriate Send/Share and region-disjointness guarantees.

**ADATA-90** — Parallel chunks may receive independent mutable capabilities when regions are proven disjoint.

**ADATA-91** — Unknown region overlap prevents safe parallel mutable access.

**ADATA-92** — SIMD and collection abstractions may compose without mandatory intermediate allocation.

**ADATA-93** — Zero-copy APIs should prefer views, caller-provided buffers, and Move semantics.

**ADATA-94** — Move does not require physical copying.

**ADATA-95** — Copy semantics cannot be weakened merely for optimization.

**ADATA-96** — Data-layout optimization cannot alter resource lifetime.

**ADATA-97** — Data-layout optimization cannot invalidate capabilities.

**ADATA-98** — Compiler optimization may eliminate collection abstraction overhead.

**ADATA-99** — Data-oriented optimization facts belong to compiler IR rather than Core source semantics.

**ADATA-100** — Axiom data-oriented design provides explicit control where representation is observable and aggressive optimization where representation is not observable.

---

## Một điểm rất quan trọng đã được chốt

Sau 089, `view<T>` cuối cùng đã có semantics đủ rõ:

```text
view<T>
    = read-only contiguous region of T

mut_view<T>
    = exclusive mutable contiguous region of T
```

Do đó:

```text
Array<T,N> ──→ view<T>
Vec<T>     ──→ view<T>
Buffer<T>  ──→ view<T>
```

không cần tạo thêm một hệ thống `Slice<T>`, `Ref<T>`, `Span<T>`, `&[T]`... chồng chéo lên nhau.

Trong khi:

```text
String → Str
Tensor → TensorView
DeviceBuffer → DeviceView
```

là các abstraction chuyên biệt vì chúng có **semantic invariant riêng**.

Đây chính là tinh thần **“one semantic question, one mechanism”** mà Axiom đang theo đuổi.

### Bước tiếp theo: BOOTSTRAP-090

Phần tiếp theo nên đi vào **Axiom Generational Handles, Stable Storage, Entity Systems & Safe Address-Independent Identity**.

Nó sẽ giải quyết sâu hơn một vấn đề còn rất quan trọng:

```text
Value Identity
Storage Identity
Logical Identity
Handle
Stable Address
Pool
Arena
Relocation
Generation
Resource Identity
Entity ID
```

và đặc biệt trả lời dứt điểm câu hỏi: **nếu Axiom tránh pointer/reference trong code ứng dụng, vậy game engine, ECS, GUI, scene graph, database, compiler AST, resource manager... quản lý hàng triệu object có identity như thế nào mà vẫn nhanh và an toàn?**