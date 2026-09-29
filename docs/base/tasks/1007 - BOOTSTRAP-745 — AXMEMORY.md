# BOOTSTRAP-745 — AXMEMORY

**Namespace:** `AXMEMORY`  
**Phase:** Axiom Civilization Runtime / Native Memory & Virtual Memory Infrastructure  
**Status:** **ARCHITECTURAL BASELINE — FROZEN TARGET**  
**Depends on:** `AXPROCESS`, `AXTHREAD`, `AXCOMPUTE`, `AXSTORAGE`, `AXSECURITY`, `AXAPPLICATION`, `AXGRAPHICS`, `AXMEDIA`, `AXAUDIO`, `AXNETWORK`, `AXASSET`

AXMEMORY là tầng quản lý **memory abstraction thực sự** bên dưới `AXPROCESS` và `AXTHREAD`.

Đây là một task đặc biệt quan trọng đối với mục tiêu Axiom vì memory model ảnh hưởng trực tiếp tới:

```text
performance
fragmentation
cache locality
multithreading
GPU/CPU interoperability
binary size
allocator complexity
determinism
native ABI
```

Axiom **không bắt buộc GC** và **không bắt buộc borrow checker**.

Thay vào đó, AXMEMORY xây dựng một hệ thống explicit, predictable:

```text
Virtual Address
      │
      ▼
Memory Region
      │
      ▼
Mapping
      │
      ▼
Page
      │
      ▼
Physical / Device Backing
```

và một tầng allocation:

```text
Application
     │
     ▼
AXMEMORY
 ┌───┼───────────────────────┐
 ▼   ▼       ▼       ▼       ▼
Heap Arena   Pool   Slab   mmap
 │
 ▼
Virtual Memory
 │
 ▼
Page / Device Memory
```

---

# 745.1 — Mục tiêu

AXMEMORY phải cung cấp native primitives cho:

```text
virtual memory
physical-page abstraction
memory mappings
protection
allocation
deallocation
heaps
arenas
pools
slabs
thread-local allocation
shared memory
memory-mapped files
copy-on-write
guard pages
large pages
NUMA memory
pinned memory
DMA
device memory
executable memory
memory pressure
reclamation
fragmentation control
memory accounting
debugging
tracing
deterministic allocation
simulation
zero-copy
```

---

# 745.2 — Strong Boundary

### AXMEMORY owns

```text
virtual memory
mapping
page abstraction
allocation
allocator policies
memory regions
memory protection
NUMA memory placement
memory pressure
memory accounting
memory diagnostics
```

### AXPROCESS owns

```text
process
address-space identity
thread
execution context
process isolation
```

### AXSTORAGE owns

```text
persistent storage
files
block storage
filesystem
database storage
```

### AXCOMPUTE owns

```text
compute resources
device scheduling
resource placement
```

### AXGRAPHICS owns

```text
graphics resource semantics
textures
meshes
render targets
```

AXMEMORY chỉ cung cấp backing memory primitives.

---

# 745.3 — Memory Model

Axiom sử dụng mô hình:

```text
logical object
      ↓
memory allocation
      ↓
memory region
      ↓
virtual mapping
      ↓
physical/device backing
```

Object identity **không phải** virtual address.

---

# 745.4 — Virtual Address

```axiom
virtual_address
```

là địa chỉ trong address space.

Không được coi virtual address là global identity.

---

# 745.5 — Memory Address

Axiom có thể expose:

```axiom
address
```

cho low-level code.

Nhưng API high-level ưu tiên:

```text
handle
slice
span
buffer
region
```

thay vì raw pointer arithmetic ở mọi nơi.

---

# 745.6 — Raw Pointer

Raw pointer vẫn tồn tại để phục vụ:

```text
native systems code
FFI
device programming
compiler runtime
allocator implementation
```

nhưng không phải abstraction duy nhất của memory.

---

# 745.7 — Pointer Semantics

Pointer phải có semantics rõ ràng:

```text
address
type
mutability
alignment
```

Không tự động imply ownership.

---

# 745.8 — Memory Handle

```axiom
memory_handle
```

đại diện logical allocation/region.

Handle không thay đổi khi physical backing thay đổi nếu backend hỗ trợ relocation.

---

# 745.9 — Memory Region

```axiom
memory_region {
    id
    address_space
    virtual_address
    size
    protection
    backing
    flags
}
```

---

# 745.10 — Region Identity

Region ID khác:

```text
virtual address
physical page
allocation ID
object ID
file ID
```

---

# 745.11 — Page

```axiom
memory_page {
    id
    size
    state
    backing
}
```

Page size phụ thuộc platform:

```text
4 KiB
16 KiB
64 KiB
large page
```

Runtime phải query capability.

---

# 745.12 — Page Granularity

Memory APIs phải phân biệt:

```text
allocation granularity
mapping granularity
page size
cache line size
large-page size
```

Không được giả định chúng giống nhau.

---

# 745.13 — Physical Memory

AXMEMORY có abstraction:

```axiom
physical_page
```

nhưng application thông thường không được truy cập physical address trực tiếp.

---

# 745.14 — Physical Access

Raw physical mapping yêu cầu:

```text
AXSECURITY capability
```

và thường chỉ dành cho:

```text
kernel
driver
hypervisor
trusted runtime
```

---

# 745.15 — Virtual Memory Mapping

```axiom
map_memory(
    address_space,
    backing,
    virtual_address,
    size,
    protection
)
```

---

# 745.16 — Unmapping

```axiom
unmap_memory(region)
```

Sau khi unmap:

```text
region → invalid
```

mọi access tới vùng đó phải fail theo platform semantics.

---

# 745.17 — Protection

```text
READ
WRITE
EXECUTE
```

với flags:

```text
PRIVATE
SHARED
GUARD
COPY_ON_WRITE
```

---

# 745.18 — W^X

Executable memory phải tuân policy:

```text
WRITE xor EXECUTE
```

