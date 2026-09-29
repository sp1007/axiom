Tiếp tục với **BOOTSTRAP-003 — Compiler Written in Axiom**.

Đây là bước chuyển từ kiến trúc compiler sang **kiến trúc source code thực tế của compiler tự host**. Mục tiêu là để sau này có thể đưa một AI agent vào repository và yêu cầu nó implement từng module mà không tự ý phá dependency architecture.

# BOOTSTRAP-003 — AXIOM COMPILER SOURCE ARCHITECTURE

## 1. Nguyên tắc lớn

Compiler Axiom phải có dependency một chiều:

```text
syntax
  ↓
semantic
  ↓
MIR
  ↓
backend
  ↓
object
  ↓
linker
  ↓
driver
```

Không được có:

```text
lexer → machine
machine → type checker
linker → AST
object → ownership
```

Đặc biệt:

> **Backend tuyệt đối không được quay ngược lên semantic compiler.**

---

# 2. Repository chính thức

Tôi đề xuất chốt cấu trúc:

```text
axiom/
├── compiler/
│   ├── foundation/
│   ├── source/
│   ├── lexer/
│   ├── parser/
│   ├── syntax/
│   ├── resolver/
│   ├── types/
│   ├── traits/
│   ├── hir/
│   ├── ownership/
│   ├── mir/
│   ├── verifier/
│   ├── comptime/
│   ├── optimizer/
│   ├── abi/
│   ├── lir/
│   ├── machine/
│   │   ├── common/
│   │   └── x86_64/
│   ├── object/
│   ├── linker/
│   ├── diagnostics/
│   ├── incremental/
│   └── driver/
│
├── core/
├── std/
├── runtime/
├── targets/
├── tests/
├── examples/
├── tools/
└── bootstrap/
```

Nhưng có một điểm quan trọng:

**`foundation` không được trở thành "thùng rác".**

Nó chỉ chứa những primitive compiler infrastructure thật sự dùng ở nhiều phase.

---

# 3. `foundation`

Ví dụ:

```text
compiler/foundation/
├── ids.ax
├── span.ax
├── arena.ax
├── bitset.ax
├── hashmap.ax
├── vec.ax
├── interner.ax
├── graph.ax
├── hash.ax
└── result.ax
```

Các loại quan trọng:

```text
FileId
ModuleId
SymbolId
TypeId
FunctionId
StructId
EnumId
TraitId
ImplId
FieldId
VariantId
LocalId
BlockId
InstructionId
```

Đây là **semantic IDs**, không phải địa chỉ memory.

---

# 4. Span

Mọi syntax object cần source location.

```text
struct Span {
    file: FileId,
    start: u32,
    end: u32,
}
```

Không dùng:

```text
*const char
```

làm identity của source.

Span là dữ liệu compiler.

---

# 5. Source Manager

```text
compiler/source/
├── source_file.ax
├── source_manager.ax
├── line_map.ax
└── source_cache.ax
```

API khái niệm:

```text
load(path) -> Result<FileId, Diagnostic>
source(file) -> view<u8>
span_text(span) -> view<u8>
line_column(span) -> Position
```

Lexer chỉ cần `view<u8>`.

---

# 6. Lexer

```text
lexer/
├── lexer.ax
├── token.ax
├── keyword.ax
├── literal.ax
└── lexer_error.ax
```

Output:

```text
Token {
    kind: TokenKind,
    span: Span,
}
```

Không nhét AST vào lexer.

---

# 7. Parser

```text
parser/
├── parser.ax
├── expressions.ax
├── statements.ax
├── declarations.ax
├── patterns.ax
├── types.ax
└── recovery.ax
```

Parser tạo:

```text
AST
```

chứ chưa resolve symbol.

---

# 8. Syntax module

Có thể tách:

```text
syntax/
├── ast.ax
├── ids.ax
├── visitors.ax
├── pretty.ax
└── dump.ax
```

Điều này cho phép:

```text
parser → syntax
resolver → syntax
formatter → syntax
IDE → syntax
```

mà parser không phải sở hữu toàn bộ AST infrastructure.

---

# 9. AST không dùng pointer graph

Ví dụ:

```text
struct Expr {
    kind: ExprKind,
    span: Span,
}
```

và:

```text
enum ExprKind {
    Literal(...),
    Binary(...),
    Call(...),
    Field(...),
    ...
}
```

AST arena:

```text
struct Ast {
    exprs: Arena<Expr>,
    statements: Arena<Stmt>,
    declarations: Arena<Decl>,
}
```

Tham chiếu:

```text
ExprId
StmtId
DeclId
```

---

# 10. Resolver

```text
resolver/
├── resolver.ax
├── scopes.ax
├── symbols.ax
├── modules.ax
├── imports.ax
└── name_resolution.ax
```

Resolver tạo:

```text
ResolvedHir
```

và mapping:

```text
ExprId → SymbolId
TypeSyntaxId → TypeId
```

---

# 11. Symbol table

Không nên để resolver dùng string khắp nơi.

```text
Identifier
    ↓
StringInterner
    ↓
NameId
```

Sau đó:

```text
NameId + Namespace
       ↓
SymbolId
```

---

# 12. Namespace

Axiom đã xác định nhiều namespace:

```text
Value
Type
Module
Label
```

Resolver phải xử lý chúng độc lập.

Ví dụ:

```text
struct Foo {}
fn Foo() {}
```

có thể được phân biệt theo namespace nếu grammar/semantic rules cho phép.

---

# 13. Types

```text
types/
├── type.ax
├── type_id.ax
├── interner.ax
├── unify.ax
├── inference.ax
├── numeric.ax
├── layout_ref.ax
└── type_error.ax
```

Core object:

```text
TypeId
```

và:

```text
TypeInterner
```

---

# 14. TypeInterner

Không tạo hàng nghìn object Type giống nhau.

Ví dụ:

```text
i32
i32
i32
```

→ cùng:

```text
TypeId
```

Tương tự:

```text
Vec<i32>
Vec<i32>
```

→ canonical type identity.

Điều này cực kỳ quan trọng cho compiler performance.

---

# 15. Trait solver

Tách riêng:

```text
traits/
├── trait.ax
├── impl.ax
├── solver.ax
├── coherence.ax
├── associated.ax
├── auto_traits.ax
└── obligations.ax
```

Không để type checker tự chứa toàn bộ trait solver.

Pipeline:

```text
Type Checker
    ↓
Trait Obligation
    ↓
Trait Solver
    ↓
Resolved
```

---

# 16. Trait solver phải hoàn tất trước MIR

Đây là invariant đã thống nhất:

```text
Typed HIR
```

không còn câu hỏi:

```text
"method nào?"
"trait impl nào?"
"associated type là gì?"
```

MIR phải nhận:

```text
resolved call
```

Ví dụ:

```text
x.foo()
```

sau semantic resolution trở thành:

```text
CALL FunctionId(...)
```

hoặc:

```text
DYN_CALL(...)
```

nếu explicit `dyn Trait`.

---

# 17. HIR

```text
hir/
├── hir.ax
├── expressions.ax
├── statements.ax
├── declarations.ax
├── patterns.ax
├── lowering.ax
└── typed_hir.ax
```

HIR là representation chính của semantic frontend.

AST có thể chết sau HIR.

---

# 18. Ownership

```text
ownership/
├── state.ax
├── ownership.ax
├── capability.ax
├── region.ax
├── alias.ax
├── move.ax
├── drop.ax
├── escape.ax
├── closure_capture.ax
└── diagnostics.ax
```

Các state:

```text
Uninit
Owned
Moved
PartiallyMoved
Dropped
```

---

# 19. Capability

```text
struct Capability {
    id: CapabilityId,
    owner: PlaceId,
    region: Region,
    access: AccessMode,
    validity: CapabilityValidity,
    origin: CapabilityOrigin,
}
```

