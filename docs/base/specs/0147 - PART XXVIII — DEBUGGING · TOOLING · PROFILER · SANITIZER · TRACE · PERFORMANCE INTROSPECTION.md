# PART XXVIII — DEBUGGING · TOOLING · PROFILER · SANITIZER · TRACE · PERFORMANCE INTROSPECTION

Part XXVIII khóa lớp **quan sát và chẩn đoán chương trình** của Axiom.

Mục tiêu quan trọng nhất:

> **Debugging và profiling phải giúp nhìn thấy semantics và hiệu năng của chương trình, nhưng không được trở thành một phần bắt buộc của semantics hoặc runtime.**

Vì vậy Axiom tiếp tục áp dụng nguyên tắc:

> **Explicit at semantic boundaries, implicit within the compiler.**

và thêm một nguyên tắc cho tooling:

> **Observation Must Not Redefine Semantics.**

---

# 1. Mô hình tổng thể

Tooling của Axiom không được thiết kế như một tập công cụ rời rạc.

Nó dựa trên cùng một semantic model:

```text
Source
  │
  ├── AST
  ├── HIR
  ├── Typed HIR
  ├── MIR
  ├── Verified MIR
  ├── LIR
  └── Machine IR
        │
        ├── Debug Info
        ├── Trace Info
        ├── Profile Info
        ├── Coverage Info
        └── Sanitizer Info
```

Do đó:

```text
Compiler Semantics
       │
       ├── Debugger
       ├── Inspector
       ├── Profiler
       ├── Tracer
       ├── Sanitizer
       ├── Coverage
       └── Benchmark
```

Tất cả đều quan sát **cùng một chương trình**.

Không được có:

```text
compiler semantics ≠ debugger semantics
compiler semantics ≠ profiler semantics
compiler semantics ≠ LSP semantics
```

---

# 2. Debug information

Debug information là metadata mô tả quan hệ:

```text
Source
  ↓
AST
  ↓
HIR
  ↓
MIR
  ↓
LIR
  ↓
Machine instruction
```

Ví dụ:

```text
main.axiom:42
      ↓
HIR node #183
      ↓
MIR value %27
      ↓
LIR vreg %9
      ↓
x86 instruction 0x4012A4
```

Compiler phải có khả năng duy trì mapping này khi khả thi.

Không yêu cầu mọi machine instruction đều có mapping hoàn hảo.

---

# 3. Debug location

Mỗi instruction có thể mang:

```text
DebugLocation {
    file
    line
    column
    span
    inline_stack
}
```

`inline_stack` rất quan trọng.

Ví dụ:

```text
main()
  → Vec.push()
      → Buffer.reserve()
          → allocator.allocate()
```

Nếu compiler inline toàn bộ:

```text
main → machine code
```

debugger vẫn có thể hiển thị logical call stack:

```text
main
Vec.push
Buffer.reserve
allocator.allocate
```

mặc dù machine code thực tế không có các function frame tương ứng.

---

# 4. Debug level

Axiom có các mức debug:

```text
-O0
-Og
-O1
-O2
-O3
-Os
-Oz
```

Ý nghĩa chính:

### `-O0`

Tối ưu tối thiểu.

Ưu tiên:

- debug dễ dàng
- mapping source tốt
- biến dễ quan sát
- machine code gần với MIR

### `-Og`

Tối ưu nhưng vẫn ưu tiên khả năng debug.

Đây là profile mặc định cho phát triển lâu dài.

### `-O1`

Tối ưu cơ bản.

### `-O2`

Tối ưu production thông thường.

### `-O3`

Tối ưu hiệu năng mạnh.

Có thể:

- aggressive inlining
- vectorization
- loop transformation
- specialization
- devirtualization
- scalar replacement

### `-Os`

Tối ưu kích thước.

### `-Oz`

Tối ưu kích thước cực mạnh.

---

# 5. Optimization không thay đổi semantics

Đây là invariant cực kỳ quan trọng:

```text
-O0
-Og
-O1
-O2
-O3
-Os
-Oz
```

phải giữ cùng observable semantics.

Ví dụ:

```axiom
var x = 10
x += 20
print(x)
```

Không được xảy ra:

```text
-O0 → 30
-O3 → 29
```

chỉ vì optimizer.

Debug information có thể khác.

Machine layout có thể khác.

Performance có thể khác.

Nhưng semantics không được khác.

---

# 6. Optimized debugging

Một biến có thể:

```text
- nằm trong register
- bị constant-fold
- bị scalarized
- bị merge
- bị eliminate
- tồn tại ở nhiều register khác nhau
- không còn tồn tại vật lý
```

