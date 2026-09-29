# BOOTSTRAP-440 — DEBUG INFO, STACK UNWINDING, PANIC/EXCEPTION RUNTIME & NATIVE DEBUGGER CONTRACT

**Trạng thái: COMPLETED / LOCKED**

Mục tiêu của 440 là đảm bảo Axiom có thể debug native binary thực tế mà **không đưa overhead debug vào release executable**.

Kiến trúc:

```text
Source
 ↓
AST / HIR
 ↓
MIR
 ↓
LIR
 ↓
Machine IR
 ↓
Machine Code
 │
 ├── Debug Mapping
 ├── Variable Location
 ├── Inline Mapping
 └── Unwind Metadata
 ↓
Object
 ↓
Executable + Debug Artifact
 ↓
Debugger / Crash Reporter / AI Diagnostics
```

---

## 440.1 — Debug information là metadata

Debug information không phải một phần của language semantics.

Nó có thể bị loại hoàn toàn khỏi release artifact.

---

## 440.2 — Debug levels

Axiom chuẩn hóa:

```text
debug = full debug
line = source-line mapping tối thiểu
none = không debug information
```

---

## 440.3 — Debug profile

Mặc định debug build:

```text
-O0
debug info
assertions enabled
```

release:

```text
-O2
debug info optional
```

---

## 440.4 — Source identity

Debug metadata tham chiếu:

```text
FileId
ContentHash
Path
Line
Column
```

---

## 440.5 — Source path normalization

Để reproducible builds, compiler không embed absolute path mặc định.

Ví dụ:

```text
/project/src/main.ax
```

thay vì:

```text
C:\Users\...\project\src\main.ax
```

---

## 440.6 — Debug compilation unit

Mỗi package/module compilation unit có:

```text
CompileUnit {
    package
    module
    source_files
    compiler_version
    target
}
```

---

## 440.7 — Function debug record

Function metadata:

```text
DebugFunction {
    symbol
    source_span
    declaration_span
    machine_range[]
}
```

---

## 440.8 — Line table

Machine instruction range map về:

```text
File
Line
Column
```

---

## 440.9 — Statement boundaries

Compiler giữ boundary đủ để debugger step:

```text
next
step
continue
```

hợp lý.

---

## 440.10 — Instruction mapping

Một source statement có thể map tới nhiều machine instructions.

Không yêu cầu 1:1.

---

## 440.11 — Multiple source instructions

Optimizer có thể merge nhiều source operations thành một instruction sequence.

Debug metadata giữ mapping nhiều-nhiều khi cần.

---

## 440.12 — Optimized-out values

Nếu variable không còn tồn tại sau optimization:

Debugger phải báo:

```text
<optimized out>
```

không được hiển thị giá trị giả.

---

## 440.13 — Variable location

Một variable có thể chuyển:

```text
register
→ stack
→ register
```

trong lifetime.

Debug info cần location ranges.

---

## 440.14 — Location expression

Conceptual:

```text
Location =
    Register
  | StackOffset
  | Memory
  | Constant
  | Composite
  | Unavailable
```

---

## 440.15 — SSA debug value

SSA value:

```text
v17
```

có thể được map:

```text
source variable x → v17
```

---

## 440.16 — Phi debug

Nếu variable có nhiều SSA definitions:

```text
x = phi(v1, v2)
```

debugger phải xác định location/value theo CFG path.

---

## 440.17 — Inline function

Nếu:

```text
foo()
```

được inline vào:

```text
bar()
```

debug info phải giữ inline call-site tree.

---

## 440.18 — Inline call tree

Conceptual:

```text
bar
 └── foo @ main.ax:20
      └── helper @ math.ax:7
```

---

## 440.19 — Stack frame identity

Debugger phải phân biệt:

```text
physical machine frame
```

với:

```text
logical inline frame
```

---

## 440.20 — Backtrace

Runtime có thể tạo:

```text
frame #0
frame #1
frame #2
...
```

với:

```text
function
module
source location
```

nếu symbols/debug info khả dụng.

---

## 440.21 — Unwind metadata

Axiom hỗ trợ unwind metadata độc lập với debug information.

Điều này rất quan trọng:

```text
debug info ≠ unwind info
```

---

## 440.22 — Unwind không cần full debug

Release binary có thể có unwind table nhưng không có source debug information.

---

## 440.23 — Unwind purpose

Unwind phục vụ:

- panic;
- exception;
- stack trace;
- debugger;
- crash reporting;
- cleanup.

---

## 440.24 — Unwind strategy

Target backend chọn một trong:

```text
DWARF CFI
Windows unwind metadata
platform-specific unwind format
```

---

## 440.25 — Frame pointer fallback

Axiom có thể dùng frame pointer khi:

```text
debug
simple unwind
special target
```

nhưng release không bắt buộc.

---

## 440.26 — Frame-pointer omission

Release có thể:

```text
omit-frame-pointer
```

nếu unwind metadata vẫn đủ.

---

## 440.27 — Stack walking

Debugger ưu tiên:

```text
unwind metadata
```

sau đó frame-pointer fallback nếu available.

---

## 440.28 — Leaf function unwind

Leaf functions có thể có minimal unwind metadata.

---

## 440.29 — Prologue/epilogue awareness

Compiler phải emit unwind information tương ứng với machine prologue/epilogue.

---

## 440.30 — Unwind state

Conceptual:

```text
PC range
CFA rule
register restore rules
```