trừ khi platform/security profile cho phép khác.

---

# 745.19 — JIT Memory

JIT runtime flow:

```text
allocate RW
    ↓
write machine code
    ↓
flush instruction cache
    ↓
change RX
    ↓
execute
```

Không giữ RWX vô thời hạn.

---

# 745.20 — Instruction Cache

Sau code generation:

```axiom
flush_instruction_cache(region)
```

phải được hỗ trợ trên architecture cần thiết.

---

# 745.21 — Guard Page

```axiom
guard_page
```

dùng để phát hiện:

```text
stack overflow
buffer boundary violation
allocator boundary violation
```

---

# 745.22 — Memory-Mapped File

```axiom
map_file(
    file,
    offset,
    size,
    protection
)
```

cho phép:

```text
file
 ↓
virtual memory
```

tránh copy không cần thiết.

---

# 745.23 — Mapping Modes

```text
private
shared
copy_on_write
read_only
execute
```

---

# 745.24 — Copy-on-Write

```text
Process A
 └── Page X
      │
      └── shared physical backing
             │
Process B ────┘
```

Write:

```text
write fault
 ↓
allocate new page
 ↓
copy
 ↓
remap writable
```

---

# 745.25 — Anonymous Memory

```axiom
allocate_virtual(size)
```

không cần file backing.

---

# 745.26 — Commit/Reserve

AXMEMORY phải phân biệt:

```text
reserve
commit
```

Ví dụ:

```text
reserve 1 GiB
commit 16 MiB
```

cho phép growable structures mà không commit toàn bộ physical memory ngay.

---

# 745.27 — Memory State

```text
RESERVED
COMMITTED
MAPPED
PROTECTED
DECOMMITTED
UNMAPPED
RELEASED
```

---

# 745.28 — Heap

```axiom
heap {
    id
    allocator
    policy
    limits
}
```

Heap là logical allocation domain.

---

# 745.29 — Default Heap

Axiom runtime có default heap nhưng compiler/runtime không được giả định mọi allocation phải đi qua nó.

---

# 745.30 — Arena

```axiom
arena {
    backing
    cursor
    capacity
}
```

Allocation:

```text
bump
 ↓
object
 ↓
object
 ↓
object
```

---

# 745.31 — Arena Free

Arena có thể free toàn bộ:

```axiom
arena.reset()
```

thay vì free từng object.

---

# 745.32 — Pool Allocator

```axiom
pool<T> {
    capacity
    free_list
}
```

dành cho fixed-size objects.

---

# 745.33 — Slab Allocator

Slab phù hợp:

```text
many same-sized objects
```

Ví dụ:

```text
task descriptors
network buffers
AST nodes
IPC messages
```

---

# 745.34 — Thread Local Allocator

Mỗi worker/thread có:

```text
local allocation cache
```

giảm contention.

---

# 745.35 — Global Allocator

Global heap chỉ là fallback.

Hot-path allocations nên ưu tiên:

```text
stack
thread-local
arena
pool
slab
```

---

# 745.36 — Allocation Classes

Runtime chuẩn hóa:

```text
tiny
small
medium
large
huge
```

Allocator có thể chọn strategy theo size class.

---

# 745.37 — Small Allocation

Small allocation có thể dùng:

```text
slab
size-class pool
thread cache
```

---

# 745.38 — Large Allocation

Large allocation có thể bypass general heap:

```text
virtual mapping
large pages
direct region
```

---

# 745.39 — Huge Allocation

Huge allocation phải tránh fragment heap nhỏ.

Ví dụ:

```text
> large threshold
```

→ direct virtual mapping.

Threshold configurable.

---

# 745.40 — Alignment

```axiom
allocate(size, alignment)
```

Alignment phải được validate:

```text
power_of_two
platform_supported
```

---

# 745.41 — Cache-Line Alignment

API:

```axiom
cache_line_size()
```

để programmer/compiler tối ưu concurrent data structures.

---

# 745.42 — SIMD Alignment

Allocator phải hỗ trợ alignment phù hợp:

```text
16
32
64
128
...
```

nếu platform/backend cho phép.

---

# 745.43 — Allocation Metadata

Mỗi allocation có thể có:

```text
allocation_id
size
alignment
allocator
owner
flags
```

Metadata không bắt buộc nằm cạnh user memory.

---

# 745.44 — Out-of-Band Metadata

Allocator nên ưu tiên metadata tách khỏi hot data khi điều này cải thiện locality.

---

# 745.45 — Memory Ownership

AXMEMORY không áp đặt ownership type system.

Ownership có thể được biểu diễn bằng:

```text
scope
handle
allocator
arena
explicit release
reference count
unique resource wrapper
```

tùy abstraction.

---

# 745.46 — Explicit Release

Native allocation:

```axiom
mem = allocate(size)
...
release(mem)
```

không có hidden GC pause.

---

# 745.47 — Scoped Memory

```axiom
scope {
    arena local
    ...
}
```

Khi scope kết thúc:

```text
arena → reset
```

---

# 745.48 — RAII-like Cleanup

Compiler có thể lower:

```axiom
using resource
```

thành deterministic cleanup.

Memory management không phụ thuộc garbage collector.

---

# 745.49 — Reference Counting

Reference counting được phép cho những abstraction cần shared ownership.

Không phải default cho mọi object.

---

# 745.50 — Cycle Handling

Nếu sử dụng reference counting:

```text
A → B
B → A
```

cycle không được tự động giải quyết bằng GC.

API phải cung cấp:

```text
weak reference
explicit break
ownership graph design
```

khi cần.

---

# 745.51 — Memory Pressure

Runtime phải theo dõi:

```text
available
committed
resident
reclaimable
locked
mapped
```

---

# 745.52 — Memory Pressure Levels

```text
NORMAL
WARNING
CRITICAL
EMERGENCY
```

---

# 745.53 — Reclamation

Runtime có thể reclaim:

```text
cache
unused pages
clean mappings
deferred buffers
```

