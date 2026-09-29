Tiếp tục.

# Axiom — Memory Allocation, Heap, Arena, Pool & Fragmentation v0.1

Đây là phần rất quan trọng đối với mục tiêu của Axiom. Và tôi muốn chốt một điểm ngay từ đầu:

> **Không nên chọn “flat memory model” như một chiến lược cấp phát. Flat address space và allocator là hai vấn đề khác nhau.**

Axiom nên có **flat virtual address space + nhiều storage strategy**, để compiler tự chọn khi có thể.

---

# 1. Tách 4 khái niệm

Axiom phải phân biệt:

```text
Address Space
    ↓
Storage
    ↓
Allocation Strategy
    ↓
Physical Memory
```

Ví dụ:

```text
Virtual address space
        │
        ├── stack storage
        ├── heap storage
        ├── arena storage
        ├── static storage
        ├── TLS
        ├── mapped file
        └── device/GPU memory
```

Không có chuyện:

```text
heap = memory model
```

---

# 2. Flat address space

Trên hệ thống thông thường:

```text
process virtual address space
```

là một không gian địa chỉ phẳng về mặt lập trình.

Axiom giữ mô hình này.

Programmer không phải viết:

```text
near pointer
far pointer
segment
selector
```

trừ system/legacy targets.

---

# 3. Nhưng flat address space không chống fragmentation

Ví dụ heap:

```text
[A][free][B][free][C][free][D]
```

vẫn có fragmentation.

Flat address space chỉ nói:

> các địa chỉ được biểu diễn trong một không gian địa chỉ thống nhất.

Nó không quyết định:

- allocator;
- lifetime;
- compaction;
- locality;
- fragmentation.

---

# 4. Vì vậy Axiom không dùng một allocator duy nhất

Đây là quyết định quan trọng.

Không:

```text
Axiom
  ↓
GlobalAllocator
  ↓
mọi allocation
```

Mà:

```text
Axiom Storage
 ├── Stack
 ├── Inline
 ├── Static
 ├── Heap
 ├── Arena
 ├── Pool
 ├── Slab
 ├── External
 └── Device
```

---

# 5. Storage selection là compiler freedom

Ví dụ:

```axiom
fn make() -> BigStruct {
    return BigStruct(...)
}
```

Compiler có thể:

```text
register
stack
caller storage
```

Không có nghĩa:

```text
return => heap allocation
```

---

# 6. Escape analysis

Compiler phân tích:

```text
NO_ESCAPE
LOCAL_ESCAPE
CALL_ESCAPE
RETURN_ESCAPE
GLOBAL_ESCAPE
FFI_ESCAPE
UNKNOWN_ESCAPE
```

Ví dụ:

```axiom
fn foo() {
    let x = Vec2(...)
    use(x)
}
```

Nếu `x` không escape:

```text
register / stack / scalarized
```

---

# 7. Heap allocation không mặc định

Ví dụ:

```axiom
let x = Box.new(value)
```

về semantic:

> `x` có dynamic storage identity.

Nhưng compiler vẫn có thể loại bỏ allocation nếu không observable.

Ví dụ:

```text
Box allocation
    ↓
no address escape
    ↓
scalar replacement
    ↓
no heap allocation
```

---

# 8. Khi nào heap allocation thực sự bắt buộc?

Khi storage identity observable.

Ví dụ:

```axiom
let p = Box.new(value)
let address = addr_of(p)
```

hoặc:

```text
return Box
```

hoặc:

```text
foreign API retains pointer
```

Lúc đó compiler không được biến storage thành register giả tạo nếu làm thay đổi observable semantics.

---

# 9. Stable address là semantic contract

Đây là nguyên tắc quan trọng:

> **Địa chỉ ổn định chỉ tồn tại khi programmer/library yêu cầu storage identity ổn định.**

Không phải mọi object đều stable address.

---

# 10. `Box<T>`

`Box<T>` là abstraction:

```text
owned
non-Copy
Drop
dynamic storage
stable address
```

Conceptually:

```text
Box<T>
  ↓
allocation
  ↓
T
```

Nhưng implementation allocation có thể được optimizer loại bỏ nếu address không observable.

---

# 11. `Vec<T>`

`Vec<T>` khác:

```text
owned
dynamic
contiguous
relocatable
```

Ví dụ:

```text
Vec
 ┌───────────────────────┐
 │ A │ B │ C │ D │ ...   │
 └───────────────────────┘
```

`push()` có thể:

```text
reallocate
copy/move elements
free old storage
```

---

# 12. `reserve()` không đảm bảo stable address

Đã chốt:

```text
reserve()
```

chỉ đảm bảo capacity semantic.

Không có:

```text
reserve => address forever stable
```

Nếu cần stable:

```text
Box
Arena
Pool
StableBuffer
```

tùy abstraction.

---

# 13. View và relocation

Ví dụ:

```axiom
let v = view(vec)
vec.push(x)
```

Nếu `push` có khả năng relocate và `v` còn active:

```text
compile error
```

hoặc compiler có thể xác định:

```text
v last-use
```

đã kết thúc trước `push`.

Đây là nơi lifetime analysis thực sự hữu ích **mà programmer không phải viết lifetime**.

---

# 14. Đây là cách tránh borrow-checker UX

Programmer không viết:

```text
'a
'b
where 'a: 'b
```

Chỉ viết:

```axiom
let first = vec[0]
use(first)

vec.push(x)
```

Compiler tự biết:

```text
first capability expired
```

→ `push` hợp lệ.

---

# 15. Arena

Arena giải quyết một loại fragmentation khác.

Conceptually:

```text
Arena
 ┌──────────────────────────────┐
 │ allocation │ allocation │... │
 └──────────────────────────────┘
```

Allocations được tạo nhanh.

Cleanup:

```text
drop arena
```

→ giải phóng cả region.

---

# 16. Arena không phải GC

Arena:

```text
explicit owner
deterministic lifetime
bulk destruction
```

Không:

```text
trace object graph
find unreachable object
```

Do đó rất phù hợp:

- compiler;
- parser;
- AST;
- game frame;
- request processing;
- temporary graph.

---

# 17. Arena lifetime

Ví dụ:

```axiom
let arena = Arena.new()

let node = arena.alloc(Node(...))
```

`node` không được escape:

```text
arena lifetime
    └── node capability
```

Compiler phải ngăn:

```axiom
return node
```

nếu return ra ngoài arena.

---

# 18. Nhưng programmer không cần lifetime annotation

Compiler chỉ báo:

```text
AX_ARENA_0001

value allocated from arena may outlive its owner

owner:
    arena

escaping value:
    node
```

---

# 19. Pool

Pool phù hợp khi object:

- cùng size;
- lifetime thay đổi;
- cần stable address;
- allocation/deallocation thường xuyên.

Ví dụ:

```text
Pool<Node>
```

```axiom
let id = pool.insert(node)
```

hoặc:

```axiom
let slot = pool.alloc()
```

---

# 20. Pool + Handle

Đây là mô hình rất mạnh cho graph/game/ECS.

```text
Pool<Node>
     │
     ├── slot 0 → Node
     ├── slot 1 → Node
     └── slot 2 → Node

Handle<Node>
```

Handle không phải pointer.

---

# 21. Generation handle

Conceptually:

```text
Handle<T> {
    index
    generation
}
```

Ví dụ:

```text
Node #42 generation 7
```

remove:

```text
generation → 8
```

handle cũ:

```text
#42/7
```

không còn hợp lệ.

---

# 22. Đây là cách tránh dangling graph pointer

Thay vì:

```text
Node
  → raw pointer
  → Node
```

safe Axiom:

```text
Node
  → Handle<Node>
```

Pool kiểm tra generation.

---

# 23. Nhưng Handle không phải memory safety primitive của Core

Nó là library abstraction.

Compiler chỉ biết:

```text
Pool<T>
```

nếu library semantic contract cung cấp capability.

Ứng dụng không bắt buộc phải dùng handle.

