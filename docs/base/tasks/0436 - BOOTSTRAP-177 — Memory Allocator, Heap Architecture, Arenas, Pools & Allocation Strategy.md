# BOOTSTRAP-177 — Memory Allocator, Heap Architecture, Arenas, Pools & Allocation Strategy
**FROZEN / COMPLETED**

Task này chốt một điểm rất quan trọng của Axiom:

> **Axiom không chọn “stack vs heap” làm mô hình bộ nhớ của ngôn ngữ. Axiom chọn mô hình ownership + storage domain + allocation strategy, sau đó compiler quyết định vật lý hóa giá trị ở đâu.**

Và một kết luận quan trọng:

> **Flat virtual address space không phải allocator. Nó là address model.**  
> Fragmentation chủ yếu là vấn đề của allocation strategy + lifetime + locality, không phải do việc địa chỉ có “phẳng” hay không.

---

# 177.1. Tách 5 khái niệm

Axiom phải phân biệt tuyệt đối:

```text
Value
Ownership
Storage
Allocation
Address
```

Ví dụ:

```ax
let x = Vec<i32>();
```

không có nghĩa:

```text
x = heap pointer
```

Semantic chỉ nói:

```text
x owns a growable sequence
```

Compiler có thể chọn:

```text
register
stack
inline
heap
arena
pool
static
```

---

# 177.2. Storage ≠ Allocation

Đây là distinction quan trọng nhất.

```text
Storage
= nơi value tồn tại

Allocation
= cách storage được cấp phát
```

Ví dụ:

```text
heap + malloc
heap + pool
heap + arena
stack
inline
static
device memory
```

là những combination khác nhau.

---

# 177.3. Flat memory model

Axiom nên dùng:

> **Flat virtual address space ở machine/system level.**

Tức là trên target thông thường, program nhìn thấy một address space phẳng:

```text
0x0000...
        │
        ├── code
        ├── readonly
        ├── data
        ├── heap
        ├── mapped memory
        ├── shared memory
        └── stack
```

Nhưng:

> **Không biến flat address space thành semantic ownership model.**

---

# 177.4. Vì sao không nên dùng “flat memory” làm semantic model?

Nếu language semantics nói:

```text
mọi thứ là address
```

programmer sẽ phải xử lý:

```text
pointer
pointer arithmetic
lifetime
alias
dangling
alignment
ownership
```

Đó chính là vấn đề Axiom đang muốn loại bỏ.

Thay vào đó:

```text
Semantic
    Value + Ownership + Capability

Physical
    Address + Storage + Layout
```

---

# 177.5. Address chỉ xuất hiện khi observable

Nếu programmer viết:

```ax
let x = LargeStruct(...);
process(x);
```

compiler không cần tạo address cho `x`.

Có thể:

```text
SSA registers
```

hoặc:

```text
stack slot
```

hoặc:

```text
inline inside another object
```

---

# 177.6. Address-taking là semantic boundary

Khi programmer/system code thực sự yêu cầu:

```ax
unsafe {
    let p = address_of(x);
}
```

thì:

```text
address
```

trở thành observable.

Từ thời điểm đó compiler phải bảo vệ những property liên quan.

Ví dụ:

```text
stable address
```

có thể trở thành storage contract.

---

# 177.7. Không phải cứ lấy address là phải heap

Ví dụ:

```text
stack object
   ↓
address taken
   ↓
address doesn't escape
```

vẫn có thể ở stack.

Chỉ khi:

```text
address escapes
```

thì compiler mới phải đảm bảo storage tồn tại tương ứng.

---

# 177.8. Allocation abstraction

Axiom standard library nên có abstraction:

```text
Allocator
```

nhưng Core compiler không bắt mọi allocation phải đi qua virtual interface.

Ví dụ:

```ax
let x = Box.alloc(value);
```

có thể compile trực tiếp tới:

```text
allocator.allocate(...)
```

sau specialization.

---

# 177.9. Không virtual allocator mặc định

Không nên:

```text
Box
 ↓
dyn Allocator
 ↓
virtual call
```

cho mọi allocation.

