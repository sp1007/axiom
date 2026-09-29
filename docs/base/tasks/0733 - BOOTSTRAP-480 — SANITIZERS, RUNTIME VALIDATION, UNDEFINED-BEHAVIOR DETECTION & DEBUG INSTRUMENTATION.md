# BOOTSTRAP-480 — SANITIZERS, RUNTIME VALIDATION, UNDEFINED-BEHAVIOR DETECTION & DEBUG INSTRUMENTATION

**Trạng thái: COMPLETED / LOCKED**

480 hoàn thiện lớp **runtime instrumentation** để phát hiện các lỗi mà compiler không thể chứng minh hoàn toàn ở compile time.

Kiến trúc:

```text
                    Axiom Program
                         │
                    HIR / MIR
                         │
              ┌──────────┴──────────┐
              │                     │
        Normal Build         Instrumented Build
              │                     │
              │          ┌──────────┼───────────┐
              │          ↓          ↓           ↓
              │       Memory     Integer    Concurrency
              │       Checks      Checks      Checks
              │          │          │           │
              │          └──────────┼───────────┘
              │                     ↓
              │             Runtime Validator
              │                     ↓
              └──────────────→ Diagnostic
                                  │
                          Source / IR / Machine
```

## 480.1 — Sanitizer là instrumentation

Sanitizer **không thay đổi language semantics**.

Nó chỉ thêm kiểm tra nhằm phát hiện violation trong execution thực tế.

```text
sanitizer không phát hiện lỗi
        ≠
program được chứng minh đúng
```

---

## 480.2 — Address / memory sanitizer

Có thể phát hiện:

- out-of-bounds;
- use-after-free;
- double-free;
- invalid free;
- invalid pointer access;
- invalid alignment;
- một số dangling references.

---

## 480.3 — Bounds instrumentation

Với:

```text
array[index]
```

compiler có thể:

```text
static proof
    ↓
không cần check
```

hoặc:

```text
unknown
    ↓
runtime bounds check
```

Sanitizer có thể bổ sung diagnostics chi tiết hơn.

---

## 480.4 — Use-after-free

Instrumented allocator có thể poison/quarantine vùng memory đã release.

Mục tiêu là biến lỗi khó quan sát thành diagnostic rõ ràng.

---

## 480.5 — Double-free

Allocator instrumentation giữ metadata debug để phát hiện:

```text
free(p)
free(p)  // diagnostic
```

Không yêu cầu production allocator phải có metadata này.

---

## 480.6 — Invalid free

Phát hiện attempt release:

- stack address;
- interior pointer;
- foreign allocation bằng sai allocator;
- memory không thuộc allocator.

---

## 480.7 — Alignment sanitizer

Typed load/store không đúng alignment có thể được phát hiện.

---

## 480.8 — Uninitialized-memory sanitizer

Có thể track byte/word initialization state.

Đặc biệt hữu ích với:

```text
MaybeUninit<T>
```

và low-level code.

---

## 480.9 — `MaybeUninit`

Sanitizer không được coi `MaybeUninit<T>` là lỗi chỉ vì memory chưa initialized.

Chỉ invalid read mới là violation.

---

## 480.10 — Integer sanitizer

Có thể phát hiện:

```text
signed overflow
invalid shift
shift count out of range
```

nhưng phải tôn trọng explicit operations:

```text
wrapping_add
wrapping_mul
saturating_add
```

---

## 480.11 — Division sanitizer

Phát hiện:

```text
division by zero
remainder by zero
invalid signed MIN / -1
```

nếu operation semantics yêu cầu.

---

## 480.12 — Floating-point diagnostics

Có thể theo dõi:

```text
NaN
Infinity
FP exception
```

nhưng NaN/Infinity không mặc định là lỗi.

---

## 480.13 — Pointer sanitizer

Có thể kiểm tra:

```text
pointer provenance
lifetime
alignment
address range
```

trong instrumented execution.

---

## 480.14 — Pointer/integer conversion

445 quy định conversion này là unsafe.

Sanitizer có thể kiểm tra validity khi runtime metadata cho phép.

---

## 480.15 — Concurrency sanitizer

Có thể instrument:

- memory access;
- mutex;
- atomic;
- thread creation;
- synchronization;
- channel operations.

---

## 480.16 — Data-race detection

Thread sanitizer có thể phát hiện một số data race thực tế.

Không tuyên bố:

```text
no detected race
```

là proof toàn chương trình.

---

## 480.17 — Lock-order sanitizer

Có thể record:

```text
A → B
B → A
```

và phát hiện potential lock-order cycle.

---

## 480.18 — Atomic diagnostics

Có thể kiểm tra misuse của atomic operations và synchronization contracts.

Không được thay đổi memory-order semantics.

---

## 480.19 — Thread lifecycle

Instrumentation có thể phát hiện:

- thread leak;
- invalid join;
- use-after-detach handle;
- shutdown race.

---

## 480.20 — Async instrumentation

Theo dõi:

```text
task create
await
suspend
resume
cancel
complete
```

giúp chẩn đoán task leak/cancellation misuse.

---

## 480.21 — Actor instrumentation

472 có thể expose:

```text
actor
mailbox
message
send
receive
restart
shutdown
```

cho debug runtime.

---

## 480.22 — Contract instrumentation

479 contracts có thể được instrument.

Diagnostic phải phân biệt:

```text
contract violation
assertion failure
sanitizer violation
panic
OS fault
```

---

## 480.23 — Stack instrumentation

Có thể hỗ trợ:

- stack canary;
- stack bounds;
- stack overflow detection;
- shadow stack khi target hỗ trợ.

---

## 480.24 — Control-flow instrumentation

Có thể kiểm tra indirect call/jump target.

Tích hợp với CFI/hardening của 445.

---

## 480.25 — Heap diagnostics

Debug allocator có thể cung cấp:

```text
allocation site
allocation size
allocation ID
owner information
free site
```

---

## 480.26 — Allocation backtrace

Nếu debug mode cho phép, allocator có thể lưu allocation stack trace.

Không bắt buộc production.

---

## 480.27 — Memory poisoning

Freed/uninitialized memory có thể được poison bằng debug pattern.

