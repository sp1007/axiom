# BOOTSTRAP-363 — Axiom Memory Model, Atomic Semantics & Data-Race Verification Engine

Đây là bước tiếp theo sau **BOOTSTRAP-362**. 362 đã định nghĩa các primitive đồng bộ ở mức ngôn ngữ/thư viện; 363 phải đóng băng **memory model ở cấp compiler**, tức là xác định chính xác compiler được phép reorder gì, khi nào hai thread được coi là có quan hệ nhìn thấy dữ liệu, và compiler chứng minh chương trình safe không có data race như thế nào.

Điểm quan trọng: **đây không phải thiết kế thêm Mutex/Channel**. Đây là semantic foundation mà toàn bộ Thread/Async/GPU/Atomic/Optimizer sau này phải dựa vào.

---

# 1. Mục tiêu

Axiom cần một memory model có 5 đặc tính:

1. **Đủ mạnh cho CPU hiện đại**
2. **Compiler được phép tối ưu aggressive**
3. **Không có data race trong safe code**
4. **Không buộc programmer viết memory barrier thủ công**
5. **Không biến memory model thành một hệ thống quá phức tạp đối với programmer**

Nguyên tắc:

> Programmer mô tả ownership và synchronization; compiler chịu trách nhiệm bảo đảm ordering và visibility.

Ví dụ:

```axiom
let data = Box(Data(...))
let ready = Atomic(false)

spawn {
    data.value = 42
    ready.store(true, Release)
}

while !ready.load(Acquire) {}

print(data.value)
```

Quan hệ semantic phải là:

```text
write data.value
      │
      │ sequenced-before
      ▼
store ready = true (Release)
      │
      │ synchronizes-with
      ▼
load ready (Acquire)
      │
      │ happens-before
      ▼
read data.value
```

Compiler **không được** reorder read `data.value` lên trước Acquire theo cách phá vỡ semantics.

---

# 2. Ba khái niệm phải tách biệt

Axiom không được gom tất cả thành “memory ordering”.

## 2.1 Atomicity

Một operation có được thực hiện nguyên tử hay không.

```text
atomic load
atomic store
atomic RMW
atomic CAS
```

Atomicity không nói rằng các memory access khác đã được publish.

---

## 2.2 Ordering

Ordering xác định quan hệ giữa các memory operations.

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

Ví dụ:

```axiom
flag.store(true, Release)
```

không chỉ đơn thuần là atomic store.

Nó tạo một ordering boundary.

---

## 2.3 Visibility / Synchronization

Một thread có được phép dựa vào một write từ thread khác hay không.

Đây là nơi:

```text
synchronizes-with
happens-before
```

được hình thành.

Ba khái niệm phải độc lập trong compiler.

---

# 3. Memory Event Model

Mỗi memory operation semantic được biểu diễn thành một **MemoryEvent**.

Ví dụ:

```text
write x
read x
atomic_load flag
atomic_store flag
atomic_cas flag
lock mutex
unlock mutex
channel_send
channel_receive
thread_start
thread_join
await_task
```

Compiler tạo:

```text
MemoryEvent {
    EventId
    ThreadDomain
    StorageId
    Region
    AccessKind
    Atomicity
    MemoryOrder
    Location
    SourceSpan
}
```

`StorageId` không nhất thiết là physical address.

Nó biểu diễn semantic storage object.

---

# 4. Memory Access Kind

Axiom có các loại:

```text
READ
WRITE
READ_WRITE
MOVE
DROP
ATOMIC_READ
ATOMIC_WRITE
ATOMIC_RMW
VOLATILE_READ
VOLATILE_WRITE
```

Trong đó:

```text
READ/WRITE
```

là ordinary memory.

```text
ATOMIC_*
```

là atomic memory.

```text
VOLATILE_*
```

là observable machine memory.

Không được coi:

```text
volatile == atomic
```

hoặc:

```text
atomic == volatile
```

---

# 5. Sequenced-Before

Trong một execution context, các operations có quan hệ:

```text
A sequenced-before B
```

Ví dụ:

```axiom
x = 1
y = 2
```

semantic order:

```text
write x
    ↓
write y
```

Compiler vẫn có thể reorder machine instructions nếu observable behavior không thay đổi.