---

## 440.31 — CFA

Canonical concept:

```text
Canonical Frame Address
```

được mô tả theo target unwind format.

---

## 440.32 — Callee-saved registers

Unwind metadata phải biết cách restore callee-saved registers.

---

## 440.33 — Stack allocation

Dynamic/static stack allocation phải được phản ánh trong unwind rules nếu function có thể unwind.

---

## 440.34 — Dynamic alloca

Function dùng dynamic stack allocation phải có unwind metadata chính xác trên mọi path.

---

## 440.35 — Panic abort

Với:

```text
panic=abort
```

compiler không cần full panic unwinding.

Panic path:

```text
panic
 ↓
panic handler
 ↓
abort
```

---

## 440.36 — Panic unwind

Với:

```text
panic=unwind
```

panic:

```text
panic
 ↓
unwind runtime
 ↓
cleanup frames
 ↓
terminate/catch
```

---

## 440.37 — Cleanup integration

Unwind phải chạy:

```text
drop
defer
resource cleanup
```

theo BOOTSTRAP-423.

---

## 440.38 — Cleanup landing pads

Nếu target exception model yêu cầu:

```text
landing pad / cleanup region
```

backend tạo chúng từ cleanup graph.

---

## 440.39 — Double panic

Nếu destructor/cleanup gây panic trong quá trình unwind:

```text
abort
```

---

## 440.40 — FFI unwind boundary

Không cho:

```text
Axiom panic
→ xuyên qua C ABI
```

một cách ngầm định.

---

## 440.41 — FFI boundary policy

Có thể:

```text
catch → Result
catch → error code
catch → abort
```

tùy API contract.

---

## 440.42 — Native exception interoperability

Nếu Axiom function phải gọi native exception API:

```text
extern
```

thì exception semantics được khai báo ở ABI boundary.

---

## 440.43 — Exception ≠ Result

Hai cơ chế độc lập:

```text
Result
→ explicit control flow

Exception/unwind
→ exceptional control flow
```

---

## 440.44 — No hidden exception

Axiom ordinary function không tự phát sinh native exception.

---

## 440.45 — DWARF

ELF/Linux backend có thể emit DWARF:

```text
.debug_info
.debug_abbrev
.debug_line
.debug_str
.debug_loc
.debug_ranges
```

tùy debug level.

---

## 440.46 — DWARF generation

Axiom không dùng external compiler để generate debug information.

Compiler có DWARF writer riêng.

---

## 440.47 — CodeView

Windows backend có thể emit CodeView records phù hợp PDB generation.

---

## 440.48 — PDB

Axiom toolchain có thể tạo PDB hoặc tương thích với Windows debug ecosystem.

---

## 440.49 — Mach-O debug

macOS/iOS hỗ trợ:

```text
dSYM
```

hoặc embedded debug configuration.

---

## 440.50 — Debug artifact separation

Ví dụ:

```text
app.exe
app.pdb
```

hoặc:

```text
app
app.dSYM
```

---

## 440.51 — Debug artifact identity

Debug artifact chứa:

```text
BuildId
ArtifactHash
```

để symbolication đúng binary.

---

## 440.52 — Symbol server concept

Axiom tooling có thể tìm:

```text
BuildId
→ debug artifact
```

trong:

```text
local cache
project symbol store
configured symbol server
```

---

## 440.53 — No mandatory online service

Compiler/debugger hoạt động offline.

---

## 440.54 — Crash report

Axiom runtime có thể produce:

```text
CrashReport {
    build_id
    target
    signal/exception
    thread
    registers
    stack
    loaded_modules
}
```

---

## 440.55 — Privacy

Crash report không tự động gửi dữ liệu ra ngoài.

---

## 440.56 — Local crash dump

Có thể ghi:

```text
.axiom-crash
```

hoặc platform-native dump.

---

## 440.57 — Register dump

Crash report có thể chứa architectural registers.

---

## 440.58 — Stack dump

Stack memory không được dump toàn bộ mặc định nếu không cần thiết.

Có thể configurable để tránh lộ dữ liệu.

---

## 440.59 — Symbolication

Offline:

```text
address
+
BuildId
+
debug artifact
→
function/source line
```

---

## 440.60 — AI-readable crash report

JSON:

```text
{
    "build_id": "...",
    "target": "...",
    "exception": "...",
    "thread": 3,
    "frames": [...]
}
```

---

## 440.61 — AI diagnostic query

Agent có thể hỏi:

```text
crash.top_frame
crash.call_chain
crash.source_location
crash.unwind_status
```

---

## 440.62 — Compiler explanation

Compiler có thể cung cấp:

```text
why variable optimized out
why inline happened
why bounds check remains
```

ở verbose diagnostic mode.

---

## 440.63 — Debug assertions

Debug build có thể bật additional assertions.

Release không được giữ assertion nếu profile loại bỏ chúng.

---

## 440.64 — Debug-only checks

Các check có thể đánh dấu:

```text
debug_only
```

để optimizer loại ở release.

---

## 440.65 — Sanitizer debug metadata

Sanitizer instrumentation giữ source mapping.

---

## 440.66 — Address sanitizer

Nếu có:

```text
ASan-like instrumentation
```

runtime report phải map address lỗi về source.

---

## 440.67 — Undefined behavior sanitizer

Nếu enabled, report:

```text
operation
source
location
```

---

## 440.68 — Thread sanitizer

