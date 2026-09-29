# BOOTSTRAP-266 — AXIOM DEBUG INFO, UNWINDING, STACK TRACE & SOURCE-TO-MACHINE PROVENANCE

**TRẠNG THÁI: FROZEN / COMPLETED**

Task này hoàn thiện một phần cực quan trọng của compiler thực tế: **debugging không được phá vỡ bởi optimization, inlining, async, closure, comptime hay nhiều backend khác nhau**.

Nguyên tắc trung tâm:

> **Debug information mô tả mối quan hệ giữa semantic program và physical machine state; nó không định nghĩa semantics của chương trình.**

Kiến trúc:

```text
Axiom Source
     │
     ▼
Syntax / HIR
     │
     ▼
MIR
     │
     ▼
Verified MIR
     │
     ▼
OptIR
     │
     ▼
ABI MIR
     │
     ▼
Axiom LIR
     │
     ▼
Machine IR / WASM IR
     │
     ▼
Machine Code
     │
     ├──────────────► DebugInfo
     │
     └──────────────► UnwindInfo
```

---

# 1. Debug không phải một annotation đơn giản

Không nên chỉ lưu:

```text
machine_address → source_line
```

vì optimization làm quan hệ phức tạp hơn.

Cần biểu diễn:

```text
Source
  ↕
Semantic
  ↕
Optimized semantic representation
  ↕
Machine representation
```

---

# 2. Debug provenance

Thêm compiler-internal:

```text
DebugProvenance
```

Mỗi semantic/codegen entity có thể giữ:

```text
DebugOrigin {
    SourceSpan
    DeclarationId
    ExpressionId
    StatementId
    InstructionId
    InlineContextId
}
```

---

# 3. SourceSpan

Đã có từ lexer:

```text
SourceFileId
byte_start
byte_end
```

Debug system sử dụng chính `SourceSpan`, không tạo một hệ tọa độ nguồn thứ hai.

---

# 4. Instruction provenance

Mỗi MIR instruction có thể có:

```text
InstructionProvenance {
    source_span
    semantic_origin
    operation_kind
}
```

---

# 5. Sau optimization

Một machine instruction có thể xuất phát từ:

```text
1 MIR instruction
```

hoặc:

```text
many MIR instructions
```

hoặc:

```text
compiler-generated instruction
```

---

# 6. Vì vậy mapping phải là nhiều-nhiều có kiểm soát

Ví dụ:

```text
source expression
      ↓
MIR A
MIR B
MIR C
      ↓
optimized
      ↓
machine instruction X
```

---

# 7. Không được giả vờ rằng mapping luôn 1:1

Đây là lỗi thường gặp khi thiết kế debug info đơn giản.

---

# 8. Debug location

Chuẩn hóa:

```text
DebugLocation {
    source_span
    discriminator
    inline_context
    instruction_region
}
```

---

# 9. Discriminator

Hai operations cùng một dòng:

```text
foo()
bar()
```

cần phân biệt được khi debugger stepping.

---

# 10. Instruction ranges

Machine code mapping:

```text
AddressRange
→ DebugLocation
```

Ví dụ:

```text
0x1000..0x1008 → line 10
0x1008..0x1010 → line 11
```

---

# 11. Một source statement có thể có nhiều ranges

Do:

```text
inlining
code motion
loop optimization
branch folding
```

---

# 12. Source location không phải execution order

Optimizer có thể reorder instructions.

Debug location chỉ mô tả:

> instruction này vẫn đại diện cho semantic source operation nào.

Không được dùng debug line để suy ra language execution semantics.

---

# 13. Debug semantics độc lập optimization

Các profile:

```text
debug
release
size
speed
```

đều phải giữ semantic correctness.

Debug metadata chỉ thay đổi observability/tooling.

---

# 14. Variable debug information

Đây là phần khó hơn line mapping.

Ví dụ:

```text
let x = a + b
```

Sau optimization `x` có thể:

```text
register
stack
constant
eliminated
split across registers
recomputed
```

---

# 15. Variable location

Cần:

```text
VariableLocation {
    Undefined
    Constant
    Register
    Stack
    Memory
    Composite
    Recomputed
}
```

---

# 16. Location ranges

Một biến có thể:

```text
0x1000..0x1010 → RAX
0x1010..0x1020 → stack[24]
0x1020..       → optimized-out
```

---

# 17. Optimized-out là trạng thái hợp lệ

Debugger không được giả mạo giá trị.

Nếu compiler đã loại bỏ `x`:

```text
x = optimized_out
```

thay vì hiển thị dữ liệu không đáng tin.

---

# 18. Constant propagation

Nếu:

```text
let x = 42
```

compiler có thể debug bằng:

```text
Constant(42)
```

mà không cần storage.

---

# 19. Scalar replacement

Nếu:

```text
struct Point {
    x
    y
}
```

được scalarize thành:

```text
r1 = x
r2 = y
```

debugger vẫn phải có thể hiển thị semantic:

```text
Point { x, y }
```

nếu debug level yêu cầu và thông tin còn đủ.

---

# 20. Composite location

Có thể:

```text
Point.x → register
Point.y → stack
```