Không tự ý reclaim memory đang thuộc live allocation.

---

# 745.54 — Working Set

Process memory accounting phân biệt:

```text
virtual
committed
resident
shared
private
mapped
```

---

# 745.55 — Page Residency

API:

```axiom
query_residency(region)
```

có thể trả:

```text
resident
nonresident
compressed
unknown
```

---

# 745.56 — Memory Lock/PIN

```axiom
pin_memory(region)
unpin_memory(region)
```

dành cho:

```text
DMA
realtime
device transfer
```

Requires appropriate capability/quota.

---

# 745.57 — Pinned Memory

Pinned memory không được reclaim/swap theo semantics của platform.

Do đó phải chịu:

```text
quota
resource accounting
```

---

# 745.58 — DMA

```axiom
dma_buffer {
    memory
    device
    direction
}
```

Directions:

```text
DEVICE_READ
DEVICE_WRITE
BIDIRECTIONAL
```

---

# 745.59 — DMA Safety

DMA buffer phải có:

```text
ownership
lifetime
device authorization
mapping state
```

rõ ràng.

---

# 745.60 — Device Memory

AXMEMORY hỗ trợ abstraction:

```axiom
device_memory
```

cho:

```text
GPU
NPU
accelerator
specialized device
```

---

# 745.61 — Host Memory

```axiom
host_memory
```

CPU-accessible memory.

---

# 745.62 — Unified/Shared Memory

Backend có thể hỗ trợ:

```text
shared CPU/GPU memory
unified memory
managed memory
```

nhưng semantic distinction phải giữ nguyên.

---

# 745.63 — Memory Transfer

```axiom
copy_memory(src, dst)
```

Có thể được lower thành:

```text
CPU memcpy
SIMD copy
DMA
GPU copy
```

dựa trên AXCOMPUTE/backend.

---

# 745.64 — Zero-Copy

Nếu source và destination cùng có compatible backing:

```text
transfer
```

có thể trở thành:

```text
shared mapping / handle transfer
```

thay vì copy.

---

# 745.65 — Memory View

```axiom
memory_view<T> {
    pointer
    length
    stride
}
```

---

# 745.66 — Slice

```axiom
slice<T>
```

là view vào memory.

Slice không sở hữu memory backing trừ khi explicitly declared owning.

---

# 745.67 — Span

```axiom
span<T>
```

là non-owning contiguous view.

---

# 745.68 — Bounds

High-level slice/span APIs phải có:

```text
length
```

và optional checked access.

---

# 745.69 — Unchecked Access

Low-level code có thể sử dụng:

```axiom
unsafe
```

để bỏ bounds checks khi programmer đảm bảo invariant.

---

# 745.70 — Safe/Unsafe Boundary

Unsafe code phải được compiler đánh dấu rõ.

Không biến toàn bộ Axiom thành unsafe chỉ vì language hỗ trợ raw pointers.

---

# 745.71 — Bounds Checking

Compiler có thể eliminate checks khi chứng minh được:

```text
index < length
```

hoặc khi loop canonical form cho phép range analysis.

---

# 745.72 — Allocation Elision

Compiler có thể eliminate allocation nếu lifetime không escape:

```text
allocate
 ↓
use
 ↓
free
```

→ stack/register/local storage.

---

# 745.73 — Escape Analysis

Compiler có thể xác định:

```text
non_escape
thread_local_escape
heap_escape
process_escape
```

để chọn allocator phù hợp.

---

# 745.74 — Stack Allocation

Small temporary objects nên có khả năng lower:

```text
heap → stack
```

khi lifetime phù hợp.

---

# 745.75 — Scalar Replacement

Compiler có thể transform:

```text
struct object
```

thành:

```text
registers / scalar locals
```

nếu không observable.

---

# 745.76 — Object Layout

Axiom phải có deterministic layout rules cho:

```text
struct
array
tuple
union
enum
```

---

# 745.77 — Struct Layout

Native ABI cần:

```text
field offset
alignment
size
padding
```

được xác định.

---

# 745.78 — Packed Layout

```axiom
@packed
struct ...
```

được hỗ trợ cho interoperability.

Compiler phải cảnh báo/kiểm soát unaligned access.

---

# 745.79 — Explicit Layout

```axiom
@layout(...)
```

cho low-level types cần ABI stability.

---

# 745.80 — Array Layout

Default:

```text
T[0]
T[1]
T[2]
...
```

contiguous.

---

# 745.81 — Multidimensional Array

Compiler phải hỗ trợ explicit:

```text
row_major
column_major
strided
```

để phục vụ AI/GPU/scientific computing.

---

# 745.82 — Memory Pool Lifetime

Pool có ownership:

```text
pool lifetime
```

Object allocated từ pool không được tồn tại hợp lệ sau pool destruction trừ khi copied/migrated.

---

# 745.83 — Arena Lifetime

Arena allocation không hỗ trợ arbitrary individual free mặc định.

Đổi lại:

```text
O(1)-like bulk reset
```

---

# 745.84 — Fragmentation

AXMEMORY phải theo dõi:

```text
internal fragmentation
external fragmentation
virtual fragmentation
physical fragmentation
```

---

# 745.85 — Fragmentation Strategy

Không có một allocator duy nhất cho mọi workload.

Runtime phải cung cấp:

```text
general heap
arena
pool
slab
stack allocator
linear allocator
large-region allocator
```

---

# 745.86 — Compaction

Compaction chỉ được thực hiện đối với memory abstraction cho phép relocation.

Raw pointer-visible allocation không được silently move.

---

# 745.87 — Relocatable Memory

```axiom
relocatable_buffer
```

có thể move backing và update handle.

Raw pointer vào vùng này chỉ valid trong scoped pin/access window.

---

# 745.88 — Stable Memory

```axiom
stable_buffer
```

guarantee virtual address stability cho lifetime được chỉ định.

---

# 745.89 — Memory Pinning vs Stability

