# BOOTSTRAP-022 — Memory Allocation, Reclamation & Object Lifetime Runtime

Đây là phần nên khóa ngay sau memory model, vì nó trả lời câu hỏi cốt lõi của Axiom:

> **Nếu không GC, không implicit RC, không borrow checker, nhưng vẫn muốn safe + nhanh + ít phiền phức, Axiom thực sự quản lý object/memory như thế nào?**

Tôi đề xuất Axiom đi theo mô hình:

> **Ownership quyết định ai chịu trách nhiệm. Capability quyết định ai được truy cập. Lifetime analysis quyết định khi nào không còn cần nữa. Allocator quyết định đặt memory ở đâu.**

Bốn thứ này **không được trộn thành một cơ chế duy nhất**.

---

# 1. Bốn lifetime khác nhau

Axiom cần chính thức hóa điều này.

```text
             VALUE
               │
        ┌──────┴──────┐
        │             │
    Resource       Storage
     lifetime       lifetime
        │             │
        └──────┬──────┘
               │
         Capability
          lifetime
```

Cụ thể:

### Value lifetime

Giá trị còn tồn tại về mặt semantic.

```axiom
var x = Foo()
```

### Resource lifetime

Resource mà `x` sở hữu còn hợp lệ:

```text
file
socket
mutex permit
GPU allocation
OS handle
```

### Storage lifetime

Memory chứa object còn tồn tại.

### Capability lifetime

`view<T>` / `mut_view<T>` còn được phép truy cập.

Chúng **có thể kết thúc ở những thời điểm khác nhau**.

---

# 2. Drop không đồng nghĩa free

Đây là invariant cực kỳ quan trọng.

```axiom
drop(x)
```

không có nghĩa bắt buộc:

```text
free(memory(x))
```

Ví dụ Arena:

```text
Arena
 ├── Object A
 ├── Object B
 └── Object C
```

Drop A có thể:

```text
release resource A
```

nhưng memory vật lý chỉ được reclaim khi:

```text
drop(Arena)
```

Tương tự pool:

```text
Pool
 ├── slot 0
 ├── slot 1
 ├── slot 2
```

Object có thể chết nhưng slot được tái sử dụng.

---

# 3. Ownership là semantic, không phải allocator

Ví dụ:

```axiom
var x = Foo()
```

Compiler có thể đặt `x`:

```text
register
stack
inline aggregate
heap
arena
pool
static
```

Programmer không được suy ra:

```text
Foo => heap
```

hay:

```text
Foo => stack
```

trừ khi API/storage contract yêu cầu.

Đây là nền tảng để compiler tối ưu allocation.

---

# 4. Khi nào allocation thực sự cần thiết?

Axiom nên có một nguyên tắc:

> **Allocation chỉ tồn tại trong final machine code nếu storage identity hoặc lifetime semantics thực sự yêu cầu nó.**

Ví dụ:

```axiom
fn make() -> Vec2 {
    return Vec2(10, 20)
}
```

Không cần:

```text
malloc
copy
free
```

Compiler có thể:

```text
caller stack
register pair
sret
```

---

# 5. Escape analysis

Đây là một trong những vũ khí quan trọng nhất của Axiom.

```axiom
fn foo() {
    var x = BigObject()

    use(x)
}
```

Nếu `x` không escape:

```text
BigObject
   ↓
LOCAL
   ↓
no escaping capability
   ↓
no observable address
```

Compiler có thể:

```text
stack
```

hoặc thậm chí:

```text
register/scalarized
```

Nếu `x` cần stable address:

```axiom
get_address(x)
```

thì storage contract thay đổi.

---

# 6. Address observability

Đây là ranh giới rất quan trọng.

Trước:

```axiom
var x = Foo()
use(x)
```

Compiler tự do.

Sau:

```axiom
let p = address_of(x)
```

địa chỉ trở thành observable.

Khi đó compiler phải tôn trọng:

```text
stable address contract
```

nếu API yêu cầu.

Không thể tiếp tục:

```text
move x
relocate x
```

nếu làm thay đổi semantic observable address.

---

# 7. Không nên có `@heap`

Tôi không khuyến nghị syntax kiểu:

```axiom
@heap var x = Foo()
```

trong Core.

Nó làm storage strategy trở thành language-level concern quá sớm.

Thay vào đó:

```axiom
var x = Box(Foo(...))
```

nếu programmer thực sự cần **owned dynamic storage semantics**.

---

# 8. `Box<T>` chính thức hóa dynamic ownership

`Box<T>` nên có semantics:

```text
owned
dynamic-storage
stable-identity
non-Copy
Drop
```

Nhưng:

> **Box không nhất thiết phải kết thúc bằng heap allocation.**

Compiler có thể stack-promote/eliminate nó nếu:

- address không observable
- dynamic storage semantics không externally observable
- lifetime vẫn giữ đúng semantics.

Ví dụ:

```axiom
fn foo() {
    var x = Box(Foo())
    consume(x)
}
```

có thể không có allocation cuối cùng.

---

# 9. Khi nào Box thật sự cần allocation?

Ví dụ:

```axiom
fn create() -> Box<Foo> {
    return Box(Foo())
}
```

nếu `Box<Foo>` trở thành stable dynamic owner được caller giữ lâu dài:

```text
caller
   ↓
Box<Foo>
   ↓
stable storage identity
```

thì allocation thường tồn tại.

Nhưng allocation strategy vẫn thuộc implementation/runtime.

---

# 10. `Vec<T>` không phải chỉ là `ptr,len,cap`

Về semantic, `Vec<T>` phải có:

```text
logical region
length
capacity
storage identity
relocation policy
ownership
```

Representation có thể là:

```text
ptr + len + cap
```

nhưng đó chỉ là implementation phổ biến.

Compiler được phép thay đổi representation nếu ABI không bị freeze.

---

# 11. Vec relocation

Ví dụ:

```axiom
var v = Vec<i32>()

v.push(1)
v.push(2)
v.push(3)
```

Có thể relocation:

```text
old storage
    ↓
new storage
    ↓
move elements
```

Do đó:

```axiom
let p = view(v)
v.push(...)
```

không thể tùy tiện cho phép nếu `push` có thể relocate và `p` còn sống.

Compiler phải thấy:

```text
potential relocation
       ×
dependent view
```

=> reject hoặc API phải cung cấp storage contract phù hợp.

---

# 12. `reserve()` không bảo đảm stable address

Đây là quyết định nên giữ rất rõ:

```axiom
v.reserve(1024)
```

chỉ đảm bảo capacity đủ theo semantic của `Vec`.

Không nên hiểu:

```text
reserve
=
address never changes
```

Nếu cần stable address:

```text
Box
Arena
Pool
StableVec
```

hoặc abstraction tương ứng.

---

# 13. StableVec nên là library type

Không đưa stable-address collection vào Core.

Có thể có:

```axiom
StableVec<T>
```

semantic:

```text
insert
remove
resize
```

nhưng element address vẫn ổn định theo contract.

Implementation có thể:

```text
indirection
slab
pool
segmented storage
```

Không cần programmer biết.

---

# 14. Arena

Arena là abstraction cực kỳ quan trọng với Axiom.

```axiom
var arena = Arena()

var a = arena.alloc(Foo())
var b = arena.alloc(Bar())
```

Semantic:

```text
Arena owns storage
      │
      ├── Foo
      └── Bar
```

`a` không được escape khỏi lifetime của arena.

Nhưng Arena không phải GC.

Không có:

```text
tracing
mark
sweep
```

Mà:

```text
drop Arena
    ↓
reclaim region
```

---

# 15. Arena + compiler lifetime inference

Điểm rất mạnh:

Programmer không cần viết:

```text
'a
'b
```

Compiler chỉ cần biết:

```text
owner = Arena A
capability depends on Arena A
```

Nếu:

```axiom
fn bad() -> view<Foo> {
    var arena = Arena()
    var x = arena.alloc(Foo())

    return view(x)
}
```

compiler reject:

```text
AXxxxx:
returned capability depends on local Arena
```

Không cần lifetime syntax.

---

# 16. Pool

Pool dành cho object có lifecycle lặp lại:

```text
allocate
use
release
reuse
```

Ví dụ:

```axiom
var pool = Pool<Node>()

var n = pool.acquire()
...
pool.release(n)
```

Không có GC.

Memory:

```text
Pool
 ├── free slot
 ├── used slot
 ├── free slot
 └── used slot
```

---

# 17. Slab

Slab là specialization của pool cho fixed-size object.

Ví dụ:

```text
Slab<Node, 64>
```

có thể có:

```text
O(1) slot allocation
O(1) release
good locality
low fragmentation
```

Đây rất phù hợp:

- networking
- ECS
- kernel
- runtime
- scheduler
- lock-free structures

---

# 18. Flat address space không giải quyết fragmentation

Ta cần khóa lại điều này:

```text
Virtual Address Space
        ≠
Allocator
        ≠
Physical Memory
```

Ví dụ:

```text
Virtual:
0x1000 ─ object
0x2000 ─ free
0x3000 ─ object
0x4000 ─ free
```

Flat address space chỉ nói rằng process nhìn thấy một address space.

Fragmentation phụ thuộc:

```text
allocation pattern
object lifetime
allocator
page size
alignment
arena/pool strategy
virtual memory mapping
```

---

# 19. Axiom nên có nhiều allocator strategy

Không có một allocator duy nhất.

Library/system layer:

```text
GeneralAllocator
Arena
Pool
Slab
StackAllocator
LinearAllocator
RegionAllocator
OSVirtualMemory
GPUAllocator
CustomAllocator
```

Nhưng:

> Allocator không nên trở thành generic parameter bắt buộc của mọi collection.

Không muốn:

```axiom
Vec<T, Allocator>
```

ở khắp nơi.

---

# 20. Vì sao không đưa allocator vào type?

Nếu mọi API thành:

```axiom
Vec<T, A>
Map<K,V,A>
String<A>
Buffer<A>
```

thì:

- type explosion
- generic noise
- inference phức tạp
- API khó đọc
- compiler monomorphization tăng
- programmer phải nghĩ allocator liên tục.

Axiom ưu tiên:

```axiom
Vec<T>
```

và allocator là implementation/library policy.

Chỉ API cần custom allocation mới expose allocator explicitly.

---

# 21. Custom allocator vẫn phải khả thi

Ví dụ hệ thống:

```axiom
var arena = Arena.with(my_allocator)
```

hoặc:

```axiom
var buffer = Buffer.in(arena)
```

nhưng đây là **explicit storage contract**, không phải mặc định của mọi object.

---

# 22. Fragmentation strategy

Để tối ưu fragmentation, Axiom runtime/std nên cung cấp:

### Long-lived heterogeneous

```text
general allocator
```

### Same-lifetime objects

```text
arena
```

### Same-size frequent allocation

```text
pool/slab
```

### Stack-like lifetime

```text
stack/linear allocator
```

### Huge regions

```text
virtual memory reservation
```

### GPU

```text
device allocator
```

Đây thực tế quan trọng hơn việc cố tạo ra một "perfect allocator".

---

# 23. Reclamation

Reclamation là chuyện khác allocation.

Ví dụ lock-free queue:

```text
Thread A
   ↓
reads Node X

Thread B
   ↓
removes Node X
```

Không thể:

```text
free(X)
```

ngay nếu A còn có thể access X.

Đây chính là lý do cần:

```text
hazard pointer
epoch-based reclamation
RCU
generation handle
pool quarantine
```

---

# 24. Không đưa hazard pointer vào language

Tuyệt đối không thêm:

```text
hazard<'a>
epoch<'e>
borrow<'x>
```

vào source language.

Đây là runtime algorithm.

Programmer dùng:

```axiom
ConcurrentMap<K,V>
```

hoặc:

```axiom
LockFreeQueue<T>
```

Runtime implementation có thể dùng:

```text
hazard pointers
EBR
RCU
```

ở bên dưới.

---

# 25. Safe API che giấu reclamation

Ví dụ:

```axiom
var map = ConcurrentMap<Key, Value>()

map.insert(k, v)
var v = map.get(k)
```

`get()` không được trả raw pointer mà runtime có thể reclaim.

Nó có thể trả:

```text
owned snapshot
guard
view tied to guard
handle
```

