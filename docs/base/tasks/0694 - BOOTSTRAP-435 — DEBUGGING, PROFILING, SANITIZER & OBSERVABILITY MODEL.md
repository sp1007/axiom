# BOOTSTRAP-435 — DEBUGGING, PROFILING, SANITIZER & OBSERVABILITY MODEL

BOOTSTRAP-435 khóa hệ thống quan sát và chẩn đoán runtime của Axiom.

Mục tiêu không phải xây một runtime debug nặng, mà là:

> **Production binary không chịu overhead của debugging/profiling/sanitizer nếu developer không yêu cầu; compiler vẫn phải giữ đủ metadata để tạo trải nghiệm debug chuyên nghiệp.**

---

## 435.1 — Debug architecture

```text
Axiom Source
    ↓
AST / Semantic DB
    ↓
IR
    ↓
Optimized IR
    ↓
Machine Code
    ↓
Debug Metadata
    ↓
Executable / Library
```

Debug metadata phải được tạo xuyên suốt pipeline, không phải cố suy ngược từ machine code sau cùng.

---

## 435.2 — Debug information

Debug information mô tả quan hệ:

```text
machine address
    ↓
function
    ↓
inline call site
    ↓
IR instruction
    ↓
AST node
    ↓
source span
```

---

## 435.3 — Debug formats

Native targets sử dụng format phù hợp:

```text
Windows → CodeView/PDB
Linux   → DWARF
macOS   → DWARF + Mach-O debug information
WASM    → DWARF/WASM debug metadata
```

Compiler abstraction không phụ thuộc trực tiếp vào một debug format.

---

## 435.4 — Debug info abstraction

Compiler IR có:

```text
DebugLocation
DebugScope
DebugVariable
DebugFunction
DebugType
DebugInlineSite
```

Backend chuyển chúng sang target-specific representation.

---

## 435.5 — Source location

Mỗi executable instruction quan trọng có thể map về:

```text
file
line
column
```

nhưng compiler không bắt buộc map mọi instruction nếu optimization làm mapping không còn chính xác.

---

## 435.6 — Inline debugging

Nếu:

```text
@inline
fn add(...)
```

được inline vào `main`, debugger vẫn phải hiển thị call chain logic:

```text
main
 └── add
```

nếu debug information còn khả dụng.

---

## 435.7 — Variable locations

Một variable có thể tồn tại ở:

```text
register
stack
memory
multiple locations
optimized away
```

Debug metadata phải mô tả location ranges.

---

## 435.8 — Optimized-out variables

Debugger phải báo rõ:

```text
variable unavailable / optimized out
```

thay vì hiển thị dữ liệu giả.

---

## 435.9 — Debug build

Default debug profile:

```text
debug_info = full
optimization = low
assertions = enabled
```

---

## 435.10 — Release debugging

Release build vẫn có thể emit debug information:

```text
-O3 + debug_info
```

Không yêu cầu compiler phải tắt optimization.

---

## 435.11 — Split debug information

Production artifact có thể:

```text
application
application.debug
```

Executable không cần chứa toàn bộ debug data.

---

## 435.12 — Symbol stripping

Toolchain:

```text
axiom strip app
```

hoặc tương đương build option.

Strip không được làm thay đổi executable semantics.

---

## 435.13 — Breakpoints

Debugger integration phải hỗ trợ:

```text
source breakpoint
function breakpoint
address breakpoint
conditional breakpoint
```

---

## 435.14 — Watchpoints

Native debugger integration hỗ trợ:

```text
memory watchpoint
read watchpoint
write watchpoint
```

nếu target cho phép.

---

## 435.15 — Stack inspection

Debugger phải có:

```text
backtrace
frame selection
locals
arguments
source location
```

---

## 435.16 — Threads

Debugger phải hiển thị:

```text
thread ID
thread name
state
stack
current frame
```

---

## 435.17 — Async debugging

Async function không được hiển thị như một native stack frame đơn giản nếu state machine đã được lower.

Compiler phải giữ mapping:

```text
async function
 ↓
state machine
 ↓
logical async frame
```

---

## 435.18 — Future/task identity

Debugger có thể hiển thị:

```text
Task
Future
state
executor
await location
```

nếu debug runtime instrumentation được bật.

---

## 435.19 — Exception/panic debugging

Khi panic:

```text
panic location
message
stack trace
thread
```

được expose theo profile.

---

## 435.20 — Panic without allocation

Freestanding target vẫn có thể dùng panic handler tối giản:

```text
panic_handler(...)
```

không yêu cầu allocator.

---

## 435.21 — Crash reporting

Compiler/runtime cung cấp dữ liệu cần thiết để ứng dụng tự xây crash reporter.

Không tự động gửi crash report ra ngoài.

---

## 435.22 — Stack unwinding

Unwinding sử dụng:

```text
DWARF CFI
Windows unwind metadata
AArch64 unwind information
```

tùy target.

---

## 435.23 — Frame pointers

Build profile có thể chọn:

```text
frame_pointer = on
frame_pointer = off
```

Frame pointer hữu ích cho profiling/debug nhưng không phải requirement production.

---

## 435.24 — Backtrace quality

Compiler không được vô tình phá hoàn toàn stack trace chỉ vì optimization.

Khi optimization cho phép, debug metadata phải giữ inline chain.

---

# 435.25 — Profiling architecture

Profiling là một capability độc lập:

```text
program
 ↓
profiler
 ↓
samples/events/counters
 ↓
symbolication
 ↓
source/IR mapping
```

---

## 435.26 — CPU sampling profiler

Axiom tooling hỗ trợ statistical sampling:

```text
CPU time
call stack
instruction address
thread
```

---

## 435.27 — Instrumentation profiler

Có thể compile instrumentation:

```text
profile=instrumented
```

để thu thập:

```text
function entry
function exit
call counts
timings
```

---

## 435.28 — Sampling vs instrumentation

Hai phương pháp phải được phân biệt.

Sampling:

- overhead thấp;
- phù hợp production-like profiling.

Instrumentation:

- dữ liệu chi tiết hơn;
- overhead cao hơn.

---

## 435.29 — Function timing

Tool có thể report:

```text
foo       32.4%
bar       17.8%
parse      9.2%
...
```

Đây là profiling data, không phải compiler optimization guarantee.

---

## 435.30 — Call graph

Profiler có thể xây:

```text
main
 ├── parse
 │    ├── lex
 │    └── tokenize
 └── execute
```

---

## 435.31 — Flame graph

Tooling có thể export format phù hợp với flame graph visualization.

---

## 435.32 — Hardware performance counters

Nếu OS/CPU cho phép:

```text
cycles
instructions
branches
branch misses
cache misses
LLC misses
```

được thu thập.

---

## 435.33 — Architecture-neutral counters

Profiler dùng abstraction:

```text
CpuCounter
```

và target backend map sang hardware counter.

---

## 435.34 — GPU profiling

GPU profiling không thuộc core language.

Compiler/runtime chỉ cần emit đủ metadata để GPU tooling có thể map kernel:

```text
kernel
→ source
→ specialization
→ generated code
```

---

## 435.35 — Allocation profiling

Allocator API từ 423 có instrumentation hook:

```text
allocate
reallocate
deallocate
```

---

## 435.36 — Allocation events

Debug allocator có thể record:

```text
address
size
alignment
allocation site
thread
timestamp
```

---

## 435.37 — Allocation overhead

Production allocator mặc định:

```text
no tracing
no stack capture
no event logging
```

---

## 435.38 — Leak detection

Không cần GC nhưng vẫn phải có leak diagnostics.

Debug allocator có thể detect:

```text
allocation without deallocation
```

khi process kết thúc.

---

## 435.39 — Ownership leak vs resource leak

Tool phải phân biệt:

```text
memory leak
file/socket/resource leak
```

Không giả định mọi resource đều memory.

---

## 435.40 — Double free detection

Debug allocator có thể phát hiện double free.

Production behavior vẫn theo memory safety semantics đã khóa ở 423.

---

# 435.41 — Sanitizer architecture

Sanitizer là compiler instrumentation + runtime support.

Không phải language semantic requirement.

---

## 435.42 — Address sanitizer

Có thể phát hiện:

```text
out-of-bounds
use-after-free
invalid memory access
double free
```

