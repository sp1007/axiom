Tiếp tục.

# Axiom — Debugger, Profiler, Sanitizer & Developer Tooling v0.1

Đây là lớp biến Axiom từ **compiler có thể tạo binary** thành **một hệ sinh thái phát triển thực dụng**.

Nguyên tắc lớn:

> **Tooling không được trở thành runtime bắt buộc.**

Một chương trình release cực nhỏ vẫn có thể:

```text
source
 ↓
compiler
 ↓
native binary
```

không mang debugger, profiler hay sanitizer.

---

# 1. Một CLI thống nhất

Tôi đề xuất:

```text
axiom check
axiom build
axiom run
axiom test
axiom bench
axiom debug
axiom profile
axiom trace
axiom inspect
axiom fmt
axiom doc
```

Các lệnh này dùng chung:

```text
Project Graph
Compiler Driver
Diagnostic Engine
Build Cache
Target Configuration
```

Không tạo nhiều tool rời rạc như:

```text
gcc
objdump
nm
addr2line
readelf
```

Axiom có thể cung cấp các chức năng tương đương dưới một CLI.

---

# 2. `axiom check`

Chỉ kiểm tra:

```text
parse
resolve
typecheck
ownership
view
concurrency
pattern
```

Không:

```text
codegen
link
```

Ví dụ:

```text
axiom check
```

phải đủ nhanh để IDE gọi liên tục.

---

# 3. `axiom build`

Pipeline:

```text
Source
 ↓
check
 ↓
MIR
 ↓
verify
 ↓
optimize
 ↓
codegen
 ↓
link
```

---

# 4. `axiom run`

```text
axiom run
```

tự:

```text
build
 ↓
execute
```

Có thể:

```text
axiom run --release
```

---

# 5. `axiom test`

Test binary nên là executable native bình thường.

Ví dụ:

```axiom
@test
fn test_add() {
    assert(add(2, 3) == 5)
}
```

Compiler tạo:

```text
test executable
```

Không cần test runtime khổng lồ.

---

# 6. Test discovery

Compiler/toolchain biết:

```text
@test
@bench
```

nhưng framework assertion vẫn là library.

Ví dụ:

```text
@test
fn vector_sum() { ... }
```

được discover ở compile time.

---

# 7. Test isolation

Mỗi test có thể:

```text
same process
```

hoặc:

```text
separate process
```

theo profile.

Không cần mặc định spawn process cho mọi test.

---

# 8. Deterministic tests

Test runner hỗ trợ:

```text
--seed
--threads
--repeat
```

Concurrency test có thể dùng deterministic scheduler của Oracle/runtime debug.

---

# 9. Debug information architecture

Compiler tạo:

```text
DebugInfo
```

gắn với:

```text
SourceSpan
HIR
MIR
LIR
MachineInstruction
```

Ví dụ:

```text
source line 42
 ↓
MIR block 17
 ↓
LIR instruction 93
 ↓
x86 instruction address 0x401234
```

---

# 10. Debugger không cần biết MIR để debug cơ bản

Debugger có thể đọc:

```text
DWARF
PDB/CodeView
```

Nhưng Axiom nên thêm metadata riêng để debug tốt hơn.

Ví dụ:

```text
AXDBG
```

lưu:

```text
Axiom type identity
generic information
ownership state
optimized variable mapping
async state
source semantic information
```

---

# 11. Không nên tạo debugger protocol riêng

Axiom nên hỗ trợ:

```text
DAP
```

(Debug Adapter Protocol)

để IDE có thể kết nối.

Architecture:

```text
IDE
 ↓ DAP
axiom debug
 ↓
platform debugger backend
 ↓
process
```

---

# 12. Platform debugger

Linux:

```text
ptrace / native debugger backend
```

Windows:

```text
Windows debugging API
```

macOS:

```text
Mach/debug APIs
```

Axiom debugger abstraction:

