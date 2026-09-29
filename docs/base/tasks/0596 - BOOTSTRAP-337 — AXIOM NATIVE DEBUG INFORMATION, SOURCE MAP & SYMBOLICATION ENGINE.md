# BOOTSTRAP-337 — AXIOM NATIVE DEBUG INFORMATION, SOURCE MAP & SYMBOLICATION ENGINE

Sau 336, Axiom đã có thể tạo binary native được tối ưu rất sâu. Bước tiếp theo cần khóa là **debug architecture**.

Điểm quan trọng: debug không được làm ô nhiễm binary release và cũng không được buộc compiler giữ lại những thông tin runtime không cần thiết.

Mục tiêu:

> **Một binary được tối ưu mạnh vẫn phải debug được chính xác từ source → HIR → MIR → machine instruction, trong khi toàn bộ debug information có thể tách khỏi executable.**

---

# 1. Mô hình tổng thể

Axiom tách:

```text
Source
  ↓
AST/HIR
  ↓
MIR
  ↓
Machine IR
  ↓
Machine Code
```

với:

```text
Debug Information
      ↓
Source Mapping
      ↓
Symbolication
      ↓
Debugger
```

Debug information là **artifact phụ**, không phải semantic dependency của executable.

---

# 2. Debug artifact

Executable:

```text
app.exe
```

Debug artifact:

```text
app.axdbg
```

hoặc target-specific:

```text
app.pdb
app.dwarf
```

Axiom có semantic debug model riêng, sau đó emit sang format target.

---

# 3. Debug information layers

```text
DebugInfo
├── Source
├── Module
├── Declaration
├── Type
├── Variable
├── Scope
├── Inline
├── MIR
├── Machine
├── Async
├── GPU
├── Thread
├── FFI
└── Optimization
```

Không phải layer nào cũng phải emit trong release.

---

# 4. Source identity

Mỗi source file có:

```text
SourceFileId
ContentHash
PathIdentity
ModuleId
PackageId
```

Không dùng path tuyệt đối làm identity duy nhất.

Ví dụ:

```text
C:\Users\...\project\foo.ax
```

không nên xuất hiện bắt buộc trong artifact reproducible.

---

# 5. Source path mapping

Debug artifact có thể lưu:

```text
logical://package/foo.ax
```

và debugger map sang local filesystem.

Điều này giúp:

- reproducible build
- source relocation
- CI
- remote debugging

---

# 6. Source span

Mỗi semantic entity có:

```text
SourceSpan {
    file
    start
    end
}
```

Debug mapping phải giữ được:

```text
machine instruction
    ↓
MIR instruction
    ↓
HIR expression
    ↓
source span
```

---

# 7. Instruction provenance

Mỗi machine instruction có thể mang:

```text
InstructionProvenance {
    source_span
    hir_node
    mir_instruction
    optimization_history
}
```

Không nhất thiết emit toàn bộ ra debug artifact.

Compiler nội bộ vẫn giữ provenance cho diagnostics và validation.

---

# 8. Statement boundaries

Debugger cần biết:

```text
line
column
statement
expression
```

nhưng compiler không được giả định:

```text
1 source statement = 1 machine instruction
```

---

# 9. Optimized code

Ví dụ:

```text
let x = a + b;
let y = x * 2;
```

optimizer có thể biến thành:

```text
single instruction sequence
```

Debugger vẫn phải biểu diễn source semantics hợp lý.

---

# 10. Variable location

Một biến có thể:

```text
Register
Stack
Memory
Constant
MultipleLocations
OptimizedOut
Unavailable
```

Debug info phải biểu diễn location range.

---

# 11. Location ranges

Ví dụ:

```text
x:
  PC 0x1000–0x1010 → RAX
  PC 0x1010–0x1020 → stack[24]
  PC 0x1020–0x1030 → optimized out
```

Không được giả định variable có một location cố định.

---

# 12. SSA-aware debugging

Compiler internal SSA:

```text
x1
x2
x3
```

không nên lộ trực tiếp cho programmer.

Debugger reconstruct:

```text
x
```

theo source variable identity.

---

# 13. Variable value reconstruction

Nếu:

```text
x = a + b
```

và `x` không tồn tại runtime:

Debugger có thể hiển thị x bằng debug expression reconstruction nếu compiler còn đủ information.

Nhưng phải phân biệt:

```text
KnownValue
Unavailable
OptimizedOut
UndefinedAtPoint
```

---

# 14. Optimized-out semantics

Không được giả:

```text
x = 42
```

nếu compiler không thể chứng minh giá trị tại breakpoint.

Debugger phải hiển thị:

```text
optimized out
```

thay vì giá trị bịa.

---

# 15. Scope

Scope tree:

```text
Module
 └── Function
      ├── Parameter
      ├── Local
      └── NestedBlock
```

Compiler tạo `DebugScopeId`.

---

# 16. Lexical scope vs lifetime

Hai khái niệm khác nhau:

```text
LexicalScope
VariableLifetime
```

Ví dụ biến vẫn nằm trong lexical block nhưng đã:

```text
moved
```

Debugger phải phản ánh trạng thái đó.

---

# 17. Ownership-aware debugging

Axiom debugger cần hiểu:

```text
Owned
Moved
PartiallyMoved
Dropped
View
MutView
```

Ví dụ:

```text
let b = a;
```

sau Move:

```text
a = moved
b = owned
```

Debugger không được coi `a` vẫn là một value hợp lệ.

---

# 18. View debugging

Debugger có thể hiển thị:

```text
view<T>
```

với:

```text
owner
region
access
length
```

nhưng không biến view thành một owning value.

---

# 19. Capability visualization

Debug mode có thể expose:

```text
Capability {
    owner
    region
    READ/WRITE
    valid_range
}
```

Đây là tính năng rất hữu ích để tìm lỗi ownership/capability.

---

# 20. Drop debugging

Compiler biết:

```text
Drop(x)
```

Debugger có thể hiển thị lifecycle:

```text
Created
Moved
Dropped
```

Không cần instrument runtime nếu debug artifact đã đủ.

---

# 21. Async debugging

Async function:

```text
async fn foo()
```

được lower thành state machine.

Debugger phải hiển thị:

```text
foo()
  state = AwaitNetwork
```

thay vì bắt programmer nhìn:

```text
FutureState_17
```

---

# 22. Suspension points

Mỗi await:

```text
SuspensionPointId
```

Debug mapping:

```text
await #2
   ↓
state 4
   ↓
machine PC
```

---

# 23. Async stack traces

Stack thực tế có thể:

```text
executor
poll
future_state
```

nhưng debugger nên reconstruct logical stack:

```text
main
 → request
 → fetch_user
 → load_database
```

---

# 24. Task identity

Async task có:

```text
TaskId
```

Debug mode có thể hiển thị:

```text
Task #17
state = Waiting
await = socket.read
```

Không cần TaskId trong ordinary release runtime.

---

# 25. Thread debugging

Thread metadata:

```text
ThreadId
LogicalName
SpawnSite
ParentThread
```

Debugger có thể liên kết:

```text
thread
→ spawn()
→ source span
```

---

# 26. Synchronization debugging

Axiom debugger có thể hiểu:

```text
Mutex
RwLock
Semaphore
Channel
Atomic
```

Ví dụ:

```text
Thread #4
waiting on Mutex #2
```

Nhưng đây là tooling metadata, không phải language runtime requirement.

---

# 27. Data race diagnostics

Safe Axiom code không có data race.

Unsafe/FFI code có thể.

Debug instrumentation có thể ghi:

```text
AccessRegion
Thread
Synchronization
```

để tooling phân tích.

Không thay đổi language semantics.

---

# 28. GPU debugging

GPU kernel:

```text
@kernel fn add(...)
```

có:

```text
CPU launch site
GPU kernel
GPU source span
thread/index
device memory
```

Debugger model phải map được:

```text
GPU instruction
→ kernel IR
→ Axiom source
```

---

# 29. GPU variable locations

GPU backend có thể có:

```text
Register
Local
Shared
Global
Constant
```

Debug info không giả định CPU register model.

---

# 30. FFI debugging

Ví dụ:

```text
Axiom
 ↓
extern C
 ↓
foreign function
```

