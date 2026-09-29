# BOOTSTRAP-272 — AXIOM COMPILER BOOTSTRAP & SELF-HOSTING IMPLEMENTATION ARCHITECTURE

**TRẠNG THÁI: FROZEN / COMPLETED**

Task này chuyển Axiom từ trạng thái **specification hoàn chỉnh** sang **kế hoạch implementation compiler thực tế**.

Mục tiêu không phải viết ngay toàn bộ compiler, mà khóa một bootstrap architecture sao cho:

1. Compiler đầu tiên có thể xây dựng được.
2. Không khóa Axiom vào LLVM/Clang về lâu dài.
3. Có reference semantics để chống miscompilation.
4. Có thể incremental/parallel từ đầu.
5. Cuối cùng compiler tự biên dịch bằng Axiom.

---

# 1. Bootstrap principle

Axiom cuối cùng phải có:

```text
Axiom source
    ↓
Axiom compiler
    ↓
native object
    ↓
Axiom linker/object writer
    ↓
native executable
```

Nhưng compiler đầu tiên **không cần** được viết bằng Axiom.

Bootstrap:

```text
Stage 0
Host compiler implementation
        │
        ▼
Stage 1
Axiom compiler
        │
        ▼
Axiom compiler compiles Axiom compiler
        │
        ▼
Stage 2+
Self-hosted Axiom compiler
```

---

# 2. Không dùng LLVM làm semantic authority

Trong bootstrap có thể dùng LLVM/LLD nếu cần tăng tốc implementation.

Nhưng:

```text
Axiom semantics
        ≠
LLVM semantics
```

LLVM chỉ là backend bootstrap.

---

# 3. Bootstrap backend strategy

Giai đoạn đầu:

```text
Verified MIR
      ↓
Axiom LIR
      ↓
LLVM bridge
      ↓
LLVM IR
      ↓
LLVM backend
      ↓
object
```

Song song:

```text
Verified MIR
      ↓
Axiom LIR
      ↓
x86/ARM/RV64/WASM backend
```

Khi backend Axiom trưởng thành:

```text
LLVM bridge
      ↓
optional / bootstrap-only
```

có thể bỏ.

---

# 4. Bootstrap compiler implementation language

Khuyến nghị:

> **Rust làm bootstrap implementation language.**

Không phải vì Axiom phụ thuộc Rust, mà vì Rust phù hợp với:

- compiler implementation
- immutable/incremental structures
- concurrency
- parser
- type system
- LLVM interop
- cross-platform tooling
- memory safety trong chính compiler

---

# 5. Nhưng Rust không phải runtime dependency của Axiom

Sau self-hosting:

```text
Axiom compiler
```

không cần:

```text
Rust runtime
Rust standard library
Rust compiler
LLVM
```

để compile chương trình Axiom bình thường.

---

# 6. Repository

Đề xuất:

```text
axiom/
├── compiler/
│   ├── axc/
│   ├── lexer/
│   ├── syntax/
│   ├── parser/
│   ├── resolver/
│   ├── types/
│   ├── traits/
│   ├── hir/
│   ├── mir/
│   ├── verify/
│   ├── comptime/
│   ├── optimize/
│   ├── abi/
│   ├── lir/
│   ├── backend/
│   ├── object/
│   ├── linker/
│   ├── diagnostics/
│   ├── query/
│   └── db/
│
├── runtime/
│   ├── startup/
│   ├── panic/
│   ├── allocator/
│   ├── thread/
│   └── async/
│
├── std/
│
├── targets/
│   ├── x86_64/
│   ├── arm64/
│   ├── riscv64/
│   └── wasm/
│
├── tests/
│   ├── lexer/
│   ├── parser/
│   ├── semantic/
│   ├── ownership/
│   ├── traits/
│   ├── mir/
│   ├── codegen/
│   ├── abi/
│   ├── runtime/
│   └── conformance/
│
├── docs/
│   ├── design/
│   └── tasks/
│
└── _workspace/
```

---

# 7. Không chia repository theo “ngôn ngữ frontend/backend” quá sớm

Các module nên phản ánh **semantic boundary**, không phải framework đang dùng.

Ví dụ:

```text
query
syntax
semantic
mir
verify
opt
abi
backend
```

