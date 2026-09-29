# BOOTSTRAP-269 — AXIOM COMPILER REPOSITORY ARCHITECTURE, MODULE BOUNDARIES & IMPLEMENTATION CONTRACTS

**TRẠNG THÁI: FROZEN / COMPLETED**

Mục tiêu của task này:

> Chuyển kiến trúc compiler thành **một cấu trúc repository có thể bắt đầu implement ngay**, đồng thời ngăn compiler biến thành một “big ball of mud”.

---

## 1. Nguyên tắc kiến trúc

Axiom compiler phải có **dependency DAG một chiều**:

```text
Source
  ↓
Syntax
  ↓
Resolve
  ↓
Type
  ↓
HIR
  ↓
MIR
  ↓
Verify
  ↓
Optimize
  ↓
ABI
  ↓
LIR
  ↓
Backend
  ↓
Object
  ↓
Linker
```

Không module nào được phép tạo dependency ngược.

Ví dụ:

```text
Backend ─X→ Parser
Linker  ─X→ TypeChecker
Optimizer ─X→ Lexer
MIR ─X→ x86 register
```

---

# 2. Repository chính

Đề xuất cấu trúc:

```text
axiom/
├── compiler/
├── std/
├── runtime/
├── targets/
├── linker/
├── tools/
├── tests/
├── examples/
├── specs/
├── bootstrap/
├── scripts/
└── docs/
```

---

# 3. `compiler/`

```text
compiler/
├── foundation/
├── source/
├── syntax/
├── lexer/
├── parser/
├── resolver/
├── types/
├── traits/
├── consteval/
├── hir/
├── mir/
├── verify/
├── analysis/
├── optimize/
├── abi/
├── lir/
├── backend/
├── object/
├── codegen/
├── diagnostics/
├── database/
├── driver/
└── cli/
```

---

# 4. `foundation/`

Đây là tầng thấp nhất.

Chỉ chứa những abstraction compiler dùng chung:

```text
Id
Span
TextRange
Arena
Interner
Hash
SmallVec
BitSet
IndexMap
Graph
Fingerprint
SourcePosition
```

Không được chứa:

```text
Type
AST
MIR
LLVM
x86
```

---

# 5. ID system

Ví dụ:

```text
FileId
ModuleId
SyntaxId
DeclarationId
TypeId
TraitId
FunctionId
FieldId
VariantId
GenericParamId
GenericInstanceId
LocalId
BasicBlockId
InstructionId
CapabilityId
RegionId
ClosureId
SuspensionPointId
```

---

# 6. ID không được mang semantic state

Ví dụ không:

```text
TypeId {
    type: Type
}
```

mà:

```text
TypeId
```

sau đó:

```text
TypeDB.get(TypeId)
```

---

# 7. Lý do

Giúp:

```text
incremental compilation
interning
parallel compilation
cache
serialization
AI tooling
```

---

# 8. `source/`

Quản lý:

```text
SourceFile
SourceMap
LineIndex
Revision
File identity
```

API chính:

```text
load_file()
file_text()
span_text()
line_col()
source_span()
```

Không biết:

```text
type
ownership
MIR
```

---

# 9. `lexer/`

Input:

```text
SourceFile
```

Output:

```text
TokenStream
```

```text
Source
 ↓
Lexer
 ↓
Tokens
```

Lexer không resolve identifier.

---

# 10. `syntax/`

Chứa:

```text
GreenNode
GreenToken
SyntaxTree
Trivia
RecoveryNode
SyntaxCursor
```

Mục tiêu:

> lossless source representation.

---

# 11. `parser/`

```text
TokenStream
 ↓
GreenTree
 ↓
AST
```

Parser không type-check.

---

# 12. `resolver/`

Input:

```text
AST
ModuleDB
PackageDB
```

Output:

```text
Resolved AST / HIR names
```

Chịu trách nhiệm:

```text
name lookup
module
use
visibility
symbol identity
imports
exports
```

---

# 13. `types/`

Chứa:

```text
Type
TypeId
TypeDB
TypeUnifier
Inference
Coercion
Cast
Layout-independent type facts
```

Không chứa:

```text
LLVMType
MachineType
Register
```

---

# 14. `traits/`

```text
TraitDB
ImplDB
Goal
CanonicalGoal
Solver
Projection
Coherence
ObjectSafety
```