Thay vào đó:

```text
Generic allocator
 ↓
monomorphization/specialization
 ↓
direct allocation
```

hoặc compiler builtin.

---

# 177.10. Allocator categories

Axiom standard library nên hỗ trợ:

```text
SystemAllocator
GeneralAllocator
Arena
Region
Pool
Slab
StackAllocator
LinearAllocator
ThreadLocalAllocator
NUMAAllocator
DeviceAllocator
CustomAllocator
```

---

# 177.11. System allocator

Wrapper OS allocator:

```text
malloc/free
VirtualAlloc
mmap
```

chỉ là một backend.

Không phải semantic requirement.

---

# 177.12. General-purpose allocator

Dùng cho workload tổng quát:

```text
allocate
deallocate
reallocate
```

Có thể dùng implementation kiểu:

```text
size classes
bins
segregated free lists
thread caches
large allocation mapping
```

nhưng Axiom không khóa implementation cụ thể.

---

# 177.13. Arena

Arena phù hợp với:

```text
parse tree
compiler IR
request lifetime
temporary graph
game frame
```

Concept:

```text
Arena
 ├── object A
 ├── object B
 ├── object C
 └── reset()
```

Một lần release:

```text
Arena.destroy()
```

thay vì destroy từng allocation vật lý.

---

# 177.14. Arena và Drop

Không được vì arena mà bỏ qua semantic Drop.

Nếu object có:

```text
Drop
```

thì:

```text
arena reset
```

vẫn phải xử lý Drop semantics theo contract.

Compiler có thể batch cleanup khi chứng minh tương đương.

---

# 177.15. Region lifetime

Arena có:

```text
Region
```

lifetime.

Ví dụ:

```text
request region
```

mọi allocation trong region chết cùng region.

Compiler có thể hiểu region dependency để ngăn:

```text
return view_from_short_region()
```

ra ngoài.

---

# 177.16. Pool

Pool phù hợp với:

```text
many same-size objects
```

Ví dụ:

```text
Pool<Node>
```

có:

```text
allocate
release
```

và reuse slots.

---

# 177.17. Slab

Slab là specialization:

```text
fixed-size allocation
```

thường có locality rất tốt.

Đặc biệt phù hợp:

```text
network objects
game entities
OS/kernel objects
compiler nodes
```

---

# 177.18. Free-list

Pool/slab có thể giữ:

```text
free list
```

nhưng free-list pointer là implementation detail.

Không trở thành programmer-facing pointer model.

---

# 177.19. Stack allocator

Axiom có thể cung cấp:

```text
StackArena
```

hoặc scoped temporary region.

Ví dụ conceptual:

```ax
with_stack_region(fn(region) {
    ...
});
```

Compiler có thể hạ trực tiếp thành:

```text
stack pointer adjustment
```

nếu semantics cho phép.

---

# 177.20. Linear/bump allocator

Đặc biệt hiệu quả:

```text
ptr += size
```

allocation O(1).

Deallocation:

```text
reset
```

phù hợp compiler/request/frame workloads.

---

# 177.21. Thread-local allocator

Multithread workload có thể dùng:

```text
ThreadLocalAllocator
```

để tránh:

```text
global allocator lock
```

Pattern:

```text
thread
  ↓
local cache
  ↓
global fallback
```

---

# 177.22. NUMA allocator

Server lớn có thể cần:

```text
NUMA node local allocation
```

Axiom không nên đưa NUMA vào Core semantics.

Nhưng allocator API có thể expose:

```text
allocate_on(node)
```

ở system/performance layer.

---

# 177.23. Device allocator

GPU:

```text
DeviceAllocator
```

không phải:

```text
Heap<T>
```

thông thường.

Storage domain:

```text
HOST
DEVICE
SHARED
EXTERNAL
```

phải được compiler phân biệt.

---

# 177.24. Unified memory

GPU runtime có thể có:

```text
UnifiedBuffer<T>
```

nhưng semantic contract phải nói rõ:

```text
ownership
coherence
visibility
synchronization
```

Không mặc định coi unified memory giống ordinary CPU RAM.

---