Do đó:

> Sequenced-before là semantic relation, không phải machine-instruction order.

Đây là điểm cực kỳ quan trọng cho optimizer.

---

# 6. Synchronizes-With

Các primitive đã định nghĩa ở BOOTSTRAP-362 tạo synchronization edge.

Ví dụ:

### Release → Acquire

```text
store Release
        │
        ▼
load Acquire
```

nếu load quan sát giá trị tương ứng theo atomic modification order.

---

### Mutex

```text
unlock(m)
    │
    ▼
lock(m)
```

---

### Channel

```text
send(v)
    │
    ▼
receive()
```

---

### Thread

```text
thread_start
```

và:

```text
thread_completion → join
```

---

### Task

```text
task_completion → await
```

---

# 7. Happens-Before

Định nghĩa:

```text
happens-before
=
sequenced-before
+
synchronizes-with
+
transitive closure
```

Ví dụ:

```text
A SB B
B SW C
C SB D
```

suy ra:

```text
A HB D
```

Compiler phải lưu được proof này.

---

# 8. Data Race

Hai conflicting ordinary accesses:

```text
A = READ/WRITE
B = READ/WRITE
```

trên cùng một memory region,

và:

```text
at least one is WRITE
```

mà:

```text
A happens-before B
```

không tồn tại,

thì đó là race nếu hai operations có thể xảy ra concurrently.

Ví dụ:

```axiom
var x = 0

spawn {
    x = 1
}

spawn {
    x = 2
}
```

Safe compiler phải reject.

Không được biến thành:

```text
warning
```

hay:

```text
undefined behavior
```

trong safe code.

---

# 9. Read/Read không phải data race

```axiom
spawn {
    print(x)
}

spawn {
    print(x)
}
```

nếu `x` immutable/shared-read thì hợp lệ.

Compiler chỉ cần chứng minh:

```text
READ + READ
```

không conflict.

---

# 10. Ownership là lớp bảo vệ đầu tiên

Memory model không phải lớp duy nhất.

Axiom nên có hierarchy:

```text
Ownership
    ↓
Capability
    ↓
Synchronization
    ↓
Memory Model
    ↓
Hardware Memory Model
```

Ví dụ nếu compiler đã chứng minh:

```text
Thread A owns x
Thread B owns y
```

thì không cần xây dựng synchronization graph giữa chúng.

Đây là một tối ưu rất quan trọng.

---

# 11. Send / Share được compiler sử dụng

Khi:

```axiom
spawn(worker(data))
```

compiler phải kiểm tra:

```text
data : Send
```

nếu ownership được chuyển sang thread.

Nếu shared:

```text
Arc<T>
```

thì:

```text
T : Share
```

phải được chứng minh.

Không được hiểu:

```text
Arc<T>
```

là tự động thread-safe.

---

# 12. Race Verification Levels

Compiler không nên chỉ có:

```text
safe / unsafe
```

Mà internal verifier có các trạng thái:

```text
PROVEN_SAFE
PROVEN_DISJOINT
PROVEN_SYNCHRONIZED
PROVEN_SINGLE_THREAD
PROVEN_IMMUTABLE
UNKNOWN
CONFLICT
```

Ví dụ:

```axiom
fn update(a: mut_view<Data>) {
    a.x += 1
}
```

Compiler có thể chứng minh:

```text
exclusive capability
```

→ không cần runtime synchronization.

---

# 13. Region-aware race checking

Race checker không chỉ so sánh variable name.

Ví dụ:

```axiom
struct Data {
    x: i32
    y: i32
}
```

Nếu:

```text
thread A → mut_view(data.x)
thread B → mut_view(data.y)
```

thì:

```text
Region(data.x)
∩
Region(data.y)
=
∅
```

→ không race.

Nhưng:

```text
mut_view(data)
mut_view(data)
```

→ conflict.

Đây là lý do region/capability model của 282 cực kỳ quan trọng.

---

# 14. Unknown overlap

Nếu compiler không chứng minh được:

```text
DISJOINT
```

thì không được tự giả định.

Ví dụ:

```text
region A = UNKNOWN
region B = UNKNOWN
```

thì:

```text
possible conflict
```

→ reject trong safe code.

Không được biến:

```text
UNKNOWN
```

thành:

```text
probably safe
```

---

# 15. Unsafe không xóa MemoryDB

Đây là invariant quan trọng.

```axiom
unsafe {
    ...
}
```

không có nghĩa:

```text
disable race checker
```

Thay vào đó unsafe có thể **establish assumption**.

Ví dụ conceptual:

```text
unsafe establish:
    region A is disjoint from region B
```

Sau đó verifier sử dụng:

```text
TrustedMemoryFact
```

nhưng phải biết nguồn gốc:

```text
FactOrigin = UNSAFE
```

để debugger/audit/tooling truy vết.

---

# 16. Atomic Modification Order

Mỗi atomic object có:

```text
ModificationOrder
```

Ví dụ:

```text
flag.store(false)
flag.store(true)
flag.store(false)
```

các writes có thứ tự modification order riêng.

Compiler không được reorder atomic modifications theo cách làm thay đổi observable atomic semantics.

---

# 17. Relaxed

```axiom
counter.fetch_add(1, Relaxed)
```

cung cấp:

```text
atomicity
+
modification order
```

nhưng không tự tạo:

```text
publication ordering
```

Do đó:

```text
Relaxed
```

không đủ để publish arbitrary data.

---

# 18. Release / Acquire

Release:

```text
previous operations
        ↓
Release
```

Acquire:

```text
Acquire
        ↓
subsequent operations
```

Khi synchronization thành công:

```text
before Release
       HB
after Acquire
```

Đây là một trong những quan hệ mà optimizer phải bảo toàn.

---

# 19. AcqRel

RMW:

```axiom
x.fetch_add(1, AcqRel)
```

có cả:

```text
Acquire
+
Release
```

semantic effect.

Compiler không được tách nó thành hai ordinary operations.

---

# 20. SeqCst

`SeqCst` cung cấp:

```text
Acquire/Release semantics
+
single global sequentially-consistent order
```

cho SeqCst atomic operations/fences theo memory model của Axiom.

Compiler có thể optimize SeqCst chỉ khi chứng minh observable SC behavior vẫn giữ nguyên.

---

# 21. Fences

Axiom có:

```text
compiler_fence
memory_fence
```

Hai thứ hoàn toàn khác nhau.

### Compiler fence

Chỉ giới hạn compiler reordering.

Không nhất thiết sinh machine instruction.

### Memory fence

Tạo hardware ordering.

Có thể sinh instruction hoặc được target lowering thực hiện bằng primitive khác.

---

# 22. Volatile

Volatile dùng cho:

```text
MMIO
hardware registers
device memory
special machine-visible state
```

Ví dụ:

```axiom
unsafe {
    volatile_store(addr, value)
}
```

Compiler:

- không loại bỏ
- không merge tùy tiện
- không biến thành ordinary load/store
- phải bảo toàn volatile ordering semantics

Nhưng volatile **không tạo thread synchronization**.

---

# 23. Atomic vs Volatile

| Property | Atomic | Volatile |
|---|---:|---:|
| Atomicity | Có | Không mặc định |
| Thread synchronization | Có thể | Không |
| Compiler elimination | Không tùy tiện | Không |
| Hardware visibility | Có | Có |
| Modification order | Có | Không |
| MMIO | Không phải mục đích chính | Có |
| Memory ordering | Có | Không mặc định |

Có thể tồn tại API/library kết hợp các semantics khi target yêu cầu, nhưng Core semantic phải giữ chúng riêng.

---

# 24. Compiler Reordering Rules

Optimizer được phép reorder nếu:

```text
observable semantics unchanged
```

Một operation có thể reorder qua operation khác nếu không có:

```text
Dependency
+
Memory conflict
+
Happens-before constraint
+
Synchronization constraint
+
Volatile constraint
+
Atomic ordering constraint
```

Do đó memory optimizer phải hỏi:

```text
MayReorder(A, B)?
```

thay vì giả định mọi memory access đều ordered.

---

# 25. Memory Dependence Graph

Compiler xây:

```text
MemoryDependenceGraph
```

Node:

```text
MemoryEvent
```

Edge:

```text
RAW
WAR
WAW
RMW
ATOMIC
SYNC
VOLATILE
HB
```

Ví dụ:

```text
write x
   │ RAW
   ▼
read x
```

---

# 26. Synchronization Graph

Song song:

```text
SynchronizationGraph
```

Node:

```text
Atomic
Mutex
Channel
Thread
Task
Fence
```

Edge:

```text
SW
HB
```

Ví dụ:

```text
Thread A
  │
  ├─ write data
  ├─ release flag
  │
  ▼
Thread B
  ├─ acquire flag
  └─ read data
```

---

# 27. Race Proof

Mỗi potential conflict tạo:

```text
RaceCandidate
```

Compiler cố chứng minh một trong:

```text
DISJOINT
OR
READ_READ
OR
SINGLE_THREAD
OR
IMMUTABLE
OR
MUTUAL_EXCLUSION
OR
HAPPENS_BEFORE
OR
ATOMIC
OR
UNREACHABLE
```

Nếu không có proof:

```text
RACE_ERROR
```

---

# 28. RaceProof

Compiler nên lưu proof dạng:

```text
RaceProof {
    AccessA
    AccessB

    RegionRelation
    AccessRelation

    ThreadRelation
    SyncPath

    OwnershipFacts
    CapabilityFacts

    FinalReason
}
```

Ví dụ:

```text
AccessA = write(data.x)
AccessB = read(data.x)

RegionRelation = SAME
AccessRelation = WRITE_READ

ThreadRelation = ThreadA != ThreadB

SyncPath:
    release(flag)
        →
    acquire(flag)

FinalReason = PROVEN_SYNCHRONIZED
```

Điều này rất có giá trị cho AI/compiler diagnostics.

---

# 29. Diagnostic

Không nên báo:

```text
data race detected
```

đơn giản như C sanitizer.

Axiom có thể báo:

```text
error AXM-RACE-001:
concurrent write/read access may conflict

write:
    worker_a → data.value

read:
    worker_b → data.value

no happens-before relation was proven.

Possible resolutions:
    - transfer ownership
    - use a synchronization primitive
    - use an atomic type
    - establish disjoint regions
```

AI agent có thể đọc semantic proof trực tiếp.

---

# 30. CompilerDB

BOOTSTRAP-363 bổ sung:

```text
MemoryModelDB
MemoryEventDB
MemoryRegionDB
MemoryAccessDB
MemoryOrderDB
AtomicSemanticDB
AtomicObjectDB
AtomicModificationDB
AtomicLoadDB
AtomicStoreDB
AtomicRmwDB
AtomicCasDB
FenceDB
VolatileDB
SequencedBeforeDB
SynchronizesWithDB
HappensBeforeDB
MemoryDependenceDB
SynchronizationGraphDB
RaceCandidateDB
RaceProofDB
RaceVerificationDB
ThreadMemoryDB
SharedMemoryDB
MemoryVisibilityDB
MemoryReorderingDB
CompilerFenceDB
HardwareFenceDB
```

---

# 31. MIR additions

MIR semantic layer cần có:

```text
LOAD
STORE

ATOMIC_LOAD
ATOMIC_STORE
ATOMIC_RMW
ATOMIC_CAS

VOLATILE_LOAD
VOLATILE_STORE

COMPILER_FENCE
MEMORY_FENCE

LOCK
UNLOCK

CHANNEL_SEND
CHANNEL_RECEIVE

THREAD_START
THREAD_JOIN

TASK_COMPLETE
TASK_AWAIT
```

Memory metadata:

```text
MemoryRegionId
StorageId
AccessMode
Atomicity
MemoryOrder
ExecutionDomain
SynchronizationDomain
```

---

# 32. Memory Event IDs

Mỗi memory event có stable ID:

```text
MemoryEventId
```

Không dùng machine instruction address làm identity.

Điều này cho phép:

```text
source
→ HIR
→ MIR
→ optimized MIR
→ machine
```

giữ được provenance.

---

# 33. Optimization interaction

Memory model phải nằm **trước** aggressive optimization.

Pipeline:

```text
Typed MIR
   ↓
Ownership
   ↓
Capability
   ↓
Effect
   ↓
Concurrency
   ↓
Memory Model Verification
   ↓
Race Verification
   ↓
Verified MIR
   ↓
Optimization
```

Sau optimization:

```text
Optimized MIR
   ↓
Memory Semantic Validation
```

để đảm bảo transform không phá memory semantics.

---

# 34. Optimizer Contract

Mỗi optimization pass có:

```text
MemoryPreservationContract
```

Ví dụ:

```text
LoopInvariantCodeMotion:
    preserves HB
    preserves atomic modification order
    preserves volatile ordering
```

Một pass không chứng minh được điều này không được chạy trên region tương ứng.

---

# 35. Dead Load / Store Elimination

Compiler có thể loại:

```text
x = 1
x = 2
```

nếu write đầu không observable.

Nhưng không được loại:

```text
atomic_store(x, 1, Release)
```

chỉ vì giá trị cuối cùng giống nhau.

Tương tự:

```text
volatile_store(...)
```

không được DCE như ordinary store.

---

# 36. Load Reordering

Ví dụ:

```axiom
a = x
b = y
```

compiler có thể reorder machine loads nếu:

```text
x/y independent
```

và không có synchronization constraint.

Nhưng:

```text
Acquire
```

là semantic barrier đối với các memory effects mà nó bảo vệ.

---

# 37. Lock Elision

Compiler **có thể** loại mutex nếu chứng minh:

```text
only one thread can access protected object
```

hoặc lock/unlock hoàn toàn không observable.

Ví dụ:

```text
local Mutex<Data>
```

không escape khỏi thread.

Compiler có thể biến:

```text
lock
update
unlock
```

thành:

```text
update
```

Nhưng chỉ khi chứng minh semantics không observable khác.

---

# 38. Atomic Elision

Tương tự:

```text
Atomic<T>
```

không nhất thiết phải compile thành atomic instruction nếu compiler chứng minh object:

```text
single-thread confined
```

và không có observable address escape.

Ví dụ:

```axiom
fn f() {
    let x = Atomic(0)
    x.store(10, Relaxed)
    print(x.load(Relaxed))
}
```

có thể trở thành:

```text
print(10)
```

Nếu không có external observation.

Đây là **zero-cost concurrency abstraction**.

---

# 39. Important invariant

Không được có quy tắc:

```text
"Atomic luôn chậm"
```

hoặc:

```text
"Mutex luôn tạo runtime overhead"
```

Semantic abstraction trước, machine representation sau.

Compiler phải tận dụng confinement, escape analysis và whole-program analysis.

---

# 40. CPU Memory Model Independence

Axiom language memory model không được phụ thuộc trực tiếp vào:

```text
x86
ARM
RISC-V
```

Thay vào đó:

```text
Axiom Memory Model
        ↓
Target Memory Mapping
        ↓
CPU Instructions/Fences
```

Ví dụ cùng:

```text
Acquire load
```

có thể map khác nhau trên x86 và ARM.

Source semantics không đổi.

---

# 41. GPU

GPU memory model phải dùng cùng abstraction:

```text
Atomicity
Ordering
Visibility
Synchronization
```

nhưng có thêm:

```text
Scope
StorageDomain
ExecutionDomain
```

Ví dụ:

```text
WorkItem
WorkGroup
Device
System
```

GPU backend chịu trách nhiệm map semantics xuống hardware.

Không được đưa GPU-specific barrier vào Core language semantics nếu abstraction library có thể cung cấp.

---

# 42. FFI

FFI boundary là trust boundary.

Ví dụ C function:

```text
extern fn foo(*mut Data)
```

compiler không thể tự biết function có:

```text
read
write
retain
escape
synchronize
```

hay không.

Vì vậy FFI declaration phải có semantic contract.

Ví dụ conceptual:

```text
FfiMemoryContract {
    reads
    writes
    aliases
    synchronization
    thread_safety
    ownership
}
```

Nếu không đủ thông tin:

```text
unknown
```

và compiler phải conservative.

---

# 43. Unsafe FFI

Unsafe FFI có thể bypass một số proof, nhưng:

```text
unsafe ≠ compiler may assume anything
```

Mọi assumption nên được lưu:

```text
TrustedFfiFact
```

để:

- diagnostics
- static analysis
- sanitizer
- AI tooling
- formal verification

có thể truy nguyên.

---

# 44. Sanitizer integration

BOOTPSTRAP-340 đã có runtime verification.