---

# 8. Executables

Bootstrap cần tối thiểu:

```text
ax
axc
ax-ref
ax-mir
```

Trong đó:

### `ax`

Build/package/user-facing CLI.

### `axc`

Compiler core.

### `ax-ref`

Reference interpreter.

### `ax-mir`

MIR interpreter/debugger.

Sau này có thể hợp nhất executable nhưng architecture vẫn giữ các logical components.

---

# 9. `ax-ref` cực kỳ quan trọng

Reference interpreter **không tối ưu**.

Nó ưu tiên:

```text
correctness
clarity
determinism
```

Không ưu tiên:

```text
speed
binary size
```

---

# 10. Reference semantics

Pipeline:

```text
Source
 ↓
AST/HIR
 ↓
Reference Semantic Evaluation
 ↓
Observable Result
```

Dùng làm oracle cho:

```text
MIR
Optimized MIR
Native
WASM
GPU
```

---

# 11. Example differential test

```text
program.ax
```

chạy:

```text
ax-ref program.ax
axc --debug program.ax
axc --release program.ax
axc --size program.ax
```

Tất cả phải có observable behavior tương đương.

---

# 12. MIR interpreter

`ax-mir` chạy:

```text
Verified MIR
```

không cần target machine.

Điều này cực kỳ hữu ích để kiểm tra:

```text
ownership
drop
capability
async lowering
effects
panic
Result
```

---

# 13. Compiler architecture implementation

```text
                  axc
                   │
             ┌─────┴─────┐
             ▼           ▼
         CompilerDB    Config
             │
             ▼
        Query Engine
             │
   ┌─────────┼─────────┐
   ▼         ▼         ▼
 Syntax   Semantic   Backend
   │         │         │
   ▼         ▼         ▼
 AST/HIR    MIR       LIR
             │
          Verify
             │
          Optimize
             │
            ABI
             │
          Codegen
```

---

# 14. `CompilerDB`

Implementation đầu tiên phải có các database chính:

```text
SourceDB
PackageDB
ModuleDB
SyntaxDB
DeclarationDB
TypeDB
TraitDB
ConstDB
GenericDB
ComptimeDB
HIRDB
MIRDB
DiagnosticDB
LayoutDB
AbiDB
CodegenDB
BuildDB
```

Không được chờ đến cuối mới thêm incremental query.

---

# 15. Query engine phải có từ ngày đầu

Nếu viết compiler kiểu:

```text
compile_everything()
```

rồi mới incremental hóa sau, rất dễ phải rewrite architecture.

Ngay bootstrap phải dùng:

```text
query(key)
```

---

# 16. Implementation phases

Không nên triển khai theo thứ tự:

```text
lexer
parser
type system
...
backend
```

một cách tuyệt đối.

Nên triển khai theo **vertical slices**.

---

# 17. Slice 1 — Hello World

Compiler tối thiểu:

```text
fn main() {
    ...
}
```

có thể:

```text
parse
→ resolve
→ MIR
→ native code
→ executable
```

---

# 18. Slice 2 — Integer

Hỗ trợ:

```text
let
i32
i64
u32
u64
+
-
*
/
return
```

---

# 19. Slice 3 — Control flow

```text
if
loop
while
break
continue
match
```

---

# 20. Slice 4 — Struct

```text
struct Point {
    x: i32
    y: i32
}
```

và:

```text
p.x
p.y
```

---

# 21. Slice 5 — Functions

```text
fn add(a: i32, b: i32) -> i32
```

bao gồm:

- argument passing
- return
- call
- ABI
- Drop cleanup.

---

# 22. Slice 6 — Ownership

Đây là điểm khác biệt quan trọng.

Ví dụ:

```text
let a = make_buffer()
let b = a
```

Compiler phải biết:

```text
a = Moved
b = Owned
```

---

# 23. Slice 7 — Drop

```text
struct File {
    ...
}
```

có Drop contract.

Compiler kiểm tra:

```text
exactly once
```

---

# 24. Slice 8 — view

```text
fn sum(x: view<i32>) -> i32
```

và:

```text
sum(array)
```

compiler tự tạo ephemeral view.

---

# 25. Slice 9 — mut_view

```text
fn sort(x: mut_view<i32>)
```

