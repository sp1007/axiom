# BOOTSTRAP-348 — AXIOM NATIVE MEMORY, ALLOCATOR & RESOURCE MANAGEMENT ENGINE

Sau `347 — Native System API, OS Abstraction & Platform Services`, bước tiếp theo nên đi thẳng vào một phần cực kỳ quan trọng đối với mục tiêu của Axiom:

> **Axiom phải có hệ thống cấp phát bộ nhớ và quản lý resource đủ mạnh để xây dựng OS/runtime/library/application mà không cần GC, không cần `new/delete`, không cần một allocator duy nhất và không tạo abstraction overhead.**

Đây không phải thay đổi memory model đã đóng băng. Đây là **implementation/standard-library architecture nằm trên memory model**.

---

# 1. Mục tiêu

Axiom cần hỗ trợ đồng thời:

```text
Stack
Register
Inline
Heap
Arena
Pool
Slab
Linear
Region
Shared Memory
Mapped Memory
Device Memory
Static Memory
Custom Allocator
```

nhưng programmer không bị bắt buộc học một hệ thống allocator phức tạp cho những chương trình thông thường.

Mục tiêu:

```text
Simple code
    ↓
reasonable default allocation
    ↓
Compiler + optimizer
    ↓
zero-cost where possible
```

Trong systems code:

```text
Explicit allocator
Explicit lifetime
Explicit storage policy
```

---

# 2. Không có "Axiom Heap"

Một sai lầm cần tránh:

```text
Axiom
  ↓
global heap
  ↓
malloc/free
```

Axiom không nên định nghĩa một heap duy nhất.

Thay vào đó:

```text
Memory System
├── General Allocator
├── Arena
├── Pool
├── Slab
├── Linear
├── Stack/Region
├── Virtual Memory
├── Shared Memory
├── Mapped Memory
└── Device Memory
```

Mỗi abstraction có semantic contract riêng.

---

# 3. Phân biệt 4 khái niệm

Axiom phải tách rõ:

```text
Storage
Allocation
Ownership
Lifetime
```

Ví dụ:

```text
Box<T>
```

không có nghĩa:

```text
"luôn malloc"
```

Nó có nghĩa:

> một `T` có ownership và dynamic-storage semantics.

Compiler có thể biến:

```text
let x = Box.make(value)
```

thành stack/register allocation nếu address không escape.

---

# 4. Allocator là một abstraction library

Không đưa allocator cụ thể vào language core.

Core chỉ cần semantic primitive tương ứng:

```text
ALLOC
REALLOC
DEALLOC
```

và storage/capability model.

Library định nghĩa:

```text
Allocator
```

---

# 5. Allocator Trait

Có thể có:

```text
trait Allocator {
    fn allocate(
        size: usize,
        align: usize
    ) -> Result<RawBlock, AllocError>

    fn deallocate(
        block: RawBlock
    )

    fn resize(
        block: RawBlock,
        new_size: usize
    ) -> Result<RawBlock, AllocError>
}
```

Nhưng đây là **semantic interface**, không nhất thiết phải là dynamic dispatch.

Mặc định:

```text
GenericAllocator<A>
```

được monomorphize.

---

# 6. Không bắt programmer truyền allocator mọi nơi

Không muốn:

```text
fn create_vector<A: Allocator>(
    allocator: A,
    ...
)
```

xuất hiện khắp application code.

Có hai tầng:

### Default

```text
Vec<T>
String
Map<K,V>
```

dùng default allocator.

### Explicit

```text
Vec<T, ArenaAllocator>
```

khi programmer cần kiểm soát.

Compiler/library phải làm cho explicit allocation là **lựa chọn**, không phải bureaucracy.

---

# 7. Allocator Context

Có thể hỗ trợ:

```text
AllocatorContext
```

nhưng không nên biến thành implicit global mutable state.

Ví dụ:

```text
with_allocator(arena) {
    ...
}
```

Compiler có thể truyền context theo cách tối ưu.

Quan trọng:

> allocator context không được làm alias/lifetime semantics mơ hồ.