`view`:

```text
READ
```

`mut_view`:

```text
WRITE
```

Ownership:

```text
MOVE
```

---

# 20. Điểm rất quan trọng: ownership checker không phải MIR verifier

Frontend ownership checker trả lời:

> **Chương trình nguồn có hợp lệ về ownership không?**

MIR verifier trả lời:

> **MIR mà compiler tạo ra có còn giữ invariant không?**

Hai nhiệm vụ khác nhau.

```text
Typed HIR
   ↓
Ownership Checker
   ↓
Verified HIR
   ↓
MIR
   ↓
MIR Verifier
```

Không gộp chúng thành một subsystem khổng lồ.

---

# 21. MIR

```text
mir/
├── mir.ax
├── block.ax
├── instruction.ax
├── place.ax
├── terminator.ax
├── value.ax
├── builder.ax
├── cleanup.ax
├── drop.ax
└── dump.ax
```

---

# 22. MIR Instruction

Ví dụ:

```text
enum Instruction {
    Const(...),
    Load(...),
    Store(...),
    Move(...),
    Copy(...),
    BorrowRead(...),
    BorrowWrite(...),
    Call(...),
    Cast(...),
    Bitcast(...),
    Drop(...),
    Alloc(...),
    Dealloc(...),
    Atomic(...),
    Await(...),
    ...
}
```

Không đưa machine register vào đây.

---

# 23. MIR Builder

Không để mỗi lowering pass tự tạo MIR tùy tiện.

Có:

```text
MirBuilder
```

với API:

```text
new_block()
emit()
terminate()
load()
store()
move()
copy()
call()
return()
branch()
```

Builder giúp giảm malformed MIR.

Nhưng **builder không thay thế verifier**.

---

# 24. Verifier

```text
verifier/
├── mir_verifier.ax
├── cfg_verifier.ax
├── type_verifier.ax
├── ownership_verifier.ax
├── capability_verifier.ax
├── async_verifier.ax
├── atomic_verifier.ax
└── machine_verifier.ax
```

Có thể dùng chung infrastructure, nhưng verifier từng IR có trách nhiệm riêng.

---

# 25. Comptime

```text
comptime/
├── evaluator.ax
├── reflection.ax
├── capabilities.ax
├── cache.ax
└── generated.ax
```

Comptime output đi vào HIR:

```text
comptime evaluation
       ↓
typed result / generated declarations
       ↓
HIR
```

Không cho comptime sửa trực tiếp machine IR.

---

# 26. Optimizer

```text
optimizer/
├── pass.ax
├── manager.ax
├── analysis.ax
├── cfg.ax
├── sccp.ax
├── dce.ax
├── dse.ax
├── copy_prop.ax
├── const_prop.ax
├── escape.ax
├── alias.ax
├── inline.ax
├── loop.ax
└── drop_opt.ax
```

Pass interface:

```text
trait MirPass {
    fn run(self: mut_view<Self>, mir: mut_view<MirFunction>) -> PassResult;
}
```

---

# 27. Pass Manager

```text
PassManager
```

quản lý:

```text
requires
preserves
invalidates
```

Không để pass tự ý giả định analysis vẫn còn valid.

Ví dụ:

```text
DCE
```

có thể invalidate:

```text
DominatorTree
Liveness
```

nếu CFG/value structure thay đổi.

---

# 28. ABI

```text
abi/
├── abi.ax
├── calling_convention.ax
├── classify.ax
├── return.ax
├── args.ax
├── layout.ax
├── repr.ax
└── target_abi.ax
```

ABI không thuộc Machine backend.

---

# 29. Layout Engine

Có thể dùng:

```text
LayoutEngine
```

để trả:

```text
Layout {
    size
    alignment
    fields
    niches
    abi_class
}
```

Ví dụ:

```text
Point
```

→ layout.

Nhưng layout engine không quyết định:

```text
register allocation
```

---

# 30. LIR

