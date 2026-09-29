# BOOTSTRAP-313 — AXIOM DEBUGGER, PROFILER & RUNTIME INTROSPECTION INFRASTRUCTURE

Sau khi có compiler validation, self-hosting và Language Server, bước tiếp theo là xây dựng **hệ thống quan sát chương trình lúc chạy**.

Mục tiêu:

> **Axiom phải cho phép programmer và AI đi từ source → semantic state → MIR → machine code → runtime behavior → performance bottleneck mà không cần suy đoán.**

Đây không phải runtime reflection. Đây là **debug/profiling infrastructure**, chủ yếu hoạt động thông qua compiler-generated metadata và debugger protocol.

---

## 313.1. Kiến trúc tổng thể

```text
                         AXIOM SOURCE
                              │
                              ▼
                         CompilerDB
                              │
          ┌───────────────────┼───────────────────┐
          │                   │                   │
          ▼                   ▼                   ▼
       DebugInfo          ProfileInfo         TraceInfo
          │                   │                   │
          └───────────────────┼───────────────────┘
                              ▼
                       Native Executable
                              │
             ┌────────────────┼────────────────┐
             │                │                │
             ▼                ▼                ▼
         Debugger         Profiler          Tracer
             │                │                │
             └────────────────┼────────────────┘
                              ▼
                    Source / MIR / Machine
```

Ba hệ thống phải phân biệt:

```text
Debugger  = chương trình đang làm gì?
Profiler  = chương trình tốn thời gian ở đâu?
Tracer    = chương trình đã xảy ra những event gì?
```

Không gộp chúng thành một runtime subsystem khổng lồ.

---

# 313.2. Debug Information Model

Compiler tạo:

```text
DebugInfo
```

bao gồm mapping:

```text
SourceSpan
    ↓
AST/HIR
    ↓
MIR instruction
    ↓
Machine instruction
    ↓
Binary address
```

Ví dụ:

```text
source.axm:42
    ↓
FunctionId 17
    ↓
BasicBlock 8
    ↓
Instruction 91
    ↓
RIP 0x140012340
```

Mapping phải hỗ trợ cả chiều ngược:

```text
machine address
    ↓
source location
```

---

# 313.3. Debug Info không được thay đổi Semantics

Debug build không được biến:

```text
ownership
aliasing
drop
concurrency
async
ABI
```

thành semantics khác.

Debug metadata chỉ là:

```text
non-semantic metadata
```

Compiler có thể giữ thêm thông tin để debug nhưng không được thay đổi correctness.

---

# 313.4. Variable Location Model

Một biến có thể:

```text
register
stack
memory
constant
optimized away
split across locations
```

Do đó:

```text
VariableLocation
```

phải hỗ trợ:

```text
Register
StackSlot
Memory
Constant
Composite
Unavailable
```

và theo range:

```text
LocationRange {
    instruction_start
    instruction_end
    location
}
```

---

# 313.5. Optimized Debugging

Ví dụ:

```text
let x = a + b
let y = x * 2
```

optimizer có thể biến thành:

```text
y = (a + b) << 1
```

`x` có thể không tồn tại trong machine code.

Debugger phải báo:

```text
x = <optimized out>
```

thay vì tạo giá trị giả.

Nếu compiler có thể reconstruct:

```text
x = a + b
```

thì có thể cung cấp synthetic value.

Nhưng phải đánh dấu đó là:

```text
ReconstructedValue
```

không phải physical storage hiện tại.

---

# 313.6. Debugger Value Model

Debugger cần semantic value model:

```text
DebugValue {
    TypeId
    Value
    Location
    Availability
    Provenance
}
```

Hỗ trợ:

```text
primitive
struct
tuple
enum
array
view
mut_view
Option
Result
generic
closure
Future
```

---

# 313.7. Ownership-aware Debugging

Đây là một điểm đặc biệt của Axiom.

Debugger có thể hiển thị:

```text
x
Ownership:
    Owned

State:
    Initialized

Drop:
    Pending

Capabilities:
    none
```

Sau move:

```text
x
State:
    Moved
```

Nếu field-level:

```text
user.name
    Moved

user.age
    Initialized
```

Debugger không được hiển thị một moved value như thể nó còn hợp lệ.

---

# 313.8. Capability-aware Debugging

Nếu debugger đang đứng tại:

```text
foo(view)
```

có thể hiển thị:

```text
view:
    Access: READ
    Region: buffer[0..128]
    Owner: buffer
    ValidUntil: return from foo
```

Với:

```text
mut_view
```

hiển thị:

```text
Access:
    WRITE

Exclusivity:
    ACTIVE

Conflicts:
    none
```

Thông tin lấy từ compiler capability metadata.

---

# 313.9. Breakpoint Model

Hỗ trợ:

```text
source breakpoint
function breakpoint
instruction breakpoint
conditional breakpoint
watchpoint
data breakpoint
```

Source breakpoint:

```text
file.axm:42
```

có thể map tới nhiều machine locations sau optimization.

Debugger phải giữ:

```text
BreakpointLocationSet
```

thay vì giả định một source line = một instruction.

---

# 313.10. Conditional Breakpoints

Điều kiện phải được kiểm tra an toàn.

Ví dụ:

```text
break foo if x > 10
```

Debugger expression evaluator phải phân biệt:

```text
pure evaluation
```

với:

```text
side-effecting evaluation
```

Mặc định:

> Debugger expressions không được tự ý gây side effects trong target process.

---

# 313.11. Debug Expression Engine

Có thể hỗ trợ:

```text
x
x.field
array[i]
enum.variant
type_of(x)
sizeof(T)
```

và các expression read-only.

Không mặc định cho phép:

```text
foo()
x = 10
free(x)
```

vì chúng có thể phá semantic state của chương trình.

Unsafe debugger mutation phải là một mode riêng.

---

# 313.12. Stack Unwinding

Compiler phải sinh unwind metadata cho target hỗ trợ.

Stack frame:

```text
Frame {
    FunctionId
    ReturnAddress
    CFA
    Registers
    SourceLocation
}
```

Hỗ trợ:

```text
panic
exception/unwind profile
debugger break
profiler sampling
```

Nếu build:

```text
panic = abort
```

thì không cần tạo unwind machinery không cần thiết.

---

# 313.13. Panic Diagnostics

Khi chương trình panic:

```text
panic
 ↓
source location
 ↓
stack trace
 ↓
causal chain
```

Ví dụ:

```text
panic: index out of bounds

main
  → process
      → parse
          → ...
```

Stack trace phải map về source.

Không cần runtime reflection.

---

# 313.14. Async Debugging

Async function không tương đương một stack frame bình thường.

Debugger phải hiểu:

```text
Future
SuspensionPointId
StateField
Waker
ExecutorTask
```

Có thể hiển thị:

```text
Task #17

Future:
    fetch_data

State:
    Awaiting NetworkRead

Suspension Point:
    #2

Live values:
    buffer
    request_id
```

---

# 313.15. Async Stack Trace

Khi task suspend:

```text
physical stack
```

có thể không chứa logical call chain.

Debugger phải reconstruct:

```text
logical async stack
```

từ Future state metadata.

Ví dụ:

```text
main()
  └─ server()
      └─ handle_request()
          └─ fetch()
              └─ await io
```

dù physical stack hiện tại chỉ chứa executor.

---

# 313.16. Concurrency Debugging

Debugger phải biết:

```text
ThreadId
TaskId
FiberId
ExecutionDomain
```

và synchronization:

```text
Mutex
RwLock
Channel
Atomic
Semaphore
```

Có thể xem:

```text
Thread 7
    owns Mutex A

Thread 8
    waiting Mutex A
```

hoặc:

```text
Task 12
    WAITING on Channel C
```

---

# 313.17. Data Race Diagnostics

Safe Axiom code không được có data race.

Do đó nếu runtime sanitizer/debug instrumentation phát hiện violation trong:

```text
unsafe
FFI
foreign code
```

thì báo:

```text
Runtime Safety Violation
```

với:

```text
access A
access B
region
thread/task
synchronization history
```

Không biến runtime detector thành thay thế cho compile-time verifier.

---

# 313.18. Deadlock Diagnostics

Không nên tuyên bố compiler có thể phát hiện mọi deadlock.

Nhưng runtime debugger/profiler có thể phát hiện các wait graph:

```text
Thread A
   waits Lock B
       ↑
Thread B
   waits Lock A
```

và báo:

```text
Potential runtime deadlock cycle
```

Đây là **diagnostic**, không phải language semantic guarantee.

---

# 313.19. Watchpoints

Hỗ trợ:

```text
watch x
watch x.field
watch memory region
```

Nhưng với optimized code:

```text
x
```

có thể không có physical address ổn định.

Debugger phải báo:

```text
watchpoint unavailable:
    value has no stable storage location
```

thay vì phá optimization để giả lập silently.

---

# 313.20. Memory Inspection

Debugger có hai mode:

### Semantic

```text
inspect x
```

