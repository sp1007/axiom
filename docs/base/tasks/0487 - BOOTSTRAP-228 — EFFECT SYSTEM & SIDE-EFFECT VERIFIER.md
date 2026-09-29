# BOOTSTRAP-228 — EFFECT SYSTEM & SIDE-EFFECT VERIFIER

**TRẠNG THÁI: FROZEN / COMPLETED**

Task này chốt một phần rất quan trọng của Axiom:

> **Compiler phải biết một function có thể quan sát hoặc tác động gì ra bên ngoài, nhưng programmer không bị bắt viết một đống effect annotation.**

Mục tiêu không phải biến Axiom thành ngôn ngữ “effect-heavy”, mà là để compiler có đủ thông tin cho:

- tối ưu hóa;
- dead-code elimination;
- CSE/hoisting;
- parallelization;
- async;
- FFI;
- GPU;
- transaction;
- deterministic execution;
- AI/compiler explanation;
- incremental compilation.

---

# 1. Nguyên tắc trung tâm

Axiom sử dụng:

> **Inferred Effects + Explicit Effect Boundaries**

Tức là:

```text
Programmer:
    viết code bình thường

Compiler:
    tự suy luận effects

System/FFI:
    có thể yêu cầu effect contract rõ ràng

Optimizer:
    sử dụng effect facts
```

Không thiết kế kiểu:

```text
fn foo() ![IO, Alloc, Throw, Network, ...]
```

cho mọi function.

---

# 2. Vì sao không nên bắt programmer annotate effect?

Ví dụ:

```axiom
fn calculate(x: f64) -> f64 {
    return x * 2.0
}
```

Không cần:

```text
pure
```

hay:

```text
effects = {}
```

Compiler tự biết.

---

# 3. Effect không đồng nghĩa với ownership

Hai hệ thống khác nhau:

```text
Ownership:
    ai sở hữu?

Capability:
    ai truy cập vùng nào?

Effect:
    hành động đó có tác động gì?
```

Ví dụ:

```axiom
fn read_value(x: Data) -> i32 {
    return x.value
}
```

Có:

```text
READ memory
```

nhưng không có:

```text
IO
Network
Process
```

---

# 4. Effect lattice

Axiom không dùng một enum đơn giản.

Internal effect set:

```text
EffectSet {
    Memory
    Allocate
    Deallocate
    Drop
    Atomic
    Synchronize
    IO
    FileSystem
    Network
    Process
    Environment
    Time
    Random
    Foreign
    GPU
    Panic
    Unwind
    Blocking
    AsyncSuspend
    ExternalState
    Volatile
    Unsafe
}
```

Một function có thể có nhiều effect.

---

# 5. Effect hierarchy

Một số effect có quan hệ:

```text
IO
├── FileSystem
├── Network
├── Console
└── Device

ExternalState
├── Environment
├── Time
├── Random
└── Process

Concurrency
├── Atomic
├── Synchronize
└── Blocking
```

Nhưng compiler không nên coi mọi subtype là thay thế hoàn toàn cho nhau.

Ví dụ:

```text
Network ⊂ IO
```

có thể dùng cho summary, nhưng optimizer vẫn cần biết **Network cụ thể**.

---

# 6. Semantic effect vs implementation effect

Đây là điểm rất quan trọng.

Ví dụ:

```axiom
let x = Box.new(value)
```

Có thể source-level có:

```text
Allocate
```

nhưng compiler sau optimization biến nó thành:

```text
register
```

và không allocation.

Effect system phải phân biệt:

```text
Semantic Effect
```

với:

```text
Physical Implementation Event
```

---

# 7. Allocation

`Allocate` chỉ là observable effect nếu allocation failure/allocator behavior được exposed.

Nếu:

```text
Box<T>
```

được scalar-replace:

```text
heap allocation → none
```

thì implementation effect biến mất.

Semantic behavior vẫn phải tương đương.

---

# 8. MIR effect representation

Mỗi MIR instruction có effect summary:

```text
InstructionEffect {
    reads
    writes
    allocates
    deallocates
    drops
    atomics
    synchronization
    io
    foreign
    panic
    volatile
}
```

---

# 9. Function Effect Summary

Compiler tạo:

```text
EffectSummary {
    effects
    memory_regions
    external_state
    may_panic
    may_unwind
    may_block
    may_suspend
}
```

Ví dụ:

```text
foo:
    Memory.Read
    Memory.Write
```

---

# 10. Pure function

Axiom không cần keyword `pure`.

Compiler có thể suy luận:

```text
fn square(x: f64) -> f64
```

→:

```text
Effects = {}
```

theo semantic effect model.

---

# 11. Pure không có nghĩa “không đọc memory”