```text
Process
Thread
Register
Memory
Breakpoint
Watchpoint
StackFrame
Variable
```

---

# 13. Breakpoint

```text
break foo
```

hoặc:

```text
break main.axiom:42
```

Compiler map:

```text
source → machine address
```

---

# 14. Optimized debugging

Không hứa:

> mọi source variable luôn tồn tại.

Thay vào đó debugger báo:

```text
x = optimized out
```

hoặc:

```text
x = <constant 42>
```

hoặc:

```text
x = register RAX
```

---

# 15. Ownership-aware debugger

Đây là một lợi thế đặc biệt của Axiom.

Compiler đã biết:

```text
OWNED
MOVED
PARTIAL
VIEW
MUT_VIEW
DROPPED
```

Debugger có thể hiển thị:

```text
file : OWNED
buffer : MOVED
view : ACTIVE READ
```

nhưng đây là **debug metadata**, không phải runtime overhead.

---

# 16. View debugger

Ví dụ:

```text
view<i32>
```

debugger có thể hiển thị:

```text
type: view<i32>
region: buffer[10..20]
access: READ
owner: buffer
```

Nếu compiler có đủ provenance metadata trong debug build.

---

# 17. Async debugger

Future state:

```text
State #3
 ├── socket
 ├── buffer
 └── timeout
```

Debugger có thể hiển thị:

```text
async function: download
state: WaitingForRead
```

thay vì chỉ thấy một stack frame khó hiểu.

---

# 18. Thread debugger

Hiển thị:

```text
Thread 1
Thread 2
Thread 3
```

và Axiom semantic metadata:

```text
Send
Share
Mutex
Channel
Atomic
```

nếu debug build giữ metadata.

---

# 19. Panic diagnostics

Ví dụ:

```text
panic: index out of bounds

  src/vector.axiom:42
  index = 17
  length = 10

stack:
  foo()
  bar()
  main()
```

Không cần exception object.

---

# 20. Panic payload

Không nên bắt buộc panic message tồn tại trong release.

Profiles:

```text
debug:
    full panic info

release:
    configurable

size:
    minimal
```

---

# 21. Stack traces

Panic abort vẫn có thể hỗ trợ stack trace nếu:

```text
debug symbols
unwind info
```

được giữ.

Không cần unwind exception runtime.

---

# 22. Profiler

Profiler nên dựa chủ yếu trên **sampling**.

Không instrument mọi function mặc định.

```text
CPU
 ↓
periodic sample
 ↓
instruction address
 ↓
symbol/source
```

Overhead thấp.

---

# 23. `axiom profile`

Ví dụ:

```text
axiom profile run
```

tạo:

```text
profile.axprof
```

Có thể chứa:

```text
CPU samples
threads
stacks
allocations
locks
async states
```

---

# 24. Flame graph

Tool:

```text
axiom profile flamegraph
```

chuyển:

```text
samples
 ↓
call tree
 ↓
flame graph
```

Không cần browser dependency cho việc thu thập dữ liệu.

---

# 25. Instrumentation profile

Sampling không đủ cho mọi trường hợp.

Có thể:

```text
--profile=instrumented
```

Compiler chèn counters:

```text
function entry
loop edge
branch
```

nhưng chỉ khi yêu cầu.

---

# 26. PGO

Axiom nên hỗ trợ:

```text
build instrumented
 ↓
run workload
 ↓
profile data
 ↓
build optimized
```

Ví dụ:

```text
axiom build --pgo=generate
axiom run
axiom build --pgo=use
```

Compiler có thể dùng:

- hot/cold function
- branch probability
- inline decisions
- code layout
- indirect call specialization
- vectorization hints.

---

# 27. PGO không thay semantics

Profile chỉ ảnh hưởng optimization.

```text
PGO on/off
```

không được thay đổi:

```text
overflow
float semantics
atomic ordering
ownership
```

---

# 28. Allocation profiler

Vì Axiom không có mandatory heap, profiler nên đo:

```text
allocation count
allocation bytes
deallocation count
peak live bytes
allocation site
```

Ví dụ:

```text
Vec.push
  allocations: 124
  bytes: 4.2 MB
```

---

# 29. Nhưng allocation instrumentation không được mặc định

Release:

```text
no allocation hooks
```

Debug:

```text
optional
```

Profile:

```text
enabled explicitly
```

---

# 30. Memory profiler

Có thể có:

```text
axiom profile memory
```

hiển thị:

```text
heap
arena
pool
TLS
static
```

Đây là tool-level instrumentation.

---

# 31. Sanitizer philosophy

Đây là điểm rất quan trọng.

Axiom safe code đã có:

```text
type checker
ownership verifier
view verifier
concurrency verifier
```

Do đó không nên copy mô hình:

> mọi memory safety đều để runtime sanitizer phát hiện.

Thay vào đó:

```text
Compile-time
    ↓
safe memory guarantees

Runtime sanitizer
    ↓
unsafe / FFI / platform boundary
```

---

# 32. Address sanitizer

`--sanitize=address`

có thể instrument:

```text
raw pointer
unsafe memory
FFI buffer
allocation
stack/heap boundaries
```

Phát hiện:

- use-after-free
- out-of-bounds
- double free
- invalid raw access.

---

# 33. Safe code vẫn có thể chạy sanitizer

Được.

Nhưng compiler có thể loại bỏ checks mà static proof đã chứng minh không cần.

Ví dụ:

```axiom
for x in view {
    sum += x
}
```

nếu bounds proven:

```text
no runtime bounds sanitizer needed
```

---

# 34. Undefined behavior sanitizer

Axiom nên tránh khái niệm UB trong safe language.

Thay vào đó:

```text
--sanitize=invalid
```

kiểm tra:

- invalid unsafe cast
- invalid alignment
- invalid enum representation
- invalid pointer operation
- integer intrinsic preconditions
- FFI contract violations.

---

# 35. Thread sanitizer

```text
--sanitize=thread
```

có thể phát hiện:

```text
data race
```

trong các phần:

```text
unsafe
FFI
foreign synchronization
```

Safe Axiom race prevention vẫn là compile-time guarantee.

---

# 36. Leak sanitizer

Axiom deterministic ownership nên hạn chế leak trong safe ownership model.

Nhưng leak vẫn có thể xảy ra qua:

```text
unsafe
FFI
intentional global lifetime
process exit
```

Tool:

```text
--sanitize=leak
```

hữu ích để debug.

---

# 37. FFI sanitizer

Đây là thứ rất đáng có.

Ví dụ C trả:

```text
ptr + len
```

Axiom wrapper có contract:

```text
valid(ptr, len)
```

Sanitizer có thể kiểm tra runtime trong debug.

---

# 38. Unsafe boundary instrumentation

Architecture:

```text
Safe Axiom
     ↓
unsafe boundary
     ↓
runtime validation
     ↓
raw machine operation
```

Debug build có thể thêm checks.

Release:

```text
validation erased
```

nếu programmer không yêu cầu giữ.

---

# 39. Bounds checks

Safe indexing:

```axiom
a[i]
```

có semantic check.

Compiler:

```text
prove i < len
```

→ eliminate.

Nếu không chứng minh:

```text
runtime bounds check
```

Đây là **semantic safety check**, không phải sanitizer.

---

# 40. Check levels

Có thể có:

```text
debug
release
release-safe
release-fast
```

Nhưng cần cẩn thận.

Tôi không muốn:

```text
release-fast
```

biến safe semantics thành UB.

Chỉ được loại bỏ checks khi compiler chứng minh hoặc semantics cho phép.

---

# 41. `unsafe` không có nghĩa “tắt compiler”

Ví dụ:

```axiom
unsafe {
    *ptr
}
```

vẫn được compiler kiểm tra:

```text
type
alignment
instruction validity
ABI
```

