# AXIOM LANGUAGE SPECIFICATION v0.1 — Part VII
## Atomic Memory Model · Ordering · Fences · Lock-Free Semantics

Phần này là một trong những phần quan trọng nhất của Axiom, vì memory model quyết định compiler được phép tối ưu đến đâu.

Mục tiêu của Axiom:

> **Safe code có memory semantics xác định; compiler vẫn được tự do tối ưu aggressively trong phạm vi memory model.**

Axiom không cố biến concurrency thành một mô hình "sequentially consistent mọi nơi". Làm vậy sẽ gây chi phí không cần thiết.

---

# 1. Hai loại memory access

Axiom phân biệt rõ:

```text
Ordinary Memory
Atomic Memory
```

Ordinary:

```axiom
x = x + 1
```

Atomic:

```axiom
counter.fetch_add(1, Relaxed)
```

Hai loại này không được trộn lẫn tùy tiện.

---

# 2. Atomic là property của storage

Nếu:

```axiom
var counter: Atomic<u64>
```

thì:

```text
counter
```

là atomic storage.

Không phải:

```text
ordinary u64
+
atomic operations
```

theo nghĩa programmer có thể chuyển đổi tùy ý giữa hai mode.

---

# 3. Không tạo `mut_view<Atomic<T>>`

Đây là invariant quan trọng:

```text
Atomic<T>
    ✗
mut_view<T>
```

Không được phép dùng:

```axiom
let p = mut_view(counter)
```

để bypass atomic semantics.

Thay vào đó:

```axiom
counter.store(...)
counter.load(...)
counter.fetch_add(...)
```

---

# 4. Tại sao?

Nếu cho phép:

```text
atomic storage
    ↓
ordinary mutable access
```

thì compiler không còn biết access nào phải obey atomic ordering.

Điều này phá:

```text
happens-before
visibility
race detection
optimization
```

---

# 5. Atomic load

Conceptually:

```axiom
let x = counter.load(Acquire)
```

Kết quả là một ordinary value:

```text
u64
```

sau khi operation hoàn thành.

Value `x` không tự trở thành atomic.

---

# 6. Atomic store

```axiom
counter.store(42, Release)
```

ghi một giá trị atomically.

`Release` cũng tạo ordering semantics cho các ordinary operations trước đó.

---

# 7. Relaxed

```axiom
counter.load(Relaxed)
counter.store(42, Relaxed)
```

Relaxed bảo đảm atomicity và modification-order semantics của atomic object nhưng không tạo synchronization với ordinary memory.

Nó phù hợp với các counter/statistics khi chỉ cần atomic update.

Ví dụ:

```axiom
requests.fetch_add(1, Relaxed)
```

---

# 8. Acquire

Acquire thường dùng khi một thread đọc một atomic publication signal.

Ví dụ:

```axiom
// producer
data.value = 42
ready.store(true, Release)
```

và:

```axiom
// consumer
if ready.load(Acquire) {
    use(data)
}
```

Khi consumer observes store tương ứng theo memory model, các writes trước Release được ordered trước các reads sau Acquire.

---

# 9. Release

Release là publication boundary.

Conceptually:

```text
ordinary writes
      ↓
Release
      ↓
atomic publication
```

Nó thường được dùng để publish initialized data.

---

# 10. Acquire + Release

Ví dụ lock-free queue có thể cần:

```text
producer:
    write data
    Release

consumer:
    Acquire
    read data
```

Axiom không tự động nâng Relaxed lên Acquire/Release.

Programmer/library abstraction phải chọn ordering đúng.

---

# 11. AcqRel

Dùng cho read-modify-write operation vừa consume synchronization vừa publish synchronization.

Ví dụ:

```axiom
state.compare_exchange(
    expected,
    desired,
    AcqRel,
    Acquire
)
```

---

# 12. SeqCst

`SeqCst` cung cấp ordering mạnh nhất trong atomic model.