Trait solver không biết:

```text
x86
LLVM
register
```

---

# 15. `consteval/`

```text
const
comptime
CompileTimeValue
ComptimeVM
ComptimeCapabilities
ComptimeDependency
```

Output phải quay lại semantic system:

```text
comptime
   ↓
Value / Declaration
   ↓
normal semantic verification
```

---

# 16. `hir/`

HIR là:

> semantic representation gần source.

Ví dụ:

```text
MethodCall
```

sau resolution có thể trở thành:

```text
FunctionCall {
    function_id
    receiver
    args
}
```

---

# 17. HIR phải loại bỏ ambiguity

HIR không nên còn:

```text
"có thể là method A hoặc B"
```

---

# 18. `mir/`

MIR là semantic execution model.

Chứa:

```text
Place
Operand
RValue
Statement
Terminator
BasicBlock
FunctionBody
```

Ví dụ:

```text
Place
Operand
RValue
```

là các primitive compiler quan trọng.

---

# 19. MIR không biết ISA

Không có:

```text
rax
x0
sp
v0
```

---

# 20. `verify/`

Chứa:

```text
OwnershipVerifier
InitVerifier
DropVerifier
CapabilityVerifier
SendVerifier
ShareVerifier
AsyncVerifier
GpuVerifier
FfiVerifier
```

---

# 21. Tất cả dùng chung:

```text
DataflowAnalysis<State>
```

---

# 22. Verification boundary

```text
MIR
 ↓
Verification
 ↓
Verified MIR
```

Không có đường:

```text
MIR → LLVM
```

---

# 23. `analysis/`

Đây là analysis phục vụ optimizer:

```text
Liveness
Escape
Alias
Effect
Range
Loop
MemorySSA
CallGraph
SCC
```

Phân biệt:

```text
Verification
```

với:

```text
Optimization Analysis
```

---

# 24. Verification trả lời:

> Chương trình có hợp lệ theo semantic model không?

Optimization analysis trả lời:

> Compiler có đủ bằng chứng để biến đổi chương trình không?

---

# 25. `optimize/`

Pipeline:

```text
Verified MIR
 ↓
SSA
 ↓
MemorySSA
 ↓
OptIR
 ↓
Optimization
```

Các pass:

```text
SCCP
GVN
CSE
DCE
LICM
Inlining
SROA
EscapePromotion
Vectorization
BoundsCheckElimination
Devirtualization
```

---

# 26. Mỗi optimization pass phải khai báo contract

Ví dụ:

```text
Pass:
    BoundsCheckElimination

Requires:
    RangeInfo

Preserves:
    Ownership
    Capability
    Effects

Produces:
    simplified bounds operation
```

---

# 27. Không pass nào được tự ý phá semantic invariant.

---

# 28. `abi/`

Tách:

```text
semantic type
```

khỏi:

```text
physical ABI representation
```

---

# 29. ABI module

Chịu trách nhiệm:

```text
CallingConvention
ParameterClassification
ReturnClassification
AggregatePassing
SRet
RegisterClass
StackPassing
Alignment
VariadicABI
FFI ABI
```

---

# 30. ABI không thuộc type system

Ví dụ:

```text
struct Big {
    ...
}
```

không tự quyết định:

```text
pass-by-register
```

ABI target quyết định.

---

# 31. `lir/`

Axiom LIR là compiler IR gần machine nhưng **chưa phụ thuộc ISA**.

Ví dụ:

```text
LirAdd
LirLoad
LirStore
LirCall
LirBranch
LirCompare
LirAtomic
LirVector
LirAddress
```

---

# 32. LIR không được chứa:

```text
RAX
X0
A0
SP
```

---

# 33. `backend/`

```text
backend/
├── common/
├── x86_64/
├── arm64/
├── riscv64/
└── wasm/
```

---

# 34. Backend common

Chứa:

```text
TargetBackend
MachineIR
RegisterAllocator
FrameModel
MachineVerifier
Encoder interface
```

nhưng không chứa register cụ thể của target.

---

# 35. Target backend contract

```text
TargetBackend {
    target_spec()
    lower_abi()
    legalize()
    select()
    allocate()
    lower_frame()
    lower_atomic()
    lower_tls()
    schedule()
    verify()
    encode()
    emit_object()
}
```

---

