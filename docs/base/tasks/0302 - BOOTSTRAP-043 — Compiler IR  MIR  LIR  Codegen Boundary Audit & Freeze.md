Tiếp tục.

# BOOTSTRAP-043 — Compiler IR / MIR / LIR / Codegen Boundary Audit & Freeze

Đây là một trong những module quan trọng nhất của Axiom.

Mục tiêu không chỉ là “có compiler”, mà là tạo kiến trúc cho phép:

- compiler nhanh;
- incremental compilation;
- tối ưu mạnh;
- binary nhỏ;
- debug tốt;
- GPU/CPU dùng chung frontend;
- eventual self-hosting;
- không phụ thuộc LLVM trong final architecture;
- vẫn có thể dùng LLVM trong giai đoạn bootstrap nếu cần.

Nguyên tắc trung tâm:

> **Mỗi IR chỉ nên biểu diễn những semantic mà tầng đó thực sự cần biết.**

Không để MIR chứa target-specific machine details.  
Không để backend phải hiểu ownership/type system.  
Không để source-level abstraction sống xuống machine code nếu nó không có observable semantics.

---

# 1. Pipeline chính

Pipeline được freeze thành:

```text
Source
  ↓
Lexer
  ↓
Parser
  ↓
AST
  ↓
Resolver
  ↓
HIR
  ↓
Typed HIR
  ↓
Closure / Async / Pattern analysis
  ↓
MIR
  ↓
Ownership / Capability / Concurrency verification
  ↓
Drop elaboration
  ↓
Verified MIR
  ↓
Semantic Optimization
  ↓
Representation / Layout
  ↓
ABI Lowering
  ↓
ABI MIR
  ↓
Axiom LIR
  ↓
Machine IR
  ↓
Machine Optimization
  ↓
Register Allocation
  ↓
Spill / Reload
  ↓
Final Machine IR
  ↓
Machine Encoder
  ↓
Object Writer
  ↓
Linker
  ↓
Executable / Library / WASM / GPU Artifact
```

Đây là **semantic compiler pipeline**, không nhất thiết mỗi mũi tên tương ứng một pass duy nhất.

---

# 2. AST

AST phản ánh syntax gần source:

```text
if
match
struct
fn
trait
impl
...
```

AST không phải IR tối ưu.

Nó giữ:

- source locations;
- comments/doc metadata cần thiết;
- syntax structure;
- diagnostics context.

---

# 3. AST không chứa semantic ownership hoàn chỉnh

Ví dụ:

```axiom
let x = foo()
```

AST chỉ biết:

```text
let
  pattern = x
  initializer = call foo
```

Ownership chưa được quyết định đầy đủ.

---

# 4. Resolver

Resolver xác định:

```text
name → declaration
module → module
import → symbol
type name → type declaration
trait → trait
```

Sau resolver, identifier không còn phụ thuộc vào string lookup đơn giản.

---

# 5. HIR

HIR loại bỏ nhiều syntax sugar.

Ví dụ:

```axiom
v.length()
```

được normalize thành semantic method call tương đương:

```text
length(v)
```

nhưng vẫn giữ source mapping.

---

# 6. HIR phải giữ semantic abstraction

HIR vẫn biết:

```text
Trait
Generic
Closure
Async
Pattern
Ownership intent
```

Chưa hạ xuống machine representation.

---

# 7. Typed HIR

Sau type checking:

```text
foo(x)
```

đã có:

```text
foo = FunctionId
x = TypeId
result = TypeId
generic substitutions
trait resolution
```

Không cần backend tự resolve lại.

---

# 8. Type identity

Compiler nên sử dụng stable internal IDs:

```text
TypeId
DefId
ModuleId
FunctionId
TraitId
FieldId
GenericId
```

Không dùng tên string làm identity.

---

# 9. Interning

Compiler có thể intern:

```text
types
symbols
paths
generic substitutions
constants
```

để giảm memory và tăng tốc compiler.

---