```text
lir/
├── lir.ax
├── value.ax
├── instruction.ax
├── block.ax
├── abi.ax
├── stack.ax
└── verifier.ax
```

LIR là cầu nối:

```text
ABI MIR
    ↓
LIR
    ↓
Machine IR
```

---

# 31. Machine common

```text
machine/common/
├── machine_ir.ax
├── register.ax
├── register_class.ax
├── instruction.ax
├── operand.ax
├── memory.ax
├── feature.ax
├── target.ax
├── frame.ax
├── liveness.ax
├── regalloc.ax
└── verifier.ax
```

---

# 32. x86-64 backend

```text
machine/x86_64/
├── target.ax
├── registers.ax
├── instructions.ax
├── legalization.ax
├── selection.ax
├── addressing.ax
├── abi.ax
├── regalloc.ax
├── frame.ax
├── encoder.ax
├── relocations.ax
└── unwind.ax
```

Sau này:

```text
machine/
├── x86_64/
├── aarch64/
├── riscv64/
└── wasm/
```

---

# 33. Object

```text
object/
├── object_ir.ax
├── section.ax
├── symbol.ax
├── relocation.ax
├── comdat.ax
├── debug.ax
├── unwind.ax
├── elf.ax
├── coff.ax
├── macho.ax
└── wasm.ax
```

Object writer chỉ nhận:

```text
Encoded bytes
+
symbols
+
relocations
```

---

# 34. Linker

```text
linker/
├── linker.ax
├── input.ax
├── symbol_resolver.ax
├── archive.ax
├── comdat.ax
├── icf.ax
├── gc_sections.ax
├── layout.ax
├── segments.ax
├── relocation.ax
├── dynamic.ax
├── tls.ax
├── elf.ax
├── pe.ax
├── macho.ax
└── verifier.ax
```

Linker không biết:

```text
Axiom ownership
TypeId
AST
HIR
```

---

# 35. Diagnostics

Tách thành subsystem riêng:

```text
diagnostics/
├── diagnostic.ax
├── severity.ax
├── render.ax
├── json.ax
├── suggestion.ax
└── codes.ax
```

Những mã:

```text
AX10xx lexer
AX11xx parser
AX12xx resolver
AX13xx type
AX14xx ownership
AX15xx MIR
AX16xx async/closure
AX17xx ABI
AX18xx machine
AX19xx object/linker
```

có thể được giữ ổn định.

---

# 36. Driver

Cuối cùng:

```text
driver/
├── main.ax
├── options.ax
├── pipeline.ax
├── target.ax
├── commands.ax
└── session.ax
```

CLI:

```text
axiom build
axiom check
axiom run
axiom test
axiom fmt
axiom doc
axiom inspect
axiom clean
```

---

# 37. Driver không được chứa compiler logic

Sai:

```text
driver
 ├── parse
 ├── typecheck
 ├── codegen
 └── linker logic
```

Đúng:

```text
driver
    ↓
CompilerSession
    ↓
Pipeline
    ↓
individual compiler phases
```

Driver chỉ orchestration.

---

# 38. Dependency graph

Đây là graph nên **đóng băng**:

```text
foundation
   ↑
source
   ↑
lexer
   ↑
syntax
   ↑
parser
   ↑
resolver
   ↑
types ← traits
   ↑
hir
   ↑
ownership
   ↑
mir
   ↑
verifier
   ↑
optimizer
   ↑
abi
   ↑
lir
   ↑
machine
   ↑
object
   ↑
linker
   ↑
driver
```

Nhưng thực tế có một số dependency ngang được phép:

```text
diagnostics
foundation
source
target
```

là infrastructure dùng chung.

---

# 39. Không cho dependency vòng

Ví dụ cấm:

```text
types → optimizer
optimizer → types
```

Thay vào đó:

```text
types
 ↓
HIR
 ↓
MIR
 ↓
optimizer
```

Nếu optimizer cần type information:

```text
MIR type metadata
```

đã được đưa vào representation.

---

# 40. CompilerContext