---

# 8. Allocation Contract

Một allocation phải có:

```text
size
alignment
storage domain
ownership
lifetime
```

Ví dụ:

```text
Allocation {
    storage
    size
    alignment
    owner
}
```

Không cần programmer thao tác trực tiếp trong code bình thường.

---

# 9. RawBlock

Để xây allocator cấp thấp:

```text
RawBlock {
    address
    size
    alignment
}
```

phải thuộc unsafe/system layer.

Không được coi `RawBlock` là:

```text
view<T>
```

tự động.

Muốn biến thành typed memory phải có:

```text
initialize<T>()
```

hoặc tương đương.

---

# 10. Uninitialized Memory

Axiom đã có semantic:

```text
UNINIT
INIT
MOVED
DROPPED
```

Task này phải biến nó thành API có thể sử dụng.

Ví dụ:

```text
let block = allocator.allocate(...)

let value = block.initialize(MyStruct { ... })
```

Sau đó:

```text
view<MyStruct>
```

chỉ hợp lệ khi initialization đã được chứng minh.

---

# 11. Không cho đọc uninitialized memory

Ví dụ sai:

```text
let p = allocator.allocate(...)
let x = p.read<MyStruct>()
```

nếu chưa initialize.

Compiler:

```text
AXMEM001:
read from uninitialized storage
```

Unsafe có thể bypass ở tầng machine-level, nhưng sau khi tạo safe typed value:

```text
unsafe {
    ...
}
```

phải establish invariant.

---

# 12. Initialization State

Verifier cần mở rộng state:

```text
MemoryState {
    UNALLOCATED
    ALLOCATED_UNINIT
    INITIALIZED
    PARTIALLY_INITIALIZED
    MOVED
    DROPPED
    DEALLOCATED
}
```

Ví dụ:

```text
allocate
   ↓
ALLOCATED_UNINIT
   ↓ initialize
INITIALIZED
   ↓ move
MOVED
   ↓ drop
DROPPED
   ↓ deallocate
DEALLOCATED
```

---

# 13. Allocator và Drop

Nếu:

```text
Box<MyStruct>
```

mà `MyStruct` có Drop:

```text
deallocate
```

không được xảy ra trước:

```text
drop(MyStruct)
```

Pipeline:

```text
owner
 ↓
drop value
 ↓
release storage
```

không:

```text
release storage
 ↓
drop value
```

---

# 14. Box

`Box<T>` là abstraction quan trọng.

Semantic:

```text
Box<T>
```

là:

- owning
- dynamic-storage capable
- !Copy
- Drop
- Move
- addressable nếu contract yêu cầu

Nhưng:

```text
Box<T>
```

**không đảm bảo physical heap allocation**.

Compiler có thể optimize:

```text
Box allocation
→ stack
→ register
→ SSA
→ eliminated
```

nếu không quan sát được.

---

# 15. HeapBox

Nếu programmer thực sự cần:

> storage chắc chắn nằm trong heap/object allocator cụ thể

thì nên có abstraction khác:

```text
HeapBox<T, A>
```

hoặc library-level equivalent.

Semantic contract lúc này mới yêu cầu:

```text
dynamic storage
allocator A
stable allocation identity
```

Điều này tránh việc `Box` phải gánh mọi semantics.

---

# 16. Stable Address

Axiom đã xác định:

> stable address là storage contract.

Vì vậy:

```text
Vec<T>
```

không đảm bảo address ổn định.

```text
StableBox<T>
```

có thể đảm bảo.

Hoặc:

```text
PinnedStorage<T>
```

ở library layer nếu cần.

Không đưa `Pin<T>` vào Core.

---

# 17. Arena

Arena là abstraction cực kỳ quan trọng.

```text
Arena<T>
```

hoặc byte arena:

```text
Arena
```

Semantics:

```text
allocate many
release together
```

Ví dụ:

```text
let arena = Arena.new()

let a = arena.make(Node { ... })
let b = arena.make(Node { ... })

arena.reset()
```

