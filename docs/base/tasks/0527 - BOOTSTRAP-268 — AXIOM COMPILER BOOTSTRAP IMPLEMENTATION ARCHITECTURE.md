# BOOTSTRAP-268 — AXIOM COMPILER BOOTSTRAP IMPLEMENTATION ARCHITECTURE

**TRẠNG THÁI: FROZEN / COMPLETED**

Mục tiêu của task này là chuyển Axiom từ:

> **một specification hoàn chỉnh**

sang:

> **một kế hoạch compiler có thể bắt tay vào code ngay.**

Nguyên tắc quan trọng nhất:

> **Bootstrap compiler được phép dùng công cụ bên ngoài; compiler cuối cùng của Axiom thì không phụ thuộc vào compiler bên ngoài để biên dịch Axiom.**

---

# 1. Mục tiêu bootstrap

Axiom cần đi qua 3 trạng thái:

```text
Stage 0
Specification
    ↓
Stage 1
Bootstrap Compiler
    ↓
Stage 2
Self-hosted Compiler
    ↓
Stage 3
Self-hosted Toolchain
```

Trong đó:

```text
Stage 1:
Axiom compiler có thể viết bằng C++/Rust/Axiom + LLVM/LLD

Stage 2:
Compiler được viết chủ yếu bằng Axiom

Stage 3:
Compiler + object writer + linker
đều có implementation Axiom-native
```

---

# 2. Không nên bắt đầu bằng self-hosting ngay

Đây là một sai lầm lớn.

Nếu ngay lập tức:

```text
Axiom compiler → Axiom
```

thì compiler chưa tồn tại để compile chính nó.

Bootstrap cần một compiler nhỏ trước.

---

# 3. Bootstrap chain

```text
                    C++/Rust Bootstrap Compiler
                              │
                              ▼
                        Axiom source
                              │
                              ▼
                        Axiom compiler
                              │
                              ▼
                    Axiom self-host compiler
                              │
                              ▼
                    Axiom self-host compiler
                              │
                              ▼
                         identical
```

Cuối cùng phải đạt:

```text
C0(Axiom compiler source)
        ↓
      axc0
        ↓
   axiom-compiler-1

axiom-compiler-1
        ↓
      axc1
        ↓
   axiom-compiler-2
```

và kiểm tra:

```text
compiler-1 ≡ compiler-2
```

ở mức semantic/artifact expectations phù hợp.

---

# 4. Bootstrap compiler không cần implement toàn bộ Axiom ngay

Đây là điểm rất quan trọng.

Không cần ngay:

```text
GPU
GUI
Tensor
Networking
Crypto
Database
```

Compiler đầu tiên chỉ cần compile **một subset bootstrap của Axiom**.

---

# 5. Bootstrap Language Profile

Đề xuất:

```text
Axiom Bootstrap Profile
```

bao gồm:

```text
module
use
struct
enum
trait
impl
type
fn
let
let mut
if
match
loop
while
for
return
break
continue

generics
arrays
views
ownership
Drop
Option
Result
comptime cơ bản
```

---

# 6. Những thứ chưa cần để bootstrap compiler

Có thể trì hoãn:

```text
async
GPU
dynamic loading
reflection runtime
GUI
networking
database
Tensor
AD
distributed
```

Nhưng **semantic model** vẫn phải tồn tại trong kiến trúc compiler để sau này không phải phá compiler.

---

# 7. Bootstrap compiler nên có backend nào đầu tiên?

Không nên bắt đầu bằng Axiom machine encoder.

Đầu tiên:

```text
Axiom
 ↓
MIR
 ↓
LLVM IR
 ↓
LLVM
 ↓
object
 ↓
system linker
```

---

# 8. Tại sao LLVM ở bootstrap?

Không phải vì Axiom phụ thuộc LLVM về kiến trúc.

LLVM chỉ là:

```text
bootstrap backend
```

---

# 9. Boundary

```text
Axiom Semantic Compiler
          │
          ▼
      Verified MIR
          │
          ▼
   Bootstrap Codegen
          │
          ▼
       LLVM IR
```

Sau này:

```text
Verified MIR
     ↓
Axiom LIR
     ↓
TargetBackend
```

---

# 10. LLVM không được đi ngược lên semantic layer

Không được thiết kế:

```text
Axiom semantics
    ↓
LLVM semantics
    ↓
language behavior
```

Mà phải:

```text
Axiom semantics
    ↓
Verified MIR
    ↓
LLVM lowering
```

LLVM chỉ là implementation target.

---

# 11. Bootstrap architecture