# 10. Generic representation

Ví dụ:

```axiom
fn max<T: Ord>(a: T, b: T) -> T
```

Typed HIR giữ:

```text
FunctionId
T
TraitConstraint Ord<T>
```

Chưa monomorphize.

---

# 11. Trait resolution

Trait solver chạy trước hoặc trong quá trình MIR lowering tùy dependency.

Sau khi một operation cần concrete implementation:

```text
Ord<T>::compare
```

compiler phải có resolved candidate.

Backend không nên biết trait solver.

---

# 12. Closure lowering

Closure:

```axiom
|x| x + captured
```

được biến thành compiler-generated environment:

```text
ClosureEnv {
    captured: ...
}
```

và callable representation.

---

# 13. Closure vẫn chưa cần heap

HIR/MIR chỉ biểu diễn:

```text
closure value
capture fields
call
```

Storage placement để optimizer/backend quyết định.

---

# 14. Async lowering

```axiom
async fn foo() -> T
```

được hạ thành Future/state machine.

Ví dụ conceptually:

```text
FutureFoo {
    state
    local_a
    local_b
}
```

Chỉ giữ locals sống qua suspension.

---

# 15. Async lowering trước MIR

Để MIR không phải hiểu một “async language”.

Pipeline:

```text
Typed HIR
   ↓
Async lowering
   ↓
ordinary control flow
   ↓
MIR
```

---

# 16. Pattern lowering

```axiom
match x {
    Some(v) => ...
    None => ...
}
```

được chuyển thành decision tree/CFG.

MIR không cần hiểu pattern syntax.

---

# 17. MIR là semantic center

Đây là quyết định quan trọng:

> **MIR là representation trung tâm của Axiom compiler.**

MIR đủ cao để còn hiểu:

- ownership;
- capabilities;
- Drop;
- Result control flow;
- async state;
- concurrency;
- allocation semantics.

Nhưng đủ thấp để compiler optimization hoạt động hiệu quả.

---

# 18. MIR không phụ thuộc target

MIR không chứa:

```text
x86 register
ARM instruction
GPU register
stack slot number
```

---

# 19. MIR không chứa physical pointer layout mặc định

MIR có thể biểu diễn:

```text
AddressOf
Load
Store
```

nhưng representation/provenance vẫn ở semantic level.

---

# 20. MIR operations

MIR cần một instruction set tương đối nhỏ:

```text
CONST
COPY
MOVE
BORROW_VIEW
BORROW_MUT_VIEW
LOAD
STORE
CAST
BITCAST
CALL
RETURN
BRANCH
SWITCH
PHI/MERGE
ALLOC
DEALLOC
DROP
PANIC
TRAP
ATOMIC
VOLATILE
```

Tên chính thức có thể khác, nhưng semantic categories này cần tồn tại.

---

# 21. SSA hay mutable MIR?

Không nên ép MIR phải SSA thuần từ đầu.

Tôi đề xuất:

> **MIR là CFG + SSA-compatible value model, nhưng có explicit local/storage places.**

Tức có:

```text
Local
Place
Projection
Value
```

---

# 22. Place model

Ví dụ:

```axiom
x.field[i]
```

có thể biểu diễn:

```text
Place(
    base = x,
    projections = [
        Field(field),
        Index(i)
    ]
)
```

---

# 23. Tại sao cần Place?

Ownership/capability verifier cần biết:

```text
x
x.field
x.field[i]
```

là những vùng khác nhau.

Nếu MIR chỉ có SSA values, việc theo dõi partial move/drop/alias sẽ khó hơn.

---

# 24. Place và Region

MIR có thể associate:

```text
Place
   ↓
Region
```

để capability analysis biết:

```text
x.a
```

và:

```text
x.b
```

có thể DISJOINT.

---

# 25. Local states

Compiler nội bộ theo dõi:

```text
UNINIT
INIT
MOVED
PARTIALLY_MOVED
DROPPED
```

đã được thiết kế từ representation/ownership model.