Debug metadata phải hỗ trợ composite values.

---

# 21. Ownership debug state

Axiom đặc biệt ở đây.

Compiler có semantic state:

```text
Owned
Moved
PartiallyMoved
Dropped
```

Debug tooling có thể expose:

```text
ownership state
```

nhưng đây là **tooling metadata**, không phải runtime semantics.

---

# 22. Ví dụ

```text
let a = resource
let b = a
```

Tại breakpoint sau dòng thứ hai:

```text
a → Moved
b → Owned
```

IDE có thể giải thích trực tiếp.

---

# 23. Capability debug state

Tương tự:

```text
view<T>
mut_view<T>
```

debugger/IDE có thể hiển thị:

```text
READ capability
WRITE capability
provenance
region
```

nếu semantic snapshot/debug mode hỗ trợ.

---

# 24. Nhưng không phải runtime overhead bắt buộc

Release binary không cần mang ownership metadata.

---

# 25. Type debug information

Debugger cần biết:

```text
TypeId
```

→ physical representation.

Ví dụ:

```text
Axiom:
struct Point {
    x: f32
    y: f32
}
```

có thể map thành debugger type:

```text
Point {
    x: float
    y: float
}
```

---

# 26. Layout mapping

Nếu layout compiler-controlled:

```text
semantic field x
→ physical offset/register
```

phải được mô tả.

---

# 27. Field reorder

Compiler có thể reorder fields trong internal ABI nếu source không yêu cầu stable layout.

Debug info phải dùng actual layout.

---

# 28. `@repr(C)`

Với:

```text
@repr(C)
struct Point { ... }
```

debug information phải phản ánh C-compatible layout.

---

# 29. Enum debugging

Debugger cần hiển thị:

```text
Option<T>
```

như:

```text
None
```

hoặc:

```text
Some(value)
```

thay vì chỉ raw discriminant.

---

# 30. Niche optimization

Nếu `Option<Box<T>>` được niche-optimized, debugger vẫn phải decode semantic variant.

---

# 31. Debug info không được giả định enum có discriminant riêng.

---

# 32. Generic types

Ví dụ:

```text
Vec<i32>
Vec<f64>
```

có thể là hai monomorphized instances.

Debug info cần:

```text
GenericInstanceId
```

để reconstruct:

```text
Vec<i32>
```

---

# 33. Code sharing

Nếu compiler dùng generic code sharing, nhiều source instances có thể trỏ tới cùng machine implementation.

Debug metadata phải hỗ trợ multiple logical origins.

---

# 34. Inlining

Đây là phần quan trọng nhất.

Ví dụ:

```text
fn add(x: i32, y: i32) -> i32 {
    x + y
}

fn main() {
    let z = add(1, 2)
}
```

optimizer inline `add`.

Machine code không còn call.

Debugger vẫn phải hiển thị:

```text
main
  └── add
```

---

# 35. InlineContext

Chuẩn hóa:

```text
InlineContext {
    function
    call_site
    parent
}
```

---

# 36. Inline tree

```text
main
 └── foo
      └── bar
           └── baz
```

Debugger có thể reconstruct inline call stack.

---

# 37. Machine address

Một instruction:

```text
0x1234
```

có thể thuộc:

```text
baz
inline in bar
inline in foo
called by main
```

---

# 38. Không được dùng physical stack frame để biểu diễn inline stack

Inline function có thể không có frame.

---

# 39. Stack trace

Axiom stack trace gồm:

```text
PhysicalFrame
+
InlineFrames
```

---

# 40. Physical frame

Unwinding lấy:

```text
PC
SP
FP nếu có
registers
unwind metadata
```

---

# 41. Inline frame

Reconstructed từ debug metadata.

---

# 42. Vì vậy stack trace có thể:

```text
main
foo
bar
baz
```

dù machine stack chỉ có:

```text
main
```

---

# 43. Unwinding

Compiler phải hỗ trợ:

```text
UnwindInfo
```

riêng với:

```text
DebugInfo
```

---

# 44. Debug info ≠ unwind info

Debug:

```text
"Instruction này tương ứng source nào?"
```

Unwind:

```text
"Làm sao khôi phục caller state?"
```

---

# 45. Native unwind

Target-specific:

```text
Windows → unwind/PDATA/XDATA
ELF     → DWARF CFI / platform unwind
Mach-O  → unwind information
```

---

# 46. WASM unwind

WASM không có native stack unwinding model giống CPU.

Axiom runtime/profile có thể dùng:

```text
explicit stack metadata
```

hoặc host/runtime mechanism.

---

# 47. Không đưa native unwind semantics vào Core.

---

# 48. Frame state

Compiler phải biết tại mỗi machine range:

```text
CFA
saved registers
stack offsets
```

---

# 49. CFA

Conceptual:

```text
Canonical Frame Address
```

là basis để debugger/unwinder tìm caller state.

---

# 50. Frame pointer omission

Axiom không bắt buộc:

```text
frame pointer
```

---

# 51. Debug không được yêu cầu frame pointer

Nếu compiler muốn tối ưu:

```text
-fomit-frame-pointer
```

