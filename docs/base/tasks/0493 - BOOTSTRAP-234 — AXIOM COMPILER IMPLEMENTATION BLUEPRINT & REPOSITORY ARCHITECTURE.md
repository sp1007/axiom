# BOOTSTRAP-234 — AXIOM COMPILER IMPLEMENTATION BLUEPRINT & REPOSITORY ARCHITECTURE

**TRẠNG THÁI: FROZEN / COMPLETED**

Đây là bước chuyển quan trọng từ **language design** sang **engineering blueprint**.

Từ đây, một AI agent có thể bắt đầu tạo repository, module, interfaces, test harness và bootstrap compiler mà không phải tự đoán kiến trúc.

Nguyên tắc trung tâm:

> **Specification quyết định semantics. Compiler implementation hiện thực specification. Không được để implementation ngược lại quyết định language design.**

---

# 1. Mục tiêu của compiler đầu tiên

Compiler Axiom phải được thiết kế theo hướng:

```text
                Axiom Source
                     │
                     ▼
                Frontend
                     │
                     ▼
                    HIR
                     │
                     ▼
                    MIR
                     │
                     ▼
                Verification
                     │
                     ▼
              ┌──────────────┐
              │ Verified MIR │
              └──────┬───────┘
                     │
                     ▼
                  OptIR
                     │
                     ▼
                   ABI MIR
                     │
                     ▼
                    LIR
                     │
             ┌───────┴────────┐
             ▼                ▼
         Bootstrap          Future
          Backend          Axiom Backend
             │                │
          LLVM/LLD       Native Backend
             │                │
             ▼                ▼
          Native            Native
          Binary            Binary
```

**Compiler v0 không cần tự viết machine backend ngay lập tức.**

Nhưng kiến trúc phải được thiết kế sao cho LLVM chỉ là **bootstrap backend**, không trở thành dependency kiến trúc.

---

# 2. Ba compiler phases lớn

Axiom compiler chia thành:

```text
Frontend
Middle-end
Backend
```

## Frontend

```text
Source
 ↓
Lexer
 ↓
Lossless Syntax
 ↓
AST
 ↓
Resolver
 ↓
Type System
 ↓
Trait Solver
 ↓
HIR
```

## Middle-end

```text
HIR
 ↓
MIR
 ↓
Ownership
 ↓
Capability
 ↓
Effect
 ↓
Concurrency
 ↓
Comptime
 ↓
Verified MIR
 ↓
OptIR
```

## Backend

```text
OptIR
 ↓
ABI
 ↓
LIR
 ↓
Machine IR
 ↓
Register Allocation
 ↓
Machine Encoding
 ↓
Object
 ↓
Link
 ↓
Executable
```

---

# 3. Repository architecture

Repository canonical:

```text
axiom/
├── spec/
├── compiler/
├── runtime/
├── std/
├── targets/
├── tools/
├── tests/
├── examples/
├── docs/
├── bootstrap/
└── build/
```

---

# 4. `spec/`

Specification là nguồn authority.

```text
spec/
├── core/
│   ├── semantic-kernel/
│   ├── types/
│   ├── ownership/
│   ├── capability/
│   ├── effects/
│   ├── control-flow/
│   └── concurrency/
│
├── language/
│   ├── syntax/
│   ├── functions/
│   ├── traits/
│   ├── generics/
│   ├── patterns/
│   └── expressions/
│
├── compiler/
│   ├── hir/
│   ├── mir/
│   ├── verification/
│   ├── optimization/
│   └── abi/
│
├── platform/
│   ├── targets/
│   ├── abi/
│   ├── ffi/
│   └── object-format/
│
└── library/
```

Compiler code không được chứa semantics chỉ tồn tại trong đầu developer.

---

# 5. `compiler/`

Đây là phần chính:

```text
compiler/
├── common/
├── database/
├── lexer/
├── syntax/
├── parser/
├── ast/
├── resolver/
├── types/
├── traits/
├── consteval/
├── hir/
├── mir/
├── verify/
├── effects/
├── ownership/
├── capabilities/
├── concurrency/
├── async/
├── patterns/
├── opt/
├── abi/
├── lir/
├── machine/
├── object/
├── linker/
├── backend/
├── diagnostics/
├── debug/
├── query/
├── driver/
└── interpreter/
```

---

# 6. `common/`

Infrastructure không mang semantics:

```text
common/
├── ids
├── arenas
├── interner
├── hashing
├── bitsets
├── smallvec
├── graph
├── source-span
├── stable-map
└── serialization
```

Các ID:

```text
PackageId
ModuleId
FunctionId
TypeId
TraitId
FieldId
VariantId
LocalId
BasicBlockId
InstructionId
RegionId
CapabilityId
GenericInstanceId
SuspensionPointId
```

Không dùng raw pointers làm semantic identity.

---

# 7. `database/`

Central:

```text
CompilerDB
```

Các database:

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
SourceMapDB
LayoutDB
AbiDB
CodegenDB
BuildDB
```

---

# 8. Query architecture

Compiler không nên là một pipeline procedural khổng lồ:

```text
compileEverything()
```

Thay vào đó:

```text
query(FunctionId)
query(TypeId)
query(TraitId)
query(HIR)
query(MIR)
query(Layout)
query(ABI)
query(Codegen)
```

Ví dụ:

```text
MIR(FunctionId)
```

phụ thuộc:

```text
TypedHIR(FunctionId)
```

và TypedHIR phụ thuộc:

```text
ResolvedDeclarations
Types
Traits
Comptime
```

---

# 9. Incremental compilation

Dependency graph:

```text
Source
 ↓
Syntax
 ↓
Resolution
 ↓
Type
 ↓
Trait
 ↓
HIR
 ↓
MIR
 ↓
Verification
 ↓
Optimization
 ↓
Codegen
```

Nếu chỉ sửa function:

```text
fn foo()
```

không được rebuild toàn bộ package nếu dependency graph chứng minh không cần.

---

# 10. Lexer

Lexer output:

```text
Token {
    kind
    span
    flags
}
```

Token giữ source span chính xác.

Không mất trivia nếu lossless syntax tree cần giữ:

```text
whitespace
comments
formatting
```

---

# 11. Parser

Parser tạo:

```text
Lossless Syntax Tree
```

sau đó:

```text
Syntax Tree
 ↓
AST
```

AST không cần giữ mọi whitespace/comment.

---

# 12. AST

AST là semantic-neutral.

Ví dụ:

```text
FunctionDecl
    Name
    GenericParams
    Parameters
    ReturnType
    Body
```

AST không được tự quyết định:

```text
ownership
trait resolution
ABI
machine layout
```

---

# 13. Resolver

Resolver xử lý:

```text
Name → DeclarationId
```

Các namespace:

```text
value namespace
type namespace
trait namespace
module namespace
```

Resolution phải deterministic.

Không heuristic fallback.

---

# 14. Type system

TypeDB canonicalizes/interns:

```text
i32
Vec<i32>
Option<String>
fn(i32) -> i64
```

thành TypeId.

Ví dụ:

```text
TypeId 103
```

có thể đại diện duy nhất:

```text
Vec<i32>
```

trong CompilerDB revision đó.

---

# 15. Trait solver

Input:

```text
T: Ord
```

solver trả:

```text
Proven
NotProven
Ambiguous
Error
```

Không được trả:

```text
Probably
Maybe
BestGuess
```

---

# 16. Generic instantiation

Ví dụ:

```axiom
fn max<T: Ord>(a: T, b: T) -> T
```

Compiler tạo semantic generic instance:

```text
max<i32>
max<f64>
max<MyType>
```

sau đó quyết định strategy:

```text
Monomorphize
SharedGeneric
Specialized
```

nhưng semantics không thay đổi.

---

# 17. HIR

HIR là representation gần semantic language.

Ví dụ:

```text
MethodCall
```

đã được canonicalize thành:

```text
Call(
    FunctionId,
    Receiver,
    Arguments
)
```

Trait method resolution cũng được gắn vào HIR.

---

# 18. HIR phải loại bỏ syntax sugar

Các thứ như:

```text
v.length()
```

→

```text
length(v)
```

`?`:

```text
x?
```

→ semantic control-flow equivalent.

`for`:

```text
for x in iter
```

→ iterator protocol.

Mục tiêu:

> **MIR không cần hiểu hàng trăm surface syntax constructs.**

---

# 19. MIR

MIR là semantic execution representation.

Ví dụ:

```axiom
let c = a + b
```

có thể thành:

```text
bb0:
    StorageLive(c)
    c = Add(a, b)
    ...