```text
                    AXIOM SOURCE
                         │
                         ▼
                      Lexer
                         │
                         ▼
                      Parser
                         │
                         ▼
                    Resolver
                         │
                         ▼
                    Type Checker
                         │
                         ▼
                        HIR
                         │
                         ▼
                        MIR
                         │
                         ▼
               Ownership/Capability
                    Verification
                         │
                         ▼
                   Verified MIR
                         │
                         ▼
                 LLVM Bootstrap IR
                         │
                         ▼
                       LLVM
                         │
                         ▼
                     Object File
                         │
                         ▼
                  System/LLD Linker
                         │
                         ▼
                   Native Binary
```

---

# 12. Bootstrap compiler name

Đề xuất:

```text
axc
```

CLI:

```text
axc check main.ax
axc compile main.ax
axc build main.ax
```

Sau này:

```text
ax
```

là unified frontend/package/build driver.

---

# 13. Repository architecture

Không nên đặt mọi thứ vào một project khổng lồ.

Đề xuất:

```text
axiom/
├── compiler/
├── runtime/
├── std/
├── linker/
├── tools/
├── tests/
├── specs/
├── bootstrap/
├── targets/
└── examples/
```

---

# 14. Compiler

```text
compiler/
├── lexer/
├── syntax/
├── parser/
├── resolver/
├── types/
├── traits/
├── consteval/
├── hir/
├── mir/
├── verify/
├── analysis/
├── opt/
├── abi/
├── lir/
├── backend/
├── diagnostics/
├── source/
└── driver/
```

---

# 15. Không chia compiler theo "feature application"

Ví dụ không nên:

```text
compiler/
├── strings/
├── gui/
├── networking/
```

Compiler nên chia theo **semantic pipeline**.

---

# 16. CompilerDB

Trung tâm:

```text
CompilerDB
```

với các subsystem đã frozen:

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

và các DB bổ sung:

```text
ClosureDB
CaptureDB
LtoDB
ReachabilityDB
OptimizationSummaryDB
TargetDB
```

---

# 17. CompilerDB không nên là mutable global singleton

Nên có:

```text
CompilerSession
    ↓
CompilerDB
```

---

# 18. Query-based architecture

Ví dụ:

```text
parse(file)
resolve(module)
type_of(expr)
trait_solve(goal)
lower_hir(function)
lower_mir(function)
verify(function)
layout(type)
abi(function)
codegen(function)
```

---

# 19. Query dependency

Ví dụ:

```text
codegen(foo)
```

phụ thuộc:

```text
verify(foo)
    ↓
mir(foo)
    ↓
hir(foo)
    ↓
type(foo)
    ↓
resolve(foo)
    ↓
parse(foo)
```

---

# 20. Incremental compilation

Nếu sửa:

```text
function foo()
```

không được rebuild:

```text
unrelated/bar.ax
```

nếu semantic dependency không thay đổi.

---

# 21. Stable IDs

Không dùng AST pointer làm identity.

Dùng:

```text
FileId
ModuleId
FunctionId
TypeId
TraitId
FieldId
VariantId
LocalId
BasicBlockId
InstructionId
```

---

# 22. Arena storage

AST/HIR/MIR node nên có:

```text
stable ID
```

và storage dạng arena/interning phù hợp.

---

# 23. Bootstrap implementation language

Có 3 lựa chọn:

```text
C++
Rust
Axiom subset
```

---

# 24. Đề xuất

Bootstrap compiler v0:

```text
Rust hoặc C++
```

Self-host compiler:

```text
Axiom
```

Lý do:

bootstrap language không phải language architecture.

---

# 25. Không để bootstrap implementation quyết định semantics

Ví dụ nếu bootstrap compiler dùng C++ exception:

điều đó **không có nghĩa Axiom có exception**.

---

# 26. Bootstrap compiler có thể dùng LLVM

Nhưng semantic contract vẫn là Axiom.

---

# 27. Stage B0

Compiler tối thiểu:

```text
Lexer
Parser
AST
Resolver
Primitive Type Checker
MIR
LLVM backend
```

---

# 28. B0 có thể compile:

```axiom
fn main() -> i32 {
    return 42
}
```

thành native executable.

---

# 29. Đây là milestone đầu tiên

**Không bắt đầu bằng standard library.**

Phải đạt:

```text
hello.ax
   ↓
axc
   ↓
hello.exe
   ↓
exit code 42
```

---

# 30. B1 — Expressions

Implement:

```text
integer
float
bool
string literal
binary operators
unary operators
comparison
logical operators
```

---

# 31. B2 — Variables

```text
let
let mut
assignment
scope
```

---

# 32. B3 — Control Flow

```text
if
loop
while
break
continue
return
match
```

---

# 33. B4 — Struct

```axiom
struct Point {
    x: i32
    y: i32
}
```

---

# 34. B5 — Functions