thì unwind metadata phải bù lại.

---

# 52. Leaf function

Có thể không tạo stack frame.

Unwinder vẫn phải xử lý đúng.

---

# 53. Tail call

Tail call có thể loại bỏ physical frame.

Stack trace cần biểu diễn semantics phù hợp với platform/debug contract.

---

# 54. Async debugging

Đây là phần đặc biệt quan trọng với Axiom.

Source:

```text
async fn fetch() {
    let a = ...
    await ...
    let b = ...
}
```

Compiler biến thành Future state machine.

---

# 55. Debugger không nên chỉ thấy state machine

Thay vào đó có:

```text
AsyncDebugInfo
```

map:

```text
FutureState
SuspensionPointId
→ source location
→ source locals
```

---

# 56. Suspension point

Ví dụ:

```text
await #0
await #1
```

---

# 57. Khi paused

Debugger có thể hiển thị:

```text
fetch()
  state: suspended at await #1
  a: ...
  b: unavailable
```

---

# 58. State fields

Chỉ values sống qua await mới trở thành Future state fields.

Debug metadata phải map:

```text
source local
→ state field
```

---

# 59. State field optimization

Compiler có thể eliminate state fields.

Debugger phải đánh dấu:

```text
optimized out
```

nếu không còn value.

---

# 60. Closure debugging

Closure:

```text
|x| x + offset
```

có compiler-generated environment.

Debugger cần hiển thị:

```text
closure
  captured offset = ...
```

thay vì bắt programmer hiểu internal environment struct.

---

# 61. Closure environment layout

Không stable ABI mặc định.

Debug metadata mô tả actual representation.

---

# 62. Closure capture state

Có thể debug:

```text
READ capture
WRITE capture
MOVE capture
```

trong semantic/debug build.

---

# 63. Comptime debugging

Comptime code có hai thế giới:

```text
compiler execution
runtime program
```

Debug metadata phải phân biệt.

---

# 64. Source generated by comptime

Nếu comptime sinh declaration:

```text
generated function
```

source provenance phải chỉ ra:

```text
generated from
comptime invocation
source input
```

---

# 65. Không được giả mạo generated code là source code gốc.

---

# 66. Generated source mapping

```text
GeneratedNode
    ↓
ComptimeOrigin
    ↓
SourceSpan / generated artifact
```

---

# 67. Macro

Core v1 không có general macro language.

Nhưng `@derive`/typed generation vẫn phải có provenance.

---

# 68. AI tooling

Compiler có thể cung cấp:

```text
ax debug-info
ax explain location
ax inspect variable
```

với semantic provenance.

---

# 69. AXCP integration

AXCP có thể hỏi:

```text
Which source expression produced this machine instruction?
```

và:

```text
Why is variable x optimized out?
```

---

# 70. Machine → source query

Compiler DB cần index:

```text
MachineAddressRange
→ DebugLocation
→ FunctionId
→ InlineContext
→ SourceSpan
```

---

# 71. Source → machine query

Ngược lại:

```text
SourceSpan
→ MIR instructions
→ LIR instructions
→ machine ranges
```

---

# 72. Đây là bidirectional provenance.

---

# 73. CompilerDB additions

Thêm:

```text
DebugDB
UnwindDB
MachineMapDB
InlineDB
VariableLocationDB
SourceProvenanceDB
```

---

# 74. IDs

```text
DebugInfoId
DebugLocationId
InlineContextId
VariableDebugId
VariableLocationId
MachineRangeId
UnwindRuleId
```

---

# 75. Không duplicate SourceDB

DebugDB tham chiếu:

```text
SourceFileId
SourceSpanId
DeclarationId
```

---

# 76. Debug levels

Nên có:

```text
none
line
local
full
semantic
```

---

# 77. `none`

Không emit debug information.

---

# 78. `line`

Chủ yếu:

```text
address → source location
```

phục vụ stack traces/profiling.

---

# 79. `local`

Thêm:

```text
variables
types
inline info
```

---

# 80. `full`

Thêm:

```text
rich variable locations
generic instances
closures
async state
source mappings
```

---

# 81. `semantic`

Axiom-specific debug mode có thể thêm:

```text
ownership
capability
effects
Send/Share
comptime origin
allocation provenance
```

---

# 82. Semantic debug metadata

Đây là điểm Axiom có thể vượt xa compiler truyền thống.

Ví dụ debugger có thể hỏi:

```text
Why can't I mutate x here?
```

và compiler trả:

```text
x has active READ capability C17
C17 originates from owner p
region overlaps requested WRITE region
```

---

# 83. Nhưng metadata này có thể strip

Không ảnh hưởng production semantics.

---

# 84. Allocation debugging

Compiler có thể map:

```text
Axiom allocation
→ MIR ALLOC
→ physical allocation
```

---

# 85. Allocation elimination

Nếu allocation bị optimize:

```text
ALLOC → eliminated
```

debugger không được giả vờ có heap object.

---

# 86. Escape analysis debug

Có thể inspect:

```text
x
storage = register
escape = NoEscape
allocation = eliminated
```

---

# 87. Inlining explanation

AXCP có thể hỏi:

```text
why was foo inlined?
```

Compiler trả:

```text
size threshold
hot callsite
monomorphic
cost model
```

---

# 88. Đây là tooling fact, không phải semantics.

---

# 89. PGO

Nếu PGO thay đổi machine layout, debug mapping vẫn phải hợp lệ.

---

# 90. LTO

LTO có thể merge:

```text
module A
module B
```

Debug provenance phải vẫn giữ source identity.

---

# 91. Cross-module inline

Inline context phải chứa:

```text
PackageId
ModuleId
FunctionId
```

---

# 92. Dynamic library

Symbol trong dynamic library phải giữ debug identity nếu debug artifact được cung cấp.

---

# 93. Separate debug files

Có thể:

```text
app.exe
app.debug
```

hoặc:

```text
ELF + separate DWARF
```

---

# 94. Binary stripping

Strip debug info không được thay đổi code semantics.

---

# 95. Reproducibility

Debug artifact cũng cần deterministic trong reproducible build mode.

Không để:

```text
absolute random temp path
timestamp
machine-specific path
```

phá hash.

---

# 96. Path remapping

Compiler hỗ trợ source path mapping:

```text
SourceRoot
```

để reproducible debug artifacts.

---

# 97. Security

Debug metadata có thể tiết lộ:

```text
source paths
symbol names
types
internal structure
```

Release distribution có thể strip.

---

# 98. Debug symbols không phải security boundary

---

# 99. Panic stack trace

Axiom panic runtime có thể request:

```text
stack trace
```

Stack trace pipeline:

```text
PC
 ↓
Unwind
 ↓
Physical frames
 ↓
Inline reconstruction
 ↓
Debug lookup
 ↓
Source locations
```

---

# 100. Panic without debug

Nếu không có debug metadata:

```text
function symbol
address
```

có thể là tất cả thông tin available.

---

# 101. Freestanding

Freestanding binary có thể không có:

```text
unwinder
debug runtime
symbol resolver
```

nhưng compiler vẫn có thể emit external debug artifact.

---

# 102. Kernel

Kernel debugging cần:

```text
physical addresses
symbol map
source mapping
```

nhưng không được yêu cầu hosted runtime.

---

# 103. FFI frame

Stack có thể:

```text
Axiom
  ↓
C
  ↓
Axiom
```

Debugger phải giữ language identity từng frame.

---

# 104. Foreign frame

Nếu không có debug symbols:

```text
unknown foreign frame
```

không được đoán.

---

# 105. Mixed-language debugging

Có thể:

```text
Axiom source
C source
Rust source
Swift source
```

trên cùng stack nếu debug formats hỗ trợ.

Axiom chỉ chịu trách nhiệm phần của mình.

---

# 106. ABI boundary

Debug metadata phải liên kết:

```text
Axiom FunctionId
↔ exported symbol
↔ ABI signature
```

---

# 107. Dynamic symbol

Nếu symbol bị strip nhưng runtime vẫn cần:

```text
export
```

thì symbol không được debug-only strip nhầm.

---

# 108. WASM debug

WASM backend có thể emit:

```text
DWARF
name section
source map
```

tùy host/toolchain.

---

# 109. WASM source map

Mapping:

```text
WASM bytecode offset
→ source
```

không thay thế Axiom semantic provenance.

---

# 110. Native DWARF

DWARF là serialization format.

Không phải debug semantic model của Axiom.

---

# 111. PDB/CodeView

Tương tự:

```text
Axiom DebugDB
      ↓
PDB/CodeView writer
```

---

# 112. Mach-O

Debug information được emit theo target object/debug ecosystem.

---

# 113. ELF

DWARF + unwind sections tùy profile.

---

# 114. PE/COFF

CodeView/PDB và Windows unwind metadata.

---

# 115. WASM

Custom sections + DWARF/source maps.

---

# 116. Không đưa DWARF vào Core

Core chỉ định nghĩa:

```text
semantic provenance
```

---

# 117. Debug writer architecture

```text
DebugDB
   │
   ▼
Debug IR
   │
   ├── DWARF Writer
   ├── CodeView Writer
   ├── PDB Writer
   ├── WASM Debug Writer
   └── Axiom Semantic Debug Writer
```

---

# 118. Unwind architecture

```text
UnwindDB
   │
   ▼
Unwind IR
   │
   ├── DWARF CFI
   ├── Windows XDATA/PDATA
   ├── Mach-O unwind
   └── Axiom runtime unwind format
```

---

# 119. Unwind IR target-independent

Ví dụ:

```text
UnwindRule {
    CFA = SP + 32
    RA = [CFA - 8]
    R19 = [CFA - 16]
}
```

Target writer serialize theo format.

---

# 120. Async unwind

Async state machines không được giả định có traditional stack frame.

Nếu Future suspension được represented runtime-side, stack trace phải kết hợp:

```text
physical stack
+
Future state
```

nếu runtime cung cấp metadata.

---

# 121. Fiber

Fiber stack có riêng:

```text
FiberId
StackBase
StackLimit
```

Unwinder phải biết execution domain.

---

# 122. GPU debugging

GPU machine code cũng có source provenance:

```text
Axiom source
→ GPU MIR
→ shader/kernel instruction
```

nhưng GPU debugger là platform-specific.

---

# 123. GPU thread identity

Nếu platform hỗ trợ:

```text
workgroup
subgroup
lane
```

debug metadata có thể expose.

---

# 124. Không ảnh hưởng CPU semantics.

---

# 125. Constant-time code

Debug instrumentation không được vô tình được coi là production execution semantics.

Nhưng constant-time validation phải chạy trên semantic/compiler representation trước debug instrumentation khi cần.

---

# 126. Sanitizer

Sanitizer instrumentation:

```text
runtime instrumentation
```

không phải debug provenance authority.

---

# 127. Sanitizer-generated instructions

Có thể đánh dấu:

```text
compiler_generated = true
```

để debugger không nhảy sai source.

---

# 128. Compiler-generated code

Tất cả generated code cần:

```text
GeneratedOrigin
```

---

# 129. Examples

Bao gồm:

```text
closure environment
async state machine
drop glue
trait dispatch thunk
ABI adapter
FFI wrapper
bounds-check helper
panic path
comptime generated function
```

---

# 130. Drop glue

Nếu compiler tạo:

```text
drop glue
```

debugger có thể thấy:

```text
<generated drop>
```

nhưng source provenance trỏ về owner/field tương ứng.

---

# 131. Trait thunk

`dyn Trait` có thể tạo thunk.

Debugger không được coi thunk là source-level function mới.

---

# 132. ABI adapter

Tương tự:

```text
Axiom
 ↓
C ABI adapter
 ↓
foreign function
```

---

# 133. Optimized control flow

Nếu compiler merge blocks:

```text
source branches
```

thành một machine region, debug stepping không được quay về source branch đã bị loại bỏ như thể nó thực sự chạy.

---

# 134. Debug stepping

Stepping phải dựa trên:

```text
semantic execution locations
```

trong phạm vi thông tin machine còn có thể biểu diễn.

---

# 135. Optimized debugging không thể hoàn hảo

Đây là giới hạn thực tế.

Compiler không được giả tạo một illusion sai.

---

# 136. Principle

> **Khi source-level state không còn tồn tại trong machine program, debugger phải nói “optimized out”, không được dựng lại một giá trị giả.**

---

# 137. Debugger semantic query

Axiom debugger có thể query:

```text
variable(x)
type(x)
ownership(x)
capability(x)
location(x)
origin(x)
```

---

# 138. Source → machine

```text
explain --source file.ax:42
```

có thể trả:

```text
MIR instructions
OptIR instructions
machine ranges
```

---

# 139. Machine → source

```text
inspect --address 0x1234
```

có thể trả:

```text
function
inline stack
source span
MIR instruction
```

---

# 140. Compiler cache

DebugDB phải incremental.

Nếu chỉ sửa:

```text
function A
```

không cần regenerate debug info cho toàn package nếu các ranges khác không đổi.

---

# 141. Stable IDs

Debug references sử dụng semantic IDs thay vì raw memory addresses của compiler process.

---

# 142. Parallel codegen

Debug generation phải deterministic dù codegen chạy song song.

---

# 143. Reproducible debug ordering

Symbols, types, source units, ranges phải có canonical ordering.

---

# 144. Debug metadata size

Debug info có thể lớn hơn binary rất nhiều.

Không được đưa nó vào runtime binary mặc định.

---

# 145. Profile

```text
release:
    stripped

release-debug:
    external debug

dev:
    full debug

semantic-debug:
    full + Axiom semantic metadata
```

---

# 146. `@no_debug`

Có thể cần system-level opt-out cho sensitive/generated regions.

---

# 147. Nhưng không được làm mất mandatory ABI/unwind metadata nếu platform yêu cầu runtime correctness.

---

# 148. Stack trace symbolization

Có thể tách:

```text
binary
symbolizer
debug artifact
```

---

# 149. Không cần runtime reflection

Stack trace không đồng nghĩa runtime reflection.

---

# 150. Đây là distinction rất quan trọng

```text
Debug metadata
≠
Runtime reflection
```

---

# 151. Runtime reflection

Chỉ tồn tại khi application yêu cầu.

Debug info có thể tồn tại ngoài binary.

---

# 152. `.axmeta`

`.axmeta` có thể chứa semantic information phục vụ tooling.

Nhưng:

```text
.axmeta
≠
debug info
```

---

# 153. Ba artifact

Có thể có:

```text
app.exe
app.axmeta
app.debug
```

với mục đích khác nhau.

---

# 154. `.axmeta`

Compiler/IDE/AI semantic metadata.

---

# 155. `.debug`

Debugger/source/unwind metadata.

---

# 156. Binary

Runtime artifact tối thiểu.

---

# 157. Minimal binary

Một freestanding program có thể:

```text
app.exe
```

không có:

```text
runtime reflection
debug info
.axmeta
```

---

# 158. Semantic correctness boundary

Debug generation xảy ra **sau** semantics:

```text
Verified MIR
```

Không được dùng debug info để quyết định program semantics.

---

# 159. Exception/panic