```

---

# 20. MIR không phụ thuộc target

MIR không chứa:

```text
x86 eax
ARM x0
RISC-V a0
```

MIR chỉ chứa semantic operations:

```text
Add
Load
Store
Call
Drop
Move
MakeView
AtomicLoad
Await
Return
```

---

# 21. Place model

```text
Place =
    Local
    Field
    Index
    Deref
```

Ví dụ:

```text
user.address.city
```

→

```text
Field(
    Field(
        Local(user),
        address
    ),
    city
)
```

---

# 22. Ownership verifier

Module:

```text
verify/ownership/
```

gồm:

```text
init
move
copy
partial-move
drop
return
cleanup
```

State:

```text
Uninit
Owned
Moved
PartiallyMoved
Dropped
```

---

# 23. Capability verifier

```text
verify/capability/
```

theo dõi:

```text
CapabilityId
Provenance
Region
Access
Lifetime
StorageDomain
ExecutionDomain
```

---

# 24. Alias analysis

Không dùng một boolean:

```text
alias = true/false
```

Mà lattice:

```text
NO_ALIAS
MUST_ALIAS
PARTIAL_ALIAS
MAY_ALIAS
UNKNOWN
```

Điều này sau đó cung cấp dữ liệu cho optimizer.

---

# 25. Effect analysis

Compiler tính:

```text
EffectInfo
```

Ví dụ:

```text
foo:
    Read
    Write
    IO
```

hoặc:

```text
pure_add:
    {}
```

---

# 26. Escape analysis

Các trạng thái:

```text
NoEscape
ArgumentEscape
ReturnEscape
HeapEscape
ThreadEscape
ExternalEscape
UnknownEscape
```

Đây là nền tảng để:

```text
stack allocation
register promotion
allocation elimination
```

---

# 27. Async lowering

Frontend:

```text
async fn foo()
```

HIR có async information.

MIR lowering biến thành:

```text
FutureStateMachine
```

nhưng chỉ giữ values sống qua suspension.

Ví dụ:

```text
state 0
  ↓ await
state 1
  ↓ await
state 2
```

Không tạo state field cho local đã chết trước await.

---

# 28. Comptime

`const` và `comptime` được chạy bởi:

```text
Comptime VM
```

Compiler DB cache:

```text
ComptimeInputFingerprint
```

Không link Comptime VM vào executable.

---

# 29. Reference interpreter

Directory:

```text
compiler/interpreter/
├── ref/
├── mir/
├── memory/
├── effects/
├── concurrency/
└── oracle/
```

Hai implementation:

```text
ax-ref
ax-mir
```

---

# 30. `ax-ref`

`ax-ref` chạy semantic model gần source nhất.

Ví dụ:

```text
ax-ref test.ax
```

Output abstract:

```text
Result: 42
Effects: none
Panic: no
```

---

# 31. `ax-mir`

```text
ax-mir test.mir
```

phải cho cùng observable behavior.

Test:

```text
ax-ref source
    ==
ax-mir lowered-mir
```

---

# 32. Verification boundary

Pipeline bắt buộc:

```text
HIR
 ↓
MIR
 ↓
Ownership Verification
 ↓
Capability Verification
 ↓
Effect Verification
 ↓
Concurrency Verification
 ↓
Async Verification
 ↓