---

# 24. Slab

Slab là specialization của pool:

```text
integer-like slot
stable storage
cheap allocation
```

Rất hữu ích cho:

- file descriptors;
- sockets;
- ECS;
- OS resources;
- networking.

Library-level.

---

# 25. Stack allocation

Stack rất nhanh trong nhiều trường hợp, nhưng không phải mọi local đều “nằm trên stack”.

Compiler có thể:

```text
register
stack
caller frame
scalarized
```

Axiom không expose:

```text
stack<T>
```

ở Core.

---

# 26. Không có `alloca` source primitive

Không:

```axiom
alloca(...)
```

trong safe Core.

Compiler tự tạo stack slot khi cần.

System layer có thể có low-level primitive nếu target yêu cầu.

---

# 27. Static storage

```axiom
static CONFIG: Config = ...
```

có:

```text
program lifetime
stable identity
```

Khác:

```text
const CONFIG
```

là compile-time value, không có runtime storage identity.

---

# 28. TLS

```axiom
thread_static var state: State
```

có:

```text
one instance / thread
```

Compiler/OS quản lý storage.

---

# 29. External memory

Axiom phải hỗ trợ:

```text
memory-mapped file
shared memory
foreign buffer
DMA buffer
device memory
MMIO
```

nhưng không đưa tất cả vào Core type system.

System layer có:

```text
ExternalBuffer<T>
DeviceBuffer<T>
MappedRegion
```

---

# 30. External memory phải có ownership contract

Ví dụ:

```text
external buffer
```

có thể:

```text
BORROWED
OWNED
SHARED
DEVICE_OWNED
FOREIGN_OWNED
```

Compiler không được đoán bừa.

FFI wrapper phải định nghĩa contract.

---

# 31. Fragmentation

Có ít nhất ba loại cần phân biệt.

### External fragmentation

```text
free blocks scattered
```

### Internal fragmentation

```text
allocated block > requested size
```

### Virtual address fragmentation

```text
address-space holes
```

Chúng không giống nhau.

---

# 32. Flat address space không loại bỏ external fragmentation

Ví dụ:

```text
┌────┬────┬────┬────┬────┐
│ A  │free│ B  │free│ C  │
└────┴────┴────┴────┴────┘
```

Tổng free:

```text
40 MB
```

nhưng không có block contiguous 30 MB.

---

# 33. Arena gần như loại bỏ một dạng fragmentation

Arena thường:

```text
allocate → bump pointer
```

rất đơn giản:

```text
[used used used used | free.........]
                    ↑
                  cursor
```

Không free từng object.

Khi arena reset:

```text
cursor = beginning
```

---

# 34. Nhưng Arena có trade-off

Không thể giải phóng từng object dễ dàng.

Nếu:

```text
1000 objects
```

chỉ còn 1 object cần sống:

```text
arena vẫn giữ region
```

Do đó arena không phải universal allocator.

---

# 35. Pool giải quyết pattern khác

Nếu object có lifetime độc lập:

```text
Pool
```

tốt hơn:

```text
Arena
```

vì slot có thể reuse.

---

# 36. Slab giảm fragmentation cho fixed-size object

Ví dụ:

```text
Slab<Node>
```

mọi slot:

```text
sizeof(Node)
```

nên fragmentation thấp.

---

# 37. General heap

Vẫn cần.

Axiom không nên tự viết:

```text
one magical allocator
```

mà library có:

```text
SystemAllocator
GeneralAllocator
Arena
Pool
Slab
```

---

# 38. Allocator abstraction

Có thể có:

```text
trait Allocator
```

nhưng **không nên ép mọi collection thành generic trên allocator**.

Không muốn:

```axiom
Vec<T, A: Allocator>
HashMap<K,V,A>
String<A>
Box<T,A>
...
```

tràn ngập API.

---

# 39. Đây là một điểm tôi muốn thay đổi mạnh so với Rust-style design

Allocator là implementation/storage concern trong đa số code.

Do đó:

```axiom
Vec<T>
```