Ví dụ:

```axiom
fn length(v: view<i32>) -> usize {
    return v.len()
}
```

Có thể đọc metadata/capability.

Nếu chỉ đọc immutable semantic input thì function vẫn có thể được coi là **referentially transparent** tùy effect classification.

Do đó cần phân biệt:

```text
NoExternalEffect
```

với:

```text
NoMemoryRead
```

---

# 12. Effect categories chính

Axiom chốt 5 nhóm:

```text
LOCAL
MEMORY
CONCURRENCY
EXTERNAL
CONTROL
```

---

# 13. LOCAL

Các effect không quan sát được bên ngoài function:

```text
register
stack
temporary
SSA
compiler-generated state
```

Không coi là external effect.

---

# 14. MEMORY

```text
Read
Write
Move
Drop
Allocate
Deallocate
Volatile
```

Nhưng:

```text
Move
```

không nhất thiết là external side effect.

Move chủ yếu thuộc ownership semantics.

---

# 15. CONCURRENCY

```text
Atomic
Synchronize
Blocking
Wake
TaskSpawn
TaskJoin
ThreadStart
ThreadJoin
```

Các effect này quan trọng vì chúng ảnh hưởng ordering.

---

# 16. EXTERNAL

```text
FileSystem
Network
Process
Environment
Clock
Random
Device
Foreign
Console
```

Compiler phải coi chúng là observable external state.

---

# 17. CONTROL

```text
Panic
Unwind
Abort
AsyncSuspend
Cancellation
```

Đây không phải IO nhưng có ảnh hưởng observable tới control flow.

---

# 18. Effect composition

Nếu:

```text
foo → bar
bar → baz
baz → IO
```

thì:

```text
Effects(foo)
    =
DirectEffects(foo)
    ∪ Effects(bar)
```

đệ quy theo call graph.

---

# 19. Transitive effect inference

Ví dụ:

```axiom
fn save(x: Data) {
    write_file(x)
}

fn process(x: Data) {
    save(x)
}
```

Compiler tự suy ra:

```text
save:
    FileSystem
    IO

process:
    FileSystem
    IO
```

Không cần programmer annotate.

---

# 20. Recursive functions

Call graph có cycle:

```text
A → B
B → C
C → A
```

Compiler dùng fixed-point iteration:

```text
Effects(initial)
→ propagate
→ stabilize
```

---

# 21. Unknown external function

Nếu:

```axiom
extern "C" fn foreign_call(...)
```

không có contract:

```text
Effects = ConservativeForeign
```

bao gồm tối thiểu:

```text
Memory
ExternalState
Foreign
```

và các effect khác tùy ABI contract.

---

# 22. FFI contract

Nếu API khai báo:

```text
extern "C"
@effects(readonly)
fn c_strlen(...)
```

compiler có thể dùng contract.

Nhưng ABI không tự động có nghĩa effect-safe.

---

# 23. FFI không contract

Nếu không biết:

```text
foo()
```

có thể:

- modify memory;
- IO;
- spawn thread;
- access global state;
- panic;
- longjmp.

Compiler phải conservative.

---

# 24. Unsafe không đồng nghĩa tất cả effects

Không nên:

```text
unsafe => everything
```

Unsafe chỉ cho phép những thao tác semantic mà safe Core không chứng minh được.

Effect vẫn được track.

---

# 25. Unsafe example

```axiom
unsafe {
    volatile_write(...)
}
```

Effect:

```text
Volatile
Memory.Write
UnsafeBoundary
```

chứ không phải:

```text
UnknownEverything
```

---

# 26. Volatile

Volatile là observable memory operation.

Optimizer:

```text
cannot remove
cannot merge
cannot reorder
```

nếu vi phạm volatile semantics.

---

# 27. Atomic

Atomic operation:

```text
AtomicLoad
AtomicStore
AtomicRMW
```

có:

```text
Atomic
SynchronizationOrder
```

tùy memory ordering.

---

# 28. Relaxed atomic

```text
Atomic(Relaxed)
```

vẫn là observable atomic operation.

Nhưng không tạo `SynchronizesWith` như Release/Acquire.

---

# 29. Acquire/Release

Compiler effect model phải giữ:

```text
Release
Acquire
AcqRel
SeqCst
```

để optimizer không reorder vượt qua semantic boundary.

---

# 30. Mutex

```text
lock()
```

→:

```text
Synchronize
Blocking
```

nếu implementation có thể block.

`unlock()`:

```text
Synchronize
```

---

# 31. Channel

```text
send(x)
```

có:

```text
Synchronize
OwnershipTransfer
```

`receive()` tương ứng.

---

# 32. Spawn