# 177.25. External memory

Ví dụ:

```text
memory-mapped file
shared memory
DMA buffer
foreign allocation
```

nên là:

```text
ExternalStorage<T>
```

hoặc abstraction tương đương.

Compiler không được giả định allocator ownership.

---

# 177.26. Foreign allocator

Không được:

```text
foreign_malloc()
    ↓
Axiom free()
```

mặc định.

Phải biết:

```text
allocation domain
deallocation domain
ABI contract
```

Ví dụ C library:

```text
malloc
    ↓
free
```

phải dùng đúng allocator domain.

---

# 177.27. Allocation ownership contract

Mỗi dynamic storage semantic object cần biết:

```text
Owner
AllocatorDomain
StorageDomain
Deallocator
Alignment
Size
```

ở compiler/library metadata nếu cần.

---

# 177.28. `Box<T>`

`Box<T>` vẫn là:

```text
owned dynamic storage abstraction
```

nhưng **không có nghĩa compiler bắt buộc tạo heap allocation**.

Nếu:

```text
Box<T>
```

không expose address/identity ra ngoài và escape analysis chứng minh không cần heap:

```text
Box<T>
↓
stack/register/SSA
```

được phép.

---

# 177.29. Khi Box phải thật sự dynamic

Nếu semantics yêu cầu:

```text
stable address
or
storage escapes
or
dynamic lifetime
or
FFI external ownership
```

compiler phải giữ storage contract.

Khi đó heap/arena/pool có thể được chọn.

---

# 177.30. Observable allocation identity

Đây là điểm quan trọng.

Nếu programmer có thể quan sát:

```text
allocation identity
```

thì compiler không được biến:

```text
allocation A
```

thành:

```text
same allocation as B
```

nếu làm thay đổi semantics.

---

# 177.31. Allocation identity ≠ pointer identity

Axiom có ba loại identity:

```text
Value Identity
Storage Identity
Logical Identity
```

Ví dụ Entity:

```text
EntityId(123)
```

có logical identity.

Nó không cần:

```text
stable memory address
```

---

# 177.32. Vì vậy data-oriented programming dễ hơn

Thay vì:

```text
Entity *
```

làm identity:

```text
EntityId
```

Compiler có thể di chuyển entity:

```text
memory A
   ↓
memory B
```

mà logical identity vẫn:

```text
EntityId(123)
```

---

# 177.33. Fragmentation

Fragmentation có ít nhất hai loại:

```text
External fragmentation
Internal fragmentation
```

### External

Free blocks bị phân tán:

```text
used
free
used
free
used
```

### Internal

Allocation nhận block lớn hơn nhu cầu:

```text
requested = 33 bytes
block     = 48 bytes
```

---

# 177.34. Flat address space không giải quyết fragmentation

Flat address:

```text
0x1000
0x2000
0x3000
```

không quyết định allocator đặt object thế nào.

Do đó:

> **Không nên kỳ vọng flat memory tự động loại bỏ fragmentation.**

---

# 177.35. Cách Axiom giảm fragmentation

Axiom nên kết hợp:

```text
escape analysis
+
lifetime analysis
+
arena
+
pool
+
slab
+
size classes
+
stack promotion
+
allocation elimination
+
data-oriented layout
```

---

# 177.36. Lifetime-aware allocation

Nếu compiler biết:

```text
A sống 1 ms
B sống 1 ms
C sống 1 ms
```

thì có thể dùng:

```text
arena/frame allocation
```

thay vì general heap.

---

# 177.37. Non-overlapping lifetimes

Ví dụ:

```text
A █████
B      █████
C           █████
```

cùng một physical storage có thể reuse:

```text
slot 1 → A
slot 1 → B
slot 1 → C
```

Đây là:

> **storage reuse**

không phải semantic object reuse.

---

# 177.38. Compiler stack slot reuse

Trong SSA/backend:

```text
x live [1,5]
y live [6,10]
```

có thể:

```text
same stack slot
```

vì lifetime không overlap.

Programmer không thấy điều này.

---

# 177.39. Allocation elimination

Ví dụ:

```ax
fn distance(a: Point, b: Point) -> f32 {
    let tmp = Vec2(...);
    ...
}
```

Nếu `tmp` không escape:

```text
No allocation
```

thậm chí:

```text
No stack object
```

có thể xảy ra.

---

# 177.40. Scalar replacement

```ax
struct Point {
    x: f32,
    y: f32
}
```

Compiler có thể biến:

```text
Point p
```

thành:

```text
p.x → SSA value
p.y → SSA value
```

không có object vật lý.

---

# 177.41. Small object optimization

Library có thể cung cấp:

```text
SmallVec
SmallString
SmallBox
```

nhưng không nên hard-code một kích thước universal vào language.

Target/layout quyết định.

---

# 177.42. Inline storage

Ví dụ:

```text
SmallVec<T, 8>
```

semantic:

```text
capacity <= 8
```

có thể nằm inline.

Khi vượt:

```text
spill to dynamic storage
```

---

# 177.43. Compiler specialization

Generic:

```text
SmallVec<T, N>
```

có thể specialize:

```text
N = 0
N = 4
N = 8
N = 16
```

và tối ưu layout/code.

---

# 177.44. Alignment

Allocator phải đảm bảo:

```text
alignment >= required alignment
```

Compiler có:

```text
align_of(T)
```

và explicit:

```text
@align(N)
```

nếu cần.

---

# 177.45. Over-aligned allocations

Nếu:

```text
align_of(T) > default allocator alignment
```

allocator/backend phải cung cấp aligned storage.

Không được silent misalignment.

---

# 177.46. Packed storage

```text
@repr(packed)
```

đã frozen là unsafe/system.

Lý do:

```text
field address may be misaligned
```

Compiler không tự biến packed access thành ordinary aligned access.

---

# 177.47. Zero-sized types

ZST:

```text
struct Marker {}
```

có thể:

```text
size = 0
```

nhưng vẫn có semantic type identity.

Không cần physical allocation cho mỗi instance.

---

# 177.48. Allocation failure

Axiom không nên ép một chính sách duy nhất.

Profiles có thể:

```text
abort
panic
Result
custom handler
```

Library API nên có cả:

```text
try_allocate()
```

cho hệ thống cần recoverable failure.

---

# 177.49. OOM không phải ordinary exception

Out-of-memory không nên tự động tạo:

```text
Exception object
stack unwinding
```

trừ profile/runtime đã chọn.

---

# 177.50. `try_new`

Conceptual:

```ax
let x = Box.try_new(value)?;
```

có thể:

```text
Result<Box<T>, AllocError>
```

Không cần exception runtime.

---

# 177.51. Reallocation

`Vec` có thể:

```text
grow
 ↓
new allocation
 ↓
move elements
 ↓
release old storage
```

Compiler phải biết:

```text
active view
```

đang tồn tại hay không.

Nếu có view ngăn relocation:

```text
grow
→ compile/runtime contract violation
```

tùy API semantics.

---

# 177.52. `reserve`

`reserve(n)` chỉ guarantee:

```text
capacity >= required
```

Không guarantee:

```text
address stable forever
```

Stable address là contract khác.

---

# 177.53. Stable container

Nếu cần:

```text
stable address
```

dùng container có semantic contract riêng:

```text
StableBox
StableVec
SlotMap
ArenaHandle
```

chứ không làm mọi Vec chậm hơn.

---

# 177.54. Stable address nên hiếm

Nếu mọi object đều stable:

```text
compiler optimization
↓
blocked
```

Do đó Axiom default:

> **Address instability is allowed unless stability is explicitly observable/required.**

---

# 177.55. Cache locality

Allocator nên có thể tối ưu:

```text
spatial locality
temporal locality
```

Ví dụ:

```text
related objects
→ same arena/page/cache region
```

---

# 177.56. Object placement

Compiler/runtime có thể group:

```text
hot objects
cold objects
short-lived objects
long-lived objects
```

thành storage regions khác nhau.

---

# 177.57. Hot/cold lifetime separation

Nếu:

```text
HotObject
```

sống lâu nhưng:

```text
temporary metadata
```

sống ngắn, không nên bắt chúng chung allocation region nếu gây fragmentation/cache pollution.

---

# 177.58. Generation handles

Container di chuyển object:

```text
slot 10
generation 3
```

handle:

```text
EntityId {
    index: 10,
    generation: 3
}
```

Nếu slot reused:

```text
generation 4
```

old handle không còn hợp lệ.

Đây là library-level safety mechanism rất mạnh.

---

# 177.59. Handle không phải reference

Handle:

```text
EntityId
```

không cung cấp:

```text
direct memory access
```

Nó là:

```text
logical identity
```

Compiler vẫn bảo vệ actual capability khi resolve handle.

---

# 177.60. Compaction

Một arena/container có thể compact:

```text
A B _ C _ D
↓
A B C D
```

nếu external address không observable.

Handle-based identity giúp việc này dễ hơn.

---

# 177.61. Pointer-stable collections

Nếu FFI/API yêu cầu raw pointer stability:

```text
StableAddress<T>
```

hoặc explicit storage contract phải được dùng.

Compiler sẽ không:

```text
move
compact
relocate
```

trái contract.

---

# 177.62. Garbage collector

Axiom Core:

```text
NO GC
```

Không có tracing collector bắt buộc.

Nhưng library/application hoàn toàn có thể implement:

```text
GC heap
```

nếu cần.

Compiler vẫn coi GC heap như:

```text
External/Managed storage abstraction
```

với contract riêng.

---

# 177.63. Reference counting

Axiom Core:

```text
NO implicit RC
```

Nhưng:

```text
Rc<T>
Arc<T>
```

là library types.

Do đó programmer **chọn** khi cần shared ownership.

---

# 177.64. Why no implicit RC?

Vì implicit RC có:

```text
atomic/non-atomic increments
memory traffic
cycles
destruction timing complexity
```

và làm mọi object có thể mang hidden cost.

Axiom không muốn điều đó.

---

# 177.65. Why no GC?

GC có thể:

```text
pause
memory overhead
larger runtime
less predictable destruction
```

không phù hợp mục tiêu:

```text
systems + tiny binaries + deterministic resource management
```

Nhưng không cấm library/application-specific GC.

---

# 177.66. Allocation cost model

Compiler nên xem:

```text
allocation cost
```

không chỉ là function call.

Cost model có:

```text
latency
contention
cache miss
size class
zeroing
alignment
NUMA
TLB
page fault
```

---

# 177.67. Zeroing memory

OS/runtime đôi khi yêu cầu zero-initialization.

Axiom phải phân biệt:

```text
semantic initialization
```

và:

```text
physical zeroing
```

Nếu compiler chứng minh bytes sẽ được overwrite trước read, physical zeroing có thể bỏ.

---

# 177.68. Security zeroization

Ngược lại:

```text
Secret<T>
```

có explicit zeroization contract.

Compiler **không được** loại bỏ việc xóa memory chỉ vì:

```text
value no longer read
```

nếu zeroization là observable security contract.

---

# 177.69. Allocation and concurrency

Allocator phải tránh global lock nếu workload yêu cầu.

Possible architecture:

```text
Thread
 ↓
Thread-local cache
 ↓
Central allocator
 ↓
OS virtual memory
```

---

# 177.70. False sharing

Runtime/compiler có thể hỗ trợ:

```text
@cacheline
```

hoặc:

```text
CacheAligned<T>
```

ở system/performance layer.

Không biến cache line thành semantic property của mọi struct.

---

# 177.71. Memory reclamation

Shared/concurrent structures có thể dùng:

```text
HazardPointer
EpochBasedReclamation
RCU
Generation
```

đây là library/runtime mechanisms.

Compiler không cần hiểu toàn bộ algorithm, nhưng FFI/unsafe contracts phải khai báo đủ invariants.

---

# 177.72. EBR/RCU

Ví dụ:

```text
Reader
  ↓
epoch guard
  ↓
read shared node
```

Compiler chỉ cần biết capability/lifetime contract của abstraction.

Không cần programmer viết lifetime annotation.

