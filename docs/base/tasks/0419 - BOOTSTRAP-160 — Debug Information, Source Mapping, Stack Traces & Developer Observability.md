# BOOTSTRAP-160 — Debug Information, Source Mapping, Stack Traces & Developer Observability
**STATUS: FROZEN / COMPLETED**

> **Debugging phải quan sát được chương trình theo semantic model của Axiom, không phải ép compiler hy sinh optimization để debugger hoạt động.**

Đây là phần rất quan trọng sau `ATEST2`, vì Axiom đã có pipeline compiler cực kỳ sâu:

```text
Source
 ↓
AST
 ↓
HIR
 ↓
MIR
 ↓
Verified MIR
 ↓
OptIR
 ↓
ABI MIR
 ↓
LIR
 ↓
Machine
 ↓
Object
 ↓
Executable
```

Debugger phải hiểu được chuỗi biến đổi này.

---

# 1. Source Mapping là first-class compiler data

Không chỉ lưu:

```text
machine address → source line
```

Axiom lưu:

```text
SourceOrigin {
    SourceFileId
    SourceSpan
    SyntaxId
    DeclarationId
    ExpressionId
    StatementId
    MirLocation
    OptLocation
    LirLocation
    MachineLocation
}
```

---

# 2. Mapping hai chiều

Không chỉ:

```text
source → machine
```

mà phải hỗ trợ:

```text
source → HIR → MIR → OptIR → LIR → machine
```

và:

```text
machine → LIR → OptIR → MIR → source
```

Đây là nền tảng cho cả debugger lẫn AI tooling.

---

# 3. Optimization không được phá provenance

Ví dụ:

```ax
let x = a + b;
let y = x * 2;
```

Compiler biến thành:

```text
x eliminated
y = (a+b)*2
```

Debugger vẫn phải biết:

```text
x
```

đã tồn tại trong source, nhưng physical storage của nó không còn tồn tại.

---

# 4. Optimized variable state

Debugger phải phân biệt:

```text
Available
Constant
Register
Stack
OptimizedOut
Merged
Split
Rematerializable
Unavailable
```

Không được giả vờ rằng mọi source variable luôn tồn tại trong memory.

---

# 5. `optimized out`

Ví dụ debugger:

```text
x = <optimized out>
```

đây là kết quả hợp lệ.

Không nên ép compiler tạo stack slot chỉ để debugger nhìn thấy `x`.

---

# 6. Rematerialization

Nếu:

```text
x = a + 1
```

đã bị loại khỏi storage nhưng compiler có thể tính lại:

```text
x = a + 1
```

debugger có thể materialize giá trị tại breakpoint nếu semantic context cho phép.

---

# 7. Debug location không đồng nghĩa instruction location

Một source statement có thể tạo:

```text
0 instructions
```

hoặc:

```text
1 instruction
```

hoặc:

```text
20 instructions
```

hoặc bị inline vào nhiều call sites.

Mapping phải hỗ trợ one-to-many và many-to-one.

---

# 8. Inlining

Ví dụ:

```ax
fn square(x: i32) -> i32 {
    return x * x;
}

fn main() {
    let y = square(5);
}
```

Compiler inline `square`.

Machine code không còn call.

Debugger vẫn phải hiển thị logical stack:

```text
main()
  └── square()
```

dù physical stack không có frame `square`.

---

# 9. Inline stack

Debug location nên chứa:

```text
InlineFrame {
    FunctionId
    CallSite
    ParentInlineFrame
}
```

Machine instruction có thể tương ứng với:

```text
main → calculate → square
```

---

# 10. Tail call

Nếu:

```text
foo()
```

được tail-call thành:

```text
jump foo
```

physical stack frame của caller có thể biến mất.

Debugger vẫn cần semantic call relationship khi có thể.

---

# 11. Closure debugging

Closure có:

```text
code
+
environment
```

nhưng optimizer có thể scalarize environment.