Ví dụ:

```axiom
let x = 10
let y = x + 20
print(y)
```

Optimizer có thể biến thành:

```text
print(30)
```

Debugger không được giả vờ rằng có một memory slot thật cho `x`.

Thay vào đó debugger có thể báo:

```text
x = 10
location = constant
```

hoặc:

```text
x = unavailable (optimized out)
```

Đây là khác biệt quan trọng:

> **Debug information mô tả trạng thái có thể quan sát được, không tạo ra state giả để phục vụ debugger.**

---

# 7. Variable location

Debug info có thể biểu diễn:

```text
Location =
    Register(RAX)
    Stack(offset)
    Constant(value)
    Expression(...)
    Multiple(...)
    Unavailable
```

Ví dụ một biến chuyển từ:

```text
RAX
```

sang:

```text
stack[rbp-16]
```

debugger vẫn biết đó là cùng một logical variable.

---

# 8. Inline function debugging

Axiom compiler phải hỗ trợ:

```text
logical function frame
```

khác với:

```text
physical machine frame
```

Ví dụ:

```axiom
fn square(x: i32) -> i32 {
    x * x
}

fn main() {
    let x = square(10)
}
```

Optimizer có thể inline:

```text
main:
    imul ...
```

Nhưng debugger vẫn có thể hiển thị:

```text
square(x=10)
main()
```

---

# 9. Debug formats

Axiom semantic debug model phải độc lập target.

Backend chuyển nó sang format native.

### Linux / ELF

Thông thường:

```text
DWARF
```

### Windows

```text
CodeView / PDB
```

### macOS / Mach-O

debug information phù hợp hệ sinh thái Darwin, thường dựa trên DWARF.

Điểm quan trọng:

```text
Axiom Debug Model
        ↓
Target Debug Format
```

không phải:

```text
Axiom semantics = DWARF
```

---

# 10. Debugger integration

Axiom không cần tự viết debugger hoàn chỉnh ở Core.

Compiler cung cấp:

```text
debug information
debug symbols
source mapping
type metadata
variable location metadata
inline metadata
ownership metadata
capability metadata
```

Debugger bên ngoài có thể sử dụng chúng.

CLI:

```bash
axiom debug program
```

có thể tích hợp debugger hệ thống.

---

# 11. Axiom-specific debugger information

Axiom có một lợi thế mà C/C++ debugger thông thường không có:

compiler hiểu:

```text
ownership
move state
drop state
capability
provenance
Send
Share
async state
```

Do đó debugger có thể hiển thị:

```text
x
type: Buffer
ownership: OWNED
state: LIVE
```

Hoặc:

```text
x
ownership: MOVED
moved_to: y
```

Hoặc:

```text
v
type: view<i32>
access: READ
owner: buffer
region: [128..256]
```

---

# 12. Ownership debugging

Ví dụ:

```axiom
let a = Buffer(...)
let b = a
```

Debugger có thể cho:

```text
a
  state: MOVED
  moved-to: b

b
  state: OWNED
```

Đây là **semantic debug information**, không phải runtime bookkeeping bắt buộc.

Release binary không cần lưu nó.

---

# 13. Capability debugging

Ví dụ:

```axiom
let data = Buffer(...)
let v = view(data)
```

Debugger:

```text
data
  ownership: OWNED

v
  capability:
      access: READ
      owner: data
      region: [0, 1024]
```

Nếu:

```axiom
let m = mut_view(data)
```

thì:

```text
m
  capability:
      access: WRITE
      owner: data
      region: [0, 1024]
```

---

# 14. `axiom inspect`

Đây là một trong những công cụ quan trọng nhất của Axiom.

Ví dụ:

```bash
axiom inspect --type User
```

```bash
axiom inspect --layout User
```

```bash
axiom inspect --ownership x
```

```bash
axiom inspect --capabilities
```

```bash
axiom inspect --traits User
```

```bash
axiom inspect --mir
```

```bash
axiom inspect --verified-mir
```

```bash
axiom inspect --abi User
```

```bash
axiom inspect --deps
```

---

# 15. Inspect type

Ví dụ:

```bash
axiom inspect --type Vec3
```

có thể trả:

```text
type: Vec3
kind: struct
size: 12
alignment: 4

fields:
    x: f32
    y: f32
    z: f32

copy: yes
drop: no
send: yes
share: yes
```

---

# 16. Inspect layout

```bash
axiom inspect --layout Vec3
```

```text
size      = 12
alignment = 4

x offset = 0
y offset = 4
z offset = 8
```

Nếu không có `@repr(C)`, compiler vẫn có quyền thay đổi layout giữa compiler versions.