---

# 177.73. Compiler's storage decision

Thứ tự chính thức:

```text
1. Storage-domain requirement
2. Ownership/capability validity
3. Stable-address requirement
4. Observable identity
5. Escape
6. Lifetime / Drop
7. ABI
8. Performance
```

Sau đó:

```text
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

---

# 177.74. Allocation strategy selection

Compiler có thể chọn:

```text
No allocation
↓
Stack/inline
↓
Arena/pool
↓
Thread-local
↓
General allocator
↓
OS virtual memory
```

tùy semantics và profile.

---

# 177.75. Allocation elision

Nếu:

```text
allocate
write
read
destroy
```

không có observable allocation identity/address:

```text
allocation may disappear
```

thành:

```text
SSA / stack / registers
```

---

# 177.76. Deallocation elision

Nếu compiler chứng minh:

```text
storage reclaimed automatically
or
whole arena dies
```

individual physical deallocations có thể được batch/eliminate.

Semantic Drop vẫn được bảo toàn.

---

# 177.77. Arena destruction optimization

Ví dụ:

```text
Arena
  A
  B
  C
```

nếu:

```text
A/B/C
```

trivial Drop:

```text
destroy Arena
```

có thể chỉ là:

```text
release one region
```

---

# 177.78. Non-trivial Drop

Nếu:

```text
A: Drop
B: Drop
C: Drop
```

compiler vẫn phải đảm bảo semantic:

```text
C
B
A
```

theo destruction order contract.

Physical deallocation có thể vẫn batch.

---

# 177.79. Allocation and ABI

Return:

```ax
fn make() -> BigObject
```

không có nghĩa:

```text
allocate BigObject
copy BigObject
return pointer
```

ABI có thể:

```text
caller-provided result slot
```

hoặc registers.

---

# 177.80. Caller allocation

Compiler có thể lower:

```text
make()
```

thành:

```text
caller allocates destination
callee constructs directly
```

không copy.

Đây là một trong những cơ chế quan trọng để Axiom đạt performance C/C++ mà không cần syntax phức tạp.

---

# 177.81. Move return

Semantic:

```text
return x
```

là:

```text
ownership transfer
```

không phải:

```text
physical memcpy
```

---

# 177.82. Copy return

Nếu `T: Copy`:

```text
return x
```

có semantic duplication.

Compiler vẫn có thể:

```text
register return
```

hoặc optimize physical representation.

---

# 177.83. Fragmentation mitigation hierarchy

Axiom nên ưu tiên:

```text
1. Allocation elimination
2. Stack/register promotion
3. Inline storage
4. Lifetime-aware arena
5. Fixed-size pool/slab
6. Thread-local allocation
7. General allocator
```

Điều này có tác động lớn hơn việc chỉ thay đổi address model.

---

# 177.84. Memory architecture cuối cùng

```text
                 Axiom Value
                     │
             Ownership / Capability
                     │
              Storage Requirement
                     │
          ┌──────────┼──────────┐
          ↓          ↓          ↓
       Inline      Local      Dynamic
          │          │          │
       register     stack    allocator
                                │
                    ┌───────────┼────────────┐
                    ↓           ↓            ↓
                  arena       pool         general
                    │           │            │
                    └───────────┴────┬───────┘
                                     ↓
                                virtual memory
```

---

# 177.85. Kết luận về “flat memory”

**Axiom nên giữ flat virtual address space**, nhưng **không dùng nó làm semantic memory model**.

Mô hình hoàn chỉnh:

```text
                    LANGUAGE
                       │
          ┌────────────┴────────────┐
          │                         │
       Ownership                 Capability
          │                         │
          └────────────┬────────────┘
                       ↓
                 Storage Domain
                       │
             ┌─────────┼─────────┐
             ↓         ↓         ↓
           Local     Dynamic   External
             │         │         │
          stack/    arena/pool  device/
          register  heap/slab   mmap/FFI
                       │
                       ↓
                 Flat Address Space
                       │
                       ↓
                    Hardware