---

# 26. Capability states

MIR verifier theo dõi:

```text
READ
WRITE
MOVE
DROP
```

cùng:

```text
provenance
region
validity
```

---

# 27. Ownership verification không nằm ở backend

Backend không cần biết:

```text
"đây là move vì ownership"
```

Backend chỉ nhận MIR đã verified.

---

# 28. Drop elaboration

Source:

```axiom
fn foo() {
    let x = Resource(...)
    return
}
```

MIR trước drop:

```text
x = Resource()
return
```

Sau drop elaboration:

```text
x = Resource()
drop(x)
return
```

---

# 29. Drop elaboration trước optimization

Compiler phải biến cleanup thành explicit semantic CFG.

Sau đó optimizer mới được phép eliminate/reorder khi semantics cho phép.

---

# 30. Drop flags

Partial move cần internal drop state.

Ví dụ:

```axiom
let x = Struct {
    a: A,
    b: B
}

let y = x.a
```

Compiler biết:

```text
a = moved
b = live
```

Drop(x) chỉ drop `b`.

---

# 31. User-defined Drop

Nếu type có custom Drop:

```text
partial move
```

bị hạn chế như baseline đã freeze.

MIR verifier enforce.

---

# 32. Verified MIR

Đây là boundary rất quan trọng.

Sau:

```text
Ownership
Capability
Drop
Concurrency
Pattern
Async
GPU legality
```

compiler tạo:

```text
Verified MIR
```

---

# 33. Ý nghĩa Verified MIR

Từ thời điểm này:

> Backend không còn chịu trách nhiệm chứng minh high-level safety invariants.

Backend chỉ cần bảo toàn semantics.

---

# 34. Không “unsafe MIR”

Unsafe source có thể tạo:

```text
raw pointer
```

nhưng MIR vẫn phải encode explicit unsafe operation.

Unsafe không có nghĩa compiler biến MIR thành unchecked machine soup.

---

# 35. Semantic Optimization

Sau Verified MIR:

```text
inlining
constant propagation
dead code elimination
scalar replacement
copy propagation
CSE
loop optimization
bounds-check elimination
allocation elimination
```

---

# 36. Ownership optimization

Ví dụ:

```text
move x
```

không nhất thiết tạo physical copy.

Optimizer có thể chuyển ownership state mà không generate instruction.

---

# 37. Copy optimization

```text
Copy<T>
```

có thể:

```text
register move
load/store
memcpy
nothing
```

tùy context.

---

# 38. Drop elimination

Nếu compiler chứng minh resource:

```text
never initialized
```

không cần drop.

Nếu resource đã được transferred/moved:

```text
drop
```

được eliminate tương ứng.

---

# 39. Allocation elimination

Ví dụ:

```axiom
fn foo() -> Box<Point> {
    let p = Box::new(Point(...))
    return p
}
```

không nhất thiết:

```text
malloc
```

Compiler có thể caller-allocate hoặc scalarize nếu address semantics không observable.

---

# 40. Observable address

Nếu:

```axiom
let p = address_of(x)
```

và address trở thành observable:

```text
storage identity
```

không còn được tùy tiện eliminate/move.

Đúng với AMEM-55.

---

# 41. Alias optimization

Compiler có thể tận dụng:

```text
mut_view<T>
```

exclusive semantics để vectorize.

Không cần programmer viết:

```text
restrict
```

---

# 42. Bounds-check elimination

Ví dụ:

```axiom
for i in 0..n {
    out[i] = ...
}
```

nếu compiler chứng minh:

```text
i < out.len
```

thì check biến mất.

---

# 43. Safe code không đồng nghĩa slow code

Đây là mục tiêu lớn:

```text
safe abstraction
       ↓
semantic proof
       ↓
machine-level optimization
       ↓
zero unnecessary runtime cost
```

---

# 44. Representation phase

Sau semantic optimization mới quyết định:

```text
struct layout
enum layout
field offsets
alignment
niche
scalarization
aggregate representation
```

