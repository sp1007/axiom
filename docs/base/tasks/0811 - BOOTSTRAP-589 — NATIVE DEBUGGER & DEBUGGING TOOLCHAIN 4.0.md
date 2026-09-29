# BOOTSTRAP-589 — NATIVE DEBUGGER & DEBUGGING TOOLCHAIN 4.0
## BREAKPOINTS, WATCHPOINTS, REGISTER/STACK INSPECTION, DWARF/CODEVIEW, SOURCE MAPS, SYMBOLS, UNWINDING, REMOTE DEBUGGING, CRASH DUMPS & AXIOM-AWARE DEBUG SEMANTICS

**Trạng thái: COMPLETED / LOCKED**

Mục tiêu của `589` là biến debug thành một phần native của Axiom toolchain, thay vì phụ thuộc vào việc compiler chỉ xuất symbol rồi giao toàn bộ công việc cho debugger bên ngoài.

Kiến trúc:

```text
                         Axiom Source
                              │
                              ▼
                    Semantic / Debug Metadata
                              │
              ┌───────────────┼────────────────┐
              ▼               ▼                ▼
          DWARF/ELF       CodeView/PE      Mach-O/DWARF
              │               │                │
              └───────────────┼────────────────┘
                              ▼
                     Axiom Debug Engine
                              │
       ┌──────────────┬───────┼────────┬──────────────┐
       ▼              ▼       ▼        ▼              ▼
  Breakpoints     Registers Memory   Stack         Threads
       │              │       │        │              │
       └──────────────┴───────┼────────┴──────────────┘
                              ▼
                     Source / Type System
                              │
                              ▼
                       Axiom Debugger
```

---

## 589.1. Debugger architecture

Debugger gồm các lớp:

```text
Debug CLI/UI
    ↓
Debug Session
    ↓
Debug Target
    ↓
Process / Remote Target
    ↓
Platform Debug Adapter
    ↓
Native Process
```

---

## 589.2. Debug session

Một session đại diện cho một phiên debug:

```text
DebugSession {
    target
    process
    threads
    modules
    breakpoints
    watches
    frames
    debug_symbols
}
```

---

## 589.3. Debug target

Target có thể là:

```text
local executable
remote process
core dump
crash dump
post-mortem image
```

---

## 589.4. Local debugging

Local debugger phải hỗ trợ:

```text
launch
attach
detach
terminate
continue
pause
step
```

---

## 589.5. Remote debugging

Kiến trúc phải tách:

```text
Debugger Host
      │
      │ Debug Protocol
      ▼
Remote Debug Agent
      │
      ▼
Target Process
```

---

## 589.6. Debug adapter

Platform-specific implementation nằm trong adapter:

```text
WindowsDebugAdapter
LinuxDebugAdapter
MacOSDebugAdapter
AndroidDebugAdapter
WasmDebugAdapter
```

---

## 589.7. Debugger không phụ thuộc compiler

Debugger có thể debug binary được tạo bởi compiler khác nếu binary cung cấp format được hỗ trợ.

---

## 589.8. Axiom-aware mode

Khi binary có Axiom semantic metadata, debugger được phép hiển thị semantic-level information.

---

## 589.9. Debug information pipeline

Compiler:

```text
Source
 ↓
AST/HIR
 ↓
MIR
 ↓
Optimized MIR
 ↓
Machine IR
 ↓
Machine Code
```

đồng thời sinh:

```text
Debug Semantic Graph
```

---

## 589.10. Debug semantic graph

```text
DebugGraph {
    source_files
    scopes
    symbols
    types
    variables
    expressions
    locations
    inline_regions
    async_regions
}
```

---

## 589.11. Source identity

Source file được định danh bằng:

```text
path
content_hash
encoding
line_map
```

---

## 589.12. Source hash

Debug metadata phải lưu source content hash để phát hiện source/binary mismatch.

---

## 589.13. Source path normalization

Absolute host paths không được bắt buộc xuất hiện trong reproducible artifact.

---

## 589.14. Source remapping

Build có thể dùng:

```text
source_remap {
    "/build/workspace/" -> "$PROJECT/"
}
```

---

## 589.15. Source map

Mỗi machine-code range có thể map về:

```text
file
line
column
AST node
semantic entity
```

---

## 589.16. Location model

```text
DebugLocation {
    address_range
    source_location
    inline_stack
    discriminator
}
```

---