Tất cả object thuộc arena có thể bị destroy cùng lúc.

---

# 18. Arena và Drop

Không được đơn giản:

```text
arena.reset()
```

rồi bỏ qua Drop.

Nếu objects có resource:

```text
File
Socket
MutexGuard
```

arena phải:

```text
drop objects
then release storage
```

hoặc arena phải có explicit contract:

```text
Arena<Trivial>
```

cho phép bulk destruction.

---

# 19. Trivial/Bulk-Drop Optimization

Compiler có thể phát hiện:

```text
all objects are trivially destructible
```

và biến:

```text
drop all
release arena
```

thành:

```text
release arena
```

Đây là ví dụ điển hình của:

> semantic safety + zero-cost optimization.

---

# 20. Region Allocation

Có thể cung cấp:

```text
Region
```

khác Arena ở semantics.

Region có:

```text
scope lifetime
```

Compiler biết:

```text
enter region
   ↓
allocations
   ↓
exit region
   ↓
bulk release
```

Không cần programmer gọi `free()` từng object.

---

# 21. Stack Arena

Axiom có thể hỗ trợ:

```text
StackArena
```

Ví dụ:

```text
with_stack_arena(64_KB) {
    ...
}
```

Compiler có thể lower thành:

```text
stack pointer adjustment
```

không cần heap.

---

# 22. Linear Allocator

Đặc biệt hữu ích cho:

- parser
- compiler
- game engine
- frame allocator
- temporary buffers
- serialization

API:

```text
LinearArena
```

Semantics:

```text
allocate
allocate
allocate
reset
```

Không có individual free.

---

# 23. Frame Allocator

Có thể là specialization:

```text
FrameArena
```

Mỗi frame:

```text
begin_frame()
...
end_frame()
```

Compiler/runtime không cần biết game engine semantics; đây chỉ là library.

---

# 24. Pool Allocator

Pool:

```text
Pool<T>
```

cấp phát object cùng kích thước.

```text
allocate()
free()
```

Đặc biệt hữu ích cho:

- ECS
- network connection
- AST node
- task object
- game entity

Compiler không nên tự động giả định Pool là allocator an toàn nếu ownership semantics không được thiết lập.

---

# 25. Slab Allocator

```text
Slab<T>
```

có:

```text
stable slot identity
generation
reuse detection
```

Rất phù hợp với:

```text
Handle<T>
```

Ví dụ:

```text
let id = slab.insert(entity)
```

sau khi remove:

```text
id
```

không thể vô tình trỏ tới object mới nếu generation khác.

---

# 26. Handle + Generation

Axiom đã định nghĩa logical identity.

Task này biến thành standard facility:

```text
Handle<T>
Generation
SlotMap<T>
Slab<T>
```

Ví dụ:

```text
Handle<Entity>
```

không phải pointer.

Representation có thể:

```text
index + generation
```

Compiler không coi nó là memory capability.

---

# 27. Fragmentation

Phải tránh tuyên bố:

> flat memory model = không fragmentation.

Task này cần phân biệt:

```text
Virtual Address Fragmentation
Physical Memory Fragmentation
Allocator Fragmentation
Object Lifetime Fragmentation
Cache Locality
```

Axiom allocator system phải cho phép chọn chiến lược phù hợp.

---

# 28. General Allocator

Axiom Standard Library có default:

```text
SystemAllocator
```

nhưng đây chỉ là implementation mặc định.

Có thể:

```text
Mimalloc-like
TLSF
jemalloc-like
buddy
segregated-fit
```

miễn là implementation đáp ứng Allocator contract.

Axiom không được semantic dependency vào một allocator cụ thể.

---

# 29. Per-Thread Allocation

High-performance allocator có thể:

```text
ThreadLocalArena
```

giảm contention.

Compiler/runtime không cần expose implementation detail.

---

# 30. NUMA

Systems API có thể hỗ trợ:

```text
NumaNode
NumaAllocator
MemoryAffinity
```

Ví dụ:

```text
allocate_on(node)
```

Nhưng chỉ là platform extension.