---

## 435.43 — Undefined behavior sanitizer

Compiler có thể instrument:

```text
integer overflow
invalid shift
invalid enum state
alignment violation
division by zero
```

tùy semantic rule.

---

## 435.44 — Thread sanitizer

Thread sanitizer có thể detect:

```text
data race
```

trên supported targets.

---

## 435.45 — Memory sanitizer

Uninitialized-memory tracking có thể được hỗ trợ ở target phù hợp.

---

## 435.46 — Sanitizer selection

Ví dụ:

```text
axiom build --sanitize=address
axiom test --sanitize=thread
```

Có thể combine sanitizer nếu target/runtime hỗ trợ.

---

## 435.47 — Sanitizer runtime

Sanitizer runtime là optional component.

Không link nếu không dùng.

---

## 435.48 — Sanitizer + freestanding

Freestanding build có thể không hỗ trợ sanitizer.

Compiler phải báo capability rõ ràng thay vì silently bỏ instrumentation.

---

## 435.49 — Bounds-check instrumentation

Axiom có bounds checking ở safe operations.

Optimizer có thể eliminate check nếu chứng minh được:

```text
0 <= index < length
```

---

## 435.50 — Bounds-check diagnostics

Optimization report có thể nói:

```text
bounds check eliminated
```

hoặc:

```text
bounds check retained
```

---

## 435.51 — Unsafe access

Unsafe unchecked memory access không tự động được sanitizer hóa thành safe operation.

Sanitizer có thể vẫn detect lỗi vật lý nếu instrumentation có thể quan sát được.

---

## 435.52 — Integer sanitization

Không được tự động biến integer semantics thành trapping semantics.

Sanitizer chỉ instrument theo selected mode.

---

## 435.53 — Concurrency instrumentation

Atomic operations giữ nguyên semantic ordering.

Instrumentation không được thay đổi ordering contract.

---

## 435.54 — Mutex instrumentation

Debug runtime có thể ghi:

```text
lock acquisition
lock release
wait duration
owner
```

---

## 435.55 — Deadlock diagnostics

Debug synchronization layer có thể phát hiện lock-order cycle:

```text
A → B
B → A
```

và report potential deadlock.

Đây là diagnostic, không phải guarantee phát hiện mọi deadlock.

---

## 435.56 — Blocking profiler

Profiler có thể phân biệt:

```text
CPU running
mutex wait
IO wait
sleep
scheduler wait
```

---

## 435.57 — Async observability

Async runtime instrumentation:

```text
task created
task scheduled
task suspended
task resumed
task completed
task cancelled
```

---

## 435.58 — Event tracing

Axiom runtime có lightweight event API:

```text
trace_event(...)
```

nhưng event logging phải opt-in.

---

## 435.59 — Trace categories

Có thể phân loại:

```text
CPU
IO
THREAD
TASK
LOCK
ALLOC
GC
```

Trong đó **GC category không tồn tại trong Axiom runtime core**, vì Axiom không có GC.

---

## 435.60 — User-defined tracing

Library có thể tạo trace event riêng:

```text
trace("database.query.begin")
```

---

## 435.61 — Compile-time trace metadata

Compiler có thể thêm:

```text
function ID
module ID
source location
```

vào tracing metadata.

---

## 435.62 — Zero-cost disabled tracing

Nếu tracing disabled:

```text
trace_event(...)
```

nên được compile thành no-op/eliminated code khi có thể.

---

## 435.63 — Observability levels

Đề xuất:

```text
none
basic
debug
profile
trace
sanitize
```

Không bắt buộc tất cả phải độc lập; chúng là capability flags.

---

## 435.64 — Performance counters API

Standard library cung cấp abstraction:

```text
PerformanceCounter
```

nhưng target capabilities khác nhau.

---

## 435.65 — Timing API

Có:

```text
Instant
Duration
```

và monotonic clock.

---

## 435.66 — Wall clock vs monotonic

Không dùng wall-clock để đo elapsed performance.

```text
Instant
```

phải monotonic nếu platform cung cấp.

---

## 435.67 — Benchmark timing

Benchmark framework tự loại bỏ hoặc report:

```text
warmup
iterations
variance
outliers
```

---

## 435.68 — Benchmark correctness

Benchmark phải có mechanism tránh compiler loại bỏ computation không quan sát được.

Ví dụ:

```text
black_box(value)
```

---

## 435.69 — Profile-guided optimization

Axiom hỗ trợ PGO:

```text
build instrumented
→ run workload
→ collect profile
→ build optimized
```

---

## 435.70 — PGO profile format

Profile phải chứa:

```text
compiler version
target
function identity
call edges
branch data
```

---

## 435.71 — PGO compatibility

Profile cũ không được sử dụng nếu semantic/compiler/target fingerprint không tương thích.

---

## 435.72 — AutoFDO-like support

Có thể import external sampling profiles nếu mapping đủ tin cậy.

---

## 435.73 — Link-time optimization

Axiom linker/optimizer hỗ trợ LTO ở mức IR hoặc machine-code metadata phù hợp.

---

## 435.74 — Whole-program optimization

Có thể tối ưu:

```text
module
package
workspace
whole executable
```

theo profile.

---

## 435.75 — Dead code report

Compiler có thể report:

```text
unused function eliminated
unused generic instantiation eliminated
unused section eliminated
```

---

## 435.76 — Code-size profiling

Tool:

```text
axiom size
```

có thể report:

```text
text
rodata
data
bss
debug
metadata
```

---

## 435.77 — Symbol size

Có thể report:

```text
symbol → bytes
```

để tìm code bloat.

---

## 435.78 — Generic bloat

Tool đặc biệt report monomorphization:

```text
Vec<i32>
Vec<f32>
Vec<u64>
...
```

và tổng code size.

---

## 435.79 — Inlining report

Compiler có thể report:

```text
inlined
not inlined
reason
```

---

## 435.80 — Vectorization report

Tương tự:

```text
vectorized
not vectorized
reason
```

---

## 435.81 — Allocation elimination report

Compiler report:

```text
heap allocation eliminated
stack promoted
scalar replaced
```

---

## 435.82 — Escape analysis report

Có thể inspect:

```text
NoEscape
FunctionEscape
ThreadEscape
GlobalEscape
```

từ 423.

---

## 435.83 — Memory layout inspection

CLI:

```text
axiom layout TypeName
```

cho:

```text
size
alignment
fields
offsets
padding
ABI representation
```

---

## 435.84 — ABI inspection

```text
axiom abi TypeName
```

hiển thị:

```text
argument classification
return classification
calling convention
layout
```

---

## 435.85 — Instruction inspection

```text
axiom disasm binary
```

có thể map:

```text
machine instruction
→ source line
```

nếu debug information tồn tại.

---

## 435.86 — Relocation inspection

Đối với object:

```text
axiom objdump object.axo
```

hiển thị:

```text
sections
symbols
relocations
```

---

## 435.87 — Link map

Linker có thể emit:

```text
app.map
```

gồm:

```text
sections
symbols
addresses
sizes
dead-stripped symbols
```

---

## 435.88 — Binary size regression

CI có thể compare:

```text
previous artifact
vs
current artifact
```

theo machine-readable format.

---

## 435.89 — Performance regression

Benchmark tool xuất machine-readable:

```json id="6xv7ol"
{
  "benchmark": "parse",
  "iterations": 1000,
  "median_ns": 12345
}
```

---

## 435.90 — Statistical honesty

Tool không tự kết luận:

```text
"version B is faster"
```

chỉ từ một sample.

Nó cung cấp measurements và statistical metadata.

---

## 435.91 — Benchmark environment

Benchmark result ghi:

```text
CPU
OS
target
compiler
optimization
runtime
```

---

## 435.92 — Reproducible benchmark configuration

Benchmark command có thể lưu:

```text
benchmark.toml
```

---

## 435.93 — Debugger abstraction

Axiom tooling không tự viết debugger engine cho mọi OS.

Nó cung cấp:

```text
DAP integration
debug metadata
process control adapters
```

---

## 435.94 — Native debugger compatibility

Có thể sử dụng debugger hệ điều hành/third-party thông qua DAP hoặc adapter.

Điều này **không vi phạm** mục tiêu compiler independence: debugger là developer tooling, không phải compiler backend dependency.