---

# 45. Tại sao layout sau optimization?

Vì compiler có thể phát hiện:

```text
struct chỉ được dùng như hai scalar
```

và không cần materialize toàn bộ struct.

---

# 46. ABI lowering

Sau layout:

```text
function arguments
return values
aggregate passing
calling convention
register classes
stack arguments
sret
varargs
```

được xác định.

---

# 47. ABI MIR

ABI MIR là boundary:

```text
semantic function
        ↓
target ABI function
```

Ví dụ:

```text
Result<T,E>
```

được hạ thành representation cụ thể cho target.

---

# 48. Axiom LIR

LIR thấp hơn MIR nhưng vẫn target-independent phần lớn.

Có thể chứa:

```text
integer operations
floating operations
memory operations
branches
calls
address calculations
atomic
vector operations
```

---

# 49. LIR không nên quá “generic”

Nếu LIR quá cao:

```text
backend phải làm quá nhiều semantic lowering
```

Nếu quá thấp:

```text
Mỗi target phải có một compiler frontend gần như riêng.
```

Mục tiêu:

> **LIR là common machine-oriented representation, nhưng vẫn giữ target-independent semantics khi có thể.**

---

# 50. LIR type system

Không cần giữ toàn bộ Axiom type system.

Ví dụ:

```text
i32
i64
f32
f64
ptr
vector
aggregate
token
```

là đủ.

---

# 51. Trait biến mất

Sau monomorphization:

```axiom
T: Add
```

thành concrete operation/function.

Backend không cần biết Trait.

---

# 52. Generic biến mất

Ví dụ:

```text
max<i32>
max<f64>
```

là các concrete instances.

---

# 53. Closure abstraction biến mất

Closure environment trở thành aggregate/struct-like machine data.

---

# 54. Async abstraction biến mất

Future state machine trở thành:

```text
state field
switch
storage
calls
```

Backend không cần biết `async`.

---

# 55. GPU abstraction

GPU path:

```text
Verified MIR
     ↓
GPU LIR
```

thay vì CPU LIR.

Nhưng frontend/semantic verification dùng chung.

---

# 56. GPU LIR

GPU LIR cần thêm:

```text
address spaces
barriers
GPU atomics
lane/group operations
special registers
kernel entry
```

---

# 57. CPU LIR

CPU LIR cần:

```text
atomic ordering
vector
SIMD
memory
calls
branches
```

---

# 58. Machine IR

Machine IR target-specific:

```text
X86MachineIR
ARM64MachineIR
RISCVMachineIR
WasmIR
GPUBackendIR
```

hoặc generic structure với target-specific opcode tables.

---

# 59. Machine IR cần register classes

Ví dụ x86:

```text
GPR
XMM
YMM
ZMM
FLAGS
```

ARM:

```text
GPR
FP/SIMD
NZCV
```

---

# 60. Register allocation

Machine IR trước register allocation có:

```text
virtual registers
```

Sau:

```text
physical registers
```

---

# 61. Register allocator

MVP:

```text
linear scan
```

sau:

```text
graph coloring / PBQP / hybrid
```

Không cần quyết định thuật toán tối ưu nhất ngay.

---

# 62. Spill/reload

Register pressure:

```text
virtual reg
    ↓
stack slot
```

Compiler insert:

```text
spill
reload
```

sau allocation.

---

# 63. Stack frame

Stack frame layout chỉ xuất hiện ở machine/backend stage.

Không nên để source-level semantics phụ thuộc stack.

---

# 64. Tail call

Nếu ABI/target cho phép:

```text
call
return
```

có thể lower thành tail jump.

---

# 65. Calling convention

Machine backend phải biết:

```text
Axiom ABI
C ABI
System ABI
GPU ABI
```

nhưng semantic frontend không.

---

# 66. Instruction selection

LIR:

```text
a + b
```

có thể thành:

```text
ADD
LEA
vector add
fused operation
```