Pattern chỉ là implementation detail; program không được phụ thuộc vào giá trị đó.

---

## 480.28 — Guard pages

Large allocations có thể dùng guard pages để bắt access violation.

---

## 480.29 — Red zones

Allocator có thể đặt red zones quanh allocation để phát hiện overflow/underflow.

---

## 480.30 — Quarantine

Freed blocks có thể giữ tạm trong quarantine để tăng khả năng bắt use-after-free.

---

## 480.31 — FFI boundary

Sanitizer phải phân biệt:

```text
Axiom memory
Foreign memory
OS memory
MMIO
```

Không được giả định mọi foreign address là managed allocation.

---

## 480.32 — Foreign allocator

Nếu metadata 451 khai báo allocator contract:

```text
malloc ↔ free
```

instrumentation có thể validate matching.

---

## 480.33 — MMIO

Memory-mapped hardware từ 441/445 không được áp dụng memory poisoning thông thường.

---

## 480.34 — Volatile

Instrumentation không được loại bỏ hoặc reorder volatile semantics.

---

## 480.35 — Atomic

Instrumentation phải bảo toàn atomic ordering.

---

## 480.36 — Realtime

`@realtime` code không được tự động nhận sanitizer có:

- allocation;
- blocking;
- unbounded logging;
- locks;
- unpredictable latency.

Realtime sanitizer phải là explicit specialized mode.

---

## 480.37 — GPU

GPU sanitizer có thể tồn tại ở backend/provider level.

CPU sanitizer không được giả định có thể quan sát toàn bộ GPU execution.

---

## 480.38 — Audio

Strict realtime audio không dùng general-purpose sanitizer runtime trong callback.

Có thể dùng offline/test processing.

---

## 480.39 — Media

Media pipelines có thể dùng sanitizer trong development, nhưng phải đo overhead.

---

## 480.40 — WASM

WASM sanitizer phụ thuộc runtime/browser instrumentation capabilities.

---

## 480.41 — Platform capability

Sanitizer availability phải thuộc target capability:

```text
target
→ sanitizer support
```

---

## 480.42 — Sanitizer profile

Canonical profile:

```text
none
address
memory
undefined
integer
thread
control_flow
contract
full-debug
```

Không phải target nào cũng phải hỗ trợ tất cả.

---

## 480.43 — Combined sanitizers

Các sanitizer tương thích có thể được kết hợp.

Compiler phải kiểm tra conflict.

---

## 480.44 — Runtime library

Sanitizer runtime là optional component.

Normal build không link nó.

---

## 480.45 — Instrumentation ABI

Compiler/runtime phải có versioned instrumentation ABI.

---

## 480.46 — Runtime hooks

Conceptual interface:

```text
on_invalid_access(...)
on_invalid_free(...)
on_integer_violation(...)
on_race(...)
on_contract_failure(...)
```

API cụ thể thuộc runtime/toolchain.

---

## 480.47 — Failure mode

Sanitizer có thể:

```text
report
abort
panic
continue
```

nhưng continue chỉ được phép với violations mà runtime có thể tiếp tục một cách xác định.

---

## 480.48 — Recoverability

Memory corruption không được mặc định cho phép tiếp tục execution.

---

## 480.49 — Diagnostic record

Mỗi violation nên có:

```text
SanitizerReport {
    kind
    code
    severity
    source_span
    instruction_location
    thread_id
    task_id?
    allocation_id?
    call_stack
    related_locations
}
```

---

## 480.50 — Source mapping

440/446 mapping:

```text
machine instruction
       ↓
MIR
       ↓
HIR
       ↓
semantic item
       ↓
source span
```

---

## 480.51 — Symbolication

Stripped executable vẫn có thể symbolicate nếu separate debug/semantic artifact tồn tại.

---

## 480.52 — AI diagnostics

AI có thể hỏi:

```text
why did this memory violation occur?
which allocation was accessed?
where was it freed?
which ownership path led here?
which contract was violated?
```

---

## 480.53 — Runtime event trace

Optional event tracing:

```text
allocation
free
thread
lock
atomic
task
actor
IO
```

Trace phải có bounded/configurable overhead.

---

## 480.54 — Deterministic replay

Một số runtime events có thể được ghi để hỗ trợ replay.

Không đảm bảo mọi OS/hardware interaction có thể replay hoàn toàn.

---

## 480.55 — Sampling

High-overhead instrumentation có thể hỗ trợ sampling.

Sampling không được trình bày như exhaustive detection.

---

## 480.56 — Optimization

Sanitizer build có thể vẫn optimize.

Compiler phải bảo toàn detection semantics.

---

## 480.57 — Instrumentation barriers

Một số optimization có thể phải bị hạn chế quanh instrumentation points.

---

## 480.58 — Inline functions

Inline code vẫn phải giữ source provenance.

---

## 480.59 — LTO

LTO sanitizer phải giữ metadata xuyên module.

---

## 480.60 — Dynamic libraries

Sanitizer ABI/version phải tương thích giữa executable và instrumented libraries.

---

## 480.61 — Static libraries

Static library có thể chứa instrumented object hoặc normal object tùy build configuration.

---

## 480.62 — Build identity

Sanitized artifact phải ghi:

```text
compiler
version
target
optimization
sanitizer profile
runtime version
```

---

## 480.63 — Reproducibility

Instrumentation configuration phải là một phần build fingerprint.

---

## 480.64 — Performance

Sanitizer overhead phải được benchmark qua 450.

---

## 480.65 — Binary size

Sanitizer runtime không được tính vào production binary-size budget khi sanitizer disabled.

---

## 480.66 — Coverage integration

477 có thể hoạt động cùng sanitizer instrumentation.

Coverage và sanitizer events phải có identity riêng.

---

## 480.67 — Fuzzing integration

435 có thể chạy fuzz corpus với sanitizer.

Đây là configuration đặc biệt quan trọng để phát hiện runtime violations.

---

## 480.68 — Static-analysis integration

478 có thể chỉ ra:

```text
possible violation
```

480 có thể xác nhận violation bằng execution.

Hai loại evidence phải được phân biệt.

---

