# BOOTSTRAP-340 — AXIOM DYNAMIC SANITIZER, RUNTIME VERIFICATION & MEMORY-SAFETY INSTRUMENTATION ENGINE

Sau 339, Axiom đã có chuỗi:

```text
Source
 → Compiler
 → Native Binary
 → Verify
 → Sign
 → Deploy
 → Run
 → Profile
```

Nhưng profiling chỉ trả lời **“chương trình đang làm gì?”**.

Bước tiếp theo cần trả lời:

> **“Nếu chương trình có bug ở vùng mà compiler không thể chứng minh được — đặc biệt unsafe, FFI, raw pointer, GPU, concurrency — làm thế nào phát hiện nó ở runtime?”**

Axiom không nên biến toàn bộ chương trình thành một runtime-checked language. Thay vào đó, xây **sanitizer/instrumentation framework tùy chọn**, compiler-aware và có thể tắt hoàn toàn trong production.

---

# 1. Nguyên tắc nền tảng

Sanitizer không phải semantics mới.

```text
Normal build:
Source → Verified MIR → Optimized → Native

Sanitized build:
Source → Verified MIR
       → Instrumentation
       → Optimized
       → Native + checks
```

Instrumentation chỉ được phép:

- phát hiện lỗi;
- ghi telemetry;
- terminate;
- tạo diagnostic.

Nó không được làm thay đổi semantics của chương trình hợp lệ.

---

# 2. Vì sao Axiom cần sanitizer riêng?

Axiom compiler đã biết:

```text
Ownership
Capability
Region
Lifetime
Escape
Send
Share
FFI
Unsafe
GPU
```

Vì vậy sanitizer có thể tận dụng **semantic information mà C/C++ sanitizer thông thường không có**.

Ví dụ compiler biết:

```text
view<T>
owner
RegionId
CapabilityId
```

thì runtime checker có thể báo:

```text
view escaped owner lifetime
```

thay vì chỉ báo:

```text
invalid memory access
```

---

# 3. Sanitizer không thay thế verifier

Pipeline:

```text
Source
 ↓
Semantic Verification
 ↓
Verified MIR
 ↓
Sanitizer Instrumentation
 ↓
Optimization
 ↓
Machine Code
```

Không được:

```text
unsafe → sanitizer → coi như safe
```

`unsafe` vẫn phải thỏa contract.

---

# 4. Sanitizer profiles

Axiom định nghĩa:

```text
SanitizerProfile {
    Memory
    Bounds
    Ownership
    Capability
    Concurrency
    Integer
    Initialization
    FFI
    Async
    GPU
    ControlFlow
}
```

Có thể bật từng nhóm.

Ví dụ:

```text
axiom build --sanitize=memory,bounds
```

---

# 5. Zero-cost production

Production:

```text
--sanitize=none
```

thì sanitizer instrumentation phải bị loại bỏ hoàn toàn nếu không có semantic reason để giữ lại.

Không được có:

```text
hidden sanitizer runtime
```

trong binary thông thường.

---

# 6. Memory sanitizer

Phát hiện:

```text
use-after-free
double-free
invalid-free
out-of-bounds
use-of-uninitialized
invalid-alignment
```

Nhưng Axiom tận dụng ownership state để tạo diagnostic giàu ngữ nghĩa.

---

# 7. Allocation identity

Mỗi instrumented allocation có:

```text
AllocationId
Generation
Base
Size
Alignment
State
```

State:

```text
Allocated
Freed
Quarantined
```

---

# 8. Use-after-free

Nếu:

```text
owner
 ↓
view
```

owner bị drop nhưng view vẫn được sử dụng trong một đường mà verifier không chứng minh được do unsafe boundary:

runtime có thể phát hiện:

```text
AXSAN-OWN-001

Capability used after owner lifetime.

Owner:
    Buffer#17

Capability:
    View#42

Created at:
    foo.ax:81

Invalidated at:
    bar.ax:129
```

---

# 9. Red zones

Allocator sanitizer có thể đặt:

```text
[ red zone ][ object ][ red zone ]
```

để phát hiện overwrite.

Chỉ áp dụng sanitized allocation.

---

# 10. Quarantine

Sau free:

```text
object
 ↓
quarantine
```

không tái sử dụng ngay.

Điều này tăng khả năng bắt use-after-free.

---

# 11. Bounds sanitizer