→ semantic value.

### Raw

```text
inspect memory(address)
```

→ machine bytes.

Raw mode phải được đánh dấu:

```text
UNSAFE / MACHINE VIEW
```

và không được coi raw bytes là semantic value nếu representation không hợp lệ.

---

# 313.21. Type Layout Inspection

Debugger có thể hiển thị:

```text
User
size: 32
align: 8

field a:
    offset 0
    size 8

field b:
    offset 16
    size 4
```

Thông tin lấy từ `LayoutDB`.

Nếu struct layout compiler-controlled và không stable ABI:

```text
layout stability:
    compiler-private
```

Debugger không được khiến layout trở thành language ABI contract.

---

# 313.22. Enum Debugging

Enum:

```text
Result<T, E>
```

phải hiển thị:

```text
Variant:
    Ok

Payload:
    ...
```

Niche optimization không được làm debugger phải hiểu physical representation để biết semantic variant.

Debugger dùng compiler-provided enum metadata.

---

# 313.23. Closure Debugging

Closure:

```text
|x| x + captured
```

có thể được lowered thành anonymous environment.

Debugger hiển thị:

```text
closure #42

captures:
    captured: i32 = 10

function:
    ...
```

Không bắt programmer nhìn thấy internal ABI representation.

---

# 313.24. Generic Debugging

Instance:

```text
Vec<User>
```

phải hiển thị:

```text
Generic:
    Vec<T>

Instance:
    T = User
```

và cho phép inspect:

```text
Vec<User>
    len
    capacity
    elements
```

nếu debug metadata có.

---

# 313.25. Profiling Architecture

Profiler phải có nhiều mode:

```text
Sampling
Instrumentation
Allocation
Lock contention
Async
GPU
CPU hardware counters
```

Không ép tất cả chương trình link một profiler runtime.

---

# 313.26. Sampling Profiler

Sampling:

```text
timer
 ↓
capture PC
 ↓
map PC → function/source
```

cho phép profile mà không instrumentation toàn chương trình.

Output:

```text
Function
Samples
Percent
Call tree
```

---

# 313.27. Instrumentation Profiler

Compiler có thể chèn:

```text
enter function
exit function
```

hoặc region markers.

Ví dụ:

```text
@profile
fn expensive() { ... }
```

Nhưng profiling annotation phải là tooling metadata, không thay đổi language semantics.

---

# 313.28. Allocation Profiler

Theo dõi:

```text
allocation count
allocation size
deallocation count
peak live memory
allocation site
```

Ví dụ:

```text
Vec.push
    10,000 allocations
    120 MB total
```

Có thể map allocation site về source.

---

# 313.29. Escape/Allocation Explanation

Compiler đã có `EscapeInfo`.

Profiler có thể kết hợp:

```text
compiler:
    Escape = NoEscape

runtime:
    allocation occurred
```

Nếu allocation không nên tồn tại sau optimization:

```text
Optimization regression
```

AI có thể hỏi:

```text
Why was this allocated?
```

Compiler trả:

```text
Reason:
    address escapes through foreign call
```

hoặc:

```text
Reason:
    dynamic size prevents scalar replacement
```

---

# 313.30. Lock Contention Profiler

Theo dõi:

```text
lock acquisition
wait duration
owner
contention count
```

Output:

```text
Mutex A
    acquisitions: 120k
    contention: 14k
    total wait: ...
```

Không biến profiler thành semantic requirement.

---

# 313.31. Async Profiler

Theo dõi:

```text
task creation
task execution
await
wake
poll
suspend
resume
migration
```

Có thể hiển thị:

```text
Task 42

Running: 10%
Waiting: 90%

Most frequent await:
    NetworkRead
```

---

# 313.32. Scheduler Visualization

Với deterministic/test scheduler:

```text
Task A ─────┐
            ├── CPU
Task B ─────┘
       ↓
await
       ↓
Task C
```

Có thể replay schedule.

Production scheduler không cần deterministic.

---

# 313.33. Channel Profiling

Channel metrics:

```text
send count
receive count
queue depth
max queue depth
blocked send
blocked receive
```

Cho phép phát hiện:

```text
producer faster than consumer
```

mà không cần thay đổi semantics.

---

# 313.34. GPU Profiling

GPU profile phải tách:

```text
Host
Kernel
Transfer
Synchronization
```

Ví dụ:

```text
Host → Device copy     2.1 ms
Kernel A               0.8 ms
Kernel B               0.4 ms
Device → Host copy     1.9 ms
```

Có thể hiển thị dependency:

```text
copy
 ↓
kernel A
 ↓
kernel B
 ↓
copy
```

---

# 313.35. Trace Model

Trace event:

```text
TraceEvent {
    timestamp
    thread/task
    category
    event
    source
    metadata
}
```

Categories:

```text
CPU
Thread
Task
Async
Lock
Channel
Allocation
GC            // không dùng trong Core, chỉ reserved tooling category
GPU
IO
FFI
Compiler
```

---

# 313.36. Zero-cost Disabled Profiling

Nếu profiling disabled:

```text
normal build
```

thì instrumentation phải được loại bỏ hoàn toàn khi semantics cho phép.

Không:

```text
if profiling_enabled
```

ở mọi function.

Compiler có thể DCE toàn bộ profiling hooks.

---

# 313.37. Debug Build Profiles

Ví dụ:

```text
debug
release
release-debug
profile
sanitize
```

### `debug`

- symbols;
- source mapping;
- conservative optimization nếu cần.

### `release`

- maximum optimization;
- minimal debug metadata.

### `release-debug`

- full optimization;
- debug mapping.

### `profile`

- performance instrumentation.

### `sanitize`

- additional runtime checking.

Các profile không thay đổi language semantics.

---

# 313.38. Sanitizer Architecture

Axiom có thể cung cấp:

```text
AddressSan
UndefinedBehaviorSan
ThreadSan
MemorySan
FFISan
```

nhưng phải phân biệt:

```text
compile-time safety
```

và:

```text
runtime instrumentation
```

Ví dụ safe Axiom đã ngăn use-after-free.

Sanitizer chủ yếu hữu ích cho:

- unsafe;
- FFI;
- foreign code;
- compiler bugs;
- low-level machine operations.

---

# 313.39. Machine-Level Sanitizer

Unsafe code có thể yêu cầu:

```text
@sanitize
```

để compiler chèn checks:

```text
bounds
alignment
pointer provenance
integer conversion
shift
division
```

Các checks phải có explicit cost.

Release production có thể tắt nếu contract đã được chứng minh.

---

# 313.40. Debugger ↔ CompilerDB

Debugger có thể query compiler-generated metadata:

```text
get_type_at_pc()
get_source_at_pc()
get_mir_place()
get_variable_location()
get_ownership_state()
get_capability_state()
get_async_state()
get_layout()
```

Không được load compiler source và tự phân tích lại executable.

---

# 313.41. AI Debugging API

AI agent có thể hỏi:

```text
why is this value moved?
why is this allocation happening?
why isn't this function inlined?
why is this thread blocked?
why is this task waiting?
why isn't this loop vectorized?
where did this memory come from?
```

Compiler/debugger trả structured facts.

Ví dụ:

```text
Query:
    why_not_vectorized(loop42)

Result:
    reason = MAY_ALIAS
    operands = A, B
    required_proof = DISJOINT(A, B)
    proof_status = UNKNOWN
```

AI không cần đoán.

---

# 313.42. Performance Causality Graph

Axiom nên có:

```text
PerformanceExplanationGraph
```

Ví dụ:

```text
slow function
   │
   ├── 40% allocation
   │      └── foreign call escape
   │
   ├── 30% lock wait
   │      └── Mutex A
   │
   └── 20% cache miss
          └── layout/access pattern
```

Mục tiêu:

> profiler cho biết **đang chậm**, compiler explanation cho biết **vì sao compiler tạo code như vậy**.

Hai nguồn thông tin được nối lại.

---

# 313.43. Source → Machine Causality

Compiler phải giữ provenance:

```text
Source
 ↓
HIR
 ↓
MIR
 ↓
Optimization
 ↓
MachineIR
 ↓
Machine Instruction
```

Nếu instruction được tạo từ nhiều source expressions:

```text
InstructionOrigin {
    primary
    secondary[]
    transformation[]
}
```

Debugger/profiler có thể chỉ ra:

```text
instruction X
origin:
    foo.axm:42
    transformed by:
        inline
        constant-fold
        vectorize
```

---

# 313.44. Debugging Optimized Code

Không được yêu cầu:

> “Muốn debug thì phải tắt optimization.”

Axiom phải hướng tới:

```text
-O2 + debug
```

vẫn usable.

Tất nhiên có thể có:

```text
debug-friendly
```

profile để giảm một số transformation làm debugger quá khó sử dụng.

Nhưng semantics và optimizer không được bị thiết kế phụ thuộc vào debug mode.

---

# 313.45. Time-Travel / Replay Foundation

Không nhất thiết implement full reverse debugger ngay.