Tôi sẽ thay đổi nhẹ đề xuất trước:

Không dùng một `CompilerContext` khổng lồ.

Thay bằng:

```text
CompilerSession
├── SourceManager
├── Diagnostics
├── Target
├── Options
└── Databases
```

và các phase context:

```text
ResolverContext
TypeContext
MirContext
CodegenContext
LinkContext
```

---

# 41. CompilerSession là lifetime root

```text
main()
  ↓
CompilerSession
  ├── sources
  ├── interners
  ├── diagnostics
  └── target
```

Các object phase không được sống lâu hơn session nếu chúng phụ thuộc session.

Đây là nơi compiler ownership model rất đẹp:

```text
Session
 ├── owns source
 ├── owns interners
 ├── owns semantic databases
 └── owns diagnostics
```

---

# 42. Nhưng phase output có thể độc lập

Ví dụ:

```text
MirModule
```

có thể trở thành artifact độc lập:

```text
compile
  ↓
.mir semantic artifact
```

nếu sau này muốn incremental compilation.

---

# 43. Incremental compilation

```text
incremental/
├── artifact.ax
├── cache.ax
├── fingerprint.ax
├── dependency.ax
└── invalidation.ax
```

Artifact key:

```text
SourceHash
+
CompilerVersion
+
Target
+
SemanticOptions
+
ComptimeInputs
```

Không chỉ:

```text
mtime
```

---

# 44. Compiler artifact

Có thể có:

```text
.axm
```

nhưng `.axm` nên là **semantic compiler artifact**, không phải native object.

Ví dụ:

```text
.axm
├── module interface
├── type information
├── generic metadata
├── dependency fingerprints
└── optional optimized semantic IR
```

Còn:

```text
.o
.obj
```

là native object.

---

# 45. Public interface artifact

Một điểm đáng cân nhắc:

Compiler không nhất thiết phải parse lại toàn bộ dependency.

Ví dụ module:

```text
foo.ax
```

compile thành:

```text
foo.axm
foo.o
```

`foo.axm` chứa:

```text
pub struct Foo
pub fn bar(...)
pub trait X
```

và semantic information cần thiết.

Private implementation không cần expose.

---

# 46. Điều này cực kỳ quan trọng cho tốc độ compiler

Ví dụ:

```text
app
 ├── graphics
 ├── network
 ├── math
 └── ui
```

Thay vì:

```text
parse everything
typecheck everything
```

có thể:

```text
load .axm
```

và chỉ rebuild module thay đổi.

---

# 47. Một nguyên tắc nữa nên đóng băng

### `ACOMPILER-001 — Phase Ownership Isolation`

Mỗi compiler phase sở hữu representation của nó.

Ví dụ:

```text
Parser
    owns AST construction

Resolver
    owns resolution facts

TypeChecker
    owns type facts

OwnershipChecker
    owns capability verification

MIR
    owns executable semantic representation

Backend
    owns target representation
```

Không phase nào được âm thầm mutate representation của phase khác.

---

# 48. `Compiler IR` không phải một IR duy nhất

Ta nên chính thức coi:

```text
AST
HIR
MIR
LIR
Machine IR
Object IR
Link IR
```

là **các IR khác nhau với mục đích khác nhau**.

Không cố tạo một "universal IR".

Đây là quyết định rất quan trọng.

---

# 49. Pipeline cuối cùng

Kiến trúc compiler hiện tại trở thành:

```text
Source
 ↓
Lexer
 ↓
AST
 ↓
Resolver
 ↓
HIR
 ↓
Type/Trait
 ↓
Typed HIR
 ↓
Ownership/Capability
 ↓
Verified HIR
 ↓
Closure/Async/Comptime lowering
 ↓
MIR
 ↓
MIR Verification
 ↓
Semantic Optimization
 ↓
ABI/Layout
 ↓
LIR
 ↓
Target Legalization
 ↓
Machine Selection
 ↓
Machine IR
 ↓
Machine Optimization
 ↓
Register Allocation
 ↓
Frame Layout
 ↓
Final Machine IR
 ↓
Encoding
 ↓
Object IR
 ↓
ELF/COFF/Mach-O
 ↓
Axiom Linker
 ↓
Native Executable
```