GPU Verification
 ↓
FFI Verification
 ↓
Verified MIR
```

**Không backend nào được nhận unverified MIR.**

---

# 33. Optimizer

```text
opt/
├── canonicalize/
├── ssa/
├── memoryssa/
├── alias/
├── scalar/
├── cfg/
├── inline/
├── specialize/
├── devirtualize/
├── loop/
├── vectorize/
├── memory/
├── async/
├── gpu/
├── lto/
├── pgo/
└── size/
```

---

# 34. OptIR

Không optimize trực tiếp semantic MIR một cách tùy tiện.

```text
Verified MIR
    ↓
Analysis
    ↓
OptIR
```

OptIR chứa:

```text
SSA
MemorySSA
AliasInfo
EffectInfo
RangeInfo
EscapeInfo
LoopInfo
TargetInfo
```

---

# 35. Optimization pass contract

Mỗi pass phải implement conceptual interface:

```text
Pass {
    name()
    preconditions()
    transform()
    preserved_invariants()
    generated_facts()
    validate()
}
```

Ví dụ:

```text
LoopInvariantCodeMotion
```

không được chỉ:

```text
moveInstruction()
```

mà phải kiểm tra:

```text
No conflicting memory
No observable effect violation
No capability violation
Dominance preserved
SSA valid
```

---

# 36. ABI layer

```text
abi/
├── classify/
├── calling-convention/
├── return/
├── aggregate/
├── register/
├── stack/
├── varargs/
└── ffi/
```

Semantic type:

```text
Vec4
```

sau ABI có thể trở thành:

```text
4 × SIMD register
```

hoặc:

```text
memory pointer
```

---

# 37. LIR

Axiom LIR là cầu nối:

```text
OptIR
 ↓
Axiom LIR
 ↓
Machine IR
```

LIR có:

```text
VirtualRegister
StackSlot
MachineValue
CallingConvention
MemoryOperand
BasicBlock
```

nhưng vẫn target-independent ở mức nhất định.

---

# 38. Machine IR

Target-specific:

```text
machine/
├── x86_64/
├── aarch64/
├── riscv64/
├── wasm/
└── gpu/
```

Mỗi target có:

```text
InstructionSet
RegisterSet
CallingConvention
Legalizer
InstructionSelector
```

---

# 39. Bootstrap backend

Compiler v0:

```text
Axiom LIR
   ↓
LLVM IR
   ↓
LLVM
   ↓
Object
```

hoặc:

```text
Axiom LIR
   ↓
System assembler/linker
```

Nhưng architecture:

```text
compiler/backend/llvm/
```

phải là **adapter**.

Không được để:

```text
MIR = LLVM IR
```

---

# 40. Native backend tương lai

Sau bootstrap:

```text
Axiom LIR
 ↓
Machine IR
 ↓
Instruction Selection
 ↓
Register Allocation
 ↓
Scheduling
 ↓
Encoding
 ↓
AxiomObject
```

Không cần LLVM.

---

# 41. Object writer

```text
object/
├── model/
├── elf/
├── pe/
├── macho/
├── wasm/
└── archive/
```

Core model:

```text
AxiomObject
```

với:

```text
Sections
Symbols
Relocations
Imports
Exports
TLS
Unwind
Debug
Metadata
Resources
```

---

# 42. Linker

```text
linker/
├── reader/
├── resolver/
├── archive/
├── relocation/
├── layout/
├── dead-strip/
├── icf/
├── tls/
├── imports/
├── exports/
├── debug/
└── writer/
```

Bootstrap có thể gọi linker hệ thống.

Final compiler có Axiom linker.

---

# 43. Driver

CLI:

```text
ax
```

Commands:

```text
ax init
ax check
ax build
ax run
ax test
ax clean
ax fetch
ax update
ax tree
ax inspect
ax explain
ax query
ax fmt
```

Compiler frontend driver:

```text
axc
```

có thể tồn tại nội bộ, nhưng user-facing tool nên thống nhất `ax`.

---

# 44. Build modes

Compiler phải hỗ trợ từ đầu:

```text
debug
release
size
test
freestanding
reproducible
```

và:

```text
--target
--features
--profile
--emit
```

---

# 45. `--emit`

Rất quan trọng cho development/compiler debugging:

```text
ax build --emit=tokens
ax build --emit=syntax
ax build --emit=ast
ax build --emit=hir
ax build --emit=mir
ax build --emit=verified-mir
ax build --emit=opt-ir
ax build --emit=abi
ax build --emit=lir
ax build --emit=object
```

AI agent có thể inspect từng stage.

---

# 46. Compiler explainability

Ví dụ:

```text
ax explain move file.ax:42
```

Compiler trả:

```text
Value moved here
Original owner:
    line 10

