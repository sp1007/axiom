# BOOTSTRAP-178 — Virtual Memory, Memory Mapping, Protection & Low-Level Memory Resources
**FROZEN / COMPLETED**

Task này hoàn thiện tầng thấp hơn allocator.

Nguyên tắc trung tâm:

> **Allocator quản lý storage; Virtual Memory Manager quản lý address space và mapping. Hai tầng này phải độc lập.**

Axiom cần đủ mạnh để viết allocator, database engine, game engine, runtime, embedded software và cả kernel/system software mà không biến toàn bộ ngôn ngữ thành một ngôn ngữ pointer-centric.

---

## 178.1. Ba tầng memory

Axiom phân biệt:

```text
                 Application Value
                       │
                 Ownership/Capability
                       │
                Storage Resource
                       │
              ┌────────┴────────┐
              │                 │
          Allocator        Memory Resource
              │                 │
       arena/pool/heap     pages/mapping
                                │
                         Virtual Address Space
                                │
                         OS / MMU / Hardware
```

Không được nhập ba tầng này thành một abstraction duy nhất.

---

# 178.2. Virtual address space

Virtual address là:

> **machine-level address identity**, không phải ownership.

Ví dụ:

```text
0x10000000
```

chỉ là một địa chỉ trong address space.

Nó không tự động chứng minh:

```text
owner
valid memory
initialized T
alignment
lifetime
```

---

# 178.3. Raw pointer và virtual address

Axiom đã có:

```text
*const T
*mut T
```

nhưng:

```text
integer address
```

không tự động trở thành valid pointer.

Ví dụ:

```text
let addr: usize = 0x1000;
```

không cho phép:

```text
*p
```

trong safe code.

Muốn chuyển:

```text
usize → raw pointer
```

phải qua `unsafe/system` boundary.

---

# 178.4. Memory mapping là resource

Một mapping nên có semantic abstraction kiểu:

```text
MemoryMapping
```

chứa concept:

```text
virtual address range
size
protection
backing resource
mapping lifetime
```

Không nhất thiết expose implementation fields trực tiếp.

---

# 178.5. Reserve ≠ Commit

Axiom phải phân biệt:

```text
reserve
commit
```

Ví dụ:

```text
reserve 1 GB virtual address
commit 16 MB physical/backing memory
```

Đây là capability rất hữu ích cho:

```text
large arena
JIT
database
memory pool
game world
```

---

# 178.6. Reserved address range

Concept:

```text
VirtualRegion
```

có thể đảm bảo:

```text
[base, base + size)
```

được giữ cho resource đó.

Nhưng chưa nhất thiết có backing memory.

---

# 178.7. Commit

Commit biến một phần region thành:

```text
accessible backing
```

theo platform contract.

Ví dụ:

```text
reserve:
████████████████████████

commit:
████░░░░░░░░░░░░░░░░░░░
```

---

# 178.8. Decommit

Có thể:

```text
commit
   ↓
use
   ↓
decommit
```

mà vẫn giữ virtual address reservation.

Điều này cực hữu ích cho:

```text
sparse structures
large arenas
stacks
databases
```

---

# 178.9. Release

Khác với decommit:

```text
release
```

trả lại virtual address range.

Concept:

```text
reserve → commit → decommit → release
```

không được nhập thành một thao tác duy nhất.

---

# 178.10. Page

Memory protection/mapping được quản lý theo:

```text
Page
```

hoặc target-specific granularity.

Compiler không nên giả định page size cố định.

Có thể:

```text
4 KiB
16 KiB
64 KiB
...
```

tùy target.

---

# 178.11. Page size query

System API:

```ax
page_size()
```

hoặc tương đương phải trả về runtime/platform property.

Compiler không hard-code.

---

# 178.12. Protection

Memory region có protection:

```text
READ
WRITE
EXECUTE
```

và có thể:

```text
NONE
```

Các combination phải được target/system layer kiểm soát.

---

# 178.13. W^X

Axiom system layer nên hỗ trợ policy:

> **Writable memory không đồng thời executable trong normal hardened configurations.**