Nếu có, report race/synchronization information với source mapping.

---

## 440.69 — Optimized debugging contract

Axiom không hứa rằng mọi local variable luôn inspect được ở `-O2`.

Compiler chỉ hứa debug information trung thực.

---

## 440.70 — Debugging async

Async frame phải giữ source state:

```text
async fn foo
state=3
await site=foo.ax:42
```

---

## 440.71 — Async logical stack

Debugger có thể hiển thị:

```text
logical async frame
```

ngoài physical stack.

---

## 440.72 — Detached task

Nếu task detached, logical parent stack không tồn tại; debugger phải phản ánh điều đó.

---

## 440.73 — Thread identity

Debugger/runtime expose:

```text
thread id
thread name
```

nếu available.

---

## 440.74 — TLS debugging

TLS variable location được debug metadata mô tả theo target.

---

## 440.75 — Global variable debugging

Global:

```text
symbol
address
type
```

được emit nếu debug enabled.

---

## 440.76 — Type debug information

Debugger cần biết:

```text
struct
enum
tuple
array
primitive
```

layout và field names.

---

## 440.77 — Generic type debugging

Concrete generic instance:

```text
Vec<i32>
```

được biểu diễn với instantiated type information.

---

## 440.78 — Trait object debugging

`dyn Trait` có thể expose:

```text
data pointer
vtable
concrete type
```

nếu debug metadata available.

---

## 440.79 — Enum debugging

Debugger hiển thị:

```text
Some(value)
None
```

thay vì chỉ raw tag.

---

## 440.80 — String debugging

Debugger hiểu Axiom `String`/string view thay vì chỉ hiển thị raw pointer.

---

## 440.81 — Slice debugging

Hiển thị:

```text
ptr
length
elements[]
```

theo bounds an toàn của debugger.

---

## 440.82 — Pointer debugging

Raw pointer hiển thị:

```text
address
```

và type nếu metadata có.

Debugger không giả định pointer luôn hợp lệ.

---

## 440.83 — Unsafe pointer inspection

Debugger có thể inspect memory nhưng không biến hành vi đó thành language semantics.

---

## 440.84 — Breakpoint mapping

Breakpoint source line:

```text
file:line
```

map tới một hoặc nhiều machine addresses.

---

## 440.85 — Conditional breakpoint

Debugger xử lý expression evaluation.

Compiler cung cấp type/symbol metadata.

---

## 440.86 — Expression evaluation

Debugger có thể evaluate một subset expression.

Không yêu cầu chạy arbitrary compiler code.

---

## 440.87 — Debug evaluator

Có thể dùng semantic engine để parse/type-check debug expressions.

---

## 440.88 — Safety boundary

Debug expression không được tự động thực hiện:

```text
filesystem
network
process creation
```

---

## 440.89 — Watch expressions

Debugger lưu semantic expression và re-evaluate khi context thay đổi.

---

## 440.90 — Source stepping

Compiler phải emit đủ line table để hỗ trợ:

```text
step into
step over
step out
```

ở mức khả thi.

---

## 440.91 — Macro-free advantage

Vì Axiom không dựa mạnh vào token macros, source mapping ít phức tạp hơn nhiều.

---

## 440.92 — Comptime mapping

Code generated bằng comptime vẫn phải giữ provenance:

```text
generated item
← source generator
← invocation
```

---

## 440.93 — Generated code debug

Nếu generated code được debug, metadata có:

```text
generated_from
```

---

## 440.94 — No debug metadata leakage

Release binary không được chứa source path/debug strings nếu profile yêu cầu strip.

---

## 440.95 — Split DWARF-like model

Có thể tách debug data khỏi binary để giảm artifact size.

---

## 440.96 — Build ID matching

Debugger không được attach debug artifact chỉ dựa trên filename.

Phải kiểm tra identity/build ID.

---

## 440.97 — Symbol stripping

Strip removes:

```text
debug
private symbols
```

theo policy.

Không được remove symbol cần dynamic linking.

---

## 440.98 — Public ABI symbols

Symbols cần runtime/FFI vẫn phải tồn tại sau strip.

---

## 440.99 — Unwind after strip

Stripping debug symbols không được làm mất unwind metadata nếu runtime policy yêu cầu unwind.

---

## 440.100 — Minimal release backtrace

Ngay cả stripped release có thể hỗ trợ:

```text
function address
```

nếu symbols/build map được cung cấp bên ngoài.

---

## 440.101 — Panic handler API

Core runtime có:

```text
panic(message, location)
```

conceptually.

---

## 440.102 — Panic location

Compiler tự cung cấp:

```text
File
Line
Column
Function
```

nếu available.

---

## 440.103 — Panic payload

Panic payload không bắt buộc heap allocate.

---

## 440.104 — Panic formatting

Minimal runtime có thể chỉ emit:

```text
panic code
location
```

khi binary size tối thiểu được ưu tiên.

---

## 440.105 — No mandatory stack trace

Tiny/freestanding builds không bắt buộc stack trace.

---

## 440.106 — Full panic runtime

Std profile có thể bật:

```text
formatted message
stack trace
symbolication
```

---

## 440.107 — Runtime component pruning

Panic runtime được link theo capability:

```text
minimal
standard
unwind
debug
```

---

## 440.108 — Signal/exception mapping

Platform runtime map:

```text
SIGSEGV
SIGABRT
access violation
illegal instruction
```

thành crash report.

---