Transfer:
    line 42

Later use:
    line 45

Reason:
    non-Copy ownership transfer
```

Không chỉ:

```text
error: moved value
```

---

# 47. AI compiler API

Compiler phải expose structured JSON:

```text
{
  "diagnostic": {
    "code": "AOWN-001",
    "severity": "error",
    "span": {...},
    "facts": [...]
  }
}
```

AI agent có thể query:

```text
ax query type
ax query ownership
ax query effects
ax query capability
ax explain
```

---

# 48. Testing repository

```text
tests/
├── lexer/
├── parser/
├── resolver/
├── types/
├── traits/
├── generics/
├── ownership/
├── capability/
├── effects/
├── patterns/
├── async/
├── concurrency/
├── comptime/
├── ffi/
├── gpu/
├── interpreter/
├── mir/
├── optimizer/
├── abi/
├── object/
├── linker/
├── runtime/
└── integration/
```

---

# 49. Test levels

```text
L0 lexical
L1 syntax
L2 resolution
L3 type
L4 trait
L5 HIR
L6 MIR
L7 verification
L8 reference interpreter
L9 optimization
L10 backend
L11 native executable
```

Một compiler mới không cần pass L11 ngay để được coi là đúng.

---

# 50. First executable milestone

Không bắt đầu bằng:

```text
GUI
Tensor
Networking
GPU
```

Mà:

```axiom
fn main() {
    print("Hello, Axiom!")
}
```

Pipeline:

```text
Lexer
 ↓
Parser
 ↓
Resolver
 ↓
TypeChecker
 ↓
HIR
 ↓
MIR
 ↓
Verifier
 ↓
LLVM Backend
 ↓
Object
 ↓
Linker
 ↓
hello.exe
```

Đây là **vertical slice đầu tiên**.

---

# 51. Vertical slice philosophy

Không xây từng tầng hoàn chỉnh rồi mới tích hợp.

Sai:

```text
Lexer 100%
 ↓
Parser 100%
 ↓
Type 100%
 ↓
...
```

Thay vào đó:

```text
Lexer ─┐
Parser ├─→ Hello World
Type ──┤
HIR ───┤
MIR ───┤
Verify ┤
Backend┘
```

Sau khi có executable đầu tiên, mở rộng từng subsystem.

---

# 52. Bootstrap stages

## Stage 0

Compiler ngoài Axiom:

```text
Rust/C++/whatever bootstrap implementation
```

có thể sử dụng:

```text
LLVM
LLD
system SDK
```

---

## Stage 1

Compiler hiểu Core subset:

```text
struct
fn
let
if
loop
integer
enum
match
```

---

## Stage 2

Compiler có:

```text
ownership
Drop
view
mut_view
traits
generics
```

---

## Stage 3

Compiler compile được compiler source subset.

```text
Axiom compiler
     ↓
Axiom compiler
```

---

## Stage 4

Self-host:

```text
Axiom compiler
+
Axiom object writer
+
Axiom linker
```

không cần LLVM để build compiler chính thức.

---

# 53. Self-hosting bootstrap chain

Mục tiêu:

```text
C++/Rust Bootstrap Compiler
            │
            ▼
       axc-bootstrap
            │
            ▼
      Axiom compiler
            │
            ▼
       axc-stage1
            │
            ▼
       axc-stage2
            │
            ▼
       axc-stage2 compiled by itself