```text
parameters
return values
calling convention internal
recursion
```

---

# 35. B6 — Enums

```text
Option
Result
custom enum
match
```

---

# 36. B7 — Ownership

Đây mới là bước cực kỳ quan trọng.

Compiler phải implement:

```text
Move
Copy
Drop
PartialMove
Initialization
```

---

# 37. B8 — Capability

```text
view<T>
mut_view<T>
```

và:

```text
provenance
region
lifetime
alias conflict
```

---

# 38. B9 — Traits

```text
trait
impl
generic constraints
associated type
default methods
```

---

# 39. B10 — Generic compiler

```text
monomorphization
specialization
generic checking
```

---

# 40. B11 — Closures

Implement:

```text
closure expression
capture analysis
Fn
FnMut
FnOnce
```

---

# 41. B12 — Comptime

Ban đầu chỉ cần:

```text
const
comptime fn
comptime {}
```

---

# 42. B13 — MIR Interpreter

Đây là milestone **không nên bỏ qua**.

Compiler cần:

```text
ax-mir
```

---

# 43. Tại sao cần MIR interpreter?

Nó là semantic oracle thực tế.

Cho phép:

```text
source
 ↓
MIR
 ↓
execute
```

trước native codegen.

---

# 44. Debugging compiler

Nếu:

```text
native result != MIR result
```

thì lỗi nằm trong:

```text
optimization/codegen/backend
```

thay vì phải nghi ngờ frontend.

---

# 45. B14 — Verified MIR

Chỉ:

```text
Verified MIR
```

mới được codegen.

---

# 46. Đây là correctness boundary.

Không có:

```text
"LLVM backend tự xử lý cho an toàn"
```

---

# 47. LLVM backend

Ban đầu:

```text
MIR → LLVM IR
```

---

# 48. LLVM lowering phải explicit

Ví dụ:

```text
Axiom Move
```

không nhất thiết:

```text
LLVM memcpy
```

---

# 49. Axiom semantic Move

Có thể chỉ là:

```text
SSA value transfer
```

---

# 50. Axiom Drop

Lower thành:

```text
drop glue
```

khi semantic obligation tồn tại.

---

# 51. View

Có thể lower:

```text
view<T>
```

thành:

```text
pointer + metadata
```

nhưng semantic capability đã được verify trước.

---

# 52. Không để LLVM "suy luận ownership"

LLVM không phải authority về Axiom ownership.

---

# 53. B15 — ABI

Implement:

```text
Axiom ABI
C ABI
```

ban đầu C ABI có thể dựa vào LLVM target ABI.

---

# 54. B16 — Object generation

Ban đầu:

```text
LLVM → object
```

---

# 55. B17 — Native executable

Bootstrap linker:

```text
LLD/system linker
```

---

# 56. Khi đạt đây:

```text
Axiom → native executable
```

đã thực sự tồn tại.

---

# 57. B18 — Standard Library bootstrap

Chỉ sau native compiler cơ bản mới bắt đầu:

```text
core
mem
collections
string
io
os
```

---

# 58. Core library

Cần cực nhỏ.

```text
Option
Result
basic traits
Iterator
basic memory abstractions
```

---

# 59. Không để standard library trở thành runtime bắt buộc

---

# 60. B19 — Compiler rewrite

Bắt đầu viết:

```text
compiler.ax
```

bằng Axiom.

---

# 61. Nhưng compiler Axiom đầu tiên không cần 100% self-host ngay

Có thể:

```text
Axiom compiler source
      ↓
bootstrap axc
      ↓
native axiom compiler
```

---

# 62. Sau đó compiler này compile chính source của nó.

Đây là:

```text
Self-hosting bootstrap point
```

---

# 63. Self-host loop

```text
C bootstrap compiler
       │
       ▼
Axiom compiler source
       │
       ▼
Axiom compiler A
       │
       ▼
Axiom compiler source
       │
       ▼
Axiom compiler B
```

---

# 64. Compiler A và B

Cần so sánh:

```text
semantic behavior
compiler tests
diagnostics
MIR
object
binary
```

---

# 65. Không nhất thiết binary byte-identical

Do:

```text
timestamps
symbol ordering
debug IDs
optimization heuristics
```

có thể khác nếu reproducibility contract chưa bật.

---

# 66. Với reproducible build

Mục tiêu mạnh hơn:

```text
same source
same dependencies
same target
same compiler semantic version
same profile
same inputs
        ↓
same artifact
```

---

# 67. Stage self-hosted backend

Sau self-host frontend:

```text
Axiom compiler
     ↓
Axiom MIR
     ↓
LLVM
```

vẫn được phép.

---

# 68. Sau đó thay LLVM