compiler phải kiểm tra capability conflict.

---

# 26. Slice 10 — enums

```text
enum Option<T> {
    Some(T)
    None
}
```

và exhaustive `match`.

---

# 27. Slice 11 — Result

```text
Result<T, E>
?
```

---

# 28. Slice 12 — generics

```text
fn max<T: Ord>(a: T, b: T) -> T
```

---

# 29. Slice 13 — traits

Implement:

```text
impl Ord for MyType
```

và trait solver.

---

# 30. Slice 14 — closures

```text
let f = |x| x + offset
```

Capture analysis.

---

# 31. Slice 15 — async

Không cần executor native ngay.

Compiler trước tiên phải lower:

```text
async fn
```

thành:

```text
Future state machine
```

và test bằng MIR interpreter.

---

# 32. Slice 16 — concurrency

Implement semantic checking trước runtime:

```text
Send
Share
Atomic
Mutex
Channel
```

---

# 33. Slice 17 — comptime

Trước tiên:

```text
const
comptime fn
comptime {}
```

với sandbox đơn giản.

---

# 34. Slice 18 — FFI

Đầu tiên:

```text
extern "C"
```

sau đó C-compatible layout.

---

# 35. Slice 19 — static/TLS

Theo task 255:

```text
const
static
TLS
```

---

# 36. Slice 20 — backend independence

Sau khi compiler có một backend hoạt động:

```text
x86-64
```

phải đưa vào:

```text
RV64
```

hoặc WASM để kiểm tra LIR.

Không nên chờ compiler hoàn thiện 100%.

---

# 37. Bootstrap backend đầu tiên

Khuyến nghị:

```text
x86-64
```

là priority 1 trên Windows/Linux.

Sau đó:

```text
ARM64
RV64
WASM
```

---

# 38. LLVM bridge

Trong bootstrap:

```text
Axiom LIR
   ↓
LLVM Adapter
   ↓
LLVM IR
```

Adapter phải nằm ngoài semantic core.

```text
compiler/backend/llvm/
```

---

# 39. LLVM không được xuất hiện trong CoreDB

Không để:

```text
TypeDB → LLVMType
```

Đúng:

```text
TypeDB
 ↓
LayoutDB
 ↓
AbiDB
 ↓
LIR
 ↓
LLVM Adapter
```

---

# 40. Vì sao?

Sau này bỏ LLVM:

```text
LLVM Adapter
```

là có thể xóa mà không phải sửa:

```text
ownership
types
traits
MIR
ABI semantics
```

---

# 41. Native backend transition

Giai đoạn:

```text
Bootstrap
    ↓
LLVM
```

sau đó:

```text
Axiom LIR
    ↓
Native TargetBackend
```

---

# 42. Compiler self-hosting milestone

Điểm mốc không phải:

> “Axiom compiler viết bằng Axiom.”

Mà phải là:

> **Axiom compiler được Axiom compiler hiện tại biên dịch thành công và binary mới có thể tự biên dịch lại chính compiler đó.**

---

# 43. Stage definitions

### Stage 0

```text
Rust axc
```

biên dịch Axiom.

### Stage 1

```text
Rust axc
→ Axiom compiler source
→ axc.ax binary
```

### Stage 2

```text
axc.ax
→ compile axc source
→ axc2
```

### Stage 3

```text
axc2
→ compile axc source
→ axc3
```

---

# 44. Bootstrap fixed-point test

Phải có:

```text
axc2 --build axc
→ axc3
```

Sau đó so sánh:

```text
axc2
axc3
```

theo semantic/codegen identity thích hợp.

---

# 45. Không yêu cầu byte-identical compiler binary

Self-hosting không nhất thiết:

```text
hash(axc2) == hash(axc3)
```

vì:

- timestamps/debug
- linker layout
- nondeterministic metadata nếu không khóa
- codegen version

Nhưng reproducible profile nên hướng tới binary reproducibility.

---

# 46. Bootstrap trust

Compiler bootstrap là trust boundary.

Phải có:

```text
reference semantics
+
conformance tests
+
differential tests
+
bootstrap comparison
```

---

# 47. Compiler correctness loop