## 440.109 — Hardware fault ≠ panic

Hardware fault không được giả định là Axiom `panic`.

---

## 440.110 — User signal handling

Platform library có thể expose signal APIs.

---

## 440.111 — Unwind API

Core runtime có internal abstraction:

```text
unwind(frame)
resume(frame)
```

target-specific implementation phía dưới.

---

## 440.112 — No mandatory C++ exception runtime

Axiom exception/unwind infrastructure không phụ thuộc C++ runtime.

---

## 440.113 — No mandatory libc

Minimal native runtime không cần libc chỉ để panic/unwind nếu target implementation cung cấp primitive cần thiết.

---

## 440.114 — Debugger contract

Debugger integration phải có:

```text
symbols
types
line table
inline tree
variable locations
unwind
```

---

## 440.115 — IDE contract

LSP/IDE có thể yêu cầu compiler expose:

```text
debug symbol path
build id
artifact path
target
```

---

## 440.116 — Debug CLI

Các lệnh:

```text
axiom debug
axiom addr2line
axiom symbolize
axiom dump-stack
axiom inspect-object
```

---

## 440.117 — `addr2line`

Conceptual:

```text
address
→ function
→ source line
```

---

## 440.118 — Symbolize

Crash address list:

```text
addresses[]
→ symbolic frames[]
```

---

## 440.119 — Object inspection

Tool có thể:

```text
axiom objdump
axiom readelf-like
axiom nm-like
```

nhưng command naming có thể gộp thành:

```text
axiom inspect
```

để tránh CLI phình to.

---

## 440.120 — Native disassembly

Axiom có disassembler riêng hoặc target backend disassembler.

Không phụ thuộc third-party compiler.

---

## 440.121 — Source-to-machine inspection

Tool:

```text
axiom inspect --source-map
```

có thể hiển thị:

```text
source
→ MIR
→ machine instructions
```

---

## 440.122 — Compiler debugging

Compiler developers có thể dump:

```text
AST
HIR
MIR
LIR
Machine IR
Object
```

---

## 440.123 — IR-to-debug continuity

Mỗi stage giữ:

```text
DebugId
SourceSpan
```

khi có thể.

---

## 440.124 — Debug IDs

ID phải deterministic trong cùng compiler input.

---

## 440.125 — Debug metadata versioning

Debug metadata generator có:

```text
format version
compiler version
```

---

## 440.126 — Reproducible debug artifact

Cùng source/config phải tạo cùng debug artifact bytes nếu deterministic mode.

---

## 440.127 — Debug info size

Debug information không ảnh hưởng runtime memory nếu được split/stripped.

---

## 440.128 — No runtime RTTI requirement

Debug type information không phải runtime RTTI.

---

## 440.129 — Reflection distinction

Compile-time reflection:

```text
type metadata
```

khác:

```text
debug metadata
```

---

## 440.130 — Crash report reproducibility

Crash report phải lưu:

```text
build id
target
compiler
runtime version
```

để symbolication chính xác.

---

## 440.131 — Crash report schema

Versioned:

```text
AxiomCrashReport/v1
```

---

## 440.132 — AI crash analysis input

AI tooling nhận structured data thay vì phải parse terminal text.

---

## 440.133 — AI diagnostic example

```text
{
  "frame": 0,
  "function": "foo",
  "source": "src/foo.ax",
  "line": 42,
  "kind": "bounds_failure"
}
```

---

## 440.134 — No automatic external transmission

Compiler/runtime không tự upload crash report.

---

## 440.135 — Security hardening

Crash reporter phải tránh expose:

```text
secrets
environment variables
full memory
```

trừ khi explicitly requested.

---

## 440.136 — Debug/unwind separation invariant

Có thể có:

```text
unwind = yes
debug = no
```

hoặc:

```text
debug = yes
unwind = no
```

trong những target/mode phù hợp.

---

## 440.137 — Native debugger ecosystem

Mục tiêu là tương thích với debugger platform hiện có thông qua:

```text
DWARF
CodeView/PDB
Mach-O/dSYM
unwind formats
```

---

## 440.138 — No proprietary compiler dependency

Axiom tự generate metadata.

Không gọi MSVC/clang chỉ để tạo PDB/DWARF.

---

## 440.139 — Optimizer correctness

Debug metadata không được làm thay đổi optimized machine code semantics.

---

## 440.140 — Debug metadata failure

Nếu debug metadata generation lỗi:

- `debug=required` → compiler error;
- `debug=optional` → warning/fallback policy.

---

## 440.141 — Unwind metadata failure

Nếu `panic=unwind` mà unwind metadata không thể tạo:

```text
compile error
```

Không silently emit binary không unwind được.

---

## 440.142 — Minimal freestanding

Freestanding:

```text
debug=none
panic=abort
unwind=none
```

có thể tạo artifact cực nhỏ.

---

## 440.143 — Full server/native profile

Có thể:

```text
debug=line
panic=unwind
stacktrace=on
```

---

## 440.144 — Desktop development profile

Có thể:

```text
debug=full
panic=unwind
sanitizers=optional
```

---

## 440.145 — Embedded profile

Có thể:

```text
no_std
panic=abort
no_unwind
debug=optional
```

---

## 440.146 — Kernel profile

Có thể:

```text
freestanding
no allocator
no threads runtime
no unwind
custom entry
```

---

## 440.147 — Debug metadata target abstraction

Compiler API:

```text
DebugBackend {
    begin_unit()
    emit_type()
    emit_function()
    emit_line()
    emit_variable()
    emit_inline()
    finalize()
}
```

---

## 440.148 — Unwind backend abstraction

```text
UnwindBackend {
    begin_function()
    emit_frame_rule()
    emit_restore_rule()
    finalize()
}
```

---

## 440.149 — Backend output

ELF:

```text
DWARF + platform unwind
```

PE:

```text
CodeView/PDB + Windows unwind
```

Mach-O:

```text
DWARF/dSYM + platform unwind
```

---

## 440.150 — Hard invariants

1. Debug metadata không phải language semantics.
2. Release build có thể loại debug hoàn toàn.
3. Unwind và debug info độc lập.
4. `panic=abort` không yêu cầu full unwind.
5. `panic=unwind` bắt buộc unwind correctness.
6. Cleanup phải chạy khi unwind.
7. Double panic trong unwind phải abort.
8. Không unwind ngầm qua FFI.
9. Debugger phải nhận được source mapping khi debug enabled.
10. Optimized-out variable không được hiển thị giá trị giả.
11. Inline functions phải có inline call-site mapping.
12. Async state phải có source mapping.
13. Build ID phải liên kết debug artifact với binary chính xác.
14. Strip debug không được phá dynamic linking.
15. Strip debug không được phá required unwind.
16. Debug artifact phải có thể tách khỏi executable.
17. Crash report không tự động upload.
18. Crash report phải versioned.
19. AI diagnostic interface phải machine-readable.
20. Debug generation không được phụ thuộc third-party compiler.
21. DWARF/CodeView/Mach-O debug data do Axiom toolchain tạo.
22. Unwind metadata phải khớp machine prologue/epilogue.
23. Freestanding build có thể loại runtime debug/unwind.
24. Debug mode phải deterministic khi reproducibility yêu cầu.
25. Debug information phải trung thực với optimized code.
26. Compiler phải có source→IR→machine mapping.
27. Runtime panic phải configurable về message/trace/size.
28. Hardware fault không được đánh đồng với language panic.
29. Debug metadata không kéo theo runtime RTTI.
30. Debug/unwind architecture phải độc lập ISA frontend.

**BOOTSTRAP-440 hoàn tất.**

---

# BOOTSTRAP-441 — RUNTIME CONTRACT, STARTUP, PROCESS MODEL, I/O, PLATFORM ABSTRACTION & FREESTANDING EXECUTION

Đây là bước tiếp theo để hoàn thiện **ranh giới giữa Axiom compiler và operating system/runtime**.

Mục tiêu không phải tạo một runtime khổng lồ, mà tạo một runtime có thể **lắp ghép theo capability**:

```text
Axiom Program
     │
     ▼
Language/Core
     │
     ├── no runtime
     │
     ├── minimal runtime
     │
     ├── std runtime
     │
     └── platform runtime
             │
             ▼
             OS / Firmware / WASM Host
```

---

## 441.1 — Runtime không phải VM

Axiom native runtime không phải:

```text
bytecode VM
```

Program native chạy trực tiếp trên CPU.

---

## 441.2 — Runtime là capability set

Runtime được tạo từ:

```text
startup
allocator
panic
thread
async
io
filesystem
network
time
process
tls
```

---

## 441.3 — Không runtime

Một chương trình:

```text
fn entry() -> never
```

có thể chạy freestanding mà không cần Axiom runtime.

---

## 441.4 — Minimal runtime

Chỉ:

```text
startup
exit
panic/abort
```

nếu program cần.

---

## 441.5 — Standard runtime

Có:

```text
allocator
thread
io
filesystem
time
random
```

theo dependency graph.

---

## 441.6 — Runtime dependency graph

Ví dụ:

```text
String
 └── allocator

File
 └── OS

Tcp
 ├── OS
 └── allocator

Async
 ├── task
 ├── IO
 └── scheduler
```

---

## 441.7 — Capability pruning

Nếu source không dùng:

```text
network
```

network runtime không được link chỉ vì `std` tồn tại.

---

## 441.8 — Program entry

Hai entry modes:

```text
main
freestanding_entry
```

---

## 441.9 — `main`

Canonical:

```text
fn main() -> i32
```

hoặc:

```text
fn main()
```

---

## 441.10 — Main return

`i32` được map thành OS process exit code.

---

## 441.11 — Main panic

Nếu panic:

```text
panic policy
```

quyết định exit/unwind.

---

## 441.12 — Startup sequence

Typical native:

```text
OS entry
 ↓
Axiom startup
 ↓
runtime initialization
 ↓
TLS
 ↓
allocator
 ↓
global initialization
 ↓
main
 ↓
shutdown
 ↓
exit
```

---

## 441.13 — Minimal startup

Freestanding:

```text
OS/Firmware entry
 ↓
user entry
```

---

## 441.14 — Runtime initialization ordering

Runtime components có dependency DAG.

Không được dùng arbitrary initialization order.

---

## 441.15 — Global initialization

Global initialization phải explicit trong build/runtime metadata.

---

## 441.16 — Lazy initialization

Library có thể dùng:

```text
Once
```

thay vì global startup nếu phù hợp.

---

## 441.17 — Process abstraction

Standard library:

```text
Process
ExitCode
Command
Environment
```

---

## 441.18 — Environment

API đọc:

```text
environment variable
```

không expose toàn bộ environment implicit.