Tool phải nói rõ:

```text
layout stability: compiler-defined
ABI stability: unstable
```

---

# 17. Inspect ownership

```bash
axiom inspect --ownership file.axiom:42
```

Ví dụ:

```text
x:
    type: Buffer
    state: OWNED

y:
    type: view<u8>
    access: READ
    owner: x
    region: [0, 128]
```

Đây sẽ đặc biệt hữu ích cho AI coding agents.

---

# 18. Inspect MIR

```bash
axiom inspect --mir foo
```

Ví dụ:

```text
%0 = CONST 10
%1 = CONST 20
%2 = ADD %0, %1
RETURN %2
```

Verified MIR:

```bash
axiom inspect --verified-mir foo
```

có thể bổ sung:

```text
ownership: valid
capabilities: valid
drops: complete
aliasing: valid
concurrency: valid
```

---

# 19. Trace system

Axiom có structured tracing.

Không phải:

```text
printf("something")
```

mà là semantic event:

```text
TraceEvent {
    timestamp
    thread
    task
    category
    event
    payload
}
```

Ví dụ:

```text
CALL
RETURN
ALLOC
DROP
LOCK
UNLOCK
SPAWN
JOIN
SEND
RECEIVE
AWAIT
RESUME
GPU_SUBMIT
GPU_COMPLETE
PANIC
```

---

# 20. Trace phải có zero-cost khi disabled

Đây là yêu cầu quan trọng.

Nếu chương trình không bật trace:

```text
trace disabled
```

compiler phải có thể loại bỏ toàn bộ trace machinery.

Không được mặc định có:

```text
global tracer
event queue
heap allocation
timestamp
runtime callback
```

chỉ vì chương trình được viết bằng Axiom.

---

# 21. Trace configuration

Ví dụ:

```bash
axiom run --trace
```

hoặc:

```bash
axiom run --trace=concurrency
```

```bash
axiom run --trace=alloc
```

```bash
axiom run --trace=async
```

```bash
axiom run --trace=gpu
```

Trace filtering càng sớm càng tốt:

```text
source
 ↓
semantic trace category
 ↓
compiler instrumentation
 ↓
machine code
```

Nếu category không cần thiết, compiler có thể loại bỏ instrumentation.

---

# 22. Structured trace cho AI

Trace không chỉ dành cho con người.

Ví dụ JSON:

```json
{
  "event": "DROP",
  "function": "process",
  "variable": "buffer",
  "type": "Buffer",
  "reason": "scope_exit"
}
```

AI agent có thể hiểu trực tiếp mà không phải parse log text.

Điều này phù hợp với kiến trúc:

```text
Compiler
    ↓
Structured Diagnostics
    ↓
Structured Trace
    ↓
Structured Profile
    ↓
AI Agent
```

---

# 23. Deterministic trace

Khi dùng:

```bash
axiom run --deterministic
```

Axiom có thể ghi:

```text
scheduler decisions
thread events
task suspension
channel operations
atomic synchronization
random seed
virtual time
```

để replay.

Ví dụ:

```bash
axiom replay trace.axtrace
```

Mục tiêu:

```text
same program
+ same inputs
+ same scheduler decisions
+ same external environment
=
same semantic execution
```

Điều này kết nối trực tiếp với **Semantic Oracle**.

---

# 24. Profiler

Profiler là lớp quan sát performance.

Axiom hỗ trợ:

```text
CPU
allocation
lock contention
async
thread
I/O
GPU
```

nhưng profiler không phải một phần của language runtime.

---

# 25. CPU profiling

Có hai mô hình:

### Sampling

Profiler định kỳ lấy stack:

```text
program
 ↓
sample
 ↓
stack
 ↓
symbol
 ↓
source
```

Ưu điểm:

- overhead thấp
- phù hợp production
- không cần instrument mọi function

### Instrumentation

Compiler chèn:

```text
ENTER function
EXIT function
```

Ưu điểm:

- timing chính xác hơn
- call counts
- function-level statistics

Nhược điểm:

- overhead lớn hơn

Người dùng chọn.

---

# 26. Allocation profiling

Axiom có thể ghi:

```text
allocation count
allocation size
allocation site
deallocation site
lifetime
allocator
```

Ví dụ:

```text
Buffer.push
    allocations: 1823
    bytes: 14.2 MB
    peak: 512 KB
```

Nhưng điều này **không có nghĩa mọi `Buffer` đều phải heap allocate**.

Profiler chỉ quan sát allocation thực tế sau lowering.

---

# 27. Lock contention profiling

Có thể đo:

```text
lock acquisition
wait duration
hold duration
contention count
```

Ví dụ:

```text
Mutex<Cache>

acquire: 1,200,000
contentions: 83,241
total wait: 4.2s
```

Không được biến profiler thành synchronization mechanism.

---

# 28. Async profiling

Async profiler hiểu:

```text
Task
Future
await
suspend
resume
executor
queue
wake
```

Có thể hiển thị:

```text
fetch()
 ├─ await socket.read()
 │     suspended: 12ms
 └─ parse()
       CPU: 0.8ms
```

Điều này giúp phân biệt:

```text
CPU-bound
```

với:

```text
waiting
```

---

# 29. GPU profiling

GPU profiler có thể theo dõi:

```text
kernel launch
queue
device transfer
synchronization
event
kernel duration
```

Ví dụ:

```text
add_kernel
    launch: 4.1 μs
    execution: 82 μs
    transfer-in: 11 μs
    transfer-out: 9 μs
```

Hardware-specific counters thuộc target/backend layer.

---

# 30. Hardware performance counters

Axiom có API profiler abstraction:

```text
CpuCounter
GpuCounter
```

nhưng không đưa counter cụ thể vào Core language.

Ví dụ:

```text
instructions
cycles
branches
branch misses
cache misses
vector instructions
```

là target-dependent.

Compiler/tool có thể sử dụng OS/hardware facilities.

---

# 31. PGO

Axiom hỗ trợ Profile-Guided Optimization.

Flow:

```text
Source
  ↓
instrumented build
  ↓
run workload
  ↓
profile data
  ↓
optimized build
```

Ví dụ:

```bash
axiom build --profile=generate
axiom profile run
axiom build --profile=use
```

PGO có thể ảnh hưởng:

- inlining
- code layout
- branch prediction
- hot/cold splitting
- specialization
- function ordering

nhưng không được thay đổi semantics.

---

# 32. Sanitizer

Sanitizer là instrumentation để phát hiện lỗi mà compiler semantics bình thường đã định nghĩa hoặc cấm.

Các nhóm:

```text
memory
bounds
undefined-operation
ownership
capability
race
thread
integer
```

---

# 33. Address sanitizer

Axiom có thể cung cấp ASan-like mode:

```bash
axiom build --sanitize=address
```

Phát hiện:

```text
use-after-free
out-of-bounds
invalid access
double release
```

Nhưng khác với C/C++:

> Safe Axiom code vốn đã phải ngăn các lỗi ownership/lifetime tương ứng.

Vì vậy sanitizer đặc biệt hữu ích cho:

```text
unsafe
FFI
raw pointers
external memory
custom allocators
```

---

# 34. Undefined behavior sanitizer

Ví dụ:

```text
invalid shift
invalid alignment
integer operation
invalid enum state
unreachable condition
```

Axiom cố gắng định nghĩa nhiều hành vi mà C để UB.

Do đó UBSan của Axiom không được dùng như cách “bổ sung semantics còn thiếu”.

Nó chủ yếu phát hiện:

```text
unsafe contract violations
target-specific invalid states
implementation errors
```

---

# 35. Thread sanitizer

```bash
axiom build --sanitize=thread
```

Có thể phát hiện:

```text
unsafe data race
invalid synchronization
atomic misuse
```

Safe code vẫn phải giữ invariant:

```text
safe code cannot create data races
```

TSan không thay thế compiler verifier.

---

# 36. Ownership sanitizer

Đây là một điểm Axiom có thể mạnh hơn các ngôn ngữ truyền thống.

Trong debug build compiler có thể instrument:

```text
MOVE
DROP
VIEW_CREATE
VIEW_END
OWNER_END
```

Ví dụ:

```text
owner destroyed
while capability still active
```

sẽ tạo diagnostic runtime/debug nếu vấn đề chỉ xuất hiện ở boundary mà static analysis không thể chứng minh.

Tuy nhiên:

> Đây không được là cơ chế ownership runtime bắt buộc.

Release build có thể loại bỏ toàn bộ.

---

# 37. Capability sanitizer

Có thể kiểm tra runtime các invariant:

```text
capability owner alive
region valid
access valid
no conflicting mutable capability
no use-after-relocation
```

Đặc biệt hữu ích cho:

```text
unsafe → safe capability
FFI
device memory
external buffers
```

---

# 38. Debug assertions vs sanitizer

Hai thứ phải phân biệt.

### `debug_assert`

Do programmer viết:

```axiom
debug_assert(x >= 0)
```

Có thể biến mất ở release.

### Sanitizer

Do compiler/tooling chèn:

```text
runtime verification instrumentation
```