## 589.17. Statement boundaries

Compiler phải đánh dấu statement boundaries nếu debug mode yêu cầu.

---

## 589.18. Expression locations

Expression có thể có location độc lập với enclosing statement.

---

## 589.19. Optimized code

Debugger phải nhận biết variable có thể:

```text
live
optimized_out
constant
split
register_resident
memory_resident
```

---

## 589.20. No fake values

Debugger không được hiển thị giá trị không còn tồn tại như thể nó chính xác.

---

## 589.21. Optimized-out state

Canonical:

```text
<optimized out>
```

---

## 589.22. Debug levels

Axiom hỗ trợ:

```text
debug = none
debug = line
debug = full
debug = full+semantic
```

---

## 589.23. Debug metadata separation

Debug data có thể nằm:

```text
inside executable
sidecar file
debug package
remote symbol server
```

---

## 589.24. Stripping

Release binary có thể strip debug sections mà không thay đổi executable semantics.

---

## 589.25. Debug package

Canonical:

```text
program.axdbg
```

là debug artifact độc lập.

Tên extension có thể thay đổi, nhưng format identity phải canonical.

---

# 589.26. Symbol model

Debugger phải hiểu:

```text
functions
globals
statics
types
modules
imports
exports
```

---

## 589.27. Symbol identity

Symbol có:

```text
name
qualified_name
linkage
address
size
module
visibility
```

---

## 589.28. Mangled symbols

Debugger phải decode Axiom mangling từ ABI `421`.

---

## 589.29. Demangling

Ví dụ:

```text
_ZN4math3Vec3...
```

được hiển thị dưới semantic name tương ứng.

---

## 589.30. Generic symbols

Debugger phải có khả năng hiển thị:

```text
Vector<Int32>
Vector<Float64>
```

thay vì chỉ machine-mangled name.

---

## 589.31. Trait symbols

Trait implementation phải được map tới:

```text
Trait
Type
Implementation
Method
```

---

## 589.32. Function identity

Debugger function identity gồm:

```text
module
qualified_name
generic_arguments
specialization
source_range
machine_range
```

---

## 589.33. Inline function

Nếu function được inline, debugger phải giữ inline call stack.

---

## 589.34. Inline frame

Ví dụ:

```text
main()
 └── compute()
      └── Vec.length()
```

dù machine code chỉ tồn tại trong một function body.

---

## 589.35. Breakpoint architecture

Breakpoint có các loại:

```text
source
function
address
conditional
data
exception
instruction
```

---

## 589.36. Source breakpoint

```text
break main.ax:42
```

được resolve qua source map.

---

## 589.37. Function breakpoint

```text
break Vec.length
```

---

## 589.38. Qualified breakpoint

```text
break math::Vec3::normalize
```

---

## 589.39. Generic breakpoint

Có thể đặt breakpoint trên:

```text
Vector<T>::push
```

hoặc specialization cụ thể.

---

## 589.40. Conditional breakpoint

```text
break main.ax:42 if x > 100
```

Expression được evaluate trong debug context.

---

## 589.41. Breakpoint condition safety

Condition không được tự ý thực hiện side effect nếu không explicit.

---

## 589.42. Breakpoint hit count

Hỗ trợ:

```text
ignore N
break after N hits
break every N hits
```

---

## 589.43. Temporary breakpoint

Debugger có:

```text
break-once
```

---

## 589.44. Hardware breakpoint

Platform adapter có thể sử dụng hardware breakpoint registers.

---

## 589.45. Software breakpoint

Fallback bằng instruction trap khi platform cho phép.

---

## 589.46. Breakpoint relocation

Breakpoint phải được re-resolve khi shared library/module load.

---

## 589.47. Pending breakpoint

Breakpoint có thể tồn tại trước khi module được load.

---

## 589.48. Breakpoint identity

Mỗi breakpoint có stable ID:

```text
B1
B2
...
```

---

# 589.49. Watchpoint

Hỗ trợ theo dõi memory:

```text
watch x
watch *ptr
watch buffer[0]
```

---

## 589.50. Read watchpoint

Nếu hardware target hỗ trợ:

```text
watch-read
```

---

## 589.51. Write watchpoint

```text
watch-write
```

---

## 589.52. Access watchpoint

```text
watch-access
```

---

## 589.53. Software watch fallback

Nếu hardware watchpoint không đủ, debugger có thể dùng controlled single-step/instrumentation trong debug mode.