Kiểm tra:

```text
array[i]
view[i]
slice[i]
```

khi compiler không thể chứng minh an toàn.

Nhưng nếu compiler đã chứng minh:

```text
0 <= i < len
```

thì instrumentation phải bị loại bỏ.

---

# 12. Bounds-check elimination

Đây là điểm quan trọng.

Ví dụ:

```text
for i in 0..n {
    a[i] = ...
}
```

Nếu MIR proof chứng minh:

```text
i < a.length
```

thì sanitizer không cần thêm runtime check.

Do đó sanitizer có thể trở thành:

```text
compiler proof + runtime fallback
```

thay vì check mù quáng.

---

# 13. Initialization sanitizer

MIR đã có:

```text
UNINIT
INIT
MOVED
DROPPED
```

Instrumentation chỉ cần thêm runtime tracking ở những boundary compiler không chứng minh được.

Ví dụ FFI:

```text
foreign → Axiom
```

nếu contract không đảm bảo initialization.

---

# 14. Partial initialization

Struct:

```text
struct Foo {
    a: i32,
    b: Buffer,
    c: String
}
```

runtime debug metadata có thể biết:

```text
a = INIT
b = INIT
c = UNINIT
```

Không chỉ một bit:

```text
Foo = invalid
```

---

# 15. Integer sanitizer

Axiom đã có semantics rõ ràng cho:

```text
checked
wrapping
saturating
```

Do đó sanitizer **không được báo lỗi cho overflow hợp lệ**.

Chỉ instrument những operation yêu cầu:

```text
checked arithmetic
```

hoặc policy đặc biệt.

---

# 16. Shift sanitizer

Có thể phát hiện:

```text
shift >= bit_width
```

nếu operation contract yêu cầu valid range.

---

# 17. Division sanitizer

Phát hiện:

```text
division by zero
```

và các trường hợp đặc biệt target-dependent.

Compiler loại bỏ check nếu divisor đã được chứng minh khác zero.

---

# 18. Pointer sanitizer

Raw pointer chỉ xuất hiện ở:

```text
unsafe
FFI
system
```

Do đó Axiom có thể instrument:

```text
pointer provenance
alignment
bounds
lifetime
```

---

# 19. Pointer provenance

Một integer:

```text
u64 address
```

không tự động trở thành valid pointer.

Sanitizer phải duy trì:

```text
PointerProvenanceId
AllocationId
Region
Bounds
```

nếu instrumented.

---

# 20. Integer-to-pointer

Nếu unsafe code làm:

```text
address → pointer
```

sanitizer có thể kiểm tra:

```text
address belongs to valid mapped region
alignment valid
access within region
```

Nhưng không được biến sanitizer thành guarantee cho arbitrary hardware access.

---

# 21. Hardware/MMIO

Các vùng:

```text
MMIO
device memory
volatile memory
```

phải có storage classification:

```text
External
Device
Volatile
```

Sanitizer không được áp dụng ordinary heap assumptions một cách sai lệch.

---

# 22. FFI sanitizer

FFI là boundary nguy hiểm nhất.

Runtime có thể kiểm tra:

```text
nullability
alignment
length
ownership
allocator
```

nếu contract có đủ metadata.

Ví dụ:

```text
extern fn read(
    buffer: *mut u8,
    len: usize
)
```

adapter có thể kiểm tra:

```text
buffer != null
buffer aligned
buffer range valid
```

---

# 23. FFI allocator checking

Nếu foreign function trả:

```text
ForeignOwned
```

Axiom không được tự động:

```text
free()
```

Sanitizer theo dõi allocator domain:

```text
AxiomAllocator
ForeignAllocator
OSAllocator
CustomAllocator
```

---

# 24. FFI callback sanitizer

Callback:

```text
C → Axiom
```

runtime kiểm tra callback state:

```text
Registered
Active
Unregistered
```

Có thể phát hiện callback sau unregister.

---

# 25. Ownership sanitizer

Axiom compiler thường bắt được ownership lỗi.

Tuy nhiên unsafe/FFI/component boundary có thể phá vỡ static proof.

Runtime metadata có:

```text
OwnershipToken
Generation
OwnerId
```

---

# 26. Capability sanitizer

Với:

```text
view<T>
mut_view<T>
```

runtime debug mode có thể theo dõi:

```text
CapabilityId
RegionId
AccessMode
OwnerId
Validity
```

Ví dụ phát hiện:

```text
mut_view used after owner relocation
```

---

# 27. Dynamic relocation checking

Nếu `Vec` relocate:

```text
old storage
   ↓
new storage
```

mọi active capability liên quan phải invalid hoặc được cập nhật theo semantic contract.

Sanitizer có thể xác nhận compiler assumption.

---

# 28. Concurrency sanitizer

Axiom có memory model rõ ràng.

Sanitizer cần hỗ trợ:

```text
data race
lock misuse
atomic misuse
deadlock diagnostics
channel misuse
```

---

# 29. Happens-before instrumentation

Runtime có thể ghi:

```text
Thread A
  release atomic
       ↓
Thread B
  acquire atomic
```

và xây:

```text
HappensBeforeGraph
```

---

# 30. Data-race detection

Nếu ordinary memory:

```text
Thread A → WRITE
Thread B → READ
```

mà không có happens-before:

```text
DATA RACE
```

Runtime báo:

```text
AXSAN-RACE-001
```

kèm:

```text
write location
read location
thread A
thread B
creation stack
synchronization history
```

---

# 31. Capability-aware race detection

Axiom có lợi thế:

```text
mut_view
```

và ownership.

Runtime sanitizer có thể hiển thị:

```text
Region R17
Writer:
    Task#4

Reader:
    Task#9

Synchronization:
    NONE
```

---

# 32. Atomic sanitizer

Phải phân biệt:

```text
ordinary memory
atomic memory
volatile memory
```

Không báo data race cho hai atomic operations chỉ vì chúng cùng địa chỉ.

---

# 33. Memory ordering validation

Instrumentation có thể ghi:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

giúp debug ordering bugs.

Không thay đổi semantics.

---

# 34. Lock sanitizer

Theo dõi:

```text
MutexId
OwnerThread
RecursionState
Waiters
```

Phát hiện:

```text
unlock without ownership
double unlock
invalid guard
```

---

# 35. Lock-order graph

Runtime có thể xây:

```text
Lock A → Lock B
Lock B → Lock C
Lock C → Lock A
```

và cảnh báo:

```text
potential deadlock cycle
```

Đây là diagnostic heuristic, không phải semantic proof.

---

# 36. Async sanitizer

Theo dõi:

```text
FutureId
TaskId
SuspensionPointId
WakerId
ExecutorId
```

---

# 37. Async misuse

Có thể phát hiện:

```text
Future polled after completion
Future polled concurrently
invalid waker usage
task cancellation misuse
```

---

# 38. Await lifetime verification

Compiler đã kiểm tra live-across-await.

Sanitizer có thể kiểm tra debug build:

```text
view
 ↓
await
 ↓
resume
```

và xác nhận capability vẫn hợp lệ.

---

# 39. Executor diagnostics

Runtime ghi:

```text
Task A
created:
    foo.ax:42

spawned:
    bar.ax:71

await:
    baz.ax:91
```

Từ đó debugger có logical async stack.

---

# 40. GPU sanitizer

GPU code cần sanitizer riêng.

Ví dụ:

```text
@kernel
fn add(...)
```

có thể kiểm tra:

```text
index bounds
address space
shared memory
barrier usage
race
```

---

# 41. GPU bounds

Nếu kernel:

```text
out[i] = a[i] + b[i]
```

sanitizer kiểm tra:

```text
i < a.length
i < b.length
i < out.length
```

nếu compiler chưa chứng minh được.

---

# 42. GPU race sanitizer

Có thể instrument:

```text
thread A → write X
thread B → write X
```

nếu không có synchronization.

Target-specific implementation.

---

# 43. GPU barrier checking

Có thể phát hiện:

```text
barrier divergence
```

nếu GPU backend có đủ semantic metadata.

---

# 44. Control-flow sanitizer

Sanitized build có thể kiểm tra:

```text
indirect call target
return address
function pointer
vtable/dynamic dispatch target
```

---

# 45. CFI

Compiler có thể phát hành:

```text
CFI type ID
```

cho indirect-call sites.

Runtime kiểm tra:

```text
actual target
compatible signature/type
```

---

# 46. Shadow stack

Target hỗ trợ:

```text
CET
Shadow Stack
PAC
```

thì Axiom backend có thể sử dụng.

