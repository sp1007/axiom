# BOOTSTRAP-230 — AXIOM MEMORY MODEL FORMALIZATION & MACHINE MEMORY ORDERING

**TRẠNG THÁI: FROZEN / COMPLETED**

Đây là một trong những specification quan trọng nhất của Axiom, vì từ đây compiler phải biết chính xác:

> **Được phép reorder cái gì, không được reorder cái gì, và khi nào một giá trị được phép được thread khác quan sát.**

Mục tiêu không phải tạo một memory model quá phức tạp cho programmer. Ngược lại:

> **Memory model phức tạp nằm trong compiler; programmer chỉ cần sử dụng các abstraction như ordinary value, `Atomic<T>`, `Mutex<T>`, channel, async...**

---

# 1. Kiến trúc memory model

Axiom chốt 5 tầng:

```text
                    AXIOM MEMORY SEMANTICS
                            │
             ┌──────────────┴──────────────┐
             │                             │
       Ordinary Memory               Atomic Memory
             │                             │
             └──────────────┬──────────────┘
                            │
                     Axiom Memory Events
                            │
                ┌───────────┴───────────┐
                │                       │
        Language Ordering        Synchronization
                │                       │
                └───────────┬───────────┘
                            ↓
                    Verified Memory Graph
                            ↓
                    Machine Memory Model
                            ↓
                x86 / ARM64 / RISC-V / GPU
```

---

# 2. Memory location

Mọi memory access trong MIR phải được quy về một semantic location.

```text
MemoryLocation {
    provenance
    region
    byte_range
    type
    storage_domain
}
```

Ví dụ:

```axiom
let x: i32 = 10
```

có semantic memory/value location:

```text
x
```

nhưng compiler hoàn toàn có thể giữ `x` trong register.

Do đó:

> **Memory location là semantic concept, không nhất thiết là physical RAM address.**

---

# 3. Register không phá memory semantics

Ví dụ:

```axiom
let x = a + b
let y = x * 2
```

compiler có thể:

```text
R1 = a + b
R2 = R1 * 2
```

không cần allocate `x`.

Semantic value vẫn tồn tại.

---

# 4. Ordinary memory

Ordinary memory có:

```text
READ
WRITE
MOVE
DROP
```

và chịu:

- ownership;
- capability;
- alias;
- happens-before;
- data-race rules.

---

# 5. Atomic memory

`Atomic<T>` có semantic access riêng:

```text
ATOMIC_LOAD
ATOMIC_STORE
ATOMIC_RMW
ATOMIC_CAS
ATOMIC_EXCHANGE
ATOMIC_FENCE
```

Không được hạ thành ordinary load/store nếu làm thay đổi observable semantics.

---

# 6. Memory event

MIR tạo các event:

```text
MemoryEvent {
    id
    location
    access_kind
    execution_domain
    ordering
    synchronization_scope
    source_span
}
```

Ví dụ:

```text
E1 = ordinary WRITE x
E2 = atomic STORE flag Release
E3 = atomic LOAD flag Acquire
E4 = ordinary READ x
```

---

# 7. Sequenced-Before

Trong một execution domain, Axiom định nghĩa:

```text
A SB B
```

nếu A phải được thực hiện trước B theo abstract machine semantics.

Ví dụ:

```axiom
x = 1
y = 2
```

có:

```text
WRITE x
   SB
WRITE y
```

nhưng compiler không nhất thiết giữ thứ tự machine instruction nếu việc reorder không thể quan sát được.

---

# 8. Important distinction

```text
Source order
    ≠
Sequenced-before
    ≠
Machine instruction order
```

Đây là nền tảng để optimizer mạnh.

---

# 9. Observable behavior

Compiler chỉ phải giữ ordering khi nó ảnh hưởng observable behavior.

Observable behavior gồm:

```text
return value
Result
panic
termination
I/O
volatile access
atomic behavior
synchronization
FFI effects
GPU synchronization
external resource effects
```

---

# 10. Pure ordinary operations

Ví dụ:

```axiom
let a = x + 1
let b = y * 2
```

Nếu:

```text
x
y
```

không alias và không có external effects, compiler có thể reorder.

---

# 11. Effect system tham gia

Memory model không hoạt động độc lập với EffectInfo.

Ví dụ:

```text
READ
WRITE
ATOMIC
VOLATILE
IO
FOREIGN
SYNCHRONIZE
```

được compiler ghi nhận.

Optimizer phải tôn trọng effect ordering.

---

# 12. Happens-Before