Debugger phải map:

```text
closure.capture
```

về source variable ngay cả khi không còn một environment object vật lý.

---

# 12. Async debugging

Async đặc biệt khó.

Source:

```ax
let x = await read();
use(x);
```

Compiler tạo:

```text
Future state machine
```

Debugger phải hiển thị:

```text
async_function()
    state = AwaitPoint(3)
    x = ...
```

thay vì bắt programmer hiểu machine-generated state struct.

---

# 13. SuspensionPointId

Đã có:

```text
SuspensionPointId
```

Debugger sử dụng nó để map:

```text
Future state
→ source await
```

---

# 14. Async stack trace

Khi task đang chạy:

```text
Task A
 └─ foo()
     └─ await bar()
```

stack trace có thể hiển thị **logical async stack**.

Physical stack có thể chỉ chứa executor.

---

# 15. Spawn boundary

Nếu:

```text
spawn(worker())
```

thì debugger phân biệt:

```text
caller task
worker task
```

không giả vờ chúng là một call stack thông thường.

---

# 16. Thread debugging

Thread có:

```text
ThreadId
ExecutionDomain
```

Debugger có thể query:

```text
threads
thread backtrace
thread locals
thread synchronization state
```

---

# 17. Mutex/lock observability

Trong debug build, sync primitives có thể cung cấp metadata:

```text
Mutex
 owner
 acquisition location
 waiting threads
```

nhưng metadata này **không bắt buộc** trong release.

---

# 18. Ownership debugging

Đây là một lợi thế rất lớn của Axiom.

Debugger có thể hiển thị:

```text
x
 ├── ownership: Owned
 ├── state: Initialized
 ├── Drop: required
 └── capabilities: none
```

hoặc:

```text
x
 ├── ownership: Moved
 └── moved_at: source.ax:42
```

---

# 19. Capability debugging

Ví dụ:

```text
view
```

debugger có thể hiển thị:

```text
Capability #17
 owner: buffer
 region: [100,200)
 access: READ
 lifetime: active
```

Đây là **semantic debug information**, không nhất thiết tồn tại trong machine binary.

---

# 20. Không đưa ownership metadata vào release runtime

Compiler có thể erase:

```text
CapabilityId
RegionId
OwnershipState
```

sau verification nếu không observable.

Debugger đọc metadata riêng.

---

# 21. Drop debugging

Nếu:

```ax
let file = open(...);
```

debugger có thể biết:

```text
Drop obligation: active
```

và khi scope kết thúc:

```text
Drop → executed
```

rất hữu ích cho resource debugging.

---

# 22. Partial move debugging

Ví dụ:

```ax
let a = value.field_a;
```

sau đó:

```text
value
 ├── field_a → MOVED
 └── field_b → INIT
```

Debugger có thể hiển thị field-level ownership.

---

# 23. Không giả tạo object memory

Debugger không nên hiển thị một struct như một contiguous memory object nếu optimizer đã:

```text
SROA
field splitting
register allocation
```

Nó hiển thị **semantic value**.

---

# 24. Data layout observability

Nếu source dùng:

```ax
offset_of(...)
address_of(...)
@repr(C)
```

layout trở thành observable.

Debugger phải sử dụng physical layout tương ứng.

Nếu không:

```text
semantic field → logical mapping
```

được ưu tiên.

---

# 25. Debugging optimized structs

Ví dụ:

```text
Particle {
    x
    y
    velocity
}
```

compiler có thể biến thành:

```text
x → xmm0
y → xmm1
velocity → xmm2
```

Debugger vẫn hiển thị:

```text
Particle
 ├─ x
 ├─ y
 └─ velocity
```

---

# 26. Variable location expressions

Debug metadata cần hỗ trợ:

```text
Register
StackOffset
Constant
Piece
Composite
Expression
Unavailable
```

để reconstruct semantic value.

---

# 27. Composite values

Một struct có thể:

```text
x → register
y → register
z → stack
```

Debugger ghép chúng thành một logical value.

---

# 28. Constant values

Nếu:

```ax
const N = 1024;
```

thì không cần runtime storage.

Debugger vẫn có thể inspect:

```text
N = 1024
```

từ compile-time metadata.

---

# 29. Comptime values

Compiler-generated value từ:

```ax
comptime
```

có thể có source provenance:

```text
ComptimeOrigin
```

nhưng không được giả rằng nó tồn tại runtime.

---

# 30. Generated declarations

Nếu comptime tạo:

```text
GeneratedFunction
```

debugger phải map:

```text
generated declaration
→ generator source
→ generated HIR
→ machine code
```

khi metadata được giữ.

---

# 31. Macro tương lai

Nếu sau này có macro system, nguyên tắc:

```text
generated code
```

phải giữ provenance về:

```text
macro invocation
+
generated span
```

không để debugger rơi vào “mystery code”.

---

# 32. Breakpoint model

Axiom debugger hỗ trợ:

```text
source breakpoint
function breakpoint
instruction breakpoint
conditional breakpoint
watchpoint
data breakpoint
```

target debugger backend quyết định khả năng vật lý.

---

# 33. Breakpoint tại optimized code

Một source line có thể:

```text
merged
inlined
eliminated
reordered
```

Debugger đặt breakpoint tại những machine locations còn đại diện cho source location đó.

---

# 34. Conditional breakpoint

Điều kiện phải được đánh giá an toàn theo debugger expression evaluator.

Không được mặc định chạy arbitrary program code trong process.

---

# 35. Watch expression

Debugger có semantic type information:

```text
TypeId
Layout
Fields
Enum variants
```

nên có thể evaluate:

```text
x.field
```

mà không cần biết parser source-level đầy đủ.

---

# 36. Memory inspection

System debugger vẫn có thể inspect raw memory.

Nhưng phân biệt:

```text
semantic value
```

và:

```text
raw machine memory
```

đúng như Axiom memory model.

---

# 37. Raw pointer debugging

Nếu:

```ax
*mut T
```

được inspect:

```text
address
provenance
target type
```

nếu metadata có.

Nhưng debugger không được tuyên bố rằng một integer chắc chắn là valid Axiom pointer.

---

# 38. Stack traces

Stack trace chuẩn:

```text
PC
 ↓
machine symbol
 ↓
inline stack
 ↓
source span
```

Nếu unwind info có thể walk stack.

Nếu:

```text
panic=abort
```

vẫn có thể giữ optional debug backtrace metadata trong debug builds.

---

# 39. Panic backtrace

Ví dụ:

```text
panic
 ├─ source location
 ├─ logical function
 ├─ inline frames
 ├─ async frames
 └─ thread/task
```

không nhất thiết phải chứa runtime reflection.

---

# 40. Symbol model

Phân biệt:

```text
Source symbol
Debug symbol
Linker symbol
Machine symbol
Exported symbol
```

`pub` không tự động biến thành exported native symbol.

---

# 41. Stripped binary

Release binary có thể:

```text
strip debug information
```

nhưng symbol/ABI cần thiết cho dynamic linking vẫn giữ.

---

# 42. Separate debug artifacts

Đề xuất:

```text
program.exe
program.debug
```

hoặc target-native:

```text
DWARF
PDB
dSYM
```

Axiom compiler tạo metadata phù hợp target.

---

# 43. Debug metadata không ảnh hưởng semantics

Debug info:

```text
non-semantic
```

Compiler có thể bỏ toàn bộ mà executable behavior không thay đổi.

---

# 44. Debug info không được ép layout

Trừ khi debugger contract yêu cầu observability đặc biệt.

Ví dụ compiler không được:

```text
disable SROA
```

chỉ vì variable nằm trong debugger.

Thay vào đó metadata mô tả optimized state.

---

# 45. Debug build vs optimized debug