```

Cuối cùng:

```text
Stage N compiler
    ==
Stage N+1 compiler
```

theo semantic/compiler bootstrap criteria.

---

# 54. Compiler implementation language

Một quyết định quan trọng:

**Không nên cố viết toàn bộ compiler native backend ngay từ ngày đầu.**

Bootstrap compiler có thể dùng một implementation language thực dụng.

Nhưng architecture phải cấm dependency leakage:

```text
Axiom semantic model
≠
Rust semantics
≠
C++ semantics
≠
LLVM semantics
```

---

# 55. Dependency firewall

Đặc biệt:

```text
Frontend
Middle-end
```

không được phụ thuộc trực tiếp vào:

```text
LLVM API
LLD API
x86 API
Windows API
```

Chỉ:

```text
Backend adapter
Object adapter
Platform layer
```

được biết target implementation.

---

# 56. Compiler interfaces

Các boundary chính:

```text
Lexer
    → Syntax

Syntax
    → AST

AST
    → Resolver

Resolver
    → HIR

HIR
    → MIR

MIR
    → Verifier

VerifiedMIR
    → OptIR

OptIR
    → ABIMIR

ABIMIR
    → LIR

LIR
    → MachineIR

MachineIR
    → Object

Object
    → Linker

Linker
    → Binary
```

Mỗi boundary có schema/version.

---

# 57. No hidden semantic mutation

Một module backend không được:

```text
change ownership
change trait resolution
change type
change effect
```

Backend chỉ được **lower representation**.

---

# 58. Compiler invariant

```text
Frontend decides meaning.
Verifier decides legality.
Optimizer decides profitable transformations.
Backend decides representation.
Linker decides binary composition.
```

Không module nào được vượt authority của mình.

---

# 59. Compiler crash policy

Phải phân biệt:

```text
UserError
Internal Compiler Error
Compiler Bug
UnsupportedFeature
TargetLimitation
```

Ví dụ:

```text
AOWN-001
```

không bao giờ được biến thành:

```text
ICE
```

nếu đó là user program hợp lệ/không hợp lệ đã dự kiến.

---

# 60. Compiler recovery

Parser có thể tạo:

```text
MissingToken
ErrorNode
UnclosedBlock
InvalidExpression
```

nhưng:

```text
Partial AST
```

không được đi vào:

```text
Codegen
```

Production boundary:

```text
Complete
 ↓
Verified
 ↓
Codegen
```

---

# 61. Compiler concurrency

Compiler itself phải parallelize được:

```text
parse files
resolve independent modules
typecheck independent declarations
compile generic instances
comptime jobs
optimization functions
codegen functions
```

Nhưng deterministic output.

---

# 62. Parallel compiler correctness

Parallel compilation:

```text
Compiler(A, parallel)
```

phải semantic-equivalent:

```text
Compiler(A, serial)
```

Không được:

```text
race
nondeterministic trait resolution
nondeterministic symbol naming
```

---

# 63. Cache architecture

Cache key:

```text
SourceHash
+
DependencySemanticFingerprint
+
CompilerSemanticVersion
+
Target
+
Features
+
ComptimeInputs
+
CodegenConfig
```

Không dùng đơn giản:

```text
filename + timestamp
```

---

# 64. Compiler artifacts

Một package có thể sinh:

```text
.axmeta
.axlib
.o
.a
.lib
.dll
.so
.dylib
.exe
```

Tùy target/profile.

---

# 65. `.axmeta`

Chứa compiler/tooling information:

```text
Declarations
Types
Traits
Generics
ABI
Visibility
Source mapping
Reflection metadata
Optimization summaries
```

Không bắt buộc embedded trong executable.

---

# 66. `.axlib`

Logical artifact:

```text
.axlib
├── native objects
├── generic bodies
├── semantic metadata
├── ABI metadata
├── dependency metadata
└── optimization summaries
```

Cho phép compiler tận dụng package binary mà không cần source.

---

# 67. First implementation subset

Compiler agent nên bắt đầu với:

```text
bool
i8/i16/i32/i64
u8/u16/u32/u64
f32/f64