# 36. x86 backend

```text
backend/x86_64/
├── registers
├── instructions
├── selector
├── legalizer
├── allocator
├── frame
├── scheduler
├── encoder
└── verifier
```

---

# 37. ARM64 backend

Tương tự nhưng độc lập:

```text
backend/arm64/
```

---

# 38. RV64 backend

```text
backend/riscv64/
```

---

# 39. WASM backend

Đặc biệt:

```text
backend/wasm/
├── wasm_ir
├── stackifier
├── control_flow
├── locals
├── memory
├── tables
├── validator
└── encoder
```

WASM không cần giả lập register machine.

---

# 40. Đây là một test architecture cực mạnh.

Nếu WASM backend vẫn cần:

```text
RAX-like virtual registers
```

thì LIR đang sai abstraction.

---

# 41. `object/`

Logical object model:

```text
AxiomObject
Section
Symbol
Relocation
Import
Export
TLS
DebugInfo
Metadata
Resource
SecurityProperty
```

---

# 42. Object module không biết semantic source.

Nó chỉ biết:

```text
machine artifact
```

---

# 43. Object writers

```text
object/
├── elf/
├── pe/
├── macho/
└── wasm/
```

---

# 44. `linker/`

```text
linker/
├── resolver
├── archive
├── section_layout
├── relocation
├── dead_strip
├── icf
├── tls
├── import_export
├── lto
└── writer
```

---

# 45. Linker không được type-check Axiom.

---

# 46. `codegen/`

Đây là orchestration:

```text
Verified MIR
 ↓
OptIR
 ↓
ABI MIR
 ↓
LIR
 ↓
TargetBackend
 ↓
AxiomObject
```

---

# 47. `database/`

Central:

```text
CompilerDB
```

và các database:

```text
SourceDB
SyntaxDB
DeclarationDB
ModuleDB
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

---

# 48. Query API

Ví dụ:

```text
parse(file)
resolve(module)
type_of(expr)
trait_solve(goal)
hir(function)
mir(function)
verify(function)
layout(type)
abi(function)
codegen(function)
```

---

# 49. Query phải có dependency tracking

Ví dụ:

```text
codegen(Foo)
```

phụ thuộc:

```text
verify(Foo)
mir(Foo)
hir(Foo)
type_of(...)
trait_solve(...)
```

---

# 50. Cache ở query boundary

Không cache tùy tiện ở mọi function.

---

# 51. `diagnostics/`

Structured diagnostics:

```text
Diagnostic {
    code
    severity
    primary_span
    secondary_spans
    message
    notes
    proof
    related
}
```

---

# 52. Diagnostic code stable

Ví dụ:

```text
AXOWN-E001
ATYPE-E001
ATRAIT-E001
ACAP-E001
AABI-E001
ABACKEND-E001
```

---

# 53. `driver/`

Điều phối toàn bộ compilation.

```text
Driver
 ↓
BuildPlan
 ↓
CompilerDB
 ↓
CompilationPipeline
 ↓
Artifact
```

---

# 54. `cli/`

Chỉ là interface.

Ví dụ:

```text
ax check
ax build
ax run
ax test
ax explain
ax inspect
ax query
```

Không chứa semantic logic.

---

# 55. Dependency DAG chính xác

```text
foundation
   │
source
   │
syntax
   │
lexer ─────┐
           ▼
         parser
           │
           ▼
       resolver
           │
      ┌────┴────┐
      ▼         ▼
    types     consteval
      │         │
      └────┬────┘
           ▼
          HIR
           │
           ▼
          MIR
           │
           ▼
        verify
           │
           ▼
        analysis
           │
           ▼
       optimize
           │
           ▼
          ABI
           │
           ▼
          LIR
           │
           ▼
       backend
           │
           ▼
         object
           │
           ▼
         linker
```

---

# 56. Nhưng CompilerDB nằm ngang

```text
                  CompilerDB
                      │
       ┌──────────────┼──────────────┐
       ▼              ▼              ▼
    frontend       semantic       backend
       │              │              │
       └──────────── queries ─────────┘