mặc định.

Không:

```axiom
Vec<T, Global>
```

mọi nơi.

---

# 40. Custom allocator vẫn phải có đường đi

Ví dụ system code:

```axiom
let arena = Arena.new(...)
let vec = arena.vec<i32>()
```

hoặc API storage-specific:

```axiom
Vec.in(arena)
```

Nhưng collection type identity không nhất thiết phải encode allocator.

---

# 41. Vì sao?

Nếu allocator trở thành type parameter:

```text
Vec<T,A>
```

thì allocator lan khắp:

- function signatures;
- traits;
- generic constraints;
- type inference;
- ABI.

Chi phí ngôn ngữ rất lớn.

Trong khi nhiều trường hợp compiler có thể erase abstraction.

---

# 42. Storage context

Một hướng tốt hơn:

```text
StorageContext
```

library/system abstraction.

Ví dụ:

```axiom
with arena {
    let v = Vec.new<i32>()
}
```

Compiler/library có thể associate allocations với context.

Nhưng đây nên là library feature, chưa đưa vào Core syntax v0.1.

---

# 43. Allocation semantics

MIR:

```text
ALLOC
DEALLOC
```

là semantic operations.

Không:

```text
CALL malloc
CALL free
```

ngay từ MIR.

---

# 44. Vì sao?

Compiler có thể biến:

```text
ALLOC
```

thành:

```text
stack
```

hoặc:

```text
pool
```

hoặc:

```text
inline
```

hoặc:

```text
heap
```

tùy contract.

---

# 45. Allocation elimination

Ví dụ:

```axiom
fn foo() -> i32 {
    let x = Box.new(42)
    *x
}
```

Compiler:

```text
Box allocation
    ↓
address never escapes
    ↓
scalar replacement
    ↓
return 42
```

Binary cuối cùng không có allocation.

---

# 46. Caller-allocated return

Ví dụ:

```axiom
fn make_big() -> BigStruct
```

không nhất thiết:

```text
callee malloc
callee fills
callee returns pointer
```

Compiler có thể:

```text
caller allocates destination
callee writes directly
```

hoặc register return.

---

# 47. Đây là một optimization rất quan trọng

Đặc biệt với:

- strings;
- arrays;
- large structs;
- image buffers;
- math structures.

Không cần programmer viết:

```text
out parameter
```

để đạt hiệu năng.

---

# 48. Move không phải memcpy

```axiom
let b = a
```

nếu `a: !Copy`:

```text
ownership state:
a → MOVED
b → OWNED
```

Compiler có thể:

```text
register transfer
pointer transfer
no physical copy
```

---

# 49. Copy cũng không nhất thiết là function call

```axiom
let b = a
```

nếu `Copy`:

```text
machine-level copy
```

có thể:

```text
register
SIMD
memcpy
scalar
```

tùy size.

---

# 50. Large copy diagnostics

Axiom tooling nên có:

```text
axiom inspect --copies
```

Ví dụ:

```text
Copy cost:
    Matrix<1024> copied at foo:42
    estimated size: 4 MB
```

Không phải compiler error.

---

# 51. Stable address

Ta có các abstraction:

```text
Box<T>
Arena<T>
Pool<T>
Static<T>
ExternalBuffer<T>
```

đều có thể cung cấp stable storage.

Còn:

```text
Vec<T>
Array<T,N>
local T
```

không mặc định stable address.

---

# 52. Không cần `Pin<T>`

Tôi giữ quyết định trước:

> **Không đưa `Pin<T>` vào Core.**

Nếu library cần:

```text
StableBox<T>
PinnedStorage<T>
```

có thể xây bằng storage contract.

---

# 53. `Relocatable` và `StableAddress`

Compiler nội bộ có thể có property:

```text
STORAGE_RELOCATABLE
STORAGE_STABLE
```

Không nhất thiết expose thành source traits.

---

# 54. Address observability

Khi programmer làm:

```text
addr_of(x)
```

compiler biết:

```text
address observable
```