---

## 589.54. Register model

Debugger phải expose target registers:

```text
general
floating-point
vector
flags
control
special
```

---

## 589.55. Register aliases

x86:

```text
RAX
EAX
AX
AL
```

phải được biểu diễn như cùng register family.

---

## 589.56. AArch64 registers

Hỗ trợ:

```text
X0..X30
W0..W30
SP
PC
NZCV
SIMD/FP
```

---

## 589.57. Vector registers

Debugger phải hiển thị:

```text
XMM
YMM
ZMM
NEON/SIMD
```

theo target.

---

## 589.58. Register formatting

Cho phép:

```text
hex
decimal
signed
unsigned
float
vector
```

---

# 589.59. Memory inspection

Debugger hỗ trợ:

```text
read
write
dump
search
```

---

## 589.60. Memory safety

Memory read/write phải kiểm tra target process permissions.

---

## 589.61. Invalid memory

Không được crash debugger khi target address invalid.

---

## 589.62. Memory display

Hỗ trợ:

```text
hex
bytes
u8/u16/u32/u64
i8/i16/i32/i64
f32/f64
UTF-8
```

---

## 589.63. Pointer display

Pointer được hiển thị:

```text
address
target type
dereference state
```

---

## 589.64. Fat pointer display

Axiom fat pointer có thể hiển thị:

```text
data
metadata
```

---

## 589.65. Slice display

Ví dụ:

```text
slice<u8> {
    ptr = ...
    len = 128
}
```

---

## 589.66. String display

UTF-8 string phải được hiển thị dưới dạng text nếu bytes hợp lệ.

---

## 589.67. Invalid UTF-8

Fallback về byte representation.

---

# 589.68. Type display

Debugger phải sử dụng type metadata.

Ví dụ:

```text
Vec3 {
    x: 1.0
    y: 2.0
    z: 3.0
}
```

---

## 589.69. Struct layout

Debugger phải biết:

```text
field offset
field size
alignment
type
```

---

## 589.70. Enum display

Hiển thị:

```text
Some(value)
None
```

thay vì raw discriminant khi metadata tồn tại.

---

## 589.71. Tagged union

Debugger phải decode active variant.

---

## 589.72. Generic type display

Type arguments phải được giữ nếu có thể.

---

## 589.73. Trait object display

Hiển thị:

```text
dyn Drawable {
    concrete_type = Circle
    data = ...
    vtable = ...
}
```

---

## 589.74. Vtable inspection

Có thể inspect:

```text
type
method slots
drop function
metadata
```

---

## 589.75. Closure display

Closure:

```text
closure {
    captured: [...]
}
```

---

## 589.76. Closure environment

Debugger phải map capture fields về source variable names.

---

# 589.77. Stack model

Debugger phải hỗ trợ:

```text
call stack
frame
locals
arguments
return address
```

---

## 589.78. Stack frame

```text
Frame {
    function
    pc
    sp
    fp
    module
    source_location
}
```

---

## 589.79. Frame unwinding

Unwinder sử dụng:

```text
DWARF CFI
Windows unwind metadata
AArch64 unwind
platform metadata
```

---

## 589.80. Unwind fallback

Nếu debug info thiếu, debugger có thể sử dụng frame-pointer chain nếu tồn tại.

---

## 589.81. Corrupt stack

Debugger phải phát hiện unwind failure thay vì suy đoán frame tiếp theo.

---

## 589.82. Async stack

Async task có thể không có native stack liên tục.

Debugger phải reconstruct logical async stack từ metadata.

---

## 589.83. Async frame

```text
AsyncFrame {
    state
    suspended_at
    locals
    parent_task
}
```

---

## 589.84. Await boundary

Debugger phải hiển thị:

```text
await <operation>
```

thay vì chỉ machine state.

---

# 589.85. Thread model

Debugger hỗ trợ:

```text
list threads
select thread
pause thread
resume thread
```

---

## 589.86. Thread metadata

Thread có:

```text
OS id
Axiom task id
name
state
```

---

## 589.87. Task debugging

Axiom async/task runtime phải expose optional debug metadata.

---

## 589.88. Deadlock debugging

Debugger có thể hiển thị:

```text
thread
waiting-on
owner
lock
```

nếu runtime metadata tồn tại.

---

## 589.89. Channel debugging

Channel metadata có thể expose:

```text
capacity
queued items
sender count
receiver count
```