---

## 441.19 — Exit

```text
exit(code)
```

là terminal operation.

---

## 441.20 — Abort

```text
abort()
```

không chạy ordinary cleanup.

---

## 441.21 — Graceful exit

Normal return chạy required shutdown/finalization.

---

## 441.22 — File descriptors/handles

Platform-neutral abstraction:

```text
Handle
```

với ownership semantics.

---

## 441.23 — Owned handle

Handle là resource-owning type:

```text
drop(handle)
→ close
```

---

## 441.24 — Borrowed handle

API có thể expose:

```text
BorrowedHandle
```

không tự close.

---

## 441.25 — Raw OS handles

Có thể convert explicit:

```text
raw_handle()
from_raw_handle()
```

và unsafe khi ownership không thể chứng minh.

---

## 441.26 — File API

Canonical:

```text
File::open
File::create
File::read
File::write
File::close
```

---

## 441.27 — Buffered I/O

Buffering là library layer.

Không hidden buffering trong low-level handle.

---

## 441.28 — Standard streams

```text
stdin
stdout
stderr
```

được runtime/platform provide.

---

## 441.29 — `print`

High-level formatting library sử dụng stdout.

---

## 441.30 — Minimal output

Freestanding không bắt buộc có formatting.

---

## 441.31 — Console abstraction

```text
Console
```

là standard/platform library.

---

## 441.32 — Error streams

`stderr` độc lập `stdout`.

---

## 441.33 — Path

Path là type/library abstraction, không phải raw String alias về semantics.

---

## 441.34 — UTF-8

Axiom text APIs mặc định UTF-8.

---

## 441.35 — OS-native encoding

Windows-specific APIs có thể yêu cầu UTF-16/other representation.

Conversion explicit.

---

## 441.36 — No implicit encoding conversion

Không tự động chuyển:

```text
UTF-8 ↔ UTF-16
```

mỗi lần gọi OS.

---

## 441.37 — Time

Standard time API:

```text
Instant
Duration
SystemTime
```

---

## 441.38 — Monotonic clock

`Instant` dùng monotonic clock khi target cung cấp.

---

## 441.39 — Wall clock

`SystemTime` đại diện system wall-clock.

---

## 441.40 — Duration

Không gắn trực tiếp với wall-clock calendar semantics.

---

## 441.41 — Sleep

Thread sleep là blocking operation.

Async sleep là async operation.

Hai API tách biệt.

---

## 441.42 — Randomness

Hai loại:

```text
PseudoRandom
SecureRandom
```

---

## 441.43 — No implicit global RNG

Random generator nên được explicit để reproducibility.

---

## 441.44 — Networking

Network là standard/platform capability, không core.

---

## 441.45 — Socket ownership

Socket là resource-owning type.

---

## 441.46 — TCP

API:

```text
TcpListener
TcpStream
```

---

## 441.47 — UDP

```text
UdpSocket
```

---

## 441.48 — Async network

Async APIs không biến blocking socket thành async một cách hidden.

---

## 441.49 — Blocking mode

Blocking/nonblocking là explicit configuration.

---

## 441.50 — Filesystem

Filesystem APIs:

```text
read
write
rename
remove
metadata
directory
```

---

## 441.51 — Permissions

Platform-specific permission models được expose khi cần.

---

## 441.52 — Process spawning

`Command` tạo child process.

Resource handle ownership explicit.

---

## 441.53 — Environment inheritance

Child process environment explicit/configurable.

---

## 441.54 — Signals

Signal APIs thuộc platform library.

---

## 441.55 — Dynamic libraries

API:

```text
load_library
lookup_symbol
unload_library
```

là platform capability.

---

## 441.56 — FFI

FFI core contract:

```text
extern "c"
```

đã khóa từ 421.

---

## 441.57 — Native ABI

Runtime không tạo universal object wrapper quanh mọi function.

Direct native ABI là default.

---

## 441.58 — Allocator initialization

System allocator runtime được initialize trước các allocations cần nó.

---

## 441.59 — Custom allocator

Program có thể chọn:

```text
SystemAllocator
Arena
Pool
StackAllocator
CustomAllocator
```

---

## 441.60 — Allocator ownership

Object allocated bằng allocator A phải được deallocate theo contract của A.

---

## 441.61 — No hidden allocator switch

Compiler không silently đổi allocator nếu làm thay đổi semantics.

---

## 441.62 — OOM

Runtime policy:

```text
Result
panic
abort
custom handler
```

---

## 441.63 — Runtime panic handler

Program có thể configure panic handler.

---

## 441.64 — Panic handler restrictions

Panic handler không được tạo recursive panic loop vô hạn.

---

## 441.65 — Thread runtime

Thread abstraction:

```text
spawn
join
detach
```

---

## 441.66 — Thread startup

Thread entry có environment/frame explicit.

---

## 441.67 — Thread-local storage

TLS được platform backend implement.

---

## 441.68 — Thread cleanup

TLS destructors/resources phải tuân cleanup contract.

---

## 441.69 — Async runtime

Async executor là optional.

---

## 441.70 — Runtime executor

Có thể:

```text
single-thread executor
multi-thread executor
custom executor
```

---

## 441.71 — Async I/O driver

Platform implementation có thể dùng:

```text
epoll
kqueue
IOCP
io_uring
```

nhưng đây là implementation detail của standard/platform library.

---

## 441.72 — No universal async mechanism