tùy abstraction.

Compiler hiểu contract.

---

# 26. Generation Handle

Một abstraction rất hợp Axiom:

```text
Handle<T>
```

không phải pointer.

Ví dụ:

```text
EntityId {
    index
    generation
}
```

Pool:

```text
slot 42 generation 7
```

remove:

```text
slot 42 generation 8
```

Old handle:

```text
42:7
```

không còn hợp lệ.

Điều này giải quyết rất nhiều vấn đề game engine/ECS mà không cần pointer safety bureaucracy.

---

# 27. Ba loại identity chính thức

Ta đã có quyết định này, giờ cần gắn vào allocator model:

```text
Value Identity
Storage Identity
Logical Identity
```

### Value

```axiom
var a = Foo()
var b = a
```

nếu Copy:

```text
a != b
```

về ownership/value.

### Storage

```axiom
var a = Box(Foo())
```

có stable storage identity theo contract.

### Logical

```axiom
EntityId(42, 7)
```

identity tồn tại độc lập với địa chỉ.

---

# 28. Đây là cách Axiom tránh pointer-centric programming

C++ thường khiến programmer nghĩ:

```text
address → object
```

Axiom nên khuyến khích:

```text
value → object
handle → logical entity
Box → stable storage
view → temporary access
raw pointer → machine-level only
```

Điều này làm code dễ hơn đáng kể.

---

# 29. Lock-free reclamation và ownership

Ví dụ:

```text
Arc
```

giải quyết ownership bằng reference count.

Nhưng:

```text
Arc
```

không giải quyết mọi lock-free reclamation problem.

Với high-performance runtime:

```text
Arc
Hazard
Epoch
RCU
Pool
```

là các chiến lược khác nhau.

Không nên biến Arc thành "memory safety mechanism duy nhất".

---

# 30. RC không implicit

Axiom giữ nguyên:

```text
Rc<T>
Arc<T>
```

là library types.

Không có:

```text
implicit retain
implicit release
```

cho mọi reference.

Lý do:

```text
hidden atomic increments
hidden decrements
cache contention
cycles
unpredictable cost
```

đặc biệt không phù hợp mục tiêu performance.

---

# 31. Nhưng compiler có thể optimize explicit Arc

Nếu compiler thấy:

```axiom
var x = arc.clone()
use(x)
```

và có thể chứng minh clone/drop không observable ngoài refcount semantics, có thể optimize.

Tuy nhiên phải cẩn thận vì refcount có thể observable thông qua:

```text
Weak
destruction timing
custom hooks
concurrency
```

Do đó chỉ được erase khi semantic equivalence chứng minh được.

---

# 32. Allocation failure

Không nên dùng exception.

Ví dụ:

```axiom
var x = Box.try_new(Foo(...))?
```

có thể:

```text
Result<Box<Foo>, AllocError>
```

Trong API mặc định có thể có:

```axiom
Box.new(...)
```

với policy:

```text
panic/abort on allocation failure
```

Tùy std profile.

Freestanding có thể:

```text
no heap
```

hoàn toàn.

---

# 33. OOM không phải Drop error

Nếu allocation thất bại:

```text
AllocError
```

không liên quan:

```text
Drop
```

Drop vẫn non-fallible.

Không được có:

```text
Drop → Result
```

vì nó làm cleanup graph cực kỳ phức tạp.

---

# 34. Resource lifetime vs memory lifetime

Ví dụ socket:

```text
Socket
 ├── OS resource
 └── memory handle
```

`drop(socket)`:

```text
close OS resource
```

nhưng memory chứa object có thể nằm:

```text
stack
arena
pool
```

Do đó:

```text
resource lifetime
≠
storage lifetime
```

Đây là lý do `Drop` không nên được định nghĩa là "free".

---

# 35. Memory reclamation trong async

Một buffer:

```axiom
read_async(buffer)
```

OS có thể còn đang sử dụng buffer.

Do đó:

```text
Future pending
    ↓
buffer capability remains live
```

không được reclaim.

Khi operation completion/cancellation contract xác nhận OS không còn truy cập:

```text
buffer becomes reclaimable
```

Điều này nối trực tiếp:

```text
async
+
ownership
+
capability
+
OS I/O
+
reclamation
```

---

# 36. Cancellation không được free buffer sớm

Ví dụ:

```axiom
var buffer = Buffer(...)
var op = socket.read_async(buffer)

op.cancel()
```

Không được giả định:

```text
cancel()
↓
buffer free
```

trừ khi API contract nói cancellation đã hoàn tất.

Có hai trạng thái:

```text
Cancellation requested
```

và:

```text
Operation no longer accesses resource
```

Chỉ trạng thái thứ hai mới cho phép reclaim.

---

# 37. Stable address contract

Axiom nên có một semantic concept:

```text
StableAddress<T>
```

nhưng **không nhất thiết là một Core type**.

Các abstraction như:

```text
Box
Pool
PinnedBuffer
MappedMemory
DeviceBuffer
```

có thể establish stable address.

Compiler biết:

```text
storage cannot relocate
```

trong contract.

---

# 38. Relocatable storage

Ngược lại:

```text
Vec
String
Buffer
Arena implementation
```

có thể relocatable trừ khi API nói khác.

Compiler có thể:

```text
move
compact
reallocate
scalarize
```

nếu không phá capability.

---

# 39. Một nguyên tắc rất mạnh cho optimizer

> **Không có live capability phụ thuộc vào địa chỉ cũ → compiler được phép relocate storage.**

Ví dụ:

```axiom
var v = Vec(...)

{
    let p = view(v)
    use(p)
}

// p dead

v.push(...)
```

Sau scope:

```text
p dead
```

=> relocation được phép.

Không cần programmer viết lifetime.

Đây chính là điểm Axiom có thể đạt:

> borrow-checker-like safety mà không bắt programmer viết borrow/lifetime syntax.

---

# 40. Compiler lifetime analysis

Compiler nội bộ sẽ theo dõi:

```text
Owner
Capability
Region
LastUse
Escape
AddressObserved
RelocationConstraint
StorageClass
```

Ví dụ:

```text
v
│
├── view A
│   └── last use @ instruction 30
│
└── push @ instruction 40
```

Verifier thấy:

```text
view A dead before push
```

=> relocation hợp lệ.

Nếu:

```text
view A last use @ instruction 50
push @ instruction 40
```

=> relocation không hợp lệ.

Compiler có thể:

```text
reject
```

hoặc nếu API cho phép:

```text
materialize/copy
```

tùy semantics.

---

# 41. Đây không phải Borrow Checker 2.0

Điểm khác biệt về UX:

Rust:

```text
'a
'b
&'a T
&'b mut T
where ...
```

Axiom:

```axiom
let p = view(v)
```

và compiler tự suy luận.

Người dùng chỉ gặp lỗi khi semantic thực sự không hợp lệ.

Triết lý:

> **Lifetime là compiler fact, không phải programmer syntax.**

---

# 42. Runtime architecture

Từ đây runtime nên chia thành:

```text
axiom runtime
│
├── allocation
│   ├── general
│   ├── arena
│   ├── pool
│   └── virtual memory
│
├── synchronization
│   ├── atomic
│   ├── mutex
│   ├── semaphore
│   └── futex/park
│
├── execution
│   ├── thread
│   ├── fiber
│   └── scheduler
│
├── reclamation
│   ├── epoch
│   ├── hazard
│   └── RCU
│
└── OS
    ├── virtual memory
    ├── TLS
    ├── I/O
    └── handles
```

Không phải chương trình nào cũng link toàn bộ.

---

# 43. Runtime linking phải capability-driven

Ví dụ:

```axiom
fn main() {
    var x = 42
    print(x)
}
```

không nên tự động kéo:

```text
thread runtime
async runtime
GC
network
reflection
Arc runtime
scheduler
```

Binary chỉ link những component cần.

Đây là yếu tố quan trọng để đạt:

```text
small executable
```

---

# 44. Freestanding

Axiom phải cho phép:

```text
@freestanding
```

hoặc target profile tương đương.

Có thể:

```text
no heap
no thread
no OS
no runtime
no libc
```

nhưng vẫn:

```text
struct
enum
match
ownership
capability
atomic
comptime
```