chỉ trong debug mode.

---

# 589.90. Exception/panic debugging

Debugger phải bắt được:

```text
panic
abort
exception
unhandled failure
```

---

## 589.91. Panic payload

Nếu panic chứa structured payload:

```text
message
type
source location
stack
```

phải hiển thị.

---

## 589.92. Result failure

Debugger có thể stop khi `Result` failure được propagated nếu configured.

---

## 589.93. Throw breakpoint

Nếu exception model được bật:

```text
break-on-throw
break-on-catch
```

---

## 589.94. Error propagation

Debugger phải reconstruct `try` propagation chain nếu semantic metadata tồn tại.

---

# 589.95. Crash dump

Axiom phải hỗ trợ tạo crash artifact:

```text
CrashDump {
    executable_id
    module_list
    threads
    registers
    stacks
    exception
    memory_regions
    debug_identity
}
```

---

## 589.96. Minimal crash dump

Production có thể dùng dump nhẹ:

```text
exception
thread
registers
stack
modules
```

---

## 589.97. Full crash dump

Debug environment có thể capture memory regions.

---

## 589.98. Crash dump reproducibility

Crash dump phải record:

```text
binary hash
debug artifact hash
runtime version
target
```

---

## 589.99. Post-mortem debugging

Debugger phải mở crash dump mà không cần process đang chạy.

---

# 589.100. Symbol server

Axiom debug infrastructure có thể dùng symbol store:

```text
symbols/
  <build-id>/
     program.axdbg
```

---

## 589.101. Build ID

Mỗi executable phải có stable debug/build identity.

---

## 589.102. Symbol lookup

Lookup:

```text
build_id
module_id
debug_hash
```

---

## 589.103. Offline symbols

Local symbol cache phải được ưu tiên khi offline.

---

# 589.104. DWARF

ELF/Linux và các target dùng DWARF phải emit canonical DWARF mapping.

---

## 589.105. CodeView

PE/Windows target có thể emit CodeView/PDB-compatible information.

---

## 589.106. Mach-O debug

Mach-O dùng DWARF hoặc platform-compatible debug representation.

---

## 589.107. WASM debug

WASM debug metadata phải map instruction offsets về Axiom source.

---

## 589.108. Debug format abstraction

Compiler không được hardcode logic debugger vào từng object writer.

```text
Semantic Debug Model
        ↓
DWARF Writer
CodeView Writer
WASM Debug Writer
```

---

# 589.109. Debug information preservation

Optimization passes phải preserve debug mapping contract.

---

## 589.110. Debug location propagation

Mỗi transformation có thể:

```text
preserve
merge
split
invalidate
```

debug locations.

---

## 589.111. Debug-aware optimization

Debug mode không được mặc định tắt mọi optimization.

---

## 589.112. Debug optimization profiles

Có:

```text
debug-fast
debug-balanced
debug-accurate
```

---

## 589.113. Variable lifetime

Compiler phải record semantic lifetime nếu khả thi.

---

## 589.114. Variable location list

Variable có thể chuyển:

```text
RAX
 ↓
stack[32]
 ↓
R12
```

Debugger phải theo location ranges.

---

## 589.115. Constant variable

Constant có thể được materialize mà không có memory address.

---

## 589.116. Synthetic variables

Debugger có thể tạo:

```text
$pc
$sp
$thread
$task
```

---

# 589.117. Debug expression evaluator

Debugger cần expression engine riêng.

```text
Source Expression
       ↓
Debug Parser
       ↓
Type Resolver
       ↓
Debug Evaluator
```

---

## 589.118. Expression safety

Mặc định evaluator không thực hiện side effect.

---

## 589.119. Function calls

Gọi function từ debugger phải explicit và được đánh dấu unsafe/side-effecting.

---

## 589.120. Memory reads

Expression evaluator được phép đọc target memory theo policy.

---

## 589.121. Type casts

Debugger cho phép explicit cast khi layout hợp lệ.

---

## 589.122. Pointer dereference

Debugger phải cảnh báo khi dereference invalid/unmapped memory.

---

# 589.123. Conditional expression VM

Condition phức tạp có thể compile sang debug expression bytecode.

---

## 589.124. Debug expression determinism

Pure expressions phải deterministic.

---

## 589.125. Optimized variable reconstruction

Debugger có thể reconstruct logical value từ nhiều machine locations.

---