Hai khái niệm khác nhau:

```text
stable virtual address
≠
physical residency
```

---

# 745.90 — Shared Memory Lifetime

Shared memory phải có:

```text
creator
owners
mappings
reference/lifetime state
```

---

# 745.91 — Cross-Process Memory

Không cho phép:

```text
raw pointer from process A
```

được sử dụng trực tiếp trong process B.

Phải map shared region tương ứng.

---

# 745.92 — Security Integration

Memory operations phải chịu:

```text
address-space policy
mapping permissions
device access policy
DMA authority
executable memory policy
physical memory authority
```

---

# 745.93 — Secure Memory

```axiom
secure_memory
```

hỗ trợ:

```text
non-swappable
zeroize
restricted mapping
restricted duplication
```

---

# 745.94 — Zeroization

```axiom
secure_zero(memory)
```

compiler không được optimize away thao tác zeroization có semantics security.

---

# 745.95 — Memory Encryption

Nếu platform hỗ trợ:

```text
encrypted memory
confidential memory
```

AXMEMORY có thể expose capability.

---

# 745.96 — Memory Tagging

Nếu hardware hỗ trợ:

```text
memory tagging
```

AXMEMORY có thể expose optional diagnostics/security layer.

---

# 745.97 — Huge Pages

```axiom
allocate_large_pages(size)
```

được dùng cho:

```text
large datasets
AI tensors
database buffers
VMs
high-throughput workloads
```

---

# 745.98 — Transparent Large Pages

Platform có thể tự chọn large pages nhưng behavior observable phải không được phụ thuộc vào assumption rằng large pages luôn tồn tại.

---

# 745.99 — NUMA Allocation

```axiom
allocate_on_node(size, numa_node)
```

---

# 745.100 — NUMA Policies

```text
local
preferred
interleave
replicate
explicit
```

---

# 745.101 — NUMA Migration

Memory backend có thể migrate pages nếu:

```text
allocation is movable
policy permits
```

Raw-pointer stable allocation không được silently relocate.

---

# 745.102 — Memory Locality

Runtime telemetry phải có khả năng báo:

```text
local access
remote access
migration
allocation node
```

khi platform expose được thông tin.

---

# 745.103 — Cache Hints

Axiom có thể expose optional:

```axiom
prefetch(address)
cache_flush(region)
cache_invalidate(region)
```

cho low-level code/platform-specific paths.

---

# 745.104 — Compiler Prefetch

Compiler có thể tự chèn prefetch nếu profile-guided optimization chứng minh lợi ích.

Không được biến thành mandatory semantic behavior.

---

# 745.105 — Memory Barriers

AXMEMORY phối hợp với AXTHREAD để hỗ trợ:

```text
memory fence
store fence
load fence
```

Semantics atomic chính thuộc concurrency model.

---

# 745.106 — Allocation Failure

Allocation failure phải explicit:

```text
Result<Memory, MemoryError>
```

hoặc equivalent native error semantics.

Không bắt buộc process crash ngay khi allocation thất bại.

---

# 745.107 — Memory Error Types

```text
OUT_OF_MEMORY
ADDRESS_SPACE_EXHAUSTED
QUOTA_EXCEEDED
INVALID_ALIGNMENT
INVALID_SIZE
PROTECTION_DENIED
CAPABILITY_DENIED
DEVICE_MEMORY_EXHAUSTED
PIN_LIMIT_EXCEEDED
```

---

# 745.108 — Memory Pressure Callback

Application/runtime có thể đăng ký:

```axiom
memory_pressure_handler
```

nhưng callback phải có clear execution context.

Không được gọi arbitrary application code từ unsafe allocator critical section.

---

# 745.109 — Reclamation Callback

Cache systems có thể đăng ký:

```axiom
reclaimable_resource
```

để giải phóng cache khi pressure tăng.

---

# 745.110 — Persistent Mapping

AXMEMORY hỗ trợ:

```text
persistent memory mapping
```

khi platform/storage backend cung cấp semantics phù hợp.

Persistence ordering phải được explicit.

---

# 745.111 — Mapped Database Memory

AXDATABASE có thể dùng:

```text
mmap
```

nhưng database durability vẫn thuộc AXDATABASE/AXSTORAGE.

Memory mapping không tự đồng nghĩa durable transaction.

---

# 745.112 — Memory-Backed Storage

AXSTORAGE có thể expose:

```text
memory-backed file
ramdisk
cache
```

AXMEMORY cung cấp backing memory, AXSTORAGE định nghĩa storage semantics.

---

# 745.113 — Shared Ring Buffer

Native pattern:

```text
Producer
    ↓
shared memory ring
    ↓
Consumer
```

được hỗ trợ trực tiếp để xây:

```text
IPC
network
audio
media
GPU
logging
```

---

# 745.114 — Ring Buffer

```axiom
ring_buffer<T> {
    capacity
    head
    tail
    storage
}
```

Có thể specialize:

```text
SPSC
MPSC
SPMC
MPMC
```

---

# 745.115 — Memory Ownership Transfer

High-performance IPC có thể chuyển ownership:

```text
Producer
   ↓
buffer
   ↓ transfer ownership
Consumer
```

thay vì copy.

---

# 745.116 — Immutable Shared Buffer

Một buffer có thể chuyển sang:

```text
immutable/shared
```

sau khi producer hoàn tất.

Điều này giảm synchronization.

---

# 745.117 — Memory Views and Lifetimes

View:

```text
slice
span
tensor_view
image_view
```

không được outlive backing memory.

Compiler/runtime APIs phải giúp detect lifetime violations ở mức khả thi, nhưng không yêu cầu borrow checker.

---

# 745.118 — Tensor Memory

AI runtime cần:

```axiom
tensor_buffer {
    data
    shape
    stride
    dtype
    device
}
```

AXMEMORY sở hữu memory layout; AXCOMPUTE sở hữu compute execution.

---