```

Đây là hướng phù hợp với mục tiêu ban đầu của Axiom hơn rất nhiều so với:

```text
mọi object = heap object
```

hoặc:

```text
mọi object = pointer
```

hoặc:

```text
mọi object = GC object
```

---

# Invariants chính

### Memory

- **AMEMALLOC-20** — Allocation strategy is not part of ordinary type semantics.
- **AMEMALLOC-21** — Storage location is not determined solely by source-level type.
- **AMEMALLOC-22** — Flat virtual address space does not define allocation semantics.
- **AMEMALLOC-23** — Allocation identity is distinct from value identity.
- **AMEMALLOC-24** — Logical identity does not require stable physical address.
- **AMEMALLOC-25** — Address stability is an explicit contract.
- **AMEMALLOC-26** — Allocation elimination is permitted when unobservable.
- **AMEMALLOC-27** — Stack/register promotion cannot change observable semantics.
- **AMEMALLOC-28** — Physical storage reuse cannot create semantic aliasing.
- **AMEMALLOC-29** — Physical deallocation may be batched when Drop semantics are preserved.

### Allocator

- **AALLOC-20** — No mandatory global allocator.
- **AALLOC-21** — No mandatory GC.
- **AALLOC-22** — No implicit reference counting.
- **AALLOC-23** — Allocator implementations are replaceable.
- **AALLOC-24** — Foreign allocation/deallocation domains are explicit.
- **AALLOC-25** — Alignment requirements must be preserved.
- **AALLOC-26** — Allocation failure policy is profile/library configurable.
- **AALLOC-27** — Arena/pool/slab allocation must preserve ownership and Drop semantics.
- **AALLOC-28** — Device/external storage cannot be silently treated as ordinary host storage.
- **AALLOC-29** — Allocation optimizations cannot alter observable identity or address contracts.

### Fragmentation

- **AFRAG-20** — Flat address space does not guarantee absence of fragmentation.
- **AFRAG-21** — Lifetime-aware allocation is a primary fragmentation mitigation.
- **AFRAG-22** — Arena/pool/slab strategies may be selected independently of Core semantics.
- **AFRAG-23** — Compiler may eliminate allocations before allocator selection.
- **AFRAG-24** — Storage reuse is permitted when semantic lifetimes do not overlap.

---

# BOOTSTRAP-177 hoàn tất

Điểm quan trọng nhất được khóa lại là:

> **Axiom không cần “giải quyết fragmentation bằng một memory model kỳ diệu”. Nó giải quyết bằng việc compiler hiểu lifetime/escape/ownership đủ sâu để phần lớn allocation không cần tồn tại theo cách programmer tưởng tượng.**

Và điều này rất hợp với mục tiêu của bạn:

```text
Programmer:
    "Tôi cần một Vec / object / buffer."

Compiler:
    "Tôi quyết định nó cần register, stack, inline,
     arena, pool hay heap."

Programmer:
    "Tôi cần stable address."

Compiler:
    "Được, storage contract đã trở thành observable."

Programmer:
    "Tôi cần shared ownership."

Compiler:
    "Dùng Arc/Shared — chi phí này là explicit."

Programmer:
    "Tôi chỉ cần một value."

Compiler:
    "Không allocation."
```

Đây chính là hướng **“compiler hiểu nhiều hơn programmer phải viết”** mà Axiom đang theo đuổi.

---

## BOOTSTRAP-178 — Memory Resource, Virtual Memory, Mapping, Protection & Low-Level Memory API

Task tiếp theo nên đi xuống **tầng thấp hơn allocator**:

```text
Virtual Address Space
        ↓
Memory Mapping
        ↓
Pages
        ↓
Protection
        ↓
Commit / Reserve
        ↓
NUMA
        ↓
Huge Pages
        ↓
Guard Pages
        ↓
Shared Memory
        ↓
Memory-Mapped Files
        ↓
DMA / Device Memory
        ↓
Physical/Virtual address boundary
```

Đây sẽ là task quyết định **Axiom có đủ khả năng làm OS/kernel/database/engine/high-performance runtime hay không**, đồng thời phải đảm bảo các API low-level này không phá vỡ safe memory model.