```text
Specification
     ↓
Reference Interpreter
     ↓
Compiler
     ↓
MIR
     ↓
Native
     ↓
Differential Test
     ↓
Specification compliance
```

---

# 48. Optimizer validation

Mỗi pass:

```text
Input MIR
   ↓
Pass
   ↓
Output MIR
```

phải có validation:

```text
observable(Input)
==
observable(Output)
```

trong test model.

---

# 49. Debug compiler mode

Nên có:

```text
axc --verify-all
```

thực hiện:

```text
AST
HIR
MIR
Verified MIR
OptIR
ABI
LIR
MachineIR
Object
```

với verifier tương ứng.

---

# 50. Fast compiler mode

Release:

```text
axc --release
```

có thể bỏ một số expensive diagnostics nhưng **không bỏ semantic verifier cần thiết**.

---

# 51. `--unsafe-fast` không được trở thành compiler semantic bypass

Unsafe là source-level contract.

Compiler optimization level không thay đổi:

```text
ownership
capability
Drop
Send
Share
```

semantics.

---

# 52. Compiler testing hierarchy

```text
Unit
 ↓
Query
 ↓
Semantic
 ↓
MIR
 ↓
Verifier
 ↓
Optimization
 ↓
ABI
 ↓
Backend
 ↓
Object
 ↓
Executable
 ↓
Bootstrap
```

---

# 53. Golden source tests

Ví dụ:

```text
tests/semantic/move/
tests/semantic/drop/
tests/semantic/view/
tests/semantic/traits/
```

---

# 54. MIR golden tests

```text
source
→ MIR
```

Nhưng MIR golden không nên là semantic authority tuyệt đối vì compiler có thể thay đổi internal representation.

---

# 55. Semantic oracle vẫn là authority

Đã khóa ở task 188.

---

# 56. Compiler test command

Đề xuất:

```text
ax test
ax test --semantic
ax test --mir
ax test --backend
ax test --bootstrap
ax test --fuzz
```

---

# 57. Compiler fuzzing

Ngay từ đầu:

```text
lexer fuzz
parser fuzz
type fuzz
trait fuzz
MIR fuzz
ownership fuzz
```

---

# 58. Random valid program generator

Tạo chương trình hợp lệ:

```text
Generator
 ↓
ax-ref
 ↓
axc
 ↓
compare
```

---

# 59. Random invalid program generator

Tạo lỗi:

```text
use-after-move
double-drop
invalid-view
trait ambiguity
non-exhaustive match
```

Compiler phải:

```text
reject
```

và không crash.

---

# 60. Compiler crash != program rejection

Một program invalid vẫn phải tạo diagnostic bình thường.

Compiler crash là bug.

---

# 61. Diagnostics implementation

Structured diagnostic:

```text
Diagnostic {
    code
    severity
    primary_span
    secondary_spans
    message
    explanation
    fixes
    proof
}
```

---

# 62. Không format diagnostic bằng string ngay từ semantic layer

Không:

```text
return "cannot move value"
```

Mà:

```text
DiagnosticData::UseAfterMove {
    place
    move_location
    use_location
}
```

Formatter quyết định cách hiển thị.

---

# 63. Điều này cực kỳ quan trọng cho AI.

AI có thể nhận:

```text
code
spans
semantic facts
proof tree
suggested fixes
```

thay vì parse text compiler output.

---

# 64. Repository task system

Vì bạn muốn Antigravity tự động làm việc, compiler repo phải có:

```text
docs/tasks/
```

mỗi task:

```text
BOOTSTRAP-272.md
```

và trạng thái:

```text
DRAFT
DESIGNED
IMPLEMENTING
TESTING
FROZEN
```

---

# 65. Agent implementation loop

```text
Read task
 ↓
Read relevant spec
 ↓
Inspect repository
 ↓
Implement smallest vertical slice
 ↓
Run tests
 ↓
Run semantic/conformance tests
 ↓
Commit
 ↓
Update task
 ↓
Next task
```

---

# 66. Agent không được tự ý sửa frozen semantics

Nếu implementation gặp conflict:

```text
implementation
      ↕
frozen spec
```

spec thắng.

Agent phải tạo:

```text
DecisionRequired
```

thay vì âm thầm thay semantics.

---

# 67. Nhưng implementation detail không cần hỏi