```

CompilerDB **không phải một semantic layer mới**.

Nó là storage/query infrastructure.

---

# 57. Quy tắc dependency

Mỗi package compiler phải khai báo:

```text
depends_on
```

và CI kiểm tra cycle.

---

# 58. Cấm dependency cycle

Ví dụ:

```text
types → HIR → types
```

không được phép.

---

# 59. Nếu cần abstraction chung

Đưa abstraction xuống:

```text
foundation
```

hoặc:

```text
compiler-contracts
```

thay vì tạo cycle.

---

# 60. Semantic contracts package

Nên có:

```text
compiler/contracts/
```

chứa interface:

```text
TargetBackend
ObjectWriter
Linker
DiagnosticSink
Query
DataflowAnalysis
```

---

# 61. Nhưng contracts không chứa implementation.

---

# 62. Public/private compiler APIs

Mỗi module chia:

```text
api
internal
```

Không cho module khác truy cập internal state tùy ý.

---

# 63. Ví dụ

`types` cung cấp:

```text
TypeId
TypeKind
type_of()
implements()
```

nhưng không cho backend sửa:

```text
TypeDB.internal_arena
```

---

# 64. Immutable semantic objects

Ưu tiên:

```text
immutable
interned
ID-addressed
```

để hỗ trợ parallelism.

---

# 65. Mutable state

Chỉ dành cho:

```text
cache
memoization
incremental indexes
build state
```

không dùng mutable global semantic state.

---

# 66. Thread safety của CompilerDB

CompilerDB phải hỗ trợ:

```text
parallel queries
```

nhưng kết quả semantic phải deterministic.

---

# 67. Query cancellation

Compilation query có thể bị hủy:

```text
user edits file
```

query cũ trở nên stale.

---

# 68. Revision model

```text
Revision N
   ↓
edit
   ↓
Revision N+1
```

---

# 69. Query cache phải biết revision dependency.

---

# 70. Compiler error không được phá cache toàn bộ

Ví dụ sửa một expression chỉ nên invalidate dependency liên quan.

---

# 71. Artifact graph

Compiler phải tạo:

```text
Source
 ↓
SemanticFingerprint
 ↓
MIR fingerprint
 ↓
CodegenFingerprint
 ↓
Object fingerprint
 ↓
Binary fingerprint
```

---

# 72. Source fingerprint ≠ binary fingerprint

Một thay đổi source có thể không thay đổi machine code.

---

# 73. Ví dụ:

```text
unused function
```

có thể bị DCE.

---

# 74. Debug mode vẫn phải giữ source mapping.

---

# 75. `tests/`

Đề xuất:

```text
tests/
├── lexer/
├── parser/
├── resolver/
├── types/
├── traits/
├── comptime/
├── hir/
├── mir/
├── ownership/
├── capability/
├── async/
├── gpu/
├── optimization/
├── abi/
├── backend/
├── object/
├── linker/
├── ffi/
├── concurrency/
├── wasm/
└── bootstrap/
```

---

# 76. Test semantic trước codegen

Ví dụ:

```text
tests/ownership/
```

không cần biết LLVM.

---

# 77. Backend tests

Backend test có:

```text
LIR
 ↓
Machine IR
 ↓
Machine code
```

---

# 78. Không dùng assembly golden test làm semantic authority.

---

# 79. Bootstrap tests

```text
bootstrap/
├── stage0/
├── stage1/
├── stage2/
└── reproducibility/
```

---

# 80. Stage0

External compiler build:

```text
bootstrap compiler
```

---

# 81. Stage1

Stage0 build:

```text
Axiom compiler
```

---

# 82. Stage2

Stage1 build chính compiler:

```text
self-hosted compiler
```

---

# 83. Stage3

Stage2 build Stage2:

```text
stability test
```

---

# 84. Build system

Top-level:

```text
bootstrap.sh
bootstrap.ps1
```

ban đầu có thể tồn tại.

Sau khi self-host:

```text
ax build
```

là canonical.

---

# 85. `std/`

Không đặt compiler implementation vào std.

Compiler có thể sử dụng std nhưng dependency direction phải rõ:

```text
compiler
   ↓
axiom core/std
```

không:

```text
std → compiler
```

---

# 86. Compiler intrinsic

Nếu std cần compiler intrinsic:

```text
std
 ↓
