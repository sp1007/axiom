# BOOTSTRAP-317 — AXIOM REFERENCE INTERPRETER & EXECUTABLE SEMANTIC MODEL

## 1. Mục tiêu

BOOTSTRAP-315 đã định nghĩa **reference semantics**.

BOOTSTRAP-316 đã tạo **machine-readable specification**.

Bước tiếp theo là xây dựng một implementation có thể **thực sự chạy chương trình Axiom theo semantics chuẩn**, nhưng **không phụ thuộc optimizer, native backend, register allocator, linker hay runtime production**.

Đây sẽ là:

> **Axiom Reference Interpreter (ARI)** — semantic oracle độc lập dùng để xác định chương trình Axiom phải làm gì.

Mục tiêu không phải tốc độ.

Mục tiêu là:

- correctness;
- deterministic semantic behavior;
- compiler differential testing;
- optimizer verification;
- conformance testing;
- bootstrap validation;
- AI/compiler debugging.

---

# 2. Vị trí trong kiến trúc

Pipeline production:

```text
Axiom Source
    ↓
Frontend
    ↓
HIR
    ↓
MIR
    ↓
Verification
    ↓
Optimization
    ↓
Machine Code
    ↓
Executable
```

Reference pipeline:

```text
Axiom Source
    ↓
Frontend
    ↓
Reference Semantic IR
    ↓
Reference Interpreter
    ↓
Observable Result
```

Hai pipeline phải hội tụ về cùng semantics:

```text
                ┌── Production Compiler ──→ Native
Axiom Program ──┤
                └── Reference Interpreter → Result
```

---

# 3. ARI không phải VM production

ARI **không phải**:

- runtime mặc định;
- bytecode VM cho application;
- JIT;
- emulator CPU;
- replacement cho native backend.

ARI chỉ là:

```text
Semantic Oracle
```

Do đó có thể:

- chậm;
- dùng nhiều memory;
- không hỗ trợ mọi target machine;
- bỏ qua register allocation;
- bỏ qua machine instruction scheduling.

---

# 4. Reference Semantic IR

Không chạy trực tiếp machine MIR.

Định nghĩa:

```text
RSIR = Reference Semantic Intermediate Representation
```

RSIR giữ các khái niệm semantic:

```text
Value
Place
Owner
Capability
Region
Effect
ExecutionDomain
StorageDomain
Future
ComptimeValue
ForeignBoundary
```

nhưng không chứa:

```text
register
stack slot
machine opcode
physical address
calling convention
```

---

# 5. RSIR Design

RSIR instruction concept:

```text
Const
Copy
Move
Assign
Load
Store
MakeStruct
MakeEnum
MakeView
MakeMutView
Call
Return
Branch
Switch
Drop
Panic
AtomicLoad
AtomicStore
AtomicRmw
Spawn
Await
ChannelSend
ChannelReceive
ComptimeEval
ForeignCall
GpuLaunch
```

Mỗi instruction có semantic preconditions/postconditions.

---

# 6. Semantic State

Interpreter state:

```text
ReferenceState {
    variables
    places
    ownership
    capabilities
    memory
    effects
    execution
    synchronization
    tasks
    futures
    external_state
}
```

Không được mô hình hóa memory chỉ bằng một:

```text
HashMap<Address, Byte>
```

vì Axiom semantics cần ownership/provenance/capability.

---

# 7. Semantic Memory

ARI có memory model riêng:

```text
SemanticMemory {
    AllocationId
    Region
    Layout
    Initialization
    Ownership
    Provenance
}
```

Ví dụ:

```text
Allocation #17
 ├── Type: Vec<i32>
 ├── Region: R42
 ├── State: Initialized
 ├── Owner: local#3
 └── Provenance: allocation#17
```

Địa chỉ machine không cần tồn tại.

---

# 8. Provenance

Raw pointer semantics cần được mô hình hóa:

```text
RawPointer {
    provenance
    offset
}
```

Không dùng:

```text
u64
```

làm semantic pointer.

Điều này cho phép ARI phát hiện:

- invalid provenance;
- out-of-bounds;
- invalid alignment;
- use-after-free;
- pointer arithmetic violation;

mà không phụ thuộc OS memory layout.

---

# 9. Ownership State Machine

ARI phải thực thi chính xác:

```text
Uninit
   ↓
Owned
   ↓
Moved
   ↓
Dropped
```

và:

```text
Owned
 ├── Copy → Owned + Owned
 ├── Move → Moved + Owned
 ├── Drop → Dropped
 └── View → Owned + Capability
```

Partial move:

```text
Owned<T>
  ├── field A → Moved
  └── field B → Owned
```

phải được biểu diễn field-sensitive.

---

# 10. Capability State

ARI phải lưu:

```text
Capability {
    id
    provenance
    region
    access
    validity
    lifetime
}
```

Ví dụ:

```text
view<T>
```

tạo:

```text
Capability {
    access = READ
    region = R7
}
```

`mut_view<T>`:

```text
access = WRITE
```

Interpreter phải reject semantic conflict ngay cả khi source compiler verifier đã được chạy.

Điều này giúp phát hiện verifier bug.

---

# 11. Reference Interpreter không tin compiler verifier

Đây là nguyên tắc quan trọng.

Không:

```text
compiler verifier says valid
→ interpreter trusts it
```

Thay vào đó:

```text
RSIR
 ↓
Reference semantic checks
 ↓
Execution
```

Verifier production và ARI là **hai implementation độc lập của cùng semantics**.

Nếu cả hai đều dựa trên cùng một helper implementation, bug có thể bị che giấu.

---

# 12. Value Model

ARI cần phân biệt:

```text
Value
Place
Storage
Capability
Identity
```

Ví dụ:

```text
Vec<i32>
```

không được coi đơn giản là:

```text
(pointer, length, capacity)
```

nếu representation đó chưa phải semantics.

ARI giữ semantic:

```text
Vec {
    elements
    length
    capacity
    ownership
}
```

Representation chỉ xuất hiện khi kiểm tra ABI/layout.

---

# 13. Drop Execution

Interpreter thực thi Drop semantic:

```text
scope exit
     ↓
determine live owners
     ↓
reverse initialization order
     ↓
drop
```

Kiểm tra:

- moved field không drop;
- dropped value không drop lần hai;
- capability còn sống không được owner drop;
- cleanup trên early return;
- cleanup trên panic nếu profile unwind.

---

# 14. Panic Semantics

ARI phải mô hình hóa:

```text
Normal
Return
Panic
Trap
Abort
Unwind
```

Không coi panic đơn giản là:

```text
return error
```

vì Drop/unwind semantics có thể khác.

---

# 15. Effect Semantics

Interpreter tracking:

```text
Read
Write
Allocate
Deallocate
Drop
Atomic
Volatile
IO
Panic
Synchronize
Foreign
```

Mục tiêu là xác minh effect declarations.

Ví dụ một function khai báo:

```text
effect(readonly)
```

nhưng thực hiện:

```text
Store
```

→ semantic violation.

---

# 16. Concurrency Interpreter

ARI cần execution scheduler mô phỏng:

```text
Thread
Task
Fiber
```

nhưng scheduler phải **deterministic mode** mặc định.

Ví dụ:

```text
--schedule deterministic
```

cho phép reproduce race/synchronization bugs.

---

# 17. Memory Ordering

ARI phải có semantic event graph:

```text
Event A
  │
  ├── sequenced-before
  │
Event B
  │
  └── synchronizes-with
        │
        ▼
Event C
```

Sau đó tạo:

```text
happens-before
```

graph.

Không mô phỏng x86/ARM instruction.

---

# 18. Atomic Model

ARI hỗ trợ:

```text
Relaxed
Acquire
Release
AcqRel
SeqCst
```

và kiểm tra:

- atomicity;
- modification order;
- synchronization;
- happens-before.

Không giả định:

```text
x86 = memory model của Axiom.
```

---

# 19. Async Interpreter

Future trong ARI là semantic object:

```text
Future {
    state
    suspension_point
    continuation
    captured_values
}
```

`.await`:

```text
Future
  ↓
Poll
  ├── Ready(value)
  └── Pending(waker)
```

Không cần tạo machine coroutine.

---

# 20. Async Scheduler

ARI có deterministic executor:

```text
ReadyQueue
WaitingFutures
Wakers
CompletedTasks
```

Ví dụ:

```text
task A
task B
task C
```

có thể replay chính xác.

Điều này hỗ trợ test:

```text
await
cancellation
channel
mutex
task migration
```

---

# 21. Cancellation

ARI phân biệt:

```text
Future dropped
Task cancelled
Panic
Abort
Normal completion
```

Không suy luận:

```text
drop future = force terminate external operation
```

đúng với semantics đã frozen.

---

# 22. Comptime Interpreter

ARI semantic engine có thể dùng chung với:

```text
Comptime VM
```

nhưng capability environment khác:

```text
Runtime Environment
Comptime Environment
```

Ví dụ:

```text
ReadFilesystem
```

chỉ tồn tại nếu comptime capability được cấp.

---

# 23. Comptime Determinism

ARI có hai mode:

```text
deterministic
nondeterministic
```

Deterministic mode phải reject hoặc mock:

- time;
- random;
- network;
- external process;

nếu capability không có deterministic contract.

---

# 24. FFI Model

ARI không thực thi C library thật trong semantic core.