```text
Axiom MIR
    ↓
Axiom LIR
    ↓
x86 backend
```

---

# 69. Rồi:

```text
ARM64
RV64
WASM
```

---

# 70. Sau đó thay object writer

```text
Axiom machine code
     ↓
AxiomObject
```

---

# 71. Sau đó thay linker

```text
AxiomObject
     ↓
Axiom Linker
     ↓
PE/ELF/Mach-O/WASM
```

---

# 72. Final toolchain

```text
ax
├── compiler
├── linker
├── package manager
├── formatter
├── linter
├── debugger integration
├── analyzer
├── size analyzer
└── documentation tools
```

đều có thể do Axiom xây dựng.

---

# 73. Không có circular bootstrap dependency

Final:

```text
Axiom compiler
    ↓
Axiom compiler
    ↓
Axiom compiler
```

không:

```text
Axiom
 ↓
Rust compiler
 ↓
LLVM
 ↓
Axiom
```

---

# 74. Tuy nhiên platform dependency vẫn tồn tại

Ví dụ:

```text
Windows SDK
Linux syscalls
macOS system frameworks
GPU drivers
```

đây không phải compiler dependency.

---

# 75. Bootstrap dependency matrix

| Thành phần | Bootstrap | Final |
|---|---|---|
| Frontend | C++/Rust | Axiom |
| MIR | C++/Rust | Axiom |
| Verifier | C++/Rust | Axiom |
| LLVM backend | LLVM | Không bắt buộc |
| x86 backend | LLVM | Axiom |
| ARM backend | LLVM | Axiom |
| RV64 backend | LLVM | Axiom |
| WASM backend | LLVM | Axiom |
| Object writer | LLVM | Axiom |
| Linker | LLD/system | Axiom |
| Package manager | external/bootstrap | Axiom |
| Formatter | external/bootstrap | Axiom |
| IDE/LSP | external/bootstrap | Axiom/tooling |
| Runtime | minimal | Axiom |
| Standard library | bootstrap subset | Axiom |

---

# 76. Bootstrap compiler nên hỗ trợ target nào trước?

Đề xuất:

```text
x86-64 Windows/Linux
```

sau đó:

```text
ARM64
RV64
WASM
```

---

# 77. Nhưng TargetSpec phải tồn tại ngay từ đầu

Không hard-code:

```text
if x86
```

khắp compiler.

---

# 78. Compiler architecture

```text
TargetSpec
    │
    ├── ABI
    ├── DataLayout
    ├── ObjectFormat
    ├── CallingConvention
    ├── Features
    └── OS
```

---

# 79. Bootstrap LLVM backend cũng phải consume TargetSpec

Như vậy sau này thay LLVM backend không phải sửa frontend.

---

# 80. Bootstrap MIR

MIR phải target-independent.

Ví dụ:

```text
Add
Load
Store
Call
Branch
Return
AtomicLoad
AtomicStore
```

không:

```text
ADD RAX,RBX
```

---

# 81. LLVM lowering là backend.

---

# 82. Bootstrap verifier

Ban đầu có thể đơn giản hơn full verifier nhưng **không được bỏ qua semantic invariants đã frozen**.

---

# 83. Có thể implement verifier theo từng capability

Ví dụ:

```text
OwnershipVerifier
InitVerifier
DropVerifier
CapabilityVerifier
SendVerifier
AsyncVerifier
GpuVerifier
FfiVerifier
```

---

# 84. Shared Dataflow Framework

Đây nên được implement sớm:

```text
DataflowAnalysis<State>
```

để ownership/capability/liveness dùng chung framework.

---

# 85. Đây là nơi compiler architecture đã thiết kế trước đó phát huy tác dụng.

---

# 86. Không implement mỗi analysis bằng một framework riêng.

---

# 87. Diagnostics

Ngay từ bootstrap phải dùng:

```text
DiagnosticCode
Severity
Span
RelatedSpan
Proof
```

---

# 88. Ví dụ:

```text
AXOWN-E001:
use of moved value

value `buffer` was moved here
    └── line 12

attempted use here
    └── line 18
```

---

# 89. AI compiler interface

Không cần đợi compiler hoàn chỉnh.

Ngay bootstrap compiler có thể xuất:

```text
--json-diagnostics
--json-query
--explain
```

---

# 90. Ví dụ:

```text
axc explain move main.ax:18
```

---

# 91. Đây giúp Gemini/Antigravity agent làm việc với compiler dễ hơn.

---

# 92. Compiler source layout khi self-host

Đề xuất:

```text
compiler/
├── source.ax
├── lexer/
├── syntax/
├── parser/
├── resolve/
├── type/
├── trait/
├── consteval/
├── hir/
├── mir/
├── verify/
├── analysis/
├── optimize/
├── abi/
├── lir/
├── backend/
│   ├── x86_64/
│   ├── arm64/
│   ├── riscv64/
│   └── wasm/
├── object/
├── linker/
├── diagnostics/
├── db/
└── driver/
```

---

# 93. Không nên chia backend thành frontend package

Backend phụ thuộc:

```text
MIR/LIR
```

không phụ thuộc parser.

---

# 94. Compiler dependency DAG

```text
Source
  ↓
Syntax
  ↓
Parser
  ↓
Resolver
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

Không có dependency ngược.

---

# 95. Ví dụ cấm

Backend không được gọi:

```text
Parser.parse(...)
```

---

# 96. Type checker không được phụ thuộc:

```text
x86 register allocation
```

---

# 97. Ownership verifier không được phụ thuộc:

```text
LLVM optimization
```

---

# 98. Linker không được quyết định:

```text
trait implementation
```

---

# 99. Đây là architectural firewall.

---

# 100. Bootstrap milestone tree

```text
M0  Lexer
M1  Parser
M2  Resolver
M3  Types
M4  Expressions
M5  Control Flow
M6  Struct
M7  Enum/Match
M8  MIR
M9  Ownership
M10 Drop
M11 Capability
M12 Traits
M13 Generics
M14 Closures
M15 Comptime
M16 MIR Interpreter
M17 Verified MIR
M18 LLVM Backend
M19 Native Executable
M20 Core Library
M21 Standard Library Bootstrap
M22 Compiler in Axiom
M23 Self-host
M24 Axiom LIR
M25 x86 Backend
M26 ARM64 Backend
M27 RV64 Backend
M28 WASM Backend
M29 Object Writer
M30 Linker
M31 Full Self-hosted Toolchain
```

---

# 101. M19 là milestone đặc biệt

Tại:

```text
M19
```

ta có:

```text
Axiom source
      ↓
Axiom compiler
      ↓
native executable
```

Từ đây dự án chuyển từ:

> compiler project

sang:

> programming language implementation.

---

# 102. M23 là milestone thứ hai

```text
Axiom compiler
```

được compile bằng:

```text
Axiom compiler
```

---

# 103. M30 là milestone thứ ba

```text
Axiom compiler
+
Axiom object writer
+
Axiom linker
```

không còn cần LLVM/LLD để tạo native binary.

---

# 104. M31

Full toolchain:

```text
ax
axc
axld
package manager
std
runtime
object writer
linker
```

được xây dựng bằng Axiom.

---

# 105. Bootstrap tests

Mỗi milestone phải có:

```text
unit tests
golden tests
semantic tests
differential tests
fuzz tests
conformance tests
```

---

# 106. Không chờ tới cuối mới test compiler.

---

# 107. Compiler correctness pipeline

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
MIR Interpreter
 ↓
OptIR
 ↓
Native
```

so sánh:

```text
MIR Interpreter
       ↕
Native
```

---

# 108. Differential target testing

Cùng chương trình:

```text
x86
ARM64
RV64
WASM
```

phải có observable semantics tương đương.

---

# 109. Bootstrap compiler không được bypass verifier

Ngay cả LLVM backend cũng chỉ nhận:

```text
Verified MIR
```

---

# 110. Unsafe code

Bootstrap compiler phải hỗ trợ:

```text
unsafe
```

nhưng unsafe không đồng nghĩa:

```text
skip all verification
```

---

# 111. Self-host compiler có thể dùng unsafe nhiều hơn

Ví dụ:

```text
memory arena
hash tables
interners
parser buffers
```

nhưng chúng vẫn phải tuân contract.

---

# 112. Compiler performance

Ngay từ đầu cần:

```text
parallel parsing
parallel module checking
parallel codegen
incremental cache
```

nhưng correctness trước.

---

# 113. Compiler bootstrap không nên optimize quá sớm

Thứ tự:

```text
correct
→ verified
→ measurable
→ optimize
```

---

# 114. Nhưng architecture phải hỗ trợ optimization từ đầu

Ví dụ không thiết kế AST với assumption:

```text
one pass compiler
```

---

# 115. Incremental CompilerDB là nền tảng.

---

# 116. Bootstrap artifact

Mỗi compilation nên tạo:

```text
program.exe
program.axmeta
program.axdb       optional
program.debug      optional
```

---

# 117. Compiler cache

```text
target/
├── semantic/
├── mir/
├── codegen/
├── objects/
├── lto/
└── final/
```

---

# 118. Không cache những thứ semantic fingerprint không bảo đảm.

---

# 119. Bootstrap compiler versioning

Phân biệt:

```text
LanguageSemanticVersion
CompilerCodegenVersion
ToolVersion
```