Ví dụ:

```text
arena implementation
hash table implementation
thread pool implementation
```

agent tự chọn nếu không ảnh hưởng frozen contract.

---

# 68. NotebookLM

Trong workflow của bạn:

```text
Agent
 ↓
NotebookLM research
 ↓
Architecture evidence
 ↓
implementation
```

NotebookLM không phải semantic authority.

Nó chỉ cung cấp research evidence.

---

# 69. AI agent hierarchy

```text
Architect Agent
      │
      ├── Frontend Agent
      ├── Semantic Agent
      ├── MIR Agent
      ├── Verification Agent
      ├── Optimization Agent
      ├── Backend Agent
      ├── Runtime Agent
      └── Test Agent
```

---

# 70. Nhưng tất cả phải dùng chung:

```text
Axiom Spec
CompilerDB contracts
Task graph
Test oracle
```

---

# 71. Không cho mỗi agent tạo semantic interpretation riêng.

---

# 72. Agent completion criteria

Một task chỉ được:

```text
FROZEN
```

khi:

```text
implementation
+
tests
+
documentation
+
conformance
```

đạt.

---

# 73. Commit policy

Một semantic task:

```text
one logical commit
```

hoặc nhiều commit implementation nếu cần.

Nhưng task completion phải có commit reference.

---

# 74. Build bootstrap chain

```text
Stage 0 Rust axc
        │
        ▼
Axiom std bootstrap
        │
        ▼
Axiom compiler source
        │
        ▼
Axiom compiler executable
        │
        ▼
self compile
        │
        ▼
self-hosted compiler
```

---

# 75. Standard library bootstrap

Không được để compiler phụ thuộc circular:

```text
compiler
→ std
→ compiler
```

Compiler cần một:

```text
minimal compiler support library
```

tách biệt với full `std`.

---

# 76. `core`

Axiom nên có:

```text
core
```

chứa semantic/library primitives tối thiểu:

```text
Option
Result
Iterator
Copy
Clone
Drop
Send
Share
basic numeric traits
```

---

# 77. `std`

```text
std
```

mới cung cấp:

```text
IO
filesystem
network
thread
process
GUI
etc.
```

---

# 78. Compiler bootstrap core

Có thể cần:

```text
bootstrap-core
```

nhưng cuối cùng phải converge về Axiom `core`, tránh hai semantic universes.

---

# 79. No compiler-specific language extensions unless explicitly marked

Bootstrap compiler không được lén hỗ trợ:

```text
Rust-like syntax
special ownership syntax
hidden compiler keywords
```

rồi coi đó là Axiom.

Nếu compiler intrinsic cần thiết:

```text
@compiler_intrinsic
```

phải được đặc tả rõ.

---

# 80. Intrinsics

Intrinsic phải có:

```text
semantic definition
fallback
target requirements
verification contract
ABI contract
```

---

# 81. Example

```text
@intrinsic
fn cpu_cycle_counter() -> u64
```

không được có semantics chỉ:

> “LLVM instruction tương ứng.”

Phải định nghĩa observable semantics.

---

# 82. Bootstrap linker

Giai đoạn đầu:

```text
Axiom Object
 ↓
system linker / LLD
```

Sau đó:

```text
Axiom Object
 ↓
Axiom Linker
```

---

# 83. Bootstrap runtime

Runtime componentization đã khóa ở 196.

Compiler chỉ link component cần thiết:

```text
main
+
allocator
+
panic
```

không tự link:

```text
network
async
GUI
reflection
```

---

# 84. Minimal Hello World

Mục tiêu binary:

```text
main
startup
OS write
exit
```

không kéo cả runtime.

---

# 85. Freestanding bootstrap

Sau hosted native compiler:

```text
@freestanding
```

phải có khả năng compile chương trình không dùng OS runtime.

---

# 86. Kernel/embedded

Không cần compiler riêng.

Chỉ:

```text
TargetSpec
RuntimeProfile = Freestanding
```

---

# 87. WASM bootstrap

```text
Axiom
 ↓
Verified MIR
 ↓
WASM backend
 ↓
.wasm
```

không cần JS runtime nếu target environment không yêu cầu.

---

# 88. Compiler package graph