nhưng programmer chịu trách nhiệm về:

```text
ptr validity
lifetime
aliasing
```

---

# 42. Static analyzer

Ngoài compiler verifier, có:

```text
axiom inspect
```

phân tích:

- allocation hot spots
- escape
- unnecessary copies
- unnecessary moves
- bounds checks
- failed vectorization
- dynamic dispatch
- heap allocation
- lock contention.

---

# 43. Đây là phần rất giá trị

Ví dụ:

```text
warning AX_PERF_0012:

Vec<Node> reallocates inside loop.

allocation count:
    147

suggestion:
    reserve estimated capacity before loop.
```

Đây không thay đổi semantics.

---

# 44. Copy diagnostics

Compiler có thể báo:

```text
AX_PERF_0007:
large value copied: Matrix<4096>

size: 64 KiB
```

và:

```text
suggestion:
consider view<Matrix<...>>
```

Không tự động biến thành view vì điều đó có thể thay semantic ownership.

---

# 45. Escape diagnostics

Ví dụ:

```text
AX_PERF_0021:
allocation escapes through FFI call
```

Compiler biết:

```text
LOCAL_ESCAPE
CALL_ESCAPE
RETURN_ESCAPE
FFI_ESCAPE
```

đã định nghĩa trước.

---

# 46. Vectorization diagnostics

Đây sẽ liên kết với phần SIMD sau.

Ví dụ:

```text
AX_OPT_001:
loop not vectorized

reason:
    possible overlapping mutable regions
```

hoặc:

```text
AX_OPT_002:
loop vectorized
width: 8 lanes
```

Điều này rất quan trọng để đạt hiệu năng C/C++.

---

# 47. `axiom inspect`

Tôi muốn một lệnh thống nhất:

```text
axiom inspect foo
```

có thể hiển thị:

```text
type
layout
size
alignment
ABI
ownership
effects
generated code
```

Ví dụ:

```text
axiom inspect Vec<i32>
```

→

```text
semantic:
    owned dynamic contiguous sequence

layout:
    target optimized

size:
    24 bytes

alignment:
    8

copy:
    no

drop:
    yes

relocation:
    may relocate
```

---

# 48. Inspect generated code

```text
axiom inspect --asm foo
```

hoặc:

```text
axiom dump-machine foo
```

cho:

```asm
mov eax, edi
add eax, esi
ret
```

---

# 49. Inspect MIR

Đã có:

```text
axiom dump-mir
axiom dump-verified-mir
```

Tôi đề xuất thêm:

```text
axiom dump-lir
axiom dump-machine
```

Pipeline debug hoàn chỉnh:

```text
Source
 ↓
AST
 ↓
HIR
 ↓
Typed HIR
 ↓
MIR
 ↓
Verified MIR
 ↓
LIR
 ↓
Machine IR
 ↓
Object
```

---

# 50. Compiler explanation mode

Đây là tính năng đặc biệt hữu ích cho Axiom và AI-assisted development.

```text
axiom explain file.axiom:42
```

Ví dụ:

```text
variable `x` moved here

ownership:
    x: OWNED
    ↓
    argument transfer
    ↓
    x: MOVED

reason:
    type File is not Copy
```

Không cần bắt programmer học lifetime calculus.

---

# 51. Structured diagnostics

Compiler output không chỉ là text.

Internally:

```text
Diagnostic {
    code
    severity
    message
    primary_span
    secondary_spans
    notes
    suggestions
    semantic_context
}
```

Có thể output:

```text
--diagnostic-format=json
```

---

# 52. Đây cực kỳ quan trọng cho AI

AI coding agent có thể nhận:

```json
{
  "code": "AX_MOVE_0003",
  "span": "...",
  "reason": "..."
}
```

thay vì parse text compiler.

Axiom trở thành language rất phù hợp cho automated agents.

---

# 53. Machine-readable fix

Compiler có thể cung cấp:

```text
suggestion:
    replace `x.foo()` with `foo(view(x))`
```