Thay vào đó:

```text
ForeignCall
```

có thể dùng:

```text
ForeignModel
```

Ví dụ:

```text
memcpy
```

có model:

```text
reads src
writes dst
does not retain pointers
returns destination
```

Nếu cần test integration thật, external FFI harness chạy ngoài ARI.

---

# 25. External World Model

ARI phải mô hình hóa abstractly:

```text
File
Socket
Clock
Random
Environment
Process
Device
```

Ví dụ:

```text
FileSystemModel
```

có thể là:

```text
deterministic virtual filesystem
```

để test reproducibly.

---

# 26. GPU Reference Model

GPU không cần mô phỏng instruction-level.

ARI mô hình hóa:

```text
Kernel
Launch
DeviceMemory
SharedMemory
Atomic
Barrier
Completion
```

Ví dụ:

```text
GPU kernel
    ↓
semantic execution domain
    ↓
device memory effects
```

Mục tiêu là kiểm tra semantics, không benchmark GPU.

---

# 27. Undefined/Invalid State

ARI phải có trạng thái:

```text
SemanticViolation
```

Không cố chạy tiếp một chương trình semantic-invalid để tạo kết quả giả.

Ví dụ:

```text
use-after-move
```

→:

```text
SemanticViolation {
    rule = OWN-MOVE-001
}
```

---

# 28. Observable Result

ARI output:

```text
ExecutionResult {
    status
    return_value
    stdout
    stderr
    effects
    panic
    trap
    synchronization
    external_events
}
```

Không đưa internal implementation state vào semantic equality.

---

# 29. Semantic Trace

Có chế độ:

```text
axiom run --trace
```

Trace:

```text
#1 create owner x
#2 move x → y
#3 create view y
#4 read y
#5 drop y
#6 return
```

Hoặc concurrency:

```text
T1: atomic.store Release
T1: unlock
T2: lock
T2: atomic.load Acquire
```

---

# 30. Trace IDs

Mỗi semantic event:

```text
SemanticEventId
```

được liên kết với:

```text
SourceSpan
RuleId
InstructionId
```

Do đó debugger/AI có thể hỏi:

> Tại sao giá trị này bị move?

ARI trả được causal chain.

---

# 31. Differential Compiler Testing

Một test chạy:

```text
source
 ├──→ ARI → result A
 │
 └──→ native compiler → result B
```

So sánh:

```text
A == B
```

theo semantic equivalence.

Nếu mismatch:

```text
COMPILER-SEMANTIC-MISMATCH
```

và tự động tạo failure artifact.

---

# 32. MIR Differential Testing

Có thể chạy:

```text
HIR → MIR → ARI
```

và:

```text
HIR → optimized MIR → ARI
```

So sánh:

```text
Result(unoptimized)
==
Result(optimized)
```

Đây là oracle trực tiếp cho optimization.

---

# 33. Optimization Fuzzing

Generator tạo chương trình:

```text
P
```

sau đó compiler tạo:

```text
P'
```

ARI chạy cả hai:

```text
ARI(P)
ARI(P')
```

Nếu khác:

```text
optimizer bug
```

Không cần biết optimization nào vừa chạy.

---

# 34. Compiler Reduction

Khi mismatch xảy ra, ARI infrastructure tích hợp reducer:

```text
large program
      ↓
remove declaration
      ↓
remove statement
      ↓
simplify expression
      ↓
reduce types
      ↓
minimal reproducer
```

Kết quả:

```text
minimal.axm
```

để compiler developer sửa bug.

---

# 35. Semantic Snapshot

ARI có thể serialize:

```text
ReferenceSnapshot {
    source_hash
    spec_hash
    semantic_state
    result
}
```

Dùng cho regression testing.

Nếu specification thay đổi:

```text
SPEC-SNAPSHOT-STALE
```

chứ không silently accept snapshot cũ.

---

# 36. Implementation Independence

ARI phải tránh dùng production compiler components ở những điểm có thể tạo correlated bugs.

Có thể dùng chung:

- lexer;
- parser;
- source map;
- AXSpec loader;

nhưng semantic execution core phải độc lập với:

- production ownership verifier;
- optimizer;
- codegen;
- backend;
- machine model.

---

# 37. Reference Interpreter Architecture

```text id="k6o7v4"
compiler/reference/
├── ast/
├── semantic_ir/
├── values/
├── memory/
├── ownership/
├── capability/
├── effects/
├── concurrency/
├── async/
├── comptime/
├── ffi/
├── gpu/
├── scheduler/
├── environment/
├── trace/
├── equivalence/
└── diagnostics/
```

---

# 38. Public APIs