```text
spawn(task)
```

có:

```text
Concurrency
ExternalScheduling
```

và semantic ownership transfer.

---

# 33. Async await

`.await` có:

```text
AsyncSuspend
```

nhưng không nhất thiết:

```text
ThreadSwitch
```

vì executor có thể tiếp tục cùng thread.

---

# 34. Blocking

Axiom phân biệt:

```text
AsyncSuspend
```

và:

```text
Blocking
```

Ví dụ:

```axiom
await socket.read()
```

→ AsyncSuspend.

Trong khi:

```axiom
socket.read_blocking()
```

→ Blocking.

---

# 35. Đây là cơ sở cho async verifier

Async compiler có thể kiểm tra:

```text
may_block_across_async
```

và tránh:

```text
blocking operation
```

trong async context nếu policy không cho phép.

---

# 36. File

```axiom
file.read(...)
```

effects:

```text
IO
FileSystem
ExternalState
```

Có thể thêm:

```text
Blocking
```

nếu API synchronous.

---

# 37. Network

```axiom
socket.send(...)
```

effects:

```text
IO
Network
ExternalState
```

Async variant thêm:

```text
AsyncSuspend
```

---

# 38. Environment

```axiom
env.get("PATH")
```

→:

```text
Environment
ExternalState
```

Do đó compiler không được constant-fold tùy tiện thành một giá trị compile-time.

---

# 39. Time

```axiom
clock.now()
```

→:

```text
Time
ExternalState
```

Hai lần gọi không mặc định cùng giá trị.

---

# 40. Random

```axiom
rng.next()
```

→:

```text
Random
ExternalState
```

Không được CSE hai lần gọi nếu RNG state/observable semantics yêu cầu khác nhau.

---

# 41. Comptime

Comptime cũng có effect system riêng.

Ví dụ:

```axiom
comptime {
    read_source(...)
}
```

có:

```text
Comptime
ReadSource
```

---

# 42. Comptime external capability

```text
ReadFilesystem
Network
ExecuteTool
Environment
Time
Random
```

không được xem là pure compiler computation.

---

# 43. Build fingerprint

Nếu comptime đọc file:

```text
file.txt
```

thì effect phải đi vào build dependency graph:

```text
ComptimeEffect
       ↓
ExternalInput
       ↓
BuildFingerprint
```

---

# 44. Pure comptime

```axiom
comptime fn factorial(n: usize) -> usize
```

nếu chỉ tính toán:

```text
Comptime
```

nhưng không external effect.

Compiler có thể cache.

---

# 45. GPU effects

Kernel không được:

```text
FileSystem
Network
Process
```

Kernel effect verifier reject.

---

# 46. GPU memory effects

GPU kernel có:

```text
DeviceMemory.Read
DeviceMemory.Write
Atomic
Barrier
```

thay vì CPU `FileSystem`.

---

# 47. Kernel legality

Pipeline:

```text
Typed HIR
 ↓
GPU Lowering
 ↓
Effect Verification
 ↓
GPU Legality
 ↓
GPU MIR
```

---

# 48. Effect + capability

Đây là điểm mạnh:

```text
Capability:
    WRITE buffer[0..n]

Effect:
    DeviceMemory.Write
```

Compiler biết cả:

> **ghi ở đâu**

và:

> **loại tác động gì**

---

# 49. Effect + alias

Hai operations:

```text
WRITE A
WRITE B
```

Nếu:

```text
A DISJOINT B
```

có thể reorder/parallelize nếu các effect khác không cản trở.

---

# 50. External effect là barrier

Ví dụ:

```axiom
x = calculate()
print(x)
y = calculate2()
```

`print()` có:

```text
IO
```

Compiler không thể tùy tiện chuyển code qua IO nếu thay đổi observable behavior.

---

# 51. Effect ordering

MIR phải preserve:

```text
sequenced-before
```

đối với observable effects.

---

# 52. Effect independence

Nếu:

```text
calculate_a()
calculate_b()
```

đều:

```text
Effects = {}
```

và không có alias-dependent state:

compiler có thể:

- reorder;
- inline;
- duplicate/eliminate;
- parallelize.

---

# 53. Pure function CSE

```axiom
let a = sin(x)
let b = sin(x)
```

Nếu semantic FP profile cho phép:

```text
a == b
```

compiler có thể CSE.

Nếu strict FP có observable exception/rounding semantics cần giữ, effect/FP contract sẽ hạn chế transform.

---

# 54. Fast math

`@fast_math` hoặc profile tương đương tạo effect/semantic mode:

```text
FPRelaxed
```

Không được âm thầm bật.

---

# 55. Panic

Function:

```axiom
fn index(...)
```