Có thể bật riêng:

```bash
--sanitize=memory
--sanitize=ownership
--sanitize=thread
```

Không được coi sanitizer là semantics.

---

# 39. Panic report

Khi panic:

```text
PANIC
```

debug build có thể tạo:

```text
PanicReport {
    message
    source_location
    stack
    thread
    task
    async_state
    registers?
    ownership_state?
    capability_state?
}
```

Ví dụ:

```text
panic: index out of bounds

at:
    parser.axiom:182

stack:
    parse
    compile
    main
```

Ownership/capability state chỉ được ghi nếu instrumentation/debug metadata tồn tại.

---

# 40. Stack trace

Stack trace phải hỗ trợ cả:

```text
physical stack
```

và:

```text
logical inline stack
```

để không mất thông tin khi optimizer inline function.

Async cần thêm logical task stack vì:

```text
await
```

có thể làm physical stack biến mất.

---

# 41. Coverage

Axiom hỗ trợ:

```bash
axiom coverage
```

có thể đo:

```text
line coverage
branch coverage
function coverage
match-arm coverage
```

Quan trọng hơn, Axiom có thể đo semantic coverage:

```text
match variant coverage
panic path coverage
error path coverage
trait implementation coverage
comptime branch coverage
```

nhưng semantic coverage là tooling layer, không phải language semantics.

---

# 42. Fuzzing

Axiom fuzzing phải tích hợp compiler + Oracle.

Flow:

```text
Generator
    ↓
Axiom program/input
    ↓
Oracle
    ↓
Native optimized build
    ↓
Compare
```

Có thể tìm:

```text
compiler bugs
optimizer bugs
backend bugs
ownership verifier bugs
ABI bugs
```

Một testcase làm compiler sai phải trở thành regression test.

---

# 43. Benchmarking

Benchmark không được đơn giản là:

```text
start timer
run once
stop timer
```

Axiom benchmark tool phải hỗ trợ:

```text
warmup
multiple iterations
statistical distribution
outlier detection
CPU affinity
frequency information
allocation statistics
```

Ví dụ:

```bash
axiom bench
```

kết quả:

```text
benchmark: hash_map_insert

iterations: 100000
median:     42 ns
p90:        45 ns
p99:        51 ns
```

Không nên chỉ báo một con số duy nhất.

---

# 44. Benchmark semantics

Benchmark framework phải tránh tối ưu bỏ toàn bộ workload.

Ví dụ:

```axiom
fn benchmark() {
    let x = expensive()
}
```

Nếu `x` không observable, optimizer có thể loại bỏ.

Đó là **đúng**.

Benchmark phải dùng một cơ chế:

```text
black_box(x)
```

hoặc tương đương compiler intrinsic.

`black_box` tạo observable boundary cần thiết cho benchmark nhưng không biến toàn bộ optimizer thành vô hiệu.

---

# 45. Performance introspection

Compiler có thể cung cấp:

```bash
axiom profile
```

và:

```bash
axiom inspect --cost
```

Ví dụ:

```text
function: process

allocations: 0
heap allocations: 0
calls: 4
inlined calls: 7
vectorized loops: 2
branches: 8
dynamic dispatch: 0
bounds checks:
    eliminated: 14
    remaining: 1
```

Đây là **compiler analysis**, không phải runtime measurement.

---

# 46. Allocation elimination report

Một tính năng rất hữu ích:

```bash
axiom inspect --allocations
```

Ví dụ:

```text
Buffer allocation #1
    source: foo.axiom:42
    status: eliminated
    reason:
        address not observable
        lifetime local
        scalar replacement possible
```

Hoặc:

```text
allocation #2
    status: retained
    reason:
        stable address required
```

Điều này trực tiếp phản ánh triết lý:

> Storage strategy is not ordinary value semantics.

---

# 47. View/relocation diagnostics

Compiler có thể báo:

```text
Vec storage may relocate here
```

khi programmer cố tạo capability không hợp lệ.

Ví dụ:

```axiom
let v = view(buffer)
buffer.push(x)
```

Nếu `push` có thể relocate storage, verifier có thể phát hiện conflict.

Diagnostic:

```text
AX_VIEW_0012

cannot mutate relocatable storage while a dependent view is live

help:
    end the view before mutation
```

---

# 48. Trace + Oracle

Một điểm kiến trúc rất quan trọng:

```text
Oracle EventLog
```

và:

```text
Production Trace
```

không nhất thiết giống byte-for-byte.

Nhưng chúng có thể chia sẻ **semantic event vocabulary**:

```text
CALL
MOVE
DROP
ALLOC
PANIC
ATOMIC
SPAWN
SEND
RECEIVE
SUSPEND
RESUME
```

Điều này cho phép:

```text
Oracle
      ↕
semantic trace
      ↕
native execution
```

và differential testing mạnh hơn.

---

# 49. Instrumentation không được thay đổi semantics

Mọi instrumentation phải thỏa:

```text
P
P + instrumentation
```

có cùng language semantics, ngoại trừ:

```text
observable tooling output
```

Ví dụ profiler không được làm:

```text
race-free → race
```

hay:

```text
valid lifetime → invalid lifetime
```

Nếu instrumentation làm thay đổi scheduling, công cụ phải ghi rõ đó là một **instrumented execution environment**.

---

# 50. Timing-sensitive programs

Profiler/instrumentation có thể thay đổi:

```text
timing
cache behavior
thread scheduling
```

Do đó profile data không phải semantics.

Compiler phải phân biệt:

```text
semantic execution
```

với:

```text
instrumented performance observation
```

Không được dùng profiler để kết luận:

> “chương trình này có semantics khác”.

---

# 51. Typed attributes

Các attribute tooling có thể có:

```axiom
@no_debug
@trace
@profile
@sanitize
```

Nhưng attribute phải có schema rõ ràng.

Ví dụ:

```axiom
@trace("alloc")
fn create_buffer() -> Buffer {
    ...
}
```

Compiler biết:

```text
attribute kind
arguments
allowed target
semantic effect
tooling effect
```

Không có attribute tùy tiện kiểu:

```text
@magic("do whatever")
```

---

# 52. Release erasure

Một mục tiêu quan trọng:

```text
Debug build
    ↓
many metadata/instrumentation

Release build
    ↓
only required machine semantics
```

Nếu không dùng:

```text
debug metadata
trace
sanitizer
coverage
profiler
```

thì compiler phải loại bỏ chúng.

Đây chính là **Abstraction Erasure** áp dụng cho tooling.

---

# 53. Không có hidden profiler runtime

Không được có:

```text
axiom_runtime::profiler
```

tự động nhúng vào mọi executable.

Thay vào đó:

```text
normal build
    → no profiler runtime

profile build
    → explicitly linked instrumentation/profile components
```

---

# 54. Tooling CLI chuẩn

Bộ CLI chuẩn:

```bash
axiom check
axiom build
axiom run
axiom test
axiom bench

axiom debug
axiom inspect
axiom trace
axiom profile
axiom coverage

axiom replay
axiom symbolize
```

Trong đó:

```text
check      → semantic checking
build      → compilation
debug      → debugger integration
inspect    → semantic/compiler introspection
trace      → structured execution trace
profile    → performance analysis
coverage   → test/code coverage
replay     → deterministic execution replay
symbolize  → address → source/stack information
```

---

# 55. Machine-readable tooling

Mọi công cụ quan trọng đều có:

```bash
--format=json
```

Ví dụ:

```bash
axiom inspect --ownership --format=json
```

```bash
axiom profile --format=json
```

```bash
axiom trace --format=json
```

```bash
axiom coverage --format=json
```

AI agent không cần parse text terminal.

---

# 56. Tooling API

Có thể định nghĩa chung:

```text
ToolEvent
ToolResult
ToolDiagnostic
ToolArtifact
```

Ví dụ:

```text
ProfileResult
TraceResult
CoverageResult
InspectionResult
```

Tooling trở thành một API machine-readable ổn định.

---

# 57. Compiler performance report

Compiler itself cũng cần profiling.

```bash
axiom compiler-profile build
```

Có thể hiển thị:

```text
parse             120 ms
name resolution    80 ms
type checking     310 ms
trait solving      95 ms
MIR               140 ms
verification      220 ms
optimization      480 ms
codegen            90 ms
object writer      12 ms
```

Đặc biệt quan trọng cho Axiom vì compiler có ownership/capability analysis mạnh.

---

# 58. Không để verifier thành bottleneck cố định

Compiler có thể:

```text
cache
incremental verification
reuse proofs
parallelize analysis
```

Nhưng semantic correctness vẫn giữ nguyên.

Ví dụ:

```text
Verified MIR
    ↓
cache
```

Nếu source semantic fingerprint không đổi, compiler có thể tái sử dụng kết quả.

---

# 59. Debug metadata không được ảnh hưởng ABI

Debug build có thể có rất nhiều metadata.

Nhưng:

```text
debug metadata
```

không được vô tình trở thành:

```text
runtime object header
```

hoặc:

```text
ABI field
```

Trừ khi programmer explicitly yêu cầu runtime metadata.

---