Nhưng architecture phải hỗ trợ recording:

```text
ExecutionEvent
MemoryEvent
ThreadEvent
TaskEvent
SyncEvent
```

để sau này có:

```text
record
replay
reverse-step
```

Không đưa record/replay vào Core runtime.

---

# 313.46. Deterministic Replay

Cho concurrency test/debug:

```text
record:
    random seed
    scheduler decisions
    synchronization events
```

sau đó:

```text
replay
```

với cùng input.

Mục tiêu:

```text
same program
same input
same schedule
→ same semantic execution
```

trong phạm vi deterministic execution contract.

---

# 313.47. Remote Debugging

Debugger protocol phải tách:

```text
Debugger Client
        │
        ▼
Debugger Protocol
        │
        ▼
Target Debug Agent
```

Có thể debug:

```text
local
remote Linux
embedded
Android
iOS development target
GPU device
```

nhưng target-specific capabilities phải explicit.

---

# 313.48. Embedded/Freestanding Debugging

Freestanding program có thể không có:

```text
filesystem
process
network
runtime
```

nhưng vẫn có thể debug qua:

```text
JTAG
GDB-like protocol
serial
debug stub
```

Axiom debug metadata không được phụ thuộc hosted runtime.

---

# 313.49. Binary Size

Debug/profiling metadata phải có thể:

```text
embedded
separate
stripped
```

Ví dụ:

```text
program.exe
program.debug
program.profile
```

Release executable có thể loại bỏ debug metadata hoàn toàn.

---

# 313.50. Security

Debug information có thể chứa:

- source paths;
- symbol names;
- type names;
- local variables.

Production distribution có thể strip chúng.

Compiler phải hỗ trợ:

```text
strip symbols
strip source paths
redact build paths
split debug info
```

Không làm thay đổi executable semantics.

---

# 313.51. Definition of Done

BOOTSTRAP-313 hoàn thành khi Axiom có:

- source ↔ HIR ↔ MIR ↔ machine debug mapping;
- optimized-code debugging;
- variable location tracking;
- semantic value inspection;
- ownership-aware debugging;
- capability-aware debugging;
- enum/generic/closure debugging;
- async stack debugging;
- thread/task debugging;
- breakpoint/watchpoint model;
- stack unwinding;
- panic stack traces;
- sampling profiler;
- instrumentation profiler;
- allocation profiler;
- lock contention profiler;
- async profiler;
- GPU profiler;
- structured trace;
- sanitizer architecture;
- deterministic concurrency replay;
- remote debugging protocol;
- freestanding debugging foundation;
- AI debugging API;
- compiler optimization explanation;
- source-to-machine causality graph;
- debug metadata strip/split;
- zero semantic cost when debug/profiling disabled.

---

# 313.52. Invariants

`ADBG-20` — Debug metadata must never change language semantics.

`ADBG-21` — Debugger must not report unavailable optimized values as real physical values.

`ADBG-22` — Semantic values must be distinguished from raw machine representation.

`ADBG-23` — Ownership state shown by debugger must match compiler ownership facts.

`ADBG-24` — Capability state shown by debugger must match compiler capability facts.

`ADBG-25` — Moved values must never be presented as valid owned values.

`ADBG-26` — Optimized-away variables must be explicitly marked unavailable or reconstructed.

`ADBG-27` — Source breakpoints must support one-to-many mapping to machine locations.

`ADBG-28` — Async debugging must distinguish logical task stack from physical stack.

`ADBG-29` — Debugger expressions must not introduce side effects by default.

`ADBG-30` — Profiling instrumentation must be removable without semantic change.

`ADBG-31` — Sanitizers must not replace compile-time safety verification.

`ADBG-32` — Runtime diagnostics must preserve thread/task/synchronization provenance when available.

`ADBG-33` — Profiling data must be attributable to source and machine provenance.

`ADBG-34` — GPU profiling must distinguish computation, transfer and synchronization.

`ADBG-35` — Debug information may be stripped without changing program semantics.

`ADBG-36` — Compiler optimization explanations must originate from actual analysis/proof facts.

`ADBG-37` — Replay must record sufficient information to reproduce the declared deterministic execution scope.

`ADBG-38` — Remote debugging must not require a monolithic runtime.

`ADBG-39` — Freestanding targets must be debuggable without hosted runtime assumptions.

`ADBG-40` — AI debugging APIs must expose facts, not speculative explanations.

`ADBG-41` — Debugger, profiler and tracer must remain separate facilities even when sharing metadata infrastructure.