Không đưa các tính năng này vào Core semantics.

---

# 47. Stack overflow

Sanitized/debug runtime có thể:

```text
guard page
stack limit
stack probe
```

để phát hiện overflow.

Compiler có thể phát hành stack metadata.

---

# 48. Stack-use-after-return

Nếu target/runtime hỗ trợ, sanitizer có thể quarantine stack frames hoặc dùng shadow storage.

Đây là debug-only cost.

---

# 49. Leak detection

Leak sanitizer:

```text
AllocationId
creation site
reachable roots
```

sau program termination báo:

```text
Leaked:
  14 allocations
  4.2 MB
```

---

# 50. Nhưng Axiom không mặc định coi leak là bug

Ví dụ:

```text
freestanding program
static lifetime allocations
OS reclaim
arena lifetime
```

có thể hợp lệ.

Do đó leak detector là policy/tooling, không phải language semantics.

---

# 51. Resource leak detection

Ngoài memory:

```text
File
Socket
Mutex
GPUBuffer
Process
DeviceHandle
```

có thể tracking.

---

# 52. Resource lifecycle graph

Ví dụ:

```text
File#17
Created
 → Open
 → Used
 → Closed
```

Nếu program terminate:

```text
Open
```

sanitizer có thể báo.

---

# 53. Panic/unwind sanitizer

Theo dõi:

```text
panic
unwind
drop
```

để phát hiện:

```text
double drop
drop-after-move
invalid cleanup
```

---

# 54. Drop instrumentation

Mỗi Drop-bearing object có debug identity:

```text
ObjectId
TypeId
CreationSite
DropSite
```

Nếu compiler proof đủ mạnh thì production không cần metadata.

---

# 55. Component sanitizer

325 + 339 cho phép tracking:

```text
ComponentGeneration
ComponentLease
Callback
Future
Thread
GPU work
```

Sanitizer phát hiện unload khi còn dependency.

---

# 56. Dynamic library sanitizer

Theo dõi:

```text
LoadedLibrary
Symbol
Generation
Reference
```

phát hiện:

```text
call into unloaded library
```

---

# 57. Sanitizer runtime architecture

Không có một runtime khổng lồ.

```text
sanitizer/
├── core
├── memory
├── bounds
├── ownership
├── capability
├── race
├── lock
├── async
├── ffi
├── gpu
├── cfi
└── leak
```

Chỉ module được chọn mới được link.

---

# 58. Compiler instrumentation IR

Không instrument trực tiếp machine code nếu có thể tránh.

Thêm MIR operations:

```text
SANITIZE_CHECK
SANITIZE_ENTER
SANITIZE_EXIT
SANITIZE_ALLOC
SANITIZE_FREE
SANITIZE_READ
SANITIZE_WRITE
SANITIZE_SYNC
```

Sau đó lowering tùy target.

---

# 59. Optimization interaction

Pipeline:

```text
Verified MIR
 ↓
Sanitizer IR
 ↓
Optimization
 ↓
Remove redundant checks
 ↓
Machine code
```

Compiler có thể loại bỏ check đã được proof.

---

# 60. Check hoisting

Ví dụ:

```text
for i in 0..n
    check(i < n)
```

Compiler có thể biến:

```text
check(n valid)
for ...
```

nếu semantics cho phép.

---

# 61. Check fusion

Hai check:

```text
i < a.len
i < b.len
```

có thể được hợp nhất nếu proof cho phép.

---

# 62. Sanitizer metadata

Mỗi check có:

```text
SanitizerCheckId
Kind
SourceSpan
MIRLocation
Condition
FailurePolicy
```

---

# 63. Failure policies

```text
Abort
Trap
Panic
ReportAndAbort
DebuggerBreak
Continue
```

`Continue` chỉ hợp lệ với checker mà semantics cho phép.

---

# 64. Diagnostic payload

Một sanitizer failure phải có:

```text
SanitizerError {
    code
    message
    source
    stack
    async_stack
    thread
    task
    allocation
    capability
    provenance
}
```

---

# 65. Symbolication

Sanitizer crash phải kết hợp 337:

```text
PC
 ↓
Symbolication
 ↓
Source
 ↓
MIR
 ↓
Semantic object
```

---

# 66. Profile integration

Sanitizer có thể dùng 338:

```text
hot allocation
hot bounds check
hot race site
```