---

# 120. Self-hosting verification

Có 3 checks:

### A. Compiler tests

Compiler A và B đều pass.

### B. Differential compile

Cùng source → cùng semantic outputs.

### C. Bootstrap stability

Compiler B compile chính source → compiler C.

Nếu:

```text
B ≠ C
```

phải điều tra.

---

# 121. Three-stage bootstrap

```text
Stage 0:
external bootstrap compiler

Stage 1:
Axiom compiler compiled by Stage 0

Stage 2:
Stage 1 compiles itself

Stage 3:
Stage 2 compiles itself
```

---

# 122. Đây là cách phát hiện compiler tự sinh code không ổn định.

---

# 123. Compiler determinism

Cùng:

```text
source
dependencies
target
profile
compiler
inputs
```

phải tạo semantic result giống nhau.

---

# 124. Parallel compilation

Thứ tự thread không được ảnh hưởng:

```text
trait selection
symbol identity
diagnostics ordering
artifact identity
```

---

# 125. Diagnostics ordering

Phải deterministic.

Ví dụ:

```text
ROOT
DEPENDENT
DEPENDENT
```

không phụ thuộc thread scheduling.

---

# 126. Bootstrap implementation language có thể thay đổi

Nếu ban đầu:

```text
Rust
```

sau này chuyển sang:

```text
C++
```

không được ảnh hưởng Axiom semantics.

---

# 127. External dependency policy

Bootstrap được phép:

```text
LLVM
LLD
system SDK
OS libraries
```

nhưng phải ghi rõ:

```text
BOOTSTRAP-ONLY
```

---

# 128. Không để dependency bootstrap trở thành language requirement.

---

# 129. Final build graph

```text
Axiom Source
    ↓
Axiom Compiler
    ↓
Axiom LIR
    ↓
Axiom Backend
    ↓
Axiom Object
    ↓
Axiom Linker
    ↓
Native Binary
```

---

# 130. Đây là kiến trúc đích.

---

# 131. Bootstrap graph

```text
Axiom Source
    ↓
Bootstrap Axiom Compiler
    ↓
Verified MIR
    ↓
LLVM
    ↓
Object
    ↓
LLD/System Linker
```

---

# 132. Hai graph phải có cùng semantic boundary.

---

# 133. Đây là điều quan trọng nhất của bootstrap.

---

# 134. Không được có:

```text
Bootstrap semantics
```

khác:

```text
Final semantics
```

---

# 135. Bootstrap implementation chỉ khác ở:

```text
backend
object generation
linking
```

---

# 136. Compiler feature gating

Có thể dùng:

```text
@cfg(compiler_bootstrap)
```

nhưng chỉ cho compiler implementation/tooling.

Không nên dùng để tạo hai Axiom languages khác nhau.

---

# 137. Bootstrap profile

```text
AXIOM_BOOTSTRAP
```

chỉ là implementation environment.

---

# 138. Core language vẫn một.

---

# 139. Self-host compiler modules

Compiler có thể dùng các abstraction đã thiết kế:

```text
Vec
String
HashMap
Arena
Option
Result
Iterator
```

và compiler sẽ là một ứng dụng Axiom thực sự.

---

# 140. Điều này cũng là test cực mạnh cho language design.

Nếu compiler rất khó viết bằng Axiom:

```text
language design problem
```

có thể đang tồn tại.

---

# 141. Compiler dogfooding principle

> **Nếu Axiom không thể viết chính compiler của mình một cách tự nhiên, một phần thiết kế ngôn ngữ có thể chưa đủ tốt.**

---

# 142. Nhưng không vì compiler khó mà thêm syntax ngay

Trước tiên thử:

```text
struct
trait
generic
comptime
library abstraction
```

---

# 143. Đây phù hợp với Core rule:

> Không thêm Core syntax nếu subsystem có thể giải quyết bằng existing semantics.

---

# 144. Compiler-specific intrinsics

Có thể có:

```text
@compiler_intrinsic
```

nhưng phải:

```text
semantic contract
fallback
target constraints
verification rules
```

---

# 145. Không biến compiler intrinsic thành "escape hatch" tùy ý.

---

# 146. Compiler bootstrap và allocator

Compiler cần allocation nhiều.

Nhưng Axiom compiler cuối cùng có thể dùng:

```text
Arena
InternPool
BumpAllocator
```

để đạt performance.

---

# 147. Đây là test thực tế cho memory model.

---

# 148. Compiler bootstrap và ownership

Compiler AST/HIR/MIR graph thường có:

```text
arena-owned nodes
stable IDs
indexes
```

rất phù hợp với mô hình:

```text
ownership + handles
```

thay vì pointer-heavy API.