Axiom formalize:

```text
HB =
transitive closure(
    SB
    ∪ SW
)
```

Trong đó:

```text
SB = Sequenced-Before
SW = Synchronizes-With
```

---

# 13. Happens-before không phải physical time

Nếu:

```text
A HB B
```

không có nghĩa CPU nhất thiết thực thi A rồi mới bắt đầu B theo wall-clock.

Nó có nghĩa:

> Abstract machine không cho phép B quan sát trạng thái vi phạm quan hệ đó.

---

# 14. Synchronizes-With

Các abstraction có thể tạo SW:

```text
Release → Acquire
Mutex unlock → lock
Channel send → receive
Thread completion → join
Task completion → await/join
GPU event → host/device wait
```

chỉ khi contract tương ứng quy định.

---

# 15. Atomic Relaxed

```axiom
x.load(Relaxed)
x.store(v, Relaxed)
```

đảm bảo:

- atomicity;
- modification order của atomic object;

nhưng không tự tạo inter-thread synchronization.

---

# 16. Acquire

Acquire operation:

```text
load(Acquire)
```

có thể nhận synchronization từ Release operation tương ứng.

Nếu:

```text
Thread A:

x = 42
flag.store(1, Release)
```

và:

```text
Thread B:

if flag.load(Acquire) == 1 {
    read x
}
```

thì compiler phải giữ quan hệ:

```text
WRITE x
   SB
RELEASE flag
   SW
ACQUIRE flag
   SB
READ x
```

suy ra:

```text
WRITE x HB READ x
```

---

# 17. Đây là semantic guarantee

Compiler không được biến:

```text
x = 42
flag.store(1, Release)
```

thành thứ tự làm cho `flag` visible trước `x` theo cách phá vỡ Release semantics.

---

# 18. Release

Release operation đảm bảo các memory effects trước nó theo ordering semantics không bị visibility-reordered sau synchronization point.

Nói ngắn:

```text
prior writes
      ↓
Release
      ↓
Acquire
      ↓
later reads
```

---

# 19. AcqRel

RMW:

```axiom
counter.fetch_add(1, AcqRel)
```

có:

```text
Acquire
+
Release
```

semantics.

---

# 20. SeqCst

`SeqCst` mạnh hơn:

```text
atomicity
+
Acquire/Release semantics
+
single global sequentially-consistent order
```

cho tất cả SeqCst operations theo model.

---

# 21. Không dùng SeqCst làm mặc định

Axiom không biến mọi atomic thành SeqCst.

Lý do:

- compiler freedom;
- CPU instruction cost;
- scalability;
- unnecessary fences.

Programmer/library chọn ordering phù hợp.

---

# 22. Modification Order

Mỗi atomic location có một modification order:

```text
M1 → M2 → M3 → M4
```

Mọi atomic write/RMW của cùng location phải tuân thủ order này.

---

# 23. Atomic read

Một atomic load phải quan sát một modification hợp lệ theo atomic model.

Compiler không được tạo giá trị:

```text
not produced by any valid atomic modification
```

---

# 24. Không có “out of thin air”

Axiom cấm compiler tạo giá trị chỉ vì một speculative dependency vòng khiến giá trị tự xuất hiện.

Ví dụ không được:

```text
x = y ? 1 : 0
y = x ? 1 : 0
```

tạo ra giá trị mới không có nguồn hợp lệ chỉ do speculation.

---

# 25. Ordinary data race

Hai conflicting ordinary accesses:

```text
A
B
```

nếu:

```text
same/may-overlap location
+
different execution domains
+
at least one WRITE
+
no HB
```

→ program không phải safe execution.

Trong safe Axiom:

```text
compile-time reject
```

nếu compiler có thể chứng minh violation.

---

# 26. UNKNOWN không phải proof

Nếu compiler chỉ biết:

```text
MayAlias
```

không được tự suy ra:

```text
NoRace
```

Đây là nguyên tắc xuyên suốt Axiom:

> **Unknown is never proof.**

---

# 27. Nhưng compiler không phải chứng minh mọi runtime path bằng theorem prover

Axiom sử dụng:

```text
static proof
+
capability contracts
+
synchronization contracts
+
unsafe trusted boundaries
```

để tạo đủ facts.

Nếu abstraction đã cung cấp invariant, compiler có thể tin contract đó trong boundary thích hợp.

---

# 28. Memory model không cấm optimization

Ví dụ:

```axiom
let x = 10
let y = 20
let z = x + y
```

compiler có thể:

```text
z = 30
```

hoặc thậm chí:

```text
return 30
```

Memory model không yêu cầu tạo physical memory cho `x`, `y`.

---

# 29. Dead store elimination

```axiom
x = 1
x = 2
return x
```

compiler có thể bỏ:

```text
x = 1
```

nếu không có:

- volatile;
- atomic;
- aliasing observable;
- FFI;
- external effect.

---

# 30. Không được bỏ volatile

```text
volatile_write(mmio, value)
```

luôn là observable machine effect theo contract.

---

# 31. Không được merge atomic tùy tiện

Ví dụ:

```axiom
a.store(1, Relaxed)
a.store(2, Relaxed)
```

compiler không được tự động biến thành:

```text
a.store(2, Relaxed)
```

nếu một concurrent observer có thể quan sát `1` và semantics cho phép observation đó.

Atomic operations là observable synchronization events.

---

# 32. Tuy nhiên dead atomic elimination có điều kiện

Nếu compiler chứng minh atomic object:

```text
not externally reachable
+
no concurrent observer
+
no FFI
```

thì có thể optimize mạnh hơn.

Đây là consequence của escape analysis.

---

# 33. MemorySSA

Sau Verified MIR:

```text
MemorySSA
```

ghi lại:

```text
MemoryDef
MemoryUse
MemoryPhi
```

nhưng phải được xây trên semantic memory regions.

---

# 34. AliasInfo + MemorySSA

Ví dụ:

```text
A = WRITE region R1
B = READ region R2
```

Nếu:

```text
R1 DISJOINT R2
```

MemorySSA có thể chứng minh B không phụ thuộc A.

---

# 35. Atomic memory không được coi ordinary memory

MemorySSA phải có category:

```text
Ordinary
Atomic
Volatile
External
```

để tránh các optimization sai.

---

# 36. Compiler reordering

Một phép reorder:

```text
A
B
```

thành:

```text
B
A
```

chỉ hợp lệ nếu:

```text
Observable(A,B) unchanged
```

và:

```text
HB constraints preserved
```

và:

```text
atomic semantics preserved
```

và:

```text
external effects preserved
```

---

# 37. Formal optimization legality

Mỗi optimization pass phải chứng minh:

```text
Preconditions
    ↓
Transformation
    ↓
Preserved Memory Facts
    ↓
Preserved Synchronization Facts
    ↓
Observable Equivalence
```

---

# 38. Translation validation

Với những pass phức tạp, Axiom có thể dùng:

```text
before IR
+
after IR
+
proof/check
```

để xác nhận transformation.

Đặc biệt quan trọng với:

- atomic optimization;
- loop transformations;
- vectorization;
- concurrency-aware optimization.

---

# 39. Compiler barrier

Axiom phân biệt:

```text
compiler_fence(Ordering)
```

và:

```text
cpu_fence(Ordering)
```

Compiler fence chủ yếu hạn chế compiler transformations.

CPU fence tạo machine-level ordering.

---

# 40. Atomic fence

```axiom
fence(Acquire)
fence(Release)
fence(SeqCst)
```

được định nghĩa trong abstract memory model trước khi backend quyết định machine instruction.

---

# 41. Backend không được tự ý đổi semantics

Ví dụ:

```text
Axiom Release
```

trên ARM64 có thể cần:

```text
STLR
```

trong khi x86 có thể dùng ordinary store tùy context.

Axiom semantics là nguồn sự thật.

---

# 42. x86-64

x86 có memory ordering tương đối mạnh.

Compiler có thể thường xuyên lower:

```text
Release store
```

thành ordinary store.

Nhưng:

```text
SeqCst
RMW
fence
```

có thể cần instructions mạnh hơn.

---

# 43. ARM64

ARM64 weakly ordered hơn.

Release/Acquire thường map tới:

```text
STLR
LDAR
```

hoặc các sequence tương đương.

Compiler không được áp dụng x86 assumptions lên ARM.

---

# 44. RISC-V

RISC-V dùng memory ordering primitives/annotations phù hợp:

```text
AQ
RL
fence
```

backend phải map Axiom semantic ordering xuống target.

---

# 45. Pointer width không liên quan trực tiếp memory ordering

```text
usize
pointer width
address space
```

là target representation.

Memory ordering là semantic concurrency property.

Không trộn hai abstraction.

---

# 46. CPU cache coherence

Axiom không giả định programmer phải quản lý cache coherence trực tiếp trong ordinary shared memory.

Platform target phải cung cấp machine memory semantics phù hợp.