```text id="8p6j6s"
run_reference(program)
evaluate_reference(expression)
evaluate_comptime(program)
compare_semantics(program_a, program_b)
trace_execution(program)
snapshot_state()
replay_trace(trace)
```

Compiler testing API:

```text
compare_native_with_reference()
compare_mir_with_reference()
compare_optimized_mir_with_reference()
```

---

# 39. AI Integration

AI compiler agent có thể hỏi:

```text
explain_execution(source)
```

và nhận:

```text
semantic events
ownership transitions
capability transitions
effect transitions
synchronization events
drop sequence
```

Thay vì AI phải suy luận toàn bộ behavior từ source.

---

# 40. Reference Interpreter và Debugger

Debugger có thể cung cấp hai chế độ:

```text
Native Debugging
Reference Semantic Debugging
```

Reference mode cho phép inspect:

```text
Owner
Capability
Region
Effect
Future state
Synchronization
```

những thứ có thể không còn tồn tại trực tiếp trong optimized machine code.

---

# 41. Performance

ARI **không được tối ưu theo hướng biến nó thành production runtime**.

Tuy nhiên vẫn cần:

- structural sharing;
- immutable interned types;
- compact semantic values;
- arena allocation;
- deterministic scheduler;
- memoization cho pure comptime;
- snapshot delta;
- parallel independent test execution.

Mục tiêu:

> đủ nhanh để chạy hàng triệu semantic tests trong CI.

---

# 42. Conformance Integration

`axspec conformance`:

```text
AXSpec
  ↓
test generation
  ↓
Reference Interpreter
  ↓
expected semantic result
  ↓
Production Compiler
  ↓
actual result
  ↓
compare
```

Do đó conformance test không cần hard-code expected result bằng tay trong mọi trường hợp.

---

# 43. Reference Interpreter Bootstrap

Stage 0:

```text
ARI → host language
```

Stage 1:

```text
ARI → Axiom
```

Stage 2:

```text
ARI self-hosted
```

Không cần production compiler hoàn thiện trước khi ARI có thể trở thành semantic oracle.

---

# 44. Trust Model

ARI cũng phải có trust boundary rõ:

```text
AXSpec
  ↓
Reference implementation
  ↓
Reference result
```

Nếu ARI và production compiler cùng sai vì cùng một specification bug thì conformance system không phát hiện được.

Do đó cần:

```text
specification mutation tests
```

để kiểm tra test suite thực sự nhạy với semantic changes.

---

# 45. Specification Mutation Testing

Tool:

```text
axspec mutate
```

tạo các semantic mutation:

```text
READ+WRITE allowed
Move no longer consumes source
Drop order reversed
Acquire weakened
Await allows invalid guard
```

Sau đó chạy conformance suite.

Expectation:

```text
mutation → tests FAIL
```

Nếu:

```text
mutation → all tests PASS
```

thì test coverage chưa đủ.

Đây là cơ chế rất mạnh để kiểm tra **chất lượng của chính conformance suite**.

---

# 46. Definition of Done

BOOTSTRAP-317 hoàn thành khi Axiom có:

1. Reference Semantic IR.
2. Independent Reference Interpreter.
3. Semantic memory model.
4. Provenance-aware raw pointer model.
5. Ownership execution model.
6. Capability execution model.
7. Drop execution.
8. Effect execution.
9. Deterministic concurrency scheduler.
10. Memory-order execution model.
11. Async/Future interpreter.
12. Comptime interpreter.
13. FFI abstract model.
14. GPU semantic model.
15. External environment model.
16. Semantic trace.
17. Replay.
18. Semantic snapshots.
19. Native-vs-reference differential testing.
20. MIR-vs-reference testing.
21. Optimized-MIR-vs-reference testing.
22. Automatic failure reduction.
23. Specification mutation testing.
24. AI semantic execution API.
25. Conformance integration.
26. Independent semantic verification path.
27. Self-hosting roadmap.

---

## Nguyên tắc đóng băng

> **Axiom phải có một implementation chậm nhưng đáng tin cậy để trả lời “chương trình này có nghĩa gì?” mà không cần tin vào optimizer, backend hay machine code generator.**

Kiến trúc hoàn chỉnh sẽ là:

```text
                    AXSpec
                      │
             ┌────────┴────────┐
             ▼                 ▼
      Reference Semantics   Production Compiler
             │                 │
             ▼                 ▼
       Reference Result    Native Result
             │                 │
             └────────┬────────┘
                      ▼
              Semantic Equivalence
                      │
          ┌───────────┼───────────┐
          ▼           ▼           ▼
        Tests      Optimizer      AI
```

Đây là một trong những lớp quan trọng nhất để Axiom có thể hướng tới mục tiêu **compiler cực kỳ tối ưu nhưng vẫn có một “ground truth” độc lập để chống compiler/optimizer bug**.