Nhưng compiler **không tự sửa source** nếu semantic intent không chắc chắn.

Tool:

```text
axiom fix
```

chỉ áp dụng fixes có:

```text
machine_applicable = true
```

---

# 54. Formatter

```text
axiom fmt
```

phải deterministic.

Không có config format quá phức tạp.

Tôi đề xuất:

```text
axiomfmt
```

là một phần toolchain chính.

---

# 55. Documentation generator

```text
axiom doc
```

đọc:

```text
pub
doc comments
traits
functions
types
examples
```

và tạo documentation.

---

# 56. Benchmark

```text
axiom bench
```

không nên chỉ đo wall-clock.

Có thể thu:

```text
time
CPU cycles
instructions
allocations
branches
cache misses
```

nếu platform hỗ trợ.

---

# 57. Benchmark result format

Machine-readable:

```text
.axbench
```

Ví dụ:

```text
benchmark: matrix_mul
iterations: 10000
mean_ns: ...
p50_ns: ...
p95_ns: ...
allocations: 0
```

---

# 58. Regression detection

Tool có thể:

```text
axiom bench --compare baseline.axbench
```

và báo:

```text
performance regression
```

nhưng không làm compilation fail mặc định.

CI có thể đặt threshold.

---

# 59. Tracing

`axiom trace` khác profiler.

Profiler hỏi:

> CPU đang ở đâu?

Trace hỏi:

> chương trình đã làm gì theo thời gian?

Event:

```text
CALL
RETURN
ALLOC
DROP
LOCK
UNLOCK
SPAWN
AWAIT
RESUME
ATOMIC
IO
```

Ta đã có `EventLog` trong Semantic Oracle.

---

# 60. Oracle → Trace

Đây là một thiết kế rất mạnh:

```text
Semantic Oracle
      ↓
EventLog
      ↓
axiom trace
```

Debug execution có thể so sánh:

```text
Oracle trace
vs
Native trace
```

---

# 61. Differential execution

Ví dụ compiler optimization bug:

```text
Source
 ↓
Oracle
 ↓
expected result

Source
 ↓
O2 native
 ↓
actual result
```

Nếu khác:

```text
compiler bug
```

Đây nên trở thành testing infrastructure chính thức.

---

# 62. Sanitizer + Oracle

Có thể:

```text
Oracle
 ↓
semantic execution
```

và:

```text
Native sanitizer
 ↓
runtime execution
```

so sánh.

Đặc biệt hữu ích cho:

- ownership
- drop
- async
- atomics
- FFI.

---

# 63. Tooling architecture

```text
                     Axiom Driver
                          │
        ┌─────────────────┼─────────────────┐
        ↓                 ↓                 ↓
    Compiler           Debugger          Profiler
        │                 │                 │
        ↓                 ↓                 ↓
      Build             DAP              Sampling
        │
 ┌──────┼────────┐
 ↓      ↓        ↓
Test  Bench   Sanitizer
```

Tất cả dùng chung:

```text
Target
Diagnostics
DebugInfo
BuildGraph
SourceMap
Artifact
```

---

# 64. Tooling không được kéo runtime vào release

Ví dụ:

```text
axiom build --release
```

không tự link:

```text
debug runtime
profiler runtime
sanitizer runtime
```

trừ khi profile yêu cầu.

---

# 65. Sanitizer là capability

Conceptually:

```text
Normal:
    no sanitizer

ASAN:
    memory instrumentation

TSAN:
    concurrency instrumentation

UB-like:
    unsafe contract instrumentation

Leak:
    allocation instrumentation
```

Mỗi cái là optional.

---

# 66. Developer tooling invariants