Không đưa NUMA vào Core.

---

# 31. Huge Pages

Virtual memory service:

```text
HugePage
LargePage
```

có thể yêu cầu capability:

```text
virtual_memory.huge_pages
```

Nếu OS không hỗ trợ:

```text
unsupported
```

không silently fallback nếu programmer yêu cầu strict mode.

---

# 32. Shared Memory

Resource:

```text
SharedMemory
```

phải có:

```text
ownership
mapping
permissions
lifetime
synchronization
```

Ví dụ:

```text
let region = SharedMemory.create(...)
let view = region.map_mut(...)
```

`view` vẫn tuân thủ capability model.

---

# 33. Memory-Mapped Files

```text
MappedFile
```

là resource combination:

```text
File
+
VirtualMemory
```

nhưng không nên giả lập thành một byte array.

Compiler phải biết:

```text
mapping may disappear
mapping may become invalid after unmap
```

và invalidate capabilities tương ứng.

---

# 34. Device Memory

Đã có GPU model.

Allocator architecture phải mở rộng:

```text
HostAllocator
DeviceAllocator
UnifiedAllocator
PinnedHostAllocator
```

Storage domain:

```text
HOST
DEVICE
SHARED
EXTERNAL
```

Không được để:

```text
DeviceBuffer
```

trở thành `Box<T>` giả.

---

# 35. DMA / External Memory

Một số systems cần memory do:

- GPU
- driver
- OS
- device
- foreign process

cấp.

Axiom:

```text
ExternalMemory<T>
```

phải có explicit ownership contract.

Compiler không tự assume:

```text
free()
```

được phép.

---

# 36. Allocator Reentrancy

Allocator contract phải mô tả:

```text
thread-safe
reentrant
signal-safe
interrupt-safe
async-safe
```

Không phải allocator nào cũng có tất cả.

Ví dụ:

```text
InterruptAllocator
```

có contract rất khác:

```text
GeneralAllocator
```

---

# 37. Allocation Failure

Không được mặc định:

```text
allocation failure = panic
```

API phải cho phép:

```text
Result<T, AllocError>
```

và profile policy:

```text
Abort
Panic
ReturnError
OOMHandler
```

Freestanding code có thể chọn:

```text
OOM → abort
```

hoặc:

```text
OOM → custom handler
```

---

# 38. No Hidden Allocation

Axiom cần tooling để phát hiện:

```text
allocation
```

ẩn.

Ví dụ:

```text
Vec.push()
```

có thể allocate.

Compiler performance diagnostics:

```text
AXPERF120:
operation may allocate
```

Nhưng không nên biến allocation thành compile error mặc định.

Programmer có thể yêu cầu:

```text
@noalloc
fn realtime_step() {
    ...
}
```

Compiler verify:

```text
no dynamic allocation
```

trong function/call graph.

---

# 39. Allocation Effect

Effect system bổ sung:

```text
Allocate
Deallocate
```

đã có từ trước.

Task này làm chúng trở thành semantic effect rõ ràng.

Ví dụ:

```text
fn foo()
```

có effect:

```text
Read
Write
Allocate
```

Compiler có thể phát hiện:

```text
@noalloc fn foo()
```

nhưng `foo()` gọi:

```text
Vec.push()
```

có thể allocate.

=> compile error nếu allocation không chứng minh được đã eliminated.

---

# 40. Stack Usage

Tương tự:

```text
@nostackalloc
```

có thể là future profile.

Nhưng trước mắt cần:

```text
StackUsageAnalysis
```

để compiler biết:

```text
static
bounded
dynamic
unknown
```

Điều này quan trọng cho embedded/realtime.

---

# 41. Allocation Elimination

Compiler có thể:

```text
Box<T>
```

→ eliminate allocation.

```text
Vec<T>
```

→ stack promote nếu size bounded.

```text
String
```

→ SSO hoặc stack storage.

```text
Arena
```

→ stack region.

Tất cả đều hợp lệ nếu không thay đổi observable semantics.

---

# 42. Small Object Optimization