compiler intrinsic contract
```

nhưng semantic contract phải được compiler định nghĩa.

---

# 87. `runtime/`

Runtime optional:

```text
runtime/
├── startup
├── allocator
├── threads
├── async
├── panic
└── platform
```

Compiler chỉ link component cần thiết.

---

# 88. `targets/`

```text
targets/
├── x86_64/
├── arm64/
├── riscv64/
└── wasm/
```

Chứa:

```text
TargetSpec
ABI data
platform metadata
feature definitions
```

---

# 89. Không để TargetSpec nằm trong backend riêng.

Ví dụ:

```text
TargetSpec → x86 backend
```

không phải:

```text
x86 backend → định nghĩa toàn bộ target
```

---

# 90. TargetSpec là nguồn sự thật.

---

# 91. Backend đọc TargetSpec.

---

# 92. Platform layer

```text
std/os/windows
std/os/linux
std/os/macos
std/os/android
std/os/ios
std/os/wasi
```

---

# 93. Compiler không hard-code OS API.

---

# 94. Ví dụ compiler không nên biết:

```text
CreateFileW
open()
mmap()
```

trừ khi đang compile FFI metadata/platform contracts.

---

# 95. AI tooling

```text
tools/
├── lsp/
├── formatter/
├── analyzer/
├── doc/
├── debugger/
├── ai/
└── inspect/
```

AI layer chỉ đọc:

```text
CompilerDB
Diagnostics
Explain API
```

---

# 96. AI không được sửa semantic DB trực tiếp.

AI:

```text
query → proposal → source edit → compiler verification
```

---

# 97. Không:

```text
AI → force TypeDB state
```

---

# 98. Compiler explain architecture

```text
CompilerDB
    ↓
Proof/Fact Graph
    ↓
Explain API
    ↓
CLI/LSP/AI
```

---

# 99. Đây là kiến trúc rất phù hợp với mục tiêu AI-friendly của Axiom.

---

# 100. Example AI query

```text
ax explain ownership file.ax:42
```

Compiler trả:

```text
MoveFact
CapabilityFact
ProvenanceFact
DropFact
ConflictFact
```

---

# 101. Compiler implementation contract

Mỗi subsystem phải document:

```text
Purpose
Inputs
Outputs
Invariants
Dependencies
Mutation policy
Caching
Error behavior
Parallelism
```

---

# 102. Ví dụ `OwnershipVerifier`

```text
Input:
    Verified-independent MIR

Output:
    OwnershipFacts
    Diagnostics

Guarantees:
    no invalid move
    no use-after-move
    no double-drop
```

---

# 103. Không được output "best effort verification".

---

# 104. Verification failure là compile failure.

---

# 105. Optimization failure không phải compile semantic failure.

Ví dụ vectorization không thành công:

```text
→ giữ scalar code
```

---

# 106. Backend không hỗ trợ instruction:

```text
→ legalize
```

hoặc:

```text
→ diagnostic
```

không được sinh binary sai.

---

# 107. Object writer không hiểu relocation:

```text
→ diagnostic
```

---

# 108. Linker không resolve symbol:

```text
→ link error
```

---

# 109. Không có silent fallback sai semantic.

---

# 110. Logging/tracing

Compiler cần tracing theo phase:

```text
--trace lexer
--trace resolver
--trace mir
--trace verify
--trace optimize
--trace codegen
```

---

# 111. Nhưng tracing không thay đổi semantic behavior.

---

# 112. Compiler profiling

Các metric:

```text
parse_time
resolve_time
type_time
trait_time
mir_time
verify_time
opt_time
codegen_time
link_time
memory_peak
cache_hit_rate
```

---

# 113. Đây sẽ cực kỳ quan trọng khi compiler lớn.

---

# 114. Parallelism

Có thể chạy song song:

```text
modules
functions
generic instances
trait goals
optimization units
backend functions
```

nhưng phải deterministic.

---

# 115. Một nguyên tắc quan trọng:

> **Parallelism changes execution order, never semantic order.**

---

# 116. Compiler memory management

Compiler không nên dùng GC mặc định.

Có thể sử dụng:

```text
Arena
BumpArena
InternPool
GenerationalArena
```

---

# 117. Compiler lifetime

Ví dụ:

```text
CompilerDB
 ├── SourceDB
 ├── HIRDB
 └── MIRDB