nếu target hỗ trợ.

---

# 45. Memory allocator không thuộc compiler

Compiler chỉ cần biết semantic:

```text
ALLOC
DEALLOC
```

MIR:

```text
ALLOC<T>
...
DROP<T>
...
DEALLOC
```

Sau đó lowering:

```text
ALLOC
 ↓
runtime allocator
```

hoặc:

```text
stack allocation
```

hoặc:

```text
arena
```

hoặc:

```text
static
```

hoặc:

```text
eliminated
```

---

# 46. Allocation elimination

Ví dụ:

```axiom
fn f() -> i32 {
    var x = Box(10)
    return *x
}
```

Compiler có thể biến thành:

```text
return 10
```

không có:

```text
alloc
load
free
```

Đây là **abstraction erasure** đúng nghĩa.

---

# 47. Nhưng compiler không được thay đổi observable allocation

Nếu programmer dùng:

```text
custom allocator statistics
```

hoặc:

```text
allocation hook
```

thì allocation có thể trở thành observable.

Khi đó:

```text
eliminate allocation
```

chỉ được nếu semantics vẫn giữ observable behavior.

Vì vậy allocator instrumentation nên là explicit debug/system contract.

---

# 48. Debug allocator

Runtime nên có:

```text
DebugAllocator
TrackingAllocator
GuardAllocator
PoisonAllocator
```

cho:

- leak detection
- use-after-free diagnostics trong unsafe
- double free
- allocation tracing
- fragmentation analysis

Nhưng production không link chúng.

---

# 49. Sanitizer architecture

Không cần đưa sanitizer vào language semantics.

Có thể có:

```text
axiom test --asan
axiom test --msan
axiom test --tsan
```

hoặc Axiom-native equivalents sau này.

Compiler instrumentation:

```text
MIR
 ↓
instrumentation
 ↓
machine code
```

Không ảnh hưởng semantics của optimized production build.

---

# 50. Invariants BOOTSTRAP-022

Tôi đề xuất khóa:

```text id="8yhl3k"
AMEMORY-73 — Value lifetime is distinct from resource lifetime.
AMEMORY-74 — Resource lifetime is distinct from storage lifetime.
AMEMORY-75 — Capability lifetime is distinct from storage lifetime.
AMEMORY-76 — Drop does not imply physical deallocation.
AMEMORY-77 — Ownership does not determine storage placement.
AMEMORY-78 — Allocation is required only when observable storage semantics require it.
AMEMORY-79 — Escape analysis may eliminate dynamic allocation.
AMEMORY-80 — Scalar replacement may eliminate object storage.
AMEMORY-81 — Observable address constrains relocation.
AMEMORY-82 — Relocatable storage may move when no live capability depends on its address.
AMEMORY-83 — Stable address requires an explicit storage contract.
AMEMORY-84 — Vec relocation is permitted unless prevented by a valid storage contract.
AMEMORY-85 — Reserve does not establish stable address.
AMEMORY-86 — Box represents owned dynamic-storage semantics.
AMEMORY-87 — Box does not inherently require a physical heap allocation.
AMEMORY-88 — Arena bounds the lifetime of arena-owned storage.
AMEMORY-89 — Arena reclamation does not require tracing GC.
AMEMORY-90 — Pool storage permits slot reuse after valid release.
AMEMORY-91 — Slab storage is a fixed-size pool strategy.
AMEMORY-92 — Allocator strategy is not part of ordinary value semantics.
AMEMORY-93 — Allocator parameters are not mandatory for ordinary collections.
AMEMORY-94 — Custom allocation is an explicit storage/system abstraction.
AMEMORY-95 — Allocation failure is distinct from resource cleanup.
AMEMORY-96 — Drop is non-fallible.
AMEMORY-97 — Resource cleanup does not require physical memory deallocation.
AMEMORY-98 — Lock-free reclamation is a runtime/library concern.
AMEMORY-99 — Hazard-pointer metadata is not a language lifetime annotation.
AMEMORY-100 — Epoch reclamation metadata is not a language lifetime annotation.
AMEMORY-101 — RCU semantics are library/runtime abstractions.
AMEMORY-102 — Logical handles are distinct from storage addresses.
AMEMORY-103 — Generation handles may detect stale logical references.
AMEMORY-104 — Reference counting is explicit library semantics.
AMEMORY-105 — Implicit reference counting is not part of Core.
AMEMORY-106 — Compiler may optimize explicit ownership operations when observable semantics are preserved.
AMEMORY-107 — Async cancellation cannot reclaim storage before external access has ended.
AMEMORY-108 — In-flight I/O establishes a storage lifetime requirement.
AMEMORY-109 — Runtime allocation components are independently linkable.
AMEMORY-110 — Freestanding programs need not provide a heap.
AMEMORY-111 — Compiler MIR represents allocation semantically before choosing physical storage.
AMEMORY-112 — Physical allocation strategy is a lowering/runtime concern.
AMEMORY-113 — Allocation elimination must preserve observable allocator behavior.
AMEMORY-114 — Debug allocation instrumentation is not part of Core semantics.
AMEMORY-115 — Sanitizer instrumentation does not redefine production memory semantics.
```