tùy target/context.

---

# 67. Machine peephole optimization

Sau instruction selection:

```text
redundant move
dead instruction
branch folding
addressing mode fusion
```

---

# 68. Target feature

`@target_feature` và build configuration cung cấp:

```text
AVX2
AVX512
NEON
SVE
AES
...
```

Backend có thể specialize.

---

# 69. CPU dispatch

Nếu cần runtime CPU dispatch:

```text
baseline
+
specialized variant
```

đây là library/runtime/system layer.

Không làm target feature thành dynamic magic.

---

# 70. Vectorization

Compiler có thể vectorize:

```text
for
```

khi alias/capability semantics cho phép.

Đây là một trong những lợi ích lớn của ownership/capability model.

---

# 71. No source-level restrict

Axiom không cần:

```text
restrict
```

trong Core v1.

Compiler có thể biết:

```text
mut_view exclusive
```

mà không thêm syntax C-style.

---

# 72. Memory ordering preservation

Optimizer không được reorder atomic/volatile operations phá memory model.

Ví dụ:

```text
Release
Acquire
```

phải giữ happens-before semantics.

---

# 73. FFI barrier

Foreign call có conservative memory effects.

Compiler không được tự ý move memory operation qua foreign call nếu điều đó thay đổi semantics.

---

# 74. Pure function optimization

Không thêm `@pure` vào Core v1.

Compiler chỉ coi function side-effect-free nếu semantics/proof nội bộ cho phép.

---

# 75. `const`/comptime

Comptime evaluation diễn ra trước runtime IR.

Nếu value được materialize:

```text
comptime
   ↓
constant
   ↓
MIR CONST
```

---

# 76. Compile-time reflection

Reflection disappears sau compile.

Không cần runtime metadata trừ khi programmer explicit yêu cầu.

---

# 77. Debug information

Mỗi IR cần source mapping:

```text
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

để debugger có thể:

```text
machine instruction
→ source line
→ variable
→ function
```

---

# 78. Optimized variable debug

Một variable có thể:

```text
register
stack
optimized away
split into pieces
```

Debug metadata phải biểu diễn location ranges.

---

# 79. Compiler diagnostics

Diagnostics xảy ra ở semantic stages:

```text
parse error
name error
type error
ownership error
capability error
concurrency error
comptime error
ABI error
GPU legality error
```

Mỗi lỗi có:

```text
ErrorCode
primary span
secondary spans
structured facts
suggestions
```

---

# 80. Compiler IR serialization

Để AI/compiler tooling mạnh, nên có optional:

```text
.axir
```

hoặc metadata representation.

Nhưng:

> **IR binary/text format không cần là stable public format trong v1.**

---

# 81. IR snapshots

Compiler test suite có thể snapshot:

```text
AST
HIR
MIR
LIR
Machine IR
```

giúp regression testing.

---

# 82. Deterministic IR

Cùng source + compiler/config:

```text
semantic IR
```

nên deterministic.

Parallel compilation không được randomize IR identity.

---

# 83. Stable IDs

Internal IDs không nhất thiết stable giữa compiler versions.

Nhưng trong một compilation session:

```text
DefId
TypeId
BlockId
ValueId
```

phải deterministic.

---

# 84. Incremental IR

Cache có thể lưu:

```text
typed HIR
MIR
monomorphized instances
object
```

nhưng chỉ khi fingerprint hợp lệ.

---

# 85. Separate semantic and target caches

Ví dụ:

```text
source
 ↓