Axiom nên hỗ trợ:

```text
-O0 -g
-O1 -g
-O2 -g
-O3 -g
```

Không chỉ:

```text
debug = O0
release = O3
```

---

# 46. `-g` không có nghĩa disable optimization

Đây là quyết định quan trọng.

```text
-g
```

chỉ yêu cầu:

```text
retain debugging observability metadata
```

không yêu cầu:

```text
disable optimizer
```

---

# 47. Debug optimization policy

Compiler có thể có:

```text
-g
-gminimal
-gfull
-gsemantic
```

để kiểm soát metadata size.

---

# 48. Semantic debug mode

Đề xuất profile:

```text
-gsemantic
```

giữ thêm:

```text
ownership provenance
capability provenance
comptime provenance
optimization provenance
```

rất hữu ích cho compiler/AI debugging.

---

# 49. AI debugging API

Compiler/debugger có thể expose:

```text
axdbg inspect value x
axdbg inspect ownership x
axdbg inspect capability x
axdbg inspect source
axdbg inspect optimized-from
```

AI nhận structured output thay vì chỉ đọc debugger text.

---

# 50. `why` query

Ví dụ:

```text
axc explain optimized-out x
```

có thể trả:

```text
x
 ↓
constant propagation
 ↓
value substituted into y
 ↓
no observable storage
 ↓
SROA
 ↓
dead value elimination
```

---

# 51. Optimization provenance

Mỗi optimized value/instruction có thể truy ngược:

```text
OptimizationRecord {
    PassId
    InputNodes
    OutputNodes
    Reason
    LegalityFacts
}
```

đã phù hợp với `ATEST2`.

---

# 52. Debugger và code folding

Nếu hai function được ICF merge:

```text
foo
bar
 ↓
same machine body
```

debugger vẫn phải biết source identity của cả hai.

---

# 53. Debugger và tail merging

Một machine block có thể đại diện cho nhiều source paths.

Mapping phải hỗ trợ:

```text
machine block
→ multiple source origins
```

---

# 54. Debugger và hot/cold splitting

Nếu:

```text
foo.hot
foo.cold
```

được compiler tạo:

Debugger hiển thị:

```text
foo()
```

không bắt programmer hiểu implementation split.

---

# 55. Debugger và section GC

Dead code không có debug location trong final executable.

Không giữ debug references làm sống lại dead machine code.

---

# 56. Debugger và linker relaxation

Nếu linker thay đổi instruction:

```text
long branch
→ short branch
```

source mapping phải được cập nhật hoặc preserved thông qua relocation/debug mapping.

---

# 57. Cross-platform debug

Architecture:

```text
Axiom Debug Model
        ↓
Target Debug Adapter
   ┌────┼────┬────┐
 DWARF PDB dSYM WASM
```

Semantic model chung.

Format-specific encoding riêng.

---

# 58. DWARF

Linux/Unix có thể emit:

```text
DWARF
```

với semantic mapping phù hợp.

---

# 59. Windows

Windows target có thể emit:

```text
PDB
```

và PE/COFF debug references.

---

# 60. Apple

Mach-O ecosystem có thể sử dụng:

```text
dSYM / DWARF
```

---

# 61. WASM

WASM debug mapping sử dụng:

```text
source mapping
function metadata
DWARF where supported
```

theo target tooling.

---

# 62. Debugger interface

Đề xuất compiler-independent protocol:

```text
Axiom Debug Information Model
```

với:

```text
Type
Value
Variable
Location
InlineFrame
SourceSpan
Function
Thread
Task
Capability
Ownership
```

Target debugger adapter chuyển sang debugger protocol thực tế.

---

# 63. Không bắt buộc debugger riêng của Axiom

Axiom nên emit chuẩn:

```text
DWARF
PDB
```

để debugger hiện có có thể sử dụng.

Sau đó mới có:

```text
axdbg
```

làm debugger semantic-native.

---