có thể:

```text
Panic
```

nếu bounds failure có thể xảy ra.

Compiler có thể loại `Panic` effect khi proof:

```text
0 <= i < n
```

được chứng minh.

---

# 56. Panic effect không giống exception

Axiom không có exception propagation model.

Panic là:

```text
unrecoverable control effect
```

theo panic profile.

---

# 57. Result không phải effect

```axiom
fn parse(x: Str) -> Result<Value, Error>
```

không có:

```text
Error effect
```

chỉ vì function có thể trả lỗi.

Recoverable failure là data.

---

# 58. `?`

```axiom
let x = parse(input)?
```

không thêm một dynamic exception mechanism.

Nó chỉ tạo control-flow edge:

```text
Ok → continue
Err → return
```

---

# 59. Drop effect

Drop có thể:

```text
Deallocate
Close
Release
Synchronize
IO
```

tùy resource.

Ví dụ:

```text
File Drop
```

có semantic release resource.

---

# 60. Drop không đồng nghĩa IO

Một type có:

```text
Drop
```

không nhất thiết có IO.

Ví dụ:

```text
Vec<T>
```

Drop có thể chỉ release memory.

---

# 61. Fallible cleanup

`close() -> Result`:

```text
IO
```

Drop:

```text
resource release
```

Hai semantic khác nhau.

---

# 62. Optimizer và Drop

Compiler không được loại Drop nếu nó có observable effect.

Ví dụ:

```text
File Drop
```

có external resource semantics.

Nhưng:

```text
Box<i32>
```

nếu allocation bị scalarized:

Drop/deallocation có thể biến mất khi không observable.

---

# 63. Effect summaries của trait

Trait method:

```axiom
trait Writer {
    fn write(self: mut_view<Self>, data: view<Bytes>)
}
```

không cần source annotation.

Concrete implementation:

```text
ConsoleWriter → IO
MemoryWriter → Memory
NetworkWriter → IO + Network
```

Static dispatch có thể specialize theo concrete implementation.

---

# 64. Dynamic dispatch

```text
dyn Writer
```

effect summary phải nằm trong dynamic contract.

Nếu unknown implementation:

```text
conservative effect set
```

---

# 65. Generic effect inference

```axiom
fn map<T, U>(...)
```

effect phụ thuộc callback.

Nếu callback pure:

```text
map effects ≈ collection effects
```

Nếu callback IO:

```text
map effects += IO
```

---

# 66. Higher-order function

Compiler biểu diễn:

```text
EffectParam
```

nội bộ.

Ví dụ:

```text
map(F)
```

có effect:

```text
Effects(map implementation)
+
Effects(F)
```

---

# 67. Không expose effect generics v1

Programmer không cần viết:

```text
fn map<F: Fn !E>(...)
```

Compiler inference là mặc định.

Chỉ system/compiler contracts mới có thể cần explicit effect restrictions.

---

# 68. Effect restrictions

Một API có thể yêu cầu:

```text
@effectless
```

hoặc compiler-known equivalent.

Ví dụ callback dùng trong:

```text
comptime
const evaluation
parallel deterministic algorithm
```

Nếu callback tạo IO:

```text
reject
```

---

# 69. `const` / comptime

Compiler phải kiểm tra effect legality:

```text
const X = foo()
```

`foo()` không được có forbidden runtime/external effects.

---

# 70. Constant evaluation

```text
const X = 2 + 3
```

→ pure compile-time.

```text
const X = read_file(...)
```

→ reject nếu `const` không cho external effect.

Nếu muốn:

```text
comptime read_file(...)
```

phải dùng capability phù hợp.

---

# 71. Deterministic build

Reproducible profile có thể hạn chế:

```text
Time
Random
Environment
Network
```

trong comptime.

Effect verifier là cơ chế enforcement.

---

# 72. Effect polymorphism nội bộ

Compiler cần support:

```text
E1
E2
E1 ∪ E2
```

để generic inference không explode.

---

# 73. Effect normalization

Effect set được canonicalize:

```text
IO + FileSystem + Network
```

thành canonical bitset + parameters.

---

# 74. Parameterized effects

Một số effect cần region/resource:

```text
Memory.Read(region X)
Memory.Write(region Y)
File.Read(file F)
GPU.Write(buffer B)
```

Do đó EffectSet nên có:

```text
EffectKind
EffectSubject
EffectOrdering
```

---

# 75. Effect subject

Ví dụ:

```text
Write(x)
```

khác:

```text
Write(y)
```

Nếu:

```text
x DISJOINT y
```

optimizer có thể reorder.

---

# 76. Memory effect representation