Compiler itself cuối cùng là Axiom package:

```text
axiom-compiler
 ├── axiom-core
 ├── axiom-syntax
 ├── axiom-semantic
 ├── axiom-mir
 ├── axiom-codegen
 └── axiom-cli
```

---

# 89. Nhưng package boundaries không được trở thành runtime boundaries.

Compiler có thể static-link/inline/merge toàn bộ.

---

# 90. Compiler binary size

Không phải mục tiêu số 1.

Ưu tiên:

```text
correctness
maintainability
compile speed
```

sau đó:

```text
compiler binary size
```

Ngôn ngữ sinh binary nhỏ là mục tiêu riêng.

---

# 91. Bootstrap milestone map

```text
M0  Repository
M1  Lexer
M2  Parser
M3  Resolver
M4  Type system
M5  HIR
M6  MIR
M7  Reference interpreter
M8  Ownership verifier
M9  x86 backend
M10 Native executable
M11 Struct/enum/generic
M12 Traits
M13 Closures
M14 Async
M15 Concurrency
M16 Comptime
M17 FFI
M18 RV64
M19 WASM
M20 Axiom linker
M21 Axiom runtime composition
M22 Axiom std
M23 Compiler self-build
M24 Self-host
```

---

# 92. Self-hosting không phải điểm kết thúc

Sau self-host:

```text
Axiom compiler
```

có thể tự cải tiến:

```text
compiler written in Axiom
        ↓
Axiom compiler
        ↓
better compiler
```

---

# 93. Từ đó bootstrap trust có thể dùng diverse compiler strategy

Ví dụ:

```text
Reference
Rust bootstrap
Axiom self-host
```

so sánh semantic output.

---

# 94. Compiler diversity test

Nếu:

```text
Rust axc
```

và:

```text
Axiom axc
```

compile cùng source và tạo MIR semantics khác nhau:

```text
conformance failure
```

---

# 95. Compiler correctness architecture

```text
             Axiom Specification
                     │
                     ▼
              Reference Model
                     │
            ┌────────┴────────┐
            ▼                 ▼
       Rust Compiler     Axiom Compiler
            │                 │
            ▼                 ▼
           MIR               MIR
            │                 │
            └────────┬────────┘
                     ▼
              Semantic Compare
```

---

# 96. Đây là architecture phù hợp với mục tiêu ban đầu của Axiom:

Không chỉ:

> “viết một compiler nhanh.”

Mà:

> **xây một compiler có thể tự kiểm chứng, incremental, target-independent và cuối cùng tự host.**

---

# 97. Invariants mới