Storage contract trở nên mạnh hơn.

Có thể không còn:

```text
register scalarization
```

nếu làm thay đổi semantics.

---

# 55. Nhưng address không phải integer

Đã chốt:

```text
Pointer ≠ Address ≠ usize
```

Ví dụ:

```text
addr_of(p)
```

trả:

```text
addr
```

không phải:

```text
usize
```

Muốn convert:

```text
unsafe
```

---

# 56. Pointer provenance

Safe compiler theo dõi:

```text
AllocationId
Region
Capability
```

Unsafe raw pointer có thể phá vỡ provenance reasoning.

Nhưng compiler không được vì thế mà coi toàn bộ chương trình là không thể tối ưu.

Nó dùng conservative alias facts tại unsafe boundary.

---

# 57. Fragmentation và compiler optimization

Một insight quan trọng:

> **Compiler tối ưu allocation count, allocator tối ưu allocation placement.**

Hai lớp khác nhau.

Compiler:

```text
allocation elimination
stack promotion
scalar replacement
lifetime shortening
```

Allocator:

```text
binning
coalescing
pooling
arena
reuse
```

---

# 58. Lifetime shortening cực kỳ quan trọng

Ví dụ:

```axiom
{
    let x = allocate()
    use(x)
}

do_other_work()
```

Compiler biết:

```text
x lifetime ends
```

sớm hơn lexical function end.

Điều này cho allocator cơ hội:

```text
reuse memory
```

---

# 59. Nhưng Drop semantics vẫn đúng

Nếu `x: Drop`:

```text
last semantic use
    ↓
Drop may happen
```

nhưng compiler chỉ được early-drop khi:

```text
Drop observable semantics
```

không bị thay đổi.

---

# 60. Resource lifetime vs memory lifetime

Hai thứ không giống nhau.

```text
File
```

có resource lifetime.

```text
memory block
```

có storage lifetime.

Drop File có thể:

```text
close(fd)
```

không nhất thiết liên quan `free()`.

---

# 61. Vì vậy Drop không đồng nghĩa deallocation

Ví dụ:

```text
MutexGuard.Drop
    → unlock

File.Drop
    → close

GpuCommandBuffer.Drop
    → release GPU resource

Arena allocation Drop
    → có thể không làm gì riêng lẻ
```

Đây là lý do abstraction ownership rất mạnh.

---

# 62. Allocator failure

Heap allocation có thể thất bại.

Không nên panic mặc định cho mọi allocation.

Tôi đề xuất API phân biệt:

```text
try_allocate() -> Result
allocate() -> policy-dependent
```

Standard collection:

```text
Vec.new()
```

có thể dùng configured allocation failure policy.

---

# 63. Nhưng `Drop` không được fail

Đã chốt.

```text
allocation failure
    → Result / panic policy

Drop
    → guaranteed cleanup
```

Không:

```text
Drop -> Result
```

---

# 64. OOM policy

Axiom có thể hỗ trợ profile:

```text
--oom=panic
--oom=abort
--oom=handler
```

nhưng semantics cần được thống nhất.

Tôi đề xuất v0.1:

> **Allocation APIs có `try_*`; high-level convenience APIs có thể panic/abort theo profile.**

Như vậy system programming vẫn kiểm soát được OOM.

---

# 65. Embedded/freestanding

Không được giả định heap tồn tại.

Ví dụ:

```text
@freestanding
```

có thể:

```text
Array
Arena
Pool
static storage
stack
```

mà không cần allocator.

---

# 66. GPU

GPU memory cũng không phải heap của CPU.

Ví dụ:

```text
DeviceBuffer<T>
```

có storage domain:

```text
DEVICE
```

và transfer explicit.

Compiler không tự:

```text
CPU pointer → GPU pointer
```

---

# 67. Shared memory

Có thể:

```text
SharedMemory<T>
```

library/system abstraction.

Ownership contract phải rõ:

```text
process A
process B
```

cùng access.

---

# 68. Memory mapped file

Ví dụ:

```text
MappedRegion
```