---

## 435.95 — Debugger launch configuration

Project có thể có:

```text
.axiom/debug/
```

nhưng không bắt buộc.

---

## 435.96 — Remote debugging

Target hỗ trợ remote debugging có thể dùng:

```text
host compiler
→ target binary
→ remote debugger
```

---

## 435.97 — Embedded debugging

Embedded target có thể dùng:

```text
JTAG
SWD
GDB remote
```

thông qua external debugger tooling.

---

## 435.98 — Core dump

Native target có thể tạo core dump.

Axiom debug symbols phải đủ để symbolize core dump.

---

## 435.99 — Crash symbolication

Tool:

```text
axiom symbolize crash.txt
```

có thể resolve:

```text
address
→ function
→ file
→ line
```

---

## 435.100 — Symbol server

Enterprise ecosystem có thể có symbol server, nhưng compiler không yêu cầu server.

---

# 435.101 — Debug/release binary separation

Production artifact không được tự động chứa:

```text
profiling hooks
sanitizer
allocation tracker
debug strings
```

trừ khi profile yêu cầu.

---

## 435.102 — Zero-overhead principle

Khi feature disabled và compiler có thể chứng minh code không observable:

```text
debug/profiling instrumentation
→ eliminated
```

---

## 435.103 — Runtime capability pruning

Runtime components:

```text
panic
allocator
thread
async
trace
sanitizer
```

được link theo usage/profile.

---

## 435.104 — No hidden observer

Axiom runtime không tự động:

```text
collect telemetry
phone home
record source
record execution
```

---

## 435.105 — Security-sensitive data

Debug/profiling output phải có cơ chế tránh vô tình dump:

```text
secret keys
passwords
private buffers
```

Compiler không thể biết toàn bộ secret semantics, nên developer phải có API/attribute để mark sensitive data.

---

## 435.106 — Sensitive debug values

Có thể hỗ trợ:

```text
@debug_hide
secret: String
```

để debugger không hiển thị giá trị mặc định.

---

## 435.107 — Memory poisoning

Debug allocator có thể poison freed memory.

---

## 435.108 — Guard pages

Large allocation/debug allocator có thể dùng guard pages.

Đây là platform-specific optimization.

---

## 435.109 — Stack protection

Compiler có thể hỗ trợ:

```text
stack protector
```

trong security profile.

---

## 435.110 — Control-flow protection

Target hỗ trợ có thể bật:

```text
CFI
shadow stack
CET
PAC
```

tùy architecture/OS.

---

## 435.111 — Security profile

Có thể có:

```text
[profile.hardened]
```

với:

```text
stack protection
control-flow protection
sanitization where practical
```

---

## 435.112 — Sanitizer ≠ security guarantee

Sanitizer chỉ phát hiện một số classes of bugs trong build được instrument.

Không được coi sanitizer là formal proof of safety.

---

## 435.113 — Unsafe code observability

Compiler có thể đánh dấu source regions:

```text
unsafe
```

trong debug metadata.

---

## 435.114 — Unsafe inventory

Tool:

```text
axiom unsafe
```

có thể liệt kê:

```text
unsafe functions
unsafe blocks
raw pointer operations
FFI boundaries
```

---

## 435.115 — FFI diagnostics

Debugger/profiler phải giữ symbol information qua FFI nếu ABI/debug information cho phép.

---

## 435.116 — Native stack frames

Axiom stack frame phải tương thích với platform debugger conventions.

---

## 435.117 — Tail calls

Tail-call optimization có thể làm mất stack frame.

Debugger phải phản ánh đây là optimized frame omission, không phải crash.

---

## 435.118 — Async suspension

Suspended async task không nhất thiết có native stack.

Debugger phải đọc state machine metadata.

---

## 435.119 — Closure debugging

Closure phải có debug representation:

```text
closure type
captured fields
function body
```

---

## 435.120 — Generic debugging

Debugger phải hiển thị concrete generic instance:

```text
Vec<i32>
```

thay vì chỉ:

```text
Vec<T>
```

khi concrete type đã biết.

---

## 435.121 — Trait object debugging

`dyn Trait` có thể hiển thị:

```text
dynamic concrete type
trait
vtable
data address
```

nếu RTTI/debug metadata tồn tại.

---

## 435.122 — Optional runtime type metadata

Debug build có thể emit richer type metadata.

Production không bắt buộc.

---

## 435.123 — Compile-time reflection vs runtime reflection

Reflection metadata từ 431 chủ yếu compile-time.

Debugger metadata là một hệ thống riêng và không biến runtime thành reflective runtime.

---

## 435.124 — Observability API

Standard library/runtime expose abstraction:

```text
trace
metrics
time
profiler hooks
allocation hooks
```

---

## 435.125 — Metrics

Ứng dụng có thể định nghĩa:

```text
counter
gauge
histogram
```

nhưng exporter/networking nằm ở ecosystem.

---

## 435.126 — No mandatory metrics runtime

Nếu application không dùng metrics:

```text
no metrics runtime
```

được link.

---

## 435.127 — Structured logs

Logging library có thể output:

```text
JSON
text
binary event stream
```

Compiler không bắt buộc format.

---

## 435.128 — Source-level instrumentation

Attribute có thể yêu cầu instrumentation:

```text
@profile
fn expensive() { ... }
```

Nhưng syntax cụ thể sẽ khóa trong profiling library/tooling specification.

---

## 435.129 — Compiler-generated instrumentation IDs

Mỗi instrumented function có stable ID dựa trên semantic identity thay vì source line duy nhất.

---

## 435.130 — Build identity

Profile data phải chứa:

```text
compiler
source hash
target
optimization
profile identity
```

để tránh symbolize nhầm binary.

---

## 435.131 — Profile mismatch

Nếu profile không tương thích:

```text
warning/error
```

không silently apply.

---

## 435.132 — Performance metadata

Compiler có thể xuất:

```text
function size
instruction count
hot/cold classification
inline decisions
vectorization
allocation behavior
```

---

## 435.133 — Hot/cold sections

Backend có thể đặt:

```text
hot code
cold code
```

ở section/layout khác nhau nếu target hỗ trợ.

---

## 435.134 — Branch hints

Axiom có thể expose explicit compiler hints, nhưng hint không được biến thành semantic guarantee.

---

## 435.135 — Cache profiling

Nếu runtime/library có cache abstractions, profiler có thể instrument:

```text
hit
miss
eviction
```

ở library level.

---

## 435.136 — IO profiling

Profiler có thể report:

```text
file IO
network IO
blocking duration
```

nếu runtime instrumentation bật.

---

## 435.137 — System-call tracing

Không thuộc compiler core.

Có thể integrate OS tracing tools.

---

## 435.138 — External profiler integration

Axiom debug metadata phải tương thích với ecosystem profiler thay vì bắt developer dùng một profiler độc quyền.

---

## 435.139 — Perf compatibility

Linux artifacts nên hỗ trợ symbolization/perf-style profiling khi target cho phép.

---

## 435.140 — ETW compatibility

Windows artifacts phải có đủ metadata để Windows profiling ecosystem có thể sử dụng.

---

## 435.141 — Apple Instruments compatibility

Mach-O/debug metadata phải tương thích với native Apple profiling tooling ở mức platform cho phép.

---

## 435.142 — WASM profiling

WASM phải giữ source map/debug metadata khi profile/debug build yêu cầu.

---

## 435.143 — Browser debugging

WASM artifact có thể expose source mapping để browser debugger map về `.ax` source.

---

## 435.144 — GPU kernel debugging

GPU backend sau này phải giữ:

```text
kernel source
specialized type
comptime constants
generated kernel code
```

mapping.

---

## 435.145 — ML/tensor profiling

Không thuộc language core.

Tensor library có thể dùng tracing API của 435.

---

## 435.146 — Allocation domains

Allocator abstraction có thể đặt tên domain:

```text
general
frame
asset
temporary
network
```

giúp profiler phân loại allocations.

---

## 435.147 — Arena diagnostics

Arena allocator có thể report:

```text
capacity
used
peak
reset count
```

---

## 435.148 — Stack allocator diagnostics

Có thể report:

```text
high-water mark
overflow
scope lifetime
```

---

## 435.149 — Resource diagnostics