```

Arena lifetime gắn với compilation/revision.

---

# 118. Đây cũng là dogfood test cho Axiom ownership model.

---

# 119. Compiler graph references

Thay vì pointer trực tiếp:

```text
TypeId
FunctionId
BlockId
```

---

# 120. Đây cũng giảm pointer complexity trong compiler code.

---

# 121. Tuy nhiên compiler implementation vẫn được phép dùng unsafe

Ví dụ:

```text
arena indexing
packed storage
custom hash table
memory mapped cache
```

nếu cần performance.

---

# 122. Nhưng unsafe compiler code phải có contract.

---

# 123. Repository CI

Mỗi commit phải chạy tối thiểu:

```text
format
compile
unit tests
semantic tests
conformance
bootstrap smoke test
```

---

# 124. Nightly:

```text
fuzz
differential
bootstrap stage2
cross-target
reproducibility
```

---

# 125. Architecture test

CI phải kiểm tra dependency graph:

```text
parser → resolver       OK
resolver → parser       forbidden
backend → parser        forbidden
linker → type           forbidden
```

---

# 126. Đây là **architecture lint**.

Rất đáng làm ngay từ đầu.

---

# 127. Module ownership

Mỗi directory có một owner semantic:

```text
types → Type semantics
mir → execution semantics
verify → correctness
abi → physical calling convention
backend → target machine
object → binary representation
linker → final image
```

---

# 128. Không có "misc/" để nhét code.

---

# 129. Nếu code không biết thuộc layer nào

thì architecture có vấn đề.

---

# 130. Compiler implementation stack cuối cùng

```text
┌──────────────────────────────────────────────┐
│                    CLI / IDE / AI            │
├──────────────────────────────────────────────┤
│                    Driver                    │
├──────────────────────────────────────────────┤
│                  CompilerDB                  │
├──────────────────────────────────────────────┤
│ Lexer → Parser → Resolver → Type → Trait    │
├──────────────────────────────────────────────┤
│                    HIR                       │
├──────────────────────────────────────────────┤
│                    MIR                       │
├──────────────────────────────────────────────┤
│             Semantic Verification            │
├──────────────────────────────────────────────┤
│          Analysis → Optimization             │
├──────────────────────────────────────────────┤
│                    ABI                       │
├──────────────────────────────────────────────┤
│                    LIR                       │
├──────────────────────────────────────────────┤
│               Target Backend                 │
├──────────────────────────────────────────────┤
│                AxiomObject                   │
├──────────────────────────────────────────────┤
│                   Linker                     │
└──────────────────────────────────────────────┘
```

---

# 131. Một thay đổi kiến trúc đáng đóng băng

Từ task này, thêm nguyên tắc:

> **Semantic layers own meaning; representation layers own physical realization.**

Ví dụ:

```text
TypeDB
```

sở hữu:

> `Vec<T>` là gì.

```text
LayoutDB
```

sở hữu:

> `Vec<T>` có representation thế nào trên target.

```text
ABI
```

sở hữu:

> truyền `Vec<T>` qua function boundary thế nào.

```text
Backend
```

sở hữu:

> instruction nào thực hiện nó.

```text
Linker
```

sở hữu:

> binary cuối cùng bố trí thế nào.

---

# 132. Không được đảo ngược.

Ví dụ backend không được quyết định:

> `Vec<T>` có Copy hay không.

---

# 133. Đây là firewall quan trọng để Axiom không bị biến thành compiler phụ thuộc ISA.

---

# 134. Frozen invariants

```text
ACOMPARCH-20
Compiler modules form an acyclic dependency graph.

ACOMPARCH-21
Semantic meaning is owned by semantic layers.

ACOMPARCH-22
Physical representation is owned by representation/codegen layers.

ACOMPARCH-23
Frontend semantics must not depend on target ISA.

ACOMPARCH-24
Type semantics must not depend on physical register allocation.

ACOMPARCH-25
MIR must remain target-independent.

ACOMPARCH-26
LIR must remain ISA-independent.

ACOMPARCH-27
TargetBackend is the ISA portability boundary.

ACOMPARCH-28
ABI classification is target-dependent.

ACOMPARCH-29
Object representation is independent from frontend semantics.

ACOMPARCH-30
Linking is independent from source-level type checking.

ACOMPARCH-31
CompilerDB provides shared semantic query infrastructure.

ACOMPARCH-32
CompilerDB is not itself a semantic layer.

ACOMPARCH-33
Semantic IDs are stable identities and must not depend on memory addresses.