# 745.119 — Tensor Layout

Hỗ trợ:

```text
contiguous
strided
blocked
tiled
sparse
```

---

# 745.120 — Sparse Memory

AXMEMORY có thể cung cấp:

```text
sparse backing
virtual sparse allocation
```

cho GPU/AI workloads.

---

# 745.121 — Virtual Sparse Allocation

Có thể reserve address space lớn:

```text
16 TiB virtual
```

nhưng commit pages khi cần.

---

# 745.122 — Memory Aliasing

Một physical backing có thể có nhiều virtual mappings:

```text
VA1 ─┐
     ├── Physical Page
VA2 ─┘
```

Aliasing semantics phải explicit.

---

# 745.123 — Aliasing and Compiler

Compiler phải có rules để tránh tối ưu sai khi raw pointers có thể alias.

Axiom cần có:

```axiom
restrict
```

hoặc equivalent no-alias contract.

---

# 745.124 — No-Alias Contract

```axiom
@noalias
```

có thể cho compiler biết hai memory views không overlap.

Nếu programmer vi phạm contract → undefined behavior trong unsafe mode.

---

# 745.125 — Volatile Memory

```axiom
volatile<T>
```

dành cho:

```text
MMIO
device registers
special hardware
```

Compiler không được loại bỏ/reorder volatile operations ngoài semantics quy định.

---

# 745.126 — Memory-Mapped I/O

```axiom
map_device_memory()
```

requires privileged capability.

---

# 745.127 — Device Register Access

Phải hỗ trợ:

```text
volatile
alignment
ordering
access width
```

---

# 745.128 — Memory Debugging

Development mode hỗ trợ:

```text
red zones
guard pages
poisoning
use-after-free detection
double-free detection
leak tracking
allocation stack traces
```

---

# 745.129 — Debug Poisoning

Freed memory có thể được fill bằng diagnostic pattern.

Không phải production semantic guarantee.

---

# 745.130 — Leak Detection

Allocator có thể track:

```text
allocation
owner
stack
lifetime
```

để phát hiện leak.

---

# 745.131 — Memory Profiler

Metrics:

```text
allocations/sec
bytes/sec
live bytes
peak bytes
fragmentation
page faults
resident memory
allocation latency
free latency
```

---

# 745.132 — Memory Trace

```axiom
memory_trace_event {
    timestamp
    allocation_id
    operation
    size
    thread
    task
}
```

---

# 745.133 — Deterministic Allocator

Testing có:

```axiom
deterministic_allocator
```

với stable allocation sequence.

---

# 745.134 — Allocation Replay

Replay có thể reproduce:

```text
allocation order
free order
mapping order
memory pressure
```

để debug allocator-dependent bugs.

---

# 745.135 — Simulation

```axiom
memory_simulation {
    capacity
    page_size
    numa_nodes
    latency_model
    pressure_model
}
```

Có thể mô phỏng:

```text
OOM
fragmentation
NUMA effects
page faults
reclamation
allocation contention
```

---

# 745.136 — Memory Digital Twin

Digital twin biểu diễn:

```text
virtual regions
physical pages
allocator pools
NUMA nodes
device memory
pressure
fragmentation
```

---

# 745.137 — Performance Architecture

AXMEMORY phải ưu tiên:

```text
thread-local caches
size classes
arena allocation
pool allocation
slab allocation
direct large mappings
NUMA locality
large pages
zero-copy
mmap
allocation batching
```

---

# 745.138 — Allocation Hot Path

Hot path lý tưởng:

```text
request
 ↓
thread-local cache
 ↓
free block
 ↓
return
```

không:

```text
global lock
kernel syscall
metadata allocation
```

trừ khi cần.

---

# 745.139 — Free Hot Path

```text
free
 ↓
thread-local cache
 ↓
return
```

Có thể deferred coalescing.

---

# 745.140 — Cross-Thread Free

Nếu Thread B free memory allocated bởi Thread A:

```text
B local cache
```

hoặc:

```text
remote free queue
```

được sử dụng để tránh lock global heap.

---

# 745.141 — Remote Free Queue

```text
Thread A allocator
       ↑
remote frees
       │
Thread B
```

A xử lý remote frees khi appropriate.

---

# 745.142 — Allocator Specialization

Compiler có thể specialize:

```text
allocate<T>()
```

thành size/alignment constant.

---

# 745.143 — Compile-Time Allocation

Static-size structures có thể được compile thành:

```text
stack
static data
TLS
arena
```

mà không cần generic allocator.

---

# 745.144 — Static Memory

```axiom
static_buffer<T, N>
```

được layout trực tiếp trong binary/data section.

---

# 745.145 — Embedded Mode

AXMEMORY phải hỗ trợ platform hạn chế:

```text
fixed heap
static arena
no virtual memory
small page model
```

---

# 745.146 — Kernel/Runtime Mode

Trusted runtime có thể sử dụng:

```text
physical pages
page tables
DMA
MMIO
```

với security capabilities.

---

# 745.147 — User Mode

Normal application chỉ được:

```text
virtual allocation
mapping
shared memory
device-approved memory
```

theo capability.

---

# 745.148 — Cross-Platform Backend

AXMEMORY backend abstraction phải hỗ trợ:

```text
Windows
Linux
macOS
Android
iOS
WASM
embedded
```

---

# 745.149 — Backend Examples

Windows:

```text
VirtualAlloc
section mappings
NUMA APIs
```

Linux:

```text
mmap
madvise
memfd
shared mappings
```

macOS:

```text
Mach VM
mmap
```

Các API trên chỉ là backend implementation, không trở thành Axiom language dependency.

---

# 745.150 — WASM

WASM backend phải map AXMEMORY abstraction vào:

```text
linear memory
memory growth
```

nhưng giữ API semantics tương thích trong giới hạn WASM.

---

# 745.151 — Memory ABI

Compiler phải có canonical ABI metadata:

```text
size
alignment
layout
calling convention
ownership contract
```