Tức:

```text
RW
```

và:

```text
RX
```

thay vì:

```text
RWX
```

trừ khi platform/security configuration cho phép.

---

# 178.14. JIT

JIT cần:

```text
RW
 ↓
write code
 ↓
change protection
 ↓
RX
```

Compiler/runtime phải cung cấp API rõ ràng cho việc này.

Không nên cho:

```text
Box<u8> → executable code
```

một cách ngầm định.

---

# 178.15. Execute permission là storage property

Một vùng memory:

```text
READ | WRITE
```

không có nghĩa có thể execute.

Code storage:

```text
READ | EXECUTE
```

là resource khác về security contract.

---

# 178.16. MemoryMapping ownership

Mapping nên có ownership:

```text
mapping owns mapping resource
```

Khi Drop:

```text
unmap
```

theo platform contract.

Nhưng physical memory backing có thể thuộc resource khác.

Do đó:

```text
Mapping ownership
```

không nhất thiết bằng:

```text
Backing memory ownership
```

---

# 178.17. Shared mapping

Hai processes có thể map cùng backing:

```text
Process A
   │
   └── virtual mapping A ──┐
                           │
                      shared backing
                           │
   ┌── virtual mapping B ──┘
   │
Process B
```

Hai virtual addresses có thể khác nhau.

---

# 178.18. Shared memory không tự đồng bộ

Shared memory:

```text
≠ synchronization
```

Muốn synchronization cần:

```text
atomic
mutex
semaphore
futex
channel
```

hoặc mechanism tương ứng.

---

# 178.19. Memory mapping và capability

Một mapping có thể tạo:

```text
view<T>
mut_view<T>
```

nhưng chỉ sau khi compiler/system contract biết:

```text
address
alignment
size
initialization
protection
```

---

# 178.20. Mapping arbitrary memory

System API có thể có dạng conceptual:

```ax
unsafe fn map_raw(...)
```

nhưng API safe nên tạo abstraction có invariant rõ ràng.

Ví dụ:

```ax
MappedRegion
```

sau khi tạo thành công có thể cung cấp:

```text
view<u8>
mut_view<u8>
```

theo protection.

---

# 178.21. Memory protection và capability

Đây là một điểm rất đẹp trong Axiom:

```text
OS protection
+
Axiom capability
```

có thể phối hợp.

Ví dụ:

```text
READ-only mapping
```

không nên tạo được:

```text
mut_view<T>
```

trong safe abstraction.

---

# 178.22. Nhưng protection không thay thế compiler safety

Ngược lại:

```text
RW page
```

không có nghĩa programmer được phép:

```text
mutate arbitrary T
```

Compiler vẫn phải kiểm tra:

```text
type
alignment
initialization
ownership
capability
lifetime
```

---

# 178.23. Uninitialized mapped memory

Mapping anonymous memory thường ban đầu không phải semantic `T`.

Axiom không được cho:

```text
map<T>()
```

đồng nghĩa:

```text
initialized T[]
```

một cách tự động.

---

# 178.24. Raw byte storage

Safe abstraction ban đầu nên là:

```text
RawStorage
```

hoặc:

```text
view<u8>
mut_view<u8>
```

Sau đó construct:

```text
T
```

bằng initialization operation.

---

# 178.25. Initialization transition

Conceptually:

```text
UNINIT
  │
  │ initialize(T)
  ↓
INIT<T>
```

Verifier phải hiểu transition.

---

# 178.26. Destruction transition

```text
INIT<T>
   │
   │ drop
   ↓
UNINIT
```

nếu storage vẫn tồn tại.

Sau đó có thể:

```text
UNINIT
 ↓
new T
```

---

# 178.27. Reusing mapped memory

Điều này rất quan trọng cho allocator/object pool.

```text
slot
 ↓
T
 ↓
drop T
 ↓
U
```

Axiom semantic model phải cho phép nếu:

```text
alignment
size
initialization
ownership
capability
```

đều hợp lệ.

---

# 178.28. Memory resource abstraction