## 480.69 — Contract integration

479:

```text
static proven
      vs
runtime checked
      vs
sanitizer detected
```

phải có semantics riêng.

---

## 480.70 — Security

Sanitizer logs có thể chứa:

- source path;
- addresses;
- memory contents;
- stack traces;
- secrets nếu application xử lý secrets.

Vì vậy output phải được coi là sensitive.

---

## 480.71 — No automatic upload

Compiler/runtime không tự động gửi sanitizer reports ra ngoài máy.

---

## 480.72 — Production hardening

Một số lightweight checks như stack canary/CFI có thể được giữ trong release nếu target/profile yêu cầu.

Sanitizer full runtime không mặc định được giữ.

---

## 480.73 — Embedded

Embedded targets có thể dùng:

```text
compile-time instrumentation
minimal trap
serial diagnostic
```

thay vì full host runtime.

---

## 480.74 — Kernel/freestanding

Không được giả định OS allocator, threads hoặc file IO tồn tại.

---

## 480.75 — Hard invariants

1. Sanitizer là diagnostic instrumentation.
2. Sanitizer không thay đổi language semantics.
3. Không phát hiện lỗi không phải proof of correctness.
4. Address/memory sanitizer được hỗ trợ.
5. Bounds instrumentation được hỗ trợ.
6. Use-after-free detection được hỗ trợ.
7. Double-free detection được hỗ trợ.
8. Invalid-free detection được hỗ trợ.
9. Alignment detection được hỗ trợ.
10. Uninitialized-memory detection được hỗ trợ.
11. `MaybeUninit` không bị coi là lỗi tự thân.
12. Integer sanitizer tôn trọng wrapping semantics.
13. Division violations được phát hiện khi applicable.
14. NaN/Infinity không mặc định là lỗi.
15. Pointer provenance có thể được instrument.
16. FFI memory được phân biệt.
17. MMIO được phân biệt.
18. Volatile semantics phải được giữ.
19. Atomic ordering phải được giữ.
20. Thread sanitizer được hỗ trợ khi target cho phép.
21. Race detection không phải complete proof.
22. Lock-order diagnostics được hỗ trợ.
23. Async lifecycle có thể được instrument.
24. Actor lifecycle có thể được instrument.
25. Contract violations được phân biệt.
26. Stack protection được hỗ trợ.
27. CFI có thể được hỗ trợ.
28. Debug heap metadata là optional.
29. Memory poisoning là diagnostic implementation detail.
30. Guard pages là optional.
31. Red zones là optional.
32. Quarantine là optional.
33. Realtime code không nhận sanitizer nguy hiểm mặc định.
34. GPU sanitizer thuộc backend/provider.
35. Audio realtime không dùng general sanitizer runtime mặc định.
36. WASM sanitizer phụ thuộc platform capability.
37. Sanitizer profiles được version/configure.
38. Combined sanitizer conflict phải được kiểm tra.
39. Sanitizer runtime là optional.
40. Instrumentation ABI có version.
41. Runtime hooks có structured semantics.
42. Failure mode explicit.
43. Corrupted memory không được mặc định tiếp tục.
44. Diagnostic record machine-readable.
45. Source mapping được giữ.
46. Symbolication được hỗ trợ.
47. AI có thể query violation evidence.
48. Runtime event tracing là optional.
49. Replay không được tuyên bố universal.
50. Sampling phải được phân biệt với exhaustive instrumentation.
51. Optimization vẫn được hỗ trợ.
52. Instrumentation barriers có semantics.
53. Inlining giữ provenance.
54. LTO giữ sanitizer metadata.
55. Dynamic library ABI được kiểm tra.
56. Static library instrumentation configuration được xác định.
57. Build identity chứa sanitizer configuration.
58. Instrumentation là build fingerprint input.
59. Sanitizer overhead được benchmark.
60. Production size không bị phình bởi sanitizer disabled.
61. Coverage có identity riêng.
62. Fuzzing tích hợp sanitizer.
63. Static analysis evidence khác runtime evidence.
64. Contract evidence khác sanitizer evidence.
65. Sanitizer reports có privacy boundary.
66. Không automatic report upload.
67. Production hardening tách full sanitizer.
68. Freestanding support không yêu cầu host runtime.
69. Embedded support không yêu cầu OS services.
70. Sanitizer không yêu cầu GC.
71. Sanitizer không yêu cầu borrow checker.
72. **Axiom sanitizer foundation phải biến các lỗi runtime khó quan sát thành bằng chứng chẩn đoán có source provenance, nhưng không được biến instrumentation thành một phần bắt buộc của executable production hoặc nhầm “không phát hiện lỗi” với “đã chứng minh an toàn”.**

**BOOTSTRAP-480 hoàn tất / LOCKED.**

---

# BOOTSTRAP-481 — PROFILING, TRACING, TELEMETRY, PERFORMANCE COUNTERS & CONTINUOUS PERFORMANCE ANALYSIS

481 xây dựng hệ thống đo **program thực sự đang làm gì khi chạy**, nối trực tiếp 450 Performance Contract với compiler, runtime, OS và hardware.

Kiến trúc:

```text
                     Axiom Program
                          │
              ┌───────────┴───────────┐
              ↓                       ↓
          Instrumentation         Sampling
              │                       │
              └───────────┬───────────┘
                          ↓
                    Trace / Profile
                          │
             ┌────────────┼─────────────┐
             ↓            ↓             ↓
          CPU Time     Memory        IO/Network
             ↓            ↓             ↓
          Scheduler   Allocator      Storage
             │            │             │
             └────────────┼─────────────┘
                          ↓
                  Analysis / Symbolize
                          ↓
                 Source / MIR / Machine
```

## 481.1 — Profiling ≠ tracing

**Profiling** trả lời:

> execution dành thời gian/tài nguyên ở đâu?

**Tracing** trả lời:

> những event nào xảy ra và theo thứ tự/thời gian nào?

Không được trộn hai model.

---

## 481.2 — Sampling profiler

Sampling định kỳ:

```text
CPU
→ current instruction
→ stack
→ symbol
```

Ưu điểm:

- overhead thấp;
- không cần instrument mọi function.