363 cung cấp semantic metadata để sanitizer có thể instrument:

```text
MemoryEventId
RegionId
ThreadId
SynchronizationEdge
```

Runtime sanitizer có thể phát hiện những trường hợp static compiler không chứng minh được.

Hai tầng:

```text
Static Proof
      +
Dynamic Verification
```

không thay thế nhau.

---

# 45. Compile-time vs runtime race detection

Compiler không cần chứng minh mọi runtime execution.

Ví dụ:

```axiom
if condition {
    spawn(...)
}
```

Nếu race phụ thuộc runtime condition, compiler có thể tạo:

```text
runtime instrumentation
```

hoặc yêu cầu synchronization abstraction.

Nhưng safe source không được mặc định rơi xuống:

```text
undefined behavior
```

chỉ vì static proof khó.

---

# 46. Safe / Unsafe boundary

Axiom có ba trạng thái semantic:

```text
PROVEN_SAFE
TRUSTED_UNSAFE
INVALID
```

Không có:

```text
UNKNOWN → silently accepted
```

trong safe code.

---

# 47. Core invariants

Đóng băng:

### `AMEM-01`
Ordinary memory access obeys ownership/capability rules.

### `AMEM-02`
Safe code cannot contain an unproven conflicting concurrent ordinary access.

### `AMEM-03`
Atomicity and ordering are distinct properties.

### `AMEM-04`
Volatile and atomic are distinct semantics.

### `AMEM-05`
Sequenced-before is semantic, not physical instruction order.

### `AMEM-06`
Synchronizes-with is an explicit semantic relation.

### `AMEM-07`
Happens-before is the transitive closure of required ordering relations.

### `AMEM-08`
READ+READ does not constitute a data race.

### `AMEM-09`
Conflicting WRITE access requires disjointness or synchronization.

### `AMEM-10`
Unknown overlap is not automatically safe.

### `AMEM-11`
Unsafe does not globally disable memory verification.

### `AMEM-12`
Trusted unsafe facts must be provenance-tracked.

### `AMEM-13`
Relaxed atomicity does not imply publication ordering.

### `AMEM-14`
Acquire cannot be moved past protected reads/writes when that changes semantics.

### `AMEM-15`
Release cannot be moved before protected writes when that changes semantics.

### `AMEM-16`
SeqCst operations preserve the required global SC semantics.

### `AMEM-17`
Atomic modification order is preserved semantically.

### `AMEM-18`
Volatile operations are not dead-code eliminated as ordinary memory.

### `AMEM-19`
Compiler fences and hardware fences have distinct semantics.

### `AMEM-20`
Ownership confinement may eliminate synchronization.

### `AMEM-21`
Atomic operations may be optimized away when confinement proves them unobservable.

### `AMEM-22`
Lock operations may be optimized away when synchronization is provably unobservable.

### `AMEM-23`
Optimization must preserve observable memory semantics.

### `AMEM-24`
Target CPU memory models must not alter Axiom source semantics.

### `AMEM-25`
GPU memory semantics are lowered through an explicit target memory model.

### `AMEM-26`
FFI memory behavior is conservative unless explicitly contracted.

### `AMEM-27`
Safe code cannot silently depend on undefined memory ordering.

### `AMEM-28`
Memory event identity survives compiler IR transformations through provenance mapping.

### `AMEM-29`
Race proofs are compiler artifacts and are inspectable by diagnostics/tooling.

### `AMEM-30`
No mandatory runtime is required merely because a program uses safe concurrency.

---

# 48. Kiến trúc sau 363

Sau bước này, Axiom đã có một chuỗi khá hoàn chỉnh:

```text
Ownership
    ↓
Capability
    ↓
Concurrency
    ↓
Synchronization
    ↓
Memory Model
    ↓
Race Verification
    ↓
Optimization
```

và compiler có thể hiểu concurrency **ở mức semantic**, thay vì chỉ coi thread/atomic/mutex là những intrinsic rời rạc.

Đây cũng là nền tảng cần thiết trước khi đi sâu hơn vào **Thread/Execution Domain/OS scheduling**, bởi lúc đó thread không còn phải tự định nghĩa memory semantics nữa mà chỉ sử dụng model đã được đóng băng ở 363.