Ví dụ:

```axiom
flag.store(true, SeqCst)
```

Compiler/backend không được biến nó thành:

```text
Acquire
Release
Relaxed
```

nếu làm thay đổi observable atomic semantics.

---

# 13. Atomic modification order

Mỗi atomic object có một modification order phù hợp với atomic memory model.

Ví dụ:

```text
counter:
    store(1)
    store(2)
    fetch_add(1)
    store(10)
```

Các atomic modifications của object phải có một order nhất quán theo semantics.

---

# 14. Không có "partial atomic write"

Nếu:

```axiom
Atomic<u64>
```

thì operation atomic theo contract của type/target.

Không thể xảy ra semantic model kiểu:

```text
upper 32 bits mới
lower 32 bits cũ
```

do một atomic store bị chia nhỏ.

Nếu target không hỗ trợ native operation, compiler/library phải dùng implementation phù hợp.

---

# 15. Atomicity không đồng nghĩa lock-free

Đây là distinction bắt buộc:

```text
atomic
≠
lock-free
≠
wait-free
```

---

# 16. Lock-free

Một atomic operation/algorithm là lock-free nếu hệ thống đảm bảo progress property tương ứng: trong số các operations đang cạnh tranh, ít nhất một operation có thể tiến triển trong hữu hạn bước theo contract.

Axiom không giả định mọi `Atomic<T>` đều lock-free.

---

# 17. Wait-free

Wait-free mạnh hơn:

> Mỗi operation hoàn thành trong một số bước hữu hạn bị chặn độc lập với contention.

Đây là property của algorithm/API, không phải mặc định của `Atomic<T>`.

---

# 18. Query capability

Library có thể cung cấp:

```axiom
Atomic.is_lock_free<u64>()
```

hoặc compile-time capability tương đương.

Không nên hard-code:

```text
u64 == always lock-free
```

vì target có thể khác nhau.

---

# 19. Compare-and-exchange

Axiom hỗ trợ:

```axiom
compare_exchange
compare_exchange_weak
```

Conceptual semantics:

```text
if current == expected:
    current = desired
    success
else:
    expected = current
    failure
```

Tất cả diễn ra atomically.

---

# 20. Strong CAS

```axiom
compare_exchange(...)
```

không được tự ý báo failure nếu giá trị vẫn bằng expected chỉ vì spurious failure.

---

# 21. Weak CAS

```axiom
compare_exchange_weak(...)
```

có thể có spurious failure.

Vì vậy thường dùng trong loop:

```axiom
var expected = old

while !atomic.compare_exchange_weak(
    expected,
    new_value,
    AcqRel,
    Acquire
) {
}
```

---

# 22. Failure ordering

CAS có hai ordering:

```text
success_order
failure_order
```

Failure không thực hiện store thành công.

Do đó compiler phải kiểm tra failure ordering hợp lệ.

---

# 23. Atomic RMW

Các operation:

```text
fetch_add
fetch_sub
fetch_and
fetch_or
fetch_xor
swap
```

là read-modify-write operations.

Chúng có một atomic modification duy nhất về mặt semantics.

---

# 24. Fetch-add và overflow

Atomic arithmetic vẫn obey arithmetic semantics của Axiom.

Ví dụ:

```axiom
counter.fetch_add(1, Relaxed)
```

Nếu operation vượt range của type, semantics phải rõ ràng.

Để tránh một memory model riêng cho atomic arithmetic, Axiom nên dùng:

```text
atomic operation
+
explicit arithmetic mode
```

thay vì tạo một overflow model khác.

---

# 25. Đề xuất freeze

Với integer atomics, v0.1 nên quy định:

> Atomic RMW sử dụng **wrapping two's-complement arithmetic** theo bit-width của atomic type.

Ví dụ:

```text
u8 255 + 1 → 0
```

Điều này đặc biệt phù hợp với hardware atomic instructions và tránh panic bên trong primitive atomic operation.