```text
ABOOT-20
The bootstrap compiler must implement the frozen Axiom semantic specification.

ABOOT-21
Bootstrap implementation language is an implementation detail, not a language dependency.

ABOOT-22
Rust bootstrap dependencies must not become mandatory runtime dependencies of Axiom programs.

ABOOT-23
LLVM may be used as a bootstrap backend but is not a semantic authority.

ABOOT-24
Frontend and semantic layers must not depend on LLVM-specific representations.

ABOOT-25
Axiom LIR must remain the compiler backend abstraction boundary.

ABOOT-26
The reference interpreter defines observable semantic behavior for conformance testing.

ABOOT-27
The MIR interpreter must execute Verified MIR according to Axiom semantics.

ABOOT-28
Compiler optimization must be validated against semantic behavior.

ABOOT-29
Compiler crashes are implementation failures, not valid program diagnostics.

ABOOT-30
Invalid programs must produce structured diagnostics rather than compiler crashes whenever recovery is possible.

ABOOT-31
Compiler semantic queries must use CompilerDB.

ABOOT-32
Incremental query architecture must exist from bootstrap rather than being retrofitted later.

ABOOT-33
Compiler implementation details must not introduce undocumented language semantics.

ABOOT-34
Bootstrap-only intrinsics must have explicit semantic contracts.

ABOOT-35
Bootstrap-only extensions must be clearly isolated from Axiom Core.

ABOOT-36
The compiler must be able to produce native output without requiring a monolithic runtime.

ABOOT-37
Runtime components are linked according to actual program requirements.

ABOOT-38
The first native backend must not dictate Core language semantics.

ABOOT-39
Adding a new target must not require changing Core semantics.

ABOOT-40
Axiom semantics must be testable without executing generated machine code.

ABOOT-41
Reference, MIR and native execution must support differential testing.

ABOOT-42
Semantic golden tests are authoritative over internal IR golden tests.

ABOOT-43
IR representation may evolve without changing language semantics.

ABOOT-44
Backend implementation may evolve without changing language semantics.

ABOOT-45
The bootstrap compiler must support reproducible builds where the selected profile requires them.

ABOOT-46
Compiler cache identity must include all semantic inputs relevant to the result.

ABOOT-47
Self-hosting must not introduce a second incompatible semantic implementation.

ABOOT-48
The self-hosted compiler must pass the same conformance suite as the bootstrap compiler.

ABOOT-49
A self-hosted compiler must be capable of compiling its own source tree.

ABOOT-50
Self-hosting success requires repeated self-compilation stability, not merely one successful bootstrap build.

ABOOT-51
Bootstrap stages may differ in implementation language but must converge on the same Axiom semantics.

ABOOT-52
Axiom compiler source must not require a hidden non-Axiom compiler extension after self-hosting.

ABOOT-53
The final compiler must be capable of operating without LLVM when native Axiom backends are available.

ABOOT-54
The final compiler must be capable of producing Axiom native objects without a third-party compiler.

ABOOT-55
Third-party system SDKs and platform libraries remain legitimate external platform dependencies.

ABOOT-56
The final compiler must not require a third-party compiler to compile ordinary Axiom programs.

ABOOT-57
The final compiler must not require a third-party runtime for programs that do not use corresponding runtime facilities.

ABOOT-58
Bootstrap and self-hosted compilers must preserve deterministic semantic behavior.

ABOOT-59
Self-hosting must preserve the existing CompilerDB/query architecture.

ABOOT-60
Self-hosting is an implementation milestone, not a change to Axiom language semantics.
```

---

# 98. Kiến trúc Axiom hiện tại

Sau task 272, toàn bộ đường đi đã tương đối hoàn chỉnh:

```text
                        AXIOM SOURCE
                             │
                             ▼
                     ┌──────────────┐
                     │  CompilerDB  │
                     │ Query Engine │
                     └──────┬───────┘
                            │
                     Syntax / AST
                            │
                     Resolution
                            │
                       Typed HIR
                            │
                      Semantic HIR
                            │
                           MIR
                            │
                   ┌────────┴────────┐
                   │                 │
               Verification       Effects
                   │                 │
                   └────────┬────────┘
                            ▼
                       Verified MIR
                            │
                         OptIR
                            │
                           ABI
                            │
                        Axiom LIR
                            │
                ┌───────────┼────────────┐
                ▼           ▼            ▼
             x86-64       ARM64        RV64
                │           │            │
                └───────────┼────────────┘
                            │
                          WASM
                            │
                            ▼
                       Machine IR
                            │
                       Object Writer
                            │
                         Linker
                            │
                      Native Binary
```

Bootstrap:

```text
             Rust axc
                │
                ▼
        Axiom compiler source
                │
                ▼
          Axiom compiler
                │
                ▼
       self-compilation
                │
                ▼
        Self-hosted Axiom
```

---

## Điểm chuyển quan trọng

Từ đây, **không nên tiếp tục mở rộng specification vô hạn**.

Axiom đã có gần như toàn bộ các semantic/system/application contracts quan trọng. Giai đoạn tiếp theo nên chuyển sang **Implementation Specification**.

### **BOOTSTRAP-273 — AXIOM COMPILER REPOSITORY + IMPLEMENTATION SPECIFICATION**

Task kế tiếp sẽ khóa ở mức có thể giao trực tiếp cho Antigravity:

```text
module/package graph
class/type graph của CompilerDB
query definitions
ID types
memory arenas
error/result conventions
threading model của compiler
file layout
public/internal API
test layout
build bootstrap
LLVM adapter boundary
TargetBackend interface
MIR data structures
Verifier API
Diagnostic API
```

Tức là từ task 273 trở đi, chúng ta không còn chỉ nói **“compiler nên làm gì”**, mà bắt đầu đặc tả **“từng module/compiler data structure/API phải được viết như thế nào để agent có thể code ngay”**.