Đây là một pipeline đủ mạnh để hướng tới compiler production chứ không chỉ compiler demo.

---

# 50. Invariants mới

Đề nghị đóng băng:

```text
ACOMPILER-01  Compiler Phases Have Explicit Ownership
ACOMPILER-02  IRs Are Phase-Specific
ACOMPILER-03  Phase Dependencies Are Acyclic
ACOMPILER-04  Backend Does Not Depend On AST
ACOMPILER-05  Linker Does Not Depend On Semantic IR
ACOMPILER-06  Driver Does Not Implement Compiler Semantics
ACOMPILER-07  AST Is Syntax Representation
ACOMPILER-08  HIR Is Semantic Frontend Representation
ACOMPILER-09  MIR Is Semantic Execution Representation
ACOMPILER-10  LIR Is ABI-Lowered Target-Independent Representation
ACOMPILER-11  Machine IR Is Target-Specific
ACOMPILER-12  Object IR Is Format-Independent
ACOMPILER-13  Link IR Is Executable-Layout Representation
ACOMPILER-14  Trait Resolution Completes Before MIR
ACOMPILER-15  Ownership Verification Completes Before MIR
ACOMPILER-16  MIR Is Independently Verifiable
ACOMPILER-17  MIR Interpreter Is Independent Of Native Backend
ACOMPILER-18  Compiler IDs Are Stable Semantic Identities
ACOMPILER-19  Raw Addresses Are Not Semantic IDs
ACOMPILER-20  Compiler Data Does Not Require GC
ACOMPILER-21  Compiler Data Does Not Require Implicit RC
ACOMPILER-22  Arena Lifetime Is Explicit
ACOMPILER-23  Compiler Phase Output May Be Reclaimed
ACOMPILER-24  Compiler State Is Not Global Mutable State
ACOMPILER-25  Incremental Artifacts Have Semantic Identity
ACOMPILER-26  Comptime Inputs Affect Artifact Identity
ACOMPILER-27  Backend Cannot Reinterpret Frontend Semantics
ACOMPILER-28  Object Writer Cannot Resolve Link Symbols
ACOMPILER-29  Linker Cannot Modify Source Semantics
ACOMPILER-30  Each IR Has An Explicit Contract
```

---

## 51. Bây giờ Axiom đã có một điểm rất đáng chú ý

Từ đầu chúng ta đặt mục tiêu:

> **"Ngôn ngữ đơn giản cho programmer, nhưng compiler có thể phức tạp bên trong."**

Kiến trúc compiler hiện tại thực sự phản ánh điều đó.

Programmer viết:

```text
fn sum(a: view<i32>) -> i32 {
    ...
}
```

Compiler bên dưới phải xử lý:

```text
ownership
capability
provenance
region
alias
HIR
MIR
ABI
layout
register allocation
frame
machine encoding
relocation
linking
```

Nhưng **toàn bộ độ phức tạp đó không được đẩy ngược lên source language**.

Đây chính là điểm khác biệt quan trọng nhất mà tôi nghĩ nên giữ làm nguyên tắc thiết kế xuyên suốt Axiom.

---

### Bước tiếp theo

Sau khi skeleton compiler đã được xác định, bước hợp lý tiếp theo là **BOOTSTRAP-004 — xây `axiom0` thực tế**, tức xác định **thứ tự implementation chính xác của Stage-0 theo từng commit/milestone**, từ `hello.ax` → arithmetic → function → struct → ownership → MIR → x86-64 → ELF → native linker → compiler có khả năng compile chính Stage-1.

Ở bước đó chúng ta có thể chuyển từ *"compiler nên có gì"* sang *"AI agent phải code cái gì trước, cái gì sau, test nào phải pass trước khi được phép sang phase kế tiếp"*.