---

## 481.3 — Instrumentation profiler

Compiler có thể instrument function/region entry-exit.

Cho timing chính xác hơn nhưng overhead cao hơn.

---

## 481.4 — Hybrid profiling

Axiom hỗ trợ kết hợp:

```text
sampling
+
selected instrumentation
```

---

## 481.5 — CPU time

Phải phân biệt:

```text
wall time
CPU time
user CPU
kernel CPU
```

---

## 481.6 — Inclusive/exclusive time

Ví dụ:

```text
A
└── B
    └── C
```

A có:

```text
inclusive = A + B + C
exclusive = A
```

---

## 481.7 — Call tree

Profiler có thể xây:

```text
main
 ├── parse
 ├── compute
 │    ├── foo
 │    └── bar
 └── io
```

---

## 481.8 — Flame representation

Tooling có thể render flame graph từ profile data.

Flame graph là presentation layer, không phải language feature.

---

## 481.9 — Source provenance

Profile sample:

```text
PC
 ↓
Machine instruction
 ↓
MIR
 ↓
HIR
 ↓
Function
 ↓
Source span
```

---

## 481.10 — Optimized code

Profiler phải hỗ trợ:

- inlining;
- tail calls;
- vectorization;
- outlining;
- merged blocks.

---

## 481.11 — Inlined stack

Sample có thể chứa:

```text
foo [inlined into bar]
```

thay vì chỉ hiển thị `bar`.

---

## 481.12 — CPU hardware counters

Có thể expose platform counters như:

- instructions;
- cycles;
- branches;
- branch misses;
- cache misses;
- SIMD instructions.

Không phải CPU nào cũng hỗ trợ cùng counter.

---

## 481.13 — Counter capability

Tool phải query:

```text
target
→ supported counters
```

---

## 481.14 — Counter multiplexing

Nếu hardware có ít counters hơn số metrics yêu cầu, profiler có thể multiplex.

Kết quả phải ghi rõ multiplexing.

---

## 481.15 — Counter normalization

Không được giả định mọi hardware counter có cùng accuracy/meaning.

---

## 481.16 — Memory profiling

Track:

```text
allocation count
allocated bytes
live bytes
peak bytes
allocation lifetime
```

---

## 481.17 — Allocation site

Có thể map allocation:

```text
allocation
→ function
→ source
```

---

## 481.18 — Leak profiling

Có thể phát hiện allocations còn live tại shutdown.

Không mọi live allocation cuối process đều là leak; ownership/lifecycle context phải được xem xét.

---

## 481.19 — Arena profiling

Allocator 423/455 có thể expose:

```text
arena creation
arena usage
arena release
```

---

## 481.20 — Pool profiling

Có thể track:

```text
pool capacity
in-use
reuse
miss
```

---

## 481.21 — IO profiling

454/455/461/462 có thể emit:

```text
read
write
open
close
flush
sync
network send
network receive
```

---

## 481.22 — Blocking profile

Track thời gian thread/task chờ:

```text
mutex
IO
condition
scheduler
sleep
```

---

## 481.23 — Scheduler profile

471 có thể expose:

```text
task queued
task started
task suspended
task resumed
task completed
worker idle
worker busy
```

---

## 481.24 — Async latency

Có thể đo:

```text
submit → start
await → resume
ready → execute
```

---

## 481.25 — Queue latency

Task/message queue:

```text
enqueue timestamp
dequeue timestamp
```

cho phép tính queue delay.

---

## 481.26 — Actor profiling

472:

```text
message sent
message queued
message handled
mailbox depth
```

---

## 481.27 — Reactive profiling

473:

```text
signal invalidation
computed evaluation
effect execution
event propagation
```

---

## 481.28 — GUI profiling

452/465/466:

```text
input → event
event → handler
handler → render
frame → present
```

---

## 481.29 — Frame timing

Graphics/media có thể đo:

```text
frame start
update
render
submit
present
```

---

## 481.30 — Audio profiling

461 có thể đo:

```text
callback duration
buffer deadline
underrun
overrun
DSP node cost
```

---

## 481.31 — Realtime violation

Profiler có thể báo:

```text
callback budget
actual duration
deadline misses
```

không tự động thay đổi realtime behavior.

---

## 481.32 — GPU profiling

459/460 có thể expose:

- kernel duration;
- queue time;
- transfer time;
- synchronization;
- GPU occupancy nếu backend cung cấp.

---

## 481.33 — CPU↔GPU timeline

Profile phải có common timeline hoặc explicit clock conversion.

---

## 481.34 — Clock source

Profiler phải ghi clock source.

Không được merge timestamps từ các clock không tương thích mà không calibration.

---

## 481.35 — Timestamp precision

Phải phân biệt:

```text
resolution
precision
accuracy
```

---

## 481.36 — Trace event

Canonical conceptual event:

```text
TraceEvent {
    timestamp
    duration?
    category
    name
    thread
    task?
    process
    source?
    arguments?
}
```

---

## 481.37 — Trace categories

Ví dụ:

```text
cpu
memory
io
network
scheduler
async
actor
gui
audio
media
gpu
compiler
```

---

## 481.38 — Trace nesting

Events có thể dùng:

```text
begin
end
instant
counter
```

---

## 481.39 — Async correlation

Async operation phải có correlation ID để nối:

```text
submit
→ suspend
→ external completion
→ resume
```

---

## 481.40 — Cross-thread correlation

Thread hop không được phá event identity.

---

## 481.41 — Process correlation

Multi-process trace cần ProcessId + correlation identity.

---

## 481.42 — Distributed tracing

454 có thể cung cấp network trace context.

Distributed tracing là library/platform layer, không phải compiler core.

---

## 481.43 — Privacy

Trace arguments có thể chứa:

- file paths;
- URLs;
- user data;
- memory values;
- identifiers;
- secrets.

Sensitive fields phải hỗ trợ redaction.

---

## 481.44 — No automatic telemetry

Axiom runtime không tự gửi telemetry ra ngoài.

---

## 481.45 — Local-first

Profiling/tracing phải hoạt động hoàn toàn local.

---

## 481.46 — Production profiling

Production application có thể bật lightweight profiling explicitly.