Debugger phải biết boundary:

```text
Axiom frame
Foreign frame
```

và ABI:

```text
SysV64
Win64
AArch64
...
```

---

# 31. Symbolication

Native crash:

```text
PC = 0x7FF812341234
```

Symbolicator:

```text
PC
 ↓
Binary
 ↓
Function
 ↓
Inline chain
 ↓
SourceSpan
```

Output:

```text
foo.ax:42
```

---

# 32. Split debug artifact

Executable chỉ chứa:

```text
build-id
```

Debug server/storage:

```text
build-id
→ app.axdbg
```

Debugger tải đúng debug artifact.

---

# 33. Build ID

Mỗi binary có:

```text
BuildId
```

được tính từ artifact identity.

Không dùng timestamp.

Điều này giúp:

- reproducibility
- crash symbolication
- debug artifact matching

---

# 34. Debug artifact fingerprint

```text
DebugFingerprint {
    binary_build_id
    compiler_version
    target
    source_fingerprint
    debug_schema_version
}
```

---

# 35. Inline function debugging

Optimizer:

```text
foo()
  inline bar()
```

Machine code có thể chứa:

```text
foo frame
bar logical frame
```

Debugger phải reconstruct inline stack.

---

# 36. Inlining provenance

Mỗi inline region:

```text
InlineInstance {
    callee
    call_site
    parent_inline
    machine_range
}
```

---

# 37. Tail calls

Tail call:

```text
foo()
 → bar()
```

không tạo frame mới.

Debugger phải hiểu logical call chain.

---

# 38. Frame elimination

Optimizer có thể:

```text
inline
tailcall
omit frame
register-only
```

Debug info phải chịu được frame không tồn tại vật lý.

---

# 39. Machine frame vs logical frame

Axiom debugger phân biệt:

```text
PhysicalFrame
LogicalFrame
```

Đây là abstraction rất quan trọng.

---

# 40. Breakpoints

Breakpoint target:

```text
source file
line
column
function
expression
```

Debugger resolve thành:

```text
machine addresses
```

---

# 41. Conditional breakpoint

Expression evaluator phải tuân thủ Axiom semantics.

Không được tự ý thực hiện:

```text
IO
mutation
foreign call
```

chỉ vì debugger evaluate expression.

---

# 42. Debug expression evaluation

Hai mode:

```text
PureInspect
UnsafeEvaluate
```

Default:

```text
PureInspect
```

chỉ đọc state.

---

# 43. Debugger-created values

Debugger không nên tạo object runtime tùy tiện.

Nếu cần:

```text
materialize temporary
```

phải explicit và không làm thay đổi chương trình trừ khi user chọn evaluation có side effect.

---

# 44. Exception/Panic debugging

Axiom panic:

```text
Panic
```

debugger nhận:

```text
PanicSite
Message
Payload
Stack
Cause
```

Nếu profile abort:

```text
no unwind required
```

nhưng symbolication vẫn hoạt động.

---

# 45. Error chain

`Result` không phải exception.

Debugger nên phân biệt:

```text
panic
error return
cancelled
foreign exception
OS signal
```

---

# 46. Crash dump

Axiom có:

```text
axiom dump inspect crash.dump
```

Crash dump chứa:

```text
registers
stack
loaded modules
thread state
build IDs
signal/exception
```

Không nhất thiết chứa source.

---

# 47. Offline symbolication

Nếu có:

```text
binary
debug artifact
crash dump
```

có thể symbolicate offline.

---

# 48. Remote debugging

Debugger architecture:

```text
Debugger UI
     ↓
Debug Protocol
     ↓
Debug Agent
     ↓
Process
```

Agent target-specific.

---

# 49. Debug protocol

Axiom nên có semantic protocol:

```text
attach
detach
pause
resume
step
next
continue
read_memory
read_register
read_variable
set_breakpoint
remove_breakpoint
stack_trace
threads
tasks
gpu_state
```

Backend chuyển sang:

- ptrace
- Windows debugging APIs
- LLDB-like backend
- GDB remote
- platform APIs

---

# 50. Debug adapter