unit
never

let
let mut

struct
enum

fn
return

if
else

loop
while
break
continue

match

arrays

basic generics

modules
```

Sau đó:

```text
ownership
Drop
Option
Result
view
mut_view
traits
```

---

# 68. Không nên bootstrap tất cả cùng lúc

Các subsystem sau **không cần để tạo compiler executable đầu tiên**:

```text
async
GPU
GUI
network
database
crypto
Tensor
AD
dynamic loading
hot reload
reflection runtime
```

Nhưng interface architecture phải dành chỗ cho chúng.

---

# 69. Compiler milestone map

```text
M0 Repository
 ↓
M1 Lexer
 ↓
M2 Parser
 ↓
M3 AST/Resolver
 ↓
M4 Type System
 ↓
M5 HIR
 ↓
M6 MIR
 ↓
M7 Reference Interpreter
 ↓
M8 Ownership Verifier
 ↓
M9 First executable
 ↓
M10 Traits/Generics
 ↓
M11 Capability system
 ↓
M12 Optimizer
 ↓
M13 ABI
 ↓
M14 Native object writer
 ↓
M15 Native linker
 ↓
M16 Self-hosting
```

---

# 70. Gate quan trọng nhất

Không phải:

> “Compiler compile được nhiều code.”

Mà:

> **Compiler không được codegen một chương trình mà Verified MIR chưa chứng minh hợp lệ.**

Đây là quality gate số một.

---

# 71. Definition of Done cho compiler subsystem

Mỗi subsystem chỉ được đánh dấu complete khi có:

```text
Specification
Implementation
Unit Tests
Conformance Tests
Negative Tests
Diagnostics
Integration Tests
Reference Interpreter Agreement
Incremental Behavior
Determinism
Documentation
```

và nếu liên quan optimization:

```text
Translation Validation
```

---

# 72. Agent workflow

AI agent xây compiler phải hoạt động:

```text
Read Spec
 ↓
Read Existing Architecture
 ↓
Implement smallest vertical slice
 ↓
Add tests
 ↓
Run reference semantics
 ↓
Run verifier
 ↓
Run compiler
 ↓
Run regression suite
 ↓
Commit
 ↓
Next task
```

Không:

```text
generate 50,000 lines
↓
compile
↓
hope
```

---

# 73. NotebookLM integration

Với workflow Axiom hiện tại, agent nghiên cứu nên:

```text
Question
 ↓
NotebookLM research
 ↓
Source evidence
 ↓
Architecture decision
 ↓
Spec update
 ↓
Implementation
```

Không để agent tự thay đổi semantic design chỉ dựa trên một search result.

---

# 74. Compiler source of truth

Hierarchy:

```text
Formal Semantic Kernel
        ↓
Axiom Specification
        ↓
Compiler Contracts
        ↓
Tests
        ↓
Implementation
```

Implementation không đứng đầu hierarchy.

---

# 75. Architecture freeze

Sau BOOTSTRAP-234, compiler có architecture:

```text
                 AXIOM COMPILER
                      │
       ┌──────────────┼──────────────┐
       │              │              │
    FRONTEND       MIDDLE-END      BACKEND
       │              │              │
   Lexer/AST       HIR/MIR          LIR
   Resolver        Verify           Machine
   Types           Opt              Object
   Traits          Async            Linker
       │              │              │
       └──────────────┼──────────────┘
                      │
                 CompilerDB
                      │
              Reference Oracle
```

Đây là kiến trúc đủ để bắt đầu implementation thật.

---

# 76. Các invariant mới

```text
ACOMPILER-20
The Formal Semantic Kernel is the semantic authority of the compiler.

ACOMPILER-21
Compiler implementation must not redefine language semantics.

ACOMPILER-22
Frontend lowering must preserve semantic meaning.