Library types có thể sử dụng:

```text
InlineStorage<T, N>
```

Ví dụ:

```text
SmallVec<T, 8>
SmallString<64>
```

Không cần runtime allocation nếu dữ liệu nhỏ.

---

# 43. Storage Policy

Một type có thể parameterize:

```text
Buffer<T, StoragePolicy>
```

Ví dụ:

```text
Heap
Arena
Inline
Static
Device
External
```

Nhưng syntax application-level nên đơn giản.

---

# 44. Resource Management

Không chỉ memory.

Axiom cần unified abstraction:

```text
Resource<T>
```

cho:

```text
File
Socket
Process
Mutex
MemoryMap
GPUBuffer
DeviceHandle
DynamicLibrary
```

Resource có:

```text
Acquire
Own
Use
Move
Drop
Release
```

Không được dùng GC.

---

# 45. Resource Traits

Các trait:

```text
Owned
Disposable
Closable
Flushable
Mappable
Send
Share
```

không được gộp thành một trait khổng lồ.

Ví dụ:

```text
File
```

có:

```text
Drop
Closable
Readable
Writable
```

nhưng:

```text
Socket
```

có thể:

```text
Drop
Closable
```

---

# 46. Explicit Close

Với resource cần báo lỗi:

```text
file.close() -> Result<unit, IoError>
```

Sau đó Drop vẫn đảm bảo cleanup.

Điều này giữ invariant:

> Drop không phải error propagation mechanism.

---

# 47. Resource Leak Detection

Compiler có thể phát hiện một số leak logic.

Ví dụ:

```text
OwnedResource
```

escape vào:

```text
global
foreign
external
```

được ghi nhận.

Không phải mọi leak đều là compile error vì intentionally leaked resources có use cases.

Có:

```text
leak(resource)
```

explicit unsafe/system operation.

---

# 48. Resource Graph

Compiler có thể xây:

```text
ResourceGraph
```

Ví dụ:

```text
Process
 ├── Pipe
 ├── File
 └── SharedMemory
```

Drop order phải được đảm bảo.

Nếu:

```text
Pipe
```

phụ thuộc:

```text
Process
```

thì ownership graph có thể biểu diễn quan hệ.

---

# 49. Allocator Safety

Một allocator implementation không được tự động trở thành safe chỉ vì implement trait.

Ví dụ allocator custom:

```text
unsafe impl Allocator for MyAllocator
```

có thể yêu cầu chứng minh:

- alignment
- valid allocation
- no overlapping ownership
- correct deallocation
- resize correctness
- thread contract

Đây là **unsafe contract**, không phải compiler trust mù quáng.

---

# 50. CompilerDB mở rộng

```text id="a2dypo"
AllocatorDB
AllocationDB
StoragePolicyDB
ResourceDB
ResourceContractDB
MemoryRegionDB
ArenaDB
PoolDB
SlabDB
VirtualMemoryDB
SharedMemoryDB
DeviceMemoryDB
AllocationEffectDB
AllocationProofDB
StackUsageDB
ResourceGraphDB
```

---

# 51. MIR integration

MIR đã có:

```text id="q7f8w3"
ALLOC
DEALLOC
DROP
```

Task này mở rộng:

```text id="p0t1xg"
ALLOC {
    size
    alignment
    allocator
    storage_domain
}

REALLOC {
    allocation
    new_size
    allocator
}

DEALLOC {
    allocation
    allocator
}
```

và:

```text id="8h52ph"
INIT
MOVE
DROP
```

phải tương tác với allocation state.

---

# 52. Optimization contract

Compiler được phép transform:

```text id="g1qk6d"
ALLOC
...
DEALLOC
```

thành:

```text id="7m0hby"
stack storage
```

nếu:

```text
address does not escape
allocator behavior not observable
allocation failure not observable
storage identity not observable
```

Nếu allocation failure có thể quan sát:

```text
Result<...>
```

thì compiler không được đơn giản xóa allocation nếu làm thay đổi behavior.

---

# 53. Allocation Failure Observability