Cache flush/invalidate chỉ xuất hiện trong:

```text
device
DMA
non-coherent memory
MMIO
special system API
```

---

# 47. DMA

DMA memory là external/device storage domain.

Ví dụ:

```text
CPU writes buffer
↓
cache/device synchronization
↓
DMA device reads
```

cần explicit API contract.

Không đưa DMA semantics vào ordinary `view<T>`.

---

# 48. GPU memory model

GPU có memory model riêng.

Axiom semantic layer vẫn giữ:

```text
ownership
capability
ordering
synchronization
```

nhưng target backend map xuống:

- Vulkan memory model;
- SPIR-V;
- CUDA;
- Metal;
- D3D;
- WebGPU.

---

# 49. GPU barrier

GPU barrier phải encode:

```text
execution scope
memory scope
memory semantics
```

không chỉ một `fence()` generic.

---

# 50. Host/device ordering

Ví dụ:

```text
GPU writes buffer
event.signal()
CPU wait(event)
CPU reads buffer
```

phải tạo semantic:

```text
GPU WRITE
   ↓
GPU completion
   SW
CPU WAIT
   ↓
CPU READ
```

---

# 51. Memory model + FFI

Foreign function:

```axiom
extern "C" fn foo(...)
```

mặc định conservative.

Nếu compiler không biết function có:

- memory writes;
- atomic effects;
- synchronization;
- callbacks;
- thread creation;

thì phải coi nó có thể ảnh hưởng observable memory state.

---

# 52. FFI contract

Có thể cung cấp:

```text
@pure
@readonly
@noalias
@atomic
@synchronizes
```

nhưng các annotations này phải là semantic contracts, không phải optimization hints đơn thuần.

---

# 53. `@noalias`

Nếu được dùng trong system/FFI boundary:

```text
@noalias
```

phải establish real precondition.

Compiler không được chấp nhận annotation chỉ vì programmer viết nó.

---

# 54. Unsafe FFI

Unsafe FFI có thể nói:

```text
foreign function guarantees:
    memory region A does not alias B
```

Compiler có thể sử dụng fact đó trong Verified MIR.

---

# 55. Memory order không phải Effect order hoàn toàn

Ví dụ:

```text
IO
```

có ordering semantics riêng.

```text
Atomic
```

có memory ordering riêng.

Do đó:

```text
Effect ordering
≠
Memory ordering
```

nhưng hai hệ thống tương tác.

---

# 56. Pure computation

Compiler được phép reorder pure expressions gần như tự do nếu:

```text
no observable difference
```

Ví dụ:

```text
f(x) + g(y)
```

nếu `f`, `g` pure có thể reorder.

---

# 57. Impure calls

Nếu:

```text
f()
g()
```

có side effects, compiler phải giữ effect ordering tương ứng.

Không được dùng “memory model” để phá function effect semantics.

---

# 58. Function effects

Mỗi function có EffectInfo:

```text
Pure
Read
Write
Atomic
IO
Blocking
Synchronize
Foreign
Panic
AsyncSuspend
```

Compiler sử dụng nó khi phân tích reorder.

---

# 59. `pure` phải thực sự pure

Nếu function khai báo pure nhưng truy cập:

```text
global mutable
IO
volatile
atomic
foreign effect
```

compiler reject.

Không được biến annotation thành “trust me”.

---

# 60. Atomic visibility example

Conceptual:

```axiom
static data: i32 = 0
static ready: Atomic<bool> = Atomic(false)

writer:
    data = 42
    ready.store(true, Release)

reader:
    if ready.load(Acquire) {
        print(data)
    }
```

Compiler xây:

```text
WRITE data
    SB
STORE ready Release
    SW
LOAD ready Acquire
    SB
READ data
```

→:

```text
WRITE data HB READ data
```

---

# 61. Relaxed variant

Nếu:

```text
ready.store(true, Relaxed)
```

và:

```text
ready.load(Relaxed)
```

thì không có Release/Acquire synchronization.

Nếu `data` cũng ordinary shared memory:

```text
data = 42
```

reader không được dùng `ready` như publication mechanism.

---

# 62. Đây là lý do Atomic không đủ

Một programmer có thể nghĩ:

> “Tôi dùng atomic flag nên chương trình thread-safe.”

Không nhất thiết.

Atomicity và visibility/order là hai vấn đề khác nhau.

---

# 63. Mutex dễ hơn

```text
lock
write
unlock

lock
read
unlock
```

Mutex contract tạo synchronization.