Nếu cần checked arithmetic, programmer dùng explicit checked logic.

---

# 26. Fences

Axiom hỗ trợ:

```axiom
fence(Acquire)
fence(Release)
fence(AcqRel)
fence(SeqCst)
```

Fences là memory-ordering primitives.

---

# 27. Fence không phải volatile

```text
fence
```

không đọc/ghi memory.

Nó chỉ tạo ordering constraint.

---

# 28. Fence không phải compiler barrier đơn giản

Một compiler barrier chỉ nói:

```text
"đừng reorder ở compiler"
```

Trong khi atomic fence có semantic effect đối với execution của các threads.

Axiom phải phân biệt hai abstraction.

---

# 29. Compiler barrier

Nếu system programming cần compiler-only barrier:

```text
compiler_fence()
```

có thể tồn tại trong `unsafe/system`.

Nó không phải atomic synchronization.

---

# 30. Volatile

Volatile access dùng cho memory mà mỗi access có thể có external observable effect.

Ví dụ:

```text
MMIO register
device memory
hardware status register
```

Conceptually:

```axiom
volatile_load(addr)
volatile_store(addr, value)
```

---

# 31. Volatile không synchronize threads

Đây là invariant:

```text
volatile
≠
atomic
```

Một volatile store không tự tạo happens-before với thread khác.

---

# 32. MMIO

Axiom system layer có thể cung cấp:

```axiom
let status = volatile_load(reg)
volatile_store(reg, command)
```

Address này có thể thuộc:

```text
EXTERNAL
DEVICE
```

storage domain đã định nghĩa trong memory model.

---

# 33. Ordinary memory model

Với safe ordinary memory:

```text
read
write
move
drop
```

phải obey ownership/capability rules.

Compiler được phép tối ưu:

```text
load elimination
store elimination
load forwarding
scalar replacement
dead-store elimination
reordering
vectorization
```

nếu không thay đổi observable semantics.

---

# 34. Atomic memory là optimization boundary

Compiler không được áp dụng optimization ordinary-memory lên atomic operations nếu làm thay đổi:

```text
atomicity
ordering
modification order
synchronization
```

Ví dụ không được biến:

```axiom
a.load(Acquire)
a.load(Acquire)
```

thành một load duy nhất nếu semantics observable của hai atomic accesses bị thay đổi.

---

# 35. Nhưng compiler vẫn được optimize

Nếu compiler chứng minh:

```text
second atomic load
```

không observable theo semantic context, có thể eliminate.

Điều kiện là optimization phải preserve complete memory model semantics.

---

# 36. Happens-before

Axiom cần một quan hệ semantic:

```text
A happens-before B
```

Các nguồn có thể bao gồm:

```text
sequenced-before
synchronizes-with
thread join
channel communication
lock synchronization
atomic ordering
task/executor synchronization
GPU events
```

tùy domain.

---

# 37. Sequenced-before

Trong một execution context:

```axiom
x = 1
y = 2
```

có thứ tự semantic được xác định bởi Axiom evaluation rules.

Compiler có thể reorder machine instructions nếu không thay đổi observable result.

---

# 38. Synchronizes-with

Ví dụ:

```text
Thread A:
    data = 42
    flag.store(true, Release)

Thread B:
    flag.load(Acquire)
    read(data)
```

khi Acquire observes phù hợp với Release:

```text
A's prior writes
      ↓
happens-before
      ↓
B's subsequent reads
```

---

# 39. Data race và atomic

Atomic operations không tạo data race với atomic operations khác trên cùng atomic object.

Ví dụ:

```text
Thread A → counter.fetch_add()
Thread B → counter.fetch_add()
```

hợp lệ.

Nhưng:

```text
Thread A → counter atomic write
Thread B → same storage ordinary write
```

không hợp lệ.

---

# 40. Atomic object identity

Atomic semantics gắn với **storage identity**, không chỉ type.