Axiom debugger không cần tự implement mọi OS debugging primitive ngay.

Architecture:

```text
Axiom Debug Protocol
       ↓
Platform Debug Adapter
       ↓
OS Debug API
```

---

# 51. Debug info format abstraction

Internal:

```text
AxiomDebugModel
```

Emit:

```text
DWARF
PDB
CodeView
dSYM-compatible
custom .axdbg
```

---

# 52. Do not expose target quirks to language

Programmer không cần biết:

```text
DWARF DIE
PDB subsection
```

Compiler debug model thống nhất.

---

# 53. Type debug information

Debugger cần reconstruct:

```text
struct
enum
tuple
array
view
mut_view
Option
Result
generic
trait
closure
```

---

# 54. Type identity

Debug type identity dựa trên:

```text
TypeId
TypeFingerprint
```

không dựa vào debug name đơn thuần.

---

# 55. Generic debugging

Ví dụ:

```text
Vec<i32>
```

Debugger phải biết:

```text
Vec<T>
T = i32
```

và hiển thị field semantics.

---

# 56. Trait object debugging

`dyn Trait` có:

```text
dynamic_type
vtable
object_data
```

nếu representation contract cho phép debug introspection.

---

# 57. Closure debugging

Closure:

```text
|x| x + captured
```

Debugger có thể hiển thị:

```text
captured variables
```

theo source names, không phải chỉ environment struct.

---

# 58. Comptime debugging

Comptime execution không phải runtime process.

Compiler diagnostic/debugger có thể inspect:

```text
comptime value
comptime stack
comptime source span
```

trong compiler debug mode.

---

# 59. Comptime provenance

Generated declaration:

```text
GeneratedFoo
```

phải map được:

```text
GeneratedFoo
 ← comptime invocation
 ← source declaration
```

---

# 60. Generated code debugging

Nếu:

```text
comptime generate()
```

tạo code:

```text
fn foo()
```

debugger/compiler tooling có thể hiển thị:

```text
generated from:
source span
comptime call
generation fingerprint
```

---

# 61. Debug optimization levels

```text
-O0
-Og
-O1
-O2
-O3
-Os
-Oz
```

Axiom không cần copy GCC naming.

Semantic profiles:

```text
Debug
DebugOptimized
Release
ReleaseSize
ReleaseSpeed
```

---

# 62. Debug correctness

Optimization không được tạo debug mapping giả.

Compiler phải phân biệt:

```text
Exact
Approximate
Unavailable
```

Ví dụ variable value chỉ có thể approximate:

```text
<value unavailable at this point>
```

---

# 63. Debug verification

Compiler validation kiểm tra:

```text
machine PC ranges
source spans
variable locations
inline trees
scope ranges
```

không overlap bất hợp lệ.

---

# 64. Debug info compression

Debug artifact có thể được compress:

```text
zstd
```

hoặc target-specific compression.

Không ảnh hưởng executable.

---

# 65. Debug artifact garbage collection

Artifact store có thể garbage collect debug artifacts nếu:

```text
no retention policy
no deployment reference
```

Build reproducibility vẫn có thể regenerate.

---

# 66. CompilerDB additions

```text id="f6k6pq"
DebugDB
SourceMapDB
DebugTypeDB
DebugScopeDB
DebugVariableDB
DebugLocationDB
DebugInlineDB
DebugAsyncDB
DebugGpuDB
DebugFfiDB
SymbolicationDB
CrashDB
DebugArtifactDB
```

---

# 67. APIs

```text id="u4m6tq"
build_debug_info()

map_source_to_machine()
map_machine_to_source()

resolve_variable_location()

build_inline_tree()
build_scope_tree()

symbolicate_address()
symbolicate_stack()

inspect_crash_dump()

create_debug_artifact()
verify_debug_artifact()

attach_debugger()
set_breakpoint()
evaluate_debug_expression()

inspect_async_state()
inspect_gpu_state()

explain_optimized_variable()
```

---

# 68. CLI

```text id="1e0h2p"
axiom debug info
axiom debug inspect
axiom debug symbols
axiom debug source-map

axiom symbolize <address>
axiom crash inspect dump.axdump

axiom debug verify
```