## 589.126. Location recipe

```text
LocationRecipe {
    register
    memory
    constant
    composite
    piece[]
}
```

---

# 589.127. Source stepping

Hỗ trợ:

```text
step-in
step-over
step-out
next
finish
continue
```

---

## 589.128. Step-in

Đi vào function call nếu source mapping tồn tại.

---

## 589.129. Step-over

Không đi vào callee trừ khi callee tạo trap/breakpoint.

---

## 589.130. Step-out

Tiếp tục tới caller frame.

---

## 589.131. Instruction stepping

Có:

```text
step-instruction
next-instruction
```

---

## 589.132. Reverse debugging

Không bắt buộc trong core.

Có thể hỗ trợ sau thông qua execution recording.

---

# 589.133. Debug recording boundary

Kiến trúc phải để dành:

```text
record
checkpoint
replay
reverse-step
```

nhưng không đưa vào mandatory runtime.

---

# 589.134. Source-level watch

Debugger có thể theo dõi:

```text
x
obj.field
array[i]
```

---

## 589.135. Collection visualization

Debugger có thể có visualizer cho:

```text
Array
Slice
Map
Set
String
Vector
Tensor
```

---

## 589.136. Custom type visualizer

Axiom metadata có thể khai báo debug formatter:

```text
#[debug_view]
```

---

## 589.137. Debug metadata security

Production binary không được chứa secret source data ngoài phần explicitly requested.

---

## 589.138. Sensitive debug stripping

Debug artifact phải có khả năng strip:

```text
absolute paths
source content
private metadata
```

---

# 589.139. Remote debug protocol

Protocol tối thiểu:

```text
attach
detach
pause
resume
read_memory
write_memory
read_registers
write_registers
threads
modules
breakpoints
watchpoints
stack
symbols
```

---

## 589.140. Protocol transport

Có thể chạy trên:

```text
local IPC
TCP
USB
ADB
SSH tunnel
```

---

## 589.141. Authentication

Remote debugger phải authenticate nếu transport không trusted.

---

## 589.142. Capability negotiation

Client/server negotiate:

```text
breakpoints
watchpoints
registers
memory
hardware features
```

---

## 589.143. Version negotiation

Protocol version độc lập với compiler language version.

---

# 589.144. Android debugging

Android target có thể dùng debug agent/ADB transport.

Axiom debugger không cần Android compiler.

---

## 589.145. iOS debugging boundary

iOS debugging phải tách platform-required debug/signing mechanisms khỏi Axiom semantic layer.

---

# 589.146. WASM debugger

WASM debugger phải map:

```text
wasm function
instruction offset
local
stack
memory
```

về Axiom source.

---

# 589.147. Multi-process debugging

Debugger có thể quản lý:

```text
parent
child
worker
helper
```

processes.

---

## 589.148. Dynamic modules

Debugger phải detect:

```text
DLL
SO
DYLIB
framework
plugin
```

load/unload.

---

## 589.149. Module identity

Mỗi module:

```text
path
build_id
load_address
size
debug_id
```

---

## 589.150. ASLR

Debugger phải tính load bias khi ASLR được bật.

---

## 589.151. PIE

PIE executables phải được debug như relocatable main image.

---

## 589.152. TLS

Debugger phải hiểu thread-local variables.

---

## 589.153. TLS lookup

TLS variable phải resolve theo selected thread.

---

## 589.154. Static/global variables

Debugger phải distinguish:

```text
global
module-static
function-static
thread-local
```

---

# 589.155. Debugging ownership

Với Axiom ownership model:

```text
owner
moved
dropped
borrowed
```

có thể xuất hiện trong semantic metadata.

---

## 589.156. Moved variable

Sau move:

```text
x = <moved>
```

nếu compiler biết chính xác.

---

## 589.157. Dropped resource

Debugger có thể hiển thị:

```text
resource state = dropped
```

---

## 589.158. Drop breakpoint

Có thể break tại destructor/drop function.

---

## 589.159. Defer debugging

Debugger phải map `defer` cleanup về source scope.

---

## 589.160. Cleanup frames

Hidden cleanup code phải không làm stack trace trở nên khó hiểu.

---

# 589.161. Comptime debugging

Comptime execution có thể có debug diagnostics riêng.

---

## 589.162. Comptime stack

Compiler có thể expose:

```text
comptime call stack
```

khi lỗi xảy ra.

---