---

# 745.152 — FFI

C ABI / platform ABI interop phải xác định:

```text
pointer
size
alignment
ownership
lifetime
```

Không tự động giải phóng memory do foreign library cấp nếu ownership chưa được khai báo.

---

# 745.153 — Foreign Allocator

```axiom
foreign_allocator {
    allocate
    resize
    free
}
```

Cho phép Axiom dùng:

```text
C malloc
custom native allocator
OS allocator
```

mà không phụ thuộc chúng trong runtime mặc định.

---

# 745.154 — Resize

```axiom
resize(memory, new_size)
```

có thể:

```text
in_place
move
fail
```

Semantics phải trả kết quả rõ ràng.

---

# 745.155 — Reallocation

Nếu relocation xảy ra:

```text
old pointer → invalid
new pointer → valid
```

Không được silently giữ old pointer valid.

---

# 745.156 — Memory Copy

```axiom
copy
move
fill
compare
zero
```

phải có native optimized implementation.

---

# 745.157 — SIMD Memory Operations

Compiler/runtime có thể chọn:

```text
SSE
AVX
AVX2
AVX-512
NEON
SVE
```

theo target capabilities.

---

# 745.158 — Runtime Dispatch

Memory primitives có thể dùng:

```text
compile-time target
CPU feature dispatch
```

Không yêu cầu dynamic dispatch nếu target cố định.

---

# 745.159 — Memory Bandwidth

Profiler có thể đo:

```text
read bandwidth
write bandwidth
copy bandwidth
NUMA bandwidth
device transfer bandwidth
```

---

# 745.160 — Memory Latency

Telemetry có thể đo:

```text
allocation latency
page fault latency
NUMA access latency
device mapping latency
```

---

# 745.161 — Memory Pressure and AXCOMPUTE

AXCOMPUTE có thể nhận:

```text
memory availability
bandwidth
pressure
```

để scheduling.

AXMEMORY không quyết định compute scheduling.

---

# 745.162 — Memory Pressure and AXSTORAGE

AXSTORAGE có thể yêu cầu reclaim:

```text
cache
buffer
page cache
mapped cache
```

nhưng authoritative storage state không bị mất.

---

# 745.163 — Memory Pressure and AXDATABASE

Database buffer pool phải có explicit ownership:

```text
database-owned memory
```

AXMEMORY cung cấp backing/allocator primitives.

---

# 745.164 — Memory Pressure and AXMEDIA

Media buffers có thể được:

```text
pooled
reused
zero-copy
DMA-backed
```

để tránh allocation churn.

---

# 745.165 — Memory Pressure and AXAUDIO

Realtime audio memory phải ưu tiên:

```text
preallocation
pinned buffers
ring buffers
no allocation in callback
```

---

# 745.166 — Memory Pressure and AXGRAPHICS

GPU resource memory:

```text
device memory
host visible memory
staging memory
```

phải được phân biệt.

---

# 745.167 — Security: No Arbitrary Physical Access

Invariant:

```text
application
  ✕
physical memory
```

trừ khi explicit trusted capability.

---

# 745.168 — Security: No Arbitrary Cross-Process Mapping

Process A không được map process B memory chỉ bằng process ID.

Cần:

```text
capability
+
requested rights
+
security policy
```

---

# 745.169 — Security: Executable Memory

JIT/compiler code generation phải obey:

```text
W^X
```

và security policy.

---

# 745.170 — AI Boundary

AI có thể:

```text
analyze allocation profiles
suggest allocator
detect fragmentation patterns
suggest NUMA placement
predict memory pressure
analyze leaks
```

AI không được tự động:

```text
map privileged memory
disable W^X
access physical memory
bypass quotas
read protected process memory
```

---

# 745.171 — Memory Policy

```axiom
memory_policy {
    allocator
    numa
    page_size
    huge_pages
    reclaim
    protection
}
```

---

# 745.172 — Policy Resolution

Policy hierarchy:

```text
system
 ↓
process
 ↓
executor
 ↓
task
 ↓
allocation
```

Child policy không được vượt parent constraints.

---

# 745.173 — Allocation Domains

```axiom
memory_domain {
    id
    allocator
    quota
    policy
}
```

Có thể tạo:

```text
UI domain
media domain
database domain
AI domain
temporary domain
```

---

# 745.174 — Memory Quota

```axiom
memory_quota {
    reserved
    committed
    resident
    pinned
    device
}
```

---

# 745.175 — Quota Enforcement

Quota violation:

```text
allocation
 ↓
quota check
 ↓
ALLOW / FAIL / WAIT / RECLAIM
```

Không tự động kill process nếu policy không yêu cầu.

---

# 745.176 — Memory Reservation

Application có thể reserve capacity:

```axiom
reserve_budget(size)
```

để giảm runtime allocation failure bất ngờ trong critical operation.

---

# 745.177 — Reclaim Priority

Cache/resources có:

```text
reclaim_priority
```

Ví dụ:

```text
DISCARDABLE
RECREATABLE
IMPORTANT
PINNED
NON_RECLAIMABLE
```

---

# 745.178 — Memory Lifetime Classes

```text
TRANSIENT
FRAME
TASK
REQUEST
SESSION
PROCESS
GLOBAL
PERSISTENT
```

Compiler/runtime có thể dùng lifetime class để chọn allocator.

---

# 745.179 — Frame Memory

Graphics/media workload có:

```axiom
frame_arena
```

reset mỗi frame.

---

# 745.180 — Request Memory

Network/server workload có:

```axiom
request_arena
```

reset sau request completion.

---

# 745.181 — Persistent Runtime Memory

Long-lived allocations phải tránh nằm trong transient arena.

---

# 745.182 — Memory Migration

Memory có thể migrate giữa:

```text
DRAM
NUMA node
GPU
NPU
persistent mapping
```

nếu abstraction cho phép.

---

# 745.183 — Migration Semantics

Migration phải bảo toàn:

```text
logical contents
access permissions
ownership
lifetime
```

---

# 745.184 — Migration and Raw Pointers

Nếu migration thay đổi virtual address:

```text
raw pointer → invalid
```

do đó stable buffers phải pin/address-stable.

---

# 745.185 — Memory Compaction

General heap có thể compact chỉ khi allocation handles/views cho phép relocation.

Không compact arbitrary raw-pointer memory.

---

# 745.186 — Memory Statistics

```axiom
memory_stats {
    virtual_reserved
    committed
    resident
    free
    cached
    pinned
    shared
    private
    fragmentation
}
```

---

# 745.187 — Process Memory Statistics

AXPROCESS query:

```text
AXMEMORY.get_process_stats(process)
```

---

# 745.188 — Task Memory Statistics

AXTHREAD query:

```text
get_task_allocations(task)
```

có thể sử dụng sampling/tracing.

---

# 745.189 — Memory Ownership Graph

Debug mode có thể biểu diễn:

```text
Process
 ├── Arena
 │    ├── allocation
 │    └── allocation
 │
 ├── Pool
 │    └── object
 │
 └── mmap
```

---

# 745.190 — Double Free

Allocator phải phát hiện trong diagnostic mode:

```text
free(x)
free(x)
```

Production behavior có thể tối ưu nhưng API contract phải xác định undefined/error behavior.

---

# 745.191 — Use After Free

Debug allocator có thể:

```text
poison
guard
quarantine
```

để bắt lỗi.

---

# 745.192 — Quarantine

Freed memory có thể tạm giữ:

```text
allocated
 ↓
freed
 ↓
quarantine
 ↓
reusable
```

chỉ trong debug/hardened mode.

---

# 745.193 — Hardened Memory

Security profile có thể bật:

```text
guard pages
randomized allocation
quarantine
zero-on-free
metadata protection
```

với trade-off hiệu năng rõ ràng.

---

# 745.194 — ASLR Metadata

AXMEMORY phải hỗ trợ randomization của:

```text
stack
heap
mappings
libraries
```

nếu platform hỗ trợ.

---

# 745.195 — Deterministic Mode and ASLR

Deterministic simulation có thể disable/random seed ASLR trong isolated simulation domain.

Production security không bị thay đổi bởi simulation setting.

---

# 745.196 — Memory Snapshot

Snapshot có thể chứa:

```text
region metadata
mapping metadata
page contents
allocator metadata
```

nhưng không mặc định là portable cross-platform process snapshot.

---

# 745.197 — Memory Restore

Restore chỉ được phép nếu:

```text
architecture
ABI
page model
security context
backing resources
```

compatible.

---

# 745.198 — Crash Dump

Memory dump phải phân biệt:

```text
full dump
minidump
selected regions
stack-only
metadata-only
```

---

# 745.199 — Sensitive Memory

Crash dump mặc định phải có policy loại trừ:

```text
keys
passwords
secure memory
protected mappings
```

---

# 745.200 — Final Memory Architecture

```text
                    AXMEMORY
                       │
       ┌───────────────┼────────────────┐
       │               │                │
       ▼               ▼                ▼
 Virtual Memory    Allocators       Device Memory
       │               │                │
       ├── Region      ├── Heap         ├── GPU
       ├── Mapping     ├── Arena        ├── NPU
       ├── Page        ├── Pool         ├── DMA
       ├── Protection  ├── Slab         └── Pinned
       └── COW        └── TLS
       │
       ▼
   Shared Memory
       │
       ▼
   Zero-Copy
       │
       ▼
AXPROCESS / AXTHREAD / AXCOMPUTE
```

---

# 745.201 — Formal Invariants

```text id="b0a5lq"
MEM-INV-01   Every memory region has a stable logical identity.
MEM-INV-02   Region identity is distinct from virtual address.
MEM-INV-03   Virtual addresses are scoped to an address space.
MEM-INV-04   Physical memory is not directly accessible by normal applications.
MEM-INV-05   Cross-process mappings require explicit authority.
MEM-INV-06   Memory protection is explicit.
MEM-INV-07   Executable writable memory obeys explicit W^X policy.
MEM-INV-08   Unmapped memory cannot be accessed as valid memory.
MEM-INV-09   Mapping granularity is explicit.
MEM-INV-10   Page size is a backend capability, not a language constant.

MEM-INV-11   Allocation identity is distinct from virtual address.
MEM-INV-12   Allocations have explicit lifetime semantics.
MEM-INV-13   Default allocation does not imply garbage collection.
MEM-INV-14   Arena allocations cannot outlive their arena.
MEM-INV-15   Pool allocations cannot outlive their owning pool.
MEM-INV-16   Raw pointers do not imply ownership.
MEM-INV-17   Non-owning views cannot extend backing-memory lifetime.
MEM-INV-18   Reallocation invalidates old pointers when relocation occurs.
MEM-INV-19   Stable-address memory cannot silently relocate.
MEM-INV-20   Relocatable memory must use an abstraction compatible with relocation.

MEM-INV-21   Shared memory mappings preserve explicit ownership/authority semantics.
MEM-INV-22   Zero-copy transfer preserves buffer lifetime.
MEM-INV-23   DMA memory has explicit device ownership semantics.
MEM-INV-24   Pinned memory is accounted against explicit resource limits.
MEM-INV-25   Device memory is distinct from ordinary host memory.
MEM-INV-26   NUMA placement is a policy, not an ownership mechanism.
MEM-INV-27   Memory migration preserves logical contents and permissions.
MEM-INV-28   Memory compaction cannot move arbitrary pointer-visible allocations.
MEM-INV-29   Copy-on-write preserves logical isolation.
MEM-INV-30   Memory aliases have explicit mapping semantics.

MEM-INV-31   Secure memory cannot be exposed through unauthorized mappings.
MEM-INV-32   Zeroization has observable security semantics.
MEM-INV-33   Physical/MMIO mapping requires privileged authority.
MEM-INV-34   Allocation failure is representable as explicit runtime state.
MEM-INV-35   Memory quota cannot be silently exceeded.
MEM-INV-36   Reclamation cannot discard live non-reclaimable allocations.
MEM-INV-37   Disabled diagnostics cannot require full debug overhead.
MEM-INV-38   Deterministic allocation is isolated from production allocation policy.
MEM-INV-39   Memory accounting is attributable to explicit ownership domains.
MEM-INV-40   Identical deterministic allocation inputs produce identical logical allocation state.
```