Programmer không cần tự thiết kế memory ordering.

Đây là abstraction mà Axiom khuyến khích cho code thông thường.

---

# 64. Low-level programmer vẫn có đầy đủ power

Có thể viết:

```text
Atomic<T>
Acquire
Release
AcqRel
SeqCst
fence
volatile
unsafe
raw pointers
```

Nhưng đây là **explicit semantic boundary**.

---

# 65. Memory model không dùng UB kiểu C

Axiom không muốn:

```text
data race
→ undefined behavior
→ compiler được làm bất kỳ điều gì
```

thay vào đó:

```text
safe source
→ compiler reject

unsafe source
→ contract boundary
→ verifier assumptions explicit
```

---

# 66. Đây là khác biệt quan trọng

Axiom vẫn cho compiler freedom cao nhưng không dựa vào việc programmer vô tình tạo UB.

Compiler có thể optimize dựa trên **verified facts**, thay vì dựa trên:

> “Có lẽ programmer không làm sai.”

---

# 67. Unsafe vẫn có thể tạo UB ở machine level?

Có thể nếu programmer phá contract.

Nhưng Axiom yêu cầu unsafe boundary phải rõ ràng.

Ví dụ:

```text
unsafe {
    write_raw(...)
}
```

là programmer bước ra khỏi fully verified abstraction.

---

# 68. Tuy nhiên compiler không biến unsafe thành toàn bộ function unverified

Ví dụ:

```text
unsafe raw operation
      ↓
establish capability
      ↓
Verified MIR
      ↓
safe optimization
```

Đây là mô hình đã frozen từ ownership/capability verifier.

---

# 69. Memory model và object lifetime

Memory access hợp lệ phải có:

```text
valid provenance
+
initialized state
+
not moved
+
not dropped
+
valid capability
```

Memory ordering không thay thế lifetime verification.

---

# 70. Vì vậy Axiom có 4 câu hỏi độc lập

```text
1. Object có tồn tại không?
2. Tôi có quyền truy cập không?
3. Access có xung đột không?
4. Nếu concurrent, ordering có hợp lệ không?
```

Tương ứng:

```text
Lifetime
Capability
Race
Memory Order
```

---

# 71. Memory model compiler pipeline

```text
Typed MIR
   ↓
Ownership
   ↓
Capability
   ↓
Alias
   ↓
Effect
   ↓
Concurrency
   ↓
Memory Event Extraction
   ↓
Synchronization Graph
   ↓
Happens-Before
   ↓
Race Verification
   ↓
Verified Memory Model
   ↓
Verified MIR
```

---

# 72. Sau đó mới optimize

```text
Verified MIR
     ↓
SSA
     ↓
MemorySSA
     ↓
Alias
     ↓
Effect
     ↓
Loop
     ↓
Vectorization
     ↓
Parallelization
     ↓
Target lowering
```

---

# 73. Memory model facts trở thành optimizer facts

Ví dụ:

```text
NoAlias
NoRace
ReadOnly
Immutable
Atomic
Release
Acquire
Volatile
External
```

được truyền xuống optimizer.

---

# 74. Nhưng optimizer không được “suy ngược” safety

Ví dụ:

```text
optimizer phát hiện hai địa chỉ khác nhau
```

không có nghĩa semantic capability verifier được phép coi chúng là disjoint.

Safety proof phải đến từ semantic analysis.

Optimizer chỉ được **sử dụng** safety facts.

---

# 75. Đây là invariant rất quan trọng

```text
Safety → Optimization

NOT

Optimization → Safety
```

---

# 76. Memory model + vectorization

Nếu:

```text
for i:
    a[i] = b[i] + c[i]
```

và compiler chứng minh:

```text
a
b
c
```

không alias gây dependency:

→ SIMD được phép.

Nếu alias UNKNOWN:

→ không được vectorize theo giả định no-alias.

---

# 77. Memory model + loop reordering

Compiler chỉ reorder iterations nếu không phá:

```text
dependency
atomic order
volatile order
IO order
synchronization
```

---

# 78. Atomic loop

```axiom
while (...) {
    counter.fetch_add(1, Relaxed)
}
```

compiler không được tự ý biến thành:

```text
counter += N
```

nếu điều đó làm thay đổi observable modification order hoặc atomic operation semantics.

Có thể có target-specific atomic combining nếu language semantics cho phép, nhưng mặc định phải bảo toàn atomic observation.

---

# 79. SeqCst global order

Compiler có thể reorder physical instructions nhưng abstract execution phải tương đương với một execution tồn tại trong:

```text
single SeqCst total order
```

---

# 80. Memory model target abstraction

Compiler backend nhận:

```text
TargetMemoryModel {
    coherence
    atomic_widths
    native_orderings
    fence_capabilities
    cache_coherence
    address_spaces
    device_memory
}
```

---

# 81. Target lowering

Ví dụ:

```text
Axiom:
    AtomicLoad(Acquire)
```

Backend:

```text
x86-64 → suitable acquire load
ARM64  → LDAR
RISC-V → load/fence sequence or equivalent
GPU    → target-specific acquire operation
```

---

# 82. Nếu target không có native atomic width

Ví dụ target không hỗ trợ atomic 128-bit.

Axiom không giả vờ rằng:

```text
Atomic<u128>
```

luôn lock-free.

Backend có thể:

```text
library fallback
```

nếu profile cho phép.

Hoặc compile error nếu:

```text
@lock_free_required
```

---

# 83. Atomic lock-free property

Library/compiler có thể expose:

```text
is_lock_free<T>()
```

compile-time hoặc runtime tùy target.

---

# 84. Freestanding

Freestanding Axiom vẫn có memory model.

Không cần:

- OS;
- allocator;
- thread runtime.

Nhưng nếu hardware có concurrency, atomic semantics vẫn tồn tại.

---

# 85. Kernel

Kernel code có thể sử dụng:

```text
volatile
atomic
fence
interrupt synchronization
DMA
MMIO
```

qua system layer.

---

# 86. Signal/interrupt ordering

Signal/interrupt không tự tạo ordinary memory synchronization.

Nếu cần:

```text
atomic flag
```

hoặc explicit platform synchronization.

---

# 87. Memory barriers và MMIO

System layer có thể cung cấp:

```text
mmio_write()
device_fence()
dma_sync()
```

với semantic effect rõ ràng.

Không dùng generic `Atomic` cho mọi device protocol.

---

# 88. Persistent/storage memory

Memory-mapped database:

```text
mapped view
```

không tự có persistence semantics.

Phải phân biệt:

```text
memory visibility
```

với:

```text
durability
```

Ví dụ:

```text
flush
fsync
persist
```

là storage semantics riêng.

---

# 89. Network ordering

TCP ordering:

```text
network byte sequence
```

không phải CPU happens-before.

Network protocol phải tạo synchronization/causal semantics ở distributed layer.

---

# 90. Distributed causality

Có thể có:

```text
message send
      ↓
network transport
      ↓
message receive
```

nhưng đây là:

```text
distributed happens-before
```

khác với shared-memory HB.

Axiom không nhập hai model thành một.

---

# 91. Memory model formal object

Axiom execution có:

```text
ExecutionGraph {
    Events
    SequencedBefore
    SynchronizesWith
    ModificationOrder
    HappensBefore
    ReadsFrom
}
```

Đây là abstract execution model.

---

# 92. `ReadsFrom`

Atomic load:

```text
L
```

được liên kết với modification:

```text
M
```

mà nó quan sát:

```text
M --ReadsFrom--> L
```

Backend phải tạo machine behavior tương đương một valid execution graph.

---

# 93. Compiler correctness target

Compiler correctness không cần bảo toàn instruction sequence.

Nó phải bảo toàn:

```text
observable execution graph
```

trong phạm vi semantic equivalence.

---

# 94. Reference interpreter

`ax-ref` cần hỗ trợ memory events ở mức abstract:

```text
ordinary memory
atomic memory
synchronization
HB
```

không mô phỏng cache/microarchitecture.

---

# 95. MIR interpreter

`ax-mir` có thể kiểm tra:

```text
ownership
capability
atomic
sync
panic
```

và tạo event trace.

---

# 96. Litmus tests

Axiom phải có bộ:

```text
Load Buffering
Store Buffering
Message Passing
IRIW
Dekker
Peterson
CAS patterns
Fence tests
```

nhưng test phải được diễn giải theo Axiom memory model, không đơn giản copy C++ test suite.

---

# 97. Architecture litmus

Chạy:

```text
Axiom abstract interpreter
vs
x86
vs
ARM64
vs
RISC-V
```

để xác nhận backend không tạo behavior nằm ngoài allowed model.

---

# 98. Compiler stress tests

Đặc biệt test:

```text
-O0
-O1
-O2
-O3
-Os
-Oz
-LTO
-PGO
```

phải có cùng semantic result.

---

# 99. Debug/release consistency