ACOMPILER-23
HIR represents resolved language semantics rather than surface syntax.

ACOMPILER-24
MIR represents executable language semantics independently of target ISA.

ACOMPILER-25
Only Verified MIR may enter semantic optimization.

ACOMPILER-26
Optimization must preserve verified semantic invariants.

ACOMPILER-27
Backend lowering must not introduce semantic ownership or capability changes.

ACOMPILER-28
Target-specific implementation is isolated behind backend boundaries.

ACOMPILER-29
Bootstrap dependencies must not become permanent semantic dependencies.

ACOMPILER-30
LLVM is a bootstrap backend adapter, not the Axiom semantic IR.

ACOMPILER-31
Reference interpretation is an executable semantic oracle.

ACOMPILER-32
MIR interpretation must agree with reference interpretation.

ACOMPILER-33
Compiler queries must operate through stable semantic identities.

ACOMPILER-34
Incremental compilation must preserve semantic equivalence with clean compilation.

ACOMPILER-35
Parallel compilation must preserve deterministic semantic results.

ACOMPILER-36
Compiler caches must include all semantic inputs affecting the result.

ACOMPILER-37
Partial/recovered programs must never cross the production code-generation boundary.

ACOMPILER-38
Compiler diagnostics must distinguish user errors from compiler failures.

ACOMPILER-39
Each compiler subsystem must have explicit input/output contracts.

ACOMPILER-40
Compiler passes may not silently mutate facts owned by another semantic authority.

ACOMPILER-41
Native backend implementation may be replaced without changing Core semantics.

ACOMPILER-42
Object and linker implementations may be replaced without changing frontend semantics.

ACOMPILER-43
Self-hosting must reproduce compiler semantics rather than merely compiler output.

ACOMPILER-44
Axiom self-hosting must not require LLVM as a permanent semantic dependency.

ACOMPILER-45
Axiom self-hosting must not require a third-party runtime as a language requirement.

ACOMPILER-46
Compiler correctness takes precedence over optimization profitability.

ACOMPILER-47
Every optimization pass must declare and validate its legality conditions.

ACOMPILER-48
Every semantic subsystem must have negative tests for invalid programs.

ACOMPILER-49
Every correctness-critical compiler change must add regression coverage.

ACOMPILER-50
The compiler architecture must permit independent replacement of frontend, optimizer, backend, object writer and linker implementations.
```

---

# 77. Kết quả thực tế của BOOTSTRAP-234

Từ đây Axiom không còn chỉ là:

```text
"một ngôn ngữ được thiết kế trên giấy"
```

mà đã có:

```text
Language Specification
        +
Formal Semantics
        +
Compiler Architecture
        +
Verification Boundary
        +
Optimization Architecture
        +
Backend Architecture
        +
Bootstrap Strategy
        +
Self-hosting Strategy
```

Đây là mức kiến trúc mà **AI coding agent có thể bắt đầu triển khai repository thực tế**.

---

# TASK TIẾP THEO

## **BOOTSTRAP-235 — AXIOM COMPILER BOOTSTRAP SUBSET & FIRST EXECUTABLE**

Bước tiếp theo nên cực kỳ thực dụng: **định nghĩa chính xác subset Axiom tối thiểu để compiler đầu tiên tự compile được một chương trình native.**

Nó sẽ đóng đinh:

```text
Axiom Bootstrap Language
        ↓
Lexer
        ↓
Parser
        ↓
Resolver
        ↓
Type Checker
        ↓
HIR
        ↓
MIR
        ↓
Minimal Verifier
        ↓
LLVM Bootstrap Backend
        ↓
LLD/System Linker
        ↓
hello.exe
```

Sau đó sẽ xác định **từng construct nào bắt buộc phải có ở Stage 0, construct nào được hoãn**, và quan trọng nhất là thiết kế **bootstrap compiler có thể tự mở rộng chính nó** thay vì tạo một compiler prototype rồi phải viết lại gần như toàn bộ ở giai đoạn self-hosting.