Đây là điểm rất quan trọng.

Ví dụ:

```text id="3j8xwo"
let x = Box.try_new(value)?
```

Allocation failure là observable.

Compiler chỉ được eliminate physical allocation nếu vẫn bảo toàn:

```text
success/failure semantics
```

Trong khi:

```text
let x = Box.new(value)
```

có thể có profile:

```text
panic on OOM
```

và optimizer có nhiều freedom hơn.

---

# 54. Allocator ABI

Nếu FFI trả allocation cho Axiom:

```text id="3m08vi"
extern "C" fn create_buffer() -> *mut u8
```

Axiom không được tự động:

```text
Box.from_raw()
```

và sau đó `deallocate()` bằng Axiom allocator.

Phải có:

```text
allocation domain
```

Ví dụ:

```text id="a6n4r4"
CAllocator
WindowsHeap
COMAllocator
AxiomAllocator
ForeignAllocator
```

Mỗi domain có ownership/deallocation contract.

---

# 55. FFI Resource Ownership

Metadata:

```text id="q6nq92"
@returns_owned
@returns_borrowed
@allocator(CAllocator)
```

hoặc equivalent semantic metadata.

Compiler wrapper có thể biến:

```text
foreign allocation
```

thành safe resource abstraction.

---

# 56. Concurrency

Allocator có thể có:

```text
ThreadSafe
ThreadLocal
SingleThread
LockFree
Blocking
```

Nhưng đây là implementation capability.

Không được suy ra:

```text
Allocator => Share
```

hay:

```text
Allocator => Send
```

tự động.

---

# 57. Async

Không allocator nào được phép:

```text
block
```

trong async task nếu API contract yêu cầu nonblocking.

Có thể có:

```text
AsyncAllocator
```

nhưng không đưa vào Core.

---

# 58. GPU

GPU allocator:

```text
DeviceAllocator
```

phải tích hợp:

```text
DeviceBuffer<T>
DeviceView<T>
mut_device_view<T>
```

với:

```text
GpuStorageDomain
```

Không được cho:

```text
view<T>
```

host tự động truy cập device memory.

---

# 59. CLI

```bash
axiom alloc inspect
axiom alloc profile
axiom alloc trace
axiom memory layout
axiom memory regions
axiom resource graph
```

Ví dụ:

```bash
axiom memory layout app
```

có thể:

```text
Stack
Heap
Arena
Static
TLS
Mapped
Device
```

---

# 60. Diagnostics

Ví dụ:

```text
AXMEM021:
allocation may outlive allocator `arena`

owner:
    arena

escaping value:
    Node

required:
    storage lifetime >= value lifetime
```

Hoặc:

```text
AXMEM034:
attempt to deallocate memory using incompatible allocator

allocation domain:
    ForeignAllocator

requested:
    AxiomAllocator
```

---

# 61. Invariants

### `AMEM-01`
Allocation and ownership are distinct concepts.

### `AMEM-02`
Storage location is not determined solely by type.

### `AMEM-03`
Allocator selection must be explicit when allocation behavior is semantically observable.

### `AMEM-04`
No safe program may read uninitialized storage.

### `AMEM-05`
Initialization state must be tracked independently from allocation state.

### `AMEM-06`
Drop precedes deallocation for owning values.

### `AMEM-07`
Deallocation must use the allocation's valid allocator domain.

### `AMEM-08`
Allocator mismatch is invalid.

### `AMEM-09`
`Box<T>` does not inherently guarantee physical heap allocation.

### `AMEM-10`
Stable address requires an explicit storage contract.

### `AMEM-11`
Arena destruction must preserve Drop semantics.

### `AMEM-12`
Bulk destruction may be optimized away only when semantically valid.

### `AMEM-13`
Allocation failure semantics are observable when the API exposes them.

### `AMEM-14`
Compiler allocation elimination must preserve allocation failure semantics.

### `AMEM-15`
Compiler allocation elimination must preserve observable storage identity.

### `AMEM-16`
Raw allocation APIs are unsafe/system-level.