---

# 51. Kiến trúc sau BOOTSTRAP-022

Hiện tại Axiom đã có một chuỗi rất đáng chú ý:

```text
                 AXIOM MEMORY

       ┌───────────────────────────────┐
       │       Value Semantics         │
       └──────────────┬────────────────┘
                      ↓
                 Ownership
                      ↓
                 Capability
                      ↓
              Lifetime Analysis
                      ↓
       ┌──────────────┴──────────────┐
       ↓                             ↓
   Storage Identity             Resource Life
       ↓                             ↓
   Allocator                   Drop / Close
       ↓
 ┌─────┼──────┬────────┐
 ↓     ↓      ↓        ↓
Stack Heap  Arena    Pool/Slab
              │
              ↓
         Reclamation
              │
      ┌───────┼────────┐
      ↓       ↓        ↓
    Epoch   Hazard     RCU
```

Điểm quan trọng nhất là **không có một "memory management mechanism" duy nhất**.

Axiom không phải:

```text
C++  → manually free everything
Rust → borrow checker everything
Java → GC everything
```

mà là:

```text
Axiom
 ├── Ownership       → ai chịu trách nhiệm
 ├── Capability      → ai được truy cập
 ├── Lifetime        → khi nào còn hợp lệ
 ├── Storage         → đặt ở đâu
 ├── Allocator       → cấp phát thế nào
 └── Reclamation     → thu hồi thế nào
```

Compiler tự động xử lý phần khó; programmer chỉ phải **chọn abstraction khi storage/reclamation thực sự là một phần của bài toán**.

---

## Và đây là điểm rất quan trọng cho mục tiêu "nhanh hơn C/C++"

Không nên cố đạt performance bằng cách ép programmer viết code low-level.

Axiom nên đạt performance bằng:

```text
High-level source
       ↓
strong semantic facts
       ↓
aggressive lifetime analysis
       ↓
escape analysis
       ↓
alias/capability analysis
       ↓
allocation elimination
       ↓
scalar replacement
       ↓
inlining
       ↓
vectorization
       ↓
register allocation
       ↓
native code
```

Trong trường hợp tốt, source có thể trông như:

```axiom
fn sum(values: view<i32>) -> i64 {
    var total: i64 = 0

    for x in values {
        total += x as i64
    }

    return total
}
```

nhưng machine code cuối cùng hoàn toàn có thể là một loop SIMD/vectorized gần với code C tối ưu bằng tay.

**Không cần programmer nhìn thấy pointer, lifetime hay allocator để compiler làm việc đó.**

### Bước tiếp theo

Sau allocation/reclamation, phần còn thiếu để hoàn thiện "memory side" của Axiom là:

**BOOTSTRAP-023 — Object Model + Layout + ABI + Representation Contracts**

Ở đó ta sẽ khóa một vấn đề rất quan trọng khác: **khi nào Axiom được phép thay đổi layout/reorder field/niche-optimize/pack enum, khi nào địa chỉ/offset/bit pattern trở thành observable, và làm thế nào để FFI/C ABI vẫn chính xác mà default Axiom ABI không phải mang gánh nặng của C.**