Axiom không có exceptions Core.

Unwind chỉ là:

```text
panic profile
```

hoặc:

```text
FFI/platform mechanism
```

---

# 160. Panic abort

Nếu profile:

```text
panic = abort
```

không cần full unwind machinery.

---

# 161. Panic unwind

Nếu:

```text
panic = unwind
```

compiler phải emit unwind metadata và cleanup paths.

---

# 162. Drop + unwind

Unwinder phải đảm bảo semantic cleanup:

```text
owner
 ↓
Drop
```

theo verified MIR.

---

# 163. Không được để unwind bỏ qua Drop

---

# 164. `catch` nếu có

Nếu application/runtime cung cấp panic catching, semantics phải nằm ngoài Core hoặc profile rõ ràng.

Debug/unwind chỉ implement contract đó.

---

# 165. Signal/crash

OS signal:

```text
SIGSEGV
access violation
```

khác với Axiom panic.

Debugger có thể report:

```text
native fault
```

không biến nó thành language panic.

---

# 166. Unsafe fault

Raw pointer fault là machine/OS event.

Debug metadata giúp map nó về source nhưng không biến unsafe operation thành safe semantic operation.

---

# 167. Machine fault address

Crash report nên có:

```text
PC
fault address
access type
source location
inline stack
```

nếu platform cung cấp.

---

# 168. Axiom crash diagnostics

Ví dụ conceptual:

```text
Memory fault at source:
    foo.ax:42

Function:
    process

Operation:
    raw pointer load

Provenance:
    unavailable/unsafe boundary

Inline stack:
    process
    caller
```

---

# 169. Không suy đoán nguyên nhân

Compiler chỉ báo facts có thể chứng minh.

---

# 170. Debug security

Semantic debug mode có thể tiết lộ ownership/resource information.

Production release có thể strip.

---

# 171. Cryptographic secrets

Nếu compiler biết:

```text
Secret<T>
```

debugger không được tự động dump raw secret.

---

# 172. Constant-time

Debugger breakpoints/instrumentation có thể thay đổi timing.

Do đó constant-time production guarantee không thể được suy ra từ debug execution.

---

# 173. GPU secrets

Tương tự.

---

# 174. FFI

Foreign memory không được debugger giả định là Axiom-owned.

---

# 175. Dynamic libraries

Nếu library unload:

```text
debug symbol address
```

phải được invalidated theo module lifetime.

---

# 176. Module identity

Debug module:

```text
ModuleBuildId
```

để symbolizer tránh load nhầm debug artifact của phiên bản khác.

---

# 177. Build ID

Có thể:

```text
BuildId
```

liên kết:

```text
binary ↔ debug ↔ metadata
```

---

# 178. Reproducible builds

Build ID phải deterministic hoặc content-derived khi reproducible mode.

---

# 179. Symbol identity

Symbol identity không chỉ dựa vào string.

Dùng:

```text
FunctionId
SemanticFingerprint
ABI fingerprint
```

rồi serialize thành symbol/debug identity.

---

# 180. Debug artifact compatibility

Debugger phải phát hiện:

```text
binary BuildId != debug BuildId
```

thay vì dùng nhầm metadata.

---

# 181. Tooling API

Compiler cung cấp:

```text
DebugQuery {
    address_to_source()
    source_to_address()
    variable_location()
    inline_stack()
    type_layout()
    ownership_state()
    capability_state()
    generated_origin()
}
```

---

# 182. IDE

IDE có thể dùng cùng API thay vì parse DWARF/PDB trực tiếp cho các tính năng Axiom-specific.

---

# 183. External debugger

GDB/LLDB/WinDbg vẫn dùng standard debug formats.

---

# 184. Axiom debugger

Có thể có frontend riêng dùng:

```text
AXCP
+
DebugDB
```

---

# 185. Debug pipeline hoàn chỉnh

```text
Verified MIR
     │
     ├───────────────► Debug semantic provenance
     │
     ▼
    OptIR
     │
     ├───────────────► optimized provenance
     │
     ▼
  ABI MIR
     │
     ▼
 Axiom LIR
     │
     ▼
 Machine IR
     │
     ├───────────────► MachineRangeMap
     │
     ├───────────────► VariableLocationMap
     │
     └───────────────► UnwindRules
     │
     ▼
 Machine Code
     │
     ├───────────────► DWARF/PDB/CodeView
     ├───────────────► Unwind sections
     └───────────────► Axiom semantic debug metadata
```

---

# 186. CompilerDB architecture cập nhật

```text id="8q2w7s"
CompilerDB
├── SourceDB
├── PackageDB
├── ModuleDB
├── SyntaxDB
├── DeclarationDB
├── TypeDB
├── TraitDB
├── ConstDB
├── GenericDB
├── ComptimeDB
├── HIRDB
├── MIRDB
├── DebugDB
├── UnwindDB
├── InlineDB
├── VariableLocationDB
├── SourceProvenanceDB
├── DiagnosticDB
├── SourceMapDB
├── LayoutDB
├── AbiDB
├── CodegenDB
└── BuildDB
```

---

# 187. Semantic flow hiện tại