```text
MemoryEffect {
    access: READ | WRITE | READ_WRITE
    region: Region
    volatile: bool
    atomic: optional Ordering
}
```

Capability verifier cung cấp region proof.

---

# 77. Effect ordering graph

MIR có:

```text
EffectNode
```

và dependencies:

```text
A → B
```

chỉ khi ordering observable.

Optimizer có thể reorder independent nodes.

---

# 78. External effect ordering

Ví dụ:

```text
write_file(A)
write_file(B)
```

mặc định:

```text
A → B
```

giữ thứ tự source nếu API semantics yêu cầu.

---

# 79. Pure computation giữa IO

```text
write_file(A)
calculate()
write_file(B)
```

`calculate()` có thể được hoist/reorder nếu không phụ thuộc A/B và không observable.

---

# 80. Foreign effect boundary

Foreign call:

```text
foo()
```

nếu conservative:

```text
Memory.ReadWrite
ExternalState
Foreign
```

→ compiler hạn chế reorder.

Nếu contract tốt:

```text
ReadOnly
NoExternalState
```

optimizer mạnh hơn.

---

# 81. Đây là lý do FFI contract quan trọng

C ABI chỉ nói:

```text
calling convention
```

không nói:

```text
memory behavior
side effects
thread behavior
```

Axiom cần cả hai.

---

# 82. Effect + concurrency

Ví dụ:

```text
Atomic Store Release
```

có:

```text
Memory.Write
Atomic
Synchronize
Release
```

Compiler không được collapse thành ordinary store.

---

# 83. Effect + task scheduler

```text
spawn(task)
```

có observable scheduling semantics tùy API.

Do đó:

```text
spawn
```

không được loại bỏ chỉ vì return value không dùng.

---

# 84. Effect + cancellation

Async future:

```text
drop(future)
```

không tự động có:

```text
CancelExternalOperation
```

trừ khi Future contract quy định.

Effect system phải phản ánh contract thực tế.

---

# 85. Effect + GPU launch

```text
let event = kernel<<<...>>>()
```

có:

```text
GPU.Launch
Async
```

Nhưng launch không đồng nghĩa completion.

---

# 86. GPU synchronization

```text
event.wait()
```

→:

```text
GPU.Sync
Blocking
```

hoặc async suspension tùy API.

---

# 87. Render commands

Recording command buffer:

```text
record(draw)
```

không nhất thiết external GPU effect ngay lập tức.

Submission:

```text
queue.submit(cmd)
```

mới tạo:

```text
GPU.Submit
```

Đây là semantic distinction cần thiết.

---

# 88. Effect + database

```text
transaction.commit()
```

có:

```text
ExternalState
Storage
IO
```

và là observable boundary.

Optimizer không được biến:

```text
commit()
```

thành dead code chỉ vì return value không dùng.

---

# 89. Effect + filesystem cache

Compiler/library có thể đánh dấu:

```text
cache lookup
```

là external state nếu cache behavior observable.

Nếu cache chỉ là transparent performance implementation:

```text
non-observable implementation effect
```

được phép biến mất.

---

# 90. Effect erasure

Sau semantic optimization, một số effects không còn cần tồn tại.

Ví dụ:

```text
Allocate Box
Drop Box
```

nếu scalar replacement:

```text
Allocate → eliminated
Deallocate → eliminated
```

---

# 91. Nhưng external effects không được erasure tùy tiện

```text
print()
```

không được DCE.

```text
file.close()
```

nếu close có semantic effect cũng không được.

---

# 92. Effect verifier

Pipeline:

```text
Typed MIR
   ↓
Direct Effect Extraction
   ↓
Call Graph Propagation
   ↓
Effect Fixed Point
   ↓
Effect Legality
   ↓
Verified MIR
```

---

# 93. Effect legality

Verifier kiểm tra:

```text
@kernel
    no forbidden OS effects

comptime
    no forbidden runtime effects

@constant_time
    no timing-sensitive forbidden effects

async
    blocking policy

freestanding
    no unavailable runtime effects

signal handler
    restricted effect set
```

---

# 94. Constant-time

`@constant_time` cần effect information để cấm:

- uncontrolled IO;
- allocation nếu policy cấm;
- secret-dependent external behavior;
- secret-dependent branches theo contract;
- variable-time operations không được phép.

Effect system không tự chứng minh constant-time, nhưng cung cấp dependency graph.

---

# 95. Signal handler

Signal context có effect restrictions nghiêm ngặt.

Compiler có thể yêu cầu:

```text
SignalSafeEffects
```

thay vì cho phép arbitrary function.

---

# 96. Freestanding

Freestanding profile:

```text
Allowed:
    Memory
    Atomic
    Volatile
    Platform-specific

Forbidden:
    FileSystem
    Network
    Process
    Hosted runtime
```

trừ khi explicit system layer.

---

# 97. Effect profiles

Axiom có predefined semantic profiles:

```text
Hosted
Freestanding
Kernel
GPU
Comptime
ConstantTime
Signal
Interrupt
```

Mỗi profile định nghĩa effect legality.

---

# 98. Effect inference không thay thế verifier

Nếu compiler nói:

```text
foo = Pure
```

nhưng MIR thực tế có:

```text
IO
```

đó là compiler bug.

Effect summary phải được kiểm tra từ verified IR.

---

# 99. Effect summary cache

Function artifact có thể lưu:

```text
EffectFingerprint
```

để incremental compilation.

Nếu body không thay đổi semantic effects:

```text
dependent modules
```

không nhất thiết phải recompile toàn bộ.

---

# 100. Public API effect compatibility

Nếu một stable ABI function trước đây:

```text
NoExternalState
```

sau update thành:

```text
Network
```

thì đây có thể là semantic/API compatibility change.

Do đó `SemanticFingerprint` phải bao gồm relevant effect contract.

---

# 101. Nhưng inferred internal effects không nhất thiết public ABI

Một function nội bộ có thể thay đổi:

```text
Allocate
```

thành:

```text
Stack
```

mà không làm API incompatible nếu observable semantics không đổi.

---

# 102. Effect summary vs optimization fingerprint

Tách:

```text
SemanticEffectFingerprint
```

và:

```text
ImplementationEffectFingerprint
```

Implementation fingerprint có thể thay đổi liên tục.

---

# 103. AI diagnostics

Ví dụ:

```text
ax explain effect foo
```

trả:

```text
Function: foo

Effects:
    Memory.Read
    Memory.Write
    FileSystem.Read

Derived from:
    load_data()
        → File.read()

No effects:
    Network
    Process
    Random
    Time

May panic:
    yes

May block:
    yes

May suspend:
    no
```

---

# 104. Đây là một lợi thế lớn cho AI agent

AI không phải đoán:

> “Hàm này có thể mở file không?”

Compiler trả trực tiếp semantic facts.

---

# 105. Effect-aware documentation

`ax doc` có thể tự sinh:

```text
Effects
-------
Reads memory
Writes memory
Reads filesystem
May panic
May block
```

Không cần programmer duy trì annotation thủ công.

---

# 106. Effect-aware optimizer

Ví dụ:

```text
Function A:
    Pure

Function B:
    Memory.Read(X)

Function C:
    IO

Function D:
    Network
```

Optimizer biết mức độ freedom:

```text
A ↔ A
B ↔ independent memory
C → external barrier
D → external barrier
```

---

# 107. Effect and LTO

LTO có thể inline:

```text
A → B → C
```

sau đó recompute effects.

Ví dụ:

```text
C = pure
B = pure
A = pure
```

có thể aggressive optimize.

Nếu C là FFI unknown:

```text
A = ConservativeForeign
```

---

# 108. Effect and devirtualization

Dynamic call:

```text
obj.write()
```

ban đầu:

```text
UnknownEffects
```

Nếu devirtualize được:

```text
ConcreteWriter.write()
```

→ effect summary chính xác hơn.

---

# 109. Effect and specialization

Generic:

```text
fn process<T: Writer>(...)
```

có thể có effect phụ thuộc T.

Monomorphized:

```text
process<MemoryWriter>
```

→ Memory effects.

```text
process<FileWriter>
```

→ FileSystem/IO.

---

# 110. Effect and zero-cost abstraction

Đây là một mục tiêu lớn:

```text
High-level generic abstraction
          ↓
Effect inference
          ↓
Specialization
          ↓
No unnecessary runtime abstraction
```

---

# 111. Không cần effect annotation trong 95% code

Programmer viết:

```axiom
fn load_user(id: UserId) -> Result<User, Error> {
    let file = open(...)
    return decode(file.read(...))
}
```

Compiler tự biết:

```text
FileSystem
IO
Allocate
Panic? depending on implementation
```

---

# 112. Explicit annotation chỉ dành cho boundary

Ví dụ:

```text
@effect(requires = ...)
@effect(forbids = ...)
@effect(assumes = ...)
```

không phải Core syntax bắt buộc.

Chỉ system/compiler API cần.

---

# 113. Không cho programmer giả mạo effect

Sai:

```text
@pure
fn evil() {
    write_file(...)
}
```

Compiler phải reject.

Annotation là **constraint/contract**, không phải lời nói dối được tin mù quáng.

---

# 114. Trusted intrinsic

Một số compiler intrinsic có effect semantics do compiler định nghĩa.