Nên có một abstraction cấp thấp:

```text
MemoryResource
```

với các capability:

```text
reserve
commit
decommit
release
protect
map
unmap
```

Nhưng không nên bắt allocator API phải trực tiếp expose toàn bộ.

---

# 178.29. Allocator trên MemoryResource

Kiến trúc:

```text
MemoryResource
      │
      ├── VirtualMemoryResource
      ├── OSMappingResource
      ├── DeviceMemoryResource
      └── ExternalMemoryResource
              │
              ↓
          Allocator
              │
       ┌──────┼──────┐
       ↓      ↓      ↓
     Arena   Pool   GeneralHeap
```

---

# 178.30. Huge pages

System layer có thể request:

```text
HugePage
```

cho workload:

```text
database
large tensor
GPU staging
large sequential buffers
```

nhưng không guarantee nếu OS không hỗ trợ.

---

# 178.31. Huge page là optimization/resource property

Không được để:

```text
HugePage<T>
```

thay đổi semantic type của `T`.

Nó chỉ thay đổi storage resource.

---

# 178.32. Guard pages

Một vùng có thể đặt:

```text
NO_ACCESS
```

ở đầu/cuối:

```text
[GUARD][DATA][GUARD]
```

rất hữu ích cho:

```text
stack overflow
buffer overrun detection
allocator debugging
```

---

# 178.33. Guard page không phải language safety

Guard page chỉ bắt một số lỗi ở runtime.

Axiom safe verifier vẫn phải ngăn lỗi trước đó.

---

# 178.34. Stack memory

Stack cũng có thể được xem như:

```text
VirtualMemoryResource
```

ở system/runtime level.

Một thread có:

```text
stack reservation
stack committed region
```

và có thể grow hoặc fixed tùy platform.

---

# 178.35. Fiber stack

Fiber:

```text
Fiber
 ↓
owned stack resource
```

có thể dùng:

```text
guard page
```

để phát hiện overflow.

---

# 178.36. Async Future không bắt buộc stack

Đã frozen:

```text
Future
```

là stackless state machine.

Do đó:

```text
async task
```

không mặc định tạo stack riêng.

---

# 178.37. Fiber vs Future

```text
Fiber
→ stackful
→ explicit stack storage

Future
→ stackless
→ state-machine storage
```

Hai mô hình không nên nhập làm một.

---

# 178.38. Memory-mapped files

API:

```text
map_file(file)
```

có thể tạo:

```text
MappedFile
```

nhưng semantics phải phân biệt:

```text
memory contents
vs
file persistence
```

---

# 178.39. Memory mapping không đồng nghĩa persistence

Write vào mapping:

```text
memory changed
```

không nhất thiết có nghĩa:

```text
file durably stored
```

Cần explicit:

```text
flush
sync
durable_sync
```

tùy abstraction.

---

# 178.40. Database use case

Điều này cho phép Axiom viết database engine kiểu:

```text
file
 ↓
mmap
 ↓
view<u8>
 ↓
structured page
 ↓
typed access
```

mà không cần copy toàn bộ file vào heap.

---

# 178.41. Endianness

Mapped file/wire format không được phụ thuộc native memory representation.

Ví dụ:

```text
disk format = little endian
CPU = big endian
```

phải decode explicit.

Memory representation và serialization vẫn là hai khái niệm khác nhau.

---

# 178.42. DMA

DMA buffer là:

```text
External/Device storage
```

có contract về:

```text
alignment
addressability
cache coherence
ownership
synchronization
lifetime
```

Không được coi nó là ordinary `Vec<T>`.

---

# 178.43. Device memory

Đã frozen:

```text
HOST
DEVICE
SHARED
LOCAL
PRIVATE
CONSTANT
EXTERNAL
```

storage domains.

Một `DeviceBuffer<T>` không tự động chuyển thành:

```text
view<T>
```

trên CPU.

---

# 178.44. Host/device transfer

Phải explicit:

```text
upload
download
copy_to_device
copy_to_host
```

hoặc abstraction tương đương.