Deterministic destruction từ 423 cho phép tooling report:

```text
resource acquired
resource released
unreleased resource
```

---

## 435.150 — `defer` debugging

Debugger có thể biểu diễn deferred cleanup như scope cleanup, không bắt buộc hiển thị compiler-generated function.

---

## 435.151 — Destructor debugging

`drop` function có debug mapping bình thường.

---

## 435.152 — Partial initialization

Debugger phải biết field nào đã initialized khi object đang trong quá trình construction.

---

## 435.153 — Moved-from values

Debug metadata có thể đánh dấu variable:

```text
moved
```

để IDE/debugger không hiển thị nó như một valid owner.

---

## 435.154 — Ownership diagnostics

Compiler diagnostic từ 423 là compile-time.

Runtime sanitizer không được tạo một ownership runtime tracker mặc định.

---

## 435.155 — Data race diagnostics

Axiom không tự biến tất cả shared memory thành synchronized memory.

Race sanitizer là instrumentation.

---

## 435.156 — Atomic inspection

Debugger phải hiển thị atomic values bình thường nhưng không được giả định memory ordering khi đọc snapshot.

---

## 435.157 — Lock inspection

Nếu runtime instrumentation bật:

```text
mutex address
owner
waiters
```

có thể được expose.

---

## 435.158 — Scheduler inspection

Async executor có thể expose:

```text
workers
ready queue
running tasks
blocked tasks
```

---

## 435.159 — Runtime-independent core

Core language không cần:

```text
profiler runtime
debug runtime
logging runtime
```

---

## 435.160 — Debug profile composition

Profile có thể compose:

```text
debug
+ address sanitizer
+ tracing
```

nhưng compiler phải reject incompatible combinations.

---

## 435.161 — Sanitizer incompatibility

Ví dụ một target có thể không hỗ trợ:

```text
thread sanitizer + freestanding
```

Toolchain phải báo rõ.

---

## 435.162 — Instrumentation ordering

Pipeline:

```text
semantic IR
→ optimization
→ sanitizer instrumentation
→ profiling instrumentation
→ machine lowering
```

thứ tự chính xác có thể khác tùy pass, nhưng semantic correctness phải được bảo toàn.

---

## 435.163 — Optimization-aware sanitizer

Compiler được phép optimize instrumentation nhưng không được loại bỏ check cần thiết theo sanitizer semantics.

---

## 435.164 — Debug assertions

`assert` trong debug profile có thể bị eliminate trong release nếu semantic contract cho phép.

---

## 435.165 — Contracts

Future contract system có thể emit:

```text
precondition
postcondition
invariant
```

trong verification/debug profiles.

Không khóa contract language vào 435; chỉ reserve instrumentation interface.

---

## 435.166 — Runtime checks

Runtime check phải phân biệt:

```text
language-required safety check
debug assertion
sanitizer instrumentation
developer contract
```

---

## 435.167 — Production semantics

Tắt sanitizer không được thay đổi semantics của chương trình hợp lệ.

---

## 435.168 — Invalid program behavior

Sanitizer chỉ quan sát behavior đã thuộc undefined/invalid territory theo semantic rules.

Không dùng sanitizer để định nghĩa language semantics.

---

## 435.169 — Crash reproducibility

Tooling hỗ trợ lưu:

```text
binary hash
source revision
target
arguments
environment contract
```

để reproduce crash.

---

## 435.170 — Environment recording

Không tự động lưu toàn bộ environment vì có thể chứa secrets.

Chỉ record whitelisted metadata.

---

## 435.171 — Deterministic diagnostics

Cùng input + compiler + target phải tạo diagnostic ordering deterministic.

---

## 435.172 — Deterministic profiler metadata

Compiler-generated symbol IDs phải deterministic.

---

## 435.173 — Debug metadata size

Debug metadata có thể lớn nhưng phải nằm ngoài production artifact khi split debug được bật.

---

## 435.174 — Debug information compression

Toolchain có thể compress debug sections.

---

## 435.175 — Debug package

Package distribution có thể cung cấp:

```text
app
app.debug
source archive
```

nếu developer muốn.

---

## 435.176 — Source indexing

LSP có thể reuse debug/source symbol database.

---

## 435.177 — Source server

External source retrieval có thể là ecosystem capability, không thuộc compiler core.

---

## 435.178 — Profiling data storage

Profile output không thuộc executable.

Ví dụ:

```text
profile/
    cpu.prof
    alloc.prof
    trace.prof
```

---

## 435.179 — Machine-readable profile

Mọi profiler chính thức phải có structured output để CI/AI đọc được.

---

## 435.180 — AI performance analysis

AI tooling có thể query:

```text
hot_functions
largest_symbols
allocation_hotspots
lock_contention
bounds_checks
inline_failures
```

Compiler cung cấp measurements, AI có thể phân tích; compiler không tự đưa ra ranking "code tốt/xấu".

---

## 435.181 — AI debugging

AI có thể query:

```text
crash location
stack
locals
types
ownership state
async state
```

nếu developer cấp debug artifact.

---

## 435.182 — AI patch suggestions

Diagnostic có thể trả structured patch.

AI agent có thể apply patch và chạy:

```text
axiom check
axiom test
```

---

## 435.183 — AI loop

Toolchain hỗ trợ loop:

```text
build
→ diagnostic
→ semantic query
→ patch
→ check
→ test
```

đây là nền tảng quan trọng cho Axiom agent workflow.

---

## 435.184 — No autonomous code modification

Compiler chỉ cung cấp diagnostic/fix.

Việc AI tự sửa source là responsibility của external agent.

---

## 435.185 — Compiler observability

Compiler itself có profiling:

```text
axiom build --trace
```

có thể đo:

```text
parse time
typecheck time
comptime time
IR time
optimization time
codegen time
link time
```

---

## 435.186 — Compiler memory usage

Build trace có thể report:

```text
peak memory
AST memory
semantic DB
IR memory
cache usage
```

---

## 435.187 — Compiler scalability

Large projects phải có diagnostics về:

```text
number of modules
symbols
generic instantiations
comptime executions
cache hit rate
```

---

## 435.188 — Cache hit rate

Build trace:

```text
cache:
    semantic 93%
    comptime 98%
    IR       89%
    object   91%
```

Các số này chỉ là runtime measurements, không phải language guarantee.

---

## 435.189 — Build profiling

Compiler profiler giúp tìm bottleneck compiler mà không cần external instrumentation.

---

## 435.190 — Compiler self-hosting requirement

Khi compiler chuyển sang viết bằng Axiom, toàn bộ:

```text
debug
profile
sanitizer
```

phải vẫn usable.

---

## 435.191 — Bootstrap debugging

Stage compiler phải có đủ debug info để debug compiler written in Axiom.

---

## 435.192 — Backend debugging

Machine encoder 420 phải có test/debug mapping:

```text
IR instruction
→ encoded bytes
→ relocation
```

---

## 435.193 — Linker debugging

Linker trace phải có:

```text
input object
symbol
section
relocation
final address
```

---

## 435.194 — Binary reproducibility + debug

Debug artifacts có thể chứa paths khác nhau.

Compiler phải hỗ trợ path remapping:

```text
source root
→ stable logical root
```

---

## 435.195 — Path remapping

Ví dụ:

```text
--remap-path-prefix=/home/user/project=/src
```

conceptually.

---

## 435.196 — Build environment normalization

Reproducible debug artifacts phải tránh absolute host-specific paths nếu profile yêu cầu.

---

## 435.197 — Time-dependent metadata

Không nhúng:

```text
build timestamp
random UUID
host username
```

trừ khi explicitly requested.

---

## 435.198 — Randomized security vs reproducibility

Security hardening có thể cần randomness.

Khi có conflict, profile phải xác định nguồn randomness và reproducibility contract rõ ràng.

---

## 435.199 — Observability boundary

```text
Language semantics
        ↓
Compiler
        ↓
Optional instrumentation
        ↓
Optional runtime capability
        ↓
External debugger/profiler
```

Không đưa profiler/debugger vào language semantics.

---

# 435.200 — Hard invariants

BOOTSTRAP-435 khóa:

1. Debugging không phải runtime requirement.
2. Production build không chịu debug overhead nếu không yêu cầu.
3. Debug information được sinh xuyên suốt compiler pipeline.
4. Source ↔ IR ↔ machine-code mapping được duy trì khi có thể.
5. Optimized-out values phải được biểu diễn trung thực.
6. Inline functions vẫn có debug call-site metadata.
7. Async state machines có logical debug mapping.
8. Native targets sử dụng target-specific debug formats.
9. DAP là integration boundary cho debugger.
10. Profiling là capability riêng.
11. Sampling và instrumentation là hai chế độ khác nhau.
12. Hardware counters có abstraction target-independent.
13. Allocation profiling tích hợp với allocator abstraction từ 423.
14. Leak/double-free diagnostics là debug tooling, không phải GC.
15. Sanitizer là optional instrumentation.
16. Address/UB/thread/memory sanitizers có thể được hỗ trợ tùy target.
17. Sanitizer không định nghĩa language semantics.
18. Race detection không biến shared memory thành implicit synchronized memory.
19. Debug/profiling output không tự động gửi dữ liệu ra ngoài.
20. Runtime tracing là opt-in.
21. Disabled instrumentation phải được compiler eliminate khi có thể.
22. PGO được hỗ trợ.
23. Optimization remarks machine-readable.
24. Code-size và allocation profiling được hỗ trợ.
25. Ownership state có thể được expose cho tooling nhưng không có ownership runtime tracker mặc định.
26. Unsafe regions được nhận diện trong tooling.
27. ABI/layout/instruction/linker inspection được hỗ trợ.
28. Crash symbolication được hỗ trợ.
29. Debug artifacts có thể tách khỏi executable.
30. Host-specific paths có thể được remap.
31. Build/profile identity được ghi để tránh dùng sai metadata.
32. AI có thể consume debug/profile data dạng structured.
33. Compiler cung cấp dữ liệu và diagnostics, không tự biến profiling thành các kết luận chủ quan.
34. Không có telemetry bắt buộc.
35. Axiom compiler self-hosting vẫn phải debug/profile được.

**BOOTSTRAP-435 hoàn tất.**

---

# BOOTSTRAP-436 — TESTING, CONFORMANCE, FUZZING, BENCHMARKING & COMPILER CORRECTNESS

436 chuyển từ:

```text
"compiler có debug được không?"
```

sang:

```text
"làm sao chứng minh compiler đáng tin cậy?"
```

Đây là task đặc biệt quan trọng vì Axiom có compiler native riêng, machine encoder riêng, object writer riêng và linker riêng.

Không thể dựa vào LLVM/GCC để gián tiếp xác nhận correctness.

---

## 436.1 — Correctness layers

Axiom compiler test architecture:

```text
Lexer
 ↓
Parser
 ↓
AST
 ↓
Resolver
 ↓
Type Checker
 ↓
Ownership
 ↓
Comptime
 ↓
IR
 ↓
Optimizer
 ↓
Machine Encoder
 ↓
Object Writer
 ↓
Linker
 ↓
Executable
```

Mỗi tầng có test riêng và end-to-end test.

---

## 436.2 — Test categories

Tối thiểu:

```text
unit
integration
conformance
golden
compile-fail
runtime
ABI
backend
linker
fuzz
stress
performance
reproducibility
bootstrap
```

---

## 436.3 — Test directory

Convention:

```text
tests/
    lexer/
    parser/
    type/
    ownership/
    comptime/
    ir/
    optimizer/
    backend/
    abi/
    object/
    linker/
    runtime/
    integration/
    diagnostics/
```

---

## 436.4 — Test IDs

Mỗi test có stable identifier:

```text
TYPE-001
OWN-014
ABI-023
X86-117
ELF-042
LINK-031
```

---

## 436.5 — Positive tests

Positive test phải chứng minh:

```text
source
→ compile success
→ expected behavior
```

---

## 436.6 — Negative tests

Compile-fail test:

```text
source
→ expected error
```

không được chỉ kiểm tra compiler exit code.

---

## 436.7 — Diagnostic assertions

Negative test có thể assert:

```text
error code
source span
message category
suggestion
```

---

## 436.8 — Stable diagnostic testing

Test không nên phụ thuộc toàn bộ wording nếu không cần.

Ưu tiên:

```text
error code
diagnostic kind
span
structured fields
```

---

## 436.9 — Golden output

Một số tool output cần exact golden:

```text
AST dump
IR dump
formatter
assembly
object layout
diagnostic rendering
```

---

## 436.10 — Golden normalization

Golden test phải normalize những thứ intentionally nondeterministic.

Tốt nhất là thiết kế output deterministic ngay từ đầu.

---

## 436.11 — Lexer conformance

Test:

- UTF-8;
- Unicode identifiers;
- numbers;
- strings;
- comments;
- operators;
- attributes;
- escapes.

---

## 436.12 — Parser conformance

Test toàn bộ grammar.

---

## 436.13 — Formatter conformance

Invariant:

```text
fmt(fmt(source)) == fmt(source)
```

---

## 436.14 — AST round-trip

Nếu canonical printer tồn tại:

```text
parse(format(ast))
```

phải semantic-equivalent.

---

## 436.15 — Name resolution tests

Test:

```text
scope
shadowing
imports
visibility
modules
traits
generics
associated items
```

---

## 436.16 — Type checker tests

Test:

```text
inference
coercion
casts
generic constraints
trait resolution
overload resolution
layout queries
```

---

## 436.17 — Ownership tests

Test:

```text
move
copy
clone
drop
defer
partial initialization
early return
scope exit
unsafe
FFI ownership
```

---

## 436.18 — Concurrency semantic tests

Test:

```text
Send
Share
atomic
mutex
thread
async
cancellation
```

---

## 436.19 — Comptime tests

Test:

```text
const
const fn
comptime fn
const generics
reflection
derive
generated declarations
resource limits
determinism
```

---

## 436.20 — Comptime determinism

Cùng:

```text
source
arguments
target
compiler
```

phải tạo cùng comptime result.

---

## 436.21 — Comptime resource limits

Test recursion/step/memory/code-generation limits.

Compiler không được treo vô hạn vì source cố tình tạo comptime loop.

---

## 436.22 — IR tests

IR golden tests:

```text
source
→ expected IR
```

---

## 436.23 — IR semantic tests

Hai IR representations khác nhau vẫn phải produce same semantic result.

---

## 436.24 — Optimization correctness

Mỗi optimization pass cần:

```text
input IR
→ optimized IR
```

và semantic equivalence test.

---

## 436.25 — Optimization isolation

Pass phải test độc lập trước khi test pipeline toàn bộ.

---

## 436.26 — Optimization disabling

Có thể compile:

```text
-O0
```

để phân biệt frontend bug và optimizer bug.

---

## 436.27 — Differential optimizer testing

So sánh:

```text
-O0
vs
-O3
```

trên cùng test suite.

Kết quả observable phải tương đương đối với chương trình hợp lệ.

---

## 436.28 — Backend tests

Mỗi ISA backend phải có:

```text
instruction encoding tests
register allocation tests
ABI tests
relocation tests
branch relaxation tests
```

---

## 436.29 — Machine encoder golden tests

Ví dụ conceptual:

```text
instruction
→ expected bytes
```

để kiểm tra trực tiếp encoder 420.

---

## 436.30 — Decoder oracle

Nếu có instruction decoder/reference implementation, test:

```text
encode
→ decode
```

---

## 436.31 — External ISA oracle

Có thể dùng official ISA documentation/reference tools trong test development.

Nhưng final compiler không phụ thuộc runtime vào chúng.

---

## 436.32 — Object writer tests

ELF:

```text
headers
sections
symbols
relocations
segments
```

PE/COFF:

```text
COFF headers
sections
relocations
imports
exports
```

Mach-O:

```text
load commands
segments
symbols
relocations
```

---

## 436.33 — Linker tests

Test:

```text
symbol resolution
weak symbols
archives
relocations
dead stripping
section alignment
entry point
imports
exports
```

---

## 436.34 — Relocation tests

Mỗi relocation type có:

```text
input object
expected relocation
expected final bytes
```

---

## 436.35 — Cross-object tests

```text
A.ax
B.ax
```

được compile riêng rồi link.

---

## 436.36 — Static library tests

```text
libfoo.a
```

phải được archive extraction đúng.

---

## 436.37 — Dynamic library tests