Một chương trình safe không được:

```text
Debug → behavior A
Release → behavior B
```

chỉ vì optimizer reorder ordinary memory theo một cách làm thay đổi semantics.

---

# 100. Atomic optimizer tests

Mỗi atomic optimization phải có:

```text
source
→ MIR
→ optimized MIR
→ abstract execution validation
```

---

# 101. Frozen invariants

```text
AMEM-20
Every semantic memory access has a defined memory location/provenance.

AMEM-21
Semantic memory locations are independent of physical storage realization.

AMEM-22
Register allocation does not alter memory semantics.

AMEM-23
Ordinary memory and atomic memory are distinct semantic categories.

AMEM-24
Atomic operations cannot be replaced by ordinary memory operations when observable semantics change.

AMEM-25
Every execution has a Sequenced-Before relation appropriate to the language semantics.

AMEM-26
Synchronizes-With edges arise only from specified synchronization contracts.

AMEM-27
Happens-Before is the transitive closure of Sequenced-Before and Synchronizes-With.

AMEM-28
Modification order is defined independently for each atomic object.

AMEM-29
Atomic reads observe only values permitted by the memory model.

AMEM-30
The memory model forbids out-of-thin-air values.

AMEM-31
Conflicting unordered ordinary accesses constitute a data-race violation.

AMEM-32
Unknown aliasing is never treated as proof of non-conflict.

AMEM-33
Verified disjoint regions may eliminate memory-conflict candidates.

AMEM-34
Acquire operations provide the ordering semantics specified by the model.

AMEM-35
Release operations provide the ordering semantics specified by the model.

AMEM-36
AcqRel combines Acquire and Release semantics.

AMEM-37
SeqCst operations participate in a single sequentially-consistent order.

AMEM-38
Relaxed atomics do not imply inter-thread synchronization.

AMEM-39
Atomicity and ordering are independent semantic dimensions.

AMEM-40
Compiler fences and hardware fences are distinct semantic operations.

AMEM-41
Volatile operations are distinct from atomic operations.

AMEM-42
Volatile accesses remain observable according to their contract.

AMEM-43
Optimization may reorder operations only when the resulting execution is semantically equivalent.

AMEM-44
Optimization must preserve required Happens-Before relationships.

AMEM-45
Optimization must preserve atomic modification and observation semantics.

AMEM-46
Optimization must preserve volatile ordering requirements.

AMEM-47
Optimization must preserve external and FFI effects.

AMEM-48
MemorySSA must distinguish ordinary, atomic, volatile and externally observable memory.

AMEM-49
MemorySSA may exploit verified alias and capability facts.

AMEM-50
Optimizer-generated alias facts cannot retroactively establish language safety.

AMEM-51
Safety proofs precede optimization proofs.

AMEM-52
Target lowering must preserve Axiom memory semantics.

AMEM-53
Target memory ordering differences are handled by backend lowering.

AMEM-54
Axiom semantics do not assume x86-specific ordering.

AMEM-55
ARM64 weak-memory behavior must be explicitly respected.

AMEM-56
RISC-V memory ordering must be explicitly respected.

AMEM-57
GPU memory ordering is represented using target-specific execution and memory scopes.

AMEM-58
Host/device synchronization is explicit.

AMEM-59
DMA and device memory are distinct from ordinary coherent memory.

AMEM-60
FFI calls are conservative unless an explicit verified contract provides stronger facts.

AMEM-61
Pure functions cannot perform hidden observable memory effects.

AMEM-62
Atomic operations are observable synchronization events.

AMEM-63
Dead-store elimination may remove only stores proven unobservable.

AMEM-64
Atomic operations cannot be eliminated merely because their loaded/stored value is unused.

AMEM-65
Concurrent atomic observation must remain semantically valid after optimization.

AMEM-66
Memory ordering is independent of object lifetime and ownership validity.

AMEM-67
A valid memory ordering operation cannot resurrect an invalid or dropped object.

AMEM-68
A valid capability is required before ordinary memory access.

AMEM-69
Unsafe memory operations must establish explicit trusted preconditions.

AMEM-70
Safe verification resumes after a trusted unsafe boundary.

AMEM-71
The reference interpreter models abstract memory semantics rather than physical cache behavior.

AMEM-72
MIR interpretation may produce abstract memory-event traces.

AMEM-73
Compiler correctness is judged against observable execution semantics, not instruction sequence identity.

AMEM-74
Different machine implementations are valid when they implement an allowed Axiom execution.

AMEM-75
-O0 and optimized builds must preserve memory semantics.

AMEM-76
LTO and PGO must preserve memory semantics.

AMEM-77
Parallelization must preserve synchronization and dependency semantics.

AMEM-78
Vectorization must preserve memory and atomic semantics.

AMEM-79
The memory model is deterministic as a specification even when concurrent executions admit multiple legal outcomes.

AMEM-80
Axiom does not use unspecified behavior as an optimization license where a semantic rule can be defined.

AMEM-81
Data-race freedom is a safe-language guarantee.

AMEM-82
Data-race freedom does not imply deadlock freedom.

AMEM-83
Data-race freedom does not imply algorithmic correctness.

AMEM-84
Memory visibility does not imply persistence/durability.

AMEM-85
Network causality is distinct from shared-memory Happens-Before.

AMEM-86
Persistent-storage ordering is distinct from CPU memory ordering.

AMEM-87
Architecture-specific fences are implementation details of target lowering unless exposed by system APIs.

AMEM-88
Lock-free status is not implied by Atomic<T>.

AMEM-89
Atomic width support is target-dependent and explicitly represented in TargetSpec.

AMEM-90
Fallback atomic implementations must preserve the same observable Axiom semantics.

AMEM-91
The compiler may eliminate synchronization only when it proves that the synchronization is semantically unobservable and its removal preserves all permitted executions.

AMEM-92
Synchronization contracts are part of the semantic interface of concurrency abstractions.

AMEM-93
Memory-ordering facts are available to optimization but cannot weaken safety guarantees.

AMEM-94
The final machine image must implement the verified abstract memory semantics.

AMEM-95
Memory-model conformance tests are mandatory for every supported target architecture.
```