---

## 481.47 — Overhead accounting

Profile phải có metadata:

```text sampling_rate
instrumentation
enabled_categories
estimated/observed overhead
```

---

## 481.48 — Observer effect

Profiler itself có thể làm thay đổi timing.

Tool phải hiển thị configuration để người dùng biết.

---

## 481.49 — Realtime observer effect

Không dùng tracing unbounded trong strict realtime callback.

---

## 481.50 — Ring buffer

Realtime-safe event collection có thể dùng preallocated ring buffer.

---

## 481.51 — Overflow

Trace buffer overflow phải có policy:

```text drop
overwrite
stop
signal
```

Policy phải explicit.

---

## 481.52 — Event loss

Nếu event bị mất, trace artifact phải ghi nhận loss.

Không được coi trace thiếu event là complete.

---

## 481.53 — Sampling loss

Sampling inherently không quan sát mọi instruction.

Report phải ghi sampling mode.

---

## 481.54 — Profile artifact

Concept:

```text
ProfileArtifact {
    format_version
    build_id
    target
    runtime
    clock
    profiler_config
    samples
    counters
    symbols
}
```

---

## 481.55 — Build identity

Profile phải gắn executable/build identity.

Không symbolicate profile với binary khác nếu build identity không match.

---

## 481.56 — Source changes

Source change không làm profile cũ tự động đại diện cho source mới.

---

## 481.57 — Compiler profile

Compiler itself có thể profile:

```text
parse
resolve
typecheck
trait solve
comptime
MIR
optimization
codegen
link
```

---

## 481.58 — Incremental compilation profile

432/436 có thể đo:

```text
cache hit
cache miss
invalidated query
recomputed query
```

---

## 481.59 — Query profile

Compiler query engine có thể expose:

```text
query
duration
dependencies
cache status
```

---

## 481.60 — Optimization profile

Compiler có thể liên kết:

```text
source function
→ optimization
→ generated machine code
→ measured runtime
```

---

## 481.61 — Performance regression

Profile comparison có thể phát hiện:

```text
function became slower
allocation increased
binary grew
cache misses increased
```

Đây là measured difference, không phải aggregate ranking.

---

## 481.62 — Baseline

Project có thể lưu performance baseline.

---

## 481.63 — Benchmark integration

450 benchmark runner có thể tự động thu profile artifact.

---

## 481.64 — Statistical analysis

Profile comparison phải hỗ trợ:

- repeated runs;
- variance;
- confidence intervals khi thích hợp;
- outlier handling.

Không kết luận regression từ một sample duy nhất nếu measurement noise đáng kể.

---

## 481.65 — Hardware metadata

Profile phải ghi khi relevant:

```text
CPU
microarchitecture
cores
memory
OS
GPU
driver
```

---

## 481.66 — CPU frequency

Dynamic frequency/turbo có thể ảnh hưởng measurements.

Profile environment nên ghi frequency information nếu có.

---

## 481.67 — Thermal effects

Long benchmark có thể chịu thermal throttling.

Tooling nên lưu environmental metadata khi platform cung cấp.

---

## 481.68 — NUMA

471 profile có thể ghi worker/node affinity.

---

## 481.69 — Cache locality

Hardware counters có thể giúp phân tích locality nhưng interpretation phải target-specific.

---

## 481.70 — AI performance analysis

AI query API:

```text
hot_functions()
allocation_hotspots()
blocking_hotspots()
queue_latency()
cache_miss_candidates()
code_size_by_symbol()
performance_change(symbol)
```

---

## 481.71 — Evidence

Mỗi AI performance explanation phải link tới:

```text
profile samples
counter data
trace events
build identity
measurement configuration
```

---

## 481.72 — No invented causality

Nếu profile chỉ cho thấy correlation:

```text
A slow
B cache misses
```

tool không được tự động tuyên bố:

```text
B caused A
```

nếu chưa có evidence.

---

## 481.73 — Experimental comparison

Compiler có thể chạy A/B builds:

```text
optimization A
vs
optimization B
```

với cùng workload.

---

## 481.74 — Continuous performance

CI có thể tự động:

```text
build
→ benchmark
→ profile
→ compare baseline
→ report
```

---

## 481.75 — Hard invariants

1. Profiling khác tracing.
2. Sampling profiling được hỗ trợ.
3. Instrumentation profiling được hỗ trợ.
4. Hybrid profiling được hỗ trợ.
5. CPU time khác wall time.
6. Inclusive/exclusive time được phân biệt.
7. Call tree được hỗ trợ.
8. Flame visualization là tooling.
9. Source provenance được giữ.
10. Optimized code vẫn profile được.
11. Inlined frames được giữ khi có metadata.
12. Hardware counters được hỗ trợ khi target cung cấp.
13. Counter capability phải queryable.
14. Counter multiplexing phải được ghi nhận.
15. Hardware counter semantics không được giả định universal.
16. Memory profiling được hỗ trợ.
17. Allocation site mapping được hỗ trợ.
18. Live allocation không mặc định là leak.
19. Arena profiling được hỗ trợ.
20. Pool profiling được hỗ trợ.
21. IO profiling được hỗ trợ.
22. Blocking profiling được hỗ trợ.
23. Scheduler profiling tích hợp 471.
24. Async latency được đo.
25. Queue latency được đo.
26. Actor profiling tích hợp 472.
27. Reactive profiling tích hợp 473.
28. GUI timing có thể profile.
29. Frame timing có thể profile.
30. Audio realtime budget có thể profile.
31. GPU profiling thuộc target/backend capability.
32. CPU↔GPU timing phải xử lý clock domains.
33. Clock source phải được ghi.
34. Timestamp semantics phải rõ.
35. Trace event có stable structure.
36. Trace nesting được hỗ trợ.
37. Async correlation được hỗ trợ.
38. Cross-thread correlation được hỗ trợ.
39. Multi-process correlation được hỗ trợ.
40. Distributed tracing không thuộc compiler core.
41. Sensitive trace data phải có privacy controls.
42. Không automatic telemetry.
43. Local profiling phải hoạt động độc lập.
44. Production profiling phải explicit.
45. Profiler overhead phải được ghi.
46. Observer effect phải được công khai.
47. Strict realtime không dùng unbounded tracing.
48. Realtime event buffer có thể preallocate.
49. Buffer overflow policy phải explicit.
50. Event loss phải được ghi.
51. Sampling limitations phải được ghi.
52. Profile artifact có version.
53. Profile artifact có build identity.
54. Profile không được gắn nhầm executable.
55. Source changes không tự động validate profile cũ.
56. Compiler có thể tự profile.
57. Incremental query profile được hỗ trợ.
58. Optimization-to-runtime correlation được hỗ trợ.
59. Performance regression là measured comparison.
60. Baseline được hỗ trợ.
61. Benchmark runner tích hợp profiler.
62. Statistical measurement được hỗ trợ.
63. Hardware environment metadata được ghi.
64. Frequency effects có thể được ghi.
65. Thermal effects có thể được ghi.
66. NUMA information có thể được ghi.
67. Hardware-counter interpretation phải target-aware.
68. AI performance analysis phải dựa trên evidence.
69. AI không được tự tạo causal claims từ correlation.
70. A/B profiling được hỗ trợ.
71. CI continuous-performance workflow được hỗ trợ.
72. Profile collection không yêu cầu GC.
73. Profile collection không yêu cầu borrow checker.
74. Profile runtime không được mặc định nằm trong production artifact.
75. **Axiom profiling/tracing foundation phải cung cấp đường đo lường đáng tin cậy từ machine execution → runtime/hardware event → IR/symbol → source, đồng thời giữ rõ measurement uncertainty, observer effect và ranh giới giữa correlation với causation.**