Hai biến:

```axiom
a: Atomic<u64>
b: Atomic<u64>
```

là hai atomic objects khác nhau.

Không có synchronization giữa chúng chỉ vì cùng type.

---

# 41. False sharing

Axiom không tự động coi:

```text
struct Counters {
    a: Atomic<u64>
    b: Atomic<u64>
}
```

là độc lập về performance.

Hai atomics có thể nằm cùng cache line.

Đây không phải correctness violation, nhưng có thể gây contention.

---

# 42. Alignment

System layer có thể sử dụng:

```axiom
@align(64)
struct Counter {
    value: Atomic<u64>
}
```

để tránh false sharing trên target có cache line phù hợp.

Nhưng:

> `64` không phải universal cache-line size.

Do đó standard library nên cung cấp target-aware constants khi cần.

---

# 43. `@cache_align`

Có thể thêm sau:

```axiom
@cache_align
```

thay vì bắt programmer hard-code:

```text
@align(64)
```

Nhưng đây là system/library feature, chưa cần đưa vào Core v0.1.

---

# 44. Atomic pointer

Axiom có thể hỗ trợ:

```axiom
Atomic<*mut T>
```

trong unsafe/system contexts.

Nhưng atomic pointer chỉ đảm bảo:

```text
atomic address manipulation
```

không đảm bảo:

```text
pointed object lifetime
validity
ownership
```

---

# 45. Đây là điểm cực kỳ quan trọng

Ví dụ:

```text
atomic_ptr.store(ptr, Release)
```

không có nghĩa:

```text
ptr object is alive forever
```

Ownership vẫn nằm trong memory model.

---

# 46. Safe wrapper

Lock-free structure nên được đóng gói:

```text
Raw pointer
    ↓
unsafe implementation
    ↓
ownership/reclamation proof
    ↓
safe API
```

Programmer sử dụng safe abstraction không phải tự xử lý raw pointer.

---

# 47. ABA

Ví dụ conceptual:

```text
A → B
B removed
C allocated at same address
A → C
```

CAS chỉ nhìn address có thể thấy:

```text
A → A
```

dù object đã bị thay thế.

Đó là ABA.

---

# 48. Axiom không "giải quyết" ABA trong Atomic

Atomic primitive không thể biết:

```text
same address
```

có phải:

```text
same logical object
```

hay không.

Đây chính là lý do Axiom đã phân biệt:

```text
Value Identity
Storage Identity
Logical Identity
```

---

# 49. Generation handles

Một solution library-level:

```text
Handle {
    index
    generation
}
```

Object destruction:

```text
generation += 1
```

Handle cũ trở thành stale.

Đây là logical identity, không phải raw pointer.

---

# 50. Memory reclamation

Lock-free pointer structures cần một abstraction như:

```text
Epoch
HazardPointer
AtomicShared
RCU
```

tùy use case.

Không đưa tất cả vào Core.

---

# 51. Why không implicit ARC?

Nếu Axiom tự động:

```text
Atomic pointer
→ hidden reference count
```

thì mọi pointer operation có thể phát sinh:

```text
atomic increment
atomic decrement
cache contention
```

Đi ngược mục tiêu performance.

Do đó:

> **Reference counting chỉ xuất hiện khi programmer chọn abstraction có RC semantics.**

---

# 52. `Arc`

`Arc<T>` là library abstraction.

Conceptually:

```text
strong_count
weak_count
data
```

nhưng layout không phải language guarantee.

---

# 53. Arc và Atomic

Arc thường dùng atomic reference count nội bộ.

Nhưng:

```text
Arc<T>
```

không có nghĩa mọi access đến `T` là atomic.

Ví dụ:

```text
Arc<Config>
```

có thể share immutable data.

---

# 54. Arc mutable

```text
Arc<MutableState>
```

không tự cho phép:

```text
concurrent mutation
```