```text id="m3qk5s"
Source
 ↓
Lossless Syntax
 ↓
AST
 ↓
Resolution
 ↓
HIR
 ↓
Typed HIR
 ↓
MIR
 ↓
Ownership/Capability/Effect verification
 ↓
Verified MIR
 ↓
Semantic Optimization
 ↓
OptIR
 ↓
ABI Lowering
 ↓
Axiom LIR
 ↓
Target Backend
 ↓
Machine IR / WASM IR
 ↓
Machine Verification
 ↓
Machine Code
 ↓
Object
 ↓
Link
 ↓
Final Binary
```

Debug information chạy **song song với lowering**, nhưng không nằm trên semantic critical path.

---

# 188. Invariants — `ADEBUG-20..100`

```text id="l8q0c5"
ADEBUG-20
Debug information does not define Axiom program semantics.

ADEBUG-21
Semantic provenance originates from source and compiler semantic entities.

ADEBUG-22
SourceSpan remains the canonical source-location identity.

ADEBUG-23
Machine instructions may map to multiple semantic origins.

ADEBUG-24
One semantic operation may map to multiple machine ranges.

ADEBUG-25
Debug mappings must not assume one-to-one source/instruction correspondence.

ADEBUG-26
Debug locations do not define evaluation order.

ADEBUG-27
Optimization may reorder physical instructions without changing semantic provenance.

ADEBUG-28
Optimized-out values must never be represented as fabricated runtime values.

ADEBUG-29
Variable locations may change during execution.

ADEBUG-30
Variable locations may be composite.

ADEBUG-31
Semantic types may differ from physical representations.

ADEBUG-32
Debuggers must use actual target layout when displaying physical values.

ADEBUG-33
Enum debugging must reconstruct semantic variants.

ADEBUG-34
Niche optimization must not prevent semantic variant inspection when metadata is available.

ADEBUG-35
Generic instances must retain sufficient identity for debugging.

ADEBUG-36
Shared generic code may have multiple logical source origins.

ADEBUG-37
Inline call stacks must be reconstructable independently of physical stack frames.

ADEBUG-38
Inlining must not erase source-level call provenance.

ADEBUG-39
Debug info and unwind info are separate semantic artifacts.

ADEBUG-40
Unwind rules must correspond to generated frame semantics.

ADEBUG-41
Frame-pointer omission must remain debuggable/unwindable when the selected profile requires it.

ADEBUG-42
Leaf functions may omit physical frames.

ADEBUG-43
Tail calls may eliminate physical frames.

ADEBUG-44
Async state machines must preserve source provenance for suspension points.

ADEBUG-45
Source locals transformed into Future state fields must remain debuggable when information exists.

ADEBUG-46
Closure environments must retain source capture provenance.

ADEBUG-47
Generated drop glue must retain origin information.

ADEBUG-48
Generated ABI thunks must retain origin information.

ADEBUG-49
Generated comptime declarations must retain generation provenance.

ADEBUG-50
Generated code must never be falsely attributed to unrelated source.

ADEBUG-51
Debug metadata may be external to the runtime binary.

ADEBUG-52
Debug metadata is not runtime reflection.

ADEBUG-53
.axmeta and debug artifacts have distinct purposes.

ADEBUG-54
Debug metadata can be stripped without changing program semantics.

ADEBUG-55
Unwind metadata required for runtime correctness cannot be stripped when the selected profile requires it.

ADEBUG-56
Panic-abort profiles do not require full unwind machinery.

ADEBUG-57
Panic-unwind profiles must preserve verified Drop semantics.

ADEBUG-58
Native faults must not automatically be classified as Axiom panics.

ADEBUG-59
FFI frames must retain foreign-language identity where available.

ADEBUG-60
Dynamic library debug identity must follow module/build identity.

ADEBUG-61
Binary and debug artifacts must be matched by build identity.

ADEBUG-62
Reproducible builds must produce deterministic debug metadata when enabled.

ADEBUG-63
Debug paths must support deterministic source remapping.

ADEBUG-64
Debug symbol ordering must be deterministic.

ADEBUG-65
Parallel code generation must not produce nondeterministic debug mappings.

ADEBUG-66
Axiom semantic debug information may expose ownership state.

ADEBUG-67
Axiom semantic debug information may expose capability state.

ADEBUG-68
Semantic debug information must not introduce runtime ownership/capability overhead by default.

ADEBUG-69
Semantic debug information may be omitted from release artifacts.

ADEBUG-70
AI/compiler tooling may query source-to-machine provenance.

ADEBUG-71
AI/compiler tooling may query machine-to-source provenance.

ADEBUG-72
AI tooling must not fabricate unavailable optimized values.

ADEBUG-73
Debug metadata must preserve security-sensitive metadata handling rules.

ADEBUG-74
Secret values must not be automatically exposed merely because debug information exists.

ADEBUG-75
Constant-time guarantees must not depend on debug execution behavior.

ADEBUG-76
GPU debug provenance follows the same source-to-machine principle.

ADEBUG-77
WASM debug information must map WASM offsets to Axiom source provenance.

ADEBUG-78
WASM source maps do not replace Axiom semantic provenance.

ADEBUG-79
DWARF, PDB, CodeView and source maps are serialization formats, not Core semantics.

ADEBUG-80
Debug writers consume target-independent debug representation.

ADEBUG-81
Unwind writers consume target-independent unwind representation.

ADEBUG-82
Debug generation must occur after semantic correctness is established.

ADEBUG-83
Debug generation cannot weaken ownership/capability verification.

ADEBUG-84
Debug generation cannot change ABI classification.

ADEBUG-85
Debug generation cannot change target semantics.

ADEBUG-86
Debug instrumentation is not part of the semantic authority.

ADEBUG-87
Sanitizer instrumentation does not replace debug provenance.

ADEBUG-88
Optimized debugging may legitimately report unavailable values.

ADEBUG-89
Source stepping must not imply execution of source constructs removed by optimization.

ADEBUG-90
Inline frames are logical debugging frames, not necessarily physical frames.

ADEBUG-91
Async frames are logical debugging states, not necessarily physical stack frames.

ADEBUG-92
Ownership states shown by tooling are semantic facts, not mutable runtime objects.

ADEBUG-93
Machine address identity is distinct from source semantic identity.

ADEBUG-94
Debug metadata must remain consistent with actual generated machine code.

ADEBUG-95
Unwind metadata must remain consistent with actual generated frame behavior.

ADEBUG-96
Mismatched binary/debug artifacts must be detected.

ADEBUG-97
Backend-specific debug formats must not leak into frontend semantics.

ADEBUG-98
Adding a target-specific debug format must not require changing Axiom Core.

ADEBUG-99
Source-to-machine provenance is bidirectional.

ADEBUG-100
Debugging is a projection of compiler semantic knowledge, not a second semantic model.
```