## 589.163. Runtime vs compile-time frame

Debugger/compiler diagnostics phải phân biệt hai execution domains.

---

# 589.164. Macro/generator debugging

Generated code phải giữ:

```text
generator source
generated source
origin mapping
```

nếu debug metadata được bật.

---

## 589.165. Source expansion map

```text
generated line
      ↓
generator
      ↓
original source
```

---

# 589.166. AI-readable debug state

Debugger phải cung cấp machine-readable snapshot:

```text
DebugSnapshot {
    process
    thread
    frame
    registers
    locals
    source
    memory
    modules
    breakpoints
}
```

---

## 589.167. AI query

Agent có thể query:

```text
why stopped?
what is x?
where was x last changed?
which lock is blocking this task?
which source line owns this instruction?
```

---

## 589.168. AI explanation graph

Debugger có thể trả:

```text
machine address
 ↓
instruction
 ↓
MIR operation
 ↓
source expression
 ↓
variable
```

---

## 589.169. No hallucinated debug state

AI tooling chỉ được sử dụng facts từ debugger snapshot.

---

# 589.170. Crash analysis

Post-mortem analyzer phải tự động:

```text
load dump
 ↓
resolve modules
 ↓
resolve symbols
 ↓
unwind
 ↓
map source
 ↓
classify exception
```

---

## 589.171. Crash report

Canonical report:

```text
CrashReport {
    target
    build
    exception
    thread
    stack
    registers
    modules
    source_location
}
```

---

## 589.172. Crash fingerprint

Crash fingerprint dựa trên:

```text
exception class
module
function
instruction region
stack signature
```

---

## 589.173. Crash deduplication

Hai crash có cùng semantic fingerprint có thể được nhóm.

---

# 589.174. Debugger CLI

CLI tối thiểu:

```text
axiom debug program.ax
```

Commands:

```text
run
continue
next
step
finish
break
watch
stack
frame
locals
print
memory
registers
threads
modules
disassemble
source
quit
```

---

## 589.175. Break command

```text
break main.ax:42
break foo
break foo if x == 10
```

---

## 589.176. Print command

```text
print x
print obj.field
print arr[3]
```

---

## 589.177. Stack command

```text
stack
stack 20
frame 3
```

---

## 589.178. Register command

```text
registers
register rax
```

---

## 589.179. Memory command

```text
memory 0x1000 128
```

---

## 589.180. Disassembly

```text
disassemble foo
disassemble 0x401000
```

---

## 589.181. Source command

```text
source main.ax:42
```

---

# 589.182. Debug API

Public API:

```text
DebugSession
DebugTarget
Process
Thread
Frame
Breakpoint
Watchpoint
Module
Symbol
Value
Type
MemoryRegion
```

---

## 589.183. Debugger plugin boundary

Platform-specific debugging mechanisms nằm sau:

```text
DebugPlatformAdapter
```

---

## 589.184. Windows adapter

Có trách nhiệm:

```text
process attach
thread control
registers
memory
breakpoints
PE modules
unwind
CodeView/PDB
```

---

## 589.185. Linux adapter

Có trách nhiệm tương ứng cho:

```text
ELF
DWARF
ptrace-like process control
signals
unwind
```

---

## 589.186. macOS adapter

Tương ứng:

```text
Mach-O
DWARF
process/task control
threads
exceptions
```

---

## 589.187. WASM adapter

Debugger có runtime-specific process model.

---

# 589.188. Debugger performance

Debugger không được làm compiler binary chậm ở release mode nếu debug metadata disabled.

---

## 589.189. Debug metadata size

Compiler phải hỗ trợ split debug để executable vẫn nhỏ.

---

## 589.190. Debug info compression

Debug package có thể nén độc lập.

---

## 589.191. Deterministic debug output

Debug metadata phải deterministic khi reproducible build enabled.

---

## 589.192. Debug info hash

Debug artifact có canonical hash.

---

## 589.193. Binary/debug association

Executable chứa debug ID để locate sidecar.

---

## 589.194. Source mismatch

Nếu source hash khác binary:

```text
WARNING:
source does not match debug artifact
```

không được âm thầm dùng source sai.

---

## 589.195. Module mismatch

Nếu module build ID khác symbol package:

```text
symbol mismatch
```

---

# 589.196. Debugger correctness

Debugger phải distinguish:

```text
known
unknown
optimized-out
unavailable
invalid
```

---