Compiler có thể optimize/eliminate copy khi chứng minh an toàn.

---

# 178.45. Pinned memory

System/GPU layer có thể có:

```text
PinnedHostBuffer<T>
```

nhưng đây là storage contract:

```text
physical/virtual mapping constraints
```

không phải Core type property của `T`.

---

# 178.46. NUMA

Memory resource có thể hỗ trợ:

```text
allocate_on_numa(node)
```

và:

```text
bind_thread(node)
```

ở system layer.

Compiler optimization có thể dùng metadata:

```text
NUMA locality
```

nhưng semantics không phụ thuộc nó.

---

# 178.47. Cache coherence

Ordinary shared memory semantics vẫn tuân theo Axiom memory model:

```text
atomic ordering
happens-before
synchronization
```

NUMA không tạo ra một memory model khác.

---

# 178.48. Physical address

Physical address API phải nằm trong:

```text
unsafe/system/kernel
```

vì ordinary application không có quyền/khả năng kiểm soát physical mapping.

---

# 178.49. Physical address ≠ virtual address

Axiom tuyệt đối không được cho phép giả định:

```text
virtual == physical
```

hoặc:

```text
virtual address + offset
→ physical address + offset
```

---

# 178.50. Kernel profile

Trong kernel/freestanding profile, Axiom có thể expose:

```text
PhysicalAddress
VirtualAddress
PageTable
Page
Mapping
```

nhưng đây là system-level abstractions.

---

# 178.51. Page tables

Kernel code có thể cần:

```text
map_page
unmap_page
set_permissions
translate
```

Những API này nằm trong:

```text
std::os
std::kernel
```

hoặc system package, không nằm trong ordinary Core.

---

# 178.52. TLB

TLB là hardware implementation detail.

Axiom không cần semantic type:

```text
TLBFlush<T>
```

Nhưng system API có thể expose:

```text
flush_tlb()
```

ở unsafe/kernel layer nếu target cần.

---

# 178.53. Memory barriers

Đã frozen:

```text
compiler barrier
CPU fence
atomic ordering
```

là ba khái niệm khác nhau.

Không được dùng:

```text
volatile
```

để thay thế synchronization.

---

# 178.54. Volatile mapped I/O

Memory-mapped device registers:

```text
volatile read
volatile write
```

là system/unsafe operations.

Ví dụ:

```text
device register
```

không được optimize thành:

```text
cached ordinary load
```

---

# 178.55. MMIO

Axiom system layer phải hỗ trợ abstraction kiểu:

```text
Mmio<T>
```

với contract:

```text
volatile
alignment
address
access width
ordering
```

Không cho phép ordinary compiler optimization phá semantics.

---

# 178.56. MMIO ≠ RAM

Đây là distinction bắt buộc:

```text
RAM
≠
MMIO
```

Một địa chỉ có thể đọc/ghi nhưng mỗi access có side effect.

---

# 178.57. Memory-mapped device resource

Conceptual:

```text
DeviceRegion
```

có:

```text
read<T>
write<T>
volatile_read<T>
volatile_write<T>
```

tùy contract.

---

# 178.58. Capability-based mapping

Safe wrapper có thể expose:

```text
ReadOnlyMapping
WritableMapping
ExecutableMapping
MmioMapping
```

để compiler/type system thấy access class.

Đây là cách đưa OS-level capability vào Axiom mà không biến tất cả thành pointer syntax.

---

# 178.59. Protection transition

Một mapping có thể đổi:

```text
RW
→
RX
```

nhưng phải là explicit operation.

Đặc biệt quan trọng cho:

```text
JIT
dynamic linker
runtime code generation
```

---

# 178.60. Code generation security

Compiler/runtime không được âm thầm tạo:

```text
RWX
```

memory chỉ vì cần executable buffer.

Target security policy có thể reject.

---

# 178.61. Memory resource lifetime

Một view:

```text
view<u8>
```

trên mapping:

```text
MappedRegion
```

không được tồn tại sau:

```text
unmap
```

Verifier dùng chính capability provenance model đã frozen.

---