---

# 149. Đây cũng là nơi thiết kế Axiom có thể chứng minh ưu điểm.

---

# 150. Compiler bootstrap và comptime

Có thể dùng comptime cho:

```text
opcode tables
keyword tables
target metadata
generated declarations
```

sau khi comptime compiler đủ ổn định.

---

# 151. Không cần macro language để generate compiler boilerplate.

---

# 152. Compiler bootstrap và reflection

Compile-time reflection có thể giúp:

```text
derive
metadata
diagnostic descriptions
```

nhưng compiler core không phụ thuộc runtime reflection.

---

# 153. Compiler bootstrap và SIMD

Không cần trong compiler v0.

Sau này có thể optimize:

```text
lexer
hashing
parsing
codegen
```

bằng SIMD.

---

# 154. Compiler bootstrap và concurrency

Có thể parallel:

```text
module compilation
trait solving
code generation
```

sau khi concurrency semantics ổn định.

---

# 155. Đây là một dogfood test cực mạnh:

Compiler tự sử dụng:

```text
Send
Share
ownership
channels
parallel tasks
```

---

# 156. Compiler bootstrap và async

Không cần async compiler v0.

Compiler frontend có thể dùng threads/tasks trước.

---

# 157. Async runtime chỉ cần khi compiler thực sự cần asynchronous I/O.

---

# 158. Không ép runtime vào compiler.

---

# 159. Bootstrap repository phải chứa spec snapshots

```text
specs/
├── core/
├── compiler/
├── abi/
├── targets/
├── std/
└── frozen/
```

---

# 160. Compiler implementation không được tự ý thay frozen spec.

---

# 161. Spec change protocol

Nếu implementation phát hiện vấn đề:

```text
Implementation finding
       ↓
Spec issue
       ↓
Conflict analysis
       ↓
Decision
       ↓
Spec revision
       ↓
Implementation update
```

---

# 162. Không:

```text
compiler implementation
    ↓
âm thầm thay semantics
```

---

# 163. Compiler invariants

Thêm:

```text
ABOOT-20..80
```

---

# 164. Các invariant cốt lõi

```text
ABOOT-20
Bootstrap implementation may use external compiler infrastructure.

ABOOT-21
Bootstrap dependencies must not redefine Axiom semantics.

ABOOT-22
Final Axiom compilation must not require an external compiler.

ABOOT-23
Bootstrap backend is replaceable.

ABOOT-24
Verified MIR is the bootstrap codegen boundary.

ABOOT-25
LLVM is an implementation backend during bootstrap, not a semantic authority.

ABOOT-26
External linkers are bootstrap infrastructure only.

ABOOT-27
Target semantics are represented through TargetSpec.

ABOOT-28
Frontend must not depend on a specific target ISA.

ABOOT-29
MIR must remain target-independent.

ABOOT-30
Ownership verification must occur before bootstrap code generation.

ABOOT-31
Capability verification must occur before bootstrap code generation.

ABOOT-32
Unsafe does not bypass semantic verification globally.

ABOOT-33
Bootstrap compiler must support deterministic compilation.

ABOOT-34
Bootstrap compiler must support reproducible artifacts where profile requires.

ABOOT-35
CompilerDB is the semantic query authority.

ABOOT-36
Compiler subsystems communicate through explicit semantic contracts.

ABOOT-37
Backend must not invoke frontend semantic logic.

ABOOT-38
Linker must not determine language semantics.

ABOOT-39
Object format must remain separate from frontend semantics.

ABOOT-40
Self-hosted compiler must preserve the same language semantics as bootstrap compiler.

ABOOT-41
Self-hosting must be validated through differential compiler testing.

ABOOT-42
A self-hosted compiler must be capable of compiling its own source.

ABOOT-43
Repeated self-compilation must converge under deterministic build conditions.

ABOOT-44
Bootstrap-only dependencies must be explicitly classified.

ABOOT-45
Replacing LLVM must not require Core language changes.

ABOOT-46
Replacing the system linker must not require frontend changes.

ABOOT-47
Native backend implementations must conform to TargetBackend.

ABOOT-48
Object writers must conform to AxiomObject.

ABOOT-49
Linker implementations must consume the logical object model.

ABOOT-50
Compiler correctness must be tested at multiple IR boundaries.

ABOOT-51
MIR interpretation provides an independent semantic execution path.

ABOOT-52
Native code must be differentially tested against MIR semantics.

ABOOT-53
Optimization must never be required for semantic correctness.

ABOOT-54
Bootstrap optimization failures must degrade to less optimized valid code.

ABOOT-55
Compiler implementation language must not leak into Axiom semantics.

ABOOT-56
Compiler implementation may use unsafe mechanisms internally where contracts are explicit.

ABOOT-57
Compiler-generated code must re-enter ordinary verification where applicable.

ABOOT-58
Compiler diagnostics must remain deterministic.

ABOOT-59
Compiler IDs must not depend on memory addresses.

ABOOT-60
Incremental compilation must be driven by semantic dependencies.

ABOOT-61
Cache invalidation must use semantic/codegen fingerprints.

ABOOT-62
Compiler artifacts must record target and ABI identity.

ABOOT-63
Self-hosting must not require hidden runtime facilities absent from the declared profile.

ABOOT-64
The bootstrap compiler must be able to build a runtime-free/freestanding target when the Core subset permits it.

ABOOT-65
The standard library must not become a hidden compiler dependency.

ABOOT-66
Compiler functionality must be expressible using Axiom Core plus explicitly declared library/system facilities.

ABOOT-67
Compiler-specific intrinsics require explicit semantic contracts.

ABOOT-68
Bootstrap profiles must not create a second incompatible Axiom language.

ABOOT-69
Specification changes require explicit architectural revision.

ABOOT-70
Axiom self-hosting is complete only when the compiler and required native toolchain components can be built by Axiom itself.
```