có thể cung cấp:

```text
view<u8>
```

nhưng Drop phải unmap.

Đây là ví dụ đẹp cho:

```text
resource lifetime
+
memory capability
```

---

# 69. Allocator-independent ABI

Stable ABI không nên truyền:

```text
Vec<T>
Box<T>
String
```

mặc định.

Nó nên truyền:

```text
pointer
length
opaque handle
explicit ownership function
```

hoặc ABI-defined containers.

---

# 70. Một stable ABI buffer

Conceptually:

```text
AbiBuffer {
    data: *mut u8
    len: usize
    capacity: usize
    allocator_id: ...
}
```

nhưng `allocator_id` chỉ cần nếu hai bên có thể free.

Tốt hơn nữa:

```text
caller allocates
callee fills
```

hoặc:

```text
callee allocates
callee exposes destroy()
```

---

# 71. Đây là nguyên tắc FFI rất mạnh

> **Allocation domain must have a clear owner.**

Không:

```text
A allocates
B guesses how to free
```

---

# 72. Compiler không ép một memory model duy nhất

Axiom source:

```axiom
let data = ...
```

không cần nói:

```text
stack
heap
arena
```

trừ khi programmer thực sự cần semantics đó.

Đây chính là:

> **Storage abstraction.**

---

# 73. Khi programmer cần kiểm soát

System code có thể chọn:

```text
Box
Arena
Pool
Static
MappedRegion
DeviceBuffer
```

Đủ mạnh để viết:

- OS;
- game engine;
- database;
- compiler;
- renderer;
- embedded;
- high-frequency networking.

---

# 74. Không nên có “GC escape hatch”

Axiom Core:

```text
no GC
```

Nhưng ecosystem có thể xây:

```text
Gc<T>
```

library/system.

Nếu cần tracing GC cho scripting engine:

```text
engine::Gc
```

không làm language runtime bắt buộc phải có GC.

---

# 75. Reference counting cũng vậy

```text
Arc<T>
Rc<T>
```

library.

Không implicit.

Do đó:

```text
single-owner data
```

không phải trả chi phí atomic refcount.

---

# 76. Đây là điểm Axiom có thể vượt mô hình managed language

Hot path:

```text
T
```

→ ownership.

Không:

```text
GC barrier
RC increment
RC decrement
object header
```

nếu không cần.

---

# 77. Memory model tổng hợp

```text id="s3x5w0"
                    Axiom Value
                         │
             ┌───────────┼───────────┐
             │           │           │
           Inline      Dynamic     External
             │           │           │
          register      Box         FFI
          stack         Vec         mmap
          static        Arena       GPU
          TLS           Pool        shared
                        Slab
```

Và:

```text
Value
  ≠
Storage
  ≠
Address
  ≠
Pointer
  ≠
View
  ≠
Ownership
```

Đây nên trở thành một trong những nguyên tắc nền tảng nhất của Axiom.

---

# 78. Allocation invariants

Đóng băng:

```text id="qzqg1c"
AMEM-16  Address Space Is Independent From Allocation Strategy
AMEM-17  Flat Address Space Does Not Guarantee Fragmentation Freedom
AMEM-18  Storage Strategy Is Not Part Of Ordinary Value Type Semantics
AMEM-19  Heap Allocation Is Not Mandatory
AMEM-20  Compiler May Eliminate Unobservable Allocation
AMEM-21  Stable Address Is An Explicit Storage Contract
AMEM-22  Relocatable Storage May Move
AMEM-23  Reserve Does Not Imply Stable Address
AMEM-24  Dependent Views Block Invalid Relocation
AMEM-25  Escape Analysis Determines Storage Optimization Opportunities
AMEM-26  Allocation Is A Semantic MIR Operation Before Lowering
AMEM-27  Move Does Not Imply Physical Copy
AMEM-28  Return Does Not Imply Heap Allocation
AMEM-29  Caller-Allocated Returns Are Permitted
AMEM-30  Stack Storage Is A Compiler Strategy
AMEM-31  Register Storage Is A Compiler Strategy
AMEM-32  Static Storage Has Program Lifetime
AMEM-33  TLS Has Per-Thread Storage Identity
AMEM-34  Arena Ownership Bounds Arena Allocations
AMEM-35  Arena Allocation Does Not Imply Garbage Collection
AMEM-36  Pool Storage Supports Reusable Stable Slots
AMEM-37  Slab Storage Is A Fixed-Size Pool Strategy
AMEM-38  Handles Are Logical Identity, Not Raw Addresses
AMEM-39  Generation Handles Can Prevent Stale Logical References
AMEM-40  Custom Allocators Are Library/System Abstractions
AMEM-41  Allocator Choice Is Not A Mandatory Generic Parameter
AMEM-42  Collection APIs Do Not Expose Allocator Parameters By Default
AMEM-43  Resource Lifetime Is Distinct From Memory Lifetime
AMEM-44  Drop Does Not Necessarily Deallocate Memory
AMEM-45  Drop Is Non-Fallible
AMEM-46  Allocation Failure Is Distinct From Resource Cleanup
AMEM-47  Freestanding Programs Need Not Have A Heap
AMEM-48  Device Memory Is A Distinct Storage Domain
AMEM-49  External Memory Requires An Explicit Ownership Contract
AMEM-50  Stable ABI Must Define Allocation Ownership
AMEM-51  FFI Must Not Guess Allocation Domains
AMEM-52  GC Is Not A Core Runtime Requirement
AMEM-53  Reference Counting Is Not An Implicit Language Mechanism
AMEM-54  Compiler Lifetime Analysis May Shorten Storage Lifetime
AMEM-55  Observable Addresses Constrain Storage Optimization
AMEM-56  Storage Identity Is Distinct From Value Identity
AMEM-57  Fragmentation Is An Allocation-Strategy Property
AMEM-58  Allocation Placement Is An Allocator Responsibility
AMEM-59  Allocation Elimination Is A Compiler Responsibility
AMEM-60  Memory Strategy Is Explicit Only When Semantically Relevant
```

---

# 79. Một thay đổi quan trọng đối với cách chúng ta nhìn Axiom

Sau tất cả các phần trên, tôi nghĩ mô hình bộ nhớ tốt nhất cho Axiom không phải:

> “stack language” hay “heap language” hay “flat memory language”.

Mà là:

> **Value-centric + ownership-centric + storage-agnostic.**

Programmer nghĩ:

```text
Ai sở hữu giá trị?
Giá trị có thể được chia sẻ không?
Tôi cần địa chỉ ổn định không?
Tôi cần storage đặc biệt không?
```

Compiler nghĩ:

```text
Nó nằm ở đâu?
Có cần allocation không?
Có thể scalarize không?
Có thể relocate không?
Có thể vectorize không?
Có thể reuse storage không?
```

Hai bên không cần dùng cùng một abstraction level.

Đây chính xác là hướng phù hợp với mục tiêu ban đầu của bạn: **không bắt lập trình viên phải quản lý pointer/reference/lifetime một cách thủ công, nhưng vẫn cho compiler đủ thông tin để tạo machine code rất thấp tầng.**

---

# Tiếp tục

Phần tiếp theo nên chuyển sang một vấn đề mà Axiom hiện đã đủ nền móng để giải quyết:

## **Error Handling + Panic + Result + Failure Semantics hoàn chỉnh**

Ta cần khóa:

```text
Result<T,E>
Option<T>
?
panic
abort
unwind
recover
fatal error
OOM
FFI errors
OS errors
async cancellation
thread failure
GPU failure
destructor failure
error propagation
error type design
zero-cost error handling
```

Đặc biệt cần trả lời:

> **Axiom có cần `try/catch/throw` hay `exceptions` không, hay `Result + ? + panic/unwind` đã đủ cho cả application lẫn systems programming?**

Và quan trọng hơn: thiết kế sao cho **happy path gần như không có runtime overhead**, nhưng error path vẫn đủ mạnh để viết ứng dụng lớn.