### `AMEM-17`
Safe typed access requires valid initialization.

### `AMEM-18`
Allocator thread-safety must be explicit.

### `AMEM-19`
Allocator `Send`/`Share` properties are not automatic.

### `AMEM-20`
Foreign allocations cannot be released using an unrelated allocator.

### `AMEM-21`
Memory-mapped storage participates in capability validity.

### `AMEM-22`
Unmapping invalidates dependent capabilities.

### `AMEM-23`
Device memory is a distinct storage domain.

### `AMEM-24`
Host and device memory cannot be implicitly aliased.

### `AMEM-25`
Allocation effects participate in effect analysis.

### `AMEM-26`
`@noalloc` requires whole-call-graph proof.

### `AMEM-27`
Stack usage is analyzable independently from heap allocation.

### `AMEM-28`
Resource cleanup is deterministic.

### `AMEM-29`
Explicit leak requires explicit semantic operation.

### `AMEM-30`
Allocator abstractions must not require a monolithic runtime.

---

# 62. Definition of Done

`BOOTSTRAP-348` hoàn thành khi Axiom có:

```text
✓ Allocator semantic contract
✓ Default allocator
✓ Custom allocator model
✓ Box integration
✓ Explicit heap-storage contract
✓ Raw allocation API
✓ Initialization tracking
✓ Uninitialized-memory safety
✓ Arena
✓ Region allocator
✓ Stack arena
✓ Linear allocator
✓ Pool allocator
✓ Slab allocator
✓ Handle/generation integration
✓ General allocator
✓ Thread-local allocator
✓ Virtual-memory integration
✓ Shared-memory integration
✓ Memory-map integration
✓ Device-memory integration
✓ Resource ownership model
✓ Explicit close semantics
✓ Resource graph
✓ Foreign allocation domains
✓ FFI allocation contracts
✓ Allocation effects
✓ @noalloc verification
✓ Stack usage analysis
✓ Allocation elimination
✓ Escape-based storage promotion
✓ OOM policy
✓ Allocator concurrency contracts
✓ Async allocator constraints
✓ GPU allocator integration
✓ CompilerDB integration
✓ MIR integration
✓ Diagnostics
✓ Profiling/tracing
✓ Conformance tests
```

---

# 63. Kiến trúc bộ nhớ hoàn chỉnh lúc này

Sau `348`, mô hình của Axiom trở nên khá hoàn chỉnh:

```text
                 AXIOM VALUE
                     │
             ┌───────┴────────┐
             │                │
         Ownership        Capability
             │                │
             └───────┬────────┘
                     │
                  Storage
                     │
       ┌─────────────┼─────────────┐
       │             │             │
     Stack         Inline        Dynamic
                                   │
                    ┌──────────────┼──────────────┐
                    │              │              │
                  Heap           Arena           Pool
                    │              │              │
                  Slab          Linear          Region
                    │
             Custom Allocator
                    │
       ┌────────────┼─────────────┐
       │            │             │
   Host Memory  Shared Memory  Device Memory
       │            │             │
       └────────────┴─────────────┘
                    │
              Virtual Memory
                    │
                OS / Hardware
```

Điểm quan trọng nhất:

> **Axiom không chọn giữa “GC”, “borrow checker” và “manual memory” theo kiểu nhị phân.**

Axiom dùng:

**ownership + capability + compiler lifetime analysis + deterministic Drop**

ở semantic level, sau đó cho phép:

**heap / arena / pool / slab / stack / virtual memory / device memory**

ở storage/allocation level.

Vì vậy programmer có thể viết code rất đơn giản:

```text
let users = Vec<User>()
```

nhưng compiler vẫn có đủ thông tin để biến nó thành:

```text
register
→ stack
→ inline
→ arena
→ heap
```

tùy escape/lifetime/optimization.

Đây chính là hướng phù hợp nhất với mục tiêu ban đầu của Axiom: **không bắt programmer gánh complexity của memory management, nhưng cũng không hy sinh quyền kiểm soát của systems programmer.**