# 60. Performance information phải phân biệt 3 tầng

Axiom tooling phân biệt:

### Static compiler facts

```text
inlined = yes
allocation eliminated = yes
bounds check eliminated = yes
```

### Dynamic observations

```text
CPU = 2.1 ms
allocations = 300
cache misses = ...
```

### Semantic guarantees

```text
no data race
view lifetime valid
drop complete
```

Không được trộn ba loại này.

Ví dụ:

```text
"0 allocations"
```

là observation của một build/run cụ thể.

Không phải semantic guarantee của function.

---

# 61. Debugger + optimizer contract

Debugger phải chấp nhận:

```text
variable optimized out
```

và:

```text
call stack partially reconstructed
```

thay vì compiler hy sinh optimization chỉ để debugger đẹp hơn.

`-Og` dành cho trường hợp cần debug tốt.

`-O3` ưu tiên performance.

---

# 62. Sanitizer + unsafe boundary

Đây là nơi sanitizer đặc biệt quan trọng.

Ví dụ:

```axiom
unsafe {
    let p = ...
    ...
}
```

Compiler vẫn kiểm tra phần có thể kiểm tra.

Sanitizer có thể kiểm tra runtime:

```text
alignment
bounds
lifetime
initialization
provenance
```

Nhưng không được coi:

```text
unsafe
```

là:

```text
anything goes
```

---

# 63. FFI sanitizer

FFI wrapper có thể bật instrumentation:

```text
foreign allocation
foreign free
foreign callback
foreign thread
foreign pointer
```

Ví dụ phát hiện:

```text
Axiom view points into memory freed by C library
```

Đây là lỗi rất khó phát hiện bằng ownership checker thuần compile-time.

---

# 64. GPU debugging

GPU tooling có:

```text
kernel source mapping
device variable mapping
buffer ownership
launch configuration
device event trace
```

Ví dụ:

```text
kernel add
source: vector.axiom:88
thread: 142
buffer: DeviceBuffer<f32>
```

GPU sanitizer có thể kiểm tra:

```text
out-of-bounds
address-space mismatch
invalid synchronization
invalid device lifetime
```

nhưng target-specific.

---

# 65. Conformance của tooling

Tooling cũng phải được test.

Ví dụ:

```text
source
→ expected diagnostic
→ expected ownership state
→ expected MIR
→ expected trace
```

Có thể có:

```text
golden diagnostics
golden MIR
golden trace
golden profile schema
```

Nhưng performance numbers tuyệt đối không nên là golden test vì phụ thuộc máy.

---

# 66. Những gì KHÔNG được trở thành Core semantics

Các thứ sau **không phải language semantics**:

```text
debugger
profiler
sanitizer
coverage
trace
benchmark
DWARF
PDB
CPU counters
GPU profiling APIs
```

Chúng quan sát semantics.

Không ngược lại.

---

# 67. Invariants Part XXVIII

## Tooling

**ATOOL-20 — Tooling Observes Language Semantics**

Tooling không định nghĩa semantics.

**ATOOL-21 — Debug Information Is Metadata**

Debug metadata không phải runtime semantic state.

**ATOOL-22 — Debugging Does Not Require Runtime Instrumentation**

Program có thể debug mà không cần global runtime bắt buộc.

**ATOOL-23 — Debug Metadata May Be Erased**

Release build có thể loại bỏ debug metadata.

**ATOOL-24 — Optimized Debugging May Report Unavailable Values**

Compiler không tạo state giả chỉ để debugger.

**ATOOL-25 — Logical Frames May Differ From Physical Frames**

Inlining/coroutine lowering không làm mất logical source identity.

**ATOOL-26 — Inspect Uses Compiler Semantic State**

`axiom inspect` không tự xây một type system khác.

**ATOOL-27 — Tool Output Is Machine Readable**

Các tooling API quan trọng phải hỗ trợ structured output.

**ATOOL-28 — Tooling Does Not Redefine ABI**

Debug metadata không thay đổi ABI nếu không được yêu cầu.

---

## Trace

**ATRACE-20 — Trace Events Are Structured**

**ATRACE-21 — Trace Is Optional**

**ATRACE-22 — Disabled Trace Has No Required Runtime Cost**

**ATRACE-23 — Trace Does Not Redefine Semantics**

**ATRACE-24 — Trace Categories Are Explicit**

**ATRACE-25 — Trace Can Represent Semantic Execution Events**

**ATRACE-26 — Deterministic Trace Can Support Replay**

**ATRACE-27 — Replay Requires Explicitly Controlled External Inputs**

**ATRACE-28 — Trace Instrumentation May Affect Timing**