# 178.62. Unmap với active view

Nếu:

```text
region
  └── view
```

đang sống:

```text
unmap(region)
```

phải bị reject trong safe code.

Đây chính là ví dụ cho thấy memory mapping hoàn toàn có thể tích hợp với memory model hiện tại mà không cần lifetime syntax.

---

# 178.63. Remap

Một region có thể:

```text
unmap
map
```

nhưng compiler phải coi mapping identity đã thay đổi.

Không được giữ safe capability cũ qua resource transition nếu contract không cho phép.

---

# 178.64. Memory resource invalidation

Các thao tác:

```text
decommit
unmap
protect
resize
remap
```

có thể invalidate capability.

Compiler/library contract phải khai báo:

```text
which regions
which capabilities
```

bị ảnh hưởng.

---

# 178.65. Resource graph

Compiler có thể biểu diễn:

```text
MemoryResource
      │
      ├── Mapping
      │      ├── view A
      │      └── view B
      │
      └── Allocation
             └── object
```

Khi resource chết:

```text
dependents must be gone
```

---

# 178.66. Mapping và Drop

`MappedRegion` có thể có:

```text
Drop → unmap
```

nhưng physical pages có thể:

```text
remain cached
remain shared
belong to file
```

Drop chỉ kết thúc mapping ownership.

---

# 178.67. Resource hierarchy

Kiến trúc hoàn chỉnh:

```text
VirtualAddressSpace
        │
        ├── Reservation
        │       │
        │       └── Mapping
        │              │
        │              └── Storage
        │
        └── Mapping
               │
               ├── File
               ├── Anonymous
               ├── SharedMemory
               ├── Device
               └── External
```

Allocator xây trên storage/resource này.

---

# 178.68. API layering

Không nên đưa tất cả API vào `std`.

Nên phân tầng:

```text
std::memory
    safe allocation/storage abstractions

std::os::memory
    virtual memory / mapping

std::device::memory
    GPU/device resources

std::kernel::memory
    physical/page-table/MMIO
```

---

# 178.69. Safe / unsafe boundary

### Safe

```text
Box
Vec
Arena
Pool
MappedFile
SharedMemory
DeviceBuffer
```

nếu abstraction giữ invariant.

### Unsafe/system

```text
raw virtual address
physical address
page table
arbitrary map
MMIO
raw DMA
arbitrary protection transition
integer → pointer
```

---

# 178.70. Không cần pointer syntax cho memory API

Programmer bình thường có thể viết:

```ax
let region = VirtualRegion.reserve(size)?;
let map = region.commit(ReadWrite)?;
let bytes = map.bytes_mut();
```

thay vì:

```text
void*
mmap
munmap
reinterpret_cast
pointer arithmetic
```

Compiler vẫn có thể generate machine-level code tương ứng.

---

# 178.71. Low-level escape hatch vẫn đầy đủ

Kernel/system programmer vẫn có:

```ax
unsafe {
    let p = address_of(...);
    ...
}
```

và các primitive system-level.

Axiom không hy sinh low-level control để đổi lấy safety.

---

# 178.72. Memory model cuối cùng

Ta có thể chốt toàn bộ tầng memory như sau:

```text
                         Axiom Program
                              │
                  Value / Ownership / Capability
                              │
                     ┌────────┴────────┐
                     │                 │
                  Storage           Identity
                     │                 │
             ┌───────┼───────┐         │
             │       │       │         │
           Local   Dynamic External   Logical
             │       │       │         │
          stack   allocator device     Handle
          inline     │       mmap
          register   │
                     ↓
             Memory Resource
                     │
          ┌──────────┼──────────┐
          ↓          ↓          ↓
       Arena       Pool       Heap
          │          │          │
          └──────────┼──────────┘
                     ↓
              Virtual Memory
                     │
          ┌──────────┼──────────┐
          ↓          ↓          ↓
       Mapping     Pages      Protection
          │
      ┌───┼────┬──────┐
      ↓   ↓    ↓      ↓
     RAM File Shared Device
                     │
                  Hardware
```