# 64. `axdbg`

Nếu xây debugger riêng:

```text
axdbg run
axdbg attach
axdbg break
axdbg continue
axdbg next
axdbg step
axdbg inspect
axdbg threads
axdbg tasks
axdbg backtrace
axdbg watch
```

Nhưng đây là tooling, không phải Core.

---

# 65. Crash dump

Axiom system layer có thể hỗ trợ:

```text
CrashContext {
    PC
    registers
    stack
    thread
    target
    build_id
    module
}
```

Debug symbols tra cứu offline.

---

# 66. Build ID

Executable nên có:

```text
BuildId
```

liên kết với:

```text
debug artifact
profile
source fingerprint
compiler version
target
```

để crash report tìm đúng binary/debug info.

---

# 67. Reproducible debugging

Nếu build reproducible:

```text
same source
same compiler
same config
```

thì:

```text
debug mapping
```

cũng phải deterministic trong phạm vi artifact contract.

---

# 68. Security

Debug metadata có thể tiết lộ:

```text
source paths
symbols
types
internal structure
```

Release build phải có khả năng:

```text
strip
split
redact
```

mà không thay đổi executable semantics.

---

# 69. Debug metadata và reflection

Không được nhầm:

```text
debug info
```

với:

```text
runtime reflection
```

Debug info có thể tồn tại bên ngoài executable.

Runtime reflection chỉ tồn tại nếu program yêu cầu.

---

# 70. Debugging contract

Đóng băng:

### `ADEBUG-20`
Source-to-machine provenance is first-class compiler metadata.

### `ADEBUG-21`
Debug mapping is bidirectional where information remains available.

### `ADEBUG-22`
Optimization must preserve provenance for surviving observable code.

### `ADEBUG-23`
Debug information does not define program semantics.

### `ADEBUG-24`
Removing debug information must not change program semantics.

### `ADEBUG-25`
Debugging optimized programs is supported.

### `ADEBUG-26`
`-g` does not imply disabling optimization.

### `ADEBUG-27`
Optimized-out values are valid debugger states.

### `ADEBUG-28`
Debugger may reconstruct rematerializable values.

### `ADEBUG-29`
Logical variables need not have physical storage.

### `ADEBUG-30`
SSA/register/scalarized values can be represented as source-level values.

### `ADEBUG-31`
Composite values may be reconstructed from multiple physical locations.

### `ADEBUG-32`
Inlining preserves logical call provenance.

### `ADEBUG-33`
Tail calls preserve available logical provenance.

### `ADEBUG-34`
Closure environments may be optimized away without destroying source provenance.

### `ADEBUG-35`
Async state machines retain `SuspensionPointId` provenance.

### `ADEBUG-36`
Logical async stacks may differ from physical stacks.

### `ADEBUG-37`
Thread and task identity are distinct debugger concepts.

### `ADEBUG-38`
Ownership state may be exposed through semantic debug metadata.

### `ADEBUG-39`
Capability provenance may be exposed in semantic debug mode.

### `ADEBUG-40`
Compiler-only ownership/capability metadata need not exist in release runtime memory.

### `ADEBUG-41`
Partial moves may be represented at field granularity.

### `ADEBUG-42`
Physical struct layout need not equal semantic structure layout.

### `ADEBUG-43`
Observable layout contracts remain debuggable according to their physical representation.

### `ADEBUG-44`
Raw pointer inspection does not establish safe provenance.

### `ADEBUG-45`
Debug symbols are distinct from exported ABI symbols.

### `ADEBUG-46`
Stripping debug metadata does not resurrect dead code.

### `ADEBUG-47`
Code folding preserves source-level identity where observable.

### `ADEBUG-48`
Hot/cold splitting preserves logical function identity.

### `ADEBUG-49`
Tail merging supports multiple source origins for one machine region.

### `ADEBUG-50`
Linker transformations must preserve required debug provenance.