Axiom language không hard-code một OS async API.

---

## 441.73 — Cancellation

Cancellation cooperative.

---

## 441.74 — Cancellation cleanup

Cancelled task vẫn phải chạy required cleanup.

---

## 441.75 — Detached tasks

Explicit API:

```text
spawn_detached()
```

---

## 441.76 — Runtime scheduler

Scheduler không được tự tạo background threads nếu API không yêu cầu.

---

## 441.77 — Hidden runtime thread prohibition

Không có:

```text
"std library secretly starts threads"
```

trừ capability explicitly documented.

---

## 441.78 — GUI runtime

GUI không thuộc runtime core.

---

## 441.79 — GPU runtime

GPU context/queue/device là ecosystem/platform capability.

---

## 441.80 — WASM runtime

WASM program phụ thuộc host imports để:

```text
I/O
time
filesystem
network
```

nếu cần.

---

## 441.81 — WASM freestanding

Pure computation WASM:

```text
WASM module
```

có thể không cần imports.

---

## 441.82 — Embedded

Embedded target có thể cung cấp:

```text
custom startup
custom allocator
custom interrupt handlers
```

---

## 441.83 — Interrupt handlers

Có thể có attribute:

```text
@interrupt
```

ở platform-specific layer.

---

## 441.84 — Interrupt ABI

Interrupt functions có ABI riêng và không phải ordinary functions.

---

## 441.85 — Kernel mode

Axiom không assume:

```text
user-space OS services
```

trong core language.

---

## 441.86 — Privileged instructions

Unsafe/platform intrinsic layer có thể expose.

---

## 441.87 — CPU feature runtime detection

Có thể query:

```text
cpu_supports(feature)
```

runtime.

---

## 441.88 — Static CPU specialization

Compiler có thể generate:

```text
baseline
AVX2
AVX512
```

variants và dispatch runtime.

---

## 441.89 — Multi-versioning

Optional library/compiler feature.

---

## 441.90 — Function dispatch

Runtime dispatch có thể chọn implementation dựa trên CPU features.

---

## 441.91 — Determinism

Runtime không được tự động thay đổi behavior theo CPU feature nếu semantic contract yêu cầu deterministic result.

---

## 441.92 — FP environment

Floating-point environment changes phải explicit/platform API.

---

## 441.93 — Locale

Core text operations không phụ thuộc hidden process-global locale.

---

## 441.94 — Environment state

APIs đọc environment explicitly.

---

## 441.95 — Global mutable runtime state

Hạn chế tối đa.

Nếu có:

```text
Mutex/Atomic/Once
```

theo concurrency semantics.

---

## 441.96 — Runtime logging

Logging là library capability.

Không có hidden logging trong normal runtime.

---

## 441.97 — Tracing

Tracing optional.

---

## 441.98 — Metrics

Metrics optional library.

---

## 441.99 — Runtime configuration

Build config:

```text
runtime = minimal
runtime = std
runtime = freestanding
```

---

## 441.100 — Component manifest

Executable có thể ghi runtime capabilities:

```text
allocator
threads
async
io
panic
unwind
```

---

## 441.101 — Runtime ABI

Runtime internal APIs phải có versioned ABI khi binary components được tách riêng.

---

## 441.102 — Static runtime

Default native release ưu tiên static component integration khi phù hợp.

---

## 441.103 — Dynamic runtime

Dynamic runtime có thể tồn tại nhưng không bắt buộc.

---

## 441.104 — Runtime binary size

Runtime size proportional to used capabilities.

---

## 441.105 — No mandatory object header

Runtime không yêu cầu universal object header.

---

## 441.106 — No mandatory GC

Runtime không có GC subsystem.

---

## 441.107 — No mandatory scheduler

Không có async scheduler nếu program không dùng async.

---

## 441.108 — No mandatory allocator

Freestanding program có thể không allocate.

---

## 441.109 — No mandatory libc

Axiom runtime có native platform adapters riêng.

---

## 441.110 — OS adapter

Platform layer:

```text
axiom.platform.windows
axiom.platform.linux
axiom.platform.macos
axiom.platform.wasm
```

conceptually.

---

## 441.111 — Platform-neutral API

Standard library gọi abstraction:

```text
PlatformFile
PlatformThread
PlatformSocket
PlatformClock
```

thay vì OS-specific code trực tiếp ở mọi nơi.

---

## 441.112 — Platform implementation

Mỗi target implement platform contract.

---

## 441.113 — Platform capability detection

Compile-time:

```text
target.os
target.arch
target.features
```

Runtime:

```text
cpu_supports
```

---

## 441.114 — Conditional compilation

Syntax:

```text
comptime if target.os == "windows" {
    ...
}
```

đã phù hợp với BOOTSTRAP-431.

---

## 441.115 — Build feature flags

Library feature:

```text
features = ["network"]
```

được resolve build-time.

---

## 441.116 — No accidental dependency

Enabling `network` không kéo GUI hoặc database.

---

## 441.117 — Standard library layering

```text
core
 ↓
alloc
 ↓
collections
 ↓
io
 ↓
os
 ↓
network/process
```

---

## 441.118 — Dependency direction

Higher layer có thể dùng lower layer.

Lower layer không import higher layer.

---

## 441.119 — Circular runtime dependencies

Không cho phép dependency cycle trong runtime capability graph.

---

## 441.120 — Runtime tests

Mỗi component có:

```text
unit tests
integration tests
target tests
failure tests
```

---

## 441.121 — Startup tests

Minimal executable test:

```text
entry
→ main
→ exit 42
```

---

## 441.122 — Allocation tests

Test:

```text
alloc
realloc
free
OOM
alignment
zero-size
```

---

## 441.123 — Thread tests

Test:

```text
spawn
join
TLS
mutex
atomic
channel
```

---

## 441.124 — Async tests

Test:

```text
pending
ready
suspend
resume
cancel
cleanup
```

---

## 441.125 — File tests

Temporary directory based tests.

---

## 441.126 — Network tests

Không yêu cầu internet thật trong unit tests.

Loopback/in-memory test adapters preferred.

---

## 441.127 — Time tests

Có injectable clock abstraction cho deterministic tests.

---

## 441.128 — Random tests

Injectable RNG cho deterministic testing.

---

## 441.129 — Process tests

Child process tests phải có timeout và cleanup.

---

## 441.130 — Runtime failure isolation

Runtime test crash không được làm mất toàn bộ test suite.

---

## 441.131 — Runtime error mapping

OS errors map thành:

```text
ErrorKind
ErrorCode
NativeCode
```

---

## 441.132 — Preserve native error

Native error code vẫn có thể được expose.

---

## 441.133 — No universal error enum explosion

Không nhét mọi OS error vào một enum khổng lồ.

---

## 441.134 — Platform-specific extensions

Có thể expose:

```text
WindowsError
UnixError
WasmHostError
```

khi cần.

---

## 441.135 — Handle lifetime

Mọi OS resource phải có explicit ownership semantics.

---

## 441.136 — Close-on-drop

Resource-owning wrappers mặc định close khi drop.

---

## 441.137 — Double-close

Wrapper ownership phải ngăn double-close trong safe API.

Raw handles thuộc unsafe contract.

---

## 441.138 — Blocking annotation

API có thể có:

```text
@blocking
@no_block
```

effect metadata.

---

## 441.139 — Allocation annotation

API có thể:

```text
@allocates
@no_alloc
```

---

## 441.140 — Panic annotation

```text
@no_panic
```

là contract có thể được compiler verify ở mức khả thi.

---

## 441.141 — Runtime effect summaries

Compiler có thể query:

```text
may_allocate
may_block
may_panic
does_io
spawns_thread
```

---

## 441.142 — AI tooling

AI agent có thể hỏi:

```text
"what runtime capabilities does this program require?"
```

và compiler trả:

```text
allocator
filesystem
threads
```

---

## 441.143 — Artifact capability manifest

Final executable có thể có:

```text
runtime_manifest
```

để tooling inspect.

---

## 441.144 — Freestanding contract

Freestanding program được phép:

```text
no_std
no_alloc
no_runtime
custom_entry
```

---

## 441.145 — Bare-metal memory

Memory map do target platform define.

---

## 441.146 — Custom linker layout

Embedded users có thể cung cấp linker/layout configuration ở build layer.

---

## 441.147 — Device memory

MMIO:

```text
volatile load/store
```

và address types phù hợp.

---

## 441.148 — MMIO ordering

Compiler không được reorder volatile accesses phá hardware semantics.

---

## 441.149 — Interrupt synchronization

Atomics/volatile/critical-section APIs thuộc platform layer.

---

## 441.150 — Runtime contract summary

```text
Language
 ↓
Core
 ↓
Optional Alloc
 ↓
Optional Runtime
 ↓
Platform Adapter
 ↓
OS/Firmware/Host
```

---

## 441.151 — Hard invariants

1. Native Axiom không phải VM.
2. Runtime là capability set.
3. Runtime không bắt buộc.
4. GC không bắt buộc và không nằm trong core runtime.
5. Allocator không bắt buộc.
6. Thread runtime không bắt buộc.
7. Async executor không bắt buộc.
8. libc không phải compiler dependency.
9. Third-party compiler không phải runtime dependency.
10. `main` và freestanding entry tách biệt.
11. `main() -> i32` map rõ tới process exit code.
12. Resource ownership deterministic.
13. Owned handle drop phải release resource.
14. Borrowed handle không tự release.
15. Raw handle ownership là explicit/unsafe.
16. UTF-8 là default text representation.
17. OS-specific encoding conversion explicit.
18. Blocking và async API tách biệt.
19. Hidden runtime threads bị cấm.
20. Hidden allocations bị hạn chế và phải có effect contract.
21. Runtime capabilities phải được prune.
22. Standard library không kéo toàn bộ runtime.
23. Freestanding build không cần std runtime.
24. WASM host dependencies là explicit imports.
25. Embedded có custom startup.
26. Kernel/freestanding không assume OS services.
27. OOM policy configurable.
28. Panic policy configurable.
29. Unwind optional.
30. Runtime effects machine-readable.
31. Runtime dependency graph deterministic.
32. Platform layer tách khỏi language core.
33. OS errors giữ native information khi cần.
34. Test runtime phải deterministic.
35. Time/RNG có injectable implementations cho tests.
36. Network tests không phụ thuộc internet thật.
37. MMIO dùng volatile semantics.
38. Global mutable runtime state phải synchronization-safe.
39. Runtime binary size tỷ lệ với capabilities được dùng.
40. Axiom có thể tạo executable từ **zero-runtime freestanding** tới **full standard runtime** mà không thay đổi language core.

**BOOTSTRAP-441 hoàn tất.**