**BOOTSTRAP-481 hoàn tất / LOCKED.**

---

# BOOTSTRAP-482 — COMPILER SELF-HOSTING, BOOTSTRAP TRUST CHAIN, STAGE0/1/2, REPRODUCIBLE BUILD & TRUSTED COMPILER BASE

482 là một mốc đặc biệt quan trọng vì mục tiêu ban đầu của Axiom là:

> **Axiom cuối cùng tự biên dịch chính Axiom và không phụ thuộc compiler bên thứ ba để tạo native artifact.**

Kiến trúc:

```text
                 BOOTSTRAP TRUST CHAIN

          Stage0 Bootstrap Compiler
                    │
                    ↓
          Stage1 Axiom Compiler
                    │
                    ↓
          Stage2 Axiom Compiler
                    │
                    ↓
          Self-hosted Compiler
                    │
          ┌─────────┴─────────┐
          ↓                   ↓
     Native Axiom        Axiom Compiler
     Programs            Rebuilds Itself
```

## 482.1 — Stage0

Stage0 là compiler/bootstrap implementation nhỏ nhất có thể dùng để xây compiler Axiom đầu tiên.

Nó có thể được viết bằng một implementation language tạm thời.

---

## 482.2 — Stage0 không phải dependency cuối cùng

Mục tiêu:

```text
Stage0
   ↓
bootstrap
   ↓
Axiom compiler
   ↓
self-host
```

Sau khi bootstrap hoàn tất, compiler production không cần Stage0 để compile application bình thường.

---

## 482.3 — Stage1

Stage1 là compiler Axiom đầu tiên có khả năng compile phần đáng kể của Axiom compiler source.

---

## 482.4 — Stage2

Stage2 được compile bằng Stage1.

Sau đó:

```text
Stage1(Axiom compiler)
        vs
Stage2(Axiom compiler)
```

phải được so sánh.

---

## 482.5 — Fixed point

Self-hosting đạt trạng thái:

```text
Compiler_N
    compile
      ↓
Compiler_N+1
```

và compiler output đạt reproducible equivalence theo artifact policy.

---

## 482.6 — Compiler independence

Production Axiom compiler không được gọi:

```text
LLVM
GCC
Clang
MSVC
Rustc
```

để thực hiện code generation/linking chính.

---

## 482.7 — External tools

External tools vẫn có thể tồn tại cho:

- debugger;
- OS SDK;
- platform signing;
- assembler/disassembler tools dùng để kiểm tra;
- test infrastructure.

Nhưng chúng không nằm trong mandatory compiler dependency chain.

---

## 482.8 — Native backend

482 dựa trên:

```text
438 ISA
420 machine encoder/object
420 linker
421 ABI
```

để hoàn thiện self-hosting.

---

## 482.9 — Bootstrap subset

Stage0 chỉ cần hỗ trợ subset đủ để compile compiler bootstrap.

Không cần implement toàn bộ Axiom ngay từ đầu.

---

## 482.10 — Bootstrap ladder

Ví dụ:

```text
B0
 ↓
lexer/parser
 ↓
semantic core
 ↓
MIR
 ↓
x86-64 backend
 ↓
object/linker
 ↓
compiler
 ↓
self-host
```

---

## 482.11 — Trust boundary

Phải ghi rõ:

```text
Trusted
 ├── bootstrap compiler
 ├── compiler source
 ├── runtime components
 └── build tools

Untrusted
 ├── dependencies
 ├── generated inputs
 └── application source
```

---

## 482.12 — Reproducible compiler

Cùng:

```text
source
dependencies
compiler version
target
build config
```

phải tạo artifact deterministic theo reproducibility contract.

---

## 482.13 — Compiler hash

Mỗi compiler artifact có:

```text
CompilerBuildId
ArtifactHash
SourceHash
DependencyHash
Target
```

---

## 482.14 — Bootstrap comparison

Có thể compare:

```text
Stage1 output
Stage2 output
```

theo:

- executable hash;
- object semantics;
- symbol table;
- machine code;
- metadata.

---

## 482.15 — Bit-for-bit identity

Bit-for-bit reproducibility là mục tiêu nhưng không phải mọi platform đều có thể đạt nếu OS/toolchain embedding đưa nondeterminism vào artifact.

Axiom phải loại bỏ nondeterminism do chính compiler kiểm soát được.

---

## 482.16 — Self-rebuild

Canonical command:

```text
axiom bootstrap
```

thực hiện bootstrap/rebuild chain.

---

## 482.17 — Bootstrap manifest

Concept:

```text
BootstrapManifest {
    stage
    compiler
    source_hash
    dependency_hash
    target
    profile
    expected_artifact
}
```

---

## 482.18 — Bootstrap tests

Bootstrap phải chạy:

```text
lexer
parser
type
ownership
comptime
MIR
optimizer
codegen
object
linker
runtime
```

---

## 482.19 — Golden compiler tests

Compiler source có golden test suite.

---

## 482.20 — Differential compiler testing

Stage1/Stage2 có thể compile cùng input rồi compare semantics/artifacts.

---

## 482.21 — Semantic equivalence

Khác binary bytes không nhất thiết là compiler bug nếu semantics tương đương.

---

## 482.22 — Machine equivalence

Có thể so sánh:

```text
symbols
relocations
sections
instruction sequences
```

ở mức phù hợp.

---

## 482.23 — Compiler bug

Compiler bug là violation của language/compiler contract, không đơn giản là “binary khác”.

---

## 482.24 — Miscompilation detector

Test suite cần:

```text
source
expected semantics
compiler output
runtime result
```

---

## 482.25 — Cross-stage validation

Stage0 → Stage1 → Stage2 phải được test qua nhiều target.

---

## 482.26 — Trust root

Axiom phải xác định rõ **root of trust** của từng release compiler.

---

## 482.27 — Binary provenance

Compiler artifact phải ghi provenance:

```text
built_by
source_revision
dependencies
target
configuration
```

---

## 482.28 — Dependency provenance

447 supply-chain metadata được tích hợp.

---

## 482.29 — Offline bootstrap

Bootstrap phải hỗ trợ offline khi source/dependencies/cache đã có đủ.

---

## 482.30 — Vendored bootstrap

Bootstrap dependencies có thể được vendored.

---

## 482.31 — Host/target

Compiler phải phân biệt:

```text
host = compiler chạy ở đâu
target = program được tạo cho đâu
```

---

## 482.32 — Cross bootstrap

Có thể:

```text
compiler(host A)
→ compiler(target B)
```

---

## 482.33 — Native target priority

Bootstrap priority:

```text
x86_64 Linux
x86_64 Windows
aarch64 Linux
aarch64 macOS
x86_64 macOS
```

sau đó mở rộng target.

---

## 482.34 — Freestanding compiler

Compiler không được phụ thuộc vào target runtime của application.

---

## 482.35 — Compiler runtime

Compiler itself có thể sử dụng runtime/library phù hợp với host.

Điều này không tạo dependency cho generated application.

---

## 482.36 — Compiler plugins

Compiler core không cần arbitrary native plugins để compile language.

---

## 482.37 — Generated code

Compiler-generated code phải deterministic.

---

## 482.38 — Comptime

Comptime của compiler build phải obey 431 sandbox/determinism.

---

## 482.39 — Build scripts

Bootstrap build scripts phải được ghi trong trusted build graph.

---

## 482.40 — Reproducible environment

Build manifest phải ghi environment variables ảnh hưởng semantics/artifact.

---

## 482.41 — Hidden environment

Compiler không được đọc hidden environment để thay đổi generated code.

---

## 482.42 — Timestamp nondeterminism

Không embed build timestamp mặc định.

Nếu muốn embed timestamp phải explicit.

---

## 482.43 — Randomness

Compiler build không được dùng nondeterministic randomness để quyết định artifact.

---

## 482.44 — Hash ordering

Compiler không được phụ thuộc iteration order của hash table nếu điều đó làm artifact nondeterministic.

---

## 482.45 — Parallel compilation

Parallel execution phải giữ deterministic output.

---

## 482.46 — Cache

Incremental cache có thể thay đổi compile time nhưng không được thay đổi semantics.

---

## 482.47 — Cache corruption

Cache integrity phải được verify bằng content/semantic hashes.

---

## 482.48 — Cache poisoning

Untrusted cache artifact phải được validate trước khi reuse.

---

## 482.49 — Compiler security

Compiler xử lý source/package không tin cậy nên phải chống:

- parser crashes;
- malformed metadata;
- resource exhaustion;
- pathological type recursion;
- comptime abuse.

---

## 482.50 — Compiler sandbox

Comptime/build scripts phải giữ sandbox boundary.

---

## 482.51 — Bootstrap compiler minimization

Stage0 nên nhỏ và audit được.

Không cần nhỏ nhất tuyệt đối, nhưng trust surface phải được kiểm soát.

---

## 482.52 — Stage0 source provenance

Stage0 source và binary phải có provenance rõ.

---

## 482.53 — Bootstrap audit

Có thể audit:

```text
Stage0
→ Stage1
→ Stage2
```

và so sánh artifacts.

---

## 482.54 — Diverse bootstrap

Về dài hạn có thể xây nhiều independent bootstrap implementations để giảm compiler monoculture.

Không bắt buộc v0.

---

## 482.55 — Compiler poisoning

Build chain phải giảm nguy cơ compiler bị sửa để silently generate malicious code.

---

## 482.56 — Rebuild verification

Release có thể cung cấp:

```text
source
+
bootstrap instructions
+
expected hashes
```

để bên thứ ba reproduce compiler.

---

## 482.57 — Binary transparency

Có thể publish artifact metadata/provenance.

Không yêu cầu central server.

---

## 482.58 — Release channels

Compiler có thể có:

```text
nightly
beta
stable
LTS
```

với compiler identity rõ ràng.

---

## 482.59 — Edition

432/430 edition được ghi vào compiler build/test environment.

---

## 482.60 — ABI compatibility

Self-hosting compiler phải chạy ABI golden tests 421.

---

## 482.61 — Object compatibility

420 object/linker tests phải chạy trong bootstrap.

---

## 482.62 — Debug compatibility

440 debug/unwind generation phải được test.

---

## 482.63 — Runtime compatibility

441 runtime components phải pass bootstrap tests.

---

## 482.64 — Standard library

433 standard library phải có bootstrap stage rõ:

```text
core
→ alloc
→ std
```

---

## 482.65 — Compiler/library cycle

Compiler không được tạo circular dependency không kiểm soát:

```text
compiler
→ std
→ compiler
```