Test:

```text
DLL
SO
DYLIB
```

tùy target.

---

## 436.38 — FFI tests

Axiom ↔ C ABI:

```text
Axiom caller
→ C function
```

và ngược lại.

---

## 436.39 — ABI matrix

Test matrix:

```text
x86-64 SysV
x86-64 Win64
AArch64 AAPCS64
Apple AArch64
WASM ABI
```

---

## 436.40 — Layout ABI tests

Golden:

```text
sizeof
alignof
offsetof
argument classification
return classification
```

---

## 436.41 — Runtime tests

Test standard runtime:

```text
startup
allocator
panic
thread
async
IO
```

---

## 436.42 — Freestanding tests

Compile programs without standard runtime.

Ví dụ:

```text
entry
raw memory
syscall/platform primitive
exit
```

---

## 436.43 — WASM tests

Test:

```text
WASM module
imports
exports
memory
table
startup
```

---

## 436.44 — Native smoke tests

Smallest possible program:

```text
fn main() -> i32 {
    return 42
}
```

must compile/run on each supported native target.

---

## 436.45 — Exit code test

Expected:

```text
42
```

---

## 436.46 — Arithmetic smoke tests

Test:

```text
integer
float
comparison
branch
loop
function call
```

---

## 436.47 — Struct smoke tests

Test:

```text
struct
field access
method
trait
generic
```

---

## 436.48 — Memory smoke tests

Test:

```text
stack
heap
move
drop
allocator
```

---

## 436.49 — String smoke tests

UTF-8:

```text
Vietnamese
English
Unicode
multibyte
```

must compile and behave correctly.

---

## 436.50 — Unicode normalization tests

Identifier normalization behavior must be tested explicitly.

---

## 436.51 — Pattern matching tests

Test:

```text
enum
Option
Result
tuple
struct
wildcard
guard
range
OR pattern
```

---

## 436.52 — Exhaustiveness tests

Compiler must reject incomplete exhaustive matches where required.

---

## 436.53 — Generic tests

Test:

```text
function generics
struct generics
enum generics
const generics
traits
associated types
```

---

## 436.54 — Dynamic trait tests

Test:

```text
dyn Trait
vtable
object safety
dynamic dispatch
downcast
```

---

## 436.55 — Closure tests

Test:

```text
capture
move capture
nested closure
function pointer conversion
```

---

## 436.56 — Async tests

Test:

```text
await
suspend
resume
completion
cancellation
drop during suspension
```

---

## 436.57 — Panic tests

Test:

```text
panic=abort
panic=unwind
cleanup
FFI boundary
double panic
```

---

## 436.58 — Result tests

Test:

```text
Ok
Err
try propagation
error conversion
```

---

## 436.59 — Option tests

Test:

```text
Some
None
niche optimization
pattern matching
```

---

## 436.60 — Memory safety test distinction

Test suite phải phân biệt:

```text
safe program
invalid program
unsafe program
```

Không dùng compiler crash làm expected behavior cho invalid source.

---

# 436.61 — Fuzzing architecture

Fuzz targets:

```text
lexer
parser
formatter
resolver
type checker
comptime
IR optimizer
machine encoder
object writer
linker
```

---

## 436.62 — Parser fuzzing

Input:

```text
random bytes
random UTF-8
mutated valid programs
```

Compiler phải:

```text
accept
or
diagnose
```

nhưng không crash/hang.

---

## 436.63 — Fuzz timeout

Mỗi fuzz case có timeout.

Compiler không được treo vô hạn.

---

## 436.64 — Fuzz memory limit

Fuzz runner giới hạn memory để ngăn pathological inputs.

---

## 436.65 — Formatter fuzzing

Invariant:

```text
parse(source)
→ format
→ parse
```

không crash.

---

## 436.66 — Formatter idempotence fuzz

```text
format(format(source)) == format(source)
```

---

## 436.67 — Comptime fuzzing

Fuzz:

```text
expressions
const values
generic arguments
recursive generation
```

với resource limits.

---

## 436.68 — Type checker fuzzing

Compiler phải không crash khi gặp type combinations bất kỳ.

---

## 436.69 — IR fuzzing

Generated IR phải:

```text
verify
optimize
```

không crash.

Invalid IR phải bị verifier reject.

---

## 436.70 — Machine encoder fuzzing

Random valid instruction structures:

```text
→ encoder
```

không được produce invalid memory access.

---

## 436.71 — Object writer fuzzing

Malformed internal object structures phải:

```text
reject
```

không crash.

---

## 436.72 — Linker fuzzing

Random/mutated object files phải:

```text
reject safely
```

---

## 436.73 — Binary parser hardening

Linker/object reader phải coi external object input là untrusted data.

---

## 436.74 — Differential parser testing

Có thể so sánh:

```text
parser
→ AST
```

với independent grammar/reference implementation trong development.

---

## 436.75 — Differential codegen testing

Compile cùng program với:

```text
-O0
-O2
-O3
```

và compare observable behavior.

---

## 436.76 — Cross-backend differential testing

Cùng source:

```text
x86-64
AArch64
WASM
```

phải cho semantic-equivalent results.

---

## 436.77 — Interpreter oracle

Axiom có thể có một **semantic interpreter/reference VM** dùng cho compiler testing.

Điều này rất quan trọng.

```text
Axiom source
    ↓
semantic IR
    ├── interpreter
    └── native backend
```

So sánh:

```text
interpreter result
==
native result
```

---

## 436.78 — Interpreter is not production runtime

Reference interpreter chỉ phục vụ:

```text
comptime
tests
compiler development
```

không nằm trong production executable.

---

## 436.79 — Semantic oracle

Interpreter giúp test:

```text
optimizer
backend
ABI lowering
```

mà không cần compiler khác.

---

## 436.80 — Reference implementation

Một semantic reference path phải đơn giản hơn optimizer/backend.

Mục tiêu:

> **Correctness trước, performance sau.**

---

## 436.81 — Translation validation

Sau optimization:

```text
original IR
optimized IR
```

có thể được kiểm tra bằng execution-based equivalence trên test cases.

---

## 436.82 — Formal verification boundary

Không yêu cầu toàn bộ compiler formally verified.

Nhưng những component nhỏ có thể được verify mạnh hơn:

```text
lexer
parser invariants
IR verifier
machine encoder
relocation arithmetic
```

---

## 436.83 — IR verifier

IR phải có verifier:

```text
axiom verify-ir
```

kiểm tra:

- type correctness;
- SSA/value validity;
- block termination;
- dominance assumptions;
- memory operation invariants;
- target constraints.

---

## 436.84 — Backend verifier

Machine instruction representation phải được verify trước emission.

---

## 436.85 — Object verifier

Tool:

```text
axiom verify-obj
```

kiểm tra object consistency.

---

## 436.86 — Linker verifier

Sau link, linker có thể self-check:

```text
entry point
relocations
section bounds
symbol references
segment permissions
```

---

## 436.87 — Executable smoke verification

Sau build native:

```text
load
→ start
→ expected exit
```

trong CI.

---

## 436.88 — Permission tests

Executable sections phải có permission hợp lý:

```text
RX
RW
R
```

không mặc định:

```text
RWX
```

---

## 436.89 — W^X testing

Target/platform hỗ trợ phải test:

```text
Writable XOR Executable
```

ở mức artifact.

---

## 436.90 — Relocation security tests

Kiểm tra relocation không tạo memory layout sai.

---

## 436.91 — Stack alignment tests

FFI/ABI test phải verify runtime stack alignment.

---

## 436.92 — Register preservation tests

Test caller/callee saved registers qua generated code.

---

## 436.93 — Variadic ABI tests

Test:

```text
varargs
float arguments
aggregate arguments
```

trên từng ABI.

---

## 436.94 — Struct return tests

Đặc biệt:

```text
small struct
large struct
mixed float/int struct
```

---

## 436.95 — Vector ABI tests

SIMD/vector arguments và returns.

---

## 436.96 — Endianness tests

Targets little/big endian nếu hỗ trợ.

---

## 436.97 — Pointer width tests

Ít nhất:

```text
32-bit
64-bit
```

architecture abstraction phải không giả định pointer luôn 64-bit.

---

## 436.98 — Integer width tests

Tất cả:

```text
i8/i16/i32/i64
u8/u16/u32/u64
```

---

## 436.99 — Floating-point tests

```text
f16
f32
f64
```

với target capabilities.

---

## 436.100 — IEEE edge cases

Test:

```text
NaN
±Infinity
±0
subnormal
rounding
```

---

# 436.101 — Determinism tests

Build cùng source nhiều lần:

```text
build A
build B
```

compare hashes.

---

## 436.102 — Parallel determinism

```text
-j1
-j8
```

phải tạo cùng artifact khi reproducibility profile bật.

---

## 436.103 — Cache determinism

Build:

```text
cold cache
warm cache
```

phải cho cùng semantic artifact.

---

## 436.104 — Incremental correctness

Test:

```text
build
→ modify one file
→ incremental build
```

và compare với clean build.

---

## 436.105 — Incremental equivalence

```text
incremental result
==
clean rebuild result
```

---

## 436.106 — Dependency invalidation tests

Thay đổi:

```text
private implementation
```

không được invalidate unnecessary downstream semantic units.

Thay đổi:

```text
public API
```

phải invalidate dependents.

---

## 436.107 — Comptime cache correctness

Cold/warm comptime cache phải cho cùng generated semantic result.

---

## 436.108 — Generic cache correctness

Cached generic instantiation phải equivalent với fresh monomorphization.

---

## 436.109 — Artifact cache correctness

Cached object phải equivalent fresh object.

---

## 436.110 — Link cache correctness

Incremental linking phải produce same observable artifact.

---

## 436.111 — Package resolution tests

Test:

```text
version
lock
conflict
optional dependency
workspace
local dependency
git dependency
```

---

## 436.112 — Dependency integrity tests

Modified downloaded package phải bị phát hiện bằng hash.

---

## 436.113 — Build graph cycle tests

Invalid cycles phải diagnostic rõ ràng.

---

## 436.114 — Module visibility tests

Test:

```text
pub
private
package
module
```

---

## 436.115 — API compatibility tests

Public API snapshot:

```text
old
new
```

có thể được compare.

---

## 436.116 — ABI compatibility tests

ABI snapshot phải detect:

```text
size change
alignment change
calling convention change
symbol signature change
```

---

## 436.117 — Semantic versioning checks

Package tooling có thể dùng API/ABI diff để cảnh báo incompatible changes.

Không tự động quyết định version bump nếu policy project khác.

---

## 436.118 — Documentation tests

Documentation code examples có thể compile/test.

---

## 436.119 — Doctest

```text
/// Example:
/// ...
```

có thể trở thành executable test.

---

## 436.120 — Example correctness

Documentation examples phải tránh drift khỏi API thật.

---

## 436.121 — Benchmark regression suite

Compiler repository có benchmark:

```text
compile time
memory usage
runtime
binary size
```

---

## 436.122 — Compiler compile-time benchmark

Đo:

```text
lexer
parser
typecheck
comptime
optimization
codegen
link
```

---

## 436.123 — Runtime benchmark

Representative workloads:

```text
integer
floating point
string
collections
IO
concurrency
async
```

---

## 436.124 — Binary size benchmark

Track:

```text
hello world
CLI
library
larger application
```

---

## 436.125 — No absolute performance guarantee

Axiom target là performance cao, nhưng benchmark suite dùng để **đo**, không giả định trước kết quả.

---

## 436.126 — Compiler regression threshold

CI có thể đặt thresholds:

```text
compile time +10%
binary size +5%
```

nhưng thresholds thuộc project CI policy, không phải language semantics.

---

## 436.127 — Performance dashboards

Có thể lưu historical measurements.

---

## 436.128 — Benchmark reproducibility

Benchmark environment phải ghi rõ:

```text
CPU
OS
compiler
target
profile
dependencies
```

---

## 436.129 — Stress tests

Large generated project:

```text
100k symbols
1M expressions
many generic instantiations
```

để test scalability.

---

## 436.130 — Deep recursion tests

Parser/type checker/comptime phải có controlled behavior với recursion sâu.

---

## 436.131 — Huge source tests

Compiler không được integer-overflow trong source positions hoặc token lengths.

---

## 436.132 — Unicode stress

Test source chứa:

```text
UTF-8
combining characters
emoji
long identifiers
non-Latin scripts
```

---

## 436.133 — Malformed UTF-8

Compiler phải reject malformed source encoding deterministically.

---

## 436.134 — Fuzz corpus

Fuzz findings trở thành permanent regression tests.

---

## 436.135 — Crash-to-test workflow

Mọi compiler crash reproducible phải chuyển thành:

```text
regression test
```

sau khi fix.

---

## 436.136 — Security fuzzing

Object/linker/package parser fuzzing phải được coi là security testing.

---

## 436.137 — Package archive fuzzing

Package extractor phải chống:

```text
path traversal
malformed archive
resource exhaustion
```

---

## 436.138 — Manifest fuzzing

`axiom.toml` parser phải fuzz.

---

## 436.139 — Lockfile fuzzing

Lockfile parser cũng phải fuzz.

---

## 436.140 — LSP fuzzing

Malformed LSP messages không được làm server crash.

---

## 436.141 — LSP recovery

LSP phải tiếp tục hoạt động sau một malformed document/change khi có thể.

---

## 436.142 — Editor latency benchmark

LSP benchmark:

```text
completion latency
diagnostic latency
rename latency
```

---

## 436.143 — Incremental LSP benchmark

Một ký tự thay đổi không nên trigger full workspace rebuild nếu semantic dependency không yêu cầu.

---

## 436.144 — AI query benchmark

Semantic API phải đo:

```text
symbol lookup
references
type query
diagnostic generation
```

---

## 436.145 — AI protocol regression

Schema changes phải có compatibility tests.

---

## 436.146 — Bootstrap tests

Compiler được build bởi compiler trước phải compile chính nó.

---

## 436.147 — Self-hosting fixed point

Mục tiêu cuối:

```text
Axiom compiler vN
compiles
Axiom compiler vN source
```

và compiler output ổn định.

---

## 436.148 — Stage comparison

Bootstrap stages:

```text
stage0 compiler
stage1 compiler
stage2 compiler
```

phải được compare.

---

## 436.149 — Compiler trust bootstrap

Không được silently assume stage compiler correct.

Mỗi stage có smoke/conformance suite.

---

## 436.150 — Compiler determinism

Self-hosted compiler build nhiều lần phải reproducible theo profile.

---

# 436.151 — Test runner architecture

`axiom test`:

```text
discover
→ compile
→ execute
→ collect
→ summarize
```

---

## 436.152 — Parallel tests

Independent tests chạy parallel.

---

## 436.153 — Test isolation

Test có thể chạy:

```text
same process
separate process
```

tùy annotation/profile.

---

## 436.154 — Test timeout

Mọi test có timeout configurable.

---

## 436.155 — Test output

Default:

```text
PASS
FAIL
SKIP
```

Machine mode JSON.

---

## 436.156 — Test filtering

```text
axiom test parser
```

chỉ chạy test matching filter.

---

## 436.157 — Test tags

Có thể:

```text
@slow
@integration
@platform("windows")
```

---

## 436.158 — Platform tests

Test chỉ chạy trên target phù hợp.

---

## 436.159 — Expected failure

Có thể đánh dấu known unsupported test, nhưng phải có reason và không được dùng để che compiler regressions.

---

## 436.160 — Flaky test detection

CI tooling có thể chạy lại test thất bại để phân loại instability, nhưng failure không được tự động biến thành pass mà không ghi nhận.

---

## 436.161 — Randomized tests

Random tests phải ghi seed.

---

## 436.162 — Property-based tests

Standard testing library có thể hỗ trợ:

```text
property
generator
shrinker
```

---

## 436.163 — Fuzz shrinking

Khi fuzz tìm failure:

```text
large input
→ minimized input
```

để tạo regression test.

---

## 436.164 — Mutation testing

Có thể sử dụng mutation testing cho compiler/library tests.

Không phải requirement của compiler runtime.

---

## 436.165 — Coverage

Compiler test suite có thể collect:

```text
line coverage
branch coverage
function coverage
```

---

## 436.166 — Compiler coverage

Quan trọng nhất:

```text
frontend
semantic
optimizer
backend
linker
```

coverage.