Ví dụ:

```text
intrinsic atomic_load
intrinsic volatile_write
intrinsic stack_alloc
```

Không phải arbitrary user-defined trusted effects.

---

# 115. Effect inference correctness

Invariant:

```text
ActualEffects(MIR)
    ⊆
Declared/AllowedEffects
```

Nếu function không có declared effect contract:

```text
Summary = ActualEffects
```

---

# 116. Effect monotonicity

Nếu thêm một call:

```text
foo()
```

với effect `E`, summary không được tự nhiên mất `E` trừ khi optimization chứng minh operation không observable và loại nó.

---

# 117. Semantic vs optimized effect

Trước optimization:

```text
foo:
    Allocate
    Deallocate
```

Sau optimization:

```text
foo:
    none
```

Điều này hợp lệ nếu allocation/deallocation không observable.

Do đó effect analysis chạy cả:

```text
pre-optimization
post-optimization
```

nhưng hai summaries có ý nghĩa khác nhau.

---

# 118. Effect-preserving optimization

Mọi optimization phải chứng minh:

```text
ObservableEffects_before
≡
ObservableEffects_after
```

không nhất thiết:

```text
InstructionEffects_before
==
InstructionEffects_after
```

---

# 119. External observability

Các effect chắc chắn observable:

```text
IO
Volatile
Foreign unknown
Process
Network
FileSystem
Synchronization
Atomic semantics
GPU submission/completion
```

tùy contract.

---

# 120. Effect elimination

Một effect có thể bị eliminate nếu compiler chứng minh:

```text
not observable
```

Ví dụ allocation không escape.

---

# 121. Effect ordering invariant

Nếu hai effects có dependency:

```text
E1 → E2
```

optimizer không được đổi:

```text
E2 → E1
```

nếu observable semantics thay đổi.

---

# 122. Memory effect + capability

Một điểm rất quan trọng:

```text
Capability verifier
        ↓
Region
        ↓
Effect verifier
        ↓
MemoryEffect(region)
        ↓
Alias analysis
```

Hai hệ thống **không tách rời**.

---

# 123. Ví dụ hoàn chỉnh

```axiom
fn add(a: mut_view<i32>, b: view<i32>) {
    *a = *a + *b
}
```

Compiler semantic facts:

```text
a:
    WRITE region A

b:
    READ region B
```

Nếu caller chứng minh:

```text
A DISJOINT B
```

thì:

```text
Effect:
    Read(B)
    Write(A)

Alias:
    NO_ALIAS(A,B)
```

Optimizer có thể tận dụng.

---

# 124. Nếu caller truyền cùng region

```text
add(x, x)
```

Compiler phải xem:

```text
A = B
```

→ READ + WRITE conflict.

Nếu API contract yêu cầu disjoint:

```text
compile error
```

---

# 125. Đây là cách Axiom có thể mạnh hơn C

C:

```c
void add(int *restrict a, const int *restrict b);
```

Programmer phải cung cấp `restrict`.

Axiom:

```axiom
fn add(a: mut_view<i32>, b: view<i32>)
```

compiler có thể tự chứng minh:

```text
NO_ALIAS
```

từ call-site provenance/regions.

---

# 126. Nhưng không hứa compiler luôn chứng minh được

Nếu:

```text
a = runtime_pointer(...)
b = runtime_pointer(...)
```

và relation unknown:

```text
UNKNOWN
```

compiler không được đoán.

Có thể:

- reject API yêu cầu disjoint;
- dùng API runtime-check;
- dùng sequential algorithm;
- dùng unsafe/system contract.

---

# 127. Effect system và memory model đã thống nhất

Sau 226–228:

```text
Ownership
    ↓
Capability
    ↓
Effect
    ↓
Verified MIR
    ↓
Alias / MemorySSA / Optimization
```

Đây đang trở thành **semantic kernel thực sự** của Axiom.

---

# 128. Frozen invariants