Verified MIR
```

có thể reusable giữa:

```text
x86-64
ARM64
```

nếu target-independent.

Nhưng:

```text
Machine IR
```

không reusable cross-target.

---

# 86. Generic cache

Monomorphized:

```text
Vec<i32>
```

có thể cache riêng.

Thay đổi unrelated code không nên rebuild tất cả generic instances.

---

# 87. LTO

LTO hoạt động trên:

```text
Axiom LIR / optimized IR
```

không nhất thiết object-only.

Có thể có:

```text
module optimization
whole-program optimization
```

---

# 88. Thin LTO

Sau này có thể hỗ trợ incremental/parallel LTO.

Không cần freeze implementation.

---

# 89. Link-time optimization

Linker không nên phải hiểu Axiom ownership.

Tất cả high-level semantics đã biến mất trước đó.

---

# 90. Binary size

Để đạt mục tiêu binary nhỏ:

Compiler ưu tiên:

```text
dead code elimination
generic deduplication
function merging
constant folding
string/data dedup
section GC
runtime component elimination
```

---

# 91. Runtime elimination

Nếu không dùng:

```text
async
thread
GPU
reflection
panic unwind
```

thì những runtime component tương ứng không được link.

---

# 92. Static linking

Static executable có thể loại bỏ unused object sections.

---

# 93. Dynamic linking

Shared library boundary giữ symbol/API contract.

Compiler không được inline qua boundary nếu ABI/visibility không cho phép.

---

# 94. Linker GC

Object sections có thể:

```text
dead-strip
```

nếu target hỗ trợ.

---

# 95. Section model

Axiom object writer cần tạo:

```text
text
rodata
data
bss
tls
debug
relocations
metadata
```

tùy target.

---

# 96. Machine encoder

Mục tiêu eventual:

```text
Axiom Machine Encoder
```

có thể trực tiếp encode:

```text
x86-64
ARM64
RISC-V
```

không cần assembler bên ngoài.

---

# 97. Assembler dependency

Bootstrap có thể:

```text
Axiom → LLVM/assembler
```

nhưng final:

```text
Axiom → Machine Encoder
```

---

# 98. Object writer

Tương tự:

```text
Axiom → ELF writer
Axiom → PE/COFF writer
Axiom → Mach-O writer
Axiom → WASM writer
```

---

# 99. Linker

Cuối cùng:

```text
Object files
    ↓
symbol resolution
    ↓
relocation
    ↓
section layout
    ↓
import/export
    ↓
TLS
    ↓
entry point
    ↓
native executable
```

Axiom có thể tự làm.

---

# 100. Self-hosting architecture

Điểm cuối cùng của pipeline:

```text
Axiom source
      ↓
Axiom compiler written in Axiom
      ↓
Axiom MIR
      ↓
Axiom LIR
      ↓
Axiom machine backend
      ↓
Axiom object writer
      ↓
Axiom linker
      ↓
Axiom compiler executable
```

Compiler không còn cần C++/Rust/LLVM để tồn tại.

---

# 101. Compiler bootstrap stages

Tôi đề xuất 4 stage:

### Stage 0

```text
Prototype compiler
```

Có thể dùng:

```text
Rust/C++/Python
```

để validate language.

### Stage 1

```text
Axiom frontend
+
external backend
```

Có thể dùng LLVM tạm thời.

### Stage 2

```text
Axiom frontend
+
Axiom MIR
+
Axiom LIR
+
Axiom machine backend
```

### Stage 3

```text
Axiom compiler
written in Axiom
```

### Stage 4

```text
Axiom compiler
+
Axiom linker
+
Axiom object writer
+
Axiom package manager
```

self-contained.

---

# 102. Không khóa Axiom vào LLVM

Đây là quyết định quan trọng.

LLVM có thể là:

```text
bootstrap backend
```

nhưng **không phải semantic foundation**.

Nếu sau này bỏ LLVM:

```text
HIR
MIR
semantic optimizer
```

không cần thiết kế lại.

---

# 103. Không khóa Axiom vào Cranelift

Tương tự.

Các backend external chỉ là implementation options.

---

# 104. Compiler architecture cuối

```text
              Axiom Source
                    │
                 Frontend
                    │
               Typed HIR
                    │
          ┌─────────┴─────────┐
          │ Semantic Analysis │
          └─────────┬─────────┘
                    │
                   MIR
                    │
        ┌───────────┼───────────┐
        │           │           │
      CPU          GPU        WASM
        │           │           │
       LIR         GLIR        WLIR
        │           │           │
     Machine      GPU IR      WASM
        │
  Register Allocation
        │
   Machine Encoder
        │
     Object Writer
        │
       Linker