---

# 69. Implementation tree

```text id="6h4jta"
compiler/
└── debug/
    ├── source_map/
    ├── provenance/
    ├── types/
    ├── scopes/
    ├── variables/
    ├── locations/
    ├── inline/
    ├── async/
    ├── gpu/
    ├── ffi/
    ├── symbolication/
    ├── crash/
    ├── protocol/
    ├── adapters/
    ├── dwarf/
    ├── pdb/
    ├── codeview/
    └── axdbg/
```

---

# 70. Invariants

```text
ADBG-01
Debug information must never alter language semantics.

ADBG-02
Release binaries must not require debug artifacts unless explicitly configured.

ADBG-03
Debug artifacts must identify the exact binary they describe.

ADBG-04
Source mapping must be deterministic.

ADBG-05
Machine instructions must retain valid source provenance when debug information is emitted.

ADBG-06
Optimized variables may be unavailable and must never be fabricated.

ADBG-07
Logical source frames must remain distinguishable from physical machine frames.

ADBG-08
Inline call stacks must be reconstructible when emitted.

ADBG-09
Tail calls and frame elimination must not corrupt logical stack information.

ADBG-10
Ownership state must be respected by debugger inspection.

ADBG-11
Moved or dropped values must not be presented as valid live values.

ADBG-12
View and mut_view debugging must preserve capability semantics.

ADBG-13
Async state must map to source-level suspension points.

ADBG-14
GPU debugging must use the GPU execution/storage model.

ADBG-15
FFI frames must respect foreign ABI contracts.

ADBG-16
Comptime debugging must remain separate from runtime debugging.

ADBG-17
Generated code must preserve generation provenance.

ADBG-18
Symbolication must verify binary/debug artifact identity.

ADBG-19
Debug evaluation must not silently introduce side effects.

ADBG-20
Debug metadata must not become a hidden runtime dependency.

ADBG-21
Debug information must remain valid after optimization transformations.

ADBG-22
Split debug artifacts must be independently verifiable.

ADBG-23
Crash dumps must be interpretable without embedding source code in the executable.

ADBG-24
Target-specific debug formats must not change Axiom semantic debug meaning.

ADBG-25
Debug tooling must never be required for correct execution of the final binary.
```

---

# 71. Definition of Done

BOOTSTRAP-337 hoàn thành khi Axiom có:

- Source → machine source mapping.
- Bidirectional source map.
- Semantic provenance.
- Optimized variable locations.
- Scope model.
- Ownership-aware debugging.
- Capability/view debugging.
- Drop/move state debugging.
- Inline call stack.
- Logical vs physical stack frames.
- Async state debugging.
- Task/thread debugging.
- Synchronization inspection.
- GPU kernel debugging.
- FFI boundary debugging.
- Comptime provenance.
- Generated-code provenance.
- Split debug artifacts.
- Build ID.
- Debug artifact fingerprint.
- Symbolication.
- Crash dump model.
- Offline symbolication.
- Remote debug protocol.
- Platform debug adapters.
- DWARF/PDB/CodeView abstraction.
- Axiom native `.axdbg` model.
- Debug expression engine.
- Optimized-value diagnostics.
- Debug artifact verification.
- Integration với 315 Formal Semantics.
- Integration với 317 Reference Interpreter.
- Integration với 318 Translation Validation.
- Integration với 319 Pass Contracts.
- Integration với 324 ABI.
- Integration với 325 Component.
- Integration với 326 FFI.
- Integration với 336 Binary Layout.
- Integration với 313 Debugger/Profiler architecture đã có trước đó.

## Nguyên tắc khóa

> **Debug information là một phép chiếu ngược từ machine program về semantic program; nó không được trở thành một phần bắt buộc của semantic program.**

Và:

> **Compiler càng tối ưu mạnh thì debug model càng phải thông minh, chứ không phải giảm optimization để debugger hoạt động.**

Điều này giữ được mục tiêu rất quan trọng của Axiom: **Release binary có thể cực nhỏ và cực tối ưu, nhưng khi cần debug, compiler vẫn có khả năng giải thích machine code theo đúng mô hình ngôn ngữ.**