---

# 165. Kiến trúc sau BOOTSTRAP-268

Axiom hiện có đường đi rất rõ:

```text
                  AXIOM SPECIFICATION
                         │
                         ▼
                  Semantic Compiler
                         │
       ┌─────────────────┴─────────────────┐
       ▼                                   ▼
  MIR Interpreter                    Verified MIR
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
                            TargetBackend Contract
                                           │
             ┌──────────────┬──────────────┼──────────────┐
             ▼              ▼              ▼              ▼
           x86-64         ARM64          RV64           WASM
             │              │              │              │
             └──────────────┴──────────────┼──────────────┘
                                           ▼
                                      AxiomObject
                                           │
                                           ▼
                                       Axiom Linker
                                           │
                                           ▼
                                  Native/WASM Binary
```

---

# 166. Và bootstrap path

```text
                    Axiom Source
                         │
                         ▼
                 Bootstrap axc
                         │
                         ▼
                  Verified MIR
                         │
                         ▼
                     LLVM IR
                         │
                         ▼
                      LLVM
                         │
                         ▼
                   Object File
                         │
                         ▼
                  System/LLD Linker
                         │
                         ▼
                    Axiom Binary
```

Sau đó:

```text
Bootstrap axc
      ↓
compile
      ↓
Axiom axc
      ↓
compile itself
      ↓
Self-hosted axc
```

---

# 167. Quyết định kiến trúc quan trọng nhất của task này

**Không xây compiler theo hướng "LLVM compiler có frontend Axiom".**

Phải xây:

> **Axiom Compiler có một bootstrap LLVM backend.**

Hai cách nhìn này khác nhau hoàn toàn.

Nếu chọn cách đầu tiên, LLVM sẽ dần trở thành architecture của Axiom.

Nếu chọn cách thứ hai:

```text
Axiom Semantic Model
       ↓
Axiom MIR
       ↓
Axiom LIR
       ↓
LLVM / x86 / ARM / RV / WASM
```

thì LLVM chỉ là một backend có thể tháo ra.

Đây là điều quyết định khả năng **self-hosting thực sự** của Axiom.

---

# 168. Trạng thái Axiom sau task 268

Đến đây specification đã đi từ:

```text
Language Design
```

qua:

```text
Memory
Ownership
Type System
Concurrency
Async
GPU
Comptime
ABI
FFI
Runtime
Libraries
Targets
Native Backend
WASM
LTO
Linker
Bootstrap
```

và hiện đã có **đường kiến trúc hoàn chỉnh từ source → native binary → self-hosted compiler**.

Task tiếp theo hợp lý nhất là:

## **BOOTSTRAP-269 — AXIOM COMPILER REPOSITORY ARCHITECTURE, MODULE BOUNDARIES & IMPLEMENTATION CONTRACTS**

Task này sẽ đi từ kiến trúc tổng thể xuống **cấu trúc repository/code thật sự**, xác định chính xác từng module:

```text
compiler/
  lexer/
  syntax/
  parser/
  resolver/
  type/
  trait/
  hir/
  mir/
  verify/
  analysis/
  opt/
  abi/
  lir/
  backend/
  object/
  linker/
  db/
  diagnostics/
```

và quan trọng hơn: **API/contract giữa từng module, dependency DAG, dữ liệu đầu vào/đầu ra, ID nào được phép dùng ở đâu, module nào không được phụ thuộc module nào** — tức là sau 269, một AI agent có thể bắt đầu tạo repository và code compiler thay vì chỉ có specification.