---

# 745.202 — Native API

```axiom
reserve_virtual()
commit_virtual()
decommit_virtual()
release_virtual()

map_memory()
unmap_memory()
protect_memory()

map_file()
unmap_file()

allocate()
reallocate()
release()

allocate_aligned()
allocate_large()
allocate_on_node()

create_heap()
destroy_heap()

create_arena()
reset_arena()

create_pool()
destroy_pool()

create_slab()
destroy_slab()

create_memory_domain()
set_memory_policy()

create_shared_memory()
map_shared_memory()
unmap_shared_memory()

create_relocatable_buffer()
create_stable_buffer()

create_memory_view()
create_slice()
create_span()

pin_memory()
unpin_memory()

create_dma_buffer()
map_device_memory()

copy_memory()
move_memory()
fill_memory()
compare_memory()
zero_memory()

secure_zero()

flush_instruction_cache()

prefetch()

query_residency()
query_memory_stats()
query_process_memory()
query_numa_topology()

set_memory_pressure_policy()

start_memory_trace()
stop_memory_trace()

create_memory_snapshot()
restore_memory_snapshot()

create_memory_simulation()
replay_memory_trace()
```

---

# 745.203 — Canonical Flow: General Allocation

```text id="5ty7aa"
allocate(size)
      ↓
size class
      ↓
thread-local cache
      │
      ├── available → return
      │
      └── empty
           ↓
       local refill
           ↓
       arena/slab
           ↓
       page mapping
           ↓
          return
```

---

# 745.204 — Canonical Flow: Large Allocation

```text id="j0otzx"
large allocation
      ↓
direct virtual reservation
      ↓
page commit
      ↓
mapping
      ↓
return region
```

Không đi qua small-object heap nếu không cần.

---

# 745.205 — Canonical Flow: Memory-Mapped File

```text id="5q7x0k"
AXSTORAGE file
      ↓
map_file()
      ↓
AXMEMORY region
      ↓
virtual mapping
      ↓
page faults / residency
      ↓
application view
```

---

# 745.206 — Canonical Flow: Shared Memory

```text id="9jrygk"
Process A
   ↓
create shared region
   ↓
capability
   ↓
Process B
   ↓
map shared region
   ↓
zero-copy communication
```

---

# 745.207 — Canonical Flow: DMA

```text id="g2j6a5"
allocate DMA buffer
      ↓
pin
      ↓
device mapping
      ↓
DMA
      ↓
completion
      ↓
unmap
      ↓
unpin
      ↓
release
```

---

# 745.208 — Canonical Flow: Memory Pressure

```text id="czb5dy"
memory usage
      ↓
WARNING
      ↓
reclaim caches
      ↓
reduce transient allocations
      ↓
CRITICAL
      ↓
policy enforcement
      ↓
allocation failure / throttle / suspend
```

---

# 745.209 — Canonical Flow: Debug Allocation

```text id="1d5v3h"
allocate
 ↓
red zone
 ↓
user memory
 ↓
guard
 ↓
trace metadata
 ↓
use
 ↓
free
 ↓
quarantine
```

---

# 745.210 — Definition of Done

```text id="b6l5pg"
BOOTSTRAP-745
STATUS: COMPLETE / FROZEN

AXMEMORY
 ├── Virtual Memory
 ├── Physical Page Abstraction
 ├── Regions
 ├── Mapping
 ├── Protection
 ├── W^X
 ├── JIT Memory
 ├── Guard Pages
 ├── mmap
 ├── Reserve / Commit
 ├── Heap
 ├── Arena
 ├── Pool
 ├── Slab
 ├── Thread-Local Allocator
 ├── Size Classes
 ├── Alignment
 ├── Object Layout
 ├── Ownership/Lifetime
 ├── Scoped Memory
 ├── Relocatable Memory
 ├── Stable Memory
 ├── Copy-on-Write
 ├── Shared Memory
 ├── Zero-Copy
 ├── NUMA
 ├── Large Pages
 ├── Pinned Memory
 ├── DMA
 ├── Device Memory
 ├── Tensor Memory
 ├── Sparse Memory
 ├── Memory Aliasing
 ├── No-Alias Contract
 ├── Volatile/MMIO
 ├── Memory Pressure
 ├── Reclamation
 ├── Fragmentation Control
 ├── Memory Quota
 ├── Secure Memory
 ├── Zeroization
 ├── Memory Debugging
 ├── Memory Profiling
 ├── Deterministic Allocation
 ├── Snapshot
 ├── Crash Dump Boundary
 ├── Compiler Optimization
 ├── FFI / ABI
 ├── Cross-Platform Backend
 ├── AI Boundary
 ├── Native API
 ├── 40 Formal Invariants
 └── Memory Runtime 5.0
```

**BOOTSTRAP-745 / AXMEMORY — ARCHITECTURAL BASELINE FROZEN.**

---

# BOOTSTRAP-746 — AXIPC

**Native Inter-Process Communication & Message Runtime — channels, ports, message queues, typed messages, shared-memory transport, zero-copy transfer, capability/handle passing, local RPC, request/response, streaming IPC, event notification, wait sets, deadlines, cancellation, backpressure, flow control, process discovery, endpoint lifecycle, connection supervision, IPC security, cross-process synchronization, memory ownership transfer, local/remote IPC boundary, deterministic replay, IPC tracing, simulation và IPC Runtime 5.0.**