---

# 178.73. Các invariant được khóa

### Virtual memory

- **AVM-20** — Virtual addresses are machine-level identities, not ownership.
- **AVM-21** — Integer addresses do not establish safe pointer provenance.
- **AVM-22** — Reserve and commit are distinct operations.
- **AVM-23** — Decommit and release are distinct operations.
- **AVM-24** — Page size is target/platform dependent.
- **AVM-25** — Memory protection is an explicit resource property.
- **AVM-26** — Writable memory is not implicitly executable.
- **AVM-27** — Address-space mappings have explicit ownership/lifetime.
- **AVM-28** — Safe capabilities cannot outlive their backing mapping.
- **AVM-29** — Remapping/invalidation cannot silently preserve invalid capabilities.

### Protection

- **APROTECT-20** — READ/WRITE/EXECUTE permissions are distinct.
- **APROTECT-21** — W^X is supported as a hardened platform policy.
- **APROTECT-22** — JIT executable memory requires explicit protection transition.
- **APROTECT-23** — MMIO is not ordinary RAM.
- **APROTECT-24** — Volatile device access is distinct from atomic access.
- **APROTECT-25** — Compiler optimization cannot remove observable MMIO operations.

### Mapping

- **AMAP-20** — Memory mapping is distinct from allocation.
- **AMAP-21** — Shared mapping does not imply synchronization.
- **AMAP-22** — Mapped-file memory is distinct from durable file persistence.
- **AMAP-23** — Foreign/external backing ownership must be explicit.
- **AMAP-24** — Mapping transitions may invalidate dependent capabilities.
- **AMAP-25** — Mapping APIs preserve alignment/initialization/protection contracts.

### System memory

- **ASYS-MEM-20** — Physical and virtual addresses are distinct.
- **ASYS-MEM-21** — Physical-address operations are system/unsafe operations.
- **ASYS-MEM-22** — Page-table manipulation is outside ordinary Core.
- **ASYS-MEM-23** — NUMA and huge pages are resource/performance properties, not ordinary type semantics.
- **ASYS-MEM-24** — DMA/device memory requires explicit storage-domain contracts.
- **ASYS-MEM-25** — Host/device memory cannot implicitly alias as ordinary safe memory.

---

# BOOTSTRAP-178 hoàn tất

Như vậy Axiom hiện đã có một memory architecture khá hoàn chỉnh:

```text
Value semantics
      ↓
Ownership
      ↓
Capability / view
      ↓
Lifetime / Drop
      ↓
Escape analysis
      ↓
Storage selection
      ↓
Allocator
      ↓
Memory Resource
      ↓
Virtual Memory
      ↓
Machine Address
```

Điểm đáng chú ý là **không tầng nào bắt programmer phải quản lý pointer/lifetime thủ công trong code thông thường**.

Programmer chỉ cần nói:

```ax
let buffer = Vec<u8>();
let data = buffer.view();
```

Compiler có thể tự suy luận:

```text
ownership
→ capability
→ lifetime
→ escape
→ storage
→ allocation
→ address
→ register/stack/heap
```

Trong khi programmer hệ thống vẫn có thể đi thẳng xuống:

```text
virtual address
page
MMIO
DMA
physical address
page table
```

qua `unsafe/system`.

---

## BOOTSTRAP-179 — I/O, File, Socket, Device & Zero-Copy Data Path

Bước tiếp theo hợp lý là nối memory architecture vừa hoàn thành với **thế giới bên ngoài**:

```text
Memory
   ↓
Buffer
   ↓
File I/O
   ↓
Socket I/O
   ↓
Pipe
   ↓
Device I/O
   ↓
DMA
   ↓
Async I/O
   ↓
Zero-copy
   ↓
Scatter/Gather
   ↓
io_uring / IOCP / kqueue / epoll
   ↓
Axiom unified I/O abstraction
```

Đây sẽ là task rất quan trọng để quyết định Axiom có đạt được mục tiêu **network/server/storage/video/audio engine hiệu năng cao mà không cần pointer-heavy API** hay không.