```text id="j4h8n2"
ATOOL-01  Tooling Does Not Become Mandatory Runtime
ATOOL-02  Compiler Diagnostics Are Structured
ATOOL-03  Diagnostics Have Stable Codes
ATOOL-04  Diagnostics Preserve Source Context
ATOOL-05  Machine-Readable Diagnostics Are Supported
ATOOL-06  Debug Info Is Non-Semantic
ATOOL-07  Optimized Variables May Be Unavailable
ATOOL-08  Ownership State May Be Exposed In Debug Builds
ATOOL-09  View Provenance May Be Exposed In Debug Builds
ATOOL-10  Async State May Be Exposed In Debug Builds
ATOOL-11  Sampling Profiling Has Low Default Overhead
ATOOL-12  Instrumentation Is Explicit
ATOOL-13  PGO Does Not Change Semantics
ATOOL-14  Allocation Profiling Is Optional
ATOOL-15  Sanitizers Are Optional
ATOOL-16  Safe Memory Guarantees Primarily Come From Compilation
ATOOL-17  Sanitizers Primarily Strengthen Unsafe/FFI/Platform Debugging
ATOOL-18  Bounds Checks May Be Eliminated Only When Proven Safe
ATOOL-19  Unsafe Does Not Disable All Compiler Verification
ATOOL-20  Trace Uses Structured Events
ATOOL-21  Oracle Can Produce Reference Traces
ATOOL-22  Native Execution Can Be Differentially Tested
ATOOL-23  MIR/LIR/Machine Dumps Are First-Class
ATOOL-24  Performance Diagnostics Are Non-Semantic
ATOOL-25  Formatter Is Deterministic
ATOOL-26  Benchmark Data Is Machine-Readable
ATOOL-27  Debugger Supports Standard Debug Adapter Protocol
ATOOL-28  Tooling Does Not Require LLVM
```

---

# 67. Một điểm rất đáng giữ cho Axiom

Chúng ta đang hình thành một mô hình khá khác Rust/C++:

```text
             C/C++
               │
      Runtime / UB / Tools
               │
        programmer burden


             Axiom
               │
      ┌────────┴────────┐
      │                 │
 Compile-time        Explicit unsafe
 guarantees          boundaries
      │                 │
      └────────┬────────┘
               ↓
        Native machine code
```

Mục tiêu không phải là:

> “kiểm tra mọi thứ runtime”.

Mà là:

> **đưa càng nhiều correctness càng tốt vào compile-time, nhưng không bắt programmer phải viết một hệ thống lifetime/borrow phức tạp để đạt được điều đó.**

Đây chính là nơi triết lý ban đầu của Axiom — **Compiler Complexity Is Not Language Complexity** — phát huy rõ nhất.

---

# 68. Một invariant quan trọng cần thêm

Tôi đề xuất thêm vào core architecture:

```text
ACOMP-XX — Verification/Optimization Separation

Semantic verification must complete before
optimization is permitted to erase information
required to establish language correctness.
```

Nói cách khác:

```text
Typed MIR
   ↓
VERIFY
   ↓
VERIFIED MIR
   ↓
OPTIMIZE
```

chứ không:

```text
Typed MIR
   ↓
aggressive optimization
   ↓
hope verifier can understand optimized result
```

Điều này giúp compiler architecture rất sạch.

---

# Tiếp tục → SIMD, Vectorization & Data-Oriented Computing

Bây giờ mới đến phần **hiệu năng CPU thực sự**.

Ta sẽ thiết kế:

```text
Scalar
  ↓
Auto-vectorization
  ↓
Vector<T,N>
  ↓
Mask<T,N>
  ↓
SIMD operations
  ↓
LIR vector instructions
  ↓
AVX2 / AVX-512 / NEON / SVE / RVV / WASM SIMD
```

đồng thời giải quyết một vấn đề rất quan trọng:

> **Làm thế nào để Axiom đạt hiệu năng C/C++ trong các workload data-oriented mà không bắt lập trình viên viết hàng đống intrinsic CPU-specific?**

Phần đó sẽ nối trực tiếp với memory model, `view`, alias analysis, alignment và optimizer mà chúng ta đã chốt.