---

# 189. Một kết quả rất đáng chú ý

Sau task này, Axiom có thể cung cấp một khả năng mà chúng ta đã hướng tới từ đầu:

```text
Source
  ↓
"tại sao dòng này chậm?"
  ↓
CompilerDB
  ↓
MIR
  ↓
OptIR
  ↓
AliasInfo
  ↓
EscapeInfo
  ↓
Inlining
  ↓
Vectorization
  ↓
Machine instructions
```

và ngược lại:

```text
Instruction 0x1234
      ↓
MachineRange
      ↓
LIR
      ↓
OptIR
      ↓
MIR
      ↓
SourceSpan
```

Đây chính là nền tảng để **AI-native compiler tooling** của Axiom thực sự hữu ích, thay vì AI phải đoán từ source code.

---

# 190. Kiến trúc Axiom lúc này

Chúng ta đã đi từ:

```text
Language
```

đến:

```text
Language
 → Semantic model
 → Verification
 → Optimization
 → ABI
 → LIR
 → Native backends
 → WASM
 → Object
 → Linker
 → Runtime
 → Debug/Unwind
```

Một boundary rất đẹp hiện ra:

```text
                    ┌──────────────────────────┐
                    │       SEMANTIC WORLD     │
                    │                          │
                    │ Source → MIR → Verified  │
                    │ Ownership                │
                    │ Capability               │
                    │ Effects                  │
                    │ Types                    │
                    │ Concurrency              │
                    │ Async                    │
                    └────────────┬─────────────┘
                                 │
                                 ▼
                           Semantic OptIR
                                 │
                                 ▼
                              ABI MIR
                                 │
                                 ▼
                            Axiom LIR
                                 │
                    ┌────────────┴────────────┐
                    │                         │
              Physical World            Debug World
                    │                         │
              TargetBackend              Provenance
                    │                         │
              Machine IR                 DebugDB
                    │                         │
              Machine Code               UnwindDB
                    │                         │
              Object/Link                 DWARF/PDB
                    │
                    ▼
               Final Binary
```

**Debug World không được phép quay ngược và thay đổi Semantic World.**

---

## BOOTSTRAP-267 — bước tiếp theo

Sau 266, bước tiếp theo hợp lý là **không thêm feature ngôn ngữ mới**, mà xử lý một phần còn cực kỳ quan trọng của compiler native:

### **BOOTSTRAP-267 — AXIOM LINK-TIME CODE GENERATION, LTO, WHOLE-PROGRAM OPTIMIZATION & BINARY SIZE**

Sẽ formalize pipeline:

```text
Package A
Package B
Library C
      │
      ▼
   .axlib
      │
      ▼
Link-time CompilerDB
      │
      ├── cross-module type facts
      ├── ownership facts
      ├── capability/alias facts
      ├── effect facts
      ├── specialization
      ├── devirtualization
      ├── cross-module inlining
      ├── dead code elimination
      ├── identical code folding
      ├── data elimination
      ├── runtime component elimination
      └── whole-program optimization
      │
      ▼
Final AxiomObject
      │
      ▼
Native Binary / WASM
```

Đặc biệt task 267 sẽ giải quyết mục tiêu ban đầu của bạn về **binary nhỏ gọn**, nhưng theo cách không đánh đổi semantics: compiler phải biết chính xác phần nào của package/runtime/trait/generic/metadata thực sự được sử dụng và loại bỏ phần còn lại.