để tối ưu instrumentation.

Nhưng profile không được làm sanitizer bỏ qua correctness checks.

---

# 67. Debugger integration

313 + 337:

```text
break on sanitizer error
inspect object
inspect ownership
inspect capability
inspect thread
inspect async task
```

---

# 68. Fuzzing integration

Sanitizer engine phải cung cấp API:

```text
run_with_sanitizers()
report_failure()
reset_runtime_state()
```

để fuzzing engine sử dụng.

---

# 69. Fuzzing target

Compiler có thể tạo:

```text
@fuzz
fn parse(input: view<u8>) -> Result<...>
```

nhưng fuzzing framework vẫn là library/tooling, không phải Core.

---

# 70. Sanitizer corpus

Có thể lưu:

```text
input
target
compiler
sanitizer_profile
failure_signature
```

để regression testing.

---

# 71. Failure signature

Không dùng stack trace raw làm identity duy nhất.

Signature:

```text
SanitizerKind
FunctionId
MIRLocation
SourceSpan
ErrorClass
```

giúp deduplicate crash.

---

# 72. Production diagnostics

Một số checks có thể chạy production với overhead thấp:

```text
CFI
shadow stack
bounds hardening
stack protection
```

Nhưng phải phân biệt:

```text
Sanitizer Debug
Sanitizer Release
Security Hardening
```

---

# 73. Security hardening ≠ sanitizer

Ví dụ:

```text
stack protector
CFI
PAC
ASLR
W^X
```

là hardening.

Còn:

```text
ASAN-like checks
race detector
leak detector
```

là diagnostic instrumentation.

Có thể dùng chung infrastructure nhưng policy khác nhau.

---

# 74. Sanitizer profiles

Đề xuất:

```text
debug-safe
    memory
    bounds
    ownership
    initialization

concurrency
    race
    lock
    atomic

interop
    ffi
    pointer
    allocator

async
    future
    task
    waker

gpu
    bounds
    race
    barrier

security
    cfi
    shadow-stack
```

---

# 75. Command line

```text
axiom sanitize list

axiom build --sanitize=memory
axiom build --sanitize=memory,bounds
axiom build --sanitize=concurrency
axiom build --sanitize=ffi
axiom build --sanitize=async
axiom build --sanitize=gpu
axiom build --sanitize=all

axiom sanitize report
axiom sanitize suppress
axiom sanitize explain
```

---

# 76. Suppression

Một số external library có false positives hoặc behavior ngoài model.

Hỗ trợ:

```text
SanitizerSuppression {
    module
    function
    source
    sanitizer
    reason
}
```

Suppression phải explicit và được ghi lại trong build provenance.

---

# 77. Không cho suppression phá compiler proof

Suppression chỉ có nghĩa:

```text
don't report this runtime diagnostic
```

Không có nghĩa:

```text
compiler assumes this code is safe
```

---

# 78. Runtime API

```text
sanitizer.enable()
sanitizer.disable()
sanitizer.report()
sanitizer.break_on_error()
sanitizer.current_context()
```

Chỉ available khi sanitizer profile được link.

---

# 79. Compiler DB

Bổ sung:

```text
SanitizerDB
SanitizerProfileDB
SanitizerInstrumentationDB
SanitizerMetadataDB
SanitizerRuntimeDB
SanitizerMappingDB
SanitizerSuppressionDB
SanitizerFailureDB
SanitizerFuzzDB
```

---

# 80. Implementation tree

```text
compiler/
└── sanitizer/
    ├── model/
    ├── profiles/
    ├── instrumentation/
    ├── memory/
    ├── bounds/
    ├── initialization/
    ├── ownership/
    ├── capability/
    ├── pointer/
    ├── ffi/
    ├── concurrency/
    ├── race/
    ├── atomic/
    ├── lock/
    ├── async/
    ├── gpu/
    ├── cfi/
    ├── leak/
    ├── resource/
    ├── runtime/
    ├── symbolication/
    ├── debugger/
    ├── fuzzing/
    └── diagnostics/
```

---

# 81. Invariants