ACOMPARCH-34
Semantic objects should be immutable after publication where practical.

ACOMPARCH-35
Incremental queries track semantic dependencies.

ACOMPARCH-36
Parallel queries must preserve deterministic semantic results.

ACOMPARCH-37
Verification precedes optimization and code generation.

ACOMPARCH-38
Only Verified MIR may enter production code generation.

ACOMPARCH-39
Optimization failure must not invalidate semantic correctness.

ACOMPARCH-40
Backend failure must produce a diagnostic rather than invalid machine code.

ACOMPARCH-41
Object-writer failure must produce a diagnostic rather than a corrupt artifact.

ACOMPARCH-42
AI tooling cannot directly mutate semantic compiler state.

ACOMPARCH-43
AI-generated source is verified through the same compiler pipeline.

ACOMPARCH-44
Compiler diagnostics are structured semantic data.

ACOMPARCH-45
Architecture dependency violations are CI-detectable.

ACOMPARCH-46
Compiler implementation may use unsafe mechanisms internally under explicit contracts.

ACOMPARCH-47
Compiler memory management must not require tracing GC.

ACOMPARCH-48
Compiler caches are separate from semantic truth.

ACOMPARCH-49
Bootstrap implementation language must not define module semantics.

ACOMPARCH-50
Bootstrap-only dependencies must remain replaceable.

ACOMPARCH-51
Replacing a backend must not require frontend semantic changes.

ACOMPARCH-52
Replacing an object writer must not require frontend semantic changes.

ACOMPARCH-53
Replacing a linker must not require type-system changes.

ACOMPARCH-54
Adding a target must not require changing Core semantics solely for ISA accommodation.

ACOMPARCH-55
Every compiler subsystem has explicit input/output/invariant/dependency contracts.

ACOMPARCH-56
No generic miscellaneous layer may become an uncontrolled dependency sink.

ACOMPARCH-57
Compiler phase boundaries are observable through diagnostic and debug infrastructure.

ACOMPARCH-58
Semantic fingerprints and codegen fingerprints remain distinct.

ACOMPARCH-59
Revision-based incremental compilation cannot change language semantics.

ACOMPARCH-60
Self-hosted compiler architecture must use the same module contracts as bootstrap compiler.
```

---

# 135. Kiến trúc repository sau 269

```text
                         AXIOM REPOSITORY
                               │
        ┌──────────────────────┼──────────────────────┐
        │                      │                      │
     compiler                 std                  runtime
        │
        ▼
   CompilerDB
        │
        ├── Frontend
        │    ├── source
        │    ├── lexer
        │    ├── syntax
        │    ├── parser
        │    └── resolver
        │
        ├── Semantic
        │    ├── types
        │    ├── traits
        │    ├── consteval
        │    ├── HIR
        │    └── MIR
        │
        ├── Correctness
        │    ├── verify
        │    └── analysis
        │
        ├── Optimization
        │    └── optimize
        │
        ├── Physical
        │    ├── ABI
        │    ├── LIR
        │    └── codegen
        │
        ├── Targets
        │    └── backend
        │
        └── Binary
             ├── object
             └── linker
```

---

# 136. Ý nghĩa của task 269

Đến đây Axiom không còn chỉ có:

```text
"compiler pipeline"
```

mà đã có:

```text
module ownership
+
dependency boundaries
+
data ownership
+
semantic authority
+
incremental query model
+
bootstrap boundary
+
backend boundary
+
binary boundary
```

Đây chính là mức kiến trúc cần thiết để **AI agent bắt đầu tạo repository và implement compiler mà không tự phát minh lại architecture**.

---

## Task tiếp theo: **BOOTSTRAP-270 — AXIOM COMPILER DATA MODEL & CORE IR TYPES**

Task 270 sẽ đi xuống một tầng nữa: định nghĩa **các struct/enum/trait nội bộ cụ thể** mà compiler phải có, đặc biệt:

```text
Type
TypeId
Place
Operand
RValue
Statement
Terminator
BasicBlock
MIRFunction
Capability
Region
EffectSet
AliasFact
Layout
AbiSignature
LirInstruction
MachineIR
```

và quan trọng nhất là **quan hệ ownership giữa toàn bộ các object này**, để từ đó agent có thể bắt đầu viết **compiler data structures thật**, thay vì chỉ tạo folder/module rỗng.