---

## 436.167 — Coverage limitations

Coverage cao không đồng nghĩa compiler correct.

---

## 436.168 — Mutation + coverage

Mutation testing giúp phát hiện test suite có thực sự kiểm tra behavior hay chỉ chạy code.

---

## 436.169 — Differential execution

Một chương trình test có thể chạy:

```text
interpreter
native O0
native O3
WASM
```

và compare observable output.

---

## 436.170 — Undefined behavior exclusion

Differential tests chỉ áp dụng cho chương trình có behavior được định nghĩa.

---

## 436.171 — Floating-point tolerance

FP differential tests phải có tolerance/bit-level contract phù hợp semantics.

---

## 436.172 — Platform-specific behavior

OS-dependent APIs không bị ép phải trả kết quả giống nhau nếu semantics vốn platform-specific.

---

## 436.173 — Test oracle

Mỗi test phải có oracle rõ:

```text
value
exit code
stdout
stderr
diagnostic
artifact
```

---

## 436.174 — No snapshot-only runtime testing

Runtime correctness không nên chỉ dựa vào snapshot text.

---

## 436.175 — Artifact testing

Executable/object tests có thể inspect:

```text
headers
symbols
sections
relocations
permissions
```

---

## 436.176 — Binary compatibility tests

ABI libraries có compatibility fixtures.

---

## 436.177 — External compatibility

Test với:

```text
C
system libraries
OS APIs
```

---

## 436.178 — Standard library conformance

Mỗi standard library component có:

```text
API tests
behavior tests
performance tests
thread tests
platform tests
```

---

## 436.179 — Runtime conformance

Runtime component phải test độc lập khỏi full std library.

---

## 436.180 — Freestanding conformance

Core language phải test được khi:

```text
allocator = none
runtime = none
```

---

## 436.181 — Embedded conformance

Target nhỏ có thể chạy subset conformance suite.

---

## 436.182 — WASM conformance

WASM output phải test cả:

```text
binary validity
execution
imports/exports
```

---

## 436.183 — Native startup conformance

Test entrypoint từng target.

---

## 436.184 — Linker portability

Linker tests phải không phụ thuộc host OS khi xử lý target object nếu có thể.

---

## 436.185 — Object parser security

External object files được xem là untrusted input.

---

## 436.186 — Compiler input security

Source code cũng có thể là hostile input.

Parser/type checker không được:

```text
stack overflow
integer overflow
unbounded memory growth
```

mà không có giới hạn thích hợp.

---

## 436.187 — Resource exhaustion

Compiler có giới hạn:

```text
recursion
AST size
comptime steps
memory
generated code
generic instantiations
```

---

## 436.188 — Diagnostics under resource exhaustion

Resource exhaustion phải tạo diagnostic rõ:

```text
compilation resource limit exceeded
```

thay vì compiler crash.

---

## 436.189 — Reproducible failure

Fuzz/test failure phải lưu:

```text
input
seed
compiler version
target
flags
```

---

## 436.190 — CI matrix

CI tối thiểu:

```text
Linux x86-64
Windows x86-64
macOS x86-64/AArch64
Linux AArch64
WASM
```

khi các backend tương ứng đã tồn tại.

---

## 436.191 — Tiered targets

Không yêu cầu mọi target phải có cùng mức maturity.

Target status:

```text
bootstrap
experimental
supported
```

là **development status**, không phải quality ranking.

---

## 436.192 — Release gate

Một target chỉ được release-supported khi đạt conformance threshold được định trước.

---

## 436.193 — Compiler release suite

Trước release:

```text
all conformance
all regression
backend smoke
ABI
linker
reproducibility
```

phải pass theo target support matrix.

---

## 436.194 — Release artifacts

Release compiler nên kèm:

```text
compiler
stdlib
target specs
checksums
debug symbols
source archive
test manifest
```

---

## 436.195 — Compiler version test

Artifact phải encode compiler version.

---

## 436.196 — Language edition test

Source edition phải được test đúng grammar/semantics của edition.

---

## 436.197 — Backward compatibility suite

Old valid programs được chạy qua compatibility suite.

---

## 436.198 — Intentional breaking changes

Nếu language edition có breaking change, test suite phải ghi explicit migration behavior.

---

## 436.199 — Correctness hierarchy

Axiom correctness được xem theo thứ tự:

```text
1. compiler does not crash
2. compiler diagnostics are correct
3. generated IR is valid
4. generated machine/object is valid
5. executable semantics are correct
6. optimization preserves semantics
7. ABI interoperability is correct
8. artifacts are reproducible when requested
```

---

# 436.200 — Hard invariants

BOOTSTRAP-436 khóa:

1. Compiler có conformance suite chính thức.
2. Mỗi compiler phase có test riêng.
3. Compiler có integration/end-to-end tests.
4. Negative tests kiểm tra stable diagnostic identity.
5. Formatter phải có idempotence tests.
6. AST/IR có golden tests khi thích hợp.
7. Optimizer phải được test với semantic equivalence.
8. `-O0` và optimized builds phải được differential-tested.
9. Machine encoder có golden instruction tests.
10. Object writer có format conformance tests.
11. Relocation có dedicated tests.
12. Linker có cross-object tests.
13. ABI có matrix test theo architecture/OS.
14. FFI có C ABI compatibility tests.
15. Native smoke test `main → 42` là bootstrap requirement.
16. WASM có binary + execution conformance.
17. Freestanding compilation được test riêng.
18. Parser/type checker/comptime/backend/linker đều được fuzz.
19. Fuzz input phải có timeout/resource limits.
20. Compiler crash trở thành regression test sau khi fix.
21. External object/package input được xử lý như untrusted input.
22. Comptime phải deterministic và resource-bounded.
23. Incremental build phải equivalent với clean build.
24. Warm-cache và cold-cache build phải equivalent.
25. Parallel build phải deterministic.
26. Package resolution phải deterministic với lockfile.
27. Binary reproducibility được test.
28. Interpreter/reference semantic path được dùng làm oracle khi thích hợp.
29. Interpreter không phải production runtime.
30. IR verifier là bắt buộc.
31. Object/linker verification được hỗ trợ.
32. Compiler self-hosting phải có bootstrap tests.
33. Test runner hỗ trợ parallel execution nhưng deterministic reporting.
34. Randomized tests phải ghi seed.
35. Fuzz failures phải được shrink và lưu corpus.
36. Performance benchmarks ghi environment.
37. Benchmark không được biến thành compiler correctness assumption.
38. Coverage không được coi là proof of correctness.
39. Security/resource exhaustion tests là một phần compiler QA.
40. Mỗi release target phải đạt support/conformance gate được định trước.
41. Compiler version và language edition phải được test.
42. ABI/API compatibility phải có regression fixtures.
43. AI tooling có thể consume test/build results machine-readably.
44. Compiler phải ưu tiên **correctness trước optimization**.
45. Không được dùng compiler bên thứ ba làm hidden correctness dependency của native backend.

**BOOTSTRAP-436 hoàn tất.**

---

# BOOTSTRAP-437 — LANGUAGE SECURITY, UNSAFE BOUNDARY, SANDBOXING & HARDENED EXECUTION

Task tiếp theo sẽ khóa **security model của chính ngôn ngữ**, đặc biệt quan trọng vì Axiom đã chọn:

```text
no GC
no mandatory borrow checker
explicit ownership
raw pointers
unsafe
FFI
native code
comptime
```

437 sẽ giải quyết ranh giới:

```text
SAFE AXIOM
   │
   ├── deterministic ownership
   ├── bounds checking
   ├── typed memory access
   ├── controlled FFI
   │
   ▼
UNSAFE AXIOM
   │
   ├── raw pointer
   ├── unchecked memory
   ├── ABI escape hatch
   └── platform intrinsics
```

đồng thời khóa:

- security invariants của memory model;
- integer/pointer safety;
- unsafe auditing;
- FFI isolation;
- comptime sandbox;
- package/build-script trust;
- executable hardening;
- ASLR/DEP/W^X/CFI/PAC;
- secrets;
- supply-chain integrity;
- capability-oriented APIs;
- sandboxed execution;
- secure defaults nhưng **không làm chậm production code một cách bắt buộc**.

**BOOTSTRAP-437 là task tiếp theo.**