```text
ASAN-01
Sanitizer instrumentation must not redefine language semantics.

ASAN-02
Sanitizers are optional.

ASAN-03
A normal unsanitized build must not require sanitizer runtime support.

ASAN-04
Sanitizers must never replace static semantic verification.

ASAN-05
Unsafe code remains unsafe even when sanitizer instrumentation is enabled.

ASAN-06
Compiler-proven checks should be removable when their runtime condition is redundant.

ASAN-07
Sanitizer instrumentation must preserve source and MIR provenance.

ASAN-08
Memory sanitizer must distinguish allocation identity and generation.

ASAN-09
Bounds sanitizer must respect proven bounds.

ASAN-10
Initialization sanitizer must distinguish partial initialization.

ASAN-11
Ownership sanitizer must understand Move/Copy/Drop semantics.

ASAN-12
Capability sanitizer must distinguish view and mut_view.

ASAN-13
Pointer sanitizer must preserve provenance semantics.

ASAN-14
FFI sanitizer must respect allocator and ownership domains.

ASAN-15
Concurrency sanitizer must respect the Axiom memory model.

ASAN-16
Atomic operations must not be reported as ordinary data races.

ASAN-17
Async sanitizer must distinguish polling, suspension and execution.

ASAN-18
GPU sanitizer must understand GPU address spaces and synchronization.

ASAN-19
Component sanitizer must track component generation lifetime.

ASAN-20
Suppression must never create a compiler safety proof.

ASAN-21
Sanitizer failures must be symbolicated through the debug infrastructure.

ASAN-22
Sanitizer metadata must be removable from production binaries when not required.

ASAN-23
Sanitizer runtime components must be independently linkable.

ASAN-24
Sanitizer diagnostics must be machine-readable.

ASAN-25
Sanitizer instrumentation must remain compatible with optimization unless explicitly using a diagnostic-only transformation.

ASAN-26
Profile data must never cause sanitizer correctness checks to be removed.

ASAN-27
Sanitizer behavior must be target-aware.

ASAN-28
Sanitizer diagnostics must distinguish proven compiler errors from runtime-detected contract violations.

ASAN-29
Sanitizer configuration must be part of build identity.

ASAN-30
A sanitized binary must retain enough metadata to explain each reported failure.
```

---

# 82. Definition of Done

BOOTSTRAP-340 hoàn thành khi Axiom có:

- memory sanitizer;
- bounds sanitizer;
- initialization sanitizer;
- ownership sanitizer;
- capability sanitizer;
- raw-pointer/provenance sanitizer;
- FFI sanitizer;
- allocator-domain sanitizer;
- data-race detector;
- atomic instrumentation;
- lock sanitizer;
- channel diagnostics;
- async sanitizer;
- Future/waker validation;
- GPU bounds sanitizer;
- GPU race sanitizer;
- GPU synchronization diagnostics;
- CFI instrumentation;
- stack protection integration;
- leak detector;
- resource lifetime detector;
- component-generation checking;
- sanitizer-aware MIR;
- redundant-check elimination;
- sanitizer metadata;
- sanitizer runtime modules;
- suppression system;
- symbolication integration;
- debugger integration;
- profile integration;
- fuzzing integration;
- machine-readable diagnostics;
- deterministic sanitizer mode;
- incremental-build integration;
- `.axif`/artifact metadata integration;
- sanitizer-aware build fingerprints.

## Kiến trúc quan trọng nhất của 340

Axiom sẽ có **hai tầng bảo vệ bổ sung nhau**:

```text
                 ┌──────────────────────┐
                 │ STATIC VERIFICATION  │
                 │                      │
                 │ Ownership            │
                 │ Capability           │
                 │ Lifetime             │
                 │ Send / Share         │
                 │ Effects              │
                 │ FFI contracts        │
                 └──────────┬───────────┘
                            │
                     Verified MIR
                            │
                            ▼
                 ┌──────────────────────┐
                 │ RUNTIME VERIFICATION │
                 │                      │
                 │ Memory              │
                 │ Bounds              │
                 │ Race                │
                 │ FFI                 │
                 │ Async               │
                 │ GPU                 │
                 │ CFI                 │
                 └──────────┬───────────┘
                            │
                            ▼
                       Native Code
```

Điểm khác biệt quan trọng của Axiom là **sanitizer không phải “bù lại một type system yếu”**. Compiler đã cố chứng minh mọi thứ có thể chứng minh tĩnh; runtime instrumentation chỉ xuất hiện ở những chỗ **proof không đủ mạnh hoặc boundary không thể biết trước**, đặc biệt `unsafe`, FFI, external resources và hardware.