---

# 102. Kiến trúc cuối cùng sau BOOTSTRAP-230

Axiom hiện có một chuỗi rất rõ:

```text
SOURCE
  │
  ▼
Ownership
  │
  ▼
Capability
  │
  ▼
Alias / Region
  │
  ▼
Effect
  │
  ▼
Concurrency
  │
  ▼
Memory Model
  │
  ▼
Verified MIR
  │
  ▼
Optimization
  │
  ▼
ABI
  │
  ▼
Machine Code
```

Điểm cực kỳ quan trọng là **optimizer không nằm trong correctness boundary**.

Nó chỉ được phép hoạt động trên những facts đã được verifier chứng minh.

---

# 103. Một nguyên tắc lớn được khóa lại

Axiom không cần chọn giữa:

> **“an toàn nhưng chậm”**

và:

> **“nhanh nhưng nguy hiểm”.**

Thiết kế hiện tại cố đạt:

```text
SAFE PROGRAM
     │
     ├── ownership proof
     ├── capability proof
     ├── race proof
     ├── memory-order proof
     │
     ▼
VERIFIED MIR
     │
     ├── aggressive alias analysis
     ├── scalar replacement
     ├── SIMD
     ├── loop optimization
     ├── parallelization
     ├── LTO
     └── target-specific lowering
     │
     ▼
NATIVE CODE
```

Compiler càng thông minh thì programmer **càng ít phải viết**, chứ không phải càng nhiều annotation.

---

# TASK TIẾP THEO

## **BOOTSTRAP-231 — COMPILER INTRINSICS, BUILTINS & TARGET-SPECIFIC OPERATIONS**

Task tiếp theo sẽ chốt một vấn đề rất quan trọng:

Axiom muốn đạt hiệu năng sát C/C++/ASM, GPU, SIMD, atomics, crypto, CPU instructions... nhưng **không được biến Core thành một đống intrinsic phụ thuộc từng CPU**.

Sẽ thiết kế:

```text
Axiom semantic operation
        ↓
Compiler builtin
        ↓
Target-independent intrinsic
        ↓
Target legalization
        ↓
CPU/GPU instruction
```

và phân biệt rõ:

- language primitive;
- compiler builtin;
- intrinsic;
- target intrinsic;
- CPU instruction;
- SIMD;
- atomic;
- fence;
- bit operation;
- overflow operation;
- CPU feature;
- GPU intrinsic;
- inline assembly;
- system intrinsic;
- `unsafe`;
- `@target`;
- `@requires`;
- fallback implementation;
- constant folding;
- compile-time evaluation;
- runtime dispatch;
- multiversioning.

Đặc biệt sẽ giải quyết câu hỏi:

> **Axiom làm thế nào để programmer có thể xuống gần ASM khi cần, nhưng 99% code không phải học instruction set của từng CPU?**