```

---

# 105. Invariants — BOOTSTRAP-043

```text
AIR-20   AST represents source syntax, not machine representation.
AIR-21   Resolver establishes semantic symbol identity.
AIR-22   HIR removes selected syntax sugar while preserving semantics.
AIR-23   Typed HIR contains resolved type information.
AIR-24   Type identity is represented by compiler identities, not strings.
AIR-25   Generic definitions remain generic until monomorphization.
AIR-26   Trait resolution occurs before backend lowering requires concrete behavior.
AIR-27   Closure lowering produces explicit capture state.
AIR-28   Closure lowering does not imply heap allocation.
AIR-29   Async lowering produces an explicit state machine.
AIR-30   Async lowering does not require backend knowledge of async syntax.
AIR-31   Pattern lowering produces explicit control flow.
AIR-32   MIR is the central semantic compiler representation.
AIR-33   MIR is target-independent.
AIR-34   MIR represents ownership-relevant storage places.
AIR-35   MIR places preserve field/index projections.
AIR-36   MIR supports region/capability analysis.
AIR-37   MIR explicitly represents semantic moves.
AIR-38   MIR explicitly represents semantic copies where required.
AIR-39   MIR explicitly represents Drop operations after drop elaboration.
AIR-40   Moved values are never implicitly dropped.
AIR-41   Partial moves are represented explicitly.
AIR-42   Custom Drop restrictions are enforced before backend lowering.
AIR-43   Ownership verification occurs before unsafe backend optimization.
AIR-44   Capability verification occurs before semantic optimization.
AIR-45   Concurrency verification occurs before backend lowering.
AIR-46   GPU legality is verified before GPU backend lowering.
AIR-47   Verified MIR is the boundary after high-level safety verification.
AIR-48   Backend code generation does not reimplement ownership semantics.
AIR-49   Unsafe source operations remain explicit in IR semantics.
AIR-50   Unsafe does not disable unrelated compiler verification.
AIR-51   Semantic optimization occurs before target-specific lowering.
AIR-52   Optimization cannot alter observable Axiom semantics.
AIR-53   Move does not imply physical copying.
AIR-54   Copy does not require a physical memory copy.
AIR-55   Drop elimination is permitted when semantics prove it unnecessary.
AIR-56   Allocation elimination is permitted when storage identity is unobservable.
AIR-57   Observable addresses constrain storage optimization.
AIR-58   Safe alias guarantees may enable vectorization.
AIR-59   Bounds checks may be eliminated only when safety is proven.
AIR-60   Representation lowering is distinct from semantic type checking.
AIR-61   Struct layout is determined after semantic analysis.
AIR-62   Enum representation is determined after semantic analysis.
AIR-63   ABI lowering occurs after representation analysis.
AIR-64   ABI MIR contains target ABI decisions.
AIR-65   Axiom LIR is lower than MIR and higher than target machine IR.
AIR-66   LIR does not require the full Axiom type system.
AIR-67   Traits do not survive into machine IR unless runtime representation is explicitly required.
AIR-68   Generic abstractions are erased or specialized before machine code.
AIR-69   Closure abstractions are lowered before machine code.
AIR-70   Async abstractions are lowered before machine code.
AIR-71   GPU abstractions may lower into GPU-specific LIR.
AIR-72   CPU and GPU share semantic verification where applicable.
AIR-73   Machine IR is target-specific.
AIR-74   Register allocation operates on machine-oriented IR.
AIR-75   Spill/reload insertion occurs after or during register allocation.
AIR-76   Calling conventions are enforced by ABI lowering/backend.
AIR-77   Foreign calls retain conservative memory effects unless contracted.
AIR-78   Atomic ordering cannot be invalidated by optimization.
AIR-79   Volatile semantics cannot be optimized away incorrectly.
AIR-80   FFI boundaries constrain legal optimization.
AIR-81   Debug information preserves source-to-machine mappings.
AIR-82   Optimized variables may have fragmented or absent machine locations.
AIR-83   IR identities are deterministic within a compilation session.
AIR-84   IR snapshots may be used for compiler regression testing.
AIR-85   Incremental caches use semantic fingerprints.
AIR-86   Target-independent IR may be reused across compatible targets.
AIR-87   Machine IR is not generally cross-target reusable.
AIR-88   Generic instances may be independently cached.
AIR-89   Comptime results may be independently cached.
AIR-90   LTO operates only after semantic verification.
AIR-91   Link-time optimization cannot invalidate ABI contracts.
AIR-92   Runtime components may be eliminated when semantically unused.
AIR-93   Binary size is not determined by source abstraction count.
AIR-94   Zero-cost abstractions may disappear before machine code.
AIR-95   Object generation is distinct from linking.
AIR-96   Object formats are target-specific.
AIR-97   Machine encoding is target-specific.
AIR-98   Axiom may eventually implement its own machine encoders.
AIR-99   Axiom may eventually implement its own object writers.
AIR-100  Axiom may eventually implement its own linker.
AIR-101  External compiler backends are bootstrap implementation choices, not language semantics.
AIR-102  LLVM is not a required semantic dependency of Axiom.
AIR-103  External assemblers are not required by the final compiler architecture.
AIR-104  External linkers are not required by the final compiler architecture.
AIR-105  Self-hosting does not require changing Axiom semantics.
AIR-106  Compiler implementation may initially be written in another language.
AIR-107  The final compiler may be implemented entirely in Axiom.
AIR-108  Compiler correctness is preserved across backend replacement.
AIR-109  Backend replacement does not require changing source language semantics.
AIR-110  Every lower IR must preserve the observable semantics of its input IR.
```

---

# Một điểm tôi muốn nhấn mạnh

Kiến trúc này giải quyết trực tiếp mục tiêu trước đây của bạn:

> **“hiệu năng bằng hoặc hơn C/C++, kích thước nhỏ gọn như ASM.”**

Không nên cố đạt điều đó bằng cách làm syntax thấp cấp như ASM.

Axiom đi theo hướng ngược lại:

```text
Axiom high-level
      ↓