```text
AEFFECT-20
Effects are compiler-inferred by default.

AEFFECT-21
Programmers are not required to annotate ordinary function effects.

AEFFECT-22
Effect inference is deterministic.

AEFFECT-23
Function effects are transitively inferred through calls.

AEFFECT-24
Recursive effect inference uses a deterministic fixed-point algorithm.

AEFFECT-25
Unknown foreign calls receive conservative effect summaries unless an explicit verified contract exists.

AEFFECT-26
Unsafe does not erase effect tracking.

AEFFECT-27
Volatile operations are observable effects.

AEFFECT-28
Atomic operations carry atomic and ordering effects.

AEFFECT-29
Synchronization operations carry synchronization effects.

AEFFECT-30
Blocking and async suspension are distinct effects.

AEFFECT-31
Recoverable Result/Option failure is not itself an exception effect.

AEFFECT-32
Panic is a distinct control effect.

AEFFECT-33
Unwind is distinct from panic semantics.

AEFFECT-34
External state effects are not assumed pure.

AEFFECT-35
Time and randomness are external effects unless explicitly deterministic by contract.

AEFFECT-36
Environment access is an external effect.

AEFFECT-37
Filesystem and network operations are observable external effects.

AEFFECT-38
Process operations are observable external effects.

AEFFECT-39
FFI effects require explicit contracts or conservative inference.

AEFFECT-40
Comptime effects are tracked separately from runtime effects.

AEFFECT-41
Comptime external inputs participate in build identity.

AEFFECT-42
GPU kernels may not perform effects forbidden by their execution profile.

AEFFECT-43
GPU memory effects remain explicit by storage domain.

AEFFECT-44
Effect legality is checked before code generation.

AEFFECT-45
Effect information is available to optimization.

AEFFECT-46
Memory effects carry region information where available.

AEFFECT-47
Capability proofs may refine memory effect alias information.

AEFFECT-48
UNKNOWN aliasing is never silently converted to NO_ALIAS.

AEFFECT-49
Observable effects cannot be eliminated by ordinary dead-code elimination.

AEFFECT-50
Non-observable implementation effects may be eliminated.

AEFFECT-51
Allocation effects may disappear after proven allocation elimination.

AEFFECT-52
Effect-preserving optimization preserves observable behavior, not physical instruction effects.

AEFFECT-53
Effect ordering is preserved whenever observable semantics require it.

AEFFECT-54
Pure computations may be reordered when dependencies permit.

AEFFECT-55
Effect summaries are separate from physical implementation details.

AEFFECT-56
Optimization level cannot change semantic effect legality.

AEFFECT-57
Effect summaries participate in incremental compilation fingerprints where semantically relevant.

AEFFECT-58
Stable public contracts may constrain effect evolution.

AEFFECT-59
Dynamic dispatch conservatively represents unknown implementation effects.

AEFFECT-60
Devirtualization may refine effect information.

AEFFECT-61
Generic specialization may refine effect information.

AEFFECT-62
Effect facts are explainable through CompilerDB and AXCP.

AEFFECT-63
AI-generated code is subject to the same effect verifier.

AEFFECT-64
Generated comptime declarations cannot bypass effect verification.

AEFFECT-65
Effect metadata is not a mandatory runtime data structure.

AEFFECT-66
Effect inference must not introduce runtime overhead by itself.

AEFFECT-67
Effect contracts cannot falsely suppress compiler-visible effects.

AEFFECT-68
Trusted compiler intrinsics have compiler-defined effect semantics.

AEFFECT-69
Effect summaries compose with ownership, capability, concurrency and execution-domain verification.

AEFFECT-70
The semantic effect system is part of the correctness boundary before optimization.
```

---

# 129. Kiến trúc Axiom lúc này

Có thể xem semantic kernel đã có 4 câu hỏi:

```text
             AXIOM SEMANTIC KERNEL

     ┌───────────────┐
     │  OWNERSHIP    │
     │ "Ai sở hữu?"  │
     └───────┬───────┘
             │
             ▼
     ┌───────────────┐
     │  CAPABILITY   │
     │ "Ai truy cập?"│
     └───────┬───────┘
             │
             ▼
     ┌───────────────┐
     │    EFFECT     │
     │ "Làm gì?"     │
     └───────┬───────┘
             │
             ▼
     ┌───────────────┐
     │ CONCURRENCY   │
     │ "Khi nào?"    │
     └───────────────┘
```

Trong đó concurrency sẽ dùng cả ba tầng trước.

---

# BOOTSTRAP-229 — CONCURRENCY SEMANTICS & DATA-RACE VERIFIER

Task tiếp theo sẽ chốt tầng thứ tư:

> **Ownership quyết định ai có value → Capability quyết định ai truy cập → Effect quyết định hành động gì → Concurrency quyết định những hành động đó được phép xảy ra đồng thời và theo thứ tự nào.**

229 sẽ đặc biệt formalize:

- `Send`;
- `Share`;
- thread/task/fiber execution domains;
- happens-before;
- Acquire/Release/SeqCst;
- Mutex/RwLock;
- Channel;
- atomic;
- data-race verification;
- task migration;
- structured concurrency;
- parallel iteration;
- GPU synchronization;
- interaction với `view/mut_view`;
- interaction với async/await;
- compiler-generated `NO_DATA_RACE` và synchronization facts;
- cách compiler có thể dùng các proof này cho parallelization và optimization.