## 589.197. Register correctness

Register state phải đọc trực tiếp từ target adapter.

---

## 589.198. Memory correctness

Memory display phải reflect actual target memory tại thời điểm stop.

---

## 589.199. Stack correctness

Stack frame chỉ được hiển thị khi unwind có confidence hợp lệ.

---

## 589.200. Debugger verification

Test suite phải gồm:

```text
breakpoint tests
step tests
symbol tests
DWARF tests
CodeView tests
unwind tests
optimized variable tests
async tests
crash dump tests
remote tests
```

---

# 589.201. FINAL DEBUGGER CONTRACT

Một Axiom debugger hoàn chỉnh phải có khả năng:

```text
source
  ↓
semantic symbol
  ↓
machine address
  ↓
native process
  ↓
register/memory/stack
  ↓
semantic value
  ↓
source-level explanation
```

---

# 589.202. FINAL HARD INVARIANTS

### Invariant 1 — source truth

> Mọi source-level state được debugger hiển thị phải có debug metadata hoặc machine-level evidence tương ứng.

### Invariant 2 — no fake values

> Optimized-out hoặc unavailable value không được hiển thị như giá trị thật.

### Invariant 3 — native correctness

> Breakpoint, register, memory và unwind phải phản ánh trạng thái native thực tế.

### Invariant 4 — target independence

> Debug semantic model độc lập với DWARF/CodeView/Mach-O/ELF/PE.

### Invariant 5 — reproducibility

> Debug artifacts có identity và hash deterministic trong reproducible mode.

### Invariant 6 — optimization compatibility

> Debugging không bắt buộc phải disable toàn bộ optimization.

### Invariant 7 — async awareness

> Async/task execution có thể được debug ở logical task level, không chỉ native stack.

### Invariant 8 — ownership awareness

> Axiom debugger có thể biểu diễn move/drop/cleanup state khi compiler cung cấp metadata.

### Invariant 9 — crash independence

> Crash dump phải có thể được phân tích mà không cần process gốc còn chạy.

### Invariant 10 — AI observability

> Debug state phải có machine-readable representation để IDE và AI agent truy vấn mà không phải suy đoán.

### Invariant 11 — no compiler dependency

> Debugger không được biến compiler thành dependency bắt buộc của debugger runtime.

### Invariant 12 — platform isolation

> Platform-specific debug mechanisms phải nằm trong debug adapter, không làm ô nhiễm semantic debug model.

---

# 589 — LOCKED

Axiom hiện đã có:

```text
Compiler
   │
   ├── Native code generation
   ├── Native linker
   ├── Native image builder
   ├── Self-hosting
   ├── Bootstrap verification
   ├── Toolchain / SDK
   └── Native debugger
```

Đây là điểm quan trọng: từ `586 → 589`, Axiom đã chuyển từ **một compiler tự build được** thành **một development toolchain có thể phân phối, cross-compile và debug native application**.

---

# NEXT — BOOTSTRAP-590

## IDE PLATFORM & SEMANTIC DEVELOPMENT ENVIRONMENT 5.0
### EDITOR, PROJECT MODEL, SEMANTIC INDEX, LSP, DEBUGGER INTEGRATION, BUILD GRAPH, REFACTORING, CODE ACTIONS, PROFILING, TESTING, VISUAL UI & AI-NATIVE DEVELOPMENT WORKSPACE

Kiến trúc tiếp theo:

```text
                         Axiom IDE
                            │
       ┌────────────────────┼────────────────────┐
       ▼                    ▼                    ▼
   Source Editor       Project Model        Toolchain
       │                    │                    │
       └──────────────┬─────┴────────────┬───────┘
                      ▼                  ▼
                Semantic Engine      Build Engine
                      │                  │
          ┌───────────┼──────────┐       │
          ▼           ▼          ▼       ▼
        LSP       Refactoring   AI    Compiler
          │           │          │       │
          └───────────┼──────────┘       ▼
                      ▼               Debugger
                Unified Workspace        │
                      │                  │
                      └────────┬─────────┘
                               ▼
                     Native Application
```

`590` sẽ hợp nhất những subsystem đã xây ở `434`, `486`, `555`, `569–570`, `589` thành một **semantic development environment thống nhất**, trong đó editor, compiler, debugger, profiler, build system và AI agent cùng sử dụng **một semantic database**, thay vì mỗi công cụ tự phân tích source một lần.