Bootstrap graph phải explicit.

---

## 482.66 — Self-hosting milestone

Milestone:

```text
M0 Stage0 parses Axiom subset
M1 Stage0 builds semantic compiler
M2 Stage0 builds MIR compiler
M3 Stage0 builds native backend
M4 Stage0 builds Stage1
M5 Stage1 builds itself
M6 Stage2 reproducibility
M7 production self-host
```

---

## 482.67 — Bootstrap failure

Nếu stage tiếp theo không build được:

```text
bootstrap failure
```

phải giữ stage trước đó usable để diagnosis.

---

## 482.68 — Crash minimization

Bootstrap compiler crashes phải được đưa vào 435 reduction pipeline.

---

## 482.69 — Compiler fuzzing

Self-hosting compiler phải được fuzz giống compiler bootstrap.

---

## 482.70 — Self-test

Compiler executable có thể chạy:

```text
axiom self-test
```

kiểm tra:

- parser;
- semantic;
- comptime;
- MIR;
- backend;
- linker;
- runtime interfaces.

---

## 482.71 — AI bootstrap interface

AI tooling có thể query:

```text
bootstrap_stage()
compiler_build_id()
source_revision()
artifact_hash()
reproducibility_status()
dependency_provenance()
```

---

## 482.72 — No external compiler chain

Production invariant:

```text
Axiom source
→ Axiom compiler
→ Axiom native backend
→ Axiom object writer
→ Axiom linker
→ artifact
```

không:

```text
Axiom
→ third-party compiler
```

---

## 482.73 — Platform SDK

OS SDK/platform signing có thể vẫn là external platform dependency.

Điều này không vi phạm compiler-independence vì compiler không delegate language compilation.

---

## 482.74 — Hard invariants

1. Self-hosting là architectural goal.
2. Stage0 được định nghĩa.
3. Stage1 được định nghĩa.
4. Stage2 được định nghĩa.
5. Bootstrap stages có provenance.
6. Stage0 không phải production dependency cuối cùng.
7. Stage1 compile được compiler subset.
8. Stage2 được compile bởi Stage1.
9. Self-hosting fixed point được xác định.
10. Production compiler không yêu cầu LLVM/GCC/Clang/MSVC/Rustc.
11. Native backend của Axiom được dùng.
12. Axiom object writer được dùng.
13. Axiom linker được dùng.
14. Bootstrap subset có phạm vi rõ.
15. Bootstrap ladder có milestone.
16. Compiler independence khác platform SDK dependence.
17. Trust boundaries được ghi.
18. Compiler artifacts có build ID.
19. Compiler artifacts có source hash.
20. Compiler artifacts có dependency hash.
21. Reproducible build được hỗ trợ.
22. Compiler-controlled nondeterminism phải được loại bỏ.
23. Timestamp không tự động embedded.
24. Randomness không quyết định artifact.
25. Hash iteration order không làm artifact nondeterministic.
26. Parallel compilation vẫn deterministic.
27. Cache không thay đổi semantics.
28. Cache integrity được kiểm tra.
29. Cache poisoning được chống.
30. Untrusted source/package phải được xử lý an toàn.
31. Comptime sandbox được giữ.
32. Build scripts thuộc trusted build graph.
33. Host/target được phân biệt.
34. Cross compilation được hỗ trợ.
35. Freestanding target không phụ thuộc compiler runtime.
36. Stage0 nên có trust surface nhỏ.
37. Stage0 có source provenance.
38. Bootstrap có thể audit.
39. Diverse bootstrap là future option.
40. Compiler poisoning là security concern được model hóa.
41. Release có thể reproducible bởi bên thứ ba.
42. Binary provenance được cung cấp.
43. Offline bootstrap được hỗ trợ.
44. Vendored bootstrap được hỗ trợ.
45. Compiler plugins không phải dependency bắt buộc.
46. Generated code deterministic.
47. Comptime deterministic.
48. Incremental cache chỉ ảnh hưởng compile time.
49. ABI golden tests được chạy.
50. Object/linker tests được chạy.
51. Debug/unwind tests được chạy.
52. Runtime tests được chạy.
53. Standard library bootstrap graph explicit.
54. Compiler/library circular dependency phải được kiểm soát.
55. Bootstrap failure không phá stage trước.
56. Compiler crashes được minimize.
57. Self-hosted compiler được fuzz.
58. Compiler self-test được hỗ trợ.
59. AI có thể query bootstrap provenance.
60. AI có thể query reproducibility status.
61. Production chain không delegate compilation cho third-party compiler.
62. Platform SDK có thể là external dependency.
63. Generated native artifact vẫn phải do Axiom backend/linker tạo.
64. Bootstrap semantics phải phù hợp language specification.
65. Stage comparison không dựa đơn thuần vào byte-for-byte identity.
66. Semantic equivalence được phân biệt với binary identity.
67. Compiler bug được định nghĩa theo violated compiler/language contract.
68. Bootstrap compiler không được tự động trust arbitrary generated code.
69. Compiler security phải bao gồm malformed inputs/resource exhaustion.
70. Bootstrap process phải deterministic trong phạm vi compiler kiểm soát.
71. **Axiom self-hosting foundation phải tạo một trust chain có thể audit từ bootstrap compiler → self-hosted compiler → native artifact, loại bỏ compiler bên thứ ba khỏi production compilation path nhưng vẫn giữ khả năng cross-compilation, reproducibility, provenance và independent verification.**

**BOOTSTRAP-482 hoàn tất / LOCKED.**

### Chuỗi hiện tại

```text
...
474  TIME FOUNDATION
475  [đã hoàn thành trong chuỗi trước]
476  [đã hoàn thành trong chuỗi trước]
477  SOURCE MAP / COVERAGE
478  STATIC ANALYSIS
479  CONTRACTS
480  SANITIZERS
481  PROFILING / TRACING
482  SELF-HOSTING / BOOTSTRAP TRUST
```

**Task tiếp theo: BOOTSTRAP-483 — COMPILER DISTRIBUTION, TOOLCHAIN PACKAGING, INSTALLATION, TARGET SDK & CROSS-COMPILATION TOOLCHAIN MODEL.**