### `ADEBUG-51`
Target debug formats are backend adapters to the Axiom debug model.

### `ADEBUG-52`
DWARF/PDB/dSYM/WASM debug representations are target-specific.

### `ADEBUG-53`
Runtime reflection and debug information remain separate mechanisms.

### `ADEBUG-54`
Crash artifacts identify the exact executable build.

### `ADEBUG-55`
Debug artifacts may be separated from production binaries.

### `ADEBUG-56`
Release builds may strip or redact debug metadata.

### `ADEBUG-57`
Debug metadata must not force unnecessary runtime allocation or object headers.

### `ADEBUG-58`
Semantic debugging can expose compiler reasoning without changing execution semantics.

### `ADEBUG-59`
Optimization provenance can explain why a source value or operation disappeared.

### `ADEBUG-60`
AI tooling may consume structured debug provenance.

### `ADEBUG-61`
Debugger behavior must distinguish semantic values from raw machine memory.

### `ADEBUG-62`
Debugger must not fabricate unavailable optimized state.

### `ADEBUG-63`
Compiler and debugger must preserve source identity through abstraction erasure where practical.

### `ADEBUG-64`
Debugging must remain compatible with freestanding/runtime-free programs where target support permits.

### `ADEBUG-65`
Debug metadata generation is deterministic under reproducible builds.

### `ADEBUG-66`
Debug information must not weaken safety verification.

### `ADEBUG-67`
Unsafe/FFI state may expose only information actually available from target/debug contracts.

### `ADEBUG-68`
Comptime-generated code may retain generator provenance without implying runtime existence.

### `ADEBUG-69`
Debugging infrastructure is optional and is not a mandatory production runtime component.

### `ADEBUG-70`
Axiom debugging observes the semantic program model rather than imposing a physical storage model.

---

# Kiến trúc Axiom sau BOOTSTRAP-160

Hiện tại compiler đã có một vòng khép kín khá mạnh:

```text
                  SOURCE
                     │
                     ▼
                   HIR
                     │
                     ▼
                   MIR
                     │
                     ▼
               VERIFICATION
                     │
                     ▼
                VERIFIED MIR
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
       Alias       Effect     Escape
          │          │          │
          └──────┬───┴──────┬───┘
                 ▼          ▼
             SSA/MemorySSA
                 │
                 ▼
                OptIR
                 │
        ┌────────┼───────────┐
        ▼        ▼           ▼
     Inline   Vectorize    Layout
        │        │           │
        └────────┼───────────┘
                 ▼
               LTO
                 │
                 ▼
             ABI MIR
                 │
                 ▼
                LIR
                 │
                 ▼
              MACHINE
                 │
                 ▼
               OBJECT
                 │
                 ▼
               LINKER
                 │
                 ▼
             EXECUTABLE
```

và song song với toàn bộ pipeline:

```text
Source
  ↕
HIR
  ↕
MIR
  ↕
OptIR
  ↕
LIR
  ↕
Machine
```

đều có **provenance/debug information**.

Đây là nền rất tốt để Axiom đạt mục tiêu khó nhất: **compiler được phép tối ưu cực mạnh mà programmer vẫn có thể hiểu chuyện gì đã xảy ra.**

---

# BOOTSTRAP-161 — Security Model, Unsafe Boundary, Constant-Time & Memory Safety Hardening

Bước tiếp theo nên khóa **security architecture**.

Không chỉ memory safety, mà phải xác định rõ:

```text
safe code
unsafe code
FFI
raw memory
integer overflow
pointer provenance
uninitialized memory
constant-time
side channels
secret data
zeroization
sandbox
capability security
```

Đặc biệt cần giải quyết một câu hỏi quan trọng cho Axiom:

> **Làm thế nào để Axiom vừa cho phép programmer viết low-level code gần như C/ASM, vừa khiến safe code có memory safety/data-race safety mạnh mà không cần GC, borrow-checker syntax hay programmer-written lifetime?**