Phải có synchronization abstraction.

---

# 55. Memory reclamation và Drop

Nếu object đang được atomic structure sử dụng:

```text
logical removal
```

không đồng nghĩa:

```text
physical deallocation
```

Đây phù hợp với invariant:

### AMEM-43
Resource lifetime is distinct from memory lifetime.

---

# 56. Compiler freedom

Axiom memory model cho phép compiler thực hiện:

```text
register promotion
load/store forwarding
instruction scheduling
vectorization
inlining
loop transformation
dead code elimination
```

nhưng phải giữ:

```text
atomic semantics
volatile semantics
synchronization
observable side effects
```

---

# 57. Không dùng "undefined behavior" làm optimization escape hatch

Đây là một lựa chọn thiết kế đáng giá.

Trong safe code, các lỗi như:

```text
use-after-free
out-of-bounds
data race
double drop
invalid capability
```

không được biến thành:

```text
"compiler có thể làm bất kỳ điều gì"
```

Compiler phải reject statically hoặc tạo behavior đã được định nghĩa như:

```text
panic
trap
```

---

# 58. Unsafe vẫn có machine-level freedom

Trong:

```axiom
unsafe {
    ...
}
```

programmer có thể tạo assumptions compiler không thể chứng minh.

Nhưng unsafe không có nghĩa:

```text
mọi behavior đều hợp lệ
```

Nó có nghĩa:

> Programmer assumes responsibility for invariants outside safe verifier.

---

# 59. Unsafe atomic code

Ví dụ lock-free algorithm:

```axiom
unsafe fn pop(queue: *mut Queue) -> Option<Node> {
    ...
}
```

Compiler vẫn phải preserve atomic instructions.

Unsafe không cho phép compiler biến:

```text
Acquire
```

thành:

```text
Relaxed
```

---

# 60. Atomic và FFI

Foreign function:

```axiom
extern "C" fn external(...)
```

có thể đọc/write memory.

Compiler không biết foreign implementation có synchronization semantics gì.

Do đó FFI boundary mặc định:

```text
conservative
```

---

# 61. FFI atomic contract

Nếu C API cung cấp atomic synchronization:

```text
```

Axiom wrapper phải khai báo semantics phù hợp.

Không được giả định:

```text
extern fn foo()
```

tự động tạo happens-before.

---

# 62. Volatile FFI

MMIO/hardware APIs có thể được wrapper bằng:

```text
volatile_load
volatile_store
```

thay vì ordinary load/store.

---

# 63. GPU

Atomic model này có thể mở rộng sang GPU.

GPU có thể thêm:

```text
scope
```

ví dụ:

```text
Workgroup
Device
System
```

nhưng không thay đổi semantic concept:

```text
ordering
atomicity
visibility
```

---

# 64. GPU atomic

Conceptually:

```axiom
atomic_add(
    counter,
    1,
    Relaxed,
    Workgroup
)
```

`scope` là một dimension bổ sung.

Không cần tạo một memory model hoàn toàn mới cho GPU.

---

# 65. Freeze memory model

Tại v0.1, Axiom nên khóa:

```text
Atomic<T>
Relaxed
Acquire
Release
AcqRel
SeqCst
CAS
Weak CAS
Fences
Volatile
Happens-before
Synchronization
```

và để:

```text
lock-free algorithms
memory reclamation
RCU
hazard pointers
epoch GC
```

ở library/system layer.

---

# 66. Normative invariants

### AATOM-20
Atomicity is a property of atomic storage.

### AATOM-21
Atomic storage cannot be accessed through ordinary mutable capability.

### AATOM-22
Relaxed operations provide atomic modification semantics without general synchronization ordering.

### AATOM-23
Acquire establishes the required acquire ordering.

### AATOM-24
Release establishes the required release ordering.

### AATOM-25
AcqRel combines acquire and release semantics.

### AATOM-26
SeqCst provides the strongest standard atomic ordering.