compiler biết ownership/capability
      ↓
compiler biết aliasing
      ↓
compiler biết lifetime
      ↓
compiler biết allocation có observable hay không
      ↓
compiler biết generic/closure/async có thể erase
      ↓
Verified MIR
      ↓
aggressive optimization
      ↓
machine code
```

Tức là **đẩy complexity từ programmer sang compiler**, đúng với triết lý đã thống nhất:

> **Compiler Complexity Is Not Language Complexity.**

Và đây cũng là lý do quyết định **không đưa borrow checker/lifetime syntax vào source language** vẫn hợp lý: compiler vẫn có thể thực hiện các phân tích tương tự ở MIR, nhưng programmer không phải viết:

```text
'a
'b
&'a T
&'b mut T
```

---

## Chuỗi kiến trúc tiếp theo

Sau khi đã freeze compiler IR, bước kế tiếp nên là:

**BOOTSTRAP-044 — Standard Library / Core Library Boundary**

Phần này cần quyết định rất kỹ **cái gì thuộc ngôn ngữ, cái gì thuộc standard library**, đặc biệt:

```text
Vec
String
HashMap
Box
Rc / Arc
Mutex / RwLock
Channel
Future
Executor
File
Socket
Thread
Process
Time
Random
Tensor
GPU Buffer
Collections
Iterator
```

Đây là chỗ rất dễ làm Axiom phình thành một “runtime khổng lồ”, nên cần freeze ranh giới **Core Language ↔ Core Library ↔ Standard Library ↔ Optional Runtime** trước khi bắt đầu thiết kế API cụ thể.