**ATRACE-29 — Timing Effects Are Not Language Semantics**

---

## Profiling

**APROF-20 — Profiling Is Optional**

**APROF-21 — Sampling And Instrumentation Are Distinct**

**APROF-22 — Profiling Does Not Define Semantics**

**APROF-23 — Allocation Profiles Observe Actual Lowered Storage**

**APROF-24 — Compiler Allocation Elimination Is Distinct From Runtime Allocation Counting**

**APROF-25 — Async Profiling Distinguishes Suspension From CPU Execution**

**APROF-26 — Lock Profiling Observes Synchronization**

**APROF-27 — GPU Profiling Is Target-Specific**

**APROF-28 — Hardware Counters Are Platform-Specific**

**APROF-29 — PGO Cannot Change Program Semantics**

**APROF-30 — Profile Data Is Not A Semantic Guarantee**

---

## Sanitizer

**ASAN-20 — Sanitizers Are Optional Instrumentation**

**ASAN-21 — Sanitizers Do Not Replace Static Safety Verification**

**ASAN-22 — Sanitizers May Instrument Unsafe Boundaries**

**ASAN-23 — Sanitizers May Instrument FFI Boundaries**

**ASAN-24 — Sanitizer Instrumentation Does Not Define Core Semantics**

**ASAN-25 — Address Checks Are Distinct From Ownership Proofs**

**ASAN-26 — Race Detection Is Distinct From Atomic Semantics**

**ASAN-27 — Capability Checking May Be Instrumented**

**ASAN-28 — Sanitizer Runtime Is Not Mandatory**

**ASAN-29 — Release Builds May Remove Sanitizer Instrumentation**

---

## Benchmark

**ABENCH-20 — Benchmark Results Are Measurements**

**ABENCH-21 — Benchmarking Requires Warmup Where Appropriate**

**ABENCH-22 — Benchmarking Uses Multiple Samples**

**ABENCH-23 — Benchmark Statistics Must Represent Distribution**

**ABENCH-24 — Optimizer Cannot Be Defeated By Accident**

**ABENCH-25 — Black-Box Boundaries Are Explicit**

**ABENCH-26 — Benchmark Results Are Not Language Guarantees**

---

# 68. Kiến trúc cuối Part XXVIII

Toàn bộ hệ thống hiện tại:

```text
                 AXIOM SEMANTIC MODEL
                         │
          ┌──────────────┼──────────────┐
          │              │              │
       Compiler        Oracle        Tooling
          │              │              │
          │              │        ┌─────┼─────┐
          │              │        │     │     │
          │              │      Debug Trace Profile
          │              │        │     │     │
          │              │      Sanitizer Coverage
          │              │        │     │
          │              │      Benchmark
          │              │
          └──────────────┴──────────────┘
                         │
                    Native Binary
```

Điểm quan trọng nhất là **Oracle và Tooling đều dựa trên semantic model**, chứ không tự định nghĩa semantics.

---

# 69. Trạng thái Axiom sau Part XXVIII

Axiom hiện đã có gần như toàn bộ trục semantic lớn:

```text
01 Lexical
02 Grammar
03 Names
04 Types
05 Expressions
06 Statements
07 Functions
08 Struct/Enum
09 Traits/Generics
10 Ownership
11 Views/Capabilities
12 Drop
13 Error/Panic
14 Async
15 Concurrency
16 Atomics
17 Memory/Allocation
18 Unsafe
19 FFI/ABI
20 GPU
21 Comptime/Reflection
22 Modules/Packages
23 Build
24 Runtime
25 Compiler Pipeline
26 Oracle
27 Diagnostics/AI Interface
28 Debug/Tooling/Profiler/Sanitizer
```

Còn đúng **hai mảnh cuối cực kỳ quan trọng**:

```text
PART XXIX — TARGETS · NATIVE CODE · OBJECT FILE · LINKER · BINARY
PART XXX  — CONFORMANCE · SPECIFICATION FREEZE · SELF-HOSTING
```

Part XXIX sẽ khóa phần mà mục tiêu ban đầu của Axiom nhấn mạnh nhất: **làm thế nào từ MIR của Axiom tạo ra `.exe`, ELF, Mach-O, WASM... mà cuối cùng không phụ thuộc LLVM/C compiler hay toolchain bên ngoài.**

Sau đó Part XXX sẽ đóng toàn bộ specification thành một **Axiom Language Definition v1.0 + Conformance Suite + Bootstrap/Self-hosting roadmap**, và lúc đó mới có thể đánh giá toàn bộ thiết kế một lần cuối để tìm contradiction còn sót lại.