### AATOM-27
Atomic ordering cannot be weakened by optimization.

### AATOM-28
Volatile is distinct from atomic synchronization.

### AATOM-29
Atomic does not imply lock-free.

### AATOM-30
Atomic does not imply wait-free.

### AATOM-31
Atomic pointer operations do not establish object lifetime.

### AATOM-32
Atomic operations do not solve ABA.

### AATOM-33
Memory reclamation is distinct from atomic synchronization.

### AATOM-34
Safe ordinary memory cannot participate in a data race.

### AATOM-35
Synchronization establishes happens-before according to its contract.

### AATOM-36
Unsafe does not disable atomic semantic preservation.

### AATOM-37
FFI synchronization semantics require an explicit contract.

### AATOM-38
GPU atomic scope extends the memory model without replacing its ordering semantics.

### AATOM-39
Atomic RMW integer arithmetic has defined wrapping semantics in v0.1.

### AATOM-40
Compiler optimization must preserve the complete atomic memory model.

---

# 67. Một quyết định kiến trúc rất quan trọng

Đến đây Axiom có một đặc điểm khá khác biệt:

```text
C/C++
    Undefined behavior
       ↓
    optimizer freedom

Axiom
    Safe semantic guarantees
       ↓
    optimizer freedom inside those guarantees
```

Tức là Axiom không cần "hy sinh" safety để đạt performance.

Compiler vẫn có thể generate:

```text
same native instructions
```

khi semantics tương đương.

---

# 68. Quan trọng hơn: không cần một GC để đạt điều này

Memory safety của Axiom hiện tại đến từ:

```text
Ownership
+
Capability
+
Drop
+
Region analysis
+
Concurrency properties
+
Atomic model
+
Unsafe boundary
```

chứ không phải:

```text
GC
```

hay:

```text
mandatory runtime
```

Đây chính xác là hướng phù hợp với mục tiêu ban đầu của Axiom.

---

# 69. Chuỗi semantic hoàn chỉnh hiện tại

Ta đã có thể nhìn Axiom như sau:

```text
VALUE
  │
  ├── Copy
  ├── Move
  └── Clone
       │
       ▼
OWNERSHIP
       │
       ├── Drop
       └── Storage
             │
             ├── Stack
             ├── Register
             ├── Inline
             ├── Heap
             ├── Arena
             ├── Pool
             └── Device
       │
       ▼
CAPABILITY
       │
       ├── view
       └── mut_view
       │
       ▼
EXECUTION
       │
       ├── synchronous
       ├── thread
       ├── async task
       └── GPU
       │
       ▼
SYNCHRONIZATION
       │
       ├── Channel
       ├── Mutex/RwLock
       └── Atomic
       │
       ▼
MEMORY ORDER
       │
       ├── Relaxed
       ├── Acquire
       ├── Release
       ├── AcqRel
       └── SeqCst
```

Đây là một hệ thống khá thống nhất.

---

# AXIOM LANGUAGE SPECIFICATION v0.1 — Part VIII

Phần kế tiếp nên đi vào một chủ đề còn nền tảng hơn nữa:

## **Type System hoàn chỉnh + Layout + Representation + ABI**

Cụ thể sẽ khóa:

```text
Primitive types
Struct
Tuple
Enum
Option
Result
Array
Slice/View
Unsized types
Generic types
Associated types
Trait objects
dyn Trait
impl Trait
Function types
Closure types
Never
Unit
ZST
Recursive types
Newtype
Type alias
Type identity
Type inference
Numeric literals
Coercion
Conversion
Layout
Alignment
Padding
Niche optimization
Discriminant
ABI
Calling convention
Return-value ABI
Aggregate passing
Generic ABI
```

Đây là bước cần làm **trước khi đi sâu vào compiler backend**, vì nếu type/layout semantics chưa khóa thì MIR, ABI và native code generator rất dễ phải sửa lại sau này.